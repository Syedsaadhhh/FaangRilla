"""DynamoDB repository used by the AWS-hosted rehearsal API."""

from __future__ import annotations

import os
from typing import List, Optional, Type, TypeVar

import boto3
from boto3.dynamodb.conditions import Attr, Key
from pydantic import BaseModel

from opendoor_relay.domain.models import (
    AccommodationPlan,
    AuditEvent,
    Event,
    Provider,
    ProviderOffer,
    RecoveryCase,
)
from opendoor_relay.repository.interface import RepositoryInterface
from opendoor_relay.repository.memory import InMemoryRepository

ModelT = TypeVar("ModelT", bound=BaseModel)


class DynamoDBRepository(RepositoryInterface):
    """Small single-table adapter for the synthetic hackathon workflow."""

    def __init__(self, table_name: str, dynamodb_resource=None) -> None:
        if not table_name:
            raise ValueError("A DynamoDB table name is required")
        resource = dynamodb_resource or boto3.resource(
            "dynamodb",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )
        self.table = resource.Table(table_name)
        self._seed_if_empty()

    @staticmethod
    def _decode(item: Optional[dict], model: Type[ModelT]) -> Optional[ModelT]:
        if not item:
            return None
        return model.model_validate_json(item["payload"])

    def _put(
        self,
        *,
        pk: str,
        sk: str,
        entity_type: str,
        model: BaseModel,
        **attributes,
    ) -> None:
        item = {
            "pk": pk,
            "sk": sk,
            "entity_type": entity_type,
            "payload": model.model_dump_json(),
            **attributes,
        }
        self.table.put_item(Item=item)

    def _get(self, pk: str, sk: str, model: Type[ModelT]) -> Optional[ModelT]:
        response = self.table.get_item(
            Key={"pk": pk, "sk": sk},
            ConsistentRead=True,
        )
        return self._decode(response.get("Item"), model)

    def _scan_models(
        self,
        *,
        entity_type: str,
        model: Type[ModelT],
        extra_filter=None,
    ) -> List[ModelT]:
        filter_expression = Attr("entity_type").eq(entity_type)
        if extra_filter is not None:
            filter_expression = filter_expression & extra_filter

        items: list[dict] = []
        kwargs = {
            "FilterExpression": filter_expression,
            "ConsistentRead": True,
        }
        while True:
            response = self.table.scan(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        return [
            decoded
            for item in items
            if (decoded := self._decode(item, model)) is not None
        ]

    def _seed_if_empty(self) -> None:
        if self.get_case("case-synthetic-001") is not None:
            return

        seed = InMemoryRepository()
        event = seed.get_event("evt-synthetic-001")
        plan = seed.get_plan("plan-synthetic-001")
        case = seed.get_case("case-synthetic-001")

        if event:
            self.save_event(event)
        if plan:
            self.save_plan(plan)
        for provider in seed.list_providers():
            self.save_provider(provider)
        if case:
            self.save_case(case)

    def get_event(self, event_id: str) -> Optional[Event]:
        return self._get(f"EVENT#{event_id}", "METADATA", Event)

    def save_event(self, event: Event) -> None:
        self._put(
            pk=f"EVENT#{event.event_id}",
            sk="METADATA",
            entity_type="event",
            model=event,
        )

    def get_plan(self, plan_id: str) -> Optional[AccommodationPlan]:
        return self._get(f"PLAN#{plan_id}", "METADATA", AccommodationPlan)

    def save_plan(self, plan: AccommodationPlan) -> None:
        self._put(
            pk=f"PLAN#{plan.plan_id}",
            sk="METADATA",
            entity_type="plan",
            model=plan,
        )

    def get_provider(self, provider_id: str) -> Optional[Provider]:
        return self._get(f"PROVIDER#{provider_id}", "METADATA", Provider)

    def list_providers(self) -> List[Provider]:
        return self._scan_models(entity_type="provider", model=Provider)

    def save_provider(self, provider: Provider) -> None:
        self._put(
            pk=f"PROVIDER#{provider.provider_id}",
            sk="METADATA",
            entity_type="provider",
            model=provider,
        )

    def get_case(self, case_id: str) -> Optional[RecoveryCase]:
        return self._get(f"CASE#{case_id}", "METADATA", RecoveryCase)

    def save_case(self, case: RecoveryCase) -> None:
        self._put(
            pk=f"CASE#{case.case_id}",
            sk="METADATA",
            entity_type="case",
            model=case,
        )

    def get_offer(self, offer_id: str) -> Optional[ProviderOffer]:
        return self._get(f"OFFER#{offer_id}", "METADATA", ProviderOffer)

    def get_offer_by_token_hash(self, token_hash: str) -> Optional[ProviderOffer]:
        offers = self._scan_models(
            entity_type="offer",
            model=ProviderOffer,
            extra_filter=Attr("token_hash").eq(token_hash),
        )
        return offers[0] if offers else None

    def list_offers_for_case(self, case_id: str) -> List[ProviderOffer]:
        return self._scan_models(
            entity_type="offer",
            model=ProviderOffer,
            extra_filter=Attr("case_id").eq(case_id),
        )

    def save_offer(self, offer: ProviderOffer) -> None:
        self._put(
            pk=f"OFFER#{offer.offer_id}",
            sk="METADATA",
            entity_type="offer",
            model=offer,
            case_id=offer.case_id,
            token_hash=offer.response_token_hash,
            ttl=int(offer.expires_at.timestamp()),
        )

    def add_audit_event(self, event: AuditEvent) -> None:
        self._put(
            pk=f"CASE#{event.case_id}",
            sk=f"AUDIT#{event.timestamp.isoformat()}#{event.audit_id}",
            entity_type="audit",
            model=event,
        )

    def get_audit_events_for_case(self, case_id: str) -> List[AuditEvent]:
        response = self.table.query(
            KeyConditionExpression=(
                Key("pk").eq(f"CASE#{case_id}")
                & Key("sk").begins_with("AUDIT#")
            ),
            ConsistentRead=True,
        )
        events = [
            decoded
            for item in response.get("Items", [])
            if (decoded := self._decode(item, AuditEvent)) is not None
        ]
        return sorted(events, key=lambda event: event.timestamp)

    def reset(self) -> None:
        keys: list[dict] = []
        kwargs = {"ProjectionExpression": "pk, sk"}
        while True:
            response = self.table.scan(**kwargs)
            keys.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key

        if keys:
            with self.table.batch_writer() as batch:
                for key in keys:
                    batch.delete_item(Key={"pk": key["pk"], "sk": key["sk"]})
        self._seed_if_empty()
