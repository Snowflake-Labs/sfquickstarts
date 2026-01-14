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

The integration showcases Snowflake's [semantic view](https://docs.snowflake.com/en/user-guide/views-semantic/overview)), a new schema-level object in Snowflake which is crucial for Generative AI (GenAI) because it provides the meaning and business context to raw enterprise data, acting as a reliable bridge between human language and complex data structures. You can define business metrics and model business entities and their relationships. You can use semantic views in Cortex Analyst and query these views in a SELECT statement. You can also share semantic views in private listings, in public listings on the Snowflake Marketplace, and in organizational listings. By adding business meaning to physical data, the semantic view enhances data-driven decisions and provides consistent business definitions across enterprise applications.

![Semantic View diagram](assets/semantic-views-diagram.png)


### Prerequisites
- Familiarity with [Snowflake](/en/developers/guides/getting-started-with-snowflake/) and a Snowflake account [signup here](https://signup.snowflake.com/)
- Familiarity with SQL
- Familiarity with Python
- Familiarity with AWS 

### What You’ll Learn 

You will learn about the following Snowflake features during this Quickstart:
- Snowflake([Notebook](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-notebooks/)
- Cortex analyst and [semantic view](https://docs.snowflake.com/en/user-guide/views-semantic/overview))
  

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed


### What You’ll Build 
- A Snowflake Guide in Markdown format


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
