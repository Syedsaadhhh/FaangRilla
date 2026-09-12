"""Unit tests for the 9 typed recovery agent tools."""

import pytest
from datetime import datetime, timezone, timedelta
from opendoor_relay.domain.models import CaseState, OfferState
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.agent.tools import (
    ToolExecutionContext,
    set_current_context,
    reset_current_context,
    get_case_context,
    find_eligible_replacements,
    create_provider_offer,
    send_provider_offer,
    schedule_offer_timeout,
    record_provider_response,
    apply_confirmed_replacement,
    notify_attendee,
    request_human_decision,
)


@pytest.fixture
def tool_context():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    ctx = ToolExecutionContext(
        repo=repo,
        gateway=gateway,
        correlation_id="test-corr-tool-001",
        idempotency_key="idem-key-tool-001",
    )
    token = set_current_context(ctx)
    yield ctx
    reset_current_context(token)


def test_get_case_context_returns_typed_structure(tool_context):
    res = get_case_context(case_id="case-synthetic-001")
    assert isinstance(res, dict)
    assert res["case_id"] == "case-synthetic-001"
    assert res["service_type"] == "live_captioning"
    assert res["budget_ceiling"] == 300.0
    assert "service_type" in res["consent_scope"]
    assert "diagnosis" not in res  # Privacy minimization



def test_find_eligible_replacements(tool_context):
    res = find_eligible_replacements(case_id="case-synthetic-001")
    assert isinstance(res, dict)
    assert "candidates" in res
    assert res["eligible_count"] >= 1
    # Provider B should be eligible
    prov_ids = [p["provider_id"] for p in res["candidates"]]
    assert "prov-b-beacon" in prov_ids
    # Blocked Provider C must NOT be in eligible candidates
    assert "prov-c-apex-blocked" not in prov_ids


def test_create_and_send_provider_offer(tool_context):
    case = tool_context.repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    tool_context.repo.save_case(case)

    offer_res = create_provider_offer(
        case_id="case-synthetic-001",
        provider_id="prov-b-beacon",
    )
    assert offer_res["provider_id"] == "prov-b-beacon"
    assert offer_res["state"] == "PENDING"
    assert "offer_id" in offer_res

    send_res = send_provider_offer(offer_id=offer_res["offer_id"])
    assert "response_url" in send_res
    assert send_res["provider_id"] == "prov-b-beacon"

    timeout_res = schedule_offer_timeout(offer_id=offer_res["offer_id"])
    assert timeout_res["scheduled"] is True


def test_record_provider_response_and_apply_replacement(tool_context):
    case = tool_context.repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    tool_context.repo.save_case(case)

    offer_res = create_provider_offer(
        case_id="case-synthetic-001",
        provider_id="prov-b-beacon",
    )
    offer_id = offer_res["offer_id"]

    # Record response as ACCEPT
    resp_res = record_provider_response(offer_id=offer_id, response="ACCEPT")
    assert resp_res["response_state"] == "ACCEPTED"

    # Apply replacement
    apply_res = apply_confirmed_replacement(case_id="case-synthetic-001", offer_id=offer_id)
    assert apply_res["assigned_provider_id"] == "prov-b-beacon"
    assert apply_res["case_state"] == CaseState.ATTENDEE_CONFIRMATION_PENDING.value

    # Notify attendee
    notif_res = notify_attendee(case_id="case-synthetic-001")
    assert notif_res["status"] == "DELIVERED"


def test_request_human_decision_escalates_case(tool_context):
    case = tool_context.repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    tool_context.repo.save_case(case)

    res = request_human_decision(
        case_id="case-synthetic-001",
        reason="No equivalent provider available",
        safe_options=["Option A", "Option B"],
    )
    assert res["case_state"] == CaseState.ESCALATION_REQUIRED.value
    assert res["decision_required"] is True

    updated_case = tool_context.repo.get_case("case-synthetic-001")
    assert updated_case.state == CaseState.ESCALATION_REQUIRED
    assert updated_case.human_decision_required is True
