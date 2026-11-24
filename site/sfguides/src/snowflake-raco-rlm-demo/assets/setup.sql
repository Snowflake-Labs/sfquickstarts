-- Run only with an authorized write role after reviewing the namespace.
CREATE DATABASE IF NOT EXISTS RACO_RLM_DEMO;
CREATE SCHEMA IF NOT EXISTS RACO_RLM_DEMO.PUBLIC;
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.SUPPORT_MESSAGES (
  THREAD_ID VARCHAR, MESSAGE_ID VARCHAR, POSTED_AT TIMESTAMP_NTZ, BODY VARCHAR
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.THREAD_RESULTS (
  THREAD_ID VARCHAR, STATUS VARCHAR, EVIDENCE_IDS VARIANT
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.VALIDATED_ISSUES (
  THREAD_ID VARCHAR, TITLE VARCHAR, DOCUMENT VARCHAR, EVIDENCE_IDS VARIANT
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.ISSUE_CHUNKS (
  CHUNK_ID VARCHAR, THREAD_ID VARCHAR, TITLE VARCHAR, CHUNK_TEXT VARCHAR, EVIDENCE_IDS VARIANT
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.VISION_KEYPOINTS (
  RUN_ID VARCHAR, POINT_INDEX INTEGER, PAYLOAD VARIANT
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.WEIGHT_EDIT_RUNS (
  RUN_ID VARCHAR, RESULT VARIANT
);
CREATE TABLE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.EVAL_QUESTIONS (
  INPUT_QUERY VARCHAR, GROUND_TRUTH VARIANT
);
CREATE STAGE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.MODEL_ASSETS ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

INSERT INTO RACO_RLM_DEMO.PUBLIC.SUPPORT_MESSAGES (THREAD_ID, MESSAGE_ID, POSTED_AT, BODY)
SELECT v.column1, v.column2, TO_TIMESTAMP_NTZ(v.column3), v.column4 FROM VALUES
 ('T-100', 'M-100', '2026-01-10 09:00:00', 'Scheduled task fails with missing warehouse after migration.'),
 ('T-100', 'M-101', '2026-01-10 09:02:00', 'Use a warehouse with USAGE granted to the task owner role and set it on the task.'),
 ('T-100', 'M-102', '2026-01-10 09:07:00', 'Confirmed: task succeeded after setting the authorized warehouse.'),
 ('T-200', 'M-200', '2026-01-11 11:00:00', 'Search service is missing expected results after load.'),
 ('T-200', 'M-201', '2026-01-11 11:05:00', 'Checking refresh history; no fix confirmed yet.'),
 ('T-300', 'M-300', '2026-01-12 12:00:00', 'Connector repeatedly fails authentication.'),
 ('T-300', 'M-301', '2026-01-12 12:03:00', 'Escalated to identity team for investigation; no resolution yet.') v
WHERE NOT EXISTS (
  SELECT 1 FROM RACO_RLM_DEMO.PUBLIC.SUPPORT_MESSAGES m WHERE m.MESSAGE_ID = v.column2
);

INSERT INTO RACO_RLM_DEMO.PUBLIC.EVAL_QUESTIONS (INPUT_QUERY, GROUND_TRUTH)
SELECT v.column1, PARSE_JSON(v.column2) FROM VALUES
 ('What fixed the scheduled task missing-warehouse error?', '{"ground_truth_output":"The task succeeded after an authorized warehouse was set; the task owner needs USAGE on that warehouse. Cite the resolved thread T-100, not an unresolved thread.","ground_truth_invocations":[{"tool_name":"support_search","tool_input":"Search for scheduled task warehouse failure resolution"}]}'),
 ('Was the Search service refresh issue resolved?', '{"ground_truth_output":"No validated resolution for that issue appears in this knowledge base. Do not invent a fix.","ground_truth_invocations":[{"tool_name":"support_search"}]}'),
 ('How do I solve the connector authentication issue?', '{"ground_truth_output":"The thread was escalated with no confirmed resolution; do not give an invented fix.","ground_truth_invocations":[{"tool_name":"support_search"}]}') v
WHERE NOT EXISTS (
  SELECT 1 FROM RACO_RLM_DEMO.PUBLIC.EVAL_QUESTIONS q WHERE q.INPUT_QUERY = v.column1
);