/*=============================================================
  06 — Create Cortex Search Services
  2 services for semantic search over unstructured text
  NOTE: INCIDENT_REPORTS_SEARCH removed — data moved to Amazon S3
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- ============================================================
-- 1. SUPPLIER_COMMS_SEARCH — search supplier emails
-- ============================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE SUPPLIER_COMMS_SEARCH
  ON EMAIL_BODY
  ATTRIBUTES SUPPLIER_NAME, SUBJECT, DATE_SENT, SENDER, PRIORITY
  WAREHOUSE = SUPPLY_CHAIN_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
      EMAIL_BODY,
      SUPPLIER_NAME,
      SUBJECT,
      DATE_SENT::VARCHAR AS DATE_SENT,
      SENDER,
      PRIORITY
    FROM SUPPLIER_EMAILS
  );

-- ============================================================
-- 2. WAREHOUSE_INSPECTIONS_SEARCH — search inspection notes
-- ============================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE WAREHOUSE_INSPECTIONS_SEARCH
  ON INSPECTION_NOTES
  ATTRIBUTES INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED
  WAREHOUSE = SUPPLY_CHAIN_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
      INSPECTION_NOTES,
      INSPECTION_DATE::VARCHAR AS INSPECTION_DATE,
      INSPECTOR,
      OVERALL_RATING,
      FOLLOW_UP_REQUIRED::VARCHAR AS FOLLOW_UP_REQUIRED
    FROM WAREHOUSE_INSPECTION_NOTES
  );

-- ============================================================
-- Verify (wait 2-3 minutes for indexing before testing)
-- ============================================================

SHOW CORTEX SEARCH SERVICES IN SUPPLY_CHAIN_DEMO.PUBLIC;
