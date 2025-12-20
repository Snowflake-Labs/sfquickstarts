id: getting-started-with-ocr-and-rag-with-snowflake-notebooks
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/certified-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform
language: en
summary: Getting Started with OCR and RAG with Snowflake Notebooks 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
author: James Cha Earley

fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-ocr-rag-with-snowflake-notebooks



# Getting Started with OCR and RAG with Snowflake Notebooks
<!-- ------------------------ -->
## Overview 

In this quickstart, you'll learn how to build an end-to-end application that extracts text from images and makes it searchable using Large Language Models (LLMs). The application combines Optical Character Recognition (OCR), vector embeddings, and Retrieval Augmented Generation (RAG) to create an intelligent document assistant. 

### What You'll Learn
- Setting up OCR processing in Snowflake using Tesseract
- Creating and managing vector embeddings for semantic search
- Building a RAG-based question answering system
- Developing an interactive Streamlit interface

### What You'll Build
A full-stack application that enables users to:
- Upload images containing text
- Process images through OCR to extract text
- Search through extracted text using semantic similarity
- Ask questions about the documents' content and get AI-powered responses
- View source images alongside answers

### Prerequisites
- Snowflake account in a [supported region for Cortex functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability)
- Account must have these features enabled:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Anaconda Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages#using-third-party-packages-from-anaconda)
  - [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
  - [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

## Setup Environment

### Create Database and Schema

1. Open a new worksheet in Snowflake
2. Create the database and schema:

```sql
CREATE DATABASE IF NOT EXISTS ocr_rag;
CREATE SCHEMA IF NOT EXISTS ocr_rag;
```

### Create Image Storage Stage

1. Create a stage to store your images:

```sql
CREATE STAGE IF NOT EXISTS ocr_rag.images_to_ocr
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = true);
```

### Upload Images

[Download Sample Images](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ocr-rag-with-snowflake-notebooks/tree/main/sample_images)

1. Navigate to Data > Databases > OCR_RAG > IMAGES_TO_OCR > Stages
2. Click "Upload Files" button in top right
3. Select your image files
4. Verify upload success:

```sql
ls @images_to_ocr;
```

You should see your uploaded files listed with their sizes.

> 
> TIP: For best OCR results, ensure your images are:
> - Clear and well-lit
> - Text is oriented correctly
> - Minimum 300 DPI resolution
> - In common formats (PNG, JPEG, TIFF)

### Dataset citation
Sample Images taken from RVL-CDIP Dataset

A. W. Harley, A. Ufkes, K. G. Derpanis, "Evaluation of Deep Convolutional Nets for Document Image Classification and Retrieval," in ICDAR, 2015

Bibtex format:

@inproceedings{harley2015icdar,
    title = {Evaluation of Deep Convolutional Nets for Document Image Classification and Retrieval},
    author = {Adam W Harley and Alex Ufkes and Konstantinos G Derpanis},
    booktitle = {International Conference on Document Analysis and Recognition ({ICDAR})}},
    year = {2015}
}

## Open Snowflake Notebooks

1. Click on [Getting Started Notebook](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ocr-rag-with-snowflake-notebooks/blob/main/getting_started_with_ocr_and_rag_with_snowflake_notebooks.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)
2. In your Snowflake account:
* On the left hand navigation menu, click on Projects » Notebooks
* On the top right, click on Notebook down arrow and select **Import .ipynb** file from the dropdown menu
* Select the file you downloaded in step 1 above
3. In the Create Notebook popup
* For Notebook location, select **ocr_rag** for your database and **ocr_rag** as your schema
* Select your **Warehouse**
* Click on Create button
4. On the top right Click Packages
* Install **tesserocr**, **pillow**, and **snowflake**

Here we add our imports that we will use for our project 
Key Components:
- `Tesseract`: A powerful OCR engine that converts images to text
- `PIL [Pillow] (Python Imaging Library)`: Handles image processing tasks


```python
# Import python packages
import streamlit as st
import tesserocr
import io
import pandas as pd
from PIL import Image

# Import Snowpark packages
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.types import StringType, StructField, StructType, IntegerType
from snowflake.snowpark.files import SnowflakeFile
from snowflake.core import CreateMode
from snowflake.core.table import Table, TableColumn
from snowflake.core.schema import Schema
from snowflake.core import Root

# Setup session
session = get_active_session()
session.use_schema("ocr_rag")
root = Root(session)
database = root.databases[session.get_current_database()]
```

## Create Table Structure

In the Notebook we will create the table that will store processed documents:

```python
docs_chunks_table = Table(
    name="docs_chunks_table",
    columns=[TableColumn(name="relative_path", datatype="string"),
            TableColumn(name="file_url", datatype="string"),
            TableColumn(name="scoped_file_url", datatype="string"),
            TableColumn(name="chunk", datatype="string"),
            TableColumn(name="chunk_vec", datatype="vector(float,768)")]
)
database.schemas["ocr_rag"].tables.create(docs_chunks_table, mode=CreateMode.or_replace)
);
```

This table stores:
- `relative_path`: Path to source image in stage
- `file_url`: Full URL to access image
- `scoped_file_url`: Temporary URL for secure access
- `chunk`: Extracted text segment
- `chunk_vec`: Vector embedding for semantic search

## Implement OCR Processing

### Create OCR Function

In the Notebook we will create a User-Defined Table Function (UDTF) for OCR:

```python
session.sql("DROP FUNCTION IF EXISTS IMAGE_TEXT(VARCHAR)").collect()

class ImageText:
    def process(self, file_url: str):
        with SnowflakeFile.open(file_url, 'rb') as f:
            buffer = io.BytesIO(f.readall())
        image = Image.open(buffer)
        text = tesserocr.image_to_text(image)
        yield (text,)

output_schema = StructType([StructField("full_text", StringType())])

session.udtf.register(
    ImageText,
    name="IMAGE_TEXT",
    is_permanent=True,
    stage_location="@ocr_rag.images_to_ocr",
    schema="ocr_rag",
    output_schema=output_schema,
    packages=["tesserocr", "pillow","snowflake-snowpark-python"],
    replace=True
)
```

This function:
1. Reads image binary data from stage
2. Converts to PIL Image object
3. Processes with Tesseract OCR
4. Returns extracted text

### Process Images

In the Notebook we will run OCR on staged images:

```sql
SELECT 
    relative_path, 
    file_url, 
    build_scoped_file_url(@ocr_rag.images_to_ocr, relative_path) AS scoped_file_url,
    ocr_result.full_text
FROM 
    directory(@ocr_rag.images_to_ocr),
    TABLE(IMAGE_TEXT(build_scoped_file_url(@ocr_rag.images_to_ocr, relative_path))) AS ocr_result;
```

> 
> TROUBLESHOOTING: If OCR results are poor, check:
> - Image quality and resolution
> - Text orientation
> - Image format compatibility
> - Tesseract installation

## Process Text and Create Embeddings

In the Notebook we will insert processed text and create embeddings:

```sql
INSERT INTO docs_chunks_table (relative_path, file_url, scoped_file_url, chunk, chunk_vec)
SELECT 
    relative_path, 
    file_url,
    scoped_file_url,
    chunk.value,
    SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', chunk.value) AS chunk_vec
FROM
    {{run_through_files_to_ocr}},
    LATERAL FLATTEN(SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(full_text,'none', 4000, 400)) chunk;
```

This query:
1. Takes OCR output text
2. Splits into 4000-character chunks (400 character overlap)
3. Creates vector embeddings using e5-base-v2 model
4. Stores results in docs_chunks_table

Verify data insertion:
```sql
SELECT COUNT(*) FROM docs_chunks_table;
```

## Build Question-Answering Interface

### Create Streamlit App

This section in the Notebook creates a Streamlit application that enables users to ask questions about their OCR-processed documents. 
The application uses semantic search to find relevant text and generates answers using Snowflake Cortex LLMs.

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import pandas as pd

num_chunks = 3 
model = "mistral-7b"

def create_prompt(myquestion):
    cmd = """
     with results as
     (SELECT RELATIVE_PATH,
       VECTOR_COSINE_SIMILARITY(docs_chunks_schema.docs_chunks_table.chunk_vec,
                SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', ?)) as similarity,
       chunk
     from docs_chunks_schema.docs_chunks_table
     order by similarity desc
     limit ?)
     select chunk, relative_path from results 
     """
    df_context = session.sql(cmd, params=[myquestion, num_chunks]).to_pandas()      

    context_lenght = len(df_context) -1
    prompt_context = ""
    for i in range (0, context_lenght):
        prompt_context += df_context._get_value(i, 'CHUNK')
    prompt_context = prompt_context.replace("'", "")
    relative_path =  df_context._get_value(0,'RELATIVE_PATH')
    prompt = f"""
      'You are an expert assistance extracting information from context provided. 
       Answer the question based on the context. Be concise and do not hallucinate. 
       If you don´t have the information just say so.
      Context: {prompt_context}
      Question:  
       {myquestion} 
       Answer: '
       """
    cmd2 = f"select GET_PRESIGNED_URL(@ocr_rag.images_to_ocr, '{relative_path}', 360) as URL_LINK from directory(@ocr_rag.images_to_ocr)"
    df_url_link = session.sql(cmd2).to_pandas()
    url_link = df_url_link._get_value(0,'URL_LINK')

    return prompt, url_link, relative_path

def complete(myquestion, model_name):
    prompt, url_link, relative_path = create_prompt(myquestion)
    cmd = """
             select SNOWFLAKE.CORTEX.COMPLETE(?,?) as response
           """
    df_response = session.sql(cmd, params=[model_name, prompt]).collect()
    return df_response, url_link, relative_path

def display_response(question, model):
    response, url_link, relative_path = complete(question, model)
    res_text = response[0].RESPONSE
    st.markdown(res_text)
    display_url = f"Link to [{relative_path}]({url_link}) that may be useful"
    st.markdown(display_url)

st.title("Asking Questions to Your Scanned Documents with Snowflake Cortex:")
docs_available = session.sql("ls @ocr_rag.images_to_ocr").collect()
question = st.text_input("Enter question", placeholder="What are my documents about?", label_visibility="collapsed")
if question:
    display_response(question, model)
```

### Code Walkthrough

The application:
1. Uses vector similarity to find relevant text chunks
2. Creates a prompt with context and question
3. Calls Cortex LLM to generate answer
4. Displays answer and source image link

Key parameters:
- `num_chunks`: Number of context chunks (default: 3)
- `model`: LLM model (default: mistral-7b)

## Conclusion and Resources

Congratulations! You've successfully built an end-to-end OCR and RAG application in Snowflake that transforms images into searchable, queryable content. Using Snowflake Notebooks and Cortex capabilities, you've implemented a solution that processes images through OCR, creates vector embeddings for semantic search, and provides AI-powered answers using Large Language Models - all while keeping your data secure within Snowflake's environment. Finally, you created a Streamlit application that allows users to interactively query their document content using natural language.


### What You Learned
* How to implement OCR processing in Snowflake using Tesseract and Snowpark Python
* How to use open-source Python libraries from curated Snowflake Anaconda channel
* How to create and manage vector embeddings for semantic search capabilities
* How to build RAG applications using Snowflake Cortex Search and LLM functions
* How to create automated document processing pipelines using Snowflake Tasks
* How to develop interactive Streamlit applications within Snowflake

### Related Resources
Documentation:
- [Snowflake Notebooks Overview](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Streamlit in Snowflake Guide](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Download Reference Architecture](/content/dam/snowflake-site/developers/2025/ocr-rag-snowflake-notebooks.pdf)
- [Fork Notebook](https://github.com/Snowflake-Labs/sfguide-getting-started-with-ocr-rag-with-snowflake-notebooks)

Blogs & Articles:
- [Introduction to RAG Applications](/en/developers/guides/ask-questions-to-your-own-documents-with-snowflake-cortex-search/)
- [Cortex Search Best Practices](/engineering-blog/cortex-search-and-retrieval-enterprise-ai/)
- [Read Medium Blog](https://medium.com/snowflake/unlocking-insights-from-images-with-ocr-and-rag-in-snowflake-968298b0c3cc)

Sample Code & Guides:
- [Snowpark Python Guide](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
- [Snowflake Machine Learning](https://docs.snowflake.com/en/developer-guide/snowflake-ml/overview)
- [Watch the Demo](https://youtu.be/fEI9CbkJcCU?list=TLGG9VdpCfB4GAQyMjA5MjAyNQ)
