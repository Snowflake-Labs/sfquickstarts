author: Gilberto Hernandez
id: comprehensive-guide-to-dynamic-tables
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/dynamic-tables
language: en
summary: Learn how to build automated data pipelines on Snowflake using Dynamic Tables. 
open in snowflake link: https://app.snowflake.com/templates/?template=getting_started_with_dynamic_tables&utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=getting_started_with_dynamic_tables&utm_cta=developer-guides-deeplink
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Comprehensive Guide to Snowflake Dynamic Tables

Snowflake Dynamic Tables provide a **declarative way to build data pipelines** that automatically refresh based on changes to upstream data. They simplify data transformation workflows by eliminating the need to manually manage refresh schedules and dependencies.

## Overview

**In this guide, you will learn:**
- How Dynamic Tables automatically maintain fresh data with TARGET_LAG
- How to leverage incremental refresh for efficient pipeline processing
- The differences between Dynamic Tables and Materialized Views
- How Dynamic Tables simplify Change Data Capture (CDC) workflows
  - Traditional approach using Streams and Tasks
  - Simplified approach using Dynamic Tables
  - Side-by-side comparison and when to use each
- Monitoring and validating Dynamic Table refresh operations

---

## Load Sample Data

In this section, we load data from CSV files in S3 into Snowflake tables.

```sql
-- =============================================================================
-- LOAD DATA
-- =============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE SNOWFLAKE_LEARNING_DB;
USE WAREHOUSE COMPUTE_WH;

-- Create user-specific schema based on current user
SET user_schema = CURRENT_USER() || '_DYNAMIC_TABLES';
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($user_schema);
USE SCHEMA IDENTIFIER($user_schema);

-- File format for CSV files
CREATE OR REPLACE FILE FORMAT csv_ff
  TYPE = 'CSV';

-- External stage pointing to Tasty Bytes public S3 bucket
CREATE OR REPLACE STAGE tasty_bytes_stage
  URL = 's3://sfquickstarts/tastybytes/'
  FILE_FORMAT = csv_ff;

-- Create raw menu table
CREATE OR REPLACE TABLE menu_raw
(
  menu_id NUMBER(19,0),
  menu_type_id NUMBER(38,0),
  menu_type VARCHAR,
  truck_brand_name VARCHAR,
  menu_item_id NUMBER(38,0),
  menu_item_name VARCHAR,
  item_category VARCHAR,
  item_subcategory VARCHAR,
  cost_of_goods_usd NUMBER(38,4),
  sale_price_usd NUMBER(38,4),
  menu_item_health_metrics_obj VARIANT
);

-- Load menu data from S3
COPY INTO menu_raw
FROM @tasty_bytes_stage/raw_pos/menu/;

-- Verify data loaded
SELECT * FROM menu_raw LIMIT 10;
```

---

## Create Dynamic Tables

A Dynamic Table is a declarative way to define a data pipeline in Snowflake. Unlike traditional tables or views, dynamic tables automatically refresh based on the TARGET_LAG you specify, ensuring data freshness without manual intervention.

**Key Components:**

| Parameter | Description |
|:----------|:------------|
| `TARGET_LAG` | Controls how fresh the data should be (e.g., '10 minutes', '1 hour', 'DOWNSTREAM') |
| `WAREHOUSE` | Specifies the compute resource to use for refresh operations |
| `REFRESH_MODE` | Can be 'AUTO' (default), 'INCREMENTAL', or 'FULL' |
| `AS SELECT` | The query that defines the table's contents |

```sql
-- This creates a dynamic table that calculates menu item profitability
-- and refreshes automatically to stay within 3 hours of the source data
CREATE OR REPLACE DYNAMIC TABLE menu_profitability
  TARGET_LAG = '3 hours'
  WAREHOUSE = COMPUTE_WH
  AS
SELECT
  -- Product identifiers
  menu_item_id,
  menu_item_name,
  truck_brand_name,
  menu_type,
  item_category,
  item_subcategory,

  -- Pricing information
  cost_of_goods_usd,
  sale_price_usd,

  -- Profitability calculations
  (sale_price_usd - cost_of_goods_usd) AS profit_usd,
  ROUND(
    ((sale_price_usd - cost_of_goods_usd) / NULLIF(sale_price_usd, 0)) * 100,
    2
  ) AS profit_margin_pct,

  -- Price categorization
  CASE
    WHEN sale_price_usd < 5 THEN 'Budget'
    WHEN sale_price_usd BETWEEN 5 AND 10 THEN 'Mid-Range'
    ELSE 'Premium'
  END AS price_tier

FROM menu_raw
WHERE sale_price_usd IS NOT NULL
  AND cost_of_goods_usd IS NOT NULL;
```

Query the dynamic table:

```sql
SELECT
  truck_brand_name,
  menu_item_name,
  price_tier,
  profit_usd,
  profit_margin_pct
FROM menu_profitability
ORDER BY profit_margin_pct DESC
LIMIT 10;
```

---

## Incremental Refresh

Incremental refresh is when a dynamic table processes only the rows that changed in the source table since the last refresh, rather than recomputing the entire table from scratch.

To demonstrate how dynamic tables refresh incrementally, we:

1. Create a stored procedure to generate new menu data
2. Call the stored procedure to insert new rows into the `menu_raw` table
3. Manually refresh the dynamic tables to demonstrate incremental processing
4. Query refresh history to verify incremental vs full refresh

### Create a Stored Procedure to Generate Test Data

```sql
-- Create stored procedure to generate new menu items
CREATE OR REPLACE PROCEDURE generate_menu_items(num_rows INTEGER)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
  items_before INTEGER;
  items_after INTEGER;
  items_inserted INTEGER;
BEGIN
  -- Capture count before insert
  SELECT COUNT(*) INTO :items_before FROM menu_raw;

  -- Insert new menu items based on existing data with randomized values
  INSERT INTO menu_raw (
    menu_id,
    menu_type_id,
    menu_type,
    truck_brand_name,
    menu_item_id,
    menu_item_name,
    item_category,
    item_subcategory,
    cost_of_goods_usd,
    sale_price_usd,
    menu_item_health_metrics_obj
  )
  SELECT
    (SELECT COALESCE(MAX(menu_id), 0) FROM menu_raw) + ROW_NUMBER() OVER (ORDER BY RANDOM()) AS menu_id,
    menu_type_id,
    menu_type,
    truck_brand_name,
    (SELECT COALESCE(MAX(menu_item_id), 0) FROM menu_raw) + ROW_NUMBER() OVER (ORDER BY RANDOM()) AS menu_item_id,
    'New Menu Item ' || ((SELECT COALESCE(MAX(menu_item_id), 0) FROM menu_raw) + ROW_NUMBER() OVER (ORDER BY RANDOM())) AS menu_item_name,
    item_category,
    item_subcategory,
    cost_of_goods_usd * (0.8 + UNIFORM(0, 0.4, RANDOM())) AS cost_of_goods_usd,
    sale_price_usd * (0.8 + UNIFORM(0, 0.4, RANDOM())) AS sale_price_usd,
    menu_item_health_metrics_obj
  FROM menu_raw
  WHERE menu_item_id IS NOT NULL
  ORDER BY RANDOM()
  LIMIT :num_rows;

  -- Capture count after insert
  SELECT COUNT(*) INTO :items_after FROM menu_raw;

  items_inserted := :items_after - :items_before;

  RETURN 'Successfully inserted ' || items_inserted::STRING || ' new menu items. Total items: ' || items_after::STRING;
END;
$$;
```

### Generate Test Data and Trigger Refresh

```sql
-- Example: Generate and insert 100 new menu items
CALL generate_menu_items(100);

-- Verify new rows were added
SELECT COUNT(*) AS total_rows FROM menu_raw;
```

### Manual Refresh of Dynamic Tables

To observe incremental refresh now — rather than wait on the scheduled refresh — we manually refresh the dynamic tables. Snowflake will automatically detect changes and perform an incremental refresh when possible.

```sql
-- Refresh the menu_profitability dynamic table
ALTER DYNAMIC TABLE menu_profitability REFRESH;
```

### Verify Incremental Refresh

Query the refresh history to verify that incremental refresh was used. The `refresh_action` column will show 'INCREMENTAL' for incremental refreshes and 'FULL' for full table refreshes.

```sql
-- Check refresh history for menu_profitability
SELECT
  name,
  refresh_action,  -- Look for 'INCREMENTAL' vs 'FULL'
  state,
  refresh_start_time,
  refresh_end_time,
  DATEDIFF('second', refresh_start_time, refresh_end_time) AS duration_seconds
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
WHERE name = 'MENU_PROFITABILITY'
ORDER BY refresh_start_time DESC
LIMIT 5;
```

```sql
-- View refresh history for all dynamic tables
SELECT
  name,
  refresh_action,
  state,
  refresh_start_time,
  refresh_end_time,
  DATEDIFF('second', refresh_start_time, refresh_end_time) AS duration_seconds
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY())
ORDER BY refresh_start_time DESC
LIMIT 10;
```

---

## Materialized View Migration

A Materialized View stores the results of a query physically, similar to a table. Unlike regular views (which execute the query each time), materialized views pre-compute and store the results for faster query performance.

Converting a Materialized View to a Dynamic Table provides several benefits:

**Materialized Views:**
- Background refresh — no control over timing
- No incremental refresh capability
- Cannot chain dependencies (one materialized view cannot read from another materialized view)

**Dynamic Tables:**
- Declarative refresh with TARGET_LAG — you control data freshness
- Automatic incremental refresh when possible
- Can chain transformations (DT can read from another DT)
- Integrated dependency management

### Migration Pattern

To migrate, simply change the DDL header. The rest of the query stays identical:

```sql
-- Materialized View:
CREATE OR REPLACE MATERIALIZED VIEW menu_summary_mv AS
SELECT ...
```

```sql
-- Becomes:
CREATE OR REPLACE DYNAMIC TABLE menu_summary_dt
  TARGET_LAG = '1 hour'  -- Control refresh timing
  WAREHOUSE = COMPUTE_WH -- Specify compute
AS
SELECT ... -- Same query!
```

**Summary of migration steps:**
1. Create a dynamic table with the same query
2. Add TARGET_LAG and WAREHOUSE parameters
3. Optionally specify REFRESH_MODE
4. Test the new dynamic table to ensure it behaves as expected
5. Drop the materialized view if no longer needed

### Example: Create a Materialized View

```sql
-- Create a materialized view showing menu summary by brand and category
CREATE OR REPLACE MATERIALIZED VIEW menu_summary_mv
AS
SELECT
  truck_brand_name,
  menu_type,
  item_category,

  -- Aggregated metrics
  COUNT(*) AS item_count,
  ROUND(AVG(cost_of_goods_usd), 2) AS avg_cost_usd,
  ROUND(AVG(sale_price_usd), 2) AS avg_price_usd,
  ROUND(AVG(sale_price_usd - cost_of_goods_usd), 2) AS avg_profit_usd,
  ROUND(
    AVG(((sale_price_usd - cost_of_goods_usd) / NULLIF(sale_price_usd, 0)) * 100),
    2
  ) AS avg_margin_pct,
  MIN(sale_price_usd - cost_of_goods_usd) AS min_profit_usd,
  MAX(sale_price_usd - cost_of_goods_usd) AS max_profit_usd

FROM menu_raw
WHERE sale_price_usd IS NOT NULL
  AND cost_of_goods_usd IS NOT NULL
GROUP BY
  truck_brand_name,
  menu_type,
  item_category;

-- Query the materialized view
SELECT
  truck_brand_name,
  menu_type,
  item_category,
  item_count,
  avg_profit_usd,
  avg_margin_pct
FROM menu_summary_mv
ORDER BY avg_margin_pct DESC
LIMIT 10;
```

```sql
-- OPTIONAL: Drop the materialized view (if converting)
-- DROP MATERIALIZED VIEW IF EXISTS menu_summary_mv;
```

---

## CDC Comparison

This section demonstrates two approaches to propagating changes from a source table:

- **Approach A:** Traditional approach using Streams and Tasks
- **Approach B:** Modern approach using Dynamic Tables

### Approach A: Traditional CDC with Streams and Tasks

In this approach, we create a stream on a table, then process the stream using a task. We insert mock data into the table to populate the stream, which allows us to view tangible results after executing the task.

> **Note:** This stream only captures changes made to `menu_raw` AFTER the stream is created. The existing data in `menu_raw` (loaded earlier) will NOT appear in the stream. Therefore, `menu_profitability_cdc` will only contain rows from changes made after this point.

In production, you would typically:
1. Do an initial load to populate the target table with existing data
2. Create the stream
3. Let the task handle incremental changes going forward

#### Create Stream and Target Table

```sql
-- Create stream on source table
CREATE OR REPLACE STREAM menu_changes_stream
  ON TABLE menu_raw;

-- Target table with transformations applied
CREATE OR REPLACE TABLE menu_profitability_cdc
(
  menu_item_id NUMBER(38,0),
  menu_item_name VARCHAR,
  truck_brand_name VARCHAR,
  profit_usd NUMBER(38,4),
  profit_margin_pct NUMBER(38,2),
  updated_at TIMESTAMP_NTZ
);
```

#### Create Task to Process Stream

```sql
-- Task to process the stream and update the target table
CREATE OR REPLACE TASK update_menu_profitability
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = '3 HOURS'
WHEN
  SYSTEM$STREAM_HAS_DATA('menu_changes_stream')
AS
  MERGE INTO menu_profitability_cdc t
  USING (
    SELECT 
      menu_item_id,
      menu_item_name,
      truck_brand_name,
      sale_price_usd - cost_of_goods_usd AS profit_usd,
      ROUND(((sale_price_usd - cost_of_goods_usd) / NULLIF(sale_price_usd, 0)) * 100, 2) AS profit_margin_pct,
      METADATA$ACTION
    FROM menu_changes_stream
  ) s
  ON t.menu_item_id = s.menu_item_id
  WHEN MATCHED AND s.METADATA$ACTION = 'DELETE' THEN 
    DELETE
  WHEN MATCHED THEN 
    UPDATE SET
      t.menu_item_name = s.menu_item_name,
      t.truck_brand_name = s.truck_brand_name,
      t.profit_usd = s.profit_usd,
      t.profit_margin_pct = s.profit_margin_pct,
      t.updated_at = CURRENT_TIMESTAMP()
  WHEN NOT MATCHED THEN 
    INSERT (menu_item_id, menu_item_name, truck_brand_name, profit_usd, profit_margin_pct, updated_at)
    VALUES (s.menu_item_id, s.menu_item_name, s.truck_brand_name, s.profit_usd, s.profit_margin_pct, CURRENT_TIMESTAMP());
```

#### Initial Load and Execute Task

```sql
-- Insert initial data to populate target table
INSERT INTO menu_profitability_cdc
SELECT 
  menu_item_id, menu_item_name, truck_brand_name,
  sale_price_usd - cost_of_goods_usd AS profit_usd,
  ROUND(((sale_price_usd - cost_of_goods_usd) / NULLIF(sale_price_usd, 0)) * 100, 2) AS profit_margin_pct,
  CURRENT_TIMESTAMP() AS updated_at
FROM menu_raw
WHERE sale_price_usd IS NOT NULL AND cost_of_goods_usd IS NOT NULL;
```

```sql
-- Manually run the task to test
EXECUTE TASK update_menu_profitability;
```

```sql
-- Query the traditional CDC results
SELECT
  menu_item_id,
  menu_item_name,
  truck_brand_name,
  profit_usd,
  profit_margin_pct,
  updated_at
FROM menu_profitability_cdc
ORDER BY profit_margin_pct DESC
LIMIT 10;
```

### Approach B: CDC with Dynamic Tables

In this approach, we create a dynamic table with the same CDC logic. We get the same results, but use a declarative approach that requires management of fewer objects (one dynamic table, instead of streams and tasks).

**Dynamic tables simplify CDC by automatically:**
- Detecting changes in the source table
- Refreshing based on TARGET_LAG
- No manual stream/task management needed
- Same transformation logic with declarative syntax

```sql
-- Create dynamic table with same CDC logic
-- Same result, declarative approach
CREATE OR REPLACE DYNAMIC TABLE menu_profitability_dt
  TARGET_LAG = '3 HOURS'
  WAREHOUSE = COMPUTE_WH
AS
SELECT
  menu_item_id,
  menu_item_name,
  truck_brand_name,
  (sale_price_usd - cost_of_goods_usd) AS profit_usd,
  ROUND(((sale_price_usd - cost_of_goods_usd) / NULLIF(sale_price_usd, 0)) * 100, 2) AS profit_margin_pct
FROM menu_raw;
```

```sql
-- Query the dynamic table results
SELECT
  menu_item_id,
  menu_item_name,
  truck_brand_name,
  profit_usd,
  profit_margin_pct
FROM menu_profitability_dt
ORDER BY profit_margin_pct DESC
LIMIT 10;
```

### Comparison Summary

| Aspect | Streams + Tasks | Dynamic Tables |
|:-------|:----------------|:---------------|
| **Objects to manage** | Stream + Task + Target Table | Dynamic Table only |
| **Refresh control** | Task schedule + WHEN condition | TARGET_LAG parameter |
| **CDC logic** | Manual MERGE statement | Automatic |
| **Incremental processing** | Manual implementation | Automatic when possible |
| **Dependency management** | Manual task chaining | Automatic with DOWNSTREAM |

```sql
-- Suspend the task to stop running: be sure to run this!
ALTER TASK update_menu_profitability SUSPEND;
```

---

## Cleanup

Running the commands below will clean up your environment and drop the objects created in this guide.

```sql
-- =============================================================================
-- CLEANUP (Optional)
-- =============================================================================

DROP TASK IF EXISTS update_menu_profitability;
DROP STREAM IF EXISTS menu_changes_stream;
DROP TABLE IF EXISTS menu_profitability_cdc;

DROP DYNAMIC TABLE IF EXISTS menu_profitability_dt;

DROP PROCEDURE IF EXISTS generate_menu_items(INTEGER);
DROP DYNAMIC TABLE IF EXISTS menu_profitability;
DROP MATERIALIZED VIEW IF EXISTS menu_summary_mv;
DROP TABLE IF EXISTS menu_raw;
DROP STAGE IF EXISTS tasty_bytes_stage;
DROP FILE FORMAT IF EXISTS csv_ff;

-- Drop the user-specific schema (optional - uncomment if you want to remove the schema entirely)
-- DROP SCHEMA IF EXISTS IDENTIFIER($user_schema);
```

---

## Conclusion and Resources

In this guide, you learned how to:

1. **Create Dynamic Tables** with TARGET_LAG for automatic refresh
2. **Leverage incremental refresh** to process only changed rows
3. **Convert Materialized Views** to Dynamic Tables for better control
4. **Simplify CDC workflows** by replacing Streams + Tasks with Dynamic Tables
5. **Monitor refresh operations** using INFORMATION_SCHEMA

Dynamic Tables provide a declarative, low-maintenance approach to building data pipelines in Snowflake. For most CDC and transformation use cases, they offer a simpler alternative to the traditional Streams + Tasks pattern.

### Additional Resources

- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [Getting Started with Dynamic Tables](https://www.snowflake.com/en/developers/guides/getting-started-with-dynamic-tables/)
