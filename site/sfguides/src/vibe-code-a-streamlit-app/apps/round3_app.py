import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Explorer", page_icon="📊", layout="wide")

st.title("📊 Data Explorer")

with st.sidebar:
    st.markdown("### Upload Data")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    st.markdown("### About")
    st.info("This is a simple data explorer app. Upload a CSV file to view its contents.")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.metric("Rows", df.shape[0])
        with col2:
            with st.container(border=True):
                st.metric("Columns", df.shape[1])
            
        st.write("### Data Preview")
        st.dataframe(df, use_container_width=True)
        
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if len(numeric_columns) > 0:
            st.write("### Data Visualization")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                chart_type = st.selectbox("Select Chart Type", options=["Bar", "Line", "Scatter"])
            with col2:
                x_axis = st.selectbox("Select X-Axis", options=df.columns.tolist())
            with col3:
                y_axis = st.selectbox("Select Y-Axis", options=numeric_columns)
            
            chart_data = pd.DataFrame({x_axis: df[x_axis], y_axis: df[y_axis]}).set_index(x_axis)
            
            st.write(f"#### {y_axis} by {x_axis}")
            if chart_type == "Bar":
                st.bar_chart(chart_data, use_container_width=True, height=500)
            elif chart_type == "Line":
                st.line_chart(chart_data, use_container_width=True, height=500)
            else:
                st.scatter_chart(chart_data, use_container_width=True, height=500)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👈 Please upload a CSV file using the sidebar to begin.")
