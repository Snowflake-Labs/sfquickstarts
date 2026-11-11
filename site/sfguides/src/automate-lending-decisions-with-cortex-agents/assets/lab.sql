-- ============================================================
-- lab.sql  —  Agentic lending lab: AI Underwriting
-- ============================================================
-- Each section is labelled with the module step it belongs to.
-- To run a block: select the statements and press
--   Cmd+Return  (Mac) / Ctrl+Enter  (Windows)
-- ============================================================

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE LENDING_WH;
USE DATABASE LENDING;
USE SCHEMA LOANS;


-- ── Step 3.1.3  ───────────────────────────────────────────────────────────────
-- Run the first evaluation (use if CoCo does not run it automatically).

CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'baseline_' || TO_CHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISS')),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_baseline_eval.yaml'
);


-- ── Step 3.2.3  ───────────────────────────────────────────────────────────────
-- Run the evaluation on the improved agent.

CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'improved_' || TO_CHAR(CURRENT_TIMESTAMP(), 'YYYYMMDD_HH24MISS')),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_eval.yaml'
);


-- ── MODULE 4: Before you start ────────────────────────────────────────────────
-- Resets APP_1001 and APP_1004 to their correct starting state.
-- Run this entire block before Step 4.1.1.

UPDATE LENDING.LOANS.APPLICATIONS
SET STATUS = 'PENDING', POLICY_TIER = NULL, APPROVED_AMOUNT = NULL,
    MAX_EXPOSURE = NULL, ESCALATION_QUESTION = NULL, PROCESSED_AT = NULL
WHERE APPLICANT_ID IN ('APP_1001', 'APP_1004');

-- Remove any existing memo for Diane Whitfield so the agent must escalate.
DELETE FROM LENDING.LOANS.CREDIT_MEMO WHERE APPLICANT_ID = 'APP_1001';

-- Set Grant Kelleher's memo to what diligence should have found.
CALL LENDING.LOANS.WRITE_CREDIT_MEMO(
  'APP_1004',
  0.52,
  '{"guaranteed_commercial_loan_monthly": 3870.00, "cosigned_auto_loan_monthly": 612.00}',
  'Bank statement shows a commercial loan payment under a personal guarantee and a co-signed auto loan payment, neither on the credit report. Both are personal obligations, so the ratio after diligence is 0.52 against 0.19 reported.',
  'doc_APP_1004_bank_statement.pdf,doc_APP_1004_commercial_loan_agreement.pdf,doc_APP_1004_auto_loan_statement.pdf'
);


-- ── Step 4.1.2  ───────────────────────────────────────────────────────────────
-- Check Grant Kelleher's decision after the underwriting agent runs.

SELECT APPLICANT_ID, STATUS, APPROVED_AMOUNT, POLICY_TIER, MAX_EXPOSURE
FROM LENDING.LOANS.APPLICATIONS
WHERE APPLICANT_ID = 'APP_1004';


-- ── Step 4.1.3  ───────────────────────────────────────────────────────────────
-- Clear Diane Whitfield's memo if she has one from a prior run.

DELETE FROM LENDING.LOANS.CREDIT_MEMO WHERE APPLICANT_ID = 'APP_1001';


-- ── Step 4.2.2  ───────────────────────────────────────────────────────────────
-- Check both decisions after the delegation agent runs.

SELECT APPLICANT_ID, STATUS, APPROVED_AMOUNT, POLICY_TIER, MAX_EXPOSURE
FROM LENDING.LOANS.APPLICATIONS
WHERE APPLICANT_ID IN ('APP_1001', 'APP_1004')
ORDER BY APPLICANT_ID;


-- ── Optional Step 4.3.1  ──────────────────────────────────────────────────────
-- Create the stream that watches for new loan applications.

CREATE OR REPLACE STREAM LENDING.LOANS.NEW_APPLICATIONS
  ON TABLE LENDING.LOANS.APPLICATIONS
  APPEND_ONLY = TRUE;


-- ── Optional Step 4.3.2  ──────────────────────────────────────────────────────
-- Create the task and start it.

CREATE OR REPLACE TASK LENDING.LOANS.UNDERWRITE_ON_ARRIVAL
  WAREHOUSE = LENDING_WH
  WHEN SYSTEM$STREAM_HAS_DATA('LENDING.LOANS.NEW_APPLICATIONS')
AS
  CALL LENDING.LOANS.UNDERWRITE_ARRIVALS();

ALTER TASK LENDING.LOANS.UNDERWRITE_ON_ARRIVAL RESUME;


-- ── Optional Step 4.3.3 (part 1)  ────────────────────────────────────────────
-- Submit a new loan application to trigger the task.

DELETE FROM LENDING.LOANS.APPLICATIONS WHERE APPLICANT_ID = 'APP_2001';
DELETE FROM LENDING.LOANS.UNDERWRITING_LOG WHERE APPLICANT_ID = 'APP_2001';

INSERT INTO LENDING.LOANS.APPLICATIONS
    (APPLICANT_ID, FIRST_NAME, LAST_NAME, CREDIT_SCORE, ANNUAL_INCOME,
     DEBT_TO_INCOME_RATIO, REQUESTED_AMOUNT, LOAN_PURPOSE,
     EMPLOYMENT_STATUS, YEARS_EMPLOYED, APPLICATION_DATE, STATUS)
VALUES
    ('APP_2001', 'Ana', 'Ferreira', 775, 135000, 0.19, 40000,
     'home improvement', 'employed', 8, CURRENT_DATE(), 'PENDING');


-- ── Optional Step 4.3.3 (part 2)  ────────────────────────────────────────────
-- Poll until DECIDED_AT fills in (~1-2 minutes). Run this a few times.

SELECT l.APPLICANT_ID, l.ARRIVED_AT, l.DECIDED_AT,
       a.STATUS, a.POLICY_TIER, a.APPROVED_AMOUNT
FROM LENDING.LOANS.UNDERWRITING_LOG l
JOIN LENDING.LOANS.APPLICATIONS a ON a.APPLICANT_ID = l.APPLICANT_ID
ORDER BY l.ARRIVED_AT DESC;


-- ── Optional Step 4.3.3 (part 3)  ────────────────────────────────────────────
-- Suspend the task once you are done.

ALTER TASK LENDING.LOANS.UNDERWRITE_ON_ARRIVAL SUSPEND;
