"""
Cortex Code Credit Manager - Usage Trends (Admin) v3
=====================================================
Altair-based. No borders on charts. Clean alignment.
Heatmap with scope selector (account/cohort/user).
"""

import streamlit as st
import pandas as pd
import altair as alt

from config import DATE_PRESETS, get_tz_offset
from utils import (
    get_daily_trend,
    get_daily_usage,
    get_hourly_usage,
    get_model_breakdown,
    get_session,
    get_top_users,
    get_usage_summary_metrics,
    list_roles,
    list_users,
)


def render(session):
    st.header("Usage Trends", help="Analyse credit consumption patterns across surfaces, cohorts, models, and users. Includes spike detection and actionable recommendations.")
    st.caption("Pre-aggregated data — refreshes every 30 minutes.")

    # --- Filters (single row, well-spaced) ---
    c1, c2, c3 = st.columns(3)
    with c1:
        period_label = st.selectbox("Period", list(DATE_PRESETS.keys()), index=2,
                                    key="trend_period", help="Time range for all charts.")
    with c2:
        roles = ["All"] + list_roles(session)
        cohort = st.selectbox("Cohort", roles, key="trend_cohort",
                              help="Filter to users within this role.")
    with c3:
        agg_mode = st.selectbox("Group by", ["Daily", "Weekly"], key="trend_agg",
                                help="Aggregation for trend chart.")

    days = DATE_PRESETS[period_label]
    cohort_filter = None if cohort == "All" else cohort

    st.divider()

    # --- KPI row ---
    m = get_usage_summary_metrics(session, days, cohort_filter)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Credits", f"{m['total_credits']:,.1f}", help="Sum of all credits consumed in this period.")
    c2.metric("Active Users", f"{m['active_users']}", help="Distinct users with at least 1 request.")
    c3.metric("Avg Credits/User", f"{m['avg_per_user']:.1f}", help="Total credits ÷ active users.")
    c4.metric("Total Requests", f"{m['total_requests']:,}", help="Number of LLM API calls.")

    st.divider()

    # --- Daily/Weekly trend (stacked area by surface) ---
    st.markdown("**Credit Consumption by Surface**")
    df = get_daily_trend(session, days, cohort_filter)
    if not df.empty and "USAGE_DATE" in df.columns:
        df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"])
        if agg_mode == "Weekly":
            df["PERIOD"] = df["USAGE_DATE"].dt.to_period("W").apply(lambda x: x.start_time)
            agg = df.groupby(["PERIOD", "SURFACE"])["CREDITS"].sum().reset_index()
            agg = agg.rename(columns={"PERIOD": "DATE"})
        else:
            agg = df.rename(columns={"USAGE_DATE": "DATE"})

        chart = alt.Chart(agg).mark_area(opacity=0.7).encode(
            x=alt.X('DATE:T', title=''),
            y=alt.Y('CREDITS:Q', title='Credits', stack='zero'),
            color=alt.Color('SURFACE:N', legend=alt.Legend(title="")),
        ).properties(height=280).configure_view(strokeWidth=0).configure(background='#0e1117')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No trend data available.")

    st.divider()

    # --- Top Users ---
    st.markdown("**Top Users by Total Credits**")
    top_n = st.selectbox("Show top", [10, 20, 50], index=0, key="top_n_select",
                         help="Number of top users to display.")
    top = get_top_users(session, days, cohort_filter, limit=top_n)
    if not top.empty:
        # Sort properly
        top = top.sort_values("CREDITS", ascending=False).head(top_n)
        chart = alt.Chart(top).mark_bar().encode(
            x=alt.X('CREDITS:Q', title='Total Credits'),
            y=alt.Y('USER_NAME:N', sort=alt.EncodingSortField(field='CREDITS', order='descending'), title=''),
        ).properties(height=max(250, len(top) * 24)).configure_view(strokeWidth=0).configure(background='#0e1117')
        st.altair_chart(chart, use_container_width=True)

        st.dataframe(top, use_container_width=True, hide_index=True,
                     column_config={
                         "USER_NAME": st.column_config.TextColumn("User"),
                         "CREDITS": st.column_config.NumberColumn("Credits", format="%.2f"),
                         "TOKENS": st.column_config.NumberColumn("Tokens", format="%d"),
                         "REQUESTS": st.column_config.NumberColumn("Requests", format="%d"),
                     })
    else:
        st.info("No user data for this period.")

    st.divider()

    # --- Model Breakdown ---
    st.markdown("**Credits by Model**")
    mdf = get_model_breakdown(session, days, cohort_filter)
    if not mdf.empty:
        mdf = mdf.sort_values("CREDITS", ascending=False)
        chart = alt.Chart(mdf).mark_bar().encode(
            x=alt.X('CREDITS:Q', title='Total Credits'),
            y=alt.Y('MODEL_NAME:N', sort=alt.EncodingSortField(field='CREDITS', order='descending'), title=''),
        ).properties(height=max(150, len(mdf) * 35)).configure_view(strokeWidth=0).configure(background='#0e1117')
        st.altair_chart(chart, use_container_width=True)

        if "TOKENS" in mdf.columns and "CREDITS" in mdf.columns:
            mdf_display = mdf.copy()
            mdf_display["TOKENS_PER_CREDIT"] = (mdf_display["TOKENS"] / mdf_display["CREDITS"]).round(0)
            st.dataframe(mdf_display[["MODEL_NAME", "CREDITS", "TOKENS", "TOKENS_PER_CREDIT"]].rename(
                columns={"MODEL_NAME": "Model", "CREDITS": "Credits",
                         "TOKENS": "Tokens", "TOKENS_PER_CREDIT": "Tokens/Credit"}
            ), use_container_width=True, hide_index=True)
    else:
        st.info("No model data for this period.")

    st.divider()

    # --- Scatter Plot: User Distribution by Cohort ---
    st.markdown("**User Distribution (Credits vs Requests)**")
    st.caption("Each dot = one user. Color = cohort role. See who's consuming most and where clusters form.")

    scatter_df = get_top_users(session, days, cohort_filter, limit=100)
    if not scatter_df.empty and "CREDITS" in scatter_df.columns and "REQUESTS" in scatter_df.columns:
        # Add cohort info if available
        try:
            from config import TABLE_USER_COHORT_RESOLVED, fq_table
            cohort_tbl = fq_table(session, TABLE_USER_COHORT_RESOLVED)
            cohort_df = session.sql(f"SELECT USER_NAME, COHORT_ROLE FROM {cohort_tbl}").to_pandas()
            if not cohort_df.empty:
                cohort_df.columns = [c.strip('"').upper() for c in cohort_df.columns]
                scatter_df = scatter_df.merge(cohort_df, on="USER_NAME", how="left")
                scatter_df["COHORT_ROLE"] = scatter_df["COHORT_ROLE"].fillna("Unassigned")
            else:
                scatter_df["COHORT_ROLE"] = "Unassigned"
        except Exception:
            scatter_df["COHORT_ROLE"] = "Unassigned"

        chart = alt.Chart(scatter_df).mark_circle(size=60, opacity=0.7).encode(
            x=alt.X('CREDITS:Q', title='Total Credits'),
            y=alt.Y('REQUESTS:Q', title='Total Requests'),
            color=alt.Color('COHORT_ROLE:N', legend=alt.Legend(title="Cohort")),
            tooltip=['USER_NAME', 'CREDITS', 'REQUESTS', 'COHORT_ROLE'],
        ).properties(height=350).configure_view(strokeWidth=0).configure(background='#0e1117')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Not enough data for scatter plot.")

    st.divider()

    # --- Heatmap with scope selector ---
    st.markdown("**Usage Heatmap**")

    hm_col1, hm_col2 = st.columns([1, 3])
    with hm_col1:
        heatmap_scope = st.radio(
            "Scope", ["Account (all users)", "By Cohort", "Single User"],
            key="heatmap_scope",
            help="Account: average across all users. Cohort: filter by role. User: one specific user."
        )

    hm_cohort = cohort_filter
    hm_user = None

    if heatmap_scope == "Single User":
        with hm_col2:
            all_users_df = list_users(session)
            if not all_users_df.empty:
                user_list = all_users_df["NAME"].dropna().tolist()[:100]
                hm_user = st.selectbox("Select user", user_list, key="heatmap_user",
                                       help="Show hourly pattern for this specific user.")

    hdf = get_hourly_usage(session, 7, hm_cohort, hm_user)

    if not hdf.empty and "USAGE_DATE" in hdf.columns:
        # Apply timezone offset to UTC hours
        user_tz = st.session_state.get("user_tz", "UTC")
        tz_offset = get_tz_offset(user_tz)

        hdf["LOCAL_HOUR"] = (hdf["USAGE_HOUR"] + tz_offset) % 24
        # Recalculate day-of-week after timezone shift (hour wrapping may shift the date)
        hdf["USAGE_DATE_DT"] = pd.to_datetime(hdf["USAGE_DATE"])
        hdf["LOCAL_DATETIME"] = hdf["USAGE_DATE_DT"] + pd.to_timedelta(hdf["USAGE_HOUR"], unit="h") + pd.to_timedelta(tz_offset, unit="h")
        hdf["DOW"] = hdf["LOCAL_DATETIME"].dt.strftime("%a")

        # Metric toggle
        hm_metric = st.radio(
            "Show", ["Credits", "Requests"], horizontal=True, key="heatmap_metric",
            help="Credits: cost intensity by hour. Requests: activity volume by hour (better for 'when do people work?')."
        )
        metric_col = "TOTAL_CREDITS" if hm_metric == "Credits" else "QUERY_COUNT"
        tz_label = f"Hour ({user_tz})" if tz_offset == 0 else f"Hour ({user_tz}, UTC{tz_offset:+d})"

        if heatmap_scope == "Single User" and hm_user:
            pivot = hdf.groupby(["DOW", "LOCAL_HOUR"])[metric_col].sum().reset_index()
            credit_label = f"Total {hm_metric} (7 days)"
        else:
            pivot = hdf.groupby(["DOW", "LOCAL_HOUR"])[metric_col].mean().reset_index()
            credit_label = f"Avg {hm_metric} per User per Hour"

        st.caption(f"**{credit_label}** — last 7 days — times shown in {user_tz}")
        st.caption("⚠️ Daily credit limits always reset at **midnight UTC**, regardless of timezone shown.")

        chart = alt.Chart(pivot).mark_rect().encode(
            x=alt.X('LOCAL_HOUR:O', title=tz_label),
            y=alt.Y('DOW:N', title='', sort=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]),
            color=alt.Color(f'{metric_col}:Q', scale=alt.Scale(scheme='orangered'), title=credit_label),
            tooltip=['DOW', alt.Tooltip('LOCAL_HOUR:O', title=tz_label),
                     alt.Tooltip(f'{metric_col}:Q', format='.2f', title=hm_metric)]
        ).properties(height=200).configure_view(strokeWidth=0).configure(background='#0e1117')
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No hourly data available for heatmap.")

    st.divider()

    # --- Intelligence: Spike Detection + Recommendations ---
    _render_intelligence(session, days, cohort_filter)


def _render_intelligence(session, days, cohort_filter):
    """Spike detection and usage recommendations."""
    st.markdown("**Usage Intelligence**")
    st.caption("Anomaly detection and recommendations based on usage patterns.")

    df = get_daily_usage(session, days=days, cohort_role=cohort_filter)
    if df.empty or "USAGE_DATE" not in df.columns:
        st.info("Not enough data for intelligence analysis.")
        return

    df["USAGE_DATE"] = pd.to_datetime(df["USAGE_DATE"])

    # Per-user daily totals
    user_daily = df.groupby(["USAGE_DATE", "USER_NAME"])["TOTAL_CREDITS"].sum().reset_index()

    # --- Spike Detection ---
    # Calculate per-user mean + 2 std dev threshold
    user_stats = user_daily.groupby("USER_NAME")["TOTAL_CREDITS"].agg(["mean", "std"]).reset_index()
    user_stats.columns = ["USER_NAME", "AVG_DAILY", "STD_DAILY"]
    user_stats["SPIKE_THRESHOLD"] = user_stats["AVG_DAILY"] + 2 * user_stats["STD_DAILY"].fillna(0)

    # Find spike days
    spikes = user_daily.merge(user_stats, on="USER_NAME")
    spikes = spikes[spikes["TOTAL_CREDITS"] > spikes["SPIKE_THRESHOLD"]]
    spikes = spikes[spikes["SPIKE_THRESHOLD"] > 0]  # Only meaningful where there's variance

    if not spikes.empty:
        st.markdown("**🔴 Detected Spikes** (usage > 2σ above user's average)")
        spike_display = spikes[["USAGE_DATE", "USER_NAME", "TOTAL_CREDITS", "AVG_DAILY"]].copy()
        spike_display["USAGE_DATE"] = spike_display["USAGE_DATE"].dt.strftime("%Y-%m-%d")
        spike_display = spike_display.rename(columns={
            "USAGE_DATE": "Date", "USER_NAME": "User",
            "TOTAL_CREDITS": "Credits (that day)", "AVG_DAILY": "User's Avg Daily"
        }).sort_values("Credits (that day)", ascending=False).head(10)
        st.dataframe(spike_display, use_container_width=True, hide_index=True,
                     column_config={
                         "Credits (that day)": st.column_config.NumberColumn(format="%.2f"),
                         "User's Avg Daily": st.column_config.NumberColumn(format="%.2f"),
                     })
    else:
        st.caption("No anomalous spikes detected in this period.")

    st.divider()

    # --- Recommendations: Users consistently at high usage ---
    st.markdown("**📈 Recommendations**")
    st.caption("Actionable insights based on usage patterns vs assigned limits.")

    if not user_stats.empty:
        # Categorize users
        p75 = user_stats["AVG_DAILY"].quantile(0.75)
        p95 = user_stats["AVG_DAILY"].quantile(0.95)

        high_users = user_stats[user_stats["AVG_DAILY"] > p75].copy()
        high_users = high_users.sort_values("AVG_DAILY", ascending=False).head(15)

        if not high_users.empty:
            def get_recommendation(row):
                avg = row["AVG_DAILY"]
                if avg > p95:
                    return "⚠️ Investigate — top 5% usage, verify use case is legitimate"
                elif avg > 50:
                    return "Review — high consumption, consider dedicated budget discussion"
                elif avg > 20:
                    return f"Consider setting limit to {int(avg + row['STD_DAILY'])} (avg + 1σ buffer)"
                else:
                    return "Within normal range for active user"

            high_users["RECOMMENDATION"] = high_users.apply(get_recommendation, axis=1)
            st.dataframe(
                high_users[["USER_NAME", "AVG_DAILY", "STD_DAILY", "RECOMMENDATION"]].rename(columns={
                    "USER_NAME": "User", "AVG_DAILY": "Avg Daily Credits",
                    "STD_DAILY": "Daily Variability (σ)", "RECOMMENDATION": "Recommendation"
                }),
                use_container_width=True, hide_index=True,
                column_config={
                    "Avg Daily Credits": st.column_config.NumberColumn(format="%.1f"),
                    "Daily Variability (σ)": st.column_config.NumberColumn(format="%.1f"),
                }
            )
        else:
            st.caption("No high-usage patterns detected yet.")
