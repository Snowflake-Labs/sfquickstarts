author: sfc-gh-drichert
id: servicenow_to_snowflake_connector
summary: Step-by-step to set up Servicenow connector
categories: Connectors
environments: web
status: Private 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Connectors, Data Engineering, Servicenow 

# Servicenow to Snowflake Connector Installation
<!-- ------------------------ -->
## Overview 
Duration: 1

Use this quickstart to configure the Servicenow to Snowflake connector.  

### Prerequisites
- Servicenow account with administrator's rights.
- Snowflake account and user with accountadmin's role.

### What You’ll Learn 
- how to set up the Snowflake Servicenow connector.
- 

### What You’ll Need 
- A [Snowflake](https://snowflake.com/) Account 
- A [Servicenow](https://developer.servicenow.com/dev.do/) developer account

### What You’ll Build 
- A Servicenow connector to load data from Servicenow to Snowflake

<!-- ------------------------ -->
## Servicenow Setup
Duration: 30

1. Go to the [Servicenow developer website](https://developer.servicenow.com), and create a developer user.

1. Log on to the developer website with your newly created user and select **Create an Instance**. 
1. Choose an instance type. Tokyo worked for me. Wait for about 5 minutes. You should receive an email with your instance URL, and admin user and password. 

## Servicenow endpoint configuration
This creates an OAuth client application record and generates a client ID and client secret that the client needs to access the restricted resources on the instance.

1. Log on to your instance.
1. From the main page, select **All** and  search **Application Registry**.
1. Select **New**.
1. Select **Create an OAuth API endpoint for external clients**. 
1. Give the endpoint a name, such as **Snowflake_connector**. Leave the client secret blank. This will autofill.
1. Fill in the redirect URL with this syntax (Alternatively, Snowflake will generate this in a later step and you can come back and modify the redirect URL). 

  ```javascript
   https://apps-api.c1.<cloud_region_id>.<cloud>.app.snowflake.com/oauth/complete-secret
   ```
   where 
   - **cloud_region_id** can be found in the URL of Snowsight, for example: 
 
  https://app.snowflake.com/**us-west-2**/MyAccountId/worksheets

  - and **cloud** is aws or azure or gcp.

   For example, for  AWS US WEST 2 if your Snowflake account is in that region:
  ```javascript
  https://apps-api.c1.us-west-2.aws.app.snowflake.com/oauth/complete-secret
  ```

Select Submit.


---


<!-- ------------------------ -->
## Snowflake Configuration
Duration: 2

Log on to your Snowflake account and change to the accountadmin role.

### Set up Virtual Warehouse
Create a warehouse with the name **SERVICENOW_CONNECTOR_WH**, either through the commnand line or through the GUI, for example:
```SQL
CREATE WAREHOUSE IDENTIFIER('"SERVICENOW_CONNECTOR_WH"') COMMENT = '' WAREHOUSE_SIZE = 'X-Small' AUTO_RESUME = true AUTO_SUSPEND = 60 ENABLE_QUERY_ACCELERATION = false WAREHOUSE_TYPE = 'STANDARD' MIN_CLUSTER_COUNT = 1 MAX_CLUSTER_COUNT = 1 SCALING_POLICY = 'STANDARD';
```
### Get and Configure the Servicenow connector
From the Snowflake Account Home page, select **Data** and then **Private Sharing** 

> aside positive
> Note: this may change for the general release.

In the search window, enter **servicenow**. 

Select the **Snowflake Connector for ServiceNow**.

Select **Get**.

Select the warehouse you created above.

Select **Get**.

You get the following message, "Snowflake Connector for ServiceNow is now ready to use in your account."

Select **Manage**.

Select **Connect**.

Fill in the Servicenow instance. This is the first part of the Servicenow URL for your Servicenow account, **without** the trailing service-now.com

Select **OAuth2** for the Authentication method.

Enter the Client id from Servicenow.

Copy the Client secret from Servicenow. 

> aside positive Hint: unlock the field, and then copy the text to make sure you are actually copying the right thing. 

Select Connect.

Servicenow requests to connet to Snowflake. Accept

Select Configure, and Select Configure again. You will get the message "Connector Successfully configured".

##Select Tables##

From the Snowflake Account Home page, select **Data** and then **Private Sharing** 

> aside positive
> Note: this may change for the general release.

From the search window enter **incident** and choose the incident, incident_fact, and incident_task tables. 

Choose a sync scedule of 30 minutes for the three tables. 

## Connector Monitoring
 
 ### Get general information about all ingestions
 ```sql
 use database SNOWFLAKE_CONNECTOR_FOR_SERVICENOW;
 select * from connector_stats;
```
### Search for information about particular table ingestions
 ```sql
select * from connector_stats where table_name = 'incident';
```

## Accessing the Servicenow data in Snowflake
```SQL
CREATE ROLE servicenow_reader_role;
GRANT USAGE ON DATABASE SERVICENOW_DEST_DB TO ROLE servicenow_reader_role;
GRANT USAGE ON SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role; 
GRANT SELECT ON FUTURE TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
```

## Stop the Connector
From the Snowflake Account Home page, select **Data** and then **Private Sharing** 

> aside positive
> Note: this may change for the general release.

In the search window, enter **servicenow**. 

Select the **Snowflake Connector for ServiceNow**.

Select **Stop Ingestion**.

You get the message: "The configuration of tables will be cleared but data ingested from this report will still be available in SERVICENOW_DEST_DB until you remove it manually."

Again, Select **Stop Ingestion**.


## Delete the Connector (but not the data)
To delete the connector you need to drop the connector database: 
```SQL
DROP DATABASE SNOWFLAKE_CONNECTOR_FOR_SERVICENOW;

```
<!-- ------------------------ -->
## Conclusion
Duration: 1
Upon successful completion of this Quickstart you were able to setup the Servicenow connector!


