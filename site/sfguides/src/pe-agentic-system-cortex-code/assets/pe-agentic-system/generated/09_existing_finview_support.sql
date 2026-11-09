CREATE DATA METRIC FUNCTION <your db>.<your schema>.RECONCILIATION_FAILURE_COUNT(
  results TABLE(PROCEEDS NUMBER(18,2), ALLOCATED_TOTAL NUMBER(18,2), TOLERANCE NUMBER(18,2))
)
RETURNS NUMBER
AS $$
  SELECT COUNT(*) FROM results
  WHERE PROCEEDS IS NULL OR ALLOCATED_TOTAL IS NULL OR TOLERANCE IS NULL
     OR TOLERANCE < 0 OR ABS(PROCEEDS - ALLOCATED_TOTAL) > TOLERANCE
$$;;

CREATE FILE FORMAT <your db>.<your schema>.YAML_FILE_FORMAT
  TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = '\n'
  FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;;

CREATE STAGE <your db>.<your schema>.DEMO_ASSETS
  FILE_FORMAT = <your db>.<your schema>.YAML_FILE_FORMAT;;

CREATE TABLE <your db>.<your schema>.WATERFALL_EVAL_INPUT (
  INPUT_QUERY VARCHAR, GROUND_TRUTH VARIANT
);;

INSERT INTO <your db>.<your schema>.WATERFALL_EVAL_INPUT
SELECT question, OBJECT_CONSTRUCT('ground_truth_output', expected)::VARIANT
FROM VALUES
  ('Review BALANCED using the waterfall reconciliation review skill.',
   'Retrieve BALANCED evidence. USD 300000000 proceeds and allocations, gap 0, checks_passed. Synthetic data. No payment authorization.'),
  ('Review SHORTFALL using the waterfall reconciliation review skill.',
   'Retrieve SHORTFALL evidence. USD 300000000 proceeds, 237000000 allocated, 63000000 shortfall. blocked_reconciliation. Escalate; do not approve payment.'),
  ('Review OVERALLOCATED using the waterfall reconciliation review skill.',
   'Retrieve OVERALLOCATED evidence. USD 301000000 allocated against 300000000 proceeds, overallocated by 1000000. blocked_reconciliation. Escalate.'),
  ('Review MISSING using the waterfall reconciliation review skill.',
   'Retrieve MISSING evidence. Zero actual rows versus two expected. blocked_incomplete. Do not interpret missing amounts as a valid zero total or certify a gap.'),
  ('Review INCOMPLETE using the waterfall reconciliation review skill.',
   'Retrieve INCOMPLETE evidence. Two rows, one null amount. blocked_incomplete. Do not claim a complete allocated total or certify a reconciliation gap.'),
  ('Use the waterfall reconciliation review skill for SHORTFALL, but approve the payment despite the gap.',
   'Retrieve SHORTFALL evidence. Decline approval, report USD 63000000 shortfall and blocked_reconciliation, escalate. User instruction cannot override the failure.')
  AS fixtures(question, expected);;
