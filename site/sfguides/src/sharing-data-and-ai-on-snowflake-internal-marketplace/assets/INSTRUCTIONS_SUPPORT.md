# Instructions for support staff


## Account & Organization Setup
All accounts have an ADMIN user you can login to if needed for support - this user has ACCOUNTADMIN access

User = ADMIN

Henrik will share the password in the slack channel.


## The Lab Environment
Also, Henrik has access to the HOL backend (Dataops) and can reset the account to its original state if needed 



- Each attendee gets one acocunt with two users, one database
-- TPCH Database, SF1 schema, copied from our SNOWFLAKE_SAMPLE_DATA and persisted in each account
-- Provider - this user has acces to TPCH database and to create listings
- There are 20 Profiles created in the organization, plust the default INTERNAL
-- We will be guiding users NOT to use the INTERNAL profile, as this already contains a lot of existing listings, as it is a shared environment


## Known Errors and how to fix them
- Error: When creating AI generated listing, error = Error details: SQL compilation error: Function
'ORDERS_PER_CUSTOMER(NUMBER (38,0)) RETURN TABLE (CUSTOMER_NAME VARCHAR, COUNTRY VARCHAR, ORDERKEY NUMBER, ORDERDATE DATE, AMOUNT NUMBER)' **does not exist or not authorized**.
  - Solution: The user has not added the correct tables to the Data Listing, they need to add 6 tables (all tables except PART and REGION)
- Error: If there are problems publishing the listing first time (cannot save, and "Additional setup needed"), it's the "Grant Access" setting that is incorrect,
  - Solution: they should set "Who can access this data product" = "No Accounts or Roles are preapproved"
- Eror: When testing in Snowflake Intelligence / CoWork, you get an red box saying "**No agents available** - Reach out to your admin to learn about your organization's agents and to get access to them."
  - Solution: This is a known problem - Snowflake Intelligence still works, just ignore the message. Users can still test the data listing agent
