id: getting-started-with-cortex-aisql
summary: This guide outlines the process for getting started with Cortex AISQL.
categories: featured,getting-started,data-science-&-ml,app-development
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Data-Science-&-Ai, Featured
authors: Dash Desai

# Getting Started with Cortex AISQL
<!-- ------------------------ -->

## Overview

Duration: 4

Cortex AISQL reimagines SQL into an AI query language for multimodal data, bringing powerful AI capabilities directly into Snowflake's SQL engine. It enables users to build scalable AI pipelines across text, images, and audio using familiar SQL commands. 
With native support for multimodal data through a new FILE datatype, Cortex AISQL seamlessly integrates AI operators with traditional SQL primitives like AI_FILTER and AGGREGATE, allowing analysts to process diverse data types more efficiently and cost-effectively while maintaining enterprise-grade security and governance.

### What is Cortex AISQL? 

Cortex AISQL bridges the traditional divide between structured and unstructured data analysis, eliminating the need for separate tools and specialized skills. 

It delivers three key benefits:

* Simplicity through familiar SQL syntax that transforms any analyst into an AI engineer without complex coding
* High-performance processing through deep integration with Snowflake's query engine, offering 30%+ faster query runtime
* Cost efficiency with up to 60% savings compared to traditional AI implementations

By unifying all data types in a single platform with zero setup required, Cortex AISQL democratizes AI-powered analytics across the enterprise.

![Cortex AISQL](assets/cortex_aisql.png)

### Use Cases

Cortex AISQL benefits organizations across industries dealing with diverse data types including:

* Financial services: Automate corporate action processing by filtering news feeds and joining with internal holdings
* Retail and e-commerce: Detect product quality issues by analyzing customer reviews and identifying concerning patterns
* Healthcare: Accelerate medical research by bridging unstructured clinical notes, transcripts and images with structured patient records
* Legal: Streamline contract analysis and compliance monitoring
* Media: Optimize content and target advertising through multimodal data analysis

Business analysts can extract insights without AI expertise, data engineers can build simpler pipelines, and data scientists can create richer feature sets, all using familiar SQL.

### Prerequisites

* Access to a Snowflake account in one of [these regions](https://docs.snowflake.com/user-guide/snowflake-cortex/aisql?lang=de%2F) with ACCOUNTADMIN role. If you do not have access to an account, create a [free Snowflake trial account](https://signup.snowflake.com/?utm_cta=quickstarts_).

*NOTE: Individual functions in the Cortex AISQL suite are Preview Features. Check the status of each function on its SQL reference page before using it in production. Functions not marked as preview features are generally available (GA) and can be used in production.*

### What You Will Learn

You'll learn how to use powerful operators of Cortex AISQL to analyze multimodal data within Snowflake using natural language.

* AI_COMPLETE: Generate AI-powered text completions or descriptions for various inputs including text and images
* AI_TRANSCRIBE: Transcribe audio files
* AI_FILTER: Semantic filtering
* AI_AGG: Aggregate insights across multiple rows
* AI_CLASSIFY: Text and image classification

### What You Will Build

Snowflake Notebook that helps you get started with using Cortex AISQL with multimodal data across test, images, and audio files.

<!-- ------------------------ -->
## Setup

Duration: 10 

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/setup.sql) to execute all statements in order from top to bottom.

**Step 2.** Download sample [images files](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/tree/main/data/images) and use **Snowsight >> Data >> Add Data >> Load files into a Stage** to upload them to `DASH_DB.DASH_SCHEMA.DASH_IMAGE_FILES` stage created in step 1.

**Step 3.** Download sample [audio files](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/tree/main/data/audio) and use **Snowsight >> Data >> Add Data >> Load files into a Stage** to upload them to `DASH_DB.DASH_SCHEMA.DASH_AUDIO_FILES` stage created in step 1.

**Step 4.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [images.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/images.sql) to execute all statements in order from top to bottom to create IMAGES table.

**Step 5.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [audio.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/audio.sql) to execute all statements in order from top to bottom to create VOICEMAILS table.

**Step 6.** Click on [cortex_aisql.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/cortex_aisql.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

**Step 7.** In Snowsight:

* On the left hand navigation menu, click on **Projects** » **Notebooks**
* On the top right, click on **Notebook** down arrow and select **Import .ipynb file** from the dropdown menu
* Select **cortex_aisql.ipynb** file you downloaded in the step above
* In the Create Notebook popup
    * For Notebook location, select `DASH_DB` and `DASH_SCHEMA`
    * For Python environment, select `Run on warehouse`
    * For Query warehouse, select `DASH_WH_S`
    * For Notebook warehouse, select default `SYSTEM$STREAMLIT_NOTEBOOK_WH`
    * Click on **Create** button

**Step 8.** Open Notebook

* Click on **Start** button on top right

> aside positive
> NOTE: At this point, it may take a couple of minutes for the session to start. You will not be able to proceed unless the status changes from **Starting** to **Active**.

<!-- ------------------------ -->
## Run Notebook

Duration: 15

> aside negative
> PREREQUISITE: Successful completion of steps outlined under **Setup**.

Here's the code walkthrough of the [cortex_aisql.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/cortex_aisql.ipynb) notebook that you downloaded and imported into your Snowflake account. *NOTE: Individual functions in the Cortex AISQL suite are Preview Features. Check the status of each function on its SQL reference page before using it in production. Functions not marked as preview features are generally available (GA) and can be used in production.*

Once the status changes from **Starting** to **Active**, run through all the cells from top to bottom.

### Cell **Import_Libraries** 

Import libraries required for running cells in the notebook.

### Cell **Multimodal**

Identify customer issues across text, image, and audio data using [AI_COMPLETE()](https://docs.snowflake.com/en/sql-reference/functions/ai_complete) and [AI_TRANSCRIBE()](https://docs.snowflake.com/en/sql-reference/functions/ai_transcribe) to see how the SQL operators work seamlessly across all modalities.

* Text: Emails 
* Images: Screenshots
* Audio: Voicemails

### Cell **Preview_Data** 

Notice that native FILE datatype allows for consolidating all data formats into one table. 

### Cell AI_FILTER

Semantically "JOIN" customer issues with existing solutions using JOIN ... ON [AI_FILTER()](https://docs.snowflake.com/en/sql-reference/functions/ai_filter).

### Cell AI_AGG

Get aggregated insights across multiple rows using [AI_AGG()](https://docs.snowflake.com/en/sql-reference/functions/ai_agg).

### Cell AI_CLASSIFY

Classification of labels that can be used in downstream applications using [AI_CLASSIFY()](https://docs.snowflake.com/en/sql-reference/functions/ai_classify). For example, to train ML models.

==================================================================================================

### OPTIONAL: Display images in cell results

If you'd like to see images displayed in the Notebook as part of the consolidated data in **Preview_Data** cell, follow these instructions.

**Step 1**. In a SQL worksheet, execute the following statement to create a Snowflake managed internal stage to store the sample python files.

```sql
 create or replace stage DASH_DB.DASH_SCHEMA.DASH_PY_FILES 
    encryption = (TYPE = 'SNOWFLAKE_SSE') 
    directory = ( ENABLE = true );
```

**Step 2.** Use [Snowsight]((https://docs.snowflake.com/en/user-guide/data-load-local-file-system-stage-ui#upload-files-onto-a-named-internal-stage)) to upload [snowbooks_extras.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql/blob/main/snowbooks_extras.py) on stage **DASH_DB.DASH_SCHEMA.DASH_PY_FILES**.

**Step 3.** Reopen existing **cortex_aisql.ipynb** Notebook, and on the top right click on **Packages** >> **State Packages** and enter **@DASH_DB.DASH_SCHEMA.DASH_PY_FILES/snowbooks_extras.py** and then click on **Import**. 

![Add package](assets/add_package.png)

**Step 4.** If the session is **Active**, click on it to end the current session. Otherwise, click on **Start** to start a new session which will also update the packages list and include our custom package **snowbooks_extras**.

> aside positive
> NOTE: At this point, it may take a couple of minutes for the session to start. You will not be able to proceed unless the status changes from **Starting** to **Active**.

**Step 5.** Add `import snowbooks_extras` to the libraries list under **Import_Libraries** and run the cell.

**Step 6.** Now if you run **Preview_Data** cell, you will see images displayed in **INPUT_FILE** column as shown below.

> aside negative 
> Before importing `snowbooks_extras` 

![Data without images](assets/df_without_img.png)

> aside negative 
> After importing `snowbooks_extras` -- you will need to click twice (not exactly a double-click though :)) to see the enlarged image as shown.

![Data with images](assets/df_with_img.png)

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 1

Congratulations! You've successfully created a Snowflake Notebook that helps you get started with using Cortex AISQL with multimodal data.

### What You Learned

You've learned how to use powerful operators of Cortex AISQL to analyze multimodal data within Snowflake using natural language.

* AI_COMPLETE: Generate AI-powered text completions or descriptions for various inputs including text and images
* AI_FILTER: Semantic filtering
* AI_TRANSCRIBE: Transcribe audio files
* AI_AGG: Aggregate insights across multiple rows
* AI_CLASSIFY: Text and image classification

### Related Resources

- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-aisql)
- [Cortex AISQL Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/aisql)
- [Download Reference Architecture](https://quickstarts.snowflake.com/guide/getting-started-with-cortex-aisql/img/f65e99c9c8dbf752.png?_ga=2.50488033.970314110.1758562613-1806211272.1741193538&_gac=1.112796406.1758675992.CjwKCAjwisnGBhAXEiwA0zEOR1sIXOVV_EsVJWwLfve5dvv0oNT7nVRSlx19ZM16B3Kj1k4neCKwLxoCf70QAvD_BwE)
- [Read the Blog](https://www.snowflake.com/en/blog/ai-sql-query-language/)

