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


class DemoEventResponse(BaseModel):
    event: Event
    plan: AccommodationPlan
    case: RecoveryCase
    providers: List[Provider]
    recent_outbox: List[Dict[str, Any]] = Field(default_factory=list)


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


class EvaluationStatusResponse(BaseModel):
    status: str = "NOT_GENERATED"
    message: str = "Ten-case evaluation suite is scheduled for Run 2 and has not been executed yet."
    run: str = "RUN_1"
    evaluation_cases_planned: int = 10
    generated_at: Optional[datetime] = None
    results: Optional[List[Dict[str, Any]]] = None

