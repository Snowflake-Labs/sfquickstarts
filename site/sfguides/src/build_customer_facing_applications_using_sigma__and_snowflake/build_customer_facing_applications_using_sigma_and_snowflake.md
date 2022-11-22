author: Kelsey Hammock
id: build_customer_facing_applications_using_sigma_and_snowflake
summary: This guide will lead you through the process of connecting Sigma to a Snowflake environment and building an application that leverages the data in Snowflake. This guide additionally highlights unique end user capabilities when Sigma is embedded in an application. 
categories: Data-Applications, Data-Engineering, Analytics
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Applications, Data Engineering, Sigma 

# Build Customer Facing Applications Using Sigma and Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 1

 This lab introduces you to the user interface and embedding capabilities of Sigma Workbooks. This lab does not get into complex data analysis use cases for Sigma, but is designed to showbase the type of engagement and capabilities available in an application development use case.


### Prerequisites
- This lab is designed for semi-technical users who will be aiding in the planning or implementation of Sigma. No SQL or technical data skills are required for this lab.  

### What You’ll Learn 
- How to ingest data into Snowflake & connect to Sigma
- How to leverage Sigma functions for data prep 
- How to build a workbook and visualizations 
- How to embed a workbook in your application  
- How end users of the application can explore data and generate new insights in a self-serve fashion 

### What You’ll Need 
- Access to a Snowflake account on AWS
- Download Portal Template: 
- Download and Install Node.js:
- Download SQL Script: 

### What You’ll Build 
- In this lab you will build a sales performance portal that live queries data in Snowflake and provides unique drill down and exploration capabilities to the end users through embedding Sigma. 

<!-- ------------------------ -->
## Setting up Snowflake 
Duration: 2

### Prepare Your Snowflake Lab Environment

1. If not done yet, register for a Snowflake free 30-day trial at https://trial.snowflake.com

- You will have different Snowflake editions (Standard, Enterprise, e.g.), cloud providers (GCP, AWS, or Azure), and regions (Us Central, Europe West, e.g.) available to you. For this lab, please select AWS as your cloud provider and at minimum enterprise edition.

- After registering, you will recieve an email with an activation link and your Snowflake account URL. Bookmark this URL for easy future access. 

2. Click here and download the "sigma_vhol.sql" file to your local machine. This file contains pre-written SQL commands and we will use this file later in the lab. 
   
### The Snowflake User Interface   

### Logging into the Snowflake User Interface (UI)

1. Open a browser window and enter the URL of your Snowflake 30-day trial environment. You should see the login screen below. Enter your unique credentials to log in. 
   
![login](assets/settingupsnowflake_1.png)
### Navigating the Snowflake Snowsight UI

1. From the Worksheets tab, click the "+ Worksheet" button in the top right to open a new worksheet. 
- In the left pane you will see the database objects browser, which enables users to explore all databases, schemas, tables, and views accessible by the role selected for a worksheet.
- The bottom pane shows results of queries and operations. 

![image2](assets/settingupsnowflake_2.png)

2. At the top left of the page click on the dowward facing arrow next to the worksheet name, select "Import SQL from File", then brose to the "sigma_vhol.sql" file you downloaded in the prior module. Click "Open". 
   - All of the SQL commands you need to run for the remainder of this lab will now appear on the new worksheet. Do not run any of the SQL commands yet. 

 ![imgae3](assets/settingupsnowflake_4.png) 
  ## Provisioning Sigma
  ### Provisioning Sigma via Snowflake Partner Connect

1. On the lefthand side of the Snowflake UI, navigate to Admin, then select partner connect. Click the icon for Sigma.
   
 ![partnerconnect](assets/provisioningsigma_1.png)  

2. You will see a dialog box that will show you the objects that will be created in your Snowflake account by Sigma. We will be using the PC_SIGMA_WH warehouse, PC_SIGMA_DB database, and the PC_SIGMA_ROLE for this lab, which are automatically created for you as part of the launch. 

![connecting](assets/provisioningsigma_2.png)

3. Click "Connect" then "Activate", which will open a new tab. You will be prompted to choose a name for your new Sigma Organization to be be created. Once you have chosen a name, click continue. This will open Sigma in a new tab. Please keep this tab open, as we will return to it later in the lab. 
   
![sigmaorg](assets/provisioningsigma_3.png)

## Preparing and Loading Data into Snowflake

# The Lab Story

This Snowflake and Sigma lab will be done as part of a theoretical real world story to help you better understand why we are performing the steps in this lab, and the order they appear. 

Throughout the lab, we will be working with some common sales data from our fictious physical retail company "Plugs Electronics". This data includes order and SKU number, product names, prices, store names and regions, as well as customer data. Some of this data is structured and some is JSON (semi-structured). 

We will use this data to create a retailer portal where brands who sell their products at Plugs retail locations can log in to see their sales performance across different metrics. 

### Create a Database and Table

1. Go back to the Snowfalke UI and click on the worksheets tab. Per the prior steps, ensure the SQL text from the "Sigma_vhol.sql" file has been loaded into the workseet.

![dbandtable](assets/prepandloaddata_1.png)

- As you can see from the SQL we loaded into our worksheet, a worksheet can have more than one command in it. SQL commands are delimited by semicolons. In order to run a single command, click anywhere on the line / command you would like to execture, then click the "Run" or "Play" button.  

- In this lab, never check the "All Queries" box at the top of the worksheet. We want to run SQL queries one at a time, in a specific order. 

2. <strong> USE ROLE SYSADMIN; </strong> This will set the context of the worksheet to use the role of SYSADMIN when we run the command. We do not want to be in the role ACCOUNTADMIN any more in this lab. 

1. <strong> USE WAREHOUSE PC_SIGMA_WH; </strong> Sets the PC_SIGMA_WH to be used for commands run in the worksheet As you can see by the (XS) to the right of the warehouse name, that an extra small warehouse is being used for this lab. An XS translates to a single node cluster for our virtual warehouse. [Here is a link to Snowflake's docs covering warehouses in detail.](https://docs.snowflake.com/en/user-guide/warehouses-overview.html)
2. <strong> USE DATABASE PC_SIGMA_DB; </strong> This command tells Snowflake to opperate off the PC_SIGMA_DB database, which was created when your Sigma trial was spun up. 
3. <strong>CREATE SCHEMA EMBEDDED_LAB;</strong> This creates a new schema in our PC_SIGMA_DB database.
4. <strong>USE SCHEMA EMBEDDED_LAB; </strong>This sets the context of the worksheet to use our newly created schema. 
5. <strong>CREATE STAGE SIGMA_LAB_STAGE URL = 's3://sigma-embedded-lab-demo/LabData/'; </strong>This creates an external stage in Snowflake that points to an S3 bucket that has the data files we would like to use for the lab. 
6. <strong>LS @SIGMA_LAB_STAGE; </strong>This command lists all of the files in the stage we just created. 

### Loading Data into Snowflake

The data we will be using is demo data for a fictious retailer called Plugs Electronics. This data has been exported and pre=staged for you in an AWS S3 bucket in the US-East(Northern Virginia) region. THe data is in a CSV format, and includes transaction data like order numbers, product names and prices, as well as customer information. This data set is just under 4 million rows.

1. CREATE FILE FORMAT SIGMA_CSV
   TYPE = CSV
   COMPRESSION = GZIP
   FIELD_OPTIONALLY_ENCLOSED_BY = '0x27'
   NULL_IF='null';

 

2. CREATE TABLE TRANSACTIONS
   (ORDER_NUMBER INTEGER,
   PURCHASE_DATE TIMESTAMP,
   TRANSACTION_TYPE STRING,
   PURCHASE_METHOD STRING,
   SALES_QUANTITY INTEGER,
   SALE_AMOUNT INTEGER,
   ITEM_PRICE INTEGER,
   WHOLESALE_COST INTEGER,
   PRODUCT_KEY INTEGER,
   PRODUCT_NAME STRING,
   PRODUCT_TYPE STRING,
   PRODUCT_FAMILY STRING,
   PRODUCT_BRAND STRING,
   STORE_KEY INTEGER,
   STORE_NAME STRING,
   STORE_CITY STRING,
   STORE_STATE STRING,
   STORE_ZIP STRING,
   STORE_REGION STRING,
   ORDER_CHANNEL STRING,
   CUST_KEY INTEGER,
   CUST_SINCE TIMESTAMP,
   CUST_JSON VARIANT
    );


We have data files in our stage as shown in the previous list (ls) command. THese files have certain formats that need to be defined in Snowflake in order for the data to be properly loaded. In this case, we are creating a file format named SIGMA_CSV that is specifiying that the data in the files is delimited by commas, has been compressed, and how to determine null values. We additionally created a table to hold the data we are about to load. More information regarding file formats can be found [here](https://docs.snowflake.com/en/sql-reference/sql/create-file-format.html). 

3. <strong>COPY INTO TRANSACTIONS FROM @SIGMA_LAB_STAGE
   FILE_FORMAT = SIGMA_CSV;</strong>

  - This copies the data from our S3 bucket and loads it into our Transactions table. A SELECT COUNT(*) from the table will show we loaded 3.9 million rows into the table. 

4. <strong>GRANT USAGE ON DATABASE PC_SIGMA_DB TO ROLE PC_SIGMA_ROLE; </strong>
 - Snowflake access rights are based upon [role based access control (RBAC)](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html). This command allows the PC_SIGMA_ROLE to use the PC_SIGMA_DB database. 
  
  5.<strong> GRANT USAGE ON SCHEMA PC_SIGMA_DB.EMBEDDED_LAB TO ROLE PC_SIGMA_ROLE; </strong>
  - This allows the PC_SIGMA_ROLE to use the schema we created earlier in the lab. 

6. <strong>GRANT SELECT ON ALL TABLES IN SCHEMA PC_SIGMA_DB.EMBEDDED_LAB TO ROLE PC_SIGMA_ROLE;</strong> 
- This allows our PC_SIGMA_ROLE to query against the transactions table we created. 
   
7. <strong>USE ROLE PC_SIGMA_ROLE; </strong>
- We completed granting access to the data we ingested to the PC_SIGMA ROLE. This command will now allow the user to start reporting on the data from Sigma using this role. 

8. <strong>SELECT * FROM TRANSACTIONS;</strong>
- A SELECT * from the transactions table should complete successfully. If not, please go back and re-run the prior steps of this module as SYSADMIN to ensure permissions were granted to the new role appropriately.    
  

## Building Your Sigma Workbook 

### Connect Your Workbook to the Dataset

1. Navigate to the Sigma tab that was previously opened through partner connect. Select the top left Paper Crane logo to navigate back to the Sigma homepage if you are not there already. 

2. Lets create a new Workbook and connect it to the data we just ingested into Snowflake. Click on the "+ Create New" button at the top left of the page and select Create New Workbook.

![build](assets/buildworkbook_1.png)

3. We are now inside a Sigma Workbook. Sigma workbooks are a collaborative canvas for data driven decision makers. Each workbook can have one or more pages, and each page has its own canvas. Each canvas supports one or more visual elements (e.g. charts, tables, controls, images, etc).

4. We'll first add a new data source to our workbook. Click the "+" icon on the left hand side in the Elements sidebar, then select the "Table" option. For source, select "Tables and Datasets". 

![build2](assets/buildworkbook_2.png)
![build3](assets/buildworkbook_3.png)

5. On the resulting page, navigate to "Connections", expand the drop down, and click into "Snowflake PC_SIGMA_WH". Select PC_SIGMA_DB, then navigate to teh EMBEDDED_LAB schema and select the "TRANSACTIONS" table. You will notice Sigma automatically populates a preview of the table. Click "Select" to begin our data modeling. 

 ![build4](assets/buildworkbook_4.png)

 ### Workbook Analysis 
 In this segment we will begin to clean up the data set for our customer portal. We will create calculations, parse JSON, and build visualizations with the ultiate goal of creating and embedding a dashboard for our brand managers to get a sense of how their products are performing in Plugs Electronics stores. 

 1. First, lets save our workbook as Customer Portal Workbook by clicking Save As at the top of the page. We will then rename our page to "Data" by clicking the down arrow next to "Page 1" in the bottom left of the UI. 

![build5](assets/buildworkbook_5.png)

  - All workbooks are considered purley exploratory until you as their creator actively save the first version. This means you have one central location to start both your ad-hoc analysis and reporting. Once you begin exploring your data, you can choose to leave the unsaved workbook behind, or you can save it an continue to build it out as a report. 

  2. Let's start by formatting our currency columns. Select the columns for Sale Amount, Item Price, and Wholesale Cost, then click the "$" icon by the formula bar. You will see that these columns are now formatted as curency.

![build6](assets/buildworkbook_6.png)

  3. Double click on the Sale Amount column name and rename this column to Revenue.

![build7](assets/buildworkbook_7.png)

  4. Click the drop down to the right of Purchase Date and select Truncate Date - Day. This will now display the purchase timestamps as the date only. Rename the column to Purchase Date, then repeate this process for the Cust Since column.

![build8](assets/buildworkbook_8.png)

  5. On the far right side of the table you will see the CUST_JSON column. This column hold JSON data around the customers who made these transactons. CLick on the arrow to the right of the column name, and choose extract columns. This will bring up a window where Sigma has already identified the fields within the JSON object. Select Age Group and Cust_Gender. You will notice that Sigma intuitively parses this data out of the JSON object and adds it to the table as columns. 

![build9](assets/buildworkbook_9.png)

  6. Finally, to prevent end users from extracting more sensitive customer information, click the arrow next to the Cust_JSON column and select "Hide Column" from the drop down. 

![build10](assets/buildworkbook_10.png)

  - Every action we take in Sigma produces machine-generated SQL, optimized for Snowflake, that runs live against the warehouse. This ensures that the data is secure and up to date at all times. YOu can see the queries we are generating by clicking the dropdown next to the refresh button on the top right and selecting "Query History". 

  - If we navigate back to our Snowflake environment quickly, we can see the queries being pushed down in our Snowflake query history view as well. 

![build11](assets/buildworkbook_11.png)



  ### Creating Visualizations 
  It is often easier to spot trends, outliers, or inishgts which lead to further questions when viewing data in a vizualization. Sigma makes it easy to create vizualizations of your data while also enabling you to dig into the data that makes up the vizualization. 

  1. Start the creation of a visuzalization by sclicking on the table that we just build, then clicking the "Create Child Element" icon on the top right corner. Select "Visualization" to start creating a new chart. 
   
![build12](assets/buildworkbook_12.png)

  2. You will see a new visualization element has been created under our table. In the left-hand bar you will see a dropdown that lists all of the visualizations that Sigma currently supports. Select the bar chart. 

  3. On the X-Axis click the plus icon and add our "Store Region" column. Notice that Sigma allows you to search for the column you would like to add. We can also drag values onto the axies instead of using the add button. Find "Revenue" in the list of columns and drag it to the Y-axis. The value will automatically aggregate and become "Sum of Revenue". Double click the header on the bar chart and name it Revenue by Store Region. 

![build13](assets/buildworkbook_13.png)
![build14](assets/buildworkbook_14.png)

  4. Click the 'kebab' (3 dots) on the top right hand side of the element. From the drop down, select move to new page. This will create a page in our workbook to hold our visualizations. Rename this new page "Customer Portal".
   
![build38](assets/buildworkbook_38.png)

  5. Now lets looks at our sales over time to get an understanding of how we are trending. Another way to create a new chart is by selectiong the plus icon on the top of the left hand pannel next to our 'Page Elements' title. Click on this icon to get a list of elements that we can add to our canvas, and choose 'Viz'. 

![build15](assets/buildworkbook_15.png)
![build16](assets/buildworkbook_16.png)

  6. After selecting the 'Viz' icon, you will be prompted to select a source to use for that visuzalization. You can see tabs for "In Use", which shows sources currently being used by other elements in the workbook, "New", which allows you to add a new source from a table, dataset, SQL, or CSV upload, and "Page Elements", which holds all of the data elements already in the workbook, such as the bar chart we created or the table. From the "In Use" tab, select the Workbook Element "Transactions". 

![build17](assets/buildworkbook_17.png)

  7. Click on the visualization drop down and select "Line". Next, drag the "Purchase Date" column to the X-Axis. (Optionally add it using the + icon next to the x-axis)

  ![build18](assets/buildworkbook_18.png)

  8. Notice that Sigma has defaulted to change the aggregation to "Day", and the title now reads "Day of Date". We can change this aggregation at any time using the dropdown next to the field name, and selecting a new aggregation level under the "Truncate Date" submenu. Let's change the aggregation level to be "Month".   

![build19](assets/buildworkbook_19.png)

  9.  Next we can place our "Revenue" column on the Y-Axis to see our revenue over time. Again, Sigma has automatically summed the reveue to the monthly level.

![build20](assets/buildworkbook_20.png)

  10. We now have a line graph with revenue by month. Lets add some more detail by breaking the series out by customer age group. To do this add "AGE_GROUP" to the color grouping section in the left sidebar. Once this is done, double click the title on the line graph and rename it Revenue by Month & Age Group. 

![build21](assets/buildworkbook_21.png)

  11. Lets create one more visualization around our revenue generated. Again, select the "+" icon on the top left of the screen and select "Viz". 

![build22](assets/buildworkbook_22.png)
![build23](assets/buildworkbook_23.png)

After selecting the 'Viz' icon, you will be prompted to select a source to use for that 'viz'. You can see tabs for selecting:
- <strong> In Use </strong> : sources that are currently being used by other elements in the workbook.
- <strong> New </strong>: a new source that could be a table, dataset, SQL, or uploaded CSV.
- <strong> Page Elements </strong> : any data elements already in the workbook, such as the bar chart or table we created.

12. For the data source, go to the In Use tab and select the Workbook Element "Transactions". For the visualization type, select "Single Value" from the drop down list. 

 ![build24](assets/buildworkbook_24.png)

  13. Next drag Revenue to the value. This will automatically sum the revenue across all transactions. Rename this visualization to Total Revenue by double clicking Sum of Revenue on the left hand side and typing Total Revenue. 

 ![build25](assets/buildworkbook_25.png)

  14. Finally, we want to share some transaction level data with our end users. From our transactions table on the data page, click create child element - table. This create a new table from our Transactions table. Let's sort this table by purchase date descending, so that our most recent transactions are shown first. Then move this element to our Customer Portal page. 

  ![build26](assets/buildworkbook_26.png)

  15. Drage and drop the visuzaliations on the Customer Portal page so that the Total Revenue element is at the top, the line chart and bar graph are side by side below it, and the transactions table is at the bottom.

  ![build27](assets/buildworkbook_27.png)

   ### Create Filters
   Let's add a filter to this data. We will do this by adding a control element to our canvas. Controls enable interactions with the chart such as filtering the charts when in use. When clicking the '+' icon in the upper left hand pane, we will see options for control elements:
   - <strong> Number Range</strong>: Creates a range of values you wish to look at
   - <strong> List Values</strong>: Creates a list of values for users to choose from
   - <strong> Text Box</strong>: Allows users to input free form text
   - <strong> Switch</strong>: Allows users to filter on Boolean (true/false) values
   - <strong> Drill Down</strong>: Allows you to specify specific drill paths
   - <strong> Date </strong>: Allows users to filter for a specific date or date range
   
   
  1. Clicking the "+" icon on the upper left hand pane next to "Page ELements", select "Date". This will add a Date control element to the canvas. 

![build28](assets/buildworkbook_28.png)

   1. After adding the "Date" control to our Customer Portal page, lets drag it to the top of the page and update the control_id to say "Date-Range" and update the control label to say "Select a Date Range". 

![build29](assets/buildworkbook_29.png)

   3. Next we need to tell the control which elements we wan tit applied to. Clicking on the filter control, we have some options in the left hand pane. Select "Targets", then choose "Add Target". Select the 3 visualizations we previously created, Revenue by Store Region, Revenue by Month & Customer Age, and Total Revenue. 

   ![build30](assets/buildworkbook_30.png)

   4. On the data page, right click on the drop down next to the column "Product Brand" and select the "Fliter" option from the menue. A new filter will be added to the table. 

   ![build31](assets/buildworkbook_31.png)
   ![build32](assets/buildworkbook_32.png)


   5. CLick on the kebab menu to the right of the "Product Brand" filter and select "Convert to Page Control".
   
   ![build33](assets/buildworkbook_33.png)
   
    The filter will be added as a page control to the canvas. This product brand filter is additionally what we will pass into our embed URL to only serve up data related to the brand we are exploring. Since this filter started out with a target, there is no need to add one. 
   ### Finishing up the Canvas
In Sigma, you can add a variety of UI elements to your workbook to customize the look and feel. In this section, we will work with text elements to create a dynamic text element as the header for our workbook. When you click the '+' in the top left, you will see a variety of elements available to you such as:
- <strong> Image</strong>: Upload images or links to URLs to show an image on the canvas
- <strong> Button</strong>: Use buttons to navigate to toher workbooks, websites, or download the workbook as a PDF
- <strong>Embed</strong>: Embed other websites or applications into your workbook
- <strong>Spacer</strong>: Use to add space between elements on the canvas
- <strong>Divider</strong>: Use to create hard divisions between sections of the canvas

1. To start, navigate to your Customer Portal page, and click add element. Under UI elements, select Text. 

   ![build34](assets/buildworkbook_34.png)

2. We are going to create a dynamic Text element as the header for our page. In the text bar type <strong>=If(CountDistint([TRANSACTIONS/Product Brand]) >1, "All Brands", [TRANSACTIONS/Product Brand])Sales Performance</strong>. From the text bar, select "Large Heading" for the element size, and drag it to the top. Finally, click the formatting option to center the element. This text element will adjust based ont eh user we log into our portal as, and the brand we are exploring. 

   ![build35](assets/buildworkbook_35.png)

3. On the bottom left, click the down arrow next to your 'Data' page and select "Hide". This will hide the page with the underlying data set from your end users. 

   ![build36](assets/buildworkbook_36.png)

4. Click Publish to save these changes. 
   ## Embedding the Sigma Workbook into an Application

   ### Building the Application / Portal

  We are now going to begin buildng our portal where we can embed our workbook. This will be a Sales Performance dashboard where our family of brands can log in to see how their products are performing in our store. 

  1. First we will need to install Node.js. Node is going to allow us to set up a local server, as well as the front end portal, and securely embed our dashboards with row level security so that brands are not seeing eachother's data. Downlaod and install Node.js by going here: [https://nodejs.org/](https://nodejs.org/)
   - Note, there are many programming languages and libraries you can use to code a client and server side application, this just happens to be the one we will be using today. 

   ![embed1](assets/embeddingtheworkbook_1.png)

  2. Once downloaded, double click on the download and go through the installation steps. This should only take a minute. 

  ![embed2](assets/embeddingtheworkbook_2.png)

  3. Now open the app_embed folder that was provided to you. This holds the shell for the portal we will be building today. 

  ![embed3](assets/embeddingtheworkbook_3.png)

  4. First, open the two files index.html and server.js in your favorite text editor. 

  ![embed4](assets/embeddingtheworkbook_4.png)

  5. If we look first at the index. html file, we can see it is just a basic HTML page that calls an API to the backend server. js file. When the server is running, you will be able to access the page by going to the URL http://localhost:3000 in your browser. This is also where you would define the client-facing website if you wanted to customerize the look and feel of the portal. 

  ![embed5](assets/embeddingtheworkbook_5.png)

  6. If we move over to the server.js file, we can start to see what is expected.  Sigma requires a variety of parameters to be set when requesting a dashboard. These parameters not only ensure security, but also allow for flexible interaction with filters and parameters within the dashboard.
- <strong> <dashboard_embed_path> </strong>is the Embed Path that is generated on the dashboard you wish to embed.
- <strong><random_nonce_value></strong> is a  random unique string (less than 255 characters). Sigma uses this to prevent application embed URLs from being shared and reused.
- <strong> <allow_export_boolean> </strong>(optional) is a boolean (true/false) parameter that controls whether the viewer of the dashboard will be able to download data from the dashboard visualizations. If this parameter is not specified, the URL will default to false and viewers will not be able to download data.
- <strong><session_length></strong> is the number of seconds after <unix_timestamp> that the URL will remain valid. After the specified number of seconds, the Application Embed will no longer display new values.
- <strong><unix_timestamp></strong> is the current time as a UNIX timestamp. Sigma uses this in combination with the <strong><session_length> </strong>to determine if your link has expired. The URL is valid after the <strong><unix_timestamp></strong> and before the <strong><session_length></strong> expiration.
- <strong><control_id></strong> and <strong><control_value></strong> are the ID and value of a dashboard control you'd wish to pass through to the dashboard. You may pass multiple control IDs and values. This will allow you to customize what your viewers see.
Note: All controls must exist on the dashboard. This is to ensure changes to a dashboard do not cause data to be visible unintentionally.
- <Strong>< mode ></strong> Determines the end users permissions. For this lab, it will be set to <strong>mode = explore</strong> to allow end users to take advantage of Sigma’s exploratory capabilities. 

We need to install a couple libraries in order to get this working: express and uuid. These libraries are used to construct a unique signature for your embed URLs when combined with a secret key provided by Sigma. This makes it so that no one is able to ever modify ad request the dashboard other than the server.

![embed6](assets/embeddingtheworkbook_6.png)

7. Go back to the Finder, right-click on the app_embed folder, and select "New Terminal at Folder". 

![embed7](assets/embeddingtheworkbook_7.png)

8. Now we can install the needed libraries by issuing the following command:<strong> npm install expresss uuid</strong>.

![embed8](assets/embeddingtheworkbook_8.png)

There are two key edits we need to make in order for the server to use our workbook, the Secret Key and the Embed URL of our workbook. We will obtain both of these pieces of information next. 

![embed9](assets/embeddingtheworkbook_9.png)

### Generating an Application Embedding Secret in Sigma

1. If we go back to Sigma, we can generate our secret key that is needed for application embedding. You can do this by clicking on your user icon on the top right of the screen and selecting "Administration". 

![embed10](assets/embeddingtheworkbook_10.png)

2. On the account screen there is an Embedding section with a subheading labeled "Application Embedding". Click on the "Add" button to generate the key.

![embed11](assets/embeddingtheworkbook_11.png)

3. You will now get your secret key that can be used for all embedded workbooks. Please make sure to save this key in a secure place. If you lose it, you will have to re-generate a new key. 

![embed12](assets/embeddingtheworkbook_12.png)

4. Copy this key and place it in the server.js file where it says "YOUR_SECRET_KEY_HERE". 

![embed13](assets/embeddingtheworkbook_13.png)

### Generating an Embed URL for your Workbook

1. Now, if we go back to your Sigma workbook by clicking on the back button in the top left, we can retrieve the embed URL. 

![embed14](assets/embeddingtheworkbook_14.png)

2. Find the drop-down icon next to the dashboard name in the top header bar and select "Embedding". 

![embed15](assets/embeddingtheworkbook_15.png)

3. Next, click on the tab labeled "Application(0)" and use the dropdown to generate an embed path for the entire workbook. 

![embed16](assets/embeddingtheworkbook_16.png)

4. Now it has generated the embed path for your dashboard. IF you select the unique identifier on the end you can copy and pase it into the server.js file where it says "YOUR_DASHBOARD_ID_HERE".

![embed17](assets/embeddingtheworkbook_17.png)

5. Save your server.js file.
6. Once complete, we are ready to start our sever. Back in your terminal, you can run the folloiwng command to start the server: node server.js

![embed18](assets/embeddingtheworkbook_18.png)

7. Now that the server is running, we can visit our portal by going to http://localhost:3000 in our browser. 

![embed19](assets/embeddingtheworkbook_19.png)
## Row Level Security 

1. Now we might want to put some row level security on this dashboard, so that brands can only see data related to the sale of their own products. Navigate back to your data page in your Sigma workbook. 

2. On the data page, find the page control we created previously for Product-Brand. When we select it the left pannel will show its properties. Find the Control ID and copy the value. It should be a value similar to "Product-Brand". 

![rls1](assets/rowlevelsecurity_1.png)

3. Click Publish to save the changes. 

![rls2](assets/rowlevelsecurity_2.png)

4. Navigate to your server.js file and un-comment the field that describes the control_id by deleting the "//" at the beginning of the line. Here is where we can place our control_id and pass a value to set that control. Today we will hardcode the value to "Samsung", but in a real world scenario, you would likely pass in a customer_id or other unique identifier to filter the dashboard.

![rls3](assets/rowlevelsecurity_3.png)

5. Save your server.js file and navigate back to your terminal. Here we need to stop the server by pressing "Control + C". This will exit the running server process. We can then start it again with our new configuration by running the command "Node server.js".

![rls4](assets/rowlevelsecurity_4.png)

6. Now if you go back to your browser and reload the web page, you should notice that we only see data for Samsung now. You will additionally notice that the dynamic text we created for the header now reads "Samsung Sales Performance" rather than "All Brands Sales Performance". 

![rls5](assets/rowlevelsecurity_5.png)
## Exploring the Embed

For the purpose of this lab, we will now explore the portal as a memeber of the Samsung merchandising team. We have been tasked with identifying which regions to focus our in store marketing efforts on, and will use the Plugs Sales Performance portal to help identify where the majority of our purchases are coming from. 

1. Looking at the customer portal, click maximize element in the top right of the Revenue by Store Region bar chart. 

![Explore1](assets/exploretheembed_1.png)
![Explore2](assets/exploretheembed_2.png)

2. Lets get some additional insights from this dashboard. Drage Product Type to the color category, then collapse the bar chart by clicking minimize element in the same place you clicked to expland it. 

3. Next, scroll down to the Transactions table and click Maximize element. 

4. Scroll right to the store region column. Click the drop down arrow and select "Group Column". Then, scroll to the Order Channel column, and again select "Group Column". We can now see that our data has been aggregated at two levels, first the store region, then the order channel. 

![Explore3](assets/exploretheembed_3.png)

5. Click the drop down next to Order Channel and select "Add new column". 

6. In the formula bar, type CountDistinct([Order Number]). Rename this column Number of Orders. 

7. Again, click the drop down next to Order Channel and select "Add Column". This time, type Sum([Revenue]) in the formula bar. What we can now see is Revenue generated for a sepecific region by the Order CHannel the purchase was made from. 

8. With Sum of Revenue column selected, click the paintbrush on the right of the table icon in the left hand tool pane. 

![explore4](assets/exploretheembed_4.png)

9. Select "Conditional Formatting", then click "Data Bars". 

![explore5](assets/exploretheembed_5.png)

10. Click the minus to the left of Order Channel to collapse the view at the aggregate level. You should now see revenue generated by different order channels across regions. 

![explore6](assets/exploretheembed_6.png)

11. Minimize the element using the arrows in the top right to collapse this new visuzalization back into the larger page. 

## Helpful Resource

- Help Center including Documentation: https://help.sigmacomputing.com/hc/en-us
- Sigma Blog: https://www.sigmacomputing.com/blog/
- Resource and Case Studies: https://www.sigmacomputing.com/resources/
- Sigma Embedding Docs: https://help.sigmacomputing.com/hc/en-us/categories/1500001787282-Embedded-Analytics
  

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: sample 
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Science, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Daniel Myers 
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
Positive
: This will appear in a positive info box.


Negative
: This will appear in a negative info box.

### Buttons
<button>
  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files