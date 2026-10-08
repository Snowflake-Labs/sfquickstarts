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
    CHARGEBACK_PAGES,
    COMMON_TIMEZONES,
    DEFAULT_TZ,
    GLOBAL_CSS,
    PAGE_ACCESS_MGMT,
    PAGE_ALERTS,
    PAGE_ATTRIBUTION,
    PAGE_AUDIT_LOG,
    PAGE_CHARGEBACK,
    PAGE_COST_ATTRIBUTION,
    PAGE_CREDIT_CONFIG,
    PAGE_CREDIT_REQUESTS,
    PAGE_HOME,
    PAGE_MODEL_ACCESS,
    PAGE_MODEL_BAKEOFF,
    PAGE_MODEL_INTEL,
    PAGE_NATIVE_QUOTAS,
    PAGE_OBSERVABILITY,
    PAGE_POLICY_RULES,
    PAGE_PROMPT_ANALYSIS,
    PAGE_USER_INTEL,
    PAGE_SETTINGS,
    PAGE_SETUP,
    PAGE_USAGE_TRENDS,
    PAGE_WAREHOUSE_ACTIVITY,
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
            PAGE_CHARGEBACK:       "🧾",
            PAGE_WAREHOUSE_ACTIVITY: "🏭",
            PAGE_ATTRIBUTION:      "🎯",
            PAGE_NATIVE_QUOTAS:    "⚡",
            PAGE_MODEL_BAKEOFF:    "⚖️",
        }

        # Grouped navigation: a "Chargeback" section is rendered under its own
        # heading. Each section is its own radio; selecting in one
        # clears the others (index=None) so exactly one page is active across all.
        if is_admin:
            sections = [
                ("", [p for p in ALL_PAGES if p not in CHARGEBACK_PAGES]),
                ("Chargeback", [p for p in CHARGEBACK_PAGES]),
            ]
        else:
            sections = [("", [p for p in USER_PAGES])]

        if "cc_page" not in st.session_state or st.session_state["cc_page"] not in available_pages:
            st.session_state["cc_page"] = available_pages[0]

        def _pick(section_key):
            val = st.session_state.get(f"cc_nav_{section_key}")
            if val:
                st.session_state["cc_page"] = val.split(" ", 1)[1]

        for si, (label, pages) in enumerate(sections):
            visible = [p for p in pages if p in available_pages]
            if not visible:
                continue
            if label:
                st.markdown(
                    f'<div style="margin:0.5rem 0 0.15rem 0.15rem;font-size:0.7rem;'
                    f'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'
                    f'color:#3b82f6">{label}</div>', unsafe_allow_html=True)
            opts = [f"{page_icons.get(p, '•')} {p}" for p in visible]
            sel = st.session_state["cc_page"]
            key = f"cc_nav_{si}"
            # Sync this radio's stored value to the global selection every run.
            # Streamlit ignores index= once a keyed widget already holds a value in
            # session_state, so a stale value would keep a second section's dot lit.
            # Setting session_state[key] directly (the active option, or None to
            # deselect) forces exactly one highlighted dot across all sections.
            st.session_state[key] = (
                f"{page_icons.get(sel, '•')} {sel}" if sel in visible else None
            )
            st.radio(label or "Navigation", opts,
                     label_visibility="collapsed", key=key,
                     on_change=_pick, args=(si,))

        page_name = st.session_state["cc_page"]

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
        from app_pages.home import render
        render(session)
    elif page_name == PAGE_ACCESS_MGMT and is_admin:
        from app_pages.access_management import render
        render(session)
    elif page_name == PAGE_CREDIT_CONFIG and is_admin:
        from app_pages.credit_config import render
        render(session)
    elif page_name == PAGE_USAGE_TRENDS and is_admin:
        from app_pages.usage_trends import render
        render(session)
    elif page_name == PAGE_MODEL_ACCESS and is_admin:
        from app_pages.model_access import render
        render(session)
    elif page_name == PAGE_CREDIT_REQUESTS:
        from app_pages.credit_requests import render
        render(session)
    elif page_name == PAGE_SETTINGS and is_admin:
        from app_pages.settings import render
        render(session)
    elif page_name == PAGE_AUDIT_LOG and is_admin:
        from app_pages.audit_logs import render
        render(session)
    elif page_name == PAGE_SETUP and is_admin:
        from app_pages.setup import render
        render(session)
    elif page_name == PAGE_OBSERVABILITY and is_admin:
        from app_pages.observability import render
        render(session)
    elif page_name == PAGE_COST_ATTRIBUTION and is_admin:
        from app_pages.cost_attribution import render
        render(session)
    elif page_name == PAGE_PROMPT_ANALYSIS and is_admin:
        from app_pages.prompt_analysis import render
        render(session)
    elif page_name == PAGE_USER_INTEL and is_admin:
        from app_pages.user_intelligence import render
        render(session)
    elif page_name == PAGE_POLICY_RULES and is_admin:
        from app_pages.policy_rules import render
        render(session)
    elif page_name == PAGE_ALERTS and is_admin:
        from app_pages.alerts import render
        render(session)
    elif page_name == PAGE_MODEL_INTEL and is_admin:
        from app_pages.model_intelligence import render
        render(session)
    elif page_name == PAGE_CHARGEBACK and is_admin:
        from app_pages.chargeback import render
        render(session)
    elif page_name == PAGE_WAREHOUSE_ACTIVITY and is_admin:
        from app_pages.warehouse_activity import render
        render(session)
    elif page_name == PAGE_ATTRIBUTION and is_admin:
        from app_pages.attribution import render
        render(session)
    elif page_name == PAGE_MODEL_BAKEOFF and is_admin:
        from app_pages.model_bakeoff import render
        render(session)
    elif page_name == PAGE_NATIVE_QUOTAS and is_admin:
        from app_pages.user_quotas import render
        render(session)
    else:
        st.error("⛔ Access denied. This page requires admin privileges.")


main()
