"""
CoCo Control Hub — Cost Attribution
=====================================
Per-prompt and per-session credit costs via ACCOUNT_USAGE join.
Also shows cohort-level cost vs limit and surface breakdown.
Loaded on demand — no SQL fires on page init.
"""

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_CREDIT_CONFIG,
    TABLE_USAGE_DAILY,
    TABLE_USER_COHORT_RESOLVED,
    escape_sql_literal,
    fq_table,
)
from utils import get_app_setting, get_session

_BG  = "#0e1117"
_P   = "#7dd3fc"   # sky-300   (muted)
_G   = "#6ee7b7"   # emerald-300 (muted)
_O   = "#fcd34d"   # amber-300 (muted, was #F0A500)
_R   = "#fca5a5"   # rose-300  (muted)

_COST_CSS = """
<style>
.cost-card{background:rgba(240,165,0,0.06);border-left:3px solid #F0A500;
  border-radius:4px;padding:0.5rem 0.8rem;margin-bottom:0.6rem}
.cost-card h4{margin:0;font-size:0.9rem;font-weight:600;color:#F0A500}
</style>
"""

_COST_QUERY = """
SELECT
    obs.TIMESTAMP,
    obs.RESOURCE_ATTRIBUTES['snow.user.name']::STRING                                       AS USER_NAME,
    obs.RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.model']::STRING             AS MODEL,
    obs.RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.request_id']::STRING        AS REQUEST_ID,
    obs.TRACE['trace_id']::STRING                                                            AS SESSION_ID,
    TRIM(REGEXP_REPLACE(
        obs.RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.query']::STRING,
        '<system-reminder>[\\\\s\\\\S]*?</system-reminder>\\\\s*', '', 1, 0, 's'
    ))                                                                                        AS CLEAN_PROMPT,
    usage.TOKEN_CREDITS,
    usage.SURFACE
FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS obs
JOIN (
    SELECT REQUEST_ID, TOKEN_CREDITS, 'CLI' AS SURFACE
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY
    WHERE USAGE_TIME >= DATEADD('day', -{days}, CURRENT_TIMESTAMP())
    UNION ALL
    SELECT REQUEST_ID, TOKEN_CREDITS, 'SNOWSIGHT' AS SURFACE
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY
    WHERE USAGE_TIME >= DATEADD('day', -{days}, CURRENT_TIMESTAMP())
) usage
    ON obs.RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.request_id']::STRING
       = usage.REQUEST_ID
WHERE obs.RECORD_TYPE = 'SPAN'
  AND obs.RECORD:name::STRING = 'CodingAgent.Step-0'
  AND obs.TIMESTAMP >= DATEADD('day', -{days}, CURRENT_TIMESTAMP())
{user_filter}
ORDER BY TOKEN_CREDITS DESC
LIMIT 2000
"""


@st.cache_data(ttl=1800, show_spinner=False)
def _load_cost_data(_session, days: int, user_filter: str, usd_per_credit: float = 3.0):
    uf = (
        f"AND obs.RESOURCE_ATTRIBUTES['snow.user.name']::STRING = '{escape_sql_literal(user_filter)}'"
        if user_filter else ""
    )
    try:
        df = _session.sql(_COST_QUERY.format(days=days, user_filter=uf)).to_pandas()
    except Exception as e:
        return pd.DataFrame(), str(e)
    if df.empty:
        return df, None
    df.columns = [c.upper() for c in df.columns]
    df["TIMESTAMP"]     = pd.to_datetime(df["TIMESTAMP"])
    df["TOKEN_CREDITS"]  = pd.to_numeric(df["TOKEN_CREDITS"], errors="coerce").fillna(0)
    df["EST_USD"]        = (df["TOKEN_CREDITS"] * usd_per_credit).round(4)
    df["PROMPT_PREVIEW"] = df["CLEAN_PROMPT"].str[:100]
    return df, None


@st.cache_data(ttl=300, show_spinner=False)
def _load_cohort_cost(_session, days: int):
    """Per-cohort credits used vs configured limit from CC tables."""
    tbl_usage   = fq_table(_session, TABLE_USAGE_DAILY)
    tbl_cohort  = fq_table(_session, TABLE_USER_COHORT_RESOLVED)
    tbl_config  = fq_table(_session, TABLE_CREDIT_CONFIG)
    try:
        df = _session.sql(f"""
            SELECT
                COALESCE(ucr.COHORT_ROLE, 'Uncategorised') AS COHORT,
                COUNT(DISTINCT uds.USER_NAME)               AS USERS,
                ROUND(SUM(uds.TOTAL_CREDITS), 4)            AS CREDITS_USED,
                MAX(cc.CLI_DAILY_LIMIT)                     AS COHORT_CLI_LIMIT,
                MAX(cc.SNOWSIGHT_DAILY_LIMIT)               AS COHORT_SS_LIMIT,
                MAX(cc.DESKTOP_DAILY_LIMIT)                 AS COHORT_DT_LIMIT
            FROM {tbl_usage} uds
            LEFT JOIN {tbl_cohort} ucr
                ON ucr.USER_NAME = uds.USER_NAME
            LEFT JOIN {tbl_config} cc
                ON cc.ROLE_NAME = ucr.COHORT_ROLE
                AND cc.CONFIG_TYPE = 'COHORT'
                AND cc.IS_ACTIVE = TRUE
            WHERE uds.USAGE_DATE >= DATEADD('day', -{days}, CURRENT_DATE())
            GROUP BY 1
            ORDER BY CREDITS_USED DESC
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()


def _sec(title):
    """Section header — consistent muted slate across all pages."""
    st.markdown(
        '<div style="border-left:2px solid #475569;padding:0.25rem 0.65rem;'
        'margin:0.5rem 0 0.3rem 0;background:linear-gradient(90deg,'
        'rgba(71,85,105,0.08),transparent);border-radius:0 4px 4px 0">'
        f'<span style="font-size:0.85rem;font-weight:600;color:#94a3b8">{title}</span></div>',
        unsafe_allow_html=True)


def render(session):
    st.markdown(_COST_CSS, unsafe_allow_html=True)
    st.header("Cost Attribution",
              help="Per-prompt and per-session credit costs via ACCOUNT_USAGE join. "
                   "Separate from observability so cost queries don't slow down the main dashboard.")

    # ── Filters ──────────────────────────────────────────────────────────────
    if "cost_days" not in st.session_state:
        st.session_state["cost_days"] = 30
    if "cost_user" not in st.session_state:
        st.session_state["cost_user"] = ""

    with st.form("cost_filter_form"):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            days = st.selectbox("Lookback", [7, 14, 30, 60, 90],
                                index=[7,14,30,60,90].index(st.session_state["cost_days"]),
                                key="cost_days_input")
        with c2:
            user_inp = st.text_input("Filter by user", value=st.session_state["cost_user"],
                                     placeholder="Leave blank for all users")
        with c3:
            st.write("")
            submitted = st.form_submit_button("Apply", use_container_width=True)

    if submitted:
        st.session_state["cost_days"] = days
        st.session_state["cost_user"] = user_inp.strip().upper()

    active_days   = st.session_state["cost_days"]
    active_filter = st.session_state["cost_user"]

    # Read configured USD/credit rate (default $3.00 — update in Settings)
    usd_rate = float(get_app_setting(session, "USD_PER_CREDIT", "3.00"))

    # ── Cohort cost summary (CC tables — always visible, fast) ────────────────
    _sec("Cohort Credit Consumption")
    coh_df = _load_cohort_cost(session, active_days)
    if not coh_df.empty:
        cohort_chart = (
            alt.Chart(coh_df)
            .mark_bar()
            .encode(
                x=alt.X("CREDITS_USED:Q", title="Credits Used"),
                y=alt.Y("COHORT:N", sort="-x", title=""),
                color=alt.value(_O),
                tooltip=["COHORT:N","USERS:Q","CREDITS_USED:Q",
                         "COHORT_CLI_LIMIT:Q","COHORT_SS_LIMIT:Q"],
            )
            .properties(height=max(180, len(coh_df)*36))
            .configure_view(strokeWidth=0)
            .configure(background=_BG)
        )
        st.altair_chart(cohort_chart, use_container_width=True)
        st.dataframe(coh_df, use_container_width=True, hide_index=True,
                     column_config={
                         "COHORT":           st.column_config.TextColumn("Cohort"),
                         "USERS":            st.column_config.NumberColumn("Users"),
                         "CREDITS_USED":     st.column_config.NumberColumn("Credits Used", format="%.4f"),
                         "COHORT_CLI_LIMIT": st.column_config.NumberColumn("CLI Limit/day"),
                         "COHORT_SS_LIMIT":  st.column_config.NumberColumn("Snowsight Limit/day"),
                     })
    else:
        st.info("No cohort usage data for this period.")

    st.divider()

    # ── Per-prompt cost (ACCOUNT_USAGE JOIN — on demand) ──────────────────────
    _sec("Per-Prompt Cost Attribution (ACCOUNT_USAGE — 45min–2hr latency)")

    cost_key = f"cost_prompt_{active_days}_{active_filter}"

    if cost_key not in st.session_state:
        st.info("Joins ACCOUNT_USAGE.CORTEX_CODE_*_USAGE_HISTORY on REQUEST_ID. "
                "Loaded on demand — cached 30 min once loaded.")
        st.caption(
            f"Pricing reference: Input 2.75 cr/1M · Output 13.75 cr/1M · Cache 0.28 cr/1M "
            f"(Snowflake list rates — may vary by contract). "
            f"USD rate: **${usd_rate:.2f}/credit** — update in ⚙️ Settings."
        )
        if st.button("Load Prompt Cost Data", key="btn_load_prompt_cost", type="primary"):
            with st.spinner("Joining usage history…"):
                cdf, cerr = _load_cost_data(session, active_days, active_filter, usd_rate)
            st.session_state[cost_key] = (cdf, cerr)
            st.rerun()  # show data immediately
    else:
        cdf, cerr = st.session_state[cost_key]

        col_r, _ = st.columns([1, 5])
        with col_r:
            if st.button("↺ Refresh", key="btn_refresh_prompt_cost"):
                del st.session_state[cost_key]
                _load_cost_data.clear()

        if cerr:
            st.error(f"Could not load: {cerr}")
        elif cdf.empty:
            st.info("No matched cost data yet — ACCOUNT_USAGE may have up to 2hr lag.")
        else:
            total_credits = cdf["TOKEN_CREDITS"].sum()
            total_usd     = cdf["EST_USD"].sum()
            avg_credits   = cdf["TOKEN_CREDITS"].mean()
            top_model     = cdf.groupby("MODEL")["TOKEN_CREDITS"].sum().idxmax()

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Credits",    f"{total_credits:,.4f}")
            k2.metric("Est. USD",         f"${total_usd:,.2f}",
                      help=f"Credits × ${usd_rate:.2f} (configured USD/credit rate — update in Settings).")
            k3.metric("Avg Cost/Prompt",  f"{avg_credits:.5f}")
            k4.metric("Top Cost Model",   top_model)

            st.divider()

            # Top spenders
            _sec("Top Users by Credit Consumption")
            by_user = (cdf.groupby("USER_NAME")["TOKEN_CREDITS"]
                          .sum().reset_index()
                          .sort_values("TOKEN_CREDITS", ascending=False).head(15))
            ch = (
                alt.Chart(by_user).mark_bar()
                .encode(
                    x=alt.X("TOKEN_CREDITS:Q", title="Credits"),
                    y=alt.Y("USER_NAME:N", sort="-x", title=""),
                    color=alt.value(_O),
                    tooltip=["USER_NAME:N", alt.Tooltip("TOKEN_CREDITS:Q", format=".5f")],
                )
                .properties(height=max(200, len(by_user)*32))
                .configure_view(strokeWidth=0).configure(background=_BG)
            )
            st.altair_chart(ch, use_container_width=True)

            st.divider()

            # Per-prompt table
            _sec("Per-Prompt Detail")
            st.dataframe(
                cdf[["TIMESTAMP","USER_NAME","MODEL","SURFACE","TOKEN_CREDITS","EST_USD","PROMPT_PREVIEW"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "TIMESTAMP":      st.column_config.DatetimeColumn("Time"),
                    "TOKEN_CREDITS":  st.column_config.NumberColumn("Credits", format="%.5f"),
                    "EST_USD":        st.column_config.NumberColumn("Est. USD", format="$%.4f"),
                    "PROMPT_PREVIEW": st.column_config.TextColumn("Prompt", width="large"),
                }
            )

            st.divider()

            # Session rollup
            _sec("Session Cost Rollup")
            sess = (cdf.groupby(["SESSION_ID","USER_NAME"])
                       .agg(PROMPTS=("REQUEST_ID","count"),
                            TOTAL_CREDITS=("TOKEN_CREDITS","sum"),
                            EST_USD=("EST_USD","sum"))
                       .reset_index()
                       .sort_values("TOTAL_CREDITS", ascending=False).head(50))
            sess["TOTAL_CREDITS"] = sess["TOTAL_CREDITS"].round(5)
            sess["EST_USD"]        = sess["EST_USD"].round(4)
            threshold = sess["TOTAL_CREDITS"].quantile(0.90)
            sess["HIGH_COST"] = sess["TOTAL_CREDITS"] > threshold
            st.dataframe(sess, use_container_width=True, hide_index=True,
                         column_config={
                             "SESSION_ID":    st.column_config.TextColumn("Session ID", width="medium"),
                             "TOTAL_CREDITS": st.column_config.NumberColumn("Credits", format="%.5f"),
                             "EST_USD":       st.column_config.NumberColumn("Est. USD", format="$%.4f"),
                             "HIGH_COST":     st.column_config.CheckboxColumn("Top 10%?"),
                         })
