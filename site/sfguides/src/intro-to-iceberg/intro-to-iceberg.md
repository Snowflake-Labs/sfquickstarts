author: Gilberto Hernandez, Jacob Prall
id: intro-to-iceberg
language: en
summary: Learn how to create and query Iceberg tables in Snowflake using Snowpark Connect
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/iceberg
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
open in snowflake link: https://app.snowflake.com/templates/?template=intro_to_iceberg&utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=intro_to_iceberg&utm_cta=developer-guides-deeplink

# Introduction to Apache Iceberg™

<!-- ------------------------ -->
## Overview

Welcome to this quickstart for Apache Iceberg in Snowflake. This guide walks you through setting up your environment, creating Iceberg tables, and exploring powerful Iceberg features like time travel and schema evolution.

### Prerequisites
- A Snowflake account with ACCOUNTADMIN privileges (for external volume creation)
- Basic familiarity with Python and SQL
- Access to cloud storage (S3, GCS, or Azure Blob)

### What You'll Learn
- How to set up Snowpark Connect for Iceberg table operations
- How to create and configure external volumes for Iceberg storage
- How to read and write to Snowflake-managed Iceberg tables
- How to use Iceberg's time travel and snapshot capabilities
- How to perform schema evolution without downtime

### What You'll Need
- A [Snowflake Account](https://signup.snowflake.com/)
- Cloud storage bucket (S3, GCS, or Azure) with appropriate IAM permissions

### What You'll Build
- A menu analytics pipeline using Iceberg tables that demonstrates data ingestion, transformation, and Iceberg-specific features

<!-- ------------------------ -->
## Snowpark Setup

Using the **Packages** drop-down at the top of this notebook environment, search for and select **snowpark-connect**. This will install the **snowpark-connect** library in your environment.

```python
# =============================================================================
# INITIALIZE SESSION
# =============================================================================

from snowflake import snowpark_connect
from snowflake.snowpark.context import get_active_session
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col, lit, when, coalesce, trim, upper,
    sum, avg, count, min, max, countDistinct,
    current_timestamp, round
)

# initialize session
session = get_active_session()
spark = snowpark_connect.server.init_spark_session()

# print session info
print(session)


session.sql(f"USE ROLE SNOWFLAKE_LEARNING_ROLE").collect()
session.sql(f"USE WAREHOUSE SNOWFLAKE_LEARNING_WH").collect()
session.sql(f"USE DATABASE SNOWFLAKE_LEARNING_DB").collect()

# Create user-specific schema
current_user = session.sql("SELECT current_user()").collect()[0][0]
schema_name = f"{current_user}_MENU_ANALYTICS"
session.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}").collect()
session.sql(f"USE SCHEMA {schema_name}").collect()
```

<!-- ------------------------ -->
## Create External Volume

An external volume defines the cloud storage location where Iceberg table data and metadata are stored. This is required for Snowflake-managed Iceberg tables.

> **Note:** ACCOUNTADMIN privileges are required to create external volumes. In production, consider creating volumes in a separate setup process.

```python
# ACCOUNTADMIN privileges required to create external volume
session.sql(f"USE ROLE accountadmin").collect()

# Follow these instructions to create an external volume if using S3:
# https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3
session.sql(f"""
    CREATE EXTERNAL VOLUME IF NOT EXISTS iceberg_volume
    STORAGE_LOCATIONS =
    (
        (
            NAME = 's3_iceberg_storage'
            STORAGE_PROVIDER = 'S3'
            STORAGE_BASE_URL = '<your_storage_base_url>'
            STORAGE_AWS_ROLE_ARN = '<your_aws_role_arn>'
            STORAGE_AWS_EXTERNAL_ID = '<your_aws_external_id>'
        )
    )
""").collect()
```

<!-- ------------------------ -->
## Load Data

In this section, we create Iceberg tables and load data from CSV files stored in S3.

### Create Stage and Tables

```python
# =============================================================================
# LOADING DATA
# =============================================================================

# Create stage for S3 access
session.sql(f"""
    CREATE OR REPLACE STAGE blob_stage
    URL = 's3://sfquickstarts/tastybytes/'
    FILE_FORMAT = (TYPE = CSV)
""").collect()

# Create raw Iceberg table with proper schema
session.sql(f"""
    CREATE OR REPLACE ICEBERG TABLE menu_raw (
        MENU_ID NUMBER(19,0),
        MENU_TYPE_ID NUMBER(38,0),
        MENU_TYPE VARCHAR,
        TRUCK_BRAND_NAME VARCHAR,
        MENU_ITEM_ID NUMBER(38,0),
        MENU_ITEM_NAME VARCHAR,
        ITEM_CATEGORY VARCHAR,
        ITEM_SUBCATEGORY VARCHAR,
        COST_OF_GOODS_USD NUMBER(38,4),
        SALE_PRICE_USD NUMBER(38,4)
    )
    EXTERNAL_VOLUME = 'iceberg_volume'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'menu_brand_summary/'
""").collect()

# Create output Iceberg table with proper schema
session.sql(f"""
    CREATE OR REPLACE ICEBERG TABLE menu_brand_summary (
        TRUCK_BRAND_NAME VARCHAR,
        MENU_TYPE VARCHAR,
        ITEM_COUNT NUMBER(38,0),
        AVG_COST_USD NUMBER(38,2),
        AVG_PRICE_USD NUMBER(38,2),
        AVG_PROFIT_USD NUMBER(38,2),
        AVG_MARGIN_PCT NUMBER(38,2),
        MIN_PROFIT_USD NUMBER(38,2),
        MAX_PROFIT_USD NUMBER(38,2),
        TOTAL_POTENTIAL_PROFIT_USD NUMBER(38,2),
        PROCESSED_AT TIMESTAMP
    )
    EXTERNAL_VOLUME = 'iceberg_volume'
    CATALOG = 'SNOWFLAKE'
    BASE_LOCATION = 'menu_brand_summary/'
""").collect()
```

### Load CSV Data

```python
"""Load CSV data using COPY INTO."""
result = session.sql(f"""
    COPY INTO menu_raw
    FROM (
        SELECT 
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
        FROM @blob_stage/raw_pos/menu/
    )
""").collect()

# Get loaded row count
count_result = session.sql(f"SELECT COUNT(*) FROM menu_raw").collect()
row_count = count_result[0][0]

session.sql(f"USE ROLE SNOWFLAKE_LEARNING_ROLE").collect()

# Read into Spark DataFrame for processing
df_raw = spark.read.table("menu_raw")
print(f"DataFrame created with {len(df_raw.columns)} columns")
```

<!-- ------------------------ -->
## Transformations

Apply business logic transformations to calculate profitability metrics and aggregate by brand.

### Data Cleaning

```python
# =============================================================================
# TRANSFORMATIONS
# =============================================================================

df_clean = df_raw \
    .withColumn("TRUCK_BRAND_NAME", trim(upper(col("TRUCK_BRAND_NAME")))) \
    .withColumn("ITEM_CATEGORY", trim(upper(col("ITEM_CATEGORY")))) \
    .withColumn("MENU_TYPE", trim(upper(col("MENU_TYPE")))) \
    .filter(col("COST_OF_GOODS_USD").isNotNull()) \
    .filter(col("SALE_PRICE_USD").isNotNull())
```

### Profit Calculations

```python
df_with_profit = df_clean \
    .withColumn(
        "PROFIT_USD",
        round(col("SALE_PRICE_USD") - col("COST_OF_GOODS_USD"), 2)
    ) \
    .withColumn(
        "PROFIT_MARGIN_PCT",
        round(
            (col("SALE_PRICE_USD") - col("COST_OF_GOODS_USD")) / 
            col("SALE_PRICE_USD") * 100, 
            2
        )
    )
```

### Categorization

```python
df_categorized = df_with_profit \
    .withColumn(
        "PROFIT_TIER",
        when(col("PROFIT_MARGIN_PCT") >= 70, "Premium")
        .when(col("PROFIT_MARGIN_PCT") >= 50, "High")
        .when(col("PROFIT_MARGIN_PCT") >= 30, "Medium")
        .otherwise("Low")
    ) \
    .withColumn(
        "PRICE_TIER",
        when(col("SALE_PRICE_USD") >= 10, "Premium")
        .when(col("SALE_PRICE_USD") >= 5, "Mid-Range")
        .otherwise("Value")
    )
```

### Aggregation by Brand

```python
df_brand_summary = df_categorized.groupBy(
    "TRUCK_BRAND_NAME",
    "MENU_TYPE"
).agg(
    count("*").alias("ITEM_COUNT"),
    round(avg("COST_OF_GOODS_USD"), 2).alias("AVG_COST_USD"),
    round(avg("SALE_PRICE_USD"), 2).alias("AVG_PRICE_USD"),
    round(avg("PROFIT_USD"), 2).alias("AVG_PROFIT_USD"),
    round(avg("PROFIT_MARGIN_PCT"), 2).alias("AVG_MARGIN_PCT"),
    round(min("PROFIT_USD"), 2).alias("MIN_PROFIT_USD"),
    round(max("PROFIT_USD"), 2).alias("MAX_PROFIT_USD"),
    round(sum("PROFIT_USD"), 2).alias("TOTAL_POTENTIAL_PROFIT_USD")
).orderBy(col("AVG_MARGIN_PCT").desc())

# Add metadata
df_transformed = df_brand_summary \
    .withColumn("PROCESSED_AT", current_timestamp())

# Calculate overall average margin
avg_margin = df_transformed.agg(avg("AVG_MARGIN_PCT")).collect()[0][0]

df_transformed.cache()

df_transformed.select(
    "TRUCK_BRAND_NAME", "MENU_TYPE", "ITEM_COUNT", 
    "AVG_PRICE_USD", "AVG_PROFIT_USD", "AVG_MARGIN_PCT"
).show(10, truncate=False)
```

<!-- ------------------------ -->
## Write Output

Write the transformed data to the Iceberg table and verify the results.

```python
# =============================================================================
# WRITE OUTPUT
# =============================================================================
"""Write transformed data to Snowflake table."""

# Write to Snowflake
df_transformed.write.mode("append").insertInto("menu_brand_summary")

# Verify
written_count = spark.read.table("menu_brand_summary").count()
print(f"Rows written: {written_count:,}")
```

<!-- ------------------------ -->
## Iceberg Features

Iceberg tables in Snowflake provide powerful features for data management:

- **Time Travel:** Query historical data and view table snapshots using Snowpark Connect and SQL
- **Versioning:** Work with Iceberg's snapshot management system to track changes over time
- **Rollback:** Restore tables to previous versions when needed
- **Schema Evolution:** Add, drop, and rename columns without downtime or data migration

<!-- ------------------------ -->
## Cleanup

Release resources and optionally drop the objects created in this guide.

```python
# =============================================================================
# CLEANUP
# =============================================================================

# Unpersist cached DataFrames
df_transformed.unpersist()

# Optional: Drop resources (uncomment to clean up)
# session.sql(f"DROP TABLE IF EXISTS menu_raw").collect()
# session.sql(f"DROP TABLE IF EXISTS menu_brand_summary").collect()
# session.sql(f"DROP STAGE IF EXISTS blob_stage").collect()
# session.sql(f"DROP SCHEMA IF EXISTS {schema_name}").collect()
```

### Best Practices

- Use COPY INTO for bulk loading (faster than spark.read for CSV)
- Cache DataFrames when performing multiple operations
- Avoid UDFs when possible — use built-in SQL functions instead

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully created and queried Iceberg tables in Snowflake using Snowpark Connect.

### What You Learned
- How to configure external volumes for Iceberg storage
- How to create Snowflake-managed Iceberg tables
- How to load and transform data using Snowpark Connect
- Key Iceberg features available in Snowflake

### Related Resources
- [Apache Iceberg Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Configure External Volume for S3](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3)
- [Snowpark Connect Overview](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
