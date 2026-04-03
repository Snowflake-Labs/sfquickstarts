author: Jan Sommerfeld, Gilberto Hernandez
id: build-data-pipelines-with-snowflake-dcm-projects
summary: Learn how to split platform infrastructure and data pipelines into separate DCM Projects, deploy them sequentially, and build a medallion-architecture transformation layer.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
environments: web
status: Published
language: en
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/snowflake_dcm_projects

# Build Data Pipelines with Snowflake DCM Projects
<!-- ------------------------ -->
## Overview

In the [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/) guide, you learned the fundamentals of DCM Projects — how to define Snowflake infrastructure as code, use Jinja templating, and plan and deploy changes from Snowsight Workspaces.

In this guide, you'll take that a step further. You'll work with **two separate DCM Projects** that together build a complete data pipeline:

- **DCM_Platform_Demo** — Defines shared platform infrastructure: a database, raw staging tables, an ingestion stage and Task, warehouses, roles, and grants
- **DCM_Pipeline_Demo** — Defines a data transformation pipeline on top of the platform: silver-layer Dynamic Tables, gold-layer fact tables and views, and data quality expectations

By splitting platform infrastructure and data pipelines into separate projects, you get a clean separation of concerns. The Platform project can be owned by a platform team and deployed independently, while the Pipeline project can be owned by a data engineering team that builds transformations on top.

> **Note:** DCM Projects is currently in Public Preview. See the [DCM Projects documentation](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-overview) for the latest details.

### Prerequisites
- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN access (or a role with sufficient privileges)
- Familiarity with DCM Projects concepts (complete [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/) first)

### What You'll Learn
- How to split infrastructure into multiple DCM Projects with different responsibilities
- How to define stage-based data ingestion with Tasks and CRON schedules
- How to build a medallion architecture (silver/gold layers) using Dynamic Tables defined as code
- How to use Jinja macros and loops to create per-team infrastructure (warehouses, roles, grants)
- How to attach data quality expectations across projects
- How to use `post_hook` to run setup commands after deployment

### What You'll Need
- A [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN access
- A Snowsight Workspace linked to the [sample DCM Projects repository](https://github.com/Snowflake-Labs/snowflake_dcm_projects) (created in [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/))

### What You'll Build
- A fully deployed data platform and transformation pipeline consisting of:
  - A shared raw database with 16 staging tables
  - An ingestion stage and scheduled Task for loading CSV data
  - Per-team warehouses, databases, roles, and grants
  - A silver layer of Dynamic Tables that clean, filter, and transform raw data
  - A gold layer of fact tables, views, and aggregate calculations
  - Data quality expectations attached to gold-layer tables

<!-- ------------------------ -->
## Set Up Roles and Permissions

In this step, you'll create a dedicated admin role for managing DCM Projects and grant it the necessary privileges.

If you already have the workspace from [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/), navigate to **Quickstarts/DCM_Project_Quickstart_2** and open the `setup.ipynb` notebook. Otherwise, create a new workspace from the Git repository:

1. In Snowsight, navigate to **Workspaces**.
2. Click **Create** and select **From Git repository**.
3. Enter the repository URL: `https://github.com/snowflake-labs/snowflake_dcm_projects`
4. Select an API Integration for GitHub (create one if needed).
5. Select **Public repository** and click **Create**.

Once the workspace is created, navigate to **Quickstarts/DCM_Project_Quickstart_2** and open the `setup.ipynb` notebook. Connect it to a compute pool so you can run the setup commands step by step.

### Create a DCM Admin Role

Run the following SQL in a Snowsight worksheet or in the setup notebook:

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS dcm_admin;
SET user_name = (SELECT CURRENT_USER());
GRANT ROLE dcm_admin TO USER IDENTIFIER($user_name);
```

### Grant Infrastructure Privileges

The DCM_ADMIN role needs privileges to create infrastructure objects through DCM deployments:

```sql
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE dcm_admin;
GRANT CREATE ROLE ON ACCOUNT TO ROLE dcm_admin;
GRANT CREATE DATABASE ON ACCOUNT TO ROLE dcm_admin;
GRANT EXECUTE MANAGED TASK ON ACCOUNT TO ROLE dcm_admin;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE dcm_admin;

GRANT MANAGE GRANTS ON ACCOUNT TO ROLE dcm_admin;
```

### Grant Data Quality Privileges

To define and test data quality expectations, grant the following:

```sql
GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE dcm_admin;
GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_ADMIN TO ROLE dcm_admin;
GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE dcm_admin;
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE dcm_admin WITH GRANT OPTION;
```

### Create a Warehouse (Optional)

If you don't have a warehouse available, create one. DCM commands are mostly metadata changes, so an X-Small warehouse is sufficient:

```sql
CREATE WAREHOUSE IF NOT EXISTS dcm_wh
WITH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 300
    COMMENT = 'For Quickstart Demo of DCM Projects';
```

<!-- ------------------------ -->
## Explore the Platform Project

Before deploying anything, take a moment to explore the Platform project structure. Navigate to **DCM_Platform_Demo** in the file explorer.

### Manifest

Open `manifest.yml`. The Platform manifest defines two targets (DEV and PROD) and includes several templating variables:

```yaml
manifest_version: 2
type: DCM_PROJECT

default_target: DCM_DEV

targets:
  DCM_DEV:
    account_identifier: MYORG-MY_DEV_ACCOUNT
    project_name: DCM_DEMO.PROJECTS.DCM_PLATFORM_PROJECT_DEV
    project_owner: DCM_DEVELOPER
    templating_config: DEV

  DCM_PROD:
    account_identifier: MYORG-MY_PROD_ACCOUNT
    project_name: DCM_DEMO.PROJECTS.DCM_PLATFORM_PROJECT
    project_owner: DCM_PROD_DEPLOYER
    templating_config: PROD

templating:
  defaults:
    user: "GITHUB_ACTIONS_SERVICE_USER"
    wh_size: "X-SMALL"

  configurations:
    DEV:
      env_suffix: "_DEV"
      user: "INSERT_YOUR_USER"
      ingest_perc: "5"
      teams:
        - name: "Finance"

    PROD:
      env_suffix: ""
      ingest_perc: "100"
      wh_size: "MEDIUM"
      teams:
        - name: "Marketing"
        - name: "Finance"
        - name: "HR"
        - name: "IT"
        - name: "Sales"
        - name: "Research"
        - name: "Design"
```

A few things to notice:

- **`teams`** — DEV has a single team (Finance), while PROD has seven. The Jinja loops in the definition files will create per-team infrastructure for each.
- **`ingest_perc`** — Controls what percentage of sample data to load. DEV uses 5%, PROD uses 100%.
- **`wh_size`** — DEV uses X-Small warehouses, PROD uses Medium.

### Definition Files

The `sources/definitions/` directory contains three SQL files:

| File | What It Defines |
|:-----|:----------------|
| `raw.sql` | Shared database (`DCM_DEMO_2`), RAW schema, and 16 staging tables with change tracking |
| `wh_roles_and_grants.sql` | Per-team warehouses, databases, schemas, roles, and grants using Jinja loops |
| `ingest.sql` | INGEST schema, a stage for CSV files, a scheduled Task for loading data, and a `post_hook` for file format creation |

#### Raw Tables

Open `raw.sql`. This file defines a shared database and 16 staging tables for a financial trading dataset. Each table has `CHANGE_TRACKING = TRUE` and `DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES'` enabled:

```sql
DEFINE DATABASE dcm_demo_2;
DEFINE SCHEMA dcm_demo_2.raw;

DEFINE TABLE dcm_demo_2.raw.account_stg (
    cdc_flag VARCHAR(1) COMMENT 'I OR U DENOTES INSERT OR UPDATE',
    cdc_dsn TIMESTAMP_NTZ(9) COMMENT 'DATABASE SEQUENCE NUMBER',
    ca_id NUMBER(38,0) COMMENT 'CUSTOMER ACCOUNT IDENTIFIER',
    ca_b_id NUMBER(38,0) COMMENT 'IDENTIFIER OF THE MANAGING BROKER',
    ca_c_id NUMBER(38,0) COMMENT 'OWNING CUSTOMER IDENTIFIER',
    ca_name VARCHAR(50) COMMENT 'NAME OF CUSTOMER ACCOUNT',
    ca_tax_st NUMBER(38,0) COMMENT '0, 1 OR 2 TAX STATUS OF THIS ACCOUNT',
    ca_st_id VARCHAR(4) COMMENT 'ACTV OR INAC CUSTOMER STATUS TYPE IDENTIFIER'
)
CHANGE_TRACKING = TRUE
DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';
```

The full file defines tables for accounts, cash transactions, customers, daily market data, dates, finwire records, holding history, HR data, industries, prospects, status types, tax rates, time dimensions, trades, trade history, and watch history.

#### Per-Team Infrastructure

Open `wh_roles_and_grants.sql`. This is where the Jinja `{% for %}` loop creates infrastructure for each team defined in the manifest:

```sql
{% for team in teams %}
    {% set team = team | upper %}
    DEFINE WAREHOUSE dcm_demo_2_{{team}}_wh{{env_suffix}}
        WITH WAREHOUSE_SIZE='{{wh_size}}'
        COMMENT = 'For DCM Demo Quickstart 2';
    DEFINE DATABASE dcm_demo_2_{{team}}{{env_suffix}};
    DEFINE SCHEMA dcm_demo_2_{{team}}{{env_suffix}}.projects;

    {{ create_team_roles(team) }}

    {% if team == 'FINANCE' %}
        GRANT USAGE ON DATABASE dcm_demo_2 TO ROLE dcm_demo_2_{{team}}_admin;
        GRANT USAGE ON SCHEMA dcm_demo_2.raw TO ROLE dcm_demo_2_{{team}}_admin;
        GRANT SELECT ON ALL TABLES IN SCHEMA dcm_demo_2.raw TO ROLE dcm_demo_2_{{team}}_admin;
    {% endif %}

    GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE dcm_demo_2_{{team}}_admin;
    GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE dcm_demo_2_{{team}}_admin;
{% endfor %}
```

For each team, this creates a dedicated warehouse, database, and `PROJECTS` schema. The `{% if team == 'FINANCE' %}` conditional grants the Finance team read access to the shared raw tables — this is what allows the Pipeline project to read from the Platform project's data.

#### Grants Macro

Open `sources/macros/grants_macro.sql`. This reusable macro creates a standard role hierarchy for each team:

```sql
{% macro create_team_roles(team) %}

    DEFINE ROLE dcm_demo_2_{{team}}_admin;
    DEFINE ROLE dcm_demo_2_{{team}}_usage;

    GRANT CREATE SCHEMA ON DATABASE dcm_demo_2_{{team}}{{env_suffix}}
        TO ROLE dcm_demo_2_{{team}}_admin;
    GRANT USAGE ON WAREHOUSE dcm_demo_2_{{team}}_wh{{env_suffix}}
        TO ROLE dcm_demo_2_{{team}}_usage;
    GRANT USAGE ON DATABASE dcm_demo_2_{{team}}{{env_suffix}}
        TO ROLE dcm_demo_2_{{team}}_usage;
    GRANT USAGE ON SCHEMA dcm_demo_2_{{team}}{{env_suffix}}.projects
        TO ROLE dcm_demo_2_{{team}}_usage;
    GRANT CREATE DCM PROJECT ON SCHEMA dcm_demo_2_{{team}}{{env_suffix}}.projects
        TO ROLE dcm_demo_2_{{team}}_admin;

    GRANT ROLE dcm_demo_2_{{team}}_usage TO ROLE dcm_demo_2_{{team}}_admin;
    GRANT ROLE dcm_demo_2_{{team}}_admin TO ROLE {{project_owner_role}};

    {% for user_name in users %}
        GRANT ROLE dcm_demo_2_{{team}}_usage TO USER {{user_name}};
    {% endfor %}
{% endmacro %}
```

Each team gets an `_admin` role (with CREATE permissions) and a `_usage` role (with read access), following a standard role hierarchy pattern where usage rolls up into admin, and admin rolls up into the project owner.

#### Ingestion

Open `ingest.sql`. This file defines the data ingestion infrastructure:

```sql
DEFINE SCHEMA dcm_demo_2.ingest;

DEFINE STAGE dcm_demo_2.ingest.dcm_sample_data
    DIRECTORY = ( ENABLE = TRUE )
    COMMENT = 'for csv files with sample data to demo DCM Pipeline project';

DEFINE TASK dcm_demo_2.ingest.load_new_data
SCHEDULE='USING CRON 15 8-18 * * MON-FRI CET'
COMMENT = 'loading sample data to demo DCM Pipeline project'
AS
BEGIN
    COPY INTO dcm_demo_2.raw.date_stg
    FROM '@dcm_demo_2.ingest.dcm_sample_data/DATE_STG.csv'
    FILE_FORMAT = dcm_demo_2.ingest.csv_format
    ON_ERROR = CONTINUE;

    -- ... similar COPY INTO statements for all 16 staging tables ...

    CALL SYSTEM$SET_RETURN_VALUE('random {{ingest_perc}}% of raw dataset written into all dimension tables');
END;

ATTACH POST_HOOK
AS
[
    CREATE FILE FORMAT IF NOT EXISTS dcm_demo_2.ingest.csv_format
        TYPE = CSV
        COMPRESSION = NONE
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        FIELD_DELIMITER = ','
        NULL_IF = ('NULL', 'null', '')
        EMPTY_FIELD_AS_NULL = TRUE;
];
```

There are two new concepts here that weren't covered in [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/):

- **`SCHEDULE` with CRON** — The Task is configured to run on a schedule (every hour from 8 AM to 6 PM, Monday through Friday). In production, this would automatically ingest new data on a recurring basis.
- **`ATTACH POST_HOOK`** — This is a block of SQL that runs *after* the deployment completes. Here, it creates a file format that the Task's COPY INTO statements depend on. This is useful for setup steps that can't be expressed as `DEFINE` statements.

<!-- ------------------------ -->
## Deploy the Platform Project

Now that you've explored the Platform project files, create the DCM Project object and deploy it.

### Create the DCM Project Object

Run the following in the setup notebook or in a Snowsight worksheet:

```sql
USE ROLE dcm_admin;

CREATE DATABASE IF NOT EXISTS dcm_demo;
CREATE SCHEMA IF NOT EXISTS dcm_demo.projects;

CREATE OR REPLACE DCM PROJECT dcm_demo.projects.dcm_platform_project_dev
    COMMENT = 'for DCM Platform Demo - Quickstart 2';
```

Both the Platform and Pipeline project objects will live in `dcm_demo.projects`. This is a common pattern — use a single schema to house all of your DCM project objects, even when the projects deploy infrastructure to different databases.

### Plan the Deployment

1. In the DCM control panel above the workspace tabs, select the project **DCM_Platform_Demo**.
2. The `DCM_DEV` target should already be selected (it's the default in the manifest).
3. Click on the target profile to verify it uses `DCM_PLATFORM_PROJECT_DEV` and the `DEV` templating configuration.
4. Override the templating value for `user` with your own Snowflake username.

![Selecting the Platform project in the DCM control panel](assets/select_platform_project.png)

Click the play button to the right of **Plan** and wait for the definitions to render, compile, and dry-run.

![Platform project plan results](assets/platform_plan_results.png)

Since none of the defined objects exist yet, the plan will show only **CREATE** statements. You should see planned operations for:

- 1 shared database (`DCM_DEMO_2`) with a RAW schema and 16 staging tables
- 1 team-specific database (`DCM_DEMO_2_FINANCE_DEV`) with a PROJECTS schema
- 1 warehouse (`DCM_DEMO_2_FINANCE_WH_DEV`)
- Roles and grants for the Finance team
- An INGEST schema with a stage and a scheduled Task

### Deploy

1. In the top-right corner of the Plan results tab, click **Deploy**.
2. Optionally, add a **Deployment alias** (e.g., "Initial platform deployment").
3. DCM will create all objects and attach grants using the owner role of the project object.

![Platform deploy dialog](assets/platform_deploy_dialog.png)

Once the deployment completes, refresh the Database Explorer. You should see both `DCM_DEMO_2` (the shared raw database) and `DCM_DEMO_2_FINANCE_DEV` (the Finance team's database).

![Database Explorer showing platform objects](assets/platform_deployed_objects.png)

<!-- ------------------------ -->
## Load Sample Data

The Platform deployment created the table structures, the ingestion stage, and the load Task — but the tables are empty. In this step, you'll upload sample CSV files to the stage and trigger the Task to load data into the raw tables.

### Upload CSV Files to the Stage

The `sample_data/` folder in the workspace contains 17 CSV files. Upload them to the ingestion stage using PUT commands in the setup notebook:

```sql
PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/ACCOUNT_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/CASHTRANSACTION_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/CUSTOMER_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/DAILYMARKET_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/DATE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/FINWIRE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/HOLDINGHISTORY_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/HR_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/INDUSTRY_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/PROSPECT_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/STATUSTYPE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/TAXRATE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/TIME_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/TRADE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/TRADETYPE_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/TRADEHISTORY_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;

PUT file:///home/airflow/workspace_api/Quickstarts/DCM_Project_Quickstart_2/sample_data/WATCH_HISTORY_STG.csv
    @dcm_demo_2.ingest.dcm_sample_data/
    AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
```

### Trigger the Load Task

Verify the files are staged, then manually execute the load Task:

```sql
LIST @dcm_demo_2.ingest.dcm_sample_data;

EXECUTE TASK dcm_demo_2.ingest.load_new_data;
```

### Verify the Data

Check that data has been loaded into the raw tables:

```sql
SELECT COUNT(*) FROM dcm_demo_2.raw.customer_stg;
SELECT COUNT(*) FROM dcm_demo_2.raw.trade_stg;
SELECT COUNT(*) FROM dcm_demo_2.raw.dailymarket_stg;
```

You should see rows in each table. The exact counts depend on the sample data files.

<!-- ------------------------ -->
## Explore the Pipeline Project

With the Platform infrastructure deployed and data loaded, you can now explore the Pipeline project. Navigate to **DCM_Pipeline_Demo** in the file explorer.

### Manifest

Open `manifest.yml`. The Pipeline manifest is simpler than the Platform's — it only needs `env_suffix` and `user`:

```yaml
manifest_version: 2
type: DCM_PROJECT

default_target: DCM_DEV

targets:
  DCM_DEV:
    account_identifier: MYORG-MY_DEV_ACCOUNT
    project_name: DCM_DEMO.PROJECTS.DCM_PIPELINE_PROJECT_DEV
    project_owner: DCM_DEVELOPER
    templating_config: DEV

  DCM_PROD:
    account_identifier: MYORG-MY_PROD_ACCOUNT
    project_name: DCM_DEMO.PROJECTS.DCM_PIPELINE_PROJECT
    project_owner: DCM_PROD_DEPLOYER
    templating_config: PROD

templating:
  defaults:
    user: "GITHUB_ACTIONS_SERVICE_USER"

  configurations:
    DEV:
      env_suffix: "_DEV"
      user: "INSERT_YOUR_USER"

    PROD:
      env_suffix: ""
```

Notice that the Pipeline project points to a different DCM Project object (`DCM_PIPELINE_PROJECT_DEV`) but still lives in the same `DCM_DEMO.PROJECTS` schema. This separation means you can plan and deploy each project independently.

### Definition Files

The `sources/definitions/` directory contains three SQL files that implement a medallion architecture:

| File | What It Defines |
|:-----|:----------------|
| `silver_layer.sql` | SILVER schema and 11 Dynamic Tables that clean, filter, and transform raw data |
| `gold_layer.sql` | GOLD schema with aggregate fact tables, views, and calculations |
| `expectations.sql` | Data quality expectations using Data Metric Functions on gold-layer tables |

#### Silver Layer

Open `silver_layer.sql`. This file defines the SILVER schema inside the Finance team's database and creates Dynamic Tables that transform the raw staging data:

```sql
DEFINE SCHEMA dcm_demo_2_finance{{env_suffix}}.silver;

DEFINE DYNAMIC TABLE dcm_demo_2_finance{{env_suffix}}.silver.finwire_cmp_stg
TARGET_LAG='DOWNSTREAM'
WAREHOUSE='dcm_demo_2_finance_wh{{env_suffix}}'
DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES'
AS
SELECT
    TO_TIMESTAMP_NTZ(pts,'YYYYMMDD-HH24MISS') AS pts,
    rec_type,
    company_name,
    cik,
    status,
    industry_id,
    sp_rating,
    TRY_TO_DATE(founding_date) AS founding_date,
    addr_line1,
    addr_line2,
    postal_code,
    city,
    state_province,
    country,
    ceo_name,
    description
FROM dcm_demo_2.raw.finwire_stg
WHERE rec_type = 'CMP';
```

This is a key cross-project pattern: the Dynamic Table in the **Pipeline** project reads from `dcm_demo_2.raw.finwire_stg`, a table created by the **Platform** project. The Finance team's admin role was granted `SELECT` access to the raw schema during the Platform deployment, making this cross-project dependency work.

The silver layer includes several types of transformations:

- **Filtering and type casting** — `finwire_cmp_stg`, `finwire_fin_stg`, and `finwire_sec_stg` split a single raw finwire table into company, financial, and security records
- **SCD2 (slowly changing dimension) patterns** — `finwire_cmp_ods` and `finwire_sec_cik_ods` use `LEAD()` window functions to track historical changes with start and end dates
- **Sparse value fill-forward** — `customer_ods` and `account_ods` use `LAG() IGNORE NULLS` to carry forward non-null values from prior CDC records
- **Dimension and fact tables** — `dim_trade`, `dim_account`, `dim_date`, and others join and reshape data for the gold layer

All Dynamic Tables use `TARGET_LAG='DOWNSTREAM'`, meaning they refresh only when a downstream table needs them — keeping compute costs low.

#### Gold Layer

Open `gold_layer.sql`. This file defines the gold schema with aggregate fact tables and views:

```sql
DEFINE SCHEMA dcm_demo_2_finance{{env_suffix}}.gold;

DEFINE DYNAMIC TABLE dcm_demo_2_finance{{env_suffix}}.gold.fact_market_history
TARGET_LAG='1 hour'
WAREHOUSE='dcm_demo_2_finance_wh{{env_suffix}}'
DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES'
AS
SELECT
    fmht.sk_security_id,
    fmht.sk_company_id,
    fmht.sk_date_id,
    fmht.yield,
    fmht.close_price,
    fmht.day_high,
    fmht.day_low,
    fmht.volume,
    COALESCE(fmht.close_price / dfrye.roll_year_eps, 0) AS pe_ratio,
    fmhchl.fifty_two_week_high,
    fmhchl.sk_fifty_two_week_high_date,
    fmhchl.fifty_two_week_low,
    fmhchl.sk_fifty_two_week_low_date
FROM dcm_demo_2_finance{{env_suffix}}.silver.fact_market_history_trans fmht
LEFT OUTER JOIN dcm_demo_2_finance{{env_suffix}}.silver.dim_financial_roll_year_eps dfrye
    ON fmht.sk_company_id = dfrye.sk_company_id
    AND YEAR(TO_DATE(fmht.sk_date_id::STRING, 'YYYYMMDD')) || QUARTER(TO_DATE(fmht.sk_date_id::STRING, 'YYYYMMDD')) = dfrye.year_qtr
INNER JOIN dcm_demo_2_finance{{env_suffix}}.silver.fact_market_history_calc_high_low fmhchl
    ON fmht.sk_security_id = fmhchl.sk_security_id
    AND fmht.sk_date_id = fmhchl.sk_date_id;
```

Notice that `fact_market_history` uses `TARGET_LAG='1 hour'` — unlike the silver-layer tables that use `DOWNSTREAM`, this gold-layer table refreshes on a fixed schedule. This is common for aggregate tables that serve dashboards.

The gold layer also includes:
- **`fact_holdings`** — A view (not a Dynamic Table) that joins raw holding history with the silver-layer trade dimension
- **`fact_prospect`** — A Dynamic Table that unions prospect data with customer designations and builds a marketing nameplate
- **`fact_cash_balances`** — A Dynamic Table that calculates running cash balances per account using window functions

#### Data Quality Expectations

Open `expectations.sql`. This file attaches Data Metric Functions to the gold-layer prospect table:

```sql
ATTACH DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
    TO TABLE dcm_demo_2_finance{{env_suffix}}.gold.fact_prospect
        ON (agency_id)
        EXPECTATION no_missing_id (VALUE = 0);

ATTACH DATA METRIC FUNCTION SNOWFLAKE.CORE.MAX
    TO TABLE dcm_demo_2_finance{{env_suffix}}.gold.fact_prospect
        ON (age)
        EXPECTATION no_dead_prospects (VALUE < 120);

ATTACH DATA METRIC FUNCTION SNOWFLAKE.CORE.MIN
    TO TABLE dcm_demo_2_finance{{env_suffix}}.gold.fact_prospect
        ON (age)
        EXPECTATION no_kids (VALUE > 18);
```

These expectations enforce three data quality rules on the `fact_prospect` table:
- **`no_missing_id`** — The `agency_id` column must have zero nulls
- **`no_dead_prospects`** — The maximum age must be less than 120
- **`no_kids`** — The minimum age must be greater than 18

Because the table has `DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES'`, these expectations are automatically evaluated whenever the data changes.

<!-- ------------------------ -->
## Deploy the Pipeline Project

With the Platform deployed and data loaded, you can now deploy the Pipeline project to build the transformation layers.

### Create the DCM Project Object

```sql
USE ROLE dcm_admin;

CREATE OR REPLACE DCM PROJECT dcm_demo.projects.dcm_pipeline_project_dev
    COMMENT = 'for DCM Pipeline Demo - Quickstart 2';
```

### Plan the Deployment

1. In the DCM control panel, select the project **DCM_Pipeline_Demo**.
2. Verify the `DCM_DEV` target is selected and it points to `DCM_PIPELINE_PROJECT_DEV`.
3. Override the templating value for `user` with your own Snowflake username.

![Selecting the Pipeline project](assets/select_pipeline_project.png)

Click **Plan** and wait for the definitions to render, compile, and dry-run.

![Pipeline project plan results](assets/pipeline_plan_results.png)

The plan should show CREATE statements for:

- 2 schemas (`SILVER` and `GOLD`) in `DCM_DEMO_2_FINANCE_DEV`
- 11 Dynamic Tables in the silver layer
- 4 Dynamic Tables and 1 view in the gold layer
- 3 data quality expectations attached to `FACT_PROSPECT`

### Deploy

1. Click **Deploy** in the top-right corner of the Plan results.
2. Add a deployment alias (e.g., "Initial pipeline deployment").

![Pipeline deploy dialog](assets/pipeline_deploy_dialog.png)

Once the deployment completes, refresh the Database Explorer. You should see the `SILVER` and `GOLD` schemas inside `DCM_DEMO_2_FINANCE_DEV`, each populated with Dynamic Tables and views.

![Database Explorer showing pipeline objects](assets/pipeline_deployed_objects.png)

<!-- ------------------------ -->
## Query the Results

With both projects deployed and data loaded, the Dynamic Tables will begin refreshing. You can query the gold-layer tables to verify the end-to-end pipeline is working.

### Query Fact Tables

```sql
SELECT * FROM dcm_demo_2_finance_dev.gold.fact_market_history LIMIT 10;
```

```sql
SELECT * FROM dcm_demo_2_finance_dev.gold.fact_prospect LIMIT 10;
```

```sql
SELECT * FROM dcm_demo_2_finance_dev.gold.fact_cash_balances LIMIT 10;
```

```sql
SELECT * FROM dcm_demo_2_finance_dev.gold.fact_holdings LIMIT 10;
```

### Check Data Quality Expectations

You can verify the data quality expectations by querying the Data Metric Function results:

```sql
SELECT *
FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    REF_ENTITY_NAME => 'dcm_demo_2_finance_dev.gold.fact_prospect',
    REF_ENTITY_DOMAIN => 'TABLE'
));
```

This shows all attached expectations and their current status. The `no_missing_id`, `no_dead_prospects`, and `no_kids` expectations should all be passing if the sample data is clean.

<!-- ------------------------ -->
## Cleanup

To clean up all objects created in this guide, run the following:

```sql
USE ROLE dcm_admin;

-- Drop deployed infrastructure from the Pipeline project
DROP DATABASE IF EXISTS dcm_demo_2_finance_dev;

-- Drop deployed infrastructure from the Platform project
DROP DATABASE IF EXISTS dcm_demo_2;
DROP WAREHOUSE IF EXISTS dcm_demo_2_finance_wh_dev;

-- Drop roles created by the deployments
DROP ROLE IF EXISTS dcm_demo_2_finance_admin;
DROP ROLE IF EXISTS dcm_demo_2_finance_usage;

-- Drop DCM Project objects
USE ROLE ACCOUNTADMIN;
DROP DCM PROJECT IF EXISTS dcm_demo.projects.dcm_pipeline_project_dev;
DROP DCM PROJECT IF EXISTS dcm_demo.projects.dcm_platform_project_dev;
DROP SCHEMA IF EXISTS dcm_demo.projects;
DROP DATABASE IF EXISTS dcm_demo;

-- Drop the DCM Admin role and warehouse (optional)
DROP ROLE IF EXISTS dcm_admin;
DROP WAREHOUSE IF EXISTS dcm_wh;
```

<!-- ------------------------ -->
## Conclusion and Resources

In this guide, you learned how to:

- **Split infrastructure across multiple DCM Projects** — separating platform infrastructure from data transformation pipelines for cleaner ownership and independent deployment
- **Define stage-based data ingestion** using a stage, a CRON-scheduled Task, and a `post_hook` for setup commands
- **Build a medallion architecture as code** with silver-layer Dynamic Tables for cleaning and transformation, and gold-layer fact tables for aggregation
- **Use Jinja macros and loops** to create per-team infrastructure (warehouses, databases, roles, grants) from a single set of definition files
- **Attach data quality expectations** to gold-layer tables using Data Metric Functions
- **Deploy projects sequentially** where one project's output becomes another project's input

### Related Resources
- [DCM Projects Documentation](https://docs.snowflake.com/en/user-guide/dcm-projects/dcm-projects-overview)
- [Sample DCM Projects Repository](https://github.com/Snowflake-Labs/snowflake_dcm_projects)
- [Get Started with Snowflake DCM Projects](https://www.snowflake.com/en/developers/guides/get-started-snowflake-dcm-projects/)
