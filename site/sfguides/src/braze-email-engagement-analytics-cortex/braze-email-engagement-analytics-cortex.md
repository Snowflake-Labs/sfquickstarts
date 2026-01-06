author: Snowflake
id: braze-email-engagement-analytics-cortex
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Analyze Braze email engagement data with Snowflake Cortex AI for campaign optimization, personalization, and marketing insights.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# AI-Powered Campaign Analytics with Braze and Snowflake Cortex

## Overview

In this hands-on lab, you'll build an intelligent email engagement analytics application that combines Braze marketing data with Snowflake's Cortex AI capabilities. You'll create a natural language interface that allows marketers to query their email campaign performance data and receive AI-powered insights and recommendations.

## About Braze

Braze is a Customer Engagement Platform used to power personalized, real-time marketing communications across every touchpoint, including email, push notifications, in-app messages, SMS, and WhatsApp. The platform captures a rich stream of first-party data, such as detailed user profiles, message engagement metrics (sends, opens, clicks), and custom behavioral events like purchases or conversions.

By centralizing this granular engagement data in Snowflake, you can join it with other business data to build a comprehensive 360-degree customer view. This enables deeper analytics on user behavior, more sophisticated customer segmentation, and the ability to power data-driven personalization. 

Fundamentally, combining Braze and Snowflake allows you to fully understand the total business impact of your marketing workflows, campaigns and interactions across the ecosystem.


### What You'll Learn
- How to set up Snowflake environment for Braze engagement data
- How to create and configure a Cortex Analyst semantic model
- How to build a Streamlit application with natural language querying
- How to leverage Cortex Complete for automated insights and recommendations

### What You'll Build
- A complete data pipeline for Braze email engagement data
- A semantic model that enables natural language queries
- A Streamlit application with AI-powered analytics and recommendations

### Prerequisites
- Basic familiarity with SQL
- Access to Snowflake account with Cortex enabled
- Understanding of email marketing concepts

## Environment Setup

First, let's prepare your Snowflake environment and enable cross-region LLM usage.

### Enable Cross-Region Cortex Access

Run the following command in a SQL worksheet to enable cross-region usage of LLMs, as your current region may be limited in which LLMs it can use. This quickstart guide uses 'snowflake-arctic':

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

### Create Database and Schema

Run the following SQL commands in a SQL worksheet to create the warehouse, database and schema:

```sql
-- create the database
CREATE OR REPLACE DATABASE BRAZE_ENGAGEMENT;

-- create the schema
CREATE SCHEMA BRAZE_ENGAGEMENT.EMAIL_DATA;

-- switch to database and schema that was created
USE DATABASE BRAZE_ENGAGEMENT;
USE SCHEMA EMAIL_DATA;

-- create stage for raw data
CREATE OR REPLACE STAGE EMAIL_STAGE DIRECTORY = (ENABLE = TRUE);
```

## Create Data Tables

Now we'll create tables for your email engagement data and campaign changelog data. The full table schemas for Braze engagement data can be found [here](https://www.braze.com/docs/assets/download_file/data-sharing-raw-table-schemas.txt?dadd92e90dc27e8a5066e9eea327c65e).

You will be prompted to download the files shortly from GDRIVE or an AWS bucket.

Positive
: **Note on Data Types**: For this lab, we're using `TIMESTAMP_LTZ` datatype rather than a Number representing a UNIX timestamp for easier use in setting up our semantic model.

Run the following SQL to create all necessary tables:

```sql
-- create the table to hold our changelog data
CREATE OR REPLACE TABLE CAMPAIGN_CHANGELOGS (
    ID VARCHAR(16777216),
	TIME NUMBER(38,0),
	APP_GROUP_ID VARCHAR(16777216),
	API_ID VARCHAR(16777216) PRIMARY KEY,  -- Primary key for relationships
	NAME VARCHAR(16777216),
	CONVERSION_BEHAVIORS ARRAY,
	ACTIONS ARRAY
);

-- create the table to hold our email send data
CREATE OR REPLACE TABLE EMAIL_SENDS (
    ID VARCHAR(16777216) PRIMARY KEY,  -- Primary key
	USER_ID VARCHAR(16777216),
	EXTERNAL_USER_ID VARCHAR(16777216),
	DEVICE_ID VARCHAR(16777216),
	APP_GROUP_ID VARCHAR(16777216),
	APP_GROUP_API_ID VARCHAR(16777216),
	TIME TIMESTAMP_LTZ(9),
	DISPATCH_ID VARCHAR(16777216),
	SEND_ID VARCHAR(16777216),
	CAMPAIGN_ID VARCHAR(16777216),
	CAMPAIGN_API_ID VARCHAR(16777216),
	MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_ID VARCHAR(16777216),
	CANVAS_API_ID VARCHAR(16777216),
	CANVAS_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_STEP_API_ID VARCHAR(16777216),
	CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	GENDER VARCHAR(16777216),
	COUNTRY VARCHAR(16777216),
	TIMEZONE VARCHAR(16777216),
	LANGUAGE VARCHAR(16777216),
	EMAIL_ADDRESS VARCHAR(16777216),
	IP_POOL VARCHAR(16777216),
	MESSAGE_EXTRAS VARCHAR(16777216),
	ESP VARCHAR(16777216),
	FROM_DOMAIN VARCHAR(16777216),
	SF_CREATED_AT TIMESTAMP_LTZ(9)
);

-- create the table to hold our email open data
CREATE OR REPLACE TABLE EMAIL_OPENS (
    ID VARCHAR(16777216),
	USER_ID VARCHAR(16777216),
	EXTERNAL_USER_ID VARCHAR(16777216),
	DEVICE_ID VARCHAR(16777216),
	APP_GROUP_ID VARCHAR(16777216),
	APP_GROUP_API_ID VARCHAR(16777216),
	TIME TIMESTAMP_LTZ(9),
	DISPATCH_ID VARCHAR(16777216),
	SEND_ID VARCHAR(16777216),
	CAMPAIGN_ID VARCHAR(16777216),
	CAMPAIGN_API_ID VARCHAR(16777216),
	MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_ID VARCHAR(16777216),
	CANVAS_API_ID VARCHAR(16777216),
	CANVAS_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_STEP_API_ID VARCHAR(16777216),
	CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	GENDER VARCHAR(16777216),
	COUNTRY VARCHAR(16777216),
	TIMEZONE VARCHAR(16777216),
	LANGUAGE VARCHAR(16777216),
	EMAIL_ADDRESS VARCHAR(16777216),
	USER_AGENT VARCHAR(16777216),
	IP_POOL VARCHAR(16777216),
	MACHINE_OPEN VARCHAR(16777216),
	ESP VARCHAR(16777216),
	FROM_DOMAIN VARCHAR(16777216),
	IS_AMP BOOLEAN,
	SF_CREATED_AT TIMESTAMP_LTZ(9),
	-- Compound primary key for one-to-one relationships
	PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);

-- create the table to hold our email click
CREATE OR REPLACE TABLE EMAIL_CLICKS (
    ID VARCHAR(16777216),
	USER_ID VARCHAR(16777216),
	EXTERNAL_USER_ID VARCHAR(16777216),
	DEVICE_ID VARCHAR(16777216),
	APP_GROUP_ID VARCHAR(16777216),
	APP_GROUP_API_ID VARCHAR(16777216),
	TIME TIMESTAMP_LTZ(9),
	DISPATCH_ID VARCHAR(16777216),
	SEND_ID VARCHAR(16777216),
	CAMPAIGN_ID VARCHAR(16777216),
	CAMPAIGN_API_ID VARCHAR(16777216),
	MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_ID VARCHAR(16777216),
	CANVAS_API_ID VARCHAR(16777216),
	CANVAS_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_STEP_API_ID VARCHAR(16777216),
	CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	GENDER VARCHAR(16777216),
	COUNTRY VARCHAR(16777216),
	TIMEZONE VARCHAR(16777216),
	LANGUAGE VARCHAR(16777216),
	EMAIL_ADDRESS VARCHAR(16777216),
    URL VARCHAR(16777216),
	USER_AGENT VARCHAR(16777216),
	IP_POOL VARCHAR(16777216),
    LINK_ID VARCHAR(16777216),
	LINK_ALIAS VARCHAR(16777216),
	MACHINE_OPEN VARCHAR(16777216),
	ESP VARCHAR(16777216),
	FROM_DOMAIN VARCHAR(16777216),
	IS_AMP BOOLEAN,
	SF_CREATED_AT TIMESTAMP_LTZ(9),
	-- Compound primary key for one-to-one relationships
	PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);

-- create the table to hold our email unsubscribe data
CREATE OR REPLACE TABLE EMAIL_UNSUBSCRIBES (
    ID VARCHAR(16777216),
	USER_ID VARCHAR(16777216),
	EXTERNAL_USER_ID VARCHAR(16777216),
	DEVICE_ID VARCHAR(16777216),
	APP_GROUP_ID VARCHAR(16777216),
	APP_GROUP_API_ID VARCHAR(16777216),
	TIME TIMESTAMP_LTZ(9),
	DISPATCH_ID VARCHAR(16777216),
	SEND_ID VARCHAR(16777216),
	CAMPAIGN_ID VARCHAR(16777216),
	CAMPAIGN_API_ID VARCHAR(16777216),
	MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_ID VARCHAR(16777216),
	CANVAS_API_ID VARCHAR(16777216),
	CANVAS_VARIATION_API_ID VARCHAR(16777216),
	CANVAS_STEP_API_ID VARCHAR(16777216),
	CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
	GENDER VARCHAR(16777216),
	COUNTRY VARCHAR(16777216),
	TIMEZONE VARCHAR(16777216),
	LANGUAGE VARCHAR(16777216),
	EMAIL_ADDRESS VARCHAR(16777216),
	IP_POOL VARCHAR(16777216),
	SF_CREATED_AT TIMESTAMP_LTZ(9),
	-- Compound primary key for one-to-one relationships
	PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);
```

After running this SQL, navigate to **Data** > **Databases** and you should see your BRAZE_ENGAGEMENT database, EMAIL_DATA schema, and the 5 tables you just created.

## Upload Sample Data

Now we'll upload sample CSV files to populate our tables with demo data.

### Download Sample Files

Download the following CSV files (also available through the AWS bucket provided):

- [USERS_MESSAGES_EMAIL_UNSUBSCRIBE_VIEW.csv](https://drive.google.com/file/d/18UVrQtTiKxjeuvZGjSevQqsf4Tvos-oe/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_CLICK_VIEW.csv](https://drive.google.com/file/d/1J-q5QXGfcXqaHeAuRbx5xZP5NFAHVsnq/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_OPEN_VIEW.csv](https://drive.google.com/file/d/1flPAmYxc5GDAE39C7AfxDoxJO3hGFtJg/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_SEND_VIEW.csv](https://drive.google.com/file/d/10IJVJ57RymlVodGQZOHXznDddx28sYBy/view?usp=sharing)
- [CHANGELOGS_CAMPAIGN_VIEW.csv](https://drive.google.com/file/d/1bh7hC__TMH52pmqnH2ZAEUA19AsC5Q7r/view?usp=sharing)

### Upload Files to Stage

To upload the data files:

1. Choose **Create** in the left-hand navigation and select **Add Data** from the dropdown
2. On the Add Data page, select **Load files into a stage**
3. Select the five files that you want to upload (listed above)
4. Select BRAZE_ENGAGEMENT as Database, EMAIL_DATA as Schema, and EMAIL_STAGE as Stage
5. Click **Upload**

Navigate to **Data > Databases**, click into your BRAZE_ENGAGEMENT Database, EMAIL_DATA Schema, and the EMAIL_STAGE. You should see your 5 files listed.

## Load Data into Tables

Now we'll load the data from your CSV files into their respective tables. Run the following SQL against the BRAZE_ENGAGEMENT database:

```sql
-- load data into changelog 
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."CAMPAIGN_CHANGELOGS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('CHANGELOGS_CAMPAIGN_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email sends tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_SENDS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_SEND_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email opens tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_OPENS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_OPEN_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email clicks tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_CLICKS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, null, $28, $29, $30, $31
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_CLICK_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email unsubscribes tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_UNSUBSCRIBES"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_UNSUBSCRIBE_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;
```

### Verify Data Load

Run the following queries to verify that your data has been loaded successfully:

```sql
-- view changelog table data
SELECT *
FROM BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
LIMIT 10;
```

```sql
-- view email sends data
SELECT *
FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS
LIMIT 10;
```

```sql
-- view email open data
SELECT *
FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS
LIMIT 10;
```

```sql
-- view email click data
SELECT *
FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS
LIMIT 10;
```

```sql
-- view email unsubscribes data
SELECT *
FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES
LIMIT 10;
```

## Create Semantic Model

Now we'll create a semantic model that enables natural language queries using Cortex Analyst.

### Initialize the Model

In Snowsight, go to **AI & ML > Cortex Analyst** and choose **Create new model**.

In the **Create Semantic Model** UI:
- Choose Stages
- Choose BRAZE_ENGAGEMENT as your Database, EMAIL_DATA as your Schema, and EMAIL_STAGE as your stage
- Name your model **"CAMPAIGN_ANALYTICS_MODEL"** (important: use this exact name)

### Select Tables

In the **Select tables** screen:
- Choose BRAZE_ENGAGEMENT as the database, EMAIL_DATA as the schema
- Check all 5 of your tables

### Select Columns

In the **Select columns** screen, expand all tables and choose the following columns (31 total):

**BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS**
- EXTERNAL_USER_ID
- DISPATCH_ID
- CAMPAIGN_API_ID
- URL
- LINK_ALIAS
- TIME
- TIMEZONE
- GENDER

**BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS**
- EXTERNAL_USER_ID
- DISPATCH_ID
- CAMPAIGN_API_ID
- TIME
- TIMEZONE
- GENDER

**BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES**
- EXTERNAL_USER_ID
- DISPATCH_ID
- CAMPAIGN_API_ID
- TIME
- TIMEZONE
- GENDER

**BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS**
- EXTERNAL_USER_ID
- DISPATCH_ID
- CAMPAIGN_API_ID
- MESSAGE_VARIATION_API_ID
- TIME
- TIMEZONE
- GENDER

**BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS**
- API_ID
- NAME
- CONVERSION_BEHAVIORS
- ACTIONS

Choose **"Include example data from selected columns to improve its quality"** and then **Create and Save**.

### Add Metrics

Now let's add metrics to our engagement tables. Defining these metrics ensures consistent, accurate, and reusable calculations across campaigns.

For **BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS** table, add:
- **Total Clicks**
  - Expression: `COUNT(ID)`
  - Metric Name: `TOTAL_CLICKS`
- **Unique Clickers**
  - Expression: `COUNT(DISTINCT EXTERNAL_USER_ID)`
  - Metric Name: `UNIQUE_CLICKERS`

For **BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS** table, add:
- **Total Opens**
  - Expression: `COUNT(ID)`
  - Metric Name: `TOTAL_OPENS`
- **Unique Openers**
  - Expression: `COUNT(DISTINCT EXTERNAL_USER_ID)`
  - Metric Name: `UNIQUE_OPENERS`

For **BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS** table, add:
- **Total Sends**
  - Expression: `COUNT(ID)`
  - Metric Name: `TOTAL_SENDS`
- **Unique Senders**
  - Expression: `COUNT(DISTINCT EXTERNAL_USER_ID)`
  - Metric Name: `UNIQUE_SENDS`

For **BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES** table, add:
- **Total Unsubs**
  - Expression: `COUNT(ID)`
  - Metric Name: `TOTAL_UNSUBS`
- **Unique Unsubs**
  - Expression: `COUNT(DISTINCT EXTERNAL_USER_ID)`
  - Metric Name: `UNIQUE_UNSUBS`

### Define Relationships

Click "+" to create new relationships. Set up the following 4 relationships:

**Sends to Changelog**
- Join type: left_outer
- Relationship type: many-to-one
- Left table: BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS
- Right table: BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
- Relationship Columns: CAMPAIGN_API_ID → API_ID

**Opens to Changelog**
- Join type: left_outer
- Relationship type: many-to-one
- Left table: BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS
- Right table: BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
- Relationship Columns: CAMPAIGN_API_ID → API_ID

**Clicks to Changelog**
- Join type: left_outer
- Relationship type: many-to-one
- Left table: BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS
- Right table: BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
- Relationship Columns: CAMPAIGN_API_ID → API_ID

**Unsubscribes to Changelog**
- Join type: left_outer
- Relationship type: many-to-one
- Left table: BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES
- Right table: BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
- Relationship Columns: CAMPAIGN_API_ID → API_ID

### Custom Instructions

Add the following custom instructions:

```
- "Engagement" is defined as opens or clicks
- "Success" is defined as opens or clicks
- This dataset contains email engagement data spanning from June 2023 through June 2025
- When suggesting time-based queries, use specific date ranges like "in 2024", "in 2025", "in June 2025", "in the first half of 2025", or "between January and June 2025"
- Avoid suggesting queries with "last month", "this month", or "recent" timeframes since the data has a fixed range ending in June 2025
- The most recent data available is from June 2025, so queries should reference that timeframe or earlier periods within the dataset range
- When users ask about recent performance, interpret this as referring to the most recent data available (June 2025 or late 2024/early 2025)
```

Click **Save** to save your semantic model.

### Test Your Model

Test your model with these questions:
- "What campaign had the most unsubscribes over all time?"
- "What campaign had the most engagement in the last 180 days?"

Save these as verified queries and add them as onboarding questions.

## Create Streamlit App

Now we'll create a Streamlit application that provides a natural language interface to your Braze data.

### Create the App

In the left-hand navigation, choose **Create** from the dropdown and select **Streamlit App > New Streamlit App**.

- Title your app: **"MyEngagementAnalyticApp"**
- For the App location, choose the BRAZE_ENGAGEMENT database and EMAIL_DATA schema

### Add the Application Code

Replace the default code with the following Streamlit application:

```python
"""
Email Engagement Data
====================
This app allows marketers to interact with their Braze engagement data using natural language.
"""
import json  # To handle JSON data
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import _snowflake  # For interacting with Snowflake-specific APIs
import pandas as pd
import streamlit as st  # Streamlit library for building the web app
from snowflake.snowpark.context import (
    get_active_session,
)  # To interact with Snowflake sessions
from snowflake.snowpark.exceptions import SnowparkSQLException

# List of available semantic model paths in the format: <DATABASE>.<SCHEMA>.<STAGE>/<FILE-NAME>
# Each path points to a YAML file defining a semantic model
AVAILABLE_SEMANTIC_MODELS_PATHS = [
    "BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_STAGE/CAMPAIGN_ANALYTICS_MODEL.yaml"
]
API_ENDPOINT = "/api/v2/cortex/analyst/message"
API_TIMEOUT = 50000  # in milliseconds

# Initialize a Snowpark session for executing queries
session = get_active_session()


def main():
    # Initialize session state
    if "messages" not in st.session_state:
        reset_session_state()
    show_header_and_sidebar()
    if len(st.session_state.messages) == 0:
        process_user_input("What questions can I ask about this email engagement data? The data covers June 2023 through June 2025.")
    display_conversation()
    handle_user_inputs()
    handle_error_notifications()
    display_warnings()


def reset_session_state():
    """Reset important session state elements."""
    st.session_state.messages = []  # List to store conversation messages
    st.session_state.active_suggestion = None  # Currently selected suggestion
    st.session_state.warnings = []  # List to store warnings


def show_header_and_sidebar():
    """Display the header and sidebar of the app."""

    # Sidebar with a reset button
    with st.sidebar:
        # sidebar with the title and introductory text of the app
        st.title("Marketing Insight Navigator")
        st.markdown(
        "Welcome to your Marketing Co-Pilot! I'm here to help you analyze your engagement data. Ask a question, and I'll find key insights, suggest improvements, and guide you to your next discovery."
        )
        st.selectbox(
            "Selected semantic model:",
            AVAILABLE_SEMANTIC_MODELS_PATHS,
            format_func=lambda s: s.split("/")[-1],
            key="selected_semantic_model_path",
            on_change=reset_session_state,
        )
        st.divider()
        # Center this button
        _, btn_container, _ = st.columns([2, 6, 2])
        if btn_container.button("Clear Chat History", use_container_width=True):
            reset_session_state()


def handle_user_inputs():
    """Handle user inputs from the chat interface."""
    # Handle chat input
    user_input = st.chat_input("What is your question?")
    if user_input:
        process_user_input(user_input)
    # Handle suggested question click
    elif st.session_state.active_suggestion is not None:
        suggestion = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(suggestion)


def handle_error_notifications():
    if st.session_state.get("fire_API_error_notify"):
        st.toast("An API error has occured!", icon="🚨")
        st.session_state["fire_API_error_notify"] = False


def process_user_input(prompt: str):
    """
    Process user input and update the conversation history.

    Args:
        prompt (str): The user's input.
    """
    # Clear previous warnings at the start of a new request
    st.session_state.warnings = []

    # Create a new message, append to history and display immediately
    new_user_message = {
        "role": "user",
        "content": [{"type": "text", "text": prompt}],
    }
    st.session_state.messages.append(new_user_message)
    with st.chat_message("user"):
        user_msg_index = len(st.session_state.messages) - 1
        display_message(new_user_message["content"], user_msg_index)

    # Show progress indicator inside analyst chat message while waiting for response
    with st.chat_message("analyst"):
        with st.spinner("Waiting for Analyst's response..."):
            time.sleep(1)
            response, error_msg = get_analyst_response(st.session_state.messages)
            if error_msg is None:
                analyst_message = {
                    "role": "analyst",
                    "content": response["message"]["content"],
                    "request_id": response["request_id"],
                }
            else:
                analyst_message = {
                    "role": "analyst",
                    "content": [{"type": "text", "text": error_msg}],
                    "request_id": response["request_id"],
                }
                st.session_state["fire_API_error_notify"] = True

            if "warnings" in response:
                st.session_state.warnings = response["warnings"]

            st.session_state.messages.append(analyst_message)
            st.rerun()


def display_warnings():
    """
    Display warnings to the user.
    """
    warnings = st.session_state.warnings
    for warning in warnings:
        st.warning(warning["message"], icon="⚠️")


def get_analyst_response(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """
    Send chat history to the Cortex Analyst API and return the response.

    Args:
        messages (List[Dict]): The conversation history.

    Returns:
        Optional[Dict]: The response from the Cortex Analyst API.
    """
    # Prepare the request body with the user's prompt
    request_body = {
        "messages": messages,
        "semantic_model_file": f"@{st.session_state.selected_semantic_model_path}",
    }

    # Send a POST request to the Cortex Analyst API endpoint
    resp = _snowflake.send_snow_api_request(
        "POST",  # method
        API_ENDPOINT,  # path
        {},  # headers
        {},  # params
        request_body,  # body
        None,  # request_guid
        API_TIMEOUT,  # timeout in milliseconds
    )

    # Content is a string with serialized JSON object
    parsed_content = json.loads(resp["content"])

    # Check if the response is successful
    if resp["status"] < 400:
        return parsed_content, None
    else:
        error_msg = f"""
🚨 An Analyst API error has occurred 🚨

* response code: `{resp['status']}`
* request-id: `{parsed_content['request_id']}`
* error code: `{parsed_content['error_code']}`

Message:

{parsed_content['message']}

        """
        return parsed_content, error_msg


def display_conversation():
    """
    Display the conversation history between the user and the assistant.
    """
    for idx, message in enumerate(st.session_state.messages):
        role = message["role"]
        content = message["content"]
        with st.chat_message(role):
            if role == "analyst":
                display_message(content, idx, message.get("request_id"))
            else:
                display_message(content, idx)


def display_message(
    content: List[Dict[str, Union[str, Dict]]],
    message_index: int,
    request_id: Union[str, None] = None,
):
    """
    Display a single message content.

    Args:
        content (List[Dict[str, str]]): The message content.
        message_index (int): The index of the message.
    """
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            # Display suggestions as buttons
            for suggestion_index, suggestion in enumerate(item["suggestions"]):
                if st.button(
                    suggestion, key=f"suggestion_{message_index}_{suggestion_index}"
                ):
                    st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            # Display the SQL query and results
            display_sql_query(
                item["statement"], message_index, item["confidence"], request_id
            )


@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute the SQL query and convert the results to a pandas DataFrame.

    Args:
        query (str): The SQL query.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[str]]: The query results and the error message.
    """
    global session
    try:
        df = session.sql(query).to_pandas()
        return df, None
    except SnowparkSQLException as e:
        return None, str(e)


def display_sql_confidence(confidence: dict):
    if confidence is None:
        return
    verified_query_used = confidence["verified_query_used"]
    with st.popover(
        "Verified Query Used",
        help="The verified query from Verified Query Repository, used to generate the SQL",
    ):
        with st.container():
            if verified_query_used is None:
                st.text(
                    "There is no query from the Verified Query Repository used to generate this SQL answer"
                )
                return
            st.text(f"Name: {verified_query_used['name']}")
            st.text(f"Question: {verified_query_used['question']}")
            st.text(f"Verified by: {verified_query_used['verified_by']}")
            st.text(
                f"Verified at: {datetime.fromtimestamp(verified_query_used['verified_at'])}"
            )
            st.text("SQL query:")
            st.code(verified_query_used["sql"], language="sql", wrap_lines=True)

@st.cache_data(show_spinner="Generating summary and recommendations...")
def get_summary_and_recommendations(df: pd.DataFrame, user_prompt: str) -> str:
    """
    Uses Cortex Complete to generate a summary based on the query results.

    Args:
        df (pd.DataFrame): The dataframe containing the results from the SQL query.
        user_prompt (str): The original natural language prompt from the user.

    Returns:
        str: A string with the summary and recommendations.
    """
    df_string = df.to_string(index=False)

    prompt = f"""
        A user asked the following question about their marketing engagement data:
        "{user_prompt}"

        Here is the data that was retrieved to answer the question:
        ```markdown
        {df_string}
        ```

        Please provide your textual response based on this data and question.
        The user asking the question is a marketer using Braze to create marketing campaigns. Therefore, try to always tie your answer into how the user can use the insights to make better marketing decisions on the platform.
        Format your response in Markdown.
    """

    try:
        prompt = prompt.replace("'", "''")
        summary_sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', '{prompt}') as summary"
        summary_df = session.sql(summary_sql).to_pandas()
        summary = summary_df["SUMMARY"][0]
        return summary
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return "Could not generate a summary and recommendation at this time."

@st.cache_data(show_spinner="Generating follow-up questions...")
def get_follow_up_questions(user_prompt: str, summary: str) -> List[str]:
    """
    Uses Cortex Complete to generate follow-up questions.
    """
    prompt = f"""
        Based on the original question "{user_prompt}" and the following summary:
        ---
        {summary}
        ---
        Generate 1 relevant follow-up question a marketer might ask. Only reference the data made available about email campaigns sends, opens, clicks and unsubscribes.
        The output must be only a single JSON array of strings, like:
        ["question 1"]
    """
    try:
        prompt = prompt.replace("'", "''")
        sql_query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', '{prompt}') as response"
        response_df = session.sql(sql_query).to_pandas()
        raw_response = response_df["RESPONSE"][0]
        json_part = raw_response[raw_response.find("[") : raw_response.rfind("]") + 1]
        questions = json.loads(json_part)
        return questions if isinstance(questions, list) else []
    except Exception as e:
        print(f"Error generating follow-up questions: {e}")
        return []

def display_sql_query(
    sql: str, message_index: int, confidence: dict, request_id: Union[str, None] = None
):
    """
    Executes the SQL query and displays the results in form of a data frame.

    Args:
        sql (str): The SQL query.
        message_index (int): The index of the message.
        confidence (dict): The confidence information of SQL query generation
        request_id (str): Request id from user request
    """

    # Display the SQL query
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")
        display_sql_confidence(confidence)

    # Display the results of the SQL query
    with st.expander("Results", expanded=True):
        with st.spinner("Running SQL..."):
            df, err_msg = get_query_exec_result(sql)
            if df is None:
                st.error(f"Could not execute generated SQL query. Error: {err_msg}")
            elif df.empty:
                st.write("Query returned no data")
            else:
                # Get the user's original prompt to provide context for the summary
                user_prompt = st.session_state.messages[message_index - 1]['content'][0]['text']
                summary_and_recs = get_summary_and_recommendations(df, user_prompt)
                
                # Show query results in two tabs
                data_tab, summary_tab = st.tabs(["Data 📄", "Summary & Recommendation 💡"])

                with data_tab:
                    st.dataframe(df, use_container_width=True)

                with summary_tab:
                    st.markdown(summary_and_recs)

                # Generate and display follow-up questions
                follow_up_questions = get_follow_up_questions(
                    user_prompt, summary_and_recs
                )
                if follow_up_questions:
                    st.markdown("---")
                    st.markdown("##### Suggested Follow-ups")
                    for i, question in enumerate(follow_up_questions):
                        if st.button(question, key=f"follow_up_{message_index}_{i}"):
                            st.session_state.active_suggestion = question
                            st.rerun()

if __name__ == "__main__":
    main()
```

Click **Create** to create your Streamlit app.

## Understanding Cortex Integration

Let's examine how our application leverages Snowflake Cortex capabilities:

### Cortex Analyst

Our app uses Cortex Analyst to convert natural language questions into SQL queries. Here's the key integration point:

```python
# Compile the request body with the user's prompt
request_body = {
    "messages": messages,
    "semantic_model_file": f"@{st.session_state.selected_semantic_model_path}",
}

# Send a POST request to the Cortex Analyst API endpoint
resp = _snowflake.send_snow_api_request(
    "POST",  # method
    API_ENDPOINT,  # path
    {},  # headers
    {},  # params
    request_body,  # body
    None,  # request_guid
    API_TIMEOUT,  # timeout in milliseconds
)
```

### Cortex Complete for Insights

We make two separate calls to Cortex Complete:

**1. Generate Summaries and Recommendations**

This function analyzes query results and provides marketing-specific insights.

**2. Generate Follow-up Questions**

This function suggests relevant next questions for deeper analysis.

Positive
: Both functions use the `snowflake-arctic` model to ensure consistent, high-quality responses tailored for marketing use cases.

## Testing Your Application

Now let's test our Marketing Insight Navigator application!

### Launch the App

Your Streamlit app should now be running. You can access it from the **Apps** section in Snowsight.

### Initial Questions

When you first open the app, it will automatically ask: "What questions can I ask about this email engagement data?"

You should see suggested questions including the verified queries we added earlier:
- "What campaign had the most unsubscribes over all time?"
- "What campaign had the most engagement in the last 180 days?"

### Test Natural Language Queries

Try asking specific questions about your email engagement data:

**Example 1: Timezone Analysis**
Ask: "What timezone had the highest engagement for Back In Stock campaigns?"

The app will:
- Generate and execute the appropriate SQL query
- Display the raw data results
- Provide a summary with marketing insights
- Suggest relevant follow-up questions

**Example 2: Testing Data Boundaries**
Ask: "What subject lines had the most engagement?"

The app should respond that it cannot answer this question because subject line data is not included in the current dataset. This demonstrates that the app won't hallucinate data.

### Understanding the Output

For each query, you'll see:

1. **SQL Query**: The generated SQL (expandable section)
2. **Results**: Two tabs containing:
   - **Data 📄**: Raw query results in a dataframe
   - **Summary & Recommendation 💡**: AI-generated insights and recommendations
3. **Suggested Follow-ups**: Relevant next questions to explore

### Key Features to Test

- **Natural Language Processing**: Ask questions in plain English
- **Data Validation**: Try asking about data that doesn't exist
- **Follow-up Suggestions**: Use the suggested questions to explore deeper
- **Marketing Context**: Notice how recommendations are tailored for marketers

Negative
: Remember that the app can only answer questions about data that exists in your semantic model. Questions about missing data fields will be politely declined.

## Conclusion And Resources

Congratulations! You've successfully built an intelligent email engagement analytics application that combines Braze marketing data with Snowflake's Cortex AI capabilities.

### What You Learned

You now have experience with:
- Setting up Snowflake environment for Braze engagement data
- Creating and configuring Cortex Analyst semantic models
- Building Streamlit applications with natural language querying
- Leveraging Cortex Complete for automated insights and recommendations
- Integrating multiple Cortex AI services in a single application

### What You Built

Your complete solution includes:
- **Data Pipeline**: Stores and processes Braze email engagement data in Snowflake
- **Semantic Model**: Enables natural language queries through Cortex Analyst
- **AI-Powered App**: Provides automated insights using Cortex Complete
- **Marketing Focus**: Delivers actionable guidance specifically for marketing stakeholders

### Key Capabilities

Your application can:
- Access and query Braze engagement data in Snowflake
- Offer a natural language interface for non-technical users
- Automatically generate summaries, SQL, and follow-up analysis
- Deliver actionable insights to marketing stakeholders
- Maintain data integrity by not hallucinating unavailable information

### Next Steps

To extend this solution, consider:
- Adding more Braze data tables (push notifications, in-app messages, etc.)
- Incorporating additional metrics and KPIs in your semantic model
- Creating scheduled data refreshes for real-time insights
- Building dashboard views for executive reporting
- Implementing user access controls and sharing capabilities

### Resources

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Braze Data Export Documentation](https://www.braze.com/docs/user_guide/data_and_analytics/export_braze_data/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Semantic Modeling Best Practices](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)

You now have the foundation to build sophisticated, AI-powered analytics applications that can transform how marketing teams interact with their data!
