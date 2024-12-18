author: James Cha-Earley
id: getting_started_with_anthropic_through_snowflake_cortex
summary: Getting Started with Anthropic through Snowflake Cortex
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering

# Getting Started with Anthropic RAG using Snowflake Notebooks
<!-- ------------------------ -->
## Overview 
Duration: 5

In this quickstart, you'll learn how to build an end-to-end application that creates an intelligent document assistant using PDF documents and Large Language Models (LLMs). The application combines PDF processing, vector embeddings, and Retrieval Augmented Generation (RAG) to enable natural language interactions with your documents.

### What You'll Learn
- Setting up PDF processing in Snowflake using PyPDF2
- Creating and managing vector embeddings for semantic search
- Building a RAG-based chat system with Anthropic's Claude
- Developing an interactive Streamlit chat interface

### What You'll Build
A full-stack application that enables users to:
- Upload and process PDF documents
- Search through documents using semantic similarity
- Engage in conversational Q&A about document content
- View source documents for responses
- Maintain chat history for contextual conversations

### Prerequisites
- Snowflake account in a [supported region for Cortex functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability)
- Account must have these features enabled:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Anaconda Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages#using-third-party-packages-from-anaconda)
  - [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
  - [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

## Setup Database, Schema, Stage
Duration: 10

### Create Database and Schema

1. Create a new database and schema for your project:

```sql
CREATE DATABASE IF NOT EXISTS anthropic_rag;
CREATE SCHEMA IF NOT EXISTS anthropic_rag;
```

### Create Document Storage Stage

1. Create a stage to store your PDF documents:

```sql
CREATE STAGE IF NOT EXISTS @Documents
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);
```

## Upload Documents

1. Navigate to Data > Databases > ANTHROPIC_RAG > DOCUMENTS > Stages
2. Click "Upload Files" button in top right
3. Select your PDF files

> aside positive
> TIP: For best results with PDFs:
> - Ensure text is machine readable (not scanned images)
> - Check document encoding is correct
> - Keep individual files under 10MB
> - Use standard PDF format

## Open Snowflake Notebooks
Duration: 5

1. Click on [Getting Started with Anthropic Notebook](https://github.com/your-repo/getting-started-with-anthropic.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

2. In your Snowflake account:
   * On the left hand navigation menu, click on Projects » Notebooks
   * On the top right, click on Notebook down arrow and select **Import .ipynb** file from the dropdown menu
   * Select the file you downloaded in step 1 above

3. In the Create Notebook popup:
   * For Notebook location, select **anthropic_rag** for your database and schema
   * Select your **Warehouse**
   * Click on Create button

## Environment Setup
Duration: 5

Here we add our imports that we will use for our project:
Key Components:
- `PyPDF2`: For processing PDF documents
- `langchain`: For text splitting and chunking
- `Streamlit`: Creates an intuitive chat interface
- `snowflake-ml-python`: For Snowflake Cortex capabilities

```python
# Import python packages
import streamlit as st
import pandas as pd
import PyPDF2, io
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

from snowflake.snowpark.context import get_active_session
from snowflake.cortex import Complete, EmbedText768
from snowflake.snowpark.types import VectorType, FloatType
from snowflake.core.table import Table, TableColumn
from snowflake.core import CreateMode, Root
from snowflake.snowpark.functions import cast, col

session = get_active_session()
root = Root(session)
database = root.databases[session.get_current_database()]
schema = database.schemas[session.get_current_schema()]
```

## Create Table Structure
Duration: 5

Create the table that will store processed documents:

```python
docs_chunks_table = Table(
    name="docs_chunks_table",
    columns=[TableColumn(name="file_url", datatype="string"),
             TableColumn(name="chunk", datatype="string"),
             TableColumn(name="chunk_vec", datatype="vector(float,768)")]
)
schema.tables.create(docs_chunks_table, mode=CreateMode.or_replace)
```

This table stores:
- `file_url`: Path to source document
- `chunk`: Extracted text segment
- `chunk_vec`: Vector embedding for semantic search

## Implement Document Processing
Duration: 15

### Create Processing Functions

The notebook implements two key functions for document processing:

```python
def read_pdf(file_url: str) -> str:
    with io.open(file_url, 'rb') as f:
        buffer = io.BytesIO(f.read())

    reader = PyPDF2.PdfReader(buffer)
    text = ""
    for page in reader.pages:
        try:
            text += page.extract_text().replace('\n', ' ').replace('\0', ' ')
        except:
            text = "Unable to Extract"
            logger.warn(f"Unable to extract from file {file_url}, page {page}")

    return text

def process(file_url: str):
    text = read_pdf(file_url)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,  # Adjust this as needed
        chunk_overlap = 300,  # Overlap to keep chunks contextual
        length_function = len
    )

    chunks = text_splitter.split_text(text)
    df = pd.DataFrame({
        'CHUNK' : chunks,
        'FILE_URL': file_url
    })
    
    return df
```

These functions:
1. Read PDF binary data
2. Extract text content
3. Split into overlapping chunks
4. Return structured DataFrame

## Process Text and Create Embeddings
Duration: 10

Process documents and create embeddings:

```python
# Extract file names and process files
file_names = [file['name'].split('/')[1] for file in files]

# Download and process files into a DataFrame
final_dataframe = pd.concat([
    process(f"downloads/{file_name}")
    for file_name in file_names
    if session.file.get(stage_name + '/' + file_name, "downloads") is not None
], ignore_index=True)

# Add CHUNK_VEC column
final_dataframe['CHUNK_VEC'] = final_dataframe['CHUNK'].apply(lambda chunk: EmbedText768('e5-base-v2', chunk))

# Create a Snowpark DataFrame and cast the vector type
snowpark_df = session.create_dataframe(final_dataframe).select(
    col("file_url"),
    col("chunk"),
    col("CHUNK_VEC").cast(VectorType(float, 768)).alias("CHUNK_VEC")
)

# Write the transformed data to the table
snowpark_df.write.mode("overwrite").save_as_table("docs_chunks_table")
```

This process:
1. Extracts text from all PDFs
2. Creates vector embeddings using e5-base-v2 model
3. Stores results in docs_chunks_table

## Build Chat Interface
Duration: 20

The notebook implements a sophisticated chat interface using Streamlit. Key components include:

### Chat History Management
```python
def init_messages():
    if st.session_state.clear_conversation or "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.suggestions = []
        st.session_state.active_suggestion = None
```

### Context Retrieval
```python
def vector_search(my_question):
    cmd = """
        with results as
     (SELECT file_url,
       VECTOR_COSINE_SIMILARITY(docs_chunks_table.chunk_vec,
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', ?)) as similarity,
       chunk
     from docs_chunks_table
     order by similarity desc
     limit ?)
     select chunk, file_url from results 
     """
    df_context = session.sql(cmd, params=[my_question, num_chunks]).to_pandas()
```

### Response Generation
```python
def create_prompt(user_question):
    chat_history = get_chat_history()
    if chat_history != []:
        question_summary = make_chat_history_summary(chat_history, user_question)
        prompt_context, file_name = vector_search(question_summary)
    else:
        prompt_context, file_name = vector_search(user_question)
        question_summary = ''

    prompt = f"""You are a documentation specialist focused on providing precise answers based on provided documentation...
    """
    return prompt, file_name
```

The interface provides:
- Chat history tracking
- Semantic search for relevant context
- Dynamic prompt generation
- Source document attribution
- Conversation management

## Performance Tips
Duration: 5

To optimize your RAG system:

1. Document Processing:
   - Use appropriate chunk sizes (default: 1500 characters)
   - Adjust overlap for better context (default: 300 characters)
   - Monitor processing times for large documents

2. Search Optimization:
   - Tune number of context chunks (default: 3)
   - Consider similarity thresholds
   - Monitor response times

3. Chat Experience:
   - Adjust history length for context (default: 5 messages)
   - Balance context window size
   - Consider memory usage with long conversations

## Conclusion and Resources
Duration: 5

Congratulations! You've built a sophisticated document Q&A system using Snowflake's Cortex capabilities and Anthropic's Claude. The system combines PDF processing, vector search, and conversational AI to create an intelligent document assistant.

### What You Learned
- How to process PDF documents in Snowflake
- How to implement semantic search with vector embeddings
- How to build a RAG system with chat history
- How to create an interactive Streamlit interface

### Related Resources
- [Snowflake Notebooks Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Streamlit in Snowflake Guide](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [PyPDF2 Documentation](https://pythonhosted.org/PyPDF2/)
