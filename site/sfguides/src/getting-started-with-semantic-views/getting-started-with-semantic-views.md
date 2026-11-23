author: Reinout Korbee
id: getting-started-with-semantic-views
language: en
summary: Build semantic views over public Marketplace data with SQL, review their business meaning, and connect them to a Cortex Agent.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# Getting Started with Semantic Views and Cortex Agents

## Overview

A semantic view is an agreement about what the business means. Someone still needs to decide whether a price should be averaged, whether two terms mean the same thing, and which questions the model should answer. Generating the definition is the easy part; reviewing it is the work.

In this guide, you start with public data from Snowflake Marketplace. You create two semantic views, check them against hand-written SQL, refine their vocabulary and instructions, and connect both to a Cortex Agent through Cortex Analyst tools. 

**This guide uses SQL for every step.** Snowflake also offers other ways to do most of this work: Semantic View Autopilot and Semantic Studio in Snowsight for semantic views, the Snowsight agent editor for agents, and Cortex Code skills that generate definitions from a prompt. They produce the same objects. This guide mentions them where they apply but doesn't walk through them. SQL definitions are explicit, reviewable in a diff, and easy to put under version control.

Building AI-powered Business Intelligence apps on top of semantic views is covered in: [Getting Started with Snowflake Semantic View](https://www.snowflake.com/en/developers/guides/snowflake-semantic-view/). This guide contains runnable SQL and all SQL is available in the accompanying [labs.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-semantic-views/assets/lab.sql) file.

### Prerequisites

- Comfort writing SQL, including joins and aggregates.
- A Snowflake account with access to Cortex Analyst and Cortex Agents.
- An administrator who can approve Marketplace acquisition and provision the lab privileges if you cannot do so yourself.

### What You'll Learn

- Scope a semantic view around a persona and a set of questions.
- Write semantic views with `CREATE SEMANTIC VIEW` and refine them with `CREATE OR ALTER`.
- Add synonyms, SQL generation instructions, and verified queries.
- Check semantic view results against reference SQL.
- Create an agent with two Cortex Analyst tools using `CREATE AGENT`.

### What You'll Need

- A SQL worksheet in Snowsight, or the [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation).
- Access to [Snowflake Curated Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255).
- An existing, approved warehouse for the exercises.
- A lab role with access to the imported data and permission to create a database, or a dedicated database provisioned by an administrator.

The lab role needs `USAGE` on the warehouse and the lab database and schema, plus `CREATE VIEW`, `CREATE SEMANTIC VIEW`, and `CREATE AGENT` on the lab schema, and the appropriate Cortex feature access. It also needs read access to the source data. See [Cortex Agent access control](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-setup).

Do not change account-wide AI settings for this exercise without administrator approval. Model availability and any cross-region inference settings must meet your organization's requirements.

> The listing has no data subscription charge under its free tier, but warehouse queries and Cortex services incur charges. The free listing has a three-month data lag; this guide deliberately uses a historical period.

### What You'll Build

- Three small SQL views that scope the public source data without copying it.
- `EQUITY_MARKET_SV` and `MORTGAGE_MARKET_SV`, two semantic views written in SQL.
- `MARKETS_DESK_AGENT`, with one Cortex Analyst tool per semantic view.

## Define the Questions

Your persona is a **financial news writer** on a markets desk, looking back at 2024. The writer covers two beats: big tech stocks and borrowing costs. They need accurate historical figures, not investment recommendations or forecasts.

The two beats produce different questions, so each gets its own semantic view. This is the scoping rule to take away: keep data in one semantic view when the persona's questions combine it, and split where the questions split.

| Topic | Questions it answers | Questions it does not answer |
|---|---|---|
| Equity market | Observed stock prices and Nasdaq trading volume for AAPL, MSFT, and AMZN during 2024 | Portfolio returns, dividends, buy/sell recommendations, mortgage rates |
| Mortgage market | US national 15-year and 30-year fixed mortgage-rate observations during 2024 | Individual loan quotes, regional rates, stock prices |

Use these questions to guide the build:

1. What was AAPL's average post-market closing price in January 2024?
2. What was MSFT's total Nasdaq trading volume in January 2024?
3. Show the monthly average 30-year fixed mortgage rate for 2024, including its source unit.
4. Compare the average 15-year and 30-year fixed mortgage rates in January 2024, keeping each series separate.
5. What was the average rate in January 2024?

The fifth question is deliberately ambiguous. The desired behaviour is to ask which mortgage term the user means, rather than invent a default.

Sometimes the writer wants a recap that covers both beats. The agent can answer that by querying each semantic view separately and combining the results in one response. It does not join the two views, so questions that need row-level alignment between them, such as "how did stocks move in the weeks when rates rose", belong in a single semantic view instead.

A **semantic view** defines business meaning. **Cortex Analyst** uses that meaning to generate SQL from a question. The **agent** chooses tools and presents their results. These are separate responsibilities.

## Get Public Data

### Acquire the listing

Your role needs `CREATE DATABASE` and `IMPORT SHARE`, or you can use `ACCOUNTADMIN`. Run the commands as a person user whose profile includes a first name, last name, and email address. You can also get the listing from its [Marketplace page](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255) in Snowsight.

```sql
-- Check that the listing is available in your region (is_ready_for_import = TRUE).
DESCRIBE AVAILABLE LISTING GZTSZ290BV255;

-- Only if is_ready_for_import is FALSE: request the listing and wait for it.
CALL SYSTEM$REQUEST_LISTING_AND_WAIT('GZTSZ290BV255');

-- Accept the listing terms, then create the imported database.
CALL SYSTEM$ACCEPT_LEGAL_TERMS('DATA_EXCHANGE_LISTING', 'GZTSZ290BV255');
CREATE DATABASE SNOWFLAKE_PUBLIC_DATA_FREE FROM LISTING 'GZTSZ290BV255';
```

Review the listing terms before you accept them. If accepting the terms with SQL fails, accept them on the listing page in Snowsight, then run the `CREATE DATABASE` statement. If your account already has the listing under another database name, replace `SNOWFLAKE_PUBLIC_DATA_FREE` consistently in the SQL below. See [Manage listings with SQL as a consumer](https://docs.snowflake.com/en/collaboration/consumer-listings-progaccess-examples).

If another role created the database, grant `IMPORTED PRIVILEGES` on it to your lab role. Do not create lab objects inside the imported database. It contains provider-managed, read-only data.

Confirm the schema and object names:

```sql
SHOW VIEWS IN SCHEMA SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE;
```

The source objects used in this guide are:

- `STOCK_PRICE_TIMESERIES`: dated price and trading-volume observations.
- `FREDDIE_MAC_HOUSING_TIMESERIES`: dated housing and mortgage observations.
- `FREDDIE_MAC_HOUSING_ATTRIBUTES`: definitions and attributes for those housing variables.

The provider documents the [stock data](https://data-docs.snowflake.com/sources/stocks) and [Freddie Mac data](https://data-docs.snowflake.com/sources/freddie-mac).

### Prepare the lab schema

```sql
SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(), CURRENT_WAREHOUSE();

CREATE DATABASE SEMANTIC_VIEWS_LAB;
CREATE SCHEMA SEMANTIC_VIEWS_LAB.DEMO;
USE SCHEMA SEMANTIC_VIEWS_LAB.DEMO;
```

These statements intentionally do not replace existing objects. If the database name is already taken, choose a unique lab name and update all subsequent SQL. If an administrator provisioned the database and schema, skip the two `CREATE` statements but keep the `USE SCHEMA`.

### Scope the source data

Public time-series datasets often store different measures in a shared `VALUE` column. A price, a volume, and an interest rate are not interchangeable just because they are numeric.

Create three small SQL views to keep the exercise focused. These views filter and select columns; they do not copy the data.

```sql
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
```

Preview the selected data:

```sql
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
```

**Checkpoint:** Both queries return data. Look closely at the mortgage rows: the `UNIT` column says `Percent`, but the values are fractions, such as `0.066` for a 6.6% rate. The guide keeps the source values as they are and makes sure every answer reports them with their unit. Don't rescale them based on magnitude alone. The mortgage series is weekly, so a monthly average is an average of about four observations.

## Create the Equity View

Start with a single logical table. Relationships come in the second view.

### Write the definition

```sql
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
```

The building blocks are:

| Clause | Purpose in this example |
|---|---|
| `TABLES` | Maps the logical table `equity` to the scoped SQL view |
| `FACTS` | Row-level values that metrics are built from |
| `DIMENSIONS` | Ticker, trading date, and the source series name |
| `METRICS` | Aggregations, each limited to one series |
| `COMMENT` and `WITH SYNONYMS` | Business meaning and approved alternative terms; Cortex Analyst reads them |

The conditional `CASE` expressions are the important design decision. The source stores prices and volumes in the same `VALUE` column, so a plain `AVG(VALUE)` would average prices with share counts. Each metric includes only its own series.

Semantic View Autopilot can generate a first draft like this from a table and a business description, and a Cortex Code skill can write one from a prompt. Either way, review the definition against the points above before you rely on it.

### Check it against reference SQL

A semantic view that deploys is syntactically valid. That doesn't make its calculations right. Compare a metric with SQL you wrote by hand:

```sql
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
```

**Checkpoint:** Both rows show the same value. If they differ, inspect the metric expression and filters before continuing. Record the value as your reference answer for this run of the lab; historical data can be revised, so the guide doesn't hard-code it.

## Refine the Equity View

`CREATE OR ALTER SEMANTIC VIEW` changes an existing semantic view to match the statement. Any property you leave out is removed, so always submit the complete definition.

### Add vocabulary and a verified query

For this exercise, the desk uses **extended-session close** to mean the provider's **Post-Market Close** series. This is a lab vocabulary decision, not a universal industry definition, so it goes into the metric as a synonym and its comment explains exactly what it means.

You also add a **verified query**: a question paired with SQL that you have checked. Cortex Analyst uses verified queries as examples when generating SQL, and when a question matches one exactly, the agent runs its SQL directly. In verified-query SQL, refer to a logical table by its name with a double-underscore prefix, such as `__equity`.

```sql
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
```

A synonym changes vocabulary, not the formula. If two terms mean different calculations, define separate metrics instead. Add synonyms only for terms your users actually use; a long generated list makes matching less precise, not more.

### Review the stored definition

Read the definition back as YAML to confirm what Snowflake stored:

```sql
SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW(
    'SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV'
) AS SEMANTIC_VIEW_YAML;
```

Check that the synonym, the updated comments, and the verified query are present. The YAML form is useful for reviews and for tools that work with YAML; Semantic Studio in Snowsight shows the same definition visually. This guide keeps the SQL statement as the source of truth.

### Keep filters explicit

The source SQL views enforce the lab's ticker, geography, and 2024 boundaries. The conditional metric expressions enforce which series contributes to each metric. Question-specific date filters further narrow the scope.

Do not assume that a comment or an instruction restricts every query. Comments and instructions guide Cortex Analyst; they are not constraints or security controls. Inspect generated SQL to confirm that the required predicates are present.

## Add the Mortgage View

The second topic is mortgage rates. Here the observations join to series descriptions, which gives you a relationship to review.

### Check the join key

A relationship assumes that the referenced key is unique. Check it before declaring it. This query must return no rows:

```sql
SELECT VARIABLE, COUNT(*) AS ROW_COUNT
FROM SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES
GROUP BY VARIABLE
HAVING VARIABLE IS NULL OR COUNT(*) > 1;
```

If it returns rows, joining would duplicate observations. Fix the source view rather than hiding duplicates with `DISTINCT`.

### Write the definition

```sql
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
```

Three things to review:

- **The relationship** joins observations to variables on the `VARIABLE` key, not on the human-readable name. Each observation matches exactly one series row, which the key check confirmed.
- **The metric** is a plain `AVG(VALUE)`. It is only meaningful per series and unit, which is why the comment says so.
- **`AI_SQL_GENERATION`** gives Cortex Analyst instructions that apply to every question on this view. Here it handles the ambiguous "rate" question and protects against mixing the two series.

### Check the second view

```sql
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
```

**Checkpoint:** Both queries return two rows, one per series, with matching values and units.

## Create the Agent

The agent receives a question, decides which tool to call, and writes the answer. Each Cortex Analyst tool points to one semantic view. Tool descriptions drive tool choice, so make each one say what the tool covers and what it doesn't.

Replace `COMPUTE_WH` with your approved warehouse. You can also build or edit the same agent in the Snowsight agent editor.

```sql
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
```

The specification has three parts:

- **`instructions.orchestration`** guides planning: which tool to use, when to ask for clarification, and how to handle questions that span both topics.
- **`instructions.response`** guides how the answer is written.
- **`tools` and `tool_resources`** declare each Cortex Analyst tool and connect it to its semantic view and warehouse.

These instructions guide behaviour; they don't replace access controls or testing. See [Create and manage agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage) for the full specification format.

**Checkpoint:** `DESCRIBE AGENT` shows both tools and their semantic views. You can ask the agent questions in the Snowsight agent playground, or with SQL through `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`.

## Troubleshoot and Clean Up

### Troubleshooting

| Symptom | Check |
|---|---|
| The listing cannot be acquired | Role privileges, user profile details, listing availability, and terms |
| A source query returns no rows | Imported database and schema names, series names, and historical coverage |
| `CREATE SEMANTIC VIEW` fails | Clause order (`FACTS` before `DIMENSIONS`), logical table names, and doubled single quotes inside string literals |
| A metric looks inflated | Mixed series, duplicate keys in a referenced table, or an incorrect relationship |
| Mortgage rates look 100 times too small | The source stores fractions with unit `Percent`; report values as returned with their unit |
| The agent selects the wrong tool | Make tool descriptions more distinct and retest |
| The agent reports an inaccessible tool | The caller's role, warehouse access, semantic view access, and underlying data privileges |

### Clean up lab objects

Run the following only if you created these objects for this lab and no longer need them:

```sql
DROP AGENT IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MARKETS_DESK_AGENT;
DROP SEMANTIC VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_MARKET_SV;
DROP SEMANTIC VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_MARKET_SV;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.EQUITY_OBSERVATIONS;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_OBSERVATIONS;
DROP VIEW IF EXISTS SEMANTIC_VIEWS_LAB.DEMO.MORTGAGE_VARIABLES;
```

Ask the database owner to remove the lab schema and database if they contain no other work. Do not drop the imported Marketplace database or a shared warehouse as part of this cleanup.

## Conclusion And Resources

You now have two semantic views with reviewed business meaning, and an agent that chooses between them and combines their results when a question spans both. All of it is defined in SQL you can review and version.

### What You Learned

- Start with a persona's questions and scope, not with every available table.
- Split semantic views where the questions split.
- Write semantic views in SQL, and keep each metric limited to the data it describes.
- Check semantic view results against hand-written reference SQL.
- Add synonyms, SQL generation instructions, and verified queries deliberately.
- Connect semantic views to an agent as Cortex Analyst tools with `CREATE AGENT`.

Next, adapt the question set to one domain in your own organisation. When you're ready to measure answer quality systematically, see Cortex Analyst and [Cortex Agent evaluations](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-agent-evaluations/).

### Related Resources

- [CREATE SEMANTIC VIEW](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Best practices for modelling semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-modeling)
- [Querying semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/querying)
- [Create and manage Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [Cortex Analyst evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst-evaluations)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Developing and deploying semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-dev)
- [Semantic View Autopilot](https://docs.snowflake.com/en/user-guide/views-semantic/autopilot)
- [Snowflake Public Data documentation](https://data-docs.snowflake.com/)
