# Private Equity Agentic System - Architecture

**Version**: 1.0.0  
**Last Updated**: 2026-09-09

> **Read `../CLAIMS.md` first.** Parts of this document describe intended design
> rather than shipped code — notably the multi-agent chain (no agent loop exists),
> semantic views, and the performance figures (withdrawn; see
> `../integrations/rust/benchmarks/README.md`).

---

## The Architectural Pattern

Everything below is in service of one pattern. If you take away a single diagram,
take this one:

```
  probabilistic          structured           validated
   reasoning       ──▶     contract      ──▶   boundary
  (LLM proposes)         (typed schema)      (policy checks)
                                                   │
                                                   ▼
   evidence-backed   ◀──   deterministic   ◀──  only validated
      output               computation           inputs pass
  (with provenance)      (Rust/Python)
```

The load-bearing idea is the **boundary**, not the speed of what sits behind it.
An LLM may *propose* financial assumptions; it may never hand them directly to a
valuation engine. Implemented in `assurance/contracts.py`; demonstrated in
`examples/assurance_boundary_demo.py`.

## Planes, not layers

The earlier four-item list ("AI / Rust / Snowflake / Python") conflated
responsibilities that must stay distinct. In particular it described Snowflake
Cortex as "the data layer," which undersells governance and misplaces inference.
The correct decomposition separates **what governs data** from **what performs
inference**:

| Plane | Responsibility | Implementation |
|---|---|---|
| **Governed data plane** | Single source of truth, RBAC, masking, policy, lineage, audit trail | Snowflake. Not Cortex — Cortex is a capability *within* Snowflake, not a synonym for it. |
| **Reasoning plane** | Document understanding, synthesis, drafting | Cortex `AI_COMPLETE` by default, behind a provider-neutral gateway (`config/models.yaml`) that can route to other approved providers |
| **Assurance plane** | Typed contract, range and policy validation, provenance, sign-off routing | `assurance/contracts.py` |
| **Deterministic compute plane** | DCF, LBO, waterfalls, Monte Carlo — with declared numerical guarantees | Rust kernels (UDF, container, or WASM); Python for orchestration and experimentation |
| **Evidence plane** | Provenance, input hashing, reproducibility, query history | Snowpark write-back + `ACCOUNT_USAGE` |

Two consequences worth stating explicitly, because both were previously blurred:

**Governance is not inference.** Access control, masking, lineage, and audit are
properties of the data plane and apply whether or not a model is involved. Folding
them into "the AI layer" makes the governance story invisible — and in private
markets, where there is no market price to check a valuation against, governance
*is* the differentiator.

**Model routing is a policy decision, not a cost decision.** `config/models.yaml`
already implements task → tier → platform → model, which is the right shape.
Routing should key on task type, risk, latency, data classification, required
tools, context needs, and assurance requirements — not cost alone. Describe tiers
by capability (frontier reasoning, balanced, low-cost extraction) and treat
concrete model IDs as swappable examples; several entries in the current catalog
are already flagged `available: false`, which makes the point.

## Numerical boundaries

State these explicitly rather than banning floats outright:

| Domain | Representation | Why |
|---|---|---|
| Money, accounting, anything that must reconcile to a spreadsheet in an audit | `Decimal` / `rust_decimal` | Exact base-10; no representation error on cents |
| Monte Carlo, statistics, numerical optimization | `f64` | Sampling error dominates representation error by orders of magnitude; decimal here costs speed and buys nothing |

Current code does not fully honour this: PyO3 entry points accept `f64` and
convert via `Decimal::from_f64_retain` (`lib.rs:32`, `dcf.rs:58`), so precision is
lost at the boundary before the decimal engine ever runs. See `CLAIMS.md` §2.6.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PE Agentic System                             │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Domain Skills│  │ Integrations │  │   Examples   │          │
│  │              │  │              │  │              │          │
│  │ • Modeling   │  │ • Cortex     │  │ • Workflows  │          │
│  │ • DD         │  │ • OpenAI     │  │ • Notebooks  │          │
│  │ • Portfolio  │  │ • Bedrock    │  │ • Scripts    │          │
│  │ • Advanced   │  │ • Rust/Wasm  │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│                      Core Platform                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         AGENTS.md (Persistent Instructions)             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ├──────────────────────────────┐
                             │                              │
                             ▼                              ▼
         ┌─────────────────────────────┐    ┌──────────────────────────┐
         │    Platform Runtimes         │    │    Data & Compute        │
         │                              │    │                          │
         │  • Claude Code               │    │  • Snowflake             │
         │  • Cortex Code               │    │  • S3/Data Lakes         │
         │  • OpenAI API                │    │  • Rust Native           │
         │  • Bedrock AgentCore         │    │  • WebAssembly           │
         └─────────────────────────────┘    └──────────────────────────┘
```

---

## Component Architecture

### 1. Core Layer

**AGENTS.md**
- Persistent instructions loaded by all agents
- PE domain knowledge base
- Best practices and principles
- Output standards and guidelines

**Skills/**
- Modular domain expertise
- Financial modeling (DCF, LBO, comps)
- Due diligence automation
- Portfolio monitoring
- Advanced analytics (PINNs, real options)

### 2. Integration Layer

**Cortex Client** (`integrations/cortex/`)
- Session token auth (preferred for Notebooks/SiS)
- TOML config support (external development)
- JWT keypair (production/CI)
- Proper error handling for Cortex-specific issues

**OpenAI-Compatible Client** (`integrations/python/`)
- Unified interface across OpenAI, Bedrock, Cortex
- Model recommendations by task
- High-level PE methods (analyze_deal, build_model, etc.)
- Streaming support

**Rust/WebAssembly** (`integrations/rust/`)
- High-performance financial calculations
- Portable across platforms
- 30-100x speedup for heavy computation
- PyO3 bindings for Python integration

### 3. Application Layer

**Examples/**
- Complete end-to-end workflows
- Jupyter notebooks for interactive use
- Production deployment patterns
- Multi-agent orchestration examples

---

## Data Flow

### Typical Workflow: Deal Analysis

```
1. Document Ingestion
   ├─ CIM PDF uploaded
   └─ Extract text/tables → Raw data

2. Analysis (Multi-Agent)
   ├─ Research Agent (Claude Sonnet)
   │  └─ Extract metrics, thesis, risks
   │
   ├─ Modeling Agent (GPT-5.1)
   │  └─ Build DCF, LBO, sensitivity
   │
   └─ Portfolio Agent (Cortex + Snowflake)
      └─ Pull comparable deals

3. Synthesis (Claude Opus)
   ├─ Combine all analyses
   ├─ Generate IC memo
   └─ Flag key risks/opportunities

4. Storage & Audit
   ├─ Save to Snowflake
   └─ Full lineage tracking
```

---

## Platform-Specific Architectures

### Cortex Code (Snowflake)

```
Snowflake Environment
├─ Notebooks (Streamlit in Snowflake)
│  ├─ Import pe_agent modules
│  ├─ Session-based auth (no keys needed)
│  └─ Direct SQL/DataFrame access
│
├─ Data Layer
│  ├─ Portfolio tables
│  ├─ Historical deal data
│  └─ Market data feeds
│
└─ Cortex AI
   ├─ REST API (via session token)
   ├─ Model selection by task
   └─ Semantic views for discovery
```

**Advantages**:
- Native data access (no ETL)
- Governed and secure
- Built-in lineage tracking
- Cost-effective for data-heavy work

**Best For**: Portfolio analytics, data-driven DD

---

### OpenAI

```
External Environment (Local/Cloud)
├─ Python Scripts/Notebooks
│  ├─ OpenAI SDK
│  ├─ PE Agent wrapper
│  └─ API key auth
│
├─ Data Sources
│  ├─ Files (PDF, Excel)
│  ├─ APIs (external)
│  └─ Optional: Snowflake connector
│
└─ OpenAI API
   ├─ GPT-4 Turbo (reasoning)
   ├─ GPT-4 (general)
   └─ Structured outputs
```

**Advantages**:
- Quick setup
- Strong code generation
- Structured output support
- Wide ecosystem

**Best For**: General modeling, prototyping

---

### Bedrock AgentCore

```
AWS Environment
├─ Agent Definition
│  ├─ Action groups (tools)
│  ├─ Knowledge bases
│  └─ IAM policies
│
├─ Lambda Functions
│  ├─ Rust modules (compiled)
│  ├─ Python integrations
│  └─ Snowflake connectors
│
├─ Step Functions
│  ├─ Multi-agent orchestration
│  ├─ Human-in-the-loop approvals
│  └─ Error handling
│
└─ Claude Models (via Bedrock)
   ├─ Claude 3 Opus
   ├─ Claude 3 Sonnet
   └─ Claude 3 Haiku
```

**Advantages**:
- Production-grade orchestration
- Enterprise security (IAM)
- Scalable and managed
- Full audit logging

**Best For**: Production deployment, multi-agent systems

---

### Claude Code

```
Local Interactive Environment
├─ Terminal/CLI
│  ├─ @AGENTS.md auto-loaded
│  ├─ Reference skill files
│  └─ Full context window
│
├─ File System Access
│  ├─ Read deal materials
│  ├─ Execute Python code
│  └─ Write outputs
│
└─ Claude Models (Native)
   ├─ Deep reasoning
   ├─ Document analysis
   └─ Code generation
```

**Advantages**:
- Superior reasoning depth
- Full document context
- Interactive iteration
- Local development

**Best For**: Complex analysis, research, prototyping

---

## Performance Characteristics

### Latency by Task

| Task | Python | Rust | Speedup |
|------|--------|------|---------|
| 1,000 scenario DCF | 4.5s | 0.12s | 37x |
| Monte Carlo (10k) | 45s | 1.2s | 37x |
| LBO waterfall | 2.1s | 0.08s | 26x |
| Portfolio MOIC calc | 8.0s | 0.3s | 27x |

### AI Model Performance

| Model | Tokens/sec | Quality | Cost/1M tokens |
|-------|-----------|---------|----------------|
| Claude Opus 4-6 | ~50 | Excellent | $15 |
| GPT-4 Turbo | ~80 | Very Good | $10 |
| Claude Sonnet 4-5 | ~100 | Good | $3 |
| Mistral Large | ~120 | Good | $2 |

### Throughput (Portfolio Monitoring)

- **Python-only**: ~10 companies/min
- **Cortex + Python**: ~50 companies/min
- **Rust + Cortex**: ~200 companies/min

---

## Security Architecture

### Authentication Flow

```
┌──────────────┐
│   User       │
└──────┬───────┘
       │
       ├─── Snowflake Session Token ───► Cortex API
       │    (In-Snowflake workloads)
       │
       ├─── OpenAI API Key ───────────► OpenAI
       │    (External workloads)
       │
       └─── AWS IAM + JWT ────────────► Bedrock
            (Production deployment)
```

### Data Access Controls

**Snowflake**:
- Role-based access control (RBAC)
- Row-level security (RLS) on portfolio data
- Masking for sensitive fields (e.g., SSN, financial details)
- Audit logging (QUERY_HISTORY)

**Bedrock**:
- IAM policies per agent
- Resource-based policies for tools
- CloudTrail for all actions
- Secrets Manager for credentials

**OpenAI**:
- API key rotation
- Usage monitoring
- No data retention (zero data retention mode)

---

## Deployment Patterns

### Pattern 1: Snowflake-Native (Recommended for Portfolio Work)

```yaml
Environment: Snowflake Notebooks
Auth: Session token (automatic)
Data: Native Snowflake tables
Models: Cortex AI (claude-opus-4-6, openai-gpt-5.1)
Compute: Warehouse (<your warehouse>)
Cost: Snowflake AI credits + compute

Deployment Steps:
1. Upload pe-agentic-system/ to Snowflake stage
2. Create Notebook with sys.path.append(stage_path)
3. Import create_pe_agent
4. Run workflows interactively or scheduled
```

---

### Pattern 2: OpenAI + Local/Cloud Python

```yaml
Environment: Jupyter / Python scripts
Auth: OPENAI_API_KEY env var
Data: Files (PDF, Excel) + optional Snowflake connector
Models: OpenAI (gpt-4-turbo, gpt-4)
Compute: Local CPU/GPU or cloud VM
Cost: OpenAI token-based

Deployment Steps:
1. pip install -r requirements.txt
2. Set OPENAI_API_KEY
3. Run scripts or notebooks
4. Optionally: Deploy to EC2/Lambda for scheduled runs
```

---

### Pattern 3: Bedrock Production (Enterprise)

```yaml
Environment: AWS Lambda + Step Functions
Auth: IAM roles + JWT for Snowflake
Data: S3 + Snowflake (via connector)
Models: Bedrock (Claude 3)
Compute: Lambda (Python/Rust)
Cost: Bedrock + Lambda invocations

Deployment Steps:
1. Package Rust modules as Lambda layers
2. Define Agent in Bedrock console
3. Create action groups (tools) pointing to Lambdas
4. Build Step Functions state machine for workflows
5. Configure IAM policies (least privilege)
6. Enable CloudTrail logging
```

---

### Pattern 4: Hybrid (Best of All)

```yaml
Research & Prototyping: Claude Code (deep analysis)
Modeling: Python + Rust (high performance)
Data Operations: Cortex Code (Snowflake-native)
Production: Bedrock (orchestration)

Workflow:
1. Research in Claude Code → draft analysis
2. Build models in Jupyter + Rust modules
3. Run at scale in Cortex + Snowflake
4. Deploy to Bedrock for production automation
```

---

## Scaling Considerations

### Small Fund (<$500M AUM)
- Start with OpenAI or Cortex Code
- 1-2 portfolio companies analyzed at a time
- Monthly reporting manually triggered
- Cost: <$500/month

### Mid-size Fund ($500M - $2B AUM)
- Use Cortex Code + Snowflake for portfolio
- Bedrock for complex multi-agent DD
- Automated monthly reporting
- 10-15 active deals per year
- Cost: $2k-5k/month

### Large Fund (>$2B AUM)
- Full Bedrock AgentCore deployment
- Rust/Wasm for high-performance modules
- Automated sourcing, monitoring, reporting
- 30+ active deals per year
- Cost: $10k-20k/month (still cheaper than 1 analyst)

---

## Monitoring & Observability

### Key Metrics

```yaml
Agent Performance:
  - Latency (p50, p95, p99)
  - Token usage per request
  - Error rate
  - Model selection distribution

Financial Accuracy:
  - DCF validation errors
  - Sensitivity coverage
  - Human correction rate

Business Impact:
  - Time saved vs manual
  - Deals analyzed per month
  - IC memos generated
  - Portfolio reports automated
```

### Logging

**Snowflake**:
```sql
SELECT * FROM QUERY_HISTORY 
WHERE QUERY_TEXT LIKE '%cortex%'
ORDER BY START_TIME DESC;
```

**Bedrock**:
```python
# CloudTrail events
event_name = "InvokeAgent"
```

**OpenAI**:
```python
# Custom application logging
logger.info(f"Request: {prompt[:100]}...")
logger.info(f"Tokens: {response.usage.total_tokens}")
```

---

## Disaster Recovery

### Backup Strategy

1. **Code**: Git repository (version controlled)
2. **Data**: Snowflake Time Travel (90 days)
3. **Models**: Model outputs stored in Snowflake tables
4. **Audit Trail**: Immutable logs in CloudTrail / Snowflake

### Recovery Procedures

**Scenario 1: Bad model output**
- Use Time Travel to revert data
- Review lineage to identify issue
- Rollback to previous working state

**Scenario 2: Platform outage**
- Cortex → OpenAI (change one line)
- OpenAI → Bedrock (change one line)
- Hybrid approach always available

**Scenario 3: Data corruption**
- Restore from Snowflake snapshot
- Re-run analyses (idempotent)
- Validate against historical results

---

## Future Enhancements

### Q3 2026
- [ ] Streamlit dashboard for portfolio monitoring
- [ ] Carta integration for live cap table data
- [ ] Advanced PINN solvers

### Q4 2026
- [ ] dbt integration for data transformation
- [ ] Airflow DAGs for scheduled workflows
- [ ] LangGraph implementation

### 2027
- [ ] Real-time market data integration
- [ ] Predictive analytics for portfolio exits
- [ ] Automated LP reporting

---

## References

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Bedrock AgentCore Guide](https://docs.aws.amazon.com/bedrock/)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [SciPhyRL Paper](https://arxiv.org/abs/2607.15195)

---

*This architecture supports institutional-grade PE operations while remaining flexible and portable across platforms.*
