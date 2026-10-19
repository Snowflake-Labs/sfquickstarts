# Sample data: synthetic electronics supply chain

Small, synthetic data for the RelationalAI notebook quickstart. It describes an electronics manufacturer that builds 20 IoT products from 315 parts supplied by 80 suppliers in four tiers, plus 1,500 open customer orders.

Most of the data is random, generated with a fixed seed by `scripts/generate_data.py`. On top of that, **four cases are planted deliberately**. Each one is a realistic supply-chain situation that is hard to find with fixed-shape SQL. The notebook looks for each case, and checks its answer against `expected_results.json`.

## Tables

| File / table | Rows | Content |
|---|---|---|
| `parts.csv` / `PARTS` | 315 | 20 finished parts, 60 assemblies, 235 components (`PART_TYPE`), with unit cost |
| `products.csv` / `PRODUCTS` | 20 | Sellable products; `PART_ID` is the product's top-level part |
| `bom.csv` / `BOM` | 469 | Bill of materials: `PARENT_PART_ID` contains `QTY_PER` × `CHILD_PART_ID`. 3–5 levels deep; subassemblies are shared between products |
| `substitutes.csv` / `SUBSTITUTES` | 60 | `PART_ID` may be replaced by `SUBSTITUTE_PART_ID` |
| `suppliers.csv` / `SUPPLIERS` | 80 | Suppliers in tiers 1–4, with country and region |
| `supplier_parts.csv` / `SUPPLIER_PARTS` | 483 | Tier-1 suppliers of components: capacity per week, lead time, unit price |
| `supplier_dependencies.csv` / `SUPPLIER_DEPENDENCIES` | 81 | `SUPPLIER_ID` depends on `DEPENDS_ON_SUPPLIER_ID` (one tier up) |
| `inventory.csv` / `INVENTORY` | 315 | Stock on hand per part; 13 components are out of stock |
| `customers.csv` / `CUSTOMERS` | 100 | Customers with region |
| `orders.csv` / `ORDERS` | 1,500 | Open orders: customer, product, quantity, due date, value |

## The planted cases

### Case 1: One control board inside eight products

**In the data:** the assembly `P-040` "Control board CB-1" is used in 8 of the 20 products. Six use it directly under the top-level part; two use it one level deeper, inside another assembly:

| Product | Path in the BOM |
|---|---|
| `PR-01` Cold-chain tracker | `P-001 > P-040` |
| `PR-02` Factory gateway | `P-002 > P-053 > P-040` |
| `PR-03` Smart thermostat | `P-003 > P-040` |
| `PR-04` Fleet telematics unit | `P-004 > P-040` |
| `PR-05` Air quality monitor | `P-005 > P-040` |
| `PR-06` Smart meter | `P-006 > P-040` |
| `PR-07` Asset tag | `P-007 > P-040` |
| `PR-08` Edge controller | `P-008 > P-025 > P-040` |

**What we're looking for:** "Which products contain the control board, at any depth?" The answer is `PR-01` to `PR-08`. A query that only looks one level down misses `PR-02` and `PR-08`.

**Why it matters:** you can't know in advance how deep to look. Products range from 3 to 5 levels deep.

### Case 2: A "dual-sourced" sensor with a hidden single point of failure

**In the data:** the control board contains 2 × `P-141` "Temperature sensor TS-9". On paper this part has two independent suppliers, in different countries and regions:

| Tier-1 supplier | Location | Capacity / week | Lead time | Depends on (tier 2) | Which depends on (tier 3) |
|---|---|---|---|---|---|
| `S-T1-02` | China, APAC | 4,800 | 42 days | `S-T2-03` (China) | `S-T3-07` (Canada) |
| `S-T1-05` | Canada, AMER | 2,600 | 14 days | `S-T2-08` (Germany) | `S-T3-07` (Canada) |

Both supply chains run through the same tier-3 supplier, `S-T3-07`.

**What we're looking for:** "If tier-3 supplier `S-T3-07` fails, what is affected?" The failure spreads down the tiers to `S-T2-03`, `S-T2-08`, `S-T1-02` and `S-T1-05`. That leaves `P-141` with no supplier, and through the control board it affects:

| | Result |
|---|---|
| Parts left without any supplier | `P-141` only |
| Affected products | `PR-01` … `PR-08` (case 1) |
| Affected open orders | 568, across all 100 customers |
| Affected order value | 6,840,136.49 |

**Why it matters:** a tier-1 view shows two suppliers, so the risk looks covered. The concentration only appears when you follow supplier dependencies *up* the tiers and then the bill of materials *down* to products. That means two traversals of unknown depth, chained together.

### Case 3: A product that is only buildable with a substitute

**In the data:** `PR-04` "Fleet telematics unit" (`P-004`) directly contains `P-121` "Radio chip RC-2". `P-121` is out of stock, and it's the only out-of-stock component in `PR-04`'s whole bill of materials. `SUBSTITUTES` lists `P-122` "Radio chip RC-2B" as an approved replacement (ratio 1.0), and `P-122` has 2,500 in stock.

**What we're looking for:** "Which products can be built from current stock?" A part counts as available if it's in stock, *or* all its children are available, *or* an approved substitute is available. The rule applies at every level of the bill of materials.

| | Buildable products |
|---|---|
| Ignoring substitutes | 9: `PR-02`, `PR-05`, `PR-10`, `PR-13`, `PR-15`, `PR-16`, `PR-17`, `PR-18`, `PR-19` |
| Including substitutes | 11: the 9 above plus `PR-04` and `PR-09` |

`PR-04` is the planted case, and its 69 open orders depend on the substitute. `PR-09` is also rescued, through one of the 59 randomly generated substitute pairs, which is a realistic side effect.

**Why it matters:** the rule needs "all children" (AND) and "any substitute" (OR) to propagate up a tree of unknown depth.

### Case 4: A cycle in the supplier network

**In the data:** `S-T2-11` (Netherlands) depends on `S-T2-14` (Canada), and `S-T2-14` depends on `S-T2-11`. Large suppliers that trade with each other really do this. Every other dependency points one tier up.

**What we're looking for:** any traversal of `SUPPLIER_DEPENDENCIES` must finish and give the same answer despite the loop. For example: "which suppliers does `S-T1-11` depend on, directly or indirectly?"

**Why it matters:** a naive recursive query loops on these two rows until it hits a recursion limit, unless you add explicit cycle detection.

## Expected results

`expected_results.json` holds the answers above in machine-readable form; the notebook asserts against it.

| Key | Case |
|---|---|
| `shared_subassembly` | 1 |
| `hidden_shared_dependency`, `failure_S_T3_07` | 2 |
| `substitute_rescue`, `buildable_without_substitutes`, `buildable_with_substitutes` | 3 |
| `supplier_cycle` | 4 |
| `min_bom_depth`, `max_bom_depth` | BOM depth range (3–5) |

## Regenerating

```bash
python scripts/generate_data.py
```

Same seed, same files. The script checks that the planted cases hold before writing anything.
