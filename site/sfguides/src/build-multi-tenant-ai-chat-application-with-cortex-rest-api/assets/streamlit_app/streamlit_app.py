import streamlit as st

st.set_page_config(page_title="CoCo AI Chat", page_icon="🤖", layout="wide")

chat_page = st.Page("app_pages/chat.py", title="AI Chat", icon="💬", default=True)
st.navigation([chat_page]).run()
