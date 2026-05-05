-- =============================================================================
-- SNOW SPORTS CATALOG SEARCH DEMO — Complete Snowflake Setup
-- =============================================================================
-- Creates all Snowflake objects for the Snow Sports Multi-Index Cortex Search demo.
-- Showcases: a SINGLE Cortex Search service with TEXT INDEXES (BM25) and
--            VECTOR INDEXES (semantic) over a synthetic winter sports catalog.
--
-- DATABASE: CATALOG_SEARCH_DB
-- WAREHOUSE: CATALOG_SEARCH_WH
-- SCHEMAS:
--   APP  — Cortex Search service
--   DATA — Product catalog table
--
-- Architecture:
--   One service (PRODUCT_SEARCH) with:
--     TEXT INDEXES:   BRAND, ITEM_NAME, SUBCATEGORY  (BM25 keyword recall)
--     VECTOR INDEXES: SEARCH_TEXT                    (semantic intent recall)
--   The built-in reranker fuses BM25 and vector signals automatically.
--
-- Run as SYSADMIN or ACCOUNTADMIN.
-- =============================================================================

USE ROLE SYSADMIN;

-- =============================================================================
-- SECTION 1: WAREHOUSE
-- =============================================================================
-- SMALL size is sufficient for search indexing and product queries.
-- AUTO_SUSPEND=60 saves credits; AUTO_RESUME handles all on-demand queries.
-- =============================================================================

CREATE WAREHOUSE IF NOT EXISTS CATALOG_SEARCH_WH
  WAREHOUSE_SIZE = 'SMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE
  COMMENT = 'Warehouse for Cortex Search service and queries';

USE WAREHOUSE CATALOG_SEARCH_WH;

-- =============================================================================
-- SECTION 2: DATABASE & SCHEMAS
-- =============================================================================

CREATE DATABASE IF NOT EXISTS CATALOG_SEARCH_DB;

CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.APP
  COMMENT = 'Cortex Search service and application objects';

CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.DATA
  COMMENT = 'Snow sports product catalog';

USE DATABASE CATALOG_SEARCH_DB;
USE SCHEMA DATA;

-- =============================================================================
-- SECTION 3: PRODUCT CATALOG TABLE
-- =============================================================================
-- SEARCH_TEXT is a pre-computed column that concatenates all searchable
-- attributes. It is the column that gets the VECTOR INDEX.
-- DESCRIPTION_ORIGINAL preserves the original description before AI enrichment.
-- =============================================================================

CREATE OR REPLACE TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS (
  PRODUCT_ID           NUMBER AUTOINCREMENT PRIMARY KEY,
  ITEM_NAME            VARCHAR(500),
  BRAND                VARCHAR(200),
  CATEGORY             VARCHAR(100),     -- Equipment | Apparel | Protection | Accessories
  SUBCATEGORY          VARCHAR(200),
  DISCIPLINE           VARCHAR(100),     -- Alpine | Freeride | Nordic | Touring | Park
  SKILL_LEVEL          VARCHAR(50),      -- Beginner | Intermediate | Advanced | Expert
  GENDER               VARCHAR(50),
  PRICE                NUMBER(10, 2),
  PRODUCT_TYPE         VARCHAR(100),
  FLEX_RATING          VARCHAR(50),
  DESCRIPTION          VARCHAR(2000),
  SEARCH_TEXT          VARCHAR(4000),
  DESCRIPTION_ORIGINAL VARCHAR(2000)
);

-- =============================================================================
-- SECTION 4: LOAD SAMPLE DATA
-- =============================================================================
-- 30 representative products across Equipment, Apparel, Protection, Accessories.
-- In production, point the search service at your real PRODUCTS table.
-- =============================================================================

INSERT INTO CATALOG_SEARCH_DB.DATA.PRODUCTS
  (ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY, DISCIPLINE, SKILL_LEVEL, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING, DESCRIPTION)
VALUES
  ('Freeride Jacket', 'Ridgeline', 'Apparel', 'Outerwear', 'Freeride', 'Advanced', 'Male', 449.00, 'Jacket', NULL, '3-layer Gore-Tex shell with powder skirt, helmet-compatible hood, and pit zips for ventilation in deep snow.'),
  ('Powder Skis Pro', 'Ridgeline', 'Equipment', 'Skis', 'Freeride', 'Expert', 'Unisex', 899.00, 'Skis', 'Stiff', 'Full rocker profile with carbon fibre layup for float in deep powder. 112mm underfoot.'),
  ('All-Mountain Helmet', 'Ridgeline', 'Protection', 'Helmets', 'Alpine', 'Intermediate', 'Unisex', 189.00, 'Helmet', NULL, 'MIPS-equipped helmet with adjustable ventilation and audio-ready ear pads.'),
  ('Touring Boots Lite', 'Ridgeline', 'Equipment', 'Boots', 'Touring', 'Advanced', 'Male', 649.00, 'Boots', 'Medium-Stiff', 'Lightweight touring boot with walk mode and Vibram sole for uphill efficiency.'),
  ('Insulated Bib Pants', 'Ridgeline', 'Apparel', 'Pants', 'Freeride', 'Intermediate', 'Female', 399.00, 'Pants', NULL, 'Waterproof insulated bib with stretch panels and reinforced cuffs for all-day comfort.'),
  ('Goggles Pro', 'Ridgeline', 'Accessories', 'Eyewear', 'Alpine', 'Advanced', 'Unisex', 219.00, 'Goggles', NULL, 'Spherical lens with photochromic technology and triple-layer face foam.'),
  ('Spine Protector', 'Ridgeline', 'Protection', 'Body Armor', 'Freeride', 'Expert', 'Unisex', 159.00, 'Back Protector', NULL, 'CE Level 2 back protector with breathable mesh and adjustable straps.'),
  ('Alpine Race Skis', 'Ridgeline', 'Equipment', 'Skis', 'Alpine', 'Expert', 'Unisex', 1099.00, 'Skis', 'Very Stiff', 'Full-camber race ski with titanal layers for edge grip on ice at speed.'),
  ('Merino Base Layer', 'Ridgeline', 'Apparel', 'Base Layers', 'Alpine', 'Beginner', 'Female', 89.00, 'Base Layer', NULL, '100% merino wool base layer with flatlock seams and odour resistance.'),
  ('Corpus Freebird Jacket', 'Black Crows', 'Apparel', 'Outerwear', 'Freeride', 'Expert', 'Male', 599.00, 'Jacket', NULL, 'Premium 3L shell designed for big mountain skiing with Dermizax membrane and minimalist design.'),
  ('Atris Skis', 'Black Crows', 'Equipment', 'Skis', 'Freeride', 'Advanced', 'Unisex', 799.00, 'Skis', 'Medium-Stiff', 'Versatile freeride ski with poplar wood core and early rise tip for mixed conditions.'),
  ('Nocta Goggles', 'Black Crows', 'Accessories', 'Eyewear', 'Freeride', 'Advanced', 'Unisex', 179.00, 'Goggles', NULL, 'Wide cylindrical lens with anti-fog coating and helmet-compatible strap.'),
  ('QST Charge Jacket', 'Salomon', 'Apparel', 'Outerwear', 'Freeride', 'Advanced', 'Male', 479.00, 'Jacket', NULL, 'AdvancedSkin Dry waterproof shell with motion fit design for unrestricted movement in steep terrain.'),
  ('S/PRO Alpha 120', 'Salomon', 'Equipment', 'Boots', 'Alpine', 'Advanced', 'Male', 549.00, 'Boots', 'Stiff', 'Performance alpine boot with Coreframe shell and custom fit liner for precision skiing.'),
  ('MTN Explore Skis', 'Salomon', 'Equipment', 'Skis', 'Touring', 'Advanced', 'Unisex', 699.00, 'Skis', 'Medium', 'Lightweight touring ski with carbon chassis for efficient climbing and confident descents.'),
  ('Shift Pro Bindings', 'Salomon', 'Equipment', 'Bindings', 'Touring', 'Expert', 'Unisex', 599.00, 'Bindings', NULL, 'Hybrid touring binding with alpine-level DIN and touring release for backcountry missions.'),
  ('Kingpin 13', 'Marker', 'Equipment', 'Bindings', 'Touring', 'Expert', 'Unisex', 549.00, 'Bindings', NULL, 'Pin tech touring binding with 13 DIN release and power transmission rivaling alpine bindings.'),
  ('Griffon 13 ID', 'Marker', 'Equipment', 'Bindings', 'Alpine', 'Advanced', 'Unisex', 329.00, 'Bindings', NULL, 'All-mountain freeride binding with Inter Pivot heel for consistent release.'),
  ('Kendo 88', 'Volkl', 'Equipment', 'Skis', 'Alpine', 'Intermediate', 'Unisex', 599.00, 'Skis', 'Medium', 'Versatile all-mountain ski with Titanal frame for stability on groomers and soft snow.'),
  ('Revolt 104', 'Volkl', 'Equipment', 'Skis', 'Freeride', 'Advanced', 'Unisex', 699.00, 'Skis', 'Medium-Stiff', 'Freestyle-oriented freeride ski with full twin tip and multilayer wood core.'),
  ('Cochise 130 DYN', 'Tecnica', 'Equipment', 'Boots', 'Freeride', 'Expert', 'Male', 749.00, 'Boots', 'Very Stiff', 'Freeride boot with C.A.S. custom shell and hike mode for aggressive skiing with touring capability.'),
  ('Zero G Tour Pro', 'Tecnica', 'Equipment', 'Boots', 'Touring', 'Advanced', 'Male', 699.00, 'Boots', 'Medium', 'Ultra-lightweight touring boot at 1090g with 62-degree range of motion for fast ascents.'),
  ('Vertical Ski Pants', 'Dynastar', 'Apparel', 'Pants', 'Touring', 'Advanced', 'Male', 349.00, 'Pants', NULL, 'Lightweight stretch pants with DWR coating designed for skinning up ridgelines in variable weather.'),
  ('Legend X96 Skis', 'Dynastar', 'Equipment', 'Skis', 'Freeride', 'Advanced', 'Unisex', 749.00, 'Skis', 'Medium-Stiff', 'Directional freeride ski with Hybridcore construction for float and power in all snow conditions.'),
  ('Aura MIPS Helmet', 'Giro', 'Protection', 'Helmets', 'Alpine', 'Intermediate', 'Female', 199.00, 'Helmet', NULL, 'Low-profile helmet with MIPS rotational impact protection and thermostat control ventilation.'),
  ('Contour Helmet', 'Giro', 'Protection', 'Helmets', 'Alpine', 'Beginner', 'Unisex', 129.00, 'Helmet', NULL, 'Entry-level helmet with in-mold construction and passive ventilation for resort skiing.'),
  ('Soft Shell Touring Jacket', 'Ortovox', 'Apparel', 'Outerwear', 'Touring', 'Intermediate', 'Female', 299.00, 'Jacket', NULL, 'Breathable soft shell with Merino wool lining for high-output touring in cold conditions.'),
  ('Avalanche Airbag Pack', 'Ortovox', 'Protection', 'Avalanche Safety', 'Touring', 'Expert', 'Unisex', 899.00, 'Backpack', NULL, 'Electronic avalanche airbag system with 30L capacity and integrated rescue tools compartment.'),
  ('Heated Gloves Pro', 'Hestra', 'Accessories', 'Gloves', 'Alpine', 'Intermediate', 'Unisex', 299.00, 'Gloves', NULL, 'Rechargeable heated gloves with army leather palm and waterproof membrane for extreme cold days.'),
  ('Fleece Neck Gaiter', 'Buff', 'Accessories', 'Neckwear', 'Alpine', 'Beginner', 'Unisex', 35.00, 'Gaiter', NULL, 'Midweight fleece gaiter with moisture-wicking fabric and seamless construction for helmet compatibility.');

-- =============================================================================
-- SECTION 5: (OPTIONAL) AI ENRICHMENT
-- =============================================================================
-- Enrich product descriptions with CORTEX.COMPLETE() before building SEARCH_TEXT.
-- This closes the vocabulary gap between terse product copy and customer queries.
-- =============================================================================

-- Step 5a: Preserve originals
-- ALTER TABLE CATALOG_SEARCH_DB.DATA.PRODUCTS
--     ADD COLUMN IF NOT EXISTS DESCRIPTION_ORIGINAL VARCHAR(2000);
-- UPDATE CATALOG_SEARCH_DB.DATA.PRODUCTS SET DESCRIPTION_ORIGINAL = DESCRIPTION;

-- Step 5b: Enrich all descriptions (~1-2 credits per 1,000 rows)
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

-- =============================================================================
-- SECTION 6: BUILD SEARCH_TEXT COLUMN
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

-- Verify
SELECT COUNT(*) AS total_products FROM CATALOG_SEARCH_DB.DATA.PRODUCTS;

SELECT PRODUCT_ID, BRAND, ITEM_NAME, CATEGORY,
       LEFT(SEARCH_TEXT, 200) AS search_text_preview
FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
LIMIT 5;

-- =============================================================================
-- SECTION 7: CORTEX SEARCH SERVICE (SINGLE MULTI-INDEX)
-- =============================================================================
-- One service with:
--   TEXT INDEXES   — BM25 keyword indexes on BRAND, ITEM_NAME, SUBCATEGORY
--   VECTOR INDEXES — Dense embedding index on SEARCH_TEXT
--   ATTRIBUTES     — Columns returned with each result (not indexed)
--
-- The built-in reranker fuses BM25 and vector signals automatically.
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
-- SECTION 8: TEST QUERIES
-- =============================================================================

-- Test 1: Brand name lookup (exercises TEXT INDEX on BRAND)
SELECT PARSE_JSON(
    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH',
        '{
            "query": "ridgeline",
            "columns": ["PRODUCT_ID", "ITEM_NAME", "BRAND", "CATEGORY", "PRICE"],
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

-- =============================================================================
-- SECTION 9: GRANTS (optional — uncomment and adjust role as needed)
-- =============================================================================
-- GRANT USAGE ON DATABASE CATALOG_SEARCH_DB TO ROLE <your_role>;
-- GRANT USAGE ON SCHEMA CATALOG_SEARCH_DB.APP TO ROLE <your_role>;
-- GRANT USAGE ON SCHEMA CATALOG_SEARCH_DB.DATA TO ROLE <your_role>;
-- GRANT SELECT ON ALL TABLES IN SCHEMA CATALOG_SEARCH_DB.DATA TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH TO ROLE <your_role>;

-- =============================================================================
-- CLEANUP (run to remove all objects created by this quickstart)
-- =============================================================================
-- DROP CORTEX SEARCH SERVICE IF EXISTS CATALOG_SEARCH_DB.APP.PRODUCT_SEARCH;
-- DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.APP;
-- DROP SCHEMA IF EXISTS CATALOG_SEARCH_DB.DATA;
-- DROP DATABASE IF EXISTS CATALOG_SEARCH_DB;
-- DROP WAREHOUSE IF EXISTS CATALOG_SEARCH_WH;
