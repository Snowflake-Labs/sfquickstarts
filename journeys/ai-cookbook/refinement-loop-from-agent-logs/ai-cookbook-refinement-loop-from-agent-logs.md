sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy
id: ai-cookbook-refinement-loop-from-agent-logs
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Mine Cortex Agent traces for guessed, exploratory, and no-data answers, get the right answer from a subject matter expert, ship it into the semantic view, and re-test.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs

# Refine a semantic view from agent logs: triage, SME review, and verified queries

## Overview

An agent's first week of real questions is the best specification its semantic view will ever get. This recipe turns that traffic into changes to the view on a fixed cadence: read every turn from the agent's traces, sort the turns into review buckets, send the uncertain ones to a subject matter expert as plain question-and-answer pairs, turn each confirmed answer into a description, dimension, metric, custom instruction, or verified query, and re-ask the same questions to confirm the change. The runnable example does one full cycle on a small fictional support-ticket dataset: before the change, the agent guesses what "urgent" means, answers "no escalated tickets" when there are five, and averages resolution time over the wrong population; after, each of those questions is answered correctly.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Evaluate, Operate |
| Topics | Semantic Views, AI Observability, Cortex Agents |
| Time | 30 min |
| Edition | Any edition with semantic views and Cortex Agents |
| Regions | Regions where Cortex Agents and Cortex Analyst are available |
| Privileges | ACCOUNTADMIN for the account statements in 01, the READ UNREDACTED AI OBSERVABILITY EVENTS TABLE grant in 02, and teardown; everything else runs as COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS_ROLE |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Brefinement-loop-from-agent-logs%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Frefinement-loop-from-agent-logs) |

## When to use this

- An agent (in Snowflake CoWork, an MCP client, or your own app over the Agent REST API) is live on a semantic view and you want its answers to improve week over week instead of staying at first-draft quality.
- Your users say things the data doesn't: business words ("urgent", "escalated", "waiting on the customer") over coded values (P1, OPEN, PENDING_CUSTOMER).
- You want a review process where subject matter experts judge answers, not SQL or semantic view diffs.

When not to use it:

- There is no traffic yet. Build the first evaluation set from expected questions instead; see [agent-feedback-to-evals](/en/developers/guides/ai-cookbook/agent-feedback-to-evals/) for turning traffic into an evaluation dataset once it exists.
- You are debugging one slow or failing request. [diagnose-agent-requests](/en/developers/guides/ai-cookbook/diagnose-agent-requests/) breaks a single trace down span by span.
- The wrong numbers come from the data model (mixed grains, fan traps), not from missing definitions. [mixed-grain-and-verified-queries](/en/developers/guides/ai-cookbook/mixed-grain-and-verified-queries/) covers the mixed-grain case; the `sv_diagnostics` snippet under [Related skills](#related-skills) covers joins.

## How it works

![How it works: Refine a semantic view from agent logs: triage, SME review, and verified queries](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/refinement-loop-from-agent-logs/assets/refinement-loop-from-agent-logs-01.png)

- **The trace is the log.** Every agent turn writes one trace to `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`, read per agent with `SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(db, schema, agent, 'CORTEX AGENT')`. A trace holds the question, the answer, each SQL statement the agent ran, and whether a verified query was used. Direct Cortex Analyst traffic (not through an agent) is logged separately and read with `SNOWFLAKE.LOCAL.CORTEX_ANALYST_REQUESTS('SEMANTIC_VIEW', '<view>')`; Analyst calls made by an agent are in the agent trace, not there. `CORTEX_AGENT_USAGE_HISTORY` is for cost and adoption and has no question text, so it can't drive this loop.
- **Triage sorts work; people judge answers.** `REFRESH_TRIAGE` labels each turn `NO_DATA` (said the data isn't there), `NO_TOOL` (answered without SQL), `GUESSED` (said it interpreted or assumed), `EXPLORED` (ran more than one query, usually to discover coded values), `VERIFIED` (used a verified query), or `ANSWERED`. These are text and count heuristics. A confident wrong answer looks exactly like a right one, so a random sample of `ANSWERED` turns goes to review too. In this example, that sample is what catches the Billing average reported over 42 tickets when only 20 were resolved.
- **The expert sees the question and the answer, never the SQL.** Their reply ("urgent means P1", "escalated means P1 or P2 and still open") is the raw material. The engineer translates it into the view.
- **Fix the view, not the agent, and not the client.** Each confirmed answer becomes a durable artifact in the semantic view, so every surface inherits it. The trace only records what reached the agent: instructions kept in an MCP client's system prompt or skills never reach it, aren't reviewable here, and don't help any other client.
- **Version every change.** `CHANGE_LOG` records each shipped change, its view version, and whose answer it came from. Triage labels every turn with the version that answered it, which gives a before and after on the same questions, and the log is the close-out note you send back to the experts.

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Cortex Agents and Cortex Analyst | The recipe role gets `SNOWFLAKE.CORTEX_USER`. |
| ACCOUNTADMIN | Only for the account statements in `01_example_setup.sql`, the grant in `02_grant_unredacted.sql`, and `99_teardown.sql`. |
| `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` | Account-level privilege. Without it the table functions return span names, tools, latency, and tokens, but the question and answer text is redacted and there is nothing to triage. A role that holds it can read every conversation with every agent it can monitor: grant it only to the small role that curates the semantic layer, after privacy review. |
| `MONITOR` (or `OWNERSHIP`) on the agent | The recipe role owns the agent. For your own agents, `GRANT MONITOR ON AGENT` or `GRANT MONITOR ON FUTURE AGENTS IN SCHEMA`. |
| Default role | The agent's Cortex Analyst tool runs as the caller. Make sure your default role inherits `COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS_ROLE` (setup grants it to you and to `SYSADMIN`). |

## Quickstart

Run in order:

1. [sql/01_example_setup.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/01_example_setup.sql): role, warehouse, database, 120 fictional tickets, the thin first-draft semantic view, the agent, and `CHANGE_LOG`.
2. [sql/02_grant_unredacted.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/02_grant_unredacted.sql): the account-level privilege that makes conversation text readable. Read the prerequisite above first.
3. [sql/03_generate_traffic.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/03_generate_traffic.sql): five questions through `DATA_AGENT_RUN`, one statement at a time. Wait about a minute.
4. [sql/04_triage.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/04_triage.sql): creates `REFRESH_TRIAGE`, builds `TRIAGE`, and prints the bucket counts, the review queue, and the list for the expert.
5. [sql/05_apply_refinements.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/05_apply_refinements.sql): the expert's answers as a `CREATE OR ALTER SEMANTIC VIEW`, the `CHANGE_LOG` entries, and a YAML round-trip check.
6. [sql/06_retest.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/06_retest.sql): the same five questions against the refined view, then the before and after comparison. Wait about a minute before its `CALL`.
7. [sql/99_teardown.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs/sql/99_teardown.sql).

## Walkthrough

### 1. Read one row per turn

`REFRESH_TRIAGE` is a caller's-rights procedure, so it only reads traces the calling role may monitor. Every name it uses arrives as a parameter: the agent goes to the table function as bind variables, and the change log is read with `IDENTIFIER(:CHANGE_LOG_TABLE)`. It writes `TRIAGE` to the caller's current schema. To point it at another agent, call it by its full name from a schema where your role can create a table, and pass that agent's change log, or `NULL` if its semantic view has none:

```sql
CALL COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS.SUPPORT.REFRESH_TRIAGE(
  'MY_DB', 'MY_SCHEMA', 'MY_AGENT', 7,
  'MY_DB.MY_SCHEMA.MY_CHANGE_LOG');   -- needs VIEW_VERSION and CHANGED_AT; or NULL
```

With `NULL`, `VIEW_VERSION` is empty and the window is the lookback alone. The core of the procedure groups spans by trace:

```sql
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(:AGENT_DB, :AGENT_SCHEMA, :AGENT_NAME, 'CORTEX AGENT'))
WHERE TIMESTAMP >= :since                       -- UTC; see Gotchas
...
MAX(IFF(SPAN = 'AgentV2RequestResponseInfo', A:"ai.observability.record_root.input"::VARCHAR,  NULL)) AS QUESTION,
MAX(IFF(SPAN = 'AgentV2RequestResponseInfo', A:"ai.observability.record_root.output"::VARCHAR, NULL)) AS ANSWER,
COUNT_IF(SPAN = 'SystemExecuteSQLTool_system_execute_sql')                                             AS SQL_RUNS,
BOOLOR_AGG(A:"snow.ai.observability.agent.tool.sql_execution.verified_query_used"::BOOLEAN)            AS USED_VERIFIED_QUERY
```

The documentation defines the table function, the event layout, and the `CORTEX_AGENT_FEEDBACK` record name for explicit feedback. The span and attribute names above are what the events hold today, not a documented contract, so `04_triage.sql` shows how to list them if a column comes back empty. Explicit thumbs up or down is a separate signal: [agent-feedback-to-evals](/en/developers/guides/ai-cookbook/agent-feedback-to-evals/) links feedback events to turns.

### 2. Triage the first-draft view

Against the thin view (every column present, descriptions like `'Priority.'`), three runs of the same five questions triaged the same way each time:

| Question | Bucket | What happened |
| --- | --- | --- |
| How many urgent tickets are still open? | GUESSED | Queried for `priority ILIKE 'urgent'`, got nothing, listed the values, then said it "interpreted urgent as the highest priority (P1)". The number (6) was right; the definition was a guess. |
| How many escalated tickets do we have for the Mobile App? | EXPLORED | Searched for an "Escalated" status, found none, and answered "no escalated tickets" or said the data has no escalated status. The support team's answer is 5. |
| How many tickets are waiting on the customer? | ANSWERED or EXPLORED | Found `PENDING_CUSTOMER`, sometimes after listing the status values. Right (30). |
| What is the average time to resolve Billing tickets? | ANSWERED | 19.25 hours, which is right, "based on 42 Billing tickets". Only 20 are resolved; the other 22 have no resolution time. |
| Which support engineer closed the most tickets? | NO_DATA | Said the data doesn't track engineers. Correct: a real scope gap. |

The `ANSWERED` Billing turn is the reason for the spot-check sample: no heuristic flags it, and a support lead reading "based on 42 tickets" would.

### 3. Route each finding to its fix

The trace tells you which part of the view to change. Each cause has a different fix:

| Symptom in the trace | Cause | Fix in the semantic view |
| --- | --- | --- |
| Filter on a literal that doesn't exist (`ILIKE 'urgent'`), then a query to list values | The words users say aren't mapped to the codes | Describe the codes in the column `COMMENT`; add `SAMPLE_VALUES`, and `IS_ENUM` when the list is closed |
| "No such status" for a business term | A business definition that lives in people's heads | A dimension or metric that encodes it (`is_escalated`), with the definition in its comment |
| Right SQL, misleading answer | The metric is correct but its population isn't stated | A companion metric (`resolved_ticket_count`) and an `AI_SQL_GENERATION` instruction to report it |
| The same question answered ad hoc every week | No verified query | Add it to `AI_VERIFIED_QUERIES`, with `ONBOARDING_QUESTION TRUE` for the ones new users should see |
| A question the view can't answer | Scope | `AI_QUESTION_CATEGORIZATION` to say so, or a different agent or view |
| Wrong view or tool chosen | Overlapping tool descriptions in the agent | Rewrite the agent's tool descriptions to be mutually exclusive |
| Wrong totals, not wrong words | The data model (grain, joins) | See [mixed-grain-and-verified-queries](/en/developers/guides/ai-cookbook/mixed-grain-and-verified-queries/) and the `sv_diagnostics` snippet |

For writing the descriptions themselves, [description-quality](/en/developers/guides/ai-cookbook/description-quality/) has a rubric and a linter. For pattern-level fixes (derived metrics, semi-additive metrics, time intelligence, range joins), use the `semantic-view-patterns` skill in apply mode rather than hand-writing them.

### 4. Ship the expert's answers

`05_apply_refinements.sql` applies all five answers in one `CREATE OR ALTER SEMANTIC VIEW`, which keeps existing grants and unsets anything omitted, so always send the full definition. The parts that came from the expert:

```sql
tickets.priority AS PRIORITY
  COMMENT = 'Priority code. P1 = urgent (highest), P2 = high, P3 = normal.'
  SAMPLE_VALUES ('P1', 'P2', 'P3') IS_ENUM,
tickets.is_escalated AS (PRIORITY IN ('P1', 'P2') AND STATUS = 'OPEN')
  COMMENT = 'TRUE for escalated tickets: priority P1 or P2 and still OPEN. ...',
...
tickets.resolved_ticket_count AS COUNT(hours_to_resolve)
  COMMENT = 'Number of RESOLVED tickets, the population behind AVG_HOURS_TO_RESOLVE.'
...
AI_SQL_GENERATION 'When reporting AVG_HOURS_TO_RESOLVE, also return RESOLVED_TICKET_COUNT ...'
AI_QUESTION_CATEGORIZATION 'This view has no assignee, engineer, or agent data. ...'
AI_VERIFIED_QUERIES (
  vq_urgent_open AS (
    QUESTION 'How many urgent tickets are still open?'
    VERIFIED_AT 1790640000
    ONBOARDING_QUESTION TRUE
    VERIFIED_BY '(STEWARD = support_operations)'
    SQL 'SELECT COUNT(ticket_id) AS urgent_open_tickets FROM tickets WHERE priority = ''P1'' AND status = ''OPEN'''
  ),
  vq_escalated_by_product AS ( ... )
)
```

`VERIFIED_BY` names a team contact, not a person. The same script then records the change in `CHANGE_LOG` as version `v1`, one row per answer, and prints the close-out list for the experts: which of their answers shipped, and as what. That message is what keeps them answering the next batch.

### 5. Keep the view in version control

Semantic views export as YAML (`SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW`) or DDL (`GET_DDL('SEMANTIC_VIEW', ...)`). Pick one format, commit it, and validate every change in CI with the four-argument procedure:

```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML('<db>.<schema>', $$ <yaml> $$,
  TRUE,    -- verify_only: validate, create nothing
  TRUE);   -- create_or_alter: CREATE OR ALTER semantics when you deploy with verify_only = FALSE
```

Without the fourth argument, the procedure replaces an existing view (`CREATE OR REPLACE ... COPY GRANTS`). `05_apply_refinements.sql` exports the refined view and validates the export with `TRUE, TRUE`. The exported YAML keeps the custom instructions under `module_custom_instructions` (`sql_generation`, `question_categorization`) and the verified queries under `verified_queries` with `verified_by`, `verified_at`, and `use_as_onboarding_question`.

### 6. Re-ask and compare

`06_retest.sql` sends the same five questions and rebuilds `TRIAGE`. In all three runs:

| Question | Before | After |
| --- | --- | --- |
| Urgent tickets still open | GUESSED, 2 to 3 queries | VERIFIED, 1 query: "6 urgent (P1) tickets" |
| Escalated tickets for the Mobile App | EXPLORED, "no escalated tickets" | VERIFIED, 1 query: "5 escalated tickets (P1 or P2 and still OPEN)" |
| Waiting on the customer | ANSWERED or EXPLORED | ANSWERED, 1 query: 30 |
| Average time to resolve Billing | "based on 42 Billing tickets" | "based on 20 resolved tickets" |
| Support engineer with most closures | NO_DATA | NO_DATA |

The escalated question matched `vq_escalated_by_product` even though it was phrased differently and filtered to one product. The urgent question matched its verified query word for word, which is the expected outcome for a recurring question; in production, judge the loop on next week's new questions, not only on replays.

### Who does what

- **Platform or analytics engineering** owns the semantic views, agents, and the triage cadence, and holds the unredacted privilege.
- **Subject matter experts and analysts** supply correct answers and definitions and are the contacts on verified queries. They don't review DDL.
- **Consumers** reach the agent through CoWork, an MCP client, or an app, and need no role beyond what the agent path requires.

Run the cycle weekly at first and monthly once the review queue shrinks. The output of each cycle is a change to the view, not a report.

## Verify

After `04_triage.sql`, the bucket counts cover exactly the five turns from `03`, all on `v0`:

```sql
SELECT VIEW_VERSION, BUCKET, COUNT(*) FROM COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS.SUPPORT.TRIAGE GROUP BY ALL;
-- v0 | five turns in total, for example ANSWERED 1-2 | EXPLORED 1-2 | GUESSED 0-1 | NO_DATA 1-2
```

Agent answers vary, so the split between buckets varies too. In one run the urgent question needed two queries and landed in `EXPLORED` rather than `GUESSED`, and the escalated question said the data has no escalated status and landed in `NO_DATA`.

The `CALL REFRESH_TRIAGE` result reads `5 turns since <time> UTC, 5 with question text`. If the second number is 0, the role lacks the unredacted privilege.

After `05`, the YAML check returns `YAML file is valid for creating a semantic view. No object has been created yet.` and `CHANGE_LOG` has six rows (one `v0`, five `v1`); rerunning `05` keeps it at six.

After `06`, the comparison shows the urgent and escalated questions moving to `VERIFIED` with `SQL_RUNS_AFTER = 1`, and the answers match the ground-truth row that the script prints: `URGENT_OPEN 6`, `ESCALATED_MOBILE_APP 5`, `WAITING_ON_CUSTOMER 30`, `AVG_HOURS_BILLING 19.25`, `RESOLVED_BILLING 20`. Agent answers vary between runs, so treat one run as a sample; the before and after pattern above held in every run while this recipe was built.

## Gotchas

| Symptom | Cause | Fix |
| --- | --- | --- |
| `QUESTION` and `ANSWER` are NULL, but turns are counted | The role lacks `READ UNREDACTED AI OBSERVABILITY EVENTS TABLE` | Run `02_grant_unredacted.sql` for the curating role only |
| Triage shows turns from an earlier run | Events outlive a dropped agent; a recreated agent with the same name sees them again | `REFRESH_TRIAGE` never reads earlier than the first row of the change log you pass; keep that row. With `NULL` only the lookback limits the window |
| A time window is off by several hours | The event `TIMESTAMP` is UTC `TIMESTAMP_NTZ` | Compare against `SYSDATE()`, not `CURRENT_TIMESTAMP()` |
| Triage is empty right after the questions | Traces arrive within about a minute | Wait, then `CALL REFRESH_TRIAGE` again |
| `SQL_RUNS` is 0 and `AGENT_SQL` is empty on every turn | Span or attribute names changed | List them with `SELECT DISTINCT RECORD:name FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_EVENTS(...))` and update the procedure |
| Wrong answers never reach review | They land in `ANSWERED`; heuristics can't see confident errors | Keep the random spot-check sample (`SPOT_CHECK`) |
| A description or instruction disappeared after a change | `CREATE OR ALTER` unsets anything omitted | Always apply the full definition from version control |
| A YAML deploy recreated the view | `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` without the fourth argument replaces the view | Pass `create_or_alter = TRUE` |
| Agent calls fail with privilege errors | The Cortex Analyst tool runs as the caller | The caller's role needs `SELECT` on the semantic view and its base tables |
| Business logic keeps drifting between clients | It lives in MCP client prompts or skills, which never reach the agent | Move it into the semantic view or the agent's instructions |

## Teardown

```sql
-- sql/99_teardown.sql
DROP ROLE IF EXISTS COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS_ROLE;      -- also removes the READ UNREDACTED grant
DROP DATABASE IF EXISTS COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS;       -- agent, semantic view, tables, procedure
DROP WAREHOUSE IF EXISTS COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS_WH;
```

The agent's events stay in `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS`: ingested rows can't be modified, and only a role with the `SNOWFLAKE.AI_OBSERVABILITY_ADMIN` application role can delete them for retention management.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable the semantic-view-patterns skill from Snowflake-Labs/coco-skills, and the bundled agent-studio skill.

Run the recipe in site/cortex-ai-cookbook/src/refinement-loop-from-agent-logs on my current Snowflake connection.
1. Confirm the account and role with SELECT CURRENT_ACCOUNT(), CURRENT_ROLE() and show me before continuing.
2. Show me the account-level statements at the top of sql/01_example_setup.sql (a role, a warehouse, a database,
   and their grants, run as ACCOUNTADMIN) and ask before running it. Then show me sql/02_grant_unredacted.sql and
   ask before running it: it grants an account-level privilege that exposes conversation text.
3. Run sql/03_generate_traffic.sql one statement at a time, wait a minute, then run sql/04_triage.sql.
   Report the bucket for each question and which answers you think are wrong, and why.
4. Run sql/05_apply_refinements.sql and sql/06_retest.sql (wait a minute before the CALL).
   Report the before and after table and check the answers against the ground-truth row.
5. Then apply the loop to one of my agents: from a schema where your role can create a table, CALL
   COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS.SUPPORT.REFRESH_TRIAGE('<db>', '<schema>', '<agent>', 7, NULL) with a
   role that has MONITOR on it (pass that view's change log instead of NULL if it has one), summarize the review
   queue, and propose semantic view changes as a diff. Use semantic-view-patterns in apply mode for any
   pattern-level fix. Do not deploy without asking.
6. Ask me before running sql/99_teardown.sql. Only drop objects named COOKBOOK_REFINEMENT_LOOP_FROM_AGENT_LOGS*.
```

## Related skills

- `semantic-view-patterns` (coco-skills): apply mode adapts a modeling pattern to your own view. The `ai_metadata` snippet teaches `AI_SQL_GENERATION`, `AI_QUESTION_CATEGORIZATION`, and `AI_VERIFIED_QUERIES`; `sv_diagnostics` covers joins that produce wrong numbers. Use it for the pattern-level fixes the loop identifies.
- `agent-studio` (bundled): creating, auditing, and optimizing semantic views, verified queries, and agents, including an agent observability report over the same event table.

## References

- [Monitor Cortex Agent requests](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-monitor)
- [AI_OBSERVABILITY_EVENTS table](https://docs.snowflake.com/en/sql-reference/local/ai_observability_events)
- [GET_AI_OBSERVABILITY_EVENTS (SNOWFLAKE.LOCAL)](https://docs.snowflake.com/en/sql-reference/functions/get_ai_observability_events-snowflake-local)
- [Account privilege READ UNREDACTED AI OBSERVABILITY EVENTS TABLE](https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/bcr-read-unredacted-ai-observability-events)
- [Cortex Analyst administrator monitoring](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/admin-observability)
- [CREATE SEMANTIC VIEW](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Using SQL commands to create and manage semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/sql)
- [SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML](https://docs.snowflake.com/en/sql-reference/stored-procedures/system_create_semantic_view_from_yaml)
- [Custom instructions in Cortex Analyst](https://docs.snowflake.com/en/user-guide/views-semantic/custom-instructions)
- [Cortex Analyst Verified Query Repository](https://docs.snowflake.com/en/user-guide/views-semantic/verified-query-repository)
- [Suggestions for semantic models and views](https://docs.snowflake.com/en/user-guide/views-semantic/verified-query-suggestions)
- [Optimize an existing semantic view or model with verified queries](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/analyst-optimization) (Preview)
- [Best practices for modeling semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-modeling)
