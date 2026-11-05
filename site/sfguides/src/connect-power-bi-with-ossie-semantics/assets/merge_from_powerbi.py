"""Merge Power BI measure changes into the Ossie model exported from Snowflake.

The Snowflake export stays the base. Only measure changes made in Power BI are
copied in: new measures, edited DAX, and edited descriptions. Tables, fields,
keys, relationships, and existing SQL come from the base unchanged.

A measure counts as changed when its DAX differs from both the model.bim that
was originally exported and the DAX already in the base, so re-running the
merge is safe. New or changed measures need a SNOWFLAKE expression; the script
lists them and exits 1 until one exists.

Usage: python merge_from_powerbi.py <base.ossie.yaml> <original.bim> <imported.ossie.yaml> <out.ossie.yaml>
"""
import json
import sys

import yaml

base_path, original_bim, imported_path, out_path = sys.argv[1:5]
base = yaml.safe_load(open(base_path))
imported = yaml.safe_load(open(imported_path))
bim = json.load(open(original_bim, encoding="utf-8-sig"))
exported_dax = {m["name"]: m["expression"] for t in bim["model"]["tables"] for m in t.get("measures", [])}

# Snowflake accepts Ossie 0.1.1 with the model at the document root
if "semantic_model" in base:
    base = {"version": base["version"], **base["semantic_model"][0]}
base["version"] = "0.1.1"


def expression(metric, dialect):
    return next((d["expression"] for d in metric["expression"]["dialects"] if d["dialect"] == dialect), None)


metrics = {m["name"]: m for m in base.get("metrics", [])}
changes, needs_sql = [], []

for pbi in imported.get("metrics", []):
    name, dax = pbi["name"], expression(pbi, "DAX")
    metric = metrics.get(name)
    if metric is None:
        metric = {"name": name, "expression": {"dialects": [{"dialect": "DAX", "expression": dax}]}}
        base.setdefault("metrics", []).append(metric)
        changes.append(f"added {name}")
    elif dax not in (exported_dax.get(name), expression(metric, "DAX")):
        metric["expression"]["dialects"] = [{"dialect": "DAX", "expression": dax}]
        changes.append(f"changed DAX for {name}")
    if pbi.get("description") and pbi["description"] != metric.get("description"):
        metric["description"] = pbi["description"]
        changes.append(f"changed description for {name}")
    if expression(metric, "SNOWFLAKE") is None:
        needs_sql.append(name)

for name in sorted(set(metrics) - {m["name"] for m in imported.get("metrics", [])}):
    print(f"WARNING: {name} was removed in Power BI; kept in the merged model", file=sys.stderr)

with open(out_path, "w") as f:
    yaml.safe_dump(base, f, sort_keys=False, allow_unicode=True, width=10000)

print("\n".join(changes) if changes else "no measure changes")
for name in needs_sql:
    print(f"NEEDS SQL: add a SNOWFLAKE expression for {name} before deploying", file=sys.stderr)
sys.exit(1 if needs_sql else 0)
