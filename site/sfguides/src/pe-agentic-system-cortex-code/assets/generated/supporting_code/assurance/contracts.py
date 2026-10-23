"""
Assurance boundary — the contract between probabilistic reasoning and
deterministic computation.

The architectural claim this package exists to make good on:

    probabilistic reasoning -> structured contract -> validated boundary
                            -> deterministic computation -> evidence-backed output

An LLM may *propose* financial assumptions. It may never hand them directly to a
valuation engine. Everything crossing this boundary is parsed into a typed
schema, range-checked, policy-checked, and stamped with provenance. Anything that
fails is rejected with a machine-readable reason — never silently coerced,
clamped, or defaulted.

Design rules, in priority order:

1.  **Fail closed.** An unparseable or out-of-policy extraction raises. There is
    no "best effort" path into the valuation engine. A missing number is a
    blocking finding, not a zero.
2.  **Never repair silently.** Clamping an implausible 400% EBITDA margin to 100%
    would produce a plausible-looking valuation from a misread document. Reject
    and surface it.
3.  **Provenance is mandatory, not optional.** Every field carries where it came
    from — page, quote, extracting model, confidence. A number no one can trace
    is not usable in an IC memo, however correct it happens to be.
4.  **Separate the impossible from the implausible.** Violating an identity
    (margins outside 0-100%, negative revenue) is an error. Being unusual (a 60%
    EBITDA margin) is a warning that a human must clear. Conflating the two
    either blocks legitimate deals or waves through bad data.
5.  **Economic coherence is part of validation.** WACC > terminal growth is not a
    style preference; violating it makes the Gordon Growth denominator negative
    and silently returns a *negative* terminal value. Structural checks of this
    kind belong at the boundary, not in the engine.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

__all__ = [
    "Severity",
    "Finding",
    "Provenance",
    "ExtractedValue",
    "CIMExtraction",
    "DCFAssumptions",
    "LBOAssumptions",
    "ValidatedModelInputs",
    "AssuranceReport",
    "BoundaryRejection",
    "cross_boundary",
]


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    """
    ERROR   — violates an identity or makes computation meaningless. Blocks.
    WARNING — possible but unusual. Requires explicit human sign-off.
    INFO    — recorded for the audit trail; does not gate anything.
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Finding(BaseModel):
    """A single validation result. Machine-readable so it can be logged, queried
    in Snowflake, and shown in a review UI without string parsing."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(description="Stable identifier, e.g. WACC_BELOW_TERMINAL_GROWTH")
    severity: Severity
    field_path: str = Field(description="Dotted path to the offending field")
    message: str
    observed: Any = None
    expected: str | None = None

    def __str__(self) -> str:
        loc = f"{self.field_path}: " if self.field_path else ""
        obs = f" (observed: {self.observed!r})" if self.observed is not None else ""
        return f"[{self.severity.value.upper()}] {self.code} — {loc}{self.message}{obs}"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """
    Where a number came from. Required on every extracted value.

    In private markets there is no market price to check a valuation against, so
    defensibility *is* the deliverable. A number without provenance cannot go in
    front of an IC, an auditor, or an LP, regardless of whether it is correct.
    """

    model_config = ConfigDict(frozen=True)

    source_document: str
    page: int | None = Field(default=None, ge=1)
    quote: str | None = Field(
        default=None,
        description="Verbatim supporting span from the source. Enables spot-audit "
        "without reopening the document.",
    )
    extracted_by: str = Field(description="Model or process identifier, e.g. 'cortex:claude-opus-4-6'")
    extracted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Self-reported model confidence. Advisory only — "
        "never used to bypass a check."
    )


class ExtractedValue(BaseModel):
    """A numeric value bound to its provenance.

    Decimal, not float: these are monetary and ratio quantities that must
    round-trip exactly against a spreadsheet in an audit.
    """

    model_config = ConfigDict(frozen=True)

    value: Decimal
    provenance: Provenance
    unit: Literal["USD", "ratio", "multiple", "years", "count"] = "USD"


# ---------------------------------------------------------------------------
# Stage 1 — the structured contract (what the LLM is allowed to return)
# ---------------------------------------------------------------------------


class CIMExtraction(BaseModel):
    """
    The *only* accepted shape for LLM output from a CIM.

    `extra="forbid"` is deliberate: a model that invents fields is
    misunderstanding the task, and silently discarding them hides that. Fail
    loudly instead.

    Field-level constraints here encode arithmetic impossibility only. Judgment
    about plausibility happens in validate(), so that impossible and merely
    unusual values produce different severities.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    company_name: str = Field(min_length=1, max_length=200)

    revenue: ExtractedValue
    ebitda_margin: ExtractedValue = Field(description="As a ratio, not a percentage: 0.25 not 25")
    revenue_growth_rate: ExtractedValue = Field(description="Ratio. May be negative.")
    tax_rate: ExtractedValue = Field(description="Ratio in [0, 1)")

    fiscal_year: int = Field(ge=1990, le=2100)
    currency: Literal["USD"] = "USD"

    unresolved_items: list[str] = Field(
        default_factory=list,
        description="Figures the model could not find or could not disambiguate. "
        "Populating this is a success, not a failure — it is how the model "
        "declines to guess.",
    )

    @model_validator(mode="after")
    def _reject_placeholder_names(self) -> CIMExtraction:
        """LLMs emit these when they have nothing; they must not reach an IC memo."""
        placeholders = {"unknown", "n/a", "na", "none", "null", "company", "target", "tbd", ""}
        if self.company_name.strip().lower() in placeholders:
            raise ValueError(
                f"company_name is a placeholder ({self.company_name!r}); extraction did not "
                "identify the target"
            )
        return self


# ---------------------------------------------------------------------------
# Stage 2 — validated engine inputs (what deterministic code may consume)
# ---------------------------------------------------------------------------


class DCFAssumptions(BaseModel):
    """Validated DCF inputs. Construction implies the boundary was crossed
    successfully; the engine performs no further checking."""

    model_config = ConfigDict(frozen=True)

    initial_revenue: Decimal = Field(gt=0)
    growth_rate: Decimal
    ebitda_margin: Decimal = Field(gt=0, le=1)
    tax_rate: Decimal = Field(ge=0, lt=1)
    wacc: Decimal = Field(gt=0, lt=1)
    terminal_growth: Decimal
    years: int = Field(ge=1, le=30)

    @model_validator(mode="after")
    def _terminal_growth_below_wacc(self) -> DCFAssumptions:
        """
        Gordon Growth requires wacc > terminal_growth. Violated, the denominator
        (wacc - g) goes negative and the engine returns a confidently negative
        terminal value rather than failing — the single most dangerous silent
        error in a DCF. dcf.rs does not guard this, so it is enforced here.
        """
        if self.terminal_growth >= self.wacc:
            raise ValueError(
                f"terminal_growth ({self.terminal_growth}) must be strictly less than "
                f"wacc ({self.wacc}); otherwise the Gordon Growth denominator is "
                "non-positive and terminal value is meaningless"
            )
        return self


class LBOAssumptions(BaseModel):
    """Validated LBO inputs."""

    model_config = ConfigDict(frozen=True)

    purchase_price: Decimal = Field(gt=0)
    debt_pct: Decimal = Field(ge=0, lt=1, description="Fully debt-funded (1.0) is not a buyout")
    entry_metric: Decimal = Field(gt=0)
    exit_multiple: Decimal = Field(gt=0)
    metric_cagr: Decimal
    hold_years: int = Field(ge=1, le=15)


class ValidatedModelInputs(BaseModel):
    """
    Everything downstream of the boundary, bundled with the evidence that it was
    checked. `input_hash` lets a later reviewer prove which exact inputs produced
    a given valuation.
    """

    model_config = ConfigDict(frozen=True)

    dcf: DCFAssumptions
    lbo: LBOAssumptions | None = None
    source_extraction: CIMExtraction
    findings: list[Finding]
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_hash: str

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARNING]

    @property
    def requires_human_signoff(self) -> bool:
        return bool(self.warnings)


# ---------------------------------------------------------------------------
# Policy thresholds
# ---------------------------------------------------------------------------

# Plausibility bands. Breaching one is a WARNING, never an ERROR: unusual
# companies exist, and blocking them would make the system useless on exactly
# the deals that matter most. Tune per strategy — these suit mid-market buyout.
POLICY = {
    "ebitda_margin_typical": (Decimal("0.02"), Decimal("0.45")),
    "growth_rate_typical": (Decimal("-0.20"), Decimal("0.60")),
    "tax_rate_typical": (Decimal("0.15"), Decimal("0.35")),
    "wacc_typical": (Decimal("0.06"), Decimal("0.20")),
    "terminal_growth_typical": (Decimal("0.00"), Decimal("0.04")),
    "revenue_floor": Decimal("1000000"),
    "min_wacc_terminal_spread": Decimal("0.02"),
    "min_confidence": Decimal("0.70"),
}


class BoundaryRejection(Exception):
    """Raised when input may not cross into deterministic computation.

    Carries the full report so a caller can log it, surface it for review, or
    route it back for re-extraction — without re-deriving what went wrong.
    """

    def __init__(self, report: AssuranceReport):
        self.report = report
        errors = report.errors
        super().__init__(
            f"{len(errors)} blocking finding(s): " + "; ".join(f.code for f in errors)
        )


class AssuranceReport(BaseModel):
    """Outcome of a boundary crossing: accepted or rejected, and why."""

    model_config = ConfigDict(frozen=True)

    accepted: bool
    findings: list[Finding]
    validated_inputs: ValidatedModelInputs | None = None
    raw_input_sha256: str

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARNING]

    def summary(self) -> str:
        head = "ACCEPTED" if self.accepted else "REJECTED"
        parts = [f"Boundary crossing: {head}", f"  input sha256: {self.raw_input_sha256[:16]}..."]
        if not self.findings:
            parts.append("  no findings")
        for f in self.findings:
            parts.append(f"  {f}")
        if self.accepted and self.warnings:
            parts.append(
                f"\n  {len(self.warnings)} warning(s) — human sign-off required before "
                "this valuation is used."
            )
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# The boundary itself
# ---------------------------------------------------------------------------


def _sha256_of(payload: str | dict) -> str:
    if isinstance(payload, dict):
        payload = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _band_check(
    name: str, value: Decimal, band_key: str, path: str, findings: list[Finding]
) -> None:
    low, high = POLICY[band_key]
    if not (low <= value <= high):
        findings.append(
            Finding(
                code=f"{name.upper()}_OUTSIDE_TYPICAL_RANGE",
                severity=Severity.WARNING,
                field_path=path,
                message=f"{name} is outside the typical band [{low}, {high}]; "
                "possible but requires human confirmation",
                observed=str(value),
                expected=f"[{low}, {high}]",
            )
        )


def cross_boundary(
    raw_llm_output: str | dict,
    *,
    wacc: Decimal,
    terminal_growth: Decimal,
    projection_years: int = 5,
    lbo_params: dict[str, Any] | None = None,
    strict: bool = True,
) -> AssuranceReport:
    """
    The single gate between LLM output and deterministic computation.

    `wacc` and `terminal_growth` are supplied by the caller, not extracted from
    the document, and that is deliberate: they are firm-level judgments owned by
    the investment team, not facts to be read out of a seller's CIM. Letting a
    model infer the discount rate from marketing material would let the document
    influence its own valuation.

    Args:
        raw_llm_output: JSON string or dict from the extraction model.
        wacc: Discount rate — a firm input.
        terminal_growth: Terminal growth — a firm input.
        projection_years: Explicit projection horizon.
        lbo_params: Optional LBO parameters; validated the same way.
        strict: If True, warnings do not block but are flagged for sign-off.
                If False, only schema/identity errors block. Warnings never
                auto-approve either way.

    Returns:
        AssuranceReport. Accepted reports carry `validated_inputs`.

    Raises:
        BoundaryRejection: if `strict` and there are blocking findings.
    """
    findings: list[Finding] = []
    raw_hash = _sha256_of(raw_llm_output)

    # -- Stage 1: parse into the contract ----------------------------------
    try:
        payload = json.loads(raw_llm_output) if isinstance(raw_llm_output, str) else raw_llm_output
    except json.JSONDecodeError as exc:
        report = AssuranceReport(
            accepted=False,
            raw_input_sha256=raw_hash,
            findings=[
                Finding(
                    code="MALFORMED_JSON",
                    severity=Severity.ERROR,
                    field_path="",
                    message=f"LLM output is not valid JSON: {exc}",
                )
            ],
        )
        if strict:
            raise BoundaryRejection(report) from exc
        return report

    try:
        extraction = CIMExtraction.model_validate(payload)
    except ValidationError as exc:
        report = AssuranceReport(
            accepted=False,
            raw_input_sha256=raw_hash,
            findings=[
                Finding(
                    code="SCHEMA_VIOLATION",
                    severity=Severity.ERROR,
                    field_path=".".join(str(p) for p in err["loc"]),
                    message=err["msg"],
                    observed=err.get("input"),
                )
                for err in exc.errors()
            ],
        )
        if strict:
            raise BoundaryRejection(report) from exc
        return report

    # -- Stage 2: provenance ----------------------------------------------
    for field_name in ("revenue", "ebitda_margin", "revenue_growth_rate", "tax_rate"):
        ev: ExtractedValue = getattr(extraction, field_name)
        if ev.provenance.quote is None:
            findings.append(
                Finding(
                    code="MISSING_SUPPORTING_QUOTE",
                    severity=Severity.WARNING,
                    field_path=f"{field_name}.provenance.quote",
                    message="No verbatim quote; this value cannot be spot-audited without "
                    "reopening the source document",
                )
            )
        conf = ev.provenance.confidence
        if conf is not None and Decimal(str(conf)) < POLICY["min_confidence"]:
            findings.append(
                Finding(
                    code="LOW_EXTRACTION_CONFIDENCE",
                    severity=Severity.WARNING,
                    field_path=f"{field_name}.provenance.confidence",
                    message="Model reported low confidence; verify against the source",
                    observed=conf,
                    expected=f">= {POLICY['min_confidence']}",
                )
            )

    if extraction.unresolved_items:
        findings.append(
            Finding(
                code="UNRESOLVED_EXTRACTION_ITEMS",
                severity=Severity.WARNING,
                field_path="unresolved_items",
                message=f"Extraction left {len(extraction.unresolved_items)} item(s) "
                f"unresolved: {'; '.join(extraction.unresolved_items[:3])}",
                observed=extraction.unresolved_items,
            )
        )

    # -- Stage 3: plausibility bands ---------------------------------------
    _band_check("ebitda_margin", extraction.ebitda_margin.value, "ebitda_margin_typical",
                "ebitda_margin.value", findings)
    _band_check("growth_rate", extraction.revenue_growth_rate.value, "growth_rate_typical",
                "revenue_growth_rate.value", findings)
    _band_check("tax_rate", extraction.tax_rate.value, "tax_rate_typical",
                "tax_rate.value", findings)
    _band_check("wacc", wacc, "wacc_typical", "wacc", findings)
    _band_check("terminal_growth", terminal_growth, "terminal_growth_typical",
                "terminal_growth", findings)

    if extraction.revenue.value < POLICY["revenue_floor"]:
        findings.append(
            Finding(
                code="REVENUE_BELOW_FLOOR",
                severity=Severity.WARNING,
                field_path="revenue.value",
                message="Revenue below the mandate floor — may be a units error "
                "(thousands read as dollars) rather than a genuinely small target",
                observed=str(extraction.revenue.value),
                expected=f">= {POLICY['revenue_floor']}",
            )
        )

    # -- Stage 4: structural coherence -------------------------------------
    spread = wacc - terminal_growth
    if spread <= 0:
        findings.append(
            Finding(
                code="WACC_BELOW_TERMINAL_GROWTH",
                severity=Severity.ERROR,
                field_path="wacc",
                message="wacc must exceed terminal_growth; otherwise the Gordon Growth "
                "denominator is non-positive and terminal value is meaningless",
                observed=f"wacc={wacc}, g={terminal_growth}",
                expected="wacc > terminal_growth",
            )
        )
    elif spread < POLICY["min_wacc_terminal_spread"]:
        findings.append(
            Finding(
                code="NARROW_WACC_TERMINAL_SPREAD",
                severity=Severity.WARNING,
                field_path="wacc",
                message=f"Spread of {spread} is narrow; terminal value dominates the "
                "valuation and becomes hypersensitive to small assumption changes",
                observed=str(spread),
                expected=f">= {POLICY['min_wacc_terminal_spread']}",
            )
        )

    # -- Stage 5: build engine inputs --------------------------------------
    try:
        dcf = DCFAssumptions(
            initial_revenue=extraction.revenue.value,
            growth_rate=extraction.revenue_growth_rate.value,
            ebitda_margin=extraction.ebitda_margin.value,
            tax_rate=extraction.tax_rate.value,
            wacc=wacc,
            terminal_growth=terminal_growth,
            years=projection_years,
        )
        lbo = LBOAssumptions(**lbo_params) if lbo_params else None
    except ValidationError as exc:
        findings.extend(
            Finding(
                code="ENGINE_INPUT_VIOLATION",
                severity=Severity.ERROR,
                field_path=".".join(str(p) for p in err["loc"]),
                message=err["msg"],
                observed=err.get("input"),
            )
            for err in exc.errors()
        )
        report = AssuranceReport(accepted=False, findings=findings, raw_input_sha256=raw_hash)
        if strict:
            raise BoundaryRejection(report) from exc
        return report

    blocking = [f for f in findings if f.severity is Severity.ERROR]
    if blocking:
        report = AssuranceReport(accepted=False, findings=findings, raw_input_sha256=raw_hash)
        if strict:
            raise BoundaryRejection(report)
        return report

    validated = ValidatedModelInputs(
        dcf=dcf,
        lbo=lbo,
        source_extraction=extraction,
        findings=findings,
        input_hash=_sha256_of(dcf.model_dump(mode="json")),
    )
    return AssuranceReport(
        accepted=True,
        findings=findings,
        validated_inputs=validated,
        raw_input_sha256=raw_hash,
    )
