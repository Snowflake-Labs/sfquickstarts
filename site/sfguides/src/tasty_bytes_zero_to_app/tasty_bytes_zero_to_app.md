author: Brian Hess, Fredrik Göransson, Charles Yorek, Kesav Rayaprolu 
id: build_a_data_app_with_snowflake
summary: A guide to building and running a data application powered by Snowflake and Node.js
categories: getting-started,app-development,architecture-patterns,solution-examples
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, API 

# Build a Data App with Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 5

Snowflake is a terrific platform on which to build data applications. The unique characteristics and
cloud-based design allow for building applications that scale with data and workload. This tutorial
will go through how to build and deploy both the Processing Layer and the User Interface Layer paired
with Snowflake as the Persistence Layer.

The Processing and User Interface Layers will be built using Node.js. The dataset is a orders history
for a food truck company, Tasty Bytes.

### Prerequisites
- A Snowflake account, and familiarity with the Snowsight interface
- Privileges necessary to create a user, database, and warehouse in Snowflake
- Ability to install and run software on your computer
- Basic experience using git
- Intermediate knowledge of Node.js and React JS

### What You’ll Learn 
- How to configure and build a custom API Powered by Snowflake, written in Node.js
- How to configure and build a custom frontend website to communicate with the API, written in React and Node.js
- How to run and test the frontend and API on your machine

### What You’ll Need 
- [VSCode](https://code.visualstudio.com/download) Installed
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed
- [NPM](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) Installed

### What You’ll Build 
- API Powered by Snowflake built in Node.js
- React JS Web Application that connects to that API


<!-- ------------------------ -->
## Lab 1: Data
Duration: 10

### Overview
In this part of the lab we'll set up our Snowflake account, create database structures to house our data, create a Virtual Warehouse to use for data loading and finally load our Tasty Bytes Food Truck orders data into our ORDERS table and run a few queries to get familiar with the data.


### Step 1.1 Initial Snowflake Setup

For this part of the lab we will want to ensure we run all steps as the ACCOUNTADMIN role 
```sql
-- Change role to accountadmin
use role accountadmin;
```

First we can create a [Virtual Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview) that can be used for data exploration and general querying in this lab.  We'll create this warehouse with a size of `Medium` which is right sized for that use case in this lab.  
```sql
-- Create a virtual warehouse for data exploration
create or replace warehouse query_wh with 
	warehouse_size = 'medium' 
	warehouse_type = 'standard' 
	auto_suspend = 300 
	auto_resume = true 
	min_cluster_count = 1 
	max_cluster_count = 1 
	scaling_policy = 'standard';
```

### Step 1.2 Load Data

Next we will create a database and schema that will house the tables that store our application data.
```sql
-- Create the application database and schema
create or replace database frostbyte_tasty_bytes;
create or replace schema app;
```

This DDL will create the structure for the ORDERS table which is the main source of data for our application in this lab. 
```sql
-- Create table structure for order data 
create or replace table orders (
	order_id number(38,0),
	truck_id number(38,0),
	order_ts timestamp_ntz(9),
	order_detail_id number(38,0),
	line_number number(38,0),
	truck_brand_name varchar(16777216),
	menu_type varchar(16777216),
	primary_city varchar(16777216),
	region varchar(16777216),
	country varchar(16777216),
	franchise_flag number(38,0),
	franchise_id number(38,0),
	franchisee_first_name varchar(16777216),
	franchisee_last_name varchar(16777216),
	location_id number(19,0),
	customer_id number(38,0),
	first_name varchar(16777216),
	last_name varchar(16777216),
	e_mail varchar(16777216),
	phone_number varchar(16777216),
	children_count varchar(16777216),
	gender varchar(16777216),
	marital_status varchar(16777216),
	menu_item_id number(38,0),
	menu_item_name varchar(16777216),
	quantity number(5,0),
	unit_price number(38,4),
	price number(38,4),
	order_amount number(38,4),
	order_tax_amount varchar(16777216),
	order_discount_amount varchar(16777216),
	order_total number(38,4)
);
```

For loading data into the ORDERS table we will create a new Virtual Warehouse sized as a `Large` to help us quickly ingest the data we have stored in an S3 bucket. 
```sql
-- Create a virtual warehouse for data loading
create or replace warehouse load_wh with 
	warehouse_size = 'large' 
	warehouse_type = 'standard' 
	auto_suspend = 300 
	auto_resume = true 
	min_cluster_count = 1 
	max_cluster_count = 1 
	scaling_policy = 'standard';
```
Next we have to create a [STAGE](https://docs.snowflake.com/en/user-guide/data-load-overview) which is a Snowflake object that points to a cloud storage location Snowflake can access to both ingest and query data.  In this lab the data is stored in a publically accessible AWS S3 bucket which we are referencing when creating the Stage object. 
```sql
-- Create stage for loading orders data
create or replace stage tasty_bytes_app_stage
	url = 's3://sfquickstarts/frostbyte_tastybytes/app/orders/';
```
Once we've created both the Virtual Warehouse we want to use for loading data and the Stage which points to where the data resides in cloud storage we can simply [COPY](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table) the data from that Stage into our ORDERS table. 
```sql
-- Copy data into orders table using the load wh
 copy into orders from @tasty_bytes_app_stage;
```


### Step 1.3 Explore Data
Now that we've loaded our data into the ORDERS table we can run a few queries to get familiar with it - but first we will want to change the Virtual Warehouse we're using from the `LOAD_WH` back to the `QUERY_WH` created earlier in the lab. 
```sql
-- Change our Virtual Warehouse context to use our query_wh
 use warehouse query_wh;
```

To begin with we can simply look at a sample of the entire table.
```sql 
-- Simple query to look at 10 rows of data 
select * from orders limit 10;
```

Next we can see how many records we've loaded into the table.  Notice how quickly the query executes - this is due to Snowflake's unique architecture which enables a certain class of queries like this one to pull results from metadata instead of requiring compute to generate the result. You should see that the table has a little more than 231M rows.
```sql 
-- Query to count all records in the table
select count(*) from orders;
```

Next we can see the date range included in our data. You should see that the data ranges from `2022-01-01` to `2022-10-31`.
```sql
-- Query to find the date range of the data
select min(order_ts), max(order_ts) from orders;
```

Finally we can run a more complex query to look at the total revenue by month where we will use a couple of [functions](https://docs.snowflake.com/en/sql-reference-functions) to parse the month number and name from the ORDER_TS column in the ORDERS table. 
```sql
-- Sales by month
select month(order_ts),monthname(order_ts), sum(price)
from orders 
group by month(order_ts), monthname(order_ts)
order by month(order_ts);
```

## Lab 2: Queries
Duration: 20

### Overview
Now that we've done the initial set up within our Snowflake account including loading data into the ORDERS table we will focus on turning our business questions into queries for our application.  

Our queries will be broken into two groups - `Franchise` queries and `Truck Brand` level queries.  For the sake of ease we will focus on the following Franchise, Truck Brand, and Date Range for this part of the lab.

* Franchise:  `1`
* Truck Brand: `Guac 'n Roll`
* Date Range: `2022-01-01` to `2022-03-31`

### Setting Snowsight Context
To ensure the correct context is use for these queries we will set our database, schema, and Virtual Warehouse using the following SQL:
```sql
-- Set query context
use database frostbyte_tasty_bytes;
use schema app;
use warehouse query_wh;
```

### 2.1 Franchise Queries
To answer the business questions about how our overall Franchise business is doing we'll need create the three following queries.  All of the columns required for these exist in the `ORDERS` table and no joining of tables are required. 

1. Top 10 Countries Based on Revenue in a Time Window
2. Top 10 Truck Brands Based on Revenue in a Time Window
3. Year-to-Date Revenue, by Month, per Truck Brand

You can spend some time creating the queries for each of these and then check your answers against the provided queries below by expanding each section. 

<details>
    <summary>Top 10 Countries Based on Revenue in a Time Window</summary>

```sql
SELECT
    TOP 10 country,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= '2022-03-31'
    AND franchise_id = 1
GROUP BY
    country
ORDER BY
    sum(price) desc;
```
</details>

<details>
    <summary>Top 10 Truck Brands Based on Revenue in a Time Window</summary>

```sql
SELECT
    TOP 10 truck_brand_name,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= '2022-03-31'
    AND franchise_id = 1
GROUP BY
    truck_brand_name
ORDER BY
    sum(price) desc;
```
</details>

<details>
    <summary>Year-to-Date Revenue, by Month, per Truck Brand</summary>

```sql
SELECT
    country,
    month(order_ts) as date,
    sum(price) AS revenue
FROM
    app.orders
WHERE
        year(order_ts) = 2022
    AND franchise_id = 1
GROUP BY
    country,
    month(order_ts)
ORDER BY
    sum(price) desc;
```
</details>


### 2.2 Truck Brand Queries
Franchise owners will want to dig deeper into the data and better understand performance trends at the Truck Brand level so we'll need to create four more queries to analyze the data.  All of the columns required for these exist in the `ORDERS` table and no joining of tables are required. 

1. Total Sales by Day-of-Week
2. Top Selling Items
3. Top Selling items by Day-of-Week
4. Best Cities by Day of Week

You can spend some time creating the queries for each of these and then check your answers against the provided queries below by expanding each section. 

<details>
    <summary>Total Sales by Day-of-Week</summary>

```sql
SELECT
    dayofweek(order_ts) as DoW,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= :'2022-03-31'
    AND truck_brand_name = 'Guac ''n Roll'
    AND franchise_id = 1
GROUP BY
    dayofweek(order_ts)
ORDER BY
    dayofweek(order_ts),
        sum(price) desc;
```
</details>

<details>
    <summary>Top Selling Items</summary>

```sql
SELECT
    menu_item_name,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= '2022-03-31'
    AND truck_brand_name = 'Guac ''n Roll'
    AND franchise_id = 1
GROUP BY
    menu_item_name
ORDER BY
    sum(price) desc;
```
</details>

<details>
    <summary>Top Selling items by Day-of-Week</summary>

```sql
SELECT
    dayofweek(order_ts) as DoW,
    menu_item_name,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= '2022-03-31'
    AND truck_brand_name = 'Guac ''n Roll'
    AND franchise_id = 1
GROUP BY
    dayofweek(order_ts),
    menu_item_name
ORDER BY
    dayofweek(order_ts),
        sum(price) desc;
```
</details>

<details>
    <summary>Best Cities by Day of Week</summary>

```sql
SELECT
    dayofweek(order_ts) as DoW,
    primary_city,
    sum(price) AS revenue
FROM
    app.orders
WHERE
    date(order_ts) >= '2022-01-01'
    AND date(order_ts) <= '2022-01-01'
    AND truck_brand_name = 'Guac ''n Roll'
    AND franchise_id = 1
GROUP BY
    dayofweek(order_ts),
    primary_city
ORDER BY
    dayofweek(order_ts),
    sum(price) desc;
```
</details>

## Lab 3: Snowflake Setup

### Overview
Now that we've created our database, loaded data and developed the queries needed to answer our business questions the last step before getting into application code is setting up the necessary objects so that the application can connect to Snowflake securely and query data on its own Virtual Warehouse

### Setting Snowsight Context
To ensure the correct context is use for these queries we will set our database, schema, and Virtual Warehouse using the following SQL:
```sql
-- Set query context
use database frostbyte_tasty_bytes;
use schema app;
use warehouse query_wh;
```

### Step 3.1 Creating the Service User

To enable our application to connect securely to Snowflake we are going to create a service user in the Snowflake account and create a key pair that we will use to authenticate that user.
Start by generating a private and a public key to associate with the user. We will use the following command-line
tools and calls to generate the key pair.
```sh
$ openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out app_user_rsa_key.p8 -nocrypt
Generating RSA private key, 2048 bit long modulus (2 primes)

$ openssl rsa -in app_user_rsa_key.p8 -pubout -out app_user_rsa_key.pub
writing RSA key

$ cat app_user_rsa_key.pub
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmT/
....
+SWsODZKAhqU8PRAqlXhIQIDAQAB
-----END PUBLIC KEY-----
```
You should now have two key files in your folder, app_user_rsa_key.p8 and app_user_rsa_key.pub.
We can now create the service user in Snowflake, in the Snowflake account you created in the earlier lab (as `ACCOUNTADMIN`), run the following:
```sql
-- Change role to accountadmin
use role accountadmin;

-- Create a database role for our application
create role tasty_app_api_role;

-- Grant privileges to the newly created role on required database objects
grant usage on database frostbyte_tasty_bytes to role tasty_app_api_role;
grant usage on schema frostbyte_tasty_bytes.app to role tasty_app_api_role;
grant select on all tables in schema frostbyte_tasty_bytes.app to role tasty_app_api_role;
grant select on future tables in schema frostbyte_tasty_bytes.app to role tasty_app_api_role;

-- Create the service user
create user if not exists tasty_app_api_user
    password = null
    login_name = 'tasty_app_api_user'
    display_name = 'tasty app api user'
    first_name = 'tasty app api user'
    last_name = 'tasty app api user'
    must_change_password = false
    disabled = false
    default_warehouse = tasty_app_api_wh
    default_namespace = frostbyte_tasty_bytes.app
    default_role = tasty_app_api_role
    rsa_public_key = '<rsa_public_key>'
    comment = 'api user for tasty app';

-- Grant the role to the user
grant role tasty_app_api_role to user tasty_app_api_user;
```

Where you replace `<rsa_public_key>` with the contents of the `app_user_rsa_key.pub` file you just created locally (copy everything between the `-----BEGIN PUBLIC KEY-----` and the `-----END PUBLIC KEY-----` lines)

### Step 3.2 Creating a Virtual Warehouse for the Application

Much like we created separate Virtual Warehouses for exploring and loading data, we will create one specifically for our service to use when executing queries on Snowflake. We will also grant the privilege `USAGE` to the service role so that it can use the warehouse. 

```sql
-- Create Warehouse for the API
create or replace warehouse tasty_app_api_wh with 
    warehouse_size = 'small' 
    warehouse_type = 'standard' 
    auto_suspend = 300 
    auto_resume = true 
    min_cluster_count = 1 
    max_cluster_count = 1 
    scaling_policy = 'standard';

-- Grant permission to use the warehouse to the service role
grant usage on warehouse tasty_app_api_wh to role tasty_app_api_role;
```

### Step 3.3 Building the Users Login table
Since our application will be connecting to Snowflake using a service user, we need a place to store the Franchisee login information and encrypted passwords so the application can authenticate them at login. 

```sql
-- Create Users table for the Website
create or replace table users (
	user_id number(38,0) autoincrement,
	user_name varchar(16777216) not null,
	hashed_password varchar(16777216),
	franchise_id number(38,0),
	password_date timestamp_ntz(9),
	status boolean,
	unique (user_name)
);
```

```sql
 -- Add Franchisee logins 
insert into users
    values
    (1,'user1','$2b$10$v0IoU/pokkiM13e.eayf1u3DkgtIBMGO1uRO2O.mlb2K2cLztV5vy',1,current_timestamp,TRUE), 
    (2,'user2','$2b$10$e2TXM/kLlazbH1xl31SeOe6RTyfL3E9mE8sZZsU33AE52rO.u44JC',120,current_timestamp,TRUE),
    (3,'user3','$2b$10$WX4e1LAC.rAabBJV58RuKerEK4T/U4htgXrmedTa5oiGCWIRHwe0e',271,current_timestamp,TRUE);
```

<!-- ------------------------ -->
## Lab 4: Backend Overview
Duration: 50

This lab will take you through building the backend, in the form of an API, that can be called by the frontend application. The backend API will connect to the Snowflake database and serve the results of queries over a number of API endpoints.
We will take the queries designed in the <a href="#3" target="_self">Lab 3: Snowflake Setup</a> and have the results of these queries returned by endpoints in the API.
We will then secure access to the API using bearer authorization tokens in the form of signed JWTs (Javascript Web Tokens). For this lab we are not securing the communication using HTTPS, but in a production environment this should be added.

### Lab 4.1: Setting up the code

The starting code for this lab is hosted on GitHub. You can start by cloning the repository into a separate folder if you haven’t done so already as part of the earlier labs.
```bash
git clone https://github.com/sfc-gh-fgoransson/zero-to-app
```
Change directory to the `zero-to-app/` directory that is created when you clone the repository. You should now have a directory with subdirectories for the different labs. For this lab we will use the `backend/` directory. Open this directory in an IDE (like VSCode).

We will start by adding the Node dependencies to the project. In a terminal window run the following:
```bash
npm i bcrypt body-parser cors dotenv express snowflake-sdk
npm i nodemon --save-dev
```

Start the server by running:
```sh
npm run serve
```

This will run the server and you can access the supplied endpoint in a browser, or using curl:
```sh
curl http://localhost:3000
```

Note that this runs the Node server using `nodemon`, which helps us by restarting the server whenever it detects a change to the code we are working on. However, if you need to stop it, simply press <kbd>Ctrl</kbd> + <kbd>c</kbd> in the terminal where you started it. Once stopped, or if it crashed or something else happend, you can simply run `npm run serve` again to start it back up. In several steps below you are asked to do additional tasks in the terminal/shell, easiest is often to open an additional terminal window for these and keeping the server running in the first one.

### Lab 4.2: Configuring the connection to Snowflake

We can now connect to the Snowflake database we created in the earlier lab. To do so we are going to use the service user in the Snowflake account created in the previous lab. We will need the private key created in [Lab 3](#lab-3-snowflake-setup). If you didn't change the location of where that key was created, we can simply reference it in our code.

In `app.js`, after starting the server on line 17x, add the following:
```js
const options = {
    account: process.env.ACCOUNT,
    username: process.env.USERNAME,
    authenticator: "SNOWFLAKE_JWT",
    privateKeyPath: "../../app_user_rsa_key.p8",
    database: process.env.DATABASE,
    schema: process.env.SCHEMA,
    warehouse: process.env.WAREHOUSE,
};

// Create a new Snowflake connection
const connection = snowflake.createConnection(options);
// Connect to Snowflake
connection.connect((err, conn) => {
    if (err) {
        console.error('Unable to connect to Snowflake', err);
    } else {
        console.log('Connected to Snowflake account ' + options.account);
    }
});
```

Also create a new file called `.env` in the `backend` directory by copying the `.env.example` file:
```sh
cp .env.example .env
```

Edit the `.env` file and replace `REPLACE_WITH_ACCOUNT` with the [account identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier) of your Snowflake account.

To test out the connection, start by replacing the `/` route in the `app.js` file:
```js
app.get("/", (req, res, next) => {
    console.log(req.method + ': ' + req.path);

    connection.execute({
        sqlText: sql_queries.all_franchise_names,
        complete: (err, stmt, rows) => {
            if (err) {
                console.error('Unable to retrieve franchises', err);
                res.status(500).json({ error: 'Unable to retrieve franchises' });
            } else {
                res.status(200).json(rows);
            }
        },
    });
});
```

Here we are executing the SQL command that is defined in the `sql.js` file. Include this file in the `app.js` as a requirement, add the following to the top of `app.js`:
```js
var sql_queries = require('./sql')
```

Open the `sql.js` file and examine the SQL statement being executed. Test this out in a browser [http://localhost:3000/](http://localhost:3000/), or by running a curl command:
```sh
curl http://localhost:3000
```
> aside negative
> **Need help with this step?**
>
> You can set your entire backend folder to the end of this step by running a `git` command to grab it from the repo. In the `/backend` folder (it will only reset changes you have set in this folder), run `git checkout tags/4.2 -- ./`
>
> However, as it will also overwrite the `.p8` key in your backend folder. Copy it again from the root folder where you created it in the first place `cp ../app_user_rsa_key.p8 .`


---
### Lab 4.3: Building the endpoints

We can now add the queries to each endpoint to make them return some more interesting results. Start with the endpoint for getting sales for the top 10 countries:
```js
app.get('/franchise/:franchise/countries/', (req, res) => {
    console.log(req.method + ': ' + req.path);

    const franchise = req.params.franchise
    const startdate = utils.parseDate(req.query.start) ?? utils.defaultStartDate();
    const enddate = utils.parseDate(req.query.end) ?? utils.defaultEndDate();

    console.log('start: ' + startdate + ', end: ' + enddate);

    connection.execute({
        sqlText: sql_queries.top_10_countries,
        binds: [franchise, startdate, enddate],
        complete: (err, stmt, rows) => {
            if (err) {
                console.error('Unable to retrieve order data', err);
                res.status(500).json({ error: 'Unable to retrieve order data' });
            } else {
                res.status(200).json(rows);
            }
        },
    });
});
```

Include the `utils.js` at the top of the `app.js` file:
```js
var utils = require('./utils')
```
This contains helper functions to parse out the supplied query string parameters.

We are now picking up both the franchise id from the parameters of the request, like [http://localhost:3000/franchise/1/countries](http://localhost:3000/franchise/1/countries) and optionally allowing the user to specify a start and end date for the data to be returned, like [http://localhost:3000/franchise/1/countries?start=2022-01-01&end=2022-03-01](http://localhost:3000/franchise/1/countries?start=2022-01-01&end=2022-03-01). These parameters are then bound to the query using the `binds` argument to the `execute()` function call. Looking at the SQL statement in the `sql.js` file, we see how they are used in the condition for the query:
```sql
-- Top 10 Countries
    SELECT
        TOP 10 country,
        sum(price) AS revenue
    FROM
        app.orders
    WHERE
        franchise_id = :1
        AND date(order_ts) >= :2
        AND date(order_ts) <= :3
    GROUP BY
        country
    ORDER BY
        sum(price) desc;
```

In the query, you can see how each argument (`franchise`, `startdate`, `enddate`) passed to the query gets bound to the ordinal markers (`:1`, `:2`, `:3`).

You can now go ahead and implement the remaining endpoints in the same way, by getting the parameters from the request and binding them to the executed SQL statements. Update the SQL statements in the `sql.js` file, using the queries built in the first labs.

The different routes we will add are:
| Route | Method | Query Parameters |
| ------- | --------- | ------- |
| / | Return a list of available franchises and the truck brands for each |
| /franchise/:franchise/countries | Returns a top 10 countries by sales for the specified franchise | |
| /franchise/:franchise/trucks | Returns a top 10 trucks by sales for the specified franchise | startdate and enddate |
| /franchise/:franchise/revenue/:year | Return the revenue for the specified year and truck |
| /franchise/:franchise/trucks/:truckbrandname/sales | Returns the top selling items by truck brand for a specified franchise. By adding a ?analysis=(topitems,dayofweek,topitems_dayofweek) different views of the data is returned | startdate and enddate |
| /franchise/:franchise/trucks/:truckbrandname/locations | Returns the top 10 locations for a truck brand for a specified franchise | startdate and enddate |

The routes can then be filtered by adding `?start=2022-01-01&end=2022-03-01` as optional query parameters.

> aside negative
> Need help with this step?
>
> You can set your entire backend folder to the end of this step by running a `git` command to grab it from the repo. In the `/backend` folder (it will only reset changes you have set in this folder), run `git checkout tags/4.3 -- ./`

---

### Lab 4.4: Securing the API

We should now add a way to secure the access to the API, so that the frontend that we will build in a later lab, can authenticate and we can manage the access to the data and the endpoints.
For this API we will use a HTTP authentication scheme usually referred to as Bearer Authentication. An application, like the frontend, can login using a username and password, and get a signed token back from the backend that in subsequent calls can be included in the header. The token will be signed by the backend so that in later calls the signature can be verified, adding a measure of protection against tampering. It should be noted that in this lab we are not setting up secured communication with HTTPS, but in a production scenario, this should be done to ensure that both username and passwords, as well as tokens sent between backend and frontend, are protected from interception. The very nature of bearer tokens means that anyone in possession of (bearing) a valid token will be given access to the protected resource (hence the name bearer). For this lab we will be using signed JWTs (JSON Web Token), which is a common standard for token authentication.

### Creating access tokens
We will start by generating two random secrets that should be secured with the backend and not shared with other parties. We will use the `node` command-line tool to do this.
```sh
$ node
> require("crypto").randomBytes(64).toString("hex")
'0b5191c5f9257c3999d1c7d1324e66f6af9a187881b52e2a4117afe6c7f901329e0a6bb1bebc5d5ea9e6a98984e288f12bb29950b77c4d98075dba87bdb6c5bb'
> require("crypto").randomBytes(64).toString("hex")
'b8f994547e66fa6cecf3e02ab35275616d900368fe0ca2ac6bf4342ff63abef7d093d6f4d6c574f7d44ee30ea54f6716c6f1c5bef23e61ab9888fccb061ba9f4'
> .exit
```

Generate two random strings like this and add them in the `.env` file.
```sh
ACCESS_TOKEN_SECRET=0b5191c5.....dba87bdb6c5bb
REFRESH_TOKEN_SECRET=b8f99454.....fccb061ba9f4
```

The provided code in the `auth.js` file helps us create access and refresh tokens:
```js
const jwt = require("jsonwebtoken")
module.exports = {

    refreshTokens: [],

    // accessTokens
    generateAccessToken: function(user) {
        return jwt.sign(user, process.env.ACCESS_TOKEN_SECRET, { expiresIn: "360m" })
    },

    // refreshTokens
    generateRefreshToken: function(user) {
        const refreshToken =
            jwt.sign(user, process.env.REFRESH_TOKEN_SECRET, { expiresIn: "20m" })
        this.refreshTokens.push(refreshToken)
        return refreshToken
    },
};
```

Include the `auth.js` at the top of the `app.js` file:
```js
var auth = require('./auth')
```

Notice how the `ACCESS_TOKEN_SECRET` and `REFRESH_TOKEN_SECRET` from the `.env` file are now used to sign the tokens we generate. Having different secrets means that this back backend can uniquely verify that a token was generated and signed by itself.
> aside positive
> Note that here we are setting an expiration time of 360 minutes for the access tokens to make this lab a little easier (meaning a token will not expire during the entire lab), in a production scenario it would likely be a much shorter expiration time, like 15 minutes.

### Adding a login endpoint to the API
In `app.js` we can now add two endpoints to login and get an access token and a refresh token. We will check the supplied username and password with the hashed password in our database in the `USERS` table. Additionally, we will add an endpoint to get a new access token using the refresh token, in case the access token has expired.
```js
app.post("/login", async (req, res) => {
    if(!req.body.name || !req.body.password ) {
        res.status(422).send("Incorrect data")
        return
    }

    const login_user = req.body.name
    const login_password = req.body.password
    connection.execute({
        sqlText: sql_queries.verify_user,
        binds: [login_user],
        complete: (err, stmt, rows) => {
            if (err) {
                console.error('Unable to validate user', err);
                res.status(500).json({ error: 'Unable to validate user' })
                return
            } else {
                if (rows.length == 0){
                    console.log('User does not exist: ' + login_user)
                    res.status(401).json('Invalid user or password')
                    return
                } else {
                    user_row = rows[0]
                    user_name = user_row.USER_NAME
                    hashed_password = user_row.HASHED_PASSWORD
                    franchise_id = user_row.FRANCHISE_ID                    
                    bcrypt.compare(login_password, hashed_password, function(err, result) {
                        if (err){
                            console.log('Failed to check password for: ' + login_user + ' - ' + err.message)
                            res.status(401).json('Invalid user or password')
                            return
                        }
                        if (result){
                            console.log('Successful login, generating token for: ' + user_name + ', franchise: ' + franchise_id)
                            const accessToken = auth.generateAccessToken({ user: req.body.name, franchise: franchise_id })
                            const refreshToken = auth.generateRefreshToken({ user: req.body.name, franchise: franchise_id })
                            res.json({ accessToken: accessToken, refreshToken: refreshToken })
                            return
                        }
                        console.log('Incorrect password for user: ' + login_user)
                        res.status(401).json('Invalid user or password')
                        return
                    });
                }
            }
        },
    });
});

app.post("/refresh", (req, res) => {
    if (!req.body.token)
        res.status(422).send("Incorrect data")
    if (!auth.refreshTokens.includes(req.body.token))
        res.status(400).send("Refresh Token Invalid")
    auth.refreshTokens = auth.refreshTokens.filter((c) => c != req.body.token)
    //remove the old refreshToken from the refreshTokens list
    const accessToken = auth.generateAccessToken({ user: req.body.token.user, franchise: req.body.token.franchise })
    const refreshToken = auth.generateRefreshToken({ user: req.body.token.user, franchise: req.body.token.franchise })
    //generate new accessToken and refreshTokens
    res.json({ accessToken: accessToken, refreshToken: refreshToken })
});
```

> aside positive
> Note how in the login endpoint we are comparing the stored hashed passwords with a hash of the passed in password, meaning we are never storing plaintext passwords in the database, and the only time we are handling the plaintext password is in this method. Again this makes it important to ensure that the communication between the frontend and the backend is secured using HTTPS in a production scenario.

Since we already created users in the first lab and stored hashed passwords for them in the database, we can try out the login endpoint to get an access token:
```sh
curl -X POST http://localhost:3000/login -H 'Content-Type:application/json' -d '{"name":"user2","password":"password120"}'
```

You can inspect the content of the JWT tokens using [JWT.io](JWT.io), paste it in and inspect the payload. It should contain something like this in the payload part:
```json
{
  "user": "user2",
  "franchise": "120",
  "iat": 1681417090,
  "exp": 1681418290
}
```
Just for reference, the users that were created in the earlier database set up lab are the following:

| User name | Hashed password | Franchise id | Plaintext password |
| ------- | --------- | --------------- | ------------ |
| user1	| $2b$10$3/teX....iH7NI1SjoTjhi74a	| 1	| password1 |
| user2	| $2b$10$9wdGi....U8qeK/nX3c9HV8VW	| 120	| password120 |
| user3	| $2b$10$CNZif....IXZFepwrGtZbGqIO	| 271	| password271 |

### Validating tokens
We can now add a validation of the token that should now be included in each call to the backend by adding a middleware to the routes. 

Include the `auth.js` at the top of the `app.js` file:
```js
var auth = require('./auth')
```

In `auth.js` we have a method to validate a token, meaning that the backen can look at a supplied token and verify that is was actually signed using the same secret we generated earlier.
```js
    validateToken: function (req, res, next) {
        ..
        jwt.verify(token, process.env.ACCESS_TOKEN_SECRET, (err, user) => {
            if (err) {
                res.status(403).send("Token invalid")
            }
            else {
                req.user = user
                next() //proceed to the next action in the calling function
            }
        });
    },
```

This validates the JWT token and picks up the user and franchise that should be set in it, we can now access the data in the `req.user` variable in our endpoints.

In `auth.js` we can also have a method to validate that the user has access to the franchise that is requested in the route, meaning that if you log in with a user with a `franchise_id` we simply verify that you in the queries are trying to access that franchise (if not we will throw back an Unauthorized status for the request) :
```js
    validateAccess: function (req, res, next) {
        if (req.user && req.user.franchise) {
            const franchise = req.params.franchise
            if (franchise == req.user.franchise) {
                res.franchise = req.user.franchise
                next()
            }             
            else {
                res.status(403).json({ error: 'Unauthorized' })
            }
        }
        else {
            res.status(403).json({ error: 'Unauthorized' });
        }
    }
```

These two functions can now be added as route middleware (meaning they will be executed as part of the request/response chain), to `app.js` like this:
```js
app.get('/franchise/:franchise/countries/',  auth.validateToken, auth.validateAccess, (req, res) => {
    console.log(req.method + ': ' + req.path);

    const franchise = req.user.franchise
    ...
});
```

Now go ahead and add this to each endpoint in the API, except for the first `/` endpoint, for this one only add the token validation (_because we don't have a `franchise_id` as a parameter to check against_).
```js
app.get('/',  auth.validateToken, (req, res) => {
    console.log(req.method + ': ' + req.path);

    ...
});
```

Test this out by calling an endpoint, using `curl` and supplying the access token we got earlier when testing the `login` endpoint:
```sh
curl http://localhost:3000/ -H "Accept: application/json" -H "Authorization: Bearer eyJhbGciOiJIUzI1....ceiHArwUcaA8"
```


> aside negative
> Need help with this step?
>
> You can set your entire backend folder to the end of this step by running a `git` command to grab it from the repo. In the `/backend` folder (it will only reset changes you have set in this folder), run `git checkout tags/4.4 -- ./`

---

### Lab 4.5 Adding CORS to the API

Since the frontend will be calling the backend from another host, we need to add allowed origins for requests to the backend. 

In the development of this lab we are using `localhost:3000` for the backend and `localhost:3001` for the frontend, when deployed they would have some different hostnames. 

For security reasons, browsers restrict cross-origin HTTP requests initiated from scripts, meaning that if we don’t explicitly allow another origin, like `localhost:3001` to request a resource from our API it will be blocked.

We solve this in Node Express by adding the `cors` package to the application and then configuring the allowed origins.

Right before we start the server in `app.js`, add the following to allow CORS (Cross Origin Request Scripting) for the frontend that we will later build:
```js
app.use(cors({
    origin: ['http://localhost:3001']
}));
```

> aside negative
> Need help with this step?
>
> You can set your entire backend folder to the end of this step by running a `git` command to grab it from the repo. In the `/backend` folder (it will only reset changes you have set in this folder), run `git checkout tags/4.5 -- ./`

---

### Lab 4.6 Finalizing the API

The backend is now ready to be used by the frontend. We can do some final updates to the API to make it easier to manage and making it a little more flexible.

First, we move all configuration in `app.js` to an environment file. This will help us when are deploying it somwhere else:
```js
cors_origin = process.env.CORS_ADDRESS ?? 'http://localhost:3001'
app.use(cors({
    origin: [cors_origin]
}));

app.use(express.json())

port = process.env.PORT ?? 3000
environment = process.env.NODE_ENV
app.listen(port, () => {    
    environment = app.get('env')
    console.log('Server running on port ' + port);
    console.log('Environment: ' + environment)
    console.log('CORS origin allowed: ' + cors_origin)
});
```

Since we may want to test out the API, without having to add a bearer token to the request header (which is not possible with a regular browser window), we can add a simple way to bypass the validation. We only allow this when the API is running in development mode however. In the `auth.js` file we can update the `validateToken` function:
```js
    validateToken: function (req, res, next) {
        //get token from request header
        const authHeader = req.headers["authorization"]
        if (authHeader == null) {
            environment = process.env.NODE_ENV
            if('development'==environment){
                if (process.env.DEV_AUTH_USER){
                    console.warn('Development mode: no auth header found, accepting user ' + process.env.DEV_AUTH_USER + ' fron environment variables')
                    req.user = {user:process.env.DEV_AUTH_USER, franchise:process.env.DEV_AUTH_FRANCHISE}
                    next()
                    return
                }
            }
            res.status(400).send("Auth header not present")
            return
        }
        ...
```

With this, if we add the `NODE_ENV=development` variable to the environment variables, we can bypass the token validation and use a preset user (`DEV_AUTH_USER=user1`) and franchise (`DEV_AUTH_FRANCHISE=1`). This is great for testing and development, but should of course not be present in the production deployment of the API.

The final `.env` file would then look like this:
```sh
ACCOUNT=my_account_123
USERNAME=tasty_app_api_user
DATABASE=FROSTBYTE_TASTY_BYTES
SCHEMA=RAW_POS
WAREHOUSE=TASTY_DATA_APP_WH

ACCESS_TOKEN_SECRET=0b5191c5f9257c3999d1c7d1324e66f6af9a187881b52e2a4117afe6c7f901329e0a6ba1bebc5d5ea9e6a98984e288f12bb29950b77c4d98075dba87bdb6c5bb
REFRESH_TOKEN_SECRET=b8f994547e66fa6cecf3e02ab35275616d900368fe0ca2ac6bf4342ff63abef7d093d6f4d6e574f7d44ee30ea54f6716c6f1c5bef23e61ab9888fccb061ba9f4

PORT=3000
CORS_ADDRESS=http://localhost:3001
NODE_ENV=development
DEV_AUTH_USER=user1
DEV_AUTH_FRANCHISE=1
```

> aside negative
> Need help with this step?
>
> You can set your entire backend folder to the end of this step by running a `git` command to grab it from the repo. In the `/backend` folder (it will only reset changes you have set in this folder), run `git checkout tags/4.6 -- ./`


<!-- ------------------------ -->
## Lab 5: Frontend Overview
Duration: 40

This lab will take you through building a React JS frontend that can then be displayed in your favorite browser. The frontend will connect to the backend API which then connects to the Snowflake database and serves the results of queries over a number of API endpoints. The query results are then rendered in the browser as charts which are then easily consumed by the end users.

We will take the API Endpoints designed in the [Data API Lab](#lab-4-backend-overview) and display charts on the web page.

In this lab we are not securing the communication using HTTPS, but in a production environment this should be added.


### Lab 5.1: Setting up the code

The starting code for this lab is in the GitHub repository we cloned earlier. For this lab we will use the `frontend` subdirectory from the main directory. Open this folder in an IDE (like VSCode).

We will start by adding the Node dependencies to the project. In a terminal window run the following:
```sh
npm i react
npm i react-bootstrap
npm i recharts
```

Start the server by running:
```sh
npm start
```

This will start a development web server and you can access the web application in a browser:
```sh
http://localhost:3001/
```

To stop the Web Server, simply terminate the task that started the server, press <kbd>Ctrl</kbd>+<kbd>c</kbd>

---
### Lab 5.2: Configuring the connection to Backend APIs

We can now connect to the Snowflake database using the Backend APIs we created in the earlier lab. 

To configure the application, copy the example file `.env.example` to create a new file in the frontend directory called `.env`
```sh
cp .env.example .env
```

---
### Lab 5.3: Building the UI.

On successful Login, the Backend API returns ***Franchise_Id*** and ***AccessToken***, we will use them to make subsequent calls to the Backend API. 

We can now start building the UI. Let us start with building a Bar Chart for the ***Sales for the Top 10 Countries***. The Backend API end point is `/franchise/:franchise/countries`, optionally specifying the Start and End dates. 

First, let us fetch Data from Backend for Sales by Top10 Countries. Update the stubbed method in ***pages/Home.js*** add a variable to hold the data returned by the backend as Step1.
```js
let [top10Countries, setTop10Countries] = useState([]);
```
add the following code as Step2.
```js
function fetchTop10Countries() {
    const requestOptions = {
        method: 'GET',
        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + location.state.accessToken },
    };
    fetch(backendURL+'/franchise/'+franchise+'/countries?start='+fromDate+'&end='+toDate, requestOptions)
        .then((result) => result.json())
            .then((data) => {
                setTop10Countries(data)
    })
}
```
We are using the Franchise_id and the accessToken we recieved from the Backend API on successful Login. AccessToken is then validated by the Backend API and the Snowflake query is executed and the results are returned, we convert the results to JSON and store in a local variable.

In the requestOptions, we are setting the Request Method (GET/POST), and we are sending the accessToken in the header as a Bearer Token.

Update the React UI hooks, so the newly created method is called when the page is requested. Update the useEffect() method as Step3, to add the following.

```js
fetchTop10Countries();
```

Now that we have the data from the Backend API, we can build the BarChart, to do that, we are using a react library ***recharts***. Add the below is the code as Step4 to display the chart.

```html 
<ResponsiveContainer width="100%" height="100%">
    <BarChart
        layout='vertical'
        width={700}
        height={0}
        data={top10Countries}
        margin={{top: 15, right: 15, left: 25, bottom: 5,}}>
        <XAxis type="number" dataKey="REVENUE" tickFormatter={tickFormater}>
        </XAxis>                            
        <YAxis type="category" dataKey="COUNTRY">
        </YAxis>
        <Tooltip formatter={(value) => 'US$'+(new Intl.NumberFormat('en').format(value))} />
        <Bar dataKey="REVENUE" fill="#548bf2">
            <LabelList dataKey="REVENUE" position="insideRight" fill='white' formatter={labelFormatter} />
        </Bar>
    </BarChart>
</ResponsiveContainer>
```

Now uet us add a Bar Chart for the ***Sales for the Top 10 Trucks***. The Backend API end point is `/franchise/:franchise/trucks`, optionally specifying the Start and End dates. 

Let us fetch Data from Backend for Sales by Top10 Trucks. In this method, since we are fetching Top Trucks, we will add a little bit of complexity to store unique list of Trucks. Update the stubbed method in ***pages/Home.js*** add a variable to hold the data returned by the backend as Step1.
```js
let [top10Trucks, setTop10Trucks] = useState([]); //used to hold Sales of the Top 10 Trucks
let [trucks, setTrucks] = useState([]); // used to hold unique Trucks brands.
```
add the following code as Step2.
```js
function fetchTop10Trucks() {
    const requestOptions = {
            method: 'GET',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + location.state.accessToken },
    };
    fetch(backendURL+'/franchise/'+franchise+'/trucks?start='+fromDate+'&end='+toDate, requestOptions)
        .then((result) => result.json())
            .then((data) => {
                setTop10Trucks(data)
                let t = [];

                for (let i=0; i<data.length; i++) {
                    t.push(data[i].TRUCK_BRAND_NAME);
                }
                setTrucks(t);
        })
}
```
We are using the Franchise_id and the accessToken we recieved from the Backend API on successful Login. AccessToken is then validated by the Backend API and the Snowflake query is executed and the results are returned, we convert the results to JSON and store in a local variable.

In the requestOptions, we are setting the Request Method (GET/POST), and we are sending the accessToken in the header as a Bearer Token.

Update the React UI hooks, so the newly created method is called when the page is requested. Update the useEffect() method as Step3, to add the following.

```js
fetchTop10Trucks();
```

Now that we have the data from the Backend API, we can build the BarChart, to do that, we are using a react library ***recharts***. Add the below is the code as Step4 to display the chart.

```html 
<ResponsiveContainer width="100%" height="100%">
    <BarChart
        layout='horizontal'
        width={700}
        height={0}
        data={top10Trucks}
        margin={{top: 15, right: 15, left: 25, bottom: 5,}}>
        <XAxis type="category" dataKey="TRUCK_BRAND_NAME" />
        <YAxis type="number" dataKey="REVENUE"  tickFormatter={tickFormater} />                       
        <Tooltip formatter={(value) => 'US$'+(new Intl.NumberFormat('en').format(value))} />
        <Bar dataKey="REVENUE" fill="#548bf2">
            <LabelList dataKey="REVENUE" position="top" fill='grey' formatter={labelFormatter} />
        </Bar>
    </BarChart>
</ResponsiveContainer>
```

You should see the below chart displayed in your browser running the Web Application.

![Alt text](chart1.png)

The final step to finish the page is to add the navigation to the Truck Details page, to do so add the following code as Step5.
```js
function gotoDetails() {
    navigate('/details', {state: {franchise: franchise, truck_brand_name: top10Trucks[0]['TRUCK_BRAND_NAME'], fromDate: fromDate, toDate:toDate, trucks: trucks, accessToken: location.state.accessToken, refreshToken: location.state.refreshToken}});
}
```


---
### Lab 5.4: Use the Website.

The web application has 3 pages (Login Page, Franchise Page and Truck Details Page)

***Login as User***, is the way for a user to be validated and also establish a session in the Backend for the user. This is a simple page, when user enters their username and password and press Login button, user is authenticated and is navigated to the Franchise View. 
![Alt text](Login_Screen.png)

***Franchise View***, displays various charious charts like Sales for Top 10 Countries, Sales from Top 10 Trucks and the YTD revuenue for the *Franchise*. On this page, user is presented with 2 date pickers to choose Start and End Dates which are used for filtering the data. 

The user can then navigate to the Truck Details page by clicking on the Truck Details button on the top right. 

![Alt text](Home_Screen.png)

***Truck Details View***, displays various charts like Top Items, Sales by Day-of-Week, Best Sellers by Day-of-Week, Best Cities by Day-of-Week for the selected *Franchise* and *Truck Brand*. On this page, the user is presented with the same 2 date pickers from the previous page. In addition, the user has the option to choose a Truck Brand. 

The user can navigate back to the Franchise page, by clicking on the *Back to Overview* button on the top right.

![Alt text](Truck_Details_Screen.png)

<!-- ------------------------ -->


## Lab 6: Cleanup

### Front End 
There isn't very much to clean up or tear down after this lab. When you don't need the frontend any more stop the development web server, simply by terminating the task that started the server, press <kbd>Ctrl</kbd>+<kbd>c</kbd>.

### Back End
To make sure that the backend is not running any more, simply terminate the task that started the server, press <kbd>Ctrl</kbd>+<kbd>c</kbd>.

### Snowflake Database
To clean up your Snowflake environment you can run the following SQL Statements. 

```sql 
drop database frostbyte_tasty_bytes;
drop warehouse query_wh;
drop warehouse load_wh;
drop warehouse tasty_app_api_wh;
drop user tasty_app_api_user;
drop role tasty_app_api_role;
```