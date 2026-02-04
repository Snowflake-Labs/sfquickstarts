author: Susan Devitt, Severin Gassauer-Fleissner
id: getting-started-with-horizon-for-data-governance-in-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/community-sourced, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/ingestion, snowflake-site:taxonomy/product/cortex-ai, snowflake-site:taxonomy/snowflake-feature/horizon
language: en
summary: This guide demonstrates Snowflake Horizon's capabilities for modern data governance, including AI-powered automation. Learn to monitor data pipelines, govern data with lineage and masking, leverage AI for automated PII classification and redaction, create governed semantic views for Cortex Analyst, and query governance metadata using natural language.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake


# Getting Started with Horizon for Data Governance in Snowflake
<!-- ------------------------ -->
## Overview 

Snowflake Horizon is a suite of native Snowflake features that help people easily find, understand, and trust data. In this comprehensive lab, you'll learn how Horizon ensures reliable and trustworthy data for confident, data-driven decisions while maintaining observability and security of data assets—including AI-powered analytics.

In this hands-on lab, you will follow a step-by-step guide using a sample database of synthetic customer orders. You'll explore how Horizon monitors and governs data through three key personas:
 - **Data Engineer**: Monitoring pipelines and data quality
 - **Data Governor**: Protecting PII with masking and classification
 - **Data Governor Admin**: Auditing access, lineage, and compliance

This lab demonstrates governance capabilities including AI-powered extensions that automate PII discovery, enable governed natural language queries, and ensure consistent policy enforcement across SQL and AI workloads. 

### AI-Powered Governance Extensions

This lab showcases how Snowflake's AI capabilities enhance and automate governance:

**Automated PII Discovery (Section 2)**  
Use native CLASSIFICATION_PROFILE to automatically discover and tag 50+ PII types across your structured data with custom tag mapping.

**AI_REDACT for Unstructured Data (Section 5)**  
Apply AI_REDACT to remove sensitive information from unstructured text like customer feedback.

**Governed AI Analytics (Section 4)**  
Create semantic views for Cortex Analyst where masking policies, row access policies, and tags automatically apply to natural language queries—zero additional configuration required.

**Natural Language Governance (Section 6)**  
Query governance metadata using Cortex Code and Cortex Analyst in plain English. Ask questions like "Which tables have PII but no masking policy?" without writing SQL.

**Key Principle**: Fine-grained access controls are consistently enforced whether users query data via SQL, Python, or AI-powered natural language interfaces. The same governance policies protect traditional and AI workloads.

### Introduction to Horizon

Before we dive into the lab, let's take a look at a typical governance workflow and learn a bit more about the personas we will be exploring today. 
#### Typical Governance Workflow  
![img](assets/workflow.png)


#### [Data Engineer Persona Video](https://youtu.be/MdZ1PaJWH2w?si=o8k8HDrzQjZ5Jhst)  


#### [Data Governor/Steward Persona Video](https://youtu.be/bF6FAMeGEZc?si=mKxGlzJL6843B-FK)  


#### [Data Governor Admin Persona Video](https://youtu.be/doView4YqUI?si=tQd_KP7YzIIvogla)  

Now that you have the introduction to Horizon and our personas, let's get started.

### - What You’ll Learn 
**Core Governance (Sections 1-3):**
- Protect sensitive data with role-based masking and row access policies
- Visualize column-level lineage for impact analysis
- Monitor data quality with custom and system data metric functions
- Audit data access and track schema changes
- Create Horizon dashboards in Snowsight

**AI Governance Extensions (Sections 4-6):**
- Create governed semantic views for Cortex Analyst
- Automate PII discovery with CLASSIFICATION_PROFILE
- Redact sensitive data from unstructured text with AI_REDACT
- Query governance metadata using natural language
- Ensure consistent policy enforcement across SQL and AI workloads

### - What You’ll Need 
- A trial [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account with ACCOUNTADMIN access (recommended) or an existing Snowflake account
- Approximately 115 minutes to complete all sections
- Basic familiarity with SQL (no AI/ML expertise required)
<!-- ------------------------ -->
## Setup


All the scripts for this lab are available at [Snowflake Labs](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake) for you as a resource.

Let's get started! First we will run the [script 0_lab_setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/0-lab-Setup.sql) 


### Step 1 - Create a new worksheet titled 0_lab_setup

In Snowsight create a new worksheet and rename it 0_lab_setup.

### Step 2 - Copy the below script in its entirety and paste into your worksheet

This script will create the objects and load data needed to run the lab. More explanation on these objects and how they are used will be provided in later steps.
### [script 0_lab_setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/0-lab-Setup.sql)

````
--Create all Roles and assign to user
USE ROLE SECURITYADMIN;
CREATE OR REPLACE ROLE HRZN_DATA_ENGINEER;
CREATE OR REPLACE ROLE HRZN_DATA_GOVERNOR;
CREATE OR REPLACE ROLE HRZN_DATA_USER;
CREATE OR REPLACE ROLE HRZN_IT_ADMIN;

GRANT ROLE HRZN_DATA_ENGINEER TO ROLE SYSADMIN;
GRANT ROLE HRZN_DATA_GOVERNOR TO ROLE SYSADMIN;
GRANT ROLE HRZN_DATA_USER TO ROLE SYSADMIN;
GRANT ROLE HRZN_IT_ADMIN TO ROLE SYSADMIN;

SET MY_USER_ID  = CURRENT_USER();
SELECT ($MY_USER_ID);
GRANT ROLE HRZN_DATA_ENGINEER TO USER identifier($MY_USER_ID);
GRANT ROLE HRZN_DATA_GOVERNOR TO USER identifier($MY_USER_ID);
GRANT ROLE HRZN_DATA_USER TO USER identifier($MY_USER_ID);
GRANT ROLE HRZN_IT_ADMIN TO USER identifier($MY_USER_ID);

--Create warehouse and provide grants
USE ROLE SYSADMIN;
CREATE OR REPLACE WAREHOUSE HRZN_WH WITH WAREHOUSE_SIZE='X-SMALL';
GRANT USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ENGINEER;
GRANT USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_GOVERNOR;
GRANT USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_USER;
GRANT USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_IT_ADMIN;

--Create database, schemas and assign to appropriate roles

GRANT  CREATE DATABASE ON ACCOUNT TO ROLE HRZN_DATA_ENGINEER;

USE ROLE HRZN_DATA_ENGINEER;
CREATE OR REPLACE DATABASE HRZN_DB;
CREATE OR REPLACE SCHEMA HRZN_DB.HRZN_SCH;

GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;
GRANT USAGE ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT CREATE SCHEMA ON DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;

GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;

GRANT SELECT ON ALL TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT ON ALL VIEWS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;

GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;
GRANT USAGE ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_IT_ADMIN;
GRANT CREATE SCHEMA ON DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;



GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_DATA_USER;
GRANT USAGE ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_USER;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_DATA_USER;
GRANT SELECT ON ALL TABLES IN DATABASE HRZN_DB TO ROLE HRZN_DATA_USER;

USE ROLE HRZN_DATA_GOVERNOR;

-- Create a  Schema to contain classifiers
CREATE OR REPLACE SCHEMA HRZN_DB.CLASSIFIERS
COMMENT = 'Schema containing Classifiers';

-- Create a Schema to contain Tags
CREATE OR REPLACE SCHEMA HRZN_DB.TAG_SCHEMA
COMMENT = 'Schema containing Tags';

CREATE OR REPLACE TABLE HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP
    (role STRING, state_visibility STRING);

-- with the table in place, we will now INSERT the relevant Role to State Permissions mapping to ensure
-- our Test Role can only see Massachusetts (MA) customers
INSERT INTO HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP
    VALUES ('HRZN_DATA_USER','MA'); 

    
-- Create a Schema to contain Security Policies
CREATE OR REPLACE SCHEMA SEC_POLICIES_SCHEMA
COMMENT = 'Schema containing Security Policies';

USE ROLE SECURITYADMIN;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;

GRANT SELECT ON FUTURE TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_USER;
GRANT SELECT ON FUTURE TABLES IN DATABASE HRZN_DB TO ROLE HRZN_DATA_USER;

GRANT SELECT ON FUTURE TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_IT_ADMIN;
GRANT SELECT ON FUTURE TABLES IN DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;

GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;
GRANT SELECT ON ALL VIEWS IN DATABASE HRZN_DB TO ROLE HRZN_IT_ADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_IT_ADMIN;
GRANT SELECT ON ALL VIEWS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_IT_ADMIN;


USE ROLE ACCOUNTADMIN;
GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE HRZN_DATA_ENGINEER;
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE HRZN_DATA_ENGINEER;
-- Note: This grant may not be available in all trial accounts.
-- GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE HRZN_DATA_ENGINEER;

GRANT DATABASE ROLE SNOWFLAKE.GOVERNANCE_VIEWER TO ROLE HRZN_DATA_GOVERNOR;
GRANT DATABASE ROLE SNOWFLAKE.OBJECT_VIEWER TO ROLE HRZN_DATA_GOVERNOR;
GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER TO ROLE HRZN_DATA_GOVERNOR;
GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE HRZN_DATA_GOVERNOR;
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE HRZN_DATA_GOVERNOR;
-- Note: This grant may not be available in all trial accounts.
-- GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE HRZN_DATA_GOVERNOR;


GRANT DATABASE ROLE SNOWFLAKE.GOVERNANCE_VIEWER TO ROLE HRZN_IT_ADMIN;
GRANT DATABASE ROLE SNOWFLAKE.OBJECT_VIEWER TO ROLE HRZN_IT_ADMIN;
GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER TO ROLE HRZN_IT_ADMIN;
GRANT DATABASE ROLE SNOWFLAKE.DATA_METRIC_USER TO ROLE HRZN_IT_ADMIN;
GRANT EXECUTE DATA METRIC FUNCTION ON ACCOUNT TO ROLE HRZN_IT_ADMIN;
-- Note: This grant may not be available in all trial accounts.
-- GRANT APPLICATION ROLE SNOWFLAKE.DATA_QUALITY_MONITORING_VIEWER TO ROLE HRZN_IT_ADMIN;



/***** C R E A T E   T A B L E *******/

USE ROLE HRZN_DATA_ENGINEER;
CREATE OR REPLACE TABLE HRZN_DB.HRZN_SCH.CUSTOMER (
	ID FLOAT,
	FIRST_NAME VARCHAR,
	LAST_NAME VARCHAR,
	STREET_ADDRESS VARCHAR,
	STATE VARCHAR,
	CITY VARCHAR,
	ZIP VARCHAR,
	PHONE_NUMBER VARCHAR,
	EMAIL VARCHAR,
	SSN VARCHAR,
	BIRTHDATE VARCHAR,
	JOB VARCHAR,
	CREDITCARD VARCHAR,
	COMPANY VARCHAR,
	OPTIN VARCHAR
);
CREATE OR REPLACE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS (
    CUSTOMER_ID VARCHAR,	
    ORDER_ID VARCHAR,	
    ORDER_TS DATE,	
    ORDER_CURRENCY VARCHAR,	
    ORDER_AMOUNT FLOAT,	
    ORDER_TAX FLOAT,	
    ORDER_TOTAL FLOAT
);
-- Load data from S3 into target tables. Then perform GRANTS.
COPY INTO HRZN_DB.HRZN_SCH.CUSTOMER
FROM s3://sfquickstarts/summit_2024_horizon_hol/CustomerDataRaw.csv
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1)
;

COPY INTO HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
FROM s3://sfquickstarts/summit_2024_horizon_hol/CustomerOrders.csv
FILE_FORMAT = (TYPE = 'CSV', SKIP_HEADER = 1)
;
GRANT ALL ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER TO ROLE HRZN_DATA_USER;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER TO ROLE HRZN_IT_ADMIN;

GRANT ALL ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS TO ROLE HRZN_DATA_USER;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS TO ROLE HRZN_IT_ADMIN;



USE ROLE ACCOUNTADMIN;
GRANT APPLY TAG on ACCOUNT to ROLE HRZN_DATA_GOVERNOR;
GRANT APPLY MASKING POLICY on ACCOUNT to ROLE HRZN_DATA_GOVERNOR;
GRANT APPLY ROW ACCESS POLICY ON ACCOUNT TO ROLE HRZN_DATA_GOVERNOR;
GRANT APPLY AGGREGATION POLICY ON ACCOUNT TO ROLE HRZN_DATA_GOVERNOR;
GRANT APPLY PROJECTION POLICY ON ACCOUNT TO ROLE HRZN_DATA_GOVERNOR;

GRANT DATABASE ROLE SNOWFLAKE.CLASSIFICATION_ADMIN TO ROLE HRZN_DATA_GOVERNOR;

--USE ROLE HRZN_DATA_ENGINEER;
--truncate table HRZN_DB.HRZN_SCH.CUSTOMER;
--truncate table HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS;

--Create View for Semantic Models and Analysis
USE ROLE HRZN_DATA_ENGINEER;
use database HRZN_DB;
use schema HRZN_DB.HRZN_SCH;
USE WAREHOUSE HRZN_WH;

-- Create summary view for customer order analytics
CREATE OR REPLACE VIEW HRZN_DB.HRZN_SCH.CUSTOMER_ORDER_SUMMARY AS
SELECT C.ID, C.FIRST_NAME, C.LAST_NAME, COUNT(CO.ORDER_ID) ORDERS_COUNT, SUM(CO.ORDER_TOTAL) ORDER_TOTAL
FROM HRZN_DB.HRZN_SCH.CUSTOMER C, HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS CO
WHERE C.ID = CO.CUSTOMER_ID
GROUP BY 1,2,3;

-- ============================================================================
-- AI GOVERNANCE EXTENSION PRIVILEGES
-- ============================================================================
-- These grants enable sections 4-6 (Semantic Views, AI_REDACT, NL Governance)
-- Added for AI Governance Lab Extensions
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Section 4: Semantic View Governance
GRANT CREATE SEMANTIC VIEW ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT CREATE VIEW ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER TO ROLE HRZN_DATA_GOVERNOR;
GRANT SELECT ON TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS TO ROLE HRZN_DATA_GOVERNOR;

-- Section 5: Cortex Agent Governance
GRANT CREATE SCHEMA ON DATABASE HRZN_DB TO ROLE HRZN_DATA_GOVERNOR;

-- Section 6: AI-Powered Classification
GRANT CREATE FUNCTION ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT CREATE PROCEDURE ON SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT USAGE ON SCHEMA HRZN_DB.CLASSIFIERS TO ROLE HRZN_DATA_GOVERNOR;
GRANT CREATE FUNCTION ON SCHEMA HRZN_DB.CLASSIFIERS TO ROLE HRZN_DATA_GOVERNOR;

-- Allow roles to use Cortex functions
GRANT USAGE ON FUTURE FUNCTIONS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_GOVERNOR;
GRANT USAGE ON FUTURE FUNCTIONS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_USER;
GRANT USAGE ON FUTURE FUNCTIONS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_IT_ADMIN;

SELECT 'Lab setup complete. You can now run sections 1-6.' as status;
````
<!-- ------------------------ -->

## Data Quality Monitoring


### Overview: Horizon as a Data Engineer 
Data Governance doesn't need to be a daunting undertaking. This section is all about how to get started with curating assets to understand common problems that most data organizations want to solve such as data quality monitoring. We will show you how easily all roles benefit from Horizon and Snowflake's RBAC Framework. 

Before we begin, the Snowflake Access Control Framework is based on:
- Role-based Access Control (RBAC): Access privileges are assigned to roles, which 
    are in turn assigned to users.
- Discretionary Access Control (DAC): Each object has an owner, who can in turn 
    grant access to that object.

> 
>The key concepts to understanding access control in Snowflake are:
>- Securable Object: An entity to which access can be granted. Unless allowed by a 
    grant, access is denied. Securable Objects are owned by a Role (as opposed to a User)
>>- Examples: Database, Schema, Table, View, Warehouse, Function, etc
>- Role: An entity to which privileges can be granted. Roles are in turn assigned 
    to users. Note that roles can also be assigned to other roles, creating a role 
    hierarchy.
>- Privilege: A defined level of access to an object. Multiple distinct privileges 
    may be used to control the granularity of access granted.
 >- User: A user identity recognized by Snowflake, whether associated with a person 
    or program.

In Summary:
- In Snowflake, a Role is a container for Privileges to a Securable Object.
- Privileges can be granted Roles
- Roles can be granted to Users
- Roles can be granted to other Roles (which inherit that Roles Privileges)
- When Users choose a Role, they inherit all the Privileges of the Roles in the hierarchy.


### System Defined Roles and Privileges
> 
 >Before beginning to deploy Role Based Access Control (RBAC) for Horizon HOL,
 let's first take a look at the Snowflake System Defined Roles and their privileges

In Snowsight create a new worksheet and rename it 1_Data_Engineer. Copy and paste each code block below and execute. You can also find the entire Data Engineer Script at [ 1-DataEngineer.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/1-DataEngineer.sql) 

Let's start by assuming the Data Engineer role and our Snowflake Development Warehouse (synonymous with compute) and we will set the context with the appropriate Database and Schema. 
```
USE ROLE HRZN_DATA_ENGINEER;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;
```

To follow best practices we will begin to investigate and deploy RBAC (Role-Based Access Control)

First, let's take a look at the Roles currently in our account
```
SHOW ROLES;
```

This next query, will turn the output of our last SHOW command and allow us to filter on the Snowflake System Roles provided by default in all Snowflake Accounts
  > Note: Depending on your permissions you may not see a result for every Role in the Where clause below.
```
SELECT
    "name",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "name" IN ('ORGADMIN','ACCOUNTADMIN','SYSADMIN','USERADMIN','SECURITYADMIN','PUBLIC');
```

#### Snowflake System Defined Role Definitions:
1. **ORGADMIN**: Role that manages operations at the organization level.
2. **ACCOUNTADMIN**: Role that encapsulates the SYSADMIN and SECURITYADMIN system-defined roles.
            It is the top-level role in the system and should be granted only to a limited/controlled number of users
            in your account.
3. **SECURITYADMIN**: Role that can manage any object grant globally, as well as create, monitor,
          and manage users and roles.
4. **USERADMIN**: Role that is dedicated to user and role management only.
5. **SYSADMIN**: Role that has privileges to create warehouses and databases in an account.
> 
>If, as recommended, you create a role hierarchy that ultimately assigns all custom roles to the SYSADMIN role, this role also has the ability to grant privileges on warehouses, databases, and other objects to other roles.
6. PUBLIC: Pseudo-role that is automatically granted to every user and every role in your account. The PUBLIC role can own securable objects, just like any other role; however, the objects owned by the role are available to every other user and role in your account.

 
                       
### Role Creation, GRANTS and SQL Variables

Now that we understand System Defined Roles, let's begin leveraging them to create a Test Role and provide it access to the Customer Order data we will deploy our initial Snowflake Horizon Governance features against.

We will use the Useradmin Role to create a Data Analyst Role
```
USE ROLE USERADMIN;

CREATE OR REPLACE ROLE HRZN_DATA_ANALYST
    COMMENT = 'Analyst Role';
```

Now we will switch to Securityadmin to handle our privilege GRANTS
```
USE ROLE SECURITYADMIN;
```
First we will grant ALL privileges on the Development Warehouse to our Sysadmin
```
GRANT ALL ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ANALYST;
```

Next we will grant only OPERATE and USAGE privileges to our Test Role
```
GRANT OPERATE, USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ANALYST;
```

> 
>**Snowflake Warehouse Privilege Grants**
>1. MODIFY: Enables altering any properties of a warehouse, including changing its size.
>2. MONITOR: Enables viewing current and past queries executed on a warehouse as well as usage statistics on that warehouse.
>3. OPERATE: Enables changing the state of a warehouse (stop, start, suspend, resume). In addition,enables viewing current and past queries executed on a warehouse and aborting any executing queries.
>4. USAGE: Enables using a virtual warehouse and, as a result, executing queries on the warehouse.
If the warehouse is configured to auto-resume when a SQL statement is submitted to it, the warehouse resumes automatically and executes the statement.
>5. ALL: Grants all privileges, except OWNERSHIP, on the warehouse.

Now we will grant USAGE on our Database and all Schemas within it
```
GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;
```
> 
> **Snowflake Database and Schema Grants**
>1. MODIFY: Enables altering any settings of a database.
>2. MONITOR: Enables performing the DESCRIBE command on the database.
>3. USAGE: Enables using a database, including returning the database details in the SHOW DATABASES command output. Additional privileges are required to view or take actions on objects in a database.
>4. ALL: Grants all privileges, except OWNERSHIP, on a database.

We are going to test Data Governance features as our Test Role, so let's ensure it can run SELECT statements against our Data Model
```
GRANT SELECT ON ALL TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_ANALYST;
GRANT SELECT ON ALL VIEWS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_ANALYST;
```
> 
>**Snowflake View and Table Privilege Grants**
>1. SELECT: Enables executing a SELECT statement on a table/view.
>2. INSERT: Enables executing an INSERT command on a table. 
>3. UPDATE: Enables executing an UPDATE command on a table.
>4. TRUNCATE: Enables executing a TRUNCATE TABLE command on a table.
>5. DELETE: Enables executing a DELETE command on a table.
    **/

Before we proceed, let's SET a SQL Variable to equal our CURRENT_USER()
```
SET MY_USER_ID  = CURRENT_USER();
```

Now we can GRANT our Role to the User we are currently logged in as and use that role
```
GRANT ROLE HRZN_DATA_ANALYST TO USER identifier($MY_USER_ID);
```

### Data Quality Monitoring 

Within Snowflake, you can measure the quality of your data by using Data Metric Functions. Using these, we want to ensure that there are not duplicate or invalid Customer Email Addresses present in our system. While our team works to resolve any existing bad records, as a data engineer, we will work to monitor these occuring moving forward.

#### Creating Data Metric functions
Within this step, we will walk through adding Data Metric Functions to our Customer Order Table to capture Duplicate and Invalid Email Address counts everytime data is updated.

Creating a System DMF by first setting a schedule on the table and then setting the metrics
```
USE ROLE HRZN_DATA_ENGINEER;
--Schedule
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER SET DATA_METRIC_SCHEDULE = 'TRIGGER_ON_CHANGES';

--Accuracy
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT on (EMAIL);

--Uniqueness
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.UNIQUE_COUNT on (EMAIL);
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.DUPLICATE_COUNT on (EMAIL);;

--Volume
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER ADD DATA METRIC FUNCTION SNOWFLAKE.CORE.ROW_COUNT on ();


--Review Counts
SELECT SNOWFLAKE.CORE.NULL_COUNT(SELECT EMAIL FROM HRZN_DB.HRZN_SCH.CUSTOMER);
SELECT SNOWFLAKE.CORE.UNIQUE_COUNT(SELECT EMAIL FROM HRZN_DB.HRZN_SCH.CUSTOMER);
SELECT SNOWFLAKE.CORE.DUPLICATE_COUNT (SELECT EMAIL FROM HRZN_DB.HRZN_SCH.CUSTOMER) AS duplicate_count;
```

Before moving on, let's validate Trigger on Changes Schedule is in place
```
SHOW PARAMETERS LIKE 'DATA_METRIC_SCHEDULE' IN TABLE HRZN_DB.HRZN_SCH.CUSTOMER;
```

#### Creating a custom DMF
To accompany the Duplicate Count DMF, let's also create a Custom Data Metric Function that uses Regular Expression (RegEx) to Count Invalid Email Addresses
```
CREATE DATA METRIC FUNCTION HRZN_DB.HRZN_SCH.INVALID_EMAIL_COUNT(IN_TABLE TABLE(IN_COL STRING))
RETURNS NUMBER 
AS
'SELECT COUNT_IF(FALSE = (IN_COL regexp ''^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$'')) FROM IN_TABLE';
```

For demo purposes, let's grant this to everyone
```
GRANT ALL ON FUNCTION HRZN_DB.HRZN_SCH.INVALID_EMAIL_COUNT(TABLE(STRING)) TO ROLE PUBLIC;
```

As we did above, let's see how many Invalid Email Addresses currently exist
```
SELECT HRZN_DB.HRZN_SCH.INVALID_EMAIL_COUNT(SELECT EMAIL FROM HRZN_DB.HRZN_SCH.CUSTOMER) AS INVALID_EMAIL_COUNT;
```

Before we can apply our DMF's to the table, we must first set the Data Metric Schedule. For our demo we will trigger this to run every 5 minutes
```
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER SET DATA_METRIC_SCHEDULE = '5 minute'; 
```
> 
>Data Metric Schedule specifies the schedule for running Data Metric Functions
for tables and can leverage MINUTE, USING CRON or TRIGGER_ON_CHANGES

Now we will add our Invalid Email Count Data Metric Function (DMF) to our table
```
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER 
    ADD DATA METRIC FUNCTION HRZN_DB.HRZN_SCH.INVALID_EMAIL_COUNT ON (EMAIL);
```

Before moving on, let's validate the Schedule is in place
```
SHOW PARAMETERS LIKE 'DATA_METRIC_SCHEDULE' IN TABLE HRZN_DB.HRZN_SCH.CUSTOMER;
```

Review the schedule:
```
SELECT metric_name, ref_entity_name, schedule, schedule_status 
FROM TABLE(INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES(
    ref_entity_name => 'HRZN_DB.HRZN_SCH.CUSTOMER', 
    ref_entity_domain => 'TABLE'));
```


The results our Data Metric Functions are written to an Event table, let's start by taking a look at the Raw output
> Note: Latency can be up to a few minutes. If the queries below are empty please wait a few minutes.

For ease of use, a flattened View is also provided so let's take a look at this as well

> 
>This view will not work in a trial account.
```
SELECT 
    change_commit_time,
    measurement_time,
    table_schema,
    table_name,
    metric_name,
    value
FROM SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS
WHERE table_database = 'HRZN_DB'
ORDER BY change_commit_time DESC;
```


 With the Data Quality metrics being logged every time our table changes we will be able to monitor the counts as new data flows in and existing e-mail updates are run.

> 
>In a production scenario a logical next step would be to configure alerts to notify you when changes to data quality occur. By combining the DMF and alert functionality, you can have consistent threshold notifications for data quality on the tables that you measure. 



## Know & protect your data


### Overview: Horizon as Data Governor

In today's world of data management, it is common to have policies and procedures that range from data quality and retention to personal data protection. A Data Governor within an organization defines and applies data policies. Here we will explore Horizon features such as **universal search** that makes it easier to find Account objects,Snowflake Marketplace listings, relevant Snowflake Documentation and Snowflake Community Knowledge Base articles.

> 
>
>Note: Universal Search understands your query and information about your database objects and can find objects with names that differ from your search terms.
>Even if you misspell or type only part of your search term, you can still see
useful results.

To leverage Universal Search in Snowsight:
- Use the Left Navigation Menu 
- Select "Search" (Magnifying Glass)
- Enter Search criteria such as:
    - Snowflake Best Practices
    - How to use Snowflake Column Masking

### Create a new worksheet
  In snowsight create a new worksheet and rename it 2_Data_Governor. Copy and paste each code block below and execute. You can also find the entire Data Governor Script at [ 2-DataGovernor_DataUser.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/2-DataGovernor_DataUser.sql)  

Let's start by assuming the Data User role and using our Horizon Warehouse (synonymous with compute). This lets us see what access our Data Users have to our customer data.

````
USE ROLE HRZN_DATA_USER;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;
````

Now, Let's look at the customer details
````
SELECT FIRST_NAME, LAST_NAME, STREET_ADDRESS, STATE, CITY, ZIP, PHONE_NUMBER, EMAIL, SSN, BIRTHDATE, CREDITCARD
FROM HRZN_DB.HRZN_SCH.CUSTOMER
SAMPLE (100 ROWS);
````

### AI-Powered Data Classification with Tag Mapping

Looking at this table we can see there is a lot of PII and sensitive data that needs to be protected. However, as a Data user, we may not understand what fields contain the sensitive data.

To set this straight, we need to ensure that the right fields are classified and tagged properly using AI-powered classification. Let's switch to the Data Governor role and explore automated classification with custom tag mapping.

````
USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;
````

#### Create Custom Classification Tag

We'll create a custom DATA_CLASSIFICATION tag that will automatically propagate to downstream tables. This implements the BYOT (Bring Your Own Tags) pattern.

````
-- Create tag schema
CREATE SCHEMA IF NOT EXISTS HRZN_DB.TAG_SCHEMA;
USE SCHEMA HRZN_DB.TAG_SCHEMA;

-- Create enterprise classification tag with propagation enabled
CREATE OR REPLACE TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION 
    ALLOWED_VALUES 'PII', 'RESTRICTED', 'SENSITIVE', 'INTERNAL', 'PUBLIC'
    COMMENT = 'Enterprise data classification with AI automation and propagation'
    PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT;
````

>
>Note: PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT ensures tags automatically flow to tables created via CREATE TABLE AS SELECT (CTAS) or views. System tags don't propagate, only user-defined tags do.

#### Create Classification Profile with Tag Map

Create a classification profile that maps native categories to our custom tag:

````
USE ROLE SYSADMIN;

CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE 
    HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE(
    {
      'minimum_object_age_for_classification_days': 0,
      'maximum_classification_validity_days': 90,
      'auto_tag': true,
      'classify_views': true,
      'tag_map': {
        'column_tag_map': [
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'PII',
            'semantic_categories': [
              'EMAIL', 
              'US_SOCIAL_SECURITY_NUMBER',
              'NATIONAL_IDENTIFIER',
              'US_BANK_ACCOUNT_NUMBER',
              'CREDIT_CARD_NUMBER'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'RESTRICTED',
            'semantic_categories': [
              'PHONE_NUMBER',
              'DATE_OF_BIRTH'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'SENSITIVE',
            'semantic_categories': [
              'NAME',
              'STREET_ADDRESS',
              'CITY',
              'US_STATE',
              'ZIP_CODE'
            ]
          },
          {
            'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
            'tag_value': 'INTERNAL',
            'semantic_categories': [
              'JOB_TITLE',
              'OCCUPATION',
              'COMPANY'
            ]
          }
        ]
      }
    });
````

>
>Note: The tag_map defines a five-tier classification taxonomy:
>- PII: Personal identifiers (highest protection)
>- RESTRICTED: Sensitive personal data
>- SENSITIVE: Personal information
>- INTERNAL: Business data
>- PUBLIC: Non-sensitive identifiers (implicit for unclassified columns)

#### Apply Classification Profile and Run Classification

Apply the profile to the database and classify tables:

````
USE ROLE HRZN_DATA_GOVERNOR;

-- Apply classification profile to the database
ALTER DATABASE HRZN_DB 
    SET CLASSIFICATION_PROFILE = 'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE';

-- Run AI classification on CUSTOMER table
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE'
);

-- Classify CUSTOMER_ORDERS table for tag propagation
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS',
    'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE'
);
````

View all tags applied (both system and custom):

````
-- View all tags applied (system + custom)
SELECT TAG_DATABASE, TAG_SCHEMA, OBJECT_NAME, COLUMN_NAME, TAG_NAME, TAG_VALUE
FROM TABLE(
  HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    'table'
))
ORDER BY TAG_NAME, COLUMN_NAME;
````

View only the DATA_CLASSIFICATION tags (the ones that will propagate):

````
-- View DATA_CLASSIFICATION tags on CUSTOMER table
SELECT 
    COLUMN_NAME,
    TAG_VALUE as CLASSIFICATION_LEVEL
FROM TABLE(
    INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
        'HRZN_DB.HRZN_SCH.CUSTOMER', 
        'table'
    )
)
WHERE TAG_NAME = 'DATA_CLASSIFICATION'
ORDER BY 
    CASE TAG_VALUE 
        WHEN 'PII' THEN 1
        WHEN 'RESTRICTED' THEN 2
        WHEN 'SENSITIVE' THEN 3
        WHEN 'INTERNAL' THEN 4
        WHEN 'PUBLIC' THEN 5
    END,
    COLUMN_NAME;
````

>
>Key Insight: The classification profile applied both system tags (SEMANTIC_CATEGORY, PRIVACY_CATEGORY) and our custom DATA_CLASSIFICATION tag. Only the DATA_CLASSIFICATION tag will propagate to downstream tables.

#### Custom Classification for Credit Cards

Extend classification with custom patterns for domain-specific data:

````
USE SCHEMA HRZN_DB.CLASSIFIERS;

-- Create a custom classifier for credit card patterns
CREATE OR REPLACE SNOWFLAKE.DATA_PRIVACY.CUSTOM_CLASSIFIER CREDITCARD();

SHOW SNOWFLAKE.DATA_PRIVACY.CUSTOM_CLASSIFIER;

-- Add regex patterns for different credit card types
CALL creditcard!add_regex('MC_PAYMENT_CARD','IDENTIFIER','^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$');
CALL creditcard!add_regex('AMX_PAYMENT_CARD','IDENTIFIER','^3[4-7][0-9]{13}$');

SELECT creditcard!list();

-- Verify credit card data exists
SELECT CREDITCARD 
FROM HRZN_DB.HRZN_SCH.CUSTOMER 
WHERE CREDITCARD REGEXP '^3[4-7][0-9]{13}$'
LIMIT 5;

-- Re-classify with custom classifier
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    {'custom_classifiers': ['HRZN_DB.CLASSIFIERS.CREDITCARD'], 'auto_tag': true}
);

-- Check credit card classification
SELECT SYSTEM$GET_TAG('snowflake.core.semantic_category','HRZN_DB.HRZN_SCH.CUSTOMER.CREDITCARD','column');
````

#### Tag-Based Masking Policies (Multi-Type)

Snowflake masking policies are **data-type specific**. A STRING policy only works on STRING columns. For production-ready protection, create one policy per data type and attach all to the same tag.

First, create a consent lookup table for masking decisions:

````
USE ROLE HRZN_DATA_GOVERNOR;
USE SCHEMA HRZN_DB.TAG_SCHEMA;

-- Create opt-in lookup table for masking decisions
CREATE OR REPLACE TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP AS
SELECT DISTINCT ID as CUSTOMER_ID, OPTIN 
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

GRANT SELECT ON TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP TO ROLE HRZN_DATA_USER;
GRANT SELECT ON TABLE HRZN_DB.TAG_SCHEMA.CUSTOMER_CONSENT_MAP TO ROLE HRZN_IT_ADMIN;
````

Now create the multi-type masking policies:

````
-- ============================================================================
-- STRING MASKING POLICY (for VARCHAR columns)
-- ============================================================================
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING
AS (VAL STRING) 
RETURNS STRING ->
CASE
    -- Governors and admins always see full data
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
    THEN VAL
    
    -- PII: Full redaction for non-governors
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
    THEN '***PII-REDACTED***'
    
    -- RESTRICTED: Partial masking - show last 4 characters
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
    THEN CONCAT('***-', RIGHT(VAL, 4))
    
    -- SENSITIVE: SHA2 hash for pseudonymization
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
    THEN SHA2(VAL, 256)
    
    -- INTERNAL and PUBLIC: Visible to all
    ELSE VAL
END;

-- ============================================================================
-- NUMBER MASKING POLICY (for FLOAT, INTEGER, NUMBER columns)
-- ============================================================================
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_NUMBER
AS (VAL NUMBER) 
RETURNS NUMBER ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
    THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
    THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
    THEN ROUND(VAL, -2)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
    THEN ABS(HASH(VAL))
    ELSE VAL
END;

-- ============================================================================
-- DATE MASKING POLICY (for DATE columns)
-- ============================================================================
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_DATE
AS (VAL DATE) 
RETURNS DATE ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
    THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
    THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
    THEN DATE_TRUNC('YEAR', VAL)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
    THEN DATE_TRUNC('MONTH', VAL)
    ELSE VAL
END;

-- ============================================================================
-- TIMESTAMP MASKING POLICY (for TIMESTAMP columns)
-- ============================================================================
CREATE OR REPLACE MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_TIMESTAMP
AS (VAL TIMESTAMP) 
RETURNS TIMESTAMP ->
CASE
    WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN')
    THEN VAL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'PII'
    THEN NULL
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'RESTRICTED'
    THEN DATE_TRUNC('DAY', VAL)
    WHEN SYSTEM$GET_TAG_ON_CURRENT_COLUMN('HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION') = 'SENSITIVE'
    THEN DATE_TRUNC('MONTH', VAL)
    ELSE VAL
END;

-- ============================================================================
-- ATTACH ALL POLICIES TO THE DATA_CLASSIFICATION TAG
-- ============================================================================
ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION 
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION 
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_NUMBER;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION 
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_DATE;

ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION 
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_TIMESTAMP;
````

>
>**Best Practice**: Each data type gets appropriate masking logic. Here's the complete masking matrix:

| Data Type | PII | RESTRICTED | SENSITIVE | INTERNAL/PUBLIC |
|-----------|-----|------------|-----------|-----------------|
| **STRING** | `***PII-REDACTED***` | `***-` + last 4 chars | SHA2 hash | Visible |
| **NUMBER** | NULL | Rounded (-2 precision) | ABS(HASH) | Visible |
| **DATE** | NULL | Year only (Jan 1) | Month only (1st) | Visible |
| **TIMESTAMP** | NULL | Day only (midnight) | Month only (1st) | Visible |

>**Key Benefits**:
>- **Type Safety**: Policies match column data types automatically
>- **Automatic Application**: Any column tagged with DATA_CLASSIFICATION gets the right policy
>- **Future-Proof**: Add new tables/columns - just tag them!

Test the masking as different roles:

````
-- Test as HRZN_DATA_GOVERNOR (sees unmasked data, all records)
USE ROLE HRZN_DATA_GOVERNOR;
SELECT 
    ID,              -- PUBLIC
    FIRST_NAME,      -- SENSITIVE
    EMAIL,           -- PII
    SSN,             -- PII
    PHONE_NUMBER,    -- RESTRICTED
    BIRTHDATE,       -- RESTRICTED
    COMPANY,         -- INTERNAL
    OPTIN            -- Shows consent status
FROM HRZN_DB.HRZN_SCH.CUSTOMER
LIMIT 10;

-- Count all customers vs opted-in customers (Governor sees all)
SELECT 
    COUNT(*) as total_customers,
    SUM(CASE WHEN OPTIN = 'Y' THEN 1 ELSE 0 END) as opted_in_customers
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

-- Test as HRZN_DATA_USER (sees masked data)
USE ROLE HRZN_DATA_USER;
SELECT 
    ID,              -- PUBLIC: Visible
    FIRST_NAME,      -- SENSITIVE: SHA2 hashed
    EMAIL,           -- PII: ***PII-REDACTED***
    SSN,             -- PII: ***PII-REDACTED***
    PHONE_NUMBER,    -- RESTRICTED: ***-1234
    BIRTHDATE,       -- RESTRICTED: ***-0590
    COMPANY          -- INTERNAL: Visible
FROM HRZN_DB.HRZN_SCH.CUSTOMER
LIMIT 10;
````

#### Opt-In Governance with Row Access Policy

For consent-based data access, the best practice is to use a **row access policy** combined with masking policies. This creates layered protection:
- **Row access policy**: Controls which records are visible based on consent
- **Masking policy**: Controls how visible data appears based on classification

````
USE ROLE HRZN_DATA_GOVERNOR;
USE SCHEMA HRZN_DB.TAG_SCHEMA;

-- Create opt-in row access policy
CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY
    AS (OPTIN_STATUS STRING) RETURNS BOOLEAN ->
    CASE
        -- Governors and admins see all records regardless of consent
        WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR', 'HRZN_IT_ADMIN')
        THEN TRUE
        -- Data users only see opted-in customers
        WHEN CURRENT_ROLE() = 'HRZN_DATA_USER' AND OPTIN_STATUS = 'Y'
        THEN TRUE
        -- Hide non-opted-in records from data users
        ELSE FALSE
    END;

-- Apply opt-in policy to CUSTOMER table
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    ADD ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY ON (OPTIN);
````

Test the layered governance:

````
-- As Governor: See all customers and count
USE ROLE HRZN_DATA_GOVERNOR;
SELECT 
    COUNT(*) as total_customers,
    SUM(CASE WHEN OPTIN = 'Y' THEN 1 ELSE 0 END) as opted_in_customers
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

-- As Data User: Only see opted-in customers (with masking applied)
USE ROLE HRZN_DATA_USER;
SELECT COUNT(*) as visible_customers FROM HRZN_DB.HRZN_SCH.CUSTOMER;

SELECT EMAIL, SSN, PHONE_NUMBER, OPTIN 
FROM HRZN_DB.HRZN_SCH.CUSTOMER 
LIMIT 5;
-- Notice: All visible rows have OPTIN='Y', and PII is still masked!
````

>
>**Key Observation - Defense in Depth**:
>- Row access policy filters WHO can see WHICH records (consent-based)
>- Masking policy controls HOW data appears when visible (classification-based)
>- Both policies apply automatically - no application code changes needed!

#### Demonstrate Tag Propagation

Create a copy of the CUSTOMER table to show automatic tag propagation:

````
-- Create derived table - tags propagate automatically
USE ROLE HRZN_DATA_ENGINEER;
CREATE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_COPY AS 
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER;

-- View propagated tags
USE ROLE HRZN_DATA_GOVERNOR;
-- Check if DATA_CLASSIFICATION tags propagated
SELECT 
    COLUMN_NAME,
    TAG_VALUE as CLASSIFICATION_LEVEL
FROM TABLE(
    INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
        'HRZN_DB.HRZN_SCH.CUSTOMER_COPY', 
        'table'
    )
)
WHERE TAG_NAME = 'DATA_CLASSIFICATION'
ORDER BY 
    CASE TAG_VALUE 
        WHEN 'PII' THEN 1
        WHEN 'RESTRICTED' THEN 2
        WHEN 'SENSITIVE' THEN 3
        WHEN 'INTERNAL' THEN 4
        WHEN 'PUBLIC' THEN 5
    END,
    COLUMN_NAME;

-- Query the copy as HRZN_DATA_USER - masking still applies!
USE ROLE HRZN_DATA_USER;
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER_COPY LIMIT 5;

USE ROLE HRZN_DATA_GOVERNOR;
````

>
>Key Observation: The DATA_CLASSIFICATION tags automatically propagated to CUSTOMER_COPY, and the masking policy attached to the tag automatically protects the new table. Zero manual work required!

#### Row-Access Policies (State-Based Filtering)

Now that our Data Governor is happy with our Tag Based Dynamic Masking controlling masking at the column level, we will now look to restrict access at the row level for our Data User role.

Within our Customer table, the HRZN_DATA_USER role should only see Customers who are based in Massachusetts (MA).

>
>**Note**: Multiple row access policies on the same table are ANDed together. We'll first drop the opt-in policy to demonstrate state-based filtering in isolation.

````
USE ROLE HRZN_DATA_GOVERNOR;

-- Drop the opt-in policy to demonstrate state-based filtering cleanly
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    DROP ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY;

-- Unset STATE tag to allow it to be used in WHERE clause
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER MODIFY COLUMN STATE UNSET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION;

-- The mapping for the user is in the table ROW_POLICY_MAP
SELECT * FROM HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP; 
````

> 
>Note: Snowflake supports row-level security through the use of Row Access Policies to determine which rows to return in the query result. The row access policy can be relatively simple to allow one particular role to view rows, or be more complex to include a mapping table in the policy definition to determine access to rows in the query result.

````
CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_STATE_RESTRICTIONS
    AS (STATE STRING) RETURNS BOOLEAN ->
       CURRENT_ROLE() IN ('ACCOUNTADMIN','HRZN_DATA_ENGINEER','HRZN_DATA_GOVERNOR') -- list of roles that will not be subject to the policy
        OR EXISTS -- this clause references our mapping table from above to handle the row level filtering
            (
            SELECT rp.ROLE
                FROM HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP rp
            WHERE 1=1
                AND rp.ROLE = CURRENT_ROLE()
                AND rp.STATE_VISIBILITY = STATE
            )
COMMENT = 'Policy to limit rows returned based on mapping table of ROLE and STATE: governance.row_policy_map';

-- Apply the Row Access Policy to the STATE column
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
    ADD ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_STATE_RESTRICTIONS ON (STATE);
````

With the policy successfully applied, let's test it using the Data User Role:

````
USE ROLE HRZN_DATA_USER;
SELECT FIRST_NAME, STREET_ADDRESS, STATE, PHONE_NUMBER, EMAIL, JOB, COMPANY 
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

USE ROLE HRZN_DATA_GOVERNOR;
````

>
>Result: Only Massachusetts (MA) customers are visible to HRZN_DATA_USER. All other states are filtered out automatically.

#### Aggregation Policies

Outside of the Data Access Policies (Masking and Row Access) we have covered, Snowflake Horizon also provides Privacy Policies. In this section we will cover the ability to set Aggregation Policies on Database Objects which can restrict certain roles to only aggregate data by only allowing for queries that aggregate data into groups of a minimum size versus retrieving individual rows.

> 
> An Aggregation Policy is a schema-level object that controls what type of query can access data from a table or view. When an aggregation policy is applied to a table, queries against that table must aggregate data into groups of a minimum size in order to return results, thereby preventing a query from returning information from an individual record.

For our use case, we will create a Conditional Aggregation Policy that will only allow queries from non-admin users to return results for queries that aggregate more than 100 rows:

````
USE ROLE HRZN_DATA_GOVERNOR;

CREATE OR REPLACE AGGREGATION POLICY HRZN_DB.TAG_SCHEMA.aggregation_policy
  AS () RETURNS AGGREGATION_CONSTRAINT ->
    CASE
      WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN','HRZN_DATA_ENGINEER','HRZN_DATA_GOVERNOR')
      THEN NO_AGGREGATION_CONSTRAINT()  
      ELSE AGGREGATION_CONSTRAINT(MIN_GROUP_SIZE => 100) -- atleast 100 rows in aggregate
    END;

-- Apply to CUSTOMER_ORDERS table
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
    SET AGGREGATION POLICY HRZN_DB.TAG_SCHEMA.aggregation_policy;
````    

Test the aggregation policy:

````
-- As governor - no restrictions
USE ROLE HRZN_DATA_GOVERNOR;
SELECT TOP 10 * FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS;

-- As data user - restricted to aggregates only
USE ROLE HRZN_DATA_USER;

-- This will fail - can't SELECT * with aggregation policy
SELECT TOP 10 * FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS;

-- This works - aggregates over 100 rows
SELECT ORDER_CURRENCY, SUM(ORDER_AMOUNT) 
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS 
GROUP BY ORDER_CURRENCY;
````

Let's answer aggregate business questions with the combined policies:

````
-- Total order amounts by state and city (>100 row groups allowed)
SELECT 
    cl.state,
    cl.city,
    COUNT(oh.order_id) AS count_order,
    SUM(oh.order_amount) AS order_total
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS oh
JOIN HRZN_DB.HRZN_SCH.CUSTOMER cl
    ON oh.customer_id = cl.id
GROUP BY ALL
ORDER BY order_total DESC;
````

> 
>Note: If the query returns a group that contains fewer records than the minimum group size of the policy, then Snowflake combines those groups into a remainder group.

````
-- Total order amounts by company and job
SELECT 
    cl.company,
    cl.job,
    COUNT(oh.order_id) AS count_order,
    SUM(oh.order_amount) AS order_total
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS oh
JOIN HRZN_DB.HRZN_SCH.CUSTOMER cl
    ON oh.customer_id = cl.id
GROUP BY ALL
ORDER BY order_total DESC;
````

Switch to Data Governor to see unrestricted results:

````
USE ROLE HRZN_DATA_GOVERNOR;

SELECT 
    cl.company,
    cl.job,
    COUNT(oh.order_id) AS count_order,
    SUM(oh.order_amount) AS order_total
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS oh
JOIN HRZN_DB.HRZN_SCH.CUSTOMER cl
    ON oh.customer_id = cl.id
GROUP BY ALL
ORDER BY order_total DESC;
````

#### Projection Policies

Within this step, we will cover another Privacy Policy framework provided by Snowflake Horizon this time diving into Projection Policies which in short will prevent queries from using a SELECT statement to project values from a column.

> 
> A projection policy is a first-class, schema-level object that defines whether a column can be projected in the output of a SQL query result. A column with a projection policy assigned to it is said to be projection constrained.

For our use case, we will create a Conditional Projection Policy that will only allow our Admin Roles to project the columns we will assign it to:

````
-- Unset ZIP tag first
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER MODIFY COLUMN ZIP UNSET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION;

-- Create projection policy
CREATE OR REPLACE PROJECTION POLICY HRZN_DB.TAG_SCHEMA.projection_policy
  AS () RETURNS PROJECTION_CONSTRAINT -> 
  CASE
    WHEN CURRENT_ROLE() IN ('ACCOUNTADMIN','HRZN_DATA_ENGINEER', 'HRZN_DATA_GOVERNOR')
    THEN PROJECTION_CONSTRAINT(ALLOW => true)
    ELSE PROJECTION_CONSTRAINT(ALLOW => false)
  END;
````

With the Projection Policy in place, let's assign it to our ZIP column:

````
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER
 MODIFY COLUMN ZIP
 SET PROJECTION POLICY HRZN_DB.TAG_SCHEMA.projection_policy;
````

Let's see how our projection policy works for the Data User:

````
USE ROLE HRZN_DATA_USER;
SELECT TOP 100 * FROM HRZN_DB.HRZN_SCH.CUSTOMER; -- Fails - ZIP cannot be projected
````

What if we EXCLUDE the ZIP column?

````
SELECT TOP 100 * EXCLUDE ZIP FROM HRZN_DB.HRZN_SCH.CUSTOMER; -- Works!
````

Although our Projection Policy blocks our Data User Role from including the ZIP column in the SELECT clause, it can still be used in the WHERE clause to assist with analysis:

````
-- Filter by ZIP without projecting it
SELECT 
    * EXCLUDE ZIP
FROM HRZN_DB.HRZN_SCH.CUSTOMER
WHERE ZIP NOT IN ('97135', '95357');

-- Find customers who opted in from specific ZIP codes
SELECT 
    ID, FIRST_NAME, PHONE_NUMBER, EMAIL, COMPANY
FROM HRZN_DB.HRZN_SCH.CUSTOMER
WHERE ZIP IN ('97135', '95357')
    AND OPTIN = 'Y';
````

#### Optional Cleanup for Next Labs

Reset policies for subsequent sections:

````
USE ROLE HRZN_DATA_GOVERNOR;

-- Optional cleanup for next labs
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS UNSET AGGREGATION POLICY;
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER MODIFY COLUMN ZIP UNSET PROJECTION POLICY;

-- Re-apply DATA_CLASSIFICATION tag to ZIP for consistency
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER MODIFY COLUMN ZIP SET TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION = 'SENSITIVE';
````

Now that we've protected our data with AI-powered classification and our users can access it appropriately, let's move on to explore the Governor Admin role.


## Access & Audit


### Overview: Governor Admin 

Access History provides insights into user queries encompassing what data was 
read and when, as well as what statements have performed a write operations. Access History is particularly important for Compliance, Auditing, and Governance.

Within this step, we will walk through leveraging Access History to find when the last time our Raw data was read from and written to. 
In Snowsight create a new worksheet and rename it 3_Governor_Admin. Copy and paste each code block below and execute. You can also find the entire Data Governor Admin Script at [ 3-Data-governor-Admin.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/3-Data-governor-Admin.sql) 

> 
>Note: Access History latency is up to 3 hours.  So, some of the queries below may not have results right away. 
````
USE ROLE HRZN_IT_ADMIN;
 USE DATABASE HRZN_DB;
 USE SCHEMA HRZN_SCH;
 USE WAREHOUSE HRZN_WH;
````

Let's check out how our data is being accessed
- How many queries have accessed each of our Raw layer tables directly?
````
SELECT 
    value:"objectName"::STRING AS object_name,
    COUNT(DISTINCT query_id) AS number_of_queries
FROM snowflake.account_usage.access_history,
LATERAL FLATTEN (input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name
ORDER BY number_of_queries DESC;
````

- What is the breakdown between Read and Write queries and when did they last occur?
````
SELECT 
    value:"objectName"::STRING AS object_name,
    CASE 
        WHEN object_modified_by_ddl IS NOT NULL THEN 'write'
        ELSE 'read'
    END AS query_type,
    COUNT(DISTINCT query_id) AS number_of_queries,
    MAX(query_start_time) AS last_query_start_time
FROM snowflake.account_usage.access_history,
LATERAL FLATTEN (input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name, query_type
ORDER BY object_name, number_of_queries DESC;

-- last few "read" queries
SELECT
    qh.user_name,    
    qh.query_text,
    value:objectName::string as "TABLE"
FROM snowflake.account_usage.query_history AS qh
JOIN snowflake.account_usage.access_history AS ah
ON qh.query_id = ah.query_id,
    LATERAL FLATTEN(input => ah.base_objects_accessed)
WHERE query_type = 'SELECT' AND
    value:objectName = 'HRZN_DB.HRZN_SCH.CUSTOMER' AND
    start_time > dateadd(day, -90, current_date());

-- last few "write" queries
SELECT
    qh.user_name,    
    qh.query_text,
    value:objectName::string as "TABLE"
FROM snowflake.account_usage.query_history AS qh
JOIN snowflake.account_usage.access_history AS ah
ON qh.query_id = ah.query_id,
    LATERAL FLATTEN(input => ah.base_objects_accessed)
WHERE query_type != 'SELECT' AND
    value:objectName = 'HRZN_DB.HRZN_SCH.CUSTOMER' AND
    start_time > dateadd(day, -90, current_date());
````

- Find longest running queries
````
SELECT
query_text,
user_name,
role_name,
database_name,
warehouse_name,
warehouse_size,
execution_status,
round(total_elapsed_time/1000,3) elapsed_sec
FROM snowflake.account_usage.query_history
ORDER BY total_elapsed_time desc
LIMIT 10;
````
- Find queries that have been executed against sensitive tables
````
SELECT
  q.USER_NAME,
  q.QUERY_TEXT,
  q.START_TIME,
  q.END_TIME
FROM
  SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY q 
WHERE
  q.QUERY_TEXT ILIKE '%HRZN_DB.HRZN_SCH.CUSTOMER%'
ORDER BY
  q.START_TIME DESC;
````

- Show the flow of sensitive data
````
SELECT
    *
FROM
(
    select
      directSources.value: "objectId"::varchar as source_object_id,
      directSources.value: "objectName"::varchar as source_object_name,
      directSources.value: "columnName"::varchar as source_column_name,
      'DIRECT' as source_column_type,
      om.value: "objectName"::varchar as target_object_name,
      columns_modified.value: "columnName"::varchar as target_column_name
    from
      (
        select
          *
        from
          snowflake.account_usage.access_history
      ) t,
      lateral flatten(input => t.OBJECTS_MODIFIED) om,
      lateral flatten(input => om.value: "columns", outer => true) columns_modified,
      lateral flatten(
        input => columns_modified.value: "directSources",
        outer => true
      ) directSources
    union
// 2
    select
      baseSources.value: "objectId" as source_object_id,
      baseSources.value: "objectName"::varchar as source_object_name,
      baseSources.value: "columnName"::varchar as source_column_name,
      'BASE' as source_column_type,
      om.value: "objectName"::varchar as target_object_name,
      columns_modified.value: "columnName"::varchar as target_column_name
    from
      (
        select
          *
        from
          snowflake.account_usage.access_history
      ) t,
      lateral flatten(input => t.OBJECTS_MODIFIED) om,
      lateral flatten(input => om.value: "columns", outer => true) columns_modified,
      lateral flatten(
        input => columns_modified.value: "baseSources",
        outer => true
      ) baseSources
) col_lin
   WHERE
       (SOURCE_OBJECT_NAME = 'HRZN_DB.HRZN_SCH.CUSTOMER' OR TARGET_OBJECT_NAME='HRZN_DB.HRZN_SCH.CUSTOMER')
    AND
        (SOURCE_COLUMN_NAME IN (
                SELECT
                    COLUMN_NAME
                FROM
                (
                    SELECT
                        *
                    FROM TABLE(
                      HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
                        'HRZN_DB.HRZN_SCH.CUSTOMER',
                        'table'
                      )
                    )
                )
                WHERE TAG_NAME IN ('SEMANTIC_CATEGORY','PRIVACY_CATEGORY','DATA_CLASSIFICATION') 
            )
            OR
            TARGET_COLUMN_NAME IN (
                SELECT
                    COLUMN_NAME
                FROM
                (
                    SELECT
                        *
                    FROM TABLE(
                      HRZN_DB.INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS(
                        'HRZN_DB.HRZN_SCH.CUSTOMER',
                        'table'
                      )
                    )
                )
                WHERE TAG_NAME IN ('SEMANTIC_CATEGORY','PRIVACY_CATEGORY','DATA_CLASSIFICATION') --Enter the relevant tag(s) to check against.
            )
            );
````
    
- How many queries have accessed each of our tables indirectly?
````
SELECT 
    base.value:"objectName"::STRING AS object_name,
    COUNT(DISTINCT query_id) AS number_of_queries
FROM snowflake.account_usage.access_history,
LATERAL FLATTEN (input => base_objects_accessed) base,
LATERAL FLATTEN (input => direct_objects_accessed) direct,
WHERE 1=1
    AND object_name ILIKE 'HRZN%'
    AND object_name <> direct.value:"objectName"::STRING -- base object is not direct object
GROUP BY object_name
ORDER BY number_of_queries DESC;
````
> 
>Direct Objects Accessed: Data objects directly named in the query explicitly.
Base Objects Accessed: Base data objects required to execute a query.
 
 > Clean up (Optional).
 >Create a new worksheet named 99_lab_teardown. Copy and paste the entire Teardown Script at [ 99-lab-teardown.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/99-lab-teardown.sql) 
<!-- ------------------------ -->
## Semantic Views for AI Analytics

### Overview: Data Governor 

Semantic views are database objects that enable natural language querying via Cortex Analyst while automatically enforcing existing governance policies. In this section, you'll create a semantic view with dimensions, metrics, and facts that inherits all masking and row access policies from underlying tables.

In Snowsight create a new worksheet and rename it `4_Semantic_View_Governance`. Copy and paste each code block below and execute. You can also find the entire script at [4-Semantic-View-Governance.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/4-Semantic-View-Governance.sql)

### Create a Semantic View

Create a semantic view that defines business-friendly dimensions and metrics:

````
USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

CREATE OR REPLACE SEMANTIC VIEW CUSTOMER_ORDER_ANALYTICS
  TABLES (
    customers AS HRZN_DB.HRZN_SCH.CUSTOMER
      PRIMARY KEY (ID)
      WITH SYNONYMS ('customer', 'clients', 'buyers'),
    orders AS HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
      PRIMARY KEY (ORDER_ID)
  )
  RELATIONSHIPS (
    orders_to_customers AS
      orders (CUSTOMER_ID) REFERENCES customers (ID)
  )
  DIMENSIONS (
    customers.customer_name AS CONCAT(FIRST_NAME, ' ', LAST_NAME),
    customers.email_address AS EMAIL,
    customers.phone AS PHONE_NUMBER,
    customers.location_state AS STATE,
    orders.order_date AS ORDER_TS
  )
  FACTS (
    orders.order_total_fact AS ORDER_TOTAL
      WITH SYNONYMS ('revenue', 'sales', 'amount')
      COMMENT 'Total dollar value of individual orders',
    orders.order_tax_fact AS ORDER_TAX
      WITH SYNONYMS ('tax', 'tax amount')
      COMMENT 'Tax amount for individual orders'
  )
  METRICS (
    orders.total_revenue AS SUM(orders.order_total_fact)
      WITH SYNONYMS ('total sales', 'revenue total')
      COMMENT 'Sum of all order totals',
    orders.total_orders AS COUNT(ORDER_ID)
      COMMENT 'Count of orders'
  );
````

### Query the Semantic View

Use the SEMANTIC_VIEW() function to query:

````
-- Total revenue by state
SELECT * FROM SEMANTIC_VIEW(
    CUSTOMER_ORDER_ANALYTICS
    DIMENSIONS customers.location_state
    METRICS orders.total_revenue, orders.total_orders
)
ORDER BY TOTAL_REVENUE DESC;
````

### Verify Policy Inheritance

Test as different roles to see governance in action:

````
-- As HRZN_DATA_GOVERNOR - see all data
SELECT * FROM SEMANTIC_VIEW(
    CUSTOMER_ORDER_ANALYTICS
    DIMENSIONS customers.customer_name, customers.email_address, customers.location_state
    METRICS orders.total_revenue
) LIMIT 5;

-- Switch to restricted role
USE ROLE HRZN_DATA_USER;

-- Email should be MASKED, only MA state visible (row access policy)
SELECT * FROM SEMANTIC_VIEW(
    CUSTOMER_ORDER_ANALYTICS
    DIMENSIONS customers.customer_name, customers.email_address, customers.location_state
    METRICS orders.total_revenue
) LIMIT 5;
````

> 
>Notice: Email column shows masked values and only Massachusetts (MA) state records are visible. This happens automatically - no special AI policy needed!

### Use with Cortex Analyst

To use in Snowsight Cortex Analyst:

1. Open Snowsight → **Projects** → **Cortex Analyst**
2. Select semantic view: `HRZN_DB.HRZN_SCH.CUSTOMER_ORDER_ANALYTICS`
3. Ask natural language questions:
   - "What are the total sales by state?"
   - "Who are my top 10 customers by revenue?"
   - "Get me the full names and phone numbers of our ten highest billing customers per state"

> 
>Key Governance Benefit: If logged in as HRZN_DATA_USER, the AI returns MASKED emails and only MA customers—no additional configuration needed!

**Key Takeaways:**
- Semantic Views are SQL objects created with CREATE SEMANTIC VIEW
- Policy inheritance automatic - masking and row access policies apply to AI queries
- Query with SEMANTIC_VIEW() function or Cortex Analyst UI
- Lineage tracked in OBJECT_DEPENDENCIES

<!-- ------------------------ -->
## AI-Powered Governance Automation

### Overview: Data Governor 

In Section 2, you used AI-powered classification with CLASSIFICATION_PROFILE and custom tag mapping to automatically classify and protect structured data. Now we'll extend governance to unstructured data using AI_REDACT to remove PII from free-form text like customer feedback.

Create a new worksheet named `5_Cortex_AI_Redact`. Copy and paste each code block below and execute. You can also find the entire script at [5-Cortex-AI-Redact.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/5-Cortex-AI-Redact.sql)

### Recap: AI Classification from Section 2

In Section 2, we created:
- **DATA_CLASSIFICATION tag** with 5-tier taxonomy (PII, RESTRICTED, SENSITIVE, INTERNAL, PUBLIC)
- **Classification profile with tag_map** that maps native categories to our custom tag
- **Tag propagation** enabled via PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT

These tags and policies automatically apply to downstream tables, which we'll verify in this section.

### AI_REDACT for Unstructured Customer Feedback

Traditional masking policies work on structured columns, but what about free-form text containing PII? AI_REDACT solves this by automatically detecting and removing 50+ PII types from unstructured text.

#### Add Customer Feedback Column

Add a column to CUSTOMER_ORDERS to store unstructured customer feedback:

````
USE ROLE HRZN_DATA_GOVERNOR;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

-- Add feedback column
ALTER TABLE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS 
ADD COLUMN IF NOT EXISTS CUSTOMER_FEEDBACK VARCHAR;

-- Populate with sample feedback containing PII
UPDATE HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
SET CUSTOMER_FEEDBACK = 
    CASE 
        WHEN MOD(ORDER_ID::INT, 10) = 0 THEN 
            'Customer John Smith called from 555-123-4567 about order. Email: john.smith@email.com. Very satisfied!'
        WHEN MOD(ORDER_ID::INT, 10) = 1 THEN 
            'Jane Doe (jane.doe@company.com) requested refund. Phone: (555) 987-6543. Issue resolved.'
        WHEN MOD(ORDER_ID::INT, 10) = 2 THEN
            'Michael Johnson (SSN: 123-45-6789) reported billing error. Contact: mjohnson@example.com, 555-234-5678'
        WHEN MOD(ORDER_ID::INT, 10) = 3 THEN
            'Sarah Williams called regarding delivery to 123 Main St, Boston MA 02101. Phone 555-345-6789.'
        WHEN MOD(ORDER_ID::INT, 10) = 4 THEN
            'Order expedited for Robert Brown (DOB: 1985-06-15). Credit card ending 4532 charged.'
        WHEN MOD(ORDER_ID::INT, 10) = 5 THEN
            'Dr. Emily Chen (emily.chen@hospital.org) placed rush order for medical supplies. Contact: 555-456-7890'
        WHEN MOD(ORDER_ID::INT, 10) = 6 THEN
            'Complaint from David Martinez (DL: CA-D1234567) about damaged packaging. Email: dmartinez@gmail.com'
        WHEN MOD(ORDER_ID::INT, 10) = 7 THEN
            'VIP customer Lisa Thompson (loyalty #98765) requested gift wrap. Ship to 456 Oak Ave, Suite 200.'
        WHEN MOD(ORDER_ID::INT, 10) = 8 THEN
            'Return processed for James Wilson. Refund to card ending 8901. Phone callback requested: 555-567-8901'
        WHEN MOD(ORDER_ID::INT, 10) = 9 THEN
            'Corporate order from Acme Corp, attn: Patricia Lee (patricia.lee@acme.com). PO#: AC-2024-789'
        ELSE 
            'Standard order processed. No issues reported.'
    END
WHERE CUSTOMER_FEEDBACK IS NULL;
````

#### Demonstrate AI_REDACT

Use AI_REDACT to automatically remove PII from customer feedback:

````
-- View original vs redacted feedback
SELECT 
    ORDER_ID,
    CUSTOMER_FEEDBACK as original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(CUSTOMER_FEEDBACK) as redacted_feedback
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS 
WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
LIMIT 5;
````

>
>Result: Names, emails, phone numbers, addresses, SSNs, and dates are automatically replaced with tokens like [NAME], [EMAIL], [PHONE_NUMBER], [ADDRESS], [SSN], [DATE_OF_BIRTH]!

#### Create Pre-Computed Redacted Table

For production workloads, pre-compute redaction rather than calling AI_REDACT in views (which would be expensive on every query):

````
USE ROLE SYSADMIN;

-- Create table with both original and redacted columns
-- Limited to 100 rows for demo performance
CREATE OR REPLACE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED AS
SELECT 
    ORDER_ID,
    CUSTOMER_ID,
    ORDER_TS,
    CUSTOMER_FEEDBACK as original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(CUSTOMER_FEEDBACK) as redacted_feedback,
    CURRENT_TIMESTAMP() as redacted_at,
    CURRENT_USER() as redacted_by
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS 
WHERE CUSTOMER_FEEDBACK IS NOT NULL
LIMIT 100;

-- View the table
SELECT ORDER_ID, original_feedback, redacted_feedback 
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED 
LIMIT 5;
````

>
>Performance Note: We limit to 100 rows for demo purposes. In production, run AI_REDACT in batch jobs (e.g., via scheduled tasks) rather than on every query.

#### Verify Tag Propagation

Check if DATA_CLASSIFICATION tags propagated from CUSTOMER_ORDERS to our new CUSTOMER_FEEDBACK_REDACTED table:

````
-- Query tag references for the new table
SELECT 
    OBJECT_NAME as TABLE_NAME,
    COLUMN_NAME,
    TAG_VALUE as CLASSIFICATION_LEVEL
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
    AND OBJECT_SCHEMA = 'HRZN_SCH'
    AND OBJECT_NAME = 'CUSTOMER_FEEDBACK_REDACTED'
    AND TAG_NAME = 'DATA_CLASSIFICATION'
ORDER BY COLUMN_NAME;
````

>
>Note: ACCOUNT_USAGE views have up to 2-hour latency. You can also check immediately using INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS.

#### Create Secure View with Role-Based Access

Create a secure view that shows original feedback to governors and redacted feedback to others:

````
-- Efficient secure view using pre-computed columns
CREATE OR REPLACE SECURE VIEW HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE AS
SELECT 
    ORDER_ID,
    CUSTOMER_ID,
    ORDER_TS,
    CASE 
        WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR', 'ACCOUNTADMIN') 
        THEN original_feedback
        ELSE redacted_feedback
    END as CUSTOMER_FEEDBACK,
    redacted_at,
    redacted_by
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED;
````

Test the secure view as different roles:

````
-- As HRZN_DATA_GOVERNOR (sees original feedback)
USE ROLE HRZN_DATA_GOVERNOR;
SELECT ORDER_ID, CUSTOMER_FEEDBACK 
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE 
LIMIT 5;

-- As HRZN_DATA_USER (sees redacted feedback)
USE ROLE HRZN_DATA_USER;
SELECT ORDER_ID, CUSTOMER_FEEDBACK 
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE 
LIMIT 5;
````

>
>Key Benefit: The view simply switches between pre-computed columns - no expensive AI_REDACT calls on query time!

#### Sentiment Analysis on Redacted Data

Demonstrate that AI analytics work on redacted data:

````
USE ROLE HRZN_DATA_USER;

-- Run sentiment analysis on redacted feedback
SELECT 
    ORDER_ID,
    CUSTOMER_FEEDBACK as redacted_text,
    SNOWFLAKE.CORTEX.SENTIMENT(CUSTOMER_FEEDBACK) as sentiment_score
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE 
WHERE CUSTOMER_FEEDBACK NOT LIKE 'Standard order%'
LIMIT 10;
````

>
>Result: Sentiment analysis works on redacted text because the meaning is preserved even though PII is removed.

#### Business Insights from Redacted Feedback

Demonstrate extracting business insights without exposing PII:

````
USE ROLE HRZN_DATA_USER;

-- Extract common themes/issues without PII
SELECT 
    COUNT(*) as feedback_count,
    ROUND(AVG(SNOWFLAKE.CORTEX.SENTIMENT(CUSTOMER_FEEDBACK)), 3) as avg_sentiment,
    CASE 
        WHEN CUSTOMER_FEEDBACK ILIKE '%refund%' THEN 'Refund Request'
        WHEN CUSTOMER_FEEDBACK ILIKE '%delivery%' THEN 'Delivery Issue'
        WHEN CUSTOMER_FEEDBACK ILIKE '%billing%' THEN 'Billing Issue'
        WHEN CUSTOMER_FEEDBACK ILIKE '%satisfied%' THEN 'Positive Feedback'
        WHEN CUSTOMER_FEEDBACK ILIKE '%rush%' OR CUSTOMER_FEEDBACK ILIKE '%expedited%' THEN 'Rush Order'
        ELSE 'General'
    END as feedback_category
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE
GROUP BY feedback_category
ORDER BY feedback_count DESC;
````

>
>Key Insight: Business teams can analyze feedback patterns and sentiment without ever seeing customer PII!

### Natural Language Governance Queries

Use Cortex Code to query governance metadata:

> 
>Open Snowsight and click the Cortex Code icon, then ask:
>
>Classification & Tags:
>- "What tags have been applied to the CUSTOMER_FEEDBACK_REDACTED table?"
>- "Show me all columns in HRZN_DB that are classified as PII"
>
>Masking & Redaction:
>- "Which tables use AI_REDACT for PII protection?"
>- "How many rows in CUSTOMER_FEEDBACK_REDACTED have been redacted?"
>
>Governance Gaps:
>- "Which columns contain email addresses but don't have masking policies?"
>
>Note: Cortex Code understands your database schema and writes SQL to answer your questions!

### Classification Tags in Snowsight

> 
>Switch to the Snowsight UI to see the classification results:
>
>STEP 1: Navigate to the CUSTOMER_FEEDBACK_REDACTED table
>- Go to Data > Databases > HRZN_DB > HRZN_SCH > Tables > CUSTOMER_FEEDBACK_REDACTED
>- Click on the table name to open detail view
>
>STEP 2: View propagated tags
>- Look at the Columns tab
>- You'll see DATA_CLASSIFICATION tags propagated from CUSTOMER_ORDERS:
>  - CUSTOMER_ID: PII or RESTRICTED (depending on classification)
>  - ORDER_TS: INTERNAL or SENSITIVE
>- System tags (SEMANTIC_CATEGORY, PRIVACY_CATEGORY) do NOT propagate
>
>Note: This demonstrates the BYOT (Bring Your Own Tags) pattern - only user-defined tags propagate!

**Key Takeaways:**
- AI_REDACT: Production-grade PII removal for unstructured text (50+ PII types)
- Pre-Computed Redaction: Create redacted tables in batch, not expensive views
- Tag Propagation: DATA_CLASSIFICATION tags from Section 2 automatically flow to new tables
- Role-Based Access: Secure views switch between original/redacted based on CURRENT_ROLE()
- AI Analytics Compatible: Sentiment analysis and other AI functions work on redacted data
- Performance: AI_REDACT is expensive - use pre-computed tables and batch jobs

<!-- ------------------------ -->
## Natural Language Governance Queries


### Overview: Data Governor 

Query governance metadata using natural language with Cortex Analyst or manual SQL. This section demonstrates governance reporting and compliance queries.

Create a new worksheet named `6_Natural_Language_Governance`. You can find the complete script with additional examples at [6-Natural-Language-Governance.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/hol-lab/6-Natural-Language-Governance.sql)

### Example Governance Questions

These questions can be asked using Cortex Analyst (natural language) or run as SQL:

**Compliance & Audit:**
1. "Which tables have PII but no masking policy?"
2. "Who accessed PII data in the last 7 days?"
3. "What policies are applied to the CUSTOMER table?"

**Usage & Adoption:**
4. "Who are the top users accessing sensitive data?"

### Manual SQL Example

Example SQL for "Which tables have PII but no masking policy?":

````
USE ROLE HRZN_DATA_GOVERNOR;

WITH pii_tables AS (
    SELECT DISTINCT 
        OBJECT_DATABASE,
        OBJECT_SCHEMA,
        OBJECT_NAME,
        TAG_VALUE as pii_type
    FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
    WHERE TAG_NAME = 'SEMANTIC_CATEGORY'
      AND TAG_VALUE IN ('EMAIL', 'SSN', 'PHONE_NUMBER', 'CREDIT_CARD', 'NAME')
      AND DOMAIN = 'COLUMN'
      AND OBJECT_DATABASE = 'HRZN_DB'
),
masked_tables AS (
    SELECT DISTINCT
        SPLIT_PART(REF_ENTITY_NAME, '.', 3) as table_name
    FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
    WHERE POLICY_KIND = 'MASKING_POLICY'
      AND POLICY_STATUS = 'ACTIVE'
)
SELECT 
    p.OBJECT_DATABASE || '.' || p.OBJECT_SCHEMA || '.' || p.OBJECT_NAME as full_table_name,
    LISTAGG(DISTINCT p.pii_type, ', ') as pii_types,
    'HIGH RISK: No masking policy' as governance_status
FROM pii_tables p
LEFT JOIN masked_tables m ON p.OBJECT_NAME = m.table_name
WHERE m.table_name IS NULL
GROUP BY p.OBJECT_DATABASE, p.OBJECT_SCHEMA, p.OBJECT_NAME;
````

> 
>Note: ACCOUNT_USAGE views have up to 2-hour latency. Results may not appear immediately after making changes.

### Governance Coverage Query

Get an overview of your governance coverage:

````
USE ROLE HRZN_DATA_GOVERNOR;

-- Governance coverage summary
SELECT 
    'Tags Applied' as metric,
    COUNT(DISTINCT OBJECT_NAME) as coverage
FROM SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES
WHERE OBJECT_DATABASE = 'HRZN_DB'
  AND TAG_NAME = 'DATA_CLASSIFICATION'
UNION ALL
SELECT 
    'Masking Policies' as metric,
    COUNT(DISTINCT REF_ENTITY_NAME) as coverage
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
WHERE POLICY_KIND = 'MASKING_POLICY'
  AND REF_DATABASE_NAME = 'HRZN_DB'
UNION ALL
SELECT 
    'Row Access Policies' as metric,
    COUNT(DISTINCT REF_ENTITY_NAME) as coverage
FROM SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES
WHERE POLICY_KIND = 'ROW_ACCESS_POLICY'
  AND REF_DATABASE_NAME = 'HRZN_DB';
````

**Key Takeaways:**
- Democratizes Governance: Non-technical users can audit compliance
- SQL or Natural Language: Choose the interface that works for you
- Real-Time Insights: Query current governance state
- Audit-Ready: Generate compliance reports on demand

<!-- ------------------------ -->
## Conclusion And Resources

You did it! In this comprehensive lab, you have seen how Horizon:
- Secures data with role-based access control, governance policies, and more 
- Monitors data quality with both out-of-the-box and custom metrics
- Audits data usage through Access History and Schema Change Tracking
- Understands the flow of data through object dependencies and lineage
- Automates PII discovery with AI-powered classification
- Enables governed AI analytics via semantic views
- Democratizes governance with natural language queries

### What You Learned

**Core Governance (Sections 1-3):**
- How to create stages, databases, tables, views, and virtual warehouses
- As a Data Engineer, how to implement Data Quality Monitoring and data metric functions
- As a Data Governor, how to apply column-level and row-level security and use projection and aggregation constraints
- As a Governor Admin, how to use data lineage and dependencies to audit access and understand the flow of data

**AI Governance Extensions (Sections 4-6):**
- As a Data Governor, how to create semantic views where governance policies are automatically enforced
- How to use CLASSIFICATION_PROFILE and AI_REDACT for automated governance
- How fine-grained access controls are honored when accessing data via AI
- How to query governance metadata using Cortex Code and Cortex Analyst

### Clean Up (Optional)

To remove all lab objects, create a new worksheet named `99_lab_teardown` and run the [99-lab-teardown.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake/blob/main/99-lab-teardown.sql) script.

### Resources

**Horizon & Core Governance:**
- Check out more Horizon [resources](/en/data-cloud/horizon/) and [documentation](https://docs.snowflake.com/en/guides-overview-govern)
- Read the [Definitive Guide to Governance in Snowflake](/resource/the-definitive-guide-to-governance-in-snowflake)

**AI Governance Features:**
- Learn about [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- Explore [AI_REDACT](https://docs.snowflake.com/en/sql-reference/functions/ai_redact)
- Read about [Native Classification](https://docs.snowflake.com/en/user-guide/classification-auto)
- Discover [Cortex Code](https://docs.snowflake.com/en/user-guide/ui-snowsight/cortex-code)

**Community & Learning:**
- Join the [Snowflake Community](https://community.snowflake.com/s/)
- Sign up for [Snowflake University](https://community.snowflake.com/s/snowflake-university)
- Fork the [Repo on GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-horizon-data-governance-in-snowflake)
- [Read the Blog](https://medium.com/snowflake/re-imagine-data-governance-with-snowflake-horizon-and-powered-by-ai-9ac1ead51b6f)
- [Watch the Demo](https://youtu.be/CML-mhhCvOA?list=TLGGiSkeWqigbJ4yNDA5MjAyNQ)
