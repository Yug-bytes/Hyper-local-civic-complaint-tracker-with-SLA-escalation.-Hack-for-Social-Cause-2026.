"""Civic Complaint Tracker — entry point.

Loads the modern SaaS design system, provides clean branded sidebar navigation,
and manages persistent language state without any emojis.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Civic Complaint Tracker",
    page_icon=":material/account_balance:",
    layout="centered",
    initial_sidebar_state="auto",
)

# ── Load design-system CSS (static CSS file we control) ──
_CSS_PATH = Path(__file__).parent / "assets" / "style.css"
if _CSS_PATH.exists():
    st.markdown(
        f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

# ── Persistent session state defaults ──
if "lang" not in st.session_state:
    st.session_state.lang = "en"

# ── Clean Branded Sidebar Header ──
st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                 stroke="#2563EB" stroke-width="2.2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 21h18"/>
                <path d="M5 21V7l7-4 7 4v14"/>
                <path d="M9 10a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v11H9V10z"/>
            </svg>
            <span>Civic Portal</span>
        </div>
        <div class="sidebar-brand-sub">Public Infrastructure & SLA Tracker</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Multi-page navigation (grouped with Material Symbols icons, NO emojis) ──
citizen_page = st.Page(
    "pages/citizen.py",
    title="Complaints",
    icon=":material/assignment:",
    default=True,
)
dashboard_page = st.Page(
    "pages/public_dashboard.py",
    title="Dashboard",
    icon=":material/dashboard:",
)
admin_page = st.Page(
    "pages/admin.py",
    title="Admin",
    icon=":material/shield:",
)

pg = st.navigation(
    {
        "MAIN": [dashboard_page, citizen_page],
        "MANAGEMENT": [admin_page],
    }
)

# ── Language selector in sidebar ──
st.sidebar.markdown(
    """
    <div class="sidebar-lang-wrapper">
        <div class="sidebar-section-title">Language / भाषा</div>
    </div>
    """,
    unsafe_allow_html=True,
)
lang_choice = st.sidebar.radio(
    "Select Language",
    options=["English", "हिन्दी"],
    index=0 if st.session_state.lang == "en" else 1,
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state.lang = "en" if lang_choice == "English" else "hi"

pg.run()
