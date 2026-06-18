author: Nagesh Cherukuri
id: federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/iceberg
language: en
summary: Use Snowpark Connect for Apache Spark to create, govern, and federate Iceberg tables — from Snowflake-managed storage to cross-platform open lakehouse access with Horizon governance enforced at every layer.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts
open in snowflake: https://app.snowflake.com/developer-guides/snowpark-connect

# Federate and Govern Iceberg Tables Using Snowpark Connect for Apache Spark
<!-- ------------------------ -->

## Overview

Through this quickstart you will work through three progressive scenarios that show Snowflake as a first-class Iceberg platform — from native managed storage to bidirectional open lakehouse federation.

**Scenario 1 — Snowflake-Managed Iceberg + SCOS:**
Snowflake creates and owns the Iceberg tables on its managed storage. Snowflake Horizon governance policies (column masking and row access) are applied. Snowpark Connect (SCOS) queries those tables using PySpark DataFrames — and because SCOS routes through Snowflake's SQL engine, governance is fully enforced.

**Scenario 2 — External Engine Reads Snowflake Tables:**
An external Iceberg-compatible engine connects to the same Scenario 1 tables via Snowflake Horizon IRC (Iceberg REST Catalog). It reads data using vended S3 credentials. Write access to the protected table is automatically blocked by credential vending. This scenario also shows the governance contrast: the external engine reads raw Parquet and bypasses Snowflake's SQL-layer policies, while Scenario 1 enforced them.

**Scenario 3 — Externally-Managed Iceberg Tables Read by Snowflake:**
An external catalog creates Iceberg tables (Delta + UniForm) and publishes them via an Iceberg REST endpoint. Snowflake federates them into a catalog-linked database and applies its own independent Horizon governance. SCOS queries the federated tables with live role-based masking — demonstrating that Snowflake governance applies regardless of where the data originated.

### What You'll Learn

- How Snowflake manages Iceberg tables on its own storage and enforces Horizon governance through SCOS
- How Snowpark Connect (SCOS) runs PySpark DataFrames on Snowflake's engine with governance fully applied
- How Snowflake Horizon IRC (Iceberg REST Catalog) exposes managed tables to any Iceberg-compatible engine
- How credential vending enforces write protection on Snowflake-managed tables at the S3 layer
- The governance contrast: SCOS enforces policies; external engines reading via IRC read raw Parquet
- How Delta + Iceberg UniForm generates interoperable Iceberg metadata with no data duplication
- How Snowflake catalog-linked databases auto-discover and federate externally-managed Iceberg tables
- The three setup rules for using SCOS with catalog-linked databases

### Key Capabilities

- **Snowflake-native Iceberg**: Snowflake manages table storage, schema, and governance end-to-end
- **Governance at the SQL layer**: SCOS enforces Horizon policies on every query, regardless of the caller's role
- **Open interoperability**: Horizon IRC exposes Snowflake-managed tables to any Iceberg REST catalog client
- **Credential-vending write control**: Snowflake controls which engines can write, enforced at S3 without any application-side code
- **Live role-based masking**: Same query, same Parquet files — different results per Snowflake role

### What You'll Build

- Snowflake-managed Iceberg tables with column masking and row access policies
- A SCOS notebook demonstrating Horizon governance enforced via PySpark on Snowflake's engine
- An external engine read/write demo against those same tables via Horizon IRC
- Externally-managed Iceberg tables federated into Snowflake via a catalog-linked database
- A second SCOS notebook showing live role-based masking on federated tables

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/) with `ACCOUNTADMIN` access
- An Iceberg-compatible compute environment (for Scenario 2) — any engine that supports the Iceberg REST Catalog protocol
- An external catalog workspace with Unity Catalog enabled (for Scenario 3)
- An S3 bucket accessible from Snowflake via an external volume (for Scenario 3)

### Prerequisites

- Familiarity with Snowflake SQL and the Snowsight UI
- Basic familiarity with PySpark DataFrames
- An external volume already configured in Snowflake for Scenario 3 (`CREATE EXTERNAL VOLUME`)

<!-- ------------------------ -->

## Architecture

### Scenario 1 — Snowflake-Managed Iceberg + SCOS

```
Snowflake Account
  │  CREATE ICEBERG TABLE ... CATALOG = 'SNOWFLAKE'
  │  Horizon governance: column masking, row access policy
  │
  └─ SCOS (Snowpark Connect)
       spark.table("DEMO_SCHEMA.OPEN_TABLE")
       spark.table("DEMO_SCHEMA.PROTECTED_TABLE")
       → queries route through Snowflake SQL engine
       → Horizon policies ARE enforced
```

### Scenario 2 — External Engine Reads Snowflake Tables

```
Snowflake Account  (same tables as Scenario 1)
  │
  │  Horizon IRC endpoint: /polaris/api/catalog
  │  OAuth PAT → credential vending (S3 signed URLs)
  │
External Spark Cluster  (no Unity Catalog required)
  spark.table("sf_horizon.DEMO_SCHEMA.OPEN_TABLE")    ✅ read + write
  spark.table("sf_horizon.DEMO_SCHEMA.PROTECTED_TABLE") ✅ read only
                                                         ❌ write blocked (S3 403)
  → reads raw Parquet via vended S3 credentials
  → Snowflake SQL-layer governance NOT applied to this path
```

### Scenario 3 — External Catalog Tables Federated into Snowflake

```
External Catalog (Unity Catalog)
  │  Delta + Iceberg UniForm
  │  Iceberg REST endpoint: /api/2.1/unity-catalog/iceberg-rest
  │
Snowflake Catalog-Linked Database
  │  Auto-discovers schemas + tables every 30 s
  │  Applies independent Horizon masking policies
  │
  └─ SCOS Notebook
       spark.sql(f"SELECT * FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.customer_orders")
       → Snowflake SQL engine enforces its own masking policy
       → EU row filter, credit_card masked per role
```

<!-- ------------------------ -->

## Download the Demo Files

All scripts for this quickstart are in the assets folder:

| File | Used in | Purpose |
|------|---------|---------|
| [01_sf_iceberg_catalog_setup.sql](assets/01_sf_iceberg_catalog_setup.sql) | Snowflake worksheet | Scenario 1: create managed Iceberg tables, governance policies, credential vending, PAT |
| [02_scos_sf_iceberg_demo.py](assets/02_scos_sf_iceberg_demo.py) | Snowflake Notebook | Scenario 1: SCOS reads SF-managed tables with Horizon governance enforced |
| [03_databricks_rw_sf_iceberg.py](assets/03_databricks_rw_sf_iceberg.py) | External Spark Cluster | Scenario 2: external engine reads/writes Snowflake tables via Horizon IRC |
| [04_databricks_create_uc_tables.py](assets/04_databricks_create_uc_tables.py) | External Cluster with UC | Scenario 3 setup: create Delta + UniForm tables in external catalog |
| [05_sf_federate_databricks_uc.sql](assets/05_sf_federate_databricks_uc.sql) | Snowflake worksheet | Scenario 3 setup: catalog integration, catalog-linked database, masking |
| [06_sf_notebook_query_databricks.ipynb](assets/06_sf_notebook_query_databricks.ipynb) | Snowflake Notebook | Scenario 3: SCOS reads federated tables with live role-based masking |

> Fill in all `<PLACEHOLDER>` values in each file before running. Every parameter is documented in the header comment of each script.

<!-- ------------------------ -->

## Cluster Configuration for Scenario 2

Scenario 2 requires an external Spark cluster configured with the Apache Iceberg library. Scenarios 1 and 3 run entirely within Snowflake notebooks — no external cluster needed.

### Cluster A — Iceberg REST Catalog Client (Scenario 2 only)

| Setting | Value |
|---------|-------|
| Databricks Runtime | 14.3 LTS or 15.4 LTS (Spark 3.5.x) |
| Cluster Mode | Single User or Standard |
| Unity Catalog | **Not required — do not attach** |

**Maven Library** (install before attaching the notebook):
```
org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.0
```
> For Spark 3.4 (DBR 13.3 LTS): use `iceberg-spark-runtime-3.4_2.12:1.7.0`

**Spark Configuration** (Cluster → Advanced Options → Spark):
```
spark.sql.extensions  org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
```

### Cluster B — Unity Catalog (Scenario 3 setup only)

| Setting | Value |
|---------|-------|
| Databricks Runtime | 13.3 LTS or higher |
| Cluster Mode | Single User with Unity Catalog |
| Unity Catalog | **Metastore must be attached** |

No extra libraries or Spark config required.

<!-- ------------------------ -->

## Scenario 1 — Snowflake Setup

Run `01_sf_iceberg_catalog_setup.sql` in a Snowflake worksheet as `ACCOUNTADMIN`.

This creates two Snowflake-managed Iceberg tables, applies Horizon governance policies, and configures credential-vending database roles (used in Scenario 2).

### Create Database and Tables

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE <SF_WAREHOUSE>;

CREATE DATABASE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    COMMENT = 'Snowflake-managed Iceberg catalog (Horizon IRC)';

CREATE SCHEMA IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>;

-- OPEN_TABLE: no governance restrictions
CREATE OR REPLACE ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE (
    id          INT,
    product     STRING,
    quantity    INT,
    price       DECIMAL(10, 2),
    created_at  TIMESTAMP
)
CATALOG = 'SNOWFLAKE';

-- PROTECTED_TABLE: column masking + row access policy applied below
CREATE OR REPLACE ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE (
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
CREATE OR REPLACE MASKING POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.MASK_SENSITIVE
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') THEN val
        ELSE '*** MASKED ***'
    END;

ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    MODIFY COLUMN sensitive_data
    SET MASKING POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.MASK_SENSITIVE;

-- Row access policy: non-admin roles see current-year rows only
CREATE OR REPLACE ROW ACCESS POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.CURRENT_YEAR_ONLY
    AS (created_at TIMESTAMP) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN')
        OR YEAR(created_at) = YEAR(CURRENT_DATE());

ALTER ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    ADD ROW ACCESS POLICY <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.CURRENT_YEAR_ONLY
    ON (created_at);
```

### Configure Credential Vending (for Scenario 2)

```sql
-- OPEN_TABLE_RW: SELECT + writes → Snowflake vends write-capable S3 credentials
CREATE DATABASE ROLE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE
    TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW;

-- PROTECTED_TABLE_RO: SELECT only → Snowflake vends read-only S3 credentials
CREATE DATABASE ROLE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;
GRANT SELECT ON TABLE
    <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE
    TO DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO;

GRANT DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.OPEN_TABLE_RW      TO ROLE <SF_DATABRICKS_ROLE>;
GRANT DATABASE ROLE <SF_MANAGED_ICEBERG_DB>.PROTECTED_TABLE_RO TO ROLE <SF_DATABRICKS_ROLE>;
```

### Generate PAT (for Scenario 2)

```sql
-- ⚠ Copy the token immediately — shown only once
ALTER USER <SF_USERNAME>
    ADD PROGRAMMATIC ACCESS TOKEN MY_DEMO_PAT
    COMMENT = 'Iceberg Federation Demo — Horizon IRC integration';
```

<!-- ------------------------ -->

## Scenario 1 — SCOS Governance Demo

Upload `02_scos_sf_iceberg_demo.py` to your Snowflake workspace:
**Snowsight → Notebooks → + Notebook → Import .ipynb file**

Install the `snowpark-connect` package via the notebook package picker, then restart the session.

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

**Expected:** Same Iceberg table, same Parquet files — ACCOUNTADMIN sees 3 unmasked rows, reader role sees 2 masked rows. This is Snowflake Horizon governance enforced through SCOS.

> **Key insight:** SCOS routes queries through the Snowflake SQL engine. Horizon policies apply to every query regardless of the PySpark API used. Scenario 2 demonstrates the contrast — an external engine reading the same table bypasses these policies.

<!-- ------------------------ -->

## Scenario 2 — External Engine Reads Snowflake Tables

Attach `03_databricks_rw_sf_iceberg.py` to **Cluster A** (Iceberg REST catalog client, no Unity Catalog).

This connects to the same tables created in Scenario 1 via Snowflake Horizon IRC.

### Configure Horizon IRC

```python
SNOWFLAKE_ACCOUNT = "<SF_ACCOUNT_IDENTIFIER>"   # e.g. myorg-myaccount
SNOWFLAKE_ROLE    = "<SF_DATABRICKS_ROLE>"
SNOWFLAKE_PAT     = "<SF_PAT_TOKEN>"             # from ALTER USER output
SF_DATABASE       = "<SF_MANAGED_ICEBERG_DB>"
SF_SCHEMA         = "<SF_DEMO_SCHEMA>"

CATALOG_NAME = "sf_horizon"
IRC_BASE_URL = f"https://{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/polaris/api/catalog"
OAUTH_URL    = f"{IRC_BASE_URL}/v1/oauth/tokens"

spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}",              "org.apache.iceberg.spark.SparkCatalog")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.catalog-impl", "org.apache.iceberg.rest.RESTCatalog")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.uri",          IRC_BASE_URL)
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.oauth2-server-uri", OAUTH_URL)
# PAT as client_secret with empty client_id — prepend ':' per Iceberg credential format
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.credential", f":{SNOWFLAKE_PAT}")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.scope",      f"session:role:{SNOWFLAKE_ROLE}")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.warehouse",  SF_DATABASE)
```

### Demo 1 — Read OPEN_TABLE ✅

```python
spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE").show(truncate=False)
```

**Expected:** 3 rows. All data visible via vended S3 credentials.

### Demo 2 — Read PROTECTED_TABLE ✅ (governance contrast)

```python
spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE").show(truncate=False)
```

**Expected:** All 3 rows including the 2023 row. `sensitive_data` is **unmasked** — raw Parquet values.

> **Key contrast with Scenario 1:** Scenario 1 SCOS enforced the mask and row filter. Here, the external engine reads raw Parquet via vended S3 credentials — Snowflake's SQL-layer policies do not apply to this path.

### Demo 3 — Write OPEN_TABLE ✅

```python
spark.sql(f"""
    INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE
    VALUES (99, 'Demo Widget', 3, 19.99, current_timestamp())
""")
```

**Expected:** Succeeds. `OPEN_TABLE_RW` has write grants → Snowflake vends write-capable S3 credentials.

### Demo 4 — Write PROTECTED_TABLE ❌

```python
try:
    spark.sql(f"""
        INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE
        VALUES (99, 'Test User', 'TEST-DATA', 0.00, current_timestamp())
    """)
except Exception as e:
    print(f"Write BLOCKED ✅ — {type(e).__name__}: {str(e)[:300]}")
```

**Expected:** `AmazonS3Exception: Access Denied (Status Code: 403)`.
`PROTECTED_TABLE_RO` has SELECT only → Snowflake vends read-only credentials → `s3:PutObject` denied.

<!-- ------------------------ -->

## Scenario 3 — External Catalog Setup

Attach `04_databricks_create_uc_tables.py` to **Cluster B** (Unity Catalog enabled).

### Create Catalog, Schema, and Tables

```python
CATALOG_NAME = "<DBX_UC_CATALOG>"    # e.g. my_demo
SCHEMA_NAME  = "<DBX_UC_SCHEMA>"     # e.g. my_demo_schema (lowercase)

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

Copy these values into `05_sf_federate_databricks_uc.sql`.

<!-- ------------------------ -->

## Scenario 3 — Snowflake Setup

Run `05_sf_federate_databricks_uc.sql` in a Snowflake worksheet.

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
CREATE DATABASE IF NOT EXISTS <SF_FEDERATED_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    LINKED_CATALOG = ( CATALOG = 'MY_DATABRICKS_UC_CI' )
    COMMENT = 'Iceberg Federation Demo — Federated from external Iceberg catalog';

-- Wait ~30 s for auto-discovery, then verify
SHOW ICEBERG TABLES IN DATABASE <SF_FEDERATED_DB>;
SELECT * FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.customer_orders LIMIT 5;
```

### Apply Snowflake Horizon Governance

```sql
CREATE OR REPLACE MASKING POLICY <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES.MASK_CREDIT_CARD
    AS (val STRING) RETURNS STRING ->
    CASE
        WHEN CURRENT_ROLE() = 'ACCOUNTADMIN' THEN val
        ELSE CONCAT('****-****-****-', RIGHT(val, 4))
    END;

ALTER ICEBERG TABLE <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders
    MODIFY COLUMN "credit_card"
    SET MASKING POLICY <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES.MASK_CREDIT_CARD;
```

Snowflake defines and enforces this policy independently — it applies whether the data was written by Snowflake, the external catalog, or any other engine.

<!-- ------------------------ -->

## Scenario 3 — SCOS Governance Demo

Upload `06_sf_notebook_query_databricks.ipynb` to your Snowflake workspace.
Install the `snowpark-connect` package, then restart the session.

### Session Setup for Catalog-Linked Databases

Three setup rules are required when using SCOS with a catalog-linked database:

1. **Initialize SCOS on a regular Snowflake database** — set the session context before calling `init_spark_session`.
2. **Enable `caseSensitive` mode** — external Iceberg catalogs use lowercase schema and table names; this ensures SCOS resolves them correctly.
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

## Conclusion And Resources

Congratulations — you have completed all three scenarios!

### What You Built

- ✅ **Snowflake-managed Iceberg tables** with Horizon column masking and row access policies
- ✅ **SCOS governance demo** showing Horizon policies enforced through PySpark on Snowflake's engine
- ✅ **External engine read/write demo** via Horizon IRC with credential-vending write control
- ✅ **Catalog-linked database** auto-federating externally-managed Iceberg tables
- ✅ **Second SCOS notebook** with live role-based masking on federated tables

### What You Learned

- How Snowflake manages Iceberg tables on its own storage with Horizon governance enforced at the SQL layer
- How SCOS runs PySpark DataFrames on Snowflake's engine — governance applies to every query
- How Horizon IRC exposes Snowflake tables to any Iceberg-compatible engine via open standards
- How credential vending enforces write protection at the S3 layer without application-side code
- The governance contrast: SCOS enforces policies; external engines read raw Parquet via vended credentials
- How Delta + Iceberg UniForm generates interoperable metadata with no data duplication or ETL
- The three setup rules for using SCOS with catalog-linked databases

### Governance Summary

| Access path | Table | Governance result |
|-------------|-------|-------------------|
| SCOS (ACCOUNTADMIN) | PROTECTED_TABLE | 3 rows, `sensitive_data` raw — Scenario 1 |
| SCOS (reader role) | PROTECTED_TABLE | 2 rows filtered, `*** MASKED ***` — Scenario 1 |
| External engine via IRC | PROTECTED_TABLE | 3 rows, raw Parquet — Scenario 2 |
| External engine write to OPEN_TABLE | OPEN_TABLE | ✅ Succeeds (write credentials vended) |
| External engine write to PROTECTED_TABLE | PROTECTED_TABLE | ❌ S3 403 (read-only credentials vended) |
| SCOS (ACCOUNTADMIN) | sensitive_orders | Real credit card numbers — Scenario 3 |
| SCOS (reader role) | sensitive_orders | `****-****-****-XXXX` — Scenario 3 |

### Related Resources

- [Snowpark Connect for Apache Spark Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
- [Snowflake Managed Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-snowflake)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Horizon IRC (Iceberg REST Catalog)](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-integration-open-api)
- [Intro to Snowpark Connect](https://www.snowflake.com/en/developers/guides/getting-started-with-snowpark-connect-for-apache-spark/)
- [Getting Started with Iceberg Tables in Snowflake](https://www.snowflake.com/en/developers/guides/getting-started-iceberg-tables/)
