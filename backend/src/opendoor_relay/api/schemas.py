"""API request and response schemas."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from opendoor_relay.domain.models import (
    Event,
    AccommodationPlan,
    Provider,
    RecoveryCase,
    ProviderOffer,
    AuditEvent,
)


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    mode: str = "local-deterministic"
    agent_mode: str = "rehearsal"
    agent_framework: str = "strands-agents"
    model_mode: str = "deterministic-rehearsal"
    bedrock_status: str = "BLOCKED_BY_DAILY_QUOTA"
    agentcore_status: str = "NOT_DEPLOYED"


class DemoEventResponse(BaseModel):
    event: Event
    plan: AccommodationPlan
    case: RecoveryCase
    providers: List[Provider]
    recent_outbox: List[Dict[str, Any]] = Field(default_factory=list)
    agent_mode: str = "rehearsal"



class ProviderFailureRequest(BaseModel):
    trigger_text: Optional[str] = "Provider A declared unavailability 45 minutes before event readiness cutoff"


class ProviderFailureResponse(BaseModel):
    case: RecoveryCase
    offer: Optional[ProviderOffer]
    response_url: Optional[str]


class CaseResponse(BaseModel):
    case: RecoveryCase
    plan: AccommodationPlan
    assigned_provider: Optional[Provider] = None


class TimelineResponse(BaseModel):
    case_id: str
    current_state: str
    opened_at: Optional[datetime]
    recovered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    headline_metric_seconds: Optional[float] = Field(
        None, description="Headline metric: confirmed_at - opened_at (failure to attendee-confirmed recovery)"
    )
    time_to_confirmed_seconds: Optional[float] = Field(
        None, description="Headline metric: confirmed_at - opened_at"
    )
    time_to_recovered_seconds: Optional[float] = Field(
        None, description="Supporting metric: recovered_at - opened_at"
    )
    audit_events: List[AuditEvent]


class ProviderRespondRequest(BaseModel):
    action: str = Field(description="'ACCEPT' or 'DECLINE'")
    response_text: Optional[str] = None


class ProviderRespondResponse(BaseModel):
    status: str
    offer_id: str
    case_id: str
    offer_state: str
    case_state: str
    message: str


class AttendeeConfirmResponse(BaseModel):
    case_id: str
    state: str
    confirmed_at: datetime
    headline_metric_seconds: Optional[float] = Field(
        None, description="Headline metric: confirmed_at - opened_at"
    )
    time_to_confirmed_seconds: Optional[float] = Field(
        None, description="Headline metric: confirmed_at - opened_at"
    )
    time_to_recovered_seconds: Optional[float] = Field(
        None, description="Supporting metric: recovered_at - opened_at"
    )


class HumanDecisionRequest(BaseModel):
    decision: str
    rationale: str


class HumanDecisionResponse(BaseModel):
    case_id: str
    state: str
    message: str


class DemoResetResponse(BaseModel):
    status: str = "ok"
    message: str = "Synthetic demo environment reset to initial state"


class TraceRecordSchema(BaseModel):
    step: int
    timestamp: str
    actor: str
    action: str
    category: Optional[str] = "AUDIT_EVENT"
    tool_name: Optional[str] = None
    policy_result: str
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CaseTraceResponse(BaseModel):
    case_id: str
    agent_mode: str = "rehearsal"
    model_invocations: int = 0
    current_state: str
    opened_at: Optional[str] = None
    recovered_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    human_decision_required: bool = False
    blocked_reason: Optional[str] = None
    trace_record_count: int
    trace_records: List[TraceRecordSchema]


class EvaluationStatusResponse(BaseModel):
    status: str = "COMPLETED"
    message: str = "Ten-case synthetic evaluation suite completed."
    run: str = "RUN_2"
    evaluation_cases_planned: int = 10
    total_cases_evaluated: int = 10
    autonomous_recoveries: int = 2
    human_decisions_requested: int = 3
    policy_violations_prevented: int = 5
    duplicate_side_effects: int = 0
    live_bedrock_status: str = "BLOCKED_BY_ACCESS"
    generated_at: Optional[str] = None
    summary_markdown_path: Optional[str] = "docs/evaluation/evaluation_summary.md"
    results: Optional[List[Dict[str, Any]]] = None


