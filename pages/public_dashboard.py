"""Public accountability view: department resolution times and overdue metrics.

Production-grade civic dashboard with zero emojis, modern SaaS styling,
clean Plotly themes, and strict privacy protection.
Uses ONLY db.get_public_metrics().
Never accesses personal data, names, phones, or complaint descriptions.
"""

from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db
from constants import COLOR_CIVIC, STATUS_COLORS, Status
from strings import CATEGORY_STRING_KEYS, t

# ──────────────────────────────────────────────────────────────
# Dashboard Components
# ──────────────────────────────────────────────────────────────


def _render_header() -> None:
    """Render top hero header and live timestamp."""
    now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

    st.markdown(
        f"""
        <div class="app-header">
            <div class="app-header-left">
                <div class="app-header-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                         stroke="#2563EB" stroke-width="2"
                         stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="20" x2="18" y2="10"/>
                        <line x1="12" y1="20" x2="12" y2="4"/>
                        <line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                </div>
                <div>
                    <div class="app-header-title">{t("dashboard_title")}</div>
                    <div class="app-header-desc">{t("dashboard_subtitle")}</div>
                </div>
            </div>
            <div class="app-header-timestamp">
                <span>{t("dashboard_updated_at")}: </span>
                <strong>{now_str}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_kpis(dept_metrics: list[dict]) -> None:
    """Render top summary KPI cards across all departments."""
    total_filed = sum(d["total"] for d in dept_metrics)
    total_resolved = sum(d["resolved"] for d in dept_metrics)
    total_open = sum(d.get("open", d["total"] - d["resolved"]) for d in dept_metrics)
    total_overdue = sum(d["overdue"] for d in dept_metrics)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("dashboard_total_filed"), total_filed)
    with col2:
        st.metric(t("dashboard_open"), total_open)
    with col3:
        st.metric(t("dashboard_resolved"), total_resolved)
    with col4:
        st.metric(t("dashboard_overdue"), total_overdue)


def _render_explainer_note() -> None:
    """Render a plain-language note explaining what these metrics mean."""
    with st.expander(t("dashboard_explainer_title"), expanded=False):
        st.markdown(
            f'<div class="explainer-body">{t("dashboard_explainer_body")}</div>',
            unsafe_allow_html=True,
        )


def _render_department_table(dept_metrics: list[dict]) -> None:
    """Render a clean summary table of department performance."""
    st.markdown(
        f'<div class="section-heading">{t("dashboard_dept_breakdown")}</div>',
        unsafe_allow_html=True,
    )

    table_data = []
    for d in dept_metrics:
        cat_key = CATEGORY_STRING_KEYS.get(d["category"], d["category"])
        table_data.append(
            {
                t("category"): t(cat_key),
                t("dashboard_total_filed"): d["total"],
                t("dashboard_open"): d.get("open", d["total"] - d["resolved"]),
                t("dashboard_resolved"): d["resolved"],
                t("dashboard_overdue"): d["overdue"],
                t("dashboard_chart_resolution_time"): (
                    f"{d['avg_resolution_hours']} {t('admin_hours')}"
                    if d["resolved"] > 0
                    else "—"
                ),
            }
        )

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _render_charts(dept_metrics: list[dict]) -> None:
    """Render Plotly charts with a modern SaaS minimal theme."""
    chart_font = dict(
        family="Inter, -apple-system, sans-serif", size=12, color="#475569"
    )

    # 1. Stacked bar chart: Open vs. Resolved by Department
    st.markdown(
        f'<div class="section-heading">{t("dashboard_chart_status_breakdown")}</div>',
        unsafe_allow_html=True,
    )

    categories = [
        t(CATEGORY_STRING_KEYS.get(d["category"], d["category"])) for d in dept_metrics
    ]
    resolved_counts = [d["resolved"] for d in dept_metrics]
    open_counts = [d.get("open", d["total"] - d["resolved"]) for d in dept_metrics]

    fig_stack = go.Figure()
    fig_stack.add_trace(
        go.Bar(
            name=t("dashboard_resolved"),
            x=categories,
            y=resolved_counts,
            marker_color=STATUS_COLORS[Status.RESOLVED],
            marker_line_width=0,
        )
    )
    fig_stack.add_trace(
        go.Bar(
            name=t("dashboard_open"),
            x=categories,
            y=open_counts,
            marker_color=STATUS_COLORS[Status.ASSIGNED],
            marker_line_width=0,
        )
    )
    fig_stack.update_layout(
        barmode="stack",
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(
            title=dict(text=t("category"), font=chart_font),
            showgrid=False,
            linecolor="#E2E8F0",
        ),
        yaxis=dict(
            title=dict(text="Count", font=chart_font),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
        ),
        margin=dict(l=30, r=20, t=30, b=30),
        height=320,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=chart_font,
        ),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # 2. Bar chart: Average Resolution Time per Department
    st.markdown(
        f'<div class="section-heading">{t("dashboard_chart_resolution_time")}</div>',
        unsafe_allow_html=True,
    )
    avg_times = [d["avg_resolution_hours"] for d in dept_metrics]

    fig_time = px.bar(
        x=categories,
        y=avg_times,
        labels={"x": t("category"), "y": t("admin_hours")},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_time.update_traces(marker_line_width=0)
    fig_time.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=chart_font,
        xaxis=dict(
            title=dict(text=t("category"), font=chart_font),
            showgrid=False,
            linecolor="#E2E8F0",
        ),
        yaxis=dict(
            title=dict(text=t("admin_hours"), font=chart_font),
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#E2E8F0",
        ),
        margin=dict(l=30, r=20, t=20, b=30),
        height=300,
    )
    st.plotly_chart(fig_time, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

_render_header()

dept_stats = db.get_public_metrics()

if not dept_stats or all(d["total"] == 0 for d in dept_stats):
    st.info("No complaints recorded yet. File the first one to view live metrics.")
else:
    _render_summary_kpis(dept_stats)
    _render_explainer_note()
    _render_department_table(dept_stats)
    _render_charts(dept_stats)
