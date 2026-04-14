author: Jacob Prall
id: agentic-snowpark-best-practices
language: en
summary: Learn best practices for writing production-grade Snowpark Python with Cortex Code, Snowflake's AI coding agent, using natural language prompts for transformations, UDFs, stored procedures, and performance optimization.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
status: Published

# Agentic Snowpark Data Engineering Best Practices with Cortex Code

## Write Production-Grade Snowpark Python Without the Boilerplate

Snowpark Python gives data engineers the full power of Python's ecosystem running directly on Snowflake's compute, with all the security and scalability benefits that come with it. But writing production-grade Snowpark code still involves a lot of scaffolding: session management, DataFrame API chains, UDF registration, package dependency declarations, error handling patterns, and warehouse optimization.

Cortex Code eliminates that scaffolding. As Snowflake's native AI coding agent, it generates idiomatic Snowpark Python from natural language descriptions, handles the API nuances for you, and produces code that pushes computation down to Snowflake rather than pulling data client-side. Whether you're building transformation logic with the DataFrame API, packaging reusable functions as UDFs, or orchestrating multi-step pipelines as stored procedures, Cortex Code gets you to working code faster.

All of the Snowpark workflows in this guide are powered by the `$data-engineering` skill in Cortex Code.

## Get Started with Cortex Code

### Step 1: Ensure Cortex Code is enabled with appropriate permissions on your account

**In Snowsight**

Cortex Code is built directly into Snowsight, Snowflake's web UI. No installation required \-- open Workspaces in Snowsight and start a Cortex Code session to generate Snowpark Python code that runs directly in Snowflake Notebooks.

Try Cortex Code today in Snowsight with a [30-day free trial](https://app.snowflake.com).

**In CLI**

To use Cortex Code from your terminal, VS Code, or Cursor, install the CLI:

```shell
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh
```

For more details see the [Cortex Code CLI documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli). You can also try the CLI with a [30-day Cortex Code CLI trial](https://signup.snowflake.com).

## Terminology

**Snowpark**: The set of libraries and runtimes that let you run Python, Java, or Scala code directly on Snowflake's compute infrastructure. Snowpark pushes computation to the data rather than pulling data to the client.

**DataFrame API**: Snowpark's primary interface for data manipulation, similar to pandas or PySpark DataFrames, but operations are lazily evaluated and pushed down as SQL to Snowflake's engine.

**User-Defined Functions (UDFs)**: Custom functions written in Python that run server-side in Snowflake. UDFs process data row-by-row or in vectorized batches and can be called from SQL or Snowpark code.

**Vectorized UDFs**: UDFs that receive batches of input rows as pandas DataFrames/Series instead of individual rows. Vectorized UDFs can improve numerical computations by 30-40% compared to scalar UDFs.

**User-Defined Table Functions (UDTFs)**: Functions that return tabular results, ie multiple rows and columns from each input. Useful for exploding, pivoting, or generating data.

**Stored Procedures**: Named, reusable Snowpark Python programs that run server-side. Unlike UDFs (which operate on rows), stored procedures orchestrate multi-step operations like ETL workflows, administrative tasks, or data quality checks.

**Snowpark-Optimized Warehouses**: Warehouse configurations with extra memory per node, designed for memory-intensive operations like large UDFs, ML training, or complex DataFrame operations.

**pandas on Snowflake (Modin)**: A compatibility layer that lets you write pandas code that executes in a distributed fashion on Snowflake's engine. Change the import statement and your pandas code scales without rewriting.

## Best Practices

### General Cortex Code Best Practices

Always ensure you're on the latest CLI version. Run `cortex --version` and update with `cortex update` if needed.

Use plain language. Describe what you want, not how to do it. You don't need to know the exact DataFrame API methods; Cortex Code will find the right ones.

Front-load context, focus each turn on a single goal. Give Cortex Code your table schemas, data types, and expected volumes upfront, then focus each prompt on one transformation or function.

Build iteratively. One function or transformation at a time. Get each piece working before composing them into a larger pipeline.

Use `/plan` for complex tasks. Before building a multi-step stored procedure, ask Cortex Code to outline its approach.

Review before accepting. Always review generated Snowpark code to ensure it uses pushdown operations (DataFrame API) rather than pulling data client-side (`.to_pandas()`).

### Snowpark-Specific Best Practices

Prefer the DataFrame API over pandas for transformations. Snowpark DataFrames push computation to Snowflake's engine and scale with your warehouse. Pandas DataFrames pull data to a single node and fail on large datasets. Snowpark DataFrames are \~8x faster than pandas for equivalent operations.

**Do:**

"Write a Snowpark DataFrame transformation that reads from RAW.ORDERS, filters rows where status \= 'COMPLETED', joins with RAW.CUSTOMERS on customer\_id, groups by region, and computes total\_revenue and order\_count. Write results to ANALYTICS.REGIONAL\_METRICS."

**Don't:**

"Read the orders table into pandas, filter it, and save it back."

Include table schemas and column types when asking for transformation code. This helps Cortex Code generate type-safe code and avoids runtime casting errors.

**Do:**

"RAW.ORDERS has columns: order\_id (NUMBER), customer\_id (NUMBER), order\_ts (TIMESTAMP\_NTZ), amount (NUMBER(12,2)), status (VARCHAR). Build a Snowpark transformation that..."

**Don't:**

"Transform the orders table."

Specify Python package dependencies explicitly. When creating UDFs or stored procedures that use third-party libraries, tell Cortex Code which packages are needed so it generates the correct `packages` clause.

Ask for error handling and logging upfront. Don't bolt them on later. Tell Cortex Code you want try/except blocks, logging to a pipeline\_errors table, and meaningful error messages from the start.

Use vectorized UDFs for numerical computations. If you're applying a mathematical function to every row, vectorized UDFs (batch API) process data as pandas Series and are 30-40% faster than scalar UDFs.

Avoid `.collect()` and `.to_pandas()` in production pipelines. These methods pull all data to the client and break at scale. Use `.write.save_as_table()` or `.create_or_replace_view()` to keep results in Snowflake.

## Build DataFrame Transformations

The DataFrame API is the core of Snowpark Python. It's how you express transformation logic that Snowflake executes at scale. Cortex Code generates idiomatic DataFrame chains that push all computation down to the engine, avoiding the common pitfall of pulling data client-side.

```
Write a Snowpark Python transformation in a Snowflake Notebook that:
1. Reads RAW.PUBLIC.ORDERS (order_id NUMBER, customer_id NUMBER, 
   order_ts TIMESTAMP_NTZ, amount NUMBER(12,2), product_id NUMBER, status VARCHAR)
2. Filters to status = 'COMPLETED' and amount > 0
3. Adds columns: order_date (DATE from order_ts), day_of_week (DAYOFWEEK), 
   order_hour (HOUR), and is_weekend (boolean: Saturday or Sunday)
4. Joins with RAW.PUBLIC.CUSTOMERS (customer_id NUMBER, name VARCHAR, 
   segment VARCHAR, region VARCHAR) on customer_id
5. Writes the result to ANALYTICS.PUBLIC.ORDERS_ENRICHED
Use DataFrame API operations -- do not use .to_pandas() or raw SQL strings.
```

Refine the transformation:

```
Add a running total column: for each customer, compute their cumulative 
spend over the last 90 days using a window function. The column should be 
called customer_90d_spend. Use Snowpark's Window functions, not pandas.
```

```
The join is dropping rows where customer_id doesn't exist in the CUSTOMERS 
table. Change it to a left outer join and fill missing customer fields with 
'Unknown' for name and segment, 'Unassigned' for region.
```

## Create Reusable UDFs and UDTFs

When you have transformation logic that needs to be reused across multiple pipelines or called from SQL, package it as a UDF. Cortex Code handles the registration boilerplate, package declarations, and input/output type specifications.

```
Create a vectorized UDF called CALCULATE_DISCOUNT_TIER that takes an 
order_amount (FLOAT) and a customer_segment (VARCHAR) and returns a 
discount_pct (FLOAT). The logic:
- 'Enterprise' customers: 15% if amount > 10000, 10% if > 5000, 5% otherwise
- 'Mid-Market': 10% if amount > 10000, 5% if > 5000, 0% otherwise  
- All others: 5% if amount > 10000, 0% otherwise
Register it as a permanent UDF in ANALYTICS.PUBLIC. Use the vectorized 
(batch) API with pandas Series for performance.
```

Extend with a table function:

```
Create a UDTF called PARSE_ORDER_TAGS that takes a JSON string column 
(tags VARCHAR) and returns a table with two columns: tag_name (VARCHAR) 
and tag_value (VARCHAR). The JSON contains an array of objects like 
[{"name": "priority", "value": "high"}, {"name": "source", "value": "web"}].
Use Python's json module. Register in ANALYTICS.PUBLIC.
```

Compose UDFs into queries:

```
Show me how to use CALCULATE_DISCOUNT_TIER and PARSE_ORDER_TAGS together 
in a single Snowpark DataFrame pipeline that reads ORDERS_ENRICHED, 
applies the discount tier, explodes the tags, and writes to 
ANALYTICS.PUBLIC.ORDERS_WITH_DISCOUNTS_AND_TAGS.
```

## Build Stored Procedures for Multi-Step Pipelines

Stored procedures are where individual transformations become orchestrated pipelines. They run server-side, can call other procedures, execute DDL, and handle errors. Cortex Code generates procedures with proper session management, error handling, and logging.

```
Create a stored procedure SP_DAILY_ORDER_PIPELINE in ANALYTICS.PUBLIC that:

1. Reads new rows from a Stream on RAW.PUBLIC.ORDERS 
   (check SYSTEM$STREAM_HAS_DATA first; return early if no new data)
2. Applies the enrichment logic: add order_date, day_of_week, order_hour, 
   is_weekend. Join with CUSTOMERS for segment and region.
3. MERGEs enriched rows into ANALYTICS.PUBLIC.ORDERS_ENRICHED using 
   order_id as the match key
4. Aggregates into ANALYTICS.PUBLIC.DAILY_METRICS: total_orders, 
   total_revenue, avg_order_value, unique_customers by order_date
5. Logs each step's row count and duration to ANALYTICS.PUBLIC.PIPELINE_LOG
6. Wraps everything in try/except -- on failure, logs the error with 
   traceback to PIPELINE_LOG and re-raises

Use Snowpark Python. Specify packages=['snowflake-snowpark-python']. 
The procedure should run on warehouse ETL_WH_S.
```

Iterate on robustness:

```
Add input validation to SP_DAILY_ORDER_PIPELINE. Before processing, 
check that RAW.PUBLIC.ORDERS has the expected columns and types. If the 
schema has changed, log a SCHEMA_MISMATCH error and abort without 
processing any data.
```

```
Add a MERGE deduplication step. If the Stream contains duplicate order_ids 
(from upstream retries), deduplicate by keeping the row with the latest 
order_ts before merging into ORDERS_ENRICHED.
```

## Optimize Snowpark Performance

Snowpark code that works on small datasets can fail or crawl at production scale. The key performance levers are: keep computation in Snowflake (DataFrame API over pandas), use vectorized UDFs for row-level operations, choose the right warehouse size, and understand when to use Snowpark-optimized warehouses.

```
I have a Snowpark stored procedure that processes 50M rows from 
RAW.PUBLIC.EVENTS. It currently:
1. Reads the table into a DataFrame
2. Calls .to_pandas() to apply a Python function row-by-row
3. Converts back to a Snowpark DataFrame and writes to a table

This takes 45 minutes on an M warehouse. Rewrite it to use only 
DataFrame API operations and vectorized UDFs so all computation stays 
in Snowflake. The Python function calculates a risk_score based on 
event_type, amount, and time_since_last_event.
```

Diagnose performance issues:

```
My DataFrame transformation chains 8 joins and 12 column expressions 
before writing to a table. It generates a massive SQL query that takes 
20 minutes. Should I break this into intermediate tables or temp tables? 
Show me how to use .cache_result() or write intermediate DataFrames to 
temp tables to let the optimizer work on smaller query plans.
```

```
When should I use a Snowpark-optimized warehouse vs. a standard warehouse?
My stored procedure creates a large UDF that loads a 2GB lookup dictionary 
into memory. It fails with OOM on a standard Large warehouse. Would a 
Snowpark-optimized warehouse help, and what size should I use?
```

## Test and Debug Snowpark Code

Production Snowpark pipelines need testing \-- unit tests for UDFs, integration tests for stored procedures, and debugging tools for when things break. Cortex Code can generate test harnesses and help you trace issues.

```
Generate unit tests for the CALCULATE_DISCOUNT_TIER UDF. Test all 
segment/amount combinations including edge cases:
- Boundary values (exactly 5000, exactly 10000)
- NULL inputs  
- Unknown segment values
- Negative amounts
Use Python's pytest framework. The tests should run in a Snowflake Notebook 
by calling the UDF on a small test DataFrame.
```

Debug runtime errors:

```
My stored procedure SP_DAILY_ORDER_PIPELINE fails with: 
"SnowparkSQLException: Column 'ORDER_DISCOUNT_AMOUNT' does not exist"
but the column exists in RAW.PUBLIC.ORDERS. The procedure was working 
yesterday. Help me debug: check if the column was renamed, if there's a 
case sensitivity issue, or if the Stream definition is stale.
```

```
Show me how to add structured logging to my stored procedure so I can 
trace exactly which step failed. Log to a table with columns: 
run_id, step_name, status, row_count, duration_seconds, error_message, 
and timestamp. Include a unique run_id per execution so I can trace 
end-to-end.
```

## Conclusion and Resources

The key to effective Snowpark development with Cortex Code is to think in DataFrames, not pandas, keep computation in Snowflake's engine, package reusable logic as UDFs, and orchestrate multi-step workflows as stored procedures. Start with a single transformation, validate it works, then build up. Use vectorized UDFs for row-level operations, avoid `.to_pandas()` in production, and let Cortex Code handle the registration boilerplate and API nuances while you focus on the business logic.

- [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)  
- [Snowpark Python DataFrame API Reference](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/dataframe)  
- [Creating UDFs in Python](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-creating)  
- [Creating Stored Procedures in Python](https://docs.snowflake.com/en/developer-guide/stored-procedure/python/procedure-python-overview)  
- [pandas on Snowflake (Modin)](https://docs.snowflake.com/en/developer-guide/snowpark/python/pandas-on-snowflake)  
- [Cortex Code Documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code)  
- [Cortex Code in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)  
- [Start your 30-day Cortex Code trial in Snowsight](https://signup.snowflake.com/cortex-code)  
- [Snowpark Python Performance Tips](https://www.snowflake.com/en/developers/guides/snowpark-python-top-three-tips-for-optimal-performance/)  
- [Intro to Data Engineering with Python](https://www.snowflake.com/en/developers/guides/data-engineering-with-snowpark-python-intro/)  
- [Best Practices for Cortex Code CLI](https://www.snowflake.com/en/developers/guides/best-practices-cortex-code-cli/)
