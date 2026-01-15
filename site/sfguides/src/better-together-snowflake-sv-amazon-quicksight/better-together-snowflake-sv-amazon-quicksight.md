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

We leverage Snowflake native ingestion capabilities to ingest data from Amazon S3 into Snowflake. We then load the structured movie review data into a database schema and create a semantic view that bridges the gap between business users and databases. [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) then allows self-serve analytics via natural language queries for business teams and non-technical users with instant answers and insights from their structured data in Snowflake. We will then export the semantic view for metadata extraction via Snowflake notebook which enriches the data for Amazon Quick Sight integration as Topics. This allows the BI team to create interactive charts/dashboard, build calculated fields, create data stories, build scenarios (what-if) all via natural language.


The end-to-end workflow will look like this:

![architecture diagram](assets/xx-diagram.png)

<br>

### What You’ll Learn 

- How to setup a warehouse, database and schema in Snowflake
- How to load data into Snowflake from Amazon S3
- The process of defining a Snowflake semantic view with tables, relationships, dimensions, and metrics
- Introduction to Snowflake notebook [Notebook](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-notebooks/)
- How semantic views enhance AI-powered analytics (Cortex Analyst) and consistency across BI tools (Amazon Quick Sight) 


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

Firstly, to follow along with this quickstart, download the Notebook [update-me-better-together-snowflake-sv-amazon-quicksight.ipynb](https://github.com/update-me-quicksight.ipynb) from GitHub.

Snowflake Notebooks come pre-installed with common Python libraries for data science and machine learning, such as `numpy`, `pandas`, `matplotlib`, and more! If you are looking to use other packages, click on the Packages dropdown on the top right to add additional packages to your notebook.

### Setup your Database and Schema

First, we'll create a new database named `SAMPLE_DATA` and a schema named `TPCDS_SF10TCL` to organize our data. We will then set the context to use this new schema.

```sql
-- Create a new test database named SAMPLE_DATA
CREATE DATABASE SAMPLE_DATA;

-- Use the newly created database
USE DATABASE SAMPLE_DATA;
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

<!-- ------------------------ -->

<!-- ------------------------ -->
## Headers and Subheaders

Keep the headers to a minimum as a best practice.
These show up as your menu on the right.  Keeping them short (3-4 words) helps keep the guide precise and easy to follow.



### Formatting Operations

You can format various elements in markdown format in your guide.
Details of that are available at: 

[Get Started with Guides](##) to refresh markdown to add formatting, generate code snippets, info boxes, and download buttons etc. 


The guide linked above explains how you can use various formatting elements and the tag categories etc. to keep in mind when drafting your guide.<br>
Please use the guide to add elements to your markdown within this template.  <p>


> NOTE:
> This template is an example of the layout/flow to use.



<!-- ------------------------ -->
## Adding Appropriate Tags 

**Content Type & Industries Tags** 
- Pick the appropriate content type that applies to your Guide. This helps with filtering content on the website.
- If relevant, please pick industry tags as well so content is reflected appropriately on the website.

- Languages
Guides are available in various languages for the regions.
specific language tags must be added to the document to ensure the regional pages can see your guide.

**Please pick from the list of languages** 
- These are the supported exact acronyms used on the main page.  
- Deviating from the accronyms means your pages will not show up on the regional pages.


**Please pick tags from the list of 3 types of categories** 
- DO NOT create new tags if you don't see them in the list.  


A complete list of the language and category tags is available here: https://www.snowflake.com/en/developers/guides/get-started-with-guides/#language-and-category-tags



<!-- ------------------------ -->
## Images and Videos

Ensure your videos are uploaded to the YouTube Channel (Snowflake Developer) before you start working on your guide.

You have the option to submit videos to Snowflake Corporate channel, Developers Channel or International Channel.
Use this link to [submit your videos](https://www.wrike.com/frontend/requestforms/index.html?token=eyJhY2NvdW50SWQiOjE5ODk1MzYsInRhc2tGb3JtSWQiOjExNDYyNzB9CTQ4NDU3Mjk1MjcxNjYJMTk3ZmNhNWQ1ODM5NTc1OGI2OWY5Mjc4Mzk4M2YwOGQ1Y2RiNGVlMGUzZDg3OTk3NzI3N2JkMTIyOGViZTdjMQ==)


Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
Image Guidelines: 
- Naming convention should be all lower case and include underscores (no hyphens)
- No special characters 
- File size should be less than 1MB. Gifs may be larger, however, should be optimized to prevent reduction of page load times
- Image file name should align to the name in .md file (this is case sensitive) 
- All images should be added to the 'assets' subfolder for your guide (please do not create additional subfolders within the 'assets' subfolder)
- No full resolution images; these should be optimized for web (recommended: tinypng) 
- Do no use HTML code for adding images



<!-- ------------------------ -->
## Conclusion And Resources

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Snowflake Guide](#)

### What You Learned
- Basics of creating sections
- adding formatting and code snippets
- Adding images and videos with considerations to keep in mind

### Related Resources
- <link to github code repo>
- <link to related documentation>
- [Getting started](https://www.snowflake.com/en/developers/guides/snowflake-semantic-view/#0) with Semantic views

### EXAMPLES:
* **Logged Out experience with one click into product:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)
* **Simple Hands-on Guide**: [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)
