summary: Begin modeling your Snowflake database online with SqlDBM 
id: database_modeling_with_SqlDBM 
categories: Getting Started
environments: web
status: Hidden 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Modeling, Data Engineering, CICD 
authors: Sergey Gershkovich


# Cloud-native Database Modeling with SqlDBM 
<!-- ------------------------ -->
## Overview 
Duration: 2

Relational database modeling enables instant visual review of a database landscape and the relationships between its entities - like a map for your data. 

[SqlDBM](https://www.SqlDBM.com) is an online database modeling tool that works with leading cloud platforms such as Snowflake, and requires absolutely no coding to get started. In this Quickstart, you will see how you can model your entire Snowflake database in just a few clicks and begin taking advantage of all the time-saving features that SqlDBM delivers. 

### What you’ll learn 
* How to quickly diagram an existing schema through reverse engineering
* Create and manipulate database objects using time-saving features like copying and cloning
* The importance of primary and foreign key relationships and how to declare them 
* Inheritance for parent/child objects 
* Forward engineering & deployment of changes to Snowflake

### What You'll Use During the Lab

* An existing or trial [Snowflake account](https://trial.snowflake.com/) with `ACCOUNTADMIN` access

* An existing or trial [SqlDBM account](https://sqldbm.com/Home/)  


### What You'll Build
* A relational model of an entire database schema
* Add new tables with no coding required
* Relate the tables through primary and foreign key constraints
* A data catalog with column-level descriptions

A sample schema diagram like the one we will create: 
![diagram sample](assets/diagram_sample.jpg)

<!-- ------------------------ -->
## Use Case Overview 
Duration: 3

### What is Database Modeling?
An entity-relationship (ER) diagram is the traditional way of visualizing the tables and their relationships in a relational database. Having a diagram not only makes it easier to find relevant tables, but also gives the user an instantaneous idea of how tables can be joined to one another for analytics purposes. 

SqlDBM takes the ER diagram's visual, no-code approach, and allows user to manipulate their database directly using the graphical perspective. Instead of writing DDL by hand, SqlDBM users can drag, drop, copy, and clone objects using an intuitive, browser-based graphical interface. Then, we take it a step further!

With SqlDBM, changes made on a diagram can be forward-engineered into neat, Snowflake-specific DDL and deployed back to the database. What's more, the tool leverages this intuitive, code-free approach to enable collaboration, documentation, and version control. 

We'll go through all these features in detail as part of this quickstart, so let's get started by setting up our account. 

![SqlDBM Architecture](assets/SqlDBM_architecture.png)   

<!-- ------------------------ -->
## Snowflake Configuration 
Duration: 3

1. Login to your Snowflake trial account.  
![Snowflake Log In Screen](assets/snowflake_login.png)  

2. Familiarize yourself with the UI if logging in for the first time in the [Snowflake UI Tour](https://docs.snowflake.com/en/user-guide/snowflake-manager.html#quick-tour-of-the-web-interface).  
![Snowflake Worksheets](assets/snowflake_worksheets.png)  

3. Ensure that your user has the following grants assigned in order to follow along with the quickstart. If not, sample DDL will be provided where needed. 


Privilege | Required for | Alternative
---------|----------|---------
 USAGE on SCHEMA | Bringing existing database into a SqlDBM project | Use sample DDL provided
 ALL on schema | Deploying changes back into Snowflake | N/A

<!-- ------------------------ -->
## Create a New Project and Bring your Schema
Duration: 5

After logging in to SqlDBM, you will be taken to the Projects Dashboard. Otherwise, select "Dashboard" from the top-right dropdown.

![Dashboard](assets/dashboard.jpg)  

Follow the steps to create a Snowflake project and bring your schema: 

1. Click the "New Project" button at the top to get started.

2. Select "Snowflake" as the database type and click "Bring your database".

![Creating a new project](assets/bring_your_db.jpg)

3. Click the "Connect to DW" to create a live connection to Snowflake

* Alternatively, run the GET_DDL command by hand and copy and paste the output onto the text area on the screen, or save it in a file and upload via the "Drop your File" button. 

```sql
SELECT GET_DDL('schema','"DATABASE_NAME"."SCHEMA_NAME"', true);
```

* Or use our [example DDL](assets/sample_schema.sql ) and paste it into the text area on the screen.

4. Enter your Snowflake server instance and log in with a user which has usage privileges on the schema you wish to import.

![Direct Connect ](assets/direct_connect.jpg)

5. Select the Database and Schema you wish to import and press the "Apply" button below. 

6. Press the up arrow icon / "Upload SQL Script" button at the top to parse the DDL provided.

![Upload SQL script](assets/upload_sql.jpg)

7. Review the objects that are being imported on the left panel. Optionally, you can exclude individual items from being imported by de-selecting the check-box next to them. 

8. Press the "Import" button to create a project with the selected objects. 


<!-- ------------------------ -->
## Configure project defaults
Duration: 5

Let's configure some initial time-saving defaults for our project as well as set the visual level of detail and look-and-feel for our diagrams.

### Project-level properties

![project settings](assets/project_settings.jpg)

1. Save first revision and name your project

* Click the save button at the top right and name your project with something descriptive. [1]


2. Rename revision title

* Let's rename "Initial Revision" to something that fits with your way of working. Name your revisions based the Agile Sprint, current project phase, or even calendar month. Something to allow for a meaningful grouping of changes. 

* Click on the text "Initial Revision" to modify it. [2]

3. Enable dark theme

* Click on the blue SqlDBM logo at the top left to bring up the project menu. Click "Dark Theme" to enable it, if that's your thing. 

4. Set naming conventions for the project

* Click on the blue SqlDBM logo at the top left to bring up the project menu and select "Naming Conventions"

* Any changes made here can be "[applied] to all existing objects" and validated going forward by ticking the "Validate on project save" using the buttons at the bottom of the menu.

* Case standards - set the standard naming style for the entire project (e.g., UPPER_CASE, Title_Case, PascalCase, etc.). 

* Name mapping - here we can set the default names for the objects in our project. Tick the checkbox next to any object to override the default naming. Click the pencil icon to enter the expression editor. Here you can edit both the static part of the default naming, as well as use the context variables available to make the name dynamic.

![PK expression](assets/PK_expression.jpg)

### Diagram look and feel 

![diagram properties](assets/diagram_properties2.jpg)


5. Set diagram properties

* In the Diagram Explorer screen, open a diagram and expand the various options on the right-screen properties menu. 

In the view mode options [6], configure the preferred look and feel of the diagram.



6. Set relational notation


7. Switch view modes