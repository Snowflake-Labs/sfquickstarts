author: Snowflake Developer Relations
id: understanding-customer-reviews-using-snowflake-cortex
summary: Understanding customer feedback is critical for businesses, but analyzing large volumes of unstructured text can be challenging.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
open in snowflake: https://app.snowflake.com/templates?template=customer_review_analysis_with_aisql&utm_source=solutioncenter&utm_medium=solutioncenter&utm_campaign=-us-en-all&utm_content=app-customer-review-template

# Understanding Customer Reviews using Snowflake Cortex
<!-- ------------------------ -->
## Overview

Understanding customer feedback is critical for businesses, but analyzing large volumes of unstructured text can be challenging. In this solution, you will use Cortex AISQL to systematically gain insights from unstructured customer feedback.

This solution is one of the [templates inside Snowflake](https://app.snowflake.com/_deeplink/templates?utm_source=solutioncenter&utm_medium=solutioncenter&utm_campaign=-us-en-all&utm_content=app-snowflake-templates), that allows you to leverage multiple AISQL functions to answer different use case questions upon customer reviews.   You can access the template from within Snowflake by clicking the “[Open in Snowflake](https://app.snowflake.com/templates?template=customer_review_analysis_with_aisql&utm_source=solutioncenter&utm_medium=solutioncenter&utm_campaign=-us-en-all&utm_content=app-customer-review-template)” button above, or you can follow the instructions below to execute this code on your own.

Tasty Bytes is a global e-commerce company selling different merchandise. They collect customer reviews to gain insights into how their products are performing.

The following code can be copied into a notebook to execute.  It leverages multiple AISQL functions to answer different use case questions upon customer reviews.

#### Step 1:  Set up your environment and data

Let's begin by running the query below. It sets the proper context for this session. It also creates and populates two tables, PRODUCT\_REVIEWS and PRODUCT\_CATALOG, with sample data for our analysis.

Create a Project > [Notebook](https://app.snowflake.com/_deeplink/#/notebooks?utm_source=solutioncenter&utm_medium=solutioncenter&utm_campaign=-us-en-all&utm_content=app-understanding-customer-reviews-using-snowflake-cortex) and add the following SQL code and add the cell name: IMPORT\_DATA\_SQL

Now add this code to another SQL cell and name it: CHECK\_DATA\_SQL

#### Step 2: Correlate sentiment with ratings

As a first step, let's perform a quick sanity check. We'll use the SNOWFLAKE.CORTEX.SENTIMENT function to score the sentiment of each review. We can then check if it correlates with the user-provided star rating to see if they align.

Add the following code to another SQL cell and name it: SENTIMENT\_CHECK\_SQL

#### Step 3: Find top issues in a category

Now, let's dig deeper. Suppose you want to know what the biggest complaints are for 'Electronics'. You can focus on the ones with negative sentiments, and use AI\_AGG to analyze all relevant reviews and aggregate the common themes into a single summary.

Add the following code to another SQL cell and name it: AGG\_TOP\_ISSUES\_SQL

-- The text may not display fully in the SQL cell. Please hover or double-click on the SQL cell to view the full text.  Print the result to a dataframe for easier reading using the following code in a Python cell, name it: DISPLAY\_TOP\_ISSUES\_PY

#### Step 4:  Identify the most common issues

To answer this question, we start with filtering to Clothing category. Another way to identify comments that mentioned product issue is to leverage our latest [AI\_FILTER](https://docs.snowflake.com/sql-reference/functions/ai_filter) to conduct filtering using natural language.

The next step we use the [AI\_AGG](https://docs.snowflake.com/sql-reference/functions/ai_agg) function to get a list of all product issues mentioned.  
Create a SQL cell to add the following code and name it: COMMON\_ISSUE\_SQL

Now, we'll print the result to a dataframe for easier reading.  Use the following Python code and name the cell:

#### Step 5:  Productionalize the pipeline

With the issues suggested through the [AI\_AGG](https://docs.snowflake.com/sql-reference/functions/ai_agg) function pipeline above, we can now leverage [AI\_CLASSIFY](https://docs.snowflake.com/sql-reference/functions/ai_classify) to turn into continuous data pipeline to keep classify the reviews.

Paste the following code in a SQL cell and name it CLASSIFY\_SQL

#### Step 6:  Generate responses to customer complaints

Finally, let's close the loop. You can use AI\_COMPLETE to help your support team draft empathetic and relevant responses to negative reviews, improving customer satisfaction at scale.

Create another SQL Cell and name it: GENERATE\_SQL.  Add the following code to it:

* End-to-End Workflow: You can chain Cortex AI functions together (SENTIMENT -> AI\_AGG -> AI\_CLASSIFY -> AI\_COMPLETE) to build a powerful analysis pipeline entirely within Snowflake.
* Insight from Unstructured Data: You don't need complex data science tools to extract valuable insights from text. All of this was done with familiar SQL.
* Automate and Scale: By identifying common issues and creating classifiers, you can automate the process of tracking feedback and responding to customers more efficiently.

<!-- ------------------------ -->
## Code Example

```sql
classified_reviews AS (
  SELECT
    review_id,
    review_text,
    AI_CLASSIFY(
      review_text,

      [
        'Sizing issue',
        'Color issue',
        'Fabric quality issue',
        'Washing problem',
        'Pricing issue'
      ]
    ) as classification
  FROM clothing_issue_reviews
)
classified_reviews AS (
  SELECT
    review_id,
    review_text,
    AI_CLASSIFY(
      review_text,

      [
        'Sizing issue',
        'Color issue',
        'Fabric quality issue',
        'Washing problem',
        'Pricing issue'
      ]
    ) as classification
  FROM clothing_issue_reviews
)
classified_reviews AS (
  SELECT
    review_id,
    review_text,
    AI_CLASSIFY(
      review_text,

      [
        'Sizing issue',
        'Color issue',
        'Fabric quality issue',
        'Washing problem',
        'Pricing issue'
      ]
    ) as classification
  FROM clothing_issue_reviews
)
classified_reviews AS (
  SELECT
    review_id,
    review_text,
    AI_CLASSIFY(
      review_text,

      [
        'Sizing issue',
        'Color issue',
        'Fabric quality issue',
        'Washing problem',
        'Pricing issue'
      ]
    ) as classification
  FROM clothing_issue_reviews
)
classified_reviews AS (
  SELECT
    review_id,
    review_text,
    AI_CLASSIFY(
      review_text,

      [
        'Sizing issue',
        'Color issue',
        'Fabric quality issue',
        'Washing problem',
        'Pricing issue'
      ]
    ) as classification
  FROM clothing_issue_reviews
)
```

<!-- ------------------------ -->
## Get Started

- [open in snowflake](https://app.snowflake.com/templates?template=customer_review_analysis_with_aisql&utm_source=solutioncenter&utm_medium=solutioncenter&utm_campaign=-us-en-all&utm_content=app-customer-review-template)
- [Template Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/snowsight-templates)
- [Cortex AI SQL Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql)
