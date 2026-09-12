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
    ) -> None:
        self.repo = repo
        self.gateway = gateway

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
        Record initial provider failure and deterministically dispatch offer to first eligible equivalent provider.
        Returns: (updated_case, dispatched_offer, provider_response_url)
        """
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        case = self.repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Recovery case {case_id} not found")

        plan = self.repo.get_plan(case.plan_id)
        if not plan:
            raise NotFoundError(f"Accommodation plan {case.plan_id} not found")

        now = datetime.now(timezone.utc)

        # 1. State transition: CONFIRMED -> AT_RISK -> RECOVERING
        initial_state = case.state
        validate_transition(case.state, CaseState.AT_RISK)
        case.state = CaseState.AT_RISK
        case.trigger_type = "provider_decline"
        case.trigger_text = trigger_text
        case.opened_at = now
        self.repo.save_case(case)

        self._record_audit(
            case_id=case.case_id,
            actor_type=ActorType.PROVIDER,
            action="ORIGINAL_PROVIDER_DECLINED",
            correlation_id=cid,
            before_state=initial_state.value,
            after_state=case.state.value,
            metadata={"trigger_text": trigger_text},
        )

        validate_transition(case.state, CaseState.RECOVERING)
        prev_state = case.state
        case.state = CaseState.RECOVERING
        self.repo.save_case(case)

        self._record_audit(
            case_id=case.case_id,
            actor_type=ActorType.SYSTEM,
            action="AUTONOMOUS_RECOVERY_INITIATED",
            correlation_id=cid,
            before_state=prev_state.value,
            after_state=case.state.value,
        )

        # 2. Find eligible providers (excluding current failed provider)
        all_providers = self.repo.list_providers()
        available_candidates = [
            p for p in all_providers if p.provider_id != plan.assigned_provider_id
        ]

        eligible = filter_eligible_providers(plan, available_candidates)

        if not eligible:
            # Escalation required: no safe equivalent within budget
            validate_transition(case.state, CaseState.ESCALATION_REQUIRED)
            case.state = CaseState.ESCALATION_REQUIRED
            case.human_decision_required = True
            case.blocked_reason = "No eligible replacement provider found within budget and specifications."
            self.repo.save_case(case)

            self._record_audit(
                case_id=case.case_id,
                actor_type=ActorType.SYSTEM,
                action="ESCALATION_NO_ELIGIBLE_PROVIDER",
                correlation_id=cid,
                before_state=CaseState.RECOVERING.value,
                after_state=case.state.value,
                policy_result="BLOCKED",
            )
            return case, None, None

        # 3. Select first eligible provider (e.g. Provider B) and dispatch offer
        selected_provider = eligible[0]
        deadline = now + timedelta(minutes=15)
        case.response_deadline = deadline

        offer, raw_token, response_url = self.gateway.dispatch_offer(
            case=case,
            plan=plan,
            provider=selected_provider,
            expires_at=deadline,
        )
        self.repo.save_offer(offer)

        validate_transition(case.state, CaseState.REPLACEMENT_PENDING)
        prev_state = case.state
        case.state = CaseState.REPLACEMENT_PENDING
        case.attempt_count += 1
        self.repo.save_case(case)

        self._record_audit(
            case_id=case.case_id,
            actor_type=ActorType.SYSTEM,
            action="PROVIDER_OFFER_DISPATCHED",
            tool_name="send_provider_offer",
            policy_result="APPROVED",
            correlation_id=cid,
            before_state=prev_state.value,
            after_state=case.state.value,
            metadata={
                "offer_id": offer.offer_id,
                "provider_id": selected_provider.provider_id,
                "provider_name": selected_provider.display_name,
                "expires_at": deadline.isoformat(),
            },
        )

        return case, offer, response_url

    def record_provider_response(
        self,
        raw_token: str,
        action: str,
        response_text: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> Tuple[RecoveryCase, ProviderOffer]:
        """
        Record provider acceptance or decline with strict idempotency and token expiry check.
        Returns: (updated_case, updated_offer)
        """
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        token_hash = self.gateway.hash_token(raw_token)
        offer = self.repo.get_offer_by_token_hash(token_hash)
        if not offer:
            raise NotFoundError("Invalid or unknown provider response token")

        case = self.repo.get_case(offer.case_id)
        if not case:
            raise NotFoundError(f"Recovery case {offer.case_id} not found")

        plan = self.repo.get_plan(case.plan_id)
        if not plan:
            raise NotFoundError(f"Plan {case.plan_id} not found")

        now = datetime.now(timezone.utc)
        action_upper = action.strip().upper()

        # Idempotency check: if offer already recorded with the same terminal state
        if offer.state == OfferState.ACCEPTED and action_upper == "ACCEPT":
            # Idempotent replay: return immediately with zero side-effects
            return case, offer

        if offer.state == OfferState.DECLINED and action_upper == "DECLINE":
            return case, offer

        # Check token expiration
        if now > offer.expires_at:
            offer.state = OfferState.EXPIRED
            self.repo.save_offer(offer)
            raise OfferExpiredError("Provider response token has expired")

        if action_upper == "ACCEPT":
            # 1. Update Offer
            offer.state = OfferState.ACCEPTED
            offer.response_at = now
            offer.response_text = response_text or "Offer accepted via provider portal"
            self.repo.save_offer(offer)

            # 2. Update Accommodation Plan
            prev_provider = plan.assigned_provider_id
            plan.assigned_provider_id = offer.provider_id
            plan.version += 1
            plan.status = CaseState.RECOVERED
            self.repo.save_plan(plan)

            # 3. State transition: REPLACEMENT_PENDING -> RECOVERED -> ATTENDEE_CONFIRMATION_PENDING
            validate_transition(case.state, CaseState.RECOVERED)
            case.state = CaseState.RECOVERED
            case.recovered_at = now
            self.repo.save_case(case)

            self._record_audit(
                case_id=case.case_id,
                actor_type=ActorType.PROVIDER,
                action="PROVIDER_OFFER_ACCEPTED",
                correlation_id=cid,
                before_state=CaseState.REPLACEMENT_PENDING.value,
                after_state=case.state.value,
                metadata={
                    "offer_id": offer.offer_id,
                    "provider_id": offer.provider_id,
                    "previous_provider_id": prev_provider,
                },
            )

            validate_transition(case.state, CaseState.ATTENDEE_CONFIRMATION_PENDING)
            prev_state = case.state
            case.state = CaseState.ATTENDEE_CONFIRMATION_PENDING
            self.repo.save_case(case)

            self._record_audit(
                case_id=case.case_id,
                actor_type=ActorType.SYSTEM,
                action="AWAITING_ATTENDEE_CONFIRMATION",
                correlation_id=cid,
                before_state=prev_state.value,
                after_state=case.state.value,
            )

            return case, offer

        elif action_upper == "DECLINE":
            offer.state = OfferState.DECLINED
            offer.response_at = now
            offer.response_text = response_text or "Offer declined by provider"
            self.repo.save_offer(offer)

            self._record_audit(
                case_id=case.case_id,
                actor_type=ActorType.PROVIDER,
                action="BACKUP_PROVIDER_DECLINED",
                correlation_id=cid,
                metadata={"offer_id": offer.offer_id, "provider_id": offer.provider_id},
            )
            # Escalate or retry
            validate_transition(case.state, CaseState.ESCALATION_REQUIRED)
            case.state = CaseState.ESCALATION_REQUIRED
            case.human_decision_required = True
            case.blocked_reason = "Backup provider declined offer."
            self.repo.save_case(case)
            return case, offer

        else:
            raise ValueError(f"Unsupported provider response action: {action}")

    def confirm_attendee(
        self,
        case_id: str,
        correlation_id: Optional[str] = None,
    ) -> RecoveryCase:
        """
        Record final attendee confirmation, completing the recovery loop and locking the recovery clock.
        """
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        case = self.repo.get_case(case_id)
        if not case:
            raise NotFoundError(f"Recovery case {case_id} not found")

        plan = self.repo.get_plan(case.plan_id)
        if not plan:
            raise NotFoundError(f"Plan {case.plan_id} not found")

        # If already confirmed, return idempotently
        if case.state == CaseState.ATTENDEE_CONFIRMED:
            return case

        validate_transition(case.state, CaseState.ATTENDEE_CONFIRMED)
        now = datetime.now(timezone.utc)
        prev_state = case.state

        case.state = CaseState.ATTENDEE_CONFIRMED
        case.confirmed_at = now
        self.repo.save_case(case)

        plan.status = CaseState.ATTENDEE_CONFIRMED
        self.repo.save_plan(plan)

        # Calculate time metrics
        recovery_time = None
        if case.recovered_at and case.opened_at:
            recovery_time = (case.recovered_at - case.opened_at).total_seconds()

        total_time = None
        if case.opened_at:
            total_time = (now - case.opened_at).total_seconds()

        self._record_audit(
            case_id=case.case_id,
            actor_type=ActorType.ATTENDEE,
            action="ATTENDEE_CONFIRMED_RECOVERY",
            correlation_id=cid,
            before_state=prev_state.value,
            after_state=case.state.value,
            metadata={
                "time_to_recovered_seconds": recovery_time,
                "time_to_confirmed_seconds": total_time,
            },
        )

        return case

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
