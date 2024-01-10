author: Vitaly Markov
id: getting_started_with_snowddl
summary: Getting started with object management tool SnowDDL
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering

# Getting Started with object management tool SnowDDL
<!-- ------------------------ -->
## Overview
Duration: 1

<img src="assets/logo.png" width="150" />

SnowDDL is a [declarative-style](https://www.snowflake.com/blog/embracing-agile-software-delivery-and-devops-with-snowflake/) tool for object management automation in Snowflake.

It is not intended to replace other tools entirely, but to provide an alternative approach focused on practical data engineering challenges.

### Prerequisites
- Basic knowledge of Python;
- Basic knowledge of YAML;
- Basic knowledge of terminal commands;

### What You’ll Learn
- What makes SnowDDL different from schemachange and Terraform;
- How to install SnowDDL and create administration user;
- How to use SnowDDL CLI interface to apply bundled test configs;
- How to create and apply your own YAML config;

### What You’ll Need
- Python 3.7+;
- Snowflake account for tests (e.g. [trial account](https://signup.snowflake.com/) or [new account within your organization](https://docs.snowflake.com/en/sql-reference/sql/create-account.html));

### What You’ll Build
- A working example of SnowDDL config applied to your Snowflake account.

<!-- ------------------------ -->
## Main features
Duration: 3

This section describes main features of SnowDDL.

### 1) SnowDDL is "stateless"

Unlike [schemachange](https://github.com/Snowflake-Labs/schemachange) and [Terraform](https://github.com/chanzuckerberg/terraform-provider-snowflake), SnowDDL does not maintain any kind of "state". Instead, it reads current metadata from Snowflake account, compares it with desired configuration and generates DDL commands to apply changes.

### 2) SnowDDL can revert changes

SnowDDL can revert object schema to any point in the past. You may simply checkout previous version of configuration from Git and apply it with SnowDDL.

### 3) SnowDDL supports ALTER COLUMN

Most changes to Snowflake table structure requires full re-creation of table and micro-partitions with data. For large tables it may incur significant additional costs.

But some changes are possible with [ALTER TABLE ... ALTER COLUMN](https://docs.snowflake.com/en/sql-reference/sql/alter-table-column.html) statement, which executes instantly and costs nothing. SnowDDL detects if it is possible to use ALTER TABLE before suggesting costly CREATE OR REPLACE TABLE ... AS SELECT.

### 4) SnowDDL provides built-in "role hierarchy" model

Snowflake documentation mentions benefits of [role hierarchy](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html#roles), but it does not provide any real world examples.

SnowDDL [offers](https://docs.snowddl.com/guides/role-hierarchy) a well thought 3-tier role hierarchy model. It is easy to understand, largely automated and requires minimal configuration. Also, it is crystal clear for security officers and external auditors.

### 5) SnowDDL re-creates invalid views automatically

Views may become invalid when underlying objects were changed. SnowDDL detects such views using a free `.describe()` call, and re-creates such views if necessary.

### 6) SnowDDL simplifies code review

DDL queries are classified into ["safe" and "unsafe"](https://docs.snowddl.com/guides/other/safe-unsafe) categories.

"Safe" queries can be applied and reverted with little to no risk (e.g. CREATE). "Safe" queries usually do not require code review and can be applied immediately.

"Unsafe" queries may potentially cause loss of data or security issues (e.g. ALTER, DROP). "Unsafe queries" usually do require more attention.

This classification helps to manage code review process better, but it is optional.

### 7) SnowDDL supports creation of isolated "environments" for individual developers and CI/CD scripts

Multiple independent versions of the same configuration can be applied to one Snowflake account using [env prefix](https://docs.snowddl.com/guides/other/env-prefix). Unique prefix will be added to name of each account-level object, which allows multiple developers to work on the same code simultaneously without conflicts.

It is also helpful for automated testing, when each set of tests will be executed in a separate "environment".

### 8) SnowDDL strikes a good balance between dependency management overhead and parallelism

Different object types are resolved sequentially. But objects of the same type are resolved [in parallel](https://docs.snowddl.com/guides/other/dependency-management). It provides great performance for configurations with large number of objects, but it also simplifies dependency management.

### 9) SnowDDL configuration can be generated dynamically in Python code

SnowDDL can run in "basic mode", using provided CLI interface and YAML configs. It should be enough for most users.

However, it can also run in ["advanced mode"](https://docs.snowddl.com/advanced/architecture-overview), when configuration is generated dynamically in Python code.

### 10) SnowDDL can manage packages for Java and Python UDF scripts natively

Recently, Snowflake introduced [Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/index.html) and [UDF functions](https://docs.snowflake.com/en/sql-reference/sql/create-function.html) written in Java, Scala, Python. Such functions may rely on external packages and libraries, which should be uploaded to internal stages. Changes in packages should be synchronised with changes in UDF function code, and SnowDDL can do it for you using special object type [STAGE FILE](https://docs.snowddl.com/basic/yaml-configs/stage-file).

<!-- ------------------------ -->
## Snowflake account & administration user
Duration: 5

It is a good practice to create a dedicated user for SnowDDL and avoid using `ACCOUNTADMIN` super-user.

1. Create a new [Snowflake Trial Account](https://signup.snowflake.com/) or create a new [account within your organization](https://docs.snowflake.com/en/sql-reference/sql/create-account.html).
2. Create administration user for SnowDDL. Replace `[password]` placeholder with [randomly generated password](https://www.random.org/passwords/?num=5&len=16&format=html&rnd=new) of your choice:
   ```sql
   USE ROLE ACCOUNTADMIN;

   CREATE ROLE SNOWDDL_ADMIN;

   GRANT ROLE SYSADMIN TO ROLE SNOWDDL_ADMIN;
   GRANT ROLE SECURITYADMIN TO ROLE SNOWDDL_ADMIN;

   CREATE USER SNOWDDL
   PASSWORD = '[password]'
   DEFAULT_ROLE = SNOWDDL_ADMIN;

   GRANT ROLE SNOWDDL_ADMIN TO USER SNOWDDL;
   GRANT ROLE SNOWDDL_ADMIN TO ROLE ACCOUNTADMIN;
   ```
3. (Optional) If you want to run `CREATE OR REPLACE TABLE ... AS SELECT` queries using SnowDDL, you should also create a `WAREHOUSE` for this purpose:
   ```sql
   USE ROLE ACCOUNTADMIN;

   CREATE WAREHOUSE SNOWDDL_WH
   WAREHOUSE_SIZE = 'XSMALL'
   AUTO_SUSPEND = 60
   AUTO_RESUME = TRUE
   INITIALLY_SUSPENDED = TRUE;

   GRANT USAGE, OPERATE ON WAREHOUSE SNOWDDL_WH TO ROLE SNOWDDL_ADMIN;

   ALTER USER SNOWDDL SET DEFAULT_WAREHOUSE = SNOWDDL_WH;
   ```

**Important!** Please do not use production accounts with real data to test any object management tools, including SnowDDL.

<!-- ------------------------ -->
## Python & bundled config tests
Duration: 5

Run the following commands in terminal.

1. Install SnowDDL.
   ```
   pip install snowddl
   ```
2. Apply [first version](https://github.com/littleK0i/snowddl/tree/master/snowddl/_config/sample01_01) of sample config (provided with SnowDDL installation). Replace `[account_identifier]` placeholder with Snowflake [account identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html).
   ```
   snowddl \
   -c sample01_01 \
   -a [account_identifier] \
   -u snowddl \
   -p [password] \
   --apply-unsafe \
   apply
   ```

   Observe database `SNOWDDL_DB` in Snowflake account. Check list of warehouses and roles.
3. Apply [second version](https://github.com/littleK0i/snowddl/tree/master/snowddl/_config/sample01_02) of sample config (provided with SnowDDL installation).
   ```
   snowddl \
   -c sample01_02 \
   -a [account_identifier] \
   -u snowddl \
   -p [password] \
   --apply-unsafe \
   apply
   ```

   Observe logs. Some objects will be altered, some objects will be dropped.
4. Reset Snowflake account to the original state. All objects created earlier will be dropped.
   ```
   snowddl \
   -c sample01_02 \
   -a [account_identifier] \
   -u snowddl \
   -p [password] \
   --apply-unsafe \
   --destroy-without-prefix \
   destroy
   ```

Congratulations!

Now you are ready to create your own config and start experimenting.

<!-- ------------------------ -->
## Creating custom config
Duration: 5

It is easy to create a custom config from scratch.

1. Create a new empty directory for **config root**, choose any name you like.
2. Create **database directory** inside config root: `test_db`.
3. Create **schema directory** inside database directory: `test_schema`.
4. Create **object type directory** inside schema directory: `table`.
5. Create **YAML file** inside `table` object type directory: `test_table.yaml`. File contents:
   ```yaml
   columns:
     actor_id: NUMBER(10,0) NOT NULL
     first_name: VARCHAR(45) NOT NULL
     last_name: VARCHAR(45) NOT NULL
     last_update: TIMESTAMP_NTZ(3)

   primary_key: [actor_id]
   ```
6. Create **object type directory** inside schema directory: `view`.
7. Create **YAML file** inside `view` object type directory: `test_view.yaml`. File contents:
   ```yaml
   text: |-
     SELECT actor_id
       , first_name
       , last_name
       , first_name || ' ' || last_name AS full_name
     FROM test_table
     WHERE last_update >= DATEADD(DAY, -90, CURRENT_DATE)

   is_secure: true
   ```
8. Create **YAML file** for warehouses in config root: `warehouse.yaml`. File contents:
   ```yaml
   test_wh_1:
     size: XSMALL
     auto_suspend: 60

   test_wh_2:
     size: SMALL
     auto_suspend: 120
   ```
9. The final object tree should look like this:
   ```
   [config_root_directory]
   |-- test_db (dir)
       |-- test_schema (dir)
           |- table (dir)
               |- test_table.yaml
           |- view (dir)
               |- test_view.yaml
   warehouse.yaml
   ```
10. Run command in terminal to apply config. Replace placeholder `[config_directory]` with path to root config directory:
    ```
    snowddl \
    -c [config_directory] \
    -a [account_identifier] \
    -u snowddl \
    -p [password] \
    --apply-unsafe \
    apply
    ```

    Observe objects created in Snowflake account.


<!-- ------------------------ -->
## Further topics
Duration: 1

Now you are ready to learn more advanced topics related to SnowDDL:

- [CLI interface options](https://docs.snowddl.com/basic/cli)
- [YAML configs for all supported object types](https://docs.snowddl.com/basic/yaml-configs)
- [Role hierarchy](https://docs.snowddl.com/guides/role-hierarchy)
- [Env prefix](https://docs.snowddl.com/guides/other/env-prefix)
- [Limitations & workarounds](https://docs.snowddl.com/guides/other/limitations-and-workarounds)
- [Fivetran](https://docs.snowddl.com/guides/other/fivetran)

Also, if you want to manage schema objects in ONE database only, consider simplified [SingleDB mode](https://docs.snowddl.com/single-db/overview).

Please use [GitHub "Issues"](https://github.com/littleK0i/SnowDDL/issues) to report bugs and technical problems.

Please use [GitHub "Discussions"](https://github.com/littleK0i/SnowDDL/discussions) to ask questions and provide feedback.

Enjoy!
