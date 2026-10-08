"""Custom error types for the Civic Complaint Tracker.

See api.md for when each error is raised and the user-facing message.
"""


class ValidationError(Exception):
    """Raised when user input fails validation."""


class NotFoundError(Exception):
    """Raised when a tracking ID is not found."""


class StorageError(Exception):
    """Raised when photo upload to Supabase Storage fails."""


class AuthError(Exception):
    """Raised when admin authentication fails."""
