author: Mary Law
id: better-together-snowflake-sv-amazon-quicksight
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/snowflake-feature/business-intelligence, snowflake-site:taxonomy/snowflake-feature/cortex-analyst
language: en
summary: This is a Quickstart for building Snowflake and Amazon Quicksight highlight Snowflake Semantic View as part of better together enablement
title: Better Together: Unleash AI-Powered BI with Snowflake Semantic View and Amazon Quick Sight 
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
fork repo link: <optional but modify to link to your repo>
open in snowflake: <[Open in Snowflake](https://signup.snowflake.com/)>


# Better Together: Unleash AI-Powered BI with Snowflake Semantic View and Amazon Quick Sight 
<!-- ------------------------ -->
## Overview 

Unlock the full potential of your data with the powerhouse combination of [Snowflake](https://www.snowflake.com/en/) and [Amazon Quick](https://aws.amazon.com/quicksuite/). Say goodbye to data silos and hello to seamless, intelligent insights. As a multi-award-winning [AWS Technology Partner](https://www.snowflake.com/en/why-snowflake/partners/all-partners/aws/) (Winner- Global Data & Analytics Partner -2023, 2024, 2025) with multiple AWS accreditations that include AWS ISV Competencies in Generative AI, Machine Learning, Data and Analytics, and Retail. Snowflake powers AI, data engineering, applications, and analytics on a trusted, scalable AI Data Cloud—eliminating silos and accelerating innovation.

This Quickstart demostrates the integration between Snowflake and [Amazon Quick Sight](https://aws.amazon.com/quicksuite/quicksight/) to deliver AI-powered BI capabilities and unified intelligence across all your enterprise data sources, and bridges the critical "last-mile gap" between insights and action.

The integration showcases Snowflake's [semantic view](https://docs.snowflake.com/en/user-guide/views-semantic/overview), a new schema-level object in Snowflake. Semantic view provides the meaning and business context to raw enterprise data - "metrics" (eg. total view, user_rating) and "dimensions" (e.g., movie, genre), acting as a reliable bridge between human language and complex data structures. By embedding organizational context and definitions directly into the data layer, semantic views ensure that both AI and BI systems interpret information uniformly, leading to trustworthy answers and significantly reducing the risk of AI hallucinations. You can use semantic views in Cortex Analyst and query these views in a SELECT statement. You can also share semantic views in [private listings](https://docs.snowflake.com/en/collaboration/provider-listings-creating-publishing.html#label-listings-create), in public listings on the [Snowflake Marketplace](https://app.snowflake.com/_deeplink/marketplace), and in organizational listings. By adding business meaning to physical data, the semantic view enhances data-driven decisions and provides consistent business definitions across enterprise applications. Lastly, as native Snowflake schema objects, semantic views have object-level access controls. You can grant or restrict usage and query rights on semantic views just as with tables and views, ensuring authorized, governed usage across SQL, BI and AI endpoints.  You can read more about how to write “Semantic SQL” [here](https://docs.snowflake.com/en/user-guide/views-semantic/querying).

<br>

![Semantic View diagram](assets/semantic-views-diagram.png)

## Usecase

This integration leverages Snowflake's native capabilities to ingest structured movie review data directly from Amazon S3 into a database schema. Defining a Snowflake semantic view with table, relationships, dimensions, and metrics to enhance AI-powered analytics. Semantic models are shifted from individual BI tool layers to the core data platform, guaranteeing that all tools utilize the same semantic concepts.  

**🔑 Key Steps and Benefits:**  

**1. Data Ingestion and Semantic View Creation**: Data is loaded from Amazon S3 using Snowflake's native ingestion tools. A semantic view is then established to simplify the database structure for business users.  
**2. Self-Serve Analytics with [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)**: Business teams and non-technical users can perform self-serve analytics using natural language queries via Snowflake Cortex Analyst, gaining instant insights from the structured data in Snowflake.  
**3. Amazon Quick Sight Integration**: Snowflake Notebook is used to programmatically interact with [Amazon Quick Sight API](https://boto3.amazonaws.com/v1/documentation/api/1.12.0/reference/services/quicksight.html) to set up integration and create a data source and data set.  
**4. Enhanced AI-powered BI**: This integration empowers the BI team to use natural language for creating interactive charts/dashboards, building calculated fields, developing data stories, and conducting what-if scenarios and significantly reducing the risk of AI hallucinations.  

![architecture diagram](assets/arch.png)

<br>

### What You’ll Learn 

- How to setup a Snowflake warehouse, database and schema
- How to load data into Snowflake from Amazon S3
- The process of defining a Snowflake semantic view with tables, relationships, dimensions, and metrics
- Introduction to Snowflake [Notebook](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-notebooks/)
- How semantic views enhance AI-powered analytics (Cortex Analyst) and consistency across BI tools (Amazon Quick Sight via [API call](https://boto3.amazonaws.com/v1/documentation/api/1.12.0/reference/services/quicksight.html))
  


### What You’ll Build 
You will build a foundational yet practical setup of a Snowflake semantic view, complete with data views and a defined semantic model, enabling consistent data querying for AI and BI with Amazon Quick Sight.



### What You'll Need
- Familiarity with [Snowflake](/en/developers/guides/getting-started-with-snowflake/). If you do not have an account, sign up for a [trial account here](https://signup.snowflake.com/)
  - Access to ACCOUNTADMIN role is required for creating semantic views
- Familiarity with AWS. If you do not have an account, [signup for an AWS Account](https://docs.aws.amazon.com/quicksuite/latest/userguide/setting-up.html#sign-up-for-aws) and [Quick Suite](https://docs.aws.amazon.com/quicksuite/latest/userguide/signing-in.html)

  **Ensure to sign up to both of the above in AWS US West (Oregon)** 
  At launch, Quick is available in 4 Regions: US East (N. Virginia), US West (Oregon), Asia Pacific (Sydney), and Europe (Ireland). Refer to See the [Amazon Quick documentation](https://docs.aws.amazon.com/quicksuite/latest/userguide/regions.html)
- Basic knowledge of SQL and Python
- Familiarity with data analysis concepts
<br>

<!-- ------------------------ -->

## Setup Environment

### Download the Notebook

Firstly, to follow along with this quickstart, download the Notebook [update-me-better-together-snowflake-sv-amazon-quicksight.ipynb](https://github.com/update-me-sfquicksight.ipynb) from GitHub.

>Snowflake Notebooks come pre-installed with common Python libraries for data science and machine learning, such as `numpy`, `pandas`, `matplotlib`, and more! 
If you are looking to use other packages, click on the Packages dropdown on the top right to add additional packages to your notebook.

After login to Snowflake, click on the "+" (Create) to import the notebook we downloaded.


![import notebook](assets/import-notebook.png)
![import notebook](assets/import-notebook2.png)

### Setup your Database and Schema

First, we'll create a new database named `SAMPLE_DATA` and a schema named `TPCDS_SF10TCL` to organize our data. We will then set the context to use this new schema.

```sql
-- Create a new test database named SAMPLE_DATA
CREATE DATABASE SAMPLE_DATA;

-- Use the newly created database
USE DATABASE SAMPLE_DATA;
```

<!-- ------------------------ -->
## Setting up the Data in Snowflake

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
* Create Snowflake objects (warehouse, database, schema, raw tables)
* Ingest data from S3 to raw tables
* Create review view 

### Creating Objects, Loading Data, and Joining Data
* Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
* Paste and run the following SQL in the worksheet to create Snowflake objects (warehouse, database, schema, raw tables), ingest shift  data from S3,  and create the review view

  ```sql

  USE ROLE sysadmin;

  /*--
  • database, schema and warehouse creation
  --*/

  -- create tb_voc database
  CREATE OR REPLACE DATABASE tb_voc;

  -- create raw_pos schema
  CREATE OR REPLACE SCHEMA tb_voc.raw_pos;


<!-- ------------------------ -->
## Setting up Snowflake Notebook
### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

* Download the notebook **xxxxx.ipynb** using this [link](https://github.com/Snowflake-Labs/xx/tree/main/notebook)

* Navigate to Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on Projects -> Notebook

* Using the import button on the top right, import the downloaded notebook.

* Provide a name for the notebook and select appropriate database `tb_voc`, schema `analytics` and warehouse `tasty_ds_wh`

* Open the notebook once created and add the following packages by using the "Packages" button on the top right
  * snowflake-snowpark-python
  * snowflake-ml-python

* Now you are ready to run the notebook by clicking "Run All" button on the top right or running each cell individually. 





## Conclusion And Resources

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Snowflake Guide](#)

### What You Learned
- Basics of creating sections
- adding formatting and code snippets
- Adding images and videos with considerations to keep in mind

### Related Resources
- <link to github code repo>
- <link to related documentation>
* [Getting started with Semantic views](https://www.snowflake.com/en/developers/guides/snowflake-semantic-view/#0)  
* [Getting Started with Cortex Analyst](https://www.snowflake.com/en/developers/guides/getting-started-with-cortex-analyst/)
