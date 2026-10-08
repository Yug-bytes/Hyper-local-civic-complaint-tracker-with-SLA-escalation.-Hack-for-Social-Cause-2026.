"""Tests for status transition rules and state machine progression."""

import pytest

from constants import ALLOWED_STATUS_TRANSITIONS, Status


def test_allowed_forward_transitions() -> None:
    """Status progression strictly follows:
    submitted -> assigned -> in_progress -> resolved.
    """
    assert ALLOWED_STATUS_TRANSITIONS[Status.SUBMITTED] == Status.ASSIGNED
    assert ALLOWED_STATUS_TRANSITIONS[Status.ASSIGNED] == Status.IN_PROGRESS
    assert ALLOWED_STATUS_TRANSITIONS[Status.IN_PROGRESS] == Status.RESOLVED
    assert Status.RESOLVED not in ALLOWED_STATUS_TRANSITIONS


@pytest.mark.parametrize(
    "current, invalid_target",
    [
        (Status.SUBMITTED, Status.IN_PROGRESS),  # skipped assigned
        (Status.SUBMITTED, Status.RESOLVED),  # skipped assigned & in_progress
        (Status.ASSIGNED, Status.SUBMITTED),  # backwards
        (Status.ASSIGNED, Status.RESOLVED),  # skipped in_progress
        (Status.IN_PROGRESS, Status.SUBMITTED),  # backwards
        (Status.IN_PROGRESS, Status.ASSIGNED),  # backwards
        (Status.RESOLVED, Status.IN_PROGRESS),  # backwards from resolved
        (Status.RESOLVED, Status.SUBMITTED),  # backwards from resolved
    ],
)
def test_disallowed_transitions(current: str, invalid_target: str) -> None:
    """Disallowed transitions are detected and disallowed."""
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current)
    assert invalid_target != allowed_next
