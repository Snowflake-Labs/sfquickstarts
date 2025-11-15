summary: This guide outlines the updates and changes to Snowflake Guides creation process and formatting updates.  
id: get-started-with-guides
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
language: en
environments: web
status: Hidden
author:  Snowflake DevRel Team

# Snowflake Guide Basics

## Components of a Guide

### Overview 

Please use [this markdown file](site/sfguides/src/_markdown-template/) as a template for writing your own Snowflake Guides. This example guide has elements that you will use when writing your own guides, including: code snippet highlighting, downloading files, inserting photos, and more. 

It is important to include on the first page of your guide the following sections: Prerequisites, What you'll learn, What you'll need, and What you'll build. Remember, part of the purpose of a Snowflake Guide is that the reader will have **built** something by the end of the tutorial; this means that actual code needs to be included (not just pseudo-code or concepts).

Previously, we had Quickstarts and Solutions which are now combined into a single page for "Guides" at [www.snowflake.com/en/developers/guides](https://www.snowflake.com/en/developers/guides/) page.  Going forward, we encourage users to think along creating **logged out experiences**  or **topic pages.** A few examples of these pages are:

* **Logged Out experience with one click into product:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)




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
- (OPTIONAL) A Code Editor like [VSCode](https://code.visualstudio.com/download) if you choose to edit locally


### What You’ll Build 
- Once you complete this guide, you should be able to create your "Snowflake Guide" and submit it using the updated process.



### Conclusion & Next Steps

The Conclusion and Next Steps section is one of the most important parts of a guide. This last section helps to sum up all the information the reader has gone through, and in many ways should read like a [TLDR summary](https://www.howtogeek.com/435266/what-does-tldr-mean-and-how-do-you-use-it/#post-435266:~:text=How%20Do%20You%20Use%20TLDR%3F,you%E2%80%99re%20the%20author%20or%20commenter.%20Using). 

There are three main sub-headers in a Conclusion step:

1. a general conclusion paragraph 
2. "What We've Covered" section with a bulleted list of things
3. "Related Resources" with links to various other resources, other guides, docs, videos, GitHub source code, etc.

It's also important to remember that by the time a reader has completed a Guide, the goal is that they have actually built something! Guides teach through hands-on examples -- not just explaining concepts.

### What We've Covered
- Creating steps and setting duration
- Adding code snippets
- Embedding images and videos
- Importing other markdown files

### Related Resources
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides)
- [Learn the GitHub Flow](https://guides.github.com/introduction/flow/)
- [Learn How to Fork a project on GitHub](https://guides.github.com/activities/forking/)



<!-- ------------------------ -->
## Metadata Configuration

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:

```diff
- REQUIRED
```

- **id**: sample-separated-by-hyphens-not-underscores 
  - Make sure to match the id here with the name of the file, all one word.
- **language**: pick from list 
  - Pick the appropriate language from the lsit provided.  
- **categories**: Pick from the list
  - Select from the complete list of content type categories, categories 1, 2 and 3 and/or industries categories provided.  Please DO NOT create new categories.
- **status**: (`Published`, `Archived`, `Hidden`)<br>
  `Published` - implies the guide is active<br>
  `Hidden` - this status will no longer be used.  Preview links are generated during the PR submission process and can be used for internal review.<br>
  `Archived` - implies the sfguide is out of date and deprecated and no longer available.
- **authors**: Author Full Name (+ author GitHub account)
  - Indicate the author(s) of this specific sfguide.  Including the GitHub Account login helps us notify you of any changes requested in the future.

```diff
- OPTIONAL
```
  - **summary**: This is a sample Snowflake Guide 
  - This should be a short, 1 sentence description of your guide. This will be visible on the main landing page. 
  - **environments**: web 
  - `web` is default. If this will be published for a specific event or  conference, include it here.
  - **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
  - **fork repo link**: add a link to your repo
  - **open in snowflake**: add a link to the product as a deeplink or a template link
---

You can see the source metadata for this guide you are reading now, on [the github repo](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/_template/markdown.template).



<!-- ------------------------ -->
## Formatting Considerations

A single sfguide consists of multiple steps. 
These steps are defined in Markdown using Header 2 tag `##`. 
Sub-steps will use a Header 3 tag `###` and so forth.  Please avoid going beyond H4 `####`.

```markdown
## Step 1 Title

All the content for the step goes here.

## Step 2 Title

All the content for the step goes here.

### Subheading for Step 2

  **This text will be bold.**
  __This text will also be bold.__



> NOTE:  Please add images and tables in Markdown format - not HTML.
```


### Markdown Basics 

This section covers the basic markdown formatting options that you will need for your QuickStart. 

Look at the [markdown source for this sfguide](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/_template/markdown.template) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

#### Things to Keep in Mind
Sticking to these guidelines ensures that all Guides have a similar look and feel.  Keeping the document clean helps create a good end-user experience.

- Remember to include the header info in  your markdown 
- Keep the Headings short: 3-4 words
- Have an Overview section <br>(this includes the Prerequisites, What You'll Learn, What You'll Build and What You'll Need subsections)
- Have a Conclusion and Resources section <br>
 (this includes the What We've Covered and Related Resources links)


#### Adding Colors

Basic colors can be  added to callouts using "diff" in a code block in between "```".  

```diff
- text in red
+ text in green
# text in white
``` 

CODE: 
``` 
```diff
- text in red
+ text in green
# text in white ```
``` 




Multiple colors can also be added for emphasis at times:

$${\color{red}Adding \space \color{lightblue}Different \space \color{orange}Colors}$$

CODE: 
```
$${\color{red}Adding \space \color{lightblue}Different \space \color{orange}Colors}$$  


```


#### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

#### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

#### Info Boxes

> [!NOTE]
> This is an informational aside.

> [!TIP]
> A positive or helpful note.

> [!IMPORTANT]
> Something you shouldn’t overlook.

> [!WARNING]
> A cautionary message.

> [!CAUTION]
> A serious negative or danger message.

CODE:
```
> Adding an Info Box:
> Pick the messages above and use this code.  This will appear as an info box.
```



#### Buttons

<button>[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)</button>

CODE:
```
<button>[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)</button>
```

### Tables
| Column 1 | Column 2 | Column 3 |
|-----------|-----------|-----------|
| Row 1     | Data      | More data |
| Row 2     | More      | Still more |



CODE:
```
| Column 1 | Column 2 | Column 3 |
|-----------|-----------|-----------|
| Row 1     | Data      | More data |
| Row 2     | More      | Still more |
```

#### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

CODE:
```
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)
```


#### Images
![Puppy](assets/puppy.jpg)

Please DO NOT use HTML code for adding images. 
Use this markdown format for images: 

CODE:
```
![](my-guide-folder/assets/image-1.jpg "Optional Title of Image")
```

**Images should:**
- Have lower case and hyphens
- Cannot have $ signs or special characters
- Should have the same correct image file name in the .md file (this is case sensitive)
- Upload all images should be in the "assets" folder. 
  Navigage to the folder,  click "Add file"  on top-right and select "Upload files."  Drag-and-drop or "choose your files."
  >Please DO NOT create subfolders inside this folder. 
- Be sized appropriately (no full res images), and optimized for web (recommend tinypng)
- Sizes should be 1 MB max file size, gifs are an exception but they should also be optimized - large images will slow down the page load


#### Videos
Videos from youtube can be linked to the text like a normal link like [this video](https://www.youtube.com/watch?v=KmeiFXrZucE).

CODE:
```
[this video](https://www.youtube.com/watch?v=KmeiFXrZucE)>

```

```diff 
- DO NOT -
use HTML tags in the markdown file since that will cause errors! 
```



<!-- ------------------------ -->
## Language and Category tags

>NOTE:
>**Please pick tags from the 3 categories below.** <br>
```diff
- DO NOT -
create new tags if you don't see them in the list. 
 ``` 


### Language Tags

| Code  | Language         |
|:------|:-----------------|
| en    | English          |
| es    | Spanish          |
| it    | Italian          |
| fr    | French           |
| ja    | Japanese         |
| ko    | Korean           |
| pt_br | Portuguese/Brazil |






## Pick tags from categories  
```diff
- DO NOT -
create new tags if you don't see them in the list. 
 ```
### Content Type:

| Content Type | Taxonomy Path |
|--------------|---------------|
| Community Solution | snowflake-site:taxonomy/solution-center/certification/community-sourced |
| Partner Solution | snowflake-site:taxonomy/solution-center/certification/partner-solution |
| Certified Solution | snowflake-site:taxonomy/solution-center/certification/certified-solution |
| Quickstart | snowflake-site:taxonomy/solution-center/certification/quickstart |



### Category 1: Product Category

| Product | Taxonomy Path |
|:---------|:--------------|
| AI | snowflake-site:taxonomy/product/ai |
| Analytics | snowflake-site:taxonomy/product/analytics |
| Applications & Collaboration | snowflake-site:taxonomy/product/applications-and-collaboration |
| Data Engineering | snowflake-site:taxonomy/product/data-engineering |
| Platform | snowflake-site:taxonomy/product/platform |


### Category 2: Technical Use-Case

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


### Category 3: Prioritized Features

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


### Industries Category

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


<!-- ------------------------ -->
## Converting to Markdown


If you have an existing word document that needs to be converted to markdown format, you can do that using Pandoc.  You will use the **GitHub Flavored Markdown (GFM)**.

To convert a Word document (.docx) to Markdown using Pandoc:

CODE:
```
brew install pandoc
pandoc -f docx -t markdown -o output.md input.docx
```

You can also use the Google Docs feature of saving to Markdown, however please review your markdown before submission as some formatting options can be different.

> NOTE: Once the document is converted, please review the markdown file to ensure it uses the appropriate formatting mentioned in this guide. 






<!-- ------------------------ -->
## Submitting Your Guide

The process to submit your Guide has been simplified. 

- Create a Fork for the main repo and begin writing and formatting your guide.

- Once you are done with the content creation process for your guide, create a Pull Request in GitHub and submit.

- The pull request goes through a validation process to ensure the appropriate formatting and tags are used.  If any errors are detected, you will be notified of them **before** submitting the PR.

- Please correct any errors and try submitting the PR again.  If all looks ok, the PR comes to DevRel team for approval.  
 At this point, a staging URL is generated in GitHub that can be reviewed.

- The DevRel team will approve the PR to publish it to www.snowflake.com/en/developers/guides page.

> NOTE: Any updates or edits after submission must be made in GitHub and a new PR needs to be generated and will go through this same process of approval(s).




<!-- ------------------------ -->
## Conclusion and Resources

Congratulations!  You should now be able to create, format and submit a guide. 

### What We've Covered
- The basic components of a Guide
- Metadata configuration to include 
- Various formatting options available (including headers, subheaders, code, buttons, links, images and videos)
- List of language and category tags for reference.
- How to convert content to markdown 
- The new easier process to submit your guide for approval

### Related Resources
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides)
- [Learn the GitHub Flow](https://guides.github.com/introduction/flow/)
- [Learn How to Fork a project on GitHub](https://guides.github.com/activities/forking/)
- [Markdown template that can be used](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/_template/markdown.template).
- [Submit a Repository Request](https://docs.google.com/forms/d/1AQ0SOMi0-kAHHluEx9HJDDUctwisHqrSVWo-wvfDMwU/edit#responses) to obtain a repo  in Snowflake Labs GitHub.

### EXAMPLES:

You can do one of the following types of Guides.  Each one has a different layout and end user journey.
* **Logged Out experience with one click into Product Template:** [Understanding Customer Reviews using Snowflake Cortex](https://www.snowflake.com/en/developers/guides/understanding-customer-reviews-using-snowflake-cortex/)
* **Topic pages with multiple use cases below the Overview:** [Data Connectivity with Snowflake Openflow](https://www.snowflake.com/en/developers/guides/data-connectivity-with-snowflake-openflow/)
* **Basic Guide with hands-on Instructions:** [Getting Started with Snowflake Intelligence](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-intelligence/)


