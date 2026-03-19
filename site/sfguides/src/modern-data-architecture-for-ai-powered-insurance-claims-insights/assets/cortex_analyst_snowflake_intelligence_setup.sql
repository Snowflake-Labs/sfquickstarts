-- =============================================================================
-- Cortex Analyst + Snowflake Intelligence Setup
-- =============================================================================
-- This script enables:
--   1. Cortex Analyst (natural language to SQL via semantic model)
--   2. Snowflake Intelligence (AI agent accessible from Snowsight UI)
--
-- Prerequisites:
--   - INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.CLAIMS_PROCESSED_FEATURES table exists
--   - Semantic model YAML file: semantic_models/claims_semantic_view.yaml
-- =============================================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE INSURANCE_CLAIMS_WH;

-- =============================================================================
-- STEP 1: Upload Semantic Model YAML to Snowflake Stage
-- =============================================================================
-- This enables Cortex Analyst REST API with the stage-based semantic model

CREATE STAGE IF NOT EXISTS INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for Cortex Analyst semantic model YAML files';

-- Run this PUT command from SnowSQL or Snowflake CLI:
PUT claims_semantic_view.yaml @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Verify upload
LIST @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE;

-- =============================================================================
-- STEP 2: Test Cortex Analyst with Stage-Based Semantic Model
-- =============================================================================
-- You can now query Cortex Analyst via REST API using:
--   semantic_model_file: @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE/claims_semantic_view.yaml
--
-- Example REST API call:
-- POST https://<account>.snowflakecomputing.com/api/v2/cortex/analyst/message
-- {
--   "messages": [{"role": "user", "content": [{"type": "text", "text": "Show me high risk fraud claims"}]}],
--   "semantic_model_file": "@INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE/claims_semantic_view.yaml"
-- }

-- =============================================================================
-- STEP 3: Create Semantic View (Required for Cortex Agent / Snowflake Intelligence)
-- =============================================================================
-- Cortex Agents require a SEMANTIC VIEW (not a stage file).
-- The semantic view wraps the YAML model as a Snowflake object.

CREATE OR REPLACE FILE FORMAT INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.YAML_FORMAT 
TYPE = 'CSV' 
FIELD_DELIMITER = NONE 
RECORD_DELIMITER = NONE 
ESCAPE_UNENCLOSED_FIELD = NONE


 CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
    'INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS',
    (SELECT $1::VARCHAR FROM
  @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.SEMANTIC_MODEL_STAGE/claims_semantic_view.yaml (FILE_FORMAT =>
  'INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.YAML_FORMAT'))
  )

-- =============================================================================
-- STEP 4: Setup Snowflake Intelligence Database and Schema
-- =============================================================================
-- Agents for Snowflake Intelligence MUST be in SNOWFLAKE_INTELLIGENCE.AGENTS schema

CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
GRANT USAGE ON DATABASE SNOWFLAKE_INTELLIGENCE TO ROLE PUBLIC;

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_INTELLIGENCE.AGENTS;
GRANT USAGE ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE PUBLIC;

-- Grant CREATE AGENT to roles that need to create agents
GRANT CREATE AGENT ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE ACCOUNTADMIN;
-- GRANT CREATE AGENT ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE SALES_ENGINEER;

-- =============================================================================
-- STEP 5: Create Snowflake Intelligence Agent
-- =============================================================================
-- This agent uses Cortex Analyst (text-to-SQL) with your semantic view

CREATE OR REPLACE AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.INSURANCE_CLAIMS_AGENT
  COMMENT = 'AI agent for insurance claims analytics, fraud detection, and operational metrics'
  PROFILE = '{"display_name": "Insurance Claims Analyst" }'
  FROM SPECIFICATION $$
  {
    "models": {
      "orchestration": "claude-4-sonnet"
    },
    "instructions": {
      "orchestration": "Use the claims_analyst tool for all questions about insurance claims, fraud detection, policy details, estimates, and investigations. Always query the data before providing answers.",
      "response": "Provide clear, data-driven insights. When showing claim data, highlight fraud risk scores and SIU referral status. Use specific numbers and percentages. For fraud-related questions, prioritize claims with FRAUD_RISK_CATEGORY = 'High Risk' or ML_FRAUD_RISK_SCORE > 70."
    },
    "tools": [
      {
        "tool_spec": {
          "type": "cortex_analyst_text_to_sql",
          "name": "claims_analyst",
          "description": "Query insurance claims data including claim details, fraud risk scores, SIU investigations, policy information, estimates, and operational metrics. Use for questions about claims, fraud detection, loss types, claimants, and policy analytics."
        }
      }
    ],
    "tool_resources": {
      "claims_analyst": {
        "semantic_view": "INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.INSURANCE_CLAIMS_ANALYTICS",
        "execution_environment": {
          "type": "warehouse",
          "warehouse": "INSURANCE_CLAIMS_WH"
        },
        "query_timeout": 60
      }
    }
  }
  $$;

-- =============================================================================
-- STEP 6: Grant Access Permissions
-- =============================================================================

-- Grant access to the agent
GRANT USAGE ON AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.INSURANCE_CLAIMS_AGENT TO ROLE PUBLIC;

-- Grant access to the semantic view (required for the agent to work)
GRANT SELECT ON SEMANTIC VIEW INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.INSURANCE_CLAIMS_SEMANTIC_VIEW TO ROLE PUBLIC;

-- Grant access to underlying table
GRANT SELECT ON TABLE INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.CLAIMS_PROCESSED_FEATURES TO ROLE PUBLIC;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE INSURANCE_CLAIMS_WH TO ROLE PUBLIC;

-- =============================================================================
-- STEP 7: Verify Setup
-- =============================================================================

-- List agents
SHOW AGENTS IN SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS;

-- Describe agent
DESC AGENT SNOWFLAKE_INTELLIGENCE.AGENTS.INSURANCE_CLAIMS_AGENT;


