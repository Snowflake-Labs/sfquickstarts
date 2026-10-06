author: James Cha-Earley
id: getting-started-with-cortex-agent-sdk
language: en
summary: Build programmatic AI agent workflows using the Snowflake Cortex Agent SDK for Python — from your first agent run to an automated data engineering ops agent.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex, Agent, SDK, Python, AI

# Getting Started with the Cortex Agent SDK

<!-- ------------------------ -->
## Overview

The [Snowflake Cortex Agent SDK](https://pypi.org/project/snowflake-cortex-agent-sdk/) gives you programmatic Python access to Snowflake Cortex Agents. Instead of clicking through Snowsight, you can build, run, and orchestrate agents from scripts, notebooks, CI/CD pipelines, and scheduled jobs.

This guide walks you from a first "hello world" agent run through streaming events, multi-turn conversations, a coding agent sandbox, and finally an automated data engineering ops agent that monitors your pipelines and data quality.

### Prerequisites
- A Snowflake account with Cortex AI enabled
- Basic Python and SQL knowledge

### What You'll Learn
- How to authenticate with the SDK using a programmatic access token (PAT)
- How to run a lite agent and stream its response
- How to process streaming events and extract results
- How to manage threads and build multi-turn conversations
- How to run a coding agent in a sandboxed environment
- How to build an automated data engineering ops agent

### What You'll Need
- A [Snowflake account](https://signup.snowflake.com/) (Enterprise edition or higher)
- Python 3.10 or later
- A programmatic access token (PAT) -- we'll create one in the Setup step

### What You'll Build
- Five progressively more advanced agent scripts
- A production-ready automated ops agent that checks pipeline health, data quality, and diagnoses incidents

<!-- ------------------------ -->
## Setup

### Install the SDK

```bash
pip install snowflake-cortex-agent-sdk
```

### Create a Programmatic Access Token (PAT)

1. In Snowsight, click your name in the bottom-left corner
2. Go to **Settings** > **Authentication**
3. Under **Programmatic access tokens**, click **Generate Token**
4. Give it a name (e.g., `agent-sdk-quickstart`) and copy the token

### Set Environment Variables

```bash
export SNOWFLAKE_ACCOUNT="your-account-identifier"
export SNOWFLAKE_PAT="your-pat-token"
```

> NOTE: Your account identifier is the `<orgname>-<accountname>` portion of your Snowflake URL (e.g., `myorg-myaccount`).

### Create Demo Objects

Run the following SQL in Snowsight or via SnowSQL to create the demo schema and sample data:

```sql
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS AGENT_SDK_DEMO_DB;
CREATE SCHEMA IF NOT EXISTS AGENT_SDK_DEMO_DB.QUICKSTART;

-- Create a demo role with limited access
USE ROLE USERADMIN;
CREATE ROLE IF NOT EXISTS AGENT_SDK_DEMO_ROLE;
GRANT ROLE AGENT_SDK_DEMO_ROLE TO USER IDENTIFIER(CURRENT_USER());

-- Grant access to the demo objects only
USE ROLE SYSADMIN;

CREATE OR REPLACE TABLE AGENT_SDK_DEMO_DB.QUICKSTART.SALES (
    sale_date DATE,
    region VARCHAR,
    product VARCHAR,
    units_sold INT,
    revenue FLOAT
);

INSERT INTO AGENT_SDK_DEMO_DB.QUICKSTART.SALES VALUES
    ('2026-10-01', 'North America', 'Widget A', 150, 4500.00),
    ('2026-10-01', 'Europe', 'Widget A', 120, 3600.00),
    ('2026-10-01', 'Asia Pacific', 'Widget B', 200, 8000.00),
    ('2026-10-02', 'North America', 'Widget B', 180, 7200.00),
    ('2026-10-02', 'Europe', 'Widget A', 90, 2700.00),
    ('2026-10-02', 'Asia Pacific', 'Widget A', 160, 4800.00),
    ('2026-10-03', 'North America', 'Widget A', 130, 3900.00),
    ('2026-10-03', 'Europe', 'Widget B', 110, 4400.00),
    ('2026-10-03', 'Asia Pacific', 'Widget B', 220, 8800.00),
    ('2026-10-04', 'North America', 'Widget B', 170, 6800.00),
    ('2026-10-04', 'Europe', 'Widget A', 140, 4200.00),
    ('2026-10-04', 'Asia Pacific', 'Widget A', 190, 5700.00);

-- Grant access to the demo role (not PUBLIC)
GRANT USAGE ON DATABASE AGENT_SDK_DEMO_DB TO ROLE AGENT_SDK_DEMO_ROLE;
GRANT USAGE ON SCHEMA AGENT_SDK_DEMO_DB.QUICKSTART TO ROLE AGENT_SDK_DEMO_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA AGENT_SDK_DEMO_DB.QUICKSTART TO ROLE AGENT_SDK_DEMO_ROLE;
GRANT INSERT ON ALL TABLES IN SCHEMA AGENT_SDK_DEMO_DB.QUICKSTART TO ROLE AGENT_SDK_DEMO_ROLE;
```

> NOTE: Generate your PAT while using the `AGENT_SDK_DEMO_ROLE` role, or set the role in your connection config. This ensures the agent can only access the demo database.

You're ready to write your first agent script.

<!-- ------------------------ -->
## Your First Agent Run

In this step you'll connect to Snowflake and run a lite agent that answers a question about your sales data using the `cortex_analyst_text_to_sql` tool.

The agent takes an inline semantic model that describes your table's dimensions and measures, generates SQL to answer the question, and returns the results.

Create a file called `01_hello_agent.py`:

```python
import os
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

# Stream and extract the response
print("=== Streaming agent run ===\n")

stream = client.agent.stream(body)
events = list(stream)

result = extract_analyst_response(events)

print(f"Interpretation: {result.get('text', '(none)')}\n")
print(f"Generated SQL:\n{result.get('sql', '(none)')}\n")

rows = result.get("results", [])
if rows:
    print(f"Results ({len(rows)} rows):")
    for row in rows:
        print(f"  {row}")

client.close()
print("\nDone!")
```

Run it:

```bash
python 01_hello_agent.py
```

You should see the agent interpret your question, generate SQL to query the `SALES` table, and return the results grouped by region.

Key concepts:
- **`CortexAgentClient`** is the main entry point — pass your account and a `PatAuth` token
- **`client.agent.stream(body)`** sends a request and returns an event iterator
- **Tool spec** uses `cortex_analyst_text_to_sql` with an inline semantic model that maps your table structure
- The response includes both the generated SQL and a natural language interpretation

<!-- ------------------------ -->
## Streaming and Callbacks

In this step you'll process events as they arrive and use background runs for asynchronous execution.

Create `02_streaming_callbacks.py`:

```python
import os
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

SEMANTIC_MODEL = """..."""
# Copy the full SEMANTIC_MODEL from 01_hello_agent.py (the inline semantic model
# describing AGENT_SDK_DEMO_DB.QUICKSTART.SALES)


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
                {"type": "text", "text": "Which product has the highest total revenue?"}
            ],
        }
    ],
    "tools": [
        {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales_analyst"}}
    ],
    "tool_resources": {
        "sales_analyst": {"inline_semantic_model": SEMANTIC_MODEL}
    },
}

# Process events as they arrive
print("=== Processing events ===\n")
stream = client.agent.stream(body)
process_events(stream)

# Background run
print("\n\n=== Background run ===\n")

bg_body = dict(body)
bg_body["messages"] = [
    {"role": "user", "content": [{"type": "text", "text": "What are the daily revenue trends?"}]}
]

bg_body["stream"] = False
bg_body["background"] = True
bg_run = client.agent.run(bg_body)
print(f"Run started: {bg_run.run_id}")
print("Waiting for completion...\n")

response = bg_run.wait()
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
```

Key patterns:

- **Event processing** — iterate the stream and switch on `item["type"]` to handle `tool_use`, `tool_results`, and `text` events differently
- **Background runs** — set `stream=False` and `background=True` in the body dict, then call `client.agent.run(body)` to get a `BackgroundRun` handle; call `.wait()` to block until done, or `.cancel()` to abort
- This is useful for kicking off multiple agent runs in parallel

<!-- ------------------------ -->
## Threads and Conversations

Threads persist message history across turns. You create a thread, then pass `thread_id` on subsequent runs so the agent has context from previous turns.

Create `03_conversations.py`:

```python
import os
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

SEMANTIC_MODEL = """..."""
# Copy the full SEMANTIC_MODEL from 01_hello_agent.py (the inline semantic model
# describing AGENT_SDK_DEMO_DB.QUICKSTART.SALES)


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


def run_on_thread(client, thread_id, question):
    """Run an agent turn on an existing thread."""
    body = {
        "model": "auto",
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": question}]},
        ],
        "tools": [
            {"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "sales_analyst"}}
        ],
        "tool_resources": {
            "sales_analyst": {"inline_semantic_model": SEMANTIC_MODEL}
        },
        "thread_id": thread_id,
    }
    stream = client.agent.stream(body)
    events = list(stream)
    return extract_text(events)


# Create a thread
print("=== Multi-turn conversation ===\n")

thread = client.threads.create(origin_application="sdk-quickstart")
thread_id = thread.get("thread_id") or thread.get("id")
print(f"Thread created: {thread_id}\n")

# Turn 1
print("User: What are the top selling products?\n")
text = run_on_thread(client, thread_id, "What are the top selling products?")
print(f"Agent: {text}\n")
print("-" * 60)

# Turn 2 — the agent has context from turn 1
print("\nUser: Break that down by region.\n")
text = run_on_thread(client, thread_id, "Break that down by region.")
print(f"Agent: {text}\n")
print("-" * 60)

# Turn 3
print("\nUser: Which region shows the strongest performance?\n")
text = run_on_thread(client, thread_id, "Which region shows the strongest performance?")
print(f"Agent: {text}\n")

# Thread operations
print("\n=== Thread operations ===\n")

client.threads.update(thread_id, thread_name="Sales Analysis Q4")
print("Thread renamed to 'Sales Analysis Q4'")

desc = client.threads.describe(thread_id)
messages = desc.get("messages", [])
print(f"Messages in thread: {len(messages)}")

# Search
results = client.threads.search(query="sales", limit=5)
threads = results.get("threads", [])
print(f"Found {len(threads)} threads matching 'sales'")

# Clean up
client.threads.delete(thread_id)
print("\nThread deleted. Done!")
client.close()
```

Key patterns:

- **`client.threads.create()`** creates a new thread — pass `origin_application` to tag it
- **`thread_id`** on subsequent runs links them to the same conversation
- **`client.threads.search()`** finds threads by keyword (fuzzy or regex)
- **`client.threads.update()`** renames threads; **`.delete()`** removes them

<!-- ------------------------ -->
## Coding Agent Sandbox

The coding agent runs in a sandboxed environment with `code_toolset_all` — it can execute SQL, run bash commands, read/write files, and use skills. This is powerful for automated data engineering tasks.

Create `04_coding_agent.py`:

```python
import os
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
    return "".join(text_parts)


# Single coding agent run
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

# Multi-turn coding session
print("\n\n=== Multi-turn coding session ===\n")

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
                    "text": "Analyze the AGENT_SDK_DEMO_DB.QUICKSTART.SALES table. "
                    "Run some queries to find interesting patterns.",
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
    print(f"\nAgent: {text2[:500]}...")

# Turn 2: Build on findings
print("\n\nUser: Create a view based on what you found.\n")
body3 = {
    "model": "auto",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Based on your analysis, create a useful view in AGENT_SDK_DEMO_DB.QUICKSTART "
                    "that highlights the most interesting pattern you found.",
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
    print(f"\nAgent: {text3[:500]}...")

client.threads.delete(thread_id)
client.close()
print("\nDone!")
```

Key patterns:

- **`client.coding_agent.stream(body)`** runs an agent with full code execution capabilities
- **`permission_policy: "always_allow"`** auto-approves all tool calls (use `"always_ask"` for interactive approval). Since the agent can execute SQL and bash commands, always use a **least-privilege role** like `AGENT_SDK_DEMO_ROLE` rather than ACCOUNTADMIN.
- **`thread_id`** links multi-turn coding sessions so the agent builds on its own previous work
- The agent can execute SQL, create objects, and analyze data autonomously

> NOTE: The coding agent has real write access to your Snowflake account. Use appropriate roles and permissions in production.

<!-- ------------------------ -->
## Automated Data Engineering Ops Agent

This is the showcase: an all-in-one ops agent that monitors pipeline health, checks data quality, and diagnoses incidents — all programmatically via the SDK.

Create `05_data_eng_ops_agent.py`:

```python
import os
from datetime import datetime
from cortex_agent_sdk import CortexAgentClient
from cortex_agent_sdk.auth import PatAuth

client = CortexAgentClient(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    auth=PatAuth(os.environ["SNOWFLAKE_PAT"]),
)

CODING_OPTS = {
    "model": "auto",
    "permission_policy": "always_allow",
}


def extract_text(stream):
    """Extract text content from coding agent stream events."""
    text_parts = []
    for event in stream:
        delta = event.get("delta", {})
        for item in delta.get("content", []):
            if item.get("type") == "text":
                text = item.get("text", {})
                val = text.get("value", text) if isinstance(text, dict) else text
                text_parts.append(str(val))
    return "".join(text_parts) if text_parts else "(No text response)"


def run_check(client, thread_id, prompt):
    """Run a coding agent turn on a thread and return the text response."""
    body = {
        **CODING_OPTS,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "thread_id": thread_id,
    }
    stream = client.coding_agent.stream(body)
    return extract_text(stream)


def main():
    print("=" * 70)
    print("  DAILY DATA ENGINEERING OPS REPORT")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    thread = client.threads.create(origin_application="ops-agent")
    thread_id = thread.get("thread_id") or thread.get("id")

    # Pipeline Health
    print("\n[1/3] Running pipeline health check...\n")
    pipeline_report = run_check(
        client,
        thread_id,
        """You are a data engineering ops agent. Perform a pipeline health check:

1. Query SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY for tasks that FAILED or were
   CANCELLED in the last 24 hours. Show the task name, database, schema,
   error message, and scheduled time.

2. Check if any tasks are stuck by looking for tasks that have been running
   for more than 30 minutes.

3. Summarize your findings in this exact format:
   - Total failures in last 24h: <count>
   - Critical failures (list each with task name, error, and database.schema)
   - Stuck tasks (if any)
   - Overall pipeline health: HEALTHY / DEGRADED / CRITICAL

If there are no failures, report HEALTHY status.""",
    )
    print(pipeline_report)

    # Data Quality
    print("\n" + "-" * 70)
    print("\n[2/3] Running data quality check...\n")
    quality_report = run_check(
        client,
        thread_id,
        """You are a data engineering ops agent. Perform a data quality check:

1. Query SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_RESULTS for any
   DMF violations in the last 24 hours. If this view is not available or
   returns no results, note that and move on.

2. Check table freshness: query SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
   or INFORMATION_SCHEMA.TABLES to find tables that haven't been updated
   in the last 48 hours (look at last_altered or similar columns) in
   databases that are NOT system databases (skip SNOWFLAKE, SNOWFLAKE_SAMPLE_DATA).
   Limit to 10 stalest tables.

3. Summarize your findings:
   - DMF violations: <count> (list each with table, metric, value)
   - Stale tables: <count> (list the top 5 stalest with last update time)
   - Overall data quality: GOOD / WARNING / CRITICAL""",
    )
    print(quality_report)

    # Incident Diagnosis
    needs_diagnosis = any(
        keyword in pipeline_report.lower() + quality_report.lower()
        for keyword in ["critical", "degraded", "failed", "violation"]
    )

    if needs_diagnosis:
        print("\n" + "-" * 70)
        print("\n[3/3] Critical issues detected — running incident diagnosis...\n")
        incident_report = run_check(
            client,
            thread_id,
            f"""You are a senior data engineering ops agent. Based on the pipeline
health and data quality checks you just ran, diagnose root causes and
suggest concrete fixes.

For each critical or degraded finding:
1. Investigate the root cause — run additional queries if needed
   (check object dependencies, recent DDL changes, permission issues)
2. Suggest a specific fix (SQL command, configuration change, or escalation)
3. Rate the urgency: P1 (fix now), P2 (fix today), P3 (fix this week)

Format your response as an incident report with clear sections.""",
        )
        print(incident_report)
    else:
        print("\n" + "-" * 70)
        print("\n[3/3] No critical issues detected. Skipping incident diagnosis.")

    print("\n" + "=" * 70)
    print("  OPS REPORT COMPLETE")
    print("=" * 70)

    client.threads.delete(thread_id)
    client.close()


if __name__ == "__main__":
    main()
```

### How It Works

1. **Pipeline Health Check** — the coding agent queries `TASK_HISTORY` for failures, identifies stuck tasks, and rates overall health
2. **Data Quality Check** — the agent looks for DMF violations and stale tables, rates overall quality
3. **Incident Diagnosis** — if anything is CRITICAL or DEGRADED, the agent investigates root causes and suggests specific fixes with urgency ratings

All three steps run on the **same thread**, so the agent has full context from earlier checks when diagnosing incidents.

### Running It

```bash
python 05_data_eng_ops_agent.py
```

### Extending It

This pattern is designed to be extended:

- **Schedule it** with a Snowflake Task or cron job
- **Send notifications** via webhook (Slack, PagerDuty, email) based on severity
- **Store reports** in a Snowflake table for historical trending
- **Add more checks** — Snowpipe latency, warehouse queue depth, credit consumption anomalies

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've built five progressively more powerful agent scripts using the Cortex Agent SDK.

### What You Learned
- How to authenticate with the SDK using a programmatic access token
- How to run lite agents with streaming and extract structured results
- How to use background runs for asynchronous execution
- How to build multi-turn conversations with persistent threads
- How to use the coding agent sandbox for automated SQL execution
- How to orchestrate multiple agent checks into an automated ops workflow

### Cleanup

To remove the demo objects created in this quickstart:

```sql
DROP DATABASE IF EXISTS AGENT_SDK_DEMO_DB;
```

### Related Resources
- [Cortex Agent SDK on PyPI](https://pypi.org/project/snowflake-cortex-agent-sdk/)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Cortex Agents Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
