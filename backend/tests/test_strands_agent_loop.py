"""Integration test proving the load-bearing Strands Agent loop and developer trace.

Conforms strictly to Run 2.1 integrity requirements:
- A real strands.Agent using RehearsalModel proposes the required safe tool sequence.
- Model invocation count is greater than zero.
- Registered tools execute through Strands tool dispatcher.
- Provider B is offered and accepted.
- The attendee plan reaches ATTENDEE_CONFIRMED.
- The trace distinguishes MODEL_DECISION, TOOL_PROPOSED, POLICY_APPROVED, TOOL_EXECUTED, and STATE_CHANGED.
- Zero internal chain-of-thought exposed.
"""

import pytest
from opendoor_relay.domain.models import CaseState, OfferState
from opendoor_relay.repository.memory import InMemoryRepository
from opendoor_relay.provider_gateway.local_inbox import LocalInboxProviderGateway
from opendoor_relay.agent.orchestrator import RecoveryAgentOrchestrator
from opendoor_relay.agent.models import RehearsalModel


def test_successful_strands_agent_loop_end_to_end():
    """Prove that the recovery loop executes entirely through strands.Agent with structured trace categories."""
    repo = InMemoryRepository()
    gateway = LocalInboxProviderGateway()
    model = RehearsalModel()
    orchestrator = RecoveryAgentOrchestrator(repo=repo, gateway=gateway, model=model)

    case_id = "case-synthetic-001"

    # Step 1: Initiate recovery through real Strands Agent
    case, offer, response_url = orchestrator.initiate_recovery(
        case_id=case_id,
        trigger_text="Provider A equipment failure",
        correlation_id="test-strands-loop-corr",
    )

    # Assertions on model invocations and tool dispatch
    assert model.model_invocations > 0, "Expected model invocation count > 0"
    assert offer is not None, "Expected Provider B offer to be created"
    assert offer.provider_id == "prov-b-beacon"
    assert case.state == CaseState.REPLACEMENT_PENDING

    # Step 2: Provider B accepts via Strands Agent processing
    case, offer = orchestrator.process_provider_reply(
        offer_id=offer.offer_id,
        reply_text="Accept and confirmed with CART equipment",
        correlation_id="test-strands-loop-corr",
    )
    assert offer.state == OfferState.ACCEPTED
    assert case.state == CaseState.ATTENDEE_CONFIRMATION_PENDING

    # Step 3: Attendee confirms recovery
    case = orchestrator.confirm_attendee(case_id=case_id, correlation_id="test-strands-loop-corr")
    assert case.state == CaseState.ATTENDEE_CONFIRMED

    # Assert plan reached ATTENDEE_CONFIRMED with Provider B
    plan = repo.get_plan(case.plan_id)
    assert plan.assigned_provider_id == "prov-b-beacon"
    assert plan.status == CaseState.ATTENDEE_CONFIRMED
    assert plan.version == 2

    # Step 4: Verify developer trace distinctions
    trace = orchestrator.get_developer_trace(case_id)
    assert trace["case_id"] == case_id
    assert trace["current_state"] == "ATTENDEE_CONFIRMED"
    assert trace["model_invocations"] > 0
    assert trace["agent_mode"] == "rehearsal"

    trace_records = trace["trace_records"]
    categories = [r.get("category") for r in trace_records]

    # Must distinguish MODEL_DECISION, TOOL_PROPOSED, POLICY_APPROVED, TOOL_EXECUTED, and STATE_CHANGED
    assert "MODEL_DECISION" in categories, f"Expected MODEL_DECISION in {categories}"
    assert "TOOL_PROPOSED" in categories, f"Expected TOOL_PROPOSED in {categories}"
    assert "POLICY_APPROVED" in categories, f"Expected POLICY_APPROVED in {categories}"
    assert "TOOL_EXECUTED" in categories, f"Expected TOOL_EXECUTED in {categories}"
    assert "STATE_CHANGED" in categories, f"Expected STATE_CHANGED in {categories}"

    # Verify no secret or internal reasoning is exposed in metadata
    for r in trace_records:
        meta_str = str(r.get("metadata", {})).lower()
        assert "secret" not in meta_str
        assert "chain_of_thought" not in meta_str
        assert "reasoning" not in meta_str
