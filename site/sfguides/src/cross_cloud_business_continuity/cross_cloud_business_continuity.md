author: Prateek Parashar, Vinay Srihari
id: cross_cloud_business_continuity
summary: This is a sample Snowflake Guide
categories: data-engineering,app-development,devops
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Cross Cloud Business Continuity With Snowflake
<!-- ------------------------ -->
## Overview

“By failing to prepare, you are preparing to fail” - Benjamin Franklin

A sound business continuity/disaster recovery plan is an important milestone for organizations looking to build resilient data platforms. Data-driven insights grow revenue, provide services, support customers and aid with critical decision making. Businesses face many forms of disruptions like fire, floods, cyberattacks, ransomware etc. These disruptions can spiral into various undesirable outcomes - from operational systems coming to a standstill leading to financial losses to something worse, like reputational damage.

Technology is the center-piece of all businesses and mission-critical data can never be unavailable. As businesses move critical applications to the public cloud, continuous global operations rely even more on cloud dependability.

Snowflake’s **Replication and Failover/Failback** feature enables account metadata, including everything from user identity and role-based access controls to governance policies, warehouses and resource monitors, to be automatically synchronized across clouds and regions for continuous availability. Multiple databases, shares and account metadata can be replicated as a unit, ensuring point-in-time consistency with the primary region.

Snowflake's **Client Redirect** feature facilitates seamless failover from primary to secondary so that apps and users can continue functioning without disruption. In the past, to recover, the connection string in every client application had to be manually changed to connect to the new primary site (the former secondary site) in a different region or cloud. With Client Redirect, administrators can use a single server-side command to redirect client applications to the new primary site, without disrupting business teams. 
 

### Prerequisites
- Create 2 Snowflake trial accounts in the same Organization - in AWS, Azure cloud regions - and enable replication for each account.
    > #### Create an AWS trial account [here](https://signup.snowflake.com/)
    >
    > - choose **Business Critical** edition, **AWS** as cloud provider, any **US** region
    > - activate account with username `snowgrid` - this user has ACCOUNTADMIN
    > - create a SQL Worksheet to setup an **Azure** account
    >
    > #### Create an Azure trial account from the AWS account (same Org)
    > ```sql
    > USE ROLE ORGADMIN;
    >
    > CREATE ACCOUNT snowflake_azure_target
    >   admin_name = snowgrid
    >   admin_password = 'FILL_IN_PASSWORD'
    >   email = 'FILL_IN_EMAIL'
    >   edition = business_critical
    >   region = azure_eastus2;
    > ```
    > #### Enable replication for AWS and Azure accounts (doc [here](https://docs.snowflake.com/en/user-guide/account-replication-config#prerequisite-enable-replication-for-accounts-in-the-organization))
    > ```sql
    > -- note the organization_name, account_name for AWS and Azure accounts
    > SHOW ORGANIZATION ACCOUNTS;
    >
    > SELECT SYSTEM$GLOBAL_ACCOUNT_SET_PARAMETER('FILL_ORG_NAME.FILL_AWS_ACCOUNT_NAME', 'ENABLE_ACCOUNT_DATABASE_REPLICATION', 'true'); 
    >
    > SELECT SYSTEM$GLOBAL_ACCOUNT_SET_PARAMETER('FILL_ORG_NAME.FILL_AZURE_ACCOUNT_NAME', 'ENABLE_ACCOUNT_DATABASE_REPLICATION', 'true'); 
    > ```
    > 
    > #### Verify that accounts are enabled for replication
    > ```sql
    > USE ROLE ACCOUNTADMIN;
    > SHOW REPLICATION ACCOUNTS;
    >```

- [Install SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html#installing-snowsql) (CLI Client): used to load data into a Snowflake internal stage 
- Check that SNOWFLAKE_SAMPLE_DATA shared database is visible, otherwise create it:
    >```sql
    > USE ROLE ACCOUNTADMIN;
    > CREATE DATABASE IF NOT EXISTS SNOWFLAKE_SAMPLE_DATA FROM SHARE SFC_SAMPLES.SAMPLE_DATA;
    > GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE_SAMPLE_DATA TO ROLE PUBLIC;
    >```

- (**Optional**) Python Streamlit Dashboard - install the following modules/connectors:
  - Install Python (3.8 or higher): `python --version`
  - [Install Snowflake Python connector](https://docs.snowflake.com/developer-guide/python-connector/python-connector-install#installing-the-python-connector)
  - [Install Streamlit](https://docs.streamlit.io/library/get-started/installation#install-streamlit-on-macoslinux), then a few components
    >```bash
    > pip install streamlit-echarts
    > pip install pandas
    > streamlit hello
    >```

- (**Optional**) Sigma BI Dashboard
  - [Sigma Free Trial](https://www.sigmacomputing.com/free-trial/) or launch the Sigma tile in Snowflake Partner Connect from your Snowsight UI

### What You’ll Learn 
In this quickstart you will learn
- How to use out of the box features available in Snowflake to build resiliency against region failures.
- Group based replication and failover of account objects.
- Database replication (as part of the group) from primary to secondary. 
- Account object replication (users, roles, WHs, resource monitors, data shares) from primary to secondary.
- How to keep a DR instance ready to serve as exact replica of the primary instance - with upto date data and governance policies.
- How to trigger failover of replication/failover groups and client connections.

### What You’ll Need 

- Python installed on local machine to stimulate a python app failover (Needed for streamlit app).
- A Sigma trial account to stimulate a BI dashboard failover (Needed for Sigma BI app). 

### What You’ll Build 
- Source account resources to mimic a production grade Snowflake account.
- Replicate/Failover selective resources to a secondary account in a transactionally consistent fashion.
- Build apps powered by primary snowflake account.
- Failover from primary to secondary account.
- Observe your apps now seamlessly powered by the secondary account.

<!-- ------------------------ -->
## Primary Account Setup (AWS)

Download ZIP or Clone [sfguide_failover_scripts](https://github.com/Snowflake-Labs/sfguide_failover_scripts) Github repo to your local machine

![Code Button](assets/code-download.png)

To match provided scripts, copy `data` and `scripts` directories to `/tmp` 
```bash
cd sfguide_failover_scripts-main
cp -r data /tmp
cp -r scripts /tmp
```

### Run SQL scripts 100-600 in sequential order on the AWS Primary account

[Create Snowsight Worksheets from SQL File](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-in-sf-web-interface) - use one worksheet per SQL script

![Create Worksheet](assets/create-worksheets.png)


1. `100_create_replication_objects.sql`: create roles, databases, warehouses, resource monitors
2. `200_create_users_source.sql`: create users with basic password authentication
3. `300_grant_privileges.sql`: grant object and account level privileges
4. `400_load_data.sql`: create and load tables, views, functions, stored procedures, shares
5. `500_add_governance_policies.sql`: assign tags, masking and row access policies
6. `600_update_primary_task.sql`: setup task to update primary tables every few mins


### Ingest Payroll Data
Load data file `data/hr_data_sample.csv` into table `PAYROLL.NOAM_NORTHEAST.EMPLOYEE_DETAIL` with the Snowsight UI interface.

![load_payroll_1](assets/load-data-payroll.png)

Browse to find the `data/hr_data_sample.csv` file and set the CSV format correctly

![load_payroll_2](assets/load-data-format.png)

You should have successfully loaded `100 records`

![load_payroll_3](assets/load-data-success.png)

### Create ELT Pipeline using the [TPC-DI](https://www.tpc.org/tpcdi/) benchmark schema
This modified TPC-DI benchmark flow simulates the process of extracting data from operational (OLTP) systems in a variety of data formats, loading into a set of staging tables, then transforming into a unified model for analytical reporting and insights.

We will observe how Snowflake's pipeline replication features (in Public Preview) support seamless failover and idempotent restart of the pipeline on the new primary.

7. `700_setup_tpcdi_pipeline.sql`: create external stage, internal stage w/directory table, create staging tables and batch load plan, use dynamic table DAG to build a declarative pipeline from staging to warehouse.

    *Stop after creating the internal stage here, run Step 8, then continue*

    ![switch-to-step8](assets/switch-to-step-8.png)

8. Use SnowSQL CLI to load batches from `data/tpcdi-scale5` and `data/tpcdi-scale10` to **internal stage**

    Run in a Terminal window (after installing SnowSQL): this script assumes file locations are `/tmp/data` and `/tmp/scripts`, modify appropriately.
```bash
% snowsql -a ORGNAME-ACCOUNTNAME -u snowgrid -f /tmp/scripts/snowsql/tpcdi_load.sql -o output_format=csv -o output_file=output_file.csv
```

9. `800_execute_pipeline.sql`: call batch load procedure that simulates an ingest pipeline

<!-- ------------------------ -->
## Review Source Account

Our scripts in the previous step have created a production like snowflake environment for us. Here's a list of objects you just created when you ran those scripts:
- Users & Roles
- RBAC Hierarchy
- Databases
- Compute warehouses
- Data copied from the snowflake_sample_data share
- Direct data shares
- Dynamic data masking policies
- Row access policy
- Object tags

Phew! That's quite a list here's what all of this looks like in a picture:

![snowflake_source_account](assets/source_account_snapshot.png)

### Let's review our source account

#### Observe your RBAC
Below is what the roles hierarchy should look like in your source account. Do note that the roles hierarchy is only available via the new UI - Snowsight. Log on to Snowsight and assume the "securityadmin" role and then navigate to home -> admin -> users & roles -> roles.

![snowsight_screenshot](assets/snowsight_screenshot.png)

#### Verify Row Access Policy
Our row access policy is applied to the global_sales.online_retail.customer table with the following rules:

- sales_analyst role should be able to see data for market segments 'automobile' and 'machinery'.
- sales_admin role should be able to see data for market segments 'automobile', 'machinery', 'building' and 'household'.
- product_manager role should be able to see data for ALL market segments.
- All other roles should not be able to see data for ANY market segment.

Below query when run with the sysadmin role should return 0 records, but when run with the sales_analyst, sales_admin or product_manaher role it should return results based on their privilege described above. Run the query once with each role - sysadmin, sales_analyst, sales_admin and product_manager and verify whether these rules are being adhered. Switch roles in your worksheet with the "use role <role_name>" command.

```sql
use role sysadmin;
use warehouse sales_wh;
select * from global_sales.online_retail.customer limit 100;
```

When we replicate our data and our account objects, row level security is applied to the target account as well. This ensures that your access rules around data are retained even on the DR instance.

#### Verify dynamic data masking policy
Our payroll.noam_northeast.employee_detail data contains critical PII data elements such as salary, ssn, email and iban. This is information that cannot be visible by everyone that has access to this data. We therefore deploy dynamic data masking policy protecting this dataset and only allowing authorized roles to see this information in the clear. The remaining roles would either see partially masked or completely redacted version of these columns, while having full visibility on other columns in this dataset that they can still use. Below are the rules of our dynamic data masking policy.

- email_address: hr_admin and product_manager roles can see complete email ids while all the other roles would see partially masked values, with only the domain name (@gmail.com, @yahoo.com) being visible.
- iban, credits_card and ssn: hr_admin and product_manager see ibans in the clear, all the other roles would see fully masked values.
- salary: hr_admin and product_manager see actual salaries and all the other roles would see 0.0

Run the query below with two different roles - hr_analyst and hr_admin, observe all fields in the return results. What values does hr_analyst see for email, iban, cc and salary columns? What values does the hr_admin see?

```sql
use role hr_analyst;
use warehouse hr_wh;
select * from payroll.noam_northeast.employee_detail limit 100;
```

#### Verify data shares
We've created a few data shares with different variations, we'll observe what permissions each of these shares have and whether these are replicated as is to our secondary account.

Below code snippet displays permissions on three data shares - GLOBAL_SALES_SHARE, INVENTORY_SHARE and CROSS_DATABASE_SHARE

```sql 
use role accountadmin;
show grants to share global_sales_share;
show grants to share inventory_share;
show grants to share cross_database_share;
```

- GLOBAL_SALES_SHARE should have
  - usage on global_sales DB
  - usage on global_sales.online_retail schema
  - select on customer, lineitem and nation tables in global_sales.online_retail schema

- INVENTORY_SHARE should have 
  - usage on products DB
  - reference_usage on references DB
  - usage on internal and public schema in the products DB
  - usage on products.internal.item_quantity() table function

- CROSS_DATABASE_SHARE should have 
  - usage on cross_database DB
  - reference_usage on references and sales DB
  - usage on cross_database.public schema
  - usage on cross_database.public.morning_sales view

#### Verify location, type and owner of governance policies
We have built 6 masking policies, 4 object tags and 2 row access policies that we use to protect our data. Observe their details like which schema are these policies kept in, who owns them etc.

```sql
use role governance_admin;
show masking policies;
show row access policies;
show tags;
```
The output of the three commands should look something like this:

__Masking Policies:__
![masking_policy](assets/masking_policy_loc_latest.png)

__Row Access Policy:__
![row_access_policy](assets/row_access_policy_loc_latest.png)

__Object Tags:__
![object_tags](assets/object_tag_loc_latest.png)


<!-- ------------------------ -->
## Configure Primary(AWS) and Secondary(Azure) for Business Continuity
Now that our Primary AWS account has been populated with users, database objects, governance policies, account metadata and data tranformation pipelines - we are ready to configure our Azure account as a Secondary target.

Snowflake BCDR is simple to setup, maintain and test. The key capabilities are [**Replication with Failover**](https://docs.snowflake.com/en/user-guide/replication-intro#replication-and-failover-failback) and [**Client Redirect**](https://docs.snowflake.com/en/user-guide/client-redirect), available only with Business Critical edition (or higher).

We will create these two first-class Snowflake objects that deliver business continuity:
- **Connection:** a connection object provides a *secure connection URL* for any Snowflake client to connect to an account and to be redirected to another account.
- **Failover Group:**  a defined collection of objects in a source account that are replicated as a unit to one or more target accounts and can failover. A secondary failover group in a target account provides read-only access for the replicated objects. When a secondary failover group is promoted to become the primary failover group, read-write access is available.

#### Run in a SQL worksheet named *BCDR Configuration* on the `Primary(AWS)`
```sql
use role accountadmin;
show replication accounts;
```

#### Substitute `organization_name`, `source account_name` and `target account_name` in these commands to create connection and failover group objects:

```sql
use role accountadmin;

create connection prodsnowgrid;
alter connection prodsnowgrid 
    enable failover to accounts <organization_name.target_account_name>;

show connections;

create failover group sales_payroll_failover
    object_types = users, roles, warehouses, resource monitors, databases, shares
    allowed_databases = global_sales,common,payroll,inventory,loyalty,sales,crm,products,references,cross_database,externals
    allowed_shares = global_sales_share,sales_history_share, cross_database_share, crm_share, inventory_share
    allowed_integration_types = storage integrations
    allowed_accounts = <organization_name.target_account_name>;
```

#### Run in a SQL worksheet named *BCDR Configuration* on the `Secondary(Azure)`
Here you'll create a secondary connection and a secondary failover group.

- A secondary connection is linked to the primary connection and must be created in an account in a different region from the source account. The secondary connection name must be the same as the primary connection name.
- Just like the secondary connection, a secondary failover group is also linked to it's corresponding primary failover group and must be created in an account in a different region from the source account and with the same name as the primary failover group.

Substitue value of orgname and source_account_name (as noted above) in the commands below

```sql
use role accountadmin;
create connection sfsummitfailover
    as replica of <organame.source_account_name.SFSUMMITFAILOVER>;

create failover group SALES_PAYROLL_FAILOVER
    as replica of <organame.source_account_name.SALES_PAYROLL_FAILOVER>;
```

#### Note the value for connection_url
Once you've setup your connection object successfully, we need to note the value for connection_url for our connection object. This URL is what we'll be using in all our application building from this point on. The url takes an account agnostic form (_orgname-connection_name.snowflakecomputing.com_) because it could be pointing to either account depending upon which one is primary. 

```sql
#Fire command below and for the connection object created note the value of 
#connection_url_ property. It is the 3rd last column in the result of the 
# show connections command.
show connections;
```

<!-- ------------------------ -->
## Build BI and/or Streamlit Apps
Duration: 2

Welcome app developers! this is where we have some fun, all of the hard work thus far with account setup, data curation, RBAC hierarchy and governance policy would be of no use if we're not powering apps that provide meaningful insights. It is after all these insightful apps that we want operational in case of an outage. 

We have two options for you today to build quick and simple, snowflake powered apps that we'll see later, will continue to be operational (By failing over to the DR) once we simulate a region failure.

You can choose to build one of both of these.

- Option 1: For BI enthusiasts (Now is when that Sigma trial account will come in handy) - You'll be building a Sigma dashboard. Step by step instructions are available in the video below.

- Option 2: For the pythonistas in the house - you'll be playing with some streamlit and streamlit extensions magic (hopefully, it's already installed on your local machines. If not, don't stress - pip install streamlit & pips install streamlit-echarts is all you need). If you have the required libraries installed, you can leverage the code below - enter your credentials to your Snowflake account and run the streamlit app. 

- Option3: If you're not in the mood to build, no problem. There's an easy (and unfotrunately boring) way to test this too. You can stick with the good ole snowflake UI or Snowflake's CLI tool - snowsql to connect to the url mentioned in the connection_url field and see which account did snowflake route you to?

### Sigma BI Dashboard

In this step, we'll build a sigma dashboard that will rely on data available on our primary account. Once we replicate this data to our secondary account and failover, we'll see the sigma dashboard seamlessly point to the failover region and powered by our secondary account.

In the video, you will see we connect Sigma to Snowflake by creating a connection. When filling up the connection details ensure that account name is same as the value recorded for "connection_url" at the end of step 4.

<video id="vfmmDcQ1uB0"></video>

#### Query used to build the global sales dashboard
Here's the code snippet used for charting the global revenue figures. 
```bash
select n_name nation
    , sum(o_totalprice) revenue
from global_sales.online_retail.orders 
inner join global_sales.online_retail.customer on c_custkey = o_custkey
inner join global_sales.online_retail.nation on c_nationkey = n_nationkey
where o_orderdate between dateadd(day,-2,current_date) and current_date()
group by 1
order by 2 desc
```

#### Final Dashboard
Once you're done building the dashboard, the end result should look something like this
![sigma_dashboard](assets/sigma_dashboard_image.png)


### Python Streamlit App
Save the code below in a python file and run it with the command "streamlit run <your-python-filename.py>". Remember to substitute user_name, password and account_name (in the ctx object) for your account before running the script. The account_name should be same as the value recorded for "connection_url" at the end of step 4, you only need to include everything before ".snowflakecomputing.com".

```python
#Save this python script in a file and run from terminal/command prompt as 'streamlit run <name_of_script>.py'
import snowflake.connector
import streamlit as st
import pandas as pd
import streamlit_echarts as ste
import json

# Snowflake connection details
ctx = snowflake.connector.connect(
    user=<user_name>,
    password=<password>,
    #account name value should be that of connection_url from the show connections command. Everything before snowflakecomputing.com
    account=<account_name>,
    session_parameters={
        'QUERY_TAG': 'Snowflake Summit 2022: Failover HoL'
    },
    warehouse='bi_reporting_wh',
    database='global_sales',
    role='product_manager'
    )

# Create a cursor object
cur = ctx.cursor()

#Query to power streamlit app
app_sql = """
select round(sum(o_totalprice)/1000,2) as value,
       lower(c_mktsegment) as name
       from
       global_sales.online_retail.orders
       inner join global_sales.online_retail.customer
       on c_custkey = o_custkey
       where o_orderdate between dateadd(day,-4,current_date) and current_date()
       group by 2
       order by 1 desc;
"""
#Query to get account name.
get_account_sql = "select current_account() as account_name;"

#Query to get region name.
get_region_sql = "select current_region() as region_name;"

#Query to get total sales transactions.
trans_count_sql = "select count(*) as transaction_count from sales..total_sales;"

#Query to get median qty.
median_qty_sql = "select median(quantity) as median_qty from sales..total_sales;"

#Query to get Last Update.
last_update_sql = "select max(last_update_time) as last_update from sales..total_sales;"

#Get Query results to power the main viz.
cur.execute(app_sql)
df = cur.fetch_pandas_all()

#Get account name.
cur.execute(get_account_sql)
account_name_json = cur.fetch_pandas_all().to_json(orient = 'records')
account_name = json.loads(account_name_json)[0]['ACCOUNT_NAME']

#Get region name.
cur.execute(get_region_sql)
region_name_json = cur.fetch_pandas_all().to_json(orient = 'records')
region_name = json.loads(region_name_json)[0]['REGION_NAME']

#Get total transactions.
cur.execute(trans_count_sql)
trans_count_json = cur.fetch_pandas_all().to_json(orient = 'records')
trans_count = json.loads(trans_count_json)[0]['TRANSACTION_COUNT']

#Get median qty.
cur.execute(median_qty_sql)
median_qty_json = cur.fetch_pandas_all().to_json(orient = 'records')
median_qty = json.loads(median_qty_json)[0]['MEDIAN_QTY']

#Get last update timestamp.
cur.execute(last_update_sql)
last_update_json = cur.fetch_pandas_all().to_json(orient = 'records')
last_update = json.loads(last_update_json)[0]['LAST_UPDATE']

#Adjust column case for our data frame to work well with streamlit extensions.
df_col_case = df.rename(columns = {'VALUE':'value','NAME':'name'})
df_chart_data = df_col_case.to_json(orient = 'records')
df_chart_data = json.loads(df_chart_data);

#Streamlit Extensions Pie chart visualization config.
options = {
    "tooltip": {"trigger": "item"},
    "legend": {"top": "5%", "left": "center"},
    "series": [
        {
            "name": "Revenue By Market Segment",
            "type": "pie",
            "radius": ["40%", "70%"],
            "avoidLabelOverlap": False,
            "itemStyle": {
                "borderRadius": 15,
                "borderColor": "#fff",
                "borderWidth": 7,
            },
            "label": {"show": False, "position": "center"},
            "emphasis": {
                "label": {"show": True, "fontSize": "40", "fontWeight": "bold"}
            },
            "labelLine": {"show": False},
            "data": df_chart_data,
        }
    ],
}

#st.sidebar.title("Real Time Sales Insight")
#original_title = '<p style="font-family:Courier; color:Blue; font-size: 20px;">Transaction Count</p>'
title_template = '<p style="color:Grey; font-size: 15px;">'
value_template = '<p style="color:Black; font-size: 25px;">'

account_title = title_template + 'Account Name:</p>'
region_title = title_template + 'Region Name:</p>'
transaction_title = title_template + 'Transaction Count:</p>'
median_title = title_template + 'Median Qty:</p>'
update_title = title_template + 'Last Updated Time:</p>'

account_value = value_template + account_name + '</p>'
region_value = value_template + region_name + '</p>'
transaction_value = value_template + str(trans_count) + '</p>'
median_value = value_template + str(median_qty) + '</p>'
update_time_value = value_template + str(last_update) + '</p>'

st.sidebar.markdown(account_title,unsafe_allow_html=True)
st.sidebar.markdown(account_value,unsafe_allow_html=True)
st.sidebar.markdown("***")
st.sidebar.markdown(region_title,unsafe_allow_html=True)
st.sidebar.markdown(region_value,unsafe_allow_html=True)
st.sidebar.markdown("***")
st.sidebar.markdown(transaction_title,unsafe_allow_html=True)
st.sidebar.markdown(transaction_value,unsafe_allow_html=True)
st.sidebar.markdown("***")
st.sidebar.markdown(median_title,unsafe_allow_html=True)
st.sidebar.markdown(median_value,unsafe_allow_html=True)
st.sidebar.markdown("***")
st.sidebar.markdown(update_title,unsafe_allow_html=True)
st.sidebar.markdown(update_time_value,unsafe_allow_html=True)

overview_text = """
This dashboard will help demonstrate revenue share per market segment
as of yesterday. It is additionally highlighting information about the
Snowflake deployment that is powering the pie-chart visualization,
observe the name and region of your snowflake account. We will now
stimulate a failover scenario by promoting our secondary account to
primary and observe seamless failover while our ever so important data
apps such as this continue to be powered by Snowflake, not just on a
completely new region but also on a different cloud provider as well.
"""
conclusion_text = """
Congratulations, on achieving cross-cloud cross-region
replication in a matter of minutes. Remember, what happens in vegas doesn't
necessarily need to stay in Vegas. Now go out, share this useful spear of
knowledge that you now have in your quiver and go make your org resilient
to region failures.
"""
st.button("Refresh")
st.title("Snowflake + Streamlit")
st.header("Overview")
st.text(overview_text)

st.header("Revenue By Market Segment")
ste.st_echarts(
    options=options, height="500px"
)
st.header("Conclusion")
st.text(conclusion_text)
st.snow()
```

#### Streamlit app should look like this

![streamlit_ss](assets/streamlit_dashboard.png)

<!-- ------------------------ -->
## Replication To Target
All that work behind us, we set up our account resources like users, roles, RBAC hierarchy, databases (not to mention, the crucial data it contains), compute warehouses, governance policies with RLS and CLS features, direct shares and then some beautiful customer facing apps - Phew!

Now we have to do this all over again just to have a DR instance - how much more work will this be?? Oh right, negligible. With Snowflake a single command will bring all that setup from our source account to our target account in a matter of minutes if not seconds (depending upon the size/number of objects).

But wait a minute, our source account and target account are on _different_ public cloud providers - won't that factor into the setup or cause some kind of _extra work_? Nope, not with Snowflake - we're cloud agnostic and we hide all that complexity from you.  

#### Replicate to Secondary
Run the command below on your **target/secondary account** to begin replication

```bash
use role accountadmin;
alter failover group sales_payroll_failover refresh;
```

#### Did the replication fail?
Why do you think the first attempt to replication fail? Notice that there's an externals db that contains an external table which is not supported for replication and is the reason why replication failed.

Let's fix this by removing the externals db from our failover group. Run the below command on the **primary account**.

```sql
use role accountadmin;
alter failover group sales_payroll_failover remove externals from allowed_databases;
```

Now lets re-reun our replication, it should succeed this time. Run the below command on the **secondary account**.

```bash
use role accountadmin;
alter failover group sales_payroll_failover refresh;
```

This command would take about a minute to run , but wait where's it getting the compute from? is it using any of our WHs that we've provisioned? Nope, we got you covered - this is serverless compute that Snowflake provides and autoscales depending upon the amound of work that needs to get done. There will be a separate lineitem under "Replication" for this on your bill.

After this command has run - you should all of the databases and other objects that we included in the failover group definition available in your secondary account.

#### Verify Replication
In order to ensure that replication worked, go back to step 3 and run all commands under "Lets review our source account" on _your target account_ and ensure that you see the exact same results as you did on your source account. This will confirm that our replication worked as expected.

#### Replicate on a schedule
With the initial replication successfully completed, we want to now replicate on a schedule so that any additional changes on the primary account are regularly made available to the secondary. Let's assume a strict RPO and replicate every 3 minutes. It is important to note that if there are no changes to primary, nothing will be replicated to secondary and there will be no replication cost incurred. Run the command below (on the **primary account**) to replicate our group evey three minutes.

```sql
use role accountadmin;
alter failover group sales_payroll_failover set replication_schedule = '3 MINUTES';
```


<!-- ------------------------ -->
## Failover To Target
Moment of truth! With our data and account objects safely replicated to the secondary account. Let's assume disaster has struck! Our primary account is experiencing outage and business and tech teams (The awesome failover HoL participants) have invested time and money in ensuring that they are prepared for this very event.

So what do we do? Again, something very simple - fire two commands.

- The first command will failover our connection - making the secondary account the new primary account for account redirect. Meaning the url in the connection_url property of our connection object will start to point to the new primary account. 
- The second command will do the same for our failover group, it has made the other account primary for objects covered in the failover group. This means that databases within this FG have now become read-write and the same databases in our new secondary (old primary) account have become read-only.

Run the two commands below on the **secondary account**


```bash
use role accountadmin;

alter connection sfsummitfailover primary;
alter failover group sales_payroll_failover primary;
```

#### Run sales updates on the new primary account
Now that we have a new primary account, let's re-create the task (remember that tasks are not replicated) from our 600 script to update the sales table every 3 minutes

```sql
use role sysadmin;
#Important to note that IT_WH is available as part of the failover group that was replicated.
use warehouse it_wh;

CREATE OR REPLACE TASK REFERENCES..UPDATESALES
    WAREHOUSE = etl_wh
    SCHEDULE = '3 minute'
AS
    CALL sales..update_sales();

use role accountadmin;
grant execute task on account to role sysadmin;
use role sysadmin;
ALTER TASK REFERENCES..UPDATESALES RESUME;
```

<!-- ------------------------ -->
## Let's Revisit Our Apps
With your connection_url now pointing to a new primary account, refresh your BI Dashboards and/or Streamlit Apps and notice which accounts are they powered by? But let's not blindly believe the visualizations! Login to the new primary account and look at the query history. Were the queries behind the Viz indeed fired on your new primary account? They should very well be!  


<!-- ------------------------ -->
## Conclusion
Duration: 1

In this lab we have seen advantages of having a BC/DR strategy ensuring the data apps (that power the world) are resilient to region failures. 

We utilized Snowflake's shiny new group based replication to replicate not just our databases but other critical account resources like users, roles (and the privileges), data shares, warehouses, resource monitors.

We also noticed that the data governance rules that keep our data secured on the source account, are retained on the target account. Masking policies, row access policies and object tags are replicated along with the database and applied on the target account. Thereby ensuring that in the event of a region failure you're not tasked with re-applying governance rules on your new primary.

We've worked through the following tasks:

- Setup source account resources needed to mimic a prod like environment.
- Understood the new group based replication and client re-direct. 
- Configured failover group and connection on primary and created clones of these objects in the secondary.
- Built _slightly_ fancy apps in Sigma and Streamlit.
- Replicated all resources configured in the failover group to the secondary account (_ahem, at lightning speed, ahem_)
- Finally, we simulated a DR scenario simply by promoting our secondary account to be the new primary account and observed that our applications continued to function seamlessly.