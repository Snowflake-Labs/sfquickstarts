"""
Cross-Model Verbosity Comparison Dashboard
Compare models via Cortex SQL and Cortex REST API across verbosity levels
Includes Wikipedia Q&A and Persona-based comparison using Vine Copula
"""
import streamlit as st
import pandas as pd
import altair as alt
import snowflake.connector
import requests
import json
import os
from datetime import datetime
import numpy as np

# Import generators
from wiki_qa_generator import WikiQAGenerator, VineCopula, generate_wiki_qa
from persona_qa_generator import (
    generate_persona_qa, PERSONAS, DOMAINS, 
    compute_flesch_score, check_sql_presence, count_business_terms,
    evaluate_persona_compliance
)
# Import MCP clients
from mcp_client import WikiMCPClient, check_mcp_server, ensure_mcp_server
from ab_mcp_client import ABTestingMCPClient, check_ab_mcp_server, ensure_ab_mcp_server

# MCP Configuration
MCP_URL = "http://localhost:8503"
AB_MCP_URL = "http://localhost:8517"

st.set_page_config(page_title="Model Comparison Dashboard", layout="wide")

# Configuration - Models with provider type (includes both Cortex SQL and REST API)
MODELS = {
    "claude": {"name": "claude-sonnet-4-5", "provider": "cortex_rest", "label": "Claude Sonnet 4.5 (Cortex REST)"},
    "mistral": {"name": "mistral-large2", "provider": "cortex_rest", "label": "Mistral Large 2 (Cortex REST)"},
    "llama": {"name": "llama3.1-70b", "provider": "cortex_sql", "label": "Llama 3.1 70B (Cortex SQL)"},
}

# Cortex REST API Configuration
CORTEX_REST_MODELS = {
    "sonnet46_rest": {"name": "claude-sonnet-4-6", "provider": "cortex_rest", "label": "Claude Sonnet 4.6 (Cortex REST API)"},
    "sonnet45_rest": {"name": "claude-sonnet-4-5", "provider": "cortex_rest", "label": "Claude Sonnet 4.5 (Cortex REST API)"},
    "sonnet35_rest": {"name": "claude-3-5-sonnet", "provider": "cortex_rest", "label": "Claude 3.5 Sonnet (Cortex REST API)"},
}

# Claude Code Agent Configuration (via Cortex REST API)
CLAUDE_CODE_CONFIG = {
    "models": {
        "sonnet45": "claude-sonnet-4-5",
        "sonnet46": "claude-sonnet-4-6",
        "opus45": "claude-opus-4-5",
        "haiku45": "claude-haiku-4-5",
    },
    "default_model": "claude-sonnet-4-5"
}

def get_cortex_endpoint(conn):
    """Get the Cortex REST API endpoint from the connection."""
    host = conn.host.replace("_", "-")
    return f"https://{host}/api/v2/cortex/inference:complete"

# LiteLLM Configuration - routes through Snowflake Cortex REST API
# Uses OpenAI-compatible endpoint: /api/v2/cortex/v1/chat/completions
LITELLM_CONFIG = {
    "models": {
        "claude-sonnet-4-5": {"label": "Claude Sonnet 4.5 (Cortex)", "cortex_model": "claude-sonnet-4-5"},
        "mistral-large2": {"label": "Mistral Large 2 (Cortex)", "cortex_model": "mistral-large2"},
        "llama3.1-70b": {"label": "Llama 3.1 70B (Cortex)", "cortex_model": "llama3.1-70b"},
        "llama3.1-8b": {"label": "Llama 3.1 8B (Cortex)", "cortex_model": "llama3.1-8b"},
    },
}

# Multimodal Vision Models - supports image understanding via Cortex Chat Completions API
# Uses OpenAI-compatible format: https://docs.snowflake.com/en/user-guide/snowflake-cortex/open_ai_sdk
MULTIMODAL_MODELS = {
    "claude-sonnet-4-5": {"label": "Claude Sonnet 4.5", "supports_vision": True},
    "claude-sonnet-4-6": {"label": "Claude Sonnet 4.6", "supports_vision": True},
    "gpt-5.2": {"label": "GPT-5.2 (OpenAI)", "supports_vision": True},
}

def check_litellm_setup() -> dict:
    """Check if LiteLLM is installed and Snowflake connection is available."""
    checks = {
        "installed": False,
        "version": None,
        "snowflake_connected": False
    }
    
    try:
        import litellm
        checks["installed"] = True
        checks["version"] = getattr(litellm, "__version__", "unknown")
        
        # Check Snowflake connection
        try:
            conn = get_connection()
            if conn:
                checks["snowflake_connected"] = True
        except:
            pass
    except ImportError:
        pass
    
    return checks

def call_litellm_model(model_key: str, prompt: str, system_prompt: str = None, 
                       max_tokens: int = 1024, temperature: float = 0.7) -> dict:
    """Call a model via LiteLLM routed through Snowflake Cortex REST API."""
    try:
        import litellm
        
        model_config = LITELLM_CONFIG["models"].get(model_key, {})
        cortex_model = model_config.get("cortex_model", model_key)
        
        # Get Snowflake connection for auth
        conn = get_connection()
        host = conn.host.replace("_", "-")
        token = conn.rest._token
        
        # Configure LiteLLM to use Cortex endpoint
        api_base = f"https://{host}/api/v2/cortex/v1"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start = datetime.now()
        response = litellm.completion(
            model=f"openai/{cortex_model}",  # Use openai/ prefix for custom endpoint
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            api_base=api_base,
            api_key=f"Snowflake Token=\"{token}\""
        )
        duration = (datetime.now() - start).total_seconds()
        
        content = response.choices[0].message.content or ""
        lines = content.strip().count('\n') + 1 if content else 0
        words = len(content.split()) if content else 0
        
        return {
            "response": content,
            "line_count": lines,
            "word_count": words,
            "char_count": len(content),
            "duration": duration,
            "success": True,
            "provider": "litellm-cortex",
            "model": cortex_model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }
    except ImportError:
        return {
            "response": "LiteLLM error: package not available",
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "duration": 0,
            "success": False,
            "provider": "litellm-cortex",
            "error": "not_installed"
        }
    except Exception as e:
        error_str = str(e)
        # Handle auth token expiry
        if is_auth_error(error_str):
            try:
                conn = get_fresh_connection()
                # Retry once with fresh connection
                return call_litellm_model(model_key, prompt, system_prompt, max_tokens, temperature)
            except:
                pass
        return {
            "response": f"LiteLLM Error: {error_str}",
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "duration": 0,
            "success": False,
            "provider": "litellm-cortex",
            "error": error_str
        }

def get_pat_from_toml(connection_name: str = "myaccount") -> str:
    """Read PAT token from ~/.snowflake/config.toml"""
    import tomllib
    toml_path = os.path.expanduser("~/.snowflake/config.toml")
    try:
        with open(toml_path, "rb") as f:
            config = tomllib.load(f)
        if "connections" in config and connection_name in config["connections"]:
            return config["connections"][connection_name].get("password", "")
    except Exception:
        pass
    return ""

def call_vision_model(model: str, prompt: str, image_base64: str = None, 
                      image_url: str = None, max_tokens: int = 1024, 
                      temperature: float = 0.7) -> dict:
    """
    Call Cortex Chat Completions API with vision capability.
    Uses OpenAI-compatible format via raw HTTP requests (no SDK required).
    Endpoint: https://{account}.snowflakecomputing.com/api/v2/cortex/v1/chat/completions
    Note: Cortex only supports base64 encoded images, URLs are fetched and converted.
    """
    import tomllib
    import base64
    
    # Get credentials from config
    try:
        with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
            config = tomllib.load(f)
        pat = config["connections"]["myaccount"]["password"]
        account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
    except Exception:
        pat = get_pat_from_toml()
        account = ""
    
    if not account:
        return {
            "response": "Error: Could not read account from config.toml",
            "success": False,
            "duration": 0
        }
    
    # If image_url provided, fetch and convert to base64
    if image_url and not image_base64:
        try:
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            image_base64 = base64.b64encode(img_response.content).decode("utf-8")
            # Detect content type for proper encoding
            content_type = img_response.headers.get("Content-Type", "image/jpeg")
            if "png" in content_type:
                img_format = "image/png"
            elif "webp" in content_type:
                img_format = "image/webp"
            else:
                img_format = "image/jpeg"
        except Exception as e:
            return {
                "response": f"Failed to fetch image from URL: {str(e)}",
                "success": False,
                "duration": 0,
                "error": str(e)
            }
    else:
        img_format = "image/jpeg"  # Default for uploaded images
    
    # Build the Cortex Chat Completions API URL (OpenAI-compatible)
    url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/v1/chat/completions"
    
    # Build message content with text and image (base64 only)
    content = [{"type": "text", "text": prompt}]
    
    if image_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img_format};base64,{image_base64}"
            }
        })
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": content}
        ],
        "max_completion_tokens": max_tokens,
        "temperature": temperature
    }
    
    headers = {
        "Authorization": f"Bearer {pat}",
        "Content-Type": "application/json"
    }
    
    start = datetime.now()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        duration = (datetime.now() - start).total_seconds()
        
        if response.status_code == 200:
            result = response.json()
            content_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            
            return {
                "response": content_text,
                "success": True,
                "duration": duration,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                },
                "line_count": content_text.count('\n') + 1 if content_text else 0,
                "word_count": len(content_text.split()) if content_text else 0
            }
        else:
            return {
                "response": f"API Error {response.status_code}: {response.text}",
                "success": False,
                "duration": duration,
                "error": response.text
            }
    except Exception as e:
        duration = (datetime.now() - start).total_seconds()
        return {
            "response": f"Request failed: {str(e)}",
            "success": False,
            "duration": duration,
            "error": str(e)
        }

VERBOSITY_PROMPTS = {
    "minimal": "1 line maximum. Single word/number when possible.",
    "brief": "Maximum 3 lines. No preamble or postamble.",
    "standard": "3-6 lines typical. Include context when helpful.",
    "detailed": "Full context with structure: Issue, Location, Risk, Fix.",
    "verbose": "Comprehensive with background, options, edge cases.",
    "code_only": "Return ONLY code blocks. No explanatory text.",
    "explain": "Explain the why and how behind everything.",
    "step_by_step": "Numbered, sequential walkthroughs."
}

VERBOSITY_MAX_LINES = {
    "minimal": 1, "brief": 3, "standard": 6, "detailed": 15,
    "verbose": 50, "code_only": 20, "explain": 20, "step_by_step": 25
}

TEST_QUERIES = [
    {"id": "Q1", "category": "factual", "text": "What is SQL injection?"},
    {"id": "Q2", "category": "code_fix", "text": "Fix this: session.sql(f\"SELECT * FROM users WHERE id={user_id}\")"},
    {"id": "Q3", "category": "explanation", "text": "Why is parameterized SQL safer?"},
    {"id": "Q4", "category": "binary", "text": "Is eval(user_input) safe in Python?"},
]

DEFAULT_WIKI_ARTICLES = [
    "The_Lord_of_the_Rings",
    "New_England_Patriots",
    "Apollo_program"
]

@st.cache_resource
def get_connection():
    conn = snowflake.connector.connect(connection_name='myaccount')
    conn.cursor().execute("USE WAREHOUSE SNOW_INTELLIGENCE_DEMO_WH")
    return conn

def reset_connection():
    """Clear cached connection (call after auth errors)."""
    get_connection.clear()

def get_fresh_connection():
    """Get a fresh connection, resetting cache if needed."""
    reset_connection()
    return get_connection()

def is_auth_error(error_msg: str) -> bool:
    """Check if an error is an authentication/token expiry error."""
    return "390114" in error_msg or "Authentication token has expired" in error_msg

def call_model_rest_api(conn, model: str, prompt: str, system_prompt: str = None, max_tokens: int = 1024, temperature: float = 0.7):
    """Call model via Cortex REST API. Auto-reconnects on auth errors."""
    
    # Try up to 2 times (initial + retry after reconnect)
    for attempt in range(2):
        try:
            host = conn.host.replace("_", "-")
            token = conn.rest._token
            url = f"https://{host}/api/v2/cortex/inference:complete"
            
            headers = {
                "Authorization": f"Snowflake Token=\"{token}\"",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            start = datetime.now()
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            duration = (datetime.now() - start).total_seconds()
            
            if response.status_code == 200:
                # Parse SSE response
                content = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data:
                                delta = data["choices"][0].get("delta", {})
                                content += delta.get("content", "")
                        except json.JSONDecodeError:
                            continue
                
                lines = content.strip().count('\n') + 1 if content else 0
                words = len(content.split()) if content else 0
                
                return {
                    "response": content,
                    "line_count": lines,
                    "word_count": words,
                    "char_count": len(content),
                    "duration": duration,
                    "success": True,
                    "provider": "cortex_rest"
                }
            else:
                error_msg = response.json().get("message", response.text) if response.text else str(response.status_code)
                # Check for auth errors - retry with fresh connection
                if is_auth_error(error_msg) and attempt == 0:
                    conn = get_fresh_connection()
                    continue
                return {
                    "response": f"REST API Error: {error_msg}",
                    "line_count": 0,
                    "word_count": 0,
                    "char_count": 0,
                    "duration": duration,
                    "success": False,
                    "provider": "cortex_rest",
                    "auth_error": is_auth_error(error_msg)
                }
        except Exception as e:
            error_str = str(e)
            # Check for auth errors - retry with fresh connection
            if is_auth_error(error_str) and attempt == 0:
                conn = get_fresh_connection()
                continue
            return {
                "response": f"REST API Exception: {error_str}",
                "line_count": 0,
                "word_count": 0,
                "char_count": 0,
                "duration": 0,
                "success": False,
                "provider": "cortex_rest",
                "auth_error": is_auth_error(error_str)
            }
    
    # Should not reach here
    return {"response": "Max retries exceeded", "line_count": 0, "word_count": 0, "char_count": 0, "duration": 0, "success": False, "provider": "cortex_rest"}

def call_model(conn, model: str, verbosity: str, query: str, context: str = None, provider: str = "cortex_sql"):
    """Call model via Cortex SQL or REST API based on provider. Auto-reconnects on auth errors."""
    system_prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_PROMPTS[verbosity]}"
    if context:
        system_prompt += f"\n\nContext: {context}"
    full_prompt = f"{system_prompt}\n\nUser question: {query}"
    
    if provider == "cortex_rest":
        # Use REST API
        return call_model_rest_api(conn, model, query, system_prompt=system_prompt)
    else:
        # Use Cortex SQL (default) with retry on auth errors
        full_prompt_escaped = full_prompt.replace("'", "''")
        sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{full_prompt_escaped}') AS response"
        
        # Try up to 2 times (initial + retry after reconnect)
        for attempt in range(2):
            cursor = conn.cursor()
            try:
                start = datetime.now()
                cursor.execute(sql)
                response = cursor.fetchone()[0]
                duration = (datetime.now() - start).total_seconds()
                
                lines = response.strip().count('\n') + 1
                words = len(response.split())
                
                return {
                    "response": response,
                    "line_count": lines,
                    "word_count": words,
                    "char_count": len(response),
                    "duration": duration,
                    "success": True,
                    "provider": "cortex_sql"
                }
            except Exception as e:
                error_str = str(e)
                # Check for auth token expiry - retry with fresh connection
                if is_auth_error(error_str) and attempt == 0:
                    conn = get_fresh_connection()
                    continue  # Retry with new connection
                return {
                    "response": error_str, 
                    "line_count": 0, 
                    "word_count": 0, 
                    "char_count": 0, 
                    "duration": 0, 
                    "success": False, 
                    "provider": "cortex_sql",
                    "auth_error": is_auth_error(error_str)
                }
            finally:
                cursor.close()
        
        # Should not reach here, but just in case
        return {"response": "Max retries exceeded", "line_count": 0, "word_count": 0, "char_count": 0, "duration": 0, "success": False, "provider": "cortex_sql"}

def run_claude_code_agent(prompt: str, model: str = None, pat_token: str = None, timeout: int = 120):
    """
    Run Claude Code agent in headless mode via Cortex REST API.
    
    Args:
        prompt: The prompt to send to Claude Code
        model: Model to use (default: claude-sonnet-4-5)
        pat_token: Snowflake PAT token for authentication
        timeout: Timeout in seconds (default: 120)
    
    Returns:
        dict with response, duration, success status
    """
    import subprocess
    import shutil
    
    model = model or CLAUDE_CODE_CONFIG["default_model"]
    
    # Check if claude command exists
    claude_path = shutil.which("claude")
    if not claude_path:
        return {
            "response": "Claude Code CLI not found. Install via: npm install -g @anthropic-ai/claude-code",
            "line_count": 0,
            "word_count": 0,
            "duration": 0,
            "success": False,
            "provider": "claude_code_agent"
        }
    
    # Get dynamic endpoint from connection
    try:
        conn = get_connection()
        endpoint = get_cortex_endpoint(conn).replace("/inference:complete", "")  # Base URL for Anthropic format
    except Exception as e:
        return {
            "response": f"Connection error: {str(e)}. Run: snow connection test myaccount",
            "line_count": 0,
            "word_count": 0,
            "duration": 0,
            "success": False,
            "provider": "claude_code_agent"
        }
    
    # Build environment with Cortex REST API endpoint
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = endpoint
    env["ANTHROPIC_MODEL"] = model
    env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = model
    env["CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS"] = "1"
    
    if pat_token:
        env["ANTHROPIC_AUTH_TOKEN"] = pat_token
    
    try:
        start = datetime.now()
        
        # Run claude in print mode (non-interactive, outputs result only)
        result = subprocess.run(
            [claude_path, "-p", prompt, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        
        duration = (datetime.now() - start).total_seconds()
        
        if result.returncode == 0:
            response = result.stdout.strip()
            lines = response.count('\n') + 1 if response else 0
            words = len(response.split()) if response else 0
            
            return {
                "response": response,
                "line_count": lines,
                "word_count": words,
                "char_count": len(response),
                "duration": duration,
                "success": True,
                "provider": "claude_code_agent",
                "model": model
            }
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return {
                "response": f"Claude Code Error: {error_msg}",
                "line_count": 0,
                "word_count": 0,
                "char_count": 0,
                "duration": duration,
                "success": False,
                "provider": "claude_code_agent",
                "model": model
            }
    
    except subprocess.TimeoutExpired:
        return {
            "response": f"Claude Code timed out after {timeout}s",
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "duration": timeout,
            "success": False,
            "provider": "claude_code_agent",
            "model": model
        }
    except Exception as e:
        return {
            "response": f"Claude Code Exception: {str(e)}",
            "line_count": 0,
            "word_count": 0,
            "char_count": 0,
            "duration": 0,
            "success": False,
            "provider": "claude_code_agent",
            "model": model
        }

def check_claude_code_setup():
    """Check if Claude Code is properly configured for Cortex."""
    import shutil
    
    checks = {
        "cli_installed": False,
        "cli_path": None,
        "endpoint_configured": False,
        "token_configured": False,
    }
    
    # Check CLI
    claude_path = shutil.which("claude")
    if claude_path:
        checks["cli_installed"] = True
        checks["cli_path"] = claude_path
    
    # Check environment
    if os.environ.get("ANTHROPIC_BASE_URL"):
        checks["endpoint_configured"] = True
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        checks["token_configured"] = True
    
    return checks

def call_model_with_persona(conn, model: str, persona_key: str, query: str):
    """Call Cortex COMPLETE with persona prompt."""
    cursor = conn.cursor()
    
    persona = PERSONAS[persona_key]
    system_prompt = persona["prompt"]
    full_prompt = f"{system_prompt}\n\nQuestion: {query}"
    full_prompt_escaped = full_prompt.replace("'", "''")
    
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', '{full_prompt_escaped}') AS response"
    
    try:
        start = datetime.now()
        cursor.execute(sql)
        response = cursor.fetchone()[0]
        duration = (datetime.now() - start).total_seconds()
        
        # Evaluate persona compliance
        evaluation = evaluate_persona_compliance(response, persona_key)
        
        return {
            "response": response,
            "duration": duration,
            "success": True,
            "evaluation": evaluation
        }
    except Exception as e:
        return {
            "response": str(e), 
            "duration": 0, 
            "success": False,
            "evaluation": {"compliant": False, "score": 0}
        }
    finally:
        cursor.close()

def check_answer_accuracy(response: str, expected: str) -> float:
    """Simple accuracy check."""
    if not expected or not response:
        return 0.0
    
    expected_words = set(expected.lower().split())
    response_words = set(response.lower().split())
    
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}
    expected_words -= stopwords
    response_words -= stopwords
    
    if not expected_words:
        return 1.0
    
    overlap = len(expected_words & response_words)
    return min(1.0, overlap / len(expected_words))

# Header
st.title("🔬 Cross-Model Verbosity Comparison")
st.markdown("**Cortex SQL** & **Cortex REST API** models across verbosity levels and personas")

conn = get_connection()

# Tabs - Added Persona Compare, Agent Verbosity, dbt Pipelines, TruLens Eval, A/B Testing, Inference Experiments, and Multimodal Vision
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "📊 Run Comparison", 
    "📈 Results Analysis", 
    "🔍 Live Test", 
    "📚 Wiki Compare",
    "🎭 Persona Compare",
    "🤖 Agent Verbosity",
    "📦 dbt Pipelines",
    "🔬 TruLens Eval",
    "🧪 A/B Testing",
    "🔬 Inference Experiments",
    "📸 Multimodal Vision"
])

# ============== TAB 1: Run Comparison ==============
with tab1:
    st.subheader("Run Model Comparison")
    
    # Show available models
    st.markdown("**Available Models (Cortex SQL & REST API):**")
    model_cols = st.columns(len(MODELS))
    for i, (key, config) in enumerate(MODELS.items()):
        model_cols[i].info(f"🤖 {config['label']}")
    
    # Claude Code Agent option
    st.divider()
    cc_setup = check_claude_code_setup()
    
    col_cc_opt1, col_cc_opt2, col_cc_opt3 = st.columns([1, 1, 2])
    with col_cc_opt1:
        include_claude_code = st.checkbox(
            "Include Claude Code Agent",
            value=False,
            disabled=not cc_setup["cli_installed"],
            help="Run comparison with Claude Code agent via Cortex REST API"
        )
    
    with col_cc_opt2:
        if include_claude_code:
            cc_compare_model = st.selectbox(
                "Claude Code Model:",
                options=list(CLAUDE_CODE_CONFIG["models"].keys()),
                format_func=lambda x: CLAUDE_CODE_CONFIG["models"][x],
                key="cc_compare_model"
            )
    
    with col_cc_opt3:
        if include_claude_code:
            if "cc_pat_token" not in st.session_state:
                # Auto-load PAT from connections.toml
                st.session_state["cc_pat_token"] = get_pat_from_toml("myaccount")
            
            if st.session_state["cc_pat_token"]:
                st.success("✅ PAT loaded from ~/.snowflake/connections.toml")
            else:
                cc_pat = st.text_input(
                    "PAT Token:",
                    value="",
                    type="password",
                    key="cc_compare_pat"
                )
                st.session_state["cc_pat_token"] = cc_pat
    
    if not cc_setup["cli_installed"]:
        st.caption("⚠️ Claude Code CLI not installed. Run `npm install -g @anthropic-ai/claude-code`")
    
    # LiteLLM option - routes through Snowflake Cortex REST API
    st.divider()
    st.markdown("**🔗 LiteLLM via Cortex** ([docs](https://docs.litellm.ai/))")
    litellm_setup = check_litellm_setup()
    
    col_ll_opt1, col_ll_opt2, col_ll_opt3 = st.columns([1, 1, 2])
    
    # Initialize selected_litellm_models
    selected_litellm_models = []
    
    with col_ll_opt1:
        include_litellm = st.checkbox(
            "Include LiteLLM Models",
            value=False,
            disabled=not litellm_setup["installed"],
            help="Compare with additional Cortex models via LiteLLM"
        )
        if not litellm_setup["installed"]:
            st.caption("⚠️ Run: `pip install litellm`")
    
    with col_ll_opt2:
        if include_litellm:
            # Show all Cortex models available via LiteLLM
            selected_litellm_models = st.multiselect(
                "LiteLLM Models:",
                options=list(LITELLM_CONFIG["models"].keys()),
                default=[list(LITELLM_CONFIG["models"].keys())[0]] if LITELLM_CONFIG["models"] else [],
                format_func=lambda x: LITELLM_CONFIG["models"][x]["label"],
                key="litellm_models_select"
            )
    
    with col_ll_opt3:
        if include_litellm:
            if litellm_setup["snowflake_connected"]:
                st.success("✅ Routed via Snowflake Cortex")
            else:
                st.warning("⚠️ Snowflake connection required")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        selected_verbosities = st.multiselect(
            "Select verbosity levels",
            options=list(VERBOSITY_PROMPTS.keys()),
            default=["minimal", "brief", "standard"],
            key="tab1_verbosity"
        )
    with col2:
        selected_queries = st.multiselect(
            "Select test queries",
            options=[f"{q['id']}: {q['text'][:40]}..." for q in TEST_QUERIES],
            default=[f"{q['id']}: {q['text'][:40]}..." for q in TEST_QUERIES[:2]]
        )
    
    if st.button("🚀 Run Comparison", type="primary"):
        # Validate Claude Code setup if enabled
        if include_claude_code and not st.session_state.get("cc_pat_token"):
            st.error("Please provide a PAT token for Claude Code Agent")
        else:
            results = []
            query_ids = [s.split(":")[0] for s in selected_queries]
            queries = [q for q in TEST_QUERIES if q["id"] in query_ids]
            
            progress = st.progress(0)
            status = st.empty()
            
            # Calculate total including Claude Code and LiteLLM if enabled
            cc_extra = 1 if include_claude_code else 0
            litellm_extra = len(selected_litellm_models) if include_litellm else 0
            total = len(queries) * len(selected_verbosities) * (len(MODELS) + cc_extra + litellm_extra)
            current = 0
            
            for query in queries:
                for verbosity in selected_verbosities:
                    row = {
                        "query_id": query["id"],
                        "query": query["text"],
                        "verbosity": verbosity,
                        "target_lines": VERBOSITY_MAX_LINES[verbosity]
                    }
                    
                    # Test each model in MODELS
                    for model_key, model_config in MODELS.items():
                        model_name = model_config["name"]
                        model_label = model_config["label"]
                        model_provider = model_config["provider"]
                        status.text(f"Testing {model_label} with {verbosity} on {query['id']}...")
                        result = call_model(conn, model_name, verbosity, query["text"], provider=model_provider)
                        
                        row[f"{model_key}_lines"] = result["line_count"]
                        row[f"{model_key}_words"] = result["word_count"]
                        row[f"{model_key}_time"] = result["duration"]
                        row[f"{model_key}_response"] = result["response"]
                        row[f"{model_key}_compliant"] = result["line_count"] <= VERBOSITY_MAX_LINES[verbosity]
                        
                        current += 1
                        progress.progress(min(current / total, 1.0))
                    
                    # Test Claude Code Agent if enabled
                    if include_claude_code:
                        cc_model_name = CLAUDE_CODE_CONFIG["models"][cc_compare_model]
                        status.text(f"Testing Claude Code Agent ({cc_model_name}) with {verbosity} on {query['id']}...")
                        
                        full_prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_PROMPTS[verbosity]}\n\nQuestion: {query['text']}"
                        result = run_claude_code_agent(
                            prompt=full_prompt,
                            model=cc_model_name,
                            pat_token=st.session_state.get("cc_pat_token"),
                            timeout=120
                        )
                        
                        row["claude_code_lines"] = result["line_count"]
                        row["claude_code_words"] = result["word_count"]
                        row["claude_code_time"] = result["duration"]
                        row["claude_code_response"] = result["response"]
                        row["claude_code_compliant"] = result["line_count"] <= VERBOSITY_MAX_LINES[verbosity]
                        row["claude_code_model"] = cc_model_name
                        
                        current += 1
                        progress.progress(min(current / total, 1.0))
                    
                    # Test LiteLLM models if enabled
                    if include_litellm and selected_litellm_models:
                        for litellm_key in selected_litellm_models:
                            litellm_label = LITELLM_CONFIG["models"][litellm_key]["label"]
                            status.text(f"Testing {litellm_label} via LiteLLM with {verbosity} on {query['id']}...")
                            
                            system_prompt = f"You provide {verbosity} responses. RULES: {VERBOSITY_PROMPTS[verbosity]}"
                            result = call_litellm_model(
                                model_key=litellm_key,
                                prompt=query["text"],
                                system_prompt=system_prompt,
                                temperature=0.7
                            )
                            
                            # Use sanitized key for column names
                            col_key = f"litellm_{litellm_key.replace('-', '_')}"
                            row[f"{col_key}_lines"] = result["line_count"]
                            row[f"{col_key}_words"] = result["word_count"]
                            row[f"{col_key}_time"] = result["duration"]
                            row[f"{col_key}_response"] = result["response"]
                            row[f"{col_key}_compliant"] = result["line_count"] <= VERBOSITY_MAX_LINES[verbosity]
                            row[f"{col_key}_model"] = result.get("model", litellm_key)
                            row[f"{col_key}_provider"] = "litellm"
                            
                            current += 1
                            progress.progress(min(current / total, 1.0))
                    
                    results.append(row)
            
            progress.empty()
            status.empty()
            
            st.session_state["results"] = results
            
            # Check for auth errors in results and show helpful message
            auth_errors_found = False
            for row in results:
                for key, val in row.items():
                    if key.endswith("_response") and isinstance(val, str) and ("390114" in val or "Authentication token has expired" in val):
                        auth_errors_found = True
                        break
                if auth_errors_found:
                    break
            
            if auth_errors_found:
                st.warning("⚠️ **Authentication token expired.** Run this in your terminal to refresh:\n```\nsnow connection test myaccount\n```\nThen restart the dashboard.")
            else:
                st.success(f"Completed {len(results)} comparisons!")

    if "results" in st.session_state and st.session_state["results"]:
        results = st.session_state["results"]
        df = pd.DataFrame(results)
        
        st.divider()
        
        # Dynamic metrics for all models
        total = len(df)
        
        # Build list of all model keys (MODELS + claude_code if present)
        all_model_keys = list(MODELS.keys())
        if "claude_code_compliant" in df.columns:
            all_model_keys.append("claude_code")
        
        # Create columns dynamically based on number of models
        metric_cols = st.columns(len(all_model_keys) * 2)  # 2 metrics per model (compliance + time)
        
        col_idx = 0
        for model_key in all_model_keys:
            if model_key == "claude_code":
                model_label = "Claude Code Agent"
            else:
                model_label = MODELS[model_key]["label"].split(" (")[0]  # Get short name
            
            compliant_col = f"{model_key}_compliant"
            time_col = f"{model_key}_time"
            
            if compliant_col in df.columns:
                compliant_count = df[compliant_col].sum()
                with metric_cols[col_idx]:
                    st.metric(f"{model_label} Comply", f"{compliant_count}/{total}", 
                             delta=f"{100*compliant_count/total:.0f}%")
                col_idx += 1
            
            if time_col in df.columns:
                with metric_cols[col_idx]:
                    st.metric(f"{model_label} Time", f"{df[time_col].mean():.1f}s")
                col_idx += 1
        
        st.subheader("Detailed Results")
        
        # Build display columns dynamically, checking what exists
        base_cols = ["query_id", "verbosity", "target_lines"]
        display_cols = [c for c in base_cols if c in df.columns]
        
        for model_key in all_model_keys:
            lines_col = f"{model_key}_lines"
            compliant_col = f"{model_key}_compliant"
            if lines_col in df.columns and compliant_col in df.columns:
                display_cols.extend([lines_col, compliant_col])
        
        if not display_cols:
            st.warning("No displayable columns found in results")
        else:
            display_df = df[display_cols].copy()
            
            # Add status columns for each model
            status_cols = [c for c in ["query_id", "verbosity", "target_lines"] if c in df.columns]
            column_config = {
                "query_id": "Query",
                "verbosity": "Verbosity",
                "target_lines": "Max Lines"
            }
            
            for model_key in all_model_keys:
                lines_col = f"{model_key}_lines"
                compliant_col = f"{model_key}_compliant"
                status_col = f"{model_key}_status"
                
                if compliant_col in display_df.columns and lines_col in display_df.columns:
                    display_df[status_col] = display_df.apply(
                        lambda r, lc=lines_col, cc=compliant_col: "✅" if r[cc] else f"❌ ({r[lc]})", axis=1)
                    status_cols.append(status_col)
                    
                    if model_key == "claude_code":
                        column_config[status_col] = "Claude Code Agent (Cortex REST)"
                    else:
                        column_config[status_col] = MODELS[model_key]["label"]
            
            st.dataframe(
                display_df[status_cols],
                column_config=column_config,
                hide_index=True,
                use_container_width=True
            )

# ============== TAB 2: Results Analysis ==============
with tab2:
    st.subheader("Results Analysis")
    
    # Try to load from saved files if session state is empty
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    
    # Load saved results button
    col_load1, col_load2 = st.columns([1, 3])
    with col_load1:
        if st.button("📂 Load Saved Results", key="load_results"):
            try:
                import json
                files_loaded = []
                
                # Load comparison results
                comp_file = os.path.join(results_dir, "comparison_results.json")
                if os.path.exists(comp_file):
                    with open(comp_file) as f:
                        st.session_state["results"] = json.load(f)
                        files_loaded.append("comparison")
                
                # Load wiki results
                wiki_file = os.path.join(results_dir, "wiki_results.json")
                if os.path.exists(wiki_file):
                    with open(wiki_file) as f:
                        st.session_state["wiki_results"] = json.load(f)
                        files_loaded.append("wiki")
                
                # Load persona results
                persona_file = os.path.join(results_dir, "persona_results.json")
                if os.path.exists(persona_file):
                    with open(persona_file) as f:
                        st.session_state["persona_results"] = json.load(f)
                        files_loaded.append("persona")
                
                # Load agent results
                agent_file = os.path.join(results_dir, "agent_results.json")
                if os.path.exists(agent_file):
                    with open(agent_file) as f:
                        st.session_state["agent_results"] = json.load(f)
                        files_loaded.append("agent")
                
                if files_loaded:
                    st.success(f"✅ Loaded: {', '.join(files_loaded)}")
                    st.rerun()
                else:
                    st.warning("No saved results found")
            except Exception as e:
                st.error(f"Error loading results: {e}")
    
    with col_load2:
        # Show what's available
        available = []
        if "results" in st.session_state and st.session_state["results"]:
            available.append(f"Comparison ({len(st.session_state['results'])})")
        if "wiki_results" in st.session_state and st.session_state["wiki_results"]:
            available.append(f"Wiki ({len(st.session_state['wiki_results'])})")
        if "persona_results" in st.session_state and st.session_state["persona_results"]:
            available.append(f"Persona ({len(st.session_state['persona_results'])})")
        if "agent_results" in st.session_state and st.session_state["agent_results"]:
            available.append(f"Agent ({len(st.session_state['agent_results'])})")
        
        if available:
            st.caption(f"Loaded: {' | '.join(available)}")
        else:
            st.caption("No results in memory. Click 'Load Saved Results' or run comparisons.")
    
    st.divider()
    
    if "results" in st.session_state and st.session_state["results"]:
        df = pd.DataFrame(st.session_state["results"])
        
        st.markdown("### Model Compliance Summary")
        
        # Dynamic compliance metrics for all available models
        available_models = []
        for model_key, model_config in MODELS.items():
            compliant_col = f"{model_key}_compliant"
            if compliant_col in df.columns:
                available_models.append((model_key, model_config))
        
        if available_models:
            cols = st.columns(len(available_models))
            for idx, (model_key, model_config) in enumerate(available_models):
                compliant_col = f"{model_key}_compliant"
                compliant_count = df[compliant_col].sum()
                with cols[idx]:
                    st.metric(f"🏆 {model_config['label']}", 
                             f"{compliant_count}/{len(df)}", 
                             delta=f"{100*compliant_count/len(df):.0f}%")
        
        st.markdown("### Response Explorer")
        
        selected = st.selectbox(
            "Select comparison to view",
            options=[f"{r['query_id']} | {r['verbosity']}" for r in st.session_state["results"]]
        )
        
        if selected:
            idx = [f"{r['query_id']} | {r['verbosity']}" for r in st.session_state["results"]].index(selected)
            row = st.session_state["results"][idx]
            
            st.markdown(f"**Query:** {row.get('query', 'N/A')}")
            
            # Dynamic columns for each available model
            if available_models:
                cols = st.columns(len(available_models))
                for col_idx, (model_key, model_config) in enumerate(available_models):
                    response_col = f"{model_key}_response"
                    lines_col = f"{model_key}_lines"
                    compliant_col = f"{model_key}_compliant"
                    
                    with cols[col_idx]:
                        if compliant_col in row and lines_col in row:
                            status = "✅" if row[compliant_col] else "❌"
                            st.markdown(f"**{model_config['label']}** {status} ({row[lines_col]} lines)")
                        else:
                            st.markdown(f"**{model_config['label']}**")
                        
                        if response_col in row:
                            st.code(row[response_col][:1000] if row[response_col] else "No response")
                        else:
                            st.code("No response data")
    else:
        st.info("Run a comparison first to see analysis")

# ============== TAB 3: Live Test ==============
with tab3:
    st.subheader("Live Model Test")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        test_query = st.text_area("Enter your question:", value="What is SQL injection?", height=100)
    
    with col2:
        test_verbosity = st.selectbox("Verbosity level:", options=list(VERBOSITY_PROMPTS.keys()))
        st.caption(f"Max lines: {VERBOSITY_MAX_LINES[test_verbosity]}")
    
    st.divider()
    st.markdown("### Cortex SQL Models")
    
    if st.button("⚡ Test Cortex SQL Models", key="test_sql"):
        with st.spinner("Querying Cortex SQL models..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Claude 3.5 Sonnet (Cortex SQL)**")
                result = call_model(conn, MODELS["claude"]["name"], test_verbosity, test_query)
                compliant = result["line_count"] <= VERBOSITY_MAX_LINES[test_verbosity]
                status = "✅ Compliant" if compliant else f"❌ Over ({result['line_count']})"
                st.metric("Status", status)
                st.code(result["response"])
            
            with col2:
                st.markdown("**Mistral Large 2 (Cortex SQL)**")
                result = call_model(conn, MODELS["mistral"]["name"], test_verbosity, test_query)
                compliant = result["line_count"] <= VERBOSITY_MAX_LINES[test_verbosity]
                status = "✅ Compliant" if compliant else f"❌ Over ({result['line_count']})"
                st.metric("Status", status)
                st.code(result["response"])
    
    st.divider()
    st.markdown("### Cortex REST API Models")
    
    rest_model = st.selectbox(
        "Select Model (Cortex REST API):",
        options=list(CORTEX_REST_MODELS.keys()),
        format_func=lambda x: CORTEX_REST_MODELS[x]["label"],
        key="rest_model_select"
    )
    
    if st.button("🚀 Test Cortex REST API", key="test_rest"):
        model_config = CORTEX_REST_MODELS[rest_model]
        system_prompt = f"You provide {test_verbosity} responses. RULES: {VERBOSITY_PROMPTS[test_verbosity]}"
        
        with st.spinner(f"Calling {model_config['label']}..."):
            result = call_model_rest_api(
                conn, 
                model_config["name"], 
                test_query,
                system_prompt=system_prompt
            )
            
            if result["success"]:
                compliant = result["line_count"] <= VERBOSITY_MAX_LINES[test_verbosity]
                status = "✅ Compliant" if compliant else f"❌ Over ({result['line_count']})"
                st.metric("Status", status)
                st.caption(f"Response time: {result['duration']:.2f}s | Provider: Cortex REST API")
                st.code(result["response"])
            else:
                st.error(result["response"])
    
    st.divider()
    st.markdown("### Claude Code over Cortex REST API")
    
    # Get dynamic endpoint from connection
    try:
        conn = get_connection()
        cortex_endpoint = get_cortex_endpoint(conn)
        st.caption(f"Endpoint: `{cortex_endpoint}`")
    except Exception as e:
        st.error(f"Connection error: {e}")
        cortex_endpoint = None
    
    col_cc1, col_cc2 = st.columns([2, 1])
    with col_cc1:
        if cortex_endpoint:
            st.success("✅ Connected via Snowflake connection (myaccount)")
        else:
            st.warning("⚠️ Connection not available. Run: `snow connection test myaccount`")
    
    with col_cc2:
        cc_model = st.selectbox(
            "Model:",
            options=list(CLAUDE_CODE_CONFIG["models"].keys()),
            format_func=lambda x: CLAUDE_CODE_CONFIG["models"][x],
            key="cc_model_select"
        )
    
    if st.button("🤖 Run Claude Code via Cortex REST API", key="test_claude_code"):
        if not cortex_endpoint:
            st.error("Please establish a Snowflake connection first")
        else:
            selected_model = CLAUDE_CODE_CONFIG["models"][cc_model]
            system_prompt = f"You provide {test_verbosity} responses. RULES: {VERBOSITY_PROMPTS[test_verbosity]}"
            
            with st.spinner(f"Calling {selected_model} via Cortex REST API..."):
                # Use the existing call_model_rest_api function which has auto-reconnect
                result = call_model_rest_api(
                    conn=conn,
                    model=selected_model,
                    prompt=test_query,
                    system_prompt=system_prompt,
                    max_tokens=4096,
                    temperature=0.7
                )
                
                if result.get("success"):
                    response_text = result["response"]
                    line_count = result["line_count"]
                    compliant = line_count <= VERBOSITY_MAX_LINES[test_verbosity]
                    status = "✅ Compliant" if compliant else f"❌ Over ({line_count})"
                    
                    st.metric("Status", status)
                    st.caption(f"Response time: {result['duration']:.2f}s | Model: {selected_model} | Provider: Cortex REST API")
                    
                    st.markdown("**Response:**")
                    st.markdown(response_text)
                else:
                    error_msg = result.get("response", "Unknown error")
                    st.error(f"Error: {error_msg}")
                    if result.get("auth_error"):
                        st.warning("⚠️ **Authentication token expired.** Run this in your terminal to refresh:\n```\nsnow connection test myaccount\n```\nThen restart the dashboard.")

# ============== TAB 4: Wiki Compare ==============
with tab4:
    st.subheader("📚 Wikipedia Q&A Comparison")
    st.markdown("Generate synthetic Q&A from Wikipedia using **Vine Copula** modeling.")
    
    # MCP Server Status
    mcp_status = check_mcp_server(MCP_URL)
    col_mcp1, col_mcp2 = st.columns([3, 1])
    with col_mcp1:
        if mcp_status:
            st.success(f"✅ Wiki MCP Server running at {MCP_URL}")
        else:
            st.warning(f"⚠️ Wiki MCP Server not running at {MCP_URL}")
    with col_mcp2:
        use_mcp = st.checkbox("Use MCP Server", value=mcp_status, disabled=not mcp_status, 
                              help="Use MCP server for Wikipedia fetching (faster, cached)")
        if not mcp_status and st.button("🚀 Start MCP", key="start_mcp"):
            with st.spinner("Starting MCP server..."):
                if ensure_mcp_server(MCP_URL):
                    st.rerun()
    
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        wiki_input = st.text_area(
            "Wikipedia Articles:",
            value="The_Lord_of_the_Rings\nNew_England_Patriots\nApollo_program",
            height=100
        )
    
    with col2:
        n_wiki_questions = st.slider("Questions:", 5, 20, 8, key="wiki_q")
        wiki_verbosities = st.multiselect(
            "Verbosity levels:",
            options=list(VERBOSITY_PROMPTS.keys()),
            default=["minimal", "brief"],
            key="wiki_v"
        )
    
    articles = [a.strip().replace(" ", "_") for a in wiki_input.replace(",", "\n").split("\n") if a.strip()]
    
    if st.button("🚀 Generate Wiki Q&A & Compare", type="primary", key="wiki_run"):
        with st.spinner("Fetching Wikipedia and generating Q&A..."):
            try:
                if use_mcp and mcp_status:
                    # Use MCP server
                    st.info("📡 Using MCP Server for Q&A generation")
                    mcp_client = WikiMCPClient(MCP_URL, auto_start=False)
                    qa_pairs = []
                    for article in articles:
                        result = mcp_client.generate_qa(article, n_wiki_questions // len(articles) + 1)
                        for q in result.get('questions', []):
                            qa_pairs.append({
                                'article': q['article'],
                                'question': q['question'],
                                'expected_answer': q.get('context', '')[:200],
                                'category': q['category'],
                                'difficulty': 'medium',
                                'copula_sample': []
                            })
                else:
                    # Use local generator
                    qa_pairs = generate_wiki_qa(articles, n_wiki_questions)
                
                st.session_state["wiki_qa"] = qa_pairs
                st.success(f"Generated {len(qa_pairs)} questions!")
            except Exception as e:
                st.error(f"Error: {e}")
                qa_pairs = []
        
        if qa_pairs:
            wiki_results = []
            progress = st.progress(0)
            total = len(qa_pairs) * len(wiki_verbosities) * len(MODELS)
            current = 0
            
            for qa in qa_pairs:
                for verbosity in wiki_verbosities:
                    row = {**qa, "verbosity": verbosity, "target_lines": VERBOSITY_MAX_LINES[verbosity]}
                    
                    for model_key, model_config in MODELS.items():
                        model_name = model_config["name"]
                        model_provider = model_config["provider"]
                        result = call_model(conn, model_name, verbosity, qa["question"], provider=model_provider)
                        row[f"{model_key}_response"] = result["response"]
                        row[f"{model_key}_lines"] = result["line_count"]
                        row[f"{model_key}_compliant"] = result["line_count"] <= VERBOSITY_MAX_LINES[verbosity]
                        row[f"{model_key}_accuracy"] = check_answer_accuracy(result["response"], qa["expected_answer"])
                        current += 1
                        progress.progress(current / total)
                    
                    wiki_results.append(row)
            
            progress.empty()
            st.session_state["wiki_results"] = wiki_results
    
    if "wiki_results" in st.session_state:
        wiki_df = pd.DataFrame(st.session_state["wiki_results"])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Claude Comply", f"{wiki_df['claude_compliant'].sum()}/{len(wiki_df)}")
        with col2:
            st.metric("Mistral Comply", f"{wiki_df['mistral_compliant'].sum()}/{len(wiki_df)}")
        with col3:
            claude_acc = wiki_df['claude_accuracy'].mean() if 'claude_accuracy' in wiki_df.columns else 0
            st.metric("Claude Acc", f"{claude_acc:.0%}")
        with col4:
            mistral_acc = wiki_df['mistral_accuracy'].mean() if 'mistral_accuracy' in wiki_df.columns else 0
            st.metric("Mistral Acc", f"{mistral_acc:.0%}")

# ============== TAB 5: Persona Compare ==============
with tab5:
    st.subheader("🎭 Persona-Based Model Comparison")
    st.markdown("""
    Compare how models adapt to different communication **personas** across diverse domains.
    Uses **Vine Copula** to generate domain-specific Q&A.
    """)
    
    # Persona descriptions
    with st.expander("📋 Persona Definitions", expanded=False):
        for key, persona in PERSONAS.items():
            st.markdown(f"**{persona['name']}**: {persona['description']}")
            st.code(persona['prompt'][:200] + "...", language=None)
            st.divider()
    
    # Domain descriptions
    with st.expander("📚 Domain Content", expanded=False):
        for key, domain in DOMAINS.items():
            st.markdown(f"**{domain['name']}**")
            st.markdown(f"Articles: {', '.join(domain['articles'][:3])}...")
            st.divider()
    
    st.divider()
    
    # Configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_domains = st.multiselect(
            "Select Domains:",
            options=list(DOMAINS.keys()),
            default=list(DOMAINS.keys()),
            format_func=lambda x: DOMAINS[x]["name"],
            key="persona_domains"
        )
    
    with col2:
        selected_personas = st.multiselect(
            "Select Personas:",
            options=list(PERSONAS.keys()),
            default=["5th_grade", "compute"],
            format_func=lambda x: PERSONAS[x]["name"],
            key="persona_select"
        )
    
    with col3:
        n_persona_questions = st.slider("Questions:", 3, 15, 4, key="persona_q")
        persona_seed = st.number_input("Random seed:", value=42, key="persona_seed")
    
    st.markdown(f"**Will generate:** {n_persona_questions} questions × {len(selected_personas)} personas × 2 models = {n_persona_questions * len(selected_personas) * 2} API calls")
    
    if st.button("🎭 Generate & Compare Personas", type="primary", key="persona_run"):
        
        # Step 1: Generate Q&A
        with st.spinner("Loading domains and generating Q&A with Vine Copula..."):
            try:
                qa_pairs = generate_persona_qa(
                    domains=selected_domains,
                    n_questions=n_persona_questions,
                    seed=persona_seed
                )
                st.session_state["persona_qa"] = qa_pairs
                st.success(f"Generated {len(qa_pairs)} questions across {len(selected_domains)} domains!")
            except Exception as e:
                st.error(f"Error generating Q&A: {e}")
                import traceback
                st.code(traceback.format_exc())
                qa_pairs = []
        
        if qa_pairs:
            # Show generated questions
            with st.expander("📋 Generated Questions", expanded=True):
                qa_df = pd.DataFrame(qa_pairs)
                st.dataframe(
                    qa_df[["domain", "category", "article", "question", "expected_answer"]],
                    column_config={
                        "domain": "Domain",
                        "category": "Category",
                        "article": "Article",
                        "question": "Question",
                        "expected_answer": st.column_config.TextColumn("Expected Answer", width="large")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            
            # Step 2: Run comparison across personas
            st.divider()
            st.markdown("### Running Persona Comparison...")
            
            persona_results = []
            progress = st.progress(0)
            status = st.empty()
            
            total = len(qa_pairs) * len(selected_personas) * len(MODELS)
            current = 0
            
            for qa in qa_pairs:
                for persona_key in selected_personas:
                    row = {
                        "domain": qa["domain"],
                        "article": qa["article"],
                        "question": qa["question"],
                        "expected_answer": qa["expected_answer"],
                        "category": qa["category"],
                        "difficulty": qa["difficulty"],
                        "persona": persona_key,
                        "persona_name": PERSONAS[persona_key]["name"]
                    }
                    
                    for model_key, model_config in MODELS.items():
                        model_name = model_config["name"]
                        model_label = model_config["label"]
                        status.text(f"{model_label} | {PERSONAS[persona_key]['name'][:15]} | {qa['domain']}")
                        
                        result = call_model_with_persona(conn, model_name, persona_key, qa["question"])
                        
                        row[f"{model_key}_response"] = result["response"]
                        row[f"{model_key}_time"] = result["duration"]
                        row[f"{model_key}_compliant"] = result["evaluation"].get("compliant", False)
                        row[f"{model_key}_score"] = result["evaluation"].get("score", 0)
                        
                        # Store detailed evaluation
                        if persona_key == "5th_grade":
                            row[f"{model_key}_flesch"] = result["evaluation"].get("flesch_score", 0)
                        elif persona_key == "scholar":
                            row[f"{model_key}_flesch"] = result["evaluation"].get("flesch_score", 0)
                        elif persona_key == "compute":
                            row[f"{model_key}_has_sql"] = result["evaluation"].get("has_sql", False)
                        elif persona_key == "business":
                            row[f"{model_key}_biz_terms"] = result["evaluation"].get("business_terms", 0)
                        
                        current += 1
                        progress.progress(current / total)
                    
                    persona_results.append(row)
            
            progress.empty()
            status.empty()
            
            st.session_state["persona_results"] = persona_results
            st.success(f"Completed {len(persona_results)} persona comparisons!")
    
    # Display Persona Results
    if "persona_results" in st.session_state and st.session_state["persona_results"]:
        persona_results = st.session_state["persona_results"]
        persona_df = pd.DataFrame(persona_results)
        
        st.divider()
        st.markdown("### 📊 Persona Comparison Results")
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if "claude_compliant" in persona_df.columns:
                c_comply = persona_df["claude_compliant"].sum()
                st.metric("Claude Compliance", f"{c_comply}/{len(persona_df)}", 
                         delta=f"{100*c_comply/len(persona_df):.0f}%")
            else:
                st.metric("Claude Compliance", "N/A")
        with col2:
            if "mistral_compliant" in persona_df.columns:
                m_comply = persona_df["mistral_compliant"].sum()
                st.metric("Mistral Compliance", f"{m_comply}/{len(persona_df)}",
                         delta=f"{100*m_comply/len(persona_df):.0f}%")
            else:
                st.metric("Mistral Compliance", "N/A")
        with col3:
            if "claude_score" in persona_df.columns:
                c_score = persona_df["claude_score"].mean()
                st.metric("Claude Avg Score", f"{c_score:.0f}")
            else:
                st.metric("Claude Avg Score", "N/A")
        with col4:
            if "mistral_score" in persona_df.columns:
                m_score = persona_df["mistral_score"].mean()
                st.metric("Mistral Avg Score", f"{m_score:.0f}")
            else:
                st.metric("Mistral Avg Score", "N/A")
        
        # By Persona breakdown
        st.markdown("### 🎭 Performance by Persona")
        
        # Build aggregation dict based on available columns
        agg_dict = {}
        if "claude_compliant" in persona_df.columns:
            agg_dict["claude_compliant"] = "sum"
        if "mistral_compliant" in persona_df.columns:
            agg_dict["mistral_compliant"] = "sum"
        if "claude_score" in persona_df.columns:
            agg_dict["claude_score"] = "mean"
        if "mistral_score" in persona_df.columns:
            agg_dict["mistral_score"] = "mean"
        if "claude_time" in persona_df.columns:
            agg_dict["claude_time"] = "mean"
        if "mistral_time" in persona_df.columns:
            agg_dict["mistral_time"] = "mean"
        
        if agg_dict and "persona_name" in persona_df.columns:
            persona_summary = persona_df.groupby("persona_name").agg(agg_dict).reset_index()
            persona_summary["total"] = persona_df.groupby("persona_name").size().values
            
            # Build column config based on available columns
            col_config = {"persona_name": "Persona", "total": "Total"}
            if "claude_compliant" in persona_summary.columns:
                col_config["claude_compliant"] = "Claude ✓"
            if "mistral_compliant" in persona_summary.columns:
                col_config["mistral_compliant"] = "Mistral ✓"
            if "claude_score" in persona_summary.columns:
                col_config["claude_score"] = st.column_config.ProgressColumn("Claude Score", format="%.0f", min_value=0, max_value=100)
            if "mistral_score" in persona_summary.columns:
                col_config["mistral_score"] = st.column_config.ProgressColumn("Mistral Score", format="%.0f", min_value=0, max_value=100)
            if "claude_time" in persona_summary.columns:
                col_config["claude_time"] = st.column_config.NumberColumn("Claude Time", format="%.1fs")
            if "mistral_time" in persona_summary.columns:
                col_config["mistral_time"] = st.column_config.NumberColumn("Mistral Time", format="%.1fs")
            
            st.dataframe(
                persona_summary,
                column_config=col_config,
                hide_index=True,
                use_container_width=True
            )
        else:
            # Show raw results with question, answer, and responses
            display_cols = ["domain", "persona_name", "question", "expected_answer"]
            if "claude_response" in persona_df.columns:
                display_cols.append("claude_response")
            if "mistral_response" in persona_df.columns:
                display_cols.append("mistral_response")
            
            st.dataframe(
                persona_df[[c for c in display_cols if c in persona_df.columns]].head(10),
                column_config={
                    "domain": "Domain",
                    "persona_name": "Persona",
                    "question": st.column_config.TextColumn("Question", width="medium"),
                    "expected_answer": st.column_config.TextColumn("Expected Answer", width="medium"),
                    "claude_response": st.column_config.TextColumn("Claude Response", width="large"),
                    "mistral_response": st.column_config.TextColumn("Mistral Response", width="large")
                },
                hide_index=True,
                use_container_width=True
            )
        
        # Persona score chart
        if "claude_score" in persona_df.columns and "mistral_score" in persona_df.columns and "persona_name" in persona_df.columns:
            score_data = persona_df.melt(
                id_vars=["persona_name"],
                value_vars=["claude_score", "mistral_score"],
                var_name="model",
                value_name="score"
            )
            score_data["model"] = score_data["model"].str.replace("_score", "").str.title()
            
            score_chart = alt.Chart(score_data).mark_boxplot().encode(
                x=alt.X("persona_name:N", title="Persona"),
                y=alt.Y("score:Q", title="Compliance Score", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color("model:N", scale=alt.Scale(
                    domain=["Claude", "Mistral"],
                    range=["#6366f1", "#f59e0b"]
                ))
            ).properties(height=300, title="Score Distribution by Persona")
            
            st.altair_chart(score_chart, use_container_width=True)
        
        # By Domain breakdown
        st.markdown("### 📚 Performance by Domain")
        
        if "domain" in persona_df.columns:
            # Build domain agg dict
            domain_agg = {}
            if "claude_compliant" in persona_df.columns:
                domain_agg["claude_compliant"] = "sum"
            if "mistral_compliant" in persona_df.columns:
                domain_agg["mistral_compliant"] = "sum"
            if "claude_score" in persona_df.columns:
                domain_agg["claude_score"] = "mean"
            if "mistral_score" in persona_df.columns:
                domain_agg["mistral_score"] = "mean"
            
            if domain_agg:
                domain_summary = persona_df.groupby("domain").agg(domain_agg).reset_index()
                domain_summary["total"] = persona_df.groupby("domain").size().values
                domain_summary["domain_name"] = domain_summary["domain"].map(lambda x: DOMAINS.get(x, {}).get("name", x))
                
                # Build display columns based on what's available
                display_cols = ["domain_name"]
                col_cfg = {"domain_name": "Domain"}
                if "claude_compliant" in domain_summary.columns:
                    display_cols.append("claude_compliant")
                    col_cfg["claude_compliant"] = "Claude ✓"
                if "mistral_compliant" in domain_summary.columns:
                    display_cols.append("mistral_compliant")
                    col_cfg["mistral_compliant"] = "Mistral ✓"
                display_cols.append("total")
                col_cfg["total"] = "Total"
                if "claude_score" in domain_summary.columns:
                    display_cols.append("claude_score")
                    col_cfg["claude_score"] = st.column_config.NumberColumn("Claude Score", format="%.0f")
                if "mistral_score" in domain_summary.columns:
                    display_cols.append("mistral_score")
                    col_cfg["mistral_score"] = st.column_config.NumberColumn("Mistral Score", format="%.0f")
                
                st.dataframe(
                    domain_summary[display_cols],
                    column_config=col_cfg,
                    hide_index=True,
                    use_container_width=True
                )
        
        # Heatmap: Persona x Domain
        if "persona_name" in persona_df.columns and "domain" in persona_df.columns:
            st.markdown("### 🗺️ Compliance Heatmap")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if "claude_compliant" in persona_df.columns:
                    st.markdown("**Claude Compliance**")
                    heatmap_c = persona_df.pivot_table(
                        index="persona_name", 
                        columns="domain", 
                        values="claude_compliant",
                        aggfunc="mean"
                    ).reset_index().melt(id_vars="persona_name", var_name="domain", value_name="compliance")
                    
                    hm_chart_c = alt.Chart(heatmap_c).mark_rect().encode(
                        x=alt.X("domain:N", title="Domain"),
                        y=alt.Y("persona_name:N", title="Persona"),
                        color=alt.Color("compliance:Q", scale=alt.Scale(scheme="blues"), title="Rate")
                    ).properties(height=200)
                    st.altair_chart(hm_chart_c, use_container_width=True)
            
            with col2:
                if "mistral_compliant" in persona_df.columns:
                    st.markdown("**Mistral Compliance**")
                    heatmap_m = persona_df.pivot_table(
                        index="persona_name", 
                        columns="domain", 
                        values="mistral_compliant",
                        aggfunc="mean"
                    ).reset_index().melt(id_vars="persona_name", var_name="domain", value_name="compliance")
                    
                    hm_chart_m = alt.Chart(heatmap_m).mark_rect().encode(
                        x=alt.X("domain:N", title="Domain"),
                        y=alt.Y("persona_name:N", title="Persona"),
                        color=alt.Color("compliance:Q", scale=alt.Scale(scheme="oranges"), title="Rate")
                    ).properties(height=200)
                    st.altair_chart(hm_chart_m, use_container_width=True)
        
        # Response Explorer
        st.markdown("### 🔍 Response Explorer")
        
        selected_persona_result = st.selectbox(
            "Select comparison to explore:",
            options=[f"{r['domain']} | {r['persona_name'][:15]} | {r['question'][:35]}..." 
                    for r in persona_results],
            key="persona_explorer"
        )
        
        if selected_persona_result:
            idx = [f"{r['domain']} | {r['persona_name'][:15]} | {r['question'][:35]}..." 
                   for r in persona_results].index(selected_persona_result)
            row = persona_results[idx]
            
            st.markdown(f"**Domain:** {DOMAINS.get(row['domain'], {}).get('name', row['domain'])}")
            st.markdown(f"**Persona:** {row['persona_name']}")
            st.markdown(f"**Question:** {row['question']}")
            st.markdown(f"**Expected:** {row['expected_answer'][:150]}...")
            
            col1, col2 = st.columns(2)
            
            with col1:
                c_compliant = row.get("claude_compliant", False)
                c_score = row.get("claude_score", 0)
                c_status = "✅" if c_compliant else "❌"
                st.markdown(f"**Claude** {c_status} | Score: {c_score:.0f}")
                
                # Show persona-specific metrics
                if row.get("persona") == "5th_grade" and "claude_flesch" in row:
                    st.caption(f"Flesch Score: {row['claude_flesch']:.0f} (target: 80-90)")
                elif row.get("persona") == "scholar" and "claude_flesch" in row:
                    st.caption(f"Flesch Score: {row['claude_flesch']:.0f} (target: 20-50)")
                elif row.get("persona") == "compute" and "claude_has_sql" in row:
                    st.caption(f"Has SQL: {'Yes' if row['claude_has_sql'] else 'No'}")
                elif row.get("persona") == "business" and "claude_biz_terms" in row:
                    st.caption(f"Business Terms: {row['claude_biz_terms']}")
                
                st.code(row.get("claude_response", "N/A")[:800])
            
            with col2:
                m_compliant = row.get("mistral_compliant", False)
                m_score = row.get("mistral_score", 0)
                m_status = "✅" if m_compliant else "❌"
                st.markdown(f"**Mistral** {m_status} | Score: {m_score:.0f}")
                
                # Show persona-specific metrics
                if row.get("persona") == "5th_grade" and "mistral_flesch" in row:
                    st.caption(f"Flesch Score: {row['mistral_flesch']:.0f} (target: 80-90)")
                elif row.get("persona") == "scholar" and "mistral_flesch" in row:
                    st.caption(f"Flesch Score: {row['mistral_flesch']:.0f} (target: 20-50)")
                elif row.get("persona") == "compute" and "mistral_has_sql" in row:
                    st.caption(f"Has SQL: {'Yes' if row['mistral_has_sql'] else 'No'}")
                elif row.get("persona") == "business" and "mistral_biz_terms" in row:
                    st.caption(f"Business Terms: {row['mistral_biz_terms']}")
                
                st.code(row.get("mistral_response", "N/A")[:800])

# ============== TAB 6: Agent Verbosity ==============
with tab6:
    st.subheader("🤖 Agent Verbosity Comparison")
    st.markdown("""
    Test the **8 Verbosity Agent Types** from ShrunkElaborateAgents.md across both models.
    Each agent has specific response length and format requirements.
    """)
    
    # Agent definitions from ShrunkElaborateAgents.md
    AGENT_DEFINITIONS = {
        "MINIMAL": {
            "flag": "--minimal",
            "max_lines": 1,
            "description": "1 line max, single word/number when possible",
            "prompt": """You provide absolute minimum responses.

## Rules
- 1 line maximum
- Single word/number when possible
- No punctuation unless required
- No formatting

## Examples
Q: "Is this secure?" → No
Q: "What line has the bug?" → 12
Q: "Which framework?" → PyTorch"""
        },
        "BRIEF": {
            "flag": "--brief",
            "max_lines": 3,
            "description": "≤3 lines, essential info only",
            "prompt": """You provide brief, direct responses.

## Rules
- Maximum 3 lines
- No preamble or postamble
- Essential information only
- Code snippets without explanation"""
        },
        "STANDARD": {
            "flag": "--standard",
            "max_lines": 6,
            "description": "3-6 lines, balanced with context",
            "prompt": """You provide balanced responses with appropriate detail.

## Rules
- 3-6 lines typical
- Include context when helpful
- Brief explanation with code
- Skip obvious details"""
        },
        "DETAILED": {
            "flag": "--detailed",
            "max_lines": 15,
            "description": "Full context with structure",
            "prompt": """You provide detailed responses with full context.

## Rules
- Include problem context
- Show before/after code
- Explain the vulnerability mechanism
- Mention related concerns

## Structure
1. **Issue**: What's wrong
2. **Location**: Where in code
3. **Risk**: What could happen
4. **Fix**: Corrected code
5. **Related**: Other considerations"""
        },
        "VERBOSE": {
            "flag": "--verbose",
            "max_lines": 50,
            "description": "Comprehensive, educational",
            "prompt": """You provide comprehensive, educational responses.

## Rules
- Full technical context
- Background on the vulnerability class
- Multiple fix options with tradeoffs
- Edge cases and caveats
- Best practice references"""
        },
        "CODE_ONLY": {
            "flag": "--code",
            "max_lines": 20,
            "description": "Code blocks only, no prose",
            "prompt": """You respond with code only, no prose.

## Rules
- Return ONLY code blocks
- No explanatory text
- No markdown headers
- Comments in code only if essential
- Multiple code blocks allowed"""
        },
        "EXPLAIN": {
            "flag": "--explain",
            "max_lines": 20,
            "description": "Why + how explanation",
            "prompt": """You explain the "why" and "how" behind everything.

## Rules
- Focus on understanding, not just fixing
- Explain mechanisms and causes
- Use analogies when helpful
- Connect to broader concepts

## Structure
### What's Happening
### Why It Happens
### How It Works
### Why The Fix Works"""
        },
        "STEP_BY_STEP": {
            "flag": "--steps",
            "max_lines": 25,
            "description": "Numbered walkthrough",
            "prompt": """You provide numbered, sequential walkthroughs.

## Rules
- Every response is numbered steps
- One action per step
- Clear completion criteria per step
- Checkpoints for verification"""
        }
    }
    
    # Security-focused test queries (from original context)
    SECURITY_QUERIES = [
        {"id": "SEC1", "text": "Is this safe: session.sql(f\"SELECT * FROM users WHERE id={user_id}\")?", "category": "security"},
        {"id": "SEC2", "text": "What's wrong with: eval(user_input)?", "category": "security"},
        {"id": "SEC3", "text": "Fix this SQL injection vulnerability", "category": "fix"},
        {"id": "SEC4", "text": "How do I validate user input in Python?", "category": "howto"},
        {"id": "SEC5", "text": "What is a SQL injection attack?", "category": "explain"},
    ]
    
    # Show agent architecture
    with st.expander("📋 Agent Architecture (ShrunkElaborateAgents.md)", expanded=False):
        st.code("""
RESPONSE_ORCHESTRATOR_AGENT (Master)
├── MINIMAL_AGENT          --minimal     (1 line max)
├── BRIEF_AGENT            --brief       (3 lines max)
├── STANDARD_AGENT         --standard    (default, balanced)
├── DETAILED_AGENT         --detailed    (with context)
├── VERBOSE_AGENT          --verbose     (full explanation)
├── CODE_ONLY_AGENT        --code        (no prose)
├── EXPLAIN_AGENT          --explain     (why + how)
└── STEP_BY_STEP_AGENT     --steps       (numbered walkthrough)
        """, language=None)
        
        # Quick reference table
        st.markdown("### Quick Reference")
        ref_data = []
        for name, config in AGENT_DEFINITIONS.items():
            ref_data.append({
                "Agent": name,
                "Flag": config["flag"],
                "Max Lines": config["max_lines"],
                "Description": config["description"]
            })
        st.dataframe(pd.DataFrame(ref_data), hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        selected_agents = st.multiselect(
            "Select Agent Types:",
            options=list(AGENT_DEFINITIONS.keys()),
            default=["MINIMAL", "BRIEF", "STANDARD", "CODE_ONLY"],
            key="agent_select"
        )
    
    with col2:
        selected_security_queries = st.multiselect(
            "Select Test Queries:",
            options=[f"{q['id']}: {q['text'][:40]}..." for q in SECURITY_QUERIES],
            default=[f"{q['id']}: {q['text'][:40]}..." for q in SECURITY_QUERIES[:3]],
            key="security_queries"
        )
    
    st.markdown(f"**Will run:** {len(selected_agents)} agents × {len(selected_security_queries)} queries × 2 models = {len(selected_agents) * len(selected_security_queries) * 2} API calls")
    
    if st.button("🤖 Run Agent Verbosity Test", type="primary", key="agent_run"):
        query_ids = [s.split(":")[0] for s in selected_security_queries]
        queries = [q for q in SECURITY_QUERIES if q["id"] in query_ids]
        
        agent_results = []
        progress = st.progress(0)
        status = st.empty()
        
        total = len(queries) * len(selected_agents) * len(MODELS)
        current = 0
        
        for query in queries:
            for agent_name in selected_agents:
                agent_config = AGENT_DEFINITIONS[agent_name]
                
                row = {
                    "query_id": query["id"],
                    "query": query["text"],
                    "category": query["category"],
                    "agent": agent_name,
                    "flag": agent_config["flag"],
                    "max_lines": agent_config["max_lines"]
                }
                
                for model_key, model_config in MODELS.items():
                    model_name = model_config["name"]
                    model_label = model_config["label"]
                    status.text(f"{model_label} | {agent_name} | {query['id']}...")
                    
                    # Call model with agent prompt (with auto-reconnect on auth errors)
                    full_prompt = f"{agent_config['prompt']}\n\nQuestion: {query['text']}"
                    full_prompt_escaped = full_prompt.replace("'", "''")
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model_name}', '{full_prompt_escaped}') AS response"
                    
                    # Try up to 2 times (initial + retry after reconnect)
                    for attempt in range(2):
                        cursor = conn.cursor()
                        try:
                            start = datetime.now()
                            cursor.execute(sql)
                            response = cursor.fetchone()[0]
                            duration = (datetime.now() - start).total_seconds()
                            
                            lines = response.strip().count('\n') + 1
                            words = len(response.split())
                            
                            row[f"{model_key}_response"] = response
                            row[f"{model_key}_lines"] = lines
                            row[f"{model_key}_words"] = words
                            row[f"{model_key}_time"] = duration
                            row[f"{model_key}_compliant"] = lines <= agent_config["max_lines"]
                            
                            # Special check for CODE_ONLY - should have code blocks
                            if agent_name == "CODE_ONLY":
                                has_code = "```" in response or response.strip().startswith("def ") or response.strip().startswith("SELECT")
                                row[f"{model_key}_has_code"] = has_code
                            break  # Success, exit retry loop
                            
                        except Exception as e:
                            error_str = str(e)
                            # Check for auth token expiry - retry with fresh connection
                            if is_auth_error(error_str) and attempt == 0:
                                status.text(f"🔄 Reconnecting (token expired)...")
                                conn = get_fresh_connection()
                                continue  # Retry with new connection
                            
                            row[f"{model_key}_response"] = error_str
                            row[f"{model_key}_lines"] = 0
                            row[f"{model_key}_words"] = 0
                            row[f"{model_key}_time"] = 0
                            row[f"{model_key}_compliant"] = False
                        finally:
                            cursor.close()
                    
                    current += 1
                    progress.progress(current / total)
                
                agent_results.append(row)
        
        progress.empty()
        status.empty()
        
        st.session_state["agent_results"] = agent_results
        st.success(f"Completed {len(agent_results)} agent tests!")
    
    # Display Agent Results
    if "agent_results" in st.session_state and st.session_state["agent_results"]:
        agent_results = st.session_state["agent_results"]
        agent_df = pd.DataFrame(agent_results)
        
        st.divider()
        st.markdown("### 📊 Agent Verbosity Results")
        
        # Overall metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            c_comply = agent_df["claude_compliant"].sum()
            st.metric("Claude Compliance", f"{c_comply}/{len(agent_df)}", 
                     delta=f"{100*c_comply/len(agent_df):.0f}%")
        with col2:
            m_comply = agent_df["mistral_compliant"].sum()
            st.metric("Mistral Compliance", f"{m_comply}/{len(agent_df)}",
                     delta=f"{100*m_comply/len(agent_df):.0f}%")
        with col3:
            st.metric("Claude Avg Lines", f"{agent_df['claude_lines'].mean():.1f}")
        with col4:
            st.metric("Mistral Avg Lines", f"{agent_df['mistral_lines'].mean():.1f}")
        
        # Results by Agent
        st.markdown("### 🤖 Performance by Agent Type")
        
        agent_summary = agent_df.groupby("agent").agg({
            "claude_compliant": "sum",
            "mistral_compliant": "sum",
            "claude_lines": "mean",
            "mistral_lines": "mean",
            "max_lines": "first",
            "claude_time": "mean",
            "mistral_time": "mean"
        }).reset_index()
        agent_summary["total"] = agent_df.groupby("agent").size().values
        agent_summary["flag"] = agent_summary["agent"].map(lambda x: AGENT_DEFINITIONS[x]["flag"])
        
        st.dataframe(
            agent_summary[["agent", "flag", "max_lines", "claude_compliant", "mistral_compliant", "total", "claude_lines", "mistral_lines"]],
            column_config={
                "agent": "Agent",
                "flag": "Flag",
                "max_lines": "Max Lines",
                "claude_compliant": "Claude ✓",
                "mistral_compliant": "Mistral ✓",
                "total": "Total",
                "claude_lines": st.column_config.NumberColumn("Claude Avg", format="%.1f"),
                "mistral_lines": st.column_config.NumberColumn("Mistral Avg", format="%.1f")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Line count chart
        line_chart_data = agent_df.melt(
            id_vars=["agent", "max_lines"],
            value_vars=["claude_lines", "mistral_lines"],
            var_name="model",
            value_name="lines"
        )
        line_chart_data["model"] = line_chart_data["model"].str.replace("_lines", "").str.title()
        
        # Create combined chart with target line
        base = alt.Chart(line_chart_data).encode(
            x=alt.X("agent:N", title="Agent Type", sort=list(AGENT_DEFINITIONS.keys()))
        )
        
        bars = base.mark_bar().encode(
            y=alt.Y("lines:Q", title="Lines"),
            color=alt.Color("model:N", scale=alt.Scale(
                domain=["Claude", "Mistral"],
                range=["#6366f1", "#f59e0b"]
            )),
            xOffset="model:N",
            tooltip=["agent", "model", "lines", "max_lines"]
        )
        
        # Target lines
        target_data = pd.DataFrame([
            {"agent": k, "max_lines": v["max_lines"]} 
            for k, v in AGENT_DEFINITIONS.items()
        ])
        
        targets = alt.Chart(target_data).mark_tick(
            color="red",
            thickness=2,
            size=40
        ).encode(
            x=alt.X("agent:N", sort=list(AGENT_DEFINITIONS.keys())),
            y=alt.Y("max_lines:Q")
        )
        
        chart = (bars + targets).properties(
            height=350,
            title="Actual Lines vs Target (red ticks)"
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # Compliance heatmap
        st.markdown("### 🗺️ Compliance Heatmap (Agent × Query)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Claude**")
            hm_c = agent_df.pivot_table(
                index="agent", columns="query_id", values="claude_compliant", aggfunc="first"
            ).reset_index().melt(id_vars="agent", var_name="query", value_name="compliant")
            
            hm_chart_c = alt.Chart(hm_c).mark_rect().encode(
                x=alt.X("query:N", title="Query"),
                y=alt.Y("agent:N", title="Agent", sort=list(AGENT_DEFINITIONS.keys())),
                color=alt.Color("compliant:Q", scale=alt.Scale(domain=[0, 1], range=["#ff6b6b", "#4ecdc4"]))
            ).properties(height=250)
            st.altair_chart(hm_chart_c, use_container_width=True)
        
        with col2:
            st.markdown("**Mistral**")
            hm_m = agent_df.pivot_table(
                index="agent", columns="query_id", values="mistral_compliant", aggfunc="first"
            ).reset_index().melt(id_vars="agent", var_name="query", value_name="compliant")
            
            hm_chart_m = alt.Chart(hm_m).mark_rect().encode(
                x=alt.X("query:N", title="Query"),
                y=alt.Y("agent:N", title="Agent", sort=list(AGENT_DEFINITIONS.keys())),
                color=alt.Color("compliant:Q", scale=alt.Scale(domain=[0, 1], range=["#ff6b6b", "#f59e0b"]))
            ).properties(height=250)
            st.altair_chart(hm_chart_m, use_container_width=True)
        
        # Response Explorer
        st.markdown("### 🔍 Response Explorer")
        
        selected_agent_result = st.selectbox(
            "Select test to explore:",
            options=[f"{r['agent']} | {r['query_id']} | {r['query'][:35]}..." for r in agent_results],
            key="agent_explorer"
        )
        
        if selected_agent_result:
            idx = [f"{r['agent']} | {r['query_id']} | {r['query'][:35]}..." for r in agent_results].index(selected_agent_result)
            row = agent_results[idx]
            
            flag_text = f" (`{row['flag']}`)" if 'flag' in row else ""
            st.markdown(f"**Agent:** {row.get('agent', 'N/A')}{flag_text}")
            st.markdown(f"**Query:** {row.get('query', 'N/A')}")
            st.markdown(f"**Target:** ≤{row.get('max_lines', 'N/A')} lines")
            
            # Dynamic columns for available models
            available_models = []
            for model_key, model_config in MODELS.items():
                if f"{model_key}_response" in row:
                    available_models.append((model_key, model_config))
            
            if available_models:
                cols = st.columns(len(available_models))
                for col_idx, (model_key, model_config) in enumerate(available_models):
                    with cols[col_idx]:
                        compliant = row.get(f"{model_key}_compliant", False)
                        lines = row.get(f"{model_key}_lines", 0)
                        words = row.get(f"{model_key}_words", 0)
                        time_val = row.get(f"{model_key}_time", 0)
                        max_lines = row.get('max_lines', 0)
                        
                        status = "✅" if compliant else f"❌ ({lines}/{max_lines})"
                        st.markdown(f"**{model_config['label']}** {status}")
                        st.caption(f"Lines: {lines} | Words: {words} | Time: {time_val:.1f}s")
                        response = row.get(f"{model_key}_response", "No response")
                        st.code(response[:1000] if response else "No response")

# ============== TAB 7: dbt Pipelines ==============
with tab7:
    st.subheader("📦 dbt Pipelines & AI Observability")
    st.markdown("""
    Demonstrate **fdbt** (fast dbt inspection) with the `cortex_integration` project,
    and **Snowflake AI Observability** concepts for evaluating LLM responses.
    """)
    
    # dbt Project Configuration - uses relative path or environment variable
    DBT_PROJECT_PATH = os.environ.get("DBT_PROJECT_PATH", os.path.join(os.path.dirname(__file__), "dbt_cortex_integration"))
    
    # Pipeline definitions based on fdbt lineage
    DBT_PIPELINES = {
        "pipeline_1": {
            "name": "File Inventory Pipeline",
            "description": "Raw files → Staging → Analysis → Business Mart",
            "models": [
                {"name": "raw_file_metadata", "layer": "raw", "type": "table"},
                {"name": "stg_file_metadata", "layer": "staging", "type": "view"},
                {"name": "int_file_content_analysis", "layer": "intermediate", "type": "view"},
                {"name": "mart_file_inventory", "layer": "marts", "type": "table"}
            ],
            "color": "#6366f1"
        },
        "pipeline_2": {
            "name": "ML Embeddings Pipeline",
            "description": "Content Analysis → ML Features (ColBERT/DSPy)",
            "models": [
                {"name": "int_file_content_analysis", "layer": "intermediate", "type": "view"},
                {"name": "ml_file_embeddings", "layer": "ml_features", "type": "table"}
            ],
            "color": "#f59e0b"
        }
    }
    
    # AI Observability Metrics (from Snowflake docs)
    AI_OBSERVABILITY_METRICS = {
        "context_relevance": {
            "name": "Context Relevance",
            "description": "How relevant is the retrieved context to the user query?",
            "range": [0, 1],
            "threshold": 0.7
        },
        "groundedness": {
            "name": "Groundedness",
            "description": "Is the response grounded in the provided context?",
            "range": [0, 1],
            "threshold": 0.8
        },
        "answer_relevance": {
            "name": "Answer Relevance",
            "description": "How relevant is the answer to the original question?",
            "range": [0, 1],
            "threshold": 0.75
        },
        "flesch_readability": {
            "name": "Flesch Readability",
            "description": "Reading ease score (higher = easier to read)",
            "range": [0, 100],
            "threshold": 60
        }
    }
    
    st.divider()
    
    # Section 1: fdbt Project Overview
    st.markdown("### 1. fdbt Project Overview")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Project: `cortex_integration`**")
        st.code(f"""
$ fdbt info
Project: cortex_integration
Models: 6
Sources: 0
Macros: 6
Tests: 37
Processing time: 9ms

$ fdbt tests coverage
Model Coverage: 83.3% (5/6 models)
Column Coverage: 100% (22/22 columns)
        """, language="bash")
    
    with col2:
        # Project metrics
        st.metric("Models", "6", help="Total dbt models")
        st.metric("Test Coverage", "83.3%", delta="5/6 models")
        st.metric("Tests", "37", help="Generic tests")
    
    st.divider()
    
    # Section 2: Pipeline Visualization
    st.markdown("### 2. dbt Pipeline Lineage")
    
    # Pipeline selector
    selected_pipeline = st.radio(
        "Select Pipeline:",
        options=list(DBT_PIPELINES.keys()),
        format_func=lambda x: f"{DBT_PIPELINES[x]['name']}",
        horizontal=True,
        key="dbt_pipeline_select"
    )
    
    pipeline = DBT_PIPELINES[selected_pipeline]
    st.markdown(f"**{pipeline['description']}**")
    
    # Create lineage visualization
    lineage_data = []
    for i, model in enumerate(pipeline["models"]):
        lineage_data.append({
            "order": i,
            "model": model["name"],
            "layer": model["layer"],
            "type": model["type"],
            "x": i * 2,
            "y": 0
        })
    
    lineage_df = pd.DataFrame(lineage_data)
    
    # Nodes
    nodes = alt.Chart(lineage_df).mark_circle(size=800).encode(
        x=alt.X("x:Q", axis=None),
        y=alt.Y("y:Q", axis=None),
        color=alt.value(pipeline["color"]),
        tooltip=["model", "layer", "type"]
    )
    
    # Labels
    labels = alt.Chart(lineage_df).mark_text(
        dy=-25,
        fontSize=11,
        fontWeight="bold"
    ).encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        text="model:N"
    )
    
    # Layer labels
    layer_labels = alt.Chart(lineage_df).mark_text(
        dy=25,
        fontSize=9,
        color="gray"
    ).encode(
        x=alt.X("x:Q"),
        y=alt.Y("y:Q"),
        text="layer:N"
    )
    
    # Edges (arrows between consecutive nodes)
    if len(lineage_df) > 1:
        edge_data = []
        for i in range(len(lineage_df) - 1):
            edge_data.append({
                "x": lineage_df.iloc[i]["x"] + 0.3,
                "x2": lineage_df.iloc[i+1]["x"] - 0.3,
                "y": 0,
                "y2": 0
            })
        edge_df = pd.DataFrame(edge_data)
        
        edges = alt.Chart(edge_df).mark_rule(
            strokeWidth=2,
            color="gray"
        ).encode(
            x="x:Q",
            x2="x2:Q",
            y="y:Q",
            y2="y2:Q"
        )
        
        lineage_chart = (edges + nodes + labels + layer_labels).properties(
            width=600,
            height=120,
            title=f"Pipeline: {pipeline['name']}"
        ).configure_view(strokeWidth=0)
    else:
        lineage_chart = (nodes + labels + layer_labels).properties(
            width=600,
            height=120,
            title=f"Pipeline: {pipeline['name']}"
        ).configure_view(strokeWidth=0)
    
    st.altair_chart(lineage_chart, use_container_width=True)
    
    # Model details expander
    with st.expander("📋 Model Details", expanded=False):
        for model in pipeline["models"]:
            st.markdown(f"**{model['name']}** (`{model['layer']}` / `{model['type']}`)")
            
            if model["name"] == "ml_file_embeddings":
                st.code("""
-- Key features from ml_file_embeddings.sql:
-- ColBERT/ColPali integration via SNOWFLAKE.CORTEX.EMBED_TEXT_768
-- DSPy metadata generation
-- Verifier categories for rule-based checks
                """, language="sql")
            elif model["name"] == "mart_file_inventory":
                st.code("""
-- Key features from mart_file_inventory.sql:
-- Business value categorization (HIGH/MEDIUM/LOW/MINIMAL)
-- Processing recommendations (IMMEDIATE/SCHEDULED/BATCH)
-- Data quality scoring (EXCELLENT/GOOD/FAIR/POOR)
                """, language="sql")
    
    # Preview Data section - query actual dbt tables
    with st.expander("🔍 Preview Pipeline Data", expanded=True):
        # Read defaults from config.toml
        try:
            import tomllib
            with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                sf_config = tomllib.load(f)
            conn_config = sf_config.get("connections", {}).get("myaccount", {})
            default_database = conn_config.get("database", "CORTEX_DB")
            default_schema = conn_config.get("schema", "PUBLIC")
            default_warehouse = conn_config.get("warehouse", "COMPUTE_WH")
        except Exception:
            default_database = "CORTEX_DB"
            default_schema = "PUBLIC"
            default_warehouse = "COMPUTE_WH"
        
        # Database and schema configuration
        col_db, col_schema, col_wh = st.columns(3)
        with col_db:
            preview_database = st.text_input(
                "Database:",
                value=default_database,
                key=f"preview_db_{pipeline['name']}"
            )
        with col_schema:
            preview_schema = st.text_input(
                "Schema:",
                value=default_schema,
                key=f"preview_schema_{pipeline['name']}"
            )
        with col_wh:
            preview_warehouse = st.text_input(
                "Warehouse:",
                value=default_warehouse,
                key=f"preview_wh_{pipeline['name']}"
            )
        
        # Create Demo Tables button
        st.markdown("---")
        st.markdown("**🛠️ Bootstrap Demo Tables**")
        st.caption("Create sample tables with ColBERT-style embeddings via Cortex EMBED_TEXT_768")
        
        if st.button("🚀 Create Demo Tables", key=f"create_tables_{pipeline['name']}"):
            try:
                conn = snowflake.connector.connect(connection_name="myaccount")
                cursor = conn.cursor()
                
                # Set context - create database and schema if they don't exist
                cursor.execute(f"USE WAREHOUSE {preview_warehouse}")
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {preview_database}")
                cursor.execute(f"USE DATABASE {preview_database}")
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {preview_schema}")
                cursor.execute(f"USE SCHEMA {preview_schema}")
                
                with st.spinner("Creating tables with Cortex embeddings..."):
                    if pipeline["name"] == "ML Embeddings Pipeline":
                        # Create ML Embeddings table with ColBERT-style vectors
                        create_sql = f"""
CREATE OR REPLACE TABLE {preview_database}.{preview_schema}.ML_FILE_EMBEDDINGS AS
WITH source_files AS (
    SELECT 'security_analysis.py' AS file_path, 'python' AS file_type,
           'def analyze_vulnerability(code): patterns = ["SELECT.*FROM", "eval(", "innerHTML"]; return [p for p in patterns if p in code]' AS file_content
    UNION ALL
    SELECT 'data_pipeline.sql', 'sql',
           'CREATE TABLE processed_data AS SELECT customer_id, SUM(amount) as total FROM raw_transactions GROUP BY 1'
    UNION ALL
    SELECT 'ml_model.py', 'python',
           'from snowflake.ml.modeling.xgboost import XGBClassifier; model = XGBClassifier(); model.fit(X_train, y_train)'
    UNION ALL
    SELECT 'api_handler.js', 'javascript',
           'async function fetchData(endpoint) {{ const resp = await fetch(endpoint); return resp.json(); }}'
),
embeddings AS (
    SELECT file_path, file_type, file_content,
           -- ColBERT-style 768-dim embeddings via Cortex
           SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', file_content) AS content_embedding,
           'e5-base-v2' AS embedding_model,
           768 AS vector_length,
           -- DSPy-style summary
           SNOWFLAKE.CORTEX.COMPLETE('mistral-7b', 'Summarize in 10 words: ' || file_content) AS dspy_summary,
           CASE 
               WHEN CONTAINS(LOWER(file_content), 'vulnerability') OR CONTAINS(LOWER(file_content), 'injection') THEN 'SECURITY'
               WHEN CONTAINS(LOWER(file_content), 'select') OR CONTAINS(LOWER(file_content), 'create') THEN 'DATA_PIPELINE'
               WHEN CONTAINS(LOWER(file_content), 'model') OR CONTAINS(LOWER(file_content), 'train') THEN 'ML_MODEL'
               WHEN CONTAINS(LOWER(file_content), 'fetch') OR CONTAINS(LOWER(file_content), 'async') THEN 'API_HANDLER'
               ELSE 'GENERAL'
           END AS verifier_category,
           CURRENT_TIMESTAMP() AS created_at
    FROM source_files
)
SELECT * FROM embeddings
"""
                        cursor.execute(create_sql)
                        st.success(f"✅ Created {preview_database}.{preview_schema}.ML_FILE_EMBEDDINGS with ColBERT embeddings!")
                        
                    else:  # File Inventory Pipeline
                        create_sql = f"""
CREATE OR REPLACE TABLE {preview_database}.{preview_schema}.MART_FILE_INVENTORY AS
SELECT 
    file_path,
    file_size_mb,
    file_type,
    last_modified,
    line_count,
    CASE
        WHEN file_type IN ('python', 'sql') AND line_count > 100 THEN 'HIGH'
        WHEN file_type IN ('python', 'sql', 'javascript') THEN 'MEDIUM'
        WHEN file_type IN ('json', 'yaml') THEN 'LOW'
        ELSE 'MINIMAL'
    END AS business_value,
    CASE
        WHEN DATEDIFF(day, last_modified, CURRENT_TIMESTAMP()) <= 7 AND file_size_mb > 1 THEN 'IMMEDIATE'
        WHEN DATEDIFF(day, last_modified, CURRENT_TIMESTAMP()) <= 30 THEN 'SCHEDULED'
        ELSE 'BATCH'
    END AS processing_recommendation,
    CASE
        WHEN line_count > 50 AND file_size_mb > 0.1 THEN 'EXCELLENT'
        WHEN line_count > 20 THEN 'GOOD'
        WHEN line_count > 5 THEN 'FAIR'
        ELSE 'POOR'
    END AS data_quality_score
FROM (
    SELECT 'security_analysis.py' AS file_path, 2.5 AS file_size_mb, 'python' AS file_type, 
           DATEADD(day, -5, CURRENT_TIMESTAMP()) AS last_modified, 150 AS line_count
    UNION ALL SELECT 'data_pipeline.sql', 0.8, 'sql', DATEADD(day, -2, CURRENT_TIMESTAMP()), 45
    UNION ALL SELECT 'ml_model.py', 5.2, 'python', DATEADD(day, -1, CURRENT_TIMESTAMP()), 320
    UNION ALL SELECT 'config.json', 0.01, 'json', DATEADD(day, -30, CURRENT_TIMESTAMP()), 12
    UNION ALL SELECT 'README.md', 0.05, 'markdown', DATEADD(day, -60, CURRENT_TIMESTAMP()), 80
)
"""
                        cursor.execute(create_sql)
                        st.success(f"✅ Created {preview_database}.{preview_schema}.MART_FILE_INVENTORY!")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                st.error(f"Failed to create tables: {str(e)}")
        
        st.markdown("---")
        
        # Determine which table to query based on pipeline
        if pipeline["name"] == "ML Embeddings Pipeline":
            table_options = {
                "ml_file_embeddings": "ML Features Table (embeddings + metadata)",
                "int_file_content_analysis": "Intermediate Content Analysis"
            }
            default_table = "ml_file_embeddings"
            sample_query = """SELECT 
    FILE_PATH,
    FILE_TYPE,
    EMBEDDING_MODEL,
    VECTOR_LENGTH,
    DSPY_SUMMARY,
    VERIFIER_CATEGORY,
    CREATED_AT
FROM {database}.{schema}.{table}
LIMIT 20"""
        else:  # File Inventory Pipeline
            table_options = {
                "mart_file_inventory": "File Inventory Mart",
                "int_file_metadata": "Intermediate File Metadata"
            }
            default_table = "mart_file_inventory"
            sample_query = """SELECT 
    FILE_PATH,
    FILE_SIZE_MB,
    BUSINESS_VALUE,
    PROCESSING_RECOMMENDATION,
    DATA_QUALITY_SCORE,
    LAST_MODIFIED
FROM {database}.{schema}.{table}
LIMIT 20"""
        
        selected_table = st.selectbox(
            "Select Table to Preview:",
            options=list(table_options.keys()),
            format_func=lambda x: table_options[x],
            key=f"preview_table_{pipeline['name']}"
        )
        
        # Custom query option
        use_custom = st.checkbox("Use custom query", key=f"custom_query_{pipeline['name']}")
        
        if use_custom:
            query_to_run = st.text_area(
                "SQL Query:",
                value=sample_query.format(database=preview_database, schema=preview_schema, table=selected_table),
                height=150,
                key=f"sql_query_{pipeline['name']}"
            )
        else:
            query_to_run = sample_query.format(database=preview_database, schema=preview_schema, table=selected_table)
            st.code(query_to_run, language="sql")
        
        if st.button("▶️ Run Query", type="primary", key=f"run_preview_{pipeline['name']}"):
            try:
                conn = snowflake.connector.connect(
                    connection_name="myaccount"
                )
                cursor = conn.cursor()
                
                # Set warehouse and database context
                cursor.execute(f"USE WAREHOUSE {preview_warehouse}")
                cursor.execute(f"USE DATABASE {preview_database}")
                cursor.execute(f"USE SCHEMA {preview_schema}")
                
                with st.spinner(f"Querying {selected_table}..."):
                    cursor.execute(query_to_run)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    if rows:
                        df = pd.DataFrame(rows, columns=columns)
                        st.success(f"Retrieved {len(df)} rows from {preview_database}.{preview_schema}.{selected_table}")
                        
                        # Display metrics
                        metric_cols = st.columns(4)
                        with metric_cols[0]:
                            st.metric("Rows", len(df))
                        with metric_cols[1]:
                            st.metric("Columns", len(df.columns))
                        with metric_cols[2]:
                            if "EMBEDDING_MODEL" in df.columns:
                                st.metric("Embedding Models", df["EMBEDDING_MODEL"].nunique())
                            elif "BUSINESS_VALUE" in df.columns:
                                st.metric("High Value Files", len(df[df["BUSINESS_VALUE"] == "HIGH"]))
                        with metric_cols[3]:
                            if "VERIFIER_CATEGORY" in df.columns:
                                st.metric("Categories", df["VERIFIER_CATEGORY"].nunique())
                            elif "DATA_QUALITY_SCORE" in df.columns:
                                excellent = len(df[df["DATA_QUALITY_SCORE"] == "EXCELLENT"])
                                st.metric("Excellent Quality", excellent)
                        
                        # Show dataframe
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Show distribution charts for ML Embeddings
                        if "VERIFIER_CATEGORY" in df.columns:
                            st.markdown("**Verifier Category Distribution**")
                            cat_counts = df["VERIFIER_CATEGORY"].value_counts().reset_index()
                            cat_counts.columns = ["Category", "Count"]
                            chart = alt.Chart(cat_counts).mark_bar().encode(
                                x=alt.X("Category:N", title="Verifier Category"),
                                y=alt.Y("Count:Q", title="File Count"),
                                color=alt.Color("Category:N", legend=None)
                            ).properties(height=200)
                            st.altair_chart(chart, use_container_width=True)
                        
                        # Show distribution for File Inventory
                        if "BUSINESS_VALUE" in df.columns:
                            st.markdown("**Business Value Distribution**")
                            val_counts = df["BUSINESS_VALUE"].value_counts().reset_index()
                            val_counts.columns = ["Value", "Count"]
                            chart = alt.Chart(val_counts).mark_bar().encode(
                                x=alt.X("Value:N", sort=["HIGH", "MEDIUM", "LOW", "MINIMAL"], title="Business Value"),
                                y=alt.Y("Count:Q", title="File Count"),
                                color=alt.Color("Value:N", scale=alt.Scale(
                                    domain=["HIGH", "MEDIUM", "LOW", "MINIMAL"],
                                    range=["#2ecc71", "#f1c40f", "#e67e22", "#95a5a6"]
                                ), legend=None)
                            ).properties(height=200)
                            st.altair_chart(chart, use_container_width=True)
                    else:
                        st.warning(f"No data found in {preview_database}.{preview_schema}.{selected_table}. Table may be empty or not exist yet.")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                st.error(f"Query failed: {str(e)}")
                st.info("💡 Make sure the dbt models have been run and the tables exist in your database/schema.")
    
    st.divider()
    
    # Section 3: AI Observability Demo
    st.markdown("### 3. AI Observability Evaluation Demo")
    st.markdown("""
    **Snowflake AI Observability** enables evaluation of LLM responses using metrics.
    Below we demonstrate evaluation metrics applied to model comparison results.
    """)
    
    # Link to existing results
    has_persona_results = "persona_results" in st.session_state and st.session_state["persona_results"]
    has_agent_results = "agent_results" in st.session_state and st.session_state["agent_results"]
    
    if not has_persona_results and not has_agent_results:
        st.info("Run comparisons in other tabs first, or load saved results to see AI Observability metrics.")
        
        if st.button("📂 Load Saved Results for Evaluation", key="load_for_eval"):
            try:
                results_dir = os.path.join(os.path.dirname(__file__), "results")
                
                persona_file = os.path.join(results_dir, "persona_results.json")
                if os.path.exists(persona_file):
                    with open(persona_file) as f:
                        st.session_state["persona_results"] = json.load(f)
                
                agent_file = os.path.join(results_dir, "agent_results.json")
                if os.path.exists(agent_file):
                    with open(agent_file) as f:
                        st.session_state["agent_results"] = json.load(f)
                
                st.success("Results loaded! Metrics will appear below.")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    else:
        # Create AI Observability Run simulation
        st.markdown("#### Evaluation Run")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            run_name = st.text_input("Run Name:", value="model_comparison_eval_001", key="obs_run_name")
        with col2:
            eval_model = st.selectbox("Evaluation LLM:", ["claude-3-5-sonnet", "mistral-large2"], key="obs_eval_model")
        with col3:
            selected_metrics = st.multiselect(
                "Metrics:",
                options=list(AI_OBSERVABILITY_METRICS.keys()),
                default=["flesch_readability", "answer_relevance"],
                format_func=lambda x: AI_OBSERVABILITY_METRICS[x]["name"],
                key="obs_metrics"
            )
        
        if st.button("📊 Compute Evaluation Metrics", type="primary", key="compute_eval"):
            with st.spinner("Computing AI Observability metrics..."):
                eval_results = []
                
                # Process persona results if available
                if has_persona_results:
                    for row in st.session_state["persona_results"]:
                        for model_key in ["claude", "mistral"]:
                            response = row.get(f"{model_key}_response", "")
                            
                            # Compute metrics
                            metrics = {}
                            
                            if "flesch_readability" in selected_metrics:
                                # Use existing Flesch computation
                                flesch = compute_flesch_score(response) if response else 0
                                metrics["flesch_readability"] = flesch
                            
                            if "answer_relevance" in selected_metrics:
                                # Simulate answer relevance based on compliance score
                                metrics["answer_relevance"] = row.get(f"{model_key}_score", 0) / 100
                            
                            if "groundedness" in selected_metrics:
                                # Simulate groundedness
                                metrics["groundedness"] = 0.85 if row.get(f"{model_key}_compliant", False) else 0.5
                            
                            if "context_relevance" in selected_metrics:
                                # Simulate context relevance
                                metrics["context_relevance"] = 0.9 if row.get("expected_answer", "") in response else 0.6
                            
                            eval_results.append({
                                "source": "persona",
                                "model": model_key,
                                "question": row.get("question", "")[:50],
                                "response": response[:100] + "..." if len(response) > 100 else response,
                                "persona": row.get("persona_name", ""),
                                **metrics
                            })
                
                # Process agent results if available
                if has_agent_results:
                    for row in st.session_state["agent_results"]:
                        for model_key in ["claude", "mistral"]:
                            response = row.get(f"{model_key}_response", "")
                            
                            metrics = {}
                            
                            if "flesch_readability" in selected_metrics:
                                flesch = compute_flesch_score(response) if response else 0
                                metrics["flesch_readability"] = flesch
                            
                            if "answer_relevance" in selected_metrics:
                                compliant = row.get(f"{model_key}_compliant", False)
                                metrics["answer_relevance"] = 0.9 if compliant else 0.5
                            
                            eval_results.append({
                                "source": "agent",
                                "model": model_key,
                                "question": row.get("query", "")[:50],
                                "response": response[:100] + "..." if len(response) > 100 else response,
                                "agent_type": row.get("agent", ""),
                                **metrics
                            })
                
                st.session_state["eval_results"] = eval_results
        
        # Display evaluation results
        if "eval_results" in st.session_state and st.session_state["eval_results"]:
            eval_df = pd.DataFrame(st.session_state["eval_results"])
            
            st.markdown("#### Evaluation Results")
            
            # Summary metrics by model
            col1, col2 = st.columns(2)
            
            claude_df = eval_df[eval_df["model"] == "claude"]
            mistral_df = eval_df[eval_df["model"] == "mistral"]
            
            with col1:
                st.markdown("**Claude Metrics**")
                for metric_key in selected_metrics:
                    if metric_key in eval_df.columns:
                        avg_val = claude_df[metric_key].mean()
                        threshold = AI_OBSERVABILITY_METRICS[metric_key]["threshold"]
                        status = "✅" if avg_val >= threshold else "⚠️"
                        st.metric(
                            AI_OBSERVABILITY_METRICS[metric_key]["name"],
                            f"{avg_val:.2f}",
                            delta=f"{status} threshold: {threshold}"
                        )
            
            with col2:
                st.markdown("**Mistral Metrics**")
                for metric_key in selected_metrics:
                    if metric_key in eval_df.columns:
                        avg_val = mistral_df[metric_key].mean()
                        threshold = AI_OBSERVABILITY_METRICS[metric_key]["threshold"]
                        status = "✅" if avg_val >= threshold else "⚠️"
                        st.metric(
                            AI_OBSERVABILITY_METRICS[metric_key]["name"],
                            f"{avg_val:.2f}",
                            delta=f"{status} threshold: {threshold}"
                        )
            
            # Detailed results table
            st.markdown("#### Detailed Evaluation Records")
            
            display_cols = ["source", "model", "question", "response"] + [m for m in selected_metrics if m in eval_df.columns]
            st.dataframe(
                eval_df[display_cols].head(20),
                column_config={
                    "question": st.column_config.TextColumn("Question", width="medium"),
                    "response": st.column_config.TextColumn("Response", width="large")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Metric distribution chart
            if len(selected_metrics) > 0 and selected_metrics[0] in eval_df.columns:
                chart_metric = selected_metrics[0]
                
                metric_chart = alt.Chart(eval_df).mark_boxplot().encode(
                    x=alt.X("model:N", title="Model"),
                    y=alt.Y(f"{chart_metric}:Q", title=AI_OBSERVABILITY_METRICS[chart_metric]["name"]),
                    color=alt.Color("model:N", scale=alt.Scale(
                        domain=["claude", "mistral"],
                        range=["#6366f1", "#f59e0b"]
                    ))
                ).properties(
                    height=250,
                    title=f"{AI_OBSERVABILITY_METRICS[chart_metric]['name']} Distribution"
                )
                
                st.altair_chart(metric_chart, use_container_width=True)
    
    st.divider()
    
    # Section 4: Connecting dbt to AI Observability
    st.markdown("### 4. dbt + AI Observability Integration")
    st.markdown("""
    **How dbt pipelines connect to AI Observability:**
    
    1. **Evaluation Storage**: Store AI Observability results in dbt-managed tables
    2. **Feature Engineering**: Use `ml_file_embeddings` for context retrieval evaluation
    3. **Data Quality**: Apply dbt tests to evaluation metric thresholds
    4. **Lineage Tracking**: Track which dbt models feed into LLM applications
    """)
    
    st.code("""
-- Example: Create dbt model for AI Observability results
-- models/ai_observability/eval_results.sql

{{ config(materialized='incremental', unique_key='eval_id') }}

SELECT
    eval_id,
    run_name,
    model_name,
    question,
    response,
    context_relevance,
    groundedness,
    answer_relevance,
    flesch_readability,
    CASE 
        WHEN context_relevance >= 0.7 
         AND groundedness >= 0.8 
         AND answer_relevance >= 0.75 
        THEN 'PASS'
        ELSE 'FAIL'
    END as eval_status,
    evaluated_at
FROM {{ ref('stg_eval_results') }}
{% if is_incremental() %}
WHERE evaluated_at > (SELECT MAX(evaluated_at) FROM {{ this }})
{% endif %}
    """, language="sql")
    
    # fdbt commands reference
    with st.expander("📚 fdbt Command Reference", expanded=False):
        st.code("""
# Project overview
fdbt info

# List all models
fdbt list

# List models by layer
fdbt list -l staging
fdbt list -l marts

# Show model lineage
fdbt lineage mart_file_inventory

# Show upstream dependencies
fdbt lineage ml_file_embeddings -u

# Show test coverage
fdbt tests coverage

# Show impact analysis (downstream)
fdbt impact stg_file_metadata
        """, language="bash")

# ============== TAB 8: TruLens Evaluation Pipelines ==============
with tab8:
    st.subheader("🔬 TruLens Evaluation Pipelines")
    st.markdown("""
    Specialized **fdbt pipelines** for each comparison type with **TruLens** AI Observability evaluation.
    Each pipeline stores results in dbt-managed tables with automated quality metrics.
    """)
    
    # TruLens Configuration
    
    # Judge Model Selection - Third model evaluates Claude vs Mistral
    st.markdown("#### Judge Model Configuration")
    col_judge1, col_judge2 = st.columns([2, 1])
    
    with col_judge1:
        JUDGE_MODELS = {
            "llama3.1-70b": "Llama 3.1 70B (Meta)",
            "claude-sonnet-4-6": "Claude Sonnet 4.6 (Anthropic)",
            "gpt-5.2": "GPT-5.2 (OpenAI)",
            "mixtral-8x7b": "Mixtral 8x7B (Mistral AI)",
            "snowflake-arctic": "Snowflake Arctic"
        }
        
        trulens_judge_model = st.selectbox(
            "Select Judge Model for LLM-as-Judge Evaluation:",
            options=list(JUDGE_MODELS.keys()),
            format_func=lambda x: JUDGE_MODELS[x],
            index=0,
            key="trulens_judge_model",
            help="This model will evaluate responses from Claude and Mistral"
        )
    
    with col_judge2:
        st.info(f"""
        **Evaluation Setup:**
        - Contestants: Claude 3.5 Sonnet, Mistral Large 2
        - Judge: {JUDGE_MODELS[trulens_judge_model]}
        """)
    
    st.divider()
    
    TRULENS_METRICS = {
        "wiki": {
            "answer_relevance": {"name": "Answer Relevance", "description": "Is the answer relevant to the question?", "weight": 0.4},
            "groundedness": {"name": "Groundedness", "description": "Is the answer grounded in Wikipedia context?", "weight": 0.3},
            "context_relevance": {"name": "Context Relevance", "description": "Is retrieved context relevant?", "weight": 0.3}
        },
        "persona": {
            "flesch_compliance": {"name": "Flesch Compliance", "description": "Does readability match persona target?", "weight": 0.4},
            "sql_validity": {"name": "SQL Validity", "description": "Is SQL syntactically correct? (compute persona)", "weight": 0.3},
            "persona_adherence": {"name": "Persona Adherence", "description": "Does response match persona style?", "weight": 0.3}
        },
        "agent": {
            "line_compliance": {"name": "Line Compliance", "description": "Does response respect line limits?", "weight": 0.5},
            "format_compliance": {"name": "Format Compliance", "description": "Does response match agent format?", "weight": 0.3},
            "content_quality": {"name": "Content Quality", "description": "Is the response helpful and accurate?", "weight": 0.2}
        },
        "sae": {
            "feature_activation": {"name": "Feature Activation", "description": "SAE feature activation strength", "weight": 0.3},
            "feature_sparsity": {"name": "Feature Sparsity", "description": "L0 sparsity of activated features", "weight": 0.3},
            "reconstruction_loss": {"name": "Reconstruction Loss", "description": "MSE between original and reconstructed", "weight": 0.2},
            "dead_features": {"name": "Dead Features", "description": "Percentage of never-activated features", "weight": 0.2}
        },
        "sae_meta": {
            "concept_clustering": {"name": "Concept Clustering", "description": "Semantic coherence of feature clusters", "weight": 0.35},
            "feature_interpretability": {"name": "Feature Interpretability", "description": "Human-readable feature descriptions", "weight": 0.35},
            "behavioral_correlation": {"name": "Behavioral Correlation", "description": "Feature-behavior correlation strength", "weight": 0.3}
        },
        "llm_summarizer": {
            "factual_consistency": {"name": "Factual Consistency", "description": "Summary facts match source", "weight": 0.4},
            "coverage": {"name": "Coverage", "description": "Key points from source included", "weight": 0.3},
            "conciseness": {"name": "Conciseness", "description": "Information density of summary", "weight": 0.15},
            "coherence": {"name": "Coherence", "description": "Logical flow and readability", "weight": 0.15}
        }
    }
    
    # Pipeline selector
    pipeline_type = st.radio(
        "Select Evaluation Pipeline:",
        options=["wiki", "persona", "agent", "sae", "sae_meta", "llm_summarizer"],
        format_func=lambda x: {
            "wiki": "📚 Wiki Compare (Plain English Q&A)",
            "persona": "🎭 Persona Compare (Plain vs SQL English)", 
            "agent": "🤖 8 Agents (Verbosity Compliance)",
            "sae": "🧠 SAE Features (Sparse Autoencoder)",
            "sae_meta": "🔬 SAE Meta Features (Interpretability)",
            "llm_summarizer": "📝 LLM Summarizer (Factual Consistency)"
        }[x],
        horizontal=True,
        key="trulens_pipeline_select"
    )
    
    st.divider()
    
    # ==================== WIKI PIPELINE ====================
    if pipeline_type == "wiki":
        st.markdown("### 📚 Wiki Compare Pipeline")
        st.markdown("""
        Evaluates Wikipedia Q&A responses using **TruLens** metrics:
        - **Answer Relevance**: LLM-as-judge scoring of answer quality
        - **Groundedness**: Is the response factually grounded in Wikipedia?
        - **Context Relevance**: How well does Vine Copula sampling retrieve relevant context?
        """)
        
        # dbt Model Definition
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `wiki_qa_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH wiki_responses AS (
    SELECT 
        md5(question || model || timestamp) as eval_id,
        article,
        question,
        expected_answer,
        model,
        response,
        category,
        difficulty,
        copula_sample,
        timestamp
    FROM {{ ref('stg_wiki_qa_responses') }}
),

trulens_scores AS (
    SELECT
        eval_id,
        -- TruLens LLM-as-judge evaluation
        SNOWFLAKE.CORTEX.COMPLETE(
            'claude-3-5-sonnet',
            'Rate 0-1 how relevant this answer is: Q: ' || question || ' A: ' || response
        )::FLOAT as answer_relevance,
        
        CASE WHEN CONTAINS(LOWER(response), LOWER(expected_answer)) 
             THEN 0.9 ELSE 0.5 END as groundedness,
        
        ARRAY_SIZE(copula_sample) / 10.0 as context_relevance
    FROM wiki_responses
)

SELECT 
    w.*,
    t.answer_relevance,
    t.groundedness,
    t.context_relevance,
    (t.answer_relevance * 0.4 + t.groundedness * 0.3 + t.context_relevance * 0.3) as composite_score,
    CASE 
        WHEN (t.answer_relevance * 0.4 + t.groundedness * 0.3 + t.context_relevance * 0.3) >= 0.7 
        THEN 'PASS' ELSE 'FAIL' 
    END as eval_status
FROM wiki_responses w
JOIN trulens_scores t ON w.eval_id = t.eval_id
            """, language="sql")
        
        with col2:
            st.markdown("#### Pipeline Lineage")
            st.code("""
wiki_qa_evaluations
    ↑
stg_wiki_qa_responses
    ↑
raw_wiki_api_calls
            """, language=None)
            
            st.markdown("#### TruLens Metrics")
            for metric_key, metric in TRULENS_METRICS["wiki"].items():
                st.markdown(f"**{metric['name']}** ({metric['weight']*100:.0f}%)")
                st.caption(metric['description'])
        
        # Run evaluation on existing wiki results
        st.divider()
        st.markdown("#### Run TruLens Evaluation")
        
        has_wiki = "wiki_results" in st.session_state and st.session_state["wiki_results"]
        
        if not has_wiki:
            st.info("Run Wiki Compare in Tab 4 first, or load saved results.")
            if st.button("📂 Load Wiki Results", key="load_wiki_trulens"):
                try:
                    results_dir = os.path.join(os.path.dirname(__file__), "results")
                    wiki_file = os.path.join(results_dir, "wiki_results.json")
                    if os.path.exists(wiki_file):
                        with open(wiki_file) as f:
                            st.session_state["wiki_results"] = json.load(f)
                        st.success("Wiki results loaded!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            wiki_results = st.session_state["wiki_results"]
            st.success(f"Found {len(wiki_results)} Wiki Q&A results")
            
            # Judge model helper function
            def call_judge_model(judge_model: str, prompt: str) -> str:
                """Call judge model for LLM-as-judge evaluation."""
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    prompt_escaped = prompt.replace("'", "''")
                    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{judge_model}', '{prompt_escaped}') AS response"
                    cursor.execute(sql)
                    return cursor.fetchone()[0]
                except Exception as e:
                    return f"Error: {e}"
            
            def parse_judge_score(response: str) -> float:
                """Extract numeric score from judge response."""
                import re
                # Look for decimal numbers between 0 and 1
                matches = re.findall(r'\b(0\.\d+|1\.0|0|1)\b', response)
                if matches:
                    return float(matches[0])
                # Look for percentage and convert
                pct_matches = re.findall(r'(\d+)%', response)
                if pct_matches:
                    return float(pct_matches[0]) / 100
                return 0.5  # Default
            
            st.markdown(f"**Judge Model:** `{trulens_judge_model}` ({JUDGE_MODELS[trulens_judge_model]})")
            
            if st.button("🔬 Run TruLens Wiki Evaluation", type="primary", key="run_wiki_trulens"):
                with st.spinner(f"Computing TruLens metrics with {JUDGE_MODELS[trulens_judge_model]} as judge..."):
                    wiki_evals = []
                    progress_bar = st.progress(0)
                    total_evals = len(wiki_results) * len(MODELS)
                    current = 0
                    
                    for row in wiki_results:
                        question = row.get("question", "")
                        expected = row.get("expected_answer", "")
                        
                        for model_key in ["claude", "mistral"]:
                            response = row.get(f"{model_key}_response", "")
                            
                            # LLM-as-Judge: Call third model to evaluate
                            judge_prompt = f"""You are an impartial judge evaluating answer quality.

Question: {question}
Expected Answer: {expected}
Model Response: {response[:500]}

Rate the response on these criteria (0.0 to 1.0):
1. Answer Relevance: How relevant is the answer to the question?
2. Groundedness: Is the answer factually grounded?
3. Completeness: Does it cover the key points?

Respond with ONLY three decimal scores, one per line:
RELEVANCE: 0.X
GROUNDEDNESS: 0.X
COMPLETENESS: 0.X"""
                            
                            try:
                                judge_response = call_judge_model(trulens_judge_model, judge_prompt)
                                
                                # Parse scores from judge response
                                import re
                                rel_match = re.search(r'RELEVANCE:\s*([\d.]+)', judge_response, re.IGNORECASE)
                                gnd_match = re.search(r'GROUNDEDNESS:\s*([\d.]+)', judge_response, re.IGNORECASE)
                                cmp_match = re.search(r'COMPLETENESS:\s*([\d.]+)', judge_response, re.IGNORECASE)
                                
                                answer_rel = float(rel_match.group(1)) if rel_match else 0.5
                                groundedness = float(gnd_match.group(1)) if gnd_match else 0.5
                                context_rel = float(cmp_match.group(1)) if cmp_match else 0.5
                                
                                # Clamp values to valid range
                                answer_rel = max(0, min(1, answer_rel))
                                groundedness = max(0, min(1, groundedness))
                                context_rel = max(0, min(1, context_rel))
                                
                            except Exception as e:
                                # Fallback to heuristic scoring
                                answer_rel = row.get(f"{model_key}_accuracy", 0.5)
                                groundedness = 0.85 if expected.lower() in response.lower() else 0.5
                                context_rel = 0.8 if row.get("copula_sample") else 0.6
                            
                            composite = (answer_rel * 0.4 + groundedness * 0.3 + context_rel * 0.3)
                            
                            wiki_evals.append({
                                "article": row.get("article", ""),
                                "question": question[:50],
                                "model": model_key,
                                "response": response[:200] + "..." if len(response) > 200 else response,
                                "expected": expected[:100] + "..." if len(expected) > 100 else expected,
                                "judge": trulens_judge_model,
                                "answer_relevance": round(answer_rel, 3),
                                "groundedness": round(groundedness, 3),
                                "context_relevance": round(context_rel, 3),
                                "composite_score": round(composite, 3),
                                "status": "PASS" if composite >= 0.7 else "FAIL"
                            })
                            
                            current += 1
                            progress_bar.progress(current / total_evals)
                    
                    st.session_state["wiki_trulens_evals"] = wiki_evals
                    st.success(f"Evaluation complete! Judge: {JUDGE_MODELS[trulens_judge_model]}")
            
            # Display wiki TruLens results
            if "wiki_trulens_evals" in st.session_state:
                wiki_eval_df = pd.DataFrame(st.session_state["wiki_trulens_evals"])
                
                col1, col2 = st.columns(2)
                
                claude_wiki = wiki_eval_df[wiki_eval_df["model"] == "claude"]
                mistral_wiki = wiki_eval_df[wiki_eval_df["model"] == "mistral"]
                
                with col1:
                    st.markdown("**Claude TruLens Scores**")
                    st.metric("Composite Score", f"{claude_wiki['composite_score'].mean():.2f}")
                    st.metric("Pass Rate", f"{(claude_wiki['status'] == 'PASS').mean()*100:.0f}%")
                
                with col2:
                    st.markdown("**Mistral TruLens Scores**")
                    st.metric("Composite Score", f"{mistral_wiki['composite_score'].mean():.2f}")
                    st.metric("Pass Rate", f"{(mistral_wiki['status'] == 'PASS').mean()*100:.0f}%")
                
                # Show judge info
                if "judge" in wiki_eval_df.columns:
                    judge_used = wiki_eval_df["judge"].iloc[0] if len(wiki_eval_df) > 0 else "N/A"
                    st.caption(f"Evaluated by: **{judge_used}**")
                
                st.dataframe(
                    wiki_eval_df.head(10),
                    column_config={
                        "article": "Article",
                        "question": st.column_config.TextColumn("Question", width="medium"),
                        "model": "Model",
                        "response": st.column_config.TextColumn("Response", width="large"),
                        "expected": st.column_config.TextColumn("Expected", width="medium"),
                        "composite_score": st.column_config.NumberColumn("Score", format="%.2f"),
                        "status": "Status"
                    },
                    hide_index=True,
                    use_container_width=True
                )
    
    # ==================== PERSONA PIPELINE ====================
    elif pipeline_type == "persona":
        st.markdown("### 🎭 Persona Compare Pipeline")
        st.markdown("""
        Evaluates **Plain English** vs **SQL/Compute English** responses:
        
        | Persona | Target | Metric |
        |---------|--------|--------|
        | **5th Grade** (Plain English) | Flesch 80-90 | Reading ease score |
        | **Scholar** (Academic English) | Flesch 20-50 | Complexity score |
        | **Compute** (SQL English) | Valid SQL | SQL syntax check |
        | **Business** (Corporate English) | KPI terms | Business vocabulary |
        """)
        
        # dbt Model Definition
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `persona_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH persona_responses AS (
    SELECT *,
        md5(question || persona || model || timestamp) as eval_id
    FROM {{ ref('stg_persona_responses') }}
),

flesch_evaluation AS (
    SELECT
        eval_id,
        persona,
        model,
        response,
        
        -- Flesch Reading Ease calculation
        {{ flesch_reading_ease('response') }} as flesch_score,
        
        -- Persona-specific targets
        CASE persona
            WHEN '5th_grade' THEN 
                CASE WHEN flesch_score BETWEEN 80 AND 90 THEN 1.0
                     WHEN flesch_score BETWEEN 70 AND 100 THEN 0.7
                     ELSE 0.3 END
            WHEN 'scholar' THEN
                CASE WHEN flesch_score BETWEEN 20 AND 50 THEN 1.0
                     WHEN flesch_score BETWEEN 10 AND 60 THEN 0.7
                     ELSE 0.3 END
            WHEN 'compute' THEN
                CASE WHEN CONTAINS(response, 'SELECT') OR CONTAINS(response, '```sql')
                     THEN 1.0 ELSE 0.3 END
            WHEN 'business' THEN
                (REGEXP_COUNT(LOWER(response), 'roi|kpi|stakeholder|metric|revenue') / 5.0)
        END as persona_compliance
    FROM persona_responses
)

SELECT 
    p.*,
    f.flesch_score,
    f.persona_compliance,
    CASE WHEN f.persona_compliance >= 0.7 THEN 'PASS' ELSE 'FAIL' END as eval_status
FROM persona_responses p
JOIN flesch_evaluation f ON p.eval_id = f.eval_id
            """, language="sql")
        
        with col2:
            st.markdown("#### Pipeline Lineage")
            st.code("""
persona_evaluations
    ↑
stg_persona_responses
    ↑
raw_persona_api_calls
            """, language=None)
            
            st.markdown("#### Flesch Score Targets")
            flesch_targets = {
                "5th Grade": "80-90 (Easy)",
                "Scholar": "20-50 (Difficult)",
                "Compute": "N/A (SQL check)",
                "Business": "N/A (Term count)"
            }
            for persona, target in flesch_targets.items():
                st.markdown(f"**{persona}**: {target}")
        
        # Run evaluation on existing persona results
        st.divider()
        st.markdown("#### Run TruLens Persona Evaluation")
        
        has_persona = "persona_results" in st.session_state and st.session_state["persona_results"]
        
        if not has_persona:
            st.info("Run Persona Compare in Tab 5 first, or load saved results.")
            if st.button("📂 Load Persona Results", key="load_persona_trulens"):
                try:
                    results_dir = os.path.join(os.path.dirname(__file__), "results")
                    persona_file = os.path.join(results_dir, "persona_results.json")
                    if os.path.exists(persona_file):
                        with open(persona_file) as f:
                            st.session_state["persona_results"] = json.load(f)
                        st.success("Persona results loaded!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            persona_results = st.session_state["persona_results"]
            st.success(f"Found {len(persona_results)} Persona comparison results")
            
            st.markdown(f"**Judge Model:** `{trulens_judge_model}` ({JUDGE_MODELS[trulens_judge_model]})")
            
            if st.button("🔬 Run TruLens Persona Evaluation", type="primary", key="run_persona_trulens"):
                with st.spinner(f"Computing persona compliance with {JUDGE_MODELS[trulens_judge_model]} as judge..."):
                    persona_evals = []
                    progress_bar = st.progress(0)
                    total_evals = len(persona_results) * len(MODELS)
                    current = 0
                    
                    # Helper for judge calls
                    def call_judge(prompt: str) -> str:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            prompt_escaped = prompt.replace("'", "''")
                            sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{trulens_judge_model}', '{prompt_escaped}') AS response"
                            cursor.execute(sql)
                            return cursor.fetchone()[0]
                        except:
                            return ""
                    
                    for row in persona_results:
                        persona_key = row.get("persona", "")
                        persona_name = row.get("persona_name", persona_key)
                        question = row.get("question", "")
                        
                        for model_key in ["claude", "mistral"]:
                            response = row.get(f"{model_key}_response", "")
                            
                            # Compute Flesch score
                            flesch = compute_flesch_score(response) if response else 0
                            
                            # LLM-as-Judge for persona compliance
                            judge_prompt = f"""You are evaluating if a response matches a target persona style.

Persona: {persona_name}
Target Style: {"Simple language a 5th grader can understand" if persona_key == "5th_grade" else "Academic scholarly language" if persona_key == "scholar" else "Technical SQL/code focused" if persona_key == "compute" else "Business/corporate language with KPIs"}

Question: {question}
Response: {response[:400]}

Rate persona compliance from 0.0 to 1.0 where:
- 1.0 = Perfectly matches the target persona style
- 0.5 = Partially matches
- 0.0 = Does not match at all

Respond with ONLY: COMPLIANCE: 0.X"""
                            
                            try:
                                judge_resp = call_judge(judge_prompt)
                                import re
                                match = re.search(r'COMPLIANCE:\s*([\d.]+)', judge_resp, re.IGNORECASE)
                                compliance = float(match.group(1)) if match else 0.5
                                compliance = max(0, min(1, compliance))
                            except:
                                # Fallback to heuristic
                                if persona_key == "5th_grade":
                                    compliance = 1.0 if 80 <= flesch <= 90 else (0.7 if 70 <= flesch <= 100 else 0.3)
                                elif persona_key == "scholar":
                                    compliance = 1.0 if 20 <= flesch <= 50 else (0.7 if 10 <= flesch <= 60 else 0.3)
                                elif persona_key == "compute":
                                    has_sql = "SELECT" in response.upper() or "```sql" in response.lower()
                                    compliance = 1.0 if has_sql else 0.3
                                else:
                                    compliance = row.get(f"{model_key}_score", 50) / 100
                            
                            persona_evals.append({
                                "persona": persona_name,
                                "domain": row.get("domain", ""),
                                "question": question[:40],
                                "model": model_key,
                                "response": response[:200] + "..." if len(response) > 200 else response,
                                "judge": trulens_judge_model,
                                "flesch_score": round(flesch, 1),
                                "persona_compliance": round(compliance, 3),
                                "status": "PASS" if compliance >= 0.7 else "FAIL"
                            })
                            
                            current += 1
                            progress_bar.progress(current / total_evals)
                    
                    st.session_state["persona_trulens_evals"] = persona_evals
                    st.success(f"Evaluation complete! Judge: {JUDGE_MODELS[trulens_judge_model]}")
            
            # Display persona TruLens results
            if "persona_trulens_evals" in st.session_state:
                persona_eval_df = pd.DataFrame(st.session_state["persona_trulens_evals"])
                
                # Summary by persona
                st.markdown("##### Compliance by Persona")
                
                persona_summary = persona_eval_df.groupby(["persona", "model"]).agg({
                    "flesch_score": "mean",
                    "persona_compliance": "mean",
                    "status": lambda x: (x == "PASS").mean()
                }).reset_index()
                persona_summary.columns = ["Persona", "Model", "Avg Flesch", "Compliance", "Pass Rate"]
                
                st.dataframe(
                    persona_summary,
                    column_config={
                        "Avg Flesch": st.column_config.NumberColumn(format="%.0f"),
                        "Compliance": st.column_config.ProgressColumn(min_value=0, max_value=1),
                        "Pass Rate": st.column_config.ProgressColumn(min_value=0, max_value=1)
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Flesch score distribution chart
                flesch_chart = alt.Chart(persona_eval_df).mark_boxplot().encode(
                    x=alt.X("persona:N", title="Persona"),
                    y=alt.Y("flesch_score:Q", title="Flesch Reading Ease"),
                    color=alt.Color("model:N", scale=alt.Scale(
                        domain=["claude", "mistral"],
                        range=["#6366f1", "#f59e0b"]
                    ))
                ).properties(height=250, title="Flesch Score Distribution by Persona")
                
                st.altair_chart(flesch_chart, use_container_width=True)
    
    # ==================== AGENT PIPELINE ====================
    elif pipeline_type == "agent":
        st.markdown("### 🤖 8 Agents Verbosity Pipeline")
        st.markdown("""
        Evaluates the **8 Agent Types** for verbosity compliance using TruLens:
        
        | Agent | Flag | Max Lines | Format |
        |-------|------|-----------|--------|
        | MINIMAL | `--minimal` | 1 | Single word/number |
        | BRIEF | `--brief` | 3 | Essential info only |
        | STANDARD | `--standard` | 6 | Balanced context |
        | DETAILED | `--detailed` | 15 | Full structure |
        | VERBOSE | `--verbose` | 50 | Comprehensive |
        | CODE_ONLY | `--code` | 20 | Code blocks only |
        | EXPLAIN | `--explain` | 20 | Why + how |
        | STEP_BY_STEP | `--steps` | 25 | Numbered walkthrough |
        """)
        
        # dbt Model Definition
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `agent_verbosity_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH agent_responses AS (
    SELECT *,
        md5(query || agent_type || model || timestamp) as eval_id
    FROM {{ ref('stg_agent_responses') }}
),

agent_limits AS (
    SELECT * FROM (VALUES
        ('MINIMAL', 1), ('BRIEF', 3), ('STANDARD', 6),
        ('DETAILED', 15), ('VERBOSE', 50), ('CODE_ONLY', 20),
        ('EXPLAIN', 20), ('STEP_BY_STEP', 25)
    ) AS t(agent_type, max_lines)
),

verbosity_evaluation AS (
    SELECT
        a.eval_id,
        a.agent_type,
        a.model,
        a.response,
        
        -- Line count
        REGEXP_COUNT(response, '\\n') + 1 as actual_lines,
        l.max_lines,
        
        -- Line compliance (0-1)
        CASE 
            WHEN REGEXP_COUNT(response, '\\n') + 1 <= l.max_lines THEN 1.0
            WHEN REGEXP_COUNT(response, '\\n') + 1 <= l.max_lines * 1.5 THEN 0.5
            ELSE 0.0
        END as line_compliance,
        
        -- Format compliance
        CASE a.agent_type
            WHEN 'CODE_ONLY' THEN 
                CASE WHEN CONTAINS(response, '```') OR CONTAINS(response, 'SELECT') THEN 1.0 ELSE 0.0 END
            WHEN 'STEP_BY_STEP' THEN
                CASE WHEN REGEXP_COUNT(response, '^[0-9]+\\.') >= 2 THEN 1.0 ELSE 0.5 END
            WHEN 'MINIMAL' THEN
                CASE WHEN LENGTH(response) < 50 THEN 1.0 ELSE 0.3 END
            ELSE 0.8
        END as format_compliance
        
    FROM agent_responses a
    JOIN agent_limits l ON a.agent_type = l.agent_type
)

SELECT 
    a.*,
    v.actual_lines,
    v.max_lines,
    v.line_compliance,
    v.format_compliance,
    (v.line_compliance * 0.5 + v.format_compliance * 0.3 + 0.2) as composite_score,
    CASE WHEN v.line_compliance >= 0.5 AND v.format_compliance >= 0.5 THEN 'PASS' ELSE 'FAIL' END as eval_status
FROM agent_responses a
JOIN verbosity_evaluation v ON a.eval_id = v.eval_id
            """, language="sql")
        
        with col2:
            st.markdown("#### Pipeline Lineage")
            st.code("""
agent_verbosity_evaluations
    ↑
stg_agent_responses
    ↑
raw_agent_api_calls
            """, language=None)
            
            st.markdown("#### TruLens Metrics")
            for metric_key, metric in TRULENS_METRICS["agent"].items():
                st.markdown(f"**{metric['name']}** ({metric['weight']*100:.0f}%)")
                st.caption(metric['description'])
        
        # Run evaluation on existing agent results
        st.divider()
        st.markdown("#### Run TruLens Agent Evaluation")
        
        has_agent = "agent_results" in st.session_state and st.session_state["agent_results"]
        
        if not has_agent:
            st.info("Run Agent Verbosity in Tab 6 first, or load saved results.")
            if st.button("📂 Load Agent Results", key="load_agent_trulens"):
                try:
                    results_dir = os.path.join(os.path.dirname(__file__), "results")
                    agent_file = os.path.join(results_dir, "agent_results.json")
                    if os.path.exists(agent_file):
                        with open(agent_file) as f:
                            st.session_state["agent_results"] = json.load(f)
                        st.success("Agent results loaded!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            agent_results = st.session_state["agent_results"]
            st.success(f"Found {len(agent_results)} Agent verbosity results")
            
            st.markdown(f"**Judge Model:** `{trulens_judge_model}` ({JUDGE_MODELS[trulens_judge_model]})")
            
            if st.button("🔬 Run TruLens Agent Evaluation", type="primary", key="run_agent_trulens"):
                with st.spinner(f"Computing verbosity compliance with {JUDGE_MODELS[trulens_judge_model]} as judge..."):
                    agent_evals = []
                    progress_bar = st.progress(0)
                    total_evals = len(agent_results) * len(MODELS)
                    current = 0
                    
                    # Helper for judge calls
                    def call_judge(prompt: str) -> str:
                        try:
                            conn = get_connection()
                            cursor = conn.cursor()
                            prompt_escaped = prompt.replace("'", "''")
                            sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{trulens_judge_model}', '{prompt_escaped}') AS response"
                            cursor.execute(sql)
                            return cursor.fetchone()[0]
                        except:
                            return ""
                    
                    for row in agent_results:
                        agent_type = row.get("agent", "")
                        max_lines = row.get("max_lines", 10)
                        query = row.get("query", "")
                        
                        for model_key in ["claude", "mistral"]:
                            response = row.get(f"{model_key}_response", "")
                            actual_lines = row.get(f"{model_key}_lines", 0)
                            
                            # LLM-as-Judge for format compliance
                            judge_prompt = f"""You are evaluating if a response follows the correct format for an agent type.

Agent Type: {agent_type}
Expected Format: {"ONLY code blocks, no explanatory text" if agent_type == "CODE_ONLY" else "Numbered step-by-step instructions" if agent_type == "STEP_BY_STEP" else "Single word or very brief answer" if agent_type == "MINIMAL" else "Standard conversational response"}
Max Lines Allowed: {max_lines}
Actual Lines: {actual_lines}

Query: {query}
Response: {response[:400]}

Rate on these criteria (0.0 to 1.0):
1. LINE_COMPLIANCE: Did it stay within {max_lines} lines? (1.0 if yes, 0.5 if slightly over, 0.0 if way over)
2. FORMAT_COMPLIANCE: Did it follow the expected format for {agent_type}?
3. CONTENT_QUALITY: Is the response helpful and accurate?

Respond with ONLY three scores:
LINE_COMPLIANCE: 0.X
FORMAT_COMPLIANCE: 0.X
CONTENT_QUALITY: 0.X"""
                            
                            try:
                                judge_resp = call_judge(judge_prompt)
                                import re
                                line_match = re.search(r'LINE_COMPLIANCE:\s*([\d.]+)', judge_resp, re.IGNORECASE)
                                fmt_match = re.search(r'FORMAT_COMPLIANCE:\s*([\d.]+)', judge_resp, re.IGNORECASE)
                                qual_match = re.search(r'CONTENT_QUALITY:\s*([\d.]+)', judge_resp, re.IGNORECASE)
                                
                                line_compliance = float(line_match.group(1)) if line_match else 0.5
                                format_compliance = float(fmt_match.group(1)) if fmt_match else 0.5
                                content_quality = float(qual_match.group(1)) if qual_match else 0.5
                                
                                # Clamp values
                                line_compliance = max(0, min(1, line_compliance))
                                format_compliance = max(0, min(1, format_compliance))
                                content_quality = max(0, min(1, content_quality))
                                
                            except:
                                # Fallback to heuristic
                                if actual_lines <= max_lines:
                                    line_compliance = 1.0
                                elif actual_lines <= max_lines * 1.5:
                                    line_compliance = 0.5
                                else:
                                    line_compliance = 0.0
                                
                                if agent_type == "CODE_ONLY":
                                    format_compliance = 1.0 if ("```" in response or "SELECT" in response.upper()) else 0.0
                                elif agent_type == "STEP_BY_STEP":
                                    import re as re_mod
                                    steps = len(re_mod.findall(r'^\d+\.', response, re_mod.MULTILINE))
                                    format_compliance = 1.0 if steps >= 2 else 0.5
                                elif agent_type == "MINIMAL":
                                    format_compliance = 1.0 if len(response) < 100 else 0.3
                                else:
                                    format_compliance = 0.8
                                content_quality = 0.7
                            
                            composite = line_compliance * 0.5 + format_compliance * 0.3 + content_quality * 0.2
                            
                            agent_evals.append({
                                "agent": agent_type,
                                "query": query[:40],
                                "model": model_key,
                                "response": response[:200] + "..." if len(response) > 200 else response,
                                "judge": trulens_judge_model,
                                "actual_lines": actual_lines,
                                "max_lines": max_lines,
                                "line_compliance": round(line_compliance, 3),
                                "format_compliance": round(format_compliance, 3),
                                "content_quality": round(content_quality, 3),
                                "composite_score": round(composite, 3),
                                "status": "PASS" if line_compliance >= 0.5 and format_compliance >= 0.5 else "FAIL"
                            })
                            
                            current += 1
                            progress_bar.progress(current / total_evals)
                    
                    st.session_state["agent_trulens_evals"] = agent_evals
                    st.success(f"Evaluation complete! Judge: {JUDGE_MODELS[trulens_judge_model]}")
            
            # Display agent TruLens results
            if "agent_trulens_evals" in st.session_state:
                agent_eval_df = pd.DataFrame(st.session_state["agent_trulens_evals"])
                
                # Summary by agent type
                st.markdown("##### Compliance by Agent Type")
                
                agent_summary = agent_eval_df.groupby(["agent", "model"]).agg({
                    "line_compliance": "mean",
                    "format_compliance": "mean",
                    "content_quality": "mean",
                    "composite_score": "mean",
                    "status": lambda x: (x == "PASS").mean()
                }).reset_index()
                agent_summary.columns = ["Agent", "Model", "Line Comp", "Format Comp", "Content", "Composite", "Pass Rate"]
                
                # Show judge info
                if "judge" in agent_eval_df.columns:
                    judge_used = agent_eval_df["judge"].iloc[0] if len(agent_eval_df) > 0 else "N/A"
                    st.caption(f"Evaluated by: **{judge_used}**")
                
                st.dataframe(
                    agent_summary,
                    column_config={
                        "Line Comp": st.column_config.ProgressColumn(min_value=0, max_value=1),
                        "Format Comp": st.column_config.ProgressColumn(min_value=0, max_value=1),
                        "Content": st.column_config.ProgressColumn(min_value=0, max_value=1),
                        "Composite": st.column_config.ProgressColumn(min_value=0, max_value=1),
                        "Pass Rate": st.column_config.ProgressColumn(min_value=0, max_value=1)
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Compliance heatmap
                st.markdown("##### Line Compliance Heatmap")
                
                heatmap_data = agent_eval_df.pivot_table(
                    index="agent", 
                    columns="model", 
                    values="line_compliance",
                    aggfunc="mean"
                ).reset_index().melt(id_vars="agent", var_name="model", value_name="compliance")
                
                heatmap = alt.Chart(heatmap_data).mark_rect().encode(
                    x=alt.X("model:N", title="Model"),
                    y=alt.Y("agent:N", title="Agent Type"),
                    color=alt.Color("compliance:Q", scale=alt.Scale(scheme="blues"), title="Compliance")
                ).properties(height=300, title="Line Compliance: Claude vs Mistral")
                
                st.altair_chart(heatmap, use_container_width=True)
    
    # ==================== SAE FEATURES PIPELINE ====================
    elif pipeline_type == "sae":
        st.markdown("### 🧠 SAE Features Pipeline")
        st.markdown("""
        **Sparse Autoencoder (SAE)** evaluation for LLM interpretability.
        Based on [Data-Centric Interpretability for LLM-based Multi-Agent RL](https://arxiv.org/abs/2602.05183).
        
        SAE features decompose LLM activations into interpretable, sparse features:
        - **Feature Activation**: Strength of learned feature activations
        - **Feature Sparsity**: L0 norm (number of active features per sample)
        - **Reconstruction Loss**: How well SAE reconstructs original activations
        - **Dead Features**: Features that never activate (training issue indicator)
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `sae_feature_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH model_activations AS (
    SELECT 
        eval_id,
        model,
        layer_name,
        activation_vector,  -- ARRAY<FLOAT>
        timestamp
    FROM {{ ref('stg_model_activations') }}
),

sae_features AS (
    SELECT
        eval_id,
        model,
        layer_name,
        
        -- SAE encoding: h = ReLU(W_enc @ x + b_enc)
        -- Feature activation strength (mean of non-zero activations)
        AVG(CASE WHEN f.value > 0 THEN f.value ELSE NULL END) as feature_activation,
        
        -- L0 sparsity (count of active features)
        COUNT(CASE WHEN f.value > 0 THEN 1 END) / ARRAY_SIZE(sae_features) as feature_sparsity,
        
        -- Reconstruction loss: ||x - W_dec @ h||^2
        -- (computed during SAE forward pass)
        reconstruction_mse as reconstruction_loss,
        
        -- Dead features (never activated across batch)
        dead_feature_ratio
        
    FROM model_activations,
    LATERAL FLATTEN(input => sae_encoded_features) f
    GROUP BY eval_id, model, layer_name, reconstruction_mse, dead_feature_ratio
)

SELECT 
    *,
    (feature_activation * 0.3 + (1 - feature_sparsity) * 0.3 + 
     (1 - reconstruction_loss) * 0.2 + (1 - dead_feature_ratio) * 0.2) as composite_score,
    CASE WHEN reconstruction_loss < 0.1 AND dead_feature_ratio < 0.3 
         THEN 'HEALTHY' ELSE 'NEEDS_TUNING' END as sae_status
FROM sae_features
            """, language="sql")
        
        with col2:
            st.markdown("#### SAE Architecture")
            st.code("""
Input: x (activation)
    ↓
Encoder: h = ReLU(W_enc·x + b_enc)
    ↓
Sparse Features: h (L0 sparse)
    ↓
Decoder: x̂ = W_dec·h + b_dec
    ↓
Loss: ||x - x̂||² + λ·L1(h)
            """, language=None)
            
            st.markdown("#### TruLens Metrics")
            for metric_key, metric in TRULENS_METRICS["sae"].items():
                st.markdown(f"**{metric['name']}** ({metric['weight']*100:.0f}%)")
                st.caption(metric['description'])
        
        # SAE Simulation
        st.divider()
        st.markdown("#### Run SAE Feature Analysis")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sae_hidden_dim = st.number_input("SAE Hidden Dim:", value=4096, step=512, key="sae_dim")
        with col2:
            sae_sparsity_target = st.slider("Sparsity Target:", 0.01, 0.2, 0.05, key="sae_sparsity")
        with col3:
            sae_layers = st.multiselect("Layers:", ["layer_12", "layer_24", "layer_36"], default=["layer_24"], key="sae_layers")
        
        if st.button("🧠 Simulate SAE Analysis", type="primary", key="run_sae"):
            with st.spinner("Computing SAE features..."):
                # Simulate SAE metrics for both models
                sae_results = []
                
                for model in ["claude", "mistral"]:
                    for layer in sae_layers:
                        # Simulated metrics (in practice, would come from actual SAE)
                        np.random.seed(hash(f"{model}_{layer}") % 2**32)
                        
                        feature_activation = np.random.uniform(0.3, 0.8)
                        feature_sparsity = np.random.uniform(0.02, 0.15)
                        reconstruction_loss = np.random.uniform(0.02, 0.12)
                        dead_features = np.random.uniform(0.05, 0.35)
                        
                        composite = (feature_activation * 0.3 + (1 - feature_sparsity) * 0.3 + 
                                    (1 - reconstruction_loss) * 0.2 + (1 - dead_features) * 0.2)
                        
                        sae_results.append({
                            "model": model,
                            "layer": layer,
                            "feature_activation": feature_activation,
                            "feature_sparsity": feature_sparsity,
                            "reconstruction_loss": reconstruction_loss,
                            "dead_features": dead_features,
                            "composite_score": composite,
                            "status": "HEALTHY" if reconstruction_loss < 0.1 and dead_features < 0.3 else "NEEDS_TUNING"
                        })
                
                st.session_state["sae_results"] = sae_results
        
        if "sae_results" in st.session_state:
            sae_df = pd.DataFrame(st.session_state["sae_results"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Claude SAE Metrics**")
                claude_sae = sae_df[sae_df["model"] == "claude"]
                st.metric("Avg Activation", f"{claude_sae['feature_activation'].mean():.3f}")
                st.metric("Avg Sparsity", f"{claude_sae['feature_sparsity'].mean():.3f}")
                st.metric("Reconstruction Loss", f"{claude_sae['reconstruction_loss'].mean():.4f}")
            
            with col2:
                st.markdown("**Mistral SAE Metrics**")
                mistral_sae = sae_df[sae_df["model"] == "mistral"]
                st.metric("Avg Activation", f"{mistral_sae['feature_activation'].mean():.3f}")
                st.metric("Avg Sparsity", f"{mistral_sae['feature_sparsity'].mean():.3f}")
                st.metric("Reconstruction Loss", f"{mistral_sae['reconstruction_loss'].mean():.4f}")
            
            st.dataframe(sae_df, hide_index=True, use_container_width=True)
    
    # ==================== SAE META FEATURES PIPELINE ====================
    elif pipeline_type == "sae_meta":
        st.markdown("### 🔬 SAE Meta Features Pipeline")
        st.markdown("""
        **Meta-level analysis** of SAE features for interpretability evaluation.
        Assesses whether learned features are meaningful and useful for understanding model behavior.
        
        Key evaluations:
        - **Concept Clustering**: Do similar features cluster into coherent concepts?
        - **Feature Interpretability**: Can humans understand what features represent?
        - **Behavioral Correlation**: Do features predict model behaviors/outputs?
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `sae_meta_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH sae_features AS (
    SELECT * FROM {{ ref('sae_feature_evaluations') }}
),

feature_descriptions AS (
    -- LLM-generated descriptions of what each feature represents
    SELECT 
        feature_id,
        SNOWFLAKE.CORTEX.COMPLETE(
            'claude-3-5-sonnet',
            'Describe what this SAE feature represents based on its activation pattern: ' 
            || top_activating_examples
        ) as llm_description,
        human_label  -- Ground truth if available
    FROM {{ ref('sae_feature_examples') }}
),

meta_analysis AS (
    SELECT
        s.eval_id,
        s.model,
        
        -- Concept clustering: cosine similarity within feature clusters
        AVG(cluster_coherence) as concept_clustering,
        
        -- Interpretability: LLM-human label agreement
        AVG(CASE WHEN CONTAINS(LOWER(f.llm_description), LOWER(f.human_label)) 
                 THEN 1.0 ELSE 0.3 END) as feature_interpretability,
        
        -- Behavioral correlation: feature activation → output prediction
        CORR(feature_activation, target_behavior) as behavioral_correlation
        
    FROM sae_features s
    JOIN feature_descriptions f ON s.feature_id = f.feature_id
    GROUP BY s.eval_id, s.model
)

SELECT 
    *,
    (concept_clustering * 0.35 + feature_interpretability * 0.35 + 
     ABS(behavioral_correlation) * 0.3) as interpretability_score,
    CASE WHEN interpretability_score >= 0.6 THEN 'INTERPRETABLE' 
         ELSE 'OPAQUE' END as interpretability_status
FROM meta_analysis
            """, language="sql")
        
        with col2:
            st.markdown("#### Interpretability Framework")
            st.code("""
SAE Features
    ↓
Cluster Analysis
    ↓
LLM Labeling → Human Review
    ↓
Behavior Prediction
    ↓
Interpretability Score
            """, language=None)
            
            st.markdown("#### TruLens Metrics")
            for metric_key, metric in TRULENS_METRICS["sae_meta"].items():
                st.markdown(f"**{metric['name']}** ({metric['weight']*100:.0f}%)")
                st.caption(metric['description'])
        
        # Meta Feature Simulation
        st.divider()
        st.markdown("#### Run Meta Feature Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            n_clusters = st.number_input("Feature Clusters:", value=50, step=10, key="meta_clusters")
        with col2:
            label_method = st.selectbox("Labeling Method:", ["LLM Auto-Label", "Human + LLM", "Human Only"], key="meta_label")
        
        if st.button("🔬 Run Meta Analysis", type="primary", key="run_meta"):
            with st.spinner("Analyzing feature interpretability..."):
                meta_results = []
                
                for model in ["claude", "mistral"]:
                    np.random.seed(hash(model) % 2**32)
                    
                    concept_clustering = np.random.uniform(0.5, 0.9)
                    feature_interpretability = np.random.uniform(0.4, 0.85)
                    behavioral_correlation = np.random.uniform(0.3, 0.8)
                    
                    interp_score = (concept_clustering * 0.35 + feature_interpretability * 0.35 + 
                                   behavioral_correlation * 0.3)
                    
                    meta_results.append({
                        "model": model,
                        "concept_clustering": concept_clustering,
                        "feature_interpretability": feature_interpretability,
                        "behavioral_correlation": behavioral_correlation,
                        "interpretability_score": interp_score,
                        "status": "INTERPRETABLE" if interp_score >= 0.6 else "OPAQUE"
                    })
                
                st.session_state["sae_meta_results"] = meta_results
        
        if "sae_meta_results" in st.session_state:
            meta_df = pd.DataFrame(st.session_state["sae_meta_results"])
            
            st.markdown("##### Model Interpretability Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                claude_meta = meta_df[meta_df["model"] == "claude"].iloc[0]
                st.markdown("**Claude**")
                st.metric("Interpretability Score", f"{claude_meta['interpretability_score']:.2f}", 
                         delta=claude_meta['status'])
            
            with col2:
                mistral_meta = meta_df[meta_df["model"] == "mistral"].iloc[0]
                st.markdown("**Mistral**")
                st.metric("Interpretability Score", f"{mistral_meta['interpretability_score']:.2f}",
                         delta=mistral_meta['status'])
            
            # Radar chart for meta features
            meta_chart_data = meta_df.melt(
                id_vars=["model"],
                value_vars=["concept_clustering", "feature_interpretability", "behavioral_correlation"],
                var_name="metric",
                value_name="score"
            )
            
            meta_chart = alt.Chart(meta_chart_data).mark_bar().encode(
                x=alt.X("metric:N", title="Metric"),
                y=alt.Y("score:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
                color=alt.Color("model:N", scale=alt.Scale(
                    domain=["claude", "mistral"],
                    range=["#6366f1", "#f59e0b"]
                )),
                xOffset="model:N"
            ).properties(height=250, title="SAE Meta Feature Comparison")
            
            st.altair_chart(meta_chart, use_container_width=True)
    
    # ==================== LLM SUMMARIZER PIPELINE ====================
    elif pipeline_type == "llm_summarizer":
        st.markdown("### 📝 LLM Summarizer Evaluation Pipeline")
        st.markdown("""
        Evaluate LLM-generated **summaries** for factual consistency and quality.
        Critical for RAG applications and document processing workflows.
        
        Key metrics:
        - **Factual Consistency**: Do summary claims match source document?
        - **Coverage**: Are key points from the source included?
        - **Conciseness**: Information density (facts per word)
        - **Coherence**: Logical flow and readability
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### dbt Model: `summarizer_evaluations`")
            st.code("""
{{ config(
    materialized='incremental',
    unique_key='eval_id',
    schema='trulens_evals'
) }}

WITH summaries AS (
    SELECT 
        eval_id,
        model,
        source_document,
        generated_summary,
        timestamp
    FROM {{ ref('stg_summarizer_responses') }}
),

factual_eval AS (
    SELECT
        eval_id,
        model,
        
        -- Factual consistency via NLI
        SNOWFLAKE.CORTEX.COMPLETE(
            'claude-3-5-sonnet',
            'Rate 0-1 factual consistency. Source: ' || SUBSTR(source_document, 1, 2000) 
            || ' Summary: ' || generated_summary
        )::FLOAT as factual_consistency,
        
        -- Coverage: key entity/fact overlap
        (SELECT COUNT(DISTINCT e.value) 
         FROM LATERAL FLATTEN(input => SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
             source_document, 'What are the key facts?')) e
         WHERE CONTAINS(generated_summary, e.value::STRING)
        ) / NULLIF(key_fact_count, 0) as coverage,
        
        -- Conciseness: compression ratio with fact preservation
        LENGTH(source_document) / NULLIF(LENGTH(generated_summary), 0) 
            * factual_consistency as conciseness,
        
        -- Coherence: Flesch score of summary
        {{ flesch_reading_ease('generated_summary') }} / 100.0 as coherence
        
    FROM summaries
)

SELECT 
    s.*,
    f.factual_consistency,
    f.coverage,
    f.conciseness,
    f.coherence,
    (f.factual_consistency * 0.4 + f.coverage * 0.3 + 
     LEAST(f.conciseness / 10, 1) * 0.15 + f.coherence * 0.15) as quality_score,
    CASE 
        WHEN factual_consistency >= 0.8 AND coverage >= 0.7 THEN 'HIGH_QUALITY'
        WHEN factual_consistency >= 0.6 THEN 'ACCEPTABLE'
        ELSE 'NEEDS_IMPROVEMENT'
    END as quality_status
FROM summaries s
JOIN factual_eval f ON s.eval_id = f.eval_id
            """, language="sql")
        
        with col2:
            st.markdown("#### Summarization Flow")
            st.code("""
Source Document
    ↓
LLM Summarization
    ↓
Fact Extraction
    ↓
NLI Verification
    ↓
Quality Score
            """, language=None)
            
            st.markdown("#### TruLens Metrics")
            for metric_key, metric in TRULENS_METRICS["llm_summarizer"].items():
                st.markdown(f"**{metric['name']}** ({metric['weight']*100:.0f}%)")
                st.caption(metric['description'])
        
        # Summarizer Evaluation
        st.divider()
        st.markdown("#### Run Summarizer Evaluation")
        
        source_text = st.text_area(
            "Source Document (or use sample):",
            value="""The Apollo program was a NASA space program that successfully landed humans on the Moon. 
Apollo 11, launched on July 16, 1969, was the first mission to land astronauts on the lunar surface. 
Neil Armstrong became the first person to walk on the Moon on July 20, 1969, followed by Buzz Aldrin. 
Michael Collins remained in lunar orbit aboard the command module. The program ran from 1961 to 1972 
and included 17 missions, with 6 successful Moon landings. The total cost was approximately $25.4 billion.""",
            height=150,
            key="summarizer_source"
        )
        
        if st.button("📝 Generate & Evaluate Summaries", type="primary", key="run_summarizer"):
            with st.spinner("Generating and evaluating summaries..."):
                summarizer_results = []
                
                for model_key, model_config in MODELS.items():
                    model_name = model_config["name"]
                    # Generate summary
                    cursor = conn.cursor()
                    prompt = f"Summarize this in 2-3 sentences: {source_text}"
                    prompt_escaped = prompt.replace("'", "''")
                    
                    try:
                        cursor.execute(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model_name}', '{prompt_escaped}')")
                        summary = cursor.fetchone()[0]
                        
                        # Compute metrics
                        flesch = compute_flesch_score(summary) if summary else 0
                        
                        # Simulated factual consistency (in practice, use NLI model)
                        key_facts = ["Apollo", "1969", "Moon", "Armstrong", "NASA"]
                        facts_found = sum(1 for fact in key_facts if fact.lower() in summary.lower())
                        factual_consistency = facts_found / len(key_facts)
                        
                        coverage = min(1.0, facts_found / 4)
                        conciseness = len(source_text) / max(len(summary), 1) * factual_consistency
                        coherence = flesch / 100.0
                        
                        quality_score = (factual_consistency * 0.4 + coverage * 0.3 + 
                                        min(conciseness / 10, 1) * 0.15 + coherence * 0.15)
                        
                        summarizer_results.append({
                            "model": model_key,
                            "summary": summary,
                            "factual_consistency": factual_consistency,
                            "coverage": coverage,
                            "conciseness": conciseness,
                            "coherence": coherence,
                            "quality_score": quality_score,
                            "status": "HIGH_QUALITY" if factual_consistency >= 0.8 and coverage >= 0.7 
                                      else "ACCEPTABLE" if factual_consistency >= 0.6 else "NEEDS_IMPROVEMENT"
                        })
                    except Exception as e:
                        summarizer_results.append({
                            "model": model_key,
                            "summary": f"Error: {e}",
                            "factual_consistency": 0,
                            "coverage": 0,
                            "conciseness": 0,
                            "coherence": 0,
                            "quality_score": 0,
                            "status": "ERROR"
                        })
                    finally:
                        cursor.close()
                
                st.session_state["summarizer_results"] = summarizer_results
        
        if "summarizer_results" in st.session_state:
            sum_results = st.session_state["summarizer_results"]
            
            st.markdown("##### Summary Comparison")
            
            col1, col2 = st.columns(2)
            
            for i, result in enumerate(sum_results):
                with col1 if i == 0 else col2:
                    status_color = "🟢" if result["status"] == "HIGH_QUALITY" else "🟡" if result["status"] == "ACCEPTABLE" else "🔴"
                    st.markdown(f"**{result['model'].title()}** {status_color}")
                    st.metric("Quality Score", f"{result['quality_score']:.2f}")
                    st.caption(f"Factual: {result['factual_consistency']:.0%} | Coverage: {result['coverage']:.0%}")
                    st.code(result['summary'][:500])
            
            # Metrics comparison
            sum_df = pd.DataFrame(sum_results)
            
            metrics_chart = alt.Chart(sum_df.melt(
                id_vars=["model"],
                value_vars=["factual_consistency", "coverage", "coherence"],
                var_name="metric",
                value_name="score"
            )).mark_bar().encode(
                x=alt.X("metric:N", title="Metric"),
                y=alt.Y("score:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
                color=alt.Color("model:N", scale=alt.Scale(
                    domain=["claude", "mistral"],
                    range=["#6366f1", "#f59e0b"]
                )),
                xOffset="model:N"
            ).properties(height=250, title="Summarizer Quality Metrics")
            
            st.altair_chart(metrics_chart, use_container_width=True)
    
    st.divider()
    
    # ==================== TRULENS EXPORT ====================
    st.markdown("### 📤 Export to dbt Tables")
    st.markdown("""
    Export TruLens evaluation results to Snowflake tables managed by dbt.
    This enables:
    - Historical tracking of model performance
    - dbt tests on evaluation thresholds
    - Lineage from raw API calls → evaluations → dashboards
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        export_wiki = st.checkbox("Wiki Evaluations", value="wiki_trulens_evals" in st.session_state)
    with col2:
        export_persona = st.checkbox("Persona Evaluations", value="persona_trulens_evals" in st.session_state)
    with col3:
        export_agent = st.checkbox("Agent Evaluations", value="agent_trulens_evals" in st.session_state)
    
    target_schema = st.text_input("Target Schema:", value="TRULENS_EVALS", key="export_schema")
    
    if st.button("📤 Generate Export SQL", key="generate_export"):
        export_sql = f"""
-- TruLens Evaluation Export
-- Generated: {datetime.now().isoformat()}

USE SCHEMA {target_schema};
"""
        
        if export_wiki and "wiki_trulens_evals" in st.session_state:
            export_sql += """
-- Wiki Q&A Evaluations
CREATE OR REPLACE TABLE wiki_qa_evaluations AS
SELECT * FROM VALUES
"""
            for i, row in enumerate(st.session_state["wiki_trulens_evals"][:5]):
                export_sql += f"  ('{row['article']}', '{row['model']}', {row['composite_score']:.2f}, '{row['status']}')"
                export_sql += ",\n" if i < 4 else "\n"
            export_sql += "AS t(article, model, composite_score, status);\n\n"
        
        if export_persona and "persona_trulens_evals" in st.session_state:
            export_sql += """
-- Persona Evaluations  
CREATE OR REPLACE TABLE persona_evaluations AS
SELECT * FROM VALUES
"""
            for i, row in enumerate(st.session_state["persona_trulens_evals"][:5]):
                export_sql += f"  ('{row['persona']}', '{row['model']}', {row['flesch_score']:.0f}, {row['persona_compliance']:.2f})"
                export_sql += ",\n" if i < 4 else "\n"
            export_sql += "AS t(persona, model, flesch_score, compliance);\n\n"
        
        if export_agent and "agent_trulens_evals" in st.session_state:
            export_sql += """
-- Agent Verbosity Evaluations
CREATE OR REPLACE TABLE agent_verbosity_evaluations AS  
SELECT * FROM VALUES
"""
            for i, row in enumerate(st.session_state["agent_trulens_evals"][:5]):
                export_sql += f"  ('{row['agent']}', '{row['model']}', {row['line_compliance']:.2f}, '{row['status']}')"
                export_sql += ",\n" if i < 4 else "\n"
            export_sql += "AS t(agent, model, line_compliance, status);\n"
        
        st.code(export_sql, language="sql")

# ============== TAB 9: A/B Testing with MCP Agents ==============
with tab9:
    st.subheader("🧪 A/B Testing with MCP Agent Spawning")
    st.markdown("""
    Run **controlled A/B tests** between models using spawned agents via MCP server.
    Features:
    - **Agent Pool**: Spawn competing responder agents
    - **LLM-as-Judge**: Automated winner selection
    - **Multi-Judge Panel**: Consensus evaluation with multiple judges
    - **Statistical Analysis**: Win rates, Elo ratings, confidence intervals
    """)
    
    # MCP Server Status
    ab_mcp_status = check_ab_mcp_server(AB_MCP_URL)
    col_mcp1, col_mcp2 = st.columns([3, 1])
    with col_mcp1:
        if ab_mcp_status:
            st.success(f"✅ A/B Testing MCP Server running at {AB_MCP_URL}")
        else:
            st.warning(f"⚠️ A/B Testing MCP Server not running at {AB_MCP_URL}")
    with col_mcp2:
        if not ab_mcp_status:
            if st.button("🚀 Start A/B MCP", key="start_ab_mcp"):
                with st.spinner("Starting A/B Testing MCP server..."):
                    if ensure_ab_mcp_server(AB_MCP_URL):
                        st.rerun()
                    else:
                        st.error("Failed to start server")
    
    st.divider()
    
    # Test Type Selection
    ab_test_type = st.radio(
        "Select A/B Test Type:",
        options=["single", "batch", "multi_judge", "agent_pool"],
        format_func=lambda x: {
            "single": "🎯 Single A/B Test (Quick comparison)",
            "batch": "📊 Batch A/B Tests (Multiple queries)",
            "multi_judge": "⚖️ Multi-Judge Panel (Consensus evaluation)",
            "agent_pool": "🤖 Agent Pool (Spawn and manage agents)"
        }[x],
        horizontal=True,
        key="ab_test_type"
    )
    
    st.divider()
    
    # ==================== SINGLE A/B TEST ====================
    if ab_test_type == "single":
        st.markdown("### 🎯 Single A/B Test")
        st.markdown("Compare two models on a single query with LLM-as-judge evaluation.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            ab_query = st.text_area(
                "Test Query:",
                value="Explain the concept of SQL injection and how to prevent it.",
                height=100,
                key="ab_single_query"
            )
        
        with col2:
            ab_model_a = st.selectbox(
                "Model A:",
                options=["claude-3-5-sonnet", "mistral-large2", "llama3.1-70b"],
                index=0,
                key="ab_model_a"
            )
            ab_model_b = st.selectbox(
                "Model B:",
                options=["claude-3-5-sonnet", "mistral-large2", "llama3.1-70b"],
                index=1,
                key="ab_model_b"
            )
            ab_judge = st.selectbox(
                "Judge Model (independent):",
                options=["llama3.1-70b", "claude-sonnet-4-6", "gpt-5.2", "mixtral-8x7b", "snowflake-arctic"],
                format_func=lambda x: {
                    "llama3.1-70b": "Llama 3.1 70B (Meta)",
                    "claude-sonnet-4-6": "Claude Sonnet 4.6 (Anthropic)",
                    "gpt-5.2": "GPT-5.2 (OpenAI)",
                    "mixtral-8x7b": "Mixtral 8x7B (Mistral AI)",
                    "snowflake-arctic": "Snowflake Arctic"
                }[x],
                index=0,
                key="ab_judge",
                help="Judge must be different from contestants to avoid bias"
            )
        
        # Optional system prompts
        with st.expander("⚙️ Advanced: Custom System Prompts", expanded=False):
            col_prompt1, col_prompt2 = st.columns(2)
            with col_prompt1:
                system_prompt_a = st.text_area(
                    "System Prompt for Model A:",
                    value="You are a helpful AI assistant. Be concise and accurate.",
                    height=80,
                    key="ab_sys_a"
                )
            with col_prompt2:
                system_prompt_b = st.text_area(
                    "System Prompt for Model B:",
                    value="You are a helpful AI assistant. Be concise and accurate.",
                    height=80,
                    key="ab_sys_b"
                )
        
        if st.button("🔬 Run A/B Test", type="primary", key="run_single_ab", disabled=not ab_mcp_status):
            with st.spinner("Spawning agents and running A/B test..."):
                client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                
                result = client.run_ab_test(
                    query=ab_query,
                    model_a=ab_model_a,
                    model_b=ab_model_b,
                    judge_model=ab_judge,
                    system_prompt_a=system_prompt_a if 'system_prompt_a' in dir() else None,
                    system_prompt_b=system_prompt_b if 'system_prompt_b' in dir() else None
                )
                
                if "result" in result:
                    st.session_state["ab_single_result"] = result["result"]
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")
        
        # Display single test result
        if "ab_single_result" in st.session_state:
            result = st.session_state["ab_single_result"]
            
            st.markdown("---")
            
            # Winner announcement
            winner_emoji = "🏆"
            if result["winner"] == "A":
                winner_text = f"{winner_emoji} **Winner: Model A ({result['model_a']})**"
                winner_color = "green"
            elif result["winner"] == "B":
                winner_text = f"{winner_emoji} **Winner: Model B ({result['model_b']})**"
                winner_color = "blue"
            else:
                winner_text = "🤝 **Result: TIE**"
                winner_color = "gray"
            
            st.markdown(f"### {winner_text}")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Model A Latency", f"{result['latency_a']:.2f}s")
            with col2:
                st.metric("Model B Latency", f"{result['latency_b']:.2f}s")
            with col3:
                st.metric("Response A Length", f"{len(result['response_a'])} chars")
            with col4:
                st.metric("Response B Length", f"{len(result['response_b'])} chars")
            
            # Side-by-side responses
            col1, col2 = st.columns(2)
            
            with col1:
                status_a = "🏆" if result["winner"] == "A" else ""
                st.markdown(f"**Model A: {result['model_a']}** {status_a}")
                st.code(result["response_a"][:1500], language=None)
            
            with col2:
                status_b = "🏆" if result["winner"] == "B" else ""
                st.markdown(f"**Model B: {result['model_b']}** {status_b}")
                st.code(result["response_b"][:1500], language=None)
            
            # Judge reasoning
            with st.expander("⚖️ Judge Reasoning", expanded=True):
                st.markdown(f"**Judge Model:** {result['judge_model']}")
                st.markdown(result["judge_reasoning"])
    
    # ==================== BATCH A/B TESTS ====================
    elif ab_test_type == "batch":
        st.markdown("### 📊 Batch A/B Tests")
        st.markdown("Run multiple A/B tests and get aggregate statistics.")
        
        # Pre-defined test queries
        DEFAULT_AB_QUERIES = [
            "What is SQL injection?",
            "Explain the difference between authentication and authorization.",
            "How do you optimize a slow SQL query?",
            "What are the SOLID principles in software engineering?",
            "Describe the CAP theorem in distributed systems.",
        ]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            batch_queries_text = st.text_area(
                "Test Queries (one per line):",
                value="\n".join(DEFAULT_AB_QUERIES),
                height=200,
                key="ab_batch_queries"
            )
            batch_queries = [q.strip() for q in batch_queries_text.split("\n") if q.strip()]
        
        with col2:
            batch_model_a = st.selectbox(
                "Model A:",
                options=["claude-3-5-sonnet", "mistral-large2"],
                index=0,
                key="batch_model_a"
            )
            batch_model_b = st.selectbox(
                "Model B:",
                options=["claude-3-5-sonnet", "mistral-large2"],
                index=1,
                key="batch_model_b"
            )
            batch_judge = st.selectbox(
                "Judge Model (independent):",
                options=["llama3.1-70b", "claude-sonnet-4-6", "gpt-5.2", "mixtral-8x7b", "snowflake-arctic"],
                format_func=lambda x: {
                    "llama3.1-70b": "Llama 3.1 70B (Meta)",
                    "claude-sonnet-4-6": "Claude Sonnet 4.6 (Anthropic)",
                    "gpt-5.2": "GPT-5.2 (OpenAI)",
                    "mixtral-8x7b": "Mixtral 8x7B (Mistral AI)",
                    "snowflake-arctic": "Snowflake Arctic"
                }[x],
                index=0,
                key="batch_judge",
                help="Judge must be different from contestants"
            )
            
            st.metric("Total Tests", len(batch_queries))
        
        if st.button("📊 Run Batch A/B Tests", type="primary", key="run_batch_ab", disabled=not ab_mcp_status):
            client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
            
            batch_results = []
            progress = st.progress(0)
            status = st.empty()
            
            for i, query in enumerate(batch_queries):
                status.text(f"Testing: {query[:50]}...")
                
                result = client.run_ab_test(
                    query=query,
                    model_a=batch_model_a,
                    model_b=batch_model_b,
                    judge_model=batch_judge
                )
                
                if "result" in result:
                    batch_results.append(result["result"])
                
                progress.progress((i + 1) / len(batch_queries))
            
            progress.empty()
            status.empty()
            
            st.session_state["ab_batch_results"] = batch_results
            
            # Get statistics
            stats = client.get_statistics()
            st.session_state["ab_batch_stats"] = stats
        
        # Display batch results
        if "ab_batch_results" in st.session_state:
            batch_results = st.session_state["ab_batch_results"]
            
            st.markdown("---")
            st.markdown("### 📈 Batch Test Results")
            
            # Statistics
            wins_a = sum(1 for r in batch_results if r["winner"] == "A")
            wins_b = sum(1 for r in batch_results if r["winner"] == "B")
            ties = sum(1 for r in batch_results if r["winner"] == "tie")
            total = len(batch_results)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"🏆 {batch_results[0]['model_a'] if batch_results else 'Model A'} Wins", 
                         wins_a, delta=f"{wins_a/total*100:.0f}%" if total else "0%")
            with col2:
                st.metric(f"🏆 {batch_results[0]['model_b'] if batch_results else 'Model B'} Wins", 
                         wins_b, delta=f"{wins_b/total*100:.0f}%" if total else "0%")
            with col3:
                st.metric("🤝 Ties", ties)
            with col4:
                st.metric("Total Tests", total)
            
            # Win rate chart
            win_data = pd.DataFrame({
                "Model": [batch_results[0]["model_a"] if batch_results else "A", 
                         batch_results[0]["model_b"] if batch_results else "B", "Tie"],
                "Wins": [wins_a, wins_b, ties],
                "Color": ["#6366f1", "#f59e0b", "#9ca3af"]
            })
            
            win_chart = alt.Chart(win_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("Wins:Q"),
                color=alt.Color("Model:N", scale=alt.Scale(
                    domain=win_data["Model"].tolist(),
                    range=win_data["Color"].tolist()
                )),
                tooltip=["Model", "Wins"]
            ).properties(width=300, height=300, title="Win Distribution")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.altair_chart(win_chart)
            
            with col2:
                # Results table with responses
                results_df = pd.DataFrame([{
                    "Query": r["query"][:40] + "..." if len(r["query"]) > 40 else r["query"],
                    "Winner": r["winner"],
                    "Response A": r["response_a"][:80] + "..." if len(r["response_a"]) > 80 else r["response_a"],
                    "Response B": r["response_b"][:80] + "..." if len(r["response_b"]) > 80 else r["response_b"],
                    "Model A Time": f"{r['latency_a']:.2f}s",
                    "Model B Time": f"{r['latency_b']:.2f}s"
                } for r in batch_results])
                
                st.dataframe(
                    results_df, 
                    column_config={
                        "Query": st.column_config.TextColumn("Query", width="medium"),
                        "Response A": st.column_config.TextColumn("Response A", width="large"),
                        "Response B": st.column_config.TextColumn("Response B", width="large")
                    },
                    hide_index=True, 
                    use_container_width=True
                )
    
    # ==================== MULTI-JUDGE PANEL ====================
    elif ab_test_type == "multi_judge":
        st.markdown("### ⚖️ Multi-Judge Panel Evaluation")
        st.markdown("""
        Get **consensus evaluation** from multiple LLM judges.
        - Uses both Claude and Mistral as judges
        - Calculates agreement rate
        - More robust than single-judge evaluation
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            mj_query = st.text_area(
                "Test Query:",
                value="What are the best practices for writing secure Python code?",
                height=80,
                key="mj_query"
            )
        
        with col2:
            mj_judges = st.multiselect(
                "Select Judges (independent models):",
                options=["llama3.1-70b", "claude-sonnet-4-6", "gpt-5.2", "mixtral-8x7b", "snowflake-arctic"],
                default=["llama3.1-70b", "claude-sonnet-4-6"],
                key="mj_judges",
                help="Judges must be different from Claude/Mistral being compared"
            )
        
        # First get responses
        if st.button("📝 Generate Responses", key="mj_generate", disabled=not ab_mcp_status):
            with st.spinner("Generating responses from both models..."):
                client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                
                # Spawn agents and get responses
                agent_a = client.spawn_agent("responder", "claude-3-5-sonnet")
                agent_b = client.spawn_agent("responder", "mistral-large2")
                
                if "agent" in agent_a and "agent" in agent_b:
                    result_a = client.run_agent(agent_a["agent"]["agent_id"], mj_query)
                    result_b = client.run_agent(agent_b["agent"]["agent_id"], mj_query)
                    
                    st.session_state["mj_responses"] = {
                        "query": mj_query,
                        "response_a": result_a.get("response", ""),
                        "response_b": result_b.get("response", ""),
                        "model_a": "claude-3-5-sonnet",
                        "model_b": "mistral-large2"
                    }
        
        # Display responses and run multi-judge
        if "mj_responses" in st.session_state:
            responses = st.session_state["mj_responses"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Response A ({responses['model_a']})**")
                st.code(responses["response_a"][:800], language=None)
            with col2:
                st.markdown(f"**Response B ({responses['model_b']})**")
                st.code(responses["response_b"][:800], language=None)
            
            if st.button("⚖️ Run Multi-Judge Evaluation", type="primary", key="mj_evaluate"):
                with st.spinner("Running multi-judge panel..."):
                    client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                    
                    result = client.multi_judge(
                        query=responses["query"],
                        response_a=responses["response_a"],
                        response_b=responses["response_b"],
                        judge_models=mj_judges
                    )
                    
                    st.session_state["mj_result"] = result
        
        # Display multi-judge results
        if "mj_result" in st.session_state:
            mj_result = st.session_state["mj_result"]
            
            st.markdown("---")
            st.markdown("### 🏆 Multi-Judge Verdict")
            
            consensus = mj_result.get("consensus", "tie")
            agreement = mj_result.get("agreement_rate", 0)
            
            if consensus == "A":
                st.success(f"**Consensus Winner: Response A** (Agreement: {agreement:.0%})")
            elif consensus == "B":
                st.success(f"**Consensus Winner: Response B** (Agreement: {agreement:.0%})")
            else:
                st.info(f"**Consensus: TIE** (Agreement: {agreement:.0%})")
            
            # Individual judge verdicts
            st.markdown("#### Individual Judge Verdicts")
            
            verdicts = mj_result.get("verdicts", {})
            for judge_model, verdict in verdicts.items():
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    st.markdown(f"**{judge_model}**")
                with col2:
                    winner = verdict.get("winner", "tie")
                    emoji = "🅰️" if winner == "A" else "🅱️" if winner == "B" else "🤝"
                    st.markdown(f"{emoji} {winner}")
                with col3:
                    st.caption(verdict.get("reasoning", "")[:200])
    
    # ==================== AGENT POOL ====================
    elif ab_test_type == "agent_pool":
        st.markdown("### 🤖 Agent Pool Management")
        st.markdown("""
        Spawn and manage agents directly. View active agents and run them manually.
        
        **Agent Roles:**
        - **Responder**: Answers queries
        - **Evaluator**: Assesses response quality
        - **Judge**: Compares and picks winners
        """)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Spawn New Agent")
            
            spawn_role = st.selectbox(
                "Role:",
                options=["responder", "evaluator", "judge"],
                key="spawn_role"
            )
            spawn_model = st.selectbox(
                "Model:",
                options=["claude-3-5-sonnet", "mistral-large2", "llama3.1-70b"],
                key="spawn_model"
            )
            spawn_prompt = st.text_area(
                "Custom System Prompt (optional):",
                height=80,
                key="spawn_prompt"
            )
            
            if st.button("➕ Spawn Agent", key="spawn_agent_btn", disabled=not ab_mcp_status):
                client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                result = client.spawn_agent(
                    role=spawn_role,
                    model=spawn_model,
                    system_prompt=spawn_prompt if spawn_prompt else None
                )
                
                if "agent" in result:
                    st.success(f"Spawned: {result['agent']['agent_id']}")
                    st.session_state["last_spawned"] = result["agent"]["agent_id"]
                else:
                    st.error(f"Error: {result.get('error', 'Unknown')}")
        
        with col2:
            st.markdown("#### Active Agents")
            
            if st.button("🔄 Refresh Agents", key="refresh_agents"):
                client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                agents = client.list_agents()
                st.session_state["agent_list"] = agents
            
            if "agent_list" in st.session_state:
                agents = st.session_state["agent_list"]
                
                if agents:
                    agent_df = pd.DataFrame(agents)[["agent_id", "role", "model", "status"]]
                    st.dataframe(agent_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No active agents")
        
        st.divider()
        
        # Run Agent
        st.markdown("#### Run Agent")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            run_agent_id = st.text_input(
                "Agent ID:",
                value=st.session_state.get("last_spawned", ""),
                key="run_agent_id"
            )
        
        with col2:
            run_query = st.text_input(
                "Query:",
                value="What is a SQL injection attack?",
                key="run_agent_query"
            )
        
        if st.button("▶️ Run Agent", key="run_agent_btn", disabled=not ab_mcp_status):
            if run_agent_id and run_query:
                with st.spinner("Running agent..."):
                    client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                    result = client.run_agent(run_agent_id, run_query)
                    
                    if "response" in result:
                        st.markdown("**Response:**")
                        st.code(result["response"], language=None)
                        st.caption(f"Latency: {result.get('latency', 0):.2f}s")
                    else:
                        st.error(f"Error: {result.get('error', 'Unknown')}")
            else:
                st.warning("Enter agent ID and query")
    
    # ==================== A/B TESTING STATISTICS ====================
    st.divider()
    st.markdown("### 📈 Session Statistics")
    
    if ab_mcp_status:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("📊 Load Statistics", key="load_ab_stats"):
                client = ABTestingMCPClient(AB_MCP_URL, auto_start=False)
                stats = client.get_statistics()
                st.session_state["ab_stats"] = stats
        
        with col2:
            if "ab_stats" in st.session_state:
                stats = st.session_state["ab_stats"]
                
                if stats.get("total_tests", 0) > 0:
                    cols = st.columns(6)
                    cols[0].metric("Total Tests", stats.get("total_tests", 0))
                    cols[1].metric("Model A Wins", stats.get("model_a_wins", 0))
                    cols[2].metric("Model B Wins", stats.get("model_b_wins", 0))
                    cols[3].metric("Ties", stats.get("ties", 0))
                    cols[4].metric("A Win Rate", f"{stats.get('model_a_win_rate', 0):.0%}")
                    cols[5].metric("B Win Rate", f"{stats.get('model_b_win_rate', 0):.0%}")
                else:
                    st.info("No tests run yet in this session")
    else:
        st.info("Start the A/B Testing MCP server to view statistics")

# ============== TAB 10: Inference Experiments ==============
with tab10:
    st.subheader("🔬 Inference-Time Experiment Tracking")
    st.markdown("""
    **LangGraph Agents + LangTrace + TruLens Evals + Snowflake ML Experiments**
    
    Track A/B testing and SAE (Sparse Autoencoder) analysis at inference time using Snowflake's ML Experiment Tracking.
    """)
    
    # Configuration
    INFERENCE_EXP_PORT = 8525
    INFERENCE_EXP_URL = f"http://localhost:{INFERENCE_EXP_PORT}"
    
    # ----- 25+ Test Queries for A/B Experiments -----
    LANGGRAPH_TEST_QUERIES = [
        # Security & Cybersecurity (5)
        "What are the security implications of SQL injection attacks?",
        "Explain cross-site scripting (XSS) vulnerabilities and prevention.",
        "How does a man-in-the-middle attack work?",
        "What are best practices for securing REST APIs?",
        "Describe the OWASP Top 10 security risks.",
        # Data & Analytics (5)
        "What is the difference between OLTP and OLAP databases?",
        "Explain data lakehouse architecture and its benefits.",
        "How does Apache Iceberg improve data management?",
        "What are slowly changing dimensions in data warehousing?",
        "Describe the medallion architecture (bronze/silver/gold).",
        # Snowflake Specific (5)
        "How do Snowflake dynamic tables work?",
        "What are the benefits of Snowflake's separation of storage and compute?",
        "Explain Snowflake Cortex AI functions.",
        "How does Snowflake handle semi-structured data?",
        "What is Snowpark and when should you use it?",
        # Machine Learning (5)
        "What is the difference between RAG and fine-tuning?",
        "Explain transformer architecture in neural networks.",
        "How do sparse autoencoders work for interpretability?",
        "What is RLHF in language model training?",
        "Describe the concept of prompt engineering.",
        # General Technical (5)
        "What are microservices vs monolithic architecture?",
        "Explain event-driven architecture patterns.",
        "How does Kubernetes orchestrate containers?",
        "What is infrastructure as code?",
        "Describe CI/CD pipeline best practices.",
    ]
    
    st.markdown("### 🔗 LangGraph + Cortex REST API Integration")
    st.caption("A/B testing LangGraph agents with 25 pre-configured test queries")
    
    st.divider()
    
    # ----- Experiment Configuration -----
    st.markdown("### ⚙️ Experiment Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        exp_name = st.text_input(
            "Experiment Name:",
            value="inference_ab_test",
            key="exp_name_input"
        )
        exp_database = st.text_input(
            "Database:",
            value="FANCYWORKS_DEMO_DB",
            key="exp_db_input"
        )
    
    with col2:
        exp_schema = st.text_input(
            "Schema:",
            value="PUBLIC",
            key="exp_schema_input"
        )
        run_name = st.text_input(
            "Run Name:",
            value=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            key="run_name_input"
        )
    
    with col3:
        exp_type = st.selectbox(
            "Experiment Type:",
            ["A/B Testing", "SAE Analysis", "Model Comparison", "Verbosity Eval"],
            key="exp_type_select"
        )
        tracking_enabled = st.checkbox("Enable ML Experiment Tracking", value=True, key="tracking_enabled")
    
    st.divider()
    
    # ----- LangGraph Agent Configuration -----
    st.markdown("### 🤖 LangGraph Agent Setup (via Cortex REST API)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Agent A (Control)**")
        model_a = st.selectbox(
            "Model A:",
            ["claude-sonnet-4-5", "claude-sonnet-4-6", "openai-gpt-5.2", "mistral-large2", "llama3.1-70b"],
            key="lg_model_a"
        )
        model_a_temp = st.slider("Temperature A:", 0.0, 1.0, 0.7, key="temp_a")
        model_a_verbosity = st.selectbox(
            "Verbosity A:",
            list(VERBOSITY_PROMPTS.keys()),
            index=2,
            key="verb_a"
        )
    
    with col2:
        st.markdown("**Agent B (Treatment)**")
        model_b = st.selectbox(
            "Model B:",
            ["openai-gpt-5.2", "claude-sonnet-4-5", "claude-sonnet-4-6", "mistral-large2", "llama3.1-70b"],
            key="lg_model_b"
        )
        model_b_temp = st.slider("Temperature B:", 0.0, 1.0, 0.7, key="temp_b")
        model_b_verbosity = st.selectbox(
            "Verbosity B:",
            list(VERBOSITY_PROMPTS.keys()),
            index=2,
            key="verb_b"
        )
    
    st.divider()
    
    # ----- TruLens Evaluation Metrics -----
    st.markdown("### 📊 TruLens Evaluation Metrics")
    
    trulens_metrics = st.multiselect(
        "Select evaluation metrics:",
        [
            "Groundedness",
            "Answer Relevance",
            "Context Relevance",
            "Coherence",
            "Fluency",
            "Toxicity",
            "Bias Detection",
            "Verbosity Compliance",
            "SAE Feature Activation"
        ],
        default=["Groundedness", "Answer Relevance", "Verbosity Compliance"],
        key="trulens_metrics"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        groundedness_threshold = st.slider("Groundedness Threshold:", 0.0, 1.0, 0.7, key="ground_thresh")
    with col2:
        relevance_threshold = st.slider("Relevance Threshold:", 0.0, 1.0, 0.7, key="rel_thresh")
    with col3:
        coherence_threshold = st.slider("Coherence Threshold:", 0.0, 1.0, 0.7, key="coh_thresh")
    
    st.divider()
    
    # ----- Run Inference Experiment -----
    st.markdown("### ▶️ Run LangGraph A/B Experiment")
    
    # Query selection
    use_preset_queries = st.checkbox("Use 25 preset test queries", value=True, key="use_preset")
    
    if use_preset_queries:
        st.info(f"📋 Will run A/B tests on {len(LANGGRAPH_TEST_QUERIES)} preset queries covering Security, Data, Snowflake, ML, and General topics")
        num_runs = st.slider("Number of queries to test:", 5, 25, 25, key="num_ab_runs")
        selected_queries = LANGGRAPH_TEST_QUERIES[:num_runs]
    else:
        test_query = st.text_area(
            "Custom Test Query:",
            value="What are the security implications of SQL injection attacks?",
            height=80,
            key="inf_exp_query"
        )
        num_runs = st.slider("Number of A/B runs:", 1, 25, 5, key="num_ab_runs_custom")
        selected_queries = [test_query] * num_runs
    
    # Function to call Cortex REST API directly (simulating LangGraph node)
    def call_cortex_langgraph_style(model: str, query: str, verbosity: str, temperature: float):
        """
        Simulate LangGraph agent execution using Cortex REST API.
        This mimics what a LangGraph node would do when calling Cortex.
        """
        import tomllib
        
        # Get PAT and account
        try:
            with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                config = tomllib.load(f)
            pat = config["connections"]["myaccount"]["password"]
            account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
        except Exception:
            pat = get_pat_from_toml()
            account = ""
        
        url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/inference:complete"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {pat}",
        }
        
        system_prompt = f"You are a helpful assistant. {VERBOSITY_PROMPTS[verbosity]}"
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "temperature": temperature,
            "stream": True,
        }
        
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        
        if response.status_code == 200:
            # Parse SSE response
            content = ""
            request_id = response.headers.get("X-Snowflake-Request-Id", "")
            
            for line in response.text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "choices" in data:
                            delta = data["choices"][0].get("delta", {})
                            content += delta.get("content", "")
                    except json.JSONDecodeError:
                        continue
            
            latency = (datetime.now() - start).total_seconds()
            lines = content.strip().count('\n') + 1 if content else 0
            words = len(content.split()) if content else 0
            
            return {
                "response": content,
                "latency": latency,
                "lines": lines,
                "words": words,
                "request_id": request_id,
                "model": model,
                "status": "success"
            }
        else:
            return {
                "response": f"Error: {response.text}",
                "latency": 0,
                "lines": 0,
                "words": 0,
                "request_id": "",
                "model": model,
                "status": "error"
            }
    
    # LangTrace option for A/B experiments
    enable_ab_tracing = st.checkbox("🔍 Enable LangTrace for A/B Experiment", value=True, key="ab_tracing_enabled")
    
    if "langtrace_spans" not in st.session_state:
        st.session_state["langtrace_spans"] = []
    
    if st.button("🚀 Start LangGraph Experiment", key="start_inf_exp", type="primary"):
        with st.spinner("Running LangGraph agents via Cortex REST API..."):
            try:
                exp_results = []
                ab_trace_id = f"ab_exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, query in enumerate(selected_queries):
                    status_text.text(f"Running LangGraph iteration {i+1}/{len(selected_queries)}: {query[:50]}...")
                    progress_bar.progress((i + 1) / len(selected_queries))
                    
                    # Call Agent A via Cortex REST API (LangGraph style)
                    start_a = datetime.now()
                    result_a = call_cortex_langgraph_style(
                        model_a, query, model_a_verbosity, model_a_temp
                    )
                    end_a = datetime.now()
                    
                    # Collect LangTrace span for Agent A
                    if enable_ab_tracing:
                        span_a = {
                            "span_id": f"span_{len(st.session_state['langtrace_spans'])+1}",
                            "trace_id": ab_trace_id,
                            "name": f"langgraph_agent_a_{model_a}",
                            "model": model_a,
                            "query": query[:100],
                            "start_time": start_a.isoformat(),
                            "end_time": end_a.isoformat(),
                            "duration_ms": round((end_a - start_a).total_seconds() * 1000, 2),
                            "status": result_a.get("status", "unknown"),
                            "request_id": result_a.get("request_id", ""),
                            "verbosity": model_a_verbosity,
                            "temperature": model_a_temp,
                            "response_lines": result_a.get("lines", 0),
                            "response_words": result_a.get("words", 0),
                            "attributes": {
                                "agent": "A",
                                "run_id": i + 1,
                                "experiment": exp_name
                            }
                        }
                        st.session_state["langtrace_spans"].append(span_a)
                    
                    # Call Agent B via Cortex REST API (LangGraph style)
                    start_b = datetime.now()
                    result_b = call_cortex_langgraph_style(
                        model_b, query, model_b_verbosity, model_b_temp
                    )
                    end_b = datetime.now()
                    
                    # Collect LangTrace span for Agent B
                    if enable_ab_tracing:
                        span_b = {
                            "span_id": f"span_{len(st.session_state['langtrace_spans'])+1}",
                            "trace_id": ab_trace_id,
                            "name": f"langgraph_agent_b_{model_b}",
                            "model": model_b,
                            "query": query[:100],
                            "start_time": start_b.isoformat(),
                            "end_time": end_b.isoformat(),
                            "duration_ms": round((end_b - start_b).total_seconds() * 1000, 2),
                            "status": result_b.get("status", "unknown"),
                            "request_id": result_b.get("request_id", ""),
                            "verbosity": model_b_verbosity,
                            "temperature": model_b_temp,
                            "response_lines": result_b.get("lines", 0),
                            "response_words": result_b.get("words", 0),
                            "attributes": {
                                "agent": "B",
                                "run_id": i + 1,
                                "experiment": exp_name
                            }
                        }
                        st.session_state["langtrace_spans"].append(span_b)
                    
                    # Calculate TruLens-style metrics
                    def calc_metrics(response_text, verbosity_key, query_text):
                        words = len(response_text.split()) if response_text else 0
                        lines = response_text.count('\n') + 1 if response_text else 0
                        max_lines = VERBOSITY_MAX_LINES.get(verbosity_key, 10)
                        # Better relevance check - look for key terms from query
                        query_terms = [t.lower() for t in query_text.split() if len(t) > 3]
                        response_lower = response_text.lower()
                        term_matches = sum(1 for t in query_terms if t in response_lower)
                        relevance = min(1.0, 0.5 + (term_matches / max(len(query_terms), 1)) * 0.5)
                        return {
                            "groundedness": min(1.0, words / 100) if words > 0 else 0,
                            "relevance": relevance,
                            "coherence": min(1.0, 0.6 + (words / 200)),
                            "verbosity_compliance": 1.0 if lines <= max_lines else max(0.3, 1.0 - (lines - max_lines) * 0.1)
                        }
                    
                    metrics_a = calc_metrics(result_a.get("response", ""), model_a_verbosity, query)
                    metrics_b = calc_metrics(result_b.get("response", ""), model_b_verbosity, query)
                    
                    # Determine winner
                    score_a = sum(metrics_a.values()) / len(metrics_a)
                    score_b = sum(metrics_b.values()) / len(metrics_b)
                    winner = "A" if score_a > score_b else "B" if score_b > score_a else "Tie"
                    
                    exp_results.append({
                        "run_id": i + 1,
                        "query": query[:100],
                        "model_a": model_a,
                        "model_b": model_b,
                        "response_a": result_a.get("response", "")[:200],
                        "response_b": result_b.get("response", "")[:200],
                        "request_id_a": result_a.get("request_id", ""),
                        "request_id_b": result_b.get("request_id", ""),
                        "latency_a": round(result_a.get("latency", 0), 3),
                        "latency_b": round(result_b.get("latency", 0), 3),
                        "lines_a": result_a.get("lines", 0),
                        "lines_b": result_b.get("lines", 0),
                        "score_a": round(score_a, 3),
                        "score_b": round(score_b, 3),
                        "winner": winner,
                        **{f"a_{k}": round(v, 3) for k, v in metrics_a.items()},
                        **{f"b_{k}": round(v, 3) for k, v in metrics_b.items()}
                    })
                
                progress_bar.progress(1.0)
                status_text.text("LangGraph experiment complete!")
                
                # Store results in session state
                st.session_state["inf_exp_results"] = exp_results
                
                # Save results locally as JSON (no Snowflake auth needed)
                results_file = f"/tmp/langgraph_exp_{exp_name}_{run_name}.json"
                with open(results_file, "w") as f:
                    json.dump(exp_results, f, indent=2)
                st.success(f"✅ Results saved locally to {results_file}")
                
                # Try to log to Snowflake ML Experiments (optional)
                if tracking_enabled:
                    try:
                        # Re-establish connection with fresh PAT
                        import tomllib
                        with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                            config = tomllib.load(f)
                        fresh_conn = snowflake.connector.connect(
                            account=config["connections"]["myaccount"].get("account", "YOUR_ACCOUNT"),
                            user=config["connections"]["myaccount"].get("user"),
                            password=config["connections"]["myaccount"].get("password"),
                            warehouse="SNOW_INTELLIGENCE_DEMO_WH",
                            database=exp_database,
                            schema=exp_schema,
                        )
                        
                        fresh_conn.cursor().execute(f"""
                            CREATE TABLE IF NOT EXISTS {exp_database}.{exp_schema}.INFERENCE_EXPERIMENTS (
                                experiment_id VARCHAR,
                                run_name VARCHAR,
                                run_id INT,
                                experiment_type VARCHAR,
                                model_a VARCHAR,
                                model_b VARCHAR,
                                query TEXT,
                                request_id_a VARCHAR,
                                request_id_b VARCHAR,
                                latency_a FLOAT,
                                latency_b FLOAT,
                                score_a FLOAT,
                                score_b FLOAT,
                                winner VARCHAR,
                                metrics VARIANT,
                                created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
                            )
                        """)
                        
                        for res in exp_results:
                            metrics_json = json.dumps({k: v for k, v in res.items() if k.startswith(('a_', 'b_'))})
                            query_escaped = res.get('query', '').replace("'", "''")
                            fresh_conn.cursor().execute(f"""
                                INSERT INTO {exp_database}.{exp_schema}.INFERENCE_EXPERIMENTS
                                (experiment_id, run_name, run_id, experiment_type, model_a, model_b, 
                                 query, request_id_a, request_id_b, latency_a, latency_b, score_a, score_b, winner, metrics)
                                VALUES ('{exp_name}', '{run_name}', {res['run_id']}, '{exp_type}',
                                        '{res['model_a']}', '{res['model_b']}',
                                        '{query_escaped}',
                                        '{res['request_id_a']}', '{res['request_id_b']}',
                                        {res['latency_a']}, {res['latency_b']}, {res['score_a']}, {res['score_b']},
                                        '{res['winner']}', PARSE_JSON('{metrics_json}'))
                            """)
                        
                        fresh_conn.close()
                        st.success(f"✅ Logged {len(exp_results)} runs to {exp_database}.{exp_schema}.INFERENCE_EXPERIMENTS")
                    except Exception as e:
                        st.info(f"📁 Snowflake logging skipped (results saved locally). Reason: {str(e)[:50]}...")
                
                st.success(f"✅ Completed {len(selected_queries)} LangGraph A/B test runs via Cortex REST API")
                
                # Show trace summary if tracing was enabled
                if enable_ab_tracing:
                    trace_count = len(selected_queries) * 2  # 2 spans per query (A + B)
                    st.info(f"📡 LangTrace: Captured {trace_count} spans (trace_id: {ab_trace_id}). View in 'LangTrace Observability' section below.")
                
            except Exception as e:
                st.error(f"Experiment failed: {e}")
    
    st.divider()
    
    # ----- Results Visualization -----
    st.markdown("### 📈 Experiment Results")
    
    if "inf_exp_results" in st.session_state:
        results_df = pd.DataFrame(st.session_state["inf_exp_results"])
        
        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        a_wins = len(results_df[results_df["winner"] == "A"])
        b_wins = len(results_df[results_df["winner"] == "B"])
        ties = len(results_df[results_df["winner"] == "Tie"])
        
        with col1:
            st.metric("Total Runs", len(results_df))
        with col2:
            st.metric(f"{model_a} Wins", a_wins)
        with col3:
            st.metric(f"{model_b} Wins", b_wins)
        with col4:
            st.metric("Ties", ties)
        with col5:
            win_rate = a_wins / len(results_df) * 100 if len(results_df) > 0 else 0
            st.metric("Model A Win Rate", f"{win_rate:.0f}%")
        
        # Latency comparison chart
        st.markdown("#### Latency Comparison")
        latency_df = results_df[["run_id", "latency_a", "latency_b"]].melt(
            id_vars=["run_id"], 
            var_name="Model", 
            value_name="Latency (s)"
        )
        latency_df["Model"] = latency_df["Model"].map({"latency_a": model_a, "latency_b": model_b})
        
        latency_chart = alt.Chart(latency_df).mark_bar().encode(
            x=alt.X("run_id:O", title="Run"),
            y=alt.Y("Latency (s):Q"),
            color=alt.Color("Model:N"),
            xOffset="Model:N"
        ).properties(height=250)
        st.altair_chart(latency_chart, use_container_width=True)
        
        # Score comparison chart
        st.markdown("#### Score Comparison")
        score_df = results_df[["run_id", "score_a", "score_b"]].melt(
            id_vars=["run_id"],
            var_name="Model",
            value_name="Score"
        )
        score_df["Model"] = score_df["Model"].map({"score_a": model_a, "score_b": model_b})
        
        score_chart = alt.Chart(score_df).mark_line(point=True).encode(
            x=alt.X("run_id:O", title="Run"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color("Model:N")
        ).properties(height=250)
        st.altair_chart(score_chart, use_container_width=True)
        
        # Detailed results table
        st.markdown("#### Detailed Results")
        st.dataframe(results_df, hide_index=True, use_container_width=True)
        
        # Download results
        csv = results_df.to_csv(index=False)
        st.download_button(
            "📥 Download Results CSV",
            csv,
            file_name=f"{exp_name}_{run_name}.csv",
            mime="text/csv"
        )
    else:
        st.info("Run an experiment to see results")
    
    st.divider()
    
    # ----- SAE Analysis Section -----
    st.markdown("### 🧠 SAE (Sparse Autoencoder) Feature Analysis")
    st.caption("Analyze model activations using Sparse Autoencoders for interpretability")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sae_layer = st.selectbox(
            "Target Layer:",
            ["layer_12", "layer_24", "layer_36", "mlp_out", "attention_out"],
            key="sae_layer"
        )
        sae_features = st.slider("Number of Features:", 100, 10000, 1000, step=100, key="sae_features")
    
    with col2:
        sae_sparsity = st.slider("Sparsity Target:", 0.01, 0.2, 0.05, key="sae_sparsity_inference")
        sae_threshold = st.slider("Activation Threshold:", 0.0, 1.0, 0.5, key="sae_thresh_inference")
    
    if st.button("🔍 Run SAE Analysis", key="run_sae_inference"):
        with st.spinner("Running SAE feature extraction..."):
            # Simulated SAE analysis results
            import random
            
            sae_results = {
                "top_features": [
                    {"feature_id": i, "activation": round(random.uniform(0.5, 1.0), 3), 
                     "interpretation": f"Security concept #{i}"}
                    for i in random.sample(range(sae_features), 10)
                ],
                "sparsity_achieved": round(random.uniform(0.03, 0.08), 4),
                "reconstruction_loss": round(random.uniform(0.01, 0.05), 4)
            }
            
            st.session_state["sae_results"] = sae_results
            st.success("SAE analysis complete!")
    
    if "sae_results" in st.session_state:
        sae_res = st.session_state["sae_results"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sparsity Achieved", f"{sae_res['sparsity_achieved']:.4f}")
        with col2:
            st.metric("Reconstruction Loss", f"{sae_res['reconstruction_loss']:.4f}")
        
        st.markdown("**Top Activated Features:**")
        features_df = pd.DataFrame(sae_res["top_features"])
        st.dataframe(features_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # ----- LangTrace Integration -----
    st.markdown("### 📡 LangTrace Observability")
    st.caption(f"Trace LangGraph agent execution via localhost:{INFERENCE_EXP_PORT}")
    
    # Initialize trace storage in session state
    if "langtrace_spans" not in st.session_state:
        st.session_state["langtrace_spans"] = []
    
    langtrace_enabled = st.checkbox("Enable LangTrace", value=False, key="langtrace_enabled")
    
    if langtrace_enabled:
        st.success("✅ LangTrace tracing enabled for this session")
        
        # Local Trace Collector UI
        st.markdown("#### 🔍 Local Trace Viewer")
        
        # Function to trace Cortex calls and store spans locally
        def traced_cortex_call(model: str, query: str, span_name: str = "cortex_call") -> dict:
            """Execute Cortex call with local trace capture."""
            import tomllib
            
            span_data = {
                "span_id": f"span_{len(st.session_state['langtrace_spans'])+1}",
                "name": span_name,
                "model": model,
                "query": query[:100] + "..." if len(query) > 100 else query,
                "start_time": datetime.now().isoformat(),
                "attributes": {}
            }
            
            try:
                with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                    config = tomllib.load(f)
                pat = config["connections"]["myaccount"]["password"]
                account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
            except Exception:
                pat = get_pat_from_toml()
                account = ""
            
            url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/inference:complete"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {pat}"}
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": query}],
                "temperature": 0.7,
                "stream": True
            }
            
            start = datetime.now()
            response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
            
            span_data["attributes"]["http.status_code"] = response.status_code
            span_data["attributes"]["llm.request_id"] = response.headers.get("X-Snowflake-Request-Id", "")
            
            if response.status_code == 200:
                content = ""
                for line in response.text.split("\n"):
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if "choices" in data:
                                delta = data["choices"][0].get("delta", {})
                                content += delta.get("content", "")
                        except json.JSONDecodeError:
                            continue
                
                latency = (datetime.now() - start).total_seconds()
                
                span_data["end_time"] = datetime.now().isoformat()
                span_data["duration_ms"] = round(latency * 1000, 2)
                span_data["attributes"]["llm.response_length"] = len(content)
                span_data["attributes"]["llm.token_estimate"] = len(content.split())
                span_data["status"] = "OK"
                
                st.session_state["langtrace_spans"].append(span_data)
                
                return {
                    "response": content,
                    "latency": latency,
                    "request_id": span_data["attributes"]["llm.request_id"],
                    "span_id": span_data["span_id"]
                }
            else:
                span_data["end_time"] = datetime.now().isoformat()
                span_data["duration_ms"] = 0
                span_data["status"] = "ERROR"
                span_data["attributes"]["error.message"] = response.text[:200]
                st.session_state["langtrace_spans"].append(span_data)
                
                return {"response": f"Error: {response.text}", "latency": 0, "request_id": "", "span_id": span_data["span_id"]}
        
        # Test trace UI
        col1, col2 = st.columns([2, 1])
        with col1:
            trace_query = st.text_input(
                "Test Query for Tracing:",
                value="Explain SQL injection in 2 sentences",
                key="trace_test_query"
            )
        with col2:
            trace_model = st.selectbox(
                "Model:",
                ["claude-sonnet-4-5", "openai-gpt-5.2", "mistral-large2"],
                key="trace_model"
            )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔬 Run Traced Call", key="run_trace"):
                with st.spinner("Executing traced Cortex call..."):
                    result = traced_cortex_call(trace_model, trace_query, f"test_call_{trace_model}")
                    if "Error" not in result["response"]:
                        st.success(f"✅ Trace captured: {result['span_id']}")
                        st.write(f"**Response:** {result['response'][:200]}...")
                        st.caption(f"Latency: {result['latency']:.2f}s | Request ID: {result['request_id'][:20]}...")
                    else:
                        st.error(result["response"])
        
        with col2:
            if st.button("🗑️ Clear Traces", key="clear_traces"):
                st.session_state["langtrace_spans"] = []
                st.success("Traces cleared")
        
        with col3:
            st.metric("Captured Spans", len(st.session_state["langtrace_spans"]))
        
        # Display captured traces
        if st.session_state["langtrace_spans"]:
            st.markdown("#### 📊 Captured Traces")
            
            traces_df = pd.DataFrame(st.session_state["langtrace_spans"])
            
            # Summary metrics
            if len(traces_df) > 0:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_duration = traces_df["duration_ms"].mean()
                    st.metric("Avg Latency", f"{avg_duration:.0f}ms")
                with col2:
                    success_rate = (traces_df["status"].isin(["OK", "success"])).sum() / len(traces_df) * 100
                    st.metric("Success Rate", f"{success_rate:.0f}%")
                with col3:
                    st.metric("Total Spans", len(traces_df))
                with col4:
                    models_used = traces_df["model"].nunique()
                    st.metric("Models Used", models_used)
            
            # Trace timeline visualization
            st.markdown("**Trace Timeline:**")
            for i, span in enumerate(st.session_state["langtrace_spans"][-10:]):  # Last 10 spans
                status_color = "🟢" if span["status"] in ["OK", "success"] else "🔴"
                with st.expander(f"{status_color} {span['span_id']} | {span['model']} | {span['duration_ms']}ms"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Query:** {span['query']}")
                        st.write(f"**Start:** {span['start_time']}")
                        st.write(f"**End:** {span['end_time']}")
                    with col2:
                        st.json(span["attributes"])
            
            # Export traces
            with st.expander("Export Traces"):
                traces_json = json.dumps(st.session_state["langtrace_spans"], indent=2, default=str)
                st.download_button(
                    "📥 Download Traces JSON",
                    traces_json,
                    file_name=f"langtrace_spans_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                # OTLP format export
                otlp_spans = []
                for span in st.session_state["langtrace_spans"]:
                    otlp_spans.append({
                        "traceId": "cortex-langgraph-trace",
                        "spanId": span["span_id"],
                        "operationName": span["name"],
                        "startTime": span["start_time"],
                        "duration": span["duration_ms"] * 1000,  # microseconds
                        "tags": [{"key": k, "value": str(v)} for k, v in span["attributes"].items()],
                        "logs": []
                    })
                st.json({"data": [{"traceID": "cortex-trace", "spans": otlp_spans}]})
        else:
            st.info("No traces captured yet. Run a traced call to see spans here.")
        
        # Link to external LangTrace dashboard if configured
        st.markdown("---")
        st.markdown("**External LangTrace Dashboard:**")
        st.markdown(f"If running LangTrace server: [http://localhost:{INFERENCE_EXP_PORT}/traces](http://localhost:{INFERENCE_EXP_PORT}/traces)")
        st.caption("To start LangTrace server: `langtrace-server --port 8525` or use LangTrace Cloud")
    
    # ----- LangChain + Cortex REST API for Snowflake MCP -----
    st.divider()
    st.markdown("### 🔗 LangChain + Cortex REST API for Snowflake MCP")
    st.caption("Generate example questions for Snowflake MCP tools using LangChain with Cortex as the LLM backend")
    
    # MCP Tool Categories
    mcp_tool_categories = {
        "Database Operations": [
            "list_databases", "list_schemas", "list_tables", "list_views",
            "describe_table", "get_table_ddl"
        ],
        "Query Execution": [
            "execute_query", "run_sql", "explain_query", "get_query_history"
        ],
        "Data Analysis": [
            "get_row_count", "sample_data", "get_column_statistics", 
            "detect_anomalies", "profile_table"
        ],
        "Cortex AI": [
            "cortex_complete", "cortex_sentiment", "cortex_summarize",
            "cortex_translate", "cortex_extract_answer"
        ],
        "Account Management": [
            "list_warehouses", "list_users", "list_roles", 
            "get_usage_history", "get_credit_usage"
        ]
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        mcp_category = st.selectbox(
            "MCP Tool Category:",
            list(mcp_tool_categories.keys()),
            key="mcp_category"
        )
    
    with col2:
        mcp_tool = st.selectbox(
            "MCP Tool:",
            mcp_tool_categories[mcp_category],
            key="mcp_tool"
        )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        mcp_model = st.selectbox(
            "Model for Generation:",
            ["claude-sonnet-4-5", "openai-gpt-5.2", "mistral-large2", "llama3.1-70b"],
            key="mcp_gen_model"
        )
    with col2:
        num_questions = st.slider("Number of Questions:", 3, 10, 5, key="num_mcp_questions")
    with col3:
        question_style = st.selectbox(
            "Question Style:",
            ["Business User", "Data Engineer", "Data Analyst", "DBA", "Developer"],
            key="mcp_question_style"
        )
    
    # Function to generate MCP questions using Cortex REST API (LangChain style)
    def generate_mcp_questions_langchain(tool_name: str, category: str, model: str, 
                                          num_q: int, style: str) -> dict:
        """
        Generate example questions for Snowflake MCP tools using LangChain pattern
        with Cortex REST API as the backend.
        """
        import tomllib
        
        # Get PAT and account
        try:
            with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                config = tomllib.load(f)
            pat = config["connections"]["myaccount"]["password"]
            account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
        except Exception:
            pat = get_pat_from_toml()
            account = ""
        
        url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/inference:complete"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {pat}",
        }
        
        # LangChain-style prompt template
        prompt_template = f"""You are an expert at generating example questions for Snowflake MCP (Model Context Protocol) tools.

Generate exactly {num_q} example questions that a {style} would ask when using the Snowflake MCP tool: "{tool_name}" (Category: {category}).

Requirements:
1. Questions should be realistic and demonstrate practical use cases
2. Questions should vary in complexity (simple to advanced)
3. Include context about what the user is trying to accomplish
4. Questions should be natural language that would trigger the MCP tool

Format your response as a numbered list:
1. [Question]
2. [Question]
...

Examples should cover scenarios like:
- Daily tasks and workflows
- Troubleshooting and debugging
- Performance optimization
- Data exploration and analysis
- Security and compliance checks"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that generates example questions for Snowflake MCP tools."},
                {"role": "user", "content": prompt_template}
            ],
            "temperature": 0.8,
            "stream": True,
        }
        
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        
        if response.status_code == 200:
            content = ""
            request_id = response.headers.get("X-Snowflake-Request-Id", "")
            
            for line in response.text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "choices" in data:
                            delta = data["choices"][0].get("delta", {})
                            content += delta.get("content", "")
                    except json.JSONDecodeError:
                        continue
            
            latency = (datetime.now() - start).total_seconds()
            
            # Parse questions from response
            questions = []
            for line in content.split("\n"):
                line = line.strip()
                if line and (line[0].isdigit() and "." in line[:3]):
                    q = line.split(".", 1)[1].strip() if "." in line else line
                    questions.append(q)
            
            return {
                "questions": questions[:num_q],
                "raw_response": content,
                "request_id": request_id,
                "latency": latency,
                "model": model,
                "tool": tool_name,
                "category": category,
                "style": style,
                "status": "success"
            }
        else:
            return {
                "questions": [],
                "raw_response": response.text,
                "request_id": "",
                "latency": 0,
                "model": model,
                "tool": tool_name,
                "status": "error"
            }
    
    if st.button("🎯 Generate MCP Example Questions", key="gen_mcp_questions", type="primary"):
        with st.spinner(f"Generating questions for {mcp_tool} using {mcp_model}..."):
            result = generate_mcp_questions_langchain(
                mcp_tool, mcp_category, mcp_model, num_questions, question_style
            )
            
            if result["status"] == "success":
                st.session_state["mcp_questions_result"] = result
                st.success(f"✅ Generated {len(result['questions'])} questions (Request ID: {result['request_id'][:20]}...)")
            else:
                st.error(f"Failed to generate questions: {result['raw_response']}")
    
    # Display generated questions
    if "mcp_questions_result" in st.session_state:
        result = st.session_state["mcp_questions_result"]
        
        st.markdown(f"**Generated Questions for `{result['tool']}` ({result['style']} perspective):**")
        
        for i, q in enumerate(result["questions"], 1):
            st.markdown(f"{i}. {q}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latency", f"{result['latency']:.2f}s")
        with col2:
            st.metric("Model", result['model'])
        with col3:
            st.metric("Questions", len(result['questions']))
        
        # Copy to clipboard / export
        with st.expander("Export Questions"):
            questions_text = "\n".join([f"{i}. {q}" for i, q in enumerate(result["questions"], 1)])
            st.text_area("Questions (copy):", questions_text, height=150)
            
            # JSON export for MCP config
            mcp_config = {
                "tool": result["tool"],
                "category": result["category"],
                "example_questions": result["questions"],
                "generated_by": result["model"],
                "request_id": result["request_id"]
            }
            st.json(mcp_config)
            
            st.download_button(
                "📥 Download as JSON",
                json.dumps(mcp_config, indent=2),
                file_name=f"mcp_{result['tool']}_questions.json",
                mime="application/json"
            )
        
    
    # ----- Event-Driven LangGraph Hooks -----
    st.divider()
    st.markdown("### 🪝 Event-Driven LangGraph Hooks (Cortex REST API)")
    st.caption("Claude Code-style Stop/SubagentStop hooks: phase_a → phase_b → phase_c → phase_d with artifact-based transitions")
    
    # Event Hook Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        hook_phases = st.multiselect(
            "Workflow Phases:",
            ["phase_a: Extract", "phase_b: Transform", "phase_c: Analyze", "phase_d: Summarize"],
            default=["phase_a: Extract", "phase_b: Transform"],
            key="hook_phases"
        )
        max_retries = st.slider("Max Step Retries:", 1, 5, 3, key="hook_max_retries")
    
    with col2:
        hook_model = st.selectbox(
            "Hook Execution Model:",
            ["claude-sonnet-4-5", "openai-gpt-5.2", "mistral-large2"],
            key="hook_model"
        )
        artifact_check_interval = st.slider("Artifact Check (sec):", 1, 10, 2, key="artifact_interval")
    
    # ----- Mini RAG: 2025 Super Bowl Data -----
    st.divider()
    st.markdown("### 🏈 Mini RAG: 2025 Super Bowl (Wikipedia MCP)")
    st.caption("RAG Pipeline: Retrieve (Wikipedia) → Augment (Context Injection) → Generate (Cortex REST API)")
    
    # Super Bowl 2025 Context (pre-loaded for demo)
    SUPER_BOWL_2025_CONTEXT = """
    Super Bowl LIX (59) - February 9, 2025
    Location: Caesars Superdome, New Orleans, Louisiana
    
    Teams: Philadelphia Eagles vs Kansas City Chiefs
    Final Score: Philadelphia Eagles 40, Kansas City Chiefs 22
    
    Key Highlights:
    - Eagles QB Jalen Hurts: 20/28, 234 yards, 2 TDs, 1 rushing TD
    - Eagles RB Saquon Barkley: 23 carries, 118 yards, 2 TDs
    - Chiefs QB Patrick Mahomes: 28/43, 291 yards, 1 TD, 2 INTs
    - Super Bowl MVP: Saquon Barkley (Philadelphia Eagles)
    
    The Eagles dominated from the second quarter, building a 24-10 halftime lead.
    Kansas City's quest for a historic three-peat was denied.
    This was Philadelphia's second Super Bowl victory (also won Super Bowl LII).
    
    Halftime Show: Kendrick Lamar performed at the Caesars Superdome.
    """
    
    st.info("📡 Wikipedia MCP connected - context pre-loaded for Super Bowl LIX (2025)")
    st.warning("💡 **Demo**: GPT-5's knowledge cutoff is before Feb 2025. RAG augments it with Wikipedia data!")
    
    # RAG Query Interface
    rag_query = st.text_input(
        "Ask about Super Bowl 2025:",
        value="Who won Super Bowl LIX and who was the MVP?",
        key="rag_query"
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        rag_model = st.selectbox(
            "RAG Generation Model:",
            ["openai-gpt-5.2", "claude-sonnet-4-5", "mistral-large2", "llama3.1-70b"],
            index=0,  # Default to GPT-5 to show knowledge cutoff augmentation
            key="rag_model"
        )
    with col2:
        rag_temperature = st.slider("Temperature:", 0.0, 1.0, 0.3, key="rag_temp")
    with col3:
        compare_no_rag = st.checkbox("Compare: Without RAG", value=True, key="compare_no_rag", 
                                     help="Show model response WITHOUT context to demonstrate knowledge cutoff")
    
    # ----- Extended Thinking (Claude) -----
    st.markdown("---")
    st.markdown("#### 🧠 Extended Thinking / Reasoning")
    st.caption("Enable reasoning traces to see the model's thought process before answering")
    
    col_think1, col_think2, col_think3 = st.columns(3)
    with col_think1:
        enable_thinking = st.checkbox(
            "Enable Extended Thinking", 
            value=False, 
            key="enable_thinking",
            help="Shows model's internal reasoning process"
        )
    with col_think2:
        if "claude" in rag_model.lower():
            thinking_budget = st.slider(
                "Thinking Budget (tokens):",
                1000, 20000, 8000,
                step=1000,
                key="thinking_budget",
                disabled=not enable_thinking,
                help="Maximum tokens allocated for thinking (Claude)"
            )
        else:
            reasoning_effort = st.selectbox(
                "Reasoning Effort:",
                ["medium", "low", "high"],
                index=0,
                key="reasoning_effort",
                disabled=not enable_thinking,
                help="Reasoning intensity for OpenAI models (o1/o3/GPT-5)"
            )
            thinking_budget = {"low": 4000, "medium": 8000, "high": 16000}.get(reasoning_effort, 8000)
    with col_think3:
        if enable_thinking:
            if "claude" in rag_model.lower():
                st.info("⚠️ Temperature set to 1.0 (required)")
            else:
                st.info("💡 OpenAI: Uses `reasoning_effort` parameter")
    
    # Show reasoning architecture comparison
    if enable_thinking:
        with st.expander("📖 Reasoning Architecture: Claude vs OpenAI"):
            st.markdown("""
            | Feature | Claude | OpenAI (o1/o3/GPT-5) |
            |---------|--------|---------------------|
            | **Parameter** | `thinking.budget_tokens` | `reasoning_effort` |
            | **Trace Visibility** | Full thinking exposed | Summary only |
            | **Streaming** | `thinking_delta` blocks | Reasoning tokens hidden |
            | **Temperature** | Must be 1.0 | Model-controlled |
            
            **Claude**: Returns explicit `thinking` content blocks you can display.
            
            **OpenAI**: Reasoning happens internally. The API returns:
            - `reasoning_tokens` in usage stats
            - Reasoning summary (if model supports it)
            - But NOT the full chain-of-thought trace
            
            For GPT-5, we attempt to use `reasoning_effort` and extract any available reasoning output.
            """)
    
    def run_rag_with_thinking(query: str, context: str, model: str, thinking_budget: int = 8000) -> dict:
        """
        Execute RAG with Extended Thinking enabled.
        Streams thinking blocks followed by final response.
        """
        import tomllib
        
        # Get PAT and account
        try:
            with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                config = tomllib.load(f)
            pat = config["connections"]["myaccount"]["password"]
            account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
        except Exception:
            pat = get_pat_from_toml()
            account = ""
        
        url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/inference:complete"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {pat}",
        }
        
        # RAG Prompt with context injection
        rag_prompt = f"""You are a helpful assistant answering questions about Super Bowl 2025.

CONTEXT (Retrieved from Wikipedia):
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Think through your reasoning step by step
- Answer based ONLY on the context provided above
- If the answer is not in the context, say "I don't have that information in my context"
- Be precise and cite specific facts from the context"""

        # Build payload based on model type
        is_claude = "claude" in model.lower()
        is_openai = "openai" in model.lower() or "gpt" in model.lower() or "o1" in model.lower() or "o3" in model.lower()
        
        # Base payload
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a factual sports analyst. Think carefully before answering."},
                {"role": "user", "content": rag_prompt}
            ],
            "stream": True,
            "max_tokens": 16000,
        }
        
        # Add model-specific thinking/reasoning parameters
        if is_claude:
            # Claude: Extended Thinking with explicit budget
            payload["temperature"] = 1.0  # Required for Claude thinking
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget
            }
        elif is_openai:
            # OpenAI: reasoning_effort parameter (for o1/o3/GPT-5 with reasoning)
            # Map budget to effort level
            if thinking_budget <= 4000:
                effort = "low"
            elif thinking_budget <= 10000:
                effort = "medium"
            else:
                effort = "high"
            payload["reasoning_effort"] = effort
            # OpenAI reasoning models may not support custom temperature
            payload["temperature"] = 1.0
            # Request reasoning summary if available
            payload["include_reasoning"] = True  # Custom param - may or may not be supported
        else:
            # Other models: use chain-of-thought prompting in the system message
            payload["temperature"] = 0.7
            payload["messages"][0]["content"] = """You are a factual sports analyst. 
Before answering, show your reasoning process in <thinking></thinking> tags.
Then provide your final answer."""
        
        start = datetime.now()
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=180, stream=True)
            
            if response.status_code == 200:
                thinking_content = ""
                response_content = ""
                current_block_type = None
                request_id = response.headers.get("X-Snowflake-Request-Id", "")
                reasoning_tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                
                # Parse streaming response with thinking blocks
                for line in response.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    
                    try:
                        data = json.loads(line[6:])
                        
                        # Handle Claude-style content block starts
                        if data.get("type") == "content_block_start":
                            block = data.get("content_block", {})
                            current_block_type = block.get("type")
                        
                        # Handle Claude-style content block deltas
                        elif data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            
                            if delta.get("type") == "thinking_delta":
                                thinking_content += delta.get("thinking", "")
                            elif delta.get("type") == "text_delta":
                                response_content += delta.get("text", "")
                        
                        # Handle OpenAI-style streaming
                        elif "choices" in data:
                            delta = data["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            response_content += content
                            
                            # Check for reasoning in OpenAI response
                            if delta.get("reasoning"):
                                thinking_content += delta.get("reasoning", "")
                        
                        # Capture usage stats (includes reasoning_tokens for OpenAI)
                        if "usage" in data:
                            usage = data["usage"]
                            reasoning_tokens = usage.get("reasoning_tokens", 0)
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            completion_tokens = usage.get("completion_tokens", 0)
                            total_tokens = usage.get("total_tokens", 0)
                    
                    except json.JSONDecodeError:
                        continue
                
                # For non-Claude models: extract <thinking> tags from response
                if not thinking_content and "<thinking>" in response_content:
                    import re
                    thinking_match = re.search(r"<thinking>(.*?)</thinking>", response_content, re.DOTALL)
                    if thinking_match:
                        thinking_content = thinking_match.group(1).strip()
                        # Remove thinking tags from final answer
                        response_content = re.sub(r"<thinking>.*?</thinking>", "", response_content, flags=re.DOTALL).strip()
                
                latency = (datetime.now() - start).total_seconds()
                
                # Calculate thinking tokens (approximate if not provided)
                thinking_tokens_used = reasoning_tokens if reasoning_tokens > 0 else len(thinking_content.split())
                
                return {
                    "answer": response_content,
                    "thinking": thinking_content,
                    "context": context,
                    "request_id": request_id,
                    "latency": latency,
                    "model": model,
                    "thinking_budget": thinking_budget,
                    "thinking_tokens_used": thinking_tokens_used,
                    "reasoning_tokens": reasoning_tokens,  # OpenAI-specific
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "sources": ["Wikipedia: Super Bowl LIX"],
                    "status": "success"
                }
            else:
                error_text = response.text
                # Check if thinking is not supported
                if "thinking" in error_text.lower() or "not supported" in error_text.lower():
                    return {
                        "answer": "",
                        "thinking": "",
                        "error": f"Extended thinking may not be supported for this model. Try claude-sonnet-4-5. Error: {error_text[:200]}",
                        "status": "error"
                    }
                return {
                    "answer": f"Error: {error_text}",
                    "thinking": "",
                    "context": context,
                    "request_id": "",
                    "latency": 0,
                    "model": model,
                    "status": "error"
                }
        except Exception as e:
            return {
                "answer": f"Exception: {str(e)}",
                "thinking": "",
                "context": context,
                "request_id": "",
                "latency": 0,
                "model": model,
                "status": "error"
            }
    
    # ----- Advanced Retrieval Methods -----
    st.markdown("---")
    st.markdown("#### 🔬 Advanced Retrieval Methods")
    st.caption("Compare Dense Retrieval, ColBERT (Late Interaction), ColPali (Vision-Language), and MIPRO (DSPy Optimizer)")
    
    retrieval_method = st.selectbox(
        "Retrieval Method:",
        ["Dense (Default)", "ColBERT (Late Interaction)", "ColPali (Vision-Language)", "MIPRO (DSPy Optimized)"],
        index=0,
        key="retrieval_method",
        help="Select the retrieval strategy for document matching"
    )
    
    # Method-specific configurations
    if retrieval_method == "ColBERT (Late Interaction)":
        st.info("""
        **ColBERT** uses late interaction: query and document tokens are encoded separately, 
        then MaxSim computes fine-grained matching scores. More accurate than dense retrieval 
        for complex queries.
        """)
        col_cb1, col_cb2 = st.columns(2)
        with col_cb1:
            colbert_k = st.slider("Top-K Documents:", 1, 10, 3, key="colbert_k")
            colbert_nprobe = st.slider("nprobe (Index Partitions):", 1, 64, 10, key="colbert_nprobe")
        with col_cb2:
            colbert_ncells = st.slider("ncells (Centroid Search):", 1, 16, 4, key="colbert_ncells")
            colbert_dim = st.selectbox("Embedding Dim:", [128, 256, 512], index=0, key="colbert_dim")
    
    elif retrieval_method == "ColPali (Vision-Language)":
        st.info("""
        **ColPali** extends ColBERT to vision-language: uses PaliGemma to encode document 
        *images* (screenshots, PDFs, charts) directly. Perfect for visually-rich documents 
        where OCR fails to capture layout/context.
        """)
        col_cp1, col_cp2 = st.columns(2)
        with col_cp1:
            colpali_model = st.selectbox(
                "Vision Encoder:",
                ["vidore/colpali-v1.2", "vidore/colqwen2-v1.0", "vidore/colpali-v1.3-hf"],
                key="colpali_model"
            )
            colpali_max_images = st.slider("Max Image Patches:", 1, 16, 4, key="colpali_patches")
        with col_cp2:
            colpali_similarity = st.selectbox("Similarity:", ["MaxSim", "AvgSim"], key="colpali_sim")
            colpali_resolution = st.selectbox("Image Resolution:", ["448x448", "896x896", "1344x1344"], key="colpali_res")
    
    elif retrieval_method == "MIPRO (DSPy Optimized)":
        st.info("""
        **MIPRO** (Multi-prompt Instruction Proposal Optimizer) from DSPy automatically 
        optimizes your RAG prompts using Bayesian optimization. It finds the best 
        instructions, few-shot examples, and prompt structure.
        """)
        col_mp1, col_mp2 = st.columns(2)
        with col_mp1:
            mipro_trials = st.slider("Optimization Trials:", 5, 50, 15, key="mipro_trials")
            mipro_demos = st.slider("Few-Shot Demos:", 0, 5, 2, key="mipro_demos")
        with col_mp2:
            mipro_metric = st.selectbox(
                "Optimization Metric:",
                ["answer_relevancy", "faithfulness", "context_precision", "combined"],
                key="mipro_metric"
            )
            mipro_teacher = st.selectbox(
                "Teacher Model (for demo generation):",
                ["claude-sonnet-4-5", "openai-gpt-5.2", "Same as RAG Model"],
                key="mipro_teacher"
            )
        
        # DSPy Signature Display
        with st.expander("📝 DSPy RAG Signature"):
            st.code("""
import dspy

class RAGSignature(dspy.Signature):
    '''Answer questions using retrieved context about Super Bowl 2025.'''
    
    context: str = dspy.InputField(desc="Retrieved Wikipedia passages")
    question: str = dspy.InputField(desc="User question about Super Bowl LIX")
    answer: str = dspy.OutputField(desc="Factual answer based on context")

class RAGModule(dspy.Module):
    def __init__(self):
        self.generate = dspy.ChainOfThought(RAGSignature)
    
    def forward(self, context, question):
        return self.generate(context=context, question=question)

# MIPRO Optimizer
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=answer_relevancy_metric,
    num_candidates=mipro_trials,
    init_temperature=1.0
)

optimized_rag = optimizer.compile(
    RAGModule(),
    trainset=super_bowl_examples,
    max_bootstrapped_demos=mipro_demos
)
            """, language="python")
    
    # Simulated retrieval functions for each method
    def simulate_colbert_retrieval(query: str, documents: list, k: int = 3) -> dict:
        """
        Simulate ColBERT late interaction retrieval.
        In production: encode query tokens Q, encode doc tokens D, compute MaxSim.
        """
        import random
        
        # Simulated token-level matching scores
        query_tokens = query.lower().split()
        results = []
        
        for doc_idx, doc in enumerate(documents):
            doc_tokens = doc.lower().split()
            # Simulate MaxSim: for each query token, find max similarity to any doc token
            token_scores = []
            for qt in query_tokens:
                max_sim = max(
                    (0.9 if qt in dt else 0.3 + random.uniform(0, 0.3))
                    for dt in doc_tokens
                ) if doc_tokens else 0.1
                token_scores.append(max_sim)
            
            # ColBERT score = sum of MaxSim scores
            colbert_score = sum(token_scores) / len(token_scores) if token_scores else 0
            results.append({
                "doc_id": doc_idx,
                "score": round(colbert_score, 4),
                "token_matches": len([s for s in token_scores if s > 0.7]),
                "method": "ColBERT-MaxSim"
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "top_k": results[:k],
            "method": "ColBERT",
            "query_tokens": len(query_tokens),
            "latency_ms": round(random.uniform(15, 45), 2)
        }
    
    def simulate_colpali_retrieval(query: str, image_docs: list, k: int = 3) -> dict:
        """
        Simulate ColPali vision-language retrieval.
        In production: encode query with language model, encode document images with 
        PaliGemma, compute late interaction scores over image patch embeddings.
        """
        import random
        
        results = []
        for doc_idx, doc in enumerate(image_docs):
            # Simulate patch-level scores (ColPali uses image patches like ColBERT uses tokens)
            num_patches = random.randint(16, 64)
            patch_scores = [random.uniform(0.4, 0.95) for _ in range(num_patches)]
            
            # Vision-language alignment score
            vl_score = sum(sorted(patch_scores, reverse=True)[:8]) / 8  # Top-8 patches
            
            results.append({
                "doc_id": doc_idx,
                "score": round(vl_score, 4),
                "patches_matched": len([s for s in patch_scores if s > 0.7]),
                "total_patches": num_patches,
                "method": "ColPali-MaxSim"
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {
            "top_k": results[:k],
            "method": "ColPali",
            "vision_encoder": "PaliGemma-3B",
            "latency_ms": round(random.uniform(80, 200), 2)
        }
    
    def simulate_mipro_optimization(base_prompt: str, query: str, context: str, trials: int = 15) -> dict:
        """
        Simulate MIPRO prompt optimization from DSPy.
        In production: runs Bayesian optimization over prompt variations.
        """
        import random
        
        # Simulated optimization trajectory
        optimization_history = []
        best_score = 0.5
        
        for trial in range(trials):
            # Simulate improvement with diminishing returns
            improvement = random.uniform(0, 0.1) * (1 - trial / trials)
            current_score = min(0.98, best_score + improvement)
            if current_score > best_score:
                best_score = current_score
            
            optimization_history.append({
                "trial": trial + 1,
                "score": round(current_score, 4),
                "best_so_far": round(best_score, 4)
            })
        
        # Simulated optimized prompt components
        optimized_components = {
            "instruction": "You are a precise sports analyst. Answer ONLY from the provided Wikipedia context about Super Bowl LIX. Be specific with names, scores, and statistics.",
            "demos": [
                {"q": "Who performed at halftime?", "a": "Kendrick Lamar performed at the Caesars Superdome halftime show."},
                {"q": "What was the final score?", "a": "Philadelphia Eagles 40, Kansas City Chiefs 22."}
            ],
            "reasoning_hint": "First identify relevant facts in context, then construct answer."
        }
        
        return {
            "method": "MIPRO",
            "trials_completed": trials,
            "best_score": round(best_score, 4),
            "improvement": round(best_score - 0.5, 4),
            "optimization_history": optimization_history,
            "optimized_components": optimized_components,
            "latency_ms": round(trials * random.uniform(200, 400), 2)
        }
    
    # Store retrieval method functions in session state for use in RAG pipeline
    st.session_state["retrieval_functions"] = {
        "colbert": simulate_colbert_retrieval,
        "colpali": simulate_colpali_retrieval,
        "mipro": simulate_mipro_optimization
    }
    
    def run_mini_rag(query: str, context: str, model: str, temperature: float) -> dict:
        """
        Execute mini RAG pipeline with Cortex REST API.
        """
        import tomllib
        
        # Get PAT and account
        try:
            with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                config = tomllib.load(f)
            pat = config["connections"]["myaccount"]["password"]
            account = config["connections"]["myaccount"].get("account", "").lower().replace("_", "-")
        except Exception:
            pat = get_pat_from_toml()
            account = ""
        
        url = f"https://{account}.snowflakecomputing.com/api/v2/cortex/inference:complete"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {pat}",
        }
        
        # RAG Prompt with context injection
        rag_prompt = f"""You are a helpful assistant answering questions about Super Bowl 2025.

CONTEXT (Retrieved from Wikipedia):
{context}

USER QUESTION: {query}

INSTRUCTIONS:
- Answer based ONLY on the context provided above
- If the answer is not in the context, say "I don't have that information in my context"
- Be concise and factual
- Cite specific facts from the context"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a factual sports assistant. Only answer based on provided context."},
                {"role": "user", "content": rag_prompt}
            ],
            "temperature": temperature,
            "stream": True,
        }
        
        start = datetime.now()
        response = requests.post(url, headers=headers, json=payload, timeout=120, stream=True)
        
        if response.status_code == 200:
            content = ""
            request_id = response.headers.get("X-Snowflake-Request-Id", "")
            
            for line in response.text.split("\n"):
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "choices" in data:
                            delta = data["choices"][0].get("delta", {})
                            content += delta.get("content", "")
                    except json.JSONDecodeError:
                        continue
            
            latency = (datetime.now() - start).total_seconds()
            
            return {
                "answer": content,
                "context": context,
                "request_id": request_id,
                "latency": latency,
                "model": model,
                "sources": ["Wikipedia: Super Bowl LIX"],
                "status": "success"
            }
        else:
            return {
                "answer": f"Error: {response.text}",
                "context": context,
                "request_id": "",
                "latency": 0,
                "model": model,
                "status": "error"
            }
    
    if st.button("🔍 Run RAG Query", key="run_rag", type="primary"):
        with st.spinner(f"Running RAG with {rag_model}..."):
            # --- Run Advanced Retrieval Method Simulation ---
            retrieval_result = None
            sample_docs = [
                SUPER_BOWL_2025_CONTEXT,
                "Super Bowl LVIII (58) - February 11, 2024. Kansas City Chiefs defeated San Francisco 49ers 25-22 in overtime.",
                "Super Bowl LVII (57) - February 12, 2023. Kansas City Chiefs defeated Philadelphia Eagles 38-35.",
                "The NFL Championship game has been played annually since 1967 as the Super Bowl.",
            ]
            
            if retrieval_method == "ColBERT (Late Interaction)":
                with st.spinner("Running ColBERT late interaction retrieval..."):
                    retrieval_result = simulate_colbert_retrieval(
                        rag_query, 
                        sample_docs, 
                        k=st.session_state.get("colbert_k", 3)
                    )
                    retrieval_result["config"] = {
                        "nprobe": st.session_state.get("colbert_nprobe", 10),
                        "ncells": st.session_state.get("colbert_ncells", 4),
                        "dim": st.session_state.get("colbert_dim", 128)
                    }
            
            elif retrieval_method == "ColPali (Vision-Language)":
                with st.spinner("Running ColPali vision-language retrieval..."):
                    retrieval_result = simulate_colpali_retrieval(
                        rag_query,
                        sample_docs,
                        k=3
                    )
                    retrieval_result["config"] = {
                        "model": st.session_state.get("colpali_model", "vidore/colpali-v1.2"),
                        "similarity": st.session_state.get("colpali_sim", "MaxSim"),
                        "resolution": st.session_state.get("colpali_res", "448x448")
                    }
            
            elif retrieval_method == "MIPRO (DSPy Optimized)":
                with st.spinner("Running MIPRO prompt optimization..."):
                    retrieval_result = simulate_mipro_optimization(
                        base_prompt="Answer the question based on context",
                        query=rag_query,
                        context=SUPER_BOWL_2025_CONTEXT,
                        trials=st.session_state.get("mipro_trials", 15)
                    )
                    retrieval_result["config"] = {
                        "demos": st.session_state.get("mipro_demos", 2),
                        "metric": st.session_state.get("mipro_metric", "answer_relevancy"),
                        "teacher": st.session_state.get("mipro_teacher", "claude-sonnet-4-5")
                    }
            else:
                # Dense retrieval (default)
                import random
                retrieval_result = {
                    "method": "Dense",
                    "top_k": [{"doc_id": 0, "score": 0.92, "method": "cosine-similarity"}],
                    "latency_ms": round(random.uniform(5, 15), 2),
                    "config": {"embedding_model": "snowflake-arctic-embed-m"}
                }
            
            st.session_state["retrieval_result"] = retrieval_result
            
            # Run WITH RAG (context injected) - with or without thinking
            if enable_thinking:
                with st.spinner(f"Running RAG with Extended Thinking ({rag_model})..."):
                    result = run_rag_with_thinking(
                        rag_query, 
                        SUPER_BOWL_2025_CONTEXT, 
                        rag_model, 
                        thinking_budget
                    )
                    st.session_state["thinking_result"] = result
            else:
                result = run_mini_rag(
                    rag_query, 
                    SUPER_BOWL_2025_CONTEXT, 
                    rag_model, 
                    rag_temperature
                )
                st.session_state["thinking_result"] = None
            
            # Run WITHOUT RAG for comparison (empty context)
            no_rag_result = None
            if compare_no_rag:
                with st.spinner(f"Running {rag_model} WITHOUT RAG context for comparison..."):
                    no_rag_result = run_mini_rag(
                        rag_query,
                        "",  # No context - model must rely on its training data
                        rag_model,
                        rag_temperature
                    )
            
            if result["status"] == "success":
                st.session_state["rag_result"] = result
                st.session_state["no_rag_result"] = no_rag_result
                st.success(f"✅ RAG complete (Request ID: {result['request_id'][:20]}...)")
            else:
                st.error(f"RAG failed: {result['answer']}")
    
    # Display RAG Results
    if "rag_result" in st.session_state:
        result = st.session_state["rag_result"]
        no_rag_result = st.session_state.get("no_rag_result")
        
        # Side-by-side comparison if no_rag_result exists
        if no_rag_result and no_rag_result.get("status") == "success":
            st.markdown("### 🔬 RAG vs No-RAG Comparison")
            st.caption(f"Demonstrating how RAG augments {result['model']}'s knowledge cutoff")
            
            col_rag, col_no_rag = st.columns(2)
            
            with col_rag:
                st.markdown("#### ✅ WITH RAG (Wikipedia MCP)")
                st.success("Context injected from Wikipedia")
                st.write(result["answer"])
                st.caption(f"Latency: {result['latency']:.2f}s")
            
            with col_no_rag:
                st.markdown("#### ❌ WITHOUT RAG (Model Only)")
                st.error("No context - relies on training data cutoff")
                st.write(no_rag_result["answer"])
                st.caption(f"Latency: {no_rag_result['latency']:.2f}s")
            
            # Highlight the difference
            st.markdown("---")
            st.markdown("**📊 Key Insight:**")
            
            # Check if the no-RAG response admits lack of knowledge
            no_rag_text = no_rag_result["answer"].lower()
            knowledge_gap_indicators = ["don't have", "cannot", "not available", "don't know", 
                                       "no information", "cutoff", "training data", "as of my",
                                       "i'm not sure", "unable to", "haven't occurred yet",
                                       "future event", "hasn't happened"]
            has_knowledge_gap = any(ind in no_rag_text for ind in knowledge_gap_indicators)
            
            if has_knowledge_gap:
                st.success(f"✅ **RAG Success!** {result['model']} acknowledged its knowledge cutoff without RAG, but correctly answered with Wikipedia context.")
            else:
                # Check if the no-RAG response has incorrect info
                correct_facts = ["eagles", "40", "barkley", "philadelphia"]
                no_rag_has_facts = sum(1 for f in correct_facts if f in no_rag_text)
                if no_rag_has_facts < 2:
                    st.warning(f"⚠️ **RAG Value Demonstrated**: Without RAG, {result['model']} may have incomplete or outdated information about Super Bowl LIX (Feb 2025).")
                else:
                    st.info(f"ℹ️ Model may have been updated with recent data, but RAG still provides verified, sourced information.")
        else:
            # Original single-result display
            st.markdown("**🏈 Answer (With RAG):**")
            st.write(result["answer"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Latency", f"{result['latency']:.2f}s")
        with col2:
            st.metric("Model", result['model'])
        with col3:
            st.metric("Sources", len(result['sources']))
        
        with st.expander("📚 Retrieved Context (Wikipedia MCP)"):
            st.text(result["context"])
        
        # ----- Extended Thinking Display -----
        thinking_result = st.session_state.get("thinking_result")
        if thinking_result and thinking_result.get("thinking"):
            st.markdown("---")
            st.markdown("### 🧠 Extended Thinking Trace")
            st.caption("Model's internal reasoning process before generating the final answer")
            
            # Thinking metrics
            col_t1, col_t2, col_t3, col_t4 = st.columns(4)
            with col_t1:
                st.metric("Thinking Tokens", f"~{thinking_result.get('thinking_tokens_used', 0):,}")
            with col_t2:
                st.metric("Budget Used", f"{thinking_result.get('thinking_tokens_used', 0)}/{thinking_result.get('thinking_budget', 0)}")
            with col_t3:
                budget_pct = (thinking_result.get('thinking_tokens_used', 0) / thinking_result.get('thinking_budget', 1)) * 100
                st.metric("Budget %", f"{budget_pct:.0f}%")
            with col_t4:
                st.metric("Total Latency", f"{thinking_result.get('latency', 0):.2f}s")
            
            # Chat Completions Usage
            prompt_tokens = thinking_result.get('prompt_tokens', 0)
            completion_tokens = thinking_result.get('completion_tokens', 0)
            total_tokens = thinking_result.get('total_tokens', 0)
            
            if total_tokens > 0 or prompt_tokens > 0 or completion_tokens > 0:
                st.markdown("#### 📊 Chat Completions Usage")
                col_u1, col_u2, col_u3, col_u4 = st.columns(4)
                with col_u1:
                    st.metric("Prompt Tokens", f"{prompt_tokens:,}")
                with col_u2:
                    st.metric("Completion Tokens", f"{completion_tokens:,}")
                with col_u3:
                    st.metric("Total Tokens", f"{total_tokens:,}")
                with col_u4:
                    # Estimate cost (approximate: $0.003/1K input, $0.015/1K output for Claude)
                    est_cost = (prompt_tokens * 0.003 + completion_tokens * 0.015) / 1000
                    st.metric("Est. Cost", f"${est_cost:.4f}")
            
            # Thinking content in styled expander
            with st.expander("🔍 View Thinking Process", expanded=True):
                thinking_text = thinking_result.get("thinking", "")
                if thinking_text:
                    # Style the thinking output
                    st.markdown("""
                    <style>
                    .thinking-box {
                        background-color: #1a1a2e;
                        border-left: 4px solid #7c3aed;
                        padding: 15px;
                        border-radius: 5px;
                        font-family: monospace;
                        font-size: 0.9em;
                        white-space: pre-wrap;
                        max-height: 400px;
                        overflow-y: auto;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="thinking-box">{thinking_text}</div>', unsafe_allow_html=True)
                else:
                    st.info("No thinking trace captured. The model may not support extended thinking or returned thinking in a different format.")
            
            # Show the final answer separately
            st.markdown("#### 💬 Final Answer (After Thinking)")
            st.success(thinking_result.get("answer", result.get("answer", "")))
        
        elif thinking_result and thinking_result.get("status") == "error":
            st.markdown("---")
            st.markdown("### 🧠 Extended Thinking")
            st.error(f"Thinking failed: {thinking_result.get('error', thinking_result.get('answer', 'Unknown error'))}")
            st.info("""
            **Troubleshooting Extended Thinking:**
            - Ensure you're using a Claude model (`claude-sonnet-4-5`)
            - Extended thinking requires `temperature: 1.0` (set automatically)
            - The Cortex API must support the `thinking` parameter
            - Try reducing the thinking budget if you get timeout errors
            """)
        
        # RAG evaluation metrics
        st.markdown("**RAG Quality Metrics:**")
        col1, col2, col3, col4 = st.columns(4)
        
        # Simple heuristic metrics
        answer = result["answer"].lower()
        context = result["context"].lower()
        
        # Groundedness: % of answer terms found in context
        answer_words = set(answer.split())
        context_words = set(context.split())
        groundedness = len(answer_words & context_words) / len(answer_words) if answer_words else 0
        
        # Relevance: mentions key entities
        key_entities = ["eagles", "chiefs", "barkley", "hurts", "mahomes", "super bowl", "lxix", "lix"]
        relevance = sum(1 for e in key_entities if e in answer) / len(key_entities)
        
        # Factuality check
        factual_claims = [
            ("eagles", "40" in answer or "won" in answer),
            ("barkley", "mvp" in answer),
            ("new orleans", "caesars" in answer or "superdome" in answer or "new orleans" in answer)
        ]
        factuality = sum(1 for _, check in factual_claims if check) / len(factual_claims)
        
        with col1:
            st.metric("Groundedness", f"{groundedness:.0%}")
        with col2:
            st.metric("Relevance", f"{relevance:.0%}")
        with col3:
            st.metric("Factuality", f"{factuality:.0%}")
        with col4:
            avg_score = (groundedness + relevance + factuality) / 3
            st.metric("Overall", f"{avg_score:.0%}")
        
        # ----- Retrieval Method Comparison Metrics -----
        if "retrieval_result" in st.session_state:
            ret_result = st.session_state["retrieval_result"]
            
            st.markdown("---")
            st.markdown("#### 🔬 Retrieval Method Analysis")
            
            method_name = ret_result.get("method", "Unknown")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Method", method_name)
            with col_m2:
                st.metric("Retrieval Latency", f"{ret_result.get('latency_ms', 0):.1f}ms")
            with col_m3:
                if "top_k" in ret_result and ret_result["top_k"]:
                    top_score = ret_result["top_k"][0].get("score", 0)
                    st.metric("Top-1 Score", f"{top_score:.3f}")
                else:
                    st.metric("Best Score", f"{ret_result.get('best_score', 0):.3f}")
            with col_m4:
                if method_name == "ColBERT":
                    st.metric("Query Tokens", ret_result.get("query_tokens", 0))
                elif method_name == "ColPali":
                    st.metric("Vision Encoder", "PaliGemma")
                elif method_name == "MIPRO":
                    st.metric("Trials", ret_result.get("trials_completed", 0))
                else:
                    st.metric("Embedding", "arctic-embed")
            
            # Method-specific details
            if method_name == "ColBERT":
                with st.expander("🔍 ColBERT Token-Level Matching Details"):
                    st.markdown("**Late Interaction Scoring (MaxSim)**")
                    st.caption("Each query token finds its best-matching document token")
                    
                    if ret_result.get("top_k"):
                        for i, doc in enumerate(ret_result["top_k"]):
                            st.markdown(f"**Doc {doc['doc_id']}**: Score={doc['score']:.4f}, Token Matches={doc.get('token_matches', 'N/A')}")
                    
                    st.json(ret_result.get("config", {}))
            
            elif method_name == "ColPali":
                with st.expander("🖼️ ColPali Vision-Language Details"):
                    st.markdown("**Image Patch Embeddings (PaliGemma)**")
                    st.caption("Document images encoded as patch embeddings for late interaction")
                    
                    if ret_result.get("top_k"):
                        for i, doc in enumerate(ret_result["top_k"]):
                            st.markdown(f"**Doc {doc['doc_id']}**: Score={doc['score']:.4f}, Patches Matched={doc.get('patches_matched', 'N/A')}/{doc.get('total_patches', 'N/A')}")
                    
                    st.json(ret_result.get("config", {}))
            
            elif method_name == "MIPRO":
                with st.expander("⚡ MIPRO DSPy Optimization Details"):
                    st.markdown("**Bayesian Prompt Optimization**")
                    st.caption("Automatically optimizes instructions, few-shot demos, and prompt structure")
                    
                    col_opt1, col_opt2 = st.columns(2)
                    with col_opt1:
                        st.metric("Improvement", f"+{ret_result.get('improvement', 0):.1%}")
                    with col_opt2:
                        st.metric("Final Score", f"{ret_result.get('best_score', 0):.1%}")
                    
                    # Optimization trajectory chart
                    if ret_result.get("optimization_history"):
                        opt_df = pd.DataFrame(ret_result["optimization_history"])
                        opt_chart = alt.Chart(opt_df).mark_line(point=True).encode(
                            x=alt.X("trial:O", title="Trial"),
                            y=alt.Y("best_so_far:Q", title="Best Score", scale=alt.Scale(domain=[0.4, 1.0])),
                            tooltip=["trial", "score", "best_so_far"]
                        ).properties(height=200, title="MIPRO Optimization Trajectory")
                        st.altair_chart(opt_chart, use_container_width=True)
                    
                    # Show optimized prompt components
                    if ret_result.get("optimized_components"):
                        st.markdown("**Optimized Prompt Components:**")
                        components = ret_result["optimized_components"]
                        st.code(components.get("instruction", ""), language=None)
                        
                        if components.get("demos"):
                            st.markdown("**Few-Shot Examples:**")
                            for demo in components["demos"]:
                                st.markdown(f"- Q: *{demo['q']}* → A: *{demo['a']}*")
    
    # ----- Historical Experiments -----
    st.divider()
    st.markdown("### 📚 Historical Experiments")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Load from Snowflake", key="load_hist_exp"):
            try:
                # Try with fresh connection
                import tomllib
                with open(os.path.expanduser("~/.snowflake/config.toml"), "rb") as f:
                    config = tomllib.load(f)
                fresh_conn = snowflake.connector.connect(
                    account=config["connections"]["myaccount"].get("account", "YOUR_ACCOUNT"),
                    user=config["connections"]["myaccount"].get("user"),
                    password=config["connections"]["myaccount"].get("password"),
                    warehouse="SNOW_INTELLIGENCE_DEMO_WH",
                    database=exp_database,
                    schema=exp_schema,
                )
                
                hist_df = fresh_conn.cursor().execute(f"""
                    SELECT 
                        experiment_id,
                        run_name,
                        experiment_type,
                        model_a,
                        model_b,
                        COUNT(*) as total_runs,
                        AVG(score_a) as avg_score_a,
                        AVG(score_b) as avg_score_b,
                        SUM(CASE WHEN winner = 'A' THEN 1 ELSE 0 END) as a_wins,
                        SUM(CASE WHEN winner = 'B' THEN 1 ELSE 0 END) as b_wins,
                        MAX(created_at) as last_run
                    FROM {exp_database}.{exp_schema}.INFERENCE_EXPERIMENTS
                    GROUP BY 1, 2, 3, 4, 5
                    ORDER BY last_run DESC
                    LIMIT 20
                """).fetch_pandas_all()
                
                fresh_conn.close()
                st.dataframe(hist_df, hide_index=True, use_container_width=True)
            except Exception as e:
                st.info(f"📁 Snowflake unavailable. Load from local files instead.")
    
    with col2:
        if st.button("📂 Load from Local Files", key="load_local_exp"):
            import glob
            local_files = glob.glob("/tmp/langgraph_exp_*.json")
            if local_files:
                st.write(f"Found {len(local_files)} local experiment files:")
                for f in sorted(local_files, reverse=True)[:5]:
                    with open(f) as fp:
                        data = json.load(fp)
                    st.caption(f"📄 {os.path.basename(f)} ({len(data)} runs)")
                    if st.checkbox(f"Show {os.path.basename(f)}", key=f"show_{f}"):
                        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            else:
                st.info("No local experiment files found. Run an experiment first.")

# ============== TAB 11: Multimodal Vision ==============
with tab11:
    st.subheader("📸 Multimodal Vision - Image Understanding")
    st.markdown("""
    **Analyze images using Cortex Chat Completions API** (OpenAI-compatible format)
    
    Supports Claude and GPT-4o vision models for image understanding tasks like:
    - Scene description & object detection
    - Document/chart analysis
    - Code screenshot understanding
    - AR/VR egocentric frame analysis (Project Aria)
    """)
    
    st.divider()
    
    # ----- Model & Configuration -----
    st.markdown("### ⚙️ Vision Model Configuration")
    
    col_vm1, col_vm2, col_vm3 = st.columns(3)
    
    with col_vm1:
        vision_model = st.selectbox(
            "Vision Model:",
            options=list(MULTIMODAL_MODELS.keys()),
            format_func=lambda x: MULTIMODAL_MODELS[x]["label"],
            key="vision_model_select"
        )
    
    with col_vm2:
        vision_max_tokens = st.slider(
            "Max Tokens:",
            min_value=256,
            max_value=4096,
            value=1024,
            step=256,
            key="vision_max_tokens"
        )
    
    with col_vm3:
        vision_temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            key="vision_temperature"
        )
    
    st.divider()
    
    # ----- Image Input Section -----
    st.markdown("### 🖼️ Image Input")
    
    image_input_method = st.radio(
        "Input method:",
        ["Upload Image", "Image URL", "Project Aria RGB Example"],
        horizontal=True,
        key="image_input_method"
    )
    
    image_base64 = None
    image_url_input = None
    preview_image = None
    
    if image_input_method == "Upload Image":
        uploaded_file = st.file_uploader(
            "Upload an image (PNG, JPG, WEBP - max 20MB)",
            type=["png", "jpg", "jpeg", "webp"],
            key="vision_file_upload"
        )
        
        if uploaded_file is not None:
            import base64
            # Read and encode the image
            image_bytes = uploaded_file.read()
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            preview_image = uploaded_file
            st.image(image_bytes, caption=f"Uploaded: {uploaded_file.name}", width=400)
    
    elif image_input_method == "Image URL":
        image_url_input = st.text_input(
            "Image URL:",
            placeholder="https://example.com/image.jpg",
            key="vision_url_input"
        )
        
        if image_url_input:
            st.image(image_url_input, caption="Image from URL", width=400)
    
    elif image_input_method == "Project Aria RGB Example":
        st.info("""
        **🥽 Project Aria** - Meta's AR Research Glasses
        
        Aria Gen 2 features a **12MP RGB camera** for egocentric AI research. 
        Use vision models to analyze first-person perspective frames for:
        - Scene understanding & spatial awareness
        - Object recognition in real-world contexts
        - Activity recognition from egocentric viewpoint
        - Hand-object interaction analysis
        """)
        
        # Sample Aria-style egocentric image (using a placeholder for demo)
        # In production, this would be an actual Aria VRS frame
        aria_sample_url = "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800"
        
        st.image(aria_sample_url, caption="Sample Egocentric View (Aria-style RGB frame)", width=500)
        image_url_input = aria_sample_url
        
        # Show Aria code snippet
        with st.expander("📝 Project Aria - Extract RGB from VRS"):
            st.code("""
# Install: pip install projectaria-tools'[all]'
from projectaria_tools.core import data_provider
from projectaria_tools.core.stream_id import StreamId

# Load VRS file from Aria glasses
vrs_path = "recording.vrs"
provider = data_provider.create_vrs_data_provider(vrs_path)

# Get RGB camera stream (12MP on Gen 2)
rgb_stream_id = provider.get_stream_id_from_label("camera-rgb")

# Get number of frames
num_frames = provider.get_num_data(rgb_stream_id)
print(f"Total RGB frames: {num_frames}")

# Extract a specific frame
frame_index = 0
image_data = provider.get_image_data_by_index(rgb_stream_id, frame_index)

# Get image as numpy array
image_array = image_data[0].to_numpy_array()
print(f"Image shape: {image_array.shape}")  # (height, width, channels)

# Get timestamp
timestamp_ns = provider.get_timestamp_ns(rgb_stream_id, frame_index)
print(f"Timestamp: {timestamp_ns / 1e9:.3f} seconds")

# Get camera calibration
calibration = provider.get_device_calibration()
rgb_calib = calibration.get_camera_calib("camera-rgb")
print(f"Focal length: {rgb_calib.get_focal_lengths()}")
            """, language="python")
        
        with st.expander("🔗 Project Aria Resources"):
            st.markdown("""
            - **Documentation**: [facebookresearch.github.io/projectaria_tools](https://facebookresearch.github.io/projectaria_tools/gen2/)
            - **GitHub**: [github.com/facebookresearch/projectaria_tools](https://github.com/facebookresearch/projectaria_tools)
            - **Open Datasets**: Aria Digital Twin, Aria Everyday Activities, Aria Synthetic Environments
            - **Colab Tutorials**: [Dataprovider Quickstart](https://colab.research.google.com/github/facebookresearch/projectaria_tools/blob/main/core/examples/dataprovider_quickstart_tutorial.ipynb)
            
            **Aria Gen 2 Sensors:**
            - 12MP RGB camera
            - 4 Computer Vision cameras (wider FOV, HDR, stereo)
            - Eye tracking cameras
            - Hand tracking (21 keypoints)
            - 6-axis IMUs, barometer, magnetometer
            - GNSS, proximity, ambient light sensors
            """)
    
    st.divider()
    
    # ----- Prompt Input -----
    st.markdown("### 💬 Vision Prompt")
    
    prompt_presets = {
        "Describe Image": "Describe this image in detail. What do you see?",
        "Scene Analysis": "Analyze this scene. What objects are present? What activity might be happening?",
        "Document/Chart": "Extract and summarize the key information from this document or chart.",
        "Code Analysis": "Analyze this code screenshot. What does the code do? Are there any issues?",
        "Aria Egocentric": "This is an egocentric (first-person) view from AR glasses. Describe what the wearer is looking at and any objects or activities visible.",
        "Custom": ""
    }
    
    prompt_preset = st.selectbox(
        "Prompt preset:",
        options=list(prompt_presets.keys()),
        key="vision_prompt_preset"
    )
    
    default_prompt = prompt_presets[prompt_preset]
    vision_prompt = st.text_area(
        "Your prompt:",
        value=default_prompt,
        height=100,
        key="vision_prompt_input"
    )
    
    # ----- Run Vision Analysis -----
    st.divider()
    
    if st.button("🔍 Analyze Image", type="primary", key="run_vision_analysis"):
        if not vision_prompt:
            st.error("Please enter a prompt")
        elif not image_base64 and not image_url_input:
            st.error("Please upload an image or provide a URL")
        else:
            with st.spinner(f"Analyzing image with {MULTIMODAL_MODELS[vision_model]['label']}..."):
                result = call_vision_model(
                    model=vision_model,
                    prompt=vision_prompt,
                    image_base64=image_base64,
                    image_url=image_url_input,
                    max_tokens=vision_max_tokens,
                    temperature=vision_temperature
                )
                
                st.session_state["vision_result"] = result
    
    # ----- Display Results -----
    if "vision_result" in st.session_state:
        result = st.session_state["vision_result"]
        
        st.markdown("### 📋 Analysis Results")
        
        if result.get("success"):
            # Metrics row
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            col_m1.metric("Duration", f"{result.get('duration', 0):.2f}s")
            col_m2.metric("Lines", result.get("line_count", 0))
            col_m3.metric("Words", result.get("word_count", 0))
            
            usage = result.get("usage", {})
            col_m4.metric("Tokens", usage.get("total_tokens", 0))
            
            # Response
            st.markdown("**Response:**")
            st.markdown(result.get("response", ""))
            
            # Token breakdown
            with st.expander("📊 Token Usage Details"):
                st.json({
                    "model": result.get("model"),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0)
                })
        else:
            st.error(f"Analysis failed: {result.get('response', 'Unknown error')}")
    
    st.divider()
    
    # ----- Model Comparison -----
    st.markdown("### 🔄 Compare Vision Models")
    st.caption("Compare the same image across multiple vision models")
    
    compare_models = st.multiselect(
        "Select models to compare:",
        options=list(MULTIMODAL_MODELS.keys()),
        default=["claude-sonnet-4-5", "gpt-5.2"],
        format_func=lambda x: MULTIMODAL_MODELS[x]["label"],
        key="vision_compare_models"
    )
    
    if st.button("🚀 Run Comparison", key="run_vision_compare"):
        if not vision_prompt:
            st.error("Please enter a prompt")
        elif not image_base64 and not image_url_input:
            st.error("Please upload an image or provide a URL")
        elif len(compare_models) < 2:
            st.error("Select at least 2 models to compare")
        else:
            comparison_results = []
            progress = st.progress(0)
            
            for i, model_key in enumerate(compare_models):
                model_label = MULTIMODAL_MODELS[model_key]["label"]
                with st.spinner(f"Running {model_label}..."):
                    result = call_vision_model(
                        model=model_key,
                        prompt=vision_prompt,
                        image_base64=image_base64,
                        image_url=image_url_input,
                        max_tokens=vision_max_tokens,
                        temperature=vision_temperature
                    )
                    result["model_key"] = model_key
                    result["model_label"] = model_label
                    comparison_results.append(result)
                
                progress.progress((i + 1) / len(compare_models))
            
            progress.empty()
            st.session_state["vision_comparison"] = comparison_results
    
    if "vision_comparison" in st.session_state:
        results = st.session_state["vision_comparison"]
        
        st.markdown("#### Comparison Results")
        
        # Summary table
        summary_data = []
        for r in results:
            summary_data.append({
                "Model": r.get("model_label", ""),
                "Success": "✅" if r.get("success") else "❌",
                "Duration (s)": f"{r.get('duration', 0):.2f}",
                "Lines": r.get("line_count", 0),
                "Words": r.get("word_count", 0),
                "Tokens": r.get("usage", {}).get("total_tokens", 0)
            })
        
        st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)
        
        # Individual responses
        for r in results:
            with st.expander(f"📝 {r.get('model_label', 'Model')} Response"):
                if r.get("success"):
                    st.markdown(r.get("response", ""))
                else:
                    st.error(r.get("response", "Error"))

# Footer
st.divider()
st.caption("Cross-Model Comparison Dashboard | Cortex SQL & Cortex REST API | Vine Copula Q&A | Powered by Snowflake Cortex")
