"""Provider gateway interface for dispatching offers and verifying response tokens."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple, Dict, Any, List
from opendoor_relay.domain.models import RecoveryCase, AccommodationPlan, Provider, ProviderOffer


class ProviderGatewayInterface(ABC):
    """Interface for outbound provider communication and tokenized response link generation."""

    @abstractmethod
    def dispatch_offer(
        self,
        case: RecoveryCase,
        plan: AccommodationPlan,
        provider: Provider,
        expires_at: datetime,
    ) -> Tuple[ProviderOffer, str, str]:
        """
        Generate an offer with a cryptographically secure single-use token.
        Returns: (ProviderOffer, raw_token, provider_response_url)
        """
        pass

    @abstractmethod
    def hash_token(self, token: str) -> str:
        """Hash token using SHA-256 for secure persistence."""
        pass

    @abstractmethod
    def get_outbox(self) -> List[Dict[str, Any]]:
        """Retrieve dispatched messages for inspection in tests and local development."""
        pass

    @abstractmethod
    def clear_outbox(self) -> None:
        """Clear local outbox."""
        pass
