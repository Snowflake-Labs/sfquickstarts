
/***************************************************************************************************
 Advanced Data Governance: AI-Powered Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 5 — AI_REDACT for Unstructured PII (Data Governor Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL
                                         (Adapted from original Horizon Lab v2.0
                                          by Severin Gassauer)
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Overview — What This Step Covers

  In Step 2 we used AI classification to protect STRUCTURED data — columns with
  well-defined types where classification can detect PII by analyzing column names
  and sample values.

  But what about UNSTRUCTURED data? Customer feedback, support tickets, chat logs,
  and survey responses are free-form text that can contain PII embedded anywhere.
  Standard column masking policies do not help here.

  SNOWFLAKE.CORTEX.AI_REDACT is a purpose-built Cortex function that:
    - Automatically detects 50+ PII types in free-form text
    - Replaces detected PII with labeled placeholders ([NAME], [EMAIL], [PHONE_NUMBER])
    - Works in any language (multilingual support)
    - Requires no regex patterns or manual configuration

  In this step you will:
    1. Add customer feedback text with embedded PII to CUSTOMER_ORDERS
    2. Preview raw feedback to see the problem
    3. Use AI_REDACT to automatically remove PII from the text
    4. Create a pre-computed redacted table for efficient analytics
    5. Demonstrate selective redaction (redact only specific PII types)
    6. Build a role-based secure view switching between original and redacted content
    7. Run privacy-safe sentiment analysis on the redacted data

  PREREQUISITE: Step 2 must be completed (tags propagate from CUSTOMER to new tables).
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;


/*----------------------------------------------------------------------------------
Step 5.1 — Add Customer Feedback Data with Embedded PII

  We will add a CUSTOMER_FEEDBACK column to CUSTOMER_ORDERS and populate it with
  realistic feedback that contains various PII types mixed into free-form text.
----------------------------------------------------------------------------------*/

ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
    ADD COLUMN IF NOT EXISTS CUSTOMER_FEEDBACK VARCHAR;

UPDATE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
SET CUSTOMER_FEEDBACK =
    CASE
        WHEN MOD(ORDER_ID::INT, 10) = 0 THEN
            'Customer John Smith called from 555-123-4567 about order. Email: john.smith@email.com. Very satisfied!'
        WHEN MOD(ORDER_ID::INT, 10) = 1 THEN
            'Jane Doe (jane.doe@company.com) requested refund. Phone: (555) 987-6543. Issue resolved.'
        WHEN MOD(ORDER_ID::INT, 10) = 2 THEN
            'Great product! Contact me at michael.johnson@gmail.com or 555-222-3333 for wholesale orders.'
        WHEN MOD(ORDER_ID::INT, 10) = 3 THEN
            'Customer Sarah Williams mentioned her SSN 123-45-6789 was visible on invoice. URGENT: Fix privacy issue!'
        WHEN MOD(ORDER_ID::INT, 10) = 4 THEN
            'Bob Martinez at 456 Oak Street, Boston MA 02101 wants expedited shipping. Call 555-444-5555.'
        WHEN MOD(ORDER_ID::INT, 10) = 5 THEN
            'Lisa Chen from Acme Corp called about bulk pricing. Reach her at 555-777-8888 or lisa.chen@acmecorp.com.'
        WHEN MOD(ORDER_ID::INT, 10) = 6 THEN
            'David Brown (david.b@email.net) reported shipping to wrong address: 789 Pine Ave, Seattle WA 98101.'
        WHEN MOD(ORDER_ID::INT, 10) = 7 THEN
            'Follow up with Maria Garcia at 555-333-2222. She wants to change credit card ending in 4567.'
        WHEN MOD(ORDER_ID::INT, 10) = 8 THEN
            'Customer feedback from james.wilson@company.org: Product exceeded expectations! My DOB is 03/15/1985 for loyalty program.'
        WHEN MOD(ORDER_ID::INT, 10) = 9 THEN
            'Emily Davis called from 555-666-9999. Lives at 321 Elm Street, Chicago IL 60601. Wants expedited shipping.'
        ELSE
            'Standard order processed. No issues reported.'
    END
WHERE CUSTOMER_FEEDBACK IS NULL;

-- Preview raw feedback — observe the PII embedded in free text
SELECT
    ORDER_ID,
    CUSTOMER_FEEDBACK
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
LIMIT 10;

/*
  KEY OBSERVATION — The Unstructured PII Problem:
  The feedback contains:
    - Names:     John Smith, Jane Doe, Sarah Williams
    - Emails:    john.smith@email.com, jane.doe@company.com
    - Phones:    555-123-4567, (555) 987-6543
    - SSN:       123-45-6789
    - Addresses: 456 Oak Street, Boston MA 02101
    - DOB:       03/15/1985

  This is free-form text. Column masking policies cannot protect this.
  AI_REDACT handles it automatically.
*/


/*----------------------------------------------------------------------------------
Step 5.2 — AI_REDACT: Automated PII Removal

  SNOWFLAKE.CORTEX.AI_REDACT scans text for PII and replaces it with labeled
  placeholders. No regex patterns, no ML training, no configuration required.
----------------------------------------------------------------------------------*/

WITH sample_feedback AS (
    SELECT
        ORDER_ID,
        CUSTOMER_FEEDBACK AS original_feedback
    FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
    WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
    LIMIT 5
)
SELECT
    ORDER_ID,
    original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(original_feedback) AS redacted_feedback
FROM sample_feedback;

/*
  KEY OBSERVATION — AI_REDACT Results:

  ORIGINAL: "Customer John Smith called from 555-123-4567. Email: john.smith@email.com"
  REDACTED: "Customer [NAME] called from [PHONE_NUMBER]. Email: [EMAIL]"

  AI_REDACT automatically detected and replaced:
    - Personal names    → [NAME]
    - Email addresses   → [EMAIL]
    - Phone numbers     → [PHONE_NUMBER]
    - SSN               → [US_SOCIAL_SECURITY_NUMBER]
    - Street addresses  → [STREET_ADDRESS]

  No manual patterns needed!
*/


/*----------------------------------------------------------------------------------
Step 5.3 — Selective Redaction (Specific PII Types Only)

  AI_REDACT accepts an optional list of entity types to redact.
  This allows you to redact only the PII categories relevant to your use case.
----------------------------------------------------------------------------------*/

WITH feedback_sample AS (
    SELECT 'Contact John Smith at john.smith@email.com or call 555-123-4567 for updates.' AS text
)
SELECT
    text                                                      AS original,
    SNOWFLAKE.CORTEX.AI_REDACT(text)                         AS full_redaction,
    SNOWFLAKE.CORTEX.AI_REDACT(text, ['NAME', 'EMAIL'])       AS names_and_emails_only
FROM feedback_sample;

/*
  FULL REDACTION:    "[NAME] at [EMAIL] or call [PHONE_NUMBER] for updates."
  PARTIAL REDACTION: "[NAME] at [EMAIL] or call 555-123-4567 for updates."

  Use case: a vendor needs contact details for shipping but must not receive names or emails.
*/


/*----------------------------------------------------------------------------------
Step 5.4 — Create a Pre-Computed Redacted Table

  Running AI_REDACT on every query is expensive. The recommended pattern is to
  pre-compute the redacted version once during table creation and store it.
  Views then switch between the original and pre-computed columns based on role.

  NOTE: Limited to 100 rows for lab performance. AI_REDACT takes ~50 seconds for this size.
  In production, run as a batch job or scheduled task.
----------------------------------------------------------------------------------*/

USE ROLE SYSADMIN;

CREATE OR REPLACE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED AS
SELECT
    ORDER_ID,
    CUSTOMER_ID,
    ORDER_TS,
    CUSTOMER_FEEDBACK             AS original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(CUSTOMER_FEEDBACK) AS redacted_feedback,
    CURRENT_TIMESTAMP()           AS redacted_at,
    CURRENT_USER()                AS redacted_by
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
WHERE CUSTOMER_FEEDBACK IS NOT NULL
LIMIT 100;

-- Preview the redacted table
SELECT
    ORDER_ID,
    original_feedback,
    redacted_feedback
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED
WHERE original_feedback NOT LIKE 'Standard order%'
LIMIT 10;


/*----------------------------------------------------------------------------------
Step 5.5 — Role-Based Secure View

  Governors see original feedback (for governance and compliance reviews).
  Analysts and data users see the pre-computed redacted version.
  The secure view switches between columns based on CURRENT_ROLE().
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_GOVERNOR;

CREATE OR REPLACE SECURE VIEW HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE AS
SELECT
    ORDER_ID,
    CUSTOMER_ID,
    ORDER_TS,
    CASE
        WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
            THEN original_feedback
        ELSE redacted_feedback
    END AS CUSTOMER_FEEDBACK,
    redacted_at,
    redacted_by
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED;

-- Governor sees original PII
USE ROLE HRZN_DATA_GOVERNOR;
SELECT ORDER_ID, CUSTOMER_FEEDBACK
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE
WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
LIMIT 5;

-- Data user sees the pre-redacted version
USE ROLE HRZN_DATA_USER;
SELECT ORDER_ID, CUSTOMER_FEEDBACK
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE
WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
LIMIT 5;

USE ROLE HRZN_DATA_GOVERNOR;

/*
  KEY OBSERVATION — Performance-Efficient Role-Based Redaction:
  - AI_REDACT runs ONCE during table creation (not on every query)
  - The secure view selects pre-computed columns (instant response)
  - Governors get the original; analysts get the safe version automatically
*/


/*----------------------------------------------------------------------------------
Step 5.6 — Privacy-Safe Sentiment Analysis

  The redacted text preserves the semantic meaning of the feedback while removing
  PII. Sentiment analysis works perfectly because tone and context remain intact.
  This enables ML training, analytics, and reporting without PII exposure.
----------------------------------------------------------------------------------*/

SELECT
    ORDER_ID,
    redacted_feedback,
    SNOWFLAKE.CORTEX.SENTIMENT(redacted_feedback)    AS sentiment_score,
    CASE
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(redacted_feedback) > 0.5  THEN 'Positive'
        WHEN SNOWFLAKE.CORTEX.SENTIMENT(redacted_feedback) < -0.5 THEN 'Negative'
        ELSE 'Neutral'
    END                                              AS sentiment_category
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED
WHERE redacted_feedback NOT LIKE 'Standard order%'
ORDER BY sentiment_score DESC
LIMIT 100;

-- Business insights from redacted data: which feedback categories drive negative sentiment?
WITH feedback_analysis AS (
    SELECT
        ORDER_ID,
        redacted_feedback,
        SNOWFLAKE.CORTEX.SENTIMENT(redacted_feedback) AS sentiment,
        CASE
            WHEN LOWER(redacted_feedback) LIKE '%refund%'                                  THEN 'Refund Request'
            WHEN LOWER(redacted_feedback) LIKE '%shipping%'
              OR LOWER(redacted_feedback) LIKE '%expedited%'                               THEN 'Shipping Issue'
            WHEN LOWER(redacted_feedback) LIKE '%bulk%'
              OR LOWER(redacted_feedback) LIKE '%wholesale%'                               THEN 'Bulk Order'
            WHEN LOWER(redacted_feedback) LIKE '%credit card%'                             THEN 'Payment Issue'
            WHEN LOWER(redacted_feedback) LIKE '%urgent%'
              OR LOWER(redacted_feedback) LIKE '%privacy%'                                 THEN 'Urgent / Privacy'
            ELSE 'General Feedback'
        END AS feedback_category
    FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED
    WHERE redacted_feedback NOT LIKE 'Standard order%'
)
SELECT
    feedback_category,
    COUNT(*)          AS feedback_count,
    AVG(sentiment)    AS avg_sentiment,
    CASE
        WHEN AVG(sentiment) > 0.3  THEN 'Positive'
        WHEN AVG(sentiment) < -0.3 THEN 'Negative'
        ELSE 'Neutral'
    END               AS sentiment_label
FROM feedback_analysis
GROUP BY feedback_category
ORDER BY feedback_count DESC;

/*
  KEY TAKEAWAYS — Step 5:

  AI_REDACT USE CASES:
    - Customer feedback and reviews
    - Support tickets and chat logs
    - Email content analysis
    - Social media mentions
    - Survey open-ended responses
    - Legal documents and contracts

  PATTERN: PRE-COMPUTE + SECURE VIEW
    - Run AI_REDACT once as a batch job; store results
    - Secure view switches columns based on role — no per-query AI cost
    - Enables fast, privacy-safe analytics for downstream consumers

  INTEGRATION WITH STEP 2:
    - Structured columns: protected by DATA_CLASSIFICATION tag masking (Step 2)
    - Unstructured text: protected by AI_REDACT (Step 5)
    - Tags propagate automatically from CUSTOMER to CUSTOMER_FEEDBACK_REDACTED
    - Complete coverage across all data formats

  Proceed to Step 6 to use Cortex Code governance skills to audit and improve
  the governance framework you've built.
*/
