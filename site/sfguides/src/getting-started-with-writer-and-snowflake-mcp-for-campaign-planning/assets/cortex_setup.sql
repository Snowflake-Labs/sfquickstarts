/*=============================================================================
  WRITER + Snowflake MCP Quickstart — Cortex AI Setup
  
  Getting Started with WRITER and Snowflake MCP for Campaign Planning
  https://github.com/Snowflake-Labs/sfquickstarts

  Run this script in a Snowsight SQL Worksheet as ACCOUNTADMIN, AFTER
  running setup_data.sql.

  It creates:
    - Table:          CAMPAIGN_BRIEFS       (empty — write-back target)
    - Procedure:      SAVE_BRIEF            (governed write path)
    - Search Service: CAMPAIGN_LIBRARY_SEARCH
    - Semantic View:  CUSTOMER_360_SV
    - Agent:          WRITER_CAMPAIGN_PLANNER
    - MCP Server:     WRITER_QUICKSTART_MCP_SERVER
    - All grants for WRITER_QUICKSTART_ROLE
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

-- ── Write-back target ──────────────────────────────────────────────────────
CREATE OR REPLACE TABLE CAMPAIGN_BRIEFS (
  BRIEF_ID      VARCHAR(50)   NOT NULL,
  CAMPAIGN_ID   VARCHAR(30),
  STATUS        VARCHAR(20)   DEFAULT 'draft',
  CREATED_BY    VARCHAR(100),
  CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  APPROVED_AT   TIMESTAMP_NTZ,
  BRIEF_CONTENT VARIANT
)
COMMENT = 'Campaign briefs written back from WRITER through SAVE_BRIEF';

-- ── Governed write procedure ───────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE SAVE_BRIEF(
  P_CAMPAIGN_ID VARCHAR,
  P_BRIEF_JSON  VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Upserts a campaign brief into CAMPAIGN_BRIEFS. Returns the BRIEF_ID.'
EXECUTE AS CALLER
AS
$$
DECLARE
  v_brief_id  VARCHAR;
  v_brief_obj VARIANT;
BEGIN
  v_brief_obj := PARSE_JSON(:P_BRIEF_JSON);

  v_brief_id := COALESCE(
    v_brief_obj:brief_id::VARCHAR,
    'BRF-' || REPLACE(:P_CAMPAIGN_ID, 'CMP-', '') || '-' ||
      TO_CHAR(CURRENT_TIMESTAMP(), 'HH24MISS')
  );

  MERGE INTO CAMPAIGN_BRIEFS tgt
  USING (SELECT :v_brief_id AS BRIEF_ID) src
    ON (tgt.BRIEF_ID = src.BRIEF_ID)
  WHEN MATCHED THEN UPDATE SET
    CAMPAIGN_ID   = :P_CAMPAIGN_ID,
    STATUS        = COALESCE(:v_brief_obj:status::VARCHAR, 'draft'),
    CREATED_BY    = :v_brief_obj:created_by::VARCHAR,
    BRIEF_CONTENT = :v_brief_obj
  WHEN NOT MATCHED THEN INSERT (
    BRIEF_ID, CAMPAIGN_ID, STATUS, CREATED_BY, CREATED_AT, BRIEF_CONTENT
  ) VALUES (
    :v_brief_id,
    :P_CAMPAIGN_ID,
    COALESCE(:v_brief_obj:status::VARCHAR, 'draft'),
    :v_brief_obj:created_by::VARCHAR,
    CURRENT_TIMESTAMP(),
    :v_brief_obj
  );

  RETURN :v_brief_id;
END;
$$;

-- ── Cortex Search over campaign copy ───────────────────────────────────────
CREATE OR REPLACE CORTEX SEARCH SERVICE CAMPAIGN_LIBRARY_SEARCH
  ON SEARCH_CONTENT
  ATTRIBUTES CAMPAIGN_ID, CAMPAIGN_NAME, TARGET_SEGMENT, CAMPAIGN_TYPE, CHANNEL, TONE, PERFORMANCE_TIER
  WAREHOUSE = WRITER_QUICKSTART_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  COMMENT = 'Searchable index of 60 historical Apex Athletics campaigns'
  AS
    SELECT
      CAMPAIGN_ID, CAMPAIGN_NAME, TARGET_SEGMENT, CAMPAIGN_TYPE, CHANNEL, TONE,
      PERFORMANCE_TIER, OPEN_RATE, CLICK_RATE, CONVERSION_RATE, REVENUE_GENERATED,
      SUBJECT_LINE || ' ' ||
      COALESCE(BODY_PREVIEW, '') || ' ' ||
      COALESCE(CTA_TEXT, '') || ' ' ||
      'Tone: ' || COALESCE(TONE, '') || '. ' ||
      'Campaign type: ' || CAMPAIGN_TYPE || '. ' ||
      'Channel: ' || CHANNEL || '. ' ||
      'Target segment: ' || COALESCE(TARGET_SEGMENT, '') || '. ' ||
      'Performance tier: ' || COALESCE(PERFORMANCE_TIER, '') || '. ' ||
      'Tags: ' || COALESCE(TAGS, '') AS SEARCH_CONTENT
    FROM CAMPAIGN_LIBRARY;

-- ── Semantic view over customer data ───────────────────────────────────────
CREATE OR REPLACE SEMANTIC VIEW CUSTOMER_360_SV
  TABLES (
    c AS CUSTOMER_360
      PRIMARY KEY (CUSTOMER_ID),
    s AS MICRO_SEGMENTS
      PRIMARY KEY (SEGMENT_ID)
      UNIQUE (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
  )
  RELATIONSHIPS (
    c (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
    REFERENCES s (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
  )
  FACTS (
    c.ANNUAL_SPEND             AS ANNUAL_SPEND             COMMENT = 'Annual spend from profile',
    c.TOTAL_SPEND_12M          AS TOTAL_SPEND_12M          COMMENT = 'Total spend last 12 months',
    c.AVG_ORDER_VALUE          AS AVG_ORDER_VALUE          COMMENT = 'Average order value (12 months)',
    c.LOYALTY_POINTS           AS LOYALTY_POINTS           COMMENT = 'Current loyalty points balance',
    c.PURCHASE_COUNT_12M       AS PURCHASE_COUNT_12M       COMMENT = 'Purchases last 12 months',
    c.CART_ADD_COUNT_12M       AS CART_ADD_COUNT_12M       COMMENT = 'Cart adds last 12 months',
    c.TOTAL_EVENTS_12M         AS TOTAL_EVENTS_12M         COMMENT = 'Total behavioral events last 12 months',
    c.ACTIVE_DAYS_12M          AS ACTIVE_DAYS_12M          COMMENT = 'Active days last 12 months',
    c.TRAINING_LOGS_12M        AS TRAINING_LOGS_12M        COMMENT = 'Training logs last 12 months',
    c.EMAIL_OPENS_12M          AS EMAIL_OPENS_12M          COMMENT = 'Emails opened last 12 months',
    c.EMAIL_CLICKS_12M         AS EMAIL_CLICKS_12M         COMMENT = 'Email clicks last 12 months',
    c.CAMPAIGN_CONVERSIONS_12M AS CAMPAIGN_CONVERSIONS_12M COMMENT = 'Campaign conversions last 12 months',
    c.CAMPAIGN_REVENUE_12M     AS CAMPAIGN_REVENUE_12M     COMMENT = 'Campaign revenue last 12 months',
    c.TENURE_DAYS              AS TENURE_DAYS              COMMENT = 'Days since customer signup',
    c.DAYS_SINCE_LAST_PURCHASE AS DAYS_SINCE_LAST_PURCHASE COMMENT = 'Days since last purchase',
    c.LTV_ANNUALIZED           AS LTV_ANNUALIZED           COMMENT = 'Annualized customer lifetime value',
    c.ENGAGEMENT_SCORE         AS ENGAGEMENT_SCORE         COMMENT = 'Engagement score (0-100)',
    s.TOTAL_REVENUE_OPPORTUNITY AS TOTAL_REVENUE_OPPORTUNITY COMMENT = 'Total revenue opportunity for segment'
  )
  DIMENSIONS (
    c.CUSTOMER_ID        AS CUSTOMER_ID        COMMENT = 'Unique customer identifier (CUST-NNNNNN)',
    c.FIRST_NAME         AS FIRST_NAME         COMMENT = 'Customer first name',
    c.LAST_NAME          AS LAST_NAME          COMMENT = 'Customer last name',
    c.EMAIL              AS EMAIL              COMMENT = 'Customer email address',
    c.GENDER             AS GENDER             COMMENT = 'Gender',
    c.CITY               AS CITY               COMMENT = 'City of residence',
    c.STATE              AS STATE              COMMENT = 'US state',
    c.REGION             AS REGION             COMMENT = 'Geographic region',
    c.LOYALTY_TIER_NAME  AS LOYALTY_TIER_NAME  COMMENT = 'Loyalty tier: Starter/Active/Performance/Elite',
    c.PREFERRED_CHANNEL  AS PREFERRED_CHANNEL  COMMENT = 'Preferred channel (email/push/sms)',
    c.TOP_CATEGORY       AS TOP_CATEGORY       COMMENT = 'Top product category (Running/Yoga/Training/Outdoor/Recovery/Cycling)',
    c.MARKETING_OPT_IN   AS MARKETING_OPT_IN   COMMENT = 'Opted in to marketing',
    c.RFM_SEGMENT        AS RFM_SEGMENT        COMMENT = 'RFM segment (Champion/Loyal/Recent/At Risk/Dormant/Potential/Needs Attention/New)',
    c.CHURN_RISK_TIER    AS CHURN_RISK_TIER    COMMENT = 'Churn risk tier (High/Medium/Low)',
    c.SIGNUP_DATE        AS SIGNUP_DATE        COMMENT = 'Date customer joined Apex Athletics',
    c.LAST_PURCHASE_DATE AS LAST_PURCHASE_DATE COMMENT = 'Date of most recent purchase',
    s.SEGMENT_ID         AS SEGMENT_ID         COMMENT = 'Micro-segment ID',
    s.SEGMENT_NAME       AS SEGMENT_NAME       COMMENT = 'Full micro-segment name'
  )
  METRICS (
    c.AVG_ENGAGEMENT_SCORE   AS AVG(ENGAGEMENT_SCORE)          COMMENT = 'Average engagement score (0-100)',
    c.AVG_CHURN_RISK         AS AVG(CHURN_RISK_SCORE)          COMMENT = 'Average churn risk score (0-100)',
    c.AVG_HEALTH_SCORE       AS AVG(CUSTOMER_HEALTH_SCORE)     COMMENT = 'Average customer health score',
    c.AVG_LTV                AS AVG(LTV_ANNUALIZED)            COMMENT = 'Average annualized LTV',
    c.TOTAL_LTV              AS SUM(LTV_ANNUALIZED)            COMMENT = 'Total annualized LTV',
    c.TOTAL_REVENUE_OPP      AS SUM(REVENUE_OPPORTUNITY_SCORE) COMMENT = 'Total revenue opportunity',
    c.TOTAL_CAMPAIGN_REVENUE AS SUM(CAMPAIGN_REVENUE_12M)      COMMENT = 'Total campaign revenue last 12 months',
    c.AVG_EMAIL_OPEN_RATE    AS AVG(EMAIL_OPEN_RATE)           COMMENT = 'Average email open rate',
    c.AVG_CLICK_RATE         AS AVG(EMAIL_CLICK_RATE)          COMMENT = 'Average email click-through rate',
    c.AVG_CONVERSION_RATE    AS AVG(CAMPAIGN_CONVERSION_RATE)  COMMENT = 'Average campaign conversion rate',
    c.CUSTOMER_COUNT         AS COUNT(CUSTOMER_ID)             COMMENT = 'Number of distinct customers',
    s.AVG_INTENT_SCORE       AS AVG(INTENT_SCORE)              COMMENT = 'Average segment intent score (60.5-82.9)'
  )
  COMMENT = 'Apex Athletics customer intelligence: CUSTOMER_360 + MICRO_SEGMENTS, 18 dimensions, 18 facts, 12 metrics';

-- ── Cortex Agent ───────────────────────────────────────────────────────────
CREATE OR REPLACE AGENT WRITER_CAMPAIGN_PLANNER
  COMMENT = 'Apex Athletics campaign planning agent for the WRITER quickstart'
  PROFILE = '{"display_name": "WRITER Campaign Planner", "color": "blue"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  orchestration:
    budget:
      seconds: 120
      tokens: 16000

  instructions:
    response: >
      You are the Apex Athletics campaign planner. Lead with specific numbers:
      customer counts, LTV, intent scores, and conversion rates. When recommending
      campaigns, cite the historical campaign that supports the recommendation by
      name. Keep responses concise and structured for a marketer to act on.
    orchestration: >
      Use CustomerAnalyst for any question about customers, segments, counts, LTV,
      churn risk, engagement, intent scores, or conversion rates.
      Use CampaignSearch for questions about past campaign copy, subject lines,
      CTAs, tone, or what has performed well for an audience.
      When asked to recommend an audience for a campaign, call CustomerAnalyst
      first to rank segments, then CampaignSearch to find supporting campaign history.

    sample_questions:
      - question: "Which five micro-segments have the highest intent score?"
      - question: "What campaigns have worked for at-risk customers?"
      - question: "Compare average LTV across churn risk tiers"
      - question: "Which segments should I target for a winter running campaign, and what copy has worked?"

  tools:
    - tool_spec:
        type: cortex_analyst_text_to_sql
        name: CustomerAnalyst
        description: >
          Queries the CUSTOMER_360_SV semantic view for customer and segment
          analytics. Use for segment rankings by intent score, LTV, churn risk,
          engagement scores, customer counts, and campaign conversion rates.

    - tool_spec:
        type: cortex_search
        name: CampaignSearch
        description: >
          Searches 60 historical Apex Athletics campaigns. Use to find past
          subject lines, body copy, CTAs, tone, and performance by audience or topic.

  tool_resources:
    CustomerAnalyst:
      semantic_view: WRITER_SF_QUICKSTART.MARKETING.CUSTOMER_360_SV
      execution_environment:
        type: warehouse
        warehouse: WRITER_QUICKSTART_WH

    CampaignSearch:
      name: WRITER_SF_QUICKSTART.MARKETING.CAMPAIGN_LIBRARY_SEARCH
      max_results: 5
  $$;

-- ── MCP Server ─────────────────────────────────────────────────────────────
CREATE OR REPLACE MCP SERVER WRITER_QUICKSTART_MCP_SERVER
  FROM SPECIFICATION
  $$
  tools:
    - title: "WRITER Campaign Planner"
      name: "campaign-planner"
      type: "CORTEX_AGENT_RUN"
      identifier: "WRITER_SF_QUICKSTART.MARKETING.WRITER_CAMPAIGN_PLANNER"
      description: >
        Recommends Apex Athletics customer micro-segments and retrieves historical
        campaign performance. Use this for any question about which audience to
        target, segment metrics such as intent score, LTV, or churn risk, and what
        campaign copy has performed well before.

    - title: "Save Campaign Brief"
      name: "save-brief"
      type: "GENERIC"
      identifier: "WRITER_SF_QUICKSTART.MARKETING.SAVE_BRIEF"
      description: >
        Saves a completed campaign brief to Snowflake and returns the BRIEF_ID.
        Call this only after the brief has been fully drafted. Re-calling with the
        same brief_id updates the existing brief instead of creating a duplicate.
      config:
        type: "procedure"
        warehouse: "WRITER_QUICKSTART_WH"
        query_timeout: 120
        input_schema:
          type: "object"
          properties:
            P_CAMPAIGN_ID:
              type: "string"
              description: "Campaign identifier, for example CMP-2026-001"
            P_BRIEF_JSON:
              type: "string"
              description: >
                The complete campaign brief serialized as a JSON string. Include
                a brief_id, status, created_by, title, and any brief sections.
          required: ["P_CAMPAIGN_ID", "P_BRIEF_JSON"]
  $$;

-- ── Grants — everything WRITER_QUICKSTART_ROLE needs ───────────────────────
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON WAREHOUSE WRITER_QUICKSTART_WH        TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON DATABASE WRITER_SF_QUICKSTART         TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON SCHEMA WRITER_SF_QUICKSTART.MARKETING TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE CUSTOMER_360     TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE MICRO_SEGMENTS   TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE CAMPAIGN_LIBRARY TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT, INSERT, UPDATE ON TABLE CAMPAIGN_BRIEFS TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON PROCEDURE SAVE_BRIEF(VARCHAR, VARCHAR) TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON SEMANTIC VIEW CUSTOMER_360_SV               TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON CORTEX SEARCH SERVICE CAMPAIGN_LIBRARY_SEARCH TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON AGENT WRITER_CAMPAIGN_PLANNER                TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON MCP SERVER WRITER_QUICKSTART_MCP_SERVER      TO ROLE WRITER_QUICKSTART_ROLE;

-- ── Verify ─────────────────────────────────────────────────────────────────
DESCRIBE AGENT WRITER_CAMPAIGN_PLANNER;
DESCRIBE MCP SERVER WRITER_QUICKSTART_MCP_SERVER;
SHOW CORTEX SEARCH SERVICES IN SCHEMA WRITER_SF_QUICKSTART.MARKETING;
