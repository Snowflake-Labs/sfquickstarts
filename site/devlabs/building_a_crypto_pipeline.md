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
Duration: 2

All data stored in Snowflake is encrypted at rest and uses encrypted tunnels to get to and from you to Snowflake and back. For some sensitive information, you may wish to add even more encryption than that. If you want to also encrypt the information stored in the tables, you need to take advantage of the next layers of Snowflake's encryption features. We'll walk you through how to keep your data encrypted at every possible step along the way from loading to consumption. You'll build an automated pipeline to consume data and automatically encrypt it with keys managed in your organization's key management service.

### Prerequisites
- Familiarity with Snowflake connectivity and SQL syntax
- Basic familiarity with encryption concepts
- Basic familiarity with runnning Java and Python code
- An appreciation of running with least prvileges to enhance security

### What You’ll Learn 
- How to use Snowflake's built-in encryption functions and client side encryption support

### What You’ll Need 
- A [Snowflake](https://www.snowflake.com/) Account and user
- A Text Editor or IDE
- Rights to use the Snowflake built in sample data
- (Optional but suggested) Access to the `SYSADMIN`, `USERADMIN`, `SECURITYADMIN`, and `ACCOUNTADMIN` roles, or a means to have SQL run as these roles
- (Optional but suggested) Access to an S3 bucket where you can read and write
- (Optional but suggested) Access to an AWS API Gateway and the ability to run Lambda code there
- A method to deliver key materials. This lab uses AWS Secrets Manager, but that is optional.

### What You’ll Build 
- An example pipline that takes sensitive information and automatically encrypts it at the field level

<!-- ------------------------ -->
## Clean Up from Last Time (Optional)
Duration: 1

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
## Set up the Lab Roles and Objects Using Elevated Rights
Duration: 6

In this step, you will need elevated rights (`ACCOUNTADMIN` role, `USERADMIN` role, `SYSADMIN` role, and `SECURITYADMIN` role). If you do not have these rigths, future steps will provide an alternative where you can move ahead without the things we create here. We will assume you have the rights and you can adjust as needed.

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

Here we will set up the database and all the schemas for this lab. In real life you may integrate much of this into pre-existing resources. If you do not have access to `SYSADMIN` role, then you can create these objects wherever you like as long as you adjust all the following SQL to use that database in place of the `CRYPTODEMO` database used by default.

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

Here we use `SECURITYADMIN` to grant access to existnig warehouses since that built in role will always have access to grant rights to anything. If you want to continue to use the least privileges needed (which is always a good idea) and you know the role that owns the specific warehouse you want to grant rights to, then you can change `SECURITYADMIN` to the specifc role which owns that warehouse in this next block of SQL.

```
use role SECURITYADMIN;
grant usage on warehouse <YOURWAREHOUSE> to role CRYPTO_PIPE_RAW_USER;
grant usage on warehouse <YOURWAREHOUSE> to role CRYPTO_PIPE_PROD_USER;
grant usage on warehouse <YOURWAREHOUSE> to role CRYPTO_PIPE_TASK_OWNER;
```

Finally, the task privilege must be granted to the role which will run tasks. The task privilege can only be granted by `ACCOUNTADMIN` (at the time of this writing). 
```
use role ACCOUNTADMIN;
grant execute task on account to CRYPTO_PIPE_TASK_OWNER;
```

<!-- ------------------------ -->

## Set Up Cloud Service Provider (CSP) Resources
Duration: 10

In this step, you will need elevated rights (`SECURITYADMIN` role) as well as cloud service provider (CSP) resources (cloud storage resources and API resources). If you do not have these rigths and resources, future steps will provide an alternative where you can move ahead without the things we create here. We will assume you have the rights and you can adjust as needed.

Next we will set up access to a storage integration and an API integration. 

Setting up access to a storage integration and an API integration implies both of these exist. Setting these up is out of the scope of this guide, but you can find the instructions on how to do this here:
- [Creating a Storage Integration](https://docs.snowflake.com/en/sql-reference/sql/create-storage-integration.html)
- [Creating an API Integration](https://docs.snowflake.com/en/sql-reference/sql/create-api-integration.html)

Once you have these integrations ready, here's the block of SQL you will run. Again, if you know the roles that own the storage integration and API integration you will use here, then you can change `SECURITYADMIN` to the specifc role which owns that integration in this next block of SQL:
```
use role SECURITYADMIN;
grant usage on integration <YOURSTORAGEINTEGRATION> to role CRYPTO_PIPE_RAW_USER; 
grant usage on integration <YOURAPIINTEGRATION> to role GET_DATA_KEY; 
```

Create a stage where the files containing the data we will import can live.
```
use role CRYPTO_PIPE_RAW_USER;
create or replace stage CRYPTODEMO.UNENCRYPTED.cyptostream_stage URL='<YOURFULLSTORAGEURIANDPATH>'
    STORAGE_INTEGRATION = <YOURSTORAGEINTEGRATION>;
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
    API_INTEGRATION = <YOURAPIINTEGRATION>
    AS '<YOURFULLAPIURIANDPATH>'
    ;
```

<!-- ------------------------ -->
## Create Tables
Duration: 6

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
  end; 
grant apply on masking policy CRYPTODEMO.POLICIES.hide_unencrypted_values to role CRYPTO_PIPE_RAW_USER;
grant usage on schema CRYPTODEMO.POLICIES to role CRYPTO_PIPE_RAW_USER; 
use role CRYPTO_PIPE_RAW_USER;
alter table if exists CRYPTODEMO.UNENCRYPTED.raw_data modify column data_stuff set masking policy CRYPTODEMO.POLICIES.hide_unencrypted_values;
```

Create a table where the sensitive data can be encrypted and then await further processesing. Here we use a `CREATE as SELECT` syntax only to demonstrate how the [`ENCRYPT_RAW`](https://docs.snowflake.com/en/sql-reference/functions/encrypt_raw.html) function works. As we will see in the next step, this will produce a column of type variant, and we could have simply created the column with that type.

Note that we grant the `CRYPTO_PIPE_RAW_USER` role rights on this table as it will be used to populate the data here frm the raw, unencrypted schema.

> WARNING: The key and other cryptographic materials used in this example are human readable for ease of learning, but represent terrible examples for use in any real world circumstances. DO NOT use these values to protect any of your actual sensitive information.

```
use role CRYPTO_PIPE_PROD_USER;
use warehouse <YOURWAREHOUSE>;
create or replace table CRYPTODEMO.ENCRYPTED.staged_data as (
  select ENCRYPT_RAW(
                TO_BINARY(HEX_ENCODE('data worth encrypting'), 'HEX'), 
                TO_BINARY(HEX_ENCODE('areallybadkeystrareallybadkeystr'), 'HEX'), -- key
                TO_BINARY(HEX_ENCODE('anIVakaNONCE'), 'HEX'), -- iv/nonce
                TO_BINARY(HEX_ENCODE('additional-data-for-AEAD'), 'HEX'), -- additional data for AEAD
                'AES-GCM/pad:none' 
            ) as data_stuff, 
         '1234567890' as id_thing, '1234567890' as batch_id
    );  
truncate table CRYPTODEMO.ENCRYPTED.staged_data; desc table CRYPTODEMO.ENCRYPTED.staged_data;
create or replace stream CRYPTODEMO.ENCRYPTED.staged_to_target_data_stream ON TABLE CRYPTODEMO.ENCRYPTED.staged_data append_only=true;
create or replace stream CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream ON TABLE CRYPTODEMO.ENCRYPTED.staged_data append_only=true;
grant insert on table CRYPTODEMO.ENCRYPTED.staged_data to role CRYPTO_PIPE_RAW_USER;
grant select on table CRYPTODEMO.ENCRYPTED.staged_data to role CRYPTO_PIPE_RAW_USER;
grant select on CRYPTODEMO.ENCRYPTED.delete_raw_based_on_staged_data_stream to role CRYPTO_PIPE_RAW_USER;
```

Create a table which represents the final, target table where the data being processed will land. Note that we simply give the `data_stuff` column where the encrypted data will live type `VARIANT`. 

```
use role CRYPTO_PIPE_PROD_USER;
use warehouse <YOURWAREHOUSE>;
create or replace table CRYPTODEMO.ENCRYPTED.target_table (data_stuff VARIANT, id_thing VARCHAR(10), batch_id number(10)); 
create or replace stream CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table_stream ON TABLE CRYPTODEMO.ENCRYPTED.target_table append_only=true;
```

<!-- ------------------------ -->
## Create Stored Procedure to Move Data from Raw to Stage
Duration: 5

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
## Create Other Stored Procedures to Move Data to Target
Duration: 6

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
Duration: 6

Create Tasks which will move the data through the process of being encrypted and inserted to the target table after it has landed in the raw table. The Tasks will use the Stored Procedures we created in the last steps. The first Task will be the root of a tree which will run on an agressive 1 minute schedule looking for new data in the raw table to process. All other Tasks will trigger based on the success of their preceding Task in the tree. 

```
use role CRYPTO_PIPE_TASK_OWNER;

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.insert_data_from_raw_to_stage
  WAREHOUSE = <YOURWAREHOUSE>
  SCHEDULE = '1 minute'
WHEN
  SYSTEM$STREAM_HAS_DATA('CRYPTODEMO.UNENCRYPTED.raw_to_staged_insert_stream')
AS
  CALL CRYPTODEMO.UNENCRYPTED.move_and_encrypt_raw_data_to_stage();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.delete_data_from_raw_after_hits_staged
  WAREHOUSE = <YOURWAREHOUSE>
AFTER 
  CRYPTODEMO.TASKS.insert_data_from_raw_to_stage
AS
  CALL CRYPTODEMO.UNENCRYPTED.delete_raw_based_on_staged_data();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.insert_data_from_stage_to_target
  WAREHOUSE = <YOURWAREHOUSE>
AFTER 
  CRYPTODEMO.TASKS.delete_data_from_raw_after_hits_staged
AS
  CALL CRYPTODEMO.ENCRYPTED.staged_to_target_data_insert();

CREATE OR REPLACE TASK CRYPTODEMO.TASKS.delete_data_from_stage_after_hits_target
  WAREHOUSE = <YOURWAREHOUSE>
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
Duration: 3

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
grant usage on warehouse <YOURWAREHOUSE> to role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
grant role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST to user <YOURUSERNAME>;
```

<!-- ------------------------ -->
## Create File with Copy and Apply Client Side Encryption 
Duration: 10

In the real world, your import methods for data would likely involve sophisticated ELT/ETL routines like [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro.html). For the purposes of this lab we will use Snowflake's built in [`COPY`](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table.html) capabilities. If you did not create the resources in the *Elevated Rights and CSP Resources* section, then an alternative will be provided in the penultimate step.

First we will create a file with data that suits our needs by copying some data into a file from the sample data Snowflake supplies out of the box. For these SQL statements, you can simply pick a number each time you run them, but if you run them many times in rapid succession be careful to pick a different number each imte. Use that number in the SQL where you see `RANDOMNUMBER`.
```
use role CRYPTO_PIPE_RAW_USER;
COPY INTO @CRYPTODEMO.UNENCRYPTED.cyptostream_stage/testTransformOnLoad<RANDOMNUMBER>.csv
  FROM (
        SELECT 
            C.C_LAST_NAME as data_stuff,
            D.CD_DEMO_SK as id_thing, 
            '<RANDOMNUMBER>' as batch_id
        FROM 
            SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER C, 
            SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER_DEMOGRAPHICS D  
        WHERE
            C.C_CUSTOMER_SK = D.CD_DEMO_SK
        QUALIFY 
            ROW_NUMBER() OVER (PARTITION BY C.C_LAST_NAME ORDER BY C.C_LAST_NAME) = 1
        LIMIT 5 -- you can use as many rows as you like by changing this
       )
  FILE_FORMAT = (FORMAT_NAME = CRYPTODEMO.UNENCRYPTED.cyptostream_csv_format)
;
```

Using client side encryption would be recommended in a real world implamentation of this. What that provides is maximum security for the sensitive information being loaded. It means that the file contianing this information will be encrypted by your side fo the conversation and Snowflake would only be able to process it when your organization supplies the key. This code is a modified version of the AWS sample for doing Client Side Encryption. It requires a number of different Java modules to run as is, and the second block of code shows how it would be called at the command line. You can also take this as guidance and apply your own approach to this, as long as it conforms to the AWS requirements. Of course, you can also apply a similar approach for other CSPs as is appropriate for your operations. 

```
/*
 * Copyright 2018-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * 
 * This file is licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License. A copy of
 * the License is located at
 * 
 * http://aws.amazon.com/apache2.0/
 * 
 * This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */

// snippet-sourcedescription:[S3ClientSideEncryptionSymMasterKey.java demonstrates how to upload and download encrypted objects using S3 with a client-side symmetric master key.]
// snippet-service:[s3]
// snippet-keyword:[Java]
// snippet-sourcesyntax:[java]
// snippet-keyword:[Amazon S3]
// snippet-keyword:[Code Sample]
// snippet-keyword:[PUT Object]
// snippet-keyword:[GET Object]
// snippet-sourcetype:[full-example]
// snippet-sourcedate:[2019-01-28]
// snippet-sourceauthor:[AWS]
// snippet-start:[s3.java.s3_client_side_encryption_sym_master_key.complete]

import com.amazonaws.AmazonServiceException;
import com.amazonaws.SdkClientException;
import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3EncryptionClientBuilder;
import com.amazonaws.services.s3.model.*;

import org.apache.commons.cli.*;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.io.*;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;

public class S3ClientSideEncryptionSymMasterKey {

    public static void main(String[] args) throws Exception {
        //silly defaults to show the variables we need
        Regions clientRegion = Regions.DEFAULT_REGION;
        String bucketName = "*** Bucket name ***";
        String objectKeyName = "*** our Filename ***";
	    String filePath = "*** our Filepath ***";
        String keyString = "12345678901234567890123456789012"; // 32 chars = 256 bit key

        // grab real settings using Apache Commons CLI library
        CommandLineParser parser = new DefaultParser();

        // create the Options
        Options options = new Options();
        options.addOption( "r", "region", true, "AWS region where S3 bucket lives" );
        options.addOption( "b", "bucket", true, "AWS S3 bucket name" );
        options.addOption( "f", "filename", true, "Name of file to be uploaded" );
        options.addOption( "p", "filepath", true, "Path to file to be uploaded" );
        options.addOption( "k", "key", true, "Plain text string of secret key not encoded" );
        
        try {
            // parse the command line arguments
            CommandLine line = parser.parse( options, args );
        
            // make the help 
            HelpFormatter formatter = new HelpFormatter();

            // validate that options are set correctly
            if( line.hasOption( "r" ) ) {
	            clientRegion = Regions.fromName( line.getOptionValue( "r" ) );
            } else {
                formatter.printHelp("S3ClientSideEncryptionSymMasterKey CLI", options);
                System.exit(1);
            }
            if( line.hasOption( "b" ) ) {
	            bucketName = line.getOptionValue( "b" );
            } else {
                formatter.printHelp("S3ClientSideEncryptionSymMasterKey CLI", options);
                System.exit(1);
            }
            if( line.hasOption( "f" ) ) {
	            objectKeyName = line.getOptionValue( "f" );
            } else {
                formatter.printHelp("S3ClientSideEncryptionSymMasterKey CLI", options);
                System.exit(1);
            }
            if( line.hasOption( "p" ) ) {
	            filePath = line.getOptionValue( "p" );
            } else {
                formatter.printHelp("S3ClientSideEncryptionSymMasterKey CLI", options);
                System.exit(1);
            }
            if( line.hasOption( "k" ) ) {
	            keyString = line.getOptionValue( "k" );
            } else {
                formatter.printHelp("S3ClientSideEncryptionSymMasterKey CLI", options);
                System.exit(1);
            }
        }
        catch( ParseException exp ) {
            System.out.println( "Unexpected exception:" + exp.getMessage() );
        }

        String fullPath = filePath + "/" + objectKeyName;
        File file = new File(fullPath);

        /*
        * This is how you would generate and manage a dynamic key.
        * We want to use the same key across uses, so we will make
        * one to use and apply it both here and in Snowflake. But
        * keeping this code here for reference.
        *
        // Generate a symmetric 256-bit AES key.
        KeyGenerator symKeyGenerator = KeyGenerator.getInstance("AES");
        symKeyGenerator.init(256);
        SecretKey symKey = symKeyGenerator.generateKey();

        // To see how it works, save and load the key to and from the file system.
        saveSymmetricKey(masterKeyDir, masterKeyName, symKey);
        System.out.println("masterKeyName: " + masterKeyName);
        System.out.println("masterKeyDir: " + masterKeyDir);
        symKey = loadSymmetricAESKey(masterKeyDir, masterKeyName, "AES");
        System.out.println(symKey);
        */

        //Make our own 256 bit key
        SecretKey key = new SecretKeySpec(keyString.getBytes(), "AES"); 
        
        // output the base64 key to use with Snowflake stage
        // only here for convenience
        String encodedKey = Base64.getEncoder().encodeToString(key.getEncoded());
        System.out.println("Base64 Encoded Key: " + encodedKey);

        try {
            // Create the Amazon S3 encryption client.
            EncryptionMaterials encryptionMaterials = new EncryptionMaterials(key);
            AmazonS3 s3EncryptionClient = AmazonS3EncryptionClientBuilder.standard()
                    .withCredentials(new ProfileCredentialsProvider())
                    .withEncryptionMaterials(new StaticEncryptionMaterialsProvider(encryptionMaterials))
                    .withRegion(clientRegion)
                    .build();

            // Upload a new object. The encryption client automatically encrypts it.
            byte[] plaintext = "S3 Object Encrypted Using Client-Side Symmetric Master Key.".getBytes();
            System.out.println("Putting file in bucket: " + bucketName);
            s3EncryptionClient.putObject(new PutObjectRequest(
                bucketName,
                objectKeyName,
	            file));

            // not needed for this example
            // Download and decrypt the object.
            // S3Object downloadedObject = s3EncryptionClient.getObject(bucketName, objectKeyName);
            // byte[] decrypted = com.amazonaws.util.IOUtils.toByteArray(downloadedObject.getObjectContent());
        } catch (AmazonServiceException e) {
            // The call was transmitted successfully, but Amazon S3 couldn't process 
            // it, so it returned an error response.
            e.printStackTrace();
        } catch (SdkClientException e) {
            // Amazon S3 couldn't be contacted for a response, or the client
            // couldn't parse the response from Amazon S3.
            e.printStackTrace();
        }
    }

    // used with dynamic keys
    private static void saveSymmetricKey(String masterKeyDir, String masterKeyName, SecretKey secretKey) throws IOException {
        X509EncodedKeySpec x509EncodedKeySpec = new X509EncodedKeySpec(secretKey.getEncoded());
        FileOutputStream keyOutputStream = new FileOutputStream(masterKeyDir + File.separator + masterKeyName);
        keyOutputStream.write(x509EncodedKeySpec.getEncoded());
        keyOutputStream.close();
    }

    // used with dynamic keys
    private static SecretKey loadSymmetricAESKey(String masterKeyDir, String masterKeyName, String algorithm)
            throws IOException, NoSuchAlgorithmException, InvalidKeySpecException, InvalidKeyException {
        // Read the key from the specified file.
        File keyFile = new File(masterKeyDir + File.separator + masterKeyName);
        FileInputStream keyInputStream = new FileInputStream(keyFile);
        byte[] encodedPrivateKey = new byte[(int) keyFile.length()];
        keyInputStream.read(encodedPrivateKey);
        keyInputStream.close();

        // Reconstruct and return the master key.
        return new SecretKeySpec(encodedPrivateKey, "AES");
    }
}

// snippet-end:[s3.java.s3_client_side_encryption_sym_master_key.complete]
```

Here is an example of how this code might be used at the command line. You would download the file created in the previous step, and then run this code to encrypt that file and upload it in that encrypted form to the Snowflake stage location. In this example, we use a *terribe* key as an example, `12345678901234567890123456789012`. This serves to show the minumum length of the key, which is 32 charachters, but this very simplistic key should never be used in production. Note that the program will output the base64 encoded version of the key that can then be used in the `COPY` SQL statement in the last step. Run this between the first and second blocks of SQL in the previous step. 

> NOTE: This example uses a key string, `12345678901234567890123456789012`, which should *NEVER* be used to protect an real sensitive information. 

```
$ aws s3 cp s3://<YOURFULLSTORAGEURIANDPATH>/testTransformOnLoad999.csv_0_0_0.csv.gz ./
download: s3://<YOURFULLSTORAGEURIANDPATH>/testTransformOnLoad999.csv_0_0_0.csv.gz to ./testTransformOnLoad999.csv_0_0_0.csv.gz
$ java -cp .:/full/path/v1/aws-java-sdk-1.11.868/lib/aws-java-sdk-1.11.868.jar:/full/path/v1/aws-java-sdk-1.11.868/third-party/lib/*:/full/path/commons-cli/commons-cli-1.4/commons-cli-1.4.jar S3ClientSideEncryptionSymMasterKey -b <YOURFULLSTORAGEURIANDPATH> -f testTransformOnLoad999.csv_0_0_0.csv.gz -k 12345678901234567890123456789012 -p ./ -r <YOURREGION>
Base64 Encoded Key: MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=
Putting file in bucket: <YOURFULLSTORAGEURIANDPATH>
```



<!-- ------------------------ -->

## Kick Off Tasks by Inserting Into Raw Table
Duration: 6

This copies the data from the file into the raw table to start the automated process of encrypting and inserting the data into the target table. Be sure to use the same `RANDOMNUMBER` value as you did in the last block of SQL. If you wish to also use the Client Side Encryption options, then see the next step (*Copy with Client Side Encryption*) for how to do that. Those steps would be inserted between the preceeding and the following blocks of SQL.
```
COPY INTO CRYPTODEMO.UNENCRYPTED.raw_data 
  FROM (
        select t.$1, t.$2, t.$3 
        from @CRYPTODEMO.UNENCRYPTED.cyptostream_stage/testTransformOnLoad<RANDOMNUMBER>.csv t
    )
  -- only use this encryption line when using the Client Side Encryption options
  --ENCRYPTION = ( TYPE = 'AWS_CSE' MASTER_KEY = '<BASE64ENCODEDCSEKEY>' )
  FILE_FORMAT = (FORMAT_NAME = CRYPTODEMO.UNENCRYPTED.cyptostream_csv_format)
  ON_ERROR = CONTINUE
  PURGE = TRUE;
;
```

If you did not have the rights or resources to run the steps using Elevated Rights and CSP Resources, you can still see how the `ENCRYPT_RAW` function is used to process the data by doing several steps manually. 

To insert data into the raw table, you can use the same SQL from the `COPY` in a `INSERT AS SELECT` syntax:
```
use role CRYPTO_PIPE_RAW_USER;
insert into CRYPTODEMO.UNENCRYPTED.raw_data 
        SELECT 
            C.C_LAST_NAME as data_stuff,
            D.CD_DEMO_SK as id_thing, 
            '999' as batch_id
        FROM 
            SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER C, 
            SNOWFLAKE_SAMPLE_DATA.TPCDS_SF100TCL.CUSTOMER_DEMOGRAPHICS D  
        WHERE
            C.C_CUSTOMER_SK = D.CD_DEMO_SK
        QUALIFY 
            ROW_NUMBER() OVER (PARTITION BY C.C_LAST_NAME ORDER BY C.C_LAST_NAME) = 1
        LIMIT 5;
```

<!-- ------------------------ -->
## Watch Progress as Tasks Move Data or Move it Manually
Duration: 5

Once data is inserted into the raw table, the tasks will kick in and process it. Run this SQL to watch the progress as the data flows from raw to stage to target. You would run this several times over a 5-7 minute period to see the data move through a full cycle. At the end you expect the count to increate in the target table by the amount it processed through the raw and stage tables. 
```
use role CRYPTO_PIPE_CONVENIENCE_SHOULD_NOT_EXIST;
select (select count(*) from CRYPTODEMO.UNENCRYPTED.raw_data) as RAWCOUNT, (select count(*) from CRYPTODEMO.ENCRYPTED.staged_data) as STAGECOUNT, (select count(*) from CRYPTODEMO.ENCRYPTED.target_table) as TARGETCOUNT;
```

If you also could not create the Tasks, then you can run each of the Stored Procedures in succession as the owners:
```
use role CRYPTO_PIPE_RAW_USER;
CALL CRYPTODEMO.UNENCRYPTED.move_and_encrypt_raw_data_to_stage()
CALL CRYPTODEMO.UNENCRYPTED.delete_raw_based_on_staged_data()

use role CRYPTO_PIPE_PROD_USER;
CALL CRYPTODEMO.ENCRYPTED.staged_to_target_data_insert()
CALL CRYPTODEMO.ENCRYPTED.delete_staged_based_on_target_table()
```

In the end, you should see the same results as if you had all the other rights and resources set up for automation. 

<!-- ------------------------ -->
## Read Data with Other Systems Using Same Key Materials (Optional)
Duration: 5

Consuming the data using the keys and other cryptographic materials is the next step in a real world application of this pipeline. This is an example of how to do that using Python calling to the AWS Secrets Manager. If you delivered the key materials in a different way, you can adjust this code to call that - or even simply pass these key materials when needed in the code. If you do use the AWS method, this code assumes you have an AWS credential configured in the session with proper access to interact with AWS. 

```
from Crypto.Cipher import AES
import json
import snowflake.connector
import boto3
import getpass

# define our decryption function
def decrypt_data(ciphertext:bytes, nonce:bytes, tag:bytes, key:bytes, additionalData:bytes):
    aesCipher = AES.new(key, AES.MODE_GCM, nonce)

    aesCipher.update(additionalData)
    
    plaintext = aesCipher.decrypt_and_verify(ciphertext, tag)

    return plaintext

# define function for getting an encrypted row from Snowflake
def get_single_encrypted_result_from_snowflake(sfuser:str, sfrolei:str, sfpass:str):
    con = snowflake.connector.connect(
                user=sfuser,
                password=sfpass,
                account='<YOURSNOWFLAKEACCOUNT>',
                warehouse='<YOURWAREHOUSE>',
                database='CRYPTODEMO', # be sure to change this if you did not use the default for this lab
                schema='ENCRYPTED', # be sure to change this if you did not use the default for this lab
                role=sfrole
                )
    
    # be sure to change this if you did not use the default for this lab
    getCipherJsonSQL = 'select data_stuff::varchar from CRYPTODEMO.ENCRYPTED.target_table limit 1'

    cipherJson = con.cursor().execute(getCipherJsonSQL).fetchone()

    # Snowflake output is like:
    # {
    #  "ciphertext": "AE27A735B765E9B6CD",
    #  "iv": "616E4956616B614E4F4E4345",
    #  "tag": "5196990E38F701BCE848A7562CEDD7C9"
    # }

    # process the row from Snowflake 
    oneRow = cipherJson[0]

    return oneRow

# define function for getting secrets from AWS secrets manager
# you can also simply change this to return your key materials if you didn't use a secrets manager
def get_secret_from_aws_secrets_manager():
    secret_name = "<YOURSECRETNAME>"
    region_name = "<YOURREGION>"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            
            return secret
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            
            return decoded_binary_secret

# the creds for talking to snowflake
sfuser = input("Snowflake Username: ")
sfrole = input("Snowflake Role: ")
sfpass = getpass.getpass("Snowflake Password: ")

# get the encrypted data from Snowflake (a pseudorandom, single row)
rowFromSnowflakeRaw = get_single_encrypted_result_from_snowflake(sfuser, sfrole, sfpass)
print("The raw results from Snowflake: ", rowFromSnowflakeRaw, "\n")

# cypto materials required
cryptoMaterialsRaw = get_secret_from_aws_secrets_manager()
print("The raw secret from AWS Secrets Manager: ", cryptoMaterialsRaw, "\n")

# convert retrieved row and crypto materials to json objects
snowflakeRowJson = json.loads(rowFromSnowflakeRaw)
cryptoMaterialJson = json.loads(cryptoMaterialsRaw)

# extract strings required
ciphertextStr = snowflakeRowJson['ciphertext']
ivNonceStr = snowflakeRowJson['iv']
tagStr = snowflakeRowJson['tag']
keyStr = cryptoMaterialJson['key']
adStr = cryptoMaterialJson['ad']

# sanity check 
print("The ciphertext (str) is: ", ciphertextStr, "\n")
print("The iv/nonce (str) is: ", ivNonceStr, "\n")
print("The tag (str) is: ", tagStr, "\n")
print("The key (str) is: ", keyStr, "\n")
print("The additional data for AEAD (str) is: ", adStr, "\n")

# get bytes for each item to use in decryption
ciphertextBytes = bytes.fromhex(ciphertextStr)
ivNonceBytes = bytes.fromhex(ivNonceStr)
tagBytes = bytes.fromhex(tagStr)
keyBytes = bytes(keyStr, 'utf-8')
adBytes = bytes(adStr, 'utf-8')

# run the decryption
decryptedText = decrypt_data(ciphertextBytes, ivNonceBytes, tagBytes, keyBytes, adBytes)

print("The final decrypted result is: ", decryptedText, "\n")
```

When you run this, the interaction and output will look something like this:
```
$ python3 cryptoPipelineReadRow.py
Username: ReedRichards
Role: fantasticScientists
Password:
The raw results from Snowflake:  {"ciphertext":"AE27A735B765E9B6CD","iv":"616E4956616B614E4F4E4345","tag":"5196990E38F701BCE848A7562CEDD7C9"}

The raw secret from AWS Secrets Manager:  {"key":"areallybadkeystrareallybadkeystr","ad":"additional-data-for-AEAD"}

The ciphertext (str) is:  AE27A735B765E9B6CD

The iv/nonce (str) is:  616E4956616B614E4F4E4345

The tag (str) is:  5196990E38F701BCE848A7562CEDD7C9

The key (str) is:  areallybadkeystrareallybadkeystr

The additional data for AEAD (str) is:  additional-data-for-AEAD

The final decrypted result is:  b'data worth encrypting'
```