"""Thread-safe in-memory repository implementation with seeded synthetic demo data."""

import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from copy import deepcopy

from opendoor_relay.domain.models import (
    Event,
    AccommodationPlan,
    Provider,
    RecoveryCase,
    ProviderOffer,
    AuditEvent,
    CaseState,
)
from opendoor_relay.repository.interface import RepositoryInterface


class InMemoryRepository(RepositoryInterface):
    """In-memory data store for local development, unit tests, and Run 1."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: Dict[str, Event] = {}
        self._plans: Dict[str, AccommodationPlan] = {}
        self._providers: Dict[str, Provider] = {}
        self._cases: Dict[str, RecoveryCase] = {}
        self._offers: Dict[str, ProviderOffer] = {}
        self._offers_by_token_hash: Dict[str, str] = {}  # token_hash -> offer_id
        self._audit_events: List[AuditEvent] = []
        self._seed_data()

    def _seed_data(self) -> None:
        """Seed authoritative synthetic demo fixtures."""
        now = datetime.now(timezone.utc)

        # 1. Seeded Synthetic Workshop
        event = Event(
            event_id="evt-synthetic-001",
            title="Community Tech & Accessibility Workshop (Synthetic Demo)",
            venue="Civic Auditorium - Room 204",
            starts_at=now + timedelta(hours=3),
            readiness_deadline=now + timedelta(hours=2, minutes=15),
            timezone="America/New_York",
        )
        self._events[event.event_id] = event

        # 2. Seeded Synthetic Accommodation Plan
        plan = AccommodationPlan(
            plan_id="plan-synthetic-001",
            event_id=event.event_id,
            attendee_alias="Attendee Taylor (Synthetic)",
            functional_need="Live real-time CART captioning and front-row reserved seating",
            service_type="live_captioning",
            language="en-US",
            format="CART",
            equipment="projector_screen_hdmi",
            consent_scope=["service_type", "language", "format", "equipment", "event_title", "venue"],
            budget_ceiling=300.0,
            assigned_provider_id="prov-a-starlight",
            status=CaseState.CONFIRMED,
            version=1,
        )
        self._plans[plan.plan_id] = plan

        # 3. Provider A: Initial confirmed provider (will decline)
        prov_a = Provider(
            provider_id="prov-a-starlight",
            display_name="Starlight Captioning Co. (Synthetic)",
            service_types=["live_captioning"],
            languages=["en-US"],
            formats=["CART", "remote_stream"],
            equipment_supported=["projector_screen_hdmi", "usb_c_hub"],
            qualifications=["Certified CART Provider"],
            cost=220.0,
            approved=True,
            contact_channel="email",
        )
        self._providers[prov_a.provider_id] = prov_a

        # 4. Provider B: Eligible, approved backup provider
        prov_b = Provider(
            provider_id="prov-b-beacon",
            display_name="Beacon Live Access (Synthetic)",
            service_types=["live_captioning", "asl_interpretation"],
            languages=["en-US", "es-MX"],
            formats=["CART"],
            equipment_supported=["projector_screen_hdmi", "aux_audio"],
            qualifications=["Master CART Specialist", "State Registry Approved"],
            cost=250.0,
            approved=True,
            contact_channel="email",
        )
        self._providers[prov_b.provider_id] = prov_b

        # 5. Provider C: Intentionally blocked provider (exceeds $300 budget ceiling)
        prov_c = Provider(
            provider_id="prov-c-apex-blocked",
            display_name="Apex Specialized Services (Synthetic - Intentionally Blocked)",
            service_types=["live_captioning"],
            languages=["en-US"],
            formats=["CART"],
            equipment_supported=["projector_screen_hdmi"],
            qualifications=["Elite Access Partner"],
            cost=450.0,  # $450 > $300 ceiling
            approved=True,
            contact_channel="email",
        )
        self._providers[prov_c.provider_id] = prov_c

        # 6. Seeded Recovery Case
        case = RecoveryCase(
            case_id="case-synthetic-001",
            event_id=event.event_id,
            plan_id=plan.plan_id,
            trigger_type="none",
            trigger_text="Initial confirmed state",
            state=CaseState.CONFIRMED,
            opened_at=None,
            response_deadline=None,
            recovered_at=None,
            confirmed_at=None,
            attempt_count=0,
            idempotency_key=None,
            blocked_reason=None,
            human_decision_required=False,
        )
        self._cases[case.case_id] = case

    def get_event(self, event_id: str) -> Optional[Event]:
        with self._lock:
            event = self._events.get(event_id)
            return deepcopy(event) if event else None

    def save_event(self, event: Event) -> None:
        with self._lock:
            self._events[event.event_id] = deepcopy(event)

    def get_plan(self, plan_id: str) -> Optional[AccommodationPlan]:
        with self._lock:
            plan = self._plans.get(plan_id)
            return deepcopy(plan) if plan else None

    def save_plan(self, plan: AccommodationPlan) -> None:
        with self._lock:
            self._plans[plan.plan_id] = deepcopy(plan)

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        with self._lock:
            provider = self._providers.get(provider_id)
            return deepcopy(provider) if provider else None

    def list_providers(self) -> List[Provider]:
        with self._lock:
            return [deepcopy(p) for p in self._providers.values()]

    def save_provider(self, provider: Provider) -> None:
        with self._lock:
            self._providers[provider.provider_id] = deepcopy(provider)

    def get_case(self, case_id: str) -> Optional[RecoveryCase]:
        with self._lock:
            case = self._cases.get(case_id)
            return deepcopy(case) if case else None

    def save_case(self, case: RecoveryCase) -> None:
        with self._lock:
            self._cases[case.case_id] = deepcopy(case)

    def get_offer(self, offer_id: str) -> Optional[ProviderOffer]:
        with self._lock:
            offer = self._offers.get(offer_id)
            return deepcopy(offer) if offer else None

    def get_offer_by_token_hash(self, token_hash: str) -> Optional[ProviderOffer]:
        with self._lock:
            offer_id = self._offers_by_token_hash.get(token_hash)
            if not offer_id:
                return None
            offer = self._offers.get(offer_id)
            return deepcopy(offer) if offer else None

    def list_offers_for_case(self, case_id: str) -> List[ProviderOffer]:
        with self._lock:
            return [
                deepcopy(o) for o in self._offers.values() if o.case_id == case_id
            ]

    def save_offer(self, offer: ProviderOffer) -> None:
        with self._lock:
            self._offers[offer.offer_id] = deepcopy(offer)
            self._offers_by_token_hash[offer.response_token_hash] = offer.offer_id

    def add_audit_event(self, event: AuditEvent) -> None:
        with self._lock:
            self._audit_events.append(deepcopy(event))

    def get_audit_events_for_case(self, case_id: str) -> List[AuditEvent]:
        with self._lock:
            return [
                deepcopy(a)
                for a in sorted(self._audit_events, key=lambda x: x.timestamp)
                if a.case_id == case_id
            ]

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
            self._plans.clear()
            self._providers.clear()
            self._cases.clear()
            self._offers.clear()
            self._offers_by_token_hash.clear()
            self._audit_events.clear()
            self._seed_data()
