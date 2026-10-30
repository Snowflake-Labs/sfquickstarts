sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy, Parker Erickson
id: ai-cookbook-gateway-governance-quickstart
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Route an app through Cortex AI Gateway with its own identity: both API formats, a model allowlist, traces, per-user cost, and a blocking quota.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-gateway/gateway-governance-quickstart

# Cortex AI Gateway governance quickstart

## Overview

Put one application behind Cortex AI Gateway with its own Snowflake identity, then govern it the way a platform team would. By the end, the application calls OpenAI-format and Claude models through a single endpoint. A second role, with `MONITOR` and no gateway `USAGE` of its own, reads every call's trace and the per-user credits. A model allowlist is enforced and then cleanly reverted, and a per-user quota caps the application's daily gateway spend.

| At a glance | |
|---|---|
| Status | Preview |
| Stages | Operate, Secure |
| Topics | Cortex AI Gateway, AI Observability |
| Time | 45 min |
| Edition | Any edition with Cortex AI Gateway |
| Regions | AWS commercial regions only (preview), excluding Asia Pacific (New Zealand), Asia Pacific (Malaysia), and Europe (Spain) |
| Privileges | ACCOUNTADMIN for sql/01, 02, 03, 05, 06, 07 and 99 (setup, network policy, the gateway spec, the token, the optional budget, and teardown); sql/04 runs as the recipe's quota admin role, and the client runs as a service user |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-ai-gateway/gateway-governance-quickstart) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/cortex-ai-gateway/gateway-governance-quickstart/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bgateway-governance-quickstart%5D%20&recipe=recipes%2Fcortex-ai-gateway%2Fgateway-governance-quickstart) |

## When to use this

Cortex AI Gateway is in **preview** and available only on **AWS commercial regions** (excluding Asia Pacific (New Zealand), Asia Pacific (Malaysia), and Europe (Spain)). Use this recipe when:

- Applications or coding agents outside Snowflake call LLMs, and you want them on a governed Snowflake endpoint with a Snowflake credential instead of vendor API keys.
- You need to see what each application sent, attribute its spend, and stop it at a limit.
- You are about to change the account's gateway specification and want a tested snapshot-and-restore path.

When not to use it:

- The workload runs inside Snowflake as AI functions or Cortex Agents. Those have their own usage views, budgets, and quotas; see the bundled `cost-intelligence` skill.
- You need an application or agent dimension in billing data. Gateway cost is attributed to the calling user only, so this recipe gets per-application cost by giving each application its own service user.
- You need a hard stop at an exact credit value. Quotas block within minutes of the spend, so expect some overshoot.

## How it works

![How it works: Cortex AI Gateway governance quickstart](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/gateway-governance-quickstart/assets/gateway-governance-quickstart-01.png)

- **One gateway per account.** Snowflake provisions a single `AI GATEWAY` named `SNOWFLAKE`. Read its endpoint from `SHOW AI GATEWAYS`. `/api/v2/cortex` is Cortex Inference: it accepts the same request and token, but it bypasses the allowlist and writes no gateway span.
- **The spec is the control plane, and it is replaced whole.** `ALTER AI GATEWAY ... FROM SPECIFICATION` sets `models` and `logging` in full. Any field you omit reverts to its default. The recipe snapshots the spec first and restores it with a hash check.
- **Two privileges, two personas.** `USAGE` on the gateway lets a role send inference (with `SNOWFLAKE.CORTEX_USER` as the model entitlement). `MONITOR` lets a role read `AGENT_TRACE_TABLE`. The recipe keeps them in separate roles. Every role also inherits `PUBLIC`, which holds gateway `USAGE` by default, so the split is real only after you revoke that grant (see the walkthrough).
- **Identity is the only cost dimension.** Traces carry `resource_attributes:"user"`, and `AI_GATEWAY_USAGE_HISTORY` carries `USER_ID`. A dedicated service user per application is what makes showback and quotas per application.
- **Traces explain; metering bills.** Spans arrive within about a minute and can be dropped. `AI_GATEWAY_USAGE_HISTORY` is the billing source and lags.

## Prerequisites

| Requirement | Notes |
|---|---|
| Account on AWS commercial region with Cortex AI Gateway | Preview. `SHOW AI GATEWAYS` must return one row. |
| `ACCOUNTADMIN` | For `sql/01`, `02`, `03`, `05`, `06`, `07`, `99`. `sql/04` runs as the recipe's quota admin role. |
| The client's IPv4 egress address | A `TYPE = SERVICE` user can generate or use a programmatic access token only while it is subject to a network policy. `sql/01` creates `COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_SVC_POLICY` and sets it on the service user only. It allows `client_cidr`, which defaults to `CURRENT_IP_ADDRESS()` of the setup session as a `/32`. If the client runs on another host, set `client_cidr` in `sql/01` to that host's address. The account-level network policy, if any, is not changed. |
| Gateway `logging.enabled: true` | Check with `DESCRIBE AI GATEWAY SNOWFLAKE`. Without it no traces are written. Section 4 of the notebook depends on it. |
| Models available to the account | Defaults are `openai-gpt-5` and `claude-sonnet-4-6`. Override with `GATEWAY_OPENAI_MODEL` and `GATEWAY_CLAUDE_MODEL`. |
| Python 3.11+ locally | `pip install -r notebooks/requirements.txt`, plus Jupyter or VS Code. |
| A Snowflake connection for your own user | The notebook uses the active Snowpark session, or `Session.builder.getOrCreate()` with `SNOWFLAKE_DEFAULT_CONNECTION_NAME`. |

## Quickstart

Object names are fixed. Besides the warehouse size and the models, the values you may change are `client_cidr` in `sql/01`, `daily_credits` in `sql/04`, and `monthly_credits` in `sql/07`.

1. `sql/01_setup.sql`: database, warehouse, three roles, the service user and its network policy, the cost-center tag, and the usage view. It prints the gateway `base_url`.
2. `sql/02_snapshot_gateway_spec.sql`: records the current spec (first run only) and creates `GOV.RESTORE_GATEWAY_SPEC()`.
3. `sql/03_service_user_pat.sql`: issues the service user's PAT. Run it yourself (`snow sql -f sql/03_service_user_pat.sql`), then run `export COOKBOOK_GATEWAY_PAT='<token_secret>'`.
4. `sql/04_per_user_quota.sql`: daily quota on gateway spend, scoped by tag to the service user, with blocking on.
5. `notebooks/01_gateway_governance.ipynb`: run sections 0 to 5, 7, and 8.
6. Optional allowlist: run `sql/05_allowlist_restrict.sql`, wait about a minute, run notebook section 6, then run `sql/06_restore_gateway_spec.sql`.
7. Optional budget: `sql/07_shared_resource_budget_optional.sql` tracks the same user's gateway spend against a monthly budget.
8. `sql/99_teardown.sql`.

## Walkthrough

### Identity and roles (`sql/01`)

```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_APP;
GRANT USAGE   ON AI GATEWAY SNOWFLAKE TO ROLE COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_APP;      -- can spend
GRANT MONITOR ON AI GATEWAY SNOWFLAKE TO ROLE COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_MONITOR;  -- can read traces
```

The APP role has no warehouse and no database, because gateway inference needs neither. The service user is `TYPE = SERVICE` with the APP role as its default.

`USAGE` on the gateway is granted to `PUBLIC` by default, and every role inherits `PUBLIC`. In a default account the MONITOR role can therefore still send inference, and so can every other role. This recipe leaves that grant unchanged, because removing it is an account-wide decision. To make the split real, first grant `USAGE` to every role that should keep reaching the gateway, then run:

```sql
REVOKE USAGE ON AI GATEWAY SNOWFLAKE FROM ROLE PUBLIC;
```

To undo it, `GRANT USAGE ON AI GATEWAY SNOWFLAKE TO ROLE PUBLIC;`. Teardown does not touch the `PUBLIC` grant either way.

```sql
CREATE NETWORK RULE IF NOT EXISTS IDENTIFIER($svc_network_rule)
  TYPE = IPV4 MODE = INGRESS VALUE_LIST = ($client_cidr);
CREATE NETWORK POLICY IF NOT EXISTS IDENTIFIER($svc_network_policy)
  ALLOWED_NETWORK_RULE_LIST = ($svc_network_rule);
ALTER USER IDENTIFIER($svc_user) SET NETWORK_POLICY = $svc_network_policy;
```

A service user cannot generate or use a PAT unless it is subject to a network policy. Setup gives the service user its own policy rather than relying on an account-level one, so the token works only from `client_cidr`. Before it creates the rule, setup refuses any value that is not one IPv4 address or a range from `/16` to `/32`, so `0.0.0.0/0` cannot slip in. A user-level policy takes precedence over the account-level policy for that user only, and no other user is affected.

`MONITOR` does not open `ACCOUNT_USAGE`. Rather than grant `SNOWFLAKE.USAGE_VIEWER` and `ACCOUNT_USAGE.USERS` access, setup publishes `GOV.GATEWAY_USAGE_BY_USER`. That view flattens `CREDITS_GRANULAR`, so a request's credits are split by model and never double counted, and it joins `USERS` for the name.

### Snapshot and restore (`sql/02`, `sql/06`)

`DESCRIBE AI GATEWAY` output goes into `GOV.GATEWAY_SPEC_SNAPSHOT` once, together with its `SHA2`. Rerunning never overwrites it. `RESTORE_GATEWAY_SPEC()` runs with caller's rights. It checks the gateway name against `SHOW AI GATEWAYS`, refuses a spec that contains a double dollar sign, re-applies the snapshot, and returns `RESTORED` only if the live hash matches.

### Calling the gateway (notebook sections 0 to 3)

```python
gw = session.sql("SHOW AI GATEWAYS").collect()[0]
scheme, rest = gw["base_url"].split("://", 1)
host, path = rest.split("/", 1)
BASE_URL = f"{scheme}://{host.replace('_', '-')}/{path}"   # TLS needs hyphens

headers = {
    "Authorization": f"Bearer {PAT}",
    "traceparent": f"00-{uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-01",   # one trace per turn
    "x-snowflake-ai-gateway-conversation-id": CONVERSATION_ID,          # one id per conversation
}
requests.post(f"{BASE_URL}/v1/chat/completions", headers=headers,
              json={"model": "openai-gpt-5", "max_completion_tokens": 512, "messages": [...]})
requests.post(f"{BASE_URL}/v1/messages", headers=headers,
              json={"model": "claude-sonnet-4-6", "max_tokens": 256, "messages": [...]})
```

Observed behavior:

- `openai-gpt-5` with `max_tokens` returns HTTP 400 ("Use 'max_completion_tokens' instead").
- `claude-sonnet-4-6` on `/v1/chat/completions` fails, with HTTP 400 (some runs return HTTP 503 with an empty message).
- The OpenAI SDK takes `base_url=f"{BASE_URL}/v1"`. The Anthropic SDK takes `base_url=BASE_URL` and an `httpx.Client` that sends the Bearer header.

### Traces (section 4)

```sql
SELECT trace:"trace_id"::STRING, record:"name"::STRING,
       TRY_TO_NUMBER(record_attributes:"http.status_code"::STRING) AS http_status,
       record_attributes:"gen_ai.usage.input_tokens"::INT, record_attributes:"gen_ai.usage.output_tokens"::INT
FROM TABLE(AGENT_TRACE_TABLE('SNOWFLAKE'))
WHERE timestamp >= DATEADD('hour', -2, CURRENT_TIMESTAMP())
  AND resource_attributes:"user"::STRING = ?                    -- the service user
  AND record_attributes:"gen_ai.conversation.id"::STRING = ?    -- this run
```

Failed calls are spans too (both HTTP 400 calls appear with their status). Calls sent without `traceparent` get a trace id that starts with zeros, so each one stands alone.

### The bypass path (section 5)

The same PAT and body sent to `https://<host>/api/v2/cortex/v1/chat/completions` returns HTTP 200. The conversation's gateway span count does not change. That traffic is metered in `CORTEX_REST_API_USAGE_HISTORY`, not the gateway view.

### Allowlist (`sql/05`, section 6)

`sql/05` applies `models: [{name: 'claude-*'}]` and keeps logging on. With it in place, `openai-gpt-5` on the gateway returns HTTP 401 and Claude returns HTTP 200, while `/api/v2/cortex` still serves the OpenAI model with HTTP 200. The allowlist governs the gateway path only, so combine it with not handing out ungoverned endpoints. `sql/06` restores the original.

### Per-user quota (`sql/04`, section 8)

```sql
CREATE SNOWFLAKE.CORE.QUOTA IF NOT EXISTS GATEWAY_APP_QUOTA();
CALL GATEWAY_APP_QUOTA!SET_USER_TAGS([[(SELECT SYSTEM$REFERENCE('TAG', '<db>.GOV.COST_CENTER', 'SESSION', 'APPLYBUDGET')), 'cookbook_gateway_app']], 'UNION');
CALL GATEWAY_APP_QUOTA!ADD_SHARED_RESOURCE('AI GATEWAY');
CALL GATEWAY_APP_QUOTA!SET_PER_USER_LIMIT(5, 'DAILY');
CALL GATEWAY_APP_QUOTA!SET_BLOCK_ENFORCEMENT_ENABLED(TRUE, FALSE);   -- (block, email the blocked user)
```

A new quota covers every user in the account, so the script narrows the scope by tag **before** it sets a limit, and nothing is enforced until a limit exists. The role needs `SNOWFLAKE.QUOTA_CREATOR`, `CREATE SNOWFLAKE.CORE.QUOTA` on the schema, and `APPLYBUDGET` on the tag. The quota admin role owns the quota, so setup grants that role to `SYSADMIN`; without it, `ACCOUNTADMIN` cannot drop the quota in teardown. `GET_USERS()` resolves tags through `TAG_REFERENCES`, so the service user can take a while to appear. When a user reaches the limit, further gateway requests are denied with an error that names the exhausted quota, and the block lifts at the next UTC day.

### Shared resource budget (`sql/07`, optional)

The budget uses the same tag with `ADD_SHARED_RESOURCE('AI GATEWAY')` and a monthly `SET_SPENDING_LIMIT`. It notifies, or runs your procedure, when spend crosses a threshold. It does not block, and it is evaluated periodically, so it can react hours late. Use it for team showback and the quota for a stop.

## Verify

- `sql/01` ends with one row from `SHOW AI GATEWAYS` whose `base_url` contains `/api/v2/aigateways/`. `SHOW PARAMETERS LIKE 'NETWORK_POLICY' IN USER COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_SVC` returns `COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_SVC_POLICY` at level `USER`, and `DESCRIBE NETWORK RULE COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART.GOV.COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART_SVC_CLIENTS` shows your `client_cidr`.
- `sql/02` shows one snapshot row. `CALL GOV.RESTORE_GATEWAY_SPEC()` on an unchanged gateway returns `RESTORED: SNOWFLAKE spec matches snapshot`.
- Notebook section 1 returns HTTP 200, then HTTP 400 for `max_tokens`. Section 2 returns HTTP 200, then HTTP 400 (or 503).
- Section 4 lists 6 spans for the conversation id (statuses 200, 400, 200, 400 or 503, 200, 200) with `provider` `openai` or `anthropic`.
- Section 5 shows HTTP 200 on the direct path and an unchanged span count.
- Section 6 (after `sql/05`) prints 401 for the OpenAI model on the gateway, 200 for Claude, and 200 on the direct path. `sql/06` returns `matches_snapshot = TRUE`.
- Section 8 shows `BLOCK_ENFORCEMENT_ENABLED = True`, `PER_USER_LIMIT_DAILY = 5`, and a scope of domain `AI_GATEWAY` with the `COST_CENTER` tag.
- Section 7 lists the service user with per-model credits once `ACCOUNT_USAGE` catches up.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Calls succeed but no spans appear and the allowlist has no effect | Client is calling `/api/v2/cortex`, which is Cortex Inference, not the gateway | Use `base_url` (or `privatelink_base_url`) from `SHOW AI GATEWAYS` |
| TLS or hostname error | Account host from `SHOW` contains an underscore | Replace `_` with `-` in the host part only |
| HTTP 400, or HTTP 503 with `{"message":""}`, for a Claude model | Claude sent to `/v1/chat/completions` | Use `/v1/messages` (Anthropic format) |
| HTTP 400 "Unsupported parameter: 'max_tokens'" | gpt-5 models require `max_completion_tokens` | Send `max_completion_tokens` |
| HTTP 401 for a model that worked yesterday | The spec's `models` list does not match it | `DESCRIBE AI GATEWAY SNOWFLAKE`; restore with `sql/06` |
| An OpenAI-format call takes minutes, times out, or returns HTTP 500 once, then works | Upstream model latency varies | Retry; keep client timeouts generous (the notebook uses 180 s) |
| Logging or payload capture silently turned off after a spec change | `FROM SPECIFICATION` replaces the whole spec; omitted fields reset | Start from `DESCRIBE` output and submit the full document |
| `DESCRIBE` shows `capture_payload: {}` | The gateway stores `request_response: false` that way | Expected; it means capture is off |
| "must have MONITOR granted on AI GATEWAY" | Reading `AGENT_TRACE_TABLE` without `MONITOR` | Grant `MONITOR`, not `USAGE`, to the reading role |
| MONITOR role gets "Schema 'SNOWFLAKE.ACCOUNT_USAGE' does not exist or not authorized" | `MONITOR` does not grant `ACCOUNT_USAGE` access | Query `GOV.GATEWAY_USAGE_BY_USER` |
| Role separation looks broken in testing (a role without MONITOR reads traces) | Default secondary roles added a privileged role | `USE SECONDARY ROLES NONE` before testing |
| Issuing the PAT fails with a network policy error, or the client's calls with a valid token are rejected | The service user is not under a network policy, or the client calls from an address outside `client_cidr` | Set `client_cidr` in `sql/01` to the client's egress address, rerun `sql/01`, then rerun `sql/03` |
| `sql/01` stops with "client_cidr must be one IPv4 address or range from /16 to /32" | The setup session reached Snowflake over IPv6, or `client_cidr` is malformed or broader than `/16` | Set `client_cidr` to the client's IPv4 address with `/32` |
| The MONITOR role can still call the gateway | `PUBLIC` holds `USAGE` on the gateway by default, and the recipe leaves it | Grant `USAGE` to every role that needs it, then `REVOKE USAGE ON AI GATEWAY SNOWFLAKE FROM ROLE PUBLIC` (an account-wide change) |
| Error 099421 "role restriction ... does not match the session role" issuing the PAT | Your own session signed in with a PAT | Run `sql/03` from a password, SSO, or key-pair session |
| `GET_USERS()` on the quota is empty right after setup | Tag resolution uses `TAG_REFERENCES`, which lags | Wait; `GET_QUOTA_SCOPE()` already shows the tag |
| `SET_PER_USER_LIMIT` raises `INVALID_LIMIT` | Limits are positive whole credits | Use an integer of 1 or more |
| Teardown fails with "Insufficient privileges to operate on instance 'GATEWAY_APP_QUOTA'" | The quota admin role owns the quota and is not under `SYSADMIN`, and the session has no secondary roles | Teardown grants the role to `SYSADMIN` before it drops the quota; rerun it as `ACCOUNTADMIN` |
| Teardown stops with "Gateway spec restore did not match the snapshot" or "The live gateway spec does not match the snapshot" | The live spec could not be restored exactly | Run `sql/06` to see both specs; the snapshot is kept until this passes |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It restores the gateway spec from the snapshot (stopping, with the snapshot kept, if the hash does not match), turns off quota enforcement, and drops the quota and budget. It then removes the network policy from the service user, drops the user (which revokes its token) and the policy, and drops the database only after checking again that the live spec matches the snapshot. Last, it drops the roles and the warehouse. Every name comes from the script's `SET` block, which matches setup. It finishes with `SHOW GRANTS ON AI GATEWAY SNOWFLAKE` and `DESCRIBE AI GATEWAY SNOWFLAKE`, so you can confirm no `COOKBOOK_` grants remain and the spec is the one you started with.

Teardown does not remove the service user's spans from `AGENT_TRACE_TABLE` or its rows from `AI_GATEWAY_USAGE_HISTORY`. If payload capture is on, those spans contain the prompts and responses the notebook sent.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Run the recipe in recipes/cortex-ai-gateway/gateway-governance-quickstart against my current
Snowflake connection. Enable the bundled cost-intelligence skill and use it for any follow-up
cost questions; this recipe does not repeat what that skill covers.

1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(), CURRENT_IP_ADDRESS(); and show
   me the result. Confirm SHOW AI GATEWAYS returns one row. Print DESCRIBE AI GATEWAY SNOWFLAKE and
   keep a copy of the specification text. Stop if any of this fails.
2. Before sql/01, tell me what it changes at account level: a service user, a network policy on
   that user only that allows client_cidr (show me the value), and USAGE and MONITOR grants on the
   gateway. Wait for my yes, then run sql/01 and sql/02 in order.
3. Ask me to issue the token myself in a separate terminal, outside this session, with
   snow sql -f sql/03_service_user_pat.sql, and to run
   export COOKBOOK_GATEWAY_PAT='<token_secret>'. Never run sql/03 yourself, and never print, read,
   or store the token.
4. Show me sql/04 (a per-user daily quota on gateway spend that blocks the service user) and wait
   for my yes before running it.
5. Run notebooks/01_gateway_governance.ipynb sections 0-5, 7 and 8 and report each HTTP status.
6. Only if I say yes: run sql/05 (it replaces the account's whole gateway spec), notebook
   section 6, then sql/06 immediately, and show that matches_snapshot is TRUE.
7. Only if I say yes: run sql/07 (a monthly shared resource budget).
8. When I say so, run sql/99_teardown.sql. Show that SHOW GRANTS ON AI GATEWAY SNOWFLAKE has no
   COOKBOOK_ grantee, that SHOW NETWORK POLICIES LIKE 'COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART%'
   and SHOW USERS LIKE 'COOKBOOK_GATEWAY_GOVERNANCE_QUICKSTART%' are empty, and that DESCRIBE AI
   GATEWAY SNOWFLAKE matches the copy from step 1.
Never drop or alter objects that do not start with COOKBOOK_, and do not change the PUBLIC grant
on the gateway.
```

## Related skills

- `cost-intelligence` (bundled): ad-hoc questions over `AI_GATEWAY_USAGE_HISTORY`, budgets, and per-user quotas across all Cortex AI features. This recipe covers the gateway-specific setup, and that skill covers analysis across the account.

## References

- [Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway)
- [Inference with Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway/inference)
- [Observability for Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway/observability)
- [Cost management for Cortex AI Gateway](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-ai-gateway/cost-management)
- [AI_GATEWAY_USAGE_HISTORY view](https://docs.snowflake.com/en/sql-reference/account-usage/ai_gateway_usage_history)
- [Per-user quotas](https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas)
- [Using budgets for AI features (shared resources)](https://docs.snowflake.com/en/user-guide/budgets/budget-shared-resources)
- [Using programmatic access tokens for authentication](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
