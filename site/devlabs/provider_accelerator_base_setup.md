summary: Example Provider Accelerator Base Setup
id: provider_accelerator_base_setup
categories: Data Exchange
tags: medium
status: Published 
Feedback Link: https://developers.snowflake.com

# Example Provider Accelerator Base Setup
<!-- ------------------------ -->
## Overview 
Duration: 1

This accelerator contains code that can be used as templates or full automation to build the end-to-end workflow for listing data on the Snowflake Marketplace or in a private Exchange. There are multiple approaches to doing this, depending on where your data already exists as a provider. These approaches are listed below.

- Approach 1 (direct-load-from-object-store) - use this approach when your data already exists in cloud object store and you are comfortable loading that data into Snowflake using traditional loading methods. This method works best when the consumer experience is consistent customer to customer and region to region. 
- Approach 2 (external-tables) - use this approach when you'd rather "point" to some of your data in object store and only load it into a given Snowflake region as customer demand dictates.

### What You’ll Learn 
- Create a virtual warehouse (create_warehouse.sql)
- Create a database and schema (create_database.sql)
- Create an external stage (create_stage.sql)
- Perform the steps appropriate to each approach (.sql files are in the subfolders)
- Create a listing on the Marketplace or Exchange through the UI (create_listing.sql)

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
## Choosing the Right Approach
Duration: 5

Before moving onto the next code step, it's important to reflect on which approach is best for you.

### Approach 1 (direct-load-from-object-store) 
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

### Approach 2 (external-tables) 
- This approach creates external tables that point to your files. Snowflake external tables do not ingest data, but do allow you to run queries against your files. However, these queries will perform slower than against regular Snowflake tables and when the external tables points to your files in another cloud/region, data transfer charges will be incurred with every query.
- Snowflake materialized views can be written on top of external tables to materialize (ingest) the data into Snowflake to produce faster queries and incur the data transfer costs once versus with every query. The materialized view definitions can include where clauses, allowing you to define what slice of data gets materialized.
- The setup in this approach, then, is to create Snowflake accounts in whatever clouds/regions you have consumers, create the same library of external tables in each accounted, pointed to your files in one central object store location, and create materialized views with customized where clauses in each cloud/region to control what data gets "pulled" into which cloud/region. These materialized views can be changed (or dropped) at any time as consumer demand changes.
- With this approach, however, the data refresh process is to refresh the external table (look for new files), and the presence of new files will cause the materialized view to refresh automatically. Because there can be a timing lag between those two steps, this approach is best done when the data refresh can be done in off-hours so users don't experience query slowdown during the lag.

![Approach 2](assets/approach2.png)

Now that you have more details on the different options and know your path, let's move onto the next step using one of the links below.

- [Provider Accelerator Approach 1 Guide](../provider_accelerator_approach_1)
- [Provider Accelerator Approach 2 Guide](../provider_accelerator_approach_2)
