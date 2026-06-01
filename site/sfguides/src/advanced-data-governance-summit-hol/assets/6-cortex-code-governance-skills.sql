
/***************************************************************************************************
 Advanced Data Governance: Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 6 — Cortex Code Governance Skills (Data Governor Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL — new step
                                         (Expands on original Horizon Lab v2.0 Section 6
                                          by Severin Gassauer)
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Overview — What This Step Covers

  Cortex Code is Snowflake's AI-powered coding assistant built into Snowsight and
  available as a desktop IDE (CoCo). It ships with built-in data governance skills
  that let you accomplish governance tasks in plain English — no SQL required.

  The governance skills query ACCOUNT_USAGE views using an embedded semantic model,
  generate and execute SQL automatically, and interpret results in context.

  SKILL DOMAINS IN THIS LAB:
    1. General Data Governance      — audit, compliance posture, role hierarchy
    2. Sensitive Data Classification — discover PII, analyze results, set up profiles
    3. Data Protection Policies     — create/audit masking and row access policies

  OPEN CORTEX CODE:
    - Snowsight: Click the Cortex Code icon (✨) in the left navigation sidebar
    - Desktop app: Launch CoCo and connect to your Snowflake account

  ACCESS REQUIREMENTS (already granted in 0-lab-setup.sql):
    HRZN_DATA_GOVERNOR has:
      GOVERNANCE_VIEWER, OBJECT_VIEWER, USAGE_VIEWER, SECURITY_VIEWER
      (required for all skill queries against ACCOUNT_USAGE)

  IMPORTANT: Run each Cortex Code prompt in the chat panel, then run the
  SQL verification queries below to confirm the skill's output.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

-- Verify governance metadata is available before starting
SELECT
    TAG_NAME, TAG_VALUE, OBJECT_NAME, DOMAIN, COUNT(*) AS count
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
GROUP BY TAG_NAME, TAG_VALUE, OBJECT_NAME, DOMAIN
LIMIT 10;

SELECT
    POLICY_KIND, POLICY_NAME, REF_ENTITY_NAME, REF_COLUMN_NAME, POLICY_STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
WHERE POLICY_DB = 'HRZN_DB'
LIMIT 10;


/*===========================================================================
  SECTION 6.1 — GOVERNANCE MATURITY ASSESSMENT

  Use Cortex Code to assess the overall governance posture of HRZN_DB.
  The General Data Governance skill queries ACCOUNT_USAGE to answer
  compliance questions and generate a health report.
===========================================================================*/

/*
  CORTEX CODE PROMPTS — paste each into the Cortex Code chat panel:

  ── Prompt 1 (Broad overview) ──────────────────────────────────────────
  "What is the governance coverage for HRZN_DB?
   Which tables have PII but no masking policy applied?"

  ── Prompt 2 (Health report) ───────────────────────────────────────────
  "Generate a data governance health report for the HRZN_DB database.
   Include: tables with sensitive data, policy coverage percentage, and
   the top governance risks."

  ── Prompt 3 (Maturity score) ──────────────────────────────────────────
  "Show me a governance maturity score for HRZN_DB. What is well-protected
   and what still needs attention?"

  OBSERVE: Cortex Code queries TAG_REFERENCES and POLICY_REFERENCES
  and synthesizes the results into a readable governance health summary.
*/

-- SQL EQUIVALENT: Governance maturity score (use to verify Cortex Code output)
WITH sensitive_tables AS (
    SELECT DISTINCT OBJECT_NAME AS TABLE_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
    WHERE OBJECT_DATABASE = 'HRZN_DB'
      AND TAG_NAME  = 'DATA_CLASSIFICATION'
      AND TAG_VALUE IN ('PII', 'RESTRICTED', 'SENSITIVE')
),
protected_tables AS (
    SELECT DISTINCT SPLIT_PART(REF_ENTITY_NAME, '.', 3) AS TABLE_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
    WHERE SPLIT_PART(REF_ENTITY_NAME, '.', 1) = 'HRZN_DB'
      AND POLICY_KIND   = 'MASKING_POLICY'
      AND POLICY_STATUS = 'ACTIVE'
)
SELECT
    COUNT(DISTINCT st.TABLE_NAME)                                          AS total_sensitive_tables,
    COUNT(DISTINCT pt.TABLE_NAME)                                          AS tables_with_masking,
    ROUND(COUNT(DISTINCT pt.TABLE_NAME) * 100.0
          / NULLIF(COUNT(DISTINCT st.TABLE_NAME), 0), 1)                  AS pct_coverage,
    CASE
        WHEN COUNT(DISTINCT pt.TABLE_NAME) * 100.0
             / NULLIF(COUNT(DISTINCT st.TABLE_NAME), 0) >= 80 THEN 'Strong'
        WHEN COUNT(DISTINCT pt.TABLE_NAME) * 100.0
             / NULLIF(COUNT(DISTINCT st.TABLE_NAME), 0) >= 50 THEN 'Moderate'
        ELSE 'Needs Improvement'
    END                                                                    AS governance_maturity
FROM sensitive_tables st
LEFT JOIN protected_tables pt ON st.TABLE_NAME = pt.TABLE_NAME;

-- Tables with PII but no masking policy
WITH pii_tables AS (
    SELECT DISTINCT
        OBJECT_DATABASE, OBJECT_SCHEMA, OBJECT_NAME,
        TAG_VALUE AS pii_type
    FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
    WHERE TAG_NAME IN ('SEMANTIC_CATEGORY', 'SNOWFLAKE.CORE.SEMANTIC_CATEGORY')
      AND TAG_VALUE IN ('EMAIL', 'US_SOCIAL_SECURITY_NUMBER', 'PHONE_NUMBER', 'CREDIT_CARD_NUMBER')
      AND OBJECT_DATABASE = 'HRZN_DB'
      AND DOMAIN = 'COLUMN'
),
masked_tables AS (
    SELECT DISTINCT SPLIT_PART(REF_ENTITY_NAME, '.', 3) AS table_name
    FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
    WHERE POLICY_KIND   = 'MASKING_POLICY'
      AND POLICY_STATUS = 'ACTIVE'
)
SELECT
    p.OBJECT_DATABASE || '.' || p.OBJECT_SCHEMA || '.' || p.OBJECT_NAME AS full_table_name,
    LISTAGG(DISTINCT p.pii_type, ', ')                                   AS pii_types_detected,
    'HIGH RISK: No masking policy'                                       AS governance_status
FROM pii_tables p
LEFT JOIN masked_tables m ON p.OBJECT_NAME = m.table_name
WHERE m.table_name IS NULL
GROUP BY p.OBJECT_DATABASE, p.OBJECT_SCHEMA, p.OBJECT_NAME;


/*===========================================================================
  SECTION 6.2 — AI CLASSIFICATION VIA CORTEX CODE SKILLS

  The sensitive data classification skill can scan tables for PII, analyze
  existing classification results, and even help create classification profiles
  — interactively, using plain English.
===========================================================================*/

/*
  CORTEX CODE PROMPTS:

  ── Prompt 4 (Scan unclassified table) ────────────────────────────────
  "Scan HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS for PII and sensitive data.
   Which columns appear to contain sensitive information?"

  ── Prompt 5 (Analyze results) ────────────────────────────────────────
  "Show me all columns classified as sensitive data in HRZN_DB.
   Group them by sensitivity category and tell me which tables have the most
   sensitive columns."

  ── Prompt 6 (Stale classification check) ─────────────────────────────
  "Which tables in HRZN_DB need re-classification because their classification
   results are older than 30 days?"

  ── Prompt 7 (Custom classifier guidance) ─────────────────────────────
  "Help me create a custom classifier for employee IDs that match the
   pattern EMP-XXXXX and store it in HRZN_DB.CLASSIFIERS."

  OBSERVE: For Prompt 4, Cortex Code generates and executes a SYSTEM$CLASSIFY
  call on CUSTOMER_ORDERS. For Prompt 5, it queries TAG_REFERENCES.
*/

-- After Cortex Code runs classification, check the custom DATA_CLASSIFICATION tags
SELECT
    OBJECT_NAME    AS TABLE_NAME,
    COLUMN_NAME,
    TAG_VALUE      AS SENSITIVITY
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
  AND OBJECT_NAME     = 'CUSTOMER_ORDERS'
  AND TAG_NAME        = 'DATA_CLASSIFICATION'
ORDER BY COLUMN_NAME;

-- Summary: which tables have the most sensitive columns?
SELECT
    OBJECT_NAME                            AS TABLE_NAME,
    COUNT(*)                               AS sensitive_column_count,
    LISTAGG(DISTINCT TAG_VALUE, ', ')      AS sensitivity_levels,
    LISTAGG(COLUMN_NAME, ', ')             AS sensitive_columns
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
  AND TAG_NAME        = 'DATA_CLASSIFICATION'
  AND DOMAIN          = 'COLUMN'
GROUP BY OBJECT_NAME
ORDER BY sensitive_column_count DESC;


/*===========================================================================
  SECTION 6.3 — POLICY CREATION AND AUDIT VIA CORTEX CODE SKILLS

  The data protection policies skill:
    - Creates masking policies using Snowflake best practices (IS_ROLE_IN_SESSION,
      memoizable functions, ABAC patterns)
    - Audits existing policies for security anti-patterns
    - Generates compliance-specific policy templates (GDPR, HIPAA, PCI-DSS)

  KEY TEACHING MOMENT:
  The masking policies we created in Step 2 use CURRENT_ROLE(). While functional,
  Snowflake best practice recommends IS_ROLE_IN_SESSION() because:
    - CURRENT_ROLE() evaluates the active primary role only
    - IS_ROLE_IN_SESSION() evaluates all active roles (including secondary roles
      activated with USE SECONDARY ROLES ALL)
  Cortex Code will flag this as an anti-pattern when you ask it to audit policies.
===========================================================================*/

/*
  CORTEX CODE PROMPTS:

  ── Prompt 8 (Policy audit) ───────────────────────────────────────────
  "Audit all masking policies in HRZN_DB.TAG_SCHEMA.
   Are there any security anti-patterns or best practice violations?"

  ── Prompt 9 (Anti-pattern detection) ─────────────────────────────────
  "Review my masking policies. Do they use IS_ROLE_IN_SESSION() instead
   of CURRENT_ROLE()? Flag any that use CURRENT_ROLE() as an anti-pattern."

  EXPECTED CORTEX CODE OUTPUT FOR PROMPT 9:
    Cortex Code will retrieve the policy DDL and flag the CURRENT_ROLE()
    usage in DATA_CLASSIFICATION_MASK_STRING (and other types) as an
    anti-pattern. It will suggest replacing:
      WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
    with:
      WHEN IS_ROLE_IN_SESSION('HRZN_DATA_GOVERNOR')
        OR IS_ROLE_IN_SESSION('ACCOUNTADMIN')

  ── Prompt 10 (Policy creation — GDPR) ────────────────────────────────
  "Create a GDPR-compliant masking policy for the SSN column in
   HRZN_DB.HRZN_SCH.CUSTOMER. Use IS_ROLE_IN_SESSION() best practice.
   Store the policy in HRZN_DB.TAG_SCHEMA."

  ── Prompt 11 (ABAC pattern) ──────────────────────────────────────────
  "What is the recommended Attribute-Based Access Control (ABAC) pattern
   for masking in Snowflake? Show me an example for role-based data access."

  ── Prompt 12 (Compliance report) ─────────────────────────────────────
  "Generate a PCI-DSS compliance checklist for my current masking policies
   in HRZN_DB. Which requirements are met and which are gaps?"

  NOTE: Cortex Code generates complete, runnable CREATE MASKING POLICY SQL.
  Review the generated SQL before applying it to any table.
*/

-- SQL: View policy DDL to see the CURRENT_ROLE() vs IS_ROLE_IN_SESSION() issue
SHOW MASKING POLICIES IN SCHEMA HRZN_DB.TAG_SCHEMA;

-- Retrieve the DDL of the string masking policy
SELECT GET_DDL('POLICY', 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING');

/*
  After Cortex Code generates an improved policy, apply it with:

  CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING_V2
  AS (VAL STRING)
  RETURNS STRING ->
  CASE
      WHEN IS_ROLE_IN_SESSION('HRZN_DATA_GOVERNOR')
        OR IS_ROLE_IN_SESSION('ACCOUNTADMIN')
          THEN VAL
      WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
          THEN '***PII-REDACTED***'
      ...
  END;

  Then update the tag attachment:
  ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
      SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING_V2;
*/


/*===========================================================================
  SECTION 6.4 — COMPLIANCE AUDIT VIA CORTEX CODE SKILLS

  The General Data Governance skill answers compliance and access audit questions
  by querying ACCOUNT_USAGE views. Instead of hand-crafting complex joins,
  ask Cortex Code in plain English.
===========================================================================*/

/*
  CORTEX CODE PROMPTS:

  ── Prompt 13 (Access audit) ──────────────────────────────────────────
  "Who has accessed the HRZN_DB.HRZN_SCH.CUSTOMER table in the last 30 days?
   Show the user, role, and number of queries."

  ── Prompt 14 (PII access) ────────────────────────────────────────────
  "List all users who have run queries against tables containing PII in HRZN_DB
   in the last 7 days."

  ── Prompt 15 (After-hours activity) ──────────────────────────────────
  "Were there any queries on HRZN_DB sensitive tables outside of business hours
   (before 8am or after 7pm UTC) in the last 7 days?"

  ── Prompt 16 (Tag inventory) ─────────────────────────────────────────
  "Show me all tags applied to columns in HRZN_DB. List them by tag name and value,
   and tell me which columns each tag is applied to."

  ── Prompt 17 (Policy inventory) ──────────────────────────────────────
  "What row access policies are currently active in HRZN_DB?
   Which tables do they protect and what is the policy logic?"

  ── Prompt 18 (Role analysis) ─────────────────────────────────────────
  "Which roles in my Snowflake account have the APPLY MASKING POLICY privilege?
   Show me the full role hierarchy for HRZN_DATA_GOVERNOR."
*/

-- SQL EQUIVALENTS (what Cortex Code generates — run these to verify skill output):

-- Who accessed CUSTOMER recently?
SELECT
    qh.USER_NAME,
    qh.ROLE_NAME,
    qh.START_TIME::DATE                    AS access_date,
    COUNT(DISTINCT qh.QUERY_ID)            AS query_count
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
WHERE qh.QUERY_TEXT ILIKE '%HRZN_DB.HRZN_SCH.CUSTOMER%'
  AND qh.START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
  AND qh.EXECUTION_STATUS = 'SUCCESS'
GROUP BY qh.USER_NAME, qh.ROLE_NAME, qh.START_TIME::DATE
ORDER BY access_date DESC, query_count DESC;

-- Who accessed PII data in the last 7 days?
SELECT
    qh.USER_NAME,
    qh.ROLE_NAME,
    qh.START_TIME::DATE                                AS access_date,
    COUNT(DISTINCT qh.QUERY_ID)                        AS pii_query_count,
    LISTAGG(DISTINCT f.value:objectName::STRING, ', ') AS pii_tables_accessed
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
JOIN SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY ah ON qh.QUERY_ID = ah.QUERY_ID,
LATERAL FLATTEN(input => ah.DIRECT_OBJECTS_ACCESSED) f
WHERE f.value:objectName::STRING IN (
    SELECT DISTINCT OBJECT_DATABASE || '.' || OBJECT_SCHEMA || '.' || OBJECT_NAME
    FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
    WHERE TAG_NAME IN ('SEMANTIC_CATEGORY', 'SNOWFLAKE.CORE.SEMANTIC_CATEGORY')
      AND TAG_VALUE IN ('EMAIL', 'US_SOCIAL_SECURITY_NUMBER', 'PHONE_NUMBER')
      AND OBJECT_DATABASE = 'HRZN_DB'
)
AND qh.START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY qh.USER_NAME, qh.ROLE_NAME, qh.START_TIME::DATE
ORDER BY access_date DESC, pii_query_count DESC;

-- Tag distribution across HRZN_DB
SELECT
    TAG_NAME,
    TAG_VALUE,
    DOMAIN            AS object_type,
    COUNT(*)          AS tagged_objects,
    COUNT(DISTINCT OBJECT_NAME) AS unique_objects
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
GROUP BY TAG_NAME, TAG_VALUE, DOMAIN
ORDER BY tagged_objects DESC;

-- All active policies in HRZN_DB
SELECT
    POLICY_KIND,
    POLICY_NAME,
    REF_ENTITY_NAME   AS protected_object,
    REF_COLUMN_NAME   AS protected_column,
    POLICY_STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
WHERE SPLIT_PART(REF_ENTITY_NAME, '.', 1) = 'HRZN_DB'
  AND POLICY_STATUS = 'ACTIVE'
ORDER BY POLICY_KIND, REF_ENTITY_NAME;

-- Governance coverage by schema: what % of tables are tagged and protected?
WITH table_inventory AS (
    SELECT
        TABLE_SCHEMA,
        COUNT(*)                                          AS total_tables,
        SUM(CASE WHEN TABLE_TYPE = 'BASE TABLE' THEN 1 ELSE 0 END) AS base_tables,
        SUM(CASE WHEN TABLE_TYPE = 'VIEW'       THEN 1 ELSE 0 END) AS views
    FROM HRZN_DB.INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = 'HRZN_SCH'
    GROUP BY TABLE_SCHEMA
),
governance_stats AS (
    SELECT
        OBJECT_SCHEMA,
        COUNT(DISTINCT CASE WHEN tr.DOMAIN = 'TABLE'  THEN tr.OBJECT_NAME END) AS tagged_tables,
        COUNT(DISTINCT CASE WHEN tr.DOMAIN = 'COLUMN' THEN tr.OBJECT_NAME END) AS tables_with_tagged_columns,
        COUNT(DISTINCT CASE WHEN pr.REF_ENTITY_DOMAIN = 'TABLE'
                            THEN SPLIT_PART(pr.REF_ENTITY_NAME, '.', 3) END)   AS protected_tables
    FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES tr
    FULL OUTER JOIN SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES pr
        ON  tr.OBJECT_NAME   = SPLIT_PART(pr.REF_ENTITY_NAME, '.', 3)
        AND tr.OBJECT_SCHEMA = SPLIT_PART(pr.REF_ENTITY_NAME, '.', 2)
    WHERE tr.OBJECT_DATABASE = 'HRZN_DB'
       OR SPLIT_PART(pr.REF_ENTITY_NAME, '.', 1) = 'HRZN_DB'
    GROUP BY OBJECT_SCHEMA
)
SELECT
    ti.TABLE_SCHEMA,
    ti.total_tables,
    ti.base_tables,
    ti.views,
    COALESCE(gs.tagged_tables, 0)                                             AS tagged_tables,
    COALESCE(gs.protected_tables, 0)                                          AS protected_tables,
    ROUND(COALESCE(gs.tagged_tables, 0) * 100.0   / NULLIF(ti.total_tables, 0), 1) AS pct_tagged,
    ROUND(COALESCE(gs.protected_tables, 0) * 100.0 / NULLIF(ti.total_tables, 0), 1) AS pct_protected,
    CASE
        WHEN COALESCE(gs.protected_tables, 0) * 100.0 / NULLIF(ti.total_tables, 0) >= 80 THEN 'Excellent'
        WHEN COALESCE(gs.protected_tables, 0) * 100.0 / NULLIF(ti.total_tables, 0) >= 60 THEN 'Good'
        WHEN COALESCE(gs.protected_tables, 0) * 100.0 / NULLIF(ti.total_tables, 0) >= 40 THEN 'Fair'
        ELSE 'Needs Improvement'
    END                                                                       AS governance_grade
FROM table_inventory ti
LEFT JOIN governance_stats gs ON ti.TABLE_SCHEMA = gs.OBJECT_SCHEMA;

/*
  KEY TAKEAWAYS — Step 6:

  CORTEX CODE GOVERNANCE SKILLS:
    - Governance Maturity Skill: generates a health score and flags unprotected tables
      using TAG_REFERENCES and POLICY_REFERENCES
    - Classification Skill: runs SYSTEM$CLASSIFY, reads results, and explains detections
      in plain English — no SQL required
    - Data Protection Policies Skill: creates best-practice policies with
      IS_ROLE_IN_SESSION(), audits for anti-patterns like CURRENT_ROLE(), and generates
      compliance-specific templates (GDPR, HIPAA, PCI-DSS)
    - General Governance Skill: answers access audit questions by querying
      ACCOUNT_USAGE views through an embedded semantic model

  VALUE OF AI-ASSISTED GOVERNANCE:
    - Reduces the SQL expertise required to govern data at scale
    - Enforces best practices that are easy to miss (IS_ROLE_IN_SESSION vs CURRENT_ROLE)
    - Makes governance accessible to data stewards who are not SQL experts
    - Lets compliance teams audit governance posture without engineering support

  CORTEX CODE TIPS:
    - Be specific with fully-qualified object names (DATABASE.SCHEMA.TABLE)
    - Start with a health check prompt, then drill into specific issues
    - Review generated SQL before applying policies — Cortex Code provides an
      explanation with every SQL block it generates
    - If ACCOUNT_USAGE is not yet populated, instruct Cortex Code:
      "Check INFORMATION_SCHEMA as ACCOUNT_USAGE may not be populated yet"

  CONGRATULATIONS! You have completed the lab.
  Run 99-teardown.sql to remove all lab objects from your account.
*/
