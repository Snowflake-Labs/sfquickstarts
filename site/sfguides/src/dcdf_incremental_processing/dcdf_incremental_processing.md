author: melindawebster
id: dcdf_incremental_processing
summary: Getting Started with DCDF Data Architecture Incremental Processing/Logical Partitions
categories: architecture-patterns
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Cloud Deployment Framework, DCDF, Data Engineering, Data Architecture 

# Getting Started with DCDF Data Architecture Incremental Processing & Logical Partitions
<!-- ------------------------ -->
## Overview 
Duration: 3

These topics of incremental processing and logical partitions was originally in Episode 2 of the Webinar series for the Data Cloud Deployment Framework (DCDF).  In [Webinar Episode 2](https://www.snowflake.com/webinar/for-customers/applying-architectural-patterns-to-solve-business-questions-2023-01-11/) we focused on the ELT implementation patterns to operationalize data loading, centralize the management of data transformations and restructure the data for optimal reporting and analysis.  The episode can be watched on demand as well.

In this quickstart, we will focus on the actual SQL code templates for ingesting, transforming, and restructuring data into the presentation layer using incremental processing and logical partition definitions.

>aside negative
>
> **Caveat:** This DCDF data architecture quickstart and template scripts are for illustrative purposes only.  These scripts can be run in a customer’s own account or free trial account to understand the concepts and patterns.   These scripts can then be customized into your own environment with your own business use cases.

### Prerequisites
- A Snowflake account.  Existing or a free [Trial Account](https://trial.snowflake.com/) can be used.
- Working knowledge with Snowflake database objects and the Snowflake Web UI/Snowsight.
- Familiarity with Snowflake and Snowflake objects.
- [SnowSQL installed](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html) and configured to your Snowflake account.
- Familiarity and understanding of SQL syntax

### What You Will Learn 
- DCDF Data Architecture
- Incremental processing and Logical Partitions

### What You Will Need 
- A Snowflake Account or [Trial Account](signup.snowflake.com), any edition will do as the scripts will run on any edition.
- Login to Snowflake account that has ACCOUNTADMIN role access (Note: Free Trial accounts provide this automatically)
- [SnowSQL installed](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html)
- Snowsight or Classic Ui will be used in these examples.  

>aside negative
> VS Code Snowflake Extension Note: If you are using VS Code Snowflake Extension to view the code and run it, the SHA1_BINARY fields will not display correctly.  

### What You Will Build 
- This lab will walk you through the process of deploying a sample ELT data pipeline utilizing the techniques for incremental processing using logical partitions andn the repeatable processing patterns.
- End to end sample templates for a data pipeline for a sample set of data.
- Data pipeline repeatable patterns for ingestion, transformation and consumable data assets.

<!-- ------------------------ -->
## DCDF Data Architecture Review
Duration: 3

Let's review the DCDF Data Architecture processing layers and the purpose of each layer.  This was discussed in detail in the [Data Cloud Deployment Framework Webinar Series Episode 1](https://www.snowflake.com/webinar/for-customers/data-cloud-deployment-framework-series/).  For more details this webinar can be watched on-demand.

![img](assets/dcdf_architecture_review.png)

### Raw Layer
This represents the first processing layer within Snowflake.  It facilitates data ingestion into Snowflake and will manage the data as it exists in the source system, with no applied transformations.
- A database per source.  
- Hash generation for surrogate keys can be derived here.
- No transformations are performed at this layer, other than maybe creating a surrogate key derivations

### Integration Layer
Integration is used to centralize all business rules applied to the data. Performs the data transformation processing, centralizing and materializing the application of business rules.  It is extremely important to note that this is the only layer where business rules are applied to the data.
- Centralized business rules
- Units of work in one place with reusable components
- Persist those intermediate results as tables.
- Purpose is to have one place where business rules or logic are applied and the intermediate results are persisted.

### Presentation Layer
Performs the re-organization of data from the raw and integration layers into various purpose-built solutions for reporting and analytics.  Scope can cover conforming dimensions, atomic fact aggregate fact tables, flat data sets for data science model building and views for governing exposure of data to end-users and applications.  Note that business rules should not be implemented within this processing layer.
- Purpose built solutions for consumption, analytics and sharing
- Recommend using permanent tables for incrementally updated tables.

### Common Database
Single database with one or more schemas to manage objects that span the breadth of the data architecture layers.  
- Used for reusable common objects such as UDFs, file formats, stages, common table data that are utilized across the DCDF layers.

### Workspace Databases
Can contain a database and related warehouse for each department/team within a business entity that requires the ability to persist intermediate results, non-production solution datasets and compute isolation to mitigate contention and facilitate cost tracking.
- A sandbox where individual teams can persist data for their own development and testing.
- Some teams such as Data Science teams might clone the data from the presentation layer into their workspace and run certain models on the data to determine insights.

<!-- ------------------------ -->
## Incremental Processing Concepts
Duration: 4
>aside positive
>
>"The best way to process big data, is to turn it into small data"

### Three steps for Incremental Processing
#### Step 1 - Define Logical Partitions
- Logical partitions are defined usually as logical periods of time, time series data such as day, week, month, etc based on a business event represented in the data.
- The volume of data being processed along with the typical periods impacted by the delta feed from the source system will drive the logical partition approach.
- In our quickstart we will use order date as our logical partition in the line item table.  This defines how to identify new or changed data.

#### Step 2 - Identify Impacted Partitions
- Next step is to identify the impacted logical partitions that are represented in the delta feed from the sources system. 
- As the delta data is ingested into our staging tables in the raw layer, the impacted logical partitions (orderdate) can be identified.  
 
#### Step 3 - Incrementally Process those Partitions
- We will utilize the logical partitions identified in Step 2, to incrementally process the partitions. 

![img](assets/overview_diagram.png)

In our example above we follow the three steps.
#### Define Logical Partitions
- Line item has order date and we will use order date.  
- It identifies the business event in our data that represents lifecycle changes over time for a given period.

#### Identify Impacted Partitions
- Here we will query the staging table in the raw layer for the distinct order dates that have been in the data we just loaded.  
- We will store these dates into a common database table (DELTA_DATE) since this table is utilized across the data architecture layers.

#### Incrementally Process those Partitions
- We will utilize the impacted partitions and process those dates of data through the raw, integration and presentation layers.  

Let's see how this works!

<!-- ------------------------ -->
## Lab Overview
Duration: 3

Below is an overview diagram of what we will be building in this Quickstart.  Each step builds upon what was built in the prior step.

![img](assets/overview_diagram.png)

### Raw Layer
- Staging tables used for most recent loaded data - *_stg 
- History tables to track the history of changes, like an transaction log or audit table to record all changes to rows  - *_hist
- Permanent tables are used to maintain the current state of those rows in that table. 
- Transient tables are used for the _stg tables.

### Integration Layer
- For our labs, we have identified a unit of work to derive the margin at the line item level. 
- We will walk through the code to derive these intermediate results and how to utilize incremental processing for this.

### Presentation Layer
- In our example, we will create the order line fact table as well as the part dimension as part of a dimensional model that can be used for consumption.
- We will walk through how to incrementally process the new data coming in.

### Common database
- Used for common UDFs, file formats, stages and tables that are utilized across the layers.
- In our example we will create a table to hold the dates that need to be incrementally processed.  
- There will also be a table function created in the common database utilized for the logical partitions.

<!-- ------------------------ -->
## Quickstart Setup
Duration: 5

### Clone Repository for Quickstart
These are sample code templates used to demonstrate incremental processing and logical partitions.  This code is written using SQL Scripting.  The code is tool ignostic and can be easily implemented into your tool set.

You'll need to clone the repository for this Quickstart in your GitHub account. Visit the [DCDF Incremental Processing associated GitHub Repository](https://github.com/Snowflake-Labs/samples/dcdf_incremental_processing). For connection details about your new Git repository, open the Repository, click on the green "Code" icon near the top of the page and copy the "HTTPS" link.

<img src="assets/git_repo_url.png" width="300" />

>aside positive
>
> **NOTE:** This sample code contains additional tables that we will not go through as part of the quickstart.  They are just a continuation of the patterns we will discussing to build out a purpose built dimensional model sample.

### Sample Code Information
- These code templates are written using SQL Scripting.
  - Purpose of these scripts is to illustrate incremental processing and logical partitions
  - These scripts are tool agnostic.
  - These templates can be easily modified to your environment and implemented in your toolset.

- Naming Conventions of scripts
  - Names of the folders are prefixed with a number to identify the order they will run as part of the data pipeline.
  - Table Creation Scripts - Files with postfix of _tbl.sql
  - ELT Process Scripts - Files with postfix of _ld.sql
  - ddl_orch.sql is the parent script that will execute all the database, schema, and table creation scripts.
  - dml_orch.sql is the parent script that will execute the data pipeline.

<!-- ------------------------ -->
## Snowflake Setup
Duration: 5

### Sample Data Set
- Login to your account and verify that you have access to the SNOWFLAKE_SAMPLE_DATA database.  See screenshot below.
- SNOWFLAKE_SAMPLE_DATA data share is created by default in newer accounts.  If you are not seeing this data share, you might need to create the data share in your account.  [Using Sample Data](https://docs.snowflake.com/en/user-guide/sample-data-using.html)

![img](assets/sample_data_set.png)

### Creating Example Databases, Schemas, Tables and Warehouse
- Make sure you are in the folder on your laptop where you cloned the sample code.  You want to be at the top level where you see the sub-folders of 000_admin, 100_raw, etc.
- Let's create the databases, tables and warehouse using the default names.
- Run Snowsql from the command line.  This will create all the databases, schemas, tables and a warehouse that are needed for this sample code.  
``` sql
snowsql -a <account_name> -u <username> -r sysadmin -D l_env=dev -f ddl_orch.sql -o output_file=ddl_orch.out
```
- End of the output should show success like this screenshot.

![img](assets/snowsql_success.png)

### Example Line Items
As part of the labs, we will monitor specific line item records.
1. Login to your Snowflake account and open a worksheet. 
2. Copy and paste this query into a worksheet.
``` sql
-- Sample Order
select
              row_number() over(order by uniform( 1, 60, random() ) ) as seq_no
             ,l.l_orderkey
             ,o.o_orderdate
             ,l.l_partkey
             ,l.l_suppkey
             ,l.l_linenumber
             ,l.l_quantity
             ,l.l_extendedprice
             ,l.l_discount
             ,l.l_tax
             ,l.l_returnflag
             ,l.l_linestatus
             ,l.l_shipdate
             ,l.l_commitdate
             ,l.l_receiptdate
             ,l.l_shipinstruct
             ,l.l_shipmode
             ,l.l_comment
        from
            snowflake_sample_data.tpch_sf1000.orders o
            join snowflake_sample_data.tpch_sf1000.lineitem l
              on l.l_orderkey = o.o_orderkey
        where
                o.o_orderdate >= to_date('7/1/1998','mm/dd/yyyy')
            and o.o_orderdate  < to_date('7/2/1998','mm/dd/yyyy')
            and l_orderkey = 5722076550
            and l_partkey in ( 105237594, 128236374);
```
3. Output should look like this.
![img](assets/sample_initial_query.png)

<!-- ------------------------ -->
## Data Acquistion
Duration: 7

During this step we will acquiring the data from the SNOWFLAKE_SAMPLE_DATA to load in the next step. We will use the SNOWFLAKE_SAMPLE_DATA data set, lineitem table data to generate the data files to load into our raw layer.  

### Step 1 - Explain code snippets
1. Select to *"create worksheet from SQL file"* and load the 100_acquisition/line_item_acq.sql.
![img](assets/snowsight_load_from_file.png)
![img](assets/load_line_item_acq.png)
2. In the first few lines of the script we are setting the context for this script. For the lab, the defaults are DEV_WEBINAR_ORDERS_RL_DB for the database and TPCH for the schema in the raw layer.
``` sql
use database DEV_WEBINAR_ORDERS_RL_DB;
use schema   TPCH;
```
3. Next we are setting the date range of the data we want to acquire by setting the l_start_dt and l_end_dt variables.  There is a 17 day range here.  
``` sql
-- Set variables for this sample data for the time frame to acquire
set l_start_dt = dateadd( day, -16, to_date( '1998-07-02', 'yyyy-mm-dd' ) );
set l_end_dt   = dateadd( day,   1, to_date( '1998-07-02', 'yyyy-mm-dd' ) );
```
4. The *"copy into"* statement is where we are copying (Unloading) the data from the SNOWFLAKE_SAMPLE_DATA into CSV formatted files into an internal table stage.  As part of this copy we are modifying the data a bit to show changes in l_line_status over time.  

``` sql
-- run this 2 or 3 times to produce overlapping files with new and modified records.
copy into
    @~/line_item
from
(
    with l_line_item as
    (
        select
              row_number() over(order by uniform( 1, 60, random() ) ) as seq_no
             ,l.l_orderkey
             ,o.o_orderdate
             ,l.l_partkey
             ,l.l_suppkey
             ,l.l_linenumber
             ,l.l_quantity
             ,l.l_extendedprice
             ,l.l_discount
             ,l.l_tax
             ,l.l_returnflag
             ,l.l_linestatus
             ,l.l_shipdate
             ,l.l_commitdate
             ,l.l_receiptdate
             ,l.l_shipinstruct
             ,l.l_shipmode
             ,l.l_comment
        from
            snowflake_sample_data.tpch_sf1000.orders o
            join sample_data.tpch_sf1000.lineitem l
              on l.l_orderkey = o.o_orderkey
        where
                o.o_orderdate >= $l_start_dt
            and o.o_orderdate  < $l_end_dt
    )
    select
         l.l_orderkey
        ,l.o_orderdate
        ,l.l_partkey
        ,l.l_suppkey
        ,l.l_linenumber
        ,l.l_quantity
        ,l.l_extendedprice
        ,l.l_discount
        ,l.l_tax
        ,l.l_returnflag
        -- simulate modified data by randomly changing the status
        ,case uniform( 1, 100, random() )
            when  1 then 'A'
            when  5 then 'B'
            when 20 then 'C'
            when 30 then 'D'
            when 40 then 'E'
            else l.l_linestatus
         end                            as l_linestatus
        ,l.l_shipdate
        ,l.l_commitdate
        ,l.l_receiptdate
        ,l.l_shipinstruct
        ,l.l_shipmode
        ,l.l_comment
        ,current_timestamp()            as last_modified_dt -- generating a last modified timestamp as part of data acquisition.
    from
        l_line_item l
    order by
        l.l_orderkey
)
file_format      = ( type=csv field_optionally_enclosed_by = '"' )
overwrite        = false
single           = false
include_query_id = true
max_file_size    = 16000000
;
```

### Step 2 - Execute the code and Verify results
In this step we will unload data for the line_item, part and orders data.

**LINE_ITEM_ACQ.SQL**

1. Setting the context of your script.  Highlight these in your worksheet, and run them to set the context.
``` sql

use database DEV_WEBINAR_ORDERS_RL_DB;
use schema   TPCH;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Highlight the code to set the variables for l_start_dt, l_end_dt and run them.
``` sql
-- Set variables for this sample data for the time frame to acquire
set l_start_dt = dateadd( day, -16, to_date( '1998-07-02', 'yyyy-mm-dd' ) );
set l_end_dt   = dateadd( day,   1, to_date( '1998-07-02', 'yyyy-mm-dd' ) );
```
![img](assets/Statement_executed_successfully.png)

3. Let's verify those variables have been set. Run the following statement in your worksheet.
``` sql
select $l_start_dt, $l_end_dt;
```
![img](assets/acq_start_end_dates.png)

4. Set your cursor on the *"copy into"* command and run it.
5. This might take around 2-3 minutes on a small warehouse.  If you want to increase the size of your warehouse, it will run faster. The output should be similar to this.
![img](assets/acq_copy_output.png)

6. Let's verify the number of files created. Paste this SQL into your worksheet and run it.  Output should be similar to this.
``` sql
list @~/line_item;
```
![img](assets/acq_list_files.png)

**PART_ACQ.SQL**
1. Select to *"create worksheet from SQL file"* and load the 100_acquisition/part_acq.sql.
2. Setting the context of your script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use database DEV_WEBINAR_ORDERS_RL_DB;
use schema   TPCH;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

3. Set your cursor on the *"copy into"* command and run it.  This might take a few minutes.  The output should be similar to this.
![img](assets/acq_part_results.png)

**ORDERS_ACQ.SQL**
1. Select to *"create worksheet from SQL file"* and load the 100_acquisition/orders_acq.sql.
2. Setting the context of your script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use database DEV_WEBINAR_ORDERS_RL_DB;
use schema   TPCH;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

3. Set your cursor on the *"copy into"* command and run it.  This might take a few minutes.  The output should be similar to this.
![img](assets/acq_orders_results.png)

<!-- ------------------------ -->
## Raw Layer - Staging the data
Duration: 7

During this step we will load the acquired data from the prior step (Data Acquisition) into the staging tables in the raw layer.

![img](assets/raw_layer_load_stg_diagram.png)
>aside positive
>
>This diagram illustrates the first steps of loading the new data files into the raw layer tables.
>
> - **Incremental Processing Step 1** is to define the logical partitions.  In the line item data we have identified the orderdate as the logical partition.
> - New data files from the Online Orders data source are placed into cloud storage.
> - Truncate/Reload pattern is used here to load the line_item_stg table.
> - First we truncate the prior data, and then load the new into the line_item_stg table.
 
#### Step 1 - Explain code snippets
1. In Snowsight, *"create worksheet from SQL file"*, select the 200_raw/line_item_stg_ld.sql
2. In the code, after setting the context, the next step is to truncate the line_item_stg table to remove any old ddata from the previous run.
``` sql
truncate table line_item_stg;
```
3. Below in the *"copy into"* statement, the data from the files produced in the acquisition steps, will be loaded in one statement.  This is a bulk load.  
4. The purge parameter is set to true so that the files will be purged from the internal table stage once they have been loaded.  This saves on storage usage and cost since these files are no longer needed.
``` sql
-- perform bulk load
copy into
    line_item_stg
from
    (
    select
         s.$1                                            -- l_orderkey
        ,s.$2                                            -- o_orderdate
        ,s.$3                                            -- l_partkey
        ,s.$4                                            -- l_suppkey
        ,s.$5                                            -- l_linenumber
        ,s.$6                                            -- l_quantity
        ,s.$7                                            -- l_extendedprice
        ,s.$8                                            -- l_discount
        ,s.$9                                            -- l_tax
        ,s.$10                                           -- l_returnflag
        ,s.$11                                           -- l_linestatus
        ,s.$12                                           -- l_shipdate
        ,s.$13                                           -- l_commitdate
        ,s.$14                                           -- l_receiptdate
        ,s.$15                                           -- l_shipinstruct
        ,s.$16                                           -- l_shipmode
        ,s.$17                                           -- l_comment
        ,s.$18                                           -- last_modified_dt
        ,metadata$filename                               -- dw_file_name
        ,metadata$file_row_number                        -- dw_file_row_no
        ,current_timestamp()                             -- dw_load_ts
    from
        @~ s
    )
purge         = true
pattern       = '.*line_item/data.*\.csv\.gz'
file_format   = ( type=csv field_optionally_enclosed_by = '"' )
on_error      = skip_file
--validation_mode = return_all_errors
;
```

#### Step 2 - Execute code and Verify Results
In this step we will load 3 _stg tables: line_item_stg, orders_stg and part_stg.

**LINE_ITEM_STG_LD.SQL**
1. Make sure you have 200_raw/line_item_stg_ld.sql script open in Snowsight.  
2. Setting the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

3. Highlight the truncate command in the script and run it.
``` sql
truncate table line_item_stg;
```
![img](assets/Statement_executed_successfully.png)

4. Set your cursor on the *"copy into"* command and run it.  On a small warehouse this will take approximately 1 minute to load the files. The results should look like this.
![img](assets/raw_layer_line_item_stg_load_complete.png)

5. Let's verify the data was loaded.  Highlight this in your worksheet and run it.  
``` sql
select 
    *
from 
    table(information_schema.copy_history(table_name=>'LINE_ITEM_STG', start_time=> dateadd(hours, -1, current_timestamp())))
where
    status = 'Loaded'
order by
    last_load_time desc
;
```
7.  The results will look similar to this.  File name might differ.
![img](assets/raw_layer_copy_history_results.png)

8. Let's verify that the lines that we are monitoring are loaded into the line_item_stg table. Highlight this in your worksheet and run it.
``` sql
select * 
from dev_webinar_orders_rl_db.tpch.line_item_stg 
where l_orderkey = 5722076550
and l_partkey in ( 105237594, 128236374); -- 2 lines
```

![img](assets/raw_layer_verify_stg_ld.png)

**PART_STG_LD.SQL**

1. Now, we will load the part data into the staging table so we can utilize this later. Select to *"create worksheet from SQL file"* and load the 200_raw/part_stg_ld.sql.  
2. Setting the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

3. Highlight the truncate command in the script and run it.
``` sql
truncate table part_stg;
```
![img](assets/Statement_executed_successfully.png)

4. Set your cursor on the *"copy into"* command and run it.  On a small warehouse this will take approximately 2 minutes to load the files. The results should look like this.
![img](assets/raw_layer_part_stg_results.png)

**ORDERS_STG_LD.SQL**

1. Now, we will load the part data into the staging table so we can utilize this later. Select to *"create worksheet from SQL file"* and load the 200_raw/orders_stg_ld.sql.  
2. Setting the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

3. Highlight the truncate command in the script and run it.
``` sql
truncate table orders_stg;
```
![img](assets/Statement_executed_successfully.png)

4. Set your cursor on the *"copy into"* command and run it.  On a small warehouse this will take approximately 2 minutes to load the files. The results should look like this.
![img](assets/raw_layer_orders_stg_results.png)

<!-- ------------------------ -->
## Raw Layer - Identify Impacted Partitions
Duration: 5

During this step we will identify the impacted partitions that were loaded into the staging tables in the raw layer and persisting those identified partitions in a table for use in subsequent steps.

![img](assets/raw_layer_impacted_partitions.png)

>aside positive
>
>In this diagram illustrates the concept of identifying the impacted partitions, persisting them to be utilized in all the layers of the data architecture to incrementally process the data.
>
> - **Incremental Processing Step 2** is to identify the impacted partitions.  
> - In this diagram, we select from the line_item_stg table all the distinct orderdates that are impacted by the new data that was loaded.  
> - Then we persist those dates into a table called *"dw_delta_date"* so that we can utilize those impacted partitions to do our incremental processing at each layer (raw, integration and presentation).

### Step 1 - Explain code snippets
1. In Snowsight, *"create worksheet from SQL file"*, select the 200_raw/dw_delta_date_ld.sql
2. After setting the context there is an *"insert"* statement.  As part of the *"insert"* statement, there is a [CTE (Common Table Expression)](https://docs.snowflake.com/en/user-guide/queries-cte.html) identified by the *"with"* statement inside the *"insert"* statement. This *"select"* identifies all the orderdates that were impacted with the load into the stg table.
``` sql
insert overwrite into dw_delta_date
with l_delta_date as
(
    select distinct
        o_orderdate as event_dt
    from
        dev_webinar_orders_rl_db.tpch.line_item_stg 
)
select
     event_dt
    ,current_timestamp()            as dw_load_ts
from
    l_delta_date
order by
    1
;
```
3. As part of the objects we created back in the Getting Started Section, we created a table function called dw_delta_date_range_f.  This function will take a type of time period such as day, week, month, quarter and year as a parameter, and return rows with a start_date and end_date of that period.  
4. In Snowsight, *"create worksheet from SQL file"*, select the 000_admin/dw_delta_date_range_f.sql
``` sql
use schema   &{l_common_schema};;

create or replace function dw_delta_date_range_f
(
    p_period_type_cd   varchar
)
returns table( start_dt timestamp_ltz, end_dt timestamp_ltz )
as
$$
    select
         start_dt
        ,end_dt
    from
        (
        select
             case lower( p_period_type_cd )
                 when 'all'     then current_date()
                 when 'day'     then date_trunc( day, event_dt )
                 when 'week'    then date_trunc( week, event_dt )
                 when 'month'   then date_trunc( month, event_dt )
                 when 'quarter' then date_trunc( quarter, event_dt )
                 when 'year'    then date_trunc( year, event_dt )
                 else current_date()
             end                as partition_dt
            ,min( event_dt ) as start_dt
            ,max( event_dt ) as end_dt
        from
            dw_delta_date
        group by
            1
        )
    order by
        1
$$
;
```

### Step 2 - Execute code and Verify Results
**DW_DELTA_DATE_LD.SQL**

1. Setting the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use database dev_webinar_common_db;
use schema util;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Set the cursor on the *"insert overwrite"* statement and run it. The output should look like the following.

![img](assets/delta_date_results.png)

3. Verify that the order dates for 17 days were loaded into the dw_delta_date table. Highlight this query into your worksheet and run it.
``` sql
select * 
from dev_webinar_common_db.util.dw_delta_date
order by event_dt;
```
![img](assets/delta_date_load_verify.png)

4. Verify the table function returns results as well. Highlight this query your worksheet and run it.  This will return 3 rows representing 3 weeks of data.  We will utilize this table function in future scripts.
``` sql
select start_dt, end_dt 
FROM table(dev_webinar_common_db.util.dw_delta_date_range_f('week')) 
order by 1;
```
![img](assets/delta_date_table_function_output.png)


<!-- ------------------------ -->
## Raw Layer - Incrementally Process
Duration: 15

During this step we will incrementally process through the data, loading it into the persistent tables in the raw layer utilizing the impacted partitions that were identified in the prior step. 

![img](assets/raw_layer_incremental_processing.png)

>aside positive
>In this diagram we are illustrating the concept of "looping" through the impacted partitions and processing only that data impacted into the persistent tables in the raw layer.
>
> -  **Incremental Processing Step 3** is to utilize the impacted partitions to process the data through each of the layers.
> - Here we are using the order dates stored in the delta_date table to identify the dates that need to be processed into the line_item_hist and line_item tables.  
> - In the line_item_hist table we are capturing the life cycle of the rows as they change.  This is for audit purposes or tracking.
> - In the line_item table, we are peristing the current state of that line_item row.

### Step 1 - Explain code snippets
1. In Snowsight, *"create worksheet from SQL file"*, select the 200_raw/line_item_hist_ld.sql
2. After we set the context, there is the statement as below.  Since we are using [SQL Scripting](https://docs.snowflake.com/en/developer-guide/snowflake-scripting/index.html) this statement is used to create the anonymous block.
``` sql
execute immediate $$
```
3. In the declaration section, we are defining 2 variables (l_start_dt, and l_end_dt) that we will use to process the logical partition start and end dates.  
``` sql
declare
  l_start_dt date;
  l_end_dt   date;
```
4. Then we are declaring the cursor which is the results of the dw_delta_date_range_f table function that will return a start and end date for a week.  
``` sql
declare
  ...
  c1 cursor for select start_dt, end_dt FROM table(dev_webinar_common_db.util.dw_delta_date_range_f('week')) order by 1;
```
5.  The *"for"* loop is where we will loop through the weeks and process a week at a time.  This is the incremental processing.
``` sql
begin
  --
  -- Loop through the dates to incrementally process based on the logical partition definition.
  -- In this example, the logical partitions are by week.
  --
  for record in c1 do
    l_start_dt := record.start_dt;
    l_end_dt   := record.end_dt;
    ...
  end for;

end;
```
6. Scroll down to the *"insert"* statement.  
7. Inside that CTE *"with"* statement named l_stg, the surrogate key and hash diff columns (_shk) are being created in this CTE that will be used in this script, to assist in identifying which rows have changed.
``` sql
insert into line_item_hist
with l_stg as
    (
        --
        -- Driving CTE to identify all records in the logical partition to be processed.
        select
            -- generate hash key and hash diff to streamline processing
             sha1_binary( concat( s.l_orderkey, '|', s.l_linenumber ) )  as dw_line_item_shk
            --
            -- note that last_modified_dt is not included in the hash diff since it only represents recency of the record versus an 
            -- actual meaningful change in the data
            ,sha1_binary( concat( s.l_orderkey
                                         ,'|', coalesce( to_char( s.o_orderdate, 'yyyymmdd' ), '~' )
                                         ,'|', s.l_linenumber
                                         ,'|', coalesce( to_char( s.l_partkey ), '~' )
                                         ,'|', coalesce( to_char( s.l_suppkey ), '~' )
                                         ,'|', coalesce( to_char( s.l_quantity ), '~' )
                                         ,'|', coalesce( to_char( s.l_extendedprice ), '~' )
                                         ,'|', coalesce( to_char( s.l_discount ), '~' )
                                         ,'|', coalesce( to_char( s.l_tax ), '~' )
                                         ,'|', coalesce( to_char( s.l_returnflag ), '~' )
                                         ,'|', coalesce( to_char( s.l_linestatus ), '~' )
                                         ,'|', coalesce( to_char( s.l_shipdate, 'yyyymmdd' ), '~' )
                                         ,'|', coalesce( to_char( s.l_commitdate, 'yyyymmdd' ), '~' )
                                         ,'|', coalesce( to_char( s.l_receiptdate, 'yyyymmdd' ), '~' )
                                         ,'|', coalesce( s.l_shipinstruct, '~' )
                                         ,'|', coalesce( s.l_shipmode, '~' )
                                         ,'|', coalesce( s.l_comment, '~' )
                                )
        
                        )               as dw_hash_diff
            ,s.*
        from
            line_item_stg s
```

8. In that CTE, the data is also being filtered (*"where"* clause) from the line_item_stg table to select only those rows that have an orderdate that is in that logical partiton week.  Processing one week at a time.
``` sql
insert into line_item_hist
with l_stg as
    (
        --
        -- Driving CTE to identify all records in the logical partition to be processed.
        select
            ...
        from
            line_item_stg s
        where
                s.o_orderdate >= :l_start_dt
            and s.o_orderdate  < :l_end_dt
    )
```

9. The next CTE named l_deduped will go through and dedupe the records in the prior CTE (l_stg) using the hash_diff to identify duplicate rows.  This eliminates duplicates from getting loaded into the permanent raw layer line_item_hist table.
``` sql
,l_deduped as
    (
        --
        -- Dedupe the records from the staging table.
        -- This assumes that there may be late arriving or duplicate data that were loaded
        -- Need to identify the most recent record and use that to update the Current state table.
        -- as there is no reason to process each individual change in the record, the last one would have the most recent updates
        select
            *
        from
            l_stg
        qualify
            row_number() over( partition by dw_hash_diff order by last_modified_dt desc, dw_file_row_no )  = 1
    )
```

10. The final outside *"select"* will again select from the permanent raw layer table (line_item_hist) for the same logical partition range (week), and compare it to the deduped staging records to identify what needs to be inserted into the line_item_hist table.
``` sql
    select
        ...
    from
        l_deduped s
    where
        s.dw_hash_diff not in
        (
            -- Select only the rows in that logical partition from the final table.
            select dw_hash_diff from line_item_hist 
            where
                    o_orderdate >= :l_start_dt
                and o_orderdate  < :l_end_dt
        )
```

11. **Important:**  The *"order by"* is a key point as it sorts the rows with the same orderdate together in the micropartitions as they are inserted into the table, to optimize query performance.
``` sql
    order by
        o_orderdate  -- physically sort rows by a logical partitioning date
    ;
```

12. In Snowsight, *"create worksheet from SQL file"*, select the 200_raw/line_item_ld.sql
13. This script is very similar to line_item_hist_ld.sql but this is a merge pattern.  This has the same anonymous block and same variable declarations and same cursor definition with the table function to loop through the logical partitions.  Also it has the same *"for"* loop.
``` sql
execute immediate $$

declare
  l_start_dt date;
  l_end_dt   date;
  -- Grab the dates for the logical partitions to process
  c1 cursor for select start_dt, end_dt FROM table(dev_webinar_common_db.util.dw_delta_date_range_f('week')) order by 1;

begin

  --
  -- Loop through the dates to incrementally process based on the logical partition definition.
  -- In this example, the logical partitions are by week.
  --
  for record in c1 do
    l_start_dt := record.start_dt;
    l_end_dt   := record.end_dt;
    ...
```

14. It has the same initial CTE (l_stg) to identify the line_item_stg records within that week of logical partitions. It also doing the same surrogate key and hash diff derivations.
``` sql
       with l_stg as
        (
            --
            -- Driving CTE to identify all records in the logical partition to be processed
            --
            select
                -- generate hash key and hash diff to streamline processing
                 sha1_binary( concat( s.l_orderkey, '|', s.l_linenumber ) )  as dw_line_item_shk
                --
                -- note that last_modified_dt is not included in the hash diff since it only represents recency of the record versus an 
                -- actual meaningful change in the data
                --
                ,sha1_binary( concat( s.l_orderkey
                                     ,'|', coalesce( to_char( s.o_orderdate, 'yyyymmdd' ), '~' )
                                     ,'|', s.l_linenumber
                                     ,'|', coalesce( to_char( s.l_partkey ), '~' )
                                     ,'|', coalesce( to_char( s.l_suppkey ), '~' )
                                     ,'|', coalesce( to_char( s.l_quantity ), '~' )
                                     ,'|', coalesce( to_char( s.l_extendedprice ), '~' )
                                     ,'|', coalesce( to_char( s.l_discount ), '~' )
                                     ,'|', coalesce( to_char( s.l_tax ), '~' )
                                     ,'|', coalesce( to_char( s.l_returnflag ), '~' )
                                     ,'|', coalesce( to_char( s.l_linestatus ), '~' )
                                     ,'|', coalesce( to_char( s.l_shipdate, 'yyyymmdd' ), '~' )
                                     ,'|', coalesce( to_char( s.l_commitdate, 'yyyymmdd' ), '~' )
                                     ,'|', coalesce( to_char( s.l_receiptdate, 'yyyymmdd' ), '~' )
                                     ,'|', coalesce( s.l_shipinstruct, '~' )
                                     ,'|', coalesce( s.l_shipmode, '~' )
                                     ,'|', coalesce( s.l_comment, '~' )
                                    )
            
                            )               as dw_hash_diff
                ,s.*
            from
                line_item_stg s
            where
                    s.o_orderdate >= :l_start_dt
                and s.o_orderdate  < :l_end_dt
        )
```

15. It has the same dedupe logic.
``` sql
,l_deduped as
    (
        --
        -- Dedupe the records from the staging table.
        -- This assumes that there may be late arriving or duplicate data that were loaded
        -- Need to identify the most recent record and use that to update the Current state table.
        -- as there is no reason to process each individual change in the record, the last one would have the most recent updates
        select
            *
        from
            l_stg
        qualify
            row_number() over( partition by dw_hash_diff order by last_modified_dt desc, dw_file_row_no )  = 1
    )
```
16. But...it does have an additional CTE.  This CTE is important for partition pruning efficiencies.  Selecting only those rows from the final table that are in the logical partition range we are processing.  
``` sql
,l_tgt as
        (
            --
            -- Select the records in the logical partition from the current table. 
            -- Its own CTE, for partition pruning efficiencies
            select *
            from line_item
            where
                    o_orderdate >= :l_start_dt
                and o_orderdate  < :l_end_dt
        )
```
17. Now let's look at the *"merge"* statement.  In the *"select"* statement below, the l_deduped CTE and l_tgt CTE are joined together with a left join to identify the rows that are in line_item_stg table that might not in the permanent table or where the hash_diff is different and the modified date is after what is already in the table.  
``` sql
-- Merge Pattern 
    --
    merge into line_item tgt using
    (
      ...
        select
             current_timestamp()        as dw_version_ts
            ,s.*
        from
            l_deduped s
            left join l_tgt t on
                t.dw_line_item_shk = s.dw_line_item_shk
        where
            -- source row does not exist in target table
            t.dw_line_item_shk is null
            -- or source row is more recent and differs from target table
            or (
                    t.last_modified_dt  < s.last_modified_dt
                and t.dw_hash_diff     != s.dw_hash_diff
               )
        order by
            s.o_orderdate  -- physically sort rows by logical partitioning date
    ) src
```
18. **Important:** Another note is the *"on"* clause of the *"merge"* statement.  The logical partition dates are used there to filter/limit the full table scan on the line_item permanent table for the *"merge"*.
``` sql
-- Merge Pattern 
    --
    merge into line_item tgt using
    (
      ...
    on
    (
            tgt.dw_line_item_shk = src.dw_line_item_shk
        and tgt.o_orderdate     >= :l_start_dt
        and tgt.o_orderdate      < :l_end_dt
    )
```
### Step 2 - Execute code and Verify Results

**LINE_ITEM_HIST_LD.SQL**
1. Select *"create worksheet from SQL file"*, select the 200_raw/line_item_hist_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Put your cursor on the *"execute immediate"* command at the top of the script and run it.
![img](assets/anonymous_block_success.png)

3. Let's verify that the data was loaded into the line_item_hist table. Copy/Paste this query into your worksheet.  If you have run these load scripts multiple times you may see history changes in this table.
``` sql
select * 
from dev_webinar_orders_rl_db.tpch.line_item_hist 
where l_orderkey = 5722076550 
and l_partkey in ( 105237594, 128236374)
order by 1;
```
![img](assets/raw_layer_line_item_hist_output.png)

4. Open the worksheet for the 200_raw/line_item_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

5. Put your cursor on the *"execute immediate"* command at the top of the script and run it.
![img](assets/anonymous_block_success.png)

6. Let's verify that the data was loaded into the line_item table. Highlight this query in your worksheet and run it.
``` sql
select * 
from dev_webinar_orders_rl_db.tpch.line_item 
where l_orderkey = 5722076550 
and l_partkey in ( 105237594, 128236374)
order by 1;
```
![img](assets/raw_layer_line_item_hist_output.png)

**PART_LD.SQL**
1. Now we want to load the part data into the part table.  Open the worksheet for the 200_raw/part_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Put your cursor on the *"execute immediate"* command at the top of the script and run it.
![img](assets/anonymous_block_success.png)

3. Verify the part table was loaded.  Highlight the query and run it.
``` sql
select *
from dev_webinar_orders_rl_db.tpch.part
where p_partkey in ( 105237594, 128236374);
```
![img](assets/raw_layer_part_verify.png)

**ORDER_HIST_LD.SQL**
1. Now we want to load the changed order data into the order_hist table.  Open the worksheet for the 200_raw/order_hist_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Put your cursor on the *"execute immediate"* command back up at the top of the script and run it.
![img](assets/anonymous_block_success.png)

**ORDER_LD.SQL**
1. Now we want to load the order data into the order table.  Open the worksheet for the 200_raw/order_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_orders_rl_db;
use schema   tpch;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Put your cursor on the *"execute immediate"* command back up at the top of the script and run it.
![img](assets/anonymous_block_success.png)

3. Verify the orders table was loaded with our order.  Highlight the query and run it.
``` sql
select * 
from dev_webinar_orders_rl_db.tpch.orders 
where o_orderkey = 5722076550;
```
![img](assets/raw_layer_order_verify.png)

<!-- ------------------------ -->
## Integration Layer
Duration: 10

During this step we will incrementally process an isolated unit of work deriving certain business rules utilizing the identified impacted partitions. 

![img](assets/integration_incremental_process.png)
>aside positive
>
>In this diagram illustrates the steps for incremental processing units of work in the integration layer of the DCDF data architecture.
>
> - A unit of work has been identified where the line item margin needs to be derived/calculated for each line item.
> - This is an isolated unit of work with business rules that should be incrementally processed each time new or changed line items are processed.  
> - Extensible, ease of maintenance for that unit of work.  As rules change to derive the margin, then they can be added/changed here in one place.
> - The impacted logical partitions have been identified and will be incrementally processed.  

### Step 1 - Explain code snippets
1. In Snowsight, *"create worksheet from SQL file"*, select the 310_derivation/line_item_margin_ld.sql
2. This script is also using the anonymous block in SQL Scripting. 
``` sql
execute immediate $$
```
3. Again, the cursor is being declared which is the results of the dw_delta_date_range_f table function that will return a start and end date for a week.  We are going to loop through the weeks and process a week at a time.  This is the incremental processing.
``` sql
declare
  l_start_dt date;
  l_end_dt   date;
  -- Grab the dates for the logical partitions to process
  c1 cursor for select start_dt, end_dt FROM table(dev_webinar_common_db.util.dw_delta_date_range_f('week')) order by 1;

begin

  --
  -- Loop through the dates to incrementally process based on the logical partition definition.
  -- In this example, the logical partitions are by week.
  --
  for record in c1 do
    l_start_dt := record.start_dt;
    l_end_dt   := record.end_dt;
```
4. The merge processing pattern is being used here just like in the line_item_ld.sql with similar CTEs to select the data using the logical partitions.  Important is on the *"on"* clause of the *"merge"*, it is filtering on the logical partitions again here. 
``` sql
merge into line_item_margin t using
    (
        with l_src as
        (
            -- 
            -- Driving CTE to identify all the records in the logical partition to be process
            --
            select
                 s.dw_line_item_shk
                ,s.o_orderdate
                ,s.l_extendedprice - (s.l_quantity * p.ps_supplycost ) as margin_amt
                ,s.last_modified_dt
            from
                dev_webinar_orders_rl_db.tpch.line_item s
                join dev_webinar_orders_rl_db.tpch.partsupp p
                  on ( p.ps_partkey = s.l_partkey
                       and p.ps_suppkey = s.l_suppkey )
            where
                    s.o_orderdate >= :l_start_dt
                and s.o_orderdate  < :l_end_dt
        )
        ,l_tgt as
        (
            -- 
            -- Select the records in the logical partition from the current table.
            -- Its own CTE, for partition pruning efficiencies
            select *
            from line_item_margin
            where
                    o_orderdate >= :l_start_dt
                and o_orderdate  < :l_end_dt
        )
        select
             current_timestamp()        as dw_update_ts
            ,s.*
        from
            l_src s
            left join l_tgt t on
                t.dw_line_item_shk = s.dw_line_item_shk
        where
            -- source row does not exist in target table
            t.dw_line_item_shk is null
            -- or source row is more recent and differs from target table
            or (
                    t.last_modified_dt  < s.last_modified_dt
                and t.margin_amt       != s.margin_amt
               )
        order by
            s.o_orderdate
    ) s
    on
    (
        t.dw_line_item_shk = s.dw_line_item_shk
        and t.o_orderdate >= :l_start_dt 
        and t.o_orderdate  < :l_end_dt
    )
```

### Step 2 - Execute code and Verify Results
1. Open the worksheet for the line_item_margin_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_il_db;
use schema   main;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)

2. Put your cursor on the *"execute immediate"* command back up at the top of the script and run it.
![img](assets/anonymous_block_success.png)

3. Let's verify that the data was loaded into the line_item_margin table. Copy/Paste this query into your worksheet.  If you have run these load scripts multiple times you may see history changes in this table.
``` sql
-- Integration
select m.*
from dev_webinar_il_db.main.line_item_margin m
    join dev_webinar_orders_rl_db.tpch.line_item l
where l.l_orderkey = 5722076550 
and l.l_partkey in ( 105237594, 128236374)
and m.dw_line_item_shk = l.dw_line_item_shk;
```
![img](assets/integration_line_item_margin_results.png)
<!-- ------------------------ -->
## Presentation Layer
Duration: 6

During this step we will incrementally process the data that was loaded, and re-organizing the data for consumption utilizing the identified impacted partitions.

![img](assets/presentation_incremental_process.png)
>aside positive
>
>In this diagram illustrates the steps for incremental processing for the presentation layer of the DCDF data architecture.
>
> - Order_line_fact is a purpose built solution for consumption and analytics.
> - Dimensional model as an example to provide a solution around the orders lines and consumption at that atomic level of data.
> - The impacted logical partitions have been identified and will be incrementally processed in the presentation layer.

### Step 1 - Explain code snippets
1. In Snowsight, *"create worksheet from SQL file"*, select the 410_fact_atomic/order_line_fact_ld.sql
2. This script is also using the anonymous block in SQL Scripting. 
``` sql
execute immediate $$
```
3. Again, the cursor is being declared which is the results of the dw_delta_date_range_f table function that will return a start and end date for a week.  We are going to loop through the weeks and process a week at a time.  This is the incremental processing.
``` sql
declare
  l_start_dt date;
  l_end_dt   date;
  -- Grab the dates for the logical partitions to process
  c1 cursor for select start_dt, end_dt FROM table(dev_webinar_common_db.util.dw_delta_date_range_f('week')) order by 1;

begin

  --
  -- Loop through the dates to incrementally process based on the logical partition definition.
  -- In this example, the logical partitions are by week.
  --
  for record in c1 do
    l_start_dt := record.start_dt;
    l_end_dt   := record.end_dt;
```
4.  Within the loop, this is a delete/insert processing pattern.  There are both a *"delete"* and *"insert"* statements.  The *"delete"* statement will delete from the order_line_fact table any rows within the logical partition. This logical partition is the week of order dates in our example.  Then the insert will insert all the rows for that logical partition into the order_line_fact table.
5. The reason the deletes and then inserts are being done is to handle situations such as late arriving dimensions. For instance if the supplier wasn't available when the order line item was first ordered, that value would be some default.  Then as the status of the lfine item changes, and the supplier was updated, the original defaulted row would need to be removed.
``` sql
-- Delete the records using the logical partition 
     -- Very efficient when all the rows are in the same micropartitions.  Mirrors a truncate table in other database platforms.
     delete from order_line_fact
     where orderdate >= :l_start_dt
       and orderdate <  :l_end_dt;
 
     -- Insert the logical partitioned records into the table
     -- Inserts data from same order date into the same micropartitions
     -- Enables efficient querying of the data for consumption
     insert into order_line_fact
     select
         li.dw_line_item_shk
        ,o.o_orderdate
        ,o.dw_order_shk
        ,p.dw_part_shk
        ,s.dw_supplier_shk
        ,li.l_quantity      as quantity
        ,li.l_extendedprice as extendedprice
        ,li.l_discount      as discount
        ,li.l_tax           as tax
        ,li.l_returnflag    as returnflag
        ,li.l_linestatus    as linestatus
        ,li.l_shipdate
        ,li.l_commitdate
        ,li.l_receiptdate
        ,lim.margin_amt
        ,current_timestamp() as dw_load_ts
     from
         webinar_rl_db.tpch.line_item li
         --
         join webinar_rl_db.tpch.orders o
           on o.o_orderkey = li.l_orderkey
         --
         join webinar_il_db.main.line_item_margin lim
           on lim.dw_line_item_shk = li.dw_line_item_shk
         --
         -- Left outer join in case the part record is late arriving
         --
         left outer join webinar_rl_db.tpch.part p
           on p.p_partkey = li.l_partkey
         --
         -- left outer join in case the supplier record is late arriving
         --
         left outer join webinar_rl_db.tpch.supplier s
           on s.s_suppkey = li.l_suppkey
     where 
             li.o_orderdate >= :l_start_dt
         and li.o_orderdate <  :l_end_dt
     order by o.o_orderdate;
```
6. Let's look at a dimension table load to illlustrate a different processing pattern *"insert overwrite"*.
7. In Snowsight, *"create worksheet from SQL file"*, select the 400_dimension/part_dm_ld.sql
8. This script is also using the anonymous block in SQL Scripting. 
``` sql
execute immediate $$
```
9. This script uses an insert overwrite pattern.  The code will overwrite the table with the new values in essence doing a truncate/insert.  The advantage of doing *"insert overwrite"* is that the table will never be empty.  With a truncate/insert pattern there could be time period in which the table is empty if users query the data.

``` sql
insert overwrite into part_dm
   select
       p.dw_part_shk
      ,p.p_partkey
      ,p.p_name as part_name
      ,p.p_mfgr as mfgr
      ,p.p_brand as brand
      ,p.p_type as type
      ,p.p_size as size
      ,p.p_container as container
      ,p.p_retailprice as retail_price
      ,p.p_comment as comment
      ,d.first_orderdate
      ,p.last_modified_dt
      ,p.dw_load_ts
      ,p.dw_update_ts
   from
       dev_webinar_orders_rl_db.tpch.part p
       left join dev_webinar_il_db.main.part_first_order_dt d
         on d.dw_part_shk = p.dw_part_shk;
```

### Step 2 - Execute code and Verify Results
1. Open the worksheet for the order_line_fact_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_pl_db;
use schema   main;
use warehouse dev_webinar_wh;
```
![img](assets/Statement_executed_successfully.png)
2. Put your cursor on the *"execute immediate"* command back up at the top of the script and run it.
![img](assets/anonymous_block_success.png)

3. Let's verify that the data was loaded into the order_line_fact table. Copy/Paste this query into your worksheet.  If you have run these load scripts multiple times you may see history changes in this table. 
``` sql
select olf.*
from dev_webinar_pl_db.main.order_line_fact olf
  join dev_webinar_orders_rl_db.tpch.line_item l
    on l.dw_line_item_shk = olf.dw_line_item_shk
where l.l_orderkey = 5722076550 
and l.l_partkey in ( 105237594, 128236374);
```
![img](assets/presentation_order_line_results.png)

4. Open the worksheet for the part_dm_ld.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_pl_db;
use schema   main;
use warehouse dev_webinar_wh;
```
5. Put your cursor on the *"execute immediate"* command back up at the top of the script and run it.
![img](assets/anonymous_block_success.png)

6. Let's verify that the data was loaded into the part_dm table. Copy/Paste this query into your worksheet.  If you have run these load scripts multiple times you may see history changes in this table. 
``` sql
select *
from dev_webinar_pl_db.main.part_dm p
where p_partkey in ( 105237594, 128236374);
```
![img](assets/presentation_part_dm_output.png)

<!-- ------------------------ -->
## BONUS - Type 2 Slowly Changing Dimension
Duration: 4

"Slowly changing dimension type 2 changes add a new row in the dimension with the updated attribute values. This requires generalizing the primary key of the dimension beyond the natural or durable key because there will potentially be multiple rows describing each member. When a new row is created for a dimension member, a new primary surrogate key is assigned and used as a foreign key in all fact tables from the moment of the update until a subsequent change creates a new dimension key and updated dimension row." -  Kimball Group.

During this section we will go through a Type 2 slowly changing dimension example of incremental processing for this dimension.   

### Step 1 - Acquistion
1. Select to *"create worksheet from SQL file"* and load the 100_acquisition/customer_initial_acq.sql.
2. In the first few lines of the script we are setting the context for this script. Run these.
3. The *"copy into"* statement is where we are copying (Unloading) the data from the SNOWFLAKE_SAMPLE_DATA into CSV formatted files into an internal table stage.  Run this.  
![img](assets/raw_layer_customer_acq_results.png)

### Step 2 - Raw Layer
1. Open the worksheet for the 100_acquisition/customer_acq.sql.  Set the context of our script.  Highlight these in your worksheet, and run them to set the context.
``` sql
use role     sysadmin;
use database dev_webinar_rl_orders_db;
use schema   tpch;
```
![img](assets/Statement_executed_successfully.png)

2. Make sure you have selected the *DEV_WEBINAR_WH* warehouse.
![img](assets/Setting_warehouse.png)
3. 



![img](assets/raw_layer_customer_stg_ld_results.png)

<!-- ------------------------ -->
## Cleanup
Duration: 2

This step is to cleanup and drop all the objects we created as part of this quickstart.

1. Open the worksheet for the 000_admin/cleanup.sql.  
``` sql
-- Cleanup all the objects we created

use role sysadmin;

drop database dev_webinar_orders_rl_db;
drop database dev_webinar_il_db;
drop database dev_webinar_pl_db;
drop database dev_webinar_common_db;
```
2. Run all the SQL statements to drop all the objects that were created.
![img](assets/Statement_executed_successfully.png)

<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 4

This tutorial was designed as a hands-on introduction to the Data Cloud Deployment Framework (DCDF) data architecture incremental processing and logical partitions.

We encourage you to continue with learning about the Data Cloud Deployment Framework, by watching the [Data Cloud Deployment Framework Series Webinars](https://www.snowflake.com/webinar/for-customers/data-cloud-deployment-framework-series/) either on-demand on register for upcoming episodes.  

Also the github repo scripts contain more tables than what was covered in this lab.  It's a full working template model taking source data from raw, through integration, to presentation layer dimension model ready for consumption. Take the time to go through each one of them and run them over and over.  Feel free to use these as code templates to be utilized in your own environment and accounts for your processing.

As you went through this quickstart, our hope is that you also noticed the repeatable patterns throughout these scripts which can facilitate that agile development process.

### What we have covered
- A data pipeline utilizing incremental processing and logical partition definitions
- Walked through raw, integration and presentation layer scripts and how each utilizes incremental processing and the logical partition definitions.
- Walked through code snippets for different processing patterns such as truncate/reload, insert overwrite, merge and delete/insert.