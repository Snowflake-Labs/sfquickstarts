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

Snowflake offers a rich set of functionalities for time series analytics making it a performant and cost effective platform for bringing in your time series workloads. This lab covers a real world scenario of ingesting, analyzing and visualizing IOT time series data.


### What You'll Learn

Upon completing this quickstart, you will have learned how to perform time series analytics in Snowflake, and will have gained practical experience in several areas:

- **Setup a streaming ingestion** client to to stream time series data into Snowflake using Snowpipe Streaming
- **Model and transform** the streaming time series data using Dynamic Tables
- **Analyzing the data** using native time series functions
- **Building your own time series functions** using Snowpark UDFs when necessary
- **Deploying a Streamlit application** for visualizing and analyzing time series data

<img src="assets/overview_architecture.png" width="800" />


### What You'll Build

By the end of this lab you will have an **end-to-end streaming Time Series Analysis solution**, with a front-end application deployed using Streamlit in Snowflake.

<img src="assets/streamlit_video_summary.gif" />


### What You'll Need

- A supported Snowflake [Browser](https://docs.snowflake.com/en/user-guide/setup#browser-requirements)
- [Sign-up for a Snowflake Trial](https://signup.snowflake.com/?lab=getting_started_with_time_series_using_snowflake_streaming_sis_ml_notebooks&utm_cta=getting_started_with_time_series_using_snowflake_streaming_sis_ml_notebooks) OR have access to an existing Snowflake account with the ACCOUNTADMIN role. Select the Enterprise edition, AWS as a cloud provider.
- Access to a **personal [GitHub](https://github.com/signup) account** to fork the QuickStart repo and create [GitHub Codespaces](https://docs.github.com/en/codespaces/overview). Codespaces offer a hosted development environment. GitHub offers [free Codespace hours each month](https://github.com/features/codespaces) when using a 2 or 4 node environment, which should be enough to work through this lab.

> aside negative
> 
> It is recommended to use a personal GitHub account which will have permissions to deploy a GitHub Codespace.
>

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

> aside negative
>
> If you are seeing the message **Codespace access limited**, you may be logged into Github with an organization account. Please [Sign up to GitHub](https://github.com/signup) using a personal account and retry the **Lab Setup**.
>

<img src="assets/labsetup_codespace_limited.png" />

> aside positive
> 
> This will open a new browser window and begin **Setting up your codespace**. The Github Codespace deployment will take several minutes to set up the entire environment for this lab.
>

<img src="assets/labsetup_setupcodespace.png" width="800" />

> aside negative
>
> **Please wait** for the **postCreateCommand** to run. It may take 5-10 mins to fully deploy.
>
> **Ignore any notifications** that may prompt to refresh the Codespace, these will disappear once the postCreateCommand has run.
>

<img src="assets/labsetup_postcreate.png" />


### INFO: Github Codespace Deployment Summary

Once complete you should see a hosted web-based version of **VS Code Integrated Development Environment (IDE)** in your browser with your forked repository.

<img src="assets/labsetup_vscode.png" width="800" />

The Github Codespace deployment will contain all the resources needed to complete the lab.

> aside negative
>
> If you do not see the **Snowflake VS Code Extension** try **Refreshing** your browser window.
>

### Step 3 - Verify Your Anaconda Environment is Activated

During the Codespace setup the postCreateCommand script created an Anaconda virtual environment named **hol-timeseries**. This virtual environment contains the packages needed to connect and interact with Snowflake using the Snowflake CLI.

To activate the virtual environment:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

<img src="assets/labsetup_newterminal.png" />

2. Enter command `conda activate hol-timeseries`

<img src="assets/labsetup_condaactivate.png" />

<img src="assets/labsetup_condaactivated.png" />

The terminal prompt should now show a prefix `(hol-timeseries)` to confirm the **hol-timeseries** virtual environment is activated.


### Step 4 - Update Snowflake Account Connection Identifiers in Lab Files

1. Login to your Snowflake account using a browser 

2. From the menu expand `Projects > Worksheets`

<img src="assets/analysis_worksheets.png" />

3. At the top right of the **Worksheets** screen select `+ > SQL Worksheet`. This will open a new worksheet in Snowsight.

<img src="assets/analysis_newworksheet.png" />

4. **In the new worksheet**, execute the [SYSTEM$ALLOWLIST](https://docs.snowflake.com/en/sql-reference/functions/system_allowlist) command:

```sql
SELECT SYSTEM$ALLOWLIST();

-- Note down your Snowflake account identifier details
-- <account_identifier>.snowflakecomputing.com
```

5. In the results returned, below the command, **select the first row returned**, and **Copy** the **<account_identifier>**.snowflakecomputing.com for the **host** attribute returned, where the **type** is **"type":"SNOWFLAKE_DEPLOYMENT_REGIONLESS"**.

    - **Worksheet Output** for `SELECT SYSTEM$ALLOWLIST();`. **<account_identifier>** is in-front of `.snowflakecomputing.com`.

<img src="assets/labsetup_regionless.png" />

6. Back in **VS Code**, navigate to the following files and replace **<ACCOUNT_IDENTIFIER>** with your account identifier value:

* `.snowflake/config.toml`
    - **account** variable for **both** connections
 
* `iotstream/snowflake.properties`
    - **account** variable
    - **host** variable


### Step 5 - Configure Snowflake VS Code Extension Connection

1. Open the Snowflake VS Code Extension

<img src="assets/labsetup_vscodeextension.png" />

2. For **Account Identifier/URL**, enter your **<ACCOUNT_IDENTIFIER>**, **without** the `.snowflakecomputing.com`
3. Click Continue

<img src="assets/labsetup_snowextension.png" />

1. For Auth Method select `Username/password`
2. Now enter the **ACCOUNTADMIN** user
3. Enter the ACCOUNTADMIN **password**
3. Click `Sign in`

<img src="assets/labsetup_snowsignin.png" />

> aside positive
>
> **The VS Code Snowflake Extension** should now be connected to your Snowflake. **Once connected**, it will show a `Sign Out` button along with **Databases** and **Applications** in the `OBJECT EXPLORER` section.

<img src="assets/labsetup_snowconnected.png" />


### Step 6 - Expand Snowflake Worksheets Folder

**Worksheets** have been provided for the next sections, these can be accessed by going to **VS Code Explorer** and expanding the `worksheets` folder.

<img src="assets/labsetup_worksheet1.png" />

> aside negative
>
> We'll need to update the **setup worksheet** with your **PUBLIC KEY** to be used during the initial Snowflake setup.


### INFO: Retrieve Snowflake Private Key-Pair
As part of the GitHub Codespace setup, an OpenSSL Private Key-pair was generated in the VS Code `keys` directory.

Retrieve the **PUBLIC KEY** value from the `keys/rsa_key.pub` file. This will be needed in the setup worksheet.

> aside negative
>
> Only the **PUBLIC KEY** value is required, which is the section **between**
>
> `-----BEGIN PUBLIC KEY-----` and `-----END PUBLIC KEY-----`
>
> ensure you **DO NOT** copy these lines.


### Step 7 - Update Snowflake "Setup" Worksheet with Lab Provisioned PUBLIC KEY
1. Open worksheet: `worksheets/hol_timeseries_1_setup.sql`

2. **Find and replace** the **<RSA_PUBLIC_KEY>** with the **PUBLIC KEY** retrieved from the `keys/rsa_key.pub` file.

<img src="assets/labsetup_rsakey.png" />

**NOTE:** The pasted **PUBLIC KEY** can show on multiple lines and will work.

3. **NO NEED TO RUN** anything just yet, this is just setup, this worksheet will be run in the next section.

> aside positive
>
> The **Snowflake setup** worksheets are now ready to run, and The Lab environment is now ready!

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
    - **TRANSFORM** - transformed and modeled data schema
    - **ANALYTICS** - serving and analytics functions schema

<img src="assets/snowsetup_architecture.png" />


### Step 1 - Run Snowflake Setup Worksheet

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

-- Create TRANSFORM schema - for modeled data
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

> aside positive
> 
>  The Snowflake foundation objects have now been deployed, and we can continue on to set up a **Snowpipe Streaming Ingestion**.
>

<!-- ------------------------ -->
## Snowpipe Streaming Ingestion
Duration: 5

With the foundational objects setup, we can now deploy a staging table to stream time series data into Snowflake via a Snowpipe Streaming client.

For this lab a Java IOT Simulator Client application has been created to stream IoT sensor readings into Snowflake.

<img src="assets/snowpipe_streamingest.png" />


### Step 1 - Create Streaming Staging Table

We'll create a stage loading table to stream RAW time series data into Snowflake. This will be located in the **STAGING** schema of the **HOL_TIMESERIES** database.

<img src="assets/snowpipe_stagetable.png" />

In the **GitHub Codespace VS Code** open worksheet: `worksheets/hol_timeseries_2_ingest.sql`

1. Create the staging table to load IoT streaming data

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

The IoT data will be streamed into Snowflake in a similar [schema format as Kafka](https://docs.snowflake.com/en/user-guide/kafka-connector-overview#schema-of-tables-for-kafka-topics) which contains two columns:
- **RECORD_CONTENT** - This contains the Kafka message.
- **RECORD_METADATA** - This contains metadata about the message, for example, the topic from which the message was read.

> aside negative
> 
>  There is an **EXTERNAL ACTIVITY** section in the worksheet, which will be executed within the **GitHub Codespace** terminal. Details in the next steps.
>


### INFO: Snowpipe Streaming Ingest Client SDK

Snowflake provides an [Ingest Client SDK](https://mvnrepository.com/artifact/net.snowflake/snowflake-ingest-sdk) in Java that allows applications, such as Kafka, to stream rows of data into a Snowflake table at low latency.

<img src="assets/data-load-snowpipe-streaming.png" />

The Ingest Client SDK is configured with a secure JDBC connection to Snowflake, and will establish a streaming [Channel](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview#channels) between the client and a Snowflake table.

<img src="assets/data-load-snowpipe-streaming-client-channel.png" />


### Step 2 - Test Streaming Client Channel

Now that a staging table is available to stream time series data. We can look at setting up a streaming connection channel with a Java Snowpipe Streaming client. The simulator Java application is available in the `iotstream` folder of the lab, and can be run via a terminal with a Java runtime.

> aside positive
> 
>  The lab environment has been set up with a **Java Runtime** to execute the Java Snowpipe Streaming client application.
>

In the **GitHub Codespace VS Code**:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

<img src="assets/labsetup_newterminal.png" />

2. Change directory into to the **iotstream** folder: `cd iotstream`

3. Run the `Test.sh` script to confirm a table channel stream can be established with Snowflake.

```bash
./Test.sh
```

> aside positive
> 
> If **successful**, it will return:
> `** Successfully Connected, Test complete! **`
>
> This will confirm that the Java streaming client is able to connect to Snowflake, and is able to establish a channel to the target table.
>

4. In **VS Code** open the worksheet `worksheets/hol_timeseries_2_ingest.sql` and run the `SHOW CHANNELS` command to confirm a channel is now open to Snowflake.

```sql
SHOW CHANNELS;
```

The query should return a single channel `CHANNEL_1_TEST` opened to the `RAW_TS_IOTSTREAM_DATA` table.

<img src="assets/snowpipe_channeltest.png" />

With a channel now opened to the table we are ready to stream data into the table!


### Step 3 - Load a Simulated IoT Data Set

With the channel connection being successful, we can now load the IoT data set, as fast as the connection and machine will allow.

<img src="assets/snowpipe_streamingclient.png" />

The simulated IoT dataset contains six sensor device tags at different frequencies, within a single **namespace** called **"IOT"**.

| NAMESPACE | TAGNAME | FREQUENCY |
| --- | --- | --- |
| IOT | TAG101 | 5 SEC |
| IOT | TAG201 | 10 SEC |
| IOT | TAG301 | 1 SEC |
| IOT | TAG401 | 60 SEC |
| IOT | TAG501 | 60 SEC |
| IOT | TAG601 | 10 SEC |


1. In the **VS Code** `Terminal` run the `Run_MAX.sh` script to load the IoT data.

```bash
./Run_MAX.sh
```

> aside positive
> 
> The Java client application is being called using a Terminal shell script. The client accepts various speed parameters to change the number of rows that are streamed. The "MAX" script will send as many rows as the device will allow.
>

2. In **VS Code** open the worksheet `worksheets/hol_timeseries_2_ingest.sql` and view the streamed records.

```sql
-- Check stream table data
SELECT * FROM HOL_TIMESERIES.STAGING.RAW_TS_IOTSTREAM_DATA LIMIT 10;
```

- **RECORD_CONTENT** - This contains the IOT Tag reading.

<img src="assets/snowpipe_record_content.png" />

- **RECORD_METADATA** - This contains metadata about IOT Tag reading.

<img src="assets/snowpipe_record_meta.png" />

Each IoT device reading is a JSON payload, transmitted in the following Kafka like format:
```json
{
    "meta":
    {
        "LogAppendTime": "1714487166815",
        "headers":
        {
            "namespace": "IOT",
            "source": "STREAM_DATA.csv",
            "speed": "MAX"
        },
        "offset": "116",
        "partition": "1",
        "topic": "time-series"
    },
    "content":
    {
        "datatype": "double",
        "tagname": "SENSOR/TAG301",
        "timestamp": "1704067279",
        "units": "KPA",
        "value": "118.152"
    } 
}
```

> aside positive
> 
>  Data has now been **streamed into Snowflake**, and we can now look at modeling the data for analytics.
>

<!-- ------------------------ -->
## Data Modeling and Transformation
Duration: 5

Now that data has been streamed into Snowflake, we are ready for some **Data Engineering** activities to get the data into a report ready state for analytics. We'll be transforming the data from the **JSON VARIANT** format into a tabular format. Using Snowflake **Dynamic Tables**, the data streamed into Snowflake will continuously update the analytics layers.

Along with setting up Dynamic Tables for continuous loading, we'll also deploy some analytics views for the consumer serving layer. This will allow for specific columns of data to be exposed to the end users and applications.

<img src="assets/model_dataengineering.png" />


### INFO: Dynamic Tables

[Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-intro) are a declarative way of defining your data pipeline in Snowflake. It's a Snowflake table which is defined as a query to continuously and automatically materialize the result of that query as a table. Dynamic Tables can join and aggregate across **multiple source objects** and **incrementally update** results as sources change.

Dynamic Tables can also be chained together to create a DAG for more complex data pipelines.

<img src="assets/dynamic_tables.png" />


### Step 1 - Model Time Series Data with Dynamic Tables

For the IoT streaming data we'll setup two Dynamic Tables in a simple Dimension and Fact model:
- **DT_TS_TAG_METADATA (Dimension)**: Containing Tag Metadata such as tag names, sourcing, and data types
- **DT_TS_TAG_READINGS (Fact)**: Containing the readings from each IoT sensor in raw and numeric format

<img src="assets/model_dynamictables.png" />

In **VS Code** open the worksheet `worksheets/hol_timeseries_3_transform.sql` and run the **Dynamic Tables Setup** scripts.

```sql
-- Dynamic Tables Setup
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.TRANSFORM;
USE WAREHOUSE HOL_TRANSFORM_WH;

/* Tag metadata (Dimension)
TAGNAME - uppercase concatenation of namespace and tag name
QUALIFY - deduplication filter to only include unique tag names
*/
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
QUALIFY ROW_NUMBER() OVER (PARTITION BY UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))) ORDER BY SRC.RECORD_CONTENT:timestamp::NUMBER, SRC.RECORD_METADATA:offset::NUMBER) = 1
;

/* Tag readings (Fact)
TAGNAME - uppercase concatenation of namespace and tag name
QUALIFY - deduplication filter to only include unique tag readings based on tagname and timestamp
*/
CREATE OR REPLACE DYNAMIC TABLE HOL_TIMESERIES.TRANSFORM.DT_TS_TAG_READINGS
TARGET_LAG = '1 MINUTE'
WAREHOUSE = HOL_TRANSFORM_WH
REFRESH_MODE = 'INCREMENTAL'
AS
SELECT
    UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))) AS TAGNAME,
    SRC.RECORD_CONTENT:timestamp::VARCHAR::TIMESTAMP_NTZ AS TIMESTAMP,
    SRC.RECORD_CONTENT:value::VARCHAR AS VALUE,
    TRY_CAST(SRC.RECORD_CONTENT:value::VARCHAR AS FLOAT) AS VALUE_NUMERIC,
    SRC.RECORD_METADATA:partition::VARCHAR AS PARTITION,
    SRC.RECORD_METADATA:offset::VARCHAR AS OFFSET
FROM HOL_TIMESERIES.STAGING.RAW_TS_IOTSTREAM_DATA SRC
QUALIFY ROW_NUMBER() OVER (PARTITION BY UPPER(CONCAT('/', SRC.RECORD_METADATA:headers:namespace::VARCHAR, '/', TRIM(SRC.RECORD_CONTENT:tagname::VARCHAR))), SRC.RECORD_CONTENT:timestamp::NUMBER ORDER BY SRC.RECORD_METADATA:offset::NUMBER) = 1;
```

> aside positive
> 
>  **Dynamic Tables** have a [TARGET_LAG](https://docs.snowflake.com/en/user-guide/dynamic-tables-refresh#label-dynamic-tables-understand-dt-lag) parameter, which defines how out of date the data can be before a refresh is automatically triggered. In this case, we have configured the Dynamic Tables to have a TARGET_LAG of 1 minute. 
>


### Step 2 - Create Analytics Views for Consumers

The Dynamic Tables are now set up to continuously transform streaming data. We can now look at setting up an **Analytics** serving layer with some views for end users and applications to consume the streaming data.

<img src="assets/model_analyticviews.png" />

We'll create a set of analytics views similar to the Dynamic Tables with a subset of columns in the **ANALYTICS** schema:
- **TS_TAG_REFERENCE (Dimension)**: Containing Tag Metadata such as tag names, sourcing, and data types
- **TS_TAG_READINGS (Fact)**: Containing the readings from each IoT sensor in raw and numeric format

In **VS Code** open the worksheet `worksheets/hol_timeseries_3_transform.sql` and run the **Analytics Views Setup** scripts.

```sql
-- Analytics Views Setup
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

> aside positive
> 
>  Data is now **modeled in Snowflake** and available in the **ANALYTICS** schema, and we can now proceed to analyze the data using Snowflake time series functions.
>

<!-- ------------------------ -->
## Time Series Analysis
Duration: 15

Now that we have created the analytics views, we can start to query the data using Snowflake native time series functions.

<img src="assets/analysis_overview.png" />


### INFO - Time Series Query Profiles

The following query profiles will be covered in this section.

| **Query Profile** | **Functions** | **Description** |
| --- | --- | --- |
| Raw | Time Boundary: Left, Right, and Both | Raw data within a time range. |
| Math [Statistical Aggregates](https://docs.snowflake.com/en/sql-reference/functions-aggregation) | [MIN](https://docs.snowflake.com/en/sql-reference/functions/min), [MAX](https://docs.snowflake.com/en/sql-reference/functions/max), [AVG](https://docs.snowflake.com/en/sql-reference/functions/avg), [COUNT](https://docs.snowflake.com/en/sql-reference/functions/count), [SUM](https://docs.snowflake.com/en/sql-reference/functions/sum), [APPROX_PERCENTILE](https://docs.snowflake.com/en/sql-reference/functions/approx_percentile) | Mathematical calculations over values within a time range. |
| Distribution [Statistical Aggregates](https://docs.snowflake.com/en/sql-reference/functions-aggregation) | [STDDEV](https://docs.snowflake.com/en/sql-reference/functions/stddev), [VARIANCE](https://docs.snowflake.com/en/sql-reference/functions/variance), [KURTOSIS](https://docs.snowflake.com/en/sql-reference/functions/kurtosis), [SKEW](https://docs.snowflake.com/en/sql-reference/functions/skew) | Statistics on distributions of data. |
| [Window Functions](https://docs.snowflake.com/en/sql-reference/functions-analytic) | [LAG](https://docs.snowflake.com/en/sql-reference/functions/lag), [LEAD](https://docs.snowflake.com/en/sql-reference/functions/lead), [FIRST_VALUE](https://docs.snowflake.com/en/sql-reference/functions/first_value), [LAST_VALUE](https://docs.snowflake.com/en/sql-reference/functions/last_value), ROWS BETWEEN, RANGE BETWEEN | Functions over a group of related rows. |
| Time Gap Filling | [GENERATOR](https://docs.snowflake.com/en/sql-reference/functions/generator), [ROW_NUMBER](https://docs.snowflake.com/en/sql-reference/functions/row_number), [SEQ](https://docs.snowflake.com/en/sql-reference/functions/seq1) | Generating timestamps to fill time gaps. |
| Downsampling / Time Binning | [TIME_SLICE](https://docs.snowflake.com/en/sql-reference/functions/time_slice) | Time binning aggregations over time intervals. |
| Aligning time series datasets | [ASOF JOIN](https://docs.snowflake.com/en/sql-reference/constructs/asof-join) | Joining time series datasets when the timestamps don't match exactly, and interpolating values. |


### Step 1 - Copy Worksheet Content To Snowsight Worksheet

This section will be executed within a Snowflake Snowsight Worksheet.

1. Login to Snowflake, and from the menu expand `Projects > Worksheets`

<img src="assets/analysis_worksheets.png" />

2. At the top right of the **Worksheets** screen select `+ > SQL Worksheet`. This will open a new worksheet in Snowsight.

<img src="assets/analysis_newworksheet.png" />

3. In **VS Code** open the worksheet `worksheets/hol_timeseries_4_anaysis.sql`

4. **Copy** the contents of the worksheet to **clipboard**, and paste it into the newly created **Worksheet in Snowsight**


### Step 2 - Run the Snowsight Worksheet Time Series Analysis Queries


### Time Series Raw Query

We'll start with a simple **Raw** query that returns time series data between an input start time and end time.

```sql
-- RAW
SELECT TAGNAME, TIMESTAMP, VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:00:10'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;
```

**Raw Query**
<img src="assets/analysis_query_rawleft.png" />

### Time Series Statistical Aggregates

The following set of queries contains various [Aggregate Functions](https://docs.snowflake.com/en/sql-reference/functions-aggregation) covering **counts, math operations, distributions, and watermarks**.

**Counts**

Retrieve count and distinct counts within the time boundary.

```sql
/* COUNT AND COUNT DISTINCT
Retrieve counts within the time boundary
COUNT - Count of all values
COUNT DISTINCT - Count of unique values
Counts can work with both varchar and numeric data types
*/
SELECT TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP,
    COUNT(VALUE) AS COUNT_VALUE,
    COUNT(DISTINCT VALUE) AS COUNT_DISTINCT_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME
;
```

<img src="assets/analysis_query_aggcount.png" />

**Math Operations**



```sql
/* MIN/MAX/AVG/SUM/APPROX_PERCENTILE
Retrieve statistical aggregates for the readings within the time boundary
MIN - Minimum value
MAX - Maximum value
AVG - Average of values (mean)
SUM - Sum of values
PERCENTILE_50 - 50% of values are less than this
PERCENTILE_95 - 95% of values are less than this
Aggregates can work with numerical data types
*/
SELECT TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP,
    MIN(VALUE_NUMERIC) AS MIN_VALUE,
    MAX(VALUE_NUMERIC) AS MAX_VALUE,
    SUM(VALUE_NUMERIC) AS SUM_VALUE,
    AVG(VALUE_NUMERIC) AS AVG_VALUE,
    APPROX_PERCENTILE(VALUE_NUMERIC, 0.5) AS PERCENTILE_50_VALUE,
    APPROX_PERCENTILE(VALUE_NUMERIC, 0.95) AS PERCENTILE_95_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS 
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME
;
```

<img src="assets/analysis_query_aggminmaxavgsumperc.png" />

### INFO: Query Result Data Contract

The following **two** queries are written with a standard return set of columns, namely TAGNAME, TIMESTAMP, and VALUE. This is a way to structure your query results format if looking to build an API for time series data, similar to a data contract with consumers.

The TAGNAME is updated to show that a calculation has been applied to the returned values, and multiple aggregations can be grouped together using unions.

**Distribution Statistics**

```sql
/* DISTRIBUTIONS - sample distributions statistics
Retrieve distribution sample statistics within the time boundary
STDDEV - Closeness to the mean/average of the distribution
VARIANCE - Spread between numbers in the time boundary
KURTOSIS - Measure of outliers occuring
SKEW - Left (negative) and right (positive) distribution skew
Distributions can work with numerical data types
*/
SELECT TAGNAME || '~STDDEV_1HOUR' AS TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP, STDDEV(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
UNION ALL
SELECT TAGNAME || '~VARIANCE_1HOUR' AS TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP, VARIANCE(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
UNION ALL
SELECT TAGNAME || '~KURTOSIS_1HOUR' AS TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP, KURTOSIS(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
UNION ALL
SELECT TAGNAME || '~SKEW_1HOUR' AS TAGNAME, TO_TIMESTAMP_NTZ('2024-01-01 01:00:00') AS TIMESTAMP, SKEW(VALUE_NUMERIC) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME
;
```

<img src="assets/analysis_query_aggdistributions.png" />

**Watermarks**

```sql
/* WATERMARKS
Retrieve both the high and low watermark readings within the time boundary
MAX_BY - High Watermark - latest reading in the time boundary
MIN_BY - Low Watermark - earliest reading in the time boundary
*/ 
SELECT TAGNAME || '~MAX_BY_1HOUR' AS TAGNAME, MAX_BY(TIMESTAMP, TIMESTAMP) AS TIMESTAMP, MAX_BY(VALUE, TIMESTAMP) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
UNION ALL
SELECT TAGNAME || '~MIN_BY_1HOUR' AS TAGNAME, MIN_BY(TIMESTAMP, TIMESTAMP) AS TIMESTAMP, MIN_BY(VALUE, TIMESTAMP) AS VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 01:00:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TAGNAME
ORDER BY TAGNAME
;
```

<img src="assets/analysis_query_aggwatermark.png" />


### Time Series Window Functions

[Window Functions](https://docs.snowflake.com/en/sql-reference/functions-analytic) enable aggregates to operate over groups of data, looking forward and backwards in the data rows, and returning a single result for each group.

**Lag and Lead**



```sql
/* WINDOW FUNCTIONS
LAG - Prior time period value
LEAD - Next time period value
*/
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    LAG(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS LAG_VALUE,
    LEAD(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS LEAD_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:00:10'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_windowlaglead.png" />

**Rows Between - Preceding**
```sql
/* ROWS BETWEEN
ROW_SUM_PRECEDING - Rolling sum from 5 preceding rows and current row
ROW_SUM_FOLLOWING - Rolling sum from current row and 5 following rows
*/
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        ROWS BETWEEN 5 PRECEDING AND CURRENT ROW) AS ROW_SUM_PRECEDING,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        ROWS BETWEEN CURRENT ROW AND 5 FOLLOWING) AS ROW_SUM_FOLLOWING
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:00:10'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_windowrowsbetween.png" />

**Range Between - Preceding and Following**
```sql
/* RANGE BETWEEN
INTERVAL - Natural time input intervals
*/
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        RANGE BETWEEN INTERVAL '5 SEC' PRECEDING AND CURRENT ROW) AS RANGE_SUM_PRECEDING,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        RANGE BETWEEN CURRENT ROW AND INTERVAL '5 SEC' FOLLOWING) AS RANGE_SUM_FOLLOWING
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:00:10'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_windowrangebetween.png" />

> aside positive
> 
>  **RANGE BETWEEN** differs from **ROWS BETWEEN** in that it can handle gaps between **INTERVALS** of time or where the reporting frequency differs from the data frequency, for example data at 10 second frequency that you want to aggregate the prior 25 seconds.
>
> <img src="assets/analysis_info_range_between.png" />
>

**Range Between - 10 sec frequency tag with 25 sec preceding sum**
```sql
/* RANGE BETWEEN
INTERVAL - 10 second tag with 25 seconds preceding SUM
*/
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    SUM(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP
        RANGE BETWEEN INTERVAL '25 SEC' PRECEDING AND CURRENT ROW) AS RANGE_SUM_PRECEDING
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP > '2024-01-01 00:00:00'
AND TIMESTAMP <= '2024-01-01 00:01:40'
AND TAGNAME = '/IOT/SENSOR/TAG201'
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_windowrangebetween_gap.png" />

**First and Last Value**
```sql
/* FIRST_VALUE AND LAST_VALUE
FIRST_VALUE - First value in the time boundary
LAST_VALUE - Last value in the time boundary
*/
SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE, 
    FIRST_VALUE(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS FIRST_VALUE,
    LAST_VALUE(VALUE_NUMERIC) OVER (
        PARTITION BY TAGNAME ORDER BY TIMESTAMP) AS LAST_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:00:10'
AND TAGNAME = '/IOT/SENSOR/TAG301'
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_windowfirstlast.png" />


### Time Series Gap Filling

Time gap filling is the process of generating timestamps for given a start and end time boundary, and joining to a tag with less frequent timestamp values.

```sql
/* TIME GAP FILLING
TIME_PERIODS - variable passed into query to determine time stamps generated for gap filling
*/
SET TIME_PERIODS = (SELECT TIMESTAMPDIFF('SECOND', '2024-01-01 00:00:00'::TIMESTAMP_NTZ, '2024-01-01 00:00:00'::TIMESTAMP_NTZ + INTERVAL '1 MINUTE'));

-- LAST OBSERVED VALUE CARRIED FORWARD (LOCF) - IGNORE NULLS
WITH TIMES AS (
    SELECT
    DATEADD('SECOND', ROW_NUMBER() OVER (ORDER BY SEQ8()) - 1, '2024-01-01')::TIMESTAMP_NTZ AS TIMESTAMP
    FROM TABLE(GENERATOR(ROWCOUNT => $TIME_PERIODS))
),
DATA AS (
    SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC AS VALUE,
    FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
    WHERE TIMESTAMP >= '2024-01-01 00:00:00'
    AND TIMESTAMP < '2024-01-01 00:01:00'
    AND TAGNAME = '/IOT/SENSOR/TAG101'
)
SELECT TIMES.TIMESTAMP,
    A.TAGNAME AS TAGNAME,
    B.VALUE,
    A.VALUE AS LOCF_VALUE
FROM TIMES
LEFT JOIN DATA B ON TIMES.TIMESTAMP = B.TIMESTAMP
ASOF JOIN DATA A MATCH_CONDITION(TIMES.TIMESTAMP >= A.TIMESTAMP)
ORDER BY TAGNAME, TIMESTAMP;
```

**Lag - LOCF - ASOF Join**

<img src="assets/analysis_query_gapfill_locf.png" />


### Downsampling Time Series Data

Downsampling is used to decrease the frequency of time samples, such as from seconds to minutes, by placing time series data into fixed time intervals using aggregate operations on the existing values within each time interval.

**Time Binning - 1 min Aggregate - START Label**
```sql
/* TIME BINNING - 1 min AGGREGATE with START label
Create a downsampled time series data set with 1 minute aggregates, showing the START timestamp label of the interval
COUNT - Count of values within the time bin
SUM - Sum of values within the time bin
AVG - Average of values (mean) within the time bin
PERCENTILE_95 - 95% of values are less than this within the time bin
*/
SELECT TAGNAME, TIME_SLICE(TIMESTAMP, 1, 'MINUTE', 'START') AS TIMESTAMP,
    COUNT(*) AS COUNT_VALUE,
    SUM(VALUE_NUMERIC) AS SUM_VALUE,
    AVG(VALUE_NUMERIC) AS AVG_VALUE,
    APPROX_PERCENTILE(VALUE_NUMERIC, 0.95) AS PERCENTILE_95_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:10:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(TIMESTAMP, 1, 'MINUTE', 'START'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_timebin_start.png" />

**Time Binning - 1 min Aggregate - END Label**
```sql
/* TIME BINNING - 1 min AGGREGATE with END label
Same as before, but now showing the END timestamp label of the interval
COUNT - Count of values within the time bin
SUM - Sum of values within the time bin
AVG - Average of values (mean) within the time bin
PERCENTILE_95 - 95% of values are less than this within the time bin
*/
SELECT TAGNAME, TIME_SLICE(TIMESTAMP, 1, 'MINUTE', 'END') AS TIMESTAMP,
    COUNT(*) AS COUNT_VALUE,
    SUM(VALUE_NUMERIC) AS SUM_VALUE,
    AVG(VALUE_NUMERIC) AS AVG_VALUE,
    APPROX_PERCENTILE(VALUE_NUMERIC, 0.95) AS PERCENTILE_95_VALUE
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
WHERE TIMESTAMP >= '2024-01-01 00:00:00'
AND TIMESTAMP < '2024-01-01 00:10:00'
AND TAGNAME = '/IOT/SENSOR/TAG301'
GROUP BY TIME_SLICE(TIMESTAMP, 1, 'MINUTE', 'END'), TAGNAME
ORDER BY TAGNAME, TIMESTAMP
;
```

<img src="assets/analysis_query_timebin_end.png" />


### Aligning Time Series Data

Often you will need to align two data sets that may have differing time frequencies. To do this you can utilize the Time Series ASOF join to pair closely matching records based on timestamps.

```sql
/* ASOF JOIN - Align a 1 second tag with a 5 second tag
Using the ASOF JOIN two data sets can be aligned by applying a matching condition to pair closely aligned timestamps and values.
*/
SELECT ONE_SEC.TAGNAME AS ONE_SEC_TAGNAME, ONE_SEC.TIMESTAMP AS ONE_SEC_TIMESTAMP, ONE_SEC.VALUE_NUMERIC AS ONE_SEC_VALUE, FIVE_SEC.VALUE_NUMERIC AS FIVE_SEC_VALUE, FIVE_SEC.TAGNAME AS FIVE_SEC_TAGNAME, FIVE_SEC.TIMESTAMP AS FIVE_SEC_TIMESTAMP
FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS ONE_SEC
ASOF JOIN (
    -- 5 sec tag data
    SELECT TAGNAME, TIMESTAMP, VALUE_NUMERIC
    FROM HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS
    WHERE TAGNAME = '/IOT/SENSOR/TAG101'
    ) FIVE_SEC
MATCH_CONDITION(ONE_SEC.TIMESTAMP >= FIVE_SEC.TIMESTAMP)
WHERE ONE_SEC.TAGNAME = '/IOT/SENSOR/TAG301'
AND ONE_SEC.TIMESTAMP >= '2024-01-01 00:00:00'
AND ONE_SEC.TIMESTAMP < '2024-01-01 00:01:00'
ORDER BY ONE_SEC.TIMESTAMP;
```

<img src="assets/analysis_query_asof_align.png" />

> aside positive
> 
>  You have now run through several **Time Series Analysis** queries, we can now look at creating Time Series Functions.
>

<!-- ------------------------ -->
## Build Your Own Time Series Functions
Duration: 5

Now that you have a great understanding of running Time Series Analysis, we will now look at deploying time series [User Defined Table Functions (UDTF)](https://docs.snowflake.com/en/developer-guide/udf/udf-overview) that can query time series data in a re-usable manner. Table functions will accept a set of input parameters, and will operate and return data in a table format.

<img src="assets/byo_functions.png" />


### INFO: Upsampling Time Series Data

Upsampling is used to increase the frequency of time samples, such as from hours to minutes, by placing time series data into fixed time intervals using aggregate operations on the values within each time interval. Due to the frequency of samples being increased it has the effect of creating new values if the interval is more frequent than the data itself. If the interval does not contain a value, it will be interpolated from the surrounding aggregated data.

### Step 1 - Deploy Time Series Functions and Procedures

1. In **VS Code** open the worksheet `worksheets/hol_timeseries_5_functions.sql`

2. Run the **Create Interpolate Table Function**

```sql
-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.ANALYTICS;
USE WAREHOUSE HOL_ANALYTICS_WH;

-- Create Interpolate Table Function
CREATE OR REPLACE FUNCTION HOL_TIMESERIES.ANALYTICS.FUNCTION_TS_INTERPOLATE (
    V_TAGLIST VARCHAR,
    V_START_TIMESTAMP TIMESTAMP_NTZ,
    V_INTERVAL NUMBER,
    V_BUCKETS NUMBER
)
RETURNS TABLE (
    TIMESTAMP TIMESTAMP_NTZ,
    TAGNAME VARCHAR,
    INTERP_VALUE FLOAT,
    LOCF_VALUE FLOAT,
    LAST_TIMESTAMP TIMESTAMP_NTZ
)
LANGUAGE SQL
AS
$$
WITH
TSTAMPS AS (
    SELECT 
        DATEADD('SEC', V_INTERVAL * ROW_NUMBER() OVER (ORDER BY SEQ8()) - V_INTERVAL, V_START_TIMESTAMP) AS TIMESTAMP
    FROM TABLE(GENERATOR(ROWCOUNT => V_BUCKETS))
),
TAGLIST AS (
    SELECT
        TRIM(TAGLIST.VALUE) AS TAGNAME
    FROM
        TABLE(SPLIT_TO_TABLE(V_TAGLIST, ',')) TAGLIST
),
TIMES AS (
    SELECT
        TSTAMPS.TIMESTAMP,
        TAGLIST.TAGNAME
    FROM
        TSTAMPS
        CROSS JOIN TAGLIST
),
LAST_VALUE AS (
    SELECT
        TIMES.TIMESTAMP,
        RAW_DATA.TIMESTAMP RAW_TS,
        RAW_DATA.TAGNAME,
        RAW_DATA.VALUE_NUMERIC
    FROM
        TIMES ASOF JOIN HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS RAW_DATA
            MATCH_CONDITION(TIMES.TIMESTAMP >= RAW_DATA.TIMESTAMP)
            ON TIMES.TAGNAME = RAW_DATA.TAGNAME
),
NEXT_VALUE AS (
    SELECT
        TIMES.TIMESTAMP,
        RAW_DATA.TIMESTAMP RAW_TS,
        RAW_DATA.TAGNAME,
        RAW_DATA.VALUE_NUMERIC
    FROM
        TIMES ASOF JOIN HOL_TIMESERIES.ANALYTICS.TS_TAG_READINGS RAW_DATA
            MATCH_CONDITION(TIMES.TIMESTAMP < RAW_DATA.TIMESTAMP)
            ON TIMES.TAGNAME = RAW_DATA.TAGNAME
),
COMB_VALUES AS (
    SELECT
        TIMES.TIMESTAMP,
        TIMES.TAGNAME,
        LV.VALUE_NUMERIC LAST_VAL,
        LV.TIMESTAMP LV_TS,
        LV.RAW_TS LV_RAW_TS,
        NV.VALUE_NUMERIC NEXT_VAL,
        NV.TIMESTAMP NV_TS,
        NV.RAW_TS NV_RAW_TS
    FROM TIMES
    INNER JOIN LAST_VALUE LV ON TIMES.TIMESTAMP = LV.TIMESTAMP AND TIMES.TAGNAME = LV.TAGNAME
    INNER JOIN NEXT_VALUE NV ON TIMES.TIMESTAMP = NV.TIMESTAMP AND TIMES.TAGNAME = NV.TAGNAME
),
INTERP AS (
    SELECT
        TIMESTAMP,
        TAGNAME,
        TIMESTAMPDIFF(SECOND, LV_RAW_TS, NV_RAW_TS) TDIF_BASE,
        TIMESTAMPDIFF(SECOND, LV_RAW_TS, TIMESTAMP) TDIF,
        LV_TS,
        NV_TS,
        LV_RAW_TS,
        LAST_VAL,
        NEXT_VAL,
        DECODE(TDIF, 0, LAST_VAL, LAST_VAL + (NEXT_VAL - LAST_VAL) / TDIF_BASE * TDIF) IVAL
    FROM
        COMB_VALUES
)
SELECT
    TIMESTAMP,
    TAGNAME,
    IVAL INTERP_VALUE,
    LAST_VAL LOCF_VALUE,
    LV_RAW_TS LAST_TIMESTAMP
FROM
    INTERP
$$
;
```

> aside positive
> 
>  The **INTERPOLATE Table Function** is using the [ASOF JOIN](https://docs.snowflake.com/en/sql-reference/constructs/asof-join) for each time interval to look both backwards (LAST_VALUE) and forwards (NEXT_VALUE) in time, to calculate the time and value difference at each time interval, which is then used to generate a smooth linear interpolated value.
>
> The **INTERPOLATE Table Function** will return both **linear interpolated values** and the **last observed value carried forward (LOCF)**.
>

3. Run the **Create Interpolate Procedure** Script

```sql
-- Add helper procedure to accept start and end times, and return either LOCF or Linear Interpolated Values
CREATE OR REPLACE PROCEDURE HOL_TIMESERIES.ANALYTICS.PROCEDURE_TS_INTERPOLATE_LIN (
    V_TAGLIST VARCHAR,
    V_FROM_TIME TIMESTAMP_NTZ,
    V_TO_TIME TIMESTAMP_NTZ,
    V_INTERVAL NUMBER,
    V_INTERP_TYPE VARCHAR
)
RETURNS TABLE (
    TIMESTAMP TIMESTAMP_NTZ,
    TAGNAME VARCHAR,
    VALUE FLOAT
)
LANGUAGE SQL
AS
$$
DECLARE
TIME_BUCKETS NUMBER;
RES RESULTSET;
BEGIN
    TIME_BUCKETS := (TIMESTAMPDIFF('SEC', :V_FROM_TIME, :V_TO_TIME) / :V_INTERVAL);

    IF (:V_INTERP_TYPE = 'LOCF') THEN
        RES := (SELECT TIMESTAMP, TAGNAME, LOCF_VALUE AS VALUE FROM TABLE(HOL_TIMESERIES.ANALYTICS.FUNCTION_TS_INTERPOLATE(:V_TAGLIST, :V_FROM_TIME, :V_INTERVAL, :TIME_BUCKETS)) ORDER BY TAGNAME, TIMESTAMP);
    ELSE
        RES := (SELECT TIMESTAMP, TAGNAME, INTERP_VALUE AS VALUE FROM TABLE(HOL_TIMESERIES.ANALYTICS.FUNCTION_TS_INTERPOLATE(:V_TAGLIST, :V_FROM_TIME, :V_INTERVAL, :TIME_BUCKETS)) ORDER BY TAGNAME, TIMESTAMP);
    END IF;

    RETURN TABLE(RES);
END;
$$
;
```

> aside positive
> 
>  The **INTERPOLATE PROCEDURE** can calculate the number of time buckets within a time boundary based on the interval specified. It then calls the **INTERPOLATE** table function, and depending on the **V_INTERP_TYPE** variable, it will return the last observed value carried forward (LOCF) or linear interpolated values (default).
>

4. Run the **LTTB Downsampling Table Function** Script

```sql
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

> aside positive
> 
>  The **Largest Triangle Three Buckets (LTTB)** algorithm is a time series downsampling algorithm that reduces the number of visual data points, whilst retaining the shape and variability of the time series data. It's useful for reducing large time series data sets for charting purposes where the consumer system may have reduced memory resources.
>
> This is a **Snowpark Python** implementation using the **plotly-resampler** package.
>
> The original code for LTTB is available at [Sveinn Steinarsson - GitHub](https://github.com/sveinn-steinarsson/flot-downsample).
>

### Step 2 - Copy Worksheet Content To Snowsight Worksheet

This section will be executed within a Snowflake Snowsight Worksheet.

1. Login to Snowflake, and from the menu expand `Projects > Worksheets`

<img src="assets/analysis_worksheets.png" />

2. At the top right of the **Worksheets** screen select `+ > SQL Worksheet`. This will open a new worksheet in Snowsight.

<img src="assets/analysis_newworksheet.png" />

3. In **VS Code** open the worksheet `worksheets/hol_timeseries_6_function_queries.sql`

4. **Copy** the contents of the worksheet to **clipboard**, and paste it into the newly created **Worksheet in Snowsight**


### Step 3 - Query Time Series Data Using Deployed Functions and Procedures

Interpolate Query
```sql
-- Directly Call Interpolate Table Function
SELECT * FROM TABLE(HOL_TIMESERIES.ANALYTICS.FUNCTION_TS_INTERPOLATE('/IOT/SENSOR/TAG401', '2024-01-01 01:05:23'::TIMESTAMP_NTZ, 5, 100)) ORDER BY TAGNAME, TIMESTAMP;
```

LOCF Interpolate Query
```sql
-- Call Interpolate Procedure with Taglist, Start Time, End Time, and Intervals
CALL HOL_TIMESERIES.ANALYTICS.PROCEDURE_TS_INTERPOLATE_LIN(
    -- V_TAGLIST
    '/IOT/SENSOR/TAG401',
    -- V_FROM_TIME
    '2024-01-01 01:05:00',
    -- V_TO_TIME
    '2024-01-01 03:05:00',
    -- V_INTERVAL
    10,
    -- V_INTERP_TYPE
    'LOCF'
);
```

Linear Interpolate Query
```sql
-- Call Interpolate Procedure with Taglist, Start Time, End Time, and Intervals
CALL HOL_TIMESERIES.ANALYTICS.PROCEDURE_TS_INTERPOLATE_LIN(
    -- V_TAGLIST
    '/IOT/SENSOR/TAG401',
    -- V_FROM_TIME
    '2024-01-01 01:05:00',
    -- V_TO_TIME
    '2024-01-01 03:05:00',
    -- V_INTERVAL
    10,
    -- V_INTERP_TYPE
    'LINEAR'
);
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

> aside positive
> 
>  You have now built your own **Time Series Analysis** functions and procedures, these can be called within applications working with time series data. We can now look at deploying a Time Series application.
>

<!-- ------------------------ -->
## Build Your Time Series Application in Streamlit
Duration: 10

After completing the analysis of the time series data that was streamed into Snowflake, we are now ready to deliver an analytics application for end users to easily consume time series data. For this purpose we are going to use Streamlit.

<img src="assets/streamlit_overview.png" />


### INFO: Streamlit
Streamlit is an open-source Python library that makes it easy to create web applications for machine learning, data analysis, and visualization. [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit) helps developers securely build, deploy, and share Streamlit apps on Snowflake’s data cloud, without moving data or application code to an external system.


### INFO: Snowflake CLI

[Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/introduction/introduction) is an open-source command-line tool explicitly designed for developers to create, manage, update, and view apps running on Snowflake. We will use Snowflake CLI to deploy the Streamlit app to your Snowflake account.

### Step 1 - Setup Snowflake Stage for Streamlit Application

1. In **VS Code** open the worksheet `worksheets/hol_timeseries_7_streamlit.sql`

2. Run the Worksheet to **create a stage for the Streamlit** application

```sql
/*
SNOWFLAKE STREAMLIT SCRIPT
*/

-- Set role, context, and warehouse
USE ROLE ROLE_HOL_TIMESERIES;
USE HOL_TIMESERIES.ANALYTICS;
USE WAREHOUSE HOL_ANALYTICS_WH;

-- CREATE STAGE FOR STREAMLIT FILES
CREATE OR REPLACE STAGE HOL_TIMESERIES.ANALYTICS.STAGE_TS_STREAMLIT
DIRECTORY = (ENABLE = TRUE, REFRESH_ON_CREATE = TRUE)
ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

/* EXTERNAL ACTIVITY

Use Snowflake CLI to upload Streamlit app

*/

/*
STREAMLIT SCRIPT COMPLETED
*/
```

> aside negative
> 
>  There are **EXTERNAL ACTIVITY** sections in the worksheet, this will be covered in the next step.
>


### Step 2 - Deploy Streamlit Application to Snowflake

In this step, we will now deploy the Streamlit application on the Snowflake account using Snowflake CLI.

In the **GitHub Codespace VS Code**:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

<img src="assets/labsetup_newterminal.png" />

2. Activate `hol-timeseries` python virtual environment by running `conda activate hol-timeseries`

```bash
conda activate hol-timeseries
```

<img src="assets/labsetup_condaactivate.png" />

<img src="assets/labsetup_condaactivated.png" />

3. **Copy and run** the following Snowflake CLI command **into the Terminal** to deploy the Streamlit application

```bash
snow --config-file=".snowflake/config.toml" streamlit deploy --replace --project "streamlit" --connection="hol-timeseries-streamlit"
```

> aside negative
> 
>  The **GitHub Codespace** may prompt to allow pasting into **VSCode**, select **Allow** if prompted.
>

<img src="assets/streamlit_codespace_paste.png" />

**Streamlit Deploy with Snowflake CLI**

This command does the following:

- Deploys the Streamlit application using the Snowflake account details mentioned in the ".snowflake/config.toml" file
- --config-file option provides the location of the config file that contains Snowflake account details
- --replace option ensures that the existing application, if present, is overwritten
- --project option provides the path where the Streamlit app project resides
- --connection option dictates which connection section from the ".snowflake/config.toml" file should be used for deployment


### Step 2 - Launch the Streamlit Application

Once the Streamlit application is successfully deployed, Snowflake CLI will display the message **"Streamlit successfully deployed and available"** and will provide the URL for the Streamlit application.

<img src="assets/streamlit_launch.png" />

1. Press **Command/Ctrl** and **click the URL** link to launch the Streamlit application in a new tab. Alternatively, copy and paste the URL into a new tab.

2. Select `Open` once prompted.

<img src="assets/streamlit_open.png" />


### INFO: Working with the Streamlit Application

The **Streamlit in Snowflake** application contains several pages, accessible via the left menu, that cover the following Time Series queries:
* **Raw** Time Series Data
* **Statistical Aggregate** Time Series Data
* **Time Binning / Downsampling** Time Series Data

<img src="assets/streamlit_video_summary.gif" />

**Filtering Menu**

Each page has a filtering menu to:
* Select one or more tags
* Change reporting time selection
* Set the sample size of chart visualizations
* Select various aggregations

<img src="assets/streamlit_video_menu.gif" />

**Streamlit Features**

At the bottom of each page there are options to:
* **Select** how much data is displayed in the table along with the order
* **Download as CSV** - To download the data in CSV file format
* **Supporting Detail** - Shows the queries being run
* **Refresh Mode** - Contains a toggle to enable auto refresh and see new data automatically

<img src="assets/streamlit_video_features.gif" />

### Step 3 - Query Time Series Data using Streamlit in Snowflake

The initial data set contains two weeks of data loaded for 1-Jan-2024 to 14-Jan-2024. Let's query this using the Streamlit application.

Open the **Streamlit Application**:

1. Select the **TS Raw** page

2. From **Select Tag Name** choose the `/IOT/SENSOR/TAG101`

3. For **Start Date** select `1-Jan-2024`

4. For **Start Time** select `00:00`

5. For **End Date** select `1-Jan-2024`

6. For **End Time** select `04:00`

<img src="assets/streamlit_query_filter.png" />

> aside positive
> 
> **Streamlit** will automatically refresh the page after making filter selections.
>
> Review the chart and table detail.
>

7. Select the **TS Aggregates** page

    - The aggregates page will show high level statistical detail for the selected tag and time period.

8. Select the **TS Binning** page

    - The binning page shows a 1 minute downsampled average for the selected tag and time period.

9. Try changing the **Select Aggregation Method** to `MIN` 

    - This will now show the 1 minute minimums for the tag and time period

10. Try changing the **Label Position** to `START`

    - The **Tag Data** table will now show the **Start** timestamp for each minute


### Step 4 - Start a Continuous Simulated Stream

We can now start a continuous stream of data into Snowflake, similar to the initial streaming load, to simulate IoT device data streaming in near real-time to Snowflake.

<img src="assets/model_streamingclient.png" />

In the **GitHub Codespace VS Code**:

1. Open `Menu > Terminal > New Terminal` - a new terminal window will now open

<img src="assets/labsetup_newterminal.png" />

2. Change directory into to the **iotstream** folder: `cd iotstream`

3. Run the `Run_Slooow.sh` script to load the IoT data.

```bash
./Run_Slooow.sh
```

> aside positive
> 
> If there are no errors, IoT data will now be **streaming into Snowflake**, and the **Dynamic Tables** will start to update.
>

4. Back **in the Streamlit application** try enabling `Auto Refresh` by `Expanding Refresh Mode > Toggle Auto Refresh`

    - The charts and data should now start to automatically update with new data streaming into Snowflake every minute.

5. Select the **TS Raw** page to see the raw data

6. Try adding `/IOT/SENSOR/TAG401` and `/IOT/SENSOR/TAG601` to the **Select Tag Names** filter

    - The charts and data should now contain two additional tags with the data updating every minute.

<img src="assets/streamlit_query_stream.png" />

> aside positive
> 
>  You have now successfully deployed a **Time Series Application** using Streamlit in Snowflake. This will allow end users easy access to visualize time series data as well as run their own **Time Series Analysis** on all Time Series data available in Snowflake.
>

<!-- ------------------------ -->
## Cleanup
Duration: 2

1. In **VS Code** open the worksheet `worksheets/hol_timeseries_8_cleanup.sql` and run the script to remove Snowflake objects.

```sql
/*
SNOWFLAKE CLEANUP SCRIPT
*/

-- Set role
USE ROLE ACCOUNTADMIN;

-- Cleanup Snowflake objects
DROP DATABASE HOL_TIMESERIES;
DROP WAREHOUSE HOL_TRANSFORM_WH;
DROP WAREHOUSE HOL_REPORT_WH;
DROP ROLE ROLE_HOL_TIMESERIES;
DROP USER USER_HOL_TIMESERIES;

/*
CLEANUP SCRIPT COMPLETED
*/
```

2. Stop or delete the [Github Codespace](https://github.com/codespaces), using the Codespace actions menu.

<img src="assets/cleanup_codespace.png" />

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 2

> aside positive
> 
> **Congratulations!** You've successfully deployed an end-to-end time series analytics solution with streaming data in Snowflake.
>

### What You Learned

- How to **stream time series data** into Snowflake using Snowpipe Streaming
- How to **use Dynamic Tables** for continuous data pipeline transformations
- How to **analyze time series data** using native Snowflake time series functions
- How to **create custom time series functions** and procedure in Snowflake
- How to **deploy a Streamlit application using Snowflake CLI** to enable end users to run time series analytics


### Additional Resources
- [Getting Started with Snowflake CLI](https://quickstarts.snowflake.com/guide/getting-started-with-snowflake-cli/index.html)
