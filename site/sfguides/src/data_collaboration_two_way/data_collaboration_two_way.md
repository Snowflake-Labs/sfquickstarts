author: Tim Buchhorn
id: data_collaboration_two_way
summary: This is a Snowflake Guide on how to use Snowflake's Data Collaboration features to share an enrich data. 
<!--- Categories below should be hyphenated, i.e., Getting-Started. Do not leave blank. Visit site for available categories. -->
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Two Way Data Collaboration
<!-- ------------------------ -->
## Overview 
Duration: 1

This guide will take you through Snowflake's Collaboration features, and highlight how easy it is to share data between two organisations.

It also highlights Snowflakes ability to host a ML Model, score data from shared data, and share the enriched (scored) data back to the original Provider. Hence, it is a 2-way sharing relationship, where both accounts are Providers and Consumers.

### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- How to become a Provider in Snowflake Marketplace (Private Listings)
- How to Consume a shared private asset in the Snowflake Marketplace
- How to Deploy a ML Model in Snowflake
- How to share seamlessly between two Snowflake Accounts 

### What You’ll Need 
- Two [Snowflake](https://signup.snowflake.com/) Accounts in the same cloud and region 

### What You’ll Build 
- Ingestion of Credit Card Customer Profile Data
- Sharing raw data seamlessly via a private listing
- Consuming shared data via a private listing
- Enriching shared data using a ML model
- Sharing back enriched data to the original Provider account

<!-- ------------------------ -->
## Business Use Case
Duration: 2

In this hands-on-lab, we are playing the role of a bank. The Credit Risk team has noticed a rise in credit card default rates which affect the bottom line of the business. It has employed the help of an external organisation to score the credit card default risk of their existing customers, based on a series of attributes in categories such as spending, balance, delinquency, payment and risk. The data needs to be shared between the two parties.

Both companies have chosen to use Snowflake. The advantages of doing this are:
- Low latency between the Provider and Consumer accounts
- The files stay within the security perimeter of Snowflake, with Role Based Access Control (RBAC)

Below is a schematic of the data share
![Diagram](assets/two_way_data_collaboration.png)

### Dataset Details

The dataset contains aggregated profile features for each customer at each statement date. Features are anonymized and normalized, and fall into the following general categories:

D_* = Delinquency variables
S_* = Spend variables
P_* = Payment variables
B_* = Balance variables
R_* = Risk variables

### Dataset Citation

Addison Howard, AritraAmex, Di Xu, Hossein Vashani, inversion, Negin, Sohier Dane. (2022). American Express - Default Prediction. Kaggle. https://kaggle.com/competitions/amex-default-prediction

<!-- ------------------------ -->
## Set up
Duration: 1

Navigate to the [Snowflake Trial Landing Page](https://signup.snowflake.com/). Follow the prompts to create a Snowflake Account.

Repeat the process above. Be sure to select the same cloud and region as the first account your created. Although it is possible to share accross clouds and regions, this guide will not cover this scenario.

Check your emails and follow the prompts to activate both the accounts. One will be the Provider and one will be the Consumer.

<!-- ------------------------ -->
## Provider Account - Set Up
Duration: 10

In this part of the lab we'll set up our Provider Snowflake account, create database structures to house our data, create a Virtual Warehouse to use for data loading and finally load our credit card approval data into our AMEX_DATA table and run a few queries to get familiar with the data.

### Initial Set Up

For this part of the lab we will want to ensure we run all steps as the ACCOUNTADMIN role

```SQL
  -- Change role to accountadmin
  use role accountadmin;
```

First we can create a [Virtual Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview) that can be used for data exploration and general querying in this lab. We'll create this warehouse with a size of Medium which is right sized for that use case in this lab.

```SQL
  -- Create a virtual warehouse for data exploration
  create or replace warehouse query_wh with 
    warehouse_size = 'medium' 
    warehouse_type = 'standard' 
    auto_suspend = 300 
    auto_resume = true 
    min_cluster_count = 1 
    max_cluster_count = 1 
    scaling_policy = 'standard';
```

### Load Data 

Next we will create a database and schema that will house the tables that store our data to be shared.

```SQL
  -- Create the application database and schema
  create or replace database amex_data;
  create or replace schema amex_data;
```

This DDL will create the structure for the table which is the main source of data for our lab.

```SQL
  create or replace table amex_transaction_data_sf (
    customer_ID varchar,
    B_3 float,
    D_66 float,
    S_12 float,
    D_120 float
  );
```

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
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files