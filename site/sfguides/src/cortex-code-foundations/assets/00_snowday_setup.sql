-- ============================================================================
-- Snowday Setup: Database, Schema, Warehouse, Roles
-- Run this ONCE before any vignettes
-- ============================================================================

USE ROLE SYSADMIN;

-- Database
CREATE DATABASE IF NOT EXISTS COCO_WORKSHOP;

-- Schemas
-- PIPELINE_LAB: legacy / vignette-owned schema (kept for backwards compatibility)
-- SOURCE_DATA: shared, read-only inputs for participants
CREATE SCHEMA IF NOT EXISTS COCO_WORKSHOP.PIPELINE_LAB;
CREATE SCHEMA IF NOT EXISTS COCO_WORKSHOP.SOURCE_DATA;

-- Warehouse
CREATE WAREHOUSE IF NOT EXISTS COCO_WORKSHOP_WH
  WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Snowday workshop warehouse for Cortex Code demos';

-- Set context
USE DATABASE COCO_WORKSHOP;
USE SCHEMA PIPELINE_LAB;
USE WAREHOUSE COCO_WORKSHOP_WH;

-- ============================================================================
-- Optional: Grant access to a workshop role
-- Uncomment and customize if using a dedicated role for participants
-- ============================================================================

-- USE ROLE SECURITYADMIN;
-- CREATE ROLE IF NOT EXISTS COCO_WORKSHOP_ROLE;
-- GRANT USAGE ON DATABASE COCO_WORKSHOP TO ROLE COCO_WORKSHOP_ROLE;
-- GRANT USAGE ON SCHEMA COCO_WORKSHOP.PIPELINE_LAB TO ROLE COCO_WORKSHOP_ROLE;
-- GRANT ALL ON SCHEMA COCO_WORKSHOP.PIPELINE_LAB TO ROLE COCO_WORKSHOP_ROLE;
-- GRANT USAGE ON WAREHOUSE COCO_WORKSHOP_WH TO ROLE COCO_WORKSHOP_ROLE;
-- GRANT OPERATE ON WAREHOUSE COCO_WORKSHOP_WH TO ROLE COCO_WORKSHOP_ROLE;

-- ============================================================================
-- Tags (used in Vignette 4: Guardrails Pack)
-- Pre-create tag objects so participants can apply them during the demo
-- ============================================================================

CREATE TAG IF NOT EXISTS COCO_WORKSHOP.PIPELINE_LAB.COST_CENTER
  COMMENT = 'Cost attribution tag for chargeback tracking';

CREATE TAG IF NOT EXISTS COCO_WORKSHOP.PIPELINE_LAB.DATA_DOMAIN
  COMMENT = 'Business domain tag for data classification';

CREATE TAG IF NOT EXISTS COCO_WORKSHOP.PIPELINE_LAB.PIPELINE
  COMMENT = 'Pipeline identifier tag for operational tracking';

-- ============================================================================
-- Verify setup
-- ============================================================================

SELECT 'Setup complete' AS STATUS,
       CURRENT_DATABASE() AS DATABASE,
       CURRENT_SCHEMA() AS SCHEMA,
       CURRENT_WAREHOUSE() AS WAREHOUSE;
