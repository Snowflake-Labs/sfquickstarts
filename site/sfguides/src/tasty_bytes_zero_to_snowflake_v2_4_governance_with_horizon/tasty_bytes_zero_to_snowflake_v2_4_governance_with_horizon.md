author: Cameron Shimmin
id: tasty_bytes_governance_with_horizon
summary: Tasty Bytes - Zero to Snowflake - Governance with Horizon Quickstart
categories: Tasty-Bytes, Getting-Started, Featured
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Tasty Bytes, Zero to Snowflake, Governance, Horizon, Data Security, RBAC, Masking, Data Quality

# Tasty Bytes - Zero To Snowflake - Governance with Horizon
## Data Governance with Snowflake Horizon
Duration: 1
<!-- <img src = "assets/governance_header.png"> -->

### Overview
Welcome to the Powered by Tasty Bytes - Zero to Snowflake Quickstart focused on Data Governance with Snowflake Horizon!

Within this Quickstart, we will explore some of the powerful governance features within Snowflake Horizon. We will begin with a look at Role-Based Access Control (RBAC), before diving into features like automated data classification, tag-based masking policies for column-level security, row-access policies, data quality monitoring, and finally, account-wide security monitoring with the Trust Center.

### Prerequisites
- Before beginning, please make sure you have completed the [**Introduction to Tasty Bytes Quickstart**](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html) which provides a walkthrough on setting up a trial account and deploying the Tasty Bytes Foundation required to complete this Quickstart.

### What You Will Learn
- The fundamentals of Role-Based Access Control (RBAC) in Snowflake.
- How to automatically classify and tag sensitive data.
- How to implement column-level security with Dynamic Data Masking.
- How to implement row-level security with Row Access Policies.
- How to monitor data quality with Data Metric Functions.
- How to monitor account security with the Trust Center.

### What You Will Build
- A custom, privileged role.
- A data classification profile for auto-tagging PII.
- Tag-based masking policies for string and date columns.
- A row access policy to restrict data visibility by country.
- A custom Data Metric Function to check data integrity.


## Creating a Worksheet and Copying in our SQL
Duration: 1

### Overview
Within this Quickstart, we will follow a Tasty Bytes themed story via a Snowsight SQL Worksheet with this page serving as a side by side guide complete with additional commentary, images and documentation links.

This section will walk you through logging into Snowflake, Creating a New Worksheet, Renaming the Worksheet, and Pasting the SQL we will be leveraging within this Quickstart.

### Step 1 - Accessing Snowflake via URL
- Open a browser window and enter the URL of your Snowflake Account.

### Step 2 - Logging into Snowflake
- Log into your Snowflake account.

### Step 3 - Navigating to Worksheets
- Click on the **Projects** Tab in the left-hand navigation bar and click **Worksheets**.

### Step 4 - Creating a Worksheet
- Within Worksheets, click the **"+"** button in the top-right corner of Snowsight.

### Step 5 - Renaming a Worksheet
- Rename the Worksheet by clicking on the auto-generated Timestamp name and inputting "Tasty Bytes - Governance".

### Step 6 - Pasting SQL into your Snowflake Worksheet
- Copy the entire SQL block below and paste it into your worksheet.

```sql
/*************************************************************************************************** Asset:        Zero to Snowflake v2 - Governance with Horizon
Version:      v1     
Copyright(c): 2025 Snowflake Inc. All rights reserved.
****************************************************************************************************/

ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"tb_101_v2","version":{"major":1, "minor":1},"attributes":{"is_quickstart":0, "source":"tastybytes", "vignette": "governance_with_horizon"}}';

USE ROLE useradmin;
USE DATABASE tb_101;
USE WAREHOUSE tb_dev_wh;

/* 1. Introduction to Roles and Access Control */
SHOW ROLES;

CREATE OR REPLACE ROLE tb_data_steward
    COMMENT = 'Custom Role';
    
USE ROLE securityadmin;
GRANT OPERATE, USAGE ON WAREHOUSE tb_dev_wh TO ROLE tb_data_steward;

GRANT USAGE ON DATABASE tb_101 TO ROLE tb_data_steward;
GRANT USAGE ON ALL SCHEMAS IN DATABASE tb_101 TO ROLE tb_data_steward;

GRANT SELECT ON ALL TABLES IN SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT ALL ON SCHEMA governance TO ROLE tb_data_steward;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO ROLE tb_data_steward;

GRANT ROLE tb_data_steward TO USER USER;

USE ROLE tb_data_steward;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 2. Tag-Based Classification with Auto Tagging */
USE ROLE accountadmin;

CREATE OR REPLACE TAG governance.pii;
GRANT APPLY TAG ON ACCOUNT TO ROLE tb_data_steward;

GRANT EXECUTE AUTO CLASSIFICATION ON SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE tb_data_steward;
GRANT CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE ON SCHEMA governance TO ROLE tb_data_steward;

USE ROLE tb_data_steward;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
  governance.tb_classification_profile(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 30,
      'auto_tag': true
    });
    
CALL governance.tb_classification_profile!SET_TAG_MAP(
  {'column_tag_map':[
    {
      'tag_name':'tb_101.governance.pii',
      'tag_value':'pii',
      'semantic_categories':['NAME', 'PHONE_NUMBER', 'POSTAL_CODE', 'DATE_OF_BIRTH', 'CITY', 'EMAIL']
    }]});
    
CALL SYSTEM$CLASSIFY('tb_101.raw_customer.customer_loyalty', 'tb_101.governance.tb_classification_profile');

SELECT 
    column_name,
    tag_database,
    tag_schema,
    tag_name,
    tag_value,
    apply_method
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('raw_customer.customer_loyalty', 'table'));

/* 3. Column-level Security with Masking Policies */
CREATE OR REPLACE MASKING POLICY governance.mask_string_pii AS (original_value STRING)
RETURNS STRING ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN '****MASKED****'
    ELSE original_value
  END;
  
CREATE OR REPLACE MASKING POLICY governance.mask_date_pii AS (original_value DATE)
RETURNS DATE ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN DATE_TRUNC('year', original_value)
    ELSE original_value
  END;
  
ALTER TAG governance.pii SET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
    
USE ROLE public;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

USE ROLE tb_admin;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 4. Row Level Security with Row Access Policies */
USE ROLE tb_data_steward;

CREATE OR REPLACE TABLE governance.row_policy_map
    (role STRING, country_permission STRING);
    
INSERT INTO governance.row_policy_map
    VALUES('tb_data_engineer', 'United States');
    
CREATE OR REPLACE ROW ACCESS POLICY governance.customer_loyalty_policy
    AS (country STRING) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
        OR EXISTS 
            (
            SELECT 1
                FROM governance.row_policy_map rp
            WHERE
                UPPER(rp.role) = CURRENT_ROLE()
                AND rp.country_permission = country
            );
            
ALTER TABLE raw_customer.customer_loyalty
    ADD ROW ACCESS POLICY governance.customer_loyalty_policy ON (country);
    
USE ROLE tb_data_engineer;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;

/* 5. Data Quality Monitoring with Data Metric Functions */
USE ROLE tb_data_steward;

SELECT SNOWFLAKE.CORE.NULL_PERCENT(SELECT customer_id FROM raw_pos.order_header);
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT(SELECT order_id FROM raw_pos.order_header); 
SELECT SNOWFLAKE.CORE.AVG(SELECT order_total FROM raw_pos.order_header);

CREATE OR REPLACE DATA METRIC FUNCTION governance.invalid_order_total_count(
    order_prices_t table(order_total NUMBER, unit_price NUMBER, quantity INTEGER))
RETURNS NUMBER
AS
'SELECT COUNT(*) FROM order_prices_t WHERE order_total != unit_price * quantity';

INSERT INTO raw_pos.order_detail
SELECT 904745311, 459520442, 52, null, 0, 2, 5.0, 5.0, null;

SELECT governance.invalid_order_total_count(
    SELECT price, unit_price, quantity FROM raw_pos.order_detail
) AS num_orders_with_incorrect_price;
    
ALTER TABLE raw_pos.order_detail
    SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';
    
ALTER TABLE raw_pos.order_detail
    ADD DATA METRIC FUNCTION governance.invalid_order_total_count
    ON (price, unit_price, quantity);

/* 6. Account Security Monitoring with the Trust Center */
USE ROLE accountadmin;
GRANT APPLICATION ROLE SNOWFLAKE.TRUST_CENTER_ADMIN TO ROLE tb_admin;
USE ROLE tb_admin;

-------------------------------------------------------------------------
--RESET--
-------------------------------------------------------------------------
USE ROLE accountadmin;

DROP ROLE IF EXISTS tb_data_steward;

ALTER TAG IF EXISTS governance.pii UNSET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
DROP MASKING POLICY IF EXISTS governance.mask_string_pii;
DROP MASKING POLICY IF EXISTS governance.mask_date_pii;

ALTER SCHEMA IF EXISTS raw_customer UNSET CLASSIFICATION_PROFILE;
DROP SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE IF EXISTS tb_classification_profile;

ALTER TABLE IF EXISTS raw_customer.customer_loyalty 
    DROP ALL ROW ACCESS POLICIES;
DROP ROW ACCESS POLICY IF EXISTS governance.customer_loyalty_policy;

DELETE FROM raw_pos.order_detail WHERE order_detail_id = 904745311;
ALTER TABLE IF EXISTS raw_pos.order_detail
    DROP DATA METRIC FUNCTION governance.invalid_order_total_count ON (price, unit_price, quantity);
DROP FUNCTION IF EXISTS governance.invalid_order_total_count(TABLE(NUMBER, NUMBER, INTEGER));
ALTER TABLE IF EXISTS raw_pos.order_detail UNSET DATA_METRIC_SCHEDULE;

ALTER TABLE IF EXISTS raw_customer.customer_loyalty
  MODIFY
    COLUMN first_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN last_name UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN e_mail UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN phone_number UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN postal_code UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN marital_status UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN gender UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN birthday_date UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN country UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY,
    COLUMN city UNSET TAG governance.pii, SNOWFLAKE.CORE.PRIVACY_CATEGORY, SNOWFLAKE.CORE.SEMANTIC_CATEGORY;

DROP TAG IF EXISTS governance.pii;
ALTER SESSION UNSET query_tag;
```

### Step 7 - Click Next --\>

## Introduction to Roles and Access Control

Duration: 2

### Overview

Snowflake's security model is built on a framework of Role-based Access Control (RBAC) and Discretionary Access Control (DAC). Access privileges are assigned to roles, which are then assigned to users. This creates a powerful and flexible hierarchy for securing objects.

> aside positive
> **[Access Control Overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)**: To learn more about the key concepts of access control in Snowflake, including securable objects, roles, privileges, and users.

### Step 1 - Set Context and View Existing Roles

First, let's set our context for this exercise and view the roles that already exist in the account.

```sql
USE ROLE useradmin;
USE DATABASE tb_101;
USE WAREHOUSE tb_dev_wh;

SHOW ROLES;
```

### Step 2 - Create a Custom Role

We will now create a custom `tb_data_steward` role. This role will be responsible for managing and protecting our customer data.

```sql
CREATE OR REPLACE ROLE tb_data_steward
    COMMENT = 'Custom Role';
```

The typical hierarchy of system and custom roles might look something like this:

```
                                +---------------+
                                | ACCOUNTADMIN  |
                                +---------------+
                                  ^    ^     ^
                                  |    |     |
                    +-------------+-+  |    ++-------------+
                    | SECURITYADMIN |  |    |   SYSADMIN   |<------------+
                    +---------------+  |    +--------------+             |
                            ^          |     ^        ^                  |
                            |          |     |        |                  |
                    +-------+-------+  |     |  +-----+-------+  +-------+-----+
                    |   USERADMIN   |  |     |  | CUSTOM ROLE |  | CUSTOM ROLE |
                    +---------------+  |     |  +-------------+  +-------------+
                            ^          |     |      ^              ^      ^
                            |          |     |      |              |      |
                            |          |     |      |              |    +-+-----------+
                            |          |     |      |              |    | CUSTOM ROLE |
                            |          |     |      |              |    +-------------+
                            |          |     |      |              |           ^
                            |          |     |      |              |           |
                            +----------+-----+---+--+--------------+-----------+
                                                 |
                                            +----+-----+
                                            |  PUBLIC  |
                                            +----------+
```

### Step 3 - Grant Privileges to the Custom Role

A role is useless without privileges. Let's switch to the `securityadmin` role to grant our new `tb_data_steward` role the necessary permissions to use a warehouse and access our database schemas and tables.

```sql
USE ROLE securityadmin;

-- Grant warehouse usage
GRANT OPERATE, USAGE ON WAREHOUSE tb_dev_wh TO ROLE tb_data_steward;

-- Grant database and schema usage
GRANT USAGE ON DATABASE tb_101 TO ROLE tb_data_steward;
GRANT USAGE ON ALL SCHEMAS IN DATABASE tb_101 TO ROLE tb_data_steward;

-- Grant table-level privileges
GRANT SELECT ON ALL TABLES IN SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT ALL ON SCHEMA governance TO ROLE tb_data_steward;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO ROLE tb_data_steward;
```

### Step 4 - Grant and Use the New Role

Finally, we grant the new role to our own user. Then we can switch to the `tb_data_steward` role and run a query to see what data we can access.

```sql
-- Grant role to your user
GRANT ROLE tb_data_steward TO USER USER;

-- Switch to the new role
USE ROLE tb_data_steward;

-- Run a test query
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

Looking at the query results, it's clear this table contains a lot of Personally Identifiable Information (PII). In the next sections, we'll learn how to protect it.

### Step 5 - Click Next --\>

## Tag-Based Classification with Auto Tagging

Duration: 3

### Overview

A key first step in data governance is identifying and classifying sensitive data. Snowflake Horizon's auto-tagging capability can automatically discover sensitive information by monitoring columns in your schemas. We can then use these tags to apply security policies.

> aside positive
> **[Automatic Classification](https://docs.snowflake.com/en/user-guide/classify-auto)**: Learn how Snowflake can automatically classify sensitive data based on a schedule, simplifying governance at scale.

### Step 1 - Create PII Tag and Grant Privileges

Using the `accountadmin` role, we'll create a `pii` tag in our `governance` schema. We will also grant the necessary privileges to our `tb_data_steward` role to perform classification.

```sql
USE ROLE accountadmin;

CREATE OR REPLACE TAG governance.pii;
GRANT APPLY TAG ON ACCOUNT TO ROLE tb_data_steward;

GRANT EXECUTE AUTO CLASSIFICATION ON SCHEMA raw_customer TO ROLE tb_data_steward;
GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE tb_data_steward;
GRANT CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE ON SCHEMA governance TO ROLE tb_data_steward;
```

### Step 2 - Create a Classification Profile

Now, as the `tb_data_steward`, we'll create a classification profile. This profile defines how auto-tagging will behave.

```sql
USE ROLE tb_data_steward;

CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
  governance.tb_classification_profile(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 30,
      'auto_tag': true
    });
```

### Step 3 - Map Semantic Categories to the PII Tag

Next, we'll define a mapping that tells the classification profile to apply our `governance.pii` tag to any column whose `SEMANTIC_CATEGORY` matches common PII types like `NAME`, `PHONE_NUMBER`, `EMAIL`, etc.

```sql
CALL governance.tb_classification_profile!SET_TAG_MAP(
  {'column_tag_map':[
    {
      'tag_name':'tb_101.governance.pii',
      'tag_value':'pii',
      'semantic_categories':['NAME', 'PHONE_NUMBER', 'POSTAL_CODE', 'DATE_OF_BIRTH', 'CITY', 'EMAIL']
    }]});
```

### Step 4 - Run Classification and View Results

Let's manually trigger the classification process on our `customer_loyalty` table. Then, we can query the `INFORMATION_SCHEMA` to see the tags that were automatically applied.

```sql
-- Trigger classification
CALL SYSTEM$CLASSIFY('tb_101.raw_customer.customer_loyalty', 'tb_101.governance.tb_classification_profile');

-- View applied tags
SELECT 
    column_name,
    tag_database,
    tag_schema,
    tag_name,
    tag_value,
    apply_method
FROM TABLE(INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS('raw_customer.customer_loyalty', 'table'));
```

Notice that columns identified as PII now have our custom `governance.pii` tag applied.

### Step 5 - Click Next --\>

## Column-Level Security with Masking Policies

Duration: 3

### Overview

Now that our sensitive columns are tagged, we can use Dynamic Data Masking to protect them. A masking policy is a schema-level object that determines whether a user sees the original data or a masked version at query time. We can apply these policies directly to our `pii` tag.

> aside positive
> **[Column-level Security](https://docs.snowflake.com/en/user-guide/security-column-intro)**: Column-level Security includes Dynamic Data Masking and External Tokenization to protect sensitive data.

### Step 1 - Create Masking Policies

We'll create two policies: one to mask string data and one to mask date data. The logic is simple: if the user's role is not privileged (i.e., not `ACCOUNTADMIN` or `TB_ADMIN`), return a masked value. Otherwise, return the original value.

```sql
-- Create the masking policy for sensitive string data
CREATE OR REPLACE MASKING POLICY governance.mask_string_pii AS (original_value STRING)
RETURNS STRING ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN '****MASKED****'
    ELSE original_value
  END;

-- Now create the masking policy for sensitive DATE data
CREATE OR REPLACE MASKING POLICY governance.mask_date_pii AS (original_value DATE)
RETURNS DATE ->
  CASE WHEN
    CURRENT_ROLE() NOT IN ('ACCOUNTADMIN', 'TB_ADMIN')
    THEN DATE_TRUNC('year', original_value)
    ELSE original_value
  END;
```

### Step 2 - Apply Masking Policies to the Tag

The power of tag-based governance comes from applying the policy once to the tag. This action automatically protects all columns that have that tag, now and in the future.

```sql
ALTER TAG governance.pii SET
    MASKING POLICY governance.mask_string_pii,
    MASKING POLICY governance.mask_date_pii;
```

### Step 3 - Test the Policies

Let's test our work. First, switch to the unprivileged `public` role and query the table. The PII columns should be masked.

```sql
USE ROLE public;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

<!-- \<img src="assets/masked\_data.png"/\> -->

Now, switch to a privileged role, `tb_admin`. The data should now be fully visible.

```sql
USE ROLE tb_admin;
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

<!-- \<img src="assets/unmasked\_data.png"/\> -->

### Step 4 - Click Next --\>

## Row-Level Security with Row Access Policies

Duration: 3

### Overview

In addition to masking columns, Snowflake allows you to filter which rows are visible to a user with Row Access Policies. The policy evaluates each row against rules you define, often based on the user's role or other session attributes.

> aside positive
> **[Row-level Security](https://docs.snowflake.com/en/user-guide/security-row-intro)**: Row Access Policies determine which rows are visible in a query result, enabling fine-grained access control.

### Step 1 - Create a Policy Mapping Table

A common pattern for row access policies is to use a mapping table that defines which roles can see which data. We'll create a table that maps roles to the `country` values they are permitted to see.

```sql
USE ROLE tb_data_steward;

CREATE OR REPLACE TABLE governance.row_policy_map
    (role STRING, country_permission STRING);

-- Map the tb_data_engineer role to only see 'United States' data
INSERT INTO governance.row_policy_map
    VALUES('tb_data_engineer', 'United States');
```

### Step 2 - Create the Row Access Policy

Now we create the policy itself. This policy returns `TRUE` (allowing the row to be seen) if the user's role is an admin role OR if the user's role exists in our mapping table and matches the `country` value of the current row.

```sql
CREATE OR REPLACE ROW ACCESS POLICY governance.customer_loyalty_policy
    AS (country STRING) RETURNS BOOLEAN ->
        CURRENT_ROLE() IN ('ACCOUNTADMIN', 'SYSADMIN') 
        OR EXISTS 
            (
            SELECT 1 FROM governance.row_policy_map rp
            WHERE
                UPPER(rp.role) = CURRENT_ROLE()
                AND rp.country_permission = country
            );
```

### Step 3 - Apply and Test the Policy

Apply the policy to the `country` column of our `customer_loyalty` table. Then, switch to the `tb_data_engineer` role and query the table.

```sql
-- Apply the policy
ALTER TABLE raw_customer.customer_loyalty
    ADD ROW ACCESS POLICY governance.customer_loyalty_policy ON (country);

-- Switch role to test the policy
USE ROLE tb_data_engineer;

-- Query the table
SELECT TOP 100 * FROM raw_customer.customer_loyalty;
```

The result set should now only contain rows where the `country` is 'United States'.

### Step 4 - Click Next --\>

## Data Quality Monitoring with Data Metric Functions

Duration: 2

### Overview

Data governance isn't just about security; it's also about trust and reliability. Snowflake helps maintain data integrity with Data Metric Functions (DMFs). You can use system-defined DMFs or create your own to run automated quality checks on your tables.

> aside positive
> **[Data Quality Monitoring](https://docs.snowflake.com/en/user-guide/data-quality-intro)**: Learn how to ensure data consistency and reliability using built-in and custom Data Metric Functions.

### Step 1 - Use System DMFs

Let's use a few of Snowflake's built-in DMFs to check the quality of our `order_header` table.

```sql
USE ROLE tb_data_steward;

-- This will return the percentage of null customer IDs.
SELECT SNOWFLAKE.CORE.NULL_PERCENT(SELECT customer_id FROM raw_pos.order_header);

-- We can use DUPLICATE_COUNT to check for duplicate order IDs.
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT(SELECT order_id FROM raw_pos.order_header); 

-- Average order total amount for all orders.
SELECT SNOWFLAKE.CORE.AVG(SELECT order_total FROM raw_pos.order_header);
```

### Step 2 - Create a Custom DMF

We can also create custom DMFs for our specific business logic. Let's create one that checks for orders where the `order_total` does not equal `unit_price * quantity`.

```sql
CREATE OR REPLACE DATA METRIC FUNCTION governance.invalid_order_total_count(
    order_prices_t table(
        order_total NUMBER,
        unit_price NUMBER,
        quantity INTEGER
    )
)
RETURNS NUMBER
AS
'SELECT COUNT(*)
 FROM order_prices_t
 WHERE order_total != unit_price * quantity';
```

### Step 3 - Test and Schedule the DMF

Let's insert a bad record to test our DMF. Then, we'll call the function to see if it catches the error.

```sql
-- Insert a record with an incorrect total price
INSERT INTO raw_pos.order_detail
SELECT 904745311, 459520442, 52, null, 0, 2, 5.0, 5.0, null;

-- Call the custom DMF on the order detail table.
SELECT governance.invalid_order_total_count(
    SELECT price, unit_price, quantity FROM raw_pos.order_detail
) AS num_orders_with_incorrect_price;
```

To automate this check, we can associate the DMF with the table and set a schedule to have it run automatically whenever the data changes.

```sql
ALTER TABLE raw_pos.order_detail
    SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';

ALTER TABLE raw_pos.order_detail
    ADD DATA METRIC FUNCTION governance.invalid_order_total_count
    ON (price, unit_price, quantity);
```

### Step 4 - Click Next --\>

## Account Security Monitoring with the Trust Center

Duration: 2

### Overview

The Trust Center provides a centralized dashboard for monitoring security risks across your entire Snowflake account. It uses scheduled scanners to check for issues like missing Multi-Factor Authentication (MFA), over-privileged roles, or inactive users, and then provides recommended actions.

> aside positive
> **[Trust Center Overview](https://docs.snowflake.com/en/user-guide/trust-center/overview)**: The Trust Center enables automatic checks to evaluate and monitor security risks on your account.

### Step 1 - Grant Privileges and Navigate to the Trust Center

First, an `ACCOUNTADMIN` needs to grant the `TRUST_CENTER_ADMIN` application role to a user or role. We'll grant it to our `tb_admin` role.

```sql
USE ROLE accountadmin;
GRANT APPLICATION ROLE SNOWFLAKE.TRUST_CENTER_ADMIN TO ROLE tb_admin;
USE ROLE tb_admin; 
```

Now, navigate to the Trust Center in the Snowsight UI:

1.  Click the **Monitoring** tab in the left navigation bar.
2.  Click on **Trust Center**.

\<img src="assets/trust\_center.png"/\>

### Step 2 - Enable Scanner Packages

By default, most scanner packages are disabled. Let's enable them to get a comprehensive view of our account's security posture.

1.  In the Trust Center, click the **Scanner Packages** tab.
2.  Click on **CIS Benchmarks**.
3.  Click the **Enable Package** button.
4.  In the modal, set the **Frequency** to `Monthly` and click **Continue**.
5.  Repeat this process for the **Threat Intelligence** scanner package.

### Step 3 - Review Findings

After the scanners have had a moment to run, navigate back to the **Findings** tab.

  - You will see a dashboard summarizing violations by severity.
  - The list below details each violation, its severity, and the scanner that found it.
  - Clicking on any violation will open a details pane with a summary and recommended remediation steps.
  - You can filter the list by severity, status, or scanner package to focus on the most critical issues.

This powerful tool gives you a continuous, actionable overview of your Snowflake account's security health.

### Step 4 - Click Next --\>

## Conclusion and Next Steps

Duration: 1

### Conclusion

Fantastic work\! You have successfully completed the Tasty Bytes - Governance with Horizon Quickstart.

By doing so you have now explored how to:

  - Create custom roles and manage privileges using RBAC.
  - Automatically classify PII using classification profiles and tags.
  - Apply tag-based dynamic data masking to protect sensitive columns.
  - Implement row-level security using row access policies.
  - Monitor data quality with both system and custom Data Metric Functions.
  - Continuously monitor account security with the Trust Center.

If you would like to re-run this Quickstart, please run the `RESET` scripts located at the bottom of your worksheet.

### Next Steps

To continue your journey in the Snowflake AI Data Cloud, please now visit the link below to see all other Powered by Tasty Bytes - Quickstarts available to you.

  - ### [Powered by Tasty Bytes - Quickstarts Table of Contents](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3)

<!-- end list -->

```
```