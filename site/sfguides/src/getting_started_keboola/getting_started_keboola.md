author: Anthony Alteirac
id: getting_started_keboola
summary: Getting Started With Keboola
categories: getting-started,partner-integrations
environments: web
status: Draft 
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: Getting Started, Data Engineering 

# Getting Started with Keboola 
<!-- ------------------------ -->
## Overview 

Duration: 1


Modern Data Stack requires setup and maintenance and Snowflake goes a long way to lowering the bar.

Our Powered By Snowflake partner Keboola offers Data Platform as a Service, helping users further accelerate data projects by delivering a ready-to-use managed platform. It includes all the technologies a data team needs. Therefore enabling everyone to capitalize on Snowflake’s capabilities and acting as an avenue to the incredible modern no-maintenance and no-code solution.

This Quickstart will guide you to build a complete data pipeline from ingestion, transformation, orchestration to presentation in a Streamlit application.

### Prerequisites
- Familiarity with Snowflake
 
### What You’ll discover 
* How to start working with Keboola
* How to create a flow based on Keboola template
* How to configure Keboola template 
* How to work with SQL transformation in Snowflake
* Introduction to Snowpark Python UDF
* How to run Keboola flow
* How to visualize data with Streamlit
 
### ![Template](assets/important-point-icon.png) What You’ll Need 
- A [Snowflake](https://trial.snowflake.com/) account or free trial with an ACCOUNTADMIN user.

### What You’ll Build 
- A complete data pipeline from Shopify. The Keboola template will automatically join, clean and transform data into Snowflake. Within few clicks, Keboola will generate all necessary steps plus a Streamlit Application to interact with data. The template will also generate a Snowpark UDF to create RFM segmentation. This will help you to optimize the monetization of your online traffic.

![Template](assets/template.png) 

## Create Keboola Account with Partner Connect
Duration: 5

### Step 1 
1. Login to **Snowflake Snowsight**.
2. Switch role to **ACCOUNTADMIN**.
3. Click **Admin > Partner Connect**.
4. Search for **Keboola**.
![kebPC](assets/pctile.png) 
5. Click **Keboola** tile.

### Step 2
1. See objects that will be created in Snowflake.
2. Click **Connect**.<BR>
![PartnerConnect](assets/pcinfo.png)

### Step 3
1. Click **Activate**.<BR>
![PartnerConnect](assets/pcactivate.png)

### Troubleshooting

You must have a verified email in your profile. Otherwise you'll get the following message:

![PartnerConnect](assets/pcemailverif.png)

You also MUST have a first name and last name in your profile:

Open your profile:

![PartnerConnect](assets/pcprofile1.png)

Add email, first and last name:

![PartnerConnect](assets/pcprofile2.png)

## Activate Keboola Account
Duration: 2

### Define your Keboola password
After you have clicked "Activate" from the previous section, you'll land on Keboola's Welcome page to define your password:

![PartnerConnect](assets/pckebaccountactivation.png)

### Enable full features

Congratulation, you have now a Keboola account!

We need to enable all features for this lab. It's a simple process. 

Click on "Enable All Features" link:

![PartnerConnect](assets/pcenablelink.png)

Copy the SQL code from the Keboola UI:

![PartnerConnect](assets/pcenableall.png)

In Snowflake Snowsight, open a new worksheet, paste the code and select "Run All", be sure all rows are executed!

![PartnerConnect](assets/pcenableallsnow.png)

Go back to Keboola, you should see the following:

![PartnerConnect](assets/pcenableallsuccess.png)


## Get Snowflake Account URL
Duration: 1

Here we'll prepare everything for Keboola to write into Snowflake account, remember Partner Connect flow already created a DB (PC_KEBOOLA_DB) and a warehouse (PC_KEBOOLA_WH):

- Get hostname information, note for later usage

Login to Snowflake trial account

- Get host name:

![PartnerConnect](assets/hostname.png)

At the left bottom of the screen, hover the account and click on "Copy account URL".

Paste the content in safe place to reuse later.

## Instantiate the Template
Duration: 3

We need first to activate the Data Apps feature in Keboola:

In the top right corner, select your user and navigate to "Settings"

![Template Creation](assets/menufeat.png)

Activate the Data Apps Feature:

![Template Creation](assets/dataappfeat.png)

Let's move to Keboola platform, after you have created your Keboola trial account, login to the platform and navigate to the "Templates" tabs. 

In the searchbar, type "RFM"

![Template](assets/important-point-icon.png) Be sure you select the correct template "Shopify RFM Analysis with Streamlit".

![Template Creation](assets/template_creation.png)

Click the green button "+ USE TEMPLATE"

![Template Creation](assets/tpdetails.png)

You'll see more details on the template, click the top right green button "+ USE TEMPLATE"

![Template Creation](assets/tpname.png)

Enter a name and click " -> NEXT STEP"

## Configure the Template
Duration: 5

For this lab, we'll use dummy Shopify data so we don't need to configure the Shopify Component.

The template configuration constists in setting-up connection information to each component needed to run the flow.

For our lab, we'll need to setup only Snowflake.

![Template Creation](assets/tpoverview.png)


We need to enter Snowflake information in the "Snowflake Destination" step of the flow:

Click on "Edit Configuration"

![Template Creation](assets/snowinfo1.png)

Add the information we created during step 4 (Get Snowflake Account URL) 

![Template Creation](assets/snowinfo.png)

![Template](assets/important-point-icon.png) Hostname is the URL you copied in Snowflake WITHOUT "https://"

![Template](assets/important-point-icon.png) Port is "443"

![Template](assets/important-point-icon.png) Username is your Snowflake user name

![Template](assets/important-point-icon.png) Password is your Snowflake password

![Template](assets/important-point-icon.png) Database Name is "PC_KEBOOLA_DB"

![Template](assets/important-point-icon.png) Schema Name is "PUBLIC"

![Template](assets/important-point-icon.png) Warehouse is "PC_KEBOOLA_WH"

Save the template: 

![Template](assets/savetp.png) 

## Configure the Data App Secrets
Duration: 5

### Get Keboola token:

From the Streamlit application, we can write back data thanks to Keboola API.

We need first to get an API token. Follow the steps to generate this token.

Navigate to token page in Keboola:

![Template Creation](assets/tokenk.gif)

![Template](assets/important-point-icon.png)  Generate the token, do not forget to set "Full Access" and to copy the value, paste into a text file!

![Template Creation](assets/tokenk2.gif)

### Get Snowflake account name:

![Template](assets/important-point-icon.png) At the left bottom of the screen, hover the account and click on "Copy account URL" paste into a text file!

![Template Creation](assets/hostname.png)

Navigate to the Flow page:
![Template](assets/navflow.png) 

Select the Flow:
![Template](assets/navflow2.png) 

Scroll down in the Flow and select the "RFM Analysis Data App", click on "Edit Configuration":

![Template](assets/navconfapp.png) 

Change the values according to your Snowflake account and Keboola API token:

![Template](assets/important-point-icon.png) user and password are your SNOWFLAKE user and password

![Template](assets/important-point-icon.png) account is the snowflake URL you have pasted in your text file

![Template](assets/important-point-icon.png) keboola_key is the keboola API token you have pasted in your text file

![Template Creation](assets/appsecrets.png)

## Run the Flow
Duration: 10

The template generated a Keboola Flow. A flow is a sequence of actions.

Navigate to the Flow page:
![Template](assets/navflow.png) 

Select the Flow:
![Template](assets/navflow2.png) 

Run the Flow:

![Template](assets/flowrun.png) 

Monitor the run:

![Template](assets/flowrunnav.png)

The inital run can take about 10mn, subsequent will take only few mn.

Success!

![Template](assets/success.png)

## See results in Snowflake
Duration: 2

Open your Snowflake web tab and check the PC_KEBOOLA_DB content.

You should see the tables created:

![Template](assets/ressnow.png)


## Open Streamlit
Duration: 5

We have seen Keboola Shopify template in action. We have now a complete set of tables in Snowflake with Shopify sales data including an RFM segmentation, ready to use!


_RFM stands for Recency, Frequency, and Monetary value, each corresponding to some key customer charasteritics. These RFM metrics are important indicators of a customer’s behavior because frequency and monetary value affects a customer’s lifetime value, and recency affects retention, a measure of engagement_


In this section, we'll leverage this segmentation in the Streamlit application, automatically created from the template.

This application will :

- Connect to your Snowflake account
- Connect to your Keboola project
- Give you an overview of the generated RFM Segmentation
- Simulate Revenue impact of discount on targeted segment(s)
- Get targeted customer list and expected discount to trigger a marketing campaign
- Write back this information in Keboola for a next flow to create the campaign

Navigate to the Data Apps section

![Template Creation](assets/navapp.png)

Open the Data App

![Template Creation](assets/openapp.png)

## Play with Data
Duration: 5

If your Snowflake information are correct, after clicking "Connect" you should see:

![Template Creation](assets/appli.png)

### RFM Segmentation Overview

You see here the generated segmentation and the number of customers assigned to.

![Template Creation](assets/segmentation.png)

### Simulate discount

You can select the segment(s) you want to assign discount:

![Template Creation](assets/targetSeg.png)



You can then adjust discount level and expected revenue increase. 

![Template Creation](assets/simul.png)



This will calculate the impact on the total revenue

![Template Creation](assets/revsim.png)

### Generated list of targeted customers

Scrolling down the page, you'll find an always adjusted list of customers (based on selected segments) and the level of discount.

This list can be used to trigger a marketing campaign:

![Template Creation](assets/listcust.png)

### Write the table back into Keboola

Finally press the "UPLOAD" button:

![Template Creation](assets/uploadtable.png)

Wait until the upload is finished:

![Template Creation](assets/upfinish.png)

Check the table in Keboola:

![Template Creation](assets/tableinkeb.png)

YOU'RE DONE WITH THE LAB !!  🍾

## Troubleshooting
Duration: 0

### You choose the wrong template

Delete the associated Flow

![Template Creation](assets/delflow.png)

Delete the Components

![Template Creation](assets/delcompo.png)

Delete the Storage

![Template Creation](assets/delsto.png)

Same player, start again :-)

### Your Snowflake credentials are wrong

Navigate to the Components tab, click on the Snowflake Data Destination:

![Template Creation](assets/modConn.png)

Select "Database Credentials" on the right:

![Template Creation](assets/modCred.png)

Udpate and test your credentials:

![Template Creation](assets/checkCred.png)

### Your DB name, schema, warehouse name are wrong

Navigate to the Components tab, click on the Snowflake Data Destination:

![Template Creation](assets/modConn.png)

Select "Database Credentials" on the right:

![Template Creation](assets/modCred.png)

Check the DB, Schema, Warehouse:

![Template Creation](assets/checkCred.png)

### Your Data Application secrets are wrong

Navigate to the Data Apps section:

![Template](assets/navapp.png) 

Open the configuration:

![Template](assets/navsecapp.png) 

Correct the secrets:

![Template Creation](assets/appsecrets.png)

## Conclusion
Duration: 1

Congratulations! You've successfully built a complete data pipeline from ingestion, transformation, orchestration, to presentation in a Streamlit application!

### What You Learned
 - Connect to your Snowflake account to Keboola project
 - Instanciate Keboola template
 - Automatically generate RFM segmentation
 - Connect Snowflake and Keboola to Streamlit application
 - Write back data from Streamlit to Keboola 

### Related Resources

  - [Keboola documentation](https://help.keboola.com/)
  - [Github Streamlit source code](https://github.com/sfc-gh-aalteirac/streamlit_keboola_vhol_pc)
  - [Keboola Streamlit Component](https://pypi.org/project/streamlit-keboola-api/)

