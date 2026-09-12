"""Abstract repository interface for OpenDoor Relay storage."""

from abc import ABC, abstractmethod
from typing import List, Optional
from opendoor_relay.domain.models import (
    Event,
    AccommodationPlan,
    Provider,
    RecoveryCase,
    ProviderOffer,
    AuditEvent,
)


class RepositoryInterface(ABC):
    """Authoritative persistence contract for OpenDoor Relay."""

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[Event]:
        """Fetch event by ID."""
        pass

    @abstractmethod
    def save_event(self, event: Event) -> None:
        """Upsert an event."""
        pass

    @abstractmethod
    def get_plan(self, plan_id: str) -> Optional[AccommodationPlan]:
        """Fetch accommodation plan by ID."""
        pass

    @abstractmethod
    def save_plan(self, plan: AccommodationPlan) -> None:
        """Upsert an accommodation plan."""
        pass

    @abstractmethod
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Fetch provider by ID."""
        pass

    @abstractmethod
    def list_providers(self) -> List[Provider]:
        """List all available providers."""
        pass

    @abstractmethod
    def save_provider(self, provider: Provider) -> None:
        """Upsert a provider."""
        pass

    @abstractmethod
    def get_case(self, case_id: str) -> Optional[RecoveryCase]:
        """Fetch recovery case by ID."""
        pass

    @abstractmethod
    def save_case(self, case: RecoveryCase) -> None:
        """Upsert a recovery case."""
        pass

    @abstractmethod
    def get_offer(self, offer_id: str) -> Optional[ProviderOffer]:
        """Fetch provider offer by ID."""
        pass

    @abstractmethod
    def get_offer_by_token_hash(self, token_hash: str) -> Optional[ProviderOffer]:
        """Fetch provider offer by single-use token hash."""
        pass

    @abstractmethod
    def list_offers_for_case(self, case_id: str) -> List[ProviderOffer]:
        """List all offers dispatched for a given case."""
        pass

    @abstractmethod
    def save_offer(self, offer: ProviderOffer) -> None:
        """Upsert a provider offer."""
        pass

    @abstractmethod
    def add_audit_event(self, event: AuditEvent) -> None:
        """Record an immutable audit event."""
        pass

    @abstractmethod
    def get_audit_events_for_case(self, case_id: str) -> List[AuditEvent]:
        """Fetch all audit events for a case in chronological order."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the data store to initial seeded state (demo use only)."""
        pass
