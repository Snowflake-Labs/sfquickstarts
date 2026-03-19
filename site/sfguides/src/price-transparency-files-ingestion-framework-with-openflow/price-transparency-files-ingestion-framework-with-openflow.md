authors: Aaron Wasserman, Jeevan Rag, Cameron Shimmin
id: price-transparency-files-ingestion-framework-with-openflow
summary: Process Healthcare Price Transparency Machine-Readable Files (MRFs) using Snowflake Openflow's Apache NiFi engine for streaming data ingestion and analytics.
categories: snowflake-site:taxonomy/snowflake-feature/openflow, snowflake-site:taxonomy/industry/healthcare-and-life-sciences
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork_repo_link: https://github.com/Snowflake-Labs/sfguide-price-transparency-files-ingestion-framework-with-openflow
tags: Openflow, Healthcare, Price Transparency, Apache NiFi, Data Ingestion, Snowpipe Streaming, MRF


# Healthcare Price Transparency Files Ingestion Framework with Openflow

<!-- ------------------------ -->

## Overview

Duration: 5

Under the Transparency in Coverage rule, U.S. healthcare payers must publish monthly Machine-Readable Files (MRFs) detailing negotiated rates for covered items and services. These files are large (often 1-50+ GB), deeply nested JSON structures that are difficult to process with traditional tools.

This quickstart demonstrates how to ingest and analyze these MRF files using Snowflake Openflow, which provides a managed Apache NiFi engine for streaming data integration.

### What You'll Build

- An Openflow pipeline that downloads MRF files from payer websites (e.g., Blue Cross Blue Shield)
- NiFi flows that parse deeply nested JSON structures for negotiated rates and provider information
- Snowflake tables populated via Snowpipe Streaming for near real-time ingestion
- Analytical queries for healthcare price analysis and comparison

### What You'll Learn

- How to set up and configure Snowflake Openflow
- How to create Openflow deployments and runtimes
- How to import and run NiFi flow definitions for JSON parsing
- How to use Snowpipe Streaming for high-throughput data ingestion
- How to analyze healthcare pricing data with SQL

### What You'll Need

- A Snowflake account (capacity or on-demand with credit card -- trial accounts cannot use Openflow)
- ACCOUNTADMIN role access for initial setup
- A non-ACCOUNTADMIN default role (users with ACCOUNTADMIN as default role cannot log in to Openflow)
- 30-60 minutes for setup and initial data ingestion

### Assets Created

By the end of this quickstart, you'll have deployed:

- **Database**: `OPENFLOW_PRICE_TRANSPARENCY`
- **Tables**: `HEALTH_PLAN_RATES` and `PROVIDERS`
- **Roles**: `OPENFLOW_ADMIN` and `OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY`
- **Network Rule**: `ALLOW_HEALTH_PAYER_STORAGE`
- **External Access Integration**: `PRICE_TRANSPARENCY_INTEGRATION`
- **Openflow Deployment**: SPCS-based deployment
- **Openflow Runtime**: NiFi runtime with two flow definitions

<!-- ------------------------ -->

## Setup Roles, Database, and Tables

Duration: 10

Run the following SQL as **ACCOUNTADMIN** in a Snowflake SQL worksheet. This script creates the Openflow admin role, database, tables, runtime role, network rule, and external access integration.

### Step 1: Setup Openflow Admin Role

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"price-transparency-files-ingestion-framework","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS OPENFLOW_ADMIN;
GRANT CREATE ROLE ON ACCOUNT TO ROLE OPENFLOW_ADMIN;
GRANT CREATE OPENFLOW DATA PLANE INTEGRATION ON ACCOUNT TO ROLE OPENFLOW_ADMIN;
GRANT CREATE OPENFLOW RUNTIME INTEGRATION ON ACCOUNT TO ROLE OPENFLOW_ADMIN;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE OPENFLOW_ADMIN;

-- Modify with your username:
GRANT ROLE OPENFLOW_ADMIN TO USER YOUR_USERNAME;
ALTER USER YOUR_USERNAME SET DEFAULT_ROLE = OPENFLOW_ADMIN;
```

> Setting your default role to `OPENFLOW_ADMIN` is required. Users with `ACCOUNTADMIN` as their default role cannot log in to the Openflow Control Plane.

### Step 2: Create Database and Tables

```sql
CREATE OR REPLACE DATABASE OPENFLOW_PRICE_TRANSPARENCY;
USE SCHEMA OPENFLOW_PRICE_TRANSPARENCY.PUBLIC;

CREATE OR REPLACE TABLE HEALTH_PLAN_RATES (
    FILE_URL VARCHAR(16777216),
    NAME VARCHAR(16777216),
    DESCRIPTION VARCHAR(16777216),
    NEGOTIATED_TYPE VARCHAR(16777216),
    NEGOTIATED_RATE VARCHAR(16777216),
    NEGOTIATION_ARRANGEMENT VARCHAR(16777216),
    BILLING_CODE VARCHAR(16777216),
    BILLING_CODE_TYPE VARCHAR(16777216),
    BILLING_CLASS VARCHAR(16777216),
    SERVICE_CODE VARCHAR(16777216),
    EXPIRATION_DATE VARCHAR(16777216),
    PROVIDER_REFERENCES VARIANT
);

CREATE OR REPLACE TABLE PROVIDERS (
    FILE_URL VARCHAR(16777216),
    PROVIDER_GROUP_ID VARCHAR(16777216),
    TIN_TYPE VARCHAR(16777216),
    NPI ARRAY,
    TIN_VALUE VARCHAR(16777216)
);
```

#### Table Schemas

**HEALTH_PLAN_RATES** stores negotiated rates from the IN_NETWORK array:

| Column | Description |
|--------|-------------|
| FILE_URL | Source MRF file URL |
| NAME | Plan name |
| DESCRIPTION | Service description |
| NEGOTIATED_TYPE | Type of negotiation (fee schedule, etc.) |
| NEGOTIATED_RATE | The negotiated price |
| BILLING_CODE | CPT/HCPCS/DRG code |
| BILLING_CODE_TYPE | Type of billing code |
| PROVIDER_REFERENCES | Array of provider reference IDs |

**PROVIDERS** stores provider information from the PROVIDER_REFERENCE array:

| Column | Description |
|--------|-------------|
| PROVIDER_GROUP_ID | Reference ID (links to HEALTH_PLAN_RATES) |
| TIN_TYPE | Tax ID type (EIN, NPI) |
| TIN_VALUE | Tax identification number |
| NPI | Array of National Provider Identifiers |

### Step 3: Create Runtime Role

```sql
USE ROLE OPENFLOW_ADMIN;

CREATE OR REPLACE ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
GRANT ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY TO ROLE OPENFLOW_ADMIN;

GRANT USAGE ON DATABASE OPENFLOW_PRICE_TRANSPARENCY TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
GRANT USAGE ON SCHEMA OPENFLOW_PRICE_TRANSPARENCY.PUBLIC TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
GRANT SELECT, INSERT ON TABLE OPENFLOW_PRICE_TRANSPARENCY.PUBLIC.HEALTH_PLAN_RATES TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
GRANT SELECT, INSERT ON TABLE OPENFLOW_PRICE_TRANSPARENCY.PUBLIC.PROVIDERS TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
```

### Step 4: Create Network Rule and External Access Integration

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE OPENFLOW_PRICE_TRANSPARENCY;

CREATE OR REPLACE NETWORK RULE ALLOW_HEALTH_PAYER_STORAGE
    MODE = EGRESS
    TYPE = HOST_PORT
    VALUE_LIST = (
        '0.0.0.0:443',
        '*.blob.core.windows.net:443',
        '*.s3.amazonaws.com:443',
        '*.s3.us-east-1.amazonaws.com:443',
        '*.s3.us-west-2.amazonaws.com:443',
        '*.cloudfront.net:443',
        '*.googleapis.com:443'
    );

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION PRICE_TRANSPARENCY_INTEGRATION
    ALLOWED_NETWORK_RULES = (ALLOW_HEALTH_PAYER_STORAGE)
    ENABLED = TRUE
    COMMENT = 'External access for downloading healthcare price transparency MRF files';

GRANT USAGE ON INTEGRATION PRICE_TRANSPARENCY_INTEGRATION TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
```

### Verify Setup

```sql
SHOW ROLES LIKE 'OPENFLOW%';
SHOW TABLES IN SCHEMA OPENFLOW_PRICE_TRANSPARENCY.PUBLIC;
SHOW GRANTS TO ROLE OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;
DESCRIBE INTEGRATION PRICE_TRANSPARENCY_INTEGRATION;
```

<!-- ------------------------ -->

## Create Openflow Deployment

Duration: 20

An Openflow deployment provisions the underlying compute infrastructure that runs your NiFi runtimes. Only one SPCS deployment can exist per Snowflake account.

1. In Snowsight, navigate to **Ingestion > Openflow**
2. Click **Launch Openflow** to open the Openflow Control Plane
3. Switch to the **OPENFLOW_ADMIN** role in the Openflow UI header
4. Click the **Deployments** tab
5. Click **Create deployment**
6. Click **Next** to proceed past Prerequisites
7. Select **Snowflake** as the deployment location (this option only appears when using the OPENFLOW_ADMIN role)
8. Enter a name for the deployment (e.g., `PRICE_TRANSPARENCY_DEPLOYMENT`)
9. Click **Next** to proceed to Configuration
10. Click **Create deployment**
11. Wait for the deployment to reach **Active** state (approximately 15-20 minutes)

> If the "Snowflake (SPCS)" option does not appear, ensure you have switched to the **OPENFLOW_ADMIN** role in the Openflow UI header. Without this role, only "BYOC on AWS" is available.

<!-- ------------------------ -->

## Create Openflow Runtime

Duration: 10

A runtime is a NiFi instance running on your deployment where you'll import and execute flow definitions.

1. In the Openflow Control Plane, click the **Runtimes** tab
2. Click **Create runtime**
3. Configure the runtime:
   - **Name**: `price_transparency`
   - **Deployment**: Select the deployment created in the previous step
   - **Size**: Large (recommended for MRF file processing)
   - **Min/Max Nodes**: 1 (increase to 5-10 for files larger than 10 GB)
   - **Snowflake Role**: `OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY`
   - **External Access Integration**: `PRICE_TRANSPARENCY_INTEGRATION`
4. Click **Create runtime**
5. When the confirmation modal appears, click **View runtimes** to return to the runtimes list
6. Wait for the runtime to reach **Active** state (approximately 5-10 minutes)

<!-- ------------------------ -->

## Import Flow Definitions

Duration: 10

The repository includes two NiFi flow definition files that handle the MRF parsing:

- **`in_network_processing.json`** -- Parses the IN_NETWORK array from MRF files and writes negotiated rate data to the `HEALTH_PLAN_RATES` table
- **`provider_reference_processing.json`** -- Parses provider reference data and writes to the `PROVIDERS` table

### Import In Network Processing Flow

1. Click on your runtime name to open the NiFi canvas
2. Drag the **Process Group** icon from the toolbar onto the canvas
3. In the dialog, click the browse icon and select `openflow/in_network_processing.json` from the repository
4. Click **Add**
5. Double-click the new process group to enter it
6. Right-click the canvas and select **Enable All Controller Services**
7. Right-click the canvas and select **Start**

### Import Provider Reference Processing Flow

1. Navigate back to the root canvas (right-click > **Leave group**)
2. Drag another **Process Group** icon onto the canvas
3. Browse and select `openflow/provider_reference_processing.json`
4. Click **Add**
5. Double-click the process group
6. Right-click the canvas and select **Enable All Controller Services**
7. Right-click the canvas and select **Start**

> As an alternative to manual import, you can use the `scripts/import_flows.py` script included in the repository. This script uses the NiFi REST API to programmatically import both flows, enable controller services, and start all processors. It requires a Programmatic Access Token (PAT) with the `OPENFLOW_ADMIN` role.

Data ingestion begins immediately after starting both process groups.

<!-- ------------------------ -->

## Monitor Data Ingestion

Duration: 5

Once the flows are running, MRF data streams into your Snowflake tables via Snowpipe Streaming. Monitor ingestion progress with the following query:

```sql
SELECT 'HEALTH_PLAN_RATES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT
FROM OPENFLOW_PRICE_TRANSPARENCY.PUBLIC.HEALTH_PLAN_RATES
UNION ALL
SELECT 'PROVIDERS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT
FROM OPENFLOW_PRICE_TRANSPARENCY.PUBLIC.PROVIDERS;
```

Ingestion time depends on the MRF file size:

| File Size | Approximate Time | Example |
|-----------|-----------------|---------|
| Small (~1 GB) | ~10 minutes | Blue Cross Blue Shield of Illinois |
| Large (~10+ GB) | Several hours | UnitedHealthcare of Washington |

> You may see "Invalid channel" errors on the PutSnowpipeStreaming processor during initial writes. This is normal and can be ignored as long as data appears in the tables.

### Processing Other Files

To process a different MRF file after the initial ingestion:

1. Stop the In Network Processing process group
2. Double-click the **InvokeHTTP** processor inside the group
3. Change the **HTTP URL** property to the new file URL
4. Start the process group

<!-- ------------------------ -->

## Run Analytics

Duration: 10

Once data ingestion is complete, run the following analytical queries to explore the healthcare pricing data.

### Data Quality Check

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"price-transparency-files-ingestion-framework","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

USE SCHEMA OPENFLOW_PRICE_TRANSPARENCY.PUBLIC;

SELECT
    'HEALTH_PLAN_RATES' AS TABLE_NAME,
    COUNT(*) AS TOTAL_ROWS,
    COUNT(BILLING_CODE) AS ROWS_WITH_BILLING_CODE,
    COUNT(NEGOTIATED_RATE) AS ROWS_WITH_RATE,
    COUNT(DESCRIPTION) AS ROWS_WITH_DESCRIPTION
FROM HEALTH_PLAN_RATES
UNION ALL
SELECT
    'PROVIDERS' AS TABLE_NAME,
    COUNT(*) AS TOTAL_ROWS,
    COUNT(PROVIDER_GROUP_ID) AS ROWS_WITH_GROUP_ID,
    COUNT(TIN_VALUE) AS ROWS_WITH_TIN,
    COUNT(NPI) AS ROWS_WITH_NPI
FROM PROVIDERS;
```

### Most Common Billing Codes (Top 10)

```sql
SELECT
    BILLING_CODE_TYPE,
    BILLING_CODE,
    DESCRIPTION,
    COUNT(*) AS TOTAL_OCCURRENCES,
    AVG(NEGOTIATED_RATE::NUMBER) AS AVG_RATE,
    MAX(NEGOTIATED_RATE::NUMBER) AS MAX_RATE,
    MIN(NEGOTIATED_RATE::NUMBER) AS MIN_RATE
FROM HEALTH_PLAN_RATES
WHERE BILLING_CODE IS NOT NULL
GROUP BY BILLING_CODE_TYPE, DESCRIPTION, BILLING_CODE
ORDER BY TOTAL_OCCURRENCES DESC
LIMIT 10;
```

### Lowest Rates for a Specific Service (S5190)

```sql
SELECT DISTINCT
    h.BILLING_CODE,
    h.DESCRIPTION,
    pref.value::STRING AS PROVIDER_REFERENCE_ID,
    TRY_CAST(h.NEGOTIATED_RATE AS FLOAT) AS NEGOTIATED_RATE
FROM HEALTH_PLAN_RATES h,
LATERAL FLATTEN(input => h.PROVIDER_REFERENCES) AS pref
WHERE h.BILLING_CODE = 'S5190'
    AND pref.value IS NOT NULL
    AND h.NEGOTIATED_RATE IS NOT NULL
    AND TRY_CAST(h.NEGOTIATED_RATE AS FLOAT) > 0
ORDER BY TRY_CAST(h.NEGOTIATED_RATE AS FLOAT) ASC
LIMIT 10;
```

### Price Variation by Billing Code Type

```sql
SELECT
    BILLING_CODE_TYPE,
    COUNT(DISTINCT BILLING_CODE) AS UNIQUE_CODES,
    COUNT(*) AS TOTAL_RATES,
    AVG(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS AVG_RATE,
    STDDEV(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS RATE_STDDEV,
    MAX(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS MAX_RATE,
    MIN(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS MIN_RATE
FROM HEALTH_PLAN_RATES
WHERE NEGOTIATED_RATE IS NOT NULL
    AND TRY_CAST(NEGOTIATED_RATE AS FLOAT) > 0
GROUP BY BILLING_CODE_TYPE
ORDER BY TOTAL_RATES DESC;
```

### Services with Highest Price Variability

```sql
SELECT
    BILLING_CODE,
    BILLING_CODE_TYPE,
    DESCRIPTION,
    COUNT(*) AS NUM_RATES,
    AVG(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS AVG_RATE,
    MAX(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS MAX_RATE,
    MIN(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS MIN_RATE,
    MAX(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) - MIN(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS PRICE_RANGE,
    (MAX(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) - MIN(TRY_CAST(NEGOTIATED_RATE AS FLOAT))) /
        NULLIF(AVG(TRY_CAST(NEGOTIATED_RATE AS FLOAT)), 0) AS VARIATION_RATIO
FROM HEALTH_PLAN_RATES
WHERE NEGOTIATED_RATE IS NOT NULL
    AND TRY_CAST(NEGOTIATED_RATE AS FLOAT) > 0
    AND BILLING_CODE IS NOT NULL
GROUP BY BILLING_CODE, BILLING_CODE_TYPE, DESCRIPTION
HAVING COUNT(*) >= 10
ORDER BY PRICE_RANGE DESC
LIMIT 20;
```

### Join Rates with Provider Information

```sql
SELECT
    h.BILLING_CODE,
    h.DESCRIPTION,
    h.NEGOTIATED_RATE,
    pref.value::STRING AS PROVIDER_REFERENCE_ID,
    p.TIN_TYPE,
    p.TIN_VALUE,
    p.NPI
FROM HEALTH_PLAN_RATES h,
LATERAL FLATTEN(input => h.PROVIDER_REFERENCES) AS pref
JOIN PROVIDERS p
    ON p.PROVIDER_GROUP_ID = pref.value::STRING
WHERE h.BILLING_CODE IS NOT NULL
    AND TRY_CAST(h.NEGOTIATED_RATE AS FLOAT) > 0
LIMIT 100;
```

### Negotiation Types Distribution

```sql
SELECT
    NEGOTIATED_TYPE,
    NEGOTIATION_ARRANGEMENT,
    COUNT(*) AS TOTAL_COUNT,
    COUNT(DISTINCT BILLING_CODE) AS UNIQUE_BILLING_CODES,
    AVG(TRY_CAST(NEGOTIATED_RATE AS FLOAT)) AS AVG_RATE
FROM HEALTH_PLAN_RATES
WHERE NEGOTIATED_TYPE IS NOT NULL
GROUP BY NEGOTIATED_TYPE, NEGOTIATION_ARRANGEMENT
ORDER BY TOTAL_COUNT DESC;
```

### Provider TIN Distribution

```sql
SELECT
    TIN_TYPE,
    COUNT(*) AS PROVIDER_COUNT,
    COUNT(DISTINCT TIN_VALUE) AS UNIQUE_TINS,
    AVG(ARRAY_SIZE(NPI)) AS AVG_NPIS_PER_TIN
FROM PROVIDERS
GROUP BY TIN_TYPE
ORDER BY PROVIDER_COUNT DESC;
```

<!-- ------------------------ -->

## Scaling

Duration: 3

For larger MRF files (10+ GB), you can increase the number of runtime nodes to speed up processing:

1. In the Openflow Control Plane, go to the **Runtimes** tab
2. Click the three-dot menu next to your runtime and select **Edit**
3. Increase **Min/Max Nodes** (5-10 recommended for files larger than 10 GB)
4. Click **Apply**

### Sample MRF URLs

**Blue Cross Blue Shield of Illinois** (smaller, ~10 min):
```
https://app0004702110a5prdnc868.blob.core.windows.net/output/2025-07-18_Blue-Cross-and-Blue-Shield-of-Illinois_Blue-Options-or-Blue-Choice-Options_in-network-rates.json.gz
```

**UnitedHealthcare of Washington** (larger, ~9 hours with 5 nodes):
```
https://mrfstorageprod.blob.core.windows.net/public-mrf/2025-11-01/2025-11-01_UnitedHealthcare-of-Washington--Inc-_Insurer_Choice-EPO_561_in-network-rates.json.gz
```

<!-- ------------------------ -->

## Cleanup

Duration: 5

To remove all resources created by this quickstart, follow this order. You must clean up Openflow components before dropping SQL objects to avoid orphaned deployments.

### Step 1: Delete Runtime (Openflow UI)

1. In the Openflow Control Plane, go to the **Runtimes** tab
2. Click the three-dot menu next to the `price_transparency` runtime
3. Select **Suspend**, then wait for the runtime to reach Suspended state
4. Click the three-dot menu again and select **Delete**
5. Type `delete` to confirm and click **Delete runtime**
6. Wait for the runtime to fully disappear from the list

### Step 2: Delete Deployment (Openflow UI)

1. Go to the **Deployments** tab
2. Click the three-dot menu next to your deployment
3. Select **Delete**
4. Type `delete` to confirm and click **Delete deployment**
5. Wait for the deployment to disappear (approximately 5-10 minutes)

### Step 3: Drop SQL Objects

Run the following SQL after the runtime and deployment have been deleted:

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"price-transparency-files-ingestion-framework","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

DROP DATABASE IF EXISTS OPENFLOW_PRICE_TRANSPARENCY;

USE ROLE ACCOUNTADMIN;
DROP INTEGRATION IF EXISTS PRICE_TRANSPARENCY_INTEGRATION;
DROP NETWORK RULE IF EXISTS ALLOW_HEALTH_PAYER_STORAGE;

USE ROLE OPENFLOW_ADMIN;
DROP ROLE IF EXISTS OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY;

-- Optionally drop the Openflow Admin role if no longer needed:
-- USE ROLE ACCOUNTADMIN;
-- DROP ROLE IF EXISTS OPENFLOW_ADMIN;
```

### Verify Cleanup

```sql
SHOW DATABASES LIKE 'OPENFLOW_PRICE_TRANSPARENCY';
SHOW ROLES LIKE 'OPENFLOW_RUNTIME_ROLE_PRICE_TRANSPARENCY';
```

<!-- ------------------------ -->

## Troubleshooting

Duration: 3

### "Invalid channel" error on PutSnowpipeStreaming

This error is normal during initial writes. As long as data appears in the target tables, it can be safely ignored.

### Cannot log in to Openflow

Your default role is likely set to ACCOUNTADMIN. Change it to OPENFLOW_ADMIN:

```sql
ALTER USER YOUR_USERNAME SET DEFAULT_ROLE = OPENFLOW_ADMIN;
```

### "Snowflake (SPCS)" option missing when creating deployment

You must switch to the **OPENFLOW_ADMIN** role in the Openflow Control Plane UI header before clicking "Create deployment". Without this role, only "BYOC on AWS" appears.

### Network access errors in NiFi

Ensure the External Access Integration (`PRICE_TRANSPARENCY_INTEGRATION`) is attached to the runtime in the Openflow UI, not just created in SQL.

<!-- ------------------------ -->

## Conclusion

Duration: 1

In this quickstart, you built an end-to-end healthcare price transparency data pipeline using Snowflake Openflow. You created an Openflow deployment and runtime, imported NiFi flow definitions to parse deeply nested MRF JSON files, and streamed the results into Snowflake tables using Snowpipe Streaming. You then ran analytical queries to explore negotiated rates, identify price variability across services, and join rate data with provider information.

This solution demonstrates how Openflow makes it possible to process large, complex healthcare data files that would be difficult to handle with traditional ETL approaches, all within the Snowflake ecosystem.

### Related Resources

- [Blog Post: Processing Healthcare Price Transparency Files with Snowflake Openflow](https://medium.com/snowflake/processing-healthcare-price-transparency-files-with-snowflake-openflow-7413286dca6f)
- [Openflow Documentation](https://docs.snowflake.com/en/user-guide/data-integration/openflow/about)
- [CMS Price Transparency](https://www.cms.gov/priorities/key-initiatives/hospital-price-transparency)
- [GitHub Repository](https://github.com/Snowflake-Labs/sfguide-price-transparency-files-ingestion-framework-with-openflow)
