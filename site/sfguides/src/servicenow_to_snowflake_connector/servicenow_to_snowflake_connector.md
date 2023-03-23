author: sfc-gh-drichert
id: servicenow_to_snowflake_connector
summary: Step-by-step to set up Servicenow connector
categories: Connectors
environments: web
status: Private 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Connectors, Data Engineering, Servicenow 

# Snowflake Connector for ServiceNow Installation
<!-- ------------------------ -->
## Overview 
Duration: 1

Use the Snowflake Connector for ServiceNow to ingest data from ServiceNow into Snowflake automatically and directly. The connector supports both the initial load of historical data as well as incremental updates. The latest data is regularly pulled from ServiceNow and you control how frequently it is refreshed.  

The connector lets you replicate key dimensions and metrics from ServiceNow, including:
- Incidents
- Changes
- Users
- Service catalog items
- Configuration items
- Company assets

Use this quickstart to configure and understand the Snowflake Connector for Servicenow using the Snowsight wizard, select some tables, ingest data, and run some typical usage queries. When you are done stop the connector to avoid costs. You can also do all these steps programmatically; for that please refer to the [Snowflake Conector for ServiceNow documentation](https://https://other-docs.snowflake.com/en/connectors/servicenow/servicenow-index.html). 

Note: This quickstart assumes you do not have a Servicenow account, so it guides you through the steps of creating a developer account. Of course, if you do have a Servicenow account, please feel free to try it out, with the caveat that, at the time of writing, the connector is in public preview and should not be used for production. Make sure to check out the Snowflake documentation for all the necessary rights and limitations. 
### Prerequisites
- Servicenow account with administrator's rights.
- ACCOUNTADMIN rights on the Snowflake account where you will install the connector.
- ORGADMIN rights to Accept the Terms of Service in the Snowflake Marketplace.
- Data ingestion relies on v2 of the ServiceNow table API.
### What You’ll Learn 
- How to set up the Snowflake Connector for Servicenow.
- How to ingest Servicenow data into Snowflake
- How to stop the connector to avoid unnecessary costs in a development environment.
### What You’ll Need 
- A [Snowflake](https://snowflake.com/) Account 
- A [Servicenow](https://developer.servicenow.com/dev.do/) developer account
### What You’ll Build 
A Servicenow to Snowflake ingestion data flow.

<!-- ------------------------ -->
## Servicenow Developer Instance Setup
Duration: 5
If you do not want to test this connector on your ServiceNow account, no problem, set up a developer instance!

1. Go to the [Servicenow developer website](https://developer.servicenow.com), and create a developer user.

1. Log on to the developer website with your newly created user and select **Create an Instance**. 
1. Choose an instance type. You receive an email with your instance URL, and admin user and password. 

And while you are waiting for the ServiceNow account to deploy, let's continue on the Snowflake side!
## Snowflake Configuration
Duration: 10

### Accept Terms & Conditions
1. Log on to your Snowflake account through the Snowsight web interface and change to the **orgadmin** role. 
1. Select “Admin -> Billing & Terms”.
4. In the “Snowflake Marketplace” section, review the Consumer Terms of Service.
5. If you agree to the terms, select “Accept Terms & Conditions”.

### Set Up Two Virtual Warehouses

Log on to your Snowflake account and change to the **accountadmin** role.

1. Navigate to Admin -> Warehouses and select **+ Warehouse**. 
2. Name the first vitural warehosue **SERVICENOW_CONNECTOR_WH** and, leaving the defaults, select **Create Warehouse**. 
1. Repeat the above two steps to create a second virtual warehouse **SERVICENOW_WAREHOUSE**.

### Install the Servicenow connector
The connector is delivered through the Snowflake marketplace. It is delivered into your account as a database with several schemas, tables, views, and stored procedures. 

1. From the Snowflake Account Home page, select **Marketplace**.
1. In the search window, enter **ServiceNow** and select the tile.
1. Review the business needs and usage samples. 
1. Select the warehouse you created above, **SERVICENOW_CONNECTOR_WH**.
1. For this quickstart, leave the default name for the installation database, **Snowflake_Connector_for_ServiceNow**.
1. Select **Get**. You receive the following message, **Snowflake Connector for SeviceNow is now ready to use in your account.**
1. Select **Done**.

Let's check that the connector was installed. From Snowsight, go to **Data -> Databases**. You will see a new database with the name **Snowflake_Connector_for_ServiceNow**. Open the Public schema and views to see the Global_Config view. Some of the Procedures have
also been installed. Others will appear after the installation finishes. 

![installed](assets/installed.png)

## Set up the Snowflake to ServiceNow Oauth hand-shake
Please have two tabs in your browser open for the next part, as you will have to copy some data from Snowflake to ServiceNow and vice-versa. 
* From the Snowflake side, we want the connector to generate the re-direct URL which we will paste into the Application Registry, and
* From the ServiceNow side we want the Application Registry to provide the Cient id and password, which we then paste into Snowflake.

### Snowflake side - part 1 of handshake
Launch the Snowflake Connector for ServiceNow from the **Marketplace** -> **Snowflake Connector for Servicenow**.
1. Select **Manage**.
1. Select **Connect**.
1. Fill in the Servicenow instance details. This is the first part of the Servicenow URL for your Servicenow account, **without** the trailing *service-now.com*.

1. Select **OAuth2** for the Authentication method.
1. Copy the redirect URL for use in a couple of minutes.

Now, open a new tab in your browser (without closing the above), and follow the steps in the next section. 

### Servicenow - part 1 of handshake
1. Log on to your Servicenow developer instance.
1. From the main page, select **All** and search **Application Registry**.

![Application Registry](assets/now_reg_auth.png)
1. Select **New** in the upper right-hand side of the window.
1. Select **Create an OAuth API endpoint for external clients**. 
1. Give the endpoint a name, such as **Snowflake_connector**. Leave the client secret blank. This will autofill.
1. Paste in the redirect URL that was generated on the Snowflake side - part 1. 

![Oauth](assets/now_oauth_endpoint.png)
1. Select **Submit**.
1. Note that the **Client id** and **Client secret** are auto-generated. 
1. Copy the **Client id**.

Now, time to jump back to the Snowflake configuration tab.

### Snowflake - part 2 of handshake

1. Paste the  **Client id** from Servicenow into the Snowflake configure pop-up.
1. Go back to the Servicenow tab and copy the **Client secret** and paste it into the Snowflake configure pop-up. 
 ![Connect](assets/now_connect.png)
1. Select **Connect**. Your Servicenow accounts pops up and requests to connect to Snowflake. 
![check](assets/now_check.png)
1. Select **Allow**.
The connection is established between the two systems. 

To verify the connection, select the three dots [...] and **View Details**. At the top of the pop-up you will see the date **ServiceNow** Authenticated.

[Add a screen shot here]

## Configure the Connector
1. Under the status for the connector, select Configure.
    This displays the Configure Connector dialog. By default, the fields are set to the names of objects that are created when you configure the connector.
Check out the [Configuring the Snowflake Connector for ServiceNow documentation](https://other-docs.snowflake.com/en/connectors/servicenow/servicenow-installing-ui.html#configuring-the-snowflake-connector-for-servicenow) for more information on these fields. 
1. Select Configure. The dialog box closes and the status of the connector changes to Provisioning. It can take a few minutes for the configuration process to complete.

## Select Servicenow Tables
A couple of things to be aware of:
- The connector can only ingest tables with sys_id columns present.
- ServiceNow views are not supported. Instead of ingesting these views, you should synchronize all tables for the underlying view and join the synchronized tables in Snowflake.
- Incremental updates occur only for tables with sys_updated_on or sys_created_on columns.
- For tables that do not have sys_updated_on or sys_created_on columns, the connector uses truncate and load mode.

1. In the **Snowflake Connector for ServiceNow** window, select **Select Tables**.

1. From the search window enter **incident** and check the box next to it and choose a 30 minute sync time. **Do not start the ingestion yet!**

1. To choose other tables, clear the search, put the table name and select the checkbox. Do this for the following tables:
  

   * incident 
   * sys_audit_delete
   * task

    Hint: Select Field title **Status** to sort and show all the tables you selected.
1. Select **Configure** and review the default values for destinations and schemas, roles, a secondary warehouse and journal table.
1. Select **Start Ingestion**. The select windows closes and you get the message "Loading Data" from the main Connector window.

![load](assets/load.png)

You receive a message indicating success:

![success](assets/success.png)

## Connector Monitoring (Query Sync History)
 
In the connector interface, choose **Query Sync History.** A worksheet
opens with several SQL queries you can execute to get monitoring
information.
## Stop the Ingestion
> aside positive
> If you do not stop the connector, it will wake up the virtual warehouse at the specified time interval and consume credits.


1. In Snowsight, select the **Snowflake Connector for Servicenow** tile.

1. In the **Snowflake Connector for ServiceNow** window, select **Stop Ingestion**.

![stop](assets/stop.png)

Read the warning and select **Stop Ingestion**.

## Setting reader role permissions
Now that you have ingested some data, let's create the **servicenow_reader_role** and give it access to the database, schema, and virtual warehouse.
```SQL
USE ROLE accountadmin;
CREATE ROLE servicenow_reader_role;
GRANT USAGE ON DATABASE SERVICENOW_DEST_DB TO ROLE servicenow_reader_role;
GRANT USAGE ON DATABASE SERVICENOW_DEST_DB TO ROLE servicenow_reader_role;
GRANT USAGE ON SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role; 
GRANT USAGE ON WAREHOUSE SERVICENOW_WH TO ROLE servicenow_reader_role;
GRANT SELECT ON FUTURE TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON FUTURE VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL TABLES IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
GRANT SELECT ON ALL VIEWS IN SCHEMA DEST_SCHEMA TO ROLE servicenow_reader_role;
```
## Query the Data
Check out the tables that the connector has created under the DEST_SCHEMA. For each table in ServiceNow that is configured for synchronization, the connector creates the following table and views:

- A table with the same name that contains the data in raw form, where each record is contained in a single VARIANT column.

- A view named table_name__view that contains the data in flattened form, where the view contains a column for each column in the original table and a row for each record that is present in the original table.

- A view named table_name__view_with_deleted that contains the same data as table_name__view as well as rows for records that have been deleted in ServiceNow.

- A table table_name__event_log that contains the history of changes made to records in ServiceNow.

 To query from the raw data, check out [Accessing the raw data](https://other-docs.snowflake.com/en/connectors/servicenow/servicenow-accessing-data.html#accessing-the-raw-data). To query the views (recommended), check out [Accessing the flattened data](https://other-docs.snowflake.com/en/connectors/servicenow/servicenow-accessing-data.html#accessing-the-flattened-data).

### Use this query to identify number of incidents raised by month and priority
Here's a little test query for you to identify the number of incidents raised by month and priority. Other example queries are provided on the Snowflake Connector for ServiceNow page in the Marketplace.

```SQL
USE ROLE ACCOUNTADMIN;
USE DATABASE SERVICENOW_DEST_DB;
USE SCHEMA DEST_SCHEMA;

WITH T1 AS (
    SELECT
    DISTINCT
        T.NUMBER AS TICKET_NUMBER
        ,T.SHORT_DESCRIPTION
        ,T.DESCRIPTION
        ,T.PRIORITY
        ,T.SYS_CREATED_ON AS CREATED_ON
        ,T.SYS_UPDATED_ON AS UPDATED_ON
        ,T.CLOSED_AT
    FROM
      TASK__VIEW T
     LEFT JOIN 
          INCIDENT__VIEW I 
          ON I.SYS_ID = T.SYS_ID -- ADDITIONAL INCIDENT DETAIL
      LEFT JOIN 
          SYS_AUDIT_DELETE__VIEW DEL 
          ON T.SYS_ID = DEL.DOCUMENTKEY -- THIS JOIN HELPS IDENTIFY DELETED TICKETS  
    WHERE
        DEL.DOCUMENTKEY IS NULL --  THIS CONDITION HELPS KEEP ALL DELETED RECORDS OUT
    AND
        I.SYS_ID IS NOT NULL -- THIS CONDITION HELPS KEEP JUST THE INCIDENT TICKETS
)
SELECT
    YEAR(CREATED_ON) AS YEAR_CREATED
    ,MONTH(CREATED_ON) AS MONTH_CREATED
    ,CONFIGURATION_ITEM AS APPLICATION
    ,PRIORITY
    ,COUNT(DISTINCT TICKET_NUMBER) AS NUM_INCIDENTS
FROM
    T1
GROUP BY
    YEAR_CREATED
    ,MONTH_CREATED
    ,PRIORITY
ORDER BY
    YEAR_CREATED
    ,MONTH_CREATED
    ,PRIORITY
;
```

## Delete the Connector (but not the data)
To delete the connector you need to drop the connector database: 
```SQL
DROP DATABASE SNOWFLAKE_CONNECTOR_FOR_SERVICENOW;

```
## Conclusion
Duration: 1

Upon successful completion of this Quickstart you were able to setup the Servicenow connector, ingest some data and run some queries!


