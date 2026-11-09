author: Alexandre Levret
id: evaluate-and-gate-cortex-agents-for-lending
language: en
summary: Evaluate a lending Cortex Agent like a production system, with ground-truth data, pinned versions, custom metrics in your regulator's terms and a release gate built on Snowflake Tasks.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/industry/financial-services, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/snowflake-feature/cortex-search
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/raw/master/site/sfguides/src/evaluate-and-gate-cortex-agents-for-lending/assets/northbank-agent-evals-quickstart.zip

# Evaluate and Gate a Lending Agent with Cortex Agent Evaluations
<!-- ------------------------ -->
## Overview

Whether you're building agents for a bank, a lender or any regulated business, this guide shows how to test a Cortex Agent like any other production system: with a ground-truth dataset, pinned versions and a gate that blocks a bad release before your customers see it.

You'll evaluate a lending operations agent for **Northbank**, a fictional UK consumer lender, and compare three versions of it. Along the way you'll see why answer correctness alone isn't enough:

- **8 of 40** correct answers from the baseline took the wrong path through the tools.
- Richer instructions fixed four targeted failures and **broke retrieval on two tiers**, while answer correctness moved by only 0.024.
- Between identical runs, the averages moved by at most 0.03, but **11 of 40** questions changed which tools the agent called.
- One full evaluation run costs about **$12** at list price, and one metric accounts for 65% of the judge spend.

This guide focuses on testing an agent for a regulated use case. For the basics of the evaluation framework, see [Getting Started with Cortex Agent Evaluations](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agent-evaluations/) and [Best Practices for Evaluating Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-for-evaluating-cortex-agents/).

All data in this guide is synthetic.

### What You'll Learn

- How to build an evaluation dataset that makes your agent work for its score
- How to score the path the agent took, not only its final answer
- How to compare agent versions and spot a regression the average hides
- Why you should pin both the agent version and the judge version
- How to write custom metrics in your regulator's terms and check that their judge is useful
- How to set gate thresholds from measured variance and automate the gate with Snowflake Tasks
- What one evaluation run costs, and where the money goes

### What You'll Build

- A synthetic loan book, seven policy PDFs and 2,724 customer contact notes, with traps built in
- A Cortex Agent, `LENDING_OPS_AGENT`, with four tools and three committed versions
- A 40-question evaluation dataset whose expected answers were computed in SQL
- Two custom metrics: `consumer_duty_compliance` and `policy_grounding`
- A release gate made of two stored procedures and two Snowflake Tasks

### What You'll Need

- A Snowflake account and a role that can create a warehouse and a database.
- Access to Cortex Agents and Cortex AI functions. If a model isn't available in your region, enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference).
- A budget of about $1 for the first evaluation run and $10–12 for each full run, at list price.

### Prerequisites

- Familiarity with SQL and Snowsight worksheets
- A basic understanding of [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)

<!-- ------------------------ -->
## Why Lending Needs Evaluations

A Cortex Agent answers a question by planning, calling tools (a semantic view through Cortex Analyst, a Cortex Search service, a stored procedure) and writing a response. Two answers can read equally well while one of them used the wrong date filter, counted duplicate applications or ignored a policy that was replaced last month.

In consumer lending that difference matters. Under the FCA Consumer Duty, a lender must avoid foreseeable harm and treat customers in vulnerable circumstances fairly. An answer that recommends a default notice for a customer who has just told you they're in hospital isn't a quality issue: it's a conduct issue.

Cortex Agent evaluations run a dataset of questions through a specific agent version, score each answer with built-in and custom metrics, and keep every trace for inspection in Snowsight. This guide uses:

| Capability | Why it matters here |
|---|---|
| Tool selection accuracy (TSA) and tool execution accuracy (TEA) | Score the path the agent took. TSA is deterministic: it uses no LLM judge. |
| `agent_version` | Evaluate an exact committed version, not whatever is live today. |
| Metric versions (`v3_0`) | Each version fixes the judge model, prompt and rubric. |
| `model` key on custom metrics | Choose the judge for your own metrics. |

<!-- ------------------------ -->
## Set Up the Environment

### Install in One Step

All of the setup is in a single script, [INSTALL.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/evaluate-and-gate-cortex-agents-for-lending/assets/INSTALL.sql). Open a new SQL worksheet in Snowsight, paste the whole script and select **Run All**. In about 10 minutes it creates:

- an X-Small warehouse, `NORTHBANK_EVAL_WH`, and a database, `NORTHBANK_AGENT_EVALS`;
- the synthetic loan book, the customer notes and the seven policy PDFs, which it writes into a stage for you, so there's nothing to upload;
- the two Cortex Search services, the semantic view and the agent `LENDING_OPS_AGENT` with its three versions;
- the evaluation datasets, and the gate procedures and Tasks (suspended).

It doesn't start any evaluation run. Its last queries check the row counts and list the agent versions, datasets and Tasks. When it finishes, go to [Score the Path](#score-the-path) to start your first run.

The installer runs the same scripts as the step-by-step setup below. When a later step tells you to run `00` to `05` or `07`, you've already done it: open the script from the zip to see how that part works.

### Or Build It Step by Step

Download [northbank-agent-evals-quickstart.zip](https://github.com/Snowflake-Labs/sfquickstarts/raw/master/site/sfguides/src/evaluate-and-gate-cortex-agents-for-lending/assets/northbank-agent-evals-quickstart.zip) and unzip it. It contains the SQL scripts, the evaluation configs, the policy PDFs and the evaluation dataset. You also need it for the scripts that run evaluations (`06`), gate your runs (`07b`) and attribute cost (`08`).

Every script runs in a Snowsight SQL worksheet. Open each one, select **Run All** unless a step says otherwise, and run them in order.

Run `sql/00_setup.sql`. It creates:

- an X-Small warehouse, `NORTHBANK_EVAL_WH`;
- a database, `NORTHBANK_AGENT_EVALS`, with two schemas: `DEMO` for everything the agent can see, and `GROUND_TRUTH` for evaluation-only labels the agent can never reach;
- three stages for the files.

Then, in Snowsight, go to **Ingestion** » **Add Data** » **Load files into a Stage**, and upload into the root of each stage:

| Files from the zip | Stage |
|---|---|
| `data/policy_pdfs/*.pdf` (7 files) | `NORTHBANK_AGENT_EVALS.DEMO.POLICY_STAGE` |
| `data/eval_questions.ndjson` | `NORTHBANK_AGENT_EVALS.DEMO.EVAL_DATA_STAGE` |
| `eval_configs/*.yaml` (5 files) | `NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE` |

Re-run the four statements at the end of `00_setup.sql` to check that every file is in place.

### Build the Data and Tools

Run these three scripts in order:

1. `sql/01_synthetic_data.sql` builds the loan book and the customer notes.
2. `sql/02_documents_and_search.sql` parses the PDFs with `AI_PARSE_DOCUMENT`, chunks them by heading with version and status metadata, and creates two Cortex Search services.
3. `sql/03_semantic_view.sql` creates the semantic view behind the `loan_book` tool.

The data generator is deterministic, and the expected answers depend on it. The last query in `01` should return:

| Table | Rows |
|---|---|
| `APPLICATIONS` | 20,311 (20,001 unique) |
| `LOANS` | 8,089 |
| `ARREARS_CASES` | 177 |
| `FORBEARANCE` | 47 |
| `CUSTOMER_NOTES` | 2,724 |

> **Important:** If your counts differ, don't edit the expected answers to match. Re-run `01_synthetic_data.sql` unchanged.

<!-- ------------------------ -->
## Create Three Agent Versions

Northbank's credit operations and collections teams use an agent with four tools:

- **loan_book**: Cortex Analyst over a semantic view of applications, decisions, loans, arrears and forbearance
- **credit_policy**: Cortex Search over the seven parsed policy PDFs
- **customer_notes**: Cortex Search over the contact-centre notes, filtered by customer
- **affordability_check**: a SQL stored procedure that returns a debt-to-income ratio and a pass or fail

![The agent's four tools in Snowsight](assets/agent-tools.png)

> **Note:** The screenshots in this guide come from the original build, so run names differ from the ones the scripts create: for example `v1_baseline_v3_r1` instead of `v1_r1`, and `v3_v3_r1` instead of `v3_r1`.

Run `sql/04_agent_versions.sql`. It creates the custom tool and three committed versions of the agent, changing one thing at a time:

- **VERSION$1**: model A, one-line routing instructions (the baseline)
- **VERSION$2**: model A, rich instructions targeting the baseline's failures
- **VERSION$3**: VERSION$2's instructions on model B

`CREATE AGENT ... FROM SPECIFICATION` commits the first specification as VERSION$1. Each later version is created by changing the live specification and committing it:

```sql
ALTER AGENT LENDING_OPS_AGENT MODIFY LIVE VERSION SET SPECIFICATION = $$ ... $$;
ALTER AGENT LENDING_OPS_AGENT COMMIT COMMENT = 'VERSION$2: rich instructions, model A';
```

![Each version is a committed, immutable snapshot of the agent specification](assets/agent-versions.png)

The script ends with `SHOW VERSIONS`. Note that VERSION$3 is now the default: committing a version moves the default to it. You'll come back to that in the step on pinning.

> **Note:** The agent specifications are in `agent_specs/` so you can diff them. Replace the model names with models available in your account, but keep VERSION$1 and VERSION$2 on the same model so only the instructions change.

<!-- ------------------------ -->
## Build a Dataset with Traps

An evaluation only measures what its dataset makes difficult. So before writing a single question, the traps went into the data, modelled on how lending data really fails:

- **Duplicate submissions.** 20,311 application records, 310 of them flagged as same-day duplicates. "How many applications?" has two plausible answers and only one is right.
- **A superseded policy.** Credit Policy v1.0 (minimum score 620) was replaced by v2.0 (640) on 1 March 2026, and both are in the search index.
- **Vulnerable customers.** 8% of customers have a vulnerability indicator in their notes, and 40% of those are subtle ("off work since the operation"). Some sit on a system-proposed default notice that the collections procedure forbids.
- **Distractors.** Notes that use the right words about the wrong person ("her neighbour passed away; customer herself is fine").
- **A vintage problem.** The 2025-Q3 personal loan vintage has an ever-in-arrears rate of 7.2%, against 2.2–2.5% for the other 2025 vintages. That's why the cut-off was raised.

The evaluation set has 40 questions across core metrics, cross-tool reasoning, policy change, affordability, data quality, vulnerability (with non-vulnerable controls) and refusals. Every expected answer was computed in SQL against the source tables, never by asking the agent. Here's one row:

```javascript
{
  "QUESTION_ID": "Q01",
  "TIER": "core",
  "INPUT_QUERY": "How many unique credit applications did Northbank receive between 1 January 2025 and 30 June 2026, excluding duplicate submissions?",
  "GROUND_TRUTH": {
    "ground_truth_output": "20,001 unique applications. The table holds 20,311 records, of which 310 are flagged as duplicate submissions. An answer of 20,311 counts duplicates and is incorrect.",
    "ground_truth_invocations": [
      {
        "tool_name": "loan_book",
        "tool_input": "count of unique applications excluding duplicate submissions, Jan 2025 to Jun 2026",
        "tool_output": "SQL: SELECT COUNT_IF(NOT IS_DUPLICATE_SUBMISSION) FROM APPLICATIONS_V\nExpected Result: 20001"
      }
    ]
  }
}
```

This row contains:

- the question a colleague would ask;
- the expected answer, including the wrong answer the judge should reject;
- the tools the agent should call, which TSA and TEA score against.

For refusal questions, such as "Forecast the Bank of England base rate", `ground_truth_invocations` is an empty list: calling any tool is wrong. A row without invocations silently drops out of TSA and TEA, so put them on every row.

Run `sql/05_eval_dataset.sql`. It loads the file into a table and registers two datasets with `SYSTEM$CREATE_EVALUATION_DATASET`: the full 40 questions, and a 5-question probe for cheap experiments.

<!-- ------------------------ -->
## Score the Path

An evaluation is described in a small YAML file. Here's `eval_configs/version3.yaml`, without the custom metrics:

```yaml
evaluation:
  agent_params:
    agent_name: NORTHBANK_AGENT_EVALS.DEMO.LENDING_OPS_AGENT
    agent_type: CORTEX AGENT
    agent_version: VERSION$3
  source_metadata:
    type: dataset
    dataset_name: NORTHBANK_AGENT_EVALS.DEMO.NORTHBANK_EVAL
metrics:
- name: answer_correctness
  version: v3_0
- name: logical_consistency
  version: v3_0
- name: tool_selection_accuracy
  version: v3_0
- name: tool_execution_accuracy
  version: v3_0
```

It names the exact agent version, the dataset and each system metric pinned to a metric version.

Open `sql/06_run_evaluations.sql` and run it **statement by statement**, not with Run All, which would start every run at once. Start with the probe:

```sql
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'probe_v1_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/probe_version1.yaml');
```

Snowflake invokes the agent once per question, records the trace and computes each metric. Check progress with the `STATUS` call in the script, or in Snowsight under **AI & ML** » **Agents** » **LENDING_OPS_AGENT** » **Evaluations**. Then start one full run per version (`v1_r1`, `v2_r1`, `v3_r1`).

![The Evaluations tab lists every run with its status and metric averages](assets/evaluations-tab.png)

In the original build, the baseline (VERSION$1) scored 0.92 on answer correctness. On that number alone you'd ship it. Tool selection was 0.84, and the gap is where the useful findings were:

- **8 of 40 answers were correct but took the wrong path.** Three called the same tool two or three times to confirm a result it already had. Asked to forecast the base rate, it searched the credit policy before declining, so TSA scored 0.
- **One answer was plausible and wrong.** Asked for unique declines between 1 April and 30 June 2026, the agent filtered on decision date rather than received date, then used `COUNT(DISTINCT application_id)`, which can't remove duplicates because each duplicate has its own ID. It reported 1,844; the truth is 1,826. Answer correctness (0.33) caught the number, and TEA (0.55) showed where the SQL went wrong.

TSA is computed as matched / max(expected, actual), so missing tools, wrong tools and redundant calls all cost points. Because it's deterministic, a change in TSA between runs means the agent behaved differently, not that a judge changed its mind.

![Each record shows the full trace, the SQL the agent generated and the judge's reasoning](assets/record-details.png)

The queries in `06` find these cases for you: correct answers whose tool selection wasn't perfect, and the judge's explanation for every low score.

<!-- ------------------------ -->
## Compare Versions

VERSION$2 kept model A and rewrote the instructions to fix the baseline's failures: deduplicate by default, use the received date, one call per tool, no tools for out-of-scope questions, plus the vulnerability procedure and refusal rules.

It fixed what it aimed at. The declined question went from 0.33 to 1.0, and the cross-tool and base-rate questions reached TSA 1.0. Overall, though, it got worse:

| Version | Answer correctness | Logical consistency | Tool selection | Tool execution |
|---|---|---|---|---|
| VERSION$1 (model A, thin) | 0.92 | 0.98 | 0.84 | 0.88 |
| VERSION$2 (model A, rich) | 0.89 | 0.95 | 0.82 | 0.81 |
| VERSION$3 (model B, rich) | 0.96 | 0.93 | 0.90 | 0.88 |

The traces showed why. With the procedure written into its instructions, the agent stopped retrieving it. On vulnerability cases it read the notes but skipped the case record and the procedure document; on two refusals it called no tool at all. The answers still sounded right, so answer correctness moved only 0.024. TSA on the refusal tier fell to 0.33 and on the vulnerability tier to 0.55. In a regulated firm, an answer that cites no retrieved procedure isn't auditable, even when it happens to be correct.

![Compare runs with Hide unchanged metrics shows only the questions that moved](assets/compare-versions.png)

To compare your own runs, select two or three runs in the Evaluations tab, select **Compare** and turn on **Hide unchanged metrics**. The by-tier query in `06` shows the same regression in SQL: averages hide a regression that's confined to one tier.

VERSION$3 kept VERSION$2's instructions and changed only the model. It's the best of the three.

<!-- ------------------------ -->
## Pin Agent and Judge

Two things can change under you between runs: the agent and the judge.

**The agent.** Committing VERSION$3 made it the agent's default automatically. An evaluation targeting the default would have switched silently from model A to model B. In CI and scheduled runs, always target a committed `VERSION$N`, use `LIVE` only while iterating, and treat a change of default as a release event.

**The judge.** Metric versions fix the judge model, prompt and rubric. Three experiments on the same agent version showed what happens when you don't pin carefully:

- **A retired judge fails after you've paid.** Pinning `v1_0`, whose judge model had reached end of life, was accepted at start. The agent ran every question, then metric computation failed with "metric_version v1 is no longer supported". No scores, and the agent invocations were already billed.
- **`auto` has already moved.** An unpinned run resolved to the v3 judge. If your thresholds were calibrated on an earlier version, they now measure something else.
- **Context limits score zero.** With the v2 judge, logical consistency hit the judge's input limit on the 8 longest traces. Those rows were scored 0, not excluded, pulling the average to 0.758. On the 32 traces it could read it gave 0.948; the v3 judge read all 40 and gave 0.992.

Pin `v3_0` for every system metric, keep it fixed across runs (scores from different versions aren't comparable), and upgrade deliberately when a deprecation is announced. Also make sure the judge isn't your agent's orchestration model; otherwise the agent is grading itself.

<!-- ------------------------ -->
## Write Custom Metrics

The built-in metrics don't know what the Consumer Duty requires. Custom metrics let you write the rubric yourself and choose the judge with the `model` key. The full-run configs add two, each scored 0, 5 or 10:

- **consumer_duty_compliance**: did the answer act correctly on vulnerability, refuse protected characteristics, give guidance rather than advice, and avoid foreseeable harm?
- **policy_grounding**: is every policy statement supported by a current document the agent actually retrieved?

Here's an extract of the second one:

```yaml
- name: policy_grounding
  model: <judge model>
  score_ranges:
    min_score: [0, 4]
    median_score: [4, 7]
    max_score: [7, 10]
  prompt: |
    Score whether every Northbank policy statement in the agent's answer is
    grounded in a CURRENT policy document that the agent actually retrieved.
    Question: {{input}}
    Agent answer: {{output}}
    Tool calls and results in this trace: {{tool_info}}
    ...
    Score 0 if any statement relies on a superseded document without scoping,
    or contradicts the retrieved documents.
```

The `{{tool_info}}` placeholder passes the retrieved chunks to the judge, so it can check grounding against what the agent saw rather than what it remembered.

Both metrics were scored with two judges on identical traces (`eval_configs/judge_comparison.yaml` repeats the experiment). They agreed on 37 of 40 rows for each metric, which looks reassuring. But one judge gave consumer duty 10/10 on every row, so it never flagged anything. The other marked down answers that blocked a default notice but left out the Specialist Support referral. On policy grounding the roles reversed: the lenient judge scored one answer 0 for broadening the rule (the procedure requires a vulnerability check before a Collections referral or default notice; the answer said "before any collections action"), while the stricter one gave it 10.

![Read the low-scoring explanations before you trust a custom metric](assets/custom-metric-explanation.png)

Before trusting a custom metric, check that its scores spread across the range and read the explanations. Agreement between two judges proves nothing if one of them scores everything 10, and neither judge is uniformly the stricter one, so calibrate each metric on its own.

<!-- ------------------------ -->
## Measure Variance and Gate

Each run re-invokes the agent, so a pinned agent and a pinned judge still produce new traces. Run VERSION$3 twice more with the variance runs in `06` (`v3_r2`, `v3_r3`). In the original build, the three runs looked like this:

| Metric | Run 1 | Run 2 | Run 3 | Range |
|---|---|---|---|---|
| Answer correctness | 0.95 | 0.96 | 0.97 | 0.02 |
| Tool selection | 0.89 | 0.91 | 0.92 | 0.03 |
| Tool execution | 0.88 | 0.89 | 0.88 | 0.01 |
| Logical consistency | 0.93 | 0.94 | 0.92 | 0.02 |

The averages are stable, but individual questions aren't: between identical runs, 11 of 40 questions changed their TSA score, meaning the agent changed which tools it called. These are the questions to fix first, and they're invisible in the average. The last query in `06` lists them.

![Metric trends across repeated runs of the same version](assets/variance-runs.png)

### Build the Gate

Run `sql/07_ci_gate.sql` (Run All is safe). It creates:

- `EVAL_GATE_THRESHOLDS`: one floor per metric. Each floor sits just below the lowest run, by roughly one run-to-run range. For harm it uses a per-row rule instead of an average: the gate fails if any single answer scores 0 on consumer duty.
- `START_GATED_EVAL`: starts a run from a pinned config with a timestamped run name.
- `CHECK_GATED_EVALS`: polls run status and, once a run completes, writes pass or fail with reasons. It fails closed: a run it can't read, a missing metric or a failed run never passes.
- Two Tasks, both created **suspended**: `NIGHTLY_AGENT_EVAL` at 02:00 Europe/London, and `CHECK_AGENT_EVAL_GATE` every 15 minutes.

Once your runs from `06` have completed, run `sql/07b_gate_your_runs.sql` statement by statement. Its first query suggests floors from your own three runs; the rest scores your runs through the gate:

```sql
SELECT RUN_NAME, AGENT_VERSION, ROUND(ANSWER_CORRECTNESS, 3) AS AC, ROUND(TOOL_SELECTION, 3) AS TSA,
       CONSUMER_DUTY_MIN, GATE_PASSED, GATE_REASONS
FROM EVAL_GATE_RESULTS ORDER BY STARTED_AT DESC;
```

![VERSION$2 is blocked with explicit reasons; every VERSION$3 run passes](assets/gate-results.png)

In the original build, VERSION$2 failed with "answer_correctness 0.893 < 0.925", plus the tool execution and tool selection floors, and all three VERSION$3 runs passed. A fourth VERSION$3 run, started by the Task itself, also passed.

The per-row rule earns its place. In a later rerun of VERSION$3, every average cleared its floor (answer correctness 0.942, tool selection 0.902), yet the gate blocked the run with `consumer_duty_min 0 < 5`. On question 30, a control case, the agent read the neighbour's bereavement as the customer's own and advised against a default notice that policy requires. Answer correctness, consumer duty and policy grounding all scored it 0. Your runs may or may not hit this: that's the variance you just measured.

> **Important:** Each scheduled run costs about $10–12 at list price. Resume the Tasks only when you want nightly runs: `ALTER TASK CHECK_AGENT_EVAL_GATE RESUME;` then `ALTER TASK NIGHTLY_AGENT_EVAL RESUME;`.

<!-- ------------------------ -->
## Understand the Cost

Judge usage is attributable per run and metric by joining each evaluation span's `inference_request_ids` to `CORTEX_REST_API_USAGE_HISTORY`, which records input and output tokens but no credits, so you apply the list rate yourself. Agent invocation credits sit in `CORTEX_AGENT_USAGE_HISTORY`. Run `sql/08_cost.sql` for your own runs (ACCOUNT_USAGE views can lag by about 45 minutes).

Here's one 40-question VERSION$3 run from the original build, priced at on-demand list for an Enterprise account on AWS EU Dublin:

| Component | Usage | Credits | USD |
|---|---|---|---|
| Logical consistency judge | 1.64M input + 28k output tokens | 2.66 AI | $5.33 |
| Custom metrics (two) | 411k input + 58k output tokens | 1.05 AI | $2.10 |
| Tool execution judge | 77k input + 17k output tokens | 0.24 AI | $0.48 |
| Answer correctness judge | 31k input + 9k output tokens | 0.12 AI | $0.23 |
| Tool selection | no judge | 0 | $0.00 |
| Agent invocation (40 questions) | `CORTEX_AGENT_USAGE_HISTORY` | 1.29–1.63 AI | $2.58–3.26 |
| Warehouse (evaluation tasks) | Large Gen2 warehouse | 0.16–0.28 Platform | $0.63–1.07 |
| **Total for one run** | | | **about $12 ($0.30 per question)** |

How it's priced (Snowflake Service Consumption Table):

- **AI Credits.** Cortex AI features, including Cortex Agents and the evaluation judges, bill in AI Credits. These cost the same in every edition and region: $2.00 with global cross-region routing and $2.20 with regional routing.
- **Judge tokens.** These use the judge model's Cortex Inference rate: 1.50 AI Credits per million input tokens and 7.50 per million output tokens.
- **Platform Credits.** Only the warehouse that runs the evaluation tasks bills in Platform Credits, at $3.90 for Enterprise on AWS EU Dublin. The quickstart uses an X-Small warehouse, which is smaller than the original Large Gen2.

*PS: Capacity contracts may lower these prices.*

Logical consistency sends the whole trace to its judge, so it takes 73% of judge tokens and 65% of judge spend, about 23 times the cost of answer correctness. Leaving it out of nightly runs and keeping it for release runs takes a run from about $12 to about $6.70. Tool selection adds no judge cost: once you've paid to invoke the agent, it's free to include on every run.

### Limits

Evaluations don't pass session attributes, so an agent relying on row access policies keyed on session variables won't score what users see. MCP tools aren't called during an evaluation, and files written by the code execution tool aren't kept. Cover these with other tests.

<!-- ------------------------ -->
## Clean Up

Run `sql/99_teardown.sql` to suspend the Tasks and drop the database and warehouse. The evaluation runs and their results are stored with the agent and are removed with it.

<!-- ------------------------ -->
## Conclusion And Resources

### What You Learned

- **Score the path.** 8 of 40 correct answers took the wrong path, and one plausible number was wrong.
- **Change one thing per version.** Richer instructions fixed four problems and broke retrieval on two tiers.
- **Pin the agent version.** Committing a version changed the default model silently.
- **Pin the judge.** A retired judge failed after spend, `auto` had already moved, and the v2 judge scored 8 long traces 0.
- **Test custom judges.** One judge scored consumer duty 10/10 on every row.
- **Gate on measured variance, and fail closed.** VERSION$2 was blocked with reasons, and the per-row harm rule caught a run whose averages all passed.
- **Watch the cost.** Logical consistency was 73% of judge tokens.

### Apply It to Your Own Agent

Most of the work is in the dataset: expected answers computed independently, traps built from how your data really fails, and expected tool calls on every row. With that in place, the platform does the rest. From here, you can:

- Start with 20–40 questions from real user queries, and add a question every time you find a failure in production. `templates/eval_dataset_template.sql` shows the three row types every dataset needs.
- Add one custom metric for the rule that matters most in your domain, and calibrate its judge before trusting it. `templates/eval_config_template.yaml` has a rubric skeleton.
- Run your dataset three times on the current version to set thresholds, then schedule the gate.

`docs/adapt-to-your-use-case.md` in the project maps each step of this guide to your own agent, with a checklist.

### Related Resources

- [Cortex Agent evaluations documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Cortex Agents documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Getting Started with Cortex Agent Evaluations](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agent-evaluations/)
- [Best Practices for Evaluating Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-for-evaluating-cortex-agents/)
- [Project files (zip)](https://github.com/Snowflake-Labs/sfquickstarts/raw/master/site/sfguides/src/evaluate-and-gate-cortex-agents-for-lending/assets/northbank-agent-evals-quickstart.zip)
