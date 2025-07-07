author: Cameron Shimmin
id: tasty_bytes_zero_to_snowflake_getting_started
summary: Tasty Bytes - Zero to Snowflake - Getting Started with Snowflake
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Data Warehousing, Time Travel

# Tasty Bytes - Zero To Snowflake - Getting Started with Snowflake
<!-- ------------------------ -->

## Getting Started with Core Snowflake Features
Duration: 1
<!-- <img src="assets/getting_started_header.png"> -->

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Getting Started with Snowflake!

Within this Quickstart, we will learn about core Snowflake concepts by exploring Virtual Warehouses, using the query results cache, performing basic data transformations, leveraging data recovery with Time Travel, and monitoring our account with Resource Monitors and Budgets.

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- How to create, configure, and scale a Virtual Warehouse.
- How to leverage the Query Result Cache.
- How to use Zero-Copy Cloning for development.
- How to transform and clean data.
- How to instantly recover a dropped table using UNDROP.
- How to create and apply a Resource Monitor.
- How to create a Budget to monitor costs.
- How to use Universal Search to find objects and information.

### What You Will Build
- A Snowflake Virtual Warehouse
- A development copy of a table using Zero-Copy Clone
- A Resource Monitor
- A Budget

## Creating a Worksheet in Workspaces and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart, we will follow a Tasty Bytes-themed story via a Snowsight SQL Worksheet. This page will serve as a side-by-side guide complete with additional commentary, images, and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming it, and pasting in the SQL we will be leveraging.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account.

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.

### Step 3 - Navigating to Workspaces
- Click on the **Projects** Tab in the left-hand navigation bar and click **Workspaces**.

### Step 4 - Creating a Worksheet
- Within Workspaces, click the **"+ Add New"** button in the top-right corner of Snowsight.

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Getting Started with Snowflake".

### Step 6 - Pasting SQL into your Snowflake Worksheet
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** 
Asset:        Zero to Snowflake v2 - Getting Started with Snowflake
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

-- Before we start, run this query to set the session query tag.
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "getting_started_with_snowflake"}}';

-- We'll begin by setting our Workspace context. We will set our database, schema and role.

USE DATABASE tb_101;
USE ROLE accountadmin;

/* 1. Virtual Warehouses & Settings */

-- Let's first look at the warehouses that already exist on our account that you have access privileges for
SHOW WAREHOUSES;

-- You can easily create a warehouse with a simple SQL command
CREATE OR REPLACE WAREHOUSE my_wh
    COMMENT = 'My TastyBytes warehouse'
    WAREHOUSE_TYPE = 'standard'
    WAREHOUSE_SIZE = 'xsmall'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 2
    SCALING_POLICY = 'standard'
    AUTO_SUSPEND = 60
    INITIALLY_SUSPENDED = true,
    AUTO_RESUME = false;

-- Use the warehouse
USE WAREHOUSE my_wh;

-- We can try running a simple query, however, you will see an error message in the results pane
SELECT * FROM raw_pos.truck_details;
    
-- Resume the warehouse
ALTER WAREHOUSE my_wh RESUME;
 
-- Set auto-resume to true
ALTER WAREHOUSE my_wh SET AUTO_RESUME = TRUE;

-- The warehouse is now running, so lets try to run the query from before 
SELECT * FROM raw_pos.truck_details;

-- Scale up our warehouse
ALTER WAREHOUSE my_wh SET warehouse_size = 'XLarge';

-- Let's now take a look at the sales per truck.
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;

/* 2. Using Persisted Query Results */

-- We'll now start working with a smaller dataset, so we can scale the warehouse back down
ALTER WAREHOUSE my_wh SET warehouse_size = 'XSmall';


/* 3. Basic Transformation Techniques */

-- SELECT the truck_build column
SELECT truck_build FROM raw_pos.truck_details;

-- Create the truck_dev table as a Zero Copy clone of the truck table
CREATE OR REPLACE TABLE raw_pos.truck_dev CLONE raw_pos.truck_details;

-- Verify successful truck table clone into truck_dev 
SELECT TOP 15 * FROM raw_pos.truck_dev
ORDER BY truck_id;

-- Add new columns
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS year NUMBER;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS make VARCHAR(255);
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS model VARCHAR(255);

-- Update the new columns with the data extracted from the truck_build column.
UPDATE raw_pos.truck_dev
SET 
    year = truck_build:year::NUMBER,
    make = truck_build:make::VARCHAR,
    model = truck_build:model::VARCHAR;

-- Verify the 3 columns were successfully added and populated
SELECT year, make, model FROM raw_pos.truck_dev;

-- Count the different makes
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_dev
GROUP BY make
ORDER BY make ASC;

-- Use UPDATE to change any occurrence of 'Ford_' to 'Ford'
UPDATE raw_pos.truck_dev
    SET make = 'Ford'
    WHERE make = 'Ford_';

-- Verify the make column has been successfully updated 
SELECT truck_id, make 
FROM raw_pos.truck_dev
ORDER BY truck_id;

-- SWAP the truck table with the truck_dev table
ALTER TABLE raw_pos.truck_details SWAP WITH raw_pos.truck_dev; 

-- Run the query from before to get an accurate make count
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_details
GROUP BY
    make
ORDER BY count DESC;

-- Drop the old truck build column
ALTER TABLE raw_pos.truck_details DROP COLUMN truck_build;

-- Now we can drop the truck_dev table (on purpose for the next step!)
DROP TABLE raw_pos.truck_details;

/* 4. Data Recovery with UNDROP */
-- Optional: run this query to verify the 'truck' table no longer exists
DESCRIBE TABLE raw_pos.truck_details;

-- Run UNDROP on the production 'truck' table to restore it
UNDROP TABLE raw_pos.truck_details;

-- Verify the table was successfully restored
SELECT * from raw_pos.truck_details;

-- Now drop the real truck_dev table
DROP TABLE raw_pos.truck_dev;

/* 5. Resource Monitors */
USE ROLE accountadmin;

-- Run the query below to create the resource monitor via SQL
CREATE OR REPLACE RESOURCE MONITOR my_resource_monitor
    WITH CREDIT_QUOTA = 100
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 75 PERCENT DO NOTIFY
             ON 90 PERCENT DO SUSPEND
             ON 100 PERCENT DO SUSPEND_IMMEDIATE;

-- With the Resource Monitor created, apply it to my_wh
ALTER WAREHOUSE my_wh 
    SET RESOURCE_MONITOR = my_resource_monitor;

/* 6. Budgets */
-- Let's first create our budget
CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET my_budget()
    COMMENT = 'My Tasty Bytes Budget';


-------------------------------------------------------------------------
--RESET--
-------------------------------------------------------------------------
-- Drop created objects
DROP RESOURCE MONITOR IF EXISTS my_resource_monitor;
DROP TABLE IF EXISTS raw_pos.truck_dev;
-- Reset truck details
CREATE OR REPLACE TABLE raw_pos.truck_details
AS 
SELECT * EXCLUDE (year, make, model)
FROM raw_pos.truck;

DROP WAREHOUSE IF EXISTS my_wh;

-- Unset Query Tag
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Virtual Warehouses and Settings

Duration: 3

### Overview

Virtual Warehouses are the dynamic, scalable, and cost-effective computing power that lets you perform analysis on your Snowflake data. Their purpose is to handle all your data processing needs without you having to worry about the underlying technical details.

### Step 1 - Setting Context

First, lets set our session context. To run the queries, highlight the three queries at the top of your worksheet and click the "► Run" button.

```sql
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "getting_started_with_snowflake"}}';

USE DATABASE tb_101;
USE ROLE accountadmin;
```

### Step 2 - Creating a Warehouse

Let's create our first warehouse\! This command creates a new X-Small warehouse that will initially be suspended and will not auto-resume.

```sql
CREATE OR REPLACE WAREHOUSE my_wh
    COMMENT = 'My TastyBytes warehouse'
    WAREHOUSE_TYPE = 'standard'
    WAREHOUSE_SIZE = 'xsmall'
    MIN_CLUSTER_COUNT = 1
    MAX_CLUSTER_COUNT = 2
    SCALING_POLICY = 'standard'
    AUTO_SUSPEND = 60
    INITIALLY_SUSPENDED = true,
    AUTO_RESUME = false;
```

> **Virtual Warehouses**: A virtual warehouse, often referred to simply as a “warehouse”, is a cluster of compute resources in Snowflake. Warehouses are required for queries, DML operations, and data loading. For more information, see the [Warehouse Overview](https://docs.snowflake.com/en/user-guide/warehouses-overview).

### Step 3 - Using and Resuming a Warehouse

Now that we have a warehouse, we must set it as the active warehouse for our session. Execute the next statement.

```sql
USE WAREHOUSE my_wh;
```

If you try to run a query now, it will fail, because the warehouse is suspended. Let's resume it and set it to auto-resume in the future.

```sql
ALTER WAREHOUSE my_wh RESUME;
ALTER WAREHOUSE my_wh SET AUTO_RESUME = TRUE;
```

Now, try the query again. It should execute successfully.

```sql
SELECT * FROM raw_pos.truck_details;
```

### Step 4 - Scaling a Warehouse

Warehouses in Snowflake are designed for elasticity. We can scale our warehouse up on the fly to handle a more intensive workload. Let's scale our warehouse to an X-Large.

```sql
ALTER WAREHOUSE my_wh SET warehouse_size = 'XLarge';
```

With our larger warehouse, let's run a query to calculate total sales per truck brand.

```sql
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;
```

<!-- \<img src="assets/query\_results\_pane.png"/\> -->

### Step 5 - Click Next --\>

## Using Persisted Query Results

Duration: 1

### Overview

This is a great place to demonstrate another powerful feature in Snowflake: the Query Result Cache. When you first ran the 'sales per truck' query, it likely took several seconds. If you run the exact same query again, the result will be nearly instantaneous.

### Step 1 - Re-running a Query

Run the same 'sales per truck' query from the previous step. Note the execution time in the query details pane. It should be much faster.

```sql
SELECT
    o.truck_brand_name,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.price) AS total_sales
FROM analytics.orders_v o
GROUP BY o.truck_brand_name
ORDER BY total_sales DESC;
```

> **Query Result Cache**: Results are retained for any query for 24 hours. Hitting the result cache requires almost no compute resources, making it ideal for frequently run reports or dashboards. The cache resides in the Cloud Services Layer, making it globally accessible to all users and warehouses in the account. For more information, please visit the [documentation on using persisted query results](https://docs.snowflake.com/en/user-guide/querying-persisted-results).

### Step 2 - Scaling Down

We will now be working with smaller datasets, so we can scale our warehouse back down to an X-Small to conserve credits.

```sql
ALTER WAREHOUSE my_wh SET warehouse_size = 'XSmall';
```

### Step 3 - Click Next --\>

## Basic Data Transformation Techniques

Duration: 3

### Overview

In this section, we will see some basic transformation techniques to clean our data and use Zero-Copy Cloning to create development environments. Our goal is to analyze the manufacturers of our food trucks, but this data is currently nested inside a `VARIANT` column.

### Step 1 - Creating a Development Table with Zero-Copy Clone

First, let's take a look at the `truck_build` column. 
```sql
SELECT truck_build FROM raw_pos.truck_details;
```
This table contains data about the make, model and year of each truck, but it is nested, or embedded in an Object. We can perform operations on this column to extract these values, but first we'll create a development copy of the table.

Let's create a development copy of our `truck_details` table. Snowflake's Zero-Copy Cloning lets us create an identical, fully independent copy of the table instantly, without using additional storage.

```sql
CREATE OR REPLACE TABLE raw_pos.truck_dev CLONE raw_pos.truck_details;
```

> **[Zero-Copy Cloning](https://docs.snowflake.com/en/user-guide/object-clone)**: Cloning creates a copy of a database object without duplicating the storage. Changes made to either the original or the clone are stored as new micro-partitions, leaving the other object untouched.

### Step 2 - Adding New Columns and Transforming Data

Now that we have a safe development table, let's add columns for `year`, `make`, and `model`. Then, we will extract the data from the `truck_build` `VARIANT` column and populate our new columns.

```sql
-- Add new columns
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS year NUMBER;
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS make VARCHAR(255);
ALTER TABLE raw_pos.truck_dev ADD COLUMN IF NOT EXISTS model VARCHAR(255);

-- Extract and update data
UPDATE raw_pos.truck_dev
SET 
    year = truck_build:year::NUMBER,
    make = truck_build:make::VARCHAR,
    model = truck_build:model::VARCHAR;
```

### Step 3 - Cleaning the Data

Let's run a query to see the distribution of truck makes.

```sql
SELECT 
    make,
    COUNT(*) AS count
FROM raw_pos.truck_dev
GROUP BY make
ORDER BY make ASC;
```

We can see a data quality issue: 'Ford' and 'Ford\_' are being treated as separate manufacturers. Let's fix this with an `UPDATE` statement.

```sql
UPDATE raw_pos.truck_dev
    SET make = 'Ford'
    WHERE make = 'Ford_';
```

### Step 4 - Promoting to Production with SWAP

Our development table is now cleaned and correctly formatted. We can instantly promote it to be the new production table using the `SWAP WITH` command. This atomically swaps the two tables.

```sql
ALTER TABLE raw_pos.truck_details SWAP WITH raw_pos.truck_dev;
```

### Step 5 - Final Cleanup

Now that the swap is complete, we can drop the unnecessary `truck_build` column from our new production table. We also need to drop the old production table, which is now named `truck_dev`. But for the sake of the next lesson, we will "accidentally" drop the main table.

```sql
ALTER TABLE raw_pos.truck_details DROP COLUMN truck_build;

-- Accidentally drop the production table!
DROP TABLE raw_pos.truck_details;
```

### Step 6 - Click Next --\>

## Data Recovery with UNDROP

Duration: 2

### Overview

Oh no\! We accidentally dropped the production `truck_details` table. Luckily, Snowflake's Time Travel feature allows us to recover it instantly. The `UNDROP` command restores dropped objects.

### Step 1 - Verify the Drop

If you run a `DESCRIBE` command on the table, you will get an error stating it does not exist.

```sql
DESCRIBE TABLE raw_pos.truck_details;
```

### Step 2 - Restore the Table with UNDROP

Let's restore the `truck_details` table to the exact state it was in before being dropped.

```sql
UNDROP TABLE raw_pos.truck_details;
```

> **[Time Travel & UNDROP](https://docs.snowflake.com/en/user-guide/data-time-travel)**: Snowflake Time Travel enables accessing historical data at any point within a defined period. This allows for restoring data that has been modified or deleted. `UNDROP` is a feature of Time Travel that makes recovery from accidental drops trivial.

### Step 3 - Verify Restoration and Clean Up

Verify the table was successfully restored by selecting from it. Then, we can safely drop the actual development table, `truck_dev`.

```sql
-- Verify the table was restored
SELECT * from raw_pos.truck_details;

-- Now drop the real truck_dev table
DROP TABLE raw_pos.truck_dev;
```

### Step 4 - Click Next --\>

## Monitoring Cost with Resource Monitors

Duration: 2

### Overview

Monitoring compute usage is critical. Snowflake provides Resource Monitors to track warehouse credit usage. You can define credit quotas and trigger actions (like notifications or suspension) when thresholds are reached.

### Step 1 - Creating a Resource Monitor

Let's create a resource monitor for `my_wh`. This monitor has a monthly quota of 100 credits and will send notifications at 75% and suspend the warehouse at 90% and 100% of the quota. First, ensure your role is `accountadmin`.

```sql
USE ROLE accountadmin;

CREATE OR REPLACE RESOURCE MONITOR my_resource_monitor
    WITH CREDIT_QUOTA = 100
    FREQUENCY = MONTHLY
    START_TIMESTAMP = IMMEDIATELY
    TRIGGERS ON 75 PERCENT DO NOTIFY
             ON 90 PERCENT DO SUSPEND
             ON 100 PERCENT DO SUSPEND_IMMEDIATE;
```

<!-- \<img src="assets/create\_rm.png"/\> -->

### Step 2 - Applying the Resource Monitor

With the monitor created, apply it to `my_wh`.

```sql
ALTER WAREHOUSE my_wh 
    SET RESOURCE_MONITOR = my_resource_monitor;
```

> For more information on what each configuration handles, please visit the documentation for [Working with Resource Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors).

### Step 3 - Click Next --\>

## Monitoring Cost with Budgets

Duration: 2

### Overview

While Resource Monitors track warehouse usage, Budgets provide a more flexible approach to managing all Snowflake costs. Budgets can track spend on any Snowflake object and notify users when a dollar amount threshold is reached.

### Step 1 - Creating a Budget via SQL

Let's first create the budget object.

```sql
CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET my_budget()
    COMMENT = 'My Tasty Bytes Budget';
```

### Step 2 - Configuring the Budget in Snowsight

Configuring a budget is done through the Snowsight UI.

1.  Make sure your role is set to `ACCOUNTADMIN`.
2.  Navigate to **Admin** » **Cost Management** » **Budgets**.
3.  Click on the **MY\_BUDGET** budget we created.
4.  Click **Edit** in the Budget Details panel on the right.
5.  Set the **Spending Limit** to `100`.
6.  Enter a verified notification email address.
7.  Click **+ Tags & Resources** and add the **TB\_101.ANALYTICS** schema and the **TB\_DE\_WH** warehouse to be monitored.
8.  Click **Save Changes**.

<!-- \<img src="assets/budgets\_ui.png"/\> -->

> For a detailed guide on Budgets, please see the [Snowflake Budgets Documentation](https://docs.snowflake.com/en/user-guide/budgets).

### Step 3 - Click Next --\>

## Exploring with Universal Search

Duration: 1

### Overview

Universal Search allows you to easily find any object in your account, plus explore data products in the Marketplace, relevant Snowflake Documentation, and Community Knowledge Base articles.

### Step 1 - Searching for an Object

Let's try it now.

1.  Click **Search** in the Navigation Menu on the left.
2.  Enter `truck` into the search bar.
3.  Observe the results. You will see categories of objects on your account, such as tables and views, as well as relevant documentation.

### Step 2 - Using Natural Language Search

You can also use natural language. For example, search for: `Which truck franchise has the most loyal customer base?`
Universal search will return relevant tables and views, even highlighting columns that might help answer your question, providing an excellent starting point for analysis.

<!-- \<img src="assets/universal\_search.png"/\> -->

### Step 3 - Click Next --\>

## Conclusion and Next Steps

Duration: 1

### Conclusion

Fantastic work\! You have successfully completed the Tasty Bytes - Getting Started with Snowflake Quickstart.

By doing so you have now learned how to:

  - Create, Configure, and Scale a Snowflake Warehouse
  - Use the Query Result Cache
  - Leverage Zero-Copy Cloning and `SWAP WITH` for development
  - Clean and Transform Data
  - Recover data instantly with `UNDROP`
  - Create and Apply a Resource Monitor and a Budget
  - Use Universal Search

If you would like to re-run this Quickstart, please run the `RESET` scripts located at the bottom of your worksheet.

### Next Steps

To continue your journey in the Snowflake AI Data Cloud, please now visit the link below to see all other Powered by Tasty Bytes - Quickstarts available to you.

  - ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3)

<!-- end list -->

```
```