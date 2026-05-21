author: Jacob Prall
id: agentic-etl-best-practices
language: en
summary: Learn best practices for building production-ready ETL pipelines with Cortex Code, Snowflake's AI coding agent, using natural language prompts for ingestion, transformation, orchestration, and monitoring.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
status: Published

# Agentic ETL Best Practices with Cortex Code

## Build Production-Ready Data Pipelines with Natural Language

Snowflake is now an agentic-first data engineering platform. With Cortex Code, Snowflake's native AI coding agent, data engineering teams can build, debug, and optimize production-ready ETL pipelines using plain language prompts, all from the CLI or Snowsight. Instead of hand-coding every stage of your pipeline, you describe what you want and Cortex Code generates the DDL, transformation logic, orchestration, and monitoring infrastructure.

## Get Started with Cortex Code

### Step 1: Ensure Cortex Code is enabled with appropriate permissions on your account

**In Snowsight**

Cortex Code is built directly into Snowsight, Snowflake's web UI. No installation required \-- open Workspaces in Snowsight and start a Cortex Code session to generate fully functional ETL pipelines that run directly inside Snowflake.

Try Cortex Code today in Snowsight with a [30-day free trial](https://app.snowflake.com).

**In CLI**

To use Cortex Code from your terminal, VS Code, or Cursor, install the CLI:

```shell
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

For more details see the [Cortex Code CLI documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli). You can also try the CLI with a [30-day Cortex Code CLI trial](https://signup.snowflake.com).

## Terminology

**Dynamic Tables**: A declarative way to define data transformations. You write a SELECT statement describing the desired result, and Snowflake automatically handles refresh scheduling, dependency management, and incremental processing.

**TARGET\_LAG**: The maximum acceptable delay between when source data changes and when a Dynamic Table reflects those changes. For example, `TARGET_LAG = '12 hours'` means the table refreshes within 12 hours of source changes.

**Streams**: Change tracking objects that record DML changes (inserts, updates, deletes) to a table. Streams enable "exactly once" semantics for processing new or changed data.

**Tasks**: Scheduled or event-driven objects that execute a single SQL statement or stored procedure. Tasks can be organized into DAGs (Directed Acyclic Graphs) for multi-step pipeline orchestration.

**Task Graphs (DAGs)**: A series of tasks composed of a root task and child tasks, organized by dependencies. Task graphs flow in a single direction. A downstream task won't run until all its upstream dependencies complete.

**Snowpipe / Snowpipe Streaming**: Automated data ingestion services. Snowpipe loads data from files in stages as they arrive. Snowpipe Streaming enables real-time row-level ingestion via SDK or Kafka connector.

**COPY INTO**: The SQL command for bulk-loading data from staged files (S3, Azure Blob, GCS, or internal stages) into Snowflake tables.

**I-T-D Framework**: Ingestion-Transformation-Delivery, a common framework for structuring end-to-end data pipelines in Snowflake.

## Best Practices

### General Cortex Code Best Practices

Always ensure you're on the latest CLI version. Run `cortex --version` and update with `cortex update` if needed.

Use plain language. Describe what you want, not how to do it. Cortex Code understands intent; you don't need to write SQL to get started.

Front-load context, focus each turn on a single goal. Give Cortex Code comprehensive background upfront (source systems, table names, data volumes, freshness requirements), but limit each prompt to one primary objective.

Build iteratively. Start small, refine often. Build one pipeline stage at a time, validate it, then use follow-up prompts to extend. Avoid combining ingestion, transformation, and orchestration in a single prompt.

Use `/plan` for complex tasks. Before starting a multi-step pipeline, ask Cortex Code to lay out its full approach so you can review the DDL and orchestration logic before any objects are created.

Reiterate critical information in long conversations. The agent focuses on your initial request and the most recent turn. Remind it of target schemas, warehouse names, and freshness SLAs as the conversation progresses.

Review before accepting. Especially DDL/DML operations, warehouse provisioning, and role grants. If unsure, ask: "Why are you creating this object?" or "What will this DDL change?"

### ETL-Specific Best Practices

Always specify source and target schemas explicitly. Cortex Code performs better when it knows exactly where data lives and where results should land.

**Do:**

"Load CSV files from @RAW\_DATA.PUBLIC.S3\_STAGE into RAW\_DATA.STAGING.ORDERS. The files have headers, use comma delimiters, and the timestamp column is in ISO 8601 format."

**Don't:**

"Load data from the stage into a table."

Define idempotency requirements upfront. Tell Cortex Code whether your pipeline should handle re-runs gracefully, and whether you need MERGE logic or simple INSERT/overwrite patterns.

**Do:**

"Build a MERGE statement that upserts from STAGING.RAW\_ORDERS into ANALYTICS.DIM\_CUSTOMER using CUSTOMER\_ID as the match key. On match, update EMAIL and PHONE. On no match, insert the full row."

**Don't:**

"Move data from staging to analytics."

Include data volume and freshness SLAs in your prompts. This helps Cortex Code choose appropriate warehouse sizes, refresh intervals, and ingestion strategies.

**Do:**

"We receive \~500K new order rows per hour. The analytics team needs data fresh within 30 minutes. Recommend a Dynamic Table pipeline with appropriate TARGET\_LAG settings."

**Don't:**

"Make a pipeline for order data."

Validate on a small sample before scaling. Before running a full pipeline, use `TABLESAMPLE` or `LIMIT` to confirm the workflow runs end-to-end. Subtle issues like column-type mismatches or missing file format settings only surface at execution time.

Review schema changes and privilege grants carefully. ETL pipelines often need CREATE TABLE, CREATE STAGE, and GRANT privileges. Verify each DDL operation before accepting.

## Ingest Data from External Sources

Data ingestion is where every pipeline starts, and where the most tedious boilerplate lives \-- file format definitions, stage configuration, COPY INTO options, error handling. Cortex Code handles all of it from a single prompt and can recommend the right ingestion pattern (batch via COPY INTO, continuous via Snowpipe, or real-time via Snowpipe Streaming) based on your requirements.

```
I have CSV order data landing in s3://acme-data-lake/orders/ every 15 minutes.
Files have headers, use pipe delimiters, and some fields are double-quoted. 
Timestamps are in 'YYYY-MM-DD HH24:MI:SS' format. Create a file format, 
external stage, and COPY INTO statement to load into RAW.PUBLIC.ORDERS 
(order_id NUMBER, customer_id NUMBER, order_ts TIMESTAMP_NTZ, amount NUMBER(12,2), 
status VARCHAR). Skip any rows that fail to parse and log them.
```

Once your batch ingestion is working, extend to continuous loading:

```
Convert this batch COPY INTO pipeline to use Snowpipe for continuous ingestion. 
Configure auto-ingest from the S3 stage using SQS notifications. Show me 
the pipe definition and the S3 event notification configuration I need.
```

For real-time use cases, switch to streaming:

```
We also need real-time order status updates from Kafka. Set up a Snowpipe 
Streaming ingestion from our MSK cluster into RAW.PUBLIC.ORDER_STATUS_EVENTS 
using the Snowflake Kafka connector. The topic is 'order-status-updates' and 
messages are JSON with fields: order_id, new_status, updated_at.
```

## Transform and Model Data

Transformation is where raw data becomes useful \-- cleaning, enriching, joining, and aggregating into models that analysts and ML pipelines can consume. Cortex Code can generate multi-tier Dynamic Table pipelines that automatically handle incremental refresh, dependency management, and optimization.

```
Build a three-tier Dynamic Table pipeline in the ANALYTICS schema:

Tier 1 (enriched): Create ORDERS_ENRICHED from RAW.PUBLIC.ORDERS that adds 
day_of_week, order_hour, and a discount_flag based on whether amount > 100. 
Filter out rows where order_id IS NULL. Set TARGET_LAG = '1 hour'.

Tier 2 (fact): Create ORDER_FACT that joins ORDERS_ENRICHED with 
RAW.PUBLIC.CUSTOMERS on customer_id, adding customer_name, segment, and region. 
Set TARGET_LAG = DOWNSTREAM.

Tier 3 (metrics): Create DAILY_ORDER_METRICS that aggregates ORDER_FACT by 
order_date with total_orders, total_revenue, avg_order_value, and 
unique_customers. Set TARGET_LAG = DOWNSTREAM.
```

Iterate on the transformation logic:

```
Add a profit calculation to ORDER_FACT. Join with RAW.PUBLIC.PRODUCTS on 
product_id to get cost_of_goods, then compute unit_profit and profit_margin_pct. 
Also add a has_discount boolean flag.
```

```
The DAILY_ORDER_METRICS table needs a segment breakdown. Add a second 
aggregation table, DAILY_SEGMENT_METRICS, grouped by order_date and 
customer_segment with the same metrics plus segment_revenue_share as a 
percentage of that day's total.
```

For teams that prefer procedural transformation logic over declarative Dynamic Tables:

```
Build a stored procedure SP_TRANSFORM_ORDERS in ANALYTICS that reads from a 
Stream on RAW.PUBLIC.ORDERS, applies the same enrichment logic (day_of_week, 
order_hour, discount_flag), and MERGEs results into ANALYTICS.ORDERS_ENRICHED 
using order_id as the key. Include error handling that logs failures to 
ANALYTICS.PIPELINE_ERRORS.
```

## Orchestrate Pipelines

A transformation is only useful if it runs reliably on schedule. Snowflake offers two orchestration models: declarative (Dynamic Tables handle their own refresh) and procedural (Tasks and Task Graphs for explicit control). Cortex Code can set up either pattern and wire the dependencies.

If you used Dynamic Tables above, your orchestration is already built in. But you can still add monitoring:

```
Show me how to monitor the Dynamic Table pipeline I just created. I want to 
see refresh history, check for failed refreshes, and understand the dependency 
graph between ORDERS_ENRICHED, ORDER_FACT, and DAILY_ORDER_METRICS.
```

For procedural pipelines using Tasks:

```
Create a Task Graph (DAG) for the following pipeline:

Root task: TASK_INGEST_ORDERS runs every 15 minutes using warehouse ETL_WH_XS. 
It calls SP_INGEST_ORDERS to COPY INTO from the stage.

Child task: TASK_TRANSFORM_ORDERS depends on TASK_INGEST_ORDERS. It only runs 
when the Stream on RAW.PUBLIC.ORDERS has data (SYSTEM$STREAM_HAS_DATA). 
It calls SP_TRANSFORM_ORDERS.

Child task: TASK_AGGREGATE_METRICS depends on TASK_TRANSFORM_ORDERS. It calls 
SP_AGGREGATE_DAILY_METRICS.

Finalizer task: TASK_PIPELINE_COMPLETE runs after all tasks finish (success or 
failure) and logs the run status to ANALYTICS.PIPELINE_RUNS.

Enable the task graph and show me how to monitor it in Snowsight.
```

Extend with error handling:

```
Add retry logic to TASK_TRANSFORM_ORDERS -- retry up to 3 times with a 
60-second delay between attempts. If all retries fail, the finalizer should 
log the error with the failed task name and error message.
```

```
Add a conditional task TASK_ALERT_ON_FAILURE that only runs if any upstream 
task failed. It should call a stored procedure that sends a notification to 
our alert system with the pipeline name, failed task, and error details.
```

## Monitor and Validate Data Quality

A pipeline isn't done when data arrives in the target table. You need to know the data is correct, fresh, and complete. Cortex Code can generate monitoring queries, data quality checks, and alerting infrastructure.

```
Create a data quality validation framework for the ANALYTICS schema:

1. A stored procedure SP_VALIDATE_ORDERS that checks:
   - No NULL order_ids in ORDERS_ENRICHED
   - All amounts are positive
   - order_ts is not in the future
   - Row count increased since last run (no data loss)

2. A monitoring table DQ_CHECK_RESULTS that logs each check run with 
   check_name, status (PASS/FAIL), details, and run_timestamp.

3. A Task TASK_VALIDATE_ORDERS that runs after TASK_TRANSFORM_ORDERS 
   and calls the validation procedure.
```

Build on the monitoring:

```
Add a freshness monitor. Create a Dynamic Table PIPELINE_FRESHNESS that 
tracks the MAX(order_ts) in ORDERS_ENRICHED and computes the lag in minutes 
from CURRENT_TIMESTAMP(). If lag exceeds 60 minutes, flag it.
```

```
Show me a query to check the refresh history of all my Dynamic Tables in 
the ANALYTICS schema, including last refresh time, duration, rows processed, 
and whether it was incremental or full.
```

## Debug and Optimize Performance

When pipelines slow down or break, you need to diagnose quickly. Cortex Code can help you analyze query profiles, identify bottlenecks, and recommend optimizations.

```
My TASK_TRANSFORM_ORDERS is running slower than expected -- it's taking 
12 minutes to process 500K rows on an XS warehouse. The stored procedure 
reads from the Stream on RAW.PUBLIC.ORDERS and MERGEs into ORDERS_ENRICHED. 
Help me diagnose the issue. Check the query profile and suggest optimizations.
```

Iterate on the diagnosis:

```
You found that the MERGE is doing a full scan on the target table. 
Recommend a clustering strategy for ORDERS_ENRICHED and show me how to 
add a cluster key on order_date to improve MERGE performance.
```

```
The XS warehouse might be too small for our data volume. Compare the cost 
and performance tradeoff of running on XS for 12 minutes vs. S for 4 minutes 
vs. M for 90 seconds. Which is most cost-effective?
```

For Dynamic Table optimization:

```
One of my Dynamic Tables is doing full refreshes instead of incremental. 
Show me how to check the refresh mode using INFORMATION_SCHEMA and explain 
what SQL patterns prevent incremental refresh. Suggest how to rewrite the 
query to enable incremental mode.
```

## Conclusion and Resources

The key to success with agentic ETL in Snowflake is to start with a focused stage of your pipeline, validate it works end-to-end, then let Cortex Code handle the boilerplate while you apply your data engineering expertise on the modeling and reliability decisions that matter. Use the Ingestion-Transformation-Delivery framework to structure your approach, lean on Dynamic Tables for declarative pipelines, and use Tasks and Task Graphs when you need explicit orchestration control.

- [Snowflake Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)  
- [Snowflake Streams Documentation](https://docs.snowflake.com/en/user-guide/streams-intro)  
- [Snowflake Tasks Documentation](https://docs.snowflake.com/en/user-guide/tasks-intro)  
- [Snowpipe Streaming Documentation](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/data-load-snowpipe-streaming-overview)  
- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)  
- [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)  
- [Start your 30-day Cortex Code trial in Snowsight](https://signup.snowflake.com/cortex-code)  
- [Getting Started with Dynamic Tables](https://www.snowflake.com/en/developers/guides/comprehensive-guide-to-dynamic-tables/)  
- [Getting Started with Streams & Tasks](https://www.snowflake.com/en/developers/guides/getting-started-with-streams-and-tasks/)  
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)
