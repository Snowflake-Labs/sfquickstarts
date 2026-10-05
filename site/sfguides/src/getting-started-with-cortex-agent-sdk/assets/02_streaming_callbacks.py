"""
02_streaming_callbacks.py — Streaming and Callbacks

Demonstrates:
  - Processing events as they arrive
  - Background runs with .wait()
  - Event-type filtering
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


def process_events(stream):
    """Process streaming events, printing each type as it arrives."""
    for event in stream:
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            item_type = item.get("type", "")

            if item_type == "tool_use":
                tool = item.get("tool_use", {})
                print(f"  [TOOL_USE] {tool.get('name')} — query: {tool.get('input', {}).get('query', '')}")

            elif item_type == "tool_results":
                tr = item.get("tool_results", {})
                print(f"  [TOOL_RESULT] status: {tr.get('status', 'unknown')}")
                for c in tr.get("content", []):
                    if c.get("type") == "json":
                        j = c.get("json", {})
                        print(f"  [SQL] {j.get('sql', '')[:100]}...")
                        print(f"  [TEXT] {j.get('text', '')}")

            elif item_type == "text":
                text_val = item.get("text", {})
                if isinstance(text_val, dict):
                    print(f"  [TEXT] {text_val.get('value', '')}")
                else:
                    print(f"  [TEXT] {text_val}")


body = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Which product has the highest total revenue?",
                }
            ],
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
}

# --- Process events as they arrive ---
print("=== Processing events ===\n")
stream = client.agent.stream(body)
process_events(stream)

# --- Background run ---
print("\n\n=== Background run ===\n")

bg_body = dict(body)
bg_body["messages"] = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "What are the daily revenue trends?"}
        ],
    }
]

bg_run = client.agent.run(bg_body, background=True)
print(f"Run started: {bg_run.run_id}")
print("Waiting for completion...\n")

response = bg_run.wait()

# Extract results from the background run response
for item in response.content:
    if item.get("type") == "tool_results":
        tr = item.get("tool_results", {})
        for c in tr.get("content", []):
            if c.get("type") == "json":
                j = c.get("json", {})
                print(f"SQL: {j.get('sql', '')[:150]}...")
                print(f"Interpretation: {j.get('text', '')}")

client.close()
print("\nDone!")
