author: Sean Kim
id: build-a-streaming-pipeline-with-snowpipe-streaming-dynamic-tables-and-dbt
summary: This guide provides step-by-step instructions for building a streaming data pipeline in Snowflake with Snowpipe Streaming, Dynamic Tables and dbt Projects
categories: data-engineering
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, dbt, Streaming, IoT, Github, Dynamic Tables, Snowpipe, Python

# Build a Streaming Data Pipeline with Snowpipe Streaming, Dynamic Tables and dbt Projects
<!-- ------------------------ -->
## Overview 
Duration: 3

This guide teaches you to build a production-grade streaming data pipeline that ingests simulated real-time IoT weather and air quality sensor data from 8 locations across Sydney, Australia. You'll learn to ingest environmental readings (temperature, humidity, pressure) and air quality metrics (PM2.5, PM10, CO, CO2, O3, NH3, SO2) using [Snowflake's Snowpipe Streaming: High-Performance Architecture](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-high-performance-overview). The project simulates realistic sensor behavior with location-specific characteristics, daily seasonality patterns, and anomaly detection.

The pipeline follows modern data engineering best practices with a three-step transformation architecture (Landing → Transformed → Analytics) implemented through Dynamic Tables deployed via dbt Projects, providing you with clean, tested, and documented data transformations.

```
<img src="./assets/diagram.png" alt="drawing" width="1000"/>
```

### Use Case - Streaming IoT Analytics Pipeline

The fictional environmental engineering firm deploys IoT sensors across Sydney Central Business District (CBD) areas to monitor environmental conditions and air quality in real-time.

The firm protects public health by tracking air pollution levels (PM2.5, ozone, CO) to issue timely health advisories to government advisories, while urban planners use temperature and humidity data to optimize green space placement. Traffic management teams correlate pollution spikes with traffic patterns for dynamic route optimization, and the climate action team measures sustainability initiative effectiveness using long-term environmental trends.

Real-time 5-minute windows detect pollution spikes immediately for rapid public safety response, while daily aggregations reveal long-term changes for strategic planning. Geographic sensor distribution across Northern and Southern Sydney CBD provides location intelligence to identify hotspots, and automated anomaly detection ensures reliable data for public health decisions and regulatory compliance.

### Prerequisites
- Familiarity with Snowflake
- Familiarity with Python
- Familiarity with dbt

### What You’ll Learn 
- How to ingest streaming data in near-realtime into Snowflake with [Snowpipe Streaming: High-Performance Architecture](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-high-performance-overview)
- How to create and run a dbt Project from a Git repository with Snowflake Workspaces for developer workflows
- How to configure and build Dynamic Tables with dbt

### What You’ll Need 
1. Snowflake Account - [Create a trial account](https://signup.snowflake.com)
    - Ensure you select **AWS** as your cloud provider
    - A Snowflake User with ACCOUNTADMIN role
2. Github Account
3. Python 3.10+ installed on your local machine

### What You’ll Build 

1. A Python IoT streaming data generator with Python
2. A real-time data ingestion pipeline with Snowpipe Streaming v2
3. A dbt data transformation project with Dynamic Tables
    - LANDING: Raw JSON sensor payloads
    - TRANSFORMED layer: A dynamic table that materialises cleaned & flattened sensor readings
    - ANALYTICS layer: A set of dynamic tables for business-ready analytics and aggregations
    - Testing with dbt test
    - Documentation
4. A dbt Project running and deployed within the Snowflake account


<!-- ------------------------ -->
## Setup Github
Duration: 2

### About

GitHub is a collaborative version control platform for tracking changes and managing code for any application including data pipelines, ensuring reproducibility and teamwork.

You are required to have a Github account to perform the steps in this quickstart. You can sign-up for a free account [here](https://github.com/signup). Visit the [Github documentation](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git) for further details.

### Fork the Quickstart Repository

The Git repository for this quickstart can be found here: [Build a Streaming Data Pipeline with Snowpipe Streaming](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming). Click the "Fork" button to create your own copy of the repository.

Save the URL for future steps.

```
<img src="./assets/fork_repo.png" alt="drawing" width="800"/>
```

<!-- ------------------------ -->
## Setup Environment
Duration: 10

We will set up a Snowflake demo environment where all demo assets will be stored, as well as necessary Users and RBAC configuration.

### Create Streaming Service User

The Python Snowpipe Streaming SDK requires a user configured with Key-pair authentication. Run the following commands in your terminal to generate the keys:

```sh
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

Run the following command to generate the SQL to set the public key on the streaming user. Copy the output into your clipboard.

```sh
PUBK=$(cat ./rsa_key.pub | grep -v KEY- | tr -d '\012')
echo "ALTER USER STREAMING_INGEST_SVC_USER SET RSA_PUBLIC_KEY='$PUBK';"
``` 

Run the following SQL in Snowflake to create the service user:

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE USER STREAMING_INGEST_SVC_USER TYPE=SERVICE;

-- Configure Authentication Policy (optional, but recommended for explicit control)
CREATE OR REPLACE AUTHENTICATION POLICY STREAMING_USER_AUTH_POLICY
  AUTHENTICATION_METHODS = ('KEYPAIR')
  CLIENT_TYPES = ('SNOWSQL', 'DRIVERS');
ALTER USER STREAMING_INGEST_SVC_USER SET AUTHENTICATION POLICY STREAMING_USER_AUTH_POLICY;

-- Substitute the below with the copied output from the previous code snippet:
ALTER USER STREAMING_INGEST_SVC_USER SET RSA_PUBLIC_KEY='MII...'
```

### Create Database, Schema, Tables, Database Roles and Roles

Run the [set-up script](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming/blob/main/snowflake_setup/snowflake_env_setup.sql) in Snowflake to create the necessary database and schema objects.

Before running the script, ensure you set the URL of your Git repo in the `GIT_REPOSITORY_URL` variable.

The script installs the following:

- A production database
- `LANDING`, `TRANSFORMED`, `ANALYTICS` schemas
- `PROJECTS` schema where dbt Projects will be stored
- Ingestion landing table
- Static lookup tables in the `LANDING` schema that will be joined to the sensor payloads
- Three database roles for least privilege access for ingestion and transformation roles: 
  - `DB_INGEST`
    - Least privilege permissions for landing data into the LANDING schema
  - `DB_READER` 
    - Least privilege permissions to read data from all schemas
  - `DB_TRANSFORM`
    - Inherits from `DB_READER`
    - Additional permissions to create dbt projects in the `PROJECTS` schema, and create tables and dynamic tables in `TRANSFORMED` and `LANDING` schemas
- Two roles: `STREAMING_INGEST_ROLE` and `STREAMING_TRANSFORM_ROLE`
  - Database role `DB_INGEST` is granted to Role `STREAMING_INGEST_ROLE`
  - `STREAMING_INGEST_ROLE` to be granted to the streaming ingest service user
  - `STREAMING_TRANSFORM_ROLE` to be granted to the human user running the script

### Create a PIPE with In-Flight Transformation

A key feature of Snowpipe Streaming v2 is the ability to perform stateless in-flight transformations of the data. Common use cases include casting elements in semi-structured data into separate columns, type transformations and manipulation of text fields including regex. The [Documentation](https://docs.snowflake.com/en/user-guide/data-load-transform#supported-functions) contains a list of supported functions for COPY transformations. 

Transformation is included in the ingestion cost - allowing you to perform transformations for no additional cost.

> aside negative
> 
> It's crucial to weigh the trade-offs between transforming data in-flight versus transforming post For instance, if the payload schema changes frequently, transforming data in-flight may result in frequent errors or undesirable output, thus often require careful management of schema evolution upstream. Often in such scenarios, a more flexible strategy may be to land the streaming payload into a single VARIANT column and handle schema evolution downstream within Snowflake, which simplifies operational management.

Run this [set-up script](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming/blob/main/snowflake_setup/snowflake_pipe_setup.sql) in Snowflake to create the PIPE object with in-flight transformation that extracts elements from the payload and casts them into individual columns.

### Clustering

Snowpipe Streaming v2 also allows you to cluster in-flight during ingestion, improving query performance of the target table by pre-sorting the data. The pipe used in this quickstart has this feature enabled via the `CLUSTER_AT_INGEST_TIME=TRUE` setting on the PIPE definition.

### Grant Roles to Users

Run the following SQL to grant the roles to the newly created users:

```sql
GRANT ROLE STREAMING_INGEST_ROLE TO USER STREAMING_INGEST_SVC_USER;
ALTER USER STREAMING_INGEST_SVC_USER SET DEFAULT_ROLE=STREAMING_INGEST_ROLE;

--Grant dev role to current user
SET CURRENT_USER = (CURRENT_USER());
GRANT ROLE STREAMING_TRANSFORM_DEV_ROLE TO USER IDENTIFIER($CURRENT_USER);
ALTER USER IDENTIFIER($CURRENT_USER) SET DEFAULT_ROLE=STREAMING_TRANSFORM_DEV_ROLE;
```

<!-- ------------------------ -->
## Python Streaming Client Setup
Duration: 5

> aside positive
> 
>  This has been tested with Python 3.10.16 on MacOS. The Snowpipe Streaming Python SDK requires Python 3.9 or later. Please [raise a GitHub issue](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming/issues) for any issues running the Quickstart in your own enrivonment. 

Navigate to the root folder of where you have cloned the repository and create an environment:

```sh
# Recommended: create a venv
python -m venv ./streaming_client_env
source ./streaming_client_env/bin/activate
```

Install the Snowpipe Streaming SDK:
```sh
pip install snowpipe-streaming
```

### Create a profile configuration file

Connection and authentication settings for the Streaming Client is saved in a `profile.json` file.

Run the following command in your terminal to generate a private key with newline characters escaped:

```sh
sed 's/$/\\n/' rsa_key.p8 | tr -d '\n'
```

Create a new file profile.json in the stream_simulator_app folder:

```sh
cd stream_simulator_app
touch profile.json
```

Edit `profile.json` with the following:

```sh
{
    "user": "STREAMING_INGEST_USER",
    "account": "<your_account_identifier>",
    "url": "https://<your_account_identifier>.snowflakecomputing.com:443",
    "private_key": "<your_formatted_private_key>"
}
```

Replace the placeholders:
- <your_account_identifier>: Your Snowflake account identifier (for example, xy12345).
- <your_formatted_private_key>: The output from the sed command executed above. Example format: -----BEGIN PRIVATE KEY-----\n-----END PRIVATE KEY-----.


<!-- ------------------------ -->
## Run Python Streaming Client
Duration: 2

While in the stream_simulator_app folder, execute the application:

```sh
python3 emit_sensor_readings.py
```

The script by default runs with the following parameter values:
- Minimum sleep time between records: 0.001s (`--min-sleep 0.001`)
- Maximum sleep time between records: 0.1s (`--max-sleep 0.1`)
- Log progress every 100 records (`--log-interval 100`)
- Check commit status every 1000 records (`--commit-check-interval 1000`)
- Profile path: `profile.json` (`---profile profile.json`)

Adjust the above values to test different ingestion rates

If running correctly, you should see an output in stdout similar to the below:

```sh
python3 emit_sensor_readings.py --min-sleep 0.01 --max-sleep 2 --log-interval 50 --commit-check-interval 100
✓ SIGINT (Ctrl+C) handler registered
✓ SIGTERM handler registered
Initialized sensor factory with 8 locations:
  - SYDN001: Sydney Opera House (Type: 1, Area: 1)
  - SYDN002: Harbour Bridge (Type: 2, Area: 1)
  - SYDN003: Circular Quay (Type: 3, Area: 1)
  - SYDN004: Royal Botanic Gardens (Type: 1, Area: 1)
  - SYDN005: Museum of Contemporary Art (Type: 2, Area: 1)
  - SYDN006: Central Railway Station (Type: 3, Area: 2)
  - SYDN007: Hyde Park (Type: 1, Area: 2)
  - SYDN008: Darling Harbour (Type: 2, Area: 2)

--- Sample IoT Sensor Record ---
{
  "record_id": "f42bb08c-b6ee-4a93-a077-8a699dca6afd",
  "sensor_id": "SYDN008",
  "device_type_id": 2,
  "area_id": 2,
  "event_timestamp_utc": "2025-09-19T00:51:09.204949+00:00",
  "location": {
    "latitude": -33.8688,
    "longitude": 151.2018
  },
  "readings": [
    {
      "type": "temperature",
      "value": 16.19,
      "unit": "C"
    },
    {
      "type": "humidity",
      "value": 98.58,
      "unit": "%"
    },
    {
      "type": "pressure",
      "value": 1009.5,
      "unit": "hPa"
    },
    {
      "type": "pm25",
      "value": 8.41,
      "unit": "\u03bcg/m\u00b3"
    },
    {
      "type": "pm10",
      "value": 20.1,
      "unit": "\u03bcg/m\u00b3"
    },
    {
      "type": "nh3",
      "value": 14.88,
      "unit": "ppb"
    },
    {
      "type": "co",
      "value": 0.97,
      "unit": "ppm"
    },
    {
      "type": "co2",
      "value": 418.42,
      "unit": "ppm"
    },
    {
      "type": "so2",
      "value": 2.82,
      "unit": "ppb"
    },
    {
      "type": "o3",
      "value": 0.9,
      "unit": "ppb"
    }
  ]
}
--- End Sample Record ---

Initializing Snowflake Streaming Ingest Client...
Channel opened: IOT_CHANNEL_35825386-cddb-4beb-9f6a-f09d40d4ddd3
Starting continuous IoT sensor data streaming...
Configuration:
  Sleep interval: 0.010-2.000s between records
  Log interval: Every 50 records
  Commit check: Every 100 records
  Profile: profile.json
  Platform: Darwin
  Unix system detected - Use Ctrl+C or send SIGTERM to stop gracefully

Records sent: 50 | Rate: 0.91 records/sec | Last sensor: SYDN002 | Area: 1
Records sent: 100 | Rate: 1.04 records/sec | Last sensor: SYDN008 | Area: 2
  ✓ Committed: 98, Pending: 2
Records sent: 150 | Rate: 1.02 records/sec | Last sensor: SYDN005 | Area: 1
Records sent: 200 | Rate: 1.02 records/sec | Last sensor: SYDN007 | Area: 2
  ✓ Committed: 197, Pending: 3
```


<!-- ------------------------ -->
## Query Streaming Data
Duration: 2

Set up for Snowpipe Streaming: High-Performance Architecture is now complete! You should see data immediately in the `LANDING.SENSOR_READINGS` table:

```sql
SELECT COUNT(*) FROM STREAMING_DATA_PIPELINE_PROD.LANDING.SENSOR_READINGS;

+----------+
| COUNT(*) |
|----------|
| 1041     |
+----------+
```

### Example Query - Temperature Measurement

Calculate minimum and maximum temperature recorded for each location per day:

```sql
SELECT
  to_date(convert_timezone('Australia/Sydney', sr.event_timestamp_utc)) as sensor_reading_date
  , slm.sensor_location_name
  , min(sr.temperature_c) as min_temp_c
  , max(sr.temperature_c) as max_temp_c
FROM STREAMING_DATA_PIPELINE_PROD.LANDING.SENSOR_READINGS sr
LEFT JOIN STREAMING_DATA_PIPELINE_PROD.LANDING.SENSOR_LOCATION_MAPPING slm ON sr.sensor_id = slm.sensor_id
GROUP BY sensor_location_name, sensor_reading_date;

+----------------------------------------------------------------------------+
| SENSOR_READING_DATE | SENSOR_LOCATION_NAME       | MIN_TEMP_C | MAX_TEMP_C |
|---------------------+----------------------------+------------+------------|
| 2025-09-19          | Darling Harbour            | 12.44      | 26.04      |
| 2025-09-19          | Circular Quay              | 14.07      | 25.00      |
| 2025-09-19          | Museum of Contemporary Art | 10.09      | 25.70      |
| 2025-09-19          | Harbour Bridge             | 14.32      | 21.93      |
| 2025-09-19          | Central Railway Station    | 15.41      | 29.29      |
| 2025-09-19          | Sydney Opera House         | 15.23      | 24.58      |
| 2025-09-19          | Royal Botanic Gardens      | 12.13      | 29.49      |
| 2025-09-19          | Hyde Park                  | 9.03       | 21.88      |
+----------------------------------------------------------------------------+
```

### Example Query - Particulate Matter Measurement

Calculate average particulate matter ($PM_{10}$, $PM_{2.5}$) averaged over the previous 24 hours. National Environment Protection Measure for Ambient Air Quality, Australian governments have set a national ambient air quality standards for particulate matter [(source)](https://www.dcceew.gov.au/environment/protection/npi/substances/fact-sheets/particulate-matter-pm10-and-pm25):

- $PM_{10}$: 50 µg/m3 in outdoor air averaged over a 24-hour period
- $PM_{2.5}$: 25 µg/m3 in outdoor air averaged over a 24-hour period

```sql
SELECT
  slm.sensor_location_name
  , avg(pm10_ugm3) as mean_pm10_ugm3
  , avg(pm25_ugm3) as mean_pm25_ugm3
FROM STREAMING_DATA_PIPELINE_PROD.LANDING.SENSOR_READINGS sr
LEFT JOIN STREAMING_DATA_PIPELINE_PROD.LANDING.SENSOR_LOCATION_MAPPING slm ON sr.sensor_id = slm.sensor_id
WHERE sr.event_timestamp_utc > dateadd('hours', -24, current_timestamp())
GROUP BY slm.sensor_location_name;

+--------------------------------------------------------------+
| SENSOR_LOCATION_NAME       | MEAN_PM10_UGM3 | MEAN_PM25_UGM3 |
|----------------------------+----------------+----------------|
| Central Railway Station    | 39.77463687    | 24.28656611    |
| Harbour Bridge             | 20.77116966    | 11.46277280    |
| Hyde Park                  | 19.73043462    | 10.93317979    |
| Circular Quay              | 31.93518393    | 18.88282658    |
| Sydney Opera House         | 24.73675746    | 13.87869030    |
| Royal Botanic Gardens      | 17.76581878    | 9.99081150     |
| Darling Harbour            | 26.50707554    | 14.77627150    |
| Museum of Contemporary Art | 28.32162142    | 16.63670213    |
+--------------------------------------------------------------+
```

### Use Case - Near-realtime monitoring

While the query above gives us a useful snapshot for the given query time, it is important to continually monitor particulate matter levels throughout the day in order to act as quickly levels whenever levels of pollution exceed safe levels. In the next steps, we will create Dynamic Tables that can calculate rolling averages in near-realtime that enables agencies and engineers to quickly monitor and respond to changes in air pollution levels.

<!-- ------------------------ -->
## Setup Workspace
Duration: 5

We will now set up your personal Workspace. This is a user interface that allows you to work with dbt project files and directories. You can build, test and deploy your dbt projects that are stored in your personal database (`USER$<YOUR_USER_NAME>`), which is isolated from other user's projetcs and cannot be accessed by other users. You can also define and store your personal credentials (via the [SECRETS](https://docs.snowflake.com/en/sql-reference/sql/create-secret) object) within your personal database.

### Create New Workspace from Git Repository

1. In Snowsight UI, Navigate to Projects >> Workspaces
2. Under the Workspaces dropdown, expand the list of Workspaces and select Create Workspace From Git Repository:
```
<img src="./assets/workspace_dropdown.png" alt="drawing" width="600"/>
```
3. Fill in the following details:
```
<img src="./assets/git_workspace.png" alt="drawing" width="600"/>
```
- **Repository URL**: URL of the git repository
- **Workspace name**: Your name for the workspace
- **API integration**: Name of the API integration created in the Snowflake setup (`STREAMING_DEMO_GIT_API_INTEGRATION`)

If your repo is public, click "Public Repository" then click Create.

If you have set your Github repo to private, you will need to create a `SECRET` object containing your Github personal access token. Follow the steps on the [Github documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic) to create a personal access token (classic). As this is a token that is specific to your own Github user, we recommend storing this in your personal database.

### Select Profile

Ensure the profile is set to "prod".

<!-- ------------------------ -->
## Test landing data
Duration: 3

Before running the dbt project to generate our Dynamic Tables, we want to test the validity of the source data. 

dbt allows you to define schema and column definitions in YAML files in the `/models` subfolder, including any data sources that are queried to generate the model. You can optionally define any data and unit tests to be performed on each column. See below for an excerpt from the `models/sources.yaml` file in the repository:

```yaml
sources:
  - name: LANDING_landing_tables
    description: "LANDING landing tables ingested via Snowpipe Streaming and static lookup tables"
    schema: LANDING
    tables:
      - name: sensor_readings
        description: "Raw IoT sensor readings ingested via Snowpipe Streaming"
        columns:
          - name: area_id
            description: "Area identifier (1=Northern CBD, 2=Southern CBD)"
            data_tests:
              - not_null
              - accepted_values:
                  values: [1, 2]
```

The column `area_id` runs two tests:

- Test for nulls within the column
- Checks that all values in the column match one of the two accepted values (1, 2)

### Run Source Tests

Run tests on only data sources on this project by:

1. In the top panel of your Workspace, select `Test` from the list of dbt operations.
2. Select the dropdown next to the play button, untick the `Execute with defaults` tickbox and enter `--select "source:*"` in the Additional Flags textbox.
3. Click `Test` to execute the dbt test
```
<img src="./assets/workspace_test.png" alt="drawing" width="800"/>
```
If the tests ran correctly, you should see an output in the bottom "Output" panel similar to the below:

```sh
06:25:01  Running with dbt=1.9.4
06:25:01   adapter: Invalid profile: 'user' is a required property.
06:25:01  Registered adapter: snowflake=1.9.2
06:25:04  Found 5 models, 76 data tests, 5 sources, 477 macros
06:25:04  
06:25:04  Concurrency: 1 threads (target='prod')
06:25:04  
06:25:06  1 of 19 START test source_accepted_values_LANDING_landing_tables_sensor_readings_area_id__1__2  [RUN]
06:25:06  1 of 19 PASS source_accepted_values_LANDING_landing_tables_sensor_readings_area_id__1__2  [PASS in 0.71s]
06:25:06  2 of 19 START test source_accepted_values_LANDING_landing_tables_sensor_readings_device_type_id__1__2__3  [RUN]
06:25:07  2 of 19 PASS source_accepted_values_LANDING_landing_tables_sensor_readings_device_type_id__1__2__3  [PASS in 0.72s]
.....................
06:25:23  19 of 19 START test source_not_null_LANDING_landing_tables_sensor_readings_temperature_c  [RUN]
06:25:24  19 of 19 PASS source_not_null_LANDING_landing_tables_sensor_readings_temperature_c  [PASS in 0.79s]
06:25:24  
06:25:24  Finished running 19 data tests in 0 hours 0 minutes and 20.22 seconds (20.22s).
06:25:24  
06:25:24  Completed successfully
06:25:24  
06:25:24  Done. PASS=19 WARN=0 ERROR=0 SKIP=0 TOTAL=19
```

<!-- ------------------------ -->
## Run and deploy dbt Project
Duration: 3

The dbt project already contains all configuration and models for you to process raw sensor reading data in Snowflake. We will deploy a number of Dynamic Tables that will automatically refresh as new records are streamed into landing tables.

### Dynamic Table Configuration

All models in this project have been configured to materialize as Dynamic Tables. 

This can be configured at each model file (within the `{{ config() }}` header), but as all outputs are Dynamic Tables, it has been set at the project level within the `dbt_project.yml` file:

(TODO: Fix up dbt_project.yml with new definitions and paste it here)

See [dbt documentation for the Snowflake adapter support](https://docs.getdbt.com/reference/resource-configs/snowflake-configs#dynamic-tables) for further details on currently available parameters.

### Build dbt Project

We will now build out all models and tests with a single dbt command - `build`. This command will run all models, tests, snapshots and seeds. See [documentation] for further details.

1. In the top panel of your Workspace, select `Build` from the list of dbt operations.
2. Click the play button immediately to the right.

Assuming it all ran correctly, you should see an output in the bottom "Output" panel similar to the below:

```sh
execute dbt project from workspace USER$.PUBLIC.build-a-streaming-data-pipeline-with-snowpipe-streaming args='compile --target prod'

01:14:39  Running with dbt=1.9.4
01:14:39   adapter: Invalid profile: 'user' is a required property.
01:14:39  Registered adapter: snowflake=1.9.2
01:14:40  Unable to do partial parsing because saved manifest not found. Starting full parse.
01:14:43  Found 5 models, 66 data tests, 5 sources, 477 macros
01:14:43  
01:14:43  Concurrency: 1 threads (target='prod')
01:14:43  


Command Execution Finished

execute dbt project from workspace USER$.PUBLIC.build-a-streaming-data-pipeline-with-snowpipe-streaming args='build --target prod'

11:15:32.978947 [info ] [Dummy-1   ]: Running with dbt=1.9.4
11:15:33.047940 [error] [Dummy-1   ]:  adapter: Invalid profile: 'user' is a required property.
11:15:33.340112 [info ] [Dummy-1   ]: Registered adapter: snowflake=1.9.2
11:15:34.748362 [info ] [Dummy-1   ]: Found 5 models, 66 data tests, 5 sources, 477 macros
11:15:34.756710 [info ] [Dummy-1   ]: 
11:15:34.757374 [info ] [Dummy-1   ]: Concurrency: 1 threads (target='prod')
11:15:34.757986 [info ] [Dummy-1   ]: 
11:15:39.798367 [info ] [Thread-2 (]: 1 of 71 START test source_accepted_values_LANDING_landing_tables_sensor_readings_area_id__1__2  [RUN]
11:15:40.815386 [info ] [Thread-2 (]: 1 of 71 PASS source_accepted_values_LANDING_landing_tables_sensor_readings_area_id__1__2  [PASS in 1.02s]

...

11:16:38.287718 [info ] [Thread-2 (]: 70 of 71 START test not_null_sensor_rolling_5min_window_minute ................. [RUN]
11:16:39.312003 [info ] [Thread-2 (]: 70 of 71 PASS not_null_sensor_rolling_5min_window_minute ....................... [PASS in 1.02s]
11:16:39.315083 [info ] [Thread-2 (]: 71 of 71 START test not_null_sensor_rolling_5min_window_start_time ............. [RUN]
11:16:40.181450 [info ] [Thread-2 (]: 71 of 71 PASS not_null_sensor_rolling_5min_window_start_time ................... [PASS in 0.87s]
11:16:40.187622 [info ] [Dummy-1   ]: 
11:16:40.188263 [info ] [Dummy-1   ]: Finished running 5 dynamic table models, 66 data tests in 0 hours 1 minutes and 5.43 seconds (65.43s).
11:16:40.270595 [info ] [Dummy-1   ]: 
11:16:40.271348 [info ] [Dummy-1   ]: Completed successfully
11:16:40.272066 [info ] [Dummy-1   ]: 
11:16:40.272701 [info ] [Dummy-1   ]: Done. PASS=71 WARN=0 ERROR=0 SKIP=0 TOTAL=71

```

### dbt Model Description

The models in `ANALYTICS` contains four complementary models that provide comprehensive sensor monitoring capabilities across different time horizons. The sensor_latest_readings model serves as a real-time dashboard table, capturing the most recent status of each IoT sensor with current environmental readings (temperature, humidity, pressure) and air quality measurements (PM2.5, PM10, NH3, CO, CO2, SO2, O3), along with intelligent status classification that marks sensors as ACTIVE, DELAYED, or OFFLINE based on their last communication time, and quality assessment that flags readings as NORMAL, INCOMPLETE, or ANOMALY based on sensor completeness and environmental thresholds. This table is perfect for operations teams monitoring sensor network health, environmental agencies tracking real-time air quality conditions, or facility managers ensuring HVAC systems respond to current environmental conditions.

The three rolling window models (sensor_rolling_5min, sensor_rolling_1hour, and sensor_rolling_1day) provide time-series analytics by calculating statistical aggregations (average, minimum, maximum, range, and standard deviation) for temperature, humidity, and pressure measurements over their respective time windows. 

- The rolling 5-minute model (`sensor_rolling_5min.sql`) enables near real-time trend detection for applications like automated climate control systems or immediate air quality alerts
- The rolling 1-hour model (`sensor_rolling_1hour.sql`) supports operational decision-making such as identifying equipment performance patterns or scheduling maintenance based on environmental stress indicators. 
- The rolling 1-day rolling model (`sensor_rolling_1day.sql`) facilitates strategic analysis including long-term environmental trend monitoring for urban planning, compliance reporting for regulatory agencies, or predictive maintenance scheduling based on historical sensor behavior patterns. 

### dbt Macros

dbt macros are reusable pieces of Jinja code that generate SQL dynamically, enabling you to write DRY (Don't Repeat Yourself) transformations and reduce code duplication across your models. This project leverages two key macros to efficiently generate the rolling window analytics:

**`rolling_sensor_metrics` Macro**
The `rolling_sensor_metrics` macro is the primary macro that generates comprehensive time-series analytics for sensor data. It accepts two parameters: `window_interval` (e.g., "5 minutes", "1 hour", "1 day") and `window_label` (e.g., "5min", "1hour", "1day"). The macro creates rolling window calculations for temperature, humidity, and pressure measurements, computing statistical aggregations including average, minimum, maximum, and standard deviation over the specified time window. It also handles window timing metadata such as start/end times and record counts, making it easy to create consistent analytics across different time horizons with a single macro call.

**`window_calculation` Macro**
The `window_calculation` macro is a utility macro that standardizes individual window function generation. It takes four parameters: `agg_func` (aggregation function like 'avg', 'min', 'max'), `measure_col_name` (column name like 'temperature_c'), `window_interval`, and `window_label`. This macro eliminates repetitive window function syntax by generating standardized SQL window functions with consistent partitioning and ordering logic. By using this macro, the `rolling_sensor_metrics` macro reduces code duplication by approximately 75% and ensures all window calculations follow the same pattern for maintainability and consistency.

<!-- ------------------------ -->
## Deploy dbt Project
Duration: 2

### Deploy dbt Project

The dbt Project you have run thus far is stored in your personal database. We will now deploy the project as a separate `DBT PROJECT` object.

1. Click on the Connect button on the top right of the Workspace UI.
2. Click "Deploy dbt project"
3. Select databases `STREAMING_DATA_PIPELINE_PROD` and schema `PROJECTS`
4. Specify a name (e.g. `ENVIRO_READINGS_DBT_PROJECT`)
5. Click Deploy
```
<img src="./assets/deploy_dbt.png" alt="drawing" width="600"/>
```
### Continuous testing with Tasks

All models in this project are deployed as Dynamic Tables, thus it is not necessary to schedule dbt runs for models. However, you may still benefit from running test frequently to monitor for data quality.

To create a schedule to perform a continuously scheduled dbt test:

1. Click on the the dbt Project dropdown on the top right of the screen
2. Under 'Scheduled runs', select 'Create schedule'
3. Specify a name (e.g. 'ENVIRO_READINGS_DBT_TEST_TASK')
4. Specify a frequency (e.g. Hourly at 01 min, UTC)
5. Under select operation, select `Test`
6. Under 'Select profile', select `prod`
7. Leave 'Additional flags' blank
8. Click create
```
<img src="./assets/schedule_dbt_test.png" alt="drawing" width="600"/>
```

<!-- ------------------------ -->
## Cleanup
Duration: 5

Run the [clean-up script](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming/blob/main/snowflake_setup/cleanup.sql) to clean up all resources created in this Quickstart.


<!-- ------------------------ -->
## Conclusion And Resources
Duration: 2

Congratulations! You've successfully built a streaming data pipeline that demonstrates incorporating some of Snowflake's latest features in Streaming ingestion and processing.

The Dynamic Tables you've deployed will continue to refresh automatically as new sensor data streams in, providing your organization with up-to-date environmental monitoring capabilities. Your dbt project includes comprehensive data quality testing and documentation, ensuring reliable and maintainable data transformations. The multi-layered analytics approach enables everything from immediate operational responses (5-minute windows) to strategic environmental planning (daily aggregations).

This foundation can be extended to support additional use cases such as predictive maintenance, automated alerting systems, regulatory compliance reporting, or integration with visualization tools for executive dashboards.

### What You Learned
- How to set up Snowpipe Streaming v2 with high-performance architecture for real-time data ingestion
- How to implement in-flight transformations and clustering during data ingestion for improved performance
- How to create and manage dbt Projects using Snowflake Workspaces with Git integration
- How to configure and deploy Dynamic Tables that automatically refresh with streaming data
- How to implement a layered data architecture (Landing, Transformed, Analytics) following modern data engineering patterns
- How to build comprehensive data quality testing and monitoring with dbt
- How to create time-series analytics with rolling window calculations for IoT sensor data
- How to deploy and schedule dbt projects for continuous data quality monitoring

### Related Resources
- [Snowpipe Streaming: High-Performance Architecture Documentation](https://docs.snowflake.com/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Dynamic Tables Documentation](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
- [dbt Snowflake Adapter Documentation](https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup)
- [Snowflake Workspaces Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces)
- [Snowflake dbt Projects Documentation](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake)
- [Snowpipe Streaming Python SDK Reference](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-sdk-python/reference/latest/index)
- [dbt Dynamic Tables Configuration](https://docs.getdbt.com/reference/resource-configs/snowflake-configs#dynamic-tables)
- [Snowflake Time Series Analytics Best Practices](https://docs.snowflake.com/en/user-guide/querying-time-series-data)
