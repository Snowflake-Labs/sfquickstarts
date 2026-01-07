id: getting-started-with-llamaparse-and-cortex-search
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/partner-solution, snowflake-site:taxonomy/solution-center/includes/architecture, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/build
language: en
summary: Parse Documents with LlamaParse and Search with Cortex 
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
authors: Josh Reini


# Getting Started with LlamaParse and Cortex Search
<!-- ------------------------ -->

## Overview


This guide walks through how to build a RAG using LlamaParse (from LlamaIndex) to parse documents and Snowflake Cortex for text splitting, search and generation.

[LlamaParse](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/) is a genAI-native document parsing platform - built with LLMs and for LLM use cases. The main goal of LlamaParse is to parse and clean your data, ensuring that it's high quality before passing to any downstream LLM use case such as RAG or agents.

LlamaParse comes equipped with the following features:

* State-of-the-art table extraction
* Provide natural language instructions to parse the output in the exact format you want it.
* JSON mode
* Image extraction
* Support for 10+ file types (.pdf, .pptx, .docx, .html, .xml, and more)
* Foreign language support

<!-- ------------------------ -->

### What You Will Learn

* How to parse complex PDFs using LlamaParse
* How to convert Llama-Index document format to DataFrames
* How to load data into Snowflake
* How to split text for retrieval
* How to create and use Cortex Search services
* How to build a RAG pipeline for question answering

<!-- ------------------------ -->

### What You Will Build

* A workflow to parse and ingest PDFs into Snowflake
* A table of split text chunks for hybrid search (via Cortex Search)
* A RAG pipeline for Q&A using Cortex Search and Snowflake Cortex generation

<!-- ------------------------ -->

### What You Will Need

* A LlamaCloud API key ([get one here](https://docs.cloud.llamaindex.ai/api_key))
* A Snowflake account ([sign up here](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides))
* Python **3.10+**
* Required Python packages: `llama-cloud`, `snowflake-snowpark-python`, `snowflake-ml-python`, `pandas`

<!-- ------------------------ -->

## Setup


Set up your environment and credentials for LlamaParse and Snowflake. You'll need a [LlamaCloud API key](https://docs.cloud.llamaindex.ai/api_key) and a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides).

Once you have signed up for a Snowflake account, create database and warehouse using the following SQL statements:

```sql
CREATE DATABASE IF NOT EXISTS SEC_10KS;

CREATE OR REPLACE WAREHOUSE LLAMAPARSE_CORTEX_SEARCH_WH WITH
     WAREHOUSE_SIZE='X-SMALL'
     AUTO_SUSPEND = 120
     AUTO_RESUME = TRUE
     INITIALLY_SUSPENDED=TRUE;
```

To open the notebook, open [llama-parse-cortex-search.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-llamaparse-and-cortex-search/blob/main/llama-parse-cortex-search.ipynb) to download the Notebook from GitHub. (NOTE: Do NOT right-click to download.)

First, et your Llama-Cloud API key and Snowflake credentials as environment variables.

```python
import os
import nest_asyncio
nest_asyncio.apply()

os.environ["LLAMA_CLOUD_API_KEY"] = "llx-..."  # Replace with your LlamaCloud API key
os.environ["SNOWFLAKE_ACCOUNT"] = "..."        # Use hyphens in place of underscores
os.environ["SNOWFLAKE_USER"] = "..."
os.environ["SNOWFLAKE_PASSWORD"] = "..."
os.environ["SNOWFLAKE_ROLE"] = "..."
os.environ["SNOWFLAKE_WAREHOUSE"] = "LLAMAPARSE_CORTEX_SEARCH_WH"
os.environ["SNOWFLAKE_DATABASE"] = "SEC_10KS"
os.environ["SNOWFLAKE_SCHEMA"] = "PUBLIC"
```

<!-- ------------------------ -->

## Parse Documents with LlamaParse


This step uses [LlamaParse](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/) to parse your PDF or other supported documents into structured data suitable for downstream LLM and RAG workflows.

Download a PDF (e.g., [Snowflake's latest 10K](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/663fb935-b123-4bbb-8827-905bcbb8953c.pdf)) and save as `snowflake_2025_10k.pdf` in your working directory.

Then, use LlamaParse to parse the documents.

```python
from llama_cloud_services import LlamaParse

parser = LlamaParse(
    num_workers=4,
    verbose=True,
    language="en",
)

result = parser.parse("./snowflake_2025_10k.pdf")
```

<!-- ------------------------ -->

## Write to Snowflake


Convert the parsed documents to a DataFrame and load them into your Snowflake database for further processing and search.

Before writing to Snowflake, we need to convert LlamaIndex Documents to python DataFrames.

```python
# Get markdown documents
markdown_documents = result.get_markdown_documents(split_by_page=False)

import pandas as pd

# fields that matter only to vector/RAG helpers – we don’t need them here
_INTERNAL_KEYS_TO_SKIP = {
    "excluded_embed_metadata_keys",
    "excluded_llm_metadata_keys",
    "relationships",
    "metadata_template",
    "metadata_separator",
    "text_template",
    "class_name",
}

def documents_to_dataframe(documents):
    """Convert a list of LlamaIndex documents to a tidy pandas DataFrame,
    omitting vector-store helper fields that aren’t needed for retrieval.
    """
    rows = []

    for doc in documents:
        d = doc.model_dump(exclude_none=True)

        for k in _INTERNAL_KEYS_TO_SKIP:
            d.pop(k, None)

        # Pull out & flatten metadata
        meta = d.pop("metadata", {})
        d.update(meta)

        # Extract raw text
        t_res = d.pop("text_resource", None)
        if t_res is not None:
            d["text"] = t_res.get("text") if isinstance(t_res, dict) else getattr(t_res, "text", None)

        rows.append(d)

    return pd.DataFrame(rows)
```

Then, we can connect to Snowflake and write the dataframe to a table.

```python
from snowflake.snowpark import Session

connection_parameters = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "role": os.getenv("SNOWFLAKE_ROLE"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database": os.getenv("SNOWFLAKE_DATABASE"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA"),
}

session = Session.builder.configs(connection_parameters).create()
snowpark_df = session.create_dataframe(documents_df)
snowpark_df.write.mode("overwrite").save_as_table("snowflake_10k")
```

<!-- ------------------------ -->

## Split Text


Split the loaded document text into smaller chunks using the [Snowflake Cortex Text Splitter](https://docs.snowflake.com/en/sql-reference/functions/split_text_recursive_character-snowflake-cortex), preparing your data for search.

```python
split_text_sql = """
CREATE OR REPLACE TABLE SNOWFLAKE_10K_MARKDOWN_CHUNKS AS
SELECT
    ID,
    "file_name" as FILE_NAME,
    c.value::string as TEXT
FROM
    SNOWFLAKE_10K,
    LATERAL FLATTEN(input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
        "text",
        'markdown',
        512,
        128
    )) c;
"""

session.sql(split_text_sql).collect()
```

<!-- ------------------------ -->

## Create Cortex Search Service


Create a [Cortex Search Service](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview) on your chunked data to enable fast, hybrid search over your documents in Snowflake.

```python
create_search_service_sql = """
CREATE OR REPLACE CORTEX SEARCH SERVICE SNOWFLAKE_10K_SEARCH_SERVICE
  ON TEXT
  ATTRIBUTES ID, FILE_NAME
  WAREHOUSE = S
  TARGET_LAG = '1 hour'
AS (
  SELECT
    ID,
    FILE_NAME,
    TEXT
  FROM SEC_10KS.PUBLIC.SNOWFLAKE_10K_MARKDOWN_CHUNKS
);
"""

session.sql(create_search_service_sql).collect()
```

Now that the Cortex Search Service is created, we can create a python class to retrieve relevant chunks from the service.

```python
from snowflake.core import Root
from typing import List
from snowflake.snowpark.session import Session

class CortexSearchRetriever:
    def __init__(self, snowpark_session: Session, limit_to_retrieve: int = 4):
        self._snowpark_session = snowpark_session
        self._limit_to_retrieve = limit_to_retrieve

    def retrieve(self, query: str) -> List[str]:
        root = Root(self._snowpark_session)
        search_service = (
            root.databases["SEC_10KS"]
                .schemas["PUBLIC"]
                .cortex_search_services["SNOWFLAKE_10K_SEARCH_SERVICE"]
        )
        resp = search_service.search(
            query=query,
            columns=["text"],
            limit=self._limit_to_retrieve
        )
        return [curr["text"] for curr in resp.results] if resp.results else []

retriever = CortexSearchRetriever(snowpark_session=session, limit_to_retrieve=5)
retrieved_context = retriever.retrieve("What was the total revenue (in billions) for Snowflake in FY 2024? How much of that was product revenue?")
retrieved_context
```

<!-- ------------------------ -->

## Build RAG pipeline


Build a simple Retrieval-Augmented Generation (RAG) pipeline that uses your Cortex Search Service to retrieve relevant context and generate answers using [Snowflake Cortex Complete](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex) LLMs.

```python
from snowflake.cortex import complete

class RAG:
    def __init__(self, session):
        self.session = session
        self.retriever = CortexSearchRetriever(snowpark_session=self.session, limit_to_retrieve=10)

    def retrieve_context(self, query: str) -> list:
        return self.retriever.retrieve(query)

    def generate_completion(self, query: str, context_str: list) -> str:
        prompt = f"""
          You are an expert assistant extracting information from context provided.\n
          Answer the question concisely, yet completely. Only use the information provided.\n
          Context: {context_str}\n
          Question:\n{query}\nAnswer:\n"""
        response = complete("claude-4-sonnet", prompt, session=self.session)
        return response

    def query(self, query: str) -> str:
        context_str = self.retrieve_context(query)
        return self.generate_completion(query, context_str)

rag = RAG(session)
response = rag.query("What was the total revenue (in billions) for Snowflake in FY 2024? How much of that was product revenue?")
print(response)
```

<!-- ------------------------ -->

## Conclusion And Resources


Congratulations! You have parsed a PDF with LlamaParse, loaded it into Snowflake, indexed it with Cortex Search, and built a simple RAG pipeline for question answering on your data.

### What You Learned

* How to parse PDFs with LlamaParse
* How to load and split data in Snowflake
* How to create and use Cortex Search
* How to build a simple RAG pipeline for Q&A

### Related Resources

* [LlamaParse (LlamaIndex)](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/)
* [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
* [Snowflake Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
* [Fork the Repo](https://github.com/sfc-gh-jreini/llama-parse-cortex-search/blob/main/llama-cloud-snowflake.ipynb)
* [Watch the Demo](https://youtu.be/D1rw57cuwm8?list=TLGG75AAIM6FkzoyNDA5MjAyNQ)

