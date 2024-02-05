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

Note that this Quickstart is limited to a single-account installation. You'll use a single Snowflake account to experience the app from the provider's perspective and from the consumer's perspective. Listing to the Snowflake Marketplace and versions / release directives are outside of the scope of this guide.

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

To create our Snowflake Native Application, we will first clone the [starter project](https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps) by running this command:

```bash
git clone https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps.git
```

If you do not have git installed, you can also download the code directly from [GitHub](https://github.com/Snowflake-Labs/sfguide-getting-started-with-native-apps/archive/refs/heads/main.zip) and extract it to a local folder.

This repository contains all of our starter code for our native app. Throughout the rest of this tutorial we will be modifying various parts of the code to add functionality and drive a better understanding of what is happening at each step in the process.


Let's explore the directory structure:

```plaintext
|-- repos
    |-- .gitignore
    |-- LICENSE
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

Now that we've modified our project files locally, lets create the Snowflake Application Package so we can upload our project:

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

Now, let's create a database that we will use to store provider's shipping data. This is the data that we will share with the application so that the consumer can enrich their own supply chain data with it when they install the app in their account.

Start by running the SQL below in a Snowflake SQL worksheet. It creates the database, warehouse, schema, and defines the table that will hold the shipping data.

```
CREATE OR REPLACE WAREHOUSE NATIVE_APP_QUICKSTART_WH WAREHOUSE_SIZE=SMALL INITIALLY_SUSPENDED=TRUE;

-- this database is used to store our data
CREATE OR REPLACE DATABASE NATIVE_APP_QUICKSTART_DB;
USE DATABASE NATIVE_APP_QUICKSTART_DB;

CREATE OR REPLACE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;
USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;

CREATE OR REPLACE TABLE MFG_SHIPPING (
  order_id NUMBER(38,0), 
  ship_order_id NUMBER(38,0),
  status VARCHAR(60),
  lat FLOAT,
  lon FLOAT,
  duration NUMBER(38,0)
);
```

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

Run the SQL below in a SQL worksheet. Here's what the SQL does:

- Creates a schema in the application package that will be used for sharing the shipping data

- Create a view within that schema

- Grants usage on the schema to the application package

- Grants reference usage on the database holding the provider shipping data to the application package

- Grants SELECT privileges on the view to the application package, meaning the app will be able to SELECT on the view once it is installed

```sql
-- ################################################################
-- Create SHARED_CONTENT_SCHEMA to share in the application package
-- ################################################################
use database NATIVE_APP_QUICKSTART_PACKAGE;
create schema shared_content_schema;

use schema shared_content_schema;
create or replace view MFG_SHIPPING as select * from NATIVE_APP_QUICKSTART_DB.NATIVE_APP_QUICKSTART_SCHEMA.MFG_SHIPPING;

grant usage on schema shared_content_schema to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
grant reference_usage on database NATIVE_APP_QUICKSTART_DB to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
grant select on view MFG_SHIPPING to share in application package NATIVE_APP_QUICKSTART_PACKAGE;
```

This flow ensures that the data is able to be shared securely with the consumer through the application. The objects containing the provider's proprietary shipping data are **never** shared directly with the consumer via a Snowflake Native Application. This means the provider's proprietary data remains safe, secure, and in the provider's Snowflake account. Instead, the application package has reference usage on objects (databases) corresponding to the provider's data, and when a consumer install the app (i.e., instantiates the application package), they are able to use the shared data through the application.

<!-- ------------------------ -->
## Create App Package Version
Duration: 4

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

In this scenario, consumers will provider their own supply chain data (orders and site recovery data) from their own Snowflake account. The app will use the consumer's data to render graphs representing different aspects of the supply chain.

Run the SQL below in a worksheet. We'll use the `NATIVE_APP_QUICKSTART_DB` to store the consumer supply chain data.

```
USE WAREHOUSE NATIVE_APP_QUICKSTART_WH;

-- this database is used to store our data
USE DATABASE NATIVE_APP_QUICKSTART_DB;

USE SCHEMA NATIVE_APP_QUICKSTART_SCHEMA;

CREATE OR REPLACE TABLE MFG_ORDERS (
  order_id NUMBER(38,0), 
  material_name VARCHAR(60),
  supplier_name VARCHAR(60),
  quantity NUMBER(38,0),
  cost FLOAT,
  process_supply_day NUMBER(38,0)
);

-- Load app/data/orders_data.csv using Snowsight

CREATE OR REPLACE TABLE MFG_SITE_RECOVERY (
  event_id NUMBER(38,0), 
  recovery_weeks NUMBER(38,0),
  lat FLOAT,
  lon FLOAT
);

-- Load app/data/site_recovery_data.csv using Snowsight
```

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

To use the application, we'll first need to install it in the account. Normally you'd simply click an install button in the Snowflake Marketplace, but since we're building the application and using a single account to demonstrate the provider and consumer experiences, you'll need to run the following SQL to install the application in the account. 

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

With the application installed, you can now run the app! To run the app, navigate to the `Apps` tab in Snowflake. From there, you will see your new application. Click on the app to launch it and give it a few seconds to warm up. 

When running the app for the first time, you'll be prompted to do some first-time setup by granting the app access to certain tables (i.e., create object-level bindings). The bindings link references defined in the manifest file to corresponding objects in the Snowflake account. These bindings ensure that the application can run as intended.

Upon running the application, you will see this:

![streamlit](assets/streamlit.png)



<!-- ------------------------ -->
## Conclusion & Next Steps
Duration: 1

Congratulations, you have now developed your first Snowflake Native Application! As next steps and to learn more, checkout additional documentation at [docs.snowflake.com](https://docs.snowflake.com) and demos of other Snowflake Native Apps at [developers.snowflake.com/demos](https://developers.snowflake.com/demos/analytics-snowflake-native-app/).

For a slightly more advanced Snowflake Native Application, see the following Quickstart: [Build a Snowflake Native App to Analyze Chairlift Sensor Data](https://quickstarts.snowflake.com/guide/native-app-chairlift/).

### What we've covered
- Prepare data to be included in your application.
- Create an application package that contains the data and business logic of your application.
- Share data with an application package.
- Add business logic to an application package.
- Test the application locally.
- View and test the application in Snowsight.

