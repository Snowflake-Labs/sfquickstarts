author: James Cha-Earley
id: gain-insights-from-unstructured-data
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Gain Insights From Unstructured Data with Snowflake Cortex
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Gain Insights From Unstructured Data using Snowflake Cortex
<!-- ------------------------ -->
## Overview 

In this Quickstart guide, you will be help the fictitious food truck company, Tasty Bytes, to identify where their customer experience may be falling short at the truck and business level by leveraging **Snowflake Cortex**. The company gathers customer reviews across multiple sources and languages to assess their food truck operations. This comprehensive feedback helps them identify areas for improvement, ultimately boosting customer satisfaction and loyalty. Leveraging Snowflake Cortex's advanced language AI capabilities, they can automatically process reviews through real-time translation, generate actionable insights through intelligent summarization, and analyze customer sentiment at scale – transforming diverse, unstructured feedback into strategic business decisions that drive their food truck operations forward.

### Prerequisites
* Familiarity with Python
* Familiarity with the DataFrame API
* Familiarity with Snowflake
* Familiarity with Snowpark
* Familiarity with the SQL

### What You’ll Need

You will need the following things before beginning:

* Snowflake account in a cloud region where Snowflake Cortex LLM functions/models are [supported](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions#availability).
  * Cortex functions used - AI_Complete, Translate, Sentiment, AI_Summarize_Agg, AI_Classify, AI_Transcribe
  * Model used - openai-gpt-4.1, claude-3-5-sonnet
* Snowflake Notebook enabled in your Snowflake account

### What You’ll Learn 

In this quickstart, you will learn:
* How to translate multilingual reviews
* How to summarize large amounts of reviews to get specific learnings
* How to categorize unstructured review text data at scale
* How to answer specific questions you have based on the reviews 
* How to derive customer sentiment from reviews 

### What You’ll Build 
* You will analyze Tasty Bytes' customer reviews using **Snowflake Cortex** within **Snowflake Notebook** to understand :
  * What our international customers are saying with Cortex **Translate**
  * Get a summary of what customers are saying with Cortex **AI AGG**
  * Classify reviews to determine if they would recommend a food truck with Cortex **AI Classify**
  * Gain specific insights with Cortex **Complete/AI Complete**
  * Understand how customers are feeling with Cortex **Sentiment**

<!-- ------------------------ -->
## Setup Data

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
* Create Snowflake objects (warehouse, database, schema, raw tables)
* Ingest data from S3 to raw tables
* Create review view 
* Upload Images and Audio

### Creating Objects, Loading Data, and Joining Data
1. Download the [setup.sql](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/setup.sql) file
2. Open it in Workspaces in Snowflake
3. Paste the contents of setup.sql or upload and run the file
4. The script will create:
   - create Snowflake objects (warehouse, database, schema, raw tables), ingest shift  data from S3,  and create the review view
   - A new database and schema for your project
   - Image and audio storage stages

### Upload Images and Audio File to Stage
1. Download [data.zip](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/data.zip) and extract
2. Navigate to Catalog -> Database Explorer
3. Select **TB_VOC** -> **MEDIA** -> **Stages** -> **AUDIO** 
4. Click the **+ Files** on the top right hand corner
5. Click **Browse** and upload the files in the Audio Folder in the data.zip
6. Select **TB_VOC** -> **MEDIA** -> **Stages** -> **IMAGE** 
7. Click the **+ Files** on the top right hand corner
8. Click **Browse** and upload the files in the Image Folder in the data.zip

<!-- ------------------------ -->
## Setup Notebook
### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

* Download the notebook **gaining_insights_from_unstructured_data.ipynb** using this [link](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/gaining_insights_from_unstructured_data.ipynb)

* Navigate to Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on Projects -> Notebook

* Using the import button on the top right, import the downloaded notebook.

* Provide a name for the notebook and select appropriate **database** `tb_voc`, **schema** `analytics`

* For **Runtime** select `Run on container`

* Now you are ready to run the notebook by clicking "Run All" button on the top right or running each cell individually. 

<!-- ------------------------ -->
## Translate

### Overview

You will leverage **Translate** - one of the **Snowflake Cortex specialized LLM functions** are available in Snowpark ML:
  * Translate the multilingual reviews to english to enable easier analysis.

### Hear what your international customers are saying
This is done within the notebook using following code snippet in cell `CORTEX_TRANSLATE`.

#### Python
  ```python
  # Conditionally translate reviews that are not english using Cortex Translate
  reviews_df = reviews_df.withColumn('TRANSLATED_REVIEW',when(F.col('LANGUAGE') != F.lit("en"), \
                                                              cortex.translate(F.col('REVIEW'), \
                                                                              F.col('LANGUAGE'), \
                                                                              "en")) \
                                    .otherwise(F.col('REVIEW')))

  reviews_df.filter(F.col('LANGUAGE') != F.lit("en")).select(["REVIEW","LANGUAGE","TRANSLATED_REVIEW"]).show(3)
  ```
#### SQL
 ```sql
  -- Add the TRANSLATED_REVIEW column with conditional translation
  WITH TRANSLATED_REVIEWS AS (
      SELECT 
          REVIEW,
          LANGUAGE,
          CASE 
              WHEN LANGUAGE != 'en' THEN SNOWFLAKE.CORTEX.TRANSLATE(REVIEW, LANGUAGE, 'en') 
              ELSE REVIEW
          END AS TRANSLATED_REVIEW
      FROM TRUCK_REVIEWS_V
  )

  -- Filter rows where the LANGUAGE is not English and select the desired columns
  SELECT 
      REVIEW, 
      LANGUAGE, 
      TRANSLATED_REVIEW
  FROM TRANSLATED_REVIEWS
  WHERE LANGUAGE != 'en'
  LIMIT 3;
  ```
<!-- ------------------------ -->

## Summarize reviews

### Overview

In this section, you will leverage **Snowflake Cortex LLM - AI_SUMMARIZE_AGG** to quickly understand what the customers are saying:
* Summarization allows us to get key learnings from large amounts of unstructured text, all in a readable form

### We want to get a insight on what people are saying

* In this step, we will get a summarization of customers are saying **Snowflake Cortex LLM - AI_SUMMARIZE_AGG** 

#### Python
  ```python
  summarized_reviews_df = session.table("TRUCK_REVIEWS_V") \
      .group_by("TRUCK_BRAND_NAME") \
      .agg(ai_summarize_agg(F.col("REVIEW")).alias("SUMMARY"))

  summarized_reviews_df.select(["TRUCK_BRAND_NAME", "SUMMARY"]).show(3)
  ```
#### SQL
  ```sql
  WITH SUMMARIZED_REVIEWS AS (
      SELECT 
          TRUCK_BRAND_NAME,
          AI_SUMMARIZE_AGG(REVIEW) AS SUMMARY
      FROM TRUCK_REVIEWS_V
      GROUP BY TRUCK_BRAND_NAME
  )
  SELECT * FROM SUMMARIZED_REVIEWS;
  ```
<!-- ------------------------ -->

## Categorize reviews  

### Overview
In this section, you will make use of **Snowflake Cortex LLM - AI_CLASSIFY** to categories reviews to understand:
  * How likely their customers are to recommend Tasty Bytes food trucks to someone they know 

### Get intention to recommend based on review with Cortex AI_CLASSIFY

* You can understand if a customer would recommend the food truck based on their review using **Snowflake Cortex LLM - AI_CLASSIFY**.  

#### Python
  ```python
  # To understand whether a customer would recommend food truck based on their review 
  reviews_df = reviews_df.withColumn('RECOMMEND', ai_classify(prompt("Tell me based on the following food truck customer review {0}, will they recommend the food truck to their friends and family?", F.col('REVIEW')),["Likely","Unlikely","Unsure"])["labels"][0])

  reviews_df.select(["REVIEW","CLEAN_RECOMMEND"]).show(3)
  ```
#### SQL
  ```sql
  WITH CLASSIFIED_REVIEWS AS (
      SELECT 
          REVIEW,
          AI_CLASSIFY(
              REVIEW, 
              ['Likely', 'Unlikely', 'Unsure'], 
              OBJECT_CONSTRUCT('task_description', 
                  'Tell me based on the following food truck customer review, will they recommend the food truck to their friends and family?'
              )
          ):labels[0]::TEXT AS RECOMMEND
      FROM TRUCK_REVIEWS_V
  )
  SELECT * FROM CLASSIFIED_REVIEWS LIMIT 3;
  ```
<!-- ------------------------ -->

## Leverage an LLM

### Overview

In this section, you will leverage **Snowflake Cortex LLM - AI_COMPLETE** to get answers to your specific questions:

* Answer specific questions you have that lives inside the unstructured data you have

### Answer specific questions you have    

* Using **Snowflake Cortex LLM - AI_COMPLETE** to dive into questions you have  

#### Python
  ```python
    question = "What is the number one dish positively mentioned in the feedback?"

    summarized_reviews_df = session.table("CONCATENATED_REVIEWS").select(
        F.col("TRUCK_BRAND_NAME"),
        ai_complete(
            "openai-gpt-4.1",
            F.concat(
                F.lit("Context: "),
                F.col("ALL_REVIEWS_TEXT"),
                F.lit(f" Question: {question} Answer briefly and concisely and only name the dish:")
            )
        ).alias("NUMBER_ONE_DISH")
    )

    summarized_reviews_df.show(3)
  ```
#### SQL
  ```sql
    -- Gain Learnings from a specific question
    WITH GAIN_LEARNINGS AS (
        SELECT 
            TRUCK_BRAND_NAME,
            AI_COMPLETE(
              'openai-gpt-4.1', 
              'Context:' || ALL_REVIEWS_TEXT || ' Question: What is the number one dish positively mentioned in the feedback? Answer briefly and concisely and only name the dish:'
          ) AS NUMBER_ONE_DISH
        FROM CONCATENATED_REVIEWS
    )
    SELECT TRUCK_BRAND_NAME, NUMBER_ONE_DISH FROM GAIN_LEARNINGS LIMIT 3;
  ```
<!-- ------------------------ -->

## Analyze Images

### Overview

In this section, you will leverage **Snowflake Cortex LLM - AI_COMPLETE** to for analyzing images

```sql
  SELECT
    AI_COMPLETE (
      'claude-3-5-sonnet',
      'Please describe what you see in this image.',
      TO_FILE ('@TB_VOC.MEDIA.IMAGES', IMAGE_PATH)
    ) AS IMAGE_DESCRIPTION
  FROM
    TB_VOC.MEDIA.IMAGE_TABLE
  LIMIT
    1;
```

## Transcription

### Overview

In this section, you will leverage **Snowflake Cortex LLM - AI_TRANSCRIBE** to for transcription

```sql
  SELECT
    AI_TRANSCRIBE (
      TO_FILE ('@TB_VOC.MEDIA.AUDIO', AUDIO_PATH)
    ) AS TRANSCRIPTION_RESULT
  FROM
    TB_VOC.MEDIA.AUDIO_TABLE
  LIMIT
    1;
```

## Understand sentiment 

### Overview

Next, you will look at another **task specific LLM function in Cortex - Sentiment/AI_SENTIMENT**. 
* This sentiment function is used to understand the customer's tone based on the review they provided.

### Understand sentiment with Cortex Sentiment/AI_SENTIMENT
* This is done within the notebook using the following code snippet in cell `CORTEX_SENTIMENT`.
* CORTEX_SENTIMENT return value between -1 and 1 such that -1 is the most negative while 1 is the most positive. 
* AI_SENTIMENT will return a string of the sentiment. [AI_SENTIMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_sentiment#returns)

#### Python
  ```python
  # Understand the sentiment of customer review using Cortex Sentiment
  reviews_df = reviews_df.withColumn('SENTIMENT', cortex.sentiment(F.col('REVIEW')))

  reviews_df.select(["REVIEW","SENTIMENT"]).show(3)
  ```
#### SQL
  ```sql
  SELECT 
      REVIEW, 
      AI_SENTIMENT(REVIEW) AS SENTIMENT
  FROM TRUCK_REVIEWS_V
  LIMIT 3;
  ```

<!-- ------------------------ -->
## Conclusion And Resources

### Overview
You've mastered powerful customer analytics using Snowflake Cortex, processing multilingual reviews and extracting valuable insights – all while maintaining data security within Snowflake's ecosystem. By leveraging these built-in AI capabilities, you've eliminated the complexity of managing external infrastructure while keeping sensitive customer feedback protected within Snowflake's secure environment.

### What You Learned
With the completion of this quickstart, you have now: 
  * Implementing advanced AI capabilities through Snowflake Cortex in minutes
  * Leveraging enterprise-grade language models directly within Snowflake's secure environment
  * Executing sophisticated natural language processing tasks with pre-optimized models that eliminate the need for prompt engineering. 
  * You've mastered a powerful suite of AI-driven text analytics capabilities, from seamlessly breaking through language barriers with Translate, to decoding customer emotions through Sentiment analysis, extracting precise insights with Complete, and automatically categorizing feedback using AI Classify. These sophisticated functions transform raw customer reviews into actionable business intelligence, all within Snowflake's secure environment.

### Resources

Want to learn more about the tools and technologies used in this quickstart? Check out the following resources:

* [Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Intelligent document field extraction and analytics with Document AI](/en/developers/guides/automating-document-processing-workflows-with-document-ai/)
* [Build a RAG-based knowledge assistant with Cortex Search and Streamlit](/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
* [Build conversational analytics app (text-to-SQL) with Cortex Analyst](/en/developers/guides/getting-started-with-cortex-analyst/)
