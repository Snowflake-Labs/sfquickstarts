summary: This guide outlines the updates and changes to Snowflake Guides creation process and formatting updates.
id: get-started-with-guides
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
language: en
environments: web
status: Hidden
author:  Snowflake DevRel Team

# Snowflake Guide Basics

## Components of a Guide

The following sections explain the various headings of a guide that are required to keep the look and feel consistent.

Your guide will reside in this [sfguides/src folder](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src)

### Overview 

Please use [this markdown file](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template) as a template for writing your own Snowflake Guides. This example guide has elements that you will use when writing your own guides, including: code snippet highlighting, downloading files, inserting photos, and more. 


### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- Components of a Guide
- Metadata configuration
- Formatting considerations (including headers, subheaders, code, buttons, links, images and videos)
- Tags to include (Language, industries, content type and category)
- Converting content to markdown 
- Submitting your guide for approval

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- (OPTIONAL) A code editor like [VSCode](https://code.visualstudio.com/download) if you choose to edit locally


### What You’ll Build 
Once you complete this guide, you should be able to create your "Snowflake Guide" and submit it using the updated process.


### Layout Basics

At a minimum, the Guide should include the following headings and subheadings. A single sfguide consists of multiple steps. 
These steps are defined in Markdown using Header 2 tag `##`. Sub-steps will use a Header 3 tag `###` and so forth.  Please avoid going beyond H4 `####`.

```
## Overview
It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build.
Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial;
this means that actual code needs to be included (not just pseudo-code or concepts).


### Prerequisites
Include the basic requirements to get started in this subtopic


### What You'll Learn
Include what the end user will learn in this subtopic


### What You'll Build
Include what the end user will build with the Guide in this subtopic


## Hands-on topics
Cover the main components as H2s that appear on the right column menu.


## Conclusion & Resources
This last section helps to sum up all the information the reader has gone through. 


### What you Learned
Re-iterate what the users learned with this Guide


### Resource Links
Add any links that can be helpful to the readers.

```


<!-- ------------------------ -->
## Metadata Configuration

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:

**REQUIRED FIELDS**

- **id**: 
  - the id should be separated by hyphens, not underscores
  - Make sure to match the id here with the name of the file, all one word
- **language**: 
  - Pick the appropriate language from the list provided 
- **categories**: 
  - Select from the complete list of content type categories, categories 1, 2 and 3 and/or industries categories provided.  Please DO NOT create new categories.
- **status**: 
  - `Published` - implies the guide is active<br>
  - `Archived` - implies the sfguide is out of date and deprecated and no longer available<br>
  - Please note the `hidden` status will no longer be supported. If a content piece is not ready for publication, please keep this in draft form until you are ready to make this live. 
  - `Archived` status wil be assessed on a case by case basis and is preferred that it is avoided to prevent redirect issues.  It is recommended to update existing guides.  Redirects will only be applied where absolutely needed.
- **authors**:
  - Provide author full name. Multiple authors can be added
  - Including the GitHub Account login helps us notify you of any changes requested in the future.


**OPTIONAL FIELDS**

  - **summary**: 
    - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
  - **environments**: web 
    - `web` is the default. If this will be published at a specific event or conference, include it here.
  - **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
  - **fork repo link**:
    - add a link to your repo
  - **open in snowflake link**:
    - add a link to the product as a deeplink or a template link


You can see the source metadata at the top of the markdown for this guide [here](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/get-started-with-guides/get-started-with-guides.md?plain=1) for reference.



## Markdown File and Formatting

This section covers the basic markdown formatting options that you will need for your QuickStart. 

Look at the [markdown source for this sfguide](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

> **Ctrl+Click** (Windows/Linux) or **Cmd+Click** (macOS) to open links in a new tab.  This is useful when following along instructions in a guide.

**Things to Keep in Mind**
Sticking to these guidelines ensures that all Guides have a similar look and feel.  Keeping the document clean helps create a good end-user experience.

- Remember to include the header info in  your markdown 
- Keep the H2 (##) Headings short: 3-4 words
- Have an Overview section <br>(this includes the Prerequisites, What You'll Learn, What You'll Build and What You'll Need subsections)
- Have a Conclusion and Resources section <br>
 (this includes the What We've Covered and Related Resources links)
- **Do not** use html in markdown files as this will cause errors


### Adding Tables

Code for adding tables:
```

| Column 1 | Column 2 | Column 3 |
|-----------|-----------|-----------|
| Row 1     | Data      | More data |
| Row 2     | More      | Still more |

```


### Adding Images


Images should:
- Have lower case and hyphens
- Cannot have $ signs or special characters
- Should have the same correct image file name in the .md file (this is case sensitive)
- Upload all images in the "assets" folder. The path to this folder will be used to embed your image within your file.<br> 
  Navigate to the folder,  click "Add file"  on top-right and select "Upload files."  Drag-and-drop or "choose your files."<br>
  **Please DO NOT create subfolders inside this folder** 
- Be sized appropriately (no full res images), and optimized for web (recommend tinypng)
- Sizes should be 1 MB max file size, gifs are an exception but they should also be optimized - large images will slow down the page load
- Please add images and tables in Markdown format, not HTML

Code for adding images:

```
![text of your choice](path within sfguide repo "assets" subfolder where image has been uploaded)

--Sample URL: ![puppy](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/get-started-with-guides/assets/puppy.jpg)
```


### Hyperlinking
Code for hyperlinking:

```
[Link Title](Link URL)
```


### Adding Videos
Code for adding videos:

```
[this video](https://www.youtube.com/watch?v=KmeiFXrZucE)
```

<!-- ------------------------ -->

## Important tags to include

All tags are added into the metadata at the start of your markdown file. For fields beyond language, the taxonomy path is added to the "categories" section. Multiple categories are separated by commas. 


### Language Tags

Language tags are important for the guides to show up in the regional pages.  Please use appropriate tags as they align to your guide content.

>NOTE:
>Please pick the Code from the language category below and include "language: `Code`. **Do not create new tags if you don't see them in the list**<br>

| Code  | Language         |
|:------|:-----------------|
| en    | English          |
| es    | Spanish          |
| it    | Italian          |
| fr    | French           |
| ja    | Japanese         |
| ko    | Korean           |
| pt_br | Portuguese/Brazil |


### Content Type Tagging

Select the taxonomy path from the list below and add to the "category" field at the start of your markdown file to specify the content type that the guide will be displayed as on the site. 
**Do not create new content types if you don't see them in the list**

| Content Type | Taxonomy Path |
|--------------|---------------|
| Community Solution | snowflake-site:taxonomy/solution-center/certification/community-sourced |
| Partner Solution | snowflake-site:taxonomy/solution-center/certification/partner-solution |
| Certified Solution | snowflake-site:taxonomy/solution-center/certification/certified-solution |
| Quickstart | snowflake-site:taxonomy/solution-center/certification/quickstart |



### Category Tagging

>NOTE:
>Please pick applicable categories from the tables below. Not all 3 categories are not required. The taxonomy path is input into the "tags" field and multiple tags are separated by commas. **Do not create new tags if you don't see them in the list**<br>

Add the "Taxonomy Path" in comma separated format for multiple selections in the "categories: " portion of the header. 

#### Category 1: Product Category

| Product | Taxonomy Path |
|:---------|:--------------|
| AI | snowflake-site:taxonomy/product/ai |
| Analytics | snowflake-site:taxonomy/product/analytics |
| Applications & Collaboration | snowflake-site:taxonomy/product/applications-and-collaboration |
| Data Engineering | snowflake-site:taxonomy/product/data-engineering |
| Platform | snowflake-site:taxonomy/product/platform |


#### Category 2: Technical Use-Case

| Use Case | Taxonomy Path |
|:----------|:--------------|
| Ingestion | snowflake-site:taxonomy/snowflake-feature/ingestion |
| Transformation | snowflake-site:taxonomy/snowflake-feature/transformation |
| Interoperable Storage | snowflake-site:taxonomy/snowflake-feature/interoperable-storage |
| Business Intelligence | snowflake-site:taxonomy/snowflake-feature/business-intelligence |
| Lakehouse Analytics | snowflake-site:taxonomy/snowflake-feature/lakehouse-analytics |
| Interactive Analytics | snowflake-site:taxonomy/snowflake-feature/interactive-analytics |
| Applied Analytics | snowflake-site:taxonomy/snowflake-feature/applied-analytics |
| Migrations | snowflake-site:taxonomy/snowflake-feature/migrations |
| Conversational Assistants | snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants |
| Unstructured Data Insights | snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis |
| Model Development | snowflake-site:taxonomy/snowflake-feature/model-development |
| Internal Collaboration | snowflake-site:taxonomy/snowflake-feature/internal-collaboration |
| External Collaboration | snowflake-site:taxonomy/snowflake-feature/external-collaboration |
| Build | snowflake-site:taxonomy/snowflake-feature/build |
| Commercialize | snowflake-site:taxonomy/snowflake-feature/commercialize |
| Compliance, Security, Discovery & Governance | snowflake-site:taxonomy/snowflake-feature/compliance-security-discovery-governance |
| Financial Operations | snowflake-site:taxonomy/snowflake-feature/financial-operations |
| Observability | snowflake-site:taxonomy/snowflake-feature/observability |
| Storage | snowflake-site:taxonomy/snowflake-feature/storage |


#### Category 3: Prioritized Features

| Feature | Taxonomy Path |
|:---------|:--------------|
| Account Replication | snowflake-site:taxonomy/snowflake-feature/account-replication |
| Diagnostics | snowflake-site:taxonomy/snowflake-feature/diagnostics |
| Monitoring | snowflake-site:taxonomy/snowflake-feature/monitoring |
| Geospatial | snowflake-site:taxonomy/snowflake-feature/geospatial |
| Time Series Functions | snowflake-site:taxonomy/snowflake-feature/time-series-functions |
| Cortex Analyst | snowflake-site:taxonomy/snowflake-feature/cortex-analyst |
| Cortex LLM Functions | snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions |
| Cortex Search | snowflake-site:taxonomy/snowflake-feature/cortex-search |
| Document AI | snowflake-site:taxonomy/snowflake-feature/document-ai |
| ML Functions | snowflake-site:taxonomy/snowflake-feature/ml-functions |
| Snowflake ML Functions | snowflake-site:taxonomy/snowflake-feature/snowflake-ml-functions |
| Snowpark Container Services | snowflake-site:taxonomy/snowflake-feature/snowpark-container-services |
| Data Clean Rooms | snowflake-site:taxonomy/snowflake-feature/data-clean-rooms |
| Marketplace and Integrations | snowflake-site:taxonomy/snowflake-feature/marketplace-and-integrations |
| Native Apps | snowflake-site:taxonomy/snowflake-feature/native-apps |
| Unistore | snowflake-site:taxonomy/snowflake-feature/unistore |
| Internal Marketplace | snowflake-site:taxonomy/snowflake-feature/internal-marketplace |
| Prescriptive Selling | snowflake-site:taxonomy/snowflake-feature/prescriptive-selling |
| Salesforce Zero Copy Integration | snowflake-site:taxonomy/snowflake-feature/salesforce-zero-copy-integration |
| Spark Attack | snowflake-site:taxonomy/snowflake-feature/spark-attack |
| Connectors | snowflake-site:taxonomy/snowflake-feature/connectors |
| Dynamic Tables | snowflake-site:taxonomy/snowflake-feature/dynamic-tables |
| Apache Iceberg | snowflake-site:taxonomy/snowflake-feature/apache-iceberg |
| Openflow | snowflake-site:taxonomy/snowflake-feature/openflow |
| Serverless Tasks | snowflake-site:taxonomy/snowflake-feature/serverless-tasks |
| Snowpark | snowflake-site:taxonomy/snowflake-feature/snowpark |
| Snowpipe Streaming | snowflake-site:taxonomy/snowflake-feature/snowpipe-streaming |
| Snowflake Intelligence | snowflake-site:taxonomy/snowflake-feature/snowflake-intelligence |
| Data Lake | snowflake-site:taxonomy/snowflake-feature/data-lake |
| Horizon | snowflake-site:taxonomy/snowflake-feature/horizon |

#### Industries Category

Please select any relevant Industries for your Guide and add in the "categories: " section of the header. 

| Industry | Taxonomy Path |
|-----------|---------------|
| Advertising, Media & Entertainment | snowflake-site:taxonomy/industry/advertising-media-and-entertainment |
| Financial Services | snowflake-site:taxonomy/industry/financial-services |
| Manufacturing & Industrial | snowflake-site:taxonomy/industry/manufacturing |
| Healthcare & Life Sciences | snowflake-site:taxonomy/industry/healthcare-and-life-sciences |
| Public Sector | snowflake-site:taxonomy/industry/public-sector |
| Retail & Consumer Goods | snowflake-site:taxonomy/industry/retail-and-cpg |
| Sports | snowflake-site:taxonomy/industry/sports |
| Telecom | snowflake-site:taxonomy/industry/telecom |
| Transportation | snowflake-site:taxonomy/industry/transportation |
| Travel and Hospitality | snowflake-site:taxonomy/industry/travel-and-hospitality |


<!-- ------------------------ -->

## Converting Existing Files to Markdown


You can use the Google Docs feature of saving to Markdown, however **please review your markdown before submission as some formatting options can be different.** In some instances Google Docs may add additional spacing or characters during conversion that will cause markdown errors. 
 


<!-- ------------------------ -->
## Submitting Your Guide



**The process to submit your Guide has been simplified**

1. Create a Fork for the main repo and begin writing and formatting your guide (top right of webpage, `fork` button). If you have already forked the repository, you can go to your branch and select 'sync fork' to update the repository
   
3. In your fork, select the 'site' folder on the home page -> Then select the 'sfguides/src' folder and navigate to the folder for your guide or create a new guide.
   
4.  Specific steps to "Create" or "Edit" a Guide are covered in the [README file](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/README.md) for easy reference

5. The pull request goes through a validation process to ensure the appropriate formatting and tags are used.  If any errors are detected, you will be notified of them in a comment on GitHub before you are able to submit the PR.

6.  An automated preview link is generated and commented on your PR for you to review and make sure everything looks as expected. 

7. The DevRel team will review and approve the PR. Once approved it will publish to www.snowflake.com/en/developers/guides within an hour. 



**The following automated checks are run and must pass before PRs can be created:**

- Categories are applied from the [approved list](https://www.snowflake.com/en/developers/guides/get-started-with-guides/#important-tags-to-include )

- ID criteria (second line in template): id must exist, id must be separated by dashes, id must be lowercase, id must match the markdown file name (without .md extension), id must match the immediate folder name the file is in

- Language tag must be populated (see [here](https://www.snowflake.com/en/developers/guides/get-started-with-guides/##important-tags-to-include) for the list)

 
<!-- ------------------------ -->
## Additional Resources


### Github Process Documentation 
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides)
- [Learn the GitHub Flow](https://guides.github.com/introduction/flow/)
- [Learn How to Fork a project on GitHub](https://guides.github.com/activities/forking/)
- Video on [How to Fork a Repo](https://youtu.be/ePRJHFXU6n4)
- [Markdown template that can be used](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template).
- Video on [How to Edit a Guide](https://youtu.be/yd9LXsvTSTU)
