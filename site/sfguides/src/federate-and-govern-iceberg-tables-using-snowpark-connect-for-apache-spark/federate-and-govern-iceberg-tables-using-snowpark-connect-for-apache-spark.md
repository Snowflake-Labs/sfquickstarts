author: Nagesh Cherukuri
id: federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/iceberg
language: en
summary: Use Snowpark Connect for Apache Spark to create, govern, and federate Iceberg tables — from Snowflake-managed storage to AI enrichment pipelines and cross-platform open lakehouse access with Horizon governance enforced at every layer.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts
open in snowflake: https://app.snowflake.com/developer-guides/snowpark-connect

# Federate and Govern Iceberg Tables Using Snowpark Connect for Apache Spark
<!-- ------------------------ -->

## Overview

**By the end of this quickstart, a business user opens Snowsight → Cortex Analyst, types _"Which orders are HIGH risk and need immediate attention?"_, and gets a governed, AI-enriched answer — drawn in real time from Iceberg tables that live across two completely separate catalogs.**

Behind that single query:
- Order data originates in **Databricks Unity Catalog** (Delta + Iceberg UniForm tables on Databricks-managed S3)
- Snowflake federates those tables into a **Catalog-Linked Database** — no data movement, no copy jobs
- **Snowpark Connect** reads the federated tables and calls **Snowflake Cortex** to classify risk and generate operational notes inline in SQL
- Results are written to a new **Snowflake-managed Iceberg table** on Snowflake's own storage
- **Horizon governance** — column masking and row access policies — applies to every table, including the AI-generated `risk_level` column
- When a non-admin user asks the same question, Cortex Analyst returns `*** RESTRICTED ***` for HIGH risk orders — governance fires through conversational AI just as it does through SQL

This is federated Iceberg analytics with AI enrichment and end-to-end governance, all without rewriting pipelines or duplicating data.

---

### The Problem

Data teams increasingly run Iceberg tables in multiple catalogs — Snowflake, Databricks, AWS Glue. Getting a unified, governed, AI-powered analytics layer across all of them requires stitching together bespoke ETL, cross-catalog security policies, and custom ML pipelines.

This quickstart shows how to replace that with a single, open-standards approach:

> **Iceberg everywhere + Snowpark Connect as the unified compute layer + Horizon for governance + Cortex for AI**

---

### What You Build

**Step 1 — Snowflake-managed Iceberg + Horizon governance** (`01`, `02`)
Create two Snowflake-managed Iceberg tables. Apply column masking (hide `sensitive_data` from non-admin roles) and a row access policy (filter historical rows). Use Snowpark Connect to run PySpark DataFrames against them — governance fires on every query because Snowpark Connect routes through Snowflake's SQL engine.

**Step 2 — Federate external Iceberg tables + Snowpark Connect governance** (`04`, `05`)
Create Iceberg tables in Databricks Unity Catalog (Delta + UniForm). Federate them into Snowflake as a Catalog-Linked Database. Apply Snowflake's own Horizon masking policy to `credit_card` — independent of any Databricks policies. Snowpark Connect queries the federated tables with live role-based masking.

**Step 3 — Cortex AI enrichment pipeline → Cortex Analyst** (`07`, `08`)
Snowpark Connect reads from both catalogs. Cortex classifies each order as HIGH / MEDIUM / LOW risk and generates a one-sentence operational note. Results are written to a new Snowflake-managed Iceberg table. Horizon masking applies to `risk_level` exactly as it does to raw columns. A Cortex Analyst semantic view spans all three Iceberg tables — ask questions in natural language from Snowsight, with governance enforced per active role.

> **Download the code:**
> [Download all files (ZIP)](https://download-directory.github.io/?url=https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets)
>
> Or download individual files:
> - [01_sf_iceberg_catalog_setup.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/01_sf_iceberg_catalog_setup.sql)
> - [02_sf_iceberg_demo.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/02_sf_iceberg_demo.ipynb)
> - [03_databricks_rw_sf_iceberg.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/03_databricks_rw_sf_iceberg.py)
> - [04_databricks_create_uc_tables.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/04_databricks_create_uc_tables.py)
> - [05_databricks_federation_demo.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/05_databricks_federation_demo.ipynb)
> - [06_cortex_ai_pipeline.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/06_cortex_ai_pipeline.ipynb)
> - [07_ai_pipeline.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/07_ai_pipeline.ipynb)

### What You'll Learn

- How **Snowpark Connect** runs PySpark DataFrames through Snowflake's SQL engine — enforcing Horizon governance on every query regardless of the caller
- How **Catalog-Linked Databases** federate externally-managed Iceberg tables into Snowflake with independent Horizon governance applied at query time
- How **Cortex LLM functions** enrich federated Iceberg data inline in SQL, writing AI results to Snowflake-managed Iceberg
- Why **Horizon masking applies to AI-generated columns** exactly as it does to raw data — no extra configuration
- How **Cortex Analyst** queries a semantic view spanning multiple Iceberg catalogs with governance enforced per role

### Key Capabilities

- **Federated Iceberg**: Query Iceberg tables across Snowflake and external catalogs from a single Snowflake Workspace notebook
- **Governance at the SQL layer**: Snowpark Connect routes every query through Snowflake's SQL engine — Horizon policies apply regardless of the caller's role
- **Independent governance on federated tables**: Snowflake applies its own masking policies on top of externally-managed tables, independently of the source catalog's policies
- **AI enrichment on Iceberg**: Cortex LLM functions run inline in SQL on federated data, writing results to Snowflake-managed Iceberg
- **Governed AI output**: Horizon masking applies to Cortex-generated columns exactly as it does to raw data
- **Conversational analytics**: Cortex Analyst semantic view spans SF-managed and federated Iceberg tables — natural language queries with governance enforced per active role

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/) with `ACCOUNTADMIN` access and Cortex LLM functions enabled (us-east-1 or us-west-2)
- A Databricks workspace with Unity Catalog enabled (for Step 2)
- An S3 bucket accessible from Snowflake via an external volume (`CREATE EXTERNAL VOLUME`)

### Prerequisites

- Familiarity with Snowflake SQL and the Snowsight UI
- Basic familiarity with PySpark DataFrames
- An external volume already configured in Snowflake (`CREATE EXTERNAL VOLUME`)

<!-- ------------------------ -->

## Architecture

### Scenario 1 — Snowflake-Managed Iceberg + Snowpark Connect

```
Snowflake Account
  │  CREATE ICEBERG TABLE ... CATALOG = 'SNOWFLAKE'
  │  Horizon governance: column masking, row access policy
  │
  └─ Snowpark Connect
       spark.table("DEMO_SCHEMA.OPEN_TABLE")
       spark.table("DEMO_SCHEMA.PROTECTED_TABLE")
       → queries route through Snowflake SQL engine
       → Horizon policies ARE enforced
```

### Scenario 2 — Federate External Iceberg + Cortex AI Enrichment

```
External Catalog (Unity Catalog)
  │  Delta + Iceberg UniForm tables
  │  Iceberg REST endpoint → Snowflake Catalog Integration
  │
Snowflake Catalog-Linked Database (DATABRICKS_DEMO_DB)
  │  Auto-discovers schemas + tables every 30 s
  │  Applies independent Horizon masking policies
  │
  └─ Snowpark Connect
       spark.sql("SELECT * FROM DATABRICKS_DEMO_DB.horizon_demo.customer_orders")
       sf_session.sql(CTAS + CORTEX.COMPLETE → AI_ORDER_INSIGHTS)
       → Snowflake SQL engine enforces masking on both raw and AI columns
       → Cortex Analyst: natural language queries on AI-enriched Iceberg table
```

> **Governance contrast (external engine vs Snowpark Connect):** An external Spark engine reading via Horizon IRC receives raw Parquet via vended S3 credentials — Snowflake SQL-layer policies do not apply to that path. Snowpark Connect routes through the Snowflake SQL engine, so Horizon masking and row access policies are always enforced. See `03_databricks_rw_sf_iceberg.py` for the full Databricks IRC demo.

<!-- ------------------------ -->

## Databricks Cluster Setup (Scenario 2 prerequisites)

Scenarios 1 and 2 Snowflake notebooks run entirely within Snowflake — no external cluster needed.

Scenario 2 requires two Databricks notebooks run once as setup:

| Notebook | Cluster needed |
|----------|---------------|
| `04_databricks_create_uc_tables.py` | Single User + Unity Catalog, DBR 13.3 LTS+ |
| `03_databricks_rw_sf_iceberg.py` *(optional governance contrast)* | Single User, no UC, DBR 14.3 LTS+, Maven: `org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1` |

<!-- ------------------------ -->

## Scenario 1 — Snowflake Setup

Run `01_sf_iceberg_catalog_setup.sql` in a Snowflake worksheet as `ACCOUNTADMIN`.

This creates two Snowflake-managed Iceberg tables and applies Horizon governance policies.

### Create Database and Tables

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE LOAD_WH;

CREATE DATABASE IF NOT EXISTS HORIZON_DEMO_SFDB
    EXTERNAL_VOLUME = 'SNOWFLAKE_MANAGED'
    COMMENT = 'Snowflake-managed Iceberg catalog (Horizon IRC)';

CREATE SCHEMA IF NOT EXISTS HORIZON_DEMO_SFDB.DEMO_SCHEMA;

-- OPEN_TABLE: no governance restrictions
CREATE OR REPLACE ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.OPEN_TABLE (
    id          INT,
    product     STRING,
    quantity    INT,
    price       DECIMAL(10, 2),
    created_at  TIMESTAMP
)
CATALOG = 'SNOWFLAKE';

-- PROTECTED_TABLE: column masking + row access policy applied below
CREATE OR REPLACE ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.PROTECTED_TABLE (
    id              INT,
    customer_name   STRING,
    sensitive_data  STRING,
    amount          DECIMAL(10, 2),
    created_at      TIMESTAMP
)
CATALOG = 'SNOWFLAKE';
```

### Apply Horizon Governance Policies

```sql
-- Column masking: hide sensitive_data from non-admin roles
CREATE OR REPLACE MASKING POLICY HORIZON_DEMO_SFDB.DEMO_SCHEMA.MASK_SENSITIVE
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
        ELSE '*** MASKED ***'
    END;

ALTER ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.PROTECTED_TABLE
    MODIFY COLUMN sensitive_data
    SET MASKING POLICY HORIZON_DEMO_SFDB.DEMO_SCHEMA.MASK_SENSITIVE;

-- Row access policy: non-admin roles see current-year rows only
CREATE OR REPLACE ROW ACCESS POLICY HORIZON_DEMO_SFDB.DEMO_SCHEMA.CURRENT_YEAR_ONLY
    AS (created_at TIMESTAMP) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN')
        OR YEAR(created_at) = YEAR(CURRENT_DATE());

ALTER ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.PROTECTED_TABLE
    ADD ROW ACCESS POLICY HORIZON_DEMO_SFDB.DEMO_SCHEMA.CURRENT_YEAR_ONLY
    ON (created_at);
```

### Configure Credential Vending (for Scenario 2)

```sql
-- OPEN_TABLE_RW: SELECT + writes → Snowflake vends write-capable S3 credentials
CREATE DATABASE ROLE IF NOT EXISTS HORIZON_DEMO_SFDB.OPEN_TABLE_RW;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    HORIZON_DEMO_SFDB.DEMO_SCHEMA.OPEN_TABLE
    TO DATABASE ROLE HORIZON_DEMO_SFDB.OPEN_TABLE_RW;

-- PROTECTED_TABLE_RO: SELECT only → Snowflake vends read-only S3 credentials
CREATE DATABASE ROLE IF NOT EXISTS HORIZON_DEMO_SFDB.PROTECTED_TABLE_RO;
GRANT SELECT ON TABLE
    HORIZON_DEMO_SFDB.DEMO_SCHEMA.PROTECTED_TABLE
    TO DATABASE ROLE HORIZON_DEMO_SFDB.PROTECTED_TABLE_RO;

GRANT DATABASE ROLE HORIZON_DEMO_SFDB.OPEN_TABLE_RW      TO ROLE $SF_EXT_COMPUTE_ROLE;
GRANT DATABASE ROLE HORIZON_DEMO_SFDB.PROTECTED_TABLE_RO TO ROLE $SF_EXT_COMPUTE_ROLE;
```

### Generate PAT (for Scenario 2)

```sql
-- ⚠ Copy the token immediately — shown only once
ALTER USER <YOUR_USERNAME>
    ADD PROGRAMMATIC ACCESS TOKEN MY_DEMO_PAT
    COMMENT = 'Iceberg Federation Demo — Horizon IRC integration';
```

<!-- ------------------------ -->

## Scenario 1 — Snowpark Connect Governance Demo

Upload `02_sf_iceberg_demo.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `02_sf_iceberg_demo.ipynb` into the file tree**

> `snowpark-connect` is pre-installed in Snowflake Workspaces — no package picker step needed.

### Initialize Session

```python
from snowflake.snowpark.context import get_active_session
from snowflake import snowpark_connect
from pyspark.sql.functions import col
import pandas as pd

sf_session = get_active_session()
sf_session.sql(f"USE DATABASE {SF_MANAGED_ICEBERG_DB}").collect()

spark = snowpark_connect.init_spark_session()

def switch_role(role):
    sf_session.sql(f"USE ROLE {role}").collect()
    print(f"Active role → {role}")

switch_role("ACCOUNTADMIN")
```

### Demo 1 — Read OPEN_TABLE

```python
spark.table(TBL_OPEN).orderBy("id").show(truncate=False)
```

**Expected:** 3 rows (Laptop, Mouse, Keyboard). All columns visible. No policies applied.

### Demo 2 — ACCOUNTADMIN Reads PROTECTED_TABLE

```python
switch_role("ACCOUNTADMIN")
spark.table(TBL_PROTECTED).orderBy("id").show(truncate=False)
```

**Expected:** 3 rows including the 2023 row. `sensitive_data` shows raw values (e.g. `SSN-123-45-6789`).

### Demo 3 — Reader Role Reads PROTECTED_TABLE

```python
switch_role(SF_READER_ROLE)
spark.table(TBL_PROTECTED).orderBy("id").show(truncate=False)
```

**Expected:** 2 rows (2023 row filtered by row access policy). `sensitive_data` shows `*** MASKED ***`.

### Demo 4 — Side-by-Side Comparison

```python
COLS = ["id", "customer_name", "sensitive_data", "amount"]

switch_role("ACCOUNTADMIN")
admin_rows = spark.table(TBL_PROTECTED).select(*COLS).collect()

switch_role(SF_READER_ROLE)
reader_rows = spark.table(TBL_PROTECTED).select(*COLS).collect()

admin_pd  = pd.DataFrame([r.asDict() for r in admin_rows])
admin_pd.insert(0, "role", "ACCOUNTADMIN")

reader_pd = pd.DataFrame([r.asDict() for r in reader_rows])
reader_pd.insert(0, "role", SF_READER_ROLE)

combined = pd.concat([admin_pd, reader_pd]).sort_values(["id", "role"]).reset_index(drop=True)
print(combined.to_string(index=False))
```

**Expected:** Same Iceberg table, same Parquet files — ACCOUNTADMIN sees 3 unmasked rows, reader role sees 2 masked rows. This is Snowflake Horizon governance enforced through Snowpark Connect.

> **Key insight:** Snowpark Connect routes queries through the Snowflake SQL engine. Horizon policies apply to every query regardless of the PySpark API used. Scenario 2 demonstrates the contrast — an external engine reading the same table bypasses these policies.

<!-- ------------------------ -->

## Governance Contrast — Snowpark Connect vs External Engine

The same Snowflake-managed Iceberg table returns different results depending on the read path.

| Access path | Engine | Route | Horizon policies |
|-------------|--------|-------|-----------------|
| Snowpark Connect (Scenarios 1 & 2) | Snowflake SQL engine | Logical query plan | ✅ Enforced |
| Horizon IRC (external Spark) | Databricks / any Spark | Raw Parquet via vended S3 creds | ❌ Bypassed |

**Snowpark Connect — PROTECTED_TABLE (masking + row filter enforced):**

```python
switch_role("EXT_COMPUTE_ENG_DEMO_ROLE")
spark.table("HORIZON_DEMO_SFDB.DEMO_SCHEMA.PROTECTED_TABLE").show()
# 2 rows (2023 row filtered) │ sensitive_data: *** MASKED ***
```

**External Spark via Horizon IRC — same table (raw Parquet):**

```python
# Databricks reads via vended S3 credentials
spark.table("sf_horizon.DEMO_SCHEMA.PROTECTED_TABLE").show()
# 3 rows (all rows) │ sensitive_data: raw value visible
```

Snowflake's masking and row access policies execute inside the SQL engine. An engine that bypasses the SQL engine and reads Parquet files directly will never see those policies fire.

> **Credential vending also enforces write access:** `PROTECTED_TABLE_RO` (SELECT only) → Snowflake vends read-only S3 credentials → any `s3:PutObject` attempt returns 403. `OPEN_TABLE_RW` (INSERT/UPDATE/DELETE) → write-capable credentials vended. No application code required — the catalog decides.

**Full Databricks IRC notebook:** `03_databricks_rw_sf_iceberg.py` (reads, writes, credential vending demo).

<!-- ------------------------ -->

## Scenario 2 — External Catalog Setup

Attach `04_databricks_create_uc_tables.py` to **Cluster B** (Unity Catalog enabled).

### Create Catalog, Schema, and Tables

```python
CATALOG_NAME = "<DBX_UC_CATALOG>"    # e.g. my_demo
SCHEMA_NAME  = "horizon_demo"         # pre-set

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}")
spark.sql(f"CREATE SCHEMA  IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}")
```

```python
spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders (
    order_id BIGINT, customer_id BIGINT, product STRING,
    amount DECIMAL(10,2), order_date DATE, status STRING
)
USING DELTA
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableIcebergCompatV2'          = 'true',
    'delta.columnMapping.mode'             = 'name'
)
""")
```

Delta UniForm writes standard Delta files **and** Iceberg metadata in parallel — no data duplication, no ETL.

### Apply External Catalog Governance

```python
# Column mask on credit_card (applies within the external catalog only)
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card(cc STRING)
RETURN CASE WHEN is_account_group_member('account_unity_admin') THEN cc
            ELSE CONCAT('****-****-****-', RIGHT(cc, 4)) END
""")
spark.sql(f"""ALTER TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders
ALTER COLUMN credit_card SET MASK {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card""")
```

> These external catalog policies apply within that catalog only. Snowflake applies its own independent governance policies in the next step.

### Get the Iceberg REST Endpoint

```python
WORKSPACE_HOST = "<DBX_WORKSPACE_HOST>"
print(f"CATALOG_URI  : https://{WORKSPACE_HOST}/api/2.1/unity-catalog/iceberg-rest")
print(f"CATALOG_NAME : {CATALOG_NAME}")
```

Copy these values into `05_databricks_federation_demo.ipynb`.

<!-- ------------------------ -->

## Scenario 2 — Snowflake Setup

Open `05_databricks_federation_demo.ipynb` in a Snowflake Workspace notebook (drag and drop into the file tree).

### Create Catalog Integration

```sql
CREATE OR REPLACE CATALOG INTEGRATION MY_DATABRICKS_UC_CI
    CATALOG_SOURCE = ICEBERG_REST
    TABLE_FORMAT   = ICEBERG
    REST_CONFIG = (
        CATALOG_URI  = 'https://<DBX_WORKSPACE_HOST>/api/2.1/unity-catalog/iceberg-rest'
        CATALOG_NAME = '<DBX_UC_CATALOG>'
        ACCESS_DELEGATION_MODE = EXTERNAL_VOLUME_CREDENTIALS
    )
    REST_AUTHENTICATION = (
        TYPE         = BEARER
        BEARER_TOKEN = '<DBX_PAT_TOKEN>'
    )
    ENABLED = TRUE;

-- Verify connectivity — must return {"success": true}
SELECT SYSTEM$VERIFY_CATALOG_INTEGRATION('MY_DATABRICKS_UC_CI');
```

### Create Catalog-Linked Database

```sql
CREATE DATABASE IF NOT EXISTS DATABRICKS_DEMO_DB
    EXTERNAL_VOLUME = 'ICEBERG_EXTERNAL_S3_VOLUME'
    LINKED_CATALOG = ( CATALOG = 'MY_DATABRICKS_UC_CI' )
    COMMENT = 'Iceberg Federation Demo — Federated from external Iceberg catalog';

-- Wait ~30 s for auto-discovery, then verify
SHOW ICEBERG TABLES IN DATABASE DATABRICKS_DEMO_DB;
SELECT * FROM DATABRICKS_DEMO_DB.horizon_demo.customer_orders LIMIT 5;
```

### Apply Snowflake Horizon Governance

```sql
CREATE OR REPLACE MASKING POLICY HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES.MASK_CREDIT_CARD
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        ELSE CONCAT('****-****-****-', RIGHT(val, 4))
    END;

ALTER ICEBERG TABLE DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders
    MODIFY COLUMN "credit_card"
    SET MASKING POLICY HORIZON_DEMO_SFDB.GOVERNANCE_POLICIES.MASK_CREDIT_CARD;
```

Snowflake defines and enforces this policy independently — it applies whether the data was written by Snowflake, the external catalog, or any other engine.

<!-- ------------------------ -->

## Scenario 2 — Snowpark Connect Governance Demo

Upload `05_databricks_federation_demo.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `05_databricks_federation_demo.ipynb` into the file tree**

> `snowpark-connect` is pre-installed in Snowflake Workspaces — no package picker step needed.

### Session Setup for Catalog-Linked Databases

Three setup rules are required when using Snowpark Connect with a catalog-linked database:

1. **Initialize Snowpark Connect on a regular Snowflake database** — set the session context before calling `init_spark_session`.
2. **Enable `caseSensitive` mode** — external Iceberg catalogs use lowercase schema and table names; this ensures Snowpark Connect resolves them correctly.
3. **Use fully-qualified lowercase names** in `spark.sql()` for catalog-linked tables.

```python
# Rule 1: session context must be a regular (non-catalog-linked) database
sf_session.sql(f"USE DATABASE {SF_INIT_DB}").collect()

# Rule 2: preserve lowercase identifiers used by the external catalog
conf = SparkConf().set("spark.sql.caseSensitive", "true")
spark = snowpark_connect.init_spark_session(conf=conf)

# Rule 3: fully-qualified reference with lowercase schema and table names
df = spark.sql(f"SELECT * FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.customer_orders")
```

### Initialize Sessions

```python
from snowflake.snowpark.context import get_active_session
from snowflake import snowpark_connect
from pyspark import SparkConf
from pyspark.sql.functions import col, count, sum as spark_sum

sf_session = get_active_session()
sf_session.sql(f"USE DATABASE {SF_INIT_DB}").collect()

conf = SparkConf().set("spark.sql.caseSensitive", "true")
spark = snowpark_connect.init_spark_session(conf=conf)

def switch_role(role):
    sf_session.sql(f"USE ROLE {role}").collect()
    print(f"Active role → {role}")

switch_role("ACCOUNTADMIN")
```

### Demo 1 — Read customer_orders

```python
df_orders = spark.sql(f"SELECT * FROM {TBL_ORDERS}")
df_orders.orderBy("order_id").show(truncate=False)
```

### Demo 2–3 — Filter and Aggregate

```python
df_orders.filter(col("status").isin("SHIPPED", "DELIVERED")) \
    .select("order_id", "product", "amount", "status") \
    .orderBy("amount", ascending=False).show(truncate=False)

df_orders.groupBy("status") \
    .agg(count("*").alias("order_count"), spark_sum("amount").alias("total_revenue")) \
    .orderBy("total_revenue", ascending=False).show(truncate=False)
```

### Demo 4–5 — Role-Based Masking on Federated Tables

```python
# ACCOUNTADMIN: credit_card unmasked
switch_role("ACCOUNTADMIN")
spark.sql(f"SELECT * FROM {TBL_SENSITIVE}") \
    .select("order_id", "customer_name", "credit_card").show(truncate=False)

# Reader role: credit_card masked by Snowflake Horizon policy
switch_role(SF_READER_ROLE)
spark.sql(f"SELECT * FROM {TBL_SENSITIVE}") \
    .select("order_id", "customer_name", "credit_card").show(truncate=False)
```

### Demo 6 — Side-by-Side Governance

```python
import pandas as pd
COLS = ["order_id", "customer_name", "credit_card"]

switch_role("ACCOUNTADMIN")
admin_rows  = spark.sql(f"SELECT * FROM {TBL_SENSITIVE}").select(*COLS).collect()

switch_role(SF_READER_ROLE)
reader_rows = spark.sql(f"SELECT * FROM {TBL_SENSITIVE}").select(*COLS).collect()

admin_pd  = pd.DataFrame([r.asDict() for r in admin_rows])
admin_pd.insert(0, "role", "ACCOUNTADMIN")
reader_pd = pd.DataFrame([r.asDict() for r in reader_rows])
reader_pd.insert(0, "role", SF_READER_ROLE)

combined = pd.concat([admin_pd, reader_pd]).sort_values(["order_id","role"]).reset_index(drop=True)
print(combined.to_string(index=False))
```

**Expected:** Same federated Parquet files — ACCOUNTADMIN sees `4111-1111-1111-1111`, reader role sees `****-****-****-1111`. Snowflake Horizon governance applied independently of the source catalog's policies.

<!-- ------------------------ -->

## Scenario 2 — AI Enrichment Pipeline Setup

Open `06_cortex_ai_pipeline.ipynb` in a Snowflake Workspace notebook as `ACCOUNTADMIN`.

This creates an AI-enriched Iceberg table from the Scenario 2 federated data, applies Horizon governance to the AI-generated column, and creates a Cortex Analyst semantic view.

### Step 1 — Verify Cortex Is Available

```sql
SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', 'Reply with exactly one word: ready') AS cortex_status;
```

**Expected:** `Ready`. If this errors, your trial region does not support Cortex LLM functions — switch to `us-east-1` or `us-west-2`.

> **Trial availability:** `SNOWFLAKE.CORTEX.COMPLETE` and `SNOWFLAKE.CORTEX.CLASSIFY_TEXT` are available in standard 30-day trial accounts on AWS us-east-1, us-west-2, and Azure eastus2. Cortex Analyst semantic views are available on the same regions.

### Step 2 — Create AI_ORDER_INSIGHTS Iceberg Table

```sql
CREATE OR REPLACE ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS
    CATALOG = 'SNOWFLAKE'
    AS
WITH deduped_orders AS (
    SELECT order_id, customer_id, product, amount, order_date, status
    FROM DATABRICKS_DEMO_DB.horizon_demo.customer_orders
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
),
deduped_sensitive AS (
    SELECT order_id, region
    FROM DATABRICKS_DEMO_DB.horizon_demo.sensitive_orders
    QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
)
SELECT
    co.order_id, co.customer_id, co.product, co.amount, co.order_date, co.status,
    COALESCE(so.region, 'UNKNOWN') AS region,
    -- Deterministic risk tier (reliable for governance demo)
    CASE
        WHEN co.status = 'CANCELLED' THEN 'HIGH'
        WHEN co.amount >= 500        THEN 'HIGH'
        WHEN co.amount >= 100        THEN 'MEDIUM'
        ELSE 'LOW'
    END AS risk_level,
    -- Cortex-generated operational note
    SNOWFLAKE.CORTEX.COMPLETE(
        'llama3.1-8b',
        'Write one operational sentence (max 15 words) for logistics. Product: ' || co.product ||
        ', Amount: $' || co.amount::STRING || ', Status: ' || co.status || '.'
    )::VARCHAR AS ops_note,
    CURRENT_TIMESTAMP()::TIMESTAMP_LTZ(6) AS enriched_at
FROM deduped_orders co
LEFT JOIN deduped_sensitive so ON co.order_id = so.order_id;
```

> **Why `QUALIFY ROW_NUMBER()`:** The source federated tables may contain duplicate rows from multiple Databricks INSERT runs. `QUALIFY` deduplicates per `order_id` before enrichment.

> **Why deterministic `CASE WHEN` for `risk_level`:** LLMs produce inconsistent results for strict classification rules. Using `CASE WHEN` ensures reliable HIGH/MEDIUM/LOW splits for the governance demo. `CORTEX.COMPLETE` is used for `ops_note` where natural language generation excels.

### Step 3 — Re-Apply Masking Policy

```sql
-- CREATE OR REPLACE drops all column policies — must re-apply every time
ALTER ICEBERG TABLE HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS
    MODIFY COLUMN risk_level
    SET MASKING POLICY HORIZON_DEMO_SFDB.DEMO_SCHEMA.MASK_RISK_LEVEL;
```

> **Important:** `CREATE OR REPLACE ICEBERG TABLE` drops all column policies on the table. Always run this `ALTER ICEBERG TABLE` immediately after the CTAS. The `06_cortex_ai_pipeline.ipynb` script does this automatically.

### Step 4 — Governance Comparison on AI Output

```sql
-- ACCOUNTADMIN: sees actual risk level including HIGH
USE ROLE ACCOUNTADMIN;
SELECT 'ACCOUNTADMIN' AS role_context, order_id, product, amount, region, risk_level
FROM HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS ORDER BY order_id;

-- Reader role: HIGH masked to *** RESTRICTED ***
USE ROLE EXT_COMPUTE_ENG_DEMO_ROLE;
SELECT 'EXT_COMPUTE_ENG_DEMO_ROLE' AS role_context, order_id, product, amount, region, risk_level
FROM HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS ORDER BY order_id;
```

**Expected:**

| role | order_id | product | risk_level |
|------|----------|---------|------------|
| ACCOUNTADMIN | 1 | Laptop | HIGH |
| ACCOUNTADMIN | 4 | Monitor | MEDIUM |
| reader role | 1 | Laptop | *** RESTRICTED *** |
| reader role | 4 | Monitor | MEDIUM |

### Step 5 — Create Cortex Analyst Semantic View

```sql
CREATE OR REPLACE SEMANTIC VIEW HORIZON_DEMO_SFDB.DEMO_SCHEMA.ICEBERG_AI_SEMANTIC_VIEW
TABLES (
  orders     AS HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS
               PRIMARY KEY (order_id)
               WITH SYNONYMS = ('ai orders', 'enriched orders', 'risk orders'),
  fed_orders AS DATABRICKS_DEMO_DB.horizon_demo.customer_orders
               PRIMARY KEY (order_id)
               WITH SYNONYMS = ('federated orders', 'source orders')
)
RELATIONSHIPS (
  orders(order_id) REFERENCES fed_orders
)
FACTS (
  orders.amount AS amount WITH SYNONYMS = ('order value', 'revenue')
)
DIMENSIONS (
  orders.product    AS product,
  orders.status     AS status     WITH SYNONYMS = ('fulfillment status'),
  orders.region     AS region,
  orders.risk_level AS risk_level WITH SYNONYMS = ('risk', 'risk tier'),
  orders.order_date AS order_date,
  orders.ops_note   AS ops_note   WITH SYNONYMS = ('operational note', 'ai note')
)
METRICS (
  orders.total_revenue   AS SUM(orders.amount)     WITH SYNONYMS = ('revenue', 'total sales'),
  orders.order_count     AS COUNT(orders.order_id) WITH SYNONYMS = ('number of orders'),
  orders.avg_order_value AS AVG(orders.amount)      WITH SYNONYMS = ('average order', 'AOV')
);

GRANT SELECT ON SEMANTIC VIEW HORIZON_DEMO_SFDB.DEMO_SCHEMA.ICEBERG_AI_SEMANTIC_VIEW
    TO ROLE EXT_COMPUTE_ENG_DEMO_ROLE;
```

> **Semantic views** are the recommended path for Cortex Analyst — they replace legacy YAML files and appear automatically in Snowsight → AI & ML → Cortex Analyst. Note: the alias direction in TABLES is `alias AS db.schema.table` (not `table AS alias`).

<!-- ------------------------ -->

## Scenario 2 — Snowpark Connect AI Pipeline Notebook

Upload `07_ai_pipeline.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `07_ai_pipeline.ipynb` into the file tree**

> `snowpark-connect` is pre-installed in Snowflake Workspaces — no package picker step needed.

### Initialize Session

```python
sf_session = get_active_session()
sf_session.sql(f"USE DATABASE {SF_INIT_DB}").collect()

conf = SparkConf().set("spark.sql.caseSensitive", "true")
spark = snowpark_connect.init_spark_session(conf=conf)
```

> `caseSensitive=true` is required when reading catalog-linked (FDN) tables, which use lowercase identifiers. It is harmless when reading SF-managed tables.

### Step 2 — Snowpark Connect Reads Federated Source Tables

```python
# Read from CLD — federated Databricks Iceberg (read only)
df_orders = spark.sql(f"SELECT * FROM {TBL_ORDERS}")
df_orders.select("order_id", "product", "amount", "status").orderBy("order_id").show()
```

### Step 4 — Cortex Enrichment + Write via sf_session

```python
sf_session.sql(f"""
    CREATE OR REPLACE ICEBERG TABLE {TBL_INSIGHTS} CATALOG = 'SNOWFLAKE' AS
    WITH deduped_orders AS ( ... ),
         deduped_sensitive AS ( ... )
    SELECT ..., SNOWFLAKE.CORTEX.COMPLETE('llama3.1-8b', ...) AS ops_note ...
    FROM deduped_orders co LEFT JOIN deduped_sensitive so ON co.order_id = so.order_id
""").collect()

# Re-apply masking — CREATE OR REPLACE drops column policies
sf_session.sql(f"""
    ALTER ICEBERG TABLE {TBL_INSIGHTS}
    MODIFY COLUMN risk_level
    SET MASKING POLICY {SF_MANAGED_ICEBERG_DB}.{SF_DEMO_SCHEMA}.MASK_RISK_LEVEL
""").collect()
```

### Step 5 — Governance Comparison via Snowpark Connect

```python
COLS = ["order_id", "product", "amount", "region", "risk_level"]

switch_role("ACCOUNTADMIN")
admin_df = sf_session.sql(f"SELECT {','.join(COLS)} FROM {TBL_INSIGHTS}").to_pandas()
admin_df.columns = [c.lower() for c in admin_df.columns]

switch_role(SF_READER_ROLE)
reader_df = sf_session.sql(f"SELECT {','.join(COLS)} FROM {TBL_INSIGHTS}").to_pandas()
reader_df.columns = [c.lower() for c in reader_df.columns]
```

> `sf_session.sql().to_pandas()` returns **uppercase** column names. Call `.columns = [c.lower() for c in df.columns]` immediately after `to_pandas()`.

<!-- ------------------------ -->

## Scenario 2 — Cortex Analyst Demo

**Open:** Snowsight → **AI & ML** → **Cortex Analyst**

**Select the semantic view:**
1. In the Cortex Analyst list, click `ICEBERG_AI_SEMANTIC_VIEW` under `HORIZON_DEMO_SFDB.DEMO_SCHEMA`
2. Click the **Playground** tab at the top of the screen
3. Type prompts in the **chat box at the bottom** of the Playground and press Enter

### Demo Prompt Sequence

**Prompt 1 — Revenue overview**
> *"What is the total revenue by risk level?"*

Expected: HIGH = highest amount (Laptop $999.99), MEDIUM, LOW.

**Prompt 2 — Governance live demo (key moment)**
> *"Which orders are classified as HIGH risk and what are their operational notes?"*

As ACCOUNTADMIN: Laptop, $999.99, `risk_level = HIGH` with Cortex ops note.
Switch role to `EXT_COMPUTE_ENG_DEMO_ROLE` and ask again → `risk_level = *** RESTRICTED ***`.

**Prompt 3 — Business intelligence**
> *"Show me all SHIPPED orders in the US-WEST region"*

**Prompt 4 — Cross-table (uses the RELATIONSHIP)**
> *"Compare total revenue from enriched orders versus source federated orders"*

The semantic view joins `AI_ORDER_INSIGHTS` (SF-managed) and `customer_orders` (Databricks-federated CLD) in a single query — Horizon masking applies throughout.

**Prompt 5 — Analytics**
> *"What is the average order value by fulfillment status?"*

<!-- ------------------------ -->

## Conclusion And Resources

Congratulations — you have completed all three scenarios!

### What You Built

- ✅ **Snowflake-managed Iceberg tables** with Horizon column masking and row access policies
- ✅ **Snowpark Connect governance demo** showing Horizon policies enforced through PySpark on Snowflake's engine
- ✅ **External engine read/write demo** via Horizon IRC with credential-vending write control
- ✅ **Catalog-linked database** auto-federating externally-managed Iceberg tables
- ✅ **Snowpark Connect notebook** with live role-based masking on federated tables
- ✅ **Cortex Analyst semantic view** spanning SF-managed and federated Iceberg tables with Horizon masking enforced

### What You Learned

- How Snowflake manages Iceberg natively with Horizon governance enforced through Snowpark Connect at every query
- How Horizon IRC exposes Snowflake-managed tables to any Iceberg-compatible engine, and how credential vending enforces write protection at the S3 layer
- How catalog-linked databases auto-federate externally-managed Iceberg tables — and how Snowflake applies independent governance regardless of data origin
- How `SNOWFLAKE.CORTEX.COMPLETE` enriches federated Iceberg data inline in SQL, with Horizon masking applying to AI-generated columns exactly as it does to raw data
- How Cortex Analyst semantic views enable natural language querying across SF-managed and federated Iceberg tables with role-based masking enforced

### Governance Summary

| Access path | Table | Governance result |
|-------------|-------|-------------------|
| Snowpark Connect (ACCOUNTADMIN) | PROTECTED_TABLE | 3 rows, `sensitive_data` raw — Scenario 1 |
| Snowpark Connect (reader role) | PROTECTED_TABLE | 2 rows filtered, `*** MASKED ***` — Scenario 1 |
| External engine via IRC | PROTECTED_TABLE | 3 rows, raw Parquet — Scenario 2 |
| External engine write to OPEN_TABLE | OPEN_TABLE | ✅ Succeeds (write credentials vended) |
| External engine write to PROTECTED_TABLE | PROTECTED_TABLE | ❌ S3 403 (read-only credentials vended) |
| Snowpark Connect (ACCOUNTADMIN) | sensitive_orders | Real credit card numbers — Scenario 2 |
| Snowpark Connect (reader role) | sensitive_orders | `****-****-****-XXXX` — Scenario 2 |
| Snowpark Connect (ACCOUNTADMIN) | AI_ORDER_INSIGHTS | `risk_level = HIGH` visible — Scenario 2 |
| Snowpark Connect (reader role) | AI_ORDER_INSIGHTS | `risk_level = *** RESTRICTED ***` — Scenario 2 |
| Cortex Analyst (ACCOUNTADMIN) | ICEBERG_AI_SEMANTIC_VIEW | NL query → `HIGH` risk orders — Scenario 2 |
| Cortex Analyst (reader role) | ICEBERG_AI_SEMANTIC_VIEW | NL query → `*** RESTRICTED ***` — Scenario 2 |

### Related Resources

- [Snowpark Connect for Apache Spark Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
- [Snowflake Managed Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-snowflake)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Horizon IRC (Iceberg REST Catalog)](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-integration-open-api)
- [Snowflake Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Cortex Analyst Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Intro to Snowpark Connect](https://www.snowflake.com/en/developers/guides/getting-started-with-snowpark-connect-for-apache-spark/)
- [Getting Started with Iceberg Tables in Snowflake](https://www.snowflake.com/en/developers/guides/getting-started-iceberg-tables/)
