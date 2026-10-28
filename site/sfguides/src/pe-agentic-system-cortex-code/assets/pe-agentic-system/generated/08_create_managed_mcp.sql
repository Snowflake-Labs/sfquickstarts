-- Run only after 01_setup.sql and 02_checks.sql succeed. Stop on any error.
-- No agent or managed evaluation is required for this direct-function MCP demo.
EXECUTE IMMEDIATE 'DECLARE
  wrong_context EXCEPTION (-20001, ''Wrong account or namespace. Stop and check the connection.'');
BEGIN
  IF (CURRENT_ACCOUNT_NAME() <> ''<your account>'') THEN RAISE wrong_context; END IF;
USE DATABASE <your db>;
USE SCHEMA <your db>.<your schema>;
USE WAREHOUSE <your warehouse>;
DESCRIBE FUNCTION <your db>.<your schema>.REVIEW_RECONCILIATION(VARCHAR);
CREATE MCP SERVER <your db>.<your schema>.FINANCIAL_VERIFICATION_MCP
FROM SPECIFICATION $$
tools:
- name: review_distribution_reconciliation
  title: Review synthetic distribution reconciliation
  type: GENERIC
  identifier: <your db>.<your schema>.REVIEW_RECONCILIATION
  description: Review one synthetic distribution case for completeness and conservation.
    Returns recorded amounts, discrepancy and blocking status. Does not verify contractual
    entitlements or authorize payments. Accepts BALANCED, SHORTFALL, OVERALLOCATED,
    MISSING or INCOMPLETE; unknown cases are blocked by the function.
  config:
    type: function
    warehouse: <your warehouse>
    query_timeout: 30
    input_schema:
      type: object
      properties:
        P_CASE_ID:
          type: string
          description: Synthetic case identifier to review.
      required:
      - P_CASE_ID
      additionalProperties: false
$$;
END;';
DESCRIBE MCP SERVER <your db>.<your schema>.FINANCIAL_VERIFICATION_MCP;
