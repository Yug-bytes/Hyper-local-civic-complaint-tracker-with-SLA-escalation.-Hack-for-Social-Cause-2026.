"""Tests for services/routing.py — category routing and SLA computation."""

from datetime import datetime, timedelta, timezone

import pytest

from constants import CATEGORIES
from services.routing import compute_due_at, route


class TestRoute:
    """Tests for the route() function."""

    @pytest.mark.parametrize("category", CATEGORIES)
    def test_all_categories_return_a_department(self, category: str) -> None:
        """Every known category must map to a department."""
        dept = route(category)
        assert dept["category"] == category
        assert dept["department_name"]
        assert dept["responsible_role"]
        assert dept["escalation_role"]
        assert dept["sla_days"] > 0

    def test_unknown_category_raises(self) -> None:
        """An unknown category must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown category"):
            route("teleportation")

    def test_route_returns_dict_with_expected_keys(self) -> None:
        """The returned dict must have all required keys."""
        dept = route("pothole")
        expected_keys = {
            "category",
            "department_name",
            "responsible_role",
            "escalation_role",
            "sla_days",
        }
        assert expected_keys.issubset(dept.keys())


class TestComputeDueAt:
    """Tests for the compute_due_at() function."""

    def test_adds_sla_days(self) -> None:
        """Due date should be created_at + sla_days."""
        created = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
        due = compute_due_at(created, sla_days=3)
        assert due == created + timedelta(days=3)

    def test_one_day_sla(self) -> None:
        """A 1-day SLA should set the due date to the next day."""
        created = datetime(2026, 10, 8, 18, 30, 0, tzinfo=timezone.utc)
        due = compute_due_at(created, sla_days=1)
        assert due == datetime(2026, 10, 9, 18, 30, 0, tzinfo=timezone.utc)

    def test_preserves_timezone(self) -> None:
        """The due date must keep the same timezone as created_at."""
        created = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
        due = compute_due_at(created, sla_days=7)
        assert due.tzinfo == created.tzinfo
