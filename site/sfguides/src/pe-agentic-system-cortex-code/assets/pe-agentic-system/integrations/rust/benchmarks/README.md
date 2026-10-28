# Monte Carlo Benchmark — Methodology and Findings

Replaces the estimated performance figures previously hardcoded as a print
statement in `integrations/rust/examples/python_usage.py:201-222`, where the
columns were explicitly labeled `"Python (estimated)"` and `"Rust (actual)"`.

**Status: the Rust half is still unmeasured.** The crate has never been compiled
in this repo — no `Cargo.lock`, no `target/`, no `.wasm`. The Python baselines
below are measured. Until `cargo`/`maturin` is available and the build step runs,
no speedup figure of any kind should appear in the abstract, the blog, or the
README.

---

## Headline finding: the published baseline is wrong by ~800x

The blog states:

> Running 10,000 Monte Carlo simulations in Python can take 40 seconds — an
> eternity in production. Running the same code in Rust? 1.2 seconds. That's a
> 33x speedup.

Measured, on the exact workload from `monte_carlo.rs` `test_monte_carlo()`
(10,000 simulations x 5 years):

| Implementation | Median | vs the claimed 40s |
|---|---|---|
| Naive Python loop | **0.050 s** | ~800x faster than claimed |
| Vectorized NumPy | **0.001 s** | ~40,000x faster than claimed |

Scaling is linear and stable across three orders of magnitude:

| Simulations | Naive loop | Vectorized NumPy | NumPy advantage |
|---|---|---|---|
| 10,000 | 0.050 s | 0.001 s | 49.0x |
| 100,000 | 0.490 s | 0.011 s | 43.7x |
| 1,000,000 | — | 0.158 s | — |

Two consequences, both fatal to the current framing:

1. **The 40-second baseline is not reproducible.** Reaching 40 s would require
   roughly 8 million simulations with the naive loop, or on the order of 250
   million with NumPy — not 10,000. The published number is off by a factor of
   ~800 against the slowest reasonable Python implementation.

2. **At the stated workload, the claimed Rust time would be a 1,200x
   regression.** Vectorized NumPy finishes 10,000 simulations in about 1
   millisecond. The blog's "Rust: 1.2 seconds" is ~1,200x *slower* than the
   Python baseline it is being credited with beating. Whatever 1.2 s measured, it
   was not this workload — and Rust cannot show a meaningful win against a 1 ms
   baseline, because PyO3 marshalling plus the `serde_json` serialization of the
   result (`lib.rs:163-175`) would occupy a large fraction of the budget.

The speedup claim is therefore not merely unverified. At the workload as
described, it is inverted.

## Why the naive baseline must not be quoted

NumPy alone accounts for a 44-49x speedup over the naive loop. Benchmarking Rust
against a naive Python loop silently credits that entire factor to Rust. A
"30-100x vs Python" claim is almost exactly what you get from vectorizing
*Python* and never touching Rust — which is why this comparison will not survive
its first question from an audience that writes numerical code.

The harness reports both baselines side by side and labels which to quote.

## Where Rust genuinely helps

The Monte Carlo kernel is the weakest case for Rust in this codebase, because
NumPy already vectorizes it near memory bandwidth. Stronger arguments, worth
measuring instead:

- **Decimal-correct money paths.** `dcf.rs` and `lbo.rs` use `rust_decimal`.
  Python's `decimal` module is *very* slow and does not vectorize at all, so a
  decimal-exact DCF or LBO is a real Rust win. This is the honest performance
  story: Rust makes *exactness* affordable, not floats faster.
- **Path-dependent, branch-heavy logic** — debt waterfalls, covenant tests,
  tiered carry — which resists vectorization because each period depends on the
  last. `calculate_waterfall` in `lbo.rs` is the natural candidate.
- **WASM portability**, i.e. running the same audited kernel client-side and
  server-side from one source of truth. This is a *correctness and provenance*
  argument, not a speed one.

Recommendation: retarget the benchmark at decimal-exact DCF/LBO, and drop the
Monte Carlo speedup claim entirely.

## Retargeted benchmark: decimal-exact DCF (`bench_decimal_dcf.py`)

Since Monte Carlo is Rust's weakest case here, the benchmark was retargeted at the
decimal money path, where the argument is *exactness*, not speed. Measured on the
same machine (macOS 26.6.2 arm64, Python 3.11.6, NumPy 2.4.2, decimal precision 28
to match `rust_decimal`), WACC x growth sensitivity grid, median of 3-5 reps:

| Grid | DCFs | Python `Decimal` (exact) | Python `float` | NumPy (vectorized) | Cost of exactness |
|---|---|---|---|---|---|
| 15x15 | 225 | 0.0012 s | 0.0002 s | <0.0001 s | 5.9x |
| 40x40 | 1,600 | 0.0129 s | 0.0015 s | 0.0001 s | 8.7x |
| 80x80 | 6,400 | 0.0357 s | 0.0060 s | 0.0001 s | 6.0x |

### Finding 1 — exactness costs only ~6-9x in Python, not 30-100x

This bounds the *entire* opportunity for `rust_decimal`. If Rust made decimal
arithmetic free, the ceiling against Python decimal is roughly an order of
magnitude on this workload — nowhere near "30-100x." The withdrawn claim is not
recoverable by switching workloads; it was simply too large.

Note also that vectorized NumPy float is **~350x faster** than Python decimal at
the 80x80 grid. So a Rust decimal kernel will very likely be *slower* than NumPy
float. That is the correct outcome and should be stated plainly: Rust is not
competing on float throughput, it is making exact arithmetic cheap enough to use
by default.

### Finding 2 — float and decimal genuinely disagree, by cents

Worst divergence between the decimal and float implementations on identical
inputs, same operation order:

| Grid | Worst absolute divergence | Relative error |
|---|---|---|
| 15x15 | **$0.2488** | 8.13e-10 |
| 40x40 | **$0.3889** | 1.02e-09 |
| 80x80 | **$0.4206** | 9.88e-10 |

Concretely, at WACC 9.71% and growth 14.29%: decimal gives
**$305,935,374.198877**, float gives **$305,935,373.950073** — a 25-cent gap on a
$306M enterprise value. NumPy diverges identically, confirming this is
representation error rather than an implementation difference.

**This is the real argument, and it is not about the size of the error.** A ~1e-9
relative error is numerically irrelevant to the valuation. It is operationally
expensive anyway, because reconciliation against an audited model is pass/fail
rather than tolerance-based: an IC deck that disagrees with the underlying
spreadsheet by any amount costs an analyst an afternoon establishing which one is
correct, and does it every time the model is rerun. Decimal eliminates that
category of question instead of shrinking it.

That is a *governance and audit* argument, which is far stronger for this audience
than a speed claim — and unlike the speed claim, it is measured and reproducible
today without a Rust build.

### What Rust still has to prove

The claim that survives is narrow and honest:

> `rust_decimal` closes the ~6-9x exactness penalty measured above, making
> decimal-exact valuation the default rather than a performance compromise.

Unverified until the crate builds. The upside is bounded by the table above, so
set expectations at "roughly an order of magnitude against Python decimal," and
expect to lose to NumPy float — which is not the comparison that matters.

---

## Building `pe_finance` (required for the Rust columns)

**Quickest path — use the script:**

```bash
cd integrations/rust
./build.sh --test        # build, install, run cargo tests + parity suite
```

**Manual, if you prefer:**

```bash
# 1. Rust toolchain, if absent
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
export PATH="$HOME/.cargo/bin:$PATH"

# 2. maturin
python3 -m pip install maturin

# 3. Build with the python feature, then install the wheel
cd integrations/rust
python3 -m maturin build --release --features python
python3 -m pip install --force-reinstall target/wheels/pe_finance-*.whl

# 4. Verify
python3 -c "import pe_finance; print(pe_finance.py_dcf_exact('100000000','0.10','0.25','0.25','0.05','0.10','0.12','0.03',5))"
```

### Four gotchas, each of which cost real time

1. **`export PATH="$HOME/.cargo/bin:$PATH"`.** rustup does not always modify your
   PATH, and will not have at all if installed with `--no-modify-path`.
2. **maturin may have no console script.** `maturin` can be "command not found"
   while `python3 -m maturin` works. Use the module form.
3. **`--features python` is mandatory.** `Cargo.toml` has `[features] default = []`,
   so a plain `cargo build` yields a library with no Python module inside it —
   `import pe_finance` then fails at *runtime* with no build error to explain why.
4. **`maturin develop` needs an active virtualenv** and fails outside one. Use
   `maturin build` plus `pip install` of the wheel with a system Python.

Also note: `Cargo.toml:57-59` carries a `[tool.maturin]` table, which is a
`pyproject.toml` section that cargo ignores. `integrations/rust/pyproject.toml` is
the file maturin actually reads.

### Use the string entry points for money

`py_dcf_exact` and `py_parity_evaluate` take and return **strings**. The legacy
`py_calculate_dcf`, `py_calculate_lbo`, `py_monte_carlo` etc. take `f64` and corrupt
monetary inputs before the decimal engine runs — 9 of 11 realistic money literals do
not survive an f64 round trip. They are retained for compatibility only. See
`CLAIMS.md` §1.9 and `tests/test_decimal_parity.py` class 1.

### Without the build

Every harness runs without Rust and reports the Python baselines, skipping the Rust
column with a reason. The two cross-language parity tests skip rather than fail, so
**a green test run does not imply parity was checked** — confirm with:

```bash
python3 -m pytest tests/test_decimal_parity.py -q   # expect 37 passed, 0 skipped
```

If it says `32 passed, 5 skipped`, the extension is not installed and every
cross-language assertion was silently skipped.

---

## Equalization / incentive fees (`bench_equalization.py`) — the wedge is CORRECTNESS, not speed

Built to prove the performance wedge on the function where exactness is
contractual. It proved something else, and the honest result kills most of the
remaining Rust performance argument while making the correctness argument
much stronger.

400 investors, 120 monthly periods, staggered entries, 20% performance fee with a
5% compounding hurdle, 50% catch-up, per-investor HWM, loss carryforward,
equalization credits, annual crystallization, clawback on drawdown. Fees quantized
to cents, as real payments are.

| Implementation | 400 inv | 2,000 inv | Exact? |
|---|---|---|---|
| Python `Decimal`, per investor | 0.0257 s | 0.1264 s | yes |
| Python `float`, per investor | 0.0102 s (2.5x) | 0.0563 s (2.2x) | no |
| NumPy, vectorized across investors | 0.0026 s (10x) | 0.0057 s (22x) | no |

Linear at **0.063-0.064 ms per investor per 10-year history** (~0.5 µs per
investor-month), stable across scales.

### Finding 1 — there is no performance wedge here. At all.

| Book | Exact Python |
|---|---|
| single fund, 400 investors | 0.03 s |
| multi-class fund, 2k investor-classes | 0.13 s |
| platform/administrator, 10k accounts | 0.6 s |
| large administrator, 50k accounts | **3.2 s** |

A large administrator's entire book recomputes in about **three seconds** in exact
Python. Even at a 12x-per-year recompute cadence there is no interactivity
threshold to cross and nothing for Rust to rescue. The hypothesis in
`docs/hedge-fund-functions.md` §3 — that investor x series x period combinatorics
would push this into minutes — is **refuted**. The per-path cost is ~2x lower than
the credit waterfall *and* the path count is far smaller than assumed, because a
fund has hundreds of investors, not hundreds of thousands.

Taken with the earlier benchmarks, the picture is now consistent: **exact Python is
fast enough for every workload measured here except the 200-obligor CLO on monthly
periods (~18 min).** That single case is the only surviving performance argument.

### Finding 2 — but 28% of investors would be paid a different amount

This is the result that matters, and it is far stronger than any speedup.

| Metric | 400 inv | 800 inv | 2,000 inv |
|---|---|---|---|
| Performance fee differs (decimal vs float) | **113 (28.2%)** | 224 (28.0%) | 588 (29.4%) |
| Management fee differs | 2 (0.5%) | — | — |
| Largest single gap | $0.03 | — | — |
| Aggregate absolute gap | $1.27 | — | — |
| Total performance fee computed | $232,135,786.37 | — | — |

NumPy diverges from decimal on **exactly the same 113 investors** as scalar float,
confirming representation error rather than an implementation difference.

The relative error is ~1e-9 and numerically irrelevant. That is the point. These are
**payments**, quantized to cents and allocated between the manager and each
investor. Roughly **three in ten investors receive a different fee depending on
which arithmetic the administrator happened to use** — not an approximation to be
tolerated but a reconciliation break that has to be explained investor by investor
at audit. Absolute amounts are small ($1.27 aggregate on $232M of fees); the cost is
not the money, it is the investigation, the restatement risk, and the credibility.

This is the cleanest available answer to "why not just use float?", and it needs no
Rust to make the case — it is a property of decimal versus binary floating point.

### What this does to the Rust argument

**Removes:** speed. Nothing here is slow. Cython and Numba are irrelevant too, since
there is no bottleneck to accelerate.

**Leaves:**
1. **Exactness by construction** in a compiled kernel, with a declared rounding
   policy at every money boundary — the property that eliminates the 28%.
2. **One audited kernel, three deployment targets** — server, Snowflake UDF, and
   browser via WASM. Cython and Numba cannot reach the browser at all. One
   implementation to validate rather than three.

Both are correctness and governance arguments. Neither is a performance argument.
The session should say so.

---

## The wedge: exact portfolio-scale credit math (`bench_credit_waterfall.py`)

The first two benchmarks were unkind to Rust: NumPy vectorizes both cleanly. So
this one went hunting for a workload where NumPy *cannot follow* — a multi-tranche
leveraged credit schedule with cash sweep, covenant tests, PIK toggle, revolver
draws, and early default. 2,000 scenarios x 60 monthly periods x 4 tranches, with
80.5% of scenarios breaching a covenant, 24.6% defaulting early, and 55 distinct
path lengths. Decimal and NumPy agree on the default flag for 2,000/2,000 paths.

| Implementation | Median | vs exact | Exact? |
|---|---|---|---|
| Python `Decimal`, scalar | 0.2715 s | — | yes |
| Python `float`, scalar | 0.1323 s | 2.1x | no |
| NumPy float, vectorized + masked | 0.0044 s | **61x** | no |

### The hypothesis was partly refuted — say so

Branch divergence does **not** stop NumPy. Even at 80% breach and 55 ragged path
lengths it still wins by 61x. Its advantage did fall from ~350x on the smooth DCF
grid to 61x here — a genuine ~6x collapse — but that is a dent, not a wall. Masked
all-branch evaluation in C is simply cheaper than branching in Python bytecode.

A second hypothesis also failed: `Decimal` in a NumPy `object` array is **1.76x
faster** than the same arithmetic over a plain list, not slower as expected, because
NumPy's dispatch loop is C while a comprehension pays per-iteration bytecode cost.
The correct statement is narrower: there is no decimal dtype, so exact math gets no
SIMD, no contiguous-buffer arithmetic, and no asymptotic gain from array size —
native `float64` is ~20x faster than object-`Decimal` on identical work.

### What the wedge actually is

Not speed. **Admissibility, then scale.**

NumPy buys its 61x by giving up exactness, and for contractual money — sweep
payments, waterfall distributions, covenant compliance certificates — that trade is
not on offer. Vectorization and exactness are mutually exclusive in NumPy. So among
*admissible* implementations there is exactly one Python baseline, and it is the
0.2715 s figure.

Cost is linear at ~0.136 ms per scenario-path, which puts exact Python here:

| Workload | Exact Python |
|---|---|
| single credit, 10k sims | 1.4 s |
| 50-credit portfolio, 10k sims | 67.9 s |
| 100-credit portfolio, 10k sims | **135.7 s (2.3 min)** |
| same, 20-yr CLO monthly (240 periods) | **543 s (9.0 min)** |

Crossing from seconds into minutes is the threshold that matters — it separates an
analyst iterating on a capital structure from an analyst submitting a batch job and
context-switching away. That is the defensible Rust claim: not throughput, but
keeping *exact* portfolio-scale credit math interactive.

**Still UNVERIFIED:** `rust_decimal` is fixed-width integer arithmetic rather than
Python's arbitrary-precision objects, and branches are nearly free in compiled
code, so it should land at or below the float-scalar time (0.1323 s) while staying
exact — moving the 100-credit case from minutes to seconds. Measure before quoting.

### Calibration note

Two bugs were found and fixed while building this, both worth knowing because they
would have produced a confidently wrong benchmark:

1. **Double-annualization.** The EBITDA paths already hold annualized figures, and
   the LTM calculation multiplied by 12 again — understating leverage by 12x
   (0.397x instead of 4.75x) so that *no covenant could ever bind*. The first three
   runs reported 0% breaches and were insensitive to covenant tightness, which is
   what exposed it. A benchmark that silently measures the wrong thing is worse
   than no benchmark.
2. **Insufficient stress.** Even after the fix, positive EBITDA drift plus a
   75-100% cash sweep deleveraged fast enough that nothing breached. `--drift`,
   `--vol`, and `--covenant-open` are now exposed so the divergence rate is
   explicit and reproducible rather than accidental.

---

## Known build blockers

1. **No Rust toolchain** on the current machine (`cargo`, `rustc`, `maturin` all
   absent).
2. **`Cargo.toml` contains a `[tool.maturin]` table** (`Cargo.toml:57-59`). That
   is a `pyproject.toml` section and is not valid Cargo manifest metadata; cargo
   will warn on the unused key and maturin will not read it from there. A correct
   `pyproject.toml` is provided in this directory's parent — use it.
3. **PyO3 is not a default feature.** `[features] default = []`, so a plain
   `cargo build` produces no Python module. The `--features python` flag is
   required.
4. **`monte_carlo.rs` will not benefit from `--release` as much as expected**
   until the per-simulation `thread_rng()` and distribution construction
   (`monte_carlo.rs:49-67`) are hoisted out of the hot loop. Those three
   `Normal::new`/`LogNormal::new` calls currently run once *per simulation*
   rather than once per batch.

## Running it

```bash
# Baselines only — works today, no Rust required
python3 bench_monte_carlo.py

# Larger workloads
python3 bench_monte_carlo.py --sims 100000
python3 bench_monte_carlo.py --sims 1000000 --skip-naive

# Machine-readable output for the record
python3 bench_monte_carlo.py --json bench_results.json
```

To include Rust, from `integrations/rust/`:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # if needed
pip install maturin
maturin develop --release --features python
cd benchmarks && python3 bench_monte_carlo.py --json bench_results.json
```

## Correctness gate

The harness refuses to print a speedup unless the implementations agree
numerically. Because Monte Carlo is stochastic, agreement is checked as relative
error on mean, median, std dev, P5, and P95 against the vectorized reference,
within `--tolerance` (default 10%). If they disagree the script prints the
divergence, suppresses the speedup, and exits non-zero.

The naive port in `bench_monte_carlo.py` deliberately reproduces two quirks of
`simulate_single_dcf`, and they must not be "cleaned up" or the comparison
becomes invalid:

- the lognormal is anchored at `ln(base_revenue)` while `revenue` mutates each
  year, so `growth_shock` is computed against a drifting denominator
  (`monte_carlo.rs:75`);
- a separate WACC is sampled for terminal value (`monte_carlo.rs:92`), distinct
  from the in-loop yearly draws.

Both are arguably modelling bugs. They are out of scope for a benchmark, but they
should be reviewed on their own merits before this kernel is called
institutional-grade.

## What to report if you publish

State all of: machine and OS, Python and NumPy versions, simulation count and
year count, repetition count and that the median is reported, the exact baseline
implementation, and whether the figure is a measurement or an estimate. The
harness prints every one of these and `--json` captures them.

Measured baselines in this document: macOS 26.6.2, arm64, Python 3.11.6,
NumPy 2.4.2, 5 repetitions, median reported.
