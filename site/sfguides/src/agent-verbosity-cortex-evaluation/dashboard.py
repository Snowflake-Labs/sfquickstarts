#!/usr/bin/env python3
"""
Agent Verbosity Comparison Dashboard
Config-driven Streamlit app using Cortex REST API and Chat Completions.
"""

import streamlit as st
import pandas as pd
import requests
import tomllib
import json
import os
from dataclasses import dataclass
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG_PATH = Path(__file__).parent / "mcp_config.json"

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

CONFIG = load_config()

st.set_page_config(
    page_title=CONFIG["dashboard"]["title"],
    page_icon="🎯",
    layout="wide"
)

# ============================================================
# MODEL CONFIGURATION (from config)
# ============================================================
@dataclass
class ModelConfig:
    name: str
    model_id: str
    supports_thinking: bool = False

MODEL_CONFIGS = {
    key: ModelConfig(
        name=key.title(),
        model_id=cfg["model_id"],
        supports_thinking=cfg.get("supports_thinking", False)
    )
    for key, cfg in CONFIG["models"].items()
}

# ============================================================
# CORTEX REST API CLIENT
# ============================================================
class CortexRESTClient:
    def __init__(self, connection_name: str = "myusage"):
        self.connection_name = connection_name
        self._load_credentials()
    
    def _load_credentials(self):
        toml_path = os.path.expanduser("~/.snowflake/config.toml")
        with open(toml_path, "rb") as f:
            config = tomllib.load(f)
        conn = config["connections"][self.connection_name]
        self.account = conn.get("account", "")
        self.pat = conn.get("password", "")
        self.base_url = f"https://{self.account}.snowflakecomputing.com"
    
    def complete(self, model: str, messages: list, **kwargs) -> dict:
        url = f"{self.base_url}/api/v2/cortex/inference:complete"
        headers = {"Authorization": f"Bearer {self.pat}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, **kwargs}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def chat_completions(self, model: str, messages: list, **kwargs) -> dict:
        url = f"{self.base_url}/api/v2/cortex/chat/completions"
        headers = {"Authorization": f"Bearer {self.pat}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": messages, **kwargs}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    
    def chat_completions_with_thinking(self, model: str, messages: list, thinking_budget: int = 8000) -> dict:
        url = f"{self.base_url}/api/v2/cortex/chat/completions"
        headers = {"Authorization": f"Bearer {self.pat}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 1.0,
            "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
            "stream": True
        }
        response = requests.post(url, headers=headers, json=payload, stream=True)
        return self._parse_streaming_response(response)
    
    def _parse_streaming_response(self, response) -> dict:
        thinking_content = ""
        response_content = ""
        usage = {}
        
        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            if line.strip() == "data: [DONE]":
                break
            try:
                data = json.loads(line[6:])
                for choice in data.get("choices", []):
                    delta = choice.get("delta", {})
                    if "thinking" in delta:
                        thinking_content += delta.get("thinking", "")
                    if "content" in delta:
                        response_content += delta.get("content", "")
                if "usage" in data:
                    usage = data["usage"]
            except json.JSONDecodeError:
                continue
        
        return {
            "response": response_content,
            "thinking": thinking_content,
            "usage": usage
        }

# Initialize client
@st.cache_resource
def get_client():
    return CortexRESTClient()

client = get_client()

# ============================================================
# VERBOSITY CONFIGURATION (from config)
# ============================================================
VERBOSITY_CONFIG = CONFIG["verbosity_levels"]

# ============================================================
# MCP CLIENT
# ============================================================
def call_mcp(server_name: str, endpoint: str, method: str = "GET", **params) -> dict:
    """Call an MCP server endpoint."""
    port = CONFIG["mcp_servers"][server_name]["port"]
    url = f"http://localhost:{port}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=5)
        else:
            response = requests.post(url, params=params, timeout=5)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# DASHBOARD UI
# ============================================================
st.title("🎯 " + CONFIG["dashboard"]["title"])
st.markdown(f"Compare models using **Cortex REST API** and **Chat Completions**")

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Services")
    st.markdown(f"**Dashboard**: `localhost:{CONFIG['dashboard']['port']}`")
    for name, cfg in CONFIG["mcp_servers"].items():
        st.markdown(f"**{name}**: `localhost:{cfg['port']}`")
    
    st.divider()
    
    st.subheader("Models")
    selected_models = st.multiselect(
        "Select models",
        list(MODEL_CONFIGS.keys()),
        default=list(MODEL_CONFIGS.keys()),
        format_func=lambda k: f"{MODEL_CONFIGS[k].name} ({MODEL_CONFIGS[k].model_id})"
    )
    
    st.subheader("Verbosity Levels")
    selected_verbosities = st.multiselect(
        "Select levels",
        list(VERBOSITY_CONFIG.keys()),
        default=["minimal", "brief", "standard"]
    )

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Comparison", "🧠 Extended Thinking", "🔬 MCP Services", "📈 Results"])

# ============================================================
# TAB 1: Verbosity Comparison
# ============================================================
with tab1:
    st.header("Cross-Model Verbosity Comparison")
    
    query = st.text_area("Enter your query:", value="What is SQL injection and how do you prevent it?", height=100)
    
    if st.button("🚀 Run Comparison", type="primary"):
        results = []
        
        progress = st.progress(0)
        total = len(selected_models) * len(selected_verbosities)
        i = 0
        
        for verbosity in selected_verbosities:
            row = {"verbosity": verbosity}
            
            for model_key in selected_models:
                config = MODEL_CONFIGS[model_key]
                system_prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_CONFIG[verbosity]['prompt']}"
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
                
                try:
                    result = client.complete(config.model_id, messages)
                    answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    usage = result.get("usage", {})
                    
                    lines = len(answer.strip().split("\n"))
                    max_lines = VERBOSITY_CONFIG[verbosity]["max_lines"]
                    
                    row[f"{model_key}_lines"] = lines
                    row[f"{model_key}_compliant"] = "✅" if lines <= max_lines else "❌"
                    row[f"{model_key}_tokens"] = usage.get("total_tokens", 0)
                except Exception as e:
                    row[f"{model_key}_lines"] = 0
                    row[f"{model_key}_compliant"] = "❌"
                    row[f"{model_key}_tokens"] = 0
                
                i += 1
                progress.progress(i / total)
            
            results.append(row)
        
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # Compliance summary
        st.subheader("Compliance Summary")
        cols = st.columns(len(selected_models))
        for idx, model_key in enumerate(selected_models):
            with cols[idx]:
                compliant_count = sum(1 for r in results if r[f"{model_key}_compliant"] == "✅")
                rate = (compliant_count / len(results)) * 100 if results else 0
                st.metric(MODEL_CONFIGS[model_key].name, f"{rate:.0f}%")

# ============================================================
# TAB 2: Extended Thinking
# ============================================================
with tab2:
    st.header("🧠 Extended Thinking (Chat Completions)")
    
    thinking_models = [k for k, v in MODEL_CONFIGS.items() if v.supports_thinking]
    
    if not thinking_models:
        st.warning("No models with extended thinking support configured.")
    else:
        selected_thinking_model = st.selectbox(
            "Select model",
            thinking_models,
            format_func=lambda k: f"{MODEL_CONFIGS[k].name} ({MODEL_CONFIGS[k].model_id})"
        )
        
        thinking_budget = st.slider("Thinking Budget (tokens)", 1000, 16000, 8000, step=1000)
        
        thinking_query = st.text_area(
            "Enter your query:",
            value="Explain the security implications of SQL injection and provide a secure code example.",
            height=100,
            key="thinking_query"
        )
        
        if st.button("🧠 Run with Extended Thinking", type="primary"):
            config = MODEL_CONFIGS[selected_thinking_model]
            
            messages = [{"role": "user", "content": thinking_query}]
            
            with st.spinner("Thinking..."):
                try:
                    result = client.chat_completions_with_thinking(
                        config.model_id,
                        messages,
                        thinking_budget=thinking_budget
                    )
                    
                    # Display thinking
                    if result.get("thinking"):
                        with st.expander("💭 Thinking Process", expanded=True):
                            st.markdown(result["thinking"])
                    
                    # Display response
                    st.subheader("📝 Response")
                    st.markdown(result.get("response", "No response"))
                    
                    # Display usage
                    usage = result.get("usage", {})
                    if usage:
                        st.subheader("📊 Chat Completions Usage")
                        cols = st.columns(4)
                        with cols[0]:
                            st.metric("Prompt Tokens", f"{usage.get('prompt_tokens', 0):,}")
                        with cols[1]:
                            st.metric("Completion Tokens", f"{usage.get('completion_tokens', 0):,}")
                        with cols[2]:
                            st.metric("Reasoning Tokens", f"{usage.get('reasoning_tokens', 0):,}")
                        with cols[3]:
                            total = usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0)
                            est_cost = (usage.get('prompt_tokens', 0) * 0.003 + usage.get('completion_tokens', 0) * 0.015) / 1000
                            st.metric("Est. Cost", f"${est_cost:.4f}")
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ============================================================
# TAB 3: MCP Services
# ============================================================
with tab3:
    st.header("🔬 MCP Services")
    
    mcp_tabs = st.tabs(list(CONFIG["mcp_servers"].keys()))
    
    for idx, (server_name, server_cfg) in enumerate(CONFIG["mcp_servers"].items()):
        with mcp_tabs[idx]:
            st.subheader(f"{server_name}")
            st.markdown(f"**Port**: {server_cfg['port']} | **Description**: {server_cfg['description']}")
            
            # Health check
            health = call_mcp(server_name, "/health")
            if "error" in health:
                st.error(f"❌ Server not running: {health['error']}")
            else:
                st.success(f"✅ Server healthy")
            
            # Server-specific UI
            if server_name == "WikiMCP":
                wiki_query = st.text_input("Search Wikipedia:", key=f"wiki_{idx}")
                if st.button("Search", key=f"wiki_btn_{idx}"):
                    result = call_mcp("WikiMCP", "/search", query=wiki_query, limit=5)
                    st.json(result)
            
            elif server_name == "VerbosityMCP":
                test_response = st.text_area("Test response:", key=f"verb_{idx}")
                test_level = st.selectbox("Verbosity level:", list(VERBOSITY_CONFIG.keys()), key=f"verb_lvl_{idx}")
                if st.button("Evaluate", key=f"verb_btn_{idx}"):
                    result = call_mcp("VerbosityMCP", "/evaluate", method="POST", response=test_response, verbosity_level=test_level)
                    st.json(result)
            
            elif server_name == "ABTestMCP":
                st.markdown("**Create Experiment**")
                exp_name = st.text_input("Experiment name:", value="verbosity_test", key=f"ab_name_{idx}")
                if st.button("Create", key=f"ab_btn_{idx}"):
                    result = call_mcp("ABTestMCP", "/experiment/create", method="POST",
                                     name=exp_name, variants="minimal,brief,standard", traffic_split="0.33,0.33,0.34")
                    st.json(result)

# ============================================================
# TAB 4: Results History
# ============================================================
with tab4:
    st.header("📈 Results & Analytics")
    st.info("Results history will be stored in Snowflake tables for persistent analytics.")
    
    st.markdown("""
    ### Planned Features:
    - Store comparison results in `CORTEX_DB.AGENTS.VERBOSITY_RESULTS`
    - Track compliance trends over time
    - Model performance benchmarks
    - Token usage analytics
    """)

# Footer
st.divider()
st.markdown(f"**Dashboard Port**: {CONFIG['dashboard']['port']} | **Config**: `mcp_config.json`")
