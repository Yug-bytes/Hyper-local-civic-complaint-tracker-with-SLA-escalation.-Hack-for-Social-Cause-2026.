"""Escalation service for civic complaints.

Calculates escalation levels based on due dates and SLA durations.
Plain business logic with zero database dependencies.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from constants import Status


def _parse_datetime(dt_val: str | datetime | None) -> datetime | None:
    """Safely parse a datetime or ISO string to an aware UTC datetime."""
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc)
        return dt_val.astimezone(timezone.utc)
    try:
        dt = datetime.fromisoformat(str(dt_val))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def escalation_level(complaint: dict[str, Any], now: datetime) -> int:
    """Compute the escalation level (0, 1, or 2) for a complaint.

    - 0: On time, or already resolved.
    - 1: Overdue (past due date, but within half the SLA duration).
    - 2: Severely overdue (past due date plus more than half the SLA).
    """
    if complaint.get("status") == Status.RESOLVED:
        return 0

    due_at = _parse_datetime(complaint.get("due_at"))
    if due_at is None:
        return 0

    now_utc = _parse_datetime(now)
    if now_utc is None:
        return 0

    # On time if not strictly past the due date
    if now_utc <= due_at:
        return 0

    # Calculate SLA duration to determine half SLA
    if "sla_days" in complaint and complaint["sla_days"] is not None:
        sla_duration = timedelta(days=float(complaint["sla_days"]))
    elif "created_at" in complaint and complaint["created_at"] is not None:
        created_at = _parse_datetime(complaint["created_at"])
        if created_at is not None and due_at > created_at:
            sla_duration = due_at - created_at
        else:
            sla_duration = timedelta(days=7)
    else:
        sla_duration = timedelta(days=7)

    level_2_threshold = due_at + (sla_duration / 2)
    if now_utc > level_2_threshold:
        return 2

    return 1
