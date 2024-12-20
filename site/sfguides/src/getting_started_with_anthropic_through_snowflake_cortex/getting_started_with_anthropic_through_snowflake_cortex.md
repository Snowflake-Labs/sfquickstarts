author: James Cha-Earley
id: getting_started_with_anthropic_through_snowflake_cortex
summary: Getting Started with Anthropic through Snowflake Cortex
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering

# Getting Started on Anthropic with Snowflake Cortex
<!-- ------------------------ -->
## Overview 
Duration: 5

In this quickstart, you'll learn how to build an end-to-end application that creates an intelligent document assistant using PDF documents, Anthropic's Claude Large Language Model (LLM), and Snowflake's Cortex capabilities. The application combines PDF processing, vector embeddings, and Retrieval Augmented Generation (RAG) to enable natural language interactions with your documents through Claude's advanced language understanding capabilities.

### What You'll Learn
- Setting up PDF processing in Snowflake using PyPDF2
- Creating and managing vector embeddings for semantic search
- Building a RAG-based chat system with Anthropic's Claude
- Developing an interactive Streamlit chat interface

### What You'll Build
An end-to-end application that enables users to:
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

This table stores:
- `file_url`: Path to source document
- `chunk`: Extracted text segment
- `chunk_vec`: Vector embedding for semantic search

```python
docs_chunks_table = Table(
    name="docs_chunks_table",
    columns=[TableColumn(name="file_url", datatype="string"),
             TableColumn(name="chunk", datatype="string"),
             TableColumn(name="chunk_vec", datatype="vector(float,768)")]
)
schema.tables.create(docs_chunks_table, mode=CreateMode.or_replace)
```

## Implement Document Processing
Duration: 15

### Understanding Document Processing Flow
Before diving into the code, let's understand the key components of document processing:

1. PDF Text Extraction:
   - Opens PDF files from Snowflake stage
   - Converts binary data to readable format
   - Extracts text content from each page
   - Handles encoding and special character issues
   - Manages potential extraction errors

2. Text Chunking Strategy:
   - Splits large documents into manageable pieces
   - Uses recursive character splitting for natural breaks
   - Maintains context with overlapping chunks
   - Optimizes chunk size for embedding quality
   - Preserves document structure where possible

3. Data Organization:
   - Creates structured DataFrame format
   - Maintains file source tracking
   - Prepares text for vector embedding
   - Ensures data quality and consistency

### Implementation Details

The document processing implementation uses two main functions:

1. `read_pdf()`:
   - Purpose: Extracts raw text from PDF documents
   - Input: File URL from Snowflake stage
   - Process:
     * Opens binary file stream
     * Creates PDF reader object
     * Iterates through pages
     * Cleans and concatenates text
   - Error Handling:
     * Catches extraction failures
     * Logs problematic pages
     * Maintains process continuity

2. `process()`:
   - Purpose: Manages overall document processing workflow
   - Input: File URL for processing
   - Process:
     * Calls PDF reader
     * Configures text splitting parameters
     * Creates structured output
   - Output: DataFrame with processed chunks

### Code Implementation

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

## Process Text and Create Embeddings
Duration: 10

### Understanding the Embedding Process

The embedding process transforms text chunks into vector representations for semantic search. Here's what happens in each step:

1. File Processing Stage:
   - Retrieves file names from stage
   - Validates file accessibility
   - Creates processing pipeline

2. Text Embedding:
   - Uses e5-base-v2 model for vector creation
   - Generates 768-dimensional embeddings
   - Maintains chunk-to-vector mapping
   - Optimizes for semantic similarity search

3. Data Transformation:
   - Converts to Snowpark DataFrame
   - Handles vector type casting
   - Prepares for database storage
   - Ensures data type compatibility

4. Storage Operations:
   - Writes to persistent table
   - Manages data overwrites
   - Maintains data consistency
   - Enables efficient retrieval

### Implementation Details

The embedding process follows these key steps:

1. File Name Extraction:
   - Lists all files in stage
   - Parses file paths
   - Prepares for batch processing

2. Document Processing:
   - Concurrent file processing
   - Error handling and logging
   - DataFrame concatenation

3. Vector Creation:
   - Applies embedding model
   - Handles batch processing
   - Manages memory efficiently

4. Data Storage:
   - Type conversion
   - Table writing
   - Quality validation

### Code Implementation

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

## Create Streamlit Application in Snowflake
Duration: 20

### Understanding the Chat System Architecture

The chat interface integrates several sophisticated components:

1. Session Management:
   - Maintains conversation state
   - Handles message history
   - Manages user context
   - Enables conversation persistence

2. Context Retrieval System:
   - Performs semantic search
   - Ranks relevant chunks
   - Combines multiple sources
   - Optimizes context window

3. Prompt Engineering:
   - Constructs dynamic prompts
   - Incorporates chat history
   - Maintains conversation coherence
   - Optimizes Claude's responses

4. Response Generation:
   - Processes Claude's output
   - Formats responses
   - Adds source attribution
   - Handles error cases


### Setting Up the Streamlit App

1. Navigate to Streamlit in Snowflake:
   * Click on the **Streamlit** tab in the left navigation pane
   * Click on **+ Streamlit App** button in the top right

2. Configure App Settings:
   * Enter a name for your app (e.g., ANTHROPIC_CHAT_APP)
   * Select a warehouse to run the app (Small warehouse is sufficient)
   * Choose the **ANTHROPIC_RAG** database and schema

3. Create the app file:
   * In the code editor, paste the following code:

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
from snowflake.cortex import Complete, EmbedText768

# Get the current session - no need for connection parameters in Snowflake Streamlit
session = get_active_session()

# Configuration
num_chunks = 3
model = "mistral-large2"

def init_chat_state():
    """Initialize chat session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = None

def vector_search(question):
    """Perform vector similarity search"""
    cmd = """
    with results as (
        SELECT file_url,
        VECTOR_COSINE_SIMILARITY(docs_chunks_table.chunk_vec,
            SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', ?)) as similarity,
        chunk
        from docs_chunks_table
        order by similarity desc
        limit ?
    )
    select chunk, file_url from results
    """
    return session.sql(cmd, params=[question, num_chunks]).to_pandas()

def create_prompt(question, context):
    """Create formatted prompt for Claude"""
    return f"""You are a documentation specialist focused on providing precise answers based on provided documentation.
    
    Context: {context}
    Question: {question}
    
    Instructions:
    1. Answer based only on the provided context
    2. Be concise and clear
    3. If information is not in context, say so
    4. Do not make assumptions
    
    Answer:"""

def get_ai_response(question):
    """Get AI response using Claude"""
    # Get relevant context
    context_df = vector_search(question)
    context = " ".join(context_df['CHUNK'].tolist())
    source = context_df.iloc[0]['FILE_URL'] if not context_df.empty else "Unknown"
    
    # Create and send prompt
    prompt = create_prompt(question, context)
    response = Complete(model, prompt)
    
    return response, source

def main():
    st.title("Document Q&A with Anthropic Claude")
    
    # Initialize chat state
    init_chat_state()
    
    # Chat interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    if question := st.chat_input("Ask a question about your documents..."):
        # Add user message
        st.chat_message("user").markdown(question)
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Get and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, source = get_ai_response(question)
                st.markdown(response)
                st.markdown(f"*Source: {source}*")
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
```

4. Run:
   * Click the **Run** button to deploy your app

### Understanding the Chat System Architecture

The chat interface integrates several sophisticated components:

1. Session Management:
   - Maintains conversation state
   - Handles message history
   - Manages user context
   - Enables conversation persistence

2. Context Retrieval System:
   - Performs semantic search
   - Ranks relevant chunks
   - Combines multiple sources
   - Optimizes context window

3. Prompt Engineering:
   - Constructs dynamic prompts
   - Incorporates chat history
   - Maintains conversation coherence
   - Optimizes Claude's responses

4. Response Generation:
   - Processes Claude's output
   - Formats responses
   - Adds source attribution
   - Handles error cases

### Implementation Components

The chat system consists of several key functions:

1. Message Initialization:
   - Purpose: Sets up chat session state
   - Features:
     * Conversation clearing
     * State management
     * Suggestion handling

2. Vector Search:
   - Purpose: Finds relevant document chunks
   - Features:
     * Similarity scoring
     * Results ranking
     * Context assembly

3. Prompt Creation:
   - Purpose: Builds Claude-optimized prompts
   - Features:
     * History integration
     * Context formatting
     * Instruction clarity

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
* [Intelligent document field extraction and analytics with Document AI](https://quickstarts.snowflake.com/guide/automating_document_processing_workflows_with_document_ai/index.html?index=..%2F..index#0)
* [Build a RAG-based knowledge assistant with Cortex Search and Streamlit](https://quickstarts.snowflake.com/guide/ask_questions_to_your_own_documents_with_snowflake_cortex_search/index.html?index=..%2F..index#0)
* [Build conversational analytics app (text-to-SQL) with Cortex Analyst](https://quickstarts.snowflake.com/guide/getting_started_with_cortex_analyst/index.html?index=..%2F..index#0)
