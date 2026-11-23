USE DATABASE <your db>;
USE SCHEMA <your db>.<your schema>;
USE WAREHOUSE <your warehouse>;
CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', 'distribution_reconciliation_v1'), '@<your db>.<your schema>.DEMO_ASSETS/evaluation/v1/evaluation.yaml');
SELECT * FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('<your db>', '<your schema>', 'WATERFALL_REVIEW_AGENT', 'CORTEX AGENT', 'distribution_reconciliation_v1'));
