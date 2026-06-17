author: Josh Reini, Elliot Botwick
id: compare-and-evaluate-chunking-strategies
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Compare document chunking strategies with Snowflake AI Observability for optimal RAG performance, retrieval accuracy, and embeddings.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Compare and Evaluate Chunking Strategies

<!-- ------------------------ -->
## Overview


Chunking strategies play a critical role in the effectiveness of Retrieval Augmented Generation (RAG) applications. The way you split your documents can significantly impact the quality of responses your AI system provides. In this guide, you'll learn how to systematically compare different chunking approaches using Snowflake's AI Observability features.

You'll build a complete RAG application that analyzes SEC 10-K filings, implementing two different chunking strategies:

1. Basic paragraph-based chunking
2. Context-enhanced chunking with document summaries

By the end, you'll have quantitative metrics to determine which approach delivers better results for your specific use case.

### What You'll Learn

- How to parse and process PDF documents in Snowflake
- Techniques for implementing different text chunking strategies
- Methods to create and compare vector search services
- How to use AI Observability to evaluate RAG performance
- Ways to make data-driven decisions about chunking approaches

### What You'll Build

A complete RAG application that can answer questions about SEC 10-K filings, with tools to measure and compare the performance of different chunking strategies.

### What You'll Need

- Access to a [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides)
- Basic familiarity with SQL and Python
- Understanding of RAG concepts

<!-- ------------------------ -->
## Setup


### Database and Schema Setup

Run [setup.sql](https://github.com/Snowflake-Labs/sfguide-compare-and-evaluate-chunking-strategies/blob/main/setup.sql) to create the neccessary databases, schemas, warehouses and roles.

### Notebook Configuration

Firstly, to follow along with this quickstart, you can download the Notebook from the [GitHub repository](https://github.com/Snowflake-Labs/sfguide-compare-and-evaluate-chunking-strategies) and then create a new Snowflake notebook by importing the notebook file in Snowsight into the `CHUNKING_EVALUATION` database and `CHUNKING_EVALUATION` schema.

In your Snowflake notebook, install the following python packages from the Snowflake conda channel:

- snowflake-ml-python
- snowflake.core
- trulens-core
- trulens-providers-cortex
- trulens-connectors-snowflake

Then, you can get the active snowpark session and turn on TruLens OpenTelemetry tracing.

```python
from snowflake.snowpark.context import get_active_session
session = get_active_session()

# Enable OpenTelemetry tracing for AI Observability
import os
os.environ["TRULENS_OTEL_TRACING"] = "1"
```

### Data Preparation

Download the PDF documents from the [data folder in the GitHub repository](https://github.com/Snowflake-Labs/sfguide-compare-and-evaluate-chunking-strategies/tree/main/data) and upload them to the stage `@CHUNKING_EVALUATION.CHUNKING_EVALUATION.PDF_10KS`.

> IMPORTANT:
> - Make sure to upload the PDF files to the correct stage
> - The PDFs contain SEC 10-K filings which will be used throughout this tutorial

<!-- ------------------------ -->
## Parse Documents


In this section, we'll extract text from the PDF documents using Snowflake's AI_PARSE_DOCUMENT function. This function can handle complex document layouts, including tables and columns.

### Create a Table for Parsed Text

First, let's define our database and schema variables:

```python
DB_NAME = 'CHUNKING_EVALUATION'
DOC_SCHEMA_NAME = 'DOCS'
TEXT_SCHEMA_NAME = 'PARSED_DATA'
```

Now, create a table to store the parsed text:

```sql
-- Create a table to hold the extracted text from the PDF files
CREATE TABLE CHUNKING_EVALUATION.PARSED_DATA.PARSED_TEXT (
  relative_path VARCHAR(500), 
  raw_text VARIANT
) IF NOT EXISTS;
```

### Extract Text from PDFs

Next, we'll use the PARSE_DOCUMENT function to extract text from each PDF file:

```sql
INSERT INTO CHUNKING_EVALUATION.PARSED_DATA.PARSED_TEXT (relative_path, raw_text)
WITH pdf_files AS (
    SELECT DISTINCT
        METADATA$FILENAME AS relative_path
    FROM @CHUNKING_EVALUATION.DOCS.PDF_10KS
    WHERE METADATA$FILENAME ILIKE '%.pdf'
      -- Exclude files that have already been parsed
      AND METADATA$FILENAME NOT IN (SELECT relative_path FROM CHUNKING_EVALUATION.PARSED_DATA.PARSED_TEXT)
)
SELECT 
    relative_path,
    SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
        '@CHUNKING_EVALUATION.DOCS.PDF_10KS',  -- Your stage name
        relative_path,  -- File path
        {'mode': 'layout'}  -- Using layout mode to preserve document structure
    ) AS raw_text
FROM pdf_files;
```

The 'layout' mode preserves the document's structure, including tables and formatting, which is important for financial documents like 10-K filings.

### Inspect the Parsed Documents

Let's check our parsed documents and count the tokens in each:

```sql
-- Inspect the results and count the tokens for each document
SELECT *, SNOWFLAKE.CORTEX.COUNT_TOKENS('mistral-7b', RAW_TEXT) as token_count
FROM CHUNKING_EVALUATION.PARSED_DATA.PARSED_TEXT;
```

This gives us a sense of the document sizes and helps us plan our chunking strategy.

<!-- ------------------------ -->
## Implement Chunking Strategies


Now we'll implement two different chunking strategies to compare their effectiveness.

### Strategy 1: Basic Paragraph Chunking

First, let's create chunks based on paragraph separators:

```sql
-- Chunk the text based on paragraph separators
CREATE OR REPLACE TABLE CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS AS
WITH text_chunks AS (
    SELECT
        relative_path,
        SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
            raw_text:content::STRING,  -- Extract the 'content' field from the JSON
            'markdown', -- Format type
            2000,       -- Chunk size (in tokens)
            100,        -- Overlap size
            ['\n\n']    -- Paragraph separators
        ) AS chunks
    FROM CHUNKING_EVALUATION.PARSED_DATA.PARSED_TEXT
)
SELECT
    relative_path,
    c.value AS chunk  -- Extract each chunk of the parsed text
FROM text_chunks,
LATERAL FLATTEN(INPUT => chunks) c;
```

This approach splits the text at paragraph boundaries, creating chunks of approximately 2000 tokens with a 100-token overlap between consecutive chunks.

### Strategy 2: Context-Enhanced Chunking

For our second strategy, we'll enhance each chunk with document-level context by adding a document summary using `AI_SUMMARIZE_AGG`:

```sql
-- Add the DOC_SUMMARY column if it doesn't exist
ALTER TABLE CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS
    ADD COLUMN IF NOT EXISTS DOC_SUMMARY VARCHAR(5000);

-- Generate document summaries
UPDATE CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS AS tgt
SET DOC_SUMMARY = src.DOC_SUMMARY
FROM (
    SELECT 
        RELATIVE_PATH,
        AI_SUMMARIZE_AGG(CHUNK) AS DOC_SUMMARY
    FROM CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS
    GROUP BY RELATIVE_PATH
) AS src
WHERE tgt.RELATIVE_PATH = src.RELATIVE_PATH
  AND tgt.DOC_SUMMARY IS NULL;

-- Create combined chunks with summary context
ALTER TABLE CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS 
ADD COLUMN IF NOT EXISTS CHUNK_WITH_SUMMARY VARCHAR;

UPDATE CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS
  SET CHUNK_WITH_SUMMARY = DOC_SUMMARY || '\n\n' || CHUNK;
```

This strategy prepends each chunk with a summary of the entire document, providing additional context that might help the model understand the content better.

<!-- ------------------------ -->
## Create Search Services


Now we'll create two Cortex Search services, one for each chunking strategy, to enable vector search capabilities.

### Basic Chunk Search Service

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE CHUNKING_EVALUATION.PARSED_DATA.SEC_CHUNK_RETRIEVAL
  ON SEARCH_COL
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
AS (
  SELECT
    RELATIVE_PATH,
    CHUNK::STRING AS SEARCH_COL,
  FROM CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS
);
```

### Context-Enhanced Search Service

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE CHUNKING_EVALUATION.PARSED_DATA.SEC_CONTEXTUAL_CHUNK_RETRIEVAL
  ON SEARCH_COL
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
AS (
  SELECT
    RELATIVE_PATH,
    CHUNK,
    CHUNK_WITH_SUMMARY::STRING AS SEARCH_COL
  FROM CHUNKING_EVALUATION.PARSED_DATA.PARAGRAPH_CHUNKS
);
```

Both services use the same embedding model but index different content - one uses basic chunks while the other uses chunks enhanced with document summaries.

### Test the Search Services

Let's test our search services to make sure they're working correctly:

```python
# Query the basic search service
from snowflake.snowpark import Session
from snowflake.core import Root
root = Root(session)

sec_search_service = (root
  .databases[DB_NAME]
  .schemas[TEXT_SCHEMA_NAME]
  .cortex_search_services['SEC_CHUNK_RETRIEVAL']
)

resp = sec_search_service.search(
  query="What was under armour's net sales?",
  columns=['SEARCH_COL'],
  limit=3
)
results = resp.results
results
```

```python
# Query the contextual search service
sec_contextual_search_service = (root
  .databases[DB_NAME]
  .schemas[TEXT_SCHEMA_NAME]
  .cortex_search_services['SEC_CONTEXTUAL_CHUNK_RETRIEVAL']
)

resp = sec_contextual_search_service.search(
  query="What was zscalar's net sales?",
  columns=['SEARCH_COL'],
  limit=3
)
results = resp.results
results
```

These tests help us verify that both search services are operational and returning relevant results.

<!-- ------------------------ -->
## Build RAG Applications


Now we'll build two RAG applications, one for each chunking strategy, using the search services we created.

### Define the RAG Class

First, let's define a RAG class that we can use for both versions:

```python
from snowflake.cortex import complete
from trulens.core.otel.instrument import instrument
from trulens.otel.semconv.trace import SpanAttributes

class RAG:

    def __init__(self, search_service):
        self.search_service = search_service

    @instrument(
        span_type=SpanAttributes.SpanType.RETRIEVAL,
        attributes={
            SpanAttributes.RETRIEVAL.QUERY_TEXT: "query",
            SpanAttributes.RETRIEVAL.RETRIEVED_CONTEXTS: "return",
            }
    )
    def retrieve_context(self, query: str) -> list:
        """
        Retrieve relevant text from vector store.
        """
        
        response = self.search_service.search(
          query=query,
          columns=['SEARCH_COL'],
          limit=4
        )

        if response.results:
            return [curr["SEARCH_COL"] for curr in response.results]
        else:
            return []


    @instrument(
        span_type=SpanAttributes.SpanType.GENERATION)
    def generate_completion(self, query: str, context_list: list) -> str:
        """
        Generate answer from context.
        """
        prompt = f"""
          You are an expert assistant extracting information from context provided.
          Answer the question as concisely as possible without any preface.
          Context: {context_list}
          Question:
          {query}
          Answer:
        """
        response = complete("claude-4-sonnet", prompt)
        return response

    @instrument(
        span_type=SpanAttributes.SpanType.RECORD_ROOT, 
        attributes={
            SpanAttributes.RECORD_ROOT.INPUT: "query",
            SpanAttributes.RECORD_ROOT.OUTPUT: "return",
        })
    def query(self, query: str) -> str:
        context_str = self.retrieve_context(query)
        return self.generate_completion(query, context_str)
```

### Create RAG Instances

Now, let's create two instances of our RAG class, one for each search service:

```python
rag = RAG(search_service = sec_search_service)
contextual_rag = RAG(search_service = sec_contextual_search_service)
```

The `@instrument` decorators in our RAG class enable AI Observability, which will help us track and evaluate the performance of our RAG applications.

<!-- ------------------------ -->
## Set Up AI Observability


Now we'll set up AI Observability to compare the performance of our two RAG applications.

### Connect to Snowflake

First, let's establish a connection to Snowflake for AI Observability:

```python
from trulens.apps.app import TruApp
from trulens.connectors.snowflake import SnowflakeConnector

tru_snowflake_connector = SnowflakeConnector(snowpark_session=session)
```

### Register RAG Applications

Next, we'll register our two RAG applications with AI Observability:

```python
app_name = "sec_10k_chat_app"

base_tru_recorder = TruApp(
        rag,
        app_name=app_name,
        app_version="base",
        connector=tru_snowflake_connector,
        main_method_name="query"
    )

contextual_tru_recorder = TruApp(
        contextual_rag,
        app_name=app_name,
        app_version="contextual chunks",
        connector=tru_snowflake_connector,
        main_method_name="query"
    )
```

This registration allows AI Observability to track and compare the performance of our two RAG versions.

<!-- ------------------------ -->
## Create Test Dataset


To evaluate our RAG applications, we need a test dataset with questions and ground truth answers.

```sql
CREATE OR REPLACE TABLE SEC_FILINGS_QA (
  COMPANY_NAME        STRING,
  QUESTION            STRING,
  GROUND_TRUTH_ANSWER STRING
);

INSERT INTO SEC_FILINGS_QA
  (COMPANY_NAME, QUESTION, GROUND_TRUTH_ANSWER)
VALUES
  (
    'Autodesk, Inc.',
    'In Autodesk's Form 10-K covering fiscal year 2024, what amount of Remaining Performance Obligations (RPO) was reported as of the close of the fiscal year on January 31, 2024?',
    '$6.11 billion'
  ),
  (
    'IQVIA Holdings Inc.',
    'According to IQVIA's most recent annual 10-K, what was the approximate total number of employees worldwide at the end of the reporting period?',
    'IQVIA has approximately 87,000 employees.'
  ),
  (
    'Alcoa Corporation',
    'Within Alcoa's 2022 10-K, how many thousand metric tons of alumina shipments to third parties were disclosed for the six months ending June 30, 2022?',
    '4,715 kmt'
  ),
  (
    'Zscaler, Inc.',
    'As reported in Zscaler's 2024 10-K, what was the total deferred revenue recorded at the fiscal year-end date of July 31, 2024?',
    '$1,895.0 million'
  ),
  (
    '3M Company',
    'In 3M's discussion of environmental litigation matters in its 2018 Form 10-K, what was the pre-tax amount recorded in connection with the Minnesota settlement over PFAS?',
    '$897 million'
  ),
  (
    'Under Armour, Inc.',
    'Looking at Under Armour's 2020 10-K, what net revenue and cost of goods sold figures were reported for the three-month period ending June 30, 2020?',
    'Net revenue: $707,640 thousand - Cost of goods sold: $358,471 thousand'
  ),
  (
    'Packaging Corporation of America',
    'According to PCA's 2019 annual 10-K disclosures, what was the final purchase price paid to acquire the assets of Englander?',
    '$57.7 milion'
  ),
  (
    'Spectrum Brands Holdings',
    'In Spectrum's 2022 10-K, which specific appliances and cookware business acquisition was highlighted in the notes to the financial statements?',
    'Tristar Business'
  ),
  (
    'Spectrum Brands Holdings',
    'Per Spectrum's most recent 10-K description of its operating structure, what are the principal business segments reported?',
    'GPC (Global Pet Care), H&G (Home & Garden), and HPC (Home & Personal Care)'
  ),
  (
    'Southwestern Energy Company',
    'In the 2018 10-K, Southwestern Energy reported the divestiture of its Arkansas subsidiaries — which buyer purchased them and at what agreed price?',
    'Flywheel Energy Operating LLC, for a price of $1,650 million.'
  );
```

This dataset contains specific questions about information in the 10-K filings, along with the correct answers.

<!-- ------------------------ -->
## Run Evaluations


Now we'll create and run evaluations to compare our two RAG applications.

### Configure Evaluation Runs

First, let's configure the evaluation runs:

```python
from trulens.core.run import Run
from trulens.core.run import RunConfig
from datetime import datetime

TEST_RUN_NAME = f"base_run_{datetime.now().strftime('%Y%m%d%H%M%S')}"

base_run_config = RunConfig(
    run_name=TEST_RUN_NAME,
    description="Questions about SEC 10KS",
    dataset_name="SEC_FILINGS_QA",
    source_type="TABLE",
    label="CHUNKS",
    dataset_spec={
        "RECORD_ROOT.INPUT": "QUESTION",
        "RECORD_ROOT.GROUND_TRUTH_OUTPUT":"GROUND_TRUTH_ANSWER",
    },
)

base_run = base_tru_recorder.add_run(run_config=base_run_config)
```

```python
CONTEXTUAL_TEST_RUN_NAME = f"contextual_run_{datetime.now().strftime('%Y%m%d%H%M%S')}"

contextual_run_config = RunConfig(
    run_name=CONTEXTUAL_TEST_RUN_NAME,
    dataset_name="SEC_FILINGS_QA",
    description="Questions about SEC 10KS",
    source_type="TABLE",
    label="CONTEXTUAL_CHUNKS",
    dataset_spec={
        "RECORD_ROOT.INPUT": "QUESTION",
        "RECORD_ROOT.GROUND_TRUTH_OUTPUT":"GROUND_TRUTH_ANSWER",
    }
)

contextual_run = contextual_tru_recorder.add_run(run_config=contextual_run_config)
```

### Start the Evaluation Runs

Now, let's start the evaluation runs:

```python
base_run.start()
print("Finished base run")

contextual_run.start()
print("Finished contextual run")

run_list = [base_run, contextual_run]
```

### Compute Evaluation Metrics

After the runs complete, we'll compute metrics to evaluate performance:

```python
import time
for i in run_list:
    while i.get_status() == "INVOCATION_IN_PROGRESS":
        time.sleep(3)
    if i.get_status() == "INVOCATION_COMPLETED":
        i.compute_metrics(["correctness",
                           "answer_relevance",
                           "context_relevance",
                           "groundedness",])
        print(f"Kicked off Metrics Computation for Run {i.run_name}")
    if i.get_status() in ["FAILED", "UNKNOWN"]:
        print("Not able to compute metrics! Run status:", i.get_status())
```

These metrics will help us understand how well each RAG version performs:
- **Correctness**: How accurate the answers are compared to ground truth
- **Answer Relevance**: How relevant the answers are to the questions
- **Context Relevance**: How relevant the retrieved context is to the questions
- **Groundedness**: How well the answers are supported by the retrieved context

<!-- ------------------------ -->
## View and Compare Results


### Compare results

Finally, let's view the results of our runs by opening the evaluations page:

<a href="https://app.snowflake.com/_deeplink/#/ai-evaluations/databases/CHUNKING_EVALUATION/schemas/PUBLIC/applications/SEC_10K_CHAT_APP?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_campaign=-us-en-all&utm_content=app-compare-and-evaluate-chunking-strategies&utm_cta=developer-guides-deeplink" class="_deeplink">AI Observability Leaderboard</a>

In the dashboard, you can:

1. Compare overall metrics between the two versions
2. Analyze performance on individual questions
3. Examine retrieved contexts and generated answers
4. Identify strengths and weaknesses of each chunking strategy

To compare the runs head to head, click the checkbox for each version and then clicking `Compare` on the right side of the screen.

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You've successfully built and compared two different chunking strategies for a RAG application using Snowflake's AI Observability features. By systematically evaluating these approaches, you now have data-driven insights into which chunking strategy works better for your specific use case.

This methodology can be applied to optimize any RAG application, helping you make informed decisions about document processing, chunking, and retrieval strategies. The quantitative metrics provided by AI Observability allow you to iterate and improve your RAG applications with confidence.

### What You Learned

- Parsed and processed PDF documents using Snowflake's document parsing capabilities
- Implemented two different chunking strategies for RAG applications
- Created search services to retrieve data using our two chunking strategies
- Built complete RAG applications with instrumentation for observability
- Evaluated and compared RAG performance using AI Observability metrics

### Related Resources

Read more:

- [AI Observability in Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/ai-observability)
- [Long Context Isn't All You Need: Impact of Retrieval and Chunking on Finance RAG](/en/engineering-blog/impact-retrieval-chunking-finance-rag/)
