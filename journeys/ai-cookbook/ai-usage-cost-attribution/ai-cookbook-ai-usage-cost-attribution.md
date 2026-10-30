sidebar: true
sidebar_json: ai-cookbook
author: Parker Erickson, Bala Krishnamoorthy
id: ai-cookbook-ai-usage-cost-attribution
categories: snowflake-site:taxonomy/product/ai
language: en
summary: One reconciled view of Cortex AI credits by surface, user, agent, model, and cost center, plus budgets and per-user quotas.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/ai-observability/ai-usage-cost-attribution

# AI usage and cost attribution across agents, CoWork, Cortex Code, and AI functions

## Overview

Build a small set of views over `SNOWFLAKE.ACCOUNT_USAGE` that answer "who is spending AI credits, on which surface, with which model, and for which cost center", and that reconcile to the credits on your bill. The recipe then adds the two spend controls Snowflake offers for AI: a tag-based budget that runs your own action, and a per-user quota that blocks users on its own.

| At a glance | |
|---|---|
| Status | GA |
| Stage | Operate |
| Topics | AI Observability, Cortex Code, Cortex AI Functions |
| Time | 30 min |
| Edition | Enterprise |
| Regions | Any region with Cortex AI usage views in ACCOUNT_USAGE |
| Privileges | ACCOUNTADMIN for 01_setup.sql, 04_budget_and_quota.sql and 99_teardown.sql; everything else runs as a read-only COOKBOOK_* role |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/ai-observability/ai-usage-cost-attribution) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/recipes/ai-observability/ai-usage-cost-attribution/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bai-usage-cost-attribution%5D%20&recipe=recipes%2Fai-observability%2Fai-usage-cost-attribution) |

## When to use this

- You need showback or chargeback for Cortex Agents, Snowflake CoWork, Cortex Code (CoCo), AI functions, and Cortex Analyst in one place.
- You want to know which interface drives agent traffic (SQL, REST/external, MCP, Snowsight, Teams).
- You want to set a spend limit and need to choose between a budget and a quota.

When not to use this:

- One-off questions such as "what did AI cost last week". Ask the bundled `cost-intelligence` skill in Cortex Code instead.
- Organization-wide reporting across accounts. The same views exist in `ORGANIZATION_USAGE` (organization account only, higher latency); this recipe covers one account.
- Per-request tracing of what an agent did. See [diagnose-agent-requests](/en/developers/guides/ai-cookbook/diagnose-agent-requests/).

## How it works

![How it works: AI usage and cost attribution across agents, CoWork, Cortex Code, and AI functions](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/ai-usage-cost-attribution/assets/ai-usage-cost-attribution-01.png)

Key concepts:

1. **One source view per billing service type.** Each usage view maps to one service type in `METERING_DAILY_HISTORY` (agents to `CORTEX_AGENTS`, CoWork to `SNOWFLAKE_COWORK`, Cortex Code to the `SNOWFLAKE_COCO*` types, AI functions to `AI_FUNCTIONS`). `V_RECONCILE_METERING` proves the totals match the bill, which is the check that nothing is counted twice. CoWork requests are not in the agent view and agent requests are not in the CoWork view, so a `UNION ALL` of the two is safe. `SNOWFLAKE_COCO_USAGE_HISTORY` already covers the CLI, Desktop, and Snowsight interfaces, so the per-interface `CORTEX_CODE_*` views are left out.
2. **Nested token detail.** In the agent and CoWork views, `TOKENS_GRANULAR` and `CREDITS_GRANULAR` are arrays of `{sub_request_id: {service_type: {model: {input, cache_read_input, cache_write_input, output}}, start_time}}`. The recipe flattens four levels and keeps only object values, which drops the sibling `start_time` key. `TOKENS` on the row equals the sum of all four categories.
3. **Cache ratio.** `input` counts only the uncached input tokens, so the prompt-cache ratio is `cache_read_input / (input + cache_read_input + cache_write_input)`. Dividing by `input` alone gives numbers far above 100%.
4. **Two kinds of credits per agent request.** `TOKEN_CREDITS` is AI spend. `METADATA:sql_query_credits` is warehouse compute run by the request (for example, Cortex Analyst SQL) and is billed as warehouse metering. The views keep them in separate columns so AI totals stay reconcilable.
5. **Budgets observe, quotas block.** A budget evaluates periodically and calls your stored procedure at a threshold; after the limit is crossed, the action can take up to 8 hours (2 hours with the latency-optimized option). A per-user quota blocks further AI requests from a user within minutes of reaching the limit, with no code of yours. The attribution views cover every surface in the title, but the spend controls this recipe creates do not: the budget covers tagged agents, and the quota covers Cortex Agents and AI functions only.

## Prerequisites

| Requirement | Notes |
|---|---|
| Enterprise Edition | Budgets and per-user quotas |
| `ACCOUNTADMIN` | Only for `01_setup.sql` (role, grants), `04_budget_and_quota.sql` (budget and quota creator roles), and `99_teardown.sql` |
| AI usage in the account | Any mix of agents, CoWork, Cortex Code, AI functions. Empty views return empty results, not errors |
| `SNOWFLAKE.USAGE_VIEWER` and `SNOWFLAKE.SECURITY_VIEWER` | Granted by `01_setup.sql`. `USAGE_VIEWER` exposes the Cortex usage views and `METERING_DAILY_HISTORY`; `SECURITY_VIEWER` exposes `ACCOUNT_USAGE.USERS` |

## Quickstart

1. `sql/01_setup.sql` as `ACCOUNTADMIN`: creates `COOKBOOK_AI_USAGE_COST_ATTRIBUTION`, its warehouse, the `COOKBOOK_AI_USAGE_COST_ATTRIBUTION_ANALYST` role (granted to you), and the `COST_CENTER` tag.
2. `sql/02_views.sql` as the analyst role: creates the six views.
3. `sql/03_attribution_queries.sql`: the reports (surface mix, top users, per-agent cost, model and cache mix, Cortex Code, cost centers, REST API tokens, reconciliation).
4. Optional, `sql/04_budget_and_quota.sql`: a tag-based agent budget with a custom action and a per-user quota scoped to tagged users. It ends with `GET_USERS()` and sets no limit.
5. Optional, `sql/05_quota_limit.sql`: sets the per-user daily limit and turns on blocking. Run it only after `GET_USERS()` in 04 returned the users you expect, and at least 10 minutes after 04, because scope changes take 5 to 10 minutes to propagate.
6. `sql/99_teardown.sql` when done.

## Walkthrough

### Read access without IMPORTED PRIVILEGES

The analyst role owns the recipe database, so the views run with that role's read-only grants, not with `ACCOUNTADMIN`'s:

```sql
GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER    TO ROLE IDENTIFIER($cookbook_role);
GRANT DATABASE ROLE SNOWFLAKE.SECURITY_VIEWER TO ROLE IDENTIFIER($cookbook_role);
GRANT OWNERSHIP ON DATABASE IDENTIFIER($cookbook_db) TO ROLE IDENTIFIER($cookbook_role) COPY CURRENT GRANTS;
```

Anyone you later grant `SELECT` on these views can read the usage data they expose, through the owner's privileges. Grant them the way you would grant the underlying views.

### Flattening the granular columns

```sql
FROM V_AGENT_REQUESTS r,
     LATERAL FLATTEN(input => r.tokens_granular) el,   -- array element
     LATERAL FLATTEN(input => el.value)          sub,  -- sub_request_id
     LATERAL FLATTEN(input => sub.value)         svc,  -- service_type (cortex_agents, cortex_analyst)
     LATERAL FLATTEN(input => svc.value)         mdl   -- model
WHERE IS_OBJECT(svc.value)                              -- skip the "start_time" sibling
```

`CREDITS_GRANULAR` has the same shape and is joined back on sub-request, service type, and model. In Cortex Code, `TOKENS_GRANULAR` is a plain object keyed by model, so one flatten is enough.

### Users behind USER_ID

`CORTEX_AI_FUNCTIONS_USAGE_HISTORY` and `CORTEX_REST_API_USAGE_HISTORY` carry `USER_ID` only. The views join `ACCOUNT_USAGE.USERS` on `USER_ID` to get the name. `CORTEX_ANALYST_USAGE_HISTORY` is an hourly roll-up by `USERNAME` with no request id.

### Interface mix for agents

```sql
SELECT surface, interface, SUM(request_count) AS requests, ROUND(SUM(ai_credits), 4) AS ai_credits,
       ROUND(SUM(sql_query_credits), 4) AS agent_warehouse_credits
FROM V_AI_USAGE_UNIFIED
WHERE usage_time >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2 ORDER BY ai_credits DESC;
```

The documented examples for `METADATA:interaction_interface` are `agent_admin_ui`, `sql_function`, `microsoft_teams`, and `external`; other values can appear (for example `mcp`), and `NULL` means unknown or a row older than the field. The view groups on the raw value, mapping `NULL` to `unknown`, instead of hard-coding a list.

### Cost centers from tags

`USER_TAGS` and `AGENT_TAGS` hold one entry per level at which a tag applies (account, database, schema, agent). Pick one value per request before summing, or a request tagged at two levels is counted twice. Query Q6 in `03_attribution_queries.sql` ranks the agent-level tag first.

### Budget versus quota

```sql
-- Budget: tag-scoped, monthly, runs your procedure at a threshold (periodic evaluation)
CALL AGENT_BUDGET!SET_RESOURCE_TAGS(
    [[(SELECT SYSTEM$REFERENCE('TAG', $cost_tag, 'SESSION', 'APPLYBUDGET')), $cost_center]], 'UNION');
CALL AGENT_BUDGET!ADD_CUSTOM_ACTION(
    SYSTEM$REFERENCE('PROCEDURE', $cookbook_db || '.GOVERNANCE.ON_AGENT_BUDGET_THRESHOLD(STRING, NUMBER)'),
    ARRAY_CONSTRUCT($cost_center, 100), 'ACTUAL', 100);

-- Quota (04 and 05): per user, blocks AI requests within minutes once the limit is reached
CALL AI_USER_QUOTA!ADD_SHARED_RESOURCE('CORTEX AGENT');
CALL AI_USER_QUOTA!ADD_SHARED_RESOURCE('AI FUNCTION');
CALL AI_USER_QUOTA!SET_USER_TAGS(
    [[(SELECT SYSTEM$REFERENCE('TAG', $cost_tag, 'SESSION', 'APPLYBUDGET')), $cost_center]], 'UNION');
CALL AI_USER_QUOTA!SET_PER_USER_LIMIT($per_user_daily_credits, 'DAILY');
CALL AI_USER_QUOTA!SET_BLOCK_ENFORCEMENT_ENABLED(TRUE, FALSE);
```

| | Budget | Per-user quota |
|---|---|---|
| Scope | Tagged objects (agents), or tagged users on a shared resource | Each user in scope, same limit for all |
| Cycle | Monthly | Monthly, weekly, daily (UTC) |
| Enforcement | Your stored procedure at a threshold | Built-in block for AI domains, or your procedure |
| Timing | Up to 8 hours after the limit (2 hours latency-optimized) | Within minutes; some overshoot is expected |
| Pooled limit | Yes, one ceiling for the tagged set | No, per user only |

The quota in `04_budget_and_quota.sql` monitors two domains, `CORTEX AGENT` and `AI FUNCTION`. CoWork and Cortex Code spend from tagged users is reported by the views but is not counted against the quota and is never blocked. To include it, add the two other AI domains to the same quota before you set the limit:

```sql
CALL AI_USER_QUOTA!ADD_SHARED_RESOURCE('SNOWFLAKE INTELLIGENCE');  -- Snowflake CoWork
CALL AI_USER_QUOTA!ADD_SHARED_RESOURCE('CORTEX CODE');             -- Cortex Code
```

The agent budget covers only agents carrying the `COST_CENTER` tag; it does not see CoWork, Cortex Code, or AI function spend.

The sample custom action only logs. Replace its `INSERT` with your enforcement, for example the revoke pattern in the resource-budget documentation.

## Verify

- `01_setup.sql` ends with a row count per source view; every view returns a number (zero is fine), none returns an access error.
- Q1 lists your surfaces with `pct_of_ai_credits` summing to 100.
- Q4 shows `cache_read_ratio` between 0 and 1 for each model.
- Q8 shows `delta` of `0.0000` per surface over complete UTC days. Per-day rows in `V_RECONCILE_METERING` can show small offsetting deltas on adjacent days (requests that straddle UTC midnight) and a large delta for the current day, which billing has not closed yet. When such a pair falls on the first day of the Q8 window, Q8 shows that one day's small delta for the surface; `SELECT * FROM V_RECONCILE_METERING WHERE delta <> 0 ORDER BY usage_date` shows the matching day just outside the window.
- If you ran 04: `GET_QUOTA_SCOPE()` lists the `AI_FUNCTION` and `CORTEX_AGENT` domains and the `COST_CENTER = cookbook` tag, and `GET_USERS()` returns only users you tagged (none if you tagged no one). After 05, `GET_CONFIG()` shows `PER_USER_LIMIT_DAILY` of 5 and `BLOCK_ENFORCEMENT_ENABLED` true.
- The sum of `credits` in `V_AGENT_TOKENS_BY_MODEL` equals the sum of `token_credits` in `V_AGENT_REQUESTS`, and the flattened token categories sum to `TOKENS`.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Today's numbers are lower than expected | Agent, CoWork, and Cortex Code views can lag up to 1 hour | Report on complete periods; reconcile only closed UTC days |
| `sql_query_credits` is `NULL` for recent agent rows | SQL cost attribution fills in separately and can lag the row by up to 8 hours; it also excludes Adaptive Warehouses | Treat `NULL` as "not yet attributed", not zero; Q3 counts them |
| Cache ratio above 100% | Divided `cache_read_input` by `input` | Divide by `input + cache_read_input + cache_write_input` |
| Totals higher than the bill | Summed overlapping views, such as `SNOWFLAKE_COCO_USAGE_HISTORY` plus `CORTEX_CODE_CLI_USAGE_HISTORY`, or legacy AI function views | Use one view per service type and check Q8 |
| `Object 'SNOWFLAKE.ACCOUNT_USAGE.USERS' does not exist or not authorized` when creating views | `USAGE_VIEWER` does not cover `USERS` | Grant `SNOWFLAKE.SECURITY_VIEWER`, as `01_setup.sql` does |
| Query works in a worksheet but view creation fails | Secondary roles gave your session access the view owner lacks | View DDL checks the primary role only; grant the database roles to the owning role |
| REST API spend missing from credit totals | `CORTEX_REST_API_USAGE_HISTORY` reports tokens and is billed in currency | Report it from `V_REST_API_TOKENS`, separately |
| Budget exceeded but nothing happened yet | Budgets evaluate periodically | Expect up to 8 hours (2 with latency-optimized); use a quota for fast blocking |
| Quota blocked more people than intended | A new quota covers all users until scoped, and scope changes take 5 to 10 minutes to propagate | Set tags first (04), confirm `GET_USERS()`, wait at least 10 minutes, then set the limit and enable blocking (05) |
| A tagged user keeps spending on CoWork or Cortex Code after hitting the quota | The recipe's quota monitors `CORTEX AGENT` and `AI FUNCTION` only | Add the `SNOWFLAKE INTELLIGENCE` and `CORTEX CODE` domains with `ADD_SHARED_RESOURCE` |
| Budget custom action procedure uses owner's rights | The SNOWFLAKE application calls it and it writes the log table | Keep the body small and fixed; it takes no identifiers from its arguments |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It drops the quota and budget (if created, which also removes the limit and blocking from 05), the database (views, tag, log table, procedure), the warehouse, and the role. If you tagged a user or agent with the recipe's `COST_CENTER` tag, unset it first; the file shows the statements.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Enable the bundled cost-intelligence skill and use it for any follow-up cost questions; this
recipe does not repeat what that skill covers. Then, from
recipes/ai-observability/ai-usage-cost-attribution:
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(); and show me the result.
   Stop if it is not the account I expect.
2. Run sql/01_setup.sql (it switches to ACCOUNTADMIN to create a role and grant the
   SNOWFLAKE.USAGE_VIEWER and SECURITY_VIEWER database roles), then sql/02_views.sql and
   sql/03_attribution_queries.sql, each with snow sql -f.
3. Report Q1 (surface mix), Q4 (model and cache ratio), and Q8 (reconciliation). Q8 delta
   should be 0 per surface; if it is not, show the nonzero rows of V_RECONCILE_METERING so
   I can see whether it is a UTC-midnight straddle at the window edge.
4. sql/04_budget_and_quota.sql creates a budget and a per-user quota, which are account-level
   spend controls. Show me what it creates and wait for my yes before running it. Then show
   me GET_QUOTA_SCOPE() and GET_USERS().
5. Run sql/05_quota_limit.sql only if I say yes after seeing the scope, and no sooner than
   10 minutes after step 4.
6. When I say so, run sql/99_teardown.sql and confirm SHOW DATABASES, SHOW WAREHOUSES and
   SHOW ROLES LIKE 'COOKBOOK_AI_USAGE_COST_ATTRIBUTION%' return nothing.
Never drop or alter objects that do not start with COOKBOOK_.
```

## Related skills

- `cost-intelligence` (bundled with Cortex Code): ad-hoc questions about the same usage views, budgets, and quotas in plain language. Use it for exploration; use this recipe when you want durable, reconciled views.

## References

- [AI cost management and governance](https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance)
- [CORTEX_AGENT_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_agent_usage_history)
- [SNOWFLAKE_COWORK_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/snowflake_cowork_usage_history_view)
- [SNOWFLAKE_COCO_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/snowflake_coco_usage_history)
- [CORTEX_AI_FUNCTIONS_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_ai_functions_usage_history)
- [CORTEX_ANALYST_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_analyst_usage_history)
- [CORTEX_REST_API_USAGE_HISTORY](https://docs.snowflake.com/en/sql-reference/account-usage/cortex_rest_api_usage_history)
- [SNOWFLAKE database roles](https://docs.snowflake.com/en/sql-reference/snowflake-db-roles)
- [Resource budgets for Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-resource-budgets)
- [Per-user quotas](https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas)
