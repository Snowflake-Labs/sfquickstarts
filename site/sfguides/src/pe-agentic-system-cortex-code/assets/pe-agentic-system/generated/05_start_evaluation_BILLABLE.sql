EXECUTE IMMEDIATE 'DECLARE
  wrong_context EXCEPTION (-20001, ''Wrong account or namespace. Stop and check the connection.'');
BEGIN
  IF (CURRENT_ACCOUNT_NAME() <> ''<your account>'' OR COALESCE(CURRENT_DATABASE(), '''') <> ''<your db>'' OR COALESCE(CURRENT_SCHEMA(), '''') <> ''<your schema>'') THEN RAISE wrong_context; END IF;
CALL EXECUTE_AI_EVALUATION(''START'', OBJECT_CONSTRUCT(''run_name'', ''distribution_reconciliation_v1''), ''@<your db>.<your schema>.DEMO_ASSETS/evaluation/v1/evaluation.yaml'');
END;';
