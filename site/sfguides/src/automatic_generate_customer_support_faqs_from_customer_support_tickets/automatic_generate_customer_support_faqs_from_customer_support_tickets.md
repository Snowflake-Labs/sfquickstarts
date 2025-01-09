id: autogen-faqs-customer-support
summary: Getting Started with AutoGen FAQs for Customer Support
categories: featured,getting-started,data-science-&-ml
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Snowflake Cortex, Customer Support
author: James Cha-Earley

# Getting Started with AutoGen FAQs for Customer Support
<!-- ------------------------ -->
## Overview 
Duration: 5

In this quickstart, you'll learn how to build an automated FAQ generation system using customer support tickets and Large Language Models (LLMs). The application analyzes support conversations and automatically generates relevant FAQ entries that can be viewed through an interactive Streamlit interface.

### What You'll Learn 
- How to process customer support conversations using Snowflake
- How to generate FAQs automatically using LLMs
- How to create an interactive FAQ viewer with filtering and search capabilities

### What You'll Build
- A system that processes support tickets to extract common issues
- A searchable FAQ interface with filtering capabilities
- An automated FAQ generation pipeline using LLMs

### Prerequisites
- Snowflake account with:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
  - [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

<!-- ------------------------ -->
## Setup Environment
Duration: 10

### Create Database and Tables

First, let's set up our database and required tables:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS CUSTOMER_SUPPORT;
CREATE SCHEMA IF NOT EXISTS CUSTOMER_SUPPORT.FAQS;

-- Create FAQ table
CREATE OR REPLACE TABLE CUSTOMER_SUPPORT_FAQ (
    ISSUE_AREA VARCHAR,
    ISSUE_CATEGORY VARCHAR,
    QUESTION VARCHAR,
    ANSWER VARCHAR,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create tickets table
CREATE OR REPLACE TABLE CUSTOMER_SUPPORT_TICKETS (
    ISSUE_AREA VARCHAR,
    ISSUE_CATEGORY VARCHAR,
    CONVERSATION VARCHAR
);
```

### Setup Python Environment

Initialize the required Python packages and Snowflake session:

```python
# Import python packages
import streamlit as st
import pandas as pd
from snowflake.cortex import Complete

# We can also use Snowpark for our analyses!
from snowflake.snowpark.context import get_active_session
session = get_active_session()
```

<!-- ------------------------ -->
## Process Support Tickets
Duration: 10

Let's examine our customer support tickets:

```sql
Select ISSUE_AREA, ISSUE_CATEGORY, CONVERSATION 
FROM CUSTOMER_SUPPORT_TICKETS 
LIMIT 3;
```

> aside positive
> Before processing large volumes of tickets, examine a sample to ensure data quality and structure.

<!-- ------------------------ -->
## Generate FAQs with LLMs
Duration: 15

Now we'll generate FAQ entries using the Mistral LLM:

```sql
INSERT INTO CUSTOMER_SUPPORT_FAQ (ISSUE_AREA, ISSUE_CATEGORY, QUESTION, ANSWER)
WITH GroupedData AS (
    SELECT 
        ISSUE_AREA, 
        ISSUE_CATEGORY, 
        LISTAGG(CONVERSATION, ' ||| ') AS CONCATENATED_CONVERSATIONS
    FROM CUSTOMER_SUPPORT_TICKETS
    GROUP BY ISSUE_AREA, ISSUE_CATEGORY
),
Prompts AS (
    SELECT 
        ISSUE_AREA, 
        ISSUE_CATEGORY,
        LEFT(
            CONCAT(
                'You are a customer service assistant. Based on the following conversations, generate an FAQ entry in valid JSON format with two keys: "question" and "answer". Conversations: ',
                CONCATENATED_CONVERSATIONS,
                ' Output: {"question": "<your question here>", "answer": "<your answer here>"}'
            ),
            2000
        ) AS PROMPT
    FROM GroupedData
),
RawOutputs AS (
    SELECT 
        ISSUE_AREA, 
        ISSUE_CATEGORY,
        SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', PROMPT) AS RAW_OUTPUT
    FROM Prompts
),
CleanedOutputs AS (
    SELECT 
        ISSUE_AREA, 
        ISSUE_CATEGORY,
        REPLACE(
            REPLACE(
                REPLACE(
                    RAW_OUTPUT,
                    '```', ''
                ),
                'json', ''
            ),
            '\n', ''
        ) AS CLEANED_OUTPUT
    FROM RawOutputs
),
ParsedOutputs AS (
    SELECT 
        ISSUE_AREA,
        ISSUE_CATEGORY,
        TRY_PARSE_JSON(CLEANED_OUTPUT) AS PARSED_JSON
    FROM CleanedOutputs
    WHERE TRY_PARSE_JSON(CLEANED_OUTPUT) IS NOT NULL
)
SELECT 
    ISSUE_AREA, 
    ISSUE_CATEGORY,
    PARSED_JSON:"question"::STRING AS QUESTION,
    PARSED_JSON:"answer"::STRING AS ANSWER
FROM ParsedOutputs;
```

<!-- ------------------------ -->
## Build the FAQ Viewer
Duration: 20

Create an interactive Streamlit interface:

```python
# Query to fetch FAQs
def fetch_faqs():
    query = """
        SELECT 
            ISSUE_AREA, 
            ISSUE_CATEGORY, 
            QUESTION, 
            ANSWER, 
            CREATED_AT
        FROM CUSTOMER_SUPPORT_FAQ
        ORDER BY CREATED_AT DESC;
    """
    return session.sql(query).to_pandas()

# Paginate FAQs
def paginate_data(data, page, page_size=5):
    start = page * page_size
    end = start + page_size
    return data.iloc[start:end]

# Main Streamlit app
def main():
    st.title("Customer Support FAQ Viewer")
    
    # Sidebar for search and filters
    st.sidebar.header("Filters & Search")
    search_query = st.sidebar.text_input("Search FAQs:", "")
    
    # Connect to Snowflake
    faqs = fetch_faqs()
    
    # Filters in the sidebar
    issue_area = st.sidebar.selectbox(
        "Filter by Issue Area:", 
        ["All"] + sorted(faqs["ISSUE_AREA"].unique())
    )
    issue_category = st.sidebar.selectbox(
        "Filter by Issue Category:", 
        ["All"] + sorted(faqs["ISSUE_CATEGORY"].unique())
    )
```

<!-- ------------------------ -->
## Verify and Review
Duration: 10

Check the generated FAQs:

```sql
SELECT * FROM CUSTOMER_SUPPORT_FAQ ORDER BY CREATED_AT DESC;
```

Ensure:
- Questions are relevant and clear
- Answers are accurate and helpful
- Categories are correctly assigned

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 5

Congratulations! You've built an automated FAQ generation system that:
- Processes support conversations
- Generates FAQs using LLMs
- Provides a searchable interface

### What You Learned
- Using Snowflake Cortex LLM functions
- Processing conversational data
- Building Streamlit applications in Snowflake
- Implementing search and filtering

### Related Resources
Documentation:
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

Sample Code & Guides:
- [Snowpark Python Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Streamlit Components](https://docs.streamlit.io/library/api-reference)
- [LLM Best Practices](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-overview)