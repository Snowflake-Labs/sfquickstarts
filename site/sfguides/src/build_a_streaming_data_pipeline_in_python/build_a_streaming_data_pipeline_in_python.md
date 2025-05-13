author: Brad Culberson, Keith Gaputis
id: build_a_streaming_data_pipeline_in_python
summary: A guide to using Rowset API, Dynamic Tables, and Streamlit to build a streaming data pipeline in Python
categories: data-engineering,app-development,streamlit
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Data Applications, Snowpark, Python

# Build a Streaming Data Pipeine in Python

<!-- ------------------------ -->
## Overview
Duration: 5

Snowflake is a powerful platform to process streaming data and do near real-time reporting.

In this guide, we will use the Snowflake Streaming v2 (SSv2) REST API to ingest data into Snowflake tables seconds from generation. The dataset is a randomly generated dataset one would find from ski resorts. It generates Resort Tickets, Lift Rides, and Season Passes in Python and enqueues the data in a SQLite database. The streamer component reads data from the database and sends it to Snowflake and cleans up the database from data sent.

To have fast and efficient near real-time reporting, we will use Dynamic Tables to materialize reports which are then queried from a Streamlit application deployed in the account.

### Prerequisites

- Privileges necessary to create a service user, database, and warehouse in Snowflake
- Access to run SQL in the Snowflake console or SnowSQL
- Basic experience using git, GitHub, and Codespaces
- Intermediate knowledge of Python and SQL

### What You’ll Learn

- How to send data from Python to Snowflake Streaming v2 REST API
- How to prepare data for reporting using Dynamic Tables
- How to create a basic Streamlit application for reporting

### What You’ll Need

- [Snowflake](https://snowflake.com) Account in an AWS commercial region
- [GitHub](https://github.com/) Account with credits for Codespaces

### What You’ll Build

- Streaming pipeline to do near real-time reporting

## Launch the Codespace in GitHub

Navigate to the [code repository](https://github.com/sfc-gh-bculberson/Summit2025-DE214) in GitHub.

Click on the green Code Button, go to the Codespaces tab, and click the green Create codespace on main. You must be logged into GitHub to see the Codespaces tab.

<!-- ------------------------ -->
## Creating the Service User & Role
Duration: 4

To send data to Snowflake, the client must have a Service User's credentials. We will use key-pair authentication in this guide to authenticate to Snowflake and create a custom role with minimal privileges.

To generate the keypair run the following commands in the terminal in the codespace.

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

COPY the contents of the public key in rsa_key.pub from codespaces to the clipboard.

Login to Snowsight or use SnowSQL to execute the following commands replacing `===YOUR_PUBLIC_KEY_HERE===` with the key copied previously:

```sql

USE ROLE ACCOUNTADMIN;

CREATE WAREHOUSE IF NOT EXISTS STREAMING_INGEST;
CREATE ROLE IF NOT EXISTS STREAMING_INGEST;
CREATE USER STREAMING_INGEST LOGIN_NAME='STREAMING_INGEST' DEFAULT_WAREHOUSE='STREAMING_INGEST', DEFAULT_NAMESPACE='STREAMING_INGEST.STREAMING_INGEST', DEFAULT_ROLE='STREAMING_INGEST', TYPE=SERVICE, RSA_PUBLIC_KEY='===YOUR_PUBLIC_KEY_HERE===';
GRANT ROLE STREAMING_INGEST TO USER STREAMING_INGEST;
SET USERNAME=CURRENT_USER();
GRANT ROLE STREAMING_INGEST TO USER IDENTIFIER($USERNAME);

GRANT USAGE ON WAREHOUSE STREAMING_INGEST TO ROLE STREAMING_INGEST;
GRANT OPERATE ON WAREHOUSE STREAMING_INGEST TO ROLE STREAMING_INGEST;
```

## Creating the Database and Schema for data
Duration: 2

Login to Snowsight or use SnowSQL to execute the following commands:

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS STREAMING_INGEST;
USE DATABASE STREAMING_INGEST;
CREATE SCHEMA IF NOT EXISTS STREAMING_INGEST;
USE SCHEMA STREAMING_INGEST;
GRANT OWNERSHIP ON DATABASE STREAMING_INGEST TO ROLE STREAMING_INGEST;
GRANT OWNERSHIP ON SCHEMA STREAMING_INGEST.STREAMING_INGEST TO ROLE STREAMING_INGEST;
```

## Creating the Tables and Pipes needed for data
Duration: 2

Tables are used to store the data from the clients and a pipe is needed to accept data from the clients. The data is inserted into the table from the pipe.

Login to Snowsight or use SnowSQL to execute the following commands:

```sql
USE ROLE STREAMING_INGEST;
USE DATABASE STREAMING_INGEST;
USE SCHEMA STREAMING_INGEST;

CREATE OR REPLACE TABLE RESORT_TICKET(TXID varchar(255), RFID varchar(255), RESORT varchar(255), PURCHASE_TIME datetime, PRICE_USD DECIMAL(7,2), EXPIRATION_TIME date, DAYS number, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);

CREATE OR REPLACE PIPE RESORT_TICKET_PIPE AS
COPY INTO RESORT_TICKET
FROM TABLE (
      DATA_SOURCE (
      TYPE => 'STREAMING'
  )
)
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE;

CREATE OR REPLACE TABLE SEASON_PASS(TXID varchar(255), RFID varchar(255), PURCHASE_TIME datetime, PRICE_USD DECIMAL(7,2), EXPIRATION_TIME date, NAME varchar(255), ADDRESS variant, PHONE varchar(255), EMAIL varchar(255), EMERGENCY_CONTACT variant);

CREATE OR REPLACE PIPE SEASON_PASS_PIPE AS
COPY INTO SEASON_PASS
FROM TABLE (
      DATA_SOURCE (
      TYPE => 'STREAMING'
  )
)
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE;

CREATE OR REPLACE TABLE LIFT_RIDE(TXID varchar(255), RFID varchar(255), RESORT varchar(255), LIFT varchar(255), RIDE_TIME datetime);

CREATE OR REPLACE PIPE LIFT_RIDE_PIPE AS
COPY INTO LIFT_RIDE
FROM TABLE (
      DATA_SOURCE (
      TYPE => 'STREAMING'
  )
)
MATCH_BY_COLUMN_NAME=CASE_SENSITIVE;
```

## Write Streaming Application

To authenticate to Snowflake, you will need to setup the environment with credentials to your account.

This will all be done in the codespace created previously.

Make a copy of the env file to edit by running this command in the codespace terminal.

```bash
cp .env.example .env
```

Edit the Account Name in the .env file to match your Snowflake Account name.

If you do not know your account name, you can run this sql in Snowsight or via snowsql.

```sql
select current_account();
```

### Stream the Data to Snowflake

This repository will generate sample data and supplies the framework and dependencies needed for you to stream data to Snowflake. You need to write the code to stream data to Snowflake.

You will write the main body of the function stream_data in streamer.py. The pipe_name and 2 data access functions are passed to this function. All configuration parameters needed are in the streamer.py under `# parameters`.

fn_get_data takes 2 parameters, the first parameter is the offset to read data from ex: (SELECT * where > offset) and the second parameter is the maximum number of records to read. It will return a list of json strings which can be sent to Snowflake.

Example usage: 

```python
rows = fn_get_data(latest_committed_offset_token, BATCH_SIZE)
```

fn_delete_data takes 1 parameter: the offset to delete data up to and including ex: (DELETE * where offset <= offset).

```python
fn_delete_data(current_committed_offset_token)
```

The first thing the stream_data fn should do is to create a SnowflakeStreamingIngestClient. This client will allow you to operate on Channels which are needed to send data to Snowflake.

To create a SnowflakeStreamingIngestClient, you will need to pass it the channel name and kwargs: account, user, database, schema, private_key, ROWSET_DEV_VM_TEST_MODE.

```python
client = SnowflakeStreamingIngestClient(client_name, account=account_name, user=user_name, database=database_name, schema=schema_name, private_key=private_key, ROWSET_DEV_VM_TEST_MODE="false")
```

This client can be used to open a channel you will need to send data. client.open_channel function takes the channel_name, database_name, schema_name, and the pipe_name as arguments.

```python
channel = client.open_channel(channel_name, database_name, schema_name, pipe_name)
```

To know where this process left off on last run (or if this is the first run) you can pull the current committed offset. This is available by calling channel.get_latest_committed_offset_token()

```python
latest_committed_offset_token = channel.get_latest_committed_offset_token()
```

If this returns None, there has been no data sent to Snowflake, otherwise it will be the latest offset sent.

The channel should be long lived, so there should be an event loop grabbing data. Data can be pulled using fn_get_data from the that offset, or 0 if this is the first data.

Data is returned from the fn_get_data in a list of json strings, but the insert_rows function expects line delimited json. This can easily be converted using join and a list comprehension. You wll also need to get the last offset in the rows you are sending to set the correct offset token.

```python
nl_json = "\n".join([row[1] for row in rows])
latest_committed_offset_token = rows[-1][0]
channel.insert_rows(nl_json, offset_token=latest_committed_offset_token)
```

In order to cleanup you will also want to occasionally delete the local data from the committed offset (retrieved from Snowflake). You can use the fn_delete_data function to do so. This should also be done in the event loop.

### Test the Streaming Application

In the codespace, build and start the docker container.

```bash
docker compose build
docker compose up
```

### Verify Data is Streaming

Run the following sql to verify data is arriving in your account.

Verify Season Passes are being streamed:

```sql
select * from SEASON_PASS limit 10;
```

Verify Resort Tickets are being streamed:

```sql
select * from RESORT_TICKET limit 10;
```

Verify Lift Rides are being streamed:

```sql
select * from LIFT_RIDE limit 10;
```

## Build Pipeline in Python


## Build Reports in Streamlit



<!-- ------------------------ -->
## Cleanup
Duration: 2

To fully remove everything you did today you only need to drop some objects in your Snowflake account. From the Snowflake console or SnowSQL, as `ACCOUNTADMIN` run:
```SQL
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS STREAMING_INGEST;
DROP WAREHOUSE IF EXISTS STREAMING_INGEST;
DROP USER IF EXISTS STREAMING_INGEST;
DROP ROLE IF EXISTS STREAMING_INGEST;
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

### What we've covered
- 
-

