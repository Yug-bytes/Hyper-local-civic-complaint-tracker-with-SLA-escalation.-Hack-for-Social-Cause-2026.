"""Shared constants for the Civic Complaint Tracker.

All status values, categories, and limits are defined here.
No magic strings anywhere else in the codebase.
"""

from enum import StrEnum


class Status(StrEnum):
    """Complaint status values matching the database constraint."""

    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


# Valid categories (must match data/departments.json)
CATEGORIES: list[str] = ["pothole", "water", "streetlight", "garbage", "other"]

# Display names for categories (English)
CATEGORY_LABELS: dict[str, str] = {
    "pothole": "Pothole / Road damage",
    "water": "Water supply",
    "streetlight": "Streetlight",
    "garbage": "Garbage / Sanitation",
    "other": "Other",
}

# Input limits (from security.md section 4)
MAX_DESCRIPTION_LENGTH: int = 1000
MAX_LOCALITY_LENGTH: int = 100
MAX_NAME_LENGTH: int = 80
MAX_NOTE_LENGTH: int = 500
MAX_PHOTO_MB: int = 5
MAX_PHOTO_BYTES: int = MAX_PHOTO_MB * 1024 * 1024

# Phone validation (10-digit Indian mobile)
PHONE_LENGTH: int = 10

# Allowed photo content types
ALLOWED_PHOTO_TYPES: set[str] = {"image/jpeg", "image/png"}

# Rate limiting (security.md section 7)
COMPLAINT_COOLDOWN_SECONDS: int = 30
MAX_COMPLAINTS_PER_SESSION: int = 5

# Supabase Storage bucket name
PHOTO_BUCKET: str = "complaint-photos"

# Allowed forward status transitions (submitted -> assigned -> in_progress -> resolved)
ALLOWED_STATUS_TRANSITIONS: dict[str, str] = {
    Status.SUBMITTED: Status.ASSIGNED,
    Status.ASSIGNED: Status.IN_PROGRESS,
    Status.IN_PROGRESS: Status.RESOLVED,
}

# Status color tokens from designsystem.md
STATUS_COLORS: dict[str, str] = {
    Status.SUBMITTED: "#6B7785",
    Status.ASSIGNED: "#1D5C8A",
    Status.IN_PROGRESS: "#B87600",
    Status.RESOLVED: "#2E7D4F",
}
COLOR_OVERDUE: str = "#B3261E"
COLOR_CIVIC: str = "#1D5C8A"
COLOR_PAPER: str = "#F6F7F4"
COLOR_INK: str = "#1E2A32"
COLOR_LINE: str = "#D5DADD"
