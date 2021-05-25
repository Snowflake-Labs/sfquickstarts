summary: Building a Single-Page Data Application on Snowflake
id: data_app 
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, API
authors: Brad Culberson

# Building a Data Application

## Overview 
Duration: 1

Snowflake powers a huge variety of applications across many industries and use-cases. In this tutorial you will get an API and web application running that uses Snowflake as it's analytical engine. You will run also load test against the custom API endpoints and scale the backend vertically and horizontally to see the impact. For the finale you will increase efficiency and performance of
the APIs by using a materialization. The example application you will be starting from is based on [Express](https://expressjs.com/) and connects to Snowflake through our connector. The dataset we chose to use for this guide is a snapshot of [Citi Bike](https://www.citibikenyc.com/) ride data.


### Prerequisites
- Privileges to Snowflake to create a user, database, and warehouse
- Ability to install and run software on your computer
- Basic experience using git and editing json
- Intermediate knowledge of SQL
- Access to run sql in Snowflake console or Snowsql

### What You’ll Learn 
- How applications can be built on Snowflake
- Scaling workloads vertically for latency
- Scaling workloads horizontally for concurrency
- Optimizing applications through materialization

### What You’ll Need 
- [VSCode](https://code.visualstudio.com/download) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed

### What You’ll Build 
- A Data Application


## Setting up the Database, Warehouse
Duration: 1

The application requires a warehouse to query the data and a database to store the data we will use for the dashboard. Connect to Snowflake and run these commands (snowsql or snowflake console):

```sql
USE ROLE ACCOUNTADMIN;
CREATE WAREHOUSE DATA_APPS_ADHOC WITH WAREHOUSE_SIZE='medium';
USE WAREHOUSE DATA_APPS_ADHOC;
CREATE DATABASE DATA_APPS_DEMO;
CREATE SCHEMA DATA_APPS_DEMO.DEMO;
CREATE WAREHOUSE DATA_APPS_DEMO WITH WAREHOUSE_SIZE='small' STATEMENT_TIMEOUT_IN_SECONDS=15 STATEMENT_QUEUED_TIMEOUT_IN_SECONDS=15;
CREATE STAGE "DATA_APPS_DEMO"."DEMO"."DEMOCITIBIKEDATA" ENCRYPTION=(TYPE='AWS_SSE_S3') URL='s3://demo-citibike-data/';
```

## Create a Service User for the Application

We will now create a user account separate from your own that uses key-pair authentication. The application will run as this user account in order to query Snowflake. The account will be setup with limited access.

### Create an RSA key for Authentication

This creates the private and public keys we use to authenticate the service account we will use
for Terraform.

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_demo_key 4096
$ openssl rsa -in snowflake_demo_key -pubout -out snowflake_demo_key.pub
```

### Create the User and Role in Snowflake

Log in to the Snowflake console and create the user account by running the following command as the `ACCOUNTADMIN` role.

But first:
1. Copy the text contents of the `~/.ssh/snowflake_demo_key.pub` file, starting _after_ the `PUBLIC KEY` header, and stopping just _before_ the `PUBLIC KEY` footer.
1. Paste over the `RSA_PUBLIC_KEY_HERE` label (shown below).

Execute both of the following SQL statements to create the User and grant it access to the data needed for the application.

```SQL
USE ROLE ACCOUNTADMIN;
CREATE ROLE DATA_APPS_DEMO_APP;

GRANT USAGE ON WAREHOUSE DATA_APPS_DEMO TO ROLE DATA_APPS_DEMO_APP;
GRANT USAGE ON DATABASE DATA_APPS_DEMO TO ROLE DATA_APPS_DEMO_APP;
GRANT USAGE ON SCHEMA DATA_APPS_DEMO.DEMO TO ROLE DATA_APPS_DEMO_APP;

CREATE USER "DATA_APPS_DEMO" RSA_PUBLIC_KEY='RSA_PUBLIC_KEY_HERE' DEFAULT_ROLE=DATA_APPS_DEMO_APP DEFAULT_WAREHOUSE=DATA_APPS_DEMO DEFAULT_NAMESPACE=DATA_APPS_DEMO.DEMO MUST_CHANGE_PASSWORD=FALSE;

GRANT SELECT ON FUTURE TABLES IN SCHEMA DATA_APPS_DEMO.DEMO TO ROLE DATA_APPS_DEMO_APP;
GRANT SELECT ON FUTURE MATERIALIZED VIEWS IN SCHEMA DATA_APPS_DEMO.DEMO TO ROLE DATA_APPS_DEMO_APP;
GRANT ROLE DATA_APPS_DEMO_APP TO USER DATA_APPS_DEMO;
```

## Importing the data
Duration: 10

All the data needed for this demo is in an S3 bucket which is now accessible via an external stage which was added in a previous step. The following commands will load the data into a temporary table and persist into a table for use by the data application.

To import the base dataset for this demo run the following sql in snowsql or snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
CREATE TEMPORARY TABLE TEMP_TRIPS (
	TRIPDURATION NUMBER(38,0),
	STARTTIME TIMESTAMP_NTZ(9),
	STOPTIME TIMESTAMP_NTZ(9),
	START_STATION_ID NUMBER(38,0),
	END_STATION_ID NUMBER(38,0),
	BIKEID NUMBER(38,0),
	USERTYPE VARCHAR(16777216),
	BIRTH_YEAR NUMBER(38,0),
	GENDER NUMBER(38,0)
);

CREATE TEMPORARY TABLE TEMP_WEATHER (
	STATE VARCHAR(80),
	OBSERVATION_DATE DATE,
	DAY_OF_YEAR NUMBER(3,0),
	TEMP_MIN_F NUMBER(5,1),
	TEMP_MAX_F NUMBER(5,1),
	TEMP_AVG_F NUMBER(5,1),
	TEMP_MIN_C FLOAT,
	TEMP_MAX_C FLOAT,
	TEMP_AVG_C FLOAT,
	TOT_PRECIP_IN NUMBER(4,2),
	TOT_SNOWFALL_IN NUMBER(4,2),
	TOT_SNOWDEPTH_IN NUMBER(4,1),
	TOT_PRECIP_MM NUMBER(8,1),
	TOT_SNOWFALL_MM NUMBER(8,1),
	TOT_SNOWDEPTH_MM NUMBER(8,1)
);

COPY INTO TEMP_TRIPS from @DEMOCITIBIKEDATA
file_format=(type=csv skip_header=1) pattern='.*trips.*.csv.gz';

CREATE TABLE TRIPS AS
(Select * from TEMP_TRIPS order by STARTTIME);

COPY INTO TEMP_WEATHER from @DEMOCITIBIKEDATA 
file_format=(type=csv skip_header=1) pattern='.*weather.*.csv.gz';

CREATE TABLE WEATHER AS
(Select * from TEMP_WEATHER order by OBSERVATION_DATE);
```

## Getting the source code for the project
Duration: 3

The application you will be running is written on node.js. It is a dashboard to view bike usage over time and differing weather conditions for Citi Bike. The source code for this application is available at [GitHub](https://github.com/Snowflake-Labs/sfguide-data-apps-demo).

Download the code into a folder of your choice and open the project in VSCode. In VSCode go into the terminal and install the modules needed for this project.

```bash
npm install
npm install -g artillery
```

## Configure the Application
Duration: 5

Copy the config-template.js to config.js and edit the snowflake_account, snowflake_user, snowflake_private_key to be what you created in the previous steps. The Snowflake account (snowflake_account) can be retrieved from Snowflake running Select CURRENT_ACCOUNT(). The user will be DATA_APPS_DEMO, and the snowflake_private_key will be the full path to the private key you created in the earlier step.

To start the application run ```npm start``` in a terminal. If you see any errors, check the configuration is correct.

## Testing the Application
Duration: 5

Open a web browser on your computer and navigate to [http://localhost:3000](http://localhost:3000).

If the page loads and renders graphs your application is working! You can choose other date ranges to test the interactivity of the dashboard and also let the application pick random dates with the link on the upper right.

The application is going through gigabytes of data to aggregate counts over windows of time for the dashboard, and joining data from trips and weather, all real time. The data is return to the website via an API.

Open up these uris in a browser of your choice to see the APIs are exposed to the application.
- [Trips by Month](http://localhost:3000/trips/monthly?start=03/04/2017&end=01/25/2020)
- [Trips by Day of Week](http://localhost:3000/trips/day_of_week?start=03/04/2017&end=01/25/2020)
- [Trips by Temperature](http://localhost:3000/trips/temperature?start=03/04/2017&end=01/25/2020)

You now have a fully working custom single-page application that's using a custom API powered by Snowflake!

## Query Cache Performance
Duration: 5

One really powerful capability of Snowflake is the query cache. Snowflake can determine when no data has changed for a query and return previous results increasing the efficiency and decreasing latencies. To exercise the performance of Snowflake when hitting the cache, we have a load test that uses [artillery](https://artillery.io/). To run the load test you will need to open a new terminal session (leaving ```npn start``` in another session).

```Shell
artillery run scripts/load_tests/all.yaml
```

The queries coming in will be visible in terminal 1 and the results from the queries will be in the second terminal. The load test will run for 2 minutes.

In Snowflake console, go to the history and see the query latencies and how those change from first query to those which were cached. These latencies will align to the load test min/max latencies. You should see cached queries returning the query result in under 100ms. Each test in artillery is hitting the 3 endpoints referenced earlier with the default date range (all). With a dashboard like this, the default set of queries when a user visits the application can all reuse the same cached query results. When more data is ingested, the cache will be updated on the next query. The time for the API responses will be longer than the query response time due to latency and bandwidth of client to Snowflake, and the processing time on your computer to retrieve, format, and return the result set.

## Load Test for a Small Cluster
Duration: 5

All clusters in Snowflake are restricted to 8 concurrent queries. In order to validate this concurrency from an application, we will perform another load test. To avoid the cached query results we saw in the previous step, there is another endpoint and load test which uses random dates. First you will run that load test against that endpoint to get a baseline for a Small Cluster which 
should be able to do 8 concurrency.

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

In Snowflake console, go to the history again to see the queries which are being executed in your account. You will notice that queries start queuing as load increases in this scenario and in the load test you will begin to see timeouts. The goal we are trying to attain with this application is a p95 under 5 seconds. Control-C will stop the load test.


## Load Test for a Medium Cluster
Duration: 5

In Snowflake we can scale out workloads both vertically (bigger clusters) and horizontally (more clusters). The first instinct for customers is usually to increase the cluster size. Increasing the cluster size does not increase concurrency but can double the performance of complex/data intensive queries for every increase in size.

Increasing the size of a cluster in Snowflake is REALLY easy. Run the following sql from snowsql or the Snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
ALTER WAREHOUSE DATA_APPS_DEMO SET WAREHOUSE_SIZE='medium';
```

You can run the same load test again to look for improvement. Leave the node application running as before in another Terminal.

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

Unfortunately these queries are not scanning enough data to distribute across a Medium sized cluster and you will still hit similar concurrency limits from the previous test. This would have decreased the query latency up to 2x if the query scanned more data. The amount of bytes scanned is available in the query history in the Snowflake console.

## Load Test for a Multi-Cluster Warehouse
Duration: 5

In order to get more concurrency you need more clusters. Snowflake has a technology called multi-cluster warehouse which will automatically add clusters after queries are queued.

After doing some usage analysis/projections/load tests, customers can pick minimum and maximum cluster sizes that can meet their performance goals. It is quite easy to change this in production as load changes. In this guide, we'll use a minimum of 1 cluster and allow up to 5 clusters for peak usage. This would allow for up to 40 concurrent queries during peak load. When altering the warehouse you will see 3 clusters come online and be ready for your load test within seconds.

Run the following sql from snowsql or the Snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
ALTER WAREHOUSE DATA_APPS_DEMO SET MIN_CLUSTER_COUNT=1, MAX_CLUSTER_COUNT=5; 
```

You can run the same load test again to look for improvement. Leave the node application running as before.

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

In this load test you should no longer see timeouts because you have enough compute available to meet customer needs. Control-C will stop the load test. Log into the Snowflake console to view the query history again. You will now see which cluster a query was executed on as well as the timings of the query. As the load test ramped up more clusters were *automatically* added to support the influx of users.

## Materialization
Duration: 5

The SLO for this application was a 5 second p95 and we are approaching success. The best way at this point to decrease the latency is to simplify the amount of work needed to populate the dashboard.

Look at the file models/trips.js in VSCode. You will see the sql queries we are running and there are some optional queries which are using materialized views when the environment variable MATERIALIZED is set. These new queries perform aggregation such that the UI can aggregate less rows ex: the API will aggregate the counts per day instead of aggregate every ride during query.

Snowflake will automatically compute the entire materialized view when the view is created immediately. It is also updated atomically on every change of the source table. Run the following sql from snowsql or the Snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE MATERIALIZED VIEW COUNT_BY_DAY_MVW AS
select COUNT(*) as trip_count, date_trunc('DAY', starttime) as starttime from demo.trips group by date_trunc('DAY', starttime);

CREATE OR REPLACE MATERIALIZED VIEW COUNT_BY_MONTH_MVW AS
select COUNT(*) as trip_count, MONTHNAME(starttime) as month, MIN(starttime) as starttime from demo.trips group by month;
```

The results of the queries will be identical to before using the materialization but less compute will be needed during the query.

You will need to stop the Node.js application running in your terminal before starting the new instance with queries enabled.

```Shell
export MATERIALIZED=true && npm start
```

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

Your load tests will be faster than before now, you should be below the 5 second p95 desired by this application with no timeouts. You have now scaled out the API for higher performance and concurrency!

## Cleanup
Duration: 1

To cleanup all the objects we created for this demo, run the following sql from snowsql or the Snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE DATA_APPS_DEMO;
DROP USER DATA_APPS_DEMO;
DROP ROLE DATA_APPS_DEMO_APP;
DROP WAREHOUSE DATA_APPS_DEMO;
DROP WAREHOUSE DATA_APPS_ADHOC;
```

## Conclusion & Next Steps
Duration: 2

In this guide you got a custom single-page application powered by a custom API powered by Snowflake. You also learned how Snowflake scales workloads vertically and horizontally.

If you'd like to learn more, look through the code to see how we built the API endpoints. After you are comfortable on how the application works, you can modify the load tests and endpoints to see how changes affect performance and results. I would suggest you try to create materialized views for all the endpoints to get the maximum performance you can as well as edit the load tests for other customer scenarios.

### What We've Covered
- Configure and Run a custom single-page application and API powered by Snowflake
- Scaling a Data Application Vertically
- Scaling a Data Application Horizontally
- Materialization for Performance

### Related Resources
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides)
- [Express](https://expressjs.com/en/starter/hello-world.html)
- [Node.js Snowflake Driver](https://docs.snowflake.com/en/user-guide/nodejs-driver.html)
- [Multi-cluster Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-multicluster.html)
- [Materialized Views](https://docs.snowflake.com/en/user-guide/views-materialized.html)



