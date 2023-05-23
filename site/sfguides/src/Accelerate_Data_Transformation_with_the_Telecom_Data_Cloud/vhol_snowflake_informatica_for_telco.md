author: 
id: Accelerate_Data_Transformation_with_the_Telecom_Data_Cloud
summary: This is a guide for getting started with Data Integration using Informatica Data Management Cloud
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Data Integration, ETL, ELT, PDO, Informatica

# Accelerate Data Transformation with the Telecom Data Cloud and Informatica

<!-- ------------------------ -->

## Overview
Duration: 2

This quickstart will guide you through the steps to use the Informatica Intelligent Cloud Services Accelerator for Snowflake to create an Informatica Intelligent Data Management Cloud (IDMC) organization, which provides free data processing of up to one billion records per month.  You will then learn how to build a data integration mapping and mapping task or data pipeline using Informatica's Data Integration.

The Informatica IDMC provides complete, comprehensive cloud-native and AI-powered data management capabilities, including data catalog, data integration, API and application integration, data prep, data quality, master data management, and a data marketplace, on a foundation of governance and privacy. Informatica IDMC is powered by our AI and machine learning (ML) engine, CLAIRE, optimized for intelligence and automation, and is built on a modern, elastic, serverless microservices stack that connects data consumers to the data sources they need. It enables you to intelligently discover and understand all the data within and outside the enterprise, access and ingest all types of data wherever and whenever you want, curate and prepare data in a self-service fashion so that it is fit for use, and deliver an authoritative and trusted single view of all your data. Informatica IDMC is the single and most complete platform you will ever need for cloud-native data management.

IDMC Data Integration allows you to load source data from databases, applications, and data files in the cloud or on-premises into Snowflake. Data Integration supports many transformations that can be used to transform and enrich the source data. In addition, pushdown optimization (PDO) can be utilized for some transformations and functions to take advantage of Snowflake compute resources for data processing.

In this lab, you will create a mapping to read two delimited files (loyalty and mobile traffic) from S3, join the files, perform an aggregation to create a count and total, and write the results into a new table in Snowflake. Then in the mapping task, you will turn on pushdown optimization to enable the processing to occur in Snowflake.

JSON (JavaScript Object Notation) is a text-based data format commonly used between servers and web applications and web-connected devices.  Because it is text-based, it is readable by both humans and machines.  JSON semi-structured data can be stored in Snowflake variant column alongside relational data.  In IDMC, the hierarchy parser transformation parses and transforms hierarchy data to relational data.

In this lab, you will also use additinal traffic informations data to create a hierarchical schema, then use it in a mapping to parse and transform the JSON weather forecast data, join them, add an expression to convert the temperature, and then write the data to a new table.

### Prerequisites
- Familiarity with Snowflake
- Familiarity with data integration (ETL) concepts
- Familiarity with AWS S3
- Familiarity with hiearchical data

### What You'll Learn
By the end of this guide, you'll learn:
- How to create an IDMC organization from Snowflake Partner Connect
- How to view the Snowflake connection configuration in IDMC
- How to configure an S3 connection.
- How to build a data integration mapping to read S3 files and load into Snowflake.
- How to turn on Pushdown Optimization (PDO) or ELT in a mapping task to use Snowflake's warehouse to process the data integration mapping.
- How to verify PDO is successfully enabled.
- How to configure a hierarchical schema
- How to build a data integration mapping to flatten JSON data into relational data
- All of the above without writing a single line of code.

### What You'll Need 
- A Snowflake account with access to the ACCOUNTADMIN role
- An email address for IDMC registration
- Configured Snowflake connection in IDMC org if your org will not be registered from Partner Connect.  [Documentation on how to create a Snowflake connection](https://docs.informatica.com/integration-cloud/data-integration-connectors/current-version/snowflake-data-cloud-connector/connections-for-snowflake-data-cloud/snowflake-data-cloud-connection-properties/standard-authentication.html)
- AWS S3 bucket access and credential

### What You'll Build
- An Informatica Data Management Cloud organization
- An S3 connection
- A data integration mapping to load S3 files into Snowflake
- A mapping task to use PDO for processing the data integration mapping
- A hierarchical schema
- A data integration mapping to parse JSON weather data and flatten it.

<!-- ------------------------ -->

## Prepare Your Lab Environment

Duration: 5

![Warning](assets/v_warning1.png) <BR>
<BR>
If you already have an Informatica Data Management Cloud (IDMC) account make sure to log off and close the browser.

If you haven't already, register for a [Snowflake free 30-day trial](https://trial.snowflake.com), right click to open in new tab avoiding to change current lab page.  You can also use an existing Snowflake account **as long as you have ACCOUNTADMIN access in that account**.

Please select a region which is physically closest to you, and select the Enterprise edition (that is the default choice) so you can leverage some advanced capabilities that are not available in the Standard Edition.  

After registering, you will receive an email with an activation link and your Snowflake account URL. Bookmark this URL for easy, future access. After activation, you will create a user name and password. Write down these credentials.

Resize your browser window, so that you can view this guide and your web browser side-by-side and follow the lab instructions. If possible, use a secondary display dedicated to the lab guide.

<!-- ------------------------ -->

## Create the IDMC Organization
Duration: 3



### Step 1 
1. Login to **Snowflake Snowsight**.
2. Switch role to **ACCOUNTADMIN**.
3. Click **Admin > Partner Connect**.
4. Search for **Informatica**.
5. Click **Informatica** tile.
6. Be sure to select **Informatica** and NOT **Informatica Data Loader** (this allows ingest data with a wizard-based approach without transformations)
![PartnerConnect](assets/v_partnerconnect.png)

### Step 2
1. Note the objects that will be created in Snowflake.
2. Click **Connect**.<BR>
![Connect](assets/Lab1_Picture2.png)

### Step 3
1. Click **Activate**.<BR>
![Activate](assets/Lab1_Picture3.png)

### Step 4
1. Fill in the Informatica registration form.
2. **Uncheck** Use my email address as my username box (this will prenvent account failure creation if you already have an IDMC account)
3. Select **Europe** for your Data Center.
4. Click **Submit**.<BR>
![Register](assets/v_idmc_account_creation.png)

5. Upon successful registration, you will receive an email with the subject line: **Thanks for signing up for the Informatica Intelligent Cloud Services Accelerator for Snowflake**.
![Email](assets/Lab1_Picture4.1.png)


### Step 5
1. Please read through Knowledge Base materials and demo recording for more information.
2. From below page, click the **region** you selected in step 4 to go to the **Login** page.
![Workshop](assets/Lab1_Picture5.png)

### Step 6
1. Enter your **username** and **password**.
2. Click **Log In**.<BR>
![Login](assets/Lab1_Picture6.png)

### Step 7
1. The first time logging in, you will be prompted to enter a security **question** and **answer**.  Fill them in.
2. Click **Log In**.<BR>
![SecurityQ](assets/Lab1_Picture7.png)

3. The Sample Use-Cases walkthrough page shows up.  Click "Don't show this again".
![Walkthrough](assets/Lab1_Picture7.1.png)

4. To re-visit the Sample Use-Cases walkthrough page, click **?** at the top right and choose **Walkthroughs**.  Feel free to go through the sample use-cases walkthrough at your convenience.
![OpenWalkthrough](assets/Lab1_Picture7.2.png)

5. In the next section, we will look at the Snowflake connection that was created by the registration process.

<!-- ------------------------ -->
## Review the Snowflake Connection
Duration: 2

The Snowflake connection is automatically configured in the IDMC organization when you create the organization through Snowflake Partner Connect.  Let's take a look at the connection.

### Step 1
1. Click **Administrator** in the service selector page.
![Administrator](assets/Lab1_Picture8.png)

2. Click **Connections** on the left panel.
![Connections](assets/v_snowflake_connection.png)

3. Click the Snowflake connection that was created by the registration process.  Your connection name will have Snowflake followed by your Snowflake account name.

4. Following is a screenshot of a Snowflake connection.  Note the properties i.e. Snowflake objects under the **Connection Section**.
![SnowflakeConnection](assets/v_snowflake_test_connection.png)

5. Click **Test Connection** button and you should see a successful test notification.

6. In the next section, we will review the Snowflake objects that were created by Partner Connect.

<!-- ------------------------ -->
## Review the Snowflake Objects
Duration: 2

As described in Step 2 of **Create IDMC Organization** section, a set of Snowflake objects were created.  Those objects are Database, Warehouse, System User, and System Role.

Let's take a look at those objects.

### Step 1
1. Go to **Worksheets** in Snowflake, create a new worksheet and perform the following queries.
![Worksheet_Creation](assets/v_creation_worksheet.png)
Note : You will have several SQL statements in the worksheet, position your cursor on the query to execute.


### Step 2
1. Run the following query to show the database object.
```SQL 
show databases like 'PC_INF%';
```
![Database](assets/v_snowflake_db.png)

2. Run the following query to show the warehouse object.
```SQL
show warehouses like 'PC_INF%';
```
![Warehouse](assets/v_snowflake_wh.png)

3. Run the following query to show the user object.
```SQL
show users like 'PC_INF%';
```
![User](assets/v_snowflake_users.png)

4. Run the following query to show the role object.
```SQL
show roles like 'PC_INF%';
```
![Role](assets/v_snowflake_roles.png)

5. Now we're ready to start building our data integration pipeline.

<!-- ------------------------ -->
## Configure an AWS S3 connection
Duration: 5

An AWS S3 connection is required to access and read an AWS S3 bucket.  Follow configuration steps below to create the S3 connection.

Note that the S3 connection requires that the S3 objects be encrypted.  If you are doing this lab live, you will be given an Access Key and Secret Key to use.  Alternatively, you can download the files at the end of this page and load them to your own S3 bucket.

### Step 1
1. Click **Connections** on the left panel.
2. Click **New Connection** button to create a new connection.
![NewConnection](assets/Lab2_Picture21.png)

### Step 2
1.	Enter **S3** in the Connection Name field.
2.	Select **Amazon S3 v2** from the Type dropdown field.
3.	Select **Informatica Cloud Hosted Agent** from the Runtime Environment dropdown field.  
4.	Enter your access key in the Access Key field.
5.	Enter your secret key in the Secret Key field.
6.	Enter S3 bucket name **dataforingestion-eu** in the Folder Path field. 
7.	Select your bucket's region from the Region Name dropdown field.
8.	Click **Test Connection** button.  If the configuration is correct, the page should display **The test for this connection was successful.** 
9.	Click **Save** button.
![S3Connection](assets/v_admin_s3_connection.png)
Reference: [AWS S3 V2 Connector Documentation](https://docs.informatica.com/integration-cloud/cloud-data-integration-connectors/current-version/amazon-s3-v2-connector/amazon-s3-v2-connections/amazon-s3-v2-connection-properties.html)

10. You should have an AWS S3 and Snowflake connections configured.
![S3andSnowflake](assets/v_list_of_connections.png)

### Step 3 (Alternative method for using your own S3 bucket)
1. Click to download the following files.<br>
  <button>
  [telco_info.csv](https://snowflake-corp-se-workshop.s3.us-west-1.amazonaws.com/VHOL_Snowflake_informatica_Telco/telco_info.csv)
  </button>
  <button>
  [loyalty_customers.csv](https://snowflake-corp-se-workshop.s3.us-west-1.amazonaws.com/VHOL_Snowflake_informatica_Telco/loyalty_customers.csv)
  </button>
  <button>
  [additional_telco_info.json](https://snowflake-corp-se-workshop.s3.us-west-1.amazonaws.com/VHOL_Snowflake_informatica_Telco/additional_telco_info.json)
  </button>
2. This action is optional and not needed for this lab. The only purpose is if you want to use the files using own bucket later.
<!-- ------------------------ -->
## Create a Project Folder
Duration: 2

### Step 1
1. Click the Service Selector at the top left, then select **Data Integration** service.
![ServiceSelector](assets/Lab2_Picture24.png)

### Step 2
Let's create a project to store our mapping or assets.
1. Click **Explore** on the left panel.
2. Click **New Project** to create a new project.
![NewProject](assets/Lab2_Picture25.png)
3. Enter **Hands-on Lab** in the Name field.
4. Click **Save**.<BR>
![Save](assets/Lab2_Picture26.png)
5. Click **Hands-on Lab** project.
![HandsonLab](assets/Lab2_Picture27.png)

<!-- ------------------------ -->
## Load Data from AWS S3 into Snowflake using Pushdown Optimization (ELT)
Duration: 25

IDMC Data Integration allows you to load source data from databases, applications, and data files in the cloud or on-premises into Snowflake.  Data Integration supports many transformations that can be used to transform and enrich the source data.  In addition, pushdown optimization (PDO) can be utilized for some transformations and functions to take advantage of Snowflake compute resources for data processing.

In this lab, you will create a mapping to read two delimited files (loyalty_customer and telco_info) from S3, join the files, perform an aggregation to create a count and total, and write the results into a new table in Snowflake.  Then in the mapping task, you will turn on pushdown optimization to enable the processing to occur in Snowflake.

### Step 1
Create a new mapping
1. Click **New...**
2. Click **Mappings**
3. Select **Mapping**
4. Click **Create** <BR>
![NewMapping](assets/Lab2_Picture28.png)
5. Under properties, enter **m_S3_into_Snowflake_pushdown** in Name field.
6. Ensure that Location is **Hands-on Lab**. If not, click **Browse** and select it.
![Mapping](assets/v_mapping_creation.png)

### Step 2
Let's configure customers loyalty data source from S3.
1.	Click the **Source** transform in the mapping canvas to assign its properties.
2.	In the General tab, enter **src_S3_Customers_Loyalty** in the Name field.<BR>
![src1](assets/v_mapping_creation_src_1.png)
3.	In the Source tab, select **S3** in the Connection dropdown field.
4.	Click **Select** to select a source file.
![srcS3Orders](assets/v_mapping_creation_src1_select.png)
5.	Click on **dataforingestion-eu** S3 bucket.
6.	From the results on the right, select **loyalty_customers.csv** file.
7.	Click **OK**. <BR>
![srcS3Orders2](assets/v_mapping_creation_src_loyalty_customer.png)
8.	Click Format dropdown field and select **Flat**.
9.	Click **Formatting Options**.
![srcS3OrdersFormat](assets/v_mapping_creation_src_loyalty_customer_format.png)
10.	Enter a **semicolon** character in the delimiter field, remove **double-quote** for the Qualifier.
![srcS3CustLoyaltyFormat1](assets/v_mapping_creation_src_loyalty_customer_formatting.png)
11.	Click **Data Preview** to view the first 10 records.  
12.	Records should be separated by fields.
![srcS3CustLoyaltyFormat2](assets/v_mapping_creation_src_loyalty_customer_preview.png)
13.	Click **OK**.
14.	Click **Save** to save work in progress.

### Step 3
Now we will add the Lineitem file as another data source.  The steps are the same as the above Orders data source.

1.	From the transformation palette, drag **Source** transform and drop in the mapping canvas.
![srcS3newSource](assets/v_mapping_creation_src_telco_infos.png)
2.	Let's assign its properties.
3.	In the General tab, enter **src_S3_Telco_Info** in the Name field.
4.	In the Source tab, select **S3** in the Connection dropdown field.
5.	Click **Select** to select a source file.
6.	Click on **dataforingestion-eu** S3 bucket.
7.	From the results on the right, select **telco_info.csv** file.
8.	Click **OK**.
9.	Click Format dropdown field and select **Flat**.
10.	Click **Formatting Options**.
11.	Enter a **semicolon** character in the delimiter field, remove **double-quote** for the Qualifier.
12.	Click **Data Preview** to view the first 10 records.
13.	Records should be separated by fields.
14.	Click **OK**.
15.	Click **Save** to save work in progress.

### Step 4
Let's join the two data sources.

1.	From the transformation palette, drag the **Joiner** transform and drop it over the line between the src_S3_Customers_Loyalty source and target transforms.  The Joiner should now be linked to the Orders and target.  If not, manually link them.
2.	Click align icon to align transformations in the mapping canvas.
![joinertx](assets/v_mapping_creation_add_joiner.png)
3.	Click the plus icon above the Joiner to expand.  
4.	Link **src_S3_Telco_Info** to the Detail of Joiner transform.
![joinerdetail](assets/v_mapping_creation_master_detail.png)
5.	Let's assign the Joiner properties.
6.	In the General tab, enter **jnr_sources** in the Name field.
7.	In the Join Condition tab, click the plus icon to add a new condition.
8.	Select **PHONE_NUMBER** for Master and **MSISDN** for Detail.
![joinercondition](assets/v_last_jnr_screen.png)
9.	Click **Save** to save work in progress.


### Step 5
Let's add an expession transformation and add an new port.

1.	From the transformation palette, drag the **Expression** transform and drop it over the line between the jnr_sources source target transforms.
2.	Click align icon to align transformations in the mapping canvas.
![expnameadd](assets/v_mapping_jnr_add_expression.png)
3. In the General tab, enter **exp_add_port** in the Name field.
![expname](assets/v_mapping_jnr_expression_name.png)
4. Go to **expression** under General and click + icon on right to add Output Field
5.	Add the following field:
<br>	**o_grpby**
<br>
![expportdefintion](assets/v_mapping_jnr_expression_add_port.png)
6. Click **Configure** and enter the following in the Expression field.
![expportdefintion](assets/v_mapping_jnr_expression_configure.png)
```SQL
SUBSTR(EVENT_DATE,1,10)
```
7. Click **OK** <BR>
![expfinal](assets/v_mapping_jnr_expression_final_result.png).
8.	Click **Save** to save work in progress.

### Step 6
Now we will count the number of event types per day per phone number.

1.	From the transformation palette, select **Aggregator** transformation, drag and drop between the exp_add_port and Target in mapping canvas window.
2.	Click align icon to align transformations in the mapping canvas.
![aggr](assets/v_mapping_add_aggragator.png)
3.	Let's assign the properties.
4.	In the General tab, enter **agg_by_date** in the Name field.
5.	In the Group By tab, click the plus icon to add new fields.
6.	Add the following fields:
<br>	**o_grpby**
<br>	**PHONE_NUMBER**

7.	When completed, the Group By tab properties should look like this:
![groupby](assets/v_mapping_add_aggragator_add_groupbyports.png)
8.	In the Aggregate tab, click the plus icon to add a new field.
9.	Enter **o_count** in the Name field.
10.	Select **integer** in the Type dropdown field.
11.	Enter **10** in the Precision field.
12.	Enter **0** in the Scale field.
13.	Click **OK**.
14.	Click **Configure** to configure the expression.
15.	Enter **count(EVENT_DTTM)** in the Expression field. This function will count the number of event types per day per number. 
16.	Enter the following in the Expression field.  
```SQL
count(EVENT_DTTM)
````
17.	Click **Validate**.
18.	Click **OK**.
19.	When completed, your Expression tab properties should look like this:
![groupbycomplete](assets/v_mapping_add_aggragator_expression.png)
20.	Click **Save** to save work in progress.

### Step 7
Lastly the target table is going to be in Snowflake.

1.	Click **Target** to set a target properties.
2.	In the General tab, enter **tgt_Snowflake** in the Name field.
3.	In the Incoming Fields tab, select Named Fields
![target](assets/v_mapping_tgt_named_fields.png)
4.	Select below fields :
<br>	**o_count** 
<br>	**o_grpby**
<br>	**PHONE_NUMBER**
![target](assets/v_mapping_tgt_named_fields_selected.png)
5.	Go to **Rename Fields** tab and rename fields as below
<br> 	Rename **o_count** as **C_TOTAL**
<br>    Rename **o_grpby** as **C_DATE**
![targetrenamedfields](assets/v_mapping_tgt_named_fields_renamed.png)
6. Click **OK**
7.	When completed, the Incoming Fields tab should look like this:
![targetfields](assets/v_mapping_tgt_named_fields_final_view.png)
8.	In the target tab, select **snowflake** connection and click **Select** to select target table.
![targetcomplete](assets/Lab2_Picture58.png)
9.	Select **Create New at Runtime** for Target Object.
10.	Enter **T_TELCO_AGG** in Object Name field.
11.	Enter **TABLE** in the TableType field.
12.	Enter **PC_INFORMATICA_DB/PUBLIC** in Path field.
![targettable](assets/v_mapping_target_create_at_runtime.png)
13.	The Target Fields tab should look like this:
![targetfields](assets/v_mct_hierarchical_target_fields_screen.png)
14.	The Field Mapping tab should look like this:
![targetcomplete](assets/v_mct_hierarchical_target_fields_mapping.png)
15. Run the mapping by selecting your mapping and click **run** button on top right
![runmapping](assets/v_mapping_run.png)
16. Click **My Jobs** to monitor the job execution. <br>
![myjobs1](assets/v_mapping_my_jobs.png)
17. The monitor tab should look like this :
![myjobs2](assets/v_mapping_monitor.png)



## Configure Pushdown Optimization and Execute the Mapping Task
Duration: 10

Let's configure Pushdown Optimization (PDO) in the Mapping Task and execute it.

### Step 1

1.	Click **Save** to save and validate the mapping.
2.	Click 3 dots icon to create a **Mapping task** from the mapping <br>
![mct](assets/v_mct_creation.png)
<br>
3.	Select **New Mapping Task** 
<br>
![mctnew](assets/Lab2_Picture63.png)
4.	In the New mapping task window, enter **mct_S3_into_Snowflake_pushdown** in the Name field.
5.	Select **Hands-on Lab** for Location.
6.	Select **Informatica Cloud Hosted Agent** for Runtime Environment.
7.	Click **Next**. <BR>
![mctdef](assets/v_mct_creation1.png) 
8.	Scroll down to the Pushdown Optimization section.
9.	Select **Full** from the Pushdown Optimization dropdown list.
10.	Click **Finish**. <BR>
![mct](assets/v_mct_creation2.png)
11.	Click **Run** to execute the mapping task.
![mctrun](assets/v_mct_run.png)

### Step 2
View job execution progress.

1.	Click **My Jobs** to monitor the job execution. <br>
![job](assets/Lab2_Picture67.png)
2.	Click **Refresh** icon when the “Updates available” message appears.
3.	When the job is completed, make sure Status is **Success**.
![success](assets/v_mct_status.png)
4.	Drill down to the completed job by clicking the instance name.  Then click Download Session Log to view the log.  
![download](assets/v_mct_status1.png)
5. In the log you will see a message indicating that Pushdown Optimization is successfully enabled. 
![pdosuccess](assets/v_mct_pdo_enabled.png)
6.	You will also see an INSERT SQL statement that Informatica generated for execution in Snowflake.

```SQL
INSERT INTO "PC_INFORMATICA_DB"."PUBLIC"."T_TELCO_AGG"("C_TOTAL","C_DATE","PHONE_NUMBER")     SELECT t5.t5c4::NUMBER(18,0),            t5.t5c3,            t5.PHONE_NUMBER     FROM (         SELECT T_T3.PHONE_NUMBER,                SUBSTR(T_T1.EVENT_DATE, 1, 10)::VARCHAR(10),                T_T3.PHONE_NUMBER as c0,                SUBSTR(T_T1.EVENT_DATE, 1, 10)::VARCHAR(10) as c1,                COUNT(T_T1.EVENT_DTTM)::NUMBER(10,0)         FROM (             SELECT T_T0."LOOKUP_ID"::VARCHAR(256),                    T_T0."HOME_NETWORK_TAP_CODE"::VARCHAR(256),                    T_T0."SERVING_NETWORK_TAP_CODE"::VARCHAR(256),                    T_T0."IMSI_PREFIX"::VARCHAR(256),                    T_T0."IMEI_PREFIX"::VARCHAR(256),                    T_T0."HOME_NETWORK_NAME"::VARCHAR(256),                    T_T0."HOME_NETWORK_COUNTRY"::VARCHAR(256),                    T_T0."BID_SERVING_NETWORK"::VARCHAR(256),                    T_T0."BID_DESCRIPTION"::VARCHAR(256),                    T_T0."SERVICE_CATEGORY"::VARCHAR(256),                    T_T0."CALL_EVENT_DESCRIPTION"::VARCHAR(256),                    T_T0."ORIG_ID"::VARCHAR(256),                    T_T0."EVENT_DATE"::VARCHAR(256),                    T_T0."IMSI_SUFFIX"::VARCHAR(256),                    T_T0."IMEI_SUFFIX"::VARCHAR(256),                    T_T0."LOCATION_AREA_CODE"::VARCHAR(256),                    T_T0."CELL_ID"::VARCHAR(256),                    T_T0."CHARGED_UNITS"::VARCHAR(256),                    T_T0."MSISDN"::VARCHAR(256),                    T_T0."EVENT_DTTM"::VARCHAR(256)             FROM "PC_INFORMATICA_DB"."PUBLIC"."T_TELCO_AGG_1672851099992_261294f8-6d21-4275-aba1-cd32e54534da"              AS T_T0)              AS T_T1(LOOKUP_ID, HOME_NETWORK_TAP_CODE, SERVING_NETWORK_TAP_CODE, IMSI_PREFIX, IMEI_PREFIX, HOME_NETWORK_NAME, HOME_NETWORK_COUNTRY, BID_SERVING_NETWORK, BID_DESCRIPTION, SERVICE_CATEGORY, CALL_EVENT_DESCRIPTION, ORIG_ID, EVENT_DATE, IMSI_SUFFIX, IMEI_SUFFIX, LOCATION_AREA_CODE, CELL_ID, CHARGED_UNITS, MSISDN, EVENT_DTTM)         Join (             SELECT T_T2."ID"::VARCHAR(256),                    T_T2."FIRST_NAME"::VARCHAR(256),                    T_T2."LAST_NAME"::VARCHAR(256),                    T_T2."EMAIL"::VARCHAR(256),                    T_T2."GENDER"::VARCHAR(256),                    T_T2."STATUS"::VARCHAR(256),                    T_T2."ADDRESS"::VARCHAR(256),                    T_T2."PHONE_NUMBER"::VARCHAR(256),                    T_T2."POINTS"::VARCHAR(256)             FROM "PC_INFORMATICA_DB"."PUBLIC"."T_TELCO_AGG_1672851099885_f3e780ff-b0db-423f-98fc-c86871635698"              AS T_T2)              AS T_T3(ID, FIRST_NAME, LAST_NAME, EMAIL, GENDER, STATUS, ADDRESS, PHONE_NUMBER, POINTS)          ON T_T3.PHONE_NUMBER = T_T1.MSISDN         GROUP BY 1, 2)      AS t5(PHONE_NUMBER, t5c1, PHONE_NUMBER0, t5c3, t5c4) ]
```

### Step 3
1.	In Snowflake Snowsight, you should see 438485 rows inserted in the **T_TELCO_AGG** table.
![snowflake](assets/v_snowflake_results.png)
2. Click  
3. You can also view the Informatica-generated INSERT statement that was executed in the Snowflake query history.
4. Click Home button
![snowhomeButton](assets/v_m_home_directory.png) <br>
5.  Go to Activity --> **Query History and selecting**, select "All" or "PC_INFORMATICA_USER" as user.
![snowflakehistory1](assets/v_last_snowflake_history.png) <br>
![snowflakehistory2](assets/v_snowflake_history.png)

<!-- ------------------------ -->
## Transform Semi-Structured JSON Data
Duration: 3

### Step 1 
JSON (JavaScript Object Notation) is a text-based data format commonly used between servers and web applications and web-connected devices.  Because it is text-based, it is readable by both humans and machines.  JSON semi-structured data can be stored in Snowflake variant column alongside relational data.  In IDMC, the hierarchy parser transformation parses and transforms hierarchy data to relational data.

In this section, we'll load some JSON-formatted telco data into the PC_INFORMATICA_DB database.  You will then use it to create a hierarchical schema, then use it in a mapping to parse and transform, join them, add an expression to convert the timestamp, then write to a new table.

For this step we will use standard Snowflake SQL commands to create a table with a Snowflake **VARIANT** column.

1. In Snowflake **Snowsight**, execute all of the following SQL statements.

```SQL
-- Set the correct ROLE, WAREHOUSE, and SCHEMA
use role PC_INFORMATICA_ROLE;
use warehouse PC_INFORMATICA_WH;
use schema PC_INFORMATICA_DB.PUBLIC;

-- Create the table
create or replace table pc_informatica_db.public.T_VHOL_JSON (
  v variant);

copy into T_VHOL_JSON
	  from s3://snowflake-corp-se-workshop/VHOL_Snowflake_informatica_Telco/additional_telco_info.json
	  FILE_FORMAT = ( TYPE = JSON);
	  
```
![copytable](assets/v_last_insert_snowflake_sql.png)

## Configure Hierarchical Schema
Duration: 15

### Step 1
Copy JSON data from the Snowflake table and save it locally in your computer.

1.	Go to Worksheets, execute the following query:
```SQL
select * from pc_informatica_db.public.T_VHOL_JSON;
```
2. Click data in column V in the result panel.
3. Click Copy icon.
![daily14total](assets/v_m_hierarchical_copy_file.png)
4. Save the copied JSON data in a text file locally on your computer and name it **additional_data.json**.

### Step 2
Create a Hierarchical Schema in IDMC.

1.	In IDMC, go to **Data Integration** service.
2.  Click **New**.
3.	Click **Components**.
4.	Select **Hierarchical Schema** and click **Create**.
![Hschema](assets/Lab3_Picture3.png)
5.	Enter **hs_vhol_data** in the Name field.
6.	Select **Hands-on Lab** in the Location field if not already filled in.
7.	Click **Upload**.
![upload](assets/v_hs_creation.png)
8.	Click **Choose File** and select the JSON file you saved in Step 1 above.
9.	Click **Validate** and you should see **"JSON Sample is Valid"** message.
10.	Click **OK**.
![upload](assets/v_hs_validation.png)
11.	Click Save.
![save](assets/v_hs_save.png)

## Create a Mapping to Read Hierarchical Data
Duration: 15

Create a mapping to read from the t_vhol_json table, use hierarchy parser to parse the JSON data.

### Step 1
1.	Click **New**
2.	Click **Mappings**.
3.	Select **Mapping**.
4.	Click **Create**.
5.	Under properties, enter **m_parse_json_data** in Name field.
6.	Ensure Location is **Hands-on Lab**. If not, click **Browse** and select it.
![newmapping](assets/v_last_parse_hierarchical.png)

### Step 2
Let's configure the data source from Snowflake. 

1.	Click **Source** transform in the mapping canvas to assign its properties.
2.	In General tab, enter **src_vhol_json** in the Name field.
3.	In Source tab, select Snowflake_[account name] in the Connection dropdown field.
4.	Click Select **T_VHOL_JSON** to select the source table/object.
5.	In Select Source Object window, scroll down to find **PC_INFORMATICA_DB** and click it.  Then click **PUBLIC** schema.
6.	Select **T_VHOL_JSON** in the tables list on the right pane.
7.	Click **OK**.
![newmapping](assets/v_hs_mapping_source_select.png)
8.	Click **Save** to save work in progress.

### Step 3
Add HierarchyParser transform and configure it. 

1.	Drag and drop **Hierarchy Parser** transform on to the canvas.
![Hparser](assets/v_hs_mapping_bring_parser.png)
2.	In General tab, enter **hp_parse_JSON** in the Name field.
3.	In Input Settings tab, click Select and select the **hs_vhol_data** hierarchical schema.  Click **OK**.
![Hparserjson](assets/v_hs_mapping_parser_inputsettings.png)
4.	Select the link from **src_vhol_json** to **Target** and click delete icon.
5.	Link **src_vhol_json** to **hp_parse_JSON**.  
![link](assets/v_hs_mapping_src_to_parser.png)
6.	Select the hp_parse_JSON transformation, then, in Input Field Selection tab, drag and drop **V** field from Incoming Fields to Input field in Hierarchical Schema Input Fields
![drop](assets/v_hs_mapping_map.png)
7.	In Field Mapping tab, expand root element by clicking the triangle icon or expand/contract icon.
8.	Click rootArray and select **Map all descendants**
![drop1](assets/v_hs_mapping_map_descendants.png)
9. you should see 
![drop2](assets/v_hs_mappig_all_descendants2.png)
9.	Click **Save** to save work in progress.

### Step 4
Add a Joiner transform to link root and data relational field groups and configure it. 

1.	Drag and drop **Joiner** transform on the canvas.
3.	In the General tab, enter **jnr_hierarchical_data** in the Name field.
2.	Link **hp_parse_JSON** to the **Master** in Joiner transform.  
3.	Select Output Group window appears.  Select **root** and click **OK**.
![root](assets/v_hs_mapping_jnr_master.png)
4.	Link **hp_parse_JSON** again but this time to the **Detail** in Joiner transform.
5.	Select **data** in Output Group and click **OK**.
![data](assets/v_hs_mapping_jnr_master_detail.png)
6.	In Join Condition tab, click add icon.
7.	Select **PK_root (bigint)** in Master column and **FK_root (bigint)** in the Detail.
![condition](assets/v_hs_mapping_jnr_condition.png)
8.	In Advanced tab, select **Sorted Input**.
![sort](assets/v_hs_mapping_jnr_sorted_input.png)
9.	Click **Save** to save work in progress.


### Step 5
Finally, let's configure the Target. 

1.	Link **jnr_hierarchical_data** to Target.
2.	In the General tab, enter **tgt_Snowflake_Telco_Info** in the Name field.
3.	In the Incoming Fields tab, change All Fields to **Named Fields** by clicking on that field.
4.	Then click **Configure** to select fields.  Select the fields that were created in the **jnr_hierarchical_data** expression transform.
![targetincomingfields](assets/v_hs_mapping_selecting_fields.png)
5. Go to Rename Fields tab and rename selected fields
![targetrenamingfields](assets/v_hs_mapping_renaming_fields.png)
6.	In the Target tab, select **Snowflake** connection.
7.	Click **Select** to select a table.
8.	In the Target Object window, check **Create New at Runtime**.
9.	Enter **T_TELCO_INFO** in Object Name field.
10.	Enter **TABLE** in TableType.
11.	Enter **PC_INFORMATICA_DB/PUBLIC** in Path.
12.	Click **OK**.
![target](assets/v_hs_mapping_tgt_snowflake.png)
![field mapping](assets/v_hs_mapping_tgt_snowflake_fields.png)
13.	Click **Save**.


## Create and Execute a Mapping Task
Duration: 5

### Step 1

Let's configure a Mapping Task and execute it.

1.	Click 3 dots to create Mapping task from the mapping
2.	Select **New Mapping Task**
<br>
![newmct](assets/Lab3_Picture28.png) <br>
3.	In the New mapping task window, enter **mct_parse_json_data** in the Name field.
4.	Select **Hands-on Lab** for Location.
5.	Select **Informatica Cloud Hosted Agent** for Runtime Environment.
6.	Click **Finish**.
![newmct](assets/v_mct_hierarchical_screen.png)
7.	Click Run to execute the mapping task.

### Step 2
Validate job execution result.

1.	Click **My Jobs** to monitor the job execution.
2.	Click **Refresh** icon when Updates available message appears.
3.	When the job is completed, make sure the Status is **Success**.
4.	**140** rows were processed.
![864rows](assets/v_hs_mct_status.png)
5.	In the Snowflake table preview, there are 140 rows as well.  Notice that the columns label are in the order as configured in the Expression transform.
![864rowsinSF](assets/v_hs_snwflake_results.png)

<!-- ------------------------ -->

## Optional -  Create a Mapping to load additional data into aggragate table
Duration: 15

Optionally you can load data T_TELCO_INFO into T_TELCO_AGG and review results.


### Steps
1.	Click **New**
2.	Click **Mappings**.
3.	Select **Mapping**.
4.	Click **Create**.
5.	Under properties, enter **m_add_data_to_aggregate** in Name field.
6.	Ensure Location is **Hands-on Lab**. If not, click **Browse** and select it.
7.	Click the **Source** transform in the mapping canvas to assign its properties.
8.	In the General tab, enter **src_telco_info** in the Name field
9.	In the Source tab, select **snowflake** connection and **T_TELCO_INFO** as Object
10.	From the transformation palette, drag the **Expression** transform and drop it over the line between the jnr_sources source target transforms.
11.	Click align icon to align transformations in the mapping canvas.
12. In the General tab, enter **exp_add_port** in the Name field.
13. Go to expression and click + icon on right as an Output Field
14.	Add the following field **o_grpby**
15. Enter the following in the Expression field **SUBSTR(EVENT_DTTM,1,10)**
16.	From the transformation palette, select **Aggregator** transformation, drag and drop between the exp_add_port and Target in mapping canvas window..
17.	In the General tab, enter **agg_by_date** in the Name field.
18.	In the Group By tab, click the plus icon to add new fields.
19.	Add the following fields:
<br>	**o_grpby**
<br>	**MSISDN**
19.	In the Aggregate tab, click the plus icon to add a new field.
20.	Enter **o_count** in the Name field.
21.	Select **integer** in the Type dropdown field.
22.	Enter **10** in the Precision field.
23.	Enter **0** in the Scale field.
24.	Click **OK**.
25.	Click **Configure** to configure the expression.
26.	Enter **count(EVENT_DTTM)** in the Expression field. This function will count the number of event types per day per number. 
27.	Click **Target** to set a target properties.
30.	In the General tab, enter **tgt_agg_snowflake** in the Name field.
31. select the **snowflake** connection in the target 
32.	Select **Existing** for Target Object.
33.	Select **PC_INFORMATICA_DB/PUBLIC/T_TELCO_AGG** in Object Name field.
![targettableExisting](assets/v_optional_existing.png)
34.	The Target Fields tab should look like this:
![targetfields](assets/v_opt_tgt_fields.png)
35.	The Field Mapping tab should look like this:
![targetcomplete](assets/v_opt_field_mapping.png)
36. Create a mapping task **mct_add_data_to_aggregate**  and **run** it. 
37.	The  mapping task  should look like this:
![mctfinal](assets/v_optional_mapping_final_look.png)
38. In Snowflake Snowsight, you should see now 438619 rows  in the **T_TELCO_AGG** table.
![snowfinal](assets/v_optional_snow_results.png)



## Conclusion
Duration: 2

**Congratulations! You have successfully completed these Labs**

In this guide, you learned how to create a free IDMC organization, use Pushdown Optimization/ELT to load and transform mobile traffic and customer loyalty data from S3 files into Snowflake, and how to transform JSON data using Hierarchy Parser transformation.
You can utilize your new IDMC org to load data from various data sources into Snowflake and perform data transformations using Data Integration service. With this free IDMC org, you can load 1 billion records per month for free


### What we've covered in this guide
- Create an IDMC org via Snowflake Partner Connect
- Review Snowflake connection in IDMC
- Review Snowflake objects created by the registration process
- Configure AWS S3 connection
- Create a Project folder
- Create a data integration mapping to load S3 files into Snowflake
- Configure Pushdown Optimization
- View mapping job result 
- Confirm Pushdown Optimization is activated
- View result in Snowflake
- Create JSON schema in Data Integration service
- Use Hierarchy Parser transformation
- Create a data integration mapping to load transform JSON hierarchical data into relational format
- Create a mapping task
- View mapping job result 
- View result in Snowflake

### Continue learning and check out these guides

[Documentation: Informatica Data Integration](https://docs.informatica.com/integration-cloud/cloud-data-integration/current-version/introduction/introducing-informatica-cloud--data-integration/data-integration.html)

[Documentation: Snowflake connector](https://docs.informatica.com/integration-cloud/cloud-data-integration/current-version/data-integration-connections/connection-properties/snowflake-data-cloud-connection-properties.html)

[Landing page for Informatica Intelligent Cloud Services Accelerator for Snowflake](https://marketplace.informatica.com/listings/cloud/connectors/snowflake_elastic_data_warehouse.html) 

[FAQ for Snowflake Accelerator](https://docs.informatica.com/integration-cloud/cloud-platform/h2l/1423-informatica-intelligent-cloud-services-for-snowflake-accele/frequently-asked-questions/frequently-asked-questions.html)

