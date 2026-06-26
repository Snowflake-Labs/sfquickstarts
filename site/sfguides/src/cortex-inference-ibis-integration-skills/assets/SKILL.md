---
name: cortex-ibis
description: "**[REQUIRED]** Use for ALL tasks combining Snowflake Cortex AI functions with Ibis (Python dataframe library): AI_COMPLETE, AI_SENTIMENT, AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_SUMMARIZE_AGG, SNOWFLAKE.CORTEX.COMPLETE, SNOWFLAKE.CORTEX.EMBED_TEXT_768/1024, vector similarity search, semantic search, EnrichmentPipeline, direct Cortex REST API calls (PAT auth, JWT auth, streaming SSE, tool calling), cortex_ibis, cortex_rest."
---

# Cortex + Ibis Integration Skill

Routes all Cortex AI + Ibis dataframe tasks to the correct reference. Nothing executes until you read the relevant reference file.

---

## Routing

| User intent | Route |
|---|---|
| AI_* functions, SNOWFLAKE.CORTEX.*, Ibis UDFs, `.mutate()`, `.filter()` with Cortex | `references/cortex-ibis-api.md` |
| EnrichmentPipeline, fluent chain, `.classify().sentiment().embed()` | `references/enrichment-pipeline.md` |
| Embeddings, `EMBED_TEXT_768`, `EMBED_TEXT_1024`, `cache_embeddings` | `references/embeddings.md` |
| Semantic search, `semantic_search()`, cosine/L2/inner product | `references/semantic-search.md` |
| Direct REST API, `CortexInferenceClient`, PAT auth, JWT auth, streaming, tool calling | `references/cortex-inference.md` |
| TurboPuffer, hybrid search, ANN, BM25, namespace branching | `references/turbopuffer.md` |
| Shannon entropy, distribution analysis, category diversity, `category_entropy`, `normalized_entropy`, synthetic data | `references/distributions.md` |

**Always read the routed reference file before writing any code.**

---

## Quick Start

```python
# Ibis path (SQL-based, lazily evaluated)
import ibis
from cortex_ibis import EnrichmentPipeline, add_classification, semantic_search

con = ibis.snowflake.connect(
    user="you@example.com",
    account="myorg-myaccount",
    database="MY_DB/MY_SCHEMA",
    warehouse="COMPUTE_WH",
    authenticator="externalbrowser",
)

# REST path (direct HTTP, streaming capable)
from cortex_rest import CortexInferenceClient   # PAT auto-loaded from ~/.snowflake/config.toml
client = CortexInferenceClient()
```

---

## Key Principles

1. **Ibis is lazy** — nothing runs until `.execute()` or `.cache()`. All Cortex calls compile to a single SQL query.
2. **REST is eager** — `CortexInferenceClient.complete()` fires an HTTP request immediately.
3. **Embeddings live in Snowflake** — `EMBED_TEXT_768/1024` runs server-side; no Python-side vector API call needed.
4. **PAT prefix for LiteLLM** — when wiring through LiteLLM proxy, the api_key must start with `pat/`. For direct REST, use the raw token.
5. **Sampling params** — `temperature`, `top_p`, `top_k` were removed for `claude-opus-4-7+`. Strip them before sending (see `references/cortex-inference.md`).

---

## Workspace Files

| File | Purpose |
|---|---|
| `cortex_ibis.py` | Ibis UDFs for all Cortex AI + embedding + vector functions |
| `cortex_rest.py` | Direct REST client — PAT + JWT auth, streaming SSE, tool calling |
| `demo.py` | End-to-end Ibis enrichment walkthrough |
| `turbopuffer_demo.py` | Cortex + Ibis + TurboPuffer vector index pipeline |
| `test_cortex_rest.py` | 7-section REST validation suite with SVG screenshot capture |
