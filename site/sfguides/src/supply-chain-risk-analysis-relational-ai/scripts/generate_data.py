"""Generate the synthetic supply-chain sample data for the RelationalAI notebook quickstart.

Writes CSV files to ../data and the planted scenario answers to ../data/expected_results.json.
Deterministic: the same seed always produces the same files.

    python scripts/generate_data.py
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

rng = random.Random(SEED)

# --------------------------------------------------------------------------- parts
COMPONENT_TYPES = [
    "Temperature sensor", "Humidity sensor", "Pressure sensor", "Microcontroller", "Memory chip",
    "Power regulator", "Capacitor bank", "Resistor array", "Connector", "Antenna", "Battery cell",
    "LED module", "Display glass", "Enclosure shell", "Gasket", "Screw set", "Copper wire",
    "Heat sink", "Crystal oscillator", "Radio chip", "GPS chip", "Fan", "Cable harness",
    "Mounting bracket", "Lens", "Speaker", "Microphone", "Switch", "Fuse", "Label set",
]
ASSEMBLY_TYPES = [
    "Sensor module", "Power module", "Radio module", "Display module", "Housing assembly",
    "Main board", "Battery pack", "Cooling unit", "Interface board", "Antenna assembly",
]
PRODUCT_NAMES = [
    "Cold-chain tracker", "Factory gateway", "Smart thermostat", "Fleet telematics unit",
    "Air quality monitor", "Smart meter", "Asset tag", "Edge controller", "Vibration monitor",
    "Leak detector", "Smart lock", "Warehouse scanner", "Solar inverter monitor", "EV charger board",
    "Medical cooler monitor", "Rail sensor node", "Water flow meter", "Greenhouse controller",
    "Pallet tracker", "Wind turbine monitor",
]

N_PRODUCTS = 20
ASSEMBLY_LEVELS = {1: 20, 2: 15, 3: 15, 4: 10}  # level -> number of assemblies
N_COMPONENTS = 235

parts = []  # dicts: PART_ID, PART_NAME, PART_TYPE, UNIT_COST
level_of = {}


def new_part(name, ptype, cost, level):
    pid = f"P-{len(parts) + 1:03d}"
    parts.append({"PART_ID": pid, "PART_NAME": name, "PART_TYPE": ptype, "UNIT_COST": round(cost, 2)})
    level_of[pid] = level
    return pid


finished = [new_part(f"{PRODUCT_NAMES[i]} final assembly", "FINISHED", rng.uniform(40, 120), 0)
            for i in range(N_PRODUCTS)]
assemblies = {lvl: [new_part(f"{rng.choice(ASSEMBLY_TYPES)} A{lvl}-{k + 1:02d}", "ASSEMBLY",
                             rng.uniform(10, 60), lvl) for k in range(n)]
              for lvl, n in ASSEMBLY_LEVELS.items()}
components = [new_part(f"{rng.choice(COMPONENT_TYPES)} C-{k + 1:03d}", "COMPONENT",
                       rng.uniform(0.2, 25), 5) for k in range(N_COMPONENTS)]
all_assemblies = [p for lvl in sorted(assemblies) for p in assemblies[lvl]]

# Planted parts get fixed, readable names
CONTROL_BOARD = all_assemblies[19]          # shared subassembly used by 8 products
SENSOR_DUAL = components[60]                # "dual-sourced" part with a hidden shared tier-3 dependency
SUB_PRIMARY, SUB_ALT = components[40], components[41]  # PR-04 needs SUB_PRIMARY; SUB_ALT is its substitute
for pid, name in [(CONTROL_BOARD, "Control board CB-1"), (SENSOR_DUAL, "Temperature sensor TS-9"),
                  (SUB_PRIMARY, "Radio chip RC-2"), (SUB_ALT, "Radio chip RC-2B")]:
    next(p for p in parts if p["PART_ID"] == pid)["PART_NAME"] = name
level_of[CONTROL_BOARD] = 2

# --------------------------------------------------------------------------- BOM (a DAG)
bom = {}  # (parent, child) -> qty


def add_edge(parent, child, qty=None):
    if (parent, child) not in bom:
        bom[(parent, child)] = qty or rng.choice([1, 1, 1, 2, 2, 3, 4])


regular_assemblies = [a for a in all_assemblies if a != CONTROL_BOARD]
reserved = {SENSOR_DUAL, SUB_PRIMARY, SUB_ALT}
free_components = [c for c in components if c not in reserved]

for top in finished:
    for child in rng.sample([a for a in regular_assemblies if level_of[a] <= 3], rng.randint(2, 4)):
        add_edge(top, child, 1)
    for child in rng.sample(free_components, rng.randint(1, 3)):
        add_edge(top, child)
for a in regular_assemblies:
    deeper = [b for b in regular_assemblies if level_of[b] > level_of[a]]
    for child in rng.sample(deeper, min(len(deeper), rng.randint(0, 2))):
        add_edge(a, child, rng.choice([1, 1, 2]))
    for child in rng.sample(free_components, rng.randint(2, 5)):
        add_edge(a, child)
# make sure every component is used at least once
used = {c for _, c in bom}
for c in free_components:
    if c not in used:
        add_edge(rng.choice(regular_assemblies), c)
# control board: its own components
for child in rng.sample(free_components, 4):
    add_edge(CONTROL_BOARD, child)
add_edge(CONTROL_BOARD, SENSOR_DUAL, 2)


def children(p):
    return [c for (a, c) in bom if a == p]


def descendants(p):
    seen, stack = set(), [p]
    while stack:
        for c in children(stack.pop()):
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return seen


def depth(p):
    cs = children(p)
    return 0 if not cs else 1 + max(depth(c) for c in cs)


# Attach the control board under 8 products, at different depths, using parent parts that
# are not shared with other products, so exactly 8 products contain it.
def owners(p):
    return {t for t in finished if p == t or p in descendants(t)}


cb_products = finished[:8]
for i, top in enumerate(cb_products):
    if i % 2 == 0:
        add_edge(top, CONTROL_BOARD, 1)  # directly under the product
    else:
        exclusive = [a for a in descendants(top) if a in regular_assemblies and owners(a) == {top}]
        add_edge(max(exclusive, key=lambda a: level_of[a]) if exclusive else top, CONTROL_BOARD, 1)

# PR-04 (finished[3]) needs SUB_PRIMARY, via a part used only by PR-04
pr04 = finished[3]
pr04_exclusive = [a for a in descendants(pr04) if a in regular_assemblies and owners(a) == {pr04}]
add_edge(pr04_exclusive[0] if pr04_exclusive else pr04, SUB_PRIMARY, 1)

# --------------------------------------------------------------------------- substitutes
substitutes = {(SUB_PRIMARY, SUB_ALT): 1.0}
while len(substitutes) < 60:
    a, b = rng.sample(free_components, 2)
    substitutes.setdefault((a, b), rng.choice([1.0, 1.0, 2.0]))

# --------------------------------------------------------------------------- suppliers
REGIONS = {"EMEA": ["Germany", "Netherlands", "Poland", "Italy"],
           "AMER": ["United States", "Mexico", "Canada"],
           "APAC": ["China", "Taiwan", "Vietnam", "Malaysia", "Japan"]}
TIER_SIZES = {1: 30, 2: 25, 3: 15, 4: 10}
suppliers = []
for tier, n in TIER_SIZES.items():
    for k in range(1, n + 1):
        region = rng.choice(list(REGIONS))
        suppliers.append({"SUPPLIER_ID": f"S-T{tier}-{k:02d}", "SUPPLIER_NAME": f"Supplier T{tier}-{k:02d}",
                          "TIER": tier, "COUNTRY": rng.choice(REGIONS[region]), "REGION": region})
by_tier = {t: [s["SUPPLIER_ID"] for s in suppliers if s["TIER"] == t] for t in TIER_SIZES}

# tier-1 suppliers supply components
supplies = {}
PLANTED_T1 = ["S-T1-02", "S-T1-05"]  # supply only the planted dual-sourced sensor
for c in components:
    if c == SENSOR_DUAL:
        chosen = PLANTED_T1
    else:
        chosen = rng.sample([s for s in by_tier[1] if s not in PLANTED_T1], rng.choice([1, 2, 2, 3]))
    for s in chosen:
        supplies[(s, c)] = {"CAPACITY_PER_WEEK": rng.randrange(200, 5000, 50),
                            "LEAD_TIME_DAYS": rng.choice([7, 14, 21, 28, 42, 56]),
                            "UNIT_PRICE": round(next(p for p in parts if p["PART_ID"] == c)["UNIT_COST"]
                                                * rng.uniform(0.9, 1.3), 2)}

# tier-N dependencies: tier t depends on tier t+1
depends = set()
planted = {"S-T1-02": ["S-T2-03"], "S-T1-05": ["S-T2-08"], "S-T2-03": ["S-T3-07"], "S-T2-08": ["S-T3-07"]}
for s, targets in planted.items():
    for t in targets:
        depends.add((s, t))
for tier in (1, 2, 3):
    for s in by_tier[tier]:
        if s in planted:
            continue
        pool = [x for x in by_tier[tier + 1] if x not in {"S-T3-07", "S-T2-03", "S-T2-08"}]
        for t in rng.sample(pool, rng.choice([1, 1, 2]) if tier < 3 else rng.choice([0, 1])):
            depends.add((s, t))
depends |= {("S-T2-11", "S-T2-14"), ("S-T2-14", "S-T2-11")}  # planted cycle

# --------------------------------------------------------------------------- inventory
pr04_tree = descendants(pr04)
stockouts = set(rng.sample([c for c in free_components if c not in pr04_tree], 12)) | {SUB_PRIMARY}
inventory = {}
for p in parts:
    pid = p["PART_ID"]
    if p["PART_TYPE"] == "COMPONENT":
        inventory[pid] = 0 if pid in stockouts else rng.randrange(50, 3000, 10)
    elif p["PART_TYPE"] == "ASSEMBLY":
        inventory[pid] = rng.choice([0, 0, 0, 0, 25, 60])
    else:
        inventory[pid] = 0
inventory[SUB_ALT] = 2500

# --------------------------------------------------------------------------- customers and orders
customers = [{"CUSTOMER_ID": f"C-{k:03d}", "CUSTOMER_NAME": f"Customer {k:03d}",
              "REGION": rng.choice(list(REGIONS))} for k in range(1, 101)]
products = [{"PRODUCT_ID": f"PR-{i + 1:02d}", "PRODUCT_NAME": PRODUCT_NAMES[i], "PART_ID": finished[i],
             "LIST_PRICE": round(rng.uniform(120, 900), 2)} for i in range(N_PRODUCTS)]
orders = []
start = date(2026, 11, 2)
for k in range(1, 1501):
    prod = rng.choice(products)
    qty = rng.randint(1, 50)
    orders.append({"ORDER_ID": f"O-{k:05d}", "CUSTOMER_ID": rng.choice(customers)["CUSTOMER_ID"],
                   "PRODUCT_ID": prod["PRODUCT_ID"], "QUANTITY": qty,
                   "DUE_DATE": (start + timedelta(days=rng.randint(0, 90))).isoformat(),
                   "ORDER_VALUE": round(qty * prod["LIST_PRICE"], 2)})

# --------------------------------------------------------------------------- expected results
part_to_product = {p["PART_ID"]: p["PRODUCT_ID"] for p in products}


def products_containing(part):
    return sorted(part_to_product[t] for t in finished if part in descendants(t))


def buildable(use_substitutes):
    memo = {}
    subs = {}
    for (a, b) in substitutes:
        subs.setdefault(a, []).append(b)

    def ok(p, path=()):
        if p in memo:
            return memo[p]
        res = inventory.get(p, 0) > 0
        if not res and children(p):
            res = all(ok(c, path + (p,)) for c in children(p))
        if not res and use_substitutes:
            res = any(ok(s, path + (p,)) for s in subs.get(p, []) if s not in path)
        memo[p] = res
        return res

    return sorted(part_to_product[t] for t in finished if ok(t))


def failed_suppliers(root):
    failed, stack = {root}, [root]
    while stack:
        x = stack.pop()
        for (s, t) in depends:
            if t == x and s not in failed:
                failed.add(s)
                stack.append(s)
    return failed


failed = failed_suppliers("S-T3-07")
supplier_of = {}
for (s, c) in supplies:
    supplier_of.setdefault(c, set()).add(s)
lost_parts = sorted(c for c, ss in supplier_of.items() if ss <= failed)
affected_products = sorted({pr for c in lost_parts for pr in products_containing(c)})
affected_orders = [o for o in orders if o["PRODUCT_ID"] in affected_products]

expected = {
    "seed": SEED,
    "shared_subassembly": {"part_id": CONTROL_BOARD, "products": products_containing(CONTROL_BOARD)},
    "hidden_shared_dependency": {
        "tier3_supplier": "S-T3-07", "tier1_suppliers": ["S-T1-02", "S-T1-05"], "part_id": SENSOR_DUAL},
    "supplier_cycle": ["S-T2-11", "S-T2-14"],
    "substitute_rescue": {"product_id": "PR-04", "part_id": SUB_PRIMARY, "substitute_part_id": SUB_ALT},
    "buildable_without_substitutes": buildable(False),
    "buildable_with_substitutes": buildable(True),
    "failure_S_T3_07": {
        "failed_suppliers": sorted(failed), "parts_without_supply": lost_parts,
        "affected_products": affected_products, "affected_open_orders": len(affected_orders),
        "affected_order_value": round(sum(o["ORDER_VALUE"] for o in affected_orders), 2)},
    "max_bom_depth": max(depth(t) for t in finished),
    "min_bom_depth": min(depth(t) for t in finished),
}

# sanity checks on the planted scenarios
assert len(expected["shared_subassembly"]["products"]) == 8, expected["shared_subassembly"]
assert "PR-04" in expected["buildable_with_substitutes"] and "PR-04" not in expected["buildable_without_substitutes"]
assert lost_parts == [SENSOR_DUAL], lost_parts
assert affected_products == expected["shared_subassembly"]["products"], affected_products

# --------------------------------------------------------------------------- write files
DATA_DIR.mkdir(exist_ok=True)


def write(name, rows, columns):
    with open(DATA_DIR / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)
    print(f"{name:28s} {len(rows):6d} rows")


write("parts.csv", parts, ["PART_ID", "PART_NAME", "PART_TYPE", "UNIT_COST"])
write("products.csv", products, ["PRODUCT_ID", "PRODUCT_NAME", "PART_ID", "LIST_PRICE"])
write("bom.csv", [{"PARENT_PART_ID": a, "CHILD_PART_ID": c, "QTY_PER": q} for (a, c), q in sorted(bom.items())],
      ["PARENT_PART_ID", "CHILD_PART_ID", "QTY_PER"])
write("substitutes.csv", [{"PART_ID": a, "SUBSTITUTE_PART_ID": b, "RATIO": r} for (a, b), r in sorted(substitutes.items())],
      ["PART_ID", "SUBSTITUTE_PART_ID", "RATIO"])
write("suppliers.csv", suppliers, ["SUPPLIER_ID", "SUPPLIER_NAME", "TIER", "COUNTRY", "REGION"])
write("supplier_parts.csv", [{"SUPPLIER_ID": s, "PART_ID": c, **v} for (s, c), v in sorted(supplies.items())],
      ["SUPPLIER_ID", "PART_ID", "CAPACITY_PER_WEEK", "LEAD_TIME_DAYS", "UNIT_PRICE"])
write("supplier_dependencies.csv", [{"SUPPLIER_ID": s, "DEPENDS_ON_SUPPLIER_ID": t} for (s, t) in sorted(depends)],
      ["SUPPLIER_ID", "DEPENDS_ON_SUPPLIER_ID"])
write("inventory.csv", [{"PART_ID": k, "ON_HAND_QTY": v} for k, v in inventory.items()], ["PART_ID", "ON_HAND_QTY"])
write("customers.csv", customers, ["CUSTOMER_ID", "CUSTOMER_NAME", "REGION"])
write("orders.csv", orders, ["ORDER_ID", "CUSTOMER_ID", "PRODUCT_ID", "QUANTITY", "DUE_DATE", "ORDER_VALUE"])
(DATA_DIR / "expected_results.json").write_text(json.dumps(expected, indent=2) + "\n")
print(json.dumps({k: v for k, v in expected.items() if k != "failure_S_T3_07"}, indent=1))
print(json.dumps(expected["failure_S_T3_07"], indent=1))
