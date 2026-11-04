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
-- Northbank agent evals quickstart | 06 Run and compare evaluations
-- Each START invokes the agent once per question, then scores every trace.
-- Runs take several minutes; check STATUS, or watch the agent's Evaluations tab in
-- Snowsight (AI & ML > Agents > LENDING_OPS_AGENT > Evaluations).
-- Cost at list price: the probe run is about $1; each full run is about $10-12
-- (see 08_cost.sql). Start with the probe.
-- Run statement by statement, NOT Run All: Run All would start every run at once.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;   -- runs execute in the session schema
USE WAREHOUSE NORTHBANK_EVAL_WH;

-- -----------------------------------------------------------------------------
-- Step 1: probe run (5 questions, system metrics only)
-- -----------------------------------------------------------------------------
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'probe_v1_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/probe_version1.yaml');

CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', 'probe_v1_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/probe_version1.yaml');

-- -----------------------------------------------------------------------------
-- Step 2: one full run per agent version (each pinned to a committed VERSION$N)
-- Runs can execute in parallel. Run names must be unique per agent.
-- -----------------------------------------------------------------------------
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'v1_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version1.yaml');
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'v2_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version2.yaml');
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'v3_r1'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version3.yaml');

-- Step 3 (variance): repeat the final version twice more before setting gate floors.
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'v3_r2'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version3.yaml');
CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'v3_r3'),
  '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version3.yaml');

-- Optional: same custom metrics scored by two judge models
-- CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'judges_r1'),
--   '@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/judge_comparison.yaml');

-- -----------------------------------------------------------------------------
-- Results. Set the run to inspect, then run the queries below.
-- -----------------------------------------------------------------------------
SET RUN = 'probe_v1_r1';

-- Average score per metric. Rows the judge could not score count as missing here,
-- but the Snowsight averages count them as 0, so check SCORED = N_ROWS.
SELECT METRIC_NAME,
       COUNT(*) AS N_ROWS,
       COUNT(EVAL_AGG_SCORE) AS SCORED,
       ROUND(AVG(EVAL_AGG_SCORE), 3) AS AVG_SCORE
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
       'NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', $RUN))
GROUP BY 1 ORDER BY 1;

-- Right answer, wrong path: correct answers whose tool selection was not perfect
SELECT q.QUESTION_ID, q.TIER, q.INPUT_QUERY,
       MAX(IFF(d.METRIC_NAME = 'answer_correctness', d.EVAL_AGG_SCORE, NULL)) AS AC,
       MAX(IFF(d.METRIC_NAME = 'tool_selection_accuracy', d.EVAL_AGG_SCORE, NULL)) AS TSA,
       MAX(IFF(d.METRIC_NAME = 'tool_execution_accuracy', d.EVAL_AGG_SCORE, NULL)) AS TEA
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
       'NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', $RUN)) d
JOIN EVAL_QUESTIONS q ON q.INPUT_QUERY = d.INPUT
GROUP BY 1, 2, 3
HAVING AC >= 0.99 AND TSA < 1
ORDER BY 1;

-- Judge reasoning for the low scores
SELECT d.METRIC_NAME, d.EVAL_AGG_SCORE, d.INPUT,
       d.METRIC_CALLS[0]:explanation::VARCHAR AS JUDGE_EXPLANATION
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
       'NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', $RUN)) d
WHERE d.EVAL_AGG_SCORE < 0.5
ORDER BY d.METRIC_NAME, d.EVAL_AGG_SCORE;

-- -----------------------------------------------------------------------------
-- Compare runs by tier: averages hide regressions in one tier
-- -----------------------------------------------------------------------------
SELECT q.TIER, d.RUN_NAME, d.METRIC_NAME, ROUND(AVG(d.EVAL_AGG_SCORE), 3) AS AVG_SCORE
FROM (
  SELECT 'v1_r1' AS RUN_NAME, * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v1_r1'))
  UNION ALL
  SELECT 'v2_r1', * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v2_r1'))
  UNION ALL
  SELECT 'v3_r1', * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r1'))
) d
JOIN EVAL_QUESTIONS q ON q.INPUT_QUERY = d.INPUT
WHERE d.METRIC_NAME IN ('answer_correctness', 'tool_selection_accuracy')
GROUP BY 1, 2, 3
ORDER BY 1, 3, 2;

-- -----------------------------------------------------------------------------
-- Variance: which questions change tool path between identical runs?
-- TSA has no judge, so any change means the agent called different tools.
-- -----------------------------------------------------------------------------
WITH r AS (
  SELECT 'v3_r1' AS RUN_NAME, INPUT, METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r1'))
  UNION ALL
  SELECT 'v3_r2', INPUT, METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r2'))
  UNION ALL
  SELECT 'v3_r3', INPUT, METRIC_NAME, EVAL_AGG_SCORE FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', 'v3_r3'))
)
SELECT q.QUESTION_ID, q.TIER, r.METRIC_NAME,
       ARRAY_AGG(ROUND(r.EVAL_AGG_SCORE, 2)) WITHIN GROUP (ORDER BY r.RUN_NAME) AS SCORES_R1_R2_R3
FROM r JOIN EVAL_QUESTIONS q ON q.INPUT_QUERY = r.INPUT
WHERE r.METRIC_NAME = 'tool_selection_accuracy'
GROUP BY 1, 2, 3
HAVING MIN(r.EVAL_AGG_SCORE) <> MAX(r.EVAL_AGG_SCORE)
ORDER BY 1;

-- Warnings and errors logged during a run (for example a judge hitting its context limit)
SELECT TIMESTAMP, RECORD:"severity_text"::VARCHAR AS SEVERITY, VALUE::VARCHAR AS MESSAGE
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_OBSERVABILITY_LOGS(
       'NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT'))
WHERE RECORD:"severity_text" IN ('ERROR', 'WARN')
  AND RECORD_ATTRIBUTES:"snow.ai.observability.run.name" = $RUN
ORDER BY TIMESTAMP;
