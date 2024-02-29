summary: This is a broad introduction of Snowflake and covers how to login, run queries, and load data.
id: getting_started_with_snowflake
categories: featured,getting-started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering

# Getting Started with Snowflake - Zero to Snowflake
<!-- ------------------------ -->

## Overview

Duration: 2

Welcome to Snowflake! This entry-level guide designed for database and data warehouse administrators and architects will help you navigate the Snowflake interface and introduce you to some of our core capabilities. [Sign up for a free 30-day trial of Snowflake](https://trial.snowflake.com) and follow along with this lab exercise. Once we cover the basics, you'll be ready to start processing your own data and diving into Snowflake's more advanced features like a pro.

### Free Virtual Hands-on Lab

This Snowflake Guide is available as a free, instructor-led Virtual Hands on Lab. [Sign up for the VHOL today](https://www.snowflake.com/virtual-hands-on-lab/).

### Prerequisites:

- Use of the [Snowflake free 30-day trial environment](https://trial.snowflake.com)
- Basic knowledge of SQL, database concepts, and objects
- Familiarity with CSV comma-delimited files and JSON semi-structured data

### What You'll Learn:

- How to create stages, databases, tables, views, and virtual warehouses.
- How to load structured and semi-structured data.
- How to consume Cybersyn data from the Snowflake Data Marketplace.
- How to perform analytical queries on data in Snowflake, including joins between tables.
- How to clone objects.
- How to undo user errors using Time Travel.
- How to create roles and users, and grant them privileges.
- How to securely and easily share data with other accounts.

### Data You'll Use:
<!-- Meghan to provide Cybersyn data overview -->

<!-- ------------------------ -->

## Prepare Your Lab Environment

Duration: 2

If you haven't already, register for a [Snowflake free 30-day trial](https://signup.snowflake.com/developers). The rest of the sections in this lab assume you are using a new Snowflake account created by registering for a trial.

The Snowflake edition (Standard, Enterprise, Business Critical, etc.), cloud provider (AWS, Azure, GCP), and Region (US East, EU, etc.) you use for this lab, do not matter. However, we suggest you select the region that is physically closest to you and Enterprise, our most popular offering, as your Snowflake edition.

After registering, you will receive an email with an activation link and URL for accessing your Snowflake account.

### Logging into the Snowflake User Interface (UI)

Open a browser window and enter the URL of your Snowflake 30-day trial environment that was sent with your registration email.

You should see the following login dialog​. Enter the username and password that you specified during the registration:

![login screen](assets/3UIStory_1.png)

<!-- ------------------------ -->

## The Snowflake ​User Interface

Duration: 8

> aside negative
> 
>  **About the screenshots, sample code, and environment**
Screenshots in this lab depict examples; results may vary slightly from what you see when you complete the exercises.

### Navigating the Snowflake UI

Let's get you acquainted with Snowflake! This section covers the basic components of the user interface. We will move from top to bottom on the left-hand side margin.

![snowflake navbar](assets/3UIStory_2.png)

#### Worksheets

![worksheets tab main](assets/3UIStory_3.png)

The ​**Worksheets​** tab provides an interface for submitting SQL queries, performing DDL and DML operations, and viewing results as your queries or operations complete. A new worksheet is created by clicking **+ Worksheet** on the top right.

![worksheets tab details](assets/3UIStory_4.png)

The top left corner contains the following:

- **Home** icon: Use this to get back to the main console/close the worksheet.
- **Worksheet_name** drop-down: The default name is the timestamp when the worksheet was created. Click the timestamp to edit the worksheet name. The drop-down also displays additional actions you can perform for the worksheet.
- **Manage filters** button: Custom filters are special keywords that resolve as a subquery or list of values.

The top right corner contains the following:

- **Context** box: This lets Snowflake know which role and warehouse to use during this session. It can be changed via the UI or SQL commands.
- **Share** button: Open the sharing menu to share to other users or copy the link to the worksheet.
- **Play/Run** button: Run the SQL statement where the cursor currently is or multiple selected statements.

The middle pane contains the following:

- Drop-down at the top for setting the database/schema/object context for the worksheet.
- General working area where you enter and execute queries and other SQL statements. 

The middle-left panel contains the following:
- **Worksheets** tab: Use this tab to quickly select and jump between different worksheets
- **Databases** tab: Use this tab to view all of the database objects available to the current role
- **Search** bar: database objects browser which enables you to explore all databases, schemas, tables, and views accessible by the role currently in use for the worksheet. 

The bottom pane displays the results of queries and other operations. Also includes 4 options (**Object**, **Query**, **Result**, **Chart**) that open/close their respective panels on the UI. **Chart** opens a visualization panel for the returned results. More on this later.

The various panes on this page can be resized by adjusting their sliders. If you need more room in the worksheet, collapse the database objects browser in the left panel. Many of the screenshots in this guide keep this panel closed.

> aside negative
> 
>  **Worksheets vs the UI**
Most of the exercises in this lab are executed using pre-written SQL within this worksheet to save time. These tasks can also be done via the UI, but would require navigating back-and-forth between multiple UI tabs.

#### Dashboards

![dashboards tab](assets/3UIStory_5.png)

The **Dashboards** tab allows you to create flexible displays of one or more charts (in the form of tiles, which can be rearranged). Tiles and widgets are produced by executing SQL queries that return results in a worksheet. Dashboards work at a variety of sizes with minimal configuration.

#### Databases

![databases tab](assets/3UIStory_6.png)

Under **Data**, the **Databases**​ tab shows information about the databases you have created or have permission to access. You can create, clone, drop, or transfer ownership of databases, as well as load data in the UI. Notice that a database already exists in your environment. However, we will not be using it in this lab.

#### Private Shared Data

![shared data tab](assets/3UIStory_7.png)

Also under **Data**, the **Private Shared Data** tab is where data sharing can be configured to easily and securely share Snowflake tables among separate Snowflake accounts or external users, without having to create a copy of the data. We will cover data sharing in Section 10.

#### Marketplace

![marketplace tab](assets/3UIStory_8.png)
<!-- victoria ^ -->

The **Marketplace** tab is where any Snowflake customer can browse and consume data sets made available by providers. There are two types of shared data: Public and Personalized. Public data is free data sets available for querying instantaneously. Personalized data requires reaching out to the provider of data for approval of sharing data.
<!-- victoria - get content from Meghan -->

#### Query History

![history tab](assets/3UIStory_9.png)

Under **Activity** there are two tabs **Query History** and **Copy History**:

- **Query History** is where previous queries are shown, along with filters that can be used to hone results (user, warehouse, status, query tag, etc.). View the details of all queries executed in the last 14 days from your Snowflake account. Click a query ID to drill into it for more information.
- **Copy History** shows the status of copy commands run to ingest data into Snowflake.

#### Warehouses

![warehouses tab](assets/3UIStory_10.png)

Under **Admin**, the **​Warehouses​** tab is where you set up and manage compute resources known as virtual warehouses to load or query data in Snowflake. A warehouse called COMPUTE_WH already exists in your environment.

#### Resource Monitors

![resource monitors tab](assets/3UIStory_11.png)

Under **Admin**, the **Resource Monitors** tab shows all the resource monitors that have been created to control the number of credits that virtual warehouses consume. For each resource monitor, it shows the credit quota, type of monitoring, schedule, and actions performed when the virtual warehouse reaches its credit limit.

#### Roles

![roles tab](assets/3UIStory_12.png)

Under **Admin**, the **Roles** sub-tab of the **Users and Roles** tab shows a list of the roles and their hierarchies. Roles can be created, reorganized, and granted to users in this tab. The roles can also be displayed in tabular/list format by selecting the **Table** sub-tab.

#### Users

![users tab](assets/3UIStory_13.png)

Also under **Admin** tab, the **Users** sub-tab of the **Users and Roles** tab shows a list of users in the account, default roles, and owner of the users. For a new account, no records are shown because no additional roles have been created. Permissions granted through your current role determine the information shown for this tab. To see all the information available on the tab, switch your role to ACCOUNTADMIN.


![user preferences dropdown](assets/3UIStory_14.png)

Clicking on your username in the top right of the UI allows you to change your password, roles, and preferences. Snowflake has several system defined roles. You are currently in the default role of `SYSADMIN` and will stay in this role for the majority of the lab.

> aside negative
> 
>  **SYSADMIN**
The `SYSADMIN` (aka System Administrator) role has privileges to create warehouses, databases, and other objects in an account.
In a real-world environment, you would use different roles for the tasks in this lab, and assign roles to your users. We will cover more on roles and Snowflake's access control model in Section 9 and you can find additional information in the [Snowflake documentation](https://docs.snowflake.net/manuals/user-guide/security-access-control.html).

<!-- ------------------------ -->

## Data Lab: Preparing Data

Duration: 14
<!-- dash to advise on changed durations from rework? (throughout entire document) -->

### The Lab Story
You are a university researcher that wants to study stock performance of major consumer goods (CPG) companies in the US. This lab combines Nasdaq's daily stock price data with SEC company filings to understand how stocks react to certain reports.

We will start by collecting data from three different sources:
1. Load company metadata `.csv` file.
2. Load SEC filings, which are in a semi-structured JSON format.
3. Use the Snowflake Marketplace to find free stock price data from Cybersyn.

### Loading Data into Snowflake
Let's start by preparing to load structured `.csv` data into Snowflake.

The data we are using is company metadata provided by Cybersyn. The data has been exported and pre-staged for you in an Amazon AWS S3 bucket in the US-EAST region. The data details the consumer goods companies we are evaluating 
<!-- trip times, locations, user type, gender, age, etc. On AWS S3, the data represents 61.5M rows, 377 objects, and 1.9GB compressed. victoria --> 
. _(The full dataset is available for free [here](https://app.snowflake.com/marketplace/listing/GZTSZAS2KF7).)_

> aside negative
> 
>  **Getting Data into Snowflake**
There are many ways to get data into Snowflake from many locations including the COPY command, Snowpipe auto-ingestion, external connectors, or third-party ETL/ELT solutions. For more information on getting data into Snowflake, see the [Snowflake documentation](https://docs.snowflake.net/manuals/user-guide-data-load.html).
For the purposes of this lab, we use the COPY command and AWS S3 storage to load data manually. In a real-world scenario, you would more likely use an automated process or ETL solution.

Below is a snippet from consumer goods CSV data files:
<!-- victoria -->

It is in comma-delimited format with a single header line and double quotes enclosing all string values, including the field headings in the header line. This will come into play later in this section as we configure the Snowflake table to store this data.

#### Create a Database and Table

Ensure you are using the sysadmin role by selecting your name at the top left, **Switch Role** > **SYSADMIN**.

Navigate to the **Databases** tab. Click **Create**, name the database `COMPANY_DATA`, then click **CREATE**.

<!-- ------------------------ -->

## Loading Data

Duration: 10

In this section, we will use a virtual warehouse and the COPY command to initiate bulk loading of structured data into the Snowflake table we created in the last section.

### Resize and Use a Warehouse for Data Loading

Compute resources are needed for loading data. Snowflake's compute nodes are called virtual warehouses and they can be dynamically sized up or out according to workload, whether you are loading data, running a query, or performing a DML operation. Each workload can have its own warehouse so there is no resource contention.

Navigate to the **Warehouses** tab (under **Admin**). This is where you can view all of your existing warehouses, as well as analyze their usage trends.

Note the **+ Warehouse** option in the upper right corner of the top. This is where you can quickly add a new warehouse. However, we want to use the existing warehouse COMPUTE_WH included in the 30-day trial environment.

Click the row of the `COMPUTE_WH` warehouse. Then click the **...** (dot dot dot) in the upper right corner text above it to see the actions you can perform on the warehouse. We will use this warehouse to load the data from AWS S3.

![compute warehouse configure](assets/5Load_1.png)

Click **Edit** to walk through the options of this warehouse and learn some of Snowflake's unique functionality.

> aside positive
> 
>  If this account isn't using Snowflake Enterprise Edition (or higher), you will not see the **Mode** or **Clusters** options shown in the screenshot below. The multi-cluster warehouses feature is not used in this lab, but we will discuss it as a key capability of Snowflake.

![warehouse configure settings](assets/5Load_2.png)

- The **Size** drop-down is where the capacity of the warehouse is selected. For larger data loading operations or more compute-intensive queries, a larger warehouse is recommended. The sizes translate to the underlying compute resources provisioned from the cloud provider (AWS, Azure, or GCP) where your Snowflake account is hosted. It also determines the number of credits consumed by the warehouse for each full hour it runs. The larger the size, the more compute resources from the cloud provider are allocated to the warehouse and the more credits it consumes. For example, the `4X-Large` setting consumes 128 credits for each full hour. This sizing can be changed up or down at any time with a simple click.

- If you are using Snowflake Enterprise Edition (or higher) the **Query Acceleration** option is available. When it is enabled for a warehouse, it can improve overall warehouse performance by reducing the impact of outlier queries, which are queries that use more resources than the typical query. Leave this disabled 

- If you are using Snowflake Enterprise Edition (or higher) and the **Multi-cluster Warehouse** option is enabled, you will see additional options. This is where you can set up a warehouse to use multiple clusters of compute resources, up to 10 clusters. For example, if a `4X-Large` multi-cluster warehouse is assigned a maximum cluster size of 10, it can scale out to 10 times the compute resources powering that warehouse...and it can do this in seconds! However, note that this will increase the number of credits consumed by the warehouse to 1280 if all 10 clusters run for a full hour (128 credits/hour x 10 clusters). Multi-cluster is ideal for concurrency scenarios, such as many business analysts simultaneously running different queries using the same warehouse. In this use case, the various queries are allocated across multiple clusters to ensure they run quickly.

- Under **Advanced Warehouse Options**, the options allow you to automatically suspend the warehouse when not in use so no credits are needlessly consumed. There is also an option to automatically resume a suspended warehouse so when a new workload is sent to it, it automatically starts back up. This functionality enables Snowflake's efficient "pay only for what you use" billing model which allows you to scale your resources when necessary and automatically scale down or turn off when not needed, nearly eliminating idle resources. Additionally, there is an option to change the Warehouse type from Standard to Snowpark-optimized. Snowpark-optmized warehouses provide 16x memory per node and are recommended for workloads that have large memory requirements such as ML training use cases using a stored procedure on a single virtual warehouse node. Leave this type as Standard

> aside negative
> 
>  **Snowflake Compute vs Other Data Warehouses**
Many of the virtual warehouse and compute capabilities we just covered, such as the ability to create, scale up, scale out, and auto-suspend/resume virtual warehouses are easy to use in Snowflake and can be done in seconds. For on-premise data warehouses, these capabilities are much more difficult, if not impossible, as they require significant physical hardware, over-provisioning of hardware for workload spikes, and significant configuration work, as well as additional challenges. Even other cloud-based data warehouses cannot scale up and out like Snowflake without significantly more configuration work and time.

**Warning - Watch Your Spend!**
During or after this lab, you should be careful about performing the following actions without good reason or you may burn through your $400 of free credits more quickly than desired:

- Do not disable auto-suspend. If auto-suspend is disabled, your warehouses continues to run and consume credits even when not in use.
- Do not use a warehouse size that is excessive given the workload. The larger the warehouse, the more credits are consumed.

We are going to use this virtual warehouse to load the structured data in the CSV files (stored in the AWS S3 bucket) into Snowflake. However, we are first going to change the size of the warehouse to increase the compute resources it uses. After the load, note the time taken and then, in a later step in this section, we will re-do the same load operation with an even larger warehouse, observing its faster load time.

Change the **Size** of this data warehouse from `X-Small` to `Small`. then click the **Save Warehouse** button:

![configure settings small](assets/5Load_3.png)

### Load the Data
Now we can run a COPY command to load the data into the `COMPANY` table we created earlier.

Navigate back to the `ZERO_TO_SNOWFLAKE` worksheet in the **Worksheets** tab. Make sure the worksheet context is correctly set:

Role: `SYSADMIN`
Warehouse: `COMPUTE_WH`
Database: `COMPANY_DATA`
Schema = `CYBERSYN`

![worksheet context](assets/5Load_4.png)

Execute the following statements in the worksheet to load the staged data into the table. This may take up to 30 seconds.

```SQL
copy into company_metadata from @cybersyn_company_metadata file_format=csv PATTERN = '.*csv.*' ;
```

In the result pane, you should see the status of each file that was loaded. Once the load is done, in the **Query Details** pane on the bottom right, you can scroll through the various statuses, error statistics, and visualizations for the last statement executed:

![results load status](assets/5Load_5.png)

Next, navigate to the **Query History** tab by clicking the **Home** icon and then **Activity** > **Query History**. Select the query at the top of the list, which should be the COPY INTO statement that was last executed. Select the **Query Profile** tab and note the steps taken by the query to execute, query details, most expensive nodes, and additional statistics.

![history and duration](assets/5Load_6.png)

Now let's reload the `COMPANY_DATA` table with a larger warehouse to see the impact the additional compute resources have on the loading time.

Go back to the worksheet and use the TRUNCATE TABLE command to clear the table of all data and metadata:

```SQL
truncate table company_metadata;
```

Verify that the table is empty by running the following command:

```SQL
--verify table is clear
select * from company_metadata limit 10;
```

The result should show "Query produced no results".

Change the warehouse size to `large` using the following ALTER WAREHOUSE:
 
```SQL
--change warehouse size from small to large (4x)
alter warehouse compute_wh set warehouse_size='large';
```

Verify the change using the following SHOW WAREHOUSES:

```SQL
--load data with large warehouse
show warehouses;
```

![resize context to large in UI step 1](assets/5Load_7.png)


The size can also be changed using the UI by clicking on the worksheet context box, then the **Configure** (3-line) icon on the right side of the context box, and changing `Small` to `Large` in the **Size** drop-down:

![resize context to large in UI step 1](assets/5Load_8.png)
![resize context to large in UI step 2](assets/5Load_8b.png)

Execute the same COPY INTO statement as before to load the same data again:

```SQL
copy into company_metadata from @cybersyn_company_metadata
file_format=CSV;
```

![compare load durations](assets/5Load_9.png)

Once the load is done, navigate back to the **Queries** page (**Home** icon > **Activity** > **Query History**). Compare the times of the two COPY INTO commands. The load using the `Large` warehouse was significantly faster.

### Create a New Warehouse for Data Analytics

Going back to the lab story, let's assume the research team wants to eliminate resource contention between their data loading/ETL workloads and the analytical end users using BI tools to query Snowflake. As mentioned earlier, Snowflake can easily do this by assigning different, appropriately-sized warehouses to various workloads. Since our internal team already has a warehouse for data loading, let's create a new warehouse for the end users of our research to run analytics. We will use this warehouse to perform analytics in the next section.

Navigate to the **Admin** > **Warehouses** tab, click **+ Warehouse**, and name the new warehouse `` and set the size to `Large`.

If you are using Snowflake Enterprise Edition (or higher) and **Multi-cluster Warehouses** is enabled, you will see additional settings:

- Make sure **Max Clusters** is set to `1`.
- Leave all the other settings at their defaults.

![warehouse settings](assets/5Load_10.png)

Click the **Create Warehouse** button to create the warehouse.


































<!-- ------------------------ -->

## Accessing Cybersyn Data from Snowflake Marketplace

Duration: 5

### Snowflake Data Marketplace

Make sure you're using the ACCOUNTADMIN role and, navigate to the **Marketplace**:

![data marketplace tab](assets/10Share_7.png)
<!-- dash to update -->

#### Find a listing

The search box at the top allows you to search for a listing based on the type of data that you are looking for. The drop-down lists to the right of the search box let you filter data listings by Provider, Business Needs, and Category.

Type `stock prices` in the search box, scroll through the results, and select **Financial & Economic Essentials** provided by Cybersyn.

![health tab](assets/10Share_8.png)
<!-- dash to update -->

In the **Financial & Economic Essentials** page, you can learn more about the dataset and see some sample queries. Click the **Get** button to make this information available within your Snowflake account:

![get data fields](assets/10Share_starschema_get_data.png)
<!-- dash to update -->

Review the information in the dialog and click **Get** again:

![get data fields](assets/10Share_starschema_get_data2.png)
<!-- dash to update -->

You can now click **Done** or choose to run the sample queries provided by Cybersyn:

![get data fields](assets/10Share_starschema_query_data.png)
<!-- dash to update -->

If you chose **Open**, a new worksheet opens in a new browser tab/window:

1. Set your context 
2. Select the query you want to run (or place your cursor in the query text).
3. Click the **Run/Play** button (or use the keyboard shortcut).
4. You can view the data results in the bottom pane.
5. When you are done running the sample queries, click the **Home** icon in the upper left corner.

![get data fields](assets/10Share_starschema_query_data2.png)
<!-- dash to update -->

Next:
1. Click **Data** > **Databases**
2. Click the `FINANCIAL__ECONOMIC_ESSENTIALS` database.
3. You can see details about the `CYBERSYN` schema, tables, and views that are available to query.

![covid19 databases](assets/10Share_starschema_db_info.png)
<!-- dash to update -->

That's it! You have now successfully subscribed to the Financial & Economics Essentials data from Cybersyn, which offers many different datasets. **Stock price** and **foreign exchange rate** data is updated daily. Notice we didn't have to create databases, tables, views, or an ETL process. We simply searched for and accessed shared data from Cybersyn in the Snowflake Data Marketplace.

_To learn more about how to use the new worksheet interface, go to the [Snowsight Docs](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#using-snowsight)._

<!-- ------------------------ -->

## Queries, the Results Cache, & Cloning

Duration: 8

In the previous exercises, we loaded data into two tables using Snowflake's COPY bulk loader command and the `COMPUTE_WH` virtual warehouse. We also grabbed additional data from Cybersyn on the Snowflake Marketplace. Now, we are going to take on the role of the university researchers to query data in those tables using the worksheet and second warehouse `ANALYTICS_WH`.

> aside negative
> 
>  **Real World Roles and Querying**
Within a real company or research team, analytics users would likely have a different role than SYSADMIN. To keep the lab simple, we are going to stay with the SYSADMIN role for this section.
Additionally, querying would typically be done with a business intelligence product like Tableau, Looker, PowerBI, etc. For more advanced analytics, data science tools like Datarobot, Dataiku, AWS Sagemaker or many others can query Snowflake. Any technology that leverages JDBC/ODBC, Spark, Python, or any of the other supported programmatic interfaces can run analytics on the data in Snowflake. To keep this lab simple, all queries are being executed via the Snowflake worksheet.

### Execute Some Queries

Go to the **ZERO_TO_SNOWFLAKE** worksheet and change the warehouse to use the new warehouse you created in the last section. Your worksheet context should be the following:

Role: `SYSADMIN`
Warehouse: `ANALYTICS_WH (L)`
Database: `COMPANY_DATA`
Schema = `CYBERSYN`

Run the following query to see a sample of the `company_metadata`:

```SQL
select * from company_metadata limit 20;
```

![sample data query results](assets/6Query_1.png)
<!-- dash to update -->

Now, let's look at some basic daily statistics on stock price data. Run the query below in the worksheet. For each day, it shows the day-over-day stock price change, volume of Nasdaq trading, and post-close price.

```SQL

```

![sample data query results](assets/6Query_2.png)
<!-- dash to update -->

### Use the Result Cache

Snowflake has a result cache that holds the results of every query executed in the past 24 hours. These are available across warehouses, so query results returned to one user are available to any other user on the system who executes the same query, provided the underlying data has not changed. Not only do these repeated queries return extremely fast, but they also use no compute credits.

Let's see the result cache in action by running the exact same query again.

```SQL

```

In the **Query Details** pane on the right, note that the second query runs significantly faster because the results have been cached.

![cached query duration](assets/6Query_4.png)
<!-- dash to update -->

### Execute Another Query

Next, let's run the following query to see which stocks are the most volatile:

```SQL

```

![months query results](assets/6Query_5.png)
<!-- dash to update -->

### Clone a Table

Snowflake allows you to create clones, also known as "zero-copy clones" of tables, schemas, and databases in seconds. When a clone is created, Snowflake takes a snapshot of data present in the source object and makes it available to the cloned object. The cloned object is writable and independent of the clone source. Therefore, changes made to either the source object or the clone object are not included in the other.

A popular use case for zero-copy cloning is to clone a production environment for use by Development & Testing teams to test and experiment without adversely impacting the production environment and eliminating the need to set up and manage two separate environments.

> aside negative
> 
>  **Zero-Copy Cloning**
A massive benefit of zero-copy cloning is that the underlying data is not copied. Only the metadata and pointers to the underlying data change. Hence, clones are “zero-copy" and storage requirements are not doubled when the data is cloned. Most data warehouses cannot do this, but for Snowflake it is easy!

Run the following command in the worksheet to create a development (dev) table clone of the `company_metadata` table:

```SQL
create table company_metadata_dev clone company_metadata;
```

Click the three dots (**...**) in the left pane and select **Refresh**. Expand the object tree under the `COMPANY_DATA` database and verify that you see a new table named `company_metadata_dev`. Your Development team now can do whatever they want with this table, including updating or deleting it, without impacting the `company_metadata` table or any other object.

![trips_dev table](assets/6Query_6.png)
<!-- dash to update -->

<!-- ------------------------ -->

## Semi-Structured Data, Views, & Joins

Duration: 16













<!-- ------------------------ -->

## Using Time Travel

Duration: 6

Snowflake's powerful Time Travel feature enables accessing historical data, as well as the objects storing the data, at any point within a period of time. The default window is 24 hours and, if you are using Snowflake Enterprise Edition, can be increased up to 90 days. Most data warehouses cannot offer this functionality, but - you guessed it - Snowflake makes it easy!

Some useful applications include:
- Restoring data-related objects such as tables, schemas, and databases that may have been deleted.
- Duplicating and backing up data from key points in the past.
- Analyzing data usage and manipulation over specified periods of time.

### Drop and Undrop a Table

First let's see how we can restore data objects that have been accidentally or intentionally deleted.

In the `ZERO_TO_SNOWFLAKE` worksheet, run the following DROP command to remove the `COMPANY_METADATA` table:
```SQL
drop table company_metadata;
```

Run a query on the table:
```SQL
select * from company_metadata limit 10;
```

In the results pane at the bottom, you should see an error because the underlying table has been dropped:
![table dropped error](assets/8Time_1.png)
<!-- dash to update -->

Now, restore the table:
```SQL
undrop table company_metadata;
```

The `company_metadata` table should be restored. Verify by running the following query:
```SQL 
select * from company_metadata limit 10;
```
![restored table result](assets/8Time_2.png)
<!-- dash to update -->

### Roll Back a Table

Let's roll back the `COMPANY_METADATA` table in the `COMPANY_DATA` database to a previous state to fix an unintentional DML error that replaces all the station names in the table with the word "oops".

First, run the following SQL statements to switch your worksheet to the proper context:

```SQL
use role sysadmin;

use warehouse compute_wh;

use database company_data;

use schema cybersyn;
```

Run the following command to replace all of the station names in the table with the word "oops":

```SQL
update company_metadata set ticker = 'OOPS';
```

Now, run a query that returns the unique tickers in the dataset. Notice that each row now has the same ticker `'OOPS'`:

```SQL
select *
from company_metadata
order by ticker;
```

![one row result](assets/8Time_3.png)
<!-- dash to update -->

Normally we would need to scramble and hope we have a backup lying around.

In Snowflake, we can simply run a command to find the query ID of the last UPDATE command and store it in a variable named `$QUERY_ID`.

```SQL
set query_id =
(select query_id from table(information_schema.query_history_by_session (result_limit=>5))
where query_text like 'update%' order by start_time desc limit 1);
```

Use **Time Travel** to recreate the table with the correct station names:

```SQL
create or replace table company_metadata as
(select * from company_metadata before (statement => $query_id));
```

Run the previous query again to verify that the tickers have been restored:

```SQL
select *
from company_metadata
order by ticker;
```

![restored names result](assets/8Time_4.png)
<!-- dash to update -->

<!-- ------------------------ -->

## Working with Roles, Account Admin, & Account Usage

Duration: 8

In this section, we will explore aspects of Snowflake's access control security model, such as creating a role and granting it specific permissions. We will also explore other usage of the `ACCOUNTADMIN` (Account Administrator) role, which was briefly introduced earlier in the lab.

Continuing with the lab story, let's assume a junior DBA has joined our research team, and we want to create a new role for them with less privileges than the system-defined, default role of `SYSADMIN`.

> aside negative
> 
>  **Role-Based Access Control**
Snowflake offers very powerful and granular access control that dictates the objects and functionality a user can access, as well as the level of access they have. For more details, check out the [Snowflake documentation](https://docs.snowflake.net/manuals/user-guide/security-access-control.html).

### Create a New Role and Add a User

In the `ZERO_TO_SNOWFLAKE` worksheet, switch to the `ACCOUNTADMIN` role to create a new role. `ACCOUNTADMIN` encapsulates the `SYSADMIN` and `SECURITYADMIN` system-defined roles. It is the top-level role in the account and should be granted only to a limited number of users.

In the `ZERO_TO_SNOWFLAKE` worksheet, run the following command:

```SQL
use role accountadmin;
```

Notice that, in the top right of the worksheet, the context has changed to `ACCOUNTADMIN`:

![ACCOUNTADMIN context](assets/9Role_1.png)

Before a role can be used for access control, at least one user must be assigned to it. So let's create a new role named `JUNIOR_DBA` and assign it to your Snowflake user. To complete this task, you need to know your username, which is the name you used to log in to the UI.

Use the following commands to create the role and assign it to you. Before you run the `GRANT ROLE` command, replace `YOUR_USERNAME_GOES_HERE` with your username:

```SQL
create role junior_dba;

grant role junior_dba to user YOUR_USERNAME_GOES_HERE;
```

> aside positive
> 
>  If you try to perform this operation while in a role such as `SYSADMIN`, it would fail due to insufficient privileges. By default (and design), the `SYSADMIN` role cannot create new roles or users.

Change your worksheet context to the new `JUNIOR_DBA` role:

```SQL
use role junior_dba;
```

In the top right of the worksheet, notice that the context has changed to reflect the `JUNIOR_DBA` role. 

![JUNIOR_DBA context](assets/9Role_2.png)

Also, the warehouse is not selected because the newly created role does not have usage privileges on any warehouse. Let's fix it by switching back to `ACCOUNTADMIN` role and grant usage privileges to `COMPUTE_WH` warehouse.

```SQL
use role accountadmin;

grant usage on warehouse compute_wh to role junior_dba;
```

Switch back to the `JUNIOR_DBA` role. You should be able to use `COMPUTE_WH` now.

```SQL
use role junior_dba;

use warehouse compute_wh;
```

Finally, you can notice that in the database object browser panel on the left, the `COMPANY_DATA` and `FINANCIAL__ECONOMIC_ESSENTIALS` databases no longer appear. This is because the `JUNIOR_DBA` role does not have privileges to access them.

Switch back to the `ACCOUNTADMIN` role and grant the `JUNIOR_DBA` the USAGE privilege required to view and use the `COMPANY_DATA` and `FINANCIAL__ECONOMIC_ESSENTIALS` databases:

```SQL
use role accountadmin;

grant usage on database COMPANY_DATA to role junior_dba;

grant usage on database FINANCIAL__ECONOMIC_ESSENTIALS to role junior_dba;
```

Switch to the `JUNIOR_DBA` role:

```SQL
use role junior_dba;
```

Notice that the `COMPANY_DATA` and `FINANCIAL__ECONOMIC_ESSENTIALS` databases now appear in the database object browser panel on the left. If they don't appear, try clicking **...** in the panel, then clicking **Refresh**.

![object browser panel with databases](assets/9Role_3.png)

### View the Account Administrator UI

Let's change our access control role back to `ACCOUNTADMIN` to see other areas of the UI accessible only to this role. However, to perform this task, use the UI instead of the worksheet.

First, click the **Home** icon in the top left corner of the worksheet. Then, in the top left corner of the UI, click your name to display the user preferences menu. In the menu, go to **Switch Role** and select `ACCOUNTADMIN`.

![switch UI role](assets/9Role_4.png)

> aside negative
> 
>  **Roles in User Preference vs Worksheet**
Why did we use the user preference menu to change the role instead of the worksheet? The UI session and each worksheet have their own separate roles. The UI session role controls the elements you can see and access in the UI, whereas the worksheet role controls only the objects and actions you can access within the role.

Notice that once you switch the UI session to the `ACCOUNTADMIN` role, new tabs are available under **Admin**.


#### Usage

![account usage](assets/9Role_5.png)

The **Usage** tab shows the following, each with their own page:

- **Organization**: Credit usage across all the accounts in your organization.
- **Consumption**: Credits consumed by the virtual warehouses in the current account.
- **Storage**: Average amount of data stored in all databases, internal stages, and Snowflake Failsafe in the current account for the past month.
- **Transfers**: Average amount of data transferred out of the region (for the current account) into other regions for the past month.

The filters in the top right corner of each page can be used to break down the usage/consumption/etc. visualizations by different measures.

#### Security

![account usage](assets/9Role_6.png)

The **Security** tab contains network policies created for the Snowflake account. New network policies can be created by selecting “+ Network Policy” at the top right hand side of the page.

#### Billing

![account usage](assets/9Role_7.png)

The **Billing** tab contains the payment method for the account:

- If you are a Snowflake contract customer, the tab shows the name associated with your contract information.
- If you are an on-demand Snowflake customer, the tab shows the credit card used to pay month-to-month, if one has been entered. If no credit card is on file, you can add one to continue using Snowflake when your trial ends.

<!-- ------------------------ -->

## Sharing Data Securely on the Snowflake Marketplace

Duration: 6

Snowflake enables data access between accounts through the secure data sharing features. Shares are created by data providers and imported by data consumers, either through their own Snowflake account or a provisioned Snowflake Reader account. The consumer can be an external entity or a different internal business unit that is required to have its own unique Snowflake account.

> aside positive
> 
>  **Cybersyn**
<!-- Meghan content ^^ -->

With secure data sharing:

- There is only one copy of the data that lives in the data provider's account.
- Shared data is always live, real-time, and immediately available to consumers.
- Providers can establish revocable, fine-grained access to shares.
- Data sharing is simple and safe, especially compared to older data sharing methods, which were often manual and insecure, such as transferring large `.csv` files across the internet.

> aside positive
> 
>  **Cross-region & cross-cloud data sharing** To share data across regions or cloud platforms, you must set up replication. This is outside the scope of this lab, but more information is available in [this Snowflake article](https://www.snowflake.com/trending/what-is-data-replication).

Snowflake uses secure data sharing to provide account usage data and sample data sets to all Snowflake accounts. In this capacity, Snowflake acts as the data provider of the data and all other accounts.

Secure data sharing also powers the Snowflake Data Marketplace, which is available to all Snowflake customers and allows you to discover and access third-party datasets from numerous data providers and SaaS vendors. Again, in this data sharing model, the data doesn't leave the provider's account and you can use the datasets without any transformation.


### View Existing Shares

In the home page, navigate to **Data** > **Databases**. In the list of databases, look at the **SOURCE** column. You should see two databases with `Local` in the column. These are the two databases we created previously in the lab. The other database, `SNOWFLAKE`, shows `Share` in the column, indicating it's shared from a provider.

![arrow over database icon](assets/10Share_1.png)
<!-- dash to update -->

### Create an Outbound Share

Let's go back to the stock price data story and assume we are the Account Administrator for Snowflake at a university. We have a trusted partner who wants to analyze the data in our `COMPANY_DATA` database on a near real-time basis. This partner also has their own Snowflake account in the same region as our account. So let's use secure data sharing to allow them to access this information.

Navigate to **Data** > **Private Sharing**, then at the top of the tab click **Shared by My Account**. Click the **Share** button in the top right corner and select **Create a Direct Share**:

![shares outbound button](assets/10Share_2.png)
<!-- dash to update -->

Click **+ Select Data** and navigate to the `COMPANY_DATA` database and `CYBERSYN` schema. Select the 2 tables we created in the schema and click the **Done** button:

![share fields](assets/10Share_3.png)
<!-- dash to update -->

The default name of the share is a generic name with a random numeric value appended. Edit the default name to a more descriptive value that will help identify the share in the future (e.g. `ZERO_TO_SNOWFLAKE_SHARED_DATA`. You can also add a comment.

In a real-world scenario, the Account Administrator would next add one or more consumer accounts to the share, but we'll stop here for the purposes of this lab.

Click the **Create Share** button at the bottom of the dialog:

![success message](assets/10Share_4.png)
<!-- dash to update -->

The dialog closes and the page shows the secure share you created:

![TRIPS_SHARE share](assets/10Share_5.png)
<!-- dash to update -->

You can add consumers, add/change the description, and edit the objects in the share at any time. In the page, click the **<** button next to the share name to return to the **Share with Other Accounts** page:

![TRIPS_SHARE share](assets/10Share_6.png)
<!-- dash to update -->

We've demonstrated how it only takes seconds to give other accounts access to data in your Snowflake account in a secure manner with no copying or transferring of data required!

Snowflake provides several ways to securely share data without compromising confidentiality. In addition to tables, you can share secure views, secure UDFs (user-defined functions), and other secure objects. For more details about using these methods to share data while preventing access to sensitive information, see the [Snowflake documentation](https://docs.snowflake.com/en/user-guide/data-sharing-secure-views.html).

<!-- ------------------------ -->

## Resetting Your Snowflake Environment

Duration: 2

If you would like to reset your environment by deleting all the objects created as part of this lab, run the SQL statements in a worksheet.

First, ensure you are using the ACCOUNTADMIN role in the worksheet:

```SQL
use role accountadmin;
```

Then, run the following SQL commands to drop all the objects we created in the lab:

```SQL
drop share if exists zero_to_snowflake_shared_data;
-- If necessary, replace "zero_to_snowflake-shared_data" with the name you used for the share

drop database if exists company_data;

drop warehouse if exists analytics_wh;

drop role if exists junior_dba;
```

<!-- ------------------------ -->

## Conclusion & Next Steps

Duration: 2

Congratulations on completing this introductory lab exercise! You've mastered the Snowflake basics and are ready to apply these fundamentals to your own data. Be sure to reference this guide if you ever need a refresher.

We encourage you to continue with your free trial by loading your own sample or production data and by using some of the more advanced capabilities of Snowflake not covered in this lab.

### Additional Resources:

- Learn more about the [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#using-snowsight) docs.
- Read the [Definitive Guide to Maximizing Your Free Trial](https://www.snowflake.com/test-driving-snowflake-the-definitive-guide-to-maximizing-your-free-trial/) document.
- Attend a [Snowflake virtual or in-person event](https://www.snowflake.com/about/events/) to learn more about our capabilities and customers.
- Join the [Snowflake Community](https://community.snowflake.com/s/topic/0TO0Z000000wmFQWAY/getting-started-with-snowflake).
- Sign up for [Snowflake University](https://community.snowflake.com/s/article/Getting-Access-to-Snowflake-University).
- Contact our [Sales Team](https://www.snowflake.com/free-trial-contact-sales/) to learn more.
- [Cybersyn data on the Snowflake Marketplace](https://app.snowflake.com/marketplace/listings/Cybersyn%2C%20Inc)
- [Cybersyn Data Catalog](https://app.cybersyn.com/data_catalog/?utm_source=Snowflake+Quickstart&utm_medium=organic&utm_campaign=Snowflake+Quickstart)

### What we've covered:

- How to create stages, databases, tables, views, and virtual warehouses.
- How to load structured and semi-structured data.
- How to consume Cybersyn data from the Snowflake Data Marketplace.
- How to perform analytical queries on data in Snowflake, including joins between tables.
- How to clone objects.
- How to undo user errors using Time Travel.
- How to create roles and users, and grant them privileges.
- How to securely and easily share data with other accounts.