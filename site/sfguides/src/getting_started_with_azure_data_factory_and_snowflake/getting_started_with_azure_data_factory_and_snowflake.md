author: sfc-gh-etolotti
id: getting_started_with_azure_data_factory_and_snowflake
summary: This is a quickstart for using Snowflake with Azure Data Factory
categories: Getting-Started, data-engineering, Microsoft
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Azure, Microsoft

# Getting Started with Azure Data Factory and Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 10

Azure Data Factory serves as a central orchestrator for managing data tasks, especially in ETL processes. It empowers businesses to seamlessly manage data movement through a code-free UI for intuitive authoring and single-pane-of-glass monitoring and management.. By streamlining these workflows, Azure Data Factory enables organizations to harness their data assets effectively, driving informed decision-making and operational efficiency in today's data-centric landscape.

In this quickstart we will build an architecture that demonstrates how to use Azure Data Factory to orchestrate data ingestion from an Azure SQL transactional database into Snowflake to generate powerful analytical insights.


### Prerequisites
- Familiarity with [Snowflake](https://quickstarts.snowflake.com/guide/getting_started_with_snowflake/index.html#0) and a Snowflake account
- Familiarity with Azure and an Azure account, an ADF workspace, and an Azure SQL with Adventure works sample data.

### You'll Learn
- How to deploy an Azure SQL with Adventure Works sample data
- Setup an Azure Data Factory pipeline, with linked services and datasets
- Utilize Copy Data, Data Flow, and Script activities using both SQL and SnowPark Python within ADF

### What You’ll Need 
- A free [Snowflake Account](https://signup.snowflake.com/)
- [Azure Account](https://azure.microsoft.com/en-us/free/search/?ef_id=_k_2ba2be3ad9791e57964fda0c62ccd55c_k_&OCID=AIDcmm5edswduu_SEM_k_2ba2be3ad9791e57964fda0c62ccd55c_k_&msclkid=2ba2be3ad9791e57964fda0c62ccd55c) with ADF, storage container, and Azure SQL.

### What You’ll Build 
You will build an orchestrated data pipeline from Azure SQL to Snowflake.
- Deploy an Azure SQL with Adventure Works 
- Deploy and ADF Workspace
- Build an ADF pipeline
- Trigger the data pipeline

The end-to-end workflow will look like this:
![](assets/openai_sf_arch.png)

<!-- ------------------------ -->
## Use Case
Duration: 5

As a retail analyst, imagine effortlessly unraveling your company's sales performance with Azure Data Factory and Snowflake. Your sales data, stored in Azure SQL, seamlessly flows into Snowflake, where you can conduct comprehensive analyses with unprecedented speed and scalability. A combination of GUI and scripting-based interfaces allows anyone, no matter their skillset or preferences, to easily orchestrate data pipelines. With pushdown compute capabilities, choose between SQL and Python to effortlessly sift through the data within Snowflake, revealing invaluable insights. 


<!-- ------------------------ -->
## Set Up Snowflake Environment
Duration: 5

The first thing you will do is create a database and warehouse in your Snowflake environment. Run the below code in a Snowflake worksheet. We are using the AccountAdmin role here for demo purposes, but in production you will likely use a different role.
```sql
-- Create a new database (if not already created)
CREATE DATABASE IF NOT EXISTS ADFdemo;
USE DATABASE ADFdemo;
-- Create a new virtual warehouse (if not already created)
CREATE WAREHOUSE IF NOT EXISTS ADFdemo WITH WAREHOUSE_SIZE='X-SMALL';
CREATE SCHEMA IF NOT EXISTS Raw;
CREATE SCHEMA IF NOT EXISTS Analytics;

CREATE OR REPLACE TABLE Raw.Customer(
	CustomerID int,
	NameStyle STRING ,
	Title STRING NULL,
	FirstName STRING ,
	MiddleName STRING NULL,
	LastName STRING ,
	Suffix STRING NULL,
	CompanyName STRING NULL,
	SalesPerson STRING NULL,
	EmailAddress STRING NULL,
	Phone STRING NULL,
	PasswordHash STRING ,
	PasswordSalt STRING ,
	rowguid STRING ,
	ModifiedDate datetime 
);

CREATE OR REPLACE TABLE Raw.Product(
	ProductID int  ,
	Name STRING ,
	ProductNumber STRING ,
	Color STRING NULL,
	StandardCost decimal ,
	ListPrice decimal ,
	Size STRING NULL,
	Weight decimal(8, 2) NULL,
	ProductCategoryID int NULL,
	ProductModelID int NULL,
	SellStartDate datetime ,
	SellEndDate datetime NULL,
	DiscontinuedDate datetime NULL,
	ThumbNailPhoto STRING NULL,
	ThumbnailPhotoFileName STRING NULL,
	rowguid STRING ,
	ModifiedDate datetime 
); 

CREATE OR REPLACE TABLE Raw.ProductCategory(
	ProductCategoryID int  ,
	ParentProductCategoryID int NULL,
	Name STRING ,
	rowguid STRING ,
	ModifiedDate datetime 
);

CREATE OR REPLACE TABLE Raw.SalesOrderDetail(
	SalesOrderID int ,
	SalesOrderDetailID int ,
	OrderQty int ,
	ProductID int ,
	UnitPrice DECIMAL ,
	UnitPriceDiscount DECIMAL ,
	LineTotal  DECIMAL,
	rowguid STRING ,
	ModifiedDate datetime 
) ;

CREATE OR REPLACE TABLE Raw.SalesOrderHeader(
	SalesOrderID int ,
	RevisionNumber int ,
	OrderDate datetime ,
	DueDate datetime ,
	ShipDate datetime NULL,
	Status int ,
	OnlineOrderFlag STRING ,
	SalesOrderNumber  STRING,
	PurchaseOrderNumber STRING NULL,
	AccountNumber STRING NULL,
	CustomerID int ,
	ShipToAddressID int NULL,
	BillToAddressID int NULL,
	ShipMethod STRING ,
	CreditCardApprovalCode STRING NULL,
	SubTotal DECIMAL ,
	TaxAmt DECIMAL ,
	Freight DECIMAL ,
	TotalDue  DECIMAL,
	Comment STRING NULL,
	rowguid STRING ,
	ModifiedDate datetime 
);
```
This has set up the raw tables for us to land data into, as well as some stored procedures we’ll use later in the quickstart.

The result should look like this, with tables and Schemas: 
![](assets/recent_purchases.png)

<!-- ------------------------ -->
## Set Up Azure SQL with AdventureWorks data
Duration: 5

Now we need to set up our Azure SQL instance.  When we create it we can include a sample Adventure Works dataset, this will represent our transactional sales database.

Create Service > Azure SQL > SQL Databases, Single Database
Database Name: ADFdemo
Server (Select create new): Give a unique server name, enable SQL authentication for this quickstart and enter an admin login and password. Go to Networking, Connectivity method select Public Endpoint, select yes for both Allow Azure Services and Add Current client IP.
Back
No changes in Networking or Security
Under Additional Settings, Use Existing Data: Select Sample
Create


![](assets/SQL.png)

<!-- ------------------------ -->
## Set Up ADF Workspace
Duration: 10

Head back to the azure marketplace and search for Data Factory
Give it a name and create with the default settings

![](assets/ManagedID.png)

<!-- ------------------------ -->
## Set up Container for staging
Duration: 5

Behind the scenes, ADF will use blob storage to stage data as it is moved.  So we need to have a blob storage container available.

From the Marketplace, search for Storage Account and create.
Give the Account a unique name
Keep all the default settings the same and Create
(Note: We are leaving the Networking open to public access for this quickstart, be sure to follow your organization's security best practices for non-demo projects)

Once created select Go to Resource
On the left select Containers
Add a Container named adfdemo

![](assets/Containers.png)

You’ll need to generate a SAS token for ADF to access the container.
On the left panel select Shared Access Signature
Ensure all resource types are available
Make the expiration End date long enough to finish the quickstart
Generate SAS and connection strong, then copy out the SAS token
(Note: Be sure to save it or leave this tab open, you won’t be able to get back to the token)

![](assets/SAS.png)

<!-- ------------------------ -->
## Configure the Linked Services
Duration: 10

Now you want to get into the ADF Studio.  Go to the ADF resource you created and click Launch Studio from the Overview tab.  This will open up the Data Factory Studio.

On the Left panel, click on the Manage tab, and then linked services.
![](assets/LinkedServices.png)

Linked Services act as the connection strings to any data sources or destinations you want to interact with. In this case we want to set up services for Azure SQL, Snowflake, and Blob storage.

Click Create Linked Services > Select Azure SQL Database > Continue
Name it, select all the subscription information for you Azure SQL database. Enter your SQL authentication username and password setup previously. Test connection and create.

Click Create Linked Services > Select Azure Blob Storage> Continue
Set Authentication type to SAS URI and enter the information created in previous steps.
The URL should be just the base URL: such as https://tolottiadfdemo.blob.core.windows.net/

Click Create Linked Services > Select Snowflake > Continue
Fill out the details for your account, note the format of the account name
The database and warehouse are both ADFDEMO

![](assets/LinkedServices2.png)

<!-- ------------------------ -->
## Create source & sink datasets
Duration: 15

Next you need to create datasets, these map the data inside the linked services.  In this case we’ll need to setup 5 source datasets for the Azure SQL tables, and 5 sink datasets for the Snowflake tables.

Navigate to Author, under the three dot menu on datasets select new dataset. Select Azure SQL database,, name it AzureSQL_Product and enter your linked server to azure SQL. 
Then set the table name to SalesLT.Product.
Repeat this process for the following:
AzureSQL_ProductCategory
AzureSQL_Customer
AzureSQL_SalesOrderHeader
AzureSQL_SalesOrderDetail

Now you want to setup the Sink datasets in snowflake.
Again create a new dataset, but this time select Snowflake. Name the dataset Snowflake_Product. Set the linked service to the Snowflake one you created.  And set the tablename to Raw.Product.
Again repeat this process for the following:
Snowflake_ProductCategory
Snowflake_Customer
Snowflake_SalesOrder

![](assets/.png)

<!-- ------------------------ -->
## Create the Pipeline
Duration: 20

Now it’s time to setup the pipeline, this is the object that will control the flow of the data.

## Copy Data

Under Move and transform, select a copy data activity. Copy data is the ELT option, it will move data from source to sink without any changes.
Name the CopyData as Product. 
Under the Source tab, select AzureSql_Product
Under the Sink tab, select Snowflake_Product. In the pre-copy script enter “Truncate table Raw.Product;” This will clear what's in the raw staging in snowflake each time data is loaded.
Under the Settings tab, check enable staging and set the Staging account to the blob storage set up previously

You can copy and paste the Activity to create two more Copy Data activities.
For the first, update the name to ProductCategory, and update the source and sink to the product category tables. Update the Sink truncate command to Raw.ProductCategory
For the second, do the same with Customer

![](assets/Pipelines.png)

## Data Flow

Now add a Data Flow Activity. Data Flows are a traditional ETL task. You can perform transformations on the data in the middle of the data movement.  If you are familiar with SSIS, data flows have similar functionality. In this case we are going to merge the Sales Order Header and Detail into a single table in Snowflake.

Name the activity SalesOrders
Under Settings select New Data flow

Under the Properties set the Name to SalesOrder DataFlow

Add a Source.  Name the output stream name SalesOrderHeader and Select the dataset as AzureSQL_SalesOrderHeader.  Under projection click Import projection to get the field names.

Add a second source. Name the output stream name SalesOrderDetail and Select the dataset as AzureSQL_SalesOrderDetail.  Under projection click Import projection to get the field names.

Select the small + to the right of the SalesOrderHeader task, and add Join.
Set the left stream to SalesOrderHeader, and the right to SalesOrderDetail
Under join conditions set both the left and right to SalesOrderID

Now click the + and add in a select task.  Since there are some columns in both tables with the same name, the skip duplicate input columns will just use the SalesOrderHeader columns.

And then select + and add a sink.  Name it Snowflake, set the dataset to Snowflake_SalesOrder. Under mapping uncheck auto mapping so it uses the fields from the select step.

![](assets/DataFlows.png)

## Script Tasks

In order to push compute to Snowflake, you can add in script activities to call queries or stored procedures. 
Back in the pipeline, under the general activities, add in a script activity.  Name the activity Update CustomerOrders, under settings add in a query for CALL Analytics.InsertCustomerOrders();

Now orchestrate the order of execution by connecting activities with the success connector.

![](assets/Debug.png)

By clicking the validate and debug you can perform a test run of the entire pipeline. And validate the tables have data in Snowflake.

<!-- ------------------------ -->
## Triggers and Monitors
Duration: 5

ADF is designed to be an automated pipeline orchestrator. 

At the top of the pipeline click Add trigger, and New/Edit
Set recurrence to Every 1 Day
Set the time to whatever works best for your testing

![](assets/Triggers.png)

Now publish all objects created by clicking on publish all at the top.

Once the trigger has activated and the pipeline is running, you can monitor the progress of all runs in the monitor tab on the far left.

![](assets/Monitor.png)

<!-- ------------------------ -->
## Conclusion and Additional Considerations
Duration: 5

This quickstart is just that, a quick way to get you started with ADF and Snowflake. You will want to consider the additional items below for enterprise-grade workloads:
- Review the [official documentation](https://learn.microsoft.com/en-us/azure/data-factory/connector-snowflake?tabs=data-factory) for any updates on capabilities.
- Check this [documentation](https://learn.microsoft.com/en-us/azure/data-factory/connector-troubleshoot-snowflake) for troubleshooting common errors.
- [Learn](https://community.snowflake.com/s/article/How-to-set-up-a-managed-private-endpoint-from-Azure-Data-Factory-or-Synapse-to-Snowflake) about private managed endpoints with ADF.
- Options for [Key-Pair authentication](https://medium.com/snowflake/azure-data-factory-connecting-to-snowflake-using-keypair-authentication-906000506345)


### What We covered
- How to deploy an Azure SQL with Adventure Works sample data
- Setup an Azure Data Factory pipeline, with linked services and datasets
- Utilize Copy Data, Data Flow, and Script activities using both SQL and SnowPark Python within ADF

If you have any questions, reach out to your Snowflake account team!