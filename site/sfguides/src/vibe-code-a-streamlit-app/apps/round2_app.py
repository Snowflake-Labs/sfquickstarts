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
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👈 Please upload a CSV file using the sidebar to begin.")
