summary: Example Provider Accelerator Approach 2
id: provider_accelerator_approach_2
categories: Data Exchange
tags: medium
status: Published 
Feedback Link: https://developers.snowflake.com

# Example Provider Accelerator Approach 2
<!-- ------------------------ -->
## Complete Base Setup
Duration: 1

The steps in this codelab assume you have already completed the base setup codelab located [here](../provider_accelerator_base_setup).

<!-- ------------------------ -->
## Create an External Table
Duration: 10

To create external tables to point to your data from Snowflake, run the SQL code below using the `create_ext_table.sql` file.
- Replace `MY_EXT_TABLE` with your preferred name
- Replace `MY_DB`, `MY_SCHEMA`, and `MY_STAGE` with the names you used in previous steps
This template follows the documentation located here:
- [Create External Table](https://docs.snowflake.com/en/sql-reference/sql/create-external-table.html)
- [Data Types](https://docs.snowflake.com/en/sql-reference/data-types.html)

Query performance against external tables is highly dependent on a good partitioning scheme within your object store folder structures based on how your users will query your data, or based on how your materialized views will materialized the data in Snowflake as new data arrives. It is common to partition data by tenant (user, company, etc) and time (year, month, day), though your exact needs will vary.

Note that this is a single basic example external table with a few columns representing the more common data types; it will need to be customized to your data and the columns in your data and repeated for as many tables as you need. More advanced options are available in the documentation.

### Create a File Format
You will create one or more file formats for your data files, depending on how many different formats you use. The example below creates a CSV file format named `MY_FORMAT` that defines the following rules for data files: 
- fields are delimited using the pipe character ( `|` ), 
- files include a single header line that will be skipped, 
- the strings NULL and null will be replaced with NULL values, 
- empty strings will be interpreted as NULL values, 
- files will be compressed/decompressed using GZIP compression. 

Your rules may be different - parameters can be changed or omitted based on your files.

#### Create a File Format
```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE FILE FORMAT MY_FORMAT
TYPE = CSV
FIELD_DELIMITER = '|'
SKIP_HEADER = 1
NULL_IF = ('NULL', 'null')
EMPTY_FIELD_AS_NULL = TRUE
COMPRESSION = GZIP
;
```

### Create an External Table
To create one or more external tables to point to your data from Snowflake, run the SQL code below.
- Replace `MY_FILE_PATH` with your preferred value
- Replace `MY_FORMAT` with the name you used in the above step

This examples assumes that data files are organized into a `<stage>/<tenant_id>/<year>/<month>/<day_num>` structure. Note the use of `METADATA$FILENAME` to extract parts of the file path. You may need to change the numbers in the `SPLIT_PART` function based on your file path construction and the value of `MY_FILE_PATH` below, if any. There is currently no option to reverse engineer a table structure from a file, so this step must be done before you can query your data through Snowflake. 

#### Create an External Table
```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE EXTERNAL TABLE MY_EXT_TABLE (
TENANT_ID NUMBER AS TO_NUMBER(SPLIT_PART(METADATA$FILENAME, '/', 2)) COMMENT 'A NUMBER COLUMN REPRESENTING THE TENANT_ID DERIVED FROM THE FILE PATH',
COL2 DATE AS TO_DATE(SPLIT_PART(METADATA$FILENAME, '/', 3) || '/' || SPLIT_PART(METADATA$FILENAME, '/', 4) || '/' || SPLIT_PART(METADATA$FILENAME, '/', 5), 'YYYY/MM/DD') COMMENT 'A DATE COLUMN CREATED BY CONCATENATING THE PARTS OF THE FILE PATH THAT REPRESENT YEAR, MONTH, AND MONTH DAY NUMBER',
COL3 STRING AS (VALUE:C1::STRING) COMMENT 'A STRING COLUMN THAT REFERENCES THE FIRST COLUMN IN THE CSV',
COL4 STRING AS (VALUE:C2::STRING) COMMENT 'A STRING COLUMN THAT REFERENCES THE SECOND COLUMN IN THE CSV',
COL5 NUMBER AS (VALUE:C3::NUMBER) COMMENT 'A NUMBER COLUMN THAT REFERENCES THE THIRD COLUMN IN THE CSV',
) 
PARTITION BY (COL1, COL2)
LOCATION = @MY_STAGE/<MY_FILE_PATH>
FILE_FORMAT = (FORMAT_NAME = MY_FORMAT)
REFRESH_ON_CREATE = TRUE;
COMMENT='A TABLE COMMENT'
;
```

<!-- ------------------------ -->
## Automate the Refresh of the External Table
Duration: 5

To refresh your external table on a schedule, run the SQL below using the `refresh_ext_table.sql` file.
- Replace `MY_EXT_TABLE`, `MY_DB`, `MY_SCHEMA`, `MY_WH` with the names you used in previous steps
- Replace `MY_TASK` with your preferred names

This template follows the documentation located here:
- [Alter External Table](https://docs.snowflake.com/en/sql-reference/sql/alter-external-table.html)
- [Create Task](https://docs.snowflake.com/en/sql-reference/sql/create-task.html)

This script creates a Snowflake task to refresh the external table on a scheduled or interval basis. You should determine the type of task (schedule or interval) based on how frequently new files are added to object store and how frequently you want to expose new data to your consumers. 
- Tasks are always created in a suspended state and must be resumed before they will run. 
- The example below assumes that this task will be run on a cron schedule of every night at 2am America/Los Angeles time, reflected by the format which is documented in the link above. You can customize the schedule to your needs. 
- Tasks can also be scheduled to run on an interval measured in minutes. See the documentation for more details.

### Create and Resume the Task
```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE TASK MY_TASK
WAREHOUSE = MY_WH
SCHEDULE = 'USING CRON 0 2 * * * America/Los_Angeles'
AS 
ALTER EXTERNAL TABLE MY_EXT_TABLE REFRESH;
;

ALTER TASK MY_TASK RESUME;
```

### Monitor the Task History (Last 10 Runs in the Last Hour)
```sql
USE DATABASE MY_DB;

SELECT *
	FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
		SCHEDULED_TIME_RANGE_START=>DATEADD('HOUR',-1,CURRENT_TIMESTAMP()),
		RESULT_LIMIT => 10,
		TASK_NAME=>'MY_TASK'));
```

<!-- ------------------------ -->
## Create a Secure Materialized View on the External Table
Duration: 3

To create one or more materialized views to create highly performant copies of your external tables in Snowflake, run the SQL below using the `create_matview.sql` file.
- Replace `MY_EXT_TABLE_MV` with your value. The `MV` suffix can be used to distinguish materialized views from base tables, but is optional.
- Replace `MY_WH`, `MY_DB`, `MY_SCHEMA`, and `MY_EXT_TABLE` with the names you used in previous steps.

This template follows the documentation located here:
- [About Materialized Views](https://docs.snowflake.com/en/user-guide/views-materialized.html)
- [Create Materialized View](https://docs.snowflake.com/en/sql-reference/sql/create-materialized-view.html)
- [About Secure Views](https://docs.snowflake.com/en/user-guide/views-secure.html)

The following should be considered about materialized views
- A Snowflake materialized view will typically create a new physical copy of the data from a base table, model it in a different form (as defined by a query), and store it as a new queryable object that looks and feels like a regular table. However, under the covers, the materialized view looks for new updates to the base table and updates itself after those updates to the base table occurs. Queries run against a materialized view when it hasn't yet updated itself from changes to the base external table will not lock, but will run more slowly than after the materialized view updates itself. This experience should be factored into your external table refresh schedule.
- When a materialized view is pointed to an external table, the materialized view also serves as the mechanism to load the external data into Snowflake to create a more performant object to query than the underlying external table, which will be slower to query.
- The creation of the materialized view in this approach is technically optional, but is highly recommended to a) improve performance for your consumers, and b) to better control multi-region data sharing (as covered in share_multi_region.sql). 
- The query below used to define the materialized view has an optional WHERE clause that defines which tenants in a multi-tenant external table will be included in the materialized view. This is helpful when you want to isolate tenants from each other and/or you want to control which tenants' data gets loaded into which cloud/region. If you are not using a multi-tenant design, the WHERE clause and the TENANT_COL in the SELECT clause can be omitted.
- The query below shows a simple selection of all rows. More sophisticated aggregation and transformation queries can be used.

### Create Secure Materialized View
```sql
USE WAREHOUSE MY_WH;
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE SECURE MATERIALIZED VIEW MY_EXT_TABLE_MV AS 
SELECT COL1, COL2, COLN, TENANT_COL FROM MY_EXT_TABLE
-- WHERE TENANT_COL IN (<VALUE1>,<VALUE2>,<VALUEN>)
-- WHERE TENANT_COL = <VALUE>
;
```

<!-- ------------------------ -->
## Create a Share
Duration: 5

To create a share object to allow other Snowflake customers to access your data, run the SQL below using the  `create_share.sql` file.
- Replace `MY_DB`, `MY_SCHEMA`, `MY_EXT_TABLE` and `MY_EXT_TABLE_MV` with the names you used in previous steps. 
- Replace `MY_SHARED_SCHEMA`, `MY_SECURE_VIEW` and `MY_SHARE` with your preferred names.

This template follows the documentation located here:
- [About Shares](https://docs.snowflake.com/en/user-guide-data-share.html)
- [Create Share](https://docs.snowflake.com/en/sql-reference/sql/create-share.html)
- [About Secure Views](https://docs.snowflake.com/en/user-guide/views-secure.html)

Note that it is good practice to abstract the objects that other Snowflake customers can see through the use of Secure Views rather than sharing objects directly. Secure Views can be simple views or have account-based row-level security built into them (one Snowflake customer account see one slice of data, another Snowflake customer account sees a different slice). This script inclues an example of setting up row-level security at the bottom of the script.

This accelerator also assumes that you are operating as a user with the ACCOUNTADMIN role. If you have implemented more fine-grained role permissions in Snowflake, there are likely tweaks to the code below that will be required based on how you have implemented roles and privileges.

### Create a Share Without Account-based Row-level Security
#### Create a Schema for Sharing Objects and a Secure View in the Schema
```sql
USE DATABASE MY_DB;

CREATE OR REPLACE SCHEMA MY_SHARED_SCHEMA;

USE SCHEMA MY_DB.MY_SHARED_SCHEMA;

CREATE OR REPLACE SECURE VIEW MY_SECURE_VIEW AS 
SELECT COL1, COL2, COLN FROM MY_DB.MY_SCHEMA.MY_EXT_TABLE;
-- Optionally select from MY_DB.MY_SCHEMA.MY_EXT_TABLE_MV
```

#### Create the Share and Examine the Share Metadata
```sql
CREATE OR REPLACE SHARE MY_SHARE;

GRANT USAGE ON DATABASE MY_DB TO SHARE MY_SHARE;

GRANT USAGE ON SCHEMA MY_DB.MY_SHARED_SCHEMA TO SHARE MY_SHARE;

GRANT SELECT ON VIEW MY_SECURE_VIEW TO SHARE MY_SHARE;

SHOW SHARES LIKE 'MY_SHARE%';

DESC SHARE MY_SHARE;
```

### Create a Share With Account-based Row-level Security
This template follows the documentation located here:
- [Data Sharing with Secure Views](https://docs.snowflake.com/en/user-guide/data-sharing-secure-views.html)

Securing a multi-tenant object requires a `TENANT_ID` column in the primary table to be shared. Additionally, an entitlements table defines which Snowflake accounts can see which tenants. There does not have to be a 1:1 relationship between `TENANT_ID` and Snowflake account, but that is the most common setup, which is reflected below.

#### Create Entitlements Table
```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE TABLE SHARING_ENTITLEMENTS (
TENANT_ID STRING COMMENT 'KEY COLUMN THAT CONTROLS ROW VISIBILITY ON BASE TABLES',
SNOWFLAKE_ACCOUNT STRING COMMENT 'COLUMN THAT CONTROLS WHICH SNOWFLAKE ACCOUNT CAN SEE WHICH TENANT'
)
COMMENT 'A TABLE USED TO ENFORCE ROW-LEVEL SECURITY ON SHARED MULTI-TENANT TABLES'
;

Populate this table based on your values. Note that because sharing works specifically within cloud/region, the SNOWFLAKE_ACCOUNT value does not need to include any cloud/region designation. An example insert is shown below; replace the placeholder values with your own values.

#### Populate the Entitlements Table
```sql
INSERT INTO SHARING_ENTITLEMENTS VALUES ('<TENANT_ID1','<SNOWFLAKE_ACCOUNT1>');
```

Create a secure view that joines the entitlement table with the base table using the CURRENT_ACCOUNT() function.

#### Create Secure View
```sql
USE SCHEMA MY_DB.MY_SHARED_SCHEMA;

CREATE OR REPLACE SECURE VIEW MY_SECURE_VIEW AS
SELECT COL1, COL2, COLN FROM MY_DB.MY_SCHEMA.MY_EXT_TABLE_MV EXT
JOIN MY_DB.MY_SCHEMA.SHARING_ENTITLEMENTS SE ON EXT.TENANT_ID = SE.TENANT_ID
AND SE.SNOWFLAKE_ACCOUNT = CURRENT_ACCOUNT()
;
```

#### Create the Share and Examine the Share Metadata
```sql
CREATE OR REPLACE SHARE MY_SHARE;

GRANT USAGE ON DATABASE MY_DB TO SHARE MY_SHARE;

GRANT USAGE ON SCHEMA MY_DB.MY_SHARED_SCHEMA TO SHARE MY_SHARE;

GRANT SELECT ON VIEW MY_SECURE_VIEW TO SHARE MY_SHARE;

SHOW SHARES LIKE 'MY_SHARE%';

DESC SHARE MY_SHARE;
```

<!-- ------------------------ -->
## Create a Listing in the Marketplace
Duration: 5

There is no SQL to run for this step (yet) until listings can be created with SQL, but you can visit the documentation page below to walk through your listing creation:
- [Create Listing](https://docs.snowflake.com/en/user-guide/marketplace-managing-data-listings.html)

<!-- ------------------------ -->
## Prepare for Sharing in Multiple Clouds/Regions
Duration: 10

To prepare yourself to share in other clouds/regions based on the cloud/region where your customers have Snowflake accounts, read the following and execute the SQL below.
- Replace `MY_USER`, `MY_EMAIL`, and `MY_EDITION` with your existing values.
- Replace `MY_SECONDARY_ACCOUNT` and `MY_SECONDARY_REGION` with your preferred values.

This approach requires you to "clone" the setup in your primary account to all other Snowflake accounts that you operate. This is one benefit of this approach - each Snowflake account is the same except for a few exceptions noted below.
- The steps in this guide refer to your `PRIMARY` account, which is the first account you created, and any `SECONDARY` accounts, which are the accounts you will create below. 
- The general flow is that you will repeat the setup you did in your `PRIMARY` account to all `SECONDARY` accounts. 
- In the beginning of this script, you will set yourself up as an Organization Administrator in your `PRIMARY` account and then create any required `SECONDARY` accounts. 
- Then you will re-execute most of the steps done in prior steps.

### Using your PRIMARY account

Contact your Snowflake team to make sure you are enabled for the Organizations Preview

#### Grant yourself ORGADMIN privileges
```sql
GRANT ROLE ORGADMIN TO USER MY_USER;
```

### Create one or more accounts in various clouds/regions. 
Make sure you understand what edition of Snowflake you are using by navigating to the "Organization" area of the Snowflake UI and noting your edition
#### Create Account
```sql
USE ROLE ORGADMIN;

-- Show the list of all possible Snowflake regions and note the one you want

SHOW REGIONS;

CREATE ACCOUNT MY_SECONDARY_ACCOUNT ADMIN_NAME=MY_USER, ADMIN_PASSWORD='CHANGEM3', EMAIL='MY_EMAIL', EDITION='MY_EDITION', REGION='MY_SECONDARY_REGION', COMMENT='A COMMENT'; 
```

### Re-run Previous Setup Steps in SECONDARY Accounts
Execute the following setup steps in your `SECONDARY` Snowflake accounts based on however many accounts you created above. Additional notes are provided for each step where needed.

1. Create a virtual warehouse using the `create_warehouse.sql` file (script is at the root level).
2. Create a database and schema using the `create_database.sql` file (script is at the root level).
3. Create an external stage using the `create_stage.sql` file (script is at the root level).
	- In this step, you are pointing to the same external stage location from every account, no matter what cloud/region the external stage and the Snowflake account reside in. For example, it's possible to create an S3-based external stage in an Azure-hosted Snowflake account. The setup steps are exactly the same.
4. Create one or more external tables to point to your data from Snowflake using the `create_ext_table.sql` file.
5. Create one or more materialized views to create highly performant copies of your external tables in Snowflake using the `create_matview.sql` file.
	- In this step you are likely employing a filter (WHERE clause) in the SQL statement that defines the materialized view because you want to only materialize (ingest) the data for the customers who will be receiving a share from that account. Note that while this accelerator shows hard-coding within the WHERE clause for the materialized view statement, it is possible to use Snowflake stored procedures to dynamically generate the materialized view CREATE statement and dynamically populate the WHERE clause with values from the entitlement table, if your entitlement table in a given Snowflake account is only populated with the tenant_id values specific to that account. However, it is not possible in a Snowflake materialized view to populate the WHERE clause with a sub-select to the entitlements table. See the documentation below for an example of how to use a stored procedure to dynamically generate the materialized view create statement:
		- [Dynamically Create SQL Statement](https://docs.snowflake.com/en/sql-reference/stored-procedures-usage.html#dynamically-creating-a-sql-statement)
	- Also note that if you ever add a new sharing customer (tenant_id) to that Snowflake account, a new row will need to be added to the entitlements table and the materialized view definition will need to be recreated. This could affect sharing access while the materialized view is being recreated and should be done in off-hours when possible.
6. Create one or more shares  using the `create_share.sql` file.
7. Create a listing on the Marketplace or Exchange through the UI  using the `create_listing.sql` file (script is at the root level).
	- In this step, you will not be creating a new listing, but rather expanding the cloud/regions where the existing share is available.
8. Automate the refresh of your external tables using the `refresh_ext_table.sql` file.
