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
-- SECTION 3 — Sample Data (replace or extend with your own catalog)
--
-- 30 representative rows across all four categories.
-- In production, load your existing catalog table here instead.
-- =============================================================================

INSERT INTO CATALOG_SEARCH_DB.DATA.PRODUCTS
    (ITEM_NAME, BRAND, CATEGORY, SUBCATEGORY, DISCIPLINE, SKILL_LEVEL, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING, DESCRIPTION)
VALUES
    -- Equipment — Skis
    ('Freeride Pro 184',        'Ridgeline',  'Equipment',   'Skis',           'Freeride',  'Advanced',     'Male',   749.00, 'Ski',     '90',   'Wide-waist freeride ski built for deep powder and off-piste terrain. Rocker profile for easy float and turn initiation in variable snow conditions.'),
    ('Powder Daddy 178',        'Ridgeline',  'Equipment',   'Skis',           'Freeride',  'Expert',       'Male',   849.00, 'Ski',     '95',   'Maximum float ski designed for the deepest powder days. Twin-tip construction allows switch riding. Ridgeline signature topsheet.'),
    ('All-Mountain Carver 172', 'Ridgeline',  'Equipment',   'Skis',           'Alpine',    'Intermediate', 'Unisex', 599.00, 'Ski',     '80',   'Versatile all-mountain ski with a medium waist for confident edge-to-edge transitions on groomed and off-piste terrain.'),
    ('Corpus Freebird 186',     'Black Crows','Equipment',   'Skis',           'Freeride',  'Expert',       'Male',   899.00, 'Ski',     '95',   'Black Crows signature freeride ski. Poplar-ash core with carbon reinforcement. Built for couloirs, cliffs, and untracked faces.'),
    ('QST 106 182',             'Salomon',    'Equipment',   'Skis',           'Freeride',  'Advanced',     'Male',   799.00, 'Ski',     '92',   'Lightweight touring and freeride ski with carbon cork core. Walks like a touring ski, charges like a freeride ski.'),
    ('Kendo 88 176',            'Völkl',      'Equipment',   'Skis',           'Alpine',    'Advanced',     'Male',   699.00, 'Ski',     '85',   'Iconic frontside ski with Titanal construction. Exceptional grip on hard pack. Responsive torsionally stiff tip-to-tail.'),
    ('Cinder 96 170',           'K2',         'Equipment',   'Skis',           'All-Mountain','Intermediate','Female', 649.00, 'Ski',     '82',   'Women-specific all-mountain ski with a lighter wood core. Surfy in powder, precise on groomers. Ideal for advancing skiers.'),
    -- Equipment — Boots
    ('Freeride Boot 130',       'Ridgeline',  'Equipment',   'Boots',          'Freeride',  'Expert',       'Male',   549.00, 'Boot',    '130',  'Stiff freeride boot for aggressive charging. Boa dial entry system. Walkable sole for short approaches. Warm liner rated to -20°C.'),
    ('Tourlite Boot 110',       'Ridgeline',  'Equipment',   'Boots',          'Touring',   'Advanced',     'Unisex', 499.00, 'Boot',    '110',  'Lightweight touring boot with 60° range of motion in walk mode. Comfortable enough for long uphill approaches. Grippy rubber sole.'),
    ('Nexo LYT 100W',           'Lange',      'Equipment',   'Boots',          'Alpine',    'Intermediate', 'Female', 449.00, 'Boot',    '100',  'Women-specific boot with a wider last and lower cuff. Easy entry, warm liner, reliable buckle closure. Forgiving flex for all-day comfort.'),
    ('TLT X 130',               'Dynafit',    'Equipment',   'Boots',          'Touring',   'Expert',       'Male',   699.00, 'Boot',    '130',  'Race-proven touring boot. Lightest 130-flex performance boot. Dynafit Speed Nose for fast transitions. Carbon cuff.'),

    -- Equipment — Bindings & Poles
    ('Kingpin 13 110-130',      'Marker',     'Equipment',   'Bindings',       'Touring',   'Advanced',     'Unisex', 399.00, 'Binding', NULL,   'Pin binding with alpine release. Compatible with AT and GripWalk soles. Reliable heel release for confident downhill riding. 10-year field-proven track record.'),
    ('Attack 13 GW',            'Marker',     'Equipment',   'Bindings',       'Alpine',    'Intermediate', 'Unisex', 279.00, 'Binding', NULL,   'Gripwalk-compatible alpine binding with titanium toe piece. Wide brakes available. Outstanding power transmission.'),
    ('Titanal Touring Pole 125', 'Ridgeline', 'Equipment',   'Poles',          'Touring',   'Advanced',     'Unisex',  89.00, 'Pole',   NULL,   'Lightweight Titanal 7075 pole with ergonomic cork grip. Adjustable 100-130cm. Compatible with Ridgeline powder baskets (sold separately).'),

    -- Apparel
    ('Freeride Shell Jacket',   'Ridgeline',  'Apparel',     'Outerwear',      'Freeride',  'Advanced',     'Male',   449.00, 'Jacket',  NULL,   '3-layer Gore-Tex shell with powder skirt, RECCO reflector, and 3 chest pockets. Designed for high-output off-piste skiing. Breathes under hard effort.'),
    ('Insulated Touring Jacket','Ridgeline',  'Apparel',     'Outerwear',      'Touring',   'Intermediate', 'Female', 399.00, 'Jacket',  NULL,   'PrimaLoft Gold insulated jacket with stretch panels under arms. Warm enough for cold morning starts, packable for summit conditions. Women-fit.'),
    ('Softshell Bib Pants',     'Ridgeline',  'Apparel',     'Pants',          'Touring',   'Advanced',     'Male',   329.00, 'Pants',   NULL,   'Softshell bib with 4-way stretch fabric. Excellent breathability for skinning. Reinforced cuff patches. Zippered venting thighs.'),
    ('Wild Descent Ski Pants',  'Ridgeline',  'Apparel',     'Pants',          'Freeride',  'Expert',       'Male',   379.00, 'Pants',   NULL,   'Waterproof hardshell bib pants with reinforced scuff guards. Boot-over design. Suspender system for secure fit during big lines.'),
    ('Merino Base Layer Top',   'Icebreaker', 'Apparel',     'Base Layers',    'All-Mountain','Beginner',   'Unisex', 110.00, 'Base Layer',NULL, '200-weight merino wool next-to-skin top. Naturally odour-resistant, temperature-regulating. Machine washable. Ideal for all winter sports as a warm first layer.'),
    ('Midlayer Fleece Zip',     'Patagonia',  'Apparel',     'Midlayers',      'All-Mountain','Beginner',   'Unisex',  89.00, 'Fleece',  NULL,   'R2 TechFace fleece with 4-way stretch. Moisture-wicking, fast-drying midlayer. Compresses small for packing. Worn alone or under a shell.'),
    ('Heated Gloves Pro',       'Ridgeline',  'Apparel',     'Gloves',         'Alpine',    'Intermediate', 'Unisex', 249.00, 'Gloves',  NULL,   'Battery-heated ski gloves with 3 heat settings. 6-hour battery life on low. Gore-Tex insert, wrist leash. Perfect for circulation issues or extreme cold.'),
    ('Race Gloves GS',          'Leki',       'Apparel',     'Gloves',         'Alpine',    'Expert',       'Unisex',  79.00, 'Gloves',  NULL,   'Trigger S race glove with LEKI strap-free connection system. Slim fit for maximum feel. Goat leather palm. Competition-grade for gates or fast GS runs.'),

    -- Protection
    ('All-Mountain Helmet MIPS','Ridgeline',  'Protection',  'Helmets',        'All-Mountain','Beginner',   'Unisex', 229.00, 'Helmet',  NULL,   'MIPS-equipped ski helmet with goggle ventilation sync. Adjustable dial fit. Rated for temperatures down to -30°C. CE EN1077 and ASTM certified.'),
    ('Freeride Helmet Carbon',  'Ridgeline',  'Protection',  'Helmets',        'Freeride',  'Expert',       'Unisex', 449.00, 'Helmet',  NULL,   'Carbon shell freeride helmet. 20% lighter than standard ABS. Full face compatible. MIPS Spherical technology. Ventilation channels for high-output touring.'),
    ('Back Protector D3O',      'Ridgeline',  'Protection',  'Back Protectors','Freeride',  'Advanced',     'Male',   189.00, 'Protector',NULL,  'Level 2 CE EN13158 D3O back protector. Slim profile fits under any jacket. Harness attachment points for pack integration. Soft at rest, rigid on impact.'),
    ('Knee Guards Pro',         'Ridgeline',  'Protection',  'Knee Guards',    'Park',      'Intermediate', 'Unisex', 149.00, 'Guards',  NULL,   'Hard-shell knee guard with soft EVA backing. Slip-on design fits under ski pants. Protects patella and knee cap on park and pipe riding or mogul fields.'),
    ('Airbag Vest ABS',         'Mammut',     'Protection',  'Airbag Systems', 'Freeride',  'Expert',       'Male',   699.00, 'Airbag',  NULL,   'ABS trigger airbag vest for avalanche safety. Compatible with Mammut dual airbag packs. Lightweight 800g trigger unit. Essential for off-piste and touring.'),
    ('Wrist Guards',            'Dakine',     'Protection',  'Wrist Guards',   'Park',      'Beginner',     'Unisex',  49.00, 'Guards',  NULL,   'Hard-shell wrist guard for beginner and freestyle skiing. Fits inside gloves. Prevents hyperextension on falls. Low-profile hard cap insert.'),

    -- Accessories
    ('Ski Touring Backpack 30L','Ridgeline',  'Accessories', 'Backpacks',      'Touring',   'Advanced',     'Unisex', 199.00, 'Backpack',NULL,   'Ski touring pack with diagonal and A-frame ski carry, ice axe loops, and hip fins for skiing downhill. Hydration-compatible. 30L for day tours.'),
    ('Goggle Photochromic',     'Ridgeline',  'Accessories', 'Goggles',        'All-Mountain','Intermediate','Unisex', 189.00, 'Goggle',  NULL,   'Photochromic OTG goggle with automatic VLT adjustment from S1 (flat light) to S4 (full sun). Magnetic lens swap system. Fits Ridgeline and most OEM helmets.');

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
