# Config-Driven Model Routing

Model selection across **Claude and GPT** is now driven by a single
config file (`config/models.yaml`) instead of hardcoded dictionaries. Change a
model, a price tier, or a task's routing *without touching any Python code*.

## Files

| File | Purpose |
|------|---------|
| `config/models.yaml`       | Model catalog, per-platform model IDs, task→tier routing |
| `config/models_loader.py`  | `ModelRouter` — resolves task → tier → model ID |
| `examples/model_routing_showcase.py` | Runnable demo of the routing logic |
| `examples/reasoning_demo.sql`      | Live Cortex-Inference comparison: reasoning vs cheap model |

## How it works

```
PE task  ->  task_routing[tier]  ->  platform_tiers[platform][tier]  ->  model ID
```

* **`task_routing`** — assigns a tier to each task:
  `reasoning`, `modeling` → **reasoning**; `extraction`, `summarization` → **cheap**;
  `default` → **balanced**.
* **`platform_tiers`** — for each platform (`cortex`, `openai`, `bedrock`) which
  concrete model to use per tier.
* **`family_defaults`** — fallback per family (`gpt`, `claude`)
  used when a platform doesn't override a tier.

## Showcased models

| Model | Family | Tier | When |
|-------|--------|------|------|
| `openai-gpt-5.4`  | gpt    | reasoning | strong reasoning, codegen (live) |
| `claude-opus-4-6` | claude | reasoning | deepest reasoning (DD, IC memos) |
| `claude-sonnet-4-5`| claude | balanced  | fast extraction & balanced tasks |
| *(reference-only, not on this account)* — `openai-gpt-5.6`, `openai-gpt-sol`, `mistral-large-2-2`, `llama-4.1-nemotron` |
| `anthropic.claude-3-haiku-20240307-v1` | claude | cheap | cheap & fast extraction |

## When to use a reasoning vs a cheaper model

**Reasoning tier (Claude Opus 4.6 / GPT 5.4)** — use when the task needs
multi-step judgment, long-context synthesis, or correct code that must run:
- IC memo drafting
- Deep due-diligence / red-flag analysis on long documents
- Executable financial model generation (DCF, LBO, cap table)
- Deal thesis synthesis across many sources

**Cheap tier (GPT 5.1 / Claude Sonnet 4.5)** — use for high-volume, mechanical work
where per-token cost and latency dominate quality headroom:
- Extracting metrics / entities / table fields from a CIM
- Portfolio KPI summarization and traffic-light statusing
- Bulk document classification / triage
- Routine Q&A on structured data

## Live demonstration: reasoning vs cheap model

Same PE task run on the active connection through three models
(`examples/reasoning_demo.sql`):

| Model | Tier | Y1 EBITDA basis | Taxes assumed | Y1 UFCF | MOIC |
|-------|------|-----------------|---------------|---------|------|
| `claude-opus-4-6` | reasoning | $50M (LTM) | 25% | $26.25M | 1.62x |
| `claude-sonnet-4-5` | balanced/cheap | $52.5M (grown) | 25% | $28.1M | 1.62x |
| `openai-gpt-5.4` | reasoning | $52.5M (grown) | 0% | $37.5M | 1.62x |

While the MOIC remains consistent at approximately 1.62x, the Year-1 UFCF
fluctuates by 40% due to variable assumptions regarding EBITDA timing and tax
rates. Reasoning-tier models provided superior value by identifying,
stress-testing, and highlighting these uncertainties. In contrast, lower-cost
models prioritized speed, offering a single output without flagging the
underlying risks. This distinction defines their use cases: lower-cost models
are sufficient for mechanical calculations, whereas reasoning-tier models are
necessary when financial judgment and risk assessment are required.

## Usage

```python
from config.models_loader import get_router

router = get_router()
info = router.tier_for("extraction", default_platform="cortex")
# {'task': 'extraction', 'tier': 'cheap', 'model': 'openai-gpt-5.1',
#  'cost_rank': 'mid', 'max_output_tokens': 16384, ...}

model = router.resolve("reasoning", platform="openai")  # 'openai-gpt-5.4'
```

Through the agent client:

```python
from integrations.python.openai_compatible_client import create_pe_agent

agent = create_pe_agent("cortex", session=session)   # same code, any platform
agent = create_pe_agent("openai")                     # GPT family
agent = create_pe_agent("bedrock")                    # Claude family (AWS)

info = agent.get_model_info("extraction")             # shows tier + why
print(info["model"], info["tier"], info["cost_rank"])
```

## Swapping families

To prefer **Claude** on Cortex instead of GPT, edit `config/models.yaml`:

```yaml
platform_tiers:
  cortex:
    reasoning: "claude-opus-4-6"   # default for cortex
    balanced:  "claude-sonnet-4-5"
    cheap:     "openai-gpt-5.1"
```

No code changes needed.

## Run the demo

```bash
python examples/model_routing_showcase.py
```
