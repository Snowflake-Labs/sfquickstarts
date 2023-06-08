author: Kelsey Hammock
id: snowflake_build_secure_multitenant_data_applications_snowflake_sigma
summary: Snowflake Summit 2023 HoL with Sigma
categories: Snowflake
environments: web
status: Published
feedback link: https://github.com/sigmacomputing/sigmaquickstarts/issues
tags: Snowflake, Sigma

# Build and Secure Multi-Tenant Data Applications with Snowflake and Sigma
<!-- The above name is what appears on the website and is searchable. -->

## Overview 
Duration: 5 


Whether you are a global retailer, a tech company, or a financial services firm, providing near real-time embedded analytics to your external users can help optimize your operations, improve your product conversion, drive new lines of revenue, and more. 

This Sigma and Snowflake lab is designed to teach you how to build customer facing analytics applications that allow your end users to dive deeper and go further with data. 

 ### Target Audience
Data Analysts, Business Analysts, or others who are doing next level analysis on their data in Sigma. No SQL is required for this lab, but the concepts do get technically complex.

### Prerequisites

<ul>
  <li>A computer with a current browser. It does not matter which browser you want to use.</li>
  <li>A Snowflake trial account with Enterprise Edition or higher.</li>
</ul>

[Snowflake Free Trial](https://signup.snowflake.com/)

Once you have created your Snowflake trial environment, you will need to complete the data loading and object creation steps found in the Snowflake Tasty Bytes Quickstart, which you can access here: [An Introduction to Tasty Bytes.](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html?index=..%2F..index#0)

<aside class="postive">
<strong>NOTE:</strong><br> You do not need a Sigma instance prior to starting this lab as one will be provisioned during the course of this lab.
</aside>


  
### What You’ll Learn
In this lab you’ll learn how to:

 <ul>
      <li>Build an interactive, embeddable dashboard with unique drill down capabilities using Snowflake and Sigma</li>
      <li>Explore data sets using Sigma’s unique UI</li>
      <li>Leverage column & row-level security policies to secure data in Snowflake</li>
      <li>Dynamically assign Snowflake Role & Warehouse using Sigma User Attributes</li>
      <li>Analyze engagement across customer demographics</li>
      <li>See the end user experience in data products built on Sigma & Snowflake</li>
</ul>



![Footer](assets/sigma_footer.png)
<!-- END OF OVERVIEW -->

## Setting up the Lab Environment
Duration: 16

2.1 After setting up your trial, log into Snowflake.

2.2 From the Snowflake home page click `Worksheets` then `+` button and select `SQL Worksheet`:

<img src="assets/ss1.png" width="500"/>

2.3 Copy and Paste the following code into  your new SQL worksheet:
```console 
USE ROLE TASTY_ADMIN; 
USE WAREHOUSE TASTY_BI_WH;
USE DATABASE FROSTBYTE_TASTY_BYTES;
USE SCHEMA HARMONIZED;
ALTER WAREHOUSE TASTY_BI_WH SET WAREHOUSE_SIZE = 'MEDIUM';
ALTER WAREHOUSE TASTY_DATA_APP_WH SET WAREHOUSE_SIZE = 'MEDIUM';

---CREATE TABLE FROM VIEW---

CREATE OR REPLACE TABLE ORDERS AS SELECT * FROM ORDERS_V;
```

2.4 Now that the SQL is in your worksheet, execute the code by placing your cursor in each line and hitting `Command + Enter`. You may also execute the code by selecting the blue arrow in the top right corner of the worksheet and selecting `Run All`.

2.5 While the SQL executes, navigate back to the Snowflake homepage by `clicking the home icon`, then navigate to the `Admin tab`. Select `Partner Connect` under the Admin tab, then click to select `Sigma`.

<img src="assets/ss3.png" width="600"/>

2.6 You will now see a pop up explaining the objects that will be created as part of spinning up a new Sigma instance. Click the blue `Connect` button. 

<img src="assets/ss4.png" width="500"/>

2.7 Click `Activate`:

<img src="assets/ss5.png" width="600"/>

2.8 You will be prompted to input a company name for your URL. You may choose whatever you feel best fits. 

<img src="assets/ss6.png" width="600"/>

2.9 Then complete the steps to create a user and password for yourself. 

2.10 Finally, select `Get Started Using Sigma`.

<img src="assets/ss7.png" width="500"/>

2.11 If this was done correctly, you should now see the Sigma home page. Bookmark this page for easy access later in the lab:

<img src="assets/ss8.png" width="800"/>

2.12 In the top right corner, select your `name`, then select `Administration.`

<img src="assets/ss9.png" width="400"/>

2.14 From the left-hand panel, select `Connections`, then click the new connection that was created for you through partner connect. It should read something like `Snowflake PC_SIGMA_WH`:

<aside class="negative">
<strong>NOTE:</strong><br> This is not the Sigma Sample Database Connection. 
</aside>

<img src="assets/ss10.png" width="600"/>

2.15 Select `Edit` in the top right on the connection page:

<img src="assets/ss11.png" width="700"/>

2.16 Adjust the connection so that the warehouse is `TASTY_BI_WH`, the role is `TASTY_ADMIN` and the User is **YOUR** Snowflake User name. Enter your Snowflake password and click `Save`.  You may adjust the connection name if you so choose as well. 

Upon save, Sigma will validate the connection is reachable.

<img src="assets/ss12.png" width="600"/>

 2.17 Click the `paper crane` icon in the top left to return to the Sigma homepage:

<img src="assets/ss13.png" width="600"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Setting up the Workbook
Duration: 16

3.1 From the home page select `Create New` then select `Workbook`:

<img src="assets/ss14.png" width="400"/>

3.2 In the left-hand pane, select `Add New` then click `Table.`:

<img src="assets/ss15.png" width="400"/>

3.3 Next, select `Tables and Datasets.`:

<img src="assets/ss16.png" width="400"/>

3.4 For your source, select `Connections`, then choose the connection we created earlier. If you did not choose to rename it, it should be labeled something like `Snowflake  PC_SIGMA_WH.`:

<img src="assets/ss17.png" width="400"/>

3.5 When you have found the connection, expand the `FROSTBYTE_TASTY_BYTES` database, and select the `Orders` table from the Harmonized Schema.:

<img src="assets/ss18.png" width="400"/>

<aside class="negative">
<strong>NOTE:</strong><br> This is different than the Orders_V view.
</aside>

3.6 You will notice that Sigma populates a preview of the table you have selected. On this interface, you have the ability to select which columns from the table you would like to bring into the workbook table. De-select `Customer Id, First Name, Last Name, Email, Phone Number, Children Count, Marital Status, Order Tax Amount, and Order Discount Amount`. You will not need these columns for the purpose of this lab. 

Then Click `Select` in the bottom right corner:

<img src="assets/ss19.png" width="800"/>

3.7 Rename the table by clicking on the title `Orders`, and rename it to `Orders Base Table`:

<img src="assets/ss20.png" width="600"/>

<aside class="positive">
<strong>IMPORTANT:</strong><br> In Sigma, it is best practice to begin with base elements, and build child elements like visualizations from there. 
</aside>

3.8 Select the drop down arrow to the right of the `Order Ts` Column. Select `Truncate Date`, then choose `Day`. 

This will change the formatting to show the timestamp as just the year, month, and day of the timestamp:

<img src="assets/ss21.png" width="400"/>

3.9 Double click the column name and rename `Purchase Date`:

<img src="assets/ss22.png" width="400"/>

3.10 Scroll through the Orders Base Table to the right until you locate the `Unit Price, Price, Order Amount, and Order Total` columns. Use `Shift + Click` to select all 4 columns, then hit the `Format As Currency` (or Dollar Sign) button on the top formula bar to format these columns as currency:

<img src="assets/ss23.png" width="800"/>

3.11 Now we will add another table to the `Workbook Page`.

Click the `plus sign` in the left hand pane to add a new element, and select `Table`. Click the tab for `New` then select `Tables and Datasets`. 

This time, you are looking for the `Menu` table in the `RAW_POS` schema within the `FROSTBYTE_TASTY_BYTES` database. We only want the columns `Menu Item ID and Cost of Goods Usd`. Click `Select` when done. 

<img src="assets/ss25.png" width="800"/>

3.12 We now have two tables on the page and we want to create a relationship between them.

On your `Orders Base Table`, scroll all the way to the far right column `Order Total`, then click the drop down arrow. Select `Add column via lookup`.

<img src="assets/ss26.png" width="400"/>

3.13 From the drop down, select `MENU` as the element, and `Cost of Goods Usd` as the column to add. Map the elements on `Menu Item Id`, then click `Done`:

<img src="assets/ss27.png" width="400"/>

3.14 With the `Cost of Goods Usd (Menu)` column still selected, click the `Format as Currency` button once again to format the cost as a currency.

<img src="assets/ss28.png" width="800"/>

3.15 Click the arrow next to `Cost of Goods Used (MENU)` and select `Add new column`:

<img src="assets/ss29.png" width="400"/>

3.16 In the formula bar, type `[Quantity] * [Cost of Goods Usd (MENU)]` and hit enter. 

This will create a new calculated column. Name this column `COGS` (Cost of Goods Sold) 

<img src="assets/ss30.png" width="800"/>

3.17 Click the drop down by the newly created `COGS` column. Select `Add a new Column`. This time, type `[Price]-[COGS]` and hit Enter. Name this new column `Profit`:

<img src="assets/ss30a.png" width="600"/>

3.18 Scroll through the Orders Base Table until you find the `Truck Brand Name` column. Click the arrow to open the drop down, then select `Group Column`:

<img src="assets/ss31.png" width="600"/>

3.19 Now that we have brought in our base elements, click the `Save As` button in the top right corner and save your workbook as `Tasty Bytes Sales Portal`:  

<img src="assets/ss32.png" width="600"/>

3.20 Now, double click on `Page 1` in the bottom left corner. Rename the page `Data`: 

<img src="assets/ss33.png" width="600"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Building the Workbook 
Duration: 16

Now that we have created our base data elements and saved the first version of our workbook, we are ready to move on to building the visualizations for our sales portal. 

4.1 Hover over the upper right hand corner of the `Orders Base Table`, then select the icon for `Create Child Element` and select `Visualization` from the drop down:

<img src="assets/ss34.png" width="600"/>

This places a empty visualization on the page.

4.2 On the left hand pane, drag `Region to X-Axis`, then drag `Profit to the Y-Axis`. 

You will notice Sigma automatically performs the aggregation for profit, formatting it as `Sum of Profit`:

<img src="assets/ss35.png" width="600"/>

4.3 Double click the title for your new bar chart and rename it `Profit by Region`:

<img src="assets/ss36.png" width="600"/>

4.4 Now click the `three dot icon` in the top right of the new visualization. From the drop down, select `Move to` then `New Page`:

<img src="assets/ss37.png" width="400"/>

You will see your bar chart has now been moved to a separate page than the data sets.

Lets create another visualization using the same workflow.

4.5 Back on the `data` page, repeat the process of creating a `child visualization` from the `Orders Base Table` by hovering over the top right corner, selecting `Create Child Element`, then `Visualization`.

4.6 On the left hand menu, change the visualization type to a Line chart by selecting `Line` from the drop down menu where you initially see Bar.

4.7 Drag `Purchase Date to the X-Axis`. 

4.8 Once you have placed it there, click the arrow to the right of `Purchase Date`, select `Truncate Date`, then `Month`. 

This will group our values based on the purchase month rather than the individual purchase date. 

<img src="assets/ss38.png" width="600"/>

4.9 `Drag in Order Id to the Y-Axis`. Select the drop down arrow and go to `Set Aggregate -> CountDistinct`. 

This will give us the count of distinct orders over time:

<img src="assets/ss39.png" width="600"/>

4.10 Rename this visual `Orders by Month`.

4.11 You will notice a sharp decline in orders on the far right of the line graph. This is because our data set does not include the orders for the full month of November 2022. Right Click the furthest right data point, and select `Exclude 2022-11` to remove the sharp drop off from our visualization. 

<img src="assets/ss40.png" width="400"/>

4.12 Move this element to the page you placed your bar chart on earlier. 

4.13 On the `Orders base table`, locate the `Purchase Date` column, and select `Filter` from the drop-down.

<img src="assets/ss41.png" width="600"/>

No need to set a date range right now so just click away from the calendar to make disappear.

4.14 On the new `Filters & Controls` pane, click the `three dots` to the right of the filter. Select `Convert to page control` from the dropdown menu. 

<img src="assets/ss42.png" width="600"/>

4.15 Move this new Control element to the page with your visualizations. 

<aside class="negative">
<strong>NOTE:</strong><br> You can drag page elements around to reorder them and also change their size. Drag the filter control to the top of the visualizations pages to make it easy for users to set filters.
</aside>

4.16 One last time, return to the `Orders Base Table` and select `Create Child Element`. This time, select `Pivot Table` from the drop down. 

4.17 Drag `Truck Id` to Pivot Rows, `Purchase Date` to Pivot Columns, and `Profit` and `COGS` to values. 

4.18 Select the arrow to the right of Purchase Date, and truncate to the year.

<img src="assets/ss43.png" width="800"/>

<aside class="negative">
<strong>NOTE:</strong><br> I may take a a moment for the data to appear as there are almost 700M rows in the "Orders Base Table".
</aside>

4.19 Double click on `Sum of Profit` on the left hand pane and rename to `Profit`. Repeat the same for `Sum of COGS`, renaming it `COGS`.

4.20 Rename the pivot table `Yearly Profit & Cost by Truck`:

<img src="assets/ss44.png" width="600"/>

4.21 With the pivot table selected, click on the `paintbrush `in the left hand pane, then click `Conditional Formatting`:

<img src="assets/ss45.png" width="600"/>

4.22 On the Apply to drop down, select `Profit` as the column to apply formatting to. 

Then select `Color Scale` as the formatting type:

<img src="assets/ss46.png" width="600"/>

4.23 Finally, `move the pivot table` to the new page you created for your visualizations. 

4.24 On the visualizations page, double click where you see `Page 1` in the bottom left hand corner and rename the page to `Dashboard`. 

4.25 Click the plus sign in the top left corner of the page for Add New. Then select `Viz`.

<img src="assets/ss47.png" width=" 400"/>

4.26 For the data source for the new visualization, select `ORDERS BASE TABLE` from the `Workbook Elements` field:

<img src="assets/ss48.png" width="400"/>

4.27 Under visualization, change the type to `KPI`. Then drag `Truck Id` to the Value field:

<img src="assets/ss49.png" width="400"/>

4.28 To the right of Sum of Truck Id, select the drop down and `change the aggregate to CountDistinct`:

<img src="assets/ss50.png" width="400"/>

4.29 With the KPI selected, click the `decrease decimal button` in the top formula bar until you see the total count of trucks with no decimal places:

<img src="assets/ss51.png" width="400"/>

4.30 Finally, double click `CountDistinct of Truck Id` in the left hand pane, and rename the value to `Number of Trucks`: 

<img src="assets/ss52.png" width="400"/>

4.31 Repeat the process to create another KPI Visualization from the `Orders Base Table`, but this time, drag `Order Id` to the value. Set the aggregate to `CountDistinct`, decrease the decimal places, set the datatype to `number` (under the "123" icon) and rename the field `Number of Orders`. 

Your KPI tile should look like this: 

<img src="assets/ss53.png" width="600"/>

4.32 Drag your visualizations to rearrange them so that your KPIs are side by side at the top, your control element is below them, the bar & line charts are side by side below that, with the pivot table at the bottom so that your page looks like this: 

Don't worry if you make a mistake; you can always just go back by clicking the `back icon` as shown by the red arrow:

<img src="assets/ss54.png" width="800"/>

4.33 Once again select the plus sign in the left hand panel to add a new element. This time, select `Text`. 

<img src="assets/ss55.png" width="400"/>

4.34 Drag your new text element to the top of the page. 

4.35 In the text box type the `=` sign and a formula bar will appear. Copy and paste this formula into the formula bar:
```console
If(CountDistinct([Orders Base Table/Truck Brand Name]) >1, “Tasty Bytes”, [Orders Base Table/Truck Brand Name])
```

<img src="assets/ss56.png" width="600"/>

4.36 Click the green checkmark after completing the formula, then type `Sales Performance`to the right of the dynamic text bubble. 

4.37 Format your new text element as a `Large Heading` and center on the page:

<img src="assets/ss57.png" width="600"/>

4.38 Click the `gear icon` in the bottom corner to open the `Workbook Settings` menu:

<img src="assets/ss58.png" width="600"/>

4.39 Uncheck the box for `Show Cards`:

<img src="assets/ss59.png" width="400"/>

4.40 We don't want end-users to see the Data tab, so we will make that hidden for them. It will still be available to you, but not others who do not have the correct permissions to see it.

From the drop down next to the data page, click `Hide`:

<img src="assets/ss60.png" width="400"/>

4.41 Our work was being auto-saved as `Draft` as we made each change. We can now change the state of the Workbook to `Published`.

Click the blue `Publish` button in the top right corner.

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Setting up Security 
Duration: 16

Now that we have created our workbook, we need to set up the security permissions on the data set and the workbook itself. 

5.1 Navigate back to your Snowflake instance and the worksheet you created earlier in this lab. 

5.2 Once you have navigated back to your Snowflake worksheet, copy and paste the following SQL into your worksheet:

<aside class="negative">
<strong>NOTE:</strong><br> These statements will be executed one at a time by placing your cursor in the statement line and hitting “Command + Enter” or the play button in the top right hand corner of the Snowflake UI. Detail on what each statement is doing is provided just after the codeblock under "What the script is doing". You may find it useful to read along as you run each statement in the set.
</aside>

You will have to modify this code to set the username to your Snowflake username:

<img src="assets/ss61.png" width="800"/>

```console
---SET DATABASE TO BE USED ---
USE ROLE TASTYADMIN;
USE DATABASE FROSTBYTE_TASTY_BYTES;
USE SCHEMA HARMONIZED;

---CREATE MAPPING TABLE FOR RLS POLICY ---
CREATE OR REPLACE TABLE BRANDMANAGERS (MANAGER VARCHAR, BRAND VARCHAR);

INSERT INTO BRANDMANAGERS (MANAGER, BRAND) VALUES 
('KITAKATA_MANAGER' , 'Kitakata Ramen Bar'),
('AMPEDUPFRANKS_MANAGER', 'Amped Up Franks'),
('CHEEKYGREEK_MANAGER', 'Cheeky Greek'),
('FREEZINGPOINT_MANAGER', 'Freezing Point');

SELECT * FROM BRANDMANAGERS;

--- CREATE MANAGER ROLE FOR USAGE IN RLS POLICY --- 
USE ROLE ACCOUNTADMIN;
CREATE ROLE KITAKATA_MANAGER;
GRANT ROLE KITAKATA_MANAGER TO ROLE TASTY_ADMIN;
GRANT ROLE KITAKATA_MANAGER TO USER <YOUR USERNAME>;
GRANT USAGE ON DATABASE FROSTBYTE_TASTY_BYTES TO ROLE KITAKATA_MANAGER;
GRANT USAGE ON ALL SCHEMAS IN DATABASE FROSTBYTE_TASTY_BYTES TO ROLE KITAKATA_MANAGER;
GRANT SELECT ON ALL TABLES IN DATABASE FROSTBYTE_TASTY_BYTES TO ROLE KITAKATA_MANAGER;
GRANT USAGE ON WAREHOUSE TASTY_BI_WH TO ROLE KITAKATA_MANAGER;
GRANT USAGE ON WAREHOUSE TASTY_DATA_APP_WH TO ROLE KITAKATA_MANAGER;


---TEST YOU CAN ACCESS BOTH ROLES---

USE ROLE KITAKATA_MANAGER;
USE ROLE TASTY_ADMIN;

--- CREATE ROW ACCESS POLICY THAT LEVERAGES THE BRANDMANAGERS MAPPING TABLE TO RESTRICT DATA ACCESS ---
USE ROLE ACCOUNTADMIN;
CREATE OR REPLACE ROW ACCESS POLICY brand_policy AS 
(truck_brand_name VARCHAR) RETURNS BOOLEAN ->
'TASTY_ADMIN'= CURRENT_ROLE()
    OR EXISTS (
      SELECT 1 FROM BRANDMANAGERS
       WHERE MANAGER = CURRENT_ROLE()
       AND truck_brand_name = BRAND
      )
;

--- SET POLICY ON ORDERS TABLE---

ALTER TABLE FROSTBYTE_TASTY_BYTES.HARMONIZED.ORDERS ADD ROW ACCESS POLICY brand_policy on (truck_brand_name);

---TEST IF POLICY WORKED----
USE ROLE TASTY_ADMIN;
USE WAREHOUSE TASTY_BI_WH;
SELECT * FROM FROSTBYTE_TASTY_BYTES.HARMONIZED.ORDERS LIMIT 100;

USE ROLE KITAKATA_MANAGER;
USE WAREHOUSE TASTY_BI_WH;
SELECT * FROM FROSTBYTE_TASTY_BYTES.HARMONIZED.ORDERS LIMIT 100;
```

5.3 Once you have run all of the SQL statements and successfully tested the Row Access Policy, you can return to your Sigma instance. 

### What the script is doing:
The first statement sets the database to FROSTBYTE_TASTY_BYTES.

The next two statements we will run create our BRANDMANAGERS table, and populate it with values. This table will be used as a mapping table for the creation of our row-level access policy.  

The third statement simply selects from this new table to verify the values have populated as expected into the table. 

The next set of statements creates a Snowflake role for our brand managers at Tasty Bytes to use, in this instance, the brand manager for Kitakata Ramen Bar. These statements additionally grant usage of the role to yourself, as well as grant usage on the Orders table that is powering our visualizations in Sigma. Finally, there are two statements that test your access to both roles. If you are unable to assume the new KITAKATA_MANAGER role, try running the grant statements again. 

The next statement we will run creates our Row Access Policy. This policy is written so that when a user is in the “Tasty_Admin” role, they will be able to see all the rows of the table. However, if they are not in the Tasty_Admin role, Snowflake will evaluate which rows they should be able to see based on their current role and the values we populated in our BRANDMANAGERS mapping table. 

Now that we have created our access policy, run the next statement in order to apply it to the ORDERS table, with access being determined by the value in the truck_brand_name field. 

Finally, run the next group of statements which will have you assume the TASTY_ADMIN role and select against the Orders table, then do the same from the KITAKATA_MANAGER role. You should notice that when you are in the KITAKATA_MANAGER role, you only see data related to the Kitakata Ramen Bar.

<img src="assets/ss61b.png" width="800"/>

5.4 Back on the Sigma home page, click the icon with your initials in the top right hand corner, and select `Administration`: 

<img src="assets/ss62.png" width="400"/>

5.5 On the left hand side, select “Teams”, then select `Create Team`. We will create two different teams here. 

<img src="assets/ss63.png" width="800"/>

5.6 For the first team, give it the team name of `Tasty Admins`, then click `Create`:

<img src="assets/ss64.png" width="800"/>

5.7 Click on `Teams` on the left sidebar and repeat this process, creating a second team called `Kitakata Managers`.

5.8 Once you have created both teams, select `User Attributes` from the left-hand panel and click `Create Attribute`:

<img src="assets/ss65.png" width="800"/>

5.9 Name your attribute `Tasty Role`, and give it a Default Value of `Public`. Click `Create` to finish. 

<img src="assets/ss66.png" width="600"/>

5.10 Next, create a second User Attribute, this time calling it `Tasty Warehouse` and giving it a default value of `Compute_WH`

<img src="assets/ss67.png" width="600"/>

5.11 Navigate back to User Attributes by clicking `User Attributes` on the left hand side. You should now see your Tasty Warehouse and Tasty Role attributes. 

<img src="assets/ss68.png" width="800"/>

5.12 Select `Tasty Role`, then click `Assign Attribute`

<img src="assets/ss69.png" width="600"/>

5.13 From the drop down list, select the two teams you created earlier, `Tasty Admins and Kitakata Managers`. Assign them the role attributes of `TASTY_ADMIN and KITAKATA_MANAGER` respectively. Click the blue `Assign` button to complete:

<img src="assets/ss70.png" width="600"/>

5.14 Repeat this process for the Tasty Warehouse attribute, this time assigning your `Tasty Admins team the warehouse of TASTY_BI_WH` and your `Kitakata Managers team the warehouse of TASTY_DATA_APP_WH`. Click `Assign` to complete:

<img src="assets/ss71.png" width="600"/>

5.15 On the left hand side, navigate to the `Connections tab`, and select the connection you have been using throughout this lab. Click `Edit` next to the connection name:

<img src="assets/ss72.png" width="800"/>

5.16 In the warehouse field, click the list icon to Set by User Attributes. From the dropdown, select the `Tasty Warehouse` attribute you created earlier. 
 
5.17 Do the same for the role field, selecting the `Tasty Role` attribute you created. 
 
5.18 Finally, enter your Snowflake password and click `Save` in the top right corner:

<img src="assets/ss73.png" width="600"/>

Your Connection Details pane should now show that your warehouse and role in Snowflake will be determined by the User Attributes you have created. 

5.19 On the connections tab, select your TastyBytes connection and click `Browse Connection`.

<img src="assets/Editconnection1.png" width="600">

5.20 Under Permissions, click 'Add Permission'

<img src="assets/editconnection2.png" width ="600">

5.21 Select both teams you have created and grant them `Can Use` Permissions on the Connection. Then click `Save`.

<img src="assets/editconnection3.png" width="600">

<aside class="positive">
<strong>IMPORTANT:</strong><br> By leveraging User Attributes and dynamically assigning the Snowflake role & warehouse our end users have access to, we are able to allow the row level security policy we created in Snowflake to pass through to our users in Sigma. 
</aside>

<img src="assets/ss74.png" width="600"/>

### Create a Version Tag

5.22 On the left hand side, we will now select `Tags`. Next, click `Create Tag`.

5.23 Name your tag `Production`, and give it a description (required). Click `Create`:

<img src="assets/ss75.png" width="800"/>

### Embedding Keys

5.24 For the last piece of work we will do in our administration UI, select the `Account` field from on the top left. Then scroll down to where you see `Embedding`. Click `Add`.

<img src="assets/CleanShot%202023-06-08%20at%2010.04.52@2x.png" width ="800">

5.25 You will see a prompt asking if you want to enable the premium feature. Click `Enable`. You will not be charged for leveraging this in a trial environment.

<img src="assets/CleanShot%202023-06-08%20at%2010.05.47@2x.png" width ="800">

5.26 Finally, you will see your embedding secret. You may save this to another location for future labs, but it will not be needed for this lab. Click `Close`.

<img src="assets/CleanShot%202023-06-08%20at%2010.06.19@2x.png" width="600">

5.27 Select `APIs & Embed Secrets` from the lefthand menu. 

5.28 Click `Create New`:

<img src="assets/ss76.png" width="800"/>

5.29 Select `Embed Secret`, and name the secret `Tasty Embed`. 

5.30 In the Owner field, select your Sigma user, and click `Create`:

<img src="assets/ss77.png" width="600"/>

Normally, you would save the `ClientID and Secret` keys that are auto-generated and presented in a pop-up to a secure location for use later.

We do not need to do this for the purposes of this lab. The keys are required to exist as we will demonstrate embedding directly within Sigma.

5.31 Click `Close`.

### Workspaces

We will create a Workspace and grant permission based on team membership. 

5.32 Navigate back to the Sigma homepage by clicking the `Paper Crane` logo in the top left corner. Select `Workspaces` from the left hand side:

<img src="assets/ss78.png" width="400"/>

5.33 Select `Create Workspace` in the top right corner, then name your workspace `Tasty Bytes`. 

You will see your user listed with `Can Manage` permissions. 

5.34 Add the two teams you created earlier by using the search bar below your user, and grant them `Can Contribute` permissions. 

5.35 Uncheck the `Send an email notification` so that we don't try to send mail at this time.

5.36 Click `Save`: 

<img src="assets/ss79.png" width="600"/>

You will now see your new Tasty Bytes Workspace. Click on its title, then select `Create Folder` in the top right corner. 

5.37 Name your new folder `Workbooks`, then `click the green check mark`:

<img src="assets/ss80.png" width="600"/>

5.38 Navigate back to the home page by `clicking the Sigma logo` in the top left corner. 

5.39 From the home page, click into your `Tasty Bytes Sales Portal` Workbook you created earlier. I should be at the top of the `RECENT` list:

<img src="assets/ss81.png" width="600"/>

5.40 On the top bar, click the drop down next to the workbook title. Select `Tag this published version`:

<img src="assets/ss82.png" width="600"/>

5.41 From the drop down, select the `Production` tag we created earlier. Check the box for `Allow Saving as a New Workbook`, followed by `Set Tag`:

<img src="assets/ss83.png" width="400"/>

5.42 Once again, select the drop down by the workbook title, this time selecting `Move`: 

<img src="assets/ss84.png" width="400"/>

5.43 When prompted to choose a destination, select the `Tasty Bytes workspace` we created earlier:

<img src="assets/ss85.png" width="400"/>

5.44 Then, select the `Workbooks folder` we created and click `Move`:

<img src="assets/ss86.png" width="400"/>

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Exploring Embedding
Duration: 16

Many customers want to embed Sigma content in another web application. Embedding allows that to happen. In the case of this lab, we don't have another application handy, but we can still build and test embedding directly in Sigma.

6.1 From the drop down by your workbook title select `Embedding`:

<img src="assets/ss87.png" width="600"/>

If you recieve a message that `Application Embedding requires a generated secret in the Admin Settings`, you will need to navigate to `Administration` > `Account`, scroll down to the `Embedding` section and click `Add` to enable Application Embedding. You will not be charged for this in the trial.

If you do not see this message you can skip this and scroll down to **6.2**.

<img src="assets/ss88.png" width="800"/>

Click `Enable` in the pop-up to enable the feature. 

You will be presented a `Secret` but we do not need to copy this for the lab. Click `Close`.

6.2 **Return to your Sigma Workbook** and click drop down by your workbook title select `Embedding`:

6.3 From the drop down labeled Generate Application Embed Path For, select “Entire Workbook”. Then click “Test”, which will take you to the Sigma Embedding Sandbox. 

<img src="assets/ss89.png" width="600"/>

6.4 On the left hand side choose the following parameters:
 <ul>
      <li>Select the embed secret we created earlier from the Client Id drop down.</li>
      <li>For Mode, select “User-Backed”</li>
      <li>For External User Teams select “Kitakata Managers”</li>
      <li>For email, input any random email address that is NOT the email you log into Sigma with. It does   
        not need to be a real email address, and you can put something like managers@tastybytes.com.</li>      
      <li>For account type select “Creator”</li>      
</ul>

6.5 Click `Load Embed`.

If everything worked correctly, your dashboard should now read `Sales Performance Kitakata Ramen Bar`. 

<img src="assets/ss90.png" width="800"/>
 
This is because Sigma leveraged the User Attributes you set up previously, and filtered the data per the row access policy you created in Sigma. Now members of the Kitakata Managers team can only see data for the brand they manage. 
 
6.6 Click `Collapse` in the top left if you want to just view the embed full page. 

6.7 Hover over the pivot table and select `Maximize Element` in the top right corner:

<img src="assets/ss91.png" width="600"/>

You will now see the data set underlying the Pivot table. 

As you can see, `Sigma has created a grouped table automaically`, that powers the Pivot. 

Lets add additional metrics to the pivot table. 

6.8 Click the arrow on the right hand side of the `COGS` column, and select `Add new column`:

<img src="assets/ss92.png" width="600"/>

6.9 In the formula bar, copy and paste this:
```console
[Profit]/(Sum([Price]))
```

6.10 Then click the `% button` to format this as a percentage.

6.11 Double click the `Calc` column header and re-name the column `Profit Margin`:

<img src="assets/ss93.png" width="400"/>

6.12 Now click the two arrows in the top right corner to `minimize` the element:

<img src="assets/ss94.png" width="400"/>

You will see that the newly calculated column has been added to the Pivot Table on the main dashboard page:

<img src="assets/ss95.png" width="400"/>

6.13 Click the blue `Save as` button in the bottom right corner:

<img src="assets/ss96.png" width="400"/>

6.14 Save the updated workbook to the `Workbooks` folder within the `Tasty Bytes workspace` we created earlier. 

<img src="assets/ss97.png" width="400"/>

6.15 Navigate back to the Sigma homepage, and select `Workspaces` from the left hand menu. 

6.16 Open the `Workbooks` folder within the `Tasty Bytes workspace`. 

You should now see the new version of the workbook that was created by your Embed User.

<img src="assets/ss98.png" width="800"/>

6.17 Open the workbook `created by the embed user` to verify that the calculations they added to the pivot table have been maintained. 


6.18 Navigate back to the production workbook you created. You will notice that changes made by end users have not impacted the production tagged workbook version. 

<img src="assets/verifyproduction.png" width="800">

![Footer](assets/sigma_footer.png)
<!-- END OF SECTION-->

## Conclusion And Resources
Duration: 5

Thank you for your participation in this hands-on lab. We hope this exercise has helped you understand the value Sigma on Snowflake can drive for your customers.



<!-- THE FOLLOWING ADDITIONAL RESOURCES IS REQUIRED AS IS FOR ALL QUICKSTARTS -->
**Additional Resource Links**

[Help Center Home](https://help.sigmacomputing.com/hc/en-us)<br>
[Sigma Blog](https://www.sigmacomputing.com/blog/)<br>
[Resources and Case Studies](https://www.sigmacomputing.com/resources/)

![Footer](assets/sigma_footer.png)
<!-- END OF WHAT WE COVERED -->
<!-- END OF QUICKSTART -->