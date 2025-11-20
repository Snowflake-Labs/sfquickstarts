author: Tim Buchhorn
id: sfguide-getting-started-with-fgac-for-cortex-search
language: en
summary: This guide walks you thorough creating an internal chatbot application that controls access to unstructured documents based on role
categories: snowflake-site:taxonomy/product/ai
environments: web
status: Hidden 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: AI, Conversational Assistants, Cortex Search

# Getting Started with Fine Grained Access Control (FGAC) for RAGs (Cortex Search)
<!-- ------------------------ -->
## Overview 
Duration: 1

Retrieval-Augmented Generation (RAG) promises to unlock unprecedented value from enterprise data. The vast majority (80-90%) of corporate knowledge is trapped in unstructured documents, emails, and messages, often containing sensitive PII, IP, and financial data with inconsistent access controls. Deploying AI models without robust governance exposes this sensitive data, creating severe risks of data breaches, regulatory non-compliance, and loss of intellectual property.

For businesses to adopt AI safely, applications must be "permissions-aware." This is not an optional feature but a foundational requirement. AI systems must respect and enforce the existing security and access permissions of every user at the moment of retrieval. An AI, like any employee, must only be allowed to "see" and surface data that the user querying it is already authorized to access. You can see our documentation on RBAC for Cortex Agents [here](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents#access-control-requirements).

In this guide, you will build a secure RAG pipeline (using Cortex Search) that leverages Snowflake's in-built governance features to enforce document-level access control. Specifically, we will create a RAG that has Fine Grained Access Control (FGAC), where the user will have responses tailored to the documents that they have access to. You will see how Snowflake's features are truly differential, and make developing, securing and distribution AI apps safe and simple. 


### Prerequisites
- Access to an account that can use Snowpark Container Services (non trial accounts).

### What You’ll Learn 
- How to build a RAG chatbot in Streamlit in Snowflake (SiS) with Fine Grained Access Control (FGAC).

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- [VSCode](https://code.visualstudio.com/download) Installed
- [NodeJS](https://nodejs.org/en/download/) Installed
- [GoLang](https://golang.org/doc/install) Installed

### What You’ll Build 
- A RAG chatbot in in Streamlit in Snowflake (SiS) with Fine Grained Access Control (FGAC) powered by Cortex Search.

<!-- ------------------------ -->
## Setup
Duration: 2

# Clone Repository

Open up your terminal or command line and clone the repository here

# Snowflake Setup

Open a SQL Worksheet and run through the following code to set up the neccessary objects and permissions in Snowflake.

```SQL
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS RAG_RLS_OWNER;

GRANT CREATE DATABASE ON ACCOUNT TO ROLE RAG_RLS_OWNER;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE RAG_RLS_OWNER;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE RAG_RLS_OWNER;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;
GRANT ROLE RAG_RLS_OWNER to USER identifier($USERNAME);

---

USE ROLE RAG_RLS_OWNER;

CREATE COMPUTE POOL IF NOT EXISTS RAG_STREAMLIT
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS;

CREATE WAREHOUSE IF NOT EXISTS RAG_WH
  WAREHOUSE_TYPE = STANDARD
  WAREHOUSE_SIZE = XSMALL;

CREATE DATABASE IF NOT EXISTS RAG_RLS_DB;
USE DATABASE RAG_RLS_DB;
CREATE SCHEMA IF NOT EXISTS RAG_RLS_DB.RAG_RLS_SCHEMA;
USE SCHEMA RAG_RLS_SCHEMA;

-- CREATE OR REPLACE STAGE SPECS DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');
CREATE OR REPLACE STAGE SOURCE_DOCUMENTS DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');
```

# Upload Documents

Upload the documents in the Documents folder in the cloned repo to the SOURCE_DOCUMENTS stage we just created. You can do this through the Snowsight UI. Thie instructions on how to do this can be found in our documentation [here](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-stage-ui#upload-files-onto-a-named-internal-stage) or below.

In the navigation menu, select Ingestion » Add Data.

On the Add Data page, select Load files into a Stage.
![Load File Menu](assets/load_file_menu.png)

Then upload the files from Documents folder in the cloned repository from the previous step. Be sure to select the RAG_RLS_DB database, the RAG_RLS_SCHEMA schema and the SOURCE_DOCUMENTS stage.
![Upload Modal](assets/upload_modal.png)


Once you have uploaded them, run the following SQL from your SQL Worksheet to check if the files have been uploaded successfully.

```SQL
LS @SOURCE_DOCUMENTS;
```

# Prepare Data for RAG

In this section, we use Snowflake's helper functions to prepare the unstructured documents and set up the Cortex Search Service. 

The functions below simplify the process of creating a RAG in to only a few steps. Specifically, we are using the following unique Snowflake features:
- AISQL (AI_PARSE_DOCUMENT):
- SPLIT_TEXT_RECURSIVE_CHARACTER:

Note that we are adding an attribute column that we will dynamically filter on.

Run the following SQL in a SQL worksheet

```SQL
USE SCHEMA RAG_RLS_DB.RAG_RLS_SCHEMA;

CREATE OR REPLACE TABLE documents_table AS
  (SELECT TO_FILE('@source_documents', RELATIVE_PATH) AS docs, 
    RELATIVE_PATH as RELATIVE_PATH
    FROM DIRECTORY(@source_documents));

CREATE OR REPLACE TABLE EXTRACTED_TEXT_TABLE AS (
    SELECT  RELATIVE_PATH, 
            AI_PARSE_DOCUMENT(docs, {'mode': 'OCR'}):content::VARCHAR AS EXTRACTED_TEXT,
            CASE
                WHEN RELATIVE_PATH ILIKE '%ski%' THEN 'SKI'
                WHEN RELATIVE_PATH ILIKE '%bike%' OR RELATIVE_PATH ILIKE '%bicycle%' THEN 'BICYCLES'
                ELSE 'Other' -- Default category for files that don't match
            END AS product_department
            FROM documents_table
            );


CREATE OR REPLACE TABLE CHUNKED_TABLE AS (
        SELECT
            e.*,
            c.value::VARCHAR AS chunk
        FROM EXTRACTED_TEXT_TABLE e,
        LATERAL FLATTEN(
            INPUT => snowflake.cortex.split_text_recursive_character(
                EXTRACTED_TEXT,
                'none',
                2000,
                300
            )
        ) c
    );

SELECT * FROM CHUNKED_TABLE;

--- Create Cortex Search Service

CREATE OR REPLACE CORTEX SEARCH SERVICE rag_rls_cortex_search_service
  ON chunk
  ATTRIBUTES product_department
  WAREHOUSE = RAG_WH
  TARGET_LAG = '1 hour'
  INITIALIZE = ON_SCHEDULE
AS SELECT * FROM RAG_RLS_DB.RAG_RLS_SCHEMA.CHUNKED_TABLE;
```


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
