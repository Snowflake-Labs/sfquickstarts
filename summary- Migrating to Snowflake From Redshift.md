summary: Migrating to Snowflake From Redshift
id: FintechMigrationOne
categories: Data Warehouse, Fintech, Migration
tags: medium
status: Published 
Feedback Link: https://developers.snowflake.com

# Migrating to Snowflake From Redshift
\<!-- ------------------------ --\>
## Introduction 
Duration: 1

In the following Devlab writeup, we will pretend we are a FinTech firm, Iceberg Portfolio Management, currently on AWS’s Redshift platform. The company has grown considerably over the past few months and we are beginning to experience concurrency issues from our BI platform, Looker. We are also worried about scalability as the company continues to increase its data footprint. The following guides will serve as a reference point for things to consider when migrating to Snowflake, as well as a framework for taking advantage of all aspects of the Snowflake architecture. By the end of this six part Devlab, your Snowflake environment will be able to handle workloads from data engineering to data science, eventually encompassing the backend for even your application as a whole. 

In this section, we are going to focus on the first step – Replacing your Redshift data warehouse. We will cover what to look out for when migrating and make sure the Snowflake architecture has the features and functionality currently in your Redshift environment.  

### What You’ll Learn 
- how to replicate your current data architecture in Snowflake
- how to repoint data ingestion pipelines
- how to update your BI frontend to run on Snowflake
- how to validate the migration was successful

\<!-- ------------------------ --\>
## Overview
Duration: 1

There are five major steps to migrating from a data warehouse to Snowflake, listed below. We will go through each five steps one by one, based on the fictional architecture of our prospective, fintech company, Iceberg Portfolio Management. 

1. Create the same database, schema, and table framework in Snowflake 
2. One-time data loads from Redshift to Snowflake
3. Repointing ETL pipelines into Snowflake. 
4. Setting up Snowflake as your backend for Looker.
5. Validating the data and sunsetting Redshift.


\<!-- ------------------------ --\>
## Creating the Data Warehouse Framework in Snowflake 
Duration: 10

The first step in migrating your data warehouse, is to make sure all data that you’re moving over has a place to go. In Snowflake, this is relatively straight forward with a few lines of SQL. While we also offer the ability to create databases, schemas and tables via the Snowflake UI, we will be using a more programmatic method to ease the lift and shift burden.

To start, you’ll want to identify which tables need to be migrated. Since the migration of data warehouses, is a, hopefully, infrequent occurrence, most use this time as a way to clear out tables and schemas that are no longer needed. 

At Iceberg Portfolio Management (IPM), every team has the create ability on the company’s shared redshift instance. Which means there are a number of tables that likely don’t need to be included in the migration effort. To find these tables, you can take a look at the underlying data tracked by Redshift.  **Take nightly snapshots** of `STL_SCAN`, `STL_QUERY`, and `SVV_TABLE_INFO`, and joining the tables together to give you an idea of which tables are actually being queried. `STL_SCAN` gives information about which tables are hit during a query, `STL_QUERY` will give the actual query text as well as the user who ran the query, and `SVV_TABLE_INFO` will provide data about the table itself. Choosing to not migrate jobs that are no longer used can greatly reduce the time of a migration, as well as clean up the schema.

Business intelligence is oftentimes the most difficult aspect of migration. A Looker model is a fairly hefty body of work to move, and in addition to the model itself, many business owners within the company will create their own content which needs to be rebuilt. The best way to track down which tables need to be migrated from a BI side, is to **send out surveys** asking folks to submit links to any dashboards or reports they use on a persistent basis, with what frequency, and an importance rating.  Also, be wary of reports that are only used on a periodic basis. Those reports may not be top of mind for their owners today, and might not appear in the Redshift usage metrics. However, when quarter close comes around and they’re missing, you’ll be sure to hear about it.

Once you’ve determined the list of your database objects using the usage metrics and team surveys, next you’ll want to convert the underlying DDL to Snowflake DDL. To get the Redshift DDL you can check the table `STL_DDLTEXT`. Additionally, here are two scripts you can run within Redshift, courtesy of [our friends at Instacart](#), 

[https://gist.github.com/tamiroze/a90a182da3ffa2f47c6b3b01320d79e6#file-run\_data\_migration-py](https://gist.github.com/tamiroze/a90a182da3ffa2f47c6b3b01320d79e6#file-run_data_migration-py)

[https://gist.github.com/tamiroze/30cca624b8098c62b26b0b9a8ac30059#file-redshift\_generate\_ddl-py](https://gist.github.com/tamiroze/30cca624b8098c62b26b0b9a8ac30059#file-redshift_generate_ddl-py)

Below is a list of data types and mappings, you should be aware of when converting.

Snowflake and Redshift data type discrepancies: 
- INT, BIGINT, SMALLINT, TINYINT in Redshift all map to NUMBER(38,0) in Snowflake

- DOUBLE, FLOAT, FLOAT4, FLOAT8 in Redshift are all synonymous with FLOAT in Snowflake (double-precision 64-bit IEEE 754 floating point numbers)

- All VARCHAR fields in Snowflake have a maximum length of 16 MB. There is limited benefit to declaring VARCHAR(16) vs VARCHAR(256) vs VARCHAR(16777216) like there would be in Redshift.

	- Some partner tools may benefit from declaring a smaller value for VARCHAR length, since those tools may internally allocate 16MB of memory for those strings (e.g., MicroStrategy)

- Be sure you understand how Snowflake deals with timestamps and timezones. The path of least resistance is to export all timestamp data in UTC from Redshift, and load as `TIMESTAMP_NTZ` in Snowflake.

Below is a Python script that can be used to convert a DDL of a Redshift table over to a DDL of a Snowflake table. While this should handle the majority of heavy lifting, we would recommend double checking all outputs before running in Snowflake.

[https://gist.github.com/tamiroze/dc0bdd596ed2c6b70fe921061401e739#file-sql2sf-py](https://gist.github.com/tamiroze/dc0bdd596ed2c6b70fe921061401e739)

Now that you have the Snowflake DDL for all tables on the migration list, feel free to run these in Snowflake.(1) After running this for IPM, our Snowflake cloud data warehouse is now set up with the proper database framework seen in our Redshift environment. Next up, is actual lifting and shifting of the data. 


(1) For the purposes of these training sessions, we will not be dealing with permissioning models, or table access rights. Please see our RBAC documentation for more information.


## One-time Data Loads from Redshift to Snowflake
Duration: 5

Loading data into Snowflake typically takes place from one of our supported cloud storage providers. In this case, since Redshift runs on AWS, we will be looking to unload data to S3, then load this data into our Snowflake instance. 

Redshift conveniently comes with an UNLOAD command that does this unloading into S3. The below command will unload data from the `emp` table to a private s3 bucket and path named `mybucket` and `mypath`, respectively:

	sql
	
	to 's3://mybucket/mypath/emp-'
	credentials 'aws_access_key_id=XXX;aws_secret_access_key=XXX'
	delimiter '\001'
	null '\\N'
	escape
	[allowoverwrite]
	[gzip];

Now, you can load this directly into Snowflake with the following COPY INTO command:
	sql
	
	copy into emp
	from s3://mybucket/mypath/
	credentials = (aws_key_id = 'XXX' aws_secret_key = 'XXX')
	file_format = (
	  type = csv
	  field_delimiter = '\001'
	  null_if = ('\\N')
	);

It’s important to note the above `file_format` is dependent on your underlying data. The `FIELD_DELIMITER` and `NULL_IF` values were chosen for this example because they match the default text formats for Hive and PostgreSQL COPY for unquoted strings, however, your specific use case might need different values. More information can be found [here](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table.html#optional-parameters). 

You can run the above two jobs for all underlying tables needed to be migrated. If you are migrating a large number of tables, you could programmatically update the table name and specific s3 bucket path based on the table’s schema and name. After completing, we now have two copies of all historic data- one in Redshift and one in Snowflake. Next up, is re-pointing our ingestion streams to Snowflake.

## Ingesting Data into Snowflake
Duration: 3

Migrating ingestion of data sources that move data into Redshift is relatively easy today, due to the flourishing cloud data ecosystem. Vendors such as Fivetran, Stitch, Matillion and Snowplow all have relatively turnkey integrations that can help get your data in. If a native Snowflake integration doesn’t exist, find or build a component to move data to S3, where [Snowpipe](https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro.html) can be configured to ingest it. 

It is important to note, Snowflake allows for ingestion of semi-structured data using our **variant** data type. While reviewing the ETL pipelines to push to Snowflake, oftentimes data engineers move from an ETL type structure to one of ELT. The data is loaded first in a semi-structured table, then tasks are ran to transform this data into its final format. (2)

The re-pointing of data ingestion tools, like Fivetran or Stitch, and auto-ingestion from S3 into Snowflake using Snowpipe with the above guide should be enough to get the majority of pipelines pointed to Snowflake from Redshift. 


2) Snowpipe will be covered in much more detail in a future devlab 

## Setting up Snowflake as the backend for Looker.
Duration: 2
  
Thanks, to Snowflake’s [many connectors](https://docs.snowflake.com/en/user-guide/conns-drivers.html) , there are a number of ways to connect to Snowflake. In this case, there is a custom connector in Looker to create the connection to your Snowflake account. Follow the [instructions on Looker’s site](https://docs.looker.com/setup-and-management/connecting-to-db#existing_database) to create the database connection. 

If your Looker models are based on underlying views, the migration effort of converting Redshift views to Snowflake views should handle the majority of the dashboarding backend. Fishtown Analytics, the makers of dBT, have put together a guide for the majority of syntax differences between Redshift and Snowflake. Use [this article](https://medium.com/@jthandy/how-compatible-are-redshift-and-snowflakes-sql-syntaxes-c2103a43ae84) as a reference when migrating your views to Snowflake. At the end of the day, there’s no substitution for running the view’s sql and handling the errors as they appear. In this case, we recommend you use Snowflake’s [Snowsight worksheet UI](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html). This comes with auto-completing formulas and better schema exploration to help you with any code conversion.

Following the above steps should give you the blueprint to begin the migration effort of BI dashboards to Snowflake. Just like the table migration earlier, this is a good opportunity to clean up any dashboards that aren’t being actively used. Once migrated, you should now have 2 data warehouses with the exact same underlying data, ingestion pipelines going to both locations, and the front end BI workload being handled by Snowflake. The last step is to make sure everything looks good and to turn off the lights on Redshift.

## Validating the Data
Duration: 2

There are numerous ways to validate the data in Snowflake is accurate, ranging from a simple count comparison on tables to comparing BI dashboard outputs. We recommend a little mix of both, with an emphasis on accurate KPIs between the two data warehouses.

For the overall architecture, we recommend handling following Instacart’s instructions on this comparison:
 
- Select count of each table and compare results with Redshift.
- Select count distinct of each string column and compare with Redshift.
- Structure comparison of each table.
- Simple check if table exists.
- Select sum of each numeric column and compare with Redshift. 

For the KPI and BI level comparison, a framework like [Great Expectation](https://docs.greatexpectations.io/en/latest/)  can help data and analytics teams construct test suites. If numbers appear to be off, the likely culprit we see is timezone issues. For these concerns, Hashmap produced a [comprehensive guide](https://community.snowflake.com/s/article/The-Hitchhiker-s-Guide-to-Timestamps-in-Snowflake-Part-1) that would be worth the read. 

Ideally, the checks above produce equal results on both Redshift and Snowflake. This means the migration has been successful and the migration has reached its close. When you feel comfortable, close down your Redshift instance.


## Conclusion
Duration: 2

In our example, Iceberg Portfolio Management has now replaced Redshift with Snowflake. End users are now getting the added benefit of Snowflake’s built-in concurrency processes. Database Administrators are getting the benefit of Snowflake’s cloud services. And the company is driving forward on revenue goals while dropping the overall data infrastructure costs. 

However, the work is far from done. Snowflake can do much more than just replace Redshift. In the coming sections, we will expand on the Snowflake workloads. Taking advantage of the additional features to move from having a Data Warehouse to a Data Platform. Stay tuned for Chapter 2: Moving from ETL to ELT. 