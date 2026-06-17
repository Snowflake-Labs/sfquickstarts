import streamlit as st
import requests
import json
import os
import re

# -----------------------------------------------------------------------------
# Streamlit app: Snowflake Agents API (SiS on Containers) with multi-turn chat
# - Auth via container session token (/snowflake/session/token)
# - Threads API to maintain conversation context
# - Agent invocation via SSE (text/event-stream) with message id tracking
# - Optional prompt reinforcement to improve multi-turn grounding
# -----------------------------------------------------------------------------

# Page configuration
st.set_page_config(
    page_title="Snowflake Agent Chat",
    page_icon="🏔️",
    layout="wide"
)

def get_token():
    """Read the oauth token from SPCS container
    
    In Snowflake SiS on Containers, the runtime provides an OAuth bearer token
    at /snowflake/session/token for calling Snowflake REST APIs.
    """
    try:
        return open("/snowflake/session/token", "r").read().strip()
    except FileNotFoundError:
        st.error("❌ Token file not found at /snowflake/session/token")
        return None

def get_snowflake_context():
    """Get current Snowflake session context
    
    Used for display in the sidebar and for composing the agent run URL path.
    """
    try:
        session = st.connection("snowflake").session()
        context = session.sql("""
            SELECT 
                CURRENT_DATABASE() as database,
                CURRENT_SCHEMA() as schema,
                CURRENT_WAREHOUSE() as warehouse,
                CURRENT_ROLE() as role,
                CURRENT_USER() as user_name
        """).collect()[0]
        
        env_info = {
            'snowflake_host': os.getenv('SNOWFLAKE_HOST'),
            'snowflake_account': os.getenv('SNOWFLAKE_ACCOUNT')
        }
        
        return context, env_info, True
        
    except Exception as e:
        st.error(f"❌ Error getting Snowflake context: {str(e)}")
        return None, None, False

def create_thread():
    """Create a new conversation thread
    
    Threads maintain multi-turn state on the server side. The returned
    thread_id is stored in Streamlit session_state.
    """
    host = os.getenv("SNOWFLAKE_HOST")
    token = get_token()
    
    if not token:
        return None
    
    url = f"https://{host}/api/v2/cortex/threads"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Snowflake-Authorization-Token-Type": "OAUTH"
    }
    
    request_body = {
        "origin_application": "docs_agent"
    }
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(request_body),
            timeout=30
        )
        
        if response.status_code == 200:
            thread_data = response.json()
            return thread_data
        else:
            st.error(f"❌ Failed to create thread: {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"❌ Error creating thread: {str(e)}")
        return None

def parse_sse_response(response_text):
    """Parse Server-Sent Events response to extract agent content
    
    Simple parser used when we receive entire SSE payload as text. Our main
    code path uses streaming (iter_lines), but we keep this as a fallback.
    """
    messages = []
    
    # Split by lines and process SSE format
    lines = response_text.strip().split('\n') if response_text else []
    current_data = ""
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and event lines
        if not line or line.startswith('event:'):
            continue
            
        # Process data lines
        if line.startswith('data: '):
            data_content = line[6:]  # Remove 'data: ' prefix
            
            # Skip metadata-only messages
            if '"role":"user"' in data_content or not data_content or data_content == '[DONE]':
                continue
                
            try:
                data_json = json.loads(data_content)
                
                # Extract content from assistant messages
                if data_json.get('role') == 'assistant':
                    content = data_json.get('content', [])
                    for item in content:
                        if item.get('type') == 'text':
                            text = item.get('text', '')
                            if text.strip():
                                messages.append(text)
                                
            except json.JSONDecodeError:
                # Sometimes the content is plain text
                if data_content.strip() and data_content != '[DONE]':
                    messages.append(data_content)
    
    return ' '.join(messages) if messages else None

def call_agent_with_thread(prompt, thread_data):
    """Call agent with existing thread and parse streaming response
    
    - Builds the agent run request with the active thread_id
    - Sends parent_message_id to preserve multi-turn linkage
    - Streams SSE and aggregates assistant text
    - Extracts and persists the latest message id into session_state
    """
    host = os.getenv("SNOWFLAKE_HOST")
    token = get_token()
    
    if not token:
        return None
    
    # Extract thread ID
    if isinstance(thread_data, dict):
        actual_thread_id = thread_data['thread_id']
    else:
        actual_thread_id = thread_data
    
    # Determine parent message id for multi-turn continuity
    parent_message_id = st.session_state.get('parent_message_id', 0) or 0
    # Ensure numeric where possible (API commonly expects integer ids)
    effective_parent_id = parent_message_id
    try:
        if isinstance(parent_message_id, str) and parent_message_id.isdigit():
            effective_parent_id = int(parent_message_id)
    except Exception:
        pass
    
    session = st.connection("snowflake").session()
    context = session.sql("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()").collect()[0]
    database, schema = context[0], context[1]
    
    url = f"https://{host}/api/v2/databases/{database}/schemas/{schema}/agents/SNOWFLAKE_DOCUMENTATION:run"
    
    headers = {
        "Content-Type": "application/json", 
        # Request server-sent events so we can stream and/or parse multi-part responses
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {token}",
        "X-Snowflake-Authorization-Token-Type": "OAUTH"
    }
    
    request_body = {
        "thread_id": actual_thread_id,
        "parent_message_id": effective_parent_id,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }
    
    try:
        with st.spinner("🤖 Agent is thinking..."):
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(request_body),
                timeout=60,
                stream=True
            )
        
        if response.status_code != 200:
            # Surface server error text to help debug
            try:
                error_text = response.text
            except Exception:
                error_text = ""
            st.error(f"❌ Agent call failed: {response.status_code}")
            if error_text:
                st.code(error_text)
            return None
        
        # Aggregate assistant text tokens from SSE
        aggregated_text = []
        last_message_id = None
        
        def try_extract_id(obj):
            # Heuristic: try common id locations
            # Some implementations include { message_id }, others flatten to { id },
            # and some nest under { message | data | event | payload }.
            if isinstance(obj, dict):
                for key in ["message_id", "id"]:
                    if key in obj and obj[key]:
                        return str(obj[key])
                # Nested common containers
                for key in ["message", "data", "event", "payload"]:
                    if key in obj and isinstance(obj[key], (dict, list)):
                        nested = try_extract_id(obj[key])
                        if nested:
                            return nested
            elif isinstance(obj, list):
                for item in obj:
                    nested = try_extract_id(item)
                    if nested:
                        return nested
            return None
        
        # Stream parsing for SSE: lines prefixed by "data: ..."
        for raw_line in response.iter_lines(decode_unicode=True):
            if not raw_line:
                continue
            line = raw_line.strip()
            if not line or line.startswith('event:'):
                continue
            if line.startswith('data:'):
                data_content = line[5:].strip()
                if not data_content or data_content == "[DONE]":
                    continue
                # Try JSON first, fall back to plain text
                try:
                    data_json = json.loads(data_content)
                    if isinstance(data_json, dict):
                        # Capture message id if present (ids may be strings)
                        extracted = try_extract_id(data_json)
                        if extracted:
                            last_message_id = extracted
                        
                        if data_json.get("role") == "assistant":
                            # Aggregate assistant textual chunks
                            for item in data_json.get("content", []):
                                if item.get("type") == "text":
                                    text_piece = item.get("text", "")
                                    if text_piece:
                                        aggregated_text.append(text_piece)
                        # Some server implementations may stream incremental chunks under choices/delta or similar
                        elif "choices" in data_json:
                            for choice in data_json.get("choices", []):
                                delta = choice.get("delta") or {}
                                if "content" in delta:
                                    aggregated_text.append(delta["content"])
                    elif isinstance(data_json, list):
                        for msg in data_json:
                            extracted = try_extract_id(msg)
                            if extracted:
                                last_message_id = extracted
                            if msg.get("role") == "assistant":
                                # Aggregate assistant textual chunks from batched array
                                for item in msg.get("content", []):
                                    if item.get("type") == "text":
                                        text_piece = item.get("text", "")
                                        if text_piece:
                                            aggregated_text.append(text_piece)
                except json.JSONDecodeError:
                    # Plain text line
                    aggregated_text.append(data_content)
        
        final_text = " ".join(aggregated_text).strip() if aggregated_text else None
        
        # Persist the last message id for the next turn if we were able to extract it
        if last_message_id is not None:
            st.session_state.parent_message_id = last_message_id
        else:
            # Fallback: query thread for the latest message id
            fetched_id = fetch_latest_message_id(thread_data)
            if fetched_id:
                st.session_state.parent_message_id = fetched_id
        
        return final_text
            
    except Exception as e:
        st.error(f"❌ Error calling agent: {str(e)}")
        return None

def fetch_latest_message_id(thread_data):
    """Fetch the latest assistant message id from a thread (fallback when SSE does not include ids).
    
    Calls: GET /api/v2/cortex/threads/{thread_id}/messages
    Returns the newest assistant message id when available.
    """
    host = os.getenv("SNOWFLAKE_HOST")
    token = get_token()
    if not token:
        return None
    
    # Extract thread ID
    if isinstance(thread_data, dict):
        thread_id = thread_data.get('thread_id') or thread_data.get('id') or thread_data
    else:
        thread_id = thread_data
    
    url = f"https://{host}/api/v2/cortex/threads/{thread_id}/messages"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Snowflake-Authorization-Token-Type": "OAUTH"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Expecting a list of messages or an object with "messages"
        messages = []
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get("messages", [])
        # Find the last assistant message id
        last_assistant = None
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                last_assistant = msg
        if last_assistant:
            msg_id = last_assistant.get("message_id") or last_assistant.get("id")
            if msg_id:
                return str(msg_id)
        # If no assistant message, fall back to the last message in the list
        if messages:
            any_msg = messages[-1]
            msg_id = any_msg.get("message_id") or any_msg.get("id")
            if msg_id:
                return str(msg_id)
        return None
    except Exception:
        return None

def main():
    # ----------------------------- Page content ------------------------------
    st.title("🏔️ Snowflake Documentation Agent")
    st.markdown("Ask questions about Snowflake documentation!")
    
    # Initialize session state for cross-interaction continuity
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'parent_message_id' not in st.session_state:
        st.session_state.parent_message_id = 0
    
    # Sidebar with context info
    with st.sidebar:
        st.header("🔧 System Info")
        
        # Display live Snowflake context and environment details
        context, env, success = get_snowflake_context()
        if success:
            st.success("✅ Connected to Snowflake")
            st.info(f"**Database:** {context['DATABASE']}")
            st.info(f"**Schema:** {context['SCHEMA']}")
            st.info(f"**User:** {context['USER_NAME']}")
            st.info(f"**Host:** {env['snowflake_host']}")
        else:
            st.error("❌ Not connected to Snowflake")
        
        # Thread management
        st.header("💬 Thread Management")
        # Multiturn Conversation: when enabled, we add the prior assistant answer
        # as lightweight context to reinforce follow-up questions
        st.checkbox("Multiturn Conversation", value=True, key="reinforce_prompt")
        if st.button("🆕 New Conversation"):
            thread_data = create_thread()
            if thread_data:
                st.session_state.thread_id = thread_data
                st.session_state.messages = []
                st.session_state.parent_message_id = 0
                st.success(f"✅ New thread: {thread_data['thread_id']}")
                st.rerun()
        
        if st.session_state.thread_id:
            thread_id = st.session_state.thread_id['thread_id']
            st.success(f"📝 Active Thread: {thread_id}")
            st.caption(f"Parent message id: {st.session_state.get('parent_message_id')}")
    
    # Chat interface
    st.header("💬 Chat with Documentation Agent")
    
    # Display chat history (user and assistant messages)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input handles thread creation (if needed) and emits messages to agent
    if prompt := st.chat_input("Ask about Snowflake documentation..."):
        # Ensure we have a thread
        if not st.session_state.thread_id:
            with st.spinner("Creating new thread..."):
                thread_data = create_thread()
                if thread_data:
                    st.session_state.thread_id = thread_data
                    st.session_state.parent_message_id = 0
                else:
                    st.error("❌ Failed to create thread. Please try again.")
                    st.stop()
        
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            # Optionally reinforce context by injecting previous assistant answer
            effective_prompt = prompt
            if st.session_state.get("reinforce_prompt"):
                try:
                    last_assistant = next(
                        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
                        None
                    )
                except Exception:
                    last_assistant = None
                if last_assistant:
                    # Prepend prior assistant response to help the agent resolve
                    # ambiguous follow-ups (e.g., "show syntax for any of these")
                    effective_prompt = (
                        "Context from the previous assistant answer:\n"
                        f"{last_assistant}\n\n"
                        "User request:\n"
                        f"{prompt}"
                    )
            
            response_content = call_agent_with_thread(effective_prompt, st.session_state.thread_id)
            
            if response_content:
                # Persist the assistant reply in the conversation transcript
                st.write(response_content)
                st.session_state.messages.append({"role": "assistant", "content": response_content})
            else:
                error_msg = "❌ Sorry, I couldn't process your request. Please try again."
                st.write(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main()