summary: Building a Single-Page Data Application on Snowflake
id: data_app
categories: app-development
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, API
authors: Brad Culberson

# Building a Data Application

## Overview
Duration: 1

Snowflake powers a huge variety of applications across many industries and use-cases. In this tutorial you will create a data application and API that uses Snowflake as its analytical engine. You will then load test against custom API endpoints and scale the backend both vertically and horizontally to see the impact. Finally, you will increase the API's efficiency and performance using a materialization.

The example application you start with is based on [Express](https://expressjs.com/) and connects to Snowflake through our connector. The dataset is a snapshot of [Citi Bike](https://www.citibikenyc.com/) ride data.


### Prerequisites
- Privileges necessary to create a user, database, and warehouse in Snowflake
- Ability to install and run software on your computer
- Basic experience using git and editing JSON
- Intermediate knowledge of SQL
- Access to run SQL in the Snowflake console or SnowSQL

### What You’ll Learn
- How applications can be built on Snowflake
- Scaling workloads vertically for latency
- Scaling workloads horizontally for concurrency
- Optimizing applications through materialization

### What You’ll Need
- [VSCode](https://code.visualstudio.com/download) installed
- [NodeJS](https://nodejs.org/en/download/) installed

### What You’ll Build
- A data application


## Setting up the Database and Warehouse
Duration: 1

The application needs a warehouse to query the data, and a database to store the data presented on the dashboard. To create the database and warehouse, connect to Snowflake and run the following commands in the Snowflake console or using SnowSQL:

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

You will now create a user account separate from your own that the application will use to query Snowflake. In keeping with sound security practices, the account will use key-pair authentication and have limited access in Snowflake.

### Create an RSA key for Authentication

Run the following commands to create a private and public key. These keys are necessary to authenticate the service account we will use for Terraform.

```Shell
$ cd ~/.ssh
$ openssl genrsa -out snowflake_demo_key 4096
$ openssl rsa -in snowflake_demo_key -pubout -out snowflake_demo_key.pub
```

### Create the User and Role in Snowflake

To create a user account, log in to the Snowflake console and run the following commands as the `ACCOUNTADMIN` role.

But first:
1. Open the `~/.ssh/snowflake_demo_key.pub` file and copy the contents starting just _after_ the `PUBLIC KEY` header, and stopping just _before_ the `PUBLIC KEY` footer.
1. Prior to running the `CREATE USER` command, paste over the `RSA_PUBLIC_KEY_HERE` label, which follows the `RSA_PUBLIC_KEY` attribute.

Execute the following SQL statements to create the user account and grant it access to the data needed for the application.

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

The data for this demo is in an S3 bucket in the external stage that you added in step two. The following commands load the data into a temporary table for use by the data application.

Import the base dataset for this demo by running the following SQL in SnowSQL or the Snowflake console:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE DATA_APPS_ADHOC;
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

COPY INTO TEMP_TRIPS from @DEMO.DEMOCITIBIKEDATA
file_format=(type=csv skip_header=1) pattern='.*trips.*.csv.gz';

CREATE TABLE TRIPS AS
(Select * from TEMP_TRIPS order by STARTTIME);

COPY INTO TEMP_WEATHER from @DEMO.DEMOCITIBIKEDATA
file_format=(type=csv skip_header=1) pattern='.*weather.*.csv.gz';

CREATE TABLE WEATHER AS
(Select * from TEMP_WEATHER order by OBSERVATION_DATE);
```

## Getting the source code for the project
Duration: 3

The application you will be running is written on node.js. It is a Citi Bike dashboard that lets users view bike usage over time and in differing weather conditions. The source code is available in [GitHub](https://github.com/Snowflake-Labs/sfguide-data-apps-demo).

Download the code into a folder of your choice and open the project in VSCode. In VSCode, go into the terminal and install the modules needed for this project:

```bash
npm install
npm install -g artillery
```

## Configure the Application
Duration: 5

Copy the contents of `config-template.js` to `config.js` and change the following settings to match the values that you created in the previous steps:
* `snowflake_account`
* `snowflake_user`
* `snowflake_private_key`    

To get the `snowflake_account` value from Snowflake, run `Select CURRENT_ACCOUNT()`. The user is `DATA_APPS_DEMO`, and the `snowflake_private_key` will be the text of the private key that you created previously.

Run ```npm start``` in a terminal to start the application. If you see errors, check that the configuration is correct.

## Testing the Application
Duration: 5

Open a web browser and go to: [http://localhost:3000](http://localhost:3000)

If the page loads and renders graphs, your application works! Try choosing other date ranges to test the interactivity of the dashboard. Or let the application pick random dates by clicking the link in the upper right part of the page.

The application processes gigabytes of data for the dashboard, aggregates counts over time, and joins data from trips and weather—all in real time. The application then returns data to the website via an API.

Open these URIs in a browser to see the APIs that control the application:
- [Trips by Month](http://localhost:3000/trips/monthly?start=03/04/2017&end=01/25/2020)
- [Trips by Day of Week](http://localhost:3000/trips/day_of_week?start=03/04/2017&end=01/25/2020)
- [Trips by Temperature](http://localhost:3000/trips/temperature?start=03/04/2017&end=01/25/2020)

You now have a custom, single-page application that uses a custom API powered by Snowflake!

## Query Cache Performance
Duration: 5

If Snowflake determines that the data result for a query remains unchanged, it returns cached results, increasing efficiency and decreasing latencies. The query cache is a really powerful Snowflake capability.

To exercise Snowflake's performance when hitting the cache, we will be running a load test that uses [artillery](https://artillery.io/). To run the test, open a new terminal session (leave ```npm start``` running in the original session), then run the following:

```Shell
artillery run scripts/load_tests/all.yaml
```

Next, monitor incoming queries in terminal 1, and view the query results in terminal 2. The load test will run for 2 minutes.

Open **History** in the Snowflake console to review how query latencies changed between the initial query and the subsequent cached queries. Latencies align to the load test min/max latencies. Each test in artillery hits the three endpoints referenced earlier with the default date range (all). The results should show that cached queries returned query results in under 100ms.

In a dashboard application such as this, default queries reuse cached results when users visit the application. If additional data is ingested, the cache updates during the next query.

API response times typically exceed query response times. This is partly due to latency and bandwidth constraints between the client and Snowflake, and partly due to the processing time it takes your computer to retrieve, format, and return the result set.

## Load Test for a Small Cluster
Duration: 5

Clusters in Snowflake are restricted to eight concurrent queries. Let's perform another load test to validate the concurrency limit. To avoid the cached query results we saw in the previous step, we will use a different endpoint and run a different test that uses random dates. First, run the test against the endpoint to get a baseline result for a small cluster that should be able to do eight concurrency.

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

Open **History** in the Snowflake console to see the queries that executed in your account. You will notice that queries start queuing as load increases in this scenario, and in the load test, you will begin to see timeouts. The goal we are trying to attain with this application is a p95 under 5 seconds.

Press Control-C to stop the test.


## Load Test for a Medium Cluster
Duration: 5

In Snowflake we can scale out workloads both vertically (bigger clusters) and horizontally (more clusters). The first instinct for customers is usually to increase the cluster size. Increasing the cluster size does not increase concurrency but can double the performance of complex/data-intensive queries for every increase in size.

Increasing the size of a cluster in Snowflake is REALLY easy. Run the following SQL either from SnowSQL or the Snowflake console:

```sql
USE ROLE ACCOUNTADMIN;
ALTER WAREHOUSE DATA_APPS_DEMO SET WAREHOUSE_SIZE='medium';
```

Now run the same load test again to look for improvement. (Again, leave ```npm start``` running in the original session.)

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

Unfortunately, these queries are not scanning enough data to distribute across a Medium-sized cluster, and you will still hit similar concurrency limits from the previous test. This would have decreased the query latency up to 2x if the query scanned more data. The amount of bytes scanned is available in the query history in the Snowflake console.

## Load Test for a Multi-Cluster Warehouse
Duration: 5

To get more concurrency you need more clusters. Snowflake has a technology called multi-cluster warehouse that automatically adds clusters after queries are queued.

After doing some usage analysis/projections/load tests, you can pick minimum and maximum cluster sizes that can meet your performance goals. It is quite easy to change this in production as load changes. In this lab, we'll use a minimum of one cluster and allow up to five clusters for peak usage. These settings would allow for up to 40 concurrent queries during peak load. When altering the warehouse you will see three clusters come online and be ready for your load test within seconds.

Run the following SQL either from SnowSQL or the Snowflake console.

```sql
USE ROLE ACCOUNTADMIN;
ALTER WAREHOUSE DATA_APPS_DEMO SET MIN_CLUSTER_COUNT=1, MAX_CLUSTER_COUNT=5;
```

Run the same load test again to look for improvement. As before, leave ```npm start``` running in the original session.

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

In this load test you should no longer see timeouts because you have enough compute available to meet customer needs.

Press Control-C to stop the load test.

Log in to the Snowflake console to view the query history again. You will now see which cluster a query was executed on, as well as the timings of the query. As the load test ramped up, more clusters were *automatically* added to support the influx of users.

## Materialization
Duration: 5

The SLO for this application is a five second p95. We are approaching success! The best way at this point to decrease latency is to simplify the amount of work needed to populate the dashboard.

Open the `models/trips.js` file in VSCode. You should see the SQL queries we are running, and some optional queries that use materialized views when the environment variable `MATERIALIZED` is set. These new queries perform aggregation such that the UI aggregates less rows. For example, the API aggregates the counts per day instead of aggregating every ride during the query.

Snowflake immediately and automatically computes the entire materialized view when the view is created. It also updates atomically on every change of the source table.

Run the following SQL from SnowSQL or the Snowflake console:

```sql
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE MATERIALIZED VIEW COUNT_BY_DAY_MVW AS
select COUNT(*) as trip_count, date_trunc('DAY', starttime) as starttime from demo.trips group by date_trunc('DAY', starttime);

CREATE OR REPLACE MATERIALIZED VIEW COUNT_BY_MONTH_MVW AS
select COUNT(*) as trip_count, MONTHNAME(starttime) as month, MIN(starttime) as starttime from demo.trips group by month;
```

The results of the queries are identical to the results you got before you used the materialization, but the queries required less compute resources.

Stop the `Node.js` (```npm start```) application running in your terminal before starting the new instance with queries enabled.

```Shell
export MATERIALIZED=true && npm start
```

```Shell
artillery run scripts/load_tests/monthly_random.yaml
```

Your load tests will be faster than before. You should now be below the five second p95 desired by this application with no timeouts. You have now scaled out the API for higher performance and concurrency!

## Cleanup
Duration: 1

To clean up the objects we created for this demo, run the following SQL either from SnowSQL or the Snowflake console:

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

In this guide you created a custom, single-page, data application and custom API powered by Snowflake. You also learned how Snowflake scales workloads vertically and horizontally.

To learn more, review the code to see how we built the API endpoints. When you are comfortable with how the application works, modify the load tests and endpoints to see how changes affect performance and results. Create materialized views for all of the endpoints to get the maximum performance, and edit the load tests for other scenarios.

### What We Covered
- Configuring and running a custom, single-page application and API powered by Snowflake
- Scaling a data application vertically and horizontally
- Improving performance by using materialization

### Related Resources
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides)
- [Express getting started example](https://expressjs.com/en/starter/hello-world.html)
- [Node.js Snowflake Driver documentation](https://docs.snowflake.com/en/user-guide/nodejs-driver.html)
- [Multi-cluster Warehouses documentation](https://docs.snowflake.com/en/user-guide/warehouses-multicluster.html)
- [Materialized Views documentation](https://docs.snowflake.com/en/user-guide/views-materialized.html)
