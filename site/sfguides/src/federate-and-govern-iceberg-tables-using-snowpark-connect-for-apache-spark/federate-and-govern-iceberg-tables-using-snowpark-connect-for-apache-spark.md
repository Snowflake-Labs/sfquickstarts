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

Through this quickstart you will use **Snowpark Connect for Apache Spark** to work through three progressive scenarios anchored on bidirectional Apache Iceberg interoperability — from Snowflake-managed Iceberg storage and Horizon governance, to open lakehouse federation with external catalogs, to AI enrichment pipelines with Cortex that bring intelligence directly to your Iceberg data.

**Scenario 1 — Snowflake-Managed Iceberg + Snowpark Connect:**
Snowflake creates and owns the Iceberg tables on its managed storage. Snowflake Horizon governance policies (column masking and row access) are applied. Snowpark Connect queries those tables using PySpark DataFrames — and because Snowpark Connect routes through Snowflake's SQL engine, governance is fully enforced.

**Scenario 2 — External Engine Reads Snowflake Tables:**
An external Iceberg-compatible engine connects to the same Scenario 1 tables via Snowflake Horizon IRC (Iceberg REST Catalog). It reads data using vended S3 credentials. Write access to the protected table is automatically blocked by credential vending. This scenario also shows the governance contrast: the external engine reads raw Parquet and bypasses Snowflake's SQL-layer policies, while Scenario 1 enforced them.

**Scenario 3 — Federate External Iceberg Tables + AI Enrichment Pipeline:**
An external catalog creates Iceberg tables (Delta + UniForm) and publishes them via an Iceberg REST endpoint. Snowflake federates them into a catalog-linked database and applies its own independent Horizon governance. Snowpark Connect reads the federated tables with live role-based masking. Snowflake Cortex then enriches the data with AI-generated risk classification and operational notes, writing results to a new Snowflake-managed Iceberg table — where Horizon governance applies to AI-generated columns just as it does to raw data. A Cortex Analyst semantic view spans both tables for natural language querying.

> **Download the code:**
> [Download all files (ZIP)](https://download-directory.github.io/?url=https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets)
>
> Or download individual files:
> - [01_sf_iceberg_catalog_setup.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/01_sf_iceberg_catalog_setup.sql)
> - [02_scos_sf_iceberg_demo.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/02_scos_sf_iceberg_demo.ipynb)
> - [03_databricks_rw_sf_iceberg.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/03_databricks_rw_sf_iceberg.py)
> - [04_databricks_create_uc_tables.py](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/04_databricks_create_uc_tables.py)
> - [05_sf_federate_databricks_uc.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/05_sf_federate_databricks_uc.sql)
> - [06_sf_notebook_query_databricks.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/06_sf_notebook_query_databricks.ipynb)
> - [07_cortex_ai_pipeline.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/07_cortex_ai_pipeline.sql)
> - [08_scos_ai_pipeline.ipynb](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/federate-and-govern-iceberg-tables-using-snowpark-connect-for-apache-spark/assets/08_scos_ai_pipeline.ipynb)

### What You'll Learn

- How Snowpark Connect runs PySpark DataFrames through Snowflake's SQL engine — enforcing Horizon governance on every query regardless of the caller
- How Horizon IRC exposes Snowflake-managed Iceberg tables to any external engine via credential vending, with write access controlled at the S3 layer
- How catalog-linked databases federate externally-managed Iceberg tables (Delta + UniForm) into Snowflake with independent Horizon governance applied at query time
- How Snowflake Cortex enriches federated Iceberg data inline in SQL — and why Horizon masking applies to AI-generated columns exactly as it does to raw data

### Key Capabilities

- **Snowflake-native Iceberg**: Snowflake manages table storage, schema, and governance end-to-end
- **Governance at the SQL layer**: Snowpark Connect routes every query through Snowflake's SQL engine — Horizon policies apply regardless of the caller's role
- **Open interoperability**: Horizon IRC exposes Snowflake-managed tables to any Iceberg REST catalog client
- **Credential-vending write control**: Snowflake controls which engines can write, enforced at S3 without any application-side code
- **Live role-based masking**: Same query, same Parquet files — different results per Snowflake role
- **AI enrichment on Iceberg**: Cortex LLM functions run inline in SQL on federated data, writing results to Snowflake-managed Iceberg
- **Governed AI output**: Horizon masking policies apply to Cortex-generated columns exactly as they do to raw data
- **Cortex Analyst semantic views**: Natural language querying across SF-managed and federated Iceberg tables with governance enforced

### What You'll Build

- Snowflake-managed Iceberg tables with column masking and row access policies
- A Snowpark Connect notebook demonstrating Horizon governance enforced via PySpark on Snowflake's engine
- An external engine read/write demo against those same tables via Horizon IRC
- Externally-managed Iceberg tables federated into Snowflake via a catalog-linked database
- A second Snowpark Connect notebook showing live role-based masking on federated tables
- A Cortex AI pipeline (Scenario 3) that reads federated Iceberg data, enriches with `CORTEX.COMPLETE`, writes to Snowflake-managed Iceberg, and exposes results via a Cortex Analyst semantic view

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

### Scenario 3 — External Catalog Tables Federated into Snowflake + AI Enrichment

```
External Catalog (Unity Catalog)
  │  Delta + Iceberg UniForm
  │  Iceberg REST endpoint: /api/2.1/unity-catalog/iceberg-rest
  │
Snowflake Catalog-Linked Database
  │  Auto-discovers schemas + tables every 30 s
  │  Applies independent Horizon masking policies
  │
  └─ Snowpark Connect Notebook
       spark.sql(f"SELECT * FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.customer_orders")
       → Snowflake SQL engine enforces its own masking policy
       → EU row filter, credit_card masked per role
```

### Scenario 3 (continued) — AI Enrichment Pipeline on Iceberg

```
Catalog-Linked Database (Scenario 3 — read only)
  DATABRICKS_DB.horizon_demo.customer_orders   ← Databricks-managed S3
  DATABRICKS_DB.horizon_demo.sensitive_orders  ← Databricks-managed S3
          ↓  Snowpark Connect reads via spark.sql() / spark.table()
          ↓  sf_session.sql() CTAS + SNOWFLAKE.CORTEX.COMPLETE() for ops_note
          ↓  ALTER ICEBERG TABLE re-applies MASK_RISK_LEVEL after CREATE OR REPLACE
SF-Managed Iceberg (new table)
  HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS  ← Snowflake-managed S3
  ┌─ risk_level: HIGH (≥$500) / MEDIUM ($100-499) / LOW (<$100)
  │              masked → *** RESTRICTED *** for non-admin roles
  └─ ops_note:   Cortex-generated operational note
          ↓  CREATE SEMANTIC VIEW ICEBERG_AI_SEMANTIC_VIEW
  Cortex Analyst (Snowsight → AI & ML → Cortex Analyst)
    "What is the total revenue by risk level?"
    "Which HIGH risk orders need immediate attention?"
    → Horizon masking enforced on risk_level per active role
```

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
org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1
```
> For Spark 3.4 (DBR 13.3 LTS): use `iceberg-spark-runtime-3.4_2.12:1.9.1`

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

Upload `02_scos_sf_iceberg_demo.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `02_scos_sf_iceberg_demo.ipynb` into the file tree**

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

## Scenario 2 — External Engine Reads Snowflake Tables

Attach `03_databricks_rw_sf_iceberg.py` to **Cluster A** (Iceberg REST catalog client, no Unity Catalog).

This connects to the same tables created in Scenario 1 via Snowflake Horizon IRC.

> **Before running — verify your PAT is active.** The PAT token expires after the configured duration. To regenerate:
> ```sql
> USE ROLE ACCOUNTADMIN;
> ALTER USER <your_user> REMOVE PROGRAMMATIC ACCESS TOKEN HORIZON_DEMO_PAT;
> ALTER USER <your_user> ADD PROGRAMMATIC ACCESS TOKEN HORIZON_DEMO_PAT
>     EXPIRY_TIME = '<date_90_days_out>'
>     COMMENT = 'Horizon IRC demo — Iceberg federation';
> ```
> Copy the token value from the output — it is shown only once.

### Configure Horizon IRC

```python
SNOWFLAKE_ACCOUNT = "<YOUR_ACCOUNT>"            # !! REPLACE: e.g. myorg-myaccount
SNOWFLAKE_ROLE    = "EXT_COMPUTE_ENG_DEMO_ROLE"
SNOWFLAKE_PAT     = "<YOUR_PAT_TOKEN>"           # from ALTER USER output
SF_DATABASE       = "HORIZON_DEMO_SFDB"
SF_SCHEMA         = "DEMO_SCHEMA"

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

> **Key contrast with Scenario 1:** Scenario 1 Snowpark Connect enforced the mask and row filter. Here, the external engine reads raw Parquet via vended S3 credentials — Snowflake's SQL-layer policies do not apply to this path.

### Demo 3 — Write OPEN_TABLE ✅

```python
# Insert a new row via the Iceberg REST Catalog write path
spark.sql(f"""
    INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE
    VALUES (99, 'Demo Widget', 3, 19.99, current_timestamp())
""")
print("Write to OPEN_TABLE: SUCCEEDED ✅")
```

**Expected:** Succeeds. The Horizon IRC credential vending path looked up the role bound to the PAT (`EXT_COMPUTE_ENG_DEMO_ROLE`), found it holds the `OPEN_TABLE_RW` database role (which has INSERT/UPDATE/DELETE), and vended write-capable S3 credentials. No application code controls this — the Snowflake catalog decides what S3 operations to permit at credential issue time.

**Confirm the write landed — verify from Snowflake immediately after:**

```python
# Read back through the same catalog to confirm the committed metadata is visible
df = spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE")
df.orderBy(df["created_at"].desc()).show(5, truncate=False)
```

**And verify from a Snowflake worksheet to show both engines see the same Iceberg table:**

```sql
-- Run in Snowflake worksheet — external write should be immediately visible
SELECT id, product, quantity, price, created_at
FROM HORIZON_DEMO_SFDB.DEMO_SCHEMA.OPEN_TABLE
ORDER BY created_at DESC
LIMIT 5;
```

**Expected:** Row `(99, 'Demo Widget', 3, 19.99, <timestamp>)` appears in both. The external engine wrote directly to Snowflake-managed S3 and committed the Iceberg metadata — Snowflake reads the same metadata and sees the row immediately. This is open Iceberg interoperability: any Iceberg-compatible engine writes, any engine reads.

> **Key governance moment — credential vending controls access at the S3 layer without any application code:**
>
> | Principal | Database Role | S3 credentials vended | Write allowed? |
> |-----------|--------------|----------------------|----------------|
> | PAT with `EXT_COMPUTE_ENG_DEMO_ROLE` → `OPEN_TABLE_RW` | INSERT / UPDATE / DELETE | Write-capable | ✅ |
> | PAT with `EXT_COMPUTE_ENG_DEMO_ROLE` → `PROTECTED_TABLE_RO` | SELECT only | Read-only | ❌ (Demo 4) |

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

## Scenario 3 — Snowpark Connect Governance Demo

Upload `06_sf_notebook_query_databricks.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `06_sf_notebook_query_databricks.ipynb` into the file tree**

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

## Scenario 3 — AI Enrichment Pipeline Setup

Run `07_cortex_ai_pipeline.sql` in a Snowflake worksheet as `ACCOUNTADMIN`.

This creates an AI-enriched Iceberg table from the Scenario 3 federated data, applies Horizon governance to the AI-generated column, and creates a Cortex Analyst semantic view.

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

> **Important:** `CREATE OR REPLACE ICEBERG TABLE` drops all column policies on the table. Always run this `ALTER ICEBERG TABLE` immediately after the CTAS. The `07_cortex_ai_pipeline.sql` script does this automatically.

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

## Scenario 3 — Snowpark Connect AI Pipeline Notebook

Upload `08_scos_ai_pipeline.ipynb` to your Snowflake workspace:
**Snowflake Workspaces → drag and drop `08_scos_ai_pipeline.ipynb` into the file tree**

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

## Scenario 3 — Cortex Analyst Demo

**Open:** Snowsight → AI & ML → Cortex Analyst

**Select semantic view:** `HORIZON_DEMO_SFDB.DEMO_SCHEMA.ICEBERG_AI_SEMANTIC_VIEW`

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
| Snowpark Connect (ACCOUNTADMIN) | sensitive_orders | Real credit card numbers — Scenario 3 |
| Snowpark Connect (reader role) | sensitive_orders | `****-****-****-XXXX` — Scenario 3 |
| Snowpark Connect (ACCOUNTADMIN) | AI_ORDER_INSIGHTS | `risk_level = HIGH` visible — Scenario 3 |
| Snowpark Connect (reader role) | AI_ORDER_INSIGHTS | `risk_level = *** RESTRICTED ***` — Scenario 3 |
| Cortex Analyst (ACCOUNTADMIN) | ICEBERG_AI_SEMANTIC_VIEW | NL query → `HIGH` risk orders — Scenario 3 |
| Cortex Analyst (reader role) | ICEBERG_AI_SEMANTIC_VIEW | NL query → `*** RESTRICTED ***` — Scenario 3 |

### Related Resources

- [Snowpark Connect for Apache Spark Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
- [Snowflake Managed Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-snowflake)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Horizon IRC (Iceberg REST Catalog)](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-integration-open-api)
- [Snowflake Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
- [Cortex Analyst Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Intro to Snowpark Connect](https://www.snowflake.com/en/developers/guides/getting-started-with-snowpark-connect-for-apache-spark/)
- [Getting Started with Iceberg Tables in Snowflake](https://www.snowflake.com/en/developers/guides/getting-started-iceberg-tables/)
