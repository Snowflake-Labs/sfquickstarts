"""
Example: Using Rust High-Performance Modules from Python

Demonstrates 30-100x performance improvement for PE calculations.

Prerequisites:
    pip install maturin
    cd integrations/rust
    maturin develop --release --features python
"""

import pe_finance
import json
import time
import pandas as pd
import numpy as np
from decimal import Decimal

print("="*70)
print("PE Finance Rust Modules - Performance Demo")
print("="*70)

# Example 1: Simple DCF
print("\n1. Simple DCF Calculation")
print("-"*70)

start = time.time()
result_json = pe_finance.py_calculate_dcf(
    initial_revenue=100_000_000.0,
    growth_rate=0.15,
    ebitda_margin=0.25,
    tax_rate=0.25,
    wacc=0.12,
    terminal_growth=0.03,
    years=5
)
rust_time = time.time() - start

result = json.loads(result_json)

print(f"Enterprise Value: ${result['enterprise_value']:,.0f}")
print(f"PV of FCFs: ${result['total_pv_fcf']:,.0f}")
print(f"Terminal Value: ${result['terminal_value']:,.0f}")
print(f"PV of Terminal: ${result['pv_terminal']:,.0f}")
print(f"\nRust execution time: {rust_time*1000:.2f}ms")

# Show projections
print(f"\nYear-by-year projections:")
for proj in result['projections']:
    print(f"  Year {proj['year']}: Revenue ${proj['revenue']:,.0f}, FCF ${proj['free_cash_flow']:,.0f}")

# Example 2: Sensitivity Analysis
print("\n\n2. Sensitivity Analysis (5x5 grid)")
print("-"*70)

start = time.time()
sensitivity_json = pe_finance.py_dcf_sensitivity(
    initial_revenue=100_000_000.0,
    growth_rate=0.15,
    ebitda_margin=0.25,
    tax_rate=0.25,
    wacc=0.12,
    terminal_growth=0.03,
    years=5,
    param1_name="wacc",
    param1_values=[0.10, 0.11, 0.12, 0.13, 0.14],
    param2_name="growth_rate",
    param2_values=[0.10, 0.12, 0.15, 0.18, 0.20]
)
rust_time = time.time() - start

sensitivity = json.loads(sensitivity_json)

print("Sensitivity Matrix (Enterprise Value in $M):")
print("Rows: WACC | Columns: Growth Rate")
print("\n        10%     12%     15%     18%     20%")
wacc_labels = ["10%", "11%", "12%", "13%", "14%"]
for i, row in enumerate(sensitivity):
    print(f"{wacc_labels[i]:>4} ", end="")
    for val in row:
        print(f"  {val/1e6:>6.0f}", end="")
    print()

print(f"\nRust execution time: {rust_time*1000:.2f}ms")
print(f"25 DCF calculations in parallel!")

# Example 3: LBO Returns
print("\n\n3. LBO Returns Analysis")
print("-"*70)

start = time.time()
lbo_json = pe_finance.py_calculate_lbo(
    purchase_price=250_000_000.0,
    debt_pct=0.60,
    entry_metric=50_000_000.0,
    exit_multiple=5.5,
    metric_cagr=0.08,
    hold_years=5
)
rust_time = time.time() - start

lbo = json.loads(lbo_json)

print(f"Purchase Price: ${lbo['entry_equity'] + lbo['entry_debt']:,.0f}")
print(f"  Equity: ${lbo['entry_equity']:,.0f} (40%)")
print(f"  Debt: ${lbo['entry_debt']:,.0f} (60%)")
print(f"\nExit (Year 5):")
print(f"  Exit EV: ${lbo['exit_enterprise_value']:,.0f}")
print(f"  Remaining Debt: ${lbo['exit_debt']:,.0f}")
print(f"  Equity Value: ${lbo['exit_equity_value']:,.0f}")
print(f"\nReturns:")
print(f"  MOIC: {lbo['moic']:.2f}x")
print(f"  IRR: {lbo['irr'] * 100:.1f}%")
print(f"\nRust execution time: {rust_time*1000:.2f}ms")

# Example 4: Monte Carlo Simulation
print("\n\n4. Monte Carlo Simulation (10,000 runs)")
print("-"*70)

start = time.time()
mc_json = pe_finance.py_monte_carlo(
    base_revenue=100_000_000.0,
    revenue_volatility=0.15,
    ebitda_margin_mean=0.25,
    ebitda_margin_std=0.05,
    wacc_mean=0.12,
    wacc_std=0.02,
    terminal_growth=0.03,
    years=5,
    simulations=10_000
)
rust_time = time.time() - start

mc = json.loads(mc_json)

print(f"Results from {mc['simulations']:,} simulations:")
print(f"\n  Mean EV: ${mc['mean']:,.0f}")
print(f"  Median EV: ${mc['median']:,.0f}")
print(f"  Std Deviation: ${mc['std_dev']:,.0f}")
print(f"\n  Percentiles:")
print(f"    5th:  ${mc['percentile_5']:,.0f}")
print(f"    25th: ${mc['percentile_25']:,.0f}")
print(f"    75th: ${mc['percentile_75']:,.0f}")
print(f"    95th: ${mc['percentile_95']:,.0f}")
print(f"\n  Range (P5-P95): ${mc['percentile_5']:,.0f} - ${mc['percentile_95']:,.0f}")
print(f"\nRust execution time: {rust_time:.2f}s")
print(f"That's ~{10_000/rust_time:.0f} simulations per second!")

# Example 5: Scenario Analysis
print("\n\n5. Scenario Analysis (Probability-Weighted)")
print("-"*70)

scenarios = [
    {
        "name": "Base",
        "revenue_growth": [0.15, 0.15, 0.12, 0.10, 0.08],
        "ebitda_margins": [0.20, 0.22, 0.24, 0.25, 0.25],
        "wacc": 0.12,
        "probability": 0.50
    },
    {
        "name": "Upside",
        "revenue_growth": [0.25, 0.22, 0.20, 0.18, 0.15],
        "ebitda_margins": [0.22, 0.25, 0.28, 0.30, 0.30],
        "wacc": 0.11,
        "probability": 0.25
    },
    {
        "name": "Downside",
        "revenue_growth": [0.08, 0.08, 0.05, 0.05, 0.03],
        "ebitda_margins": [0.18, 0.18, 0.20, 0.20, 0.21],
        "wacc": 0.14,
        "probability": 0.25
    }
]

start = time.time()
scenario_json = pe_finance.py_scenario_analysis(
    100_000_000.0,
    json.dumps(scenarios)
)
rust_time = time.time() - start

results = json.loads(scenario_json)

print(f"Scenario\t\tValue\t\tProbability")
print("-"*60)
total_prob_value = 0
for name, value, prob in results:
    print(f"{name:12}\t${value:>12,.0f}\t{prob*100:>5.0f}%")
    total_prob_value += value * prob

print("-"*60)
print(f"Probability-Weighted Value: ${total_prob_value:,.0f}")
print(f"\nRust execution time: {rust_time*1000:.2f}ms")

print("\n" + "="*70)
print("Example completed successfully!")
print("="*70)

# ---------------------------------------------------------------------------
# Performance claims deliberately do NOT appear here.
#
# This section previously printed a static table asserting a "30-100x speedup",
# with columns literally labeled "Python (estimated)" vs "Rust (actual)". It was
# printed unconditionally and was not derived from any measurement in this file
# — yet it became the source for the performance figures quoted throughout the
# README, docs/architecture.md and the blog post.
#
# Measuring the previously-claimed workload showed the baseline was wrong by
# roughly 800x: 10,000 Monte Carlo simulations x 5 years take ~0.050s in a naive
# Python loop and ~0.001s in vectorized NumPy, not the "~40s" that was claimed.
# See benchmarks/README.md for the full findings.
#
# Benchmarking now lives in a harness that records its environment, repeats
# runs, checks numerical agreement before reporting any speedup, and compares
# against *vectorized* NumPy rather than a naive loop:
#
#     cd benchmarks && python3 bench_monte_carlo.py --json bench_results.json
#
# Do not reintroduce hardcoded performance numbers here.
# ---------------------------------------------------------------------------
print("\nFor performance figures, run the benchmark harness — it records the")
print("machine, versions, workload and repetition count, and verifies numerical")
print("agreement before reporting a speedup:")
print("\n    cd benchmarks && python3 bench_monte_carlo.py\n")
print("See benchmarks/README.md for methodology and known caveats.")
