author: Daniel Myers
id: getting_started_with_native_apps
summary: Follow this tutorial to get up and running with your first Snowflake Native Application
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Native Apps 

# Getting Started with Snowflake Native Apps
<!-- ------------------------ -->
## Overview 
Duration: 3

> aside negative
> 
> **Important**
> Snowflake Native Apps are currently only available on AWS.  Ensure your Snowflake deployment or trial account uses AWS as the cloud provider. Native Apps will be available on other major cloud providers soon.

![Native Apps Framework](assets/app_framework.png)

In this Quickstart, you'll build your first Snowflake Native Application. 

Snowflake Native Applications provide developers a way to package applications for consumption by other Snowflake users. The Snowflake Marketplace is a central place for Snowflake users to discover and install Snowflake Native Applications. 

 The application you'll build will visualize data from suppliers of raw material, used for inventory and supply chain management. Let's explore the application from the perspective of the application provider and an application consumer.

– **Provider** – In this Quickstart, the provider of the app is a supply chain management company. They have proprietary data on all sorts of shipments. They've built the app, bundled it with access to their shipping data, and listed it on the Snowflake Marketplace so that manufacturers can use it in combination with manufacturing supply chain data to get a view of the supply chain.

– **Consumer** – The consumer of the app manufactures a consumer product – in this case it's ski goggles. They work with several suppliers of the raw material used to manufacture the ski goggles. When the consumer runs the application in their account, the application will render multiple charts to help them visualize information related to:

- **Lead Time Status** The lead time status of the raw material procurement process.
- **Raw Material Inventory** Inventory levels of the raw materials. 
- **Purchase Order Status** The status of all the purchase orders (shipped, in transit; completed)
- **Supplier Performance** The performance of each raw material supplier, measured in terms lead time, quality, and cost of raw materials delivered by the supplier.

The data powering the charts is a combination of the consumer's own supply chain data (orders and site recovery data) in their Snowflake account, while the provider is sharing shipping data to provide an enriched view of the overall supply chain.

**Note**

- This Quickstart is limited to a single-account installation. You'll use a single Snowflake account to experience the app from the provider's perspective and from the consumer's perspective. Listing to the Snowflake Marketplace and versions / release directives are outside of the scope of this guide.

- This Quickstart introduces a new tool called Snowflake CLI. Please refer to the installation instructions below to get set up.

Let's get started!

![streamlit](assets/streamlit.png)

### Prerequisites
- Snowflake trial account on AWS
- Beginner Python knowledge

> aside negative
> 
> **Important**
> Snowflake Native Apps are currently only available on AWS.  Ensure your Snowflake deployment or trial account uses AWS as the cloud provider. Native Apps will be available on other major cloud providers soon.

### What You’ll Learn 
- Snowflake Native App Framework
- Snowflake Native App deployment
- Snowflake Native App sharing and Marketplace Listing


### What You’ll Need 
- [VSCode](https://code.visualstudio.com/download) Installed
- [SnowflakeCLI](https://github.com/Snowflake-Labs/snowcli/tree/main) Installed

### What You’ll Build 
- A Snowflake Native Application

<!-- ------------------------ -->
## Architecture & Concepts
Duration: 2

Snowflake Native Apps are a new way to build data intensive applications. Snowflake Native Apps benefit from running *inside* Snowflake and can be installed from the Snowflake Marketplace, similar to installing an app on a smart phone. Snowflake Native Apps can read and write data to a user's database (when given permission to do so). Snowflake Native Apps can even bring in new data to their users, providing new insights. 

When discussing Snowflake Native Apps, there are two personas to keep in mind: **Providers** and **Consumers**.

- **Providers:** Developers of the app. The developer or company publishing an app to the Snowflake Marketplace is an app provider.

- **Consumer:** Users of an app. When a user installs an app from the Snowflake Marketplace, they are a consumer of the app.

The diagram below demonstrates this model:
 
![diagram](assets/deployment.png)

<!-- ------------------------ -->
## Clone Sample Repo & Directory Structure
Duration: 3

There are a few different ways to create a directory structure for our Snowflake Native Application from the [starter project](https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps).

**Option 1: Using the Snowflake CLI (Recommended)**
```bash
snow app init sf_native_app_quickstart --template-repo https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps.git
```
This command requires the use of git. If you do not have git installed, you can also download the code directly from [GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps/archive/refs/heads/main.zip) and extract it to a local folder.

**Option 2: Using Git directly**
```bash
git clone https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps.git
```

**Directory Structure**
This repository contains all of our starter code for our native app. Throughout the rest of this tutorial we will be modifying various parts of the code to add functionality and drive a better understanding of what is happening at each step in the process.


Let's explore the directory structure:

```plaintext
|-- repos
    |-- .gitignore
    |-- LICENSE
    |-- snowflake.yml
    |-- app
        |-- data
        |   |-- order_data.csv
        |   |-- shipping_data.csv
        |   |-- site_recovery_data.csv
        |-- src
        |   |-- manifest.yml
        |   |-- libraries
        |   |   |-- environment.yml
        |   |   |-- procs.py
        |   |   |-- streamlit.py
        |   |   |-- udf.py
        |   |-- scripts
        |       |-- setup.sql
        |-- test
            |-- Test_App_Locally.sql
```

There are two main directories that we will be using:

`src`

- the `src` directory is used to store all of our various source code including stored procedures, user defined functions (UDFs), our streamlit application, and even our installation script `setup.sql`.

`test`

- the `test` directory contains both our sample data used for seeding our application tests, and our test script `Test_App_Locally.sql`

There is an additional file called `snowflake.yml`, which is used by the Snowflake CLI.

<!-- ------------------------ -->
## Manifest.yml
Duration: 3

The `manifest.yml` file is an important aspect of a Snowflake Native App. This file defines some metadata about the app, configuration options, and provides references to different artifacts of the application.

Let's take a look at the one provided in the GitHub repository:

```
#version identifier
manifest_version: 1

version:
  name: V1
  label: Version One
  comment: The first version of the application

#artifacts that are distributed from this version of the package
artifacts:
  setup_script: scripts/setup.sql
  default_streamlit: app_instance_schema.streamlit
  extension_code: true

#runtime configuration for this version
configuration:
  log_level: debug
  trace_level: off

references:
  - order_table:
      label: "Orders Table" 
      description: "Select table"
      privileges:
        - SELECT
      object_type: Table 
      multi_valued: false 
      register_callback: app_instance_schema.update_reference 
  - site_recovery_table:
      label: "Site Recovery Table" 
      description: "Select table"
      privileges:
        - SELECT
      object_type: Table 
      multi_valued: false 
      register_callback: app_instance_schema.update_reference

```

`manifest_version`

- this is the Snowflake defined manifest file version. If there are new configuration options or additions, the version number will change.

`version`

- this is a user-defined version for the application. This version identifier is used when creating the app package.

`artifacts`

- this contains options and definitions for where various parts of our package is located. In particular the `setup_script` option is required.

`configuration`

- this is used to define what logging we want to use in our application. During development we will want a log level of `debug`. 

`references`

-  this part of the manifest file contains all the references to Snowflake objects that the Native App needs access to. The Native App Consumer will grant access to the objects when installing or using the application. We will use this in our native app to gain access to the `order_table` and `site_recovery_table`. 

<!-- ------------------------ -->
## Update UDF.py
Duration: 3

To add some new functionality to our application we will modify **UDF.py**. This is the Python file we use to create all our User Defined Functions (UDFs).

```python
def cal_distance(lat1,lon1,lat2,lon2):
   import math
   radius = 3959 # miles == 6371 km
   dlat = math.radians(lat2-lat1)
   dlon = math.radians(lon2-lon1)
   a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
   c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
   d = radius * c
   return dw

# process_supply_day + duration + recovery_weeks * 7 (days)
def cal_lead_time(i,j,k):
   return i + j + k

```

> aside positive
> 
> You can import any package in the `https://repo.anaconda.com/pkgs/snowflake` channel from [Anaconda](https://docs.conda.io/en/latest/miniconda.html)

Let's add a new function that simply outputs "Hello World!"

To do this, copy and paste the code below into **UDF.py**:

```python
def hello_world():
   return "Hello World!"
```

In the next step, we will expose this function to Consumers by adding it to our installation script.


<!-- ------------------------ -->
## Edit Installation Script
Duration: 3

The installation script **setup.sql** defines all Snowflake objects used within the application. This script runs every time a user installs the application into their environment. 

We will use this file to expose our new `hello_world` Python UDF.

```
-- ==========================================
-- This script runs when the app is installed 
-- ==========================================

-- Create Application Role and Schema
create application role if not exists app_instance_role;
create or alter versioned schema app_instance_schema;

-- Share data
create or replace view app_instance_schema.MFG_SHIPPING as select * from shared_content_schema.MFG_SHIPPING;

-- Create Streamlit app
create or replace streamlit app_instance_schema.streamlit from '/libraries' main_file='streamlit.py';

-- Create UDFs
create or replace function app_instance_schema.cal_lead_time(i int, j int, k int)
returns float
language python
runtime_version = '3.8'
packages = ('snowflake-snowpark-python')
imports = ('/libraries/udf.py')
handler = 'udf.cal_lead_time';

create or replace function app_instance_schema.cal_distance(slat float,slon float,elat float,elon float)
returns float
language python
runtime_version = '3.8'
packages = ('snowflake-snowpark-python','pandas','scikit-learn==1.1.1')
imports = ('/libraries/udf.py')
handler = 'udf.cal_distance';

-- Create Stored Procedure
create or replace procedure app_instance_schema.billing_event(number_of_rows int)
returns string
language python
runtime_version = '3.8'
packages = ('snowflake-snowpark-python')
imports = ('/libraries/procs.py')
handler = 'procs.billing_event';

create or replace procedure app_instance_schema.update_reference(ref_name string, operation string, ref_or_alias string)
returns string
language sql
as $$
begin
  case (operation)
    when 'ADD' then
       select system$set_reference(:ref_name, :ref_or_alias);
    when 'REMOVE' then
       select system$remove_reference(:ref_name, :ref_or_alias);
    when 'CLEAR' then
       select system$remove_all_references();
    else
       return 'Unknown operation: ' || operation;
  end case;
  return 'Success';
end;
$$;

-- Grant usage and permissions on objects
grant usage on schema app_instance_schema to application role app_instance_role;
grant usage on function app_instance_schema.cal_lead_time(int,int,int) to application role app_instance_role;
grant usage on procedure app_instance_schema.billing_event(int) to application role app_instance_role;
grant usage on function app_instance_schema.cal_distance(float,float,float,float) to application role app_instance_role;
grant SELECT on view app_instance_schema.MFG_SHIPPING to application role app_instance_role;
grant usage on streamlit app_instance_schema.streamlit to application role app_instance_role;
grant usage on procedure app_instance_schema.update_reference(string, string, string) to application role app_instance_role;
```

Let's add the following code snippet to our `setup.sql` script:

```python
create or replace function app_instance_schema.hello_world()
returns string
language python
runtime_version = '3.8'
packages = ('snowflake-snowpark-python')
imports = ('/libraries/udf.py')
handler = 'udf.hello_world';

grant usage on function app_instance_schema.hello_world() to application role app_instance_role;
```

<!-- ------------------------ -->
## Create App Package
Duration: 2

A Snowflake Application Package is conceptually similar to that of an application installer for a desktop computer (like `.msi` for Windows or `.pkg` for Mac). An app package for Snowflake contains all the material used to install the application later, including the setup scripts. In fact, we will be using this app package in future steps to test our app!

Let's look at the different ways to create an application package.

**Option 1: Using the Snowflake CLI (Recommended)**

In addition to modifying the code files locally, we need to make a few changes to `snowflake.yml` file as well. Add the following snippets under `native_app` section of the file, but do not remove any existing fields:
```yaml
  source_stage: NATIVE_APP_QUICKSTART_SCHEMA.NATIVE_APP_QUICKSTART_STAGE
  package:
    name: NATIVE_APP_QUICKSTART_PACKAGE
  artifacts:
    - src: app/src/*
      dest: ./
```
After adding the above, the `snowflake.yml` file should look like:
```yaml
definition_version: 1
native_app:
  name: sf_native_app_quickstart
  source_stage: NATIVE_APP_QUICKSTART_SCHEMA.NATIVE_APP_QUICKSTART_STAGE
  package:
    name: NATIVE_APP_QUICKSTART_PACKAGE
  artifacts:
    - src: app/src/*
      dest: ./
```
Here, `NATIVE_APP_QUICKSTART_PACKAGE` is the name of the `package` to create, `NATIVE_APP_QUICKSTART_SCHEMA` is a schema within the `package`, and `NATIVE_APP_QUICKSTART_STAGE` is the name of the stage within the `schema`.

Further, all code files under `sf_native_app_quickstart/app/src` will be uploaded to `NATIVE_APP_QUICKSTART_STAGE` as follows:

1. `sf_native_app_quickstart/app/src/manifest.yml` will be uploaded at `@NATIVE_APP_QUICKSTART_STAGE/manifest.yml`.
2. `sf_native_app_quickstart/app/src/scripts/setup.sql` will be uploaded at `@NATIVE_APP_QUICKSTART_STAGE/scripts/setup.sql`.
3. `sf_native_app_quickstart/app/src/libraries/*` will be uploaded at `@NATIVE_APP_QUICKSTART_STAGE/libraries/*`.

As a note, the `package` or any other objects do not exist at the end of these edits. There is a separate command later that will create these objects for you. If you followed this section, you can skip to the next page.

**Option 2: Manually executing SQL** 

To create an application package:

1. Login to your Snowflake account and navigate to `Apps`
2. In the top navigation, click `Packages`
3. Click `+ App Package`
4. Type `NATIVE_APP_QUICKSTART_PACKAGE` for the package name.
5. Select `Distribute to accounts in your organization`

Alternatively, you can use the SQL statement below to do the same thing:

```
-- #########################################
-- PACKAGE SETUP
-- #########################################

CREATE APPLICATION PACKAGE IDENTIFIER('"NATIVE_APP_QUICKSTART_PACKAGE"') COMMENT = '' DISTRIBUTION = 'INTERNAL';
```

Now that we have our `package` created, we need to create our `stage`. To do this, run the following code:

```
-- when we create an app package, snowflake creates a database with the same name. This database is what we use to store all of our packaged snowflake objects.
USE DATABASE NATIVE_APP_QUICKSTART_PACKAGE;

CREATE OR REPLACE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;
USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;

-- we will upload our project files here, directly into our app package
CREATE OR REPLACE STAGE NATIVE_APP_QUICKSTART_STAGE 
	DIRECTORY = ( ENABLE = true ) 
	COMMENT = '';
```

Now that a `stage` has been created, you'll need to upload the application source code into the stage. We'll do this using the Snowflake UI:

1. Login to your Snowflake account and navigate to `Data -> Databases`
2. Select `NATIVE_APP_QUICKSTART_PACKAGE` -> `NATIVE_APP_QUICKSTART_SCHEMA` -> `Stages` -> `NATIVE_APP_QUICKSTART_STAGE`
3. Click the `+ Files` button in the top right.

You'll need to upload **manifest.yml**, **setup.sql**, and all of the files inside of the **libraries/** folder.

4. In the modal that opens, upload the **manifest.yml** file. The file will be added to the stage.

5. Next, you'll upload the **setup.sql** file. Use the modal once again to select this file. Before uploading, use the form near the bottom of the modal to enter a folder name. Enter **scripts**, then upload the file. A folder called **scripts/** will be added to the stage, and the folder will contain the **setup.sql** file.

6. Repeat Step 5 to upload the four files within the **libraries/** folder. Be sure to enter **libraries** in the form at the bottom of the modal so that the folder is also created within the stage.

The file and folder structure within your `NATIVE_APP_QUICKSTART_STAGE` stage should match the structure within the [**src/** folder of the companion repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps/tree/main/app/src). It is important that the structure withiin the stage match structure in the repo so that references to files and artifacts within any of these files do not break. This will ensure that the application can run as intended when it is installed and run in a consumer's account.

<!-- ------------------------ -->
## Upload Provider Shipping Data
Duration: 2

### Create provider table to hold the data

Now, let's create a database that we will use to store provider's shipping data. This is the data that we will share with the application so that the consumer can enrich their own supply chain data with it when they install the app in their account.

The goal is to create the database, warehouse, schema, and defines the table that will hold the shipping data.

**Option 1: Using the Snowflake CLI (Recommended)**

Create a file `provider_setup.sql` in your project directory and copy in the code snippet below.
```sql
CREATE OR REPLACE WAREHOUSE NATIVE_APP_QUICKSTART_WH WAREHOUSE_SIZE=SMALL INITIALLY_SUSPENDED=TRUE;

-- this database is used to store our data
CREATE OR REPLACE DATABASE NATIVE_APP_QUICKSTART_DB;
USE DATABASE NATIVE_APP_QUICKSTART_DB;

CREATE OR REPLACE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;
USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;

-- Load app/data/shipping_data.csv into the table below using Snowsight

CREATE OR REPLACE TABLE MFG_SHIPPING (
  order_id NUMBER(38,0), 
  ship_order_id NUMBER(38,0),
  status VARCHAR(60),
  lat FLOAT,
  lon FLOAT,
  duration NUMBER(38,0)
);
```

Now run the Snowflake CLI command to run all commands in this file.
```bash
snow sql -f provider_setup.sql -c connection_name
```

where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.  

**Option 2: Manually executing SQL** 

You can also run the SQL from the above section in a Snowflake SQL worksheet.

### Upload data into the table

 Next, you'll load data into this table using the Snowflake UI.

1. Login to your Snowflake account and navigate to `Data -> Databases`
2. Select `NATIVE_APP_QUICKSTART_DB` -> `NATIVE_APP_QUICKSTART_SCHEMA` -> `Tables` 
3. From there, select table `MFG_SHIPPING` and upload the **app/data/shipping_data.csv** file from the downloaded repository:
   1. Select `Load Data` in the top right
   2. Select `NATIVE_APP_QUICKSTART_WH` for the warehouse
   3. Click `Browse` and select the corresponding `.csv` file, Click `Next`
   4. Select `Delimited Files (CSV or TSV)` for the File Format
   5. For `Field optionally enclosed by` select `Double quotes`
   6. Click `Next`, repeat for each table. 

### Share the Provider Shipping Data via the Application Package

In order for this data to be available to the application consumer, we'll need to share it in the application package via reference usage. 

The SQL described in the two sections below is identical except for one difference. The SQL aims to:

- Create a schema in the application package that will be used for sharing the shipping data

- Create a view within that schema

- Grant usage on the schema to the application package

- Grant reference usage on the database holding the provider shipping data to the application package

- Grant SELECT privileges on the view to the application package, meaning the app will be able to SELECT on the view once it is installed

This flow ensures that the data is able to be shared securely with the consumer through the application. The objects containing the provider's proprietary shipping data are **never** shared directly with the consumer via a Snowflake Native Application. This means the provider's proprietary data remains safe, secure, and in the provider's Snowflake account. Instead, the application package has reference usage on objects (databases) corresponding to the provider's data, and when a consumer installs the app (i.e., instantiates the application package), they are able to use the shared data through the application.

**Option 1: Using the Snowflake CLI (Recommended)**

Add the SQL below in a new file at `sf_native_app_quickstart/app/scripts/shared_content.sql`.

```sql
-- ################################################################
-- Create SHARED_CONTENT_SCHEMA to share in the application package
-- ################################################################
use database {{package_name}};
create or replace schema shared_content_schema;

use schema shared_content_schema;
create or replace view MFG_SHIPPING as select * from NATIVE_APP_QUICKSTART_DB.NATIVE_APP_QUICKSTART_SCHEMA.MFG_SHIPPING;

grant usage on schema shared_content_schema to share in application package {{package_name}};
grant reference_usage on database NATIVE_APP_QUICKSTART_DB to share in application package {{package_name}};
grant select on view MFG_SHIPPING to share in application package {{package_name}};
```

Here, `package_name` is a pre-defined variable that will be replaced by the name of your `package` from the `snowflake.yml` file when you execute a Snowflake CLI command. 

Next, add the following snippets under `native_app` section of the file, but do not remove any existing fields: 

```yaml
  package:
    warehouse: NATIVE_APP_QUICKSTART_WH
  scripts:
    - app/scripts/shared_content.sql
```

After adding the above, the `snowflake.yml` file should look like:
```yaml
definition_version: 1
native_app:
  name: NATIVE_APP_QUICKSTART
  source_stage: NATIVE_APP_QUICKSTART_SCHEMA.NATIVE_APP_QUICKSTART_STAGE
  package:
    name: NATIVE_APP_QUICKSTART_PACKAGE
    warehouse: NATIVE_APP_QUICKSTART_WH
    scripts:
      - app/scripts/shared_content.sql
  artifacts:
    - src: app/src/*
      dest: ./
```

This ensures that `sf_native_app_quickstart/app/scripts/shared_content.sql` will run after the `package` is created.

As a note, `package_name` will only be replaced in scripts that are listed under `native_app.package.scripts` when you execute a Snowflake CLI command.

**Option 2: Manually executing SQL** 

Run the SQL below in a SQL worksheet.

```sql
-- ################################################################
-- Create SHARED_CONTENT_SCHEMA to share in the application package
-- ################################################################
use database NATIVE_APP_QUICKSTART_PACKAGE;
create or replace schema shared_content_schema;

use schema shared_content_schema;
create or replace view MFG_SHIPPING as select * from NATIVE_APP_QUICKSTART_DB.NATIVE_APP_QUICKSTART_SCHEMA.MFG_SHIPPING;

grant usage on schema shared_content_schema to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
grant reference_usage on database NATIVE_APP_QUICKSTART_DB to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
grant select on view MFG_SHIPPING to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
```

<!-- ------------------------ -->
## Create App Package Version
Duration: 4

**Option 1: Using the Snowflake CLI (Recommended)**

Now we can create our application package, upload the application source code to the stage, share the provider shipping data via the application package, and create a version of the application package.

There is a single Snowflake CLI command that carries out all the above functionality.

```bash
snow app version create V1 -c connection_name
```
where `V1` is the name of the version we want to create and `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation. 

You can now skip to the next page.

**Option 2: Using Snowflake UI** 

We've now uploaded the application source code to our stage, created our application package, and uploaded the provider data to be shared in the application package.

From here, we will create the first version of our application package. You can have multiple versions available. 

To view our App Package in the Snowflake UI:

1. Login to your Snowflake account and navigate to `Apps`
2. In the top navigation, click `Packages`
3. Click `NATIVE_APP_QUICKSTART_PACKAGE`

Now let's add our first version using our previously uploaded code.

1. Click `Add first version`.
2. Type `V1` for the version name.
3. Select `NATIVE_APP_QUICKSTART_PACKAGE` for the database.
4. Select `NATIVE_APP_QUICKSTART_STAGE` for the stage.
5. Select `/` for the directory.
6. Create the first version.

<!-- ------------------------ -->
## Upload Consumer Supply Chain Data
Duration: 2

### Create consumer tables to hold the data

In this scenario, consumers will provider their own supply chain data (orders and site recovery data) from their own Snowflake account. The app will use the consumer's data to render graphs representing different aspects of the supply chain.

**Option 1: Using the Snowflake CLI (Recommended)**

Create a file `consumer_setup.sql` in your project directory and copy in the code snippet below.

```sql
USE WAREHOUSE NATIVE_APP_QUICKSTART_WH;

-- this database is used to store our data
USE DATABASE NATIVE_APP_QUICKSTART_DB;

USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;

-- Load app/data/order_data.csv into the table below using Snowsight

CREATE OR REPLACE TABLE MFG_ORDERS (
  order_id NUMBER(38,0), 
  material_name VARCHAR(60),
  supplier_name VARCHAR(60),
  quantity NUMBER(38,0),
  cost FLOAT,
  process_supply_day NUMBER(38,0)
);

-- Load app/data/site_recovery_data.csv using Snowsight

CREATE OR REPLACE TABLE MFG_SITE_RECOVERY (
  event_id NUMBER(38,0), 
  recovery_weeks NUMBER(38,0),
  lat FLOAT,
  lon FLOAT
);
```

Now run the Snowflake CLI command to run all commands in this file.

```bash
snow sql -f consumer_setup.sql -c connection_name
```

where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.

**Option 2: Manually executing SQL**

You can also run the SQL from the above section in a Snowflake SQL worksheet.

### Upload data into these tables  

Next, you'll load data into these newly defined tables using the Snowflake UI.

1. Login to your Snowflake account and navigate to `Data -> Databases`
2. Select `NATIVE_APP_QUICKSTART_DB` -> `NATIVE_APP_QUICKSTART_SCHEMA` -> `Tables` 
3. From there, select each table (`MFG_ORDERS`, `MFG_SITE_RECOVERY` ) and upload the corresponding `.csv` file from the cloned repository:
   1. Select `Load Data` in the top right
   2. Select `NATIVE_APP_QUICKSTART_WH` for the warehouse
   3. Click `Browse` and select the corresponding `.csv` file, Click `Next`
   4. Select `Delimited Files (CSV or TSV)` for the File Format
   5. For `Field optionally enclosed by` select `Double quotes`
   6. Click `Next`, repeat for each table. 

<!-- ------------------------ -->
## Install the Application
Duration: 3

To use the application, we'll first need to install it in the account. Normally you'd simply click an install button in the Snowflake Marketplace, but since we're building the application using a single account to demonstrate the provider and consumer experiences, you'll need to either run a Snowflake CLI command or some SQL to install the application in the account. 

**Option 1: Using the Snowflake CLI (Recommended)**

Add the following snippets under `native_app` section of the file, but do not remove any existing fields: 

```yaml
  application:
    name: NATIVE_APP_QUICKSTART_APP
    warehouse: NATIVE_APP_QUICKSTART_WH
```

After adding the above, the `snowflake.yml` file should look like:
```yaml
definition_version: 1
native_app:
  name: NATIVE_APP_QUICKSTART
  source_stage: NATIVE_APP_QUICKSTART_SCHEMA.NATIVE_APP_QUICKSTART_STAGE
  package:
    name: NATIVE_APP_QUICKSTART_PACKAGE
    warehouse: NATIVE_APP_QUICKSTART_WH
    scripts:
      - app/scripts/shared_content.sql
  application:
    name: NATIVE_APP_QUICKSTART_APP
    warehouse: NATIVE_APP_QUICKSTART_WH
  artifacts:
    - src: app/src/*
      dest: ./
```

Now run the command below.

```bash
snow app run --version V1 -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.

This command will create an application `NATIVE_APP_QUICKSTART_APP` in your account, installed from version `V1` of application package `NATIVE_APP_QUICKSTART_PACKAGE`. At the end of the command execution, it will display the URL at which the application is available in your account.

**Option 2: Manually executing SQL**

Open a SQL worksheet and run the following SQL:

```
-- ################################################################
-- INSTALL THE APP IN THE ACCOUNT
-- ################################################################

USE DATABASE NATIVE_APP_QUICKSTART_DB;
USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;
USE WAREHOUSE NATIVE_APP_QUICKSTART_WH;

-- This executes "setup.sql"; This is also what gets executed when installing the app
CREATE APPLICATION NATIVE_APP_QUICKSTART_APP FROM application package NATIVE_APP_QUICKSTART_PACKAGE using version V1 patch 0;

-- At this point you should see the app NATIVE_APP_QUICKSTART_APP listed under Apps
SHOW APPLICATIONS;
```

<!-- ------------------------ -->
## Run the Streamlit App
Duration: 1

With the application installed, you can now the app! If you are not using the Snowflake CLI and want to run the app, navigate to the `Apps` tab in Snowflake. From there, you will see your new application. Click on the app to launch it and give it a few seconds to warm up. 

When running the app for the first time, you'll be prompted to do some first-time setup by granting the app access to certain tables (i.e., create object-level bindings). The bindings link references defined in the manifest file to corresponding objects in the Snowflake account. These bindings ensure that the application can run as intended.

Upon running the application, you will see this:

![streamlit](assets/streamlit.png)


<!-- ------------------------ -->
## Drop the Application and App Package
Duration: 1

Since this is a Quickstart, we want to clean up objects that have been created in your Snowflake account.

**Option 1: Using the Snowflake CLI (Recommended)**

Run the command below to first drop the existing version `V1` in your application package `NATIVE_APP_QUICKSTART_PACKAGE`. 

```bash
snow app version drop V1 -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation. A prompt asks if you want to proceed, and you can respond with a `y`.

Then run the command below to drop both the application `NATIVE_APP_QUICKSTART_APP` and the package `NATIVE_APP_QUICKSTART_PACKAGE`.

```bash
snow app teardown -c connection_name
```

However, the tables you created in your Snowflake account will not be deleted using the commands above. In the case of this quickstart, only one database `NATIVE_APP_QUICKSTART_DB` contains both the provider and consumer tables, so dropping just this database will do the trick.
 
```bash 
snow object drop database NATIVE_APP_QUICKSTART_DB -c connection_name
snow object drop warehouse NATIVE_APP_QUICKSTART_WH -c connection_name
```

**Option 2: Manually executing SQL**

Open a SQL worksheet and run the following SQL:

```
DROP APPLICATION NATIVE_APP_QUICKSTART_APP;
DROP APPLICATION PACKAGE NATIVE_APP_QUICKSTART_PACKAGE;
DROP DATABASE NATIVE_APP_QUICKSTART_DB;
DROP WAREHOUSE NATIVE_APP_QUICKSTART_WH;
```

This will drop all the objects you created for the purpose of this Quickstart.

<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 1

Congratulations, you have now developed your first Snowflake Native Application! As next steps and to learn more, checkout additional documentation at [docs.snowflake.com](https://docs.snowflake.com) and demos of other Snowflake Native Apps at [developers.snowflake.com/demos](https://developers.snowflake.com/demos/analytics-snowflake-native-app/).

For a slightly more advanced Snowflake Native Application, see the following Quickstart: [Build a Snowflake Native App to Analyze Chairlift Sensor Data](https://quickstarts.snowflake.com/guide/native-app-chairlift/).

### Additional resources

- [Snowflake Native App Developer Toolkit](https://www.snowflake.com/snowflake-native-app-developer-toolkit/?utm_cta=na-us-en-eb-native-app-quickstart)

### What we've covered
- Prepare data to be included in your application.
- Create an application package that contains the data and business logic of your application.
- Share data with an application package.
- Add business logic to an application package.
- Test the application locally.
- View and test the application in Snowsight.
- Use Snowflake CLI to manage Native Applications

