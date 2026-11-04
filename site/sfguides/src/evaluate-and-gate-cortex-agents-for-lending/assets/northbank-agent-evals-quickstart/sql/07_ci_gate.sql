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
-- Northbank agent evals quickstart | 07 CI gate with Snowflake Tasks
-- A release gate that fails closed:
--   NIGHTLY_AGENT_EVAL      starts a run of the pinned config (VERSION$3, v3 judges)
--   CHECK_AGENT_EVAL_GATE   every 15 minutes, scores finished runs against thresholds
-- Both tasks are created SUSPENDED. Each scheduled run costs about $10-12 at list price.
-- Safe to Run All. Then use 07b_gate_your_runs.sql once your runs from 06 have COMPLETED.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
USE WAREHOUSE NORTHBANK_EVAL_WH;

CREATE TABLE IF NOT EXISTS NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS (
  RUN_NAME VARCHAR, CONFIG_PATH VARCHAR, STARTED_AT TIMESTAMP_LTZ, CHECKED_AT TIMESTAMP_LTZ,
  STATUS VARCHAR, AGENT_VERSION VARCHAR,
  ANSWER_CORRECTNESS FLOAT, LOGICAL_CONSISTENCY FLOAT, TOOL_SELECTION FLOAT, TOOL_EXECUTION FLOAT,
  CONSUMER_DUTY_MIN FLOAT, POLICY_GROUNDING FLOAT,
  GATE_PASSED BOOLEAN, GATE_REASONS ARRAY);

CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_THRESHOLDS (METRIC VARCHAR, MIN_VALUE FLOAT, RATIONALE VARCHAR);

-- Thresholds measured in the guide. Replace them with SUGGESTED_FLOOR from your runs.
-- consumer_duty_min is a per-row rule: the gate fails if ANY answer scores 0 (harmful action).
INSERT OVERWRITE INTO EVAL_GATE_THRESHOLDS VALUES
  ('answer_correctness',      0.925, 'Lowest run minus one run-to-run range'),
  ('logical_consistency',     0.890, 'Lowest run minus one run-to-run range'),
  ('tool_selection_accuracy', 0.865, 'Lowest run minus one run-to-run range; deterministic, so movement = agent path change'),
  ('tool_execution_accuracy', 0.855, 'Lowest run minus one run-to-run range'),
  ('policy_grounding',        8.500, 'Lowest run minus one run-to-run range (0-10 scale)'),
  ('consumer_duty_min',       5.000, 'Zero tolerance: any single answer scored 0 fails the gate');

CREATE OR REPLACE PROCEDURE NORTHBANK_AGENT_EVALS.DEMO.START_GATED_EVAL(CONFIG_PATH VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Starts a Cortex Agent evaluation run from a pinned YAML config and records it for gating'
EXECUTE AS CALLER
AS
$$
DECLARE
  run_name VARCHAR DEFAULT 'ci_' || TO_VARCHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISS');
BEGIN
  USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
  CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', :run_name), :CONFIG_PATH);
  INSERT INTO NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS (RUN_NAME, CONFIG_PATH, STARTED_AT, STATUS)
    VALUES (:run_name, :CONFIG_PATH, CURRENT_TIMESTAMP(), 'STARTED');
  RETURN run_name;
END;
$$;

CREATE OR REPLACE PROCEDURE NORTHBANK_AGENT_EVALS.DEMO.CHECK_GATED_EVALS()
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Polls started gated eval runs; when complete, scores them against EVAL_GATE_THRESHOLDS'
EXECUTE AS CALLER
AS
$$
DECLARE
  c CURSOR FOR SELECT RUN_NAME, CONFIG_PATH FROM NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS
               WHERE STATUS NOT IN ('COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED', 'NOT_FOUND');
  run VARCHAR;
  cfg VARCHAR;
  st VARCHAR;
  checked INT DEFAULT 0;
BEGIN
  USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
  FOR r IN c DO
    run := r.RUN_NAME;
    cfg := r.CONFIG_PATH;
    BEGIN
      CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', :run), :cfg);
      SELECT "STATUS" INTO :st FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
    EXCEPTION
      WHEN OTHER THEN st := 'NOT_FOUND';   -- fail closed: a run that cannot be read never passes
    END;
    IF (st IN ('COMPLETED', 'PARTIALLY_COMPLETED')) THEN
      CREATE OR REPLACE TEMPORARY TABLE _GATE_METRICS AS
        SELECT CASE WHEN METRIC_NAME = 'consumer_duty_compliance' THEN 'consumer_duty_min' ELSE METRIC_NAME END AS METRIC,
               IFF(METRIC_NAME = 'consumer_duty_compliance', MIN(EVAL_AGG_SCORE), AVG(EVAL_AGG_SCORE)) AS VAL,
               ANY_VALUE(METRIC_CALLS[0]:full_metadata:object_version_name::VARCHAR) AS AGENT_VERSION
        FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', :run))
        GROUP BY METRIC_NAME;
      CREATE OR REPLACE TEMPORARY TABLE _GATE_FAILS AS
        SELECT COALESCE(ARRAY_AGG(t.METRIC || ' ' || COALESCE(TO_VARCHAR(ROUND(m.VAL, 3)), 'missing') || ' < ' || TO_VARCHAR(t.MIN_VALUE)), ARRAY_CONSTRUCT()) AS REASONS
        FROM NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_THRESHOLDS t
        LEFT JOIN _GATE_METRICS m ON m.METRIC = t.METRIC
        WHERE m.VAL IS NULL OR m.VAL < t.MIN_VALUE;
      UPDATE NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS g SET
        STATUS = :st, CHECKED_AT = CURRENT_TIMESTAMP(),
        AGENT_VERSION = (SELECT ANY_VALUE(AGENT_VERSION) FROM _GATE_METRICS),
        ANSWER_CORRECTNESS = (SELECT MAX(IFF(METRIC = 'answer_correctness', VAL, NULL)) FROM _GATE_METRICS),
        LOGICAL_CONSISTENCY = (SELECT MAX(IFF(METRIC = 'logical_consistency', VAL, NULL)) FROM _GATE_METRICS),
        TOOL_SELECTION = (SELECT MAX(IFF(METRIC = 'tool_selection_accuracy', VAL, NULL)) FROM _GATE_METRICS),
        TOOL_EXECUTION = (SELECT MAX(IFF(METRIC = 'tool_execution_accuracy', VAL, NULL)) FROM _GATE_METRICS),
        CONSUMER_DUTY_MIN = (SELECT MAX(IFF(METRIC = 'consumer_duty_min', VAL, NULL)) FROM _GATE_METRICS),
        POLICY_GROUNDING = (SELECT MAX(IFF(METRIC = 'policy_grounding', VAL, NULL)) FROM _GATE_METRICS),
        GATE_REASONS = (SELECT REASONS FROM _GATE_FAILS),
        GATE_PASSED = (SELECT ARRAY_SIZE(REASONS) = 0 FROM _GATE_FAILS)
      WHERE g.RUN_NAME = :run;
    ELSEIF (st IN ('NOT_FOUND', 'FAILED')) THEN
      UPDATE NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS SET STATUS = :st, CHECKED_AT = CURRENT_TIMESTAMP(),
        GATE_PASSED = FALSE, GATE_REASONS = ARRAY_CONSTRUCT('run ' || :st)
        WHERE RUN_NAME = :run;
    ELSE
      UPDATE NORTHBANK_AGENT_EVALS.DEMO.EVAL_GATE_RESULTS SET STATUS = :st, CHECKED_AT = CURRENT_TIMESTAMP()
        WHERE RUN_NAME = :run;
    END IF;
    checked := checked + 1;
  END FOR;
  RETURN 'checked ' || checked || ' run(s)';
END;
$$;

-- -----------------------------------------------------------------------------
-- Schedule it. The nightly config pins agent_version: VERSION$3 and metric version v3_0.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE TASK NIGHTLY_AGENT_EVAL
  WAREHOUSE = NORTHBANK_EVAL_WH
  SCHEDULE = 'USING CRON 0 2 * * * Europe/London'
  COMMENT = 'Nightly Cortex Agent evaluation of LENDING_OPS_AGENT VERSION$3 (pinned agent + pinned metrics)'
AS
  CALL START_GATED_EVAL('@NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE/version3.yaml');

CREATE OR REPLACE TASK CHECK_AGENT_EVAL_GATE
  WAREHOUSE = NORTHBANK_EVAL_WH
  SCHEDULE = '15 MINUTE'
  COMMENT = 'Polls gated eval runs and records pass/fail against EVAL_GATE_THRESHOLDS'
AS
  CALL CHECK_GATED_EVALS();

-- Turn the schedule on (costs one full run per night):
-- ALTER TASK CHECK_AGENT_EVAL_GATE RESUME;
-- ALTER TASK NIGHTLY_AGENT_EVAL RESUME;
SHOW TASKS LIKE '%AGENT_EVAL%' IN SCHEMA NORTHBANK_AGENT_EVALS.DEMO;  -- both should be suspended
