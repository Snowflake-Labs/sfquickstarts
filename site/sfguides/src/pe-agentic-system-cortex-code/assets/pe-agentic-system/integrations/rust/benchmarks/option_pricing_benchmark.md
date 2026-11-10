# Additional Option-Pricing Benchmark

Measured on September 11, 2026. This is a new local European-call workload,
not a rerun of the project's DCF kernel or a reproduction of FinanceBench or
NVIDIA's Asian-barrier GPU benchmark. Existing results are unchanged.

## Workload and Validation

Risk-neutral geometric Brownian motion with exact terminal sampling:

```text
terminal = spot * exp((rate - volatility^2 / 2) * maturity
                     + volatility * sqrt(maturity) * normal)
payoff = exp(-rate * maturity) * max(terminal - strike, 0)
```

Spot 100, strike 100, annual rate 5%, volatility 20%, maturity one year,
no dividends. The analytical Black-Scholes call price is 10.450583572185565.
One normal draw per path suffices; there is no 365-step path simulation.
Monte Carlo is used here as a controlled computational workload, not as the
preferred way to price a European call with a closed-form solution.

All 20 cases passed across NumPy, Numba, and Rust: five parameter sets at four
path counts. Tests cover the base case, zero volatility in/out of the money,
expiry, and negative rates. Every payoff is finite, nonnegative, and agrees
pathwise with NumPy at rtol=1e-12 and atol=1e-12. Sample prices must fall within
five sample standard errors of the analytical reference (plus 1e-10 numerical
tolerance). This fixed-seed smoke check is not a full statistical validation suite.

## Results

Median milliseconds per evaluation, seven timing batches per implementation:

| Paths | NumPy kernel | Numba kernel | Rust kernel | NumPy end-to-end | Numba end-to-end | Rust end-to-end |
|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 0.038 | 0.030 | 0.030 | 0.080 | 0.073 | 0.073 |
| 100,000 | 0.524 | 0.497 | 0.477 | 0.948 | 0.905 | 0.864 |
| 1,000,000 | 5.552 | 5.325 | 5.242 | 10.207 | 9.781 | 9.745 |
| 10,000,000 | 59.526 | 53.763 | 53.437 | 113.953 | 105.463 | 107.800 |

Rust's measured speedup over NumPy ranged from 1.06x to 1.29x for the kernel
and 1.05x to 1.10x end-to-end. Numba was close to Rust and slightly faster
end-to-end at 10 million paths. Small differences should not be treated as a
stable ranking from one benchmark session. No large Rust advantage was observed.

## Timing Scope

- Apple M4, macOS 26.6.2 arm64, Python 3.11.6, NumPy 2.4.6, Numba 0.67.0,
  llvmlite 0.49.0, rustc 1.98.1.
- Single-threaded comparisons throughout. This run does not establish parallel
  scaling, GPU performance, or a parallel crossover point.
- NumPy uses in-place ufuncs and a reused output buffer. Numba uses a fused
  serial nopython loop with fastmath disabled. Rust uses a fused serial loop,
  opt-level=3 and target-cpu=native, exposed through a small ctypes interface.
- Kernel timing includes payoff transformation, a common NumPy mean reduction,
  and Python/FFI dispatch. Normal inputs and output buffers are preallocated.
- End-to-end timing also includes generator initialization, NumPy PCG64 normal
  draws, array allocation and release. All implementations use the same generator
  and seed; this does not compare native RNG implementations.
- JIT compilation and Rust build are excluded. Each implementation is warmed;
  implementation order is shuffled per round. Calibration targets 100 ms per
  timing batch, with per-call times retained in JSON along with min/max.
- Synthetic public-model inputs only. No account queries, Snowflake UDF execution,
  AWS deployment, network I/O, validation overhead, or JSON serialization is timed.
- The benchmark Rust kernel is separate from the production financial library.

## Reproduce

Run from this benchmark directory, using the isolated environment created for it:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMBA_NUM_THREADS=1 \
  .venv-options/bin/python bench_option_pricing.py
```

The harness compiles `option_kernel.rs` into `liboption_benchmark.dylib` and
writes `option_pricing_results.json`. The JSON includes raw batch timings,
validation diagnostics, environment, build command, and source hashes.
The ctypes interface is private to this harness and assumes valid contiguous
float64 buffers with matching lengths. The build is currently macOS-specific.

Model reference: https://www.optionseducation.org/advancedconcepts/black-scholes-formula