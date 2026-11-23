-- ============================================================================
-- CoCo CLI Hands-on Lab — Reset (run BETWEEN lab sessions)
-- ============================================================================
-- Drops all demo-created objects inside each participant schema but keeps
-- the schemas themselves, the shared SOURCE_DATA, and the role/warehouse
-- intact.  After running this, participants can start the lab fresh.
--
-- Run as: ACCOUNTADMIN  (or SYSADMIN with ownership on COCO_WORKSHOP)
-- ============================================================================

USE ROLE SYSADMIN;
USE DATABASE COCO_WORKSHOP;
USE WAREHOUSE COCO_WORKSHOP_WH;

-- ============================================================================
-- 1. DROP DEMO OBJECTS IN EVERY USER SCHEMA
-- ============================================================================
-- The lab creates these objects (in reverse dependency order):
--   - Agent:          AP_ANALYTICS_ASSISTANT   (Demo 3)
--   - Semantic View:  SV_AP_ANALYTICS          (Demo 3)
--   - Dynamic Table:  SILVER_AP_INVOICES       (Demo 1 & 2)
--   - Misc tables:    __SMOKE_TEST, etc.
--
-- This procedure loops through all USER_* schemas and drops known objects.
-- ============================================================================

CREATE OR REPLACE PROCEDURE COCO_WORKSHOP.SOURCE_DATA.RESET_USER_SCHEMAS()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
  schema_name VARCHAR;
  cnt         INT DEFAULT 0;
  cur CURSOR FOR
    SELECT SCHEMA_NAME
      FROM COCO_WORKSHOP.INFORMATION_SCHEMA.SCHEMATA
     WHERE SCHEMA_NAME LIKE 'USER_%'
     ORDER BY SCHEMA_NAME;
BEGIN
  OPEN cur;
  FOR rec IN cur DO
    schema_name := rec.SCHEMA_NAME;

    -- Demo 3: Agent
    EXECUTE IMMEDIATE 'DROP AGENT IF EXISTS COCO_WORKSHOP.' || :schema_name || '.AP_ANALYTICS_ASSISTANT';

    -- Demo 3: Semantic View
    EXECUTE IMMEDIATE 'DROP SEMANTIC VIEW IF EXISTS COCO_WORKSHOP.' || :schema_name || '.SV_AP_ANALYTICS';

    -- Demo 1 & 2: Dynamic Table
    EXECUTE IMMEDIATE 'DROP DYNAMIC TABLE IF EXISTS COCO_WORKSHOP.' || :schema_name || '.SILVER_AP_INVOICES';

    -- Cleanup: any smoke-test tables
    EXECUTE IMMEDIATE 'DROP TABLE IF EXISTS COCO_WORKSHOP.' || :schema_name || '.__SMOKE_TEST';

    cnt := cnt + 1;
  END FOR;
  CLOSE cur;

  RETURN 'Reset ' || cnt::STRING || ' user schemas — demo objects dropped';
END;
$$;

CALL COCO_WORKSHOP.SOURCE_DATA.RESET_USER_SCHEMAS();

-- ============================================================================
-- 2. VERIFY CLEAN STATE
-- ============================================================================

-- Each user schema should now be empty (no tables, views, DTs, agents)
SELECT s.SCHEMA_NAME,
       COUNT(t.TABLE_NAME) AS REMAINING_OBJECTS
  FROM COCO_WORKSHOP.INFORMATION_SCHEMA.SCHEMATA s
  LEFT JOIN COCO_WORKSHOP.INFORMATION_SCHEMA.TABLES t
    ON s.SCHEMA_NAME = t.TABLE_SCHEMA
 WHERE s.SCHEMA_NAME LIKE 'USER_%'
 GROUP BY s.SCHEMA_NAME
 ORDER BY s.SCHEMA_NAME;

-- SOURCE_DATA should still have all bronze tables
SELECT TABLE_NAME, ROW_COUNT
  FROM COCO_WORKSHOP.INFORMATION_SCHEMA.TABLES
 WHERE TABLE_SCHEMA = 'SOURCE_DATA'
 ORDER BY TABLE_NAME;

SELECT 'Lab reset complete — ready for next session' AS STATUS;
