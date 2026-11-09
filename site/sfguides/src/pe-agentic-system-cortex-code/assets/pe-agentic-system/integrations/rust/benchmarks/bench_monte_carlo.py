"""
Monte Carlo DCF benchmark: naive Python vs vectorized NumPy vs Rust.

Purpose
-------
Produce a *defensible* speedup number to replace the estimated figures that were
previously hardcoded in integrations/rust/examples/python_usage.py:201-222.

Read this before quoting any number from this script:

1. The honest comparison is Rust vs **vectorized NumPy**, not Rust vs a naive
   Python loop. A naive-loop baseline inflates the speedup by roughly the
   NumPy-vs-loop factor and will not survive scrutiny from an audience that
   writes numerical code. Both baselines are reported so the difference is
   visible; quote the NumPy one.

2. All three implementations must agree numerically before any timing is
   meaningful. The script checks distributional agreement and refuses to report
   a speedup if the implementations disagree.

3. Monte Carlo is a stochastic workload, so results are reported as median of N
   repetitions with min/max, not a single run.

Usage
-----
    python3 bench_monte_carlo.py                  # baselines only
    python3 bench_monte_carlo.py --sims 100000    # larger workload
    python3 bench_monte_carlo.py --repeat 7

To include Rust, build the extension first (see benchmarks/README.md):
    cd integrations/rust && maturin develop --release --features python
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import sys
import time
from dataclasses import dataclass, asdict

import numpy as np

# --------------------------------------------------------------------------
# Workload definition — mirrors monte_carlo.rs test_monte_carlo() exactly
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MonteCarloInputs:
    base_revenue: float = 100_000_000.0
    revenue_volatility: float = 0.15
    ebitda_margin_mean: float = 0.25
    ebitda_margin_std: float = 0.05
    wacc_mean: float = 0.12
    wacc_std: float = 0.02
    terminal_growth: float = 0.03
    years: int = 5
    simulations: int = 10_000


# FCF conversion factor, hardcoded at monte_carlo.rs:83 and :91
FCF_CONVERSION = 0.6

# Minimum spread between the terminal discount rate and terminal growth.
# Mirrors MIN_TERMINAL_SPREAD in monte_carlo.rs and
# POLICY["min_wacc_terminal_spread"] in assurance/contracts.py.
MIN_TERMINAL_SPREAD = 0.02


# --------------------------------------------------------------------------
# Baseline 1: naive Python loop
#
# Deliberately a faithful line-by-line port of simulate_single_dcf()
# (monte_carlo.rs:48-99). It must compute what the Rust computes, otherwise the
# comparison is invalid -- including the parts that are still wrong.
#
# PART OF THE SPECIFICATION (mirror it):
#   - the terminal discount rate is floored at terminal_growth + MIN_TERMINAL_SPREAD.
#     Without it a sampled rate can approach the Gordon Growth singularity or
#     cross it, which produced 40 negative valuations per 120,000 paths and left
#     dispersion tail-dominated at sd/mean = 2.17.
#
# STILL DEFECTIVE, deliberately replicated until fixed in the kernel:
#   - the lognormal is anchored at ln(base_revenue) and the shock arithmetic
#     reduces to `revenue = sample`, so there is no revenue growth process at all
#     (monte_carlo.rs:75). CLAIMS.md 6.7, open item.
#   - a *separate* wacc is drawn for terminal value (monte_carlo.rs:92),
#     uncorrelated with the in-loop yearly samples. CLAIMS.md 6.7, open item.
# Do not "fix" those two here before they are fixed in the kernel.
# --------------------------------------------------------------------------


def monte_carlo_naive(inp: MonteCarloInputs, rng: np.random.Generator) -> np.ndarray:
    valuations = np.empty(inp.simulations, dtype=np.float64)
    ln_base = math.log(inp.base_revenue)

    for i in range(inp.simulations):
        total_pv = 0.0
        revenue = inp.base_revenue

        for year in range(1, inp.years + 1):
            sampled_revenue = rng.lognormal(ln_base, inp.revenue_volatility)
            growth_shock = sampled_revenue / revenue - 1.0
            revenue = revenue * (1.0 + growth_shock)

            margin = min(max(rng.normal(inp.ebitda_margin_mean, inp.ebitda_margin_std), 0.0), 1.0)
            wacc = max(rng.normal(inp.wacc_mean, inp.wacc_std), 0.01)

            fcf = revenue * margin * FCF_CONVERSION
            total_pv += fcf / (1.0 + wacc) ** year

        final_fcf = revenue * inp.ebitda_margin_mean * FCF_CONVERSION
        sampled_terminal = max(rng.normal(inp.wacc_mean, inp.wacc_std), 0.01)
        # Mirror of the kernel's terminal floor (monte_carlo.rs).
        wacc_terminal = max(sampled_terminal, inp.terminal_growth + MIN_TERMINAL_SPREAD)
        terminal_value = final_fcf * (1.0 + inp.terminal_growth) / (
            wacc_terminal - inp.terminal_growth
        )
        total_pv += terminal_value / (1.0 + wacc_terminal) ** inp.years

        valuations[i] = total_pv

    return valuations


# --------------------------------------------------------------------------
# Baseline 2: vectorized NumPy — THIS is the number to quote against
#
# Same algorithm, all simulations advanced in lockstep. The year loop remains
# (each year depends on the previous), but it runs `simulations` paths per
# iteration instead of one, so the loop executes `years` times total rather
# than `simulations * years` times.
# --------------------------------------------------------------------------


def monte_carlo_vectorized(inp: MonteCarloInputs, rng: np.random.Generator) -> np.ndarray:
    n = inp.simulations
    ln_base = math.log(inp.base_revenue)

    total_pv = np.zeros(n, dtype=np.float64)
    revenue = np.full(n, inp.base_revenue, dtype=np.float64)

    for year in range(1, inp.years + 1):
        sampled_revenue = rng.lognormal(ln_base, inp.revenue_volatility, size=n)
        growth_shock = sampled_revenue / revenue - 1.0
        revenue = revenue * (1.0 + growth_shock)

        margin = np.clip(rng.normal(inp.ebitda_margin_mean, inp.ebitda_margin_std, size=n), 0.0, 1.0)
        wacc = np.maximum(rng.normal(inp.wacc_mean, inp.wacc_std, size=n), 0.01)

        fcf = revenue * margin * FCF_CONVERSION
        total_pv += fcf / (1.0 + wacc) ** year

    final_fcf = revenue * inp.ebitda_margin_mean * FCF_CONVERSION
    sampled_terminal = np.maximum(rng.normal(inp.wacc_mean, inp.wacc_std, size=n), 0.01)
    # Mirror of the kernel's terminal floor (monte_carlo.rs).
    wacc_terminal = np.maximum(sampled_terminal, inp.terminal_growth + MIN_TERMINAL_SPREAD)
    terminal_value = final_fcf * (1.0 + inp.terminal_growth) / (wacc_terminal - inp.terminal_growth)
    total_pv += terminal_value / (1.0 + wacc_terminal) ** inp.years

    return total_pv


# --------------------------------------------------------------------------
# Candidate: Rust via PyO3
# --------------------------------------------------------------------------


def load_rust():
    """Return py_monte_carlo, or None with a reason if unavailable."""
    try:
        import pe_finance  # type: ignore
    except ImportError as exc:
        return None, f"pe_finance not importable ({exc}). Build it: see benchmarks/README.md"
    fn = getattr(pe_finance, "py_monte_carlo", None)
    if fn is None:
        return None, "pe_finance imported but py_monte_carlo is missing (built without --features python?)"
    return fn, None


def monte_carlo_rust(fn, inp: MonteCarloInputs) -> dict:
    return json.loads(
        fn(
            inp.base_revenue,
            inp.revenue_volatility,
            inp.ebitda_margin_mean,
            inp.ebitda_margin_std,
            inp.wacc_mean,
            inp.wacc_std,
            inp.terminal_growth,
            inp.years,
            inp.simulations,
        )
    )


# --------------------------------------------------------------------------
# Statistics and agreement checking
# --------------------------------------------------------------------------


def summarize(valuations: np.ndarray) -> dict:
    """Match the summary keys returned by py_monte_carlo (lib.rs:163-172).

    One key is deliberately absent: `paths_clamped`. The kernel reports how many
    paths had the terminal rate raised to its floor; the baselines apply the same
    floor but do not count it, because `agreement()` compares distribution
    statistics only and a count is not one. If a future check wants to compare
    clamp rates across implementations, add the counter to both baselines first.
    """
    s = np.sort(valuations)

    def pct(p: float) -> float:
        # Replicates percentile() at monte_carlo.rs:130-133 (round, not interpolate)
        return float(s[int(round(p * (len(s) - 1)))])

    return {
        "mean": float(np.mean(s)),
        "median": pct(0.50),
        "std_dev": float(np.std(s)),  # population std, matching monte_carlo.rs:107-110
        "percentile_5": pct(0.05),
        "percentile_25": pct(0.25),
        "percentile_75": pct(0.75),
        "percentile_95": pct(0.95),
        "simulations": len(s),
    }


def agreement(a: dict, b: dict, tolerance: float) -> tuple[bool, list[str]]:
    """
    Compare two stochastic summaries. These are different random draws, so exact
    equality is impossible; we assert the distributions agree within `tolerance`
    relative error on each statistic.
    """
    problems = []
    for key in ("mean", "median", "std_dev", "percentile_5", "percentile_95"):
        va, vb = a[key], b[key]
        denom = max(abs(va), abs(vb), 1e-9)
        rel = abs(va - vb) / denom
        if rel > tolerance:
            problems.append(f"{key}: {va:,.0f} vs {vb:,.0f} ({rel:.1%} apart)")
    return (not problems), problems


def time_it(fn, repeat: int) -> dict:
    """Return timing stats over `repeat` runs, plus the last result."""
    timings, result = [], None
    for _ in range(repeat):
        start = time.perf_counter()
        result = fn()
        timings.append(time.perf_counter() - start)
    return {
        "median_s": statistics.median(timings),
        "min_s": min(timings),
        "max_s": max(timings),
        "runs": repeat,
        "result": result,
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sims", type=int, default=10_000, help="simulations per run (default 10000)")
    ap.add_argument("--years", type=int, default=5, help="projection years (default 5)")
    ap.add_argument("--repeat", type=int, default=5, help="repetitions per implementation (default 5)")
    ap.add_argument("--seed", type=int, default=42, help="seed for the Python baselines")
    ap.add_argument("--tolerance", type=float, default=0.10,
                    help="max relative disagreement between implementations (default 0.10)")
    ap.add_argument("--skip-naive", action="store_true",
                    help="skip the naive loop (it dominates runtime at large --sims)")
    ap.add_argument("--json", metavar="PATH", help="write full results to PATH")
    args = ap.parse_args()

    inp = MonteCarloInputs(simulations=args.sims, years=args.years)

    print("=" * 74)
    print("Monte Carlo DCF benchmark")
    print("=" * 74)
    print(f"  {platform.platform()}")
    print(f"  Python {sys.version.split()[0]} / NumPy {np.__version__}")
    print(f"  machine: {platform.processor() or platform.machine()}")
    print(f"  workload: {inp.simulations:,} simulations x {inp.years} years")
    print(f"  repetitions: {args.repeat} (reporting median)")
    print()

    results: dict[str, dict] = {}

    if not args.skip_naive:
        print("running naive Python loop ...", flush=True)
        r = time_it(lambda: monte_carlo_naive(inp, np.random.default_rng(args.seed)), args.repeat)
        r["summary"] = summarize(r.pop("result"))
        results["naive_python"] = r
        print(f"  median {r['median_s']:.3f}s")

    print("running vectorized NumPy ...", flush=True)
    r = time_it(lambda: monte_carlo_vectorized(inp, np.random.default_rng(args.seed)), args.repeat)
    r["summary"] = summarize(r.pop("result"))
    results["vectorized_numpy"] = r
    print(f"  median {r['median_s']:.3f}s")

    rust_fn, rust_err = load_rust()
    if rust_fn is None:
        print(f"\nSKIPPED Rust: {rust_err}")
    else:
        print("running Rust (PyO3) ...", flush=True)
        r = time_it(lambda: monte_carlo_rust(rust_fn, inp), args.repeat)
        r["summary"] = r.pop("result")
        results["rust"] = r
        print(f"  median {r['median_s']:.3f}s")

    # ---- correctness gate: no speedup is reported unless outputs agree -----
    print("\n" + "-" * 74)
    print("Numerical agreement (gate — a speedup from disagreeing code is meaningless)")
    print("-" * 74)

    ref_name = "vectorized_numpy"
    ref = results[ref_name]["summary"]
    all_agree = True
    for name, data in results.items():
        if name == ref_name:
            continue
        ok, problems = agreement(ref, data["summary"], args.tolerance)
        if ok:
            print(f"  PASS  {name} agrees with {ref_name} within {args.tolerance:.0%}")
        else:
            all_agree = False
            print(f"  FAIL  {name} disagrees with {ref_name}:")
            for p in problems:
                print(f"          {p}")

    # ---- speedups -----------------------------------------------------------
    print("\n" + "-" * 74)
    print("Results")
    print("-" * 74)
    print(f"  {'implementation':<22} {'median':>10} {'min':>10} {'max':>10}")
    for name, data in results.items():
        print(f"  {name:<22} {data['median_s']:>9.3f}s {data['min_s']:>9.3f}s {data['max_s']:>9.3f}s")

    if "rust" in results:
        if not all_agree:
            print("\n  NO SPEEDUP REPORTED: implementations disagree numerically (see above).")
            print("  Reconcile the algorithms first. Do not publish a number from this run.")
        else:
            rust_t = results["rust"]["median_s"]
            vec_t = results["vectorized_numpy"]["median_s"]
            print(f"\n  Rust vs vectorized NumPy : {vec_t / rust_t:>6.1f}x   <-- QUOTE THIS ONE")
            if "naive_python" in results:
                naive_t = results["naive_python"]["median_s"]
                print(f"  Rust vs naive Python loop: {naive_t / rust_t:>6.1f}x   (do not quote; "
                      f"inflated by {naive_t / vec_t:.1f}x of NumPy headroom)")
    else:
        print("\n  No Rust result. Nothing in this run supports any speedup claim.")
        if "naive_python" in results:
            naive_t, vec_t = results["naive_python"]["median_s"], results["vectorized_numpy"]["median_s"]
            print(f"  For reference, NumPy alone beats the naive loop by {naive_t / vec_t:.1f}x, "
                  f"which is the headroom\n  a naive baseline would wrongly credit to Rust.")

    if args.json:
        payload = {
            "environment": {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "numpy": np.__version__,
                "processor": platform.processor() or platform.machine(),
            },
            "workload": asdict(inp),
            "repetitions": args.repeat,
            "tolerance": args.tolerance,
            "agreement_passed": all_agree,
            "results": results,
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\n  wrote {args.json}")

    return 0 if all_agree else 1


if __name__ == "__main__":
    raise SystemExit(main())
