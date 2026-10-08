import streamlit as st
import pandas as pd
import altair as alt
import json
import _snowflake
from datetime import date, timedelta

st.set_page_config(
    page_title="Cortex AI Cost Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    [data-testid="stMetric"],
    [data-testid="metric-container"] {
        background-color: #ffffff !important;
        padding: 15px 20px !important;
        border-radius: 10px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    [data-testid="stMetric"] > div {
        width: 100% !important;
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 0.65rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    [data-testid="stMetricValue"] {
        color: #1f2937 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #10b981 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricDelta"] svg {
        display: none !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f3f4f6;
        padding: 6px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        color: #6b7280;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #1f2937 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
    }
    h1 {
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    h3 {
        color: #374151 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 8px;
        margin-bottom: 16px !important;
    }
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1px solid #e5e7eb !important;
    }

    div[data-testid="column"] {
        padding: 0 5px !important;
    }
    [data-testid="stDataFrame"] div[data-testid="glideDataEditor"] div.dvn-scroller div[role="rowheader"],
    [data-testid="stDataFrame"] div[data-testid="glideDataEditor"] div.dvn-scroller div[aria-colindex="1"]:first-child,
    [data-testid="stDataFrame"] canvas + div div[role="rowheader"],
    div[data-testid="stDataFrameResizable"] div[role="rowheader"],
    [data-testid="stDataFrame"] .row-number,
    [data-testid="stDataFrame"] div[data-testid="glideDataEditor"] header div:first-child,
    div.stDataFrame div[role="gridcell"][aria-colindex="0"],
    div.stDataFrame div[role="columnheader"][aria-colindex="0"] {
        display: none !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        overflow: hidden !important;
    }
    [data-testid="stRadio"] label span[data-checked="true"],
    [data-testid="stRadio"] label div[role="radio"][aria-checked="true"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }
    span[data-baseweb="tag"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    span[data-baseweb="tag"] span {
        color: white !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: #2563eb !important;
    }
    button[kind="primary"],
    .stButton button[kind="primary"],
    [data-testid="stBaseButton-primary"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: white !important;
    }
    button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div:first-child {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Cortex AI Cost Dashboard")

try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    IS_SIS = True
except:
    session = None
    IS_SIS = False

SCHEMA_PREFIX = f"{session.get_current_database().strip(chr(34))}.{session.get_current_schema().strip(chr(34))}" if IS_SIS else "ADMIN_DB.AI_COSTS"

@st.cache_data(ttl=300, show_spinner=False)
def run_query(sql):
    if IS_SIS:
        return session.sql(sql).to_pandas()
    else:
        return st.connection("snowflake").query(sql)

def show_df(df, **kwargs):
    fmt = {}
    for col in df.columns:
        cl = col.upper()
        if cl in ("COST ($)", "COST_USD", "RATE ($/CREDIT)"):
            fmt[col] = "${:,.2f}"
        elif cl in ("CREDITS",):
            fmt[col] = "{:,.3f}"
        elif cl in ("TOKENS", "INPUT_TOKENS", "OUTPUT_TOKENS", "REQUESTS", "REQUEST_COUNT", "CACHE_READ_TOKENS", "CACHE_WRITE_TOKENS"):
            fmt[col] = "{:,.0f}"
    numeric_cols = list(fmt.keys())
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    st.dataframe(df.style.format(fmt, na_rep=""), **kwargs)

def fmt_df(df):
    return df

def run_procedure(sql):
    if IS_SIS:
        session.sql(sql).collect()
    else:
        st.connection("snowflake").session().sql(sql).collect()


@st.cache_data(ttl=300, show_spinner=False)
def load_unified_data(days_back, start_date=None, end_date=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    return run_query(f"""
        SELECT 
            USAGE_DATE,
            SERVICE_CATEGORY,
            SERVICE_NAME,
            MODEL_NAME,
            CREDITS,
            COST_USD,
            TOKENS,
            INPUT_TOKENS,
            OUTPUT_TOKENS,
            CACHE_READ_TOKENS,
            CACHE_WRITE_TOKENS,
            REQUEST_COUNT
        FROM {SCHEMA_PREFIX}.CORTEX_AI_UNIFIED_COSTS
        WHERE {date_filter}
    """)

@st.cache_data(ttl=300, show_spinner=False)
def load_user_summary(days_back, start_date=None, end_date=None, categories=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    cat_filter = f" AND SERVICE_CATEGORY IN ({','.join(repr(c) for c in categories)})" if categories else ""
    return run_query(f"""
        SELECT USER_NAME, FULL_NAME,
               COUNT(QUERY_ID) AS REQUESTS,
               SUM(CREDITS) AS CREDITS,
               SUM(COST_USD) AS COST_USD
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE {date_filter}{cat_filter}
        GROUP BY USER_NAME, FULL_NAME
        ORDER BY CREDITS DESC
    """)

@st.cache_data(ttl=300, show_spinner=False)
def load_user_service(days_back, start_date=None, end_date=None, user_name=None, categories=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    user_filter = f" AND USER_NAME = '{user_name}'" if user_name else ""
    cat_filter = f" AND SERVICE_CATEGORY IN ({','.join(repr(c) for c in categories)})" if categories else ""
    return run_query(f"""
        SELECT FULL_NAME, SERVICE_NAME, MODEL_NAME,
               COUNT(QUERY_ID) AS REQUESTS,
               SUM(CREDITS) AS CREDITS,
               SUM(COST_USD) AS COST_USD,
               SUM(TOKENS) AS TOKENS,
               SUM(INPUT_TOKENS) AS INPUT_TOKENS,
               SUM(OUTPUT_TOKENS) AS OUTPUT_TOKENS,
               SUM(CACHE_READ_TOKENS) AS CACHE_READ_TOKENS,
               SUM(CACHE_WRITE_TOKENS) AS CACHE_WRITE_TOKENS
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE {date_filter}{user_filter}{cat_filter}
        GROUP BY FULL_NAME, SERVICE_NAME, MODEL_NAME
        ORDER BY FULL_NAME, REQUESTS DESC
    """)

@st.cache_data(ttl=300, show_spinner=False)
def load_user_daily(days_back, start_date=None, end_date=None, user_name=None, categories=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    user_filter = f" AND USER_NAME = '{user_name}'" if user_name else ""
    cat_filter = f" AND SERVICE_CATEGORY IN ({','.join(repr(c) for c in categories)})" if categories else ""
    return run_query(f"""
        SELECT FULL_NAME, USAGE_DATE, SERVICE_NAME, MODEL_NAME,
               COUNT(QUERY_ID) AS REQUESTS,
               SUM(CREDITS) AS CREDITS,
               SUM(COST_USD) AS COST_USD,
               SUM(TOKENS) AS TOKENS,
               SUM(INPUT_TOKENS) AS INPUT_TOKENS,
               SUM(OUTPUT_TOKENS) AS OUTPUT_TOKENS,
               SUM(CACHE_READ_TOKENS) AS CACHE_READ_TOKENS,
               SUM(CACHE_WRITE_TOKENS) AS CACHE_WRITE_TOKENS
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE {date_filter}{user_filter}{cat_filter}
        GROUP BY FULL_NAME, USAGE_DATE, SERVICE_NAME, MODEL_NAME
        ORDER BY USAGE_DATE DESC, REQUESTS DESC
    """)

@st.cache_data(ttl=300, show_spinner=False)
def load_unified_data_for_user(days_back, user_name, start_date=None, end_date=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    return run_query(f"""
        SELECT
            USAGE_DATE,
            SERVICE_CATEGORY,
            SERVICE_NAME,
            MODEL_NAME,
            SUM(CREDITS) AS CREDITS,
            SUM(COST_USD) AS COST_USD,
            SUM(TOKENS) AS TOKENS,
            SUM(INPUT_TOKENS) AS INPUT_TOKENS,
            SUM(OUTPUT_TOKENS) AS OUTPUT_TOKENS,
            SUM(CACHE_READ_TOKENS) AS CACHE_READ_TOKENS,
            SUM(CACHE_WRITE_TOKENS) AS CACHE_WRITE_TOKENS,
            COUNT(QUERY_ID) AS REQUEST_COUNT
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE {date_filter}
          AND USER_NAME = '{user_name}'
        GROUP BY USAGE_DATE, SERVICE_CATEGORY, SERVICE_NAME, MODEL_NAME
    """)

@st.cache_data(ttl=300, show_spinner=False)
def load_user_detail(days_back, start_date=None, end_date=None, user_name=None, categories=None):
    if start_date and end_date:
        date_filter = f"USAGE_DATE BETWEEN '{start_date}' AND '{end_date}'"
    else:
        date_filter = f"USAGE_DATE >= DATEADD('day', -{days_back}, CURRENT_DATE())"
    user_filter = f" AND USER_NAME = '{user_name}'" if user_name else ""
    cat_filter = f" AND SERVICE_CATEGORY IN ({','.join(repr(c) for c in categories)})" if categories else ""
    return run_query(f"""
        SELECT QUERY_ID, USAGE_DATE, USAGE_TIME, SERVICE_NAME, MODEL_NAME,
               TOKENS, INPUT_TOKENS, OUTPUT_TOKENS, CACHE_READ_TOKENS, CACHE_WRITE_TOKENS,
               CREDITS, COST_USD, QUERY_TEXT
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE {date_filter}{user_filter}{cat_filter}
        ORDER BY USAGE_TIME DESC
        LIMIT 500
    """)

with st.sidebar:
    st.markdown("### ⚙️ Filters")
    st.markdown("---")
    
    st.markdown("**📅 Time Range**")
    time_range_option = st.radio(
        "Time Range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Last 90 days", "Last 365 days", "Custom"],
        index=2,
        horizontal=False,
        label_visibility="collapsed"
    )
    
    if time_range_option == "Custom":
        st.markdown("")
        date_cols = st.columns(2)
        with date_cols[0]:
            start_date = st.date_input("Start", value=date.today() - timedelta(days=30))
        with date_cols[1]:
            end_date = st.date_input("End", value=date.today())
        if start_date > end_date:
            st.error("Start date must be before end date")
            st.stop()
        days_back = (date.today() - start_date).days
        custom_start = start_date
        custom_end = end_date
    else:
        days_back = int(time_range_option.split()[1])
        custom_start = None
        custom_end = None
    
    st.markdown("---")
    
    with st.spinner("Loading data..."):
        unified_df = load_unified_data(days_back, custom_start, custom_end)
        user_summary_df = load_user_summary(days_back, custom_start, custom_end)
    
    all_categories = sorted(unified_df["SERVICE_CATEGORY"].dropna().unique().tolist())
    
    st.markdown("**🏷️ Service Categories**")
    selected_categories = st.multiselect("Categories", all_categories, default=all_categories, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("**👤 User**")
    all_users_sidebar = ["All Users"] + sorted(user_summary_df["FULL_NAME"].dropna().unique().tolist())
    user_name_map = dict(zip(user_summary_df["FULL_NAME"], user_summary_df["USER_NAME"]))
    selected_global_user_display = st.selectbox("User", all_users_sidebar, label_visibility="collapsed", key="global_user_filter")
    selected_global_user = user_name_map.get(selected_global_user_display) if selected_global_user_display != "All Users" else None

    st.markdown("---")
    if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
        run_procedure(f"CALL {SCHEMA_PREFIX}.REFRESH_CORTEX_AI_COSTS({days_back})")
        run_procedure(f"CALL {SCHEMA_PREFIX}.REFRESH_USER_AI_COSTS({days_back})")
        st.cache_data.clear()
        st.success("✅ Data refreshed!")
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()


if not selected_categories:
    st.warning("⚠️ Please select at least one service category.")
    st.stop()

if selected_global_user:
    filtered_df = load_unified_data_for_user(days_back, selected_global_user, custom_start, custom_end)
    if selected_categories:
        filtered_df = filtered_df[filtered_df["SERVICE_CATEGORY"].isin(selected_categories)]
else:
    filtered_df = unified_df[unified_df["SERVICE_CATEGORY"].isin(selected_categories)]

total_credits = float(filtered_df["CREDITS"].sum() or 0)
total_cost = float(filtered_df["COST_USD"].sum() or 0)
total_tokens = float(filtered_df["TOKENS"].sum() or 0)
total_requests = int(filtered_df["REQUEST_COUNT"].sum() or 0)
services_used = filtered_df["SERVICE_NAME"].nunique()
active_days = filtered_df["USAGE_DATE"].nunique()
active_users = 1 if selected_global_user else user_summary_df["USER_NAME"].nunique()

st.subheader("📊 Key Metrics")
kpi_row1 = st.columns(4)
with kpi_row1[0]:
    st.metric("💳 Total Credits", f"{total_credits:,.2f}", help="Total Snowflake credits consumed by all selected Cortex AI services.")
with kpi_row1[1]:
    st.metric("💲 Total Cost", f"${total_cost:,.2f}", help="Estimated dollar cost based on dynamic credit rates.")
with kpi_row1[2]:
    st.metric("🔤 Total Tokens", f"{total_tokens:,.0f}", help="Total tokens processed across all LLM-based services.")
with kpi_row1[3]:
    st.metric("📨 Total Requests", f"{total_requests:,.0f}", help="Total number of API calls or queries made to Cortex AI services.")
kpi_row2 = st.columns(4)
with kpi_row2[0]:
    st.metric("🔧 Services Used", f"{services_used}", help="Number of distinct Cortex AI services used.")
with kpi_row2[1]:
    st.metric("📆 Active Days", f"{active_days}", help="Number of days with recorded Cortex AI usage.")
with kpi_row2[2]:
    st.metric("👥 Active Users", f"{active_users}", help="Number of distinct users who have executed Cortex AI queries.")
st.markdown("")

category_credits = filtered_df.groupby("SERVICE_CATEGORY").agg({"CREDITS": "sum", "COST_USD": "sum"}).sort_values("CREDITS", ascending=False).reset_index()

if not category_credits.empty and total_credits > 0:
    st.subheader("📈 Credit Distribution by Category")
    cats = list(category_credits.iterrows())
    max_per_row = 5
    for row_start in range(0, len(cats), max_per_row):
        row_chunk = cats[row_start:row_start + max_per_row]
        cat_cols = st.columns(len(row_chunk))
        for col_idx, (_, row) in enumerate(row_chunk):
            cat_name = row["SERVICE_CATEGORY"]
            cat_credits = row["CREDITS"]
            cat_cost = row["COST_USD"]
            cat_pct = (cat_credits / total_credits) * 100
            with cat_cols[col_idx]:
                st.metric(
                    cat_name,
                    f"{cat_credits:,.2f} (${cat_cost:,.2f})",
                    f"{cat_pct:.1f}%",
                    delta_color="off",
                    help=f"{cat_name}: {cat_pct:.1f}% of total credits"
                )

st.markdown("")

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📅 Month over Month Costs")
    monthly_df = filtered_df.copy()
    monthly_df["MONTH"] = pd.to_datetime(monthly_df["USAGE_DATE"]).dt.to_period("M").astype(str)
    monthly_credits = monthly_df.groupby("MONTH").agg({"CREDITS": "sum", "COST_USD": "sum"}).reset_index().sort_values("MONTH")
    if not monthly_credits.empty:
        chart = alt.Chart(monthly_credits).mark_bar(
            cornerRadiusTopLeft=8,
            cornerRadiusTopRight=8,
            color='#2563eb'
        ).encode(
            x=alt.X('MONTH:N', title='Month', sort=None),
            y=alt.Y('CREDITS:Q', title='Credits'),
            tooltip=['MONTH', alt.Tooltip('CREDITS:Q', format=',.2f'), alt.Tooltip('COST_USD:Q', title='Cost ($)', format='$,.2f')]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No monthly data available.")

with col2:
    st.subheader("📉 Daily Credit Trend")
    daily_credits = filtered_df.groupby("USAGE_DATE").agg({"CREDITS": "sum", "COST_USD": "sum"}).reset_index().sort_values("USAGE_DATE")
    if not daily_credits.empty:
        chart = alt.Chart(daily_credits).mark_area(
            line={'color': '#667eea'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='rgba(102, 126, 234, 0.1)', offset=0),
                       alt.GradientStop(color='rgba(102, 126, 234, 0.6)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('USAGE_DATE:T', title='Date'),
            y=alt.Y('CREDITS:Q', title='Credits'),
            tooltip=['USAGE_DATE:T', alt.Tooltip('CREDITS:Q', format=',.2f'), alt.Tooltip('COST_USD:Q', title='Cost ($)', format='$,.2f')]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No daily trend data available.")

col3, col4 = st.columns(2, gap="large")

with col3:
    st.subheader("⚡ Credits by Service")
    service_credits = filtered_df.groupby("SERVICE_NAME").agg({"CREDITS": "sum", "COST_USD": "sum"}).sort_values("CREDITS", ascending=False).reset_index()
    if not service_credits.empty:
        chart = alt.Chart(service_credits).mark_bar(
            cornerRadiusTopLeft=8,
            cornerRadiusTopRight=8,
            color='#11998e'
        ).encode(
            x=alt.X('SERVICE_NAME:N', title='Service', sort='-y'),
            y=alt.Y('CREDITS:Q', title='Credits'),
            tooltip=['SERVICE_NAME', alt.Tooltip('CREDITS:Q', format=',.2f'), alt.Tooltip('COST_USD:Q', title='Cost ($)', format='$,.2f')]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No credit data available.")

with col4:
    st.subheader("🤖 Tokens by Model")
    model_tokens = filtered_df.groupby("MODEL_NAME")["TOKENS"].sum().sort_values(ascending=False).head(10).reset_index()
    model_tokens["MODEL_NAME"] = model_tokens["MODEL_NAME"].fillna("Unknown")
    model_tokens["TOKENS_M"] = model_tokens["TOKENS"] / 1_000_000
    if not model_tokens.empty:
        chart = alt.Chart(model_tokens).mark_arc().encode(
            theta=alt.Theta('TOKENS_M:Q'),
            color=alt.Color('MODEL_NAME:N', legend=alt.Legend(title='Model')),
            tooltip=['MODEL_NAME', alt.Tooltip('TOKENS_M:Q', title='Tokens (M)', format=',.0f')]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No token data available.")

st.markdown("")
st.subheader("📋 Detailed Usage Data")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📄 Unified Summary", "🔧 By Service", "🤖 By Model", "👤 By User", "🤖 Cortex Agent", "🧠 Snowflake Intelligence", "💻 Cortex Code"])

with tab1:
    display_df = filtered_df[["USAGE_DATE", "SERVICE_NAME", "MODEL_NAME", "CREDITS", "COST_USD", "TOKENS", "INPUT_TOKENS", "OUTPUT_TOKENS", "CACHE_READ_TOKENS", "CACHE_WRITE_TOKENS", "REQUEST_COUNT"]].rename(columns={"SERVICE_NAME": "SERVICE", "MODEL_NAME": "MODEL", "REQUEST_COUNT": "REQUESTS", "COST_USD": "COST ($)"}).sort_values(["USAGE_DATE", "CREDITS"], ascending=[False, False]).reset_index(drop=True)
    show_df(fmt_df(display_df), use_container_width=True, height=400)
    st.download_button("Download CSV", display_df.to_csv(index=False), "unified_summary.csv", "text/csv", key="dl_unified")

with tab2:
    service_summary = filtered_df.groupby("SERVICE_NAME").agg({
        "CREDITS": "sum",
        "COST_USD": "sum",
        "TOKENS": "sum",
        "INPUT_TOKENS": "sum",
        "OUTPUT_TOKENS": "sum",
        "CACHE_READ_TOKENS": "sum",
        "CACHE_WRITE_TOKENS": "sum",
        "REQUEST_COUNT": "sum"
    }).reset_index().rename(columns={"REQUEST_COUNT": "REQUESTS", "COST_USD": "COST ($)"}).sort_values("CREDITS", ascending=False).reset_index(drop=True)
    show_df(fmt_df(service_summary), use_container_width=True, height=400)
    st.download_button("Download CSV", service_summary.to_csv(index=False), "by_service.csv", "text/csv", key="dl_service")

with tab3:
    model_summary = filtered_df.groupby("MODEL_NAME").agg({
        "CREDITS": "sum",
        "COST_USD": "sum",
        "TOKENS": "sum",
        "INPUT_TOKENS": "sum",
        "OUTPUT_TOKENS": "sum",
        "CACHE_READ_TOKENS": "sum",
        "CACHE_WRITE_TOKENS": "sum",
        "REQUEST_COUNT": "sum"
    }).reset_index().rename(columns={"REQUEST_COUNT": "REQUESTS", "COST_USD": "COST ($)"})
    model_summary["MODEL_NAME"] = model_summary["MODEL_NAME"].fillna("N/A")
    model_summary = model_summary.sort_values("CREDITS", ascending=False).reset_index(drop=True)
    show_df(fmt_df(model_summary), use_container_width=True, height=400)
    st.download_button("Download CSV", model_summary.to_csv(index=False), "by_model.csv", "text/csv", key="dl_model")

with tab4:
    user_map = dict(zip(user_summary_df["FULL_NAME"], user_summary_df["USER_NAME"]))
    all_users = ["All Users"] + sorted(user_summary_df["FULL_NAME"].dropna().unique().tolist())
    default_user_idx = all_users.index(selected_global_user_display) if selected_global_user_display in all_users else 0
    selected_user_display = st.selectbox("🔍 Filter by User", all_users, index=default_user_idx, key="user_filter")
    selected_user = user_map.get(selected_user_display, None) if selected_user_display != "All Users" else None

    filtered_summary_df = load_user_summary(days_back, custom_start, custom_end, selected_categories)
    if selected_user:
        user_summary = filtered_summary_df[filtered_summary_df["USER_NAME"] == selected_user].copy()
    else:
        user_summary = filtered_summary_df.copy()
    user_summary = user_summary.rename(columns={"COST_USD": "COST ($)"}).sort_values("CREDITS", ascending=False).reset_index(drop=True)
    
    if not user_summary.empty:
        ucol1, ucol2 = st.columns(2, gap="large")
        with ucol1:
            st.markdown("**👥 User Summary**")
            show_df(fmt_df(user_summary[["FULL_NAME", "REQUESTS", "CREDITS", "COST ($)"]]), use_container_width=True)
            st.download_button("Download CSV", user_summary.to_csv(index=False), "user_summary.csv", "text/csv", key="dl_user_summary")
        with ucol2:
            st.markdown("**📊 Requests by User**")
            chart = alt.Chart(user_summary).mark_arc(innerRadius=50).encode(
                theta=alt.Theta('REQUESTS:Q'),
                color=alt.Color('FULL_NAME:N', legend=alt.Legend(title="User")),
                tooltip=['FULL_NAME', 'REQUESTS', 'CREDITS', alt.Tooltip('COST ($):Q', format='$,.2f')]
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
    
    user_service = load_user_service(days_back, custom_start, custom_end, selected_user, selected_categories)
    if not user_service.empty:
        user_service = user_service.rename(columns={"SERVICE_NAME": "SERVICE", "MODEL_NAME": "MODEL", "COST_USD": "COST ($)"})
        st.markdown("**🔧 Usage by Service & Model**")
        show_df(fmt_df(user_service), use_container_width=True, height=300)
        st.download_button("Download CSV", user_service.to_csv(index=False), "user_by_service.csv", "text/csv", key="dl_user_service")
    
    user_daily = load_user_daily(days_back, custom_start, custom_end, selected_user, selected_categories)
    if not user_daily.empty:
        user_daily = user_daily.rename(columns={"SERVICE_NAME": "SERVICE", "MODEL_NAME": "MODEL", "COST_USD": "COST ($)"})
        st.markdown("**📅 Daily Usage Detail**")
        show_df(fmt_df(user_daily), use_container_width=True, height=300)
        st.download_button("Download CSV", user_daily.to_csv(index=False), "user_daily.csv", "text/csv", key="dl_user_daily")
    
    if selected_user is not None:
        st.markdown("---")
        st.markdown(f"**💰 AI Services Cost Detail for {selected_user_display}**")
        user_queries = load_user_detail(days_back, custom_start, custom_end, selected_user, selected_categories)
        if not user_queries.empty:
            user_queries = user_queries.rename(columns={"USAGE_DATE": "DATE", "SERVICE_NAME": "SERVICE", "MODEL_NAME": "MODEL", "COST_USD": "COST ($)"})
            show_df(fmt_df(user_queries), use_container_width=True, height=400)
            st.download_button("Download CSV", user_queries.to_csv(index=False), "user_query_detail.csv", "text/csv", key="dl_user_queries")
        else:
            st.info("No AI service usage found for this user.")

with tab5:
    agent_user_filter = f" AND USER_NAME = '{selected_global_user}'" if selected_global_user else ""
    agent_df = run_query(f"""
        SELECT COALESCE(AGENT_NAME, 'API CALL') AS AGENT_NAME,
               COALESCE(AGENT_DATABASE_NAME || '.' || AGENT_SCHEMA_NAME || '.' || AGENT_NAME, 'API CALL') AS AGENT_FQN,
               COALESCE(MODEL_NAME, 'unknown') AS MODEL_NAME,
               DATE(START_TIME) AS USAGE_DATE, FULL_NAME AS USER_NAME,
               SUM(TOKEN_CREDITS) AS CREDITS, SUM(COST_USD) AS "COST ($)",
               SUM(TOKENS) AS TOKENS, COUNT(*) AS REQUESTS
        FROM {SCHEMA_PREFIX}.CORTEX_AGENT_USAGE
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_DATE()){agent_user_filter}
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY USAGE_DATE DESC, CREDITS DESC
    """)
    if not agent_df.empty:
        agent_cost = agent_df.groupby(["AGENT_NAME", "AGENT_FQN", "MODEL_NAME"]).agg({"CREDITS": "sum", "COST ($)": "sum", "TOKENS": "sum", "REQUESTS": "sum"}).reset_index().sort_values("CREDITS", ascending=False).reset_index(drop=True)
        show_df(fmt_df(agent_cost), use_container_width=True, height=300)
        st.download_button("Download CSV", agent_cost.to_csv(index=False), "agent_costs.csv", "text/csv", key="dl_agent_cost")
        st.markdown("**Daily Detail**")
        show_df(fmt_df(agent_df), use_container_width=True, height=400)
        st.download_button("Download CSV", agent_df.to_csv(index=False), "agent_daily.csv", "text/csv", key="dl_agent_daily")
    else:
        st.info("No Cortex Agent usage found.")

with tab6:
    si_user_filter = f" AND USER_NAME = '{selected_global_user}'" if selected_global_user else ""
    si_df = run_query(f"""
        SELECT COALESCE(SNOWFLAKE_INTELLIGENCE_NAME, 'API CALL') AS SI_NAME,
               COALESCE(AGENT_DATABASE_NAME || '.' || AGENT_SCHEMA_NAME || '.' || AGENT_NAME, 'API CALL') AS AGENT_FQN,
               COALESCE(MODEL_NAME, 'unknown') AS MODEL_NAME,
               DATE(START_TIME) AS USAGE_DATE, FULL_NAME AS USER_NAME,
               SUM(TOKEN_CREDITS) AS CREDITS, SUM(COST_USD) AS "COST ($)",
               SUM(TOKENS) AS TOKENS, COUNT(*) AS REQUESTS
        FROM {SCHEMA_PREFIX}.SNOWFLAKE_INTELLIGENCE_USAGE
        WHERE START_TIME >= DATEADD('day', -{days_back}, CURRENT_DATE()){si_user_filter}
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY USAGE_DATE DESC, CREDITS DESC
    """)
    if not si_df.empty:
        si_cost = si_df.groupby(["SI_NAME", "AGENT_FQN", "MODEL_NAME"]).agg({"CREDITS": "sum", "COST ($)": "sum", "TOKENS": "sum", "REQUESTS": "sum"}).reset_index().sort_values("CREDITS", ascending=False).reset_index(drop=True)
        st.markdown("**Cost by Snowflake Intelligence Name**")
        show_df(fmt_df(si_cost), use_container_width=True, height=300)
        st.download_button("Download CSV", si_cost.to_csv(index=False), "si_costs.csv", "text/csv", key="dl_si_cost")
        st.markdown("**Daily Detail**")
        show_df(fmt_df(si_df), use_container_width=True, height=400)
        st.download_button("Download CSV", si_df.to_csv(index=False), "si_daily.csv", "text/csv", key="dl_si_daily")
    else:
        st.info("No Snowflake Intelligence usage found.")

with tab7:
    coco_user_filter = f" AND USER_NAME = '{selected_global_user}'" if selected_global_user else ""
    coco_cli_df = run_query(f"""
        SELECT USAGE_DATE, FULL_NAME AS USER_NAME, SUM(CREDITS) AS CREDITS
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE SERVICE_NAME = 'CORTEX_CODE_CLI'
          AND USAGE_DATE >= DATEADD('day', -30, CURRENT_DATE()){coco_user_filter}
        GROUP BY 1, 2
    """)
    coco_ss_df = run_query(f"""
        SELECT USAGE_DATE, FULL_NAME AS USER_NAME, SUM(CREDITS) AS CREDITS
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE SERVICE_NAME = 'CORTEX_CODE_SNOWSIGHT'
          AND USAGE_DATE >= DATEADD('day', -30, CURRENT_DATE()){coco_user_filter}
        GROUP BY 1, 2
    """)
    st.markdown("**Cortex Code Snowsight — Credits by Date & User**")
    if not coco_ss_df.empty:
        ss_pivot = coco_ss_df.pivot_table(index="USER_NAME", columns="USAGE_DATE", values="CREDITS", aggfunc="sum")
        ss_pivot = ss_pivot.reindex(sorted(ss_pivot.columns, reverse=True), axis=1)
        ss_pivot.columns = [str(c) for c in ss_pivot.columns]
        ss_pivot = ss_pivot.round(2).reset_index().sort_values("USER_NAME").reset_index(drop=True)
        show_df(fmt_df(ss_pivot), use_container_width=True, height=400)
        st.download_button("Download CSV", ss_pivot.to_csv(index=False), "coco_snowsight_credits.csv", "text/csv", key="dl_coco_ss")
    else:
        st.info("No Cortex Code Snowsight usage found.")
    st.markdown("**Cortex Code CLI — Credits by Date & User**")
    if not coco_cli_df.empty:
        cli_pivot = coco_cli_df.pivot_table(index="USER_NAME", columns="USAGE_DATE", values="CREDITS", aggfunc="sum")
        cli_pivot = cli_pivot.reindex(sorted(cli_pivot.columns, reverse=True), axis=1)
        cli_pivot.columns = [str(c) for c in cli_pivot.columns]
        cli_pivot = cli_pivot.round(2).reset_index().sort_values("USER_NAME").reset_index(drop=True)
        show_df(fmt_df(cli_pivot), use_container_width=True, height=400)
        st.download_button("Download CSV", cli_pivot.to_csv(index=False), "coco_cli_credits.csv", "text/csv", key="dl_coco_cli")
    else:
        st.info("No Cortex Code CLI usage found.")
    coco_desktop_df = run_query(f"""
        SELECT USAGE_DATE, FULL_NAME AS USER_NAME, SUM(CREDITS) AS CREDITS
        FROM {SCHEMA_PREFIX}.USER_AI_COSTS
        WHERE SERVICE_NAME = 'CORTEX_CODE_DESKTOP'
          AND USAGE_DATE >= DATEADD('day', -30, CURRENT_DATE()){coco_user_filter}
        GROUP BY 1, 2
    """)
    st.markdown("**Cortex Code Desktop — Credits by Date & User**")
    if not coco_desktop_df.empty:
        desk_pivot = coco_desktop_df.pivot_table(index="USER_NAME", columns="USAGE_DATE", values="CREDITS", aggfunc="sum")
        desk_pivot = desk_pivot.reindex(sorted(desk_pivot.columns, reverse=True), axis=1)
        desk_pivot.columns = [str(c) for c in desk_pivot.columns]
        desk_pivot = desk_pivot.round(2).reset_index().sort_values("USER_NAME").reset_index(drop=True)
        show_df(fmt_df(desk_pivot), use_container_width=True, height=400)
        st.download_button("Download CSV", desk_pivot.to_csv(index=False), "coco_desktop_credits.csv", "text/csv", key="dl_coco_desktop")
    else:
        st.info("No Cortex Code Desktop usage found.")

st.markdown("")
st.subheader("💬 Ask Questions About Your AI Costs")
st.caption("Powered by Cortex Analyst — ask natural language questions about your cost data")

SEMANTIC_MODEL = f"@{SCHEMA_PREFIX}.STREAMLIT_STAGE/cortex_ai_costs_model.yaml"

ONBOARDING_QUESTIONS = [
    "What is the total cost in dollars over the last 30 days?",
    "What is the cost breakdown by service over the last 30 days?",
    "Show me the daily cost trend for the last 30 days",
    "Who are the top 10 users by cost?",
    "What is the cost by model?",
]

if "analyst_messages" not in st.session_state:
    st.session_state.analyst_messages = []
if "active_suggestion" not in st.session_state:
    st.session_state.active_suggestion = None

def _sanitize_messages(messages):
    sanitized = []
    for m in messages:
        if sanitized and sanitized[-1]["role"] == m["role"]:
            continue
        sanitized.append(m)
    return sanitized

def send_analyst_message(prompt):
    messages = _sanitize_messages(st.session_state.analyst_messages) + [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    request_body = {
        "messages": messages,
        "semantic_model_file": SEMANTIC_MODEL,
    }
    resp = _snowflake.send_snow_api_request(
        "POST",
        "/api/v2/cortex/analyst/message",
        {},
        {},
        request_body,
        {},
        30000,
    )
    if resp["status"] < 400:
        parsed = json.loads(resp["content"])
        content = parsed["message"]["content"]
        st.session_state.analyst_messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
        st.session_state.analyst_messages.append({"role": "analyst", "content": content})
        return content
    else:
        error = json.loads(resp["content"]) if resp.get("content") else {}
        raise Exception(error.get("message", f"Error {resp['status']}"))

def display_analyst_content(content, msg_idx=0):
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            with st.expander("Suggested follow-ups", expanded=True):
                for si, s in enumerate(item["suggestions"]):
                    if st.button(s, key=f"sug_{msg_idx}_{si}"):
                        st.session_state.active_suggestion = s
        elif item["type"] == "sql":
            with st.expander("SQL Query", expanded=False):
                st.code(item["statement"], language="sql")
            with st.expander("Results", expanded=True):
                with st.spinner("Running SQL..."):
                    try:
                        df = session.sql(item["statement"]).to_pandas()
                        for c in df.select_dtypes(include="number").columns:
                            df[c] = df[c].fillna(0)
                        if len(df) > 1:
                            data_tab, bar_tab = st.tabs(["Data", "Bar Chart"])
                            with data_tab:
                                show_df(df, use_container_width=True)
                            with bar_tab:
                                if len(df.columns) > 1:
                                    st.bar_chart(df.set_index(df.columns[0]))
                        else:
                            show_df(df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Query error: {e}")

if st.session_state.analyst_messages:
    if st.button("Clear Chat", key="clear_analyst"):
        st.session_state.analyst_messages = []
        st.session_state.active_suggestion = None
        st.rerun()

if not st.session_state.analyst_messages:
    st.markdown("**Get started with a question:**")
    q_cols = st.columns(len(ONBOARDING_QUESTIONS))
    for i, q in enumerate(ONBOARDING_QUESTIONS):
        with q_cols[i]:
            if st.button(q, key=f"onboard_{i}", use_container_width=True):
                st.session_state.active_suggestion = q

for msg_idx, msg in enumerate(st.session_state.analyst_messages):
    role = "user" if msg["role"] == "user" else "assistant"
    if role == "user":
        st.markdown(f"**You:** {msg['content'][0]['text']}")
    else:
        st.markdown("**Assistant:**")
        display_analyst_content(msg["content"], msg_idx)
    st.markdown("---")

prompt_input = st.text_input("Ask a question about your AI costs...", key="analyst_prompt")
if st.button("Send", key="send_analyst") and prompt_input:
    st.session_state.active_suggestion = prompt_input

if st.session_state.active_suggestion:
    prompt = st.session_state.active_suggestion
    st.session_state.active_suggestion = None
    st.markdown(f"**You:** {prompt}")
    st.markdown("**Assistant:**")
    with st.spinner("Thinking..."):
        try:
            content = send_analyst_message(prompt)
            display_analyst_content(content, len(st.session_state.analyst_messages))
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown("---")
st.caption("📊 Use the sidebar refresh button to pull latest data from SNOWFLAKE.ACCOUNT_USAGE views")
