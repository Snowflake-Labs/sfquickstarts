id: build-supportable-data-pipelines-with-ai-in-coalesce   
language: en   
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/applications-and-collaboration   
status: Published   
authors: Doug Barrett   
summary: Learn how to leverage AI and Coalesce to rapidly build supportable, repeatable data solutions effortlessly.     
environments: web     



# **Build Supportable Data Pipelines with AI in Coalesce** 

## Overview

This Hands-On Lab exercise is designed to help you master building data pipelines using AI within Coalesce.  Coalesce data pipelines open up the power and functionality of the Snowflake platform by leveraging standardized building blocks for AI to generate repeatable, supportable code extremely rapidly.  Coalesce uses an MCP and UI optimized for data engineers to Generate, Build, Review and Refine their data pipelines.  In this lab, you’ll explore the Coalesce interface, learn how to easily transform and model your data with natural language prompts, understand how to read and support your pipelines, and play with rich column level metadata.

What You’ll Learn

* How to navigate the Coalesce interface  
* How and when to use AI  
* How to add data sources   
* How to prepare your data   
* How to build out a Data Mart  
* How to make changes to your data and propagate changes across pipelines  
* How to commit into GIT  
* How to add a Semantic View

By completing the steps we’ve outlined in this guide, you’ll have mastered the basics of Coalesce and can venture into our more advanced features.

What You’ll Need

1. Basic knowledge of SQL, database concepts, and objects

2. The [Google Chrome browser](https://www.google.com/chrome/)

What You’ll Build

* A Directed Acyclic Graph (DAG) representing a data pipeline leveraging AI and advanced Snowflake features.

```diff
- For this Hand on Lab we will start at section 3
```

## Step 1 (Optional): Create a Snowflake Trial Account

1. Fill out the Snowflake trial account form [here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=na-us-en-brand-trial-exact&utm_content=go-eta-evg-ss-free-trial&utm_term=c-g-snowflake%20trial-e&_bt=579123129595&_bk=snowflake%20trial&_bm=e&_bn=g&_bg=136172947348&gclsrc=aw.ds&gclid=Cj0KCQiAtvSdBhD0ARIsAPf8oNm6YH7UeRqFRkVeQQ-3Akuyx2Ijzy8Yi5Om-mWMjm6dY4IpR1eGvqAaAg3MEALw_wcB&utm_cta=developer-guides). Use an email address that is not associated with an existing Snowflake account.

2. When signing up for your Snowflake account, select the region that is physically closest to you and choose Enterprise as your Snowflake edition. Please note that the Snowflake edition, cloud provider, and region used when following this guide do not matter.

3. After registering, you will receive an email from Snowflake with an activation link and URL for accessing your trial account. Finish setting up your account following the instructions in the email.

## Step 2: (Optional) Create a Coalesce Trial Account 

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name.

Once you are logged into your Snowflake account, sign up for a free Coalesce trial account using Snowflake Partner Connect. Check your Snowflake account profile to make sure that it contains your fist and last name.

1. Select Data Products \> Partner Connect in the navigation bar on the left hand side of your screen and search for Coalesce in the search bar.

2. Review the connection information and then click Connect.

3. When prompted, click Activate to activate your account. You can also activate your account later using the activation link emailed to your address.

4. Once you’ve activated your account, fill in your information to complete the activation process.

Congratulations\! You’ve successfully created your Coalesce trial account. 

## Step 3 Login to Coalesce Transform

1. Enter the Coalesce URL in your browser:  [https://app.coalescesoftware.io](https://app.coalescesoftware.io/)

2. Enter your Login details provided in the course and press **Sign In**:

	![Coalesce Login](assets/image32.png)

3. Once signed in – find *your User’s workspace* in the Default Project Workspaces and press the **Launch \-\>** button:

   ![Coalesce Workspace](assets/image33.png)

4. This will open your primary development and review interface.  Feel free to orient yourself in the Build interface – primarily the \+ button, the (DAG) Browser, the Node List:

   ![Coalesce Browser](assets/image34.png)

## Step 4 Adding Data Sources

We are going to connect to Snowflake, identify source data and load its definition into Coalesce as Source Nodes.  This is the start of building a data pipeline \- identify source data.

1.  Press the **\+** button above the Node List, and select **Add Sources**:

   ![Data Sources](assets/image41.png)

2. Select the Storage Location **LAND** to select all tables in that Schema in Snowflake and Press the **Add 6 Sources** button at the bottom.
     
   ![Source Schemas](assets/image42.png)

   
3. Now you should see the Source nodes in your Graph:

   ![Landed](assets/image43.png)


## Step 5 – Build a Transformation Layer using Coalesce AI

1. Open the Coalesce AI assistant by pressing the ![Coalesce AI button](assets/copilotbutton.png) button at the top right of the Browser:

   ![Coalesce AI](assets/image51.png)

2. Note the Coalesce AI Context is showing **Browser** and **Allow Edits** is switched on.  

3. In the Chat with Coalesce AI box type in the text:  ```Add a staging layer over Source nodes``` and press the ![sendbutton](assets/sendbutton.png) (send) button.  

4. Check the end result looks like this:

   ![Stage Tables](assets/image54.png)

5. Now edit the Node called STG\_YELLOW\_CAB\_TRIPS by right clicking on the Node and choosing **Edit**:

   ![Edit Stage](assets/image55.png)

6. You should see the tables’s columns and the Coalesce AI context should change to STG\_CAB\_TRIPS:

7. Add a prompt to Coalesce AI:  ```add columns to calculate trip duration and average speed```

   ![Coalesce AI Tables](assets/image57.png)

8. To review the generated SQL find the 2 new columns that Coalesce AI added by scrolling to the bottom of the Column list in the Center pane – and double click on the SQL in the Transform column:

   ![Coalesce AI SQL](assets/image58.png)

   Note: you can write or rewrite this SQL yourself if you wanted to.  

9. Select the **Create** and then the **Run** button – it should show a data preview pane at the bottom of the screen if successful.

10. You can review the generated code in the **Code** pane down below:

   ![Code pane](assets/image510.png)

Expand the top line in the Code Pane and press the pop out button ![Expand button](assets/expandbutton.png)to the right of the **Insert …** line to see the code:

   ![Code pane review](assets/image5102.png)

This will open the Code Viewer:

   ![Code review](assets/image5103.png)

11. Now you can create and populate *all* the tables we have defined.  On the Browser choose the **Create All** option and once finished just press the **Run All** button at the top right:

   ![Create All](assets/image511.png)

## Step 5.5 – Build more Transformations

In the VENDOR\_DETAILS table we can see there is JSON data stored in a variant column in the HQ\_ADDRESS\_DETAILS column.  As part of our Transform layer we want to shred the JSON documents into a structured schema.  

1. Right click and **Edit** the STG\_VENDOR\_DETAILS table in the Browser:

   ![Stage edit](assets/image551.png)

2. You can see the data in in the Preview pane below (if not click on ![Preview button](assets/previewbutton.png) ):

   ![Preview data](assets/image552.png)

Note:  you can see a JSON document in the HQ\_ADDRESS\_DETAILS field containing Vendors’ address details.  We want to turn this into columns (and rows) to make the address data more easily readable.

3. Select the HQ\_ADDRESS\_DETAILS column and choose **Derive Mappings / From JSON**:

   ![Derive json](assets/image553.png)

This will sample the JSON structure and identify the elements / nesting in the JSON and create columns and mappings to extract the data.  In this case we will pull the Address components stored in the JSON into their own ADDRESS / CITY / STATE etc columns.  

4. Press the **Create** and **Run** buttons and review the data in the new columns.  
   
5. Now we have split apart the Vendors address we can use another staging node to combine the STG\_VENDOR details and the STG\_VENDOR\_DETAILS tables.  To do this we will use a SQL Work node type (note: we could use the standard Stage node type if we wanted).    
   Multi-select (control-click) the STG\_VENDOR and STG\_VENDOR\_DETAILS tables and choose the **Join Nodes** and choose the **SQL Work** node: 

   ![Work Node](assets/image555.png)

6. This will open a SQL editor – where we can write (or generate SQL) to transform the data.  This SQL is annotated with table details
   ```diff
   - Note: leave the top 2 lines alone as they contain node level annotations (id and node type)
   ```

   ![SQL Editor](assets/image556.png)

We could just type SQL in this editor – in this case only really the join clause needs fixing.  **Note:** This SQL is parsed into the Column list on the right hand side when the SQL is valid. 

7. Add a line after the VENDOR\_NAME (LINE 5 ABOVE) \- and type the following SQL:  
   	```sql
   VENDOR_NAME||’ ‘||STATE AS VENDOR_STATE,
   ```
   And check that this column is automatically added in the Column list on the right.  

   ![Column list](assets/image557.png)

8. Rather than type SQL lets get the Coalesce AI to generate SQL using the prompt: ```build sql that joins stage tables STG\_VENDOR and STG\_VENDOR\_DETAILS using ctes```

   If the SQL looks good copy using the **Copy Code** option and paste it (*leaving the top 2 annotation lines alone*):

   ![Coalesce AI SQL](assets/image558.png)

9. Press the **Create** and **Run** buttons and review the data in the Preview Pane.

## Step 6 \- Build and populate Datamart

Lets build some dimensions and facts.

1. Open the Browser and check Coalesce AI context is Browser and use prompt: ```What dimensions and facts would you create over these stage and work tables``` 

   ![Coalesce AI datamart](assets/image61.png)

2. If that plan looks sensible (it should) then tell Coalesce AI to go ahead and create them

   ![Coalesce AI datamart confirm](assets/image62.png)

3. Select to **Create All** and **Run All** in the Browser to create the tables on Snowflake and populate them.

   ![Datamart](assets/image63.png)

4. Now we will commit all your hard work to GIT to keep it safe by clicking on the **Git** button at the bottom Left of the screen:

   ![Git dialog](assets/image64.png)

This will open a GIT dialog that shows changes to your User GIT Branch and will show changes since the last commit:

   ![Git dialog 2](assets/image642.png)

Press the AI Sparkle icon ![Sparkle button](assets/sparklebutton.png)in the lower Commit message text box to generate a commit message and press the **Commit and Push** button.

**Note:** this Dialog also has the ability to show other branches, checkout, create branches and merge branches.

## Step 7 \- Review and Refine the Data Mart

We can see what we have built \- and make changes in the UI.  We are going to add propagate a column using column lineage, add documentation and then re-commit to GIT.

1. Open and review DIM\_VENDOR by selecting **Edit** on the DIM\_VENDOR table and view sampled data in the Preview pane at the bottom of the screen.

2. Right click on COUNTRY column and choose **View Column Lineage** to see graphical lineage. 

   ![Column lineage](assets/image72.png)

At the top right select Related \-\> **All** to see all tables related by lineage.

And hover over the ![Transform hover](assets/transformbutton.png) symbol to see Transformation Details:

   ![Column lineage2](assets/image722.png)

3. Now lets refine the model by propagating and degenerating the COUNTRY column into the downstream FACT. Click on the Ellipsis next to the COUNTRY column and choose **Propagate Addition**:

   ![Column lineage propagate](assets/image73.png)

4. Check the checkbox at the top of the FACT\_CAB\_TRIPS table to choose to propagate the column into the FACT table, press the **Preview** and **Apply** buttons:

   ![Propagate review](assets/image74.png)

5. Then press **Propagate**.  This will alter the structure and mapping for the FACT table

   ![Propagate confirm](assets/image75.png)

6. Finally we should add (AI generated) documentation over the columns in the FACT table.  Edit the FACT table, and find the Description column in the table headings:

   ![Column descriptions](assets/image76.png)

This will use metadata context to generate column descriptions that can be surfaced in Documentation and any tools that point at the database

7. Select the header checkbox to select all the descriptions and press **Apply**:

   ![Column descriptions apply](assets/image77.png)

8. Press the **Create** button and review the generated DDL – you will see the descriptions are pushed down to Snowflake so that any other data tools can use this documentation.

   ![Column descriptions ddl](assets/image78.png)

9. Lets commit your changes to GIT like we did at the end of Chapter 6\.

## Step 8 (Optional) – Install a Semantic View node type

We can use the Coalesce Node Marketplace to install more node types into your environment. We have over 80 node types that embody Snowflake best practises and standards built in.  We are going to install a Semantic view node.  

1. Open the Build Settings at the bottom left of your screen:

   ![Build settings](assets/image81.png)

2. Select Packages and press the Browse button (in the middle or top right)

   ![Package Browse](assets/image82.png)

3. Feel free to scroll through the list of available Node type packages available \- these are provided at no charge.  In the Search enter **Semantic View** and click to view the details.
   
   ![Marketplace](assets/image83.png)

4. Copy the **Package ID:**
   
   ![Package ID](assets/image84.png)

5. Back in Coalesce / Build Settings, press the **Install** button and paste in the Package ID.  The version should default to the latest.  And use Semantic for the Alias, then press **Install**.:

   ![Package Install](assets/image85.png)

6. In the Browser \- you can now create a node of type Semantic View.  Select the FACT\_CAB\_TRIPS right-click and choose **Add Node / Semantic / Semantic View**:

   ![SV](assets/image86.png)

7. Choose the simplest options to start with:  
   * Dont Create Schema Table  
   * For Primary Key choose TRIP\_ID  
   * Dont Enable Relationships  
   * Dont Enable Facts  
   * Dont Enable Dimensions  
   * Enable Metrics:  
     * Choose to SUM \- FARE\_AMOUNT with an Alias of TOTAL\_FARE\_AMOUNT

	Feel free to read the documentation to understand the other options.  But for now press **Create**

   ![SV1](assets/image87.png)

   ![SV2](assets/image872.png)

## Conclusion And Resources

Congratulations on completing your lab. You've mastered working with AI, Coalesce Transform and the Coalesce Marketplace. Be sure to reference this exercise if you ever need a refresher.

We encourage you to continue working with Coalesce Transform by using it with your own data and use cases and by using some of the more advanced capabilities not covered in this lab.

What You Learned

* How to navigate the Coalesce interface

* How to leverage AI to build repeatable / supportable data pipelines.

* How to add data sources to your graph

* How to prepare your data for transformations with Stage nodes

* How to leverage GIT for Version Control and Branching

* How to extend the Node Types from the Coalesce Marketplace with other Snowflake objects such as Dynamic tables or Semantic Views


Related Resources

* [Getting Started](https://coalesce.io/get-started/)

* [Documentation](https://docs.coalesce.io/docs) & [Quickstart Guide](https://docs.coalesce.io/docs/quick-start)

* [Video Tutorials](https://fast.wistia.com/embed/channel/foemj32jtv)

* [Help Center](mailto:support@coalesce.io)

Reach out to our sales team at [coalesce.io](https://coalesce.io/contact-us/) or by emailing [sales@coalesce.io](mailto:sales@coalesce.io) to learn more.
