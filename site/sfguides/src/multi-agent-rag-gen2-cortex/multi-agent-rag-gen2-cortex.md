author: Rohith Thiruvalluru
id: multi-agent-rag-gen2-cortex
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions, snowflake-site:taxonomy/snowflake-feature/build
language: en
summary: Building Production-Grade Multi-Agent RAG Systems with Snowflake Gen2 Warehouses and Cortex
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Multi-Agent RAG with Gen2 Warehouses and Cortex

## Overview
Duration: 3

The AI landscape is full of demos and one-off pipelines, but building production-grade Retrieval-Augmented Generation (RAG) systems introduces real engineering constraints.

In this quickstart, you'll build a **Snowflake-centric multi-agent RAG system** that:
- Retrieves from unstructured documents AND structured data
- Combines retrieval with metrics, charts, and semantic models
- Returns context-rich responses at production scale
- Leverages Gen2 Warehouses for high-concurrency execution

### Why Gen2 Warehouses?

Multi-agent architectures require:
- **30-50% faster joins** for analytical workloads
- **High concurrency** for parallel agent execution
- **Auto-scaling** from 1 to 100+ concurrent users
- **Cost-efficient bursting** without always-on warehouses

### Multi-Agent Architecture

1. **Retrieval Agent**: Semantic search via vector database
2. **Analyst Agent**: SQL generation from natural language
3. **Explainer Agent**: Context synthesis with Cortex LLMs
4. **Refiner Agent**: Quality control and PII masking
5. **Visualizer Agent**: Chart generation via Python UDFs
6. **Coordinator Agent**: Workflow orchestration

### Prerequisites

- Snowflake account with Cortex enabled
- External vector database (Pinecone/Weaviate)
- Python and SQL knowledge

## Architecture  
Duration: 5

```
User Query →
  Embedding Generator →
  Retrieval Agent (Vector DB) +
  Analyst Agent (Semantic SQL) →
  Explainer Agent (LLM) →
  Refiner Agent (Quality) →
  Visualizer Agent (Charts) →
Response (4.2s on Gen2 Medium)
```

Based on the article: [Query. Retrieve. Reason. Visualize.](https://medium.com/@i3xpl0it_58074/query-retrieve-reason-visualize-all-inside-snowflake-powered-by-gen2-warehouses-320f6e66539b)

## Setup
Duration: 5

```sql
USE ROLE SYSADMIN;
CREATE DATABASE MULTI_AGENT_RAG_DB;
CREATE SCHEMA RAG_SCHEMA;

CREATE WAREHOUSE RAG_GEN2_WH
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

USE WAREHOUSE RAG_GEN2_WH;
```

### External Vector DB Access

```sql
CREATE NETWORK RULE vector_db_rule
  TYPE = 'HOST_PORT'
  MODE = 'EGRESS'
  VALUE_LIST = ('api.pinecone.io:443');

CREATE EXTERNAL ACCESS INTEGRATION vector_db_int
  ALLOWED_NETWORK_RULES = (vector_db_rule)
  ENABLED = TRUE;
```

## Data Ingestion
Duration: 10

### Create Tables

```sql
CREATE TABLE document_chunks (
  chunk_id VARCHAR,
  chunk_text STRING,
  embedding VECTOR(FLOAT, 768)
);
```

### Semantic Chunking

```sql
CREATE FUNCTION chunk_document(content STRING)
RETURNS TABLE (chunk_id INT, chunk_text STRING)
LANGUAGE PYTHON
HANDLER = 'ChunkProcessor'
AS $$
class ChunkProcessor:
    def process(self, content):
        # 512-token chunks for coherence
        ...
$$;
```

### Generate Embeddings

```sql
UPDATE document_chunks
SET embedding = SNOWFLAKE.CORTEX.EMBED_TEXT_768(
  'e5-base-v2', chunk_text
);
```

## Retrieval Agent
Duration: 10

```sql
CREATE FUNCTION retrieval_agent(
  query VARCHAR, top_k INT
)
RETURNS TABLE (chunk_id VARCHAR, score FLOAT)
LANGUAGE PYTHON
EXTERNAL_ACCESS_INTEGRATIONS = (vector_db_int)
AS $$
import pinecone
class RetrievalAgent:
    def process(self, session, query, top_k):
        # Generate embedding
        emb = session.sql(f"""SELECT 
          SNOWFLAKE.CORTEX.EMBED_TEXT_768(
            'e5-base-v2', '{query}'
          )""").collect()[0][0]
        # Query Pinecone
        results = index.query(vector=emb, top_k=top_k)
        return results
$$;
```

## Analyst Agent
Duration: 12

### Semantic Model

```yaml
name: healthcare_360
tables:
  - name: claims
    measures:
      - name: total_claims
        expr: COUNT(DISTINCT CLAIM_ID)
```

### Agent

```sql
CREATE FUNCTION analyst_agent(question VARCHAR)
RETURNS TABLE (sql VARCHAR, results VARIANT)
AS $$
  -- Uses Cortex Analyst for SQL generation
  cortex.analyst.query(
    semantic_model='healthcare_360.yaml',
    query=question
  )
$$;
```

## Multi-Agent Coordination
Duration: 15

```sql
CREATE FUNCTION coordinator_agent(query VARCHAR)
RETURNS VARIANT
AS $$
  -- Parallel execution
  retrieval_results = retrieval_agent(query, 5)
  analyst_results = analyst_agent(query)
  
  -- Synthesize
  explanation = SNOWFLAKE.CORTEX.COMPLETE(
    'llama3.1-70b',
    CONCAT('Context:', retrieval_results, analyst_results)
  )
  
  RETURN explanation
$$;
```

## Sample Query
Duration: 3

```sql
SELECT * FROM TABLE(coordinator_agent(
  'ER visits for hypertensive patients in ZIP 10453'
));
```

**Result**: 4.2 seconds end-to-end

## Conclusion
Duration: 2

### What You Built

- Multi-agent RAG with 6 specialized agents
- Gen2 Warehouse optimization
- External vector DB integration  
- Production-scale performance (<5s)

### Resources

- [Original Article](https://medium.com/@i3xpl0it_58074/query-retrieve-reason-visualize-all-inside-snowflake-powered-by-gen2-warehouses-320f6e66539b)
- [Snowflake Cortex Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Gen2 Warehouses](https://docs.snowflake.com/en/user-guide/warehouses-overview)
