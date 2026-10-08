"""Citizen-facing page: file a complaint and check its status.

Production-grade civic-tech UI with zero emojis, clean SaaS cards,
visual step progress timeline, and robust security protections.
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
    Status,
)
from errors import StorageError, ValidationError
from strings import CATEGORY_STRING_KEYS, STATUS_STRING_KEYS, t

# ──────────────────────────────────────────────────────────────
# Visual Badge & Timeline Helpers (Safe HTML - System Tokens Only)
# ──────────────────────────────────────────────────────────────


def _status_badge_html(status: str) -> str:
    """Return safe HTML for a modern status badge with dot indicator."""
    badge_class = f"badge-{status}"
    label = t(STATUS_STRING_KEYS.get(status, status))
    return (
        f'<span class="status-badge {badge_class}">'
        f'<span class="dot"></span>{label}'
        f"</span>"
    )


def _overdue_badge_html() -> str:
    """Return safe HTML for an overdue danger badge."""
    label = t("overdue")
    return (
        f'<span class="status-badge badge-overdue">'
        f'<span class="dot"></span>{label}'
        f"</span>"
    )


def _format_datetime(iso_str: str | None) -> str:
    """Format an ISO datetime string into human-readable standard format."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(iso_str)


def _render_stepper(current_status: str) -> None:
    """Render a modern visual 4-step progress indicator."""
    steps = [
        (Status.SUBMITTED, t("status_submitted")),
        (Status.ASSIGNED, t("status_assigned")),
        (Status.IN_PROGRESS, t("status_in_progress")),
        (Status.RESOLVED, t("status_resolved")),
    ]

    status_order = {
        Status.SUBMITTED: 0,
        Status.ASSIGNED: 1,
        Status.IN_PROGRESS: 2,
        Status.RESOLVED: 3,
    }
    current_idx = status_order.get(current_status, 0)

    step_items_html = []
    for idx, (_, label) in enumerate(steps):
        if idx < current_idx:
            state_class = "completed"
            icon_content = "&#10003;"
        elif idx == current_idx:
            state_class = "active"
            icon_content = str(idx + 1)
        else:
            state_class = ""
            icon_content = str(idx + 1)

        step_items_html.append(
            f'<div class="step-item {state_class}">'
            f'<div class="step-indicator">{icon_content}</div>'
            f'<div class="step-label">{label}</div>'
            f"</div>"
        )

    stepper_html = f'<div class="stepper-container">{"".join(step_items_html)}</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)


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
# Complaint Submission Form
# ──────────────────────────────────────────────────────────────


def _complaint_form() -> None:
    """Render the structured complaint submission form."""
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-left">
                <div class="app-header-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                         stroke="#2563EB" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <path
                            d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2"
                        />
                        <path d="M18 22h2a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                        <polyline points="10 9 9 9 8 9"/>
                    </svg>
                </div>
                <div>
                    <div class="app-header-title">{t("file_complaint")}</div>
                    <div class="app-header-desc">
                        Submit your grievance for routing and SLA tracking.
                    </div>
                </div>
            </div>
            <div class="app-header-badge">Automated SLA Routing</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    category_options = [""] + CATEGORIES
    category_labels = [t("select_category")] + [
        t(CATEGORY_STRING_KEYS[c]) for c in CATEGORIES
    ]

    with st.form("complaint_form", clear_on_submit=True):
        col_cat, col_loc = st.columns(2)
        with col_cat:
            category_idx = st.selectbox(
                t("category"),
                range(len(category_options)),
                format_func=lambda i: category_labels[i],
            )
            selected_category = category_options[category_idx] if category_idx else ""

        with col_loc:
            locality = st.text_input(
                t("locality"),
                max_chars=MAX_LOCALITY_LENGTH,
                placeholder="e.g. Ward 14, Main Road near Community Center",
            )

        description = st.text_area(
            t("description"),
            max_chars=MAX_DESCRIPTION_LENGTH,
            placeholder="Provide specific details about the issue...",
            help=t("description_help"),
        )

        st.markdown(
            f'<div class="field-label">{t("photo")}</div>',
            unsafe_allow_html=True,
        )
        st.caption(t("photo_warning"))
        photo_file = st.file_uploader(
            t("photo"),
            type=["jpg", "jpeg", "png"],
            help=f"JPG or PNG format, max {MAX_PHOTO_MB} MB",
            label_visibility="collapsed",
        )

        col_name, col_phone = st.columns(2)
        with col_name:
            name = st.text_input(t("name"), placeholder="Optional citizen name")
        with col_phone:
            phone = st.text_input(
                t("phone"), placeholder="Optional 10-digit mobile number"
            )

        st.markdown(
            f"""
            <div class="privacy-notice">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                     stroke="#64748B" stroke-width="2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                <span>{t("consent")}</span>
            </div>
            """,
            unsafe_allow_html=True,
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


# ──────────────────────────────────────────────────────────────
# Success Screen
# ──────────────────────────────────────────────────────────────


def _show_success(tracking_id: str) -> None:
    """Display the tracking ID hero card after successful submission."""
    st.markdown(
        f"""
        <div class="tracking-hero-card">
            <div class="hero-success-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2.5"
                     stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                </svg>
            </div>
            <div class="hero-success-title">{t("complaint_saved")}</div>
            <div class="tracking-hero-label">{t("tracking_id_label")}</div>
            <div class="tracking-hero-value">{tracking_id}</div>
            <div class="tracking-hero-sub">{t("tracking_id_instruction")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Status Lookup
# ──────────────────────────────────────────────────────────────


def _status_lookup() -> None:
    """Render the tracking ID lookup hero input and search handler."""
    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-left">
                <div class="app-header-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                         stroke="#2563EB" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="11" cy="11" r="8"/>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
                    </svg>
                </div>
                <div>
                    <div class="app-header-title">{t("check_status")}</div>
                    <div class="app-header-desc">
                        Track progress, department assignment, and SLA status.
                    </div>
                </div>
            </div>
            <div class="app-header-badge">Public Tracking</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    """Fetch and display complaint status, visual progress stepper, and history."""
    complaint = db.get_public_status(tracking_id)

    if complaint is None:
        st.warning(t("no_complaint_found"))
        return

    is_overdue = False
    if complaint["status"] != Status.RESOLVED and complaint.get("due_at"):
        try:
            due_dt = datetime.fromisoformat(complaint["due_at"])
            if datetime.now(due_dt.tzinfo) > due_dt:
                is_overdue = True
        except (ValueError, TypeError):
            pass

    badges_html = _status_badge_html(complaint["status"])
    if is_overdue:
        badges_html += " " + _overdue_badge_html()

    st.markdown(
        f"""
        <div class="status-bar">
            <div>
                <div class="status-bar-title">Complaint ID</div>
                <div class="status-bar-id">{tracking_id}</div>
            </div>
            <div>
                {badges_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_stepper(complaint["status"])

    cat_key = CATEGORY_STRING_KEYS.get(complaint["category"], complaint["category"])
    cat_label = t(cat_key)
    locality_label = complaint.get("locality", "—")
    filed_on_label = _format_datetime(complaint.get("created_at"))
    due_date_label = _format_datetime(complaint.get("due_at"))
    resolved_on_label = (
        _format_datetime(complaint.get("resolved_at"))
        if complaint.get("resolved_at")
        else None
    )

    resolved_html = (
        f"""
        <div>
            <div class="meta-item-label">{t("resolved_on")}</div>
            <div class="meta-item-value">{resolved_on_label}</div>
        </div>
        """
        if resolved_on_label
        else ""
    )

    meta_cols = f"""
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
            <div class="meta-item-value">{due_date_label}</div>
        </div>
        {resolved_html}
    </div>
    """
    st.markdown(meta_cols, unsafe_allow_html=True)

    if complaint.get("photo_url"):
        st.markdown(f"**{t('photo')}**")
        st.image(complaint["photo_url"], width=340)

    history = complaint.get("history", [])
    if history:
        st.markdown(
            f'<div class="section-heading">{t("history")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="activity-timeline">', unsafe_allow_html=True)
        for entry in history:
            badge = _status_badge_html(entry["status"])
            timestamp = _format_datetime(entry.get("changed_at"))
            note = entry.get("note") or ""

            st.markdown(
                f"""
                <div class="activity-item">
                    <div class="activity-meta">
                        <span>{timestamp}</span>
                        {badge}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if note:
                st.text(f"  {note}")
        st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Page Entry Point
# ──────────────────────────────────────────────────────────────

tab_file, tab_track = st.tabs([t("file_complaint"), t("check_status")])

with tab_file:
    _complaint_form()

with tab_track:
    _status_lookup()
