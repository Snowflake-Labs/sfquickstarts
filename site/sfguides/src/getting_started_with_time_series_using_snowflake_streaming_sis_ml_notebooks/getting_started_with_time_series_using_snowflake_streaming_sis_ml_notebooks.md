id: getting_started_with_time_series_using_snowflake_streaming_sis_ml_notebooks
summary: Getting Started with Time Series Analysis in Snowflake
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering
author: nathan.birch@snowflake.com, jonathan.regenstein@snowflake.com

# Getting Started with Time Series Analysis in Snowflake
<!-- ------------------------ -->
## Overview
Duration: 5

Snowflake has functionality built-in for ingesting, storing, and analyzing time series data. This guide will take you through a scenario of using Snowflake's Snowpipe Streaming to ingest a time series simulated stream, then utilize Dynamic tables to transform the ingested data from a raw JSON format into a model ready to analyze the data using Snowflake time series functions. Finally, a Streamlit applciation will be deployed to Snowflake to serve time series data to end users via an easy to use interface within Snowflake Snowsight.


### Key Activities

To achieve this goal, the following key activities will be performed:
- **Configure a Snowflake account** to work with time series data
- **Setup a streaming ingestion** client to to stream time series data into Snowflake using Snowpipe Streaming
- **Model and transform** the streaming time series data using Dynamic Tables
- **Analyze the data** using time series queries
- **Create a time series Snowpark functions** to assist in analysis
- **Deploy a time series Streamlit** application in Snowflake for end users to query time series


### Goal
The goal of this lab is to gain experience with Snowflake time series functionailty by working through an end-to-end deploy of a Streamlit application that will enable users to easily execute time series queries against data streamed into Snowflake.

<img src="assets/overview_streamlit.png" width="800" />


### Architecture Plan
A simulated IOT streaming datafeed will be used for this exercise, ingesting into a RAW staging table via Snowpark Streaming. Once data is streamed into a stage table, a task will detect when new records are loaded, and execute a procedure to transform the data into a dimensional model, ready for analytics. A Streamlit application will be deployed in Snowflake to then enable end users to report on the IOT streamed data.

<img src="assets/overview_architecture.png" width="800" />


<!-- ------------------------ -->
## Prerequisites

### Knowledge and Tooling

To participate in the virtual hands-on lab, attendees need the following:
- Familiarity with Snowflake, basic SQL knowledge, Snowsight UI and Snowflake objects
- Familiarity with command-line navigation within a terminal
- Access or sign-up to a [Snowflake Enterprise Account on preferred AWS region](https://signup.snowflake.com/?lab=getting_started_with_time_series_using_snowflake_streaming_sis_ml_notebooks&utm_cta=getting_started_with_time_series_using_snowflake_streaming_sis_ml_notebooks) with **ACCOUNTADMIN** access
- Access to a personal GitHub account to fork the QuickStart repo and create GitHub Codespace


### Lab environment
For this Quickstart we will be using [GitHub Codespaces](https://docs.github.com/en/codespaces/overview) for our development environment. Codespaces offer a hosted development environment with a hosted, web-based VS Code environment. At the time of writing, GitHub offers [free Codespace hours each month](https://github.com/features/codespaces) when using a 2 node environment, which should be enough to work through this lab.

> aside negative
> 
> It is recommended to use a personal GitHub account which will have permissions to deploy a GitHub Codespace.


### Snowflake Account details
Login to your Snowflake account using Snowsight and execute the [SYSTEM$ALLOWLIST](https://docs.snowflake.com/en/sql-reference/functions/system_allowlist) command:

```sql
-- Note down your Snowflake account identifier details
-- <account_identifier>.snowflakecomputing.com

SELECT SYSTEM$ALLOWLIST();
```

**Note** the **<account_identifier>**.snowflakecomputing.com by retrieving the **host** attribute returned. This will be used during the lab when referencing the **<ACCOUNT_IDENTIFIER>** configuration variables during setup.


<!-- ------------------------ -->
## Lab Setup

Duration: 10

### Step 1 - Fork the Lab GitHub Repository

The first step is to create a fork of the Lab GitHub repository.

1. In a web browser log into your [Github](https://github.com/) account.

2. Open [Getting Started with Time Series in Snowflake associated GitHub Repository](https://github.com/Snowflake-Labs/sfguide-getting-started-with-time-series-using-snowflake-streaming-sis-ml-notebooks). 
    - This repository contains all the code you need to successfully complete this Quickstart guide.

3. Click on the **"Fork"** button near the top right.

<img src="assets/labsetup_fork.png" width="800" />

4. Click **"Create Fork"**.

<img src="assets/labsetup_createfork.png" width="800" />


### Step 2 - Deploy a GitHub Codespace for the Lab

Now create the GitHub Codespace.

1. Click on the green `<> Code` button from the GitHub repository homepage. 

2. In the Code popup, click on the `Codespaces` tab.

3. Click `Create codespace on main`.

<img src="assets/labsetup_createcodespace.png" width="800" />

> aside positive
> 
> This will open a new browser window and begin **Setting up your codespace**. The Github Codespace deployment will take several minutes to setup the entire environment for this lab.
>

<img src="assets/labsetup_setupcodespace.png" width="800" />

> aside negative
>
> **Please wait** for the **postCreateCommand** to run.
>
> **Ignore any notifications** that may prompt to refresh the Codespace, these will disappear once the postCreateCommand has run.
>

<img src="assets/labsetup_postcreate.png" />


### Github Codespace Deployment Summary

Once complete you should see a hosted web-based version of **VS Code Integrated Development Environment (IDE)** in your browser with your forked repository.

<img src="assets/labsetup_vscode.png" width="800" />

The Github Codespace deployment is automating the following:
- Starting a hosted, web-based VS Code Integrated Development Environment (IDE)
- Pulling a copy of the forked Lab QuickStart GitHub repository within the VS Code container
- Installing Python Anaconda (conda) package management
- Installing a Java Runtime Environment (JRE)
- Creates an Anaconda virtual environment called **hol-timeseries** with required packages for the lab installed
  - Using the [Snowflake Anaconda Channel](https://repo.anaconda.com/pkgs/snowflake/)
  - Installs Snowflake Python packages
    - [Snowflake Snowpark Python library and connector](https://docs.snowflake.com/en/developer-guide/snowpark/index) package
    - [Snowflake Command Line Interface (CLI)](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/index)
- VS Code setup
  - Installing the [Snowflake VS Code Extension](https://docs.snowflake.com/en/user-guide/vscode-ext)
- Private key pair setup using OpenSSL to be used to connect to Snowflake
- Downloads and extracts a Java IOT streaming client application

> aside negative
>
> If you do not see the **Snowflake VS Code Extension** try **Refreshing** your browser window.


### Step 3 - Verify Your Anaconda Environment is Activated

During the Codespace setup the postCreateCommand script created an Anaconda virtual environment named **hol-timeseries**. This virtual environment contains the packages needed to connect and interact with Snowflake using the Snowflake CLI.

To activate the virtual environment:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

<img src="assets/labsetup_newterminal.png" />

2. Enter command `conda activate hol-timeseries`

<img src="assets/labsetup_condaactivate.png" />

The terminal prompt should now show a prefix `(hol-timeseries)` to confirm the **hol-timeseries** virtual environment is activated.


### Step 4 - Configure Snowflake Account Connection Configurations

> aside negative
>
> This section will require the Snowflake **<account_identifier>** noted earlier.
>
> **NOTE:** The account identifers entered will **NOT** include the **.snowflakecomputing.com** domain.

In VS Code navigate to the following files and replace **<ACCOUNT_IDENTIFER>** with your account identifer value:

1. `.snowflake/config.toml`
    - **account** variable for both connections 
2. `iotstream/snowflake.properties`
    - **account** variable
    - **host** variable


### Step 5 - Configure Snowflake VS Code Extension Connection

1. Open the Snowflake VS Code Extension
2. Enter your **<ACCOUNT_IDENTIFER>**
3. Click Continue

<img src="assets/labsetup_snowextension.png" />

1. For Auth Method select `Username/password`
2. Now enter the **ACCOUNTADMIN** user
3. Enter the ACCOUNTADMIN **password**
3. Click `Sign in`

<img src="assets/labsetup_snowsignin.png" />

> aside positive
>
> **The VS Code Snowflake Extension** should now be connected to your Snowflake.

<img src="assets/labsetup_snowconnected.png" />


### Step 6 - Update Snowflake Setup Worksheet

**Worksheets** have been provided for the next sections, these can be accessed by going to **VS Code Explorer** and expanding the `worksheets` folder.

<img src="assets/labsetup_worksheet1.png" />

> aside negative
>
> We'll need to update the setup worksheet with your **PUBLIC KEY** to be used during the initial Snowflake setup.


### Retrieve Snowflake Private Keypair
As part of the GitHub Codespace setup, an OpenSSL Private Keypair was generated in the VS Code `keys` directory.

Retrieve the **PUBLIC KEY** value from the `keys/rsa_key.pub` file. This will be need in the setup worksheet.

> aside negative
>
> Only the **PUBLIC KEY** value is required, which is the section between:
>
> `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----`
>
> ensure you **DO NOT** copy these lines.


### Update Snowflake Setup Worksheet with Lab Provisioned PUBLIC KEY
Open worksheet: `worksheets/hol_timeseries_1_setup.sql`

**Find and replace** the **<RSA_PUBLIC_KEY>** with the **PUBLIC KEY** retrieved from the `keys/rsa_key.pub` file.

<img src="assets/labsetup_rsakey.png" />

> aside positive
>
> The pasted **PUBLIC KEY** can show on mulitple lines and will work.

The **Snowflake setup** worksheets are now ready to run, and The Lab environment is now ready!


<!-- ------------------------ -->
## Setup Snowflake Resources
Duration: 5

Create the foundational Snowflake Objects for this lab.

This includes:
- Role: **ROLE_HOL_TIMESERIES** - role used for working throughout the lab
- User: **USER_HOL_TIMESERIES** - the user to connect to Snowflake
- Warehouses:
    - **HOL_TRANSFORM_WH** - warehouse used for transforming ingested data
    - **HOL_ANALYTICS_WH** - warehouse used for analytics
- Database: **HOL_TIMESERIES** - main database to store all lab objects
- Schemas:
    - **STAGING** - RAW data source landing schema
    - **TRANSFORM** - transformed and modelled data schema
    - **ANALYTICS** - serving and analytics functions schema

<img src="assets/snowsetup_architecture.png" />

### a) Run Snowflake Setup Worksheet

In the **GitHub Codespace VS Code** open worksheet: `worksheets/hol_timeseries_1_setup.sql`

**Run through the worksheet to get Snowflake resources created.**

> aside negative
> 
>  This section will run using the **ACCOUNTADMIN** login setup via **Snowflake VS Code Extension** connection.
> 
>  There are **EXTERNAL ACTIVITY** sections in the worksheet, these sections will be executed within the **GitHub Codespace**.
>

```sql
/*
SNOWFLAKE FOUNDATION SETUP SCRIPT
*/

-- Login and assume ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Create lab role
CREATE ROLE IF NOT EXISTS ROLE_HOL_TIMESERIES;
GRANT ROLE ROLE_HOL_TIMESERIES TO ROLE SYSADMIN;

-- Create lab user
CREATE OR REPLACE USER USER_HOL_TIMESERIES DEFAULT_ROLE = "ROLE_HOL_TIMESERIES"
COMMENT = "HOL Time Series user.";
GRANT ROLE ROLE_HOL_TIMESERIES TO USER USER_HOL_TIMESERIES;

/* EXTERNAL ACTIVITY

A public key is setup in Github Codespace VS Code environment "keys" folder

Retrieve the public key detail from keys/rsa_key.pub and replace <RSA_PUBLIC_KEY>
with the contents of the public key excluding
the -----BEGIN PUBLIC KEY----- and -----END PUBLIC KEY----- lines

*/

-- Assign lab user public key
ALTER USER USER_HOL_TIMESERIES SET RSA_PUBLIC_KEY='<RSA_PUBLIC_KEY>';

-- Setup HOL infrastructure objects
-- Assume the SYSADMIN role
USE ROLE SYSADMIN;

-- Create a TRANSFORM WH - used for ingest and transform activity
CREATE WAREHOUSE IF NOT EXISTS HOL_TRANSFORM_WH WITH WAREHOUSE_SIZE = XSMALL
AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
COMMENT = 'Transform Warehouse' ENABLE_QUERY_ACCELERATION = TRUE;

-- Create an Analytics WH = used for analytics and reporting
CREATE WAREHOUSE IF NOT EXISTS HOL_ANALYTICS_WH WITH WAREHOUSE_SIZE = XSMALL
AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE
COMMENT = 'Analytics Warehouse' ENABLE_QUERY_ACCELERATION = TRUE;


-- Create HOL Database
CREATE DATABASE IF NOT EXISTS HOL_TIMESERIES COMMENT = 'HOL Time Series database.';


-- HOL Schemas
-- Create STAGING schema - for RAW data
CREATE SCHEMA IF NOT EXISTS HOL_TIMESERIES.STAGING WITH MANAGED ACCESS
COMMENT = 'HOL Time Series STAGING schema.';

-- Create TRANSFORM schema - for modelled data
CREATE SCHEMA IF NOT EXISTS HOL_TIMESERIES.TRANSFORM WITH MANAGED ACCESS
COMMENT = 'HOL Time Series TRANSFORM schema.';

-- Create ANALYTICS schema - for serving analytics
CREATE SCHEMA IF NOT EXISTS HOL_TIMESERIES.ANALYTICS WITH MANAGED ACCESS
COMMENT = 'HOL Time Series ANALYTICS schema.';


-- Grant HOL role access to lab resources
-- Assign database grants to lab role
GRANT USAGE ON DATABASE HOL_TIMESERIES TO ROLE ROLE_HOL_TIMESERIES;

-- Assign Warehouse grants to lab role
GRANT ALL ON WAREHOUSE HOL_TRANSFORM_WH TO ROLE ROLE_HOL_TIMESERIES;

GRANT ALL ON WAREHOUSE HOL_ANALYTICS_WH TO ROLE ROLE_HOL_TIMESERIES;

-- Assign schema grants to lab role
GRANT ALL ON SCHEMA HOL_TIMESERIES.STAGING TO ROLE ROLE_HOL_TIMESERIES;

GRANT ALL ON SCHEMA HOL_TIMESERIES.TRANSFORM TO ROLE ROLE_HOL_TIMESERIES;

GRANT ALL ON SCHEMA HOL_TIMESERIES.ANALYTICS TO ROLE ROLE_HOL_TIMESERIES;

/*
SETUP SCRIPT NOW COMPLETED
*/
```

<!-- ------------------------ -->
## Snowpipe Streaming Ingestion
Duration: 5

Now that the foundational objects have been deployed, we can now deploy a staging table to load streaming time series data, and begin streaming time series data via a Snowpipe Streaming client.

<img src="assets/snowpipe_stagetable.png" />

### a) Create Streaming Staging Table

We'll create a stage loading table to stream RAW time series data into Snowflake. This will be located in the **STAGING** schema of the **HOL_TIMESERIES** database.

<img src="assets/snowpipe_stagetable.png" />

In the **GitHub Codespace VS Code** open worksheet: `worksheets/hol_timeseries_2_ingest.sql`

**Run through the worksheet to get Snowflake resources created.**

```sql
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE SCHEMA HOL_TIMESERIES.STAGING;
USE WAREHOUSE HOL_TRANSFORM_WH;

-- Setup staging tables
-- IOTSTREAM
CREATE OR REPLACE TABLE HOL_TIMESERIES.STAGING.RAW_TS_IOTSTREAM_DATA (
    RECORD_METADATA VARIANT,
    RECORD_CONTENT VARIANT
)
CHANGE_TRACKING = TRUE
COMMENT = 'IOTSTREAM staging table.'
;
```

> aside negative
> 
>  There is an **EXTERNAL ACTIVITY** sections in the worksheet, which will be executed within the **GitHub Codespace** terminal. Details in the next steps.
>

### Snowpipe Streaming Ingest Client SDK

Snowflake provides an [Ingest Client SDK](https://mvnrepository.com/artifact/net.snowflake/snowflake-ingest-sdk) in Java that allows applications, such as Kafka, to streaming rowset data into a Snowflake table at low latency.

<img src="assets/data-load-snowpipe-streaming.png" />

The Ingest Client SDK is configured with a secure connection to Snowflake, and will establish a streaming [Channel](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview#channels) between the client and a Snowflake table.

<img src="assets/data-load-snowpipe-streaming-client-channel.png" />

Now that a staging table is available to stream time series data. We can look at setting up a streaming connection channel with a Java Snowpipe Streaming client.

### b) Test Streaming Client Channel

In the **GitHub Codespace VS Code**:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

2. Change directory into to the **iotstream** folder: `cd iotstream`

3. Run the `Test.sh` script to confirm a table channel stream can be established with Snowflake.

```bash
./Test.sh
```

If successful, it will return:
`** Successfully Connected, Test complete! **`

4. Open the `worksheets/hol_timeseries_2_ingest.sql` **VS Code** worksheet run the `SHOW CHANNELS;` command to confirm a channel is open in Snowflake.

```sql
SHOW CHANNELS;
```

The query should return a single channel `CHACHANNEL_1_TEST` opened to the `RAW_TS_IOTSTREAM_DATA` table.

<img src="assets/snowpipe_channeltest.png" />

With the channel connection being successful, we can now look at loading the full historical set, as fast as the connection and machine will allow.

5. Back in the **VS Code** `Terminal` run the `Run_MAX.sh` script to load a month of IoT data.

```bash
./Run_MAX.sh
```


<!-- ------------------------ -->
## Data Modelling and Transformation
Duration: 2

Dynamic tables are new declarative way of defining your data pipeline in Snowflake. It's a new kind of Snowflake table which is defined as a query to continuously and automatically materialize the result of that query as a table. Dynamic Tables can join and aggregate across **multiple source objects** and **incrementally update** results as sources change. 

Dynamic Tables can also be chained together to create a DAG for more complex data pipelines. 

<img src="assets/dynamic_tables.png" />

Dynamic Tables are the building blocks for continuous data pipelines. They are the easiest way to build data transformation pipelines in snowflake across batch and streaming use cases. 


```sql
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.TRANSFORM;
USE WAREHOUSE HOL_TRANSFORM_WH;

-- Setup Transform Dynamic Tables
-- Sensor metadata (Dimension)
CREATE OR REPLACE DYNAMIC TABLE HOL_TIMESERIES.TRANSFORM.DT_TS_TAG_METADATA
TARGET_LAG = '1 MINUTE'
WAREHOUSE = HOL_TRANSFORM_WH
REFRESH_MODE = 'INCREMENTAL'
AS
SELECT
    SRC.RECORD_METADATA:headers:namespace::VARCHAR AS NAMESPACE,
    SRC.RECORD_METADATA:headers:source::VARCHAR AS TAGSOURCE,
    UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))) AS TAGNAME,
    SRC.RECORD_CONTENT:units::VARCHAR AS TAGUNITS,
    SRC.RECORD_CONTENT:datatype::VARCHAR AS TAGDATATYPE
FROM HOL_TIMESERIES.STAGING.RAW_TS_IOTSTREAM_DATA SRC
QUALIFY ROW_NUMBER() OVER (PARTITION BY UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))) ORDER BY SRC.RECORD_CONTENT:timestamp::VARCHAR::TIMESTAMP_NTZ, SRC.RECORD_METADATA:offset::NUMBER) = 1
;

-- Sensor readings (Fact)
CREATE OR REPLACE DYNAMIC TABLE HOL_TIMESERIES.TRANSFORM.DT_TS_TAG_READINGS
TARGET_LAG = '1 MINUTE'
WAREHOUSE = HOL_TRANSFORM_WH
REFRESH_MODE = 'INCREMENTAL'
AS
SELECT
    UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))) AS TAGNAME,
    DATE_TRUNC('SECOND', SRC.RECORD_CONTENT:timestamp::VARCHAR::TIMESTAMP_NTZ) AS TIMESTAMP,
    SRC.RECORD_CONTENT:value::VARCHAR AS VALUE,
    TRY_CAST(SRC.RECORD_CONTENT:value::VARCHAR AS FLOAT) AS VALUE_NUMERIC,
    SRC.RECORD_METADATA:partition::VARCHAR AS PARTITION,
    SRC.RECORD_METADATA:offset::VARCHAR AS OFFSET
FROM HOL_TIMESERIES.STAGING.RAW_TS_IOTSTREAM_DATA SRC
QUALIFY ROW_NUMBER() OVER (PARTITION BY UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))), DATE_TRUNC('SECOND', SRC.RECORD_CONTENT:timestamp::VARCHAR::TIMESTAMP_NTZ) ORDER BY SRC.RECORD_METADATA:offset::NUMBER) = 1;
```


<!-- ------------------------ -->
## Time Series Analysis
Duration: 2

Setup serving layer views

```sql
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.ANALYTICS;
USE WAREHOUSE HOL_ANALYTICS_WH;

-- Tag Reference View
CREATE OR REPLACE VIEW HOL_TIMESERIES.ANALYTICS.TS_TAG_REFERENCE AS
SELECT
    META.NAMESPACE,
    META.TAGSOURCE,
    META.TAGNAME,
    META.TAGUNITS,
    META.TAGDATATYPE
FROM HOL_TIMESERIES.TRANSFORM.DT_TS_TAG_METADATA META;

-- Tag Readings View
CREATE OR REPLACE VIEW HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS AS
SELECT
    READ.TAGNAME,
    READ.TIMESTAMP,
    READ.VALUE,
    READ.VALUE_NUMERIC
FROM HOL_TIMESERIES.TRANSFORM.DT_TS_TAG_READINGS READ;
```

Time Series queries

```sql
-- Run Time Series Analysis across various query profiles
-- RAW DATA
SELECT TAGNAME, TIMESTAMP, VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;

-- STATISTICAL
-- COUNT
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, COUNT(VALUE) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- COUNT DISTINCT
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, COUNT(DISTINCT VALUE) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- SUM
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, SUM(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS 
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- AVG
SELECT TAGNAME, TO_TIMESTAMP('2024-04-26 14:45:37') AS TIMESTAMP, AVG(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS 
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- STDDEV
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, STDDEV(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- VARIANCE
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, VARIANCE(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- MAX_BY - HI WATER
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, MAX_BY(VALUE, TIMESTAMP) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- MIN-BY - LOW WATER
SELECT TAGNAME, TO_TIMESTAMP('2024-01-01 00:00:30') AS TIMESTAMP, MIN_BY(VALUE, TIMESTAMP) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- DOWNSAMPLING / RESAMPLING
-- BINNING - PERCENTILE
SELECT TAGNAME, TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END') AS TIMESTAMP, APPROX_PERCENTILE(VALUE_NUMERIC, 0.5) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- BINNING - SUM
SELECT TAGNAME, TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END') AS TIMESTAMP, SUM(VALUE_NUMERIC) AS VALUE, COUNT(*) AS READING_COUNT
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- BINNING - AVERAGE
SELECT TAGNAME, TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END') AS TIMESTAMP, AVG(VALUE_NUMERIC) AS VALUE, COUNT(*) AS READING_COUNT
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;

-- BINNING - STDDEV
SELECT TAGNAME, TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END') AS TIMESTAMP, STDDEV(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;


-- WINDOW FUNCTIONS
-- LAG
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    LAG(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS PRIOR_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG101'
ORDER BY TAGNAME, TIMESTAMP
;

SET TIME_PERIODS = (SELECT TIMESTAMPDIFF('SECOND', '2024-01-01 00:00:00'::TIMESTAMP_NTZ, '2024-01-01 00:00:00'::TIMESTAMP_NTZ + INTERVAL '720 HOURS') / 5);

SELECT '2024-01-01 00:00:00'::TIMESTAMP_NTZ + INTERVAL '720 HOURS';

SELECT $TIME_PERIODS;

WITH TIMES AS (
    SELECT
    DATEADD('SECOND', ROW_NUMBER() OVER (ORDER BY SEQ8()), '2024-01-01')::TIMESTAMP_NTZ AS TIMESTAMP
    FROM TABLE(GENERATOR(ROWCOUNT => $TIME_PERIODS))
),
DATA AS (
    SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
    WHERE TIMESTAMP > '2024-01-01 00:00:00'
    AND TIMESTAMP <= '2024-01-31 00:00:00'
    AND TAGNAME = '/IOT/SENSOR/TAG101'
)
SELECT TIMES.TIMESTAMP, DATA.TAGNAME, DATA.VALUE,
    LAG(DATA.VALUE) IGNORE NULLS OVER (
        ORDER BY TIMES.TIMESTAMP) AS PRIOR_VALUE
FROM TIMES
LEFT JOIN DATA ON TIMES.TIMESTAMP = DATE_TRUNC('SECOND', DATA.TIMESTAMP)
ORDER BY TIMESTAMP;

WITH times AS (
    SELECT dateadd(sec, 5 * row_number() over (order by SEQ8()), '2022-07-01 01:05:25.000') AS timestamp
    FROM table(generator(rowcount => 518400)))
SELECT * FROM TIMES;

SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    LAG(VALUE_NUMERIC) IGNORE NULLS OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS PRIOR_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-31 00:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG101'
ORDER BY TAGNAME, TIMESTAMP
;

-- RANGE BETWEEN - ROW BASED
-- PRECEDING
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS ROLL_SUM_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-31 00:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;

-- FOLLOWING
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    AVG(VALUE_NUMERIC) OVER (PARTITION BY TAGNAME ORDER BY TIMESTAMP
    ROWS BETWEEN CURRENT ROW AND 5 FOLLOWING) AS ROLL_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-31 00:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;

-- RANGE BETWEEN INTERVAL - TIME BASED
-- PRECEEDING
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        RANGE BETWEEN INTERVAL '5 SEC' PRECEDING AND CURRENT ROW) AS PREC_ROLL_SUM_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-31 00:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;

-- FOLLOWING
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        RANGE BETWEEN CURRENT ROW AND INTERVAL '5 SEC' FOLLOWING) AS FOLL_ROLL_SUM_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-31 00:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;



-- FIRST_VALUE / LAST_VALUE
SELECT TAGNAME, TS AS TIMESTAMP, F_VALUE, L_VALUE
FROM (
SELECT TAGNAME, TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END') AS TS, TIMESTAMP, VALUE_NUMERIC, FIRST_VALUE(VALUE_NUMERIC) OVER (PARTITION BY TAGNAME, TS ORDER BY TIMESTAMP) AS F_VALUE, LAST_VALUE(VALUE_NUMERIC) OVER (PARTITION BY TAGNAME, TS ORDER BY TIMESTAMP) AS L_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:30'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(DATEADD(MILLISECOND, -1, TIMESTAMP), 10, 'SECOND', 'END'), TIMESTAMP, TAGNAME, VALUE_NUMERIC
)
GROUP BY TAGNAME, TS, F_VALUE, L_VALUE
ORDER BY TAGNAME, TS
;


-- ASOF JOIN
SELECT SMP.TAGNAME, SMP.TIMESTAMP, SMP.VALUE_NUMERIC AS VALUE, IOT.VALUE_NUMERIC AS IOT_VALUE, IOT.TAGNAME AS IOT_TAGNAME, IOT.TIMESTAMP AS IOT_TIMESTAMP
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS SMP
ASOF JOIN (
    SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC
    FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
    WHERE TAGNAME = '/IOT/SENSOR/TAG101'
    ) IOT
MATCH_CONDITION(SMP.TIMESTAMP >= IOT.TIMESTAMP)
WHERE SMP.TAGNAME = '/IOT/SENSOR/TAG301'
AND SMP.TIMESTAMP >= '2024-01-01 00:00:00'
AND SMP.TIMESTAMP < '2024-01-01 00:01:00'
ORDER BY SMP.TIMESTAMP;
```


<!-- ------------------------ -->
## Build Your Own - Snowpark User Defined Table Function
Duration: 2

Setup LTTB Downsample Function
```sql
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.ANALYTICS;
USE WAREHOUSE HOL_ANALYTICS_WH;

-- LTTB Downsampling Table Function
CREATE OR REPLACE FUNCTION HOL_TIMESERIES.ANALYTICS.FUNCTION_TS_LTTB (
    TIMESTAMP NUMBER,
    VALUE FLOAT,
    SIZE NUMBER
) 
RETURNS TABLE (
    TIMESTAMP NUMBER,
    VALUE FLOAT
)
LANGUAGE PYTHON
RUNTIME_VERSION = 3.11
PACKAGES = ('pandas', 'plotly-resampler')
HANDLER = 'lttb_run'
AS $$
from _snowflake import vectorized
import pandas as pd
from plotly_resampler.aggregation.algorithms.lttb_py import LTTB_core_py

class lttb_run:
    @vectorized(input=pd.DataFrame)

    def end_partition(self, df):
        if df.SIZE.iat[0] >= len(df.index):
            return df[['TIMESTAMP','VALUE']]
        else:
            idx = LTTB_core_py.downsample(
                df.TIMESTAMP.to_numpy(),
                df.VALUE.to_numpy(),
                n_out=df.SIZE.iat[0]
            )
            return df[['TIMESTAMP','VALUE']].iloc[idx]
$$;
```

LTTB Query
```sql
-- LTTB
SELECT data.tagname, lttb.timestamp::varchar::timestamp_ntz AS timestamp, NULL AS value, lttb.value_numeric 
FROM (
SELECT tagname, TIME_SLICE(DATEADD(MILLISECOND, -1, timestamp), 1, 'SECOND', 'END') AS timestamp, APPROX_PERCENTILE(value_numeric, 0.5) AS value_numeric 
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE timestamp > '2000-03-26 02:50:21' AND timestamp <= '2024-03-26 14:50:21' 
AND tagname IN ('/WITSML/NO 15/9-F-7/DEPTH') 
GROUP BY tagname, TIME_SLICE(DATEADD(MILLISECOND, -1, timestamp), 1, 'SECOND', 'END')
) AS data 
CROSS JOIN TABLE(HOL_TIMESERIES.ANALYTICS.function_ts_lttb(date_part(epoch_nanosecond, data.timestamp), data.value_numeric, 500) OVER (PARTITION BY data.tagname ORDER BY data.timestamp)) AS lttb
ORDER BY tagname, timestamp
;
```


<!-- ------------------------ -->
## Streamlit in Snowflake
Duration: 2

Deploy Streamlit application to Snowflake

```bash
snow --config-file=".snowflake/config.toml" streamlit deploy --replace --project "streamlit" --connection="hol-timeseries-streamlit"
```


<!-- ------------------------ -->
## Milestone

### Key Activities
- Ingest streaming time series data into Snowflake
- Created a data pipeline to transform streaming time series data
- Deployed ana analytics layer for serving time series data
- Delivered a Streamlit application interface for end users to run time series analytics

### Outcomes Achieved
- A standard ingestion pattern has been established for easy onboarding of time series data sources
- Unlocked low latency ingestion pipelines for data sources
- Delivered an easy user experience in Streamlit to derive insights and value from time series data


<!-- ------------------------ -->
## Streams and Tasks

> aside positive
> 
>  [Streams](https://docs.snowflake.com/en/user-guide/streams-intro) provides a change tracking mechanism for your tables and > views, enabling and ensuring "exactly once" semantics for new or changed data.
>
> [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro) are Snowflake objects to execute a single command, which could be simple SQL command or calling an extensive stored > > procedure.  Tasks can be scheduled or run on-demand, either within a Snowflake Virtual warehouse or serverless.



<!-- ------------------------ -->
## Clean-up
Duration: 1

- Remove [Github Codespace](https://github.com/codespaces)


<!-- ------------------------ -->
## Conclusion and Resources
Duration: 1


### What we've covered


### Additional resources
- [Getting Started with Snowflake CLI](https://quickstarts.snowflake.com/guide/getting-started-with-snowflake-cli/index.html)
- [Getting Started with Streams & Tasks](https://quickstarts.snowflake.com/guide/getting_started_with_streams_and_tasks/index.html)