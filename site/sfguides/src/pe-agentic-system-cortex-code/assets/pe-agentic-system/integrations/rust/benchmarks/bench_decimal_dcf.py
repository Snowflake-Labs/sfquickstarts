"""
Decimal-exact DCF benchmark: the honest case for Rust.

Why this benchmark and not the Monte Carlo one
----------------------------------------------
Monte Carlo is Rust's *weakest* case in this codebase. NumPy vectorizes it to near
memory bandwidth — measured at ~1 ms for 10,000 simulations — so there is no
meaningful speedup available, and the previously published "33x" was refuted (see
benchmarks/README.md).

The defensible argument is different, and it is about *exactness*, not speed:

    Money must be computed in decimal to reconcile with an audited spreadsheet.
    Python's `decimal` is slow and does not vectorize. Rust's `rust_decimal` is
    fast. So Rust does not make floats faster — it makes *exactness affordable*.

That reframes Rust from a performance optimization into a correctness enabler,
which is both true and much harder to argue with.

What this measures
------------------
1. **Speed** across four implementations of the identical DCF from dcf.rs:
     - Python `Decimal`      — exact, the correctness reference
     - Python `float`        — fast, inexact
     - NumPy vectorized      — fast, inexact, vectorized across the grid
     - Rust `rust_decimal`   — exact AND fast (the claim; requires a build)

2. **Precision divergence** between decimal and float on the same inputs. This is
   the part that matters for an audit and the part a speed-only benchmark misses
   entirely.

Workload: a WACC x growth sensitivity grid, which is what analysts actually run —
a single DCF is too fast to time meaningfully.

Usage
-----
    python3 bench_decimal_dcf.py
    python3 bench_decimal_dcf.py --grid 25        # 25x25 = 625 DCFs
    python3 bench_decimal_dcf.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext

import numpy as np

# rust_decimal carries 28 significant digits; match it so the comparison is fair.
getcontext().prec = 28


# --------------------------------------------------------------------------
# Inputs — mirrors DCFInputs::new_constant_growth (dcf.rs:44-69)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DCFInputs:
    initial_revenue: str = "100000000"
    growth_rate: str = "0.10"
    ebitda_margin: str = "0.25"
    tax_rate: str = "0.25"
    wacc: str = "0.12"
    terminal_growth: str = "0.03"
    capex_pct_revenue: str = "0.05"   # dcf.rs:62 default
    nwc_pct_revenue: str = "0.10"     # dcf.rs:63 default
    projection_years: int = 5


# --------------------------------------------------------------------------
# Implementation 1: Python Decimal — the correctness reference
#
# Line-by-line port of calculate_dcf (dcf.rs:71-139). Deliberately keeps the
# same operation order: floating-point and decimal results both depend on it,
# and reordering would make the precision comparison meaningless.
# --------------------------------------------------------------------------


def dcf_decimal(inp: DCFInputs, wacc: Decimal, growth: Decimal) -> Decimal:
    one = Decimal(1)
    revenue = Decimal(inp.initial_revenue)
    margin = Decimal(inp.ebitda_margin)
    tax = Decimal(inp.tax_rate)
    capex_pct = Decimal(inp.capex_pct_revenue)
    nwc_pct = Decimal(inp.nwc_pct_revenue)
    g_term = Decimal(inp.terminal_growth)

    total_pv_fcf = Decimal(0)
    fcf = Decimal(0)

    for year in range(1, inp.projection_years + 1):
        revenue = revenue * (one + growth)                       # dcf.rs:82
        ebitda = revenue * margin                                # dcf.rs:85
        nopat = ebitda * (one - tax)                             # dcf.rs:89
        capex = revenue * capex_pct                              # dcf.rs:92
        nwc = revenue * nwc_pct * growth / (one + growth)        # dcf.rs:95
        fcf = nopat - capex - nwc                                # dcf.rs:98
        discount = (one + wacc) ** year                          # dcf.rs:101
        total_pv_fcf += fcf / discount                           # dcf.rs:104-105

    terminal_value = fcf * (one + g_term) / (wacc - g_term)      # dcf.rs:123-124
    pv_terminal = terminal_value / (one + wacc) ** inp.projection_years
    return total_pv_fcf + pv_terminal                            # dcf.rs:130


# --------------------------------------------------------------------------
# Implementation 2: Python float — same algorithm, inexact
# --------------------------------------------------------------------------


def dcf_float(inp: DCFInputs, wacc: float, growth: float) -> float:
    revenue = float(inp.initial_revenue)
    margin = float(inp.ebitda_margin)
    tax = float(inp.tax_rate)
    capex_pct = float(inp.capex_pct_revenue)
    nwc_pct = float(inp.nwc_pct_revenue)
    g_term = float(inp.terminal_growth)

    total_pv_fcf = 0.0
    fcf = 0.0

    for year in range(1, inp.projection_years + 1):
        revenue = revenue * (1.0 + growth)
        ebitda = revenue * margin
        nopat = ebitda * (1.0 - tax)
        capex = revenue * capex_pct
        nwc = revenue * nwc_pct * growth / (1.0 + growth)
        fcf = nopat - capex - nwc
        total_pv_fcf += fcf / (1.0 + wacc) ** year

    terminal_value = fcf * (1.0 + g_term) / (wacc - g_term)
    return total_pv_fcf + terminal_value / (1.0 + wacc) ** inp.projection_years


# --------------------------------------------------------------------------
# Implementation 3: NumPy vectorized over the whole grid
# --------------------------------------------------------------------------


def dcf_numpy_grid(inp: DCFInputs, waccs: np.ndarray, growths: np.ndarray) -> np.ndarray:
    """All (wacc, growth) pairs at once. Returns a 2D grid of enterprise values."""
    w = waccs[:, None]          # column vector -> broadcasts over rows
    g = growths[None, :]        # row vector    -> broadcasts over columns

    margin = float(inp.ebitda_margin)
    tax = float(inp.tax_rate)
    capex_pct = float(inp.capex_pct_revenue)
    nwc_pct = float(inp.nwc_pct_revenue)
    g_term = float(inp.terminal_growth)

    revenue = np.full((len(waccs), len(growths)), float(inp.initial_revenue))
    total_pv_fcf = np.zeros_like(revenue)
    fcf = np.zeros_like(revenue)

    for year in range(1, inp.projection_years + 1):
        revenue = revenue * (1.0 + g)
        nopat = revenue * margin * (1.0 - tax)
        capex = revenue * capex_pct
        nwc = revenue * nwc_pct * g / (1.0 + g)
        fcf = nopat - capex - nwc
        total_pv_fcf += fcf / (1.0 + w) ** year

    terminal_value = fcf * (1.0 + g_term) / (w - g_term)
    return total_pv_fcf + terminal_value / (1.0 + w) ** inp.projection_years


# --------------------------------------------------------------------------
# Implementation 4: Rust
# --------------------------------------------------------------------------


def load_rust():
    try:
        import pe_finance  # type: ignore
    except ImportError as exc:
        return None, f"pe_finance not importable ({exc}). Build: see benchmarks/README.md"
    fn = getattr(pe_finance, "py_dcf_sensitivity", None)
    if fn is None:
        return None, "pe_finance lacks py_dcf_sensitivity (built without --features python?)"
    return fn, None


def dcf_rust_grid(fn, inp: DCFInputs, waccs: list[float], growths: list[float]):
    return json.loads(
        fn(
            float(inp.initial_revenue), float(inp.growth_rate), float(inp.ebitda_margin),
            float(inp.tax_rate), float(inp.wacc), float(inp.terminal_growth),
            inp.projection_years, "wacc", waccs, "growth_rate", growths,
        )
    )


# --------------------------------------------------------------------------
# Harness
# --------------------------------------------------------------------------


def time_it(fn, repeat: int) -> dict:
    timings, result = [], None
    for _ in range(repeat):
        t0 = time.perf_counter()
        result = fn()
        timings.append(time.perf_counter() - t0)
    return {
        "median_s": statistics.median(timings),
        "min_s": min(timings),
        "max_s": max(timings),
        "runs": repeat,
        "result": result,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grid", type=int, default=15,
                    help="grid dimension N; runs N*N DCFs (default 15 -> 225)")
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--years", type=int, default=5)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    inp = DCFInputs(projection_years=args.years)
    n = args.grid

    # WACC 8%-20%, growth 4%-16%. Deliberately chosen so every cell keeps
    # wacc > terminal_growth (3%); otherwise Gordon Growth is undefined and the
    # engine would silently return negative terminal values.
    wacc_f = np.linspace(0.08, 0.20, n)
    growth_f = np.linspace(0.04, 0.16, n)
    wacc_d = [Decimal(str(round(v, 10))) for v in wacc_f]
    growth_d = [Decimal(str(round(v, 10))) for v in growth_f]

    print("=" * 76)
    print("Decimal-exact DCF benchmark")
    print("=" * 76)
    print(f"  {platform.platform()}")
    print(f"  Python {sys.version.split()[0]} / NumPy {np.__version__}")
    print(f"  decimal precision: {getcontext().prec} significant digits "
          f"(matching rust_decimal)")
    print(f"  workload: {n}x{n} = {n*n:,} DCFs x {inp.projection_years} years")
    print(f"  repetitions: {args.repeat} (median reported)")
    print()

    results: dict[str, dict] = {}

    print("running Python Decimal (exact) ...", flush=True)
    r = time_it(lambda: [[dcf_decimal(inp, w, g) for g in growth_d] for w in wacc_d], args.repeat)
    grid_dec = r.pop("result")
    results["python_decimal"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running Python float ...", flush=True)
    r = time_it(lambda: [[dcf_float(inp, float(w), float(g)) for g in growth_f] for w in wacc_f],
                args.repeat)
    grid_flt = r.pop("result")
    results["python_float"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running NumPy vectorized ...", flush=True)
    r = time_it(lambda: dcf_numpy_grid(inp, wacc_f, growth_f), args.repeat)
    grid_np = r.pop("result")
    results["numpy_vectorized"] = r
    print(f"  median {r['median_s']:.4f}s")

    rust_fn, rust_err = load_rust()
    if rust_fn is None:
        print(f"\nSKIPPED Rust: {rust_err}")
    else:
        print("running Rust rust_decimal ...", flush=True)
        r = time_it(lambda: dcf_rust_grid(rust_fn, inp, list(wacc_f), list(growth_f)), args.repeat)
        r.pop("result")
        results["rust_decimal"] = r
        print(f"  median {r['median_s']:.4f}s")

    # ---- precision: the part that actually matters -------------------------
    print("\n" + "-" * 76)
    print("Precision: decimal vs float on identical inputs")
    print("-" * 76)

    worst_abs = Decimal(0)
    worst_cell = None
    for i in range(n):
        for j in range(n):
            diff = abs(grid_dec[i][j] - Decimal(str(grid_flt[i][j])))
            if diff > worst_abs:
                worst_abs, worst_cell = diff, (i, j)

    ref = grid_dec[worst_cell[0]][worst_cell[1]]
    print(f"  worst absolute divergence : ${worst_abs:,.6f}")
    print(f"  at wacc={wacc_f[worst_cell[0]]:.4f}, growth={growth_f[worst_cell[1]]:.4f}")
    print(f"  enterprise value (decimal): ${ref:,.6f}")
    print(f"  enterprise value (float)  : ${Decimal(str(grid_flt[worst_cell[0]][worst_cell[1]])):,.6f}")
    print(f"  relative error            : {float(worst_abs / abs(ref)):.3e}")

    np_worst = max(
        abs(grid_dec[i][j] - Decimal(str(grid_np[i][j])))
        for i in range(n) for j in range(n)
    )
    print(f"  worst divergence, NumPy   : ${np_worst:,.6f}")

    print()
    print("  Interpretation: the relative error is tiny, but it is a *nonzero and")
    print("  input-dependent* discrepancy in a number that has to tie out to an")
    print("  audited model. Reconciliation is pass/fail, not tolerance-based: an")
    print("  IC deck that disagrees with the underlying spreadsheet by any amount")
    print("  costs an analyst an afternoon proving which one is right. Decimal")
    print("  removes that class of question entirely.")

    # ---- speed -------------------------------------------------------------
    print("\n" + "-" * 76)
    print("Speed")
    print("-" * 76)
    print(f"  {'implementation':<22} {'median':>11} {'min':>11} {'exact?':>8}")
    exactness = {
        "python_decimal": "yes", "python_float": "no",
        "numpy_vectorized": "no", "rust_decimal": "yes",
    }
    for name, data in results.items():
        print(f"  {name:<22} {data['median_s']:>10.4f}s {data['min_s']:>10.4f}s "
              f"{exactness[name]:>8}")

    dec_t = results["python_decimal"]["median_s"]
    flt_t = results["python_float"]["median_s"]
    print(f"\n  Cost of exactness in Python: {dec_t / flt_t:.1f}x slower than float")

    if "rust_decimal" in results:
        rust_t = results["rust_decimal"]["median_s"]
        print(f"  Rust decimal vs Python decimal: {dec_t / rust_t:.1f}x faster  "
              f"<-- THE DEFENSIBLE CLAIM")
        print(f"  Rust decimal vs NumPy float   : "
              f"{results['numpy_vectorized']['median_s'] / rust_t:.2f}x")
        print("\n  If the second number is below 1.0, Rust is slower than inexact NumPy —")
        print("  which is fine and expected. The claim is that Rust delivers *exact*")
        print("  results at a speed competitive with inexact ones, not that it beats")
        print("  NumPy at float math.")
    else:
        print(f"\n  Rust not built, so the central claim — that rust_decimal collapses")
        print(f"  the {dec_t / flt_t:.1f}x exactness penalty measured above — remains")
        print( "  UNVERIFIED. That penalty is the gap Rust must close; publish nothing")
        print( "  until it is measured.")

    if args.json:
        payload = {
            "environment": {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "numpy": np.__version__,
                "decimal_precision": getcontext().prec,
            },
            "workload": {**asdict(inp), "grid": n, "total_dcfs": n * n},
            "repetitions": args.repeat,
            "speed": results,
            "precision": {
                "worst_abs_divergence_decimal_vs_float": str(worst_abs),
                "worst_relative_error": float(worst_abs / abs(ref)),
                "worst_abs_divergence_decimal_vs_numpy": str(np_worst),
            },
            "rust_available": "rust_decimal" in results,
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\n  wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
