author: Josh Reini
id: build-evaluate-rag-langchain-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/model-development
language: en
summary: Build and evaluate RAG applications with LangChain and Snowflake for document Q&A, knowledge retrieval, and chatbot development.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Build and Evaluate RAG with LangChain and Snowflake
<!-- ------------------------ -->
## Overview


Retrieval-Augmented Generation (RAG) has become a cornerstone technique for enhancing Large Language Models (LLMs) with domain-specific knowledge. In this guide, you'll learn how to build a RAG application using the `langchain-snowflake` package with `SnowflakeCortexSearchRetriever` and `ChatSnowflake`. You'll then evaluate your RAG's performance using TruLens and Snowflake's AI Observability features.

By combining Snowflake's data platform capabilities with LangChain's flexible framework, you'll create a powerful RAG system that can answer questions based on your own data.

### What You'll Learn

- How to set up a Snowflake environment for RAG applications
- How to create a retriever using Snowflake Cortex Search
- How to build a complete RAG chain with LangChain and Snowflake
- How to evaluate RAG performance using TruLens
- How to analyze evaluation results in Snowflake

### What You'll Build

A complete RAG application that can answer questions about sales conversations by retrieving relevant information from a knowledge base and generating contextually appropriate responses. You'll also implement evaluation metrics to measure the quality of your RAG system.

### What You'll Need

- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- A Snowflake account with Cortex features enabled
- Valid Snowflake credentials
- Python 3.8+

<!-- ------------------------ -->
## Setup


Firstly, to follow along with this quickstart, you can click on [build-and-evaluate-rag-with-langchain-and-snowflake.ipynb](https://github.com/Snowflake-Labs/sfguide-build-and-evaluate-rag-with-langchain-and-snowflake/blob/main/build-and-evaluate-rag-with-langchain-and-snowflake.ipynb) to download the Notebook from GitHub.

### Environment Configuration

Before we can build our RAG application, we need to prepare our Snowflake environment with data and search capabilities. This involves:

1. **Loading sample data**: We'll use sales conversation transcripts as our knowledge base
2. **Creating a Cortex Search Service**: This will index our data and enable semantic search

Run the SQL commands in the [setup.sql](https://github.com/Snowflake-Labs/sfguide-build-and-evaluate-rag-with-langchain-and-snowflake/blob/main/setup.sql) file in your Snowflake environment to:

- Create the necessary database, schema, and tables
- Load sample sales conversation data
- Set up the Cortex Search Service with appropriate indexing configuration
- Enable cross-region inference for access to Claude 4

### Installing Required Packages

Notebooks come pre-installed with common Python libraries for data science and machine learning. For this guide, we'll need to install additional packages specific to our RAG implementation:

```python
%pip install --quiet -U langchain-core langchain-snowflake trulens-core trulens-providers-cortex trulens-connectors-snowflake trulens-apps-langchain
```

> IMPORTANT:
> - Make sure your Snowflake account has Cortex features enabled
> - You'll need appropriate permissions to create databases, schemas, and search services

<!-- ------------------------ -->
## Creating a Snowflake Session


### Setting Up Environment Variables

To securely connect to Snowflake, we'll configure our credentials as environment variables. This approach keeps sensitive information out of your code and follows security best practices.

```python
import os

os.environ["SNOWFLAKE_ACCOUNT"] = "your_account_identifier"
os.environ["SNOWFLAKE_USER"] = "your_username"
os.environ["SNOWFLAKE_PASSWORD"] = "your_password"
os.environ["SNOWFLAKE_WAREHOUSE"] = "SALES_INTELLIGENCE_WH"
os.environ["SNOWFLAKE_DATABASE"] = "SALES_INTELLIGENCE"
os.environ["SNOWFLAKE_SCHEMA"] = "DATA"
```

### Creating a Snowflake Session

Now we'll create a session that will be used by both the retriever and LLM components:

```python
from langchain_snowflake import create_session_from_env

session = create_session_from_env()
```

This session will handle authentication and connection management for all Snowflake operations in our RAG application.

<!-- ------------------------ -->
## Building the Retriever


### Creating a Cortex Search Retriever

The retriever is responsible for finding relevant documents from our knowledge base. We'll use `SnowflakeCortexSearchRetriever` which leverages Snowflake's Cortex Search capabilities:

```python
from langchain_snowflake import SnowflakeCortexSearchRetriever

# Replace with your actual Cortex Search service
CORTEX_SEARCH_SERVICE = "SALES_INTELLIGENCE.DATA.SALES_CONVERSATION_SEARCH"

retriever = SnowflakeCortexSearchRetriever(
    session=session,
    service_name=CORTEX_SEARCH_SERVICE,
    k=3,  # Number of documents to retrieve
    auto_format_for_rag=True,  # Automatic document formatting
    content_field="TRANSCRIPT_TEXT",  # Extract content from this metadata field
    join_separator="\n\n",  # Separator used for multiple documents
    fallback_to_page_content=True  # Fall back to page_content if metadata field is empty
)
```

### Testing the Retriever

Let's test our retriever to make sure it's working correctly:

```python
import textwrap

docs = retriever.get_relevant_documents("What happened in our last sales conversation with DataDriven?")

for doc in docs:
    wrapped_text = textwrap.fill(doc.page_content, width=80)
    print(f"{wrapped_text}\n{'-' * 120}")
```

The retriever should return the most relevant documents from our sales conversations that match the query about DataDriven.

<!-- ------------------------ -->
## Building the RAG Chain


### Creating the LLM Component

Now we'll set up the language model component using Snowflake's Cortex LLM capabilities:

```python
from langchain_snowflake import ChatSnowflake

# Initialize chat model
llm = ChatSnowflake(
    session=session, 
    model="claude-4-sonnet", 
    temperature=0.1, 
    max_tokens=1000
)
```

### Creating the RAG Prompt Template

We'll create a prompt template that instructs the model to answer questions based on the retrieved context:

```python
from langchain_core.prompts import ChatPromptTemplate

# Create RAG prompt template
rag_prompt = ChatPromptTemplate.from_template("""
Answer the question based on the following context from Snowflake Cortex Search:

Context:
{context}

Question: {question}

Provide a comprehensive answer based on the retrieved context. If the context doesn't contain enough information, say so clearly.
""")
```

### Building the Complete RAG Chain

Now we'll chain everything together using LangChain's LCEL (LangChain Expression Language):

```python
from langchain_core.runnables import RunnablePassthrough

# Build RAG chain
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()} | rag_prompt | llm
)
```

### Testing the RAG Chain

Let's test our RAG chain with a sample question:

```python
response = rag_chain.invoke("What happened in our last sales conversation with DataDriven?")
print(f"{response.content}")
```

The RAG chain should retrieve relevant context about DataDriven from our knowledge base and generate a comprehensive answer based on that context.

<!-- ------------------------ -->
## Evaluating RAG Performance


### Setting Up TruLens with Snowflake

To evaluate our RAG application, we'll use TruLens with Snowflake integration:

```python
from trulens.apps.langchain import TruChain
from trulens.connectors.snowflake import SnowflakeConnector

tru_snowflake_connector = SnowflakeConnector(snowpark_session=session)

app_name = "sales_assistance_rag"
app_version = "cortex_search"

tru_rag = TruChain(
    rag_chain,
    app_name=app_name,
    app_version=app_version,
    connector=tru_snowflake_connector,
    main_method_name="invoke"
)
```

### Creating an Evaluation Run

We'll create a run configuration and dataset for our evaluation:

```python
import pandas as pd
from trulens.core.run import Run, RunConfig
from datetime import datetime

# Create a dataset of test queries
queries = [
    "What happened in our last sales conversation with DataDriven?",
    "What is the status of the deal with DataDriven?",
    "What is the status of the deal with HealthTech?"
]

queries_df = pd.DataFrame(queries, columns=["query"])

# Create a run configuration
run_name = f"experiment_1_{datetime.now().strftime('%Y%m%d%H%M%S')}"

run_config = RunConfig(
    run_name=run_name,
    dataset_name="sales_queries",
    source_type="DATAFRAME",
    dataset_spec={
        "input": "query",
    },
)

# Create and start the run
run: Run = tru_rag.add_run(run_config=run_config)
run.start(input_df=queries_df)
```

### Computing Evaluation Metrics

We'll compute several key metrics to evaluate our RAG system:

```python
import time

# Wait for all invocations to complete
while run.get_status() != "INVOCATION_COMPLETED":
    time.sleep(3)

# Compute metrics
run.compute_metrics([
    "answer_relevance",
    "context_relevance",
    "groundedness",
])
```

These metrics will help us understand:

- How well the answer addresses the user query (answer_relevance)
- How relevant the retrieved context is to the query (context_relevance)
- How well the answer is supported by the retrieved context (groundedness)

### Viewing Evaluation Results

You can view the evaluation results in Snowflake's AI Observability UI: <a href="https://app.snowflake.com/_deeplink/#/ai-evaluations/databases/SALES_INTELLIGENCE/schemas/DATA/applications/SALES_ASSISTANCE_RAG?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-build-and-evaluate-rag-with-langchain-and-snowflake&utm_cta=developer-guides-deeplink" class="_deeplink">Open in Snowflake AI Observability</a>

1. Navigate to the Snowflake AI Observability page
2. Filter by your app_name, app_version, and run_name
3. Inspect individual invocations and their metrics
4. Identify areas for improvement in your RAG system

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You've successfully built and evaluated a complete RAG application using LangChain and Snowflake. You've learned how to create a retriever using Snowflake Cortex Search, build a RAG chain with LangChain, and evaluate its performance using TruLens and Snowflake's AI Observability features.

This foundation can be extended in numerous ways, such as experimenting with different LLM models, adjusting retrieval parameters, adding conversation memory, or building a user interface with Streamlit.

### What You Learned

- Created a Snowflake environment for RAG applications
- Built a retriever using Snowflake Cortex Search
- Constructed a complete RAG chain with LangChain
- Evaluated RAG performance using TruLens
- Analyzed evaluation results in Snowflake

### Related Resources

Documentation:

- [Getting Started with langchain-snowflake](https://github.com/langchain-ai/langchain-snowflake/blob/main/libs/snowflake/docs/getting_started.ipynb)
- [Advanced Patterns with langchain-snowflake](https://github.com/langchain-ai/langchain-snowflake/blob/main/libs/snowflake/docs/advanced_patterns.ipynb)
- [Snowflake AI Observability](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)

Happy building with LangChain and Snowflake!

<!-- Example of embedding images in the article:
![image](assets/img01.PNG)
-->
