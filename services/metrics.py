"""Metrics calculation service for civic complaints.

Calculates averages, category/status counts, overdue counts,
and per-department statistics. Pure Python functions without database calls.
"""

from datetime import datetime, timezone
from typing import Any

from constants import CATEGORIES, Status
from services.escalation import _parse_datetime, escalation_level


def avg_resolution_hours(complaints: list[dict[str, Any]]) -> float:
    """Calculate the average resolution time in hours for resolved complaints.

    Ignores complaints that are not resolved or lack resolution timestamps.
    Returns 0.0 if no complaints have been resolved.
    """
    total_seconds = 0.0
    resolved_count = 0

    for c in complaints:
        if c.get("status") != Status.RESOLVED:
            continue
        created_at = _parse_datetime(c.get("created_at"))
        resolved_at = _parse_datetime(c.get("resolved_at"))
        if created_at and resolved_at and resolved_at >= created_at:
            total_seconds += (resolved_at - created_at).total_seconds()
            resolved_count += 1

    if resolved_count == 0:
        return 0.0

    return round((total_seconds / resolved_count) / 3600.0, 1)


def counts_by_status(complaints: list[dict[str, Any]]) -> dict[str, int]:
    """Return complaint counts grouped by status."""
    counts: dict[str, int] = {s.value: 0 for s in Status}
    for c in complaints:
        status = c.get("status")
        if status in counts:
            counts[status] += 1
    return counts


def counts_by_category(complaints: list[dict[str, Any]]) -> dict[str, int]:
    """Return complaint counts grouped by category."""
    counts: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for c in complaints:
        cat = c.get("category")
        if cat in counts:
            counts[cat] += 1
        elif cat:
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def overdue_count(complaints: list[dict[str, Any]], now: datetime | None = None) -> int:
    """Count open complaints that have exceeded their SLA deadline."""
    check_time = now or datetime.now(timezone.utc)
    return sum(1 for c in complaints if escalation_level(c, check_time) > 0)


def per_department_stats(
    complaints: list[dict[str, Any]], now: datetime | None = None
) -> list[dict[str, Any]]:
    """Compute summary statistics grouped by category/department.

    Returns a list of dicts with:
    category, total, resolved, overdue, avg_resolution_hours.
    """
    check_time = now or datetime.now(timezone.utc)
    grouped: dict[str, list[dict[str, Any]]] = {}

    for c in complaints:
        cat = c.get("category", "other")
        grouped.setdefault(cat, []).append(c)

    results: list[dict[str, Any]] = []
    # Ensure all defined categories appear in stats
    all_categories = list(dict.fromkeys(CATEGORIES + list(grouped.keys())))

    for cat in all_categories:
        cat_complaints = grouped.get(cat, [])
        total = len(cat_complaints)
        resolved = sum(1 for c in cat_complaints if c.get("status") == Status.RESOLVED)
        overdue = sum(1 for c in cat_complaints if escalation_level(c, check_time) > 0)
        avg_hours = avg_resolution_hours(cat_complaints)

        results.append(
            {
                "category": cat,
                "total": total,
                "resolved": resolved,
                "open": total - resolved,
                "overdue": overdue,
                "avg_resolution_hours": avg_hours,
            }
        )

    return results
