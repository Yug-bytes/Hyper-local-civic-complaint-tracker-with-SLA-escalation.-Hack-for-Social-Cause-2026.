"""Citizen-facing page: file a complaint and check its status.

No SQL or business rules here — all logic goes through db.py and services/.
"""

import time
from datetime import datetime
from typing import Any

import streamlit as st

import db
from constants import (
    CATEGORIES,
    COMPLAINT_COOLDOWN_SECONDS,
    MAX_COMPLAINTS_PER_SESSION,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCALITY_LENGTH,
    MAX_PHOTO_MB,
    Status,
)
from errors import StorageError, ValidationError
from strings import CATEGORY_STRING_KEYS, STATUS_STRING_KEYS, t

# ── Status chip colors (only used with known enum values, not user text) ──
_STATUS_COLORS: dict[str, str] = {
    Status.SUBMITTED: "#6B7785",
    Status.ASSIGNED: "#1D5C8A",
    Status.IN_PROGRESS: "#B87600",
    Status.RESOLVED: "#2E7D4F",
}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _status_chip_html(status: str) -> str:
    """Return safe HTML for a status chip. Only renders known values."""
    color = _STATUS_COLORS.get(status)
    if color is None:
        return ""
    label = t(STATUS_STRING_KEYS.get(status, status))
    return f'<span class="status-chip" style="background-color:{color}">{label}</span>'


def _format_datetime(iso_str: str | None) -> str:
    """Format an ISO datetime string for display."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(iso_str)


def _check_rate_limit() -> str | None:
    """Enforce per-session cooldown and complaint limit. Returns error or None."""
    count = st.session_state.get("complaint_count", 0)
    if count >= MAX_COMPLAINTS_PER_SESSION:
        return t("error_session_limit").format(limit=MAX_COMPLAINTS_PER_SESSION)

    last_time: float = st.session_state.get("last_complaint_time", 0.0)
    elapsed = time.time() - last_time
    if elapsed < COMPLAINT_COOLDOWN_SECONDS:
        remaining = int(COMPLAINT_COOLDOWN_SECONDS - elapsed)
        return t("error_cooldown").format(seconds=remaining)

    return None


def _record_complaint_filed() -> None:
    """Update session counters after a complaint is successfully filed."""
    st.session_state["complaint_count"] = st.session_state.get("complaint_count", 0) + 1
    st.session_state["last_complaint_time"] = time.time()


# ──────────────────────────────────────────────────────────────
# Complaint form
# ──────────────────────────────────────────────────────────────


def _complaint_form() -> None:
    """Render the complaint submission form."""
    st.header(t("file_complaint"))

    # Build category display names for the dropdown
    category_options = [""] + CATEGORIES
    category_labels = [t("select_category")] + [
        t(CATEGORY_STRING_KEYS[c]) for c in CATEGORIES
    ]

    with st.form("complaint_form", clear_on_submit=True):
        # Category
        category_idx = st.selectbox(
            t("category"),
            range(len(category_options)),
            format_func=lambda i: category_labels[i],
        )
        selected_category = category_options[category_idx] if category_idx else ""

        # Description
        description = st.text_area(
            t("description"),
            max_chars=MAX_DESCRIPTION_LENGTH,
            help=t("description_help"),
        )

        # Locality
        locality = st.text_input(
            t("locality"),
            max_chars=MAX_LOCALITY_LENGTH,
        )

        # Photo (optional)
        st.caption(t("photo_warning"))
        photo_file = st.file_uploader(
            t("photo"),
            type=["jpg", "jpeg", "png"],
            help=f"JPG or PNG, max {MAX_PHOTO_MB} MB",
        )

        # Name and phone (optional)
        name = st.text_input(t("name"))
        phone = st.text_input(t("phone"))

        # Consent line
        st.markdown(
            f'<p class="consent-text">{t("consent")}</p>',
            unsafe_allow_html=True,  # safe: static translated text, no user input
        )

        submitted = st.form_submit_button(
            t("send_complaint"), type="primary", use_container_width=True
        )

    if submitted:
        _handle_submission(
            selected_category, description, locality, photo_file, name, phone
        )


def _handle_submission(
    category: str,
    description: str,
    locality: str,
    photo_file: Any,
    name: str,
    phone: str,
) -> None:
    """Validate, rate-limit, and submit the complaint."""
    # Rate limit check
    rate_error = _check_rate_limit()
    if rate_error:
        st.error(rate_error)
        return

    # Quick client-side check for empty required fields
    if not category:
        st.error(f"{t('category')}: {t('select_category')}")
        return

    # Read photo bytes if provided
    photo_bytes: bytes | None = None
    if photo_file is not None:
        photo_bytes = photo_file.getvalue()

    try:
        tracking_id = db.create_complaint(
            category=category,
            description=description,
            locality=locality,
            photo_bytes=photo_bytes,
            name=name or None,
            phone=phone or None,
        )
        _record_complaint_filed()
        _show_success(tracking_id)
    except ValidationError as exc:
        st.error(str(exc))
    except StorageError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Service is currently unavailable. Please try again in a moment.")


# ──────────────────────────────────────────────────────────────
# Success screen
# ──────────────────────────────────────────────────────────────


def _show_success(tracking_id: str) -> None:
    """Display the tracking ID after a successful submission."""
    st.success(t("complaint_saved"))
    st.markdown(f"**{t('tracking_id_label')}**")
    st.markdown(
        f'<div class="tracking-id-box">{tracking_id}</div>',
        unsafe_allow_html=True,  # safe: tracking_id is system-generated, not user text
    )
    st.info(t("tracking_id_instruction"))


# ──────────────────────────────────────────────────────────────
# Status lookup
# ──────────────────────────────────────────────────────────────


def _status_lookup() -> None:
    """Render the tracking ID lookup form and results."""
    st.header(t("check_status"))

    tracking_id = st.text_input(
        t("enter_tracking_id"),
        placeholder=t("tracking_id_placeholder"),
    )

    if st.button(t("check"), type="primary", use_container_width=True):
        if not tracking_id.strip():
            st.error(t("enter_tracking_id"))
            return
        _show_status_result(tracking_id)


def _show_status_result(tracking_id: str) -> None:
    """Fetch and display the complaint status (no personal data)."""
    complaint = db.get_public_status(tracking_id)

    if complaint is None:
        st.warning(t("no_complaint_found"))
        return

    # ── Status chip ──
    status_html = _status_chip_html(complaint["status"])

    # Check if overdue
    is_overdue = False
    if complaint["status"] != Status.RESOLVED and complaint.get("due_at"):
        try:
            due_dt = datetime.fromisoformat(complaint["due_at"])
            if datetime.now(due_dt.tzinfo) > due_dt:
                is_overdue = True
        except (ValueError, TypeError):
            pass

    if is_overdue:
        status_html += (
            ' <span class="status-chip" '
            f'style="background-color:#B3261E">{t("overdue")}</span>'
        )

    st.markdown(status_html, unsafe_allow_html=True)

    # ── Key details ──
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t('category')}**")
        cat_key = CATEGORY_STRING_KEYS.get(complaint["category"], complaint["category"])
        st.text(t(cat_key))
    with col2:
        st.markdown(f"**{t('locality')}**")
        st.text(complaint.get("locality", "—"))

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"**{t('filed_on')}**")
        st.text(_format_datetime(complaint.get("created_at")))
    with col4:
        st.markdown(f"**{t('due_date')}**")
        st.text(_format_datetime(complaint.get("due_at")))

    if complaint.get("resolved_at"):
        st.markdown(f"**{t('resolved_on')}**")
        st.text(_format_datetime(complaint["resolved_at"]))

    # ── Photo ──
    if complaint.get("photo_url"):
        st.image(complaint["photo_url"], width=300)

    # ── History timeline (newest first) ──
    history = complaint.get("history", [])
    if history:
        st.markdown(f"**{t('history')}**")
        for entry in history:
            chip = _status_chip_html(entry["status"])
            timestamp = _format_datetime(entry.get("changed_at"))
            note = entry.get("note") or ""

            st.markdown(
                f'<div class="timeline-entry">'
                f'<span class="timestamp">{timestamp}</span> {chip}'
                f"</div>",
                unsafe_allow_html=True,  # safe: timestamp and chip are system data
            )
            if note:
                # Note may contain admin text — render as plain text, not HTML
                st.text(f"  {note}")


# ──────────────────────────────────────────────────────────────
# Page entry point
# ──────────────────────────────────────────────────────────────

tab_file, tab_track = st.tabs([t("file_complaint"), t("check_status")])

with tab_file:
    _complaint_form()

with tab_track:
    _status_lookup()
