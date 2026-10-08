"""Public accountability view: department resolution times and overdue metrics.

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


def _render_summary_kpis(dept_metrics: list[dict]) -> None:
    """Render top summary numbers across all departments."""
    total_filed = sum(d["total"] for d in dept_metrics)
    total_resolved = sum(d["resolved"] for d in dept_metrics)
    total_open = sum(d.get("open", d["total"] - d["resolved"]) for d in dept_metrics)
    total_overdue = sum(d["overdue"] for d in dept_metrics)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("dashboard_total_filed"), total_filed)
    col2.metric(t("dashboard_open"), total_open)
    col3.metric(t("dashboard_resolved"), total_resolved)
    col4.metric(t("dashboard_overdue"), total_overdue)


def _render_explainer_note() -> None:
    """Render a plain-language note explaining what these metrics mean."""
    with st.expander(f"ℹ️ {t('dashboard_explainer_title')}", expanded=False):
        st.markdown(t("dashboard_explainer_body"))


def _render_department_table(dept_metrics: list[dict]) -> None:
    """Render a clean summary table of department performance."""
    st.subheader(t("dashboard_dept_breakdown"))

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
    """Render Plotly charts for department speeds and open vs resolved."""
    # 1. Stacked bar chart: Open vs. Resolved by Department
    st.subheader(t("dashboard_chart_status_breakdown"))

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
        )
    )
    fig_stack.add_trace(
        go.Bar(
            name=t("dashboard_open"),
            x=categories,
            y=open_counts,
            marker_color=STATUS_COLORS[Status.IN_PROGRESS],
        )
    )
    fig_stack.update_layout(
        barmode="stack",
        xaxis_title=t("category"),
        yaxis_title="Count",
        margin=dict(l=20, r=20, t=20, b=20),
        height=320,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_stack, use_container_width=True)

    # 2. Bar chart: Average Resolution Time per Department
    st.subheader(t("dashboard_chart_resolution_time"))
    avg_times = [d["avg_resolution_hours"] for d in dept_metrics]

    fig_time = px.bar(
        x=categories,
        y=avg_times,
        labels={"x": t("category"), "y": t("admin_hours")},
        color_discrete_sequence=[COLOR_CIVIC],
    )
    fig_time.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
    )
    st.plotly_chart(fig_time, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

st.header(t("dashboard_title"))
st.caption(t("dashboard_subtitle"))

# Timestamp
now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")
st.markdown(f"**{t('dashboard_updated_at')}:** `{now_str}`")

# Fetch public metrics ONLY (no personal data, no descriptions)
dept_stats = db.get_public_metrics()

if not dept_stats or all(d["total"] == 0 for d in dept_stats):
    st.info("No complaints recorded yet. File the first one!")
else:
    _render_summary_kpis(dept_stats)
    _render_explainer_note()
    _render_department_table(dept_stats)
    _render_charts(dept_stats)
