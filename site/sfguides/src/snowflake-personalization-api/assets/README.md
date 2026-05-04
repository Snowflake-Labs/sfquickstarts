# Create a Data API for Snowflake Data using Python and Flask
Technologies used: [Snowflake](https://snowflake.com/), [Python](https://www.python.org/), 
[Flask](https://palletsprojects.com/p/flask/), [Docker](https://www.docker.com/)

This project demonstrates how to build a custom REST API, powered by Snowflake, to perform point-lookups in real-time (under ~200ms). 
It uses a simple Python Flask API service running in Snowflake Container Services, as well as a Snowflake Hybrid Table.

## Requirements:
* Snowflake account
* Snowflake user with
  * SELECT access to the `SNOWFLAKE_SAMPLES.TPCH_SF10.ORDERS` table
  * USAGE access on a warehouse

## Running
The main guide to this code is featured as a Snowflake Quickstart, found here: https://quickstarts.snowflake.com/guide/snowflake_personalization_api/index.html#0

This QuickStart is best run by forking this repository, and then running in GitHub codespaces.

## Testing
You can test this API using curl or other command-line tools. You can also use a tool such as Postman.

Additionally, the API serves a testing page you can open in a web browser at `https://<INGRESS_URL>/test`.

Finally, to optionally test performance, a jMeter test plan `snow_papi.jmx` is included, along with the `cust_ids.csv`. This will allow you to test 10,000 requests to the API in between 150-200 QPS.
