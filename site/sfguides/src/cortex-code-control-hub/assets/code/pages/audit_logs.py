"""
Cortex Code Credit Manager - Audit Log (Admin)
================================================
Read-only viewer of CC_AUDIT_LOG with filters and export.
"""

import streamlit as st
import pandas as pd

from config import AUDIT_PREVIEW_LIMIT, DATE_PRESETS
from utils import get_audit_logs, get_session


def render(session):
    st.header("Audit Log", help="Immutable record of every admin action: grants, limit changes, approvals, rejections, and rebalances.")

    col_period, col_action, col_limit = st.columns([2, 2, 1])

    with col_period:
        period_label = st.radio("Period", list(DATE_PRESETS.keys()), horizontal=True,
                                index=1, key="audit_period",
                                help="Filter audit records to this time window.")
    with col_action:
        action_filter = st.selectbox(
            "Action Type",
            ["All", "GRANT_ACCESS", "REVOKE_ACCESS", "SET_ACCOUNT_LIMIT",
             "SET_COHORT_LIMIT", "SET_USER_OVERRIDE", "REMOVE_USER_OVERRIDE",
             "APPROVE_REQUEST", "REJECT_REQUEST", "REBALANCE_REDUCE",
             "REBALANCE_INCREASE", "UPDATE_SETTINGS"],
            key="audit_action",
            help="Filter to a specific operation. 'All' shows every action taken by any admin."
        )
    with col_limit:
        row_limit = st.number_input("Max rows", min_value=10, max_value=500,
                                    value=AUDIT_PREVIEW_LIMIT, step=10, key="audit_limit",
                                    help="Maximum records to display. Increase for deeper history searches (up to 500).")

    days = DATE_PRESETS[period_label]
    action = None if action_filter == "All" else action_filter

    df = get_audit_logs(session, days=days, action_type=action, limit=row_limit)

    if df.empty:
        st.info("No audit records for this period.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"Showing {len(df)} records")

    csv = df.to_csv(index=False)
    st.download_button("Download CSV", csv, "cc_audit_log.csv", "text/csv", key="audit_download",
                       help="Export the current filtered view as a CSV file for offline analysis or compliance records.")
