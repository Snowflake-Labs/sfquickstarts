# Databricks notebook source
# ================================================================
# SCENARIO 1 — SCOS READS SNOWFLAKE-MANAGED ICEBERG TABLES
#
# What this demonstrates:
#   Snowpark Connect (SCOS) runs PySpark DataFrames on Snowflake's
#   engine. Because queries route through the Snowflake SQL engine,
#   Horizon governance policies ARE enforced — unlike Databricks
#   reading via Horizon IRC (shown in Scenario 2).
#
#   Demo 1 — Read OPEN_TABLE          (no policies, all roles same)
#   Demo 2 — ACCOUNTADMIN view        (3 rows, sensitive_data raw)
#   Demo 3 — Reader role view         (2 rows filtered, *** MASKED ***)
#   Demo 4 — Side-by-side comparison  (same table, different outcomes)
#
# Prerequisites:
#   Run 01_sf_iceberg_catalog_setup.sql in Snowflake first.
#   Upload this notebook to Snowflake Workspace:
#     Snowsight → Notebooks → + Notebook → Import .ipynb file
#   Install snowpark-connect package via the notebook package picker.
#
# !! REPLACE all <PLACEHOLDER> values below before running.
# ================================================================

# COMMAND ----------
# %md
# ## Step 0 — Parameters

# COMMAND ----------

# !! REPLACE: Snowflake database containing the managed Iceberg tables
#    (created by 01_sf_iceberg_catalog_setup.sql)
SF_MANAGED_ICEBERG_DB = "<SF_MANAGED_ICEBERG_DB>"   # e.g. 'MY_ICEBERG_DB'

# !! REPLACE: Schema inside that database
SF_DEMO_SCHEMA = "<SF_DEMO_SCHEMA>"                  # e.g. 'DEMO_SCHEMA'

# !! REPLACE: Non-admin reader role for governance demo
SF_READER_ROLE = "<SF_DATABRICKS_ROLE>"              # e.g. 'DATABRICKS_DEMO_ROLE'

# Table references
TBL_OPEN      = f"{SF_MANAGED_ICEBERG_DB}.{SF_DEMO_SCHEMA}.OPEN_TABLE"
TBL_PROTECTED = f"{SF_MANAGED_ICEBERG_DB}.{SF_DEMO_SCHEMA}.PROTECTED_TABLE"


# COMMAND ----------
# %md
# ## Step 1 — Initialize SCOS Session

# COMMAND ----------

from snowflake.snowpark.context import get_active_session
from snowflake import snowpark_connect
from pyspark.sql.functions import col
import pandas as pd

sf_session = get_active_session()
sf_session.sql(f"USE DATABASE {SF_MANAGED_ICEBERG_DB}").collect()

# Native Snowflake tables — no caseSensitive override needed
spark = snowpark_connect.init_spark_session()

def switch_role(role: str):
    """USE ROLE via sf_session — spark.sql('USE ROLE ...') raises parse error in SCOS."""
    sf_session.sql(f"USE ROLE {role}").collect()
    print(f"Active role → {role}")

switch_role("ACCOUNTADMIN")
print("Session ready")


# COMMAND ----------
# %md
# ## Demo 1 — Read OPEN_TABLE  ✅
#
# No governance policies. All roles see identical rows and columns.

# COMMAND ----------

switch_role("ACCOUNTADMIN")
print(f"[DataFrame] OPEN_TABLE — all roles see the same data:")
spark.table(TBL_OPEN).orderBy("id").show(truncate=False)


# COMMAND ----------
# %md
# ## Demo 2 — ACCOUNTADMIN reads PROTECTED_TABLE
#
# Masking policy: admin bypasses mask → `sensitive_data` is raw.
# Row access policy: admin sees ALL rows including 2023 row.

# COMMAND ----------

switch_role("ACCOUNTADMIN")
print("[DataFrame] PROTECTED_TABLE — ACCOUNTADMIN (unmasked, all rows):")
spark.table(TBL_PROTECTED).orderBy("id").show(truncate=False)
print()
print("Rows returned : 3  (including 2023 row)")
print("sensitive_data: raw value visible")


# COMMAND ----------
# %md
# ## Demo 3 — Reader role reads PROTECTED_TABLE
#
# Masking policy fires: `sensitive_data` → `*** MASKED ***`
# Row access policy fires: 2023 row filtered out.

# COMMAND ----------

switch_role(SF_READER_ROLE)
print(f"[DataFrame] PROTECTED_TABLE — {SF_READER_ROLE} (masked, filtered):")
spark.table(TBL_PROTECTED).orderBy("id").show(truncate=False)
print()
print("Rows returned : 2  (2023 row filtered by row access policy)")
print("sensitive_data: *** MASKED ***")


# COMMAND ----------
# %md
# ## Demo 4 — Side-by-Side Governance Comparison
#
# Same Iceberg table. Same Parquet files on S3.
# Different results depending on the active Snowflake role.
# This is Snowflake Horizon governance enforced through SCOS.

# COMMAND ----------

COLS = ["id", "customer_name", "sensitive_data", "amount"]

switch_role("ACCOUNTADMIN")
admin_rows = spark.table(TBL_PROTECTED).select(*COLS).collect()

switch_role(SF_READER_ROLE)
reader_rows = spark.table(TBL_PROTECTED).select(*COLS).collect()

admin_pd  = pd.DataFrame([r.asDict() for r in admin_rows])
admin_pd.insert(0,  "role", "ACCOUNTADMIN")

reader_pd = pd.DataFrame([r.asDict() for r in reader_rows])
reader_pd.insert(0, "role", SF_READER_ROLE)

combined = pd.concat([admin_pd, reader_pd]).sort_values(["id", "role"]).reset_index(drop=True)
print("[DataFrame side-by-side] Horizon governance via SCOS:")
print(combined.to_string(index=False))
print()
print("Key takeaway:")
print("  SCOS routes through Snowflake SQL → Horizon policies ARE enforced.")
print("  Scenario 2 shows the contrast: Databricks reads raw Parquet and bypasses these policies.")
