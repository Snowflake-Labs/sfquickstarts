author: Charlie Hammond
id: dbt-projects-on-snowflake
summary: This Quickstart will show you how to get started using dbt Projects on Snowflake
categories: Getting-Started, Data-Engineering, Tasty-Bytes
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering

# Getting Started with dbt Projects on Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 1



### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- how Workspaces allow you to edit
- how dbt Projects can be run within Snowflake
- how to deploy and orchistrate dbt Projects from within Snowflake.

### What You’ll Need 
- A [GitHub](https://github.com/) Account 

### What You’ll Build 
- A dbt Project running within your Snowflake account

<!-- ------------------------ -->
## Setup
Duration: 5

todo: test with existing tb setup
todo: test with sysadmin

We will be using Tasty Bytes data in this lab. Run the script below to build the data required for this lab. 

``` sql
USE ROLE accountadmin;
USE WAREHOUSE tasty_bytes_dbt_wh;

CREATE OR REPLACE DATABASE tb_101; -- source
CREATE OR REPLACE SCHEMA tb_101.raw;


CREATE OR REPLACE FILE FORMAT tb_101.public.csv_ff 
type = 'csv';

CREATE OR REPLACE STAGE tb_101.public.s3load
COMMENT = 'Quickstarts S3 Stage Connection'
url = 's3://sfquickstarts/frostbyte_tastybytes/'
file_format = tb_101.public.csv_ff;

/*--
 raw zone table build 
--*/

-- country table build
CREATE OR REPLACE TABLE tb_101.raw.country
(
    country_id NUMBER(18,0),
    country VARCHAR(16777216),
    iso_currency VARCHAR(3),
    iso_country VARCHAR(2),
    city_id NUMBER(19,0),
    city VARCHAR(16777216),
    city_population VARCHAR(16777216)
) 
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- franchise table build
CREATE OR REPLACE TABLE tb_101.raw.franchise 
(
    franchise_id NUMBER(38,0),
    first_name VARCHAR(16777216),
    last_name VARCHAR(16777216),
    city VARCHAR(16777216),
    country VARCHAR(16777216),
    e_mail VARCHAR(16777216),
    phone_number VARCHAR(16777216) 
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- location table build
CREATE OR REPLACE TABLE tb_101.raw.location
(
    location_id NUMBER(19,0),
    placekey VARCHAR(16777216),
    location VARCHAR(16777216),
    city VARCHAR(16777216),
    region VARCHAR(16777216),
    iso_country_code VARCHAR(16777216),
    country VARCHAR(16777216)
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- menu table build
CREATE OR REPLACE TABLE tb_101.raw.menu
(
    menu_id NUMBER(19,0),
    menu_type_id NUMBER(38,0),
    menu_type VARCHAR(16777216),
    truck_brand_name VARCHAR(16777216),
    menu_item_id NUMBER(38,0),
    menu_item_name VARCHAR(16777216),
    item_category VARCHAR(16777216),
    item_subcategory VARCHAR(16777216),
    cost_of_goods_usd NUMBER(38,4),
    sale_price_usd NUMBER(38,4),
    menu_item_health_metrics_obj VARIANT
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- truck table build 
CREATE OR REPLACE TABLE tb_101.raw.truck
(
    truck_id NUMBER(38,0),
    menu_type_id NUMBER(38,0),
    primary_city VARCHAR(16777216),
    region VARCHAR(16777216),
    iso_region VARCHAR(16777216),
    country VARCHAR(16777216),
    iso_country_code VARCHAR(16777216),
    franchise_flag NUMBER(38,0),
    year NUMBER(38,0),
    make VARCHAR(16777216),
    model VARCHAR(16777216),
    ev_flag NUMBER(38,0),
    franchise_id NUMBER(38,0),
    truck_opening_date DATE
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- order_header table build
CREATE OR REPLACE TABLE tb_101.raw.order_header
(
    order_id NUMBER(38,0),
    truck_id NUMBER(38,0),
    location_id FLOAT,
    customer_id NUMBER(38,0),
    discount_id VARCHAR(16777216),
    shift_id NUMBER(38,0),
    shift_start_time TIME(9),
    shift_end_time TIME(9),
    order_channel VARCHAR(16777216),
    order_ts TIMESTAMP_NTZ(9),
    served_ts VARCHAR(16777216),
    order_currency VARCHAR(3),
    order_amount NUMBER(38,4),
    order_tax_amount VARCHAR(16777216),
    order_discount_amount VARCHAR(16777216),
    order_total NUMBER(38,4)
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- order_detail table build
CREATE OR REPLACE TABLE tb_101.raw.order_detail 
(
    order_detail_id NUMBER(38,0),
    order_id NUMBER(38,0),
    menu_item_id NUMBER(38,0),
    discount_id VARCHAR(16777216),
    line_number NUMBER(38,0),
    quantity NUMBER(5,0),
    unit_price NUMBER(38,4),
    price NUMBER(38,4),
    order_item_discount_amount VARCHAR(16777216)
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

-- customer loyalty table build
CREATE OR REPLACE TABLE tb_101.raw.customer_loyalty
(
    customer_id NUMBER(38,0),
    first_name VARCHAR(16777216),
    last_name VARCHAR(16777216),
    city VARCHAR(16777216),
    country VARCHAR(16777216),
    postal_code VARCHAR(16777216),
    preferred_language VARCHAR(16777216),
    gender VARCHAR(16777216),
    favourite_brand VARCHAR(16777216),
    marital_status VARCHAR(16777216),
    children_count VARCHAR(16777216),
    sign_up_date DATE,
    birthday_date DATE,
    e_mail VARCHAR(16777216),
    phone_number VARCHAR(16777216)
)
COMMENT = '{"origin":"sf_sit-is", "name":"tasty-bytes-dbt", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":0, "source":"sql"}}';

/*--
 raw zone table load 
--*/

-- country table load
COPY INTO tb_101.raw.country
FROM @tb_101.public.s3load/raw_pos/country/;

-- franchise table load
COPY INTO tb_101.raw.franchise
FROM @tb_101.public.s3load/raw_pos/franchise/;

-- location table load
COPY INTO tb_101.raw.location
FROM @tb_101.public.s3load/raw_pos/location/;

-- menu table load
COPY INTO tb_101.raw.menu
FROM @tb_101.public.s3load/raw_pos/menu/;

-- truck table load
COPY INTO tb_101.raw.truck
FROM @tb_101.public.s3load/raw_pos/truck/;

-- customer_loyalty table load
COPY INTO tb_101.raw.customer_loyalty
FROM @tb_101.public.s3load/raw_customer/customer_loyalty/;

-- order_header table load
COPY INTO tb_101.raw.order_header
FROM @tb_101.public.s3load/raw_pos/order_header/;

-- order_detail table load
COPY INTO tb_101.raw.order_detail
FROM @tb_101.public.s3load/raw_pos/order_detail/;

-- setup completion note
SELECT 'tb_101 setup is now complete' AS note;

```

<!-- ------------------------ -->
## Introduction to Workspaces
Duration: 5

We will start with your personal Workspace. Workspaces provides a developer environment where you can  edit, test, and deploy your dbt projects, all within Snowflake. The personal workspace is your own area where you can create and edit files. 

Navigate to Projects > Workspaces to get started.

### Explore the Data
Let's explore the data we will be using in this lab. 

1. Create a new sql file in your Workspace and name it `data_profile.sql`.
2. Copy and paste the code below into the new file
3. Run the following queries just like you would in worksheets. 

``` sql 
USE WAREHOUSE default_wh;
USE ROLE attendee_role; 

-- What tables exist?
SHOW TABLES IN SCHEMA tb_101.raw;

-- What is the scale of data? 
SELECT COUNT(*) FROM tb_101.raw.order_header;

-- Understand a query that might be used in a mart -- in this case sales grouped by customer
SELECT 
    cl.customer_id,
    cl.city,
    cl.country,
    cl.first_name,
    cl.last_name,
    cl.phone_number,
    cl.e_mail,
    SUM(oh.order_total) AS total_sales,
    ARRAY_AGG(DISTINCT oh.location_id) AS visited_location_ids_array
FROM tb_101.raw.customer_loyalty cl
JOIN tb_101.raw.order_header oh
ON cl.customer_id = oh.customer_id
GROUP BY cl.customer_id, cl.city, cl.country, cl.first_name,
cl.last_name, cl.phone_number, cl.e_mail;
```

![data-profile](assets/data-profile.png)

### Create dbt Project from GitHub

Let's now clone an example dbt project we will use in the rest of this lab. 

1. Click the workspace dropdown > Create Workspace From Git Repository
2. In the popup, enter the following fields:
    1. Repository URL: `https://github.com/Snowflake-Labs/getting-started-with-dbt-on-snowflake.git`
    2. Workspace Name: `Example-dbt-Project`
    3. API Integration: `GIT_INTEGRATION`. Note: the [API Integration](https://docs.snowflake.com/en/developer-guide/git/git-setting-up#label-integrating-git-repository-api-integration) has already been configured for you. 
    4. Select Public Repository
3. Click Create!

![create-dbt-project](assets/create-workspace-git.png)
![create-dbt-project 2](assets/create-workspace-git-2.png)


<!-- ------------------------ -->
## Operate dbt Projects on Snowflake
Duration: 10

### Example Project 

We will work with Tasty Bytes data in this lab. The raw data includes sales data, truck metadata, and customer information. This will all be transformed with dbt and saved as a table in Snowflake. 

![data-linege](assets/data-lineage.png)

#### Add a new model

We will start by adding a new model to show how you can create using workspaces. Create a SQL file called `sales_data_by_truck.sql` in tasty_bytes_dbt_demo/models/marts. Copy the following code. 

```sql
with order_details as (
    select 
        od.order_id,
        od.menu_item_id,
        od.quantity,
        od.price,
        oh.truck_id,
        oh.order_ts,
        m.menu_type,
        m.truck_brand_name,
        m.item_category
    {% raw %} 
    from {{ ref('raw_pos_order_detail') }} od
    inner join {{ ref('raw_pos_order_header') }} oh on od.order_id = oh.order_id
    inner join {{ ref('raw_pos_menu') }} m on od.menu_item_id = m.menu_item_id
    {% endraw %}
)

select
    truck_brand_name,
    menu_type,
    item_category,
    date_trunc('month', order_ts) as sales_month,
    sum(quantity) as total_items_sold,
    sum(price) as total_revenue,
    count(distinct order_id) as total_orders
from order_details
where truck_brand_name is not null
group by 1, 2, 3, 4
order by 1, 2, 3, 4
```

![new-model](assets/new-model.png)

### Configure profiles.yml

Each dbt project folder in your Snowflake workspace must contain a profiles.yml file that specifies a target warehouse, database, schema, and role in Snowflake for the project. The type must be set to snowflake. 

dbt requires an account and user, but these can be left empty because the dbt project runs in Snowflake under the current account and user context.

When you run dbt commands, your workspace reads profiles.yml. When you have at least one valid target specified in profiles.yml, the selections for the targets defined in that project and the dbt commands available to run are available in the workspace menu bar.

We will keep the values in profiles.yml unchanged.

![profiles](assets/profiles.png)

### dbt deps

Let's start by running `dbt deps` to pull in the dbt_utils package. The dbt_utils package contains several usefull test that we have built into the project. 

From the dbt toolbar, you get dropdowns for the project, target, and command. Clicking the play button will run the relevant command. You can also click the down arrow to override the arguments. 

1. From the toolbar, select dev and deps. 
2. Click the dropdown arrow and enter `dbt_access_integration`. This [external access integration](https://docs.snowflake.com/en/sql-reference/sql/create-external-access-integration) has already been configured for you. 
3. Click the Deps button.

![dbt-deps](assets/dbt-deps.png)

### dbt compile

We will now run `dbt compile`. From the dropdown, click compile and run it. 

![dbt-compile](assets/dbt-compile.png)

#### View Compiled SQL

Once you have compiled the project, you can view the compiled SQL by clicking the View Compiled SQL button from an individual model. This shows the true tables and views the model will reference. 

#### View the DAG

You can also view the DAG to see how models interact with one another. Click DAG from the top toolbar to open the DAG.

### dbt run

Let's now run the project to pull data through our pipeline. From the dbt toolbar, select run from the dropdown, and click the play button. Once this completes, we have data in our marts tables!

### dbt test

Open tasty_bytes_dbt_demo/models/staging/__sources.yml to view data tests we have created. There are several common tests included, including ones from dbt_utils. On line 219, we have defined a maximum allowed value for order_amount. This is to flag abnormally large orders. 

Let's first run dbt tests to confirm the data meets our requirements. From the toolbar, select test, and click the play button. 

Oh no! There's an error with one of our tests. It looks like there is a test that doesn't quite look right. Let's update line 219 of `tasty_bytes_dbt_demo/models/staging/__sources.yml to be 10000 instead of 10. That should fix it. 

```yml
        - dbt_utils.accepted_range:  # Realistic order amount range
            min_value: 0
            max_value: 10000
            inclusive: true
```

### Deploy dbt Project

Now that we have updated and validated our dbt project, let's deploy it so we can build automation. Deploying a dbt project creates a Snowflake object and allows us to create tasks based on the object. 

1. Click Deploy in the top right of workspaces
2. Select database `tasty_bytes_dbt_db` and schema `raw`
3. Name it `dbt_project`
4. Deploy!

![deploy-dbt](assets/deploy-dbt.png)

### View git

Workspaces are fully git backed. To view changes and commit, click changes from the file selector. In this case, we have pulled from a public repository, so we will skip committing. 

![git-changes](assets/git-changes.png)


<!-- ------------------------ -->
## Orchistration and Monitoring
Duration: 5

### Tasks

Let's create tasks to regularly run and test our dbt project. Copy the script below into a new SQL file and run the commands one by one. Note the alert will fail unless you have verified your email. To verify your email, click on the user icon in the bottom left of the screen > profile > enter your email > click the link in your email. 

/// html | div[class="collapse-code"]
```sql
USE WAREHOUSE default_wh;
USE ROLE accountadmin;

CREATE OR REPLACE TASK tasty_bytes_dbt_db.raw.dbt_deps_task
	WAREHOUSE=TASTY_BYTES_DBT_WH
	SCHEDULE='60 MINUTES'
	AS EXECUTE DBT PROJECT "TASTY_BYTES_DBT_DB"."RAW"."DBT_PROJECT" args='deps --target dev';


CREATE OR REPLACE TASK tasty_bytes_dbt_db.raw.dbt_run_task
	WAREHOUSE=TASTY_BYTES_DBT_WH
	AFTER tasty_bytes_dbt_db.raw.dbt_deps_task
	AS EXECUTE DBT PROJECT "TASTY_BYTES_DBT_DB"."RAW"."DBT_PROJECT" args='run --target dev';


CREATE OR REPLACE TASK tasty_bytes_dbt_db.raw.dbt_test_task
	WAREHOUSE=TASTY_BYTES_DBT_WH
	AFTER tasty_bytes_dbt_db.raw.dbt_run_task
	AS
        DECLARE 
            dbt_success BOOLEAN;
            dbt_exception STRING;
            my_exception EXCEPTION (-20002, 'My exception text');
        BEGIN
            EXECUTE DBT PROJECT "TASTY_BYTES_DBT_DB"."RAW"."DBT_PROJECT" args='test --target dev';
            SELECT SUCCESS, EXCEPTION into :dbt_success, :dbt_exception FROM TABLE(result_scan(last_query_id()));
            IF (NOT :dbt_success) THEN
              raise my_exception;
            END IF;
        END;

-- Run the tasks once
ALTER TASK tasty_bytes_dbt_db.raw.dbt_run_task RESUME;
ALTER TASK tasty_bytes_dbt_db.raw.dbt_test_task RESUME;
EXECUTE TASK tasty_bytes_dbt_db.raw.dbt_deps_task;

-- Optionally create alerts from the task
-- NOTE: you must validate your email and replace it at the bottom of the alert
create or replace alert tasty_bytes_dbt_db.raw.dbt_alert
--- no warehouse selected to run serverless
schedule='60 MINUTES'          
if (exists (
    SELECT 
        NAME,
        SCHEMA_NAME
    FROM 
        TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
            SCHEDULED_TIME_RANGE_START => (greatest(timeadd('DAY', -7, current_timestamp),  SNOWFLAKE.ALERT.LAST_SUCCESSFUL_SCHEDULED_TIME())),
            SCHEDULED_TIME_RANGE_END => SNOWFLAKE.ALERT.SCHEDULED_TIME(),
            ERROR_ONLY => True)) 
    WHERE database_name = 'TASTY_BYTES_DBT_DB'
        )
    ) 
THEN          
    BEGIN
        LET TASK_NAMES string := (
            SELECT
                LISTAGG(DISTINCT(SCHEMA_NAME||'.'||NAME),', ') as FAILED_TASKS
            FROM 
                TABLE(RESULT_SCAN(SNOWFLAKE.ALERT.GET_CONDITION_QUERY_UUID()))); -- results of the condition query above
        CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(
            SNOWFLAKE.NOTIFICATION.TEXT_HTML(
                'Tasks '||:TASK_NAMES ||' failed since '||(greatest(timeadd('DAY', -7, current_timestamp), SNOWFLAKE.ALERT.LAST_SUCCESSFUL_SCHEDULED_TIME())
                    )
                ),
            SNOWFLAKE.NOTIFICATION.EMAIL_INTEGRATION_CONFIG(
                'DEMO_EMAIL_NOTIFICATIONS_DBT',                       -- email integration
                'Snowflake DEMO Pipeline Alert',                      -- email header
                array_construct('<YOUR EMAIL HERE>')      -- validated user email addresses
                )      
        );
    END;
;

-- Execute once
EXECUTE ALERT tasty_bytes_dbt_db.raw.dbt_alert;
```
///

You can view the status or running tasks by going to Monitoring > Task History.

![tasks](assets/tasks.png)

### Tracing

dbt projects in Snowflake integrate with [Tracing and Logging](https://docs.snowflake.com/en/developer-guide/logging-tracing/logging-tracing-overview), allowing you to easily monitor and debug dbt projects. Tracing follows the OpenTelemetry standard and allows you to keep logs within a single platform. 

To view tracing, go to Monitoring > Traces & Logs. Click on the most recent one which should be our failed dbt test. 

![tracing](assets/tracing-details.png)

### Cost Monitoring

Snowflake makes it easy to monitor usage across your account. To view consumption, go to Admin > Cost Management > Consumption Tab. Depending on your setup, you can create a dedicated warehouse to run dbt jobs to allow easy monitoring. 

Additionally, you are able to build [resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors) and alerts based on warehouse consumption. 

![cost-management](assets/cost-management.png)


<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files

### Related Resources
- <link to github code repo>
- <link to documentation>
