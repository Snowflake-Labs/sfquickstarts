author: James Cha-Earley
id: gain_insights_from_unstructured_data
summary: Gain Insights From Unstructured Data with Snowflake Cortex
categories: data-science, gen-ai, data-science-&-ai, cortex
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Science, Tasty Bytes, Cortex, Notebook,Generative AI, LLMs

# Gain Insights From Unstructured Data using Snowflake Cortex
<!-- ------------------------ -->
## Overview 
Duration: 2

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
  * Cortex functions used - Complete/AI Complete, Translate, Sentiment, AI Aggregation, AI Classify
  * Model used - openai-gpt-4.1
* Snowflake Notebook enabled in your Snowflake account

### What You’ll Learn 

In this quickstart, you will learn:
* How to translate multilingual reviews
* How to summarize large amounts of reviews to get specific learnings
* How to categories unstructured review text data at scale
* How to answer specific questions you have based on the reviews 
* How to derive customer sentiment from reviews 

### What You’ll Build 
* You will analyze Tasty Bytes' customer reviews using **Snowflake Cortex** within **Snowflake notebook** to understand :
  * What our international customers are saying with Cortex **Translate**
  * Get a summary of what customers are saying with Cortex **AI AGG**
  * Classify reviews to determine if they would recommend a food truck with Cortex **AI Classify**
  * Gain specific insights with Cortex **Complete/AI Complete**
  * Understand how customers are feeling with Cortex **Sentiment**

<!-- ------------------------ -->
## Setting up the Data in Snowflake
Duration: 2

### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to:
* Create Snowflake objects (warehouse, database, schema, raw tables)
* Ingest data from S3 to raw tables
* Create review view 

### Creating Objects, Loading Data, and Joining Data
* Navigate to Worksheets, click "+" in the top-right corner to create a new Worksheet, and choose "SQL Worksheet".
* Paste and run the following SQL in the worksheet to create Snowflake objects (warehouse, database, schema, raw tables), ingest shift  data from S3,  and create the review view

  ```sql

    USE ROLE sysadmin;

    /*--
    • database, schema and warehouse creation
    --*/

    -- create tb_voc database
    CREATE OR REPLACE DATABASE tb_voc;

    -- create raw_pos schema
    CREATE OR REPLACE SCHEMA tb_voc.raw_pos;

    -- create raw_customer schema
    CREATE OR REPLACE SCHEMA tb_voc.raw_support;

    -- create harmonized schema
    CREATE OR REPLACE SCHEMA tb_voc.harmonized;

    -- create analytics schema
    CREATE OR REPLACE SCHEMA tb_voc.analytics;

    -- create tasty_ds_wh warehouse
    CREATE OR REPLACE WAREHOUSE tasty_ds_wh
        WAREHOUSE_SIZE = 'large'
        WAREHOUSE_TYPE = 'standard'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE
        INITIALLY_SUSPENDED = TRUE
    COMMENT = 'data science warehouse for tasty bytes';


    USE WAREHOUSE tasty_ds_wh;

    /*--
    • file format and stage creation
    --*/

    CREATE OR REPLACE FILE FORMAT tb_voc.public.csv_ff 
    type = 'csv';

    CREATE OR REPLACE STAGE tb_voc.public.s3load
    COMMENT = 'Quickstarts S3 Stage Connection'
    url = 's3://sfquickstarts/tastybytes-voc/'
    file_format = tb_voc.public.csv_ff;

    /*--
    raw zone table build 
    --*/

    -- menu table build
    CREATE OR REPLACE TABLE tb_voc.raw_pos.menu
    (
        menu_id NUMBER(19,0),
        menu_type_id NUMBER(38,0),
        menu_type VARCHAR(16777216),
        truck_brand_name VARCHAR(16777216),
        menu_item_id NUMBER(38,0),
        menu_item_name VARCHAR(16777216),
        item_category VARCHAR(16777216),
        item_subcategory VARCHAR(16777216),
        cost_of_goods_usd NUMBER(38,4),
        sale_price_usd NUMBER(38,4),
        menu_item_health_metrics_obj VARIANT
    );

    -- truck table build 
    CREATE OR REPLACE TABLE tb_voc.raw_pos.truck
    (
        truck_id NUMBER(38,0),
        menu_type_id NUMBER(38,0),
        primary_city VARCHAR(16777216),
        region VARCHAR(16777216),
        iso_region VARCHAR(16777216),
        country VARCHAR(16777216),
        iso_country_code VARCHAR(16777216),
        franchise_flag NUMBER(38,0),
        year NUMBER(38,0),
        make VARCHAR(16777216),
        model VARCHAR(16777216),
        ev_flag NUMBER(38,0),
        franchise_id NUMBER(38,0),
        truck_opening_date DATE
    );

    -- order_header table build
    CREATE OR REPLACE TABLE tb_voc.raw_pos.order_header
    (
        order_id NUMBER(38,0),
        truck_id NUMBER(38,0),
        location_id FLOAT,
        customer_id NUMBER(38,0),
        discount_id VARCHAR(16777216),
        shift_id NUMBER(38,0),
        shift_start_time TIME(9),
        shift_end_time TIME(9),
        order_channel VARCHAR(16777216),
        order_ts TIMESTAMP_NTZ(9),
        served_ts VARCHAR(16777216),
        order_currency VARCHAR(3),
        order_amount NUMBER(38,4),
        order_tax_amount VARCHAR(16777216),
        order_discount_amount VARCHAR(16777216),
        order_total NUMBER(38,4)
    );

    -- truck_reviews table build
    CREATE OR REPLACE TABLE tb_voc.raw_support.truck_reviews
    (
        order_id NUMBER(38,0),
        language VARCHAR(16777216),
        source VARCHAR(16777216),
        review VARCHAR(16777216),
        review_id NUMBER(18,0)
    );

    /*--
    • harmonized view creation
    --*/

    -- truck_reviews_v view
    CREATE OR REPLACE VIEW tb_voc.harmonized.truck_reviews_v
        AS
    SELECT DISTINCT
        r.review_id,
        r.order_id,
        oh.truck_id,
        r.language,
        source,
        r.review,
        t.primary_city,
        oh.customer_id,
        TO_DATE(oh.order_ts) AS date,
        m.truck_brand_name
    FROM tb_voc.raw_support.truck_reviews r
    JOIN tb_voc.raw_pos.order_header oh
        ON oh.order_id = r.order_id
    JOIN tb_voc.raw_pos.truck t
        ON t.truck_id = oh.truck_id
    JOIN tb_voc.raw_pos.menu m
        ON m.menu_type_id = t.menu_type_id;

    /*--
    • analytics view creation
    --*/

    -- truck_reviews_v view
    CREATE OR REPLACE VIEW tb_voc.analytics.truck_reviews_v
        AS
    SELECT * FROM harmonized.truck_reviews_v;


    /*--
    raw zone table load 
    --*/


    -- menu table load
    COPY INTO tb_voc.raw_pos.menu
    FROM @tb_voc.public.s3load/raw_pos/menu/;

    -- truck table load
    COPY INTO tb_voc.raw_pos.truck
    FROM @tb_voc.public.s3load/raw_pos/truck/;

    -- order_header table load
    COPY INTO tb_voc.raw_pos.order_header
    FROM @tb_voc.public.s3load/raw_pos/order_header/;

    -- truck_reviews table load
    COPY INTO tb_voc.raw_support.truck_reviews
    FROM @tb_voc.public.s3load/raw_support/truck_reviews/;

    CREATE OR REPLACE TABLE CONCATENATED_REVIEWS AS
    WITH RANKED_REVIEWS AS (
        SELECT 
            TRUCK_BRAND_NAME,
            REVIEW,
            ROW_NUMBER() OVER (PARTITION BY TRUCK_BRAND_NAME ORDER BY REVIEW) AS ROW_NUM
        FROM TRUCK_REVIEWS_V
    ),
    FILTERED_REVIEWS AS (
        SELECT *
        FROM RANKED_REVIEWS
        WHERE ROW_NUM <= 20
    ),
    AGGREGATED_REVIEWS AS (
        SELECT 
            TRUCK_BRAND_NAME,
            ARRAY_AGG(REVIEW) AS ALL_REVIEWS
        FROM FILTERED_REVIEWS
        GROUP BY TRUCK_BRAND_NAME
    ),
    CONCATENATED_REVIEWS AS (
        SELECT 
            TRUCK_BRAND_NAME,
            ARRAY_TO_STRING(ALL_REVIEWS, ' ') AS ALL_REVIEWS_TEXT
        FROM AGGREGATED_REVIEWS
    )

    SELECT * FROM CONCATENATED_REVIEWS;

  -- setup completion note
  SELECT 'Setup is complete' AS note;
  ```

<!-- ------------------------ -->
## Setting up Snowflake Notebook
Duration: 5
### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

* Download the notebook **gaining_insights_from_unstructured_data.ipynb** using this [link](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/blob/main/gaining_insights_from_unstructured_data.ipynb)

* Navigate to Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on Projects -> Notebook

* Using the import button on the top right, import the downloaded notebook.

* Provide a name for the notebook and select appropriate database `tb_voc`, schema `analytics` and warehouse `tasty_ds_wh`

* Open the notebook once created and add the following packages by using the "Packages" button on the top right
  * snowflake-snowpark-python
  * snowflake-ml-python

* Now you are ready to run the notebook by clicking "Run All" button on the top right or running each cell individually. 

<!-- ------------------------ -->
## Translate multilingual reviews
Duration: 2

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

## Summarize what the customers are saying
Duration: 5

### Overview

In this section, you will leverage **Snowflake Cortex LLM - Summarize** to quickly understand what the customers are saying:
* Summarization allows us to get key learnings from large amounts of unstructured text, all in a readable form

### We want to get a insight on what people are saying

* In this step, we will get a summarization of customers are saying **Snowflake Cortex LLM - Summarize** 

#### Python
  ```python
  summarized_reviews_df = session.table("TRUCK_REVIEWS_V") \
      .group_by("TRUCK_BRAND_NAME") \
      .agg(ai_agg(F.col("REVIEW"), 'Summarize reviews').alias("SUMMARY"))

  summarized_reviews_df.select(["TRUCK_BRAND_NAME", "SUMMARY"]).show(3)
  ```
#### SQL
  ```sql
  WITH SUMMARIZED_REVIEWS AS (
      SELECT 
          TRUCK_BRAND_NAME,
          AI_AGG(REVIEW, 'Summarize the reviews') AS SUMMARY
      FROM TRUCK_REVIEWS_V
      GROUP BY TRUCK_BRAND_NAME
  )
  SELECT * FROM SUMMARIZED_REVIEWS;
  ```
<!-- ------------------------ -->

## Categorize unstructured review text data  
Duration: 5

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

## Leverage an LLM to find your answer
Duration: 5

### Overview

In this section, you will leverage **Snowflake Cortex LLM - Complete/AI_Complete** to get answers to your specific questions:

* Answer specific questions you have that lives inside the unstructured data you have

### Answer specific questions you have    

* Using **Snowflake Cortex LLM - Complete/AI_Complete** to dive into questions you have  

#### Python
  ```python
    question = "What is the number one dish positively mentioned in the feedback?"

    summarized_reviews_df = session.table("CONCATENATED_REVIEWS").select(
        F.col("TRUCK_BRAND_NAME"),
        cortex.complete(
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

## Understand customer sentiment 
Duration: 2

### Overview

Next, you will look at another **task specific LLM function in Cortex - Sentiment**. 
* This sentiment function is used to understand the customer's tone based on the review they provided.

### Understand sentiment with Cortex Sentiment
* This is done within the notebook using the following code snippet in cell `CORTEX_SENTIMENT`.
* Sentiment return value between -1 and 1 such that -1 is the most negative while 1 is the most positive.  

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
      SNOWFLAKE.CORTEX.SENTIMENT(REVIEW) AS SENTIMENT
  FROM TRUCK_REVIEWS_V
  LIMIT 3;
  ```

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

**Congratulations!** You've mastered powerful customer analytics using Snowflake Cortex, processing multilingual reviews and extracting valuable insights – all while maintaining data security within Snowflake's ecosystem. By leveraging these built-in AI capabilities, you've eliminated the complexity of managing external infrastructure while keeping sensitive customer feedback protected within Snowflake's secure environment.

### What we've covered
With the completion of this quickstart, you have now: 
* Implementing advanced AI capabilities through Snowflake Cortex in minutes
  * Leveraging enterprise-grade language models directly within Snowflake's secure environment
  * Executing sophisticated natural language processing tasks with pre-optimized models that eliminate the need for prompt engineering. 
  * You've mastered a powerful suite of AI-driven text analytics capabilities, from seamlessly breaking through language barriers with Translate, to decoding customer emotions through Sentiment analysis, extracting precise insights with Complete, and automatically categorizing feedback using AI Classify. These sophisticated functions transform raw customer reviews into actionable business intelligence, all within Snowflake's secure environment.

### Related Resources

Want to learn more about the tools and technologies used in this quickstart? Check out the following resources:

* [Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Intelligent document field extraction and analytics with Document AI](https://quickstarts.snowflake.com/guide/automating_document_processing_workflows_with_document_ai/index.html?index=..%2F..index#0)
* [Build a RAG-based knowledge assistant with Cortex Search and Streamlit](https://quickstarts.snowflake.com/guide/ask_questions_to_your_own_documents_with_snowflake_cortex_search/index.html?index=..%2F..index#0)
* [Build conversational analytics app (text-to-SQL) with Cortex Analyst](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_analyst/index.html?index=..%2F..index#0)