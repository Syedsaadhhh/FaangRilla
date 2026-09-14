"""Deterministic recovery orchestrator enforcing state transitions, policy boundaries, and idempotency."""

from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple

from opendoor_relay.domain.models import (
    CaseState,
    OfferState,
    ActorType,
    AuditEvent,
    RecoveryCase,
    AccommodationPlan,
    Provider,
    ProviderOffer,
)
from opendoor_relay.domain.state_machine import validate_transition
from opendoor_relay.domain.policy import (
    PolicyResult,
    check_equivalence,
    check_budget,
    check_consent,
    filter_eligible_providers,
)
from opendoor_relay.repository.interface import RepositoryInterface
from opendoor_relay.provider_gateway.interface import ProviderGatewayInterface


class RecoveryError(Exception):
    """Base recovery domain exception."""
    pass


class NotFoundError(RecoveryError):
    pass


class OfferExpiredError(RecoveryError):
    pass


class PolicyViolationError(RecoveryError):
    pass


class RecoveryService:
    """Core orchestration service for OpenDoor Relay."""

    def __init__(
        self,
        repo: RepositoryInterface,
        gateway: ProviderGatewayInterface,
        model: Optional[Any] = None,
    ) -> None:
        self.repo = repo
        self.gateway = gateway
        from opendoor_relay.agent.orchestrator import RecoveryAgentOrchestrator
        self.orchestrator = RecoveryAgentOrchestrator(repo=repo, gateway=gateway, model=model)

    def get_developer_trace(self, case_id: str) -> Dict[str, Any]:
        """Delegate developer trace extraction to orchestrator."""
        return self.orchestrator.get_developer_trace(case_id)


    def _record_audit(
        self,
        case_id: str,
        actor_type: ActorType,
        action: str,
        correlation_id: str,
        tool_name: Optional[str] = None,
        policy_result: Optional[str] = None,
        before_state: Optional[str] = None,
        after_state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            audit_id=f"aud-{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            timestamp=datetime.now(timezone.utc),
            actor_type=actor_type,
            action=action,
            tool_name=tool_name,
            policy_result=policy_result,
            before_state=before_state,
            after_state=after_state,
            correlation_id=correlation_id,
            metadata=metadata or {},
        )
        self.repo.add_audit_event(event)
        return event

    def trigger_provider_failure(
        self,
        case_id: str,
        trigger_text: str = "Provider A declared unavailability",
        correlation_id: Optional[str] = None,
    ) -> Tuple[RecoveryCase, Optional[ProviderOffer], Optional[str]]:
        """
        Record initial provider failure and autonomously orchestrate recovery using Strands SDK.
        Returns: (updated_case, dispatched_offer, provider_response_url)
        """
        return self.orchestrator.initiate_recovery(
            case_id=case_id,
            trigger_text=trigger_text,
            correlation_id=correlation_id,
        )

    def record_provider_response(
        self,
        raw_token: str,
        action: str,
        response_text: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[RecoveryCase, ProviderOffer]:
        """
        Record provider acceptance or decline by delegating to the autonomous Strands agent.
        Returns: (updated_case, updated_offer)
        """
        token_hash = self.gateway.hash_token(raw_token)
        offer = self.repo.get_offer_by_token_hash(token_hash)
        if not offer:
            raise NotFoundError("Invalid or unknown provider response token")
        now = datetime.now(timezone.utc)
        if now > offer.expires_at:
            offer.state = OfferState.EXPIRED
            self.repo.save_offer(offer)
            from opendoor_relay.service.recovery import OfferExpiredError
            raise OfferExpiredError("Provider response token has expired")
        
        reply_text = f"[{action.upper()}] {response_text or action}"
        case, updated_offer = self.orchestrator.process_provider_reply(
            offer_id=offer.offer_id,
            reply_text=reply_text,
            correlation_id=correlation_id,
        )
        if not updated_offer:
            raise RuntimeError("Orchestrator failed to return updated offer")
            
        return case, updated_offer

    def confirm_attendee(
        self,
        case_id: str,
        correlation_id: Optional[str] = None,
    ) -> RecoveryCase:
        """
        Record final attendee confirmation, completing the recovery loop and locking the recovery clock.
        """
        return self.orchestrator.confirm_attendee(
            case_id=case_id,
            correlation_id=correlation_id,
        )

    def attempt_apply_provider(
        self,
        case_id: str,
        provider_id: str,
    ) -> Tuple[bool, PolicyResult]:
        """
        Explicit test harness method demonstrating deterministic policy blocking (e.g. for Provider C).
        """
        case = self.repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")

        plan = self.repo.get_plan(case.plan_id)
        if not plan:
            raise NotFoundError(f"Plan {case.plan_id} not found")

        provider = self.repo.get_provider(provider_id)
        if not provider:
            raise NotFoundError(f"Provider {provider_id} not found")

        # Run equivalence check
        eq_res = check_equivalence(plan, provider)
        if not eq_res.allowed:
            return False, eq_res

        # Run budget check
        bg_res = check_budget(plan, provider)
        if not bg_res.allowed:
            return False, bg_res

        return True, PolicyResult(allowed=True, policy_name="all", reason="Allowed")
