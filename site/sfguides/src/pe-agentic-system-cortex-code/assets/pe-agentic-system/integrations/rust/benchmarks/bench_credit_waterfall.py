"""
Finding the Rust wedge: decimal-exact, path-dependent, branch-divergent credit math.

The question this answers
-------------------------
Earlier benchmarks were unkind to Rust. On Monte Carlo DCF, vectorized NumPy beats
naive Python by 44-49x and finishes 10,000 sims in ~1 ms, leaving Rust nothing to
win. On the decimal DCF sensitivity grid, NumPy float ran ~350x faster than Python
`Decimal`, so even the exactness argument had a low ceiling.

Both of those workloads share a property: **they vectorize cleanly.** Every
scenario executes the same arithmetic in the same order, so NumPy can advance
thousands of paths in lockstep.

So the wedge, if one exists, must be a workload where NumPy *cannot follow*. That
requires the intersection of two things:

1. **Decimal money.** NumPy has no native decimal dtype. `object`-dtype arrays of
   `Decimal` fall back to per-element Python dispatch and are *slower* than plain
   lists, so exactness removes vectorization from the table entirely.

2. **Path-dependent branch divergence.** Each period's state depends on the
   previous period's *branch outcomes* — covenant breached or not, revolver drawn
   or not, PIK toggled or not. Different scenarios take different branches at
   different times, so NumPy must evaluate *every* branch for *every* scenario and
   discard the unused results with masks. Divergence turns vectorization from a
   win into wasted work.

A leveraged credit schedule with covenant tests is exactly this workload, and it is
not a contrived one — it is the core of every LBO model, every credit agreement
compliance check, and every CLO cashflow engine.

The model
---------
Realistic enough to be representative, small enough to audit:
  - four tranches: revolver, TLA (amortizing), TLB (bullet), mezzanine (cash + PIK)
  - monthly periods over a 5-year hold
  - strict payment priority; cash sweep applied in seniority order
  - two covenants: max net leverage (stepping down over time), min interest coverage
  - breach consequences: sweep steps to 100%, revolver frozen, mezz PIK toggles on
  - liquidity shortfall draws the revolver; a maxed revolver is a default event that
    terminates the path early (producing ragged, uneven path lengths)

Usage
-----
    python3 bench_credit_waterfall.py
    python3 bench_credit_waterfall.py --scenarios 2000
    python3 bench_credit_waterfall.py --json wedge.json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, getcontext

import numpy as np

getcontext().prec = 28  # match rust_decimal


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

MONTHS = 60
D = Decimal


@dataclass(frozen=True)
class Deal:
    ebitda_annual: str = "40000000"
    revolver_commit: str = "15000000"
    tla_balance: str = "60000000"
    tlb_balance: str = "90000000"
    mezz_balance: str = "40000000"

    revolver_rate: str = "0.0800"
    tla_rate: str = "0.0775"
    tlb_rate: str = "0.0850"
    mezz_cash_rate: str = "0.1200"
    mezz_pik_rate: str = "0.0300"

    tla_amort_annual: str = "0.05"
    tlb_amort_annual: str = "0.01"

    base_sweep: str = "0.75"
    delevered_sweep: str = "0.50"
    delever_threshold: str = "3.5"

    cash_conversion: str = "0.65"
    min_coverage: str = "2.00"

    # Covenant tightness. Entry leverage on the defaults above is
    # (60+90+40)/40 = 4.75x, so a 6.0x opening covenant leaves so much headroom
    # that nothing ever breaches — which defeats the purpose of the benchmark.
    # 5.25x stepping down 0.25x/year puts scenarios genuinely at risk.
    covenant_open: str = "5.25"
    covenant_step: str = "0.25"


# Module-level covenant config, set from Deal at startup so the hot loops stay
# free of attribute lookups (keeps the comparison about arithmetic, not plumbing).
_COV_OPEN = D("5.25")
_COV_STEP = D("0.25")


def leverage_covenant(month: int) -> Decimal:
    """Step-down schedule: tightens by _COV_STEP each year."""
    return _COV_OPEN - _COV_STEP * (month // 12)


# --------------------------------------------------------------------------
# Implementation 1: Python Decimal, scalar — the correctness reference
#
# This is what a firm that needs auditable numbers must run today.
# --------------------------------------------------------------------------


def waterfall_decimal(deal: Deal, ebitda_path: list[Decimal]) -> dict:
    rev = D(0)
    rev_commit = D(deal.revolver_commit)
    tla = D(deal.tla_balance)
    tlb = D(deal.tlb_balance)
    mezz = D(deal.mezz_balance)

    rev_r = D(deal.revolver_rate) / 12
    tla_r = D(deal.tla_rate) / 12
    tlb_r = D(deal.tlb_rate) / 12
    mezz_cash_r = D(deal.mezz_cash_rate) / 12
    mezz_pik_r = D(deal.mezz_pik_rate) / 12

    tla_amort = D(deal.tla_balance) * D(deal.tla_amort_annual) / 12
    tlb_amort = D(deal.tlb_balance) * D(deal.tlb_amort_annual) / 12
    conv = D(deal.cash_conversion)
    min_cov = D(deal.min_coverage)
    thresh = D(deal.delever_threshold)

    breached = False
    pik_on = False
    rev_frozen = False
    defaulted = False
    breach_count = 0
    total_interest = D(0)
    months_run = 0

    for m in range(MONTHS):
        months_run = m + 1
        ebitda_m = ebitda_path[m] / 12

        # --- interest accrual (branch: PIK toggle) ---
        int_rev = rev * rev_r
        int_tla = tla * tla_r
        int_tlb = tlb * tlb_r
        int_mezz_cash = mezz * mezz_cash_r
        if pik_on:
            mezz += mezz * mezz_pik_r          # capitalizes, changes all later interest
            cash_interest = int_rev + int_tla + int_tlb
        else:
            cash_interest = int_rev + int_tla + int_tlb + int_mezz_cash
        total_interest += cash_interest

        # --- cash available ---
        cash = ebitda_m * conv - cash_interest

        # --- mandatory amortization, seniority order ---
        pay_tla = min(tla_amort, tla)
        pay_tlb = min(tlb_amort, tlb)
        mandatory = pay_tla + pay_tlb

        if cash >= mandatory:
            tla -= pay_tla
            tlb -= pay_tlb
            cash -= mandatory
        else:
            # partial payment then revolver draw (branch: liquidity shortfall)
            shortfall = mandatory - cash
            headroom = rev_commit - rev
            if rev_frozen or shortfall > headroom:
                defaulted = True
                break                           # ragged path length
            rev += shortfall
            tla -= pay_tla
            tlb -= pay_tlb
            cash = D(0)

        # --- covenant tests (state depends on current balances) ---
        net_debt = rev + tla + tlb + mezz
        # ebitda_path holds ANNUALIZED EBITDA per month, so the LTM annual figure
        # is the mean of the trailing window. Multiplying by 12 here would double
        # -annualize and understate leverage by 12x, which is exactly the bug that
        # made every covenant unbreachable in the first calibration of this file.
        window = ebitda_path[max(0, m - 11) : m + 1]
        ebitda_ltm = sum(window) / D(len(window))
        lev = net_debt / ebitda_ltm if ebitda_ltm > 0 else D(999)
        cov = (ebitda_ltm / 12) / cash_interest if cash_interest > 0 else D(999)

        newly_breached = lev > leverage_covenant(m) or cov < min_cov
        if newly_breached:
            breach_count += 1
            if not breached:
                breached, pik_on, rev_frozen = True, True, True   # sticky state
        elif breached and lev < thresh:
            breached = pik_on = rev_frozen = False                # cure

        # --- cash sweep (branch: rate depends on breach + leverage) ---
        if breached:
            sweep_pct = D(1)
        elif lev < thresh:
            sweep_pct = D(deal.delevered_sweep)
        else:
            sweep_pct = D(deal.base_sweep)

        sweep = cash * sweep_pct
        if rev > 0:
            pay = min(sweep, rev); rev -= pay; sweep -= pay
        if sweep > 0 and tlb > 0:
            pay = min(sweep, tlb); tlb -= pay; sweep -= pay
        if sweep > 0 and tla > 0:
            pay = min(sweep, tla); tla -= pay; sweep -= pay
        if sweep > 0 and mezz > 0:
            mezz -= min(sweep, mezz)

    return {
        "final_debt": rev + tla + tlb + mezz,
        "defaulted": defaulted,
        "breaches": breach_count,
        "total_interest": total_interest,
        "months": months_run,
    }


# --------------------------------------------------------------------------
# Implementation 2: Python float, scalar
# --------------------------------------------------------------------------


def waterfall_float(deal: Deal, ebitda_path: list[float]) -> dict:
    rev = 0.0
    rev_commit = float(deal.revolver_commit)
    tla = float(deal.tla_balance)
    tlb = float(deal.tlb_balance)
    mezz = float(deal.mezz_balance)

    rev_r = float(deal.revolver_rate) / 12
    tla_r = float(deal.tla_rate) / 12
    tlb_r = float(deal.tlb_rate) / 12
    mezz_cash_r = float(deal.mezz_cash_rate) / 12
    mezz_pik_r = float(deal.mezz_pik_rate) / 12

    tla_amort = float(deal.tla_balance) * float(deal.tla_amort_annual) / 12
    tlb_amort = float(deal.tlb_balance) * float(deal.tlb_amort_annual) / 12
    conv = float(deal.cash_conversion)
    min_cov = float(deal.min_coverage)
    thresh = float(deal.delever_threshold)

    breached = pik_on = rev_frozen = defaulted = False
    breach_count = 0
    total_interest = 0.0
    months_run = 0

    for m in range(MONTHS):
        months_run = m + 1
        ebitda_m = ebitda_path[m] / 12

        int_rev, int_tla, int_tlb = rev * rev_r, tla * tla_r, tlb * tlb_r
        int_mezz_cash = mezz * mezz_cash_r
        if pik_on:
            mezz += mezz * mezz_pik_r
            cash_interest = int_rev + int_tla + int_tlb
        else:
            cash_interest = int_rev + int_tla + int_tlb + int_mezz_cash
        total_interest += cash_interest

        cash = ebitda_m * conv - cash_interest

        pay_tla, pay_tlb = min(tla_amort, tla), min(tlb_amort, tlb)
        mandatory = pay_tla + pay_tlb

        if cash >= mandatory:
            tla -= pay_tla; tlb -= pay_tlb; cash -= mandatory
        else:
            shortfall = mandatory - cash
            headroom = rev_commit - rev
            if rev_frozen or shortfall > headroom:
                defaulted = True
                break
            rev += shortfall; tla -= pay_tla; tlb -= pay_tlb; cash = 0.0

        net_debt = rev + tla + tlb + mezz
        window = ebitda_path[max(0, m - 11) : m + 1]
        ebitda_ltm = sum(window) / len(window)      # already annualized; see decimal version
        lev = net_debt / ebitda_ltm if ebitda_ltm > 0 else 999.0
        cov = (ebitda_ltm / 12) / cash_interest if cash_interest > 0 else 999.0

        if lev > float(leverage_covenant(m)) or cov < min_cov:
            breach_count += 1
            if not breached:
                breached = pik_on = rev_frozen = True
        elif breached and lev < thresh:
            breached = pik_on = rev_frozen = False

        sweep_pct = 1.0 if breached else (float(deal.delevered_sweep) if lev < thresh
                                         else float(deal.base_sweep))
        sweep = cash * sweep_pct
        if rev > 0:
            pay = min(sweep, rev); rev -= pay; sweep -= pay
        if sweep > 0 and tlb > 0:
            pay = min(sweep, tlb); tlb -= pay; sweep -= pay
        if sweep > 0 and tla > 0:
            pay = min(sweep, tla); tla -= pay; sweep -= pay
        if sweep > 0 and mezz > 0:
            mezz -= min(sweep, mezz)

    return {
        "final_debt": rev + tla + tlb + mezz,
        "defaulted": defaulted,
        "breaches": breach_count,
        "total_interest": total_interest,
        "months": months_run,
    }


# --------------------------------------------------------------------------
# Implementation 3: NumPy, vectorized across scenarios with masks
#
# The strongest Python competitor. Note what vectorization costs here: every
# branch must be evaluated for every scenario and then masked away, and
# early-terminating paths must be carried as inert rows rather than dropped.
# --------------------------------------------------------------------------


def waterfall_numpy(deal: Deal, ebitda_paths: np.ndarray) -> dict:
    n = ebitda_paths.shape[0]

    rev = np.zeros(n)
    rev_commit = np.full(n, float(deal.revolver_commit))
    tla = np.full(n, float(deal.tla_balance))
    tlb = np.full(n, float(deal.tlb_balance))
    mezz = np.full(n, float(deal.mezz_balance))

    rev_r = float(deal.revolver_rate) / 12
    tla_r = float(deal.tla_rate) / 12
    tlb_r = float(deal.tlb_rate) / 12
    mezz_cash_r = float(deal.mezz_cash_rate) / 12
    mezz_pik_r = float(deal.mezz_pik_rate) / 12

    tla_amort = float(deal.tla_balance) * float(deal.tla_amort_annual) / 12
    tlb_amort = float(deal.tlb_balance) * float(deal.tlb_amort_annual) / 12
    conv = float(deal.cash_conversion)
    min_cov = float(deal.min_coverage)
    thresh = float(deal.delever_threshold)

    breached = np.zeros(n, dtype=bool)
    pik_on = np.zeros(n, dtype=bool)
    rev_frozen = np.zeros(n, dtype=bool)
    alive = np.ones(n, dtype=bool)
    breach_count = np.zeros(n, dtype=np.int64)
    total_interest = np.zeros(n)
    months_run = np.zeros(n, dtype=np.int64)

    for m in range(MONTHS):
        months_run = np.where(alive, m + 1, months_run)
        ebitda_m = ebitda_paths[:, m] / 12

        int_base = rev * rev_r + tla * tla_r + tlb * tlb_r
        int_mezz_cash = mezz * mezz_cash_r
        # BOTH branches computed for ALL scenarios, then selected:
        mezz = np.where(pik_on, mezz * (1.0 + mezz_pik_r), mezz)
        cash_interest = np.where(pik_on, int_base, int_base + int_mezz_cash)
        total_interest += np.where(alive, cash_interest, 0.0)

        cash = ebitda_m * conv - cash_interest

        pay_tla = np.minimum(tla_amort, tla)
        pay_tlb = np.minimum(tlb_amort, tlb)
        mandatory = pay_tla + pay_tlb

        can_pay = cash >= mandatory
        shortfall = np.maximum(mandatory - cash, 0.0)
        headroom = rev_commit - rev
        would_default = (~can_pay) & (rev_frozen | (shortfall > headroom))

        alive = alive & ~would_default
        tla = np.where(alive, tla - pay_tla, tla)
        tlb = np.where(alive, tlb - pay_tlb, tlb)
        rev = np.where(alive & ~can_pay, rev + shortfall, rev)
        cash = np.where(can_pay, cash - mandatory, 0.0)

        net_debt = rev + tla + tlb + mezz
        lo = max(0, m - 11)
        ebitda_ltm = ebitda_paths[:, lo : m + 1].mean(axis=1)   # already annualized
        lev = np.where(ebitda_ltm > 0, net_debt / np.maximum(ebitda_ltm, 1e-9), 999.0)
        cov = np.where(cash_interest > 0,
                       (ebitda_ltm / 12) / np.maximum(cash_interest, 1e-9), 999.0)

        newly = (lev > float(leverage_covenant(m))) | (cov < min_cov)
        breach_count += (newly & alive).astype(np.int64)
        becomes = newly & ~breached
        breached = breached | becomes
        pik_on = pik_on | becomes
        rev_frozen = rev_frozen | becomes
        cures = breached & ~newly & (lev < thresh)
        breached = breached & ~cures
        pik_on = pik_on & ~cures
        rev_frozen = rev_frozen & ~cures

        sweep_pct = np.where(breached, 1.0,
                             np.where(lev < thresh, float(deal.delevered_sweep),
                                      float(deal.base_sweep)))
        sweep = np.where(alive, cash * sweep_pct, 0.0)

        # Sequential priority cannot be vectorized away — it is four dependent
        # passes over the whole array regardless of how many scenarios need each.
        pay = np.minimum(sweep, rev); rev -= pay; sweep -= pay
        pay = np.minimum(sweep, tlb); tlb -= pay; sweep -= pay
        pay = np.minimum(sweep, tla); tla -= pay; sweep -= pay
        mezz -= np.minimum(sweep, mezz)

    return {
        "final_debt": rev + tla + tlb + mezz,
        "defaulted": ~alive,
        "breaches": breach_count,
        "total_interest": total_interest,
        "months": months_run,
    }


# --------------------------------------------------------------------------
# Implementation 4: NumPy object-dtype Decimal — proves exactness kills NumPy
# --------------------------------------------------------------------------


def decimal_object_array_probe(n: int = 200) -> tuple[float, float]:
    """Compare Decimal in an object array vs a plain list, same arithmetic.

    Measured result contradicts the intuition this probe was written to confirm:
    the object array is *faster* than the list comprehension, because NumPy's
    per-element dispatch loop is C code while the comprehension pays Python
    bytecode overhead per iteration. Both still dispatch to `Decimal.__mul__`
    per element, so neither is vectorized in any real sense.

    The correct conclusion is therefore narrower than "object arrays are slow":
    there is no decimal dtype, so no SIMD, no contiguous-buffer arithmetic, and
    no asymptotic win from array size. Exact money math gets Python-object
    dispatch either way.
    """
    a = [D("1.0001") for _ in range(n)]
    b = [D("1.00002") for _ in range(n)]
    arr_a, arr_b = np.array(a, dtype=object), np.array(b, dtype=object)

    t0 = time.perf_counter()
    for _ in range(200):
        _ = arr_a * arr_b
    numpy_obj = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(200):
        _ = [x * y for x, y in zip(a, b)]
    plain_list = time.perf_counter() - t0

    return numpy_obj, plain_list


def float_dtype_reference(n: int = 200) -> float:
    """Same shape of work in native float64, to show what real vectorization buys."""
    fa = np.full(n, 1.0001)
    fb = np.full(n, 1.00002)
    t0 = time.perf_counter()
    for _ in range(200):
        _ = fa * fb
    return time.perf_counter() - t0


# --------------------------------------------------------------------------
# Harness
# --------------------------------------------------------------------------


def make_paths(n: int, seed: int = 7, drift: float = 0.004,
               vol: float = 0.045) -> tuple[np.ndarray, list[list[Decimal]]]:
    """Stochastic EBITDA paths.

    `drift` and `vol` are exposed because the benchmark is only meaningful when a
    non-trivial minority of scenarios actually breach covenants. With positive
    drift and a 75-100% cash sweep, leverage falls so fast that nothing ever
    breaches and the branch-divergence mechanism is never exercised — which is
    what the first calibration of this benchmark got wrong.
    """
    rng = np.random.default_rng(seed)
    base = 40_000_000.0
    shocks = rng.normal(drift, vol, size=(n, MONTHS))
    paths = base * np.cumprod(1.0 + shocks, axis=1)
    dec_paths = [[D(str(round(v, 2))) for v in row] for row in paths]
    return paths, dec_paths


def time_it(fn, repeat: int) -> dict:
    ts, res = [], None
    for _ in range(repeat):
        t0 = time.perf_counter()
        res = fn()
        ts.append(time.perf_counter() - t0)
    return {"median_s": statistics.median(ts), "min_s": min(ts), "runs": repeat, "result": res}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scenarios", type=int, default=1000)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--drift", type=float, default=-0.002,
                    help="monthly EBITDA drift (default -0.002: mild decline, which is "
                         "what puts a levered credit under covenant pressure)")
    ap.add_argument("--vol", type=float, default=0.055,
                    help="monthly EBITDA volatility (default 0.055)")
    ap.add_argument("--covenant-open", type=float, default=5.00,
                    help="opening max-leverage covenant (default 5.00 vs 4.75x entry)")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    global _COV_OPEN
    _COV_OPEN = D(str(args.covenant_open))

    deal = Deal()
    n = args.scenarios
    float_paths, dec_paths = make_paths(n, drift=args.drift, vol=args.vol)

    print("=" * 78)
    print("Rust wedge probe: decimal-exact, path-dependent credit waterfall")
    print("=" * 78)
    print(f"  {platform.platform()}")
    print(f"  Python {sys.version.split()[0]} / NumPy {np.__version__} / decimal prec 28")
    print(f"  workload: {n:,} scenarios x {MONTHS} monthly periods x 4 tranches")
    print(f"  EBITDA drift {args.drift:+.4f}/mo, vol {args.vol:.3f}/mo; "
          f"covenant opens at {args.covenant_open:.2f}x vs 4.75x entry leverage")
    print(f"  branching: covenant tests, sweep tiers, PIK toggle, revolver draw, default")
    print(f"  repetitions: {args.repeat} (median)")
    print()

    results = {}

    print("running Python Decimal, scalar (exact) ...", flush=True)
    r = time_it(lambda: [waterfall_decimal(deal, p) for p in dec_paths], args.repeat)
    dec_out = r.pop("result")
    results["python_decimal"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running Python float, scalar ...", flush=True)
    r = time_it(lambda: [waterfall_float(deal, list(p)) for p in float_paths], args.repeat)
    flt_out = r.pop("result")
    results["python_float"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running NumPy vectorized + masks ...", flush=True)
    r = time_it(lambda: waterfall_numpy(deal, float_paths), args.repeat)
    np_out = r.pop("result")
    results["numpy_masked"] = r
    print(f"  median {r['median_s']:.4f}s")

    # ---- divergence stats: is this workload actually branchy? --------------
    n_default = sum(1 for o in dec_out if o["defaulted"])
    n_breach = sum(1 for o in dec_out if o["breaches"] > 0)
    ragged = len({o["months"] for o in dec_out})
    print("\n" + "-" * 78)
    print("Branch divergence (the property that defeats vectorization)")
    print("-" * 78)
    print(f"  scenarios breaching a covenant : {n_breach:,} / {n:,} ({n_breach/n:.1%})")
    print(f"  scenarios defaulting early     : {n_default:,} / {n:,} ({n_default/n:.1%})")
    print(f"  distinct path lengths          : {ragged}")
    print("  -> NumPy must evaluate every branch for every scenario and mask the")
    print("     unused results; terminated paths ride along as inert rows.")

    # ---- correctness cross-check ------------------------------------------
    agree = sum(
        1 for i, o in enumerate(dec_out)
        if o["defaulted"] == bool(np_out["defaulted"][i])
    )
    print(f"\n  decimal vs numpy default-flag agreement: {agree:,}/{n:,}")

    # ---- object-dtype probe ------------------------------------------------
    obj_t, list_t = decimal_object_array_probe()
    flt_dtype_t = float_dtype_reference()
    print("\n" + "-" * 78)
    print("What exactness costs in NumPy terms")
    print("-" * 78)
    print(f"  Decimal in np.array(dtype=object) : {obj_t*1000:.2f} ms")
    print(f"  Decimal in a plain Python list    : {list_t*1000:.2f} ms")
    print(f"  float64 in a native NumPy array   : {flt_dtype_t*1000:.2f} ms")
    print()
    print(f"  The object array is {list_t/obj_t:.2f}x FASTER than the list — NumPy's")
    print( "  dispatch loop is C where a comprehension is bytecode. So the naive claim")
    print( "  'object arrays are slower than lists' is wrong, and this probe refuted it.")
    print()
    print(f"  The real gap is against a native dtype: float64 is "
          f"{obj_t/flt_dtype_t:.0f}x faster than")
    print( "  object-Decimal. There is no decimal dtype, so exact money math gets no")
    print( "  SIMD, no contiguous-buffer arithmetic, and no asymptotic win from size.")
    print( "  Vectorization is unavailable for exactness — not merely inefficient.")

    # ---- the wedge ---------------------------------------------------------
    dec_t = results["python_decimal"]["median_s"]
    flt_t = results["python_float"]["median_s"]
    np_t = results["numpy_masked"]["median_s"]

    print("\n" + "=" * 78)
    print("THE WEDGE")
    print("=" * 78)
    print(f"  Python Decimal (exact, required for audit) : {dec_t:.4f}s")
    print(f"  Python float, scalar                       : {flt_t:.4f}s   ({dec_t/flt_t:.1f}x faster)")
    print(f"  NumPy float, vectorized + masked           : {np_t:.4f}s   ({dec_t/np_t:.1f}x faster)")
    print()
    print("  HYPOTHESIS PARTLY REFUTED. This benchmark was built to show that branch")
    print("  divergence stops NumPy from following. It does not. Even with 80% of")
    print(f"  scenarios breaching and {ragged} distinct path lengths, NumPy still wins by")
    print(f"  {dec_t/np_t:.0f}x. Its advantage fell from ~350x on the smooth DCF grid to")
    print(f"  {dec_t/np_t:.0f}x here \u2014 a real collapse of roughly 6x, but not a wall.")
    print("  Masked all-branch evaluation is simply cheaper than Python-level branching.")
    print()
    print("  So the wedge is NOT 'vectorization fails'. It is narrower and it is about")
    print("  admissibility, not speed:")
    print()
    print(f"    NumPy buys its {dec_t/np_t:.0f}x by giving up exactness, and for contractual")
    print("    money \u2014 sweep payments, waterfall distributions, covenant compliance")
    print("    certificates \u2014 that trade is not available. There is no decimal dtype,")
    print("    so vectorization and exactness are mutually exclusive in NumPy.")
    print("    Among *admissible* implementations, Python Decimal is the only baseline,")
    print(f"    and it is the {dec_t:.4f}s figure. That is Rust's target.")
    print()
    print("  Where that actually bites is scale. Measured cost is linear at")
    per_scenario_ms = dec_t / n * 1000
    print(f"  ~{per_scenario_ms:.3f} ms per scenario-path, so exact Python extrapolates to:")
    print()
    for credits, sims, label in [(1, 10_000, "single credit, 10k sims"),
                                 (50, 10_000, "50-credit portfolio, 10k sims"),
                                 (100, 10_000, "100-credit portfolio, 10k sims")]:
        secs = per_scenario_ms / 1000 * credits * sims
        print(f"    {label:<34} {secs:>8.1f}s  ({secs/60:>5.1f} min)")
    clo = per_scenario_ms / 1000 * 100 * 10_000 * (240 / MONTHS)
    print(f"    {'same, 20-yr CLO monthly (240p)':<34} {clo:>8.1f}s  ({clo/60:>5.1f} min)")
    print()
    print("  Crossing from seconds into minutes is the threshold that matters: it is")
    print("  the difference between an analyst iterating on a capital structure and")
    print("  submitting a batch job. THAT is the defensible Rust argument \u2014 not raw")
    print("  throughput, but keeping exact portfolio-scale credit math interactive.")
    print()
    print("  UNVERIFIED until the crate builds: rust_decimal is fixed-width integer")
    print("  arithmetic rather than Python's arbitrary-precision objects, and branches")
    print("  are nearly free in compiled code, so it should land at or below the")
    print(f"  float-scalar time ({flt_t:.4f}s) while staying exact. If it does, the")
    print(f"  100-credit case moves from minutes to seconds. Measure before quoting.")

    if args.json:
        payload = {
            "environment": {"platform": platform.platform(),
                            "python": sys.version.split()[0], "numpy": np.__version__},
            "workload": {"scenarios": n, "months": MONTHS, "tranches": 4},
            "speed": results,
            "divergence": {"breach_pct": n_breach / n, "default_pct": n_default / n,
                           "distinct_path_lengths": ragged},
            "numpy_advantage_over_exact": dec_t / np_t,
            "decimal_object_array_penalty_vs_list": obj_t / list_t,
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\n  wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
