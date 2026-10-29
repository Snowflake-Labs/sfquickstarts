sidebar: true
sidebar_json: ai-cookbook
author: Haebichan Jung
id: ai-cookbook-diagnose-agent-requests
categories: snowflake-site:taxonomy/product/ai
language: en
summary: A caller's-rights procedure that reads one agent request's trace, computes a time breakdown by span, and returns an LLM explanation.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/diagnose-agent-requests

# Diagnose slow Cortex Agent requests from their traces

## Overview

`CALL DIAGNOSE_REQUEST('DB.SCHEMA.AGENT', '<request_id>')` returns where one agent request spent its time: a deterministic breakdown by span category (planning, SQL execution, search, response generation, other tools), the slowest spans, and a short LLM explanation with recommendations. It reads only the documented observability table function, runs with the caller's privileges, and uses no dynamic SQL.

| At a glance | |
|---|---|
| Status | GA |
| Stage | Operate |
| Topics | AI Observability, Cortex Agents |
| Time | 20 min |
| Edition | Enterprise |
| Regions | Any region with Cortex Agents and AI_COMPLETE for the chosen model |
| Privileges | ACCOUNTADMIN for 01_setup.sql only; callers need MONITOR on the agent and SNOWFLAKE.CORTEX_USER |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/diagnose-agent-requests) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/diagnose-agent-requests/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bdiagnose-agent-requests%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fdiagnose-agent-requests) |

## When to use this

- A user reports that an agent answer was slow and you want to know whether the time went to LLM planning, a tool, or SQL.
- You want a repeatable, scriptable diagnosis that you can call from a worksheet, a task, or another agent.

When not to use this:

- Aggregate latency and usage reports across many requests: use the `agent-observability-report` sub-skill of the bundled `agent-studio` skill, or Snowsight's agent Observability pane.
- Scoring answer quality: use [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/).
- Cost questions: see [ai-usage-cost-attribution](/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/).

## How it works

![How it works: Diagnose slow Cortex Agent requests from their traces](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/diagnose-agent-requests/assets/diagnose-agent-requests-01.png)

1. **One turn is one trace.** Each agent request writes a trace to `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`. The `AgentV2RequestResponseInfo` span carries the request id, total duration, status, and user question; sibling spans cover planning steps, tool calls, SQL execution, and response generation.
2. **Top-level spans do not overlap.** Spans whose parent is the root span run one after another, so their durations add up to the time accounted for. Nested spans (for example the SQL execution under the SQL tool) are listed but not added again.
3. **Caller's rights.** The procedure reads traces with the caller's own privileges: MONITOR (or OWNERSHIP) on the agent plus `SNOWFLAKE.CORTEX_USER`, the same as reading the table function directly. It cannot show a caller anything they could not already query.
4. **No dynamic SQL.** The agent name is split into three parts, each checked against an unquoted-identifier pattern; the request id must be a UUID; the model must be in an allowlist. All three reach SQL as bind variables.
5. **One LLM call per diagnosis.** The compact trace goes to `AI_COMPLETE` once, with a JSON output schema. The model's answer is returned, never executed.

## Prerequisites

| Requirement | Notes |
|---|---|
| Cortex Agents | The sample agent uses `models.orchestration: auto` and a Cortex Analyst tool on a semantic view |
| `SNOWFLAKE.CORTEX_USER` | Granted to the recipe role by `01_setup.sql` |
| MONITOR on the agent | The recipe role owns the sample agent; grant MONITOR to diagnose your own agents |
| `claude-sonnet-4-6` for `AI_COMPLETE` | Default model. The model is not a `SET` variable, because a session variable cannot reach the procedure body. To use another, edit the `MODEL` default and the `allowed_models` list in the `DECLARE` block of `03_diagnose_request.sql` and rerun that file |
| Optional: `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` | Account-level privilege. Without it, question text and tool payloads are redacted; span names, durations, status, tokens, and model still come through |

## Quickstart

1. `sql/01_setup.sql` as `ACCOUNTADMIN`: role (granted to you), warehouse, database.
2. `sql/02_agent.sql`: 500 synthetic Northwind orders, a semantic view, and `ORDERS_AGENT`. Skip it to diagnose your own agent.
3. `sql/03_diagnose_request.sql`: creates `APP.DIAGNOSE_REQUEST`.
4. `sql/04_run_and_diagnose.sql`: asks the agent one question, waits until its trace is readable (it checks every 5 seconds for up to about 2 minutes), lists recent request ids, and diagnoses the latest one.
5. `sql/99_teardown.sql` when done.

## Walkthrough

### Find the request

`DATA_AGENT_RUN` returns the answer and token usage but not a request id, so read the id from the trace (or from `REQUEST_ID` in `CORTEX_AGENT_USAGE_HISTORY`, which can lag up to an hour):

```sql
SELECT START_TIMESTAMP,
       RECORD_ATTRIBUTES:"snow.ai.observability.agent.request_id"::STRING AS request_id,
       RECORD_ATTRIBUTES:"snow.ai.observability.agent.duration"::NUMBER   AS duration_ms
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(
    'COOKBOOK_DIAGNOSE_AGENT_REQUESTS', 'APP', 'ORDERS_AGENT', 'CORTEX AGENT'))
WHERE RECORD:name = 'AgentV2RequestResponseInfo'
ORDER BY START_TIMESTAMP DESC;
```

Pass `NULL` (or omit the argument) to diagnose the latest request.

### Validate, then bind

```sql
parts := SPLIT(:AGENT_FQN, '.');
db  := UPPER(TRIM(parts[0]::STRING));   -- likewise sch, agt
IF (NOT (REGEXP_LIKE(:db, :ident_re) AND REGEXP_LIKE(:sch, :ident_re) AND REGEXP_LIKE(:agt, :ident_re))) THEN
    RETURN OBJECT_CONSTRUCT('status', 'error', 'message', 'AGENT_FQN parts must be unquoted identifiers');
END IF;
...
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(:db, :sch, :agt, 'CORTEX AGENT'))
```

Input such as `X.Y.Z'); DROP TABLE T; --` is rejected before any query runs. Quoted, case-sensitive agent names are rejected on purpose; extend the pattern if you use them.

### Time breakdown

```sql
ev.RECORD:parent_span_id::STRING = :root_span AS is_top_level,
DATEDIFF('millisecond', ev.START_TIMESTAMP, ev.TIMESTAMP) AS duration_ms
...
SELECT OBJECT_AGG(category, total_ms::VARIANT)
FROM (SELECT category, SUM(duration_ms) AS total_ms FROM sp WHERE is_top_level GROUP BY category)
```

Status codes and error descriptions are read generically from any `*.status.code` and `*.status.description` attribute, because each tool type uses its own attribute prefix.

### The LLM call

```sql
SELECT AI_COMPLETE(:MODEL, :prompt,
         model_parameters => {'temperature': 0, 'max_tokens': 1200},
         response_format  => {'type': 'json', 'schema': {...summary, root_cause, bottleneck_span, recommendations...}})
INTO :diagnosis;
```

With `response_format`, `AI_COMPLETE` returns an OBJECT, so there is no string parsing and no retry loop.

### Letting other roles diagnose

Grant the procedure plus the same privileges a direct trace read needs:

```sql
GRANT USAGE ON DATABASE COOKBOOK_DIAGNOSE_AGENT_REQUESTS TO ROLE <role>;
GRANT USAGE ON SCHEMA COOKBOOK_DIAGNOSE_AGENT_REQUESTS.APP TO ROLE <role>;
GRANT USAGE ON PROCEDURE COOKBOOK_DIAGNOSE_AGENT_REQUESTS.APP.DIAGNOSE_REQUEST(STRING, STRING, STRING) TO ROLE <role>;
GRANT MONITOR ON AGENT <db>.<schema>.<agent> TO ROLE <role>;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <role>;
```

## Verify

`CALL DIAGNOSE_REQUEST('COOKBOOK_DIAGNOSE_AGENT_REQUESTS.APP.ORDERS_AGENT')` returns an object with:

- `status: "success"`, the `trace_id`, and a `summary` with `duration_ms` and `status_code: "200"`. The `question` key appears only if the calling role has the optional `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` privilege; without it the question is redacted and the key is left out.
- `time_breakdown_ms` with keys such as `planning`, `sql_execution`, `response_generation`, `tool_or_other`. Their sum is a little below `summary.duration_ms` (the gap is time outside any top-level span). For the sample question, planning and response generation dominate and SQL is well under a second.
- `slowest_spans` (up to three) and `diagnosis` with `summary`, `root_cause`, `bottleneck_span`, and `recommendations`.

Bad input returns `status: "error"` with a message (`AGENT_FQN parts must be unquoted identifiers`, `REQUEST_ID must be a UUID`, `MODEL not allowed`); an unknown request id returns `status: "not_found"`.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `not_found` right after a request, or the latest diagnosis is of an older request | Traces land some seconds after the request finishes, or the id belongs to another agent | `04_run_and_diagnose.sql` waits for the new trace before diagnosing; in your own scripts, wait or poll the same way, then retry. List ids with step 2 of that file |
| `Cortex Agent '<db>' does not exist or not authorized` | The caller's role lacks MONITOR (or OWNERSHIP) on the agent | `GRANT MONITOR ON AGENT <db>.<schema>.<agent> TO ROLE <role>` |
| Question and tool payloads show as redacted | Caller lacks `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` | The breakdown still works; grant the privilege only to roles that may read conversation content |
| `No active warehouse selected` | Caller's-rights procedures use the caller's session warehouse | `USE WAREHOUSE` before the `CALL` |
| `MODEL not allowed` | Model not in the procedure's allowlist | Edit `allowed_models` in the `DECLARE` block of `03_diagnose_request.sql` and rerun the file; do not pass model names through unchecked |
| Quoted or mixed-case agent name rejected | The identifier pattern accepts unquoted names only | Use the uppercase name, or extend the validation deliberately |
| Recommendations mention things the trace does not show | The LLM is summarizing, not measuring | Trust `time_breakdown_ms` and `slowest_spans`; treat `diagnosis` as a starting point |
| `DATA_AGENT_RUN` output has no request id | The SQL interface returns content, status, and usage only | Read the id from the trace (step 2 of `04_run_and_diagnose.sql`) or pass `NULL` for the latest |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It drops the database (agent, semantic view, table, procedure), the warehouse, and the role. Trace events already written stay in `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`, which can't be modified.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable the bundled agent-studio skill if it is not already available; use its
agent-observability-report sub-skill for any fleet-level latency questions. Then, from
site/cortex-ai-cookbook/src/diagnose-agent-requests:
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(); and show me the result.
   Stop if it is not the account I expect.
2. Run sql/01_setup.sql (it switches to ACCOUNTADMIN to create the role), then
   sql/02_agent.sql and sql/03_diagnose_request.sql, each with snow sql -f. Leave the
   optional READ UNREDACTED grant in 01 commented out unless I ask for it; it is an
   account-level privilege.
3. Run sql/04_run_and_diagnose.sql. It waits for the new trace before diagnosing. Show me
   time_breakdown_ms, slowest_spans, and diagnosis.root_cause.
4. In one snow sql -q session (USE ROLE COOKBOOK_DIAGNOSE_AGENT_REQUESTS_ROLE, its warehouse
   and COOKBOOK_DIAGNOSE_AGENT_REQUESTS.APP), call DIAGNOSE_REQUEST with
   'X.Y.Z''); DROP TABLE T; --' and confirm it returns a validation error.
5. When I say so, run sql/99_teardown.sql and confirm SHOW DATABASES, SHOW WAREHOUSES and
   SHOW ROLES LIKE 'COOKBOOK_DIAGNOSE_AGENT_REQUESTS%' return nothing.
Never drop or alter objects that do not start with COOKBOOK_.
```

## Related skills

- `agent-studio` (bundled with Cortex Code): its `agent-observability-report` sub-skill produces aggregate monitoring reports (latency percentiles, token economics, tool stats, feedback) from the same event table. Use it for fleet-level views; use this recipe for one request.

## References

- [Monitor Cortex Agent requests](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-monitor)
- [AI Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
- [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
- [Cortex Agents REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- [CORTEX_AGENT_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_agent_usage_history)
