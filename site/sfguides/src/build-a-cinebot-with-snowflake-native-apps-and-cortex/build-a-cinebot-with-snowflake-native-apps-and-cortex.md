author: Charles Yorek
id: build-a-cinebot-with-snowflake-native-apps-and-cortex
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/build, snowflake-site:taxonomy/snowflake-feature/native-apps
language: en
summary: Build a movie recommendation chatbot using Snowflake Native Apps and Snowflake Cortex AI for intelligent search and content generation.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build a CineBot with Snowflake Native Apps and Snowflake Cortex
<!-- ------------------------ -->
## Overview

The Snowflake Native App Framework is a powerful way for application providers to build, deploy and market applications via the Snowflake Marketplace.  In this example you will learn how to incorporate Snowflake's Cortex Suite into a Native App that will create a 'CineBot' that can recommend Movies. 

### Prerequisites
- A Snowflake account with ACCOUNTADMIN access
- Familiarity with Snowflake Snowsight Interface
- Ability to install and run software on your computer
- Basic experience using git

### What You’ll Learn 
- How to create an app using the Snowflake Native App framework
- How to utilize the Snowflake Cortex Suite and integrate it into a Native App
- How to test the Snowflake Native App Provider and Consumer experience within a single Snowflake account

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed
- A [Snowflake Account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)


### What You’ll Build 
- A Snowflake Native App that utilizes the Snowflake Cortex Search and Complete capabilities to create a movie recommendation service aka a 'CineBot'. You'll set up an Snowflake account to operate as a Provider and Consumer environment, load data from an S3 bucket into a table and build out the Snowflake Native App.

<!-- ------------------------ -->
## Snowflake Application Code
### Overview
In preparation for building our Snowflake Native App we need to download the code artifacts for the Native App.

### Clone or Download Github Repo
The code for the Native App is on Github. Start by cloning or downloading the repository into a separate folder. 
```shell
git clone https://github.com/Snowflake-Labs/sfguide-build-chatbot-with-snowflake-native-app-snowflake-cortex.git
```
<!-- ------------------------ -->
## Native App Provider Setup 
### Overview
To simulate a Native App provider experience we will create a role called 'nactx_role' and grant it the necessary privileges required to create an [Application Package](https://docs.snowflake.com/en/developer-guide/native-apps/creating-app-package) as well as create a database that will store our app code.  

### Create NACTX role and Grant Privileges
```sql
use role accountadmin;
create role if not exists nactx_role;
grant role nactx_role to role accountadmin;
grant create warehouse on account to role nactx_role;
grant create database on account to role nactx_role;
grant create application package on account to role nactx_role;
grant create application on account to role nactx_role with grant option;
```

### Create CORTEX_APP Database to Store Application Files 
```sql
use role nactx_role;
create database if not exists cortex_app;
create schema if not exists cortex_app.napp;
create stage if not exists cortex_app.napp.app_stage;
create warehouse if not exists wh_nap with warehouse_size='xsmall';
```
<!-- ------------------------ -->
## Native App Consumer Setup 
### Overview
To simulate the app consumer experience we will create a role called 'nac' and grant it the necessary privileges required to create Applications as well as set up a database to house the data we'll be querying with our Snowflake Native App.  

### Create NAC role and Grant Privileges
```sql
use role accountadmin;
create role if not exists nac;
grant role nac to role accountadmin;
grant create warehouse on account to role nac;
grant create database on account to role nac;
grant create application on account to role nac;
```

### Create Consumer Test Data Database and Load Data
```sql
use role nac;
create warehouse if not exists wh_nac with warehouse_size='medium';
create database if not exists movies;
create schema if not exists movies.data;
use schema movies.data;

CREATE STAGE MOVIES.DATA.MY_STAGE
URL='s3://sfquickstarts/vhol_build_2024_native_app_cortex_search/movies_metadata.csv'
DIRECTORY = (
ENABLE = true
AUTO_REFRESH = true
);

CREATE FILE FORMAT MOVIES.DATA.CSV_FILE_FORMAT
	TYPE=CSV
    SKIP_HEADER=1
    FIELD_DELIMITER=','
    TRIM_SPACE=TRUE
    FIELD_OPTIONALLY_ENCLOSED_BY='"'
    REPLACE_INVALID_CHARACTERS=TRUE
    DATE_FORMAT=AUTO
    TIME_FORMAT=AUTO
    TIMESTAMP_FORMAT=AUTO; 

CREATE TABLE movies.data.movies_metadata (
    adult BOOLEAN,
    belongs_to_collection VARCHAR,
    budget NUMBER(38, 0),
    genres VARCHAR,
    homepage VARCHAR,
    id NUMBER(38, 0),
    imdb_id VARCHAR,
    original_language VARCHAR,
    original_title VARCHAR,
    overview VARCHAR,
    popularity VARCHAR,
    poster_path VARCHAR,
    production_companies VARCHAR,
    production_countries VARCHAR,
    release_date DATE,
    revenue NUMBER(38, 0),
    runtime NUMBER(38, 1),
    spoken_languages VARCHAR,
    status VARCHAR,
    tagline VARCHAR,
    title VARCHAR,
    video BOOLEAN,
    vote_average NUMBER(38, 1),
    vote_count NUMBER(38, 0)
);

COPY INTO MOVIES.DATA.MOVIES_METADATA
FROM  @my_stage FILE_FORMAT = (FORMAT_NAME = CSV_FILE_FORMAT) ON_ERROR = CONTINUE;

create or replace table movies_raw as 
select title, budget::string as budget, overview, popularity, release_date::string as release_date, 
runtime::string as runtime 
from movies.data.movies_metadata;
```

## Create Application Package
### Overview
With all of our Snowflake Native App assets uploaded to our Snowflake account we can now create our Application Package using our Provider role.  Since we're doing this in a single Snowflake account we will also grant the Consumer role privileges to install it. 

### Create Application Package and Grant Consumer Role Privileges
```sql
use role nactx_role;
create application package cortex_app_pkg;
```

### Upload Native App Code
After creating the application package we'll need to upload the Native App code to the the **CORTEX_APP.NAPP.APP_STAGE** stage.  This can be accomplished by navigating to this stage using Snowsight - click on the 'Database' icon on the left side navigation bar, then select 'Database Explorer', and then on the **CORTEX_APP database > NAPP schema > APP_STAGE stage**.  You will need to do the following: 
1. Click on 'Select Warehouse' and choose 'WH_NAP' for the Warehouse 
2. Click on the '+ Files' button in the top right corner 
3. Browse to the location where you cloned or downloaded the Github repo and into the '/app/' folder
4. Select all 5 files (setup.sql, manifest.yml, readme.md, ui.py, environment.yaml) 
5. Click the 'Upload' button

When this is done succesfully your we're now ready to create the Application Package. 

### Alter the Application Package
```sql
alter application package cortex_app_pkg register version v1 using @cortex_app.napp.app_stage;
grant install, develop on application package cortex_app_pkg to role nac;
```

## Install & Run Application
### Overview
To simulate the app consumer experience we will create a role called 'nac' and grant it the necessary privileges required to create Applications as well as set up a database to house the data we'll be querying with our Snowflake Native App.  

### Install App as the Consumer
```sql
use role nac;
create application cortex_app_instance from application package cortex_app_pkg using version v1;
```
### Grant the Application Privileges on the Movies Table
```sql
grant all on database movies to application cortex_app_instance;
grant all on schema movies.data to application cortex_app_instance;
grant all on table movies.data.movies_raw to application cortex_app_instance;
grant usage on warehouse wh_nac to application cortex_app_instance;
```
### Grant the Application IMPORTED PRIVILEGES which allows it to use Cortex Functions
```sql
--This is a special step required to allow Native Apps to utilized Cortex Functions in a consumer database 
use role accountadmin;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO APPLICATION cortex_app_instance;
```


At this point you can navigate the the Application by clicking on **'Catalog'** on the left side of the Snowsight screen and then by clicking on **'Apps'**.  You can click on the **Cortext_App_Instance** application and it will bring up the Application. When run for the first time, it will detect that there is no "chunked" table, and will prompt you to run the pre-processing Stored Procedures we created in our setup.sql script. Once this is run, the app will refresh and you will be able to talk to the chatbot. Make sure you have the NAC role selected in the top right. If you receive an error that the selected model does not exist in your region, please select another on the left menu.


<!-- ------------------------ -->
## Cleanup 
### Overview

To clean up your environment you can run the following series of commands.
### Clean Up
```sql
--clean up consumer objects
use role NAC;
drop application cortex_app_instance cascade;
drop warehouse wh_nac;
drop database movies;

--clean up provider objects
use role nactx_role;
drop application package cortex_app_pkg;
drop database cortex_app;
drop warehouse wh_nap;

--clean up prep objects
use role accountadmin;
drop role nactx_role;
drop role nac;
```

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations!  You've now deployed a Snowflake Native App that utilizes the Snowflake Cortex Suite to enhance the capabilities that a Native App Provider can give to their consumers.

### What we've covered
In this Quickstart we covered the following: 
- How to create an app using the Snowflake Native App framework
- How to utilize the Snowflake Cortex Suite and integrate it into a Native App
- How to test the Snowflake Native App Provider and Consumer experience within a single Snowflake account

This Quickstart can provide a template for you to accomplish the basic steps of building a Snowflake Native App that includes the Snowflake Cortex Suite to deploy & monetize whatever unique code to your Snowflake consumers accounts.  

### Related Resources
- [Snowflake Native Apps](/en/data-cloud/workloads/applications/native-apps/?_fsi=vZHZai1N&_fsi=vZHZai1N&_fsi=vZHZai1N)
- [Snowflake Native Apps Documentation](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
- [Snowpark Cortex](https://docs.snowflake.com/en/guides-overview-ai-features)
