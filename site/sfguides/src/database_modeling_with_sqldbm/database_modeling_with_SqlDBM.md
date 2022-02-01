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

3. Click the "Connect to DW" to create a live connection to Snowflake.

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

    * Parsing and importing DDL into a project is called **Reverse Engineering** in SqlDBM and is not limited to new projects. This can be done at any point to retrieve changes to the database made outside of SqlDBM from the Reverse Engineering screen. 
    * Note, this will not re-initiate the entire project. Users will be able to choose which objects are added, updated, or deleted from a project depending on whether or not they currently exist. 

    
![Reverse Engineering ](assets/RE.png)

<!-- ------------------------ -->
## Configure project defaults
Duration: 5

Let's configure some initial time-saving defaults for our project as well as set the visual level of detail and look-and-feel for our diagrams.

![project settings](assets/project_settings.jpg)

1. Save first revision and name your project

    * Click the save button at the top right and name your project with something descriptive. [1]


2. Rename revision title

    * Let's rename "Initial Revision" to something that fits with your way of working. Name your revisions based the Agile Sprint, current project phase, or even calendar month. Something to allow for a meaningful grouping of changes. 

    * Click on the text "Initial Revision" to modify it. [2]

3. Enable dark theme

    * Click on the blue SqlDBM logo at the top left to bring up the project menu. Click "Dark Theme" to enable it, if that's your thing. [3]

4. Set naming conventions for the project

    * Click on the blue SqlDBM logo at the top left to bring up the project menu and select "Naming Conventions". [4]

    * Any changes made here can be "[applied] to all existing objects" and validated going forward by ticking the "Validate on project save" using the buttons at the bottom of the menu.

    * Case standards - set the standard naming style for the entire project (e.g., UPPER_CASE, Title_Case, PascalCase, etc.). 

    * Name mapping - here we can set the default names for the objects in our project. Tick the checkbox next to any object to override the default naming. Click the pencil icon to enter the expression editor. Here you can edit both the static part of the default naming, as well as use the context variables available to make the name dynamic.

![PK expression](assets/PK_expression.jpg)


## Diagram look and feel 
Duration: 3


Get familiar with the look-and-feel configuration for diagrams and learn to view them at varying levels of detail. 

![diagram properties](assets/diagram_properties2.jpg)


1. Set diagram properties

    * In the Diagram Explorer screen, open a diagram and expand the various options on the right-screen properties menu. 

    * In the view mode options, configure the preferred look and feel of the diagram. Here you can select which object properties will be displayed and color-coded on the diagrams. 

2. Set relational notation

    * Toggle between IDEF1X and Crow's Foot relationship notations in the "Notation" options. Note that relationship properties such as Identifying/Non-identifying (IDEF1X) and cardinality (Crow's Foot) will change accordingly. These properties are orientative and do not impact the generated DDL.

3. Change view modes (level of detail)

    * Once defined, database objects in SqlDBM diagrams can be viewed at varying levels of detail. This allows a single diagram to serve various business functions: from general planning to column-level auditing. 

    * You can get a feel for the different view modes by clicking on the "View Mode" selector on the top of the screen


View Mode | Description
---------|----------
 Table | Simplified view showing tables as boxes, providing a bird's-eye view.
 PK/AK | Shows only the primary and alternate key columns.
 Keys | Shows the primary, alternate, and foreign key columns. 
 Columns | Default view. All columns and properties are displayed.
 Descriptions | Simplified view showing tables as boxes with descriptions.
 Logical | Displays all columns, hides physical names and database-specific properties.



## Editing objects
Duration: 6 

Let's organize our project by creating some subject areas. These serve as folders for keeping your diagrams organized. Then we'll learn to create and edit its properties, as well as add/copy fields. 


![create a subject area and add tables](assets/new_diagram.gif)

### Create a Subject Area
Subject areas serve as folders for keeping diagrams organized by categories such as department or project. In the Diagrams screen, right-click on "Subject Areas" and select "Add a Subject Area". 

### Add a table to a diagram
Click on the "Diagram Explorer" button on the left-menu. Add a table to a diagram from the catalog of object by searching for part of the table name, then clicking the "Add to Diagram" button next to it. 

![name table, add pk, copy columns](assets/create_table.gif)

### Create a new table
Right-click anywhere on the canvas to and select "Add Table." Double-click on the new table to edit it. Give the table a name and add some columns with corresponding data types. 

### Copy columns from an existing table
Select a column (or shift-click to select multiple) from an existing table and drag them to another table to move them. Perform the drag operation holding the Ctrl key (Command on Mac) to copy. 

### Add a primary key (PK) to a table
Double click on a table to enter edit mode. Create a new column at the topmost section to designate it as a primary key (replacing "\<pk column name\>"). 

Alternatively, drag any existing column to the top of the table to designate it as a PK.

### Add a foreign key (FK) to a table
Click on a table which has a PK defined. Drag the bottom-right connector to another table to add it there as a FK.

![add primary and foreign keys](assets/child_parent.png)

### Create a child or parent table
Select a table in the diagram. Use the top-left or bottom-right connectors to create a parent or child table, respectively. 

Parent tables PKs will cascade to the child tables.

### Create a template
Templates save time by allowing you to define and reuse columns at your convenience. 

![template](assets/template.png)

Find "Templates" in the "Database Explorer" screen (third option from the top in the left-hand menu) and click to "Create New."

Click on the newly created template to select it and set the Template Properties on the right-hand menu.

* Template name: give the template a descriptive name, like "MetadataColumns" for example.
* Apply to new tables: tick this option if you want this template to apply automatically to all newly created tables.
* Columns: add the columns that you would like to be part of the template. In this example, let's add EtlId as date and EtlName as varchar. Be sure to provide a description.
* Description: provide a general description for the template
* Related tables: metadata showing which tables are currently associated with the existing template 

### Assign a template to a table 
Let's assign the metadata columns from the template that we just created to a table. Select a table to bring up its properties in the right-hand menu. Expand the "Options" menu and scroll down to the "Templates" text-area. 

Begin typing the template name and select it from the auto-suggestion. Hit "Add" to associate it with the table. 

Keep in mind that while the association exists, changes to the template will be reflected in the associated tables as well. To break the association, click the "X" next to the template name in the table options; you will be given a choice to keep or delete the template columns in the process. 


## Set Snowflake table properties
Duration: 4
SqlDBM's no-code interface is intended to minimize syntax errors associated with manually keying DDL. By using a GUI to manipulate database objects, SqlDBM generates neat, error-free, database-specific DDL behind the scenes. 


### Column-level properties 
Select a table from your diagram and highlight column to bring up its properties in the right-hand menu. 

* The available properties vary depending on the column data type. Set general properties like "Default Value" or data-type-specific setting like sequences accordingly.

![column properties](assets/column_prop.png)

### Table-level properties
Select a table on the diagram (or from the list on Database/Diagram Explorer) to bring up its properties in the right-hand menu. 

Review and set the following options as needed: 

![table properties](assets/table_prop.png)


1. Clusters and Keys - use the available options in this menu to view, modify, and create primary, alternate, and clustering keys. 

1. Options - Specify transient and data retention properties as well as setting file format
    * Transient: mark this flag to designate a table as transient (no Fail-safe)
    * Data Retention Time (Days): specify 0 or 1 days for Snowflake time travel function
    * File Format: select a file format for use with loading and unloading data

1. Copy Options - specify the copy options for loading and unloading operations such as on-error and purge

1. Post script - Specify manual post-script commands to be injected into the create statement (such as grants).



## Add functional information and comments
Duration: 5 

Add some functional details to your project to give it some context and make it easier for team members to navigate. 

### Notes on diagram
Add descriptive notes anywhere on the diagram by using the "Add Note" (Ctrl+Insert) feature. 


![notes](assets/notes.png)

### Data dictionary
SqlDBM's **Data Dictionary** allows users to review and edit object-level comments in one centralized and searchable screen. The descriptions provided here are intended to help the team go beyond object definitions and provide meaningful details about the data contained in the tables. 

The descriptions provided here will become part of the object DDL and can be deployed back to the database (see Forward Engineering topic ahead) - they are not meant to serve merely as project metadata.


1. Access the Data Dictionary screen by selecting the book icon on the left-hand menu. 

2. Use the search-box to perform a wildcard lookup for objects, columns, and descriptions matching a given term. 

3. Enter object-level or column-level descriptions in the description fields. By design, other DDL details such as object names, datatypes, and properties can not be changed on this screen. This allows users from any level of technical experience to contribute to a project without the possibility of changing any structural details.

4. Template descriptions - located at the bottom of the screen - can also be maintained here. Note that the description is displayed in related tables but can only be edited in the template itself.

5. The Import/Export to Excel buttons are located at the top-right of the screen. This allows users to contribute to a project by maintaining descriptions in a familiar Excel format, also without the possibility of modifying the object structure. 

    * Click the "Export to Excel" button to generate and download the data dictionary in Excel format. 
    * The Excel follows a similar format as the Data Dictionary screen: only the descriptions are editable (highlighted in orange). Modifying any other field (not highlighted in orange) will have not effect on the project, but will result in a failure to update the related description.
    * Once you have added some descriptions to the file, save it, and press the "Upload" button to incorporate the changes into the project. 
    * Search for all or part of a description entered in the previous step to navigate directly to it. 
    * Save the project to complete the process

![documentation](assets/documentation.png)

## Change tracking
Duration: 2

Every save in SqlDBM generates a versioned _revision_ which allows for change tracking and version control. SqlDBM projects store an infinite revision history and any two revisions can be compared to track changes. The latest revision is indicated next to the project name at the top of the screen (v12 in the example below). 

![documentation](assets/revisions.png)

### Review the latest changes
The next section will cover deployment. To review the changes that were made as part of this exercise, we will use the **Compare Revisions** feature of SqlDBM. 

1. Click on the "Compare Revisions" icon on the left-hand menu.

2. The latest two revisions are selected by default. Select any two revisions to see the cumulative changes between them. Changes are highlighted based on the following color scheme:


Color | Description
---------|----------
 Green | New object / addition
 Yellow | Modification 
 Red | Deletion

3. Click on any object on the top half of the screen to see the details of the change. 

## Deployment
Duration: 5

The time has come to deploy all of the changes made during this exercise to a Snowflake environnement. 

In SqlDBM, DDL is generated through a function known as **Forward Engineering**. There are two options: create SQL and alter SQL. The first (create) generates a create statement for selected objects as of the latest revision. The second (alter), creates an alter script from a previous revision. 

![forward engineer](assets/create_sql.png)

1. Access the Forward Engineering screen by clicking on the scroll icon on the left-hand menu.

### Generate create script
This option will generate a "create" script for deploying new objects (or overwriting existing depending on the options).



Generate alter script from project import
Deploy changes
