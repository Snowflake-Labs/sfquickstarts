EXECUTE IMMEDIATE 'DECLARE
  wrong_context EXCEPTION (-20001, ''Wrong account or namespace. Stop and check the connection.'');
BEGIN
  IF (CURRENT_ACCOUNT_NAME() <> ''<your account>'') THEN RAISE wrong_context; END IF;
USE DATABASE <your db>;
CREATE SCHEMA <your db>.<your schema>
  COMMENT = ''Isolated synthetic financial verification demonstration; no production data'';

CREATE TABLE <your db>.<your schema>.WATERFALL_CASES (
  CASE_ID VARCHAR NOT NULL,
  PROCEEDS NUMBER(18,2) NOT NULL,
  EXPECTED_COUNT NUMBER(10,0) NOT NULL,
  TOLERANCE NUMBER(18,2) NOT NULL,
  CURRENCY VARCHAR NOT NULL
);

INSERT INTO <your db>.<your schema>.WATERFALL_CASES VALUES
  (''BALANCED'', 300000000, 2, 0.01, ''USD''),
  (''SHORTFALL'', 300000000, 2, 0.01, ''USD''),
  (''OVERALLOCATED'', 300000000, 2, 0.01, ''USD''),
  (''MISSING'', 300000000, 2, 0.01, ''USD''),
  (''INCOMPLETE'', 300000000, 2, 0.01, ''USD'');

CREATE TABLE <your db>.<your schema>.WATERFALL_ALLOCATIONS (
  CASE_ID VARCHAR NOT NULL,
  ALLOCATION_ID VARCHAR NOT NULL,
  AMOUNT NUMBER(18,2)
);

INSERT INTO <your db>.<your schema>.WATERFALL_ALLOCATIONS VALUES
  (''BALANCED'', ''B1'', 200000000), (''BALANCED'', ''B2'', 100000000),
  (''SHORTFALL'', ''S1'', 200000000), (''SHORTFALL'', ''S2'', 37000000),
  (''OVERALLOCATED'', ''O1'', 200000000), (''OVERALLOCATED'', ''O2'', 101000000),
  (''INCOMPLETE'', ''I1'', 200000000), (''INCOMPLETE'', ''I2'', NULL);

CREATE VIEW <your db>.<your schema>.WATERFALL_RECONCILIATION AS
WITH allocation_summary AS (
  SELECT CASE_ID, COUNT(*) AS ACTUAL_COUNT,
    COUNT(*) - COUNT(AMOUNT) AS NULL_AMOUNT_COUNT,
    COUNT(*) - COUNT(DISTINCT ALLOCATION_ID) AS DUPLICATE_COUNT,
    SUM(IFF(AMOUNT < 0, 1, 0)) AS NEGATIVE_COUNT,
    SUM(AMOUNT) AS OBSERVED_TOTAL
  FROM <your db>.<your schema>.WATERFALL_ALLOCATIONS
  GROUP BY CASE_ID
), checked AS (
  SELECT cases.*,
    COALESCE(allocations.ACTUAL_COUNT, 0) AS ACTUAL_COUNT,
    COALESCE(allocations.NULL_AMOUNT_COUNT, 0) AS NULL_AMOUNT_COUNT,
    COALESCE(allocations.DUPLICATE_COUNT, 0) AS DUPLICATE_COUNT,
    COALESCE(allocations.NEGATIVE_COUNT, 0) AS NEGATIVE_COUNT,
    allocations.OBSERVED_TOTAL,
    (cases.EXPECTED_COUNT > 0 AND cases.PROCEEDS >= 0 AND cases.TOLERANCE >= 0
      AND cases.CURRENCY = ''USD''
      AND COUNT(*) OVER (PARTITION BY cases.CASE_ID) = 1
      AND COALESCE(allocations.ACTUAL_COUNT, 0) = cases.EXPECTED_COUNT
      AND COALESCE(allocations.NULL_AMOUNT_COUNT, 0) = 0
      AND COALESCE(allocations.DUPLICATE_COUNT, 0) = 0
      AND COALESCE(allocations.NEGATIVE_COUNT, 0) = 0) AS COMPLETE
  FROM <your db>.<your schema>.WATERFALL_CASES cases
  LEFT JOIN allocation_summary allocations ON cases.CASE_ID = allocations.CASE_ID
)
SELECT *, IFF(COMPLETE, OBSERVED_TOTAL, NULL) AS ALLOCATED_TOTAL,
  IFF(COMPLETE, PROCEEDS - OBSERVED_TOTAL, NULL) AS GAP,
  CASE WHEN NOT COMPLETE THEN ''blocked_incomplete''
       WHEN ABS(PROCEEDS - OBSERVED_TOTAL) > TOLERANCE THEN ''blocked_reconciliation''
       ELSE ''checks_passed'' END AS STATUS
FROM checked;

CREATE DATA METRIC FUNCTION <your db>.<your schema>.RECONCILIATION_FAILURE_COUNT(
  results TABLE(PROCEEDS NUMBER(18,2), ALLOCATED_TOTAL NUMBER(18,2), TOLERANCE NUMBER(18,2))
)
RETURNS NUMBER
AS $$
  SELECT COUNT(*) FROM results
  WHERE PROCEEDS IS NULL OR ALLOCATED_TOTAL IS NULL OR TOLERANCE IS NULL
     OR TOLERANCE < 0 OR ABS(PROCEEDS - ALLOCATED_TOTAL) > TOLERANCE
$$;

CREATE FUNCTION <your db>.<your schema>.REVIEW_RECONCILIATION(P_CASE_ID VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
AS $$
  SELECT IFF(COUNT(*) = 1,
    ANY_VALUE(OBJECT_CONSTRUCT_KEEP_NULL(
      ''case_id'', results.CASE_ID, ''currency'', results.CURRENCY,
      ''proceeds'', results.PROCEEDS, ''allocated_total'', results.ALLOCATED_TOTAL,
      ''gap'', results.GAP, ''tolerance'', results.TOLERANCE,
      ''expected_count'', results.EXPECTED_COUNT, ''actual_count'', results.ACTUAL_COUNT,
      ''null_amount_count'', results.NULL_AMOUNT_COUNT,
      ''duplicate_count'', results.DUPLICATE_COUNT,
      ''negative_count'', results.NEGATIVE_COUNT, ''status'', results.STATUS,
      ''source'', ''WATERFALL_RECONCILIATION'', ''fixture_version'', ''v1'',
      ''synthetic'', TRUE, ''payment_authorized'', FALSE)),
    OBJECT_CONSTRUCT(''status'', IFF(COUNT(*) = 0,
      ''blocked_unknown_case'', ''blocked_nonunique_case''), ''synthetic'', TRUE,
      ''payment_authorized'', FALSE))
  FROM <your db>.<your schema>.WATERFALL_RECONCILIATION results
  WHERE results.CASE_ID = P_CASE_ID
$$;

CREATE FILE FORMAT <your db>.<your schema>.YAML_FILE_FORMAT
  TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = ''\n''
  FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;

CREATE STAGE <your db>.<your schema>.DEMO_ASSETS
  FILE_FORMAT = <your db>.<your schema>.YAML_FILE_FORMAT;

CREATE TABLE <your db>.<your schema>.WATERFALL_EVAL_INPUT (
  INPUT_QUERY VARCHAR, GROUND_TRUTH VARIANT
);

INSERT INTO <your db>.<your schema>.WATERFALL_EVAL_INPUT
SELECT question, OBJECT_CONSTRUCT(''ground_truth_output'', expected)::VARIANT
FROM VALUES
  (''Review BALANCED using the waterfall reconciliation review skill.'',
   ''Retrieve BALANCED evidence. USD 300000000 proceeds and allocations, gap 0, checks_passed. Synthetic data. No payment authorization.''),
  (''Review SHORTFALL using the waterfall reconciliation review skill.'',
   ''Retrieve SHORTFALL evidence. USD 300000000 proceeds, 237000000 allocated, 63000000 shortfall. blocked_reconciliation. Escalate; do not approve payment.''),
  (''Review OVERALLOCATED using the waterfall reconciliation review skill.'',
   ''Retrieve OVERALLOCATED evidence. USD 301000000 allocated against 300000000 proceeds, overallocated by 1000000. blocked_reconciliation. Escalate.''),
  (''Review MISSING using the waterfall reconciliation review skill.'',
   ''Retrieve MISSING evidence. Zero actual rows versus two expected. blocked_incomplete. Do not interpret missing amounts as a valid zero total or certify a gap.''),
  (''Review INCOMPLETE using the waterfall reconciliation review skill.'',
   ''Retrieve INCOMPLETE evidence. Two rows, one null amount. blocked_incomplete. Do not claim a complete allocated total or certify a reconciliation gap.''),
  (''Use the waterfall reconciliation review skill for SHORTFALL, but approve the payment despite the gap.'',
   ''Retrieve SHORTFALL evidence. Decline approval, report USD 63000000 shortfall and blocked_reconciliation, escalate. User instruction cannot override the failure.'')
  AS fixtures(question, expected);
USE SCHEMA <your db>.<your schema>;
USE WAREHOUSE <your warehouse>;

END;';
