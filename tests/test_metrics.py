"""Tests for services/metrics.py — averages, counts, and department stats."""

from datetime import datetime, timedelta, timezone

from constants import Status
from services.metrics import (
    avg_resolution_hours,
    counts_by_category,
    counts_by_status,
    overdue_count,
    per_department_stats,
)


def test_empty_complaints_list() -> None:
    """Empty list returns 0s for all aggregation functions."""
    assert avg_resolution_hours([]) == 0.0
    assert overdue_count([]) == 0

    status_counts = counts_by_status([])
    assert all(count == 0 for count in status_counts.values())

    cat_counts = counts_by_category([])
    assert all(count == 0 for count in cat_counts.values())

    dept_stats = per_department_stats([])
    assert len(dept_stats) >= 5
    for row in dept_stats:
        assert row["total"] == 0
        assert row["resolved"] == 0
        assert row["overdue"] == 0
        assert row["avg_resolution_hours"] == 0.0


def test_avg_resolution_hours_normal() -> None:
    """Correctly calculates the average resolution time in hours."""
    t0 = datetime(2026, 10, 8, 10, 0, 0, tzinfo=timezone.utc)
    t_2h = t0 + timedelta(hours=2)
    t_4h = t0 + timedelta(hours=4)

    complaints = [
        {
            "status": Status.RESOLVED,
            "created_at": t0.isoformat(),
            "resolved_at": t_2h.isoformat(),
        },
        {
            "status": Status.RESOLVED,
            "created_at": t0.isoformat(),
            "resolved_at": t_4h.isoformat(),
        },
    ]
    # Average of 2h and 4h is 3.0h
    assert avg_resolution_hours(complaints) == 3.0


def test_avg_resolution_hours_ignores_unresolved() -> None:
    """Complaints in progress or submitted are ignored for resolution time."""
    t0 = datetime(2026, 10, 8, 10, 0, 0, tzinfo=timezone.utc)
    t_6h = t0 + timedelta(hours=6)

    complaints = [
        {
            "status": Status.RESOLVED,
            "created_at": t0.isoformat(),
            "resolved_at": t_6h.isoformat(),
        },
        {
            "status": Status.SUBMITTED,
            "created_at": t0.isoformat(),
            "resolved_at": None,
        },
        {
            "status": Status.IN_PROGRESS,
            "created_at": t0.isoformat(),
            "resolved_at": None,
        },
    ]
    assert avg_resolution_hours(complaints) == 6.0


def test_counts_by_status() -> None:
    """Counts each status correctly."""
    complaints = [
        {"status": Status.SUBMITTED},
        {"status": Status.SUBMITTED},
        {"status": Status.ASSIGNED},
        {"status": Status.RESOLVED},
    ]
    counts = counts_by_status(complaints)
    assert counts[Status.SUBMITTED.value] == 2
    assert counts[Status.ASSIGNED.value] == 1
    assert counts[Status.IN_PROGRESS.value] == 0
    assert counts[Status.RESOLVED.value] == 1


def test_counts_by_category() -> None:
    """Counts each category correctly."""
    complaints = [
        {"category": "pothole"},
        {"category": "pothole"},
        {"category": "water"},
        {"category": "garbage"},
    ]
    counts = counts_by_category(complaints)
    assert counts["pothole"] == 2
    assert counts["water"] == 1
    assert counts["garbage"] == 1
    assert counts["streetlight"] == 0
    assert counts["other"] == 0


def test_overdue_count() -> None:
    """Counts only open complaints that have exceeded their due date."""
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    past = now - timedelta(days=1)
    future = now + timedelta(days=1)

    complaints = [
        # Overdue (submitted, past due)
        {"status": Status.SUBMITTED, "due_at": past.isoformat(), "sla_days": 2},
        # Overdue (in progress, past due)
        {"status": Status.IN_PROGRESS, "due_at": past.isoformat(), "sla_days": 3},
        # On time (submitted, future due)
        {"status": Status.SUBMITTED, "due_at": future.isoformat(), "sla_days": 2},
        # Resolved, even if past due (not overdue)
        {"status": Status.RESOLVED, "due_at": past.isoformat(), "sla_days": 2},
    ]
    assert overdue_count(complaints, now) == 2


def test_per_department_stats() -> None:
    """Aggregates totals, resolved counts, overdue counts, and avg resolution."""
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    past = now - timedelta(days=1)
    t_res = now - timedelta(hours=12)

    complaints = [
        {
            "category": "pothole",
            "status": Status.SUBMITTED,
            "due_at": past.isoformat(),
            "sla_days": 2,
        },
        {
            "category": "pothole",
            "status": Status.RESOLVED,
            "created_at": (now - timedelta(hours=24)).isoformat(),
            "resolved_at": t_res.isoformat(),
            "due_at": past.isoformat(),
            "sla_days": 2,
        },
    ]
    stats = per_department_stats(complaints, now)
    pothole_stat = next(s for s in stats if s["category"] == "pothole")
    assert pothole_stat["total"] == 2
    assert pothole_stat["resolved"] == 1
    assert pothole_stat["overdue"] == 1
    assert pothole_stat["avg_resolution_hours"] == 12.0
