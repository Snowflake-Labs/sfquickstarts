"""
PE Agentic System - Config-Driven Model Routing Showcase

Demonstrates:
  1. The same PE task auto-resolving to different models per platform
     (Claude <-> GPT) purely from config/models.yaml.
  2. WHERE a heavy "reasoning" model makes sense vs a cheaper "cheap" model.
  3. Using the router directly and via the PEAgentClient.

Run:  python examples/model_routing_showcase.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.models_loader import get_router


def render_table(router):
    print("=" * 100)
    print("CONFIG-DRIVEN MODEL ROUTING  (config/models.yaml)")
    print("=" * 100)
    header = f"{'PE task':<16}{'Cortex':<26}{'OpenAI':<26}{'Bedrock':<30}"
    print(header)
    print("-" * 100)
    for task in ("reasoning", "modeling", "extraction", "summarization", "default"):
        row = f"{task:<16}"
        for plat in ("cortex", "openai", "bedrock"):
            info = router.tier_for(task, default_platform=plat)
            row += f"{info['model']:<26}"
        print(row)
    print()


def render_showcase(router):
    print("=" * 100)
    print("WHEN TO USE A REASONING MODEL vs A CHEAPER MODEL")
    print("=" * 100)
    print("\n[reasoning tier -> Claude Opus 4.6 / GPT 5.4] (higher cost, capable)")
    for t in router.showcase.get("reasoning_tasks", []):
        print(f"   - {t}")
    print("\n[cheap tier -> GPT 5.1 / Claude Sonnet 4.5] (fast, lower cost)")
    for t in router.showcase.get("cheap_tasks", []):
        print(f"   - {t}")

    print("\nRouting rules (task -> tier -> model for Cortex):")
    for task in ("reasoning", "modeling", "extraction", "summarization"):
        info = router.tier_for(task, default_platform="cortex")
        why = "needs deep multi-step judgment / correct code" if info["tier"] == "reasoning" else "mechanical, high-volume, cheap to run"
        print(f"   * {task:<12} -> {info['tier']:<10} ({info['model']:<24}) [{why}]")


def main():
    router = get_router()
    render_table(router)
    render_showcase(router)

    print("\nExample: pick the model for generating an IC memo on each platform:")
    for plat in ("cortex", "openai", "bedrock"):
        info = router.tier_for("reasoning", default_platform=plat)
        print(f"   agent = create_pe_agent('{plat}')   # uses {info['model']} (tier={info['tier']}, cost={info['cost_rank']})")

    print("\nTo swap GPT <-> Claude WITHOUT code changes, edit config/models.yaml")
    print("under 'platform_tiers' or 'family_defaults'.")


if __name__ == "__main__":
    main()
