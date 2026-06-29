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
    PAGE_ALERTS,
    PAGE_AUDIT_LOG,
    PAGE_COST_ATTRIBUTION,
    PAGE_CREDIT_CONFIG,
    PAGE_CREDIT_REQUESTS,
    PAGE_HOME,
    PAGE_MODEL_ACCESS,
    PAGE_MODEL_INTEL,
    PAGE_OBSERVABILITY,
    PAGE_POLICY_RULES,
    PAGE_PROMPT_ANALYSIS,
    PAGE_USER_INTEL,
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

        page_icons = {
            PAGE_HOME:             "🏠",
            PAGE_SETUP:            "🔧",
            PAGE_SETTINGS:         "⚙️",
            PAGE_AUDIT_LOG:        "📜",
            PAGE_ACCESS_MGMT:      "🔑",
            PAGE_CREDIT_CONFIG:    "💳",
            PAGE_MODEL_ACCESS:     "🧠",
            PAGE_CREDIT_REQUESTS:  "📋",
            PAGE_USAGE_TRENDS:     "📊",
            PAGE_COST_ATTRIBUTION: "💰",
            PAGE_OBSERVABILITY:    "🔍",
            PAGE_USER_INTEL:       "🕵️",
            PAGE_PROMPT_ANALYSIS:  "⚠️",
            PAGE_POLICY_RULES:     "🛡️",
            PAGE_ALERTS:           "🔔",
            PAGE_MODEL_INTEL:      "🧬",
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
            db_list = get_database_list(session)
            try:
                current_db = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0] or ""
            except Exception:
                current_db = ""
            try:
                current_schema = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0] or ""
            except Exception:
                current_schema = ""

            # Initialize from config.yaml first — CURRENT_DATABASE() can return
            # USER$<username> in enterprise accounts without a default DB set.
            from config import DEPLOYMENT_DATABASE, DEPLOYMENT_SCHEMA
            if "override_db" not in st.session_state:
                st.session_state["override_db"] = DEPLOYMENT_DATABASE or current_db
            if "override_schema" not in st.session_state:
                st.session_state["override_schema"] = DEPLOYMENT_SCHEMA or current_schema

            # Always render outside the init-if so inputs persist across reruns
            selected_db = st.selectbox(
                "Database", db_list,
                index=db_list.index(st.session_state["override_db"])
                      if st.session_state["override_db"] in db_list else 0,
                key="deploy_db",
                help="Database where app tables and SPs are deployed."
            )
            schema_input = st.text_input(
                "Schema",
                value=st.session_state.get("override_schema", DEPLOYMENT_SCHEMA or ""),
                key="deploy_schema",
                help="Schema within the database."
            )
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
        from views.home import render
        render(session)
    elif page_name == PAGE_ACCESS_MGMT and is_admin:
        from views.access_management import render
        render(session)
    elif page_name == PAGE_CREDIT_CONFIG and is_admin:
        from views.credit_config import render
        render(session)
    elif page_name == PAGE_USAGE_TRENDS and is_admin:
        from views.usage_trends import render
        render(session)
    elif page_name == PAGE_MODEL_ACCESS and is_admin:
        from views.model_access import render
        render(session)
    elif page_name == PAGE_CREDIT_REQUESTS:
        from views.credit_requests import render
        render(session)
    elif page_name == PAGE_SETTINGS and is_admin:
        from views.settings import render
        render(session)
    elif page_name == PAGE_AUDIT_LOG and is_admin:
        from views.audit_logs import render
        render(session)
    elif page_name == PAGE_SETUP and is_admin:
        from views.setup import render
        render(session)
    elif page_name == PAGE_OBSERVABILITY and is_admin:
        from views.observability import render
        render(session)
    elif page_name == PAGE_COST_ATTRIBUTION and is_admin:
        from views.cost_attribution import render
        render(session)
    elif page_name == PAGE_PROMPT_ANALYSIS and is_admin:
        from views.prompt_analysis import render
        render(session)
    elif page_name == PAGE_USER_INTEL and is_admin:
        from views.user_intelligence import render
        render(session)
    elif page_name == PAGE_POLICY_RULES and is_admin:
        from views.policy_rules import render
        render(session)
    elif page_name == PAGE_ALERTS and is_admin:
        from views.alerts import render
        render(session)
    elif page_name == PAGE_MODEL_INTEL and is_admin:
        from views.model_intelligence import render
        render(session)
    else:
        st.error("⛔ Access denied. This page requires admin privileges.")


main()
