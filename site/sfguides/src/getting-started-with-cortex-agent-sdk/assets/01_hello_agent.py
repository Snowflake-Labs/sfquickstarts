"""
01_hello_agent.py — Your First Agent Run

Demonstrates:
  - PAT authentication
  - Lite agent with cortex_analyst_text_to_sql tool
  - Streaming event iteration
  - Extracting SQL and text from the response
"""

import os
import json
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

# Inline semantic model describing the SALES table
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


def extract_analyst_response(events):
    """Extract SQL, text explanation, and results from analyst tool events."""
    for event in events:
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            if item.get("type") == "tool_results":
                tr = item.get("tool_results", {})
                for c in tr.get("content", []):
                    if c.get("type") == "json":
                        return c.get("json", {})
    return {}


body = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What are the total sales by region?"}
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

# --- Stream and extract the response ---
print("=== Streaming agent run ===\n")

stream = client.agent.stream(body)
events = list(stream)

result = extract_analyst_response(events)

# The agent returns a text interpretation and the generated SQL
print(f"Interpretation: {result.get('text', '(none)')}\n")
print(f"Generated SQL:\n{result.get('sql', '(none)')}\n")

# If results are included (depends on agent configuration)
rows = result.get("results", [])
if rows:
    print(f"Results ({len(rows)} rows):")
    for row in rows:
        print(f"  {row}")

client.close()
print("\nDone!")
