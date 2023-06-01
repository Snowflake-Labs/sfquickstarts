author: Brian Hess
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
- Privileges necessary to create a user, database, and warehouse in Snowflake
- Privileges necessary to access the tables in the `SNOWFLAKE_SAMPLE_DATA.TPCH_SF10` database and schema
- Access to run SQL in the Snowflake console or SnowSQL
- Ability to install and run software on your computer
- Basic experience using git
- Intermediate knowledge of Python

### What You’ll Learn 
- How to configure and build a custom API Powered by Snowflake
- How to run and test the API on your machine

### What You’ll Need 
- [GitHub](https://github.com/) Account
- [VSCode](https://code.visualstudio.com/download) Installed
- [Python 3](https://www.python.org/) Installed
- [Anaconda miniconda](https://docs.conda.io/en/latest/miniconda.html) Installed

### What You’ll Build 
- API Powered by Snowflake

<!-- ------------------------ -->
## Setting up a Warehouse
Duration: 1

The API needs a warehouse to query the datato return to the caller. To create the database and warehouse, connect to Snowflake and run the following commands in the Snowflake console or using SnowSQL:

```sql
USE ROLE ACCOUNTADMIN;
CREATE WAREHOUSE DATA_API_WH WITH WAREHOUSE_SIZE='medium';
```

<!-- ------------------------ -->
## Create a Service User for the API
Duration: 5

You will now create a user account separate from your own that the API will use to query Snowflake. In keeping with sound security practices, the account will use key-pair authentication and have limited access in Snowflake.

### Create an RSA key for Authentication

Run the following commands to create a private and public key. These keys are necessary to authenticate the service account we will use.

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
CREATE ROLE DATA_API_ROLE;

GRANT USAGE ON WAREHOUSE DATA_API_WH TO ROLE DATA_API_ROLE;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE DATA_API_ROLE;

CREATE USER "DATA_API" RSA_PUBLIC_KEY='RSA_PUBLIC_KEY_HERE' DEFAULT_ROLE=DATA_API_ROLE DEFAULT_WAREHOUSE=DATA_API_WH DEFAULT_NAMESPACE=SNOWFLAKE_SAMPLE_DATA.TPCH_SF10 MUST_CHANGE_PASSWORD=FALSE;

GRANT ROLE DATA_API_ROLE TO USER DATA_API;
```

<!-- ------------------------ -->
## Downloading the Code
Duration: 3

The code used in this guide is hosted in github. You can download the code as a ZIP from [GitHub](https://github.com/sfc-gh-bhess/lab_data_api_python) or use the following git command to clone the repository.

```bash
git clone https://github.com/sfc-gh-bhess/lab_data_api_python.git
```

After downloading you will have a folder `lab_data_api_python` containing all the code needed for the API. Open the folder in VSCode to review the project.

### Endpoints
The API creates two sets of endpoints, one for using the Snowflake connector:
1. `http://localhost:8001/connector/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `http://localhost:8001/connector/clerk/<CLERKID>/yearly_sales/<YEAR>`
  * Which takes 2 required path parameters:
    1. `CLERKID` - the clerk ID. Use just the numbers, such as `000000001`.
    2. `YEAR` - the year to use, such as `1995`.

And the same ones using Snowpark:
1. `http://localhost:8001/snowpark/customers/top10`
  * Which takes the following optional query parameters:
    1. `start_range` - the start date of the range in `YYYY-MM-DD` format. Defaults to `1995-01-01`.
    1. `end_range` - the end date of the range in `YYYY-MM-DD` format. Defaults to `1995-03-31`.
2. `http://localhost:8001/snowpark/clerk/<CLERKID>/yearly_sales/<YEAR>`
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

You can also review the other endpoints in [connector.py](https://github.com/sfc-gh-bhess/lab_data_api_python/blob/main/src/connector.py) to see how simple it is to host multiple endpoints.

If you would also like to see how to build endpoints using the Snowflake Snowpark API, review [snowpark.py](https://github.com/sfc-gh-bhess/lab_data_api_python/blob/main/src/snowpark.py).



<!-- ------------------------ -->
## Creating the Python environment
Duration: 5

To create a Python environment we will leverage Anaconda. The code includes a configuration file that can be used to create a Python environment with all of the necessary packages and prerequisites. To create a new Anaconda environment, run:
```bash
conda env create -f conda_environment.yml
```

This will create an environment named `pylab`, and will activate it. To activate this environment at a later time, you can run:
```bash
conda activate pylab
```

To deactivate the conda environment, run:
```bash
conda deactivate
```


<!-- ------------------------ -->
## Configuring the API
Duration: 3

The `src/config.py` file is setup to configure the application. It contains a single Python dictionary `creds`.

Copy the `config.py.example` to `config.py`.yml. Update the `config.py` by replacing:
* `&lt;SNOWFLAKE ACCOUNT&gt;` with your Snowflake account identifier, 
* `&lt;SNOWFLAKE USER&gt;` with the user you created earlier, `DATA_API`,
* `&lt;SNOWFLAKE WAREHOUSE&gt;` with the warehouse you created earlier, `DATA_API_WH`,
* `&lt;SNOWFLAKE PRIVATE KEY&gt;` with the private key you created earlier; include the `-----BEGIN RSA PRIVATE KEY-----` header and the `-----END RSA PRIVATE KEY-----` footer.

<!-- ------------------------ -->
## Starting the API
Duration: 3

To start the Python Flask API, change to the `src/` directory and run the following:
```bash
python app.py
```

This will start the API, listening on port `8001`.

<!-- ------------------------ -->
## Testing the API
Duration: 5

### Testing using cURL
The API can be tested using the cURL command-line tool.

#### Top 10 Customers
To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Connector for Python, run:
```bash
curl -X GET "http://localhost:8001/connector/customers/top10?start_range=1995-02-01&end_range=1995-02-14"
```

To retrieve the top 10 customers in the date range of `1995-02-01` to `1995-02-14` using the Snowflake Snowpark API, run:
```bash
curl -X GET "http://localhost:8001/snowpark/customers/top10?start_range=1995-02-01&end_range=1995-02-14"
```

If you call the endpoint without specifying the `start_range` then `1995-01-01` will be used. If you call the endpoint without specifying the `end_range` then `1995-03-31` will be used.

#### Monthly sales for a given year for a sales clerk
To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Connector for Python, run:
```bash
curl -X GET "http://localhost:8001/connector/clerk/000000002/yearly_sales/1995"
```

To retrieve the monthly sales for clerk `000000002` for the year `1995` using the Snowflake Snowpark API, run:
```bash
curl -X GET "http://localhost:8001/snowpark/clerk/000000002/yearly_sales/1995"
```

### Testing using the testing webpage
This project comes with a simple webpage that allows you to test the API. To get to it, open `http://localhost:8001/test` in a web browser.

At the top you can choose if you want to exercise the Snowflake Connector for Python or the Snowflake Snowpark API endpoints.

There are 2 forms below that. The first one allows you to enter parameters to test the "Top 10 Customers" endpoint. The second one allows you to enter parameters to test the "Montly Clerk Sales" endpoint.

When you hit the `Submit` button, the API endpoint is called and the data is returned to the web page.

<!-- ------------------------ -->
## Stopping the API
Duration: 1

To stop the API, simply stop the Python process using `CTRL-C` in the terminal in which you started the API.

<!-- ------------------------ -->
## Cleanup
Duration: 5

To fully remove everything you did today you only need to drop some objects in your Snowflake account. From the Snowflake console or SnowSQL, as `ACCOUNTADMIN` run:
```SQL
USE ACCOUNTADMIN;

DROP WAREHOUSE DATA_API_WH;
DROP USER "DATA_API";
DROP ROLE DATA_API_ROLE;
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

You've successfully built a custom API in Python Powered by Snowflake. 

When you go to put a data API into production you should protect the API with some level of authentication and authorization. You can do this at the network layer (e.g., via integration with an application load balancer) or at the web server layer (in our case in Flask, so consider OAuth via the [Flask-OAuth](https://pythonhosted.org/Flask-OAuth/) package). 

Another consideration is enabling a frontend website to access the endpoint, which may involve enabling Cross Origin Resource Sharing (CORS). Consider the [Flask-CORS](https://flask-cors.readthedocs.io/en/latest/) package

To get more comfortable with this solution, implement new endpoints pointing to the sample dataset provided or other datasets.

Code for this project is available at [https://github.com/sfc-gh-bhess/lab_data_api_python](https://github.com/sfc-gh-bhess/lab_data_api_python).

### What we've covered
- How to configure and build a custom API Powered by Snowflake
- How to run and test the API on your machine
