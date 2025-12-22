author: Brian Hess, Brad Culberson
id: build-a-custom-api-in-python
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/transformation
language: en
summary: Build Python REST APIs with Flask that query Snowflake for custom data application backends and integrations.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Build a Custom API in Python and Flask
<!-- ------------------------ -->
## Overview 

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

### What You’ll Build 
- API Powered by Snowflake

<!-- ------------------------ -->
## Setting Up Your Development Environment

The code used in this guide is hosted in github. You will need a new Codespace from the GitHub [repository](https://github.com/Snowflake-Labs/sfguide-build-a-custom-api-in-python-flask).

To create a new codespace, browse to the GitHub [repository](https://github.com/Snowflake-Labs/sfguide-build-a-custom-api-in-python-flask) in a browser. 

You will need to login to GitHub if you are not already logged in to access Codespaces. After logging in, click on the green "<> Code" button and "create codespace on main" button.

You will then be redirected into Codespaces where your development environment will load and all code from GitHub will be loaded in the project. 

Let's take a quick look at the code in this repository.

### Endpoints
The API creates two sets of endpoints, one for using the Snowflake connector:
1. `https://host/connector/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `https://host/connector/clerk/CLERK_ID/yearly_sales/YEAR`
  * Which takes 2 required path parameters:
    1. `CLERK_ID` - the clerk ID. Use just the numbers, such as `000000001`.
    2. `YEAR` - the year to use, such as `1995`.

And the same ones using Snowpark:
1. `https://host/snowpark/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `https://host/snowpark/clerk/CLERK_ID/yearly_sales/YEAR`
  * Which takes 2 required path parameters:
    1. `CLERK_ID` - the clerk ID. Use just the numbers, such as `000000001`.
    2. `YEAR` - the year to use, such as `1995`.

### Code
The `src/` directory has all the source code for the API. The `connector.py` file contains all the entrypoints for the API endpoints using the Snowflake Connector for Python. 
The `customers_top10()` function is one of the API endpoints we needed for this API which finds the top 10 customers by sales in a date range. 
Review the code and the SQL needed to retrieve the data from Snowflake and serialize it to JSON for the response. 
This endpoint also takes 2 optional query string parameters start_range and end_range.

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

You can also review the other endpoints in [connector.py](https://github.com/Snowflake-Labs/sfguide-build-a-custom-api-in-python-flask/blob/main/src/connector.py) to 
see how simple it is to host multiple endpoints.

If you would also like to see how to build endpoints using the Snowflake Snowpark API, 
review [snowpark.py](https://github.com/Snowflake-Labs/sfguide-build-a-custom-api-in-python-flask/blob/main/src/snowpark.py).

<!-- ------------------------ -->
## Setting Up Snowflake CLI

All of the commands in this step will be run in the terminal in Codespaces.

First, we need to install Snowflake CLI, with the following command in the terminal:
```bash
pip install snowflake-cli
```

Next, we will create a connection for SnowCLI to our Snowflake account. When you
run the following command in a terminal, you will be prompted for various details. 
You only need to supply a connection name (use `my_snowflake`), 
the account name (of the form `<ORGNAME>-<ACCTNAME>`, the part before `snowflakecomputing.com`),
the user name, and the password. The other prompts are optional:

```bash
snow connection add
```

To make this connection the default connection that SnowCLI uses, run the following in the terminal:

```bash
snow connection set-default my_snowflake
```

Test that the connection is properly set up by running the following in a terminal:

```bash
snow connection test
```

Let's create a database for this lab using Snowflake CLI. Run the following command in a terminal:

```bash
snow object create database name=api --if-not-exists
```

<!-- ------------------------ -->
## Creating A Notebook

It is useful to use a Notebook to follow the steps for this lab. It allows multiple commands to be put in a single cell and executed, and it allows
seeing the output of previous steps.

You can create a new Notebook in Snowflake and copy commands from this guide into new cells and execute them. Alternatively, the repo for this
lab comes with a Notebook file you can use to create a Notebook in Snowflake with all of the commands in it.

### Importing the Notebook file
The lab repository comes with a Notebook with the commands in it already. It actually has the full Quickstart in it 
(the text/instructions and commands) - they are the same.

To create a Notebook with this lab and commands in it, first download the `DataAPI.ipynb` file from the lab repository, 
[here](https://github.com/Snowflake-Labs/sfguide-build-a-custom-api-in-python-flask/blob/main/DataAPI.ipynb). 
If you are using Codespaces, you can right-click on the file in the file explorer and choose "Download".

Next, in the Snowflake console, choose the "Projects" sidebar and select "Notebooks". Choose the down arrow next to the "+ Notebook"
button and select "Import .ipynb file". You will be prompted to choose the file from your machine - choose the `DataAPI.ipynb` file that you saved.
Next, you will be shown a form to collect information about your Notebook. You can choose any name you would like (e.g., `Data API`). 
Choose the `API` database and the `PUBLIC` schema. Choose "Run on warehouse". Leave all of the other inputs with their defaults.

When the Notebook is created, click the "Start" button on the top.

<!-- ------------------------ -->
## Setting Up A Database and Warehouse

The API needs a warehouse to query the data to return to the caller. To create the database and warehouse, 
run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS API;
CREATE WAREHOUSE IF NOT EXISTS DATA_API_WH WITH WAREHOUSE_SIZE='xsmall';
```

### Create the Application Role in Snowflake

The application will run as a new role with minimal priviledges. The following commands create the role and grant it access to the data needed for the application.
Run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```SQL
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS DATA_API_ROLE;

GRANT ALL ON DATABASE API TO ROLE DATA_API_ROLE;
GRANT ALL ON SCHEMA API.PUBLIC TO ROLE DATA_API_ROLE;
GRANT USAGE ON WAREHOUSE DATA_API_WH TO ROLE DATA_API_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DATA_API_ROLE;

GRANT ROLE DATA_API_ROLE TO ROLE ACCOUNTADMIN;
```

<!-- ------------------------ -->
## Creating The Image Registry

To create the image registry, run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE API;
CREATE OR REPLACE IMAGE REPOSITORY API;

GRANT READ ON IMAGE REPOSITORY API TO ROLE DATA_API_ROLE;

SHOW IMAGE REPOSITORIES;
```

Note the `repository_url` in the response as that will be needed in the next step.

<!-- ------------------------ -->
## Building The Application Container

The commands in this step are to be run in a terminal in Codespaces.

To create the application container, we will leverage docker. The Dockerfile is based on python 3.8 and installs the required libraries needed for 
the application as well as the code. To create the docker container, run this command in the terminal provided by Codespaces:

```bash
docker build -t dataapi .
```

Next, we need to tag the Docker image. To do so, replace the `<repository_url>` with the `repository_url` value 
returned by the `SHOW IMAGE REPOSITORIES` command you ran above.

```bash
docker tag dataapi <repository_url>/dataapi
```

Lastly, we need to push the image to Snowflake. Before we do that, we need to log into the Image Registry for Docker. To do so, run:

```bash
snow spcs image-registry login
```

And finally we can push it to the image repository. 
```bash
docker push <repository_url>/dataapi
```

<!-- ------------------------ -->
## Creating The Compute Pool

To create the compute pool to run the application, run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE ACCOUNTADMIN;

CREATE COMPUTE POOL API
  MIN_NODES = 1
  MAX_NODES = 5
  INSTANCE_FAMILY = CPU_X64_XS;

GRANT USAGE ON COMPUTE POOL API TO ROLE DATA_API_ROLE;
GRANT MONITOR ON COMPUTE POOL API TO ROLE DATA_API_ROLE;
```

You can see the status of the `API` compute pool by running:

```sql
SHOW COMPUTE POOLS;
```

<!-- ------------------------ -->
## Creating The Application Service

To create the service to host the application, run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE ACCOUNTADMIN;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE DATA_API_ROLE;

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
serviceRoles:
- name: api_sr
  endpoints:
  - api
$$
QUERY_WAREHOUSE = DATA_API_WH;
```

It will take a few minutes for your service to initialize, you can check status with these commands:

```sql
SHOW SERVICES IN COMPUTE POOL API;
```

```sql
CALL SYSTEM$GET_SERVICE_STATUS('api.public.api');
```

```sql
CALL SYSTEM$GET_SERVICE_LOGS('api.public.api', 0, 'api');
```

After your service has started, you can get the endpoints with the following command. Note that provisioning endpoints
can take a moment. While it does you will get a note like `Endpoints provisioning in progress...`:

```sql
SHOW ENDPOINTS IN SERVICE API.PUBLIC.API;
```

Make note of the `ingress_url` as that will be need to test the application. This service will start the API, running at `https://<INGRESS_URL>`.

<!-- ------------------------ -->
## Testing The API

To verify the API is online, go to the `https://<INGRESS_URL>` in your browser. You will be asked to authenticate to Snowflake and be given the root content: 

```json
{"result":"Nothing to see here"}
```

### Endpoints
This API was implemented using both the Snowflake Python Connector and the Snowflake Snowpark for Python package. 
They both implement the same API routes. The ones implemented with the Snowflke Python Connector are under the `/connector/` route.
The ones implemented with Snowpark Python are under the `/snowpark/` route.

#### Top 10 Customers
To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Connector for Python, use:

```
https://<INGRESS_URL>/connector/customers/top10?start_range=1995-02-01&end_range=1995-02-14
```

To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Snowpark API, use:
```
https://<INGRESS_URL>/snowpark/customers/top10?start_range=1995-02-01&end_range=1995-02-14
```

If you call the endpoint without specifying the `start_range` then `1995-01-01` will be used. If you call the endpoint without specifying the `end_range` then `1995-03-31` will be used.

#### Monthly sales for a given year for a sales clerk
To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Connector for Python, run:
```
https://<INGRESS_URL>/connector/clerk/000000002/yearly_sales/1995
```

To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Snowpark API, run:
```
https://<INGRESS_URL>/snowpark/clerk/000000002/yearly_sales/1995
```

### Testing using a webpage
This project comes with a simple webpage that allows you to test the API. To get to it, open `https://<INGRESS_URL>/test` in a web browser.

At the top you can choose if you want to exercise the Snowflake Connector for Python or the Snowflake Snowpark API endpoints.

There are 2 forms below that. The first one allows you to enter parameters to test the "Top 10 Customers" endpoint. 
The second one allows you to enter parameters to test the "Monthly Clerk Sales" endpoint.

When you hit the `Submit` button, the API endpoint is called and the data is returned to the web page.

<!-- ------------------------ -->
## Programmatic Access

In many situations we want to access this data API from another process outside of Snowflake programmatically. To do this, we will need a way to programmatically 
authenticate to Snowflake to allow access to the SPCS endpoint. There are a number of ways to do this today, but we will focus on using 
Programmatic Access Tokens (PAT), one of the simpler ways.

Regardless of the authenictation method, the best practice is to create a user specifically for accessing this API endpoint, as well as a role for that user. 

To do this, run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS APIROLE;
GRANT ROLE APIROLE TO ROLE ACCOUNTADMIN;
GRANT USAGE ON DATABASE API TO ROLE APIROLE;
GRANT USAGE ON SCHEMA API.PUBLIC TO ROLE APIROLE;
CREATE USER IF NOT EXISTS APIUSER PASSWORD='User123' DEFAULT_ROLE = apirole DEFAULT_SECONDARY_ROLES = ('ALL') MUST_CHANGE_PASSWORD = FALSE;
GRANT ROLE APIROLE TO USER APIUSER;
CREATE NETWORK POLICY IF NOT EXISTS api_np ALLOWED_IP_LIST = ('0.0.0.0/0');
ALTER USER apiuser SET NETWORK_POLICY = api_np;
```

Next, we can grant the service role to access the endpoint to the APIROLE we just created:

```sql
USE ROLE ACCOUNTADMIN;
GRANT SERVICE ROLE api.public.api!api_sr TO ROLE apirole;
```

### Generating a PAT token via SQL
Lastly, we need to create a Programmatic Access Token for the `APIUSER`.
In order to use PAT, the user must have a network policy applied, so we create an "allow-all" network policy for this user. In practice you would limit to the
IP/hostname origins for your clients.You can do this via SQL as follows:

```sql
USE ROLE ACCOUNTADMIN;
ALTER USER IF EXISTS apiuser ADD PROGRAMMATIC ACCESS TOKEN api_token;
```

Copy this PAT token and save it to a file. Save it to a file named `apiuser-token-secret.txt` in the `test/` directory of the cloned/downloaded repo.

### Generating a PAT token via Snowsight
Alternatively, you can use Snowsight to create the PAT token. Click on the "Admin" option on the sidebar, then the "Users & Roles" option in the sidebar.
Next, click on the APIUSER user, and scroll down to the "Programmatic access tokens" section. Click the "Generate new token" button, give the token a name
(such as `api_token`), choose the role `APIROLE` from the pull-down, leave the rest of the defaults, and click "Generate". Click the "Download token" button
and save the file to the `test/` directory (you can leave the default filename).

<!-- ------------------------ -->
## Testing Programmatically

Next we can test accessing our API programmatically using the PAT token. We cannot use the PAT token directly to access the SPCS endpoint.
We must exchange the long-lived PAT token for a shorter-lived access token via the `/oauth/token` Snowflake endpoint. We can then use that
shorter-lived token to access the SPCS endpoint. 

We have 2 applications that demonstrate how to do this.

### Accessing the endpoint via command-line program
Change to the `test/` directory. In there is a program named `test.py`. You can see the usage instructions by running:

```bash
python test.py --help
```

You must supply the following:
* `ACCOUNT_URL` - this is the URL for your Snowflake account. It should be of the form `<ORGNAME>-<ACCTNAME>.snowflakecomputing.com`. You can find this in the
  Snowflake console by clicking the circle with initials in the lower left and choosing the "Connect a tool to Snowflake" menu option. Copy the field
  named "Account/Server URL".
* `ROLE` - the role to use when accessing the endpoint. For this example, it should be `APIROLE`.
* `ENDPOINT` - this is the full URL you are trying to access. E.g., `https://<INGRESS_URL>/connector/customers/top10`

There are 3 ways to specify the PAT to use:
1. Use the `--pat` option and supply the full PAT token. E.g., `--pat <PAT>`.
2. Use the `--patfile` option and supply the filename to the PAT token file. E.g., `--patfile /path/to/patfile`
3. If you saved your PAT token to this directory, and it ends with `-token-secret.txt` the application will discover it and use it.

For example, your call might look something like:

```bash
python test.py --account_url 'MYORG-MYACCT.snowflakecomputing.com' --role APIROLE --endpoint 'https://mzbqa5c-myorg-myacct.snowflakecomputing.app/connector/customers/top10'
```

### Accessing the endpoint via Streamlit
The repository also contains a Streamlit to access the endpoint. 

To use Streamlit we must first install the Streamlit library:

```bash
pip install streamlit
```

Next, change to the `test/` directory, and run:

```bash
python -m streamlit run test_streamlit.py
```

Enter the account URL, role, and URL in the supplied boxes.

The Streamlit will attempt to detect the PAT in the local directory in a file ending with `-token-secret.txt`. If one is found, it will use that as the PAT. 
If not, it will show another box to enter the PAT in (the actual PAT value, not the filename).

Enter the necessary items and click "Fetch it!". You will get a status update that it is "Trading PAT for Token..." and then "Getting data..." and then it will
display the result from SPCS.

<!-- ------------------------ -->
## Stopping The API

To stop the API, you can suspend the service. 
Run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```sql
USE ROLE DATA_API_ROLE;
ALTER SERVICE API.PUBLIC.API SUSPEND;
```

<!-- ------------------------ -->
## Cleanup

To fully remove everything you did today you only need to drop some objects in your Snowflake account. 
Run the following commands in the Snowflake (in a cell in a Snowflake Notebook, in a Worksheet in the Snowflake console, or using SnowSQL):

```SQL
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS API;
DROP ROLE IF EXISTS DATA_API_ROLE;
DROP COMPUTE POOL IF EXISTS API;
DROP WAREHOUSE IF EXISTS DATA_API_WH;
DROP USER IF EXISTS APIUSER;
DROP ROLE IF EXISTS APIROLE;
DROP NETWORK POLICY api_np;
```

You can now turn off your Codespaces environment.

<!-- ------------------------ -->
## Conclusion and Resources
### Overview
You've successfully built a custom API in Python Powered by Snowflake. 

When you go to put a data API into production you should protect the API with some level of authentication and authorization. 

Another consideration is enabling a frontend website to access the endpoint, the test site worked in this example because it's hosted on the same domain as the api. If you need to access the api from another website, you will need to do additional configuration.

To get more comfortable with this solution, implement new endpoints pointing to the sample dataset provided or other datasets.

### What You Learned
- How to configure and build a custom API Powered by Snowflake
- How to run and test the API on your machine

### Resources
Code for this project is available at [https://github.com/sfc-gh-bhess/lab_data_api_python](https://github.com/sfc-gh-bhess/lab_data_api_python).
