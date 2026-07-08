
/***************************************************************************************************
 Advanced Data Governance: Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 6 — Access and Audit Trail (IT Admin Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL
                                         (Adapted from original Horizon Lab v2.0 by Ravi Kumar)
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Overview — What This Step Covers

  Access History tracks every query that accessed your data objects — what was
  read, what was written, when it happened, and by whom.

  This is a foundational requirement for:
    - Regulatory compliance (GDPR, HIPAA, PCI-DSS, SOX)
    - Security incident investigation
    - Data lineage and impact analysis
    - Internal audit reporting

  NOTE: Access History has up to 3-hour latency. Some queries below may return
  empty results immediately after running the lab steps. This is expected behavior
  in production — plan for the latency in your compliance reporting.

  In this step you will:
    1. Count how many queries have accessed HRZN tables directly
    2. Break down access into reads vs. writes with timestamps
    3. View recent queries on sensitive tables
    4. Track the flow of sensitive data across objects (column-level lineage)
    5. Find indirect access patterns (views queried over base tables)
----------------------------------------------------------------------------------*/

USE ROLE HRZN_IT_ADMIN;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;
USE WAREHOUSE HRZN_WH;


/*----------------------------------------------------------------------------------
Step 6.1 — Query Count by Object

  How many distinct queries have directly accessed each HRZN table or view?
  Direct access means the object name appeared explicitly in the query.
----------------------------------------------------------------------------------*/

SELECT
    value:"objectName"::STRING       AS object_name,
    COUNT(DISTINCT query_id)         AS number_of_queries
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
LATERAL FLATTEN(input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name
ORDER BY number_of_queries DESC;


/*----------------------------------------------------------------------------------
Step 6.2 — Read vs. Write Breakdown

  Distinguish between SELECT (read) and DML/DDL (write) operations.
  When was each object last read? Last modified?
----------------------------------------------------------------------------------*/

SELECT
    value:"objectName"::STRING                                       AS object_name,
    CASE
        WHEN object_modified_by_ddl IS NOT NULL THEN 'write'
        ELSE 'read'
    END                                                              AS query_type,
    COUNT(DISTINCT query_id)                                         AS number_of_queries,
    MAX(query_start_time)                                            AS last_query_start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
LATERAL FLATTEN(input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name, query_type
ORDER BY object_name, number_of_queries DESC;


/*----------------------------------------------------------------------------------
Step 6.3 — Recent Queries on the CUSTOMER Table

  Who ran SELECT queries on the sensitive CUSTOMER table and when?
  What SQL did they execute?
----------------------------------------------------------------------------------*/

-- Last few READ queries on CUSTOMER
SELECT
    qh.USER_NAME,
    qh.QUERY_TEXT,
    value:objectName::STRING AS "TABLE"
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY AS qh
JOIN SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY AS ah ON qh.QUERY_ID = ah.QUERY_ID,
    LATERAL FLATTEN(input => ah.BASE_OBJECTS_ACCESSED)
WHERE query_type = 'SELECT'
  AND value:objectName = 'HRZN_DB.HRZN_SCH.CUSTOMER'
  AND qh.START_TIME > DATEADD(day, -90, CURRENT_DATE());

-- Last few WRITE queries on CUSTOMER
SELECT
    qh.USER_NAME,
    qh.QUERY_TEXT,
    value:objectName::STRING AS "TABLE"
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY AS qh
JOIN SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY AS ah ON qh.QUERY_ID = ah.QUERY_ID,
    LATERAL FLATTEN(input => ah.BASE_OBJECTS_ACCESSED)
WHERE query_type != 'SELECT'
  AND value:objectName = 'HRZN_DB.HRZN_SCH.CUSTOMER'
  AND qh.START_TIME > DATEADD(day, -90, CURRENT_DATE());

-- Queries on sensitive tables (CUSTOMER or CUSTOMER_ORDERS)
SELECT
    q.USER_NAME,
    q.QUERY_TEXT,
    q.START_TIME,
    q.END_TIME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q
WHERE q.QUERY_TEXT ILIKE '%HRZN_DB.HRZN_SCH.CUSTOMER%'
ORDER BY q.START_TIME DESC;

-- Top 10 longest-running queries in the account
SELECT
    query_text,
    user_name,
    role_name,
    database_name,
    warehouse_name,
    warehouse_size,
    execution_status,
    ROUND(total_elapsed_time / 1000, 3) AS elapsed_sec
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
ORDER BY total_elapsed_time DESC
LIMIT 10;


/*----------------------------------------------------------------------------------
Step 6.4 — Sensitive Data Column-Level Lineage

  This query traces how columns containing sensitive data (tagged with
  SEMANTIC_CATEGORY, PRIVACY_CATEGORY, or DATA_CLASSIFICATION) flow from
  source tables into derived objects through INSERT/CTAS/view operations.

  This is critical for:
    - Proving that PII was not copied to unauthorized locations
    - Understanding the blast radius of a sensitive column change
    - Verifying that tag propagation covered all derived paths
----------------------------------------------------------------------------------*/

SELECT *
FROM (
    -- Direct column lineage (column explicitly referenced in SELECT)
    SELECT
        directSources.value:"objectId"::VARCHAR       AS source_object_id,
        directSources.value:"objectName"::VARCHAR     AS source_object_name,
        directSources.value:"columnName"::VARCHAR     AS source_column_name,
        'DIRECT'                                      AS source_column_type,
        om.value:"objectName"::VARCHAR                AS target_object_name,
        columns_modified.value:"columnName"::VARCHAR  AS target_column_name
    FROM (SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY) t,
        LATERAL FLATTEN(input => t.OBJECTS_MODIFIED)                          om,
        LATERAL FLATTEN(input => om.value:"columns",        outer => true)   columns_modified,
        LATERAL FLATTEN(input => columns_modified.value:"directSources",
                        outer => true)                                        directSources

    UNION

    -- Base column lineage (column accessed indirectly through base table)
    SELECT
        baseSources.value:"objectId"                  AS source_object_id,
        baseSources.value:"objectName"::VARCHAR       AS source_object_name,
        baseSources.value:"columnName"::VARCHAR       AS source_column_name,
        'BASE'                                        AS source_column_type,
        om.value:"objectName"::VARCHAR                AS target_object_name,
        columns_modified.value:"columnName"::VARCHAR  AS target_column_name
    FROM (SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY) t,
        LATERAL FLATTEN(input => t.OBJECTS_MODIFIED)                          om,
        LATERAL FLATTEN(input => om.value:"columns",        outer => true)   columns_modified,
        LATERAL FLATTEN(input => columns_modified.value:"baseSources",
                        outer => true)                                        baseSources
) col_lin
WHERE
    (SOURCE_OBJECT_NAME = 'HRZN_DB.HRZN_SCH.CUSTOMER'
     OR TARGET_OBJECT_NAME = 'HRZN_DB.HRZN_SCH.CUSTOMER')
  AND (
        SOURCE_COLUMN_NAME IN (
            SELECT COLUMN_NAME
            FROM TABLE(
                HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
                    'HRZN_DB.HRZN_SCH.CUSTOMER',
                    'table'
                )
            )
            WHERE TAG_NAME IN ('SEMANTIC_CATEGORY', 'PRIVACY_CATEGORY', 'DATA_CLASSIFICATION')
        )
        OR
        TARGET_COLUMN_NAME IN (
            SELECT COLUMN_NAME
            FROM TABLE(
                HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
                    'HRZN_DB.HRZN_SCH.CUSTOMER',
                    'table'
                )
            )
            WHERE TAG_NAME IN ('SEMANTIC_CATEGORY', 'PRIVACY_CATEGORY', 'DATA_CLASSIFICATION')
        )
    );


/*----------------------------------------------------------------------------------
Step 6.5 — Indirect Access Patterns

  Some queries access tables through views or other intermediate objects.
  Base object access captures what was ultimately read, even if the query
  named a view rather than the raw table.
----------------------------------------------------------------------------------*/

SELECT
    base.value:"objectName"::STRING    AS object_name,
    COUNT(DISTINCT query_id)           AS number_of_queries
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
LATERAL FLATTEN(input => base_objects_accessed)    base,
LATERAL FLATTEN(input => direct_objects_accessed)  direct
WHERE 1=1
  AND object_name ILIKE 'HRZN%'
  AND object_name <> direct.value:"objectName"::STRING  -- base object not named directly in query
GROUP BY object_name
ORDER BY number_of_queries DESC;

/*
  KEY TAKEAWAYS — Step 6:

  ACCESS HISTORY:
    - Comprehensive audit trail for compliance and security investigations
    - Latency: up to 3 hours — factor this into real-time alerting designs
    - DIRECT_OBJECTS_ACCESSED = objects named explicitly in the query
    - BASE_OBJECTS_ACCESSED = objects that were actually read (including via views)
    - OBJECTS_MODIFIED = objects that were written (INSERT, CTAS, DDL)

  SENSITIVE DATA LINEAGE:
    - Column-level lineage shows where PII columns flowed after being read
    - Combine with TAG_REFERENCES to focus only on classified columns
    - Use this to prove compliance: "PII was not copied outside the governed zone"

  AUDIT TRAIL BEST PRACTICES:
    - Always check both DIRECT and BASE access for full coverage
    - Join ACCESS_HISTORY with QUERY_HISTORY to get query text
    - Filter on base_objects to catch indirect access through views
    - Alert on access to sensitive tables outside business hours (Cortex Code can help — see Step 4)

  CONGRATULATIONS! You have completed the lab.
  Run 99-teardown.sql to remove all lab objects from your account.
*/
