-- =============================================================================
-- SNOW SPORTS CATALOG SEARCH DEMO — Complete Snowflake Setup
-- =============================================================================
-- Creates all Snowflake objects for the Snow Sports Multi-Index Cortex Search demo.
-- Showcases: multi-index Cortex Search over a synthetic 1,000-product winter sports catalog.
--
-- DATABASE: CATALOG_SEARCH_DB
-- WAREHOUSE: CATALOG_SEARCH_WH
-- SCHEMAS:
--   APP  — Cortex Search services
--   DATA — Product catalog table
--
-- 4 Cortex Search Services (one per product segment):
--   EQUIPMENT_SEARCH  — Hardgoods: skis, snowboards, boots, bindings
--   APPAREL_SEARCH    — Softgoods: jackets, bibs, base layers, mid-layers
--   PROTECTION_SEARCH — Helmets, goggles, body armor
--   ACCESSORIES_SEARCH — Gloves, beanies, backcountry safety, maintenance tools
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
  COMMENT = 'Snow Sports Catalog Search Demo — indexing and queries';

USE WAREHOUSE CATALOG_SEARCH_WH;

-- =============================================================================
-- SECTION 2: DATABASE & SCHEMAS
-- =============================================================================

CREATE DATABASE IF NOT EXISTS CATALOG_SEARCH_DB
  COMMENT = 'Snow Sports Catalog Search Demo: multi-index Cortex Search over 1,000 synthetic products';

CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.APP
  COMMENT = 'Cortex Search services and application objects';

CREATE SCHEMA IF NOT EXISTS CATALOG_SEARCH_DB.DATA
  COMMENT = 'Snow sports product catalog';

-- =============================================================================
-- SECTION 3: PRODUCT CATALOG TABLE
-- =============================================================================
-- This table is populated by the notebook using AI_COMPLETE-generated descriptions.
-- CATEGORY drives which Cortex Search service indexes each product.
-- PRODUCT_TYPE is used by the React frontend for image mapping.
-- =============================================================================

CREATE TABLE IF NOT EXISTS CATALOG_SEARCH_DB.DATA.PRODUCTS (
  PRODUCT_ID    NUMBER        NOT NULL PRIMARY KEY,
  ITEM_NAME     VARCHAR(200)  NOT NULL,
  DESCRIPTION   TEXT          NOT NULL,   -- Full richtext — indexed by Cortex Search
  CATEGORY      VARCHAR(50)   NOT NULL,   -- Equipment | Apparel | Protection | Accessories
  SUBCATEGORY   VARCHAR(100)  NOT NULL,   -- e.g. Alpine Skis, Outer Shell Jacket, Avalanche Transceiver
  BRAND         VARCHAR(100)  NOT NULL,
  PRICE         DECIMAL(8,2)  NOT NULL,
  SKILL_LEVEL   VARCHAR(30)   NOT NULL,   -- Beginner | Intermediate | Advanced | Professional
  DISCIPLINE    VARCHAR(50)   NOT NULL,   -- Alpine | Freeride | Freestyle | Touring | General | All-Mountain
  GENDER        VARCHAR(20)   NOT NULL,   -- Mens | Womens | Unisex | Kids
  PRODUCT_TYPE  VARCHAR(50)   NOT NULL,   -- Image key: alpine_ski, freeride_ski, snowboard, etc.
  FLEX_RATING   VARCHAR(20),              -- Boots/bindings only: Soft | Medium | Stiff | Extra-Stiff
  WEIGHT_G      NUMBER,                   -- Weight in grams where applicable
  CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Quick row count (run after notebook populates the table)
-- SELECT CATEGORY, COUNT(*) AS n FROM CATALOG_SEARCH_DB.DATA.PRODUCTS GROUP BY 1 ORDER BY 1;

-- =============================================================================
-- SECTION 4: CORTEX SEARCH SERVICES
-- =============================================================================
-- One service per product segment. Each indexes the DESCRIPTION column for
-- semantic search, with key columns returned as filterable ATTRIBUTES.
--
-- EMBEDDING_MODEL: snowflake-arctic-embed-l-v2.0 — highest-quality embeddings
-- TARGET_LAG: '1 hour' — index refreshes within 1 hour of new inserts
-- WAREHOUSE: used only during index builds (incremental, low-cost)
--
-- Multi-index query pattern (used by the React app backend):
--   Fan out the same search query to all 4 services in parallel,
--   merge results, and tag each result with its source service name.
-- =============================================================================

-- 4a. Equipment Search — Hardgoods
-- Covers: Alpine Skis, All-Mountain Skis, Freeride Skis, Freestyle Skis,
--         All-Mountain Snowboards, Freestyle Snowboards, Freeride Snowboards,
--         Ski Boots, Snowboard Boots, Ski Bindings, Snowboard Bindings
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS CATALOG_SEARCH_DB.APP.EQUIPMENT_SEARCH
  ON DESCRIPTION
  ATTRIBUTES PRODUCT_ID, ITEM_NAME, BRAND, SUBCATEGORY, SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING
  WAREHOUSE = CATALOG_SEARCH_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
  AS (
    SELECT PRODUCT_ID, ITEM_NAME, DESCRIPTION, BRAND, SUBCATEGORY,
           SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE, FLEX_RATING
    FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    WHERE CATEGORY = 'Equipment'
  );

-- 4b. Apparel Search — Softgoods
-- Covers: Outer Shell Jackets, Insulated Jackets, Ski Bibs, Ski Pants,
--         Mid-Layer Fleece, Down Mid-Layers, Base Layer Tops, Base Layer Bottoms
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS CATALOG_SEARCH_DB.APP.APPAREL_SEARCH
  ON DESCRIPTION
  ATTRIBUTES PRODUCT_ID, ITEM_NAME, BRAND, SUBCATEGORY, SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
  WAREHOUSE = CATALOG_SEARCH_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
  AS (
    SELECT PRODUCT_ID, ITEM_NAME, DESCRIPTION, BRAND, SUBCATEGORY,
           SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
    FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    WHERE CATEGORY = 'Apparel'
  );

-- 4c. Protection Search — Safety Gear
-- Covers: Ski Helmets, Snowboard Helmets, Ski Goggles, Snowboard Goggles,
--         Back Protectors, Wrist Guards, Knee Pads, Impact Shorts
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS CATALOG_SEARCH_DB.APP.PROTECTION_SEARCH
  ON DESCRIPTION
  ATTRIBUTES PRODUCT_ID, ITEM_NAME, BRAND, SUBCATEGORY, SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
  WAREHOUSE = CATALOG_SEARCH_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
  AS (
    SELECT PRODUCT_ID, ITEM_NAME, DESCRIPTION, BRAND, SUBCATEGORY,
           SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
    FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    WHERE CATEGORY = 'Protection'
  );

-- 4d. Accessories Search — Handwear, Headwear, Safety, Maintenance
-- Covers: Ski Gloves, Snowboard Gloves, Mittens, Beanies, Face Masks,
--         Neck Gaiters, Avalanche Transceivers, Avalanche Probes,
--         Avalanche Shovels, Ski Wax, Edge Sharpeners, Ski Bags
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS CATALOG_SEARCH_DB.APP.ACCESSORIES_SEARCH
  ON DESCRIPTION
  ATTRIBUTES PRODUCT_ID, ITEM_NAME, BRAND, SUBCATEGORY, SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
  WAREHOUSE = CATALOG_SEARCH_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
  AS (
    SELECT PRODUCT_ID, ITEM_NAME, DESCRIPTION, BRAND, SUBCATEGORY,
           SKILL_LEVEL, DISCIPLINE, GENDER, PRICE, PRODUCT_TYPE
    FROM CATALOG_SEARCH_DB.DATA.PRODUCTS
    WHERE CATEGORY = 'Accessories'
  );

-- =============================================================================
-- VERIFY SEARCH SERVICES
-- =============================================================================
SHOW CORTEX SEARCH SERVICES IN SCHEMA CATALOG_SEARCH_DB.APP;

-- =============================================================================
-- SECTION 5: GRANTS (optional — uncomment and adjust role as needed)
-- =============================================================================
-- GRANT USAGE ON DATABASE CATALOG_SEARCH_DB TO ROLE <your_role>;
-- GRANT USAGE ON SCHEMA CATALOG_SEARCH_DB.APP TO ROLE <your_role>;
-- GRANT USAGE ON SCHEMA CATALOG_SEARCH_DB.DATA TO ROLE <your_role>;
-- GRANT SELECT ON ALL TABLES IN SCHEMA CATALOG_SEARCH_DB.DATA TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.EQUIPMENT_SEARCH TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.APPAREL_SEARCH TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.PROTECTION_SEARCH TO ROLE <your_role>;
-- GRANT USAGE ON CORTEX SEARCH SERVICE CATALOG_SEARCH_DB.APP.ACCESSORIES_SEARCH TO ROLE <your_role>;