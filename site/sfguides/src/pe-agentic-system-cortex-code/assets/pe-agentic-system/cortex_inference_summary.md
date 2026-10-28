# Cortex Inference Integration - Quick Summary

**Essential guide to using Snowflake Cortex AI in the PE Agentic System**

---

## 🎯 What is Cortex Inference?

Snowflake Cortex is Snowflake's native AI service that provides:
- Access to LLMs (Claude, GPT, Mistral, Llama) via REST API
- SQL-based AI functions
- Semantic search and vector embeddings
- Native integration with Snowflake data

**Key Advantage**: Your data never leaves Snowflake (governance, security, compliance)

---

## 🚀 Quick Start (3 Steps)

### 1. Authentication (Simplest Method)

```python
from snowflake.snowpark import Session
from integrations.cortex.cortex_client import CortexRESTClient

# Get session (in Snowflake Notebook)
session = Session.builder.getOrCreate()

# Create client (uses session token - NO keys needed!)
client = CortexRESTClient.from_session(session, model="claude-opus-4-6")
```

**Why this works**: Session token is already authenticated. No JWT, no PAT, no config files needed.

---

### 2. Simple Completion

```python
response = client.complete(
    messages=[
        {"role": "user", "content": "Analyze this CIM and extract key metrics..."}
    ],
    temperature=0.0,
    max_completion_tokens=4096
)

print(response["choices"][0]["message"]["content"])
```

---

### 3. Streaming (for long outputs)

```python
for chunk in client.complete_stream(
    messages=[{"role": "user", "content": "Generate IC memo..."}]
):
    print(chunk, end="", flush=True)
```

---

## ⚠️ Critical: Avoid Common Cortex Errors

### Error 1: "invalid request parameters" (400)

**Problem**: Cortex has a strict parameter allowlist

```python
# ❌ DON'T: Include logprobs
payload = {
    "model": "claude-opus-4-6",
    "messages": [...],
    "logprobs": False  # ← Causes 400 error!
}

# ✅ DO: Omit logprobs entirely
payload = {
    "model": "claude-opus-4-6",
    "messages": [...]
    # No logprobs parameter at all
}
```

**Solution**: Our `CortexRESTClient` automatically removes `logprobs` for you.

---

### Error 2: "max_completion_tokens exceeds limit"

**Problem**: Each model has different token limits

| Model | Max Output Tokens |
|-------|-------------------|
| claude-opus-4-6 | 16,384 |
| claude-sonnet-4-5 | 16,384 |
| openai-gpt-5.1 | 16,384 |
| openai-gpt-5.4 | 32,768 |
| mistral-large-2-2 | 32,768 |

```python
# ❌ DON'T: Request more than model supports
client.complete(messages=[...], max_completion_tokens=20000)  # Fails for Claude

# ✅ DO: Check model limits
client.complete(messages=[...], max_completion_tokens=16384)  # OK
```

**Solution**: Our client validates limits automatically.

---

### Error 3: DNS/Connection Errors

**Problem**: Account identifiers with underscores break DNS

```python
# ❌ DON'T: Reconstruct host from account
account = "<your account>"
host = f"{account}.snowflakecomputing.com"  # Invalid DNS label!

# ✅ DO: Use host field from config
host = connection_config['host']  # Pre-validated
```

**Solution**: Our client reads `host` directly from connection.

---

## 🎨 Model Selection by Task

### Financial Modeling (Code Generation)
```python
client = CortexRESTClient.from_session(session, model="openai-gpt-5.1")
# Best for: Python code generation, DCF models, formulas
```

### Deep Analysis (Complex Reasoning)
```python
client = CortexRESTClient.from_session(session, model="claude-opus-4-6")
# Best for: IC memos, due diligence synthesis, strategic analysis
```

### Fast Extraction (Cost-Effective)
```python
client = CortexRESTClient.from_session(session, model="claude-sonnet-4-5")
# Best for: CIM extraction, metric identification, quick Q&A
```

### Bulk Operations (High Volume)
```python
client = CortexRESTClient.from_session(session, model="mistral-large-2-2")
# Best for: Portfolio reports (100+ companies), batch processing
```

---

## 🔧 Complete Integration Example

### End-to-End: CIM Analysis → DCF → IC Memo

```python
from snowflake.snowpark import Session
from integrations.cortex.cortex_client import CortexRESTClient
import json

# 1. Setup
session = Session.builder.getOrCreate()

# 2. Extract metrics (fast model)
extractor = CortexRESTClient.from_session(session, "claude-sonnet-4-5")
cim_analysis = extractor.complete(
    messages=[{
        "role": "user",
        "content": f"Extract financial metrics from this CIM:\n\n{cim_text}"
    }],
    max_completion_tokens=2048
)

metrics = json.loads(cim_analysis["choices"][0]["message"]["content"])

# 3. Build model (code generation model)
modeler = CortexRESTClient.from_session(session, "openai-gpt-5.1")
dcf_code = modeler.complete(
    messages=[{
        "role": "user",
        "content": f"Generate DCF Python code with inputs: {json.dumps(metrics)}"
    }],
    max_completion_tokens=4096
)

# Execute the generated code
exec(dcf_code["choices"][0]["message"]["content"])

# 4. Synthesize IC memo (reasoning model)
synthesizer = CortexRESTClient.from_session(session, "claude-opus-4-6")
ic_memo = synthesizer.complete(
    messages=[{
        "role": "user",
        "content": f"""Generate IC memo for this deal:
        
Analysis: {cim_analysis}
Valuation: {dcf_result}
"""
    }],
    max_completion_tokens=8192
)

print(ic_memo["choices"][0]["message"]["content"])

# 5. Save to Snowflake
session.sql(f"""
    INSERT INTO deal_analyses (deal_name, analysis, valuation, memo)
    VALUES ('{deal_name}', '{cim_analysis}', '{dcf_result}', '{ic_memo}')
""").collect()
```

---

## 📊 Cortex vs Other Platforms

| Feature | Cortex (Snowflake) | OpenAI | Bedrock |
|---------|-------------------|---------|---------|
| **Data Access** | Native (no ETL) | API calls | Lambda connectors |
| **Auth** | Session token (simplest) | API key | IAM + JWT |
| **Governance** | Full RBAC, row-level | Limited | Full IAM |
| **Cost** | AI credits | Token-based | Enterprise pricing |
| **Best For** | Portfolio analytics | General modeling | Production scale |

---

## 💰 Cost Optimization

### Use the Right Model

```python
# Expensive (but best quality)
claude_opus = CortexRESTClient.from_session(session, "claude-opus-4-6")
# Use for: Final IC memos, complex synthesis

# Medium cost
gpt_5 = CortexRESTClient.from_session(session, "openai-gpt-5.1")
# Use for: Code generation, modeling

# Cost-effective
claude_sonnet = CortexRESTClient.from_session(session, "claude-sonnet-4-5")
# Use for: Extraction, quick analysis

# Cheapest
mistral = CortexRESTClient.from_session(session, "mistral-large-2-2")
# Use for: Bulk processing, simple tasks
```

### Batch Operations

```python
# ❌ DON'T: Loop with individual calls
for company in companies:
    analysis = client.complete(...)  # Expensive!

# ✅ DO: Batch in single call
all_companies = "\n\n".join([format_company(c) for c in companies])
batch_analysis = client.complete(
    messages=[{"role": "user", "content": f"Analyze all: {all_companies}"}]
)
```

---

## 🔐 Security Best Practices

### 1. Use Session Token (In-Snowflake)

```python
# ✅ PREFERRED: Automatic authentication
session = Session.builder.getOrCreate()
client = CortexRESTClient.from_session(session, model)
```

### 2. Row-Level Security

```sql
-- Restrict access to portfolio data by role
CREATE ROW ACCESS POLICY portfolio_access AS (user_role VARCHAR)
RETURNS BOOLEAN ->
  CASE
    WHEN CURRENT_ROLE() = 'PORTFOLIO_MANAGER' THEN TRUE
    WHEN CURRENT_ROLE() = '<your analyst role>' AND user_role = '<your analyst role>' THEN TRUE
    ELSE FALSE
  END;

ALTER TABLE portfolio_companies
  ADD ROW ACCESS POLICY portfolio_access ON (user_role);
```

### 3. Audit Logging

```sql
-- Query Cortex usage
SELECT 
    query_text,
    user_name,
    start_time,
    total_elapsed_time,
    credits_used_cloud_services
FROM snowflake.account_usage.query_history
WHERE query_text ILIKE '%cortex%'
  AND start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;
```

---

## 🚨 Troubleshooting Guide

### Problem: "Session not found"

**Solution**: Recreate session
```python
session = Session.builder.getOrCreate()
client = CortexRESTClient.from_session(session, model)
```

---

### Problem: "Request timeout"

**Solution**: Increase timeout or use streaming
```python
# Option 1: Increase timeout (for very long responses)
response = client.complete(messages=[...], timeout=300)

# Option 2: Use streaming (better)
for chunk in client.complete_stream(messages=[...]):
    print(chunk, end="")
```

---

### Problem: "Connection refused"

**Solution**: Check host and account
```python
# Verify connection
print(f"Host: {session.connection.host}")
print(f"Account: {session.connection.account}")

# Should NOT contain underscores in hostname
```

---

## 📈 Performance Tips

### 1. Parallel Queries for Portfolio Analysis

```python
from concurrent.futures import ThreadPoolExecutor

companies = session.table("portfolio_companies").to_pandas()

def analyze_company(company):
    client = CortexRESTClient.from_session(session, "claude-sonnet-4-5")
    return client.complete(...)

with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(analyze_company, companies))
```

### 2. Cache Results

```python
# Store AI analysis in Snowflake
CREATE TABLE ai_analyses (
    company_id STRING,
    analysis_type STRING,
    result VARIANT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Check cache before calling Cortex
SELECT result FROM ai_analyses
WHERE company_id = ?
  AND analysis_type = 'CIM_EXTRACTION'
  AND created_at >= DATEADD(day, -7, CURRENT_TIMESTAMP());
```

---

## 🎯 Quick Reference

### Three Authentication Methods (Priority Order)

1. **from_session()** - In Snowflake (Notebooks/SiS) - **PREFERRED**
2. **from_toml()** - External dev (not implemented - use JWT)
3. **from_key_file()** - Production/CI with JWT keypair

### Essential Parameters

```python
client.complete(
    messages=[...],              # Required
    temperature=0.0,             # 0.0 = deterministic, 1.0 = creative
    max_completion_tokens=4096,  # Check model limits!
    # DON'T include: logprobs, stop (unless needed)
)
```

### Model Recommendation Quick Lookup

- **Complex reasoning** → `claude-opus-4-6`
- **Code generation** → `openai-gpt-5.1`
- **Fast extraction** → `claude-sonnet-4-5`
- **Bulk/batch** → `mistral-large-2-2`

---

## 📚 Related Documentation

- **Full Integration**: See `integrations/cortex/cortex_client.py`
- **Unified Client**: See `integrations/python/openai_compatible_client.py`
- **Examples**: See `examples/complete_deal_workflow.ipynb`
- **Architecture**: See `docs/architecture.md`

---

## ✅ Summary Checklist

Before deploying to Cortex:

- ✅ Use `from_session()` for authentication (simplest)
- ✅ Never include `logprobs` parameter
- ✅ Validate `max_completion_tokens` against model limits
- ✅ Use appropriate model for task (cost optimization)
- ✅ Implement caching for repeated queries
- ✅ Add row-level security for sensitive data
- ✅ Monitor usage via `query_history`

---

**Key Takeaway**: Cortex integration is production-ready with proper error handling for all common issues. The `CortexRESTClient` handles the gotchas automatically.

---

*Part of the PE Agentic System | See AGENTS.md for full context*
