# Performance Alternatives: Is the Rust Wedge Real?

Sanity-checking the Rust argument against published benchmarks and against the
three alternatives an audience will raise: **Cython**, **Numba/JIT**, and **GPU**.

Conclusion up front: **the Rust *speed* wedge is much narrower than claimed, and on
float math it does not exist at all.** What survives is narrow, defensible, and not
primarily about speed. Details below, with sources.

---

## 1. The finding that caps everything: Python's `decimal` is already C

Verified locally:

```
_decimal (libmpdec) : PRESENT -> Python decimal is a C extension
libmpdec version    : 2.5.1
MAX_PREC            : 999999999999999999
```

Since Python 3.3, `decimal` is `_decimal`, a C implementation of libmpdec (formerly
distributed as `cdecimal`). **The digit arithmetic is already compiled C.**

This invalidates the reasoning behind the earlier framing in this repo, which
assumed Python decimal was slow because it was interpreted. It is not. The measured
penalty — 2.1x vs float on the credit waterfall, 6-9x on the DCF grid — is
**Python object overhead**: allocation, reference counting, method dispatch, and
boxing per intermediate value, not slow decimal math.

Consequence: Rust's realistic upside on decimal is bounded by how much of that
per-object overhead it removes, not by a C-vs-interpreter gap. That is a real gain
(fixed-width 128-bit values on the stack, no allocation, no refcounting) but it is
nowhere near an order of magnitude on arithmetic alone. **Any claim above ~10x on
decimal math should be treated as suspect until measured.**

Source: [Python docs, decimal](https://docs.python.org/3/library/decimal.html);
[Stack Overflow on cdecimal becoming the stdlib decimal in 3.3](https://stackoverflow.com/questions/195116/is-there-a-faster-alternative-to-pythons-decimal).

---

## 2. Cython and Numba: on float math, they *are* Rust

Published figures from a 2026 cross-runtime benchmark ladder:

| Approach | Reported speedup vs pure Python | Note |
|---|---|---|
| CPython upgrade | 1.4x | free |
| Alternative runtimes (PyPy, GraalPy) | 6-66x | GraalPy 66x on spectral-norm, zero code changes |
| Mypyc | 2.4-14x | needs type annotations |
| NumPy vectorization | up to 520x | matrix/array algebra |
| **Numba JIT** | **56-135x** | `@njit`, one decorator |
| **Cython** | **99-124x** | *within 10% of Rust on n-body* |

Sources: [The Optimization Ladder (Çavdar, 2026)](https://cemrehancavdar.com/2026/03/10/optimization-ladder/);
[BSWEN framework summary](https://docs.bswen.com/blog/2026-03-10-python-performance-optimization-ladder/);
[Cython + SIMD (Turner-Trauring)](https://pythonspeed.com/articles/faster-cython-simd/).

**This is fatal to a float-based Rust performance pitch.** Cython lands within 10%
of Rust, and Numba gets 56-135x from a single decorator. If the argument is "Rust is
fast at float math," the correct response from the audience is "so is `@njit`, and I
didn't have to add a build toolchain, a second language, or a PyO3 boundary."

### Where they cannot follow: Decimal

The constraint is documented and decisive:

> "Numba works best with NumPy arrays and numeric types. It has limited support for
> typed dicts, typed lists, and `@jitclass`, but **strings and general Python
> objects are largely out of reach.**"

`Decimal` is a general Python object. **Numba cannot accelerate decimal arithmetic
at all** — not slowly, not partially. The path is closed.

Cython is subtler. It compiles to C, but `Decimal` operations remain calls into
`_decimal`'s Python-object API, so Cython removes *interpreter* overhead around the
calls while leaving the per-object cost intact. To actually accelerate decimal in
Cython you must bind to libmpdec or decNumber at the C level — at which point you
are writing C, and Rust's advantage becomes ergonomics, memory safety, and a
sane build story rather than raw throughput.

**So the honest competitive statement is:**

| Workload | Fastest practical Python | Is there a Rust wedge? |
|---|---|---|
| Vectorizable float math | NumPy (up to 520x) | **No** |
| Scalar/branchy float loops | Numba 56-135x, Cython 99-124x | **No** — within 10% |
| **Exact decimal math** | **Nothing above ~2x** | **Yes — the only opening** |

---

## 3. GPU: the worst possible fit for this workload

Three independent reasons, all structural rather than incidental.

**(a) There is no decimal type on a GPU.** No CUDA, CuPy, PyTorch, or JAX decimal
dtype exists. GPUs offer fp16/bf16/fp32/fp64 and integers. Exact decimal money math
would have to be emulated in integer arithmetic by hand. For a workload whose entire
premise is exactness, the GPU is disqualified before performance is even discussed.

**(b) Branch divergence serializes exactly the workload we measured.** GPUs execute
32-thread warps in lockstep (SIMT). When threads in a warp take different sides of a
data-dependent branch, the paths execute *serially*:

> "When threads in a warp take different sides of a data-dependent branch, the warp
> diverges... divergence still serializes predictably." Throughput scales as **32/k**
> for a k-way split, and the penalty is **occupancy-invariant** — additional
> resident warps cannot hide it, because it is an instruction-issue cost.

Worst case is 1/32 = **3.125% utilization**; a fully random branch gives ~50%.

Our credit waterfall has 80.5% of scenarios breaching a covenant, 24.6% defaulting
early, and **55 distinct path lengths** — with per-period branches on PIK toggle,
sweep tier, revolver draw, and covenant state. This is close to a worst case for
SIMT. A GPU would spend most of its lanes idle executing branches that don't apply
to them.

Sources: [CUDA Programming Guide, SIMT model](https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/programming-model.html);
[Characterizing Warp Divergence from Pascal to Blackwell (arXiv 2607.23402)](https://arxiv.org/html/2607.23402);
[Modal GPU Glossary: warp divergence](https://modal.com/gpu-glossary/perf/warp-divergence).

**(c) It isn't available here anyway.** This machine is an Apple M4 (Metal 4, no
CUDA). CuPy, Numba CUDA, and JAX GPU all require NVIDIA. None of `cupy`, `torch`,
`jax`, `numba`, or `cython` is installed. Any GPU claim in this project would be
pure speculation.

**Where GPU genuinely would win:** the Monte Carlo *DCF* — smooth, branch-free,
float-tolerant, embarrassingly parallel. But that workload already runs in ~1 ms in
NumPy, so there is nothing to win. The GPU is fast at the problem we don't have and
disqualified from the problem we do.

---

## 4. Is the scale multiplier realistic?

The extrapolation used 100 credits x 10,000 simulations. Checking against published
market structure:

| Context | Typical count | Source |
|---|---|---|
| Broadly syndicated CLO | **>200 loans** | [Guggenheim CLO primer](https://www.guggenheiminvestments.com/perspectives/portfolio-strategy/understanding-collateralized-loan-obligations-clo/) |
| European CLO | **150-200 obligors**, ~€400m assets | [M&G CLO primer](https://www.mandg.com/dam/investments/institutional/shared/documents/an-introduction-to-clo-equity.pdf) |
| Large PE firm portfolio | ~80 portfolio companies (Thoma Bravo) | [Praxis Rock 2026 rankings](https://praxisrock.com/insights/top-private-equity-firms) |
| Mid-market PE fund | 15-30 portfolio companies | industry norm |

**Verdict: the multiplier is defensible but must be labelled by product.**

- For **CLO or private-credit portfolio analytics, 100 is conservative** — real deals
  carry 150-250 obligors, so the true figure is 1.5-2.5x higher than quoted.
- For a **single mid-market PE fund, 100 is too high.** Use 15-30, which puts exact
  Python at 20-41 s — uncomfortable but not disqualifying.
- The 20-year monthly CLO case (240 periods) is realistic for structured credit
  and is where minutes become unavoidable.

Corrected framing, with the measured 0.136 ms per scenario-path:

| Workload | Credits | Sims | Exact Python | Realistic? |
|---|---|---|---|---|
| Single deal, IC sensitivity | 1 | 10k | 1.4 s | yes — interactive, no problem |
| Mid-market PE portfolio | 25 | 10k | 34 s | yes — borderline |
| Large PE portfolio | 80 | 10k | 109 s | yes — batch territory |
| BSL CLO, annual periods | 200 | 10k | 272 s (4.5 min) | yes — conservative |
| BSL CLO, 20-yr monthly | 200 | 10k | **~18 min** | yes — clearly broken |

So the seconds-to-minutes threshold argument holds, but it belongs to **structured
credit and private-credit portfolio analytics**, not to single-deal PE work. On a
single CIM — the use case the blog actually leads with — exact Python is 1.4 s and
Rust is irrelevant.

That is worth saying plainly, because it reveals a mismatch between the demo and the
performance story: the workload where Rust matters is not the workload the platform
is being pitched on.

---

## 5. What actually survives

Strip out everything unsupported and this is what is left.

**Not defensible:**
- "30-100x faster than Python" — refuted, and NumPy/Cython/Numba account for that
  range without any Rust.
- Rust as a *float* performance play — Cython is within 10%, Numba is one decorator.
- GPU anything — no decimal type, and our branch profile is near worst-case SIMT.
- Rust mattering for single-deal analysis — 1.4 s in exact Python.

**Defensible:**
1. **Exact decimal math has no fast path in Python, and that is structural.** Numba
   cannot touch Python objects; NumPy has no decimal dtype; GPUs have no decimal
   type. Among accelerators, a compiled fixed-width decimal implementation is the
   only option, and Rust is a reasonable choice for one. This is a genuine gap in
   the ecosystem, not a preference.
2. **At structured-credit scale, exactness costs minutes.** Measured, linear, and
   verifiable: ~18 min for a 200-obligor CLO on monthly periods. That crosses the
   interactivity threshold.
3. **One audited kernel, three deployment targets.** The same Rust source runs
   server-side, as a Snowflake UDF, and in the browser via WASM. Cython and Numba
   cannot reach the browser at all. This is a *provenance and consistency*
   argument — one implementation to validate rather than three — and it is
   probably the strongest non-performance case.
4. **No GIL, real parallelism.** `rayon` parallelises across scenarios without
   multiprocessing's serialization overhead.

**The honest headline is therefore not a multiplier.** It is:

> Exact money math is the one numerical workload Python cannot accelerate — NumPy,
> Numba, and GPUs all buy their speed by giving up decimal. At portfolio scale that
> forces a choice between exactness and interactivity, and a compiled decimal kernel
> is the only way to have both.

---

## 6. A precision problem that needs resolving first

`rust_decimal` and Python's `Decimal` are **not guaranteed to agree.**

- `rust_decimal::Decimal` is a 128-bit fixed-precision type — 96-bit integer
  mantissa, roughly 28-29 significant digits, `Copy`, no allocation.
- Python's `Decimal` is *arbitrary* precision (`MAX_PREC` ≈ 1e18 digits), bounded
  only by the context.

Upstream issue [rust-decimal#471](https://github.com/paupino/rust-decimal/issues/471)
is a user reporting exactly this: a Rust service and a Python sister codebase
computing the same values and getting "ever so slight discrepancies," with no
reliable way to make `rust_decimal` match Python's semantics.

**This directly threatens the claim in the blog** that decimal gives an "audit trail
[that] matches your manual spreadsheet exactly." Two decimal implementations are not
automatically the same decimal, and division and rounding are where they part
company.

Required before publishing any exactness claim:
1. A cross-implementation parity test — same inputs through the Python decimal
   engine and the Rust kernel, asserting bit-identical results on a realistic
   corpus.
2. An explicit rounding policy (mode and scale) at every money boundary, matching
   the governing document's convention rather than the library default.
3. A stated significant-digit budget, confirming 28-29 digits is sufficient — it
   comfortably is for currency, but say so rather than assume it.

Until that parity test exists, the safe claim is "decimal arithmetic, with a
declared rounding policy," **not** "matches your spreadsheet exactly."

---

## 7. Recommended benchmark work, in priority order

1. **Cross-implementation parity test** (§6). Blocks every exactness claim, and a
   correctness failure here is far more damaging than a weak speedup.
2. **Build the crate and measure decimal DCF + credit waterfall.** Expect 2-10x over
   exact Python, not 30-100x. Publish the methodology.
3. **Add Cython and Numba to the harness as float baselines.** Pre-empt the obvious
   question, and demonstrate the decimal path is closed to Numba by showing it
   fail rather than asserting it.
4. **Do not pursue GPU.** Document why (§3) so the question is answered once.
5. **Re-scope the scale claim to structured credit** (§4), and stop implying Rust
   matters for single-deal CIM analysis.
