author: joshcrittenden
id: end-to-end-analytics-with-snowflake-and-power-bi
summary: Building end-to-end analytical solutions with Snowflake and Power BI
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Engineering, Power BI, Tasty Bytes 

# End-to-End Analytics with Snowflake and Power BI
<!-- ------------------------ -->
## Overview 
Duration: 1

By completing this Quickstart, you will learn how to easily transform raw data into an optimal format for analysis within Power BI. This quickstart will build upon the [An Introduction to Tasty Bytes](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html?index=..%2F..index#0) quickstart. We'll begin by profiling the data within Snowsight, followed by creating new roles and granting appropriate privileges for our fictitious global BI Analyst team. Next, we'll enrich our data with third party location data from the Snowflake Marketplace in a matter of minutes. From there, we'll transform our raw data into an optimal model for downstream analysis within Power BI. Finally, we'll connect the provided Power BI template (.pbit) file to our Snowflake data model and analyze sales transactions live.

![Overview_Diagram](assets/Overview_Diagram1.jpg)

### Prerequisites
- Completion of the [An Introduction to Tasty Bytes quickstart](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html?index=..%2F..index#0) as this will create the dataset used by this quickstart
- Familiarity with SQL
- Familiarity with Power BI

### What You’ll Learn 
- How easily profile data with Snowsight
- How to enrich your organizational data with third party datasets from the Snowflake Marketplace
- How to build simple ELT pipelines with SQL using Dynamic Tables
- How to tag and protect your data with Snowflake Horizon's governance features
- Understanding the fundamentals and benefits of a dimensional model
- Connecting Power BI to Snowflake to perform near-real time analytics

### What You’ll Need 
- [A Snowflake Account](https://signup.snowflake.com/)
- [Power BI Desktop](https://www.microsoft.com/en-us/download/details.aspx?id=58494) 
- Access to a [Power BI Service Workspace](https://app.powerbi.com/) (**optional**)

### What You’ll Build 
- Data engineering pipelines using declarative SQL with Dynamic Tables
- A star schema that is protected with Snowflake Horizon features such as masking policies
- A Power BI DirectQuery semantic model that is designed for performance and near real-time analytics without the hassle of scheduling refreshes

<!-- ------------------------ -->
## Reviewing the Tasty Bytes Dataset
Duration: 5

In this section we'll review the Tasty Bytes dataset and use Snowsight to easily profile the data we'll be working with.

> aside negative
> 
>  NOTE: You must complete the [An Intro to Tasty Bytes](https://quickstarts.snowflake.com/guide/tasty_bytes_introduction/index.html?index=..%2F..index#0) quickstart first, to set up the dataset we'll be working with in this guide.

### Setup
In this section we'll create a new folder to store the upcoming SQL worksheets we'll create and then we'll create our first worksheet

- Start by navigating to the Projects --> Worksheets menu using the left-hand navigation pane.

![Projects_Worksheets](Projects_Worksheets_Menu.jpg)

- Next, create a new folder using the drop down arrow in the upper-right hand corner. This folder will be used to store our SQL worksheets.

![Create_Folder](Create_Folder.jpg)

- Name your folder whatever you would like. We'll name ours End-to-End Analytics with Snowflake and Power BI to match the name of this guide

![Name_Folder](Folder_Name_Menu.jpg)

- Next, we'll create our first worksheet within our folder. Use the upper-right hand navigation to create a new worksheet. We'll name our worksheet "1 - Data Profiling".
- With our worksheet now open, let's set the worksheet context so we can query our Tasty Bytes raw data tables.

```markdown
## set database schema, role, and warehouse context
use role sysadmin;
use database tb_101;
use schema raw_pos;
use warehouse tb_dev_wh;
```

- With our worksheet context set, let's execute a few queries to get a better feel of the dataset we'll be working with



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
## Layering in Third Party Data from the Snowflake Marketplace
Duration: 5

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
## Transforming our Data with Dynamic Tables
Duration: 15

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
## Protecting our Sensitive Data with Snowflake Horizon Governance Features
Duration: 10

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
## Connecting Power BI to Snowflake and Performing a Sales Analysis
Duration: 15

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

Congratuations! You have completed the End-to-End Analytics with Snowflake and Power BI Quickstart!

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- How to easily profile data with Snowsight
- How to enrich your organizational data with third party datasets from the Snowflake Marketplace
- How to build simple ELT pipelines with SQL using Dynamic Tables
- How to tag and protect your data with Snowflake Horizon's governance features
- Why dimensional models are important, specifically when using Power BI
- Connecting Power BI to Snowflake to perform near-real time analytics

### Related Resources and Quickstarts
- <link to github code repo>
- [Understand Star Schema and the Importance for Power BI](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema) (Microsoft Documentation)
- [Getting Started with Snowflake Dynamic Tables](https://quickstarts.snowflake.com/guide/getting_started_with_dynamic_tables/index.html?index=..%2F..index#0) (Snowflake Quickstart)
- [Tasty Bytes - Zero to Snowflake - Collaboration](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_collaboration/index.html?index=..%2F..index#0) (Snowflake Quickstart)
- [Tasty Bytes - Zero to Snowflake - Governance with Snowflake Horizon](https://quickstarts.snowflake.com/guide/tasty_bytes_zero_to_snowflake_governance_with_horizon/index.html?index=..%2F..index#0) (Snowflake Quickstart)
- [Getting Started with Horizon for Data Governance in Snowflake](https://quickstarts.snowflake.com/guide/getting_started_with_horizon_for_data_governance_in_snowflake/index.html?index=..%2F..index#0) (Snowflake Quickstart)
