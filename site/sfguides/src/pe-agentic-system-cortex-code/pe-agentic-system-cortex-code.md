author: Priya Joseph
id: pe-agentic-system-cortex-code
language: en
summary: Verify a synthetic private-equity reconciliation workflow with deterministic checks, a Cortex Agent, approval gates, and evaluation evidence.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts

# PE Agentic System with Cortex Code

## Overview

Build a review workflow for synthetic private-equity distribution data. Start with
deterministic reconciliation checks, expose the evidence to a Cortex Agent, and
optionally run a managed evaluation. Inspect the trace before claiming that the
agent selected a skill or invoked a tool.

This tutorial covers one reconciliation workflow, not a complete contractual
waterfall, investment recommendation, or production financial system. All amounts
are synthetic. Balanced totals do not establish recipient entitlements.

### Prerequisites

- Familiarity with SQL, Python, and Snowflake notebooks.
- Ability to review proposed SQL, agent definitions, and evaluation configuration.
- An administrator-approved environment for creating the demo objects.

### What You'll Learn

- Separate deterministic financial checks from model-generated explanations.
- Configure and verify a hash-checked execution bundle.
- Review and explicitly approve setup, skill upload, and a billable evaluation.
- Inspect evaluation results and traces without confusing configuration with execution.

### What You'll Build

- Five synthetic reconciliation cases, including deliberately invalid cases.
- A direct Data Metric Function (DMF) check and a reconciliation review function.
- A Cortex Agent configured with a reconciliation skill.
- Optionally, a six-prompt managed evaluation and an evidence export.

### What You'll Need

- Access to a Snowflake Workspace notebook and an approved existing STANDARD
  database, role, and warehouse. Do not use a personal `USER$` database.
- Privileges for the objects in the setup bundle. Ask your administrator to review
  the SQL before running it; this tutorial does not automatically grant privileges.
- Account support for the agent skill and managed evaluation features used in the
  bundle. Confirm availability and judge-model access before proceeding.
- Python 3.10 or later locally for bundle preparation, plus Git.
- Notebook packages: `snowflake-snowpark-python`, its connector dependency,
  `pandas`, and `matplotlib`.
- Approval for warehouse, agent, judge, and storage charges before the optional
  evaluation. Time/token budgets are not hard credit caps.

The [companion project](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system)
contains the notebooks, SQL, Python, Rust, tests, and project-local Cortex Code
skills under this guide's `assets/pe-agentic-system/` directory. Non-image assets
are available from the Git repository, not from the published guide website.

![Project-local Cortex Code skills](assets/finview-skills.png)

## Step 1: Get the Code

Clone the Quickstarts repository and enter the companion project directory:

```bash
git clone https://github.com/Snowflake-Labs/sfquickstarts.git
cd sfquickstarts/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system
python3 tools/verify_bundle.py
```

The verifier should report 35 artifact hashes and the skill hash verified. A
matching hash proves file integrity relative to the manifest, not correctness or
authorization to execute the file.

Review these files before continuing:

- [Notebook](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/finview_verification_demo.ipynb)
- [Execution bundle](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated)
- [Setup SQL](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/01_setup.sql)
- [Manifest](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/manifest.json)

**Do not use Run All.** The notebook contains multiple exploratory tracks outside
the tutorial path. Every approval flag starts as `False`. Any cell that creates,
replaces, deletes, or bills raises an error until you set its `APPROVE_*` flag to
`True` in a separate cell. Use only the reconciliation block identified below, in a fresh
kernel. Review each cell before executing it. Other cells are not prerequisites.

## Step 2: Configure the Bundle

In the companion project directory, replace the five placeholder values in the following
script with your approved targets and run it locally. Use simple uppercase,
unquoted identifiers for database, schema, role, and warehouse. The schema must
be new for fresh setup; the database should already exist and be approved.

```python
import json
from pathlib import Path

bundle = Path("generated")
values = {
    "<your account>": "YOUR_ACCOUNT",
    "<your db>": "YOUR_DB",
    "<your schema>": "YOUR_SCHEMA",
    "<your role>": "YOUR_ROLE",
    "<your warehouse>": "YOUR_WAREHOUSE",
}
if any(value.startswith("YOUR_") for value in values.values()):
    raise ValueError("Replace every YOUR_* value with an approved target first.")

manifest_path = bundle / "manifest.json"
manifest = json.loads(manifest_path.read_text())
for name in manifest["files"]:
    artifact = (bundle / name).resolve()
    if not artifact.is_relative_to(bundle.resolve()):
        raise ValueError(f"Artifact outside bundle: {name}")
    text = artifact.read_text()
    for placeholder, value in values.items():
        text = text.replace(placeholder, value)
    artifact.write_text(text)

text = json.dumps(manifest, indent=2)
for placeholder, value in values.items():
    text = text.replace(placeholder, value)
manifest_path.write_text(text + "\n")
```

Review the resulting changes, then refresh the integrity manifest:

```bash
git diff -- generated
python3 tools/verify_bundle.py --refresh
python3 tools/verify_bundle.py
```

Do not commit your account-specific bundle back to the public repository. Refresh
hashes only after reviewing the edits; do not use it to bypass an unexplained
hash mismatch.

## Step 3: Open the Notebook

Upload `finview_verification_demo.ipynb` and the configured `generated/` directory
to the same folder in your Snowflake Workspace, preserving the bundle's nested
directories. Open the notebook with the required packages and a fresh kernel.

Locate the reconciliation configuration cell containing both `BUNDLE_DIR` and
`SETUP_MODE` (zero-based cell 28 in the companion version prepared for this guide).
The tutorial runs cells 28-38 only. Identify cells by their content as well as
their position; cell numbers can change when you edit a notebook.

Before running that configuration cell:

1. Change `BUNDLE_DIR` to `Path('generated')`.
2. Set `EXPECTED_ACCOUNT`, `DATABASE`, `SCHEMA`, `ROLE`, and `WAREHOUSE` to the
   same approved values used in the manifest.
3. Set `SETUP_MODE = 'fresh'` for a new demo schema. The existing default,
   `reuse_finview`, expects previously created fixtures and is not a first-run mode.
4. Keep `APPROVE_SETUP`, `APPROVE_SKILL_UPLOAD_AND_AGENT`,
   `APPROVE_ONE_BILLABLE_EVALUATION`, and `APPROVE_CANCEL` set to `False`.

Run only this configuration cell. It verifies bundle hashes and account identity,
then explicitly selects the configured role and warehouse. Confirm the displayed
context before proceeding. A connection alias is not an account identity.

## Step 4: Review and Set Up

Run the next cell, beginning with `execute_file('00_preflight.sql')`. It displays
the setup SQL, support SQL, agent and evaluation definitions, and runtime skill.
Confirm the database is STANDARD and the proposed fresh schema does not exist.
Ask your administrator to verify required privileges, including evaluation task
privileges and Cortex model access if you will use the optional evaluation.

![Preflight checks](assets/finview-preflight.png)

The approval flags start as `False`. The first screenshot shows the gates before approval, the second after you set them in a separate cell:

![Approval gates before setup](assets/finview-synthetic-gates.png)
![Approval gates after approval](assets/finview-gates-run.png)

After reviewing the exact statements, set `APPROVE_SETUP = True` in a separate
cell and run the setup cell beginning with `if not APPROVE_SETUP:` once. The gate
resets to `False` before execution. Do not rerun the configuration cell to approve
setup; doing so resets the gates.

**Fresh setup can create a database if it is absent.** Use an approved existing
database and verify its name first. Setup is not transactional. If any statement
fails, inspect the partially created state; do not rerun blindly or execute the
notebook's separate deletion/redeployment cells.

## Step 5: Check the Evidence

Run the cell that calls `execute_file('02_checks.sql')` and checks
`expected_status`. It verifies the five synthetic case outcomes:

- `BALANCED`: `checks_passed`.
- `SHORTFALL` and `OVERALLOCATED`: `blocked_reconciliation`.
- `MISSING` and `INCOMPLETE`: `blocked_incomplete`.

The direct DMF call must return **4 intentionally failed cases**. This is expected
for these fixtures; an acceptance rule requiring zero failures would reject them.
Do not reinterpret missing allocations as zero. The shortfall case represents a
synthetic $63 million discrepancy, not a rerun of a production financial algorithm.

![Data Metric Function results](assets/finview-DMF.png)
![Reconciliation results](assets/finview-waterfall-run.png)

The notebook also runs input checks on valuation assumptions and a Monte Carlo sensitivity on WACC. Both use synthetic inputs:

![Valuation input checks](assets/finview-valuation-checks.png)
![Monte Carlo WACC sensitivity](assets/finview-mc-wacc.png)

The following plotting cell is optional. Stop before agent creation if the fixture
status or DMF assertions fail. These direct queries do not establish that an agent
or skill executed.

## Step 6: Create the Agent

Review the
[agent definition](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/agent.yaml)
and
[runtime skill](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/skills/waterfall-reconciliation-review/SKILL.md).
The instruction-only reconciliation skill uses the `review_reconciliation` tool.

Set `APPROVE_SKILL_UPLOAD_AND_AGENT = True` in a separate cell. Run the cell
starting with `if not APPROVE_SKILL_UPLOAD_AND_AGENT:` once. It resets the gate,
uploads the skill and evaluation configuration, verifies downloaded stage bytes,
and executes the agent-creation SQL. This creates configuration; it does not prove
that the agent invoked a skill.

![Waterfall review agent](assets/finview-waterfall-review-agent.png)
![Created agents](assets/finview-agents.png)

An example answer, in which the agent blocks the shortfall case and cites the reconciliation evidence:

![Review agent reconciliation output](assets/finview-review-agent-reconciliation.png)

If runtime skills or the definition are unsupported, stop rather than silently
omitting the skill. Hash-addressed stage paths aid reproducibility but do not
enforce immutability.

## Step 7: Evaluate Optionally

Skip this step if you do not have approval for billable execution. Review the
[evaluation configuration](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/evaluation.yaml)
and confirm the created agent version, judge availability, and six-row input
dataset. The prompts include the five cases and an override request to approve
the known shortfall.

Set `APPROVE_ONE_BILLABLE_EVALUATION = True` in a separate cell, then run the
cell starting with `if not APPROVE_ONE_BILLABLE_EVALUATION:` once. It resets the
gate and records that a start was attempted. A failed start can still create
evaluation state; inspect status before considering a retry.

The next status/results cell may be rerun to check progress. Do not rerun START
to poll for results. Review failed records rather than tuning and repeating the
evaluation solely to obtain a favorable screenshot.

![Evaluation dashboard example](assets/finview-agent-eval-dashboard.png)
![Ground truth comparison example](assets/finview-groundtruth.png)
![Agents invoked during evaluation](assets/finview-agents-invoked.png)

Screenshots illustrate prior runs; your account, model availability, and outputs
may differ. A small synthetic evaluation is a smoke test, not evidence of
production accuracy or calibrated financial risk.

## Step 8: Inspect Traces

Select a real `RECORD_ID` from the evaluation output and set it in the next trace
cell. Inspect the trace for skill selection/loading and the reconciliation tool
invocation with returned evidence. Report uncertainty if the trace does not
establish that the skill ran; agent configuration and aggregate scores are not
substitutes for execution evidence.

You can also open the agent's Evaluations tab in Snowsight, select the run and
record, and inspect Trace details.

Run the evidence-export cell only if you intend to retain the results locally.
Review exported rows and query identifiers before sharing them. If an evaluation
is still active and you need to cancel it, review the final cancellation cell and
explicitly enable `APPROVE_CANCEL`. Cancellation does not delete demo objects.
This walkthrough does not attach scheduled DMFs. Obtain separate approval for
object cleanup; do not run the notebook's unrelated deletion cells.

## Optional Companion Examples

The repository also includes exploratory MCP, retrieval/judge, financial modeling,
and Rust examples. They are not required for this tutorial and are not covered by
the reconciliation block's approvals or validation. Each track has its own
`APPROVE_*` flags. Review their requirements, feature availability, and side
effects independently. The screenshots below come from earlier runs.

### Managed MCP Tool

The notebook can expose the reconciliation as a managed MCP tool, call it for each
synthetic case, and export every request and response as evidence. A TruLens run
then scores those calls with a Cortex judge model.

![Six instrumented MCP calls](assets/finview-mcp-six-instrument-calls.png)
![Tool call results](assets/finview-tool-call-results.png)
![MCP evidence export](assets/finview-mcp-evidence.png)
![MCP evaluation run](assets/finview-mcp-eval.png)
![MCP judge metrics](assets/finview-mcp-judgemetrics.png)

### SEC Filing Agents

A separate track builds semantic views over SEC filing data and two analyst agents
for diligence and capital-markets disclosure. Run its preflight cell before
creating anything.

![SEC agent preflight](assets/finview-preflight-secagent.png)
![Semantic view](assets/finview-sv.png)
![Issuer filings semantic view](assets/finview-mvp-issuer-filingssv.png)
![Issuer filings custom instructions](assets/finview-issuer-filings-custom-instructions.png)
![All agents in the schema](assets/finview-all-agents.png)
![PE diligence agent output](assets/finview-pe-dilligence-agent-plot.png)

### Retrieval And Judge

A standalone synthetic track reranks passages with ColBERT MaxSim, fuses rankings
with reciprocal rank fusion, and judges answers with `AI_COMPLETE` and the
`snowflake-decision` model. The model is in public preview. The judge scores two
synthetic cases with a Brier score. Treat it as a smoke test, not a calibration
result.

![ColBERT reranking](assets/finview-colbert.png)
![Reciprocal rank fusion](assets/finview-rrf.png)
![Judge results with Brier score](assets/finview-briersum.png)

### More Companion Files

- [Managed MCP notes](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/generated/managed_mcp_readme.md)
- [Project-local Cortex Code skills](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/.cortex/skills)
- [Reference implementation and limitations](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/readme.md)
- [Financial and performance claims](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/claims.md)
- [Rust implementation](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system/integrations/rust)

Do not automatically execute model-generated code or treat illustrative DCF/LBO
examples as validated financial models.

## Troubleshooting

- **Bundle hash mismatch:** stop and compare the artifact to your reviewed copy.
  Refresh hashes only for intentional, reviewed edits.
- **Wrong account or context:** select the approved notebook account, then verify
  the configured role and warehouse. Do not change configuration to conceal a mismatch.
- **Schema already exists:** inspect its state. Use `reuse_finview` only if the
  existing fixtures match the notebook's checks; do not delete it to force a retry.
- **No evaluation rows yet:** rerun only the status/results cell, not START.
- **Unsupported agent or judge feature:** stop and confirm availability with your
  administrator. Do not weaken the verification steps to make the demo pass.

## Conclusion And Resources

You prepared a reviewed execution bundle, checked deliberately flawed synthetic
financial data, and configured a reconciliation agent. If you completed the
optional evaluation, you also inspected its outputs and trace evidence. Validate
financial conclusions independently; this reference implementation is not
investment advice.

### What You Learned

- Use deterministic checks before accepting an agent's financial explanation.
- Keep integrity checks, human approval, and execution evidence separate.
- Run setup and optional evaluation deliberately, without blind retries.
- Distinguish a synthetic smoke test from production validation.

### Related Resources

- [Companion project](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/pe-agentic-system-cortex-code/assets/pe-agentic-system)
- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Data quality monitoring](https://docs.snowflake.com/en/user-guide/data-quality-working)
- [Snowflake Cortex AI](https://docs.snowflake.com/en/guides-overview-ai-features)