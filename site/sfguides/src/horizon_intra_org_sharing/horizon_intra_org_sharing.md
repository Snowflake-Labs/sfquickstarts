author: Vinay Srihari, Matthias Nicola
id: horizon_intra_org_sharing
summary: This guide demonstrates Horizon features for sharing data and applications intra-company
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: horizon-access,data-sharing,summit-hol
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Summit Lab, Data Sharing, Horizon Access

# Horizon Intra-Company Data Sharing
<!-- ------------------------ -->
## Overview 
Duration: 10

Sharing information between departments, business units and subsidiaries of a company is critical for success, particularly when there are organizational silos in place. A modern data platform must provide decentralized ownership, universal discovery, access control, federated governance, and observability. 

**Snowflake Horizon** is a suite of capabilities broken down into five pillars - the focus of this quickstart is <mark>Access</mark> 
<Image Here>

The objective of the Access pillar is to make it simple to share, discover, understand/build trust and access listings across any boundary, internal or external to the organization, and to make loose objects discoverable across account boundaries within an organization, supported by the tools necessary to ensure policy compliance, security, and data quality.

In this lab you will experience the latest **Snowflake Horizon Access pillar** features for sharing data and applications intra-company: organizational listings, unified search & discovery, data quality monitoring, role-based governance policies and programmatic management of data products. We will cover structured and unstructured data that is stored on-platform or on external storage.

### Prerequisites
- #### Create 3 Snowflake Trial Accounts in the same Snowflake Organization: two in AWS_US_WEST_2 region, one in AZURE_WESTEUROPE
    > Signup for an AWS trial account [here](https://signup.snowflake.com/)
    >
    > - choose **AWS** as cloud provider, **Business Critical** edition, **AWS_US_WEST_2 (Oregon)** region
    > - activate account with username `horizonadmin` (has ACCOUNTADMIN, ORGADMIN roles)
    > - login and create a SQL Worksheet named _**Account Setup**_
    >
    > Execute the following SQL commands in the _**Account Setup**_ worksheet to bootstrap:
    > 
    > ```sql
    > use role accountadmin;
    > create or replace warehouse compute_wh WAREHOUSE_SIZE=medium INITIALLY_SUSPENDED=TRUE;
    > create database if not exists snowflake_sample_data from share sfc_samples.sample_data;
    > grant imported privileges on database snowflake_sample_data to public;
    > 
    > select current_user(), current_account(), current_region(), current_version();
    >
    > -- Create a second AWS trial account
    > use role orgadmin;
    > create account horizon_lab_aws_consumer
    >   admin_name = horizonadmin
    >   admin_password = 'FILL_IN_PASSWORD'
    >   email = 'FILL_IN_EMAIL'
    >   must_change_password = false
    >   edition = business_critical
    >   region = AWS_US_WEST_2;
    > 
    > -- Create an Azure trial account
    > use role orgadmin;
    > create account horizon_lab_azure_consumer
    >   admin_name = horizonadmin
    >   admin_password = 'FILL_IN_PASSWORD'
    >   email = 'FILL_IN_EMAIL'
    >   must_change_password = false
    >   edition = business_critical
    >   region = AZURE_WESTEUROPE;
    >
    > -- Note the ORGANIZATION_NAME and ACCOUNT_NAME for the Trial AWS Provider account
    > show organization accounts;
    > ``` 
    >
    > Login to the two new accounts as `horizonadmin` and run these commands in a worksheet
    > ```sql
    > use role accountadmin;
    > create or replace warehouse compute_wh WAREHOUSE_SIZE=medium INITIALLY_SUSPENDED=TRUE;
    > create database if not exists snowflake_sample_data from share sfc_samples.sample_data;
    > grant imported privileges on database snowflake_sample_data to public;
    > 
    > select current_user(), current_account(), current_region(), current_version();
    > ```
- #### [Install SnowSQL](https://docs.snowflake.com/en/user-guide/snowsql-install-config.html#installing-snowsql) (CLI Client): used to load data into a Snowflake internal stage 
     

### What You’ll Learn 
- How to blend TastyBytes Point-of-Sale and Marketplace Weather data to build analytics data products, then publish Listings targeted at accounts in your company 
- How to configure data privacy polices that are preserved in the consumer accounts that install the listings. Tag-based column masking, row-access, aggregation and projection policies will be created with database roles.
- How to setup Data Metrics Functions to monitor data quality of the shared data products
- How to share Iceberg Tables within a cloud region
- How to share unstructured text files and process with Cortex LLM functions
- How to share a native application with Streamlit visualization
- How to use Universal Search and Snowflake Copilot to explore data from all sources

### What You’ll Need 
- Basic knowledge of SQL, Database Concepts, Snowflake [Listings](https://other-docs.snowflake.com/en/collaboration/collaboration-listings-about)
- Familiarity with [Snowsight Worksheets](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs)
- Quick Review of [SnowSQL CLI]((https://quickstarts.snowflake.com/guide/getting_started_with_snowsql/index.html?index=..%2F..index))

### What You’ll Build 
- Analytics data products for TastyBytes, that models a global food truck network with localized menu options in 15 countries, 30 major cities and 15 core brands
- Listings comprised of metadata, data and application code, targeted at accounts in the same organization but in different cloud regions
- Governance policies based on shared role-based-access-controls that are enforced at the target account consuming the listing
- Install listings containing Iceberg Tables, then blend with local datasets to derive insights
- Exploration of all shared and local data with Universal Search and Copilot 

<!-- ------------------------ -->
## Citations and Terms of Use

Raw text data provided for this lab is an extract from the [IMDB Large Movie Review Dataset](https://ai.stanford.edu/~amaas/data/sentiment/)

Use of this dataset requires that we cite this ACL 2011 paper by Andrew Maas, et al:
@InProceedings{maas-EtAl:2011:ACL-HLT2011,
  author    = {Maas, Andrew L.  and  Daly, Raymond E.  and  Pham, Peter T.  and  Huang, Dan  and  Ng, Andrew Y.  and  Potts, Christopher},
  title     = {Learning Word Vectors for Sentiment Analysis},
  booktitle = {Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies},
  month     = {June},
  year      = {2011},
  address   = {Portland, Oregon, USA},
  publisher = {Association for Computational Linguistics},
  pages     = {142--150},
  url       = {http://www.aclweb.org/anthology/P11-1015}
}

[Weather Source LLC: frostbyte](https://app.snowflake.com/marketplace/listing/GZSOZ1LLEL/weather-source-llc-weather-source-llc-frostbyte) Marketplace listing requires accepting terms of use by the Provider and Snowflake.

<!-- ------------------------ -->
## Horizon Provider Account Setup (AWS Trial)
Duration: 10

Download ZIP or Clone [sfguide-horizon-intra-organization-sharing)](https://github.com/Snowflake-Labs/sfguide-horizon-intra-organization-sharing) Github repo to your local machine

![Code Button](assets/code-download.png)

To simplify lab instructions, from a Terminal copy scripts folder to `/tmp` 
```bash
cp -r sfguide-horizon-intra-organization-sharing /tmp
```

Load the SQL scripts into [Snowsight Worksheets](ttps://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs#create-worksheets-in-sf-web-interface) - one script per worksheet

![Create Worksheet](assets/create-worksheets.png)

### Execute Setup SQL Scripts

1. `100_Setup_Data_Model`: create the TastyBytes foundational data model. 
[TastyBytes](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html#3) is a fictitious global food truck network that operates in 30 major cities located in 15 countries with localized menu options and brands. The single `Frostbytes_Tasty_Bytes` is organized in the following schemas:
  - `RAW_CUSTOMER`: raw customer loyalty data with personally identifiable information (PII)
  - `RAW_POS`: raw point-of-sale data denormalized by orders, menu, franchise and country 
  - `HARMONIZED`: blended metrics for customers and orders
  - `ANALYTICS`: analytic data that delivers insights for aggregate trends and drill down

Use __Run All__ pulldown to run the script

![Run All in Worksheet](assets/SAMPLE.jpg)

2. `200_Setup_Data_Products`: build data assets to share in a Listing.
First acquire <mark>Weather Source LLC</mark> listing from Marketplace and install as shared database `FROSTBYTE_WEATHERSOURCE`

```sql
-- Step 1(a) - Acquire "Weather Source LLC: frostbyte" Snowflake Marketplace Listing

/*--- 
    1. Click -> Data Products (Cloud Icon in left sidebar)
    2. Click -> Marketplace
    3. Search -> frostbyte
    4. Click -> Weather Source LLC: frostbyte
    5. Click -> Get
    6. Click -> Options
    6. Database Name -> FROSTBYTE_WEATHERSOURCE (all capital letters)
    7. "Which roles, in addition to ACCOUNTADMIN, can access this database?" -> PUBLIC
    8. Click -> Get
---*/
```

Before proceeding, check that all these databases are now visible in the Databases tab in the left panel

![Database-Explorer](assets/SAMPLE.jpg)

Switch back to the Worksheets tab, then execute `Step 1(b)`, `Step 2`, `Step 3`, `Step 4`, `Step 5`, `Step 6`, `Step 7`. 
This will create secure views, materialized views, functions and dynamic tables in the ANALYTICS schema, and an internal stage for sharing text data. 

Check out all the new objects created in the ANALYTICS schema in the Snowsight Object Explorer panel.

### Upload Unstructured Data into an Internal Stage

We have extracted 100 text files from the IMDB Large Movie Review dataset into the Github repo, that was unzipped to your local machine.

The script below assumes the location of the repo is `/tmp/sfguide-horizon-intra-organization-sharing`.
Please modify if you have cloned or unzipped to a different location.

`show organization accounts` in your AWS Provider Account will display `organization_name` and `account_name` that is required in the SnowSQL command.

![Orgname-Accountname](assets/SAMPLE.jpg)

Open a terminal on your workstation and run the following SnowSQL command, after filling in the account identifier. 
You will be prompted for the password for the Snowflake user passed as a parameter.

```bash
snowsql -a <FILL ORGNAME-ACCOUNTNAME> \
-u <user-id> -d frostbyte_tasty_bytes -r sysadmin -s film_reviews \
-D srcpath=/tmp/sfguide-horizon-intra-organization-sharing \
-D stagename=@movie_stage \
-o variable_substitution=true -f /tmp/sfguide-horizon-intra-organization-sharing/data/upload.cnf
```

Setup is now complete!

<!-- ------------------------ -->
## Create, Publish and Install a Data Listing 

### Build and Publish Listing with Provider Studio UI
- Fill in listing descriptive metadata
- Pick and attach data objects to listing
- Publish to targets in same and cross cloud
- Enable change tracking on all shared objects

### Install Listing in Consumer Accounts
- Install as Admin, make available to Public
- Consume incrementally into pipeline

### Use Listing API to modify listing properties

### Monitor Auto Fulfillment status and cost
- Dashboard for cross-cloud auto fulfillment
- Organization and Account views

<!-- ------------------------ -->
## Protect Data with Governance Policies and Monitor Data Quality

### Establish RBAC, Tag-Based Masking, Row-Access / Aggregation / Projection Policies

### Publish Data Quality Metrics for Listing

<!-- ------------------------ -->
## Create, Publish and Install a Native Application Listing


<!-- ------------------------ -->
## Share Unstructured Data within and across cloud regions


<!-- ------------------------ -->
## Share Snowflake-Managed Iceberg Tables


<!-- ------------------------ -->
## Explore Data Assets with Universal Search and Snowflake Copilot


<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files



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
