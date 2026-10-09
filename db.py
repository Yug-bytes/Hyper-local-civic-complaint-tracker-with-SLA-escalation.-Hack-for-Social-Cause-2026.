"""All database access for the Civic Complaint Tracker.

This is the ONLY module that imports the Supabase client.
Public functions never return reporter_name or reporter_phone.
Admin functions (Stage 2) will require the admin session flag.

See api.md for the full function contract.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import streamlit as st
except ImportError:
    st = None

from config import get_settings
from constants import (
    ALLOWED_PHOTO_TYPES,
    ALLOWED_STATUS_TRANSITIONS,
    CATEGORIES,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCALITY_LENGTH,
    MAX_NAME_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_PHOTO_BYTES,
    MAX_PHOTO_MB,
    PHONE_LENGTH,
    Status,
)
from errors import AuthError, NotFoundError, StorageError, ValidationError
from services import escalation, ids, metrics, routing
from supabase import Client, create_client

# ── Public columns (never includes reporter_name / reporter_phone) ──
_PUBLIC_COLUMNS: str = (
    "tracking_id, category, description, locality, photo_url, "
    "status, created_at, due_at, resolved_at"
)


# ──────────────────────────────────────────────────────────────
# Supabase client (service role key, bypasses RLS)
# ──────────────────────────────────────────────────────────────

_CLIENT_INSTANCE: Client | None = None


def set_client(client: Client | None) -> None:
    """Inject a custom or mock Supabase client (useful for tests)."""
    global _CLIENT_INSTANCE
    _CLIENT_INSTANCE = client


def _get_supabase_credentials() -> tuple[str, str]:
    """Retrieve Supabase URL and service role key from configuration."""
    settings = get_settings()
    settings.validate_required()
    return settings.supabase_url, settings.supabase_service_role_key


def _get_photo_bucket() -> str:
    """Get photo bucket name from configuration."""
    return get_settings().photo_bucket


def _get_client() -> Client:
    """Create and cache the Supabase client using the service role key."""
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is not None:
        return _CLIENT_INSTANCE

    url, key = _get_supabase_credentials()
    _CLIENT_INSTANCE = create_client(url, key)
    return _CLIENT_INSTANCE


# ──────────────────────────────────────────────────────────────
# Input validation (security.md §4 and §6)
# ──────────────────────────────────────────────────────────────


def _validate_text(
    value: str, field_name: str, max_length: int, required: bool = True
) -> str:
    """Strip, check emptiness, and enforce max length for a text field."""
    value = value.strip()
    if required and not value:
        raise ValidationError(f"{field_name} is required.")
    if len(value) > max_length:
        raise ValidationError(f"{field_name} must be {max_length} characters or fewer.")
    return value


def _validate_phone(phone: str) -> str | None:
    """Validate an optional Indian 10-digit mobile number."""
    phone = phone.strip()
    if not phone:
        return None
    if not re.fullmatch(r"\d{" + str(PHONE_LENGTH) + "}", phone):
        raise ValidationError(
            f"Phone must be exactly {PHONE_LENGTH} digits (e.g. 9876543210)."
        )
    return phone


def _detect_content_type(data: bytes) -> str:
    """Detect image content type from magic bytes, not the file extension."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return "unknown"


def _validate_photo(photo_bytes: bytes) -> str:
    """Validate photo size and real content type. Returns the detected MIME type."""
    if len(photo_bytes) > MAX_PHOTO_BYTES:
        raise ValidationError(f"Photo must be {MAX_PHOTO_MB} MB or smaller.")
    content_type = _detect_content_type(photo_bytes)
    if content_type not in ALLOWED_PHOTO_TYPES:
        raise ValidationError("Photo must be a JPG or PNG file.")
    return content_type


# ──────────────────────────────────────────────────────────────
# Photo upload
# ──────────────────────────────────────────────────────────────


def _upload_photo(client: Client, photo_bytes: bytes, content_type: str) -> str:
    """Upload photo with a random filename. Returns the public URL."""
    ext = "jpg" if content_type == "image/jpeg" else "png"
    filename = f"{uuid.uuid4().hex}.{ext}"
    bucket = _get_photo_bucket()
    try:
        client.storage.from_(bucket).upload(
            filename,
            photo_bytes,
            {"content-type": content_type},
        )
        return client.storage.from_(bucket).get_public_url(filename)
    except Exception as exc:
        raise StorageError("Photo upload failed.") from exc


def get_signed_photo_url(path_or_url: str | None, expires_in: int = 900) -> str | None:
    """Generate a temporary signed URL (default 15 minutes) for a stored photo.

    Returns None if path_or_url is empty.
    Gracefully falls back to original path_or_url if signing fails or in offline tests.
    """
    if not path_or_url:
        return None

    raw = path_or_url.strip()
    bucket = _get_photo_bucket()
    if f"/{bucket}/" in raw:
        path = raw.split(f"/{bucket}/")[-1].split("?")[0]
    elif "/" in raw and (raw.startswith("http://") or raw.startswith("https://")):
        path = raw.split("/")[-1].split("?")[0]
    else:
        path = raw.split("?")[0]

    try:
        client = _get_client()
        res = client.storage.from_(bucket).create_signed_url(
            path, expires_in=expires_in
        )
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signed_url") or raw
        elif hasattr(res, "signed_url"):
            return getattr(res, "signed_url") or raw
        elif hasattr(res, "get"):
            return res.get("signedURL") or res.get("signed_url") or raw
        return str(res)
    except Exception:
        return raw


# ──────────────────────────────────────────────────────────────
# Duplicate check (security.md §7)
# ──────────────────────────────────────────────────────────────


def _is_duplicate(
    client: Client, category: str, locality: str, description: str
) -> bool:
    """Check if the same category+locality+description was filed in the last 24 h."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    result = (
        client.table("complaints")
        .select("id")
        .eq("category", category)
        .eq("locality", locality)
        .eq("description", description)
        .gte("created_at", cutoff)
        .limit(1)
        .execute()
    )
    return bool(result.data)


# ──────────────────────────────────────────────────────────────
# Public functions (api.md)
# ──────────────────────────────────────────────────────────────


def create_complaint(
    category: str,
    description: str,
    locality: str,
    photo_bytes: bytes | None = None,
    name: str | None = None,
    phone: str | None = None,
) -> str:
    """Validate, route, insert a complaint and first history row.

    Returns the tracking_id on success.
    """
    # ── Validate category ──
    if category not in CATEGORIES:
        raise ValidationError(f"Category must be one of: {', '.join(CATEGORIES)}.")

    # ── Validate text fields ──
    description = _validate_text(description, "Description", MAX_DESCRIPTION_LENGTH)
    locality = _validate_text(locality, "Locality", MAX_LOCALITY_LENGTH)

    clean_name: str | None = None
    if name:
        clean_name = _validate_text(name, "Name", MAX_NAME_LENGTH, required=False)
        if not clean_name:
            clean_name = None

    clean_phone: str | None = None
    if phone:
        clean_phone = _validate_phone(phone)

    # ── Validate and upload photo ──
    photo_url: str | None = None
    client = _get_client()
    if photo_bytes:
        content_type = _validate_photo(photo_bytes)
        try:
            photo_url = _upload_photo(client, photo_bytes, content_type)
        except StorageError:
            # api.md: "Photo didn't upload. Your complaint was saved without it."
            photo_url = None

    # ── Duplicate check ──
    if _is_duplicate(client, category, locality, description):
        raise ValidationError(
            "A similar complaint for this location was filed in the last 24 hours."
        )

    # ── Route and compute deadline ──
    dept = routing.route(category)
    now = datetime.now(timezone.utc)
    tracking_id = ids.generate_tracking_id(now)
    due_at = routing.compute_due_at(now, dept["sla_days"])

    # ── Insert complaint ──
    complaint_data: dict[str, Any] = {
        "tracking_id": tracking_id,
        "category": category,
        "description": description,
        "locality": locality,
        "photo_url": photo_url,
        "reporter_name": clean_name,
        "reporter_phone": clean_phone,
        "status": Status.SUBMITTED,
        "due_at": due_at.isoformat(),
    }
    try:
        result = client.table("complaints").insert(complaint_data).execute()
        if not result.data:
            raise StorageError("Failed to save complaint. Please try again.")
    except StorageError:
        raise
    except Exception as exc:
        raise StorageError(
            "Service temporarily unavailable. Please try again in a moment."
        ) from exc

    complaint_id: str = result.data[0]["id"]

    # ── Insert first status history row ──
    try:
        client.table("status_history").insert(
            {
                "complaint_id": complaint_id,
                "status": Status.SUBMITTED,
                "note": "Complaint received",
                "changed_by": "system",
            }
        ).execute()
    except Exception:
        pass

    return tracking_id


def get_public_status(tracking_id: str) -> dict[str, Any] | None:
    """Look up a complaint by tracking ID for public display.

    Returns the complaint (no personal fields) with a 'history' list,
    or None if the tracking ID is not found or the database is unavailable.
    """
    tracking_id = tracking_id.strip().upper()
    try:
        client = _get_client()

        # Select public columns + id (for history lookup; id is removed before return)
        result = (
            client.table("complaints")
            .select(f"id, {_PUBLIC_COLUMNS}")
            .eq("tracking_id", tracking_id)
            .execute()
        )
        if not result.data:
            return None

        complaint: dict[str, Any] = result.data[0]
        complaint_id = complaint.pop("id")  # remove internal id before returning

        # Fetch status history (newest first)
        try:
            history_result = (
                client.table("status_history")
                .select("status, note, changed_by, changed_at")
                .eq("complaint_id", complaint_id)
                .order("changed_at", desc=True)
                .execute()
            )
            complaint["history"] = history_result.data or []
        except Exception:
            complaint["history"] = []

        if complaint.get("photo_url"):
            complaint["photo_url"] = get_signed_photo_url(complaint["photo_url"])

        return complaint
    except Exception:
        return None


def get_departments() -> list[dict[str, Any]]:
    """Return all rows from the departments table, falling back to local JSON."""
    try:
        client = _get_client()
        result = client.table("departments").select("*").execute()
        if result.data:
            return result.data
    except Exception:
        pass
    return routing._load_departments()


# ──────────────────────────────────────────────────────────────
# Admin & Metrics functions (Stage 2)
# ──────────────────────────────────────────────────────────────


def list_complaints(
    status: str | None = None,
    category: str | None = None,
    overdue_only: bool = False,
    is_admin: bool | None = None,
) -> list[dict[str, Any]]:
    """List complaints for admin with optional filters.

    Requires admin authentication (is_admin=True or st.session_state['is_admin']).
    Returns all fields including reporter_name and reporter_phone.
    """
    admin_ok = is_admin if is_admin is not None else False
    if is_admin is None:
        try:
            admin_ok = bool(st.session_state.get("is_admin", False))
        except Exception:
            admin_ok = False

    if not admin_ok:
        raise AuthError("Admin authentication required.")

    complaints: list[dict[str, Any]] = []
    try:
        client = _get_client()
        query = client.table("complaints").select("*").order("created_at", desc=True)

        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)

        result = query.execute()
        complaints = result.data or []
    except Exception:
        complaints = []

    now = datetime.now(timezone.utc)
    for c in complaints:
        c["escalation_level"] = escalation.escalation_level(c, now)
        c["is_overdue"] = c["escalation_level"] > 0
        if c.get("photo_url"):
            c["photo_url"] = get_signed_photo_url(c["photo_url"])

    if overdue_only:
        complaints = [c for c in complaints if c["is_overdue"]]

    return complaints


def update_status(
    tracking_id: str,
    new_status: str,
    note: str | None = None,
    is_admin: bool | None = None,
) -> dict[str, Any]:
    """Admin status change: validates progression, writes history, sets resolved_at.

    Requires admin authentication.
    Only allows forward progression:
    submitted -> assigned -> in_progress -> resolved
    """
    admin_ok = is_admin if is_admin is not None else False
    if is_admin is None:
        try:
            admin_ok = bool(st.session_state.get("is_admin", False))
        except Exception:
            admin_ok = False

    if not admin_ok:
        raise AuthError("Admin authentication required.")

    tracking_id = tracking_id.strip().upper()
    try:
        client = _get_client()
        fetch_result = (
            client.table("complaints")
            .select("*")
            .eq("tracking_id", tracking_id)
            .execute()
        )
    except Exception as exc:
        raise StorageError(
            "Service temporarily unavailable. Unable to retrieve complaint."
        ) from exc

    if not fetch_result.data:
        raise NotFoundError("We couldn't find that ID. Check it and try again.")

    complaint = fetch_result.data[0]
    current_status = complaint["status"]

    # Validate transition
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_status)
    if new_status != allowed_next:
        msg = (
            f"Invalid status change. Cannot move from '{current_status}' "
            f"to '{new_status}'. Next allowed status is '{allowed_next}'."
            if allowed_next
            else f"Complaint is already '{current_status}' and cannot be updated."
        )
        raise ValidationError(msg)

    clean_note: str | None = None
    if note:
        clean_note = _validate_text(note, "Note", MAX_NOTE_LENGTH, required=False)

    now = datetime.now(timezone.utc)
    update_data: dict[str, Any] = {"status": new_status}
    if new_status == Status.RESOLVED:
        update_data["resolved_at"] = now.isoformat()

    try:
        update_result = (
            client.table("complaints")
            .update(update_data)
            .eq("id", complaint["id"])
            .execute()
        )
        if not update_result.data:
            raise StorageError("Failed to update complaint status.")
    except StorageError:
        raise
    except Exception as exc:
        raise StorageError(
            "Service temporarily unavailable. Unable to update status."
        ) from exc

    # Insert status history row
    try:
        client.table("status_history").insert(
            {
                "complaint_id": complaint["id"],
                "status": new_status,
                "note": clean_note,
                "changed_by": "admin",
                "changed_at": now.isoformat(),
            }
        ).execute()
    except Exception:
        pass

    return update_result.data[0]


def unlink_photo(tracking_id: str, is_admin: bool | None = None) -> dict[str, Any]:
    """Admin action: removes photo_url from complaint and logs to status_history."""
    admin_ok = is_admin if is_admin is not None else False
    if is_admin is None:
        try:
            admin_ok = bool(st.session_state.get("is_admin", False))
        except Exception:
            admin_ok = False

    if not admin_ok:
        raise AuthError("Admin authentication required.")

    tracking_id = tracking_id.strip().upper()
    try:
        client = _get_client()
        fetch_result = (
            client.table("complaints")
            .select("*")
            .eq("tracking_id", tracking_id)
            .execute()
        )
    except Exception as exc:
        raise StorageError(
            "Service temporarily unavailable. Unable to retrieve complaint."
        ) from exc

    if not fetch_result.data:
        raise NotFoundError("We couldn't find that ID. Check it and try again.")

    complaint = fetch_result.data[0]
    old_photo_url = complaint.get("photo_url")

    if old_photo_url:
        bucket = _get_photo_bucket()
        raw = old_photo_url.strip()
        if f"/{bucket}/" in raw:
            path = raw.split(f"/{bucket}/")[-1].split("?")[0]
        elif "/" in raw and (raw.startswith("http://") or raw.startswith("https://")):
            path = raw.split("/")[-1].split("?")[0]
        else:
            path = raw.split("?")[0]
        try:
            client.storage.from_(bucket).remove([path])
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    try:
        update_result = (
            client.table("complaints")
            .update({"photo_url": None})
            .eq("id", complaint["id"])
            .execute()
        )
        if not update_result.data:
            raise StorageError("Failed to remove photo.")
    except StorageError:
        raise
    except Exception as exc:
        raise StorageError(
            "Service temporarily unavailable. Unable to remove photo."
        ) from exc

    try:
        client.table("status_history").insert(
            {
                "complaint_id": complaint["id"],
                "status": complaint["status"],
                "note": "Photo removed by administrator",
                "changed_by": "admin",
                "changed_at": now.isoformat(),
            }
        ).execute()
    except Exception:
        pass

    return update_result.data[0]


def get_public_metrics() -> list[dict[str, Any]]:
    """Return per-department metrics without any personal data.

    Publicly accessible without admin credentials.
    """
    try:
        client = _get_client()
        result = (
            client.table("complaints")
            .select("category, status, created_at, due_at, resolved_at")
            .execute()
        )
        complaints = result.data or []
    except Exception:
        complaints = []

    return metrics.per_department_stats(complaints)
