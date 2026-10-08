"""Tests for services/escalation.py — escalation level determination."""

from datetime import datetime, timedelta, timezone

from constants import Status
from services.escalation import escalation_level


def test_on_time_complaint_is_level_0() -> None:
    """A complaint before its due date must return level 0."""
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    due_at = now + timedelta(days=2)
    complaint = {
        "status": Status.SUBMITTED,
        "created_at": (now - timedelta(days=1)).isoformat(),
        "due_at": due_at.isoformat(),
        "sla_days": 3,
    }
    assert escalation_level(complaint, now) == 0


def test_boundary_exactly_at_due_date_is_level_0() -> None:
    """At exactly the due date, the complaint is not overdue yet (level 0)."""
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    complaint = {
        "status": Status.ASSIGNED,
        "due_at": now.isoformat(),
        "sla_days": 2,
    }
    assert escalation_level(complaint, now) == 0


def test_one_second_past_due_date_is_level_1() -> None:
    """One second after the deadline, escalation level becomes 1."""
    due_at = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    now = due_at + timedelta(seconds=1)
    complaint = {
        "status": Status.SUBMITTED,
        "due_at": due_at.isoformat(),
        "sla_days": 4,  # SLA = 4 days; half SLA = 2 days
    }
    assert escalation_level(complaint, now) == 1


def test_within_half_sla_is_level_1() -> None:
    """Past due date by 1 day when SLA is 4 days (half SLA = 2 days) -> level 1."""
    due_at = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    now = due_at + timedelta(days=1)
    complaint = {
        "status": Status.IN_PROGRESS,
        "due_at": due_at.isoformat(),
        "sla_days": 4,
    }
    assert escalation_level(complaint, now) == 1


def test_boundary_exactly_at_half_sla_is_level_1() -> None:
    """Exactly at due_at + (SLA / 2) is still level 1."""
    due_at = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    sla_days = 4
    half_sla = timedelta(days=sla_days / 2)  # 2 days
    now = due_at + half_sla
    complaint = {
        "status": Status.SUBMITTED,
        "due_at": due_at.isoformat(),
        "sla_days": sla_days,
    }
    assert escalation_level(complaint, now) == 1


def test_past_half_sla_is_level_2() -> None:
    """Past due_at by more than half the SLA -> level 2."""
    due_at = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    sla_days = 4
    half_sla = timedelta(days=sla_days / 2)
    now = due_at + half_sla + timedelta(minutes=5)
    complaint = {
        "status": Status.IN_PROGRESS,
        "due_at": due_at.isoformat(),
        "sla_days": sla_days,
    }
    assert escalation_level(complaint, now) == 2


def test_resolved_complaint_is_always_level_0() -> None:
    """A resolved complaint is never overdue, regardless of how late it was."""
    due_at = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 10, 20, 0, 0, 0, tzinfo=timezone.utc)  # 19 days overdue
    complaint = {
        "status": Status.RESOLVED,
        "due_at": due_at.isoformat(),
        "sla_days": 2,
    }
    assert escalation_level(complaint, now) == 0


def test_missing_due_at_returns_0() -> None:
    """If due_at is missing or invalid, level defaults to 0."""
    now = datetime.now(timezone.utc)
    complaint = {"status": Status.SUBMITTED}
    assert escalation_level(complaint, now) == 0


def test_handles_datetime_objects_directly() -> None:
    """Works when due_at is a datetime object instead of an ISO string."""
    due_at = datetime(2026, 10, 8, 10, 0, 0, tzinfo=timezone.utc)
    now = datetime(2026, 10, 8, 11, 0, 0, tzinfo=timezone.utc)
    complaint = {
        "status": Status.SUBMITTED,
        "due_at": due_at,
        "sla_days": 1,
    }
    assert escalation_level(complaint, now) == 1
