"""Recovery state machine validation and transitions."""

from typing import Dict, Set
from opendoor_relay.domain.models import CaseState


class InvalidStateTransitionError(ValueError):
    def __init__(self, from_state: CaseState, to_state: CaseState, reason: str = ""):
        message = f"Invalid state transition from {from_state.value} to {to_state.value}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.from_state = from_state
        self.to_state = to_state
        self.reason = reason


# Strict transition graph from boss specification:
# CONFIRMED -> AT_RISK -> RECOVERING -> REPLACEMENT_PENDING
# REPLACEMENT_PENDING -> RECOVERED -> ATTENDEE_CONFIRMATION_PENDING -> ATTENDEE_CONFIRMED
# RECOVERING | REPLACEMENT_PENDING -> ESCALATION_REQUIRED
# RECOVERING | REPLACEMENT_PENDING -> TIMED_OUT
VALID_TRANSITIONS: Dict[CaseState, Set[CaseState]] = {
    CaseState.CONFIRMED: {CaseState.AT_RISK},
    CaseState.AT_RISK: {CaseState.RECOVERING, CaseState.ESCALATION_REQUIRED},
    CaseState.RECOVERING: {
        CaseState.REPLACEMENT_PENDING,
        CaseState.ESCALATION_REQUIRED,
        CaseState.TIMED_OUT,
    },
    CaseState.REPLACEMENT_PENDING: {
        CaseState.RECOVERED,
        CaseState.ESCALATION_REQUIRED,
        CaseState.TIMED_OUT,
    },
    CaseState.RECOVERED: {CaseState.ATTENDEE_CONFIRMATION_PENDING},
    CaseState.ATTENDEE_CONFIRMATION_PENDING: {CaseState.ATTENDEE_CONFIRMED},
    CaseState.ATTENDEE_CONFIRMED: set(),
    CaseState.ESCALATION_REQUIRED: set(),
    CaseState.TIMED_OUT: {CaseState.RECOVERING, CaseState.ESCALATION_REQUIRED},
}


def is_valid_transition(current: CaseState, target: CaseState) -> bool:
    """Return whether transitioning from current to target state is allowed."""
    allowed = VALID_TRANSITIONS.get(current, set())
    return target in allowed


def validate_transition(current: CaseState, target: CaseState) -> None:
    """Raise InvalidStateTransitionError if transition is not permitted."""
    if not is_valid_transition(current, target):
        raise InvalidStateTransitionError(current, target)
