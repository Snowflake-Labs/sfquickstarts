
/***************************************************************************************************
 Advanced Data Governance: AI-Powered Sensitive Data Discovery and Protection at Scale
 Snowflake Summit Hands-on Lab

 Script:      Step 1 — Access Control & Role-Based Security (Data Engineer Persona)
 Version:     Summit HOL v1.0
 Create Date: May 2026
 Author:      Ankit Gupta
 Copyright(c): 2026 Snowflake Inc. All rights reserved.
****************************************************************************************************
 SUMMARY OF CHANGES
 Date(yyyy-mm-dd)    Author              Comments
 ------------------- ------------------- -------------------------------------------------------
 May 2026            Ankit Gupta         Initial Summit HOL
***************************************************************************************************/

/*----------------------------------------------------------------------------------
Snowflake's approach to access control combines two complementary models:

  - Discretionary Access Control (DAC):  Each object has an owner who can grant
    access to that object.
  - Role-Based Access Control (RBAC):    Access privileges are assigned to roles,
    which are in turn assigned to users.

Key concepts:
  - Securable Object:  An entity to which access can be granted (Database, Schema,
    Table, View, Warehouse, etc.). Unless explicitly granted, access is denied.
  - Role:              A container for privileges. Roles are assigned to users or
    other roles, creating a hierarchy.
  - Privilege:         A defined level of access to a securable object (SELECT,
    INSERT, USAGE, OWNERSHIP, etc.).
  - User:              A Snowflake identity, whether associated with a person or
    a service account.
----------------------------------------------------------------------------------*/


/*----------------------------------------------------------------------------------
Step 1.1 — System-Defined Roles and the Role Hierarchy

Snowflake ships with the following system roles in every account:

  ORGADMIN      — Manages operations at the organization level.
  ACCOUNTADMIN  — Top-level role; encapsulates SYSADMIN and SECURITYADMIN.
                  Should be granted only to a limited set of users.
  SECURITYADMIN — Can manage any object grant globally; creates and manages
                  users and roles.
  USERADMIN     — Dedicated to user and role management only.
  SYSADMIN      — Creates warehouses and databases. In a well-designed hierarchy,
                  all custom roles ultimately roll up to SYSADMIN.
  PUBLIC        — Automatically granted to every user and role; objects owned by
                  PUBLIC are available to everyone.

                          +---------------+
                          | ACCOUNTADMIN  |
                          +---------------+
                            ^    ^     ^
                            |    |     |
              +-------------+-+  |    ++-------------+
              | SECURITYADMIN |  |    |   SYSADMIN   |<------+
              +---------------+  |    +--------------+       |
                      ^          |     ^        ^            |
                      |          |     |        |            |
              +-------+-------+  |     |  +-----+-------+  ++------------+
              |   USERADMIN   |  |     |  | CUSTOM ROLE |  | CUSTOM ROLE |
              +---------------+  |     |  +-------------+  +-------------+
                                 |     |      ^
                                 |     |      |
                                 +-----+------+
                                        |
                                   +----+-----+
                                   |  PUBLIC  |
                                   +----------+
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_ENGINEER;
USE WAREHOUSE HRZN_WH;
USE DATABASE HRZN_DB;
USE SCHEMA HRZN_SCH;

-- View all roles currently in the account
SHOW ROLES;

-- Filter to show only the Snowflake system-defined roles
SELECT
    "name",
    "comment"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "name" IN ('ORGADMIN','ACCOUNTADMIN','SYSADMIN','USERADMIN','SECURITYADMIN','PUBLIC');


/*----------------------------------------------------------------------------------
Step 1.2 — Custom Role Creation, Grants, and SQL Variables

Now that we understand system roles, let's create a custom analyst role and walk
through the privilege grant pattern that every Snowflake role design follows.
----------------------------------------------------------------------------------*/

-- Use USERADMIN to create a new role
USE ROLE USERADMIN;

CREATE OR REPLACE ROLE HRZN_DATA_ANALYST
    COMMENT = 'Analyst role for querying lab data';

-- Switch to SECURITYADMIN to manage privilege grants
USE ROLE SECURITYADMIN;

-- Grant warehouse access to the new role
GRANT ALL ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ANALYST;
GRANT OPERATE, USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ANALYST;

-- Store the current user in a SQL variable
SET MY_USER_ID = CURRENT_USER();

-- Grant the new role to the current user
GRANT ROLE HRZN_DATA_ANALYST TO USER identifier($MY_USER_ID);

-- Switch to the analyst role and try to query the CUSTOMER table
USE ROLE HRZN_DATA_ANALYST;

-- This will FAIL — no database or schema access has been granted yet
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER;

/*
  EXPECTED ERROR:
  "Database 'HRZN_DB' does not exist or not authorized."
  The role exists but has no privileges on the database objects.
*/

-- Grant database and schema access
USE ROLE SECURITYADMIN;
GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;

/*
  Snowflake Database and Schema Grant Reference:
    MODIFY   — Alter any settings of a database or schema.
    MONITOR  — Enables DESCRIBE on the database.
    USAGE    — Use the database/schema; required to see objects inside.
    ALL      — All privileges except OWNERSHIP.
*/

-- Now grant SELECT on tables and views
GRANT SELECT ON ALL TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_ANALYST;
GRANT SELECT ON ALL VIEWS IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_ANALYST;

/*
  Table and View Privilege Reference:
    SELECT   — Execute a SELECT statement.
    INSERT   — Execute INSERT commands.
    UPDATE   — Execute UPDATE commands.
    TRUNCATE — Execute TRUNCATE TABLE commands.
    DELETE   — Execute DELETE commands.
*/

-- Try again — this time the query will succeed
USE ROLE HRZN_DATA_ANALYST;
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER;

/*
  KEY OBSERVATION — The customer table contains significant amounts of PII:
    - Names, addresses, phone numbers, email addresses
    - SSNs, credit card numbers, birthdates
    - All visible without any masking!

  This is exactly the problem we will solve in Step 2.
*/


/*----------------------------------------------------------------------------------
Step 1.3 — Explore the Raw Data

Before applying governance controls, let's understand what we're working with.
----------------------------------------------------------------------------------*/

USE ROLE HRZN_DATA_ENGINEER;
USE WAREHOUSE HRZN_WH;

-- Preview the CUSTOMER table — note all PII fields are visible
SELECT
    ID,
    FIRST_NAME, LAST_NAME,
    STREET_ADDRESS, STATE, CITY, ZIP,
    PHONE_NUMBER,
    EMAIL,
    SSN,
    BIRTHDATE,
    JOB, COMPANY,
    CREDITCARD,
    OPTIN
FROM HRZN_DB.HRZN_SCH.CUSTOMER
SAMPLE (100 ROWS);

-- Preview CUSTOMER_ORDERS — transaction data linked to customers
SELECT *
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS
LIMIT 20;

-- Summary stats
SELECT
    COUNT(*) AS total_customers,
    COUNT(DISTINCT STATE) AS distinct_states,
    SUM(CASE WHEN OPTIN = 'Y' THEN 1 ELSE 0 END) AS opted_in_customers,
    SUM(CASE WHEN OPTIN = 'N' THEN 1 ELSE 0 END) AS opted_out_customers
FROM HRZN_DB.HRZN_SCH.CUSTOMER;

/*
  KEY TAKEAWAYS — Step 1:

  - Snowflake RBAC separates role creation (USERADMIN/SECURITYADMIN) from
    privilege grants (SECURITYADMIN) and object creation (SYSADMIN).
  - Without explicit grants, no role can access any object — access denied by default.
  - The CUSTOMER table contains 15 columns of raw PII — email, SSN, credit card,
    phone, address — all fully visible to anyone with SELECT.
  - Proceed to Step 2 to classify and protect this sensitive data.
*/
