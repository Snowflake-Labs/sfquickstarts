# Databricks notebook source
# ================================================================
# SCENARIO 1 — DATABRICKS READS & WRITES SNOWFLAKE-MANAGED ICEBERG
#
# What this demonstrates:
#   Demo 1 — Read OPEN_TABLE        ✅ success
#   Demo 2 — Read PROTECTED_TABLE   ✅ success (raw Parquet, governance NOT applied)
#   Demo 3 — Write OPEN_TABLE       ✅ success (write-capable S3 creds vended)
#   Demo 4 — Write PROTECTED_TABLE  ❌ blocked (read-only S3 creds vended → 403)
#   Demo 5 — Delete from OPEN_TABLE ✅ success
#
# Prerequisites:
#   1. Run 01_sf_iceberg_catalog_setup.sql in Snowflake first.
#   2. Copy the PAT token from Step 8 of that script.
#   3. Attach this notebook to Cluster Config A (NO Unity Catalog).
#      See DEMO_SCRIPT.md → Cluster Configuration A.
#   4. Install Maven library on the cluster before attaching:
#        org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.7.0
#      (use iceberg-spark-runtime-3.4_2.12:1.7.0 for DBR 13.3 LTS)
#
# !! REPLACE all <PLACEHOLDER> values below before running.
# ================================================================

# COMMAND ----------
# %md
# ## Step 0 — Configure Horizon IRC Catalog
# Set your Snowflake account details and PAT token here.

# COMMAND ----------

# !! REPLACE: Snowflake account in hyphenated org-account format
#    e.g. 'myorg-myaccount'  (find in Snowsight → Admin → Accounts → Account URL)
SNOWFLAKE_ACCOUNT = "<SF_ACCOUNT_IDENTIFIER>"

# !! REPLACE: Snowflake role for Databricks (created by 01_sf_iceberg_catalog_setup.sql)
SNOWFLAKE_ROLE    = "<SF_DATABRICKS_ROLE>"

# !! REPLACE: PAT token from ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN output
#    Generate with Step 8 of 01_sf_iceberg_catalog_setup.sql.
#    ⚠  Never commit this value to source control.
SNOWFLAKE_PAT     = "<SF_PAT_TOKEN>"

# !! REPLACE: Snowflake database that is the Iceberg catalog
SF_DATABASE       = "<SF_MANAGED_ICEBERG_DB>"

CATALOG_NAME = "sf_horizon"   # local Spark catalog alias — can be any name

IRC_BASE_URL = f"https://{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/polaris/api/catalog"
OAUTH_URL    = f"{IRC_BASE_URL}/v1/oauth/tokens"

# ── Register the Iceberg REST catalog with Spark ──────────────────────────
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}",
               "org.apache.iceberg.spark.SparkCatalog")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.catalog-impl",
               "org.apache.iceberg.rest.RESTCatalog")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.uri",               IRC_BASE_URL)
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.oauth2-server-uri", OAUTH_URL)

# Horizon IRC: PAT as client_secret, no client_id → prepend ':' for empty client_id
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.credential",  f":{SNOWFLAKE_PAT}")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.scope",       f"session:role:{SNOWFLAKE_ROLE}")
spark.conf.set(f"spark.sql.catalog.{CATALOG_NAME}.warehouse",   SF_DATABASE)

print(f"Catalog  : {CATALOG_NAME}")
print(f"IRC URL  : {IRC_BASE_URL}")
print(f"Warehouse: {SF_DATABASE}")
print(f"Role     : {SNOWFLAKE_ROLE}")


# COMMAND ----------
# %md
# ## Step 1 — Discover Catalog (verify connectivity)

# COMMAND ----------

# !! REPLACE: schema name (SF_DEMO_SCHEMA from 01_sf_iceberg_catalog_setup.sql)
SF_SCHEMA = "<SF_DEMO_SCHEMA>"

print("=== Namespaces (Schemas) ===")
spark.sql(f"SHOW NAMESPACES IN {CATALOG_NAME}").show()

print(f"=== Tables in {SF_SCHEMA} ===")
spark.sql(f"SHOW TABLES IN {CATALOG_NAME}.{SF_SCHEMA}").show()


# COMMAND ----------
# %md
# ## Demo 1 — Read: OPEN_TABLE  ✅ expected: SUCCESS
#
# No governance policies on this table.
# DATABRICKS_DEMO_ROLE has OPEN_TABLE_RW (SELECT + INSERT + UPDATE + DELETE).

# COMMAND ----------

print("=== READ: OPEN_TABLE ===")
df_open = spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE")
df_open.show(truncate=False)
print(f"Row count: {df_open.count()}")


# COMMAND ----------
# %md
# ## Demo 2 — Read: PROTECTED_TABLE  ✅ expected: SUCCESS
#
# PROTECTED_TABLE carries Snowflake Horizon governance policies
# (column masking on sensitive_data, row access policy on created_at).
#
# ⚠  IMPORTANT CAVEAT: Horizon IRC vends S3 credentials directly to Databricks.
# Databricks reads raw Parquet — Snowflake SQL-engine policies are NOT applied.
# All 3 rows are visible, sensitive_data is unmasked.
#
# Governance policies DO apply when the table is queried via Snowflake SQL
# (demonstrated in 04_sf_federate_databricks_uc.sql governance section).

# COMMAND ----------

print("=== READ: PROTECTED_TABLE (via Horizon IRC — raw Parquet path) ===")
df_prot = spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE")
df_prot.show(truncate=False)
print(f"Row count: {df_prot.count()}")
print()
print("Note: All 3 rows visible; sensitive_data is unmasked in Iceberg/S3 path.")
print("Governance is enforced ONLY via Snowflake SQL, not IRC vended-credential reads.")


# COMMAND ----------
# %md
# ## Demo 3 — Write: OPEN_TABLE  ✅ expected: SUCCESS
#
# DATABRICKS_DEMO_ROLE has INSERT/UPDATE/DELETE on OPEN_TABLE.
# Snowflake vends write-capable S3 credentials → s3:PutObject succeeds.

# COMMAND ----------

print("=== WRITE: OPEN_TABLE ===")
spark.sql(f"""
    INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE
    VALUES (99, 'Demo Widget', 3, 19.99, current_timestamp())
""")
print("Write to OPEN_TABLE: SUCCESS")

print()
print("=== OPEN_TABLE after insert ===")
spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE").orderBy("id").show(truncate=False)


# COMMAND ----------
# %md
# ## Demo 4 — Write: PROTECTED_TABLE  ❌ expected: FAIL
#
# DATABRICKS_DEMO_ROLE has SELECT only on PROTECTED_TABLE
# (no INSERT/UPDATE/DELETE — see PROTECTED_TABLE_RO database role).
# Snowflake vends READ-ONLY S3 credentials for this table.
# Databricks tries to commit the Iceberg snapshot (s3:PutObject) → S3 returns 403.
#
# Expected error:
#   AmazonS3Exception: Access Denied (Status Code: 403; Error Code: AccessDenied)

# COMMAND ----------

print("=== WRITE: PROTECTED_TABLE (expected to FAIL) ===")
try:
    spark.sql(f"""
        INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE
        VALUES (99, 'Test User', 'TEST-DATA', 0.00, current_timestamp())
    """)
    print("ERROR: Write succeeded — verify PROTECTED_TABLE_RO has no write grants.")
except Exception as e:
    print("Write BLOCKED ✅ — as expected.")
    print(f"Exception : {type(e).__name__}")
    print(f"Message   : {str(e)[:600]}")


# COMMAND ----------
# %md
# ## Demo 5 — Cleanup: Delete row from OPEN_TABLE  ✅ expected: SUCCESS

# COMMAND ----------

print("=== DELETE from OPEN_TABLE (row id=99) ===")
spark.sql(f"DELETE FROM {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE WHERE id = 99")
print("Delete: SUCCESS")

print()
print("=== OPEN_TABLE after delete (back to 3 original rows) ===")
spark.table(f"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE").orderBy("id").show(truncate=False)


# COMMAND ----------
# %md
# ## Governance Comparison Summary
#
# Run these in a Snowflake worksheet to confirm policies apply via Snowflake SQL:
#
# ```sql
# -- ACCOUNTADMIN: 3 rows, unmasked
# USE ROLE ACCOUNTADMIN;
# SELECT * FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;
#
# -- DATABRICKS_DEMO_ROLE: 2 rows (2023 row filtered), *** MASKED ***
# USE ROLE <SF_DATABRICKS_ROLE>;
# SELECT * FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;
# ```
#
# | Access path                            | Rows | sensitive_data  |
# |----------------------------------------|------|-----------------|
# | Snowflake SQL (ACCOUNTADMIN)           |  3   | unmasked        |
# | Snowflake SQL (<SF_DATABRICKS_ROLE>)   |  2   | *** MASKED ***  |
# | Databricks via Horizon IRC (any role)  |  3   | unmasked        |
#
# → Snowflake Horizon governs the SQL path; credential vending governs writes.


# COMMAND ----------
# %md
# ## Horizon IRC Diagnostic (curl — run from terminal if connectivity fails)
#
# ```bash
# ACCOUNT="<SF_ACCOUNT_IDENTIFIER>"
# DB="<SF_MANAGED_ICEBERG_DB>"
# ROLE="<SF_DATABRICKS_ROLE>"
# PAT="<SF_PAT_TOKEN>"
# BASE="https://${ACCOUNT}.snowflakecomputing.com/polaris/api/catalog"
#
# # 1. Reachability
# curl -i --max-time 15 "${BASE}/v1/config?warehouse=${DB}"
#
# # 2. Exchange PAT for bearer token
# TOKEN=$(curl -s -X POST "${BASE}/v1/oauth/tokens" \
#   -H "Content-Type: application/x-www-form-urlencoded" \
#   --data-urlencode "grant_type=client_credentials" \
#   --data-urlencode "scope=session:role:${ROLE}" \
#   --data-urlencode "client_secret=${PAT}" \
#   | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
#
# # 3. List namespaces
# curl -i "${BASE}/v1/${DB}/namespaces" -H "Authorization: Bearer $TOKEN"
#
# # 4. Load table metadata
# curl -i "${BASE}/v1/${DB}/namespaces/<SF_DEMO_SCHEMA>/tables/OPEN_TABLE" \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "X-Iceberg-Access-Delegation: vended-credentials"
# ```
