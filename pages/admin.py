"""Admin dashboard for managing complaints, updating status, and viewing analytics.

Follows docs/designsystem.md with 4 top summary cards using status tokens,
colored status chips, clear overdue visual flags, and standard page header.
Protected by admin password authentication using hmac.compare_digest.
Session state gatekeeper: st.session_state['is_admin'].
"""

import hmac
from datetime import datetime
from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db
from constants import (
    ALLOWED_STATUS_TRANSITIONS,
    CATEGORIES,
    COLOR_CIVIC,
    MAX_NOTE_LENGTH,
    STATUS_COLORS,
    Status,
)
from errors import NotFoundError, StorageError, ValidationError
from services import metrics
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


def _escalation_chip_html(level: int) -> str:
    """Return safe HTML for a red overdue escalation chip."""
    if level == 1:
        label = t("admin_escalation_level_1")
    elif level == 2:
        label = t("admin_escalation_level_2")
    else:
        return ""
    return (
        f'<span class="status-chip chip-overdue" '
        f'style="background-color:#B3261E;">{label}</span>'
    )


def _format_datetime(iso_str: str | None) -> str:
    """Format an ISO datetime string for admin display."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(iso_str)


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
# Authentication
# ──────────────────────────────────────────────────────────────


def _check_password(password_input: str) -> bool:
    """Compare entered password against st.secrets using constant time comparison."""
    admin_password = st.secrets.get("ADMIN_PASSWORD")
    if not admin_password and "admin" in st.secrets:
        admin_password = st.secrets.get("admin", {}).get("password")
    if not admin_password:
        return False

    return hmac.compare_digest(
        password_input.strip().encode("utf-8"),
        str(admin_password).encode("utf-8"),
    )


def _render_login_form() -> None:
    """Render the admin password authentication card."""
    st.subheader(t("admin_title"))
    with st.form("admin_login_form"):
        password_input = st.text_input(
            t("admin_login_prompt"),
            type="password",
            placeholder="Enter admin password",
        )
        submitted = st.form_submit_button(
            t("admin_login_btn"), type="primary", use_container_width=True
        )

    if submitted:
        if _check_password(password_input):
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error(t("admin_password_error"))


# ──────────────────────────────────────────────────────────────
# Admin Summary & Detail Components
# ──────────────────────────────────────────────────────────────


def _render_summary_cards(complaints: list[dict[str, Any]]) -> None:
    """Render 4 summary cards at top using status color tokens (Requirement 1).

    Cards: total complaints, open, overdue, average resolution time in hours.
    """
    total = len(complaints)
    open_count = sum(1 for c in complaints if c.get("status") != Status.RESOLVED)
    overdue = sum(1 for c in complaints if c.get("is_overdue"))
    avg_hours = metrics.avg_resolution_hours(complaints)

    st.markdown(
        f"""
        <div class="summary-card-grid">
            <div class="summary-card summary-card-total">
                <div class="summary-card-label">{t("admin_total_complaints")}</div>
                <div class="summary-card-value">{total}</div>
            </div>
            <div class="summary-card summary-card-open">
                <div class="summary-card-label">{t("admin_open_count")}</div>
                <div class="summary-card-value">{open_count}</div>
            </div>
            <div class="summary-card summary-card-overdue">
                <div class="summary-card-label summary-label-overdue">
                    {t("admin_overdue_count")}
                </div>
                <div class="summary-card-value summary-value-overdue">{overdue}</div>
            </div>
            <div class="summary-card summary-card-time">
                <div class="summary-card-label">{t("admin_avg_resolution")}</div>
                <div class="summary-card-value">
                    {avg_hours}
                    <span class="summary-card-unit">{t('admin_hours')}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_status_update_form(complaint: dict[str, Any]) -> None:
    """Render status update controls for a selected complaint."""
    current_status = complaint["status"]
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_status)

    if not allowed_next:
        st.info(t("admin_already_resolved"))
        return

    st.subheader(t("admin_update_status"))
    next_label = t(STATUS_STRING_KEYS.get(allowed_next, allowed_next))
    st.markdown(f"**{t('admin_next_status')}:** `{next_label}`")

    with st.form("status_update_form"):
        note = st.text_area(
            t("admin_status_note"),
            max_chars=MAX_NOTE_LENGTH,
            placeholder="Optional internal note (e.g. Assigned to Line Inspector)",
        )
        submit_update = st.form_submit_button(
            f"{t('admin_update_status')} → {next_label}",
            type="primary",
            use_container_width=True,
        )

    if submit_update:
        try:
            db.update_status(
                tracking_id=complaint["tracking_id"],
                new_status=allowed_next,
                note=note or None,
            )
            st.success(f"Status updated to '{next_label}'")
            st.rerun()
        except (ValidationError, NotFoundError, StorageError) as exc:
            st.error(str(exc))


def _render_complaint_detail(complaint: dict[str, Any]) -> None:
    """Render details, reporter info, photo, and history for a complaint."""
    st.divider()

    # Status chips & Overdue flag (Requirement 2 & 3)
    chips = _status_chip_html(complaint["status"])
    esc_level = complaint.get("escalation_level", 0)
    is_overdue = complaint.get("is_overdue", False)

    if esc_level > 0:
        chips += " " + _escalation_chip_html(esc_level)
    elif is_overdue:
        chips += (
            f' <span class="status-chip chip-overdue" '
            f'style="background-color:#B3261E;">{t("overdue")}</span>'
        )

    st.markdown(f"### {complaint['tracking_id']}")
    st.markdown(chips, unsafe_allow_html=True)

    # Overdue visual alert if overdue (Requirement 3)
    if is_overdue:
        due_text = _format_datetime(complaint.get("due_at"))
        st.markdown(
            f"""
            <div class="overdue-alert">
                <span>{t("overdue")}:</span>
                <span>Deadline {due_text} has passed.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    cat_key = CATEGORY_STRING_KEYS.get(complaint["category"], complaint["category"])
    cat_label = t(cat_key)
    locality_label = complaint.get("locality", "—")
    filed_on_label = _format_datetime(complaint.get("created_at"))
    due_date_label = _format_datetime(complaint.get("due_at"))

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

    st.markdown(f"**{t('description')}:**")
    st.text(complaint.get("description", ""))

    # Confidential reporter details (admin only)
    name = complaint.get("reporter_name") or "Anonymous"
    phone = complaint.get("reporter_phone") or "Not provided"
    st.markdown(
        f"""
        <div class="confidential-card">
            <strong>{t("admin_reporter_info")}:</strong>
            Name: {name} | Phone: {phone}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if complaint.get("photo_url"):
        st.markdown(f"**{t('photo')}**")
        st.image(complaint["photo_url"], width=300)

    # Status update controls
    _render_status_update_form(complaint)

    # History timeline
    st.subheader(t("history"))
    full_info = db.get_public_status(complaint["tracking_id"])
    history = full_info.get("history", []) if full_info else []
    for entry in history:
        chip = _status_chip_html(entry["status"])
        timestamp = _format_datetime(entry.get("changed_at"))
        by_who = entry.get("changed_by", "system")

        st.markdown(
            f'<div class="timeline-entry">'
            f'<span class="timestamp">{timestamp} ({by_who})</span> {chip}'
            f"</div>",
            unsafe_allow_html=True,
        )
        note = entry.get("note")
        if note:
            st.text(f"  {note}")


def _render_complaints_tab(all_complaints: list[dict[str, Any]]) -> None:
    """Render the complaints filter list and detailed inspection view."""
    col_status, col_cat, col_overdue = st.columns([1, 1, 1])

    with col_status:
        status_options = [""] + [s.value for s in Status]
        status_labels = [t("admin_filter_all")] + [
            t(STATUS_STRING_KEYS.get(s, s)) for s in Status
        ]
        status_idx = st.selectbox(
            t("status"),
            range(len(status_options)),
            format_func=lambda i: status_labels[i],
        )
        selected_status = status_options[status_idx] if status_idx else None

    with col_cat:
        cat_options = [""] + CATEGORIES
        cat_labels = [t("admin_filter_all")] + [
            t(CATEGORY_STRING_KEYS.get(c, c)) for c in CATEGORIES
        ]
        cat_idx = st.selectbox(
            t("category"),
            range(len(cat_options)),
            format_func=lambda i: cat_labels[i],
        )
        selected_cat = cat_options[cat_idx] if cat_idx else None

    with col_overdue:
        st.write("")
        overdue_only = st.checkbox(t("admin_filter_overdue"), value=False)

    filtered = db.list_complaints(
        status=selected_status,
        category=selected_cat,
        overdue_only=overdue_only,
    )

    if not filtered:
        st.info(t("admin_no_complaints"))
        return

    # Clear overdue marker in selector list (Requirement 3)
    options = [
        f"{c['tracking_id']} | {c['category']} | {c['status']}"
        + (" [OVERDUE]" if c.get("is_overdue") else "")
        for c in filtered
    ]
    chosen_idx = st.selectbox(
        t("admin_select_complaint"),
        range(len(filtered)),
        format_func=lambda i: options[i],
    )

    _render_complaint_detail(filtered[chosen_idx])


def _render_analytics_tab(complaints: list[dict[str, Any]]) -> None:
    """Render Plotly charts with clear titles, axis labels, and status colors."""
    if not complaints:
        st.info(t("empty_chart_message"))
        return

    chart_font = dict(family="Public Sans, Inter, sans-serif", size=12, color="#1E2A32")

    # 1. Complaints by Category
    st.subheader("Complaints by Category")
    cat_counts = metrics.counts_by_category(complaints)
    cat_df_labels = [t(CATEGORY_STRING_KEYS.get(k, k)) for k in cat_counts.keys()]
    fig_cat = px.bar(
        x=cat_df_labels,
        y=list(cat_counts.values()),
        labels={"x": t("category"), "y": "Complaints"},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_cat.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(showgrid=False, linecolor="#D5DADD"),
        yaxis=dict(showgrid=True, gridcolor="#F6F7F4", linecolor="#D5DADD"),
        margin=dict(l=10, r=10, t=20, b=20),
        height=280,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    # 2. Complaints by Status (Colored by status tokens, Requirement 4)
    st.subheader("Complaints by Status")
    status_counts = metrics.counts_by_status(complaints)
    status_labels = [t(STATUS_STRING_KEYS.get(s, s)) for s in status_counts.keys()]
    colors = [STATUS_COLORS.get(s, "#6B7785") for s in status_counts.keys()]
    fig_status = go.Figure(
        data=[
            go.Bar(
                x=status_labels,
                y=list(status_counts.values()),
                marker_color=colors,
            )
        ]
    )
    fig_status.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(
            title=dict(text=t("status"), font=chart_font),
            showgrid=False,
            linecolor="#D5DADD",
        ),
        yaxis=dict(
            title=dict(text="Complaints", font=chart_font),
            showgrid=True,
            gridcolor="#F6F7F4",
            linecolor="#D5DADD",
        ),
        margin=dict(l=10, r=10, t=20, b=20),
        height=280,
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # 3. Average Resolution Time per Department
    st.subheader("Average Resolution Time per Department")
    dept_stats = metrics.per_department_stats(complaints)
    dept_labels = [
        t(CATEGORY_STRING_KEYS.get(d["category"], d["category"])) for d in dept_stats
    ]
    avg_times = [d["avg_resolution_hours"] for d in dept_stats]
    if any(d["resolved"] > 0 for d in dept_stats):
        fig_res = px.bar(
            x=dept_labels,
            y=avg_times,
            labels={"x": t("category"), "y": t("admin_hours")},
            color_discrete_sequence=[STATUS_COLORS[Status.RESOLVED]],
        )
        fig_res.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=chart_font,
            xaxis=dict(showgrid=False, linecolor="#D5DADD"),
            yaxis=dict(showgrid=True, gridcolor="#F6F7F4", linecolor="#D5DADD"),
            margin=dict(l=10, r=10, t=20, b=20),
            height=280,
        )
        st.plotly_chart(fig_res, use_container_width=True)
    else:
        st.info(
            "No complaints have been resolved yet. Average resolution times "
            "will be charted once the first complaint is completed."
        )


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

_render_page_header()

if not st.session_state.get("is_admin", False):
    _render_login_form()
else:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.subheader(t("admin_title"))
    with col_logout:
        if st.button(t("admin_logout_btn"), use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()

    all_complaints = db.list_complaints()

    _render_summary_cards(all_complaints)

    tab_manage, tab_charts = st.tabs(
        [t("admin_tab_complaints"), t("admin_tab_analytics")]
    )

    with tab_manage:
        _render_complaints_tab(all_complaints)

    with tab_charts:
        _render_analytics_tab(all_complaints)
