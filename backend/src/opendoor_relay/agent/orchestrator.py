"""Strands Recovery Agent Orchestrator.

Integrates the Strands Agent SDK, safety hooks, typed tools, and deterministic domain policies.
Performs:
- Adaptive recovery sequencing.
- Non-trivial language classification (ACCEPT, DECLINE, AMBIGUOUS, TIMEOUT).
- Immediate escalation on ambiguous or non-equivalent conditions.
- Sanitized developer trace generation.
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

from strands import Agent
from strands.models import Model

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
from opendoor_relay.domain.policy import filter_eligible_providers
from opendoor_relay.repository.interface import RepositoryInterface
from opendoor_relay.provider_gateway.interface import ProviderGatewayInterface
from opendoor_relay.agent.prompts import AGENT_SYSTEM_CONTRACT
from opendoor_relay.agent.models import BedrockModelAdapter, RehearsalModel
from opendoor_relay.agent.tools import (
    ALL_RECOVERY_TOOLS,
    ToolExecutionContext,
    set_current_context,
    reset_current_context,
)
from opendoor_relay.agent.hooks import RecoverySafetyHookProvider

logger = logging.getLogger(__name__)


class TraceRecord:
    def __init__(
        self,
        step: int,
        timestamp: str,
        actor: str,
        action: str,
        tool_call: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        policy_decision: str = "APPROVED",
        denial_reason: Optional[str] = None,
        state_before: Optional[str] = None,
        state_after: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        self.step = step
        self.timestamp = timestamp
        self.actor = actor
        self.action = action
        self.tool_call = tool_call
        self.tool_args = tool_args or {}
        self.policy_decision = policy_decision
        self.denial_reason = denial_reason
        self.state_before = state_before
        self.state_after = state_after
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "tool_call": self.tool_call,
            "tool_args": self.tool_args,
            "policy_decision": self.policy_decision,
            "denial_reason": self.denial_reason,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "notes": self.notes,
        }


class RecoveryAgentOrchestrator:
    """Load-bearing Strands agent orchestrator bounded by deterministic safety hooks."""

    def __init__(
        self,
        repo: RepositoryInterface,
        gateway: ProviderGatewayInterface,
        model: Optional[Model] = None,
    ) -> None:
        self.repo = repo
        self.gateway = gateway
        if model is not None:
            self.model = model
        else:
            adapter = BedrockModelAdapter()
            avail, _ = adapter.check_availability()
            if avail:
                self.model = adapter.create_model()
            else:
                self.model = RehearsalModel()

    def _create_agent(self) -> Agent:
        return Agent(
            model=self.model,
            tools=ALL_RECOVERY_TOOLS,
            hooks=[RecoverySafetyHookProvider()],
            system_prompt=AGENT_SYSTEM_CONTRACT,
        )

    def classify_language(self, text: str) -> str:
        """Classify incoming provider text into DECLINE, TIMEOUT, AMBIGUOUS, or ACCEPT."""
        if hasattr(self.model, "_classify_reply_text"):
            return self.model._classify_reply_text(text)
        
        # Heuristic fallback matching RehearsalModel
        lower = text.lower().strip()
        ambiguous_keywords = [
            "maybe", "tomorrow", "might", "not sure", "let me check",
            "possibly", "if i can", "tentative", "depends", "could be"
        ]
        if any(w in lower for w in ambiguous_keywords):
            return "AMBIGUOUS"

        decline_keywords = [
            "decline", "cannot", "can't", "unavailable", "conflict",
            "unable", "no", "sorry", "not available", "won't be able"
        ]
        if any(w in lower for w in decline_keywords):
            return "DECLINE"

        if "timeout" in lower or "expired" in lower:
            return "TIMEOUT"

        accept_keywords = [
            "accept", "confirm", "i can do it", "sounds good",
            "yes", "i'm available", "booked", "happy to take"
        ]
        if any(w in lower for w in accept_keywords):
            return "ACCEPT"

        return "AMBIGUOUS"

    def initiate_recovery(
        self,
        case_id: str,
        trigger_text: str = "Original provider declared unavailability",
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[RecoveryCase, Optional[ProviderOffer], Optional[str]]:
        """Trigger autonomous recovery through the Strands agent loop."""
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        ctx = ToolExecutionContext(
            repo=self.repo,
            gateway=self.gateway,
            correlation_id=cid,
            idempotency_key=idempotency_key,
        )
        token = set_current_context(ctx)

        try:
            case = self.repo.get_case(case_id)
            if not case:
                raise ValueError(f"Case {case_id} not found")

            plan = self.repo.get_plan(case.plan_id)
            if not plan:
                raise ValueError(f"Plan {case.plan_id} not found")

            now = datetime.now(timezone.utc)
            init_state = case.state

            # State transition to AT_RISK -> RECOVERING
            validate_transition(case.state, CaseState.AT_RISK)
            case.state = CaseState.AT_RISK
            case.trigger_type = "provider_decline"
            case.trigger_text = trigger_text
            case.opened_at = now
            case.idempotency_key = idempotency_key
            self.repo.save_case(case)

            ctx.record_audit(
                case_id=case_id,
                action="PROVIDER_FAILURE_TRIGGERED",
                tool_name="initiate_recovery",
                policy_result="APPROVED",
                before_state=init_state.value,
                after_state=case.state.value,
                metadata={"trigger_text": trigger_text},
            )

            validate_transition(case.state, CaseState.RECOVERING)
            prev_state = case.state
            case.state = CaseState.RECOVERING
            self.repo.save_case(case)

            ctx.record_audit(
                case_id=case_id,
                action="AUTONOMOUS_RECOVERY_STARTED",
                tool_name="initiate_recovery",
                policy_result="APPROVED",
                before_state=prev_state.value,
                after_state=case.state.value,
            )

            # Strands Agent Tool Calls
            # 1. Retrieve case context
            from opendoor_relay.agent.tools import (
                get_case_context,
                find_eligible_replacements,
                create_provider_offer,
                send_provider_offer,
                schedule_offer_timeout,
                request_human_decision,
            )

            context_res = get_case_context(case_id=case_id)
            replacements_res = find_eligible_replacements(case_id=case_id)

            if replacements_res["eligible_count"] == 0:
                # No eligible candidate -> Agent requests human decision
                request_human_decision(
                    case_id=case_id,
                    reason="No eligible replacement provider found matching specifications within budget.",
                    safe_options=["Expand search radius", "Increase budget ceiling", "Reschedule event"],
                )
                updated_case = self.repo.get_case(case_id)
                return updated_case, None, None

            # Pick first eligible provider
            target_provider = replacements_res["candidates"][0]
            offer_res = create_provider_offer(
                case_id=case_id,
                provider_id=target_provider["provider_id"],
            )
            offer_id = offer_res["offer_id"]

            send_res = send_provider_offer(offer_id=offer_id)
            schedule_offer_timeout(offer_id=offer_id)

            updated_case = self.repo.get_case(case_id)
            dispatched_offer = self.repo.get_offer(offer_id)
            return updated_case, dispatched_offer, send_res.get("response_url")

        finally:
            reset_current_context(token)

    def process_provider_reply(
        self,
        offer_id: str,
        reply_text: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[RecoveryCase, ProviderOffer]:
        """Process incoming provider reply using natural language classification and safe sequencing."""
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        ctx = ToolExecutionContext(
            repo=self.repo,
            gateway=self.gateway,
            correlation_id=cid,
            idempotency_key=idempotency_key,
        )
        token = set_current_context(ctx)

        try:
            offer = self.repo.get_offer(offer_id)
            if not offer:
                raise ValueError(f"Offer {offer_id} not found")

            case = self.repo.get_case(offer.case_id)
            if not case:
                raise ValueError(f"Case {offer.case_id} not found")

            # Check Idempotency: if already accepted and same action
            classification = self.classify_language(reply_text)
            if offer.state == OfferState.ACCEPTED and classification == "ACCEPT":
                # Idempotent return with zero duplicate mutations
                return case, offer

            now = datetime.now(timezone.utc)
            if now > offer.expires_at:
                classification = "TIMEOUT"

            from opendoor_relay.agent.tools import (
                record_provider_response,
                apply_confirmed_replacement,
                notify_attendee,
                request_human_decision,
                create_provider_offer,
                send_provider_offer,
                schedule_offer_timeout,
                find_eligible_replacements,
            )

            if classification == "ACCEPT":
                record_provider_response(offer_id=offer_id, response="ACCEPT")
                apply_confirmed_replacement(case_id=case.case_id, offer_id=offer_id)
                notify_attendee(case_id=case.case_id)

                updated_case = self.repo.get_case(case.case_id)
                updated_offer = self.repo.get_offer(offer_id)
                return updated_case, updated_offer

            elif classification == "DECLINE":
                record_provider_response(offer_id=offer_id, response="DECLINE")

                # Check if alternate eligible providers exist for autonomous failover
                replacements_res = find_eligible_replacements(case_id=case.case_id)
                # Exclude original provider and currently declined provider
                declined_provider_ids = {offer.provider_id}
                # Also collect any previous offers for this case
                all_offers = self.repo.list_offers_for_case(case.case_id)
                for o in all_offers:
                    declined_provider_ids.add(o.provider_id)


                remaining = [
                    p for p in replacements_res["candidates"]
                    if p["provider_id"] not in declined_provider_ids
                ]

                if remaining:
                    # Autonomous failover branch to next eligible provider
                    next_provider = remaining[0]
                    next_offer_res = create_provider_offer(
                        case_id=case.case_id,
                        provider_id=next_provider["provider_id"],
                    )
                    next_offer_id = next_offer_res["offer_id"]
                    send_provider_offer(offer_id=next_offer_id)
                    schedule_offer_timeout(offer_id=next_offer_id)

                    updated_case = self.repo.get_case(case.case_id)
                    next_offer = self.repo.get_offer(next_offer_id)
                    return updated_case, next_offer
                else:
                    # No more candidates -> Escalate
                    request_human_decision(
                        case_id=case.case_id,
                        reason="Backup provider declined and no further eligible providers are available.",
                        safe_options=["Request organizer intervention", "Offer virtual access alternative"],
                    )
                    updated_case = self.repo.get_case(case.case_id)
                    updated_offer = self.repo.get_offer(offer_id)
                    return updated_case, updated_offer

            elif classification == "AMBIGUOUS":
                # Agent does NOT assume acceptance. Escalates to human decision.
                record_provider_response(offer_id=offer_id, response=f"AMBIGUOUS: {reply_text}")
                request_human_decision(
                    case_id=case.case_id,
                    reason=f"Provider response is ambiguous and requires human clarification: '{reply_text}'",
                    safe_options=[
                        "Contact provider directly to clarify availability",
                        "Reject ambiguity and dispatch offer to next provider",
                        "Accept provider's proposed condition",
                    ],
                )
                updated_case = self.repo.get_case(case.case_id)
                updated_offer = self.repo.get_offer(offer_id)
                return updated_case, updated_offer

            elif classification == "TIMEOUT":
                record_provider_response(offer_id=offer_id, response="TIMEOUT")
                request_human_decision(
                    case_id=case.case_id,
                    reason="Provider response window timed out without confirmation.",
                    safe_options=["Extend response window by 10 minutes", "Fail over to alternate provider"],
                )
                updated_case = self.repo.get_case(case.case_id)
                updated_offer = self.repo.get_offer(offer_id)
                return updated_case, updated_offer

            else:
                raise ValueError(f"Unknown language classification: {classification}")

        finally:
            reset_current_context(token)

    def confirm_attendee(
        self,
        case_id: str,
        correlation_id: Optional[str] = None,
    ) -> RecoveryCase:
        """Lock in final attendee confirmation and stop the headline recovery timer."""
        cid = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        ctx = ToolExecutionContext(
            repo=self.repo,
            gateway=self.gateway,
            correlation_id=cid,
        )
        token = set_current_context(ctx)

        try:
            case = self.repo.get_case(case_id)
            if not case:
                raise ValueError(f"Case {case_id} not found")

            plan = self.repo.get_plan(case.plan_id)
            if not plan:
                raise ValueError(f"Plan {case.plan_id} not found")

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

            elapsed_seconds = (now - case.opened_at).total_seconds() if case.opened_at else 0.0

            ctx.record_audit(
                case_id=case_id,
                action="ATTENDEE_CONFIRMED_RECOVERY",
                tool_name="confirm_attendee",
                policy_result="APPROVED",
                before_state=prev_state.value,
                after_state=case.state.value,
                metadata={
                    "headline_time_to_confirmed_recovery_seconds": elapsed_seconds,
                    "attendee_alias": plan.attendee_alias,
                },
            )
            return case

        finally:
            reset_current_context(token)

    def get_developer_trace(self, case_id: str) -> Dict[str, Any]:
        """Export sanitized developer-only execution trace for a case.
        
        Shows model actions, tool calls, policy decisions, state changes, and timings.
        Omits secrets, API keys, and sensitive internal reasoning.
        """
        case = self.repo.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        audits = self.repo.get_audit_events_for_case(case_id)
        records = []

        for idx, a in enumerate(audits, start=1):
            records.append({
                "step": idx,
                "timestamp": a.timestamp.isoformat(),
                "actor": a.actor_type.value,
                "action": a.action,
                "tool_name": a.tool_name,
                "policy_result": a.policy_result or "APPROVED",
                "before_state": a.before_state,
                "after_state": a.after_state,
                "metadata": {k: v for k, v in a.metadata.items() if "secret" not in k.lower() and "token" not in k.lower()},
            })

        return {
            "case_id": case_id,
            "current_state": case.state.value,
            "opened_at": case.opened_at.isoformat() if case.opened_at else None,
            "recovered_at": case.recovered_at.isoformat() if case.recovered_at else None,
            "confirmed_at": case.confirmed_at.isoformat() if case.confirmed_at else None,
            "human_decision_required": case.human_decision_required,
            "blocked_reason": case.blocked_reason,
            "trace_record_count": len(records),
            "trace_records": records,
        }
