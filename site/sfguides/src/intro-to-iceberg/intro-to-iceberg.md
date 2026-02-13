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

Welcome to this quickstart for Apache Iceberg in Snowflake. In this guide, we'll cover:
- Setting up your Snowpark Connect environment for Snowflake-managed Iceberg table operations
- Reading and writing to Snowflake-managed Iceberg tables

We'll also take a look at:
- Time Travel and snapshot management with Iceberg tables
- Schema evolution
- Manifest and column-level statistics from Iceberg metadata
- Partition inspection and skew detection
- Table properties for descriptive metadata

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
- How to inspect manifest and column-level statistics from Iceberg metadata
- How to detect partition skew
- How to manage table properties for descriptive metadata

### What You'll Need
- A [Snowflake Account](https://signup.snowflake.com/)
- Cloud storage bucket (S3, GCS, or Azure) with appropriate IAM permissions

### What You'll Build
- A menu analytics pipeline using Iceberg tables that demonstrates data ingestion, transformation, and Iceberg-specific features

<!-- ------------------------ -->
## Snowpark Connect Setup

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

Iceberg tables store data and metadata (Iceberg snapshots, manifests) in external cloud storage, rather than Snowflake's internal storage. The external volume provides Snowflake with the storage location and credentials needed to read from and write to your cloud storage for Iceberg table operations.

> **Note:** ACCOUNTADMIN privileges are required to create external volumes. In production, consider creating volumes in a separate setup process.

```python
# ACCOUNTADMIN privileges required to create external volume
# Consider creating the volume in a separate process, but demonstrated here for completion
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
## Load Data and Transformations

We will leverage existing CSV data stored in S3. We will load the data in these files into Iceberg tables. We then perform some basic transformations on the data.

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

### Transformations, Aggregation, and Write Output

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

# -------------------------------------------------------------------------
# Profit Calculations
# -------------------------------------------------------------------------

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

# -------------------------------------------------------------------------
# Categorization
# -------------------------------------------------------------------------

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

# -------------------------------------------------------------------------
# Aggregation by Brand
# -------------------------------------------------------------------------

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

# =============================================================================
# WRITE OUTPUT
# =============================================================================
"""Write transformed data to Snowflake table."""

# Write to Snowflake
df_transformed.write.mode("append").insertInto("menu_brand_summary")

# Verify
written_count = spark.read.table("menu_brand_summary").count()
print(f"Rows written: {written_count:,}")

# =============================================================================
# CLEANUP & SUMMARY
# =============================================================================

# Unpersist cached DataFrames
df_transformed.unpersist()

# Optional: Drop resources (uncomment to clean up)
# session.sql(f"DROP TABLE IF EXISTS menu_raw").collect()
# session.sql(f"DROP TABLE IF EXISTS menu_brand_summary").collect()
# session.sql(f"DROP STAGE IF EXISTS blob_stage").collect()
# session.sql(f"DROP SCHEMA IF EXISTS {schema_name}").collect()

# =============================================================================
# BEST PRACTICES
# =============================================================================
#
# PERFORMANCE:
#    - Use COPY INTO for bulk loading (faster than spark.read for CSV)
#    - Cache DataFrame for multiple operations
#    - Avoid UDFs
# =============================================================================
```

<!-- ------------------------ -->
## Snowflake Platform Features for Iceberg Tables

Snowflake's platform features extend to Iceberg tables, allowing you to leverage familiar capabilities. The code cells below demonstrate each feature using Snowpark Connect against the tables we created in the previous section.

### Time Travel and Snapshot Management

- Query historical data snapshots within your retention period
- View snapshot history to track how the table has changed over time
- Restore to a previous snapshot when needed

### Schema Evolution

- Add, drop, or rename columns using standard `ALTER ICEBERG TABLE` commands
- Schema changes are tracked in Iceberg's metadata log

### Manifest and Column Statistics

- Read row counts, file counts, and data sizes from Iceberg metadata — no data scan required
- Check whether column-level statistics (null counts, bounds) are available for query planning

### Partition Inspection

- Inspect data file distribution across partitions
- Detect partition skew that could degrade AI workload performance

### Table Properties

- Read and set key-value properties stored in the Iceberg metadata
- Use properties for descriptions, ownership tags, classification labels, and other metadata

<!-- ------------------------ -->
## Time Travel and Snapshot Management

Iceberg tables in Snowflake maintain an immutable history of snapshots. Each write creates a new snapshot. You can query any prior snapshot within the retention window, inspect the history, and restore if needed.

```python
# =============================================================================
# 4.1  TIME TRAVEL & SNAPSHOT MANAGEMENT
# =============================================================================
# Iceberg tables in Snowflake maintain an immutable history of snapshots.
# Each write creates a new snapshot. You can query any prior snapshot within
# the retention window, inspect the history, and restore if needed.

# ---- View snapshot history ----
# Every committed write (INSERT, MERGE, DELETE) produces a snapshot.
# The snapshots metadata table shows when each one was committed.

df_snapshots = spark.read.table("menu_brand_summary.snapshots")
df_snapshots.select(
    "committed_at",
    "snapshot_id",
    "parent_id",
    "operation"
).orderBy(col("committed_at").desc()).show(truncate=False)

# ---- Measure freshness from the latest snapshot ----
# How many hours since the last write? This comes from metadata, not a data scan.

freshness = session.sql("""
    SELECT
        MAX(committed_at)                                           AS latest_snapshot_ts,
        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(committed_at)))
            / 3600.0                                                AS hours_since_last_write
    FROM menu_brand_summary.snapshots
""").collect()

print(f"Latest snapshot:       {freshness[0]['LATEST_SNAPSHOT_TS']}")
print(f"Hours since last write: {freshness[0]['HOURS_SINCE_LAST_WRITE']:.2f}")

# ---- Time Travel: query data as of a prior timestamp ----
# Replace the timestamp below with an actual value from the snapshot history.

# first_snapshot_ts = df_snapshots.orderBy("committed_at").first()["committed_at"]
# df_historical = session.sql(f"""
#     SELECT * FROM menu_brand_summary AT(TIMESTAMP => '{first_snapshot_ts}'::TIMESTAMP_LTZ)
# """).to_pandas()
# print(f"Rows at first snapshot: {len(df_historical)}")
```

<!-- ------------------------ -->
## Schema Evolution

Iceberg tracks every schema change in its metadata log. You can add, drop, and rename columns without rewriting existing data files — Iceberg handles the mapping transparently at read time.

```python
# =============================================================================
# 4.2  SCHEMA EVOLUTION
# =============================================================================
# Iceberg tracks every schema change in its metadata log. You can add, drop,
# and rename columns without rewriting existing data files — Iceberg handles
# the mapping transparently at read time.

# ---- Add a column ----
session.sql("""
    ALTER ICEBERG TABLE menu_brand_summary
    ADD COLUMN LAST_REVIEWED_AT TIMESTAMP
""").collect()
print("Column LAST_REVIEWED_AT added.")

# ---- Rename a column ----
session.sql("""
    ALTER ICEBERG TABLE menu_brand_summary
    RENAME COLUMN LAST_REVIEWED_AT TO REVIEW_TIMESTAMP
""").collect()
print("Column renamed to REVIEW_TIMESTAMP.")

# ---- Drop a column ----
session.sql("""
    ALTER ICEBERG TABLE menu_brand_summary
    DROP COLUMN REVIEW_TIMESTAMP
""").collect()
print("Column REVIEW_TIMESTAMP dropped.")

# ---- Verify current schema via Spark ----
df_schema_check = spark.read.table("menu_brand_summary")
print(f"\nCurrent columns ({len(df_schema_check.columns)}):")
for field in df_schema_check.schema.fields:
    print(f"  {field.name:40s} {str(field.dataType)}")

# ---- View the metadata log to see schema evolution events ----
# Each ALTER produces a new metadata log entry. The count reflects how many
# schema versions the table has gone through.

df_meta_log = spark.read.table("menu_brand_summary.metadata_log_entries")
df_meta_log.select(
    "timestamp",
    "file"
).orderBy(col("timestamp").desc()).show(truncate=False)

meta_count = df_meta_log.count()
print(f"Total metadata log entries: {meta_count}")
```

<!-- ------------------------ -->
## Manifest and Column Statistics

Iceberg stores rich statistics in its metadata layer — manifest files track row counts and file counts, while individual data files carry column-level statistics (null counts, lower/upper bounds). These enable profiling and query planning without ever scanning the data itself.

```python
# =============================================================================
# 4.3  MANIFEST & COLUMN STATISTICS
# =============================================================================
# Iceberg stores rich statistics in its metadata layer — manifest files track
# row counts and file counts, while individual data files carry column-level
# statistics (null counts, lower/upper bounds). These enable profiling and
# query planning without ever scanning the data itself.

# ---- Manifest-level statistics ----
# Each manifest tracks a group of data files. Summing across manifests gives
# totals for the entire table — row counts, file counts — from metadata alone.

df_manifests = spark.read.table("menu_brand_summary.manifests") \
    .filter(col("content") == 0)  # content=0 → data manifests (not delete manifests)

df_manifests.select(
    "path",
    "added_data_files_count",
    "added_rows_count",
    "existing_rows_count"
).show(truncate=False)

manifest_summary = df_manifests.agg(
    count("*").alias("manifest_count"),
    sum("added_data_files_count").alias("total_data_files"),
    sum("added_rows_count").alias("total_rows_added"),
    sum("existing_rows_count").alias("total_rows_existing")
).collect()[0]

print(f"Manifests:          {manifest_summary['manifest_count']}")
print(f"Total data files:   {manifest_summary['total_data_files']}")
print(f"Total rows added:   {manifest_summary['total_rows_added']}")
print(f"Total rows existing:{manifest_summary['total_rows_existing']}")

# ---- Column-level statistics ----
# Each data file can carry per-column stats: null counts, lower bounds, and
# upper bounds. If these are present, engines can skip files during query
# planning (min/max pruning) and profile columns without reading data.

df_files = spark.read.table("menu_brand_summary.files")

file_stats = df_files.agg(
    count("*").alias("total_files"),
    sum(when(col("null_value_counts").isNotNull(), 1).otherwise(0)).alias("files_with_null_stats"),
    sum(when(col("lower_bounds").isNotNull(), 1).otherwise(0)).alias("files_with_lower_bounds"),
    sum(when(col("upper_bounds").isNotNull(), 1).otherwise(0)).alias("files_with_upper_bounds")
).collect()[0]

total = file_stats["total_files"]
coverage = file_stats["files_with_null_stats"] / total if total > 0 else 0

print(f"\nColumn statistics coverage:")
print(f"  Total data files:           {total}")
print(f"  Files with null stats:      {file_stats['files_with_null_stats']}")
print(f"  Files with lower bounds:    {file_stats['files_with_lower_bounds']}")
print(f"  Files with upper bounds:    {file_stats['files_with_upper_bounds']}")
print(f"  Statistics coverage:        {coverage:.0%}")
```

<!-- ------------------------ -->
## Partition Inspection

Iceberg's hidden partitioning means you don't partition at query time — the table metadata already knows how files map to partitions. Inspecting the files metadata table reveals how data is distributed and whether any partitions are skewed (too many or too few files), which directly impacts AI workload scan performance.

```python
# =============================================================================
# 4.4  PARTITION INSPECTION
# =============================================================================
# Iceberg's hidden partitioning means you don't partition at query time —
# the table metadata already knows how files map to partitions. Inspecting
# the files metadata table reveals how data is distributed and whether any
# partitions are skewed (too many or too few files), which directly impacts
# AI workload scan performance.

# ---- File-level partition distribution ----
# Group data files by their partition value and count files per partition.

df_files = spark.read.table("menu_brand_summary.files")

df_partition_stats = df_files.groupBy("partition") \
    .agg(count("*").alias("file_count")) \
    .orderBy(col("file_count").desc())

df_partition_stats.show(truncate=False)

# ---- Detect partition skew ----
# A high skew ratio (max / min file count) means some partitions have far
# more files than others. This causes uneven scan times and can bottleneck
# parallel reads in training pipelines.

partition_agg = df_partition_stats.agg(
    count("*").alias("partition_count"),
    max("file_count").alias("max_files"),
    min("file_count").alias("min_files")
).collect()[0]

partition_count = partition_agg["partition_count"]
max_files = partition_agg["max_files"]
min_files = partition_agg["min_files"]
skew_ratio = max_files / min_files if min_files and min_files > 0 else None

print(f"Partitions:       {partition_count}")
print(f"Max files/part:   {max_files}")
print(f"Min files/part:   {min_files}")
print(f"Skew ratio:       {skew_ratio:.2f}" if skew_ratio else "Skew ratio:       N/A (single partition or zero-file partition)")
```

<!-- ------------------------ -->
## Table Properties

Iceberg table properties are key-value pairs stored in the table metadata. They control table behavior (compaction, write format, snapshot retention) and can also carry descriptive metadata (owner, description, classification). These properties travel with the table across engines.

```python
# =============================================================================
# 4.5  TABLE PROPERTIES
# =============================================================================
# Iceberg table properties are key-value pairs stored in the table metadata.
# They control table behavior (compaction, write format, snapshot retention)
# and can also carry descriptive metadata (owner, description, classification).
# These properties travel with the table across engines.

# ---- Read current table properties ----
df_props = session.sql("SHOW TBLPROPERTIES menu_brand_summary").to_pandas()
print("Current table properties:")
print(df_props.to_string(index=False))

# ---- Set a custom property ----
# Use table properties to store descriptions, ownership, or classification
# tags directly in the Iceberg metadata.

session.sql("""
    ALTER ICEBERG TABLE menu_brand_summary
    SET TBLPROPERTIES (
        'description' = 'Aggregated profit metrics per truck brand and menu type',
        'owner'       = 'data-engineering',
        'pii'         = 'false'
    )
""").collect()
print("\nCustom properties set.")

# ---- Verify the new properties ----
df_props_updated = session.sql("SHOW TBLPROPERTIES menu_brand_summary").to_pandas()
print("\nUpdated table properties:")
print(df_props_updated.to_string(index=False))

# ---- Remove a property ----
session.sql("""
    ALTER ICEBERG TABLE menu_brand_summary
    UNSET TBLPROPERTIES ('pii')
""").collect()
print("\nProperty 'pii' removed.")
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully created and queried Iceberg tables in Snowflake using Snowpark Connect, and explored key Iceberg platform features.

### What You Learned
- How to configure external volumes for Iceberg storage
- How to create Snowflake-managed Iceberg tables
- How to load and transform data using Snowpark Connect
- How to use time travel and snapshot management with Iceberg tables
- How to perform schema evolution without downtime
- How to inspect manifest and column-level statistics from Iceberg metadata
- How to detect partition skew from file-level metadata
- How to manage Iceberg table properties

### Related Resources
- [Apache Iceberg Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Configure External Volume for S3](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-s3)
- [Snowpark Connect Overview](https://docs.snowflake.com/en/developer-guide/snowpark-connect/snowpark-connect-overview)
