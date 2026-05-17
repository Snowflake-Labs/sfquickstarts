author: Chanin Nantasenemat
id: build-a-customer-review-analytics-dashboard
summary: Process and analyze customer review data using an LLM-powered data processing workflow with Snowflake Cortex.
categories: snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
heroButtonOverrideLabel: View Quickstart
heroButtonOverrideLink: https://www.snowflake.com/en/developers/guides/avalanche-customer-review-data-analytics/#0

# Build a Customer Review Analytics Dashboard
<!-- ------------------------ -->
## Overview

Process and analyze customer review data using an LLM-powered data processing workflow with Snowflake Cortex.

Build a  customer review analytics dashboard that processes unstructured text data and visualizes sentiment trends across products and time periods.

<!-- ------------------------ -->
## Code Example

```sql
SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;

SELECT 
  filename,
  SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
    @avalanche_db.avalanche_schema.customer_reviews,
    filename,
    {'mode': 'layout'}
  ):content AS layout
FROM files;
```

<!-- ------------------------ -->
## Get Started

- [view quickstart](https://quickstarts.snowflake.com/guide/avalanche-customer-review-data-analytics/index.html?index=..%2F..index#0)
- [fork the repo](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Avalanche-Customer-Review-Analytics/Avalanche-Customer-Review-Analytics.ipynb?_fsi=QzKQ5lY6&_fsi=QzKQ5lY6)
- [Read the Medium blog](https://medium.com/snowflake/towards-building-a-customer-review-analytics-dashboard-with-snowflake-and-streamlit-3decdde91567)
