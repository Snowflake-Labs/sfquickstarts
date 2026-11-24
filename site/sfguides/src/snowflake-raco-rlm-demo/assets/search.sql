-- Replace DEMO_WH with a warehouse your demo role can use. Run after support notebook.
-- Review before execution: indexing and serving incur charges.
CREATE CORTEX SEARCH SERVICE IF NOT EXISTS RACO_RLM_DEMO.PUBLIC.SUPPORT_SEARCH
  ON CHUNK_TEXT
  WAREHOUSE = DEMO_WH
  TARGET_LAG = '1 day'
  AS (SELECT CHUNK_ID, THREAD_ID, TITLE, CHUNK_TEXT, EVIDENCE_IDS
      FROM RACO_RLM_DEMO.PUBLIC.ISSUE_CHUNKS);

SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
    'RACO_RLM_DEMO.PUBLIC.SUPPORT_SEARCH',
    '{"query":"scheduled task missing warehouse fix","columns":["CHUNK_ID","THREAD_ID","TITLE","CHUNK_TEXT","EVIDENCE_IDS"],"limit":3}'
  )):results AS HITS;