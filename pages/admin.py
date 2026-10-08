"""Admin dashboard for managing complaints, updating status, and viewing analytics.

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
    COLOR_OVERDUE,
    MAX_NOTE_LENGTH,
    STATUS_COLORS,
    Status,
)
from errors import NotFoundError, StorageError, ValidationError
from services import metrics
from strings import CATEGORY_STRING_KEYS, STATUS_STRING_KEYS, t


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
    """Render the admin password prompt."""
    st.header(t("admin_title"))
    with st.form("admin_login_form"):
        password_input = st.text_input(
            t("admin_login_prompt"),
            type="password",
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


def _format_datetime(iso_str: str | None) -> str:
    """Format an ISO datetime string for admin display."""
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(iso_str)


def _status_badge_html(status: str) -> str:
    """Generate safe status chip HTML using fixed color tokens."""
    color = STATUS_COLORS.get(status, "#6B7785")
    label = t(STATUS_STRING_KEYS.get(status, status))
    return f'<span class="status-chip" style="background-color:{color}">{label}</span>'


def _escalation_badge_html(level: int) -> str:
    """Generate safe escalation badge HTML using overdue color token."""
    if level == 1:
        label = t("admin_escalation_level_1")
    elif level == 2:
        label = t("admin_escalation_level_2")
    else:
        return ""
    return (
        f'<span class="status-chip" '
        f'style="background-color:{COLOR_OVERDUE}">{label}</span>'
    )


def _render_summary_metrics(complaints: list[dict[str, Any]]) -> None:
    """Render top summary KPI metrics."""
    total = len(complaints)
    overdue = sum(1 for c in complaints if c.get("is_overdue"))
    resolved = sum(1 for c in complaints if c.get("status") == Status.RESOLVED)
    avg_hours = metrics.avg_resolution_hours(complaints)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("admin_total_complaints"), total)
    col2.metric(t("admin_overdue_count"), overdue)
    col3.metric(t("status_resolved"), resolved)
    col4.metric(
        t("admin_avg_resolution"),
        f"{avg_hours} {t('admin_hours')}",
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
            placeholder="e.g. Assigned to Sanitary Inspector Sharma",
        )
        submit_update = st.form_submit_button(
            t("admin_update_status"),
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
    st.subheader(f"Complaint: {complaint['tracking_id']}")

    # Status chips
    badges = _status_badge_html(complaint["status"])
    esc_level = complaint.get("escalation_level", 0)
    if esc_level > 0:
        badges += " " + _escalation_badge_html(esc_level)
    st.markdown(badges, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t('category')}:**")
        cat_key = CATEGORY_STRING_KEYS.get(complaint["category"], complaint["category"])
        st.text(t(cat_key))
        st.markdown(f"**{t('locality')}:**")
        st.text(complaint.get("locality", "—"))
        st.markdown(f"**{t('filed_on')}:**")
        st.text(_format_datetime(complaint.get("created_at")))
    with col2:
        st.markdown(f"**{t('due_date')}:**")
        st.text(_format_datetime(complaint.get("due_at")))
        if complaint.get("resolved_at"):
            st.markdown(f"**{t('resolved_on')}:**")
            st.text(_format_datetime(complaint["resolved_at"]))

    # Description (rendered safely as text, not HTML)
    st.markdown(f"**{t('description')}:**")
    st.text(complaint.get("description", ""))

    # Reporter info (private, admin only)
    st.markdown(f"**{t('admin_reporter_info')}:**")
    name = complaint.get("reporter_name") or "Anonymous"
    phone = complaint.get("reporter_phone") or "Not provided"
    st.text(f"Name: {name} | Phone: {phone}")

    # Photo (if attached)
    if complaint.get("photo_url"):
        st.image(complaint["photo_url"], width=350)

    # Status update controls
    _render_status_update_form(complaint)

    # Status history timeline
    st.subheader(t("history"))
    full_info = db.get_public_status(complaint["tracking_id"])
    history = full_info.get("history", []) if full_info else []
    for entry in history:
        chip = _status_badge_html(entry["status"])
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
    # Filter controls
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
        overdue_only = st.checkbox(t("admin_filter_overdue"), value=False)

    # Query filtered complaints
    filtered = db.list_complaints(
        status=selected_status,
        category=selected_cat,
        overdue_only=overdue_only,
    )

    if not filtered:
        st.info(t("admin_no_complaints"))
        return

    # Selection for detailed view
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
    """Render Plotly charts for categories, statuses, and resolution time."""
    if not complaints:
        st.info(t("admin_no_complaints"))
        return

    # 1. Complaints by Category
    st.subheader("Complaints by Category")
    cat_counts = metrics.counts_by_category(complaints)
    cat_df_labels = [t(CATEGORY_STRING_KEYS.get(k, k)) for k in cat_counts.keys()]
    fig_cat = px.bar(
        x=cat_df_labels,
        y=list(cat_counts.values()),
        labels={"x": t("category"), "y": "Count"},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_cat.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(fig_cat, use_container_width=True)

    # 2. Complaints by Status
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
        xaxis_title=t("status"),
        yaxis_title="Count",
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
    )
    st.plotly_chart(fig_status, use_container_width=True)

    # 3. Average Resolution Time per Department
    st.subheader("Average Resolution Time (Hours)")
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
    fig_res.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
    st.plotly_chart(fig_res, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

if not st.session_state.get("is_admin", False):
    _render_login_form()
else:
    # Header with title and logout button
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.header(t("admin_title"))
    with col_logout:
        if st.button(t("admin_logout_btn"), use_container_width=True):
            st.session_state["is_admin"] = False
            st.rerun()

    # Fetch all complaints to power metrics and tabs
    all_complaints = db.list_complaints()

    _render_summary_metrics(all_complaints)

    tab_manage, tab_charts = st.tabs(
        [t("admin_tab_complaints"), t("admin_tab_analytics")]
    )

    with tab_manage:
        _render_complaints_tab(all_complaints)

    with tab_charts:
        _render_analytics_tab(all_complaints)
