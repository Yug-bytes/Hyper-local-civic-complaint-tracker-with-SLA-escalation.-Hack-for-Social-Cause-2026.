"""Tests for services/ids.py — tracking ID generation."""

import re
from datetime import datetime, timezone

from services.ids import generate_tracking_id


def test_format_matches_pattern() -> None:
    """Tracking ID must match CT-YYMMDD-XXXX."""
    now = datetime(2026, 10, 8, 14, 30, 0, tzinfo=timezone.utc)
    tid = generate_tracking_id(now)
    assert re.fullmatch(r"CT-\d{6}-[A-Z0-9]{4}", tid), f"Bad format: {tid}"


def test_date_part_is_correct() -> None:
    """The YYMMDD part must match the given datetime."""
    now = datetime(2026, 12, 25, 0, 0, 0, tzinfo=timezone.utc)
    tid = generate_tracking_id(now)
    date_part = tid.split("-")[1]
    assert date_part == "261225"


def test_suffix_uses_unambiguous_chars() -> None:
    """Suffix must not contain easily confused characters (0, O, 1, I, L, etc.)."""
    ambiguous = set("0OoIi1Ll5Ss2Zz8Bb")
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    # Generate many IDs and check all suffixes
    for _ in range(200):
        tid = generate_tracking_id(now)
        suffix = tid.split("-")[2]
        assert len(suffix) == 4
        for char in suffix:
            assert char not in ambiguous, f"Ambiguous char '{char}' in suffix"


def test_ids_are_not_all_identical() -> None:
    """Two calls should (almost certainly) produce different IDs."""
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)
    ids = {generate_tracking_id(now) for _ in range(20)}
    assert len(ids) > 1, "All IDs were identical — random suffix not working"


def test_prefix_is_ct() -> None:
    """Every tracking ID starts with 'CT-'."""
    now = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    tid = generate_tracking_id(now)
    assert tid.startswith("CT-")
