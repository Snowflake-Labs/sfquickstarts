author: Josh Reini
id: production_ready_rag_snowflake_trulens
summary: This is a guide for building a production-ready RAG with Snowflake and TruLens.
categories: Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, RAG, LLMs, TruLens, Snowflake

# Production-Ready RAG with TruLens and Snowflake Cortex

## Overview

Duration: 1

In this quickstart, we'll show how to build a RAG with the full snowflake stack including [Cortex LLM Functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions), [Cortex Search](https://github.com/Snowflake-Labs/cortex-search?tab=readme-ov-file), and [TruLens](https://www.trulens.org/) observability.

In addition, we'll show how to run TruLens feedback functions with Cortex as the [feedback provider](https://www.trulens.org/trulens_eval/api/provider/), and how to log TruLens traces and evaluation metrics to a Snowflake table.

Last, we'll show how to use [TruLens guardrails](https://www.trulens.org/trulens_eval/guardrails/) for filtering retrieved context and reducing hallucination.

## Setup

Duration: 2

For this quickstart, you will need your Snowflake credentials and a GitHub PAT Token ready. For example purposes, we assume they are set in a `.env` file that looks like this:

```
# Loading data from github
GITHUB_TOKEN=

# Snowflake details
SNOWFLAKE_USER=
SNOWFLAKE_USER_PASSWORD=
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_ROLE=
SNOWFLAKE_CORTEX_SEARCH_SERVICE=
```

First, we'll install the packages needed:

```python
pip install snowflake-snowpark-python
pip install notebook
pip install snowflake-ml-python
pip install trulens-eval
pip install snowflake-sqlalchemy
pip install llama-index
pip install llama-index-readers-github
pip install llama-index-embeddings-huggingface
```

Then we can load our credentials and set our Snowflake connection

```python
from dotenv import load_dotenv
from snowflake.snowpark.session import Session
import os

load_dotenv()

connection_details = {
  "account":  os.environ["SNOWFLAKE_ACCOUNT"],
  "user": os.environ["SNOWFLAKE_USER"],
  "password": os.environ["SNOWFLAKE_USER_PASSWORD"],
  "role": os.environ["SNOWFLAKE_ROLE"],
  "database": os.environ["SNOWFLAKE_DATABASE"],
  "schema": os.environ["SNOWFLAKE_SCHEMA"],
  "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"]
}

session = Session.builder.configs(connection_details).create()
```

## Using Cortex Complete

Duration: 3

With the session set, we have what need to call a Snowflake Cortex LLM:

```python
from snowflake.cortex import Complete

text = """
  The Snowflake company was co-founded by Thierry Cruanes, Marcin Zukowski,
  and Benoit Dageville in 2012 and is headquartered in Bozeman, Montana.
"""

print(Complete("mistral-large", "how do snowflakes get their unique patterns?"))
```

## Adding Data for Cortex Search

Duration: 12

Next, we'll turn to the retrieval component of our RAG and set up Cortex Search.

This requires three steps:

1. Read and preprocess unstructured documents.
2. Embed the cleaned documents with Arctic Embed.
3. Call the Cortex search service.

### Read and preprocess unstructured documents

For this example, we want to load Cortex Search with documentation from Github about a popular open-source library, Streamlit. To do so, we'll use a GitHub data loader available from LlamaHub.

Here we'll also expend some effort to clean up the text so we can get better search results.

```python
import nest_asyncio
nest_asyncio.apply()

from llama_index.readers.github import GithubRepositoryReader, GithubClient

github_token = os.environ["GITHUB_TOKEN"]
client = GithubClient(github_token=github_token, verbose=False)

reader = GithubRepositoryReader(
  github_client=github_client,
  owner="streamlit",
  repo="docs",
  use_parser=False,
  verbose=True,
  filter_directories=(
    ["content"],
    GithubRepositoryReader.FilterType.INCLUDE,
  ),
  filter_file_extensions=(
    [".md"],
    GithubRepositoryReader.FilterType.INCLUDE,
  )
)

documents = reader.load_data(branch="main")

import re

def clean_up_text(content: str) -> str:
  """
  Remove unwanted characters and patterns in text input.

  :param content: Text input.

  :return: Cleaned version of original text input.
  """

  # Fix hyphenated words broken by newline
  content = re.sub(r'(\w+)-\n(\w+)', r'\1\2', content)

  unwanted_patterns = ['---\nvisible: false','---', '#','slug:']
  for pattern in unwanted_patterns:
    content = re.sub(pattern, "", content)

  # Remove all slugs starting with a \ and stopping at the first space
  content = re.sub(r'\\slug: [^\s]*', '', content)

  # normalize whitespace
  content = re.sub(r'\s+', ' ', content)
  return content

cleaned_documents = []

for d in documents:
  cleaned_text = clean_up_text(d.text)
  d.text = cleaned_text
  cleaned_documents.append(d)
```

### Process the documents with Semantic Splitting

We'll use Snowflake's Arctic Embed model available from HuggingFace to embed the documents. We'll also use Llama-Index's `SemanticSplitterNodeParser` for processing.

```python
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser

embed_model = HuggingFaceEmbedding("Snowflake/snowflake-arctic-embed-m")

splitter = SemanticSplitterNodeParser(
  buffer_size=1, breakpoint_percentile_threshold=85, embed_model=embed_model
)
```

With the embed model and splitter, we can execute them in an ingestion pipeline

```python
from llama_index.core.ingestion import IngestionPipeline

cortex_search_pipeline = IngestionPipeline(
  transformations=[
    splitter,
  ],
)

results = cortex_search_pipeline.run(show_progress=True, documents=cleaned_documents)
```

### Load data to Cortex Search

Now that we've embedded our documents, we're ready to load them to Cortex Search.

Here we can use the same connection details as we set up for Cortex Complete.

```python
import os
import snowflake.connector
from tqdm.auto import tqdm

conn = snowflake.connector.connect(
  user=connection_details["user"],
  password=connection_details["password"],
  account=connection_details["account"],
  warehouse=connection_details["warehouse"],
  database=connection_details["database"],
  schema=connection_details["schema"]
)

conn.cursor().execute("CREATE OR REPLACE TABLE streamlit_docs(doc_text VARCHAR)")
for curr in tqdm(results):
  conn.cursor().execute("INSERT INTO streamlit_docs VALUES (%s)", curr.text)
```

## Calling the Cortex Search Service

Duration: 5

Here we'll create a `CortexSearchRetreiver` class to connect to our cortex search service and add the `retrieve` method that we can leverage for calling it.

```python
import os
from snowflake.core import Root
from typing import List

class CortexSearchRetriever:

    def __init__(self, session: Session, limit_to_retrieve: int = 4):
        self._session = session
        self._limit_to_retrieve = limit_to_retrieve

    def retrieve(self, query: str) -> List[str]:
        root = Root(self._session)
        cortex_search_service = (
        root
        .databases["JREINI_DB"]
        .schemas["TRULENS_DEMO_SCHEMA"]
        .cortex_search_services["TRULENS_DEMO_CORTEX_SEARCH_SERVICE"]
    )
        resp = cortex_search_service.search(
                query=query,
                columns=["doc_text"],
                limit=self._limit_to_retrieve,
            )

        if resp.results:
            return [curr["doc_text"] for curr in resp.results]
        else:
            return []
```

Once the retriever is created, we can test it out. Now that we have grounded access to the Streamlit docs, we can ask questions about using Streamlit, like "How do I launch a streamlit app".

```python
retriever = CortexSearchRetriever(session=session, limit_to_retrieve=4)

retrieved_context = retriever.retrieve(query="How do I launch a streamlit app?")

len(retrieved_context)
```

## Create a RAG with built-in observability

Duration: 5

Now that we've set up the components we need from Snowflake Cortex, we can build our RAG.

We'll do this by creating a custom python class with each the methods we need. We'll also add TruLens instrumentation with the `@instrument` decorator to our app.

The first thing we need to do however, is to set the database connection where we'll log the traces and evaluation results from our application. This way we have a stored record that we can use to understand the app's performance. This is done when initializing `Tru`.

```python
from trulens_eval import Tru

db_url = "snowflake://{user}:{password}@{account}/{dbname}/{schema}?warehouse={warehouse}&role={role}".format(
  user=os.environ["SNOWFLAKE_USER"],
  account=os.environ["SNOWFLAKE_ACCOUNT"],
  password=os.environ["SNOWFLAKE_USER_PASSWORD"],
  dbname=os.environ["SNOWFLAKE_DATABASE"],
  schema=os.environ["SNOWFLAKE_SCHEMA"],
  warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
  role=os.environ["SNOWFLAKE_ROLE"],
)

tru = Tru(database_url=db_url)
```

Now we can construct the RAG.

```python
from trulens_eval.tru_custom_app import instrument

class RAG_from_scratch:

  def __init__(self):
    self.retriever = CortexSearchRetriever(session=session, limit_to_retrieve=4)

  @instrument
  def retrieve_context(self, query: str) -> list:
    """
    Retrieve relevant text from vector store.
    """
    return self.retriever.retrieve(query)

  @instrument
  def generate_completion(self, query: str, context_str: list) -> str:
    """
    Generate answer from context.
    """
    prompt = f"""
    'You are an expert assistance extracting information from context provided.
    Answer the question based on the context. Be concise and do not hallucinate.
    If you don´t have the information just say so.
    Context: {context_str}
    Question:
    {query}
    Answer: '
    """
    return Complete("mistral-large", query)

  @instrument
  def query(self, query: str) -> str:
    context_str = self.retrieve_context(query)
    return self.generate_completion(query, context_str)

rag = RAG_from_scratch()
```

## Add feedback functions

Duration: 5

After constructing the RAG, we can set up the feedback functions we want to use to evaluate the RAG.

Here, we'll use the [RAG Triad](https://www.trulens.org/trulens_eval/getting_started/core_concepts/rag_triad/). The RAG triad is made up of 3 evaluations along each edge of the RAG architecture: context relevance, groundedness and answer relevance.

![RAG Triad](./assets/RAG_Triad.jpg)

Satisfactory evaluations on each provides us confidence that our LLM app is free from hallucination.

We will also use [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685) evaluations, using Mistral Large on [Snowflake Cortex](https://www.trulens.org/trulens_eval/api/provider/cortex/) as the LLM.

```python
from trulens_eval.feedback.provider.cortex import Cortex
from trulens_eval.feedback import Feedback
from trulens_eval import Select
import numpy as np

provider = Cortex("mistral-large")

f_groundedness = (
  Feedback(
  provider.groundedness_measure_with_cot_reasons, name="Groundedness")
  .on(Select.RecordCalls.retrieve_context.rets[:].collect())
  .on_output()
)

f_context_relevance = (
  Feedback(
  provider.context_relevance,
  name="Context Relevance")
  .on_input()
  .on(Select.RecordCalls.retrieve_context.rets[:])
  .aggregate(np.mean)
)

f_answer_relevance = (
  Feedback(
  provider.relevance,
  name="Answer Relevance")
  .on_input()
  .on_output()
  .aggregate(np.mean)
)
```

After defining the feedback functions to use, we can just add them to the application along with giving the application an ID.

```python
from trulens_eval import TruCustomApp
tru_rag = TruCustomApp(rag,
  app_id = 'RAG v1',
  feedbacks = [f_groundedness, f_answer_relevance, f_context_relevance])
```

## Test the application and observe performance

Duration: 3

Now that the application is ready, we can run it on a test set of questions about streamlit to measure its performance.

```python
prompts = [
  "How do I launch a streamlit app?",
  "How can I capture the state of my session in streamlit?",
  "How do I install streamlit?",
  "How do I change the background color of a streamlit app?",
  "What's the advantage of using a streamlit form?",
  "What are some ways I should use checkboxes?",
  "How can I conserve space and hide away content?",
  "Can you recommend some resources for learning Streamlit?",
  "What are some common use cases for Streamlit?",
  "How can I deploy a streamlit app on the cloud?",
  "How do I add a logo to streamlit?",
  "What is the best way to deploy a Streamlit app?",
  "How should I use a streamlit toggle?",
  "How do I add new pages to my streamlit app?",
  "How do I write a dataframe to display in my dashboard?",
  "Can I plot a map in streamlit? If so, how?",
  "How do vector stores enable efficient similarity search?",
]
```

```python
with tru_rag as recording:
  for prompt in prompts:
    rag.query(prompt)

tru.get_leaderboard()
```

## Use Guardrails

Duration: 7

In addition to making informed iteration, we can also directly use feedback results as guardrails at inference time. In particular, here we show how to use the context relevance score as a guardrail to filter out irrelevant context before it gets passed to the LLM. This both reduces hallucination and improves efficiency.

![Context Filter Guardrails](./assets/guardrail_context_filtering.png)

To do so, we'll rebuild our RAG using the `@context-filter` decorator on the method we want to filter, and pass in the feedback function and threshold to use for guardrailing.

```python
from trulens_eval.guardrails.base import context_filter

# note: feedback function used for guardrail must only return a score, not also reasons
f_context_relevance_score = (
  Feedback(provider.context_relevance, name = "Context Relevance")
)

class filtered_RAG_from_scratch:

  def __init__(self):
    self.retriever = CortexSearchRetriever(session=session, limit_to_retrieve=4)

  @instrument
  @context_filter(f_context_relevance_score, 0.75, keyword_for_prompt="query")
  def retrieve_context(self, query: str) -> list:
    """
    Retrieve relevant text from vector store.
    """
    return self.retriever.retrieve(query)

  @instrument
  def generate_completion(self, query: str, context_str: list) -> str:
    """
    Generate answer from context.
    """
    prompt = f"""
    'You are an expert assistance extracting information from context provided.
    Answer the question based on the context. Be concise and do not hallucinate.
    If you don´t have the information just say so.
    Context: {context_str}
    Question:
    {question}
    Answer: '
    """
    return Complete("mistral-large", query)

  @instrument
  def query(self, query: str) -> str:
    context_str = self.retrieve_context(query=query)
    return self.generate_completion(query=query, context_str=context_str)

filtered_rag = filtered_RAG_from_scratch()
```

## Test the new app version

Duration: 7

We can combine the new version of our app with the feedback functions we already defined

```python
from trulens_eval import TruCustomApp
tru_rag = TruCustomApp(rag,
  app_id = 'RAG v1',
  feedbacks = [f_groundedness, f_answer_relevance, f_context_relevance])
```

Then we run it on a test set of questions about streamlit to measure its performance.

```python
prompts = [
  "How do I launch a streamlit app?",
  "How can I capture the state of my session in streamlit?",
  "How do I install streamlit?",
  "How do I change the background color of a streamlit app?",
  "What's the advantage of using a streamlit form?",
  "What are some ways I should use checkboxes?",
  "How can I conserve space and hide away content?",
  "Can you recommend some resources for learning Streamlit?",
  "What are some common use cases for Streamlit?",
  "How can I deploy a streamlit app on the cloud?",
  "How do I add a logo to streamlit?",
  "What is the best way to deploy a Streamlit app?",
  "How should I use a streamlit toggle?",
  "How do I add new pages to my streamlit app?",
  "How do I write a dataframe to display in my dashboard?",
  "Can I plot a map in streamlit? If so, how?",
  "How do vector stores enable efficient similarity search?",
]
```

Last, we can use `get_leaderboard()` to see the performance of the two application versions head to head.

```python
with tru_rag as recording:
  for prompt in prompts:
    rag.query(prompt)

tru.get_leaderboard()
```

## Conclusion and resources

Duration: 1

### What You Learned

- In this quickstart, we learned build a RAG with Cortex Search and Cortex LLM Fucntions.
- Additionally, we learned how to set up TruLens instrumentation and create a custom RAG class with TruLens feedback providers.
- Finally, we learned how to use feedback results as guardrails to improve a RAG application so it can be production-ready.

### Related Resources

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/cortex.html)
- [TruLens Documentation](https://trulens.org/)
- [TruLens GitHub Repository](https://github.com/truera/trulens)
