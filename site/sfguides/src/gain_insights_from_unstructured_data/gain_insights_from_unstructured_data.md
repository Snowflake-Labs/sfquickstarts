author: James Cha-Earley
id: gain_insights_from_unstructured_data
summary: Gain Insights From Unstructed Data with Snowflake Cortex
categories: data-science, gen-ai, data-science-&-ai, cortex
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Data Science, Tasty Bytes, Cortex, Notebook,Generative AI, LLMs

# Gain Insights From Unstructed Data using Snowflake Cortex
<!-- ------------------------ -->
## Overview 
Duration: 2

In this Quickstart guide, you will be help the fictitious food truck company, Tasty Bytes, to identify where their customer experience may be falling short at the truck and business level by leveraging **Snowflake Cortex** within **Snowflake Notebook**. They collect customer reviews to get customer feedback on their food-trucks which come in from multiple sources and span multiple languages. This enables them to better understand the areas which require improvement and drive up customer loyalty along with satisfaction. 

### Prerequisites
* Familiarity with Python
* Familiarity with the DataFrame API
* Familiarity with Snowflake
* Familiarity with Snowpark

### What You’ll Need

You will need the following things before beginning:

* Snowflake account in a cloud region where Snowflake Cortex LLM functions/models are [supported](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions#availability).
  * Cortex functions used - Complete, Translate, Sentiment
  * Model used - mistral-large2
* Snowflake Notebook enabled in your Snowflake account
  * **Note**: To get access to Snowflake Notebook (currently in private preview) reach out to your Snowflake account team. This solution leverages Snowflake Cortex within Snowflake Notebook and you will not be able run the quickstart successfully otherwise.

### What You’ll Learn 

In this quickstart, you will learn:
* How to translate multilingual customer reviews
* How to categorise unstructured review text data at scale
  * How to get rating from reviews
  * How to get intent to recommend from reviews
* How to derive customer sentiment from reviews 
  * How to derive aspect based customer sentiment from reviews
* How to identify issues highlighted in customer reviews
* How to take action assisted by LLM


### What You’ll Build 
* You will analyze Tasty Bytes' customer reviews using **Snowflake Cortex** within **Snowflake notebook** to understand :
  * What our international customers are saying with Cortex **Translate**
  * Get a summary of what customers are saying with Cortex **Summary**
  * Classify reviews to determine if they would recommend a food truck with Cortex **ClassifyText**
  * Gain specific insights with Cortex **ExtractAnswer**
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


  -- scale wh to medium
  ALTER WAREHOUSE tasty_ds_wh SET WAREHOUSE_SIZE = 'Medium';

  -- setup completion note
  SELECT 'Setup is complete' AS note;
  ```

<!-- ------------------------ -->
## Setting up Snowflake Notebook
Duration: 5
### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

* Download the notebook **gaining_insights_from_unstructured_data.ipynb** using this [link](https://github.com/Snowflake-Labs/sfguide-gaining-insights-from-unstructured-data-with-cortex-ai/tree/main/notebook)

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

### Enabled by Cortex Translate

You will leverage **Translate** - one of the **Snowflake Cortex specialised LLM functions** are available in Snowpark ML, to translate the multilingual reviews to english to enable easier analysis. This is done within the notebook using following code snippet in cell `CORTEX_TRANSLATE`.

  ```python
  # Conditionally translate reviews that are not english using Cortex Translate
  reviews_df = reviews_df.withColumn('TRANSLATED_REVIEW',when(F.col('LANGUAGE') != F.lit("en"), \
                                                              cortex.Translate(F.col('REVIEW'), \
                                                                              F.col('LANGUAGE'), \
                                                                              "en")) \
                                    .otherwise(F.col('REVIEW')))

  reviews_df.filter(F.col('LANGUAGE') != F.lit("en")).select(["REVIEW","LANGUAGE","TRANSLATED_REVIEW"]).show(3)
  ```

<!-- ------------------------ -->

## Summarize what the customers are saying
Duration: 5

### Overview

In this section, you will leverage **Snowflake Cortex - Summarize** to quickly understand what the customers are saying:

### We want to get a insight on what people are saying

* In this step, we will get a summarization of customers are saying **Snowflake Cortex - Summarize** 

  ```python
  # Step 1: Add a row number for each review within each TRUCK_BRAND_NAME
  window_spec = Window.partition_by("TRUCK_BRAND_NAME").order_by("REVIEW")
  ranked_reviews_df = reviews_df.with_column(
      "ROW_NUM", F.row_number().over(window_spec)
  )

  # Step 2: Filter to include only the first 20 rows per TRUCK_BRAND_NAME to get a general idea
  filtered_reviews_df = ranked_reviews_df.filter(F.col("ROW_NUM") <= 20)

  # Step 3: Aggregate reviews by TRUCK_BRAND_NAME
  aggregated_reviews_df = filtered_reviews_df.group_by("TRUCK_BRAND_NAME").agg(
      F.array_agg(F.col("REVIEW")).alias("ALL_REVIEWS")
  )

  # Step 4: Convert the array of reviews to a single string
  concatenated_reviews_df = aggregated_reviews_df.with_column(
      "ALL_REVIEWS_TEXT", F.call_function("array_to_string", F.col("ALL_REVIEWS"), F.lit(' '))
  )

  # Step 5: Generate summaries for each truck brand
  summarized_reviews_df = concatenated_reviews_df.with_column(
      "SUMMARY", cortex.Summarize(F.col("ALL_REVIEWS_TEXT"))
  )

  # Step 6: Display the results
  summarized_reviews_df.select(["TRUCK_BRAND_NAME", "SUMMARY"]).show(3)

  one_summary_row = summarized_reviews_df.limit(1).collect()
  if one_summary_row:
      brand = one_summary_row[0]['TRUCK_BRAND_NAME']
      summary = one_summary_row[0]['SUMMARY']

      # Split the summary roughly in half
      half = len(summary) // 2
      split_index = summary[:half].rfind(' ')  # Find the last space before the halfway point
      if split_index == -1:
          split_index = half  # If no space found, split at halfway

      summary_part1 = summary[:split_index].strip()
      summary_part2 = summary[split_index:].strip()

      print(f"Truck Brand: {brand}")
      print(f"Summary (part 1): {summary_part1}")
      print(f"Summary (part 2): {summary_part2}")
  ```
<!-- ------------------------ -->

## Categorise unstructured review text data 
Duration: 5

### Overview
In this section, you will make use of **Snowflake Cortex - ClassifyText** to categorise reviews to understand:
  * How good their overall experience was
  * How likely their customers are to recommend Tasty Bytes food trucks to someone they know 

### Get intention to recommend based on review with Cortex ClassifyText

* You can understand if a customer would recommend the food truck based on their review using **Snowflake Cortex - ClassifyText**. 

  ```python
  # Prompt to understand whether a customer would recommend food truck based on their review 
  text_description = """
  Tell me based on the following food truck customer review, will they recommend the food truck to \
  their friends and family? Answer should be only one of the following words - \
  "Likely" or "Unlikely" or "Unsure".
  """

  reviews_df = reviews_df.withColumn('RECOMMEND', cortex.ClassifyText(F.col('REVIEW'),["Likely","Unlikely","Unsure"], test_description))\
  .withColumn('CLEAN_RECOMMEND', when(F.contains(F.col('RECOMMEND'), F.lit('Likely')), \
                                                              F.lit('Likely')) \
                                        .when(F.contains(F.col('RECOMMEND'), F.lit('Unlikely' )), \
                                                              F.lit('Unlikely')) \
              .when(F.contains(F.col('RECOMMEND'), F.lit('Unsure' )), \
                                                              F.lit('Unsure')))

  reviews_df.select(["REVIEW","CLEAN_RECOMMEND"]).show(3)
  ```
<!-- ------------------------ -->

## Extract Answers from what your customers are saying
Duration: 5

### Overview

In this section, you will leverage **Snowflake Cortex - Extract Answer** to get answers to your questrions:

### Answer specifc quesions you have 

* Using **Snowflake Cortex - Extract Answer** to dive into quesitons you have

  ```python
  # Step 1: Add a row number for each review within each TRUCK_BRAND_NAME
  window_spec = Window.partition_by("TRUCK_BRAND_NAME").order_by("REVIEW")
  ranked_reviews_df = reviews_df.with_column(
      "ROW_NUM", F.row_number().over(window_spec)
  )

  # Step 2: Filter to include only the first 20 rows per TRUCK_BRAND_NAME to get a general idea
  filtered_reviews_df = ranked_reviews_df.filter(F.col("ROW_NUM") <= 20)

  # Step 3: Aggregate reviews by TRUCK_BRAND_NAME
  aggregated_reviews_df = filtered_reviews_df.group_by("TRUCK_BRAND_NAME").agg(
      F.array_agg(F.col("REVIEW")).alias("ALL_REVIEWS")
  )

  # Step 4: Convert the array of reviews to a single string
  concatenated_reviews_df = aggregated_reviews_df.with_column(
      "ALL_REVIEWS_TEXT", F.call_function("array_to_string", F.col("ALL_REVIEWS"), F.lit(' '))
  )

  # Step 5: Generate summaries for each truck brand
  summarized_reviews_df = concatenated_reviews_df.with_column(
      "NUMBER_ONE_DISH", cortex.ExtractAnswer(F.col("ALL_REVIEWS_TEXT"), "What is the number one dish positivly mentioned in the feedback?")
  )

  # Step 6: Extract the first element of the array
  first_element_df = summarized_reviews_df.with_column(
      "FIRST_ELEMENT", F.expr("NUMBER_ONE_DISH[0]")
  )

  # Step 7: Parse the first element as JSON and extract the "answer" field
  readable_df = first_element_df.with_column(
      "NUMBER_ONE_DISH", F.get(F.parse_json(F.col("FIRST_ELEMENT")), F.lit("answer"))
  )

  # Display the simplified results
  readable_df.select(["TRUCK_BRAND_NAME", "NUMBER_ONE_DISH"]).show()
  ```
<!-- ------------------------ -->

## Understand customer sentiment 
Duration: 2

### Enabled by Cortex Sentiment

So far you saw Snowflake Cortex - Translate & Complete. Next, you will look at another **task specific LLM function in Cortex - Sentiment**. This sentiment function is used to understand the customer's tone  based on the review they provided. Sentiment return value between -1 and 1 such that -1 is the most negative while 1 is the most positive. This is done within the notebook using the following code snippet in cell `CORTEX_SENTIMENT`.

```python
# Understand the sentiment of customer review using Cortex Sentiment
reviews_df = reviews_df.withColumn('SENTIMENT', cortex.Sentiment(F.col('REVIEW')))

reviews_df.select(["REVIEW","SENTIMENT"]).show(3)
```

<!-- ------------------------ -->
## Conclusion
Duration: 1

**Congratulations!** You've successfully enabled customer review analytics by leveraging Snowflake Cortex within Snowflake Notebook. And all this without ever needing to move any data outside of secure walls of Snowflake or managing infrastructure.

### What we've covered
With the completion of this quickstart, you have now: 
* Enabled AI for analytics in minutes powered by Snowflake Cortex 
  * Ran inference on industry performant LLMs with Complete which are hosted and served within Snowflake
  * Performed well suited NLP tasks with Translate, Sentiment, Extract Answer and Classifying Text which require zero prompt engineering
* Leveraged Snowflake Notebook which provides SQL, Python, and Markdown cell-based development interface in Snowsight

### Related Resources

Want to learn more about the tools and technologies used in this quickstart? Check out the following resources:

* [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-customer-reviews-analytics-using-snowflake-cortex)
* [Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
