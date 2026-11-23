"""Prepare a Snowflake Ossie export for the Power BI converter.

SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW wraps the model in a `semantic_model:`
list. The ossie-microsoft converter expects the model at the document root, so
this script moves it there. Nothing else is changed.

Usage: python unwrap_snowflake_export.py <snowflake_export.yaml> <out.ossie.yaml>
"""
import sys

import yaml

src, out = sys.argv[1:3]
doc = yaml.safe_load(open(src))

models = doc.get("semantic_model")
if models is None:
    flat = doc
elif len(models) == 1:
    flat = {"version": doc["version"], **models[0]}
else:
    sys.exit(f"expected one model in {src}, found {len(models)}")

with open(out, "w") as f:
    yaml.safe_dump(flat, f, sort_keys=False, allow_unicode=True, width=10000)
print(f"wrote {out}")
