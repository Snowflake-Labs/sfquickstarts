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
-- Northbank agent evals quickstart | 08 What a run costs
-- ACCOUNT_USAGE views can lag by up to about 45 minutes after a run finishes.
-- Prices: Snowflake Service Consumption Table (check the current version).
--   AI Credits (agents, judges): $2.00 with global cross-region routing, $2.20 regional,
--     in every edition and region.
--   Platform Credits (warehouse): depend on edition and region,
--     e.g. Enterprise on AWS EU Dublin $3.90 on demand.
--   Judge model rate (AI Credits per million tokens): look up the model the metric
--     version uses in the Cortex Inference table. Below: v3 judge, 1.50 input / 7.50 output.
-- These are list prices; capacity contracts and AI Credit discounts lower them.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE WAREHOUSE NORTHBANK_EVAL_WH;

SET RUN = 'v3_r1';
SET AI_CREDIT_USD = 2.00;
SET PLATFORM_CREDIT_USD = 3.90;
SET JUDGE_IN_PER_M = 1.50;
SET JUDGE_OUT_PER_M = 7.50;

-- Judge tokens and cost per metric. Each evaluation span records the inference
-- request IDs it made; CORTEX_REST_API_USAGE_HISTORY has the tokens (no credits).
WITH eval_requests AS (
  SELECT record_attributes:"ai.observability.eval.metric_name"::VARCHAR AS METRIC_NAME,
         ids.value::VARCHAR AS REQUEST_ID
  FROM SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS,
    LATERAL FLATTEN(input => STRTOK_TO_ARRAY(
      PARSE_JSON(record_attributes:"ai.observability.eval.full_metadata"::VARCHAR)
        :"ai.observability.eval.inference_request_ids"::VARCHAR, ',')) AS ids
  WHERE record_attributes:"ai.observability.span_type"::VARCHAR = 'eval'
    AND record_attributes:"snow.ai.observability.run.name"::VARCHAR = $RUN
)
SELECT e.METRIC_NAME,
       u.MODEL_NAME AS JUDGE_MODEL,
       SUM(u.TOKENS_GRANULAR:input::NUMBER) AS INPUT_TOKENS,
       SUM(u.TOKENS_GRANULAR:output::NUMBER) AS OUTPUT_TOKENS,
       ROUND(SUM(u.TOKENS_GRANULAR:input::NUMBER) / 1e6 * $JUDGE_IN_PER_M
           + SUM(u.TOKENS_GRANULAR:output::NUMBER) / 1e6 * $JUDGE_OUT_PER_M, 3) AS AI_CREDITS,
       ROUND(AI_CREDITS * $AI_CREDIT_USD, 2) AS USD
FROM eval_requests e
JOIN SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY u ON u.REQUEST_ID = e.REQUEST_ID
GROUP BY 1, 2
ORDER BY USD DESC;
-- tool_selection_accuracy does not appear: it uses no judge.

-- Agent invocation cost: one agent request per question, billed in AI Credits.
WITH reqs AS (
  SELECT DISTINCT REQUEST_ID
  FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
         'NORTHBANK_AGENT_EVALS', 'DEMO', 'LENDING_OPS_AGENT', 'CORTEX AGENT', $RUN))
)
SELECT COUNT(*) AS AGENT_REQUESTS,
       ROUND(SUM(u.TOKEN_CREDITS), 3) AS AI_CREDITS,
       ROUND(SUM(u.TOKEN_CREDITS) * $AI_CREDIT_USD, 2) AS USD
FROM reqs r
JOIN SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY u ON u.REQUEST_ID = r.REQUEST_ID;

-- Warehouse cost of the evaluation's own tasks (metric computation and status
-- updates run as SYSTEM). Approximate: polling tasks are shared when runs overlap.
SELECT COUNT(*) AS QUERIES,
       ROUND(SUM(a.CREDITS_ATTRIBUTED_COMPUTE), 4) AS PLATFORM_CREDITS,
       ROUND(SUM(a.CREDITS_ATTRIBUTED_COMPUTE) * $PLATFORM_CREDIT_USD, 2) AS USD
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY a
JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q ON q.QUERY_ID = a.QUERY_ID
WHERE q.USER_NAME = 'SYSTEM'
  AND q.QUERY_TEXT ILIKE '%EXECUTE_AI_OBSERVABILITY_TASK%'
  AND q.QUERY_TEXT ILIKE '%''' || $RUN || '''%'
  AND q.START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP());
