id: getting-started-with-llamaparse-and-cortex-search
summary: Parse Documents with LlamaParse and Search with Cortex
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Data-Science-&-Ai, Featured
authors: Josh Reini

# Getting Started with LlamaParse and Cortex Search
<!-- ------------------------ -->

## Overview

Duration: 5

This guide walks through how to build a RAG using LlamaParse (from LlamaIndex) as your parser and Cortex for text splitting and search.

The core functionalities include:

- Parse documents using LlamaParse
- Load parsed data into Snowflake
- Split text for search
- Create a Cortex Search service
- Retrieve relevant context
- Build a simple RAG pipeline

In this tutorial, you'll learn how to parse a complex PDF report with LlamaParse, load it into Snowflake, and build a Retrieval-Augmented Generation (RAG) workflow using Cortex Search on your Snowflake data.

### What we'll be building

Many LLMs don't natively orchestrate external "agent" workflows. With this workflow, you can expose Cortex Search capabilities as first-class tools in your data and AI stack.

We'll:
- Parse a PDF with LlamaParse
- Load the parsed data into Snowflake
- Split the text for search
- Create a Cortex Search service
- Retrieve relevant context
- Build a simple RAG pipeline for Q&A on your data

<!-- ------------------------ -->

### Prerequisites

* A LlamaCloud API key ([get one here](https://docs.cloud.llamaindex.ai/api_key))
* A Snowflake account ([sign up here](https://signup.snowflake.com/))
* Python **3.10+**
* Required Python packages: `llama-cloud`, `snowflake-snowpark-python`, `pandas`

<!-- ------------------------ -->

## 1. Set Keys and Import Libraries

Duration: 2

```python
import os
import nest_asyncio
nest_asyncio.apply()

# Set your API keys and Snowflake credentials
os.environ["LLAMA_CLOUD_API_KEY"] = "llx-..."  # Replace with your LlamaCloud API key
os.environ["SNOWFLAKE_ACCOUNT"] = "..."        # Use hyphens, not underscores
os.environ["SNOWFLAKE_USER"] = "..."
os.environ["SNOWFLAKE_PASSWORD"] = "..."
os.environ["SNOWFLAKE_ROLE"] = "..."
os.environ["SNOWFLAKE_WAREHOUSE"] = "..."
os.environ["SNOWFLAKE_DATABASE"] = "SEC_10KS"  # Use an existing database
os.environ["SNOWFLAKE_SCHEMA"] = "PUBLIC"
```

<!-- ------------------------ -->

## 2. Load Data

Duration: 2

Download a PDF (e.g., [Snowflake's latest 10K](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001640147/663fb935-b123-4bbb-8827-905bcbb8953c.pdf)) and save as `snowflake_2025_10k.pdf` in your working directory.

<!-- ------------------------ -->

## 3. Parse PDF with LlamaParse

Duration: 3

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

## 4. Convert LlamaIndex Documents to DataFrame

Duration: 2

```python
# Get markdown documents
markdown_documents = result.get_markdown_documents(split_by_page=False)

import pandas as pd

def documents_to_dataframe(documents):
    rows = []
    for doc in documents:
        row = {"ID": doc.id_}
        row.update(doc.metadata)
        row["text"] = getattr(doc.text_resource, "text", None)
        rows.append(row)
    return pd.DataFrame(rows)

documents_df = documents_to_dataframe(markdown_documents)
documents_df.head()
```

<!-- ------------------------ -->

## 5. Write DataFrame to Snowflake Table

Duration: 3

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

## 6. Split the Text for Search

Duration: 2

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

## 7. Create Cortex Search Service

Duration: 2

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

<!-- ------------------------ -->

## 8. Retrieve Context with Cortex Search

Duration: 2

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

## 9. Build a Simple RAG Pipeline

Duration: 3

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
<!-- ------------------------ -->

Duration: 1

Congratulations! You have parsed a PDF with LlamaParse, loaded it into Snowflake, indexed it with Cortex Search, and built a simple RAG pipeline for question answering on your data.

### What You Learned

* How to parse PDFs with LlamaParse
* How to load and split data in Snowflake
* How to create and use Cortex Search
* How to build a simple RAG pipeline for Q&A

### Related Resources

  * [LlamaParse (LlamaIndex)](https://docs.llamaindex.ai/en/stable/module_guides/loading/llamaparse.html)
  * [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
  * [Snowflake Python API](https://docs.snowflake.com/en/developer-guide/snowpark/python/index)
  * [LlamaCloud API Key](https://docs.cloud.llamaindex.ai/api_key)
