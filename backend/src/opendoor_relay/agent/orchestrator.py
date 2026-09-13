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
        from opendoor_relay.agent.models import (
            AGENT_MODE_BEDROCK,
            AGENT_MODE_REHEARSAL,
            get_agent_mode,
        )

        mode = get_agent_mode()
        if mode == AGENT_MODE_BEDROCK:
            adapter = BedrockModelAdapter()
            avail, reason = adapter.check_availability()
            if not avail:
                raise RuntimeError(
                    f"AGENT_MODE is configured for 'bedrock', but Bedrock access is unavailable: {reason}. "
                    "Failing closed to prevent unauthorized or silent fallback."
                )
            self.model = adapter.create_model()
            self.agent_mode = AGENT_MODE_BEDROCK
        elif mode == AGENT_MODE_REHEARSAL:
            if model is not None:
                self.model = model
            else:
                self.model = RehearsalModel()
            self.agent_mode = AGENT_MODE_REHEARSAL
        else:
            raise ValueError(f"Unknown AGENT_MODE: '{mode}'. Must be 'rehearsal' or 'bedrock'.")

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
        """Trigger autonomous recovery strictly through the real Strands agent loop."""
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
                action="STATE_CHANGED",
                tool_name="initiate_recovery",
                policy_result="APPROVED",
                before_state=init_state.value,
                after_state=case.state.value,
                metadata={"trigger_text": trigger_text, "event": "PROVIDER_FAILURE_TRIGGERED"},
            )

            validate_transition(case.state, CaseState.RECOVERING)
            prev_state = case.state
            case.state = CaseState.RECOVERING
            self.repo.save_case(case)

            ctx.record_audit(
                case_id=case_id,
                action="STATE_CHANGED",
                tool_name="initiate_recovery",
                policy_result="APPROVED",
                before_state=prev_state.value,
                after_state=case.state.value,
                metadata={"event": "AUTONOMOUS_RECOVERY_STARTED"},
            )

            # Invoke genuine Strands Agent loop (all tool proposals pass through BeforeToolCallEvent)
            agent = self._create_agent()
            prompt = f"Initiate recovery for case {case_id}: trigger='{trigger_text}'"
            agent_result = agent(prompt)

            # Record concise MODEL_DECISION (no internal CoT)
            decision_summary = (
                str(agent_result.message)
                if hasattr(agent_result, "message")
                else "Recovery agent completed tool proposal sequence."
            )
            ctx.record_audit(
                case_id=case_id,
                action="MODEL_DECISION",
                tool_name=None,
                policy_result="APPROVED",
                before_state=case.state.value,
                after_state=self.repo.get_case(case_id).state.value,
                metadata={"decision_summary": decision_summary},
            )

            updated_case = self.repo.get_case(case_id)
            offers = self.repo.list_offers_for_case(case_id)
            dispatched_offer = offers[-1] if offers else None

            response_url = None
            if dispatched_offer:
                dispatched = self.gateway.get_dispatched_offer(dispatched_offer.offer_id)
                if isinstance(dispatched, dict):
                    response_url = dispatched.get("response_url")
                elif dispatched and hasattr(dispatched, "response_url"):
                    response_url = dispatched.response_url
                if not response_url:
                    response_url = f"http://localhost:8000/api/provider/respond/mock-{dispatched_offer.offer_id}"

            return updated_case, dispatched_offer, response_url

        finally:
            reset_current_context(token)

    def process_provider_reply(
        self,
        offer_id: str,
        reply_text: str,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> Tuple[RecoveryCase, Optional[ProviderOffer]]:
        """Process incoming provider reply strictly through the real Strands agent loop."""
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
                return case, offer

            # Invoke genuine Strands Agent loop
            agent = self._create_agent()
            prompt = f"Process provider reply for offer {offer_id}: reply='{reply_text}'. Case ID: {case.case_id}."
            agent_result = agent(prompt)

            decision_summary = (
                str(agent_result.message)
                if hasattr(agent_result, "message")
                else "Recovery agent processed provider response."
            )
            ctx.record_audit(
                case_id=case.case_id,
                action="MODEL_DECISION",
                tool_name=None,
                policy_result="APPROVED",
                before_state=case.state.value,
                after_state=self.repo.get_case(case.case_id).state.value,
                metadata={"decision_summary": decision_summary},
            )

            updated_case = self.repo.get_case(case.case_id)
            case_offers = self.repo.list_offers_for_case(case.case_id)
            updated_offer = case_offers[-1] if case_offers else self.repo.get_offer(offer_id)
            return updated_case, updated_offer

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
                action="STATE_CHANGED",
                tool_name="confirm_attendee",
                policy_result="APPROVED",
                before_state=prev_state.value,
                after_state=case.state.value,
                metadata={
                    "event": "ATTENDEE_CONFIRMED_RECOVERY",
                    "headline_time_to_confirmed_recovery_seconds": elapsed_seconds,
                    "attendee_alias": plan.attendee_alias,
                },
            )
            return case

        finally:
            reset_current_context(token)

    def get_developer_trace(self, case_id: str) -> Dict[str, Any]:
        """Export sanitized developer-only execution trace for a case.
        
        Distinguishes MODEL_DECISION, TOOL_PROPOSED, POLICY_APPROVED, TOOL_EXECUTED, and STATE_CHANGED.
        Omits internal secrets and hidden chain-of-thought.
        """
        case = self.repo.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        audits = self.repo.get_audit_events_for_case(case_id)
        records = []

        for idx, a in enumerate(audits, start=1):
            category = "AUDIT_EVENT"
            if a.action == "MODEL_DECISION":
                category = "MODEL_DECISION"
            elif a.action == "TOOL_PROPOSED":
                category = "TOOL_PROPOSED"
            elif a.action == "POLICY_APPROVED" or (a.policy_result == "APPROVED" and "APPROVED" in a.action):
                category = "POLICY_APPROVED"
            elif a.action == "TOOL_EXECUTED":
                category = "TOOL_EXECUTED"
            elif "DENIED" in a.action or a.policy_result == "BLOCKED":
                category = "TOOL_DENIED"
            elif a.action == "STATE_CHANGED" or (a.before_state != a.after_state and a.after_state is not None):
                category = "STATE_CHANGED"

            records.append({
                "step": idx,
                "timestamp": a.timestamp.isoformat(),
                "actor": a.actor_type.value,
                "action": a.action,
                "category": category,
                "tool_name": a.tool_name,
                "policy_result": a.policy_result or "APPROVED",
                "before_state": a.before_state,
                "after_state": a.after_state,
                "metadata": {k: v for k, v in a.metadata.items() if "secret" not in k.lower() and "token" not in k.lower()},
            })

        model_invocations = getattr(self.model, "model_invocations", 0)
        return {
            "case_id": case_id,
            "agent_mode": getattr(self, "agent_mode", "rehearsal"),
            "model_invocations": model_invocations,
            "current_state": case.state.value,
            "opened_at": case.opened_at.isoformat() if case.opened_at else None,
            "recovered_at": case.recovered_at.isoformat() if case.recovered_at else None,
            "confirmed_at": case.confirmed_at.isoformat() if case.confirmed_at else None,
            "human_decision_required": case.human_decision_required,
            "blocked_reason": case.blocked_reason,
            "trace_record_count": len(records),
            "trace_records": records,
        }

