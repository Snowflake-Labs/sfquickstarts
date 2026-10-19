# Design: Synthetic Supply Chain Notebook ("Better Together")

## 1. Message

Not "RelationalAI instead of SQL", but **SQL + Python + RelationalAI on the same Snowflake data**, each used where it fits:

| Layer | Best at | In this notebook |
|---|---|---|
| **SQL** | Storing, filtering, joining and aggregating data; fixed-shape questions | Load data, simple lookups, final reporting on results |
| **Python** (pandas, NetworkX, OR-Tools…) | Flexible custom analysis | Shown as the alternative: works, but each question is custom code; data is pulled into the notebook kernel and you handle sizing/chunking yourself |
| **RelationalAI (PyRel)** | Reasoning over connected data: recursive rules, rules that build on each other, graph algorithms, optimisation, all on one shared model | Chapters where fixed-shape SQL stops and the Python alternative becomes custom code |

The audience is data scientists working in a Snowflake Notebook. The tone is neutral: every chapter shows what SQL can do, what the Python alternative costs, and what PyRel adds. Scaling is mentioned, not demonstrated.

**On memory, stated fairly:** both approaches are memory-bound. Python libraries run in the notebook kernel and need the data pulled into it; RelationalAI runs in a separate engine (SPCS compute pool, sized via config) fed from Snowflake tables via CDC. The difference is where the work runs and who manages sizing and data movement, not that RelationalAI has no limit. Engine behaviour beyond memory (spill, practical limits) is not verified — check with RelationalAI before making any claim.

## 2. Limits of SQL as a language (not engine-specific)

| Limit | Source |
|---|---|
| Fixed-shape queries | Number of joins fixed at write time; depth must be known |
| Restricted recursion | Standard SQL allows linear recursion; engines generally disallow aggregation/negation over the recursive reference |
| Cycles handled manually | Path tracking / `CYCLE` clause, support varies by engine |
| Rules don't compose | Logic restated per query; views help but don't reason |
| No graph algorithms | SQL/PGQ (SQL:2023) adds pattern matching, not centrality/communities; engine support limited |
| No optimisation | SQL describes data; it doesn't search for a best decision |

## 3. Synthetic dataset: electronics manufacturer

Generated once by `scripts/generate_data.py` (seed 42) and committed as CSV files in `data/`; loaded by `scripts/load_data.sql` into `RAI_QUICKSTART.SUPPLY_CHAIN`. Small enough to inspect by eye.

| Table | Rows | Content |
|---|---|---|
| `PARTS` | 315 | Finished goods, assemblies and components (`PART_TYPE`), unit cost |
| `PRODUCTS` | 20 | Sellable products, list price, top-level part |
| `BOM` | 469 | `PARENT_PART_ID`, `CHILD_PART_ID`, `QTY_PER`; depth 3–5; shared subassemblies (DAG) |
| `SUBSTITUTES` | 60 | `PART_ID`, `SUBSTITUTE_PART_ID`, `RATIO` |
| `SUPPLIERS` | 80 | Tier 1–4, country, region |
| `SUPPLIER_PARTS` | 483 | Tier-1 supplier, part, capacity per week, lead time, unit price |
| `SUPPLIER_DEPENDENCIES` | 81 | Tier-N supplier dependencies, including a cycle |
| `INVENTORY` | 315 | On-hand stock per part |
| `CUSTOMERS` | 100 | Customer, region |
| `ORDERS` | 1,500 | Customer, product, quantity, due date, value |

**Planted scenarios with known answers.** These are described in full for the reader in `data/README.md` (what's in the data, what we're looking for, why it's hard), are listed in `data/expected_results.json`, and are asserted in the notebook:
- Case 1, shared subassembly: control board `P-040` appears in 8 products (`PR-01`…`PR-08`), directly in 6 and one level deeper in `PR-02` and `PR-08`.
- Case 2, hidden concentration: sensor `P-141` looks dual-sourced (`S-T1-02`, `S-T1-05`), but both depend on tier-3 supplier `S-T3-07`. If `S-T3-07` fails: exactly the 8 control-board products, 568 orders, value 6,840,136.49.
- Case 3, substitute rescue: `PR-04` is buildable only if radio chip `P-121` is replaced by `P-122`. `PR-09` is also rescued, by a random substitute pair; buildable products go from 9 to 11.
- Case 4, supplier cycle: `S-T2-11 ↔ S-T2-14`.

The notebook should open with a short "What's in the data" section that summarises these four cases and links to `data/README.md`. Each chapter then names the case it's looking for before running the query.

## 4. Modelling the ontology (required step)

### 4.1 Why it is needed

RelationalAI does not reason over tables directly. It reasons over a **semantic model**, the ontology: the business concepts (Part, Supplier, Order…), the relationships between them (contains, supplies, depends on…), and a mapping from each Snowflake table onto those concepts. Every query, rule, graph algorithm and optimisation in later chapters is written against this model. **Without it there is nothing for RelationalAI to run on.** This is the first PyRel step in the notebook, before any analysis.

What it buys, and what it costs, stated fairly:

| | SQL / Python alternative | With an ontology |
|---|---|---|
| Up-front work | None | Declare concepts, relationships and mappings once (~100 lines for this dataset) |
| Each new question | Restates join paths and conditions (SQL) or rebuilds DataFrames/graphs (Python) | Reuses the same concepts and rules; a question is a short query |
| Business meaning | Lives in column names and in each query | Explicit and shared: `Part contains Part`, `Supplier depends on Supplier` |
| Data-quality guard | None by default | `Property` enforces one value per key (`FDError` on violation) |

That reuse across chapters 2–7 is the payoff. For a single fixed-shape question, SQL without a model remains the simpler choice, and the notebook says so.

What it is *not*: an OWL/RDF artefact or an enterprise-wide modelling project. It covers only what the questions need, and grows when a chapter needs more (for example, chapter 4 adds derived rules on top of it).

### 4.2 How to do it

Follow these steps (condensed from RelationalAI's ontology guidance), shown in the notebook as separate cells:

1. **Scope the questions.** Use the chapter questions (BOM explosion, supplier failure, buildability, criticality, allocation). Only model what they need.
2. **Inspect the source tables.** Get column names and types from `INFORMATION_SCHEMA.COLUMNS`. Types decide PyRel types: `NUMBER(p,0)` → `Integer`, `NUMBER(p,s>0)` → `Float`, `DATE` → `Date`, `TEXT` → `String`. A mismatch raises `TyperError` and blocks all queries.
3. **Identify concepts and their identity.** Anything with its own key becomes a concept with `identify_by`. Name them as business nouns (`Part`, not `PARTS`).
4. **Choose Property or Relationship per link,** based on multiplicity:
   - Many-to-one, one value per entity → `Property`. Examples: `Part.unit_cost`, `Order.customer`.
   - A link keyed by its endpoints that carries one value → multi-field `Property`. Example: BOM quantity per (parent, child).
   - Many-to-many with no value → `Relationship`. Example: `Supplier depends on Supplier`.
   - A link carrying several values → junction concept. Example: `Supply` with capacity, lead time and price.
   - Same-type slots get role names (`{Part:parent} contains {Part:child}`), otherwise both slots bind to the same column.
5. **Map tables to the model** with `model.Table(...)`, `Concept.new(...)` for the authoritative table, and `Concept.lookup(...)` to resolve foreign keys.
6. **Validate with queries:** instance counts per concept equal the table row counts, every relationship resolves, types read back correctly, and `inspect.schema(model)` shows what actually registered.

### 4.3 The example ontology

Implemented in `notebooks/supply_chain_ontology.py` and imported by the notebook.

```
                    top_part                 contains (qty)          substitute (ratio)
   Product ──────────────────▶ Part ◀──────────────────▶ Part ◀────────────────────▶ Part
      ▲                          ▲   (parent)      (child)   (original)   (substitute)
      │ product                  │ part
    Order ── customer ──▶ Customer        Supply (capacity, lead time, unit price)
                                 │ supplier
                              Supplier ── depends_on ──▶ Supplier (buyer → upstream; may cycle)
```

| Concept | Identity | Properties | Source |
|---|---|---|---|
| `Part` | `id` | `name`, `kind`, `unit_cost`, `on_hand` | `PARTS`, `INVENTORY` |
| `Product` | `id` | `name`, `list_price`, `top_part → Part` | `PRODUCTS` |
| `Supplier` | `id` | `name`, `tier`, `country`, `region` | `SUPPLIERS` |
| `Supply` | (`supplier`, `part`) | `capacity_per_week`, `lead_time_days`, `unit_price` | `SUPPLIER_PARTS` |
| `Customer` | `id` | `name`, `region` | `CUSTOMERS` |
| `Order` | `id` | `customer → Customer`, `product → Product`, `quantity`, `due_date`, `value` | `ORDERS` |

| Link | Kind | Reading | Source |
|---|---|---|---|
| `Part.contains` | Property (parent, child → qty) | `{Part:parent} contains {Part:child} {Integer:qty} times` | `BOM` |
| `Part.substitute` | Property (original, substitute → ratio) | `{Part:original} can be replaced by {Part:substitute} at ratio {Float:ratio}` | `SUBSTITUTES` |
| `Supplier.depends_on` | Relationship (many-to-many) | `{Supplier:buyer} depends on {Supplier:upstream}` | `SUPPLIER_DEPENDENCIES` |

Design choices worth explaining in the notebook:
- **`Supply` is a junction concept.** A supplier–part link carries three values (capacity, lead time, price), so it can't be a single multi-field property. It also gives the allocation chapter one place to put capacity constraints.
- **`Product` and `Part` stay separate.** The BOM is entirely about parts, while orders and prices are about products. `Product.top_part` connects the two.
- **`Part.kind` is a plain property, not subtypes**, for now. If chapters keep filtering on it, promote it to subtypes (`Component`, `Assembly`) later.

### 4.4 Verified (2026-10-14, relationalai 1.35.3, role `RAI_QS_ROLE`)

Run against the loaded tables; all checks passed:

| Check | Result |
|---|---|
| Instances per concept | Part 315, Product 20, Supplier 80, Supply 483, Customer 100, Order 1,500 (all equal row counts) |
| Relationships | BOM 469, substitutes 60, supplier dependencies 81 (planted cycle present), every order linked to a customer and product, 20 products linked to a top part |
| Types | `due_date` reads as a date, `value` as a float, `quantity` as an integer |
| `inspect.schema(model)` | 6 concepts, 10 data sources, 10 define rules |

**First-run cost to tell the reader:** the first query took about 5 minutes. Engine provisioning took 3m04s and indexing the 10 tables (CDC data streams) took 4m19s, partly in parallel. After that, each query took 2–8 seconds.

## 5. Chapters

| # | Question | SQL | Python alternative | PyRel |
|---|---|---|---|---|
| 0 | Load and inspect data | **Right tool** | n/a | n/a |
| 1 | **Model the domain (ontology)** | n/a | n/a | **Required.** Define concepts, relationships and mappings (section 4), validate counts |
| 2 | Explode BOM of product X with total quantities; which products contain the control board? (**case 1**) | Possible: recursive CTE, careful with shared subassemblies | Recursive function or NetworkX DAG walk | One recursive rule on `Part.contains` |
| 3 | Tier-3 supplier `S-T3-07` fails → affected products and orders? (**cases 2 and 4**) | Fragile: two recursions plus hand-written cycle guard | NetworkX reachability; custom glue between BOM and supplier graphs | Recursive rule on `Supplier.depends_on`, reusing chapter 2 |
| 4 | Which products are buildable from stock, taking substitutes into account? (**case 3**) | Works once reformulated positively ("blocked" propagates up, then take the complement) | Custom recursive code with memoisation | Same positive reformulation (PyRel doesn't allow recursion through negation); value is reuse in chapter 6 |
| 5 | Which suppliers are structurally most critical? Which clusters? | Outside SQL | NetworkX betweenness / communities, in memory | Graph reasoner on the same model |
| 6 | Allocate scarce parts across open orders to maximise delivered value within capacity and due dates | Outside SQL | OR-Tools/PuLP: build the model by hand from DataFrames | Prescriptive reasoner reusing `Supply` and the chapter 4 rules |
| 7 | Report: revenue at risk by region, plus allocation plan | **Right tool again**: results written back to tables, queried with SQL | n/a | Export results |

Chapters 2–7 follow the same pattern: question → SQL attempt (runs) → "what made this hard" → Python alternative (short, honest) → PyRel on the chapter 1 model → assert the planted answer.

## 6. Repository layout

| Path | Purpose |
|---|---|
| `getting-started-with-notebooks-relational-ai.md` | Setup guide |
| `data/*.csv`, `data/expected_results.json` | Pre-generated sample data and planted answers |
| `scripts/generate_data.py` | Regenerates the data (deterministic) |
| `scripts/load_data.sql` | Role, warehouse, schema, Git repository, tables, load |
| `scripts/admin_setup.sql` | RelationalAI health check, external access integration, compute pool grants |
| `notebooks/supply_chain_ontology.py` | The ontology (chapter 1), imported by the notebook |
| `notebooks/01_relationalai_setup.ipynb` | Setup notebook: pre-flight, install + restart, connect, first query |
| `notebooks/02_supply_chain_better_together.ipynb` | Storyline notebook, chapters 0–7 |

**Status of the notebooks.** Every code cell of notebook 02 runs locally against the loaded tables with a key-pair session. The `%pip` cell is skipped there, and every planted answer is asserted. The notebooks have not yet been run inside a Snowflake Notebook on Container Runtime.

**Lessons from building them:**
- **Chapter 4 reframed:** PyRel rejects recursion through negation (`UnsupportedRecursionError`), so "all children available" was reformulated as positive propagation of "blocked". SQL can then do it in one recursive CTE too, so the notebook no longer claims chapter 4 is beyond SQL.
- **Graph property names:** graph result properties must be named after the algorithm (`Supplier.betweenness_centrality`, `Supplier.community_assignments` for Louvain), otherwise PyRel raises `[Invalid short name]`.
- **Duplicate edge:** the planted cycle creates one in the undirected supplier graph, so it needs `aggregator="sum"`.
- **Graph cross-check:** RelationalAI and NetworkX give the same betweenness ranking, with scores within about 1%. Louvain community counts differ between runs and tools (36 vs 14), so the notebook doesn't assert them.
- **Optimisation result:** 2,960 sensors fill 48 of 568 orders, worth 1,136,506.80 (HiGHS, OPTIMAL). The first solve starts a solver engine, which takes a few minutes.
- **Unguarded SQL:** a recursive CTE without a cycle guard ran for over an hour on the cycle. The notebook shows it as text only, and `load_data.sql` sets a 10-minute statement timeout on `RAI_QS_WH`.

## 7. To verify while building

1. PyRel syntax for recursive rules, negation/union over substitutes, graph reasoner and prescriptive formulation (load `rai-pyrel`, `rai-graph-analysis`, `rai-prescriptive-problem` skills).
2. Exact SQL behaviour for chapter 4 across engines, so the "beyond one query" claim is stated precisely.
3. Runtime of graph and prescriptive reasoners on this volume in a notebook.
4. RelationalAI engine memory behaviour and sizing guidance (for the scaling side note).
5. How the notebook imports `supply_chain_ontology.py` (Workspaces file next to the notebook, or inline cells).
6. Companion repository for the data. Snowflake can't clone sfquickstarts ("exceeds set limits").
