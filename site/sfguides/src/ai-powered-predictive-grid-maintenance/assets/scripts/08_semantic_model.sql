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
 * Semantic Model Setup
 * 
 * Purpose: Create semantic view and upload semantic model for Cortex Analyst
 * Prerequisites: All ANALYTICS views must be created
 * 
 * Author: Grid Reliability AI/ML Team
 * Date: 2025-11-15
 * Version: 1.0
 ******************************************************************************/

USE DATABASE UTILITIES_GRID_RELIABILITY;
USE WAREHOUSE GRID_RELIABILITY_WH;
USE SCHEMA ANALYTICS;

-- =============================================================================
-- SECTION 1: CREATE SEMANTIC VIEW
-- =============================================================================

-- Following the user's preferred syntax for semantic views
CREATE OR REPLACE SEMANTIC VIEW GRID_RELIABILITY_ANALYTICS
TABLES (
  ASSET_HEALTH AS UTILITIES_GRID_RELIABILITY.ANALYTICS.VW_ASSET_HEALTH_DASHBOARD 
    PRIMARY KEY (ASSET_ID),
  ASSET_MASTER AS UTILITIES_GRID_RELIABILITY.RAW.ASSET_MASTER 
    PRIMARY KEY (ASSET_ID)
)
RELATIONSHIPS (
  HEALTH_TO_MASTER AS ASSET_HEALTH(ASSET_ID) REFERENCES ASSET_MASTER(ASSET_ID)
)
FACTS (
  PUBLIC ASSET_HEALTH.RISK_SCORE AS risk_score,
  PUBLIC ASSET_HEALTH.FAILURE_PROBABILITY AS failure_probability,
  PUBLIC ASSET_HEALTH.PREDICTED_RUL_DAYS AS predicted_rul_days
)
DIMENSIONS (
  PUBLIC ASSET_HEALTH.ASSET_ID AS asset_id,
  PUBLIC ASSET_HEALTH.ASSET_TYPE AS asset_type,
  PUBLIC ASSET_HEALTH.LOCATION_SUBSTATION AS location_substation,
  PUBLIC ASSET_HEALTH.LOCATION_CITY AS location_city,
  PUBLIC ASSET_HEALTH.LOCATION_COUNTY AS location_county,
  PUBLIC ASSET_HEALTH.RISK_CATEGORY AS risk_category,
  PUBLIC ASSET_HEALTH.ALERT_LEVEL AS alert_level,
  PUBLIC ASSET_HEALTH.CUSTOMERS_AFFECTED AS customers_affected,
  PUBLIC ASSET_HEALTH.CRITICALITY_SCORE AS criticality_score,
  PUBLIC ASSET_MASTER.MANUFACTURER AS manufacturer,
  PUBLIC ASSET_MASTER.MODEL AS model,
  PUBLIC ASSET_MASTER.INSTALL_DATE AS install_date
)
METRICS (
  PUBLIC ASSET_HEALTH.TOTAL_ASSETS AS COUNT(DISTINCT asset_health.asset_id),
  PUBLIC ASSET_HEALTH.AVG_RISK_SCORE AS AVG(risk_score),
  PUBLIC ASSET_HEALTH.MAX_RISK_SCORE AS MAX(risk_score),
  PUBLIC ASSET_HEALTH.HIGH_RISK_COUNT AS COUNT_IF(risk_score >= 70),
  PUBLIC ASSET_HEALTH.CRITICAL_COUNT AS COUNT_IF(risk_score >= 85),
  PUBLIC ASSET_HEALTH.TOTAL_CUSTOMERS_AT_RISK AS SUM(customers_affected)
);

-- =============================================================================
-- SECTION 2: UPLOAD SEMANTIC MODEL YAML
-- =============================================================================

-- First, upload the YAML file to the stage
/*
Instructions:
1. Upload the semantic model YAML file:
   
   PUT file:///path/to/grid_reliability_semantic.yaml @ANALYTICS.SEMANTIC_MODEL_STAGE 
   AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

2. Verify the upload:
   
   LIST @ANALYTICS.SEMANTIC_MODEL_STAGE;

3. The semantic model will be available at:
   @ANALYTICS.SEMANTIC_MODEL_STAGE/grid_reliability_semantic.yaml
*/

-- =============================================================================
-- SECTION 3: VERIFY SEMANTIC VIEW
-- =============================================================================

-- Semantic view created successfully!
-- Note: Semantic views are typically queried through:
-- 1. Cortex Analyst (natural language queries)
-- 2. Intelligence Agents
-- 3. Specific query patterns using the view name

-- Example query pattern (commented out - use after data is loaded):
-- SELECT 
--     ASSET_ID,
--     LOCATION_SUBSTATION,
--     RISK_SCORE
-- FROM VW_ASSET_HEALTH_DASHBOARD
-- WHERE RISK_SCORE >= 71;

SELECT 'Semantic view GRID_RELIABILITY_ANALYTICS created successfully!' as STATUS;

-- =============================================================================
-- SECTION 4: GRANT PERMISSIONS
-- =============================================================================

-- Grant permissions on semantic view
-- Note: Semantic views inherit permissions from underlying tables/views
-- Additional grants can be done using SELECT privilege
USE ROLE ACCOUNTADMIN;

GRANT SELECT ON VIEW ANALYTICS.GRID_RELIABILITY_ANALYTICS TO ROLE GRID_ANALYST;
GRANT SELECT ON VIEW ANALYTICS.GRID_RELIABILITY_ANALYTICS TO ROLE GRID_OPERATOR;
GRANT SELECT ON VIEW ANALYTICS.GRID_RELIABILITY_ANALYTICS TO ROLE GRID_ML_ENGINEER;

-- Grant read access to semantic model stage
GRANT READ ON STAGE ANALYTICS.SEMANTIC_MODEL_STAGE TO ROLE GRID_ANALYST;
GRANT READ ON STAGE ANALYTICS.SEMANTIC_MODEL_STAGE TO ROLE GRID_OPERATOR;

-- =============================================================================
-- SECTION 5: CREATE CORTEX ANALYST FUNCTION (OPTIONAL)
-- =============================================================================

-- This function can be used to query the semantic model using natural language
CREATE OR REPLACE FUNCTION ANALYTICS.ASK_GRID_ANALYST(QUESTION VARCHAR)
RETURNS TABLE (RESPONSE VARCHAR)
LANGUAGE SQL
AS
$$
    -- This is a placeholder for Cortex Analyst integration
    -- Will be replaced with actual CORTEX_ANALYST() function when available
    SELECT 'Cortex Analyst integration pending. Use Snowflake Intelligence Agent instead.' as RESPONSE
$$;

-- =============================================================================
-- SECTION 6: VERIFICATION AND DOCUMENTATION
-- =============================================================================

-- Show semantic view structure
DESCRIBE SEMANTIC VIEW GRID_RELIABILITY_ANALYTICS;

-- Note: SHOW TABLES IN SEMANTIC VIEW is not a valid Snowflake command
-- The structure is visible in the DESCRIBE output above

-- Documentation for users
SELECT 
    'Semantic View Created Successfully' as STATUS,
    'GRID_RELIABILITY_ANALYTICS' as VIEW_NAME,
    'Use Snowflake Intelligence Agent for natural language queries' as USAGE,
    '@ANALYTICS.SEMANTIC_MODEL_STAGE/grid_reliability_semantic.yaml' as SEMANTIC_MODEL_PATH;

-- =============================================================================
-- SAMPLE NATURAL LANGUAGE QUERIES
-- =============================================================================

/*
Once the Intelligence Agent is configured, users can ask questions like:

1. "Which substations have the highest risk?"
2. "How many critical assets are there in Miami-Dade county?"
3. "What is the total SAIDI impact if all high-risk assets fail?"
4. "Show me assets that need maintenance in the next 7 days"
5. "What is the average failure probability by county?"
6. "How much money are we saving with predictive maintenance?"
7. "List all transformers with risk score above 80"
8. "Which 5 assets affect the most customers?"
9. "Show me the trend of risk scores over the last month"
10. "What is the predicted remaining life of transformer T-SS047-001?"
*/

-- =============================================================================
-- SCRIPT COMPLETE
-- =============================================================================

SELECT 'Semantic view creation complete!' as STATUS;
SELECT 'View: ANALYTICS.GRID_RELIABILITY_ANALYTICS' as SEMANTIC_VIEW;
SELECT 'Upload YAML file: PUT file:///.../grid_reliability_semantic.yaml @ANALYTICS.SEMANTIC_MODEL_STAGE' as NEXT_STEP;
SELECT 'Then run: agents/create_grid_intelligence_agent.sql' as FINAL_STEP;


