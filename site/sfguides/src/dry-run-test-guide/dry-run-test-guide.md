author: Anna Filippova
id: dry-run-test-guide
language: en
summary: A minimal end-to-end walkthrough of the Snowpark Python API: create a session, build a DataFrame, aggregate it, and write the results back to Snowflake.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/transformation
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Dry Run Test Guide
<!-- ------------------------ -->
## Overview

The Snowpark Python API lets you query and transform data in Snowflake using
DataFrames instead of writing SQL strings. Operations are lazy: you build up a
DataFrame locally, and Snowpark pushes the whole thing down to Snowflake as a
single query when you ask for results. Nothing is copied out of Snowflake to run.

This guide walks through the smallest useful version of that loop. You will
connect from a local Python environment, create a table, read it into a
DataFrame, aggregate it, and persist the result back to Snowflake as a new table.
Every code block is runnable as written.

> Note: This guide exists to exercise the guide publishing pipeline end to end.
> The content is intentionally minimal.

### Prerequisites
- A Snowflake account (or [free trial](https://signup.snowflake.com/))
- Familiarity with SQL and basic Python

### What You'll Learn
- How to create a Snowpark session from a local Python environment
- How to read a Snowflake table into a Snowpark DataFrame
- How to filter and aggregate data with the DataFrame API instead of SQL
- How to write a DataFrame back to Snowflake as a table

### What You'll Need
- Python 3.9 or later
- A Snowflake role that can create a database, schema, and warehouse
- The `snowflake-snowpark-python` package

### What You'll Build
- A `SNOWPARK_DRY_RUN` database holding a source table of order rows
- A Python script that aggregates those orders into revenue per region
- A `REVENUE_BY_REGION` table written back to Snowflake by Snowpark

<!-- ------------------------ -->
## Setup

Install the Snowpark library into a fresh virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install snowflake-snowpark-python
```

Create the database, schema, and warehouse this guide uses, then load a small
source table. Run this in a Snowsight worksheet:

```sql
CREATE OR REPLACE DATABASE SNOWPARK_DRY_RUN;
CREATE OR REPLACE SCHEMA SNOWPARK_DRY_RUN.PUBLIC;

CREATE OR REPLACE WAREHOUSE SNOWPARK_DRY_RUN_WH
  WITH WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE OR REPLACE TABLE SNOWPARK_DRY_RUN.PUBLIC.ORDERS (
  ORDER_ID   NUMBER,
  REGION     VARCHAR,
  AMOUNT     NUMBER(10,2),
  ORDER_DATE DATE
);

INSERT INTO SNOWPARK_DRY_RUN.PUBLIC.ORDERS VALUES
  (1, 'WEST',  120.50, '2026-01-05'),
  (2, 'WEST',   89.00, '2026-01-11'),
  (3, 'EAST',  310.25, '2026-01-12'),
  (4, 'EAST',   45.75, '2026-02-02'),
  (5, 'NORTH', 500.00, '2026-02-14'),
  (6, 'NORTH',  15.00, '2026-02-20'),
  (7, 'WEST',  210.00, '2026-03-01');
```

<!-- ------------------------ -->
## Create A Session

A `Session` is the Snowpark equivalent of a connection. Build one from a
dictionary of connection parameters.

Create `dry_run.py`:

```python
import os
from snowflake.snowpark import Session

connection_parameters = {
    "account":   os.environ["SNOWFLAKE_ACCOUNT"],
    "user":      os.environ["SNOWFLAKE_USER"],
    "password":  os.environ["SNOWFLAKE_PASSWORD"],
    "role":      os.environ.get("SNOWFLAKE_ROLE", "SYSADMIN"),
    "warehouse": "SNOWPARK_DRY_RUN_WH",
    "database":  "SNOWPARK_DRY_RUN",
    "schema":    "PUBLIC",
}

session = Session.builder.configs(connection_parameters).create()
print(session.sql("SELECT CURRENT_VERSION()").collect())
```

Export your credentials and run it:

```bash
export SNOWFLAKE_ACCOUNT="your-account-identifier"
export SNOWFLAKE_USER="your-username"
export SNOWFLAKE_PASSWORD="your-password"
python dry_run.py
```

You should see a single row containing your Snowflake version.

> Note: Reading credentials from environment variables keeps them out of source
> control. Never hardcode a password into a script you plan to commit.

<!-- ------------------------ -->
## Build A DataFrame

`session.table()` returns a DataFrame that references a Snowflake table. No data
moves yet — the DataFrame is just a description of a query.

Add this to `dry_run.py`:

```python
orders = session.table("ORDERS")

print(orders.schema)
orders.show()
```

`show()` is an action, so this is the point where Snowpark compiles the DataFrame
to SQL and sends it to Snowflake.

<!-- ------------------------ -->
## Filter And Aggregate

Chain transformations to build up the query. Each call returns a new DataFrame
and still runs nothing.

```python
from snowflake.snowpark.functions import col, sum as sum_, count

revenue_by_region = (
    orders
    .filter(col("AMOUNT") > 50)
    .group_by(col("REGION"))
    .agg(
        sum_(col("AMOUNT")).alias("TOTAL_REVENUE"),
        count(col("ORDER_ID")).alias("ORDER_COUNT"),
    )
    .sort(col("TOTAL_REVENUE").desc())
)

revenue_by_region.show()
```

Import `sum` as `sum_` so it does not shadow Python's built-in `sum`.

To see the SQL Snowpark generated for you, inspect the query plan:

```python
print(revenue_by_region.queries["queries"][0])
```

This is the single pushed-down query — the filter, aggregation, and sort all
execute inside Snowflake.

<!-- ------------------------ -->
## Write Results Back

Persist the aggregated DataFrame as a new Snowflake table:

```python
revenue_by_region.write.mode("overwrite").save_as_table("REVENUE_BY_REGION")

print(session.table("REVENUE_BY_REGION").collect())
session.close()
```

`mode("overwrite")` replaces the table if it already exists, which makes the
script safe to re-run. Verify the result in Snowsight:

```sql
SELECT * FROM SNOWPARK_DRY_RUN.PUBLIC.REVENUE_BY_REGION
ORDER BY TOTAL_REVENUE DESC;
```

Expected output:

| REGION | TOTAL_REVENUE | ORDER_COUNT |
|--------|---------------|-------------|
| NORTH  | 500.00        | 1           |
| WEST   | 419.50        | 3           |
| EAST   | 310.25        | 1           |

Note that the `AMOUNT > 50` filter dropped order 6 from NORTH and order 4 from
EAST before the totals were computed.

The flow you just built:

![placeholder architecture diagram](assets/architecture-placeholder.png)

<!-- ------------------------ -->
## Clean Up

Drop everything this guide created so it does not accrue cost:

```sql
DROP DATABASE IF EXISTS SNOWPARK_DRY_RUN;
DROP WAREHOUSE IF EXISTS SNOWPARK_DRY_RUN_WH;
```

<!-- ------------------------ -->
## Conclusion And Resources

You built a complete Snowpark Python round trip: a session, a DataFrame over a
Snowflake table, a filtered aggregation expressed in Python, and a result table
written back to Snowflake. The transformation logic ran entirely inside
Snowflake — the only thing that crossed the network was the query and the final
result set.

From here, the same DataFrame patterns extend to user-defined functions, stored
procedures, and scheduled tasks, which is how Snowpark pipelines get built in
production.

### What You Learned
- How to create a Snowpark session from connection parameters
- That Snowpark DataFrames are lazy, and which calls are actions
- How to express filters and aggregations with the DataFrame API
- How to inspect the SQL Snowpark pushes down
- How to write a DataFrame back to Snowflake with `save_as_table`

### Resources
- [Snowpark Developer Guide for Python](https://docs.snowflake.com/en/developer-guide/snowpark/python)
- [Snowpark Library for Python API Reference](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/index)
- [Working with DataFrames in Snowpark Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/working-with-dataframes)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Snowflake Guides](https://www.snowflake.com/en/developers/guides/)
