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
-- Northbank agent evals quickstart | 00 Setup
-- Creates the warehouse, database, schemas and stages. Run All, upload the project
-- files into the stages (see the end of this script), re-run the last four
-- statements to check them, then run 01 to 08 in order.
-- =============================================================================

-- Role: use a role that can create a warehouse and a database. ACCOUNTADMIN is
-- simplest for a sandbox account. For the minimum privileges to run evaluations,
-- see README "Privileges".
USE ROLE ACCOUNTADMIN;

-- Cortex Agents and the evaluation judges need models that may not run in your
-- region. Cross-region inference makes them available (and uses the lower global
-- AI Credit price). Skip this if your account already allows it.
-- ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;

-- An X-Small warehouse is enough: it runs the agent's SQL, the custom tool and the
-- evaluation tasks. Agent and judge inference is serverless and billed separately.
CREATE WAREHOUSE IF NOT EXISTS NORTHBANK_EVAL_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Northbank agent evals quickstart';
USE WAREHOUSE NORTHBANK_EVAL_WH;

CREATE DATABASE IF NOT EXISTS NORTHBANK_AGENT_EVALS
  COMMENT = 'Northbank agent evals quickstart: fictional UK lender, synthetic data only';
CREATE SCHEMA IF NOT EXISTS NORTHBANK_AGENT_EVALS.DEMO
  COMMENT = 'Everything the agent can see: data, documents, tools, agent, evaluation objects';
CREATE SCHEMA IF NOT EXISTS NORTHBANK_AGENT_EVALS.GROUND_TRUTH
  COMMENT = 'Evaluation-only labels. Never exposed to agent tools.';
USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;

-- Stages (server-side encryption is required for AI_PARSE_DOCUMENT)
CREATE STAGE IF NOT EXISTS POLICY_STAGE
  DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Synthetic Northbank policy PDFs';
CREATE STAGE IF NOT EXISTS EVAL_DATA_STAGE ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Evaluation questions with ground truth (NDJSON)';
CREATE STAGE IF NOT EXISTS EVAL_CONFIG_STAGE ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Agent evaluation YAML configs read by EXECUTE_AI_EVALUATION';
CREATE FILE FORMAT IF NOT EXISTS JSON_FF TYPE = 'JSON';

-- -----------------------------------------------------------------------------
-- Next: upload the project files into the three stages, then run the checks below.
-- In Snowsight go to Ingestion > Add Data > Load files into a stage, and upload:
--   data/policy_pdfs/*.pdf      -> NORTHBANK_AGENT_EVALS.DEMO.POLICY_STAGE
--   data/eval_questions.ndjson  -> NORTHBANK_AGENT_EVALS.DEMO.EVAL_DATA_STAGE
--   eval_configs/*.yaml         -> NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE
-- Or with the Snowflake CLI from the project folder:
--   snow stage copy data/policy_pdfs/ @NORTHBANK_AGENT_EVALS.DEMO.POLICY_STAGE
--   snow stage copy data/eval_questions.ndjson @NORTHBANK_AGENT_EVALS.DEMO.EVAL_DATA_STAGE
--   snow stage copy eval_configs/ @NORTHBANK_AGENT_EVALS.DEMO.EVAL_CONFIG_STAGE
-- Upload the files into the root of each stage, without a sub-path.
-- -----------------------------------------------------------------------------

-- Run these after uploading:
ALTER STAGE POLICY_STAGE REFRESH;
LIST @POLICY_STAGE;       -- expect 7 PDFs
LIST @EVAL_DATA_STAGE;    -- expect eval_questions.ndjson
LIST @EVAL_CONFIG_STAGE;  -- expect 5 evaluation YAML files
