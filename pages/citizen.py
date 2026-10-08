"""Citizen-facing page: file a complaint and check its status.

Follows docs/designsystem.md with phone-first layout, colored status chips,
clear visual overdue flagging, and standard page header.
No SQL or business rules here — all logic flows through db.py.
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
    STATUS_COLORS,
    Status,
)
from errors import StorageError, ValidationError
from strings import CATEGORY_STRING_KEYS, STATUS_STRING_KEYS, t

# ──────────────────────────────────────────────────────────────
# Visual Helpers (Safe HTML)
# ──────────────────────────────────────────────────────────────


def _status_chip_html(status: str) -> str:
    """Return safe HTML for a status chip with token color and text label."""
    color = STATUS_COLORS.get(status, "#6B7785")
    label = t(STATUS_STRING_KEYS.get(status, status))
    return (
        f'<span class="status-chip chip-{status}" '
        f'style="background-color:{color};">{label}</span>'
    )


def _overdue_chip_html() -> str:
    """Return safe HTML for a red overdue chip."""
    label = t("overdue")
    return (
        f'<span class="status-chip chip-overdue" '
        f'style="background-color:#B3261E;">{label}</span>'
    )


def _format_datetime(iso_str: str | None) -> str:
    """Format an ISO datetime string into human-readable format."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str))
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
# Standard Page Header (Requirement 6)
# ──────────────────────────────────────────────────────────────


def _render_page_header() -> None:
    """Render the standard header with project name and one-line description."""
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-title">{t("app_title")}</div>
            <div class="page-header-desc">{t("app_description")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Complaint Submission Form
# ──────────────────────────────────────────────────────────────


def _complaint_form() -> None:
    """Render the complaint submission form."""
    st.subheader(t("file_complaint"))

    category_options = [""] + CATEGORIES
    category_labels = [t("select_category")] + [
        t(CATEGORY_STRING_KEYS[c]) for c in CATEGORIES
    ]

    with st.form("complaint_form", clear_on_submit=True):
        category_idx = st.selectbox(
            t("category"),
            range(len(category_options)),
            format_func=lambda i: category_labels[i],
        )
        selected_category = category_options[category_idx] if category_idx else ""

        locality = st.text_input(
            t("locality"),
            max_chars=MAX_LOCALITY_LENGTH,
            placeholder="Colony, ward, or nearest landmark",
        )

        description = st.text_area(
            t("description"),
            max_chars=MAX_DESCRIPTION_LENGTH,
            placeholder="Describe what is wrong and where exactly...",
            help=t("description_help"),
        )

        st.caption(t("photo_warning"))
        photo_file = st.file_uploader(
            t("photo"),
            type=["jpg", "jpeg", "png"],
            help=f"JPG or PNG format, max {MAX_PHOTO_MB} MB",
        )

        col_name, col_phone = st.columns(2)
        with col_name:
            name = st.text_input(t("name"))
        with col_phone:
            phone = st.text_input(t("phone"))

        st.caption(t("consent"))

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
    rate_error = _check_rate_limit()
    if rate_error:
        st.error(rate_error)
        return

    if not category:
        st.error(f"{t('category')}: {t('select_category')}")
        return

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


def _show_success(tracking_id: str) -> None:
    """Display the tracking ID hero box after successful submission."""
    st.success(t("complaint_saved"))
    st.markdown(f"**{t('tracking_id_label')}**")
    st.markdown(
        f'<div class="tracking-id-box">{tracking_id}</div>',
        unsafe_allow_html=True,
    )
    st.info(t("tracking_id_instruction"))


# ──────────────────────────────────────────────────────────────
# Status Lookup
# ──────────────────────────────────────────────────────────────


def _status_lookup() -> None:
    """Render the tracking ID lookup form and results."""
    st.subheader(t("check_status"))

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        tracking_id = st.text_input(
            t("enter_tracking_id"),
            placeholder=t("tracking_id_placeholder"),
            label_visibility="collapsed",
        )
    with col_btn:
        search_clicked = st.button(t("check"), type="primary", use_container_width=True)

    if search_clicked:
        if not tracking_id.strip():
            st.error(t("enter_tracking_id"))
            return
        _show_status_result(tracking_id.strip())


def _show_status_result(tracking_id: str) -> None:
    """Fetch and display complaint status with chips, due date, and history."""
    complaint = db.get_public_status(tracking_id)

    if complaint is None:
        st.warning(t("no_complaint_found"))
        return

    # Check overdue status (Requirement 3)
    is_overdue = False
    due_str = complaint.get("due_at")
    if complaint["status"] != Status.RESOLVED and due_str:
        try:
            due_dt = datetime.fromisoformat(due_str)
            if datetime.now(due_dt.tzinfo) > due_dt:
                is_overdue = True
        except (ValueError, TypeError):
            pass

    # Status chips (Requirement 2 & 3)
    status_html = _status_chip_html(complaint["status"])
    if is_overdue:
        status_html += " " + _overdue_chip_html()

    st.markdown(f"### {tracking_id}")
    st.markdown(status_html, unsafe_allow_html=True)

    # Overdue visual alert (Requirement 3)
    if is_overdue:
        st.markdown(
            f"""
            <div class="overdue-alert">
                <span>{t("overdue")}:</span>
                <span>Deadline {_format_datetime(due_str)} has passed.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Key Details Metadata Grid
    cat_key = CATEGORY_STRING_KEYS.get(complaint["category"], complaint["category"])
    cat_label = t(cat_key)
    locality_label = complaint.get("locality", "—")
    filed_on_label = _format_datetime(complaint.get("created_at"))
    due_date_label = _format_datetime(due_str)

    due_class = "overdue-due-text" if is_overdue else "meta-item-value"

    st.markdown(
        f"""
        <div class="meta-grid">
            <div>
                <div class="meta-item-label">{t("category")}</div>
                <div class="meta-item-value">{cat_label}</div>
            </div>
            <div>
                <div class="meta-item-label">{t("locality")}</div>
                <div class="meta-item-value">{locality_label}</div>
            </div>
            <div>
                <div class="meta-item-label">{t("filed_on")}</div>
                <div class="meta-item-value">{filed_on_label}</div>
            </div>
            <div>
                <div class="meta-item-label">{t("due_date")}</div>
                <div class="{due_class}">{due_date_label}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if complaint.get("resolved_at"):
        st.markdown(
            f"**{t('resolved_on')}:** "
            f"`{_format_datetime(complaint['resolved_at'])}`"
        )

    # Photo (if attached)
    if complaint.get("photo_url"):
        st.image(complaint["photo_url"], width=300)

    # History timeline (newest first, designsystem.md)
    history = complaint.get("history", [])
    if history:
        st.markdown(f"### {t('history')}")
        for entry in history:
            chip = _status_chip_html(entry["status"])
            timestamp = _format_datetime(entry.get("changed_at"))
            note = entry.get("note") or ""

            st.markdown(
                f'<div class="timeline-entry">'
                f'<span class="timestamp">{timestamp}</span> {chip}'
                f"</div>",
                unsafe_allow_html=True,
            )
            if note:
                st.text(f"  {note}")


# ──────────────────────────────────────────────────────────────
# Page Entry Point
# ──────────────────────────────────────────────────────────────

_render_page_header()

tab_file, tab_track = st.tabs([t("file_complaint"), t("check_status")])

with tab_file:
    _complaint_form()

with tab_track:
    _status_lookup()
