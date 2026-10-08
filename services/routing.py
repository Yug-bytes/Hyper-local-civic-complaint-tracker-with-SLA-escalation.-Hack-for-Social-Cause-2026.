"""Complaint routing: category -> department, SLA, due date.

Reads the routing table from data/departments.json (cached after first load).
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from constants import CATEGORIES

_DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"
_DEPARTMENTS_PATH: Path = _DATA_DIR / "departments.json"

# Module-level cache so the file is read only once per process
_cache: list[dict[str, Any]] | None = None


def _load_departments() -> list[dict[str, Any]]:
    """Load and cache the departments routing table from JSON."""
    global _cache  # noqa: PLW0603
    if _cache is None:
        with open(_DEPARTMENTS_PATH, encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def route(category: str) -> dict[str, Any]:
    """Return the department info for a category.

    Returns a dict with keys: category, department_name,
    responsible_role, escalation_role, sla_days.
    Raises ValueError if the category is not in the routing table.
    """
    if category not in CATEGORIES:
        raise ValueError(f"Unknown category: {category}")

    for dept in _load_departments():
        if dept["category"] == category:
            return dept

    raise ValueError(f"Category '{category}' not found in departments.json")


def compute_due_at(created_at: datetime, sla_days: int) -> datetime:
    """Calculate the complaint deadline by adding SLA days."""
    return created_at + timedelta(days=sla_days)
