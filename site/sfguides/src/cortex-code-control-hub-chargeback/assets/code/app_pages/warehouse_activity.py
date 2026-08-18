"""
CoCo Control Hub — CoCo Warehouse Activity
==========================================
The missing half of CoCo cost: the WAREHOUSE / SQL compute credits that Cortex
Code burns running queries on a user's behalf (LLM token credits already live in
Cost Attribution / Observability). CoCo auto-stamps every query with
query_tag:app = cortex_code_cli / _desktop / _snowsight / _sandbox / _api, and
QUERY_ATTRIBUTION_HISTORY.credits_attributed_compute gives the warehouse credits.

Fast path: KPIs + charts read the materialized CC_WAREHOUSE_USAGE_DAILY rollup
(refreshed daily by SP_CC_REFRESH_WAREHOUSE_USAGE). Heavy ACCOUNT_USAGE scans do
NOT run on page load. The per-user "what SQL did CoCo run" drill-down is the one
live query — and it's cheap because it's scoped to a single user + short window.
"""

import altair as alt
import pandas as pd
import streamlit as st

from config import (
    TABLE_WAREHOUSE_USAGE_DAILY, SP_REFRESH_WAREHOUSE_USAGE,
    fq_table, fq_sp, escape_sql_literal,
)
from utils import get_app_setting

_BG = "#0e1117"
_P  = "#7dd3fc"
_G  = "#6ee7b7"
_O  = "#fcd34d"


def _ensure_table(session):
    """Self-heal: create the rollup table if a live deployment predates the DDL."""
    try:
        session.sql(f"""
            CREATE TABLE IF NOT EXISTS {fq_table(session, TABLE_WAREHOUSE_USAGE_DAILY)} (
                USAGE_DATE        DATE          NOT NULL,
                USER_NAME         VARCHAR(255)  NOT NULL,
                SURFACE           VARCHAR(20)   NOT NULL,
                QUERY_COUNT       NUMBER(18,0)  DEFAULT 0,
                WAREHOUSE_CREDITS NUMBER(20,6)  DEFAULT 0,
                REFRESHED_AT      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
                PRIMARY KEY (USAGE_DATE, USER_NAME, SURFACE)
            )
        """).collect()
    except Exception:
        pass


@st.cache_data(ttl=300, show_spinner=False)
def _load_summary(_session, days: int) -> pd.DataFrame:
    tbl = fq_table(_session, TABLE_WAREHOUSE_USAGE_DAILY)
    try:
        df = _session.sql(f"""
            SELECT USAGE_DATE, USER_NAME, SURFACE, QUERY_COUNT, WAREHOUSE_CREDITS
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame(columns=["USAGE_DATE", "USER_NAME", "SURFACE",
                                     "QUERY_COUNT", "WAREHOUSE_CREDITS"])


@st.cache_data(ttl=300, show_spinner=False)
def _last_refreshed(_session) -> str:
    tbl = fq_table(_session, TABLE_WAREHOUSE_USAGE_DAILY)
    try:
        r = _session.sql(f"SELECT MAX(REFRESHED_AT) AS T FROM {tbl}").collect()
        return str(r[0]["T"]) if r and r[0]["T"] else "never"
    except Exception:
        return "never"


@st.cache_data(ttl=300, show_spinner=False)
def _user_list(_session, days: int) -> list:
    tbl = fq_table(_session, TABLE_WAREHOUSE_USAGE_DAILY)
    try:
        df = _session.sql(f"""
            SELECT USER_NAME, ROUND(SUM(WAREHOUSE_CREDITS),4) AS C
            FROM {tbl}
            WHERE USAGE_DATE >= DATEADD('day', -{int(days)}, CURRENT_DATE())
            GROUP BY 1 ORDER BY C DESC
        """).to_pandas()
        return df["USER_NAME"].tolist() if not df.empty else []
    except Exception:
        return []


@st.cache_data(ttl=180, show_spinner=True)
def _drilldown(_session, user: str, surface: str, days: int) -> pd.DataFrame:
    """SCOPED live query — the actual SQL CoCo ran for one user. Cheap because it
    filters to a single user + short window + the cortex_code query_tag, LIMIT 200."""
    surf_filter = ""
    smap = {"CLI": "cortex_code_cli", "DESKTOP": "cortex_code_desktop",
            "SNOWSIGHT": "cortex_code_snowsight", "SANDBOX": "cortex_code_sandbox",
            "API": "cortex_code_api"}
    if surface and surface != "All" and surface in smap:
        surf_filter = f"AND TRY_PARSE_JSON(qh.query_tag):app::string ILIKE '{smap[surface]}%'"
    try:
        df = _session.sql(f"""
            SELECT
                qh.START_TIME                                        AS STARTED,
                qh.USER_NAME                                         AS USER_NAME,
                TRY_PARSE_JSON(qh.query_tag):app::string             AS SURFACE_TAG,
                qh.WAREHOUSE_NAME                                    AS WAREHOUSE,
                qh.QUERY_TYPE                                        AS QUERY_TYPE,
                ROUND(qah.CREDITS_ATTRIBUTED_COMPUTE, 6)             AS WH_CREDITS,
                ROUND(qh.TOTAL_ELAPSED_TIME / 1000.0, 2)            AS SECONDS,
                LEFT(qh.QUERY_TEXT, 400)                             AS QUERY_TEXT
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
            JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY qah
                ON qah.QUERY_ID = qh.QUERY_ID
            WHERE qh.USER_NAME = '{escape_sql_literal(user)}'
              AND qh.START_TIME >= DATEADD('day', -{int(days)}, CURRENT_DATE())
              AND TRY_PARSE_JSON(qh.query_tag):app::string ILIKE 'cortex_code%'
              {surf_filter}
            ORDER BY qah.CREDITS_ATTRIBUTED_COMPUTE DESC
            LIMIT 200
        """).to_pandas()
        if not df.empty:
            df.columns = [c.upper() for c in df.columns]
        return df
    except Exception as e:
        st.session_state["_wh_drill_err"] = str(e)[:200]
        return pd.DataFrame()


def _kpi_row(df: pd.DataFrame, usd_rate: float):
    total_cr = float(df["WAREHOUSE_CREDITS"].sum()) if not df.empty else 0.0
    queries = int(df["QUERY_COUNT"].sum()) if not df.empty else 0
    users = df["USER_NAME"].nunique() if not df.empty else 0
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Warehouse Credits", f"{total_cr:,.4f}")
    k2.metric("Est. Cost (USD)", f"${total_cr * usd_rate:,.2f}")
    k3.metric("CoCo SQL Queries", f"{queries:,}")
    k4.metric("Active Users", f"{users:,}")


def render(session):
    st.header("CoCo Warehouse Activity",
              help="The warehouse / SQL compute credits Cortex Code burns running "
                   "queries on users' behalf — the compute half of CoCo cost, "
                   "alongside LLM tokens. Sourced from QUERY_ATTRIBUTION_HISTORY via "
                   "the cortex_code query tag.")

    _ensure_table(session)
    usd_rate = float(get_app_setting(session, "USD_PER_CREDIT", "2.00"))

    top = st.columns([1.2, 1, 2])
    with top[0]:
        days = st.selectbox("Lookback (days)", [7, 14, 30, 60, 90], index=2, key="wh_days")
    with top[1]:
        st.write(""); st.write("")
        if st.button("Refresh now", key="wh_refresh",
                     help="Re-scan QUERY_ATTRIBUTION_HISTORY for the trailing window "
                          "and re-run attribution. Normally runs daily via task."):
            try:
                with st.spinner("Refreshing warehouse credits + attribution…"):
                    r = session.sql(
                        f"CALL {fq_sp(session, SP_REFRESH_WAREHOUSE_USAGE)}({int(days)})"
                    ).collect()
                st.cache_data.clear()
                st.success(str(r[0][0]) if r else "Refreshed.")
            except Exception as e:
                st.error(f"Refresh failed: {str(e)[:180]}")
    with top[2]:
        st.write(""); st.write("")
        st.caption(f"Rollup last refreshed: {_last_refreshed(session)}  ·  "
                   f"rate ${usd_rate:.2f}/credit  ·  refreshes daily")

    df = _load_summary(session, days)
    if df.empty:
        st.info("No CoCo warehouse activity in this window yet. Click **Refresh now** to "
                "populate from QUERY_ATTRIBUTION_HISTORY, or wait for the daily task. "
                "(Sparse in low-usage accounts — richer in a shared/PM account.)")
        return

    _kpi_row(df, usd_rate)
    st.divider()

    # ── By surface + by user ────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Warehouse credits by surface**")
        by_s = (df.groupby("SURFACE", as_index=False)
                  .agg(CREDITS=("WAREHOUSE_CREDITS", "sum"),
                       QUERIES=("QUERY_COUNT", "sum")))
        by_s["CREDITS"] = by_s["CREDITS"].round(4)
        ch = (alt.Chart(by_s).mark_bar()
              .encode(x=alt.X("CREDITS:Q", title="Warehouse credits"),
                      y=alt.Y("SURFACE:N", sort="-x", title=""),
                      color=alt.value(_O),
                      tooltip=["SURFACE:N", alt.Tooltip("CREDITS:Q", format=".4f"),
                               alt.Tooltip("QUERIES:Q", format=",")])
              .properties(height=max(140, len(by_s) * 42))
              .configure_view(strokeWidth=0).configure(background=_BG))
        st.altair_chart(ch, use_container_width=True)
    with c2:
        st.markdown("**Top users by warehouse credits**")
        by_u = (df.groupby("USER_NAME", as_index=False)
                  .agg(CREDITS=("WAREHOUSE_CREDITS", "sum"))
                  .sort_values("CREDITS", ascending=False).head(15))
        by_u["CREDITS"] = by_u["CREDITS"].round(4)
        ch = (alt.Chart(by_u).mark_bar()
              .encode(x=alt.X("CREDITS:Q", title="Warehouse credits"),
                      y=alt.Y("USER_NAME:N", sort="-x", title=""),
                      color=alt.value(_G),
                      tooltip=["USER_NAME:N", alt.Tooltip("CREDITS:Q", format=".4f")])
              .properties(height=max(140, len(by_u) * 30))
              .configure_view(strokeWidth=0).configure(background=_BG))
        st.altair_chart(ch, use_container_width=True)

    # ── Daily trend ─────────────────────────────────────────────────────────
    st.markdown("**Daily warehouse credits**")
    by_d = (df.groupby("USAGE_DATE", as_index=False)
              .agg(CREDITS=("WAREHOUSE_CREDITS", "sum")))
    by_d["CREDITS"] = by_d["CREDITS"].round(4)
    ch = (alt.Chart(by_d).mark_area(opacity=0.5, line={"color": _P})
          .encode(x=alt.X("USAGE_DATE:T", title=""),
                  y=alt.Y("CREDITS:Q", title="Warehouse credits"),
                  color=alt.value(_P),
                  tooltip=["USAGE_DATE:T", alt.Tooltip("CREDITS:Q", format=".4f")])
          .properties(height=220)
          .configure_view(strokeWidth=0).configure(background=_BG))
    st.altair_chart(ch, use_container_width=True)

    st.divider()

    # ── Drill-down: what SQL did CoCo run for a user? ────────────────────────
    st.markdown("#### What SQL did CoCo run?")
    st.caption("Scoped live lookup — the individual queries Cortex Code executed for a "
               "user, with the warehouse credits each consumed. Ties a user's CoCo "
               "usage across surfaces directly to compute cost.")
    users = _user_list(session, days)
    if not users:
        st.info("No users with warehouse activity in this window.")
        return
    dc1, dc2 = st.columns([2, 1])
    with dc1:
        sel_user = st.selectbox("User", users, key="wh_drill_user")
    with dc2:
        sel_surface = st.selectbox("Surface", ["All", "CLI", "DESKTOP", "SNOWSIGHT",
                                               "SANDBOX", "API"], key="wh_drill_surface")

    detail = _drilldown(session, sel_user, sel_surface, days)
    if detail.empty:
        err = st.session_state.pop("_wh_drill_err", None)
        st.info(f"No CoCo SQL found for {sel_user} in this window."
                + (f"  ({err})" if err else ""))
        return

    d_cr = float(detail["WH_CREDITS"].sum())
    dk1, dk2, dk3 = st.columns(3)
    dk1.metric("Queries shown", f"{len(detail)}")
    dk2.metric("Warehouse credits", f"{d_cr:,.4f}")
    dk3.metric("Est. cost", f"${d_cr * usd_rate:,.2f}")

    st.dataframe(
        detail, use_container_width=True, hide_index=True,
        column_config={
            "STARTED":     st.column_config.DatetimeColumn("Started"),
            "USER_NAME":   st.column_config.TextColumn("User"),
            "SURFACE_TAG": st.column_config.TextColumn("Surface tag"),
            "WAREHOUSE":   st.column_config.TextColumn("Warehouse"),
            "QUERY_TYPE":  st.column_config.TextColumn("Type"),
            "WH_CREDITS":  st.column_config.NumberColumn("WH credits", format="%.6f"),
            "SECONDS":     st.column_config.NumberColumn("Secs", format="%.2f"),
            "QUERY_TEXT":  st.column_config.TextColumn("SQL (first 400 chars)", width="large"),
        })
    st.caption("Note: CoCo stamps a fixed per-surface query tag, so each SQL statement is "
               "attributed to the user + surface, not to an individual prompt (per-prompt "
               "linkage isn't reliable out-of-box).")
