# Streamlit in Snowflake App - Cortex REST API Usage Monitor

Copy this code into a Streamlit in Snowflake notebook cell and run.

```python
# Import python packages
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# We can also use Snowpark for our analyses!
from snowflake.snowpark.context import get_active_session
session = get_active_session()

st.title("Cortex REST API Usage Monitor")
st.markdown("Dashboard for monitoring Cortex REST API token consumption")

# Query KPI totals
try:
    totals_df = session.sql("""
        SELECT 
            SUM(TOKENS) AS total_tokens,
            COUNT(*) AS total_requests,
            COUNT(DISTINCT MODEL_NAME) AS unique_models,
            COUNT(DISTINCT USER_ID) AS unique_users
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
        WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
    """).to_pandas()

    # KPI Row
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
        WHERE START_TIME >= DATEADD(day, -14, CURRENT_TIMESTAMP())
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
            WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
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
            WHERE c.START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
            GROUP BY 1
            ORDER BY 2 DESC
        """).to_pandas()
        st.dataframe(user_df, hide_index=True, use_container_width=True)

        # Daily breakdown table
        st.subheader("Daily Usage by Model")
        st.dataframe(df, hide_index=True, use_container_width=True)

    else:
        st.info("No Cortex REST API usage data found")

except Exception as e:
    st.warning("Unable to query Cortex usage data.")
    st.code(str(e))

# Refresh button
if st.button("Refresh Data"):
    st.rerun()
```
