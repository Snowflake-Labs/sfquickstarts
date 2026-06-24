# Databricks notebook source
# ================================================================
# SCENARIO 4 — SCOS AI ENRICHMENT PIPELINE
#
# What this demonstrates:
#   Snowpark Connect (SCOS) reads federated Iceberg tables from the
#   external catalog (Scenario 3 CLD — read only), calls Snowflake
#   Cortex LLM functions for AI enrichment, and writes the results
#   to a new Snowflake-managed Iceberg table. Horizon masking applies
#   to the AI-generated risk_level column for non-admin roles.
#
# Prerequisites:
#   Completed Scenario 1 (SF-managed Iceberg tables)
#   Completed Scenario 3 (CLD federated tables exist)
#   Run 07_cortex_ai_pipeline.sql Step 1 to verify Cortex is available
#
# !! REPLACE all <PLACEHOLDER> values below before running.
# ================================================================

# COMMAND ----------
# %md
# ## Step 0 — Parameters

# COMMAND ----------

# !! REPLACE: Regular Snowflake database (non-catalog-linked) for SCOS session init
SF_INIT_DB            = "<SF_MANAGED_ICEBERG_DB>"   # e.g. 'MY_ICEBERG_DB'

# !! REPLACE: Snowflake-managed Iceberg database and schema (target for write)
SF_MANAGED_ICEBERG_DB = "<SF_MANAGED_ICEBERG_DB>"   # e.g. 'MY_ICEBERG_DB'
SF_DEMO_SCHEMA        = "<SF_DEMO_SCHEMA>"           # e.g. 'DEMO_SCHEMA'

# !! REPLACE: Catalog-linked database (Scenario 3 — source, read only)
SF_FEDERATED_DB     = "<SF_FEDERATED_DB>"            # e.g. 'MY_DATABRICKS_DB'
DBX_SCHEMA          = "<SF_FEDERATED_SCHEMA>"        # e.g. 'my_demo_schema' — lowercase

# !! REPLACE: Non-admin reader role for governance comparison
SF_READER_ROLE      = "<SF_READER_ROLE>"             # e.g. 'DATABRICKS_DEMO_ROLE'

# Fully-qualified table references
TBL_ORDERS   = f"{SF_FEDERATED_DB}.{DBX_SCHEMA}.customer_orders"    # CLD — read only
TBL_INSIGHTS = f"{SF_MANAGED_ICEBERG_DB}.{SF_DEMO_SCHEMA}.AI_ORDER_INSIGHTS"

# COMMAND ----------
# %md
# ## Step 1 — Initialize SCOS Session

# COMMAND ----------

from snowflake.snowpark.context import get_active_session
from snowflake import snowpark_connect
from pyspark import SparkConf
from pyspark.sql.functions import col, sum as spark_sum, count

sf_session = get_active_session()

# Set context to regular Snowflake DB before initializing SCOS
sf_session.sql(f"USE DATABASE {SF_INIT_DB}").collect()

# caseSensitive=true required for catalog-linked database identifier resolution
conf = SparkConf().set("spark.sql.caseSensitive", "true")
spark = snowpark_connect.init_spark_session(conf=conf)

def switch_role(role: str):
    sf_session.sql(f"USE ROLE {role}").collect()
    print(f"Active role → {role}")

switch_role("ACCOUNTADMIN")
print("SCOS session ready")


# COMMAND ----------
# %md
# ## Step 2 — Read Federated Orders from External Catalog
#
# Source: catalog-linked database (Scenario 3 — Databricks-managed S3, read only)

# COMMAND ----------

# Read from CLD — federated Databricks Iceberg table
df_orders = spark.sql(f"SELECT * FROM {TBL_ORDERS}")
print(f"[Source] customer_orders — {df_orders.count()} rows from federated external catalog")
df_orders.orderBy("order_id").show(truncate=False)


# COMMAND ----------
# %md
# ## Step 3 — Cortex AI Enrichment via Snowflake SQL
#
# CORTEX.COMPLETE runs inside Snowflake's engine.
# Results are collected back as a Spark DataFrame.

# COMMAND ----------

# Register the federated table as a temp view so Snowpark SQL can reference it
df_orders.createOrReplaceTempView("orders_temp")

# Call Cortex enrichment via sf_session.sql — routes through Snowflake SQL engine
enriched_rows = sf_session.sql(f"""
    WITH deduped_orders AS (
        SELECT order_id, customer_id, product, amount, order_date, status
        FROM {TBL_ORDERS}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
    ),
    deduped_sensitive AS (
        SELECT order_id, region
        FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.sensitive_orders
        QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
    )
    SELECT
        co.order_id,
        co.customer_id,
        co.product,
        co.amount,
        co.order_date,
        co.status,
        COALESCE(so.region, 'UNKNOWN') AS region,
        CASE
            WHEN co.status = 'CANCELLED' THEN 'HIGH'
            WHEN co.amount >= 500        THEN 'HIGH'
            WHEN co.amount >= 100        THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_level,
        SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-8b',
            'You are a logistics AI assistant. Write one actionable sentence (max 15 words) ' ||
            'for the operations team. Product: ' || co.product ||
            ', Amount: $' || co.amount::STRING || ', Status: ' || co.status ||
            CASE WHEN so.region IS NOT NULL THEN ', Region: ' || so.region ELSE '' END || '.'
        )::VARCHAR AS ops_note,
        CURRENT_TIMESTAMP()::TIMESTAMP_LTZ(6) AS enriched_at
    FROM deduped_orders co
    LEFT JOIN deduped_sensitive so ON co.order_id = so.order_id
""").to_pandas()

import pandas as pd
print("[Enriched] AI risk classification and operational notes:")
print(enriched_rows[['order_id','product','amount','status','region','risk_level','ops_note']].to_string(index=False))


# COMMAND ----------
# %md
# ## Step 4 — Write AI Results to Snowflake-Managed Iceberg Table
#
# Target: HORIZON_DEMO_SFDB.DEMO_SCHEMA.AI_ORDER_INSIGHTS
#   → Snowflake-managed S3 (NOT the Databricks-managed S3)
#   → Accessible via Horizon IRC to external engines
#   → Horizon masking policy applied on risk_level column

# COMMAND ----------

# Write via sf_session SQL (CTAS) — Cortex enrichment runs in Snowflake's engine
# anyway, so this is the natural path. Note:
#   spark.table() READS SF-managed tables ✅ (use UPPERCASE column names)
#   spark.sql('INSERT INTO ...')     WRITES SF-managed tables ✅
#   df.write.saveAsTable()           FAILS for SF-managed tables ❌ (FDN only)
sf_session.sql(f"""
    CREATE OR REPLACE ICEBERG TABLE {TBL_INSIGHTS}
        CATALOG = 'SNOWFLAKE'
        AS
    WITH deduped_orders AS (
        SELECT order_id, customer_id, product, amount, order_date, status
        FROM {TBL_ORDERS}
        QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
    ),
    deduped_sensitive AS (
        SELECT order_id, region
        FROM {SF_FEDERATED_DB}.{DBX_SCHEMA}.sensitive_orders
        QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY order_id) = 1
    )
    SELECT
        co.order_id, co.customer_id, co.product, co.amount, co.order_date, co.status,
        COALESCE(so.region, 'UNKNOWN') AS region,
        CASE
            WHEN co.status = 'CANCELLED' THEN 'HIGH'
            WHEN co.amount >= 500        THEN 'HIGH'
            WHEN co.amount >= 100        THEN 'MEDIUM'
            ELSE 'LOW'
        END AS risk_level,
        SNOWFLAKE.CORTEX.COMPLETE(
            'llama3.1-8b',
            'You are a logistics AI assistant. Write one actionable sentence (max 15 words) ' ||
            'for the operations team. Product: ' || co.product ||
            ', Amount: $' || co.amount::STRING || ', Status: ' || co.status ||
            CASE WHEN so.region IS NOT NULL THEN ', Region: ' || so.region ELSE '' END || '.'
        )::VARCHAR AS ops_note,
        CURRENT_TIMESTAMP()::TIMESTAMP_LTZ(6) AS enriched_at
    FROM deduped_orders co
    LEFT JOIN deduped_sensitive so ON co.order_id = so.order_id
""").collect()

# Re-apply masking policy — CREATE OR REPLACE drops all column policies
sf_session.sql(f"""
    ALTER ICEBERG TABLE {TBL_INSIGHTS}
    MODIFY COLUMN risk_level
    SET MASKING POLICY {SF_MANAGED_ICEBERG_DB}.{SF_DEMO_SCHEMA}.MASK_RISK_LEVEL
""").collect()
print("[Governance] Masking policy MASK_RISK_LEVEL re-applied to risk_level")

# Read back via Snowpark to confirm write
result = sf_session.table(TBL_INSIGHTS).to_pandas()
result.columns = [c.lower() for c in result.columns]
print(f"[Write] AI_ORDER_INSIGHTS written — {len(result)} rows:")
print(result[["order_id","product","amount","status","region","risk_level","ops_note"]].to_string(index=False))


# COMMAND ----------
# %md
# ## Step 5 — Governance on AI Output
#
# Same Horizon masking framework as Scenario 1.
# Non-admin roles see *** RESTRICTED *** for HIGH risk orders.

# COMMAND ----------

import pandas as pd
COLS = ["order_id", "product", "amount", "region", "risk_level"]

switch_role("ACCOUNTADMIN")
admin_df = sf_session.sql(f"SELECT {','.join(COLS)} FROM {TBL_INSIGHTS} ORDER BY order_id").to_pandas()
admin_df.insert(0, "role", "ACCOUNTADMIN")

switch_role(SF_READER_ROLE)
reader_df = sf_session.sql(f"SELECT {','.join(COLS)} FROM {TBL_INSIGHTS} ORDER BY order_id").to_pandas()
reader_df.insert(0, "role", SF_READER_ROLE)

combined = pd.concat([admin_df, reader_df]).sort_values(["order_id","role"]).reset_index(drop=True)
print("[Governance] Same AI_ORDER_INSIGHTS table — different results per Snowflake role:")
print(combined.to_string(index=False))
print()
print("Key takeaway: Horizon governance applies to AI-generated columns")
print("the same way it applies to raw data — no special configuration needed.")


# COMMAND ----------
# %md
# ## Step 6 — AI Insights Analytics
#
# Aggregate the Cortex-enriched results using Spark DataFrames.

# COMMAND ----------

# SF-managed Iceberg tables are read via sf_session (Snowpark), not spark
switch_role("ACCOUNTADMIN")

risk_summary = sf_session.sql(f"""
    SELECT risk_level, COUNT(*) AS order_count, ROUND(SUM(amount), 2) AS total_revenue
    FROM {TBL_INSIGHTS}
    GROUP BY risk_level ORDER BY total_revenue DESC
""").to_pandas()
risk_summary.columns = [c.lower() for c in risk_summary.columns]
print("[Analytics] Revenue by AI risk level:")
print(risk_summary.to_string(index=False))

region_summary = sf_session.sql(f"""
    SELECT region, risk_level, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
    FROM {TBL_INSIGHTS}
    GROUP BY region, risk_level ORDER BY region, revenue DESC
""").to_pandas()
region_summary.columns = [c.lower() for c in region_summary.columns]
print("\n[Analytics] Revenue by region and risk level:")
print(region_summary.to_string(index=False))
