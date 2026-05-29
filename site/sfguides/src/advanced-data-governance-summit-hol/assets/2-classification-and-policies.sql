
/***************************************************************************************************
 Advanced Data Governance: Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 2 — Know and Protect Your Data (Data Governor Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL
                                         (Adapted from original Horizon Lab v2.0 by Ravi Kumar
                                          and Severin Gassauer)
***************************************************************************************************/


/*----------------------------------------------------------------------------------
Overview — What This Step Covers

  1. View unprotected PII as a Data User (no masking yet)
  2. Create an enterprise DATA_CLASSIFICATION tag with propagation
  3. Create a Classification Profile with tag_map (BYOT pattern)
  4. Run classification on the CUSTOMER table
  5. Create a custom classifier for credit card formats
  6. Create multi-type tag-based masking policies
  7. Create a consent-based row access policy (opt-in)
  8. Create a state-based row access policy (geographic filtering)
  9. Create an aggregation policy on CUSTOMER_ORDERS
 10. Create a projection policy on ZIP
 11. Verify tag propagation to derived tables
----------------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------------
Step 2.1 — Observe the Problem: Raw PII Visible to Data Users

Before applying any governance controls, confirm that HRZN_DATA_USER can see
all PII columns without restriction.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_USER;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

-- All PII fields visible — SSN, email, credit card, phone, birthdate
SELECT FIRST_NAME, LAST_NAME, STREET_ADDRESS, STATE, CITY, ZIP,
       PHONE_NUMBER, EMAIL, SSN, BIRTHDATE, CREDITCARD
FROM HRZN_DB.HRZN_SCH.CUSTOMER
SAMPLE (100 ROWS);

/*
  KEY OBSERVATION:
  HRZN_DATA_USER sees every PII field in plain text.
  There is no understanding of which fields are sensitive.
  We will fix this in the steps below.
*/


/*----------------------------------------------------------------------------------
Step 2.2 — Create the Enterprise DATA_CLASSIFICATION Tag

The BYOT (Bring Your Own Tags) pattern maps AI-detected categories to your
organization's custom taxonomy. The tag uses PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT
so that derived tables (CTAS, INSERT SELECT, views) automatically inherit the tag.

Classification levels:
  PII        — Personal identifiers (email, SSN, credit card) — highest protection
  RESTRICTED — Sensitive personal data (phone, birthdate)
  SENSITIVE  — Personal information (name, address, city, state, ZIP)
  INTERNAL   — Business data (job title, company)
  PUBLIC     — Non-sensitive identifiers — lowest protection
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
CREATE SCHEMA IF NOT EXISTS HRZN_DB.TAG_SCHEMA;
USE SCHEMA HRZN_DB.TAG_SCHEMA;

CREATE OR REPLACE TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    ALLOWED_VALUES 'PII', 'RESTRICTED', 'SENSITIVE', 'INTERNAL', 'PUBLIC'
    COMMENT = 'Enterprise data classification with AI automation and propagation'
    PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT;


/*----------------------------------------------------------------------------------
Step 2.3 — Create a Classification Profile with Tag Map

The classification profile instructs Snowflake's AI classifier to:
  - Auto-detect sensitive columns using native semantic categories
  - Map detected categories to our DATA_CLASSIFICATION tag values
  - Automatically apply tags (auto_tag: true)
  - Re-classify every 90 days
----------------------------------------------------------------------------------*/

USE ROLE SYSADMIN;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
    HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 90,
      'auto_tag': true,
      'classify_views': true,
      'tag_map': {
        'column_tag_map': [
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'PII',
            'semantic_categories': [
              'EMAIL',
              'US_SOCIAL_SECURITY_NUMBER',
              'NATIONAL_IDENTIFIER',
              'US_BANK_ACCOUNT_NUMBER',
              'CREDIT_CARD_NUMBER'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'RESTRICTED',
            'semantic_categories': [
              'PHONE_NUMBER',
              'DATE_OF_BIRTH'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'SENSITIVE',
            'semantic_categories': [
              'NAME',
              'STREET_ADDRESS',
              'CITY',
              'US_STATE',
              'ZIP_CODE'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'INTERNAL',
            'semantic_categories': [
              'JOB_TITLE',
              'OCCUPATION',
              'COMPANY'
            ]
          }
        ]
      }
    });


/*----------------------------------------------------------------------------------
Step 2.4 — Run Classification on the CUSTOMER Table

Run SYSTEM$CLASSIFY manually on the CUSTOMER table to test the profile,
then attach the profile at the database level to enable auto-classification.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;

-- Run classification manually on a single table to test the profile.
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE'
);

-- Enable auto-classification by attaching classification profile at the database level.
ALTER DATABASE HRZN_DB
    SET CLASSIFICATION_PROFILE = 'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE';

-- View all tags applied (system tags + our custom DATA_CLASSIFICATION tag)
SELECT TAG_DATABASE, TAG_SCHEMA, OBJECT_NAME, COLUMN_NAME, TAG_NAME, TAG_VALUE
FROM TABLE(
    HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
        'HRZN_DB.HRZN_SCH.CUSTOMER',
        'table'
    )
)
ORDER BY TAG_NAME, COLUMN_NAME;

-- View only our DATA_CLASSIFICATION tags (these propagate to derived tables)
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
    END,
    COLUMN_NAME;

/*
  KEY OBSERVATION — Classification with Tag Mapping:
  The profile applied TWO types of tags:
    1. System tags (SEMANTIC_CATEGORY, PRIVACY_CATEGORY) — Snowflake-managed, do NOT propagate
    2. DATA_CLASSIFICATION tag                           — YOUR tag, DOES propagate!

  This BYOT pattern ensures governance policies automatically flow to derived datasets.
*/


/*----------------------------------------------------------------------------------
Step 2.5 — Custom Classifier for Credit Cards

Snowflake's built-in classifier detects CREDIT_CARD_NUMBER generically.
A custom classifier using regex can detect specific card network formats
(Mastercard, AmEx) for fine-grained control.
----------------------------------------------------------------------------------*/

USE SCHEMA HRZN_DB.CLASSIFIERS;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CUSTOM_CLASSIFIER CREDITCARD();

SHOW SNOWFLAKE.DATA_PRIVACY.CUSTOM_CLASSIFIER;

-- Add regex patterns for different credit card networks
CALL creditcard!add_regex('MC_PAYMENT_CARD',  'IDENTIFIER', '^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$');
CALL creditcard!add_regex('AMX_PAYMENT_CARD', 'IDENTIFIER', '^3[4-7][0-9]{13}$');

SELECT creditcard!list();

-- Verify AmEx card data exists in the table
SELECT CREDITCARD
FROM HRZN_DB.HRZN_SCH.CUSTOMER
WHERE CREDITCARD REGEXP '^3[4-7][0-9]{13}$'
LIMIT 5;

-- Re-classify using the custom classifier (without re-running the full profile)
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    {'custom_classifiers': ['HRZN_DB.CLASSIFIERS.CREDITCARD'], 'auto_tag': true}
);

-- Confirm the CREDITCARD column now has a semantic category
SELECT SYSTEM$GET_TAG('snowflake.core.semantic_category', 'HRZN_DB.HRZN_SCH.CUSTOMER.CREDITCARD', 'column');


/*----------------------------------------------------------------------------------
Step 2.6 — Tag-Based Masking Policies (Multi-Type)

Instead of creating one masking policy per column, we attach policies to the
DATA_CLASSIFICATION tag. Any column tagged PII, RESTRICTED, or SENSITIVE
automatically gets the appropriate masking — regardless of when it was created.

BEST PRACTICE: Create one policy per data type (STRING, NUMBER, DATE, TIMESTAMP)
and attach all of them to the same tag.

Masking logic per classification level:
  PII        — Full redaction / NULL (no visibility for non-governors)
  RESTRICTED — Partial masking (last 4 chars, year-only for dates)
  SENSITIVE  — Pseudonymization (SHA2 hash, month truncation for dates)
  INTERNAL   — Fully visible
  PUBLIC     — Fully visible
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
USE SCHEMA HRZN_DB.TAG_SCHEMA;

-- Create opt-in consent lookup table (used by masking and row access policies)
CREATE OR REPLACE TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP AS
SELECT DISTINCT ID AS CUSTOMER_ID, OPTIN
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

GRANT SELECT ON TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP TO ROLE HRZN_DATA_USER;
GRANT SELECT ON TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP TO ROLE HRZN_IT_ADMIN;

-- -----------------------------------------------------------------------
-- STRING MASKING POLICY
-- -----------------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING
AS (VAL STRING)
RETURNS STRING ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
        THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
        THEN '***PII-REDACTED***'
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
        THEN CONCAT('***-', RIGHT(VAL, 4))
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
        THEN SHA2(VAL, 256)
    ELSE VAL
END;

-- -----------------------------------------------------------------------
-- NUMBER MASKING POLICY
-- -----------------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_NUMBER
AS (VAL NUMBER)
RETURNS NUMBER ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
        THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
        THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
        THEN ROUND(VAL, -2)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
        THEN ABS(HASH(VAL))
    ELSE VAL
END;

-- -----------------------------------------------------------------------
-- DATE MASKING POLICY
-- -----------------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_DATE
AS (VAL DATE)
RETURNS DATE ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
        THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
        THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
        THEN DATE_TRUNC('YEAR', VAL)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
        THEN DATE_TRUNC('MONTH', VAL)
    ELSE VAL
END;

-- -----------------------------------------------------------------------
-- TIMESTAMP MASKING POLICY
-- -----------------------------------------------------------------------
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_TIMESTAMP
AS (VAL TIMESTAMP)
RETURNS TIMESTAMP ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
        THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
        THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
        THEN DATE_TRUNC('DAY', VAL)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
        THEN DATE_TRUNC('MONTH', VAL)
    ELSE VAL
END;

-- -----------------------------------------------------------------------
-- ATTACH ALL POLICIES TO THE TAG
-- Each data type gets its own policy — all attached to DATA_CLASSIFICATION
-- -----------------------------------------------------------------------
ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_NUMBER;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_DATE;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_TIMESTAMP;

/*
  KEY BENEFITS — Tag-Based Multi-Type Masking:
  1. TYPE SAFETY — each data type has appropriate masking logic
  2. AUTO APPLICATION — tag a column and masking is applied immediately
  3. SCALE — add new tables; just tag the columns, no policy re-assignment needed
  4. FUTURE-PROOF — tag propagation means derived tables get protected automatically
*/


/*----------------------------------------------------------------------------------
Step 2.7 — Consent-Based Row Access Policy (Opt-In)

Customers who have not opted in (OPTIN='N') have NOT consented to data use.
The HRZN_DATA_USER role should only see opted-in customer records.
Data governors see all records regardless of opt-in status.
----------------------------------------------------------------------------------*/

CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY
    AS (OPTIN_STATUS STRING) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR', 'HRZN_IT_ADMIN')
            THEN TRUE
        WHEN CURRENT_ROLE() = 'HRZN_DATA_USER' AND OPTIN_STATUS = 'Y'
            THEN TRUE
        ELSE FALSE
    END;

ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    ADD ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY ON (OPTIN);

-- Test: HRZN_DATA_GOVERNOR sees all customers
USE ROLE HRZN_DATA_GOVERNOR;
SELECT
    ID,
    FIRST_NAME, EMAIL, SSN, PHONE_NUMBER, BIRTHDATE, COMPANY, OPTIN
FROM HRZN_DB.HRZN_SCH.CUSTOMER
LIMIT 10;

SELECT
    COUNT(*) AS total_customers,
    SUM(CASE WHEN OPTIN = 'Y' THEN 1 ELSE 0 END) AS opted_in_customers
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

-- Test: HRZN_DATA_USER sees only opted-in customers (and with masking applied)
USE ROLE HRZN_DATA_USER;
SELECT
    ID,
    FIRST_NAME,      -- SENSITIVE: hashed
    EMAIL,           -- PII: redacted
    SSN,             -- PII: redacted
    PHONE_NUMBER,    -- RESTRICTED: partial mask (***-1234)
    BIRTHDATE,       -- RESTRICTED: partial mask
    COMPANY,         -- INTERNAL: visible
    OPTIN            -- All visible rows have OPTIN='Y'
FROM HRZN_DB.HRZN_SCH.CUSTOMER
LIMIT 10;

SELECT COUNT(*) AS visible_customers FROM HRZN_DB.HRZN_SCH.CUSTOMER;

/*
  KEY OBSERVATION — Layered Governance:
  HRZN_DATA_USER sees:
    1. ROW FILTERING:   Only customers with OPTIN='Y'
    2. COLUMN MASKING:  PII redacted, RESTRICTED partial, SENSITIVE hashed
  This is defense-in-depth: row policy controls WHICH records; masking controls HOW data appears.
*/

USE ROLE HRZN_DATA_GOVERNOR;


/*----------------------------------------------------------------------------------
Step 2.8 — State-Based Row Access Policy (Geographic Filtering)

HRZN_DATA_USER should only see customers in Massachusetts (MA).
The ROW_POLICY_MAP table (created in setup) holds the role-to-state mapping,
making it easy to adjust permissions without changing the policy definition.

NOTE: Multiple row access policies on the same table are ANDed together.
We drop the opt-in policy here to demonstrate the state-based policy in isolation.
----------------------------------------------------------------------------------*/

-- Drop the opt-in policy to demonstrate state-based filtering cleanly
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    DROP ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY;

-- Unset the STATE column tag so it can be used in the row access policy predicate
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    MODIFY COLUMN STATE UNSET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION;

-- Review the role-to-state mapping
USE ROLE HRZN_DATA_GOVERNOR;
SELECT * FROM HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP;

-- Before policy: DATA_USER sees all states
USE ROLE HRZN_DATA_USER;
SELECT FIRST_NAME, STREET_ADDRESS, STATE, PHONE_NUMBER, EMAIL, JOB, COMPANY
FROM HRZN_DB.HRZN_SCH.CUSTOMER
LIMIT 10;

-- Create the state-based row access policy
USE ROLE HRZN_DATA_GOVERNOR;
CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_STATE_RESTRICTIONS
    AS (STATE STRING) RETURNS BOOLEAN ->
       CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR')
        OR EXISTS (
            SELECT rp.ROLE
            FROM HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP rp
            WHERE 1=1
                AND rp.ROLE = CURRENT_ROLE()
                AND rp.STATE_VISIBILITY = STATE
        )
    COMMENT = 'Limits rows returned based on ROW_POLICY_MAP role-to-state mapping';

-- Apply the policy to the CUSTOMER table
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    ADD ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_STATE_RESTRICTIONS ON (STATE);

-- After policy: DATA_USER sees only Massachusetts customers
USE ROLE HRZN_DATA_USER;
SELECT FIRST_NAME, STREET_ADDRESS, STATE, PHONE_NUMBER, EMAIL, JOB, COMPANY
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

USE ROLE HRZN_DATA_GOVERNOR;


/*----------------------------------------------------------------------------------
Step 2.9 — Aggregation Policy on CUSTOMER_ORDERS

An Aggregation Policy controls what type of query can access data from a table.
Non-admin users must aggregate data into groups of at least 100 rows, preventing
queries that return individual records.
----------------------------------------------------------------------------------*/

CREATE OR REPLACE AGGREGATION POLICY HRZN_DB.TAG_SCHEMA.AGGREGATION_POLICY
    AS () RETURNS AGGREGATION_CONSTRAINT ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR')
            THEN NO_AGGREGATION_CONSTRAINT()
        ELSE AGGREGATION_CONSTRAINT(MIN_GROUP_SIZE => 100)
    END;

ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
    SET AGGREGATION POLICY HRZN_DB.TAG_SCHEMA.AGGREGATION_POLICY;

-- Test: DATA_USER cannot SELECT * (individual records)
USE ROLE HRZN_DATA_USER;
SELECT TOP 10 * FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS; -- EXPECTED: fails

-- This works — aggregates over 100 rows
SELECT ORDER_CURRENCY, SUM(ORDER_AMOUNT)
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
GROUP BY ORDER_CURRENCY;

-- Join with customer table (aggregated)
SELECT
    cl.STATE,
    cl.CITY,
    COUNT(oh.ORDER_ID) AS count_order,
    SUM(oh.ORDER_AMOUNT) AS order_total
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS oh
JOIN HRZN_DB.HRZN_SCH.CUSTOMER cl ON oh.CUSTOMER_ID = cl.ID
GROUP BY ALL
ORDER BY order_total DESC;

USE ROLE HRZN_DATA_GOVERNOR;


/*----------------------------------------------------------------------------------
Step 2.10 — Projection Policy on ZIP Column

A Projection Policy prevents a column from appearing in SELECT output.
The column can still be used in WHERE clauses (for filtering) but cannot
be projected into query results.
----------------------------------------------------------------------------------*/

-- Unset ZIP classification tag first (required before applying projection policy)
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    MODIFY COLUMN ZIP UNSET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION;

CREATE OR REPLACE PROJECTION POLICY HRZN_DB.TAG_SCHEMA.PROJECTION_POLICY
    AS () RETURNS PROJECTION_CONSTRAINT ->
    CASE
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR')
            THEN PROJECTION_CONSTRAINT(ALLOW => true)
        ELSE PROJECTION_CONSTRAINT(ALLOW => false)
    END;

ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    MODIFY COLUMN ZIP
    SET PROJECTION POLICY HRZN_DB.TAG_SCHEMA.PROJECTION_POLICY;

-- Test: SELECT * fails for DATA_USER (ZIP is projection-constrained)
USE ROLE HRZN_DATA_USER;
SELECT TOP 100 * FROM HRZN_DB.HRZN_SCH.CUSTOMER;             -- EXPECTED: fails
SELECT TOP 100 * EXCLUDE ZIP FROM HRZN_DB.HRZN_SCH.CUSTOMER; -- Works

-- ZIP can still be used in WHERE clause
SELECT * EXCLUDE ZIP
FROM HRZN_DB.HRZN_SCH.CUSTOMER
WHERE ZIP NOT IN ('97135', '95357')
LIMIT 10;

USE ROLE HRZN_DATA_GOVERNOR;

-- Cleanup projection and aggregation policies for subsequent steps
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS UNSET AGGREGATION POLICY;
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER MODIFY COLUMN ZIP UNSET PROJECTION POLICY;

-- Re-apply DATA_CLASSIFICATION to ZIP for consistency
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    MODIFY COLUMN ZIP SET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION = 'SENSITIVE';


/*----------------------------------------------------------------------------------
Step 2.11 — Verify Tag Propagation to Derived Tables

When a table is created from a tagged source (CTAS), the DATA_CLASSIFICATION tags
propagate automatically because we set PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT.
Masking policies attach to derived tables without any manual work.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_ENGINEER;
CREATE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_COPY AS
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER;

-- Verify propagated tags on the derived table
USE ROLE HRZN_DATA_GOVERNOR;
SELECT
    COLUMN_NAME,
    TAG_VALUE AS CLASSIFICATION_LEVEL
FROM TABLE(
    HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
        'HRZN_DB.HRZN_SCH.CUSTOMER_COPY',
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
    END,
    COLUMN_NAME;

-- Test masking on derived table (DATA_USER sees masked data automatically)
USE ROLE HRZN_DATA_USER;
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER_COPY LIMIT 5;

USE ROLE HRZN_DATA_GOVERNOR;

/*
  KEY TAKEAWAYS — Step 2:

  CLASSIFICATION:
    - AI-powered SYSTEM$CLASSIFY detects 50+ PII types automatically
    - Classification profile maps native categories to your DATA_CLASSIFICATION tag
    - Tag propagation (PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT) scales governance
      to thousands of derived tables with zero manual effort
    - Custom classifiers extend detection to domain-specific formats (credit cards, IDs)

  MASKING:
    - Single tag-based policy automatically protects all tagged columns
    - Multi-type policies ensure correct masking logic for every data type
    - No per-column policy management — just tag the column

  ADVANCED POLICIES:
    - Row access policies control WHICH rows are visible (consent, geography)
    - Aggregation policies prevent individual record access
    - Projection policies block column projection without blocking filtering

  Proceed to Step 3 to verify everything you just built using the Trust Center UI.
*/
