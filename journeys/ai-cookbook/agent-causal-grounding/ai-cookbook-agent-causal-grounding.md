sidebar: true
sidebar_json: ai-cookbook
author: Chris Caudill
id: ai-cookbook-agent-causal-grounding
categories: snowflake-site:taxonomy/product/ai
language: en
summary: A Cortex Agent whose every number comes from a persisted causal estimator, and which declines to answer for cohorts where no honest estimate exists.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/agent-causal-grounding

# Causally grounded Cortex Agent that refuses when the data cannot answer

## Overview

A Cortex Agent that answers "who should we treat, and what will it get us", where
every number it quotes comes from a causal estimator and it declines to answer when
the data cannot support one. The agent is the deliverable. The machinery underneath
it (propensity models, a doubly-robust ATE, a causal forest, a
difference-in-differences check and a dowhy refutation suite) is what makes the
answers provable. It plays the part a semantic view plays for Cortex Analyst: the
grounding layer that decides whether an answer is trustworthy at all. Everything
runs inside Snowflake on a plain XSMALL warehouse, with no compute pool and no
Snowpark Container Services.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Build, Evaluate |
| Topics | Cortex Agents, Semantic Views |
| Time | 90 min |
| Edition | Any edition with Cortex Agents |
| Regions | Any region with Cortex Agents; warehouse Python 3.11 with the Anaconda channel and the Snowflake PyPI artifact repository |
| Privileges | One build role with CREATE DATABASE and CREATE WAREHOUSE on the account plus SNOWFLAKE.CORTEX_USER runs every script, teardown included; the optional sql/10_agent_user_role.sql also switches to ACCOUNTADMIN for CREATE ROLE and the SNOWFLAKE.CORTEX_AGENT_USER grant |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/agent-causal-grounding) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bagent-causal-grounding%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fagent-causal-grounding) |

## When to use this

A risk model tells you **who will have a bad outcome**. It does not tell you **who
you can help**. Those are different rankings, and acting on the first one, which is
what nearly every intervention program does, spends a fixed budget on units that
cannot benefit.

Point a text-to-SQL agent at the same tables and it gets that wrong in a specific,
confident way. On the bundled fixture the raw treated-versus-untreated difference is
**+0.0846** when the true effect is **-0.0452**. The SQL is valid, the number is
really in the data, and the sign is inverted. An agent with no notion of confounding
will report it and sound certain. This recipe is about what you have to build for
the answers to be correct, and for the agent to know when to stop talking.

Use it when:

- The agent answers intervention questions ("what if we fund 2,000 more slots",
  "should we target by risk score") from observational history, where treatment was
  assigned on purpose rather than at random.
- A confident wrong-sign answer would be expensive, and the agent must refuse for
  cohorts that have no comparable untreated group.
- The same figure has to appear, identically, in chat, on a dashboard, and in a
  notebook.

When not to use it:

- You ran a randomized experiment. A difference in means is already the effect.
- The questions are descriptive ("how many members were readmitted"). Use Cortex
  Analyst over a semantic view.
- The outcome is a rare one-shot binary flag at modest scale. Per-unit effects are
  not statistically recoverable; see the power hazard in
  [docs/design.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/docs/design.md).
- The treatment is multi-arm, dose-response, or the outcome is time-to-event. The
  framework supports a single binary treatment and a fixed-window outcome.

## How it works

![How it works: Causally grounded Cortex Agent that refuses when the data cannot answer](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/agent-causal-grounding/assets/agent-causal-grounding-01.png)

Notebooks fit the models once and write `MODELS.*`. Six stored procedures read those
tables and never refit. The Cortex Agent reaches everything through those six, and
the Streamlit console either calls the same procedures or reads the same tables, so
a figure in chat, on the dashboard, and in the notebook is the same figure.

Six decisions here apply to any agent whose answers have to hold up:

| Decision | Why it matters |
|---|---|
| **Refusal is a tool, not a disclaimer field** | `CHECK_IDENTIFICATION` returns `identified: false` with *no numbers in it*. A tool returning a figure plus a caveat invites the model to quote the figure and drop the caveat |
| **Tools read persisted tables, they never refit** | Fitting happens once, in a notebook. There is one implementation of each number, so the surfaces cannot drift apart |
| **Cortex Analyst is deliberately omitted** | Text-to-SQL over these tables is precisely how you get the +0.0846. Restricting the agent to procedures that encapsulate the correct estimator is the design, not a limitation |
| **The agent is never stricter than its own pipeline** | An early version invented its own overlap rule and refused for a population the notebook had already estimated. That is inconsistent, not careful. The procedure mirrors `causal_core.causal.is_identified` exactly |
| **Persist every candidate you evaluated, not just the winner** | With only the winning curve in the table, the agent hedged. A missing number reads as evasion even when the underlying result is decisive |
| **Refusal propagates to every surface** | Pick an unanswerable cohort in the console and the metrics are *withheld*, not captioned with a warning. An absent number is read as an answer; a warning beside a number is read as a formality |

Three different things live here and only one of them is a simulation:

| Layer | What it actually is |
|---|---|
| Synthetic data generator | A simulation. Plants a known effect per unit so estimators can be graded |
| Estimation | Causal inference on history that already happened. Not a simulation |
| Scenario projection | Forward projection using the measured effect |

The simulation exists so correctness is checkable, which is impossible on real data
because real data has no answer key.

Two runtime constraints shape the architecture (full detail in
[docs/runtime-and-packages.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/docs/runtime-and-packages.md)):

- **Warehouse Python is aarch64.** `econml` has no aarch64 wheel on PyPI, so it must
  come from the Snowflake Anaconda channel.
- **dowhy and econml cannot share a process.** dowhy 0.14 needs `numpy>2`, econml
  needs `numpy<2`. So dowhy is encapsulated in its own stored procedure, reached with
  `CALL`, and the two environments talk through tables.

## Prerequisites

| Requirement | Notes |
|---|---|
| Role | One build role with CREATE DATABASE and CREATE WAREHOUSE on the account and `SNOWFLAKE.CORTEX_USER` (a custom role with exactly those privileges ran every step). Run every script, the Python deploy scripts, and teardown as this role, so it owns everything teardown drops |
| ACCOUNTADMIN | Only for the optional `sql/10_agent_user_role.sql`. Start it as the build role; it switches to ACCOUNTADMIN for `CREATE ROLE`, the `SNOWFLAKE.CORTEX_AGENT_USER` grant, the grant to you, and a transfer of the new role's ownership to the build role, then switches back for the object grants |
| Cortex Agents access | `SNOWFLAKE.CORTEX_USER` or `SNOWFLAKE.CORTEX_AGENT_USER`. Agents evaluate privileges with the user's **default role**, and the user needs a default warehouse |
| Snowflake PyPI repository | `SNOWFLAKE.PYPI_REPOSITORY_USER`, granted to PUBLIC by default. Needed only by `REFUTE_ESTIMATE` and the dowhy check |
| Snowflake CLI | `snow` with a default connection. No connection name is hard-coded anywhere |
| Python 3.11 | For local notebooks and the deploy scripts: `pip install -r requirements.txt`. The notebooks also run unchanged in a Snowflake Workspace notebook |
| Warehouse | `COOKBOOK_AGENT_CAUSAL_GROUNDING_WH` (XSMALL), created by the scripts |

## Quickstart

Run from this folder, as the build role from Prerequisites. Fabricated data with a planted
answer key, so every estimator can be graded against the truth.

1. Prove the two package paths work in your account. Do not skip this.

   ```bash
   snow sql -f sql/00_verify_packages.sql
   ```

2. Create the contract (database, schemas, five documented tables), then fabricate
   the data. The second script ends by asserting 10 calibration checks.

   ```bash
   snow sql -f usecases/payer_care_management/01_contract.sql
   snow sql -f usecases/payer_care_management/02_generate_synthetic.sql
   ```

3. Local environment.

   ```bash
   python3.11 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Run `notebooks/01_naive.ipynb`, `02_causal.ipynb`, and `03_allocation_equity.ipynb`
   in order, in local Jupyter or a Workspace notebook. Notebook 02 fits the models and
   writes the tables every tool reads, and notebook 03 writes the Qini curves and the
   equity report, so the agent has nothing to say until both have run.

5. Deploy the six tool procedures and the Cortex Agent. This also publishes
   `MODELS.SPEC_SNAPSHOT` and `MODELS.V_ANALYSIS_FRAME`, which the refutation
   procedure reads.

   ```bash
   python framework/deploy_agent.py
   ```

6. Optional: the Streamlit console, and a least-privilege role that can use the agent
   but cannot read its tables. Start `10_agent_user_role.sql` as the build role: it
   switches to ACCOUNTADMIN for its first part and back for the rest (see
   Prerequisites).

   ```bash
   python framework/deploy_app.py
   snow sql -f sql/10_agent_user_role.sql
   ```

7. Ask the agent something. Each of these exercises a different decision above:

   - *"What is the effect of the program, and should I believe it?"* Grounded answer
     plus the assumptions it rests on.
   - *"I'm about to commit $4M. Could this be spurious?"* Triggers refutation; the
     answer should say passing is weak evidence *for*, while failing is strong
     evidence *against*.
   - *"What about members with 7 or more comorbidities?"* No comparable untreated
     group exists, so this one should be **refused**, with the mechanism explained.

The connection comes from `SNOWFLAKE_CONNECTION_NAME`, then
`SNOWFLAKE_DEFAULT_CONNECTION_NAME`, then the default connection in
`connections.toml` (the one `snow` uses without `-c`). Inside Snowflake the notebooks
and the console use `get_active_session()`.

## Walkthrough

### The contract

Read `usecases/payer_care_management/01_contract.sql` and stop. It is the whole
contract. Do **not** read `02_generate_synthetic.sql` to understand how this works;
it is several hundred lines of data fabrication and none of it is part of the method.

Every use case supplies five objects in its `DATA` schema, as tables or views:

| Object | Meaning | Payer | Churn |
|---|---|---|---|
| `UNIT` | one row per decision subject | member | subscriber |
| `UNIT_PERIOD` | panel, one row per unit per period | member-month | customer-month |
| `TREATMENT` | who was treated, and when | program enrollment | retention offer |
| `OUTCOME` | outcome per unit, plus its pre-treatment value | readmission rate | share of months active |
| `CAPACITY` | the binding constraint | nurse slots by region | offer budget by market |

Domain names live in `usecase.yaml` and nowhere else. Nothing under `framework/`
references a domain column, which is why `usecases/subscription_churn` runs all three
notebooks with no Python changes: switch `active_usecase` in
[config.yaml](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/config.yaml) and run its two SQL files.

Each use case gets its own database (`COOKBOOK_AGENT_CAUSAL_GROUNDING` for payer,
`COOKBOOK_AGENT_CAUSAL_GROUNDING_CHURN` for churn), set once in the `SET` block of its
SQL files and in `usecase.yaml`. `framework/deploy_agent.py` substitutes
`@DATABASE@`, `@WAREHOUSE@`, `@UNIT_ID@` and `@UNIT_LABEL@` into the `agent/*.sql`
templates at deploy time, because a procedure invoked by an agent cannot rely on the
caller's session having the right database set.

### Refusal is a tool

`CHECK_IDENTIFICATION` judges overlap on the cohort's **own** propensity
distribution, because a population with adequate average overlap can still contain
slices with none, and those slices are the ones people ask about. The rule is the
share of treated units with propensity above 0.95, the same rule as
`causal_core.causal.is_identified`:

```python
reasons = []
if extreme_share > 0.25:
    reasons.append(
        f"{extreme_share:.1%} of treated units have a propensity above 0.95, so "
        "there is effectively no comparable untreated group"
    )
if n_treated < 100:
    reasons.append(f"only {n_treated} treated units, too few for a stable estimate")
```

Cohort filters are structured JSON, never SQL. The procedure validates every column
against `INFORMATION_SCHEMA.COLUMNS` for `DATA.UNIT` and binds every value, so a
hallucinated column produces a clean error listing the valid ones and a malicious
string becomes a literal. The parameter is a STRING because custom tools cannot take
OBJECT parameters. `RUN_SCENARIO` re-checks identification internally and returns
`refused: true` with no figures, rather than trusting the orchestrator to have called
`CHECK_IDENTIFICATION` first. The Streamlit console passes the cohort the same way, as
a bind parameter (`CALL AGENT.CHECK_IDENTIFICATION(?)`), so a category value such as
`O'Neil` reaches the procedure intact.

```sql
CALL COOKBOOK_AGENT_CAUSAL_GROUNDING.AGENT.CHECK_IDENTIFICATION('{"COMORBIDITY_COUNT": {"min": 7}}');
```

### The orchestration instructions are the substantive part

A tool that refuses is only useful if the orchestrator honours it, and a capable
model handed a refusal plus a population-level estimate will helpfully offer the
population number as an approximation. So [agent/02_agent.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/agent/02_agent.sql)
forbids it by name:

```yaml
instructions:
  response: |
    When a tool returns a refusal, report it as the answer. Do not soften it, do
    not substitute a number from a wider population, and do not describe an
    unavailable estimate as "roughly" or "approximately" anything. A refusal is a
    correct and complete answer.
  orchestration: |
    1. If the user asks about a SPECIFIC SUBGROUP or cohort ... call
       check_identification FIRST with that cohort before any other tool. If it
       returns identified=false, report the refusal and STOP.
```

The agent is created with `CREATE OR REPLACE AGENT ... COPY GRANTS` and
`models.orchestration: auto`, so re-deploying keeps any USAGE you granted on it.

### Refutation, in its own environment

`REFUTE_ESTIMATE` ([agent/03_refute.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/agent/03_refute.sql)) runs three attacks:
**placebo treatment** (replace treatment with a permuted copy; a real effect must
collapse), **random common cause** (add an irrelevant covariate; a stable estimate
barely moves), and **data subset** (re-estimate on random 80% subsets). It cannot
import `causal_core`, so it learns column names from `MODELS.SPEC_SNAPSHOT` and reads
the frame through `MODELS.V_ANALYSIS_FRAME`, which the framework generates.

The asymmetry is the point, and it is enforced in the wording. Passing all three is
*weak evidence for* the estimate. Failing any is *strong evidence against* it. None of
the tests can check the assumption that actually matters, that every common cause was
measured, and a test in the suite asserts the verdict never contains "proves",
"confirms", or "validates". The output also reports the primary doubly-robust estimate
alongside dowhy's linear adjustment, because the two differ and leaving that
unexplained would read as a contradiction rather than an estimator difference.

### The equity gate is not optional

Impactability correlates with being reachable, and reachability correlates with
advantage, so targeting by estimated impact can quietly withhold help from the people
who need it most. This is the failure mode documented in Obermeyer et al., *Science*
2019, which found a widely deployed commercial care-management algorithm
under-referred Black patients because it used healthcare spending as a proxy for
illness. `framework/causal_core/equity.py` **fails the pipeline** when disparity
across `fairness.protected_attributes` exceeds `fairness.max_disparity_ratio`. It
does not print a warning and continue.

Constraining each protected attribute separately does not bound the joint, so the
allocator constrains the intersection. A property test over a grid of capacities and
thresholds found a real bug here: at a 1.05 threshold with capacity 200 over 15
buckets, the integer grid was coarser than the band and the function silently
returned a selection that breached its own gate. It now falls back to a
largest-remainder proportional split and verifies the bound before returning,
raising `EquityGateFailure` rather than handing back a violating allocation.

### Owner's rights, and the role that uses the agent

The tool procedures are `EXECUTE AS OWNER`. That is deliberate: the tools are the
only sanctioned path from a question to a number, so a user should be able to ask the
agent without being able to run the raw comparison that gets the sign wrong.
[sql/10_agent_user_role.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/sql/10_agent_user_role.sql) creates
`COOKBOOK_AGENT_CAUSAL_GROUNDING_USER` with USAGE on the warehouse, database, `AGENT`
schema, the six procedures, and the agent, and nothing on `DATA` or `MODELS`. ACCOUNTADMIN
creates the role and then hands its ownership to the build role, so teardown, run as
the build role, can drop it. The trade-off is in Gotchas.

### Pointing it at your own data

Start at [docs/adding-a-use-case.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/docs/adding-a-use-case.md). Write a
`usecase.yaml`, then map your existing tables to the five canonical objects with
[usecases/_template/03_bring_your_own_data.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/usecases/_template/03_bring_your_own_data.sql).
They are created as **views**, so there is no data movement and your existing
governance policies keep applying. Then drop the `TRUTH` schema. The notebooks grade
every estimator against that answer key, so before you run them on real data, remove
`include_truth=True` and the cells that read `TRUE_ITE`, `TRUE_ATE` or `TRUE_ATT` (the
planted-truth and leaderboard cells in 01 and 02, and the cells priced against planted
truth in 03); with `TRUTH` gone those cells fail. Nothing under `framework/` changes.
[docs/design.md](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/agent-causal-grounding/docs/design.md) lists which half of this folder is synthetic
scaffolding you can delete.

### Tests

```bash
pytest -m "not snowflake and not slow"   # no connection needed
pytest -m snowflake                      # against the deployed fixture
pytest -m slow                           # coverage across 40 replications
```

**Fast tests** build small data generating processes in numpy where the true effect is
known exactly and call the estimators directly; they verify the code is *correct*.
**Integration tests** run against the deployed tables and procedures and verify the
pipeline is *wired* correctly, including that the agent's arithmetic matches
`MODELS.CATE_SCORES` to 1e-4. The calibration checks do not cover this: break the
doubly-robust estimator and all ten still pass. These tests are what complains.

## Verify

`sql/00_verify_packages.sql` returns two `OK` rows, similar to:

```text
OK econml=0.15.0 numpy=1.26.4 pandas=2.3.3 sklearn=1.4.2 statsmodels=0.15.0
OK true=-0.400 naive=-0.031 adjusted=-0.421 placebo=-0.0032 rcc=-0.420 subset=-0.413
```

`02_generate_synthetic.sql` ends with `ALL 10 CALIBRATION CHECKS PASSED`, including
`naive_has_wrong_sign: naive 0.0846 vs true ATE -0.0452`.

Notebook 02 ends with the estimator comparison. On the fixture the raw
difference has the wrong sign and every causal estimator recovers the direction:

```text
method                     target  estimate   ci_low    ci_high   truth
difference in differences  att     -0.04905  -0.05193  -0.04617  -0.04710
causal forest (DML)        ate     -0.03472  -0.06107  -0.00836  -0.04518
doubly robust (AIPW)       ate     -0.03139  -0.03438  -0.02841  -0.04518
S-learner flip-the-flag    ate     -0.03127  -0.03141  -0.03113  -0.04518
raw difference             ate      0.08458   0.08198   0.08719  -0.04518
```

The generator also plants an unmeasured confounder (the
`frailty_confounding_bounded` calibration check), so estimators that adjust only
for measured covariates land short of the truth; the AIPW interval does not cover
it. Notebook 03 reports an AUUC of +0.29 when ranking by estimated uplift against
-0.14 when ranking by risk score, fails the equity gate on the unconstrained
policy (the expected result), and passes it on the constrained policy at a cost
of about 2.4% of the benefit.

The refusal case, called directly or through the agent:

```sql
CALL COOKBOOK_AGENT_CAUSAL_GROUNDING.AGENT.CHECK_IDENTIFICATION('{"COMORBIDITY_COUNT": {"min": 7}}');
-- identified: false
-- refusal: "NOT identified for COMORBIDITY_COUNT at least 7: 46.2% of treated units have a propensity above 0.95, so there is effectively no comparable untreated group. ..."
```

And through `DATA_AGENT_RUN`:

```sql
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'COOKBOOK_AGENT_CAUSAL_GROUNDING.AGENT.DECISION_AGENT',
  $${"messages": [{"role": "user", "content": [{"type": "text",
     "text": "What is the effect of the program for members with 7 or more comorbidities?"}]}]}$$
)):content AS content;
```

The response calls `check_identification`, reports the refusal and its mechanism, and
quotes no effect size for that cohort. The same question about the whole population
returns the doubly-robust estimate with its interval and assumptions.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| A role that should not see member data gets estimates through the agent | The tool procedures are `EXECUTE AS OWNER`, so any caller with USAGE on a procedure reads `MODELS.*` and `DATA.UNIT` with the owner's privileges. `REFUTE_ESTIMATE` also overwrites `MODELS.REFUTATION` | This is the intended trade-off: users get answers without table access. Grant USAGE on the six procedures only to the intended role (`sql/10_agent_user_role.sql`), never to PUBLIC. Use caller's rights instead if every user already has SELECT on the tables |
| `CREATE PROCEDURE` fails with a dependency resolution error | `dowhy==0.14` needs `numpy>2`, `econml` needs `numpy<2`; one `PACKAGES` list cannot hold both | Keep dowhy isolated in `REFUTE_ESTIMATE`. `sql/00_verify_packages.sql` includes the failing combination, commented out |
| econml fails to install from PyPI in a procedure | Warehouse Python is aarch64 and PyPI has no aarch64 econml wheel | Take econml from the Anaconda channel (no `ARTIFACT_REPOSITORY` clause) |
| The agent sees two tools with the same name | Changing a parameter type in `CREATE OR REPLACE PROCEDURE` creates an overload rather than replacing | Drop the old signature explicitly before re-deploying |
| `CALL ...(NULL)` returns a malformed-argument error | SQL NULL reaches Python as a truthy `sqlNullWrapper`, not `None` | `_parse_cohort` checks for it explicitly; do the same in new tools |
| `to_pandas()` fails in `REFUTE_ESTIMATE` with "pandas is not installed" | The artifact-repository environment has no pyarrow bridge | Use `collect()` and `create_dataframe(...).save_as_table(...)`, as the procedure does |
| Refute tool returns "SPEC_SNAPSHOT is empty" | The spec snapshot and analysis view were never published | Run `python framework/deploy_agent.py`, which publishes both |
| `CREATE OR REPLACE AGENT ... COPY GRANTS COMMENT = ...` fails with "unexpected 'COMMENT'" | Clause order. This differs from the published syntax in [CREATE AGENT](https://docs.snowflake.com/en/sql-reference/sql/create-agent), which lists `COPY GRANTS` straight after the name | Put `COPY GRANTS` after `COMMENT` and `PROFILE`, right before `FROM SPECIFICATION`, as `agent/02_agent.sql` does |
| `sql/10_agent_user_role.sql` stops at `USE ROLE ACCOUNTADMIN` | Your user does not have ACCOUNTADMIN | Have an administrator run Part 1 of the script with your build role name, then run Part 2 yourself |
| Teardown cannot drop `COOKBOOK_AGENT_CAUSAL_GROUNDING_USER` | The role is owned by a role other than the one running teardown | Run teardown as the build role. `10_agent_user_role.sql` transfers the role's ownership to it |
| Agent answers fail for a user whose current role has every grant | Cortex Agents use the user's default role and default warehouse, not the session's current role | Make `COOKBOOK_AGENT_CAUSAL_GROUNDING_USER` the user's default role, with a default warehouse the role can use |
| Placebo test fails intermittently | Its estimate carries its own sampling noise at small samples | Use `sample_size >= 15000` and `num_simulations >= 10` |
| Local scripts hang at login | Browser-based SSO needs one interactive login before headless runs | Run `snow connection test` once, or use key-pair or PAT auth for automation |

## Teardown

```bash
snow sql -f sql/99_teardown.sql
```

Run it as the build role. Drops both use case databases (with the agent, procedures,
and console inside), the package-check database, the optional user role, and the
warehouse, then lists anything left that starts with `COOKBOOK_AGENT_CAUSAL_GROUNDING`.
The recipe makes no account-level setting changes; the only account-level objects are
the warehouse and the optional role.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
In site/cortex-ai-cookbook/src/agent-causal-grounding of the cortex-ai-cookbook repo, run
the causal grounding recipe end to end on my default Snowflake connection.
Install or enable the bundled machine-learning and agent-studio skills first, and use
them for the ML and agent sub-tasks they cover.
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(), CURRENT_WAREHOUSE() and show me the
   result. Confirm with me that the current role is the build role (CREATE DATABASE,
   CREATE WAREHOUSE, SNOWFLAKE.CORTEX_USER) before creating anything, and run every
   step below as that role.
2. snow sql -f sql/00_verify_packages.sql and confirm both checks return OK.
3. snow sql -f the payer use case 01_contract.sql, then 02_generate_synthetic.sql,
   and confirm ALL 10 CALIBRATION CHECKS PASSED.
4. Create a Python 3.11 venv outside the repo, pip install -r requirements.txt, and
   execute notebooks 01, 02, 03 in order with outputs written outside the repo, so no
   outputs are saved into it.
5. python framework/deploy_agent.py.
6. Ask the agent, via SNOWFLAKE.CORTEX.DATA_AGENT_RUN, one population question and
   one about members with 7 or more comorbidities; the second must be refused with
   no effect size.
7. Run pytest -m "not snowflake and not slow" and pytest -m snowflake.
8. Optional: sql/10_agent_user_role.sql. Show me the script first and ask before
   running it, because its Part 1 switches to ACCOUNTADMIN to create a role and grant
   it SNOWFLAKE.CORTEX_AGENT_USER.
9. When I say so, snow sql -f sql/99_teardown.sql as the build role and confirm
   nothing named COOKBOOK_AGENT_CAUSAL_GROUNDING remains.
Report each step's result and any error verbatim.
```

## Related skills

- `machine-learning` (bundled): general Snowflake ML workflows, model training and
  registry. This recipe does not use the Model Registry; the fitted effects are
  persisted as tables because the tools must read one fixed implementation.
- `agent-studio` (bundled): creating, auditing, and evaluating Cortex Agents,
  including verified-query style evaluations you can point at this agent.

## References

- [CREATE AGENT](https://docs.snowflake.com/en/sql-reference/sql/create-agent)
- [Create and manage agents (custom tools)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [DATA_AGENT_RUN](https://docs.snowflake.com/en/sql-reference/functions/data_agent_run-snowflake-cortex)
- [Caller's rights and owner's rights stored procedures](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-rights)
- [Using third-party packages (Anaconda and Artifact Repository)](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
