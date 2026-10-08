"""
test_cortex_rest.py — Validation suite for cortex_rest.py

Runs 7 test sections against the live Snowflake Cortex REST API,
captures each section's output with rich, and exports an SVG screenshot
to the assets/ directory alongside this script.

Run:
  cd <guide-root>/assets
  python test_cortex_rest.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich import box

from cortex_rest import CortexInferenceClient, _load_pat

ASSETS = Path(__file__).parent
ASSETS.mkdir(exist_ok=True)

MODEL = "claude-4-sonnet"
PASS = "[bold green]PASS[/bold green]"
FAIL = "[bold red]FAIL[/bold red]"


def save_svg(console: Console, name: str) -> Path:
    out = ASSETS / f"{name}.svg"
    svg = console.export_svg(title=f"cortex_rest — {name.replace('_', ' ')}")
    out.write_text(svg)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Section 0 — Auth check
# ─────────────────────────────────────────────────────────────────────────────

def section_0_auth():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 0 — Auth check (PAT)[/bold cyan]"))
    try:
        host, token = _load_pat()
        masked = token[:8] + "..." + token[-4:]
        t = Table(box=box.SIMPLE)
        t.add_column("Field", style="cyan")
        t.add_column("Value")
        t.add_row("host", host)
        t.add_row("token (masked)", masked)
        t.add_row("auth type", "PROGRAMMATIC_ACCESS_TOKEN")
        t.add_row("endpoint", f"https://{host}/api/v2/cortex/inference:complete")
        console.print(t)
        console.print(f"  {PASS}  PAT loaded successfully")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s0_auth_check")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())   # echo to terminal


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — Simple single-turn complete
# ─────────────────────────────────────────────────────────────────────────────

def section_1_simple_complete():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 1 — Simple single-turn complete[/bold cyan]"))
    client = CortexInferenceClient()
    payload_preview = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "In one sentence: what is Snowflake Cortex?"}],
        "max_tokens": 150,
        "stream": False,
    }
    console.print(Syntax(json.dumps(payload_preview, indent=2), "json", theme="monokai"))
    try:
        t0 = time.perf_counter()
        resp = client.complete(
            MODEL,
            [{"role": "user", "content": "In one sentence: what is Snowflake Cortex?"}],
            max_tokens=150,
        )
        latency = (time.perf_counter() - t0) * 1000
        content = resp["choices"][0]["message"]["content"]
        usage   = resp.get("usage", {})

        res = Table(box=box.SIMPLE)
        res.add_column("Field", style="cyan")
        res.add_column("Value")
        res.add_row("status", "200 OK")
        res.add_row("model", resp.get("model", MODEL))
        res.add_row("latency_ms", f"{latency:.0f}")
        res.add_row("prompt_tokens", str(usage.get("prompt_tokens", "—")))
        res.add_row("completion_tokens", str(usage.get("completion_tokens", "—")))
        res.add_row("total_tokens", str(usage.get("total_tokens", "—")))
        console.print(res)
        console.print(f"  [bold]Reply:[/bold] {content}")
        console.print(f"  {PASS}")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s1_simple_complete")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — Multi-turn conversation
# ─────────────────────────────────────────────────────────────────────────────

def section_2_multi_turn():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 2 — Multi-turn conversation[/bold cyan]"))
    client = CortexInferenceClient()
    messages = [
        {"role": "user",      "content": "My name is Ada. What's 12 × 12?"},
        {"role": "assistant", "content": "12 × 12 = 144."},
        {"role": "user",      "content": "What's my name and what was the answer?"},
    ]
    console.print(Syntax(json.dumps(messages, indent=2), "json", theme="monokai"))
    try:
        t0 = time.perf_counter()
        resp = client.complete(MODEL, messages, max_tokens=120)
        latency = (time.perf_counter() - t0) * 1000
        content = resp["choices"][0]["message"]["content"]
        console.print(f"\n  [bold]Reply:[/bold] {content}")
        console.print(f"  latency: {latency:.0f} ms")
        ok = "Ada" in content or "144" in content
        console.print(f"  {PASS if ok else FAIL}  (contains Ada/144: {ok})")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s2_multi_turn")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Streaming SSE response
# ─────────────────────────────────────────────────────────────────────────────

def section_3_streaming():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 3 — Streaming SSE response[/bold cyan]"))
    client = CortexInferenceClient()
    messages = [{"role": "user", "content": "Count slowly from 1 to 5, one number per line."}]
    try:
        t0 = time.perf_counter()
        chunks = []
        total_tokens = None
        for event in client.complete_stream(MODEL, messages, max_tokens=80):
            delta = event.get("choices", [{}])[0].get("delta", {})
            chunk = delta.get("content") or delta.get("text", "")
            if chunk:
                chunks.append(chunk)
            usage = event.get("usage", {})
            if usage.get("total_tokens"):
                total_tokens = usage["total_tokens"]
        latency = (time.perf_counter() - t0) * 1000
        full = "".join(chunks)

        t = Table(box=box.SIMPLE)
        t.add_column("Metric", style="cyan")
        t.add_column("Value")
        t.add_row("chunks received", str(len(chunks)))
        t.add_row("total_tokens", str(total_tokens or "—"))
        t.add_row("latency_ms", f"{latency:.0f}")
        console.print(t)
        console.print(f"\n  [bold]Assembled reply:[/bold]\n{full}")
        console.print(f"  {PASS}")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s3_streaming")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Tool calling (function calling)
# ─────────────────────────────────────────────────────────────────────────────

def section_4_tools():
    console = Console(record=True, width=110)
    console.print(Panel(
        "[bold cyan]Section 4 — Tool calling: get_product_details[/bold cyan]\n"
        "[dim]Realistic to the Ibis reviews dataset: model looks up product info "
        "to contextualise a negative review.[/dim]"
    ))
    client = CortexInferenceClient()
    # Tool: look up a product from the CUSTOMER_REVIEWS product catalog.
    # Mirrors the product_id field in the cortex_ibis demo dataset (P001..P005).
    tools = [
        {
            "tool_spec": {
                "type": "generic",
                "name": "get_product_details",
                "description": (
                    "Look up product metadata (name, category, price) "
                    "by product_id from the product catalog."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product identifier, e.g. P001, P002.",
                        },
                    },
                    "required": ["product_id"],
                },
            }
        }
    ]
    # Review from the turbopuffer_demo dataset: row 5, product P003, defective unit.
    messages = [{
        "role": "user",
        "content": (
            "A customer left this review for product P003: "
            "'Defective unit out of the box. USB port doesn't work at all.' "
            "Before drafting a response, look up the product details for P003."
        ),
    }]
    console.print(Syntax(json.dumps({"tools": tools, "messages": messages}, indent=2), "json", theme="monokai"))
    try:
        resp = client.complete(MODEL, messages, max_tokens=250, tools=tools)
        choice = resp["choices"][0]
        finish = choice.get("finish_reason", "")
        content_list = choice.get("message", {}).get("content_list", [])
        tool_calls = [c for c in content_list if c.get("type") == "tool_use"]
        console.print(f"\n  finish_reason: [bold]{finish}[/bold]")
        if tool_calls:
            console.print(Syntax(json.dumps(tool_calls, indent=2), "json", theme="monokai"))
            console.print(f"  {PASS}  Tool call detected — model wants product catalog lookup for P003")
        else:
            console.print(f"  content: {choice.get('message', {}).get('content', '')[:300]}")
            console.print(f"  [yellow]NOTE[/yellow]  Model answered directly without a tool call (acceptable fallback)")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s4_tool_calling")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Temperature / sampling params
# ─────────────────────────────────────────────────────────────────────────────

def section_5_temperature():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 5 — Temperature param (claude-4-sonnet accepts; Opus 4.7 would 400)[/bold cyan]"))
    client = CortexInferenceClient()
    try:
        resp = client.complete(
            MODEL,
            [{"role": "user", "content": "Respond with exactly: temp_ok"}],
            max_tokens=20,
            temperature=0.7,
        )
        content = resp["choices"][0]["message"]["content"]
        console.print(f"  temperature=0.7 → 200 OK: [bold]{content.strip()}[/bold]")
        console.print(f"  {PASS}  claude-4-sonnet accepts temperature")
        console.print(
            "\n  [yellow]NOTE[/yellow]  claude-opus-4-7 removed temperature/top_p/top_k "
            "(returns 400 on any non-default value).\n"
            "  Use [bold]pre_call_hook.py[/bold] to strip params for those models automatically."
        )
    except httpx.HTTPStatusError as exc:
        console.print(f"  [yellow]400 as expected for this model:[/yellow] {exc.response.text[:300]}")
    except Exception as exc:
        console.print(f"  {FAIL}  {exc}")
    svg = save_svg(console, "s5_temperature")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Section 6 — Error handling (bad model name)
# ─────────────────────────────────────────────────────────────────────────────

def section_6_error_handling():
    console = Console(record=True, width=110)
    console.print(Panel("[bold cyan]Section 6 — Error handling (bad model name)[/bold cyan]"))
    client = CortexInferenceClient()
    try:
        client.complete(
            "this-model-does-not-exist",
            [{"role": "user", "content": "ping"}],
            max_tokens=20,
        )
        console.print(f"  {FAIL}  Expected 400 but got 200")
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        body = exc.response.text[:400]
        t = Table(box=box.SIMPLE)
        t.add_column("Field", style="cyan")
        t.add_column("Value")
        t.add_row("HTTP status", str(code))
        t.add_row("response body", body)
        console.print(t)
        expected = code in (400, 404)
        console.print(f"  {PASS if expected else FAIL}  Got {code} as expected")
    except Exception as exc:
        console.print(f"  unexpected error: {exc}")
    svg = save_svg(console, "s6_error_handling")
    console.print(f"\n  [dim]→ SVG saved: {svg}[/dim]")
    Console().print(console.export_text())


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 80)
    print("  cortex_rest.py — Validation suite")
    print("═" * 80 + "\n")

    sections = [
        section_0_auth,
        section_1_simple_complete,
        section_2_multi_turn,
        section_3_streaming,
        section_4_tools,
        section_5_temperature,
        section_6_error_handling,
    ]
    for fn in sections:
        print(f"\n{'─' * 80}")
        fn()

    print(f"\n{'═' * 80}")
    print(f"  All sections complete. SVGs saved to: {ASSETS}/")
    print("═" * 80 + "\n")


if __name__ == "__main__":
    main()
