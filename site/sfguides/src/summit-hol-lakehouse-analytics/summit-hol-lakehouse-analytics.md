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

### What You'll Need
- A Snowflake Enterprise account with `ACCOUNTADMIN` access, deployed in **AWS US West 2 (Oregon)**

> **Don't have a Snowflake account?** Sign up for a free trial at [signup.snowflake.com/summit2026](https://signup.snowflake.com/summit2026). Select the **AI Data Cloud for Enterprise** option — this trial includes free access to Cortex Code CLI.

### What You'll Build
- A Snowflake **External Volume** connected to the lab's S3-backed Iceberg dataset
- A **Catalog Integration** pointing to the AWS Glue Iceberg REST endpoint using SigV4 authentication
- A **Catalog-Linked Database** that auto-discovers and syncs Iceberg tables from the Glue Data Catalog

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
| `surname` | string | Customer surname |
| `postcodedistrict` | string | Customer postcode district |
