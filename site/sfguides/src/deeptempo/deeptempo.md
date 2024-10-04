author: mando222
id: tempo
summary: This is a guide on getting started with tempo on Snowflake
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Security, LLGM, Intrusion Detection

# Getting Started with TEMPO (Using Sample Data)
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide will walk you through the process of setting up and using the TEMPO Native App in your Snowflake environment with provided sample data.

### What You’ll Learn 
- How to run Tempo on sample data.
- How to fine tune the model 
- How to view the output in Splunk

### What You’ll Need 
- A [SnowFlake](https://www.snowflake.com/login/) Account 
- A [Splunk](https://www.splunk.com/) Account or instance

### What You’ll Build 
- A working LLGM alerting dashboard

<!-- ------------------------ -->
## Install the TEMPO Native App
Duration: 2


1. Obtain the TEMPO native app from the Snowflake Marketplace.
2. Once installed, the app will be available for use in your Snowflake environment.
3. Grant the app privileges to create the required compute resources:

```sql
GRANT CREATE COMPUTE POOL ON ACCOUNT TO APPLICATION TEMPO;
GRANT CREATE WAREHOUSE ON ACCOUNT TO APPLICATION TEMPO;
```

The application comes with its own in-house warehouse (TEMPO_WH) and compute pool (TEMPO_COMPUTE_POOL) with the following specs, which will be used for container services runs.
- TEMPO_WH
```sql
CREATE WAREHOUSE IF NOT EXISTS TEMPO_WH
    WAREHOUSE_TYPE = 'SNOWPARK-OPTIMIZED'
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = FALSE;
```
- COMPUTE POOL
```sql
CREATE COMPUTE POOL IF NOT EXISTS TEMPO_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    AUTO_SUSPEND_SECS = 360
    INSTANCE_FAMILY = 'GPU_NV_S'
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = FALSE;
```
<!-- ------------------------ -->
## Initialize the Application and Grant Permissions for Sample Data Acces
Duration: 2

Call the startup procedure to initialize the app:

```sql
CALL TEMPO.MANAGER.STARTUP();
```
<!-- ------------------------ -->
## Perform Inference 
Duration: 2

Use the `TEMPO.DETECTION` schema's stored procedure to perform inference on sample static log data. It takes the a job service name as the only parameter.

Example:

```sql
CALL TEMPO.DETECTION.WORKSTATIONS('<job_service_name>');
```
or
```sql
CALL TEMPO.DETECTION.WEBSERVER('<job_service_name>');
```
or
```sql
CALL TEMPO.DETECTION.DEVICE_IDENTIFICATION('<job_service_name>');
```
`<job_service_name>`: the name of the run you want to perform (e.g., 'tempo_run_one', 'here_we_go').

<!-- ------------------------ -->
### Monitor Job Services

Check the status of Job services:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('DETECTION.<job_service_name>');
```

`<job_service_name>`: The name of the job service to check.

Example:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('DETECTION.WORKSTATION_RUN_ONE');
```
<!-- ------------------------ -->
## Splunk
Duration: 2

TODO

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

Soon Tempo will be avaliable for for user specific data

### What You Learned
- Completed setup of Tempo on SnowFlake
- Ran Tempo on a sample dataset

