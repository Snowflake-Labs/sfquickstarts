author: Jacob Kranzler
id: tasty_bytes_zero_to_snowflake_financial_governance
summary: Tasty Bytes - Zero to Snowflake - Financial Governance Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Data Warehouse

# Tasty Bytes - Zero to Snowflake - Financial Governance
<!-- ------------------------ -->

## Financial Governance in Snowflake
Duration: 1
<img src = "assets/financial_governance_header.png">

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Financial Governance!

Within this Quickstart, we will learn about Financial Governance in Snowflake by diving into Snowflake Warehouses and their configurabilities, Resource Monitors, and Account and Warehouse Level Timeout Parameters.

For more detail on Financial Governance in Snowflake please visit the [Financial Governance Overview documentation](https://docs.snowflake.com/guides-overview-cost#financial-governance-overview).

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- How to Create and Configure a Snowflake Warehouse
- How to Scale a Snowflake Warehouse Up and Down
- How to Suspend a Snowflake Warehouse
- How to Create, Configure and Apply a Resource Monitor
- How to set Query Timeout and Queue Timeout Parameters on a Snowflake Warehouse and Snowflake Account.

### What You Will Build
- A Snowflake Warehouse
- A Resource Monitor

## Creating a Worksheet and Copying in our SQL
Duration: 0
Within this Quickstart we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

## Creating a Warehouse 
Duration: 0

#### Overview
As a Tasty Bytes Snowflake Administrator we have been tasked with gaining an understanding of the features Snowflake provides to help ensure proper Financial Governance is in place before we begin querying and analyzing data.

#### Step 1 - Role and Warehouse Context
Before we create a Warehouse, let's first set our Role and Warehouse context. 

The queries below will assume the role of `tasty_admin` via [USE ROLE](https://docs.snowflake.com/en/sql-reference/sql/use-role.html) and leverage the `tasty_de_wh` warehouse via [USE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/use-warehouse.html). 
- To run the queries, please highlight the two queries in your created Worksheet that match what you see below and click the "► Run" button in the top-right hand corner. 
- Once these are executed you will a `Statement executed successfully.` result and notice the Worksheet context reflect the Role and Warehouse as shown in the screenshot below.
```
USE ROLE tasty_admin;
USE WAREHOUSE tasty_de_wh;
```
<img src = "assets/3.1.use_role_and_wh.png"> 

#### Step 2 - Creating and Configuring a Warehouse
Within Snowflake, Warehouses are highly configurable to meet your compute demands. This can range from scaling up and down to meet compute needs or scaling out to meet concurrency needs. 

The next query which will create our first Warehouse named `tasty_test_wh`. Please execute this query now which result in another `Statement executed successfully.` message.
```
CREATE OR REPLACE WAREHOUSE tasty_test_wh WITH
COMMENT = 'test warehouse for tasty bytes'
    WAREHOUSE_TYPE = 'standard'
    WAREHOUSE_SIZE = 'xsmall' 
    MIN_CLUSTER_COUNT = 1 
    MAX_CLUSTER_COUNT = 2 
    SCALING_POLICY = 'standard'
    AUTO_SUSPEND = 60
    AUTO_RESUME = true
    INITIALLY_SUSPENDED = true;
```

Based on the query we ran, please see the details below on what each configuration handles within our [CREATE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse) statement and when ready move on to the next section.
> aside positive
>**Warehouse Type**: Warehouses are required for queries, as well as all DML operations, including loading data into tables. Snowflake supports Standard (most-common) or Snowpark-optimized Warehouse Types.
>
>**Warehouse Size**: Size specifies the amount of compute resources available per cluster in a warehouse. Snowflake supports X-Small through 6X-Large sizes.
>
>**Minimum and Maximum Cluster Count**: With multi-cluster warehouses, Snowflake supports allocating, either statically or dynamically, additional clusters to make a larger pool of compute resources available. 
>
>**Scaling Policy**: Specifies the policy for automatically starting and shutting down clusters in a multi-cluster warehouse running in Auto-scale mode.
>
> **Auto Suspend**: By default, Auto-Suspend is enabled. Snowflake automatically suspends the warehouse if it is inactive for the specified period of time, in our case 60 seconds.
>
>**Auto Resume**: By default, auto-resume is enabled. Snowflake automatically resumes the warehouse when any statement that requires a warehouse is submitted and the warehouse is the current warehouse for the session.
>
>**Initially Suspended**: Specifies whether the warehouse is created initially in the ‘Suspended’ state.
> 
> 
> *For further information on Snowflake Warehouses please visit the* [*Snowflake Warehouse Documentation*](https://docs.snowflake.com/en/user-guide/warehouses)
>

## Creating a Resource Monitor and Applying it to our Warehouse
Duration: 0

#### Overview
With a Warehouse in place, let's now leverage Snowflakes Resource Monitors to ensure the Warehouse has a monthly quota that will allow our admins to track it's consumed credits and ensure it is suspended if it exceeds its assigned quota.

#### Step 1 - Creating a Resource Monitor
A resource monitor can be used to monitor credit usage by virtual warehouses and the cloud services needed to support those warehouses. If desired, the warehouse can be suspended when it reaches a credit limit. The number of credits consumed depends on the size of the warehouse and how long it runs.

```
USE ROLE accountadmin;
CREATE OR REPLACE RESOURCE MONITOR tasty_test_rm
WITH 
    CREDIT_QUOTA = 100 -- 100 credits
    FREQUENCY = monthly -- reset the monitor monthly
    START_TIMESTAMP = immediately -- begin tracking immediately
    TRIGGERS 
        ON 75 PERCENT DO NOTIFY -- notify accountadmins at 75%
        ON 100 PERCENT DO SUSPEND -- suspend warehouse at 100 percent, let queries finish
        ON 110 PERCENT DO SUSPEND_IMMEDIATE;
```
<img src = "assets/3.1.use_role_and_wh.png"> 

> aside positive
> **Credit Quota**: Credit quota specifies the number of Snowflake credits allocated to the monitor for the specified frequency interval. Any number can be specified.
>
> **Frequency**: The interval at which the used credits reset relative to the specified start date.
>
> **Start Timestamp**: Date and time (i.e. timestamp) when the resource monitor starts monitoring the assigned warehouses.
>
> **Notify**: Perform no action, but send an alert notification (to all account administrators with notifications enabled).
>
> **Notify & Suspend**: Send a notification (to all account administrators with notifications enabled) and suspend all assigned warehouses after all statements being executed by the warehouse(s) have completed.
>
> **Notify & Suspend Immediate**: Send a notification (to all account administrators with notifications enabled) and suspend all assigned warehouses immediately, which cancels any statements being executed by the warehouses at the time.
>
> *For further information on Snowflake Warehouses please visit the* [Working with Resource Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)


#### Step 2 - Applying our Resource Monitor to our Warehouse

`Statement executed successfully.` result.

```
ALTER WAREHOUSE tasty_test_wh SET RESOURCE_MONITOR = tasty_test_rm;
```


## Protecting our Warehouse from Long Running Queries
Duration: 0

## Protecting our Account from Long Running Queries
Duration: 0

## Leveraging, Scaling and Suspending our Warehouse
Duration: 0

## Resetting our Account
Duration: 0
