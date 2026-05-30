
/***************************************************************************************************
 Advanced Data Governance: Sensitive Data Discovery and Protection at Scale
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

  PREREQUISITE: Step 2 must be completed before Trust Center shows results.
  Classification data may take a few minutes to appear in ACCOUNT_USAGE.
----------------------------------------------------------------------------------*/


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

  NOTE: Auto-Classification (attached profile) runs asynchronously. The Trust Center
  dashboard may not show results immediately after Step 2. If tiles show zero objects,
  wait 2–5 minutes and refresh the page.
----------------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------------
Step 3.2 — SQL: Verify Classification Results

  These queries read from INFORMATION_SCHEMA (immediate) and
  SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST (up to 3-hour latency).
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

-- Step 3.2a — Verify using Information Schema (immediate — no latency)
-- Shows custom DATA_CLASSIFICATION tag values applied by the classification profile
SELECT
    COLUMN_NAME,
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
        WHEN 'INTERNAL'   THEN 4
        WHEN 'PUBLIC'     THEN 5
    END, COLUMN_NAME;


-- Step 3.2b — Verify using ACCOUNT_USAGE (up to 3-hour latency)
-- NOTE: Results may be empty immediately after classification. Run later in the lab
-- or after the session if the queries below return no rows.

-- DATA_CLASSIFICATION_LATEST returns a table-level JSON payload (RESULT column).
-- LATERAL FLATTEN pivots it to one row per column.
-- This view shows Snowflake's classification recommendations (semantic/privacy category),
-- NOT the custom DATA_CLASSIFICATION tag values — use Step 3.2a for those.
SELECT
    DATABASE_NAME,
    SCHEMA_NAME,
    TABLE_NAME,
    f.key                                              AS COLUMN_NAME,
    f.value:recommendation:semantic_category::STRING   AS SEMANTIC_CATEGORY,
    f.value:recommendation:privacy_category::STRING    AS PRIVACY_CATEGORY,
    f.value:recommendation:confidence::STRING          AS CONFIDENCE
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST,
     LATERAL FLATTEN(INPUT => RESULT) f
WHERE f.value:recommendation IS NOT NULL
  AND DATABASE_NAME = 'HRZN_DB'
ORDER BY TABLE_NAME, COLUMN_NAME;

-- Classification summary by privacy category
SELECT
    f.value:recommendation:privacy_category::STRING    AS PRIVACY_CATEGORY,
    COUNT(*)                                           AS COLUMN_COUNT
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST,
     LATERAL FLATTEN(INPUT => RESULT) f
WHERE f.value:recommendation IS NOT NULL
  AND DATABASE_NAME = 'HRZN_DB'
GROUP BY PRIVACY_CATEGORY
ORDER BY COLUMN_COUNT DESC;


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


/*
  KEY TAKEAWAYS — Step 3:

  TRUST CENTER DATA SECURITY:
    - Provides a no-SQL dashboard showing classified objects, PII/PCI/PHI breakdown,
      and policy coverage — all in one place
    - "Objects that need review" lets data stewards confirm, adjust, or reject
      classification recommendations
    - Classification errors surface objects that could not be classified so you
      can investigate and fix them

  ENTITLEMENT REPORT:
    - Answers "who can access my sensitive data?" at account scale
    - Stored in SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT (queryable via SQL)
    - Run on demand or on a schedule (daily, weekly, monthly, quarterly)
    - Supports deletion of historical report data for retention compliance

  Proceed to Step 4 for the access history audit trail.
*/
