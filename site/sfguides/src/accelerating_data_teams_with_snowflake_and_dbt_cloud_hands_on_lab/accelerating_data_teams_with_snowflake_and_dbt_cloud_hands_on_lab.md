authors: Bobby Birstock, Amy Chen
id: accelerating_data_teams_with_snowflake_and_dbt_cloud_hands_on_lab
summary: Build a dbt project and data pipeline with dbt Cloud and Snowflake
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, dbt, Data

# Accelerating Data Teams with Snowflake and dbt Cloud Hands On Lab
<!-- ------------------------ -->
## Overview 
Duration: 1

Modern businesses need modern data strategies built on platforms that support agility, growth, and operational efficiency.

[Snowflake](https://signup.snowflake.com/?utm_source=google&utm_medium=paidsearch&utm_content=go-eta-ld-free-trial&utm_term=c-g-snowflake-e&utm_campaign=na-en-Branded&_bt=470247374327&_bk=snowflake&_bm=e&_bn=g&_bg=64805047909&gclid=Cj0KCQjw18WKBhCUARIsAFiW7JwA-C_HmNQzG_OFKhM1Hn9vlW6EAs-9mveiMXychVbbK34lh4vGfHsaAv4NEALw_wcB&gclsrc=aw.ds) is the Data Cloud that enables you to build data-intensive applications without operational burden, so you can focus on data and analytics instead of infrastructure management.

[dbt](https://www.getdbt.com/) is a transformation workflow that lets teams quickly and collaboratively deploy analytics code following software engineering best practices like modularity, portability, CI/CD, and documentation. Now anyone who knows SQL can build production-grade data pipelines. It transforms data in the warehouse leveraging cloud data platforms like Snowflake.

In this Hands On Lab you will follow a step-by-step guide to using dbt with Snowflake, and see some of the benefits this tandem brings.

Let's get started.

### What You'll Use During the Lab

* A trial [Snowflake](https://signup.snowflake.com/) account with ACCOUNTADMIN access

* A [dbt Cloud](https://www.getdbt.com/signup/) account

### What You'll Learn

* How to build scalable data transformation pipelines using dbt & Snowflake

* How to establish data trust with stakeholders by incorporating key dbt testing capabilities

* How to scale Snowflake compute capabilities with the dbt workflow

* How to build lightweight charts and visualizations in Snowflake

### What You'll Build

* A set of data analytics pipelines for retail data leveraging dbt and Snowflake, making use of best practices like data quality tests and code promotion between environments

<!-- ------------------------ -->
## Architecture and Use Case Overview

In this lab we’ll be transforming raw retail data into a consumable orders model that’s ready for visualization. We’ll be utilizing the TPC-H dataset that comes out of the box with your Snowflake account and transform it using some of dbt’s most powerful features. By the time we’re done you’ll have a fully functional dbt project with testing and documentation, dedicated development and production environments, and experience with the dbt git workflow.

![Architecture Overview](assets/architecture_diagram.png)

<!-- ------------------------ -->

## Snowflake Configuration

1. To create a Snowflake trial account, follow [this link](https://signup.snowflake.com/) and fill out the form before clicking `Continue`. You’ll be asked to choose a cloud provider and for the purposes of this workshop any of them will do. After checking the box to agree to the terms, click `Get Started`. 

Once your account is created you’ll receive an email confirmation. Within that email, click the `Click to Activate` button and then create your login credentials. You should now be able to see your account! 

2. For a detailed Snowflake UI walkthrough, please refer [here](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html#getting-started-with-snowsight). From here on out we’ll be using the new Snowflake UI (Snowsight) and any Snowflake specific directions you see will be for Snowsight. Feel free to use the Snowflake Classic UI as it won’t affect your dbt experience, but it may change the location of certain features within Snowflake.

3. The dataset we’ll be using for the workshop comes standard as part of your Snowflake trial. From the `Worksheets` click the blue `Worksheet` button in the upper right hand corner of the page to create a new worksheet. 

![Snowflake Create Worksheet](Snowflake_create_worksheet.png)

4. Once there, click `Databases` and you should see a database called `Snowflake_Sample_Data` in the list of objects.

![Snowflake Sample Data Database](Snowflake_sample_data_database.png)

If you don’t see the database, you may have removed it from your account. To reinstate it, run the following command in your worksheet:

create database snowflake_sample_data from share sfc_samples.sample_data;

You should now see the database as one of your database objects, with associated schemas within it. 

5. Clicking the database name will reveal a schema dropdown, including the schema that we’ll be using for our source data, `TPCH_SF1`. 

![Snowflake TPCH SF1](Snowflake_tpch_sf1.png)

6. Let’s query one of the tables in the dataset to make sure that you’re able to access the data. Copy and paste the following code into your worksheet and run the query.

```
select *

  from snowflake_sample_data.tpch_sf1.orders

 limit 100
```

You should be able to see results, in which case we’re good to go. If you’re receiving an error, check to make sure that your query syntax is correct.

7. Great! Now it’s time to set up dbt Cloud.

<!-- ------------------------ -->





































































<!-- ------------------------ -->

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
Positive
: This will appear in a positive info box.


Negative
: This will appear in a negative info box.

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
