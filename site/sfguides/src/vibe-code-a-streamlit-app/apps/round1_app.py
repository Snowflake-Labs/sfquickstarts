import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Explorer")

st.title("Data Explorer")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.dataframe(df)
else:
    st.info("Upload a CSV file to get started.")
