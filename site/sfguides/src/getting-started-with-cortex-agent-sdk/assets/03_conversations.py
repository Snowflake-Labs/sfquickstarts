"""
03_conversations.py — Threads and Conversations

Demonstrates:
  - Thread creation and management
  - Multi-turn agent runs on the same thread
  - Thread search, rename, and delete
"""

import os
import json
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

SEMANTIC_MODEL = """
name: sales_model
tables:
  - name: SALES
    base_table:
      database: AGENT_SDK_DEMO_DB
      schema: QUICKSTART
      table: SALES
    dimensions:
      - name: sale_date
        expr: sale_date
        data_type: DATE
      - name: region
        expr: region
        data_type: VARCHAR
      - name: product
        expr: product
        data_type: VARCHAR
    measures:
      - name: units_sold
        expr: units_sold
        data_type: INT
        default_aggregation: sum
      - name: revenue
        expr: revenue
        data_type: FLOAT
        default_aggregation: sum
"""


def extract_text(events):
    """Extract the analyst text explanation from events."""
    for event in events:
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            if item.get("type") == "tool_results":
                tr = item.get("tool_results", {})
                for c in tr.get("content", []):
                    if c.get("type") == "json":
                        return c["json"].get("text", "")
    return ""


def run_on_thread(client, thread_id, parent_message_id, question):
    """Run an agent turn on an existing thread and return (text, new_parent_id)."""
    body = {
        "model": "auto",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": question}],
            }
        ],
        "tools": [
            {
                "tool_spec": {
                    "type": "cortex_analyst_text_to_sql",
                    "name": "sales_analyst",
                }
            }
        ],
        "tool_resources": {
            "sales_analyst": {"inline_semantic_model": SEMANTIC_MODEL}
        },
        "thread_id": thread_id,
    }
    if parent_message_id:
        body["parent_message_id"] = parent_message_id

    stream = client.agent.stream(body)
    events = list(stream)
    text = extract_text(events)

    # Extract message_id for threading
    new_parent = None
    for event in events:
        meta = event.get("metadata", {})
        if meta.get("message_id"):
            new_parent = meta["message_id"]

    return text, new_parent


# --- Create a thread ---
print("=== Multi-turn conversation ===\n")

thread = client.threads.create(origin_application="sdk-quickstart")
thread_id = thread.get("thread_id") or thread.get("id")
print(f"Thread created: {thread_id}\n")

parent_id = None

# Turn 1
print("User: What are the top selling products?\n")
text, parent_id = run_on_thread(client, thread_id, parent_id, "What are the top selling products?")
print(f"Agent: {text}\n")
print("-" * 60)

# Turn 2
print("\nUser: Break that down by region.\n")
text, parent_id = run_on_thread(client, thread_id, parent_id, "Break that down by region.")
print(f"Agent: {text}\n")
print("-" * 60)

# Turn 3
print("\nUser: Which region shows the strongest performance?\n")
text, parent_id = run_on_thread(
    client, thread_id, parent_id, "Which region shows the strongest performance?"
)
print(f"Agent: {text}\n")

# --- Thread operations ---
print("\n=== Thread operations ===\n")

# Rename
client.threads.update(thread_id, thread_name="Sales Analysis Q4")
print(f"Thread renamed to 'Sales Analysis Q4'")

# Describe — get messages
desc = client.threads.describe(thread_id)
messages = desc.get("messages", [])
print(f"Messages in thread: {len(messages)}")

# Search
print("\n=== Thread search ===\n")
results = client.threads.search(query="sales", limit=5)
threads = results.get("threads", [])
print(f"Found {len(threads)} threads matching 'sales'")

# Clean up
client.threads.delete(thread_id)
print("\nThread deleted. Done!")

client.close()
