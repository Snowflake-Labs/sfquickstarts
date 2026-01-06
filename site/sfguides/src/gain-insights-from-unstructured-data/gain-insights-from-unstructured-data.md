author: James Cha-Earley
id: gain-insights-from-unstructured-data
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Analyze documents, images, and audio with Snowflake Cortex AI Functions for unstructured data insights and extraction.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Gain Insights From Unstructured Data using Snowflake Cortex
<!-- ------------------------ -->
## Overview 

The fictitious food truck company, Tasty Bytes, gathers thousands of customer reviews across multiple sources and languages to assess their food truck operations. To improve customer satisfaction and loyalty, the company needs to quickly identify exactly where their customer experience is falling short, at the individual truck and business levels. The challenge is transforming this vast amount of diverse, unstructured data into actionable business insights at scale.

This guide will show you how to use this comprehensive feedback entirely within Snowflake to help them identify areas for improvement. Use [Cortex AI Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql) in Snowflake to run unstructured analytics on text and images with industry-leading LLMs from OpenAI, Anthropic, Meta, Mistral AI, and DeepSeek. They can automatically process reviews through real-time translation, generate actionable insights through intelligent summarization, and analyze customer sentiment at scale – transforming diverse, unstructured feedback into strategic business decisions that drive their food truck operations forward.

### Prerequisites
* Familiarity with Python
* Familiarity with the DataFrame API
* Familiarity with Snowflake
* Familiarity with Snowpark
* Familiarity with the SQL

### What You’ll Need

* A Snowflake account in a cloud region where Cortex LLM Functions and models are [supported](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions#availability). If you do not have a Snowflake account, you can register for a [free trial account](https://signup.snowflake.com/?utm_cta=quickstarts_&_fsi=yYZEVo4S&_fsi=yYZEVo4S).
  * Cortex AI Functions: Translate, AI_SUMMARIZE_AGG, AI_CLASSIFY, AI_COMPLETE, AI_SENTIMENT, AI_COMPLETE, AI_TRANSCRIBE
  * Models: openai-gpt-4.1, claude-3-5-sonnet
* Snowflake Notebook enabled in your Snowflake account.

### What You’ll Learn 

* How to translate multilingual reviews
* How to summarize large amounts of reviews to get specific learnings
* How to categorize unstructured review text data at scale
* How to answer specific questions you have based on the reviews 
* How to derive customer sentiment from reviews 

### What You’ll Build 
* You will analyze Tasty Bytes' customer reviews using **Snowflake Cortex AI** within **Snowflake Notebook** to understand:
  * What our international customers are saying with Cortex **Translate**
  * Get a summary of what customers are saying with Cortex **AI_SUMMARIZE_AGG**
  * Classify reviews to determine if they would recommend a food truck with Cortex **AI_CLASSIFY**
  * Gain specific insights with Cortex **AI_COMPLETE**
  * Understand how customers are feeling with Cortex **AI_SENTIMENT**
  * Insights on Images with Cortex **AI_COMPLETE**
  * Transcribe Audio with Cortex **AI_TRANSCRIBE**

<!-- ------------------------ -->
## Setup Data

This phase focuses on initializing your Snowflake environment. You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
* Create Snowflake objects (warehouse, database, schema, raw tables)
* Ingest data from S3 to raw tables
* Create review view 
* Upload Images and Audio

### Creating Objects, Loading Data, and Joining Data

We will use the setup.sql file to automate the creation of the required infrastructure and load the sample text data.

1. Download the [setup.sql](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/setup.sql) file from the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/tree/main)
2. Open up a <a href="https://app.snowflake.com/_deeplink/#/workspaces?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=gain-insights-from-unstructured-data&utm_cta=developer-guides-deeplink" class="_deeplink">Workspaces</a> in Snowflake
3. Copy and paste the contents of setup.sql or upload and run the file
4. The script will:
   - Create Snowflake objects (warehouse, database, schema, raw tables)
   - Ingest shift data from S3
   - Create the review view
   - Create a new database and schema for your project
   - Create the image and audio storage stages

### Upload Images and Audio File to Stage

Now you will upload the media files into the dedicated stages created by the setup.sql file:

1. Download [data.zip](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/data.zip) and extract its contents
2. Navigate to Catalog » Database Explorer
3. Upload
 * Select your database: **TB_VOC** » **MEDIA** » **Stages** » **AUDIO**
 * Click **+ Files** on the top right hand corner
 * Click **Browse** and upload the files in the Audio Folder within the data.zip file
4. Upload Image Files
 * Select your database: **TB_VOC** » **MEDIA** » **Stages** » **IMAGE**
 * Click **+ Files** on the top right hand corner
 * Click **Browse** and upload the files in the Image Folder within the data.zip file

Your Snowflake environment now contains the complete set of data.

<!-- ------------------------ -->
## Setup Notebook

This phase prepares your execution environment by importing the primary code into a Snowflake Notebook. You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) again to create Snowflake Notebook by importing a notebook.

* Download the notebook **[gaining_insights_from_unstructured_data.ipynb](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/gaining_insights_from_unstructured_data.ipynb)** from the GitHub repository
* Select Projects » Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#)
* Click the + Notebook drop-down and select Import .ipynb file
* Select the gaining_insights_from_unstructured_data.ipynb file
* Provide a name for the notebook and select appropriate **database** `tb_voc` and **schema** `analytics` for Notebook location
* For **Runtime** select `Run on container`
* Now you are ready to run the notebook by clicking the "Run all" button on the top right or running each cell individually

<!-- ------------------------ -->
## Translate reviews

This phase uses the Snowflake Cortex [Translate](https://docs.snowflake.com/en/sql-reference/functions/translate-snowflake-cortex) function to convert all multilingual customer reviews into English for easier analysis. This standardization is critical, as it ensures all subsequent analysis is applied consistently across the entire dataset.

Tasty Bytes gathers reviews from international customers. Before you can analyze the overall customer experience, you need to understand what these international customers are saying. The Translate function allows you to quickly hear the voice of your international customers without requiring external translation services.

### Hear what your international customers are saying

* The code snippet below (executed in the Snowflake Notebook) applies the Translate function only to reviews where the detected language is not English. This is done within the notebook in cell `CORTEX_TRANSLATE`.

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

Upon executing this code, there will be a new column containing all customer feedback in a uniform language. 
<!-- ------------------------ -->

## Summarize reviews

In this phase, you’ll move from individual reviews to aggregated insights. We will use the Snowflake Cortex [AI_SUMMARIZE_AGG](https://docs.snowflake.com/en/sql-reference/functions/ai_summarize_agg) function to quickly distill the key themes from multiple customer reviews into a readable summary.

Summarization allows Tasty Bytes to extract key learnings from large amounts of unstructured text efficiently. Instead of reading every review, users can instantly grasp what customers are saying, all in a readable form. The AI_SUMMARIZE_AGG function automatically handles the complexity of passing large amounts of text data.

### Get insight into what customers are saying

* The code snippet below (executed in the Snowflake Notebook) groups all customer reviews by the TRUCK_BAND_NAME and applies the AI_SUMMARIZE_AGG function on the entire set of reviews for that group. 

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

Upon execution, the resulting output will show a concise summary of the customer experience for each truck brand. 
<!-- ------------------------ -->

## Categorize reviews  

This phase uses the Snowflake Cortex [AI_CLASSIFY](https://docs.snowflake.com/en/sql-reference/functions/ai_classify) function to categorize each individual review based on a specific business question.

This allows Tasty Bytes to quantify how likely their customers are to recommend the food truck to someone they know. By running a classifier through the AI_CLASSIFY function, you transform open-ended text into quantifiable data. This is essential for quickly assessing customer loyalty. 

### Get intention to recommend based on reviews

* The code snippet below (executed in the Snowflake Notebook) uses the AI_CLASSIFY function to classify each review into one of three predefined categories (Likely, Unlikely, or Unsure), based on the review text.  

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

By executing this, you will have a new column indicating the recommendation intent for every customer review.
<!-- ------------------------ -->

## Leverage an LLM

In this phase, we will use the Snowflake Cortex [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete) function to get answers to your specific questions that live within your unstructured data.

Tasty Bytes can use the AI_COMPLETE function to use all the customer reviews as a single knowledge base. You provide the LLM with the text as context and to dive into a specific question that requires synthesis and reasoning. This function is essential for quickly extracting factual answers from unstructured data without manual reading.

### Answer specific questions you have    

* The code snippet below (executed in the Snowflake Notebook) uses the AI_COMPLETE function to return the name of the dish.  

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

By running this, Tasty Bytes gains immediate, actionable intelligence on their most successful menu items.
<!-- ------------------------ -->

## Analyze images

In this phase, we will use the Snowflake Cortex [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete) function again to extract descriptive text from image data.

This is essential for Tasty Bytes to gain insights from photos customers might attach to their reviews. Customers don’t just write feedback, they also share pictures. By using AI_COMPLETE with image input, you can generate a text description of what’s in the photo, making it searchable and analyzable alongside text reviews.

### Describe images    

* The code snippet below (executed in the Snowflake Notebook) uses the AI_COMPLETE function to describe what is seen in a referenced image.  

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

This description can then be used in further analysis steps to ensure images are fully integrated into your customer experience assessment.

## Transcription

In this phase, we will use the Snowflake Cortex [AI_TRANSCRIBE](https://docs.snowflake.com/en/sql-reference/functions/ai_transcribe) function to transform raw audio files into searchable, readable text. 

For Tasty Bytes, audio feedback provides another aspect of customer experience data. By transcribing these files, you convert complex audio into a simple text format that can then be subjected to the same analysis techniques you performed on written reviews.

### Transcribe audio    

* The code snippet below (executed in the Snowflake Notebook) uses the AI_TRANSCRIBE function on a secure reference to your stored audio file.  

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

This transcription process ensures all forms of customer feedback are unified into a single, analyzable dataset for Tasty Bytes.

## Understand sentiment 

This phase uses the Snowflake Cortex [AI_SENTIMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_sentiment) function to quantify the emotional tone of each customer review.

This transforms subjective text into a numerical metric that Tasty Bytes can track over time. Sentiment analysis is crucial for understanding how customers feel.

### Understand views or attitudes

* The code snippet below (executed in the Snowflake Notebook) uses the AI_SENTIMENT function to return a string of the sentiment, which will be a value between -1 (the most negative value) and 1 (the most positive value) in this case. This is done within the notebook using the following code snippet in cell `CORTEX_SENTIMENT`.

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

By executing this, every piece of customer feedback will have been processed and quantified, providing Tasty Bytes with a complete view of their customer experience.
<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've mastered powerful customer analytics using Snowflake Cortex AI Functions, processing multilingual reviews and extracting valuable insights – all while maintaining data security within Snowflake's ecosystem. By leveraging these built-in AI capabilities, you've eliminated the complexity of managing external infrastructure while keeping sensitive customer feedback protected within Snowflake's secure environment.

### What You Learned
With the completion of this quickstart, you have now: 
  * Implemented advanced AI capabilities through Snowflake Cortex in minutes
  * Leveraged enterprise-grade language models directly within Snowflake's secure environment
  * Executed sophisticated natural language processing tasks with pre-optimized models that eliminate the need for prompt engineering. 

You've mastered a powerful suite of AI-driven text analytics capabilities, from seamlessly breaking through language barriers with Translate, to decoding customer emotions through AI_SENTIMENT, extracting precise insights with AI_COMPLETE, and automatically categorizing feedback using AI_CLASSIFY. These sophisticated functions transform raw customer reviews into actionable business intelligence, all within Snowflake's secure environment.

### Resources

Want to learn more about the tools and technologies used in this quickstart? Check out the following resources:

* [Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Intelligent document field extraction and analytics with Document AI](/en/developers/guides/automating-document-processing-workflows-with-document-ai/)
* [Build a RAG-based knowledge assistant with Cortex Search and Streamlit](/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
* [Build conversational analytics app (text-to-SQL) with Cortex Analyst](/en/developers/guides/getting-started-with-cortex-analyst/)
