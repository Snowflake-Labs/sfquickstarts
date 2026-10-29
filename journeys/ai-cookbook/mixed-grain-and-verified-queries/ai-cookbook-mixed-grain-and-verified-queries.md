sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy
id: ai-cookbook-mixed-grain-and-verified-queries
categories: snowflake-site:taxonomy/product/ai
language: en
summary: An agent double-counts a table that holds daily and monthly rows. Diagnose it from wrong answers, fix the semantic view with a GRAIN enum, rules, and verified queries, re-test.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries

# Mixed-grain tables: diagnose and fix wrong agent answers with a GRAIN dimension and verified queries

## Overview

Many summary tables store more than one grain side by side: daily rows next to monthly roll-ups, districts next to
their region totals. Point a semantic view at one of these without saying so, and a Cortex Agent returns fluent,
confident answers that are exactly twice the truth. This recipe reproduces that failure on a small fictional dataset,
scores the agent on four questions (it gets 0 or 1 right), traces the wrong numbers to the SQL it wrote, and fixes
the semantic view, not the agent and not the data, until the same agent gets all four right.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Build, Evaluate |
| Topics | Semantic Views, Cortex Agents |
| Time | 30 min |
| Edition | Any edition with semantic views and Cortex Agents |
| Regions | Regions where Cortex Agents and Cortex Analyst are available |
| Privileges | ACCOUNTADMIN for the account statements in 01_setup.sql and for teardown; everything else runs as COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_ROLE |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bmixed-grain-and-verified-queries%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fmixed-grain-and-verified-queries) |

## When to use this

- An agent or Cortex Analyst answer is off by a clean multiple (2x, 3x), or an average is skewed high.
- A table mixes row types (daily and monthly, detail and subtotal, account and account group) and the rows share
  keys and dates.
- You want a repeatable before and after test for a semantic view change instead of spot-checking in a chat.

When not to use it:

- You can change the data model. Splitting the grains into separate tables (or a view per grain) removes the trap
  entirely; do that when you can.
- The wrong numbers come from joins (fan traps, multiple paths). That is a relationship problem; see the
  `sv_diagnostics` snippet under [Related skills](#related-skills).

## How it works

![How it works: Mixed-grain tables: diagnose and fix wrong agent answers with a GRAIN dimension and verified queries](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/mixed-grain-and-verified-queries/assets/mixed-grain-and-verified-queries-01.png)

- **The trap.** `STORE_SALES_SUMMARY` has 360 daily rows and 12 monthly rows that each equal the sum of their month.
  Only `PERIOD_START = PERIOD_END` tells them apart. A first-draft semantic view that calls `PERIOD_START` "sale
  date" invites `SUM(net_sales) WHERE sale_date BETWEEN ...`, which adds every sale twice.
- **Test through the agent, score against the data.** Expected answers are computed from the daily rows in setup.
  The harness asks the agent each question with `DATA_AGENT_RUN`, stores the answer and the SQL the agent wrote, and
  scores it: numbers within 0.5 percent, or an `AI_COMPLETE` judge for the "which stores" question.
- **Fix the semantic view only.** A `GRAIN` dimension with `IS_ENUM` names the row types, grain rules in
  `AI_SQL_GENERATION` say which grain answers which kind of question, and a few verified queries show the right shape.
  The agent spec is never touched.
- **Verified queries that differ from the test.** The verified queries use other stores and months than the test
  questions, so a passing re-test shows the rules generalize rather than that a stored query was replayed.
- **`CREATE OR ALTER` keeps grants.** The fix is applied in place; the analyst role's `SELECT` grant on the view is
  still there afterwards.

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Cortex Agents and Cortex Analyst | The recipe role gets `SNOWFLAKE.CORTEX_USER`. |
| ACCOUNTADMIN | Only for the account statements at the top of `01_setup.sql` and for `99_teardown.sql`. |
| Default role | Agents run with the calling user's default role. Make sure it inherits `COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_ROLE` (setup grants the role to you and to `SYSADMIN`). |
| Judge model | `claude-sonnet-4-6` scores the one list question (`MODEL` in `04` and `07`). |
| Orchestration model | `auto` (`AGENT_MODEL` in `03`). The script checks the name against a pattern before it goes into the agent specification. |

## Quickstart

Run in order. Each script sets its own role, warehouse, and database, so separate `snow sql -f` calls work:

1. [sql/01_setup.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/01_setup.sql): roles, warehouse, database, the mixed-grain table, and the test questions.
2. [sql/02_semantic_view_before.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/02_semantic_view_before.sql): the first-draft semantic view and an analyst grant.
3. [sql/03_agent_and_test_harness.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/03_agent_and_test_harness.sql): the agent and `RUN_AGENT_TESTS`.
4. [sql/04_test_before.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/04_test_before.sql): score the agent (a few minutes).
5. [sql/05_diagnose.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/05_diagnose.sql): find the cause.
6. [sql/06_fix_semantic_view.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/06_fix_semantic_view.sql): apply the fix with `CREATE OR ALTER`.
7. [sql/07_test_after.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/07_test_after.sql): re-score the same agent and compare.
8. [sql/99_teardown.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries/sql/99_teardown.sql).

## Walkthrough

### 1. The questions and the right answers

| ID | Question | Correct answer |
| --- | --- | --- |
| Q1 | Total net sales for Harbor Street in February 2026 | 35,713.00 |
| Q2 | Total net sales across all stores in Q1 2026 | 439,348.35 |
| Q3 | Average daily net sales for Canal Park in January 2026 | 1,543.90 |
| Q4 | Which stores missed their March 2026 sales target | Elm Square, Mill Road |

### 2. The symptom

Against the first-draft view, two test runs scored 1 of 4 and 0 of 4. Q1 and Q2 were wrong the same way both times;
Q3 is from the first run and Q4 from the second:

| ID | Agent answer | Ratio to correct |
| --- | --- | --- |
| Q1 | $71,426.00 | 2.00 |
| Q2 | $878,696.70 | 2.00 |
| Q3 | $2,991.30 | 1.94 |
| Q4 | "No stores missed their March 2026 sales target. All four stores exceeded their targets." | wrong |

Nothing in the answers signals a problem. Q4 is the most damaging: doubled sales against single-counted targets make
every store look like it beat plan. In the first run the agent noticed an empty result on Q4, investigated, and got
it right, which is why a scored test beats a single spot check.

### 3. The diagnosis

`05_diagnose.sql` goes from symptom to cause. The ratios above are the first clue: a SUM that is off by exactly 2.00
is two grains added together. The SQL the agent wrote confirms it, with a date filter and no grain filter:

```sql
SELECT SUM(net_sales) AS total_net_sales
FROM __sales
WHERE store_name ILIKE '%Harbor Street%'
  AND sale_date >= '2026-02-01' AND sale_date < '2026-03-01'
```

And the table itself shows the two grains, each summing to the full total:

| IMPLICIT_GRAIN | ROWS | NET_SALES | ROWS_WITH_TARGET |
| --- | --- | --- | --- |
| DAILY | 360 | 439,348.35 | 0 |
| MONTHLY | 12 | 439,348.35 | 12 |

### 4. The fix

`06_fix_semantic_view.sql` replaces the definition in place. The parts that matter for grain:

```sql
sales.grain AS IFF(PERIOD_START = PERIOD_END, 'DAILY', 'MONTHLY')
  COMMENT = 'Row type. DAILY = one store, one day. MONTHLY = one store, one calendar month, equal to the sum
             of that month''s DAILY rows, and the only rows with SALES_TARGET. Every query must filter to exactly one GRAIN.'
  SAMPLE_VALUES ('DAILY', 'MONTHLY')
  IS_ENUM,
...
AI_SQL_GENERATION
  '... Every query must filter to exactly one grain; never aggregate across both. Totals for whole calendar months,
   quarters, or years: use MONTHLY rows. Anything about targets: use MONTHLY rows. Daily figures, averages per day,
   or partial-month ranges: use DAILY rows. ...'
AI_VERIFIED_QUERIES (
  vq_store_month_total AS (
    QUESTION 'What were total net sales for Mill Road in January 2026?'
    VERIFIED_BY '(STEWARD = retail_analytics)'
    SQL 'SELECT store_name, period_start AS month, net_sales FROM sales
          WHERE grain = ''MONTHLY'' AND store_name = ''Mill Road'' AND period_start = ''2026-01-01''' ),
  ...
)
```

Also in the fix: the misleading `sale_date` name becomes `period_start` plus `period_end`, every fact and metric
comment states which grain it is valid in, and store and region get `IS_ENUM` sample values. `VERIFIED_BY` names a
team contact, not a person. Synonyms are limited to the two terms users actually use for the grain.

### 5. The re-test

The same agent, the same four questions, both test runs: 4 of 4. The agent's SQL now filters on `grain` every time,
and picks the grain the rules call for:

```sql
-- Q2: quarter total from monthly rows
SELECT SUM(net_sales) FROM __sales WHERE grain = 'MONTHLY' AND period_start BETWEEN '2026-01-01' AND '2026-03-01'
-- Q3: daily average from daily rows
SELECT AVG(net_sales) FROM __sales WHERE grain = 'DAILY' AND store_name = 'Canal Park' AND period_start BETWEEN '2026-01-01' AND '2026-01-31'
-- Q4: target comparison on the monthly row
SELECT store_name, net_sales, sales_target FROM __sales WHERE grain = 'MONTHLY' AND period_start = '2026-03-01' AND net_sales < sales_target
```

None of the test questions matched a verified query word for word.

## Verify

`07_test_after.sql` ends with a summary:

| RUN_LABEL | CORRECT | QUESTIONS |
| --- | --- | --- |
| before | 0 or 1 | 4 |
| after | 4 | 4 |

and the side-by-side table shows each answer and the agent's SQL. Also check that the grant survived:

```sql
SHOW GRANTS ON SEMANTIC VIEW COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES.RETAIL.STORE_SALES_SV;
-- SELECT ... COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_ANALYST
```

Agent answers vary between runs, so treat a single run as a sample. The "after" result was 4 of 4 in every run
while this recipe was built.

## Gotchas

| Symptom | Cause | Fix |
| --- | --- | --- |
| Answers off by exactly 2x (or Nx) | Two (or N) grains summed together | Add a `GRAIN` enum and rules; better, split the grains in the data model |
| Averages skewed high but not by a round number | Roll-up rows averaged together with detail rows | Rules: per-day averages use the detail grain only |
| "All stores beat target" | Doubled actuals compared with single-counted targets | Targets live on one grain; say so in the column comment and the rules |
| Fix passes only the exact verified questions | Verified queries doing the work, not the rules | Keep test questions different from verified queries, as here |
| `DATA_AGENT_RUN` in a procedure fails with "needs to be constant" | The request body was built inline | Build the body into a variable, then pass `:body` |
| Agent calls fail with privilege errors | Agents use the user's default role | Grant the recipe role to the default role |
| Grants disappear after a fix | `CREATE OR REPLACE` without `COPY GRANTS` | Use `CREATE OR ALTER SEMANTIC VIEW` |

## Teardown

```sql
-- sql/99_teardown.sql
DROP DATABASE IF EXISTS COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES;     -- agent, semantic view, tables, procedure
DROP WAREHOUSE IF EXISTS COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_WH;
DROP ROLE IF EXISTS COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_ANALYST;
DROP ROLE IF EXISTS COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES_ROLE;
```

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable the semantic-view-patterns skill from Snowflake-Labs/coco-skills, and the bundled agent-studio skill.

Run the recipe in site/cortex-ai-cookbook/src/mixed-grain-and-verified-queries on my current Snowflake connection.
1. Confirm the account and role with SELECT CURRENT_ACCOUNT(), CURRENT_ROLE() and show me before continuing.
2. Show me the ACCOUNTADMIN statements at the top of sql/01_setup.sql (two roles, a warehouse, a database, and
   their grants) and ask before running them. Then run sql/01 through sql/04 in order. Report the before score and
   each wrong answer.
3. Run sql/05_diagnose.sql and explain the cause in two sentences using its output.
4. Run sql/06 and sql/07. Report the after score and show the agent SQL for each question.
5. Then apply the same approach to one of my semantic views: use semantic-view-patterns in apply mode with the
   ai_metadata and sv_diagnostics snippets to check it for mixed grains, and propose a GRAIN dimension, rules, and
   verified queries as a diff. Do not deploy without asking.
6. Ask me before running sql/99_teardown.sql. Only drop objects named COOKBOOK_MIXED_GRAIN_AND_VERIFIED_QUERIES*.
```

## Related skills

- `semantic-view-patterns` (coco-skills): the `ai_metadata` snippet teaches `AI_SQL_GENERATION`,
  `AI_QUESTION_CATEGORIZATION`, and `AI_VERIFIED_QUERIES` syntax; the `sv_diagnostics` snippet covers other ways
  semantic views produce wrong numbers (fan traps, multiple paths). Apply mode adapts either to your own view.
- `agent-studio` (bundled): creating, auditing, and optimizing semantic views, verified queries, and agents.

## References

- [Using SQL commands to create and manage semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/sql)
- [CREATE SEMANTIC VIEW](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Best practices for modeling semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-modeling)
- [Optimize an existing semantic view or model with verified queries](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/analyst-optimization)
- [Create and manage agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
