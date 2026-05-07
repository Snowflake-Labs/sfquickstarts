import json
import httpx
import streamlit as st

GATEWAY_URL = "http://localhost:8000"

TENANTS = {
    "User Alpha": {
        "api_key": "sk-alpha-secret-key-001",
        "models": ["claude-4-sonnet", "mistral-large2", "openai-gpt-4.1"],
    },
    "User Beta": {
        "api_key": "sk-beta-secret-key-001",
        "models": ["openai-gpt-4.1", "llama3.1-70b", "deepseek-r1", "claude-4-sonnet"],
    },
}

with st.sidebar:
    tenant_name = st.selectbox("Tenant", list(TENANTS.keys()))
    tenant = TENANTS[tenant_name]
    model = st.selectbox("Model", tenant["models"])
    st.divider()
    if st.button("Describe Snowflake in 1 sentence"):
        st.session_state["prefill"] = "Describe Snowflake in 1 sentence"
        st.rerun()
    if st.button("Clear Chat"):
        st.session_state.pop("messages", None)
        st.session_state.pop("prefill", None)
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := (st.session_state.pop("prefill", None) or st.chat_input("Ask anything...")):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        payload = {
            "messages": st.session_state.messages,
            "model": model,
            "max_tokens": 4096,
        }
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": tenant["api_key"],
        }

        with httpx.stream(
            "POST",
            f"{GATEWAY_URL}/v1/chat/stream",
            json=payload,
            headers=headers,
            timeout=60.0,
        ) as response:
            current_event = ""
            for line in response.iter_lines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith("event:"):
                    current_event = line[len("event:"):].strip()
                elif line.startswith("data:"):
                    data = json.loads(line[len("data:"):].strip())
                    if current_event == "delta":
                        full_response += data.get("content", "")
                        placeholder.markdown(full_response + "▌")
                    elif current_event == "error":
                        st.error(f"Error: {data.get('message', 'Unknown error')}")
                        break

        placeholder.markdown(full_response)

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
