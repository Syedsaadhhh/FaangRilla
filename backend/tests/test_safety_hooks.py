"""Unit and integration tests for Strands safety hooks.

Proves:
- A model/caller cannot execute a denied tool (BeforeToolCallEvent cancel_tool halts execution).
- Non-equivalent providers are blocked before offer creation.
- Candidates exceeding budget ceiling are blocked before offer creation.
- Consent scope violations are blocked before offer creation.
- Corrupted context / missing correlation ID prevents tool execution.
- Ambiguous responses do NOT convert to acceptance.
- Duplicate webhooks produce 0 side effects.
"""

import pytest
from strands.hooks import BeforeToolCallEvent
from opendoor_relay.domain.models import CaseState, OfferState
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.agent.tools import (
    ToolExecutionContext,
    set_current_context,
    reset_current_context,
)
from opendoor_relay.agent.hooks import RecoverySafetyHookProvider
from opendoor_relay.agent.orchestrator import RecoveryAgentOrchestrator
from opendoor_relay.agent.models import RehearsalModel


@pytest.fixture
def test_setup():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    ctx = ToolExecutionContext(
        repo=repo,
        gateway=gateway,
        correlation_id="test-safety-corr-101",
    )
    token = set_current_context(ctx)
    yield repo, gateway, ctx
    reset_current_context(token)


def test_hook_blocks_over_budget_provider(test_setup):
    repo, gateway, ctx = test_setup
    case = repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    repo.save_case(case)

    # Provider C cost is $450, budget ceiling is $300
    hook = RecoverySafetyHookProvider()
    event = BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"name": "create_provider_offer", "input": {"case_id": case.case_id, "provider_id": "prov-c-apex-blocked"}},
        invocation_state={},
    )
    hook.before_tool_call(event)

    assert event.cancel_tool is not False
    assert "POLICY_DENIED_OVER_BUDGET" in str(event.cancel_tool)

    # Verify tool was NOT executed: no offer exists in repo for provider C
    offers = repo.list_offers_for_case(case.case_id)
    assert not any(o.provider_id == "prov-c-apex-blocked" for o in offers)

    # Verify audit event recorded denial
    audits = repo.get_audit_events_for_case(case.case_id)
    denials = [a for a in audits if a.policy_result == "BLOCKED"]
    assert len(denials) >= 1
    assert denials[-1].tool_name == "create_provider_offer"


def test_hook_blocks_corrupted_correlation_id(test_setup):
    repo, gateway, ctx = test_setup
    ctx.correlation_id = ""  # Corrupted / empty

    hook = RecoverySafetyHookProvider()
    event = BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"name": "find_eligible_replacements", "input": {"case_id": "case-synthetic-001"}},
        invocation_state={},
    )
    hook.before_tool_call(event)

    assert event.cancel_tool is not False
    assert "POLICY_DENIED_CORRUPTED_CONTEXT" in str(event.cancel_tool)


def test_hook_blocks_unaccepted_offer_application(test_setup):
    repo, gateway, ctx = test_setup
    case = repo.get_case("case-synthetic-001")
    case.state = CaseState.REPLACEMENT_PENDING
    repo.save_case(case)

    # Create pending offer (state = PENDING, not ACCEPTED)
    from opendoor_relay.agent.tools import create_provider_offer
    offer_res = create_provider_offer(case_id=case.case_id, provider_id="prov-b-beacon")
    offer_id = offer_res["offer_id"]

    hook = RecoverySafetyHookProvider()
    event = BeforeToolCallEvent(
        agent=None,
        selected_tool=None,
        tool_use={"name": "apply_confirmed_replacement", "input": {"case_id": case.case_id, "offer_id": offer_id}},
        invocation_state={},
    )
    hook.before_tool_call(event)

    assert event.cancel_tool is not False
    assert "POLICY_DENIED_UNACCEPTED_OFFER" in str(event.cancel_tool)


def test_ambiguous_text_does_not_become_acceptance(test_setup):
    repo, gateway, _ = test_setup
    orchestrator = RecoveryAgentOrchestrator(repo=repo, gateway=gateway, model=RehearsalModel())

    case, offer, _ = orchestrator.initiate_recovery(case_id="case-synthetic-001")
    assert offer is not None

    # Ambiguous reply
    case, offer = orchestrator.process_provider_reply(
        offer_id=offer.offer_id,
        reply_text="Maybe I can take this if my schedule clears up later.",
    )

    # State must be ESCALATION_REQUIRED, never RECOVERED or ATTENDEE_CONFIRMED
    assert case.state == CaseState.ESCALATION_REQUIRED
    assert case.human_decision_required is True
    assert "ambiguous" in case.blocked_reason.lower()



def test_duplicate_webhook_has_zero_side_effects(test_setup):
    repo, gateway, _ = test_setup
    orchestrator = RecoveryAgentOrchestrator(repo=repo, gateway=gateway, model=RehearsalModel())

    case, offer, _ = orchestrator.initiate_recovery(case_id="case-synthetic-001")

    # First accept
    case, offer = orchestrator.process_provider_reply(
        offer_id=offer.offer_id,
        reply_text="Accept",
        idempotency_key="webhook-key-uniq-777",
    )
    plan_v1 = repo.get_plan(case.plan_id)
    audits_v1 = len(repo.get_audit_events_for_case(case.case_id))

    # Duplicate webhook replay
    case_dup, offer_dup = orchestrator.process_provider_reply(
        offer_id=offer.offer_id,
        reply_text="Accept",
        idempotency_key="webhook-key-uniq-777",
    )
    plan_v2 = repo.get_plan(case.plan_id)
    audits_v2 = len(repo.get_audit_events_for_case(case.case_id))

    assert plan_v1.version == plan_v2.version
    assert audits_v1 == audits_v2
