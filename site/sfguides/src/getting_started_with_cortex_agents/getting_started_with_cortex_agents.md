author: James Cha-Earley
id: getting_started_with_cortex_agents
summary: Get started with Cortex Agents
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Getting Started with Cortex Agents

## Overview
Duration: 5

Modern organizations face the challenge of managing both structured data (like metrics and KPIs) and unstructured data (such as customer conversations, emails, and meeting transcripts). The ability to analyze and derive insights from both types of data is crucial for understanding customer needs, improving processes, and driving business growth. 

In this quickstart, you'll learn how to build an Intelligent Sales Assistant that leverages Snowflake's capabilities for analyzing sales conversations and metrics. Using Cortex Agents and Streamlit, we'll create an interactive and intuitive assistant.

#### Cortex Analyst
- Converts natural language questions into SQL queries
- Understands semantic models defined in YAML files
- Enables querying data without writing SQL manually
- Handles complex analytical questions about sales metrics
- Achieves over 90% accuracy through user-generated semantic models that capture domain knowledge and business context

#### Cortex Search
- Delivers best-in-class search performance through a hybrid approach combining semantic and keyword search
- Leverages an advanced embedding model (E5) to understand complex semantic relationships
- Enables searching across unstructured data with exceptional accuracy and speed
- Supports real-time indexing and querying of large-scale text data
- Returns contextually relevant results ranked by relevance scores

#### Cortex Agents
The Cortex Agents is a stateless REST API endpoint that:
- Seamlessly combines Cortex Search's hybrid search capabilities with Cortex Analyst's 90%+ accurate SQL generation
- Streamlines complex workflows by handling:
  - Context retrieval through semantic and keyword search
  - Natural language to SQL conversion via semantic models
  - LLM orchestration and prompt management
- Enhances response quality through:
  - In-line citations to source documents
  - Built-in answer abstaining for irrelevant questions
  - Multi-message conversation context management
- Optimizes application development with:
  - Single API call integration
  - Streamed responses for real-time interactions
  - Reduced latency through efficient orchestration

These capabilities work together to:
1. Search through sales conversations for relevant context
2. Go from Text to SQL to answer analytical questions
3. Combine structured and unstructured data analysis
4. Provide natural language interactions with your data

## Setup Workspace
Duration: 10

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=LnJgA8TM) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/setup.sql) to execute all statements in order from top to bottom.

This script will:
- Create the database, schema, and warehouse
- Create tables for sales conversations and metrics
- Load sample sales data
- Enable change tracking for real-time updates
- Configure Cortex Search service
- Create a stage for semantic models

**Step 2.** In Snowsight, upload the [sales_metrics_model.yaml](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/sales_metrics_model.yaml) to Snowflake Stage

- Select Data
- Select Databases
- Choose `SALES_INTELLIGENCE`
- Next select `DATA`
- Go to Stages, choose `MODELS`
- On the top right, choose Files
- Upload `sales_metrics_mode.yaml` file

## Building the Application
Duration: 15

**Step 1.** Create a new directory for your project and navigate to it:
```bash
mkdir intelligent-sales-assistant
cd intelligent-sales-assistant
```

**Step 2.** Download the following files from the repository:
- [app.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/app.py): Main Streamlit application
- [generate_jwt.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/generate_jwt.py): JWT token generator
- [requirements.txt](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents/blob/main/requirements.txt): Dependencies file

> aside positive
> The repository contains sample data and configuration files needed to run the application. Make sure to download all required files.

**Step 3.** Create a Python virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

**Step 4.** Install the required dependencies:
```bash
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file with your Snowflake credentials:

```text
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_ACCOUNT_URL=your_account_url
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
RSA_PRIVATE_KEY_PATH=path_to_your_key.p8
```

### Application Implementation

In your `app.py`, set up the imports and configurations:

```python
import streamlit as st
import json
import requests
import sseclient
import os
from dotenv import load_dotenv
import generate_jwt
import pandas as pd
import snowflake.connector

# Load environment variables
load_dotenv()

# Constants
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_ACCOUNT_URL = os.getenv("SNOWFLAKE_ACCOUNT_URL")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
RSA_PRIVATE_KEY_PATH = os.getenv("RSA_PRIVATE_KEY_PATH")

CORTEX_SEARCH_SERVICES = "sales_intelligence.data.sales_conversation_search"
SEMANTIC_MODELS = "@sales_intelligence.data.models/sales_metrics_model.yaml"
```

Create the Snowflake query execution function:

```python
def run_snowflake_query(query):
    """Execute a Snowflake query and return results with column names"""
    try:
        conn = snowflake.connector.connect(
            account=SNOWFLAKE_ACCOUNT,
            host=SNOWFLAKE_ACCOUNT_URL,
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            role=SNOWFLAKE_ROLE,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA
        )
        
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        results = cursor.fetchall()

        cursor.close()
        conn.close()
        return results, columns

    except Exception as e:
        st.error(f"Error executing SQL: {str(e)}")
        return None, None
```

Implement the Cortex Agents API call:

```python
def snowflake_api_call(query: str, jwt_token: str, limit: int = 10):
    """Make API call to Cortex Agents"""
    url = f"https://{SNOWFLAKE_ACCOUNT_URL}/api/v2/cortex/agent:run"
    
    headers = {
        'X-Snowflake-Authorization-Token-Type': 'KEYPAIR_JWT',
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Authorization': f'Bearer {jwt_token}'
    }
    
    payload = {
        "model": "claude-3-5-sonnet",
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": query}]
            }
        ],
        "tools": [
            {
                "tool_spec": {
                    "type": "cortex_analyst_text_to_sql",
                    "name": "analyst1"
                }
            },
            {
                "tool_spec": {
                    "type": "cortex_search",
                    "name": "search1"
                }
            }
        ],
        "tool_resources": {
            "analyst1": {"semantic_model_file": SEMANTIC_MODELS},
            "search1": {
                "name": CORTEX_SEARCH_SERVICES,
                "max_results": limit
            }
        }
    }
    
    response = requests.post(url=url, headers=headers, json=payload, stream=True)
    return sseclient.SSEClient(response)
```

Create the response processing function:

```python
def process_sse_response(sse_client):
    """Process streaming response from Cortex Agents"""
    text = ""
    citations = []
    debug_info = ""
    sql = ""
    other_info = ""
    
    if not sse_client:
        return text, citations, debug_info, sql, other_info
        
    for event in sse_client.events():
        if event.data == "[DONE]":
            break
            
        try:
            data = json.loads(event.data)
            if 'delta' in data and 'content' in data['delta']:
                for content_item in data['delta']['content']:
                    content_type = content_item.get('type')
                    
                    if content_type == "tool_use":
                        tool_use = content_item.get('tool_use', {})
                        
                    elif content_type == "tool_results":
                        tool_results = content_item.get('tool_results', {})
                        if 'content' in tool_results:
                            for result in tool_results['content']:
                                if result.get('type') == 'json':
                                    text += result.get('json', {}).get('text', '')
                                    search_results = result.get('json', {}).get('searchResults', [])
                                    for search_result in search_results:
                                        text += f"\n• {search_result.get('text', '')}"
                                    sql = result.get('json', {}).get('sql', '')
                        
        except json.JSONDecodeError:
            continue
            
    return text, citations, debug_info, sql, other_info
```

Create the main Streamlit interface:

```python
def main():
    st.title("Intelligent Sales Assistant")

    # Initialize JWT Generator
    jwt_token = generate_jwt.JWTGenerator(
        SNOWFLAKE_ACCOUNT,
        SNOWFLAKE_USER,
        RSA_PRIVATE_KEY_PATH
    ).get_token()

    # Sidebar for new chat
    with st.sidebar:
        if st.button("New Conversation", key="new_chat"):
            st.session_state.messages = []
            st.rerun()

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Chat input form
    with st.form(key="query_form"):
        query = st.text_area(
            "",
            placeholder="Ask about sales conversations or sales data...",
            key="query_input",
            height=100
        )
        submit = st.form_submit_button("Submit")

    if submit and query:
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process query
        with st.spinner("Processing your request..."):
            sse_client = snowflake_api_call(query, jwt_token)
            text, citations, debug_info, sql, other_info = process_sse_response(sse_client)
            
            # Display chat history
            if text:
                st.session_state.messages.append({"role": "assistant", "content": text})

            for message in st.session_state.messages:
                with st.container():
                    st.markdown(f"**{'You' if message['role'] == 'user' else 'Assistant'}:**")
                    st.markdown(message["content"].replace("•", "\n\n-"))
                    st.markdown("---")
            
            # Display SQL results if present
            if sql:
                st.markdown("### Generated SQL")
                st.code(sql, language="sql")
                results, columns = run_snowflake_query(sql)
                if results and columns:
                    df = pd.DataFrame(results, columns=columns)
                    st.write("### Sales Metrics Report")
                    st.dataframe(df)

if __name__ == "__main__":
    main()
```

## Conclusion and Resources
Duration: 5

Congratulations! You've successfully built an Intelligent Sales Assistant using Snowflake Cortex capabilities. This application demonstrates the power of combining structured and unstructured data analysis through:
- Natural language interactions with your sales data
- Semantic search across sales conversations
- Automated SQL generation for analytics
- Real-time streaming responses
- Interactive chat interface

### What You Learned
- **Cortex Agents**: How to integrate and use the stateless REST API for combining search and analysis capabilities
- **Cortex Search**: How to leverage hybrid search combining semantic and keyword approaches for more accurate results
- **Cortex Analyst**: How to convert natural language to SQL using semantic models for high-accuracy analytics
- **Integration**: How to combine these capabilities into a cohesive application using Streamlit

### Related Resources
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/cortex-overview)
- [Cortex Agents Guide](https://docs.snowflake.com/en/user-guide/cortex-agents)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Cortex Search Overview](https://docs.snowflake.com/en/user-guide/cortex-search)