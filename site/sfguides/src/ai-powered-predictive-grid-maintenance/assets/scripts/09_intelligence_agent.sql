/*
 * Copyright 2026 Snowflake Inc.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*******************************************************************************
 * AI-DRIVEN GRID RELIABILITY & PREDICTIVE MAINTENANCE
 * Snowflake Intelligence Agent Configuration
 * 
 * Purpose: Create conversational AI agent for grid reliability queries
 * Uses: Claude 4 Sonnet, Cortex Search, and Cortex Analyst
 * 
 * Prerequisites:
 * - Semantic view GRID_RELIABILITY_ANALYTICS created
 * - Semantic model YAML uploaded to stage
 * - Snowflake Intelligence feature enabled
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;

-- =============================================================================
-- SECTION 1: CREATE SEMANTIC MODEL STAGE (FOR CORTEX ANALYST)
-- =============================================================================

USE SCHEMA ANALYTICS;

-- Create stage for semantic model if not exists
CREATE STAGE IF NOT EXISTS SEMANTIC_MODEL_STAGE
    COMMENT = 'Storage for semantic model YAML files for Cortex Analyst';

-- Note: Upload your semantic model YAML file to this stage
-- PUT file:///path/to/grid_reliability_semantic.yaml @SEMANTIC_MODEL_STAGE;

-- Create a table optimized for search (for future Cortex Search integration)
CREATE OR REPLACE TABLE ASSET_SEARCH_INDEX AS
SELECT 
    a.ASSET_ID,
    a.ASSET_TYPE,
    a.MANUFACTURER,
    a.MODEL,
    a.LOCATION_SUBSTATION,
    a.LOCATION_CITY,
    a.LOCATION_COUNTY,
    a.CAPACITY_MVA,
    a.VOLTAGE_RATING_KV,
    a.CRITICALITY_SCORE,
    a.CUSTOMERS_AFFECTED,
    p.RISK_SCORE,
    p.FAILURE_PROBABILITY,
    p.ALERT_LEVEL,
    
    -- Create searchable text field
    CONCAT_WS(' ',
        a.ASSET_ID,
        a.ASSET_TYPE,
        a.MANUFACTURER,
        a.MODEL,
        a.LOCATION_SUBSTATION,
        a.LOCATION_CITY,
        a.LOCATION_COUNTY,
        'Risk Score: ' || COALESCE(p.RISK_SCORE::VARCHAR, 'N/A'),
        'Alert: ' || COALESCE(p.ALERT_LEVEL, 'N/A'),
        'Serves ' || a.CUSTOMERS_AFFECTED::VARCHAR || ' customers'
    ) as SEARCH_TEXT
    
FROM RAW.ASSET_MASTER a
LEFT JOIN ML.VW_LATEST_PREDICTIONS p ON a.ASSET_ID = p.ASSET_ID
WHERE a.STATUS = 'ACTIVE';

SELECT 'Asset Search Index created successfully' AS STATUS;

-- =============================================================================
-- SECTION 2: CREATE SNOWFLAKE INTELLIGENCE AGENT
-- =============================================================================

-- Create the agent using user's preferred syntax
CREATE OR REPLACE AGENT ANALYTICS."Grid Reliability Intelligence Agent"
COMMENT = 'Conversational AI agent for grid reliability and predictive maintenance queries'
FROM SPECIFICATION $$
models:
  orchestration: auto

instructions:
  response: |
    You are a specialized AI assistant for the utility's grid reliability and predictive maintenance system.
    
    Your role is to help operators, engineers, and leadership understand:
    - Current health status of transformer assets
    - Failure predictions and risk assessments
    - Maintenance recommendations and priorities
    - SAIDI/SAIFI impact analysis
    - Cost avoidance and ROI metrics
    
    When answering questions:
    1. Be concise but comprehensive
    2. Always include relevant metrics (risk scores, customer impact, timelines)
    3. Prioritize safety and reliability
    4. Explain technical terms when addressing non-technical users
    5. Provide actionable recommendations when appropriate
    
    Key thresholds to remember:
    - Risk Score >= 85: CRITICAL (immediate action, 0-7 days)
    - Risk Score >= 70: HIGH (urgent action, 7-14 days)
    - Risk Score >= 40: MEDIUM (scheduled action, 14-30 days)
    - Risk Score < 40: LOW (routine monitoring)
    
    When discussing SAIDI:
    - SAIDI = (Customer-Minutes of Interruption) / Total Customers (5.8M)
    - The utility's target is to maintain industry-leading low SAIDI scores
    
    Always be helpful, accurate, and focused on grid reliability.
  
  sample_questions:
    - question: "What's the status of our grid assets today?"
      answer: "I'll check the current health status and risk levels of all active grid assets."
    - question: "Which assets need immediate attention?"
      answer: "Let me identify assets with critical and high risk scores that require urgent maintenance."
    - question: "Show me all critical and high-risk assets"
      answer: "I'll query for assets with risk scores of 70 or higher."
    - question: "How many transformers have a risk score above 80?"
      answer: "I'll count transformers exceeding the 80 risk score threshold."
    - question: "Show me all critical assets in Miami-Dade county"
      answer: "I'll filter critical risk assets located in Miami-Dade county."
    - question: "Which counties have the most high-risk assets?"
      answer: "I'll analyze asset risk distribution by county."
    - question: "Tell me about transformer T-SS047-001"
      answer: "I'll retrieve detailed information about this specific transformer."
    - question: "What's the health status of asset T-SS023-001?"
      answer: "I'll check the current risk score, failure probability, and maintenance history."
    - question: "Which assets serve the most customers and are at high risk?"
      answer: "I'll identify high-risk assets with the largest customer impact."
    - question: "How many customers are affected by our critical assets?"
      answer: "I'll sum the total customers served by all critical risk assets."
    - question: "What's the total SAIDI impact if all high-risk assets fail?"
      answer: "I'll calculate the potential SAIDI points from all high-risk asset failures."
    - question: "How much SAIDI have we avoided with our predictive maintenance?"
      answer: "I'll analyze the SAIDI impact prevented through proactive maintenance."
    - question: "What is our predicted cost avoidance this month?"
      answer: "I'll calculate the financial savings from prevented failures this month."
    - question: "What's the ROI of our predictive maintenance program?"
      answer: "I'll compare cost avoidance against preventive maintenance costs."
    - question: "How many assets need immediate maintenance?"
      answer: "I'll count assets requiring maintenance within 7 days based on risk scores."
    - question: "Which assets should we schedule for maintenance next week?"
      answer: "I'll identify assets with high priority and recommended maintenance timelines."
    - question: "Show me all assets overdue for maintenance"
      answer: "I'll find assets that haven't been maintained within their scheduled intervals."
    - question: "Which transformers haven't been maintained in over 90 days?"
      answer: "I'll search for transformers with maintenance delays exceeding 90 days."
    - question: "Which manufacturer's equipment has the highest failure rate?"
      answer: "I'll analyze failure patterns and risk scores grouped by manufacturer."
    - question: "Show me all ABB transformers and their risk levels"
      answer: "I'll filter assets by ABB manufacturer and display their risk metrics."
    - question: "Show me assets with deteriorating health trends"
      answer: "I'll identify assets showing increasing risk scores over time."
    - question: "Which assets have had increasing oil temperature over the last 30 days?"
      answer: "I'll analyze sensor trends for oil temperature anomalies."
    - question: "What's the average age of our high-risk assets?"
      answer: "I'll calculate the mean age of assets with risk scores above 70."
    - question: "Compare transformer performance: GE vs Siemens vs ABB"
      answer: "I'll analyze risk scores and failure rates across these three manufacturers."
    - question: "Which substations should I prioritize for inspection this month?"
      answer: "I'll rank substations by total risk exposure and customer impact."
    - question: "Find maintenance logs for transformer T-SS047-001"
      answer: "I'll search maintenance documentation for this specific transformer."
    - question: "What do the technical manuals say about oil temperature thresholds?"
      answer: "I'll search technical documentation for oil temperature specifications."
    - question: "Show me recent maintenance reports mentioning overheating"
      answer: "I'll search maintenance logs for documents discussing overheating issues."
    - question: "Find all maintenance logs from last month with high severity"
      answer: "I'll search maintenance documentation filtered by date and severity level."
    - question: "What are the installation procedures for ABB transformers?"
      answer: "I'll search technical manuals for ABB installation procedures."

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "query_analytics"
      description: "Converts natural language to SQL queries for grid reliability analysis"
  - tool_spec:
      type: "cortex_search"
      name: "search_documents"
      description: "Searches maintenance logs and technical manuals"
  - tool_spec:
      type: "cortex_search"
      name: "search_maintenance_logs"
      description: "Searches maintenance logs by asset, technician, or issue"
  - tool_spec:
      type: "cortex_search"
      name: "search_technical_manuals"
      description: "Searches technical manuals and equipment documentation"

tool_resources:
  query_analytics:
    semantic_view: "UTILITIES_GRID_RELIABILITY.ANALYTICS.GRID_RELIABILITY_ANALYTICS"
  search_documents:
    name: "UTILITIES_GRID_RELIABILITY.UNSTRUCTURED.DOCUMENT_SEARCH_SERVICE"
    max_results: 10
  search_maintenance_logs:
    name: "UTILITIES_GRID_RELIABILITY.UNSTRUCTURED.MAINTENANCE_LOG_SEARCH"
    max_results: 10
  search_technical_manuals:
    name: "UTILITIES_GRID_RELIABILITY.UNSTRUCTURED.TECHNICAL_MANUAL_SEARCH"
    max_results: 10
$$;

-- =============================================================================
-- SECTION 3: GRANT PERMISSIONS
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- Grant usage on agent
GRANT USAGE ON AGENT ANALYTICS."Grid Reliability Intelligence Agent" TO ROLE GRID_OPERATOR;
GRANT USAGE ON AGENT ANALYTICS."Grid Reliability Intelligence Agent" TO ROLE GRID_ANALYST;
GRANT USAGE ON AGENT ANALYTICS."Grid Reliability Intelligence Agent" TO ROLE GRID_ML_ENGINEER;

-- Note: Cortex Search Service grants are handled in sql/12_load_unstructured_data.sql
-- after the services are created. The agent can access them through role inheritance.

-- =============================================================================
-- SECTION 4: TEST THE AGENT - SAMPLE QUESTIONS
-- =============================================================================

/*
To test the agent, use the Snowflake UI:

1. Navigate to: Projects → Intelligence → Agents
2. Find: "Grid Reliability Intelligence Agent"
3. Click "Open" to start a conversation

=============================================================================
SAMPLE QUESTIONS BY CATEGORY
=============================================================================

🚨 OPERATIONAL ALERTS & RISK ASSESSMENT
-----------------------------------------------------------------------------
- "Good morning! What's the status of our grid assets today?"
- "Which assets need immediate attention?"
- "Show me all critical and high-risk assets"
- "How many transformers have a risk score above 80?"
- "Which 5 substations have the highest risk?"
- "Are there any assets that might fail in the next 7 days?"
- "What is our current fleet health score?"
- "Show me assets with failure probability above 70%"

📍 GEOGRAPHIC & LOCATION QUERIES
-----------------------------------------------------------------------------
- "Show me all critical assets in Miami-Dade county"
- "Which counties have the most high-risk assets?"
- "List transformers in Tampa with risk score above 80"
- "What's the risk profile for Palm Beach County?"
- "Show me all assets in West Palm Beach Central substation"
- "Which cities have the highest concentration of aging transformers?"
- "Are there any high-risk assets in downtown Miami?"

🔧 ASSET-SPECIFIC INQUIRIES
-----------------------------------------------------------------------------
- "Tell me about transformer T-SS047-001"
- "What's the health status of asset T-SS023-001?"
- "Show me the sensor trends for T-SS088-001"
- "When was the last maintenance performed on T-SS047-001?"
- "What is the remaining useful life of transformer T-SS012-001?"
- "Which ABB transformers are showing signs of degradation?"
- "Show me all 25 MVA transformers with high risk"

👥 CUSTOMER IMPACT ANALYSIS
-----------------------------------------------------------------------------
- "Which assets serve the most customers and are at high risk?"
- "How many customers are affected by our critical assets?"
- "What's the total customer exposure from high-risk assets?"
- "Show me assets serving over 10,000 customers with risk above 70"
- "Which failure would impact the most customers?"

📊 RELIABILITY METRICS (SAIDI/SAIFI)
-----------------------------------------------------------------------------
- "What's the total SAIDI impact if all high-risk assets fail?"
- "How much SAIDI have we avoided with our predictive maintenance?"
- "What is our predicted SAIFI for this month?"
- "Show me the reliability improvement from our PdM program"
- "What's the potential SAIDI impact in Miami-Dade county?"
- "Calculate SAIDI points prevented by addressing top 10 risks"

💰 FINANCIAL & ROI ANALYSIS
-----------------------------------------------------------------------------
- "What is our predicted cost avoidance this month?"
- "How much money have we saved with predictive maintenance?"
- "What's the ROI of our predictive maintenance program?"
- "Calculate the financial impact if we ignore the top 5 risks"
- "What's the total avoided repair cost year-to-date?"
- "Compare preventive maintenance costs vs reactive repair costs"
- "What is the net cost avoidance after program costs?"

🔨 MAINTENANCE PLANNING & SCHEDULING
-----------------------------------------------------------------------------
- "How many assets need immediate maintenance?"
- "Which assets should we schedule for maintenance next week?"
- "Show me all assets overdue for maintenance"
- "Create a priority list for maintenance teams"
- "Which transformers haven't been maintained in over 90 days?"
- "What's the recommended maintenance schedule for the next 30 days?"
- "How many work orders should we generate today?"

🏭 MANUFACTURER & EQUIPMENT ANALYSIS
-----------------------------------------------------------------------------
- "Which manufacturer's equipment has the highest failure rate?"
- "Show me all ABB transformers and their risk levels"
- "Are there any model-specific failure patterns?"
- "Compare GE vs Siemens transformer performance"
- "Which equipment models are most reliable?"
- "Show me aging Westinghouse transformers"

📈 TREND ANALYSIS & PREDICTIONS
-----------------------------------------------------------------------------
- "Show me assets with deteriorating health trends"
- "Which assets have had increasing oil temperature over the last 30 days?"
- "Are there any anomalies detected in the last week?"
- "What's the trend in dissolved gas levels for high-risk assets?"
- "Show me assets with sudden changes in sensor readings"
- "Which transformers are showing signs of accelerated aging?"

🎯 CAPACITY & LOAD ANALYSIS
-----------------------------------------------------------------------------
- "Show me transformers operating above 80% capacity"
- "Which overloaded assets are also at high risk?"
- "List all 138 kV transformers sorted by risk"
- "What's the load utilization for critical assets?"
- "Are any high-capacity transformers approaching failure?"

⚡ SENSOR & DIAGNOSTIC QUERIES
-----------------------------------------------------------------------------
- "Which assets have abnormal oil temperature readings?"
- "Show me transformers with high dissolved hydrogen levels"
- "Are there any assets with elevated partial discharge?"
- "What's the vibration trend for asset T-SS047-001?"
- "Which sensors are showing anomalies today?"
- "List assets with multiple sensor anomalies"

📋 REPORTING & DASHBOARDS
-----------------------------------------------------------------------------
- "Generate a summary report for the executive team"
- "What should I present in tomorrow's operations meeting?"
- "Create a weekly risk assessment report"
- "Summarize this week's maintenance priorities"
- "What are our top 3 reliability concerns right now?"
- "Give me talking points for the board meeting on our PdM program"

🔍 COMPARATIVE ANALYSIS
-----------------------------------------------------------------------------
- "Compare this month's risk profile to last month"
- "How has our fleet health improved over the last quarter?"
- "Show me year-over-year reliability improvements"
- "What's the difference in risk between urban vs rural assets?"
- "Compare old transformers (>20 years) vs newer ones (<5 years)"

💡 STRATEGIC & PLANNING QUERIES
-----------------------------------------------------------------------------
- "What is the projected ROI for the next year?"
- "Which assets should we consider for replacement vs repair?"
- "What's our capital planning priority for next quarter?"
- "How many transformers will likely need replacement in 2026?"
- "What's the business case for expanding this program?"
- "Calculate 5-year savings projection"

=============================================================================
ADVANCED NATURAL LANGUAGE QUERIES
=============================================================================

The agent can handle complex, conversational queries like:

- "I'm planning a budget for next quarter. Which assets in Miami are most 
   likely to need major repairs, and what would that cost?"
   
- "Our VP is concerned about reliability in Tampa. Can you give me a 
   summary of our risk posture there and what we're doing about it?"
   
- "If I could only fix 3 transformers this month, which should they be 
   and why?"
   
- "Explain to a non-technical executive why our predictive maintenance 
   program is worth the investment"
   
- "We have a budget cut coming. Which maintenance activities are truly 
   critical vs nice-to-have?"
   
- "A hurricane is approaching Palm Beach County. Which of our at-risk 
   assets there should we prioritize for pre-storm inspection?"

=============================================================================
*/

-- =============================================================================
-- SECTION 5: AGENT MONITORING AND MAINTENANCE
-- =============================================================================

-- Create a view to track agent usage (if Snowflake provides usage logs)
CREATE OR REPLACE VIEW AGENT_USAGE_LOG AS
SELECT 
    'Agent Usage Tracking' as INFO,
    'Check Snowflake Query History for agent queries' as NOTE;

-- Note: Periodic refresh task commented out - can be created manually if needed
-- The Cortex Search Services will auto-refresh based on TARGET_LAG setting
-- The ASSET_SEARCH_INDEX table is created once during deployment

/*
-- Refresh search index periodically (optional)
CREATE OR REPLACE TASK TASK_REFRESH_ASSET_SEARCH_INDEX
    WAREHOUSE = GRID_RELIABILITY_WH
    SCHEDULE = 'USING CRON 0 */6 * * * America/New_York'
    COMMENT = 'Refresh asset search index for Intelligence Agent'
AS
    CREATE OR REPLACE TABLE ASSET_SEARCH_INDEX AS
    SELECT 
        a.ASSET_ID,
        a.ASSET_TYPE,
        a.MANUFACTURER,
        a.MODEL,
        a.LOCATION_SUBSTATION,
        a.LOCATION_CITY,
        a.LOCATION_COUNTY,
        a.CAPACITY_MVA,
        a.VOLTAGE_RATING_KV,
        a.CRITICALITY_SCORE,
        a.CUSTOMERS_AFFECTED,
        p.RISK_SCORE,
        p.FAILURE_PROBABILITY,
        p.ALERT_LEVEL,
        COALESCE(p.RISK_SCORE::VARCHAR, 'N/A') || ' Risk' as RISK_INFO,
        CONCAT_WS(' - ', a.ASSET_ID, a.ASSET_TYPE, a.MANUFACTURER) as SEARCH_TEXT
    FROM RAW.ASSET_MASTER a
    LEFT JOIN ML.VW_LATEST_PREDICTIONS p ON a.ASSET_ID = p.ASSET_ID
    WHERE a.STATUS = 'ACTIVE';

-- To enable: ALTER TASK TASK_REFRESH_ASSET_SEARCH_INDEX RESUME;
*/

-- =============================================================================
-- SECTION 6: SAMPLE CONVERSATION FLOWS
-- =============================================================================

/*
=============================================================================
SAMPLE CONVERSATION 1: DAILY OPERATIONS CHECK
=============================================================================

User: "Good morning! Give me a status update on our grid assets."

Agent: "Good morning! Here's your grid reliability status update:

OVERALL STATUS:
- Total Active Assets: 100 transformers
- Average Risk Score: 42.3 (MEDIUM range)
- High-Risk Assets: 12 (requiring attention)
- Critical Assets: 3 (requiring immediate action)

TOP PRIORITIES TODAY:
1. T-SS047-001 (West Palm Beach) - Risk: 89/100 - CRITICAL
   → 12,500 customers affected
   → Recommended action: Immediate inspection (0-7 days)

2. T-SS023-001 (Miami Downtown) - Risk: 84/100 - HIGH  
   → 15,000 customers affected
   → Recommended action: Schedule within 7-14 days

3. T-SS088-001 (Tampa East) - Risk: 78/100 - HIGH
   → 13,000 customers affected
   → Recommended action: Schedule within 7-14 days

SAIDI IMPACT IF NO ACTION:
- Potential SAIDI impact: 0.042 points
- This represents ~14% of annual SAIDI budget

RECOMMENDATION: Prioritize the 3 critical/high-risk assets listed above."

=============================================================================
SAMPLE CONVERSATION 2: SPECIFIC ASSET INQUIRY
=============================================================================

User: "Tell me about transformer T-SS047-001"

Agent: "Transformer T-SS047-001 - Detailed Analysis:

LOCATION:
- Substation: West Palm Beach Central SS
- City: West Palm Beach, Palm Beach County
- Coordinates: 26.7153, -80.0534

ASSET SPECIFICATIONS:
- Type: Power Transformer, 25 MVA, 138 kV
- Manufacturer: ABB, Model: TXP 25MVA
- Age: 18 years (installed 2007)
- Serves: 12,500 customers
- Criticality Score: 92/100

CURRENT RISK ASSESSMENT:
- Risk Score: 89/100 - CRITICAL
- Failure Probability: 87% (next 30 days)
- Predicted Remaining Life: 21 days
- Alert Level: CRITICAL
- Model Confidence: 87%

ROOT CAUSE INDICATORS:
- Oil temperature trending up: 85°C → 92°C (last 14 days)
- Dissolved hydrogen (H2): 320 ppm (normal < 100 ppm)
- Load utilization: 87% (high sustained load)
- Days since last maintenance: 145 days

IMPACT IF FAILURE OCCURS:
- Customers affected: 12,500
- Estimated outage duration: 4.2 hours
- SAIDI impact: 0.0060 points
- Estimated repair cost: $450,000

RECOMMENDED ACTION:
⚠️ IMMEDIATE inspection and maintenance required within 7 days
- Schedule oil sampling and dissolved gas analysis
- Prepare backup transformer
- Plan load transfer to T-SS047-002
- Estimated preventive maintenance cost: $45,000

This is your highest priority asset for this week."

=============================================================================
SAMPLE CONVERSATION 3: REGIONAL ANALYSIS
=============================================================================

User: "Which counties have the most high-risk assets?"

Agent: "High-Risk Assets by County:

1. MIAMI-DADE COUNTY
   - High-risk assets: 4
   - Average risk score: 76.3
   - Total customers at risk: 47,500
   - Potential SAIDI impact: 0.018 points

2. PALM BEACH COUNTY
   - High-risk assets: 3
   - Average risk score: 81.5
   - Total customers at risk: 31,000
   - Potential SAIDI impact: 0.012 points

3. HILLSBOROUGH COUNTY (Tampa)
   - High-risk assets: 2
   - Average risk score: 74.0
   - Total customers at risk: 23,000
   - Potential SAIDI impact: 0.009 points

4. ORANGE COUNTY (Orlando)
   - High-risk assets: 2
   - Average risk score: 72.5
   - Total customers at risk: 20,000
   - Potential SAIDI impact: 0.007 points

5. BROWARD COUNTY
   - High-risk assets: 1
   - Average risk score: 73.0
   - Total customers at risk: 11,000
   - Potential SAIDI impact: 0.004 points

RECOMMENDATION: 
Focus immediate resources on Palm Beach County (highest average risk) 
and Miami-Dade County (most high-risk assets and customer exposure)."

=============================================================================
*/

-- =============================================================================
-- SECTION 6: REGISTER AGENT WITH SNOWFLAKE INTELLIGENCE UI
-- =============================================================================

-- Create Snowflake Intelligence object (curated list of agents for Intelligence UI)
-- Note: This is a SHARED account-level object - may already exist from other projects
-- If the object already exists (e.g., from LOAD_FORECASTING or other projects), this is safe
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
    COMMENT = 'Curates which agents appear in the Snowflake Intelligence UI across all projects';

-- Register this agent to appear in Intelligence UI
-- This makes the agent visible in: Projects → Intelligence (not just Agents page)
-- Note: ADD AGENT does not support IF NOT EXISTS clause
ALTER SNOWFLAKE INTELLIGENCE IF EXISTS 
    IDENTIFIER('SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT') 
    ADD AGENT IDENTIFIER('UTILITIES_GRID_RELIABILITY.ANALYTICS."Grid Reliability Intelligence Agent"');

-- Grant usage to relevant roles so they can see the agent in Intelligence UI
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
    TO ROLE GRID_OPERATOR;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
    TO ROLE GRID_ANALYST;
GRANT USAGE ON SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT 
    TO ROLE GRID_ML_ENGINEER;

SELECT 'Intelligence Agent registered successfully - will appear in Intelligence UI' AS STATUS;

-- =============================================================================
-- Intelligence Agent Deployment Complete
-- Access: Snowflake UI > Projects > Intelligence (registered to Intelligence object)
-- Agent: Grid Reliability Intelligence Agent
-- =============================================================================


