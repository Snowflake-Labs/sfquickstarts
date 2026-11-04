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
-- Northbank agent evals quickstart | 02 Policy documents and Cortex Search
-- Parses the 7 synthetic policy PDFs with AI_PARSE_DOCUMENT, chunks them by heading
-- with version/status metadata, and creates two Cortex Search services.
-- PREREQUISITE: the PDFs are in @DEMO.POLICY_STAGE (uploaded after running 00_setup.sql).
-- Run in a Snowsight SQL worksheet (Run All), in numeric order.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE WAREHOUSE NORTHBANK_EVAL_WH;

ALTER STAGE DEMO.POLICY_STAGE REFRESH;
SELECT RELATIVE_PATH, SIZE FROM DIRECTORY(@DEMO.POLICY_STAGE);  -- expect 7 PDFs

-- Parse policy PDFs with AI_PARSE_DOCUMENT LAYOUT, one row per page
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.POLICY_PAGES AS
WITH parsed AS (
  SELECT RELATIVE_PATH, MD5,
    AI_PARSE_DOCUMENT(TO_FILE('@NORTHBANK_AGENT_EVALS.DEMO.POLICY_STAGE', RELATIVE_PATH),
                      {'mode': 'LAYOUT', 'page_split': TRUE}) AS doc
  FROM DIRECTORY(@NORTHBANK_AGENT_EVALS.DEMO.POLICY_STAGE)
)
SELECT RELATIVE_PATH, MD5, 'LAYOUT' AS PARSER_MODE,
  p.value:index::INT + 1 AS PAGE_NUMBER,
  p.value:content::VARCHAR AS CONTENT
FROM parsed, LATERAL FLATTEN(input => doc:pages) p;

-- Build header-aware policy chunks with version/status metadata
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.POLICY_CHUNKS AS
WITH docs AS (
  SELECT RELATIVE_PATH,
    REGEXP_REPLACE(LISTAGG(CONTENT, '\n') WITHIN GROUP (ORDER BY PAGE_NUMBER),
                   'Northbank plc - Internal - [^\n]*?Page [0-9]+', '') AS FULL_TEXT
  FROM NORTHBANK_AGENT_EVALS.DEMO.POLICY_PAGES GROUP BY 1
),
meta AS (
  SELECT d.*, m.*
  FROM docs d JOIN (
    SELECT column1 AS FILE, column2 AS DOC_TITLE, column3 AS DOC_VERSION, column4::DATE AS EFFECTIVE_DATE, column5 AS DOC_STATUS FROM VALUES
    ('credit_policy_v1_0.pdf','Northbank Credit Policy','v1.0','2024-07-01','SUPERSEDED'),
    ('credit_policy_v2_0.pdf','Northbank Credit Policy','v2.0','2026-03-01','CURRENT'),
    ('affordability_standard.pdf','Northbank Affordability Standard','3.1','2024-07-01','CURRENT'),
    ('forbearance_and_arrears_procedure.pdf','Northbank Forbearance and Arrears Procedure','2.2','2025-01-01','CURRENT'),
    ('vulnerable_customer_procedure.pdf','Northbank Vulnerable Customer Procedure','1.4','2024-07-01','CURRENT'),
    ('consumer_duty_summary.pdf','Northbank Consumer Duty Summary for Colleagues','1.2','2023-07-31','CURRENT'),
    ('complaints_handling.pdf','Northbank Complaints Handling Procedure','2.0','2025-01-01','CURRENT')
  ) m ON m.FILE = d.RELATIVE_PATH
),
split AS (
  SELECT meta.*, c.index AS CHUNK_INDEX, c.value AS ch
  FROM meta, LATERAL FLATTEN(input => SNOWFLAKE.CORTEX.SPLIT_TEXT_MARKDOWN_HEADER(
      FULL_TEXT, OBJECT_CONSTRUCT('#', 'h1', '##', 'h2'), 1500, 150)) c
)
SELECT
  RELATIVE_PATH || '#' || CHUNK_INDEX AS CHUNK_ID,
  RELATIVE_PATH AS SOURCE_FILE, DOC_TITLE, DOC_VERSION, EFFECTIVE_DATE, DOC_STATUS,
  COALESCE(ch:headers:h2::VARCHAR, ch:headers:h1::VARCHAR) AS SECTION,
  DOC_TITLE || ' ' || DOC_VERSION || ' (' || DOC_STATUS || ', effective ' || TO_VARCHAR(EFFECTIVE_DATE, 'DD Mon YYYY') || ')'
    || IFF(COALESCE(ch:headers:h2::VARCHAR, ch:headers:h1::VARCHAR) IS NULL, '', ' - ' || COALESCE(ch:headers:h2::VARCHAR, ch:headers:h1::VARCHAR))
    || '\n' || ch:chunk::VARCHAR AS CHUNK_TEXT
FROM split
WHERE LENGTH(REGEXP_REPLACE(ch:chunk::VARCHAR, '[[:space:]]', '')) > 0;

-- Create CREDIT_POLICY_SEARCH Cortex Search service
CREATE OR REPLACE CORTEX SEARCH SERVICE NORTHBANK_AGENT_EVALS.DEMO.CREDIT_POLICY_SEARCH
  ON CHUNK_TEXT
  ATTRIBUTES DOC_TITLE, DOC_VERSION, DOC_STATUS, SECTION
  WAREHOUSE = NORTHBANK_EVAL_WH
  TARGET_LAG = '1 day'
  COMMENT = 'Northbank policy documents (synthetic), chunked by section'
  AS SELECT CHUNK_ID, SOURCE_FILE, DOC_TITLE, DOC_VERSION, EFFECTIVE_DATE, DOC_STATUS, SECTION, CHUNK_TEXT
     FROM NORTHBANK_AGENT_EVALS.DEMO.POLICY_CHUNKS;

-- Create CUSTOMER_NOTES_SEARCH filterable by CUSTOMER_ID
CREATE OR REPLACE CORTEX SEARCH SERVICE NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES_SEARCH
  ON NOTE_TEXT
  ATTRIBUTES CUSTOMER_ID, CHANNEL, NOTE_DATE
  WAREHOUSE = NORTHBANK_EVAL_WH
  TARGET_LAG = '1 day'
  COMMENT = 'Northbank customer contact and hardship notes (synthetic)'
  AS SELECT NOTE_ID, CUSTOMER_ID, NOTE_DATE, CHANNEL, COLLEAGUE, NOTE_TEXT FROM NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES;