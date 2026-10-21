# Claims Register

Single source of truth for every factual claim this project makes. Any number in
the README, blog, abstract, or a slide must appear here with a status, or it must
not be published.

Status vocabulary — use these words literally, never interchangeably:

| Status | Meaning |
|---|---|
| **MEASURED** | Reproduced by a committed script on a recorded machine. Safe to publish with methodology. |
| **UNVERIFIED** | Plausible but never measured here. Do not publish. |
| **REFUTED** | Measurement contradicts it. Remove on sight. |
| **ASPIRATIONAL** | Describes intended design, not current code. Publish only in a roadmap framing. |
| **UNSOURCED** | Third-party assertion with no citation. Cite or cut. |

Last reviewed: 2026-09-09.

---

## 1. Performance

### 1.1 "Running 10,000 Monte Carlo simulations in Python can take 40 seconds" — **REFUTED**

Measured on the exact workload from `monte_carlo.rs::test_monte_carlo` (10,000 sims
x 5 years), macOS 26.6.2 arm64, Python 3.11.6, NumPy 2.4.2, 5 reps, median:

- naive Python loop: **0.050 s**
- vectorized NumPy: **0.001 s**

The claim overstates the baseline by roughly **800x** against the slowest
reasonable Python implementation. Reaching 40 s would take ~8 million simulations
with the naive loop, not 10,000.

Harness: `integrations/rust/benchmarks/bench_monte_carlo.py`.
Detail: `integrations/rust/benchmarks/README.md`.

**Action: delete wherever it appears.**

### 1.2 "Rust runs the same in 1.2 seconds — a 33x speedup" — **REFUTED as stated**

At the stated workload, vectorized NumPy finishes in ~1 ms. A 1.2 s Rust time
would be a **~1,200x regression**, not a 33x win. Whatever 1.2 s measured, it was
not 10,000 simulations of this model. Rust cannot show a meaningful margin against
a 1 ms baseline anyway, because PyO3 marshalling plus `serde_json` serialization of
the result (`lib.rs:163-175`) would consume much of the budget.

**Action: delete. Do not restate with a different multiplier until re-measured.**

### 1.3 "30-100x speedup over pure Python" — **UNVERIFIED, and misleading by construction**

Originated as a static print string in `python_usage.py:201-222`, with columns
labeled `"Python (estimated)"` and `"Rust (actual)"`. Printed unconditionally; not
derived from any measurement. It propagated verbatim into 22 files.

Independently of provenance, the comparison is unsound: **NumPy alone accounts for
44-49x over a naive Python loop** (measured). So "30-100x vs Python" is
approximately what vectorizing Python gets you *without writing any Rust*. Framed
against a naive baseline, the figure credits NumPy's headroom to Rust.

**Action: removed at source. If republished, it must be Rust vs vectorized NumPy.**

### 1.4 Per-operation table (single DCF 50x, sensitivity 40x, LBO 20x) — **UNVERIFIED**

Same static string, same absence of measurement. `bench_monte_carlo.py` currently
covers Monte Carlo only; DCF and LBO have no harness yet.

### 1.5 Where Rust plausibly does win — **partially MEASURED; upside is bounded**

Monte Carlo is the *weakest* case for Rust here, since NumPy vectorizes it to near
memory bandwidth. The benchmark was retargeted at the decimal money path
(`bench_decimal_dcf.py`). Measured, WACC x growth grid, same machine:

| Grid | DCFs | Python `Decimal` | Python `float` | NumPy | Cost of exactness |
|---|---|---|---|---|---|
| 15x15 | 225 | 0.0012 s | 0.0002 s | <0.0001 s | 5.9x |
| 40x40 | 1,600 | 0.0129 s | 0.0015 s | 0.0001 s | 8.7x |
| 80x80 | 6,400 | 0.0357 s | 0.0060 s | 0.0001 s | 6.0x |

**MEASURED: exactness costs only ~6-9x in Python.** This bounds the entire
`rust_decimal` opportunity at roughly one order of magnitude on this workload. The
"30-100x" claim is therefore *not recoverable by changing workloads* — it was
simply too large. Expect Rust decimal to be **slower than NumPy float** (which is
~350x faster than Python decimal at 80x80), and say so: Rust is not competing on
float throughput.

**MEASURED: float and decimal disagree by cents.** Worst divergence $0.2488 /
$0.3889 / $0.4206 across the three grids; relative error ~1e-9. Concretely, at
WACC 9.71%, growth 14.29%: decimal $305,935,374.198877 vs float
$305,935,373.950073 — a 25-cent gap on a $306M enterprise value. NumPy diverges
identically, confirming representation error rather than an implementation bug.

The error is numerically irrelevant and operationally expensive anyway, because
reconciliation against an audited model is pass/fail, not tolerance-based. This is
a **governance argument, not a performance argument**, and it is the strongest
version of the Rust case: *Rust makes exactness affordable*, not floats faster.
It is also measured and reproducible today, without a Rust build.

**Still UNVERIFIED:** that `rust_decimal` closes the 6-9x penalty. Also unmeasured:
branch-heavy path-dependent logic (debt waterfalls, covenant tests, tiered carry)
in `lbo.rs::calculate_waterfall`, which resists vectorization and is the other
plausible win. WASM portability remains a provenance argument, not a speed one.

**Publishable today:** the precision divergence and the 6-9x exactness cost.
**Not publishable:** any Rust speedup figure.

### 1.6 The Rust wedge — **MEASURED baseline; the wedge is admissibility + scale, not speed**

Searched for a workload where NumPy cannot follow, via a multi-tranche leveraged
credit schedule with cash sweep, covenant tests, PIK toggle, revolver draws, and
early default (`bench_credit_waterfall.py`). 2,000 scenarios x 60 monthly periods x
4 tranches; 80.5% breach a covenant, 24.6% default early, 55 distinct path lengths;
decimal and NumPy agree on default flags 2,000/2,000.

| Implementation | Median | vs exact | Exact? |
|---|---|---|---|
| Python `Decimal`, scalar | 0.2715 s | — | yes |
| Python `float`, scalar | 0.1323 s | 2.1x | no |
| NumPy float, vectorized + masked | 0.0044 s | 61x | no |

**Hypothesis partly REFUTED.** Branch divergence does not stop NumPy — it still
wins by 61x at 80% breach. The advantage fell from ~350x (smooth DCF grid) to 61x,
a real ~6x collapse but not a wall: masked all-branch evaluation in C beats Python
branching. A second hypothesis also failed — `Decimal` in a NumPy `object` array is
**1.76x faster** than a plain list, not slower, since NumPy's dispatch loop is C.
Correct narrower statement: no decimal dtype means no SIMD and no asymptotic gain
from size; native `float64` is ~20x faster than object-`Decimal`.

**The actual wedge is admissibility, then scale.** NumPy buys its 61x by giving up
exactness, and for contractual money — sweep payments, waterfall distributions,
covenant compliance certificates — that trade is unavailable. Vectorization and
exactness are mutually exclusive in NumPy, so there is exactly one admissible
Python baseline: 0.2715 s. Linear at ~0.136 ms per scenario-path:

| Workload | Exact Python |
|---|---|
| single credit, 10k sims | 1.4 s |
| 50-credit portfolio, 10k sims | 67.9 s |
| 100-credit portfolio, 10k sims | **2.3 min** |
| same, 20-yr CLO monthly (240 periods) | **9.0 min** |

Seconds-to-minutes is the threshold that matters: iterating on a capital structure
versus submitting a batch job. **Publishable claim:** exact portfolio-scale credit
math currently costs minutes in Python, and that is a workload NumPy cannot address
without abandoning exactness. **Not yet publishable:** that Rust fixes it — expected
to land at or below 0.1323 s while staying exact, but unmeasured.

Two benchmark bugs found and fixed en route, both documented in
`integrations/rust/benchmarks/README.md`: a double-annualization that understated
leverage by 12x and made every covenant unbreachable (0% breaches across three
runs, insensitive to covenant tightness), and insufficient stress calibration.

### 1.7 Cross-checked against published benchmarks — **the speed wedge largely dissolves**

Full analysis in `docs/performance-alternatives.md`. Four findings that change the
Rust argument materially:

**Python's `decimal` is already C.** Verified locally: `_decimal` / libmpdec 2.5.1.
Since Python 3.3 the digit arithmetic is compiled C, so the measured 2.1x (waterfall)
and 6-9x (DCF grid) penalties are **Python object overhead** — allocation,
refcounting, dispatch — not slow decimal math. This caps Rust's realistic decimal
upside well below an order of magnitude. Treat any claim above ~10x as suspect.

**On float math, Cython *is* Rust.** Published 2026 figures: Cython **99-124x, within
10% of Rust** on n-body; Numba **56-135x** from one decorator; NumPy up to 520x;
GraalPy 66x with zero code changes. A Rust float-performance pitch has no answer to
"so is `@njit`." Sources in the analysis doc.

**But decimal is closed to both.** Numba documents that "strings and general Python
objects are largely out of reach" — `Decimal` is a Python object, so Numba cannot
accelerate it at all. Cython removes interpreter overhead around `_decimal` calls but
not the per-object cost, absent hand-binding libmpdec/decNumber in C. **Exact decimal
is the only remaining opening for Rust**, and it is structural rather than a
preference.

**GPU is the worst fit, for three independent reasons.** (a) No decimal dtype exists
on any GPU stack — disqualifying for a workload premised on exactness. (b) SIMT warp
divergence serializes linearly at 32/k throughput, occupancy-invariant, worst case
3.125% utilization; our waterfall has 80.5% breach and 55 distinct path lengths,
near worst case. (c) This machine is an Apple M4 / Metal — no CUDA — and none of
cupy/torch/jax/numba/cython is installed, so any GPU claim would be speculation. GPU
would win on the Monte Carlo DCF, which already runs in ~1 ms and needs no help.

### 1.8 Scale multiplier — **defensible, but must be labelled by product**

Checked against published market structure: BSL CLOs carry **>200 loans**
(Guggenheim), European CLOs **150-200 obligors** (M&G); large PE firms ~80 portfolio
companies (Thoma Bravo), mid-market funds 15-30.

So 100 credits is **conservative for CLO/private-credit analytics** and **too high
for a single mid-market PE fund**. Corrected at the measured 0.136 ms/scenario-path:

| Workload | Exact Python |
|---|---|
| Single deal, IC sensitivity (1 x 10k) | 1.4 s |
| Mid-market PE portfolio (25 x 10k) | 34 s |
| Large PE portfolio (80 x 10k) | 109 s |
| BSL CLO annual (200 x 10k) | 4.5 min |
| BSL CLO 20-yr monthly (200 x 10k x 240p) | **~18 min** |

**Important mismatch to disclose:** the seconds-to-minutes argument belongs to
structured credit and portfolio analytics, **not** to single-deal PE work — where
exact Python is 1.4 s and Rust is irrelevant. The workload where Rust matters is not
the workload the blog leads with.

### 1.9 `rust_decimal` vs Python `Decimal` — **parity suite built; f64 boundary is fatal today**

`tests/test_decimal_parity.py` — 32 passing, 2 skipped pending the Rust build, plus
a 23-case golden fixture at `tests/fixtures/decimal_parity_golden.json`.

`rust_decimal` is 128-bit *fixed* precision (96-bit mantissa, ~28-29 digits, scale
≤28); Python's `Decimal` is arbitrary precision. Upstream
[rust-decimal#471](https://github.com/paupino/rust-decimal/issues/471) documents a
team hitting "ever so slight discrepancies" between a Rust service and a Python
codebase, with no clean reconciliation. Four divergence classes, all now measured:

**Class 1 — f64 boundary corruption. MEASURED, and currently fatal.** Every PyO3
entry point takes `f64` (`lib.rs:31-39`) and converts via
`Decimal::from_f64_retain` (`dcf.rs:58`), so the kernel receives binary-rounded
inputs however exact its internal arithmetic is. **9 of 11 realistic money literals
do not survive an f64 round-trip**, including `0.0775` (a real rate from the credit
benchmark) and `1234567.89`. Only exact binary fractions such as `0.25` survive:

```
0.1        -> 0.1000000000000000055511151231257827021181583404541015625
0.0775     -> 0.07749999999999999944488848768742172978818416595458984375
1234567.89 -> 1234567.88999999989755451679229736328125
```

**"Decimal-perfect precision" is therefore false at the API boundary regardless of
what `rust_decimal` does internally.** The fix is an entry point accepting strings
or scaled integers, never floats. This is a blocking API change, not a tuning issue.

**Class 2 — rounding mode.** Python defaults to `ROUND_HALF_EVEN` (banker's); money
conventions and governing documents generally specify `ROUND_HALF_UP`. `1234.565`
quantizes to `1234.57` or `1234.56` depending on mode — one cent on an ordinary fee,
multiplied by an investor book. Both sides must state the mode explicitly rather
than inherit a library default.

**Class 3 — precision budget.** 96-bit mantissa caps at 29 digits. Realistic money
is comfortable ($1T to the cent is 15 digits), but **compounding intermediates
exceed the scale cap** — verified — so the kernel must quantize at defined points
rather than carrying full scale.

**Class 4 — operation order.** Two findings, one of which corrected my own
assumption:
- Order *sometimes* matters: `(100/13)*7 != (100*7)/13`, differing in the final
  digit. Most orderings agree, which makes this an intermittent failure that passes
  hundreds of values then disagrees on one client's position.
- **The practically important case: a compounding hurdle written with `pow()`
  disagrees with the same hurdle accumulated in a loop** —
  `133.8654676952387217216506905` vs `...906`. `bench_equalization.py` uses the
  `pow` form; a Rust port would naturally loop inside a per-period state machine.
  The contract must specify *which form*, not merely "compound the hurdle."

Corrected along the way: I asserted that `rate/12 * 12` fails to round-trip and that
division order always matters. Both were wrong — Python's correctly-rounded
arithmetic recovers every realistic rate tested, and most orderings agree. Also
`0.12/12 == 0.01` exactly while `0.0775/12` runs to 28 digits, so a parity corpus
must contain both terminating and non-terminating cases or it misses half the risk.

**Publishable today:** the f64 corruption finding and the four divergence classes.
**Still blocked:** any claim that the Rust kernel matches Python, and the phrase
"matches your manual spreadsheet exactly." The two cross-implementation tests fail
with an explicit message rather than skipping silently, so this cannot be forgotten.

### 1.10 Equalization benchmark — **MEASURED: no speed wedge, but 28% of investors paid differently**

`bench_equalization.py`. 400-2,000 investors, 120 monthly periods, staggered
entries, 20% perf fee, 5% compounding hurdle, 50% catch-up, per-investor HWM, loss
carryforward, equalization credits, annual crystallization, clawback. Fees quantized
to cents.

| Implementation | 400 inv | 2,000 inv | Exact? |
|---|---|---|---|
| Python `Decimal` | 0.0257 s | 0.1264 s | yes |
| Python `float` | 0.0102 s (2.5x) | 0.0563 s (2.2x) | no |
| NumPy across investors | 0.0026 s (10x) | 0.0057 s (22x) | no |

Linear at **0.063-0.064 ms/investor/10y**.

**REFUTES my own hypothesis in `docs/hedge-fund-functions.md` §3.** I predicted
investor x series x period combinatorics would push this into minutes. It does not:
a 50,000-account administrator book recomputes in **3.2 s** in exact Python. There
is no interactivity threshold and nothing for Rust to rescue. Per-path cost is ~2x
lower than the credit waterfall and the path count is far smaller than assumed —
funds have hundreds of investors, not hundreds of thousands.

**Consistent picture across all four benchmarks: exact Python is fast enough
everywhere except the 200-obligor CLO on monthly periods (~18 min).** That is the
only surviving performance argument in this project.

**MEASURED and publishable — the real finding:**

| Metric | 400 inv | 800 inv | 2,000 inv |
|---|---|---|---|
| Performance fee differs, decimal vs float | **113 (28.2%)** | 224 (28.0%) | 588 (29.4%) |
| Largest single gap | $0.03 | — | — |
| Aggregate absolute gap | $1.27 | — | — |
| Total perf fee computed | $232,135,786.37 | — | — |

NumPy diverges on **exactly the same 113 investors**, confirming representation
error rather than an implementation bug. Relative error ~1e-9 — numerically
irrelevant, which is the point: these are **payments**, and roughly three in ten
investors receive a different fee depending on which arithmetic the administrator
used. Not a tolerance question; a reconciliation break to be explained investor by
investor at audit. The cost is the investigation and restatement risk, not the
$1.27.

**Effect on the Rust case:** speed is gone as a justification. What remains is
(1) exactness by construction with a declared rounding policy, and (2) one audited
kernel deployable to server, Snowflake UDF, and browser via WASM — which Cython and
Numba cannot do. Both are correctness and governance arguments, not performance
ones.

### 1.11 RUST BUILT AND VALIDATED — all speed claims now MEASURED

Toolchain installed (rustc 1.98.1), crate compiled, wheel built with maturin,
`pe_finance` importable. **12/12 Rust unit tests pass. 37/37 parity tests pass, zero
skipped.**

**The crate had never compiled.** Five `E0599` errors — `powi` requires
`MathematicalOps` in scope in `dcf.rs` (×2) and `lbo.rs` (×3). Fixed by importing the
trait. Every in-crate test had therefore never executed.

**A real money bug was found on first execution.** `lbo::tests::test_waterfall`
failed immediately: `calculate_waterfall` used an *eroding* `remaining` balance as
the pro-rata base, so on the crate's own test case (30%/70% tiers, $300M proceeds,
$100M invested, both non-participating) the Common tier received 70% of the
remaining $210M = $147M instead of 70% of $300M = $210M. **$63,000,000 of
$300,000,000 — 21% of the exit — was silently undistributed.** The crate's own test
asserted full distribution and caught it; it had simply never been run. Fixed:
pro-rata now computes against total exit proceeds, participating tiers share a
post-preference pool, and shortfalls distribute pro-rata to preference claims.

#### Measured performance — every earlier prediction held

**Monte Carlo, 10,000 sims × 5 years:**

| Implementation | Median |
|---|---|
| naive Python | 0.047 s |
| vectorized NumPy | 0.001 s |
| **Rust** | **0.001 s** |

**Rust vs vectorized NumPy: 1.4×.** Rust vs naive Python: 66.5× — inflated by 47.6×
of NumPy headroom, and precisely the mechanism that produced the original bogus
"30-100×". The withdrawn claim of 33× was against a fabricated 40 s baseline.

**Decimal DCF sensitivity grid, 40×40 = 1,600 DCFs:**

| Implementation | Median | Exact? |
|---|---|---|
| Python `Decimal` | 0.0088 s | yes |
| Python `float` | 0.0015 s | no |
| NumPy float | 0.0001 s | no |
| **Rust `rust_decimal`** | **0.0012 s** | **yes** |

- **Rust decimal vs Python decimal: 7.2× faster** — inside the "expect under 10×"
  bound predicted in §1.5 from the libmpdec finding.
- **Rust decimal vs NumPy float: 0.04×** — Rust is ~25× *slower* than inexact NumPy,
  exactly as predicted. Not the comparison that matters.
- **Rust decimal (0.0012 s) beats Python float (0.0015 s).** This is the one clean
  headline available: *exactness at better-than-Python-float speed*.

**Publishable, with methodology: 1.4× on Monte Carlo, 7.2× on decimal DCF. Nothing
resembling 30-100×.**

#### Parity: measured, and the root cause is structural

Raw-intermediate comparison failed on **8 of 23 golden cases** — every one a
division or division-derived value. Root cause, now characterised precisely:

> **Python `Decimal` limits SIGNIFICANT DIGITS (prec = 28). `rust_decimal` limits
> SCALE (≤ 28 decimal places, permitting up to 29 significant digits).**

| Case | Python | Rust |
|---|---|---|
| `100/3` | 28 sig digits, scale 26 | **29 sig digits**, scale 27 |
| `0.0775/12` | 28 sig digits, scale 30 | **26 sig digits**, scale 28 (capped) |

For values ≥ 1 Rust keeps *more* precision; for values < 1 the scale cap costs it
*two significant digits*. Python has no scale-limited mode and `rust_decimal` has no
significant-digit mode, so **no configuration on either side makes raw intermediates
agree.** This is a sharper statement of upstream rust-decimal#471 than the issue
itself contains.

**The resolution, now implemented and passing:** quantize both sides to a declared
scale at defined boundaries — money to the cent, rates to 10 dp — with an explicit
rounding mode. At a declared scale, Rust and Python agree on **all 23 cases** and on
end-to-end DCF. Comparing full-precision intermediates across the two libraries is
not a solvable problem and should not be attempted.

**The f64 signature costs real money.** Same DCF, same inputs, both entry points:

```
string entry point (exact) : $195142043.95369568958535795270
f64 entry point (legacy)   : $195142043.95369570138964715398
divergence                 : $0.0000000118
```

Small here, but arbitrary and input-dependent — and it is pure signature damage,
present before the decimal engine runs. String entry points (`py_dcf_exact`,
`py_parity_evaluate`) added in `parity.rs`; the legacy f64 functions remain for
compatibility and should not be used for anything monetary.

**Safe claim now:** "decimal arithmetic with a declared rounding policy and scale, verified
against a Python reference on a 23-case corpus." **Still not safe:** "matches your
spreadsheet exactly" — that depends on the spreadsheet's own rounding conventions,
which have not been tested.

---

## 2. Build and implementation status

### 2.1 "Production-ready" / "production agentic platform" — **ASPIRATIONAL**

The Rust crate has **never been compiled in this repository**: no `Cargo.lock`,
no `target/`, no `pkg/`, no `.wasm`. `import pe_finance` fails. No Rust toolchain
is installed on the development machine. `RUST_WASM_SUMMARY.md:3` self-describes
as "Complete and Ready to Build" — i.e. written, unbuilt, unverified.

### 2.2 "Agentic" — **ASPIRATIONAL**

No agent loop exists. No planning, no tool selection, no critique or iterative
evaluation, no goal-directed control flow. Actual flow is a hand-sequenced linear
chain in `examples/complete_deal_workflow.ipynb`: extraction → Python DCF →
sensitivity loop → LBO → memo synthesis → table write, with no branching on model
output. The multi-agent chain diagrammed at `docs/architecture.md:91-118` and
claimed at `AGENTS.md:21-24` has no implementation.

This is not a weakness to hide. For high-consequence finance a fixed, auditable
sequence is arguably the *correct* design, and defending that is a stronger
position than borrowing the word "agentic."

**Action: retitle to "AI-powered analytical workflow platform," or build the loop.
Drop "the future of Private Equity is agentic."**

### 2.3 `skills/` directory — **REFUTED (does not exist)**

`AGENTS.md:162-183` and `README.md:107-119` reference `@financial-modeling-skill.md`,
`@due-diligence-skill.md`, `@portfolio-monitoring-skill.md`,
`@advanced-modeling-skill.md`, and a `skills/financial-modeling/SKILL.md` tree.
None exist on disk. Anyone cloning from the blog link hits this immediately.

### 2.4 `integrations/cortex/schema.sql` — **REFUTED (does not exist)**

Referenced at `README.md:124`. The only SQL in the repo is
`examples/reasoning_demo.sql`, which contains no DDL.

### 2.5 Semantic views — **ASPIRATIONAL**

Mentioned at `AGENTS.md:209` and `docs/architecture.md:141`. No implementation.

### 2.6 "Decimal precision, no floating-point errors" — **PARTIALLY REFUTED**

- `dcf.rs`, `lbo.rs`: use `rust_decimal`. Claim holds.
- `monte_carlo.rs`: **plain `f64` throughout** (`:13-22`, `:48-99`). Claim false
  for the Monte Carlo module specifically.
- PyO3 entry points accept `f64` and convert via `Decimal::from_f64_retain`
  (`lib.rs:32`, `dcf.rs:58`), so precision is already lost at the boundary.
- `AGENTS.md:221` states that using floating-point arithmetic for financial
  calculations is forbidden. `monte_carlo.rs` violates the project's own rule.

Float is *correct* for Monte Carlo, statistics, and optimization. The fix is to
state explicit numerical boundaries — decimal for money and accounting, float for
simulation — not to claim decimal everywhere.

### 2.7 WASM "no data egress, no server overhead, decimal-perfect precision" — **OVERSTATED**

WASM is a real portable execution target. It does not by itself provide any of
these three properties; they follow from surrounding architecture, and the third is
contradicted by 2.6. Claim portability; derive the rest from design.

### 2.8 `test_system.py` — **broken**

`test_model_recommendations()` (line 153) references
`PEAgentClient.MODEL_RECOMMENDATIONS`, but the attribute is
`_LEGACY_MODEL_RECOMMENDATIONS` (`openai_compatible_client.py:63`). Raises
`AttributeError`; the file has never run green in its current state.

### 2.9 Cargo/maturin config — **broken**

`Cargo.toml:57-59` contains a `[tool.maturin]` table, which is a `pyproject.toml`
section that cargo ignores. Also `[features] default = []`, so a plain
`cargo build` yields no Python module. Corrected `pyproject.toml` added at
`integrations/rust/pyproject.toml`; build requires `--features python`.

---

## 3. ROI table — all **UNVERIFIED estimates**

Presented in the blog as "the metrics speak for themselves." None is a
measurement. There is no timing instrumentation, no logged run, and no recorded
human baseline anywhere in the repo.

| Claim | Manual | Platform | Status |
|---|---|---|---|
| CIM analysis | 2 h | 15 min | UNVERIFIED — estimate |
| Financial modeling | 4 h | 30 min | UNVERIFIED — estimate |
| IC memo drafting | 8 h | 1 h | UNVERIFIED — estimate |
| Portfolio reporting | 3 days | 30 min | UNVERIFIED — estimate |
| 1k scenario analysis | 5 h | 2 min | UNVERIFIED — estimate; also depends on the unbuilt Rust crate |

**Action:** either label the table "illustrative estimates, not measurements" in
the caption, or instrument the workflow and measure a handful of real runs. The
second is far more valuable and is about a day of work. Do not publish these as
"metrics."

### 3.1 "A typical analyst spends over 3,000 hours a year on grunt work" — **UNSOURCED**

3,000 hours implies roughly 60 hours per week on repetitive tasks alone, every week
of the year. Extraordinary claim, no citation.

**Action: cite a named study or cut.**

### 3.2 "Reclaims the capacity of 1.5 full-time analysts" — **UNSOURCED**

Derived arithmetic on top of 3.1 and the unverified table. Inherits both problems.

### 3.3 "Cut API costs by over 80% by routing to cheap-tier models" — **UNVERIFIED**

No cost telemetry, no before/after token accounting in the repo. Directionally
credible — routing bulk extraction to a smaller model does save most of the spend —
but it is an estimate. Label it as one, or produce the token counts.

---

## 4. Claims that hold up

Publish these freely.

- **Config-driven model routing exists and works as described.**
  `config/models.yaml` implements task → tier → platform → model with
  `family_defaults` fallback. `examples/model_routing_showcase.py` demonstrates it.
  Genuinely the strongest reusable pattern in the codebase.
- **Cortex REST inference is real.** `cortex_client.py:87` posts to
  `/api/v2/cortex/inference:complete`; `AI_COMPLETE` is called directly in
  `examples/reasoning_demo.sql:22-53`.
- **Native Snowflake session-token auth is real.** `cortex_client.py:104` uses
  `session.connection.rest._token`, avoiding external key management. The security
  argument is sound.
- **Snowpark write-back is real.** The notebook persists results to
  `DEAL_ANALYSES`.
- **Rust source for DCF/LBO/Monte Carlo exists** with PyO3 and wasm-bindgen
  bindings and in-crate unit tests. Say "implemented, pending build and
  benchmark" — not "production."
- **The assurance boundary is real and tested.** `assurance/contracts.py`, 25
  passing tests in `tests/test_assurance.py`, live demo in
  `examples/assurance_boundary_demo.py`. Measured: 3 of 5 representative bad
  extractions blocked before reaching the engine, including terminal growth ≥ WACC
  and percentage/ratio confusion.
- **Golden-value DCF test.** `test_system.py:68-89` checks PV of $10M/5yr/12% =
  $36,047,762.34 to within $1.

---

## 5. Modelling issues found while benchmarking

Not claims, but they undercut "institutional-grade" and should be fixed before the
kernel is described that way.

1. **Drifting lognormal denominator** (`monte_carlo.rs:75`). `growth_shock` is
   `sample / revenue - 1.0` where the distribution is anchored at
   `ln(base_revenue)` while `revenue` mutates each year. After year 1 the shock is
   computed against a moving denominator, so the intended volatility is not what
   the model realizes.
2. **Separate terminal WACC draw** (`monte_carlo.rs:92`). An independent WACC is
   sampled for terminal value, uncorrelated with the in-loop draws. Probably
   unintended, and terminal value usually dominates the result.
3. **Per-simulation RNG and distribution construction** (`:49-67`). `thread_rng()`
   and three distribution constructors run once *per simulation* instead of once
   per batch — a large avoidable cost inside the hot loop, and the first thing to
   fix before benchmarking Rust.
4. **No Gordon Growth guard** (`dcf.rs`). `wacc <= g` silently yields a negative
   terminal value. Now blocked at the assurance boundary, but the engine should
   also refuse it defensively.

---

## 6. Published post: claim set as it now stands

The post is `~/Downloads/pe-blog/institutional-grade-financial-ai.md`, rendered to HTML by
`~/Downloads/pe-blog/render_blog.py`. Its differentiating angle is the **verification boundary**, not
decimal-vs-float. Every claim below is either MEASURED here or derived by calling the
code directly at figure-generation time.

### 6.1 The boundary claims — **MEASURED**

| Claim in post | Status | Where it comes from |
|---|---|---|
| Gordon Growth returns a negative terminal value with no exception when g > WACC | **MEASURED** | `dcf.rs`; see 5.4 |
| At a 10 bp spread, terminal value = 1,119x FCF (wacc 12%, fcf $100M) | **MEASURED** | recomputed in `~/Downloads/pe-blog/make_figures.py` |
| Boundary verdicts: clean g<=0.04, warned from g=0.045, blocked from g>=0.12 | **MEASURED** | `cross_boundary()` called live per probe point |
| Five representative extractions: 1 clean, 1 warned (3 warnings), 3 blocked | **MEASURED** | `examples/assurance_boundary_demo.py` through `cross_boundary()` |
| Error codes `ENGINE_INPUT_VIOLATION`, `WACC_BELOW_TERMINAL_GROWTH`, `LOW_EXTRACTION_CONFIDENCE`, `SCHEMA_VIOLATION` | **MEASURED** | the boundary's own output |
| WACC and terminal growth are caller-supplied, not extracted | **MEASURED** | `cross_boundary()` signature, keyword-only |

Note on the clean-zone edge: it ends at `g=0.04` because `terminal_growth_typical`
`(0.00, 0.04)` binds **earlier** than `min_wacc_terminal_spread` `(0.02)`. Do not
describe the clean zone as "spread >= 0.02" — that was wrong in a draft and was fixed.

`min_wacc_terminal_spread` is enforced as a **WARNING inside `cross_boundary()`**
(`contracts.py:517`), not on the bare `DCFAssumptions` model. Instantiating the model
directly bypasses it. A draft of this register nearly recorded a non-existent gap on
that basis.

### 6.2 Claims carried over — status unchanged

- Python `Decimal` significant digits vs `rust_decimal` scale; 8/23 raw mismatches,
  37/37 at declared scale — see 1.9, **MEASURED**. Now framed as the
  research-to-production reproducibility problem.
- `pow()` vs loop-accumulated hurdle (`...905` vs `...906`) and
  `ROUND_HALF_EVEN` vs `ROUND_HALF_UP` on `1234.565` — **MEASURED**. These now carry
  the "quiet failure with pass/fail consequences" argument.
- The three Monte Carlo modelling defects — see section 5 items 1-3, **MEASURED by
  code inspection**, verified against `integrations/rust/src/monte_carlo.rs`:
  drifting lognormal denominator (`sample / revenue - 1.0` with `revenue` reassigned),
  independent terminal WACC draw (second `wacc_dist.sample()`, uncorrelated with the
  path), and per-simulation RNG/distribution construction inside `simulate_single_dcf`.
  The unguarded `(wacc_terminal - terminal_growth)` denominator is item 4.
- $63,000,000 of $300,000,000 (21% of exit) undistributed — see 2.x, **MEASURED**
- Monte Carlo 85x vs naive / 1.76x vs vectorized NumPy, 48.2x of the gap attributable
  to NumPy — see 1.5-1.8, **MEASURED**. This is now the whole of figure 3.
- ~18 min for a 200-obligor monthly CLO; 3.2 s for a 50,000-account fee book; 61x
  NumPy advantage on the branch-heavy waterfall — see 1.6-1.8, **MEASURED**
- WASM portability only, not egress/precision claims — see 2.7, **corrected in post**

### 6.2a Claims REMOVED from the post on editorial direction

These remain MEASURED and true. They were cut because the decimal-vs-float framing was
retired as the differentiating angle, not because they failed verification. Do not
delete them from this register — they are still the evidence base if the angle returns.

- 113/400 investors paid differently, $1.27 on $232,135,786.37 (1.10)
- The `f64` entry-point corruption and the nine-of-eleven money-literal round trip (1.9)
- "Exact decimal in Rust beats inexact float in Python" (0.00125 s vs 0.00140 s)
- The accelerator argument: NumPy has no decimal dtype, Numba cannot handle `Decimal`,
  GPUs have no decimal type (2.x)

### 6.3 Claims deliberately NOT in the post

- The ROI table, "3,000 hours", "1.5 FTEs", "80% API cost reduction" (section 3) —
  all UNVERIFIED or UNSOURCED. Cut entirely.
- Any "30-100x" framing (1.3) — cut.
- "Agentic" as a description of this system — explicitly disclaimed in the post's
  closing section rather than quietly dropped.
- Any decimal-vs-floating-point argument — retired as an angle (6.2a).

### 6.4 Figure integrity

The three figures are generated by `~/Downloads/pe-blog/make_figures.py`, which holds no hardcoded
results. Figures 1 and 2 obtain their zones, verdicts and error codes by **calling
`assurance.contracts.cross_boundary()`**; figure 3 (`fig3_baseline_choice.png`) reads
committed benchmark JSON. A figure therefore cannot silently drift from the code it
depicts. `~/Downloads/pe-blog/md_render.py::audit()` fails the build on any markdown construct it did
not convert, including a bullet swallowed into a paragraph.

Retired figures: `fig1_payment_divergence.png`, `fig2_precision_models.png`,
`fig3_exactness_vs_speed.png` — all deleted with the decimal-vs-float angle.

### 6.5 Voice

The post uses no first person. The system is described in the third person throughout
("the system's Monte Carlo module", not "our Monte Carlo module"). Checked with
`grep -niE "\b(we|our|ours|us)\b"` returning nothing.

### 6.6 Deployment targets — **BUILT AND VERIFIED (2026-09-10)**

An earlier draft claimed three running targets; that was aspirational. Two are now
genuinely built and measured. Verified state:

| Target | Status |
|---|---|
| CPython extension (`pyo3`, feature `python`) | **BUILT, tested, benchmarked** |
| WebAssembly (`wasm-bindgen`, feature `wasm`) | **BUILT and EXECUTING.** `integrations/rust/build_wasm.sh` → `pkg/pe_finance_bg.wasm` (201 KB, from a 584 KB raw artifact). All three `wasm_*` functions execute under node. |
| Snowflake UDF | **still not written** — no `CREATE FUNCTION` DDL, no handler |

Two build prerequisites, both discovered by failing first:

1. `rand 0.8` → `getrandom 0.2` refuses to compile for `wasm32-unknown-unknown` without
   its `js` feature. `Cargo.toml` now scopes that dependency to
   `[target.'cfg(target_arch = "wasm32")'.dependencies]` so native and Python builds are
   untouched.
2. `cargo build` alone produces a `.wasm` with `__wbindgen_placeholder__` imports that
   cannot be instantiated. It must be post-processed by the `wasm-bindgen` CLI **pinned
   to the `Cargo.lock` version** (0.2.128) or loading fails on a schema mismatch.
   `build_wasm.sh` reads the version from `Cargo.lock` and reinstalls the CLI if it
   drifts.

`rayon` compiles for wasm32 and degrades without panicking; `wasm_monte_carlo` returns
results.

**Cross-target parity — MEASURED.** Same DCF, same f64 inputs, two bindings:

```
CPython extension (PyO3)    82205005.98549509729207945944
WebAssembly (wasm-bindgen)  82205005.98549509729207945944
```

Byte-identical, 29 significant digits. Reproduce with
`python3 integrations/rust/verify_wasm_parity.py`.

**Interface asymmetry — MEASURED.** `py_dcf_exact` takes/returns `String`
(`src/lib.rs:94`, `parity::dcf_exact_from_strings` at `src/parity.rs:157`); the three
`wasm_*` functions take `f64` positionally and return a JSON string
(`src/lib.rs:232-284`). A shared implementation does not imply shared interface
guarantees. This is an interface observation, **not** a revival of the retired
decimal-vs-float angle.

### 6.6a Hidden constructor defaults — **NEW FINDING, MEASURED**

`py_calculate_dcf` and `py_dcf_exact` disagree by **+42.5%** on identical economics:

```
py_calculate_dcf(50e6, 0.0625, 0.25, 0.25, 0.125, 0.03125, 5)   82,205,005.98
py_dcf_exact(..., capex="0",    nwc="0",    ...)               117,107,690.09
py_dcf_exact(..., capex="0.05", nwc="0.10", ...)                82,205,005.98  <- identical
```

Cause: `DCFInputs::new_constant_growth` (`src/dcf.rs`) hardcodes
`capex_pct_revenue = dec!(0.05)` and `nwc_pct_revenue = dec!(0.10)`. These are **economic
assumptions injected by a convenience constructor**, invisible in the signature, worth
42% of enterprise value. The kernel agrees with itself once they are stated explicitly.

Safe to publish. Asserted permanently in `verify_wasm_parity.py`, which fails if the two
paths ever diverge with the assumptions stated.

**Recommended fix (not yet done):** make capex and NWC required, or name the constructor
for what it assumes (`new_constant_growth_with_default_capital_intensity`).

### 6.7 Monte Carlo model validation — **MEASURED, 3 of 5 checks still fail**

`tests/test_monte_carlo_validation.py`. The three open defects are committed as
`xfail(strict=True)` so the suite stays green while documenting them, and turns red if the
kernel is fixed without updating the tests. The two that item 1 fixed are now live
assertions. Full suite: **66 passed, 3 xfailed.**

The earlier draft of this section said the "output checks pass" claim was reasoning
rather than measurement. It is now measured.

| Check | Result |
|---|---|
| mean finite and positive | passes |
| percentiles ordered | passes |
| std dev positive | passes |
| no inf/nan | passes |
| year-5 log-sd equals σ√5 | **FAILS** — 0.2020 vs 0.4472 expected |
| terminal rate equals final-period rate | **FAILS** — corr **+0.0055**, expected ~1.0 |
| identical inputs → identical output | **FAILS** — no seed on the public surface |
| no path returns a negative valuation | **FIXED** — was 40 per 120,000, now 0 |
| dispersion not tail-dominated | **FIXED** — sd/mean was 2.17, now 0.41 |
| reported mean stable within its own SE | passes — and passed before the fix too, see below |

**The volatility finding is worse than section 5 item 1 stated.** That entry described a
"drifting denominator." In fact `growth_shock = sample/revenue - 1.0` followed by
`revenue = revenue * (1.0 + growth_shock)` reduces algebraically to `revenue = sample`.
The multiplication cancels exactly. There is **no revenue growth process at all** —
each year is an independent draw anchored at the base year. Correct section 5 item 1
to say this.

**Item 1, the terminal denominator, is FIXED and verified.** `monte_carlo.rs` now floors
the sampled terminal rate at `terminal_growth + MIN_TERMINAL_SPREAD` (0.02), mirroring
`POLICY["min_wacc_terminal_spread"]`. The clamp count is returned as `paths_clamped` so
the intervention is auditable rather than invisible: **0.595% of paths measured against
0.621% analytically** at `wacc ~ N(0.10, 0.02)`, `g = 0.03`. The clamp rate is
configuration-dependent — 0.023% at `N(0.12, 0.02)`. Both benchmark baselines in
`bench_monte_carlo.py` mirror the floor, so the cross-implementation agreement gate still
holds. Verified effect over 120,000 paths:

| | before clamp | after clamp |
|---|---|---|
| negative enterprise values | 40 | **0** |
| `sd/mean` | 2.17 | **0.41** |
| `min/median` | −288.40 | **0.42** |

**A CORRECTION, and it matters more than the fix.** An earlier version of this section
claimed the defect made the mean unstable — "3% to 53% spread, median ~10%" — and that a
stability check would therefore catch it. Measured like-for-like, **that is wrong.**
Comparing the observed range of 6 run means against the estimator's own standard error
gives **1.2× theory before the clamp and 1.0× after** — the check passes in both states.
The reason is that deriving `SE` from a heavy-tailed sample is self-defeating: the tail
inflates `sd`, which inflates `SE`, which inflates the expected range by the same factor
as the observed range. The earlier "5.7×" figure compared the *pre-clamp* observed range
against the *post-clamp* theoretical SE, which is not a like-for-like comparison.

The detectors that do work are `min/median` (sign of the minimum) and `sd/mean`
(dispersion ratio, bounded at 1.0 on a strictly positive quantity — a principled bound,
not a tuned one). `mean/median` does **not** work: 1.110 before against 1.111 after.

Two consequences for the post. First, the stability claim had to be replaced with the
negative-valuation finding, which is both true and more visceral. Second, the
"output-level checks are blind to these defects" framing is **too strong**: *no path
returns a negative valuation* is an output-level check and it catches this defect at once.
The defensible claim is that the output checks the suite **happened to contain** did not.

**Methodological note worth keeping:** the transcription gate first compared kernel and
transcription on the *mean* and failed at 3.1% with a correct transcription. The mean is
too unstable to gate on — the gate was measuring defect four. Comparing medians brings
them within 0.30%. A validation harness needs a statistic robust to the pathology it is
hunting, or it reports its own noise as a finding. That lesson then repeated itself one
level up, in the stability check described above — which is why the correction is recorded
rather than quietly edited out.

**Items 2, 3 and 4 remain open.** There is still no revenue growth process, the terminal
rate is still drawn independently of the path it terminates, and there is still no seed.
The module is **not demo-safe** and the post says so explicitly in its colophon.

### 6.8 Claim-drift automation — **MEASURED, task fires; audit reads NOT verified**

Registered because the post now documents this in "Keeping the numbers honest after
publication," so the operational claims there need the same treatment as the numerical ones.

`COCO_ROUTINE_PE_CLAIM_DRIFT`, cron `0 8 * * MON America/New_York`, state `started`. Prompt
committed at `~/Downloads/pe-blog/claim_drift_prompt.md`. Six artifacts staged to
`USER$.PUBLIC.DEFAULT$:/pe-claims/`.

**VERIFIED.** Task dispatch works. Via `TASK_HISTORY`, one fire `SUCCEEDED`
(2026-09-09 21:55:56 → 21:55:58) and the next is `SCHEDULED` for
2026-09-14 05:00 −07:00, which is Monday 08:00 America/New_York as intended.

**NOT VERIFIED — do not claim.** That the sandbox can actually read the staged files. The
2-second completion is the task dispatching an asynchronous agent run, not the audit
finishing. The fire's thread is not retrievable: `cortex conversations transcript` returns
"not found" for the thread id `doctor` reports. Mitigation rather than proof: Step 0 of the
prompt locates the files with `find` and is instructed to report that the audit **did not
run** if they are absent, so a blind fire cannot emit `NO DRIFT`. First real evidence is
Monday's email.

**Scope correction.** The automation was first offered as "runs the validation checks, the
benchmark, and the figure regeneration." That is **impossible** and the offer was wrong.
Automations run in a Snowflake-managed Linux sandbox with no local filesystem access; this
repo has no git remote (it is not a git repository at all), and `pe_finance` is a compiled
macOS arm64 extension that cannot load on Linux. Scoped down to a text and JSON
cross-artifact consistency audit, which is what the recurring failure actually was.

**`cortex automation doctor` does not work here.** It reads `TASK_HISTORY` without setting a
warehouse, so it returns `firesError: No active warehouse selected` and an empty fire list
even while the task is firing. The post documents the direct `TASK_HISTORY` query instead.

**Account note, and a diagnosis I got wrong.** The CLI resolves
`default_connection_name = "<your connection>"` → account `<your account locator>`, user `<your user>`,
so the automation and workspace stage live there. An interactive session on a second account is
user `<your user>`, whose personal database is `USER$<your user>`. Failing to introspect
`USER$<your user>` from that second account was a **wrong-account** error; it was initially
and incorrectly attributed to the session's read-only `<your read-only role>` role.
The read-only role is real — it is the user's `DEFAULT_ROLE`, inherited because the
connection profile sets `role = ""`, with no Restricted Session Scope involved
(`ACTIVE_RESTRICTED_SESSION_SCOPES` = `[]`) — but it was not the cause.

---

## 7. Pre-publication checklist

- [x] Every number in the abstract and blog traces to a MEASURED row here — see 6.1/6.2
- [x] All REFUTED claims deleted (1.1, 1.2, 2.3, 2.4) — none appear in the post
- [x] ROI table captioned as illustrative estimates, or measured — cut entirely (6.3)
- [x] "3,000 hours" and "1.5 FTEs" cited or cut — cut (6.3)
- [x] "Agentic" resolved — explicitly disclaimed in the post's closing section
- [ ] `skills/` created or references removed
- [x] Rust crate built; benchmark re-run against vectorized NumPy; results recorded
- [ ] `test_system.py` passes
- [x] Numerical boundaries stated explicitly (decimal for money, float for simulation)
- [x] Post's differentiating angle is the verification boundary, not decimal-vs-float
- [x] Deployment-target claim corrected to match built artifacts (6.6)
- [x] Build the WASM target — done, `build_wasm.sh`, cross-target parity byte-identical
- [x] Write the model-validation checks — done, 3 of 5 still fail (6.7)
- [x] Guard `1/(wacc_terminal - g)` in `monte_carlo.rs` — done, `MIN_TERMINAL_SPREAD`,
      verified 40 negative valuations → 0, `sd/mean` 2.17 → 0.41, clamp rate surfaced
- [ ] Re-measure the Monte Carlo benchmark honestly: 5 runs gave 0.93×, 1.1×, 1.6×, 1.9×,
      2.0× vs NumPy. A single figure for a ~1 ms workload is noise; the post now states
      the range and that one run was slower than NumPy
- [ ] Fix `revenue = sample` in `monte_carlo.rs:75-76` — there is no growth process
- [ ] Expose a seed parameter on `py_monte_carlo` so results can be pinned for audit
- [ ] Make capex/NWC required on `new_constant_growth`, or rename it (6.6a)
- [ ] Confirm from Monday's automation email that the sandbox actually read the staged
      files; until then 6.8's audit-reads claim is unverified
- [ ] Correct section 5 item 1: the defect is not a drifting denominator, it is
      `revenue = sample` with the multiplication cancelling
- [ ] Engine-level Gordon Growth guard added defensively in `dcf.rs` (5.4) — currently
      caught only at the assurance boundary, which the post is careful to state
