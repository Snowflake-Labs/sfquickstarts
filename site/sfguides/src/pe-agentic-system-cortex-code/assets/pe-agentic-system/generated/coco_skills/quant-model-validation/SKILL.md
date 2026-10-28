---
name: quant-model-validation
description: "Validate quantitative models and benchmark claims. Use for research parity, simulation diagnostics, NumPy/Numba/Rust comparisons, convergence or backtest review."
---
# Quant Model Validation

## Workflow
1. Pin formulation, calibration data, seed, sampling scheme, numerical tolerance and code/runtime revisions. Establish the benchmark baseline before timing.
2. Inspect `tests/test_monte_carlo_validation.py` and relevant parity tests for known failures and actual coverage. Preserve expected failures; a green harness is not proof that those defects are fixed.
3. Use specification-level invariants, limiting cases, distribution diagnostics, convergence and independent reference calculations. Include known-failing cases to prove the check can detect a defect.
4. For benchmark requests read `integrations/rust/benchmarks/option_pricing_results.json` and its source code. Separate compilation/warmup, RNG, kernel time, orchestration and end-to-end scope. Do not overwrite recorded baselines without approval.
5. For backtests inspect point-in-time availability, survivorship, look-ahead, transaction costs and out-of-sample design. An attractive return is not evidence of unbiased methodology.

## Stopping Points
Stop for missing reference implementations, unresolved specification failures or non-comparable timing scopes. Existing tests/benchmarks are not a general backtesting platform. No strategy promotion, risk-limit override or trading is authorized.

## Output
Validation matrix with passed/failed/unexecuted checks, exact executed commands, scoped measurements, artifacts and remaining model risk.