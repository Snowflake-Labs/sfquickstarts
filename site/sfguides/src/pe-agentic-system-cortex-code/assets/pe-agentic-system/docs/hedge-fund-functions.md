# Hedge Fund Functions: Where the Architecture Actually Applies

Companion to `positioning-v2.md`. That document argued for private markets over
capital markets. This one resolves the tension in that argument — because a large
part of the hedge fund world fits this architecture *better* than PE does, and the
single strongest instance of the deterministic-computation wedge is a hedge fund
function, not a PE one.

The distinction that matters is **not** PE versus hedge fund. It is:

> **the alpha loop versus everything else.**

The trading hot path is out of scope, permanently and for good reasons. The
middle and back office is not — and it is larger, more document-bound, more
exactness-critical, and more governed than the deal side of PE.

---

## 1. Why the earlier argument needs amending

`positioning-v2.md` argued against a quant/hedge fund framing on six grounds. Five
of them were about the **front office**: microsecond latency, signal rather than
document bottlenecks, alpha secrecy, C++ incumbency, and the futility of a
"faster than Python" claim to a quant desk. All five still hold.

But they only ever applied to alpha research and execution. Applied to fund
accounting, fee calculation, investor allocations, collateral, and regulatory
reporting, every one of them inverts:

| Property | Alpha loop | Hedge fund middle/back office |
|---|---|---|
| Latency regime | microseconds | hours to days |
| Bottleneck | signal discovery | documents and reconciliation |
| Numerical requirement | fast float | **exact decimal, contractually binding** |
| Secrecy | alpha is the asset | process is not competitively secret |
| Incumbent tooling | C++, kdb+, FPGA | **Excel, and administrators' legacy systems** |
| Governance posture | speed over auditability | **audited, regulated, investor-facing** |

That last row is the point. In the back office, being wrong is not a missed trade
— it is a restatement, an investor claim, or a regulatory finding. Exactness and
provenance are the product, which is precisely what this architecture is for.

---

## 2. Function map

Scored against the three properties the architecture actually serves: **document
understanding** (LLM adds value), **exact deterministic computation** (the Rust
wedge), and **governed data + audit** (Snowflake).

| Function | Doc-heavy | Exact compute | Governed/audited | Fit |
|---|---|---|---|---|
| **Incentive fee crystallization, HWM, equalization** | medium | **very high** | **very high** | **strongest** |
| NAV calculation and striking | medium | **very high** | **very high** | **very strong** |
| Investor allocations, subs/reds, gates, lock-ups, side pockets | high | **very high** | **very high** | **very strong** |
| Expense allocation across funds/SMAs | high | high | **very high** | **very strong** |
| Form PF / AIFMD Annex IV / N-PORT reporting | **very high** | medium | **very high** | **very strong** |
| ISDA/CSA, GMRA, PB agreement term extraction | **very high** | medium | high | strong |
| Collateral and margin call workflow | high | **high** | high | strong |
| Investment guideline / IMA mandate compliance | **very high** | medium | **very high** | strong |
| Side letter and MFN obligation tracking | **very high** | low | **very high** | strong |
| Credit agreement and covenant analysis (credit / distressed / special sits) | **very high** | **very high** | high | strong |
| PB and counterparty reconciliation, financing accruals | medium | **high** | high | strong |
| LP and risk-committee reporting, stress testing | high | medium | high | moderate |
| Best execution / TCA / MiFID reporting | medium | medium | high | moderate |
| Alpha research and signal discovery | low | low (float fine) | low | **out of scope** |
| Order routing and execution | none | none (latency-bound) | none | **out of scope** |

---

## 3. The strongest wedge is a hedge fund function

**Incentive fee crystallization with high-water marks and equalization** is a
better instance of the deterministic-computation argument than the CLO waterfall I
benchmarked. It satisfies every condition, and unlike the CLO case it also fixes
the workload mismatch flagged in `performance-alternatives.md` §4.

### Why it qualifies on every axis

**Per-investor path-dependent state.** Each investor carries their own history, and
industry sources describe it precisely:

> "Individual shareholders are often in different positions in terms of **loss
> carry-forwards, high water marks, equalization paid, equalization lost in prior
> years, and depreciation deposit balances.**"
> — [Performance-Based Incentive Fees and Equalization Mechanisms, Mondaq](https://www.mondaq.com/caymanislands/wealth-asset-management/7304/performance-based-incentive-fees-and-equalization-mechanisms)

Under series accounting, "each meaningful subscription date creates a separate
series of shares **with its own NAV path and its own performance fee accrual**"
([Resonanz Capital](https://resonanzcapital.com/insights/performance-fee-fairness-what-hedge-fund-lps-actually-pay)).
This is not one path — it is one path *per investor per series*, each with sticky
state that cannot be vectorized away.

**Branch-heavy.** Above or below HWM; hurdle met or not, with tiered catch-up;
crystallize or accrue; equalization credit issued or contingent redemption applied;
loss carryforward recovering or not; clawback on a subsequent drawdown. Every one
is a data-dependent branch on per-investor state.

**Exactness is contractual, not aesthetic.** Investors are *paid* on this number.
A cent-level discrepancy is not a rounding footnote — it is a misallocation between
the manager and the investors, and between investors. This is the cleanest possible
answer to "why not just use float?"

**It is a known, admitted failure mode.** Not a hypothetical:

> "Equalization calculations can be **very complex and error prone**. Spreadsheet
> models that may work for a small number of investors or transactions **quickly
> become unmanageable over time.**" — Mondaq, as above

And on series accounting: "in volatile periods, especially after drawdowns, a fund
can end up with **many series outstanding**, increasing accounting complexity,
administrator workload, and investor reporting burden" (Resonanz). The problem gets
worse exactly when markets are stressed and attention is scarcest.

**The document-understanding half is real too.** The rules live in the offering
memorandum and side letters — crystallization frequency, hurdle definition, whether
the hurdle is compounding, HWM reset conditions, equalization method — in prose,
differing per fund and per investor. That is genuine LLM work: extract the fee
mechanics into a typed schema, then hand the *validated* schema to a deterministic
engine. It is the assurance boundary with a real contract behind it.

### Scale drivers

> **MEASURED — and the scale prediction below was WRONG.** `bench_equalization.py`
> has since been built and run. The combinatorial argument in this section does not
> hold: a 50,000-account administrator book recomputes in **3.2 seconds** in exact
> Python, linear at 0.063 ms per investor per 10-year history. There is no
> interactivity threshold here and no performance wedge. Funds have hundreds of
> investors, not hundreds of thousands, and per-period equalization arithmetic is
> ~2x cheaper than a debt waterfall — so both factors move the wrong way for the
> prediction.
>
> **What the benchmark did find is stronger than what it was looking for:**
> **113 of 400 investors (28.2%, stable at 28-29% across scales) would be paid a
> different performance fee** under float versus decimal, with NumPy diverging on
> exactly the same investors. Relative error ~1e-9 — numerically irrelevant, which
> is precisely the point, because these are payments quantized to cents. Roughly
> three in ten investors receive a different amount depending on which arithmetic
> the administrator used.
>
> So this function is the strongest **correctness** case in the project and *not* a
> performance case. Full results in
> `integrations/rust/benchmarks/README.md`; status in `CLAIMS.md` §1.10.

The original (refuted) reasoning is retained below for the record.

~~The combinatorics are structurally worse than the CLO case.~~ Cost scales as:

```
investors  x  series  x  periods  x  share classes
```

~~A mid-sized fund with 400 investors, monthly dealing over 10 years (120 series),
multiple classes, recomputed on every NAV strike and again at year-end audit, is
orders of magnitude more path-instances than a 200-obligor CLO.~~

The lesson worth keeping: every unmeasured performance claim in this project has
turned out to be wrong, including this one, and including ones I made myself after
correcting someone else's.

---

## 4. Second tier: regulatory reporting

Form PF and AIFMD Annex IV are the strongest *document-and-governance* fit, with
less deterministic-compute content. Grounded figures:

- Annex IV requires **300+ data points**, with commercial solutions applying
  **1,000+ automated validations** ([FE fundinfo](https://www.fefundinfo.com/products/institutions/aifmd-annex-iv-reporting)).
- ESMA identifies **over 100 distinct EU reporting templates**, creating overlap
  and cross-border burden ([Alter Domus](https://alterdomus.com/insight/aifmd-annex-iv-a-guide-to-reporting-obligations/)).
- The core difficulty is explicitly aggregation, not calculation: data "does not
  reside in a single platform, but usually must be aggregated from multiple
  sources, both internal and external" ([The Hedge Fund Journal](https://thehedgefundjournal.com/compliance-for-hedge-funds/)).
- Multi-jurisdiction filing multiplies the work — a non-EU AIFM marketing in three
  member states files three separate Annex IV returns to three NCAs.
- Form PF: large hedge fund advisers face a **60-day** deadline; qualifying hedge
  funds are those with NAV ≥ $500M ([SEC / Federal Register](https://www.federalregister.gov/documents/2024/03/12/2024-03473/form-pf-reporting-requirements-for-all-filers-and-large-hedge-fund-advisers)).

Why this is a good fit for *this* architecture specifically: the hard part is
governed aggregation across fragmented sources with validation and an audit trail —
which is a Snowflake argument first, an LLM argument second, and barely a Rust
argument at all. It is the cleanest demonstration that the pattern is about the
**boundary and the governed plane**, not the compute kernel. Worth including for
exactly that reason.

---

## 5. What does not fit — say it explicitly

Naming the exclusions buys credibility with the quants in the room, and prevents
the session being judged against a claim it never made.

- **Alpha research and signal discovery.** Float is correct, NumPy/JAX/GPU already
  dominate, and LLMs are peripheral. No wedge.
- **Order routing and execution.** Microsecond-bound. Nothing in a governed cloud
  data platform belongs on that path.
- **Real-time risk on the trading desk.** Intraday, latency-sensitive, float-tolerant.
- **Anything where the answer is a distribution rather than a payment.** Monte
  Carlo VaR is float work; the ~1 ms NumPy result already settles it.

The honest boundary: **when the output is a number someone gets paid on, or files
with a regulator, this architecture applies. When it is a number someone trades
on, it does not.**

---

## 6. Consequences for the session

This materially improves the abstract and resolves the awkwardness of pitching a
"Capital Markets" audience while arguing for PE.

1. **Retitle away from private equity specifically.** The unifying subject is
   *institutional-grade financial computation over governed data* — which covers
   PE deal work, private credit, and hedge fund middle/back office in one frame.
   That addresses the 571 FSI attendees rather than only the 58 in Capital Markets,
   without pretending to serve the alpha loop.

2. **Lead the deterministic-computation demo with fee equalization, not the CIM.**
   It is where exactness is contractual, the failure mode is documented in industry
   literature, the scale is real, and "why not float?" answers itself. The CIM
   remains the right *document-understanding* demo — the two demos should be
   different functions, which the current single-workflow narrative conflates.

3. **Keep one honest exclusion slide.** "We are not doing alpha, and here is why"
   is a credibility asset, not a limitation.

4. **The assurance boundary now has a stronger contract behind it.** Fee mechanics
   extracted from an OM and a side letter, validated against policy, then executed
   deterministically — with provenance back to the governing document — is a more
   compelling instance of `LLM proposes / boundary decides / engine computes` than
   DCF assumptions from a CIM, because the consequence of getting it wrong is a
   misallocation between investors rather than a mis-estimated valuation.

---

## 7. Recommended next work

1. **Benchmark equalization/crystallization** — per-investor HWM, loss carryforward,
   hurdle with catch-up, equalization credits and contingent redemptions, over a
   realistic investor x series x period grid. Same harness discipline: exact Python
   baseline, float and NumPy comparators, correctness gate, no speedup quoted until
   implementations agree. This is where the wedge should be proven.
2. **Extend the assurance contracts** to fee mechanics — a `FeeTerms` schema with
   crystallization frequency, hurdle type and compounding, HWM reset rules, and
   equalization method, sourced from the OM with provenance. Reuse the existing
   ERROR/WARNING severity split: an impossible hurdle definition blocks, an unusual
   crystallization frequency warns.
3. **Do not attempt Form PF/Annex IV as a demo** unless there is real data — it is
   a strong *narrative* fit and a poor *demo* fit, because the value is in
   aggregation breadth that cannot be faked convincingly on stage.
