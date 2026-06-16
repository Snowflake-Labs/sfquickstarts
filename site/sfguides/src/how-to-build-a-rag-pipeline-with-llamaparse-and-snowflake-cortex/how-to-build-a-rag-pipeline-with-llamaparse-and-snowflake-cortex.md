author: Josh Reini
id: how-to-build-a-rag-pipeline-with-llamaparse-and-snowflake-cortex
summary: Quickly build a RAG pipeline to query unstructured documents like PDFs, slide decks, and manuals. Use cases include Q&A over contracts, financial reports, and compliance docs, internal copilots for onboarding and support, and retrieval over technical
categories: snowflake-site:taxonomy/solution-center/certification/partner-solution
environments: web
language: en
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
heroButtonOverrideLabel: View Quickstart
heroButtonOverrideLink: https://www.snowflake.com/en/developers/guides/getting-started-with-llamaparse-and-cortex-search/

# How to Build a RAG Pipeline with LlamaParse and Snowflake Cortex
<!-- ------------------------ -->
## Overview

Quickly build a RAG pipeline to query unstructured documents like PDFs, slide decks, and manuals. Use cases include Q&A over contracts, financial reports, and compliance docs, internal copilots for onboarding and support, and retrieval over technical specs or architecture guides, all powered by Snowflake Cortex and LlamaParse.

This guide walks you through building an end-to-end RAG workflow using LlamaParse, a genAI-native parser from LlamaIndex, and Snowflake Cortex, which provides built-in tools for text splitting, hybrid search, and LLM-powered generation.

LlamaParse is designed for LLM workflows and offers:

* Accurate table extraction
* Natural language prompts for structured output
* JSON and image extraction modes
* Support for 10+ file types (PDF, PPTX, DOCX, HTML, XML, etc.)
* Multilingual support

It ensures clean, structured data, ready for downstream tasks like RAG, semantic search, and agents.

Together, LlamaParse and Cortex offer a seamless path from raw documents to intelligent, production-ready RAG workflows, all within your Snowflake environment.

This solution was created, tested, and verified by a member of the Snowflake Partner Network and meets compatibility requirements with Snowflake instances as of date of publication.

<!-- ------------------------ -->
## Code Example

```sql
from llama_cloud_services import LlamaParse

parser = LlamaParse(
num_workers=4,
verbose=True,
language="en",
)

result = parser.parse("./snowflake_2025_10k.pdf")

# Get markdown documents
markdown_documents = result.get_markdown_documents(split_by_page=False)

import pandas as pd

# fields that matter only to vector/RAG helpers – we don't need them here
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
omitting vector-store helper fields that aren't needed for retrieval.
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

Now that the Cortex Search Service is created, we can create a python class to retrieve relevant chunks from the service.

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
## Get Started

- [view quickstart](https://quickstarts.snowflake.com/guide/getting-started-with-llamaparse-and-cortex-search)
- [fork the repo](https://github.com/sfc-gh-jreini/llama-parse-cortex-search/blob/main/llama-cloud-snowflake.ipynb)
