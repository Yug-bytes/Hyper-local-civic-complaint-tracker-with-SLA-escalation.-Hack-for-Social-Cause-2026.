"""Civic Complaint Tracker — entry point.

Loads the design-system CSS, sets up language toggle,
and configures multi-page navigation.
"""

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Civic Complaint Tracker",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="auto",
)

# ── Load design-system CSS (our own file, not user content) ──
_CSS_PATH = Path(__file__).parent / "assets" / "style.css"
if _CSS_PATH.exists():
    st.markdown(
        f"<style>{_CSS_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,  # safe: static CSS file we control
    )

# ── Language toggle (persisted in session state) ──
if "lang" not in st.session_state:
    st.session_state.lang = "en"

lang_choice = st.sidebar.radio(
    "Language / भाषा",
    options=["English", "हिन्दी"],
    index=0 if st.session_state.lang == "en" else 1,
    horizontal=True,
)
st.session_state.lang = "en" if lang_choice == "English" else "hi"

# ── Multi-page navigation ──
citizen_page = st.Page("pages/citizen.py", title="Complaint", icon="📝", default=True)
admin_page = st.Page("pages/admin.py", title="Admin", icon="🔧")
dashboard_page = st.Page("pages/public_dashboard.py", title="Dashboard", icon="📊")

pg = st.navigation([citizen_page, admin_page, dashboard_page])
pg.run()
