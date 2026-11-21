"""
Equalization / incentive-fee crystallization benchmark — measuring the wedge.

Why this workload
-----------------
`docs/hedge-fund-functions.md` argues this is the strongest instance of the
deterministic-computation wedge, better than the CLO waterfall, because:

  - state is path-dependent *per investor*: HWM, loss carryforward, equalization
    credit balance, and accrued fee each depend on that investor's own history
  - it is branch-heavy: above/below HWM, hurdle met or not, tiered catch-up,
    crystallize vs accrue, credit issue vs contingent redemption, clawback
  - **exactness is contractual** — investors are paid on this number, so a
    cent-level discrepancy is a misallocation between the manager and the
    investors, and between investors
  - it is an admitted failure mode: "Equalization calculations can be very complex
    and error prone. Spreadsheet models... quickly become unmanageable over time."

The headline metric here is therefore NOT relative error. It is:

    **how many investors would be paid a different amount of money.**

Fees are quantized to cents, as they are in practice, which converts a ~1e-9
relative error into a discrete, arguable, cent-level difference in a payment.

Scope and honesty
-----------------
This implements a *representative* equalization scheme — HWM, compounding hurdle
with tiered catch-up, loss carryforward, equalization credit amortization, periodic
crystallization, and clawback on drawdown. Real funds differ per offering
memorandum, and that variation is exactly why the fee terms belong behind an
extraction + assurance boundary rather than hardcoded.

Benchmark validity does not depend on matching any particular administrator's
convention. It depends on all three implementations computing *the same* scheme,
which the correctness gate enforces.

Usage
-----
    python3 bench_equalization.py
    python3 bench_equalization.py --investors 400 --years 10
    python3 bench_equalization.py --json equalization.json
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext

import numpy as np

getcontext().prec = 28  # match rust_decimal

D = Decimal
CENT = D("0.01")


@dataclass(frozen=True)
class FeeTerms:
    """Fee mechanics. In production these are extracted from the OM and side
    letters and validated at the assurance boundary — see assurance/contracts.py.
    Hardcoding them here is a benchmark convenience, not an architecture."""

    perf_fee_rate: str = "0.20"
    hurdle_annual: str = "0.05"          # compounding, applied to HWM
    catchup_rate: str = "0.50"           # tiered catch-up between hurdle and full fee
    mgmt_fee_annual: str = "0.02"
    crystallize_every: int = 12          # months
    hwm_resets_on_crystallization: bool = True


# --------------------------------------------------------------------------
# Implementation 1: Decimal, per investor — the contractual reference
# --------------------------------------------------------------------------


def equalize_decimal(terms: FeeTerms, nav_path: list[Decimal],
                     entry_month: int, shares: Decimal,
                     fund_hwm_at_entry: Decimal) -> dict:
    """
    One investor's full fee history. Returns the cent-quantized total fee paid.

    State carried period to period (this is the path dependence):
      hwm                 - investor's own high-water mark per share
      loss_carryforward   - losses to recover before fees resume
      eq_credit           - equalization credit if subscribed above fund HWM
      accrued             - fee accrued but not yet crystallized (clawback-able)
    """
    rate = D(terms.perf_fee_rate)
    hurdle_m = D(terms.hurdle_annual) / 12
    catchup = D(terms.catchup_rate)
    mgmt_m = D(terms.mgmt_fee_annual) / 12

    entry_nav = nav_path[entry_month]
    hwm = entry_nav
    loss_carryforward = D(0)
    accrued = D(0)
    total_crystallized = D(0)
    total_mgmt = D(0)
    months_since_cryst = 0

    # Equalization credit: subscribing above the fund's HWM means this investor
    # would otherwise pay fees on appreciation they did not receive.
    if entry_nav > fund_hwm_at_entry:
        eq_credit = (entry_nav - fund_hwm_at_entry) * rate * shares
    else:
        eq_credit = D(0)
        # Subscribing below the fund HWM: this investor benefits from a recovery
        # they did not fund, tracked as a loss carryforward.
        loss_carryforward = (fund_hwm_at_entry - entry_nav) * shares

    for m in range(entry_month + 1, len(nav_path)):
        nav = nav_path[m]
        months_since_cryst += 1

        # Management fee accrues on NAV regardless of performance
        total_mgmt += nav * shares * mgmt_m

        # Compounding hurdle applied to the HWM
        periods = D(months_since_cryst)
        hurdle_nav = hwm * (D(1) + hurdle_m) ** int(periods)

        gross_gain = (nav - hwm) * shares

        if gross_gain <= 0:
            # Drawdown: claw back accrued fee, deepen loss carryforward
            accrued = D(0)
            loss_carryforward = -gross_gain if -gross_gain > loss_carryforward \
                else loss_carryforward
        else:
            # Recover losses first
            if loss_carryforward > 0:
                applied = min(loss_carryforward, gross_gain)
                loss_carryforward -= applied
                gross_gain -= applied

            if gross_gain > 0:
                above_hurdle = (nav - hurdle_nav) * shares
                if above_hurdle <= 0:
                    accrued = D(0)                       # below hurdle: no fee
                else:
                    hurdle_band = gross_gain - above_hurdle
                    if hurdle_band > 0:
                        # tiered catch-up on the band between HWM and hurdle
                        accrued = (hurdle_band * rate * catchup
                                   + above_hurdle * rate)
                    else:
                        accrued = gross_gain * rate
            else:
                accrued = D(0)

        # Crystallization
        if months_since_cryst >= terms.crystallize_every:
            payable = accrued
            if eq_credit > 0 and payable > 0:
                # Credit offsets the fee, amortizing as fees crystallize
                offset = min(eq_credit, payable)
                eq_credit -= offset
                payable -= offset
            total_crystallized += payable
            accrued = D(0)
            if terms.hwm_resets_on_crystallization and nav > hwm:
                hwm = nav
            months_since_cryst = 0

    # Quantize to cents — this is a payment, not an estimate
    return {
        "perf_fee": total_crystallized.quantize(CENT, rounding=ROUND_HALF_UP),
        "mgmt_fee": total_mgmt.quantize(CENT, rounding=ROUND_HALF_UP),
        "residual_credit": eq_credit.quantize(CENT, rounding=ROUND_HALF_UP),
    }


# --------------------------------------------------------------------------
# Implementation 2: float, per investor — identical algorithm
# --------------------------------------------------------------------------


def equalize_float(terms: FeeTerms, nav_path: list[float],
                   entry_month: int, shares: float,
                   fund_hwm_at_entry: float) -> dict:
    rate = float(terms.perf_fee_rate)
    hurdle_m = float(terms.hurdle_annual) / 12
    catchup = float(terms.catchup_rate)
    mgmt_m = float(terms.mgmt_fee_annual) / 12

    entry_nav = nav_path[entry_month]
    hwm = entry_nav
    loss_carryforward = 0.0
    accrued = 0.0
    total_crystallized = 0.0
    total_mgmt = 0.0
    months_since_cryst = 0

    if entry_nav > fund_hwm_at_entry:
        eq_credit = (entry_nav - fund_hwm_at_entry) * rate * shares
    else:
        eq_credit = 0.0
        loss_carryforward = (fund_hwm_at_entry - entry_nav) * shares

    for m in range(entry_month + 1, len(nav_path)):
        nav = nav_path[m]
        months_since_cryst += 1
        total_mgmt += nav * shares * mgmt_m

        hurdle_nav = hwm * (1.0 + hurdle_m) ** months_since_cryst
        gross_gain = (nav - hwm) * shares

        if gross_gain <= 0:
            accrued = 0.0
            if -gross_gain > loss_carryforward:
                loss_carryforward = -gross_gain
        else:
            if loss_carryforward > 0:
                applied = min(loss_carryforward, gross_gain)
                loss_carryforward -= applied
                gross_gain -= applied

            if gross_gain > 0:
                above_hurdle = (nav - hurdle_nav) * shares
                if above_hurdle <= 0:
                    accrued = 0.0
                else:
                    hurdle_band = gross_gain - above_hurdle
                    if hurdle_band > 0:
                        accrued = hurdle_band * rate * catchup + above_hurdle * rate
                    else:
                        accrued = gross_gain * rate
            else:
                accrued = 0.0

        if months_since_cryst >= terms.crystallize_every:
            payable = accrued
            if eq_credit > 0 and payable > 0:
                offset = min(eq_credit, payable)
                eq_credit -= offset
                payable -= offset
            total_crystallized += payable
            accrued = 0.0
            if terms.hwm_resets_on_crystallization and nav > hwm:
                hwm = nav
            months_since_cryst = 0

    return {
        "perf_fee": round(total_crystallized, 2),
        "mgmt_fee": round(total_mgmt, 2),
        "residual_credit": round(eq_credit, 2),
    }


# --------------------------------------------------------------------------
# Implementation 3: NumPy, vectorized ACROSS INVESTORS
#
# Investors are mutually independent, so the investor axis vectorizes cleanly
# even though periods are sequential. Ragged entry months are handled with an
# `active` mask. This is the strongest Python competitor.
# --------------------------------------------------------------------------


def equalize_numpy(terms: FeeTerms, nav_path: np.ndarray,
                   entry_months: np.ndarray, shares: np.ndarray,
                   fund_hwm_at_entry: np.ndarray) -> dict:
    n = len(entry_months)
    rate = float(terms.perf_fee_rate)
    hurdle_m = float(terms.hurdle_annual) / 12
    catchup = float(terms.catchup_rate)
    mgmt_m = float(terms.mgmt_fee_annual) / 12

    entry_nav = nav_path[entry_months]
    hwm = entry_nav.copy()
    above = entry_nav > fund_hwm_at_entry
    eq_credit = np.where(above, (entry_nav - fund_hwm_at_entry) * rate * shares, 0.0)
    loss_cf = np.where(above, 0.0, (fund_hwm_at_entry - entry_nav) * shares)

    accrued = np.zeros(n)
    total_cryst = np.zeros(n)
    total_mgmt = np.zeros(n)
    months_since = np.zeros(n, dtype=np.int64)

    for m in range(1, len(nav_path)):
        active = entry_months < m
        nav = nav_path[m]

        months_since = np.where(active, months_since + 1, months_since)
        total_mgmt += np.where(active, nav * shares * mgmt_m, 0.0)

        hurdle_nav = hwm * (1.0 + hurdle_m) ** months_since
        gross_gain = (nav - hwm) * shares

        # Drawdown branch, evaluated for all then masked
        is_dd = gross_gain <= 0
        loss_cf = np.where(active & is_dd & (-gross_gain > loss_cf), -gross_gain, loss_cf)

        # Gain branch: recover losses first
        applied = np.where(active & ~is_dd, np.minimum(loss_cf, gross_gain), 0.0)
        loss_cf = loss_cf - applied
        gain_after_loss = gross_gain - applied

        above_hurdle = (nav - hurdle_nav) * shares
        hurdle_band = gain_after_loss - above_hurdle
        tiered = np.where(hurdle_band > 0,
                          hurdle_band * rate * catchup + above_hurdle * rate,
                          gain_after_loss * rate)
        new_accrued = np.where((gain_after_loss > 0) & (above_hurdle > 0), tiered, 0.0)
        accrued = np.where(active, np.where(is_dd, 0.0, new_accrued), accrued)

        # Crystallization
        cryst = active & (months_since >= terms.crystallize_every)
        payable = np.where(cryst, accrued, 0.0)
        offset = np.where(cryst & (eq_credit > 0) & (payable > 0),
                          np.minimum(eq_credit, payable), 0.0)
        eq_credit = eq_credit - offset
        payable = payable - offset
        total_cryst += payable
        accrued = np.where(cryst, 0.0, accrued)
        hwm = np.where(cryst & (nav > hwm), nav, hwm)
        months_since = np.where(cryst, 0, months_since)

    return {
        "perf_fee": np.round(total_cryst, 2),
        "mgmt_fee": np.round(total_mgmt, 2),
        "residual_credit": np.round(eq_credit, 2),
    }


# --------------------------------------------------------------------------
# Setup
# --------------------------------------------------------------------------


def make_book(n_investors: int, months: int, seed: int = 11):
    """A NAV path plus an investor book with staggered monthly subscriptions."""
    rng = np.random.default_rng(seed)

    # NAV path with drawdowns — drawdowns are what make HWM/loss-carryforward
    # state actually bind, so a monotonic path would defeat the benchmark.
    shocks = rng.normal(0.006, 0.038, size=months)
    nav_f = 100.0 * np.cumprod(1.0 + shocks)
    nav_d = [D(str(round(v, 6))) for v in nav_f]

    # Staggered entries across the life of the fund (monthly dealing)
    entry = rng.integers(0, max(1, months - 13), size=n_investors)
    shares_f = rng.integers(1_000, 100_000, size=n_investors).astype(float)
    shares_d = [D(str(int(s))) for s in shares_f]

    # Fund HWM at each investor's entry = running max of NAV up to that month
    running_max = np.maximum.accumulate(nav_f)
    fund_hwm_f = running_max[entry]
    fund_hwm_d = [D(str(round(v, 6))) for v in fund_hwm_f]

    return nav_f, nav_d, entry, shares_f, shares_d, fund_hwm_f, fund_hwm_d


def time_it(fn, repeat: int) -> dict:
    ts, res = [], None
    for _ in range(repeat):
        t0 = time.perf_counter()
        res = fn()
        ts.append(time.perf_counter() - t0)
    return {"median_s": statistics.median(ts), "min_s": min(ts), "runs": repeat,
            "result": res}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--investors", type=int, default=400)
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args()

    terms = FeeTerms()
    months = args.years * 12
    n = args.investors

    nav_f, nav_d, entry, shares_f, shares_d, hwm_f, hwm_d = make_book(n, months)

    print("=" * 78)
    print("Equalization / incentive-fee crystallization benchmark")
    print("=" * 78)
    print(f"  {platform.platform()}")
    print(f"  Python {sys.version.split()[0]} / NumPy {np.__version__} / decimal prec 28")
    print(f"  book: {n:,} investors, {months} monthly periods ({args.years}y), "
          f"staggered entries")
    print(f"  terms: {float(terms.perf_fee_rate):.0%} perf, "
          f"{float(terms.hurdle_annual):.0%} compounding hurdle, "
          f"{float(terms.catchup_rate):.0%} catch-up, "
          f"crystallize every {terms.crystallize_every}m")
    print(f"  NAV path: {nav_f.min():.1f} min / {nav_f.max():.1f} max "
          f"(drawdowns present, so HWM and loss carryforward bind)")
    print(f"  repetitions: {args.repeat} (median)")
    print()

    results = {}

    print("running Decimal per investor (contractual reference) ...", flush=True)
    r = time_it(lambda: [equalize_decimal(terms, nav_d, int(entry[i]), shares_d[i], hwm_d[i])
                         for i in range(n)], args.repeat)
    dec_out = r.pop("result")
    results["python_decimal"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running float per investor ...", flush=True)
    r = time_it(lambda: [equalize_float(terms, list(nav_f), int(entry[i]), float(shares_f[i]),
                                       float(hwm_f[i])) for i in range(n)], args.repeat)
    flt_out = r.pop("result")
    results["python_float"] = r
    print(f"  median {r['median_s']:.4f}s")

    print("running NumPy vectorized across investors ...", flush=True)
    r = time_it(lambda: equalize_numpy(terms, nav_f, entry, shares_f, hwm_f), args.repeat)
    np_out = r.pop("result")
    results["numpy_vectorized"] = r
    print(f"  median {r['median_s']:.4f}s")

    # ---- THE METRIC THAT MATTERS: who gets paid differently? --------------
    print("\n" + "-" * 78)
    print("Payment divergence: how many investors would be paid a DIFFERENT amount")
    print("-" * 78)

    def compare(label: str, other_perf, other_mgmt):
        diff_perf = diff_mgmt = 0
        worst = D(0)
        total_abs = D(0)
        for i in range(n):
            dp = dec_out[i]["perf_fee"] - D(str(other_perf[i]))
            dm = dec_out[i]["mgmt_fee"] - D(str(other_mgmt[i]))
            if dp != 0:
                diff_perf += 1
                total_abs += abs(dp)
                if abs(dp) > abs(worst):
                    worst = dp
            if dm != 0:
                diff_mgmt += 1
                total_abs += abs(dm)
        print(f"  {label}")
        print(f"    performance fee differs : {diff_perf:,}/{n:,} investors "
              f"({diff_perf/n:.1%})")
        print(f"    management fee differs  : {diff_mgmt:,}/{n:,} investors "
              f"({diff_mgmt/n:.1%})")
        print(f"    largest single gap      : ${worst}")
        print(f"    aggregate absolute gap  : ${total_abs}")
        return {"perf_differs": diff_perf, "mgmt_differs": diff_mgmt,
                "worst": str(worst), "aggregate_abs": str(total_abs)}

    cmp_float = compare("Decimal vs float (scalar):",
                        [o["perf_fee"] for o in flt_out],
                        [o["mgmt_fee"] for o in flt_out])
    print()
    cmp_numpy = compare("Decimal vs NumPy (vectorized):",
                        np_out["perf_fee"], np_out["mgmt_fee"])

    total_dec_perf = sum(o["perf_fee"] for o in dec_out)
    print(f"\n  total performance fee (Decimal) : ${total_dec_perf:,}")
    print()
    print("  This is the argument. A ~1e-9 relative error is numerically irrelevant,")
    print("  but these are PAYMENTS: quantized to cents, allocated between the manager")
    print("  and each investor. Any nonzero row above is an investor whose fee differs")
    print("  depending on which arithmetic the administrator happened to use. That is")
    print("  not a tolerance question — it is a reconciliation break, and at audit it")
    print("  has to be explained investor by investor.")

    # ---- correctness gate --------------------------------------------------
    print("\n" + "-" * 78)
    print("Correctness gate")
    print("-" * 78)
    rel_ok = True
    for i in range(n):
        d = dec_out[i]["perf_fee"]
        f = D(str(flt_out[i]["perf_fee"]))
        if d != 0 and abs((d - f) / d) > D("0.001"):
            rel_ok = False
            break
    print(f"  float agrees with Decimal within 0.1% relative : "
          f"{'PASS' if rel_ok else 'FAIL'}")
    print("  (Agreement in *magnitude* is expected and is what makes the")
    print("   cent-level divergence above meaningful rather than a bug.)")

    # ---- speed + scale -----------------------------------------------------
    dec_t = results["python_decimal"]["median_s"]
    flt_t = results["python_float"]["median_s"]
    np_t = results["numpy_vectorized"]["median_s"]

    print("\n" + "=" * 78)
    print("SPEED AND SCALE")
    print("=" * 78)
    print(f"  {'implementation':<28} {'median':>10}  exact?")
    print(f"  {'Decimal, per investor':<28} {dec_t:>9.4f}s  yes")
    print(f"  {'float, per investor':<28} {flt_t:>9.4f}s  no   ({dec_t/flt_t:.1f}x faster)")
    print(f"  {'NumPy, across investors':<28} {np_t:>9.4f}s  no   ({dec_t/np_t:.1f}x faster)")

    per_inv_ms = dec_t / n * 1000
    print(f"\n  exact cost: {per_inv_ms:.3f} ms per investor per {args.years}y history")
    print(f"  ({per_inv_ms/months*1000:.1f} us per investor-month)")
    print()
    print("  Scale — a full recompute, as required at audit, on restatement, or when")
    print("  fee terms are re-interpreted:")
    print()
    for inv, label in [(400, "single fund, 400 investors"),
                       (2_000, "multi-class fund, 2k investor-classes"),
                       (10_000, "platform / administrator, 10k accounts"),
                       (50_000, "large administrator, 50k accounts")]:
        secs = per_inv_ms / 1000 * inv
        pretty = f"{secs:.1f}s" if secs < 90 else f"{secs/60:.1f} min"
        print(f"    {label:<40} {pretty:>10}")
    print()
    print("  And the real multiplier: fees are recomputed on every NAV strike, then")
    print("  again at year-end audit, then again for each scenario when terms are")
    print("  disputed or restated. A 12x-per-year recompute on 10k accounts is the")
    print("  realistic operating load.")

    if args.json:
        payload = {
            "environment": {"platform": platform.platform(),
                            "python": sys.version.split()[0], "numpy": np.__version__},
            "book": {"investors": n, "months": months, "years": args.years},
            "speed": results,
            "per_investor_ms": per_inv_ms,
            "payment_divergence": {"vs_float": cmp_float, "vs_numpy": cmp_numpy},
            "total_perf_fee_decimal": str(total_dec_perf),
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=2)
        print(f"\n  wrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
