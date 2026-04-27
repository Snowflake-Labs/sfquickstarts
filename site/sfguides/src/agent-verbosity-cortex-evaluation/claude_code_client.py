"""
Claude Code Onboarding - Client App
====================================
Self-service app for users to track their onboarding progress and test Claude Code.

Run: streamlit run claude_code_client.py --server.port 8522
Test mode: ONBOARDING_TEST_MODE=1 streamlit run claude_code_client.py --server.port 8522
"""

import streamlit as st
import os
import sys
import json
import subprocess
import shutil
from datetime import datetime
import tomllib

# ============== Configuration ==============

# Test mode detection
TEST_MODE = "--test-mode" in sys.argv or os.environ.get("ONBOARDING_TEST_MODE") == "1"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "onboarding.db")
MOCK_DATA_PATH = os.path.join(BASE_DIR, "test_data")
MOCK_USERS_FILE = os.path.join(MOCK_DATA_PATH, "mock_users.json")
MOCK_PROGRESS_FILE = os.path.join(MOCK_DATA_PATH, "mock_progress.json")
MOCK_ACTIVITY_FILE = os.path.join(MOCK_DATA_PATH, "mock_activity.json")

# Claude Code configuration
CLAUDE_CODE_CONFIG = {
    "endpoint": "https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/anthropic",
    "models": {
        "sonnet45": "claude-sonnet-4-5",
        "sonnet46": "claude-sonnet-4-6",
        "opus45": "claude-opus-4-5",
        "haiku45": "claude-haiku-4-5",
    },
    "default_model": "claude-sonnet-4-5"
}

ONBOARDING_STEPS = [
    {"id": "cli_installed", "name": "Claude Code CLI Installed", "description": "npm install -g @anthropic-ai/claude-code"},
    {"id": "pat_created", "name": "PAT Token Created", "description": "Personal Access Token generated"},
    {"id": "network_policy", "name": "Network Policy Applied", "description": "IP allowlisted in Snowflake"},
    {"id": "settings_configured", "name": "Settings Configured", "description": "settings.json with Cortex endpoint"},
    {"id": "test_successful", "name": "Test Run Successful", "description": "Successfully ran Claude Code agent"},
]

# ============== Helper Functions ==============

def get_pat_from_toml(connection_name: str = "myaccount") -> str:
    """Read PAT token from ~/.snowflake/config.toml"""
    toml_path = os.path.expanduser("~/.snowflake/config.toml")
    try:
        with open(toml_path, "rb") as f:
            config = tomllib.load(f)
        if "connections" in config and connection_name in config["connections"]:
            return config["connections"][connection_name].get("password", "")
    except Exception:
        pass
    return ""

def check_claude_cli_installed() -> tuple[bool, str]:
    """Check if Claude Code CLI is installed."""
    claude_path = shutil.which("claude")
    if claude_path:
        try:
            result = subprocess.run([claude_path, "--version"], capture_output=True, text=True, timeout=10)
            version = result.stdout.strip() or result.stderr.strip() or "unknown"
            return True, f"Installed at {claude_path} (version: {version})"
        except Exception as e:
            return True, f"Installed at {claude_path}"
    return False, "Not found in PATH"

def run_claude_code_agent(prompt: str, model: str = None, pat_token: str = None, timeout: int = 120) -> dict:
    """Run Claude via Cortex REST API (Anthropic-compatible endpoint)."""
    import requests
    
    start_time = datetime.now()
    model = model or CLAUDE_CODE_CONFIG["default_model"]
    
    if not pat_token:
        return {
            "response": "PAT token is required",
            "success": False,
            "duration": 0,
            "error": "No PAT token"
        }
    
    url = f"{CLAUDE_CODE_CONFIG['endpoint']}/v1/messages"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pat_token}",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.json()
            # Extract text from response
            content = data.get("content", [])
            response_text = ""
            for block in content:
                if block.get("type") == "text":
                    response_text += block.get("text", "")
            
            return {
                "response": response_text,
                "success": True,
                "duration": duration,
                "model": model,
                "line_count": len(response_text.split('\n')),
                "word_count": len(response_text.split()),
                "usage": data.get("usage", {})
            }
        else:
            return {
                "response": response.text,
                "success": False,
                "duration": duration,
                "error": f"HTTP {response.status_code}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "response": f"Request timed out after {timeout} seconds",
            "success": False,
            "duration": timeout,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "response": str(e),
            "success": False,
            "duration": (datetime.now() - start_time).total_seconds(),
            "error": str(e)
        }

# ============== Mock Data Functions ==============

def load_mock_users():
    if os.path.exists(MOCK_USERS_FILE):
        with open(MOCK_USERS_FILE) as f:
            return json.load(f)
    return []

def load_mock_progress():
    if os.path.exists(MOCK_PROGRESS_FILE):
        with open(MOCK_PROGRESS_FILE) as f:
            return json.load(f)
    return []

def save_mock_progress(progress):
    with open(MOCK_PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def load_mock_activity():
    if os.path.exists(MOCK_ACTIVITY_FILE):
        with open(MOCK_ACTIVITY_FILE) as f:
            return json.load(f)
    return []

def save_mock_activity(activity):
    with open(MOCK_ACTIVITY_FILE, "w") as f:
        json.dump(activity, f, indent=2)

def mock_get_user_by_email(email: str):
    users = load_mock_users()
    for user in users:
        if user["email"].lower() == email.lower():
            return user
    return None

def mock_get_user_progress(user_id: int):
    progress = load_mock_progress()
    return [p for p in progress if p["user_id"] == user_id]

def mock_update_user_step(user_id: int, step_name: str, completed: bool, details: str = None):
    progress = load_mock_progress()
    activity = load_mock_activity()
    
    for p in progress:
        if p["user_id"] == user_id and p["step_name"] == step_name:
            p["completed"] = completed
            p["completed_at"] = datetime.now().isoformat() if completed else None
            p["details"] = details
            break
    
    activity.append({
        "user_id": user_id,
        "step_name": step_name,
        "action": "completed" if completed else "uncompleted",
        "timestamp": datetime.now().isoformat(),
        "details": details
    })
    
    save_mock_progress(progress)
    save_mock_activity(activity)

# ============== Database Functions ==============

def get_db_connection():
    import sqlite3
    return sqlite3.connect(DB_PATH)

def db_get_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "email": row[1],
            "snowflake_account": row[2],
            "snowflake_url": row[3],
            "role": row[4],
            "created_at": row[5]
        }
    return None

def db_get_user_progress(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT step_name, completed, completed_at, details 
        FROM onboarding_progress WHERE user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"step_name": r[0], "completed": bool(r[1]), "completed_at": r[2], "details": r[3]} for r in rows]

def db_update_user_step(user_id: int, step_name: str, completed: bool, details: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE onboarding_progress 
        SET completed = ?, completed_at = ?, details = ?
        WHERE user_id = ? AND step_name = ?
    """, (completed, datetime.now().isoformat() if completed else None, details, user_id, step_name))
    
    cursor.execute("""
        INSERT INTO activity_log (user_id, step_name, action, details)
        VALUES (?, ?, ?, ?)
    """, (user_id, step_name, "completed" if completed else "uncompleted", details))
    
    conn.commit()
    conn.close()

# ============== Function Routing ==============

if TEST_MODE:
    get_user_by_email = mock_get_user_by_email
    get_user_progress = mock_get_user_progress
    update_user_step = mock_update_user_step
else:
    get_user_by_email = db_get_user_by_email
    get_user_progress = db_get_user_progress
    update_user_step = db_update_user_step

# ============== Streamlit App ==============

st.set_page_config(
    page_title="Claude Code - Client Portal",
    page_icon="🤖",
    layout="wide"
)

# Header
mode_badge = "🧪 TEST MODE" if TEST_MODE else ""
st.title(f"🤖 Claude Code Onboarding {mode_badge}")
st.markdown("Complete your onboarding steps and test Claude Code with Snowflake Cortex")

st.divider()

# Session state for user
if "user" not in st.session_state:
    st.session_state.user = None
if "user_progress" not in st.session_state:
    st.session_state.user_progress = []

# ============== User Login Section ==============

with st.container():
    st.subheader("1. Identify Yourself")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        email_input = st.text_input(
            "Enter your email address",
            placeholder="your.email@company.com",
            key="email_input"
        )
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        lookup_btn = st.button("Look Up", type="primary", use_container_width=True)
    
    if lookup_btn and email_input:
        user = get_user_by_email(email_input)
        if user:
            st.session_state.user = user
            st.session_state.user_progress = get_user_progress(user["id"])
            st.success(f"Welcome, {user['email']}!")
        else:
            st.error("Email not found. Please contact your administrator to be added to the system.")
            st.session_state.user = None
            st.session_state.user_progress = []

# ============== Main Content (only if logged in) ==============

if st.session_state.user:
    user = st.session_state.user
    
    st.divider()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 My Progress", "🧪 Run Claude Code Agent", "📚 Setup Guide"])
    
    # ============== Tab 1: My Progress ==============
    with tab1:
        st.subheader("Your Onboarding Progress")
        
        # Refresh progress
        if st.button("🔄 Refresh Progress"):
            st.session_state.user_progress = get_user_progress(user["id"])
            st.rerun()
        
        progress_data = st.session_state.user_progress
        completed_count = sum(1 for p in progress_data if p.get("completed", False))
        total_steps = len(ONBOARDING_STEPS)
        
        # Progress bar
        progress_pct = completed_count / total_steps if total_steps > 0 else 0
        st.progress(progress_pct, text=f"{completed_count}/{total_steps} steps completed ({progress_pct*100:.0f}%)")
        
        st.write("")
        
        # Step cards
        for i, step in enumerate(ONBOARDING_STEPS):
            step_progress = next((p for p in progress_data if p.get("step_name") == step["id"]), {})
            is_completed = step_progress.get("completed", False)
            completed_at = step_progress.get("completed_at", "")
            details = step_progress.get("details", "")
            
            with st.container():
                col1, col2, col3 = st.columns([0.5, 4, 2])
                
                with col1:
                    if is_completed:
                        st.markdown("### ✅")
                    else:
                        st.markdown("### ⬜")
                
                with col2:
                    st.markdown(f"**Step {i+1}: {step['name']}**")
                    st.caption(step["description"])
                    if completed_at:
                        st.caption(f"Completed: {completed_at}")
                    if details:
                        st.caption(f"Details: {details}")
                
                with col3:
                    if is_completed:
                        if st.button("Mark Incomplete", key=f"unmark_{step['id']}", type="secondary"):
                            update_user_step(user["id"], step["id"], False)
                            st.session_state.user_progress = get_user_progress(user["id"])
                            st.rerun()
                    else:
                        # Step-specific verification
                        if step["id"] == "cli_installed":
                            # User pastes CLI version
                            version_input = st.text_input(
                                "Paste `claude --version` output", 
                                placeholder="e.g., 1.0.17",
                                key=f"version_{step['id']}"
                            )
                            if st.button("✅ Verify CLI", key=f"verify_{step['id']}", type="primary", disabled=not version_input):
                                update_user_step(user["id"], step["id"], True, f"Version: {version_input}")
                                st.session_state.user_progress = get_user_progress(user["id"])
                                st.rerun()
                        
                        elif step["id"] == "pat_created":
                            # User pastes PAT, client calls server to register
                            pat_input = st.text_input(
                                "Paste your PAT token", 
                                type="password",
                                placeholder="pat_xxxxx...",
                                key=f"pat_{step['id']}"
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✅ Register PAT", key=f"verify_{step['id']}", type="primary", disabled=not pat_input):
                                    # Call server app to register PAT (server auto-applies network policy)
                                    try:
                                        import requests
                                        server_url = "http://localhost:8525/api/register_pat"
                                        resp = requests.post(server_url, json={
                                            "user_id": user["id"],
                                            "email": user["email"],
                                            "pat_token": pat_input
                                        }, timeout=30)
                                        result = resp.json()
                                        
                                        if resp.status_code == 200 and result.get("pat_success"):
                                            # PAT success - update local state
                                            update_user_step(user["id"], step["id"], True, "PAT registered with server")
                                            st.success("✅ PAT registered successfully!")
                                            
                                            # Check network policy result (auto-applied by server)
                                            if result.get("network_policy_success"):
                                                update_user_step(user["id"], "network_policy", True, "Network policy auto-applied")
                                                st.success("✅ Network policy auto-applied!")
                                            else:
                                                st.warning("⚠️ Network policy failed - contact admin")
                                            
                                            st.session_state.user_progress = get_user_progress(user["id"])
                                            st.rerun()
                                        else:
                                            # PAT failed - logged in activity by server
                                            st.error(f"❌ PAT registration failed: {result.get('error', 'Unknown error')}")
                                    except requests.exceptions.ConnectionError:
                                        st.error("Cannot connect to server API (port 8525). Is the server app running?")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            with col2:
                                if st.button("📝 Mark Completed Manually", key=f"manual_{step['id']}", type="secondary"):
                                    # Call API to register PAT (same as automatic flow)
                                    try:
                                        import requests
                                        server_url = "http://localhost:8525/api/register_pat"
                                        resp = requests.post(server_url, json={
                                            "user_id": user["id"],
                                            "email": user["email"],
                                            "pat_token": "manual_registration"
                                        }, timeout=30)
                                        result = resp.json()
                                        
                                        if resp.status_code == 200 and result.get("pat_success"):
                                            update_user_step(user["id"], step["id"], True, "PAT registered manually via API")
                                            st.success("✅ PAT registered!")
                                            if result.get("network_policy_success"):
                                                update_user_step(user["id"], "network_policy", True, "Network policy auto-applied")
                                                st.success("✅ Network policy auto-applied!")
                                            st.session_state.user_progress = get_user_progress(user["id"])
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Registration failed: {result.get('error', 'Unknown error')}")
                                    except requests.exceptions.ConnectionError:
                                        st.error("Cannot connect to server API (port 8525). Is the server app running?")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            # Show manual SQL command
                            with st.expander("📋 Manual PAT Registration (SQL)"):
                                username = user["email"].split("@")[0].upper()
                                st.code(f"""-- Run in Snowflake as ACCOUNTADMIN
ALTER USER {username} ADD_PAT my_pat;

-- Or create new PAT with expiry
ALTER USER {username} ADD_PAT my_pat 
  EXPIRY_DAYS = 90 
  COMMENT = 'Claude Code PAT';""", language="sql")
                                st.caption("After running SQL, click 'Mark Completed Manually' above")
                        
                        elif step["id"] == "network_policy":
                            # Network policy is managed by admin on server side
                            st.caption("Managed by admin after PAT registration.")
                            st.info("💡 Contact admin to complete in **User Management** tab at http://localhost:8521")
                        
                        elif step["id"] == "test_successful":
                            # Require latency input for test verification
                            latency_input = st.text_input(
                                "Response latency (s)", 
                                placeholder="e.g., 2.35",
                                key=f"latency_{step['id']}"
                            )
                            if st.button("✅ Verify Test", key=f"verify_{step['id']}", type="primary", disabled=not latency_input):
                                update_user_step(user["id"], step["id"], True, f"Latency: {latency_input}s")
                                st.session_state.user_progress = get_user_progress(user["id"])
                                st.rerun()
                        
                        else:
                            # Honor code for settings_configured
                            if st.button("Mark Complete", key=f"mark_{step['id']}", type="primary"):
                                update_user_step(user["id"], step["id"], True)
                                st.session_state.user_progress = get_user_progress(user["id"])
                                st.rerun()
                
                st.divider()
    
    # ============== Tab 2: Run Claude Code Agent ==============
    with tab2:
        st.subheader("🧪 Test Claude Code Agent")
        st.markdown("Run a test prompt to verify your Claude Code setup is working correctly.")
        
        # Check CLI status
        cli_installed, cli_info = check_claude_cli_installed()
        
        if cli_installed:
            st.success(f"✅ Claude Code CLI: {cli_info}")
        else:
            st.error(f"❌ Claude Code CLI: {cli_info}")
            st.code("npm install -g @anthropic-ai/claude-code", language="bash")
            st.stop()
        
        st.divider()
        
        # Configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Model Selection**")
            model_options = list(CLAUDE_CODE_CONFIG["models"].items())
            model_labels = {v: k for k, v in CLAUDE_CODE_CONFIG["models"].items()}
            selected_model = st.selectbox(
                "Select Model",
                options=[m[1] for m in model_options],
                format_func=lambda x: f"{x} ({model_labels.get(x, '')})",
                index=0
            )
        
        with col2:
            st.markdown("**Authentication**")
            pat_source = st.radio(
                "PAT Token Source",
                ["Auto-load from connections.toml", "Enter manually"],
                horizontal=True
            )
            
            if pat_source == "Auto-load from connections.toml":
                connection_name = st.text_input("Connection name", value="myaccount")
                pat_token = get_pat_from_toml(connection_name)
                if pat_token:
                    st.success(f"✅ PAT loaded from [{connection_name}]")
                else:
                    st.warning(f"⚠️ No PAT found for [{connection_name}]")
            else:
                pat_token = st.text_input("PAT Token", type="password")
        
        st.divider()
        
        # Prompt input
        st.markdown("**Test Prompt**")
        
        prompt_templates = {
            "Simple greeting": "Say hello and confirm you are working via Snowflake Cortex.",
            "Version check": "What model are you and what capabilities do you have?",
            "Simple task": "Write a Python function that calculates the factorial of a number.",
            "Custom": ""
        }
        
        template_choice = st.selectbox("Quick templates", list(prompt_templates.keys()))
        
        if template_choice == "Custom":
            prompt = st.text_area(
                "Enter your prompt",
                height=100,
                placeholder="Enter your test prompt here..."
            )
        else:
            prompt = st.text_area(
                "Enter your prompt",
                value=prompt_templates[template_choice],
                height=100
            )
        
        # Timeout setting
        timeout = st.slider("Timeout (seconds)", min_value=30, max_value=300, value=120)
        
        # Run button
        st.write("")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            run_button = st.button(
                "🚀 Run Claude Code Agent",
                type="primary",
                use_container_width=True,
                disabled=not prompt or not pat_token
            )
        
        if run_button:
            with st.spinner(f"Running Claude Code with {selected_model}..."):
                result = run_claude_code_agent(
                    prompt=prompt,
                    model=selected_model,
                    pat_token=pat_token,
                    timeout=timeout
                )
            
            st.divider()
            
            if result["success"]:
                st.success(f"✅ Success! Completed in {result['duration']:.2f}s")
                
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", f"{result['duration']:.2f}s")
                with col2:
                    st.metric("Lines", result.get("line_count", 0))
                with col3:
                    st.metric("Words", result.get("word_count", 0))
                
                # Response
                st.markdown("**Response:**")
                st.markdown(result["response"])
                
                # Auto-mark test step as complete
                st.divider()
                if st.button("✅ Mark 'Test Run Successful' as Complete", type="primary"):
                    update_user_step(user["id"], "test_successful", True, f"Tested with {selected_model}")
                    st.session_state.user_progress = get_user_progress(user["id"])
                    st.success("Step marked as complete!")
                    st.balloons()
            else:
                st.error(f"❌ Failed: {result.get('error', 'Unknown error')}")
                st.markdown("**Output:**")
                st.code(result["response"])
                
                # Troubleshooting tips
                with st.expander("🔧 Troubleshooting Tips"):
                    st.markdown("""
                    **Common issues:**
                    
                    1. **Network Policy**: Ensure your IP is allowlisted in Snowflake
                       ```sql
                       CREATE OR REPLACE NETWORK POLICY claude_code_policy
                       ALLOWED_IP_LIST = ('YOUR_IP_ADDRESS');
                       ```
                    
                    2. **PAT Token**: Verify your PAT token is valid and not expired
                    
                    3. **Endpoint**: Confirm the Cortex endpoint URL is correct
                       - Current: `{}`
                    
                    4. **Model Access**: Ensure you have access to the selected model
                    """.format(CLAUDE_CODE_CONFIG["endpoint"]))
    
    # ============== Tab 3: Setup Guide ==============
    with tab3:
        st.subheader("📚 Claude Code Setup Guide")
        
        st.markdown("""
        ### Step 1: Install Claude Code CLI
        
        ```bash
        npm install -g @anthropic-ai/claude-code
        ```
        
        Verify installation:
        ```bash
        claude --version
        ```
        
        ---
        
        ### Step 2: Generate PAT Token
        
        Follow the [Snowflake PAT Documentation](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) to generate a Personal Access Token.
        
        **Quick Steps:**
        1. Go to Snowflake UI → User Menu → Profile
        2. Under "Personal Access Tokens", click "Generate Token"
        3. Set expiration and permissions
        4. Copy the token and store it somewhere safe (you won't see it again!)
        
        Once generated, paste the PAT in the "My Progress" tab to register it with the server.
        
        **Server-side setup (run by admin):**
        ```sql
        USE ROLE SECURITYADMIN;
        ALTER USER <YOUR_USERNAME> ADD_PAT my_pat;
        
        -- Ensures models are accessible cross-region if needed
        USE ROLE ACCOUNTADMIN;
        ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
        ```
        
        ---
        
        ### Step 3: Network Policy Setup
        
        Your admin will configure the network policy to allow access to the Cortex API.
        
        **Server-side setup (run by admin):**
        ```sql
        -- Create network policy
        USE ROLE ACCOUNTADMIN;
        CREATE NETWORK POLICY all_ips
          ALLOWED_IP_LIST = ('0.0.0.0/0');
        
        -- Apply at account level
        USE ROLE ACCOUNTADMIN;
        ALTER ACCOUNT SET NETWORK_POLICY = all_ips;
        
        -- Or apply at user level (optional if account level set)
        ALTER USER <YOUR_USERNAME> SET NETWORK_POLICY = all_ips;
        ```
        
        Once configured, click "Apply Network Policy" in the "My Progress" tab to verify.
        
        ---
        
        ### Step 4: Configure Claude Code Settings
        
        Create `~/.claude-code/settings.json`:
        ```json
        {
            "apiProvider": "anthropic-compatible",
            "anthropicBaseUrl": "https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/anthropic",
            "defaultModel": "claude-sonnet-4-5"
        }
        ```
        
        ---
        
        ### Step 5: Test Your Setup
        
        Go to the "Run Claude Code Agent" tab and run a test prompt!
        
        Or test from command line:
        ```bash
        export ANTHROPIC_BASE_URL="https://YOUR_ACCOUNT.snowflakecomputing.com/api/v2/cortex/anthropic"
        export ANTHROPIC_AUTH_TOKEN="YOUR_PAT_TOKEN"
        claude -p "Hello, are you working?" --output-format text
        ```
        """)
        
        # Account info
        st.divider()
        st.markdown("### Your Account Info")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Snowflake Account", value=user.get("snowflake_account", ""), disabled=True)
        with col2:
            st.text_input("Snowflake URL", value=user.get("snowflake_url", ""), disabled=True)

else:
    # Not logged in - show info
    st.info("👆 Enter your email address above to view your onboarding progress and test Claude Code.")
    
    with st.expander("ℹ️ What is this?"):
        st.markdown("""
        This portal helps you complete the Claude Code onboarding process:
        
        1. **Install Claude Code CLI** - The command-line tool
        2. **Configure Network Policy** - Allow your IP in Snowflake
        3. **Generate PAT Token** - Personal Access Token for authentication
        4. **Configure Settings** - Point Claude Code to Cortex endpoint
        5. **Test Your Setup** - Run a test prompt to verify everything works
        
        Once you've completed all steps, you'll be able to use Claude Code with Snowflake Cortex!
        """)

# ============== Footer ==============
st.divider()
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("Claude Code Onboarding Client Portal")
    if TEST_MODE:
        st.caption("🧪 Running in TEST MODE")
