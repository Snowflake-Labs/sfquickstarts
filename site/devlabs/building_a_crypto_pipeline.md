summary: Build a data loading pipline using all Snowflake built in encryption options
id: building_a_crypto_pipeline
categories: encryption, security, data-engineering
tags: python, sql, encryption, java, cse
status: Draft
Feedback Link: https://github.com/Snowflake-Labs/devlabs/issues
tags: Security, Encryption, SQL, Data Engineering, SnowSQL, Python

# Building a Data Pipeline with Built-in Snowflake Encryption
<!-- ------------------------ -->
## Overview
Duration: 1

All data stored in Snowflake is encrypted at rest and uses encrypted tunnels to get to and from you to Snowflake and back. For some sensitive information, that may not be enough. If you want to also encrypt the information stored in the tables, you need to take advantage of the next layers of Snowflake's encryption features. We'll walk you through how to keep your data encrypted at every possible step along the way from loading to consumption. You'll build an automated pipeline to consume data and automatically encrypt it with keys managed in your organization's key management service.

### Prerequisites
- Basic familiarity with Snowflake connectivity and SQL syntax
- Basic familiarity with encryption concepts
- Basic familiarity with runnning Java and Python code

### What You’ll Learn 
- how to query data

### What You’ll Need 
- A [Snowflake](https://www.snowflake.com/) Account 
- A Text Editor or IDE
- A Snowflake user with full ACCOUNTADMIN rights, and the ability to grant it any other role

### What You’ll Build 
- Examples of using the Snowflake Python Connector

<!-- ------------------------ -->
## Clean Up from Last Time (Optional)
Duration: 2

If you've run through this before and used the SQL as is, then this should clean out all the stuff you created.

```
use role SYSADMIN;
drop database if exists CRYPTODEMO;
use role USERADMIN;
drop role if exists CRYPTO_PIPE_RAW_USER; 
drop role if exists GET_CSE_KEY; 
drop role if exists GET_DATA_KEY; 
drop role if exists CRYPTO_PIPE_PROD_USER; 
drop role if exists CRYPTO_PIPE_TASK_OWNER;
drop role if exists CRYPTO_MASKING_ADMIN;
drop role if exists CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
```

<!-- ------------------------ -->
## Set up the Lab Roles
Duration: 5

Throughout this lab, we will try to stick to security best practices. We're going to to attempt to separate out the permissions being used into roles with the least privileges needed. So we will need different roles to own and operate all the moving pieces. Comments on each line of SQL explain what each role is used to do.

```
use role USERADMIN; // minimum out of the box rights with which you can perform these actions
create or replace role CRYPTO_PIPE_RAW_USER; // role which can handle unencrypted data
create or replace role GET_CSE_KEY; // role which can get the file CSE key (unused right now)
create or replace role GET_DATA_KEY; // role which can get the data crypto materials
create or replace role CRYPTO_MASKING_ADMIN; // role to set masking policies on unencrypted data
create or replace role CRYPTO_PIPE_PROD_USER; // role which can only handle encrypted data 
create or replace role CRYPTO_PIPE_TASK_OWNER; // role which will own the tasks so they can be in the same tree
// since the CRYPTO_PIPE_RAW_USER handles raw data, it needs key access
grant role GET_CSE_KEY to role CRYPTO_PIPE_RAW_USER;
grant role GET_DATA_KEY to role CRYPTO_PIPE_RAW_USER;
// to operate the lab, your user will need all these roles
grant role CRYPTO_PIPE_RAW_USER to user <YOURUSERNAME>;
grant role CRYPTO_MASKING_ADMIN to user <YOURUSERNAME>;
grant role CRYPTO_PIPE_PROD_USER to user <YOURUSERNAME>;
grant role CRYPTO_PIPE_TASK_OWNER to user <YOURUSERNAME>;
```

<!-- ------------------------ -->

## Set up the Lab Database and Schemas
Duration: 3

Here we will set up the database and all the schemas for this lab. In real life you may integrate much of this into pre-existing resources. 

```
use role SYSADMIN;
create or replace database CRYPTODEMO;
create or replace schema CRYPTODEMO.UNENCRYPTED;
create or replace schema CRYPTODEMO.POLICIES;
create or replace schema CRYPTODEMO.ENCRYPTED;
create or replace schema CRYPTODEMO.TASKS;
grant usage on database CRYPTODEMO to role CRYPTO_PIPE_RAW_USER;
grant usage on database CRYPTODEMO to role GET_DATA_KEY;
grant usage on database CRYPTODEMO to role CRYPTO_MASKING_ADMIN;
grant usage on database CRYPTODEMO to role CRYPTO_PIPE_PROD_USER;
grant usage on database CRYPTODEMO to role CRYPTO_PIPE_TASK_OWNER;
grant ownership on schema CRYPTODEMO.UNENCRYPTED to role CRYPTO_PIPE_RAW_USER;
grant ownership on schema CRYPTODEMO.POLICIES to role CRYPTO_MASKING_ADMIN;
grant ownership on schema CRYPTODEMO.ENCRYPTED to role CRYPTO_PIPE_PROD_USER;
grant ownership on schema CRYPTODEMO.TASKS to role CRYPTO_PIPE_TASK_OWNER;
use role CRYPTO_PIPE_PROD_USER; 
grant usage on schema CRYPTODEMO.ENCRYPTED to role CRYPTO_PIPE_RAW_USER;
grant usage on schema CRYPTODEMO.ENCRYPTED to role CRYPTO_PIPE_TASK_OWNER;
use role CRYPTO_PIPE_RAW_USER;
grant usage on schema CRYPTODEMO.UNENCRYPTED to role CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->

## Set Up Elevated Rights and CSP Resources
Duration: 12

In this step, you will need elevated rights (`ACCOUNTADMIN` role and `SECURITYADMIN` role) as well as cloud service provider (CSP) resources (cloud storage resources and API resources). If you do not have these rigths and resources, a future step will provide an alternative where you can move ahead without the things we create here. You can skip this step now if you don't have the elevated rights and cloud service provider resoruces. 

You've already heard how Snowflake separates storage and compute. Virtual warehouses are the "compute," and in order to do things like run queries a role will need rights to use a warehouse object. Here we use `SECURITYADMIN` to grant access to existnig warehouses since that built in role will always have access to grant rights to anything. Up to now we've been using the absolute least amount of privilege to accomplish each step. If you want to continue to do that (which is always a good idea) and you know the role that owns the specific warehouse you want to grant rights to, then you can change `SECURITYADMIN` to the specifc role which owns that warehouse in this next block of SQL.

```
use role SECURITYADMIN;
grant usage on warehouse RESET_WH to role CRYPTO_PIPE_RAW_USER;
grant usage on warehouse RESET_WH to role CRYPTO_PIPE_PROD_USER;
grant usage on warehouse RESET_WH to role CRYPTO_PIPE_TASK_OWNER;
```

Next we will set up access to a storage integration and an API integration. Again, if you know the roles that own the storage integration and API integration you will use here, then you can change `SECURITYADMIN` to the specifc role which owns that integration in this next block of SQL.

Setting up access to a storage integration and an API integration implies both of these exist. Setting these up is out of the scope of this guide, but you can find the instructions on how to do this here:
- [Creating a Storage Integration](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration.html)
- [Creating an API Integration](https://docs.snowflake.com/en/sql-reference/sql/create-api-integration.html)

Once you have these integrations ready, here's the first block of SQL you will run:
```
use role SECURITYADMIN;
grant usage on integration MULTIVERSE to role CRYPTO_PIPE_RAW_USER; 
grant usage on integration first_ext_function_api_int to role GET_DATA_KEY; 
```

Finally, the task privilege must be granted to the role which will run tasks. The task privilege can only be done by `ACCOUNTADMIN` (at the time of this writing). 
```
use role ACCOUNTADMIN;
grant execute task on account to CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->
## Set Up Stage and External Function
Duration: 10

If you skipped the "Set Up Elevated Rights and CSP Resources" step, then you should skip this as well. 

Create a stage where the files containing the data we will import can live.
```
use role CRYPTO_PIPE_RAW_USER;
create or replace stage CRYPTODEMO.UNENCRYPTED.cyptostream_stage URL='<YOURFULLSTORAGEURIANDPATH>'
    STORAGE_INTEGRATION = multiverse;
CREATE OR REPLACE FILE FORMAT CRYPTODEMO.UNENCRYPTED.cyptostream_csv_format
  TYPE = 'CSV'
  FIELD_DELIMITER = '|';
```

Create an external function that retrieves the encryption material to be used with the [`ENCRYPT_RAW`](https://docs.snowflake.com/en/sql-reference/functions/encrypt_raw.html) function to protect the sensitive information. 
```
use role CRYPTO_PIPE_RAW_USER;
grant usage on schema CRYPTODEMO.UNENCRYPTED to role GET_DATA_KEY;
grant create function on schema CRYPTODEMO.UNENCRYPTED to role GET_DATA_KEY;
use role GET_DATA_KEY; // create as other and transfer vs. create perpetiually
CREATE or REPLACE EXTERNAL FUNCTION CRYPTODEMO.UNENCRYPTED.key_external_function(tablename VARCHAR, columnname VARCHAR, role VARCHAR)
    RETURNS VARIANT
    API_INTEGRATION = first_ext_function_api_int
    AS '<YOURFULLAPIURIANDPATH>'
    ;
```


<!-- ------------------------ -->
## Create Table for Raw Data
Duration: 5

Create a table where the raw, unencrypted data will land before it's processed. Note that this table is a transient table and has `DATA_RETENTION_TIME_IN_DAYS = 0`. This deactivates [Fail Safe](https://docs.snowflake.com/en/user-guide/data-failsafe.html) and [Time Travel](https://docs.snowflake.com/en/user-guide/data-time-travel.html) for this table, respectively, in order to avoid anyone using these features to see unencrypted data after it's been procssed to be encrypted. Like the other tables we will create in the next steps, this table also has a [Stream](https://docs.snowflake.com/en/user-guide/streams.html) on it, which will be used to manage the pipeline of data in a consistent manner. This table will also have a [Masking Policy](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro.html) set to protect the column where unencrypted, sensitive data will reside. This will prevent users with elevated rights (like `ACCOUNTADMIN`) from easily seeing this information improperly. 

```
use role CRYPTO_PIPE_RAW_USER;
create or replace transient table CRYPTODEMO.UNENCRYPTED.raw_data(data_stuff VARCHAR(32), id_thing VARCHAR(10), batch_id number(10)) DATA_RETENTION_TIME_IN_DAYS = 0;
create or replace stream CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream ON TABLE CRYPTODEMO.UNENCRYPTED.raw_data append_only=true;
grant select on CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream to role CRYPTO_PIPE_TASK_OWNER; 
grant select on table CRYPTODEMO.UNENCRYPTED.raw_data to role CRYPTO_PIPE_TASK_OWNER; 
grant usage, create masking policy ON SCHEMA CRYPTODEMO.UNENCRYPTED to role CRYPTO_MASKING_ADMIN;
use role CRYPTO_MASKING_ADMIN;
create or replace masking policy CRYPTODEMO.POLICIES.hide_unencrypted_values as (val varchar) returns varchar ->
  case
    when current_role() in ('CRYPTO_PIPE_RAW_USER') then val
    else '*** UNAUTHORIZED!!! ***'
  end; // doc that this is not the BEST idea/practice in form
grant apply on masking policy CRYPTODEMO.POLICIES.hide_unencrypted_values to role CRYPTO_PIPE_RAW_USER;
grant usage on schema CRYPTODEMO.POLICIES to role CRYPTO_PIPE_RAW_USER; 
use role CRYPTO_PIPE_RAW_USER;
alter table if exists CRYPTODEMO.UNENCRYPTED.raw_data modify column data_stuff set masking policy CRYPTODEMO.POLICIES.hide_unencrypted_values;
// doc how you could choose to let the masking admin apply, but then they need some rights in unencrypted area
```

<!-- ------------------------ -->
## Create Table for Staged Data
Duration: 5

Create a table where the sensitive data can be encrypted and then await further processesing. Here we use a `CREATE as SELECT` syntax only to demonstrate how the [`ENCRYPT_RAW`](https://docs.snowflake.com/en/sql-reference/functions/encrypt_raw.html) function works. As we will see in the next step, this will produce a column of type variant, and we could have simply created the column with that type.

Note that we grant the `CRYPTO_PIPE_RAW_USER` role rights on this table as it will be used to populate the data here frm the raw, unencrypted schema.

> WARNING: The key and other cryptographic materials used in this example are human readable for ease of learning, but represent terrible examples for use in any real world circumstances. DO NOT use these values to protect any of your actual sensitive information.

```
use role CRYPTO_PIPE_PROD_USER;
use warehouse RESET_WH;
create or replace table CRYPTODEMO.ENCRYPTED.staged_data as (
  select ENCRYPT_RAW(
                TO_BINARY(HEX_ENCODE('data worth encrypting'), 'HEX'), 
                TO_BINARY(HEX_ENCODE('areallybadkeystrareallybadkeystr'), 'HEX'), -- key
                TO_BINARY(HEX_ENCODE('anIVakaNONCE'), 'HEX'), -- iv/nonce
                TO_BINARY(HEX_ENCODE('additional-data-for-AEAD'), 'HEX'), -- additional data for AEAD
                'AES-GCM/pad:none' 
            ) as data_stuff, -- note the need to ensure an encrypted value can live in this column 
         '1234567890' as id_thing, '1234567890' as batch_id
    );  
truncate table CRYPTODEMO.ENCRYPTED.staged_data; desc table CRYPTODEMO.ENCRYPTED.staged_data;
create or replace stream CRYPTODEMO.ENCRYPTED.staged_to_target_data_stream ON TABLE CRYPTODEMO.ENCRYPTED.staged_data append_only=true;
create or replace stream CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream ON TABLE CRYPTODEMO.ENCRYPTED.staged_data append_only=true;
grant insert on table CRYPTODEMO.ENCRYPTED.staged_data to role CRYPTO_PIPE_RAW_USER;
grant select on table CRYPTODEMO.ENCRYPTED.staged_data to role CRYPTO_PIPE_RAW_USER;
grant select on CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream to role CRYPTO_PIPE_RAW_USER;
```

<!-- ------------------------ -->
## Create Table for Production Data
Duration: 2

Create a table which represents the final, target table where the data being processed will land. Note that we simply give the `data_stuff` column where the encrypted data will live type `VARIANT`. 

```
use role CRYPTO_PIPE_PROD_USER;
use warehouse RESET_WH;
create or replace table CRYPTODEMO.ENCRYPTED.target_table (data_stuff VARIANT, id_thing VARCHAR(10), batch_id number(10)); // doc diff from above
create or replace stream CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table_stream ON TABLE CRYPTODEMO.ENCRYPTED.target_table append_only=true;
```

<!-- ------------------------ -->
## Create Stored Procedure to Move Data from Raw to Stage
Duration: 6

Create a Stored Procedure to encapsulate the steps to move the data from the raw, unencrypted table to the staging, encrypted table. This will leverage the stream on the raw table in order to always only insert those rows which have already been successfully processed at the time the Stored Procedure runs.  

The encryption of the sensitive data column, `data_stuff`, will take place during this process. Rights to run this Stored Procedure will be granted to the `CRYPTO_PIPE_TASK_OWNER` role since it will be run from a [Task](https://docs.snowflake.com/en/user-guide/tasks-intro.html). Note that we could have granted the `CRYPTO_PIPE_TASK_OWNER` role rights to [all future Stored Procedures](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege.html#future-grants-on-database-or-schema-objects) instead of granting rights to each one specifically. We use the more restricted rights here in keeping with the least privileges principle. 

> NOTE: In this lab we are supplying the [Initialization Vector (IV)](https://docs.snowflake.com/en/sql-reference/functions/encrypt_raw.html#arguments) as a string which would be used for all the encryption operations. In a real world scenario, you may choose to either allow for a random IV to be set by leaving it `NULL`, having the IV stored with the key and AD, or generating it based on the `batch_id` or other value. The important thing to realize is that if you would wish to use the column being encrypted in joins later, then to get consistent results in multiple tables the same informaiton would need to use the same encryption material - including the same IV - when it is encrypted. So to make the columns joinable, the IVs would need to be the same.

```
use role CRYPTO_PIPE_RAW_USER;
CREATE OR REPLACE PROCEDURE CRYPTODEMO.UNENCRYPTED.move_and_encrypt_raw_data_to_stage()
  returns string
  language javascript
  execute as owner
  as
  $$
  function snowflakeRunStatement(SQL) {
    try {
        let results = snowflake.execute({ sqlText: SQL});
        
        return results;
    } catch (err)  {
        var error =  "Failed: Code: " + err.code + "\n  State: " + err.state;
        error += "\n  Message: " + err.message;
        error += "\nStack Trace:\n" + err.stackTraceTxt; 

        throw error;
    }
  }
  
  // STEP 1 - get the crypto material from the key management system 
  var cryptoJsonString = ""
  var getCryptoWithExternalFunctionSQL = `SELECT CRYPTODEMO.UNENCRYPTED.key_external_function(
      'CRYPTODEMO.UNENCRYPTED.raw_data', 
      'data_stuff', 
      'CRYPTO_PIPE_RAW_USER')::varchar
  `;
  
  var rs1 = snowflakeRunStatement(getCryptoWithExternalFunctionSQL);
  
  // Read each row and add it to the array we will return.
  while (rs1.next())  {
    // we will assume one row for now
    cryptoJsonString = rs1.getColumnValue(1);
  }
  
  var cryptoJsonObj = JSON.parse(cryptoJsonString);
  var key = cryptoJsonObj.key;
  var ad = cryptoJsonObj.ad;
  
  // STEP 2 - run the insert as select statement
  var insertIntoStagedFromRawSQL = `insert into CRYPTODEMO.ENCRYPTED.staged_data (data_stuff, id_thing, batch_id)
      select ENCRYPT_RAW(
                    TO_BINARY(HEX_ENCODE(data_stuff), 'HEX'), 
                    TO_BINARY(HEX_ENCODE('${key}'), 'HEX'),
                    TO_BINARY(HEX_ENCODE('anIVakaNONCE'), 'HEX'),
                    TO_BINARY(HEX_ENCODE('${ad}'), 'HEX'),
                    'AES-GCM/pad:none' 
                ), id_thing, batch_id from CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream
      where METADATA$ACTION = 'INSERT'
  `;
  
  snowflakeRunStatement(insertIntoStagedFromRawSQL);

  return 0;
  $$
;

grant usage on PROCEDURE CRYPTODEMO.UNENCRYPTED.move_and_encrypt_raw_data_to_stage() to role CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->
## Create Stored Procedure to Move Data from Stage to Target
Duration: 3

Create a Stored Procedure to encapsulate the steps to move the data from the staging, encrypted table to the final table where the data will live in its encrypted form. This will leverage one of the streams on the staging table in order to always only insert those rows which have already been successfully processed at the time the Stored Procedure runs. 

```
use role CRYPTO_PIPE_PROD_USER;
CREATE OR REPLACE PROCEDURE CRYPTODEMO.ENCRYPTED.staged_to_target_data_insert()
  returns string
  language javascript
  execute as owner
  as
  $$
  function snowflakeRunStatement(SQL) {
    try {
        let results = snowflake.execute({ sqlText: SQL});
        
        return results;
    } catch (err)  {
        var error =  "Failed: Code: " + err.code + "\n  State: " + err.state;
        error += "\n  Message: " + err.message;
        error += "\nStack Trace:\n" + err.stackTraceTxt; 

        throw error;
    }
  }
  
  // STEP 1 - insert Into Target From Staged
    var insertIntoTargetFromStagedSQL = `insert into CRYPTODEMO.ENCRYPTED.target_table (data_stuff, id_thing, batch_id)
        select data_stuff, id_thing, batch_id from CRYPTODEMO.ENCRYPTED.staged_to_target_data_stream
        where METADATA$ACTION = 'INSERT'
  `;
  
  snowflakeRunStatement(insertIntoTargetFromStagedSQL);

  return 0;
  $$
;

grant usage on PROCEDURE CRYPTODEMO.ENCRYPTED.staged_to_target_data_insert() to role CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->
## Create Stored Procedure to Delete Data from Raw
Duration: 4

Create a Stored Procedure to encapsulate the steps to delete the data from the raw, unencrypted table once it's in the staging table.This will leverage one of the streams on the staging table in order to always only delete those rows which have already been successfully processed at the time the Stored Procedure runs. 

```
use role CRYPTO_PIPE_RAW_USER;
CREATE OR REPLACE PROCEDURE CRYPTODEMO.UNENCRYPTED.delete_raw_based_on_staged_data()
  returns string
  language javascript
  execute as owner
  as
  $$
  function snowflakeRunStatement(SQL) {
    try {
        let results = snowflake.execute({ sqlText: SQL});
        
        return results;
    } catch (err)  {
        var error =  "Failed: Code: " + err.code + "\n  State: " + err.state;
        error += "\n  Message: " + err.message;
        error += "\nStack Trace:\n" + err.stackTraceTxt; 

        throw error;
    }
  }
  
  // STEP 1 - use stage stream to delete from raw 
    var deleteFromRawSQL = `delete from CRYPTODEMO.UNENCRYPTED.raw_data R where 
        R.batch_id IN (
            select DISTINCT batch_id from CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream where METADATA$ACTION = 'INSERT'
        )
  `;
  
  snowflakeRunStatement(deleteFromRawSQL);

  return 0;
  $$
;

grant usage on PROCEDURE CRYPTODEMO.UNENCRYPTED.delete_raw_based_on_staged_data() to role CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->
## Create Stored Procedure to Delete Data from Staging
Duration: 4

Create a Stored Procedure to encapsulate the steps to delete the data from the staging table. This will leverage the stream on the target table in order to always only delete those rows which have already been successfully processed at the time the Stored Procedure runs. 

```
use role CRYPTO_PIPE_PROD_USER;
CREATE OR REPLACE PROCEDURE CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table()
  returns string
  language javascript
  execute as owner
  as
  $$
  function snowflakeRunStatement(SQL) {
    try {
        let results = snowflake.execute({ sqlText: SQL});
        
        return results;
    } catch (err)  {
        var error =  "Failed: Code: " + err.code + "\n  State: " + err.state;
        error += "\n  Message: " + err.message;
        error += "\nStack Trace:\n" + err.stackTraceTxt; 

        throw error;
    }
  }
  
  // STEP 1 - insert Into Target From Staged
    var deleteFromStagedSQL = `delete from CRYPTODEMO.ENCRYPTED.staged_data S where 
        S.batch_id IN (
            select DISTINCT batch_id from CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table_stream where METADATA$ACTION = 'INSERT'
        )
  `;
  
  snowflakeRunStatement(deleteFromStagedSQL);

  return 0;
  $$
;

grant usage on PROCEDURE CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table() to role CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->
## Create Tasks to Automate Data Movement
Duration: 4

Create Tasks which will move the data through the process of being encrypted and inserted to the target table after it has landed in the raw table. The Tasks will use the Stored Procedures we created in the last steps. The first Task will be the root of a tree which will run on an agressive 1 minute schedule looking for new data in the raw table to process. All other Tasks will trigger based on the success of their preceding Task in the tree. 

```
use role CRYPTO_PIPE_TASK_OWNER;

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.insert_data_from_raw_to_stage
  WAREHOUSE = RESET_WH
  SCHEDULE = '1 minute'
WHEN
  SYSTEM$STREAM_HAS_DATA('CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream')
AS
  CALL CRYPTODEMO.UNENCRYPTED.move_and_encrypt_raw_data_to_stage();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.delete_data_from_raw_after_hits_staged
  WAREHOUSE = RESET_WH
AFTER 
  CRYPTODEMO.TASKS.insert_data_from_raw_to_stage
AS
  CALL CRYPTODEMO.UNENCRYPTED.delete_raw_based_on_staged_data();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.insert_data_from_stage_to_target
  WAREHOUSE = RESET_WH
AFTER 
  CRYPTODEMO.TASKS.delete_data_from_raw_after_hits_staged
AS
  CALL CRYPTODEMO.ENCRYPTED.staged_to_target_data_insert();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.delete_data_from_stage_after_hits_target
  WAREHOUSE = RESET_WH
AFTER 
  CRYPTODEMO.TASKS.insert_data_from_stage_to_target
AS
  CALL CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table();
```

Activate the Tasks so they will run. Note that when Tasks are arranged in a tree like this, you must always operate on the branches while the root task is in a suspended state. 

```
use role CRYPTO_PIPE_TASK_OWNER;
ALTER TASK IF EXISTS CRYPTODEMO.TASKS.insert_data_from_stage_to_target RESUME;
ALTER TASK IF EXISTS CRYPTODEMO.TASKS.delete_data_from_stage_after_hits_target RESUME;
ALTER TASK IF EXISTS CRYPTODEMO.TASKS.delete_data_from_raw_after_hits_staged RESUME;
ALTER TASK IF EXISTS CRYPTODEMO.TASKS.insert_data_from_raw_to_stage RESUME;
```

<!-- ------------------------ -->
## Create Role to Monitor Task Progess (Optional)
Duration: 4

Create a role with rights to view the progress of Tasks moving data. Since this role would have access to both the unencrypted and encypted areas as well as elevated rights on these, it certainly violates the principle of least privilege. Since this is a lab, however, it makes sense to be able to see this progress all from one place. 

```
use role USERADMIN;
create or replace role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
use role SECURITYADMIN;
grant usage on database CRYPTODEMO to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant usage on schema CRYPTODEMO.UNENCRYPTED to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant usage on schema CRYPTODEMO.ENCRYPTED to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant select on table CRYPTODEMO.UNENCRYPTED.raw_data to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant select on table CRYPTODEMO.ENCRYPTED.staged_data to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant select on table CRYPTODEMO.ENCRYPTED.target_table to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
use role CRYPTO_PIPE_RAW_USER;
grant select on stream CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
use role CRYPTO_PIPE_PROD_USER;
grant select on stream CRYPTODEMO.ENCRYPTED.staged_to_target_data_stream to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant select on stream CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant select on stream CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table_stream to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
use role SECURITYADMIN;
grant usage on warehouse RESET_WH to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST to user <YOURUSERNAME>;
```

<!-- ------------------------ -->

## Kick Off Tasks by Inserting Into Raw Table
Duration: 10

In the real world, your import methods for data would likely involve sophisticated ELT/ETL routines like [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro.html). For the purposes of this lab we will use Snowflake's built in [`COPY`](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table.html) capabilities. If you did not create the resources in the *Elevated Rights and CSP Resources* section, then an alternative will be provided in the penultimate step.



<!-- ------------------------ -->
## Copy with a Stored Procedure
Duration: 2

This will create a stored procedure to load data into the 

<!-- ------------------------ -->
## Copy with Client Side Encryption
Duration: 2

Using client side encryption would be recommended in a real world implamentation of this. What that provides is maximum security for the sensitive information being loaded. It means that the file contianing this information will be encrypted by your side fo the conversation and Snowflake would only be able to process it when your organization supplies the key. 
<!-- ------------------------ -->

## Load with SQL
Duration: 2
