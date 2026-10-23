#!/usr/bin/env python3
"""
Model-validation checks for the Monte Carlo kernel.

These are deliberately different from the tests already in the crate. The crate's
tests check the *output*: that the mean is finite, that percentiles are ordered,
that the distribution looks roughly lognormal. All of those pass. These checks
compare the implementation against the specification it claims to implement, and
two of them fail.

Why a Python transcription rather than instrumenting the Rust:
`simulate_single_dcf` returns a single f64 and exposes none of its internal state,
so the per-year revenue path and the sampled discount rates cannot be observed
from outside. `_transcribe_*` below reproduces the kernel arithmetic line for line
from integrations/rust/src/monte_carlo.rs. `test_transcription_is_faithful`
validates the transcription against the real kernel before anything is concluded
from it, so a wrong transcription fails loudly rather than producing a wrong
finding.

Run:
    python3 tests/test_monte_carlo_validation.py     # prints a report
    pytest tests/test_monte_carlo_validation.py -v   # as assertions
"""

from __future__ import annotations

import math
import random
import statistics as st
import sys

try:
    import pytest
except ImportError:                                            # pragma: no cover
    pytest = None

BASE_REVENUE = 50_000_000.0
REVENUE_VOL = 0.20
MARGIN_MEAN, MARGIN_STD = 0.22, 0.03
WACC_MEAN, WACC_STD = 0.10, 0.02
TERMINAL_GROWTH = 0.03
YEARS = 5
SIMS = 20_000

# Mirrors MIN_TERMINAL_SPREAD in integrations/rust/src/monte_carlo.rs and
# POLICY["min_wacc_terminal_spread"] in assurance/contracts.py.
MIN_TERMINAL_SPREAD = 0.02


# ---------------------------------------------------------------------------
# Transcription of integrations/rust/src/monte_carlo.rs::simulate_single_dcf
# ---------------------------------------------------------------------------

def _transcribe_single(rng: random.Random) -> tuple[float, list[float], list[float], float]:
    """Returns (total_pv, revenue_path, per_year_waccs, terminal_wacc).

    Mirrors the Rust line for line, including the order of draws, which matters
    because the draws share one stream.
    """
    mu = math.log(BASE_REVENUE)

    total_pv = 0.0
    revenue = BASE_REVENUE
    revenue_path: list[float] = []
    waccs: list[float] = []

    for year in range(1, YEARS + 1):
        sample = rng.lognormvariate(mu, REVENUE_VOL)
        growth_shock = sample / revenue - 1.0          # monte_carlo.rs:75
        revenue = revenue * (1.0 + growth_shock)       # monte_carlo.rs:76
        revenue_path.append(revenue)

        margin = min(max(rng.normalvariate(MARGIN_MEAN, MARGIN_STD), 0.0), 1.0)
        wacc = max(rng.normalvariate(WACC_MEAN, WACC_STD), 0.01)
        waccs.append(wacc)

        ebitda = revenue * margin
        fcf = ebitda * 0.6
        total_pv += fcf / (1.0 + wacc) ** year

    final_fcf = revenue * MARGIN_MEAN * 0.6
    sampled_terminal = max(rng.normalvariate(WACC_MEAN, WACC_STD), 0.01)
    # Mirror of MIN_TERMINAL_SPREAD in monte_carlo.rs. Without this floor the
    # Gordon Growth denominator can approach zero or cross it.
    wacc_terminal = max(sampled_terminal, TERMINAL_GROWTH + MIN_TERMINAL_SPREAD)
    terminal_value = final_fcf * (1.0 + TERMINAL_GROWTH) / (wacc_terminal - TERMINAL_GROWTH)
    total_pv += terminal_value / (1.0 + wacc_terminal) ** YEARS

    return total_pv, revenue_path, waccs, wacc_terminal


def _transcribe_batch(n: int, seed: int = 20260910):
    rng = random.Random(seed)
    return [_transcribe_single(rng) for _ in range(n)]


# ---------------------------------------------------------------------------

def _kernel_batch(n: int) -> dict:
    import pe_finance
    import json
    return json.loads(pe_finance.py_monte_carlo(
        BASE_REVENUE, REVENUE_VOL, MARGIN_MEAN, MARGIN_STD,
        WACC_MEAN, WACC_STD, TERMINAL_GROWTH, YEARS, n))


def _gate_transcription() -> tuple[float, float, float]:
    """Gate: the transcription must reproduce the kernel's output distribution
    before any conclusion is drawn from its internals.

    Compared on the MEDIAN, not the mean. The kernel's terminal value divides by
    (wacc_terminal - terminal_growth) with no guard, and wacc_terminal is a normal
    draw, so a small fraction of paths land near the singularity and dominate the
    average. Measured over 8 independent 20,000-path runs of the real kernel, its
    own mean moves 2.9% run to run while its median moves 0.51%. A mean-based gate
    therefore measures sampling noise rather than transcription fidelity; this was
    found by writing that gate first and watching it fail on a correct
    transcription.
    """
    kernel = _kernel_batch(SIMS)
    mine = sorted(r[0] for r in _transcribe_batch(SIMS))

    k_med, m_med = kernel["median"], st.median(mine)
    rel = abs(k_med - m_med) / k_med
    assert rel < 0.02, (
        f"transcription does not match the kernel: kernel median {k_med:,.0f} vs "
        f"transcription {m_med:,.0f} ({rel:.1%}). Fix the transcription before "
        f"trusting anything below."
    )
    return k_med, m_med, rel


def test_transcription_is_faithful():
    _gate_transcription()


_XFAIL = {
    "test_volatility_accumulates_over_projection":
        "monte_carlo.rs:75-76 reduces to revenue = sample, so there is no revenue process",
    "test_terminal_rate_matches_final_period_rate":
        "monte_carlo.rs:92 draws an independent terminal WACC",
    "test_run_is_reproducible_under_a_fixed_seed":
        "thread_rng() is constructed per simulation and no seed parameter is exposed",
}


def _mark(fn):
    """Record these as expected failures with strict=True: the suite stays green
    while the defects are documented, and if the kernel is ever fixed the test
    turns XPASS and fails, forcing this file to be updated with it."""
    if pytest is None:
        return fn
    return pytest.mark.xfail(reason=_XFAIL[fn.__name__], strict=True)(fn)


# Expected range of `runs` draws from a normal distribution, in units of the
# standard deviation. For 6 draws E[range] ~ 3.08*sigma. Used to turn "is the
# mean stable?" into a question with a defensible answer instead of a round
# number. Values from the standard tables of the expected range statistic.
_EXPECTED_RANGE_IN_SD = {2: 1.13, 3: 1.69, 4: 2.06, 5: 2.33, 6: 3.08, 8: 2.85, 10: 3.08}

# How much wider than theory the observed range may be before the estimator is
# judged not to be behaving like a Monte Carlo estimator. The expected range is
# itself a random variable, so some headroom is required. Note that this bound does
# NOT discriminate the pre-clamp kernel, which sits at 1.2x -- see the docstring of
# test_point_estimate_is_stable for why that is, and which checks do.
_RANGE_TOLERANCE = 2.0


def test_point_estimate_is_stable(runs: int = 6):
    """CHECK 4 — run-to-run variation in the reported mean must be consistent with
    the estimator's own standard error.

    IMPORTANT, and the reason this docstring is long: **this check does not detect
    the terminal-denominator defect.** It was written believing it would, and
    measurement said otherwise. Keeping the reasoning here because the mistake is
    instructive.

    Deriving the expected range from the sample's own standard deviation is
    self-defeating against a heavy tail: the tail inflates `sd`, which inflates
    `SE`, which inflates the expected range by the same factor as the observed
    range. Measured like-for-like over 6 runs of 20,000 paths:

        before the clamp   observed 3.90%   expected 3.13%   ratio 1.2x   PASSES
        after  the clamp   observed 0.87%   expected 0.89%   ratio 1.0x   passes

    An earlier note claimed a 5.7x ratio before the clamp. That was wrong -- it
    compared the pre-clamp observed range against the *post-clamp* theoretical SE,
    which is not a like-for-like comparison.

    So what this check is actually worth: it confirms the estimator is internally
    consistent, and it would catch a genuinely broken RNG or a mean computed over
    the wrong sample size. It is not a tail detector. The tail detectors are
    `test_no_path_returns_a_negative_valuation` and
    `test_dispersion_is_not_tail_dominated` below.

    It is retained rather than deleted because an arbitrary-threshold version of
    this check previously asserted `spread < 0.5%`, which would have failed the
    correctly clamped kernel at 0.87%. A check compared against theory rather than
    a round number at least does not manufacture false findings.
    """
    batches = [_kernel_batch(SIMS) for _ in range(runs)]
    means = [b["mean"] for b in batches]
    observed_range = (max(means) - min(means)) / st.mean(means)

    sd_rel = st.mean(b["std_dev"] for b in batches) / st.mean(means)
    se_rel = sd_rel / math.sqrt(SIMS)
    expected_range = _EXPECTED_RANGE_IN_SD.get(runs, 3.08) * se_rel
    limit = expected_range * _RANGE_TOLERANCE

    ratio = observed_range / expected_range if expected_range else float("inf")
    assert observed_range <= limit, (
        f"the reported mean varies more than its own standard error allows: "
        f"{runs} identical runs of {SIMS:,} paths span {observed_range:.2%}, "
        f"against an expected range of {expected_range:.2%} "
        f"({ratio:.1f}x theory, limit {_RANGE_TOLERANCE:.0f}x)"
    )


def test_dispersion_is_not_tail_dominated():
    """CHECK 6 — the standard deviation of a strictly positive quantity must not
    exceed its mean.

    This is the check that does detect the unguarded terminal denominator, and the
    bound is principled rather than tuned: enterprise value is non-negative, so a
    coefficient of variation above 1.0 means the standard deviation is being set by
    a small number of extreme paths rather than by the modelled uncertainty.

    Measured, mean of 3 runs of 20,000 paths:

        before the clamp   cv = 2.17     sd is more than twice the mean
        after  the clamp   cv = 0.41

    Note that `mean/median` does NOT separate the two cases -- 1.110 before against
    1.111 after -- so skew is not a usable detector here. The dispersion ratio is.
    """
    k = _kernel_batch(SIMS)
    cv = k["std_dev"] / k["mean"]
    assert cv < 1.0, (
        f"dispersion is tail-dominated: sd/mean = {cv:.2f} on a strictly positive "
        f"quantity (sd {k['std_dev']:,.0f} against mean {k['mean']:,.0f}). A small "
        f"number of paths near the Gordon Growth singularity is setting the "
        f"standard deviation"
    )


def test_no_path_returns_a_negative_valuation():
    """CHECK 0b — no simulated path may return a negative enterprise value.

    This one is an OUTPUT-level check, and it is included precisely because it
    catches the unguarded terminal denominator. That matters for how the finding
    is described: it is not true that output checks cannot find these defects, only
    that the output checks this suite happened to contain did not. `mean is finite
    and positive` passes while individual paths are negative, because the mean is
    dominated by the positive tail.

    Measured before the clamp: 40 negative valuations per 120,000 paths, from
    `wacc_terminal` landing below `terminal_growth` and flipping the sign of the
    Gordon Growth denominator. After the clamp: zero.

    The kernel returns only summary statistics, so the 5th percentile is the
    lowest directly observable point; the transcription is used to inspect every
    path.
    """
    kernel = _kernel_batch(SIMS)
    assert kernel["percentile_5"] > 0, (
        f"5th percentile is negative ({kernel['percentile_5']:,.0f}); at least 5% "
        f"of paths returned a negative enterprise value"
    )

    negatives = [v for v, *_ in _transcribe_batch(SIMS) if v < 0]
    assert not negatives, (
        f"{len(negatives)} of {SIMS:,} paths returned a negative enterprise value "
        f"(worst {min(negatives):,.0f}). The Gordon Growth denominator "
        f"(wacc_terminal - g) went negative and the sign flip is silent"
    )


@_mark
def test_volatility_accumulates_over_projection():
    """CHECK 1 — recover sigma from the simulated paths.

    A projection carrying revenue volatility forward should show uncertainty
    accumulating: for a lognormal random walk the log standard deviation of
    year-N revenue grows as sigma*sqrt(N).

    EXPECTED TO FAIL. `revenue = revenue * (1 + (sample/revenue - 1))` reduces
    algebraically to `revenue = sample`, so every year is an independent draw
    around base_revenue. Year 5 has the same dispersion as year 1 and there is
    no revenue process at all.
    """
    batch = _transcribe_batch(SIMS)
    y1 = [r[1][0] for r in batch]
    yN = [r[1][-1] for r in batch]

    sd1 = st.stdev([math.log(v) for v in y1])
    sdN = st.stdev([math.log(v) for v in yN])
    expected_sdN = REVENUE_VOL * math.sqrt(YEARS)

    assert abs(sdN - expected_sdN) < 0.02 * expected_sdN, (
        f"volatility does not accumulate across the projection: year-1 log-sd "
        f"{sd1:.4f}, year-{YEARS} log-sd {sdN:.4f}, expected ~{expected_sdN:.4f} "
        f"(sigma*sqrt({YEARS})). Year {YEARS} carries the same uncertainty as "
        f"year 1, so the projection has no revenue process."
    )


@_mark
def test_terminal_rate_matches_final_period_rate():
    """CHECK 2 — the discount rate applied to terminal value should belong to the
    same scenario as the cash flows it terminates.

    EXPECTED TO FAIL. `wacc_terminal` is a fresh independent draw
    (monte_carlo.rs:92), uncorrelated with the per-year rates, and terminal value
    dominates the valuation.
    """
    batch = _transcribe_batch(SIMS)
    final_period = [r[2][-1] for r in batch]
    terminal = [r[3] for r in batch]

    corr = st.correlation(final_period, terminal)
    assert corr > 0.95, (
        f"terminal discount rate is independent of the path it terminates: "
        f"corr(final-period WACC, terminal WACC) = {corr:+.4f}, expected ~1.0. "
        f"The dominant term in the valuation is drawn from a different scenario "
        f"than the cash flows."
    )


@_mark
def test_run_is_reproducible_under_a_fixed_seed():
    """CHECK 3 — two runs with identical inputs should produce identical output.

    EXPECTED TO FAIL. `thread_rng()` is constructed inside the per-simulation
    function and there is no seed parameter anywhere in the public surface, so
    the kernel cannot be pinned for audit or regression.
    """
    a = _kernel_batch(2_000)
    b = _kernel_batch(2_000)
    assert a["mean"] == b["mean"], (
        f"kernel is not reproducible: two identical calls returned means "
        f"{a['mean']:,.4f} and {b['mean']:,.4f}. There is no seed parameter on "
        f"py_monte_carlo, so a result cannot be pinned for audit."
    )


CHECKS = [
    ("1. volatility accumulates over the projection", test_volatility_accumulates_over_projection),
    ("2. terminal rate matches the final-period rate", test_terminal_rate_matches_final_period_rate),
    ("3. run is reproducible under a fixed seed", test_run_is_reproducible_under_a_fixed_seed),
    ("4. reported mean is stable within its standard error", test_point_estimate_is_stable),
    ("5. no path returns a negative valuation", test_no_path_returns_a_negative_valuation),
    ("6. dispersion is not tail-dominated", test_dispersion_is_not_tail_dominated),
]

# Checks 5 and 6 are the ones that actually detect the unguarded terminal
# denominator: they failed before that guard and pass now. Check 4 passes in both
# states -- see its docstring for why it is not a tail detector despite looking
# like one.
FIXED_BY_TERMINAL_CLAMP = {
    "5. no path returns a negative valuation",
    "6. dispersion is not tail-dominated",
}


def _output_level_checks() -> list[tuple[str, bool, str]]:
    """The checks that do pass, shown for contrast."""
    k = _kernel_batch(SIMS)
    p5, p25, p50 = k["percentile_5"], k["percentile_25"], k["median"]
    p75, p95 = k["percentile_75"], k["percentile_95"]
    ordered = p5 <= p25 <= p50 <= p75 <= p95
    return [
        ("mean is finite and positive", math.isfinite(k["mean"]) and k["mean"] > 0,
         f"mean = {k['mean']:,.0f}"),
        ("percentiles are ordered", ordered,
         f"p5 {p5:,.0f} <= p25 {p25:,.0f} <= p50 {p50:,.0f} <= p95 {p95:,.0f}"),
        ("std dev is positive", k["std_dev"] > 0, f"sd = {k['std_dev']:,.0f}"),
        ("all paths finite", math.isfinite(k["percentile_95"]),
         "no inf/nan in the reported distribution"),
    ]


def main() -> int:
    print("=" * 78)
    print("MONTE CARLO MODEL-VALIDATION CHECKS")
    print("=" * 78)

    try:
        k_mean, m_mean, rel = _gate_transcription()
    except AssertionError as e:
        print(f"\nGATE FAILED: {e}")
        return 1
    print(f"\nGate — transcription is faithful to the kernel:")
    print(f"  kernel median        {k_mean:>18,.0f}")
    print(f"  transcription median {m_mean:>18,.0f}   ({rel:.2%} apart on {SIMS:,} paths)")
    print("  -> internals measured below can be trusted")

    print(f"\nOutput-level checks (the kind most numerical suites contain):")
    for name, ok, detail in _output_level_checks():
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<34} {detail}")

    print(f"\nChecks against the specification:")
    failures = 0
    for label, fn in CHECKS:
        tag = "  [terminal clamp]" if label in FIXED_BY_TERMINAL_CLAMP else ""
        try:
            fn()
            print(f"  PASS  {label}{tag}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL  {label}{tag}")
            for line in str(e).replace("  ", " ").split(". "):
                if line.strip():
                    print(f"          {line.strip().rstrip('.')}.")

    fixed = len(FIXED_BY_TERMINAL_CLAMP)
    print(f"\n{failures} of {len(CHECKS)} checks against the specification fail.")
    print(f"The {fixed} marked [terminal clamp] were failing before that guard was")
    print("added and pass now. The rest remain open defects: there is no revenue")
    print("growth process and no seed. See CLAIMS.md 6.7.")
    print()
    print("Note on the output-level checks above: one of them (no negative")
    print("valuation) DOES catch the terminal-denominator defect. The honest claim")
    print("is not that output checks cannot find these problems, but that the")
    print("output checks this suite happened to contain did not.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
