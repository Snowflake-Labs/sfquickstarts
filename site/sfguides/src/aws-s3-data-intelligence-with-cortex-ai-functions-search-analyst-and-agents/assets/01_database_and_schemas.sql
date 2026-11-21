/*=============================================================================
  01 - DATABASE, SCHEMAS & WAREHOUSE
  Healthcare AI Intelligence Pipeline

  Creates the core database structure:
    - HEALTHCARE_AI_DEMO database
    - RAW schema       : file metadata landing zone (Snowpipe -> FILES_LOG)
    - PROCESSED schema : AI-enriched intelligence tables (PDF, TXT, Audio)
    - ANALYTICS schema : structured data, views, semantic view, agent

  Run this FIRST. Everything else depends on these objects.
=============================================================================*/

USE ROLE ACCOUNTADMIN;

-----------------------------------------------------------------------
-- 1. DATABASE
-----------------------------------------------------------------------
CREATE OR REPLACE DATABASE HEALTHCARE_AI_DEMO
  COMMENT = 'Healthcare AI Intelligence Pipeline: PDF, TXT, and audio files processed with 11 Cortex AI functions';

-----------------------------------------------------------------------
-- 2. SCHEMAS
-----------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.RAW
  COMMENT = 'Landing zone for raw file metadata from S3 via Snowpipe';

CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.PROCESSED
  COMMENT = 'AI-enriched intelligence tables — one per file type (PDF, TXT, Audio)';

CREATE SCHEMA IF NOT EXISTS HEALTHCARE_AI_DEMO.ANALYTICS
  COMMENT = 'Structured data, analytics views, semantic view, Cortex Search, and Agent';

-----------------------------------------------------------------------
-- 3. WAREHOUSE
-----------------------------------------------------------------------
CREATE OR REPLACE WAREHOUSE HEALTHCARE_AI_WH
  WAREHOUSE_SIZE      = 'XSMALL'
  AUTO_SUSPEND        = 60
  AUTO_RESUME         = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for Healthcare AI pipeline processing';

USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 4. VERIFY
-----------------------------------------------------------------------
SHOW SCHEMAS IN DATABASE HEALTHCARE_AI_DEMO;
