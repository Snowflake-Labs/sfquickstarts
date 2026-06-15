author: author first and last name
id: markdown-template
language: en
summary: This is a sample Snowflake Template
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: <optional but modify to link to your repo>
open in snowflake: <optional but modify to link into the product>

# Snowflake Guide Template
<!-- ------------------------ -->
## Overview 

Please use [Snowflake Guide](https://www.snowflake.com/en/developers/guides/get-started-with-guides) as a guiding document for writing your own Snowflake Guide. <br>
This example guide has elements that you will use when writing your own guides, including: formatting, code snippet highlighting, video links, inserting photos, and more. 

It is important to include on the first page of your guide the following sections: 
- Prerequisites, 
- What you'll learn
- What you'll need
- What you'll build 

Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code).

The rest of this Snowflake Guide explains the steps of writing your own guide with some basic layout information.  
Detailed formatting options can be found in this [Snowflake Guide](https://www.snowflake.com/en/developers/guides/get-started-with-guides). 

### Prerequisites
- Familiarity with Markdown syntax

### What You’ll Learn 
- The format for a guide (the sections, the metadata and basic markdown)
- How to include code snippets 
- How to hyperlink items
- Ways to include images and videos

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed


### What You’ll Build 
- A Snowflake Guide in Markdown format

<!-- ------------------------ -->
## Metadata Configuration

It is important to set the correct metadata for your Snowflake Guide. This is the first thing that goes on top of your guide. 
The metadata contains all the information required for listing and publishing your guide and includes some required and some optional information.


```diff
- REQUIRED FIELDS
```

- **id**: sample-separated-by-hyphens-not-underscores 
  - make sure to match the id here with the name of the file, all one word.
- **language**: pick from list 
  - pick the appropriate language from the list provided here: https://www.snowflake.com/en/developers/guides/get-started-with-guides/#language-and-category-tags 
- **categories**: Pick from the list
  - select from the complete list of categories provided here: https://www.snowflake.com/en/developers/guides/get-started-with-guides/#language-and-category-tags.  Please DO NOT create new categories.
- **status**: (`Published`, `Archived`, `Hidden`)<br>
  `Published` - implies the guide is active<br>
  `Archived` - implies the sfguide is out of date and deprecated and no longer available.
- **authors**: Author Full Name 
  - Indicate the author(s) of this specific sfguide.  


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
