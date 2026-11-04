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
-- Northbank agent evals quickstart | 99 Teardown
-- Removes everything the quickstart created. Evaluation runs and their results are
-- stored with the agent and are removed with it.
-- =============================================================================
USE ROLE ACCOUNTADMIN;

ALTER TASK IF EXISTS NORTHBANK_AGENT_EVALS.DEMO.NIGHTLY_AGENT_EVAL SUSPEND;
ALTER TASK IF EXISTS NORTHBANK_AGENT_EVALS.DEMO.CHECK_AGENT_EVAL_GATE SUSPEND;

DROP DATABASE IF EXISTS NORTHBANK_AGENT_EVALS;
DROP WAREHOUSE IF EXISTS NORTHBANK_EVAL_WH;
