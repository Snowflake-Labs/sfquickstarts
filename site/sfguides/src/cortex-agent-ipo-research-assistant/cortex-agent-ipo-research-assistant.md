author: Jonathan Tao
id: markdown-template
language: en
summary: This is a guide to setup a IPO Research Assistant Cortex Agent.  Tools include AI_EXTRACT over SEC S1 Filings, A Semantic View on company information, Cortex Search over market trend PDFs, and Finnhub API for real-time stock information.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Draft
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# IPO Research Assistant with Cortex AI 
<!-- ------------------------ -->
## Overview 

This Quickstart guide will walk you through creating IPO research agent leveraging key Snowflake Cortex capabilities.  In this Quickstart, you will perform/create the following:

- Setup your account to access various APIs, including the [SEC's Edgar Database](https://www.sec.gov/search-filings) and Finnhub(https://finnhub.io/).
- Download one quarter's worth of SEC S-1 filings into stage
- Create a table referencing these filings and supply additional dimensional information, facilitated by a separate EDGAR API endpoint, and create a [Semantic View](https://docs.snowflake.com/en/user-guide/views-semantic/overview) related to this data
- Create a procedure leveraging the [AI_EXTRACT](https://docs.snowflake.com/en/sql-reference/functions/ai_extract) function
- Create procedures able to reference Finnhub's real-time stock market data
- Download market forecast reports from leading firms, in PDFs, and setup document processing and [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) on them
- Create a [Cortex Agent](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) with the ability to reason and leverage the various Cortex AI services leveraged above

### What You’ll Need 
- A [Snowflake Account](https://signup.snowflake.com) with ACCOUNTADMIN privileges

### What You’ll Build 
- A Cortex Agent with multiple tools at its disposal, leveraging the interactive UI of Snowflake Intelligence.  

<!-- ------------------------ -->
## Getting Started 

### Environment Setup
Open up a new SQL worksheet and run the following commands. To open up a new SQL worksheet, select Projects » Worksheets, then click the blue plus button and select SQL worksheet.

```
USE ROLE SYSADMIN;
CREATE OR REPLACE DATABASE IPO_RESEARCH_DB;
USE DATABASE IPO_RESEARCH_DB;

CREATE OR REPLACE WAREHOUSE IPO_RESEARCH_WH 
WAREHOUSE_SIZE = SMALL AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
GRANT USAGE ON WAREHOUSE IPO_RESEARCH_WH TO ROLE SYSADMIN;
USE WAREHOUSE IPO_RESEARCH_WH;
```

Next, let's import the Python Notebook that will download S-1 files from the EDGAR database as well as create the tables and AI_EXTRACT function.  You can import the notebook file by clicking the plus button >> Notebook >> Import .ipynb file.  

image_here

Ensure the following are set:
- Runtime: Run on Container - this is needed as we will be using custom .whl files from the SEC for our project
- Query Warehouse: IPO_RESEARCH_WH.  If you do not see it as an option, refresh your whole webpage as the left-hand navigation bar can be a bit static.

image_here



```diff
- OPTIONAL
```
  - **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
  - **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
  - **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
  - **fork repo link**: add your repo link here for GitHub
  - **open in snowflake**: add deeplinks straight into the product or to a template within Snowflake.



<!-- ------------------------ -->
## Creating Sections

A single sfguide consists of multiple steps or sections. 
These sections are defined in Markdown using Header tags.  Header 2 tag is `##`, Header 3 tag is `###` and so forth. 

```markdown
## Step 1 Title as H2 tag

All the content for the step goes here.

## Step 2 Title as H2 tag

### Subheader goes here as H3 tag.


```
>Please avoid going beyond H4 #### as it will not render on the page correctly!

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

### EXAMPLES:
* **Logged Out experience with one click into product:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)
* **Simple Hands-on Guide**: [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)
