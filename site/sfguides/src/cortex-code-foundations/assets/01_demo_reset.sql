-- ============================================================================
-- Snowday Demo Reset
-- Run this BEFORE each demo to drop objects created during the previous run
-- Then re-run 00_snowday_setup.sql and 00_sample_data.sql to restore baseline
-- ============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE COCO_WORKSHOP;

-- ============================================================================
-- Drop demo-created objects in PIPELINE_LAB (reverse creation order)
-- ============================================================================

-- Agent (created in Vignette 3: Cortex Agent)
DROP AGENT IF EXISTS COCO_WORKSHOP.PIPELINE_LAB.AP_ANALYTICS_ASSISTANT;

-- Semantic View (created in Vignette 3: Semantic View)
DROP SEMANTIC VIEW IF EXISTS COCO_WORKSHOP.PIPELINE_LAB.SV_AP_ANALYTICS;

-- Silver Dynamic Table (created in Vignette 1: Pipeline Builder)
DROP DYNAMIC TABLE IF EXISTS COCO_WORKSHOP.PIPELINE_LAB.SILVER_AP_INVOICES;

-- ============================================================================
-- Drop local skill directory (run from terminal, not SQL)
-- rm -rf <your-repo>/.cortex
-- ============================================================================

-- ============================================================================
-- Verify clean state
-- ============================================================================

SHOW OBJECTS IN SCHEMA COCO_WORKSHOP.PIPELINE_LAB;
-- Expected: only the 4 BRONZE_* tables (pre-created by setup) plus tags
