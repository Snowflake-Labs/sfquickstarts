-- ============================================================
-- Helpful queries for the lab
-- Run any block by selecting it and pressing Cmd+Return (Mac) or Ctrl+Enter (Windows)
-- ============================================================


-- ── Data: loan applications ──────────────────────────────────────────────────

-- All loan applications
SELECT * FROM LENDING.LOANS.APPLICATIONS ORDER BY APPLICATION_DATE DESC;

-- Pending applications only
SELECT APPLICANT_ID, FIRST_NAME, LAST_NAME, CREDIT_SCORE, DEBT_TO_INCOME_RATIO, REQUESTED_AMOUNT
FROM LENDING.LOANS.APPLICATIONS
WHERE STATUS = 'PENDING';


-- ── Data: credit memos ───────────────────────────────────────────────────────

-- All credit memos written so far
SELECT APPLICANT_ID, REPORTED_DTI, RECOMPUTED_DTI, EVIDENCE_REFS, GENERATED_AT
FROM LENDING.LOANS.CREDIT_MEMO
ORDER BY GENERATED_AT DESC;

-- Delete a credit memo so an agent can rewrite it
DELETE FROM LENDING.LOANS.CREDIT_MEMO WHERE APPLICANT_ID = 'APP_1004';


-- ── Data: underwriting log ───────────────────────────────────────────────────

-- All underwriting log entries
SELECT l.APPLICANT_ID, l.ARRIVED_AT, l.DECIDED_AT,
       a.STATUS, a.POLICY_TIER, a.APPROVED_AMOUNT, a.ESCALATION_QUESTION
FROM LENDING.LOANS.UNDERWRITING_LOG l
JOIN LENDING.LOANS.APPLICATIONS a ON a.APPLICANT_ID = l.APPLICANT_ID
ORDER BY l.ARRIVED_AT DESC;

-- Reset an application decision back to PENDING
UPDATE LENDING.LOANS.APPLICATIONS
SET STATUS = 'PENDING', POLICY_TIER = NULL, APPROVED_AMOUNT = NULL,
    MAX_EXPOSURE = NULL, ESCALATION_QUESTION = NULL, PROCESSED_AT = NULL
WHERE APPLICANT_ID = 'APP_1001';


-- ── Documents: stage and search index ────────────────────────────────────────

-- List all documents on the stage
LIST @LENDING.LOANS.LAB_FILES;

-- Preview indexed document chunks (what the search service sees)
SELECT APPLICANT_ID, DOC_TYPE, FILE_NAME, LEFT(CHUNK_TEXT, 200) AS PREVIEW
FROM LENDING.LOANS.DOCUMENT_CHUNKS
ORDER BY APPLICANT_ID, DOC_TYPE
LIMIT 50;

-- Search chunks for a specific applicant
SELECT DOC_TYPE, FILE_NAME, CHUNK_TEXT
FROM LENDING.LOANS.DOCUMENT_CHUNKS
WHERE APPLICANT_ID = 'APP_1004'
ORDER BY DOC_TYPE;


-- ── Agents ───────────────────────────────────────────────────────────────────

-- List all agents in the schema
SHOW AGENTS IN SCHEMA LENDING.LOANS;

-- Describe an agent (shows tools, budget, instructions)
DESCRIBE AGENT LENDING.LOANS.CREDIT_ANALYST_AGENT_BASELINE;
DESCRIBE AGENT LENDING.LOANS.CREDIT_ANALYST_AGENT_IMPROVED;
DESCRIBE AGENT LENDING.LOANS.UNDERWRITING_AGENT;
DESCRIBE AGENT LENDING.LOANS.UNDERWRITER_WITH_DELEGATION_AGENT;

-- Drop the baseline agent to rebuild it from scratch in Step 3.1.1. Do not drop
-- the other three: setup created them and the lab does not recreate them.
DROP AGENT IF EXISTS LENDING.LOANS.CREDIT_ANALYST_AGENT_BASELINE;

-- Restore the live version if the agent has no live version (e.g. after a Deploy commit)
ALTER AGENT LENDING.LOANS.CREDIT_ANALYST_AGENT_BASELINE ADD LIVE VERSION FROM LAST;
ALTER AGENT LENDING.LOANS.CREDIT_ANALYST_AGENT_IMPROVED ADD LIVE VERSION FROM LAST;
ALTER AGENT LENDING.LOANS.UNDERWRITING_AGENT ADD LIVE VERSION FROM LAST;
ALTER AGENT LENDING.LOANS.UNDERWRITER_WITH_DELEGATION_AGENT ADD LIVE VERSION FROM LAST;


-- ── MCP servers ──────────────────────────────────────────────────────────────

SHOW MCP SERVERS IN SCHEMA LENDING.LOANS;

-- If CREDIT_ANALYST_MCP is missing, copy its CREATE MCP SERVER statement from
-- setup.sql and run it in a separate SQL file.


-- ── Evaluations ──────────────────────────────────────────────────────────────

-- Start an evaluation run on the baseline agent
CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'my_baseline_run'),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_baseline_eval.yaml'
);

-- Start an evaluation run on the improved agent
CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'my_run'),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_eval.yaml'
);

-- Check status of a run (use the matching YAML for the agent)
CALL EXECUTE_AI_EVALUATION(
  'STATUS',
  OBJECT_CONSTRUCT('run_name', 'my_run'),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_eval.yaml'
);

-- Delete a run (use the matching YAML for the agent)
CALL EXECUTE_AI_EVALUATION(
  'DELETE',
  OBJECT_CONSTRUCT('run_name', 'my_run'),
  '@LENDING.LOANS.LAB_STAGE/credit_analyst_eval.yaml'
);


-- ── Optional: streams and tasks ──────────────────────────────────────────────

SHOW STREAMS IN SCHEMA LENDING.LOANS;
SHOW TASKS IN SCHEMA LENDING.LOANS;

DROP STREAM IF EXISTS LENDING.LOANS.NEW_APPLICATIONS;
DROP TASK IF EXISTS LENDING.LOANS.UNDERWRITE_ON_ARRIVAL;

-- Check task run history
SELECT NAME, STATE, ERROR_MESSAGE, SCHEDULED_TIME, COMPLETED_TIME
FROM TABLE(LENDING.INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('hour', -2, CURRENT_TIMESTAMP()),
    TASK_NAME => 'UNDERWRITE_ON_ARRIVAL'
))
ORDER BY SCHEDULED_TIME DESC LIMIT 10;
