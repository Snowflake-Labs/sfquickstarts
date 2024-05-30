author:
id: improvado
summary: Improvado Composable “Agentic” Data Platform with Snowflake
categories: Getting-Started,partner-integrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started

# Improvado Guide
<!-- ------------------------ -->
## Overview
Duration: 2

This guide will show you how to connect your Snowflake database to Improvado platform, manage user & data access, and understand how AI Agent uses your Snowflake data for analytics & marketing data governance.

Improvado is AI-powered marketing analytics & intelligence and provides secure and efficient data integration across your Snowflake databases.

Improvado's core product focuses on providing robust Extract, Transform, Load (ETL) capabilities. It supports over 500 data sources for seamless data extraction and load. 

AI Agent allows you to automatically analyze your Snowflake data, generating valuable metadata and ensuring accurate and consistent analytics reports. By leveraging advanced data profiling, AI Agent enhances your marketing data governance workflows, ensuring high data quality and compliance.

The following diagram illustrates the overview of Improvado platform capabilities:

![Overview](assets/overview.png) 


Additionally, Improvado offers a custom Marketing Data Governance solution to ensure compliance with marketing guidelines, maintaining high data quality and consistency.

![Cerebro](assets/cerebro.png)


### Prerequisites
- A [Snowflake](https://signup.snowflake.com/) Account
- Access to an Improvado instance. Please reach out to our Sales and [Book a demo](https://improvado.io/register/talk-to-an-expert)

### What you’ll learn
- How to connect Snowflake to Improvado 
- How to ensure privacy of your data within Improvado platform
- How AI Agent uses metadata to provide accurate & useful insights

<!-- ------------------------ -->
## Connect Snowflake to Improvado
Duration: 2

In this step, we’ll learn how to connect your Snowflake schema to Improvado. Improvado integrates with Snowflake using a JDBC driver, ensuring efficient data transfer and fast updates.

### Step 1. Database permissions
Now you’ll need to grant the following permissions to your Snowflake database schema:
- `CREATE`
- `ALTER TABLE`
- `DELETE`
- `INSERT`

### Step 2. Select a destination
Go to Improvado and select the **Destinations** tab. This catalog shows all the Destinations that you can use for Data Loading.
![Catalog](assets/add_a_new_destination.png)

Click on the **Snowflake** tile.

### Step 3. Complete configuration
On the Snowflake connection page, fill in the following fields:
1. Enter a name for your Destination connection in the **Title**.
2. Enter the **Account**.
3. Enter the **User Name**.
4. Enter the **Password**.
5. Enter the **Database Name**.
6. Enter the **Warehouse**.
7. Specify the **Schema** of your database.
8. Enter the **Role**.
   - The `SYSADMIN` role should be granted to the specified user. Make sure you’re using a non-public role because it doesn’t have enough permissions for the load process.
9. Select the necessary **Use static IP** option from the dropdown.

### AI Agent and your Snowflake data
After successfully connecting your Snowflake database, Improvado AI Agent will automatically analyze data in your Snowflake storage and generate metadata for accurate analytics reports and consistent Marketing Data Governance workflows.

### Connecting a Data source
Connecting a Data source in Improvado enables you to extract, transform, and load data seamlessly into your analytics and reporting frameworks. Follow these simple steps to connect a data source:
Go to the Data sources page and select a necessary Data source to extract your data
Enter required credentials or authorize using OAuth (depending on Data source API capabilities)
Then, you’ll be redirected to the Connection Details page, where you can set up data extraction.


<!-- ------------------------ -->
## Data Privacy
Duration: 2

In this step, we will learn about Data Privacy policies and rules within Improvado & Snowflake.

Improvado AI Agent is compatible with any Row Access Policies you’ve set up in Snowflake. Improvado enforces data governance policies such as access controls and quality standards right from the metadata level. This ensures that your data governance workflows are consistent and reliable.

You can check Improvado’s [Privacy Policy](https://improvado.io/company-legal/privacy-policy) for more details.

### User access management in Improvado
We also provide tools to manage user access within the Improvado platform.

Workspaces allow for access management and control within a single Improvado instance. This is especially helpful if you want to separate data by specific Products or Client accounts, ensuring a structured and simplified experience.

![Workspaces](assets/workspaces.png)


<!-- ------------------------ -->
## Data Access and Consumption
Duration: 2

The AI Agent automatically scans and collects metadata for each table, row, and column in your Snowflake storage. This step is crucial as it enables the AI Agent to understand the structure and relationships within your database.

Improvado’s integration with Snowflake ensures that your analytics, machine learning, and ETL services are all connected within a unified platform. This integration simplifies the data management process and enhances the overall efficiency of your data workflows.

By leveraging these capabilities, Improvado facilitates efficient data access and consumption, providing you with the tools necessary to extract valuable insights and maintain robust data governance practices.

### Billing dashboard
Improvado Billing Dashboard offers an in-depth analysis of your data usage, providing crucial segmented insights into extracted rows over your usage period. It also includes interactive features, enhancing your ability to examine and understand the data in a more dynamic and effective manner.

![Billing dashboard](assets/billing_dashboard.png)


<!-- ------------------------ -->
## Conclusion
Duration: 1

In this guide, we learned how to connect your Snowflake data to Improvado for analytics & governance.

Improvado provides significant value to Snowflake users and allows you to:
- Better organize your Data Warehouse
- Enable Data Governance for your marketing data
- Manage your PII within Snowflake
- Get an insight into your Snowflake data
- Scale to the needs of your enterprise

![Value](assets/conclusion_value.png)


### Learn more
- You can learn more about Improvado on [official website](https://improvado.io)
- Read about Snowflake partnership with Improvado at [Improvado-Snowflake Partnership](https://improvado.io/blog)
