author: Josh Hall
id: from-clicks-to-cortex-build-ai-ready-data-pipelines-with-coalesce-on-snowflake-in-a-snap
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Learn how to leverage Coalesce Marketplace to extend any of your data projects effortlessly.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# From Clicks to Cortex Build AI Ready Data Pipelines with Coalesce on Snowflake in a Snap

<!-- ------------------------ -->
## Overview


This Hands-On Lab exercise is designed to help you master building data pipelines using Coalesce Marketplace. In this lab, you’ll explore the Coalesce interface, learn how to easily transform and model your data with a variety of packages from Coalesce marketplace, understand how to build reporting pipelines, and play with real-time functionality.

### What You’ll Learn 
* How to navigate the Coalesce interface
* How to add data sources to your graph
* How to prepare your data for transformations with Stage nodes
* How to join tables
* How to apply transformations to individual and multiple columns at once
* How to build out Dimension and Fact nodes
* How to make changes to your data and propagate changes across pipelines
* How to configure and build an ML Forecast node

By completing the steps we’ve outlined in this guide, you’ll have mastered the basics of Coalesce and can venture into our more advanced features.

### What You’ll Need 
* A Snowflake [trial account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=na-us-en-brand-trial-exact&utm_content=go-eta-evg-ss-free-trial&utm_term=c-g-snowflake%20trial-e&_bt=579123129595&_bk=snowflake%20trial&_bm=e&_bn=g&_bg=136172947348&gclsrc=aw.ds&gclid=CjwKCAiAk--dBhABEiwAchIwkYotxMl4v5sRhNMO6LxCXUTaor9yH2mAbOwQHVO0ZNJQRuNyHrmYwRoCPucQAvD_BwE&utm_cta=developer-guides)
* A Coalesce trial account created via [Snowflake Partner Connect](https://coalesce.io/product-technology/launch-coalesce-from-snowflake-partner-connect/)
* Basic knowledge of SQL, database concepts, and objects
* The [Google Chrome browser](https://www.google.com/chrome/)

### What You’ll Build 
* A Directed Acyclic Graph (DAG) representing a real-time data pipeline leverage advanced Snowflake features.

## Before You Start

To complete this lab, please create free trial accounts with Snowflake and Coalesce by following the steps below. You have the option of setting up Git-based version control for your lab, but this is not required to perform the following exercises. Please note that none of your work will be committed to a repository unless you set Git up before developing.

We recommend using Google Chrome as your browser for the best experience.

| Note: Not following these steps will cause delays and reduce your time spent in the Coalesce environment. |
| :---- |

### Step 1: Create a Snowflake Trial Account

1. Fill out the Snowflake trial account form [here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=na-us-en-brand-trial-exact&utm_content=go-eta-evg-ss-free-trial&utm_term=c-g-snowflake%20trial-e&_bt=579123129595&_bk=snowflake%20trial&_bm=e&_bn=g&_bg=136172947348&gclsrc=aw.ds&gclid=Cj0KCQiAtvSdBhD0ARIsAPf8oNm6YH7UeRqFRkVeQQ-3Akuyx2Ijzy8Yi5Om-mWMjm6dY4IpR1eGvqAaAg3MEALw_wcB&utm_cta=developer-guides). Use an email address that is not associated with an existing Snowflake account.

2. When signing up for your Snowflake account, select the region that is physically closest to you and choose Enterprise as your Snowflake edition. Please note that the Snowflake edition, cloud provider, and region used when following this guide do not matter.

    ![image1](./assets/image1.png)

3. After registering, you will receive an email from Snowflake with an activation link and URL for accessing your trial account. Finish setting up your account following the instructions in the email.

### Step 2: Create a Coalesce Trial Account with Snowflake Partner Connect

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name.

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name.

1. Select Data Products > Partner Connect in the navigation bar on the left hand side of your screen and search for Coalesce in the search bar.

    ![image2](./assets/image2.png)

2. Review the connection information and then click Connect.

    ![image3](./assets/image3.png)

3. When prompted, click Activate to activate your account. You can also activate your account later using the activation link emailed to your address.

    ![image4](./assets/image4.png)

4. Once you’ve activated your account, fill in your information to complete the activation process.

    ![image5](./assets/image5.png)

Congratulations! You’ve successfully created your Coalesce trial account.

### Step 3: Set Up The Dataset

1. Within Worksheets, click the "+" button in the top-right corner of Snowsight and choose "SQL Worksheet.”

    ![image8](./assets/image8.png)

2. Navigate to the [Marketplace HOL Data Setup File](https://github.com/coalesceio/hands-on-labs/blob/main/marketplace-hol/hol_setup.sql) that is hosted on GitHub.

3. Within GitHub, navigate to the right side and click "Copy raw contents". This will copy all of the required SQL into your clipboard.

    ![image9](./assets/image9.png)

4. Paste the setup SQL from GitHub into your Snowflake Worksheet. Then click inside the worksheet and select All (*CMD + A for Mac or CTRL + A for Windows*) and Click "► Run".

5. After clicking "► Run" you will see queries begin to execute. These queries will run one after another within the entire worksheet taking around 60 seconds.

Once you’ve activated your Coalesce trial account and logged in, you will land in your Projects dashboard. Projects are a useful way of organizing your development work by a specific purpose or team goal, similar to how folders help you organize documents in Google Drive.

Your trial account includes a default Project to help you get started. Click on the Launch button next to your Development Workspace to get started.
    ![image10](./assets/image10.png)


## Installing Packages From Coalesce Marketplace

You will need to add packages from Coalesce Marketplace into your workspace in order to complete this lab.

1. Within your workspace, navigate to the build settings in the lower left hand corner of the left sidebar

    ![image12](./assets/image12.png)

2. Select Packages from the Build Settings options

    ![image13](./assets/image13.png)

3. Select Browse to Launch the Coalesce Marketplace

    ![image14](./assets/image14.png)

4. You'll see a variety of packages available to install. For this lab, we'll be installing each of the packages listed here:

    * External Data Package
    * Dynamic Tables
    * Cortex
    * Incremental Loading

    The process for installing each of these packages is the same, so once you do it once, you'll be able to follow the same flow for each consecutive package. Let's start with the External Data Package.

5. Select the **Find out more** button on the External Data Package. This will open the details of the package

    ![image15](./assets/image15.png)

6. Copy the package ID from the External Data Package page

   ![image16](./assets/image16.png)

7. Back in Coalesce, select the Install button:

   ![image17](./assets/image17.png)

8. Paste the Package ID into the corresponding input box:

   ![image18](./assets/image18.png)

9. Give the package an Alias, which is the name of the package that will appear within the Build Interface of Coalesce. We'll be using the following aliases for each package in this guide:

    * External Data Package: EDP
    * Dynamic Tables: Dynamic-Tables
    * Cortex: Cortex
    * Incremental Loading: Incremental

    Finish by clicking Install.

    ![image19](./assets/image19.png)

10. Continue to follow this process until all four packages have been installed.

## Configure Storage Locations and Mappings

Your Partner Connect Coalesce Account will come with two Storage Locations out of the box. We need to add one more to accomodate for some of the work we will be doing. In the setup of this guide, you will have run a SQL script in Snowflake that, among other things, created a stage and external volume. These two items will need to be mapped to a storage location in Coalesce so our packages can work with these objects.

1. To add storage locations, navigate to the left side of your screen and click on the Build settings cog.

    ![image27](./assets/image27.png)

2. Click the “Add New Storage Locations” button and name it STORE representing the data coming from your restaurant.

    ![image28](./assets/image28.png)

3. Now map your storage location to their logical destinations in Snowflake. In the upper left corner next to your Workspace name, click on the pencil icon to open your Workspace settings. Click on Storage Mappings and map your STORE location to the **MARKETPLACE_HOL** database and the **STORE** schema. Select Save to ensure Coalesce stores your mappings.

    ![image29](./assets/image29.png)

4. Go back to the build settings and click on Node Types and then click the toggle button next to View to enable View node types. Now you’re ready to start building your pipeline.

    ![image30](./assets/image30.png)

## Adding Data Sources

1. In the Browser within the Build Interface, select the + button in the upper left corner of the screen

    ![image31](./assets/image31.png)

2. Select Add Sources. This will open the data sources modal which will display all of the obects available within each storage location you have configured.

    ![image32](./assets/image32.png)

3. Within the STORE Storage Location that you configured in the previous step, you will see four tables available. Select all four of the tables and select **Add 4 Sources**

    ![image33](./assets/image33.png)

4. There is an additional data source that is a JSON file that exists in an AWS S3 Bucket. To obtain this data source, we'll use our first Marketplace package. Select the + button again in the upper left corner and navigate to Create New Node -> EDP -> Copy Into.

    ![image34](./assets/image34.png)

5. This will add a Copy Into node into your graph and immediately place you in the node. Rename the node to **CUSTOMER_REVIEWS**.

    ![image35](./assets/image35.png)

6. On the right side of the node, open the Source Data dropdown within the Config Settings of the node.

    ![image36](./assets/image36.png)

7. Toggle the Internal or External Stage toggle to on.

    ![image37](./assets/image37.png)

8. Now you'll need to confiugre each of the parameters listed. For the Coalesce Storage Location of Stage, you will list the **STORE** storage location, as this is the database and schema that each object from the setup script was created within.

    ![image38](./assets/image38.png)

9. For the Stage Name, you will use the name of the stage created in the setup script: **store_data**

    ![image39](./assets/image39.png)

10. For the Path or Subfolder, you will pass through a path called **json** which is the folder containing the json data we wish to load.

    ![image40](./assets/image40.png)

11. For the File Name(s), include the file name, which is named **customer_reviews.json**.

    ```JS
    customer_reviews.json
    ```

    ![image41](./assets/image41.png)

12. You do not need to include anything for the file pattern. Open the **File Format** dropdown next.

13. You will keep the File Format Definition as **File Format Name**. For the Coalesce Storage Location, you will again use the **STORE** storage location.

    ![image42](./assets/image42.png)

14. For the File Format Name, use the file format created in the setup script called **JSONFORMAT**

    ![image43](./assets/image43.png)

15. As already discussed, the File Type is JSON, so select that from the File Type dropdown.

    ![image44](./assets/image44.png)

16. Once complete, Create and Run the node.

    ![image45](./assets/image45.png)

## Creating Stage Nodes

Now that you have your data sources added into Coalesce, we can begin processing all of the data by building a preparation layer for the rest of our data pipeline. Specifically, we'll use some stage nodes to accomplish this for several of our tables.

1. Because Coalesce uses nodes which represent templates or standards of objects, you can easily apply the same standard over and over again. Using the shift key, select the **CUSTOMERS**, **MENU**, and **CUSTOMER_REVIEWS** nodes and right click on either of them and select Add Node -> Stage.

    ![image46](./assets/image46.png)

2. Coalesce will automatically create stage nodes for each of the data sources. Double click on the **STG_CUSTOMER_REVIEWS** node to open it.

    ![image47](./assets/image47.png)

3. You'll see that there is a VARIANT column containing all of the JSON data we loaded int the previous node. Coalesce provides a simple and powerful solution for parsing JSON and XML strings. Right click on the **SRC** column and select Derive Mappings -> From JSON.

    ![image48](./assets/image48.png)

4. Coalesce will split out each of the key value pairs into their own columns with the associated data type. With the name columns available, we no onger need the original columns from the Copy Into node. Select the **SRC** column, hold down the shift key, and select the **SCAN_TIME** column. Right click on either of these columnes and select Delete Columns.

    ![image49](./assets/image49.png)

5. You can apply data transformations at any point in Coalesce. Let's apply some column level transformations to these remaning columns. You may have noted that all of the columns names in other nodes are all upper case. To ensure consistency, let's do that to these columns as well. Again, using the shift key, select all of the columns, and right click on any column and select Bulk Edit.

    ![image50](./assets/image50.png)

6. The bulk editor will open and all of the attributes available to be edited will be displayed. In this case, we'll choose **Column Name**.

    ![image51](./assets/image51.png)

7. The SQL editor will be displayed, which allows you to write any SQL that will be applied to all of the columns. In this case, we'll use an identifier that allows Coalesce to resolve the SQL statement to each column name, while applying an UPPER function.

    ```SQL
    {{ column.name | upper }}
    ```

    ![image52](./assets/image52.png)

8. With your SQL written in the SQL editor, select Preview to view the changes that Coalesce will make in bulk to your columns. Select **Update** to apply the changes.

    ![image53](./assets/image53.png)

9. With your updates made, Create and Run the node to apply the changes to your object.

    ![image54](./assets/image54.png)

10. You can also apply single column level transformations. Back in the Browser, double click into the **STG_CUSTOMERS** node.

    ![image55](./assets/image55.png)

11. Let's create a new column and apply a transformation that allows us to determine the email domain of each of our customers. Double click on the **Column Name** at the bottom of the mapping grid. Call the column **EMAIL_DOMAIN**.

    ![image56](./assets/image56.png)

12. Next, you'll need to supply a data type, in this case, use the ```VARCHAR(50)``` data type and input this into the mapping grid.

    ![image57](./assets/image57.png)

13. Now let's transform this column. To obtain the email domain, you can use the following SQL to the Transform column to apply the transformation.

    ```SQL
    SPLIT_PART("CUSTOMERS"."EMAIL", '@', 2)
    ```

    ![image58](./assets/image58.png)

14. Create and Run all of the Stage Nodes to build and populate them with data in Snowflake.

## Using Dynamic Table Nodes

For the rest of the staging layer, you will use Dynamic Tables to transform your data while leveraging real-time pipeline updates to your data. Let's begin.

1. Using the shift key, select the **ORDERS** and **ORDER_DETAIL** tables, right click on either node and select Add Node -> Dynamic-Tables -> Dynamic Table Work Node. Coalesce will automatically add a Dynamic Table Work node to each data source.

    ![image59](./assets/image59.png)

2. Next, when using the Dynamic Table package, you need to use a parameter to configure the Dynamic Table warehouse. To do this, navigate to your workspace settings by clicking the gear icon in the upper left corner.

    ![image60](./assets/image60.png)

3. Select Parameters, and copy and paste the following code into the Parameters editor. Select Save once complete.

    ![image61](./assets/image61.png)

    ```JS
    {
    "targetDynamicTableWarehouse": "DEV ENVIRONMENT"
    }
    ```

4. Navigate back to the Browser and double click on the **DT_WRK_ORDERS** table.

    ![image62](./assets/image62.png)

5. Select the Dynamic Table Options dropdown on the right side of the node.

    ![image63](./assets/image63.png)

6. For the Warehouse on which to execute Dynamic Table, input the warehouse that is available in your Snowflake account, or was created when running the setup script called **compute_wh**.

    ![image64](./assets/image64.png)

7. Next, turn on the Downstream toggle to activate the ability for the table to automatically refresh based on the schedule of a downstream table refresh.

    ![image65](./assets/image65.png)

8. Finally, in the General Options dropdown, toggle on the Distinct toggle to ensure only distinct order records are procesed.

    ![image66](./assets/image66.png)

9. Select Create to create the Dynamic Table.

    ![image67](./assets/image67.png)

10. We'll configure the **DT_WRK_ORDER_DETAILS** node the same way.

    ![image68](./assets/image68.png)

11. Additionally, for the **DISCOUNT_AMOUNT** column, we'll apply some logic to simplify our discount policy. Use the following code to apply CASE WHEN logic to the column.

    ![image69](./assets/image69.png)

    ```SQL
    CASE WHEN "ORDER_DETAIL"."DISCOUNT_AMOUNT" > 50 THEN 10 ELSE 1 END
    ```

12. Select Create to create the Dynamic Table.

## Joining Nodes Together

Now that you have built your processing layer, it's time to join some of these objects together to prepare data for further analysis.

1. Using the shift key, select the STG_CUSTOMERS and STG_CUSTOMER_REVIEWS nodes and right click on either node and select Join Nodes -> Stage.

    ![image71](./assets/image71.png)

2. This will create a new stage node which you will be placed within. To configure the join, navigate to the Join tab in the upper left corner of the mapping grid.

    ![image72](./assets/image72.png)

3. Coalesce will automatically infer as much of the join as possible, but you will need to provide the join condition. In this case, you will be joining on CUSTOMER_ID from both nodes. You can either manually confiugre this, or copy and paste the code provided

    ![image73](./assets/image73.png)

    ```SQL
    FROM {{ ref('WORK', 'STG_CUSTOMER_REVIEWS') }} "STG_CUSTOMER_REVIEWS"
    INNER JOIN {{ ref('WORK', 'STG_CUSTOMERS') }} "STG_CUSTOMERS"
    ON "STG_CUSTOMER_REVIEWS"."customer_id" = "STG_CUSTOMERS"."CUSTOMER_ID"
    ```

4. Now that you have provided the join condition, rename the node to STG_CUSTOMER_MASTER.

    ![image74](./assets/image74.png)

5. Navigate back to the mapping grid and delete one of the CUSTOMER_ID columns, as an object can't contain duplicate column names.

    ![image75](./assets/image75.png)

6. Create and Run the node to create and populate the object.

    ![image76](./assets/image76.png)

7. Next, let's join the Dynamic Table nodes together. We want this to be a real-time pipeline, so we'll use another Dynamic Table Work Node to join our nodes together. Select the DT_WRK_ORDERS and DT_WRK_ORDER_DETAIL nodes and right click on either node and select Join Nodes -> Dynamic-Tables -> Dynamic Table Work.

    ![image77](./assets/image77.png)

8. You'll be placed inside of the new Dynamic Table node. Just as we did with the previous stage node, we can configure the join of this node exactly the same way. Navigate to the Join tab and, this time, we'll use ORDER_ID as the join condition. Which you can provide manually, or copy and paste the following code.

    ![image78](./assets/image78.png)

    ```SQL
    FROM {{ ref('WORK', 'DT_WRK_ORDERS') }} "DT_WRK_ORDERS"
    INNER JOIN {{ ref('WORK', 'DT_WRK_ORDER_DETAIL') }} "DT_WRK_ORDER_DETAIL"
    ON "DT_WRK_ORDERS"."ORDER_ID" = "DT_WRK_ORDER_DETAIL"."ORDER_ID"
    ```

9. Rename the node to DT_WRK_ORDER_MASTER.

    ![image79](./assets/image79.png)

10. Navigate back to the mapping grid and remove one of each of the ORDER_ID and ORDER_DETAIL_ID columns.

11. In the Dynamic Table Options dropdown, supply the warehouse you want this Dynamic Table to use. Again, we'll use **compute_wh**.

    ![image81](./assets/image81.png)

12. For this Dynamic Table, leave the Downstream toggle off. Instead, we'll schedule this Dynamic Table to update ever 5 minutes. In the Lag Specification parameter, input 5 as the Time Value. For the Time Period, choose Minutes from the dropdown.

    ![image82](./assets/image82.png)

13. Select Create to create the Dynamic Table object. You've now configured a pipeline of order data updating every 5 minutes.

    ![image83](./assets/image83.png)

## Processing Real Time Data

You now have an order master table, producing data that is cleaned and unified. However, there is still more that can be done to allow your data team to process this data, especially large amounts of this data, in an efficient manner.

1. Currently, you have a pipeline of Dynamic Tables updating every 5 minutes. You can use a view node to query this data as it is updating, so your entire team has insight into this data. To do so, right click on the DT_WRK_ORDER_MASTER node and select Add Node -> View. Create the Veiw.

    ![image84](./assets/image84.png)

2. In an environment where data is updating in real-time, transactional tables containing data like orders data can become quite large and it is unrealistic to processes all of the data in the table every time it updates. In these situations, you can use incremental data loading. Let's learn how to do this by incrementally processing the data from your Dynamic Table pipeline, which only contains the last 30 days worth of data.

    Right click on the DT_WRK_ORDER_MASTER node and select Add Node -> Incremental -> Incremental Load.

    ![image85](./assets/image85.png)

3. Incremental Load Nodes require you to have your data persisted down stream so that the node can incrementally load data into a table that has persisted data. Select the Create button in the Incremental Node you just created.

    ![image86](./assets/image86.png)

4. Next, you need to create a table to persist the data from the incremental node. Right Click on the INC_ORDER_MASTER node in the Browser and select Add Node -> Persistant Stage.

    ![image87](./assets/image87.png)

5. Using the options dropdown on the right side of the node, you use a business key to identify each order. In this case, it is a composite key of ORDER_ID and ORDER_DETAIL_ID.

    ![image88](./assets/image88.png)

6. Once configured, Create and Run the node to buid the object.

    ![image89](./assets/image89.png)

7. With the persistant table created, you can finish configuring the incremental node you just created. Back in the Browser, double click on the INC_ORDER_MASTER tabe you created.

    ![image90](./assets/image90.png)

8. Open the configuration options of the node on the right side of the screen and toggle on Filter data based on Persistent table. This will allow you to configure the node to incrementally filter and process data.

    ![image91](./assets/image91.png)

9. Pass through the Persistent Table storage location to the incremental node, which in this case, is called **WORK**.

    ![image92](./assets/image92.png)

10. Then, pass the persistent table name through as the table name parameter, called **PSTG_ORDER_MASTER**.

    ![image93](./assets/image93.png)

11. Finally, you'll need to supply the data column used for incremental loading in the selector dropdown. In this case, choose **ORDER_TS**

    ![image94](./assets/image94.png)

12. Once complete, navigate to the Join tab of the node and delete the line of code in the SQL editor.

    ![image95](./assets/image95.png)

13. In the upper right corner of the SQL editor, you'll see the Generate Join tool. Select Generate Join and you'll see severa lines of SQL that Coalesce has automatically generated. This is the exact SQL needed to incrementally process your data based on the parameters that were just supplied to the node.

    ![image96](./assets/image96.png)

14. Select **Copy to Editor** to copy the code into the SQL editor for you to reconfigure the dependency of the node as well as supply the incremental logic for the node.

    ![image97](./assets/image97.png)

15. Once this is complete, Run the node. Now you have a view that is processing data incrementally and loading that incremental data into a persistent table.

    ![image98](./assets/image98.png)

## Creating a type 2 slowly changing dimension

So far, you've spent your time building pipelines with some of the more exciting packages from Coalesce Marketplace. But in the real world, not every use case needs you to use functionality like this. What happens when you need to create objects from standard requests, like creating Type 2 Slowly changing dimensions? Coalesce supports this functionality out of the box, without you having to write a single line of code.

1. In the Browser, right click on the STG_MENU node and select Add Node -> Dimension.

    ![image99](./assets/image99.png)

2. Select the options dropdown within the configuration on the right side of the screen.

    ![image100](./assets/image100.png)

3. You are required to supply a business key for a dimension node to work. In this case, we'll use a composite key of MENU_ID and MENU_ITEM_ID.

    ![image101](./assets/image101.png)

4. Next, to configure a Type 2 Slowly Changing Diemnsion (SCD), select the columns you want to have changes tracked on. For this lab, choose the ITEM_NAME column to track changes on.

    ![image102](./assets/image102.png)

5. Now Create and Run the node. Once you Run the node, view the code that was automatically generated for you in the Results panel.

    ![image103](./assets/image103.png)

## Using Cortex Functions

You've processed your orders data and have built some nodes around your customer data, but now it's time to circle back to the STG_CUSTOMER_MASTER table to gain some more insights our of this data. Primarily, we want to generate a sentiment score for each of our customers, based on the reviews they have left us. Let's learn how to do this.

1. In the Browser, right click on the STG_CUSTOMER_MASTER node and select Add Node -> Cortex -> Cortex Functions.

    ![image104](./assets/image104.png)

2. In the Cortex Package options on the right side of the node, select the dropdown.

    ![image105](./assets/image105.png)

3. Toggle on the SENTIMENT toggle.

    ![image106](./assets/image106.png)

4. All Coalesce requires from you is to supply the column you want to generate a sentiment score from. In the mapping grid, select the **REVIEW_TEXT** column, right click on it, and select Duplicate Column.

    ![image107](./assets/image107.png)

5. Double Click on the new column name and rename it to **REVIEW_SENTIMENT**.

    ![image108](./assets/image108.png)

6. With a new column available to use for our sentiment score, we can keep the original text. In the Column Name dropdown in the SENTIMENT toggle, select the **REVIEW_SENTIMENT** column.

    ![image109](./assets/image109.png)

7. Create and Run the node to view the results and see how easy Coalesce makes it to work with Cortex functions in Snowflake.

    ![image110](./assets/image110.png)

## Creating aggregate FCT node

Now that you have an object that is creating a sentiment score about your customers reviews, the next thing you will do is create a Fact table that will store the measures about customers: in this case average review and average sentiment. Let's learn how to do this.

1. If it's not still open, double click into the LLM_CUSTOMER_MASTER node you created in the previous section.

    ![image111](./assets/image111.png)

2. Holding the `command` or `windows` key, select the **CUSTOMER_ID**, **REVIEW_SENTIMENT**, and **STAR_RATING** columns in the mapping grid.

    ![image112](./assets/image112.png)

3. Right click on either of the highlight columns and select Add Node -> Fact. Coalesce will automatically create a new node that contains just these three columns.

    ![image113](./assets/image113.png)

4. We want to apply aggregate functions to this data to determine average sentiment score and star rating, as some customers have reviewed multiple menu items from our restaurant. You can use the same function to apply this transformation. For the **REVIEW_SENTIMENT** column, double click into the **Transform** column and supply the SQL statement here:

    ![image114](./assets/image114.png)

    ```SQL
    AVG({{SRC}})
    ```

5. Apply the same transformation to the **STAR_RATING** column

    ![image115](./assets/image115.png)

    ```SQL
    AVG({{SRC}})
    ```

6. Since you are using aggregate functions in an object, you will need to supply a **GROUP BY**. Navigate to the Join tab, and add a new line to the SQL editor. Add the SQL code here:

    ![image116](./assets/image116.png)

    ```SQL:
    GROUP BY ALL 
    ```

7. Create and Run the node to build the object and populate it with data.

    ![image117](./assets/image117.png)

## Reporting on our data

So far, you've used packages from Coalesce Marketplace to create a pipeline that lerverages different functionality that is fully managed by the nodes you've added to the pipeline. You've also created various objects that can be joined together to provide a holistic view of your data. Let's create a reporting object that brings together your order data, menu data, and customer data.

1. Holding down the shift key, in the browser, select the **PSTG_ORDER_MASTER**, **FCT_CUSTOMER_MASTER**, and **DIM_MENU** nodes (**MAKE SURE TO SELECT THE NODES IN THE ORDER LISTED HERE**). Right click on any of the selected nodes and select Join Nodes -> View.

    ![image118](./assets/image118.png)

2. Coalesce will place you in the node. Rename the node **V_REPORT_MASTER**.

    ![image119](./assets/image119.png)

3. Next, navigate to the join tab and configure manually, or use the following SQL to complete the join condition:

    ![image120](./assets/image120.png)

    ```SQL
    FROM {{ ref('WORK', 'PSTG_ORDER_MASTER') }} "PSTG_ORDER_MASTER"
    INNER JOIN {{ ref('WORK', 'FCT_CUSTOMER_MASTER') }} "FCT_CUSTOMER_MASTER"
    ON "PSTG_ORDER_MASTER"."CUSTOMER_ID" = "FCT_CUSTOMER_MASTER"."CUSTOMER_ID"
    LEFT JOIN {{ ref('WORK', 'DIM_MENU') }} "DIM_MENU"
    ON "PSTG_ORDER_MASTER"."MENU_ITEM_ID"= "DIM_MENU"."MENU_ITEM_ID"
    ```

4. Next, select the Column Name header to alphanumerically sort the column names in the node. Using the shift key, select all of the ```SYSTEM_``` columns and delete them from the node.

    ![image121](./assets/image121.png)

5. Next, you will need to remove any duplicate columns names from the node as an object cannot contain duplicate column names. Remove one of the columns for each of the following column names:
    * CUSTOMER_ID
    * ITEM_NAME
    * MENU_ITEM_ID

    ![image122](./assets/image122.png)

6. Select the Create button to create the view.

    ![image123](./assets/image123.png)


## Conclusion And Resources

Congratulations on completing your lab. You've mastered working with Coalesce Marketplace and extending the functionality of your data pipelines. Be sure to reference this exercise if you ever need a refresher.

We encourage you to continue working with Coalesce by using it with your own data and use cases and by using some of the more advanced capabilities not covered in this lab.

### What You Learned
* How to navigate the Coalesce interface
* Configure storage locations and mappings
* How to add data sources to your graph
* How to prepare your data for transformations with Stage nodes
* How to join tables
* How to apply transformations to individual and multiple columns at once
* How to build real-time data pipelines and work with Dynamic Tables
* How to configure and understand Cortex functions node

### Related Resources
* [Getting Started](https://coalesce.io/get-started/)
* [Documentation](https://docs.coalesce.io/docs) & [Quickstart Guide](https://docs.coalesce.io/docs/quick-start)
* [Video Tutorials](https://fast.wistia.com/embed/channel/foemj32jtv)
* [Help Center](mailto:support@coalesce.io)

Reach out to our sales team at [coalesce.io](https://coalesce.io/contact-us/) or by emailing [sales@coalesce.io](mailto:sales@coalesce.io) to learn more.
