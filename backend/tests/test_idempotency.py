"""Tests proving zero duplicate side effects on repeated provider actions (idempotency)."""

import pytest
from opendoor_relay.domain.models import CaseState, OfferState
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.service.recovery import RecoveryService


def test_duplicate_provider_response_idempotency():
    """Verify that replaying Provider B's acceptance causes zero duplicate updates or side effects."""
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    service = RecoveryService(repo=repo, gateway=gateway)

    # 1. Trigger failure
    case, offer, url = service.trigger_provider_failure("case-synthetic-001")
    assert case.state == CaseState.REPLACEMENT_PENDING

    outbox = gateway.get_outbox()
    raw_token = outbox[0]["raw_token"]

    # 2. First acceptance
    case_first, offer_first = service.record_provider_response(
        raw_token=raw_token, action="ACCEPT", response_text="First acceptance call"
    )
    assert offer_first.state == OfferState.ACCEPTED
    assert case_first.state == CaseState.ATTENDEE_CONFIRMATION_PENDING

    # Record state snapshot
    plan_first = repo.get_plan(case.plan_id)
    audits_after_first = len(repo.get_audit_events_for_case(case.case_id))
    plan_version_first = plan_first.version
    assigned_provider_first = plan_first.assigned_provider_id

    # 3. Second acceptance (replayed request with same token)
    case_second, offer_second = service.record_provider_response(
        raw_token=raw_token, action="ACCEPT", response_text="Replayed duplicate call"
    )

    # State must be identical
    assert offer_second.state == OfferState.ACCEPTED
    assert case_second.state == CaseState.ATTENDEE_CONFIRMATION_PENDING

    # Invariants: no new audit events, no version increments, no duplicate provider assignments
    plan_second = repo.get_plan(case.plan_id)
    audits_after_second = len(repo.get_audit_events_for_case(case.case_id))

    assert audits_after_second == audits_after_first, "Duplicate call must not create duplicate audit events"
    assert plan_second.version == plan_version_first, "Plan version must not increment on replayed call"
    assert plan_second.assigned_provider_id == assigned_provider_first
