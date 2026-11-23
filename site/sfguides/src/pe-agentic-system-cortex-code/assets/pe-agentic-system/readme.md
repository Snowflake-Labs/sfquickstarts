# Private Equity Agentic System

## Quickstart companion

This repository contains the companion code for **PE Agentic System with Cortex
Code**. This copy lives under the guide's `assets/pe-agentic-system/` directory.
Non-image files must be obtained from Git, not the published guide website.

- `finview_verification_demo.ipynb`: original exploratory notebook, preserved
  without execution or code changes during extraction.
- `generated/`: reviewed SQL, agent/evaluation definitions, and a SHA-256 manifest.
- `.cortex/skills/`: project-local Cortex Code skills.
- `assurance/`, `tests/`, `examples/`, and `integrations/`: supporting reference code.

**Do not Run All.** The notebook includes multiple independent tracks. Every
approval flag starts as `False`. Any cell that creates, replaces, deletes, or bills
raises an error until you set its `APPROVE_*` flag to `True`. The Quickstart
uses only the reconciliation block (zero-based cells 28-38 in this version).
Review every cell before execution; set the bundle path to `Path('generated')`
and configure an approved account, role, warehouse, and STANDARD database.
The initial configuration cell changes session role and warehouse. Fresh setup
can create a database if absent. Other tracks require separate review.

Run `python3 tools/verify_bundle.py` locally before configuring the bundle.
This validates artifact hashes without connecting to Snowflake. It does not
prove financial correctness or that a notebook is safe to execute.

The Rust package retains its existing MIT declaration.

**AI-powered analytical workflow platform for the private markets deal lifecycle**

> **Status: reference implementation, not production.** Read
> [`claims.md`](claims.md) before quoting any figure from this repo. Summary of
> what is and isn't true today:
>
> - The **Rust crate now builds** (rustc 1.98.1) — see *Building the Rust extension*
>   below. It had never compiled before 2026-09-09 (5 errors), which meant its 12
>   unit tests had never run. One of them was sitting on a waterfall bug that failed
>   to distribute **21% of an exit**. Now fixed; 12/12 pass.
> - **Measured Rust speedups are 1.4x (Monte Carlo vs vectorized NumPy) and 7.2x
>   (decimal DCF vs Python decimal).** The former "30-100x" claim is withdrawn — it
>   originated in a hardcoded print string labeled `"estimated"`.
> - **"Agentic" is aspirational.** There is no agent loop — no planning, tool
>   selection, or iterative evaluation. The real flow is a fixed, auditable
>   linear sequence, which for high-consequence finance is arguably correct.
> - The **ROI table is illustrative estimates**, not measurements.
> - The **assurance boundary is real and tested** — see `assurance/`,
>   `tests/test_assurance.py` (25 passing), `examples/assurance_boundary_demo.py`.
>   This is the most defensible part of the architecture.
> - **Use the string entry points for money.** `py_dcf_exact` takes strings; the
>   legacy f64 functions corrupt monetary inputs before the decimal engine runs.

## Building the Rust extension (`pe_finance`)

Optional — all Python code, benchmarks, and the assurance boundary work without it.
Required for the Rust benchmark columns and the 5 cross-language parity tests.

```bash
cd integrations/rust
./build.sh --test          # build, install, run cargo tests + parity suite
```

Manual equivalent:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
export PATH="$HOME/.cargo/bin:$PATH"
python3 -m pip install maturin
cd integrations/rust
python3 -m maturin build --release --features python
python3 -m pip install --force-reinstall target/wheels/pe_finance-*.whl
```

**`--features python` is mandatory** — PyO3 is not a default feature, and without it
you get a library with no Python module and a runtime `ImportError` with no build
error to explain it. Full list of gotchas in
[`integrations/rust/benchmarks/README.md`](integrations/rust/benchmarks/README.md).

Verify parity was actually checked, not skipped:

```bash
python3 -m pytest tests/test_decimal_parity.py -q   # expect 37 passed, 0 skipped
```

`32 passed, 5 skipped` means the extension is not installed and the
Rust columns plus all cross-language parity assertions were silently skipped.

[![Platform](https://img.shields.io/badge/Platform-Multi--Platform-blue)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-green)]()
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-orange)]()
[![License](https://img.shields.io/badge/License-Reference-yellow)]()

---

## Overview

A comprehensive, portable agentic system for Private Equity workflows that runs on:
- ✅ **Claude Code** - Deep reasoning and prototyping
- ✅ **Cortex Code (Snowflake)** - Data-native portfolio analytics
- ✅ **Bedrock AgentCore** - Production orchestration
- ✅ **OpenAI** - General-purpose completion

### Key Features

- **🎯 Full PE Lifecycle Coverage**: Sourcing → DD → Modeling → Portfolio Management → Exit
- **🔬 Institutional Rigor**: GAAP/IFRS compliance, proper Decimal math, sensitivity analysis
- **⚡ High Performance**: Rust/WebAssembly modules for computationally intensive tasks
- **🔒 Audit Trail**: Full lineage tracking and explainability
- **🔄 Platform Portable**: Core logic works everywhere with platform-specific optimizations

---

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
# Clone or download this repo
cd pe-agentic-system

# Install Python dependencies
pip install -r requirements.txt

# Optional: Install Rust for high-performance modules
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Choose Your Platform

#### Option A: Cortex Code (Snowflake)

```python
from integrations.python.openai_compatible_client import create_pe_agent
from snowflake.snowpark import Session

session = Session.builder.getOrCreate()
agent = create_pe_agent("cortex", session=session)

# Analyze a deal
analysis = agent.analyze_deal(cim_text)
```

#### Option B: OpenAI

```python
from integrations.python.openai_compatible_client import create_pe_agent
import os

os.environ["OPENAI_API_KEY"] = "sk-..."
agent = create_pe_agent("openai")

# Build a model
code = agent.build_model("DCF", {"revenue": 50e6, "growth": 0.20, ...})
```

#### Option C: Bedrock

```python
from integrations.python.openai_compatible_client import create_pe_agent

agent = create_pe_agent("bedrock", region="us-east-1")

# Generate IC memo
memo = agent.generate_ic_memo("Deal X", analysis_dict)
```

#### Option D: Claude Code

```bash
# In terminal
cd pe-agentic-system

# Then in Claude Code conversation:
@AGENTS.md @financial-modeling-skill.md

Build a DCF model for a SaaS company with $50M revenue...
```

---

## Architecture

```
pe-agentic-system/
│
├── AGENTS.md                      # Core agent instructions (auto-loaded)
├── QUICKSTART.md                  # Detailed getting started guide
├── README.md                      # This file
│
├── CLAIMS.md                      # Status of every claim this repo makes
│
├── assurance/                     # THE VALIDATED BOUNDARY
│   ├── __init__.py
│   └── contracts.py              # LLM output -> typed schema -> policy -> engine
│
├── skills/                        # PLANNED — DOES NOT EXIST YET
│   ├── financial-modeling/       # (referenced by AGENTS.md; not implemented)
│   │   ├── SKILL.md              # DCF, LBO, comps, waterfalls
│   │   └── templates/
│   ├── due-diligence/
│   │   ├── SKILL.md              # DD automation & synthesis
│   │   └── checklist_templates/
│   ├── portfolio-monitoring/
│   │   ├── SKILL.md              # KPI tracking, reporting
│   │   └── dashboard_templates/
│   └── advanced-modeling/
│       ├── SKILL.md              # PINNs, real options, Monte Carlo
│       └── examples/
│
├── integrations/
│   ├── cortex/
│   │   ├── cortex_client.py      # Cortex REST API client
│   │   └── schema.sql            # PLANNED — DOES NOT EXIST YET
│   ├── python/
│   │   ├── openai_compatible_client.py  # Unified client
│   │   └── utils.py
│   └── rust/
│       ├── Cargo.toml
│       ├── src/
│       │   ├── dcf.rs
│       │   ├── lbo.rs
│       │   ├── monte_carlo.rs
│       │   └── lib.rs            # PyO3 bindings
│       └── README.md
│
├── examples/
│   ├── complete_deal_workflow.ipynb    # End-to-end demo
│   ├── portfolio_monitoring.ipynb      # Ongoing management
│   ├── multi_agent_dd.py               # Orchestration example
│   └── bedrock_deployment/             # Production patterns
│
├── docs/
│   ├── architecture.md
│   ├── model_recommendations.md
│   ├── troubleshooting.md
│   └── advanced_topics.md
│
└── requirements.txt
```

---

## Core Capabilities

### 1. Financial Modeling

**Supported Models**:
- Discounted Cash Flow (DCF)
- Leveraged Buyout (LBO)
- Comparable Company Analysis
- Precedent Transactions
- Cap Table & Waterfall
- 409A Valuations
- Real Options (Black-Scholes extensions)

**Features**:
- ✅ Decimal precision for financial calculations
- ✅ Automatic sensitivity analysis
- ✅ Scenario modeling (base/upside/downside)
- ✅ Excel-compatible export
- ✅ Rust/Wasm acceleration for heavy computation

### 2. Due Diligence Automation

**Capabilities**:
- CIM/Teaser extraction and summarization
- Financial spreading and normalization
- Quality of Earnings (QoE) analysis
- Red flag detection
- Management question generation
- Document comparison and discrepancy flagging

**Supported Document Types**:
- PDF, Word, Excel, PowerPoint
- Financial statements (10-K, 10-Q, audits)
- Legal documents (contracts, cap tables)
- Commercial materials (customer lists, pricing)

### 3. Portfolio Management

**Features**:
- Automated KPI tracking and dashboards
- Covenant compliance monitoring
- Performance attribution (market vs operational)
- Value creation tracking vs plan
- Board report generation
- Anomaly detection and alerting

**Integration**:
- Native Snowflake connectivity
- Real-time data pipelines
- Governance and access controls

### 4. Advanced Analytics

**Techniques**:
- Monte Carlo simulation (risk analysis)
- Physics-Informed Neural Networks (PINN) for optimization
- Real options valuation (expansion, abandonment, timing)
- Offline trajectory optimization (from SciPhyRL)
- Distributional reinforcement learning for goal-based investing

**Use Cases**:
- AI infrastructure investments (data centers, power)
- High-uncertainty early-stage deals
- Staged capital deployment decisions
- Portfolio optimization under constraints

---

## Platform Comparison

| Feature | Cortex Code | OpenAI | Bedrock | Claude Code |
|---------|-------------|--------|---------|-------------|
| **Snowflake Data Access** | Native ✅ | Via API | Via Lambda | No |
| **Best For** | Portfolio analytics | General modeling | Production | Deep analysis |
| **Cost** | AI credits | Token-based | Enterprise | Subscription |
| **Governance** | Full ✅ | Limited | Full ✅ | Limited |
| **Multi-Agent** | Yes | Yes | Native ✅ | Manual |
| **Performance** | High | Medium | High | High |
| **Setup Time** | 5 min | 2 min | 30 min | 1 min |

---

## Model Recommendations

### By Platform

**Cortex Code (Snowflake)**:
- Complex reasoning: `claude-opus-4-6`
- General modeling: `openai-gpt-5.1`
- Fast extraction: `claude-sonnet-4-5`
- Bulk processing: `mistral-large-2-2`

**OpenAI**:
- Reasoning: `gpt-4-turbo`
- Modeling: `gpt-4`
- Extraction: `gpt-4-turbo`

**Bedrock**:
- Reasoning: `anthropic.claude-3-opus-20240229-v1:0`
- Modeling: `anthropic.claude-3-sonnet-20240229-v1:0`
- Extraction: `anthropic.claude-3-haiku-20240307-v1:0`

### By Task

- **IC Memos / Deep Analysis**: Claude Opus (best reasoning)
- **Code Generation**: GPT-4 or GPT-5.1 (strong at Python)
- **Document Extraction**: Claude Sonnet (fast, accurate)
- **Bulk Operations**: Mistral Large (cost-effective)

---

## Performance Benchmarks

### Python vs Rust (10,000 scenario DCF)

| Implementation | Time | Speedup |
|---------------|------|---------|
| Pure Python | 45s | 1x |
| Pandas/NumPy | 8s | 5.6x |
| **Rust** | **1.2s** | **37x** |
| **Rust + Wasm** | **1.3s** | **35x** |

### AI Model Performance (Complex DD Memo)

| Model | Time | Quality | Cost |
|-------|------|---------|------|
| Claude Opus 4-6 | 45s | Excellent | $$$ |
| GPT-4 Turbo | 30s | Very Good | $$ |
| Claude Sonnet 4-5 | 20s | Good | $ |
| Mistral Large | 15s | Good | $ |

---

## Real-World Use Cases

### 1. AI Infrastructure Investment Analysis

**Scenario**: Evaluating a data center investment in the AI boom (2025-2026)

**Workflow**:
1. Extract metrics from offering materials
2. Build DCF with high volatility assumptions
3. Apply real options framework for expansion/abandonment
4. Run Monte Carlo for uncertainty quantification
5. Generate IC memo with risk-adjusted returns

**Tools Used**: Claude Code (analysis) + Cortex (data) + Rust (Monte Carlo)

**Result**: Comprehensive investment memo in 2 hours vs 2 days manual

---

### 2. Portfolio Company Performance Monitoring

**Scenario**: Monthly reporting across 15 portfolio companies

**Workflow**:
1. Pull KPIs from Snowflake (automated)
2. Generate performance reports with Cortex AI
3. Flag covenant breaches and anomalies
4. Create board-ready dashboards
5. Email summaries to investment team

**Tools Used**: Cortex Code + Snowflake + Streamlit

**Result**: 90% time reduction, real-time insights

---

### 3. Rapid Due Diligence (5-Day Process)

**Scenario**: Competitive auction with tight timelines

**Workflow**:
1. Multi-agent team: Document extraction, financial modeling, commercial analysis
2. Parallel execution across workstreams
3. Continuous synthesis into draft IC memo
4. Human-in-the-loop for key decisions

**Tools Used**: Bedrock AgentCore (orchestration) + Claude (reasoning)

**Result**: Comprehensive DD in 3 days vs typical 2-3 weeks

---

## Security & Compliance

### Data Handling
- ✅ All financial calculations use Decimal (no floating-point errors)
- ✅ Full audit trails with lineage tracking
- ✅ No data fabrication (always cite sources)
- ✅ Sensitive data stays in your environment (Snowflake/Bedrock)

### Access Control
- Snowflake: Native role-based access control (RBAC)
- Bedrock: IAM policies for tool and model access
- OpenAI: API key management
- Claude Code: Local execution

### Compliance
- Suitable for regulated environments (with proper deployment)
- SOC 2 compatible (when using Snowflake/Bedrock)
- GDPR/CCPA compliant data handling patterns

---

## Advanced Topics

### Multi-Agent Orchestration

```python
from integrations.python.openai_compatible_client import create_pe_agent

# Create specialist agents
sourcing_agent = create_pe_agent("cortex", session, model="claude-sonnet-4-5")
modeling_agent = create_pe_agent("cortex", session, model="openai-gpt-5.1")
synthesis_agent = create_pe_agent("cortex", session, model="claude-opus-4-6")

# Orchestrate workflow
targets = sourcing_agent.analyze_deal(market_research)
models = modeling_agent.build_model("DCF", extract_inputs(targets))
ic_memo = synthesis_agent.generate_ic_memo("Deal X", {"targets": targets, "models": models})
```

### High-Performance Rust Integration

```bash
# Build Rust modules
cd integrations/rust
cargo build --release

# Use from Python
from pe_rust import calculate_dcf, run_monte_carlo

result = calculate_dcf(inputs)
# 30-100x faster than Python
```

### WebAssembly (Browser/Edge)

```javascript
// Run PE calculations in browser
import init, { calculate_dcf_wasm } from './pkg/pe_finance.js';

await init();
const result = calculate_dcf_wasm(inputs);
// Secure, sandboxed, portable
```

---

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues and solutions.

**Quick Fixes**:

1. **Cortex 400 Error**: Remove `logprobs` parameter
2. **Token Limit**: Check model-specific `max_completion_tokens`
3. **DNS Error**: Use `host` field from config, don't reconstruct
4. **Precision Issues**: Always use `Decimal` for financial math

---

## Contributing

This is a reference implementation. Contributions welcome:
- Additional models (e.g., merger model, sum-of-parts)
- Platform integrations (e.g., Azure OpenAI)
- Performance optimizations
- Real-world case studies

---

## Roadmap

- [ ] Streamlit dashboard for portfolio monitoring
- [ ] Carta integration for live cap table data
- [ ] Advanced PINN solvers for portfolio optimization
- [ ] dbt integration for data transformation
- [ ] Airflow DAGs for scheduled workflows
- [ ] LangGraph implementation for complex orchestration

---

## License

This is an educational reference implementation,
not investment advice. Historical claims below are not new validation results.

For production use:
- Validate all calculations independently
- Implement proper access controls
- Add comprehensive audit logging
- Maintain human oversight for material decisions

---

## Contact & Support

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder
- **Quickstart**: See [QUICKSTART.md](QUICKSTART.md)

---

## Acknowledgments

- **SciPhyRL**: Offline trajectory optimization techniques (arXiv:2607.15195)
- **Snowflake**: Cortex AI infrastructure
- **Anthropic**: Claude models
- **OpenAI**: GPT models
- **AWS**: Bedrock AgentCore

---

**Built for Private Equity professionals who want to leverage AI without compromising rigor.**

*Last Updated: 2026-07-20*
