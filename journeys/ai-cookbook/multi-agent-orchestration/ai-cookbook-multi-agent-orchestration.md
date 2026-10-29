sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy, Parker Erickson
id: ai-cookbook-multi-agent-orchestration
categories: snowflake-site:taxonomy/product/ai
language: en
summary: One orchestrator agent delegates to specialist agents through caller's-rights DATA_AGENT_RUN bridges, so Snowflake grants decide which specialist each user reaches.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/multi-agent-orchestration

# Multi-agent orchestration with caller's-rights delegation

## Overview

Build one front-door agent that delegates each question to a specialist agent (sales or support), where Snowflake grants, not prompt instructions, decide which specialist a user can reach and which rows the specialist returns. You end with three agents, two caller's-rights bridge procedures, one fail-closed row access policy, persona users that prove the boundary, and a pinned-version evaluation of routing quality.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Build, Secure |
| Topics | Cortex Agents, Semantic Views |
| Time | 60 min |
| Edition | Enterprise |
| Regions | Any region with Cortex Agents and claude-sonnet-4-6 (directly or through cross-region inference) |
| Privileges | ACCOUNTADMIN for 01_setup.sql, the persona key-pair ALTER USER statements in Verify, and 99_teardown.sql; everything else runs as COOKBOOK_MULTI_AGENT_ADMIN |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/multi-agent-orchestration) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/multi-agent-orchestration/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bmulti-agent-orchestration%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fmulti-agent-orchestration) |

## When to use this

Use an orchestrator with sub-agents when you need one entry point and at least one of these:

- Different users must reach different specialists, and that must be enforced by the platform.
- Each domain needs its own instructions, tools, and budget, often owned by different teams.
- Clients (CoWork, REST apps, MCP clients) should all see one agent instead of choosing among several.

When not to use it:

- One agent with several tools covers the use case. That is simpler, cheaper, and keeps native chart and table output. Start there.
- You only want to reuse another agent's tool definitions. Use `agent_toolset`, which copies the tools into one agent at run time.
- Separate agents per role, with no single entry point, are acceptable. Grants alone then give you the boundary with no bridge code.

## How it works

![How it works: Multi-agent orchestration with caller's-rights delegation](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/multi-agent-orchestration/assets/multi-agent-orchestration-01.png)

- **Delegation is a custom tool.** Cortex Agents have no tool type that runs another agent. The orchestrator's `generic` tools call stored procedures that run the specialist with `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`. The specialist runs as a real agent with its own instructions, model, tools, and budget.
- **Caller's rights carries identity through the hop.** The bridges are `EXECUTE AS CALLER`, so the nested run is authorized against the caller's role. A persona without USAGE on a specialist gets error `399513` from Snowflake, and the bridge returns a fixed `NOT_ENTITLED` marker that the orchestrator relays as a refusal.
- **Four layers of grants.** USAGE on the orchestrator and bridges (anyone may ask), USAGE on each specialist (the boundary), SELECT on the specialist's semantic view and base table (the specialist's tools also run as the caller), and a row access policy inside the sales domain.
- **One fail-closed row access policy.** `SALES_THEATER_POLICY` looks `CURRENT_ROLE()` up in an entitlements table. A role with no row sees no rows.
- **Routing is measured, not assumed.** The orchestrator's instructions choose a specialist, and a model makes that choice, so it can vary between runs. An evaluation with judges pinned to `v3` tells you how often it is right.

### Which role does an agent run use?

Cortex Agents authorize a run against the calling user's **default role**, and the user needs a default warehouse the default role can use. How that plays out per surface:

| Surface | Role used for the run | Notes |
|---|---|---|
| Snowsight and Snowflake CoWork | Default role | CoWork starts the session on the default role and warehouse. |
| Agent REST API (`:run`) | Default role, unless the request sets `X-Snowflake-Role` | The header lets an app pick a role the user has been granted. |
| `DATA_AGENT_RUN` from SQL with key-pair (JWT) auth | The session's current role, in testing | This differs from the access-control docs and from the `399513` message, which both say the default role. A persona that ran `USE ROLE PUBLIC` was denied, and a user whose default role was PUBLIC reached the agent after `USE ROLE` to an entitled role. Do not rely on either; test with users whose default role is the persona role and run no `USE ROLE`. |
| Agent evaluations | The role that runs the evaluation | Evaluations do not impersonate other users. |

Test the boundary as a user whose default role is the persona role, and don't switch roles in that session. Running the questions yourself after `USE ROLE` doesn't test what REST and CoWork users get, because those surfaces use the default role.

## Prerequisites

| Requirement | Notes |
|---|---|
| Enterprise edition or higher | Row access policies |
| Cortex Agents and `claude-sonnet-4-6` | Directly or through cross-region inference |
| `ACCOUNTADMIN` | Only for `01_setup.sql` (roles, users, warehouse, database, `EXECUTE TASK`), the `ALTER USER ... SET RSA_PUBLIC_KEY` statements in Verify, and `99_teardown.sql` |
| Snowflake CLI or a Snowsight worksheet | CLI runs use `snow sql -f <file>` |
| `openssl` | Only to create key pairs for the persona users in Verify |

## Quickstart

1. `sql/01_setup.sql` as `ACCOUNTADMIN`: database, warehouse, `COOKBOOK_MULTI_AGENT_ADMIN`, three persona roles, three persona service users.
2. `sql/02_data.sql`: synthetic sales and support data.
3. `sql/03_semantic_views.sql`: one semantic view per specialist.
4. `sql/04_row_access_policy.sql`: entitlements table and the fail-closed policy.
5. `sql/05_bridges.sql`: the two caller's-rights bridge procedures.
6. `sql/06_agents.sql`: two specialists and the orchestrator.
7. `sql/07_grants.sql`: the persona boundary. Re-run after any re-run of 05 or 06.
8. `sql/08_routing_eval.sql`: starts a routing evaluation.
9. Verify as the persona users (below).

Scripts 02 to 08 run as `COOKBOOK_MULTI_AGENT_ADMIN`. Every script starts with a `SET` block. Object names are fixed: the same names appear as literals inside `$$` bodies (agent specifications, procedure code, semantic view DDL, evaluation YAML) and in teardown, so don't rename them. The orchestration model lives in the agent specifications in `06`; change it there if `claude-sonnet-4-6` is not available to you.

## Walkthrough

### The bridge

Each bridge builds the request body with `json.dumps` and passes both the agent name and the body as bind parameters. Nothing from the user or the model is concatenated into SQL.

```python
body = json.dumps({"messages": [{"role": "user",
                                 "content": [{"type": "text", "text": user_query[:MAX_QUERY_CHARS]}]}]})
rows = session.sql("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?) AS RESP",
                   params=[SUB_AGENT, body]).collect()
resp = json.loads(rows[0]['RESP'])
if resp.get('code'):   # errors come back as a payload, not an exception
    return NOT_ENTITLED if str(resp['code']) in DENIED_CODES else '[sales specialist call failed]'
```

A denied nested run returns this payload rather than raising:

```json
{"code": "399513", "message": "The agent does not exist or access is not authorized for the current role. ..."}
```

The sales bridge also renders the specialist's `table` content blocks as markdown, because only what the bridge returns as text reaches the orchestrator. Chart blocks from the specialist are not forwarded.

### The orchestrator

The orchestrator has two `generic` tools whose `tool_resources` point at the bridges:

```yaml
tool_resources:
  ask_sales:
    type: procedure
    identifier: COOKBOOK_MULTI_AGENT.APP.ASK_SALES_SPECIALIST
    execution_environment:
      type: warehouse
      warehouse: COOKBOOK_MULTI_AGENT_WH
```

Its instructions tell it to call both specialists for a cross-domain question, to rewrite follow-ups as self-contained questions (specialists do not see the conversation), and to relay `NOT_ENTITLED` as a refusal without retrying. Its specification is the same for every persona.

### The boundary

`07_grants.sql` is the whole access-control surface:

```sql
-- Everyone may ask, and may call either bridge (caller's rights: no authority of its own)
GRANT USAGE ON AGENT ORCHESTRATOR_AGENT TO ROLE IDENTIFIER($support_role);
GRANT USAGE ON PROCEDURE ASK_SALES_SPECIALIST(VARCHAR) TO ROLE IDENTIFIER($support_role);
-- Only sales personas may run the sales specialist and read its data
GRANT USAGE  ON AGENT SALES_AGENT                 TO ROLE IDENTIFIER($sales_emea);
GRANT SELECT ON SEMANTIC VIEW SALES_SEMANTIC_VIEW TO ROLE IDENTIFIER($sales_emea);
GRANT SELECT ON TABLE SALES_BOOKINGS              TO ROLE IDENTIFIER($sales_emea);
REVOKE USAGE ON AGENT SALES_AGENT FROM ROLE IDENTIFIER($support_role);
```

Granting both bridges to every persona is deliberate. If a persona lacks USAGE on a bridge, the tool call fails before the handler runs and the user sees a vague error. With USAGE on the bridge but not the specialist, the denial happens at the nested run, where the bridge turns it into a clean refusal.

### The row access policy

```sql
ALTER ROW ACCESS POLICY SALES_THEATER_POLICY SET BODY ->
  EXISTS (
    SELECT 1 FROM COOKBOOK_MULTI_AGENT.APP.SALES_ENTITLEMENTS e
    WHERE e.ROLE_NAME = CURRENT_ROLE()
      AND (e.THEATER = 'ALL' OR e.THEATER = theater_col)
  );
ALTER TABLE SALES_BOOKINGS DROP ALL ROW ACCESS POLICIES;
ALTER TABLE SALES_BOOKINGS ADD ROW ACCESS POLICY SALES_THEATER_POLICY ON (THEATER);
```

The policy is created once with a `FALSE` body and updated with `SET BODY`, so re-runs never need to detach it. `DROP ALL ROW ACCESS POLICIES` before `ADD` guarantees the table has exactly one policy. Inside an agent run, `CURRENT_ROLE()` is the role the run executes under (for these users, their default role).

The sales table is stored at one grain (territory by quarter), so `SUM` is always correct. If your table mixes detail rows with pre-aggregated roll-ups, fix that first: see [mixed-grain data and verified queries](/en/developers/guides/ai-cookbook/mixed-grain-and-verified-queries/).

### The routing evaluation

`08_routing_eval.sql` loads five questions with expected answers and expected tools, creates a dataset, writes the config to a stage with `COPY INTO`, and starts a run:

```yaml
metrics:
  - name: "answer_correctness"
    version: "v3"
  - name: "logical_consistency"
    version: "v3"
```

Pinning `v3` keeps scores comparable between runs. To score routing directly, add `- name: "tool_selection_accuracy"` with `version: "v3"`; that metric is in Public Preview and reads the `ground_truth_invocations` already in the dataset. For the full evaluation workflow see [agent evaluations](/en/developers/guides/ai-cookbook/agent-evaluations/).

### Optional: show the orchestrator in Snowflake CoWork

If your account uses a CoWork object to curate agents, add the orchestrator and let the persona roles see the object. This changes an account-level object, so coordinate it with your account admin:

```sql
USE ROLE ACCOUNTADMIN;
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  ADD AGENT COOKBOOK_MULTI_AGENT.APP.ORCHESTRATOR_AGENT;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
  TO ROLE COOKBOOK_MULTI_AGENT_SALES_EMEA;
```

The persona users in this recipe are `TYPE = SERVICE` and cannot sign in to the UI. To try it in CoWork, provision person users (for example through your identity provider) with the same `DEFAULT_ROLE` and `DEFAULT_WAREHOUSE`.

## Verify

`04_row_access_policy.sql` ends with `POLICY_CONTEXT` checks. Expected: 44 rows for the admin, 16 rows (EMEA only) for `COOKBOOK_MULTI_AGENT_SALES_EMEA`, 0 rows for `COOKBOOK_MULTI_AGENT_SUPPORT`.

To test as the personas, give each persona user a key pair and run the same question as each user:

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out sales_emea.p8 -nocrypt
openssl rsa -in sales_emea.p8 -pubout | grep -v '^-----' | tr -d '\n'   # paste into the ALTER USER below
```

```sql
-- as ACCOUNTADMIN, once per persona user
ALTER USER COOKBOOK_MULTI_AGENT_SALES_EMEA_USER SET RSA_PUBLIC_KEY = '<public key>';
```

```bash
snow sql -x --account <account_identifier> --user COOKBOOK_MULTI_AGENT_SALES_EMEA_USER \
  --authenticator SNOWFLAKE_JWT --private-key-file sales_emea.p8 -q "
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN('COOKBOOK_MULTI_AGENT.APP.ORCHESTRATOR_AGENT',
  \$\${\"messages\":[{\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"What were total new bookings in FY25-Q4 by theater?\"}]}]}\$\$)):content AS content"
```

Expected answers to "What were total new bookings in FY25-Q4 by theater?":

| User | Answer |
|---|---|
| `..._SALES_GLOBAL_USER` | Americas $59.6M, EMEA $38.4M, APAC $22.1M, total $120.0M |
| `..._SALES_EMEA_USER` | EMEA $38.4M only (the row access policy removed the other theaters) |
| `..._SUPPORT_USER` | "This type of question is not available at your access level..." |

A cross-domain question ("What was total new bookings in FY25-Q4, and how do I fix a 401 error from the API?") returns the part each persona is entitled to and a refusal for the other part.

Evaluation results, once `EXECUTE_AI_EVALUATION('STATUS', ...)` reports completion:

```sql
SELECT METRIC_NAME, ROUND(AVG(EVAL_AGG_SCORE), 2) AS avg_score, COUNT(*) AS n
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
  'COOKBOOK_MULTI_AGENT', 'APP', 'ORCHESTRATOR_AGENT', 'CORTEX AGENT', 'routing-baseline'))
GROUP BY METRIC_NAME;
```

Expect one row per metric with `n = 5`. Look at low-scoring inputs with `METRIC_CALLS[0]:explanation` before changing instructions.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Every persona gets every answer | Bridges created `EXECUTE AS OWNER`, so the nested run and the row access policy evaluate the owner's role | Keep bridges `EXECUTE AS CALLER`. Owner's rights hides the specialist's grants from callers, but it removes the persona boundary; use it only if every caller may see everything the owner sees |
| Boundary "passes" for every question when you test it | You ran the questions yourself; the run authorized against your default role | Test as the persona users, as in Verify |
| Specialist answers "permissions issue" for a sales persona | The persona has SELECT on the semantic view but not on the base table; Cortex Analyst's generated SQL reads the table as the caller | Grant SELECT on `SALES_BOOKINGS` (07 does) |
| Raw error text shows up in the conversation | `DATA_AGENT_RUN` returns `{"code": "399513", ...}` instead of raising, and the handler only used `try/except` | Check `resp.get('code')` as the bridges do |
| Vague "system issue" refusal | The persona lacks USAGE on the bridge procedure, so the tool fails before the handler runs | Grant both bridges to all personas and deny at the specialist agent |
| `syntax error ... unexpected 'COMMENT'` (or `'PROFILE'`) on `CREATE OR REPLACE AGENT` | `COPY GRANTS` placed before `COMMENT` or `PROFILE`. This differs from the published syntax in [CREATE AGENT](https://docs.snowflake.com/en/sql-reference/sql/create-agent), which lists `COPY GRANTS` first; that order fails when it is followed by `COMMENT` or `PROFILE` | Put `COPY GRANTS` immediately before `FROM SPECIFICATION`, after `COMMENT` and `PROFILE`, as `06` does. Grants are copied with that order |
| Personas reach nothing after re-running a script | An object was replaced without `COPY GRANTS`, or a table was recreated | Re-run `07_grants.sql`. The scripts use `COPY GRANTS`, `CREATE OR ALTER`, and `INSERT OVERWRITE` to avoid this |
| A user with several roles sees an unexpected slice | The policy keys on `CURRENT_ROLE()` only; role hierarchy is not followed | Add an entitlement row per role that should see data, or switch to `IS_ROLE_IN_SESSION` if you want hierarchy and secondary roles to count |
| Follow-up questions lose context | Specialists run in a fresh `DATA_AGENT_RUN` with no thread | The orchestrator's instructions rewrite follow-ups as self-contained questions |
| Charts from the specialist never appear | Only text and tables that the bridge returns cross the hop | Send chart-heavy users to the specialist directly, or accept the markdown table |
| Slow or costly answers | Each delegated question is at least two agent runs; three for cross-domain | Budget each agent separately; token budgets cover orchestration only, not tool tokens. For usage and cost by agent, see [AI usage and cost attribution](/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/) |
| Edited questions in `ROUTING_EVAL_INPUT` are not evaluated | The dataset is a snapshot taken when it was created; 08 creates it once | Use a new dataset name in 08 (and in the YAML `source_metadata`) after changing the input table |
| Evaluation scores do not reflect persona behavior | Evaluations run as the role that starts them and cannot pass session attributes | Evaluate routing and answer quality as the admin; test the boundary with persona users |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It drops the database (agents, procedures, policy, tables, stage, evaluation dataset and runs), the warehouse, the three persona users, and the four roles. If you ran the optional CoWork step, run the `DROP AGENT` statement at the top of the teardown file first. Delete any local `.p8` key files you created.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Run the recipe in site/cortex-ai-cookbook/src/multi-agent-orchestration.
1. Install or enable the check-agent-access skill from Snowflake-Labs/coco-skills
   if it is not already available.
2. Confirm the target with SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(),
   CURRENT_WAREHOUSE() and show me the result before creating anything.
3. sql/01_setup.sql runs as ACCOUNTADMIN and creates account-level objects: four
   roles, three service users, a warehouse, and EXECUTE TASK ON ACCOUNT. Show me
   what it creates and wait for my confirmation. Then run it, and sql/02 through
   sql/07 in order, with snow sql -f. Stop and report on the first error.
4. Confirm the POLICY_CONTEXT checks at the end of 04 return 44, 16 (EMEA), and 0.
5. Use check-agent-access to confirm each persona role reaches the orchestrator,
   both bridges, and only its own specialist.
6. For the persona tests, I create the key pairs and run the ALTER USER ... SET
   RSA_PUBLIC_KEY statements myself, then give you the private key file paths.
   Never create, print, or read a key yourself. Run the Verify question as each
   persona user, with no USE ROLE, and compare with the expected answers table.
7. Run sql/08_routing_eval.sql, poll EXECUTE_AI_EVALUATION('STATUS', ...) until
   the run completes, and report the average score per metric.
8. Do not add the agent to the Snowflake CoWork object unless I ask.
9. When I say done, run sql/99_teardown.sql and confirm SHOW DATABASES/ROLES/USERS/
   WAREHOUSES LIKE 'COOKBOOK_MULTI_AGENT%' return nothing.
```

## Related skills

- `check-agent-access` ([coco-skills](https://github.com/Snowflake-Labs/coco-skills)): audit who can reach which agent and which tool objects behind it. Use it instead of hand-written `SHOW GRANTS` checks when you extend this pattern to more specialists or roles.

## References

- [Cortex Agents: access control and authentication](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-setup)
- [Create and manage agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [CREATE AGENT](https://docs.snowflake.com/en/sql-reference/sql/create-agent)
- [DATA_AGENT_RUN (SNOWFLAKE.CORTEX)](https://docs.snowflake.com/en/sql-reference/functions/data_agent_run-snowflake-cortex)
- [Understanding caller's rights and owner's rights stored procedures](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-rights)
- [Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [User access and settings for agents in Snowflake CoWork](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-cowork/deploy-agents)
