author: ashleynagaki, vskarine
id: getting_started_with_cybersyn_shopify_streamlit_native_app
summary: How to access and use the Shopify Benchmarks App in Snowflake’s Native Apps.
categories: Streamlit
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Quickstart Guide: Cybersyn Shopify Benchmarks App
<!-- ------------------------ -->
## Overview 
Duration: 2

![logo-image](assets/Shopify_Cover_Page.png)

In this guide, we will review how to access and use the Shopify Benchmarks App in Snowflake’s Native Apps.

### What is a Snowflake Native App?
[Snowflake Native Apps](https://www.snowflake.com/native-apps/) are deployed by third party companies, like Cybersyn, through Snowflake Marketplace. Instead of customers having to copy data to apps, this technology enables data to be deployed and distributed directly through an app that lives inside an end users’ existing Snowflake account.

### What is Streamlit?
Streamlit is a pure Python [open source](https://github.com/streamlit/streamlit) application framework that enables developers to quickly and easily write, share, and deploy data applications. Learn more about [Streamlit](https://streamlit.io/).

### What you’ll get?
A Streamlit application built natively in Snowflake that is connected directly to a database. This application allows users to quickly demonstrate usage examples for the data and then copy them to query on the underlying data themselves. 

This data specifically focuses on benchmarks for Shopify ecommerce sales and advertising spend from a cohort of Shopify stores. The data consists of Shopify store sales, website engagement, and advertising metrics at the store category and subcategory level. The data is derived from a panel of thousands of Shopify stores globally. It is meant to be representative of the Shopify eCommerce ecosystem.

Categories and subcategories are based on modified Google “Verticals” Taxonomy. Examples include: “Apparel > Women’s Clothing” or “Home & Garden > Home Appliances”. In addition to covering the category level, the data includes the breakdown of each metric. Benchmarks are calculated down to the subcategory by geography level.

Sales and engagement metrics:
- Revenue
- Transaction count
- Average order value (AOV)
- Website sessions
- Website page views

Advertising metrics:
- Click through rate (CTR)
- Cost per thousand impressions (CPM)
- Cost per click (CPC)


### What you’ll Learn?
How to purchase a proprietary Native App from Snowflake Marketplace

How to interact with Cybersyn’s Financial & Economic Essentials App in Snowflake


### Prerequisites
A [Snowflake account](https://signup.snowflake.com/)
- To ensure you can mount data from the Marketplace, login to your Snowflake account with the admin credentials that were created with the account in one browser tab (a role with ORGADMIN privileges is required for this step). Keep this tab open during the session.
  - Click on the Billing on the left side panel
  - Click on Terms and Billing
  - Read and accept terms to continue


<!-- ------------------------ -->
## Accessing the Application in Snowflake Marketplace
Duration: 4

After logging into your Snowflake account, access the [Cybersyn Shopify Benchmarks App](https://app.snowflake.com/marketplace/listing/GZTSZAS2KIY). 
- Click the Get button on the top right box on the listing
- Select Limited Trial to try the App before purchasing
- Read and accept terms by clicking Get again 
  - Note: This data listing is available for free, at no additional charge. 
- The application is now available in your Snowflake instance, as the Cybersyn Shopify Benchmarks App under Apps on the left hand side panel.
- The database is also now available in your Snowflake instance, as the Cybersyn Shopify Benchmarks App database under Data on the left hand side pane. This includes all of the underlying data tables that you can query on directly


<!-- ------------------------ -->
## Walk-through of the App Functionality
Duration: 3

Access the Cybersyn Shopify Benchmarks Appin the Apps section in your Snowflake account.

![overviewgif](assets/Shopify_Overview.gif)

Cybersyn has developed this Streamlit application on our database for users to get example use cases and demo the underlying data tables. 

Each chart display includes the underlying raw data and a SQL query to copy and paste into your own Snowflake Worksheets. 

### Layout & Walkthrough
The includes a side panel navigation bar where you can flip through the following tabs: 
- Shopify Benchmarks: Overview of the data in the App with a deep dive into sales metrics where the user can filter by date and category.
- Ad Metrics: A deep dive into advertising metrics where the user can filter by date and category. 
- Comparison by Year: A deep dive into both sales and ad metrics where the user can filter by date and category and visualize in a YoY stacked format.


<!-- ------------------------ -->
## How to use the app to query the data
Duration: 3

Cybersyn has developed this Streamlit application on our database for users to get example use cases and demo the underlying data tables. Users can filter a chart then get the SQL query for the underlying database to easily access the raw data in their Snowflake Account.

![overview_gif](assets/Shopify_example.gif)

### Step 1: Filter the data in the App
Example: On Comparisons by Year tab
- Filter for
  - Category: “Beauty & Fitness”
  - Period: “Week”
  - Years: “2020” + “2021” + “2022” + “2023”
  - Periods Numbers to Display: 1 to 22


### Step 2: Copy the SQL Query
Example: On Comparisons by Year tab
- On the “Revenue by Year” chart, click “SQL Query”
- Click on the Copy button ![copushape](assets/shape.png) to copy the SQL code

### Step 3: Run the SQL Query
Example: On Comparisons by Year tab
- Click on the Open in worksheet button ![copushape](assets/shape2.png)
- Paste the SQL code into your worksheet
- Click the blue play button in the top right corner
- Now you have a query that you can modify and edit in a Snowflake Worksheet

### Success! You have learned how to use the Cybersyn Shopify Benchmarks App!
