author: Lucas Galan, Piotr Paczewski
id: getting-started-with-batch-cortex-search
language: en
summary: Learn to use Batch Cortex Search over a Cortex Search Service for processing large batches of queries
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis , snowflake-site:taxonomy/snowflake-feature/cortex-search
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Batch Cortex Search
<!-- ------------------------ -->
## Overview 

**Understand how and when to use Batch Cortex Search to tackle offline, high-throughput workloads over large sets of queries**

This guide walks you step-by-step through creating a **Cortex Search Service** and a query payload. We then run parallel queries on the service at scale, showing that for large numbers of queries, consecutive searches significantly increase the time taken. Finally, we use **Batch Cortex Search** to tackle the entire search in a matter of seconds. We also show how this solution can scale up to thousands of searches without significant impact on the time to process. 

At a high level:
-   A Cortex Search is for interactive, low latency user-facing search (RAG chatbots, search bars)
-   Batch Cortex Search is for offline, high-throughput workloads over large sets of queries (entity resolution, catalog mapping)
-   Both use the same underlying Cortex Search service and index, no need to create separate objects to use batch.

### What You'll Need

-   A Snowflake account
-   An ACCOUNTADMIN role or a custom role with sufficient privileges
-   A dataset to search through (we provide a step-by-step guide to using a free dataset from Snowflake marketplace)

### What You'll Learn

-   How to set up a **Cortex Search Service** over a marketplace dataset
-   How to run linear queries using Cortex Search Service
-   The limitations of running multiple queries over a Cortex Search Service
-   How to use **Batch Cortex Search** to tackle queries at scale

### What You'll Build

-   A marketplace integration to download wikipedia entries
-   A **Cortex Search Service** over a table of 100K articles
-   A simple synthetic query generator
-   A way to deploy **Batch Cortex Search** to quickly tackle large volumes of queries

<!-- ------------------------ -->
## What is Batch Cortex Search?

The Batch Cortex Search function is a table function that allows you to submit a batch of queries to a Cortex Search Service. It is intended for offline use-cases with high throughput requirements, such as entity resolution, deduplication, or clustering tasks.

Jobs submitted to a Cortex Search Service with the CORTEX_SEARCH_BATCH function leverage additional compute resources to provide a significantly higher level of throughput (queries per second) than the interactive (Python, REST, SEARCH_PREVIEW) API search query surfaces.

> **_NOTE:_** The throughput of the batch search function may vary depending on the amount of data indexed in the queried Cortex Search Service and the complexity of the search queries. 

> The throughput of the batch search function (the number of search queries processed per second) is not influenced by the size of the warehouse used to query it and there is no limit to the number of concurrent batch queries that can be run at a given time on a given service.  

<!-- ------------------------ -->
## Getting Data
> **_NOTE:_** Skip this if you have own data and prefer to use it for this demo instead of the marketplace data.  

For this tutorial, we will use a free dataset available on the **Snowflake Marketplace**. 

In your Snowsight account, navigate to the Marketplace and search for Wikipedia data. Click 'Get'.
![alt text](assets/marketplace_dataset.jpg)

You can also import the dataset programmatically, please note the Wikipedia global listing name (GZT0Z4C8RF3FT) might be subject to change in the future.

```sql
USE ROLE ACCOUNTADMIN;

CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZT0Z4C8RF3FT');
CREATE DATABASE IF NOT EXISTS AI_TRAINING_DATASET_FROM_WIKIPEDIA
FROM LISTING 'GZT0Z4C8RF3FT';
```

Let's begin by opening a SQL file in Snowflake workspace. Before we do anything else, let's set up our environment.
![alt text](assets/workspace_intro.png)

```sql
USE ROLE ACCOUNTADMIN;

-- Create database, schema and a warehouse
CREATE DATABASE IF NOT EXISTS BATCH_DEMO;
CREATE SCHEMA IF NOT EXISTS BATCH_TEST;
CREATE WAREHOUSE IF NOT EXISTS BATCH_SEARCH_WH WITH WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;

-- Set context
USE SCHEMA BATCH_DEMO.BATCH_TEST;
USE WAREHOUSE BATCH_SEARCH_WH;
```

Then, from the data we've downloaded, we want to build a smaller dataset, let's say 100K articles, to test the Batch Cortex Search against.

```sql
-- Create a table based on 100k articles from the source data
CREATE OR REPLACE TABLE wikipedia_articles AS
SELECT 
    URL,
    TITLE,
    RAW_TEXT,
    TABLE_OF_CONTENTS,
    SEE_ALSO
FROM AI_TRAINING_DATASET_FROM_WIKIPEDIA.PUBLIC.WIKIPEDIA
LIMIT 100000;
```
Feel free to take a look at the structure. You will see that there is a main column called RAW_TEXT which has the entire article in it.

```sql
-- Verify row count
SELECT COUNT(*) AS row_count FROM wikipedia_articles;

-- Preview sample data
SELECT TITLE, LEFT(RAW_TEXT, 200) AS text_preview 
FROM wikipedia_articles 
LIMIT 5;
```

<!-- ------------------------ -->
## Setting Up a Cortex Search Service
Now that we have data, we can set up a Cortex Search Service over the RAW_TEXT column. This will create a vector index over the column and allow for extremely fast retrieval over the unstructured text. The service takes a while to create the first time, but once it's been created, it is very fast to query.
> **_NOTE:_** This will take around 8 minutes. If you want something faster, simply reduce the table wikipedia_articles to a smaller amount of data, such as 50k. 

```sql
-- Create a Cortex Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE wikipedia_search_service
ON RAW_TEXT
ATTRIBUTES TITLE
WAREHOUSE = BATCH_SEARCH_WH
TARGET_LAG = '1 hour'
AS
SELECT 
    TITLE,
    RAW_TEXT
FROM wikipedia_articles;
```

Once the service has been created, we can test it. Run a quick search to verify it's working. We can now search for anything we'd like and return the pages (within our subset) that most closely match the results.

![alt text](assets/workspace_example.png)
```sql
-- Single search against the Cortex Search service
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{
        "query": "machine learning artificial intelligence",
         "columns": ["TITLE", "RAW_TEXT"],
        "limit": 5
    }'
) AS search_result;

-- A single result is a little hard to parse as JSON. We can wrap SEARCH_PREVIEW result into a table.
SELECT
    r.value:TITLE::VARCHAR AS title,
    r.value:RAW_TEXT::VARCHAR AS raw_text
FROM TABLE(FLATTEN(
    input => PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
            '{
                "query": "machine learning artificial intelligence",
                "columns": ["TITLE", "RAW_TEXT"],
                "limit": 5
            }'
        )
    ):results
)) AS r;
```

This type of search is extremely efficient, and Cortex Search can quickly return results even for extremely large datasets. It is even faster when used directly via Snowflake Python API or REST API, but for now let's look at the SQL for demonstration purposes. If we want to run multiple searches using SEARCH_PREVIEW function:

```sql
-- Example: 10 searches using UNION ALL via SEARCH_PREVIEW SQL function
SELECT 'quantum physics' AS query, PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "quantum physics", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR AS top_result
UNION ALL
SELECT 'world war history', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "world war history", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'climate change', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "climate change", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'solar system', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "solar system", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'ancient rome', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "ancient rome", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'machine learning', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "machine learning", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'french revolution', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "french revolution", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'deep ocean', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "deep ocean", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'renewable energy', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "renewable energy", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'human brain', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "human brain", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR;
```

The query starts to take longer and longer. So how can we leverage the power of the Cortex Search Service over multiple search queries?

<!-- ------------------------ -->
## Batch Cortex Search to the Rescue
Batch Cortex Search allows us to do just this, it's clean, elegant and easy to deploy. It allows us to submit a larger number of searches and execute them as a batch. First, let's create a table with the previous searches in it. 

```sql
-- First, create a table with our 10 search terms
CREATE OR REPLACE TABLE ten_searches (query_text VARCHAR);
INSERT INTO ten_searches VALUES 
    ('quantum physics'),
    ('world war history'),
    ('climate change'),
    ('solar system'),
    ('ancient rome'),
    ('machine learning'),
    ('french revolution'),
    ('deep ocean'),
    ('renewable energy'),
    ('human brain');
```

Then, we run Batch Cortex Search over the table. You can see this is significantly simpler to execute. 

> **_TIP:_** The throughput of `CORTEX_SEARCH_BATCH` is not influenced by the size of the warehouse used to query it. A small warehouse works just as well as a large one for batch search operations.

```sql
-- Now batch search all 10 in ONE call
SELECT
    q.query_text,
    s.TITLE AS matched_title
FROM ten_searches AS q,
LATERAL CORTEX_SEARCH_BATCH(
    service_name => 'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    query => q.query_text,
    columns => ['TITLE', 'RAW_TEXT'],
    limit => 1
) AS s;
```

That's it! And this is just the tip of the iceberg — we can run 1000 searches with virtually no impact on the query execution time!

```sql
-- Create a table of 1000 diverse search queries from Wikipedia titles
CREATE OR REPLACE TABLE thousand_searches AS
SELECT DISTINCT TITLE AS query_text
FROM wikipedia_articles
ORDER BY RANDOM()
LIMIT 1000;

-- Verify
SELECT COUNT(*) AS total_queries FROM thousand_searches;

-- Run batch search on all 1000 queries (returns up to 5000 results: 1000 queries x 5 results each)
SELECT
    q.query_text,
    s.TITLE AS matched_title,
    s.METADATA$RANK AS rank
FROM thousand_searches AS q,
LATERAL CORTEX_SEARCH_BATCH(
    service_name => 'BATCH_DEMO.BATCH_TEST.WIKIPEDIA_SEARCH_SERVICE',
    query => q.query_text,
    columns => ['TITLE', 'RAW_TEXT'],
    limit => 5
) AS s;
```

Batch Cortex Search is easy to implement, but extremely powerful. 

> **_TIP:_** You can run interactive and batch queries concurrently on the same Cortex Search Service without any degradation to interactive query performance. Separate compute resources are used to serve each type.

<!-- ------------------------ -->
## Cleanup
Now that you know how to use Batch Cortex Search, let's clean up the environment.

```sql
-- Set context
USE ROLE ACCOUNTADMIN;

-- Drop database
DROP DATABASE IF EXISTS BATCH_DEMO;

-- Drop warehouse 
DROP WAREHOUSE IF EXISTS BATCH_SEARCH_WH;

-- Unsubscribe from the Wikipedia Marketplace listing
DROP DATABASE IF EXISTS AI_TRAINING_DATASET_FROM_WIKIPEDIA;
```

<!-- ------------------------ -->
## Conclusion And Resources

### What You Learned

- How to create a **Cortex Search Service** over a Snowflake Marketplace dataset
- How to use **Batch Cortex Search** (`CORTEX_SEARCH_BATCH`) to process large volumes of queries efficiently
- That batch search scales to thousands of queries with minimal impact on processing time

### Related Resources

- [Cortex Search Reference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Batch Cortex Search Reference](https://docs.snowflake.com/en/LIMITEDACCESS/cortex-search/batch-cortex-search)