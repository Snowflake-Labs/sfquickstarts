# Northbank agent evals quickstart

Evaluate a Cortex Agent like any other production system: a ground-truth dataset, pinned agent and judge versions, custom metrics in your regulator's terms, and a gate that blocks a bad release.

This project is the companion to the Snowflake Developer Guide **Evaluate and gate a lending agent with Cortex Agent evaluations**. You build the same agent for **Northbank**, a fictional UK consumer lender, run the same evaluations, and get a set of templates for applying the method to your own agent.

All data is synthetic. Everything runs in a Snowsight SQL worksheet; no local tools are needed.

## What you'll build

```
                        ┌──────────────────────────────┐
  colleague question →  │  LENDING_OPS_AGENT agent   │  VERSION$1 → $2 → $3
                        └──┬─────────┬────────┬──────┬─┘
                           │         │        │      │
             loan_book ────┘         │        │      └──── affordability_check
    (Cortex Analyst over a     credit_policy  customer_notes   (SQL procedure:
     semantic view)            (Cortex Search (Cortex Search    debt-to-income
                               over 7 PDFs)   over 2,724 notes) pass/fail)

  40 questions with SQL-computed ground truth ──► EXECUTE_AI_EVALUATION ──► gate (Tasks)
```

- A loan book with traps: duplicate submissions, missing incomes, a superseded credit policy, a 2025-Q3 arrears spike, vulnerable customers, and notes that use the right words about the wrong person.
- An agent with three committed versions that change one thing at a time:
  - **VERSION$1**: the baseline.
  - **VERSION$2**: richer instructions on the same model.
  - **VERSION$3**: the same instructions on a different model.
- A dataset of 40 questions. Every expected answer was computed in SQL against the source tables, and every row lists the tools the agent should call.
- Two custom metrics, `consumer_duty_compliance` and `policy_grounding`.
- A CI gate built from two stored procedures and two Tasks.
- Cost attribution per run and per metric.

## Prerequisites

- A Snowflake account where you can use a role that creates warehouses and databases. A sandbox with `ACCOUNTADMIN` is simplest.
- Access to Cortex Agents and Cortex AI functions. If the models below aren't available in your region, enable cross-region inference (step 0 shows how).
- Budget: about **$1** for the probe run and **$10–12** per full 40-question run, at list price. See [What it costs](#what-it-costs).

## Quickstart

Run the scripts in `sql/` in order. Open each in a Snowsight worksheet and use **Run All**, except:

- **06** and **07b**: run these statement by statement. Run All on 06 would start every evaluation at once, and 07b needs those runs to have finished.

Step 0 also needs a file upload: after running it, upload `data/policy_pdfs/*.pdf`, `data/eval_questions.ndjson` and `eval_configs/*.yaml` to the three stages it creates (the end of the script lists which file goes where).

| Step | Script | What it does | Time |
|---|---|---|---|
| 0 | [`00_setup.sql`](sql/00_setup.sql) | Warehouse, database, schemas and stages; then upload the PDFs, questions and configs | 2 min |
| 1 | [`01_synthetic_data.sql`](sql/01_synthetic_data.sql) | Deterministic loan book and customer notes | 1 min |
| 2 | [`02_documents_and_search.sql`](sql/02_documents_and_search.sql) | Parses the PDFs with `AI_PARSE_DOCUMENT`, chunks them, creates 2 Cortex Search services | 2–3 min |
| 3 | [`03_semantic_view.sql`](sql/03_semantic_view.sql) | Semantic view for the `loan_book` tool | seconds |
| 4 | [`04_agent_versions.sql`](sql/04_agent_versions.sql) | Custom tool and the agent's VERSION$1, $2 and $3 | 1 min |
| 5 | [`05_eval_dataset.sql`](sql/05_eval_dataset.sql) | Loads the 40 questions and registers two datasets (full and 5-question probe) | seconds |
| 6 | [`06_run_evaluations.sql`](sql/06_run_evaluations.sql) | Probe run, one run per version, variance runs; comparison queries | 10–20 min per run |
| 7 | [`07_ci_gate.sql`](sql/07_ci_gate.sql) | Gate tables, thresholds, procedures and two suspended Tasks | 1 min |
| 7b | [`07b_gate_your_runs.sql`](sql/07b_gate_your_runs.sql) | Floors from your own variance runs; gates the runs from step 6 | seconds |
| 8 | [`08_cost.sql`](sql/08_cost.sql) | Judge tokens, agent credits and warehouse credits per run, in USD | seconds |
| – | [`99_teardown.sql`](sql/99_teardown.sql) | Removes everything | seconds |

### Expected row counts

The data generator is deterministic, and the expected answers depend on it. After step 1 you should see:

| Table | Rows |
|---|---|
| `APPLICATIONS` | 20,311 (20,001 unique) |
| `LOANS` | 8,089 |
| `ARREARS_CASES` | 177 |
| `FORBEARANCE` | 47 |
| `CUSTOMER_NOTES` | 2,724 |

If your counts differ, don't edit the expected answers to match: re-run step 1 unchanged.

### Where to look in Snowsight

**AI & ML › Agents › LENDING_OPS_AGENT**:

- **Versions:** the three committed versions, and which one is the default.
- **Evaluations:** every run, with metric trend charts.
  - Select a run and a question to see the full trace, the SQL the agent generated and each judge's explanation.
  - Select two or three runs and **Compare**, then turn on **Hide unchanged metrics**.

## What to look for

These are the findings from the original build described in the guide. Your numbers will differ slightly from run to run (that's the point of step 6), but the patterns should reproduce.

| Practice | What the evaluation showed |
|---|---|
| Score the path, not only the answer | VERSION$1 got 0.92 answer correctness but 0.84 tool selection: 8 of 40 correct answers took the wrong path |
| Change one thing per version | VERSION$2's richer instructions fixed the targeted failures but stopped the agent retrieving the procedure; the vulnerability tier's tool selection fell to 0.55 |
| Pin the agent version | Committing VERSION$3 made it the default automatically (step 4 shows it) |
| Pin the judge | A retired judge fails after the agent has run; `auto` moves when models are deprecated |
| Test custom judges | One judge scored consumer duty 10/10 on every row; check the spread before you trust a metric |
| Measure variance | Averages moved by up to 0.025 between identical runs, but 11 of 40 questions changed tool path |
| Gate on measured ranges and fail closed | VERSION$2 is blocked with reasons; VERSION$3 passes |

The gate's per-row harm rule matters more than the averages. In one rerun of VERSION$3 while testing this repo, every average cleared its floor (answer correctness 0.942, tool selection 0.902), yet the gate still blocked the run with `consumer_duty_min 0 < 5`.

- **The question:** Q30, a control case.
- **The trap:** the customer's note says her neighbour died and that she herself is fine.
- **What the agent did:** it read the note as the customer's own bereavement and advised against a default notice that policy requires.
- **How it was scored:** answer correctness, consumer duty and policy grounding all gave it 0.

Your runs may or may not hit this. That's the variance step 6 measures.

## What it costs

Measured on one 40-question VERSION$3 run, priced at on-demand list for an Enterprise account on AWS EU Dublin. Cortex AI features bill in AI Credits ($2.00 with global routing, $2.20 regional, in every edition and region). The warehouse bills in Platform Credits ($3.90 in this example).

| Component | USD |
|---|---|
| Logical consistency judge | $5.33 |
| Custom metrics (two) | $2.10 |
| Tool execution judge | $0.48 |
| Answer correctness judge | $0.23 |
| Tool selection | $0 (no judge) |
| Agent invocation (40 questions) | $2.58–3.26 |
| Warehouse | about $0.63 |
| **Total** | **about $12, or $0.30 per question** |

`08_cost.sql` reproduces this breakdown for your own runs. Logical consistency costs the most because it sends the whole trace to its judge; consider leaving it out of nightly runs and keeping it for release runs.

## Use it for your own agent

[`docs/adapt-to-your-use-case.md`](docs/adapt-to-your-use-case.md) maps each step to your own agent. These templates go with it:

- [`templates/eval_dataset_template.sql`](templates/eval_dataset_template.sql): the three row types every dataset needs (known answer, multi-tool, refusal).
- [`templates/eval_config_template.yaml`](templates/eval_config_template.yaml): pinned versions and a custom-metric skeleton.

## Choosing models

The agent specs and custom metrics name the models used in the original build:

- **Agent orchestration** in `sql/04_agent_versions.sql` and `agent_specs/`: model A for VERSION$1 and VERSION$2, model B for VERSION$3.
- **Custom-metric judges** in `eval_configs/*.yaml`, under the `model` key.

Replace them with models available in your account. The method doesn't depend on which models you choose, as long as you:

- keep VERSION$1 and VERSION$2 on the same model;
- pin system metrics to a metric version (`v3_0`);
- use a judge that isn't your agent's orchestration model.

## Privileges

To run evaluations, the role needs:

- one of the Cortex database roles listed in the docs, for example `SNOWFLAKE.CORTEX_USER` or `SNOWFLAKE.CORTEX_AGENT_USER`;
- `EXECUTE TASK ON ACCOUNT`;
- `USAGE` on the database, schema and warehouse;
- `CREATE FILE FORMAT` and `CREATE TASK` on the schema;
- `USAGE` and `MONITOR` on the agent;
- `READ` on the config stage;
- access to every tool the agent uses.

See [Cortex Agent evaluations: access control](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations).

## Limits to know about

- Evaluations don't pass session attributes, so agents that rely on row access policies keyed on session variables won't score what users see.
- MCP tools aren't called during an evaluation, and files written by the code execution tool aren't kept.
- Tool selection and execution accuracy cover Cortex Analyst, Cortex Search, web search and custom tools.

## Repository layout

```
sql/              00–08 quickstart scripts, 99 teardown
eval_configs/     evaluation YAML read by EXECUTE_AI_EVALUATION (probe, one per version, judge comparison)
agent_specs/      the three agent specifications, for reading and diffing
data/             policy PDFs and the 40-question dataset with ground truth
generators/       Python that produced the PDFs and the dataset (optional; needs reportlab)
templates/        starting points for your own dataset and evaluation config
docs/             adapting the method to your use case
scripts/          optional local runner (Python connector)
SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, LICENSE
```

## Learn more

- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Cortex Agent versioning](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-versioning)
- [Snowflake AI pricing](https://docs.snowflake.com/en/user-guide/snowflake-cortex/pricing)

## Licence

Apache 2.0. See [LICENSE](LICENSE). This is sample code, not a supported Snowflake product.
