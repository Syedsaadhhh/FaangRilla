"""Unit tests for deterministic equivalence, budget, and consent policies."""

import pytest
from opendoor_relay.domain.models import AccommodationPlan, Provider, CaseState
from opendoor_relay.domain.policy import (
    check_equivalence,
    check_budget,
    check_consent,
    filter_eligible_providers,
)


@pytest.fixture
def base_plan() -> AccommodationPlan:
    return AccommodationPlan(
        plan_id="plan-test-01",
        event_id="evt-test-01",
        attendee_alias="Attendee Test",
        functional_need="Live CART captioning",
        service_type="live_captioning",
        language="en-US",
        format="CART",
        equipment="projector_screen_hdmi",
        consent_scope=["service_type", "language", "format", "equipment"],
        budget_ceiling=300.0,
        status=CaseState.CONFIRMED,
        version=1,
    )


@pytest.fixture
def provider_b() -> Provider:
    return Provider(
        provider_id="prov-b",
        display_name="Beacon Live Access",
        service_types=["live_captioning"],
        languages=["en-US"],
        formats=["CART"],
        equipment_supported=["projector_screen_hdmi"],
        qualifications=["Master CART Specialist"],
        cost=250.0,
        approved=True,
    )


@pytest.fixture
def provider_c_overbudget() -> Provider:
    return Provider(
        provider_id="prov-c",
        display_name="Apex Specialized Services",
        service_types=["live_captioning"],
        languages=["en-US"],
        formats=["CART"],
        equipment_supported=["projector_screen_hdmi"],
        qualifications=["Elite Partner"],
        cost=450.0,  # Over budget ceiling ($300.0)
        approved=True,
    )


def test_equivalence_success(base_plan: AccommodationPlan, provider_b: Provider):
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is True
    assert res.policy_name == "equivalence"


def test_equivalence_service_mismatch(base_plan: AccommodationPlan, provider_b: Provider):
    provider_b.service_types = ["asl_interpretation"]
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is False
    assert res.policy_name == "service_type_equivalence"


def test_equivalence_language_mismatch(base_plan: AccommodationPlan, provider_b: Provider):
    provider_b.languages = ["es-MX"]
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is False
    assert res.policy_name == "language_equivalence"


def test_equivalence_format_mismatch(base_plan: AccommodationPlan, provider_b: Provider):
    provider_b.formats = ["audio_description"]
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is False
    assert res.policy_name == "format_equivalence"


def test_equivalence_equipment_mismatch(base_plan: AccommodationPlan, provider_b: Provider):
    provider_b.equipment_supported = ["bluetooth_headphones"]
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is False
    assert res.policy_name == "equipment_equivalence"


def test_unapproved_provider_blocked(base_plan: AccommodationPlan, provider_b: Provider):
    provider_b.approved = False
    res = check_equivalence(base_plan, provider_b)
    assert res.allowed is False
    assert res.policy_name == "provider_approval"


def test_budget_boundary_within_ceiling(base_plan: AccommodationPlan, provider_b: Provider):
    res = check_budget(base_plan, provider_b)
    assert res.allowed is True
    assert res.policy_name == "budget_ceiling"


def test_budget_boundary_exceeded_blocks_provider_c(
    base_plan: AccommodationPlan, provider_c_overbudget: Provider
):
    res = check_budget(base_plan, provider_c_overbudget)
    assert res.allowed is False
    assert res.policy_name == "budget_ceiling"
    assert "exceeds budget ceiling" in res.reason


def test_budget_dynamic_ceiling_from_plan(base_plan: AccommodationPlan, provider_b: Provider, provider_c_overbudget: Provider):
    """Prove that policy reads budget_ceiling dynamically from the plan, not from a hardcoded constant."""
    # When ceiling is increased to $500, Provider C ($450) becomes permitted
    base_plan.budget_ceiling = 500.0
    res_c = check_budget(base_plan, provider_c_overbudget)
    assert res_c.allowed is True

    # When ceiling is reduced to $200, Provider B ($250) becomes blocked
    base_plan.budget_ceiling = 200.0
    res_b = check_budget(base_plan, provider_b)
    assert res_b.allowed is False
    assert "exceeds budget ceiling" in res_b.reason


def test_consent_scope_permitted(base_plan: AccommodationPlan):
    fields = ["service_type", "language", "format"]
    res = check_consent(base_plan, fields)
    assert res.allowed is True


def test_consent_scope_unauthorized_fields_blocked(base_plan: AccommodationPlan):
    fields = ["service_type", "attendee_home_address"]
    res = check_consent(base_plan, fields)
    assert res.allowed is False
    assert res.policy_name == "consent_scope"


def test_consent_scope_diagnosis_strictly_prohibited(base_plan: AccommodationPlan):
    fields = ["service_type", "diagnosis"]
    res = check_consent(base_plan, fields)
    assert res.allowed is False
    assert res.policy_name == "privacy_boundary"
    assert "Prohibited" in res.reason


def test_filter_eligible_providers(
    base_plan: AccommodationPlan, provider_b: Provider, provider_c_overbudget: Provider
):
    candidates = [provider_b, provider_c_overbudget]
    eligible = filter_eligible_providers(base_plan, candidates)
    # Only Provider B is eligible because Provider C exceeds budget
    assert len(eligible) == 1
    assert eligible[0].provider_id == provider_b.provider_id
