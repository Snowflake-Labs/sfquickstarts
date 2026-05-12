-- =============================================================================
-- SNOW SPORTS CATALOG SEARCH DEMO — Complete Snowflake Setup
-- =============================================================================
-- Creates all Snowflake objects for the Snow Sports Multi-Index Cortex Search demo.
-- Showcases: a SINGLE Cortex Search service with TEXT INDEXES and
--            VECTOR INDEXES over a synthetic winter sports catalog.
--
-- DATABASE: CATALOG_SEARCH_DB
-- WAREHOUSE: CATALOG_SEARCH_WH
-- SCHEMAS:
--   APP  — Cortex Search service and application objects
--   DATA — Product catalog table
--
-- Architecture:
--   One service (PRODUCT_SEARCH) with:
--     TEXT INDEXES:   BRAND, ITEM_NAME, SUBCATEGORY  (keyword recall)
--     VECTOR INDEXES: SEARCH_TEXT                    (semantic intent recall)
--   The built-in reranker fuses text and vector signals automatically.
--
-- Run as ACCOUNTADMIN.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- SECTION 1: DATABASE, SCHEMAS & WAREHOUSE
-- =============================================================================

CREATE DATABASE IF NOT EXISTS CATALOG_SEARCH_DB;
CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.DATA;
CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.APP;

CREATE WAREHOUSE IF NOT EXISTS CATALOG_SEARCH_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE
  COMMENT = 'Warehouse for Cortex Search service and queries';

USE DATABASE CATALOG_SEARCH_DB;
USE SCHEMA DATA;
USE WAREHOUSE CATALOG_SEARCH_WH;

-- =============================================================================
-- SECTION 2: PRODUCT CATALOG TABLE
-- =============================================================================
-- SEARCH_TEXT is a pre-computed column that concatenates all searchable
-- attributes. It is the column that gets the VECTOR INDEX.
-- =============================================================================

CREATE OR REPLACE TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS (
  PRODUCT_ID      NUMBER AUTOINCREMENT PRIMARY KEY,
  ITEM_NAME       VARCHAR(500),
  BRAND           VARCHAR(200),
  CATEGORY        VARCHAR(100),     -- Equipment | Apparel | Protection | Accessories
  SUBCATEGORY     VARCHAR(200),
  DISCIPLINE      VARCHAR(100),     -- Alpine | Freeride | Nordic | Touring | Park
  SKILL_LEVEL     VARCHAR(50),      -- Beginner | Intermediate | Advanced | Expert
  GENDER          VARCHAR(50),
  PRICE           NUMBER(10, 2),
  PRODUCT_TYPE    VARCHAR(100),
  FLEX_RATING     VARCHAR(50),
  DESCRIPTION     VARCHAR(2000),
  SEARCH_TEXT     VARCHAR(4000)
);

-- =============================================================================
-- SECTION 3: LOAD SAMPLE DATA
-- =============================================================================
-- 1,085 products across Equipment, Apparel, Protection, Accessories.
-- 5 brands: Ridgeline (~50%), Black Crows, Salomon, Volkl, Ortovox.
-- In production, point the search service at your real PRODUCTS table.
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
--   4. Drag and drop products.csv (or click to browse and select the file)
--   5. Click "Upload"
--
-- OPTION B: Use the PUT command from SnowSQL or a Snowflake connector:
--   PUT file:///path/to/products.csv @CATALOG_SEARCH_DB.DATA.PRODUCTS_STAGE OVERWRITE=TRUE AUTO_COMPRESS=FALSE;

-- 3d. Load the CSV data into the PRODUCTS table
COPY INTO CATALOG_SEARCH_DB.DATA.PRODUCTS
  (ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY, DISCIPLINE, SKILL_LEVEL, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING, DESCRIPTION)
FROM @CATALOG_SEARCH_DB.DATA.PRODUCTS_STAGE/products.csv
FILE_FORMAT = CATALOG_SEARCH_DB.DATA.PRODUCTS_CSV_FORMAT
ON_ERROR = 'ABORT_STATEMENT';

-- Verify row count (expected: 1,085)
SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;

-- =============================================================================
-- SECTION 4: BUILD SEARCH_TEXT COLUMN
-- =============================================================================
-- Concatenates every attribute a user might describe. This gives the vector
-- index maximum coverage for semantic search.
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

-- Verify the data
SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;

SELECT PRODUCT_ID, BRAND, ITEM_NAME, CATEGORY,
       LEFT(SEARCH_TEXT, 200) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;

-- =============================================================================
-- SECTION 5: (OPTIONAL) AI ENRICHMENT
-- =============================================================================
-- Enrich product descriptions with AI_COMPLETE() before building SEARCH_TEXT.
-- This closes the vocabulary gap between terse product copy and customer queries.
-- Run this section BEFORE Section 4 if you want enriched descriptions indexed.
-- =============================================================================

-- Step 5a: Preview enrichment on 3 rows (always preview before mass update)
-- SELECT
--     PRODUCT_ID,
--     ITEM_NAME,
--     BRAND,
--     LEFT(DESCRIPTION, 100)                     AS original_description,
--     AI_COMPLETE(
--         'mistral-large2',
--         CONCAT(
--             'Write a rich, engaging product description for an online ski shop catalog. ',
--             'Use natural language a customer would search for. Mention key use cases, ',
--             'target skill level, and standout features. Keep it under 150 words.\n\n',
--             'Product: ',     ITEM_NAME,    '\n',
--             'Brand: ',       BRAND,        '\n',
--             'Category: ',    SUBCATEGORY,  '\n',
--             'Discipline: ',  DISCIPLINE,   '\n',
--             'Skill Level: ', SKILL_LEVEL,  '\n',
--             'Gender: ',      GENDER,       '\n',
--             'Original description: ', DESCRIPTION
--         )
--     )                                           AS enriched_description
-- FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
-- LIMIT 3;

-- Step 5b: Preserve originals (recommended)
-- ALTER TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS
--     ADD COLUMN DESCRIPTION_ORIGINAL VARCHAR(2000);
-- UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
--     SET DESCRIPTION_ORIGINAL = DESCRIPTION;

-- Step 5c: Enrich all descriptions (~1-2 credits per 1,000 rows)
-- UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
-- SET DESCRIPTION = AI_COMPLETE(
--     'mistral-large2',
--     CONCAT(
--         'Write a rich, engaging product description for an online ski shop catalog. ',
--         'Use natural language a customer would search for. Mention key use cases, ',
--         'target skill level, and standout features. Keep it under 150 words.\n\n',
--         'Product: ',     ITEM_NAME,    '\n',
--         'Brand: ',       BRAND,        '\n',
--         'Category: ',    SUBCATEGORY,  '\n',
--         'Discipline: ',  DISCIPLINE,   '\n',
--         'Skill Level: ', SKILL_LEVEL,  '\n',
--         'Gender: ',      GENDER,       '\n',
--         'Original description: ', DESCRIPTION
--     )
-- );

-- Step 5d: Rebuild SEARCH_TEXT with enriched descriptions
-- UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS
-- SET SEARCH_TEXT = TRIM(
--     COALESCE(BRAND,        '') || ' ' ||
--     COALESCE(ITEM_NAME,    '') || ' ' ||
--     COALESCE(SUBCATEGORY,  '') || ' ' ||
--     COALESCE(DISCIPLINE,   '') || ' ' ||
--     COALESCE(SKILL_LEVEL,  '') || ' ' ||
--     COALESCE(GENDER,       '') || ' ' ||
--     COALESCE(DESCRIPTION,  '')
-- );

-- =============================================================================
-- SECTION 6: CORTEX SEARCH SERVICE (SINGLE MULTI-INDEX)
-- =============================================================================
-- One service with:
--   TEXT INDEXES   — Keyword indexes on BRAND, ITEM_NAME, SUBCATEGORY
--   VECTOR INDEXES — Dense embedding index on SEARCH_TEXT
--   ATTRIBUTES     — Columns returned with each result (not indexed)
--
-- The built-in reranker fuses text and vector signals automatically.
-- No fan-out, no manual reranking, no separate services per category.
-- =============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH
    TEXT INDEXES   BRAND, ITEM_NAME, SUBCATEGORY
    VECTOR INDEXES SEARCH_TEXT(model='snowflake-arctic-embed-l-v2.0')
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
-- VERIFY SEARCH SERVICE
-- =============================================================================

SHOW CORTEX SEARCH SERVICES IN SCHEMA CATALOG_SEARCH_DB.APP;
DESCRIBE CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;

-- =============================================================================
-- SECTION 7: TEST QUERIES
-- =============================================================================

-- Test 1: Query all indexes for "warm waterproof jacket for off-piste skiing"
-- Uses the simple query field which searches across all indexes simultaneously.
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "warm waterproof jacket for off-piste skiing",
            "columns": ["ITEM_NAME", "BRAND", "CATEGORY", "PRICE"],
            "limit": 10
        }'
    )
) AS search_results;

-- Test 2: Multi-index query syntax — search multiple columns independently.
-- Searches the TEXT INDEX on BRAND for "ridgeline" and the VECTOR INDEX on
-- SEARCH_TEXT for "warm waterproof jacket for off-piste skiing".
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "PRICE"],
            "multi_index_query": {
                "BRAND": [{"text": "ridgeline"}],
                "SEARCH_TEXT": [{"text": "warm waterproof jacket for off-piste skiing"}]
            },
            "limit": 10
        }'
    )
) AS search_results;

-- Test 3: Attribute filter — server-side filtering by SKILL_LEVEL.
-- Only products matching the filter are scored and returned.
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

-- =============================================================================
-- SECTION 8: SPCS DEPLOYMENT (OPTIONAL)
-- =============================================================================
-- Deploy the Snow Sports Store app as a Snowpark Container Service.
-- Requires Docker installed locally and the image built and pushed.
-- =============================================================================

-- 8a. Create an image repository
CREATE IMAGE REPOSITORY IF NOT EXISTS CATALOG_SEARCH_DB.APP.APP_IMAGES;

-- Get the repository URL (needed for docker push)
SHOW IMAGE REPOSITORIES IN SCHEMA CATALOG_SEARCH_DB.APP;
-- Note the repository_url column, e.g.: <account>.registry.snowflakecomputing.com/catalog_search_db/app/app_images

-- 8b. Create a compute pool
CREATE COMPUTE POOL IF NOT EXISTS CATALOG_SEARCH_POOL
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_XS
  AUTO_SUSPEND_SECS = 300
  AUTO_RESUME = TRUE;

-- 8c. Create the SPCS service (run after building and pushing the Docker image)
CREATE SERVICE CATALOG_SEARCH_DB.APP.SNOW_SPORTS_STORE
  IN COMPUTE POOL CATALOG_SEARCH_POOL
  FROM SPECIFICATION $$
spec:
  containers:
  - name: snow-sports-store
    image: /catalog_search_db/app/app_images/snow-sports-store:v1
    env:
      SNOWFLAKE_DATABASE: CATALOG_SEARCH_DB
      SNOWFLAKE_SCHEMA: APP
      SNOWFLAKE_WAREHOUSE: CATALOG_SEARCH_WH
    resources:
      requests:
        cpu: 0.5
        memory: 1Gi
      limits:
        cpu: 2
        memory: 4Gi
  endpoints:
  - name: store-ui
    port: 8000
    public: true
$$
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1;

-- 8d. Verify deployment
SELECT SYSTEM$GET_SERVICE_STATUS('CATALOG_SEARCH_DB.APP.SNOW_SPORTS_STORE');
SHOW ENDPOINTS IN SERVICE CATALOG_SEARCH_DB.APP.SNOW_SPORTS_STORE;

-- =============================================================================
-- CLEANUP (run to remove all objects created by this quickstart)
-- =============================================================================
-- DROP DATABASE IF EXISTS CATALOG_SEARCH_DB;
-- DROP WAREHOUSE IF EXISTS CATALOG_SEARCH_WH;
