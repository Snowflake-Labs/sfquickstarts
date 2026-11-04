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
-- Northbank agent evals quickstart | 04 Custom tool and agent versions
-- Creates the affordability_check tool and the LENDING_OPS_AGENT agent with three
-- committed versions, changing ONE thing at a time:
--   VERSION$1  baseline: thin routing instructions          (orchestration model A)
--   VERSION$2  rich instructions targeting VERSION$1's failures (same model A)
--   VERSION$3  VERSION$2's instructions on a different model   (orchestration model B)
-- The specs are also in agent_specs/ for reading and diffing.
-- Model names: replace them with models available in your account and region
-- (see README "Choosing models"). Keep model A identical in VERSION$1 and VERSION$2.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
USE WAREHOUSE NORTHBANK_EVAL_WH;

-- Custom tool: Northbank Affordability Standard (debt-to-income, maximum 50%)
CREATE OR REPLACE PROCEDURE NORTHBANK_AGENT_EVALS.DEMO.AFFORDABILITY_CHECK(
    PRODUCT VARCHAR, ANNUAL_INCOME FLOAT, MONTHLY_COMMITMENTS FLOAT, AMOUNT FLOAT, TERM_MONTHS FLOAT)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Northbank Affordability Standard v3.1: DTI = (commitments + new payment) / (income/12); max 50%'
AS
$$
DECLARE
  new_payment FLOAT;
  dti FLOAT;
  result VARCHAR;
BEGIN
  IF (ANNUAL_INCOME IS NULL OR ANNUAL_INCOME <= 0) THEN
    RETURN 'RESULT: REFER - declared income is missing or zero, affordability cannot be assessed (decision REFERRED, reason INCOME_NOT_VERIFIED).';
  END IF;
  IF (UPPER(PRODUCT) = 'PERSONAL_LOAN') THEN
    IF (TERM_MONTHS IS NULL OR TERM_MONTHS <= 0) THEN
      RETURN 'RESULT: ERROR - personal loans require a term in months.';
    END IF;
    new_payment := AMOUNT * 1.08 / TERM_MONTHS;
  ELSEIF (UPPER(PRODUCT) = 'CREDIT_CARD') THEN
    new_payment := AMOUNT * 0.03;
  ELSE
    RETURN 'RESULT: ERROR - product must be PERSONAL_LOAN or CREDIT_CARD.';
  END IF;
  dti := (COALESCE(MONTHLY_COMMITMENTS, 0) + new_payment) / (ANNUAL_INCOME / 12);
  result := 'RESULT: ' || IFF(dti <= 0.50, 'PASS', 'FAIL') ||
            ' | estimated new monthly payment GBP ' || TO_VARCHAR(ROUND(new_payment, 2)) ||
            ' | debt-to-income ratio ' || TO_VARCHAR(ROUND(dti * 100, 1)) || '% (maximum 50%)';
  RETURN result;
END;
$$;

CALL AFFORDABILITY_CHECK('PERSONAL_LOAN', 42000, 650, 12000, 36);  -- expect PASS, DTI about 30%

-- VERSION$1: CREATE AGENT commits the first specification as VERSION$1 and keeps a LIVE copy.
CREATE OR REPLACE AGENT NORTHBANK_AGENT_EVALS.DEMO.LENDING_OPS_AGENT
  COMMENT = 'Northbank lending ops agent (synthetic data)'
  PROFILE = '{"display_name": "Northbank Lending Ops Agent"}'
  FROM SPECIFICATION
$$
models:
  orchestration: claude-sonnet-4-5

orchestration:
  budget:
    seconds: 300
    tokens: 32000

instructions:
  system: "You are the Northbank Lending Ops Agent, an assistant for Northbank credit operations and collections colleagues."
  response: "Be concise and factual. State the numbers you used."
  orchestration: "Use loan_book for questions about applications, decisions, loans, arrears and forbearance. Use credit_policy for Northbank policy and procedure questions. Use customer_notes for customer contact history. Use affordability_check to assess affordability."
  sample_questions:
    - question: "What was the approval rate in May 2026?"
    - question: "What is the minimum credit score for a personal loan?"

tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: loan_book
      description: "Northbank loan book: applications, credit decisions, booked loans and cards, arrears cases and forbearance arrangements (Jan 2025 to Jun 2026)."
  - tool_spec:
      type: cortex_search
      name: credit_policy
      description: "Northbank credit policy and procedure documents."
  - tool_spec:
      type: cortex_search
      name: customer_notes
      description: "Customer contact and hardship notes recorded by Northbank colleagues."
  - tool_spec:
      type: generic
      name: affordability_check
      description: "Calculates debt-to-income ratio and pass/fail for a proposed personal loan or credit card under the Northbank Affordability Standard."
      input_schema:
        type: object
        properties:
          PRODUCT:
            type: string
            description: "PERSONAL_LOAN or CREDIT_CARD"
          ANNUAL_INCOME:
            type: number
            description: "Gross annual income in GBP"
          MONTHLY_COMMITMENTS:
            type: number
            description: "Existing monthly credit commitments in GBP"
          AMOUNT:
            type: number
            description: "Loan amount or credit limit in GBP"
          TERM_MONTHS:
            type: number
            description: "Loan term in months (use 0 for credit cards)"
        required: [PRODUCT, ANNUAL_INCOME, MONTHLY_COMMITMENTS, AMOUNT, TERM_MONTHS]

tool_resources:
  loan_book:
    semantic_view: NORTHBANK_AGENT_EVALS.DEMO.SV_LOAN_BOOK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
  credit_policy:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CREDIT_POLICY_SEARCH
    id_column: CHUNK_ID
    title_column: DOC_TITLE
    max_results: 5
  customer_notes:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES_SEARCH
    id_column: NOTE_ID
    title_column: NOTE_DATE
    max_results: 10
    columns_and_descriptions:
      NOTE_TEXT:
        description: "Free-text note of a customer contact."
        type: string
        searchable: true
        filterable: false
      CUSTOMER_ID:
        description: "Customer identifier, format C00001."
        type: string
        searchable: false
        filterable: true
  affordability_check:
    type: procedure
    identifier: NORTHBANK_AGENT_EVALS.DEMO.AFFORDABILITY_CHECK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
$$;

-- VERSION$2: same model, richer instructions.
ALTER AGENT LENDING_OPS_AGENT MODIFY LIVE VERSION SET SPECIFICATION =
$$
models:
  orchestration: claude-sonnet-4-5

orchestration:
  budget:
    seconds: 300
    tokens: 32000

instructions:
  system: "You are the Northbank Lending Ops Agent, an internal assistant for Northbank credit operations and collections colleagues. You support colleagues; you never give advice to customers."
  response: |
    Be concise and factual, in UK English. State the numbers you used and the period they cover.
    When you cite policy, name the document and version. If you used a superseded policy, say so and say why it applies.
  orchestration: |
    Tool routing:
    - loan_book: applications, decisions, loans, arrears and forbearance figures.
    - credit_policy: Northbank policy and procedure wording.
    - customer_notes: contact and hardship notes for a named customer. Always filter on CUSTOMER_ID.
    - affordability_check: any affordability or debt-to-income calculation. Never calculate it yourself.

    Data rules for loan_book:
    - "Applications" means unique applications: always exclude duplicate submissions (IS_DUPLICATE_SUBMISSION = FALSE) unless the user asks for all records.
    - Date ranges refer to the application received date (APPLICATION_DATE) unless the user says otherwise. Do not use the decision date.
    - Ask for one complete result set in a single loan_book call. Do not re-query the same tool to confirm a result you already have.

    Policy rules:
    - Policy documents carry a status (CURRENT or SUPERSEDED) and an effective date in each result. Apply the version that was in force on the application date in question; for general questions use the CURRENT version.
    - One credit_policy search per topic is normally enough.

    Arrears cases:
    - Before recommending a Collections referral or a default notice, check the customer's notes with customer_notes. Treat stated or implied health, bereavement, job loss, caring or mental-health circumstances as vulnerability indicators. A third party's situation (for example a neighbour or colleague) is not an indicator for the customer.
    - If an indicator is present, do not recommend the standard action. Recommend the Vulnerable Customer Procedure steps instead and honour any communication request the customer made.

    Out of scope and refusals:
    - For questions outside Northbank lending operations (markets, economic forecasts, general knowledge), answer briefly that it is out of scope without calling any tool.
    - Never propose rules based on age or other protected characteristics, and never tell a customer whether they personally should take credit. Check credit_policy for the wording, but do not query loan_book for these.
  sample_questions:
    - question: "What was the approval rate for unique applications in May 2026?"
    - question: "What is the minimum credit score for a personal loan?"
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: loan_book
      description: "Northbank loan book: applications, credit decisions, booked loans and cards, arrears cases and forbearance arrangements (Jan 2025 to Jun 2026)."
  - tool_spec:
      type: cortex_search
      name: credit_policy
      description: "Northbank credit policy and procedure documents."
  - tool_spec:
      type: cortex_search
      name: customer_notes
      description: "Customer contact and hardship notes recorded by Northbank colleagues."
  - tool_spec:
      type: generic
      name: affordability_check
      description: "Calculates debt-to-income ratio and pass/fail for a proposed personal loan or credit card under the Northbank Affordability Standard."
      input_schema:
        type: object
        properties:
          PRODUCT:
            type: string
            description: "PERSONAL_LOAN or CREDIT_CARD"
          ANNUAL_INCOME:
            type: number
            description: "Gross annual income in GBP"
          MONTHLY_COMMITMENTS:
            type: number
            description: "Existing monthly credit commitments in GBP"
          AMOUNT:
            type: number
            description: "Loan amount or credit limit in GBP"
          TERM_MONTHS:
            type: number
            description: "Loan term in months (use 0 for credit cards)"
        required: [PRODUCT, ANNUAL_INCOME, MONTHLY_COMMITMENTS, AMOUNT, TERM_MONTHS]

tool_resources:
  loan_book:
    semantic_view: NORTHBANK_AGENT_EVALS.DEMO.SV_LOAN_BOOK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
  credit_policy:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CREDIT_POLICY_SEARCH
    id_column: CHUNK_ID
    title_column: DOC_TITLE
    max_results: 5
  customer_notes:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES_SEARCH
    id_column: NOTE_ID
    title_column: NOTE_DATE
    max_results: 10
    columns_and_descriptions:
      NOTE_TEXT:
        description: "Free-text note of a customer contact."
        type: string
        searchable: true
        filterable: false
      CUSTOMER_ID:
        description: "Customer identifier, format C00001."
        type: string
        searchable: false
        filterable: true
  affordability_check:
    type: procedure
    identifier: NORTHBANK_AGENT_EVALS.DEMO.AFFORDABILITY_CHECK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
$$;
ALTER AGENT LENDING_OPS_AGENT COMMIT COMMENT = 'VERSION$2: rich instructions, model A';

-- VERSION$3: VERSION$2's instructions, different orchestration model.
ALTER AGENT LENDING_OPS_AGENT ADD LIVE VERSION FROM LAST;
ALTER AGENT LENDING_OPS_AGENT MODIFY LIVE VERSION SET SPECIFICATION =
$$
models:
  orchestration: claude-sonnet-5

orchestration:
  budget:
    seconds: 300
    tokens: 32000

instructions:
  system: "You are the Northbank Lending Ops Agent, an internal assistant for Northbank credit operations and collections colleagues. You support colleagues; you never give advice to customers."
  response: |
    Be concise and factual, in UK English. State the numbers you used and the period they cover.
    When you cite policy, name the document and version. If you used a superseded policy, say so and say why it applies.
  orchestration: |
    Tool routing:
    - loan_book: applications, decisions, loans, arrears and forbearance figures.
    - credit_policy: Northbank policy and procedure wording.
    - customer_notes: contact and hardship notes for a named customer. Always filter on CUSTOMER_ID.
    - affordability_check: any affordability or debt-to-income calculation. Never calculate it yourself.

    Data rules for loan_book:
    - "Applications" means unique applications: always exclude duplicate submissions (IS_DUPLICATE_SUBMISSION = FALSE) unless the user asks for all records.
    - Date ranges refer to the application received date (APPLICATION_DATE) unless the user says otherwise. Do not use the decision date.
    - Ask for one complete result set in a single loan_book call. Do not re-query the same tool to confirm a result you already have.

    Policy rules:
    - Policy documents carry a status (CURRENT or SUPERSEDED) and an effective date in each result. Apply the version that was in force on the application date in question; for general questions use the CURRENT version.
    - One credit_policy search per topic is normally enough.

    Arrears cases:
    - Before recommending a Collections referral or a default notice, check the customer's notes with customer_notes. Treat stated or implied health, bereavement, job loss, caring or mental-health circumstances as vulnerability indicators. A third party's situation (for example a neighbour or colleague) is not an indicator for the customer.
    - If an indicator is present, do not recommend the standard action. Recommend the Vulnerable Customer Procedure steps instead and honour any communication request the customer made.

    Out of scope and refusals:
    - For questions outside Northbank lending operations (markets, economic forecasts, general knowledge), answer briefly that it is out of scope without calling any tool.
    - Never propose rules based on age or other protected characteristics, and never tell a customer whether they personally should take credit. Check credit_policy for the wording, but do not query loan_book for these.
  sample_questions:
    - question: "What was the approval rate for unique applications in May 2026?"
    - question: "What is the minimum credit score for a personal loan?"
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: loan_book
      description: "Northbank loan book: applications, credit decisions, booked loans and cards, arrears cases and forbearance arrangements (Jan 2025 to Jun 2026)."
  - tool_spec:
      type: cortex_search
      name: credit_policy
      description: "Northbank credit policy and procedure documents."
  - tool_spec:
      type: cortex_search
      name: customer_notes
      description: "Customer contact and hardship notes recorded by Northbank colleagues."
  - tool_spec:
      type: generic
      name: affordability_check
      description: "Calculates debt-to-income ratio and pass/fail for a proposed personal loan or credit card under the Northbank Affordability Standard."
      input_schema:
        type: object
        properties:
          PRODUCT:
            type: string
            description: "PERSONAL_LOAN or CREDIT_CARD"
          ANNUAL_INCOME:
            type: number
            description: "Gross annual income in GBP"
          MONTHLY_COMMITMENTS:
            type: number
            description: "Existing monthly credit commitments in GBP"
          AMOUNT:
            type: number
            description: "Loan amount or credit limit in GBP"
          TERM_MONTHS:
            type: number
            description: "Loan term in months (use 0 for credit cards)"
        required: [PRODUCT, ANNUAL_INCOME, MONTHLY_COMMITMENTS, AMOUNT, TERM_MONTHS]

tool_resources:
  loan_book:
    semantic_view: NORTHBANK_AGENT_EVALS.DEMO.SV_LOAN_BOOK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
  credit_policy:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CREDIT_POLICY_SEARCH
    id_column: CHUNK_ID
    title_column: DOC_TITLE
    max_results: 5
  customer_notes:
    search_service: NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES_SEARCH
    id_column: NOTE_ID
    title_column: NOTE_DATE
    max_results: 10
    columns_and_descriptions:
      NOTE_TEXT:
        description: "Free-text note of a customer contact."
        type: string
        searchable: true
        filterable: false
      CUSTOMER_ID:
        description: "Customer identifier, format C00001."
        type: string
        searchable: false
        filterable: true
  affordability_check:
    type: procedure
    identifier: NORTHBANK_AGENT_EVALS.DEMO.AFFORDABILITY_CHECK
    execution_environment:
      type: warehouse
      warehouse: NORTHBANK_EVAL_WH
$$;
ALTER AGENT LENDING_OPS_AGENT COMMIT COMMENT = 'VERSION$3: rich instructions, model B';

-- Note which version is now the DEFAULT: committing a version moves it. Any evaluation
-- or application that does not pin a version follows it silently.
SHOW VERSIONS IN AGENT LENDING_OPS_AGENT;

-- Smoke test against a pinned version
SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'NORTHBANK_AGENT_EVALS.DEMO.LENDING_OPS_AGENT!VERSION$1',
  $${"messages": [{"role": "user", "content": [{"type": "text", "text": "How many unique applications were received in May 2026?"}]}]}$$
)):content AS response;
