author: Shriya Rai
id: customer-reviews-analytics-using-snowflake-cortex
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/ai
language: en
summary: Analyze customer reviews with Snowflake Cortex AI for sentiment analysis, topic extraction, and feedback insights.
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Customer Reviews Analytics using Snowflake Cortex
<!-- ------------------------ -->
## Overview 

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
  * Models used - snowflake-arctic, mistral-large
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
  * How likely their customers are to recommend Tasty Bytes food trucks to someone they know 
  * How good their overall experience was
  * How is the customer sentiment across customer base
  * What customers are feel saying about different aspects like food, price etc
  * What are the main issues and how to remedy them

<!-- ------------------------ -->
## Setting up the Data in Snowflake

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
  SELECT 'setup is now complete' AS note;
  ```

<!-- ------------------------ -->
## Setting up Snowflake Notebook
### Overview
You will use [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#), the Snowflake web interface, to create Snowflake notebook by importing notebook.

* Download the notebook **customer_review_analytics.ipynb** using this [link](https://github.com/Snowflake-Labs/sfguide-customer-reviews-analytics-using-snowflake-cortex/tree/main/notebook)

* Navigate to Notebooks in [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight.html#) by clicking on Projects -> Notebook

* Using the import button on the top right, import the downloaded notebook.

* Provide a name for the notebook and select appropriate database `tb_voc`, schema `analytics` and warehouse `tasty_ds_wh`

* Open the notebook once created and add the following packages by using the "Packages" button on the top right
  * seaborn
  * matplotlib
  * snowflake-snowpark-python
  * snowflake-ml-python

* Now you are ready to run the notebook by clicking "Run All" button on the top right or running each cell individually. 

<!-- ------------------------ -->
## Translate multilingual reviews

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
## Categorise unstructured review text data 

### Overview
In this section, you will make use of **Snowflake Cortex - Complete** to categorise reviews to understand:
  * How good their overall experience was
  * How likely their customers are to recommend Tasty Bytes food trucks to someone they know 

### Get ratings based on review

* You will utilize **Snowflake Cortex - Complete** function to understand at scale based on a given customer's review what rating that customer is likely to rate their experience at the food truck. The prompt consists of the instruction of the task along with a sample example of the completed task also known as **one-shot learning**. This prompt is then provided to complete function along with the review. This is done within the notebook using the following code snippet in cell `GET_RATINGS`.

  ```python
  # Prompt to get a rating based on a customer review
  # We provide one shot incontext learning to better the answers we get from LLM
  prompt = """[INST]
  ### 
  You are tasked with rating cutsomer reviews for global food truck network called tasty bytes. \
  Rating can be one of the following - awful, poor, okay, good, excellent such that awful is the worst \
  possible rating and excellent is the best possible rating. Include only the rating in the output \
  without any additional text. \
  Rate the following review:
  The "Freezing Point" ice cream truck in Seoul offered a mix of classic and unique \
  options. The Sugar Cone and Waffle Cone were both fresh and crisp, providing a satisfying crunch. The \
  Bottled Water and Ice Tea were standard, as expected. The standout, however, was the Mango Sticky Rice \
  - a delightful blend of sweet and tangy, it was a refreshing twist to the usual ice cream flavors. The \
  service was efficient, but lacked a personal touch. Overall, it\'s a decent choice for a quick, cool \
  treat in the city.
  Rating : good
  Rate the following review: 
  ###"""

  # Ask cortex complete and create a new column
  review_df = reviews_df.withColumn('RATING', cortex.Complete('mistral-large', \
                                                              F.concat(F.lit(prompt), \
                                                                      F.col('REVIEW'), \
                                                                      F.lit("""[/INST]"""))))\
  .withColumn('CLEAN_RATING', when(F.contains(F.lower(F.col('RATING')), F.lit('awful')), \
                                                              F.lit('awful')) \
              .when(F.contains(F.lower(F.col('RATING')), F.lit('poor' )), \
                                                              F.lit('poor')) \
              .when(F.contains(F.lower(F.col('RATING')), F.lit('okay')), \
                                                              F.lit('okay')) \
              .when(F.contains(F.lower(F.col('RATING')), F.lit('good')), \
                                                              F.lit('good')) \
              .when(F.contains(F.lower(F.col('RATING')), F.lit('excellent')), \
                                                              F.lit('excellent')) \
                                    .otherwise(F.lit('unsure')))

  review_df.select(["REVIEW","CLEAN_RATING"]).show(3)
  ```
### Get intention to recommend based on review

* You can understand if a customer would recommend the food truck based on their review using **Snowflake Cortex - Complete**. This time prompt doesn't contain any sample examples for the task within the prompt just the task instruction - **zero shot learning**. This is done within the notebook using the following code snippet in cell `INTENT_TO_RECOMMEND`.

  ```python
  # Prompt to understand whether a customer would recommend food truck based on their review 
  prompt = """[INST]
  ### 
  Tell me based on the following food truck customer review, will they recommend the food truck to \
  their friends and family? Answer should be only one of the following words - \
  "Likely" or "Unlikely" or "Unsure". Make sure there are no additional additional text.
  Review -
  ###"""

  # Ask cortex complete and create a new column
  reviews_df = reviews_df.withColumn('RECOMMEND', cortex.Complete('snowflake-arctic', \
                                                              F.concat(F.lit(prompt), \
                                                                      F.col('REVIEW'), \
                                                                      F.lit("""[/INST]"""))))\
  .withColumn('CLEAN_RECOMMEND', when(F.contains(F.col('RECOMMEND'), F.lit('Likely')), \
                                                              F.lit('Likely')) \
                                        .when(F.contains(F.col('RECOMMEND'), F.lit('Unlikely' )), \
                                                              F.lit('Unlikely')) \
              .when(F.contains(F.col('RECOMMEND'), F.lit('Unsure' )), \
                                                              F.lit('Unsure')) \
                                    .otherwise(F.lit('NA')))

  reviews_df.select(["REVIEW","CLEAN_RECOMMEND"]).show(3)
  ```
<!-- ------------------------ -->
## Understand customer sentiment 

### Enabled by Cortex Sentiment

So far you saw Snowflake Cortex - Translate & Complete. Next, you will look at another **task specific LLM function in Cortex - Sentiment**. This sentiment function is used to understand the customer's tone  based on the review they provided. Sentiment return value between -1 and 1 such that -1 is the most negative while 1 is the most positive. This is done within the notebook using the following code snippet in cell `CORTEX_SENTIMENT`.

```python
# Understand the sentiment of customer review using Cortex Sentiment
reviews_df = reviews_df.withColumn('SENTIMENT', cortex.Sentiment(F.col('REVIEW')))

reviews_df.select(["REVIEW","SENTIMENT"]).show(3)
```

<!-- ------------------------ -->
## Dive deeper with aspect based sentiment

### Enabled by Cortex Complete 

Taking this analysis a step further, you will be looking at aspect based sentiment instead of just the overall sentiment of review and understand what the customers think about different aspects like food quality, service, pricing etc. This done by leveraging **Snowflake cortex - Complete** coupled with a prompt that includes one shot example. This is done within the notebook using the following code snippet in cell `ASPECT_BASED_SENTIMENT`.

  ```python
  # Prompt to understand sentiment for different categories mentioned in the customer review
  # We employ one shot incontext learning to inform LLM
  prompt = """[INST]
  ### 
  You are analyzing food-truck customer reviews to undertsand what a given review says about different relevant categories like \
  food quality, menu options, staff, overall experience, price, ambience, customer support, \
  hygiene standards etc and if sentiment is negative,positive or neutral for that category. \
  Only answer in a single valid JSON containing "category", "sentiment" and "details". \
  Make sure there is no additional text and not mention categories in answer which are not \
  talked in the review. \
  Get category based sentiment for the follwoing customer review:
  "This food truck offers a disappointing experience. \
  The menu lacks healthy options and the food quality is subpar. Finding a parking spot near the \
  truck can also be a frustrating ordeal. Additionally, the value for money is not worth it. To top \
  it all off, the service provided at this food truck is less than pleasant, adding to the overall \
  negative dining experience. Tried reaching out the customer support but was unable to get through." 
  Answer : [{     "category": "food quality",     "sentiment": "negative",    "details": "subpar quality"   }, {     "category": "menu options",     "sentiment": "negative",     "details": "lacks healthy options"   },   {     "category": "staff",     "sentiment": "negative",     "details": "unpleasant"   },   {     "category": "price",     "sentiment": "negative",     "details": "not worth the money"   },   {     "category": "experience",     "sentiment": "negative",     "details": "regrettable dining experience"   },   {     "category": "customer support",     "sentiment": "negative",     "details": "unable to get through"   } ].
  Get category based sentiment for the follwoing customer review:
  ###"""

  # Ask Cortex Complete and create a new column
  review_df = reviews_df.withColumn('CATEGORY_SENTIMENT', cortex.Complete('mistral-large', \
                                                              F.concat(F.lit(prompt), \
                                                                      F.col('REVIEW'), \
                                                                      F.lit("""Answer:[/INST]"""))))
  review_df.select(["REVIEW","CATEGORY_SENTIMENT"]).show(1)
  ```

<!-- ------------------------ -->
## Identify the issues

### Overview

In this section, you will leverage **Snowflake Cortex - Complete** to identify the issues that are mentioned in customer reviews and understand:
  * What is going wrong at business level?
  * What is going wrong at truck level?

### Issues at business level

* In this step, 100 most negative reviews are aggregated and provided to **Snowflake Cortex - Complete** along with a prompt to identify the  main issues found in those reviews. This is done within the notebook using the following code snippet in cell `ALL_MOST_NEG_100`.

  ```python
  # Aggregrate the 100 most negative reviews for tasty bytes
  reviews_agg_ = reviews_df.order_by(F.col('SENTIMENT')).select(F.col('REVIEW')).first(100)

  reviews_agg_str = ''.join(map(str,reviews_agg_))

  # Prompt to summarize the three top issues flagged in the aggregated reviews
  prompt = """[INST]###Summarize the issues mentioned in following aggregated food truck customer reviews with three \
  concise bullet points under 50 words each such that each bullet point also has a heading along with \
  recommendations to remedy those issues.###""" + reviews_agg_str + """[/INST]"""

  # Answer from Cortex Complete
  print(cortex.Complete('mistral-large2', prompt))
  ```
### Issues at truck level 

* Aggregate sentiment at truck level using `Snowpark Dataframe` functions. This is done within the notebook using the following code snippet in cell `SENTIMENT_BY_TRUCK`.

  ```python
  # Get average sentiment of reviews for Trucks 
  truck_agg_reviews_df = reviews_df.groupBy(F.col('TRUCK_ID')) \
                  .agg(F.avg(F.col('SENTIMENT')).alias('AVG_SENTIMENT'),F.count(F.col('REVIEW_ID')).alias('REVIEW_COUNT')) 
  truck_agg_reviews_df.show(3)
  ```
* Average sentiment by truck is utilized to find the truck which is the most negatively reviewed truck and has at least 10 reviews. This is done within the notebook using the following code snippet in cell `MOST_NEGATIVELY_REVIEWED_TRUCK`.

  ```python
  # Get the truck with most negative average sentiment
  truck_agg_reviews_df.filter(F.col('REVIEW_COUNT') >= 10).order_by(F.col('AVG_SENTIMENT')) \
                  .select(F.col('TRUCK_ID')).limit(1).collect()[0][0]
  ```
* Quick analysis of the most negative reviews for Truck 5 to understand the main issues that the customers complain about by leveraging **Snowflake cortex - Complete**. Similar to how it was performed at the business level. This is done within the notebook using the following code snippet in cell `UNDERSTAND_TRUCK_ISSUES_MD`.

  ```python
  # Aggregate the most negative reviews for Truck 5
  reviews_agg_ = reviews_df.filter(F.col('TRUCK_ID') == cells.MOST_NEGATIVELY_REVIEWED_TRUCK)\
                .order_by(F.col('SENTIMENT')).select(F.col('REVIEW')).first(100)

  reviews_agg_str = ''.join(map(str,reviews_agg_))

  # Prompt to understand the main issues with Truck 5
  prompt = """[INST]###Summarize three main issues mentioned in following aggregated customer review with three concise bullet 
  points under 50 words each such that each bullet point also has a heading.###""" + reviews_agg_str + """[/INST]"""

  # Print Cortex Complete's answer
  print(cortex.Complete('mistral-large2', prompt))
  ```

<!-- ------------------------ -->
## Generate email response
### Take action assisted by Cortex Complete

In the final step, you will utilize **Snowflake Cortex - Complete** to draft an email to the owner of the most negatively reviewed truck summarizing the issues that are highlighted in customer reviews along with any recommendation to remedy those issues.This is done within the notebook using following code snippet in cell `GENERATE_EMAIL_RESPONSE`.

  ```python
  # Prompt to get an email draft which reports the main issues with Truck 5 with recommendations to solve
  prompt =""" [INST]### Write me survey report email to the franchise owner summarizing the issues mentioned in following \
  aggregated customer review with three concise bullet points under 50 words each such that each bullet \
  point also has a heading along with recommendations to remedy those issues.###"""+ reviews_agg_str +""" \
  Mention the truck brand name and location in the email.[/INST]"""

  # Print the result from Cortex Complete
  print(cortex.Complete('mistral-large2', prompt))
  ```

<!-- ------------------------ -->
## Conclusion

**Congratulations!** You've successfully enabled customer review analytics by leveraging Snowflake Cortex within Snowflake Notebook. And all this without ever needing to move any data outside of secure walls of Snowflake or managing infrastructure.

### What we've covered
With the completion of this quickstart, you have now: 
* Enabled AI for analytics in minutes powered by Snowflake Cortex 
  * Ran inference on industry performant LLMs with Complete which are hosted and served within Snowflake
  * Performed well suited NLP tasks with Translate, Sentiment which require zero prompt engineering
* Leveraged Snowflake Notebook which provides SQL, Python, and Markdown cell-based development interface in Snowsight
  * Explored data with language of choice and visualized results using popular Python libraries

### Related Resources

Want to learn more about the tools and technologies used in this quickstart? Check out the following resources:

* [Source Code on GitHub](https://github.com/Snowflake-Labs/sfguide-customer-reviews-analytics-using-snowflake-cortex)
* [Cortex LLM](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions)
* [Snowpark Python Developer Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Download Reference Architecture](/content/dam/snowflake-site/developers/2024/08/Customer-Reviews-Analytics-using-Snowflake-Cortex.pdf)
* [Read Medium Blog](https://medium.com/snowflake/transforming-customer-experience-with-snowflake-the-tasty-bytes-story-1b213afc4fc7)
