"""
CoCo Control Hub - AI Observability
=====================================
Hierarchical view: Account Overview → Cohort / Team → User Search → Prompt Intelligence
Data sources:
  - CC_USAGE_DAILY_SUMMARY   — pre-aggregated, fast (account/cohort/user sections)
  - CC_PROMPT_EVENTS         — typed columns, fast (Prompt Intelligence tabs)
  - SHOW PARAMETERS           — enablement panel (fast)
Cost moved to Cost Attribution page. Latency moved to Model Intelligence page.
"""

import re
import json
import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_CREDIT_CONFIG,
    TABLE_USAGE_DAILY,
    TABLE_USAGE_HOURLY,
    TABLE_USER_COHORT_RESOLVED,
    TABLE_PROMPT_EVENTS,
    TABLE_RESPONSE_QUALITY,
    SP_EVALUATE_RESPONSES,
    escape_sql_literal,
    fq_table,
    fq_sp,
)

# ── Style constants — muted palette for dark theme ────────────────────────────
_BG  = "#0e1117"
_P   = "#7dd3fc"   # sky-300
_G   = "#6ee7b7"   # emerald-300
_W   = "#fcd34d"   # amber-300
_A   = "#fcd34d"   # alias for amber (used in new tabs)
_R   = "#fca5a5"   # rose-300

_CSS = """
<style>
/* Observability — chip badges for enablement status */
.enable-chip { display:inline-block; padding:0.16rem 0.55rem; border-radius:20px;
  font-size:0.7rem; font-weight:600; margin:0.1rem 0.15rem; vertical-align:middle }
.chip-ok   { background:rgba(34,197,94,0.12);  color:#4ade80; border:1px solid rgba(34,197,94,0.25) }
.chip-warn { background:rgba(245,158,11,0.12); color:#fbbf24; border:1px solid rgba(245,158,11,0.25) }
.chip-err  { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.25) }
</style>
"""


def _fmt_tokens(n: int) -> str:
    """Abbreviated token count: 2.1M, 245K, etc."""
    if not n: return "0"
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}K"
    return f"{n:,}"


def _sec(title):
    """Section header — consistent muted slate across all pages."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


def _chip(label, level="ok"):
    cls = {"ok": "chip-ok", "warn": "chip-warn", "err": "chip-err"}.get(level, "chip-ok")
    return f'<span class="enable-chip {cls}">{label}</span>'


# ── Chart helpers ──────────────────────────────────────────────────────────────
def _area(df, x, y, color=None, height=220):
    if df is None or df.empty:
        return None
    c = color or _P
    return (alt.Chart(df).mark_area(opacity=0.7, color=c)
            .encode(
                x=alt.X(f"{x}:T", title=""),
                y=alt.Y(f"{y}:Q", title=y.replace("_", " ").title()))
            .properties(height=height)
            .configure_view(strokeWidth=0).configure(background=_BG))


def _hbar(df, x, y, color=None, height=220, tooltip=None):
    if df is None or df.empty:
        return None
    c = color or _P
    enc = {
        "x": alt.X(f"{x}:Q", title=""),
        "y": alt.Y(f"{y}:N", sort="-x", title="",
                   axis=alt.Axis(labelLimit=250)),
        "color": alt.value(c),
    }
    if tooltip:
        enc["tooltip"] = tooltip
    return (alt.Chart(df).mark_bar().encode(**enc)
            .properties(height=height)
            .configure_view(strokeWidth=0).configure(background=_BG))


def _stacked_area(df, x, y, color_field, height=220):
    if df is None or df.empty:
        return None
    surface_colors = {"CLI": _P, "SNOWSIGHT": _G, "DESKTOP": _W}
    return (alt.Chart(df).mark_area(opacity=0.7)
            .encode(
                x=alt.X(f"{x}:T", title=""),
                y=alt.Y(f"{y}:Q", title=y.replace("_", " ").title(), stack="zero"),
                color=alt.Color(f"{color_field}:N",
                    scale=alt.Scale(
                        domain=list(surface_colors.keys()),
                        range=list(surface_colors.values())),
                    legend=alt.Legend(title="")))
            .properties(height=height)
            .configure_view(strokeWidth=0).configure(background=_BG))


# ── SQL queries — CC tables (fast) ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _load_account_summary(_session, days: int):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    try:
        df_surf = _session.sql(f"""
            SELECT
                USAGE_DATE,
                SURFACE,
                SUM(TOTAL_CREDITS)  AS CREDITS,
                SUM(TOTAL_TOKENS)   AS TOKENS,
                SUM(QUERY_COUNT)    AS QUERIES
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1, 2 ORDER BY 1
        """).to_pandas()

        df_dau = _session.sql(f"""
            SELECT USAGE_DATE, COUNT(DISTINCT USER_NAME) AS USERS
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1
        """).to_pandas()

        if not df_surf.empty:
            df_surf.columns = [c.upper() for c in df_surf.columns]
            df_surf["USAGE_DATE"] = pd.to_datetime(df_surf["USAGE_DATE"]).dt.date
        if not df_dau.empty:
            df_dau.columns = [c.upper() for c in df_dau.columns]
            df_dau["USAGE_DATE"] = pd.to_datetime(df_dau["USAGE_DATE"]).dt.date
        return df_surf, df_dau
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_wow(_session):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    try:
        df = _session.sql(f"""
            SELECT
                SUM(CASE WHEN USAGE_DATE >= DATEADD('day', -7, CURRENT_DATE())
                         THEN TOTAL_CREDITS END) AS CREDITS_THIS,
                SUM(CASE WHEN USAGE_DATE < DATEADD('day', -7, CURRENT_DATE())
                          AND USAGE_DATE >= DATEADD('day', -14, CURRENT_DATE())
                         THEN TOTAL_CREDITS END) AS CREDITS_PREV,
                COUNT(DISTINCT CASE WHEN USAGE_DATE >= DATEADD('day', -7, CURRENT_DATE())
                                    THEN USER_NAME END) AS USERS_THIS,
                COUNT(DISTINCT CASE WHEN USAGE_DATE < DATEADD('day', -7, CURRENT_DATE())
                                     AND USAGE_DATE >= DATEADD('day', -14, CURRENT_DATE())
                                    THEN USER_NAME END) AS USERS_PREV
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -14, CURRENT_DATE())
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            r = df.iloc[0]
            def _pct(a, b):
                a, b = float(a or 0), float(b or 0)
                if b == 0:
                    return None
                return round((a - b) / b * 100, 1)
            return {
                "credits_this": float(r["CREDITS_THIS"] or 0),
                "credits_prev": float(r["CREDITS_PREV"] or 0),
                "users_this":   int(r["USERS_THIS"] or 0),
                "users_prev":   int(r["USERS_PREV"] or 0),
                "credits_wow":  _pct(r["CREDITS_THIS"], r["CREDITS_PREV"]),
                "users_wow":    _pct(r["USERS_THIS"], r["USERS_PREV"]),
            }
        return {}
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def _load_cortex_params(_session):
    try:
        rows = _session.sql("SHOW PARAMETERS LIKE 'CORTEX%' IN ACCOUNT").collect()
        result = {}
        for row in rows:
            try:
                key = row["key"]
                val = row["value"]
                result[str(key).upper()] = val
            except Exception:
                pass
        return result or {"_error": "No CORTEX parameters found"}
    except Exception as e:
        return {"_error": str(e)[:200]}


@st.cache_data(ttl=300, show_spinner=False)
def _load_cohort_summary(_session, days: int):
    tbl_u = fq_table(_session, TABLE_USAGE_DAILY)
    tbl_c = fq_table(_session, TABLE_USER_COHORT_RESOLVED)
    tbl_cfg = fq_table(_session, TABLE_CREDIT_CONFIG)
    try:
        df = _session.sql(f"""
            SELECT
                COALESCE(ucr.COHORT_ROLE, 'Uncategorised') AS COHORT,
                COUNT(DISTINCT uds.USER_NAME)               AS MEMBERS,
                ROUND(SUM(uds.TOTAL_CREDITS), 4)            AS CREDITS_USED,
                ROUND(SUM(uds.TOTAL_TOKENS), 0)             AS TOKENS,
                COUNT(DISTINCT uds.USAGE_DATE)              AS ACTIVE_DAYS,
                MAX(uds.USAGE_DATE)                         AS LAST_ACTIVE,
                MAX(cc.CLI_DAILY_LIMIT)                     AS CLI_LIMIT,
                MAX(cc.SNOWSIGHT_DAILY_LIMIT)               AS SS_LIMIT
            FROM {tbl_u} uds
            LEFT JOIN {tbl_c} ucr ON ucr.USER_NAME = uds.USER_NAME
            LEFT JOIN {tbl_cfg} cc
                ON cc.ROLE_NAME = ucr.COHORT_ROLE
               AND cc.CONFIG_TYPE = 'COHORT' AND cc.IS_ACTIVE = TRUE
            WHERE uds.USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 ORDER BY CREDITS_USED DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_cohort_members(_session, cohort_role: str, days: int):
    tbl_u   = fq_table(_session, TABLE_USAGE_DAILY)
    tbl_c   = fq_table(_session, TABLE_USER_COHORT_RESOLVED)
    safe_r  = escape_sql_literal(cohort_role)
    try:
        df = _session.sql(f"""
            SELECT
                uds.USER_NAME,
                ROUND(SUM(uds.TOTAL_CREDITS), 4)   AS CREDITS,
                SUM(uds.QUERY_COUNT)                AS QUERIES,
                COUNT(DISTINCT uds.USAGE_DATE)      AS ACTIVE_DAYS,
                MAX(uds.USAGE_DATE)                 AS LAST_ACTIVE,
                SUM(CASE WHEN uds.SURFACE='CLI'      THEN uds.TOTAL_CREDITS ELSE 0 END) AS CLI_CREDITS,
                SUM(CASE WHEN uds.SURFACE='SNOWSIGHT' THEN uds.TOTAL_CREDITS ELSE 0 END) AS SS_CREDITS,
                SUM(CASE WHEN uds.SURFACE='DESKTOP'   THEN uds.TOTAL_CREDITS ELSE 0 END) AS DT_CREDITS
            FROM {tbl_u} uds
            JOIN {tbl_c} ucr
                ON ucr.USER_NAME = uds.USER_NAME
               AND ucr.COHORT_ROLE = '{safe_r}'
            WHERE uds.USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 ORDER BY CREDITS DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _search_users(_session, query: str, days: int):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    safe_q = escape_sql_literal(query)
    try:
        df = _session.sql(f"""
            SELECT
                USER_NAME,
                COALESCE(COHORT_ROLE, 'None') AS COHORT,
                ROUND(SUM(TOTAL_CREDITS), 4)  AS CREDITS,
                SUM(QUERY_COUNT)              AS QUERIES,
                COUNT(DISTINCT USAGE_DATE)    AS ACTIVE_DAYS,
                MAX(USAGE_DATE)               AS LAST_ACTIVE
            FROM {tbl}
            WHERE USER_NAME ILIKE '%{safe_q}%'
              AND USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1, 2
            ORDER BY CREDITS DESC
            LIMIT 50
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_user_daily(_session, username: str, days: int):
    tbl = fq_table(_session, TABLE_USAGE_DAILY)
    safe_u = escape_sql_literal(username)
    try:
        df = _session.sql(f"""
            SELECT USAGE_DATE, SURFACE,
                   ROUND(TOTAL_CREDITS, 4) AS CREDITS, TOTAL_TOKENS, QUERY_COUNT
            FROM {tbl}
            WHERE USER_NAME = '{safe_u}'
              AND USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            ORDER BY USAGE_DATE
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


# ── Prompt Intelligence queries ────────────────────────────────────────────────
_SYS_RE = re.compile(r'<system-reminder>.*?</system-reminder>', re.DOTALL)
_SENSITIVE = ["customer_pii","credit_card","ssn","password","api_key",
              "secret","private_key","salary","social_security","token"]


def _clean(raw):
    if not raw:
        return ""
    return _SYS_RE.sub("", raw).strip() or raw


@st.cache_data(ttl=300, show_spinner=False)
def _events_table_populated(_session):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        r = _session.sql(f"SELECT COUNT(*) AS N FROM {tbl}").collect()
        return int(r[0][0]) > 0
    except Exception:
        return False


@st.cache_data(ttl=300, show_spinner=False)
def _load_events(_session, days: int, user_filter: str):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    uf = f"AND USER_NAME = '{escape_sql_literal(user_filter)}'" if user_filter else ""
    try:
        df = _session.sql(f"""
            SELECT
                EVENT_TS          AS TIMESTAMP,
                USER_NAME,
                ROLE_NAME,
                MODEL,
                ENTRYPOINT,
                PROMPT            AS RAW_PROMPT,
                PROMPT,
                RESPONSE,
                COALESCE(PRIVATE_MODE, FALSE) AS PRIVATE_MODE,
                LATENCY_MS,
                STATUS,
                REQUEST_ID,
                TOTAL_TOKENS,
                TOOLS_RAW,
                SESSION_ID,
                EVENT_DATE        AS USAGE_DATE,
                ROUND(LATENCY_MS / 1000.0, 2) AS LATENCY_S,
                (STATUS = 'SUCCESS')           AS SUCCESS
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            {uf}
            ORDER BY EVENT_TS DESC
            LIMIT 5000
        """).to_pandas()
    except Exception as e:
        if "AI_OBSERVABILITY_READER" in str(e) or "Insufficient privileges" in str(e).lower():
            return pd.DataFrame(), "permission"
        return pd.DataFrame(), str(e)

    if df.empty:
        return df, None
    df.columns = [c.upper() for c in df.columns]
    df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"]).dt.date
    df["TIMESTAMP"]  = pd.to_datetime(df["TIMESTAMP"])
    df["LATENCY_S"]  = df["LATENCY_S"].fillna(0).round(2)
    df["SUCCESS"]    = df["SUCCESS"].astype(bool)
    df["PROMPT"]     = df["PROMPT"].fillna("").apply(lambda x: _clean(str(x)) if x else "")
    return df, None


@st.cache_data(ttl=300, show_spinner=False)
def _load_kpi_daily(_session, days: int, user_filter: str):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    uf = f"AND USER_NAME = '{escape_sql_literal(user_filter)}'" if user_filter else ""
    empty = {"total": 0, "users": 0, "avg_lat": 0.0, "success_rate": 0.0}
    try:
        rows = _session.sql(f"""
            SELECT
                COUNT(*)                                                          AS TOTAL_PROMPTS,
                COUNT(DISTINCT USER_NAME)                                         AS UNIQUE_USERS,
                ROUND(AVG(LATENCY_MS) / 1000.0, 1)                               AS AVG_LATENCY_S,
                ROUND(SUM(CASE WHEN STATUS = 'SUCCESS' THEN 1.0 ELSE 0.0 END)
                      / NULLIF(COUNT(*), 0) * 100, 2)                             AS SUCCESS_RATE
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            {uf}
        """).collect()
        if not rows:
            return empty, pd.DataFrame()
        r = rows[0]
        metrics = {
            "total":        int(r[0] or 0),
            "users":        int(r[1] or 0),
            "avg_lat":      float(r[2] or 0),
            "success_rate": float(r[3] or 0),
        }

        df_daily = _session.sql(f"""
            SELECT EVENT_DATE AS USAGE_DATE, STATUS, COUNT(*) AS PROMPT_COUNT
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            {uf}
            GROUP BY 1, 2
            ORDER BY 1
        """).to_pandas()
        if not df_daily.empty:
            df_daily.columns = [c.upper() for c in df_daily.columns]
            df_daily["USAGE_DATE"] = pd.to_datetime(df_daily["USAGE_DATE"]).dt.date
        return metrics, df_daily
    except Exception:
        return empty, pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_sessions(_session, days: int):
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT
                SESSION_ID,
                USER_NAME,
                MAX(ENTRYPOINT)      AS ENTRYPOINT,
                MIN(EVENT_TS)        AS SESSION_START,
                COUNT(*)             AS PROMPT_COUNT,
                SUM(TOTAL_TOKENS)    AS TOKENS,
                SUM(CASE WHEN STATUS = 'SUCCESS' THEN 1 ELSE 0 END) AS SUCCESSES
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND SESSION_ID IS NOT NULL
            GROUP BY 1, 2
            ORDER BY SESSION_START DESC
            LIMIT 100
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_token_econ_daily(_session, days: int):
    """Aggregate token economics by day for stacked area chart."""
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT EVENT_DATE,
                   SUM(INPUT_TOKENS)       AS INPUT_T,
                   SUM(OUTPUT_TOKENS)      AS OUTPUT_T,
                   SUM(CACHE_READ_TOKENS)  AS CACHE_READ_T,
                   SUM(CACHE_WRITE_TOKENS) AS CACHE_WRITE_T,
                   SUM(TOTAL_TOKENS)       AS TOTAL_T
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1 ORDER BY 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["EVENT_DATE"] = pd.to_datetime(df["EVENT_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_prompt_patterns(_session, days: int, show_system: bool = False):
    """Category distribution, trend, cost — excludes system_internal by default."""
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    sys_filter = "" if show_system else "AND PROMPT_CATEGORY != 'system_internal'"
    try:
        dist = _session.sql(f"""
            SELECT PROMPT_CATEGORY                       AS CATEGORY,
                   COUNT(*)                              AS PROMPTS,
                   COUNT(DISTINCT USER_NAME)             AS USERS,
                   ROUND(SUM(PROMPT_COST_CREDITS), 4)   AS TOTAL_COST,
                   ROUND(AVG(PROMPT_COST_CREDITS), 6)   AS AVG_COST
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND PROMPT_CATEGORY IS NOT NULL
              {sys_filter}
            GROUP BY 1 ORDER BY PROMPTS DESC
        """).to_pandas()
        if not dist.empty:
            dist.columns = [c.upper() for c in dist.columns]

        trend = _session.sql(f"""
            SELECT EVENT_DATE, PROMPT_CATEGORY AS CATEGORY, COUNT(*) AS PROMPTS
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND PROMPT_CATEGORY IS NOT NULL
              {sys_filter}
            GROUP BY 1, 2 ORDER BY 1
        """).to_pandas()
        if not trend.empty:
            trend.columns = [c.upper() for c in trend.columns]

        return dist, trend
    except Exception:
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_category_samples(_session, category: str, days: int):
    """Up to 3 sample prompts per category for the expandable section."""
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    safe_cat = escape_sql_literal(category)
    try:
        df = _session.sql(f"""
            SELECT USER_NAME, MODEL, EVENT_TS, PROMPT,
                   PROMPT_COST_CREDITS, LATENCY_MS
            FROM {tbl}
            WHERE PROMPT_CATEGORY = '{safe_cat}'
              AND EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND PROMPT IS NOT NULL
              AND (PRIVATE_MODE IS NULL OR PRIVATE_MODE = FALSE)
            ORDER BY RANDOM()
            LIMIT 3
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_tool_events(_session, days: int):
    """CC_PROMPT_EVENTS rows where TOOLS_RAW is populated. LIMIT 5000."""
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT TOOLS_RAW, USER_NAME, SESSION_ID, EVENT_DATE
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND TOOLS_RAW IS NOT NULL
            LIMIT 5000
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def _load_entrypoints(_session, days: int):
    """Aggregate queries, tokens, latency, and step depth by ENTRYPOINT and day."""
    tbl = fq_table(_session, TABLE_PROMPT_EVENTS)
    try:
        df = _session.sql(f"""
            SELECT ENTRYPOINT, EVENT_DATE,
                   COUNT(*) AS QUERIES,
                   SUM(TOTAL_TOKENS) AS TOKENS,
                   ROUND(AVG(LATENCY_MS) / 1000.0, 2) AS AVG_LATENCY_S,
                   ROUND(AVG(STEP_NUMBER), 1)          AS AVG_STEPS
            FROM {tbl}
            WHERE EVENT_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
              AND ENTRYPOINT IS NOT NULL AND ENTRYPOINT != ''
            GROUP BY 1, 2 ORDER BY 2, 1
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
            df["EVENT_DATE"] = pd.to_datetime(df["EVENT_DATE"]).dt.date
        return df
    except Exception:
        return pd.DataFrame()


# ── Main render ────────────────────────────────────────────────────────────────
def render(session):
    st.markdown(_CSS, unsafe_allow_html=True)
    st.header("AI Observability")

    # ── Global lookback ───────────────────────────────────────────────────────
    if "obs_days" not in st.session_state:
        st.session_state["obs_days"] = 30

    col_days, col_nav = st.columns([1, 5])
    with col_days:
        days = st.selectbox("Lookback", [7, 14, 30, 60, 90],
                            index=[7,14,30,60,90].index(st.session_state["obs_days"]),
                            key="obs_days_sel", label_visibility="collapsed",
                            help="Days of history for all sections.")
        if days != st.session_state["obs_days"]:
            st.session_state["obs_days"] = days
    with col_nav:
        section = st.radio("", ["Account Overview","Cohort / Team","User Search","Prompt Intelligence"],
                           horizontal=True, key="obs_section", label_visibility="collapsed",
                           help="Account Overview: DAU, WoW, enablement. Cohort/Team: per-cohort breakdown. User Search: drill into a specific user. Prompt Intelligence: raw span data.")

    active_days = st.session_state["obs_days"]
    st.divider()

    # ── Cortex AI Guardrails headline ─────────────────────────────────────────
    try:
        _gr_rows = session.sql("SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT").collect()
        _gr_val  = str(_gr_rows[0]["value"]) if _gr_rows and _gr_rows[0]["value"] else ""
        _gr_on   = "enabled: true" in _gr_val.lower()
    except Exception:
        _gr_on, _gr_val = False, ""

    if _gr_on:
        _gr_chip = _chip("🛡️ Cortex AI Guardrails — Enabled", "ok")
        _gr_msg  = "Runtime prompt injection & jailbreak protection is active for Cortex Code, Cortex Agents, and Snowflake Intelligence."
    else:
        _gr_chip = _chip("⚠️ Cortex AI Guardrails — Not Enabled", "warn")
        _gr_msg  = "Enable runtime protection against prompt injection and jailbreak attacks. Requires Enterprise Edition + cross-region inference."

    with st.expander(f"🛡️ Cortex AI Guardrails  {'✓ Active' if _gr_on else '⚠ Not Enabled'}", expanded=not _gr_on):
        st.markdown(_gr_chip + f"&nbsp;&nbsp;<span style='font-size:0.82rem;color:#94a3b8'>{_gr_msg}</span>", unsafe_allow_html=True)
        st.caption("Part of Snowflake Horizon Catalog · Enterprise Edition required · Billed per token scanned")

        c1, c2, c3 = st.columns(3)
        c1.markdown("**🔒 Prompt Injection Detection**\nIdentifies & blocks attempts to override system instructions, including indirect injections via tool calls.")
        c2.markdown("**🚫 Jailbreak Prevention**\nDetects attempts to bypass the model's safety protocols and security boundaries.")
        c3.markdown("**⚡ Zero-Day Protection**\nUses contextual reasoning to catch sophisticated, previously unknown attack patterns in real time.")

        st.divider()
        col_en, col_dis = st.columns(2)
        with col_en:
            st.markdown("**Enable** `🔐 ACCOUNTADMIN only`")
            st.code("""\
ALTER ACCOUNT SET AI_SETTINGS = $$
  guardrails:
    advanced_prompt_injection:
      - enabled: true
$$;""", language="sql")
        with col_dis:
            st.markdown("**Disable / Check status**")
            st.code("""\
-- Disable
ALTER ACCOUNT UNSET AI_SETTINGS;

-- Check current setting
SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT;""", language="sql")

        if not _gr_on:
            st.info("Also ensure cross-region inference is enabled: `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY';`")

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Account Overview
    # ══════════════════════════════════════════════════════════════════════════
    if section == "Account Overview":
        summary, dau_df_raw = _load_account_summary(session, active_days)
        wow     = _load_wow(session)
        params  = _load_cortex_params(session)

        if summary.empty:
            st.info("No Cortex Code usage data in this period.")
        else:
            total = summary.groupby("USAGE_DATE").agg(
                CREDITS=("CREDITS","sum"), TOKENS=("TOKENS","sum"),
                QUERIES=("QUERIES","sum")
            ).reset_index()

            total_credits = total["CREDITS"].sum()
            total_queries = total["QUERIES"].sum()
            peak_dau  = int(dau_df_raw["USERS"].max()) if not dau_df_raw.empty else 0
            avg_dau   = dau_df_raw["USERS"].mean()     if not dau_df_raw.empty else 0

            def _delta(val):
                if val is None:
                    return None
                return f"{'+' if val >= 0 else ''}{val:.1f}%"

            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Peak DAU",          f"{peak_dau:,}",
                      help="Highest number of distinct Cortex Code users on any single day in this period.")
            k2.metric("Avg Daily Users",   f"{avg_dau:.1f}",
                      delta=_delta(wow.get("users_wow")),
                      help="WoW = last 7 days vs prior 7 days. Distinct users across all surfaces.")
            k3.metric("Total Credits",     f"{total_credits:,.3f}",
                      delta=_delta(wow.get("credits_wow")),
                      help="Sum of all Cortex Code credits consumed in this period across CLI, Snowsight, and Desktop.")
            k4.metric("Total Queries",     f"{int(total_queries):,}",
                      help="Total number of LLM API calls (prompts sent) across all surfaces.")
            k5.metric("Period",            f"{active_days} days",
                      help="Lookback window selected above.")

            st.divider()

            # DAU trend — full width (Surface Split moved to Entrypoints tab)
            _sec("Daily Active Users")
            if not dau_df_raw.empty:
                dau_plot = dau_df_raw.copy()
                dau_plot["USAGE_DATE"] = dau_plot["USAGE_DATE"].astype(str)
                ch = _area(dau_plot, "USAGE_DATE", "USERS", height=200)
                if ch:
                    st.altair_chart(ch, use_container_width=True)

            st.caption("💡 For full credit consumption charts, heatmaps, and spike detection → see **Usage Trends** page. For surface split → see **Prompt Intelligence → Entrypoints** tab.")

        st.divider()

        # Enablement status
        _sec("Cortex Code Enablement Status")
        err = params.get("_error") if params else None
        if err:
            if "Insufficient privileges" in err or "not authorized" in err.lower():
                st.warning(
                    "Requires MONITOR privilege or ACCOUNTADMIN on the Streamlit app owner role. "
                    "Run: `GRANT MONITOR ON ACCOUNT TO ROLE CC_APP_ROLE`"
                )
            else:
                st.warning(f"Could not read account parameters: {err}")
        elif not params:
            st.warning("Could not read account parameters.")
        else:
            chips = []

            cr = params.get("CORTEX_ENABLED_CROSS_REGION","")
            if cr in ("ANY_REGION","AWS_US","AWS_EU","AWS_APJ","AZURE_US","AZURE_EU"):
                chips.append(_chip(f"Cross-region: {cr}", "ok"))
            else:
                chips.append(_chip(f"Cross-region: {cr or 'DISABLED'}", "err"))

            al = params.get("CORTEX_MODELS_ALLOWLIST","ALL")
            if al == "NONE":
                chips.append(_chip("Models: ALL BLOCKED", "err"))
            elif al == "ALL":
                chips.append(_chip("Models: All allowed", "ok"))
            else:
                chips.append(_chip(f"Models: {al[:40]}", "warn"))

            for surface, key in [
                ("CLI",       "CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER"),
                ("Snowsight", "CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER"),
                ("Desktop",   "CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER"),
            ]:
                v = params.get(key, "-1")
                if v == "0":
                    chips.append(_chip(f"{surface} limit: BLOCKED", "err"))
                elif v == "-1":
                    chips.append(_chip(f"{surface} limit: No limit", "ok"))
                else:
                    chips.append(_chip(f"{surface} limit: {v}/day", "warn"))

            st.markdown(" ".join(chips), unsafe_allow_html=True)

        st.divider()

        # Error snapshot (lazy)
        _sec("Recent Errors (from Observability Events)")
        err_key = f"obs_errors_{active_days}"
        if err_key not in st.session_state:
            st.caption("Scans AI_OBSERVABILITY_EVENTS for failed spans and zero-output events. Loaded on demand.")
            if st.button("Load Error Snapshot", key="btn_err_snap", type="primary"):
                with st.spinner("Scanning for errors…"):
                    try:
                        edf = session.sql(f"""
                            SELECT
                                RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.status']::STRING AS STATUS,
                                COUNT(*) AS SPANS,
                                COUNT(DISTINCT RESOURCE_ATTRIBUTES['snow.user.name']::STRING) AS USERS,
                                SUM(CASE WHEN
                                    COALESCE(RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.token_count.output']::INT, 0) = 0
                                    THEN 1 ELSE 0 END) AS ZERO_OUTPUT
                            FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
                            WHERE RECORD_TYPE = 'SPAN'
                              AND RECORD:name::STRING = 'CodingAgent.Step-0'
                              AND TIMESTAMP >= DATEADD('day', -{active_days}, CURRENT_TIMESTAMP())
                            GROUP BY 1 ORDER BY SPANS DESC
                        """).to_pandas()
                        edf.columns = [c.upper() for c in edf.columns]
                        st.session_state[err_key] = edf
                    except Exception as ex:
                        st.session_state[err_key] = str(ex)
                st.rerun()
        else:
            edf = st.session_state[err_key]
            if isinstance(edf, str):
                st.error(f"Could not load: {edf}")
            elif not edf.empty:
                total_spans  = edf["SPANS"].sum()
                fail_row     = edf[edf["STATUS"] != "SUCCESS"]
                fail_spans   = int(fail_row["SPANS"].sum()) if not fail_row.empty else 0
                zero_out     = int(edf["ZERO_OUTPUT"].sum()) if "ZERO_OUTPUT" in edf.columns else 0
                ok_pct       = round((1 - fail_spans / total_spans) * 100, 1) if total_spans else 100
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Spans",     f"{int(total_spans):,}",
                          help="All CodingAgent.Step-0 spans in the selected period.")
                c2.metric("Failed Spans",    f"{fail_spans:,}",
                          help="Spans where STATUS != SUCCESS.")
                c3.metric("Zero-output",     f"{zero_out:,}",
                          help="Spans that succeeded but returned 0 output tokens — silent failures.")
                c4.metric("Success Rate",    f"{ok_pct}%",
                          help="Percentage of spans that completed with STATUS = SUCCESS.")
                st.dataframe(edf, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Cohort / Team
    # ══════════════════════════════════════════════════════════════════════════
    elif section == "Cohort / Team":
        coh_df = _load_cohort_summary(session, active_days)

        if coh_df.empty:
            st.info("No cohort data. Assign users to cohorts in Credit Configuration.")
        else:
            _sec("All Cohorts — Credit Consumption")
            ch = _hbar(coh_df, "CREDITS_USED", "COHORT", color=_W,
                       height=max(180, len(coh_df)*36),
                       tooltip=["COHORT:N","MEMBERS:Q",
                                alt.Tooltip("CREDITS_USED:Q", format=".4f")])
            if ch:
                st.altair_chart(ch, use_container_width=True)
            st.dataframe(coh_df, use_container_width=True, hide_index=True,
                         column_config={
                             "CREDITS_USED": st.column_config.NumberColumn("Credits", format="%.4f"),
                             "LAST_ACTIVE":  st.column_config.DateColumn("Last Active"),
                             "CLI_LIMIT":    st.column_config.NumberColumn("CLI Limit/day"),
                             "SS_LIMIT":     st.column_config.NumberColumn("SS Limit/day"),
                         })

            st.divider()
            _sec("Cohort Member Detail")
            cohorts = coh_df["COHORT"].tolist()
            chosen  = st.selectbox("Select cohort", cohorts, key="obs_cohort_sel")
            if chosen and chosen != "Uncategorised":
                members = _load_cohort_members(session, chosen, active_days)
                if members.empty:
                    st.info(f"No usage data for {chosen} in this period.")
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Members active", len(members),
                              help="Distinct users in this cohort with at least one query in the selected period.")
                    m2.metric("Total credits",  f"{members['CREDITS'].sum():,.4f}",
                              help="Sum of all credits consumed by this cohort in the selected period.")
                    m3.metric("Total queries",  f"{int(members['QUERIES'].sum()):,}",
                              help="Total LLM API calls made by cohort members.")
                    st.dataframe(members, use_container_width=True, hide_index=True,
                                 column_config={
                                     "CREDITS":     st.column_config.NumberColumn("Credits", format="%.4f"),
                                     "LAST_ACTIVE": st.column_config.DateColumn("Last Active"),
                                     "CLI_CREDITS": st.column_config.NumberColumn("CLI Credits", format="%.4f"),
                                     "SS_CREDITS":  st.column_config.NumberColumn("SS Credits", format="%.4f"),
                                 })
            else:
                st.caption("Select a named cohort to see member breakdown.")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — User Search
    # ══════════════════════════════════════════════════════════════════════════
    elif section == "User Search":
        _sec("Search Cortex Code Users")
        query = st.text_input("Username (partial match)", placeholder="e.g. JSMITH",
                              key="obs_user_search",
                              help="Searches CC_USAGE_DAILY_SUMMARY — shows users with activity.")
        if not query.strip():
            st.caption("Enter at least part of a username to search.")
        else:
            udf = _search_users(session, query.strip(), active_days)
            if udf.empty:
                st.info(f"No users matching '{query}' with activity in the last {active_days} days.")
            else:
                st.caption(f"{len(udf)} user(s) found")
                st.dataframe(udf, use_container_width=True, hide_index=True,
                             column_config={
                                 "CREDITS":     st.column_config.NumberColumn("Credits", format="%.4f"),
                                 "LAST_ACTIVE": st.column_config.DateColumn("Last Active"),
                             })

                st.divider()
                _sec("User Daily Trend")
                sel_user = st.selectbox("Select user for detail",
                                        udf["USER_NAME"].tolist(), key="obs_user_detail")
                if sel_user:
                    uday = _load_user_daily(session, sel_user, active_days)
                    if not uday.empty:
                        cli_cred = uday[uday["SURFACE"]=="CLI"]["CREDITS"].sum()
                        ss_cred  = uday[uday["SURFACE"]=="SNOWSIGHT"]["CREDITS"].sum()
                        dt_cred  = uday[uday["SURFACE"]=="DESKTOP"]["CREDITS"].sum()
                        ud1, ud2, ud3, ud4 = st.columns(4)
                        ud1.metric("CLI Credits",      f"{cli_cred:,.4f}",
                                   help="Cortex Code CLI credits consumed by this user in the selected period.")
                        ud2.metric("Snowsight Credits", f"{ss_cred:,.4f}",
                                   help="Cortex Code Snowsight credits consumed by this user in the selected period.")
                        ud3.metric("Desktop Credits",   f"{dt_cred:,.4f}",
                                   help="Cortex Code Desktop credits consumed by this user in the selected period.")
                        ud4.metric("Active Days",
                                   str(uday["USAGE_DATE"].nunique()),
                                   help="Number of distinct days this user had at least one Cortex Code query.")

                        uday_s = uday.copy()
                        uday_s["USAGE_DATE"] = uday_s["USAGE_DATE"].astype(str)
                        ch = _stacked_area(uday_s, "USAGE_DATE", "CREDITS", "SURFACE", height=180)
                        if ch:
                            st.altair_chart(ch, use_container_width=True)

                    prompt_key = f"obs_user_prompts_{sel_user}_{active_days}"
                    st.divider()
                    _sec(f"Prompt History — {sel_user}")
                    if prompt_key not in st.session_state:
                        st.caption("Loads from CC_PROMPT_EVENTS.")
                        if st.button("Load Prompts", key="btn_user_prompts", type="primary",
                                     help="Loads raw prompt spans from CC_PROMPT_EVENTS for this user. Cached 5 min."):
                            with st.spinner("Loading…"):
                                pdf, perr = _load_events(session, active_days, sel_user)
                            st.session_state[prompt_key] = (pdf, perr)
                            st.rerun()
                    else:
                        pdf, perr = st.session_state[prompt_key]
                        if perr == "permission":
                            st.error("AI_OBSERVABILITY_READER not granted to CC_APP_ROLE.")
                        elif perr:
                            st.error(f"Error: {perr}")
                        elif pdf.empty:
                            st.info("No prompt spans found for this user/period.")
                        else:
                            st.caption(f"{len(pdf)} prompts")
                            for _, row in pdf.head(25).iterrows():
                                icon = "✓" if row["STATUS"] == "SUCCESS" else "✗"
                                with st.expander(f"{icon} {row['TIMESTAMP'].strftime('%Y-%m-%d %H:%M')} · {row['MODEL']} · {row.get('ENTRYPOINT') or '—'} · {row['LATENCY_S']}s"):
                                    st.markdown(f"**Prompt:** {row['PROMPT'] or '_Not captured_'}")
                                    c1, c2 = st.columns(2)
                                    c1.metric("Latency", f"{row['LATENCY_S']}s")
                                    c2.metric("Tokens",  int(row["TOTAL_TOKENS"]) if pd.notna(row["TOTAL_TOKENS"]) and row["TOTAL_TOKENS"] else "N/A")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Prompt Intelligence
    # ══════════════════════════════════════════════════════════════════════════
    elif section == "Prompt Intelligence":
        if not _events_table_populated(session):
            st.warning(
                "**Prompt Intelligence table is empty.** "
                "Run the SP now to backfill the last 30 days of events — this is a one-time operation. "
                "After that the nightly task keeps it current automatically."
            )
            from config import fq_sp
            if st.button("Backfill Events Now (loads last 30 days)", type="primary",
                         key="btn_backfill_events"):
                sp = fq_sp(session, "SP_CC_CLASSIFY_PROMPTS")
                with st.spinner("Loading events from AI_OBSERVABILITY_EVENTS — this may take 1–2 minutes for large accounts…"):
                    try:
                        result = session.sql(f"CALL {sp}(720)").collect()
                        raw = result[0][0] if result else "{}"
                        res = __import__("json").loads(raw) if isinstance(raw, str) else raw
                        loaded = res.get("events_loaded", 0)
                        st.cache_data.clear()
                        st.success(f"✓ Loaded {loaded:,} events. Refreshing…")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Backfill failed: {e}")
            return

        if "obs_pi_user" not in st.session_state:
            st.session_state["obs_pi_user"] = ""

        with st.form("obs_pi_form"):
            col_u, col_btn = st.columns([3, 1])
            with col_u:
                pi_user = st.text_input("Filter by user (optional)",
                                        value=st.session_state["obs_pi_user"],
                                        placeholder="Leave blank for all users",
                                        key="obs_pi_user_inp")
            with col_btn:
                st.write("")
                pi_sub = st.form_submit_button("Apply", use_container_width=True)

        if pi_sub:
            st.session_state["obs_pi_user"] = pi_user.strip().upper()

        active_filter = st.session_state["obs_pi_user"]

        # Aggregate query (no LIMIT) — drives KPI metrics and Activity Trend
        kpi, df_daily = _load_kpi_daily(session, active_days, active_filter)

        # Raw events (LIMIT 5000, most recent) — drives per-row tabs only
        df, err = _load_events(session, active_days, active_filter)

        if err == "permission":
            st.error("Grant `APPLICATION ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_APP_ROLE`.")
            return
        if err:
            st.error(f"Error: {err}")
            return
        if kpi["total"] == 0 and df.empty:
            st.info("No spans in this period.")
            return

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Prompts",  f"{kpi['total']:,}",
                  help="Total CodingAgent.Step-0 spans in the selected period from CC_PROMPT_EVENTS.")
        k2.metric("Unique Users",   f"{kpi['users']:,}",
                  help="Distinct users who sent at least one prompt in this period.")
        k3.metric("Avg Latency",    f"{kpi['avg_lat']:.1f}s",
                  help="Mean time from prompt submission to model response, in seconds.")
        k4.metric("Success Rate",   f"{kpi['success_rate']:.2f}%",
                  help="Percentage of spans that completed with STATUS = SUCCESS.")

        st.divider()

        (t_trend, t_users, t_models, t_prompts,
         t_sessions, t_token_econ, t_tool_intel, t_entrypoint, t_quality, t_patterns) = st.tabs([
            "Activity Trend", "Top Users", "Model Usage",
            "Prompt Browser", "Sessions", "Token Economics", "Tool Intelligence",
            "Entrypoints", "Quality Scores", "Prompt Patterns"
        ])

        with t_trend:
            st.caption("Daily prompt volume and success/failure split. Sourced from CC_PROMPT_EVENTS — populated nightly by SP_CC_CLASSIFY_PROMPTS.")
            _sec("Daily Prompt Volume")
            if not df_daily.empty:
                daily = df_daily.groupby("USAGE_DATE")["PROMPT_COUNT"].sum().reset_index(name="PROMPTS")
                daily["USAGE_DATE"] = daily["USAGE_DATE"].astype(str)
                c = _area(daily, "USAGE_DATE", "PROMPTS")
                if c:
                    st.altair_chart(c, use_container_width=True)

            _sec("Success vs Failure by Day")
            st.caption("FAILURE means the LLM call returned a non-SUCCESS status — e.g. timeout, content filter, or model error. "
                       "Zero failures is normal and expected when the system is healthy.")
            if not df_daily.empty:
                ds = df_daily.rename(columns={"PROMPT_COUNT": "N"}).copy()
                ds["USAGE_DATE"] = ds["USAGE_DATE"].astype(str)
                ch = (alt.Chart(ds).mark_bar()
                      .encode(x=alt.X("USAGE_DATE:T", title=""),
                              y=alt.Y("N:Q", title="Prompts"),
                              color=alt.Color("STATUS:N",
                                  scale=alt.Scale(domain=["SUCCESS","FAILURE"],
                                                  range=[_G, _R])),
                              tooltip=["USAGE_DATE:T","STATUS:N","N:Q"])
                      .properties(height=200)
                      .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch, use_container_width=True)

        with t_users:
            st.caption("Top 20 users ranked by prompt count. Helps identify power users, over-usage, or automation scripts running under a user identity.")
            _sec("Top Users by Prompt Count")
            bu = (df.groupby("USER_NAME")
                    .agg(PROMPTS=("PROMPT","count"),
                         AVG_LAT=("LATENCY_S","mean"),
                         SUCCESS=("SUCCESS","mean"),
                         TOKENS=("TOTAL_TOKENS","sum"))
                    .reset_index().sort_values("PROMPTS", ascending=False).head(20))
            bu["SUCCESS"] = (bu["SUCCESS"]*100).round(1)
            bu["AVG_LAT"] = bu["AVG_LAT"].round(2)
            c = _hbar(bu, "PROMPTS", "USER_NAME", height=max(200, len(bu)*30),
                      tooltip=["USER_NAME:N","PROMPTS:Q","AVG_LAT:Q","SUCCESS:Q"])
            if c:
                st.altair_chart(c, use_container_width=True)
            st.dataframe(bu, use_container_width=True, hide_index=True,
                         column_config={
                             "PROMPTS": st.column_config.NumberColumn("Prompts"),
                             "AVG_LAT": st.column_config.NumberColumn("Avg Lat (s)", format="%.2f"),
                             "SUCCESS": st.column_config.NumberColumn("Success %", format="%.1f"),
                             "TOKENS":  st.column_config.NumberColumn("Tokens"),
                         })

        with t_models:
            st.caption("Prompt distribution across AI models. For credit-cost analysis per model, see the **Model Intelligence** page.")
            _sec("Model Distribution")
            bm = (df.groupby("MODEL")
                    .agg(PROMPTS=("PROMPT","count"),
                         AVG_LAT=("LATENCY_S","mean"),
                         TOKENS=("TOTAL_TOKENS","sum"))
                    .reset_index().sort_values("PROMPTS", ascending=False))
            c = _hbar(bm, "PROMPTS", "MODEL", height=max(150, len(bm)*40),
                      tooltip=["MODEL:N","PROMPTS:Q","AVG_LAT:Q","TOKENS:Q"])
            if c:
                st.altair_chart(c, use_container_width=True)
            st.dataframe(bm, use_container_width=True, hide_index=True)

        with t_prompts:
            _sec("Prompt Browser")
            st.caption("Showing the most recent 5,000 events. Use the user filter above to narrow results.")
            search = st.text_input("Search prompts or responses", placeholder="ALTER USER, credit limit…",
                                   key="obs_pi_search")
            show_response = st.checkbox("Show AI response", value=False, key="obs_pi_show_resp",
                                        help="Display the AI's reply alongside the user prompt. Null for Private Mode sessions.")
            disp = df[["TIMESTAMP","USER_NAME","ROLE_NAME","MODEL","PROMPT","RESPONSE",
                        "PRIVATE_MODE","LATENCY_S","STATUS","TOTAL_TOKENS"]].copy()
            if search.strip():
                mask = (disp["PROMPT"].str.contains(search.strip(), case=False, na=False) |
                        disp["RESPONSE"].str.contains(search.strip(), case=False, na=False))
                disp = disp[mask]
            st.caption(f"Showing {len(disp):,} prompts")
            for _, row in disp.head(50).iterrows():
                icon = "✓" if row["STATUS"] == "SUCCESS" else "✗"
                pm_flag = " 🔒" if row.get("PRIVATE_MODE") else ""
                with st.expander(f"{icon} {row['TIMESTAMP'].strftime('%Y-%m-%d %H:%M')} · {row['USER_NAME']} · {row['MODEL']} · {row.get('ENTRYPOINT') or '—'} · {row['LATENCY_S']}s{pm_flag}"):
                    st.markdown("**Prompt:**")
                    st.markdown(row["PROMPT"] or "_Not captured_")
                    if show_response:
                        st.markdown("**AI Response:**")
                        if row.get("PRIVATE_MODE"):
                            st.caption("_Private Mode — response not logged_")
                        else:
                            resp = row.get("RESPONSE") or ""
                            st.markdown(resp[:2000] + ("…" if len(resp) > 2000 else "") if resp else "_Not yet loaded — run SP_CC_CLASSIFY_PROMPTS to populate_")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Status", row["STATUS"])
                    c2.metric("Latency", f"{row['LATENCY_S']}s")
                    c3.metric("Tokens", int(row["TOTAL_TOKENS"]) if pd.notna(row["TOTAL_TOKENS"]) and row["TOTAL_TOKENS"] else "N/A")

            st.divider()
            with st.expander("🚩 Sensitive Content Detection", expanded=False):
                st.caption("In-memory scan — no additional SQL.")
                kws = st.multiselect("Keywords", _SENSITIVE,
                                     default=["password","api_key","credit_card","ssn"],
                                     key="obs_pi_kws")
                custom = st.text_input("Custom keyword", key="obs_pi_custom")
                all_kws = kws + ([custom.strip().lower()] if custom.strip() else [])
                if all_kws:
                    pat = "|".join(re.escape(k) for k in all_kws)
                    flagged = df[df["PROMPT"].str.contains(pat, case=False, na=False)]
                    if flagged.empty:
                        st.success(f"✓ No matches for: {', '.join(all_kws)}")
                    else:
                        st.warning(f"⚠ {len(flagged)} prompt(s) matched")
                        st.dataframe(
                            flagged[["TIMESTAMP","USER_NAME","ROLE_NAME","MODEL","PROMPT"]]
                                .assign(PROMPT=flagged["PROMPT"].str[:150]),
                            use_container_width=True, hide_index=True)

        with t_sessions:
            st.caption("Conversation threads grouped by SESSION_ID. Depth ≥ 5 may indicate extended debugging sessions or automation. Sessions with no SESSION_ID appear individually.")
            _sec("Conversation Sessions")
            sdf = _load_sessions(session, active_days)
            if sdf.empty:
                st.info("No session data.")
            else:
                sdf.columns = [c.upper() for c in sdf.columns]
                avg_depth = sdf["PROMPT_COUNT"].mean()
                deep      = (sdf["PROMPT_COUNT"] >= 5).sum()
                # Surface split from ENTRYPOINT column
                ep_counts = sdf["ENTRYPOINT"].value_counts() if "ENTRYPOINT" in sdf.columns else pd.Series(dtype=int)
                cli_s  = int(ep_counts.get("CLI", 0))
                ss_s   = int(ep_counts.get("SNOWSIGHT", 0))
                dt_s   = int(ep_counts.get("DESKTOP", 0))
                # Count both NaN and empty string as unknown (UPPER(NULL) returns empty str)
                null_s = int((sdf["ENTRYPOINT"].isna() | (sdf["ENTRYPOINT"].fillna("") == "")).sum()) if "ENTRYPOINT" in sdf.columns else 0
                # Any other surface (e.g. SDK-TYPESCRIPT, sdk-python) — not hardcoded
                # Exclude known surfaces AND empty string (already counted in null_s)
                known  = {"CLI", "SNOWSIGHT", "DESKTOP", ""}
                ext_s  = int(ep_counts[~ep_counts.index.isin(known)].sum()) if not ep_counts.empty else 0

                sd1, sd2, sd3 = st.columns(3)
                sd1.metric("Sessions (last 100)", f"{len(sdf):,}",
                           help="Most recent 100 distinct conversation sessions.")
                sd2.metric("Avg Depth", f"{avg_depth:.1f} prompts/session",
                           help="Average number of prompts per session.")
                sd3.metric("Deep Sessions (≥5)", f"{int(deep):,}",
                           help="Sessions with 5 or more prompts.")

                # Surface split row — 5 buckets to handle all surfaces
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                sc1.metric("CLI Sessions",         f"{cli_s:,}",  help="Sessions via Cortex Code CLI / VS Code extension.")
                sc2.metric("Snowsight Sessions",   f"{ss_s:,}",   help="Sessions via Snowsight browser IDE.")
                sc3.metric("Desktop Sessions",     f"{dt_s:,}",   help="Sessions via Snowflake Desktop app.")
                sc4.metric("SDK / Extensions",     f"{ext_s:,}",  help="Sessions from other surfaces (e.g. SDK-TYPESCRIPT, sdk-python). Check Entrypoints tab for full breakdown.")
                sc5.metric("Surface Unknown",      f"{null_s:,}", help="Sessions where ENTRYPOINT was null — re-run Phase C + D2 to backfill.")
                st.dataframe(sdf, use_container_width=True, hide_index=True,
                             column_config={
                                 "SESSION_ID":    st.column_config.TextColumn("Session ID", width="medium"),
                                 "USER_NAME":     st.column_config.TextColumn("User"),
                                 "ENTRYPOINT":    st.column_config.TextColumn("Surface",
                                                   help="CLI = terminal/VS Code · SNOWSIGHT = browser IDE · DESKTOP = Snowflake Desktop"),
                                 "SESSION_START": st.column_config.DatetimeColumn("Started"),
                                 "PROMPT_COUNT":  st.column_config.NumberColumn("Prompts"),
                                 "TOKENS":        st.column_config.NumberColumn("Tokens"),
                                 "SUCCESSES":     st.column_config.NumberColumn("Successes"),
                             })

        # ── Token Economics ───────────────────────────────────────────────────
        with t_token_econ:
            with st.expander("What do these token metrics mean?", expanded=False):
                st.markdown("""
| Metric | What it is | What to expect for Cortex Code |
|---|---|---|
| **Input tokens** | Fresh prompt tokens processed from scratch — question, conversation history, open files, tool definitions | Largest share (~50%). Cortex Code sends large context per step. |
| **Output tokens** | Tokens the LLM *generated* in its response | Very small (~0.1–2%). Each `Step-0` span is a planning step — output = short tool-selection decision, not a full response. Totally normal. |
| **Cache Read** | Tokens served from Snowflake's prompt cache — NOT re-processed, charged at ~10× lower rate | High is good (>20% = real credit savings). System prompts and skill context get cached after first call. |
| **Cache Write** | Tokens being written INTO the cache for the first time | Expected 10–15%. Cost slightly more upfront, pay off on reuse. |

**Cache Hit Rate** = `cache_read ÷ (cache_read + cache_write)` × 100. Standard hits ÷ (hits + misses). Fresh `input_tokens` are not cache-related and excluded.

**Data source:** `CC_PROMPT_EVENTS` — pre-computed nightly by `SP_CC_CLASSIFY_PROMPTS` from raw `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` (`CodingAgent.Step-0` spans, `token_count.*` attributes).
                """)
            te_df = _load_token_econ_daily(session, active_days)
            if te_df.empty:
                st.info("No token data. Run SP_CC_CLASSIFY_PROMPTS to populate CC_PROMPT_EVENTS.")
            else:
                total_t      = int(te_df["TOTAL_T"].sum())
                total_input  = int(te_df["INPUT_T"].sum())
                total_output = int(te_df["OUTPUT_T"].sum())
                total_cache_r = int(te_df["CACHE_READ_T"].sum())
                total_cache_w = int(te_df["CACHE_WRITE_T"].sum())
                # Correct: hits / (hits + misses) — input_tokens excluded (not cache-related)
                cache_hit    = round(total_cache_r / max(total_cache_r + total_cache_w, 1) * 100, 1)
                credits_saved = round(total_cache_r * 0.9 * 0.000025, 4)

                k1, k2, k3, k4, k5, k6 = st.columns(6)
                k1.metric("Total Tokens", _fmt_tokens(total_t),
                          help="Sum of all token types across all events in this period.")
                k2.metric("Input Tokens", _fmt_tokens(total_input),
                          help="Fresh prompt tokens sent to the LLM.")
                k3.metric("Output Tokens", _fmt_tokens(total_output),
                          help="Completion tokens returned by the LLM.")
                k4.metric("Cache Read Tokens", _fmt_tokens(total_cache_r),
                          help="Tokens served from prompt cache — these cost significantly less than fresh input.")
                k5.metric("Cache Hit Rate *(approx)*", f"{cache_hit}%",
                           help="cache_read ÷ (cache_read + cache_write). Approximate — field semantics in AI_OBSERVABILITY_EVENTS may vary by account. Use as a directional signal.")
                k6.metric("Est. Credits Saved", f"{credits_saved:,.4f}",
                          help="Cache reads cost ~10x less than fresh input tokens. Savings = cache_read × (input_rate - cache_rate).")

                st.divider()
                _sec("Token Breakdown Over Time (Stacked Area)")
                te_long = te_df.melt(
                    id_vars=["EVENT_DATE"],
                    value_vars=["INPUT_T","OUTPUT_T","CACHE_READ_T","CACHE_WRITE_T"],
                    var_name="TOKEN_TYPE", value_name="TOKENS"
                )
                te_long["TOKEN_TYPE"] = te_long["TOKEN_TYPE"].map({
                    "INPUT_T":       "Input",
                    "OUTPUT_T":      "Output",
                    "CACHE_READ_T":  "Cache Read",
                    "CACHE_WRITE_T": "Cache Write",
                })
                te_long["EVENT_DATE"] = te_long["EVENT_DATE"].astype(str)
                type_order = ["Input", "Output", "Cache Read", "Cache Write"]
                color_scale = alt.Scale(
                    domain=type_order,
                    range=["#7dd3fc", "#6ee7b7", "#fcd34d", "#94a3b8"]
                )
                ch_area = (alt.Chart(te_long).mark_area(opacity=0.7)
                           .encode(
                               x=alt.X("EVENT_DATE:T", title=""),
                               y=alt.Y("TOKENS:Q", title="Tokens", stack="zero"),
                               color=alt.Color("TOKEN_TYPE:N", scale=color_scale,
                                               legend=alt.Legend(title="Token Type"),
                                               sort=type_order),
                               tooltip=["EVENT_DATE:T","TOKEN_TYPE:N",
                                        alt.Tooltip("TOKENS:Q", format=",")])
                           .properties(height=260)
                           .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_area, use_container_width=True)

        # ── Tool Intelligence ─────────────────────────────────────────────────
        with t_tool_intel:
            st.caption(
                "Tool calls are Snowflake-side actions Cortex Code invoked on behalf of users — "
                "SQL execution, Cortex Search, file reads, etc. "
                "Parsed from TOOLS_RAW on CC_PROMPT_EVENTS. Showing up to 5,000 most recent events."
            )
            tools_df = _load_tool_events(session, active_days)
            if tools_df.empty:
                st.info("No tool call data in CC_PROMPT_EVENTS for this period.")
            else:
                # Parse TOOLS_RAW JSON to individual tool names
                tool_rows = []
                session_ids_with_tools = set()
                for _, row in tools_df.iterrows():
                    try:
                        tools = json.loads(row["TOOLS_RAW"]) if isinstance(row["TOOLS_RAW"], str) else []
                        for t in tools:
                            tool_rows.append({"TOOL": t, "USER_NAME": row["USER_NAME"]})
                        if tools and pd.notna(row.get("SESSION_ID")):
                            session_ids_with_tools.add(row["SESSION_ID"])
                    except Exception:
                        pass

                if not tool_rows:
                    st.info("TOOLS_RAW present but could not parse any tool names.")
                else:
                    tool_frame = pd.DataFrame(tool_rows)
                    total_calls  = len(tool_frame)
                    unique_tools = tool_frame["TOOL"].nunique()
                    sessions_w   = len(session_ids_with_tools)

                    k1, k2, k3 = st.columns(3)
                    k1.metric("Total Tool Calls", f"{total_calls:,}",
                              help="Sum of all individual tool invocations parsed from TOOLS_RAW.")
                    k2.metric("Unique Tool Types", f"{unique_tools:,}",
                              help="Number of distinct tool names invoked.")
                    k3.metric("Sessions with Tools", f"{sessions_w:,}",
                              help="Distinct SESSION_IDs where at least one tool was called.")

                    st.divider()
                    _sec("Top 10 Tools by Call Count")
                    st.caption("Tools are Snowflake-side actions Cortex Code invoked on behalf of the user — SQL execution, Cortex Search, file reads, schema discovery, etc. The count shows how many times each tool was called across all sessions in this period.")
                    bt = (tool_frame.groupby("TOOL").size()
                            .reset_index(name="CALLS")
                            .sort_values("CALLS", ascending=False)
                            .head(10))
                    ch_tools = (alt.Chart(bt).mark_bar(color=_G)
                                .encode(
                                    x=alt.X("CALLS:Q", title="Call Count",
                                            axis=alt.Axis(orient="top")),
                                    y=alt.Y("TOOL:N", sort="-x", title="",
                                            axis=alt.Axis(labelLimit=300)),
                                    tooltip=["TOOL:N", alt.Tooltip("CALLS:Q", format=",")])
                                .properties(height=max(200, len(bt) * 40))
                                .configure_view(strokeWidth=0).configure(background=_BG))
                    st.altair_chart(ch_tools, use_container_width=True)

        # ── Entrypoints ───────────────────────────────────────────────────────
        with t_entrypoint:
            st.caption(
                "Entrypoint shows which surface (CLI, Snowsight IDE, Desktop app) the user was using. "
                "Avg Steps shows agent reasoning depth per session per surface. "
                "Data source: CC_PROMPT_EVENTS.ENTRYPOINT column."
            )
            ep_df = _load_entrypoints(session, active_days)
            if ep_df.empty:
                st.info("No entrypoint data. ENTRYPOINT column requires CC_PROMPT_EVENTS to be populated.")
            else:
                # Aggregate by entrypoint (sum across all days)
                ep_agg = (ep_df.groupby("ENTRYPOINT")
                          .agg(QUERIES=("QUERIES","sum"),
                               TOKENS=("TOKENS","sum"),
                               AVG_LATENCY_S=("AVG_LATENCY_S","mean"),
                               AVG_STEPS=("AVG_STEPS","mean"))
                          .round(2).reset_index())

                surfaces = ["CLI", "SNOWSIGHT", "DESKTOP"]
                cols = st.columns(len(surfaces))
                for col, surf in zip(cols, surfaces):
                    row = ep_agg[ep_agg["ENTRYPOINT"] == surf]
                    q = int(row["QUERIES"].iloc[0]) if not row.empty else 0
                    col.metric(surf, f"{q:,} queries",
                               help=f"Total prompts via {surf} in last {active_days} days.")

                st.divider()
                _sec("Queries by Entrypoint Over Time")
                ep_plot = ep_df.copy()
                ep_plot["EVENT_DATE"] = ep_plot["EVENT_DATE"].astype(str)
                ep_colors = {"CLI": _P, "SNOWSIGHT": _G, "DESKTOP": _W}
                ch_ep = (alt.Chart(ep_plot).mark_area(opacity=0.7)
                         .encode(
                             x=alt.X("EVENT_DATE:T", title=""),
                             y=alt.Y("QUERIES:Q", title="Queries", stack="zero"),
                             color=alt.Color("ENTRYPOINT:N",
                                 scale=alt.Scale(
                                     domain=list(ep_colors.keys()),
                                     range=list(ep_colors.values())),
                                 legend=alt.Legend(title="")),
                             tooltip=["EVENT_DATE:T","ENTRYPOINT:N",
                                      alt.Tooltip("QUERIES:Q", format=",")])
                         .properties(height=240)
                         .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_ep, use_container_width=True)

                _sec("Entrypoint Summary Table")
                st.caption("CLI = terminal/VS Code extension · Snowsight = browser IDE · Desktop = Snowflake Desktop app. "
                           "Rows only appear for surfaces where at least one prompt has been classified. "
                           "If CLI/Desktop/Snowsight rows are missing, no activity from that surface has been backfilled yet.")
                st.dataframe(ep_agg, use_container_width=True, hide_index=True,
                             column_config={
                                 "ENTRYPOINT":    st.column_config.TextColumn("Entrypoint"),
                                 "QUERIES":       st.column_config.NumberColumn("Queries",         format="%.0f"),
                                 "TOKENS":        st.column_config.NumberColumn("Tokens",          format="%.0f"),
                                 "AVG_LATENCY_S": st.column_config.NumberColumn("Avg Latency (s)", format="%.2f",
                                                   help="Mean LLM response time in seconds."),
                                 "AVG_STEPS":     st.column_config.NumberColumn("Avg Steps", format="%.1f",
                                                   help="Average agent reasoning steps per session. Higher = more complex interactions."),
                             })

        # ── Quality Scores ────────────────────────────────────────────────────
        with t_quality:
            st.warning(
                "⚗️ **Experimental — Custom Evaluation.** These scores are computed using the "
                "LLM judge model configured in **Settings → Alerting & Evaluation** "
                "(default: `llama3.1-70b`), via `SP_CC_EVALUATE_RESPONSES`. They are **not** "
                "Snowflake's built-in quality measurement. Use as a directional signal only — "
                "not an official assessment of Cortex Code output quality.",
                icon=None
            )
            st.caption(
                "AI response quality evaluated by a second LLM judge (custom). "
                "**Answer Relevance** — did the answer address the question? "
                "**Groundedness** — factually grounded without hallucination? "
                "**Coherence** — was the response logically structured? "
                "**Safety** — free of harmful content? All scores 0.0–1.0, higher is better."
            )
            _sec("Response Quality Scores")
            tbl_q = fq_table(session, TABLE_RESPONSE_QUALITY)
            uf_q = f"AND USER_NAME = '{escape_sql_literal(active_filter)}'" if active_filter else ""
            try:
                q_df = session.sql(f"""
                    SELECT
                        RESPONSE_DATE,
                        MODEL,
                        ROUND(AVG(ANSWER_RELEVANCE_SCORE), 3) AS AVG_ANSWER_RELEVANCE,
                        ROUND(AVG(GROUNDEDNESS_SCORE), 3)     AS AVG_GROUNDEDNESS,
                        ROUND(AVG(COHERENCE_SCORE), 3)        AS AVG_COHERENCE,
                        ROUND(AVG(SAFETY_SCORE), 3)           AS AVG_SAFETY,
                        COUNT(*) AS EVALUATED
                    FROM {tbl_q}
                    WHERE RESPONSE_DATE >= DATEADD('day', -{active_days}, CURRENT_DATE())
                    {uf_q}
                    GROUP BY 1, 2 ORDER BY 1 DESC
                """).to_pandas()
                q_df.columns = [c.upper() for c in q_df.columns]
            except Exception as e:
                q_df = pd.DataFrame()
                st.error(f"Could not load quality scores: {e}")

            if q_df.empty:
                st.info("No quality scores available for this period. "
                        "Go to **Model Intelligence → LLM-as-Judge Evaluation** to run the evaluation SP.")
            else:
                kq1, kq2, kq3, kq4 = st.columns(4)
                kq1.metric("Avg Answer Relevance", f"{q_df['AVG_ANSWER_RELEVANCE'].mean():.2f}",
                            help="1.0 = AI fully addressed the question.")
                kq2.metric("Avg Groundedness", f"{q_df['AVG_GROUNDEDNESS'].mean():.2f}",
                            help="1.0 = no hallucination detected.")
                kq3.metric("Avg Coherence", f"{q_df['AVG_COHERENCE'].mean():.2f}",
                            help="1.0 = response is logically structured.")
                kq4.metric("Avg Safety", f"{q_df['AVG_SAFETY'].mean():.2f}",
                            help="1.0 = no harmful or sensitive content detected.")
                st.dataframe(q_df, use_container_width=True, hide_index=True,
                             column_config={
                                 "RESPONSE_DATE":        st.column_config.DateColumn("Date"),
                                 "MODEL":                st.column_config.TextColumn("Model"),
                                 "AVG_ANSWER_RELEVANCE": st.column_config.NumberColumn("Answer Relevance", format="%.3f",
                                                          help="1.0 = fully answers the question"),
                                 "AVG_GROUNDEDNESS":     st.column_config.NumberColumn("Groundedness", format="%.3f",
                                                          help="1.0 = no hallucination detected"),
                                 "AVG_COHERENCE":        st.column_config.NumberColumn("Coherence", format="%.3f",
                                                          help="1.0 = logically structured"),
                                 "AVG_SAFETY":           st.column_config.NumberColumn("Safety", format="%.3f",
                                                          help="1.0 = no harmful content"),
                                 "EVALUATED":            st.column_config.NumberColumn("Count"),
                             })
                st.caption("For full model-level quality analysis → **Model Intelligence** page.")

        # ── Prompt Patterns ────────────────────────────────────────────────────
        with t_patterns:
            st.caption(
                "Prompt category clustering — automatically classified by `SP_CC_CLASSIFY_PROMPTS` "
                "using Snowflake Cortex `AI_CLASSIFY`. Categories run nightly on all uncategorised prompts. "
                "Actual per-prompt credit cost sourced from ACCOUNT_USAGE. "
                "System-injected prompts (Cortex CLI commands) are filtered out by default."
            )
            show_system = st.checkbox(
                "Show system prompts (cortex ctx / memory commands)",
                value=False, key="pat_show_system",
                help="When enabled, includes 'system_internal' category — "
                     "Cortex CLI task/memory commands that are not real user queries."
            )
            pat_dist, pat_trend = _load_prompt_patterns(session, active_days, show_system)

            if pat_dist.empty:
                st.info("No prompt categories yet. Run **Setup → Phase D → D2** "
                        "(or wait for the nightly SP) to classify prompt patterns.")
                st.markdown("""
**Categories used by AI_CLASSIFY:**

| Category | What it captures |
|---|---|
| `sql_data_engineering` | SQL queries, table design, pipelines, Snowflake-specific work |
| `agent_automation` | Building agents, tools, workflows, automation scripts |
| `code_review_debug` | Debugging, code review, explaining errors, fixing bugs |
| `data_migration` | Schema migration, ETL conversion, data movement |
| `data_modeling` | Data architecture, dbt models, star schema, entity relationships |
| `analytics_reporting` | Dashboards, KPIs, metrics queries, BI visualisations |
| `documentation` | Writing docs, explaining code, summarising, README |
| `general` | Everything else |
                """)
            else:
                # KPIs
                total_classified = int(pat_dist["PROMPTS"].sum())
                total_cost       = pat_dist["TOTAL_COST"].sum()
                top_cat          = pat_dist.iloc[0]["CATEGORY"].replace("_", " ").title()
                top_pct          = round(int(pat_dist.iloc[0]["PROMPTS"]) / max(total_classified, 1) * 100, 1)

                pk1, pk2, pk3, pk4 = st.columns(4)
                pk1.metric("Classified Prompts", f"{total_classified:,}",
                           help="Prompts with an assigned category in CC_PROMPT_EVENTS.")
                pk2.metric("Top Category", top_cat,
                           help=f"Most common prompt type — {top_pct}% of all classified prompts.")
                pk3.metric("Top Category Share", f"{top_pct}%")
                pk4.metric("Total Cost (Actual)", f"{total_cost:.4f} cr" if total_cost else "—",
                           help="Sum of PROMPT_COST_CREDITS from ACCOUNT_USAGE for this period.")

                st.divider()

                _sec("Category Distribution")
                pat_dist["CATEGORY_LABEL"] = pat_dist["CATEGORY"].str.replace("_", " ").str.title()
                ch_cat = (alt.Chart(pat_dist).mark_bar()
                          .encode(
                              x=alt.X("PROMPTS:Q", title="Prompts",
                                      axis=alt.Axis(orient="top")),
                              y=alt.Y("CATEGORY_LABEL:N", sort="-x", title="",
                                      axis=alt.Axis(labelLimit=260)),
                              color=alt.value(_P),
                              tooltip=["CATEGORY_LABEL:N", "PROMPTS:Q", "USERS:Q",
                                       alt.Tooltip("TOTAL_COST:Q", title="Cost (cr)", format=".4f")])
                          .properties(height=max(200, len(pat_dist) * 40))
                          .configure_view(strokeWidth=0).configure(background=_BG))
                st.altair_chart(ch_cat, use_container_width=True)

                if not pat_trend.empty:
                    _sec("Category Trend Over Time")
                    pat_trend["EVENT_DATE"]      = pat_trend["EVENT_DATE"].astype(str)
                    pat_trend["CATEGORY_LABEL"]  = pat_trend["CATEGORY"].str.replace("_", " ").str.title()
                    ch_trend = (alt.Chart(pat_trend).mark_area(opacity=0.7)
                                .encode(
                                    x=alt.X("EVENT_DATE:T", title=""),
                                    y=alt.Y("PROMPTS:Q", title="Prompts", stack="zero"),
                                    color=alt.Color("CATEGORY_LABEL:N", legend=alt.Legend(title="")),
                                    tooltip=["EVENT_DATE:T","CATEGORY_LABEL:N","PROMPTS:Q"])
                                .properties(height=220)
                                .configure_view(strokeWidth=0).configure(background=_BG))
                    st.altair_chart(ch_trend, use_container_width=True)

                # Cost by category
                cost_df = pat_dist[pat_dist["TOTAL_COST"].notna() & (pat_dist["TOTAL_COST"] > 0)]
                if not cost_df.empty:
                    _sec("Cost by Category (Actual Credits)")
                    st.caption("Actual credit cost per category from ACCOUNT_USAGE. "
                               "NULL means ACCOUNT_USAGE data not yet joined — re-run D2 after 45 min.")
                    ch_cost = (alt.Chart(cost_df).mark_bar()
                               .encode(
                                   x=alt.X("TOTAL_COST:Q", title="Credits",
                                           axis=alt.Axis(orient="top")),
                                   y=alt.Y("CATEGORY_LABEL:N", sort="-x", title="",
                                           axis=alt.Axis(labelLimit=260)),
                                   color=alt.value(_A),
                                   tooltip=["CATEGORY_LABEL:N",
                                            alt.Tooltip("TOTAL_COST:Q", title="Total Cost (cr)", format=".4f"),
                                            alt.Tooltip("AVG_COST:Q", title="Avg per Prompt (cr)", format=".6f"),
                                            "PROMPTS:Q"])
                               .properties(height=max(180, len(cost_df) * 40))
                               .configure_view(strokeWidth=0).configure(background=_BG))
                    st.altair_chart(ch_cost, use_container_width=True)

                # Summary table
                _sec("Category Summary Table")
                disp = pat_dist[["CATEGORY_LABEL","PROMPTS","USERS","TOTAL_COST","AVG_COST"]].copy()
                st.dataframe(disp, use_container_width=True, hide_index=True,
                             column_config={
                                 "CATEGORY_LABEL": st.column_config.TextColumn("Category"),
                                 "PROMPTS":        st.column_config.NumberColumn("Prompts",        format="%.0f"),
                                 "USERS":          st.column_config.NumberColumn("Users",           format="%.0f"),
                                 "TOTAL_COST":     st.column_config.NumberColumn("Total Cost (cr)", format="%.4f",
                                                    help="Actual credits from ACCOUNT_USAGE."),
                                 "AVG_COST":       st.column_config.NumberColumn("Avg/Prompt (cr)", format="%.6f"),
                             })

                # Sample prompts per category
                st.divider()
                _sec("Sample Prompts by Category")
                st.caption("3 random prompts per category — shows what users actually asked in each type.")
                for _, cat_row in pat_dist.iterrows():
                    cat   = cat_row["CATEGORY"]
                    label = str(cat).replace("_", " ").title()
                    cnt   = int(cat_row["PROMPTS"])
                    with st.expander(f"**{label}** — {cnt:,} prompts"):
                        samples = _load_category_samples(session, cat, active_days)
                        if samples.empty:
                            st.caption("No sample prompts available.")
                        else:
                            for _, sr in samples.iterrows():
                                ts    = str(sr.get("EVENT_TS",""))[:16]
                                cost  = f"{float(sr['PROMPT_COST_CREDITS']):.6f} cr" if sr.get("PROMPT_COST_CREDITS") else "—"
                                lat   = f"{int(sr.get('LATENCY_MS',0))/1000:.1f}s" if sr.get("LATENCY_MS") else "—"
                                st.markdown(f"**{ts}** · {sr.get('MODEL','')} · {lat} · {cost}")
                                st.markdown(f"> {str(sr.get('PROMPT',''))[:400]}")
                                st.divider()
