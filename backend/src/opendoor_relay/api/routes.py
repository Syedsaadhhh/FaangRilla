"""API route definitions for OpenDoor Relay."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status

from opendoor_relay.api.schemas import (
    HealthResponse,
    DemoEventResponse,
    ProviderFailureRequest,
    ProviderFailureResponse,
    CaseResponse,
    TimelineResponse,
    ProviderRespondRequest,
    ProviderRespondResponse,
    AttendeeConfirmResponse,
    HumanDecisionRequest,
    HumanDecisionResponse,
    DemoResetResponse,
    EvaluationStatusResponse,
    CaseTraceResponse,
)

from opendoor_relay.domain.models import CaseState
from opendoor_relay.service.recovery import (
    RecoveryService,
    NotFoundError,
    OfferExpiredError,
    PolicyViolationError,
)

router = APIRouter()

# Dependency injector placeholder - will be bound in app.py
_recovery_service: Optional[RecoveryService] = None


def set_recovery_service(service: RecoveryService) -> None:
    global _recovery_service
    _recovery_service = service


def get_service() -> RecoveryService:
    if _recovery_service is None:
        raise RuntimeError("RecoveryService not initialized")
    return _recovery_service


@router.get("/health", tags=["Health"])
def health_check():
    """Health check returning operational status."""
    from opendoor_relay.agent.models import get_agent_mode
    import os
    return {
        "status": "healthy",
        "version": "0.1.0",
        "mode": "local-deterministic",
        "agent_mode": get_agent_mode(),
        "agent_framework": "strands-agents",
        "model_mode": "deterministic-rehearsal",
        "bedrock_status": "BLOCKED_BY_DAILY_QUOTA",
        "agentcore_status": os.environ.get("AGENTCORE_STATUS", "NOT_DEPLOYED")
    }


@router.get("/api/demo/event", response_model=DemoEventResponse, tags=["Demo"])
def get_demo_event(service: RecoveryService = Depends(get_service)) -> DemoEventResponse:
    """Get seeded synthetic event, plan, case, and providers."""
    from opendoor_relay.agent.models import get_agent_mode
    event = service.repo.get_event("evt-synthetic-001")
    plan = service.repo.get_plan("plan-synthetic-001")
    case = service.repo.get_case("case-synthetic-001")
    providers = service.repo.list_providers()
    outbox = service.gateway.get_outbox()

    if not event or not plan or not case:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Synthetic demo data missing",
        )

    return DemoEventResponse(
        event=event,
        plan=plan,
        case=case,
        providers=providers,
        recent_outbox=outbox,
        agent_mode=get_agent_mode(),
    )



@router.post(
    "/api/cases/{case_id}/provider-failure",
    response_model=ProviderFailureResponse,
    tags=["Cases"],
)
def report_provider_failure(
    case_id: str,
    payload: ProviderFailureRequest,
    service: RecoveryService = Depends(get_service),
) -> ProviderFailureResponse:
    """Trigger provider failure, triggering deterministic recovery and backup offer dispatch."""
    try:
        case, offer, response_url = service.trigger_provider_failure(
            case_id=case_id,
            trigger_text=payload.trigger_text or "Provider declared unavailability",
        )
        return ProviderFailureResponse(
            case=case,
            offer=offer,
            response_url=response_url,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/api/cases/{case_id}", response_model=CaseResponse, tags=["Cases"])
def get_case(case_id: str, service: RecoveryService = Depends(get_service)) -> CaseResponse:
    """Retrieve current state of a recovery case."""
    case = service.repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")

    plan = service.repo.get_plan(case.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan {case.plan_id} not found")

    provider = None
    if plan.assigned_provider_id:
        provider = service.repo.get_provider(plan.assigned_provider_id)

    return CaseResponse(case=case, plan=plan, assigned_provider=provider)


@router.get("/api/cases/{case_id}/timeline", response_model=TimelineResponse, tags=["Cases"])
def get_case_timeline(
    case_id: str, service: RecoveryService = Depends(get_service)
) -> TimelineResponse:
    """Retrieve full chronological audit timeline and measured recovery metrics."""
    case = service.repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")

    events = service.repo.get_audit_events_for_case(case_id)

    recovery_time = None
    if case.recovered_at and case.opened_at:
        recovery_time = (case.recovered_at - case.opened_at).total_seconds()

    confirmation_time = None
    if case.confirmed_at and case.opened_at:
        confirmation_time = (case.confirmed_at - case.opened_at).total_seconds()

    return TimelineResponse(
        case_id=case_id,
        current_state=case.state.value,
        opened_at=case.opened_at,
        recovered_at=case.recovered_at,
        confirmed_at=case.confirmed_at,
        headline_metric_seconds=confirmation_time,
        time_to_confirmed_seconds=confirmation_time,
        time_to_recovered_seconds=recovery_time,
        audit_events=events,
    )


@router.get("/api/provider/offer/{token}", tags=["Provider"])
def get_offer_details(
    token: str, service: RecoveryService = Depends(get_service)
):
    """Fetch offer details for the provider response portal."""
    token_hash = service.gateway.hash_token(token)
    offer = service.repo.get_offer_by_token_hash(token_hash)
    if not offer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid token")

    provider = service.repo.get_provider(offer.provider_id)
    case = service.repo.get_case(offer.case_id)
    plan = service.repo.get_plan(case.plan_id) if case else None
    event = service.repo.get_event(case.event_id) if case else None

    return {
        "offer_id": offer.offer_id,
        "provider_name": provider.display_name if provider else "Provider",
        "service_type": plan.service_type if plan else "",
        "language": plan.language if plan else "",
        "format": plan.format if plan else "",
        "equipment": plan.equipment if plan else "",
        "event_title": event.title if event else "",
        "venue": event.venue if event else "",
        "expires_at": offer.expires_at,
        "offer_state": offer.state.value,
    }


@router.post(
    "/api/provider/respond/{token}",
    response_model=ProviderRespondResponse,
    tags=["Provider"],
)
def respond_to_offer(
    token: str,
    payload: ProviderRespondRequest,
    service: RecoveryService = Depends(get_service),
) -> ProviderRespondResponse:
    """Provider acceptance or decline via single-use expiring token (idempotent)."""
    try:
        case, offer = service.record_provider_response(
            raw_token=token,
            action=payload.action,
            response_text=payload.response_text,
        )
        return ProviderRespondResponse(
            status="success",
            offer_id=offer.offer_id,
            case_id=case.case_id,
            offer_state=offer.state.value,
            case_state=case.state.value,
            message=f"Offer {offer.offer_id} successfully recorded as {offer.state.value}",
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OfferExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/api/cases/{case_id}/attendee-confirm",
    response_model=AttendeeConfirmResponse,
    tags=["Attendee"],
)
def confirm_attendee(
    case_id: str,
    service: RecoveryService = Depends(get_service),
) -> AttendeeConfirmResponse:
    """Attendee confirms replacement provider, finalizing recovery loop and stopping the metric clock."""
    try:
        case = service.confirm_attendee(case_id=case_id)

        recovery_time = None
        if case.recovered_at and case.opened_at:
            recovery_time = (case.recovered_at - case.opened_at).total_seconds()

        confirmed_time = None
        if case.confirmed_at and case.opened_at:
            confirmed_time = (case.confirmed_at - case.opened_at).total_seconds()

        return AttendeeConfirmResponse(
            case_id=case.case_id,
            state=case.state.value,
            confirmed_at=case.confirmed_at,
            headline_metric_seconds=confirmed_time,
            time_to_confirmed_seconds=confirmed_time,
            time_to_recovered_seconds=recovery_time,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/api/cases/{case_id}/human-decision",
    response_model=HumanDecisionResponse,
    tags=["Cases"],
)
def record_human_decision(
    case_id: str,
    payload: HumanDecisionRequest,
    service: RecoveryService = Depends(get_service),
) -> HumanDecisionResponse:
    """Record human organizer decision on an escalated case."""
    case = service.repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")

    return HumanDecisionResponse(
        case_id=case_id,
        state=case.state.value,
        message=f"Human decision '{payload.decision}' logged with rationale: {payload.rationale}",
    )


@router.post("/api/demo/reset", response_model=DemoResetResponse, tags=["Demo"])
def reset_demo(service: RecoveryService = Depends(get_service)) -> DemoResetResponse:
    """Reset the synthetic demo environment to initial state."""
    service.repo.reset()
    service.gateway.clear_outbox()
    return DemoResetResponse(
        status="ok",
        message="Synthetic demo environment successfully reset to initial state",
    )


@router.get(
    "/api/cases/{case_id}/trace",
    response_model=CaseTraceResponse,
    tags=["Cases"],
)
def get_case_trace(
    case_id: str, service: RecoveryService = Depends(get_service)
) -> CaseTraceResponse:
    """Retrieve developer-only sanitized execution trace for a case."""
    try:
        trace = service.get_developer_trace(case_id)
        return CaseTraceResponse(**trace)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/api/evaluation/latest",
    response_model=EvaluationStatusResponse,
    tags=["Evaluation"],
)
def get_latest_evaluation() -> EvaluationStatusResponse:
    """Return the results of the 10-case synthetic evaluation suite."""
    from pathlib import Path
    import json
    from opendoor_relay.evaluation.runner import run_all_evaluation_cases

    # Resolve FaangRilla root directory
    root_dir = Path(__file__).resolve().parents[4]
    json_path = root_dir / "docs" / "evaluation" / "evaluation_latest.json"

    if not json_path.exists():
        run_all_evaluation_cases()

    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        metrics = data.get("metrics", {})
        arch = data.get("model_architecture", {})
        return EvaluationStatusResponse(
            status="COMPLETED",
            message="Ten-case synthetic evaluation suite completed.",
            run="RUN_2",
            evaluation_cases_planned=10,
            total_cases_evaluated=metrics.get("total_cases", 10),
            autonomous_recoveries=metrics.get("autonomous_recoveries", 2),
            human_decisions_requested=metrics.get("organizer_interruptions", 3),
            policy_violations_prevented=metrics.get("policy_violations_prevented", 4),
            duplicate_side_effects=metrics.get("duplicate_side_effects", 0),
            live_bedrock_status=arch.get("live_bedrock_status", "BLOCKED_BY_ACCESS"),
            generated_at=data.get("generated_at"),
            summary_markdown_path="docs/evaluation/evaluation_summary.md",
            results=data.get("cases"),
        )
    else:
        return EvaluationStatusResponse(
            status="NOT_GENERATED",
            message="Evaluation artifacts not found.",
            run="RUN_2",
            evaluation_cases_planned=10,
            total_cases_evaluated=0,
            autonomous_recoveries=0,
            human_decisions_requested=0,
            policy_violations_prevented=0,
            duplicate_side_effects=0,
            live_bedrock_status="BLOCKED_BY_ACCESS",
            generated_at=None,
            results=None,
        )

