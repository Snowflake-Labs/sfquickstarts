author: Allan Mitchell
id: data_mapping_in_native_apps
summary: This guide will provide step-by-step details for building a data mapping requirement in Snowflake Native Apps and Streamlit
categories: Getting-Started, featured, data-engineering, Native-App, Streamlit
environments: web
status: draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Native App, Streamlit, Python

# Data Mapping in Snowflake Native Apps using Streamlit
<!-- ------------------------ -->
## Overview
Duration: 5

The Snowflake Native App Framework is a fantastic way for Snowflake application providers to distribute proprietary functionality to their customers, partners and to the wider Snowflake Marketplace. As a provider you can be assured that your code and data (if included) is secure and that the consumers of your application can take advantage of the functionality but not see the details of the implementation. As a consumer of an application you can be assured that the provider via the application is not able to see or operate on any data in your account unless you explicitly allow them access.

> aside negative
> 
> **Note** - As of 23/10/2023, the [Snowflake Native App Framework](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about) is in public preview in all non-government AWS regions.

### Prerequisites

* A basic understanding of Snowflake Native Applications
* An introductory level of coding in Python
* A basis knowledge of Snowflake

### What You'll Learn

* The basic building blocks of a Snowflake Native Application
* Assigning Permissions to your Snowflake Native Application
* Allowing configuration of  your Snowflake native Application through a Streamlit UI

### What You'll need

* A Snowflake account in AWS
* A Snowflake user created with ACCOUNTADMIN permissions - this is more than is strictly necessary and you can read more about the permissions required [here](https://docs.snowflake.com/en/sql-reference/sql/create-application-package#access-control-requirements)
* [SnowflakeCLI](https://github.com/Snowflake-Labs/snowcli/tree/main) installed. This is a new tool currently in Public Preview.





### The Scenario
The scenario is as follows. You are a Snowflake Native Application provider. Your application requires the consumer of the application to pass in a column in a table that contains an IP address and you will write out enhanced data for that particular IP address to another column in the same consumer defined table.

The scenario presents some challenges to me as the provider

* You need Read and Write access to a table in the consumer account
* You have no idea what the name of the IP address attribute will be
* You have no idea where the consumer will want me to write out the data

Requesting read and write access to a table in the consumer account is easy because my application can simply tell the consumer I require Read/Write access to a table and the consumer can grant access. The next two points are slightly more tricky. We have the ability within the Snowflake Native App Framework to gain access to a table which the application consumer will specify. Every consumer of the application will most likely have differently named attributes as well. In testing an application's functionality locally you know the names of the columns and life is good. Let’s see two ways in which you could solve this problem with Snowflake Native Apps.  There are others but here we want to just call out two for now.

#### Solution 1:  Make the consumer do the work

In the readme file for the application you could distribute instructions for the consumer to make sure they have a table called T that contains columns labeled C_INPUT and C_OUTPUT.  The application consumer could enable this by providing a view over the top of an existing table to the application.  Whilst this will work, we don’t necessarily want new objects to be created in Snowflake databases simply to serve the purpose of our application.

#### Solution 2: Provide an intuitive UI in the application

The application provides a user interface which allows the consumer of the application to map columns in an existing table/view to the requirements of the application. This is much more user friendly and doesn’t require new objects to be created in a Snowflake database.

The first solution is not really what we want to be doing because the consumer will potentially have to create objects on their Snowflake instance just to satisfy the application's requirements, so this Quickstart will deliver the second solution.

**Note**

- This Quickstart is limited to a single-account installation. You'll use a single Snowflake account to experience the app from the provider's perspective and from the consumer's perspective. Listing to the Snowflake Marketplace and versions / release directives are outside of the scope of this guide.

<!-- ------------------------ -->
## Building the Application
Duration: 10

The application itself is a simple one and has been broken down into three parts.

* The building of the application package on the provider and the sharing of the lookup database with the application. 
* The building of the application install script which contains the functionality to accept an IP address, look it up in the database we just shared with the application and write back enhanced data from the application. 
* Arguably (certainly for this Quickstart) the most important part which is the user interface written using Streamlit. This is where we will do the mappings.

To do the enhancement of the IP addresses we will use a dataset called DB11 from [IP2LOCATION](https://www.ip2location.com/database/ip2location). There is a free version of this database available [here](https://lite.ip2location.com/database/db11-ip-country-region-city-latitude-longitude-zipcode-timezone), which is the one we will use in this quickstart.  If you do not have an account with them already you will need to create one. Download the dataset as a CSV file so it is ready to import  into the provider account.

### Create provider table to hold the data
There are a few different ways to set up the database in your provider account.

**Option 1: Using the Snowflake CLI (Recommended)**

First, we need to set up a dedicated directory in your filesystem for the application we want to build. 

```bash
snow app init streamlit_data_mapping
```

This command requires the use of git. It will create a directory structure in your filesystem for our Snowflake Native Application from a preset [template](https://github.com/snowflakedb/native-apps-templates/tree/main/basic).

At the root of `streamlit_data_mapping`, create a file called `lookup_database_setup.sql` and copy in the code snippet below.
```sql
CREATE DATABASE IP2LOCATION;
CREATE SCHEMA IP2LOCATION;

CREATE TABLE LITEDB11 (
ip_from INT,
ip_to INT,
country_code char(2),
country_name varchar(64),
region_name varchar(128),
city_name varchar(128),
latitude DOUBLE,
longitude DOUBLE,
zip_code varchar(30),
time_zone varchar(8)
);
--Create a file format for the file
CREATE OR REPLACE FILE FORMAT LOCATION_CSV
SKIP_HEADER = 1
FIELD_OPTIONALLY_ENCLOSED_BY = '"'
COMPRESSION = AUTO;
--create a stage so we can upload the file
CREATE STAGE LOCATION_DATA_STAGE
file_format = LOCATION_CSV;
```

Now execute the Snowflake CLI command to run all the SQL statements in this file.
```bash
cd streamlit_data_mapping
snow sql -f lookup_database_setup.sql -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.

**Option 2: Using Snowsight**

Head over to Snowsight on the provider account and open a new worksheet.

The first thing you need to do is create a new database which will serve as the lookup database for the application

```sql
CREATE DATABASE IP2LOCATION;
CREATE SCHEMA IP2LOCATION;

CREATE TABLE LITEDB11 (
ip_from INT,
ip_to INT,
country_code char(2),
country_name varchar(64),
region_name varchar(128),
city_name varchar(128),
latitude DOUBLE,
longitude DOUBLE,
zip_code varchar(30),
time_zone varchar(8)
);
--Create a file format for the file
CREATE OR REPLACE FILE FORMAT LOCATION_CSV
SKIP_HEADER = 1
FIELD_OPTIONALLY_ENCLOSED_BY = '"'
COMPRESSION = AUTO;
--create a stage so we can upload the file
CREATE STAGE LOCATION_DATA_STAGE
file_format = LOCATION_CSV;
```

After completing either Option 1 or Option 2, your database should look like the following:

<img src="assets/producer_org.png" width="425" />


### Upload data into the table
You now need to upload the file you just downloaded from IP2Location to the stage you just created in Snowflake.  There are a couple of ways to do this:


**Option 1: Using the Snowflake CLI (Recommended)**
Run the following command, replacing `path_to_csv_file` with the path to the CSV file on your filesystem.
```bash
snow object stage copy path_to_csv_file @IP2LOCATION/IP2LOCATION/LOCATION_DATA_STAGE -c connection_name
```
This will upload the CSV file to the stage `@IP2LOCATION/IP2LOCATION/LOCATION_DATA_STAGE`.

After the step above, the file needs to be used to populate the table `IP2LOCATION.IP2LOCATION.LITEDB11` that was just created. 
```bash
snow sql -q 'copy into IP2LOCATION.IP2LOCATION.LITEDB11 from @IP2LOCATION/IP2LOCATION/LOCATION_DATA_STAGE' -c connection_name
```

With the data loaded, you can run some test queries to get a feel for the data, such as 
```bash
snow sql -q 'SELECT COUNT(*) FROM IP2LOCATION.IP2LOCATION.LITEDB11' -c connection_name
-- OR --
snow sql -q 'SELECT * FROM IP2LOCATION.IP2LOCATION.LITEDB11 LIMIT 10' -c connection_name
```
We now have the reference database setup in the provider account so are now ready to start building the application itself.

You can skip to the next page if you chose Option 1.

**Option 2: Using Snowsight**

Using Snowsight, come out of Worksheets and go to **data/databases** and then navigate to the stage we just created.  You should see a screen similar to the below

<img src="assets/location_data_upload.png" width="800" />

Go ahead now and upload the file to the stage.  After the file is uploaded go back to your worksheet and copy the file into the table created earlier

```sql
--Copy the file into the table we just created
COPY INTO LITEDB11 FROM @LOCATION_DATA_STAGE;
```

With the data loaded you can run some test queries to get a feel for the data

```sql
SELECT COUNT(*) FROM LITEDB11;
SELECT * FROM LITEDB11 LIMIT 10;
```
We now have the reference database setup in the provider account so are now ready to start building the application itself.

<!-- ------------------------ -->
## Provider Setup
Duration: 5

As part of the setup in the provider account, we want to set up our application package with permissions onto the lookup database. We also explore different ways of creating an application package.

**Option 1: Using the Snowflake CLI (Recommended)**

There is a file called `snowflake.yml` in the root of `streamlit_data_mapping`. Edit the contents of this file so that they match the snippet below:  
```yaml
definition_version: 1
native_app:
  name: STREAMLIT_DATA_MAPPING
  source_stage: IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE
  package:
    name: IP2LOCATION_APP_PKG
    scripts:
      - app/scripts/shared_content.sql
  artifacts:
    - src: app/src/*
      dest: ./
```

Add the SQL below in a new file at `streamlit_data_mapping/app/scripts/shared_content.sql`.
```sql
USE DATABASE {{package_name}};
--create a schema
CREATE SCHEMA IP2LOCATION;
--Grant the application permissions on the schema we just created
GRANT USAGE ON SCHEMA IP2LOCATION TO SHARE IN APPLICATION PACKAGE {{package_name}}; 
--grant permissions on the database where our data resides
GRANT REFERENCE_USAGE ON DATABASE IP2LOCATION TO SHARE IN APPLICATION PACKAGE {{package_name}};
--we need to create a proxy artefact here referencing the data we want to use
CREATE VIEW IP2LOCATION.LITEDB11
AS
SELECT * FROM IP2LOCATION.IP2LOCATION.LITEDB11;
--grant permissions to the application
GRANT SELECT ON VIEW IP2LOCATION.LITEDB11 TO SHARE IN APPLICATION PACKAGE {{package_name}};
```
Here, `package_name` is a pre-defined variable that will be replaced by the name of your `package` from the `snowflake.yml` file when you execute a Snowflake CLI command.

As a note, the `package` or any other objects do not exist at the end of these edits. There is a separate command later that will create these objects for you. If you followed this section, you can skip to the next page.

**Option 2: Using Snowsight**

We are now ready to go ahead and build out our application package.  In the worksheet execute the following

```sql
--create the application package
CREATE APPLICATION PACKAGE IP2LOCATION_APP_PKG;
--set context to the application package
USE IP2LOCATION_APP_PKG;
--create a schema
CREATE SCHEMA IP2LOCATION_APP_PKG_SCHEMA;
--create a stage
CREATE STAGE APPLICATION_STAGE;
--create a schema
CREATE SCHEMA IP2LOCATION;
--Grant the application permissions on the schema we just created
GRANT USAGE ON SCHEMA IP2LOCATION TO SHARE IN APPLICATION PACKAGE IP2LOCATION_APP_PKG; 
--grant permissions on the database where our data resides
GRANT REFERENCE_USAGE ON DATABASE IP2LOCATION TO SHARE IN APPLICATION PACKAGE IP2LOCATION_APP_PKG;
--we need to create a proxy artefact here referencing the data we want to use
CREATE VIEW IP2LOCATION.LITEDB11
AS
SELECT * FROM IP2LOCATION.IP2LOCATION.LITEDB11;
--grant permissions to the application
GRANT SELECT ON VIEW IP2LOCATION.LITEDB11 TO SHARE IN APPLICATION PACKAGE IP2LOCATION_APP_PKG;
```

That's the first part of the application completed but we will be revisiting this worksheet towards the end of the exercise as we need to add a version and patch to the application.

<!-- ------------------------ -->
## The Manifest File
Duration: 3

Every Snowflake Native App is required to have a manifest file.  The manifest file defines any properties of the application as well as the location of the application's setup script.  The manifest file for this application will not use all the possible fetures of the manifest file so you can read more about it [here](https://docs.snowflake.com/en/developer-guide/native-apps/creating-manifest).  The manifest file has three requirements:

* The name of the manifest file must be manifest.yml.
* The manifest file must be uploaded to a named stage so that it is accessible when creating an application package or Snowflake Native App.
* The manifest file must exist at the root of the directory structure on the named stage.

The named stage in this example is the stage with the label **APPLICATION_STAGE** created earlier.  The manifest file looks like this

```yaml
manifest_version: 1
artifacts:
  setup_script: setup_script.sql
  default_streamlit: ui."Dashboard"

references:
  - tabletouse:
      label: "Table that contains data to be keyed"
      description: "Table that has IP address column and a column to write into"
      privileges:
        - SELECT
        - INSERT
        - UPDATE
        - REFERENCES
      object_type: TABLE
      multi_valued: false
      register_callback: config_code.register_single_callback
```

The **artifacts** section details what files will be included in the application and their location relative to the manifest file.  The **references** section is where we define the permissions we require within the consumer account.  This is what we will ask the consumer to grant.  The way it does that is by calling the **register_callback** procedure which we will shortly define in our setup script.

<!-- ------------------------ -->
## The Setup Script
Duration: 10

In a Snowflake Native App, the setup script is used to define what objects will be created when the application is installed on the consumer account.  The location of the file as we have seen is defined in the manifest file.  The setup script is run on initial installation of the application and any subsequent upgrades/patches.

Most setup scripts are called either **setup.sql** or **setup_script.sql** but that is not a hard and fast requirement.  In the setup script you will see that for some objects, the application role is given permissions and some not.  
If the application role is permissioned onto an object then the object will be visible in Snowsight after the application is installed (permissions allowing).
If the application role is not granted permissions onto an object then you will not see the object in Snowsight.  The application itself can still use the objects regardless.

```sql
--create an application role which the consumer can inherit
CREATE APPLICATION ROLE APP_PUBLIC;

--create a schema
CREATE OR ALTER VERSIONED SCHEMA ENRICHIP;
--grant permissions onto the schema to the application role
GRANT USAGE ON SCHEMA ENRICHIP TO APPLICATION ROLE APP_PUBLIC;

--this is an application version of the object shared with the application package
CREATE VIEW ENRICHIP.LITEDB11 AS SELECT * FROM IP2LOCATION.litedb11;

--accepts an IP address and returns a modified version of the IP address 
--the modified version will be used in the lookup
CREATE OR REPLACE SECURE FUNCTION ENRICHIP.ip2long(ip_address varchar(16))
RETURNS string
LANGUAGE JAVASCRIPT
AS
$$
var result = "";
var parts = [];
if (IP_ADDRESS.match(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/)) {
parts = IP_ADDRESS.split('.');
result = (parts[0] * 16777216 +
(parts[1] * 65536) +
(parts[2] * 256) +
(parts[3] * 1));
}
return result;
$$
;

--this function accepts an ip address and 
--converts it using the ip2long function above
--looks up the returned value in the view
--returns the enhanced information as an object
CREATE OR REPLACE SECURE FUNCTION ENRICHIP.ip2data(ip_address varchar(16))
returns object
as
$$
select object_construct('country_code', MAX(COUNTRY_CODE), 'country_name', MAX(COUNTRY_NAME),
'region_name', MAX(REGION_NAME), 'city_name', MAX(CITY_NAME),
'latitude', MAX(LATITUDE), 'longitude', MAX(LONGITUDE),
'zip_code', MAX(ZIP_CODE), 'time_zome', MAX(TIME_ZONE))
from ENRICHIP.LITEDB11 where ip_from <= ENRICHIP.ip2long(ip_address)::int AND ip_to >= ENRICHIP.ip2long(ip_address)::int
$$
;

--create a schema for our callback procedure mentioned in the manifest file
create schema config_code;
--grant the application role permissions onto the schema
grant usage on schema config_code to application role app_public;

--this is the permissions callback we saw in the manifest.yml file
create procedure config_code.register_single_callback(ref_name string, operation string, ref_or_alias string)
    returns string
    language sql
    as $$
        begin
            case (operation)
                when 'ADD' then
                    select system$set_reference(:ref_name, :ref_or_alias);
                when 'REMOVE' then
                    select system$remove_reference(:ref_name);
                when 'CLEAR' then
                    select system$remove_reference(:ref_name);
                else
                    return 'Unknown operation: ' || operation;
            end case;
            system$log('debug', 'register_single_callback: ' || operation || ' succeeded');
            return 'Operation ' || operation || ' succeeded';
        end;
    $$;

--grant the application role permissions to the procedure
grant usage on procedure config_code.register_single_callback(string, string, string) to application role app_public;

--create a schema for the UI (streamlit)
create schema ui;
--grant the application role permissions onto the schema
grant usage on schema ui to application role app_public;

--this is our streamlit.  The application will be looking for 
--file = enricher_dash.py in a folder called ui

--this is the reference to the streamlit (not the streamlit itself)
--this was referenced in the manifest file
create or replace streamlit ui."Dashboard" from 'ui' main_file='enricher_dash.py';

--grant the application role permissions onto the streamlit
grant usage on streamlit ui."Dashboard" TO APPLICATION ROLE APP_PUBLIC;

--this is where the consumer data is read and the enhanced information is written
CREATE OR REPLACE PROCEDURE ENRICHIP.enrich_ip_data(inp_field varchar, out_field varchar)
RETURNS number
AS
$$
    DECLARE 
        q VARCHAR DEFAULT 'UPDATE REFERENCE(''tabletouse'') SET ' || out_field || ' = ENRICHIP.ip2data(' || inp_field || ')';
        result INTEGER DEFAULT 0;
    BEGIN
        EXECUTE IMMEDIATE q;
        RETURN RESULT;
    END;
$$; 

```

> aside positive
> 
> **Note** - In the setup script we defined a stored procedure labeled **ENRICHIP.enrich_ip_data**.  In the body we make calls to **REFERENCE(tabletouse)**.  This reference was defined in the manifest file and it is the table to which the consumer has granted us permissions.  Because, as the application prodcuer, we have no way of knowing that ahead of time, the Snowflake Native App framework adds this facility and will resolve the references once permissions have been granted.

<!-- ------------------------ -->
## Creating the Streamlit
Duration: 5

We now come to arguably the most important part of the application for us which is the user interface.  We have defined all the objects we need to create and also the permissions we will require from the consumer of the application.

A little recap on what this UI needs to achieve:

* Map a field in a table to an ip column
* Map a field in a the same table to receive the enhaced output

Once we have the streamlit UI built we can then finish off the build of the application package.

### Building the User Interface

The code for the streamlit looks like this.  There will be other ways of doing this, but this is one way.

```python
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# get the active session
session = get_active_session()
# define the things that need mapping
lstMappingItems =  ["IP ADDRESS COLUMN", "RESULT COLUMN"]
# from our consumer table return a list of all the columns
option_source = session.sql("SELECT * FROM REFERENCE('tabletouse') WHERE 1=0").to_pandas().columns.values.tolist()
# create a dictionary to hold the mappings
to_be_mapped= dict()
#create a form to do the mapping visualisation
with st.form("mapping_form"):
    header = st.columns([1])
    #give it a title
    header[0].subheader('Define Mappings')
    # for each mapping requirement add a selectbox
    # populate the choices with the column list from the consumer table
    for i in range(len(lstMappingItems)):
        row = st.columns([1])
        selected_col = row[0].selectbox(label = f'Choose Mapping for {lstMappingItems[i]}',options = option_source)
        # add the mappings to the dictionary
        to_be_mapped[lstMappingItems[i]] = selected_col
        
    row = st.columns(2)
    # submit the mappings
    submit = row[1].form_submit_button('Update Mappings')

# not necessary but useful to see what the mappings look like
st.json(to_be_mapped)

#function call the stored procedure in the application that does the reading and writing
def update_table():
    # build the statement
    statement = ' CALL ENRICHIP.enrich_ip_data(\'' + to_be_mapped["IP ADDRESS COLUMN"] + '\',\'' +  to_be_mapped["RESULT COLUMN"] + '\')'
    #execute the statement
    session.sql(statement).collect()
    #again not necessary but useful for debugging (would the statement work in a worksheet)
    st.write(statement)
#update the consumer table
st.button('UPDATE!', on_click=update_table)
```

### Finishing the Application

All the pieces are in place for our application so we now need to go back to the provider account and upload the files we have just created (manifest.yml, setup_script.sql and enricher_dash.py) to the stage **APPLICATION_STAGE**.  


> aside positive
> 
> **Note** Remember our application manifest is expecting the file enricher_dash.py to be in a folder called **ui**

**Option 1: Using the Snowflake CLI (Recommended)**

In order to upload the files, let's make sure that they exist as the following structure under `app/`:
```plaintext
|-- streamlit_data_mapping
    |-- ...
    |-- app
        |-- src
        |   |-- manifest.yml
        |   |-- setup_script.sql
        |   |-- ui
        |   |   |-- enricher_dash.py
        |-- scripts
        |   |-- shared_content.sql
```

Your `snowflake.yml` has a snippet 
```yaml
  artifacts:
    - src: app/src/*
      dest: ./
```
This means that all code files under `streamlit_data_mapping/app/src` will be uploaded to `IP2LOCATION_APP_PKG.IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE` when you execute the relevant command, more of that in a later section:

1. `streamlit_data_mapping/app/src/manifest.yml` will be uploaded at `@IP2LOCATION_APP_PKG.IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE/manifest.yml`.
2. `streamlit_data_mapping/app/src/setup_script.sql` will be uploaded at `@IP2LOCATION_APP_PKG.IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE/setup_script.sql`.
3. `streamlit_data_mapping/app/src/ui/*` will be uploaded at `@IP2LOCATION_APP_PKG.IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE/ui/*`.

Now we can create our application package, upload the application source code to the stage, share the provider `IP2LOCATION` data via the application package, and create a version of the application package.

There is a single Snowflake CLI command that carries out all the above functionality.

```bash
snow app version create MyFirstVersion -c connection_name
```
where `V1` is the name of the version we want to create and `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation. 

You can now skip to the next page.

**Option 2: Using Snowsight**

You can manually upload each of the files mentioned at the top of the page to the `APPLICATION_STAGE`.

Once uploaded, the stage should look like the following

<img src="assets/code_complete.png" width="395" />

Once the files are uploaded, go into your worksheets and finish off the building of the application package:

```sql
ALTER APPLICATION PACKAGE IP2LOCATION_APP_PKG
  ADD VERSION MyFirstVersion
  USING '@IP2LOCATION_APP_PKG.IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE';
```

Our application package is built, now let's create an application.

<!-- ------------------------ -->
## Creating and Deploying the Application
Duration: 2

There are a few ways we could deploy our application:

* Same account / Different account
* Same Org / Different Org
* Debug Mode / non-debug mode

In this instance we are going to deploy the application locally so we can see what it looks like wthout having to have another account.  This will be in non-debug mode.

**Option 1: Using the Snowflake CLI (Recommended)**

Edit the contents of the `snowflake.yml` file so that they match the snippet below:  
```yaml
definition_version: 1
native_app:
  name: STREAMLIT_DATA_MAPPING
  source_stage: IP2LOCATION_APP_PKG_SCHEMA.APPLICATION_STAGE
  package:
    name: IP2LOCATION_APP_PKG
    scripts:
      - app/scripts/shared_content.sql
  artifacts:
    - src: app/src/*
      dest: ./
  application:
    name: IP2LOCATION_APP
    debug: False
```

Now run the command below.

```bash
snow app run --version MyFirstVersion -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.

This command will create an application `IP2LOCATION_APP` in your account, installed from version `MyFirstVersion` of application package `IP2LOCATION_APP_PKG`. At the end of the command execution, it will display the URL at which the application is available in your account.

**Option 2: Using Snowsight**

```sql
CREATE APPLICATION IP2LOCATION_APP
FROM APPLICATION PACKAGE IP2LOCATION_APP_PKG
USING VERSION MyFirstVersion;
```

The application is now built.  

### Testing

Because we have installed the application locally we need to create a table to test with, before we can look at the application itself.  Let's do that now.  In your worksheet execute the following

**Option 1: Using the Snowflake CLI (Recommended)**

At the root of `streamlit_data_mapping`, create a file called `consumer_test.sql` and copy in the code snippet below.
```sql
CREATE DATABASE TEST_IPLOCATION;
CREATE SCHEMA TEST_IPLOCATION;

CREATE OR REPLACE TABLE TEST_IPLOCATION.TEST_IPLOCATION.TEST_DATA (
	IP VARCHAR(16),
	IP_DATA VARIANT
);

INSERT INTO TEST_DATA(IP) VALUES('73.153.199.206'),('8.8.8.8');
```

Now execute the Snowflake CLI command to run all the SQL statements in this file.
```bash
snow sql -f consumer_test.sql -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation.

**Option 2: Using Snowsight**
```sql
CREATE DATABASE TEST_IPLOCATION;
CREATE SCHEMA TEST_IPLOCATION;

CREATE OR REPLACE TABLE TEST_IPLOCATION.TEST_IPLOCATION.TEST_DATA (
	IP VARCHAR(16),
	IP_DATA VARIANT
);

INSERT INTO TEST_DATA(IP) VALUES('73.153.199.206'),('8.8.8.8');
```

### Viewing the Application

Come out of worksheets and head over to the Apps menu in Snowsight:

<img src="assets/find_apps.png" width="233" />

click on that and you should see the following:

<img src="assets/deployed_app.png" width="1555" />

The application if you remember needs permissions onto a table in the consumer account (the one we just created.).  We have now switched roles to being the consumer.  We are finished with being the application provider.  Over on the right hand side hit the ellipses and select **View Details**:

<img src="assets/perms.png" width="288" />

This will take you through to a page which will allow you to specify the table that you want the application to work with.  This dialog is a result of the **REFERENCE** section in the manifest file.

<img src="assets/assign_perms.png" width="901" />

Click **Add** and navigate to the table we just created and select it:

> aside positive
> 
> **Note** You may at this point be asked to specify a warehouse.   Assigning permissions requires a warehouse.

<img src="assets/table_chosen.png" width="719" />

Once we click **Done** and **Save** then the application has been assigned the needed permissions.  Now go back to apps and click on the app itself.  It should open to a screen like the following:

<img src="assets/app_entry.png" width="975" />

You should recognise the layout from building the streamlit earlier.  If you drop down either of the two boxes you will see that they are populated with the columns from the table the application has been assigned permissions to.  If we populate the mappings correctly, hit **Update Mappings** then you will see the piece of JSON underneath change to tell us the currently set mappings.  The ones we want for this application are:

<img src="assets/correct_mappings.png" width="703" />

Hit the **Update Mappings** button and then the **UPDATE!** button.  At the top of the screen you will see the SQL that you just executed on your data.

<img src="assets/statement.png" width="336" />

Now go back to your worksheet to confirm that enhanced data has been written to your database table.

```sql
USE DATABASE TEST_IPLOCATION;
USE SCHEMA TEST_IPLOCATION;
SELECT * FROM TEST_DATA;
```
<img src="assets/complete.png" width="1243" />

<!-- ------------------------ -->
## Teardown
Duration: 1

**Option 1: Using the Snowflake CLI (Recommended)**

Run the command below to first drop the existing version `MyFirstVersion` in your application package `IP2LOCATION_APP_PKG` while still in `streamlit_data_mapping` directory. 

```bash
snow app version drop MyFirstVersion -c connection_name
```
where `connection_name` is the name of the connection you specified in your `config.toml` file during Snowflake CLI installation. A prompt asks if you want to proceed, and you can respond with a `y`.

Then run the command below to drop both the application `IP2LOCATION_APP` and the package `IP2LOCATION_APP_PKG`.

```bash
snow app teardown -c connection_name
```

However, other objects you created in your Snowflake account will not be deleted using the commands above. You need to explicitly drop them.

```bash 
snow object drop database IP2LOCATION -c connection_name
snow object drop database TEST_IPLOCATION -c connection_name
```

**Option 2: Using Snowsight**

Once you have finished with the application and want to clean up your environment you can execute the following script

```sql
DROP APPLICATION IP2LOCATION_APP;
DROP APPLICATION PACKAGE IP2LOCATION_APP_PKG;
DROP DATABASE IP2LOCATION;
DROP DATABASE TEST_IPLOCATION;
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

We have covered a lot of ground in this Quickstart.  We have covered the building blocks of almost every Snowflake Native App you will ever build.  Sure some will be more complicated but the way you structure them will be very similar to what you have covered here.

### What we learned

* Creating an Application Package
* Defining and understand the role of the manifest file
* Creating the Setup script
* Understanding how References work within an application
* How to deploy an application locally
* How to assign permissions to the application
* creating a user interface for an application using Streamlit

### Further Reading

* [Tutorial: Developing an Application with the Native Apps Framework](https://docs.snowflake.com/en/developer-guide/native-apps/tutorials/getting-started-tutorial)
* [Getting Started with Snowflake Native Apps](https://quickstarts.snowflake.com/guide/getting_started_with_native_apps/#0)
* [Build a Snowflake Native App to Analyze Chairlift Sensor Data](https://quickstarts.snowflake.com/guide/native-app-chairlift/#0)
* [About the Snowflake Native App Framework](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
