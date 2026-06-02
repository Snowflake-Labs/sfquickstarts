author: Vino Duraisamy
id: summit-hol-lakehouse-analytics
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/apache-iceberg, snowflake-site:taxonomy/industry/financial-services
language: en
summary: Hands-on lab for Snowflake Summit 2026 — connect Snowflake to an Apache Iceberg dataset in AWS Glue via a Catalog-Linked Database and query it without moving a single byte.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Query Apache Iceberg Tables from Snowflake using AWS Glue
<!-- ------------------------ -->
## Overview

[Apache Iceberg](https://iceberg.apache.org/) is an open table format for large analytical datasets — it brings ACID transactions, schema evolution, and high-performance queries to data stored in object storage like Amazon S3. Both Snowflake and AWS support the Iceberg format natively, enabling customers to drastically improve data interoperability and build open analytic environments without vendor lock-in.

In this hands-on lab you will connect Snowflake to a pre-configured AWS Glue Data Catalog using a **Catalog-Linked Database (CLD)** — Snowflake's mechanism for auto-discovering and staying in sync with external Iceberg catalogs. The AWS infrastructure (S3 bucket, Glue database, IAM role) has been set up for you. Your job is to wire Snowflake to it in four SQL statements and start querying.

The dataset is a Financial Services use case: insurance quote requests collected from systems and stored as Parquet on S3, converted to Iceberg format. The data contains customer, policy, and pricing attributes — a common pattern in insurance analytics for identifying churn risk and high quote frequency.

### What You'll Learn
- How Snowflake connects to external Iceberg catalogs via a [Catalog-Linked Database](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- How [External Volumes](https://docs.snowflake.com/en/user-guide/tables-iceberg-storage) and [Catalog Integrations](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration-rest-glue) work together to give Snowflake access to external Iceberg tables
- How the Glue Iceberg REST Catalog (IRC) API enables Snowflake to discover and read tables directly from the Glue Data Catalog
- How to query Apache Iceberg data in AWS Glue from Snowflake without copying or moving data
- How to apply [Snowflake Horizon](https://docs.snowflake.com/en/user-guide/snowflake-horizon) governance — RBAC and dynamic data masking — to Iceberg tables
- How to create a [Semantic View](https://docs.snowflake.com/en/user-guide/views-semantic) on top of Iceberg data for AI-ready analytics
- How to build a [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent) and query your data lake in natural language

### What You'll Need
- A Snowflake Enterprise account with `ACCOUNTADMIN` access, deployed in **AWS US West 2 (Oregon)**

> **Don't have a Snowflake account?** Sign up for a free trial at [signup.snowflake.com/summit2026](https://signup.snowflake.com/summit2026). Select the **AI Data Cloud for Enterprise** option — this trial includes free access to Cortex Code CLI.

> **Important:** When creating your trial account, select **Amazon Web Services** as the cloud provider and **US West (Oregon)** as the region. The lab infrastructure (S3 bucket, Glue catalog, IAM role) is deployed in AWS US West 2 — your Snowflake account must be in the same region to reach it.

### What You'll Build
- A Snowflake **External Volume** connected to the lab's S3-backed Iceberg dataset
- A **Catalog Integration** pointing to the AWS Glue Iceberg REST endpoint using SigV4 authentication
- A **Catalog-Linked Database** that auto-discovers and syncs Iceberg tables from the Glue Data Catalog
- **Dynamic data masking policies** protecting PII columns in the Iceberg table
- A **Semantic View** that defines business metrics and dimensions on your Iceberg data
- A **Cortex Agent** for natural language analytics on your data lake

<!-- ------------------------ -->
## Lab Environment

The AWS infrastructure for this lab has been pre-configured. You do not need an AWS account or AWS credentials to complete this lab.

Here is what has been set up on your behalf:

| Resource | Details |
|---|---|
| **S3 Bucket** | `s3://sf-lab-iceberg-407539788379/iceberg/` (us-west-2) |
| **Glue Database** | `iceberg` |
| **Iceberg Table** | `quotes` — 40 columns, insurance quote records in Iceberg V2 format |
| **IAM Role** | `arn:aws:iam::407539788379:role/sf-lab-shared-role` |

### Architecture

The diagram below shows how the components connect:

- Raw insurance data was converted from Parquet to Apache Iceberg V2 format using an AWS Glue ETL job and stored in Amazon S3
- The table is registered in the AWS Glue Data Catalog, which exposes it via the Iceberg REST Catalog (IRC) API
- Snowflake connects to the Glue catalog using SigV4 authentication via a Catalog Integration, and reads data files directly from S3 via an External Volume
- A Catalog-Linked Database auto-discovers all tables in the Glue catalog and keeps them in sync — no manual table registration needed

### The quotes table

The `quotes` dataset represents insurance quote requests with the following key columns:

| Column | Type | Description |
|---|---|---|
| `uuid` | string | Unique quote identifier |
| `quote_product` | string | Insurance product type |
| `quotedate` | date | Date the quote was requested |
| `policyno` | string | Policy number |
| `creditscore` | decimal | Customer credit score |
| `newriskpremium` | decimal | Calculated risk premium |
| `totalpremiumpayable` | decimal | Final premium amount |
| `surname` | string | Customer surname (PII) |
| `email` | string | Customer email address (PII) |
| `phonenumber` | string | Customer phone number (PII) |
| `dateofbirth` | string | Customer date of birth (PII) |
| `postcodedistrict` | string | Customer postcode district |

### Running SQL in Snowsight

All SQL in this lab runs in [Snowsight](https://app.snowflake.com), Snowflake's web interface. Here's how to run each block:

1. Log in to [Snowsight](https://app.snowflake.com) and click **Projects → Worksheets** in the left nav
2. Click **+** (top right) to create a new SQL worksheet
3. Set your role to `ACCOUNTADMIN` using the role picker in the top-left corner of the worksheet
4. Set your warehouse to `COMPUTE_WH` (or the warehouse available in your account)
5. Paste a SQL block from the lab into the editor
6. **Run all statements** in the block: press `Ctrl + Shift + Enter` (Windows/Linux) or `Cmd + Shift + Return` (Mac), or click the **Run All** button
7. **Run a single statement**: place your cursor inside it and press `Ctrl + Enter` (Windows/Linux) or `Cmd + Return` (Mac)

> **Tip:** Each section in this lab uses a separate SQL block. You can run everything in a single worksheet in order, or create one worksheet per section to keep things organized.

<!-- ------------------------ -->
## Build with Cortex Code

[Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code) is Snowflake's AI coding assistant. It connects directly to your Snowflake account, reads schema context, and can execute SQL on your behalf — so you can complete this entire lab from the terminal with a single prompt instead of running each block manually.

### Setup

Install the Snowflake CLI and start a Cortex Code session connected to your trial account:

```bash
# Install Snowflake CLI (macOS/Linux)
pip install snowflake-cli

# Configure a connection to your trial account
snow connection add

# Start Cortex Code
cortex code
```

### Starter Prompt

Once inside Cortex Code, paste the following:

```
I want to complete the Summit HOL Lakehouse Analytics lab end to end.

My Snowflake account is on AWS US West 2 (Oregon). I have ACCOUNTADMIN access
and my warehouse is COMPUTE_WH.

The lab has pre-configured AWS infrastructure:
- S3 bucket: s3://sf-lab-iceberg-407539788379/iceberg/
- IAM role: arn:aws:iam::407539788379:role/sf-lab-shared-role
- Glue database: iceberg, table: quotes (~56K insurance quote records)

Please run through all sections in order:

1. Create External Volume my_iceberg_vol, Catalog Integration my_glue_int, and
   Catalog-Linked Database my_iceberg_db. Verify the quotes table syncs.

2. Query the quotes table — row count, product breakdown by volume, and premium
   by credit score band.

3. Set up governance:
   - Create roles lab_analyst and lab_data_engineer with grants + warehouse access
   - Create view iceberg_lab_db.analytics.quotes_vw over the Iceberg table
   - Apply dynamic data masking to email, phonenumber, surname, and dateofbirth
     columns on the view using ALTER VIEW
   - Verify masking by querying as lab_analyst vs lab_data_engineer

4. Create Semantic View iceberg_lab_db.analytics.quotes_sv on top of quotes_vw
   with facts, dimensions, and metrics.

5. Create Cortex Agent iceberg_lab_db.analytics.quotes_agent backed by quotes_sv.

Run each SQL block, show me results, and explain what each step built.
```

Cortex Code will run each section end to end — including role switching for masking verification. To resume at any step, tell it where you left off.

> **Note:** If you prefer to run the SQL manually, continue to the next section.

<!-- ------------------------ -->
## Create Snowflake Objects

In this section you will create three Snowflake objects that wire your Snowflake account to the pre-configured AWS infrastructure. All three steps require `ACCOUNTADMIN`.

**How to run:**
1. Log in to [Snowsight](https://app.snowflake.com)
2. Go to **Projects → Worksheets** and click **+** to open a new SQL worksheet
3. Set your role to `ACCOUNTADMIN` and your warehouse to `COMPUTE_WH`
4. Copy each SQL block below, paste it into the worksheet, and click **Run All** (or press `Ctrl + Shift + Enter`)
5. Confirm the status message shows `successfully created` before moving to the next block

### External Volume

An **External Volume** tells Snowflake where the Iceberg data files live in cloud storage and which IAM role to use to access them. It is the credential layer between Snowflake and S3.

Copy and run in your Snowsight worksheet:

```sql
CREATE OR REPLACE EXTERNAL VOLUME my_iceberg_vol
  STORAGE_LOCATIONS = (
    (
      NAME             = 'us-west-2'
      STORAGE_PROVIDER = 'S3'
      STORAGE_BASE_URL = 's3://sf-lab-iceberg-407539788379/iceberg/'
      STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::407539788379:role/sf-lab-shared-role'
    )
  )
  ALLOW_WRITES = FALSE;
```

`ALLOW_WRITES = FALSE` marks this volume as read-only — Snowflake will not attempt to write metadata or data back to S3.

### Catalog Integration

A **Catalog Integration** tells Snowflake how to reach the external Iceberg catalog — in this case, the AWS Glue Iceberg REST Catalog (IRC) endpoint. It handles authentication (SigV4) and points to the correct AWS account and region.

Copy and run in your Snowsight worksheet:

```sql
CREATE OR REPLACE CATALOG INTEGRATION my_glue_int
  CATALOG_SOURCE = ICEBERG_REST
  TABLE_FORMAT   = ICEBERG
  REST_CONFIG = (
    CATALOG_URI      = 'https://glue.us-west-2.amazonaws.com/iceberg'
    CATALOG_API_TYPE = AWS_GLUE
    CATALOG_NAME     = '407539788379'
  )
  REST_AUTHENTICATION = (
    TYPE                 = SIGV4
    SIGV4_IAM_ROLE       = 'arn:aws:iam::407539788379:role/sf-lab-shared-role'
    SIGV4_SIGNING_REGION = 'us-west-2'
  )
  ENABLED = TRUE;
```

### Catalog-Linked Database

A **Catalog-Linked Database** connects to the Catalog Integration and automatically discovers every namespace and table registered in the Glue Data Catalog. Snowflake polls the catalog on the interval you specify and keeps its local view in sync — no manual `ALTER ICEBERG TABLE ... REFRESH` needed.

Copy and run in your Snowsight worksheet:

```sql
CREATE OR REPLACE DATABASE my_iceberg_db
  LINKED_CATALOG = (
    CATALOG                  = 'my_glue_int',
    SYNC_INTERVAL_SECONDS    = 3600,
    ALLOWED_WRITE_OPERATIONS = NONE
  )
  EXTERNAL_VOLUME = 'my_iceberg_vol';
```

`SYNC_INTERVAL_SECONDS = 3600` sets the catalog poll interval to 1 hour. `ALLOWED_WRITE_OPERATIONS = NONE` enforces read-only access at the database level.

### Verify Sync

After creating the database, Snowflake starts discovering tables from the Glue catalog. Run this in your worksheet to check the sync status:

1. Copy and run the statement below
2. Look for `"failureDetails":[]` and `"executionState":"RUNNING"` or `"SUCCEEDED"` in the output
3. If you see failures, wait 30 seconds and re-run

```sql
SELECT SYSTEM$CATALOG_LINK_STATUS('my_iceberg_db');
```

> **Note:** The `quotes` table should appear within 60 seconds of creating the database.

<!-- ------------------------ -->
## Query Data

With the Catalog-Linked Database created, the `quotes` Iceberg table is available to query like any native Snowflake table. The data is read directly from S3 — nothing is copied into Snowflake storage.

**How to run:** In your Snowsight worksheet, make sure your role is `ACCOUNTADMIN` and your warehouse is active. Copy each query below and run it with `Ctrl + Enter` (or `Cmd + Return` on Mac). You can run all queries in the same worksheet.

> **Important:** AWS Glue uses case-insensitive, lowercase identifiers. Always wrap schema and table names in double quotes when querying a Catalog-Linked Database.

### Explore the table

Run these two queries to confirm the table is accessible and check row count:

```sql
SELECT * FROM my_iceberg_db."iceberg"."quotes" LIMIT 10;

SELECT COUNT(*) AS total_quotes FROM my_iceberg_db."iceberg"."quotes";
```

### Quote volume by product

```sql
SELECT
    quote_product,
    COUNT(*)                           AS total_quotes,
    ROUND(AVG(totalpremiumpayable), 2) AS avg_premium
FROM my_iceberg_db."iceberg"."quotes"
GROUP BY quote_product
ORDER BY total_quotes DESC;
```

### High-Frequency Customers

```sql
SELECT
    surname,
    postcodedistrict,
    COUNT(*)                           AS quote_count,
    MIN(quotedate)                     AS first_quote,
    MAX(quotedate)                     AS last_quote,
    ROUND(AVG(totalpremiumpayable), 2) AS avg_premium
FROM my_iceberg_db."iceberg"."quotes"
GROUP BY surname, postcodedistrict
HAVING COUNT(*) > 1
ORDER BY quote_count DESC
LIMIT 20;
```

### Premium by Credit Score

```sql
SELECT
    CASE
        WHEN creditscore >= 8 THEN 'High (8-10)'
        WHEN creditscore >= 5 THEN 'Medium (5-7)'
        ELSE 'Low (0-4)'
    END                                AS credit_band,
    COUNT(*)                           AS quote_count,
    ROUND(AVG(newriskpremium), 2)      AS avg_risk_premium,
    ROUND(AVG(totalpremiumpayable), 2) AS avg_total_premium
FROM my_iceberg_db."iceberg"."quotes"
GROUP BY credit_band
ORDER BY avg_risk_premium DESC;
```

<!-- ------------------------ -->
## Data Governance

Snowflake Horizon governance policies apply natively to Iceberg tables in a Catalog-Linked Database — the data never needs to move into Snowflake storage for policies to take effect.

In this section you will create two roles with different data access levels, then apply dynamic data masking to PII columns in the `quotes` table. Analysts see partially masked data; data engineers see the full values.

**How to run:** Continue in your existing Snowsight worksheet (or open a new one). Each subsection below has its own SQL block — run them in order from top to bottom. The role must be `ACCOUNTADMIN` at the start of each block; the SQL includes `USE ROLE ACCOUNTADMIN` where needed.

### Create roles

Run this block to create both roles, set up the role hierarchy, grant them to your user, and give them warehouse access:

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS lab_data_engineer;
CREATE ROLE IF NOT EXISTS lab_analyst;

-- Hierarchy: analyst is a subset of data engineer
GRANT ROLE lab_analyst TO ROLE lab_data_engineer;

-- Grant both roles to your user
GRANT ROLE lab_data_engineer TO USER IDENTIFIER(CURRENT_USER());
GRANT ROLE lab_analyst TO USER IDENTIFIER(CURRENT_USER());

-- Grant warehouse access so roles can run queries
-- Replace COMPUTE_WH with your warehouse name if different
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE lab_data_engineer;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE lab_analyst;
```

### Grant Access

Run this block to give both roles access to the External Volume, Catalog Integration, and the Iceberg table in the CLD:

```sql
-- External volume and catalog integration
GRANT USAGE ON EXTERNAL VOLUME my_iceberg_vol TO ROLE lab_data_engineer;
GRANT USAGE ON INTEGRATION my_glue_int TO ROLE lab_data_engineer;

-- Catalog-linked database
GRANT USAGE ON DATABASE my_iceberg_db TO ROLE lab_data_engineer;
GRANT USAGE ON DATABASE my_iceberg_db TO ROLE lab_analyst;
GRANT USAGE ON SCHEMA my_iceberg_db."iceberg" TO ROLE lab_data_engineer;
GRANT USAGE ON SCHEMA my_iceberg_db."iceberg" TO ROLE lab_analyst;
GRANT SELECT ON ALL ICEBERG TABLES IN SCHEMA my_iceberg_db."iceberg" TO ROLE lab_data_engineer;
GRANT SELECT ON ALL ICEBERG TABLES IN SCHEMA my_iceberg_db."iceberg" TO ROLE lab_analyst;
```

### View Wrapper

Before applying masking policies, create a thin view over the Iceberg table. Masking policies cannot be applied directly to tables in a Catalog-Linked Database — they must be attached to a view wrapper. This same view is also used by the Semantic View in the next section.

Run this block to create the supporting database, schema, and view:

```sql
CREATE DATABASE IF NOT EXISTS iceberg_lab_db;
CREATE SCHEMA IF NOT EXISTS iceberg_lab_db.analytics;

CREATE OR REPLACE VIEW iceberg_lab_db.analytics.quotes_vw AS
SELECT * FROM my_iceberg_db."iceberg"."quotes";
```

### Masking Policies

Each policy partially masks a PII column. `LAB_DATA_ENGINEER` and `ACCOUNTADMIN` see the real value — all other roles see a redacted version.

Run this block to create all four masking policies:

```sql
USE DATABASE iceberg_lab_db;
USE SCHEMA analytics;

-- Email: john.doe@example.com → j***@***.com
CREATE OR REPLACE MASKING POLICY mask_email
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('LAB_DATA_ENGINEER', 'ACCOUNTADMIN') THEN val
      ELSE CONCAT(LEFT(val, 1), '***@***.', SPLIT_PART(val, '.', -1))
    END;

-- Phone: 07123456789 → 071*****789
CREATE OR REPLACE MASKING POLICY mask_phone
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('LAB_DATA_ENGINEER', 'ACCOUNTADMIN') THEN val
      ELSE CONCAT(LEFT(val, 3), REPEAT('*', LENGTH(val) - 6), RIGHT(val, 3))
    END;

-- Surname: Smith → S****
CREATE OR REPLACE MASKING POLICY mask_surname
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('LAB_DATA_ENGINEER', 'ACCOUNTADMIN') THEN val
      ELSE CONCAT(LEFT(val, 1), REPEAT('*', GREATEST(LENGTH(val) - 1, 4)))
    END;

-- Date of birth: 1985-03-15 → ****-**-15
CREATE OR REPLACE MASKING POLICY mask_dob
  AS (val STRING) RETURNS STRING ->
    CASE
      WHEN CURRENT_ROLE() IN ('LAB_DATA_ENGINEER', 'ACCOUNTADMIN') THEN val
      ELSE CONCAT('****-**-', RIGHT(val, 2))
    END;
```

### Apply Policies

Apply each masking policy to the corresponding column on the view wrapper. Masking is enforced whenever the view is queried — directly in SQL, via the semantic view, or through the Cortex Agent.

```sql
USE ROLE ACCOUNTADMIN;

ALTER VIEW iceberg_lab_db.analytics.quotes_vw
  ALTER COLUMN email SET MASKING POLICY iceberg_lab_db.analytics.mask_email;

ALTER VIEW iceberg_lab_db.analytics.quotes_vw
  ALTER COLUMN phonenumber SET MASKING POLICY iceberg_lab_db.analytics.mask_phone;

ALTER VIEW iceberg_lab_db.analytics.quotes_vw
  ALTER COLUMN surname SET MASKING POLICY iceberg_lab_db.analytics.mask_surname;

ALTER VIEW iceberg_lab_db.analytics.quotes_vw
  ALTER COLUMN dateofbirth SET MASKING POLICY iceberg_lab_db.analytics.mask_dob;
```

### Verify Masking

Switch to each role and run the same query to see the difference. You can switch roles two ways:
- **In the SQL block:** run `USE ROLE lab_analyst;` before the SELECT (as shown below)
- **In the Snowsight UI:** use the role picker at the top-left of the worksheet

Switch to the analyst role — PII is partially masked:

```sql
USE ROLE lab_analyst;

SELECT uuid, surname, email, phonenumber, dateofbirth, totalpremiumpayable
FROM iceberg_lab_db.analytics.quotes_vw
LIMIT 5;
```

Switch to the data engineer role — full values visible:

```sql
USE ROLE lab_data_engineer;

SELECT uuid, surname, email, phonenumber, dateofbirth, totalpremiumpayable
FROM iceberg_lab_db.analytics.quotes_vw
LIMIT 5;
```

> The same Iceberg data in AWS Glue, governed entirely by Snowflake — no data movement, no copies, no AWS-side policy changes needed.

<!-- ------------------------ -->
## Semantic View

A **Semantic View** defines the business meaning of your data — dimensions, metrics, and facts — so that Snowflake's AI can understand and answer questions about it in natural language. The semantic view respects masking policies automatically: an analyst querying via natural language sees the same masked values as they would in SQL.

**How to run:** Continue in your Snowsight worksheet with `ACCOUNTADMIN`. Run the blocks below in order.

### View Wrapper

The `quotes_vw` view was created in the Data Governance section with masking policies already applied. Semantic views require a plain view reference in the same schema — this view serves that role here too.

No additional SQL needed. The view `iceberg_lab_db.analytics.quotes_vw` is ready to use.

### Create View

Run this block to create the semantic view. It defines the table mapping, facts, dimensions, and metrics that Cortex Analyst will use to translate natural language into SQL:

```sql
USE DATABASE iceberg_lab_db;
USE SCHEMA analytics;

CREATE OR REPLACE SEMANTIC VIEW quotes_sv
  TABLES (
    quotes as quotes_vw
      primary key (uuid)
      comment='Insurance quote requests from the Iceberg data lake in AWS Glue'
  )
  FACTS (
    quotes.newriskpremium      as newriskpremium      comment='Calculated risk premium',
    quotes.totalpremiumpayable as totalpremiumpayable comment='Total premium payable',
    quotes.iptamount           as iptamount           comment='Insurance premium tax',
    quotes.quote_record        as 1                   comment='One record per quote'
  )
  DIMENSIONS (
    quotes.quote_product    as quote_product    with synonyms=('product type', 'insurance product', 'cover type') comment='Insurance product type',
    quotes.quotedate        as quotedate        with synonyms=('quote date', 'date', 'when requested')             comment='Date the quote was requested',
    quotes.maritalstatus    as maritalstatus    with synonyms=('marital status', 'married', 'single')              comment='Customer marital status',
    quotes.homeownerind     as homeownerind     with synonyms=('homeowner', 'owns home', 'property owner')         comment='Whether customer owns home',
    quotes.sex              as sex              with synonyms=('gender', 'customer gender')                         comment='Customer gender',
    quotes.postcodedistrict as postcodedistrict with synonyms=('district', 'location', 'area', 'region')           comment='Customer postcode district',
    quotes.previnsr         as previnsr         with synonyms=('previous insurer', 'prior insurer')                 comment='Previous insurance provider'
  )
  METRICS (
    quotes.total_quotes         as COUNT(quotes.quote_record)      comment='Total number of quote requests',
    quotes.avg_total_premium    as AVG(quotes.totalpremiumpayable)  comment='Average total premium payable',
    quotes.avg_risk_premium     as AVG(quotes.newriskpremium)       comment='Average risk premium',
    quotes.total_premium_volume as SUM(quotes.totalpremiumpayable)  comment='Total premium volume'
  )
  comment='Insurance quote analytics — Iceberg data in AWS Glue via Catalog-Linked Database';
```

> **Note:** The semantic view uses a `quotes as quotes_vw` mapping where `quotes` is the internal reference name and `quotes_vw` is the physical view. Column references in FACTS, DIMENSIONS, and METRICS use the reference name `quotes`.

### Grant Access

```sql
GRANT USAGE ON DATABASE iceberg_lab_db TO ROLE lab_analyst;
GRANT USAGE ON SCHEMA iceberg_lab_db.analytics TO ROLE lab_analyst;
GRANT SELECT ON VIEW iceberg_lab_db.analytics.quotes_vw TO ROLE lab_analyst;
GRANT SELECT ON SEMANTIC VIEW iceberg_lab_db.analytics.quotes_sv TO ROLE lab_analyst;
GRANT USAGE ON DATABASE iceberg_lab_db TO ROLE lab_data_engineer;
GRANT USAGE ON SCHEMA iceberg_lab_db.analytics TO ROLE lab_data_engineer;
GRANT SELECT ON VIEW iceberg_lab_db.analytics.quotes_vw TO ROLE lab_data_engineer;
GRANT SELECT ON SEMANTIC VIEW iceberg_lab_db.analytics.quotes_sv TO ROLE lab_data_engineer;
```

Verify the semantic view:

```sql
SHOW SEMANTIC VIEWS IN SCHEMA iceberg_lab_db.analytics;
SHOW SEMANTIC METRICS IN iceberg_lab_db.analytics.quotes_sv;
SHOW SEMANTIC DIMENSIONS IN iceberg_lab_db.analytics.quotes_sv;
```

<!-- ------------------------ -->
## Natural Language Queries

A **Cortex Agent** wraps the semantic view and exposes it as a natural language interface. Snowflake translates plain English questions into SQL against your Iceberg data — masking policies are enforced automatically based on the querying role.

**How to run:** Run the SQL blocks below in your Snowsight worksheet with `ACCOUNTADMIN`. After creating the agent, open it directly in Snowsight (no SQL needed) to ask questions.

### Create the agent

Run this block to create the agent backed by your semantic view:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE iceberg_lab_db;
USE SCHEMA analytics;

CREATE OR REPLACE AGENT iceberg_lab_db.analytics.quotes_agent
  WITH PROFILE = '{"display_name": "Insurance Quotes Analyst"}'
  COMMENT = 'Natural language analytics on Iceberg insurance quotes data in AWS Glue'
FROM SPECIFICATION $$
{
  "instructions": {
    "response": "Answer questions about insurance quote data. Use the quotes tool to query premium amounts, product types, homeowner status, marital status, and postcode district. Summarize results clearly and suggest follow-up questions."
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "Query Insurance Quotes",
        "description": "Query insurance quote data including premiums, product types, homeowner status, marital status, and postcode district."
      }
    }
  ],
  "tool_resources": {
    "Query Insurance Quotes": {
      "semantic_view": "iceberg_lab_db.analytics.quotes_sv"
    }
  }
}
$$;
```

### Cortex CoWork

To make the agent accessible via [Cortex CoWork](https://docs.snowflake.com/en/user-guide/snowflake-intelligence), grant the Snowflake service role access to the underlying objects:

```sql
USE ROLE ACCOUNTADMIN;

GRANT USAGE ON DATABASE iceberg_lab_db TO ROLE SNOWFLAKE;
GRANT USAGE ON SCHEMA iceberg_lab_db.analytics TO ROLE SNOWFLAKE;
GRANT SELECT ON VIEW iceberg_lab_db.analytics.quotes_vw TO ROLE SNOWFLAKE;
GRANT SELECT ON SEMANTIC VIEW iceberg_lab_db.analytics.quotes_sv TO ROLE SNOWFLAKE;
```

> **Note:** The `SNOWFLAKE` service role is available in Snowflake Enterprise and Business Critical accounts. Trial accounts do not include this role — if you receive a "Role does not exist" error, skip this step. The agent is still fully accessible via **AI & ML > Agents** in Snowsight.

### Ask Questions

To open the agent in Snowsight:

1. In the left nav, click **AI & ML → Agents**
2. Find **Insurance Quotes Analyst** in the list and click **Open**
3. Type a question in the chat input and press Enter
4. The agent translates your question into SQL against `quotes_sv` and returns the result
5. To test masking enforcement: change your active role (top-left role picker) to `lab_analyst` or `lab_data_engineer` and ask the same question — PII fields will be masked or unmasked based on your role

The agent is also available in Cortex CoWork (enterprise accounts only).

Try these questions:

```text
What are the top 5 insurance products by number of quotes?
```

```text
What is the average premium for homeowners vs non-homeowners?
```

```text
Which postcode district has the highest average risk premium?
```

```text
Show me quote volume broken down by marital status and product type.
```

```text
What is the total premium volume by previous insurer?
```

> Switch between the `lab_analyst` and `lab_data_engineer` roles to see how the same natural language question returns different results — masking policies are enforced end-to-end, from Iceberg through the semantic view to the agent response.

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully connected Snowflake to an Apache Iceberg data lake in AWS Glue — querying, governing, and analyzing the data entirely from Snowflake without moving a single byte.

In this lab you built a complete open lakehouse analytics stack:
- Connected Snowflake to AWS Glue via a Catalog-Linked Database using the Iceberg REST Catalog API
- Applied Snowflake Horizon governance — RBAC and dynamic data masking — to Iceberg tables in AWS
- Created a Semantic View to define business metrics and dimensions on your Iceberg data
- Built a Cortex Agent for natural language analytics, with masking enforced end-to-end

### What You Learned
- How External Volumes, Catalog Integrations, and Catalog-Linked Databases work together
- How Snowflake Horizon governance applies natively to external Iceberg tables
- How Semantic Views bridge raw Iceberg data and AI-powered analytics
- How Cortex Agents translate natural language into governed SQL against your data lake

### Related Resources

Documentation:
- [Apache Iceberg tables in Snowflake](https://docs.snowflake.com/en/user-guide/tables-iceberg)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [Configure a catalog integration for AWS Glue Iceberg REST](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration-rest-glue)
- [Dynamic Data Masking](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro)
- [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent)

Related guides:
- [Build Data Lakes using Apache Iceberg with Snowflake and AWS Glue](https://quickstarts.snowflake.com/guide/data-lake-using-apache-iceberg-with-snowflake-and-aws-glue) — Go deeper on the full AWS setup: CloudFormation, Lake Formation credential vending, and the complete Glue IRC integration with Cortex Code fast path
- [Get Started with Snowflake-Managed Iceberg Tables](https://quickstarts.snowflake.com/guide/get-started-snowflake-managed-iceberg-tables) — Create Snowflake-managed Iceberg tables, stream and transform fleet data, query with Cortex CoWork, and read the same tables from DuckDB and Apache Spark
- [Iceberg V3 Tables Comprehensive Guide](https://quickstarts.snowflake.com/guide/iceberg-v3-tables-comprehensive-guide) — Build an end-to-end enterprise lakehouse platform using Iceberg V3 tables with streaming, variant data, time-series, geospatial analytics, governance, and AI
