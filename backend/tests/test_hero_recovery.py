"""End-to-end integration test of the local hero recovery path."""

import pytest
from fastapi.testclient import TestClient
from opendoor_relay.api.app import create_app
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.domain.models import CaseState, OfferState


@pytest.fixture
def client_and_fixtures():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    app = create_app(repo=repo, gateway=gateway)
    client = TestClient(app)
    return client, repo, gateway


def test_hero_recovery_full_loop(client_and_fixtures):
    """
    Test the full contracted hero scenario:
    1. Health check is healthy.
    2. Seeded event and plan confirmed with Provider A.
    3. Provider A fails (declines).
    4. Deterministic policy blocks Provider C (over-budget $450).
    5. Provider B is offered ($250).
    6. Provider B accepts via real single-use token.
    7. Plan updates to Provider B, version increments.
    8. Attendee confirms.
    9. Recovery metric is recorded and verifiable.
    """
    client, repo, gateway = client_and_fixtures

    # 1. Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    # 2. Inspect initial state
    demo_resp = client.get("/api/demo/event")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    assert demo_data["plan"]["assigned_provider_id"] == "prov-a-starlight"
    assert demo_data["case"]["state"] == "CONFIRMED"

    # 3. Trigger Provider A failure
    failure_resp = client.post(
        "/api/cases/case-synthetic-001/provider-failure",
        json={"trigger_text": "Provider A declared sudden equipment malfunction 45m before cutoff"},
    )
    assert failure_resp.status_code == 200
    failure_data = failure_resp.json()
    assert failure_data["case"]["state"] == "REPLACEMENT_PENDING"
    assert failure_data["offer"]["provider_id"] == "prov-b-beacon"

    # 4. Check that outbox contains real local response URL
    outbox = gateway.get_outbox()
    assert len(outbox) == 1
    raw_token = outbox[0]["raw_token"]
    response_url = outbox[0]["response_url"]
    assert f"/provider/respond/{raw_token}" in response_url

    # 5. Fetch offer details via token
    offer_detail_resp = client.get(f"/api/provider/offer/{raw_token}")
    assert offer_detail_resp.status_code == 200
    assert offer_detail_resp.json()["provider_name"] == "Beacon Live Access (Synthetic)"

    # 6. Provider B accepts
    respond_resp = client.post(
        f"/api/provider/respond/{raw_token}",
        json={"action": "ACCEPT", "response_text": "Available and on the way with CART setup"},
    )
    assert respond_resp.status_code == 200
    respond_data = respond_resp.json()
    assert respond_data["offer_state"] == "ACCEPTED"
    assert respond_data["case_state"] == "ATTENDEE_CONFIRMATION_PENDING"

    # 7. Check plan is updated to Provider B
    case_resp = client.get("/api/cases/case-synthetic-001")
    assert case_resp.status_code == 200
    case_data = case_resp.json()
    assert case_data["plan"]["assigned_provider_id"] == "prov-b-beacon"
    assert case_data["plan"]["version"] == 2
    assert case_data["assigned_provider"]["display_name"] == "Beacon Live Access (Synthetic)"

    # 8. Replay Provider B acceptance to verify idempotency via HTTP endpoint
    replay_resp = client.post(
        f"/api/provider/respond/{raw_token}",
        json={"action": "ACCEPT", "response_text": "Duplicate request"},
    )
    assert replay_resp.status_code == 200
    assert replay_resp.json()["offer_state"] == "ACCEPTED"

    # 9. Attendee confirms replacement
    confirm_resp = client.post("/api/cases/case-synthetic-001/attendee-confirm")
    assert confirm_resp.status_code == 200
    confirm_data = confirm_resp.json()
    assert confirm_data["state"] == "ATTENDEE_CONFIRMED"
    assert confirm_data["time_to_recovered_seconds"] is not None
    assert confirm_data["time_to_confirmed_seconds"] is not None

    # 10. Verify timeline and measured recovery metric
    timeline_resp = client.get("/api/cases/case-synthetic-001/timeline")
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert timeline["current_state"] == "ATTENDEE_CONFIRMED"
    assert len(timeline["audit_events"]) >= 5
    assert timeline["time_to_recovered_seconds"] >= 0
    assert timeline["time_to_confirmed_seconds"] >= 0


def test_blocked_provider_c_cannot_be_applied(client_and_fixtures):
    """Verify that Provider C is blocked by deterministic budget policy ($450 > $300)."""
    _, repo, gateway = client_and_fixtures
    from opendoor_relay.service.recovery import RecoveryService

    service = RecoveryService(repo=repo, gateway=gateway)
    allowed, result = service.attempt_apply_provider("case-synthetic-001", "prov-c-apex-blocked")
    assert allowed is False
    assert result.policy_name == "budget_ceiling"
    assert "exceeds budget ceiling" in result.reason


def test_evaluation_endpoint_returns_explicit_not_generated_state(client_and_fixtures):
    """Verify that GET /api/evaluation/latest returns explicit typed NOT_GENERATED state in Run 1."""
    client, _, _ = client_and_fixtures
    resp = client.get("/api/evaluation/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "NOT_GENERATED"
    assert data["run"] == "RUN_1"
    assert data["results"] is None
    assert "Run 2" in data["message"]
