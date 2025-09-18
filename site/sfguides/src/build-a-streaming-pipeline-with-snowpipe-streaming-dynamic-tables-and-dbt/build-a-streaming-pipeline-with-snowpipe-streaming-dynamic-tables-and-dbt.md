author: Sean Kim
id: build-a-streaming-pipeline-with-snowpipe-streaming-dynamic-tables-and-dbt
summary: This guide provides step-by-step instructions for building a production-grade streaming data pipeline in Snowflake with Snowpipe Streaming, Dynamic Tables and dbt Projects.
categories: data-engineering
environments: web
status: Draft 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Engineering, dbt, Streaming, IoT, Github, Dynamic Tables

# Build a Streaming Data Pipeline with Snowpipe Streaming, Dynamic Tables and dbt Projects
<!-- ------------------------ -->
## Overview 
Duration: 2

This guide teaches you to build a production-grade streaming data pipeline that ingests simulated real-time IoT weather and air quality sensor data from 8 locations across Sydney, Australia. You'll learn to ingest environmental readings (temperature, humidity, pressure) and air quality metrics (PM2.5, PM10, CO, CO2, O3, NH3, SO2) using Snowflake's Snowpipe Streaming: High-Performance Architecture. The project simulates realistic sensor behavior with location-specific characteristics, daily seasonality patterns, and anomaly detection.

The pipeline follows modern data engineering best practices with a medallion architecture (Bronze → Silver → Gold) implemented through Dynamic Tables deployed via dbt Projects, providing you with clean, tested, and documented data transformations.

### Prerequisites
- Familiarity with Snowflake
- Familiarity with Python
- Familiarity with dbt

### What You’ll Learn 
- How to ingest streaming data in near-realtime into Snowflake with [Snowpipe Streaming: High-Performance Architecture](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-high-performance-overview)
- How to create and run a dbt Project from a Git repository with Snowflake Workspaces for developer workflows
- How to configure and build Dynamic Tables with dbt

### What You’ll Need 
1. Snowflake Account - [Create a trial account](https://signup.snowflake.com)
  - Ensure you select **AWS** as your cloud provider
  - A Snowflake User with ACCOUNTADMIN role
2. Github Account
3. Python 3.10+ installed on your local machine

### What You’ll Build 

1. A Python IoT streaming data generator with Python
2. A real-time data ingestion pipeline with Snowpipe Streaming v2
3. A dbt data transformation project with Dynamic Tables
  - Bronze: Raw JSON sensor payloads
  - Silver layer: A dynamic table that materialises cleaned & flattened sensor readings
  - Gold layer: A set of dynamic tables for business-ready analytics and aggregations
  - Testing with dbt test
  - Documentation
4. A dbt Project running and deployed within the Snowflake account

<!-- ------------------------ -->
## Github Setup
Duration: 2

### About

GitHub is a collaborative version control platform for tracking changes and managing code for any application including data pipelines, ensuring reproducibility and teamwork.

You are required to have a Github account to perform the steps in this quickstart. You can sign-up for a free account [here](https://github.com/signup). Visit the [Github documentation](https://docs.github.com/en/get-started/start-your-journey/about-github-and-git) for further details.

### Repository

The Git repository for this quickstart can be found here: [Build a Streaming Data Pipeline with Snowpipe Streaming](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming). Clone the git repository into your local machine.

You can work directly with this repository for this Quickstart as we will only be reading from this repo. Forking is not necessary for this Quickstart.

<!-- ------------------------ -->
## Snowflake Setup
Duration: 10

> aside negative
> 
>  As of writing, Snowpipe Streaming v2 is currently in Public Preview for AWS accounts only. Ensure you are working with a Snowflake account hosted on AWS.

We will set up a Snowflake demo environment where all demo assets will be stored, as well as necessary Users and RBAC configuration.

### Create Streaming Service User

The Python Snowpipe Streaming SDK requires a user configured with Key-pair authentication. Run the following commands in your terminal to generate the keys:

```sh
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
```

Run the following command to generate the SQL to set the public key on the streaming user. Copy the output into your clipboard.

```sh
PUBK=$(cat ./rsa_key.pub | grep -v KEY- | tr -d '\012')
echo "ALTER USER STREAMING_INGEST_SVC_USER SET RSA_PUBLIC_KEY='$PUBK';"
``` 

Run the following SQL in Snowflake to create the service user:

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE USER STREAMING_INGEST_SVC_USER TYPE=SERVICE;

-- Configure Authentication Policy (optional, but recommended for explicit control)
CREATE OR REPLACE AUTHENTICATION POLICY STREAMING_USER_AUTH_POLICY
  AUTHENTICATION_METHODS = ('KEYPAIR')
  CLIENT_TYPES = ('SNOWSQL', 'DRIVERS');
ALTER USER STREAMING_INGEST_SVC_USER SET AUTHENTICATION POLICY STREAMING_USER_AUTH_POLICY;

-- Paste the output from the previous code snippet here:
--ALTER USER STREAMING_INGEST_SVC_USER SET RSA_PUBLIC_KEY='MII...'
```

### Create Database, Schema, Database Roles and Roles

Run the [set-up script](https://github.com/Snowflake-Labs/build-a-streaming-data-pipeline-with-snowpipe-streaming/blob/main/snowflake_setup/snowflake_env_setup.sql) in Snowflake to create the necessary database and schema objects.

The script installs the following:

- A PROD database
- BRONZE, SILVER, GOLD schemas
- PROJECTS schema where dbt Projects will be stored
- Ingestion landing table
- PIPE object for streaming ingestion
- Static lookup tables in the BRONZE schema
- Two roles: STREAMING_INGEST_ROLE and STREAMING_TRANSFORM_ROLE
  - STREAMING_INGEST_ROLE is granted to the streaming ingest service user
  - STREAMING_TRANSFORM_ROLE is granted to the human user running the script
- Two database roles: DB_WRITER and DB_READER
  - DB_READER is granted to DB_WRITER
  - DB_WRITER is granted to STREAMING_INGEST_ROLE

  (TODO: Diagram?)

### Grant Roles to Users

Run the following SQL to grant the roles to the newly created users:

```sql
GRANT ROLE STREAMING_INGEST_ROLE TO USER STREAMING_INGEST_SVC_USER;
ALTER USER STREAMING_INGEST_SVC_USER SET DEFAULT_ROLE=STREAMING_INGEST_ROLE;

--Grant dev role to current user
SET CURRENT_USER = (CURRENT_USER());
GRANT ROLE STREAMING_TRANSFORM_DEV_ROLE TO USER IDENTIFIER($CURRENT_USER);
ALTER USER IDENTIFIER($CURRENT_USER) SET DEFAULT_ROLE=STREAMING_TRANSFORM_DEV_ROLE;
```



<!-- ------------------------ -->
## Python Setup
Duration: 2

<!-- ------------------------ -->
## Run Python Streaming Client
Duration: 2

<!-- ------------------------ -->
## Create Workspace
Duration: 2

<!-- ------------------------ -->
## Run dbt Project
Duration: 2

<!-- ------------------------ -->
## Run dbt Tests
Duration: 2

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
- **id**: sample 
  - make sure to match the id here with the name of the file, all one word.
- **categories**: data-science 
  - You can have multiple categories, but the first one listed is used for the icon.
- **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
- **status**: Published
  - (`Draft`, `Published`, `Deprecated`, `Hidden`) to indicate the progress and whether the sfguide is ready to be published. `Hidden` implies the sfguide is for restricted use, should be available only by direct URL, and should not appear on the main landing page.
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Science, Twitter 
  - Add relevant  tags to make your sfguide easily found and SEO friendly.
- **authors**: Daniel Myers 
  - Indicate the author(s) of this specific sfguide.

---

You can see the source metadata for this guide you are reading now, on [the github repo](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md).


<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.


> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files

### Related Resources
- <link to github code repo>
- <link to documentation>
