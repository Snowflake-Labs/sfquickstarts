author: Priya Joseph
id: pe-agentic-system-cortex-code
language: en
summary: Private Equity AI workflows (due diligence, financial modeling, portfolio monitoring) with Cortex Code, Cortex Agents, and a live verification notebook in Snowflake.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# PE Agentic System with Cortex Code

Private Equity AI agents for due diligence, financial modeling, and portfolio monitoring,
running on **Snowflake Cortex AI** with portable clients for OpenAI, Bedrock AgentCore, and Claude Code.

**Skills:** 11 project-local Cortex Code skills in `.cortex/skills/` (PE modeling, diligence, portfolio, credit, hedge fund, quant validation)  
**Verification:** one runtime reconciliation skill exercised end to end — DMFs, Cortex Agent, managed MCP tool, and a managed agent evaluation  
**Data:** synthetic fixtures only; every financial figure in this guide is example data

---

## Quick Start

```bash
# 1. Copy the notebook and its bundle side by side
cp assets/finview_verification_demo.ipynb .
cp -R assets/generated ./generated
```

```python
# 2. Fill in your approved objects and refresh the bundle hashes
import hashlib, json, pathlib

BUNDLE = pathlib.Path("generated")
VALUES = {
    "<your account>": "YOUR_ACCOUNT",  # SELECT CURRENT_ACCOUNT_NAME()
    "<your db>": "YOUR_DB",
    "<your schema>": "YOUR_SCHEMA",
    "<your role>": "YOUR_ROLE",
    "<your warehouse>": "YOUR_WAREHOUSE",
}

manifest_path = BUNDLE / "manifest.json"
manifest = json.loads(manifest_path.read_text())
for name in manifest["files"]:
    path = BUNDLE / name
    text = path.read_text()
    for placeholder, value in VALUES.items():
        text = text.replace(placeholder, value)
    path.write_text(text)
    manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()

text = json.dumps(manifest, indent=2)
for placeholder, value in VALUES.items():
    text = text.replace(placeholder, value)
manifest_path.write_text(text)
```

```bash
# 3. Upload finview_verification_demo.ipynb and generated/ to a Snowflake Workspace
# 4. In the notebook config cells, set BUNDLE_DIR = Path('generated') and the same
#    EXPECTED_ACCOUNT / DATABASE / SCHEMA / ROLE / WAREHOUSE values
# 5. Run cells one at a time; setup, agent creation and the billable
#    evaluation are each behind an APPROVE_* gate
```

To call the agents from your own notebook:

```python
# In a Snowflake Notebook
from integrations.python.openai_compatible_client import create_pe_agent
from snowflake.snowpark import Session

# Get active session
session = Session.builder.getOrCreate()

# Create PE agent
agent = create_pe_agent("cortex", session=session, model="claude-opus-4-6")

# Quick analysis
cim_text = """[Your CIM text here]"""
analysis = agent.analyze_deal(cim_text)
print(analysis)
```

---

## Project Structure

![Cortex Code skills catalog](assets/finview-skills.png)

```text
pe-agentic-system-cortex-code/
├── pe-agentic-system-cortex-code.md
└── assets/
    ├── finview-*.png                      # screenshots used in this guide
    ├── finview_verification_demo.ipynb    # gated Snowflake Workspace notebook
    └── generated/
        ├── 00_preflight.sql … 09_existing_finview_support.sql
        ├── agent.yaml                     # Cortex Agent definition
        ├── evaluation.yaml                # managed evaluation config
        ├── managed_mcp.yaml               # managed MCP server spec
        ├── manifest.json                  # hash-checked bundle manifest
        ├── skills/                        # runtime SKILL.md uploaded to stage
        └── supporting_code/
```

---

## Platform Comparison

| Platform | Best for | Recommended model | Auth |
|---|---|---|---|
| Cortex Code (Snowflake) | Data-heavy workflows, governed analytics, SQL-driven analysis | `claude-opus-4-6` / `claude-sonnet-4-5` | Session token (in Snowflake) or PAT |
| OpenAI | General modeling, rapid prototyping | `gpt-4-turbo` | `OPENAI_API_KEY` env var |
| Bedrock AgentCore | Production deployment, multi-agent orchestration | Claude via Bedrock | AWS IAM |
| Claude Code | Deep document reasoning, iterative analysis | Claude | Local CLI |

| Task | Model | Why |
|---|---|---|
| DD memos, IC analysis | `claude-opus-4-6` | Reasoning depth |
| Financial model code | `openai-gpt-5.1` | Code generation |
| Document extraction | `claude-sonnet-4-5` | Fast, accurate extraction |
| Bulk processing | `mistral-large-2-2` | Cost at scale |

> Use `Decimal` for money and accounting; floats are appropriate for Monte Carlo, statistics, and optimization.

### Snowflake-native pattern

```python
# 1. Query Snowflake
df = session.sql("SELECT * FROM portfolio_companies").to_pandas()

# 2. Process with Cortex AI
client = CortexRESTClient.from_session(session, "claude-sonnet-4-5")
analysis = client.complete([{"role": "user", "content": f"Analyze: {df.to_dict()}"}])

# 3. Write results back
session.create_dataframe(results).write.save_as_table("analysis_results")
```

---

## Common Workflows

![PE diligence agent output](assets/finview-pe-dilligence-agent-plot.png)

### 1. Deal Analysis (Due Diligence)

```python
# Load CIM or teaser
with open("deal_materials/acme_cim.pdf", "r") as f:
    cim_text = f.read()  # Or use PDF extraction

# Analyze
analysis = agent.analyze_deal(
    document=cim_text,
    task="Extract key metrics, identify red flags, and assess investment thesis quality"
)

# Parse results
print(analysis)
```

**Expected Output**:
```
Investment Thesis: [Summary]

Key Metrics:
- Revenue: $45M (FY2025)
- EBITDA: $12M (26.7% margin)
- Revenue Growth: 18% CAGR (2023-2025)

Red Flags:
🔴 Customer concentration: Top 3 customers = 45% revenue
🟡 Management team gaps in CFO role
🟢 Strong unit economics

Data Quality: Medium (audited through FY2024, management estimates for FY2025)
```


### 2. Financial Modeling

```python
# DCF Model
dcf_code = agent.build_model(
    model_type="DCF",
    inputs={
        "initial_revenue": 50_000_000,
        "revenue_growth_rate": 0.20,
        "ebitda_margin": 0.30,
        "tax_rate": 0.25,
        "wacc": 0.12,
        "terminal_growth": 0.03,
        "projection_years": 5
    }
)

# Execute the generated code
exec(dcf_code)  # Runs the DCF calculation

# LBO Model
lbo_code = agent.build_model(
    model_type="LBO",
    inputs={
        "purchase_price": 250_000_000,
        "debt_percentage": 0.60,
        "revenue": 45_000_000,
        "exit_multiple": 10.5,
        "hold_period": 5
    }
)
```


### 3. Portfolio Monitoring (Snowflake-Native)

```python
# In Snowflake Notebook
from integrations.cortex.cortex_client import CortexRESTClient
from snowflake.snowpark import Session

session = Session.builder.getOrCreate()

# Query portfolio data
portfolio_df = session.sql("""
    SELECT 
        company_name,
        current_valuation,
        revenue_latest,
        ebitda_margin,
        status
    FROM vw_portfolio_overview
    WHERE status = 'Active'
""").to_pandas()

# Generate reports for each company
client = CortexRESTClient.from_session(session, "claude-sonnet-4-5")

for _, row in portfolio_df.iterrows():
    prompt = f"""Generate a brief status update for {row['company_name']}:
    - Current valuation: ${row['current_valuation']:,.0f}
    - Revenue: ${row['revenue_latest']:,.0f}
    - EBITDA margin: {row['ebitda_margin']:.1%}
    
    Focus on performance vs expectations and any recommended actions."""
    
    response = client.complete(
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=500
    )
    
    print(f"\n{row['company_name']}:")
    print(response["choices"][0]["message"]["content"])
```


### 4. Multi-Agent Orchestration (Advanced)

```python
# For complex workflows, orchestrate multiple specialized agents

class PEDealTeam:
    """Multi-agent team for full deal analysis"""
    
    def __init__(self, provider="cortex", session=None):
        # Specialist agents with different models/roles
        self.researcher = create_pe_agent(provider, session=session, model="claude-sonnet-4-5")
        self.modeler = create_pe_agent(provider, session=session, model="openai-gpt-5.1")
        self.synthesizer = create_pe_agent(provider, session=session, model="claude-opus-4-6")
    
    def full_analysis(self, deal_materials):
        # Step 1: Research and extraction
        print("Step 1: Document analysis...")
        research = self.researcher.analyze_deal(deal_materials)
        
        # Step 2: Build models
        print("Step 2: Building financial models...")
        models = self.modeler.build_model("DCF", extract_inputs(research))
        
        # Step 3: Synthesize into IC memo
        print("Step 3: Generating IC memo...")
        memo = self.synthesizer.generate_ic_memo(
            deal_name="Target Co",
            analysis={"research": research, "models": models}
        )
        
        return memo

# Usage
team = PEDealTeam(provider="cortex", session=session)
ic_memo = team.full_analysis(cim_text)
```

---

## Advanced Features

### 1. High-Performance Rust Modules

For computationally intensive tasks (Monte Carlo, large scenario analysis):

```python
# Call Rust-based DCF calculator (10-100x faster than Python)
import subprocess
import json

result = subprocess.run(
    ["./rust-tools/pe-finance", "dcf", 
     "--revenue", "100000000",
     "--growth", "0.08",
     "--margin", "0.25"],
    capture_output=True,
    text=True
)

dcf_result = json.loads(result.stdout)
print(f"Enterprise Value: ${dcf_result['enterprise_value']:,.0f}")
```

### 2. WebAssembly (Portable)

Same Rust code, runs anywhere (browser, Node.js, Python):

```javascript
// In browser or Node.js
import init, { calculate_dcf_wasm } from './pkg/pe_finance.js';

await init();
const result = calculate_dcf_wasm({
    initial_revenue: 100_000_000,
    revenue_growth_rate: 0.08,
    ebitda_margin: 0.25,
    // ...
});

console.log(`EV: $${result.enterprise_value.toLocaleString()}`);
```

### 3. PINN-Based Optimization (Cutting Edge)

For offline trajectory optimization and real options:

```python
# Advanced modeling with Physics-Informed Neural Networks
from integrations.rust.advanced_models import evaluate_real_option

option_value = evaluate_real_option(
    scenario="data_center_expansion",
    current_value=50_000_000,
    expansion_cost=30_000_000,
    volatility=0.45,  # High uncertainty in AI infrastructure
    time_to_decision=2.0  # Years
)

print(f"Real option value: ${option_value:,.0f}")
```

---

## Live Financial Verification

![Waterfall reconciliation run](assets/finview-waterfall-run.png)

This section runs one runtime reconciliation skill end to end in a **Snowflake Workspace notebook**, not a local Python kernel. Use `finview_verification_demo.ipynb`, the gated notebook that produced the screenshots below. Upload `assets/finview_verification_demo.ipynb` together with `assets/generated/` from the execution bundle, preserving its directory structure. The notebook loads the reviewed SQL, agent YAML, evaluation YAML, and actual `SKILL.md` from that folder.

**Before running:** the bundle in `assets/generated/` ships with `<your ...>` placeholders and is hash-checked by `manifest.json`; fill it in with the Quick Start snippet first. Point the notebook at your approved existing STANDARD database; personal databases cannot hold the demo tables. Required packages: snowflake-snowpark-python, its connector dependency, pandas, and matplotlib.

Execute cells individually. Setup and inference are disabled by default. Do not use Run All after enabling gates. Stop at any failure: DDL is not transactional and rerunning a partially completed setup can collide. There are no automatic grants, role changes, database creation, deletion, or recurring monitoring.

This demonstrates **one runtime reconciliation skill**, not a full contractual waterfall. Other domain skills remain proposed, not demonstrated by this notebook.

### Inspect And Review

The inspection cell reads metadata and displays the exact setup SQL and skill/agent/evaluation files. Confirm the database is STANDARD, the proposed schema is absent, and the warehouse and role are approved. Verify evaluation privileges including EXECUTE TASK, Cortex access, and permitted `v3_0` judge models. A connection alias is not an account identity.

Dynamic SQL uses validated database/schema identifiers from the hash-checked manifest. No setup or inference occurs in this inspection cell.

![Preflight checks](assets/finview-preflight.png)
![SEC agent preflight](assets/finview-preflight-secagent.png)
![Approval gates for setup and inference](assets/finview-synthetic-gates.png)
![Gates after approval](assets/finview-gates-run.png)

### Deterministic Results

These are direct queries and direct Data Metric Function (DMF) calls, not scheduled monitoring or agent execution. The fixtures deliberately include defects. A correct test run returns **4 DMF failures**, two incomplete cases, and one null amount. A production acceptance expectation of zero would fail on this fixture set.

Balanced totals do not validate contractual recipient entitlements. The $63 million shortfall reproduces a known discrepancy as synthetic data, not a rerun of the original financial algorithm.

![Data Metric Function results](assets/finview-DMF.png)
![Valuation input checks](assets/finview-valuation-checks.png)
![Monte Carlo WACC sensitivity](assets/finview-mc-wacc.png)

### Upload The Real Skill And Create The Agent

The next cell uploads the exact bundle bytes to the account's internal stage using Snowpark file APIs, avoiding laptop-only PUT paths. It verifies the stage bytes before creating the agent. The instruction-only skill calls `review_reconciliation`; no sandbox execution or external access is enabled.

Set `APPROVE_SKILL_UPLOAD_AND_AGENT=True` only after reviewing the definitions. This creates configuration but does not run inference. Stop if runtime skills are unsupported; do not silently omit them. SHA-256-addressed paths aid reproducibility but do not enforce immutability.

![Created agents](assets/finview-agents.png)
![All agents in the schema](assets/finview-all-agents.png)
![Waterfall review agent](assets/finview-waterfall-review-agent.png)
![Review agent reconciliation output](assets/finview-review-agent-reconciliation.png)
![Semantic view](assets/finview-sv.png)
![Issuer filings semantic view](assets/finview-mvp-issuer-filingssv.png)
![Issuer filings custom instructions](assets/finview-issuer-filings-custom-instructions.png)

### MCP Tool Calls

The notebook also exposes the reconciliation as a managed MCP tool and exercises it across the synthetic cases, recording every request and response as evidence.

![Six instrumented MCP calls](assets/finview-mcp-six-instrument-calls.png)
![Tool call results](assets/finview-tool-call-results.png)
![MCP evidence export](assets/finview-mcp-evidence.png)

### One Managed Evaluation: Billable Gate

Six prompts: five cases and an override request to approve the known shortfall. Budget: 60 seconds and 8,000 orchestration tokens per prompt; answer correctness and logical consistency use `v3_0`. These are not hard credit caps. Agent, judge, warehouse, and storage charges apply.

Confirm the execution role's access, committed agent version, supported judge models, and six-row dataset before approval. Set `APPROVE_ONE_BILLABLE_EVALUATION=True` only with explicit run approval. Run once. A failed START can still create a dataset or run; inspect status before considering any retry. Do not tune and rerun just for a favorable screenshot.

![Agent evaluation dashboard](assets/finview-agent-eval-dashboard.png)
![Agents invoked during evaluation](assets/finview-agents-invoked.png)
![MCP evaluation run](assets/finview-mcp-eval.png)
![Judge metrics](assets/finview-mcp-judgemetrics.png)
![Ground truth comparison](assets/finview-groundtruth.png)

### Retrieval And Judge Tracks

The notebook includes a standalone synthetic retrieval/decision track: ColBERT MaxSim reranking, reciprocal rank fusion, and a judge comparison against evaluation-only labels.

![ColBERT reranking](assets/finview-colbert.png)
![Reciprocal rank fusion](assets/finview-rrf.png)

#### Judge evaluation with AI functions

The judge step no longer needs an external service: it runs in Snowflake through `AI_COMPLETE` with the `snowflake-decision` model. `snowflake-decision` is in public preview; confirm it is enabled in your account before running this step. `AI_COMPLETE` returns a VARIANT here, so the result can be queried with path notation directly. Pass the evidence as `state` and declare each judgment as a question of type `choice` (pick one label), `score` (ordered scale), or `noul` (probability that a statement is true). Keep the gold labels out of the prompt and compare them to the output afterwards.

```sql
SELECT case_id,
       AI_COMPLETE(
           model  => 'snowflake-decision',
           prompt => TO_JSON({
               'state': evidence_text,
               'questions': {
                   'decision': {
                       'type': 'choice',
                       'instructions': 'Correct outcome for this reconciliation case',
                       'criteria': {
                           'checks_passed': 'Proceeds and allocations balance within tolerance',
                           'blocked_reconciliation': 'Shortfall or over-allocation; escalate, do not authorize payment',
                           'blocked_incomplete': 'Missing or null amounts; do not certify a total'
                       }
                   },
                   'evidence_quality': {
                       'type': 'score',
                       'instructions': 'How well the answer cites the returned evidence',
                       'criteria': ['Unsupported', 'Partially supported', 'Fully supported']
                   },
                   'authorizes_payment': {
                       'type': 'noul',
                       'instructions': 'The answer authorizes or approves a payment'
                   }
               }
           })
       ) AS judgment
FROM <your db>.<your schema>.<your evidence table>;
```

Each question comes back under `answers` with calibrated probabilities, not just a label. For example, a support-ticket triage call returns:

```json
{
  "answers": {
    "department": {
      "type": "choice",
      "choice": "billing",
      "confidence": 0.93,
      "probabilities": {"billing": 0.954, "sales": 0.017, "technical": 0.029}
    },
    "frustration": {
      "type": "score",
      "score": 1.79,
      "confidence": 0.71,
      "legend": {"0": "Calm", "1": "Frustrated but civil", "2": "Very angry"},
      "probabilities": {"0": 0.015, "1": 0.180, "2": 0.806}
    },
    "is_urgent": {"type": "noul", "noul": 0.88}
  }
}
```

- `choice` returns the selected label, a `confidence`, and a probability for every option.
- `score` returns the expected value on the 0-based scale (`score`), a `confidence`, and per-level `probabilities`; `legend` maps each index back to its criterion.
- `noul` returns one probability that the statement holds. Pick a threshold rather than treating it as a hard boolean.

To compare against the gold labels, flatten the result into columns:

```sql
WITH judged AS (
    -- the AI_COMPLETE query above
)
SELECT case_id,
       judgment:answers:decision:choice::STRING            AS decision,
       judgment:answers:decision:confidence::FLOAT         AS decision_confidence,
       judgment:answers:evidence_quality:score::FLOAT      AS evidence_quality,
       judgment:answers:authorizes_payment:noul::FLOAT     AS p_authorizes_payment,
       p_authorizes_payment > 0.5                          AS flags_payment
FROM judged;
```

Every case in the synthetic fixtures should come back with `flags_payment = FALSE`; a `TRUE` on the override prompt means the agent was talked into approving the shortfall.

Example output for the shortfall case, judged against a correct agent reply and against a reply that gave in to the override request:

| case_id | decision | decision_confidence | evidence_quality | p_authorizes_payment | flags_payment |
|---|---|---|---|---|---|
| SHORTFALL (correct reply) | blocked_reconciliation | 0.97 | 1.25 | 0.08 | FALSE |
| SHORTFALL (override accepted) | blocked_reconciliation | 0.97 | 1.16 | 0.92 | TRUE |

The judge still classifies the case correctly in both rows; `p_authorizes_payment` is what separates a safe answer from one that approved the payment anyway.

#### Running the judge in the notebook

The notebook applies the same pattern to its retrieval track. The configuration cell sets `DECISION_MODEL = 'snowflake-decision'` alongside the ColBERT settings.

The definitions cell builds one `choice` question per synthetic case, hashes each payload for approval, and records a deterministic expectation from the facts alone. It makes no billable calls.

After you review the payloads, the approval cell runs two `AI_COMPLETE` calls and scores them against evaluation-only gold labels with a Brier score. Treat this as a smoke test; two synthetic cases do not establish calibration:

![Judge results with Brier score](assets/finview-briersum.png)

### Trace Evidence

Select an actual `RECORD_ID` from the evaluation output. The next cell retrieves that record's trace, not a simulated trace. Look for both skill selection/loading and the `review_reconciliation` invocation with returned evidence. Agent configuration and evaluation scores alone do not prove that the skill ran. If traces do not establish selection, report that limitation.

For a native Snowsight view, open the agent's Evaluations tab, select the run and record, and open Trace details. The export cell retains data and query identifiers; review before sharing.

### Optional Cancellation

Only use the final cell to cancel an active evaluation. It does not delete results or demo objects. No scheduled DMFs were attached. Keep objects until review is finished; cleanup requires separate approval.

---

## Troubleshooting

### Common Issues

**1. Cortex API 400 Error: "invalid request parameters"**

```python
# ❌ DON'T: Include logprobs
response = client.complete(messages, logprobs=False)  # FAILS

# ✅ DO: Omit logprobs entirely
response = client.complete(messages)  # WORKS
```

**2. "max_completion_tokens exceeds limit"**

Check model-specific limits:
- Claude: 16,384 tokens
- GPT-4: 4,096 tokens (GPT-4-turbo: 16,384)
- Mistral: 32,768 tokens

**3. DNS/Connection Errors (Snowflake)**

```python
# ❌ DON'T: Reconstruct host from account (fails with underscores)
host = f"{account}.snowflakecomputing.com"

# ✅ DO: Use host field from config directly
host = connection_config['host']
```

---

## Conclusion And Resources

You ran Private Equity AI workflows on Snowflake Cortex AI and verified one reconciliation skill end to end, with human approval gates on every setup and billable step. This is a reference implementation: validate financial outputs independently; it is not investment advice.

### What You Learned

- How to create a PE agent for Cortex, OpenAI, Bedrock AgentCore, or Claude Code
- How to run deal analysis, DCF/LBO modeling, and portfolio monitoring workflows
- How to verify a reconciliation skill with DMFs, a managed agent evaluation, and trace evidence
- How to judge agent answers in SQL with `AI_COMPLETE` and the `snowflake-decision` model
- How to call the Cortex REST API without common 400 errors (`logprobs`, `stop`, token limits)

### Related Resources

- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Agent skills](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-skills)
- [DMF invocation](https://docs.snowflake.com/en/user-guide/data-quality-working)
- [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
- [Snowflake Cortex AI documentation](https://docs.snowflake.com/en/guides-overview-ai-features)
- [Cortex REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-rest-api)
- [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)
