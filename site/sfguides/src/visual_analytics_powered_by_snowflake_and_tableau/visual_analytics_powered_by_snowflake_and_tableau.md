author: Chandra Nayak & Madeline Lee
id: visual_analytics_powered_by_snowflake_and_tableau
summary: Visual Analytics Powered by Snowflake and Tableau
categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, Data Collaboration, Date Lake

# Visual Analytics powered by Snowflake and Tableau

Duration: 60

<!-- ------------------------ -->

## Overview

Join Snowflake and Tableau for an instructor-led hands-on lab to build governed, visual, and interactive analytics quickly and easily on Food Truck data.

![img](assets/finished_dash.png)

### What You’ll Learn

* Analyzing structured and semi-structured data
* Levergaging Snowflake Marketplace and integrating External DataLakes 
* Snowflake Generative AI capability
* Building Visualization using Tableau on Snowflake tables. 


### What You’ll Build

* Using structured and semi-structured data to Snowflake tables 
* Incorporate Weather data from Snowflake Marketplace
* Use Iceberg tables to access externally stored datalakes
* Easily Extract Sentiment from unstructured data using Snowflake Cortex
* A simple Tableau dashboard to visualize Snowflake data. 

### Prerequisites

* Familiarity with Snowflake, AWS and Tableau
* [Snowflake](https://trial.snowflake.com/) account or free trial *** choose AWS and Enterprise ***
* [AWS](https://aws.amazon.com) account or free trial *** choose same region as Snowflake Account ***
* [Tabelau Online](https://www.tableau.com/products/online/request-trial) account or free trial
* [Visual Studio Code](https://code.visualstudio.com/download) editor
<!--- ------------------------- -->

## Snowflake Configuration
Duration: 2

1. Create a Snowflake enterprise trial account
2. Login to your Snowflake account


### Login User Interface

 ![Snowflake Login](assets/create_folder.png)

### Download Scripts and Create Worksheet from SQL 
![Create Worksheets](assets/Worksheet_1.png)

<!-- ------------------------ -->

## Managing Semi-Structured Data

Duration: 5

### Run the scripts in a Snowsight or VSCode 

#### Create Snowflake Database and Warehouse 
[Click here to download  create_db_wh.sql](scripts/create_db_wh.sql)


#### Grant Privileges on Snowflake Objects
[Click here to download grantperms.sql](scripts/grant_perms.sql)

#### Create Snowflake Stages and Native Tables
[Click here to download createobjects.sql](scripts/create_objects.sql)

#### Load data into Raw Tables 
[Click here to download tabloadraw.sql](scripts/tab_load_raw.sql)


## DataLake Integration 

### Create the necessary AWS Configuration 
Duration: 15 

#### Download the Customer Reviews files to your laptop

unzip the file before you load into AWS bucket
[click here to download for reviews zipfile](assets/2022.zip)

**Login to AWS Account, and create a bucket in the same region as your Snowflake account**

![img](assets/create_bucket.png)

#### Upload the folder from your laptop to the S3 bucket.
![img](assets/Upload_Folder.png)

#### Take a note of your AWS Account ID.
![img](assets/account_id.png)

**Now, in your Snowflake account**

[click here to download SQL for s3_integration](scripts/aws_integration.sql)
```sql

USE DATABASE frostbyte_tasty_bytes;
USE SCHEMA raw_customer;

CREATE or REPLACE STORAGE INTEGRATION frostbyte_tasty_bytes.raw_customer.int_tastybytes_truckreviews
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::<your AWS account ID>:role/<give a name for IAM role>' -- ex: snow_s3_access_role
  ENABLED = TRUE
  STORAGE_ALLOWED_LOCATIONS = ('s3://<name of your S3 bucket>');

DESC INTEGRATION <name of the integration>; -- you will need the output of these values in AWS CloudFormation

CREATE OR REPLACE FILE FORMAT frostbyte_tasty_bytes.raw_customer.ff_csv
    TYPE = 'csv'
    SKIP_HEADER = 1   
    FIELD_DELIMITER = '|';

CREATE OR REPLACE STAGE frostbyte_tasty_bytes.raw_customer.stg_truck_reviews
    STORAGE_INTEGRATION = int_tastybytes_truckreviews
    URL = 's3://<name of your S3 bucket>/'
    FILE_FORMAT = ff_csv;
```

### Launch the AWS CloudFormation 
**Click the template and login to AWS** [CloudFormationTemplate](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=Snowflake-storage-integration&templateURL=https://snowflake-corp-se-workshop.s3.us-west-1.amazonaws.com/CFTs/storageInt.json)

![cftemplate](assets/CloudFormation.png) 
#### Now you need to copy the following values from Snowflake Storage Integration 
![desc_storintegration](assets/descInt.png)

#### Copy the values below  
![storagedetails](assets/CFT.png)

**Select defaults for remaining screens and submit** 
``` sql
 --- Test if your AWS Storage is Accessible 
SELECT   SYSTEM$VALIDATE_STORAGE_INTEGRATION('<integration_name>',    's3://<bucket>/',    'validate_all.txt', 'all'); 
```
#### Output should show success for READ and LIST  
{
  "status" : "success","actions" : { "READ" : { "status" : "success" }, "LIST" : { "status" : "success" }}
}


### Create Snowflake managed Iceberg Tables to access Datalake 
Download and Run Queries on Customer review Data
[Review Data](scripts/query_iceberg.sql)


<!-- ------------------------ -->


## Login to Tableau Online & Connect to Snowflake

Duration: 20

Navigate to https://online.tableau.com/ and login to Tableau Cloud (Online) using your login credentials.

If using a trial site, make sure you have agent and Pulse enabled - see this video for instructions https://www.youtube.com/watch?v=I9jQt0xM_JY&ab_channel=Tableau

<br>

You will be redirected to the Tableau Cloud (Online) Home page. Within the blue “Welcome to your Tableau site” banner, click into the “New” dropdown and select “Workbook”.

 ![A](assets/Tab_1.2.png)

<br>

You will be automatically prompted to connect to a data source. Within the “Connect to Data” popup window, select “Connectors”. Find *Snowflake* in the grid.
Note: you may need to use the horizontal bottom scrollbar at the bottom of the window and scroll to the right of the “Connections" tab.

 ![A](assets/Tab_1.3.png)

<br>

Enter the Server name. Note that you will need to remove the 'https://' from the name (see screenshot). You can find the server name [insert instructions here] Change the authentication method to username/password, enter your credentials & then click the blue “Sign in” button.

 ![A](assets/no_https_in_server_name.png)

<br>

Within the connections pane, make the following selections:

* Warehouse: your warehouse
* Database: FROSTBYTE_TASTY_BYTES
* Schema: ANALYTICS


A list of tables will appear:

 ![A](assets/Tableau_Canvas_3.png)


<br>

Click and drag the 'ORDERS_V' table where it says “Drag tables here”.

<br>

Next, click and drag the 'PRODUCT_FINAL REVIEWS' to the Canvas. This will create a relationship. In Tableau, a relationship is a flexible way to do multi-table analysis without creating one large flat table. Make sure that the fields are mapped correctly by matching 'Primary City’, ‘Truck ID’, and ‘Order ID’.

![A](assets/Tableau_Relations_4.png)

Drag Customer Loyalty Metrics out to the canvas, and map Orders and Customer Loyalty Metrics table by joining on ‘Customer ID’.

![Joins](assets/Tableau_Joins_5.png)

Let’s publish this data source and call it ‘Frostbyte’. Embed the credentials for now.

![list_ds](assets/Tableau_Data_5.png)

Click Publish.

<!-- ------------------------ -->

<!-- ------------------------ -->

<br>

## Visualize Data

Now we are ready to visualize our data! Click ‘Go to Frostbye’. From the published data source, click ‘New’ and select ‘New Workbook’. In the bottom left of the screen, click “Sheet 1”.

 ![publish](assets/Tableau_Publish_7.png)

 ![workbook](assets/Tableau_Workbook_8.png)
<br>

We'll start by getting a quick sense of how each Truck Brand is doing in terms of reviews. Start a Tableau Agent session by clicking the astro logo in the top right corner. Click ‘Got it’ to initiate the session. Then, click ‘Suggestions’.

![agent](assets/Tableau_agent_9.png)

![suggest](assets/Tableau_Suggest_10.png)

<br>
Click on any suggestion. It may take time for Tableau Agent to index your data. See how it will build the visualization for you, and also give you feedback in the agent chat itself. 
<br>


![Options](assets/Tableau_Options_11.png)

Next, type in ‘Compare average reviews by truck brand’ and hit enter. See how the visualization is created. 

![Wiz](assets/Tableau_wiz_12.png)

Now Tableau Agent is iterative, so lets add complexity to the viz by dragging and dropping. we don’t have to just use the chat to build this. Drag ‘Primary City’ from the sentiment table to the rows shelf, to the left of ‘Truck Brand Name’.

<br>

![Tableau_Dash](assets/Tableau_Dash_13.png)

Now we can see the breakdown of sentiment for each truck in each city- and look, there is some average negative sentiment! Let’s focus on only those trucks.
Next, let’s use an agent to filter the data. Type in ‘filter to only trucks with negative average reviews for each city’ and hit enter.

<br>

![Tableau_Agent](assets/Tableau_agent_14.png)

Wow, this might be something to take note of. We should help those truck owners out and figure out how we can increase our service or quality, since it seems customers are disappointed and have bad associations with those trucks in those cities. 

![completed_wkbk](assets/Tableau_wbook_15.png)

Finally, we’ll want to see if it’s a busy truck, and how many orders are coming through those trucks, to figure out where to focus first. I’ll drag out ‘Count Orders_V’ onto the Color tab in the details pane.

![Publish_wkbk](assets/Tableau_Dash_16.png)

Looks like we should focus on trucks in Mumbai first, as they are getting the most orders, and have negative reviews. 

Save the workbook.


<!-- ------------------------ -->

<!-- ------------------------ -->

<br>

## Publish
![Publish_final_reviews](assets/Tableau_publish_rw_work_17.png)

Lets see if we can track that over time and get alerts on any dropping review sentiment using Tableau Pulse. Save this
![Close](assets/Tableau_close_18.png)


<br>
Next, navigate to Tableau Pulse. Click ‘New Metric Definition’.

![Pulse](assets/Tableau_Pulse_19.png)


![pulse_metric](assets/Tableau_pulse_metric_20.png)

Select the data source you just published named ‘Frostbyte’.

![create_def](assets/Tableau_create_pulse_21.png)
Name your pulse metric ‘Average Review Sentiment’ and fill out the values in the screenshot. We want to track average final review sentiment over the date. Select ‘Review Sentiment’, ‘Average aggregation, and ‘Review Date’ as the time dimension.

![save_metric](assets/Tableau_Pulse_save_22.png)

<br>

Add filters such as ‘Truck Brand Name’ and ‘Primary City’.

![filter](assets/Tableau_P_filter_23.png)

![Save_Insight](assets/Tableau_24.png)

Click Next, Next, until you get to the Records and Transitions page. Since we don’t have unique identifiers for the reviews, we will turn this setting off.

![sent_metric](assets/Tableau_25.png)

Your Metric should look something like this. Click save, and your published metric should load automatically.
![present_metric](assets/Tableau_26.png)

New: Set a goal to 0.25, or a value between 0 and 1, to get notified every time average sentiment across all trucks goes below that number. 

![Goal](assets/Tableau_27.png)

Click Save.


Congratulations! You have successfully completed the Tableau portion.


<br>

<!-- ------------------------ -->



<!-- ------------------------ -->


## Conclusion and Resources

Congratulations! you have completed the lab.

In this lab we captured semi-structured data coming from TastyBytes food truck data, enriched that weather data from Snowflake Marketplace data to find correlation between food sales and weather. We visualized the data using Tableau to quickly arrive at new insights.

[ Download tb_reset_vhol.sql & create Worksheet to run SQL file](scripts/tb_reset_vhol.sql)


[Semi-structured Data](https://docs.snowflake.com/en/user-guide/semistructured-concepts.html)
<br>
</br>
[Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg)
<br>
</br>
[Snowflake Marketplace](https://other-docs.snowflake.com/en/data-marketplace.html)
<br></br>

### Video on the Demo

[Youtube - Video on the Demo]()
<!-- ------------------------ -->

<br>

