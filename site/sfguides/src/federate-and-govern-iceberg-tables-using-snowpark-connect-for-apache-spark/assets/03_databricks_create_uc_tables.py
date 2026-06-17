# Databricks notebook source
# ================================================================
# SCENARIO 2 — STEP 1 of 2: CREATE DATABRICKS UC TABLES
#
# What this does:
#   • Creates two Delta + Iceberg UniForm tables in Databricks
#     Unity Catalog (UC).
#   • CUSTOMER_ORDERS  — open table, no access restrictions.
#   • SENSITIVE_ORDERS — PII table with UC column mask + row filter.
#   • Grants a Snowflake service principal read access.
#   • Prints the Iceberg REST endpoint for use in Step 2
#     (04_sf_federate_databricks_uc.sql).
#
# Prerequisites:
#   • Unity Catalog must be enabled on your Databricks workspace.
#   • Attach to Cluster Config B (WITH Unity Catalog).
#     See DEMO_SCRIPT.md → Cluster Configuration B.
#   • Run as a workspace admin or catalog owner.
#
# !! REPLACE all <PLACEHOLDER> values below before running.
# ================================================================

# COMMAND ----------
# %md
# ## Step 0 — Parameters

# COMMAND ----------

# !! REPLACE: Databricks workspace hostname (no https://)
#    e.g. 'adb-1234567890.12.azuredatabricks.net'
WORKSPACE_HOST = "<DBX_WORKSPACE_HOST>"

# !! REPLACE: Unity Catalog catalog name to create
CATALOG_NAME   = "<DBX_UC_CATALOG>"      # e.g. 'bny_demo'

# !! REPLACE: Schema (namespace) inside the catalog
SCHEMA_NAME    = "<DBX_UC_SCHEMA>"       # e.g. 'bny_demo_schema' — must be lowercase

# !! REPLACE: Databricks service principal or user granted SELECT for Snowflake
#    Create at: Workspace Settings → Identity & Access → Service Principals
SP_NAME        = "<DBX_SERVICE_PRINCIPAL>"  # e.g. 'snowflake-federation-sp'

print(f"Catalog : {CATALOG_NAME}")
print(f"Schema  : {SCHEMA_NAME}")
print(f"SP      : {SP_NAME}")


# COMMAND ----------
# %md
# ## Step 1 — Create Catalog and Schema

# COMMAND ----------

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}")
spark.sql(f"CREATE SCHEMA  IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}")
print(f"Ready: {CATALOG_NAME}.{SCHEMA_NAME}")


# COMMAND ----------
# %md
# ## Step 2 — Create Iceberg Tables via Delta UniForm
#
# Delta UniForm writes Delta files AND Iceberg metadata in parallel.
# Any Iceberg-compatible engine (Snowflake, Spark, Trino) can read
# the table through a standard Iceberg REST catalog.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders (
    order_id    BIGINT,
    customer_id BIGINT,
    product     STRING,
    amount      DECIMAL(10, 2),
    order_date  DATE,
    status      STRING
)
USING DELTA
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableIcebergCompatV2'          = 'true',
    'delta.columnMapping.mode'             = 'name'
)
""")
print("customer_orders created (Iceberg UniForm enabled)")

spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders (
    order_id      BIGINT,
    customer_id   BIGINT,
    customer_name STRING,
    credit_card   STRING,
    amount        DECIMAL(10, 2),
    order_date    DATE,
    region        STRING
)
USING DELTA
TBLPROPERTIES (
    'delta.universalFormat.enabledFormats' = 'iceberg',
    'delta.enableIcebergCompatV2'          = 'true',
    'delta.columnMapping.mode'             = 'name'
)
""")
print("sensitive_orders created (Iceberg UniForm enabled)")


# COMMAND ----------
# %md
# ## Step 3 — Load Sample Data

# COMMAND ----------

spark.sql(f"""
INSERT INTO {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders VALUES
    (1, 101, 'Laptop',     999.99, '2025-01-15', 'SHIPPED'),
    (2, 102, 'Mouse',       29.99, '2025-01-16', 'DELIVERED'),
    (3, 103, 'Keyboard',    49.99, '2025-01-17', 'PENDING'),
    (4, 101, 'Monitor',    399.99, '2025-01-18', 'SHIPPED'),
    (5, 104, 'Headphones',  79.99, '2025-01-19', 'DELIVERED'),
    (6, 105, 'Webcam',      59.99, '2025-01-20', 'PENDING')
""")

spark.sql(f"""
INSERT INTO {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders VALUES
    (1, 101, 'Alice Johnson', '4111-1111-1111-1111', 1299.98, '2025-01-15', 'US-WEST'),
    (2, 102, 'Bob Smith',     '4222-2222-2222-2222',   29.99, '2025-01-16', 'US-EAST'),
    (3, 103, 'Carol White',   '4333-3333-3333-3333',   49.99, '2025-01-17', 'EU'),
    (4, 101, 'Alice Johnson', '4111-1111-1111-1111',  399.99, '2025-01-18', 'US-WEST'),
    (5, 104, 'Dan Brown',     '4444-4444-4444-4444',   79.99, '2025-01-19', 'APAC')
""")
print("Sample data loaded")


# COMMAND ----------
# %md
# ## Step 4 — Apply Unity Catalog Governance on sensitive_orders
#
# Column mask: hide credit_card from non-admin users.
# Row filter:  hide EU rows from users without 'eu_data_reader' group.
#
# Note: These Databricks UC policies do NOT propagate to Snowflake when
# the table is federated. Snowflake applies its own independently-defined
# masking policies (set up in 04_sf_federate_databricks_uc.sql).

# COMMAND ----------

# Column mask: hide credit_card for non-admins
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card(cc STRING)
RETURN CASE
    WHEN is_account_group_member('account_unity_admin') THEN cc
    ELSE CONCAT('****-****-****-', RIGHT(cc, 4))
END
""")

spark.sql(f"""
ALTER TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders
ALTER COLUMN credit_card
SET MASK {CATALOG_NAME}.{SCHEMA_NAME}.mask_credit_card
""")
print("Column mask applied to credit_card")

# Row filter: hide EU rows from non-EU-reader group members
spark.sql(f"""
CREATE OR REPLACE FUNCTION {CATALOG_NAME}.{SCHEMA_NAME}.filter_eu_rows(region STRING)
RETURN CASE
    WHEN is_account_group_member('eu_data_reader') THEN TRUE
    WHEN region = 'EU' THEN FALSE
    ELSE TRUE
END
""")

spark.sql(f"""
ALTER TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders
SET ROW FILTER {CATALOG_NAME}.{SCHEMA_NAME}.filter_eu_rows ON (region)
""")
print("Row filter applied — EU rows hidden from non-eu_data_reader members")


# COMMAND ----------
# %md
# ## Step 5 — Grant Snowflake Service Principal Read Access

# COMMAND ----------

spark.sql(f"GRANT USE CATALOG ON CATALOG {CATALOG_NAME}           TO `{SP_NAME}`")
spark.sql(f"GRANT USE SCHEMA  ON SCHEMA  {CATALOG_NAME}.{SCHEMA_NAME} TO `{SP_NAME}`")
spark.sql(f"GRANT SELECT ON TABLE {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders  TO `{SP_NAME}`")
spark.sql(f"GRANT SELECT ON TABLE {CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders TO `{SP_NAME}`")
print(f"Granted SELECT on both tables to: {SP_NAME}")


# COMMAND ----------
# %md
# ## Step 6 — Verify Iceberg Metadata is Generated

# COMMAND ----------

df = spark.table(f"{CATALOG_NAME}.{SCHEMA_NAME}.customer_orders")
print(f"customer_orders row count: {df.count()}")
df.show(truncate=False)

print("\n=== Table properties (confirm UniForm is active) ===")
spark.sql(f"SHOW TBLPROPERTIES {CATALOG_NAME}.{SCHEMA_NAME}.customer_orders").show(truncate=False)


# COMMAND ----------
# %md
# ## Step 7 — Print Snowflake Catalog Integration Config
#
# Copy these values into 04_sf_federate_databricks_uc.sql.

# COMMAND ----------

ICEBERG_REST_ENDPOINT = f"https://{WORKSPACE_HOST}/api/2.1/unity-catalog/iceberg-rest"

print("=" * 60)
print("Paste into 04_sf_federate_databricks_uc.sql:")
print("=" * 60)
print(f"  CATALOG_URI  : {ICEBERG_REST_ENDPOINT}")
print(f"  CATALOG_NAME : {CATALOG_NAME}")
print()
print("Also paste a Databricks PAT or service principal OAuth token")
print("as DBX_PAT_TOKEN in 04_sf_federate_databricks_uc.sql.")
print()
print("Generate PAT: Databricks top-right avatar → Settings → Developer → Access Tokens")


# COMMAND ----------
# %md
# ## Step 8 — Quick Read Verification

# COMMAND ----------

print("=== customer_orders (no policies) ===")
spark.table(f"{CATALOG_NAME}.{SCHEMA_NAME}.customer_orders").show(truncate=False)

print("\n=== sensitive_orders (UC policies active) ===")
spark.table(f"{CATALOG_NAME}.{SCHEMA_NAME}.sensitive_orders").show(truncate=False)
# credit_card shows ****-****-****-XXXX for non-admin users
# EU row is hidden for non-eu_data_reader members
