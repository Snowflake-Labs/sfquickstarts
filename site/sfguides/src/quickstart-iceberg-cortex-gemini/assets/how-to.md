# How-To

Code cells + brief but effective UI pointers, section by section. Follows ./narration.md.


## Setup

Three environments:
- **Snowflake** — register at https://go.dataops.live/snowflake-and-gemini-workshop → log in with given credentials.
- **GCP** — open https://explore.qwiklabs.com for GCS bucket and Gemini Enterprise.
- **Looker** — open <provided in lab> for dashboard creation.

## Workspaceƒ

We create a git integration and then a new workspace connected to our git repo.

```sql
use accountadmin;
CREATE OR REPLACE API INTEGRATION github_api_integration
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-akhosro/')
  ENABLED = TRUE;

GRANT USAGE ON INTEGRATION github_api_integration TO ROLE ATTENDEE_ROLE;
```

**UI-Snowsight**:
- Go to Projects > Workspaces
- Select From Git repository
- Paste: https://github.com/sfc-gh-akhosro/gcp-snowflake-solutions.git
- Select github_api_integration from the API Integration dropdown
- Choose Public repository as the authentication method
- Select Create

- Open `hands-on-lab-cortex-gemini/hol-cortex-gemini.ipynb`. Click "Connected" to start a notebook service (accept defaults). It might take a few minutes to start a service, please do it right away while reviewing the course.

Open a second browser tab at the same Snowflake instance URL for exploring components. In this tab find Marketplace, Cortex Analyst, Agents, AI Functions, dbt Projects, Database Explorer, and Workspaces.

## RBAC

Two roles:
- **`hol_role`** — runs notebook, owns resources.
- **`end_user_role`** — CoWork and Gemini Enterprise end user.


```sql
USE ROLE ACCOUNTADMIN;

-- Create a warehouse for this lab (guaranteed to exist)
CREATE WAREHOUSE IF NOT EXISTS hol_wh
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE hol_wh;

-- Builder role: owns all workshop objects
CREATE ROLE IF NOT EXISTS hol_role;

-- Consumer role: can only use the agent (CoWork, Gemini Enterprise)
CREATE ROLE IF NOT EXISTS end_user_role;

-- Grant both roles to whoever is running this notebook
BEGIN
  LET usr := CURRENT_USER();
  EXECUTE IMMEDIATE 'GRANT ROLE hol_role TO USER ' || :usr;
  EXECUTE IMMEDIATE 'GRANT ROLE end_user_role TO USER ' || :usr;
END;

-- Builder privileges
GRANT CREATE DATABASE        ON ACCOUNT TO ROLE hol_role;
GRANT CREATE WAREHOUSE       ON ACCOUNT TO ROLE hol_role;
GRANT CREATE INTEGRATION     ON ACCOUNT TO ROLE hol_role;
GRANT CREATE EXTERNAL VOLUME ON ACCOUNT TO ROLE hol_role;
GRANT OWNERSHIP ON WAREHOUSE hol_wh TO ROLE hol_role COPY CURRENT GRANTS;

-- Cortex access for both roles
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE hol_role;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE end_user_role;

-- Switch to hol_role to build
USE ROLE hol_role;
USE WAREHOUSE hol_wh;

CREATE DATABASE IF NOT EXISTS hol_db;
USE SCHEMA hol_db.public;

-- Schema-level privileges (must come after database/schema exist)
USE ROLE ACCOUNTADMIN;
GRANT CREATE SEMANTIC VIEW ON SCHEMA hol_db.public TO ROLE hol_role;
USE ROLE hol_role;
USE WAREHOUSE hol_wh;
USE SCHEMA hol_db.public;

-- Grant consumer role usage on warehouse and database
GRANT USAGE ON WAREHOUSE hol_wh TO ROLE end_user_role;
GRANT USAGE ON DATABASE hol_db TO ROLE end_user_role;
GRANT USAGE ON SCHEMA hol_db.public TO ROLE end_user_role;

-- Verify context
SELECT CURRENT_ROLE() AS role, CURRENT_WAREHOUSE() AS wh, CURRENT_DATABASE() AS db, CURRENT_SCHEMA() AS schema;
```


## Marketplace

**UI-Snowsight**: Data Products → Marketplace → search "Snowflake Public Data" → **Get** (free).
- Database name: `SNOWFLAKE_PUBLIC_DATA_FREE` (accept default options and dont change them).

- direct links: https://app.snowflake.com/marketplace/listing/GZTSZ290BV255/snowflake-public-data-products-snowflake-public-data-free

```sql
-- Verify marketplace data access
SELECT 'BLS_PRICE' AS source, COUNT(*) AS row_count FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
UNION ALL
SELECT 'BLS_EMPLOYMENT', COUNT(*) FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
UNION ALL
SELECT 'FREDDIE_MAC', COUNT(*) FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
UNION ALL
SELECT 'IRS_INCOME', COUNT(*) FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.IRS_INDIVIDUAL_INCOME_TIMESERIES;
```


## GCS Bucket for Iceberg

**UI-GCP**: Google Cloud Console → Cloud Storage → **Create Bucket**.
- Name: `firstname_lastname_hol_0729`
- Location: `Multi-region`
- Leave everything else as default.

```sql
-- Create an external volume pointing to the shared GCS bucket
CREATE OR REPLACE EXTERNAL VOLUME hol_gcs_vol
  STORAGE_LOCATIONS = ((
    NAME = 'hol-gcs'
    STORAGE_PROVIDER = 'GCS'
    STORAGE_BASE_URL = 'gcs://hands-on-lab-cortex-gemini/iceberg/'
  ));

-- Describe to get storage config, capture query ID immediately
DESCRIBE EXTERNAL VOLUME hol_gcs_vol;
SET desc_qid = LAST_QUERY_ID();

-- Extract the GCS service account using Snowflake JSON parsing
-- PARSE_JSON converts the stored JSON string → dot notation pulls the exact field
SELECT
  PARSE_JSON("property_value"):STORAGE_GCP_SERVICE_ACCOUNT::STRING
    AS gcs_service_account_to_grant
FROM TABLE(RESULT_SCAN($desc_qid))
WHERE "property" = 'STORAGE_LOCATION_1';
```

Copy the printed service account (principal) from above.

**UI-GCP**: Google Cloud Console → your bucket → **Permissions** tab → **Grant Access**.
- Paste the service account you copied.
- Role: **Storage Admin** → Save.

Then plug your bucket name into `STORAGE_BASE_URL` above if different.

## Iceberg Table

```sql
-- Create Iceberg table: join four marketplace sources into one wide-format table
CREATE OR REPLACE ICEBERG TABLE hol_db.public.economic_indicators
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'hol_gcs_vol'
  BASE_LOCATION = 'economic_indicators'
  AS
WITH cpi AS (
  SELECT
    DATE_TRUNC('month', date) AS month,
    AVG(value) AS cpi_index
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES
  WHERE variable_name = 'CPI: All items, Not seasonally adjusted, Monthly'
    AND geo_id = 'country/USA'
  GROUP BY 1
),
mortgage_30yr AS (
  SELECT
    DATE_TRUNC('month', date) AS month,
    ROUND(AVG(value) * 100, 2) AS mortgage_rate_30yr_pct
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
  WHERE variable_name = '30-Year Fixed Rate Mortgage Rate, National Average'
    AND geo_id = 'country/USA'
  GROUP BY 1
),
mortgage_15yr AS (
  SELECT
    DATE_TRUNC('month', date) AS month,
    ROUND(AVG(value) * 100, 2) AS mortgage_rate_15yr_pct
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FREDDIE_MAC_HOUSING_TIMESERIES
  WHERE variable_name = '15-Year Fixed Rate Mortgage Rate, National Average'
    AND geo_id = 'country/USA'
  GROUP BY 1
),
unemployment AS (
  SELECT
    DATE_TRUNC('month', date) AS month,
    geo_id,
    AVG(value) AS unemployment_rate_pct
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES
  WHERE variable_name = 'Local Area Unemployment: Unemployment Rate, Not seasonally adjusted, Monthly'
    AND LENGTH(geo_id) = 8
  GROUP BY 1, 2
),
national_unemployment AS (
  SELECT month, ROUND(AVG(unemployment_rate_pct), 2) AS unemployment_rate_pct
  FROM unemployment
  GROUP BY 1
),
income_raw AS (
  SELECT
    agi.geo_id,
    YEAR(agi.date) AS yr,
    ROUND(agi.value / NULLIF(ret.value, 0), 0) AS avg_income_per_return
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.IRS_INDIVIDUAL_INCOME_TIMESERIES agi
  JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.IRS_INDIVIDUAL_INCOME_TIMESERIES ret
    ON agi.geo_id = ret.geo_id AND agi.date = ret.date
  WHERE agi.variable_name = 'Adjusted gross income (AGI), AGI bin: Total'
    AND ret.variable_name = 'Number of returns, AGI bin: Total'
    AND LENGTH(agi.geo_id) = 8
),
income_indexed AS (
  SELECT
    geo_id,
    yr,
    avg_income_per_return,
    ROUND((avg_income_per_return / FIRST_VALUE(avg_income_per_return) OVER (PARTITION BY geo_id ORDER BY yr)) * 100, 1) AS income_index
  FROM income_raw
),
national_income AS (
  SELECT yr, ROUND(AVG(income_index), 1) AS income_index
  FROM income_indexed
  GROUP BY 1
),
geo AS (
  SELECT geo_id, geo_name
  FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX
  WHERE level = 'State'
),
national AS (
  SELECT
    c.month AS date,
    'country/USA' AS geo_id,
    'United States' AS geo_name,
    ROUND(c.cpi_index, 2) AS cpi_index,
    ROUND(((c.cpi_index - LAG(c.cpi_index, 12) OVER (ORDER BY c.month))
      / NULLIF(LAG(c.cpi_index, 12) OVER (ORDER BY c.month), 0)) * 100, 2) AS inflation_pct,
    m30.mortgage_rate_30yr_pct,
    m15.mortgage_rate_15yr_pct,
    nu.unemployment_rate_pct,
    ni.income_index
  FROM cpi c
  LEFT JOIN mortgage_30yr m30 ON c.month = m30.month
  LEFT JOIN mortgage_15yr m15 ON c.month = m15.month
  LEFT JOIN national_unemployment nu ON c.month = nu.month
  LEFT JOIN national_income ni ON YEAR(c.month) = ni.yr
),
states AS (
  SELECT
    u.month AS date,
    u.geo_id,
    g.geo_name,
    NULL::FLOAT AS cpi_index,
    NULL::FLOAT AS inflation_pct,
    NULL::FLOAT AS mortgage_rate_30yr_pct,
    NULL::FLOAT AS mortgage_rate_15yr_pct,
    u.unemployment_rate_pct,
    ii.income_index
  FROM unemployment u
  JOIN geo g ON u.geo_id = g.geo_id
  LEFT JOIN income_indexed ii ON u.geo_id = ii.geo_id AND YEAR(u.month) = ii.yr
)
SELECT * FROM national
UNION ALL
SELECT * FROM states
ORDER BY date, geo_id;
```



## Data Profiling

**UI-Snowsight**: After running the query, explore the cell output:
- Click **Chart** tab to visualize trends over time.
- Click **Query Profile** tab to see the execution plan.
- Click column headers for quick profiling stats (min, max, distribution).

```sql
-- Compare CPI index growth vs income index growth (national)
-- If income_index < cpi_index, purchasing power is shrinking
SELECT
  date,
  cpi_index,
  income_index,
  inflation_pct,
  mortgage_rate_30yr_pct,
  unemployment_rate_pct
FROM hol_db.public.economic_indicators
WHERE geo_id = 'country/USA'
  AND date >= '2015-01-01'
  AND inflation_pct IS NOT NULL
ORDER BY date;
```



## Semantic View (Cortex Analyst)

**UI-Snowsight**: AI & ML → Cortex Analyst → **Create Semantic View**.
- Select table: `HOL_DB.PUBLIC.ECONOMIC_INDICATORS`.
- Click **Autopilot** to auto-generate dimensions, facts, and metrics from the table schema.
- Review the generated YAML — check that dimensions (DATE, GEO_ID, GEO_NAME), facts (CPI_INDEX, INFLATION_PCT, etc.), and metrics are correct.
- Add or edit descriptions to clarify business meaning.
- Optionally add verified queries (known-good question → SQL pairs).
- Save as `economic_semantic_view`.

In this lab we create it via code (YAML below), but Autopilot is the fastest way to get started.

```sql
-- Create the semantic view using YAML specification
CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  'hol_db.public',
  $$
name: economic_semantic_view
tables:
  - name: economic_indicators
    base_table:
      database: HOL_DB
      schema: PUBLIC
      table: ECONOMIC_INDICATORS
    dimensions:
      - name: DATE
        description: "Date of the observation"
        expr: economic_indicators.DATE
        data_type: DATE
      - name: GEO_ID
        description: "Geographic area identifier"
        expr: economic_indicators.GEO_ID
        data_type: TEXT
      - name: GEO_NAME
        description: "Geographic area — United States for national, or state name (e.g. California)"
        expr: economic_indicators.GEO_NAME
        data_type: TEXT
    facts:
      - name: CPI_INDEX
        description: "Consumer Price Index, base period 1982-84 = 100 (national only)"
        expr: economic_indicators.CPI_INDEX
        data_type: NUMBER
      - name: INFLATION_PCT
        description: "Year-over-year inflation rate as percent (national only)"
        expr: economic_indicators.INFLATION_PCT
        data_type: NUMBER
      - name: MORTGAGE_RATE_30YR_PCT
        description: "30-year fixed mortgage rate, national average, percent (national only)"
        expr: economic_indicators.MORTGAGE_RATE_30YR_PCT
        data_type: NUMBER
      - name: MORTGAGE_RATE_15YR_PCT
        description: "15-year fixed mortgage rate, national average, percent (national only)"
        expr: economic_indicators.MORTGAGE_RATE_15YR_PCT
        data_type: NUMBER
      - name: UNEMPLOYMENT_RATE_PCT
        description: "Unemployment rate as percent (available national and by state)"
        expr: economic_indicators.UNEMPLOYMENT_RATE_PCT
        data_type: NUMBER
      - name: INCOME_INDEX
        description: "Average income per tax return, indexed to earliest available year = 100. Compare to CPI_INDEX to assess purchasing power. (available national and by state, annual grain)"
        expr: economic_indicators.INCOME_INDEX
        data_type: NUMBER
    metrics:
      - name: AVG_CPI_INDEX
        description: "Average Consumer Price Index"
        expr: AVG(economic_indicators.CPI_INDEX)
      - name: AVG_INFLATION_PCT
        description: "Average year-over-year inflation rate"
        expr: AVG(economic_indicators.INFLATION_PCT)
      - name: AVG_MORTGAGE_RATE_30YR
        description: "Average 30-year fixed mortgage rate"
        expr: AVG(economic_indicators.MORTGAGE_RATE_30YR_PCT)
      - name: AVG_UNEMPLOYMENT_RATE
        description: "Average unemployment rate"
        expr: AVG(economic_indicators.UNEMPLOYMENT_RATE_PCT)
      - name: AVG_INCOME_INDEX
        description: "Average income index"
        expr: AVG(economic_indicators.INCOME_INDEX)
$$
);

-- Confirm the semantic view exists
SHOW SEMANTIC VIEWS IN SCHEMA hol_db.public;
```


## Cortex Agent

**UI-Snowsight**: AI & ML → Cortex Agents → **+ Create**.
- Name: `hol_economic_agent`
- Model: change to **Gemini** (default may be different).
- Tools: add Cortex Analyst tool → select `economic_semantic_view`.
- Instructions: describe what the agent does, e.g. "Answer questions about US economic indicators including inflation, mortgage rates, unemployment by state, and income trends."
- Warehouse: `hol_wh` (for query execution).
- Test the agent in the preview pane before saving.

In this lab we create it via SQL for reproducibility.

```sql
-- Create a Cortex Agent backed by the economic indicators semantic view
CREATE OR REPLACE AGENT hol_db.public.hol_economic_agent
  FROM SPECIFICATION $$
  tools:
    - tool_spec:
        type: cortex_analyst_text_to_sql
        name: economic_analyst
        description: "Answers questions about US economic indicators: CPI/inflation, mortgage interest rates (30-year, 15-year), unemployment rate (national and by state), and income index."

  tool_resources:
    economic_analyst:
      semantic_view: HOL_DB.PUBLIC.ECONOMIC_SEMANTIC_VIEW
      execution_environment:
        type: warehouse
        warehouse: HOL_WH
  $$;

-- Grant consumer role usage on the agent
GRANT USAGE ON AGENT hol_db.public.hol_economic_agent TO ROLE end_user_role;
GRANT SELECT ON SEMANTIC VIEW hol_db.public.economic_semantic_view TO ROLE end_user_role;
GRANT SELECT ON TABLE hol_db.public.economic_indicators TO ROLE end_user_role;

-- Verify the agent is created
SHOW AGENTS IN SCHEMA hol_db.public;
```


## CoWork

**UI-Snowsight**: AI & ML → Open Snowflake CoWork.
- In CoWork, go to bottom left profile, click setting, and switch role to `end_user_role`, warehouse: `hol_wh`. Done.
- You should be able to see **hol_economic_agent** in the agent list (control buttons of the CoWork chat).
- Ask: "How has the 30-year mortgage rate changed relative to inflation since 2020?"

Look at the response — it includes the generated SQL so you can see exactly what query was executed. Same agent, same data, different role — a chat-based surface instead of a notebook.


## MCP Server

```sql
-- MCP server exposing the Cortex Agent as a tool (requires schema ownership → hol_role)
USE ROLE hol_role;
USE WAREHOUSE hol_wh;
USE SCHEMA hol_db.public;

CREATE OR REPLACE MCP SERVER hol_db.public.hol_mcp
  FROM SPECIFICATION $$
  tools:
    - name: "hol-economic-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "HOL_DB.PUBLIC.HOL_ECONOMIC_AGENT"
      description: "US economic indicators agent — answers questions about inflation (CPI), mortgage rates, unemployment, and income."
      title: "Economic Indicators Agent"
  $$;

-- Grant MCP server usage to the consumer role (required for Gemini to discover tools)
-- ALLOWED_ROLES_LIST must include the role used in the OAuth scope, otherwise
-- Snowflake rejects it with "invalid role" even if the user has the role granted.
USE ROLE ACCOUNTADMIN;

GRANT USAGE ON MCP SERVER hol_db.public.hol_mcp TO ROLE end_user_role;

CREATE OR REPLACE SECURITY INTEGRATION hol_mcp_oauth
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://vertexaisearch.cloud.google.com/oauth-redirect'
  ALLOWED_ROLES_LIST = ('END_USER_ROLE')
  ENABLED = TRUE;

-- Get MCP server metadata (database, schema, name)
DESCRIBE MCP SERVER hol_db.public.hol_mcp;
SET mcp_qid = LAST_QUERY_ID();

-- Get OAuth integration metadata (auth URL, token URL, client ID)
DESCRIBE SECURITY INTEGRATION hol_mcp_oauth;
SET int_qid = LAST_QUERY_ID();

USE ROLE hol_role;
USE WAREHOUSE hol_wh;
USE SCHEMA hol_db.public;

-- Retrieve all credentials for Gemini Enterprise MCP connection
-- Values derived from DESCRIBE metadata — nothing hardcoded
WITH mcp_meta AS (
  SELECT "database_name", "schema_name", "name"
  FROM TABLE(RESULT_SCAN($mcp_qid))
),
oauth_meta AS (
  SELECT
    MAX(CASE WHEN "property" = 'OAUTH_AUTHORIZATION_ENDPOINT' THEN "property_value" END) AS auth_endpoint,
    MAX(CASE WHEN "property" = 'OAUTH_TOKEN_ENDPOINT' THEN "property_value" END) AS token_endpoint,
    MAX(CASE WHEN "property" = 'OAUTH_CLIENT_ID' THEN "property_value" END) AS client_id
  FROM TABLE(RESULT_SCAN($int_qid))
),
secrets AS (
  SELECT PARSE_JSON(SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('HOL_MCP_OAUTH')) AS s
),
account_base AS (
  -- Org-account URL format (required by Gemini Enterprise)
  SELECT 'https://' || CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
         || '.snowflakecomputing.com' AS url
)
SELECT field_name, value
FROM (
  SELECT 1 AS ord, 'MCP Server URL' AS field_name,
    ab.url || '/api/v2/databases/' || m."database_name" || '/schemas/' || m."schema_name" || '/mcp-servers/' || m."name" AS value
    FROM account_base ab, mcp_meta m
  UNION ALL
  SELECT 2, 'Auth URL', o.auth_endpoint FROM oauth_meta o
  UNION ALL
  SELECT 3, 'Auth URL Params', '' FROM oauth_meta o
  UNION ALL
  SELECT 4, 'Token URL', o.token_endpoint FROM oauth_meta o
  UNION ALL
  SELECT 5, 'Client ID', o.client_id FROM oauth_meta o
  UNION ALL
  SELECT 6, 'Client Secret', s.s:OAUTH_CLIENT_SECRET::STRING FROM secrets s
  UNION ALL
  SELECT 7, 'Scopes', 'session:role:end_user_role' FROM secrets s
  UNION ALL
  SELECT 8, 'MCP Server Description', 'Snowflake Cortex Agent for US economic indicators (CPI, mortgage rates, unemployment, income)' FROM secrets s
  UNION ALL
  SELECT 9, 'Agent Instructions', 'Use the hol-economic-agent tool to answer questions about US economic data including inflation, mortgage rates, unemployment by state, and income trends.' FROM secrets s
  UNION ALL
  SELECT 10, 'Data Connector Name', 'hol_cortex_gemini_economic_agent' FROM secrets s
)
ORDER BY ord;
```


## Gemini Enterprise

**UI-GCP**: Google Cloud Console → search "Gemini Enterprise" → Data stores → **+Create data store** → Add MCP Server.
- Fill in the fields using values from the MCP output above (server URL, client ID, client secret, scopes, etc.).
- Complete the OAuth authorization flow when prompted.
- Click **Actions** and then "Reload Custom Actions" and log in with your workshop provided account.
- Select the tool "hol-economic-agent" and then "Enable Actions" and confirm.

Now open Gemini Enterprise chat and ask the same question:

"How has the 30-year mortgage rate changed relative to inflation since 2020?"

You should get the same grounded answer — this time served through Google Cloud's corporate AI assistant.


## Looker
Please follow [Looker instructions](https://docs.google.com/document/d/14DwWTrCz4YLreXNiYfJ3cI86MUNT44lj_yXlIq__pwg/edit?usp=sharing&resourcekey=0-s31XT4gARcUOk4CX6ZYWvw)

We would like to:
- Log in to looker (given account, username, password)
- Create a secure connection to your Snowflake account
- Create a project and database and ecplore Looker
- Get familiar with LookML (which define the semantic model of your data)
- Talk to your Snowflake data 

## Troubleshooting

```sql
-- Temporarily disable account network policy to allow Gemini Enterprise OAuth
USE ROLE ACCOUNTADMIN;
ALTER ACCOUNT UNSET NETWORK_POLICY;

-- To re-enable later:
-- ALTER ACCOUNT SET NETWORK_POLICY = <your_policy_name>;
```

If org policy blocks MCP connector:

**UI-GCP**: IAM & Admin → Organization Policies → search `disableCustomMcpServerConnector` → Enforcement: **Off** → Save. Retry connector setup.


## Cleanup

```sql
USE ROLE ACCOUNTADMIN;

-- Drop database (cascades all objects inside: tables, views, agents, MCP servers)
DROP DATABASE IF EXISTS hol_db;
DROP WAREHOUSE IF EXISTS hol_wh;
DROP INTEGRATION IF EXISTS hol_mcp_oauth;
DROP ROLE IF EXISTS hol_role;
DROP ROLE IF EXISTS end_user_role;

-- NOTE: hol_gcs_vol is kept — GCS bucket permissions take time to set up
-- To drop it manually: DROP EXTERNAL VOLUME IF EXISTS hol_gcs_vol;

-- Re-enable network policy if it was disabled
-- ALTER ACCOUNT SET NETWORK_POLICY = ACCOUNT_VPN_POLICY_SE;

SHOW ROLES LIKE '%HOL%';
```
