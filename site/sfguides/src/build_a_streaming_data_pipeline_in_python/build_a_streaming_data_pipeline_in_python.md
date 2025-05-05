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

### Launch the Codespace in GitHub

Go to the [code repository](https://github.com/sfc-gh-bculberson/Summit2025-DE214).

Click on the green Code Button, go to the Codespaces tab, and click the green Create codespace on main.

<!-- ------------------------ -->
### Creating the Service User & Role
Duration: 4

To send data to Snowflake, the client must have a Service User's credentials. We will use key-pair authentication in this guide to authenticate to Snowflake and create a custom role with minimal privileges.

To generate the keypair run the following commands in the terminal in the codespace.

```bash
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
cat ./rsa_key.p8
```

COPY the .env.example file in the root of the project to .env and replace the PRIVATE_KEY value with the result of the last command. 
COPY the contents of the private key into a new file

```bash
cat ./rsa_key.pub
```

COPY the contents of the public key to the clipboard.

Login to Snowsight or use SnowSQL to execute the following commands replacing `<YOUR_PUBLIC KEY HERE>` with the key copied previously:

```sql

CREATE WAREHOUSE IF NOT EXISTS STREAMING_INGEST;
CREATE ROLE IF NOT EXISTS STREAMING_INGEST;
CREATE USER STREAMING_INGEST LOGIN_NAME='STREAMING_INGEST' DEFAULT_WAREHOUSE='STREAMING_INGEST', DEFAULT_NAMESPACE='STREAMING_INGEST.STREAMING_INGEST', DEFAULT_ROLE='STREAMING_INGEST', TYPE=SERVICE, RSA_PUBLIC_KEY='<YOUR_PUBLIC KEY HERE>';
GRANT ROLE STREAMING_INGEST TO USER STREAMING_INGEST;
GRANT ROLE STREAMING_INGEST TO USER <YOUR_USERNAME>;

GRANT USAGE ON WAREHOUSE STREAMING_INGEST TO ROLE STREAMING_INGEST;
GRANT OPERATE ON WAREHOUSE STREAMING_INGEST TO ROLE STREAMING_INGEST;
```

### Creating the Database and Schema for data
Duration: 2

Login to Snowsight or use SnowSQL to execute the following commands:

```sql
CREATE DATABASE IF NOT EXISTS STREAMING_INGEST;
USE DATABASE STREAMING_INGEST;
CREATE SCHEMA IF NOT EXISTS STREAMING_INGEST;
USE SCHEMA STREAMING_INGEST;
GRANT OWNERSHIP ON DATABASE STREAMING_INGEST TO ROLE STREAMING_INGEST;
GRANT OWNERSHIP ON SCHEMA STREAMING_INGEST.STREAMING_INGEST TO ROLE STREAMING_INGEST;
```

### Creating the Tables and Pipes needed for data
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

### Setup Streaming Application

To authenticate to Snowflake, you will need to setup the environment with credentials to your account.

This will all be done in the codespace created previously.

Make a copy of the env file to edit by running this command in the codespace terminal.

```bash
cp .env.example .env
```

Set the PRIVATE_KEY variable in the new .env file to the contents of the rsa_key.p8 file.

Edit the Account Name in the .env file to match your Snowflake Account name.

If you do not know your account name, you can run this sql in Snowsight or via snowsql.

```sql
select current_account();
````

### Start Streaming Application

In the codespace, build and start the docker container.

```bash
docker build -t generator .
docker run generator
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

### Build Pipeline in Python


### Build Reports in Streamlit

