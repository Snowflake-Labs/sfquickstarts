# Import python packages
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from snowflake.snowpark.context import get_active_session
session = get_active_session()

st.title("Cortex REST API Usage Monitor")
st.markdown("Dashboard for monitoring Cortex REST API token consumption")
# -----------------------------------------------------------------
# Overall KPIs
# -----------------------------------------------------------------
st.header("Overall Usage")

try:
    totals_df = session.sql("""
        SELECT 
            SUM(TOKENS) AS total_tokens,
            COUNT(*) AS total_requests,
            COUNT(DISTINCT MODEL_NAME) AS unique_models,
            COUNT(DISTINCT USER_ID) AS unique_users
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
        WHERE START_TIME >= '2025-02-13'
    """).to_pandas()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tokens", f"{totals_df['TOTAL_TOKENS'].iloc[0]:,.0f}")
    with col2:
        st.metric("Total Requests", f"{totals_df['TOTAL_REQUESTS'].iloc[0]:,.0f}")
    with col3:
        st.metric("Models Used", f"{totals_df['UNIQUE_MODELS'].iloc[0]:,.0f}")
    with col4:
        st.metric("Unique Users", f"{totals_df['UNIQUE_USERS'].iloc[0]:,.0f}")

    st.divider()

    # Query usage by model by date
    df = session.sql("""
        SELECT 
            DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
            MODEL_NAME,
            SUM(TOKENS) AS total_tokens,
            COUNT(*) AS request_count
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
        WHERE START_TIME >= '2025-02-13'
        GROUP BY 1, 2
        ORDER BY 1, 2
    """).to_pandas()

    if not df.empty:
        st.success(f"Found {len(df)} usage records")

        # Stacked bar chart
        st.subheader("Token Usage by Model (Stacked)")
        pivot_df = df.pivot(index='USAGE_DATE', columns='MODEL_NAME', values='TOTAL_TOKENS').fillna(0)
        st.bar_chart(pivot_df)

        # Seaborn grouped bar chart
        st.subheader("Token Usage by Model (Grouped)")
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.barplot(data=df, x='USAGE_DATE', y='TOTAL_TOKENS', hue='MODEL_NAME', palette='tab10', ax=ax)
        ax.set_xlabel('Date')
        ax.set_ylabel('Total Tokens')
        ax.legend(title='Model', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        st.divider()

        # Usage by model summary
        st.subheader("Usage by Model")
        model_df = session.sql("""
            SELECT 
                MODEL_NAME,
                SUM(TOKENS) AS total_tokens,
                COUNT(*) AS request_count
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
            WHERE START_TIME >= '2025-02-13'
            GROUP BY 1
            ORDER BY 2 DESC
        """).to_pandas()
        st.dataframe(model_df, hide_index=True, use_container_width=True)

        # Usage by user
        st.subheader("Usage by User")
        user_df = session.sql("""
            SELECT 
                u.NAME AS user_name,
                SUM(c.TOKENS) AS total_tokens,
                COUNT(*) AS request_count,
                COUNT(DISTINCT c.MODEL_NAME) AS models_used
            FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
            LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON c.USER_ID = u.USER_ID
            WHERE c.START_TIME >= '2025-02-13'
            GROUP BY 1
            ORDER BY 2 DESC
        """).to_pandas()
        st.dataframe(user_df, hide_index=True, use_container_width=True)

        # Usage by user per day
        st.subheader("Usage by User per Day")
        try:
            raw_user_model_df = session.sql("""
                SELECT 
                    DATE_TRUNC('day', c.START_TIME)::DATE AS usage_date,
                    COALESCE(u.NAME, 'Unknown') AS user_name,
                    c.MODEL_NAME,
                    SUM(c.TOKENS) AS model_total
                FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
                LEFT JOIN (
                    SELECT USER_ID, NAME
                    FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
                    QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_ID ORDER BY USER_ID) = 1
                ) u ON c.USER_ID = u.USER_ID
                WHERE c.START_TIME >= '2025-02-13'
                GROUP BY 1, 2, 3
                ORDER BY 1 DESC, 4 DESC
            """).to_pandas()

            if not raw_user_model_df.empty:
                model_breakdown = (
                    raw_user_model_df
                    .sort_values('MODEL_TOTAL', ascending=False)
                    .groupby(['USAGE_DATE', 'USER_NAME'], sort=False)
                    .apply(lambda g: ', '.join(f"{r['MODEL_NAME']}:{r['MODEL_TOTAL']}" for _, r in g.iterrows()))
                    .reset_index(name='model_tokens')
                )
                user_daily_summary = (
                    raw_user_model_df
                    .groupby(['USAGE_DATE', 'USER_NAME'])
                    .agg(total_tokens=('MODEL_TOTAL', 'sum'), models_used=('MODEL_NAME', 'nunique'))
                    .reset_index()
                    .merge(model_breakdown, on=['USAGE_DATE', 'USER_NAME'])
                    .sort_values(['USAGE_DATE', 'total_tokens'], ascending=[False, False])
                )
                st.dataframe(user_daily_summary, hide_index=True, use_container_width=True)
            else:
                st.info("No user daily data found since Feb 13, 2025")
        except Exception as e:
            st.warning("Unable to query user daily usage data.")
            st.code(str(e))

        # Daily breakdown table1
        st.subheader("Daily Usage by Model")
        st.dataframe(df, hide_index=True, use_container_width=True)

        st.divider()

        

    else:
        st.info("No Cortex REST API usage data found since Feb 13")

except Exception as e:
    st.warning("Unable to query Cortex usage data.")
    st.code(str(e))



# Refresh button
if st.button("Refresh Data"):
    st.rerun()
