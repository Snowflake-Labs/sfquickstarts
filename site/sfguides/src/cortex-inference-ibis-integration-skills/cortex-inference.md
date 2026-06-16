# Cortex REST API Reference

Direct HTTP client in `cortex_rest.py`. Use when you need streaming, tool calling, or want to bypass the SQL connector.

## PAT Auth (default — auto-loaded from config.toml)

```python
from cortex_rest import CortexInferenceClient

client = CortexInferenceClient()   # reads ~/.snowflake/config.toml → connections.myaccount.password

# Headers sent:
# Authorization: Bearer <token>
# X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN
```

## JWT Key-Pair Auth

```python
client = CortexInferenceClient(
    auth="jwt",
    account="myorg-myaccount",
    user="you@example.com",
    private_key_path="~/.ssh/snowflake_rsa_key.p8",
)
# Headers sent:
# Authorization: Bearer <signed_jwt>
# X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT
```

## Simple Complete

```python
resp = client.complete(
    "claude-4-sonnet",
    [{"role": "user", "content": "Summarise this review in one line."}],
    max_tokens=100,
)
text = resp["choices"][0]["message"]["content"]
usage = resp["usage"]   # {prompt_tokens, completion_tokens, total_tokens}
```

## Streaming SSE

```python
for event in client.complete_stream("claude-4-sonnet", messages, max_tokens=500):
    delta = event["choices"][0]["delta"]
    chunk = delta.get("content") or delta.get("text", "")
    print(chunk, end="", flush=True)
# Last event has: event["usage"]["total_tokens"]
```

## Tool Calling (Snowflake tool_spec format)

```python
tools = [{
    "tool_spec": {
        "type": "generic",
        "name": "get_product_details",
        "description": "Look up product metadata by product_id.",
        "input_schema": {
            "type": "object",
            "properties": {"product_id": {"type": "string"}},
            "required": ["product_id"],
        },
    }
}]
resp = client.complete("claude-4-sonnet", messages, tools=tools, max_tokens=250)
# Tool call in response:
content_list = resp["choices"][0]["message"]["content_list"]
tool_calls = [c for c in content_list if c.get("type") == "tool_use"]
# → [{"type": "tool_use", "tool_use": {"name": "get_product_details", "input": {"product_id": "P003"}}}]
```

## Sampling Parameters — Important

| Model | temperature / top_p / top_k |
|---|---|
| `claude-4-sonnet`, `llama3.3-70b`, etc. | Accepted |
| `claude-opus-4-7` and newer Opus | **Removed** — returns 400 on any non-default value |

Strip before sending for Opus 4.7+:
```python
for k in ("temperature", "top_p", "top_k"):
    payload.pop(k, None)
```

## Error Handling

```python
import httpx
try:
    resp = client.complete("bad-model", messages)
except httpx.HTTPStatusError as exc:
    print(exc.response.status_code)   # 400
    print(exc.response.json())        # {"message": "unknown model \"bad-model\""}
```

## Module-Level Shortcuts

```python
from cortex_rest import complete, stream

# One-shot (returns string)
print(complete("What is 2+2?"))

# Streaming (yields chunks)
for chunk in stream("Explain vector search in two sentences."):
    print(chunk, end="", flush=True)
```

## LiteLLM Integration Note

When routing through LiteLLM proxy, prefix the token with `pat/`:
```yaml
api_key: os.environ/SNOWFLAKE_PAT   # .env: SNOWFLAKE_PAT=pat/<raw_token>
```
For direct `CortexInferenceClient`, use the raw token (no prefix).
