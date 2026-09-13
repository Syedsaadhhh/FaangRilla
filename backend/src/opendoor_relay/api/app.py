"""FastAPI application initialization for OpenDoor Relay."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opendoor_relay.api.routes import router, set_recovery_service
from opendoor_relay.provider_gateway.interface import ProviderGatewayInterface
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.repository.dynamodb import DynamoDBRepository
from opendoor_relay.repository.interface import RepositoryInterface
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.service.recovery import RecoveryService


def _default_repository() -> RepositoryInterface:
    table_name = os.environ.get("DYNAMODB_TABLE_NAME", "").strip()
    if table_name:
        return DynamoDBRepository(table_name)
    return InMemoryRepository()


def _default_gateway() -> ProviderGatewayInterface:
    frontend_url = os.environ.get("PUBLIC_APP_URL", "http://localhost:5173")
    return LocalInboxProviderGateway(frontend_base_url=frontend_url)


def create_app(
    repo: Optional[RepositoryInterface] = None,
    gateway: Optional[ProviderGatewayInterface] = None,
) -> FastAPI:
    """Application factory for OpenDoor Relay API."""
    app = FastAPI(
        title="OpenDoor Relay API",
        description="Autonomous accessibility continuity engine for community events.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    repository = repo or _default_repository()
    provider_gateway = gateway or _default_gateway()
    service = RecoveryService(repo=repository, gateway=provider_gateway)
    set_recovery_service(service)

    app.include_router(router)
    return app


app = create_app()

from mangum import Mangum

handler = Mangum(app)
