"""
Cortex Code Credit Manager - Home Page v4
==========================================
Feature tiles (like ai-monitoring-dashboard) then live account stats.
"""

import streamlit as st
import pandas as pd
import altair as alt

from config import (
    APP_NAME, SURFACES, SURFACE_PARAMS,
    get_current_user, user_is_admin, fq_table,
    TABLE_APP_CONFIG, TABLE_ALERT_HISTORY, TABLE_PROMPT_VIOLATIONS, TABLE_POLICY_RULES,
)
from utils import (
    get_daily_trend,
    get_model_breakdown,
    get_top_users,
    get_usage_summary_metrics,
    get_user_param,
    get_user_today_usage,
)


_BG = "#0e1117"


def _sec(title):
    """Consistent section header — muted slate style."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


def _card(title, desc, prereq=None):
    prereq_html = f'<div style="font-size:0.72rem;color:#8b949e;font-style:italic;margin-top:0.4rem;">Requires: {prereq}</div>' if prereq else ''
    return f"""
    <div style="background:#161b22;border-radius:8px;padding:1rem;
                border-left:4px solid #388bfd;margin-bottom:0.6rem;">
        <div style="font-size:0.9rem;font-weight:600;color:#f0f6fc;">{title}</div>
        <div style="font-size:0.8rem;color:#c9d1d9;margin-top:0.3rem;">{desc}</div>
        {prereq_html}
    </div>"""


def render(session):
    username = get_current_user(session)
    is_admin = user_is_admin(session)

    st.markdown(f'<h1 style="font-size:1.6rem;margin-bottom:0.2rem;">{APP_NAME}</h1>', unsafe_allow_html=True)
    st.caption("Govern AI spend. Rebalance automatically. Audit everything.")

    # Setup callout for admins — only shown if app config is sparse (likely first run)
    if is_admin:
        try:
            tbl = fq_table(session, TABLE_APP_CONFIG)
            row = session.sql(f"SELECT COUNT(*) AS n FROM {tbl}").collect()
            config_count = int(row[0]["N"]) if row else 0
        except Exception:
            config_count = 0
        if config_count < 5:
            st.warning("First time here? Head to **Setup** to initialize required objects and seed defaults.")

    st.divider()

    # --- Feature Tiles ---
    st.markdown("### What's inside")

    if is_admin:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(_card("Access Management",
                "Grant CORTEX_USER + COPILOT_USER to users, roles, or by user tag. View role inheritance."), unsafe_allow_html=True)
            st.markdown(_card("Credit Configuration",
                "Set daily limits at account, cohort, or user level. Temporary overrides with auto-revert. Native AI Budgets (Preview) for agent-level hard enforcement."), unsafe_allow_html=True)
            st.markdown(_card("Credit Requests",
                "Self-service with rate limiting & EWMA-based intelligent donor selection."), unsafe_allow_html=True)
            st.markdown(_card("Model Access",
                "Assign models to TIER_1/2/3, map tiers to roles, enforce via Cortex application roles."), unsafe_allow_html=True)
            st.markdown(_card("AI Observability",
                "Account → Cohort → User drill-down. DAU, WoW, Cortex AI Guardrails status, latency, prompt intelligence, surface split (CLI/Snowsight/Desktop), tool call tracking.",
                "CC_USAGE_DAILY_SUMMARY must be populated."), unsafe_allow_html=True)
            st.markdown(_card("Cost Attribution",
                "Per-prompt & per-session credit costs via ACCOUNT_USAGE join. USD/credit rate configurable in Settings.",
                "Loaded on demand — 45min-2hr ACCOUNT_USAGE latency."), unsafe_allow_html=True)
        with col2:
            st.markdown(_card("Prompt Insights 🔬",
                "Responsible AI governance dashboard. Governance dashboard, user governance profiles, insights feed with HIGH/MEDIUM/LOW severity. Classifies both user prompts AND AI responses. Pre-computed nightly.",
                "Run SP_CC_CLASSIFY_PROMPTS or wait for 2am UTC task."), unsafe_allow_html=True)
            st.markdown(_card("Policy Rules 📋",
                "Define keyword, regex, or AI_CLASSIFY (semantic) rules. Apply rules to user prompts, AI responses, or both. Run analysis on demand."), unsafe_allow_html=True)
            st.markdown(_card("Usage Trends",
                "Stacked area charts, heatmap, spike detection, usage recommendations.",
                "CC_USAGE_HOURLY_SUMMARY must be populated."), unsafe_allow_html=True)
            st.markdown(_card("Budget Forecast",
                "Linear regression projections for 7d / 30d / 90d. Per-cohort breakdown.",
                "Minimum 7 days of usage data required."), unsafe_allow_html=True)
            st.markdown(_card("Audit Log",
                "Full audit trail — every grant, limit change, approval, rejection, and rebalance."), unsafe_allow_html=True)
            st.markdown(_card("Setup",
                "In-app wizard — 7-step Account Prerequisites (cross-region, guardrails, AI budgets), then Phases A–E to create all objects.",
                "Streamlit must be owned by ACCOUNTADMIN."), unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(_card("Home",
                "Your current credit limits, today's usage, and 7-day personal trend."), unsafe_allow_html=True)
        with col2:
            st.markdown(_card("Credit Requests",
                "Request additional credits or model access upgrades. Self-service with intelligent rebalancing."), unsafe_allow_html=True)

    st.divider()

    # --- Live Stats (admin) ---
    if is_admin:
        st.markdown("### Account Overview (Last 30 Days)")
        m = get_usage_summary_metrics(session, 30, None)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Credits", f"{m['total_credits']:,.1f}", help="Sum of all credits consumed across surfaces.")
        c2.metric("Active Users", f"{m['active_users']}", help="Distinct users with at least one request.")
        c3.metric("Avg / User", f"{m['avg_per_user']:.1f}", help="Total credits ÷ active users.")
        c4.metric("Total Requests", f"{m['total_requests']:,}", help="Number of LLM API calls.")

        col1, col2 = st.columns([2, 1])
        with col1:
            _sec("Top 10 Users")
            top = get_top_users(session, 30, None, limit=10)
            if not top.empty:
                chart = alt.Chart(top.head(10)).mark_bar().encode(
                    x=alt.X('CREDITS:Q', title='Credits'),
                    y=alt.Y('USER_NAME:N', sort=alt.EncodingSortField(field='CREDITS', order='descending'), title='',
                            axis=alt.Axis(labelLimit=220)),
                ).properties(height=300).configure_view(strokeWidth=0).configure(background='#0e1117')
                st.altair_chart(chart, use_container_width=True)
                st.caption("Credits consumed in last 30 days. Source: CC_USAGE_DAILY_SUMMARY.")
        with col2:
            _sec("Credits by Model")
            mdf = get_model_breakdown(session, 30, None)
            if not mdf.empty:
                mdf = mdf.sort_values("CREDITS", ascending=False)
                chart = alt.Chart(mdf).mark_bar().encode(
                    x=alt.X('CREDITS:Q', title=''),
                    y=alt.Y('MODEL_NAME:N', sort=alt.EncodingSortField(field='CREDITS', order='descending'), title='',
                            axis=alt.Axis(labelLimit=180)),
                ).properties(height=300).configure_view(strokeWidth=0).configure(background='#0e1117')
                st.altair_chart(chart, use_container_width=True)
                st.caption("Uncategorised models not yet assigned to a tier — go to Model Access.")

        _sec("Daily Credit Trend")
        df = get_daily_trend(session, 30, None)
        if not df.empty and "USAGE_DATE" in df.columns:
            df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"])
            chart = alt.Chart(df).mark_area(opacity=0.7).encode(
                x=alt.X('USAGE_DATE:T', title=''),
                y=alt.Y('CREDITS:Q', title='Credits', stack='zero'),
                color=alt.Color('SURFACE:N',
                    scale=alt.Scale(
                        domain=['CLI', 'SNOWSIGHT', 'DESKTOP'],
                        range=['#7dd3fc', '#6ee7b7', '#fcd34d']),
                    legend=alt.Legend(title="")),
            ).properties(height=220).configure_view(strokeWidth=0).configure(background='#0e1117')
            st.altair_chart(chart, use_container_width=True)
            st.caption("Stacked by surface (CLI / Snowsight / Desktop). For hourly breakdown → Usage Trends.")

    st.divider()

    # --- Personal Usage ---
    st.markdown(f"### Your Usage Today — {username}")
    today_usage = get_user_today_usage(session, username)
    cols = st.columns(len(SURFACES) + 1)
    for i, surface in enumerate(SURFACES):
        param = SURFACE_PARAMS[surface]
        try:
            val, level = get_user_param(session, username, param)
        except Exception:
            val, level = None, "N/A"
        limit_display = val if val and val != "-1" else "No limit"
        used = today_usage.get(surface, 0.0)
        with cols[i]:
            st.metric(f"{surface}", f"{used:.1f} cr",
                      help=f"Limit: {limit_display} (source: {level})")
            if val and val != "-1" and float(val) > 0:
                pct = min(used / float(val) * 100, 100)
                st.progress(pct / 100)

    total_used = sum(today_usage.values())
    with cols[-1]:
        st.metric("Total", f"{total_used:.1f} cr",
                  help="Sum of credits used today across all surfaces.")

    for surface in SURFACES:
        param = SURFACE_PARAMS[surface]
        try:
            val, _ = get_user_param(session, username, param)
        except Exception:
            continue
        used = today_usage.get(surface, 0.0)
        if val and val != "-1" and float(val) > 0:
            pct = used / float(val) * 100
            if pct >= 100:
                st.error(f"**{surface} limit reached.** Go to Credit Requests.")
            elif pct >= 70:
                st.warning(f"{surface}: {pct:.0f}% used.")

    with st.expander("How credit management works"):
        st.markdown("""
**Limit hierarchy:** Account → Cohort (role/tag) → User override (highest wins)

**Intelligent rebalancing:** When you hit your limit, the system predicts rest-of-day usage for teammates using 14 days of EWMA trend data. Surplus credits transfer automatically with a 20% safety buffer. Configurable donor strategies: Weighted Random, Highest Surplus, Minimum Donors, Round Robin.

**Daily limits reset at midnight UTC** regardless of your timezone.

**Model tiers:** TIER_1 = Opus (complex tasks), TIER_2 = Sonnet (daily coding), TIER_3 = fast completions.
        """)

    # ── System Health Pulse ─────────────────────────────────────────────────────
    st.divider()
    _sec("System Health")
    st.caption("Live counts — refreshed every 2 minutes.")

    @st.cache_data(ttl=120, show_spinner=False)
    def _health_counts(_session):
        counts = {"alerts_24h": 0, "violations_24h": 0, "active_rules": 0, "guardrails": None}
        try:
            tbl_ah = fq_table(_session, TABLE_ALERT_HISTORY)
            r = _session.sql(f"SELECT COUNT(*) FROM {tbl_ah} WHERE FIRED_AT >= DATEADD('hour',-24,CURRENT_TIMESTAMP())").collect()
            counts["alerts_24h"] = int(r[0][0]) if r else 0
        except Exception:
            pass
        try:
            tbl_pv = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
            r = _session.sql(f"SELECT COUNT(*) FROM {tbl_pv} WHERE VIOLATION_DATE >= CURRENT_DATE()-1").collect()
            counts["violations_24h"] = int(r[0][0]) if r else 0
        except Exception:
            pass
        try:
            tbl_pr = fq_table(_session, TABLE_POLICY_RULES)
            r = _session.sql(f"SELECT COUNT(*) FROM {tbl_pr} WHERE IS_ACTIVE=TRUE").collect()
            counts["active_rules"] = int(r[0][0]) if r else 0
        except Exception:
            pass
        try:
            rows = _session.sql("SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT").collect()
            if rows:
                val = str(rows[0]["value"]) if rows[0]["value"] else ""
                counts["guardrails"] = "enabled" if "enabled: true" in val.lower() else "disabled"
            else:
                counts["guardrails"] = "disabled"
        except Exception:
            counts["guardrails"] = None
        return counts

    hc = _health_counts(session)
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Alerts (24h)", hc["alerts_24h"],
              help="Alert rules that fired in the last 24 hours. Go to Alerts page for details.")
    h2.metric("Prompt Insights (24h)", hc["violations_24h"],
              help="Responsible AI policy prompt insights detected in the last 24 hours. Go to Prompt Insights for details.")
    h3.metric("Active Rules", hc["active_rules"],
              help="Policy rules currently enabled for responsible AI classification.")
    _gr = hc["guardrails"]
    _gr_label = "🛡️ Enabled" if _gr == "enabled" else ("⚠️ Not Enabled" if _gr == "disabled" else "—")
    h4.metric("AI Guardrails", _gr_label,
              help="Cortex AI Guardrails (Snowflake Horizon) — runtime protection against prompt injection and jailbreak attacks. Enable via Setup → Account Prerequisites.")
