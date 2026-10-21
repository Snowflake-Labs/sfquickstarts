# Positioning v2 — Private Markets, Not Quant

Revision of the SWT abstract + blog in response to review feedback, widened to answer
"why PE rather than Capital Markets," rebalanced toward Snowflake, and reconciled
against what the code actually does.

---

## 1. The thesis

Not this:

> Rust and WebAssembly make AI 30–100× faster.

This:

> **How to build institutional-grade financial AI by separating probabilistic reasoning
> from deterministic computation, over governed data, with an explicit assurance boundary
> between them.**

The reusable pattern, and the spine of the talk:

```
probabilistic reasoning  →  structured contract  →  validated boundary
                         →  deterministic computation  →  evidence-backed output
```

Every layer is then a *mechanism serving that pattern*, not a headline:

| Role in the pattern | Component |
|---|---|
| Governed data plane | Snowflake — tables, RBAC, masking, lineage, `ACCOUNT_USAGE` audit trail, semantic views |
| Reasoning layer | Cortex `AI_COMPLETE` / Cortex Agents by default; model gateway routes to other approved providers (Bedrock, OpenAI) |
| Assurance boundary | Structured output contract + validation, range, and policy checks |
| Deterministic computation | Rust financial kernels — as a Snowpark UDF, in Container Services, or compiled to WASM at the edge |
| Evidence | Results written back to Snowflake with provenance, so risk and compliance can reconstruct any number |

Rust is the *computation mechanism*. Verification is the *bridge*. Snowflake is the plane
everything else is anchored to. That ordering is the whole argument.

---

## 2. Why Private Equity, not Capital Markets (quant / hedge funds)

This is the question the abstract should answer in its first paragraph, because a Capital
Markets audience will ask it immediately. Six reasons, in descending strength:

**1. The quant world already solved deterministic speed — 25 years ago.**
Telling a quant desk that Rust beats Python by 33× lands badly. They have run C++, kdb+,
and FPGAs on the hot path for decades, and their first question is not "how fast is Rust"
but "faster than *what* — naive loops, or vectorized BLAS?" The performance framing has no
novelty for them and invites a benchmark fight we would lose. In PE, the incumbent is
Excel and Word. There is no numerical-computing incumbent to beat, and the greenfield is
genuinely open.

**2. Latency asymmetry decides where Snowflake can even play.**
Quant and HFT workloads are microsecond-bound, and nothing in a governed cloud data
platform belongs on that path — correctly so. PE workloads are hours-bound, compressing to
minutes. That is exactly the regime where a governed data plane is an asset rather than
overhead. Choosing PE is choosing the problem where our architecture is the right answer
instead of a handicap.

**3. PE's bottleneck is documents; quant's bottleneck is signal.**
CIMs, IC memos, underwriting packages, and portfolio reviews are unstructured, private, and
read by humans under time pressure. That is precisely what language models are good at.
Quant alpha research is a search problem over well-structured numerical time series — a
place where LLMs are, at best, a peripheral assistant. The technology fits the PE
bottleneck and does not fit the quant one.

**4. There is no market price in private markets, so evidence *is* the product.**
A hedge fund gets a ground-truth mark every second and can validate a model against P&L. A
PE valuation is a defensible argument about an asset that has no price, reviewed by an IC,
an auditor, and an LP. Provenance, lineage, reproducibility, and audit-readiness are not
compliance tax in PE — they are the deliverable. That makes governance the feature, which
is the strongest possible framing for a Snowflake session.

**5. Quant firms cannot adopt a public reference architecture; PE firms can.**
Alpha is the asset, so a hedge fund will not build on a published pattern or tell anyone if
it did. PE process is not competitively secret in the same way — firms differentiate on
sourcing and judgment, not on how fast they draft a memo. A reference implementation is
therefore *adoptable* in PE and largely un-adoptable in quant.

**6. The audience math in the abstract already says so.**
SWT NYC 2025: 58 Capital Markets attendees against 571 FSI. Targeting the narrow quant slice
optimizes for the smaller room. Private markets and private credit — deal screening, credit
memos, underwriting, portfolio monitoring — reach the 571.

**Where Capital Markets legitimately stays in scope.** Not the trading loop: the
document-heavy middle and back office that looks structurally identical to PE — credit
memos, underwriting packages, portfolio and risk review, LP and regulatory reporting. The
honest framing is *private markets and credit, generalizing to any document-and-model
workflow in FSI*, with the trading hot path explicitly declared out of scope. Saying what
we are not addressing buys credibility with the quant attendees in the room.

---

## 3. Claims to fix before submission

Grounded in an audit of the repository. These are correctness issues, not style.

**Blocking — the Rust crate has never been built.** `integrations/rust/` contains
`Cargo.toml`, `lib.rs`, `dcf.rs`, `lbo.rs`, `monte_carlo.rs` with PyO3 and `wasm-bindgen`
bindings, but there is no `Cargo.lock`, no `target/`, no `pkg/`, and no `.wasm` artifact
anywhere in the tree. `import pe_finance` cannot succeed in this checkout. Every
performance claim in the abstract and blog is therefore currently unbacked by anything in
this repo.

**Blocking — the speedup numbers are a hardcoded estimate, and measurement refutes
them.** The "40s → 1.2s / 33× / 30–100×" figures originate in a literal
print-string table in `integrations/rust/examples/python_usage.py:201-222`, where
the columns are explicitly labeled `"Python (estimated)"` and `"Rust (actual)"`.
They are printed unconditionally and are not computed from the timing variables
captured earlier in the same file. Those figures were then restated verbatim across
22 files.

Measured on the exact workload: 10,000 Monte Carlo simulations x 5 years take
**0.050 s** in a naive Python loop and **0.001 s** in vectorized NumPy — not 40
seconds. The baseline was overstated by roughly **800×**, and at 1 ms the claimed
"Rust: 1.2 s" would be a **~1,200× regression**. Separately, NumPy alone accounts
for 44–49× over a naive loop, so "30–100× vs Python" is approximately what you get
from vectorizing Python and never writing any Rust.

**Replace the speed story with the precision story — it is measured, and it is
better.** Retargeting the benchmark at the decimal money path
(`bench_decimal_dcf.py`) produced two findings that hold up:

*Exactness is cheap, so the ceiling is low.* Decimal costs only **6–9×** over float
in Python across grids of 225 to 6,400 DCFs. That bounds the entire `rust_decimal`
opportunity at about one order of magnitude — "30–100×" is not recoverable by
changing workloads, it was simply too large. Vectorized NumPy float is ~350× faster
than Python decimal, so a Rust decimal kernel will likely *lose* to NumPy on float
throughput. Say so plainly; it is not the comparison that matters.

*Float and decimal genuinely disagree, by cents.* At WACC 9.71% and growth 14.29%,
decimal gives **$305,935,374.198877** and float gives **$305,935,373.950073** — a
25-cent gap on a $306M enterprise value, with relative error ~1e-9. NumPy diverges
identically, confirming representation error rather than an implementation bug.

The second finding is the talk's strongest performance-adjacent claim precisely
because the error is numerically *irrelevant*. It is operationally expensive
anyway: reconciliation against an audited model is pass/fail, not
tolerance-based, so a deck that disagrees with the underlying spreadsheet by any
amount costs an analyst an afternoon proving which is right — every time the model
is rerun. Decimal eliminates the category of question rather than shrinking it.

That converts Rust from a performance optimization into a **governance and audit**
argument, which is far more durable for an FSI audience, sits naturally alongside
the Snowflake governance story, and — unlike any speedup figure — is reproducible
today with no Rust toolchain installed.

**Fix, then: delete every speedup figure. Publish the precision divergence and the
6–9× exactness cost. Build the crate before claiming Rust closes that gap.**

**"Agentic" is not yet true.** There is no planning, tool selection, critique, or
goal-directed iteration in the codebase. The real control flow is a hand-sequenced linear
chain — `examples/complete_deal_workflow.ipynb` runs CIM extraction, then a pure-Python
DCF, then a sensitivity loop, then an LBO, then memo synthesis, then a table write, with no
branching on model output. `AGENTS.md:21-24` and `docs/architecture.md:91-118` describe a
multi-agent chain that no code implements. Either build the loop or retitle to
**AI-powered analytical workflow platform** and drop "the future of Private Equity is
agentic." The linear pipeline is not a weakness — for high-consequence finance, a fixed
auditable sequence is arguably the correct design, and saying so is a stronger claim than
borrowing the word "agentic."

**The verification boundary is the missing piece — and it is the best part of the talk.**
There are no pydantic models, no JSON Schema, and no guardrails in the repo; `pydantic` and
`jsonschema` appear zero times. The only validation, `cortex_client.py:204-232`, strips
disallowed API parameters — a request sanity check, not a check on financial output. In the
notebook, DCF and LBO inputs are hand-typed dicts, *not* parsed from the CIM extraction, so
there is currently no extraction-to-model path at all. Building
`LLM → typed schema → range and policy checks → deterministic engine` closes the biggest
real gap and is the single highest-value addition. It also opens the door to genuine
assurance: policy engines, constraint solvers such as Z3, formal methods. That is the
difference between "AI plus fast math" and *probabilistic intelligence surrounded by
deterministic assurance*.

**Soften Rust and refine the floating-point message.** "Start with Rust from Day One"
overclaims — Python remains the right choice for orchestration, experimentation, and
integration; Rust earns its place in performance-critical, precision-critical, or
authoritative kernels. And "floating-point math is the enemy" is too absolute: decimal is
right for money and accounting, while float is entirely legitimate for Monte Carlo,
statistics, and optimization. The repo proves the point against itself — `monte_carlo.rs`
uses plain `f64` throughout, and the PyO3 entry points in `lib.rs:32` accept `f64` and
convert via `Decimal::from_f64_retain`. State explicit numerical boundaries instead of a
blanket rule.

**Qualify the WASM claims.** WASM is a genuinely useful portable execution target and can
run kernels client-side, but it does not by itself deliver "no data egress," "no server
overhead," or decimal precision. Those come from the surrounding architecture. Claim the
portability; derive the rest from design.

**Drop model version numbers from the architecture.** `config/models.yaml` already has the
right shape — task → tier → platform → model — with `platforms` for cortex, openai, and
bedrock and a `family_defaults` fallback. Describe it in capability tiers (frontier
reasoning, balanced, low-cost extraction) and treat concrete model IDs as swappable
examples. Several entries in the catalog are already flagged `available: false`, which makes
the point. Extend routing beyond cost to include task type, risk, latency, data
classification, required tools, context needs, and assurance requirements — that is the
reusable pattern.

**Correct the Snowflake layer description.** Snowflake is not "the data layer" with Cortex
as a synonym for it. Snowflake is the governed data platform — data, security, policy,
lineage, audit; Cortex is one AI capability within it. The current four-layer list blurs
governance and inference into one box, which undersells the governance story that is the
actual differentiator for this audience. Note also that `docs/architecture.md` references
semantic views and `README.md:124` references `integrations/cortex/schema.sql`, neither of
which exists on disk — either build them or stop citing them.

**ROI numbers need methodology.** For each row of the table — CIM analysis 2h → 15m,
modeling 4h → 30m, IC memo 8h → 1h, portfolio reporting 3 days → 30m, 1k scenarios 5h → 2m
— label it as benchmark, prototype measurement, production observation, or estimate, and
state the workload and the baseline. Given the audit, most are estimates, and saying so
costs far less credibility than being asked.

**Remove or source "3,000 analyst hours."** Over 3,000 hours a year of grunt work implies
roughly 60 hours a week on nothing but repetitive tasks. It needs a citation or it needs to
go. The "1.5 reclaimed FTEs" figure inherits the same problem.

**Fix `skills/` before pointing anyone at the repo.** `AGENTS.md:162-183` and
`README.md:107-119` describe four skill files and a `skills/financial-modeling/SKILL.md`
tree. The directory does not exist. Anyone who clones from the blog link finds this in the
first minute.

---

## 4. Revised abstract

**Title:** Institutional-Grade Financial AI: Separating Reasoning from Computation in
Private Markets

Private markets run on documents and models. Investment committee materials, credit memos,
underwriting packages, and portfolio reviews drive the most consequential decisions in
finance — and they remain the most analyst-intensive, because there is no market price to
check the answer against. Evidence *is* the product.

That makes private equity and private credit a sharper target for AI than the quant
trading loop. Quant desks solved deterministic speed decades ago in C++ and on the hot path
measured in microseconds, where no governed data platform belongs. Private markets are
document-bound rather than signal-bound, hours-bound rather than microsecond-bound, and
judged on defensibility rather than realized P&L — which is exactly the regime where
language models help and governance is a feature rather than a tax.

This session presents a replicable architecture for that regime, and the pattern
generalizes to any document-and-model workflow in FSI:

```
probabilistic reasoning → structured contract → validated boundary
                        → deterministic computation → evidence-backed output
```

Snowflake provides the governed data plane — lineage, policy, access control, and an audit
trail your risk and compliance teams can reconstruct. Cortex supplies reasoning, behind a
config-driven model gateway that routes by task, risk, latency, and data classification
across approved providers rather than hardcoding a model. A typed schema plus range and
policy validation forms an explicit assurance boundary, so high-consequence computation
only ever runs on validated inputs. Deterministic Rust kernels — reachable as UDFs, in
containers, or compiled to WebAssembly — perform the DCF, LBO, and Monte Carlo math in
decimal, because float and decimal valuations of the same company differ by cents and
reconciliation against an audited model is pass/fail rather than tolerance-based. Every
output carries provenance back to governed data.

You will leave with the layering, the model-routing configuration, the validation contract,
and the reasoning behind each numerical boundary — the architectural pattern, which is
considerably more durable than any one implementation of it.

---

## 5. Sequenced work before submission

1. Build the Rust crate. Run and record a real benchmark against vectorized NumPy;
   publish the methodology or delete the speedup claim.
2. Implement the validation boundary — typed CIM extraction schema feeding DCF and LBO
   inputs. This is the talk's strongest asset and its largest gap.
3. Retitle away from "agentic," or build the loop.
4. Label every ROI figure with its provenance; cite or cut "3,000 hours" and "1.5 FTEs."
5. Create `skills/`, or remove the references from `AGENTS.md` and `README.md`.
6. Redraw the architecture diagram with governance and inference as distinct planes, and
   the assurance boundary drawn explicitly between reasoning and computation.
7. Purge the estimated benchmark table from all eight files that currently restate it.
