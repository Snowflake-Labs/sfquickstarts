"""
Tests for the assurance boundary.

These double as the session demo: each test is a failure mode that reaches a
valuation engine unchecked in the current notebook workflow, where DCF inputs are
hand-typed dicts and LLM extraction output is never parsed at all.

Run:  python3 -m pytest tests/test_assurance.py -v
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from assurance import BoundaryRejection, Severity, cross_boundary

WACC = Decimal("0.12")
TERMINAL_GROWTH = Decimal("0.03")


def make_extraction(**overrides) -> dict:
    """A well-formed extraction. Tests corrupt one thing at a time."""

    def value(v, unit="USD", quote="see attached", confidence=0.94):
        return {
            "value": v,
            "unit": unit,
            "provenance": {
                "source_document": "acme_cim_2026.pdf",
                "page": 12,
                "quote": quote,
                "extracted_by": "cortex:claude-opus-4-6",
                "confidence": confidence,
            },
        }

    base = {
        "company_name": "Acme Industrial Holdings",
        "revenue": value("100000000", quote="Revenue of $100.0M for FY2025"),
        "ebitda_margin": value("0.25", unit="ratio", quote="EBITDA margin of 25.0%"),
        "revenue_growth_rate": value("0.15", unit="ratio", quote="15% YoY growth"),
        "tax_rate": value("0.25", unit="ratio", quote="effective tax rate of 25%"),
        "fiscal_year": 2025,
        "currency": "USD",
        "unresolved_items": [],
    }
    base.update(overrides)
    return base


def cross(payload, **kw):
    params = {"wacc": WACC, "terminal_growth": TERMINAL_GROWTH, "strict": True}
    params.update(kw)
    return cross_boundary(payload, **params)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_clean_extraction_is_accepted():
    report = cross(make_extraction())
    assert report.accepted
    assert report.errors == []
    assert report.warnings == []

    dcf = report.validated_inputs.dcf
    assert dcf.initial_revenue == Decimal("100000000")
    assert dcf.ebitda_margin == Decimal("0.25")
    assert isinstance(dcf.initial_revenue, Decimal), "money must not become float"
    assert not report.validated_inputs.requires_human_signoff


def test_accepted_inputs_are_hashed_for_audit():
    """A reviewer must be able to prove which inputs produced a valuation."""
    a = cross(make_extraction())
    b = cross(make_extraction())
    assert a.validated_inputs.input_hash == b.validated_inputs.input_hash

    c = cross(make_extraction(fiscal_year=2024), wacc=Decimal("0.13"))
    assert c.validated_inputs.input_hash != a.validated_inputs.input_hash


def test_inputs_are_immutable_after_validation():
    """Validated inputs must not be mutable, or validation proves nothing."""
    report = cross(make_extraction())
    with pytest.raises(Exception):
        report.validated_inputs.dcf.wacc = Decimal("0.01")


# ---------------------------------------------------------------------------
# Schema violations — blocking
# ---------------------------------------------------------------------------


def test_malformed_json_is_rejected():
    with pytest.raises(BoundaryRejection) as exc:
        cross("{'company_name': 'Acme', truncated...")
    assert exc.value.report.errors[0].code == "MALFORMED_JSON"


def test_missing_required_field_is_rejected():
    payload = make_extraction()
    del payload["ebitda_margin"]
    with pytest.raises(BoundaryRejection) as exc:
        cross(payload)
    assert any(f.code == "SCHEMA_VIOLATION" for f in exc.value.report.errors)


def test_hallucinated_extra_field_is_rejected():
    """extra='forbid'. A model inventing fields misunderstood the task; silently
    dropping them hides that."""
    with pytest.raises(BoundaryRejection) as exc:
        cross(make_extraction(projected_irr="0.28"))
    assert any(f.code == "SCHEMA_VIOLATION" for f in exc.value.report.errors)


def test_percentage_confused_for_ratio_is_rejected():
    """The classic extraction error: '25%' emitted as 25 rather than 0.25. A
    2500% EBITDA margin would otherwise produce a spectacular valuation."""
    payload = make_extraction()
    payload["ebitda_margin"]["value"] = "25"
    with pytest.raises(BoundaryRejection) as exc:
        cross(payload)
    assert any("ebitda_margin" in f.field_path for f in exc.value.report.errors)


def test_negative_revenue_is_rejected():
    payload = make_extraction()
    payload["revenue"]["value"] = "-5000000"
    with pytest.raises(BoundaryRejection):
        cross(payload)


def test_placeholder_company_name_is_rejected():
    for placeholder in ("Unknown", "N/A", "TBD", "target"):
        with pytest.raises(BoundaryRejection):
            cross(make_extraction(company_name=placeholder))


# ---------------------------------------------------------------------------
# Structural coherence — the dangerous silent errors
# ---------------------------------------------------------------------------


def test_terminal_growth_above_wacc_is_rejected():
    """
    The most dangerous silent error in a DCF. dcf.rs computes
    fcf * (1+g) / (wacc - g) with no guard, so g > wacc yields a negative
    denominator and a confidently negative terminal value. Must never reach it.
    """
    with pytest.raises(BoundaryRejection) as exc:
        cross(make_extraction(), wacc=Decimal("0.03"), terminal_growth=Decimal("0.05"))
    codes = {f.code for f in exc.value.report.errors}
    assert "WACC_BELOW_TERMINAL_GROWTH" in codes


def test_wacc_equal_to_terminal_growth_is_rejected():
    """Division by zero, not merely implausible."""
    with pytest.raises(BoundaryRejection):
        cross(make_extraction(), wacc=Decimal("0.04"), terminal_growth=Decimal("0.04"))


def test_narrow_spread_warns_but_does_not_block():
    """Legal but hypersensitive: terminal value dominates. Needs a human, not a block."""
    report = cross(make_extraction(), wacc=Decimal("0.055"), terminal_growth=Decimal("0.04"))
    assert report.accepted
    assert "NARROW_WACC_TERMINAL_SPREAD" in {f.code for f in report.warnings}
    assert report.validated_inputs.requires_human_signoff


# ---------------------------------------------------------------------------
# Plausibility — warns, never blocks
# ---------------------------------------------------------------------------


def test_unusual_margin_warns_rather_than_blocking():
    """A 60% EBITDA margin is unusual but real (software). Blocking it would fail
    on exactly the deals worth looking at."""
    payload = make_extraction()
    payload["ebitda_margin"]["value"] = "0.60"
    report = cross(payload)
    assert report.accepted
    assert "EBITDA_MARGIN_OUTSIDE_TYPICAL_RANGE" in {f.code for f in report.warnings}


def test_units_error_surfaces_as_revenue_floor_warning():
    """$100M reported in thousands reads as $100k. Arithmetically fine, so it
    can only be caught as a plausibility signal."""
    payload = make_extraction()
    payload["revenue"]["value"] = "100000"
    report = cross(payload)
    assert report.accepted
    assert "REVENUE_BELOW_FLOOR" in {f.code for f in report.warnings}


def test_implausible_values_are_never_silently_clamped():
    """Clamping a misread 60% margin to 45% would yield a plausible valuation
    from bad data — worse than either accepting or rejecting."""
    payload = make_extraction()
    payload["ebitda_margin"]["value"] = "0.60"
    report = cross(payload)
    assert report.validated_inputs.dcf.ebitda_margin == Decimal("0.60")


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def test_missing_quote_warns():
    payload = make_extraction()
    payload["revenue"]["provenance"]["quote"] = None
    report = cross(payload)
    assert report.accepted
    assert "MISSING_SUPPORTING_QUOTE" in {f.code for f in report.warnings}


def test_low_confidence_warns():
    payload = make_extraction()
    payload["revenue"]["provenance"]["confidence"] = 0.42
    report = cross(payload)
    assert "LOW_EXTRACTION_CONFIDENCE" in {f.code for f in report.warnings}


def test_high_confidence_does_not_excuse_a_structural_error():
    """Confidence is advisory. A model can be certain and wrong."""
    payload = make_extraction()
    for field in ("revenue", "ebitda_margin", "revenue_growth_rate", "tax_rate"):
        payload[field]["provenance"]["confidence"] = 1.0
    with pytest.raises(BoundaryRejection):
        cross(payload, wacc=Decimal("0.02"), terminal_growth=Decimal("0.05"))


def test_unresolved_items_warn_rather_than_block():
    """A model declining to guess is behaving correctly and must not be punished
    for it — but a human has to see the gap."""
    report = cross(make_extraction(unresolved_items=["FY2025 capex not disclosed"]))
    assert report.accepted
    assert "UNRESOLVED_EXTRACTION_ITEMS" in {f.code for f in report.warnings}


def test_provenance_is_required():
    payload = make_extraction()
    del payload["revenue"]["provenance"]
    with pytest.raises(BoundaryRejection):
        cross(payload)


# ---------------------------------------------------------------------------
# Report behaviour
# ---------------------------------------------------------------------------


def test_non_strict_mode_reports_instead_of_raising():
    """For batch triage: collect findings across many deals without aborting."""
    report = cross_boundary(
        make_extraction(), wacc=Decimal("0.02"),
        terminal_growth=Decimal("0.05"), strict=False,
    )
    assert not report.accepted
    assert report.validated_inputs is None
    assert report.errors


def test_findings_are_machine_readable():
    """Findings must be queryable in Snowflake, not parsed out of strings."""
    report = cross_boundary(
        make_extraction(), wacc=Decimal("0.02"),
        terminal_growth=Decimal("0.05"), strict=False,
    )
    f = report.errors[0]
    assert f.code and f.severity is Severity.ERROR
    assert json.loads(f.model_dump_json())["code"] == f.code


def test_raw_input_is_hashed_even_on_rejection():
    """Rejected extractions still need an audit record of what was submitted."""
    report = cross_boundary("not json", wacc=WACC,
                            terminal_growth=TERMINAL_GROWTH, strict=False)
    assert len(report.raw_input_sha256) == 64


def test_summary_is_human_readable():
    report = cross_boundary(
        make_extraction(), wacc=Decimal("0.02"),
        terminal_growth=Decimal("0.05"), strict=False,
    )
    text = report.summary()
    assert "REJECTED" in text and "WACC_BELOW_TERMINAL_GROWTH" in text


def test_accepts_json_string_and_dict_identically():
    payload = make_extraction()
    assert (
        cross(payload).validated_inputs.input_hash
        == cross(json.dumps(payload)).validated_inputs.input_hash
    )
