-- ============================================================================
-- Wikipedia Cortex Search Setup Script
-- Creates a 100K row sample and builds a Cortex Search service for batch testing
-- ============================================================================

-- ============================================================================
-- STEP 0: Environment setup
-- ============================================================================
USE ROLE ACCOUNTADMIN;

-- Import programatically marketplace wikipedia dataset or alternatively do it via UI as described in the snowflake guide.
CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZT0Z4C8RF3FT');
CREATE DATABASE IF NOT EXISTS AI_TRAINING_DATASET_FROM_WIKIPEDIA
FROM LISTING 'GZT0Z4C8RF3FT';

-- Create database and warehouse
CREATE DATABASE IF NOT EXISTS BATCH_DEMO;
CREATE WAREHOUSE IF NOT EXISTS BATCH_SEARCH_WH WITH WAREHOUSE_SIZE = 'SMALL' AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;

-- Set context
USE WAREHOUSE BATCH_SEARCH_WH;
USE DATABASE BATCH_DEMO;
CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

-- ============================================================================
-- STEP 1: Create the Wikipedia articles table (100K rows)
-- ============================================================================
CREATE OR REPLACE TABLE wikipedia_articles AS
SELECT 
    URL,
    TITLE,
    RAW_TEXT,
    TABLE_OF_CONTENTS,
    SEE_ALSO
FROM AI_TRAINING_DATASET_FROM_WIKIPEDIA.PUBLIC.WIKIPEDIA
LIMIT 100000;

-- Verify row count
SELECT COUNT(*) AS row_count FROM wikipedia_articles;

-- Preview sample data
SELECT TITLE, LEFT(RAW_TEXT, 200) AS text_preview 
FROM wikipedia_articles 
LIMIT 5;

-- ============================================================================
-- STEP 2: Create the Cortex Search Service on Wikipedia articles
-- ============================================================================
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

-- Verify service creation
SHOW CORTEX SEARCH SERVICES;

-- ============================================================================
-- STEP 3: Create a sample queries table for batch search testing
-- ============================================================================
CREATE OR REPLACE TABLE search_queries AS
SELECT DISTINCT TITLE AS query_text
FROM wikipedia_articles
ORDER BY RANDOM()
LIMIT 1000;

-- Preview queries
SELECT * FROM search_queries LIMIT 10;

-- ============================================================================
-- STEP 4: Test single search (verify service works)
-- ============================================================================
SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.wikipedia_search_service',
    '{
        "query": "machine learning artificial intelligence",
        "columns": ["TITLE", "RAW_TEXT"],
        "limit": 3
    }'
) AS test_result;

-- ============================================================================
-- STEP 4b: Single search as a TABLE (flattened results)
-- ============================================================================
SELECT 
    r.value:TITLE::VARCHAR AS title,
    LEFT(r.value:RAW_TEXT::VARCHAR, 200) AS raw_text_preview
FROM TABLE(FLATTEN(
    input => PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
            '{
                "query": "machine learning artificial intelligence",
                "columns": ["TITLE", "RAW_TEXT"],
                "limit": 5
            }'
        )
    ):results
)) AS r;

-- ============================================================================
-- STEP 4c: THE PROBLEM - No elegant way to do multiple searches
-- ============================================================================
-- SEARCH_PREVIEW requires constant strings. To search 10 terms, you must either:
--   1. Write 10 separate SELECT statements
--   2. Use ugly UNION ALL with hardcoded queries  
--   3. Build a stored procedure with a loop
--
-- None of these scale to 100, 1000, or 10000 searches.
--
-- THE SOLUTION: CORTEX_SEARCH_BATCH (see Step 5)
-- ============================================================================

-- Example: 10 searches using UNION ALL (ugly, doesn't scale)
SELECT 'quantum physics' AS query, PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "quantum physics", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR AS top_result
UNION ALL
SELECT 'world war history', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "world war history", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'climate change', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "climate change", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'solar system', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "solar system", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'ancient rome', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "ancient rome", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'machine learning', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "machine learning", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'french revolution', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "french revolution", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'deep ocean', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "deep ocean", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'renewable energy', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "renewable energy", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR
UNION ALL
SELECT 'human brain', PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    '{"query": "human brain", "columns": ["TITLE"], "limit": 1}'
)):results[0]:TITLE::VARCHAR;

-- ============================================================================
-- STEP 5: THE SOLUTION - CORTEX_SEARCH_BATCH
-- ============================================================================

-- ============================================================================
-- STEP 5a: Batch the SAME 10 searches (compare to Step 4c)
-- ============================================================================
-- Clean, elegant, reads from a table - no hardcoding!
-- NOTE: Run all three statements together as one block

CREATE OR REPLACE TEMPORARY TABLE ten_searches (query_text VARCHAR);
INSERT INTO ten_searches VALUES ('quantum physics'),('world war history'),('climate change'),('solar system'),('ancient rome'),('machine learning'),('french revolution'),('deep ocean'),('renewable energy'),('human brain');
SELECT q.query_text, s.* FROM ten_searches AS q, LATERAL CORTEX_SEARCH_BATCH(service_name => 'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE', query => q.query_text, limit => 1) AS s;

-- ============================================================================
-- STEP 5b: Scale to 1000 searches
-- ============================================================================
-- Create a table of 1000 diverse search queries from Wikipedia titles
-- NOTE: Run these statements together as one block

CREATE OR REPLACE TABLE thousand_searches AS SELECT DISTINCT TITLE AS query_text FROM wikipedia_articles ORDER BY RANDOM() LIMIT 1000;
SELECT COUNT(*) AS total_queries FROM thousand_searches;
SELECT q.query_text, s.* FROM thousand_searches AS q, LATERAL CORTEX_SEARCH_BATCH(service_name => 'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE', query => q.query_text, limit => 5) AS s;

-- ============================================================================
-- STEP 6: Create views for easy testing
-- ============================================================================

-- View for batch search (uncomment and run when ready)
CREATE OR REPLACE VIEW batch_search_results AS
SELECT
    q.query_text,
    s.*
FROM search_queries AS q,
LATERAL CORTEX_SEARCH_BATCH(
    service_name => 'BATCH_DEMO.PUBLIC.WIKIPEDIA_SEARCH_SERVICE',
    query => q.query_text,
    limit => 5
) AS s;

-- ============================================================================
-- STEP 7: Utility queries for testing different batch sizes
-- ============================================================================

-- Run batch search on 100 queries
/*
SELECT * FROM batch_search_results
WHERE query_text IN (SELECT query_text FROM search_queries LIMIT 100);
*/

-- Run batch search on 500 queries  
/*
SELECT * FROM batch_search_results
WHERE query_text IN (SELECT query_text FROM search_queries LIMIT 500);
*/

-- Run batch search on all 1000 queries
/*
SELECT * FROM batch_search_results;
*/

-- ============================================================================
-- SUMMARY
-- ============================================================================
-- Tables created:
--   - wikipedia_articles: 100K Wikipedia articles with title and full text
--   - search_queries: 1000 random article titles to use as search queries
--
-- Services created:
--   - wikipedia_search_service: Cortex Search service on wikipedia_articles
--
-- Views created:
--   - batch_search_results: Pre-configured batch search view
--
-- To test batch search performance, run:
--   SELECT * FROM batch_search_results;
-- ============================================================================

SELECT 'Setup complete!' AS status,
       (SELECT COUNT(*) FROM wikipedia_articles) AS articles_count,
       (SELECT COUNT(*) FROM search_queries) AS queries_count;

-- ============================================================================
-- CLEANUP: Delete everything and unsubscribe from Wikipedia data
-- ============================================================================
-- Run these commands when you're done testing to clean up all resources.
-- UNCOMMENT and run section by section.
-- ============================================================================

/*
-- Set context
USE ROLE SYSADMIN;
USE DATABASE BATCH_DEMO;
USE SCHEMA PUBLIC;

-- Step 1: Drop the Cortex Search service
DROP CORTEX SEARCH SERVICE IF EXISTS WIKIPEDIA_SEARCH_SERVICE;

-- Step 2: Drop views
DROP VIEW IF EXISTS batch_search_results;

-- Step 3: Drop tables
DROP TABLE IF EXISTS wikipedia_articles;
DROP TABLE IF EXISTS search_queries;
DROP TABLE IF EXISTS thousand_searches;
DROP TABLE IF EXISTS ten_searches;

-- Step 4: Drop schema (optional - only if you created it for this demo)
-- DROP SCHEMA IF EXISTS PUBLIC;

-- Step 5: Drop database (optional - only if you created it for this demo)
-- DROP DATABASE IF EXISTS BATCH_DEMO;

-- Step 6: Drop warehouse (optional - only if you created it for this demo)
-- DROP WAREHOUSE IF EXISTS BATCH_SEARCH_WH;

-- Step 7: Unsubscribe from the Wikipedia Marketplace listing
-- This removes access to AI_TRAINING_DATASET_FROM_WIKIPEDIA
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS AI_TRAINING_DATASET_FROM_WIKIPEDIA;

-- Verify cleanup
SELECT 'Cleanup complete!' AS status;
*/
