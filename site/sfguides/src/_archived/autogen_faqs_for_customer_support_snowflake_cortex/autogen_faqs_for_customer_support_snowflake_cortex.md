id: autogen-faqs-for-customer-support-snowflake-cortex
summary: AutoGen FAQs for Customer Support with Snowflake Cortex
categories: featured,getting-started,data-science-&-ml
environments: web
status: Archived 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Snowflake Cortex, Customer Support
author: James Cha-Earley

# AutoGen FAQs for Customer Support with Snowflake Cortex
<!-- ------------------------ -->
## Overview 

In this quickstart, you'll learn how to build an automated FAQ generation system using customer support tickets and Large Language Models (LLMs). The application analyzes support conversations and automatically generates relevant FAQ entries that can be viewed through an interactive Streamlit interface.

### What You'll Learn 
- How to process customer support conversations using Snowflake
- How to generate FAQs automatically using LLMs
- How to create an interactive FAQ viewer with filtering and search capabilities

### What You'll Build
- A system that processes support tickets to extract common issues
- A searchable FAQ interface with filtering capabilities
- An automated FAQ generation pipeline using LLMs
- An interface to view the generated FAQs

### Prerequisites
- [Snowflake account](https://signup.snowflake.com/?utm_cta=trial-en-www-homepage-top-right-nav-ss-evg&_ga=2.74406678.547897382.1657561304-1006975775.1656432605&_gac=1.254279162.1656541671.Cj0KCQjw8O-VBhCpARIsACMvVLPE7vSFoPt6gqlowxPDlHT6waZ2_Kd3-4926XLVs0QvlzvTvIKg7pgaAqd2EALw_wcB) with:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
  - [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

<!-- ------------------------ -->
## Setup Environment

### Create Database and Tables

First, let's set up our database and required tables:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS CUSTOMER_SUPPORT;
CREATE SCHEMA IF NOT EXISTS CUSTOMER_SUPPORT.FAQS;

-- Create FAQ table
CREATE OR REPLACE TABLE CUSTOMER_SUPPORT.FAQS.CUSTOMER_SUPPORT_FAQ (
    ISSUE_AREA VARCHAR,
    ISSUE_CATEGORY VARCHAR,
    QUESTION VARCHAR,
    ANSWER VARCHAR,
    CREATED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```
### Load Sample Data

1. Download the sample customer support tickets [parquet file](https://github.com/Snowflake-Labs/sfguide-autogen-faqs-for-customer-support-with-snowflake-cortex/blob/main/data/customer_service_tickets.parquet).

2. Upload the parquet file using Snowsight:
   - Navigate to Data → Databases → CUSTOMER_SUPPORT → Tables
   - Click "Load Data" in the top right
   - Select "Load from Files"
   - Choose "Upload" and select your parquet file
   - In the wizard:
     * Select "Parquet" as file format
     * Choose "CUSTOMER_SUPPORT_TICKETS" as target table
     * Click "Load" to start the upload


Dataset from NebulaByte/E-Commerce_Customer_Support_Conversations on HuggingFace
<!-- ------------------------ -->
## Process Support Tickets

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

Now we'll generate FAQ entries using the Claude 3.5 Sonnet LLM:

### Snowflake Notebook


1. Click on [Notebook](https://github.com/Snowflake-Labs/sfguide-autogen-faqs-for-customer-support-with-snowflake-cortex) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)  
     
2. In your Snowflake account:  
     
   * On the left hand navigation menu, click on Projects » Notebooks  
   * On the top right, click on Notebook down arrow and select **Import .ipynb** file from the dropdown menu
   * Select the file you downloaded in step 1 above

3. In the Create Notebook popup:  
     
   * For Notebook location, select **CUSTOMER_SUPPORT.FAQS** for your database and schema  
   * Select your **Warehouse**  
   * Click on Create button

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
        SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet', PROMPT) AS RAW_OUTPUT
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
## Verify and Review

Check the generated FAQs:

```sql
SELECT * FROM CUSTOMER_SUPPORT_FAQ ORDER BY CREATED_AT DESC;
```

Ensure:
- Questions are relevant and clear
- Answers are accurate and helpful
- Categories are correctly assigned

<!-- ------------------------ -->

<!-- ------------------------ -->
## Build the FAQ Viewer

1. Navigate to Streamlit in Snowflake:  
     
   * Click on the **Streamlit** tab in the left navigation pane  
   * Click on **\+ Streamlit App** button in the top right
   
2. Configure App Settings:  
     
   * Enter a name for your app (e.g., Customer\_Support\_AutoGen\_FAQ\_Viewer)  
   * Select a warehouse to run the app (Small warehouse is sufficient)  
   * Choose the **CUSTOMER_SUPPORT.FAQS** database and schema

```python
# Import python packages
import streamlit as st
import pandas as pd

from snowflake.snowpark.context import get_active_session

# Get the current credentials
session = get_active_session()

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

# Streamlit app
def main():
    st.title("Customer Support FAQ Viewer")
    
    # Sidebar for search and filters
    st.sidebar.header("Filters & Search")
    
    # Search bar in the sidebar
    search_query = st.sidebar.text_input("Search FAQs:", "")
    
    # Connect to Snowfla
    faqs = fetch_faqs()
    
    # Check if filters returned results
    if faqs.empty:
        st.warning("No FAQs match your filters or search query.")
        return
    
   # Filters in the sidebar
    issue_area = st.sidebar.selectbox("Filter by Issue Area:", ["All"] + sorted(faqs["ISSUE_AREA"].unique()))
    issue_category = st.sidebar.selectbox("Filter by Issue Category:", ["All"] + sorted(faqs["ISSUE_CATEGORY"].unique()))
    
    # Apply filters
    if issue_area != "All":
        faqs = faqs[faqs["ISSUE_AREA"] == issue_area]
    if issue_category != "All":
        faqs = faqs[faqs["ISSUE_CATEGORY"] == issue_category]
    if search_query.strip():
        faqs = faqs[
            faqs["QUESTION"].str.contains(search_query, case=False, na=False) |
            faqs["ANSWER"].str.contains(search_query, case=False, na=False)
        ]
    
    # Check if filters returned results
    if faqs.empty:
        st.warning("No FAQs match your filters or search query.")
        return
    
    # Pagination setup
    page_size = 5
    total_pages = (len(faqs) - 1) // page_size + 1
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = 0

    # Current page data
    current_page = st.session_state["current_page"]
    paginated_faqs = paginate_data(faqs, current_page, page_size)

    # Display FAQs
    for index, row in paginated_faqs.iterrows():
        with st.expander(f"{row['QUESTION']}"):
            st.write(f"**Answer:** {row['ANSWER']}")
            st.write(f"*Issue Area:* {row['ISSUE_AREA']}  |  *Issue Category:* {row['ISSUE_CATEGORY']}  |  *Created At:* {row['CREATED_AT']}")
    
    # Pagination controls at the bottom
    st.markdown(
        """
        <style>
        .pagination-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-top: 20px;
            gap: 20px;
        }
        .pagination-buttons {
            background-color: #007BFF;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            cursor: pointer;
            font-size: 16px;
        }
        .pagination-buttons:disabled {
            background-color: #CCCCCC;
            cursor: not-allowed;
        }
        .pagination-summary {
            font-size: 16px;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="pagination-container">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    # Safe button handling
    previous_button_pressed = col1.button("⬅️ Previous", key="prev")
    next_button_pressed = col3.button("➡️ Next", key="next")

    if previous_button_pressed and current_page > 0:
        st.session_state["current_page"] -= 1
    elif next_button_pressed and current_page < total_pages - 1:
        st.session_state["current_page"] += 1

    with col2:
        st.markdown(
            f"<div class='pagination-summary'>Page {st.session_state['current_page'] + 1} of {total_pages}</div>",
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
if __name__ == "__main__":
    main()
```

## Conclusion and Resources

Congratulations! You've built an automated FAQ generation system that:
- Processes support conversations
- Generates FAQs using LLMs
- Provides a searchable interface

### What You Learned
- Using Snowflake Cortex LLM functions
- Processing conversational data
- Building Streamlit applications in Snowflake

### Related Resources
Documentation:
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

Sample Code & Guides:
- [Snowpark Python Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Streamlit Components](https://docs.streamlit.io/library/api-reference)
- [LLM Best Practices](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-overview)