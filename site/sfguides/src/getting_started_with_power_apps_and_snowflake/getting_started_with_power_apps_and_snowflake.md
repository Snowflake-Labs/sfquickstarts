author: chandra-snow
id: power_apps_snowflake
summary: This is a quickstart for using Microsoft Power Platform, Power Apps, Power Automate and Snowflake
categories: Getting-Started, data-engineering, microsoft, power-apps, power-platform, snowflake
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Microsoft, Power Apps, Power Platform, Power Automate

# Getting Started with Power Apps and Snowflake
Duration: 45

<!-- ------------------------ -->
## Overview 
Join Snowflake and Microsoft for an instructor-led hands-on lab to build a PowerApps App that can access retail customer data as virtual tables, do a writeback, trigger a segmentation flow using PowerAutomate without making a copy of the data. We will use the PowerApps connector from Microsoft premium connectors marketplace, which is a wrapper around the Snowflake SQL API that allows to read and write data to Snowflake databases, and execute any stored procedures.

### Power Apps
Microsoft Power Apps and Power Automate are part of the Microsoft Power Platform, a suite of tools designed to empower organizations to create custom applications and automate workflows with minimal coding effort. 

### Snowflake
Snowflake is a cloud-based data platform that allows organizations to store, process, and analyze massive amounts of structured and semi-structured data. It provides a scalable and fully managed services that support diverse data types, making it an ideal choice for businesses looking to harness the power of their data. 

### You'll Learn
- Using Power Platform to read and write to Snowflake. 
- Leveraging Snowflake ML in Power Apps 

### What You’ll Need 
- A free [Snowflake Account](https://signup.snowflake.com/?utm_cta=quickstarts_)
- A Power Apps account [PowerApps](https://learn.microsoft.com/en-us/power-apps/powerapps-overview)
- You must have a premium Power Apps license


### What You’ll Build 
- Load customer data into Snowflake tables. 
- Configure a connection between PowerPlatform and Snowflake.
- Use PowerApps to build a model app, access Snowflake tables to read and writeback.
- Use Snowflake Notebook to create a Machine Learning model. 
- Invoke model predictions using PowerAutomate. 

<!-- ------------------------ -->
## Set Up Snowflake Environment
Duration: 15
### Create Snowflake Objects 

The first thing we will do is create a database and warehouse in your Snowflake environment. 

```sql
USE ROLE accountadmin;

CREATE OR REPLACE WAREHOUSE HOL_WH WITH WAREHOUSE_SIZE='X-SMALL';

CREATE OR REPLACE DATABASE HOL_DB;

GRANT USAGE ON WAREHOUSE hol_wh TO ROLE public;
grant usage on database hol_db to role public;
grant usage on schema hol_db.public to role public;

-- Create a Table with the columns suggested below 
USE ROLE accountadmin;
USE DATABASE hol_db;
USE WAREHOUSE hol_wh;
CREATE OR REPLACE TABLE CUSTOMER_PRESEGMENT (
	ID NUMBER(38,0),
	AGE NUMBER(38,0),
	GENDER VARCHAR(16777216),
	INCOME NUMBER(38,0),
	SPENDING_SCORE NUMBER(38,0),
	MEMBERSHIP_YEARS NUMBER(38,0),
	PURCHASE_FREQUENCY NUMBER(38,0),
	PREFERRED_CATEGORY VARCHAR(16777216),
	LAST_PURCHASE_AMOUNT NUMBER(38,2)
);
grant select on table hol_db.public.customer_presegments to role public;
```

### Get Sample data and scripts from Azure Blob -> Shankar, Nithin  
1. Download the data [file](assets/customer_segmentation_data.csv) 
, notebook and the sql files - or can we reference it from Ext Stage.
2. Login to Snowflake Account and go to Data -> Databases -> HOL_DB
3. Select table CUSTOMER_PRESEGMENT and click Load Data 
![load data](assets/load_db.png)
4. Accept the defaults and complete loading data.

<!-- ------------------------ -->
## Setup PowerApps Environment 
### Set up Azure AD (Entra ID) authentication for Snowflake 
Duration: 15

Now we need to set up an app registration for Active Directory (Entra ID) OAuth, which will establish trust between your Power Platform and Snowflake. This allows you to define and manage permissions and ensures only authorized users to access your application.

For the purposes of this demo, we will create a  **MAKE SURE YOU FOLLOW SERVICE PRINCIPAL AUTH** Authentication and the steps are provided
in the document below. 

https://learn.microsoft.com/en-us/connectors/snowflakev2/#supported-capabilities-for-power-apps

<!-- ------------------------ -->
### Build a PowerApp
Duration: 15

After you have configured PowerApps Connector to Snowflake, go to Power Apps 
1. Click Tables -> Create Virtual Table 

	![virtualtable](assets/Virtual_Table_Create.png)

2. Select Connection that you have setup in prior step, click NEXT
	![connection](assets/connection.jpg)
3. You should now see the table CUSTOMER_PRESEGMENT, click NEXT
4. On Configuration screen, click Next and click FINISH on the last screen.
5. Now, you see that age is negative for ID1 and ID2, click the pencil to make changes and save.
![crud](assets/CRUD_Change.png)
6. Click Apps, click [Start with a page design]
7. Select a dataverse table, and search CUSTOMER_PRESEGMENT and click Create App
8. Save the app as Marketing Segments.  
9. Click the Play button.
	![app](assets/App_Save.png)
10. As a marketer you notice the customers aren't segmented as there is no segment field. 

<!-- ------------------------ -->

## Snowflake Segmentation ML Model  
### Lets look at the clustering Model and deploy it 
Typically your datascience teams develop and deploy the models, and you can invoke them. 
1. Download the Customer Segmentation Notebook [ipynb](assets/customer_segmentation.ipynb) 
2. Connect to Snowflake: Projects -> Notebook
3. Import the notebook you downloaded earlier by clicking import .ipynb file
	![notebook](assets/ImportNotebook.jpg)

4. Click the RunALL button or Start and individual cell. 
5. Create a Procedure to Invoke Model Predictions by running below SQL in a worksheet
	[storedproc](assets/segment_storedproc)


### Build a PowerAutomate Flow -> Shankar, Nithin 
Let's build a PowerAutomate Flow that calls Snowflake Stored Procedure that runs a clustering ML model on the data.
1. Launch PowerAutomate
2. Click Create new flow -> Create from blank
3. In the canvas -> click New step 
5. Search "Snowflake" and select "Submit SQL Statement for Execution" as shown 
	![flow](assets/power_apps_choose_operation.png) 
6. Let's add the following parameters 
	![automateconnect](assets/automate_conn.png)
	Instance - your Snowflake account URL(without https)
	statement - CALL segmentize('CUSTOMER_PRESEGMENT','CUSTOMER_SEGMENT_V'); 
	database - HOL_DB
	schema - PUBLIC 
	warehouse - HOL_WH
	role  - accountadmin
7. Save it as Call_Segmentize_Flow 
		
		
![](assets/.png)
### Update PowerApp to invoke your Flow -> Shankar, Nithin  
1. Put a Button in the Powerapp banner
2. Let's name it Segmentize, and on Action - Invoke the above flow.
3. Publish the App 
4. Now you can see Market Segment information updated for all rows. 
	![segmented](assets/new_flow.png)

### Reset the Demo 
``` sql
DROP DATABASE hol_db;
DROP WAREHOUSE hol_wh;
```
<!-- ------------------------ -->
## Conclusion and Next Steps
Duration: 5

This quickstart will get you started with creating a simple power apps flow that connects to Snowflake and queries a table. From here you can use the connector in many different flows with different power apps activities to read data from and write data to Snowflake see here for more details: [Power-Apps](https://learn.microsoft.com/en-us/power-automate/getting-started). 

![](assets/sf_auth.png)

### Things to look out for
- If you're getting a username and password error make sure that you use the forward slash at the end the external_oauth_issuer parameter value
- Similarly you may explore changing the external_oauth_snowflake_user_mapping_attribute value to "email_name" as that value in your user profile will match the email address in your Power Apps account. 
- Make sure the you're getting the tenant id from your Power Apps account and not your Azure account as they don't always match.
- If you're not seeing the Snowflake actions in your options double check your Power Automate Environment and make sure you're using an environment where the Snowflake connector is available.

<!-- ------------------------ -->
### Potential Use Cases for the Snowflake Power Apps

- Build data apps using the connector to share dashboard/analytics for your marketing campaign with Sales or other business users.
- Build an app to check the NextBest Offer or LTV of a customer to avoid churn.
- Build an app that will allow a user to execute queries from Teams chat against their Snowflake environment.
