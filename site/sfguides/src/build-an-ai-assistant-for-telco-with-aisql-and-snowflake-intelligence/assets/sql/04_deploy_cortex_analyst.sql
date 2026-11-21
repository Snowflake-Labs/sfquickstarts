-- ============================================================================
-- Build an AI Assistant for Telco using AISQL and Snowflake Intelligence
-- Script 04: Deploy Cortex Analyst and Snowflake Intelligence Agent
-- ============================================================================
-- Description: Uploads semantic model YAML files and creates the AI Agent
-- Prerequisites: Run scripts 01-03 first
-- ============================================================================

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA CORTEX_ANALYST;

ALTER SESSION SET QUERY_TAG = '{"origin":"sf_sit-is", "name":"Build an AI Assistant for Telco using AISQL and Snowflake Intelligence", "version":{"major":1, "minor":0},"attributes":{"is_quickstart":1, "source":"sql"}}';

-- ============================================================================
-- Step 1: Create Stage for Semantic Models
-- ============================================================================

CREATE OR REPLACE STAGE TELCO_OPERATIONS_AI.CORTEX_ANALYST.cortex_analyst
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- ============================================================================
-- Step 2: Copy Semantic Model YAML Files from Git Repository
-- ============================================================================

COPY FILES INTO @TELCO_OPERATIONS_AI.CORTEX_ANALYST.cortex_analyst
FROM @SNOWFLAKE_QUICKSTART_REPOS.GIT_REPOS.TELCO_AI_REPO/branches/master/site/sfguides/src/build-an-ai-assistant-for-telco-with-aisql-and-snowflake-intelligence/assets/semantic_models/
PATTERN = '.*\.yaml';

-- Refresh stage to update directory table
ALTER STAGE TELCO_OPERATIONS_AI.CORTEX_ANALYST.cortex_analyst REFRESH;

-- Verify files uploaded
SELECT 'Semantic model YAML files:' as info;
LIST @TELCO_OPERATIONS_AI.CORTEX_ANALYST.cortex_analyst;

-- ============================================================================
-- Step 3: Create Supporting Analytical Views
-- ============================================================================

-- View 1: Call Center Performance Metrics
CREATE OR REPLACE VIEW TELCO_OPERATIONS_AI.CORTEX_ANALYST.CALL_CENTER_ANALYTICS
COMMENT = 'Analytical view for call center performance metrics'
AS
SELECT 
    DATE_TRUNC('day', cs.CALL_TIMESTAMP) as call_date,
    cs.CALL_CATEGORY,
    cs.RESOLUTION_STATUS,
    COUNT(DISTINCT cs.CALL_ID) as total_calls,
    AVG(cs.CALL_DURATION_SECONDS) as avg_call_duration_seconds,
    AVG(cs.AVG_SENTIMENT_SCORE) as avg_sentiment,
    AVG(cs.CUSTOMER_SENTIMENT_AVG) as avg_customer_sentiment,
    AVG(cs.AGENT_SENTIMENT_AVG) as avg_agent_sentiment,
    COUNT(DISTINCT cs.CUSTOMER_ID) as unique_customers,
    COUNT(DISTINCT cs.AGENT_ID) as unique_agents
FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.CALL_SENTIMENT_SUMMARY cs
GROUP BY call_date, cs.CALL_CATEGORY, cs.RESOLUTION_STATUS;

-- View 2: Customer Health Dashboard
CREATE OR REPLACE VIEW TELCO_OPERATIONS_AI.CORTEX_ANALYST.CUSTOMER_HEALTH_ANALYTICS
COMMENT = 'Analytical view for customer health and satisfaction metrics'
AS
SELECT 
    cp.CUSTOMER_ID,
    cp.CUSTOMER_NAME,
    cp.CUSTOMER_SEGMENT,
    cp.SERVICE_PLAN,
    cp.TENURE_MONTHS,
    cp.MONTHLY_CHARGES,
    cp.CHURN_RISK_SCORE,
    COUNT(DISTINCT cs.CALL_ID) as total_calls_30d,
    AVG(cs.AVG_SENTIMENT_SCORE) as avg_call_sentiment,
    COUNT(DISTINCT st.TICKET_ID) as total_tickets_30d,
    AVG(st.CUSTOMER_SATISFACTION_RATING) as avg_satisfaction_rating
FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.CUSTOMER_PROFILES cp
LEFT JOIN TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.CALL_SENTIMENT_SUMMARY cs 
    ON cp.CUSTOMER_ID = cs.CUSTOMER_ID
    AND cs.CALL_TIMESTAMP >= DATEADD(day, -30, CURRENT_TIMESTAMP())
LEFT JOIN TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SUPPORT_TICKETS st 
    ON cp.CUSTOMER_ID = st.CUSTOMER_ID
    AND st.CREATED_AT >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 
    cp.CUSTOMER_ID, cp.CUSTOMER_NAME, cp.CUSTOMER_SEGMENT,
    cp.SERVICE_PLAN, cp.TENURE_MONTHS, cp.MONTHLY_CHARGES, cp.CHURN_RISK_SCORE;

-- View 3: Agent Performance Dashboard
CREATE OR REPLACE VIEW TELCO_OPERATIONS_AI.CORTEX_ANALYST.AGENT_PERFORMANCE_ANALYTICS
COMMENT = 'Analytical view for agent performance and quality metrics'
AS
SELECT 
    ap.AGENT_ID,
    ap.AGENT_NAME,
    ap.TEAM,
    ap.CERTIFICATION_LEVEL,
    ap.CALLS_HANDLED_LAST_30_DAYS,
    ap.AVG_CALL_DURATION_SECONDS,
    ap.FIRST_CALL_RESOLUTION_RATE,
    ap.AVG_CUSTOMER_SENTIMENT,
    ap.AVG_SATISFACTION_RATING,
    ap.ESCALATION_RATE,
    ap.QUALITY_SCORE,
    COUNT(DISTINCT st.TICKET_ID) as tickets_handled,
    AVG(st.RESOLUTION_TIME_HOURS) as avg_resolution_time_hours
FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.AGENT_PERFORMANCE ap
LEFT JOIN TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SUPPORT_TICKETS st 
    ON ap.AGENT_ID = st.AGENT_ID
    AND st.CREATED_AT >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 
    ap.AGENT_ID, ap.AGENT_NAME, ap.TEAM, ap.CERTIFICATION_LEVEL,
    ap.CALLS_HANDLED_LAST_30_DAYS, ap.AVG_CALL_DURATION_SECONDS,
    ap.FIRST_CALL_RESOLUTION_RATE, ap.AVG_CUSTOMER_SENTIMENT,
    ap.AVG_SATISFACTION_RATING, ap.ESCALATION_RATE, ap.QUALITY_SCORE;

-- Semantic Models Info View
CREATE OR REPLACE VIEW TELCO_OPERATIONS_AI.CORTEX_ANALYST.SEMANTIC_MODELS_INFO
AS
SELECT 
    'customer_feedback' as model_name,
    'Customer feedback analysis from call transcripts and complaint documents' as description,
    '@cortex_analyst/customer_feedback.yaml' as yaml_path
UNION ALL
SELECT 
    'infrastructure_capacity' as model_name,
    'Infrastructure capacity monitoring and utilization analysis' as description,
    '@cortex_analyst/infrastructure_capacity.yaml' as yaml_path
UNION ALL
SELECT 
    'network_performance' as model_name,
    'Network performance metrics and tower health analysis' as description,
    '@cortex_analyst/network_performance.yaml' as yaml_path;

-- ============================================================================
-- Step 4: Grant Permissions
-- ============================================================================

GRANT USAGE ON SCHEMA CORTEX_ANALYST TO ROLE TELCO_ANALYST_ROLE;
GRANT SELECT ON ALL VIEWS IN SCHEMA CORTEX_ANALYST TO ROLE TELCO_ANALYST_ROLE;
GRANT READ ON STAGE TELCO_OPERATIONS_AI.CORTEX_ANALYST.cortex_analyst TO ROLE TELCO_ANALYST_ROLE;

-- ============================================================================
-- Step 5: Create Snowflake Intelligence Agent
-- ============================================================================

-- Use ACCOUNTADMIN to ensure we have privileges to create the Intelligence database
-- and grant necessary permissions
USE ROLE ACCOUNTADMIN;

-- Create database for Snowflake Intelligence
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_INTELLIGENCE.AGENTS;

-- Grant Snowflake Intelligence privileges to TELCO_ANALYST_ROLE
-- INTELLIGENCE_MODIFY is required to add agents with custom appearances
GRANT DATABASE ROLE SNOWFLAKE.INTELLIGENCE_MODIFY TO ROLE TELCO_ANALYST_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.INTELLIGENCE_USER TO ROLE TELCO_ANALYST_ROLE;

-- Grant ownership/usage on the Intelligence database and schema
GRANT USAGE ON DATABASE SNOWFLAKE_INTELLIGENCE TO ROLE TELCO_ANALYST_ROLE;
GRANT USAGE ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE TELCO_ANALYST_ROLE;
GRANT CREATE AGENT ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE TELCO_ANALYST_ROLE;

-- Grant access to underlying objects needed by the agent
GRANT USAGE ON DATABASE TELCO_OPERATIONS_AI TO ROLE TELCO_ANALYST_ROLE;
GRANT USAGE ON SCHEMA TELCO_OPERATIONS_AI.CORTEX_ANALYST TO ROLE TELCO_ANALYST_ROLE;
GRANT USAGE ON SCHEMA TELCO_OPERATIONS_AI.DEFAULT_SCHEMA TO ROLE TELCO_ANALYST_ROLE;
GRANT READ ON STAGE TELCO_OPERATIONS_AI.CORTEX_ANALYST.CORTEX_ANALYST TO ROLE TELCO_ANALYST_ROLE;

-- Now switch to TELCO_ANALYST_ROLE to create the agent
-- This ensures the agent is OWNED by TELCO_ANALYST_ROLE (not ACCOUNTADMIN)
USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE SNOWFLAKE_INTELLIGENCE;
USE SCHEMA AGENTS;

CREATE OR REPLACE AGENT SNOWFLAKE_INTELLIGENCE.AGENTS."Telco Operations AI Agent"
WITH PROFILE = '{
    "display_name": "NovaConnect Intelligence Agent",
    "avatar": "PowerAgentIcon",
    "color": "var(--chartDim_6-x12aliq8)"
}'
COMMENT = '
Intelligent assistant for telco operations that combines semantic queries 
and search across network performance, infrastructure capacity, and customer 
feedback. Ask questions about network issues, customer sentiment, support 
tickets, and call transcripts in natural language.
'
FROM SPECIFICATION $$
{
  "models": {
    "orchestration": "auto"
  },
  "orchestration": {},
  "instructions": {
    "orchestration": "when using charts if you are comparing measure in a visualisation you may need to convert to logs so you can see the pattern",
    "sample_questions": [
      {"question": "Which regions have the highest network latency issues?"},
      {"question": "Show me 5G towers operating above 80% capacity"},
      {"question": "Find calls mentioning network connectivity problems"},
      {"question": "What are the top 3 customer complaints in October 2025?"},
      {"question": "Find support tickets about billing issues"},
      {"question": "Which customer segments have the highest churn risk?"},
      {"question": "Are network issues correlated with negative customer sentiment?"},
      {"question": "Show me regions with both high latency and customer complaints"},
      {"question": "What percentage of calls mention competitor names?"}
    ]
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "network_performance",
        "description": "Network performance metrics for telecom cell towers across regions. Contains latency, speed measurements, user activity, and service quality indicators."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "Customer_Feedback",
        "description": "Customer feedback analytics with sentiment analysis, feedback categorization, and customer details including churn information."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "Infrastructure_Capacity",
        "description": "Infrastructure capacity metrics for telecom towers including bandwidth utilization, equipment status, and capacity planning data."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_search",
        "name": "CALL_TRANSCRIPTS",
        "description": "Search customer call transcripts for specific issues, keywords, or topics"
      }
    },
    {
      "tool_spec": {
        "type": "cortex_search",
        "name": "SUPPORT_TICKETS",
        "description": "Search support tickets for issue tracking and resolution analysis"
      }
    }
  ],
  "tool_resources": {
    "network_performance": {
      "execution_environment": {
        "type": "warehouse",
        "warehouse": ""
      },
      "semantic_model_file": "@TELCO_OPERATIONS_AI.CORTEX_ANALYST.CORTEX_ANALYST/network_performance.yaml"
    },
    "Customer_Feedback": {
      "execution_environment": {
        "query_timeout": 30,
        "type": "warehouse",
        "warehouse": ""
      },
      "semantic_model_file": "@TELCO_OPERATIONS_AI.CORTEX_ANALYST.CORTEX_ANALYST/customer_feedback.yaml"
    },
    "Infrastructure_Capacity": {
      "execution_environment": {
        "query_timeout": 30,
        "type": "warehouse",
        "warehouse": ""
      },
      "semantic_model_file": "@TELCO_OPERATIONS_AI.CORTEX_ANALYST.CORTEX_ANALYST/infrastructure_capacity.yaml"
    },
    "CALL_TRANSCRIPTS": {
      "max_results": 4,
      "search_service": "TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.CALL_TRANSCRIPT_SEARCH"
    },
    "SUPPORT_TICKETS": {
      "max_results": 4,
      "search_service": "TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.SUPPORT_TICKET_SEARCH"
    }
  }
}
$$;

SELECT 'Cortex Analyst and Snowflake Intelligence Agent deployed!' AS status,
       'SNOWFLAKE_INTELLIGENCE.AGENTS."Telco Operations AI Agent"' AS agent_name,
       'TELCO_ANALYST_ROLE' AS owner_role,
       CURRENT_TIMESTAMP() AS deployed_at;

