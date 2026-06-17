author: Nagesh Cherukuri
id: federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/snowpark, snowflake-site:taxonomy/snowflake-feature/iceberg
language: en
summary: Use Snowpark Connect for Apache Spark to federate, query, and govern Iceberg tables across open lakehouse environments — including Snowflake-managed tables with credential-vending write control and externally-managed Iceberg tables with Horizon governance.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts
open in snowflake: https://app.snowflake.com/developer-guides/snowpark-connect

# Federate and Govern Iceberg Tables Using Snowpark Connect for Apache Spark
<!-- ------------------------ -->

## Overview

Through this quickstart, you will build a fully bidirectional Iceberg federation between Snowflake and Databricks — without copying or moving data. You will use two complementary scenarios to demonstrate how Snowflake's open, standards-based architecture works seamlessly alongside Databricks.

**Scenario 1 — Snowflake as the Iceberg Catalog:** Snowflake manages Iceberg tables and exposes them to Databricks via Horizon IRC (Iceberg REST Catalog). Databricks reads and writes the tables using standard Apache Spark. Write access to sensitive tables is automatically blocked at the S3 credential-vending layer by Snowflake Horizon governance.

**Scenario 2 — Databricks as the Source, Snowflake as the Consumer:** Databricks creates Delta tables with Iceberg UniForm enabled in Unity Catalog. Snowflake federates those tables via a catalog-linked database, applies its own independent Horizon governance policies, and queries them using both SQL and Snowpark Connect (SCOS) — a PySpark-compatible API that executes on Snowflake's engine.

### What You'll Learn

- How Snowflake Horizon IRC (Iceberg REST Catalog) works and how Databricks connects to it
- How credential vending enforces write protection on Snowflake-managed Iceberg tables
- How Delta + Iceberg UniForm generates Iceberg metadata alongside Delta files with no data duplication
- How Snowflake catalog-linked databases auto-discover and federate Databricks Unity Catalog tables
- How Snowflake Horizon governance policies (column masking, row access) apply independently to federated tables
- How Snowpark Connect (SCOS) runs PySpark DataFrames on Snowflake's engine without Databricks compute
- The key SCOS requirement for catalog-linked databases: lowercase identifiers and `caseSensitive=true`

### Key Capabilities

- **Zero-copy federation**: Snowflake and Databricks share the same Parquet files on S3 — no ETL, no duplication
- **Independent governance**: Each platform enforces its own policies; Snowflake Horizon applies regardless of which engine wrote the data
- **Standards-based interoperability**: Apache Iceberg REST Catalog protocol works with any Iceberg-compatible engine
- **Live role-based masking**: SCOS notebook demonstrates same query returning different results per Snowflake role

### What You'll Build

- Snowflake-managed Iceberg tables with governance policies and credential-vending write control
- A Databricks notebook that reads and writes those tables via Horizon IRC — with one write intentionally blocked
- Databricks Unity Catalog Delta + UniForm tables with column masking and row filters
- A Snowflake catalog-linked database that auto-discovers and federates the Databricks tables
- A Snowflake SCOS notebook that queries the federated tables with live role-based masking

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/) with `ACCOUNTADMIN` access
- A [Databricks workspace](https://www.databricks.com/try-databricks) with:
  - Unity Catalog enabled (for Scenario 2)
  - Ability to create clusters with custom Spark config (for Scenario 1)
- An S3 bucket accessible from both Snowflake (via external volume IAM role) and Databricks

### Prerequisites

- Familiarity with Snowflake SQL and the Snowsight UI
- Basic familiarity with PySpark DataFrames
- An S3 external volume already configured in Snowflake (`CREATE EXTERNAL VOLUME`)

<!-- ------------------------ -->

## Architecture

Before writing any code, it helps to understand how data flows in each scenario.

### Scenario 1: Snowflake → Databricks

```
Snowflake (Iceberg REST Catalog / Horizon IRC)
    │
    │   OAuth PAT  →  REST /v1/oauth/tokens
    │   Warehouse  →  credential vending (S3 signed URLs)
    │
Databricks Spark Cluster (Cluster Config A — no UC)
    │   spark.table("sf_horizon.DEMO_SCHEMA.OPEN_TABLE")
    │   spark.table("sf_horizon.DEMO_SCHEMA.PROTECTED_TABLE")
    │
Amazon S3  (shared Parquet + Iceberg metadata)
```

**Write protection mechanism:**
- Snowflake inspects the database role: SELECT-only → read-only S3 credentials vended
- INSERT/UPDATE/DELETE on the role → write-capable S3 credentials vended
- Databricks never touches IAM directly — Snowflake is the credential authority

### Scenario 2: Databricks → Snowflake

```
Databricks Unity Catalog
    │  Delta + Iceberg UniForm
    │  (Parquet + _delta_log + Iceberg metadata in S3)
    │
    │  Iceberg REST API  →  /api/2.1/unity-catalog/iceberg-rest
    │
Snowflake Catalog-Linked Database
    │  Auto-discovers schemas + tables every 30 s
    │  Applies independent Horizon masking policies
    │
    ├─ Snowflake SQL (worksheet / Snowsight)
    └─ SCOS Notebook (PySpark → Snowflake engine, no Databricks compute)
```

<!-- ------------------------ -->


## Download the Demo Files

All scripts for this quickstart are available in the assets folder. Download them before starting:

| File | Used in | Purpose |
|------|---------|---------|
| [01_sf_iceberg_catalog_setup.sql](assets/01_sf_iceberg_catalog_setup.sql) | Snowflake worksheet | Scenario 1 setup: managed Iceberg tables, governance policies, credential vending, PAT |
| [02_databricks_rw_sf_iceberg.py](assets/02_databricks_rw_sf_iceberg.py) | Databricks — Cluster A | Scenario 1 demo: read and write Snowflake-managed tables via Horizon IRC |
| [03_databricks_create_uc_tables.py](assets/03_databricks_create_uc_tables.py) | Databricks — Cluster B | Scenario 2 setup: create Delta + UniForm tables in Unity Catalog |
| [04_sf_federate_databricks_uc.sql](assets/04_sf_federate_databricks_uc.sql) | Snowflake worksheet | Scenario 2 setup: catalog integration, catalog-linked database, masking |
| [05_sf_notebook_query_databricks.ipynb](assets/05_sf_notebook_query_databricks.ipynb) | Snowflake Workspace | Scenario 2 demo: SCOS notebook with live role-based masking |

> Fill in all `<PLACEHOLDER>` values in each file before running. Every parameter is documented in the header comment of each script.

## Databricks Cluster Configuration

Two Databricks clusters are required. Create both before starting.

### Cluster A — No Unity Catalog (Scenario 1)

Used for `02_databricks_rw_sf_iceberg.py`. This cluster connects to Snowflake Horizon IRC using the open-source Apache Iceberg library.

| Setting | Value |
|---------|-------|
| Databricks Runtime | 14.3 LTS or 15.4 LTS (Spark 3.5.x) |
| Cluster Mode | Single User or Standard |
| Unity Catalog | **Not required — do not attach** |

**Maven Library** (install before attaching the notebook):
```
org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.0
```
> For DBR 13.3 LTS (Spark 3.4): use `iceberg-spark-runtime-3.4_2.12:1.7.0`

**Spark Configuration** (Cluster → Advanced Options → Spark):
```
spark.sql.extensions  org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
```

### Cluster B — With Unity Catalog (Scenario 2)

Used for `03_databricks_create_uc_tables.py`. Unity Catalog must be attached.

| Setting | Value |
|---------|-------|
| Databricks Runtime | 13.3 LTS or higher |
| Cluster Mode | Single User with Unity Catalog |
| Unity Catalog | **Metastore must be attached** |

No extra Maven libraries or Spark config required.

<!-- ------------------------ -->

## Snowflake Setup — Scenario 1

Run `01_sf_iceberg_catalog_setup.sql` in a Snowflake worksheet as `ACCOUNTADMIN`.

This script creates:
- A database and schema for the managed Iceberg tables
- Two tables: `OPEN_TABLE` (read-write for Databricks) and `PROTECTED_TABLE` (read-only for Databricks)
- Snowflake Horizon governance policies: column masking on `sensitive_data`, row access policy on `created_at`
- Database roles that control credential vending (the write-protection mechanism)
- A Snowflake Programmatic Access Token (PAT) for Databricks to authenticate to Horizon IRC

### Create the Database and Tables

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE <SF_WAREHOUSE>;

CREATE DATABASE IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    COMMENT = 'Snowflake-managed Iceberg catalog (Horizon IRC)';

CREATE SCHEMA IF NOT EXISTS <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>;

-- OPEN_TABLE: no governance, Databricks can read and write
CREATE OR REPLACE ICEBERG TABLE <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.OPEN_TABLE (
    id          INT,
    product     STRING,
    quantity    INT,
    price       DECIMAL(10, 2),
    created_at  TIMESTAMP
)
CATALOG = 'SNOWFLAKE';

-- PROTECTED_TABLE: governance policies applied, Databricks read-only
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

### Configure Credential Vending via Database Roles

```sql
-- OPEN_TABLE_RW: SELECT + write grants → Snowflake vends write-capable S3 credentials
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

### Generate the Snowflake PAT

```sql
-- ⚠ Copy the token value immediately — shown only once
ALTER USER <SF_USERNAME>
    ADD PROGRAMMATIC ACCESS TOKEN BNY_DEMO_PAT
    COMMENT = 'Databricks Horizon IRC integration';
```

Paste the PAT into `02_databricks_rw_sf_iceberg.py` as `SNOWFLAKE_PAT`.

<!-- ------------------------ -->

## Databricks Reads & Writes — Scenario 1

Attach `02_databricks_rw_sf_iceberg.py` to **Cluster A** (no Unity Catalog). Run each command cell in order.

### Configure Horizon IRC

```python
SNOWFLAKE_ACCOUNT = "<SF_ACCOUNT_IDENTIFIER>"   # e.g. myorg-myaccount
SNOWFLAKE_ROLE    = "<SF_DATABRICKS_ROLE>"
SNOWFLAKE_PAT     = "<SF_PAT_TOKEN>"             # from ALTER USER output
SF_DATABASE       = "<SF_MANAGED_ICEBERG_DB>"

CATALOG_NAME = "sf_horizon"
IRC_BASE_URL = f"https://{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/polaris/api/catalog"
OAUTH_URL    = f"{IRC_BASE_URL}/v1/oauth/tokens"

spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}",           "org.apache.iceberg.spark.SparkCatalog")
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
df_open = spark.table(f"{CATALOG_NAME}.DEMO_SCHEMA.OPEN_TABLE")
df_open.show(truncate=False)
```

**Expected:** 3 rows (Laptop, Mouse, Keyboard). All data visible — no governance policies on this table.

### Demo 2 — Read PROTECTED_TABLE ✅

```python
df_prot = spark.table(f"{CATALOG_NAME}.DEMO_SCHEMA.PROTECTED_TABLE")
df_prot.show(truncate=False)
```

**Expected:** All 3 rows, `sensitive_data` unmasked (raw Parquet via vended S3 credentials — Snowflake SQL policies are not applied to this path).

> **Key insight:** Horizon governance applies when data is queried via Snowflake SQL. Databricks reads raw Parquet directly. Write access, however, is enforced at the credential layer.

### Demo 3 — Write OPEN_TABLE ✅

```python
spark.sql(f"""
    INSERT INTO {CATALOG_NAME}.DEMO_SCHEMA.OPEN_TABLE
    VALUES (99, 'Demo Widget', 3, 19.99, current_timestamp())
""")
```

**Expected:** Succeeds. `OPEN_TABLE_RW` has INSERT grants → Snowflake vends write-capable S3 credentials.

### Demo 4 — Write PROTECTED_TABLE ❌

```python
try:
    spark.sql(f"""
        INSERT INTO {CATALOG_NAME}.DEMO_SCHEMA.PROTECTED_TABLE
        VALUES (99, 'Test User', 'TEST-DATA', 0.00, current_timestamp())
    """)
except Exception as e:
    print(f"Write BLOCKED ✅ — {type(e).__name__}: {str(e)[:300]}")
```

**Expected:** `AmazonS3Exception: Access Denied (Status Code: 403)`.
`PROTECTED_TABLE_RO` has SELECT only → Snowflake vends read-only credentials → `s3:PutObject` is denied.

<!-- ------------------------ -->

## Create Databricks UC Tables — Scenario 2

Attach `03_databricks_create_uc_tables.py` to **Cluster B** (with Unity Catalog).

### Create Catalog and Schema

```python
CATALOG_NAME = "<DBX_UC_CATALOG>"    # e.g. bny_demo
SCHEMA_NAME  = "<DBX_UC_SCHEMA>"     # e.g. bny_demo_schema (lowercase)

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}")
spark.sql(f"CREATE SCHEMA  IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}")
```

### Create Delta + Iceberg UniForm Tables

Delta UniForm writes standard Delta files **and** Iceberg metadata in parallel. Any Iceberg-compatible engine (Snowflake, Spark, Trino) can read the table via a standard Iceberg REST catalog — no data duplication, no ETL.

```python
spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders (
    order_id    BIGINT, customer_id BIGINT, product STRING,
    amount      DECIMAL(10,2), order_date DATE, status STRING
)
USING DELTA
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableIcebergCompatV2'          = 'true',
    'delta.columnMapping.mode'             = 'name'
)
""")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders (
    order_id BIGINT, customer_id BIGINT, customer_name STRING,
    credit_card STRING, amount DECIMAL(10,2), order_date DATE, region STRING
)
USING DELTA
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableIcebergCompatV2'          = 'true',
    'delta.columnMapping.mode'             = 'name'
)
""")
```

### Apply Unity Catalog Governance

```python
# Column mask on credit_card (Unity Catalog side — does NOT propagate to Snowflake)
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card(cc STRING)
RETURN CASE WHEN is_account_group_member('account_unity_admin') THEN cc
            ELSE CONCAT('****-****-****-', RIGHT(cc, 4)) END
""")
spark.sql(f"""ALTER TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders
ALTER COLUMN credit_card SET MASK {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card""")

# Row filter — hide EU rows from non-EU principals
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG_NAME}.{SCHEMA_NAME}.filter_eu_rows(region STRING)
RETURN CASE WHEN is_account_group_member('eu_data_reader') THEN TRUE
            WHEN region = 'EU' THEN FALSE ELSE TRUE END
""")
spark.sql(f"""ALTER TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders
SET ROW FILTER {CATALOG_NAME}.{SCHEMA_NAME}.filter_eu_rows ON (region)""")
```

### Print the Snowflake Catalog Integration Config

```python
WORKSPACE_HOST = "<DBX_WORKSPACE_HOST>"
print(f"CATALOG_URI  : https://{WORKSPACE_HOST}/api/2.1/unity-catalog/iceberg-rest")
print(f"CATALOG_NAME : {CATALOG_NAME}")
```

Copy these values into the next step.

<!-- ------------------------ -->

## Snowflake Federates Databricks Tables — Scenario 2

Run `04_sf_federate_databricks_uc.sql` in Snowflake.

### Create Catalog Integration

```sql
CREATE OR REPLACE CATALOG INTEGRATION BNY_DATABRICKS_UC_CI
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
SELECT SYSTEM$VERIFY_CATALOG_INTEGRATION('BNY_DATABRICKS_UC_CI');

-- List schemas and tables discovered
SELECT SYSTEM$LIST_NAMESPACES_FROM_CATALOG('BNY_DATABRICKS_UC_CI');
SELECT SYSTEM$LIST_ICEBERG_TABLES_FROM_CATALOG('BNY_DATABRICKS_UC_CI', '<DBX_UC_SCHEMA>');
```

### Create Catalog-Linked Database

```sql
CREATE DATABASE IF NOT EXISTS <SF_FEDERATED_DB>
    EXTERNAL_VOLUME = '<SF_EXTERNAL_VOLUME>'
    LINKED_CATALOG = (
        CATALOG = 'BNY_DATABRICKS_UC_CI'
    )
    COMMENT = 'Federated from Databricks Unity Catalog';

-- Wait ~30 seconds for auto-discovery, then verify
SHOW ICEBERG TABLES IN DATABASE <SF_FEDERATED_DB>;

-- Read test (lowercase schema name required for Unity Catalog CLDs)
SELECT * FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.customer_orders;
```

### Apply Snowflake Horizon Governance

Snowflake applies its own masking policy **independently** from Databricks UC policies. Both platforms govern the same data — with their own rules.

```sql
CREATE SCHEMA IF NOT EXISTS <SF_GOVERNANCE_DB>.GOVERNANCE_POLICIES;

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

### Governance Comparison

```sql
-- ACCOUNTADMIN: sees real credit card numbers
USE ROLE ACCOUNTADMIN;
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders;

-- Reader role: credit_card masked
USE ROLE <SF_READER_ROLE>;
SELECT CURRENT_ROLE() AS role, order_id, customer_name, credit_card
FROM <SF_FEDERATED_DB>.<SF_FEDERATED_SCHEMA>.sensitive_orders;

USE ROLE ACCOUNTADMIN;
```

| Role | credit_card value |
|------|------------------|
| ACCOUNTADMIN | `4111-1111-1111-1111` (raw) |
| `<SF_READER_ROLE>` | `****-****-****-1111` (masked by Snowflake policy) |

<!-- ------------------------ -->

## SCOS Notebook — Governance Demos

Upload `05_sf_notebook_query_databricks.ipynb` to your Snowflake workspace:
**Snowsight → Notebooks → + Notebook → Import .ipynb file**

Install the `snowpark-connect` package using the notebook package picker, then restart the session.

### Why SCOS Works Differently for Catalog-Linked Databases

SCOS (Snowpark Connect) uses sqlglot to translate Spark plans into Snowflake SQL. By default, it auto-uppercases and quotes identifiers — sending `"HORIZON_DEMO"` (quoted uppercase). For catalog-linked databases backed by Databricks Unity Catalog, schemas and tables are stored as lowercase (`horizon_demo`). Snowflake does exact-case matching on quoted identifiers, causing a TABLE_OR_VIEW_NOT_FOUND error.

**Three requirements for SCOS to work with catalog-linked databases:**

```python
# 1. Initialize SCOS on a regular (non-catalog-linked) database
sf_session.sql(f"USE DATABASE {SF_INIT_DB}").collect()

# 2. Set caseSensitive=true to prevent auto-uppercasing of identifiers
conf = SparkConf().set("spark.sql.caseSensitive", "true")
spark = snowpark_connect.init_spark_session(conf=conf)

# 3. Use fully-qualified lowercase schema + table names in spark.sql()
df = spark.sql(f"SELECT * FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.customer_orders")
#                                                 ^^^^^^^^^^^ lowercase
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
print(f"[DataFrame] customer_orders — {df_orders.count()} rows")
df_orders.orderBy("order_id").show(truncate=False)
```

### Demo 2–3 — Filter and Aggregate

```python
# Filter SHIPPED/DELIVERED
df_orders.filter(col("status").isin("SHIPPED", "DELIVERED")) \
    .select("order_id", "product", "amount", "status") \
    .orderBy("amount", ascending=False).show(truncate=False)

# Revenue by status
df_orders.groupBy("status") \
    .agg(count("*").alias("order_count"), spark_sum("amount").alias("total_revenue")) \
    .orderBy("total_revenue", ascending=False).show(truncate=False)
```

### Demo 4–5 — Role-Based Masking

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

switch_role("ACCOUNTADMIN")
admin_rows  = spark.sql(f"SELECT * FROM {TBL_SENSITIVE}").select("order_id", "customer_name", "credit_card").collect()

switch_role(SF_READER_ROLE)
reader_rows = spark.sql(f"SELECT * FROM {TBL_SENSITIVE}").select("order_id", "customer_name", "credit_card").collect()

admin_pd  = pd.DataFrame([r.asDict() for r in admin_rows])
admin_pd.insert(0, "role", "ACCOUNTADMIN")

reader_pd = pd.DataFrame([r.asDict() for r in reader_rows])
reader_pd.insert(0, "role", SF_READER_ROLE)

combined = pd.concat([admin_pd, reader_pd]).sort_values(["order_id", "role"]).reset_index(drop=True)
print(combined.to_string(index=False))
```

**Expected output:** Same `order_id` rows appear twice — once with raw `4111-1111-1111-1111` (ACCOUNTADMIN) and once with `****-****-****-1111` (reader role). Same Parquet files, different governance outcomes.

<!-- ------------------------ -->

## Conclusion And Resources

Congratulations — you have successfully built a bidirectional Iceberg federation between Snowflake and Databricks!

### What You Built

- ✅ **Snowflake-managed Iceberg tables** exposed via Horizon IRC with credential-vending write control
- ✅ **Databricks reads and writes** those tables using standard Apache Spark and Iceberg REST catalog
- ✅ **Delta + UniForm tables** in Databricks Unity Catalog with UC governance policies
- ✅ **Snowflake catalog-linked database** that auto-discovers and federates the Databricks tables
- ✅ **Snowflake Horizon masking policies** applied independently to federated tables
- ✅ **SCOS notebook** demonstrating PySpark DataFrames on Snowflake's engine with live role-based masking

### What You Learned

- How Snowflake Horizon IRC enables Databricks to read and write managed Iceberg tables
- How credential vending enforces write protection at the S3 layer
- How Delta + Iceberg UniForm generates interoperable metadata with no data duplication
- How Snowflake catalog-linked databases provide live federation with zero ETL
- How Snowflake Horizon governance applies independently of the source platform's policies
- The three requirements to use SCOS with catalog-linked databases (non-CLD init DB, `caseSensitive=true`, lowercase schema names)

### Governance Summary

| Access path | Table | Result |
|-------------|-------|--------|
| Snowflake SQL (ACCOUNTADMIN) | PROTECTED_TABLE | 3 rows, `sensitive_data` unmasked |
| Snowflake SQL (reader role) | PROTECTED_TABLE | 2 rows (2023 filtered), `*** MASKED ***` |
| Databricks via Horizon IRC | PROTECTED_TABLE | 3 rows, raw Parquet (no SQL-layer governance) |
| Databricks write to OPEN_TABLE | OPEN_TABLE | ✅ Succeeds (write-capable credentials vended) |
| Databricks write to PROTECTED_TABLE | PROTECTED_TABLE | ❌ S3 403 (read-only credentials vended) |
| SCOS notebook (ACCOUNTADMIN) | sensitive_orders | Real credit card numbers |
| SCOS notebook (reader role) | sensitive_orders | `****-****-****-XXXX` |

### Related Resources

- [Snowpark Connect for Apache Spark Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
- [Snowflake Managed Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-snowflake)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Horizon IRC (Iceberg REST Catalog)](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-integration-open-api)
- [Intro to Snowpark Connect](https://www.snowflake.com/en/developers/guides/getting-started-with-snowpark-connect-for-apache-spark/)
- [Getting Started with Iceberg Tables in Snowflake](https://www.snowflake.com/en/developers/guides/getting-started-iceberg-tables/)
