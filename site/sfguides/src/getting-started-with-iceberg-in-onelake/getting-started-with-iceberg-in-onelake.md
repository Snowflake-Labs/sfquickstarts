author: Eric Tolotti
id: getting-started-with-iceberg-in-onelake
summary: This is a quickstart for creating Catalog Linked Databases and Iceberg tables usable by both Snowflake and Microsoft Fabric
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/apache-iceberg
environments: web
language: en
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Iceberg in OneLake
<!-- ------------------------ -->
## Overview

Apache Iceberg is an open table format for huge analytical datasets that enables high performance analytics on open data formats with ACID compliance. Snowflake and Azure both support Iceberg format that enables customers to drastically improve data interoperability, speed of implementation, and performance for integrated data lakes.

OneLake is the single, unified, and open SaaS data lake in Microsoft Fabric. Data is stored in parquet file formats, and has metadata for both the Delta Lake and Iceberg open table standards. This structure makes OneLake ideal storage for an open lakehouse. Iceberg engines like Snowflake can directly connect to and query the data in OneLake, without needing to copy or move it first. This allows using Snowflake's powerful compute engine for analysis while keeping data in a single, standard, accessible location, greatly simplifying data management and boosting interoperability.

In this quickstart you will setting OneLake as a Catalog Linked Database in Snowflake. Processing the raw data in Snowflake, and then writing as Snowflake iceberg tables in OneLake. This creates a fully interoperable, Snowflake Open Lakehouse on OneLake.

### Prerequisites
- familiarity with [Snowflake](/en/developers/guides/getting-started-with-snowflake/) and a Snowflake account
- familiarity with [Microsoft Fabric](https://learn.microsoft.com/en-us/fabric/get-started/microsoft-fabric-overview) and a Fabric workspace


### What You Will Learn
- creating an external volume
- setting up a catalog linked database
- creating and populating an Iceberg table on OneLake
- querying Iceberg from Snowflake and Fabric services

### What You Will Build 
- You will build a fully interoperable, open lakehouse by integrating Snowflake with Microsoft OneLake. You will get sample data in Fabric, create an external volume, set up OneLake as an Catalog Linked Database in Snowflake, and create Iceberg tables in OneLake. The end result is a seamless data architecture where Snowflake can manage and query data stored in the open formats of OneLake.

### What You will Need 
- A free [Snowflake Account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- [Fabric Capacity](https://learn.microsoft.com/en-us/fabric/get-started/fabric-trial)  
- For the sake of the lab it is best if both platforms have access to the public internet and are not in a virtual network.

The end-to-end workflow will look like this:
![](assets/diagram.png)


<!-- ------------------------ -->
## Prepare Sample Data

In Microsoft Fabric, begin by creating a New Item.
![](assets/NewItem.png)
Select Lakehouse and name it IcebergQuickstart.  Ensure Lakehouse schemas is checked. And Create.
In the center of the screen, select Start with sample data. And select Retail data model from Wide World Importers.
![](assets/GetData.png)
You should now see a number of tables available.
![](assets/FabricTables.png)


<!-- ------------------------ -->
## Create a Snowflake Catalog Linked Database

### Azure Portal
1. In the Azure portal search for and open "App Registrations"
![](assets/AppReg.png)

2. Click "+ New Registration"
![](assets/NewReg.png)
3. Give the app name (ex. <username>_Snowflake_Oath_Client )
Create by clicking "Register"
Copy and make note of the "Directory (tenant) ID"
Copy and make note of the "Application (client) ID"
Copy and make note of the  "Managed application in local directory" Name -- used for "Managed Access" step
![](assets/AppRegTokens.png)
4. Under Manage, choose API Permissions
Under Configured permissions, click "Add a Permission"
Select the Azure Storage tile.
Check the box for user_impersonation
Click Add Permission
![](assets/AppRegPerm.png)
5. On the left hand menu, Click "Certificates & secrets"
Click "New Client Secret"
!!IMPORTANT!! Copy the Value, as it will not be available later. (Secret ID doesn't not matter)
![](assets/CertsSecrets.png)
![](assets/AppRegCert.png)

### Fabric Workspace
6. Return to your Fabric Workspace (note: not your Lakehouse)
Click Manage Access at the top
![](assets/ManageAccess2.png)
Paste in the "Managed application in local directory" from earlier, and set the role to "Contributor"
![](assets/AddOauth.png)

These Fabric Settings needs to be enabled

![](assets/SPN.png)
![](assets/settings.png)



### Fabric Lakehouse
7. Click on your Lakehouse to fetch the following values from the url in the browser (just copy url)
![](assets/URL.png)
### Snowflake
8. Create a New SQL file. 
Because setup will require creating account level integrations, ACCOUNTADMIN role will be required for setup.
9. Paste in the variables you have captured into the variables at the start of the SQL script. You should have a total of 6 items you have captured.
```sql
/*****************************************************************************************
## ❄️ Snowflake to Microsoft Fabric OneLake Integration Script 🔗

### 📝 Overview
This script automates the setup of a read-only connection from Snowflake to a Microsoft
Fabric Lakehouse. It uses a Catalog Integration to allow you to query your Fabric
Lakehouse data directly within Snowflake, treating it like a native database.

### ✨ Features
- **Variable-driven Configuration:** Just set a few variables at the beginning to
  configure the entire script.
- **Automated Object Naming:** Consistently names all necessary Snowflake objects based on
  your inputs.
- **Step-by-Step Execution:** The script is broken down into logical blocks with clear
  instructions.
- **Validation & Troubleshooting:** Includes built-in queries to verify the setup and
  diagnose potential issues.
- **Teardown Script:** Provides commands to cleanly remove all created objects.

### 📋 Prerequisites
- **Snowflake Account:** You need the `ACCOUNTADMIN` role to create the required
  integration objects.
- **Microsoft Azure Account:** You must have permissions to create an Azure App
  Registration (Service Principal). You'll need its **Tenant ID**, **Application (client)
  ID**, and a **Client Secret**.
- **Microsoft Fabric Workspace:** You need a Fabric Lakehouse and permissions to grant
  **Admin** or **Contributor** access in the workspace settings.

---

### 🚀 How to Use
Execute the script in sequential blocks within a Snowflake worksheet. Follow the
instructions carefully, especially the manual steps.

**Block 1: User Configuration**
- **Action:** Fill in the values for the variables in the first `BEGIN...END;` block.
  These include your Azure tenant/app details and your Fabric Lakehouse information.

**Block 2: Programmatic Variable Setup**
- **Action:** Execute this block as is. **No modifications are needed.**
- **Purpose:** This block uses your inputs to programmatically construct object names and
  parse necessary IDs from the Fabric Lakehouse URL.

**Step 1: Create Catalog Integration**
- **Action:** Run the `CREATE OR REPLACE CATALOG INTEGRATION` statement.
- **Purpose:** This object tells Snowflake how to communicate with the Fabric Iceberg REST
  API.

**Step 2: Create External Volume**
- **Action:** Run the `CREATE OR REPLACE EXTERNAL VOLUME` statement.
- **Purpose:** This creates a reference to the OneLake storage location, enabling
  Snowflake to access the underlying Parquet data files.

**Step 3 & 4: Grant Permissions in Fabric ‼️ CRITICAL MANUAL STEP ‼️**
- **Action:**
    1.  Execute the query in **Step 3** (`DESC EXTERNAL VOLUME...`).
    2.  **Copy** the value from the `AZURE_MULTI_TENANT_APP_NAME` column.
    3.  **Click** the URL in the `AZURE_CONSENT_URL_CLICK_ME` column to grant consent.
        (It's normal for this to redirect to the Snowflake homepage).
    4.  Go to your **Fabric Workspace** > **Manage Access**.
    5.  Add a new user by **pasting** the `AZURE_MULTI_TENANT_APP_NAME` value and assign
        it the **Admin** or **Contributor** role.
- **IMPORTANT:** The connection will fail if this manual permission step is skipped.

**Step 5: Create Catalog Linked Database**
- **Action:** Run the `CREATE OR REPLACE DATABASE` statement.
- **Purpose:** This creates the final read-only database in Snowflake that mirrors the
  schemas and tables from your Fabric Lakehouse.

---

### ✅ Post-Setup
You're done! You can now query the schemas and tables from your Fabric Lakehouse directly
in the newly created Snowflake database.

### 🛠️ Troubleshooting
A query using `SYSTEM$CATALOG_LINK_STATUS` is at the end of the script. If you have
issues, run this query to get detailed error messages. An empty result set means the
connection is healthy.

### 🧹 Teardown
A commented-out teardown script is provided at the very end. To remove all objects created
by this script, uncomment and execute the `DROP` statements.
*****************************************************************************************/

USE ROLE ACCOUNTADMIN;


/*****************************************************************************************
This section contains all the variables that need to be configured by the user before
executing the script. Modifying these values will alter the script's behavior.

After setting the values, execute.
*****************************************************************************************/
BEGIN

-- Azure OAuth App Variables (set these values)
SET azure_tenant_id = '9a2d78cb-73e9-40ee-a558-fc1acxxxxxxx';
SET azure_oauth_app_client_id = '2c123f73-ce25-4a65-9ab4-127aexxxxxxx';
SET azure_oauth_client_secret_value = 'oHq8Q~rVo8UGMVHQk22OMNkJzlzXLBtYtxxxxxxx';
SET azure_oauth_app_managed_app_in_local_dir_name = 'Example_Snowflake_Oath_Client';

-- Lakehouse variables (set these values)
SET fabric_lakehouse_name = 'IcebergQuickstart';
SET fabric_lakehouse_url = 'https://app.fabric.microsoft.com/groups/e69d053d-2955-4d3c-9b2e-75e4fxxxxxxx/lakehouses/65541115-78bc-4ded-a2f0-058e4xxxxxxx?ctid=9a2d78cb-73e9-40ee-a558-fc1acxxxxxxx&experience=fabric-developer';

-- return message (no need to edit)
RETURN 'SUCCESS: Variables set';
END;

/*****************************************************************************************
After successfully executing the above, execute this block.
These variables are set programmatically. Do not edit the these values.
*****************************************************************************************/

-- Snowflake Object Names
SET snowflake_fabric_rest_catalog_integration_name = UPPER(CONCAT('FABRIC_', $fabric_lakehouse_name,'_IRC_INT'));
SET snowflake_fabric_external_volume = UPPER(CONCAT('FABRIC_', $fabric_lakehouse_name,'_IRC_EXTERNAL_VOLUME'));
SET snowflake_catalog_linked_db_name = UPPER(CONCAT($fabric_lakehouse_name, '_CLDB'));

-- Snowflake Object comments
SET snowflake_fabric_rest_catalog_integration_comment = CONCAT('Fabric OneLake Iceberg REST Catalog Integration for Lakehouse: ', $fabric_lakehouse_name);
SET snowflake_fabric_external_volume_comment = CONCAT('Fabric OneLake External Volume for Lakehouse: ', $fabric_lakehouse_name);
SET snowflake_catalog_linked_db_comment = CONCAT('Catalog Linked Database for Fabric Lakehouse: ', $fabric_lakehouse_name);


-- Snowflake Object Parameters
SET fabric_workspace_id = (SELECT REGEXP_SUBSTR($fabric_lakehouse_url, 'groups/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', 1, 1, 'e', 1));
SET fabric_data_item_id = (SELECT REGEXP_SUBSTR($fabric_lakehouse_url, 'lakehouses/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', 1, 1, 'e', 1));
SET catalog_name = (SELECT CONCAT_WS('/', $fabric_workspace_id, $fabric_data_item_id));
SET oauth_token_uri = (SELECT CONCAT('https://login.microsoftonline.com/', $azure_tenant_id,'/oauth2/v2.0/token'));
SET storage_base_url = (SELECT CONCAT('azure://onelake.dfs.fabric.microsoft.com/', $catalog_name));


/*****************************************************************************************
This query enables you to inspect all variables that were set above.
Optional: Save this information via copy/paste of donwnload a csv
*****************************************************************************************/

WITH validate_cte as (
    SELECT 'Azure' as variable_origin, 'azure_tenant_id' as variable_name, $azure_tenant_id as variable_value, 'Used in creation of EXTERNAL VOLUME' as notes union all
    SELECT 'Azure', 'azure_oauth_app_managed_app_in_local_dir_name', $azure_oauth_app_managed_app_in_local_dir_name, 'Used to add via "Manage Access" in Fabric Workspace (set role to "contributor")' union all
    SELECT 'Azure', 'azure_oauth_app_client_id', $azure_oauth_app_client_id, 'Used in creation of CATALOG INTEGRATION' union all
    SELECT 'Azure', 'azure_oauth_client_secret_value', $azure_oauth_client_secret_value, 'Used in creation of CATALOG INTEGRATION' union all
    SELECT 'Fabric Lakehouse', 'fabric_lakehouse_name', $fabric_lakehouse_name, 'Used to construct names for Snowflake Objects such as "snowflake_fabric_rest_catalog_integration_name", "snowflake_fabric_external_volume", and  "snowflake_catalog_linked_db_name". Note: This does not need to match the lakehouse name in fabric, this used for object naming consistency ' union all
    SELECT 'Fabric Lakehouse', 'fabric_lakehouse_url', $fabric_lakehouse_url, 'Reference. Used to extract "fabric_workspace_id" and "fabric_data_item_id"' union all
    SELECT 'Expression (constructed)', 'oauth_token_uri', $oauth_token_uri, 'Used in creation of CATALOG INTEGRATION, Constructed with "azure_tenant_id"' union all
    SELECT 'Expression (extracted)', 'fabric_workspace_id', $fabric_workspace_id, 'Reference, used to construct "catalog_name" variable' union all
    SELECT 'Expression (extracted)', 'fabric_data_item_id', $fabric_data_item_id, 'Reference, used to construct "catalog_name" variable' union all
    SELECT 'Expression (constructed)', 'catalog_name', $catalog_name, 'Used in creation of CATALOG INTEGRATION' union all
    SELECT 'Expression (constructed)', 'storage_base_url', $storage_base_url, 'Used in creation of CATALOG INTEGRATION' union all
    SELECT 'Expression (constructed)', 'snowflake_fabric_rest_catalog_integration_name', $snowflake_fabric_rest_catalog_integration_name, 'Used in creation of EXTERNAL VOLUME' union all
    SELECT 'Expression (constructed)', 'snowflake_fabric_rest_catalog_integration_comment', $snowflake_fabric_rest_catalog_integration_comment, 'Comment for snowflake_fabric_rest_catalog_integration_name' union all
    SELECT 'Expression (constructed)', 'snowflake_fabric_external_volume', $snowflake_fabric_external_volume, 'Name of EXTERNAL VOLUME object' union all
    SELECT 'Expression (constructed)', 'snowflake_fabric_external_volume_comment', $snowflake_fabric_external_volume_comment, 'Comment for snowflake_fabric_external_volume' union all
    SELECT 'Expression (constructed)', 'snowflake_catalog_linked_db_name', $snowflake_catalog_linked_db_name, 'Name of Catalog Linked Database' union all
    SELECT 'Expression (constructed)', 'snowflake_catalog_linked_db_comment', $snowflake_catalog_linked_db_comment, 'Comment for snowflake_catalog_linked_db_name'
)
SELECT * FROM validate_cte;


/*****************************************************************************************
>> Step 1
Create the Snowflake External Iceberg Rest Catalog Integration object.

The naming convention used in this script is:
FABRIC_[fabric_lakehouse_name]__IRC_INT
*****************************************************************************************/
-- Create catalog integration object
CREATE OR REPLACE CATALOG INTEGRATION IDENTIFIER($snowflake_fabric_rest_catalog_integration_name)
    CATALOG_SOURCE = ICEBERG_REST
    TABLE_FORMAT = ICEBERG
    REST_CONFIG = (
        CATALOG_URI = 'https://onelake.table.fabric.microsoft.com/iceberg' -- Iceberg base URL at the OneLake table endpoint
        CATALOG_NAME = $catalog_name -- Fabric data item scope, in the form `workspaceID/dataItemID.lakehouse`
    )
    REST_AUTHENTICATION = (
        TYPE = OAUTH -- Entra auth
        OAUTH_TOKEN_URI = $oauth_token_uri -- Entra tenant ID
        OAUTH_CLIENT_ID = $azure_oauth_app_client_id -- Entra application client ID
        OAUTH_CLIENT_SECRET = $azure_oauth_client_secret_value -- Entra application client secret value
        OAUTH_ALLOWED_SCOPES = ('https://storage.azure.com/.default') -- Storage token audience
    )
    ENABLED = TRUE
    COMMENT = $snowflake_fabric_rest_catalog_integration_comment
;


/*****************************************************************************************
Validate the Catalog Integration object was created
*****************************************************************************************/
SET SHOW_INTEGRATION_CMD = CONCAT('SHOW CATALOG INTEGRATIONS LIKE ','''', $snowflake_fabric_rest_catalog_integration_name, '''' );
EXECUTE IMMEDIATE $SHOW_INTEGRATION_CMD;


/*****************************************************************************************
Optional: describe the Catalog Integration object
*****************************************************************************************/
DESC CATALOG INTEGRATION IDENTIFIER($snowflake_fabric_rest_catalog_integration_name);


/*****************************************************************************************
>> Step 2
Create the External Volume object
*****************************************************************************************/

-- Note this command constructs and executes the SQL statement.
EXECUTE IMMEDIATE $$
DECLARE
    constructed_sql_statement VARCHAR;
BEGIN
    SELECT
        'CREATE OR REPLACE EXTERNAL VOLUME IDENTIFIER(''' || $snowflake_fabric_external_volume || ''')' ||
        '\n    STORAGE_LOCATIONS =' ||
        '\n    (' ||
        '\n        (' ||
        '\n            NAME = ''' || $snowflake_fabric_external_volume || ''',' ||
        '\n            STORAGE_PROVIDER = ''AZURE'',' ||
        '\n            STORAGE_BASE_URL = ''' || $storage_base_url || ''',' ||
        '\n            AZURE_TENANT_ID = ''' || $azure_tenant_id || '''' ||
        '\n        )' ||
        '\n    )' ||
        '\n    ALLOW_WRITES = FALSE' ||
        '\n    COMMENT = ''' || $snowflake_fabric_external_volume_comment || '''' ||
        '\n;'
    INTO :constructed_sql_statement;

    -- RETURN :constructed_sql_statement;
    EXECUTE IMMEDIATE :constructed_sql_statement;
    RETURN 'CREATE EXTERNAL VOLUME statement executed successfully.';
END;
$$;


/*****************************************************************************************
Verify the External Volume Object
* 'success' property should have a value of 'true'
*****************************************************************************************/
SELECT
    VEV.KEY as PROPERTY,
    VEV.VALUE::string as PROPERTY_VALUE
FROM LATERAL FLATTEN(
    input => PARSE_JSON(SYSTEM$VERIFY_EXTERNAL_VOLUME($snowflake_fabric_external_volume))
    ) as VEV
WHERE TRUE
    AND PROPERTY IN (
        'location'
        ,'region'
        ,'servicePrincipalProperties'
        ,'storageAccount'
        ,'storageLocationName'
        ,'storageLocationSelectionResult'
        ,'success'
        )
ORDER BY PROPERTY DESC;


/*****************************************************************************************
>> Step 3
* Copy the Azure Multi-tenant app name
* click the "consent url" (it will open snowflake's homepage, this is expected)
*****************************************************************************************/
DESC EXTERNAL VOLUME identifier($snowflake_fabric_external_volume) ->>
SELECT 
    PARSE_JSON("property_value") as property_value,
    split_part(property_value:AZURE_MULTI_TENANT_APP_NAME::string, '_', 1) as AZURE_MULTI_TENANT_APP_NAME,
    property_value:AZURE_CONSENT_URL::string as AZURE_CONSENT_URL_CLICK_ME, 
    property_value:AZURE_TENANT_ID::string as AZURE_TENANT_ID, -- exposed for troubleshooting
    property_value:STORAGE_PROVIDER::string as STORAGE_PROVIDER, -- exposed for troubleshooting
    property_value:STORAGE_REGION::string as STORAGE_REGION, -- exposed for troubleshooting
    -- property_value:STORAGE_BASE_URL::string as STORAGE_BASE_URL,
    -- property_value:STORAGE_ALLOWED_LOCATIONS as STORAGE_ALLOWED_LOCATIONS
FROM $1
    WHERE "property" = 'STORAGE_LOCATION_1';



/************************************!!! STOP !!!******************************************
>> Step 4 

1. Return to your Fabric Workspace
2. Click on Manage Access
3. Paste in the value of AZURE_MULTI_TENANT_APP_NAME from the above query
4. Choose role Admin

Once this is complete, you can return to this worksheet to create the Catalog Linked
Database
*****************************************************************************************/

```

### Fabric Workspace
1. Return to your Fabric Workspace and Click Manage Access in the top right of the interface.
Make sure you are in your Fabric Work Space, and NOT your Lakehouse interface.
2. Take the value of the AZURE_MULTI_TENANT_APP_NAME you copied from the last query you ran in Snowflake, and add it to the workspace.
![](assets/AddPeople.png)
![](assets/AddSPN.png)
3. Return to Snowflake SQL File

### Snowflake
1. Continue with the Snowflake SQL Script to Create your Catalog Linked Database
```sql
/*****************************************************************************************
Create a Snowflake Catalog linked database to connect to Fabric OneLake Lakehouse

Reference:
* https://docs.snowflake.com/en/sql-reference/sql/create-database-catalog-linked
*****************************************************************************************/
CREATE OR REPLACE DATABASE IDENTIFIER($snowflake_catalog_linked_db_name)
  LINKED_CATALOG = (
    CATALOG = $snowflake_fabric_rest_catalog_integration_name
  )
  EXTERNAL_VOLUME = $snowflake_fabric_external_volume
  COMMENT = $snowflake_catalog_linked_db_comment
;

/*****************************************************************************************
Finshed!
You can now query and explore your data.
Note: Fabric is case sensitive, so you will need to use double quoted identifiers for 
mixed case or lower case object names. ex. "schema"."table"
*****************************************************************************************/
USE DATABASE IDENTIFIER($snowflake_catalog_linked_db_name);
SHOW SCHEMAS;
SHOW TABLES;

/*****************************************************************************************
TROUBLESHOOTING

This query monitors the status of a catalog link by retrieving the
execution state, error details, and timing information from the system
function SYSTEM$CATALOG_LINK_STATUS for the variable CATALOG_LINKED_DB_NAME

No results is good. 
*****************************************************************************************/

WITH CATALOG_LINK_STATUS_CTE
AS
(
    SELECT PARSE_JSON(SYSTEM$CATALOG_LINK_STATUS($snowflake_catalog_linked_db_name)) AS RAW
)
SELECT 
    CLS.RAW:executionState::string AS EXECUTION_STATE,
    FD.INDEX as ERROR_INDEX,
    FD.value:errorCode::string AS ERROR_CODE,
    FD.value:errorMessage::string AS ERROR_MESSAGE,
    FD.value:qualifiedEntityName::string AS QUALIFIED_ENTITY_NAME,
    FD.value:entityDomain::string AS ENTITY_DOMAIN,
    FD.value:operation::string AS OPERATION,
    CLS.RAW:lastLinkAttemptStartTime::string AS LAST_LINK_ATTEMPT_START_TIME
FROM CATALOG_LINK_STATUS_CTE AS CLS,
    LATERAL FLATTEN(input => CLS.RAW, path => 'failureDetails', OUTER => True) AS FD;


/*****************************************************************************************
Teardown script
*****************************************************************************************/
-- DROP DATABASE IF EXISTS IDENTIFIER($snowflake_catalog_linked_db_name);
-- DROP EXTERNAL VOLUME IF EXISTS IDENTIFIER($snowflake_fabric_external_volume);
-- DROP CATALOG INTEGRATION IDENTIFIER($snowflake_fabric_rest_catalog_integration_name);
```
It may take a minute for the initial sync to complete. You can run the troubleshooting query above to check on the status.



<!-- ------------------------ -->
## Create a Snowflake Iceberg table in OneLake

In this section, curated and enriched data will be written back to OneLake. In a real environment this would be the data engineering work to clean the raw data in OneLake, combine data from disparate sources, modeling the unified data in your enterprise data warehouse, and preparing data products to be consumed by users. But for the sake of this quickstart, this step will just be merging some of the raw data and filtering records and writing the table back to OneLake.

### Create the External Volume for writing to OneLake
In the previous section, an external volume for reading from the Iceberg Rest Catalog was created, now one has to be created to write iceberg tables.

You will need your OneLake Base URL. To find this in Fabric UI:
- Go into your IcebergQuickstart Lakehouse.
- In the Explorer, click the ellipses next to Files and then Properties.
- In the Properties Menu, copy the URL.
- Note: You will replace the https:// from the URL with azure:// in the SQL below.
![](assets/properties.png)
![](assets/properties2.png)


Next you will need your Azure Tenant ID you found in the previous section and entered as a parameter in the SQL script. 

Copy this query into Snowflake and fill in the parameters with the collected information. This creates a database and the iceberg external volume to write to.

```sql
use role accountadmin;
CREATE OR REPLACE DATABASE IcebergQuickstart_EnrichedData;
CREATE OR REPLACE SCHEMA DBO;

CREATE OR REPLACE EXTERNAL VOLUME FABRIC_ICEBERGQUICKSTART_WRITE_EXTERNAL_VOLUME
  STORAGE_LOCATIONS =
    (
      (
        NAME = 'FABRIC_ICEBERGQUICKSTART_WRITE_EXTERNAL_VOLUME'
        STORAGE_PROVIDER = 'AZURE'
        STORAGE_BASE_URL = 'azure://onelake.dfs.fabric.microsoft.com/<FabricWorkspaceName>>/<FabricLakehouseName>.Lakehouse/Files/'
        AZURE_TENANT_ID = '<Tenant ID>'
      )
    );
```


### Create Table
Now run the following to create the Iceberg table and insert data from the sample dataset. In a real enviornment this would be the engineering to go from raw data to curated data products, but for the quickstart this step is just some basic data merging into a new fact table.

```sql
--Create the Iceberg table in OneLake
 CREATE OR REPLACE ICEBERG TABLE ICEBERGQUICKSTART_ENRICHEDDATA.DBO.FACT_EMPLOYEE_PROFIT (
        EMPLOYEE_PREFERRED_NAME STRING,
        BRAND STRING,
        TOTAL_PROFIT NUMBER(18, 2),
        TOTAL_INVOICES int,
        TOTAL_SALES_REVENUE NUMBER(18, 2)
    )
    EXTERNAL_VOLUME = 'FABRIC_ICEBERGQUICKSTART_WRITE_EXTERNAL_VOLUME'
    CATALOG = snowflake
    BASE_LOCATION = 'FACT_EMPLOYEE_PROFIT';

--Insert sample data
INSERT INTO ICEBERGQUICKSTART_ENRICHEDDATA.DBO.FACT_EMPLOYEE_PROFIT
    --Top Selling Employees: Profit Breakdown by Product Brand
SELECT
    T_E.PreferredName,
    T_SI.Brand,
    SUM(T0.Profit) AS TotalProfit,
    COUNT(T0.WWIInvoiceID) AS TotalInvoices,
    SUM(T0.TotalExcludingTax) AS TotalSalesRevenue
FROM
    fact_sale T0
JOIN
    dimension_employee T_E ON T0.SalespersonKey = T_E.EmployeeKey
JOIN
    dimension_stock_item T_SI ON T0.StockItemKey = T_SI.StockItemKey
WHERE
    T_E.IsSalesperson = 1
    AND T0.Profit > 0
GROUP BY
    T_E.PreferredName,
    T_SI.Brand
ORDER BY
    T_E.PreferredName,
    TotalProfit DESC;
```

You can then query the iceberg table from Snowflake.
```sql
Select * from ICEBERGQUICKSTART_ENRICHEDDATA.DBO.FACT_EMPLOYEE_PROFIT;
```

<!-- ------------------------ -->
## Reading Snowflake Data Object in Fabric

In order for Fabric to work on the Iceberg tables, you need to set up shortcuts to the data.

1. Open the workspace that contains your Fabric lakehouse object. 
  - Click Workspace settings.
  - Under Delegated settings, click OneLake settings, and turn on the Authenticate with OneLake user-delegated SAS tokens setting.
Note: This is a temporary step – this will be removed as a required step in the near future.

![](assets/OneLakeSettings.png)

2. In your workspace, open your Fabric lakehouse object.

3. Click New shortcut from tables.

4. Select a OneLake Shortcut.

5. Enter the connection information for your storage location.

6. Navigate the folder structure and select the checkbox next to your Iceberg table folder to select it as the shortcut target location. Do not select the checkboxes for “data” or “metadata” subfolders.

7. Click Next and Create your shortcut.

8. You can now preview the table, or query and see the same results that appear when querying the table from Snowflake.






<!-- ------------------------ -->
## Conclusion and Resources


Congratulations! You've successfully created an Iceberg table in OneLake as a Snowflake data object, and set up OneLake as a catalog linked database in Snowflake. Resulting in a fully bi-directional Open Lakehouse. You can now use this data for power BI reports, querying from Snowflake, working with Snowpark, working with Fabric  Notebooks, and many more use-cases.


### What You Learned
- creating an external volume
- using sample data through Snowflake data sharing
- creating an external volume and populating an Iceberg table on OneLake
- setting OneLake as a catalog linked database in Snowflake
- querying Iceberg from Snowflake and Fabric services

### Resources
- [CREATE CATALOG INTEGRATION (Apache Iceberg™ REST)](https://docs.snowflake.com/en/sql-reference/sql/create-catalog-integration-rest)

- [CREATE EXTERNAL VOLUME](https://docs.snowflake.com/en/sql-reference/sql/create-external-volume)

- [CREATE DATABASE (catalog-linked)](https://docs.snowflake.com/en/sql-reference/sql/create-database-catalog-linked)

- [Getting started with OneLake table APIs for Iceberg (Snowflake)](https://learn.microsoft.com/en-us/fabric/onelake/table-apis/onelake-iceberg-table-apis-detailed#snowflake)

If you have any questions, reach out to your Snowflake account team!
