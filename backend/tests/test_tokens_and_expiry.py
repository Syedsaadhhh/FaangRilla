"""Tests for single-purpose tokens, SHA-256 hashing, and expiration handling."""

from datetime import datetime, timezone, timedelta
import pytest
from opendoor_relay.domain.models import CaseState
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.service.recovery import RecoveryService, OfferExpiredError, NotFoundError


def test_token_generation_and_hashing():
    gateway = LocalInboxProviderGateway(frontend_base_url="http://localhost:5173")
    repo = InMemoryRepository()
    case = repo.get_case("case-synthetic-001")
    plan = repo.get_plan("plan-synthetic-001")
    provider = repo.get_provider("prov-b-beacon")

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=15)

    offer, raw_token, url = gateway.dispatch_offer(case, plan, provider, expires_at)

    assert len(raw_token) >= 32
    assert offer.response_token_hash == gateway.hash_token(raw_token)
    assert url == f"http://localhost:5173/provider/respond/{raw_token}"
    assert len(gateway.get_outbox()) == 1


def test_expired_token_rejected():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    service = RecoveryService(repo=repo, gateway=gateway)

    # Trigger failure to dispatch offer
    case, offer, url = service.trigger_provider_failure("case-synthetic-001")
    assert offer is not None

    outbox = gateway.get_outbox()
    raw_token = outbox[0]["raw_token"]

    # Manually backdate offer expiration to the past
    offer.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    repo.save_offer(offer)

    # Attempting to respond with expired token must raise OfferExpiredError
    with pytest.raises(OfferExpiredError):
        service.record_provider_response(raw_token=raw_token, action="ACCEPT")


def test_unknown_token_rejected():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    service = RecoveryService(repo=repo, gateway=gateway)

    with pytest.raises(NotFoundError):
        service.record_provider_response(raw_token="completely_random_fake_token_12345", action="ACCEPT")
