-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =============================================================================
-- Northbank agent evals quickstart | 07b Gate your runs
-- Needs the runs started in 06_run_evaluations.sql (v2_r1, v3_r1, v3_r2, v3_r3) to have
-- COMPLETED. Run statement by statement, not Run All.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
USE WAREHOUSE NORTHBANK_EVAL_WH;

-- -----------------------------------------------------------------------------
-- Set floors from measured variance, not from a single run.
-- Run the final version three times (06_run_evaluations.sql, step 3), then derive
-- floor = lowest run minus one run-to-run range, rounded down.
-- -----------------------------------------------------------------------------
WITH runs AS (
  SELECT 'v3_r1' AS RUN_NAME, METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r1'))
  UNION ALL
  SELECT 'v3_r2', METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r2'))
  UNION ALL
  SELECT 'v3_r3', METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r3'))
),
per_run AS (SELECT METRIC_NAME, RUN_NAME, AVG(EVAL_AGG_SCORE) AS AVG_SCORE FROM runs GROUP BY 1, 2)
SELECT METRIC_NAME,
       ROUND(MIN(AVG_SCORE), 3) AS LOWEST_RUN,
       ROUND(MAX(AVG_SCORE) - MIN(AVG_SCORE), 3) AS RANGE,
       FLOOR((2 * MIN(AVG_SCORE) - MAX(AVG_SCORE)) * 200) / 200 AS SUGGESTED_FLOOR
FROM per_run GROUP BY 1 ORDER BY 1;

-- Write your own floors (example: copy SUGGESTED_FLOOR values from the query above)
-- UPDATE EVAL_GATE_THRESHOLDS SET MIN_VALUE = <value> WHERE METRIC = 'answer_correctness';

-- Gate the runs you already have (VERSION$2 should fail, VERSION$3 should pass)
INSERT INTO EVAL_GATE_RESULTS (RUN_NAME, CONFIG_PATH, STARTED_AT, STATUS)
SELECT column1, '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/' || column2, CURRENT_TIMESTAMP(), 'BACKFILL'
FROM VALUES ('v2_r1', 'version2.yaml'), ('v3_r1', 'version3.yaml'), ('v3_r2', 'version3.yaml'), ('v3_r3', 'version3.yaml');

CALL CHECK_GATED_EVALS();   -- repeat until no run is still in progress

SELECT RUN_NAME, STATUS, AGENT_VERSION, ROUND(ANSWER_CORRECTNESS, 3) AS AC, ROUND(TOOL_SELECTION, 3) AS TSA,
       ROUND(TOOL_EXECUTION, 3) AS TEA, CONSUMER_DUTY_MIN, GATE_PASSED, GATE_REASONS
FROM EVAL_GATE_RESULTS ORDER BY STARTED_AT DESC;

-- Try the nightly task once without scheduling, then poll the gate until it records a result:
-- EXECUTE TASK NIGHTLY_AGENT_EVAL;
-- CALL CHECK_GATED_EVALS();
