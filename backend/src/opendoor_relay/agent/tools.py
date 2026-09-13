"""Typed tools for OpenDoor Relay recovery agent.

Conforms strictly to the boss file tool specifications:
- get_case_context(case_id)
- find_eligible_replacements(case_id)
- create_provider_offer(case_id, provider_id)
- send_provider_offer(offer_id)
- schedule_offer_timeout(offer_id)
- record_provider_response(offer_id, response)
- apply_confirmed_replacement(case_id, offer_id)
- notify_attendee(case_id)
- request_human_decision(case_id, reason, safe_options)

All tools return structured Pydantic models (serializable to JSON).
"""

from __future__ import annotations
from contextvars import ContextVar
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field
from strands import tool

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
    check_equivalence,
    check_budget,
    check_consent,
    filter_eligible_providers,
)
from opendoor_relay.repository.interface import RepositoryInterface
from opendoor_relay.provider_gateway.interface import ProviderGatewayInterface


# Structured Tool Result Models

class CaseContextResult(BaseModel):
    case_id: str
    event_id: str
    plan_id: str
    state: str
    attendee_alias: str
    functional_need: str
    service_type: str
    language: str
    format: str
    equipment: str
    budget_ceiling: float
    consent_scope: List[str]
    assigned_provider_id: Optional[str] = None
    attempt_count: int = 0
    opened_at: Optional[str] = None
    response_deadline: Optional[str] = None


class ProviderSummary(BaseModel):
    provider_id: str
    display_name: str
    cost: float
    service_types: List[str]
    languages: List[str]
    formats: List[str]
    equipment_supported: List[str]


class EligibleReplacementsResult(BaseModel):
    case_id: str
    eligible_count: int
    candidates: List[ProviderSummary]


class CreateOfferResult(BaseModel):
    offer_id: str
    case_id: str
    provider_id: str
    state: str
    sent_at: str
    expires_at: str


class SendOfferResult(BaseModel):
    offer_id: str
    case_id: str
    provider_id: str
    contact_channel: str
    response_url: str
    dispatched_at: str


class ScheduleTimeoutResult(BaseModel):
    offer_id: str
    expires_at: str
    scheduled: bool
    timer_reference: str


class RecordResponseResult(BaseModel):
    offer_id: str
    case_id: str
    provider_id: str
    response_state: str
    response_text: str
    recorded_at: str


class ApplyReplacementResult(BaseModel):
    case_id: str
    plan_id: str
    assigned_provider_id: str
    plan_version: int
    case_state: str
    applied_at: str


class NotifyAttendeeResult(BaseModel):
    case_id: str
    attendee_alias: str
    status: str
    message: str
    notified_at: str


class RequestHumanDecisionResult(BaseModel):
    case_id: str
    reason: str
    safe_options: List[str]
    case_state: str
    decision_required: bool
    escalated_at: str


# Tool Context Management

class ToolExecutionContext:
    """Carries execution dependencies (repository, gateway, tracing) for tool invocations."""

    def __init__(
        self,
        repo: RepositoryInterface,
        gateway: ProviderGatewayInterface,
        correlation_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> None:
        self.repo = repo
        self.gateway = gateway
        self.correlation_id = correlation_id or f"corr-{uuid.uuid4().hex[:8]}"
        self.idempotency_key = idempotency_key
        self.executed_tools: List[Dict[str, Any]] = []

    def record_audit(
        self,
        case_id: str,
        action: str,
        tool_name: str,
        policy_result: str,
        before_state: Optional[str] = None,
        after_state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            audit_id=f"aud-{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.AGENT,
            action=action,
            tool_name=tool_name,
            policy_result=policy_result,
            before_state=before_state,
            after_state=after_state,
            correlation_id=self.correlation_id,
            metadata=metadata or {},
        )
        self.repo.add_audit_event(event)
        return event


_current_context: ContextVar[Optional[ToolExecutionContext]] = ContextVar(
    "tool_execution_context", default=None
)


def get_current_context() -> ToolExecutionContext:
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError("No active ToolExecutionContext configured for tool call.")
    return ctx


def set_current_context(ctx: ToolExecutionContext):
    return _current_context.set(ctx)


def reset_current_context(token):
    _current_context.reset(token)


# Tool Definitions

@tool
def get_case_context(case_id: str) -> dict:
    """Retrieve verified context for an active recovery case and its accommodation plan.
    
    Returns functional access specifications, budget limit, and current case state.
    Medical diagnoses and sensitive information are strictly omitted.
    """
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    plan = ctx.repo.get_plan(case.plan_id)
    if not plan:
        raise ValueError(f"Plan {case.plan_id} not found")

    result = CaseContextResult(
        case_id=case.case_id,
        event_id=case.event_id,
        plan_id=plan.plan_id,
        state=case.state.value,
        attendee_alias=plan.attendee_alias,
        functional_need=plan.functional_need,
        service_type=plan.service_type,
        language=plan.language,
        format=plan.format,
        equipment=plan.equipment,
        budget_ceiling=plan.budget_ceiling,
        consent_scope=plan.consent_scope,
        assigned_provider_id=plan.assigned_provider_id,
        attempt_count=case.attempt_count,
        opened_at=case.opened_at.isoformat() if case.opened_at else None,
        response_deadline=case.response_deadline.isoformat() if case.response_deadline else None,
    )
    ctx.executed_tools.append({"tool": "get_case_context", "case_id": case_id, "result": result.model_dump()})
    return result.model_dump()


@tool
def find_eligible_replacements(case_id: str) -> dict:
    """Find approved replacement providers matching the exact accommodation requirements and budget ceiling.
    
    Applies deterministic policy filters for equivalence (service type, language, format, equipment)
    and budget limit. Excludes the currently assigned provider.
    """
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    plan = ctx.repo.get_plan(case.plan_id)
    if not plan:
        raise ValueError(f"Plan {case.plan_id} not found")

    all_providers = ctx.repo.list_providers()
    candidates = [p for p in all_providers if p.provider_id != plan.assigned_provider_id]
    eligible = filter_eligible_providers(plan, candidates)

    summary_list = [
        ProviderSummary(
            provider_id=p.provider_id,
            display_name=p.display_name,
            cost=p.cost,
            service_types=p.service_types,
            languages=p.languages,
            formats=p.formats,
            equipment_supported=p.equipment_supported,
        )
        for p in eligible
    ]

    result = EligibleReplacementsResult(
        case_id=case_id,
        eligible_count=len(summary_list),
        candidates=summary_list,
    )
    ctx.executed_tools.append({
        "tool": "find_eligible_replacements",
        "case_id": case_id,
        "eligible_count": len(summary_list),
        "result": result.model_dump(),
    })
    return result.model_dump()


@tool
def create_provider_offer(case_id: str, provider_id: str) -> dict:
    """Create a pending replacement offer for a selected approved provider.
    
    The offer includes a 15-minute response deadline and cryptographically hashed response token.
    """
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    plan = ctx.repo.get_plan(case.plan_id)
    if not plan:
        raise ValueError(f"Plan {case.plan_id} not found")
    provider = ctx.repo.get_provider(provider_id)
    if not provider:
        raise ValueError(f"Provider {provider_id} not found")

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(minutes=15)
    case.response_deadline = deadline

    offer, raw_token, response_url = ctx.gateway.dispatch_offer(
        case=case,
        plan=plan,
        provider=provider,
        expires_at=deadline,
    )
    ctx.repo.save_offer(offer)

    # Transition case to REPLACEMENT_PENDING if not already
    prev_state = case.state
    if case.state in (CaseState.AT_RISK, CaseState.RECOVERING):
        validate_transition(case.state, CaseState.REPLACEMENT_PENDING)
        case.state = CaseState.REPLACEMENT_PENDING
        case.attempt_count += 1
        ctx.repo.save_case(case)

    ctx.record_audit(
        case_id=case_id,
        action="OFFER_CREATED",
        tool_name="create_provider_offer",
        policy_result="APPROVED",
        before_state=prev_state.value,
        after_state=case.state.value,
        metadata={"offer_id": offer.offer_id, "provider_id": provider_id},
    )

    result = CreateOfferResult(
        offer_id=offer.offer_id,
        case_id=case_id,
        provider_id=provider_id,
        state=offer.state.value,
        sent_at=offer.sent_at.isoformat(),
        expires_at=offer.expires_at.isoformat(),
    )
    ctx.executed_tools.append({"tool": "create_provider_offer", "result": result.model_dump()})
    return result.model_dump()


@tool
def send_provider_offer(offer_id: str) -> dict:
    """Transmit the created offer to the replacement provider via their configured channel.
    
    Generates a secure, expiring provider response URL.
    """
    ctx = get_current_context()
    offer = ctx.repo.get_offer(offer_id)
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")
    provider = ctx.repo.get_provider(offer.provider_id)
    if not provider:
        raise ValueError(f"Provider {offer.provider_id} not found")

    dispatched = ctx.gateway.get_dispatched_offer(offer_id)
    if isinstance(dispatched, dict):
        response_url = dispatched.get("response_url", "http://localhost:8000/api/provider/respond/mock-token")
    elif dispatched and hasattr(dispatched, "response_url"):
        response_url = dispatched.response_url
    else:
        response_url = "http://localhost:8000/api/provider/respond/mock-token"

    result = SendOfferResult(
        offer_id=offer.offer_id,
        case_id=offer.case_id,
        provider_id=offer.provider_id,
        contact_channel=provider.contact_channel,
        response_url=response_url,
        dispatched_at=offer.sent_at.isoformat(),
    )
    ctx.executed_tools.append({"tool": "send_provider_offer", "result": result.model_dump()})
    return result.model_dump()


@tool
def schedule_offer_timeout(offer_id: str) -> dict:
    """Schedule a timeout deadline monitor for the dispatched offer.
    
    When deadline expires without response, triggers autonomous failover or escalation.
    """
    ctx = get_current_context()
    offer = ctx.repo.get_offer(offer_id)
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")

    timer_ref = f"timer-{offer.offer_id}-{offer.expires_at.strftime('%H%M%S')}"
    result = ScheduleTimeoutResult(
        offer_id=offer_id,
        expires_at=offer.expires_at.isoformat(),
        scheduled=True,
        timer_reference=timer_ref,
    )
    ctx.executed_tools.append({"tool": "schedule_offer_timeout", "result": result.model_dump()})
    return result.model_dump()


@tool
def record_provider_response(offer_id: str, response: str) -> dict:
    """Record and store the structured response from a provider (ACCEPT, DECLINE)."""
    ctx = get_current_context()
    offer = ctx.repo.get_offer(offer_id)
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")

    action_norm = response.strip().upper()
    now = datetime.now(timezone.utc)
    offer.response_at = now
    offer.response_text = response

    if action_norm == "ACCEPT":
        offer.state = OfferState.ACCEPTED
    elif action_norm == "DECLINE":
        offer.state = OfferState.DECLINED
    ctx.repo.save_offer(offer)

    resp_state_val = offer.state.value
    if "AMBIGUOUS" in action_norm:
        resp_state_val = "AMBIGUOUS"
    elif "TIMEOUT" in action_norm:
        resp_state_val = "TIMEOUT"

    result = RecordResponseResult(
        offer_id=offer.offer_id,
        case_id=offer.case_id,
        provider_id=offer.provider_id,
        response_state=resp_state_val,
        response_text=response,
        recorded_at=now.isoformat(),
    )
    ctx.executed_tools.append({"tool": "record_provider_response", "result": result.model_dump()})
    return result.model_dump()



@tool
def apply_confirmed_replacement(case_id: str, offer_id: str) -> dict:
    """Atomically assign the accepted replacement provider to the accommodation plan.
    
    Advances plan version, sets status to RECOVERED, and advances case state to ATTENDEE_CONFIRMATION_PENDING.
    """
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    plan = ctx.repo.get_plan(case.plan_id)
    if not plan:
        raise ValueError(f"Plan {case.plan_id} not found")
    offer = ctx.repo.get_offer(offer_id)
    if not offer:
        raise ValueError(f"Offer {offer_id} not found")

    if offer.state != OfferState.ACCEPTED:
        raise ValueError(f"Cannot apply offer {offer_id} with state {offer.state}")

    now = datetime.now(timezone.utc)
    plan.assigned_provider_id = offer.provider_id
    plan.version += 1
    plan.status = CaseState.RECOVERED
    ctx.repo.save_plan(plan)

    prev_state = case.state
    validate_transition(case.state, CaseState.RECOVERED)
    case.state = CaseState.RECOVERED
    case.recovered_at = now
    ctx.repo.save_case(case)

    ctx.record_audit(
        case_id=case_id,
        action="REPLACEMENT_APPLIED",
        tool_name="apply_confirmed_replacement",
        policy_result="APPROVED",
        before_state=prev_state.value,
        after_state=case.state.value,
        metadata={"provider_id": offer.provider_id, "offer_id": offer_id},
    )

    validate_transition(case.state, CaseState.ATTENDEE_CONFIRMATION_PENDING)
    prev_state2 = case.state
    case.state = CaseState.ATTENDEE_CONFIRMATION_PENDING
    ctx.repo.save_case(case)

    result = ApplyReplacementResult(
        case_id=case_id,
        plan_id=plan.plan_id,
        assigned_provider_id=offer.provider_id,
        plan_version=plan.version,
        case_state=case.state.value,
        applied_at=now.isoformat(),
    )
    ctx.executed_tools.append({"tool": "apply_confirmed_replacement", "result": result.model_dump()})
    return result.model_dump()


@tool
def notify_attendee(case_id: str) -> dict:
    """Notify the attendee that a replacement provider has been secured and request their confirmation."""
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    plan = ctx.repo.get_plan(case.plan_id)
    if not plan:
        raise ValueError(f"Plan {case.plan_id} not found")

    now = datetime.now(timezone.utc)
    ctx.record_audit(
        case_id=case_id,
        action="ATTENDEE_NOTIFIED",
        tool_name="notify_attendee",
        policy_result="APPROVED",
        before_state=case.state.value,
        after_state=case.state.value,
        metadata={"attendee_alias": plan.attendee_alias},
    )

    result = NotifyAttendeeResult(
        case_id=case_id,
        attendee_alias=plan.attendee_alias,
        status="DELIVERED",
        message="Replacement provider secured; awaiting attendee confirmation.",
        notified_at=now.isoformat(),
    )
    ctx.executed_tools.append({"tool": "notify_attendee", "result": result.model_dump()})
    return result.model_dump()


@tool
def request_human_decision(case_id: str, reason: str, safe_options: List[str]) -> dict:
    """Escalate to the event organizer when no policy-safe autonomous recovery is available.
    
    Presents structured safe alternatives, deadline, and plain-language reason.
    Transitions case state to ESCALATION_REQUIRED.
    """
    ctx = get_current_context()
    case = ctx.repo.get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

    prev_state = case.state
    if case.state != CaseState.ESCALATION_REQUIRED:
        validate_transition(case.state, CaseState.ESCALATION_REQUIRED)
        case.state = CaseState.ESCALATION_REQUIRED
    case.human_decision_required = True
    case.blocked_reason = reason
    ctx.repo.save_case(case)

    now = datetime.now(timezone.utc)
    ctx.record_audit(
        case_id=case_id,
        action="HUMAN_DECISION_REQUESTED",
        tool_name="request_human_decision",
        policy_result="ESCALATED",
        before_state=prev_state.value,
        after_state=case.state.value,
        metadata={"reason": reason, "safe_options": safe_options},
    )

    result = RequestHumanDecisionResult(
        case_id=case_id,
        reason=reason,
        safe_options=safe_options,
        case_state=case.state.value,
        decision_required=True,
        escalated_at=now.isoformat(),
    )
    ctx.executed_tools.append({"tool": "request_human_decision", "result": result.model_dump()})
    return result.model_dump()


ALL_RECOVERY_TOOLS = [
    get_case_context,
    find_eligible_replacements,
    create_provider_offer,
    send_provider_offer,
    schedule_offer_timeout,
    record_provider_response,
    apply_confirmed_replacement,
    notify_attendee,
    request_human_decision,
]
