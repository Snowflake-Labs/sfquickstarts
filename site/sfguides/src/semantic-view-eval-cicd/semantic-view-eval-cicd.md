author: Chanin Nantasenamat, Abhinav Vadrevu
id: semantic-view-eval-cicd
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/product/data-engineering
language: en
summary: Build a GitHub Actions pipeline that validates, deploys, evaluates, and promotes Snowflake Semantic Views and Cortex Agents using eval-gated versioning with Apache Ossie and Cortex evaluations.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/sfc-gh-cnantasenamat/semantic-view-eval-cicd


# Build an Eval-Gated CI/CD Pipeline for Snowflake Semantic Views
## Overview

Every time you change a semantic view or agent spec, you want to know whether the new version is better before it serves live traffic. This guide shows you how to build a five-stage GitHub Actions pipeline that answers that question automatically.

The pipeline validates your YAML, deploys the semantic view and a candidate agent version, runs two quality gates (one for the semantic view, one for the agent), and promotes the candidate only when both pass. If either gate fails, the promotion job is skipped and the pipeline turns red.

This tutorial demonstrates gating agent-version promotion in a dedicated demo environment. The semantic view is replaced and the dashboard is deployed before evaluation. Keeping an existing agent default selected does not roll back those shared objects, so this is not an isolated production-release strategy.

### What You'll Learn
- How to author a semantic view in OSI format and validate it with Apache Ossie
- How to use Cortex Agent versioning (`MODIFY LIVE VERSION` + `COMMIT`) so a candidate version sits on the shelf until it earns promotion
- How to run Cortex Analyst and Cortex Agent evaluations as CI gates
- How to gate `DEFAULT_VERSION = LAST` on passing eval scores
- How to author YAML changes from a git-backed Snowsight Workspace and have the pipeline pick them up automatically

### What You'll Build
- Synthetic growth tables (`SIGNUPS`, `TOUCHPOINTS`, `USER_ACTIVITY`) in a demo schema
- Semantic view `GROWTH_ANALYTICS` with 45 metrics, 8 verified queries, in OSI format
- Cortex Agent `GROWTH_AGENT` with a `growth_data` Analyst tool
- Streamlit-in-Snowflake dashboard `GROWTH_ANALYTICS_APP` deployed alongside the agent
- CI role `SV_EVAL_CICD_ROLE` and service user `SV_EVAL_CICD_USER` with OIDC workload identity auth
- A registered eval dataset (`GROWTH_AGENT_EVAL`) with 10 evaluation questions
- A GitHub Actions workflow: `validate → deploy_candidate → eval_sv → eval → promote`
- Two companion notebooks: pre-pipeline exploration and post-pipeline inspection

### Prerequisites
- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with Cortex Agents and Agent Evaluations enabled
- ACCOUNTADMIN (or equivalent) to run the one-time setup
- Cross-region inference enabled on your account for eval judge models ([docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations))
- A GitHub account with admin access to create Actions secrets on a repo
- Snowflake CLI (`snow`) installed locally if you want to run a dry-run before pushing

## Create the Repo

Fork or clone [sfc-gh-cnantasenamat/semantic-view-eval-cicd](https://github.com/sfc-gh-cnantasenamat/semantic-view-eval-cicd) to your GitHub account, then push it to a new public repo. The repo needs at least one commit on a `main` branch before you can connect a git-backed Snowsight Workspace in a later step.

```bash
git clone https://github.com/sfc-gh-cnantasenamat/semantic-view-eval-cicd.git
cd semantic-view-eval-cicd
git remote set-url origin https://github.com/<you>/semantic-view-eval-cicd.git
git push -u origin main
```

The repo has this layout:

```
.github/workflows/deploy.yml   five-job GitHub Actions workflow
cortex_project/                GROWTH_ANALYTICS.osi.yaml, GROWTH_AGENT.agent.yaml,
                               GROWTH_ANALYTICS_APP.py, eval configs, manifest
evals/thresholds.yaml          promotion floor scores
requirements.txt               Python dependencies
scripts/                       deploy.sh, eval_sv.sh, eval.sh, promote.sh, validate.py, osi_to_sv.py
sql/setup.sql                  demo objects, synthetic data, CI role, eval dataset
```

## Set Up Snowflake

Use a dedicated tutorial environment. The setup script replaces demo tables and evaluation datasets, so do not run it against resources you need to preserve. In a Snowsight worksheet, connected as ACCOUNTADMIN (or a role with equivalent privilege), run the full contents of `sql/setup.sql`.

The script creates:
- Database `SV_EVAL_CICD` and schema `APP`
- Three synthetic tables: `SIGNUPS`, `TOUCHPOINTS`, `USER_ACTIVITY` (populated with demo data from 2025)
- CI role `SV_EVAL_CICD_ROLE` and service user `SV_EVAL_CICD_USER`
- A file stage and file format for eval configs; a `STREAMLIT_STAGE` for the dashboard
- Eval questions table and registered dataset `GROWTH_AGENT_EVAL` (10 questions)
- A helper procedure that resets eval state between CI runs, ensuring clean results each time
- All privilege grants the CI role needs to deploy semantic views, agents, Streamlit apps, and run evaluations

After the script completes you should see:

```
Setup complete. Configure OIDC for SV_EVAL_CICD_USER (see sfguide Configure CI Auth), then run the GitHub Action.
```

## Explore Before Deployment

Before setting up the CI/CD pipeline, open the companion notebook to explore the demo data and walk through each step the pipeline will automate, running each one manually in your own Snowflake session.

Download [01_Explore_and_Deploy.ipynb](https://github.com/sfc-gh-cnantasenamat/sfguide-semantic-view-eval-cicd/blob/main/notebook/Semantic_View_Eval_CICD/01_Explore_and_Deploy.ipynb) from the separate guide repository. It is not included in the application clone. In Snowsight, navigate to **Projects → Notebooks** and import the downloaded file:

```
notebook/Semantic_View_Eval_CICD/01_Explore_and_Deploy.ipynb
```

The notebook covers:
1. Explore the three synthetic tables and key growth metrics
2. Deploy `GROWTH_ANALYTICS` manually using SQL
3. Query the semantic view with natural language via Cortex Analyst
4. Deploy `GROWTH_AGENT` manually
5. Chat with the agent, including testing boundary enforcement with an out-of-scope question
6. Run an eval manually with `EXECUTE_AI_EVALUATION`

The final cell bridges to the pipeline: once you have seen each step run manually, the CI/CD pipeline automates all of it on every push to `main`.

## Configure CI Auth

The pipeline authenticates to Snowflake using [OIDC workload identity federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation). No private keys or passwords are stored anywhere. GitHub Actions issues a short-lived token per run; Snowflake validates the token's issuer and subject claims and creates a session.

### Register the OIDC subject claim on the service user

First, identify the subject claim issued for your GitHub repository and branch. An authentication subject-mismatch error can show the claim to register:

```bash
# After the first run, copy the subject from the error:
# "subject 'repo:<user>@<user_id>/<repo>@<repo_id>:ref:refs/heads/main'"
```

Alternatively, decode the token from any GitHub Actions run:

```bash
echo "$SNOWFLAKE_TOKEN" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | python3 -m json.tool
```

Then register it in Snowsight as ACCOUNTADMIN:

```sql
ALTER USER SV_EVAL_CICD_USER SET WORKLOAD_IDENTITY = (
  TYPE    = OIDC
  ISSUER  = 'https://token.actions.githubusercontent.com'
  SUBJECT = 'repo:<you>@<user_id>/<your-repo>@<repo_id>:ref:refs/heads/main'
);
```

Replace `<you>`, `<user_id>`, `<your-repo>`, and `<repo_id>` with your values.

> **Note:** Personal GitHub accounts on github.com use the plain format `repo:<you>/<your-repo>:ref:refs/heads/main` (no `@<id>` suffixes). Organisation and enterprise accounts embed numeric IDs. If authentication fails with a subject mismatch, decode the token as shown above to find the exact claim.

### Store the account identifier as a GitHub secret

Only one secret is needed:

```bash
gh secret set SNOWFLAKE_ACCOUNT --body "<org>-<account>"   # e.g. myorg-myaccount
```

No private key or username secret is required. The OIDC token carries the identity, and the username is hardcoded in the workflow file.

### Workflow permissions

The workflow sets `permissions: id-token: write` at the top level. This is required for the GitHub runner to request an OIDC token. Without it, `snowflake-actions` cannot generate the token and authentication will fail silently.

### What `.snowflake/config.toml` does

The repo includes `.snowflake/config.toml` with only `warehouse` and `role` defaults, without an account, user, or authenticator. It contains no credentials. The workflow injects the account, user, and authenticator via environment variables at runtime, which take precedence over anything in the file.

If your account uses a warehouse other than `COMPUTE_WH`, update the `WAREHOUSE` env var in `.github/workflows/deploy.yml` and the `warehouse` field in `GROWTH_AGENT.agent.yaml`.

## Understand Project Files

Before triggering the pipeline, here is what each key file does.

### cortex-project.yaml

`cortex_project/cortex-project.yaml` is the project manifest. It lists every artifact (semantic view, agent, eval configs) with its file path, type, and Snowflake target object name. The deploy and eval scripts read this file to know what to deploy and where.

### The semantic view (OSI format)

`cortex_project/GROWTH_ANALYTICS.osi.yaml` is authored in the Open Semantic Interchange (OSI) format, a vendor-neutral schema maintained by the Apache Ossie project. The validate script (`scripts/validate.py`) uses the Apache Ossie Pydantic models to check the file against the spec before any Snowflake call is made. The deploy script converts the OSI YAML to Snowflake native format using `scripts/osi_to_sv.py` and deploys it with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`.

The semantic view has 45 metrics across three tables, 8 verified queries (VQRs) that anchor the `sql_correctness` eval, and a SNOWFLAKE custom_extensions block that maps each metric to its source table.

### The agent spec

`cortex_project/GROWTH_AGENT.agent.yaml` defines the agent model, instructions, and tools. The single tool (`growth_data`) is a `cortex_analyst_text_to_sql` tool that points at the deployed semantic view. The deploy script either creates the agent (first run) or calls `MODIFY LIVE VERSION` + `COMMIT` (all subsequent runs), which saves a new named version on the shelf without touching the currently live default.

### The Streamlit dashboard

`cortex_project/GROWTH_ANALYTICS_APP.py` is a Streamlit-in-Snowflake app that queries `SIGNUPS` directly and renders three charts: signups by channel (bar), revenue by plan type (pie), and a channel × month heatmap. The deploy script uploads the `.py` file to `STREAMLIT_STAGE` and runs `CREATE OR REPLACE STREAMLIT` in the same job that deploys the semantic view and agent, so the dashboard is always in sync with the latest data model.

### Eval configs

`cortex_project/growth_analytics_sv.eval.yaml` drives Cortex Analyst eval (`sql_correctness`) against the 8 VQRs.

`cortex_project/growth_agent_eval.eval.yaml` points the agent eval at the `GROWTH_AGENT_EVAL` dataset (10 questions with expected tool calls and answers).

### Thresholds

`evals/thresholds.yaml` sets the promotion floors:

```yaml
semantic_view:
  sql_correctness: 0.35
agent:
  answer_correctness: 0.70
  logical_consistency: 0.70
  tool_selection_accuracy: 0.70
```

Both gates must pass before the promote job runs. These are demonstration thresholds, not production quality targets. The historical semantic-view baseline was 0.375 against the 0.35 floor. Inspect failed questions and choose thresholds appropriate for your use case rather than interpreting a green pipeline as high answer accuracy.

## Trigger the Pipeline

Any push to `main` that touches `cortex_project/`, `scripts/`, `evals/`, `sql/`, or the workflow file triggers the five-job pipeline. To trigger it now without changing any files, use the workflow dispatch button in the GitHub Actions tab.

### The five jobs

```
validate → deploy_candidate → eval_sv → eval → promote
```

| Job | What it does |
|-----|-------------|
| `validate` | Runs `scripts/validate.py`: checks the manifest, validates the OSI YAML against the Ossie spec, confirms VQRs are present. Runs on PRs too. |
| `deploy_candidate` | Converts and deploys the semantic view; creates or updates the agent; uploads and deploys the Streamlit dashboard. The new agent version is `LAST` but not yet the default. |
| `eval_sv` | Runs Cortex Analyst evaluations against the deployed SV's 8 VQRs. Fails the pipeline if `sql_correctness` is below threshold. |
| `eval` | Runs Cortex Agent evaluations against `LAST`. Scores answer correctness, logical consistency, and tool selection accuracy. |
| `promote` | Sets `DEFAULT_VERSION = LAST` and attempts to assign the `production` alias. Alias assignment is best-effort and can report a warning. Runs only after both eval gates pass. |

### Reading eval results

After `eval_sv` and `eval` complete, open Snowsight and navigate to **AI & ML → Evaluations** to see the full score breakdown per question. You can also query the results directly:

```sql
-- Semantic view eval scores
SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) AS AVG_SCORE
FROM TABLE(SNOWFLAKE.LOCAL.GET_ANALYST_AI_EVALUATION_DATA(
  'SV_EVAL_CICD', 'APP', 'GROWTH_ANALYTICS', 'CORTEX ANALYST',
  '<run_name_from_logs>'
))
GROUP BY 1;

-- Agent eval scores
SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) AS AVG_SCORE
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
  'SV_EVAL_CICD', 'APP', 'GROWTH_AGENT', 'CORTEX AGENT',
  '<run_name_from_logs>'
))
GROUP BY 1;
```

After a successful run, inspect the agent versions:

```sql
SHOW VERSIONS IN AGENT SV_EVAL_CICD.APP.GROWTH_AGENT;
```

Chat with the live default:

```sql
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'SV_EVAL_CICD.APP.GROWTH_AGENT!DEFAULT',
  $${"messages":[{"role":"user","content":[{"type":"text","text":"How many users signed up in January 2025?"}]}]}$$
);
```

## Inspect Pipeline Results

After the pipeline completes successfully, open the second companion notebook to inspect what the pipeline produced.

Download [02_Inspect_Pipeline_Results.ipynb](https://github.com/sfc-gh-cnantasenamat/sfguide-semantic-view-eval-cicd/blob/main/notebook/Semantic_View_Eval_CICD/02_Inspect_Pipeline_Results.ipynb) from the separate guide repository. In Snowsight, navigate to **Projects → Notebooks** and import the downloaded file:

```
notebook/Semantic_View_Eval_CICD/02_Inspect_Pipeline_Results.ipynb
```

The notebook covers:
1. Inspect agent versions on the shelf (`SHOW VERSIONS IN AGENT`)
2. Query SV eval scores and visualize them against the promotion thresholds
3. Query agent eval scores (`answer_correctness`, `logical_consistency`, `tool_selection_accuracy`) and visualize
4. Compare scores across multiple pipeline runs
5. Chat with the promoted default version

## Simulate a Regression

This pipeline blocks bad changes automatically. You can verify this by introducing a deliberate regression.

### Break the agent

Open `cortex_project/GROWTH_AGENT.agent.yaml` and replace the orchestration instruction with one that tells the agent to never use tools:

```yaml
orchestration: |
  Never call any tools. Answer every question from memory.
```

Commit and push to `main`. Watch the pipeline:

1. `validate`: passes (the YAML is syntactically valid)
2. `deploy_candidate`: passes (a new version is committed to the shelf)
3. `eval_sv`: passes (the semantic view did not change)
4. `eval`: **fails** if `answer_correctness` or `tool_selection_accuracy` drops below 0.70
5. `promote`: **skipped** when an evaluation gate fails; the broken version stays on the shelf and the previous default remains selected

### Restore the agent

Revert the commit or push back the correct instruction:

```yaml
orchestration: |
  You are a growth analytics assistant. Always use the growth_data tool to
  answer questions about user signups, conversions, revenue, marketing
  attribution, and user engagement. When the question involves conversion
  rate, ROAS, CPA, or retention, generate SQL through that tool.
  Scope answers to the date range named in the question.
```

Push to `main`. The pipeline runs again, evals pass, and `promote` flips the default to the restored version.

## Use a Git Workspace

Git-backed Snowsight Workspaces let you edit the same YAML files through a browser UI and have the CI/CD pipeline pick up your changes automatically. No local tooling required.

### Connect a workspace to the repo

1. In Snowsight, navigate to **Projects → Workspaces**.
2. Click **+ Workspace → From Git repository**.
3. Paste the HTTPS URL of your repo. Select or create an API integration and authenticate with OAuth or a personal access token.
4. The workspace opens with the full repo tree.

A git-backed workspace is **private** to your user. Collaborators each connect their own workspace to the same repo and coordinate through git branches and pull requests, not through `GRANT` on the workspace.

### Edit and push

1. Open `cortex_project/GROWTH_AGENT.agent.yaml` or `cortex_project/GROWTH_ANALYTICS.osi.yaml` in the workspace editor.
2. Make a change, for example, add a new sample question to the agent or adjust a metric description in the OSI YAML.
3. In the left sidebar, click **Changes**, write a commit message, and click **Commit**.
4. Click **Push** to send the commit to `main`.
5. GitHub Actions picks up the push and the pipeline runs.

## Clean Up

Save any notebook results, evaluation evidence, and source changes you want to retain before removing tutorial resources.

1. Disable the tutorial GitHub Actions workflow and wait for any active runs to finish or cancel them. This prevents another push from recreating resources during cleanup.
2. Ask your administrator to remove the tutorial database `SV_EVAL_CICD` only after confirming it was created exclusively for this exercise. This removes its schema objects, including the demo tables, semantic view, agent, Streamlit app, stages, procedures, and evaluation datasets. Do not remove a database reused by another project.
3. Have the administrator remove `SV_EVAL_CICD_USER` and `SV_EVAL_CICD_ROLE` only if they were created solely for this tutorial and are no longer used elsewhere.
4. Keep `COMPUTE_WH` if it already existed or serves other workloads. Remove a tutorial-only warehouse only after confirming no other workloads use it.
5. Remove tutorial notebooks and the git-backed workspace after saving any work you need. Delete the `SNOWFLAKE_ACCOUNT` repository secret only if no remaining workflow uses it. Keep shared API integrations unchanged.

## Conclusion And Resources

You've built a five-stage eval-gated CI/CD pipeline for Snowflake Semantic Views and Cortex Agents. Pushes to the configured paths on `main` validate the OSI semantic view against the Apache Ossie spec, deploy a candidate agent version, run two quality gates, and promote the candidate when both pass. Before adapting this demo for production, isolate candidate semantic views and dashboards as well as agent versions.

### What You Learned
- How to model a semantic view in vendor-neutral OSI format and validate it with Apache Ossie before deploying to Snowflake
- How Cortex Agent versioning lets you accumulate candidate versions before changing the default
- How to use Cortex Analyst and Cortex Agent evaluations as hard CI gates that block promotion on regressions
- How to simulate a regression and inspect whether the evaluation gate blocks promotion
- How to author YAML changes from a git-backed Snowsight Workspace and feed them directly into the CI/CD pipeline
- How to inspect eval scores and agent versions using companion notebooks

### Related Resources

Documentation:
- [Cortex Agent versioning](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-versioning)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Cortex Analyst evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst-evaluations)
- [Git-backed Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces-git)
- [Apache Ossie (Open Semantic Interchange)](https://github.com/apache/ossie)

Notebooks:
- [01: Explore and Deploy (pre-pipeline)](https://github.com/sfc-gh-cnantasenamat/sfguide-semantic-view-eval-cicd/blob/main/notebook/Semantic_View_Eval_CICD/01_Explore_and_Deploy.ipynb)
- [02: Inspect Pipeline Results (post-pipeline)](https://github.com/sfc-gh-cnantasenamat/sfguide-semantic-view-eval-cicd/blob/main/notebook/Semantic_View_Eval_CICD/02_Inspect_Pipeline_Results.ipynb)

Additional Reading:
- [Getting Started with Cortex Agent Evaluations](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agent-evaluations/)
- [semantic-view-eval-cicd demo repo](https://github.com/sfc-gh-cnantasenamat/semantic-view-eval-cicd)
