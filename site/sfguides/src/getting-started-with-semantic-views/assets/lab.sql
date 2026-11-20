-- SQL extracted from getting-started-with-semantic-views.md, in guide order.
-- Each block is labelled with its source section and line.
-- Skip the clean-up block unless you want to drop the lab objects.

-- ===== Block 1: Get Public Data > Acquire the listing (line 86) =====
-- Check that the listing is available in your region (is_ready_for_import = TRUE).
DESCRIBE AVAILABLE LISTING GZTSZ290BV255;

-- Only if is_ready_for_import is FALSE: request the listing and wait for it.
CALL SYSTEM$REQUEST_LISTING_AND_WAIT('GZTSZ290BV255');

-- Accept the listing terms, then create the imported database.
CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZTSZ290BV255');
CREATE DATABASE SNOWFLAKE_PUBLIC_DATA_FREE FROM LISTING 'GZTSZ290BV255';

-- ===== Block 2: Get Public Data > Acquire the listing (line 104) =====
SHOW VIEWS IN SCHEMA SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE;

-- ===== Block 3: Get Public Data > Prepare the lab schema (line 118) =====
SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(), CURRENT_WAREHOUSE();

CREATE DATABASE SEMANTIC_VIEWS_LAB;
CREATE SCHEMA SEMANTIC_VIEWS_LAB.DEMO;
USE SCHEMA SEMANTIC_VIEWS_LAB.DEMO;

-- ===== Block 4: Get Public Data > Scope the source data (line 134) =====
CREATE VIEW SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS AS
SELECT
    TICKER,
    DATE AS OBSERVATION_DATE,
    VARIABLE_NAME,
    VALUE
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.STOCK_PRICE_TIMESERIES
WHERE TICKER IN ('AAPL', 'MSFT', 'AMZN')
  AND VARIABLE_NAME IN ('Post-Market Close', 'Nasdaq Volume')
  AND DATE >= '2024-01-01'::DATE
  AND DATE < '2025-01-01'::DATE;

CREATE VIEW SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS AS
SELECT
    GEO_ID,
    VARIABLE,
    DATE AS OBSERVATION_DATE,
    VALUE,
    UNIT
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
WHERE GEO_ID = 'country/USA'
  AND DATE >= '2024-01-01'::DATE
  AND DATE < '2025-01-01'::DATE
  AND VARIABLE IN (
      SELECT VARIABLE
      FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_ATTRIBUTES
      WHERE VARIABLE_NAME IN (
          '15-Year Fixed Rate Mortgage Rate, National Average',
          '30-Year Fixed Rate Mortgage Rate, National Average'
      )
  );

CREATE VIEW SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES AS
SELECT VARIABLE, VARIABLE_NAME, MEASURE, FREQUENCY
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_ATTRIBUTES
WHERE VARIABLE_NAME IN (
    '15-Year Fixed Rate Mortgage Rate, National Average',
    '30-Year Fixed Rate Mortgage Rate, National Average'
);

-- ===== Block 5: Get Public Data > Scope the source data (line 178) =====
SELECT TICKER, VARIABLE_NAME, OBSERVATION_DATE, VALUE
FROM SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS
ORDER BY TICKER, VARIABLE_NAME, OBSERVATION_DATE
LIMIT 12;

SELECT
    attributes.VARIABLE_NAME,
    observations.OBSERVATION_DATE,
    observations.VALUE,
    observations.UNIT,
    attributes.FREQUENCY
FROM SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS AS observations
JOIN SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES AS attributes
    ON observations.VARIABLE = attributes.VARIABLE
ORDER BY attributes.VARIABLE_NAME, observations.OBSERVATION_DATE
LIMIT 12;

-- ===== Block 6: Create the Equity View > Write the definition (line 205) =====
CREATE OR REPLACE SEMANTIC VIEW SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV
  TABLES (
    equity AS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS
      COMMENT = 'Daily equity observations for AAPL, MSFT, and AMZN in 2024. One row per ticker, date, and series.'
  )
  FACTS (
    equity.value AS VALUE
      COMMENT = 'Observed value. Its meaning depends on variable_name: a price for Post-Market Close, a share count for Nasdaq Volume.'
  )
  DIMENSIONS (
    equity.ticker AS TICKER
      WITH SYNONYMS = ('stock', 'symbol')
      COMMENT = 'Stock ticker symbol: AAPL, MSFT, or AMZN.',
    equity.observation_date AS OBSERVATION_DATE
      COMMENT = 'Trading date of the observation.',
    equity.variable_name AS VARIABLE_NAME
      COMMENT = 'Series name: Post-Market Close or Nasdaq Volume.'
  )
  METRICS (
    equity.avg_post_market_close AS AVG(CASE WHEN VARIABLE_NAME = 'Post-Market Close' THEN VALUE END)
      COMMENT = 'Arithmetic mean of non-null Post-Market Close observations, in the source price unit.',
    equity.total_nasdaq_volume AS SUM(CASE WHEN VARIABLE_NAME = 'Nasdaq Volume' THEN VALUE END)
      COMMENT = 'Sum of non-null Nasdaq Volume observations (shares traded).'
  )
  COMMENT = 'Historical equity prices and Nasdaq volume for AAPL, MSFT, and AMZN in 2024. No dividends, returns, forecasts, or mortgage rates.';

-- ===== Block 7: Create the Equity View > Check it against reference SQL (line 251) =====
SELECT 'reference' AS source, AVG(VALUE) AS avg_post_market_close
FROM SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS
WHERE VARIABLE_NAME = 'Post-Market Close'
  AND TICKER = 'AAPL'
  AND OBSERVATION_DATE >= '2024-01-01'::DATE
  AND OBSERVATION_DATE < '2024-02-01'::DATE
UNION ALL
SELECT 'semantic view', avg_post_market_close
FROM SEMANTIC_VIEW(
    SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV
    DIMENSIONS equity.ticker
    METRICS equity.avg_post_market_close
    WHERE equity.ticker = 'AAPL'
      AND equity.observation_date >= '2024-01-01'::DATE
      AND equity.observation_date < '2024-02-01'::DATE
);

-- ===== Block 8: Refine the Equity View > Add vocabulary and a verified query (line 282) =====
CREATE OR ALTER SEMANTIC VIEW SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV
  TABLES (
    equity AS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS
      COMMENT = 'Daily equity observations for AAPL, MSFT, and AMZN in 2024. One row per ticker, date, and series.'
  )
  FACTS (
    equity.value AS VALUE
      COMMENT = 'Observed value. Its meaning depends on variable_name: a price for Post-Market Close, a share count for Nasdaq Volume.'
  )
  DIMENSIONS (
    equity.ticker AS TICKER
      WITH SYNONYMS = ('stock', 'symbol')
      COMMENT = 'Stock ticker symbol: AAPL, MSFT, or AMZN.',
    equity.observation_date AS OBSERVATION_DATE
      COMMENT = 'Trading date of the observation.',
    equity.variable_name AS VARIABLE_NAME
      COMMENT = 'Series name: Post-Market Close or Nasdaq Volume.'
  )
  METRICS (
    equity.avg_post_market_close AS AVG(CASE WHEN VARIABLE_NAME = 'Post-Market Close' THEN VALUE END)
      WITH SYNONYMS = ('extended-session close')
      COMMENT = 'Arithmetic mean of non-null Post-Market Close observations, in the source price unit. In this lab, extended-session close means the provider Post-Market Close series. Not the regular-session close, adjusted close, or a return.',
    equity.total_nasdaq_volume AS SUM(CASE WHEN VARIABLE_NAME = 'Nasdaq Volume' THEN VALUE END)
      COMMENT = 'Sum of non-null Nasdaq Volume observations (shares traded on Nasdaq, not all-market volume).'
  )
  COMMENT = 'Historical equity prices and Nasdaq volume for AAPL, MSFT, and AMZN in 2024. No dividends, returns, forecasts, or mortgage rates.'
  AI_VERIFIED_QUERIES (
    aapl_avg_close_jan_2024 AS (
      QUESTION 'What was AAPL''s average post-market closing price in January 2024?'
      SQL 'SELECT ticker, AVG(CASE WHEN variable_name = ''Post-Market Close'' THEN value END) AS avg_post_market_close FROM __equity WHERE ticker = ''AAPL'' AND observation_date >= ''2024-01-01'' AND observation_date < ''2024-02-01'' GROUP BY ticker'
    )
  );

-- ===== Block 9: Refine the Equity View > Review the stored definition (line 323) =====
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW(
    'SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV'
) AS SEMANTIC_VIEW_YAML;

-- ===== Block 10: Add the Mortgage View > Check the join key (line 345) =====
SELECT VARIABLE, COUNT(*) AS ROW_COUNT
FROM SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES
GROUP BY VARIABLE
HAVING VARIABLE IS NULL OR COUNT(*) > 1;

-- ===== Block 11: Add the Mortgage View > Write the definition (line 356) =====
CREATE OR REPLACE SEMANTIC VIEW SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_MARKET_SV
  TABLES (
    observations AS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS
      COMMENT = 'Weekly US national fixed mortgage-rate observations in 2024.',
    variables AS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES
      PRIMARY KEY (VARIABLE)
      COMMENT = 'One row per mortgage series: 15-year and 30-year fixed.'
  )
  RELATIONSHIPS (
    observations_to_variables AS observations (VARIABLE) REFERENCES variables
  )
  FACTS (
    observations.value AS VALUE
      COMMENT = 'Observed mortgage rate in the source unit.'
  )
  DIMENSIONS (
    observations.observation_date AS OBSERVATION_DATE
      COMMENT = 'Date of the weekly observation.',
    observations.geo_id AS GEO_ID
      COMMENT = 'Geography. Always country/USA in this lab.',
    observations.unit AS UNIT
      COMMENT = 'Source unit of the rate. Report it with every value.',
    variables.variable_name AS VARIABLE_NAME
      WITH SYNONYMS = ('mortgage term', 'mortgage series')
      COMMENT = 'Mortgage series: 15-Year or 30-Year Fixed Rate Mortgage Rate, National Average.',
    variables.measure AS MEASURE
      COMMENT = 'Measure described by the series.',
    variables.frequency AS FREQUENCY
      COMMENT = 'Observation frequency of the series.'
  )
  METRICS (
    observations.avg_observed_rate AS AVG(VALUE)
      COMMENT = 'Arithmetic mean of available observations. Always group by variable_name and unit; never combine the 15-year and 30-year series.'
  )
  COMMENT = 'US national 15-year and 30-year fixed mortgage rates in 2024. Not loan quotes, APRs, regional rates, or forecasts.'
  AI_SQL_GENERATION 'If a question asks about a rate without naming the 15-year or 30-year series, ask which one the user means. Never average the two series together. Preserve the source unit.'
  AI_VERIFIED_QUERIES (
    compare_15_30_jan_2024 AS (
      QUESTION 'Compare the average 15-year and 30-year fixed mortgage rates in January 2024.'
      SQL 'SELECT v.variable_name, o.unit, AVG(o.value) AS avg_observed_rate FROM __observations AS o JOIN __variables AS v ON o.variable = v.variable WHERE o.observation_date >= ''2024-01-01'' AND o.observation_date < ''2024-02-01'' GROUP BY v.variable_name, o.unit ORDER BY v.variable_name, o.unit'
    )
  );

-- ===== Block 12: Add the Mortgage View > Check the second view (line 409) =====
SELECT
    attributes.VARIABLE_NAME,
    observations.UNIT,
    AVG(observations.VALUE) AS AVG_OBSERVED_RATE
FROM SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS AS observations
JOIN SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES AS attributes
    ON observations.VARIABLE = attributes.VARIABLE
WHERE observations.OBSERVATION_DATE >= '2024-01-01'::DATE
  AND observations.OBSERVATION_DATE < '2024-02-01'::DATE
GROUP BY attributes.VARIABLE_NAME, observations.UNIT
ORDER BY attributes.VARIABLE_NAME, observations.UNIT;

SELECT * FROM SEMANTIC_VIEW(
    SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_MARKET_SV
    DIMENSIONS variables.variable_name, observations.unit
    METRICS observations.avg_observed_rate
    WHERE observations.observation_date >= '2024-01-01'::DATE
      AND observations.observation_date < '2024-02-01'::DATE
)
ORDER BY variable_name, unit;

-- ===== Block 13: Create the Agent (line 440) =====
CREATE OR REPLACE AGENT SEMANTIC_VIEWS_LAB.DEMO.MARKETS_DESK_AGENT
  COMMENT = 'Answers a markets desk''s historical questions using a small 2024 public-data sample. Not an investment adviser, forecasting service, or live market feed.'
  PROFILE = '{"display_name": "Markets Desk Assistant"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  instructions:
    orchestration: |
      Use EQUITY_MARKET_SV for equity prices and Nasdaq trading volume.
      Use MORTGAGE_MARKET_SV for national fixed mortgage-rate observations.
      Use the tools for data-backed answers; do not supply numbers from memory.

      Ask for clarification when a rate question does not identify the mortgage
      term. Keep different mortgage series and source units in separate groups.
      If a requested calculation, instrument, or date is outside the configured
      data, explain the limitation instead of substituting another measure.

      If a question covers both stocks and mortgage rates, query each tool
      separately, then combine the results in one summary. Attribute each figure
      to its source. Do not infer relationships, correlations, or causes between
      the two topics.
    response: |
      State the measure, period, ticker or mortgage series, and source unit.
      Distinguish a period average from a value at a particular date.
      Report mortgage values exactly as returned with their source unit; do not rescale them.
      Explain missing data without treating it as zero.
      Keep responses concise and do not give investment recommendations.

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "EQUITY_MARKET_SV"
        description: >-
          Use for observed equity prices and Nasdaq trading volume for AAPL, MSFT,
          and AMZN in 2024. Supports average Post-Market Close, also called
          extended-session close in this lab, and total Nasdaq volume.
          Does not answer mortgage-rate, dividend, portfolio-return, or forecast questions.
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "MORTGAGE_MARKET_SV"
        description: >-
          Use for US national 15-year and 30-year fixed mortgage-rate observations
          in 2024. Supports averages over available observations, grouped separately
          by mortgage series and source unit. Does not answer equity-price questions,
          individual loan quotes, regional mortgage rates, or forecasts.

  tool_resources:
    EQUITY_MARKET_SV:
      semantic_view: "SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
    MORTGAGE_MARKET_SV:
      semantic_view: "SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_MARKET_SV"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
  $$;

DESCRIBE AGENT SEMANTIC_VIEWS_LAB.DEMO.MARKETS_DESK_AGENT;

-- ===== Block 14: Troubleshoot and Clean Up > Clean up lab objects (line 533) =====
DROP AGENT IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MARKETS_DESK_AGENT;
DROP SEMANTIC VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV;
DROP SEMANTIC VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_MARKET_SV;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES;
