author: Ali Khosro
id: snowflake-looker-quickstart
summary: A guide on how to connect Looker to Snowflake using Key-Pair and OAuth authentication, and build a simple dashboard. 
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/build
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Looker, BI, OAuth, Authentication, Key-Pair


# Looker and Snowflake Quickstart

<!-- ------------------------ -->
## Overview

This guide will walk you through the process of connecting Looker to Snowflake and building a simple dashboard. We will cover two authentication methods: Key-Pair for service accounts and OAuth for individual user authentication.

### What You Will Learn
* How to load sample data into Snowflake.
* How to configure both Key-Pair and OAuth connections between Looker and Snowflake.
* How to create a Looker project and model from a Snowflake schema.
* How to build a simple dashboard in Looker.
* How to version control your Looker project with Git.

### Prerequisites
* A Snowflake account with `ACCOUNTADMIN` privileges. If you don't have one, you can sign up for a [free trial](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).
* A Looker instance.
* A GitHub account.

### What You Will Build
* A connection between your Looker instance and your Snowflake account.
* A Looker dashboard visualizing Citibike trip data.
* A Git repository for your Looker project.



<!-- ------------------------ -->
## 1. Loading Data into Snowflake

First, we will load public Citibike trip data from an S3 bucket into your Snowflake account.

```sql
-- Set the context for your session
USE ROLE SYSADMIN;

-- Create a warehouse, database, and schema
CREATE WAREHOUSE IF NOT EXISTS poc_wh;
USE WAREHOUSE poc_wh;
CREATE DATABASE IF NOT EXISTS citibike;
CREATE SCHEMA IF NOT EXISTS citibike.poc;
USE DATABASE citibike;
USE SCHEMA poc;

-- Create a table for the trip data
CREATE OR REPLACE TABLE trips (
  ride_id STRING,
  rideable_type STRING,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  start_station_name STRING,
  start_station_id STRING,
  end_station_name STRING,
  end_station_id STRING,
  start_lat FLOAT,
  start_lng FLOAT,
  end_lat FLOAT,
  end_lng FLOAT,
  member_casual STRING
);

-- Create a file format for the CSV data
CREATE OR REPLACE FILE FORMAT csv_format
  TYPE = 'CSV'
  FIELD_DELIMETER = ','
  SKIP_HEADER = 1
  NULL_IF = ('NULL', '""')
  EMPTY_FIELD_AS_NULL = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- Create a stage to access the public S3 bucket
CREATE OR REPLACE STAGE citibike_trips
  URL = 's3://tripdata/';

-- Load data from the S3 bucket into the trips table
-- This pattern loads all zipped CSV files for the year 2024
COPY INTO trips
  FROM @citibike_trips
    PATTERN = '.*2024.*-citibike-tripdata.csv.zip'  
    FILE_FORMAT = (FORMAT_NAME = 'csv_format')
    ON_ERROR = 'CONTINUE';

-- Verify the data has been loaded
SELECT COUNT(*) FROM trips;
```

<!-- ------------------------ -->
## 2. Configuring Key-Pair Authentication

This method is ideal for service accounts and automated processes. We'll generate a key pair and assign the public key to a dedicated Looker service user in Snowflake.

### 2.A Create a Key Pair

1.  **Generate the keys in your terminal**:
    The following commands create a 2048-bit unencrypted private key (`rsa_key.p8`) and a public key (`rsa_key.pub`).

    ```bash
    # Create a directory to store your keys
    mkdir -p ~/secret_keys && cd ~/secret_keys

    # Generate the private key
    openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt

    # Generate the public key
    openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
    ```

2.  **Copy the public key to your clipboard**:
    The public key must be pasted into Snowflake as a single line of text.

    ```bash
    # macOS
    cat rsa_key.pub | grep -v '^-' | tr -d '\n' | pbcopy
    
    # Linux (requires xclip)
    cat rsa_key.pub | grep -v '^-' | tr -d '\n' | xclip -sel clip
    ```

### 2.B Create Snowflake Service Account and Permissions

Create a dedicated user and role for Looker and assign the public key.

```sql
USE ROLE ACCOUNTADMIN;

-- Create a role for Looker
CREATE ROLE IF NOT EXISTS looker_role;

-- Grant privileges to the role
GRANT USAGE ON DATABASE citibike TO ROLE looker_role;
GRANT USAGE ON SCHEMA citibike.poc TO ROLE looker_role;
GRANT USAGE ON WAREHOUSE poc_wh TO ROLE looker_role;
GRANT SELECT ON ALL TABLES IN SCHEMA citibike.poc TO ROLE looker_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA citibike.poc TO ROLE looker_role;

-- Create the service user for Looker
CREATE USER IF NOT EXISTS looker_service_account
  DEFAULT_ROLE = 'looker_role'
  DEFAULT_WAREHOUSE = 'poc_wh'
  MUST_CHANGE_PASSWORD = FALSE;

-- Assign the public key to the user
ALTER USER looker_service_account
  SET RSA_PUBLIC_KEY = 'your_public_key_string';

-- Grant the role to the service user
GRANT ROLE looker_role TO USER looker_service_account;
```

<!-- ------------------------ -->
## 3. Configuring OAuth Authentication

OAuth allows each Looker user to authenticate with their own Snowflake credentials.

> **Note on OAuth Limitations**
> *   **Persistent Derived Tables (PDTs):** Not supported with Snowflake OAuth.
> *   **Token Expiration:** Users may need to re-authenticate periodically.
> *   **Role Limitations:** The connection uses the user's default role in Snowflake.

### Create Security Integration in Snowflake

1.  Run the following SQL. Replace `<your_looker_hostname>` with your Looker instance's hostname.

    ```sql
    USE ROLE ACCOUNTADMIN;
    CREATE SECURITY INTEGRATION IF NOT EXISTS looker_oauth
      TYPE = OAUTH
      ENABLED = TRUE
      OAUTH_CLIENT = LOOKER
      OAUTH_REDIRECT_URI = 'https://<your_looker_hostname>/external_oauth/redirect';
    ```

2.  Retrieve the Client ID and Secret. You will need these for the Looker connection.

    ```sql
    SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('looker_oauth');
    ```

### Note on Snowflake Network Policies
If you encounter a connection error, you may need to whitelist Looker's IP addresses.

```sql
-- Use the IP from the error message or Looker documentation
CREATE OR REPLACE NETWORK POLICY looker_ip_policy
  ALLOWED_IP_LIST = ('<looker_ip_address>');

ALTER ACCOUNT SET NETWORK_POLICY = looker_ip_policy;
```

<!-- ------------------------ -->
## 4. Configuring the Looker Connections

With Snowflake configured, we can now create the connections in Looker.

1.  Navigate to **Admin** > **Database** > **Connections**.
2.  Click **Add Connection**.

### Connection A: Key-Pair Authentication
*   **Name**: `snowflake_citibike_keypair`
*   **Dialect**: `Snowflake`
*   **Host**: `<your_snowflake_account>.snowflakecomputing.com`
*   **Database**: `CITIBIKE`
*   **Schema**: `POC`
*   **Username**: `looker_service_account`
*   **Auth Method**: `Key Pair`
*   **Private Key**: Paste the content of your `rsa_key.p8` file.
*   **Warehouse**: `poc_wh`

### Connection B: OAuth Authentication
*   **Name**: `snowflake_citibike_oauth`
*   **Dialect**: `Snowflake`
*   **Host**: `<your_snowflake_account>.snowflakecomputing.com`
*   **Database**: `CITIBIKE`
*   **Schema**: `POC`
*   **Authentication**: `OAuth`
*   **OAuth Client ID**: Paste the `OAUTH_CLIENT_ID` from the previous step.
*   **OAuth Client Secret**: Paste the `OAUTH_CLIENT_SECRET`.
*   **Warehouse**: `poc_wh`

Click **Test These Settings**, and if successful, click **Add Connection**.

<!-- ------------------------ -->
## 5. Creating a Looker Project and Dashboard

#### Create a project
Now we will create a Looker project.

1.  Navigate to **Develop** > **LookML Projects**.
2.  Click **New LookML Project**.
    *   **Project Name**: `citibike_quickstart`
    *   **Starting Point**: **Generate Model from Database**.
    *   **Connection**: Select `snowflake_citibike_keypair`.
    *   **Schema**: `POC`
3.  Click **Create Project**.

Looker will automatically generate a model and view file from your database schema.

<!-- ------------------------ -->
#### Create a Dashboard

1.  From the Looker homepage, click **+ New** > **Dashboard**.
2.  Name it "Citibike Trip Overview" and click **Create Dashboard**.
3.  Click **Add Tile**, and choose the **Trips** Explore.
4.  In the Explore interface:
    *   Under **Dimensions**, click **Start Station Name**.
    *   Under **Measures**, click **Count**.
    *   Click **Run**.
5.  Select the **Bar** chart visualization and click **Save**.


<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You have successfully connected Looker to Snowflake, created a LookML project, built a dashboard, and set up version control.

### What You Learned
* How to load data into Snowflake.
* How to configure Key-Pair and OAuth authentication for Looker.
* How to create a Looker project from a database schema.
* How to build a Looker dashboard.
* How to set up Git for a Looker project.

### Related Resources
* [Looker Documentation](https://cloud.google.com/looker/docs)
* [Snowflake Documentation](https://docs.snowflake.com/en/)

