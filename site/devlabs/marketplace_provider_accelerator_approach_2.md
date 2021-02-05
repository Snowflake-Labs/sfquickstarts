summary: Marketplace Provider Accelerator Approach 2
id: marketplace_provider_accelerator_approach_2
categories: Data Exchange
tags: medium
status: Published 
Feedback Link: https://developers.snowflake.com

# Marketplace Provider Accelerator Approach 2
<!-- ------------------------ -->
## Overview 
Duration: 1

This accelerator contains code that can be used as templates or full automation to build the end-to-end workflow for listing data on the Snowflake Marketplace or in a private Exchange. There are multiple approaches to doing this, depending on where your data already exists as a provider. These approaches are listed below.

- Approach 1 (direct-load-from-object-store: [link](../marketplace_provider_accelerator_approach_1)) - use this approach when your data already exists in cloud object store and you are comfortable loading that data into Snowflake using traditional loading methods. This method works best when the consumer experience is consistent customer to customer and region to region. 
- Approach 2 (external-tables: this guide) - use this approach when you'd rather "point" to some of your data in object store and only load it into a given Snowflake region as customer demand dictates.

### What You’ll Learn 
- Choose the right approach
- Using the accelerator
- Create a virtual warehouse (create_warehouse.sql)
- Create a database and schema (create_database.sql)
- Create an external stage (create_stage.sql)
- Create one or more external tables (create_ext_table.sql)
- Automate the refresh of the external table (refresh_ext_table.sql)
- Create a secure materialized view on the external table (create_matview.sql)
- Create a share (create_share.sql)
- Prepare for multi-region data sharing (share_multi_region.sql)

<!-- ------------------------ -->
## Choosing the Right Approach
Duration: 5

Before moving onto the next step, it's important to reflect on which approach is best for you.

### Approach 1 (direct-load-from-object-store: [link](../marketplace_provider_accelerator_approach_1)) 
- This approach loads data into a primary Snowflake account and then replicates one or more databases to secondary Snowflake accounts in other clouds/regions for the purposes of sharing with consumers in that cloud/region.
- Snowflake replication is done at the database level and the entire database is replicated. For this reason, this approach is best when all of your consumers use the entire contents of the database, or the database is small enough that it isn't cost prohibitive to replicate to all required clouds/regions, even if all slices of the database are not required in every cloud/region.
- Replicated databases in the secondary accounts are read-only.
- Snowflake replication does produce additional storage, compute, and data transfer charges.
- Replication frequency is controlled by you using a Snowflake task. Only incremental data is replicated each time.
- You only need to create one secondary database per cloud/region. The same secondary database can be used to satisfy multiple consumers.
- However, if each consumer only sees their own unique slice of the data, and Approach 2 doesn't work for you, then you can use an adaptation of Approach 1 (Approach 1a below) that doesn't use a primary Snowflake account with replication and instead direct-loads each consumer's data into the proper cloud/region.

#### Approach 1
![Approach 1](assets/approach1.png)

#### Approach 1a
![Approach 1a](assets/approach1a.png)

### Approach 2 (external-tables: this guide) 
- This approach creates external tables that point to your files. Snowflake external tables do not ingest data, but do allow you to run queries against your files. However, these queries will perform slower than against regular Snowflake tables and when the external tables points to your files in another cloud/region, data transfer charges will be incurred with every query.
- Snowflake materialized views can be written on top of external tables to materialize (ingest) the data into Snowflake to produce faster queries and incur the data transfer costs once versus with every query. The materialized view definitions can include where clauses, allowing you to define what slice of data gets materialized.
- The setup in this approach, then, is to create Snowflake accounts in whatever clouds/regions you have consumers, create the same library of external tables in each accounted, pointed to your files in one central object store location, and create materialized views with customized where clauses in each cloud/region to control what data gets "pulled" into which cloud/region. These materialized views can be changed (or dropped) at any time as consumer demand changes.
- With this approach, however, the data refresh process is to refresh the external table (look for new files), and the presence of new files will cause the materialized view to refresh automatically. Because there can be a timing lag between those two steps, this approach is best done when the data refresh can be done in off-hours so users don't experience query slowdown during the lag.

![Approach 2](assets/approach2.png)

Now that you have more details on the different options and know your path, continue onto the next step if you want to continue Approach 2, otherwise click this [link](../marketplace_provider_accelerator_approach_1) to jump to Approach 1.


<!-- ------------------------ -->
## Using the Accelerator
Duration: 5

### Download the Accelerator
- You can download the accelerator from Github by clicking [this link](https://github.com/Snowflake-Labs/example-provider-accelerator).
- Click the green **Code** button and select **Download ZIP**.
- Unzip the files to a convenient place on your computer.

### How to use the .sql files in the accelerator
- Log into Snowflake with the credentials provided to you upon creation of the account
- Switch to the ACCOUNTADMIN role (gif below)
- Click the **Worksheet** icon in the Snowflake toolbar
- Click the **ellipses** icon on the far right of the window, select *Load Script*, and choose the appropriate .sql file (gif below)

#### Switch to ACCOUNTADMIN
![switch role to ACCOUNTADMIN](assets/switch_role.gif)
*Make sure to switch to ACCOUNTADMIN after each new login or set ACCOUNTADMIN as your default role.*

#### Load a .sql Script into the Worksheet
![load script into Worksheet](assets/load_script.gif)

### Template Standards Repeated Throughout
- All Snowflake objects in the template are named with the standard `MY_OBJECT` with `MY` designating a meaningful name and `OBJECT` as a suffix to designate what type of object (database, table, etc).
- You should replace `MY` with your preferred value, understanding you may run the same script multiple times (to create multiple tables, for example).
- The object suffix is optional but having some kind of suffix is a good practice. You can use, omit, or change any suffix at your discretion.
- You should save the new values you choose in an easily accessible place or use file-based find/replace on your computer across all script files (for example, replace `MY` with some other value).
- You should save the exact statements you execute in another set of .sql files for future reference or use. Snowflake does keep the statements in history and does save Worksheet tabs for reuse (you can rename them), but it's good to save the files outside of Snowflake and check them into source control.


<!-- ------------------------ -->
## Create a Virtual Warehouse and Database
Duration: 2

### Create a Virtual Warehouse
To create a virtual warehouse (compute) that executes queries in Snowflake, run the SQL code below using the `create_warehouse.sql` file.

- Replace `MY_WH` with your preferred warehouse name

This template follows the documentation located here: 
- [Create Warehouse](https://docs.snowflake.com/en/sql-reference/sql/create-warehouse.html)

#### Create Warehouse Code

```sql
CREATE OR REPLACE WAREHOUSE
MY_WH
WITH
WAREHOUSE_SIZE = XSMALL
AUTO_SUSPEND = 60
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE
;
```

### Create a Database
To create a database and schema that house your data in Snowflake, run the SQL code below using the `create_database.sql` file.

- Replace `MY_DB` with your preferred name
- Replace `MY_SCHEMA` with your preferred name

This template follows the documentation located here: 
- [Create Database](https://docs.snowflake.com/en/sql-reference/sql/create-database.html)
- [Create Schema](https://docs.snowflake.com/en/sql-reference/sql/create-schema.html)

#### Create Database Code

```sql
CREATE OR REPLACE DATABASE MY_DB;
```

#### Create Schema in Database Code

```sql
USE DATABASE MY_DB;

CREATE OR REPLACE SCHEMA MY_SCHEMA;
```

<!-- ------------------------ -->
## Create an External Stage
Duration: 10

To create a stage using simple access or a storage integration to allow Snowflake access to your files in object store, run the SQL code below using the `create_stage.sql` file.

- Replace `MY_STORAGE` with your preferred name
- Replace `MY_STAGE` with your preferred name
- Replace `MY_DB` and `MY_SCHEMA` with the names you used in previous steps 

This template follows the documentation located here: 
- [Create Storage Integration](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration.html)
- [Create Stage](https://docs.snowflake.com/en/sql-reference/sql/create-stage.html)

There are two approaches outlined below, each with different instructions based on the cloud provider you use to store your data in object store (scroll down to your cloud provider instructions). The first approach creates a stage with direct access using a key/pair. This approach is faster, but is less flexible and less appealing to more savvy cloud users. The second approach creates a storage integration, which is a more reusable object for a broader application of object store access, but requires more setup.
<br>

![aws](assets/aws.png)
### If Your Data is in AWS
#### Create a Storage Integration

To create a storage integration, run the SQL code below.
- Replace `STORAGE_AWS_ROLE_ARN` with your values
- Replace `STORAGE_ALLOWED_LOCATIONS` with your values
- Replace `URL` with your values

Before creating storage integration, work with your AWS administrator and follow the directions below:
- [Configure Access Permissions](https://docs.snowflake.com/en/user-guide/data-load-s3-config.html#step-1-configure-access-permissions-for-the-s3-bucket)

**Create Storage Integration and Acquire Key Values**

```sql
CREATE STORAGE INTEGRATION MY_STORAGE
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = S3
STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::001234567890:role/myrole'
ENABLED = TRUE
STORAGE_ALLOWED_LOCATIONS = ('s3://mybucket1/path1/', 's3://mybucket2/path2/')
;

DESC STORAGE INTEGRATION MY_STORAGE;
```

Provide the values of `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID` to your AWS administrator and follow the directions below:
- [Grant Snowflake Access Permissions](https://docs.snowflake.com/en/user-guide/data-load-s3-config.html#step-5-grant-the-iam-user-permissions-to-access-bucket-objects)

#### Create an External Stage

To create an external stage using the storage integration, run the SQL code below.
- Replace `URL` with your value

**Create External Stage Using Storage Integration**

```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE STAGE MY_STAGE
URL = 's3://mybucket1/path1/'
STORAGE_INTEGRATION = MY_STORAGE
;
```
![azure](assets/azure.png)
### If your data is in Azure
#### Create a Storage Integration
To create a storage integration, run the SQL code below.
- Replace `AZURE_TENANT_ID` and `STORAGE_ALLOWED_LOCATIONS` with your values

**Create Storage Integration and Acquire Key Values**

```sql
CREATE STORAGE INTEGRATION MY_STORAGE
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = AZURE
ENABLED = TRUE
AZURE_TENANT_ID = '<tenant_id>'
STORAGE_ALLOWED_LOCATIONS = ('azure://myaccount.blob.core.windows.net/mycontainer/path1/', 'azure://myaccount.blob.core.windows.net/mycontainer/path2/')
;

DESC STORAGE INTEGRATION MY_STORAGE;
```

Provide the values of `AZURE_CONSENT_URL` and `AZURE_MULTI_TENANT_APP_NAME` to your Azure administrator and follow the directions below
- [Grant Snowflake Access Permissions](https://docs.snowflake.com/en/user-guide/data-load-azure-config.html#step-2-grant-snowflake-access-to-the-storage-locations)

#### Create an External Stage
To create an external stage using the storage integration, run the SQL code below.
- Replace `URL` with your value

**Create External Stage Using Storage Integration**

```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE STAGE MY_STAGE
URL = 'azure://myaccount.blob.core.windows.net/load/files/'
STORAGE_INTEGRATION = MY_STORAGE
;
```
![gcp](assets/gcp.png)
### If your data is in GCP
#### Create a Storage Integration
To create a storage integration, run the SQL code below.
- Replace `STORAGE_ALLOWED_LOCATIONS` with your values

**Create Storage Integration and Acquire Key Values**

```sql
CREATE STORAGE INTEGRATION MY_STORAGE
TYPE = EXTERNAL_STAGE
STORAGE_PROVIDER = GCS
ENABLED = TRUE
STORAGE_ALLOWED_LOCATIONS = ('gcs://mybucket1/path1/', 'gcs://mybucket2/path2/')
;

DESC STORAGE INTEGRATION MY_STORAGE;
```

Provide the value of `STORAGE_GCP_SERVICE_ACCOUNT` to your GCP administrator and follow the directions below
- [Grant Snowflake Access Permissions](https://docs.snowflake.com/en/user-guide/data-load-gcs-config.html#step-3-grant-the-service-account-permissions-to-access-bucket-objects)

#### Create an External Stage
To create an external stage using the storage integration, run the SQL code below.
- Replace `URL` with your value

**Create External Stage Using Storage Integration**

```sql
USE SCHEMA MY_DB.MY_SCHEMA;

CREATE OR REPLACE STAGE MY_STAGE
URL = 'gcs://load/files/'
STORAGE_INTEGRATION = MY_STORAGE
;
```

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

<!-- ------------------------ -->
## Conclusion
Duration: 1
	
Congratulations. You have completed this guide and learned how to do the items below. To continue your journey, visit the Data Provider section of the [Snowflake documentation](https://docs.snowflake.com/en/user-guide/data-marketplace-provider.html).
	
- Choose the right approach
- Using the accelerator
- Create a virtual warehouse (create_warehouse.sql)
- Create a database and schema (create_database.sql)
- Create an external stage (create_stage.sql)
- Create one or more external tables (create_ext_table.sql)
- Automate the refresh of the external table (refresh_ext_table.sql)
- Create a secure materialized view on the external table (create_matview.sql)
- Create a share (create_share.sql)
- Prepare for multi-region data sharing (share_multi_region.sql)

	
