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
-- Template: an evaluation dataset for YOUR agent
-- Copy, replace the <placeholders>, keep one INSERT per question.
-- Guidance: docs/adapt-to-your-use-case.md
-- =============================================================================
USE SCHEMA <DB>.<SCHEMA>;   -- datasets are created in the session schema

CREATE OR REPLACE TABLE <DB>.<SCHEMA>.MY_EVAL_QUESTIONS (
  QUESTION_ID  VARCHAR,
  TIER         VARCHAR,   -- your own grouping: core, cross_tool, refusal, policy_change...
  INPUT_QUERY  VARCHAR,
  GROUND_TRUTH VARIANT
);

-- 1. A known answer from structured data. Compute the expected value in SQL first;
--    never take it from the agent. Say which wrong answer you want rejected.
INSERT INTO MY_EVAL_QUESTIONS
SELECT 'Q01', 'core',
  'How many <entities> did we <event> between 1 April and 30 June 2026?',
  PARSE_JSON($$
  {
    "ground_truth_output": "<exact value>. <What a wrong-but-plausible answer looks like, and why it is wrong.>",
    "ground_truth_invocations": [
      {
        "tool_name": "<cortex analyst tool name>",
        "tool_input": "<what the agent should ask the tool, in plain words>",
        "tool_output": "SQL:\n<the SQL you used to compute the answer>\n\nExpected Result:\n<value>"
      }
    ]
  }
  $$);

-- 2. A question that needs two tools. List every tool you expect; order is ignored.
INSERT INTO MY_EVAL_QUESTIONS
SELECT 'Q02', 'cross_tool',
  '<question that needs both data and a document>',
  PARSE_JSON($$
  {
    "ground_truth_output": "<facts the answer must contain, with values and the document version>",
    "ground_truth_invocations": [
      {"tool_name": "<analyst tool>", "tool_input": "<...>", "tool_output": "<expected SQL / result>"},
      {"tool_name": "<search tool>",  "tool_input": "<...>", "tool_output": "<document and section that should come back>"}
    ]
  }
  $$);

-- 3. Out of scope or a refusal. [] means calling ANY tool is wrong (scored by TSA).
INSERT INTO MY_EVAL_QUESTIONS
SELECT 'Q03', 'refusal',
  '<question the agent must decline>',
  PARSE_JSON($$
  {
    "ground_truth_output": "The response should decline because <reason> and should not <fabricate / give advice / use a protected characteristic>.",
    "ground_truth_invocations": []
  }
  $$);

-- Check before registering: every row needs ground_truth_invocations, or it silently
-- drops out of tool selection and tool execution accuracy.
SELECT QUESTION_ID FROM MY_EVAL_QUESTIONS
WHERE GROUND_TRUTH:ground_truth_invocations IS NULL;   -- expect no rows

CALL SYSTEM$CREATE_EVALUATION_DATASET(
  'Cortex Agent',
  '<DB>.<SCHEMA>.MY_EVAL_QUESTIONS',
  '<DB>.<SCHEMA>.MY_EVAL_V1',          -- version the dataset name; never reuse it
  OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH'));
