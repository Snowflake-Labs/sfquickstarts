"""
Cortex Code Credit Manager - Main Entry Point
===============================================
Sidebar navigation, page dispatch, global CSS.
Admin pages gated by role whitelist (same pattern as MDI DQ app).
"""

import streamlit as st

from config import (
    ADMIN_PAGES,
    ALL_PAGES,
    APP_ICON,
    APP_NAME,
    APP_VERSION,
    COMMON_TIMEZONES,
    DEFAULT_TZ,
    GLOBAL_CSS,
    PAGE_ACCESS_MGMT,
    PAGE_AUDIT_LOG,
    PAGE_BUDGET_FORECAST,
    PAGE_CREDIT_CONFIG,
    PAGE_CREDIT_REQUESTS,
    PAGE_HOME,
    PAGE_MODEL_ACCESS,
    PAGE_SETTINGS,
    PAGE_SETUP,
    PAGE_USAGE_TRENDS,
    USER_PAGES,
    get_current_user,
    user_is_admin,
)
from utils import get_database_list

st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def main():
    from utils import get_session

    session = get_session()
    is_admin = user_is_admin(session)
    current_user = get_current_user(session)

    available_pages = ALL_PAGES if is_admin else USER_PAGES

    with st.sidebar:
        st.markdown(f"### {APP_ICON} {APP_NAME}")
        st.caption(f"v{APP_VERSION}")

        st.divider()

        # Navigation with cleaner icons
        page_icons = {
            PAGE_HOME: "🏠",
            PAGE_ACCESS_MGMT: "🔑",
            PAGE_CREDIT_CONFIG: "💳",
            PAGE_USAGE_TRENDS: "📊",
            PAGE_BUDGET_FORECAST: "💰",
            PAGE_MODEL_ACCESS: "🧠",
            PAGE_CREDIT_REQUESTS: "📋",
            PAGE_SETTINGS: "⚙️",
            PAGE_AUDIT_LOG: "📜",
            PAGE_SETUP: "🔧",
        }

        options = [f"{page_icons.get(p, '•')} {p}" for p in available_pages]
        selected = st.radio("Navigation", options, label_visibility="collapsed",
                            key="cc_nav")

        page_name = selected.split(" ", 1)[1] if selected else PAGE_HOME

        st.divider()

        # Timezone selector — for chart display only, does not affect limits
        tz_labels = [t[0] for t in COMMON_TIMEZONES]
        default_idx = tz_labels.index(DEFAULT_TZ) if DEFAULT_TZ in tz_labels else 0
        st.selectbox(
            "📊 Chart Timezone", tz_labels,
            index=default_idx, key="user_tz",
            help="Shifts heatmap hours for viewing convenience only. Limits reset at midnight UTC."
        )
        st.caption("Limits reset midnight UTC")

        st.divider()

        # Deployment target (admin only) — overrides config.yaml at runtime
        if is_admin:
            st.caption("Deployment Target")
            # Cached — SHOW DATABASES is only fired once per 5 minutes
            db_list = get_database_list(session)
            try:
                current_db = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0] or ""
            except Exception:
                current_db = ""
            try:
                current_schema = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0] or ""
            except Exception:
                current_schema = ""

            selected_db = st.selectbox(
                "Database", db_list,
                index=db_list.index(current_db) if current_db in db_list else 0,
                key="deploy_db",
                help="Database where app tables and SPs are deployed."
            )
            schema_input = st.text_input(
                "Schema", value=current_schema,
                key="deploy_schema",
                help="Schema within the database."
            )
            # Persist in session so config.py getters can use it
            st.session_state["override_db"] = selected_db
            st.session_state["override_schema"] = schema_input

        st.divider()

        # User context
        st.caption(f"Signed in as **{current_user}**")
        if is_admin:
            st.caption("🛡️ Admin")
        else:
            st.caption("👤 Standard user")

    # Page dispatch
    if page_name == PAGE_HOME:
        from pages.home import render
        render(session)
    elif page_name == PAGE_ACCESS_MGMT and is_admin:
        from pages.access_management import render
        render(session)
    elif page_name == PAGE_CREDIT_CONFIG and is_admin:
        from pages.credit_config import render
        render(session)
    elif page_name == PAGE_USAGE_TRENDS and is_admin:
        from pages.usage_trends import render
        render(session)
    elif page_name == PAGE_BUDGET_FORECAST and is_admin:
        from pages.budget_forecast import render
        render(session)
    elif page_name == PAGE_MODEL_ACCESS and is_admin:
        from pages.model_access import render
        render(session)
    elif page_name == PAGE_CREDIT_REQUESTS:
        from pages.credit_requests import render
        render(session)
    elif page_name == PAGE_SETTINGS and is_admin:
        from pages.settings import render
        render(session)
    elif page_name == PAGE_AUDIT_LOG and is_admin:
        from pages.audit_logs import render
        render(session)
    elif page_name == PAGE_SETUP and is_admin:
        from pages.setup import render
        render(session)
    else:
        st.error("⛔ Access denied. This page requires admin privileges.")


main()
