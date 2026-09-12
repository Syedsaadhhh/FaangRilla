"""FastAPI application initialization for OpenDoor Relay."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.service.recovery import RecoveryService
from opendoor_relay.api.routes import router, set_recovery_service


def create_app(
    repo: InMemoryRepository | None = None,
    gateway: LocalInboxProviderGateway | None = None,
) -> FastAPI:
    """Application factory for OpenDoor Relay API."""
    app = FastAPI(
        title="OpenDoor Relay API",
        description="Autonomous accessibility continuity engine for community events.",
        version="0.1.0",
    )

    # CORS configuration
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

    repository = repo or InMemoryRepository()
    gw = gateway or LocalInboxProviderGateway()
    service = RecoveryService(repo=repository, gateway=gw)
    set_recovery_service(service)

    app.include_router(router)
    return app


app = create_app()
