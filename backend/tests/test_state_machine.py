"""Tests for recovery state machine transitions and invariants."""

import pytest
from opendoor_relay.domain.models import CaseState
from opendoor_relay.domain.state_machine import (
    validate_transition,
    is_valid_transition,
    InvalidStateTransitionError,
)


def test_valid_state_transitions():
    """Verify that all contracted positive path transitions succeed."""
    # Hero sequence
    assert is_valid_transition(CaseState.CONFIRMED, CaseState.AT_RISK)
    assert is_valid_transition(CaseState.AT_RISK, CaseState.RECOVERING)
    assert is_valid_transition(CaseState.RECOVERING, CaseState.REPLACEMENT_PENDING)
    assert is_valid_transition(CaseState.REPLACEMENT_PENDING, CaseState.RECOVERED)
    assert is_valid_transition(CaseState.RECOVERED, CaseState.ATTENDEE_CONFIRMATION_PENDING)
    assert is_valid_transition(CaseState.ATTENDEE_CONFIRMATION_PENDING, CaseState.ATTENDEE_CONFIRMED)

    # Escalation branches
    assert is_valid_transition(CaseState.RECOVERING, CaseState.ESCALATION_REQUIRED)
    assert is_valid_transition(CaseState.REPLACEMENT_PENDING, CaseState.ESCALATION_REQUIRED)

    # Timeout branches
    assert is_valid_transition(CaseState.RECOVERING, CaseState.TIMED_OUT)
    assert is_valid_transition(CaseState.REPLACEMENT_PENDING, CaseState.TIMED_OUT)


def test_invalid_state_transitions():
    """Verify that illegal transitions raise InvalidStateTransitionError."""
    # Cannot jump directly from CONFIRMED to RECOVERED
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(CaseState.CONFIRMED, CaseState.RECOVERED)

    # Cannot jump backwards from ATTENDEE_CONFIRMED
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(CaseState.ATTENDEE_CONFIRMED, CaseState.AT_RISK)

    with pytest.raises(InvalidStateTransitionError):
        validate_transition(CaseState.ATTENDEE_CONFIRMED, CaseState.CONFIRMED)

    # Cannot transition directly from AT_RISK to REPLACEMENT_PENDING (must go through RECOVERING)
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(CaseState.AT_RISK, CaseState.REPLACEMENT_PENDING)

    # Terminal escalation state cannot transition
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(CaseState.ESCALATION_REQUIRED, CaseState.CONFIRMED)
