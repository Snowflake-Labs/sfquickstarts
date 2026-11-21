# Private Equity Agentic System - Quickstart Guide

**Version**: 1.0.0  
**Last Updated**: 2026-07-20  
**Platforms**: Claude Code, Cortex Code (Snowflake), Bedrock AgentCore, OpenAI

---

## Overview

This system provides production-ready AI agents for the full Private Equity lifecycle:

- **Sourcing & Screening**: Target identification and preliminary analysis
- **Due Diligence**: Document analysis, financial spreading, red flag detection
- **Financial Modeling**: DCF, LBO, comps, cap tables, waterfalls
- **Portfolio Management**: KPI tracking, covenant monitoring, performance reporting
- **Advanced Analytics**: Real options, Monte Carlo, PINN-based optimization

**Key Features**:
- ✅ Portable across Claude Code, Cortex, Bedrock, OpenAI
- ✅ Institutional-grade financial rigor
- ✅ High-performance Rust/WebAssembly modules for heavy computation
- ✅ Snowflake-native data integration
- ✅ Multi-agent orchestration patterns
- ✅ Full audit trails and explainability

---

## Quick Setup (5 Minutes)

### Option 1: Cortex Code (Snowflake) - Recommended for Data-Heavy Workflows

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

### Option 2: OpenAI - Best for General Use

```python
from integrations.python.openai_compatible_client import create_pe_agent
import os

# Set API key
os.environ["OPENAI_API_KEY"] = "sk-..."

# Create agent
agent = create_pe_agent("openai", model="gpt-4-turbo")

# Generate IC memo
memo = agent.generate_ic_memo(
    deal_name="Acme Corp Acquisition",
    analysis={
        "thesis": "Leading SaaS platform in vertical X",
        "valuation": {"enterprise_value": 250_000_000, "multiple": 12.5},
        "risks": ["Customer concentration", "Market maturity"]
    }
)
print(memo)
```

### Option 3: Bedrock AgentCore - Best for Production/Enterprise

```python
from integrations.python.openai_compatible_client import create_pe_agent

# Create agent (uses AWS credentials from environment)
agent = create_pe_agent("bedrock", region="us-east-1")

# Portfolio report
report = agent.portfolio_report({
    "company": "Portfolio Co A",
    "kpis": {
        "revenue": 45_000_000,
        "revenue_target": 50_000_000,
        "ebitda_margin": 0.22,
        "ebitda_margin_target": 0.25
    },
    "status": "Yellow"
})
print(report)
```

### Option 4: Claude Code - Best for Deep Analysis & Prototyping

```bash
# In Claude Code terminal
cd pe-agentic-system

# Reference the AGENTS.md file
# Claude automatically loads instructions
```

Then in conversation:
```
@AGENTS.md @financial-modeling-skill.md

Build a DCF model for a SaaS company with:
- Current revenue: $50M
- Growth rate: 25%  
- EBITDA margin: 30%
- WACC: 12%
```

---

## Common Workflows

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

---

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

---

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

---

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

## Platform-Specific Tips

### Cortex Code (Snowflake)

**Best For**: Data-heavy workflows, portfolio analytics, SQL-driven analysis

**Pro Tips**:
- Always search for semantic views before writing SQL: `cortex semantic-views search "portfolio performance"`
- Use `cortex search table-details` to understand schemas
- Store model outputs back in Snowflake tables for audit trail
- Leverage Snowflake's governance for sensitive financial data

**Common Pattern**:
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

### OpenAI

**Best For**: General-purpose modeling, rapid prototyping, external integrations

**Pro Tips**:
- Use `gpt-4-turbo` for complex reasoning
- Enable structured outputs for parsing model results
- Set temperature=0.0 for deterministic financial outputs

**Common Pattern**:
```python
from openai import OpenAI
client = OpenAI()

# Structured output (JSON mode)
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": "Extract financial metrics from this CIM..."}],
    response_format={"type": "json_object"}
)
metrics = json.loads(response.choices[0].message.content)
```

---

### Bedrock AgentCore

**Best For**: Production deployment, enterprise security, multi-agent orchestration

**Pro Tips**:
- Register high-performance tools (Rust/Wasm modules) as Lambda functions
- Use Step Functions for complex multi-agent workflows
- Implement full audit logging with CloudTrail
- Use IAM for granular access control

**Common Pattern**:
```python
import boto3

bedrock = boto3.client('bedrock-agent-runtime')

# Invoke agent with action groups
response = bedrock.invoke_agent(
    agentId='AGENT123',
    agentAliasId='ALIAS456',
    sessionId='session-789',
    inputText='Analyze this deal and build a DCF model'
)

# Stream results
for event in response['completion']:
    print(event['chunk']['bytes'].decode())
```

---

### Claude Code

**Best For**: Deep document reasoning, iterative analysis, research

**Pro Tips**:
- Use `@` to reference skill files: `@financial-modeling-skill.md`
- Leverage full context window for comprehensive CIMs
- Great for exploratory workflows and generating insights

**Common Pattern**:
```
@AGENTS.md @due-diligence-skill.md

Analyze the attached CIM for Acme Corp:
1. Extract all financial metrics
2. Identify 5 key risks
3. Generate 10 management questions
4. Provide preliminary valuation range using comps

[Attach CIM PDF]
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

## Next Steps

1. **Explore Skills**: Check `skills/` directory for detailed domain guides
2. **Review Examples**: See `examples/` for complete workflows
3. **Read Docs**: `docs/` contains architecture and integration details
4. **Customize**: Adapt prompts and models for your firm's specific needs

---

## Getting Help

- **Documentation**: See `docs/` folder
- **Examples**: See `examples/` folder  
- **Skills**: See `skills/` folder
- **Integration Guides**: See `integrations/` folder

---

## License & Disclaimer

This is a reference implementation. Always validate financial outputs independently. Not investment advice.

For production use:
- Implement proper access controls
- Add comprehensive audit logging
- Validate all calculations
- Maintain human oversight for material decisions

---

**Ready to start?** Pick your platform above and run the 5-minute setup!
