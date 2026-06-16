author: Priya Joseph
id: cortex-inference-ibis-integration-skills
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
summary: Call Snowflake Cortex inference REST API directly from Python using PAT or JWT auth, with streaming, tool calling, and error handling.
language: en


# Snowflake Cortex Inference REST API — Python Quickstart

A practical guide to calling the **Snowflake Cortex REST inference endpoint** directly from Python, covering PAT and JWT authentication, streaming SSE, tool calling, and error handling.

All examples use the `cortex_rest.py` client included in this workspace.

---

## Architecture

```
Python client (httpx)
  ├── Auth: PAT  → Authorization: Bearer <token>
  │               X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN
  └── Auth: JWT  → Authorization: Bearer <signed_jwt>
                   X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT
       ↓
POST https://<account>.snowflakecomputing.com/api/v2/cortex/inference:complete
       ↓
  Snowflake Cortex (claude-4-sonnet, llama3.3-70b, mistral-large2, ...)
```

---

## Prerequisites

```bash
pip install httpx PyJWT cryptography rich
```

- Snowflake account with Cortex enabled.
- PAT (Programmatic Access Token) in `~/.snowflake/config.toml`, or an RSA key pair registered on your user.

All runnable code lives under `assets/`. Run scripts from that directory:

```bash
cd assets
python distribution_demo.py
python test_cortex_rest.py
```

---

## Section 0 — Auth Check

Verifies that the PAT loads correctly from `~/.snowflake/config.toml` and shows the endpoint that will be called.

```python
from cortex_rest import _load_pat

host, token = _load_pat()           # reads connections.myaccount.password
print(host)                          # e.g. myorg-myaccount.snowflakecomputing.com
print(token[:8] + "...")             # eyJraWQi...
```

---

## Section 1 — Simple Single-Turn Complete

Non-streaming completion with token usage stats.

```python
from cortex_rest import CortexInferenceClient

client = CortexInferenceClient()     # auto PAT from config.toml
resp = client.complete(
    "claude-4-sonnet",
    [{"role": "user", "content": "In one sentence: what is Snowflake Cortex?"}],
    max_tokens=150,
)
print(resp["choices"][0]["message"]["content"])
print(resp["usage"])   # {'prompt_tokens': 21, 'completion_tokens': 51, 'total_tokens': 72}
```

**Screenshot:**

![Simple complete](assets/s1_simple_complete.svg)

---

## Section 2 — Multi-Turn Conversation

Pass the full conversation history; Cortex maintains context.

```python
messages = [
    {"role": "user",      "content": "My name is Ada. What's 12 × 12?"},
    {"role": "assistant", "content": "12 × 12 = 144."},
    {"role": "user",      "content": "What's my name and what was the answer?"},
]
resp = client.complete("claude-4-sonnet", messages, max_tokens=120)
# → "Your name is Ada, and the answer to 12 × 12 was 144."
```

**Screenshot:**

![Multi-turn](assets/s2_multi_turn.svg)

---

## Section 3 — Streaming SSE Response

The endpoint returns [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events). `complete_stream()` parses the `data:` lines and yields token chunks incrementally.

```python
for chunk in client.complete_stream(
    "claude-4-sonnet",
    [{"role": "user", "content": "Count slowly from 1 to 5, one number per line."}],
    max_tokens=80,
):
    delta = chunk["choices"][0]["delta"]
    text  = delta.get("content") or delta.get("text", "")
    print(text, end="", flush=True)

# Raw SSE shape:
# data: {"id":"...", "model":"claude-4-sonnet",
#        "choices":[{"delta":{"type":"text","content":"1\n","text":"1\n"}}], "usage":{}}
# data: {"id":"...", ..., "usage":{"prompt_tokens":15,"completion_tokens":20,"total_tokens":35}}
```

**Screenshot:**

![Streaming](assets/s3_streaming.svg)

---

## Section 4 — Tool Calling (Function Calling)

Snowflake uses `tool_spec` format. Here the model is asked to draft a customer-service reply to a defective-product review — but first it must call `get_product_details(product_id)` to look up the product's metadata. This mirrors the `product_id` field in the `cortex_ibis` reviews dataset (P001–P005).

```python
tools = [{
    "tool_spec": {
        "type": "generic",
        "name": "get_product_details",
        "description": "Look up product metadata (name, category, price) by product_id from the product catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product identifier, e.g. P001, P002."},
            },
            "required": ["product_id"],
        },
    }
}]

# Review from the turbopuffer_demo dataset — product P003, defective unit
messages = [{
    "role": "user",
    "content": (
        "A customer left this review for product P003: "
        "'Defective unit out of the box. USB port doesn't work at all.' "
        "Before drafting a response, look up the product details for P003."
    ),
}]

resp = client.complete("claude-4-sonnet", messages, tools=tools, max_tokens=250)

# Model responds with a tool_use call:
# [{"type": "tool_use", "tool_use": {"name": "get_product_details", "input": {"product_id": "P003"}}}]
```

**Screenshot:**

![Tool calling](assets/s4_tool_calling.svg)

---

## Section 5 — Temperature & Sampling Parameters

`claude-4-sonnet` accepts `temperature`, `top_p`, `top_k`. **Note:** these parameters were removed for `claude-opus-4-7` and newer (any non-default value returns 400).

```python
# Works for claude-4-sonnet:
resp = client.complete(
    "claude-4-sonnet",
    [{"role": "user", "content": "ping"}],
    max_tokens=20,
    temperature=0.7,
)

# For Opus 4.7 — strip the param before sending:
#   payload.pop("temperature", None)   # in pre_call_hook.py
```

**Screenshot:**

![Temperature](assets/s5_temperature.svg)

---

## Section 6 — Error Handling

A bad model name returns `HTTP 400` with a JSON error body. `httpx` raises `HTTPStatusError`; catch it to extract the message.

```python
import httpx
from cortex_rest import CortexInferenceClient

client = CortexInferenceClient()
try:
    client.complete("this-model-does-not-exist", [{"role":"user","content":"ping"}])
except httpx.HTTPStatusError as exc:
    print(exc.response.status_code)    # 400
    print(exc.response.json())         # {"message": "unknown model \"this-model-does-not-exist\"", ...}
```

**Screenshot:**

![Error handling](assets/s6_error_handling.svg)

---

## JWT Key-Pair Auth

To use key-pair JWT instead of a PAT (e.g. in CI or service accounts):

```python
# 1. Generate RSA key pair (once)
#    openssl genrsa -out snowflake_rsa_key.p8 2048
#    openssl rsa -in snowflake_rsa_key.p8 -pubout -out snowflake_rsa_key.pub
#
# 2. Register the public key on your Snowflake user:
#    ALTER USER <user> SET RSA_PUBLIC_KEY='<contents of .pub>';
#
# 3. Use JWT auth:
client = CortexInferenceClient(
    auth="jwt",
    account="myorg-myaccount",
    user="you@example.com",
    private_key_path="~/.ssh/snowflake_rsa_key.p8",
)
resp = client.complete("claude-4-sonnet", [{"role": "user", "content": "ping"}])
```

The `_build_jwt()` function in `cortex_rest.py` signs a short-lived JWT (default 60 min) using PyJWT + RSA, computing the public key fingerprint as `SHA256:<base64>`.

---

## Module-Level Convenience Functions

For quick scripts that don't need the full client:

```python
from cortex_rest import complete, stream

# One-shot
print(complete("What is 2+2?"))

# Streaming (yields text chunks)
for chunk in stream("Explain vector search in two sentences."):
    print(chunk, end="", flush=True)
```

---

## Distribution Analysis — Shannon Entropy

Shannon entropy measures how diverse a product's review categories are. A product with all defect reviews has low entropy (focused root cause). A product with mixed billing/delivery/defect/positive reviews has high entropy (needs broad support coverage).



**Synthetic dataset entropy profiles:**

| Product | Profile | H (bits) | Norm H |
|---|---|---|---|
| P004 | All positive | 0.00 | 0.00 |
| P002 | 90% product defect | 0.45 | 0.23 |
| P007 | 90% billing | 0.80 | 0.40 |
| P005 | Bimodal delivery+defect | 0.97 | 0.49 |
| P008 | Trimodal billing/delivery/defect | 1.16 | 0.58 |
| P003 | Bimodal billing+delivery | 1.82 | 0.91 |
| P001 | Uniform (all 4 categories) | 1.84 | 0.92 |
| P006 | Slight positive skew | 1.88 | 0.94 |

**Screenshot:**

![Shannon entropy distribution analysis](assets/s_entropy.svg)

---

## File Layout

```
cortex-inference-ibis-integration-skills/
├── cortex-inference-ibis-integration-skills.md   ← this guide
├── cortex-ibis-api.md        ← AI_*, SNOWFLAKE.CORTEX.*, VARIANT helpers
├── enrichment-pipeline.md    ← EnrichmentPipeline fluent chain
├── embeddings.md             ← EMBED_TEXT_768/1024, cache_embeddings
├── semantic-search.md        ← semantic_search(), cosine/L2/inner product
├── cortex-inference.md        ← CortexInferenceClient, PAT/JWT, streaming, tools
├── turbopuffer.md            ← ANN, hybrid BM25+ANN, filtered, aggregations
├── distributions.md          ← category_entropy, normalized_entropy, synthetic data
└── assets/
    ├── SKILL.md                  ← Cortex Code skill entry point (routing table)
    ├── cortex_ibis.py            ← Ibis UDFs for all Cortex AI functions (SQL path)
    ├── cortex_rest.py            ← Direct REST client — PAT/JWT, streaming, tool calling
    ├── demo.py                   ← End-to-end Ibis enrichment walkthrough
    ├── distribution_demo.py      ← Shannon entropy & category distribution analysis
    ├── synthetic_data.py         ← 300-row synthetic review dataset (8 products, Dirichlet)
    ├── turbopuffer_demo.py       ← Cortex + Ibis + TurboPuffer pipeline
    ├── test_cortex_rest.py       ← 7-section validation suite + SVG screenshot capture
    ├── __init__.py
    ├── requirements.txt
    ├── s1_simple_complete.svg
    ├── s2_multi_turn.svg
    ├── s3_streaming.svg
    ├── s4_tool_calling.svg
    ├── s5_temperature.svg
    ├── s6_error_handling.svg
    └── s_entropy.svg             ← Shannon entropy bar chart output
```

---

## Cortex Code Skill

The `assets/SKILL.md` + the reference `.md` files in the root directory also ship as a **Cortex Code (CoCo) skill** — install it once and any CoCo session will auto-invoke it for Cortex + Ibis questions.

```bash
# Install the skill into Cortex Code
cortex skill add /path/to/assets

# Verify
cortex skill list | grep cortex-ibis
```

The skill routes to the right reference file based on intent:

| Ask about | Routes to |
|---|---|
| `AI_*`, `SNOWFLAKE.CORTEX.*`, `.mutate()` | `references/cortex-ibis-api.md` |
| `EnrichmentPipeline`, fluent chain | `references/enrichment-pipeline.md` |
| Embeddings, `EMBED_TEXT_768/1024` | `references/embeddings.md` |
| Semantic search, vector similarity | `references/semantic-search.md` |
| REST API, `CortexInferenceClient`, PAT/JWT, streaming | `references/cortex-inference.md` |
| TurboPuffer, ANN, BM25, hybrid search | `references/turbopuffer.md` |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `401 Unauthorized` | PAT expired or wrong token | Regenerate PAT in Snowsight |
| `400 — temperature is deprecated` | Model is Opus 4.7+ | Remove `temperature`/`top_p`/`top_k` from payload |
| `400 — unknown model` | Model name typo or unavailable in region | Check `CURRENT_REGION()` and use `claude-4-sonnet` |
| `Tunnel connection failed: 403` | Running inside sandboxed env | Use `dangerously_disable_sandbox=True` or run outside |
| `KEYPAIR_JWT` 401 | Wrong account/user in JWT issuer | Match `CURRENT_ACCOUNT()` / `CURRENT_USER()` |
