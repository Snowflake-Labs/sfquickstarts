"""
Agent Verbosity Evaluation Dashboard
Visualizes evaluation results for agent verbosity compliance
"""
import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector

st.set_page_config(page_title="Agent Eval Dashboard", layout="wide")

# Connect to Snowflake
@st.cache_resource
def get_connection():
    conn = snowflake.connector.connect(connection_name='myaccount')
    conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
    return conn

conn = get_connection()

st.title("📊 Agent Verbosity Evaluation Dashboard")

# Load data
@st.cache_data(ttl=300)
def load_eval_data():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            agent_name,
            description,
            target_max_lines,
            query_id,
            query,
            category,
            response,
            actual_lines,
            word_count,
            char_count,
            line_compliant,
            length_score,
            format_score,
            content_score,
            style_score,
            quality_pass,
            judge_reasoning
        FROM FANCYWORKS_DEMO_DB.PUBLIC.AGENT_EVAL_RESULTS
    """)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=columns)

df = load_eval_data()

# Summary metrics
st.subheader("Overall Summary")

col1, col2, col3, col4 = st.columns(4)

total_tests = len(df)
line_compliant_count = df['LINE_COMPLIANT'].sum()
judged_df = df[df['QUALITY_PASS'].notna()]
quality_pass_count = judged_df['QUALITY_PASS'].sum() if len(judged_df) > 0 else 0

with col1:
    st.metric("Total Tests", total_tests)
with col2:
    st.metric("Line Compliant", f"{line_compliant_count}/{total_tests}", 
              delta=f"{100*line_compliant_count/total_tests:.0f}%")
with col3:
    st.metric("Quality Pass", f"{int(quality_pass_count)}/{len(judged_df)}" if len(judged_df) > 0 else "N/A")
with col4:
    avg_score = judged_df[['LENGTH_SCORE', 'FORMAT_SCORE', 'CONTENT_SCORE', 'STYLE_SCORE']].mean().mean()
    st.metric("Avg Quality Score", f"{avg_score:.1f}/5" if not pd.isna(avg_score) else "N/A")

st.divider()

# Agent performance summary
st.subheader("Agent Performance Summary")

agent_summary = df.groupby('AGENT_NAME').agg({
    'LINE_COMPLIANT': ['sum', 'count'],
    'ACTUAL_LINES': 'mean',
    'TARGET_MAX_LINES': 'first',
    'WORD_COUNT': 'mean'
}).reset_index()
agent_summary.columns = ['Agent', 'Lines OK', 'Total', 'Avg Lines', 'Target Lines', 'Avg Words']
agent_summary['Compliance %'] = (agent_summary['Lines OK'] / agent_summary['Total'] * 100).round(0)

# Add quality scores
quality_summary = judged_df.groupby('AGENT_NAME').agg({
    'LENGTH_SCORE': 'mean',
    'FORMAT_SCORE': 'mean',
    'CONTENT_SCORE': 'mean',
    'STYLE_SCORE': 'mean',
    'QUALITY_PASS': ['sum', 'count']
}).reset_index()
quality_summary.columns = ['Agent', 'Length', 'Format', 'Content', 'Style', 'Pass', 'Judged']

agent_summary = agent_summary.merge(quality_summary, on='Agent', how='left')
agent_summary['Avg Score'] = ((agent_summary['Length'].fillna(0) + agent_summary['Format'].fillna(0) + 
                               agent_summary['Content'].fillna(0) + agent_summary['Style'].fillna(0)) / 4).round(1)

# Status column
def get_status(row):
    if row['Lines OK'] == row['Total'] and row['Pass'] == row['Judged']:
        return "✅ PASS"
    elif row['Lines OK'] > 0 or row['Pass'] > 0:
        return "⚠️ PARTIAL"
    else:
        return "❌ FAIL"

agent_summary['Status'] = agent_summary.apply(get_status, axis=1)

# Display table
st.dataframe(
    agent_summary[['Agent', 'Target Lines', 'Avg Lines', 'Compliance %', 'Pass', 'Judged', 'Avg Score', 'Status']],
    column_config={
        'Compliance %': st.column_config.ProgressColumn(
            "Line Compliance",
            format="%d%%",
            min_value=0,
            max_value=100
        ),
        'Avg Score': st.column_config.NumberColumn(
            "Quality Score",
            format="%.1f/5"
        ),
        'Status': st.column_config.TextColumn("Status")
    },
    hide_index=True,
    use_container_width=True
)

st.divider()

# Visualizations
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📏 Line Count: Actual vs Target")
    
    line_data = df.groupby('AGENT_NAME').agg({
        'ACTUAL_LINES': 'mean',
        'TARGET_MAX_LINES': 'first'
    }).reset_index()
    line_data.columns = ['Agent', 'Actual', 'Target']
    line_data = line_data[line_data['Target'].notna()]
    
    line_chart = alt.Chart(line_data).transform_fold(
        ['Actual', 'Target'],
        as_=['Metric', 'Lines']
    ).mark_bar().encode(
        x=alt.X('Agent:N', sort='-y', title='Agent'),
        y=alt.Y('Lines:Q', title='Average Lines'),
        color=alt.Color('Metric:N', scale=alt.Scale(
            domain=['Actual', 'Target'],
            range=['#ff6b6b', '#4ecdc4']
        )),
        xOffset='Metric:N'
    ).properties(height=300)
    
    st.altair_chart(line_chart, use_container_width=True)

with col_right:
    st.subheader("⭐ Quality Scores by Agent")
    
    if len(judged_df) > 0:
        score_data = judged_df.groupby('AGENT_NAME')[
            ['LENGTH_SCORE', 'FORMAT_SCORE', 'CONTENT_SCORE', 'STYLE_SCORE']
        ].mean().reset_index()
        score_data.columns = ['Agent', 'Length', 'Format', 'Content', 'Style']
        
        score_melted = score_data.melt(id_vars=['Agent'], var_name='Dimension', value_name='Score')
        
        score_chart = alt.Chart(score_melted).mark_bar().encode(
            x=alt.X('Dimension:N', title=''),
            y=alt.Y('Score:Q', scale=alt.Scale(domain=[0, 5]), title='Score (1-5)'),
            color=alt.Color('Dimension:N', legend=None),
            column=alt.Column('Agent:N', title='')
        ).properties(width=80, height=250)
        
        st.altair_chart(score_chart)
    else:
        st.info("No quality scores available")

st.divider()

# Compliance heatmap
st.subheader("🗺️ Compliance Heatmap by Agent and Query")

heatmap_data = df[['AGENT_NAME', 'QUERY_ID', 'LINE_COMPLIANT']].copy()
heatmap_data['Compliant'] = heatmap_data['LINE_COMPLIANT'].astype(int)

heatmap = alt.Chart(heatmap_data).mark_rect().encode(
    x=alt.X('QUERY_ID:N', title='Query'),
    y=alt.Y('AGENT_NAME:N', title='Agent', sort='-x'),
    color=alt.Color('Compliant:Q', 
                    scale=alt.Scale(domain=[0, 1], range=['#ff6b6b', '#4ecdc4']),
                    legend=alt.Legend(title='Compliant'))
).properties(height=350)

st.altair_chart(heatmap, use_container_width=True)

st.divider()

# Detailed results explorer
st.subheader("🔍 Detailed Results Explorer")

selected_agent = st.selectbox(
    "Select agent to explore",
    options=df['AGENT_NAME'].unique(),
    index=0
)

agent_df = df[df['AGENT_NAME'] == selected_agent]

for _, row in agent_df.iterrows():
    status_icon = "✅" if row['LINE_COMPLIANT'] else "❌"
    
    with st.expander(f"{status_icon} {row['QUERY_ID']}: {row['QUERY'][:50]}..."):
        col1, col2, col3 = st.columns(3)
        with col1:
            target = row['TARGET_MAX_LINES'] if pd.notna(row['TARGET_MAX_LINES']) else 'N/A'
            st.metric("Lines", f"{row['ACTUAL_LINES']}", delta=f"target: {target}")
        with col2:
            st.metric("Words", row['WORD_COUNT'])
        with col3:
            st.metric("Chars", row['CHAR_COUNT'])
        
        st.caption("**Response:**")
        st.code(row['RESPONSE'][:500] + "..." if len(row['RESPONSE']) > 500 else row['RESPONSE'])
        
        if pd.notna(row['JUDGE_REASONING']):
            st.caption("**Judge evaluation:**")
            scores_col1, scores_col2, scores_col3, scores_col4 = st.columns(4)
            with scores_col1:
                st.metric("Length", f"{row['LENGTH_SCORE']}/5")
            with scores_col2:
                st.metric("Format", f"{row['FORMAT_SCORE']}/5")
            with scores_col3:
                st.metric("Content", f"{row['CONTENT_SCORE']}/5")
            with scores_col4:
                st.metric("Style", f"{row['STYLE_SCORE']}/5")
            st.info(row['JUDGE_REASONING'])

st.divider()

# Footer
st.caption("Agent Verbosity Evaluation Dashboard | Data from FANCYWORKS_DEMO_DB.PUBLIC.AGENT_EVAL_RESULTS")
