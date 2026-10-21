"""
The assurance boundary, demonstrated.

    python3 examples/assurance_boundary_demo.py

Five extractions cross the boundary. Two are accepted, one with warnings; three
are rejected. Each rejection is a failure that reaches the valuation engine
unchecked in the current notebook workflow, where DCF inputs are hand-typed
dicts and the LLM's extraction output is never parsed at all.

This is the architectural point of the whole platform: the LLM proposes,
the boundary decides, and only validated inputs reach deterministic computation.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assurance import BoundaryRejection, cross_boundary  # noqa: E402

FIRM_WACC = Decimal("0.12")          # firm-level judgment, never read from the CIM
FIRM_TERMINAL_GROWTH = Decimal("0.03")


def prov(quote: str | None = "see attached", confidence: float = 0.94, page: int = 12) -> dict:
    return {
        "source_document": "acme_cim_2026.pdf",
        "page": page,
        "quote": quote,
        "extracted_by": "cortex:claude-opus-4-6",
        "confidence": confidence,
    }


def val(v: str, unit: str = "USD", **kw) -> dict:
    return {"value": v, "unit": unit, "provenance": prov(**kw)}


def base_extraction(**overrides) -> dict:
    payload = {
        "company_name": "Acme Industrial Holdings",
        "revenue": val("100000000", quote="Revenue of $100.0M for FY2025"),
        "ebitda_margin": val("0.25", "ratio", quote="EBITDA margin of 25.0%"),
        "revenue_growth_rate": val("0.15", "ratio", quote="15% YoY revenue growth"),
        "tax_rate": val("0.25", "ratio", quote="effective tax rate of 25%"),
        "fiscal_year": 2025,
        "currency": "USD",
        "unresolved_items": [],
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------

CASES: list[tuple[str, str, dict, dict]] = []

CASES.append((
    "1. Clean extraction",
    "Well-formed, fully sourced, plausible. Passes straight through.",
    base_extraction(),
    {},
))

# The classic extraction error: "25%" emitted as 25 instead of 0.25.
_pct = base_extraction()
_pct["ebitda_margin"]["value"] = "25"
CASES.append((
    "2. Percentage / ratio confusion",
    "The model wrote 25 where it meant 0.25 — a 2500% EBITDA margin. Arithmetically "
    "impossible, so the schema blocks it. Unchecked, this produces a spectacular "
    "valuation that looks like a find.",
    _pct,
    {},
))

CASES.append((
    "3. Terminal growth above WACC",
    "The most dangerous silent error in a DCF. dcf.rs computes "
    "fcf*(1+g)/(wacc-g) with no guard, so g > wacc gives a negative denominator "
    "and a confidently negative terminal value. No exception, no warning — just a "
    "wrong number in an IC memo.",
    base_extraction(),
    {"wacc": Decimal("0.03"), "terminal_growth": Decimal("0.05")},
))

# Unusual but real: software-like margin on an industrial name.
_high = base_extraction()
_high["ebitda_margin"]["value"] = "0.58"
_high["ebitda_margin"]["provenance"]["confidence"] = 0.61
_high["unresolved_items"] = ["FY2025 capex not disclosed in the CIM"]
CASES.append((
    "4. Unusual but legitimate",
    "A 58% margin is atypical for industrials but entirely real in software. "
    "Accepted with warnings and routed for sign-off rather than blocked — "
    "blocking here would fail on exactly the deals worth a second look.",
    _high,
    {},
))

CASES.append((
    "5. Hallucinated field",
    "The model volunteered a projected IRR nobody asked for. Under extra='forbid' "
    "that is a schema violation, not a bonus: a model inventing fields has "
    "misunderstood the task, and silently dropping them hides the problem.",
    base_extraction(projected_irr="0.31"),
    {},
))


def main() -> int:
    print("=" * 78)
    print("ASSURANCE BOUNDARY — LLM output -> typed contract -> validation -> engine")
    print("=" * 78)
    print(f"Firm inputs (not extracted from the document): WACC={FIRM_WACC}, "
          f"g={FIRM_TERMINAL_GROWTH}")

    accepted = rejected = 0

    for title, rationale, payload, overrides in CASES:
        print("\n" + "-" * 78)
        print(title)
        print("-" * 78)
        print(f"  {rationale}")
        print()

        params = {"wacc": FIRM_WACC, "terminal_growth": FIRM_TERMINAL_GROWTH, "strict": True}
        params.update(overrides)

        try:
            report = cross_boundary(payload, **params)
            accepted += 1
            dcf = report.validated_inputs.dcf
            print(f"  ACCEPTED — inputs reached the engine")
            print(f"    revenue={dcf.initial_revenue:,} margin={dcf.ebitda_margin} "
                  f"wacc={dcf.wacc} g={dcf.terminal_growth}")
            print(f"    input_hash={report.validated_inputs.input_hash[:16]}...")
            for f in report.warnings:
                print(f"    {f}")
            if report.validated_inputs.requires_human_signoff:
                print("    -> HUMAN SIGN-OFF REQUIRED before this valuation is used")
        except BoundaryRejection as rej:
            rejected += 1
            print("  REJECTED — nothing reached the engine")
            for f in rej.report.errors:
                print(f"    {f}")

    print("\n" + "=" * 78)
    print(f"{accepted} accepted, {rejected} rejected")
    print()
    print("Every rejection above is a number that would have reached a valuation")
    print("engine — and an IC memo — in a pipeline without this boundary. Note that")
    print("none of them are LLM failures of intelligence: they are failures of")
    print("*interface*. The fix is architectural, not a better prompt.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
