"""Local inbox provider gateway creating real expiring tokens and URLs without simulated emails."""

import secrets
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Optional


from opendoor_relay.domain.models import (
    RecoveryCase,
    AccommodationPlan,
    Provider,
    ProviderOffer,
    OfferState,
)
from opendoor_relay.provider_gateway.interface import ProviderGatewayInterface


class LocalInboxProviderGateway(ProviderGatewayInterface):
    """
    Local implementation of the provider gateway.
    Creates real single-purpose expiring tokens, hashes them for storage,
    and formats real local response URLs.
    """

    def __init__(self, frontend_base_url: str = "http://localhost:5173") -> None:
        self.frontend_base_url = frontend_base_url.rstrip("/")
        self._outbox: List[Dict[str, Any]] = []

    def hash_token(self, token: str) -> str:
        """Compute deterministic SHA-256 hash of response token."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def dispatch_offer(
        self,
        case: RecoveryCase,
        plan: AccommodationPlan,
        provider: Provider,
        expires_at: datetime,
    ) -> Tuple[ProviderOffer, str, str]:
        """Generate offer, secure random token, hash it, and record message in local outbox."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = self.hash_token(raw_token)
        now = datetime.now(timezone.utc)
        offer_id = f"ofr-{uuid.uuid4().hex[:8]}"

        offer = ProviderOffer(
            offer_id=offer_id,
            case_id=case.case_id,
            provider_id=provider.provider_id,
            state=OfferState.PENDING,
            sent_at=now,
            expires_at=expires_at,
            response_at=None,
            response_text=None,
            response_token_hash=token_hash,
        )

        response_url = f"{self.frontend_base_url}/provider/respond/{raw_token}"

        # Real local outbox entry (not a fake network email call)
        outbox_entry = {
            "offer_id": offer_id,
            "case_id": case.case_id,
            "provider_id": provider.provider_id,
            "provider_name": provider.display_name,
            "sent_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "raw_token": raw_token,
            "response_url": response_url,
            "disclosed_fields": {
                "service_type": plan.service_type,
                "language": plan.language,
                "format": plan.format,
                "equipment": plan.equipment,
            },
        }
        self._outbox.append(outbox_entry)

        return offer, raw_token, response_url

    def get_outbox(self) -> List[Dict[str, Any]]:
        return list(self._outbox)

    def get_dispatched_offer(self, offer_id: str) -> Optional[Dict[str, Any]]:
        for entry in self._outbox:
            if entry.get("offer_id") == offer_id:
                return entry
        return None

    def clear_outbox(self) -> None:
        self._outbox.clear()

