author: Eric Tolotti
id: connect-power-bi-with-ossie-semantics
summary: Move a semantic model between a Snowflake Semantic View and a Power BI semantic model using Apache Ossie, and round-trip changes from Power BI back to Snowflake
title: Connect Power BI with OSSIE Semantics
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Connect Power BI with OSSIE Semantics

<!-- ------------------------ -->
## Overview

Business definitions drift when every tool keeps its own copy. Revenue is defined one way in Snowflake, another way in a Power BI semantic model, and nobody notices until the numbers disagree in a meeting.

Apache Ossie (incubating), previously Open Semantic Interchange (OSI), is a vendor-neutral YAML standard for semantic models: datasets, relationships, dimensions, and metrics. Snowflake reads and writes Ossie natively, and the Apache Ossie project provides an open-source converter for Power BI. Ossie becomes the interchange format between the two platforms.

This quickstart walks through a full round trip on TPC-H sample data:

1. Create a Snowflake Semantic View and change it.
2. Export it to Ossie and convert it to a Power BI semantic model.
3. Add a measure in Power BI.
4. Bring that measure back into Snowflake, review it, and deploy it.
5. Run the loop again and confirm nothing was lost.

The end-to-end workflow looks like this:

```
 Snowflake Semantic View
   |  SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW
   v
 Ossie YAML  --- ossie-microsoft export --->  Power BI model.bim
   ^                                               |
   |  SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML  |  edit a measure
   |                                               v
 Merged Ossie YAML  <--- merge + review ---  ossie-microsoft import
```

### Prerequisites
- familiarity with [Snowflake Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- familiarity with Power BI semantic models and DAX
- comfort running commands in a terminal

### What You Will Learn
- creating a Snowflake Semantic View from YAML
- exporting a semantic view to Ossie with `SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW`
- converting Ossie to and from a Power BI `model.bim` with the `ossie-microsoft` converter
- merging a Power BI change back into the Ossie model and deploying it with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML`
- which kinds of changes survive a round trip, and which don't

### What You Will Build
- A sales semantic model that exists in both Snowflake and Power BI, with a measure authored in Power BI that is governed and deployed in Snowflake.

### What You Will Need
- A free [Snowflake Account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with access to `SNOWFLAKE_SAMPLE_DATA`
- Git, Python 3.10+, and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed locally (`pip install uv` works if you don't have it)
- A text editor, or [Tabular Editor](https://github.com/TabularEditor/TabularEditor) to edit the Power BI model file


<!-- ------------------------ -->
## Set Up Snowflake

### Create the sample data

Create a database with views over the TPC-H sample data. The model uses three tables: orders, customers, and nations.

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS OSSIE_DEMO;

CREATE OR REPLACE VIEW OSSIE_DEMO.PUBLIC.ORDERS AS
SELECT O_ORDERKEY, O_CUSTKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;

CREATE OR REPLACE VIEW OSSIE_DEMO.PUBLIC.CUSTOMER AS
SELECT C_CUSTKEY, C_NAME, C_NATIONKEY, C_MKTSEGMENT
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER;

CREATE OR REPLACE VIEW OSSIE_DEMO.PUBLIC.NATION AS
SELECT N_NATIONKEY, N_NAME
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION;
```

### Create the semantic view

The semantic view is defined in [tpch_sales_semantic_view.yaml](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/connect-power-bi-with-ossie-semantics/assets/tpch_sales_semantic_view.yaml). It joins orders to customers and customers to nations, and defines two metrics: `total_sales` and `order_count`.

Paste the file contents between the `$$` markers and run:

```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
    'OSSIE_DEMO.PUBLIC',
    $$
    <paste the contents of tpch_sales_semantic_view.yaml here>
    $$
);
```

The view takes its name from the `name` field, so this creates `OSSIE_DEMO.PUBLIC.TPCH_SALES`. Confirm it returns data:

```sql
SELECT * FROM SEMANTIC_VIEW(
    OSSIE_DEMO.PUBLIC.TPCH_SALES
    DIMENSIONS nation.n_name
    METRICS total_sales, order_count
) ORDER BY total_sales DESC LIMIT 3;
```

### Make a change in Snowflake

Add an average order value metric. In the YAML file, add this entry at the end of the `metrics:` list:

```yaml
- name: avg_order_value
  expr: AVG(orders.o_totalprice)
  description: Average value of a single order
```

Run the same `CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML` statement again with the updated file. It replaces the semantic view. Check the new metric:

```sql
SELECT * FROM SEMANTIC_VIEW(
    OSSIE_DEMO.PUBLIC.TPCH_SALES
    DIMENSIONS customer.c_mktsegment
    METRICS total_sales, order_count, avg_order_value
) ORDER BY c_mktsegment;
```


<!-- ------------------------ -->
## Export to Ossie

### Install the Power BI converter

Clone the Apache Ossie repository and install the Microsoft converter. Then download the two helper scripts for this guide into the same working folder.

```bash
mkdir -p ~/ossie-demo && cd ~/ossie-demo
git clone https://github.com/apache/ossie.git

curl -O https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/connect-power-bi-with-ossie-semantics/assets/unwrap_snowflake_export.py
curl -O https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/connect-power-bi-with-ossie-semantics/assets/merge_from_powerbi.py

cd ossie/converters/microsoft
uv sync
uv run ossie-microsoft --help
```

Run the remaining commands in this guide from `~/ossie-demo/ossie/converters/microsoft`. The working files live in `~/ossie-demo`.

### Export the semantic view

In Snowflake, export the semantic view as Ossie YAML:

```sql
SELECT SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW('OSSIE_DEMO.PUBLIC.TPCH_SALES');
```

Copy the result and save it as `~/ossie-demo/tpch_sales_export.yaml`.

The export contains the three datasets with full `OSSIE_DEMO.PUBLIC.<TABLE>` sources, the relationships, the `O_ORDERDATE` time dimension, and all three metrics as `SNOWFLAKE` SQL expressions. Names are uppercase because Snowflake normalizes unquoted identifiers.

### Prepare it for the converter

Snowflake wraps the model in a `semantic_model:` list. The Power BI converter expects the model at the top of the file, so move it there:

```bash
uv run python ~/ossie-demo/unwrap_snowflake_export.py \
    ~/ossie-demo/tpch_sales_export.yaml \
    ~/ossie-demo/tpch_sales.ossie.yaml
```

`tpch_sales.ossie.yaml` is the Ossie model you will work from.


<!-- ------------------------ -->
## Convert to Power BI

Convert the Ossie model to a Power BI semantic model in TMSL `model.bim` format:

```bash
uv run ossie-microsoft export \
    -i ~/ossie-demo/tpch_sales.ossie.yaml \
    -o ~/ossie-demo/model.bim
```

Keep an untouched copy. The merge step later compares against it to find what changed in Power BI:

```bash
cp ~/ossie-demo/model.bim ~/ossie-demo/model.original.bim
```

### What the converter produced

The three tables, their columns, and both relationships carry over. Each Snowflake metric becomes a DAX measure:

| Snowflake metric (SQL) | Power BI measure (DAX) |
|---|---|
| `SUM(orders.o_totalprice)` | `SUM('ORDERS'[O_TOTALPRICE])` |
| `COUNT(orders.o_orderkey)` | `COUNTA('ORDERS'[O_ORDERKEY])` |
| `AVG(orders.o_totalprice)` | `AVERAGE('ORDERS'[O_TOTALPRICE])` |

The converter translates simple aggregates such as `SUM`, `COUNT`, `COUNT(DISTINCT ...)`, `AVG`, and division of those. A SQL expression outside that set becomes a `BLANK()` measure with a warning instead of a guessed formula.

The converter prints warnings and ends with a count of constructs it couldn't convert faithfully. For this model they are expected:

- The file targets Ossie `0.1.1` and the converter targets `0.2.0.dev0`. The model in this guide converts fully despite the mismatch.
- Snowflake-specific settings stored in `SNOWFLAKE` custom extensions have no Power BI equivalent and are dropped from `model.bim`.
- Metrics have no home table in Ossie, so all measures are placed on the first table, `CUSTOMER`.
- The table partitions use Direct Lake with placeholder workspace and item IDs. The model definition is complete, but it isn't connected to data. Connecting it is outside the scope of this guide.


<!-- ------------------------ -->
## Make a Change in Power BI

An analyst adds a measure in Power BI: total sales divided by the number of distinct customers.

Open `~/ossie-demo/model.bim` in Tabular Editor or a text editor. Find the `CUSTOMER` table's `measures` list and add this entry at the end of the list. Put a comma after the measure before it:

```json
{
  "name": "SALES_PER_CUSTOMER",
  "expression": "DIVIDE(SUM('ORDERS'[O_TOTALPRICE]), DISTINCTCOUNT('ORDERS'[O_CUSTKEY]))",
  "description": "Average total order value per customer"
}
```

Save the file.

Choose a measure the converter can translate back from SQL, like this one. On the next export from Snowflake, a measure with a filter, such as `CALCULATE(..., 'ORDERS'[O_ORDERSTATUS] = "F")`, comes back to Power BI as `BLANK()`, because Snowflake stores only the SQL.


<!-- ------------------------ -->
## Bring the Change Back to Snowflake

### Convert Power BI back to Ossie

```bash
uv run ossie-microsoft import \
    -i ~/ossie-demo/model.bim \
    -o ~/ossie-demo/tpch_sales.imported.yaml
```

Don't deploy this file directly. The import writes Ossie version `0.2.0.dev0`, which Snowflake doesn't accept yet. It also writes two-part table names such as `PUBLIC.ORDERS`, and returns every metric as DAX only.

### Merge the change

Merge only the measure changes into the model you exported from Snowflake. That keeps the full table names, the time dimension, and the existing SQL:

```bash
uv run python ~/ossie-demo/merge_from_powerbi.py \
    ~/ossie-demo/tpch_sales.ossie.yaml \
    ~/ossie-demo/model.original.bim \
    ~/ossie-demo/tpch_sales.imported.yaml \
    ~/ossie-demo/tpch_sales.merged.yaml
```

The script reports what changed and stops on anything that has no Snowflake SQL yet:

```
added SALES_PER_CUSTOMER
changed description for SALES_PER_CUSTOMER
NEEDS SQL: add a SNOWFLAKE expression for SALES_PER_CUSTOMER before deploying
```

Compare the two files to see exactly what Power BI changed:

```bash
diff ~/ossie-demo/tpch_sales.ossie.yaml ~/ossie-demo/tpch_sales.merged.yaml
```

### Add the Snowflake SQL

This is the review step. The converter never rewrites DAX as SQL, so a person writes the SQL equivalent and approves the definition before it reaches Snowflake.

In `tpch_sales.merged.yaml`, add a `SNOWFLAKE` dialect to `SALES_PER_CUSTOMER`:

```yaml
- name: SALES_PER_CUSTOMER
  expression:
    dialects:
    - dialect: SNOWFLAKE
      expression: SUM(orders.o_totalprice) / COUNT(DISTINCT orders.o_custkey)
    - dialect: DAX
      expression: DIVIDE(SUM('ORDERS'[O_TOTALPRICE]), DISTINCTCOUNT('ORDERS'[O_CUSTKEY]))
  description: Average total order value per customer
```

Run the merge again with the merged file as the base to confirm nothing is missing:

```bash
uv run python ~/ossie-demo/merge_from_powerbi.py \
    ~/ossie-demo/tpch_sales.merged.yaml \
    ~/ossie-demo/model.original.bim \
    ~/ossie-demo/tpch_sales.imported.yaml \
    ~/ossie-demo/tpch_sales.merged.yaml
```

It reports `no measure changes` and exits cleanly, so the file is ready to deploy.

### Deploy to Snowflake

Paste the contents of `tpch_sales.merged.yaml` between the `$$` markers and run:

```sql
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML(
    'OSSIE_DEMO.PUBLIC',
    $$
    <paste the contents of tpch_sales.merged.yaml here>
    $$
);
```

The model is named `TPCH_SALES`, so this replaces the existing semantic view and keeps its grants.

### Verify the numbers

Query the new metric through the semantic view:

```sql
SELECT * FROM SEMANTIC_VIEW(
    OSSIE_DEMO.PUBLIC.TPCH_SALES
    DIMENSIONS customer.c_mktsegment
    METRICS total_sales, sales_per_customer
) ORDER BY c_mktsegment;
```

Check it against plain SQL on the underlying views. The two results should match:

```sql
SELECT c.C_MKTSEGMENT,
       SUM(o.O_TOTALPRICE) AS total_sales,
       SUM(o.O_TOTALPRICE) / COUNT(DISTINCT o.O_CUSTKEY) AS sales_per_customer
FROM OSSIE_DEMO.PUBLIC.ORDERS o
JOIN OSSIE_DEMO.PUBLIC.CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
GROUP BY 1
ORDER BY 1;
```


<!-- ------------------------ -->
## Run the Loop Again

A round trip only proves something if the next cycle works too. Export from Snowflake again and convert to Power BI.

Run the export query from earlier and save the result as `~/ossie-demo/tpch_sales_export_2.yaml`. Then:

```bash
uv run python ~/ossie-demo/unwrap_snowflake_export.py \
    ~/ossie-demo/tpch_sales_export_2.yaml \
    ~/ossie-demo/tpch_sales_2.ossie.yaml

uv run ossie-microsoft export \
    -i ~/ossie-demo/tpch_sales_2.ossie.yaml \
    -o ~/ossie-demo/model_2.bim
```

Open `model_2.bim` and find `SALES_PER_CUSTOMER`. The measure that started in Power BI is back, rebuilt from the Snowflake SQL:

```
DIVIDE(SUM('ORDERS'[O_TOTALPRICE]), DISTINCTCOUNTNOBLANK('ORDERS'[O_CUSTKEY]))
```

The converter uses `DISTINCTCOUNTNOBLANK` to match SQL's `COUNT(DISTINCT ...)`, which ignores nulls. Every order has a customer, so the result is the same as the analyst's original `DISTINCTCOUNT`.


<!-- ------------------------ -->
## Taking This to Production

The loop in this guide treats Snowflake as the hub. That works when every measure is a simple aggregate the converter can rebuild. For real teams, store the Ossie model in git as the single source of truth instead:

- **Merge from both sides.** Changes from Snowflake merge in their SQL and keep the DAX already in git. Changes from Power BI merge in their DAX and keep the SQL and Snowflake-specific settings. `merge_from_powerbi.py` covers the Power BI side for metrics; the Snowflake side is the same idea in reverse.
- **Sync before you deploy.** `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML` replaces the whole semantic view, so pull any edits made directly in Snowflake into git first.
- **Review every formula change.** A changed SQL expression needs matching DAX, and changed DAX needs matching SQL. The merge script exits with an error when SQL is missing, so it can block a CI pipeline until someone adds it.
- **Detect conflicts.** If the same metric changes in both tools between syncs, compare each side against the last synced version in git history rather than overwriting.

### Known limits

These held true when this guide was written. Apache Ossie is incubating, so check the converter and Snowflake documentation for changes.

- Snowflake exports and accepts Ossie version `0.1.1`. The Power BI converter writes `0.2.0.dev0`, which is why the import can't be deployed directly.
- Measures with filters or other logic outside simple aggregates don't survive a second trip through Snowflake. Keep them in git with both expressions.
- Synonyms aren't restored when a semantic view is created from Ossie YAML.
- Column data types aren't included in the Snowflake export, so Power BI columns come through untyped.
- Snowflake's export adds a duplicate `SNOWFLAKE` custom extension to each field on every round trip. It's harmless, but the file grows.
- The Power BI model uses Direct Lake placeholders and isn't connected to data.


<!-- ------------------------ -->
## Conclusion and Resources

You moved a semantic model from Snowflake to Power BI with Apache Ossie, added a measure in Power BI, reviewed and deployed it in Snowflake, and ran the loop a second time without losing the measure. The merge step keeps each platform's details intact, and the review step makes sure a person approves every formula before it reaches the other platform.

### What You Learned
- creating a Snowflake Semantic View from YAML
- exporting a semantic view to Ossie with `SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW`
- converting Ossie to and from a Power BI `model.bim` with the `ossie-microsoft` converter
- merging a Power BI change back into the Ossie model and deploying it with `SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML`
- which kinds of changes survive a round trip, and which don't

### Resources
- [Apache Ossie (incubating)](https://ossie.apache.org/)
- [Apache Ossie Core Specification](https://github.com/apache/ossie/blob/main/core-spec/spec.md)
- [Apache Ossie Microsoft converter](https://github.com/apache/ossie/tree/main/converters/microsoft)
- [SYSTEM$READ_OSSIE_YAML_FROM_SEMANTIC_VIEW](https://docs.snowflake.com/en/sql-reference/functions/system_read_ossie_yaml_from_semantic_view)
- [SYSTEM$CREATE_SEMANTIC_VIEW_FROM_OSSIE_YAML](https://docs.snowflake.com/en/sql-reference/stored-procedures/system_create_semantic_view_from_ossie_yaml)
- [Snowflake Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)

If you have any questions, reach out to your Snowflake account team!
