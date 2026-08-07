"""
CoCo Control Hub — Prompt Analysis
=====================================
Responsible AI governance dashboard powered by pre-computed overnight analysis.

Performance contract:
  - Governance Dashboard: reads CC_PROMPT_ANALYSIS_DAILY (small aggregate) → loads on page open
  - User Governance Profiles: CC_PROMPT_VIOLATIONS filtered by user → loads on search submit
  - insights feed: aggregates load immediately; full list is button-gated
  - NO expensive queries on page init. Zero raw observability event scans.

Classification runs nightly via SP_CC_CLASSIFY_PROMPTS + CC_CLASSIFY_PROMPTS_TASK.
"""

import json
import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_PROMPT_ANALYSIS_DAILY,
    TABLE_PROMPT_VIOLATIONS,
    TABLE_POLICY_RULES,
    TABLE_USER_COHORT_RESOLVED,
    escape_sql_literal,
    fq_table,
)

_BG  = "#0e1117"
_R   = "#fca5a5"   # rose-300     (muted, was #f87171)
_A   = "#fcd34d"   # amber-300    (muted, was #fbbf24)
_G   = "#6ee7b7"   # emerald-300  (muted, was #4ade80)
_B   = "#7dd3fc"   # sky-300      (muted blue for neutral charts)

_CSS = """<style>
.risk-hi{color:#f87171;font-weight:700} 
.risk-med{color:#fbbf24;font-weight:600}
.risk-lo{color:#4ade80;font-weight:500}
</style>"""


def _sec(title):
    """Section header — consistent muted slate across all pages."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


def _hbar(df, x, y, color=_R, height=220, tooltip=None):
    if df is None or df.empty:
        return None
    enc = {"x": alt.X(f"{x}:Q"), "y": alt.Y(f"{y}:N", sort="-x", title=""),
           "color": alt.value(color)}
    if tooltip:
        enc["tooltip"] = tooltip
    return (alt.Chart(df).mark_bar().encode(**enc)
            .properties(height=height)
            .configure_view(strokeWidth=0).configure(background=_BG))


# ── Data loaders (all fast — read from pre-computed tables) ───────────────────

@st.cache_data(ttl=300, show_spinner=False)
def _load_risk_summary(_session, days: int):
    """Fast: reads CC_PROMPT_ANALYSIS_DAILY only."""
    tbl = fq_table(_session, TABLE_PROMPT_ANALYSIS_DAILY)
    try:
        df = _session.sql(f"""
            SELECT
                ANALYSIS_DATE,
                SUM(HIGH_RISK)    AS HIGH,
                SUM(MEDIUM_RISK)  AS MEDIUM,
                SUM(LOW_RISK)     AS LOW,
                SUM(CLEAN)        AS CLEAN,
                SUM(HIGH_RISK+MEDIUM_RISK+LOW_RISK) AS TOTAL_VIOLATIONS,
                COUNT(DISTINCT USER_NAME) AS USERS
            FROM {tbl}
            WHERE ANALYSIS_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["ANALYSIS_DATE"] = pd.to_datetime(df["ANALYSIS_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_top_violators(_session, days: int):
    """Fast: small aggregation from violations table."""
    tv  = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    tuc = fq_table(_session, TABLE_USER_COHORT_RESOLVED)
    try:
        df = _session.sql(f"""
            SELECT v.USER_NAME,
                   COALESCE(ucr.COHORT_ROLE, 'Uncategorised') AS COHORT,
                   COUNT(*) AS VIOLATIONS,
                   SUM(CASE WHEN v.RISK_LEVEL='HIGH'   THEN 1 ELSE 0 END) AS HIGH,
                   SUM(CASE WHEN v.RISK_LEVEL='MEDIUM' THEN 1 ELSE 0 END) AS MEDIUM,
                   SUM(CASE WHEN v.RISK_LEVEL='LOW'    THEN 1 ELSE 0 END) AS LOW,
                   MAX(v.VIOLATION_DATE)                                    AS LAST_VIOLATION
            FROM {tv} v
            LEFT JOIN {tuc} ucr ON ucr.USER_NAME = v.USER_NAME
            WHERE v.VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1, 2 ORDER BY VIOLATIONS DESC LIMIT 20
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_rule_summary(_session, days: int):
    """Fast: violations grouped by rule — small result."""
    tv  = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    tpr = fq_table(_session, TABLE_POLICY_RULES)
    try:
        df = _session.sql(f"""
            SELECT v.RULE_NAME, v.RISK_LEVEL, v.CATEGORY,
                   COUNT(*) AS VIOLATIONS,
                   COUNT(DISTINCT v.USER_NAME) AS AFFECTED_USERS,
                   MAX(v.VIOLATION_DATE) AS LAST_SEEN
            FROM {tv} v
            WHERE v.VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1, 2, 3 ORDER BY VIOLATIONS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_user_violations(_session, username: str, days: int):
    """Load violation history for a specific user."""
    tv   = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT VIOLATION_DATE, RULE_NAME, RISK_LEVEL, CATEGORY,
                   MATCH_TYPE, PROMPT_PREVIEW, DETECTED_AT,
                   COALESCE(CONTENT_TYPE,'PROMPT') AS CONTENT_TYPE
            FROM {tv}
            WHERE USER_NAME = '{safe}'
              AND VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            ORDER BY DETECTED_AT DESC
            LIMIT 100
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_last_run_time(_session):
    tbl = fq_table(_session, TABLE_PROMPT_ANALYSIS_DAILY)
    try:
        df = _session.sql(f"SELECT MAX(ANALYZED_AT) AS LAST_RUN FROM {tbl}").to_pandas()
        if not df.empty and pd.notna(df.iloc[0, 0]):
            return str(df.iloc[0, 0])[:19]
        return None
    except Exception:
        return None


# ── Main render ────────────────────────────────────────────────────────────────

def render(session):
    st.markdown(_CSS, unsafe_allow_html=True)
    st.header("Prompt Analysis",
              help="Responsible AI governance — insight detection powered by overnight classification.")

    last_run = _load_last_run_time(session)
    if last_run:
        st.caption(f"Last analysis: **{last_run} UTC** · Next run: 2am UTC · "
                   f"Configure rules in Policy Rules page.")
    else:
        st.warning(
            "No analysis data yet. Go to **Policy Rules → Run Analysis Now** to trigger the first run, "
            "or wait for the scheduled task at 2am UTC."
        )

    # ── Lookback ──────────────────────────────────────────────────────────────
    if "pa_days" not in st.session_state:
        st.session_state["pa_days"] = 7

    col_d, col_nav = st.columns([1, 5])
    with col_d:
        days = st.selectbox("Lookback", [7, 14, 30],
                            index=[7,14,30].index(st.session_state["pa_days"]),
                            key="pa_days_sel", label_visibility="collapsed",
                            help="Days of history to analyse. Reads from pre-computed CC_PROMPT_ANALYSIS_DAILY — instant at any scale.")
        if days != st.session_state["pa_days"]:
            st.session_state["pa_days"] = days
    with col_nav:
        section = st.radio("", ["Governance Dashboard", "User Governance Profiles", "Insights Feed"],
                           horizontal=True, key="pa_section", label_visibility="collapsed",
                           help="Governance Dashboard: insight KPIs and trends from nightly analysis. User Governance Profiles: per-user history. Insights Feed: full log with filters.")

    active_days = st.session_state["pa_days"]
    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Governance Dashboard (loads on open, reads pre-computed tables only)
    # ══════════════════════════════════════════════════════════════════════════
    if section == "Governance Dashboard":
        risk_df   = _load_risk_summary(session, active_days)
        rule_df   = _load_rule_summary(session, active_days)
        violators = _load_top_violators(session, active_days)

        if risk_df.empty and rule_df.empty:
            st.info(
                "No prompt insights detected in this period. Either no rules have been triggered, "
                "or analysis hasn't run yet. Use **Policy Rules → Run Analysis Now** to start."
            )
        else:
            # KPI row
            total_v   = int(risk_df["TOTAL_VIOLATIONS"].sum()) if not risk_df.empty else 0
            total_h   = int(risk_df["HIGH"].sum()) if not risk_df.empty else 0
            total_m   = int(risk_df["MEDIUM"].sum()) if not risk_df.empty else 0
            total_l   = int(risk_df["LOW"].sum()) if not risk_df.empty else 0
            ucount    = int(violators["USER_NAME"].nunique()) if not violators.empty else 0

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total Insights", f"{total_v:,}",
                      help=f"Across all active rules in last {active_days} days.")
            k2.metric("🔴 High Severity",  f"{total_h:,}")
            k3.metric("🟡 Medium Severity", f"{total_m:,}")
            k4.metric("🟢 Low Severity",   f"{total_l:,}")
            k5.metric("Users Flagged", f"{ucount:,}")

            st.divider()

            # Trend chart
            if not risk_df.empty:
                _sec("Insight Trend")
                trend = risk_df[["ANALYSIS_DATE","HIGH","MEDIUM","LOW"]].copy()
                trend["ANALYSIS_DATE"] = trend["ANALYSIS_DATE"].astype(str)
                trend_m = trend.melt("ANALYSIS_DATE", var_name="SEVERITY", value_name="COUNT")
                ch = (alt.Chart(trend_m).mark_area(opacity=0.65)
                      .encode(
                          x=alt.X("ANALYSIS_DATE:T", title=""),
                          y=alt.Y("COUNT:Q", title="Insights", stack="zero"),
                          color=alt.Color("SEVERITY:N",
                              scale=alt.Scale(domain=["HIGH","MEDIUM","LOW"],
                                              range=[_R, _A, _G])),
                          tooltip=["ANALYSIS_DATE:T","SEVERITY:N","COUNT:Q"])
                      .properties(height=200)
                      .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

            col_l, col_r = st.columns(2)

            # Rule breakdown
            with col_l:
                if not rule_df.empty:
                    _sec("Insights by Rule")
                    ch2 = _hbar(rule_df.head(10), "VIOLATIONS", "RULE_NAME",
                                height=max(180, len(rule_df.head(10))*36),
                                tooltip=["RULE_NAME:N",
                                         alt.Tooltip("VIOLATIONS:Q", title="Insights"),
                                         "AFFECTED_USERS:Q","RISK_LEVEL:N"])
                    if ch2:
                        st.altair_chart(ch2, use_container_width=True)
                    st.dataframe(rule_df, use_container_width=True, hide_index=True,
                                 column_config={
                                     "VIOLATIONS": st.column_config.NumberColumn("Insights"),
                                     "AFFECTED_USERS": st.column_config.NumberColumn("Users"),
                                     "LAST_SEEN": st.column_config.DateColumn("Last Seen"),
                                 })

            # Top offenders
            with col_r:
                if not violators.empty:
                    _sec("Top Users by Insights")
                    ch3 = _hbar(violators.head(10), "VIOLATIONS", "USER_NAME",
                                color=_A, height=max(180, len(violators.head(10))*36),
                                tooltip=["USER_NAME:N","COHORT:N",
                                         alt.Tooltip("VIOLATIONS:Q", title="Insights"),
                                         "HIGH:Q","MEDIUM:Q","LOW:Q"])
                    if ch3:
                        st.altair_chart(ch3, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — User Governance Profiles
    # ══════════════════════════════════════════════════════════════════════════
    elif section == "User Governance Profiles":
        _sec("Search User Governance Profile")
        with st.form("pa_user_form"):
            col_u, col_btn = st.columns([3, 1])
            with col_u:
                uq = st.text_input("Username", placeholder="e.g. JSMITH",
                                   key="pa_user_inp",
                                   help="Partial match supported.")
            with col_btn:
                st.write("")
                pa_sub = st.form_submit_button("Search", use_container_width=True)

        if "pa_user_committed" not in st.session_state:
            st.session_state["pa_user_committed"] = ""
        if pa_sub:
            st.session_state["pa_user_committed"] = uq.strip().upper()

        if st.session_state["pa_user_committed"]:
            vdf = _load_user_violations(session, st.session_state["pa_user_committed"], active_days)

            if vdf.empty:
                st.info(f"No prompt insights found for '{st.session_state['pa_user_committed']}' in the last {active_days} days. ✓ Clean.")
            else:
                h = int((vdf["RISK_LEVEL"] == "HIGH").sum())
                m = int((vdf["RISK_LEVEL"] == "MEDIUM").sum())
                l = int((vdf["RISK_LEVEL"] == "LOW").sum())
                top_rule = vdf["RULE_NAME"].value_counts().index[0] if len(vdf) else "—"

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Total Insights", len(vdf))
                k2.metric("🔴 High",   h)
                k3.metric("🟡 Medium", m)
                k4.metric("Top Triggered Rule", top_rule)

                st.divider()
                _sec("Insight History")
                st.dataframe(vdf, use_container_width=True, hide_index=True,
                             column_config={
                                 "VIOLATION_DATE": st.column_config.DateColumn("Date"),
                                 "RULE_NAME":      st.column_config.TextColumn("Rule"),
                                 "RISK_LEVEL":     st.column_config.TextColumn("Severity"),
                                 "MATCH_TYPE":     st.column_config.TextColumn("Match"),
                                 "CONTENT_TYPE":   st.column_config.TextColumn("Source"),
                                 "PROMPT_PREVIEW": st.column_config.TextColumn("Content Preview", width="large"),
                                 "DETECTED_AT":    st.column_config.DatetimeColumn("Detected"),
                             })
        else:
            st.caption("Enter a username above to see their insight history.")

        # Also show leaderboard
        st.divider()
        _sec("Users with Prompt Insights")
        top_all = _load_top_violators(session, active_days)
        if not top_all.empty:
            st.dataframe(top_all, use_container_width=True, hide_index=True,
                         column_config={
                             "VIOLATIONS": st.column_config.NumberColumn("Total"),
                             "HIGH":       st.column_config.NumberColumn("High"),
                             "MEDIUM":     st.column_config.NumberColumn("Med"),
                             "LOW":        st.column_config.NumberColumn("Low"),
                             "LAST_VIOLATION": st.column_config.DateColumn("Last"),
                         })

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Insights Feed
    # ══════════════════════════════════════════════════════════════════════════
    elif section == "Insights Feed":
        _sec("Insights by Rule & Day")

        # Aggregates load immediately (small)
        rule_day = _load_rule_summary(session, active_days)
        if rule_day.empty:
            st.info("No insights in this period.")
        else:
            st.dataframe(rule_day, use_container_width=True, hide_index=True,
                         column_config={
                             "RULE_NAME":       st.column_config.TextColumn("Rule", width="medium"),
                             "RISK_LEVEL":      st.column_config.TextColumn("Severity"),
                             "CATEGORY":        st.column_config.TextColumn("Category"),
                             "VIOLATIONS":      st.column_config.NumberColumn("Count"),
                             "AFFECTED_USERS":  st.column_config.NumberColumn("Users"),
                             "LAST_SEEN":       st.column_config.DateColumn("Last Seen"),
                         })

        # Full violations list — button-gated
        st.divider()
        _sec("Full Insights Log")

        feed_key = f"pa_feed_{active_days}"
        if feed_key not in st.session_state:
            st.caption(f"Up to 500 most recent insights in the last {active_days} days.")
            col_f, col_risk, col_match, col_ct, _ = st.columns([1, 1, 1, 1, 1])
            with col_f:
                filter_rule = st.selectbox("Filter by rule", ["All"] + (
                    rule_day["RULE_NAME"].tolist() if not rule_day.empty else []),
                    key="pa_feed_rule",
                    help="Filter insights by a specific policy rule.")
            with col_risk:
                filter_risk = st.selectbox("Filter by risk", ["All","HIGH","MEDIUM","LOW"],
                                           key="pa_feed_risk",
                                           help="HIGH = PII/credentials/exfiltration. MEDIUM = competitors/anomalies. LOW = personal use.")
            with col_match:
                filter_match = st.selectbox("Filter by method", ["All","KEYWORD","REGEX","SEMANTIC"],
                                            key="pa_feed_match",
                                            help="KEYWORD/REGEX = free pattern matching. SEMANTIC = Cortex AI_CLASSIFY.")
            with col_ct:
                filter_ct = st.selectbox("Detected in", ["All","PROMPT","RESPONSE"],
                                         key="pa_feed_ct",
                                         help="PROMPT = insight from user message. RESPONSE = insight from AI response.")
            if st.button("Load Insights", key="btn_load_feed", type="primary",
                         help="Queries CC_PROMPT_VIOLATIONS with current filters. Results capped at 500 rows."):
                tv   = fq_table(session, TABLE_PROMPT_VIOLATIONS)
                where = f"VIOLATION_DATE >= DATEADD('day', -{active_days}, CURRENT_DATE())"
                if filter_rule != "All":
                    where += f" AND RULE_NAME = '{escape_sql_literal(filter_rule)}'"
                if filter_risk != "All":
                    where += f" AND RISK_LEVEL = '{filter_risk}'"
                if filter_match != "All":
                    where += f" AND MATCH_TYPE = '{filter_match}'"
                if filter_ct != "All":
                    where += f" AND COALESCE(CONTENT_TYPE,'PROMPT') = '{filter_ct}'"
                with st.spinner("Loading insights…"):
                    try:
                        fdf = session.sql(f"""
                            SELECT VIOLATION_DATE, USER_NAME, RULE_NAME, RISK_LEVEL,
                                   CATEGORY, MATCH_TYPE, MATCH_SCORE,
                                   COALESCE(CONTENT_TYPE,'PROMPT') AS CONTENT_TYPE,
                                   PROMPT_PREVIEW, DETECTED_AT
                            FROM {tv} WHERE {where}
                            ORDER BY DETECTED_AT DESC LIMIT 500
                        """).to_pandas()
                        fdf.columns = [c.upper() for c in fdf.columns]
                        st.session_state[feed_key] = fdf
                    except Exception as e:
                        st.session_state[feed_key] = str(e)
                st.rerun()
        else:
            fdf = st.session_state[feed_key]
            col_r, _ = st.columns([1, 5])
            with col_r:
                if st.button("↺ Refresh", key="btn_refresh_feed",
                             help="Clear cached results and reload with current filters."):
                    del st.session_state[feed_key]

            if isinstance(fdf, str):
                st.error(f"Error: {fdf}")
            elif fdf.empty:
                st.info("No insights match the selected filters.")
            else:
                st.caption(f"{len(fdf):,} prompt insights")
                st.dataframe(fdf, use_container_width=True, hide_index=True,
                             column_config={
                                 "VIOLATION_DATE": st.column_config.DateColumn("Date"),
                                 "USER_NAME":      st.column_config.TextColumn("User"),
                                 "RULE_NAME":      st.column_config.TextColumn("Rule"),
                                 "RISK_LEVEL":     st.column_config.TextColumn("Severity"),
                                 "CONTENT_TYPE":   st.column_config.TextColumn("Source", help="PROMPT = detected in user message. RESPONSE = detected in AI reply."),
                                 "MATCH_SCORE":    st.column_config.NumberColumn("Score", format="%.2f"),
                                 "PROMPT_PREVIEW": st.column_config.TextColumn("Content Preview", width="large"),
                                 "DETECTED_AT":    st.column_config.DatetimeColumn("Detected"),
                             })
