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

<!-- ------------------------ -->
## Create Snowflake Objects

In this section you will create three Snowflake objects that wire your Snowflake account to the pre-configured AWS infrastructure. All steps require `ACCOUNTADMIN`.

Open a new worksheet in [Snowsight](https://app.snowflake.com) and run each statement in order.

### Step 1 — Create an External Volume

An **External Volume** tells Snowflake where the Iceberg data files live in cloud storage and which IAM role to use to access them. It is the credential layer between Snowflake and S3.

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

### Step 2 — Create a Catalog Integration

A **Catalog Integration** tells Snowflake how to reach the external Iceberg catalog — in this case, the AWS Glue Iceberg REST Catalog (IRC) endpoint. It handles authentication (SigV4) and points to the correct AWS account and region.

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

### Step 3 — Create a Catalog-Linked Database

A **Catalog-Linked Database** connects to the Catalog Integration and automatically discovers every namespace and table registered in the Glue Data Catalog. Snowflake polls the catalog on the interval you specify and keeps its local view in sync — no manual `ALTER ICEBERG TABLE ... REFRESH` needed.

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

### Step 4 — Verify the Catalog Sync

After creating the database, Snowflake starts discovering tables from the Glue catalog. Run this to check the sync status:

```sql
SELECT SYSTEM$CATALOG_LINK_STATUS('my_iceberg_db');
```

Look for `"failureDetails":[]` in the output. If you see failures, wait 30 seconds and re-run.

> **Note:** The `quotes` table should appear within 60 seconds of creating the database.

<!-- ------------------------ -->
## Query the Data

With the Catalog-Linked Database created, the `quotes` Iceberg table is available to query like any native Snowflake table. The data is read directly from S3 — nothing is copied into Snowflake storage.

> **Important:** AWS Glue uses case-insensitive, lowercase identifiers. Always wrap schema and table names in double quotes when querying a Catalog-Linked Database.

### Explore the table

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

### High-frequency quote customers

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

### Premium by credit score band

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
## Apply Data Governance

Snowflake Horizon governance policies apply natively to Iceberg tables in a Catalog-Linked Database — the data never needs to move into Snowflake storage for policies to take effect.

In this section you will create two roles with different data access levels, then apply dynamic data masking to PII columns in the `quotes` table. Analysts see partially masked data; data engineers see the full values.

### Create roles

```sql
USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS lab_data_engineer;
CREATE ROLE IF NOT EXISTS lab_analyst;

-- Hierarchy: analyst is a subset of data engineer
GRANT ROLE lab_analyst TO ROLE lab_data_engineer;

-- Grant both roles to your user
GRANT ROLE lab_data_engineer TO USER IDENTIFIER(CURRENT_USER());
GRANT ROLE lab_analyst TO USER IDENTIFIER(CURRENT_USER());
```

### Grant access to the Iceberg data

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

### Create masking policies

Each policy partially masks a PII column. `LAB_DATA_ENGINEER` and `ACCOUNTADMIN` see the real value — all other roles see a redacted version.

```sql
CREATE DATABASE IF NOT EXISTS iceberg_lab_db;
CREATE SCHEMA IF NOT EXISTS iceberg_lab_db.analytics;

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

### Apply policies to the Iceberg table

```sql
USE ROLE ACCOUNTADMIN;

ALTER ICEBERG TABLE my_iceberg_db."iceberg"."quotes"
  MODIFY COLUMN email SET MASKING POLICY iceberg_lab_db.analytics.mask_email;

ALTER ICEBERG TABLE my_iceberg_db."iceberg"."quotes"
  MODIFY COLUMN phonenumber SET MASKING POLICY iceberg_lab_db.analytics.mask_phone;

ALTER ICEBERG TABLE my_iceberg_db."iceberg"."quotes"
  MODIFY COLUMN surname SET MASKING POLICY iceberg_lab_db.analytics.mask_surname;

ALTER ICEBERG TABLE my_iceberg_db."iceberg"."quotes"
  MODIFY COLUMN dateofbirth SET MASKING POLICY iceberg_lab_db.analytics.mask_dob;
```

### Verify masking in action

Switch to the analyst role — PII is partially masked:

```sql
USE ROLE lab_analyst;

SELECT uuid, surname, email, phonenumber, dateofbirth, totalpremiumpayable
FROM my_iceberg_db."iceberg"."quotes"
LIMIT 5;
```

Switch to the data engineer role — full values visible:

```sql
USE ROLE lab_data_engineer;

SELECT uuid, surname, email, phonenumber, dateofbirth, totalpremiumpayable
FROM my_iceberg_db."iceberg"."quotes"
LIMIT 5;
```

> The same Iceberg data in AWS Glue, governed entirely by Snowflake — no data movement, no copies, no AWS-side policy changes needed.

<!-- ------------------------ -->
## Create a Semantic View

A **Semantic View** defines the business meaning of your data — dimensions, metrics, and facts — so that Snowflake's AI can understand and answer questions about it in natural language. The semantic view respects masking policies automatically: an analyst querying via natural language sees the same masked values as they would in SQL.

### Create a view wrapper

Semantic views require a plain view reference in the same schema. Create a thin wrapper over the CLD Iceberg table first:

```sql
CREATE OR REPLACE VIEW iceberg_lab_db.analytics.quotes_vw AS
SELECT * FROM my_iceberg_db."iceberg"."quotes";
```

### Create the semantic view

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

### Grant access to the semantic view

```sql
GRANT USAGE ON DATABASE iceberg_lab_db TO ROLE lab_analyst;
GRANT USAGE ON SCHEMA iceberg_lab_db.analytics TO ROLE lab_analyst;
GRANT SELECT ON SEMANTIC VIEW iceberg_lab_db.analytics.quotes_sv TO ROLE lab_analyst;
GRANT USAGE ON DATABASE iceberg_lab_db TO ROLE lab_data_engineer;
GRANT USAGE ON SCHEMA iceberg_lab_db.analytics TO ROLE lab_data_engineer;
GRANT SELECT ON SEMANTIC VIEW iceberg_lab_db.analytics.quotes_sv TO ROLE lab_data_engineer;
```

Verify the semantic view:

```sql
SHOW SEMANTIC VIEWS IN SCHEMA iceberg_lab_db.analytics;
SHOW SEMANTIC METRICS IN iceberg_lab_db.analytics.quotes_sv;
SHOW SEMANTIC DIMENSIONS IN iceberg_lab_db.analytics.quotes_sv;
```

<!-- ------------------------ -->
## Query with Natural Language

A **Cortex Agent** wraps the semantic view and exposes it as a natural language interface. Snowflake translates plain English questions into SQL against your Iceberg data — masking policies are enforced automatically based on the querying role.

### Create the agent

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
    "response": "Answer questions about insurance quote data. Use the quotes tool to query premium amounts, product types, credit scores, and customer demographics. Summarize results clearly and suggest follow-up questions."
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "Query Insurance Quotes",
        "description": "Query insurance quote data including premiums, products, credit scores, and customer demographics."
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

### Ask questions in natural language

Open the agent in Snowsight: navigate to **AI & ML > Agents**, find **Insurance Quotes Analyst**, and click **Open**.

Try these questions:

```
What are the top 5 insurance products by number of quotes?
```

```
What is the average premium for homeowners vs non-homeowners?
```

```
Which postcode district has the highest average risk premium?
```

```
How does credit score affect the total premium payable?
```

```
Show me quote volume broken down by marital status and product type.
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
- [Get Started with Snowflake-Managed Iceberg Tables](https://quickstarts.snowflake.com/guide/get-started-snowflake-managed-iceberg-tables) — Create Snowflake-managed Iceberg tables, stream and transform fleet data, query with Snowflake Intelligence, and read the same tables from DuckDB and Apache Spark
- [Iceberg V3 Tables Comprehensive Guide](https://quickstarts.snowflake.com/guide/iceberg-v3-tables-comprehensive-guide) — Build an end-to-end enterprise lakehouse platform using Iceberg V3 tables with streaming, variant data, time-series, geospatial analytics, governance, and AI
