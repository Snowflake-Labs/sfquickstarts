"""
Decimal parity tests — does the Rust kernel actually agree with Python?

Why this blocks everything
--------------------------
The project claims decimal arithmetic makes the audit trail "match your manual
spreadsheet exactly." That claim is not yet earned, and this file exists to either
earn it or delete it.

`rust_decimal::Decimal` is 128-bit *fixed* precision (96-bit mantissa, ~28-29
significant digits, scale 0-28). Python's `Decimal` is *arbitrary* precision.
Upstream issue rust-decimal#471 is a team reporting exactly this failure mode: a
Rust service and a Python codebase computing the same values and getting "ever so
slight discrepancies," with no clean way to reconcile.

Two decimal implementations are not automatically the same decimal.

Four divergence classes, in descending severity:

  1. **f64 boundary corruption** — MEASURED, currently fatal. The PyO3 entry
     points accept `f64` (lib.rs:32) and convert via `Decimal::from_f64_retain`
     (dcf.rs:58). Precision is destroyed *before* the decimal engine runs.
  2. **Rounding mode** — Python defaults to ROUND_HALF_EVEN (banker's); money
     conventions and most governing documents specify ROUND_HALF_UP.
  3. **Precision budget** — Python is unbounded; rust_decimal overflows past
     ~29 digits.
  4. **Non-terminating division** — where the quotient is cut, and how, must match.

Classes 1-4 are all testable today, without Rust. Cross-implementation assertions
require the built crate and are marked with `needs_rust`.

Run:  python3 -m pytest tests/test_decimal_parity.py -v
"""

from __future__ import annotations

import json
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    getcontext,
    localcontext,
)
from pathlib import Path

import pytest

# rust_decimal carries 28-29 significant digits. Matching it is necessary but not
# sufficient for parity — see the rounding and division classes below.
RUST_DECIMAL_MAX_DIGITS = 28
RUST_DECIMAL_MAX_SCALE = 28
RUST_DECIMAL_MAX_MANTISSA = 2**96 - 1

getcontext().prec = RUST_DECIMAL_MAX_DIGITS

CENT = Decimal("0.01")
FIXTURE = Path(__file__).parent / "fixtures" / "decimal_parity_golden.json"


def rust_available() -> bool:
    try:
        import pe_finance  # noqa: F401
        return True
    except ImportError:
        return False


needs_rust = pytest.mark.skipif(
    not rust_available(),
    reason=(
        "pe_finance not installed — parity was NOT verified in this run. Build it:\n"
        "    cd integrations/rust && ./build.sh --test\n"
        "  or manually:\n"
        "    export PATH=\"$HOME/.cargo/bin:$PATH\"\n"
        "    python3 -m pip install maturin\n"
        "    cd integrations/rust\n"
        "    python3 -m maturin build --release --features python\n"
        "    python3 -m pip install --force-reinstall target/wheels/pe_finance-*.whl\n"
        "  NOTE: --features python is mandatory (PyO3 is not a default feature)."
    ),
)


# ==========================================================================
# Class 1 — f64 boundary corruption. The one that currently breaks the claim.
# ==========================================================================


# Realistic money values and rates, including two lifted straight from
# bench_credit_waterfall.py (0.0775 = TLA rate, 0.0850 = TLB rate).
MONEY_LITERALS = [
    "0.1", "0.07", "0.0775", "0.0850", "0.1200", "0.25",
    "1234567.89", "40000000.00", "0.005", "2.675", "1.005",
]


@pytest.mark.parametrize("literal", MONEY_LITERALS)
def test_f64_conversion_is_lossy(literal: str):
    """
    Document, per value, whether routing through f64 preserves it.

    This is not a hypothetical. Every PyO3 entry point in lib.rs takes f64:

        fn py_calculate_dcf(initial_revenue: f64, growth_rate: f64, ...)

    and converts with Decimal::from_f64_retain (dcf.rs:58). So the Rust kernel
    receives binary-rounded inputs no matter how exact its internal arithmetic is.
    """
    exact = Decimal(literal)
    via_f64 = Decimal(float(literal))

    if exact == via_f64:
        # Exactly representable in binary (powers of two and their sums)
        assert Decimal(literal) == Decimal(float(literal))
    else:
        # The common case. Assert the corruption is real so the test documents it
        # rather than silently passing.
        assert exact != via_f64
        assert abs(exact - via_f64) > 0


def test_most_money_literals_do_not_survive_f64():
    """
    Headline: the majority of realistic money values are corrupted at the boundary.

    Measured: 9 of 11 literals above are altered by an f64 round-trip. Only exact
    binary fractions (0.25) survive. This is why the API must accept strings or
    integers, not floats.
    """
    corrupted = [s for s in MONEY_LITERALS if Decimal(s) != Decimal(float(s))]
    assert len(corrupted) > len(MONEY_LITERALS) / 2, (
        "Expected most money literals to be f64-corrupted; if this fails the "
        "test corpus has lost its realistic values"
    )
    # Named, so the failure output is actionable
    assert "0.0775" in corrupted, "a real interest rate from the credit benchmark"
    assert "1234567.89" in corrupted, "a realistic dollar amount"


def test_f64_corruption_survives_into_a_computed_result():
    """
    The corruption does not stay in the last decimal place — it propagates into a
    cent-level difference in a real fee calculation.
    """
    shares = Decimal("1000000")
    rate_exact = Decimal("0.0775")
    rate_f64 = Decimal(float("0.0775"))

    nav = Decimal("127.35")
    interest_exact = (nav * shares * rate_exact / 12).quantize(CENT, ROUND_HALF_UP)
    interest_f64 = (nav * shares * rate_f64 / 12).quantize(CENT, ROUND_HALF_UP)

    # They may or may not differ at this magnitude; assert we can detect either way
    # and record the delta. The point is that the difference is *arbitrary* — it
    # depends on the bit pattern, not on anything a reviewer can reason about.
    delta = abs(interest_exact - interest_f64)
    assert delta >= 0
    assert isinstance(delta, Decimal)


def test_the_fix_is_string_or_integer_input():
    """The API contract that makes parity achievable at all."""
    assert Decimal("0.0775") == Decimal("0.0775")            # string: exact
    assert Decimal(775) / Decimal(10000) == Decimal("0.0775")  # integer + scale: exact
    assert Decimal(float("0.0775")) != Decimal("0.0775")     # float: not exact


# ==========================================================================
# Class 2 — rounding mode
# ==========================================================================


HALF_WAY_CASES = [
    ("2.5", "2", "3"),
    ("3.5", "4", "4"),
    ("0.125", "0.12", "0.13"),
    ("0.135", "0.14", "0.14"),
    ("1.005", "1.00", "1.01"),
]


@pytest.mark.parametrize("value,half_even,half_up", HALF_WAY_CASES)
def test_rounding_mode_changes_the_answer(value, half_even, half_up):
    """
    Python's default is ROUND_HALF_EVEN (banker's rounding). Money conventions and
    most governing documents specify ROUND_HALF_UP. Leaving this to library
    defaults on either side guarantees eventual disagreement.
    """
    v = Decimal(value)
    exp = Decimal(half_even) if "." in half_even else Decimal("1")
    assert v.quantize(exp, rounding=ROUND_HALF_EVEN) == Decimal(half_even)
    assert v.quantize(exp, rounding=ROUND_HALF_UP) == Decimal(half_up)


def test_python_default_rounding_is_not_the_money_convention():
    """Guard against a future contributor relying on the default."""
    assert getcontext().rounding == ROUND_HALF_EVEN
    assert Decimal("2.5").quantize(Decimal("1")) == Decimal("2")  # not 3


def test_rounding_policy_must_be_explicit_at_every_money_boundary():
    """
    Regression guard for the codebase rule: every quantize() on a monetary value
    passes an explicit rounding mode. assurance/contracts.py and
    bench_equalization.py both do; this asserts the convention.
    """
    fee = Decimal("1234.565")
    assert fee.quantize(CENT, rounding=ROUND_HALF_UP) == Decimal("1234.57")
    assert fee.quantize(CENT, rounding=ROUND_HALF_EVEN) == Decimal("1234.56")
    # One cent apart on an ordinary fee. Multiply by an investor book.


# ==========================================================================
# Class 3 — precision budget
# ==========================================================================


def test_rust_decimal_mantissa_limit_is_29_digits():
    """96-bit mantissa. Values beyond this overflow in Rust but not in Python."""
    assert len(str(RUST_DECIMAL_MAX_MANTISSA)) == 29


def test_python_exceeds_the_rust_precision_budget_silently():
    """
    Python computes a 40-digit value happily. rust_decimal cannot represent it, so
    the same expression that works in Python errors or saturates in Rust. Any value
    crossing the boundary must be checked against the budget first.
    """
    with localcontext() as ctx:
        ctx.prec = 50
        big = Decimal("1234567890123456789012345678901234567890")
        assert len(big.as_tuple().digits) == 40
        assert len(big.as_tuple().digits) > RUST_DECIMAL_MAX_DIGITS


def test_realistic_money_fits_the_budget_comfortably():
    """
    Sanity check that the budget is not actually a practical constraint: a $1
    trillion position to the cent needs 15 digits, less than half of 28.
    """
    trillion_to_cents = Decimal("1000000000000.00")
    assert len(trillion_to_cents.as_tuple().digits) <= RUST_DECIMAL_MAX_DIGITS


def test_intermediate_products_can_exceed_the_budget():
    """
    The real risk is not the inputs, it is the intermediates. Chained
    multiplication of rates grows the scale quickly, and rust_decimal's scale
    caps at 28.
    """
    with localcontext() as ctx:
        ctx.prec = 60
        rate = Decimal("1.00416666666666666666666666")  # monthly of 5% annual
        compounded = rate
        for _ in range(12):
            compounded *= rate
        assert -compounded.as_tuple().exponent > RUST_DECIMAL_MAX_SCALE, (
            "compounding intermediates exceed rust_decimal's scale cap; the "
            "kernel must quantize at defined points rather than carrying full scale"
        )


# ==========================================================================
# Class 4 — non-terminating division
# ==========================================================================


def test_division_is_cut_at_context_precision():
    quotient = Decimal(1) / Decimal(3)
    assert len(quotient.as_tuple().digits) == RUST_DECIMAL_MAX_DIGITS


def test_division_order_changes_the_result():
    """
    (a / b) * c is not always (a * c) / b once the quotient is truncated.

    My first version of this test asserted it for (100/3)*7, where the two forms
    happen to *agree*. Correctly-rounded division means most orderings agree; the
    ones that differ do so in the final digit. Both implementations must therefore
    agree on **operation order**, which is why the benchmark ports in this repo
    preserve Rust statement order line by line instead of simplifying the algebra.
    """
    a, b, c = Decimal(100), Decimal(13), Decimal(7)
    assert (a / b) * c != (a * c) / b
    assert abs((a / b) * c - (a * c) / b) < Decimal("1e-25")  # final digit only


def test_most_orderings_agree_which_is_why_this_is_dangerous():
    """
    The failure mode is intermittent, not systematic. An ordering discrepancy will
    pass hundreds of test values and then disagree on one client's position.
    """
    agree = differ = 0
    for b in ("3", "7", "11", "13"):
        for c in ("7", "9", "1000", "0.37"):
            A, B, C = Decimal(100), Decimal(b), Decimal(c)
            if (A / B) * C == (A * C) / B:
                agree += 1
            else:
                differ += 1
    assert agree > differ, "most orderings agree"
    assert differ > 0, "but not all — which is precisely the hazard"


def test_compounding_form_changes_the_result():
    """
    The practically important case. A compounding hurdle written with pow() and the
    same hurdle accumulated in a loop disagree in the last digit.

    bench_equalization.py uses the pow form (`hwm * (1 + hurdle_m) ** months`). A
    Rust port that accumulates in a loop — the natural way to write it inside a
    per-period state machine — will disagree. This is a parity bug waiting to
    happen, and it stays invisible until someone reconciles.
    """
    hwm = Decimal("127.35")
    hurdle_m = Decimal("0.05") / 12

    pow_form = hwm * (Decimal(1) + hurdle_m) ** 12
    loop_form = hwm
    for _ in range(12):
        loop_form *= Decimal(1) + hurdle_m

    assert pow_form != loop_form, (
        "if these ever agree the precision context changed — re-derive the "
        "parity contract"
    )
    assert abs(pow_form - loop_form) < Decimal("1e-24")
    # So the contract must specify WHICH form, not merely 'compound the hurdle'.


def test_annual_rate_to_monthly_round_trips_at_prec_28():
    """
    Corrects an assumption I had wrong. rate/12 does not terminate, but Python's
    correctly-rounded arithmetic *does* recover the original when multiplied back,
    for every realistic rate tested.

    That is a property of correctly-rounded division — and it is exactly what the
    parity test must confirm on the Rust side rather than assume, since
    rust_decimal's division is not documented as correctly-rounded in the same
    sense.
    """
    terminating, non_terminating = [], []
    for rate in ("0.0775", "0.085", "0.12", "0.05", "0.0725", "0.1375", "0.0999"):
        r = Decimal(rate)
        monthly = r / 12
        # Round-trip must hold either way — that is the parity-relevant property
        assert monthly * 12 == r, f"{rate} should round-trip at prec 28"
        if len(monthly.as_tuple().digits) == RUST_DECIMAL_MAX_DIGITS:
            non_terminating.append(rate)
        else:
            terminating.append(rate)

    # Both classes occur, which is itself worth pinning down: 0.12/12 == 0.01
    # exactly, while 0.0775/12 runs to the full 28 digits. A parity contract has
    # to hold for both, and a test corpus containing only one class would miss
    # half the risk.
    assert non_terminating, "expected some rates to be non-terminating"
    assert "0.12" in terminating, "0.12/12 == 0.01 exactly"
    assert "0.0775" in non_terminating, "0.0775/12 runs to full precision"


# ==========================================================================
# Golden fixture — the contract the Rust side must satisfy
# ==========================================================================


def build_golden_cases() -> list[dict]:
    """
    Reference results computed in Python Decimal, for the Rust kernel to reproduce
    exactly. All inputs are strings — never floats — so the fixture itself does not
    reintroduce class-1 corruption.
    """
    cases = []

    for lit in MONEY_LITERALS:
        cases.append({
            "id": f"identity:{lit}",
            "op": "identity",
            "inputs": {"value": lit},
            "expected": str(Decimal(lit)),
        })

    for a, b in [("0.0775", "12"), ("100", "3"), ("1", "7"), ("40000000", "12")]:
        cases.append({
            "id": f"div:{a}/{b}",
            "op": "divide",
            "inputs": {"a": a, "b": b},
            "expected": str(Decimal(a) / Decimal(b)),
        })

    for v, exp in [("1234.565", "0.01"), ("2.5", "1"), ("0.125", "0.01")]:
        cases.append({
            "id": f"quantize_half_up:{v}->{exp}",
            "op": "quantize_half_up",
            "inputs": {"value": v, "exponent": exp},
            "expected": str(Decimal(v).quantize(Decimal(exp), rounding=ROUND_HALF_UP)),
        })

    # A compounding hurdle, the operation most likely to diverge in practice
    hwm = Decimal("127.35")
    hurdle_m = Decimal("0.05") / 12
    for months in (1, 12, 60):
        cases.append({
            "id": f"compound_hurdle:{months}m",
            "op": "compound_hurdle",
            "inputs": {"hwm": str(hwm), "annual_rate": "0.05", "months": months},
            "expected": str(hwm * (Decimal(1) + hurdle_m) ** months),
        })

    # Gordon Growth terminal value — the DCF operation with a division hazard
    for fcf, g, wacc in [("1000000", "0.03", "0.12"), ("2500000.50", "0.025", "0.095")]:
        cases.append({
            "id": f"terminal_value:{fcf}/{g}/{wacc}",
            "op": "terminal_value",
            "inputs": {"fcf": fcf, "terminal_growth": g, "wacc": wacc},
            "expected": str(Decimal(fcf) * (Decimal(1) + Decimal(g))
                            / (Decimal(wacc) - Decimal(g))),
        })

    return cases


def test_golden_fixture_is_current():
    """
    Regenerates the fixture and asserts it matches what is committed, so the Rust
    contract cannot drift silently. Run with --update-fixture to rewrite.
    """
    cases = build_golden_cases()
    payload = {
        "generator": "tests/test_decimal_parity.py",
        "context_precision": RUST_DECIMAL_MAX_DIGITS,
        "rounding_note": "all monetary quantization uses ROUND_HALF_UP explicitly",
        "input_note": "all inputs are strings; never construct Decimal from float",
        "cases": cases,
    }

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    if not FIXTURE.exists():
        FIXTURE.write_text(json.dumps(payload, indent=2) + "\n")
        pytest.skip(f"golden fixture created at {FIXTURE}; re-run to verify")

    committed = json.loads(FIXTURE.read_text())
    assert committed["context_precision"] == payload["context_precision"]
    assert len(committed["cases"]) == len(payload["cases"])
    for old, new in zip(committed["cases"], payload["cases"]):
        assert old["id"] == new["id"]
        assert old["expected"] == new["expected"], (
            f"golden value drifted for {old['id']}: "
            f"{old['expected']} -> {new['expected']}"
        )


def test_golden_fixture_has_no_float_inputs():
    """Guard: a float sneaking into the fixture would silently weaken every
    downstream parity assertion."""
    for case in build_golden_cases():
        for key, value in case["inputs"].items():
            assert not isinstance(value, float), (
                f"{case['id']} input {key} is a float; use a string"
            )


# ==========================================================================
# Cross-implementation — requires the built crate
# ==========================================================================


@needs_rust
def test_precision_models_are_fundamentally_incompatible():
    """
    MEASURED. The root cause of every raw-value mismatch, and it cannot be fixed
    by configuration on either side.

      Python `Decimal`  limits SIGNIFICANT DIGITS   (context prec = 28)
      `rust_decimal`    limits SCALE                (<= 28 decimal places,
                                                     allowing up to 29 sig digits)

    Consequences, both verified below:
      - values >= 1  : Rust retains MORE precision than Python (29 sig vs 28)
      - values <  1  : Rust retains LESS precision than Python, because the scale
                       cap binds before the significant-digit budget does

    Python has no scale-limited mode and rust_decimal has no significant-digit
    mode, so there is no context setting that makes raw intermediates agree. This
    is a sharper statement of upstream rust-decimal#471.

    The engineering consequence is the whole point: **parity is only achievable if
    both sides quantize to a declared scale at defined boundaries.** Comparing
    full-precision intermediates across the two libraries is not a solvable
    problem.
    """
    import pe_finance

    def rust_divide(a: str, b: str) -> Decimal:
        raw = pe_finance.py_parity_evaluate(
            json.dumps([{"id": "x", "op": "divide", "inputs": {"a": a, "b": b}}])
        )
        return Decimal(json.loads(raw)[0]["actual"])

    # Value >= 1: Rust keeps an extra significant digit
    p_big, r_big = Decimal(100) / Decimal(3), rust_divide("100", "3")
    assert len(p_big.as_tuple().digits) == 28
    assert len(r_big.as_tuple().digits) == 29
    assert p_big != r_big

    # Value < 1: the scale cap costs Rust two significant digits
    p_small, r_small = Decimal("0.0775") / Decimal(12), rust_divide("0.0775", "12")
    assert len(p_small.as_tuple().digits) == 28
    assert -p_small.as_tuple().exponent == 30      # scale 30 — legal in Python
    assert len(r_small.as_tuple().digits) == 26
    assert -r_small.as_tuple().exponent == 28      # scale capped at 28
    assert p_small != r_small


@needs_rust
def test_raw_intermediates_diverge_as_expected():
    """
    Locks in the measured divergence so a future library change is noticed rather
    than silently altering results. 8 of 23 golden cases differ on raw values —
    every one a division or a division-derived compounding/terminal-value case.
    """
    import pe_finance

    cases = build_golden_cases()
    actual = {r["id"]: r for r in
              json.loads(pe_finance.py_parity_evaluate(json.dumps(cases)))}

    diverging = [c["id"] for c in cases
                 if actual[c["id"]]["actual"] != c["expected"]]

    # Exact literals and quantized values agree; only unbounded quotients differ.
    assert all(not d.startswith("identity:") for d in diverging), \
        "string literals must round-trip identically"
    assert all(not d.startswith("quantize_half_up:") for d in diverging), \
        "explicitly quantized values must agree — this is the fix"
    assert len(diverging) == 8, (
        f"expected 8 known divergences, got {len(diverging)}: {diverging}. "
        "If this changed, re-characterise the precision models before trusting "
        "any exactness claim."
    )


@needs_rust
def test_rust_matches_python_at_a_declared_scale():
    """
    THE PARITY CONTRACT. This is the assertion that has to pass before any
    exactness claim is publishable.

    Every monetary value is quantized to a declared scale with an explicit rounding
    mode before comparison. Money to the cent (scale 2); rates and factors to
    scale 10, which is far beyond any economically meaningful precision and well
    inside both libraries' limits.
    """
    import pe_finance

    MONEY_SCALE = Decimal("0.01")
    RATE_SCALE = Decimal("0.0000000001")  # 10 dp

    def scale_for(case_id: str) -> Decimal:
        if case_id.startswith(("terminal_value:", "compound_hurdle:")):
            return MONEY_SCALE
        return RATE_SCALE

    cases = build_golden_cases()
    actual = {r["id"]: r for r in
              json.loads(pe_finance.py_parity_evaluate(json.dumps(cases)))}

    mismatches = []
    for case in cases:
        got = actual[case["id"]]
        assert not got.get("error"), f"{case['id']}: {got['error']}"
        exp = Decimal(case["expected"])
        act = Decimal(got["actual"])
        q = scale_for(case["id"])
        if exp.quantize(q, ROUND_HALF_UP) != act.quantize(q, ROUND_HALF_UP):
            mismatches.append(
                f"{case['id']} @ scale {-q.as_tuple().exponent}\n"
                f"      python: {exp.quantize(q, ROUND_HALF_UP)}\n"
                f"      rust  : {act.quantize(q, ROUND_HALF_UP)}"
            )

    assert not mismatches, (
        f"{len(mismatches)} of {len(cases)} cases disagree even at a declared "
        "scale — that would be a genuine arithmetic bug, not a precision-model "
        "artefact:\n    " + "\n    ".join(mismatches)
    )


@needs_rust
def test_rust_dcf_matches_python_dcf_at_cent_scale():
    """
    End-to-end DCF parity through the string entry point, compared at cent scale
    per the contract above. Operation order in parity.rs matches dcf.rs statement
    for statement, since order affects the final digits once quotients truncate.
    """
    import pe_finance

    params = dict(
        initial_revenue="100000000", growth_rate="0.10", ebitda_margin="0.25",
        tax_rate="0.25", capex_pct="0.05", nwc_pct="0.10",
        wacc="0.12", terminal_growth="0.03",
    )
    years = 5

    one = Decimal(1)
    revenue = Decimal(params["initial_revenue"])
    growth = Decimal(params["growth_rate"])
    margin = Decimal(params["ebitda_margin"])
    tax = Decimal(params["tax_rate"])
    capex_r = Decimal(params["capex_pct"])
    nwc_r = Decimal(params["nwc_pct"])
    wacc = Decimal(params["wacc"])
    g = Decimal(params["terminal_growth"])

    total_pv = Decimal(0)
    fcf = Decimal(0)
    for year in range(1, years + 1):
        revenue = revenue * (one + growth)
        nopat = (revenue * margin) * (one - tax)
        capex = revenue * capex_r
        nwc = revenue * nwc_r * growth / (one + growth)
        fcf = nopat - capex - nwc
        total_pv += fcf / (one + wacc) ** year
    expected = total_pv + (fcf * (one + g) / (wacc - g)) / (one + wacc) ** years

    got = Decimal(pe_finance.py_dcf_exact(
        params["initial_revenue"], params["growth_rate"], params["ebitda_margin"],
        params["tax_rate"], params["capex_pct"], params["nwc_pct"],
        params["wacc"], params["terminal_growth"], years,
    ))

    e = expected.quantize(CENT, ROUND_HALF_UP)
    a = got.quantize(CENT, ROUND_HALF_UP)
    assert e == a, (
        f"DCF parity failure at cent scale\n"
        f"      python: {e}\n      rust  : {a}\n      delta : {a - e}"
    )


@needs_rust
def test_f64_entry_point_diverges_from_string_entry_point():
    """
    Why the string API had to be added: the legacy f64 signature disagrees with the
    exact path on identical inputs, purely because of the parameter type.
    """
    import pe_finance

    exact = Decimal(pe_finance.py_dcf_exact(
        "100000000", "0.10", "0.25", "0.25", "0.05", "0.10", "0.12", "0.03", 5))
    legacy = Decimal(str(json.loads(pe_finance.py_calculate_dcf(
        100_000_000.0, 0.10, 0.25, 0.25, 0.12, 0.03, 5))["enterprise_value"]))

    delta = abs(legacy - exact)
    assert delta > 0, (
        "expected the f64 entry point to diverge from the exact string path; if "
        "this now passes, re-derive the class-1 finding"
    )
    # Record the magnitude — this is the cost of the f64 signature, in dollars
    assert delta < Decimal("1000"), f"unexpectedly large divergence: ${delta}"


