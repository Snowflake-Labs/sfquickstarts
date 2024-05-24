author: Brian Hess, Brad Culberson
id: build_a_custom_api_in_python
summary: A guide to building and running a custom API Powered by Snowflake and Python/Flask
categories: getting-started,app-development,architecture-patterns,solution-examples
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, API 

# Build a Custom API in Python and Flask
<!-- ------------------------ -->
## Overview 
Duration: 5

Many builders want to share some of the data stored in Snowflake over an http API. Modern mobile and web applications often want to retrieve that data through http APIs. This tutorial will go through how to build, deploy, and host a custom API Powered by Snowflake.

This API consists of reporting endpoints from data stored in Snowflake. After completing this guide, you will have built a custom API built with [Python Flask](https://flask.palletsprojects.com/). 

The dataset is the [TPC-H](https://docs.snowflake.com/en/user-guide/sample-data-tpch) data set included in your Snowflake account.


### Prerequisites
- Privileges necessary to create a user, database, warehouse, compute pool, repository, network network rule, external access integration, and service in Snowflake
- Privileges necessary to access the tables in the `SNOWFLAKE_SAMPLE_DATA.TPCH_SF10` database and schema
- Access to run SQL in the Snowflake console or SnowSQL
- Basic experience using git, GitHub, and Codespaces
- Intermediate knowledge of Python

### What You’ll Learn 
- How to configure and build a custom API Powered by Snowflake
- How to build, publish, and deploy a container with the API in Snowflake

### What You’ll Need 
- [Snowflake](https://snowflake.com) Account in an AWS commercial region
- [GitHub](https://github.com/) Account with credits for Codespaces
- [ngrok](https://ngrok.com) Account (Optional, needed for Step 10)

### What You’ll Build 
- API Powered by Snowflake

<!-- ------------------------ -->
## Setting up a Warehouse
Duration: 1

The API needs a warehouse to query the data to return to the caller. To create the database and warehouse, connect to Snowflake and run the following commands in the Snowflake console or using SnowSQL:

```sql
USE ROLE ACCOUNTADMIN;
CREATE WAREHOUSE DATA_API_WH WITH WAREHOUSE_SIZE='xsmall';
```

### Create the Application Role in Snowflake
Duration: 1

The application will run as a new role with minimal priviledges. To create the role, connect to Snowflake and run the following SQL statements to create the role and grant it access to the data needed for the application.

```SQL
USE ROLE ACCOUNTADMIN;
CREATE ROLE DATA_API_ROLE;

GRANT USAGE ON WAREHOUSE DATA_API_WH TO ROLE DATA_API_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DATA_API_ROLE;

GRANT ROLE DATA_API_ROLE TO ROLE ACCOUNTADMIN;
```

<!-- ------------------------ -->
## Setting up your Development Environment
Duration: 3

The code used in this guide is hosted in github. You will need a new Codespace from the GitHub [repository]](https://github.com/sfc-gh-bculberson/lab_data_api_python).

To create a new codespace, browse to the GitHub [repository](https://github.com/sfc-gh-bculberson/lab_data_api_python) in a browser. You will need to login to GitHub if you are not already logged in to access Codespaces. After logging in, click on the green "<> Code" button and "create codespace on main" button.

You will then be redirected into Codespaces where your development environment will load and all code from GitHub will be loaded in the project.

### Endpoints
The API creates two sets of endpoints, one for using the Snowflake connector:
1. `https://host/connector/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `https://host/connector/clerk/<CLERKID>/yearly_sales/<YEAR>`
  * Which takes 2 required path parameters:
    1. `CLERKID` - the clerk ID. Use just the numbers, such as `000000001`.
    2. `YEAR` - the year to use, such as `1995`.

And the same ones using Snowpark:
1. `https://host/snowpark/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `https://host/snowpark/clerk/<CLERKID>/yearly_sales/<YEAR>`
  * Which takes 2 required path parameters:
    1. `CLERKID` - the clerk ID. Use just the numbers, such as `000000001`.
    2. `YEAR` - the year to use, such as `1995`.

### Code
The `src/` directory has all the source code for the API. The `connector.py` file contains all the entrypoints for the API endpoints using the Snowflake Connector for Python. The `customers_top10()` function is one of the API endpoints we needed for this API which finds the top 10 customers by sales in a date range. Review the code and the SQL needed to retrieve the data from Snowflake and serialize it to JSON for the response. This endpoint also takes 2 optional query string parameters start_range and end_range.

```python
@connector.route('/customers/top10')
def customers_top10():
    # Validate arguments
    sdt_str = request.args.get('start_range') or '1995-01-01'
    edt_str = request.args.get('end_range') or '1995-03-31'
    try:
        sdt = datetime.datetime.strptime(sdt_str, dateformat)
        edt = datetime.datetime.strptime(edt_str, dateformat)
    except:
        abort(400, "Invalid start and/or end dates.")
    sql_string = '''
        SELECT
            o_custkey
          , SUM(o_totalprice) AS sum_totalprice
        FROM snowflake_sample_data.tpch_sf10.orders
        WHERE o_orderdate >= '{sdt}'
          AND o_orderdate <= '{edt}'
        GROUP BY o_custkey
        ORDER BY sum_totalprice DESC
        LIMIT 10
    '''
    sql = sql_string.format(sdt=sdt, edt=edt)
    try:
        res = conn.cursor(DictCursor).execute(sql)
        return make_response(jsonify(res.fetchall()))
    except:
        abort(500, "Error reading from Snowflake. Check the logs for details.")
```

You can also review the other endpoints in [connector.py](https://github.com/sfc-gh-bculberson/lab_data_api_python/blob/main/src/connector.py) to see how simple it is to host multiple endpoints.

If you would also like to see how to build endpoints using the Snowflake Snowpark API, review [snowpark.py](https://github.com/sfc-gh-bculberson/lab_data_api_python/blob/main/src/snowpark.py).

<!-- ------------------------ -->
## Building the Application Container
Duration: 1

To create the application container, we will leverage docker. The Dockerfile is based on python 3.8 and installs the required libraries needed for the application as well as the code. To create the docker container, run this command in the terminal provided by Codespaces:
```bash
docker build -t dataapi .
```

<!-- ------------------------ -->
## Creating the Image Registry
Duration: 1

 To create the image registry and the database which contains it, connect to Snowflake and run the following commands in the Snowflake console or using SnowSQL:

```sql

USE ROLE ACCOUNTADMIN;
CREATE DATABASE API;

GRANT ALL ON DATABASE API TO ROLE DATA_API_ROLE;
GRANT ALL ON SCHEMA API.PUBLIC TO ROLE DATA_API_ROLE;

USE DATABASE API;
CREATE OR REPLACE IMAGE REPOSITORY API;

GRANT READ ON IMAGE REPOSITORY API TO ROLE DATA_API_ROLE;

SHOW IMAGE REPOSITORIES;
```

Note the `repository_url` in the response as that will be needed in the next step.

<!-- ------------------------ -->
## Pushing the Container to the Repository
Duration: 1

Run the following command in the terminal, replacing the `<repository_url>` with your repository in the previous step, in Codespaces to login to the container repository. You will be prompted for your Snowflake username and password to login to your repository.

```bash
docker login <repository_url>
docker build -t <repository_url>/dataapi .
docker push <repository_url>/dataapi
```

<!-- ------------------------ -->
## Creating the Compute Pool
Duration: 1

 To create the compute pool to run the application, connect to Snowflake and run the following command in the Snowflake console or using SnowSQL:

```sql

USE ROLE ACCOUNTADMIN;

CREATE COMPUTE POOL API
  MIN_NODES = 1
  MAX_NODES = 5
  INSTANCE_FAMILY = CPU_X64_XS;

GRANT USAGE ON COMPUTE POOL API TO ROLE DATA_API_ROLE;
GRANT MONITOR ON COMPUTE POOL API TO ROLE DATA_API_ROLE;

```

<!-- ------------------------ -->
## Creating the Application Service
Duration: 1

To create the service to host the application, connect to Snowflake and run the following command in the Snowflake console or using SnowSQL.

```sql

USE ROLE ACCOUNTADMIN;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE DATA_API_ROLE;

CREATE SECURITY INTEGRATION IF NOT EXISTS SNOWSERVICES_INGRESS_OAUTH 
TYPE=oauth
OAUTH_CLIENT=snowservices_ingress
ENABLED=true;

USE ROLE DATA_API_ROLE;
CREATE SERVICE API.PUBLIC.API
 IN COMPUTE POOL API
 FROM SPECIFICATION  
$$
spec:
  container:
  - name: api
    image: /api/public/api/dataapi:latest
    resources:                          
      requests:
        cpu: 0.5
        memory: 128M
      limits:
        cpu: 1
        memory: 256M
  endpoint:
  - name: api
    port: 8001
    public: true
$$
QUERY_WAREHOUSE = DATA_API_WH;

```

It will take a few minutes for your service to initialize, you can check status with these commands:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('api');
CALL SYSTEM$GET_SERVICE_LOGS('api.public.api', 0, 'api');

```

After your service has started, you can get the endpoints with this command:

```sql
SHOW ENDPOINTS IN SERVICE API;
```

Make note of the ingress_url as that will be need to test the application. This service will start the API, running at https://<INGRESS_URL>.


<!-- ------------------------ -->
## Testing the API
Duration: 1

To verify the API is online, go to the https://<INGRESS_URL> in your browser. You will be asked to authenticate to Snowflake and be given the root content: 

```json
{"result":"Nothing to see here"}
```

### Testing using a webpage
This project comes with a simple webpage that allows you to test the API. To get to it, open https://<INGRESS_URL>/test in a web browser.

At the top you can choose if you want to exercise the Snowflake Connector for Python or the Snowflake Snowpark API endpoints.

There are 2 forms below that. The first one allows you to enter parameters to test the "Top 10 Customers" endpoint. The second one allows you to enter parameters to test the "Montly Clerk Sales" endpoint.

When you hit the `Submit` button, the API endpoint is called and the data is returned to the web page.

<!-- ------------------------ -->
## Making the API Public
Duration: 3

For the next steps you will need a ngrok token. To get a token, go to [ngrok](https://ngrok.com) and Sign up for a free account. After registration you can get your authtoken in the UI under Getting Stared.

The service created will need network access to ngrok to create the tunnel. To do this, you'll need a new network rule, an external access integration and to use that integration in the service.

In order for the container to get your ngrok token, you'll also need to add it to the service environment. Make sure to replace <YOUR_NGROK_AUTHTOKEN> with your token.

Run the following commands in the Snowflake console or using SnowSQL.

```sql
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE NETWORK RULE NGROK_OUT TYPE=HOST_PORT MODE = EGRESS VALUE_LIST=('connect.ngrok-agent.com:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION NGROK
ALLOWED_NETWORK_RULES = (NGROK_OUT) ENABLED = TRUE;

GRANT USAGE ON INTEGRATION NGROK TO ROLE DATA_API_ROLE;
DROP SERVICE API.PUBLIC.API;

USE ROLE DATA_API_ROLE;
CREATE SERVICE API.PUBLIC.API
IN COMPUTE POOL API
FROM SPECIFICATION 
$$
spec:
  container:
  - name: api
    image: /api/public/api/dataapi:latest
    env:
      NGROK_AUTHTOKEN: <YOUR_NGROK_AUTHTOKEN>
    resources:                          
      requests:
        cpu: 0.5
        memory: 128M
      limits:
        cpu: 1
        memory: 256M
  endpoint:
  - name: api
    port: 8001
    public: true
$$
QUERY_WAREHOUSE = DATA_API_WH
EXTERNAL_ACCESS_INTEGRATIONS = (NGROK);

CALL SYSTEM$GET_SERVICE_STATUS('api');
```

This will deploy a new service which will have public network access and your ngrok key. 

The url of the public service will be in logs after startup.

```sql
CALL SYSTEM$GET_SERVICE_LOGS('api.public.api', 0, 'api');
```

### Testing using cURL
The API can be tested using the cURL command-line tool. Make sure to replace the <YOUR_NGROK_URL> in the commands with the url found in the previous step.

#### Top 10 Customers
To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Connector for Python, run:

```bash
curl -X GET "https://<YOUR_NGROK_URL>/connector/customers/top10?start_range=1995-02-01&end_range=1995-02-14"
```

To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Snowpark API, run:
```bash
curl -X GET "https://<YOUR_NGROK_URL>/snowpark/customers/top10?start_range=1995-02-01&end_range=1995-02-14"
```

If you call the endpoint without specifying the `start_range` then `1995-01-01` will be used. If you call the endpoint without specifying the `end_range` then `1995-03-31` will be used.

#### Monthly sales for a given year for a sales clerk
To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Connector for Python, run:
```bash
curl -X GET "https://<YOUR_NGROK_URL>/connector/clerk/000000002/yearly_sales/1995"
```

To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Snowpark API, run:
```bash
curl -X GET "https://<YOUR_NGROK_URL>/snowpark/clerk/000000002/yearly_sales/1995"
```

<!-- ------------------------ -->
## Stopping the API
Duration: 1

To stop the API, you can suspend the service. From the Snowflake console or SnowSQL, run:

```sql
USE ROLE DATA_API_ROLE;
ALTER SERVICE API.PUBLIC.API SUSPEND;
```

<!-- ------------------------ -->
## Cleanup
Duration: 2

To fully remove everything you did today you only need to drop some objects in your Snowflake account. From the Snowflake console or SnowSQL, as `ACCOUNTADMIN` run:
```SQL
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS API;
DROP ROLE IF EXISTS DATA_API_ROLE;
DROP COMPUTE POOL IF EXISTS API;
DROP WAREHOUSE IF EXISTS DATA_API_WH;
DROP INTEGRATION IF EXISTS NGROK;
DROP NETWORK RULE IF EXISTS NGROK_OUT;
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

You've successfully built a custom API in Python Powered by Snowflake. 

When you go to put a data API into production you should protect the API with some level of authentication and authorization. You can do this with ngrok, but you will need to change the configuration used as this example had it publicly accessible. 

Another consideration is enabling a frontend website to access the endpoint, the test site worked in this example because it's hosted on the same domain as the api. If you need to access the api from another website, you will need to do additional configuration.

To get more comfortable with this solution, implement new endpoints pointing to the sample dataset provided or other datasets.

Code for this project is available at [https://github.com/sfc-gh-bculberson/lab_data_api_python](https://github.com/sfc-gh-bculberson/lab_data_api_python).

### What we've covered
- How to configure and build a custom API Powered by Snowflake
- How to run and test the API on your machine
