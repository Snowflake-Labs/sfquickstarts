import streamlit as st
import pandas as pd
import altair as alt
import os
import sys
import tempfile
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_report import generate_pdf

from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Claude vs Cortex Code Budget Skills", layout="wide")

session = get_active_session()

def run_query(sql):
    try:
        return session.sql(sql).to_pandas()
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

st.title("Budget Monitor Skills")

tab1, tab2 = st.tabs([
    "📄 Budget Monitor Claude Skill",
    "💰 Budget Monitor Cortex Skill"
])

# ============== TAB 1: Claude Skill — cortex-usage-report ==============
with tab1:
    st.subheader("Claude Skill: cortex-usage-report")
    st.caption("Source: `.claude/skills/cortex-usage-report/SKILL.md`")
    st.markdown("Generates usage reports with KPI totals, daily trends, and model breakdowns.")

    st.divider()

    days_back = st.slider("Lookback (days)", 7, 90, 30, key="claude_days")
    start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    if st.button("Run Usage Report Queries", type="primary", key="claude_run"):
        with st.spinner("Querying CORTEX_REST_API_USAGE_HISTORY..."):
            kpi_df = run_query(f"""
                SELECT 
                    SUM(TOKENS) as TOTAL_TOKENS,
                    COUNT(*) as TOTAL_REQUESTS,
                    COUNT(DISTINCT MODEL_NAME) as UNIQUE_MODELS
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= '{start_date}'
            """)

            daily_df = run_query(f"""
                SELECT 
                    DATE_TRUNC('day', START_TIME)::DATE AS USAGE_DATE,
                    SUM(TOKENS) as TOTAL_TOKENS,
                    COUNT(*) as REQUEST_COUNT
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= '{start_date}'
                GROUP BY 1 ORDER BY 1
            """)

            by_model_df = run_query(f"""
                SELECT 
                    MODEL_NAME,
                    SUM(TOKENS) as TOTAL_TOKENS,
                    COUNT(*) as REQUEST_COUNT
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= '{start_date}'
                GROUP BY 1 ORDER BY 2 DESC
            """)

            daily_model_df = run_query(f"""
                SELECT 
                    DATE_TRUNC('day', START_TIME)::DATE AS USAGE_DATE,
                    MODEL_NAME,
                    SUM(TOKENS) as TOTAL_TOKENS,
                    COUNT(*) as REQUEST_COUNT
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= '{start_date}'
                GROUP BY 1, 2 ORDER BY 1, 2
            """)

            st.session_state["claude_kpi"] = kpi_df
            st.session_state["claude_daily"] = daily_df
            st.session_state["claude_by_model"] = by_model_df
            st.session_state["claude_daily_model"] = daily_model_df

    if "claude_kpi" in st.session_state:
        kpi_df = st.session_state["claude_kpi"]
        daily_df = st.session_state["claude_daily"]
        by_model_df = st.session_state["claude_by_model"]
        daily_model_df = st.session_state["claude_daily_model"]

        if not kpi_df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Tokens", f"{int(kpi_df['TOTAL_TOKENS'].iloc[0] or 0):,}")
            col2.metric("Total Requests", f"{int(kpi_df['TOTAL_REQUESTS'].iloc[0] or 0):,}")
            col3.metric("Unique Models", f"{int(kpi_df['UNIQUE_MODELS'].iloc[0] or 0)}")

        st.divider()

        if not daily_df.empty:
            st.markdown("**Daily Token Usage**")
            chart = alt.Chart(daily_df).mark_bar().encode(
                x=alt.X("USAGE_DATE:T", title="Date"),
                y=alt.Y("TOTAL_TOKENS:Q", title="Tokens"),
                tooltip=["USAGE_DATE:T", "TOTAL_TOKENS:Q", "REQUEST_COUNT:Q"]
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

        if not by_model_df.empty:
            st.markdown("**Tokens by Model**")
            chart = alt.Chart(by_model_df).mark_bar().encode(
                x=alt.X("TOTAL_TOKENS:Q", title="Tokens"),
                y=alt.Y("MODEL_NAME:N", sort="-x", title="Model"),
                tooltip=["MODEL_NAME:N", "TOTAL_TOKENS:Q", "REQUEST_COUNT:Q"]
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

        if not daily_model_df.empty:
            st.markdown("**Daily Usage by Model**")
            st.dataframe(daily_model_df, use_container_width=True, hide_index=True)

    st.divider()
    cmd = st.text_input("Command", placeholder="Type /pdf to generate a downloadable PDF report", key="claude_cmd")
    if cmd.strip().lower() == "/pdf":
        if "claude_kpi" not in st.session_state:
            st.warning("Run the usage report queries first, then type `/pdf`.")
        else:
            kpi_df = st.session_state["claude_kpi"]
            daily_df = st.session_state["claude_daily"]
            by_model_df = st.session_state["claude_by_model"]
            daily_model_df = st.session_state["claude_daily_model"]
            with st.spinner("Generating PDF report..."):
                totals = {
                    'total_tokens': int(kpi_df['TOTAL_TOKENS'].iloc[0] or 0),
                    'total_requests': int(kpi_df['TOTAL_REQUESTS'].iloc[0] or 0),
                    'unique_models': int(kpi_df['UNIQUE_MODELS'].iloc[0] or 0),
                }
                daily_records = daily_df.rename(columns=str.lower).to_dict(orient='records')
                for r in daily_records:
                    if hasattr(r.get('usage_date'), 'isoformat'):
                        r['usage_date'] = r['usage_date'].isoformat()
                model_records = by_model_df.rename(columns=str.lower).to_dict(orient='records')
                dm_records = daily_model_df.rename(columns=str.lower).to_dict(orient='records')
                for r in dm_records:
                    if hasattr(r.get('usage_date'), 'isoformat'):
                        r['usage_date'] = r['usage_date'].isoformat()
                pdf_path = os.path.join(tempfile.gettempdir(), 'cortex_usage_report.pdf')
                generate_pdf(totals, daily_records, model_records, dm_records, start_date, pdf_path)
                with open(pdf_path, 'rb') as pf:
                    st.download_button(
                        "Download PDF Report",
                        pf.read(),
                        file_name='cortex_usage_report.pdf',
                        mime='application/pdf',
                        type='primary',
                        key='pdf_dl',
                    )
                st.success(f"PDF ready — {os.path.getsize(pdf_path):,} bytes")
    elif cmd.strip():
        st.info("Available commands: `/pdf` — generate a downloadable PDF report")

# ============== TAB 2: Cortex Code Skill — cortex-rest-api-budget ==============
with tab2:
    st.subheader("Cortex Code Skill: cortex-rest-api-budget")
    st.caption("Source: CoCo `.claude/skills/cortex-rest-api-budget/SKILL.md`")
    st.markdown("Proactive budget enforcement with thresholds, burn rate, projections, and alerts.")

    st.divider()

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        daily_budget = st.number_input("Daily Token Budget", value=1_000_000, step=100_000, key="daily_budget")
    with col_b2:
        weekly_budget = st.number_input("Weekly Token Budget", value=5_000_000, step=500_000, key="weekly_budget")
    with col_b3:
        alert_threshold = st.slider("Alert Threshold (%)", 50, 100, 80, key="alert_pct")

    if st.button("Run Budget Monitor Queries", type="primary", key="coco_run"):
        with st.spinner("Checking budget status..."):
            daily_status_df = run_query(f"""
                SELECT 
                    COALESCE(SUM(TOKENS), 0) AS TODAY_TOKENS,
                    {daily_budget} AS BUDGET,
                    ROUND(100.0 * COALESCE(SUM(TOKENS), 0) / {daily_budget}, 2) AS PCT_USED,
                    CASE 
                        WHEN COALESCE(SUM(TOKENS), 0) >= {daily_budget} THEN 'OVER BUDGET'
                        WHEN COALESCE(SUM(TOKENS), 0) >= {daily_budget} * {alert_threshold/100.0} THEN 'WARNING'
                        ELSE 'OK'
                    END AS STATUS
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE DATE(START_TIME) = CURRENT_DATE()
            """)

            weekly_status_df = run_query(f"""
                SELECT 
                    COALESCE(SUM(TOKENS), 0) AS WEEK_TOKENS,
                    {weekly_budget} AS BUDGET,
                    ROUND(100.0 * COALESCE(SUM(TOKENS), 0) / {weekly_budget}, 2) AS PCT_USED,
                    CASE 
                        WHEN COALESCE(SUM(TOKENS), 0) >= {weekly_budget} THEN 'OVER BUDGET'
                        WHEN COALESCE(SUM(TOKENS), 0) >= {weekly_budget} * {alert_threshold/100.0} THEN 'WARNING'
                        ELSE 'OK'
                    END AS STATUS
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= DATE_TRUNC('week', CURRENT_TIMESTAMP())
            """)

            burn_rate_df = run_query("""
                SELECT 
                    DATE_TRUNC('day', START_TIME)::DATE AS USAGE_DATE,
                    SUM(TOKENS) AS DAILY_TOKENS,
                    COUNT(*) AS DAILY_REQUESTS,
                    AVG(SUM(TOKENS)) OVER (ORDER BY DATE_TRUNC('day', START_TIME)::DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ROLLING_7D_AVG
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
                GROUP BY 1
                ORDER BY 1 DESC
            """)

            projected_df = run_query("""
                WITH daily_avg AS (
                    SELECT AVG(daily_tokens) AS AVG_DAILY_TOKENS
                    FROM (
                        SELECT SUM(TOKENS) AS daily_tokens
                        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                        WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
                        GROUP BY DATE(START_TIME)
                    )
                )
                SELECT 
                    ROUND(AVG_DAILY_TOKENS, 0) AS AVG_DAILY_TOKENS,
                    ROUND(AVG_DAILY_TOKENS * 30, 0) AS PROJECTED_MONTHLY_TOKENS,
                    ROUND(AVG_DAILY_TOKENS * 7, 0) AS PROJECTED_WEEKLY_TOKENS
                FROM daily_avg
            """)

            by_model_budget_df = run_query("""
                SELECT 
                    MODEL_NAME,
                    SUM(TOKENS) AS TOTAL_TOKENS,
                    COUNT(*) AS REQUEST_COUNT,
                    ROUND(100.0 * SUM(TOKENS) / SUM(SUM(TOKENS)) OVER (), 2) AS PCT_OF_TOTAL
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= DATE_TRUNC('month', CURRENT_TIMESTAMP())
                GROUP BY 1
                ORDER BY 2 DESC
            """)

            by_user_df = run_query("""
                SELECT 
                    USER_ID AS USER_NAME,
                    SUM(TOKENS) AS TOTAL_TOKENS,
                    ROUND(100.0 * SUM(TOKENS) / SUM(SUM(TOKENS)) OVER (), 2) AS PCT_OF_TOTAL
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
                WHERE START_TIME >= DATE_TRUNC('month', CURRENT_TIMESTAMP())
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT 10
            """)

            wow_df = run_query("""
                SELECT 
                    'This Week' AS PERIOD,
                    SUM(TOKENS) AS TOTAL_TOKENS,
                    COUNT(*) AS REQUEST_COUNT
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= DATE_TRUNC('week', CURRENT_TIMESTAMP())

                UNION ALL

                SELECT 
                    'Last Week' AS PERIOD,
                    SUM(TOKENS) AS TOTAL_TOKENS,
                    COUNT(*) AS REQUEST_COUNT
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
                WHERE START_TIME >= DATEADD(week, -1, DATE_TRUNC('week', CURRENT_TIMESTAMP()))
                  AND START_TIME < DATE_TRUNC('week', CURRENT_TIMESTAMP())
            """)

            alerts_df = run_query(f"""
                WITH daily_totals AS (
                    SELECT 
                        DATE(START_TIME) AS ALERT_DATE,
                        SUM(TOKENS) AS DAILY_TOKENS,
                        COUNT(*) AS DAILY_REQUESTS
                    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
                    WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
                    GROUP BY 1
                ),
                weekly_totals AS (
                    SELECT
                        DATE_TRUNC('week', START_TIME)::DATE AS WEEK_START,
                        SUM(TOKENS) AS WEEKLY_TOKENS
                    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
                    WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
                    GROUP BY 1
                )
                SELECT
                    d.ALERT_DATE,
                    d.DAILY_TOKENS,
                    d.DAILY_REQUESTS,
                    CASE
                        WHEN d.DAILY_TOKENS >= {daily_budget} THEN 'OVER BUDGET'
                        WHEN d.DAILY_TOKENS >= {daily_budget} * {alert_threshold/100.0} THEN 'WARNING'
                        ELSE 'OK'
                    END AS DAILY_STATUS,
                    w.WEEKLY_TOKENS,
                    CASE
                        WHEN w.WEEKLY_TOKENS >= {weekly_budget} THEN 'OVER BUDGET'
                        WHEN w.WEEKLY_TOKENS >= {weekly_budget} * {alert_threshold/100.0} THEN 'WARNING'
                        ELSE 'OK'
                    END AS WEEKLY_STATUS
                FROM daily_totals d
                LEFT JOIN weekly_totals w ON d.ALERT_DATE >= w.WEEK_START AND d.ALERT_DATE < DATEADD(day, 7, w.WEEK_START)
                WHERE d.DAILY_TOKENS >= {daily_budget} * {alert_threshold/100.0}
                   OR w.WEEKLY_TOKENS >= {weekly_budget} * {alert_threshold/100.0}
                ORDER BY d.ALERT_DATE DESC
            """)

            st.session_state["coco_daily_status"] = daily_status_df
            st.session_state["coco_weekly_status"] = weekly_status_df
            st.session_state["coco_burn_rate"] = burn_rate_df
            st.session_state["coco_projected"] = projected_df
            st.session_state["coco_by_model"] = by_model_budget_df
            st.session_state["coco_by_user"] = by_user_df
            st.session_state["coco_wow"] = wow_df
            st.session_state["coco_alerts"] = alerts_df

    if "coco_daily_status" in st.session_state:
        daily_status_df = st.session_state["coco_daily_status"]
        weekly_status_df = st.session_state["coco_weekly_status"]
        burn_rate_df = st.session_state["coco_burn_rate"]
        projected_df = st.session_state["coco_projected"]
        by_model_budget_df = st.session_state["coco_by_model"]
        by_user_df = st.session_state["coco_by_user"]
        wow_df = st.session_state["coco_wow"]
        alerts_df = st.session_state.get("coco_alerts", pd.DataFrame())

        st.markdown("### Budget Status")
        col1, col2 = st.columns(2)

        with col1:
            if not daily_status_df.empty:
                row = daily_status_df.iloc[0]
                status = row["STATUS"]
                pct = float(row["PCT_USED"] or 0)
                tokens = int(row["TODAY_TOKENS"] or 0)

                if status == "OVER BUDGET":
                    st.error(f"Daily: **OVER BUDGET** — {tokens:,} / {daily_budget:,} ({pct}%)")
                elif status == "WARNING":
                    st.warning(f"Daily: **WARNING** — {tokens:,} / {daily_budget:,} ({pct}%)")
                else:
                    st.success(f"Daily: **OK** — {tokens:,} / {daily_budget:,} ({pct}%)")
                st.progress(min(pct / 100, 1.0))

        with col2:
            if not weekly_status_df.empty:
                row = weekly_status_df.iloc[0]
                status = row["STATUS"]
                pct = float(row["PCT_USED"] or 0)
                tokens = int(row["WEEK_TOKENS"] or 0)

                if status == "OVER BUDGET":
                    st.error(f"Weekly: **OVER BUDGET** — {tokens:,} / {weekly_budget:,} ({pct}%)")
                elif status == "WARNING":
                    st.warning(f"Weekly: **WARNING** — {tokens:,} / {weekly_budget:,} ({pct}%)")
                else:
                    st.success(f"Weekly: **OK** — {tokens:,} / {weekly_budget:,} ({pct}%)")
                st.progress(min(pct / 100, 1.0))

        st.divider()

        if not projected_df.empty and not projected_df.iloc[0].isnull().all():
            st.markdown("### Projected Usage")
            row = projected_df.iloc[0]
            pc1, pc2, pc3 = st.columns(3)
            pc1.metric("Avg Daily Tokens", f"{int(row['AVG_DAILY_TOKENS'] or 0):,}")
            pc2.metric("Projected Weekly", f"{int(row['PROJECTED_WEEKLY_TOKENS'] or 0):,}")
            pc3.metric("Projected Monthly", f"{int(row['PROJECTED_MONTHLY_TOKENS'] or 0):,}")

        if not burn_rate_df.empty:
            st.markdown("### Burn Rate (30-Day with 7-Day Rolling Avg)")
            burn_sorted = burn_rate_df.sort_values("USAGE_DATE")
            base = alt.Chart(burn_sorted).encode(x=alt.X("USAGE_DATE:T", title="Date"))
            bars = base.mark_bar(opacity=0.5).encode(
                y=alt.Y("DAILY_TOKENS:Q", title="Tokens"),
                tooltip=["USAGE_DATE:T", "DAILY_TOKENS:Q", "DAILY_REQUESTS:Q"]
            )
            line = base.mark_line(color="red", strokeWidth=2).encode(
                y=alt.Y("ROLLING_7D_AVG:Q"),
                tooltip=["USAGE_DATE:T", "ROLLING_7D_AVG:Q"]
            )
            st.altair_chart(bars + line, use_container_width=True)

        st.divider()

        col_m, col_u = st.columns(2)

        with col_m:
            if not by_model_budget_df.empty:
                st.markdown("### Top Models (This Month)")
                st.dataframe(by_model_budget_df, use_container_width=True, hide_index=True)

        with col_u:
            if not by_user_df.empty:
                st.markdown("### Top Users (This Month)")
                st.dataframe(by_user_df, use_container_width=True, hide_index=True)

        st.divider()

        if not wow_df.empty:
            st.markdown("### Week-over-Week")
            wc1, wc2 = st.columns(2)
            for _, row in wow_df.iterrows():
                col = wc1 if row["PERIOD"] == "This Week" else wc2
                tok = int(row['TOTAL_TOKENS']) if pd.notna(row['TOTAL_TOKENS']) else 0
                req = int(row['REQUEST_COUNT']) if pd.notna(row['REQUEST_COUNT']) else 0
                col.metric(row["PERIOD"], f"{tok:,} tokens", f"{req:,} requests")

        st.divider()

        st.markdown("### Rolling Alerts (30 Days)")
        if not alerts_df.empty:
            def style_status(val):
                if val == 'OVER BUDGET':
                    return 'background-color: #FF4B4B; color: white; font-weight: bold'
                elif val == 'WARNING':
                    return 'background-color: #FFA500; color: white; font-weight: bold'
                return ''

            display_df = alerts_df.copy()
            for c in ['DAILY_TOKENS', 'DAILY_REQUESTS', 'WEEKLY_TOKENS']:
                if c in display_df.columns:
                    display_df[c] = display_df[c].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "—")
            styled = display_df.style.applymap(style_status, subset=[c for c in ['DAILY_STATUS', 'WEEKLY_STATUS'] if c in display_df.columns])
            st.dataframe(styled, use_container_width=True, hide_index=True)
            over_count = ((alerts_df.get('DAILY_STATUS', pd.Series()) == 'OVER BUDGET') | (alerts_df.get('WEEKLY_STATUS', pd.Series()) == 'OVER BUDGET')).sum()
            warn_count = len(alerts_df) - over_count
            st.caption(f"{len(alerts_df)} alert(s) in last 30 days — {over_count} over budget, {warn_count} warning")
        else:
            st.success("No budget alerts in the last 30 days")

    st.divider()
    coco_cmd = st.text_input(
        "Command",
        placeholder="Type /budget-status, /burn-rate, /alerts, or /budget-summary",
        key="coco_cmd"
    )
    if coco_cmd.strip().lower() in ["/budget-status", "/status"]:
        if "coco_daily_status" not in st.session_state:
            st.warning("Run budget monitor queries first.")
        else:
            ds = st.session_state["coco_daily_status"]
            ws = st.session_state["coco_weekly_status"]
            st.markdown("#### Budget Status Snapshot")
            if not ds.empty:
                r = ds.iloc[0]
                st.markdown(f"- **Daily**: {int(r['TODAY_TOKENS'] or 0):,} / {int(r['BUDGET'] or 0):,} tokens ({r['PCT_USED']}%) — **{r['STATUS']}**")
            if not ws.empty:
                r = ws.iloc[0]
                st.markdown(f"- **Weekly**: {int(r['WEEK_TOKENS'] or 0):,} / {int(r['BUDGET'] or 0):,} tokens ({r['PCT_USED']}%) — **{r['STATUS']}**")

    elif coco_cmd.strip().lower() in ["/burn-rate", "/burn"]:
        if "coco_burn_rate" not in st.session_state:
            st.warning("Run budget monitor queries first.")
        else:
            br = st.session_state["coco_burn_rate"]
            pr = st.session_state.get("coco_projected", pd.DataFrame())
            st.markdown("#### Burn Rate Summary")
            if not br.empty:
                latest = br.iloc[0]
                st.markdown(f"- **Latest daily**: {int(latest['DAILY_TOKENS'] or 0):,} tokens ({int(latest['DAILY_REQUESTS'] or 0):,} requests)")
                st.markdown(f"- **7-day rolling avg**: {int(latest['ROLLING_7D_AVG'] or 0):,} tokens/day")
            if not pr.empty and not pr.iloc[0].isnull().all():
                r = pr.iloc[0]
                st.markdown(f"- **Projected weekly**: {int(r['PROJECTED_WEEKLY_TOKENS'] or 0):,} tokens")
                st.markdown(f"- **Projected monthly**: {int(r['PROJECTED_MONTHLY_TOKENS'] or 0):,} tokens")

    elif coco_cmd.strip().lower() in ["/alerts", "/rolling-alerts"]:
        if "coco_alerts" not in st.session_state:
            st.warning("Run budget monitor queries first.")
        else:
            al = st.session_state["coco_alerts"]
            st.markdown("#### Rolling Alerts (30 Days)")
            if not al.empty:
                over = ((al.get('DAILY_STATUS', pd.Series()) == 'OVER BUDGET') | (al.get('WEEKLY_STATUS', pd.Series()) == 'OVER BUDGET')).sum()
                st.markdown(f"**{len(al)} alert(s)** — {over} over budget, {len(al) - over} warning")
                st.dataframe(al, use_container_width=True, hide_index=True)
            else:
                st.success("No budget alerts in the last 30 days.")

    elif coco_cmd.strip().lower() in ["/budget-summary", "/summary"]:
        if "coco_daily_status" not in st.session_state:
            st.warning("Run budget monitor queries first.")
        else:
            st.markdown("#### Budget Summary")
            ds = st.session_state["coco_daily_status"]
            ws = st.session_state["coco_weekly_status"]
            pr = st.session_state.get("coco_projected", pd.DataFrame())
            br = st.session_state["coco_burn_rate"]
            al = st.session_state.get("coco_alerts", pd.DataFrame())
            if not ds.empty:
                r = ds.iloc[0]
                st.markdown(f"**Daily**: {int(r['TODAY_TOKENS'] or 0):,} / {int(r['BUDGET'] or 0):,} ({r['PCT_USED']}%) — {r['STATUS']}")
            if not ws.empty:
                r = ws.iloc[0]
                st.markdown(f"**Weekly**: {int(r['WEEK_TOKENS'] or 0):,} / {int(r['BUDGET'] or 0):,} ({r['PCT_USED']}%) — {r['STATUS']}")
            if not pr.empty and not pr.iloc[0].isnull().all():
                r = pr.iloc[0]
                st.markdown(f"**Projected monthly**: {int(r['PROJECTED_MONTHLY_TOKENS'] or 0):,} tokens")
            if not br.empty:
                st.markdown(f"**7-day avg burn rate**: {int(br.iloc[0]['ROLLING_7D_AVG'] or 0):,} tokens/day")
            if not al.empty:
                st.markdown(f"**Alerts (30d)**: {len(al)} breach(es)")
            else:
                st.markdown("**Alerts (30d)**: None")

    elif coco_cmd.strip():
        st.info("Available commands: `/budget-status`, `/burn-rate`, `/alerts`, `/budget-summary`")
