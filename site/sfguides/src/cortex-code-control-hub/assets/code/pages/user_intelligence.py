"""
CoCo Control Hub — User Intelligence
=====================================
Complete per-user profile: credit usage, LLM behaviour, token economics,
responsible AI assessment (insights, governance score), quality scores, and
full prompt search. Enterprise compliance + AI governance in one view.
"""

import json
import re

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    SURFACES, SURFACE_PARAMS,
    TABLE_PROMPT_EVENTS, TABLE_PROMPT_VIOLATIONS, TABLE_RESPONSE_QUALITY,
    TABLE_USAGE_DAILY, TABLE_CREDIT_CONFIG,
    escape_sql_literal, fq_table, get_current_user,
)
from utils import get_app_setting, get_session

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_A  = "#fcd34d"
_R  = "#fca5a5"
_S  = "#94a3b8"

_RISK_COLORS = {"HIGH": _R, "MEDIUM": _A, "LOW": _G}


def _sec(title):
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


def _risk_badge(score: float) -> str:
    if score >= 0.6:    return "🔴 High Severity"
    if score >= 0.25:   return "🟡 Monitor"
    return "✅ Clean"


# ── Data loaders ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def _search_users(_session, query: str):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe_q = escape_sql_literal(query.strip().upper())
    try:
        df = _session.sql(f"""
            SELECT DISTINCT USER_NAME
            FROM {tbl}
            WHERE UPPER(USER_NAME) LIKE '%{safe_q}%'
              AND EVENT_DATE >= DATEADD('day', -180, CURRENT_DATE())
            ORDER BY USER_NAME LIMIT 50
        """).to_pandas()
        return df["USER_NAME"].tolist() if not df.empty else []
    except Exception:
        return []


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_summary(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT
                MIN(EVENT_DATE)                            AS FIRST_SEEN,
                MAX(EVENT_DATE)                            AS LAST_SEEN,
                COUNT(*)                                   AS TOTAL_PROMPTS,
                COUNT(DISTINCT DATE_TRUNC('day',EVENT_TS)) AS ACTIVE_DAYS,
                COUNT(DISTINCT SESSION_ID)                 AS SESSIONS,
                ROUND(AVG(LATENCY_MS)/1000.0, 2)           AS AVG_LATENCY_S,
                ROUND(AVG(CASE WHEN STATUS='SUCCESS' THEN 1.0 ELSE 0.0 END)*100,1) AS SUCCESS_RATE,
                SUM(TOTAL_TOKENS)                          AS TOTAL_TOKENS,
                SUM(INPUT_TOKENS)                          AS INPUT_TOKENS,
                SUM(OUTPUT_TOKENS)                         AS OUTPUT_TOKENS,
                SUM(CACHE_READ_TOKENS)                     AS CACHE_READ,
                SUM(CACHE_WRITE_TOKENS)                    AS CACHE_WRITE,
                ROUND(AVG(STEP_NUMBER), 1)                 AS AVG_STEPS,
                SUM(CASE WHEN PRIVATE_MODE THEN 1 ELSE 0 END) AS PRIVATE_COUNT,
                MODE(MODEL)                                AS TOP_MODEL
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
              AND EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_credits(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT USAGE_DATE, SURFACE, SUM(TOTAL_CREDITS) AS CREDITS
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
              AND USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1, 2 ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_models(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT MODEL,
                   COUNT(*)                     AS PROMPTS,
                   SUM(TOTAL_TOKENS)            AS TOKENS,
                   SUM(CACHE_READ_TOKENS)       AS CACHE_READ,
                   SUM(INPUT_TOKENS)            AS INPUT_TOKENS,
                   ROUND(AVG(LATENCY_MS)/1000.0,2) AS AVG_LAT_S
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
              AND EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND MODEL IS NOT NULL
            GROUP BY 1 ORDER BY PROMPTS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_violations(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_VIOLATIONS)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT RULE_NAME, RISK_LEVEL, CATEGORY, CONTENT_TYPE,
                   COUNT(*) AS HITS,
                   MAX(VIOLATION_DATE) AS LAST_SEEN,
                   ARRAY_AGG(DISTINCT PROMPT_PREVIEW) AS PREVIEWS
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
              AND VIOLATION_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1,2,3,4 ORDER BY RISK_LEVEL, HITS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_quality(_session, username: str):
    tbl = fq_table(_session, TABLE_RESPONSE_QUALITY)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT
                ROUND(AVG(ANSWER_RELEVANCE_SCORE), 3) AS AVG_RELEVANCE,
                ROUND(AVG(GROUNDEDNESS_SCORE), 3)     AS AVG_GROUNDEDNESS,
                ROUND(AVG(COHERENCE_SCORE), 3)        AS AVG_COHERENCE,
                ROUND(AVG(SAFETY_SCORE), 3)           AS AVG_SAFETY,
                COUNT(*)                              AS EVALUATED,
                MAX(EVALUATED_AT)                     AS LAST_EVAL
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_user_daily(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT EVENT_DATE, COUNT(*) AS PROMPTS,
                   SUM(TOTAL_TOKENS) AS TOKENS,
                   ROUND(AVG(LATENCY_MS)/1000.0,2) AS AVG_LAT_S
            FROM {tbl}
            WHERE USER_NAME = '{safe}'
              AND EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120, show_spinner=False)
def _load_prompt_search(_session, username: str, days: int, keyword: str):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe_u = escape_sql_literal(username)
    safe_k = escape_sql_literal(keyword.strip())
    try:
        df = _session.sql(f"""
            SELECT EVENT_TS, MODEL, PROMPT, RESPONSE, STATUS,
                   LATENCY_MS, TOTAL_TOKENS, PRIVATE_MODE, STEP_NUMBER
            FROM {tbl}
            WHERE USER_NAME = '{safe_u}'
              AND EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND (PROMPT ILIKE '%{safe_k}%' OR RESPONSE ILIKE '%{safe_k}%')
            ORDER BY EVENT_TS DESC
            LIMIT 100
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


# ── Render ────────────────────────────────────────────────────────────────────

def render(session):
    st.header("User Intelligence",
              help="Complete profile for any Cortex Code user — credits, LLM behaviour, "
                   "token economics, responsible AI assessment, and full prompt search.")
    st.caption("Search for a user to load their full profile. All data from CC_PROMPT_EVENTS and CC_PROMPT_VIOLATIONS.")

    # ── Search bar ────────────────────────────────────────────────────────────
    col_search, col_days = st.columns([3, 1])
    with col_search:
        raw_query = st.text_input("Search username",
                                  placeholder="Type part of a username…",
                                  key="ui_search")
    with col_days:
        days = st.selectbox("Period", [7, 30, 60, 90, 180], index=2,
                            format_func=lambda d: f"{d} days", key="ui_days")

    username = None
    if raw_query.strip():
        matches = _search_users(session, raw_query.strip())
        if not matches:
            st.info(f"No users found matching '{raw_query}' in the last 180 days.")
            return
        if len(matches) == 1:
            username = matches[0]
        else:
            username = st.selectbox("Select user", matches, key="ui_select")

    if not username:
        st.caption("Enter a username above to load their profile.")
        return

    # ── Load all data for this user ───────────────────────────────────────────
    summary_df  = _load_user_summary(session, username, days)
    credits_df  = _load_user_credits(session, username, days)
    models_df   = _load_user_models(session, username, days)
    viols_df    = _load_user_violations(session, username, days)
    quality_df  = _load_user_quality(session, username)
    daily_df    = _load_user_daily(session, username, days)

    if summary_df.empty or summary_df.iloc[0]["TOTAL_PROMPTS"] == 0:
        st.warning(f"No Cortex Code activity found for **{username}** in the last {days} days.")
        return

    s = summary_df.iloc[0]
    total_prompts   = int(s.get("TOTAL_PROMPTS", 0) or 0)
    total_tokens    = int(s.get("TOTAL_TOKENS", 0) or 0)
    cache_read      = int(s.get("CACHE_READ", 0) or 0)
    cache_write     = int(s.get("CACHE_WRITE", 0) or 0)
    input_tokens    = int(s.get("INPUT_TOKENS", 0) or 0)
    # Correct formula: hits / (hits + misses) — input_tokens excluded (not cache-related)
    cache_hit_rate  = round(cache_read / max(cache_read + cache_write, 1) * 100, 1)
    viol_count      = len(viols_df) if not viols_df.empty else 0
    high_viols      = int(viols_df[viols_df["RISK_LEVEL"] == "HIGH"]["HITS"].sum()) if not viols_df.empty else 0
    viol_rate       = round(viol_count / max(total_prompts, 1) * 100, 1)

    # Composite risk score: weight HIGH violations + viol rate + low safety
    q_safety = float(quality_df.iloc[0]["AVG_SAFETY"]) if not quality_df.empty and quality_df.iloc[0]["AVG_SAFETY"] else 1.0
    risk_score = min(1.0, (high_viols * 0.15) + (viol_rate * 0.02) + max(0, (0.7 - q_safety)))
    risk_badge = _risk_badge(risk_score)

    # ── User header ───────────────────────────────────────────────────────────
    st.divider()
    hcol1, hcol2 = st.columns([3, 1])
    with hcol1:
        st.markdown(f"## 👤 {username}")
        st.caption(f"Active: {str(s.get('FIRST_SEEN',''))[:10]} → {str(s.get('LAST_SEEN',''))[:10]}  ·  "
                   f"{int(s.get('ACTIVE_DAYS',0))} active days  ·  Top LLM: {s.get('TOP_MODEL','—')}")
    with hcol2:
        st.metric("Risk Profile _(exp)_", risk_badge,
                  help="Experimental composite score: insight count × 0.15 + insight rate × 0.02 + low safety penalty. Custom formula — use as directional signal only.")

    # ── KPI row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Prompts",    f"{total_prompts:,}",
              help="All CodingAgent.Step-0 spans in the selected period.")
    k2.metric("Sessions",         f"{int(s.get('SESSIONS',0)):,}",
              help="Distinct conversation threads (SESSION_ID).")
    k3.metric("Avg Steps/Session",f"{s.get('AVG_STEPS',0):.1f}",
              help="Average agent reasoning steps per session. Higher = more complex multi-step tasks.")
    k4.metric("Cache Hit Rate",   f"{cache_hit_rate:.1f}%",
              help="Tokens served from prompt cache vs fresh input. Higher = more efficient caching.")
    k5.metric("Insights",       f"{viol_count}",
              help="Distinct rules triggered in the selected period.")
    k6.metric("Success Rate",     f"{s.get('SUCCESS_RATE',0):.1f}%",
              help="% of prompts that completed with STATUS = SUCCESS.")

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    (tab_overview, tab_credits, tab_tokens,
     tab_violations, tab_quality, tab_prompts) = st.tabs([
        "Overview", "Credits", "Token Economics",
        "Responsible AI", "Custom Quality (Exp)", "Prompt Search"
    ])

    # ── OVERVIEW ──────────────────────────────────────────────────────────────
    with tab_overview:
        st.caption("Daily activity trend — prompts sent and tokens consumed over time.")

        if not daily_df.empty:
            daily_df["EVENT_DATE"] = daily_df["EVENT_DATE"].astype(str)

            _sec("Daily Prompt Activity")
            ch = (alt.Chart(daily_df).mark_area(opacity=0.7, color=_P)
                  .encode(x=alt.X("EVENT_DATE:T", title=""),
                          y=alt.Y("PROMPTS:Q", title="Prompts"),
                          tooltip=["EVENT_DATE:T", "PROMPTS:Q",
                                   alt.Tooltip("TOKENS:Q", format=","),
                                   alt.Tooltip("AVG_LAT_S:Q", title="Avg Lat (s)", format=".2f")])
                  .properties(height=180)
                  .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch, use_container_width=True)

        oc1, oc2 = st.columns(2)
        with oc1:
            _sec("LLM Distribution")
            if not models_df.empty:
                ch_m = (alt.Chart(models_df).mark_bar()
                        .encode(x=alt.X("PROMPTS:Q", title="Prompts"),
                                y=alt.Y("MODEL:N", sort="-x", title="",
                                        axis=alt.Axis(labelLimit=200)),
                                color=alt.value(_P),
                                tooltip=["MODEL:N", "PROMPTS:Q",
                                         alt.Tooltip("TOKENS:Q", format=",")])
                        .properties(height=max(150, len(models_df)*35))
                        .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_m, use_container_width=True)

        with oc2:
            _sec("Token Breakdown")
            tok_data = pd.DataFrame([
                {"TYPE": "Input",       "TOKENS": int(s.get("INPUT_TOKENS", 0) or 0)},
                {"TYPE": "Output",      "TOKENS": int(s.get("OUTPUT_TOKENS", 0) or 0)},
                {"TYPE": "Cache Read",  "TOKENS": int(s.get("CACHE_READ", 0) or 0)},
                {"TYPE": "Cache Write", "TOKENS": int(s.get("CACHE_WRITE", 0) or 0)},
            ])
            ch_t = (alt.Chart(tok_data).mark_bar()
                    .encode(x=alt.X("TOKENS:Q", title="Tokens",
                                    axis=alt.Axis(orient="top")),
                            y=alt.Y("TYPE:N", sort=None, title=""),
                            color=alt.Color("TYPE:N",
                                scale=alt.Scale(domain=["Input","Output","Cache Read","Cache Write"],
                                                range=[_P, _G, _A, _S])),
                            tooltip=["TYPE:N", alt.Tooltip("TOKENS:Q", format=",")])
                    .properties(height=150)
                    .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch_t, use_container_width=True)
            st.caption(f"Cache Hit Rate: **{cache_hit_rate:.1f}%** — "
                       + ("efficient caching, context reuse detected." if cache_hit_rate > 20
                          else "low cache reuse — each prompt uses fresh context."))

        if int(s.get("PRIVATE_COUNT", 0) or 0) > 0:
            st.warning(f"🔒 **{int(s['PRIVATE_COUNT'])} prompts** sent in Private Mode "
                       f"(responses not logged). This is normal for sensitive queries but worth noting.")

    # ── CREDITS ───────────────────────────────────────────────────────────────
    with tab_credits:
        st.caption("Credit consumption across CLI, Snowsight, and Desktop surfaces. "
                   "Data from CC_USAGE_DAILY_SUMMARY (refreshed every 30 min).")

        if credits_df.empty:
            st.info("No credit data in CC_USAGE_DAILY_SUMMARY for this user/period.")
        else:
            total_credits = credits_df["CREDITS"].sum()
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Total Credits", f"{total_credits:,.2f}",
                       help=f"Sum across all surfaces in the last {days} days.")
            for i, surface in enumerate(["CLI", "SNOWSIGHT", "DESKTOP"]):
                surf_creds = credits_df[credits_df["SURFACE"] == surface]["CREDITS"].sum()
                [cc2, cc3, cc4][i].metric(f"{surface}", f"{surf_creds:,.2f}")

            st.divider()
            _sec("Credit Trend by Surface")
            credits_df["USAGE_DATE"] = credits_df["USAGE_DATE"].astype(str)
            ch_c = (alt.Chart(credits_df).mark_area(opacity=0.7)
                    .encode(x=alt.X("USAGE_DATE:T", title=""),
                            y=alt.Y("CREDITS:Q", title="Credits", stack="zero"),
                            color=alt.Color("SURFACE:N", legend=alt.Legend(title="")),
                            tooltip=["USAGE_DATE:T", "SURFACE:N",
                                     alt.Tooltip("CREDITS:Q", format=",.3f")])
                    .properties(height=220)
                    .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch_c, use_container_width=True)

    # ── TOKEN ECONOMICS ────────────────────────────────────────────────────────
    with tab_tokens:
        st.caption("Detailed token breakdown per LLM. Cache Hit Rate shows what % of "
                   "prompt tokens were served from cache — higher means less re-processing and lower cost.")

        if not models_df.empty:
            models_df["CACHE_HIT_PCT"] = (
                models_df["CACHE_READ"] / (models_df["INPUT_TOKENS"] + models_df["CACHE_READ"]).replace(0, pd.NA) * 100
            ).round(1).fillna(0)
            tm1, tm2 = st.columns(2)
            with tm1:
                _sec("Cache Hit Rate by LLM")
                st.caption("Higher = more tokens served from cache for this model.")
                ch_ch = (alt.Chart(models_df).mark_bar()
                         .encode(x=alt.X("CACHE_HIT_PCT:Q", title="Cache Hit %",
                                         axis=alt.Axis(orient="top"),
                                         scale=alt.Scale(domain=[0, 100])),
                                 y=alt.Y("MODEL:N", sort="-x", title="",
                                         axis=alt.Axis(labelLimit=200)),
                                 color=alt.value(_A),
                                 tooltip=["MODEL:N",
                                          alt.Tooltip("CACHE_HIT_PCT:Q", title="Cache Hit %", format=".1f"),
                                          alt.Tooltip("CACHE_READ:Q", title="Cache Read Tokens", format=",")])
                         .properties(height=max(150, len(models_df)*40))
                         .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_ch, use_container_width=True)
            with tm2:
                _sec("LLM Token Summary")
                st.dataframe(models_df[["MODEL","PROMPTS","TOKENS","INPUT_TOKENS","CACHE_READ","CACHE_HIT_PCT"]],
                             use_container_width=True, hide_index=True,
                             column_config={
                                 "MODEL":        st.column_config.TextColumn("LLM"),
                                 "PROMPTS":      st.column_config.NumberColumn("Prompts", format="%.0f"),
                                 "TOKENS":       st.column_config.NumberColumn("Total Tokens", format="%.0f"),
                                 "INPUT_TOKENS": st.column_config.NumberColumn("Input", format="%.0f"),
                                 "CACHE_READ":   st.column_config.NumberColumn("Cache Read", format="%.0f"),
                                 "CACHE_HIT_PCT":st.column_config.NumberColumn("Hit %", format="%.1f",
                                                  help="Cache Read / (Input + Cache Read)"),
                             })

    # ── RESPONSIBLE AI ─────────────────────────────────────────────────────────
    with tab_violations:
        st.caption(f"Policy prompt insights detected in this user's prompts and responses "
                   f"over the last {days} days. Sourced from CC_PROMPT_VIOLATIONS.")

        if viols_df.empty:
            st.success("✅ No policy prompt insights detected for this user in the selected period.")
        else:
            vc1, vc2, vc3 = st.columns(3)
            high = int(viols_df[viols_df["RISK_LEVEL"] == "HIGH"]["HITS"].sum())
            med  = int(viols_df[viols_df["RISK_LEVEL"] == "MEDIUM"]["HITS"].sum())
            low  = int(viols_df[viols_df["RISK_LEVEL"] == "LOW"]["HITS"].sum())
            vc1.metric("High Severity Insights", high,
                       help="Insights from rules classified as HIGH risk — PII, Security, Prompt Injection.")
            vc2.metric("Medium Severity", med)
            vc3.metric("Low Severity", low)

            st.caption(f"Violation rate: **{viol_rate:.1f}%** of prompts triggered at least one rule.")

            st.divider()
            _sec("Insights by Rule")
            rule_agg = viols_df.groupby(["RULE_NAME","RISK_LEVEL","CATEGORY"])["HITS"].sum().reset_index().sort_values("HITS", ascending=False)
            ch_v = (alt.Chart(rule_agg).mark_bar()
                    .encode(x=alt.X("HITS:Q", title="Insights",
                                    axis=alt.Axis(orient="top")),
                            y=alt.Y("RULE_NAME:N", sort="-x", title="",
                                    axis=alt.Axis(labelLimit=260)),
                            color=alt.Color("RISK_LEVEL:N",
                                scale=alt.Scale(domain=["HIGH","MEDIUM","LOW"],
                                                range=[_R, _A, _G])),
                            tooltip=["RULE_NAME:N","RISK_LEVEL:N","CATEGORY:N","HITS:Q"])
                    .properties(height=max(180, len(rule_agg)*40))
                    .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch_v, use_container_width=True)

            _sec("Insight Detail")
            for _, row in viols_df.iterrows():
                risk = row["RISK_LEVEL"]
                badge = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk, "•")
                with st.expander(f"{badge} {row['RULE_NAME']} — {row['HITS']} hit(s) · {row['CONTENT_TYPE']}"):
                    st.markdown(f"**Rule:** {row['RULE_NAME']}  ·  **Category:** {row['CATEGORY']}  ·  **Last seen:** {str(row['LAST_SEEN'])[:10]}")
                    previews = row.get("PREVIEWS", [])
                    if isinstance(previews, str):
                        try: previews = json.loads(previews)
                        except Exception: previews = [previews]
                    for p in list(previews)[:3]:
                        if p:
                            st.caption(f"Preview: {str(p)[:200]}")

    # ── LLM-AS-JUDGE ──────────────────────────────────────────────────────────
    with tab_quality:
        st.caption("LLM-as-Judge scores for this user's responses. "
                   "Runs via SP_CC_EVALUATE_RESPONSES (optional — costs Cortex credits).")

        if quality_df.empty or int(quality_df.iloc[0].get("EVALUATED", 0) or 0) == 0:
            st.info("No quality scores yet for this user. Run SP_CC_EVALUATE_RESPONSES to populate.")
        else:
            q = quality_df.iloc[0]
            qc1, qc2, qc3, qc4 = st.columns(4)
            qc1.metric("Answer Relevance", f"{float(q['AVG_RELEVANCE']):.2f}",
                       help="Did the LLM response directly address what this user asked? 1.0 = fully answers the query.")
            qc2.metric("Groundedness", f"{float(q['AVG_GROUNDEDNESS']):.2f}",
                       help="Is the response factually grounded — no hallucinated code, APIs, or functions? 1.0 = no hallucination.")
            qc3.metric("Coherence", f"{float(q['AVG_COHERENCE']):.2f}",
                       help="Is the response logically structured and clear? 1.0 = very clear.")
            qc4.metric("Safety", f"{float(q['AVG_SAFETY']):.2f}",
                       help="Is the response free of harmful content? 1.0 = fully safe.")

            st.caption(f"Based on {int(q['EVALUATED'])} evaluated responses. Last evaluation: {str(q.get('LAST_EVAL',''))[:19]}")

            scores = pd.DataFrame([
                {"Metric": "Answer Relevance", "Score": float(q["AVG_RELEVANCE"])},
                {"Metric": "Groundedness",     "Score": float(q["AVG_GROUNDEDNESS"])},
                {"Metric": "Coherence",        "Score": float(q["AVG_COHERENCE"])},
                {"Metric": "Safety",           "Score": float(q["AVG_SAFETY"])},
            ])
            ch_q = (alt.Chart(scores).mark_bar()
                    .encode(x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 1]), title="Score (0–1)"),
                            y=alt.Y("Metric:N", sort=None, title=""),
                            color=alt.Color("Score:Q",
                                scale=alt.Scale(scheme="redyellowgreen", domain=[0, 1])),
                            tooltip=["Metric:N", alt.Tooltip("Score:Q", format=".3f")])
                    .properties(height=160)
                    .configure_view(strokeWidth=0).configure(background=_BG))
            st.altair_chart(ch_q, use_container_width=True)

    # ── PROMPT SEARCH ──────────────────────────────────────────────────────────
    with tab_prompts:
        st.caption(f"Search all prompts and responses for **{username}** over the last {days} days. "
                   "Private Mode responses show as redacted but prompt text is still searchable.")

        keyword = st.text_input("Search text in prompts or responses",
                                placeholder="e.g. ALTER USER, credit card, ignore instructions…",
                                key="ui_kw")

        if keyword.strip():
            with st.spinner(f"Searching {days} days of prompts for '{keyword}'…"):
                results = _load_prompt_search(session, username, days, keyword.strip())

            if results.empty:
                st.success(f"✅ No prompts or responses containing '{keyword}' found for this user.")
            else:
                st.caption(f"Found **{len(results)}** matching prompt(s) — showing all (max 100).")
                for _, row in results.iterrows():
                    ts   = str(row.get("EVENT_TS",""))[:16]
                    mdl  = str(row.get("MODEL",""))
                    lat  = row.get("LATENCY_MS", 0)
                    lat_s = f"{int(lat)/1000:.1f}s" if lat else "—"
                    pm   = bool(row.get("PRIVATE_MODE"))
                    icon = "🔒" if pm else ("✓" if row.get("STATUS") == "SUCCESS" else "✗")
                    with st.expander(f"{icon} {ts} · {mdl} · {lat_s}"):
                        st.markdown("**Prompt:**")
                        prompt_text = str(row.get("PROMPT") or "_Not captured_")
                        # highlight keyword
                        highlighted = re.sub(
                            f"({re.escape(keyword)})",
                            r"**\1**",
                            prompt_text[:2000],
                            flags=re.IGNORECASE
                        )
                        st.markdown(highlighted)
                        st.markdown("**Response:**")
                        if pm:
                            st.caption("_Private Mode — response not logged_")
                        else:
                            resp = str(row.get("RESPONSE") or "_Not yet evaluated_")
                            resp_highlighted = re.sub(
                                f"({re.escape(keyword)})",
                                r"**\1**",
                                resp[:3000],
                                flags=re.IGNORECASE
                            )
                            st.markdown(resp_highlighted)
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Status",  str(row.get("STATUS","")))
                        m2.metric("Tokens",  f"{int(row.get('TOTAL_TOKENS',0)):,}" if row.get("TOTAL_TOKENS") else "—")
                        m3.metric("Steps",   str(int(row.get("STEP_NUMBER",0) or 0)))
        else:
            st.caption("Enter a keyword above to search this user's prompt history.")
