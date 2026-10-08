"""Admin dashboard for managing complaints, updating status, and viewing analytics.

Protected by admin password authentication using hmac.compare_digest.
Session state gatekeeper: st.session_state['is_admin'].
Zero emojis, production-grade civic-tech SaaS UI with clean badges and Plotly charts.
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


def _status_badge_html(status: str) -> str:
    """Generate safe status badge HTML with dot indicator."""
    badge_class = f"badge-{status}"
    label = t(STATUS_STRING_KEYS.get(status, status))
    return (
        f'<span class="status-badge {badge_class}">'
        f'<span class="dot"></span>{label}'
        f"</span>"
    )


def _escalation_badge_html(level: int) -> str:
    """Generate safe escalation badge HTML using danger alert styling."""
    if level == 1:
        label = t("admin_escalation_level_1")
    elif level == 2:
        label = t("admin_escalation_level_2")
    else:
        return ""
    return (
        f'<span class="status-badge badge-overdue">'
        f'<span class="dot"></span>{label}'
        f"</span>"
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
    """Render the clean admin authentication card."""
    st.markdown(
        f"""
        <div class="login-container">
            <div class="login-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="2.2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
            </div>
            <div class="login-title">{t("admin_title")}</div>
            <div class="login-subtitle">
                Enter municipal credentials to access administrative controls.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("admin_login_form"):
        password_input = st.text_input(
            t("admin_login_prompt"),
            type="password",
            placeholder="••••••••••••",
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


def _render_summary_metrics(complaints: list[dict[str, Any]]) -> None:
    """Render top summary KPI metrics."""
    total = len(complaints)
    overdue = sum(1 for c in complaints if c.get("is_overdue"))
    resolved = sum(1 for c in complaints if c.get("status") == Status.RESOLVED)
    avg_hours = metrics.avg_resolution_hours(complaints)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("admin_total_complaints"), total)
    with col2:
        st.metric(t("admin_overdue_count"), overdue)
    with col3:
        st.metric(t("status_resolved"), resolved)
    with col4:
        st.metric(t("admin_avg_resolution"), f"{avg_hours} {t('admin_hours')}")


def _render_status_update_form(complaint: dict[str, Any]) -> None:
    """Render status update controls for a selected complaint."""
    current_status = complaint["status"]
    allowed_next = ALLOWED_STATUS_TRANSITIONS.get(current_status)

    if not allowed_next:
        st.info(t("admin_already_resolved"))
        return

    next_label = t(STATUS_STRING_KEYS.get(allowed_next, allowed_next))

    st.markdown(
        f"""
        <div class="action-card">
            <div class="action-card-header">
                <div class="action-card-title">{t("admin_update_status")}</div>
                <div class="action-card-next">
                    <span>{t("admin_next_status")}: </span>
                    <strong>{next_label}</strong>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("status_update_form"):
        note = st.text_area(
            t("admin_status_note"),
            max_chars=MAX_NOTE_LENGTH,
            placeholder="e.g. Assigned to Sanitary Inspector Sharma (Ward 14)",
            label_visibility="visible",
        )
        submit_update = st.form_submit_button(
            f"{t('admin_update_status')} → {next_label}",
            type="primary",
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

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
    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

    badges = _status_badge_html(complaint["status"])
    esc_level = complaint.get("escalation_level", 0)
    if esc_level > 0:
        badges += " " + _escalation_badge_html(esc_level)

    st.markdown(
        f"""
        <div class="status-bar">
            <div>
                <div class="status-bar-title">Selected Complaint</div>
                <div class="status-bar-id">{complaint['tracking_id']}</div>
            </div>
            <div>
                {badges}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown(f"**{t('description')}**")
    st.text(complaint.get("description", ""))

    name = complaint.get("reporter_name") or "Anonymous"
    phone = complaint.get("reporter_phone") or "Not provided"
    st.markdown(
        f"""
        <div class="confidential-card">
            <div class="confidential-title">
                {t("admin_reporter_info")} (Internal / Privileged)
            </div>
            <div class="confidential-body">
                Name: <strong>{name}</strong> &nbsp;|&nbsp;
                Phone: <strong>{phone}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if complaint.get("photo_url"):
        st.markdown(f"**{t('photo')}**")
        st.image(complaint["photo_url"], width=350)

    _render_status_update_form(complaint)

    full_info = db.get_public_status(complaint["tracking_id"])
    history = full_info.get("history", []) if full_info else []
    if history:
        st.markdown(
            f'<div class="section-heading">{t("history")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="activity-timeline">', unsafe_allow_html=True)
        for entry in history:
            chip = _status_badge_html(entry["status"])
            timestamp = _format_datetime(entry.get("changed_at"))
            by_who = entry.get("changed_by", "system")

            st.markdown(
                f"""
                <div class="activity-item">
                    <div class="activity-meta">
                        <span>{timestamp} ({by_who})</span>
                        {chip}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            note = entry.get("note")
            if note:
                st.text(f"  {note}")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_complaints_tab(all_complaints: list[dict[str, Any]]) -> None:
    """Render the complaints filter list and detailed inspection view."""
    st.markdown(
        """
        <div class="status-bar-title" style="margin-bottom: 8px;">
            Filter Complaints
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        overdue_only = st.checkbox(t("admin_filter_overdue"), value=False)

    filtered = db.list_complaints(
        status=selected_status,
        category=selected_cat,
        overdue_only=overdue_only,
    )

    if not filtered:
        st.info(t("admin_no_complaints"))
        return

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
    """Render minimal Plotly charts for categories, statuses, and times."""
    if not complaints:
        st.info(t("admin_no_complaints"))
        return

    chart_font = dict(
        family="Inter, -apple-system, sans-serif", size=12, color="#475569"
    )

    # 1. Complaints by Category
    st.markdown(
        '<div class="section-heading">Complaints by Category</div>',
        unsafe_allow_html=True,
    )
    cat_counts = metrics.counts_by_category(complaints)
    cat_df_labels = [t(CATEGORY_STRING_KEYS.get(k, k)) for k in cat_counts.keys()]
    fig_cat = px.bar(
        x=cat_df_labels,
        y=list(cat_counts.values()),
        labels={"x": t("category"), "y": "Count"},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_cat.update_traces(marker_line_width=0)
    fig_cat.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0"),
        margin=dict(l=30, r=20, t=20, b=30),
        height=300,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    # 2. Complaints by Status
    st.markdown(
        '<div class="section-heading">Complaints by Status</div>',
        unsafe_allow_html=True,
    )
    status_counts = metrics.counts_by_status(complaints)
    status_labels = [t(STATUS_STRING_KEYS.get(s, s)) for s in status_counts.keys()]
    colors = [STATUS_COLORS.get(s, "#64748B") for s in status_counts.keys()]
    fig_status = go.Figure(
        data=[
            go.Bar(
                x=status_labels,
                y=list(status_counts.values()),
                marker_color=colors,
                marker_line_width=0,
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
            linecolor="#E2E8F0",
        ),
        yaxis=dict(
            title=dict(text="Count", font=chart_font),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
        ),
        margin=dict(l=30, r=20, t=20, b=30),
        height=300,
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # 3. Average Resolution Time per Department
    st.markdown(
        '<div class="section-heading">Average Resolution Time (Hours)</div>',
        unsafe_allow_html=True,
    )
    dept_stats = metrics.per_department_stats(complaints)
    dept_labels = [
        t(CATEGORY_STRING_KEYS.get(d["category"], d["category"])) for d in dept_stats
    ]
    avg_times = [d["avg_resolution_hours"] for d in dept_stats]
    fig_res = px.bar(
        x=dept_labels,
        y=avg_times,
        labels={"x": t("category"), "y": t("admin_hours")},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_res.update_traces(marker_line_width=0)
    fig_res.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(showgrid=False, linecolor="#E2E8F0"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", linecolor="#E2E8F0"),
        margin=dict(l=30, r=20, t=20, b=30),
        height=300,
    )
    st.plotly_chart(fig_res, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

if not st.session_state.get("is_admin", False):
    _render_login_form()
else:
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.markdown(
            f"""
            <div class="app-header">
                <div class="app-header-left">
                    <div class="app-header-icon">
                        <svg width="22" height="22" viewBox="0 0 24 24"
                             fill="none" stroke="#2563EB" stroke-width="2"
                             stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                    </div>
                    <div>
                        <div class="app-header-title">{t("admin_title")}</div>
                        <div class="app-header-desc">
                            Municipal grievance administration console.
                        </div>
                    </div>
                </div>
                <div class="app-header-badge">Admin Session Active</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_logout:
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button(t("admin_logout_btn"), use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()

    all_complaints = db.list_complaints()

    _render_summary_metrics(all_complaints)

    tab_manage, tab_charts = st.tabs(
        [t("admin_tab_complaints"), t("admin_tab_analytics")]
    )

    with tab_manage:
        _render_complaints_tab(all_complaints)

    with tab_charts:
        _render_analytics_tab(all_complaints)
