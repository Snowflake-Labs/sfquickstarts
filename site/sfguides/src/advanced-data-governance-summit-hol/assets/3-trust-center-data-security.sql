
/***************************************************************************************************
 Advanced Data Governance: AI-Powered Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 3 — Verifying Sensitive Data in the Trust Center (Data Governor Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL — new step
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Overview — What This Step Covers

  The Trust Center Data Security tab (GA: April 2026) provides a consolidated,
  no-SQL view of:
    - How many objects contain sensitive data (PII, PCI, PHI)
    - Which classification recommendations are pending review
    - Whether sensitive columns have masking policies attached
    - Who can access sensitive data (Entitlement Report)

  In this step you will:
    1. Navigate the Trust Center Data Security dashboard (UI walkthrough)
    2. Review classification results using SQL (mirrors what the dashboard shows)
    3. Walk through the "Objects that need review" workflow
    4. Enable and query the Sensitive Data Entitlement Report
    5. Run a governance gap analysis: sensitive columns without masking policies

  PREREQUISITE: Step 2 must be completed before Trust Center shows results.
  Classification data may take a few minutes to appear in ACCOUNT_USAGE.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;


/*----------------------------------------------------------------------------------
Step 3.1 — Navigate the Trust Center Data Security Tab

  UI NAVIGATION:
    Snowsight left navigation → Governance & Security → Trust Center
    Select the "Data Security" tab

  WHAT YOU WILL SEE ON THE DASHBOARD:
    ┌────────────────────────────────────────────────────────────────────┐
    │  Data Security Dashboard                                          │
    │                                                                   │
    │  Sensitive Objects      PII       PCI       PHI                  │
    │  ─────────────────      ─────     ─────     ─────                │
    │  [total count]          [count]   [count]   [count]              │
    │                                                                   │
    │  Objects that need review: [N tables pending]                    │
    │  Classification errors:    [0]                                   │
    │                                                                   │
    │  Policy Coverage: [% of sensitive objects with masking]          │
    └────────────────────────────────────────────────────────────────────┘

  The tiles count tables and columns where AI detected PII, PCI, or PHI data.
  After running Step 2, you should see the CUSTOMER table and its columns here.
----------------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------------
Step 3.2 — SQL: Verify Classification Results

  These queries read from SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST —
  the same underlying view the Trust Center dashboard reads.

  NOTE: ACCOUNT_USAGE has up to 3-hour latency. If results are empty, you can
  also query HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS (no latency)
  as shown in Step 2.
----------------------------------------------------------------------------------*/

-- Full classification results for HRZN_DB
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    TAG_NAME,
    TAG_VALUE,
    CLASSIFICATION_OUTCOME
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
WHERE TABLE_DATABASE = 'HRZN_DB'
ORDER BY TABLE_NAME, COLUMN_NAME;

-- PII / PCI / PHI breakdown (mirrors the Trust Center dashboard tiles)
SELECT
    TAG_VALUE                      AS CLASSIFICATION_LEVEL,
    COUNT(DISTINCT COLUMN_NAME)    AS COLUMN_COUNT,
    COUNT(DISTINCT TABLE_NAME)     AS TABLE_COUNT
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
WHERE TABLE_DATABASE = 'HRZN_DB'
GROUP BY TAG_VALUE
ORDER BY COLUMN_COUNT DESC;

-- Which columns have each classification level? (sorted by sensitivity)
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    TAG_VALUE AS CLASSIFICATION_LEVEL
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
WHERE TABLE_DATABASE = 'HRZN_DB'
ORDER BY
    CASE TAG_VALUE
        WHEN 'PII'        THEN 1
        WHEN 'RESTRICTED' THEN 2
        WHEN 'SENSITIVE'  THEN 3
        WHEN 'INTERNAL'   THEN 4
        WHEN 'PUBLIC'     THEN 5
        ELSE 6
    END,
    TABLE_NAME,
    COLUMN_NAME;

-- Information Schema alternative (instant — no ACCOUNT_USAGE latency)
-- Use this if ACCOUNT_USAGE is not yet populated
SELECT
    COLUMN_NAME,
    TAG_NAME,
    TAG_VALUE AS CLASSIFICATION_LEVEL
FROM TABLE(
    HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
        'HRZN_DB.HRZN_SCH.CUSTOMER',
        'table'
    )
)
WHERE TAG_NAME = 'DATA_CLASSIFICATION'
ORDER BY
    CASE TAG_VALUE
        WHEN 'PII'        THEN 1
        WHEN 'RESTRICTED' THEN 2
        WHEN 'SENSITIVE'  THEN 3
        ELSE 4
    END;


/*----------------------------------------------------------------------------------
Step 3.3 — UI: Objects That Need Review

  When classification runs with auto_tag=true (as in our profile), tags are
  applied automatically. However, Trust Center also shows any objects where
  Snowflake has recommendations but is waiting for you to confirm them.

  UI STEPS:
    1. On the Data Security Dashboard, select the "Objects that need review" tile
    2. Use the search and Database filter to find CUSTOMER
    3. For each column, inspect:
         CLASSIFICATION CATEGORY  — what AI detected
         TAGS                     — system tags + your DATA_CLASSIFICATION tag
         SAMPLE VALUES            — anonymized sample to verify the detection
    4. You can:
         Accept the recommended tag       → click Approve
         Change the category              → select a different value
         Remove a recommendation          → deselect the tag
    5. Select one or more tables → click "Save and apply tags to selected tables"

  WHAT TO LOOK FOR:
    - EMAIL, SSN, CREDITCARD should show CLASSIFICATION_LEVEL = PII
    - PHONE_NUMBER, BIRTHDATE should show RESTRICTED
    - FIRST_NAME, LAST_NAME, STREET_ADDRESS, CITY, STATE, ZIP → SENSITIVE
    - JOB, COMPANY → INTERNAL
    - ID → PUBLIC
----------------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------------
Step 3.4 — Sensitive Data Entitlement Report

  The Entitlement Report generates a view (SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT)
  that lists every user who has a role granting access to tables with sensitive data.

  UI STEPS TO ENABLE:
    1. Trust Center → Data Security → Settings tab
    2. In the "Reporting" section, find "Sensitive Data Entitlement Report"
    3. Click Enable
    4. Select report cadence: Daily (recommended for summit demo)
    5. Click "Enable report"
    6. Click "Run now" to generate immediately
    7. Wait ~30 seconds, then query the results below

  REQUIRED ROLE: HRZN_DATA_GOVERNOR has DATA_SECURITY_ADMIN application role
                 (granted in 0-lab-setup.sql)
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;

-- Who can access sensitive data tables and with what privilege?
SELECT DISTINCT
    USER_NAME,
    TABLE_CATALOG,
    TABLE_SCHEMA,
    TABLE_NAME,
    PRIVILEGE
FROM SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT
ORDER BY USER_NAME, TABLE_NAME, PRIVILEGE;

-- Which roles have the broadest access to sensitive tables?
SELECT
    ROLE_NAME,
    COUNT(DISTINCT TABLE_NAME)           AS sensitive_tables_accessible,
    LISTAGG(DISTINCT PRIVILEGE, ', ')    AS privileges
FROM SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT
GROUP BY ROLE_NAME
ORDER BY sensitive_tables_accessible DESC;

-- Which sensitive tables have the most users with access?
SELECT
    TABLE_CATALOG || '.' || TABLE_SCHEMA || '.' || TABLE_NAME  AS full_table_name,
    COUNT(DISTINCT USER_NAME)                                   AS user_count,
    COUNT(DISTINCT ROLE_NAME)                                   AS role_count,
    LISTAGG(DISTINCT PRIVILEGE, ', ')                           AS privileges
FROM SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT
GROUP BY TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME
ORDER BY user_count DESC;

-- List entitlement report runs
SELECT DISTINCT RUN_ID, CREATED_TIME
FROM SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT
ORDER BY CREATED_TIME DESC;


/*----------------------------------------------------------------------------------
Step 3.5 — Governance Gap Analysis

  This query identifies classified columns that do NOT have an active masking policy.
  These represent governance gaps — data that is identified as sensitive but not yet
  protected. This is the same gap analysis shown in the Trust Center policy coverage tile.
----------------------------------------------------------------------------------*/

-- Sensitive columns without active masking policies
SELECT
    dc.TABLE_NAME,
    dc.COLUMN_NAME,
    dc.TAG_VALUE                                                      AS SENSITIVITY_LEVEL,
    CASE
        WHEN pr.REF_COLUMN_NAME IS NOT NULL THEN 'Protected'
        ELSE 'UNPROTECTED — no masking policy'
    END                                                               AS POLICY_STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST dc
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES pr
    ON  dc.TABLE_NAME    = SPLIT_PART(pr.REF_ENTITY_NAME, '.', 3)
    AND dc.COLUMN_NAME   = pr.REF_COLUMN_NAME
    AND pr.POLICY_KIND   = 'MASKING_POLICY'
    AND pr.POLICY_STATUS = 'ACTIVE'
WHERE dc.TABLE_DATABASE = 'HRZN_DB'
ORDER BY
    CASE dc.TAG_VALUE
        WHEN 'PII'        THEN 1
        WHEN 'RESTRICTED' THEN 2
        WHEN 'SENSITIVE'  THEN 3
        ELSE 4
    END,
    dc.TABLE_NAME,
    dc.COLUMN_NAME;

-- High-level coverage score: what % of sensitive objects are protected?
WITH sensitive_objects AS (
    SELECT DISTINCT TABLE_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
    WHERE TABLE_DATABASE = 'HRZN_DB'
      AND TAG_VALUE IN ('PII', 'RESTRICTED', 'SENSITIVE')
),
protected_objects AS (
    SELECT DISTINCT SPLIT_PART(REF_ENTITY_NAME, '.', 3) AS TABLE_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
    WHERE SPLIT_PART(REF_ENTITY_NAME, '.', 1) = 'HRZN_DB'
      AND POLICY_KIND   = 'MASKING_POLICY'
      AND POLICY_STATUS = 'ACTIVE'
)
SELECT
    COUNT(DISTINCT so.TABLE_NAME)                                    AS total_sensitive_tables,
    COUNT(DISTINCT po.TABLE_NAME)                                    AS protected_tables,
    ROUND(COUNT(DISTINCT po.TABLE_NAME) * 100.0
          / NULLIF(COUNT(DISTINCT so.TABLE_NAME), 0), 1)            AS pct_coverage,
    CASE
        WHEN COUNT(DISTINCT po.TABLE_NAME) * 100.0
             / NULLIF(COUNT(DISTINCT so.TABLE_NAME), 0) >= 80 THEN 'Strong'
        WHEN COUNT(DISTINCT po.TABLE_NAME) * 100.0
             / NULLIF(COUNT(DISTINCT so.TABLE_NAME), 0) >= 50 THEN 'Moderate'
        ELSE 'Needs Improvement'
    END                                                              AS coverage_grade
FROM sensitive_objects so
LEFT JOIN protected_objects po ON so.TABLE_NAME = po.TABLE_NAME;

-- Active policies protecting HRZN_DB objects
SELECT
    POLICY_KIND,
    POLICY_NAME,
    REF_ENTITY_NAME     AS PROTECTED_OBJECT,
    REF_COLUMN_NAME     AS PROTECTED_COLUMN,
    POLICY_STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
WHERE SPLIT_PART(REF_ENTITY_NAME, '.', 1) = 'HRZN_DB'
  AND POLICY_STATUS = 'ACTIVE'
ORDER BY POLICY_KIND, REF_ENTITY_NAME;

/*
  KEY TAKEAWAYS — Step 3:

  TRUST CENTER DATA SECURITY:
    - Provides a no-SQL dashboard showing classified objects, PII/PCI/PHI breakdown,
      and policy coverage — all in one place
    - "Objects that need review" lets data stewards confirm, adjust, or reject
      AI-generated classification recommendations
    - Classification errors surface objects that could not be classified so you
      can investigate and fix them

  ENTITLEMENT REPORT:
    - Answers "who can access my sensitive data?" at account scale
    - Stored in SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT (queryable via SQL)
    - Run on demand or on a schedule (daily, weekly, monthly, quarterly)
    - Supports deletion of historical report data for retention compliance

  GOVERNANCE GAP ANALYSIS:
    - The gap between classified columns and masked columns represents compliance risk
    - After Step 2, the gap should be zero — all tagged columns are protected via the
      tag-based masking policy
    - If gaps exist, Step 6 (Cortex Code skills) can help generate the missing policies

  Proceed to Step 4 for the access history audit trail.
*/
