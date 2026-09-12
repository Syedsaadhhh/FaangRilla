"""Typed domain models conforming to the OpenDoor Relay specification."""

from __future__ import annotations
from enum import Enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CaseState(str, Enum):
    CONFIRMED = "CONFIRMED"
    AT_RISK = "AT_RISK"
    RECOVERING = "RECOVERING"
    REPLACEMENT_PENDING = "REPLACEMENT_PENDING"
    RECOVERED = "RECOVERED"
    ATTENDEE_CONFIRMATION_PENDING = "ATTENDEE_CONFIRMATION_PENDING"
    ATTENDEE_CONFIRMED = "ATTENDEE_CONFIRMED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    TIMED_OUT = "TIMED_OUT"


class OfferState(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"
    PROVIDER = "PROVIDER"
    ATTENDEE = "ATTENDEE"
    ORGANIZER = "ORGANIZER"


class Event(BaseModel):
    event_id: str
    title: str
    venue: str
    starts_at: datetime
    readiness_deadline: datetime
    timezone: str = "UTC"


class AccommodationPlan(BaseModel):
    plan_id: str
    event_id: str
    attendee_alias: str
    functional_need: str
    service_type: str
    language: str
    format: str
    equipment: str
    consent_scope: List[str]
    budget_ceiling: float
    assigned_provider_id: Optional[str] = None
    status: CaseState = CaseState.CONFIRMED
    version: int = 1


class AvailabilityWindow(BaseModel):
    start_time: datetime
    end_time: datetime


class Provider(BaseModel):
    provider_id: str
    display_name: str
    service_types: List[str]
    languages: List[str]
    formats: List[str]
    equipment_supported: List[str]
    qualifications: List[str]
    availability_windows: List[AvailabilityWindow] = Field(default_factory=list)
    cost: float
    approved: bool = True
    contact_channel: str = "email"


class RecoveryCase(BaseModel):
    case_id: str
    event_id: str
    plan_id: str
    trigger_type: str
    trigger_text: str
    state: CaseState = CaseState.CONFIRMED
    opened_at: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    attempt_count: int = 0
    idempotency_key: Optional[str] = None
    blocked_reason: Optional[str] = None
    human_decision_required: bool = False


class ProviderOffer(BaseModel):
    offer_id: str
    case_id: str
    provider_id: str
    state: OfferState = OfferState.PENDING
    sent_at: datetime
    expires_at: datetime
    response_at: Optional[datetime] = None
    response_text: Optional[str] = None
    response_token_hash: str


class AuditEvent(BaseModel):
    audit_id: str
    case_id: str
    timestamp: datetime
    actor_type: ActorType
    action: str
    tool_name: Optional[str] = None
    policy_result: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    correlation_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
