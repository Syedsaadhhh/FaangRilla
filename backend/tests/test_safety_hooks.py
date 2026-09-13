"""Integration tests proving Strands safety hook interception through the real Agent loop.

Conforms strictly to the boss contract and Run 2.1 integrity requirement:
- A scripted RehearsalModel proposes create_provider_offer for an over-budget or non-equivalent provider.
- The proposal travels through a real strands.Agent invocation.
- BeforeToolCallEvent cancels it.
- Provider gateway dispatch count remains zero.
- No offer or plan mutation occurs.
- A BLOCKED audit event is persisted.
- Zero manual construction of BeforeToolCallEvent or manual calls to hook.before_tool_call().
"""

import pytest
from strands import Agent
from opendoor_relay.domain.models import CaseState, OfferState, Provider, AccommodationPlan, RecoveryCase
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.agent.tools import (
    ALL_RECOVERY_TOOLS,
    ToolExecutionContext,
    set_current_context,
    reset_current_context,
)
from opendoor_relay.agent.hooks import RecoverySafetyHookProvider
from opendoor_relay.agent.orchestrator import RecoveryAgentOrchestrator
from opendoor_relay.agent.models import RehearsalModel
from opendoor_relay.agent.prompts import AGENT_SYSTEM_CONTRACT


@pytest.fixture
def agent_environment():
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    ctx = ToolExecutionContext(
        repo=repo,
        gateway=gateway,
        correlation_id="test-safety-corr-agent-loop",
    )
    token = set_current_context(ctx)
    yield repo, gateway, ctx
    reset_current_context(token)


def test_real_strands_agent_blocks_over_budget_provider(agent_environment):
    """Prove that an over-budget candidate proposed by RehearsalModel inside strands.Agent is blocked by hook."""
    repo, gateway, ctx = agent_environment
    case = repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    repo.save_case(case)
    plan_before = repo.get_plan(case.plan_id)

    # prov-c-apex-blocked cost is $450, budget ceiling is $300
    scripted_model = RehearsalModel(
        scripted_steps=[
            {
                "tool": "create_provider_offer",
                "args": {"case_id": case.case_id, "provider_id": "prov-c-apex-blocked"},
            },
            {"text": "Agent loop terminated after safety hook intercepted tool."},
        ]
    )

    # Real strands.Agent instance
    agent = Agent(
        model=scripted_model,
        tools=ALL_RECOVERY_TOOLS,
        hooks=[RecoverySafetyHookProvider()],
        system_prompt=AGENT_SYSTEM_CONTRACT,
    )

    # Invoke real Strands Agent
    result = agent(f"Propose offer for case {case.case_id} provider prov-c-apex-blocked")

    # 1. Assert model invocation count > 0
    assert scripted_model.model_invocations > 0

    # 2. Assert BeforeToolCallEvent recorded the denial
    assert "create_provider_offer" in scripted_model.denied_tools

    # 3. Assert provider gateway dispatch count remains ZERO
    assert len(gateway.get_outbox()) == 0

    # 4. Assert NO offer mutation occurred in repository
    offers = repo.list_offers_for_case(case.case_id)
    assert len(offers) == 0

    # 5. Assert plan assigned provider and version are untouched
    plan_after = repo.get_plan(case.plan_id)
    assert plan_after.assigned_provider_id == plan_before.assigned_provider_id
    assert plan_after.version == plan_before.version

    # 6. Assert a BLOCKED audit event is persisted
    audits = repo.get_audit_events_for_case(case.case_id)
    denials = [a for a in audits if a.policy_result == "BLOCKED"]
    assert len(denials) >= 1
    assert denials[-1].action == "TOOL_CALL_DENIED_OVER_BUDGET"
    assert denials[-1].tool_name == "create_provider_offer"
    assert "450" in str(denials[-1].metadata)


def test_real_strands_agent_blocks_non_equivalent_provider(agent_environment):
    """Prove that a non-equivalent candidate proposed inside strands.Agent is blocked by hook."""
    repo, gateway, ctx = agent_environment
    case = repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    repo.save_case(case)

    # Add a non-equivalent provider (e.g. ASL interpretation instead of CART captioning)
    prov_mismatched = Provider(
        provider_id="prov-mismatched-service",
        display_name="ASL Interpreters Inc",
        service_types=["ASL interpretation"],  # Plan requires CART captioning
        languages=["English"],
        formats=["in-person"],
        equipment_supported=["Projector"],
        qualifications=["Certified ASL"],
        cost=200.0,
        approved=True,
    )
    repo.save_provider(prov_mismatched)

    scripted_model = RehearsalModel(
        scripted_steps=[
            {
                "tool": "create_provider_offer",
                "args": {"case_id": case.case_id, "provider_id": "prov-mismatched-service"},
            },
            {"text": "Agent loop terminated after safety hook intercepted tool."},
        ]
    )

    agent = Agent(
        model=scripted_model,
        tools=ALL_RECOVERY_TOOLS,
        hooks=[RecoverySafetyHookProvider()],
        system_prompt=AGENT_SYSTEM_CONTRACT,
    )

    agent(f"Propose offer for case {case.case_id} provider prov-mismatched-service")

    # Assert gateway dispatch count is 0
    assert len(gateway.get_outbox()) == 0

    # Assert no offer created
    assert len(repo.list_offers_for_case(case.case_id)) == 0

    # Assert BLOCKED audit event exists
    audits = repo.get_audit_events_for_case(case.case_id)
    denials = [a for a in audits if a.policy_result == "BLOCKED"]
    assert len(denials) >= 1
    assert denials[-1].action == "TOOL_CALL_DENIED_NON_EQUIVALENT"


def test_real_strands_agent_blocks_consent_violation(agent_environment):
    """Prove that empty or withdrawn attendee consent is strictly protected by hook inside strands.Agent."""
    repo, gateway, ctx = agent_environment
    case = repo.get_case("case-synthetic-001")
    case.state = CaseState.RECOVERING
    repo.save_case(case)

    plan = repo.get_plan(case.plan_id)
    plan.consent_scope = []  # Consent withdrawn / empty
    repo.save_plan(plan)

    scripted_model = RehearsalModel(
        scripted_steps=[
            {
                "tool": "create_provider_offer",
                "args": {"case_id": case.case_id, "provider_id": "prov-b-beacon"},
            },
            {"text": "Agent loop terminated after safety hook intercepted tool."},
        ]
    )

    agent = Agent(
        model=scripted_model,
        tools=ALL_RECOVERY_TOOLS,
        hooks=[RecoverySafetyHookProvider()],
        system_prompt=AGENT_SYSTEM_CONTRACT,
    )

    agent(f"Propose offer for case {case.case_id} provider prov-b-beacon")

    # Assert 0 gateway dispatches
    assert len(gateway.get_outbox()) == 0
    assert len(repo.list_offers_for_case(case.case_id)) == 0

    # Assert BLOCKED audit event exists
    audits = repo.get_audit_events_for_case(case.case_id)
    denials = [a for a in audits if a.policy_result == "BLOCKED"]
    assert len(denials) >= 1
    assert denials[-1].action == "TOOL_CALL_DENIED_CONSENT_VIOLATION"


def test_ambiguous_text_does_not_become_acceptance(agent_environment):
    """Prove that an ambiguous reply processed via Strands agent escalates and never accepts."""
    repo, gateway, _ = agent_environment
    orchestrator = RecoveryAgentOrchestrator(repo=repo, gateway=gateway, model=RehearsalModel())

    case, offer, _ = orchestrator.initiate_recovery(case_id="case-synthetic-001")
    assert offer is not None

    case, offer = orchestrator.process_provider_reply(
        offer_id=offer.offer_id,
        reply_text="Maybe I can take this if my schedule clears up later.",
    )

    # State must be ESCALATION_REQUIRED, never RECOVERED or ATTENDEE_CONFIRMED
    assert case.state == CaseState.ESCALATION_REQUIRED
    assert case.human_decision_required is True


def test_duplicate_webhook_has_zero_side_effects(agent_environment):
    """Prove that replaying acceptance webhook produces zero duplicate mutations."""
    repo, gateway, _ = agent_environment
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
