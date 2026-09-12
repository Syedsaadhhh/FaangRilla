"""Tests for developer-only trace endpoint and trace sanitizer."""

import pytest
from fastapi.testclient import TestClient
from opendoor_relay.api.app import app
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.service.recovery import RecoveryService
from opendoor_relay.api.routes import set_recovery_service


@pytest.fixture
def test_client():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    service = RecoveryService(repo=repo, gateway=gateway)
    set_recovery_service(service)
    client = TestClient(app)
    return client, service


def test_get_case_trace_structure_and_sanitization(test_client):
    client, service = test_client

    # 1. Trigger failure to create initial recovery trace
    fail_res = client.post(
        "/api/cases/case-synthetic-001/provider-failure",
        json={"trigger_text": "Provider A declared illness"},
    )
    assert fail_res.status_code == 200

    # 2. Query trace endpoint
    trace_res = client.get("/api/cases/case-synthetic-001/trace")
    assert trace_res.status_code == 200
    data = trace_res.json()

    assert data["case_id"] == "case-synthetic-001"
    assert data["trace_record_count"] >= 2
    assert "trace_records" in data

    # Verify sanitization: no raw tokens or secrets in records
    for rec in data["trace_records"]:
        assert "step" in rec
        assert "timestamp" in rec
        assert "actor" in rec
        assert "action" in rec
        assert "policy_result" in rec
        meta_str = str(rec.get("metadata", {})).lower()
        assert "secret" not in meta_str
        assert "raw_token" not in meta_str
        assert "password" not in meta_str


def test_get_case_trace_not_found(test_client):
    client, _ = test_client
    res = client.get("/api/cases/non-existent-case-id/trace")
    assert res.status_code == 404
