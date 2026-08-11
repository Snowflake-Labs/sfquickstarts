"""
CoCo Control Hub — Alerts
==========================
Configure alert rules, view alert history, manage notification settings,
and monitor Snowflake ALERT health (batch + real-time).
"""

import json
import altair as alt
import pandas as pd
import streamlit as st

from audit import log_activity
from config import (
    TABLE_ALERT_CONFIG,
    TABLE_ALERT_HISTORY,
    SP_CHECK_ALERTS,
    escape_sql_literal,
    fq_table,
    fq_sp,
    get_current_user,
)
from utils import get_app_setting, get_session, set_app_setting

_BG = "#0e1117"
_R  = "#fca5a5"
_A  = "#fcd34d"
_G  = "#6ee7b7"
_P  = "#7dd3fc"

_ALERT_TYPES = [
    "VIOLATION_SPIKE",
    "HIGH_RISK_VIOLATION",
    "CREDIT_SPIKE",
    "NEW_UNCAT_MODEL",
]
_ALERT_TYPE_LABELS = {
    "VIOLATION_SPIKE":     "Insight Spike — total insights exceed threshold in window",
    "HIGH_RISK_VIOLATION": "High Risk Insight — HIGH-severity insights exceed threshold",
    "CREDIT_SPIKE":        "Credit Spike — today's usage exceeds X% above 7-day average",
    "NEW_UNCAT_MODEL":     "New Uncategorised Model — model appears in usage without a tier",
}


def _sec(title):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


@st.cache_data(ttl=60, show_spinner=False)
def _load_alert_config(_session):
    tbl = fq_table(_session, TABLE_ALERT_CONFIG)
    try:
        df = _session.sql(f"""
            SELECT ALERT_ID, RULE_NAME, ALERT_TYPE, THRESHOLD, WINDOW_MINUTES,
                   IS_ENABLED, CREATED_BY, CREATED_AT
            FROM {tbl} ORDER BY CREATED_AT DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=30, show_spinner=False)
def _load_alert_history(_session, days: int):
    tbl = fq_table(_session, TABLE_ALERT_HISTORY)
    try:
        df = _session.sql(f"""
            SELECT HISTORY_ID, ALERT_NAME, ALERT_TYPE, MESSAGE, MODE, FIRED_AT
            FROM {tbl}
            WHERE FIRED_AT >= DATEADD('day', -{days}, CURRENT_TIMESTAMP())
            ORDER BY FIRED_AT DESC
            LIMIT 500
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["FIRED_AT"] = pd.to_datetime(df["FIRED_AT"])
        return df
    except Exception:
        return pd.DataFrame()


def render(session):
    st.header("Alerts",
              help="Configure alert rules, manage notification settings, and view alert history.")
    st.caption("Batch alerts check every 5 minutes. Real-time alerts fire within 1 minute of a high-severity prompt insight.")

    tab_rules, tab_history, tab_config, tab_health = st.tabs([
        "Alert Rules", "Alert History", "Notification Config", "Alert Health"
    ])

    actor = get_current_user(session)

    # ── Alert Rules ────────────────────────────────────────────────────────────
    with tab_rules:
        rules = _load_alert_config(session)
        tbl = fq_table(session, TABLE_ALERT_CONFIG)

        k1, k2, k3 = st.columns(3)
        total = len(rules) if not rules.empty else 0
        active = int(rules["IS_ENABLED"].sum()) if not rules.empty else 0
        k1.metric("Total Rules", total, help="Total configured alert rules.")
        k2.metric("Active", active, help="Rules currently enabled.")
        k3.metric("Inactive", total - active, help="Rules that are paused.")

        st.divider()

        if rules.empty:
            st.info("No alert rules configured. Create your first rule below.")
        else:
            for _, row in rules.iterrows():
                with st.container(border=True):
                    col_info, col_actions = st.columns([4, 2])
                    with col_info:
                        enabled_badge = "🟢" if row["IS_ENABLED"] else "🔴"
                        st.markdown(
                            f"**{enabled_badge} {row['RULE_NAME']}** "
                            f"<span style='font-size:0.7rem;color:#6b7280;margin-left:0.5rem'>"
                            f"{row['ALERT_TYPE']} · Threshold: {int(row['THRESHOLD'])} · "
                            f"Window: {int(row['WINDOW_MINUTES'])} min</span>",
                            unsafe_allow_html=True
                        )
                        st.caption(_ALERT_TYPE_LABELS.get(str(row["ALERT_TYPE"]), ""))
                    with col_actions:
                        a1, a2 = st.columns(2)
                        enabled = bool(row["IS_ENABLED"])
                        if a1.button("Pause" if enabled else "Resume",
                                     key=f"tog_alert_{row['ALERT_ID']}",
                                     help="Pause/resume this alert rule"):
                            try:
                                session.sql(f"UPDATE {tbl} SET IS_ENABLED = {not enabled} WHERE ALERT_ID = {int(row['ALERT_ID'])}").collect()
                                _load_alert_config.clear()
                                log_activity(session, "TOGGLE_ALERT_RULE",
                                             details={"rule": row["RULE_NAME"], "enabled": not enabled})
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                        if a2.button("🗑", key=f"del_alert_{row['ALERT_ID']}",
                                     help="Delete this alert rule"):
                            if st.session_state.get(f"confirm_del_alert_{row['ALERT_ID']}"):
                                try:
                                    session.sql(f"DELETE FROM {tbl} WHERE ALERT_ID = {int(row['ALERT_ID'])}").collect()
                                    _load_alert_config.clear()
                                    log_activity(session, "DELETE_ALERT_RULE",
                                                 details={"rule": row["RULE_NAME"]})
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))
                            else:
                                st.session_state[f"confirm_del_alert_{row['ALERT_ID']}"] = True
                                st.warning("Click 🗑 again to confirm deletion.")

        st.divider()
        _sec("Create New Alert Rule")
        with st.form("create_alert_form"):
            name = st.text_input("Rule Name *", placeholder="e.g. High Severity Spike",
                                 help="Descriptive name for this alert rule.")
            alert_type = st.selectbox("Alert Type", _ALERT_TYPES,
                                      format_func=lambda x: x,
                                      help="\n".join([f"**{k}**: {v}" for k, v in _ALERT_TYPE_LABELS.items()]))
            col1, col2 = st.columns(2)
            with col1:
                threshold = st.number_input(
                    "Threshold", min_value=1, max_value=10000, value=5, step=1,
                    help="VIOLATION_SPIKE/HIGH_RISK: number of violations. CREDIT_SPIKE: % above 7-day average. NEW_UNCAT_MODEL: number of new models."
                )
            with col2:
                window = st.number_input(
                    "Window (minutes)", min_value=5, max_value=1440, value=60, step=5,
                    help="Look-back window in minutes. Use 1440 for daily checks (e.g. credit spike, new model)."
                )
            submitted = st.form_submit_button("Create Alert Rule", type="primary")

        if submitted:
            if not name.strip():
                st.error("Rule Name is required.")
            else:
                safe_name = escape_sql_literal(name.strip())
                safe_actor = escape_sql_literal(actor)
                try:
                    session.sql(f"""
                        INSERT INTO {tbl} (RULE_NAME, ALERT_TYPE, THRESHOLD, WINDOW_MINUTES, CREATED_BY)
                        VALUES ('{safe_name}', '{alert_type}', {threshold}, {window}, '{safe_actor}')
                    """).collect()
                    _load_alert_config.clear()
                    log_activity(session, "CREATE_ALERT_RULE",
                                 details={"name": name, "type": alert_type, "threshold": threshold})
                    st.success(f"✓ Alert rule '{name}' created.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    # ── Alert History ──────────────────────────────────────────────────────────
    with tab_history:
        days = st.selectbox("Lookback", [1, 7, 14, 30], index=1,
                            key="alert_hist_days",
                            help="Days of alert history to show.")
        hist = _load_alert_history(session, days)

        if hist.empty:
            st.info(f"No alerts fired in the last {days} day(s). Thresholds not yet breached, or alerts not configured.")
        else:
            k1, k2, k3 = st.columns(3)
            k1.metric("Total Fired", len(hist), help="Number of alert events in this period.")
            k2.metric("Batch", int((hist["MODE"] == "BATCH").sum()),
                      help="Alerts fired by the 5-minute batch check.")
            k3.metric("Real-time", int((hist["MODE"] == "REALTIME").sum()),
                      help="Alerts fired within 1 minute of a high-severity prompt insight (stream-based).")

            _sec("Timeline")
            daily = (hist.groupby([hist["FIRED_AT"].dt.date, "ALERT_TYPE"])
                         .size().reset_index(name="FIRES"))
            daily.columns = ["DATE", "ALERT_TYPE", "FIRES"]
            daily["DATE"] = daily["DATE"].astype(str)
            if not daily.empty:
                ch = (alt.Chart(daily).mark_bar()
                      .encode(
                          x=alt.X("DATE:T", title=""),
                          y=alt.Y("FIRES:Q", title="Alerts Fired"),
                          color=alt.Color("ALERT_TYPE:N"),
                          tooltip=["DATE:T", "ALERT_TYPE:N", "FIRES:Q"])
                      .properties(height=180)
                      .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

            _sec("Full History")
            st.dataframe(hist, use_container_width=True, hide_index=True,
                         column_config={
                             "HISTORY_ID":  st.column_config.NumberColumn("ID"),
                             "ALERT_NAME":  st.column_config.TextColumn("Alert"),
                             "ALERT_TYPE":  st.column_config.TextColumn("Type"),
                             "MESSAGE":     st.column_config.TextColumn("Message", width="large"),
                             "MODE":        st.column_config.TextColumn("Mode"),
                             "FIRED_AT":    st.column_config.DatetimeColumn("Fired At"),
                         })

    # ── Notification Config ────────────────────────────────────────────────────
    with tab_config:
        _sec("Email Notification")
        st.caption(
            "Alerts are sent via Snowflake's `SYSTEM$SEND_EMAIL()` using the `CC_EMAIL_INTEGRATION` "
            "notification integration. **Important:** Snowflake requires every recipient address to be "
            "explicitly listed in the integration's `ALLOWED_RECIPIENTS` before emails can be delivered. "
            "Saving here will attempt to update that list automatically."
        )

        current_email = get_app_setting(session, "ALERT_EMAIL_RECIPIENTS", "")
        current_notif = get_app_setting(session, "NOTIFICATION_INTEGRATION", "CC_EMAIL_INTEGRATION")

        with st.form("notif_config_form"):
            email_val = st.text_input(
                "Alert recipients (comma-separated)", value=current_email,
                placeholder="admin@company.com, oncall@company.com",
                help="All alert emails go to these addresses. Leave blank to disable email delivery."
            )
            notif_val = st.text_input(
                "Notification Integration name", value=current_notif,
                placeholder="CC_EMAIL_INTEGRATION",
                help="Name of the Snowflake NOTIFICATION INTEGRATION created during setup."
            )
            col_save, col_test = st.columns(2)
            with col_save:
                save_notif = st.form_submit_button("Save", type="primary")
            with col_test:
                test_notif = st.form_submit_button("Send Test Email",
                                                   help="Sends a real test email to confirm the integration is working.")

        if save_notif:
            ok1 = set_app_setting(session, "ALERT_EMAIL_RECIPIENTS", email_val.strip(), actor)
            ok2 = set_app_setting(session, "NOTIFICATION_INTEGRATION", notif_val.strip() or "CC_EMAIL_INTEGRATION", actor)
            if ok1 and ok2:
                log_activity(session, "UPDATE_ALERT_CONFIG",
                             details={"email_recipients": email_val, "integration": notif_val})
                # Also try to update ALLOWED_RECIPIENTS on the integration
                if email_val.strip():
                    recipients = [e.strip() for e in email_val.strip().split(",") if e.strip()]
                    allowed_list = ", ".join(f"'{r}'" for r in recipients)
                    integration_name = notif_val.strip() or "CC_EMAIL_INTEGRATION"
                    try:
                        session.sql(f"""
                            ALTER NOTIFICATION INTEGRATION {integration_name}
                            SET ALLOWED_RECIPIENTS = ({allowed_list})
                        """).collect()
                        st.success(f"✓ Saved. ALLOWED_RECIPIENTS updated on `{integration_name}` — emails will be delivered to: {', '.join(recipients)}")
                    except Exception as alter_err:
                        st.warning(f"Settings saved, but could not update `ALLOWED_RECIPIENTS` automatically: `{alter_err}`")
                        st.markdown("**Run this as ACCOUNTADMIN to complete the setup:**")
                        st.code(
                            f"ALTER NOTIFICATION INTEGRATION {integration_name}\n"
                            f"SET ALLOWED_RECIPIENTS = ({allowed_list});",
                            language="sql"
                        )
                else:
                    st.success("✓ Notification settings saved.")
            else:
                st.error("Failed to save one or more settings.")

        if test_notif:
            recipients_to_test = email_val.strip() or current_email
            integration_to_test = notif_val.strip() or current_notif or "CC_EMAIL_INTEGRATION"
            if not recipients_to_test:
                st.warning("Enter a recipient email address first.")
            else:
                with st.spinner(f"Sending test email to {recipients_to_test}…"):
                    try:
                        html_body = (
                            '<!DOCTYPE html><html><body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif">'
                            '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                            '<td align="center" style="padding:32px 16px">'
                            '<table width="560" cellpadding="0" cellspacing="0" '
                            'style="background:#ffffff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.1)">'
                            '<tr><td style="background:#0f172a;padding:22px 28px;border-radius:8px 8px 0 0">'
                            '<span style="color:#7dd3fc;font-size:18px;font-weight:700">CoCo Control Hub</span>'
                            '<span style="color:#475569;font-size:12px;margin-left:10px">Test Email</span>'
                            '</td></tr>'
                            '<tr><td style="padding:22px 28px 8px">'
                            '<span style="background:#f0fdf4;color:#16a34a;padding:4px 14px;border-radius:20px;'
                            'font-size:11px;font-weight:700;letter-spacing:0.05em">EMAIL DELIVERY CONFIRMED</span>'
                            '</td></tr>'
                            '<tr><td style="padding:8px 28px 4px">'
                            '<h2 style="margin:0;color:#111827;font-size:18px;font-weight:600">Test Notification</h2>'
                            '</td></tr>'
                            '<tr><td style="padding:12px 28px 20px">'
                            '<div style="background:#f8fafc;border-left:4px solid #6ee7b7;'
                            'padding:14px 16px;border-radius:0 6px 6px 0">'
                            '<p style="margin:0;color:#374151;font-size:14px;line-height:1.6">'
                            'Email notifications are working correctly. Real alerts will be delivered '
                            'here when insight thresholds are breached.'
                            '</p></div></td></tr>'
                            '<tr><td style="background:#f8fafc;padding:14px 28px;border-top:1px solid #e2e8f0;'
                            'border-radius:0 0 8px 8px">'
                            '<p style="margin:0;color:#94a3b8;font-size:11px">'
                            'Sent by <strong style="color:#64748b">CoCo Control Hub</strong> &nbsp;&middot;&nbsp; '
                            'Manage alerts at <em>Alerts &rarr; Notification Config</em>'
                            '</p></td></tr>'
                            '</table></td></tr></table>'
                            '</body></html>'
                        )
                        html_sql = html_body.replace("'", "''")
                        session.sql(f"""
                            CALL SYSTEM$SEND_EMAIL(
                                '{integration_to_test}',
                                '{recipients_to_test}',
                                'CoCo Hub — Test Email',
                                '{html_sql}',
                                'text/html'
                            )
                        """).collect()
                        st.success(f"✓ Test email sent to {recipients_to_test}. Check your inbox.")
                    except Exception as e:
                        err = str(e)
                        st.error(f"Failed to send test email: {err}")
                        if "ALLOWED_RECIPIENTS" in err or "not authorized" in err.lower():
                            st.markdown("**The integration's `ALLOWED_RECIPIENTS` may not include your address. Run as ACCOUNTADMIN:**")
                            recipients = [r.strip() for r in recipients_to_test.split(",") if r.strip()]
                            allowed_list = ", ".join(f"'{r}'" for r in recipients)
                            st.code(
                                f"ALTER NOTIFICATION INTEGRATION {integration_to_test}\n"
                                f"SET ALLOWED_RECIPIENTS = ({allowed_list});",
                                language="sql"
                            )

    # ── Alert Health ───────────────────────────────────────────────────────────
    with tab_health:
        _sec("Snowflake Alert Status")
        st.caption("Shows the status of the Snowflake ALERT scheduler objects. "
                   "STARTED = scheduler is running (fires when rules trigger). "
                   "If all your rules are disabled in Alert Rules, the scheduler runs but nothing fires — that is intentional.")
        try:
            from config import get_app_database, get_app_schema
            _ah_db  = get_app_database(session)
            _ah_sch = get_app_schema(session)
            # Scoped to schema — IN ACCOUNT is very slow on large enterprise accounts
            alert_rows = session.sql(f"SHOW ALERTS LIKE 'CC_%' IN SCHEMA {_ah_db}.{_ah_sch}").collect()
            if alert_rows:
                def _rget(row, key, default=""):
                    try: return row[key]
                    except Exception: return default

                rows_data = [{"NAME": str(_rget(r,"name")), "STATE": str(_rget(r,"state")),
                              "SCHEMA": str(_rget(r,"schema_name")), "DB": str(_rget(r,"database_name")),
                              "SCHEDULE": str(_rget(r,"schedule"))}
                             for r in alert_rows]
                import pandas as _pd
                st.dataframe(_pd.DataFrame(rows_data), use_container_width=True, hide_index=True)

                # Check if any app-level rules are enabled
                try:
                    tbl_ac = fq_table(session, TABLE_ALERT_CONFIG)
                    enabled_count = session.sql(f"SELECT COUNT(*) FROM {tbl_ac} WHERE IS_ENABLED = TRUE").collect()[0][0]
                    all_rules_disabled = (int(enabled_count or 0) == 0)
                except Exception:
                    all_rules_disabled = False

                for r in alert_rows:
                    name  = str(_rget(r,"name"))
                    state = str(_rget(r,"state")).upper()
                    db    = str(_rget(r,"database_name"))
                    sch   = str(_rget(r,"schema_name"))
                    if state in ("SUSPENDED", "DISABLED"):
                        st.warning(f"⚠ Alert `{name}` ({db}.{sch}) is SUSPENDED — scheduler is paused. "
                                   f"Resume with: `ALTER ALERT {db}.{sch}.{name} RESUME;`")
                    elif all_rules_disabled:
                        st.info(f"ℹ️ Alert `{name}` ({db}.{sch}) scheduler is STARTED, but all rules are disabled in Alert Rules — no alerts will fire. This is intentional if you paused alerting.")
                    else:
                        st.success(f"✓ Alert `{name}` ({db}.{sch}) is active ({state}).")
            else:
                st.info("No CC_* alerts found in this account. Run Setup to create them.")
        except Exception as e:
            st.error(f"Could not query alerts: {e}")

        st.divider()
        _sec("Policy Insight Stream Status")
        st.caption("CC_VIOLATION_STREAM powers real-time detection. Offset should advance as violations arrive.")
        try:
            from config import get_app_database, get_app_schema
            _s_db  = get_app_database(session)
            _s_sch = get_app_schema(session)
            stream_rows = session.sql(f"SHOW STREAMS LIKE 'CC_VIOLATION_STREAM' IN SCHEMA {_s_db}.{_s_sch}").collect()
            if stream_rows:
                def _rget2(row, key, default=""):
                    try: return row[key]
                    except Exception: return default

                rows_data = [{"NAME": str(_rget2(r,"name")), "DB": str(_rget2(r,"database_name")),
                              "SCHEMA": str(_rget2(r,"schema_name")),
                              "STALE": str(_rget2(r,"stale")),
                              "MODE": str(_rget2(r,"mode"))}
                             for r in stream_rows]
                import pandas as _pd2
                st.dataframe(_pd2.DataFrame(rows_data), use_container_width=True, hide_index=True)
                for r in stream_rows:
                    stale = str(_rget2(r,"stale","false")).lower()
                    db    = str(_rget2(r,"database_name"))
                    sch   = str(_rget2(r,"schema_name"))
                    if stale == "true":
                        st.warning("⚠ CC_VIOLATION_STREAM is STALE — stream offset may need to be reset.")
                    else:
                        st.success(f"✓ CC_VIOLATION_STREAM is active in `{db}.{sch}`.")
            else:
                st.info("Stream CC_VIOLATION_STREAM not found. Run Setup to create it.")
        except Exception as e:
            st.error(f"Could not query streams: {e}")
