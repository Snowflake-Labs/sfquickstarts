author: Jacob Kranzler
id: tasty_bytes_zero_to_snowflake_data_governance
summary: Tasty Bytes - Zero to Snowflake - Data Governance Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Data Governance


# Tasty Bytes - Zero to Snowflake - Data Governance
<!-- ------------------------ -->

## Data Governance in Snowflake 
Duration: 1
<img src = "assets/data_governance_header.png">

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Data Governance!

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- A

### What You Will Build
- B

## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, Copying SQL from GitHub, and Pasting the SQL we will be leveraging within this Quickstart.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account 

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.
    - <img src ="assets/log_into_snowflake.gif" width = "300"/>

### Step 3 - Navigating to Worksheets
- Click on the Worksheets Tab in the left-hand navigation bar.
    - <img src ="assets/worksheet_tab.png" width="250"/>

### Step 4 - Creating a Worksheet
- Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet"
    - <img src = "assets/+_sqlworksheet.png" width ="200">

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Data Governance"
    - <img src ="assets/rename_worksheet_tasty_bytes_setup.gif"/>

### Step 6 - Accessing Quickstart SQL in GitHub
- Click the button below which will direct you to our Tasty Bytes SQL file that is hosted on GitHub.
<button>[tb_zts_data_governance.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/tasty_bytes_zero_to_snowflake_data_governance/assets/tb_zts_data_governance.sql)</button>

### Step 7 - Copying Setup SQL from GitHub
- Within GitHub navigate to the right side and click "Copy raw contents". This will copy all of the required SQL into your clipboard.
    - <img src ="assets/github_copy_raw_contents.png"/>

### Step 8 - Pasting Setup SQL from GitHub into your Snowflake Worksheet
- Path back to Snowsight and your newly created Worksheet and Paste (*CMD + V for Mac or CTRL + V for Windows*) what we just copied from GitHub.

### Step 9 - Click Next -->

##
Duration: 0

### Overview
Our Tasty Bytes Adminstrator has been tasked with learning the process of deploying Role Based Access Control (RBAC) and proper Data Governance across our Snowflake Account. 

To begin, let's first dive into the Snowflake System Defined Roles provided by default in all accounts and learn a bit more on their privileges.

### Step 1 - Setting our Context
Before we can begin executing queries within the Snowflake Snowsight interface we must first set our context by running [USE ROLE](https://docs.snowflake.com/en/sql-reference/sql/use-role) and [USE WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/use-warehouse) commands or manually setting these in the top-right corner.

For this step, we will do these by executing our first two queries by highlighting them both and clicking the "▶ Run" button. Once complete our results pane will result in a `Statement Executed Successfully` message.

```
USE ROLE accountadmin;
USE WAREHOUSE tasty_dev_wh;
```

Once the above queries are executed we can see in the top-right corner the exact role and warehouse we instructed Snowflake to use.

<img src = "assets/3.1.context.png">

With our context set, we can continue on our learning journey.

### Step 2 - Exploring All Roles in our Account
Now let's run the next query which leverages [SHOW ROLES](https://docs.snowflake.com/en/sql-reference/sql/show-roles) to provide a result set complete of all roles currently deployed in our account.

```
SHOW ROLES;
```

<img src = "assets/3.2.show_roles.png">

If you are operating in a trial account with only Tasty Bytes deployed your result set may match the above screenshot closely, however if you are using an existing Snowflake account your list may be more extensive. Thankfully we can filter down this result set which we will cover in the next step.

###  Step 3 - Using Result Scan to Filter our Result
To filter on just the Snowflake System Defined Roles from our previous output please execute the next query which utilizes [RESULT_SCAN](https://docs.snowflake.com/en/sql-reference/functions/result_scan) and [LAST_QUERY_ID](https://docs.snowflake.com/en/sql-reference/functions/last_query_id) to query our SHOW ROLES command as if it were a table with the ability to add a WHERE clause.

```
SELECT 
    "name",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "name" IN ('ORGADMIN','ACCOUNTADMIN','SYSADMIN','USERADMIN','SECURITYADMIN','PUBLIC');
```

<img src = "assets/3.3.result_scan.png">

In our result set we can see the high-level descriptions of what these Snowflake System Defined Roles have privileges to do. 

>aside positive
>**Note:** For additional details on these, please the [Snowflake System Defined Roles](https://docs.snowflake.com/en/user-guide/security-access-control-overview#system-defined-roles) documentation.
>

## Creating a Role and Granting Privileges
Duration: 0

### Overview
Now that we understand these System Defined roles, let's begin leveraging them to create a test role and grant it access to the Customer Loyalty data we will deploy our initial Data Governance features against and our `tasty_dev_wh` Warehouse.

### Step 1 - Using the Useradmin Role to Create our Test Role
As we saw, a `useradmin` can create and manage users and roles. Please kick off the next two queries with the first assuming that `useradmin` role and the second leveraging a CREATE ROLE command to generate a new `tasty_test_role` we will use throughout this Quickstart.

```
USE ROLE useradmin;

CREATE OR REPLACE ROLE tasty_test_role
    COMMENT = 'test role for tasty bytes';
```

<img src = "assets/4.1.create_role/png">

### Step 2 - 
### Overview

##
Duration: 0

### Overview

##
Duration: 0

### Overview

##
Duration: 0

### Overview

