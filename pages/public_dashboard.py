"""Public accountability view: department resolution times and overdue metrics.

Follows docs/designsystem.md with phone-first layout, plain-language intro,
leaderboard-style department table, status color tokens, and clean Plotly charts.
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


def _render_page_header() -> None:
    """Render the standard header with project name and one-line description."""
    now_str = datetime.now(timezone.utc).strftime("%d %b %Y, %I:%M %p UTC")

    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-row">
                <div>
                    <div class="page-header-title">{t("app_title")}</div>
                    <div class="page-header-desc">{t("app_description")}</div>
                </div>
                <div class="timestamp-pill">
                    <span>{t("dashboard_updated_at")}: </span>
                    <strong>{now_str}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_plain_language_intro() -> None:
    """Render the short plain-language intro question (Requirement 5)."""
    st.markdown(
        f"""
        <div class="intro-callout">
            <div class="intro-callout-text">{t("dashboard_intro")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_summary_cards(dept_metrics: list[dict]) -> None:
    """Render top 4 summary cards using status color tokens (Requirement 1 & 2)."""
    total_filed = sum(d["total"] for d in dept_metrics)
    total_resolved = sum(d["resolved"] for d in dept_metrics)
    total_open = sum(d.get("open", d["total"] - d["resolved"]) for d in dept_metrics)
    total_overdue = sum(d["overdue"] for d in dept_metrics)

    st.markdown(
        f"""
        <div class="summary-card-grid">
            <div class="summary-card summary-card-total">
                <div class="summary-card-label">{t("dashboard_total_filed")}</div>
                <div class="summary-card-value">{total_filed}</div>
            </div>
            <div class="summary-card summary-card-open">
                <div class="summary-card-label">{t("dashboard_open")}</div>
                <div class="summary-card-value">{total_open}</div>
            </div>
            <div class="summary-card summary-card-time">
                <div class="summary-card-label">{t("dashboard_resolved")}</div>
                <div class="summary-card-value">{total_resolved}</div>
            </div>
            <div class="summary-card summary-card-overdue">
                <div class="summary-card-label summary-label-overdue">
                    {t("dashboard_overdue")}
                </div>
                <div class="summary-card-value summary-value-overdue">
                    {total_overdue}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_explainer_note() -> None:
    """Render a plain-language note explaining what these metrics mean."""
    with st.expander(t("dashboard_explainer_title"), expanded=False):
        st.markdown(t("dashboard_explainer_body"))


def _render_leaderboard_table(dept_metrics: list[dict]) -> None:
    """Render a leaderboard-style department table ranked by resolution performance."""
    st.subheader(t("dashboard_dept_breakdown"))

    # Compute resolution rate and sort for leaderboard ranking
    def sort_key(d: dict) -> tuple[float, float]:
        rate = (d["resolved"] / d["total"]) if d["total"] > 0 else 0.0
        # If tied, departments with lower average resolution time rank higher
        hours = d.get("avg_resolution_hours", 999.0)
        return (rate, -hours)

    ranked_depts = sorted(dept_metrics, key=sort_key, reverse=True)

    table_data = []
    for rank_idx, d in enumerate(ranked_depts, start=1):
        cat_key = CATEGORY_STRING_KEYS.get(d["category"], d["category"])
        dept_name = t(cat_key)
        rate_pct = int((d["resolved"] / d["total"]) * 100) if d["total"] > 0 else 0

        table_data.append(
            {
                t("dashboard_rank"): f"#{rank_idx}",
                t("category"): dept_name,
                t("dashboard_total_filed"): d["total"],
                t("dashboard_resolved"): f"{d['resolved']} ({rate_pct}%)",
                t("dashboard_open"): d.get("open", d["total"] - d["resolved"]),
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
    """Render Plotly charts with clear titles, axis labels, and status colors."""
    chart_font = dict(family="Public Sans, Inter, sans-serif", size=12, color="#1E2A32")

    categories = [
        t(CATEGORY_STRING_KEYS.get(d["category"], d["category"])) for d in dept_metrics
    ]
    resolved_counts = [d["resolved"] for d in dept_metrics]
    open_counts = [d.get("open", d["total"] - d["resolved"]) for d in dept_metrics]
    avg_times = [d["avg_resolution_hours"] for d in dept_metrics]

    # Chart 1: Open vs. Resolved by Department (Stacked Bar)
    st.subheader(t("dashboard_chart_status_breakdown"))
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
            marker_color=STATUS_COLORS[Status.ASSIGNED],
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
            linecolor="#D5DADD",
        ),
        yaxis=dict(
            title=dict(text="Complaints", font=chart_font),
            showgrid=True,
            gridcolor="#F6F7F4",
            linecolor="#D5DADD",
        ),
        margin=dict(l=10, r=10, t=25, b=25),
        height=300,
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

    # Chart 2: Average Resolution Time per Department
    st.subheader(t("dashboard_chart_resolution_time"))
    if any(d["resolved"] > 0 for d in dept_metrics):
        fig_time = px.bar(
            x=categories,
            y=avg_times,
            labels={"x": t("category"), "y": t("admin_hours")},
            color_discrete_sequence=[COLOR_CIVIC],
        )
        fig_time.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=chart_font,
            xaxis=dict(
                title=dict(text=t("category"), font=chart_font),
                showgrid=False,
                linecolor="#D5DADD",
            ),
            yaxis=dict(
                title=dict(text=t("admin_hours"), font=chart_font),
                showgrid=True,
                gridcolor="#F6F7F4",
                linecolor="#D5DADD",
            ),
            margin=dict(l=10, r=10, t=20, b=20),
            height=300,
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info(
            "No complaints have been resolved yet. Average resolution times "
            "will be charted once the first complaint is completed."
        )


# ──────────────────────────────────────────────────────────────
# Main Page Entry
# ──────────────────────────────────────────────────────────────

_render_page_header()
_render_plain_language_intro()

dept_stats = db.get_public_metrics()

if not dept_stats or all(d["total"] == 0 for d in dept_stats):
    st.info("No complaints recorded yet. File the first one!")
else:
    _render_summary_cards(dept_stats)
    _render_explainer_note()
    _render_leaderboard_table(dept_stats)
    _render_charts(dept_stats)
