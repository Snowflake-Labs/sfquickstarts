author: James Cha-Earley
id: automating-cortex-code-with-agent-sdk
language: en
summary: Automate Cortex Code programmatically using the Python Agent SDK -- from one-shot queries to multi-turn sessions with custom MCP tools and hook-based guardrails.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex, Agent, SDK, Python, AI, Automation, MCP, Cortex Code

# Automating Cortex Code with the Python Agent SDK

<!-- ------------------------ -->
## Overview
Duration: 5

Cortex Code (CoCo) is Snowflake's AI coding agent -- it can read files, write code, run SQL, search the web, and orchestrate complex multi-step workflows. Normally you interact with CoCo through the Desktop app or Snowsight. But what if you want to **drive CoCo from a Python script**?

The `cortex_agent_sdk.cortexcode` package gives you programmatic access to the same CoCo engine that powers the Desktop app. You can:

- Send one-shot prompts and stream back results
- Run multi-turn sessions that maintain context across turns
- Register **custom MCP tools** that give CoCo new capabilities
- Add **hook-based guardrails** to intercept, modify, or block agent actions
- Produce **structured JSON output** with typed schemas

This guide walks through five progressive scripts that build from a simple query to a full automated maintenance pipeline.

### What You'll Learn

- How to send one-shot prompts to CoCo and stream results
- How to run multi-turn sessions that maintain context
- How to register custom MCP tools using the `@tool` decorator
- How to add hook-based guardrails for observability and safety
- How to produce structured JSON output with typed schemas

### What You'll Need

- A Snowflake account with Cortex Code access
- The `cortex` CLI installed ([Cortex Code documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code))
- Python 3.10+
- A connection configured in `~/.snowflake/connections.toml` (PAT or key-pair auth)

### What You'll Build

| Script | What It Does |
|--------|-------------|
| `01_oneshot_query.py` | Send a prompt, stream the response |
| `02_session_client.py` | Multi-turn session with context |
| `03_custom_tools.py` | Register custom MCP tools with `@tool` |
| `04_hooks_guardrails.py` | Intercept and control agent actions |
| `05_automated_maintenance.py` | End-to-end automation pipeline |

<!-- ------------------------ -->
## Setup
Duration: 5

### Install the SDK

```bash
pip install 'snowflake-cortex-agent-sdk>=0.0.1'
```

### Verify the CLI

The `cortexcode` package drives CoCo through the `cortex` CLI. Verify it's installed:

```bash
cortex --version
```

### Configure your connection

Make sure you have a working connection in `~/.snowflake/connections.toml`. The scripts reference the connection name -- update it to match yours:

```toml
[my-connection]
account = "YOUR_ACCOUNT"
user = "YOUR_USER"
authenticator = "SNOWFLAKE_JWT"  # or use a PAT
```

### Create demo objects

Run this SQL in Snowsight or via `snow sql` to set up the objects the scripts will reference:

```sql
CREATE DATABASE IF NOT EXISTS CORTEXCODE_AUTOMATION_DB;
CREATE SCHEMA IF NOT EXISTS CORTEXCODE_AUTOMATION_DB.DEMO;
USE SCHEMA CORTEXCODE_AUTOMATION_DB.DEMO;

CREATE OR REPLACE TABLE DAILY_REVENUE (
    day DATE,
    region VARCHAR,
    revenue NUMBER(12,2)
);

INSERT INTO DAILY_REVENUE VALUES
    ('2025-01-01', 'US', 12500.00),
    ('2025-01-01', 'EU', 8300.00),
    ('2025-01-01', 'APAC', 5100.00),
    ('2025-01-02', 'US', 13200.00),
    ('2025-01-02', 'EU', 7900.00),
    ('2025-01-02', 'APAC', 5400.00),
    ('2025-01-03', 'US', 11800.00),
    ('2025-01-03', 'EU', 8600.00),
    ('2025-01-03', 'APAC', 4900.00);

CREATE OR REPLACE TABLE AUTOMATION_LOG (
    id NUMBER AUTOINCREMENT,
    action VARCHAR,
    status VARCHAR,
    details VARCHAR,
    run_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Replace COMPUTE_WH with your warehouse name
CREATE OR REPLACE TASK NIGHTLY_REFRESH
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 2 * * * America/Los_Angeles'
    AS SELECT 1;

-- Suspend the task (we don't want it actually running)
ALTER TASK NIGHTLY_REFRESH SUSPEND;
```

<!-- ------------------------ -->
## One-Shot Query
Duration: 10

The simplest way to automate CoCo is a one-shot query: send a prompt, stream the response, done. No session state, no multi-turn -- just ask and receive.

### The code

Create `01_oneshot_query.py`:

```python
"""One-shot CoCo query: send a prompt, stream the response."""

import asyncio
from cortex_agent_sdk.cortexcode import (
    query,
    CortexCodeAgentOptions,
    AssistantMessage,
    ResultMessage,
)

CONNECTION = "my-connection"  # Update to your connection name


async def main():
    options = CortexCodeAgentOptions(
        connection=CONNECTION,
        max_turns=3,  # Limit agent iterations
    )

    prompt = (
        "Show me all tables in the CORTEXCODE_AUTOMATION_DB.DEMO schema. "
        "For each table, show the row count and columns."
    )

    print(f"Prompt: {prompt}\n")
    print("--- Response ---")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print(f"\n\n--- Done (turns: {message.num_turns}) ---")


if __name__ == "__main__":
    asyncio.run(main())
```

### What's happening

1. **`CortexCodeAgentOptions`** configures the CoCo session. `connection` maps to your `~/.snowflake/connections.toml` entry. `max_turns` caps how many tool-use rounds the agent can take.

2. **`query()`** is an async generator that yields `Message` objects as the agent works. It spawns a CoCo CLI process, sends the prompt, and streams back events.

3. **`AssistantMessage`** contains the agent's response in `content` blocks. Each block can be text, a tool use, or thinking. We filter for text blocks.

4. **`ResultMessage`** signals the agent is done. It includes metadata like turn count.

### Run it

```bash
python 01_oneshot_query.py
```

You'll see CoCo discover the tables, run `SHOW COLUMNS`, and format a summary -- all streamed in real time.

<!-- ------------------------ -->
## Multi-Turn Session
Duration: 10

A one-shot query is stateless -- each call starts fresh. For workflows that need **context across turns**, use `CortexCodeSDKClient`. It keeps a persistent CoCo process running so the agent remembers everything from previous turns.

### The code

Create `02_session_client.py`:

```python
"""Multi-turn CoCo session: maintain context across turns."""

import asyncio
from cortex_agent_sdk.cortexcode import (
    CortexCodeSDKClient,
    CortexCodeAgentOptions,
    AssistantMessage,
    ResultMessage,
)

CONNECTION = "my-connection"


async def send_and_print(client: CortexCodeSDKClient, prompt: str):
    """Send a prompt and print the streamed response."""
    print(f"\n>> {prompt}\n")
    await client.query(prompt)
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print(f"\n[turns: {message.num_turns}]")


async def main():
    options = CortexCodeAgentOptions(
        connection=CONNECTION,
        max_turns=5,
    )

    async with CortexCodeSDKClient(options) as client:
        # Turn 1: Ask about the data
        await send_and_print(
            client,
            "Query CORTEXCODE_AUTOMATION_DB.DEMO.DAILY_REVENUE and "
            "tell me the total revenue by region."
        )

        # Turn 2: Follow up -- agent remembers the previous result
        await send_and_print(
            client,
            "Which region had the highest day-over-day growth? "
            "Show the calculation."
        )

        # Turn 3: Take action based on the analysis
        await send_and_print(
            client,
            "Insert a row into CORTEXCODE_AUTOMATION_DB.DEMO.AUTOMATION_LOG "
            "with action='revenue_analysis', status='complete', "
            "and details summarizing the top region."
        )


if __name__ == "__main__":
    asyncio.run(main())
```

### Key concepts

- **`CortexCodeSDKClient`** manages a persistent CoCo process. Use it as an async context manager (`async with`) so it cleans up properly.
- **`client.query(prompt)`** sends a turn. It doesn't block -- call `receive_response()` to stream the reply.
- **Context carries over**: Turn 2 references "the result" without re-querying, because the agent has full context from turn 1.
- **`interrupt()`** (not shown) lets you cancel a long-running turn mid-stream.

### Run it

```bash
python 02_session_client.py
```

Watch the agent query the table, compute growth rates, and log the result -- with each turn building on the last.

<!-- ------------------------ -->
## Custom MCP Tools
Duration: 15

CoCo has built-in tools for SQL, file operations, and web search. But real automation often needs **domain-specific tools** -- checking an on-call schedule, sending a notification, or calling an internal API.

The `@tool` decorator lets you define custom tools in Python that CoCo can discover and call. They're served as an MCP (Model Context Protocol) server that CoCo connects to automatically.

### The code

Create `03_custom_tools.py`:

```python
"""Custom MCP tools: give CoCo new capabilities."""

import asyncio
import json
from datetime import datetime, timezone

from cortex_agent_sdk.cortexcode import (
    tool,
    create_sdk_mcp_server,
    query,
    CortexCodeAgentOptions,
    AssistantMessage,
    ResultMessage,
)

CONNECTION = "my-connection"

# --- Custom tools -----------------------------------------------------------


@tool(
    name="get_oncall_schedule",
    description="Get today's on-call engineer for a given team.",
    input_schema={"type": "object", "properties": {"team": {"type": "string"}}, "required": ["team"]},
)
async def get_oncall(args):
    """Simulate looking up an on-call rotation."""
    schedules = {
        "data-platform": "Alice Chen",
        "analytics": "Bob Kumar",
        "ml-ops": "Carol Zhang",
    }
    team = args.get("team", "").lower()
    engineer = schedules.get(team, "Unknown -- check PagerDuty")
    return {
        "content": [
            {"type": "text", "text": json.dumps({"team": team, "oncall": engineer})}
        ]
    }


@tool(
    name="send_notification",
    description="Send a notification message to a channel (Slack, email, etc).",
    input_schema={
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "e.g. #data-alerts or an email"},
            "message": {"type": "string"},
            "severity": {"type": "string", "enum": ["info", "warning", "critical"]},
        },
        "required": ["channel", "message"],
    },
)
async def send_notification(args):
    """In production this would call Slack/email API. Here we just log it."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n  [NOTIFICATION] {args.get('severity','info').upper()} "
          f"-> {args['channel']}: {args['message']}")
    return {
        "content": [
            {"type": "text", "text": json.dumps({"sent": True, "timestamp": ts})}
        ]
    }


@tool(
    name="get_pipeline_config",
    description="Get the list of databases and schemas to monitor.",
    input_schema={"type": "object", "properties": {}},
)
async def get_pipeline_config(args):
    """Return a static config. In production, read from a YAML file or table."""
    config = {
        "targets": [
            {"database": "CORTEXCODE_AUTOMATION_DB", "schema": "DEMO"},
        ],
        "alert_channel": "#data-alerts",
        "oncall_team": "data-platform",
    }
    return {"content": [{"type": "text", "text": json.dumps(config)}]}


# --- Main -------------------------------------------------------------------


async def main():
    # Register tools as an MCP server
    ops_server = create_sdk_mcp_server(
        "ops_tools",
        tools=[get_oncall, send_notification, get_pipeline_config],
    )

    options = CortexCodeAgentOptions(
        connection=CONNECTION,
        max_turns=8,
        mcp_servers={"ops": ops_server},
    )

    prompt = (
        "You have access to ops tools. Do the following:\n"
        "1. Get the pipeline config to find which databases to check\n"
        "2. For each target, run SHOW TABLES to check what exists\n"
        "3. Look up who is on-call for the data-platform team\n"
        "4. Send a notification to the alert channel summarizing "
        "what you found and who is on-call\n"
    )

    print(f"Prompt: {prompt}")
    print("--- Response ---")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print(f"\n\n--- Done (turns: {message.num_turns}) ---")


if __name__ == "__main__":
    asyncio.run(main())
```

### How it works

1. **`@tool` decorator** defines a tool with a name, description, and JSON Schema for inputs. CoCo sees these in its tool list and can call them.

2. **`create_sdk_mcp_server()`** bundles tools into an MCP server config. Pass it to `mcp_servers` in options.

3. **CoCo discovers tools automatically**: when the agent needs to look up the on-call schedule or send a notification, it calls your Python functions. The return format must be `{"content": [{"type": "text", "text": "..."}]}`.

4. **Mix custom + built-in tools**: the agent still has access to `snowflake_sql_execute`, `read`, `write`, etc. Your custom tools augment, not replace, the built-in capabilities.

### Run it

```bash
python 03_custom_tools.py
```

Watch CoCo chain together your custom tools with SQL queries -- reading the config, checking tables, looking up on-call, and sending a notification.

<!-- ------------------------ -->
## Hook-Based Guardrails
Duration: 15

Hooks let you **intercept agent actions** before or after they happen. Use them for:

- **Safety**: block writes to production tables
- **Observability**: log every SQL query the agent runs
- **Injection**: add context or modify tool inputs

### The code

Create `04_hooks_guardrails.py`:

```python
"""Hooks: intercept and control CoCo's actions."""

import asyncio
import json

from cortex_agent_sdk.cortexcode import (
    query,
    CortexCodeAgentOptions,
    AssistantMessage,
    ResultMessage,
)
from cortex_agent_sdk.cortexcode.types import HookMatcher

CONNECTION = "my-connection"

# Track all SQL queries for audit
sql_audit_log: list[dict] = []


async def block_dangerous_writes(hook_input, tool_use_id, context):
    """PreToolUse hook: block DDL/DML on production schemas."""
    tool_input = hook_input.get("tool_input", {})
    sql = str(tool_input.get("sql", "")).upper().strip()

    dangerous_patterns = ["DROP ", "TRUNCATE ", "DELETE FROM", "ALTER TABLE"]
    for pattern in dangerous_patterns:
        if sql.startswith(pattern):
            print(f"\n  [HOOK BLOCKED] Dangerous SQL: {sql[:80]}")
            return {
                "decision": "block",
                "reason": f"Blocked: {pattern.strip()} operations are not allowed.",
            }

    return {}  # Allow everything else


async def log_sql_queries(hook_input, tool_use_id, context):
    """PostToolUse hook: log every SQL query for audit."""
    tool_input = hook_input.get("tool_input", {})
    tool_response = hook_input.get("tool_response", "")
    sql = tool_input.get("sql", "")

    if sql:
        entry = {
            "sql": sql[:200],
            "response_preview": str(tool_response)[:100],
        }
        sql_audit_log.append(entry)
        print(f"\n  [SQL LOG] {sql[:80]}")

    return {}


async def inject_safety_context(hook_input, tool_use_id, context):
    """PreToolUse hook: add read-only reminder to SQL tool calls."""
    return {
        "hookSpecificOutput": {
            "additionalContext": (
                "IMPORTANT: This is a read-only audit session. "
                "Do NOT modify any data. Only use SELECT, SHOW, and DESCRIBE."
            ),
        }
    }


async def main():
    options = CortexCodeAgentOptions(
        connection=CONNECTION,
        max_turns=5,
        hooks={
            "PreToolUse": [
                HookMatcher(
                    matcher="snowflake_sql_execute",
                    hooks=[block_dangerous_writes, inject_safety_context],
                ),
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher="snowflake_sql_execute",
                    hooks=[log_sql_queries],
                ),
            ],
        },
    )

    prompt = (
        "Audit the CORTEXCODE_AUTOMATION_DB.DEMO schema: "
        "list all tables with row counts and check if NIGHTLY_REFRESH task "
        "is running. Summarize what you find."
    )

    print(f"Prompt: {prompt}")
    print("--- Response ---")

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            print(f"\n\n--- Done (turns: {message.num_turns}) ---")

    # Print audit log
    if sql_audit_log:
        print("\n\n=== SQL Audit Log ===")
        for i, entry in enumerate(sql_audit_log, 1):
            print(f"  {i}. {entry['sql']}")


if __name__ == "__main__":
    asyncio.run(main())
```

### Hook anatomy

| Hook Event | When It Fires | What You Can Do |
|-----------|---------------|-----------------|
| `PreToolUse` | Before a tool runs | Block it, modify input, inject context |
| `PostToolUse` | After a tool succeeds | Log results, modify output |
| `PostToolUseFailure` | After a tool fails | Log errors, retry logic |
| `UserPromptSubmit` | When a prompt is sent | Rewrite or prepend to prompts |
| `Stop` | When the agent finishes | Final cleanup |

**`HookMatcher`** filters which tools trigger the hook. `matcher="snowflake_sql_execute"` only fires for SQL tool calls. Use `matcher=None` to match all tools, or `"Write|Edit"` for multiple.

**Return values** control what happens:
- `{}` -- allow the action (no change)
- `{"decision": "block", "reason": "..."}` -- deny the action
- `{"hookSpecificOutput": {"additionalContext": "..."}}` -- inject context into the agent's view
- `{"hookSpecificOutput": {"updatedInput": {...}}}` -- modify the tool input

### Run it

```bash
python 04_hooks_guardrails.py
```

The agent audits the schema normally, but every SQL call is logged. The `block_dangerous_writes` hook provides a best-effort check against common destructive SQL patterns. For true safety, always run automation scripts with a **read-only role** -- hooks are a defense-in-depth layer, not a guarantee, since the agent could also run commands through the Bash tool or use SQL patterns the regex doesn't catch.

<!-- ------------------------ -->
## End-to-End Automation
Duration: 15

Now let's combine everything -- custom tools, hooks, multi-turn sessions, and structured output -- into a real automation script that could run on a schedule.

### The code

Create `05_automated_maintenance.py`:

```python
"""End-to-end automation: scheduled maintenance with structured output."""

import asyncio
import json
from datetime import datetime, timezone

from cortex_agent_sdk.cortexcode import (
    tool,
    create_sdk_mcp_server,
    CortexCodeSDKClient,
    CortexCodeAgentOptions,
    AssistantMessage,
    ResultMessage,
)
from cortex_agent_sdk.cortexcode.types import HookMatcher

CONNECTION = "my-connection"

# --- Structured output schema ------------------------------------------------

REPORT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "run_timestamp": {"type": "string"},
            "databases_checked": {"type": "integer"},
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["critical", "warning", "info"]},
                        "object_name": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["severity", "object_name", "message"],
                },
            },
            "summary": {"type": "string"},
        },
        "required": ["run_timestamp", "databases_checked", "findings", "summary"],
    },
}

# --- Custom tools ------------------------------------------------------------

@tool(
    name="get_maintenance_targets",
    description="Get the list of databases and schemas to check during maintenance.",
    input_schema={"type": "object", "properties": {}},
)
async def get_targets(args):
    targets = [
        {"database": "CORTEXCODE_AUTOMATION_DB", "schema": "DEMO"},
    ]
    return {"content": [{"type": "text", "text": json.dumps(targets)}]}


@tool(
    name="log_maintenance_result",
    description="Log the maintenance run result. Call this when the check is complete.",
    input_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "needs_attention", "critical"]},
            "findings_count": {"type": "integer"},
            "summary": {"type": "string"},
        },
        "required": ["status", "findings_count", "summary"],
    },
)
async def log_result(args):
    ts = datetime.now(timezone.utc).isoformat()
    print(f"\n  [MAINTENANCE LOG] status={args['status']}, "
          f"findings={args['findings_count']}, summary={args['summary'][:60]}...")
    return {"content": [{"type": "text", "text": json.dumps({"logged": True, "timestamp": ts})}]}


# --- Hooks -------------------------------------------------------------------

sql_log: list[str] = []

async def readonly_guard(hook_input, tool_use_id, context):
    """Block any write operations."""
    sql = str(hook_input.get("tool_input", {}).get("sql", "")).upper().strip()
    write_prefixes = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "MERGE")
    if any(sql.startswith(p) for p in write_prefixes):
        return {"decision": "block", "reason": "Read-only maintenance mode."}
    sql_log.append(sql[:120])
    return {}


# --- Main --------------------------------------------------------------------

async def main():
    ops_server = create_sdk_mcp_server(
        "maintenance_tools",
        tools=[get_targets, log_result],
    )

    options = CortexCodeAgentOptions(
        connection=CONNECTION,
        max_turns=10,
        mcp_servers={"maintenance": ops_server},
        output_format=REPORT_SCHEMA,
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="snowflake_sql_execute", hooks=[readonly_guard]),
            ],
        },
    )

    async with CortexCodeSDKClient(options) as client:
        # Turn 1: Run the maintenance check
        await client.query(
            "Run a maintenance check:\n"
            "1. Call get_maintenance_targets to get the list of databases\n"
            "2. For each target, check: table row counts, task statuses, "
            "and any tables with no recent writes\n"
            "3. Call log_maintenance_result with your findings\n"
            "4. Return the structured report as your final output"
        )

        report = None
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        print(block.text, end="", flush=True)
            elif isinstance(message, ResultMessage):
                if message.structured_output:
                    report = message.structured_output
                print(f"\n[turns: {message.num_turns}]")

    # --- Post-processing ---
    print("\n\n=== Maintenance Report ===")
    if report:
        print(json.dumps(report, indent=2))
    else:
        print("(No structured output received -- check the agent response above)")

    print(f"\n=== SQL Audit ({len(sql_log)} queries) ===")
    for i, sql in enumerate(sql_log, 1):
        print(f"  {i}. {sql}")


if __name__ == "__main__":
    asyncio.run(main())
```

### What makes this production-ready

1. **Structured output** (`output_format`) forces the agent to return a typed JSON report matching your schema. Parse it directly into your data model.

2. **Read-only hooks** ensure the maintenance check never accidentally modifies data.

3. **Custom tools** integrate with your ops workflow -- the agent can call `log_maintenance_result` to write to your logging system.

4. **Multi-turn session** lets you add follow-up prompts (e.g., "Now check PROD_DB too") without losing context.

### Run it

```bash
python 05_automated_maintenance.py
```

The agent reads the config, audits each database, logs the result through your custom tool, and returns a structured JSON report. The read-only hook provides best-effort protection against accidental writes via `snowflake_sql_execute`. For production use, always run with a **read-only Snowflake role** as the primary safeguard.

<!-- ------------------------ -->
## Cleanup
Duration: 2

Remove the demo objects:

```sql
DROP DATABASE IF EXISTS CORTEXCODE_AUTOMATION_DB;
```

<!-- ------------------------ -->
## Conclusion
Duration: 2

You've learned how to programmatically automate Cortex Code using the Python Agent SDK:

- **One-shot queries** for simple ask-and-receive automation
- **Multi-turn sessions** for workflows that need context across steps
- **Custom MCP tools** to extend CoCo with your own Python functions
- **Hook-based guardrails** to intercept, log, and control agent behavior
- **Structured output** for typed JSON results you can process programmatically

### What's next

- **Schedule it**: Run `05_automated_maintenance.py` as a cron job or Snowflake Task
- **Add more tools**: Connect to PagerDuty, Jira, or Slack APIs for real notifications
- **Explore API mode**: Set `mode="api"` to bypass the CLI and talk directly to the Cortex Agent API (no MCP/hooks, but faster startup)

### Related resources

- [Cortex Code documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
- [Cortex Agents overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Programmatic access tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
