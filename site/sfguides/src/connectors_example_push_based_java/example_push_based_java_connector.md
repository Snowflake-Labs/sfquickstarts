author: Piotr Hachaj
id: connectors_example_push_based_java
summary: Overview of building Snowflake push based connectors using Java and Native Apps.
categories: connectors,solution-examples,partner-integrations
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Connectors, Native Apps

# Snowflake example push based Java connector

## Overview
Duration: 1

In this tutorial you will learn how to build native Snowflake push based connectors.
In the next steps we will cover what constitutes a connector, how to build and deploy it and how to build
application UI using Streamlit.

## Prerequisites
Duration: 1

- Basic knowledge of Snowflake Native Apps
- Basic knowledge of Java
- Snowflake user with `accountadmin` role

## You will learn
Duration: 1

- Creating Native Applications in Snowflake
- Ingesting data to Snowflake using snowflake-ingestion-sdk
- Running Snowflake procedures using snowflake-jdbc
- How to optimize merge for the CDC scenario using [deferred merge approach](img/75ce96e228ff90d2.pdf)
![](assets/deferred_merge.pdf)

## Prepare your local environment
Duration: 5

- Install Java 11 or later
- Install [snowsql](https://docs.snowflake.com/en/user-guide/snowsql)
- Configure snowsql to allow using [variables](https://docs.snowflake.com/en/user-guide/snowsql-use#enabling-variable-substitution) (`variable_substitution = True`)
- Configure snowsql to [exit on first error](https://docs.snowflake.com/en/user-guide/snowsql-config#exit-on-error) (`exit_on_error = True`)
- Clone example-push-based-java-connector repository

## Connector overview
Duration: 4


This connector consist of Java Agent and Native Application.
Java Agent acts as an application which is close to a data source, it fetches data from the data source and pushes the data to Snowflake.

![overview.svg](assets/overview.svg)

### Native Application
- runs natively in Snowflake
- contains a stored procedure which initialises resources by creating all objects in database needed for deferred merge
- contains Streamlit UI which visualises data
- contains the following database elements:
  - schemas:
    - `PUBLIC` - versioned, used to store all public procedures
    - `TASKS` - stateful, used for tasks
  - procedures:
    - `INIT_DESTINATION_DATABASE` - procedure which is used to create destination database for resources
    - `INIT_RESOURCE` - procedure which initialises resource, it creates the following elements in destination database:
      - base table
      - delta table
      - view which contains merged data from base and delta tables
      - task which periodically merges data from delta to base table
  - destination database - database for all resource data, it is created outside the Native Application by `INIT_DESTINATION_DATABASE` procedure

### Java Agent
- simple Java application
- connects to the Native Application
- runs `INIT_DESTINATION_DATABASE` procedure on startup
- initialises new resources using Native Application's procedure `INIT_RESOURCE`
  - uses snowflake-jdbc library for calling stored procedure
- ingests data to snowflake
  - uses snowflake-ingest-sdk library for ingesting data
- contains CLI for enabling new resources

## Project structure
Duration: 3

### Native Application module
Contains files which are needed to create native application in snowflake
- `manifest.yml` - Manifest file required by the native apps model.
- `setup.sql` - This script includes definition of all components that constitutes the connector including procedures, schemas and tables.
- `streamlit_app.py` - File which contains the UI of the connector.
- `deploy.sql` - Script which uploads `manifest.yml`, `setup.sql` and `streamlit_app.py` to snowflake.
- `install.sql` - Script which creates native application from the files uploaded by `deploy.sql` script.

### Java Agent module
Contains java files that constitute the Agent application and gradle files that are needed to build the application.


## Connector configuration
Duration: 6

### Snowsql configuration
This quickstart uses some convenience scripts for running necessary commands. Those scripts use snowsql. Before
proceeding further you need to configure snowsql connection to your environment according to [documentation](https://docs.snowflake.com/en/user-guide/snowsql-start#using-named-connections).


### Generating Pubic and Private Keys
Java Agent uses snowflake-ingestion-sdk library which uses [key pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth).
In order to set up the connection you need to generate Public and Private Keys. To achieve it, run the following commands:
```sh
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```
The commands will create 2 files with public key (`rsa_key.pub`) and private key (`rsa_key.p8`). The keys will be used in next steps.

### Configure user in snowflake
Configure public key for your user by running the following sql command in Snowflake worksheet. Use the public key generated in previous step.
```sql
ALTER USER <your_user> SET RSA_PUBLIC_KEY='<Your Public Key>';
```

If your user doesn't have password configured, run the following command to set the password.
```sql
ALTER USER <your_user> SET PASSWORD = '<Your Password>' MUST_CHANGE_PASSWORD = FALSE;
```
The password will be needed for Java Agent to connect to Native Application using snowflake-jdbc.

### Native application configuration
In order to create native application you need to adjust values for `APP_NAME`, `APP_VERSION`, `STAGE_DB`, `STAGE_NAME`, `WAREHOUSE` and `CONNECTION` in `Makefile` script.
Those values will be used by all scripts used in this quickstart. `CONNECTION` parameter is the name of snowsql connection defined in previous step.


### Java agent configuration
In order to build Java Agent and connect it to Snowflake you need to edit properties in `connector.properties`.
Copy the private key generated in previous step to `ingestion.private_key` property.


## Connector logic
Duration: 5

When user starts Java Agent application, it connects to Native Application and runs `INIT_DESTINATION_DATABASE` procedure.
Then CLI is launched and user can enable resource using appropriate command.
When a resource is enabled, Java Agent performs the following steps:
- Initialises resource - connects to Native App and runs INIT_RESOURCE procedure
- Runs initial upload - loads some records from data source and uploads them to base table
- Schedules periodical upload (CDC) - loads and uploads some records to delta table every 1 minute

In the meantime, on native app side, the merge task is invoked. It merges data from delta to base table.

### Simplified sequence diagram

![simplified.svg](assets/simplified.svg)

### Detailed sequence diagram
![detailed.svg](assets/detailed.svg)

## Build the connector
Duration: 2

### Overview
Build step for the app consist of:
1. Creating a new `sf_build` directory on local machine for Native App artifacts
2. Creating a new `sf_build_java` directory on local machine for Java Agent artifacts
3. Copying of `Agent.jar` to `sf_build_java` folder
4. Copying of `manifest.yml` to `sf_build` folder
5. Copying of `setup.sql` to `sf_build` folder
6. Copying of `streamlit_app.py` to `sf_build` folder

The `sf_build` serves as the source of truth about the Native Application definition.

### Building
To build the connector execute a convenience script:
```sh
make build
```

## Deploy the connector
Duration: 2

In this step we will deploy the connector to a Snowflake account.

### Overview

Deployment step consists of:
1. Creating a database and stage for app artifacts
2. Uploading the `sf_build` content to the newly created stage
3. Creating an application package using the data from the stage


### Deploy the app
To deploy the connector execute a convenience script:
```sh
make deploy
```


## Installing the connector
Duration: 2

In this step you will install the connector. The installation is encapsulated in a convenience script `install.sql`.

### Overview

Installation step consists of:
1. Creating a new application using application package which was created in previous step
2. Granting necessary privileges to the application

### Running the installation script

To install the connector using the convenience script run the following:
```shell
make install
```

## Using Java Agent to enable resources
Duration: 3

To run Java agent run the following command:
```shell
make run_agent
```

This command runs agent's command line interface. The following commands are available to use:
- `enable <resource_name>` - initialises resource and runs initial and periodical upload
- `disable <resource_name>` - disables periodical upload of given resource
- `quit` - disables all active resources and quits application



## Using Streamlit app to visualise data
Duration: 2

At this point, when the application is deployed and installed, you should be able to see the UI streamlit application.

Navigate to applications option in menu, then find and open application with your application name.
After enabling a resource you will see a bar chart with count of elements in all tables.

![streamlit.png](assets/streamlit.png)

You can check the `Refresh automatically` checkbox to enable periodical refreshing of the page - this way you will see rising charts when the data is being ingested.

## Run integration test
Duration: 4

Example-push-based-java-connector repository contains also a module with integration test.

### Overview
This test checks if the whole application flow works as expected. It performs the following steps:
- builds the connector
- deploys the connector
- installs the connector
- initializes destination database
- initializes new resource
- performs initial upload
- performs single iteration of periodical upload
- executes merge task
- drops the connector application and all database elements that were created

### Running the test
The integration test can be run using a simple make command:
```shell
make test
```

## Conclusion
Duration: 0

**Congratulations! You have successfully completed these Labs**

In this guide, you learned how to:
- create a push based connector
- create Native Applications in Snowflake
- use snowflake-ingestion-sdk to ingest data to Snowflake 
- use snowflake-jdbc to run Snowflake procedures
- optimize merge for the CDC scenario using deferred merge approach

