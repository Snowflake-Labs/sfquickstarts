author: Reinout Korbee
id: getting-started-with-notebooks-relational-ai
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/ai
language: en
summary: Set up RelationalAI PyRel in a Snowflake Notebook on Container Runtime and query a semantic model built on Snowflake tables, with no config file and no credentials.
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, RelationalAI, PyRel, Semantic Model, Snowflake Notebooks, Container Runtime

# Getting Started with RelationalAI in Snowflake Notebooks
<!-- ------------------------ -->
## Overview

[RelationalAI](https://docs.relational.ai/) adds a semantic modeling and reasoning layer to Snowflake. You build models in Python with **PyRel**: *concepts* (suppliers, parts, products), *properties* (a supplier's name) and *relationships* (a supplier supplies a part).

The official [Start building with PyRel](https://docs.relational.ai/get-started/start-building-with-pyrel) guide runs from a local terminal and needs `uv`, a `raiconfig.yaml` file and a browser sign-in. A Snowflake Notebook already has an authenticated session, a warehouse and your data. This guide shows the shortest path from there to a first PyRel query.

You answer the same question as the official guide: *If Northstar Components can't deliver, which products depend on parts it supplies?* This time the data lives in Snowflake tables.

### What You Will Learn
- Which network access a notebook needs for PyRel
- How to install PyRel in a Container Runtime notebook, and why the kernel restart matters
- How PyRel reuses the notebook session, so you need no `raiconfig.yaml`
- How to map Snowflake tables to a semantic model with `model.Table()` and query it

### What You Will Build
A Snowflake Notebook that builds a supplier-disruption semantic model over five Snowflake tables and returns the affected products.

### Prerequisites
- A Snowflake account with the [RelationalAI Native App](https://app.snowflake.com/marketplace/listing/GZTYZOOIX8H/relationalai-relationalai) installed and activated ([setup guide](https://docs.relational.ai/get-started/set-up-relationalai-in-snowflake))
- `ACCOUNTADMIN`, or an administrator who runs the setup script for you
- A user with the `RAI_DEVELOPER` role

<!-- ------------------------ -->
## Admin Setup

Run [`scripts/admin_setup.sql`](scripts/admin_setup.sql) as `ACCOUNTADMIN`. It does four things.

**1. Checks that the RelationalAI app is healthy.**

```sql
CALL RELATIONALAI.APP.SERVICE_STATUS();  -- main and otel-collector: READY
CALL RELATIONALAI.APP.CDC_STATUS();      -- CDC_ENABLED = TRUE
```

These are procedures, so use `CALL`, not `SELECT`. A `SUSPENDED` CDC engine is normal while idle.

**2. Creates the `RAI_QUICKSTART.SUPPLY` schema.**

**3. Creates an external access integration with two egress rules.** You need both:

| Rule | Why |
|---|---|
| `SNOWFLAKE.EXTERNAL_ACCESS.PYPI_RULE` | `relationalai` is not in the Snowflake Anaconda channel, so you install it from PyPI. |
| RelationalAI results host | PyRel downloads query results from a presigned URL on the RelationalAI app's S3 stage. Without this rule the query reaches the engine, then fails with `Max retries exceeded ... HTTPSConnectionPool(host='sfc-...-customer-stage.s3.<region>.amazonaws.com')`. |

The results host depends on your account and region. The script contains an example value. If your first query fails with the error above, copy the host from the message into the network rule.

**4. Grants `RAI_DEVELOPER` usage on the integration, database, warehouse and `SYSTEM_COMPUTE_POOL_CPU`.**

<!-- ------------------------ -->
## Load the Sample Data

Run [`scripts/load_sample_data.sql`](scripts/load_sample_data.sql) as `RAI_DEVELOPER`, with the database and schema names set to `RAI_QUICKSTART.SUPPLY`. It creates five small tables from the official starter project:

| Table | Content |
|---|---|
| `SUPPLIERS` | `SUPPLIER_ID`, `SUPPLIER_NAME` |
| `PARTS` | `PART_ID`, `PART_NAME` |
| `PRODUCTS` | `PRODUCT_ID`, `PRODUCT_NAME` |
| `SUPPLIER_PARTS` | which supplier supplies which part |
| `PRODUCT_PARTS` | which product requires which part |

The tables are created with `CHANGE_TRACKING = TRUE`, because RelationalAI keeps its copy of source tables in sync through change data capture (CDC).

<!-- ------------------------ -->
## Create the Notebook

1. In Snowsight, go to **Projects » Notebooks** and select **+ Notebook**.
2. Set **Runtime** to **Run on container**. The warehouse runtime cannot pip install from PyPI.
3. Set **Compute pool** to `SYSTEM_COMPUTE_POOL_CPU` and **Query warehouse** to `COMPUTE_WH`.
4. Open **⋮ » Notebook settings » External access** and enable `RAI_NOTEBOOK_ACCESS`.

The Container Runtime image ships Python 3.10, the lowest version PyRel supports.

<!-- ------------------------ -->
## Install PyRel

In the first cell, install PyRel:

```python
%pip install -q "relationalai>=1.30.1,<2.0"
```

pip reports dependency conflicts for `mlruntimes-service` and `opentelemetry-proto`. You can ignore them for this guide.

> **Restart the kernel now.** The install upgrades `protobuf` from 4.25 to 5.x, but the kernel still has the old version loaded. If you skip the restart, the first query fails with `ImportError: cannot import name 'runtime_version' from 'google.protobuf'`. Clearing modules from `sys.modules` does not help, because protobuf's compiled extension stays loaded. Use the **Restart** option in the kernel menu, then continue with the next cell. Don't rerun the install cell.

Check the install:

```python
import importlib.metadata as md
print(md.version("relationalai"), md.version("protobuf"))
```

<!-- ------------------------ -->
## Connect

In a notebook, PyRel detects the active Snowpark session automatically:

```python
from relationalai.config import create_config
cfg = create_config()
print(type(cfg).__name__)   # ConfigFromActiveSession
```

You don't need a `raiconfig.yaml`, a password or a token. PyRel runs with the notebook's role and warehouse.

<!-- ------------------------ -->
## Define the Model

```python
from relationalai.semantics import Model, String

model = Model("SupplierDisruption", config=cfg)

Supplier = model.Concept("Supplier", identify_by={"supplier_id": String})
Supplier.name = model.Property(f"{Supplier} has {String:name}")

Part = model.Concept("Part", identify_by={"part_id": String})
Part.name = model.Property(f"{Part} has {String:name}")

Product = model.Concept("Product", identify_by={"product_id": String})
Product.name = model.Property(f"{Product} has {String:name}")

Supplier.supplies = model.Relationship(f"{Supplier} supplies {Part}")
Product.requires = model.Relationship(f"{Product} requires {Part}")
```

- `identify_by` sets each concept's key: rows with the same `supplier_id` refer to the same supplier.
- `Property` holds a single value per entity, here a name.
- `Relationship` can connect one entity to many others.

<!-- ------------------------ -->
## Map Snowflake Tables

`model.Table()` replaces the official guide's `model.data(read_csv(...))`. Column names are upper case, as Snowflake stores them.

```python
DB = "RAI_QUICKSTART.SUPPLY"
suppliers      = model.Table(f"{DB}.SUPPLIERS")
parts          = model.Table(f"{DB}.PARTS")
products       = model.Table(f"{DB}.PRODUCTS")
supplier_parts = model.Table(f"{DB}.SUPPLIER_PARTS")
product_parts  = model.Table(f"{DB}.PRODUCT_PARTS")

model.define(s := Supplier.new(supplier_id=suppliers.SUPPLIER_ID), s.name(suppliers.SUPPLIER_NAME))
model.define(p := Part.new(part_id=parts.PART_ID), p.name(parts.PART_NAME))
model.define(pr := Product.new(product_id=products.PRODUCT_ID), pr.name(products.PRODUCT_NAME))

model.define(Supplier.lookup(supplier_id=supplier_parts.SUPPLIER_ID)
             .supplies(Part.lookup(part_id=supplier_parts.PART_ID)))
model.define(Product.lookup(product_id=product_parts.PRODUCT_ID)
             .requires(Part.lookup(part_id=product_parts.PART_ID)))
```

`new()` creates an entity, or finds it if one with that key already exists. `lookup()` only finds existing entities, which is why the relationship rows use it.

<!-- ------------------------ -->
## Query the Model

```python
supplier, part, product = Supplier.ref(), Part.ref(), Product.ref()

affected = model.where(
    supplier.name == "Northstar Components",
    supplier.supplies(part),
    product.requires(part),
).select(
    product.name.alias("product"),
    part.name.alias("part"),
).to_df()
affected
```

The first query takes longer, because RelationalAI resumes an engine and loads the tables. Expected output (row order may differ):

| product | part |
|---|---|
| Cold-chain tracker | Control board |
| Cold-chain tracker | Temperature sensor |
| Factory gateway | Control board |
| Smart thermostat | Temperature sensor |

Check the result:

```python
expected = {("Cold-chain tracker", "Control board"), ("Cold-chain tracker", "Temperature sensor"),
            ("Factory gateway", "Control board"), ("Smart thermostat", "Temperature sensor")}
assert set(map(tuple, affected[["product", "part"]].values.tolist())) == expected
print("Matches the official PyRel example")
```

<!-- ------------------------ -->
## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `pip install` hangs or can't reach PyPI | External access not enabled, or warehouse runtime | Use Container Runtime and enable `RAI_NOTEBOOK_ACCESS` |
| `cannot import name 'runtime_version' from 'google.protobuf'` | Kernel not restarted after install | Restart the kernel, then rerun from the Connect step |
| `TypeError: A Message class can only inherit from Message` | Modules purged instead of restarting the kernel | Restart the kernel |
| `Max retries exceeded ... customer-stage.s3...amazonaws.com` | Results host not allowed in the integration | Add the host from the error to `RAI_RESULTS_RULE` |
| `[Unknown Table] Failed to fetch schema for table` | Role can't see the table, or wrong name | Check grants and the fully qualified upper-case name |
| `Unknown user-defined function RELATIONALAI.APP.SERVICE_STATUS` | Called with `SELECT` | Use `CALL` |
| `ConfigFileNotFoundError` | Code running outside the notebook kernel (for example, a subprocess) | Run PyRel in the notebook kernel itself |

<!-- ------------------------ -->
## Cleanup

```sql
DROP DATABASE IF EXISTS RAI_QUICKSTART;
DROP INTEGRATION IF EXISTS RAI_NOTEBOOK_ACCESS;
```

Also delete the notebook in Snowsight if you created it outside `RAI_QUICKSTART`.

<!-- ------------------------ -->
## Conclusion and Resources

You built and queried a RelationalAI semantic model from a Snowflake Notebook, using the notebook's session and your Snowflake tables.

### What You Learned
- A Container Runtime notebook needs PyPI egress plus egress to the RelationalAI results host
- After `pip install relationalai`, restart the kernel
- `create_config()` picks up the notebook session, so you need no config file or credentials
- `model.Table()` maps Snowflake tables directly into concepts and relationships

### Related Resources
- [Start building with PyRel](https://docs.relational.ai/get-started/start-building-with-pyrel)
- [Set up RelationalAI in Snowflake](https://docs.relational.ai/get-started/set-up-relationalai-in-snowflake)
- [RelationalAI project templates](https://docs.relational.ai/build/templates)
- [Snowflake Notebooks on Container Runtime](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-on-spcs)
