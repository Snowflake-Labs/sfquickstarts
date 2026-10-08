import streamlit as st
import snowflake.connector
import pandas as pd
import os

st.set_page_config(page_title="Hybrid Table Monitor", layout="wide")
st.title("🔍 Hybrid Table Monitoring Dashboard")

conn = snowflake.connector.connect(
    connection_name=os.getenv("SNOWFLAKE_CONNECTION_NAME") or "default"
)

lookback = st.selectbox("Lookback Window", ["6 hours", "24 hours", "7 days"], index=1)
hours_map = {"6 hours": 6, "24 hours": 24, "7 days": 168}
hours = hours_map[lookback]

@st.cache_data(ttl=300)
def run_query(sql):
    cur = conn.cursor()
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    return pd.DataFrame(cur.fetchall(), columns=cols)

qps_df = run_query(f"""
    SELECT interval_start_time AS TS,
           SUM(calls) / 60.0 AS QPS
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
    GROUP BY interval_start_time ORDER BY TS
""")

lat_df = run_query(f"""
    SELECT interval_start_time AS TS,
           AVG(total_elapsed_time:"median"::FLOAT) AS P50,
           AVG(total_elapsed_time:"p90"::FLOAT) AS P90,
           AVG(total_elapsed_time:"p99"::FLOAT) AS P99
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
      AND calls > 0
    GROUP BY interval_start_time ORDER BY TS
""")

shapes_df = run_query(f"""
    SELECT LEFT(query_parameterized_hash, 12) AS HASH,
           ANY_VALUE(LEFT(query_text, 50)) AS QUERY_PREVIEW,
           SUM(calls) AS CALLS,
           ROUND(AVG(total_elapsed_time:"avg"::FLOAT), 1) AS AVG_MS
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
    GROUP BY query_parameterized_hash
    ORDER BY CALLS DESC LIMIT 8
""")

rw_df = run_query(f"""
    SELECT interval_start_time AS TS,
           SUM(CASE WHEN query_type = 'SELECT' THEN calls ELSE 0 END) AS READS,
           SUM(CASE WHEN query_type IN ('INSERT','UPDATE','DELETE','MERGE') THEN calls ELSE 0 END) AS WRITES
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
    GROUP BY interval_start_time ORDER BY TS
""")

err_df = run_query(f"""
    SELECT interval_start_time AS TS,
           ROUND(SUM(ARRAY_SIZE(errors))::FLOAT / NULLIF(SUM(calls), 0) * 100, 2) AS ERROR_PCT
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
    GROUP BY interval_start_time ORDER BY TS
""")

thr_df = run_query(f"""
    SELECT interval_start_time AS TS,
           SUM(hybrid_table_requests_throttled_count) AS THROTTLED
    FROM SNOWFLAKE.ACCOUNT_USAGE.AGGREGATE_QUERY_HISTORY
    WHERE interval_start_time > DATEADD(HOUR, -{hours}, CURRENT_TIMESTAMP())
    GROUP BY interval_start_time ORDER BY TS
""")

m1, m2, m3 = st.columns(3)
with m1:
    total = int(qps_df["QPS"].sum() * 60) if not qps_df.empty else 0
    st.metric("Total Queries", f"{total:,}")
with m2:
    throttled = int(thr_df["THROTTLED"].sum()) if not thr_df.empty else 0
    st.metric("Throttled Requests", f"{throttled:,}")
with m3:
    avg_err = float(err_df["ERROR_PCT"].mean()) if not err_df.empty else 0.0
    st.metric("Avg Error Rate", f"{avg_err:.2f}%")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Throughput (QPS)")
    if not qps_df.empty:
        chart_data = qps_df.set_index("TS")
        st.area_chart(chart_data["QPS"], color="#29B5E8")

with col2:
    st.subheader("Latency Percentiles (ms)")
    if not lat_df.empty:
        chart_data = lat_df.set_index("TS")
        st.line_chart(chart_data[["P50", "P90", "P99"]], color=["#29B5E8", "#FF6F61", "#FECB52"])

col3, col4 = st.columns(2)

with col3:
    st.subheader("Top Query Shapes")
    if not shapes_df.empty:
        st.dataframe(shapes_df, use_container_width=True, hide_index=True)

with col4:
    st.subheader("Read vs Write Mix")
    if not rw_df.empty:
        chart_data = rw_df.set_index("TS")
        st.area_chart(chart_data[["READS", "WRITES"]], color=["#29B5E8", "#FF6F61"])

col5, col6 = st.columns(2)

with col5:
    st.subheader("Error Rate (%)")
    if not err_df.empty:
        chart_data = err_df.set_index("TS")
        st.area_chart(chart_data["ERROR_PCT"], color="#FF6F61")

with col6:
    st.subheader("Throttled Requests")
    if not thr_df.empty:
        chart_data = thr_df.set_index("TS")
        st.bar_chart(chart_data["THROTTLED"], color="#FECB52")
