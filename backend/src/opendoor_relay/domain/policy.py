"""Deterministic safety and policy evaluation engine."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from opendoor_relay.domain.models import AccommodationPlan, Provider


class PolicyResult(BaseModel):
    allowed: bool
    policy_name: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)


PROHIBITED_CONSENT_FIELDS = {
    "diagnosis",
    "medical_record",
    "health_history",
    "disability_rating",
    "clinical_note",
}


def check_equivalence(plan: AccommodationPlan, provider: Provider) -> PolicyResult:
    """Validate whether a provider satisfies the functional equivalence requirements of the plan."""
    if not provider.approved:
        return PolicyResult(
            allowed=False,
            policy_name="provider_approval",
            reason=f"Provider {provider.provider_id} ({provider.display_name}) is not approved",
            details={"approved": False},
        )

    if plan.service_type not in provider.service_types:
        return PolicyResult(
            allowed=False,
            policy_name="service_type_equivalence",
            reason=f"Provider does not support service type '{plan.service_type}' (supported: {provider.service_types})",
            details={"required": plan.service_type, "supported": provider.service_types},
        )

    if plan.language not in provider.languages:
        return PolicyResult(
            allowed=False,
            policy_name="language_equivalence",
            reason=f"Provider does not support language '{plan.language}' (supported: {provider.languages})",
            details={"required": plan.language, "supported": provider.languages},
        )

    if plan.format not in provider.formats:
        return PolicyResult(
            allowed=False,
            policy_name="format_equivalence",
            reason=f"Provider does not support format '{plan.format}' (supported: {provider.formats})",
            details={"required": plan.format, "supported": provider.formats},
        )

    if plan.equipment not in provider.equipment_supported:
        return PolicyResult(
            allowed=False,
            policy_name="equipment_equivalence",
            reason=f"Provider does not support equipment '{plan.equipment}' (supported: {provider.equipment_supported})",
            details={"required": plan.equipment, "supported": provider.equipment_supported},
        )

    return PolicyResult(
        allowed=True,
        policy_name="equivalence",
        reason="Provider satisfies all functional equivalence requirements",
        details={"provider_id": provider.provider_id},
    )


def check_budget(plan: AccommodationPlan, provider: Provider) -> PolicyResult:
    """Validate whether the provider cost is within the plan's authorized budget ceiling."""
    if provider.cost > plan.budget_ceiling:
        return PolicyResult(
            allowed=False,
            policy_name="budget_ceiling",
            reason=f"Provider cost (${provider.cost:.2f}) exceeds budget ceiling (${plan.budget_ceiling:.2f})",
            details={
                "provider_cost": provider.cost,
                "budget_ceiling": plan.budget_ceiling,
                "overage": provider.cost - plan.budget_ceiling,
            },
        )

    return PolicyResult(
        allowed=True,
        policy_name="budget_ceiling",
        reason=f"Provider cost (${provider.cost:.2f}) is within budget ceiling (${plan.budget_ceiling:.2f})",
        details={"provider_cost": provider.cost, "budget_ceiling": plan.budget_ceiling},
    )


def check_consent(plan: AccommodationPlan, disclosure_fields: List[str]) -> PolicyResult:
    """Validate that disclosure scope strictly respects attendee consent and contains no medical diagnosis."""
    # Check for explicitly prohibited medical/diagnostic terms
    for field in disclosure_fields:
        normalized = field.lower().strip()
        if normalized in PROHIBITED_CONSENT_FIELDS or "diagno" in normalized or "medical" in normalized:
            return PolicyResult(
                allowed=False,
                policy_name="privacy_boundary",
                reason=f"Prohibited health or diagnosis field '{field}' cannot be disclosed",
                details={"prohibited_field": field},
            )

    # Check that every requested field is in the approved consent scope
    allowed_scope = set(plan.consent_scope)
    unauthorized = [f for f in disclosure_fields if f not in allowed_scope]
    if unauthorized:
        return PolicyResult(
            allowed=False,
            policy_name="consent_scope",
            reason=f"Fields {unauthorized} exceed approved consent scope {plan.consent_scope}",
            details={"unauthorized_fields": unauthorized, "approved_scope": plan.consent_scope},
        )

    return PolicyResult(
        allowed=True,
        policy_name="consent_scope",
        reason="Disclosure is strictly within authorized consent scope",
        details={"disclosed_fields": disclosure_fields},
    )


def filter_eligible_providers(plan: AccommodationPlan, providers: List[Provider]) -> List[Provider]:
    """Return only providers that satisfy both equivalence and budget policies."""
    eligible: List[Provider] = []
    for provider in providers:
        eq_res = check_equivalence(plan, provider)
        if not eq_res.allowed:
            continue
        bg_res = check_budget(plan, provider)
        if not bg_res.allowed:
            continue
        eligible.append(provider)
    return eligible
