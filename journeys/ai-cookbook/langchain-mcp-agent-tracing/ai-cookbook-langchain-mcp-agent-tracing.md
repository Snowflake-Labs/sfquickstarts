sidebar: true
sidebar_json: ai-cookbook
author: Parker Erickson, Bala Krishnamoorthy
id: ai-cookbook-langchain-mcp-agent-tracing
categories: snowflake-site:taxonomy/product/ai
language: en
summary: External LangChain agents reason through Cortex AI Gateway, act through a Snowflake MCP server, and are analyzed from gateway traces and per-user cost.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-gateway/langchain-mcp-agent-tracing

# LangChain agents on Cortex AI Gateway with MCP tools and traces

## Overview

Run LangChain agents outside Snowflake that do their model reasoning through Cortex AI Gateway and act on Snowflake data through a Snowflake-managed MCP server, authenticated only with a Snowflake token. Then analyze what they did from the gateway's traces and what they cost from metered usage, with a small Streamlit app that sees only this recipe's traffic.

| At a glance | |
|---|---|
| Status | Preview |
| Stages | Operate, Build |
| Topics | Cortex AI Gateway, Snowflake MCP, AI Observability |
| Time | 45 min |
| Edition | Any edition with Cortex AI Gateway and Snowflake-managed MCP servers |
| Regions | AWS commercial regions only (preview), excluding Asia Pacific (New Zealand), Asia Pacific (Malaysia), and Europe (Spain) |
| Privileges | ACCOUNTADMIN for sql/01, 02, 03 and 99 (setup, network policy, the token, and teardown); the agent runs as a service user and the analyzer as a role with MONITOR and no gateway USAGE of its own |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-gateway/langchain-mcp-agent-tracing) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-gateway/langchain-mcp-agent-tracing/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Blangchain-mcp-agent-tracing%5D%20&recipe=recipes%2Fcortex-ai-gateway%2Flangchain-mcp-agent-tracing) |

## When to use this

Cortex AI Gateway is in **preview** and available only on **AWS commercial regions** (excluding Asia Pacific (New Zealand), Asia Pacific (Malaysia), and Europe (Spain)). Use this recipe when:

- You already build agents in LangChain or LangGraph and want Snowflake to govern their model access and data access, without moving the agent into Snowflake.
- You want both Claude (Anthropic format) and OpenAI-format models behind one endpoint, with one credential.
- You need to reconstruct what an external agent did, turn by turn, and attribute its cost.

When not to use it:

- You want threads, feedback, and evaluations. Those are Cortex Agents features. An external agent on the gateway writes gateway spans only.
- You need to see tool execution in the traces. The gateway records model calls. MCP tool calls are visible only as content inside the next model call, and only if payload capture is on.
- You need exact per-request billing from traces. Traces are best effort; bill from `AI_GATEWAY_USAGE_HISTORY`.

## How it works

![How it works: LangChain agents on Cortex AI Gateway with MCP tools and traces](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/langchain-mcp-agent-tracing/assets/langchain-mcp-agent-tracing-01.png)

- **Two Snowflake endpoints, one token.** Model calls go to the gateway `base_url` from `SHOW AI GATEWAYS`. Tool calls go to `https://<host>/api/v2/databases/<db>/schemas/<schema>/mcp-servers/<name>`. Both accept the service user's PAT as a Bearer token.
- **Claude through `ChatAnthropic`, OpenAI models through `ChatOpenAI`.** Claude is served on `/v1/messages` only. `ChatAnthropic` points at the gateway base URL and carries the Bearer token in `default_headers`.
- **The agent shapes its own traces.** A fresh W3C `traceparent` per user turn groups that turn's model calls under one `trace_id`. `x-snowflake-ai-gateway-conversation-id` groups turns. The recipe's conversation ids start with `cookbook-lcmcp-<agent>-`, which is how the analyzer and the SQL scope themselves.
- **Least privilege on both sides.** The agent role can reach the gateway, the MCP server, and the SELECT grants its tools need. The analyst role has `MONITOR` on the gateway and one cost view, and no gateway `USAGE` of its own. It can still send inference while `PUBLIC` holds `USAGE` on the gateway, which is the default and which this recipe leaves in place.

## Prerequisites

| Requirement | Notes |
|---|---|
| Account on AWS commercial region with Cortex AI Gateway | Preview. `SHOW AI GATEWAYS` returns one row. |
| Gateway `logging.enabled: true` | `DESCRIBE AI GATEWAY SNOWFLAKE`. Payload capture (`capture_payload.request_response: true`) is needed only for the analyzer's Conversations and Search tabs. This recipe does not change the spec; to change it safely, use the snapshot and restore in [gateway-governance-quickstart](/en/developers/guides/ai-cookbook/gateway-governance-quickstart/). |
| `ACCOUNTADMIN` | For `sql/01` to `03` and `99`. |
| The agent host's IPv4 egress address | A `TYPE = SERVICE` user can generate or use a programmatic access token only while it is subject to a network policy. `sql/01` creates `COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_SVC_POLICY` and sets it on the service user only. It allows `client_cidr`, which defaults to `CURRENT_IP_ADDRESS()` of the setup session as a `/32`. If `client/agent.py` runs on another host, set `client_cidr` in `sql/01` to that host's address. The account-level network policy, if any, is not changed. |
| Models | Defaults are `claude-sonnet-4-6` and `openai-gpt-5-mini`. Override with `AGENT_CLAUDE_MODEL` and `AGENT_OPENAI_MODEL`. |
| Python 3.11+ | `pip install -r client/requirements.txt` for the agent, and `pip install -r app/requirements.txt` for the analyzer. |

## Quickstart

Object names are fixed: they also appear in the MCP server spec, the cost view, and the client. Besides the warehouse size and the models, the value you may change is `client_cidr` in `sql/01`.

1. `sql/01_setup.sql`: database, warehouse, AGENT and ANALYST roles, the service user (default role and warehouse set, as MCP sessions require) and its network policy, and the cost view. Copy `base_url` from the last result.
2. `sql/02_data_and_mcp_server.sql`: synthetic Northwind data, the semantic view, the Cortex Search service, the MCP server, and the grants.
3. `sql/03_service_user_pat.sql`: run it yourself (`snow sql -f sql/03_service_user_pat.sql`) and copy `token_secret`.
4. Run the agent:

   ```bash
   export AGENT_PAT='<token_secret>'
   export AI_GATEWAY_BASE_URL='<base_url>'
   python client/agent.py
   ```

5. After about a minute, run `sql/04_trace_queries.sql` as the ANALYST role, or start the analyzer:

   ```bash
   SNOWFLAKE_DEFAULT_CONNECTION_NAME=<your connection> streamlit run app/streamlit_app.py
   ```

6. `sql/99_teardown.sql`.

## Walkthrough

### Service user and network policy (`sql/01`)

```sql
CREATE NETWORK RULE IF NOT EXISTS IDENTIFIER($svc_network_rule)
  TYPE = IPV4 MODE = INGRESS VALUE_LIST = ($client_cidr);
CREATE NETWORK POLICY IF NOT EXISTS IDENTIFIER($svc_network_policy)
  ALLOWED_NETWORK_RULE_LIST = ($svc_network_rule);
ALTER USER IDENTIFIER($svc_user) SET NETWORK_POLICY = $svc_network_policy;
```

A service user cannot generate or use a PAT unless it is subject to a network policy. Setup gives the service user its own policy rather than relying on an account-level one, so the token works only from `client_cidr`, for both the gateway and the MCP server. Before it creates the rule, setup refuses any value that is not one IPv4 address or a range from `/16` to `/32`, so `0.0.0.0/0` cannot slip in. A user-level policy takes precedence over the account-level policy for that user only.

`USAGE` on the gateway is granted to `PUBLIC` by default, and every role inherits `PUBLIC`. In a default account the ANALYST role can therefore still send inference. This recipe leaves that grant unchanged, because removing it is an account-wide decision. To make the split real, first grant `USAGE` to every role that should keep reaching the gateway, then run `REVOKE USAGE ON AI GATEWAY SNOWFLAKE FROM ROLE PUBLIC;`. Teardown does not touch the `PUBLIC` grant.

### MCP server and grants (`sql/02`)

```sql
CREATE OR REPLACE MCP SERVER MARKETING_MCP FROM SPECIFICATION $$
tools:
  - name: query_campaigns
    type: CORTEX_ANALYST_MESSAGE
    identifier: COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING.DATA.CAMPAIGN_ANALYTICS
  - name: search_strategy_docs
    type: CORTEX_SEARCH_SERVICE_QUERY
    identifier: COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING.DATA.STRATEGY_SEARCH
  - name: execute_sql
    type: SYSTEM_EXECUTE_SQL
    config: {read_only: true, query_timeout: 60, warehouse: COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_WH}
$$;
GRANT USAGE  ON MCP SERVER MARKETING_MCP              TO ROLE COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_AGENT;
GRANT USAGE  ON CORTEX SEARCH SERVICE STRATEGY_SEARCH TO ROLE COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_AGENT;
GRANT SELECT ON SEMANTIC VIEW CAMPAIGN_ANALYTICS      TO ROLE COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_AGENT;
GRANT SELECT ON TABLE CAMPAIGN_SPEND                  TO ROLE COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_AGENT;
```

`USAGE` on the MCP server lets a client list tools. Each tool still needs its own privilege on the object behind it. `CREATE OR REPLACE` drops the grants on the replaced objects, so the script grants them again on every run. The semantic view uses `CREATE OR ALTER`, which keeps its grants.

`execute_sql` lets the model run SQL that Cortex Analyst wrote. It is read-only, and it runs with the agent role, which can SELECT only the two recipe tables. The Snowflake docs recommend exposing a Cortex Agent as the only tool on a server for governed business questions, and putting raw SQL on a separate server with a least-privileged role if you need it. This recipe keeps the three tools together to show tool chaining in LangChain, and relies on the narrow role.

### The agent (`client/agent.py`)

```python
ChatAnthropic(model="claude-sonnet-4-6",
              anthropic_api_url=base_url,            # no /v1: the SDK appends /v1/messages
              anthropic_api_key="not-used",
              default_headers={"Authorization": f"Bearer {pat}",
                               "traceparent": traceparent,
                               "x-snowflake-ai-gateway-conversation-id": conversation_id})

ChatOpenAI(model="openai-gpt-5-mini", base_url=f"{base_url}/v1", api_key=pat,
           default_headers={...}, max_completion_tokens=2048)   # gpt-5 rejects max_tokens

MultiServerMCPClient({"snowflake": {"transport": "streamable_http", "url": mcp_url,
                                    "headers": {"Authorization": f"Bearer {pat}"}}})
```

`gateway_base_url()` refuses any URL that is not `https://.../api/v2/aigateways/...`, which catches the common mistake of pointing at `/api/v2/cortex`. The script builds a new model object per turn so that each turn gets its own `traceparent`, then calls `langchain.agents.create_agent(llm, tools, system_prompt=...)`. A numbers question typically makes three model calls: one to call `query_campaigns`, one to call `execute_sql`, and one to answer.

### Traces and cost (`sql/04`, the analyzer)

Every trace query filters on the service user and the conversation prefix:

```sql
WHERE resource_attributes:"user"::STRING = $svc_user
  AND STARTSWITH(record_attributes:"gen_ai.conversation.id"::STRING, $conv_prefix)
```

The account has one gateway, so without this filter an analyzer shows every user's traffic. The app applies the same filter, passes the window, user, prefix, trace id, and search text as bind parameters (`session.sql(sql, params=[...])`), and never builds SQL from input. Text that comes from traces (model names, captured prompts and responses) is untrusted. It is rendered in dataframes and `st.code`, or passed through `esc()`, which HTML-escapes and then Markdown-escapes it. The app does not use `unsafe_allow_html`.

Cost comes from `OBS.AGENT_GATEWAY_COST`, a view over `ACCOUNT_USAGE.AI_GATEWAY_USAGE_HISTORY`. It is filtered to the service user and takes credits per model from `CREDITS_GRANULAR`. The view is owned by `ACCOUNTADMIN`, so the analyst role needs no `ACCOUNT_USAGE` access. Attribution is per user: every agent that shares this service user shares its cost line. For per-agent cost, give each agent its own service user.

## Verify

- After `sql/01`, `SHOW PARAMETERS LIKE 'NETWORK_POLICY' IN USER COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_SVC` returns `COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING_SVC_POLICY` at level `USER`.
- `client/agent.py` lists the tools `query_campaigns, search_strategy_docs, execute_sql`. It answers four questions. The first uses `query_campaigns` and `execute_sql`, and reports Q4 2025 ROAS of Email 12.7x, Paid Search 3.3x, Social Media 2.1x, and Display 1.2x.
- `sql/04` query 1 returns, for one run, four turns across three conversations, with agents `campaign-analyst` and `strategy-advisor`, 2 to 5 model calls per turn, and status `SUCCESS`.
- Query 3 shows only operation `chat`: no tool spans.
- Query 4, once `ACCOUNT_USAGE` catches up, lists `claude-sonnet-4-6` and `openai-gpt-5-mini`, and its request counts include this run's model calls. Setup reuses the service user name, so the counts also include earlier runs in the 7-day window.
- The analyzer's Overview shows the same counts. With payload capture on (`capture_payload.request_response: true`), a search such as `benchmark` returns rows; with it off, the Search and Conversations tabs have no payloads to match, so that check does not apply. Either way, a search containing quotes or SQL keywords returns no rows and no error.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| `ImportError: cannot import name 'streamablehttp_client'` | `langchain-mcp-adapters` 0.1.x with `mcp` 2.x | Install the pinned set in `client/requirements.txt` |
| Agent exits "Refusing ... only /api/v2/aigateways" | `AI_GATEWAY_BASE_URL` set to `/api/v2/cortex` or a hand-built URL | Use `base_url` from `SHOW AI GATEWAYS` |
| HTTP 400 or 503 from a Claude model | Sent through `ChatOpenAI` to `/v1/chat/completions` | Use `ChatAnthropic`; Claude is served on `/v1/messages` only |
| HTTP 400 "Unsupported parameter: 'max_tokens'" | gpt-5 models | Use `max_completion_tokens` |
| TLS or connection error to the gateway or MCP server | Account host contains an underscore | Replace `_` with `-` in the host (the script does this) |
| Tools listed but a tool call fails with a privilege error | `USAGE` on the MCP server does not cover the tool's object | Grant SELECT on the semantic view and tables, and USAGE on the search service |
| Tools vanish after rerunning `sql/02` | `CREATE OR REPLACE` dropped grants | The script re-grants; if you edit it, keep the grants after the replace |
| MCP session fails to initialize | Service user has no default warehouse or default role | `sql/01` sets both |
| Issuing the PAT fails with a network policy error, or the agent's calls with a valid token are rejected | The service user is not under a network policy, or the agent calls from an address outside `client_cidr` | Set `client_cidr` in `sql/01` to the agent host's egress address, rerun `sql/01`, then rerun `sql/03` |
| `sql/01` stops with "client_cidr must be one IPv4 address or range from /16 to /32" | The setup session reached Snowflake over IPv6, or `client_cidr` is malformed or broader than `/16` | Set `client_cidr` to the agent host's IPv4 address with `/32` |
| The ANALYST role can still call the gateway | `PUBLIC` holds `USAGE` on the gateway by default, and the recipe leaves it | Grant `USAGE` to every role that needs it, then `REVOKE USAGE ON AI GATEWAY SNOWFLAKE FROM ROLE PUBLIC` (an account-wide change) |
| Analyzer: "must have MONITOR granted on AI GATEWAY" | Running with a role that lacks `MONITOR` | Use the ANALYST role |
| Conversations tab says no payloads | `capture_payload.request_response` is off in the gateway spec | Expected; turn it on only if you accept storing prompts and responses |
| Cost tab is empty right after a run | `ACCOUNT_USAGE` latency | Check again later; traces show activity sooner |
| A turn is missing from traces | Trace delivery is best effort | Expected occasionally; do not bill from traces |
| Earlier runs still show up after teardown and setup | Spans stay in the gateway's event table and are matched by user name, which setup reuses | Narrow the window, or filter on a conversation id from the current run |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It removes the network policy from the service user, drops the user (revoking its token) and the policy, then drops the database (tables, semantic view, search service, MCP server, cost view, network rule), the warehouse, and both roles. Every name comes from the script's `SET` block, which matches setup. Dropping the roles removes their grants on the gateway. The recipe does not change the gateway specification, so there is nothing to restore. Teardown does not remove the agent's spans from `AGENT_TRACE_TABLE` or its rows from `AI_GATEWAY_USAGE_HISTORY`. If payload capture was on, those spans hold the prompts and responses.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Run the recipe in recipes/cortex-ai-gateway/langchain-mcp-agent-tracing against my current Snowflake
connection. Enable the bundled cost-intelligence skill and use it for follow-up cost questions. If
you will extend the semantic view, first install the semantic-view-patterns skill from
github.com/Snowflake-Labs/coco-skills and use it for that work.

1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(), CURRENT_IP_ADDRESS(); and show
   me the result. Confirm SHOW AI GATEWAYS returns one row and that DESCRIBE AI GATEWAY SNOWFLAKE
   shows logging.enabled: true. Keep a copy of the specification text. Do not change it.
2. Before sql/01, tell me what it changes at account level: a service user, a network policy on
   that user only that allows client_cidr (show me the value), and USAGE and MONITOR grants on the
   gateway. Wait for my yes, then run sql/01 and sql/02 in order.
3. Ask me to issue the token myself in a separate terminal, outside this session, with
   snow sql -f sql/03_service_user_pat.sql, and to export
   AGENT_PAT='<token_secret>' and AI_GATEWAY_BASE_URL='<base_url from sql/01>'. Never run sql/03
   yourself, and never print, read, or store the token.
4. In a virtual environment, pip install -r client/requirements.txt and run client/agent.py.
   Report the tools used and answers for each turn.
5. Wait a minute, run sql/04 as the ANALYST role, and summarize turns, model calls, and cost.
6. When I say so, run sql/99_teardown.sql. Show that SHOW GRANTS ON AI GATEWAY SNOWFLAKE has no
   COOKBOOK_ grantee, that SHOW NETWORK POLICIES LIKE 'COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING%' and
   SHOW USERS LIKE 'COOKBOOK_LANGCHAIN_MCP_AGENT_TRACING%' are empty, and that DESCRIBE AI GATEWAY
   SNOWFLAKE matches the copy from step 1.
Never drop or alter objects that do not start with COOKBOOK_, and do not change the PUBLIC grant
on the gateway.
```

## Related skills

- `cost-intelligence` (bundled): cost questions across all AI features, including `AI_GATEWAY_USAGE_HISTORY`. This recipe's cost view covers only its own service user.
- `semantic-view-patterns` ([coco-skills](https://github.com/Snowflake-Labs/coco-skills)): semantic view design and diagnostics. This recipe's semantic view is minimal tool data for the MCP server; use the skill to build a production one.

## References

- [Inference with Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway/inference)
- [Observability for Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway/observability)
- [Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway)
- [AI_GATEWAY_USAGE_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/ai_gateway_usage_history)
- [Snowflake-managed MCP server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [CREATE MCP SERVER](https://docs.snowflake.com/en/sql-reference/sql/create-mcp-server)
- [Using programmatic access tokens for authentication](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
