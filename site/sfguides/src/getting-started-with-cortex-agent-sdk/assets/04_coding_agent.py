"""
04_coding_agent.py — Coding Agent Sandbox

Demonstrates:
  - client.coding_agent.stream() with code_toolset_all
  - permission_policy: always_allow
  - Processing coding agent events
  - Multi-turn coding with threads
"""

import os
import json
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)


def print_coding_events(stream):
    """Process and display coding agent events."""
    text_parts = []
    for event in stream:
        # Handle different event formats
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            item_type = item.get("type", "")
            if item_type == "text":
                text = item.get("text", {})
                val = text.get("value", text) if isinstance(text, dict) else text
                text_parts.append(str(val))
            elif item_type == "tool_use":
                tool = item.get("tool_use", {})
                print(f"  [TOOL] {tool.get('name', 'unknown')}")
            elif item_type == "tool_results":
                tr = item.get("tool_results", {})
                print(f"  [RESULT] status: {tr.get('status', 'unknown')}")

        # Also check for text_delta events
        evt = event.get("event", event.get("object", ""))
        if "text" in str(evt).lower() and "delta" in str(evt).lower():
            d = event.get("data", {})
            if d.get("delta"):
                text_parts.append(d["delta"])

    return "".join(text_parts)


# --- Single coding agent run ---
print("=== Coding agent: create a summary table ===\n")

body = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Query the AGENT_SDK_DEMO_DB.QUICKSTART.SALES table, "
                        "calculate total revenue and units sold per region, "
                        "and create a new table called AGENT_SDK_DEMO_DB.QUICKSTART.REGIONAL_SUMMARY "
                        "with the results. Show me the SQL you ran and the final table contents."
                    ),
                }
            ],
        }
    ],
    "permission_policy": "always_allow",
}

stream = client.coding_agent.stream(body)
text = print_coding_events(stream)
if text:
    print(f"\nAgent response:\n{text[:1000]}")

# --- Multi-turn coding session ---
print("\n\n=== Multi-turn coding session ===\n")

# Create a thread for the multi-turn session
thread = client.threads.create(origin_application="sdk-quickstart")
thread_id = thread.get("thread_id") or thread.get("id")

# Turn 1: Analyze
print("User: Analyze the SALES table — what patterns do you see?\n")
body2 = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analyze the AGENT_SDK_DEMO_DB.QUICKSTART.SALES table. "
                        "Run some queries to find interesting patterns in the data."
                    ),
                }
            ],
        }
    ],
    "permission_policy": "always_allow",
    "thread_id": thread_id,
}
stream2 = client.coding_agent.stream(body2)
text2 = print_coding_events(stream2)
if text2:
    print(f"\nAgent: {text2[:500]}...\n")
print("-" * 60)

# Turn 2: Build on findings
print("\nUser: Create a view based on what you found.\n")
body3 = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Based on your analysis, create a useful view in AGENT_SDK_DEMO_DB.QUICKSTART "
                        "that highlights the most interesting pattern you found."
                    ),
                }
            ],
        }
    ],
    "permission_policy": "always_allow",
    "thread_id": thread_id,
}
stream3 = client.coding_agent.stream(body3)
text3 = print_coding_events(stream3)
if text3:
    print(f"\nAgent: {text3[:500]}...\n")

# Clean up
client.threads.delete(thread_id)
client.close()
print("\nDone!")
