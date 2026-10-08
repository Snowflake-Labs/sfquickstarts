"""
Cortex Code Credit Manager - Budget Forecast
==============================================
Projects future credit consumption using historical trends.
Helps answer: "What will Cortex Code cost next month/quarter?"
"""

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

from config import DATE_PRESETS, get_current_user
from utils import (
    get_daily_usage,
    get_session,
    get_usage_summary_metrics,
    list_roles,
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



def render(session):
    st.header("Budget Forecast", help="Project future Cortex Code credit spend using historical trends and linear regression.")
    st.caption("Project future credit consumption based on historical patterns.")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        lookback = st.selectbox("Historical basis", ["30 Days", "60 Days", "90 Days"],
                                index=0, key="forecast_lookback",
                                help="How much history to use for the projection.")
    with col2:
        roles = ["All (Account)"] + list_roles(session)
        cohort = st.selectbox("Cohort", roles, key="forecast_cohort",
                              help="Forecast for a specific cohort or the entire account.")

    lookback_days = {"30 Days": 30, "60 Days": 60, "90 Days": 90}[lookback]
    cohort_filter = None if cohort == "All (Account)" else cohort

    st.divider()

    # Get historical daily data
    df = get_daily_usage(session, days=lookback_days, cohort_role=cohort_filter)

    if df.empty or "USAGE_DATE" not in df.columns:
        st.warning("Not enough historical data for forecasting.")
        return

    df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"])
    daily_totals = df.groupby("USAGE_DATE")["TOTAL_CREDITS"].sum().reset_index()
    daily_totals = daily_totals.sort_values("USAGE_DATE")

    if len(daily_totals) < 7:
        st.warning("Need at least 7 days of data for a meaningful forecast.")
        return

    # --- Current Period Stats ---
    total_credits = daily_totals["TOTAL_CREDITS"].sum()
    avg_daily = daily_totals["TOTAL_CREDITS"].mean()
    days_in_data = len(daily_totals)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total (period)", f"{total_credits:,.0f} cr",
              help=f"Total credits consumed in the last {days_in_data} days.")
    c2.metric("Avg Daily", f"{avg_daily:,.1f} cr",
              help="Average daily credit consumption.")
    c3.metric("Projected (30d)", f"{avg_daily * 30:,.0f} cr",
              help="If current daily rate continues for 30 days.")
    c4.metric("Projected (90d)", f"{avg_daily * 90:,.0f} cr",
              help="If current daily rate continues for 90 days.")

    st.divider()

    # --- Trend with forecast line ---
    _sec("Historical + Projected Trend")

    # Simple linear regression for trend
    daily_totals["DAY_NUM"] = range(len(daily_totals))
    x = daily_totals["DAY_NUM"].values
    y = daily_totals["TOTAL_CREDITS"].values

    # Linear fit
    if len(x) > 1:
        slope, intercept = np.polyfit(x, y, 1)
    else:
        slope, intercept = 0, avg_daily

    # Generate forecast (next 30 days)
    last_date = daily_totals["USAGE_DATE"].max()
    forecast_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=30, freq="D")
    forecast_day_nums = range(len(daily_totals), len(daily_totals) + 30)
    forecast_values = [slope * d + intercept for d in forecast_day_nums]

    # Combine historical + forecast
    hist_df = daily_totals[["USAGE_DATE", "TOTAL_CREDITS"]].copy()
    hist_df["TYPE"] = "Historical"

    forecast_df = pd.DataFrame({
        "USAGE_DATE": forecast_dates,
        "TOTAL_CREDITS": forecast_values,
        "TYPE": "Forecast"
    })

    combined = pd.concat([hist_df, forecast_df], ignore_index=True)

    chart = alt.Chart(combined).mark_line(point=False).encode(
        x=alt.X('USAGE_DATE:T', title=''),
        y=alt.Y('TOTAL_CREDITS:Q', title='Credits / Day'),
        color=alt.Color('TYPE:N', legend=alt.Legend(title=""),
                       scale=alt.Scale(domain=["Historical", "Forecast"],
                                      range=["#388bfd", "#f97316"])),
        strokeDash=alt.StrokeDash('TYPE:N',
                                  scale=alt.Scale(domain=["Historical", "Forecast"],
                                                 range=[[1, 0], [5, 3]])),
    ).properties(height=300).configure_view(strokeWidth=0).configure(background='#0e1117')
    st.altair_chart(chart, use_container_width=True)

    # Trend direction
    if slope > 0.5:
        st.warning(f"📈 **Trending up** — consumption increasing by ~{slope:.1f} credits/day. "
                   f"At this rate, monthly cost will grow {slope * 30:.0f} credits/month.")
    elif slope < -0.5:
        st.info(f"📉 **Trending down** — consumption decreasing by ~{abs(slope):.1f} credits/day.")
    else:
        st.caption("➡️ **Stable** — consumption is roughly flat.")

    st.divider()

    # --- Budget Table ---
    _sec("Budget Projections")
    projections = []
    for period, days_ahead in [("Next 7 Days", 7), ("Next 30 Days", 30), ("Next Quarter", 90)]:
        # Use trend-adjusted projection
        future_day_nums = range(len(daily_totals), len(daily_totals) + days_ahead)
        projected = sum(slope * d + intercept for d in future_day_nums)
        # Also show flat projection for comparison
        flat = avg_daily * days_ahead
        projections.append({
            "Period": period,
            "Trend-Adjusted": f"{projected:,.0f} credits",
            "Flat (avg × days)": f"{flat:,.0f} credits",
            "Growth vs Flat": f"{((projected - flat) / flat * 100):+.1f}%" if flat > 0 else "N/A",
        })

    st.dataframe(pd.DataFrame(projections), use_container_width=True, hide_index=True)

    st.divider()

    # --- Per-Cohort Breakdown ---
    if cohort_filter is None:
        _sec("Projected Spend by Cohort")
        st.caption("If cohort roles are configured, shows projected spend per team.")

        # Try to break down by cohort
        if "COHORT_ROLE" in df.columns:
            cohort_spend = df.groupby("COHORT_ROLE")["TOTAL_CREDITS"].sum().reset_index()
            cohort_spend = cohort_spend[cohort_spend["COHORT_ROLE"].notna()]
            if not cohort_spend.empty:
                cohort_spend["DAILY_AVG"] = cohort_spend["TOTAL_CREDITS"] / days_in_data
                cohort_spend["PROJECTED_30D"] = cohort_spend["DAILY_AVG"] * 30
                cohort_spend = cohort_spend.sort_values("PROJECTED_30D", ascending=False)

                chart = alt.Chart(cohort_spend).mark_bar().encode(
                    x=alt.X('PROJECTED_30D:Q', title='Projected 30-Day Credits'),
                    y=alt.Y('COHORT_ROLE:N', sort=alt.EncodingSortField(field='PROJECTED_30D', order='descending'), title=''),
                ).properties(height=max(150, len(cohort_spend) * 30)).configure_view(strokeWidth=0).configure(background='#0e1117')
                st.altair_chart(chart, use_container_width=True)

                st.dataframe(cohort_spend[["COHORT_ROLE", "TOTAL_CREDITS", "DAILY_AVG", "PROJECTED_30D"]].rename(
                    columns={"COHORT_ROLE": "Cohort", "TOTAL_CREDITS": f"Actual ({days_in_data}d)",
                             "DAILY_AVG": "Daily Avg", "PROJECTED_30D": "Projected 30d"}
                ), use_container_width=True, hide_index=True,
                    column_config={
                        f"Actual ({days_in_data}d)": st.column_config.NumberColumn(format="%.0f"),
                        "Daily Avg": st.column_config.NumberColumn(format="%.1f"),
                        "Projected 30d": st.column_config.NumberColumn(format="%.0f"),
                    })
