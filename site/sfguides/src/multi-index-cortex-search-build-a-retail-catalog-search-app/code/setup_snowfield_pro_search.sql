-- Run this worksheet top-to-bottom in a single Snowflake session.
-- Expected runtime: ~5 min setup + 2-5 min for the service to finish indexing.

-- =============================================================================
-- SECTION 1 — Environment Setup
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- Create database and schemas
CREATE DATABASE IF NOT EXISTS CATALOG_SEARCH_DB;
CREATE SCHEMA  IF NOT EXISTS CATALOG_SEARCH_DB.DATA;
CREATE SCHEMA  IF NOT EXISTS CATALOG_SEARCH_DB.APP;

-- Dedicated warehouse for the search service
CREATE WAREHOUSE IF NOT EXISTS CATALOG_SEARCH_WH
    WAREHOUSE_SIZE = 'SMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE
    COMMENT        = 'Warehouse for Cortex Search indexing and queries';

USE DATABASE  CATALOG_SEARCH_DB;
USE SCHEMA    DATA;
USE WAREHOUSE CATALOG_SEARCH_WH;


-- =============================================================================
-- SECTION 2 — Product Catalog Table
-- =============================================================================

CREATE OR REPLACE TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS (
    PRODUCT_ID    NUMBER AUTOINCREMENT PRIMARY KEY,
    ITEM_NAME     VARCHAR(500),
    BRAND         VARCHAR(200),
    CATEGORY      VARCHAR(100),      -- Equipment | Apparel | Protection | Accessories
    SUBCATEGORY   VARCHAR(200),
    DISCIPLINE    VARCHAR(100),      -- Alpine | Freeride | Nordic | Touring | Park
    SKILL_LEVEL   VARCHAR(50),       -- Beginner | Intermediate | Advanced | Expert
    GENDER        VARCHAR(50),
    PRICE         NUMBER(10, 2),
    PRODUCT_TYPE  VARCHAR(100),
    FLEX_RATING   VARCHAR(50),
    DESCRIPTION   VARCHAR(2000),
    SEARCH_TEXT   VARCHAR(4000)      -- Pre-computed for the VECTOR INDEX
);


-- =============================================================================
-- SECTION 3 -- Load the Product Catalog from CSV
--
-- 1,085 products across Equipment, Apparel, Protection, Accessories.
-- 5 brands: Ridgeline (~50%), Black Crows, Salomon, Volkl, Ortovox.
-- In production, load your existing catalog table here instead.
-- =============================================================================

-- 3a. Create a file format for the CSV
CREATE OR REPLACE FILE FORMAT CATALOG_SEARCH_DB.DATA.PRODUCTS_CSV_FORMAT
  TYPE = 'CSV'
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('');

-- 3b. Create a stage to hold the CSV file
CREATE OR REPLACE STAGE CATALOG_SEARCH_DB.DATA.PRODUCTS_STAGE
  FILE_FORMAT = CATALOG_SEARCH_DB.DATA.PRODUCTS_CSV_FORMAT
  COMMENT = 'Stage for loading the products.csv catalog file';

-- 3c. Upload products.csv to the stage
-- OPTION A (recommended): Use the Snowsight UI
--   1. In Snowsight, navigate to: Data > Databases > CATALOG_SEARCH_DB > DATA > Stages
--   2. Click on PRODUCTS_STAGE
--   3. Click the "+ Files" button in the top right
--   4. Drag and drop products.csv (or click to browse)
--   5. Click "Upload"
--
-- OPTION B: Use the PUT command from SnowSQL or a Snowflake connector:
--   PUT file:///path/to/products.csv @CATALOG_SEARCH_DB.DATA.PRODUCTS_STAGE AUTO_COMPRESS=FALSE;

-- 3d. Load the CSV data into the PRODUCTS table
COPY INTO CATALOG_SEARCH_DB.DATA.PRODUCTS
  (ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY, DISCIPLINE, SKILL_LEVEL, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING, DESCRIPTION)
FROM @CATALOG_SEARCH_DB.DATA.PRODUCTS_STAGE/products.csv
FILE_FORMAT = CATALOG_SEARCH_DB.DATA.PRODUCTS_CSV_FORMAT
ON_ERROR = 'ABORT_STATEMENT';

-- Verify row count
SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;
-- Expected: 1,085

-- =============================================================================
-- Step 4 — Build the SEARCH_TEXT Column
--
-- The `SEARCH_TEXT` column concatenates every attribute a user might describe — brand, product name, subcategory, discipline, skill level, gender, and the full description. This ---- gives the vector index maximum coverage.
-- =============================================================================


UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET SEARCH_TEXT = TRIM(
    COALESCE(BRAND,        '') || ' ' ||
    COALESCE(ITEM_NAME,    '') || ' ' ||
    COALESCE(SUBCATEGORY,  '') || ' ' ||
    COALESCE(DISCIPLINE,   '') || ' ' ||
    COALESCE(SKILL_LEVEL,  '') || ' ' ||
    COALESCE(GENDER,       '') || ' ' ||
    COALESCE(DESCRIPTION,  '')
);

-- =============================================================================
-- Step 5 — Verify the data
--
-- Check row count and sample SEARCH_TEXT content
-- =============================================================================

SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;

SELECT PRODUCT_ID, BRAND, ITEM_NAME, CATEGORY,
       LEFT(SEARCH_TEXT, 200) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;

-- =============================================================================
-- (OPTIONAL) — AI-Enriched Product Descriptions with Cortex
--
-- Use AI_COMPLETE() to generate richer, more descriptive product
-- descriptions before building SEARCH_TEXT.
--
-- Why? Short hand-written descriptions miss synonyms and natural language
-- patterns that customers actually search for. An LLM rewrites each description
-- in the voice of a product page, improving semantic recall.
--
-- SKIP THIS SECTION to proceed with original descriptions.
-- Cost: ~1-2 credits per 1,000 rows with mistral-large2.
-- Runtime: ~30-60 sec for 30 rows | ~3-5 min for 1,040 rows.
-- =============================================================================

-- Step 1: Preview enrichment on 3 rows before committing
SELECT
    PRODUCT_ID,
    ITEM_NAME,
    BRAND,
    LEFT(DESCRIPTION, 100) AS original_description,
    AI_COMPLETE(
        'mistral-large2',
        CONCAT(
            'Write a rich, engaging product description for an online ski shop catalog. ',
            'Use natural language a customer would search for. Mention key use cases, ',
            'target skill level, and standout features. Keep it under 150 words.\n\n',
            'Product: ',     ITEM_NAME,   '\n',
            'Brand: ',       BRAND,       '\n',
            'Category: ',    SUBCATEGORY, '\n',
            'Discipline: ',  DISCIPLINE,  '\n',
            'Skill Level: ', SKILL_LEVEL, '\n',
            'Gender: ',      GENDER,      '\n',
            'Original description: ', DESCRIPTION
        )
    ) AS enriched_description
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 3;

-- Step 2 (optional): Preserve originals before overwriting
-- ALTER TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS ADD COLUMN DESCRIPTION_ORIGINAL VARCHAR(2000);
-- UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS SET DESCRIPTION_ORIGINAL = DESCRIPTION;

-- Step 3: Mass-update DESCRIPTION for all rows with AI-generated versions
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET DESCRIPTION = AI_COMPLETE(
    'mistral-large2',
    CONCAT(
        'Write a rich, engaging product description for an online ski shop catalog. ',
        'Use natural language a customer would search for. Mention key use cases, ',
        'target skill level, and standout features. Keep it under 150 words.\n\n',
        'Product: ',     ITEM_NAME,   '\n',
        'Brand: ',       BRAND,       '\n',
        'Category: ',    SUBCATEGORY, '\n',
        'Discipline: ',  DISCIPLINE,  '\n',
        'Skill Level: ', SKILL_LEVEL, '\n',
        'Gender: ',      GENDER,      '\n',
        'Original description: ', DESCRIPTION
    )
);

-- Step 4: Verify enriched descriptions
SELECT
    PRODUCT_ID,
    BRAND,
    ITEM_NAME,
    LEFT(DESCRIPTION, 200) AS enriched_description_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;

-- Step 5: Rebuild SEARCH_TEXT with enriched descriptions
-- Now that DESCRIPTION is richer, rebuild SEARCH_TEXT so the vector index
-- captures the full enriched content.
UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
SET SEARCH_TEXT = TRIM(
    COALESCE(BRAND,        '') || ' ' ||
    COALESCE(ITEM_NAME,    '') || ' ' ||
    COALESCE(SUBCATEGORY,  '') || ' ' ||
    COALESCE(DISCIPLINE,   '') || ' ' ||
    COALESCE(SKILL_LEVEL,  '') || ' ' ||
    COALESCE(GENDER,       '') || ' ' ||
    COALESCE(DESCRIPTION,  '')
);

-- Verify the enriched SEARCH_TEXT preview
SELECT PRODUCT_ID, BRAND, ITEM_NAME,
       LEFT(SEARCH_TEXT, 250) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;

-- =============================================================================
-- SECTION 6 — Create the Multi-Index Cortex Search Service
--
-- One DDL. Four indexes. One service.
--   TEXT INDEXES   — BM25 keyword indexes on BRAND, ITEM_NAME, SUBCATEGORY
--   VECTOR INDEXES — Dense embedding index on SEARCH_TEXT
-- =============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH
    TEXT INDEXES   BRAND, ITEM_NAME, SUBCATEGORY
    VECTOR INDEXES SEARCH_TEXT(model = 'snowflake-arctic-embed-l-v2.0')
    ATTRIBUTES     PRODUCT_ID, ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY,
                   SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING
    WAREHOUSE  = CATALOG_SEARCH_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT
            PRODUCT_ID,
            SEARCH_TEXT,
            ITEM_NAME,
            BRAND,
            CATEGORY,
            SUBCATEGORY,
            SKILL_LEVEL,
            DISCIPLINE,
            GENDER,
            PRICE,
            PRODUCT_TYPE,
            FLEX_RATING
        FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    );


-- =============================================================================
-- SECTION 7 — Verify Service Status
--
-- Wait for indexing_state = 'READY' before running queries (2-5 min for 30 rows,
-- longer for larger catalogs).
-- =============================================================================

-- Check all services in the APP schema
SHOW CORTEX SEARCH SERVICES IN SCHEMA CATALOG_SEARCH_DB.APP;

-- Detailed status including indexing_state, row count, and last refresh time
DESCRIBE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;


-- =============================================================================
-- SECTION 8 — Test Queries via SEARCH_PREVIEW
--
-- SEARCH_PREVIEW is the SQL interface for Cortex Search.
-- For multi_index_query, use the Python SDK (see quickstart).
-- =============================================================================

-- Test 1: Brand name lookup (exercises TEXT INDEX on BRAND)
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "ridgeline",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "SUBCATEGORY", "PRICE"],
            "limit": 10
        }'
    )
) AS search_results;

-- Test 2: Intent / semantic query (exercises VECTOR INDEX on SEARCH_TEXT)
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "warm waterproof jacket for off-piste skiing",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "PRICE"],
            "limit": 10
        }'
    )
) AS search_results;

-- Test 3: Skill level filter (server-side attribute filtering)
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "protective gear",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "SKILL_LEVEL", "PRICE"],
            "filter": {"@eq": {"SKILL_LEVEL": "Beginner"}},
            "limit": 10
        }'
    )
) AS search_results;

-- Test 4: Category breakdown — count results per category for a query
-- (demonstrates how CATEGORY attribute enables breakdown without separate services)
WITH raw AS (
    SELECT PARSE_JSON(
        SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
            'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
            '{
                "query": "ridgeline",
                "columns": ["CATEGORY"],
                "limit": 100
            }'
        )
    ) AS results
),
flattened AS (
    SELECT f.value:CATEGORY::STRING AS category
    FROM raw, LATERAL FLATTEN(input => results:results) f
)
SELECT category, COUNT(*) AS result_count
FROM flattened
GROUP BY 1
ORDER BY 2 DESC;

-- =============================================================================
-- SECTION 10 — Cleanup
--
-- Run this section ONLY when you are done with the quickstart and want to
-- remove all created objects.
-- =============================================================================

-- DROP CORTEX SEARCH SERVICE IF EXISTS CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;
-- DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.APP;
-- DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.DATA;
-- DROP DATABASE IF EXISTS CATALOG_SEARCH_DB;
-- DROP WAREHOUSE IF EXISTS CATALOG_SEARCH_WH;
