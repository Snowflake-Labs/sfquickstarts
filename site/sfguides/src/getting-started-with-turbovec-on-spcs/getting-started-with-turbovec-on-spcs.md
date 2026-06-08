author: Navnit Shukla
id: getting-started-with-turbovec-on-spcs
summary: Deploy TurboVec, a high-performance data-oblivious vector index, on Snowpark Container Services for privacy-preserving multi-tenant RAG with 8x memory compression and perfect recall.
categories: Getting-Started, Data-Science-&-AI, Solution-Examples
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: Getting Started, Snowpark Container Services, Vector Search, RAG, AI, Machine Learning

# Getting Started with TurboVec on Snowpark Container Services
<!-- ------------------------ -->
## Overview
Duration: 5

### What You'll Build
- A TurboVec vector search service running inside Snowflake's compute infrastructure
- Multi-tenant filtered search with kernel-level SIMD isolation
- A comparison benchmark against Snowflake native vector search on a public dataset

### What You'll Learn
- How to deploy a custom vector index on Snowpark Container Services (SPCS)
- How data-oblivious quantization achieves 8x memory compression with zero recall loss
- How kernel-level filtered search enables multi-tenant vector isolation
- How TurboVec compares to Snowflake native `VECTOR_COSINE_SIMILARITY`

### What You'll Need
- A Snowflake account with Snowpark Container Services enabled
- Docker installed locally
- [Snow CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index) installed
- Python 3.9+

<!-- ------------------------ -->
## Setup Environment
Duration: 5

Run the following SQL in Snowsight or via Snow CLI:

```sql
USE ROLE ACCOUNTADMIN;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE SYSADMIN;

USE ROLE SYSADMIN;
CREATE DATABASE IF NOT EXISTS TURBOVEC_DEMO;
USE DATABASE TURBOVEC_DEMO;
CREATE SCHEMA IF NOT EXISTS PUBLIC;
CREATE IMAGE REPOSITORY TURBOVEC_DEMO.PUBLIC.TURBOVEC_REPO;
CREATE OR REPLACE STAGE YAML_STAGE;
CREATE OR REPLACE STAGE INDEXES ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

Create a compute pool (CPU only — TurboVec uses SIMD kernels, no GPU needed):

```sql
CREATE COMPUTE POOL IF NOT EXISTS TURBOVEC_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_S
  AUTO_RESUME = TRUE
  AUTO_SUSPEND_SECS = 300;
```

Wait until the pool is `ACTIVE`:

```sql
DESCRIBE COMPUTE POOL TURBOVEC_COMPUTE_POOL;
```

<!-- ------------------------ -->
## Build and Push Docker Image
Duration: 10

Clone the quickstart repository:

```bash
git clone https://github.com/navnitshukla/sfguide-getting-started-turbovec-on-spcs.git
cd sfguide-getting-started-turbovec-on-spcs
```

Build the Docker image (linux/amd64 for SPCS):

```bash
docker build --rm --platform linux/amd64 -t turbovec-spcs ./images/turbovec
```

Log in to the Snowflake registry using Snow CLI (handles MFA automatically):

```bash
snow spcs image-registry login
```

Find your registry URL:

```sql
SHOW IMAGE REPOSITORIES IN SCHEMA TURBOVEC_DEMO.PUBLIC;
```

Tag and push (replace `<ORG>-<ACCOUNT>` with your values from the above query):

```bash
docker tag turbovec-spcs \
  <ORG>-<ACCOUNT>.registry.snowflakecomputing.com/turbovec_demo/public/turbovec_repo/turbovec-spcs:latest

docker push \
  <ORG>-<ACCOUNT>.registry.snowflakecomputing.com/turbovec_demo/public/turbovec_repo/turbovec-spcs:latest
```

<!-- ------------------------ -->
## Create the TurboVec Service
Duration: 5

Create the service using an inline spec (replace the image path with your registry URL):

```sql
USE DATABASE TURBOVEC_DEMO;
USE SCHEMA PUBLIC;

CREATE SERVICE IF NOT EXISTS TURBOVEC
  IN COMPUTE POOL TURBOVEC_COMPUTE_POOL
  FROM SPECIFICATION $$
spec:
  containers:
    - name: turbovec
      image: <ORG>-<ACCOUNT>.registry.snowflakecomputing.com/turbovec_demo/public/turbovec_repo/turbovec-spcs:latest
      env:
        TURBOVEC_DIM: "1536"
        TURBOVEC_BIT_WIDTH: "4"
      resources:
        requests:
          memory: 2Gi
          cpu: 2
        limits:
          memory: 4Gi
          cpu: 4
      readinessProbe:
        port: 8000
        path: /health
      volumeMounts:
        - name: index-storage
          mountPath: /data
  endpoints:
    - name: api
      port: 8000
      public: false
  volumes:
    - name: index-storage
      source: local
$$
MIN_INSTANCES = 1
MAX_INSTANCES = 1;
```

Verify it's running:

```sql
SELECT SYSTEM$GET_SERVICE_STATUS('TURBOVEC_DEMO.PUBLIC.TURBOVEC');
-- Expected: "status":"READY","message":"Running"
```

Create service functions for SQL access:

```sql
CREATE OR REPLACE FUNCTION turbovec_sf_add(input OBJECT)
RETURNS VARIANT
SERVICE = TURBOVEC
ENDPOINT = api
MAX_BATCH_ROWS = 1
AS '/sf/add';

CREATE OR REPLACE FUNCTION turbovec_sf_search(input OBJECT)
RETURNS VARIANT
SERVICE = TURBOVEC
ENDPOINT = api
MAX_BATCH_ROWS = 1
AS '/sf/search';
```

<!-- ------------------------ -->
## Load the Public Benchmark Dataset
Duration: 15

We use the [Qdrant/DBpedia OpenAI 1536-dim](https://huggingface.co/datasets/Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-1M) dataset — 100K Wikipedia entities pre-embedded with OpenAI `text-embedding-3-large`.

Download and export locally (Python):

```bash
pip install datasets pyarrow numpy
python3 benchmarks/export_dbpedia.py
```

Upload to Snowflake:

```bash
snow sql -q "PUT file://~/data/py-turboquant/export/dbpedia_10k_with_text.parquet @TURBOVEC_DEMO.PUBLIC.YAML_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
```

Load into a native VECTOR table for comparison:

```sql
CREATE OR REPLACE FILE FORMAT parquet_format TYPE = PARQUET;

CREATE OR REPLACE TABLE dbpedia_vectors AS
SELECT
  $1:id::INTEGER AS id,
  $1:text::VARCHAR AS content,
  $1:embedding::VECTOR(FLOAT, 1536) AS embedding
FROM @YAML_STAGE/dbpedia_10k_with_text.parquet (FILE_FORMAT => 'parquet_format');
```

Load into TurboVec (batch 100 vectors per call):

```sql
CREATE OR REPLACE PROCEDURE load_vectors_batch(start_id INT, end_id INT)
RETURNS VARCHAR LANGUAGE SQL AS $$
BEGIN
  LET batch_size INT := 100;
  LET current_start INT := :start_id;
  LET loaded INT := 0;
  WHILE (current_start < :end_id) DO
    LET current_end INT := LEAST(current_start + batch_size, :end_id);
    SELECT turbovec_sf_add(OBJECT_CONSTRUCT(
      'vectors', ARRAY_AGG(embedding::ARRAY), 'ids', ARRAY_AGG(id)
    )) FROM dbpedia_vectors WHERE id >= :current_start AND id < :current_end;
    loaded := loaded + (current_end - current_start);
    current_start := current_end;
  END WHILE;
  RETURN 'Loaded ' || loaded || ' vectors';
END; $$;

CALL load_vectors_batch(0, 10000);
```

<!-- ------------------------ -->
## Run the Benchmark
Duration: 10

### TurboVec Search (4-bit quantized, on SPCS):

```sql
SELECT
  turbovec_sf_search(OBJECT_CONSTRUCT(
    'query', q.embedding::ARRAY, 'k', 5
  )):ids AS turbovec_top5,
  turbovec_sf_search(OBJECT_CONSTRUCT(
    'query', q.embedding::ARRAY, 'k', 5
  )):latency_ms AS turbovec_latency_ms
FROM dbpedia_vectors q
WHERE q.id = 0;
```

### Snowflake Native Vector Search (exact FP32):

```sql
SELECT d.id, VECTOR_COSINE_SIMILARITY(d.embedding, q.embedding) AS score
FROM dbpedia_vectors d, dbpedia_vectors q
WHERE q.id = 0 AND d.id != 0
ORDER BY score DESC
LIMIT 5;
```

### Expected Results (100K vectors, d=1536):

| Method | Recall@5 | Latency | Memory |
|--------|----------|---------|--------|
| **TurboVec 4-bit (SPCS)** | **1.000** | **13ms** | **73.6 MB** |
| Snowflake Native (FP32) | 1.000 | ~500ms | 585.9 MB |

TurboVec returns identical results to exact search with 8x less memory and ~40x lower latency.

<!-- ------------------------ -->
## Multi-Tenant Filtered Search
Duration: 5

TurboVec supports kernel-level tenant isolation via allowlists:

```sql
-- Add vectors with tenant assignment
SELECT turbovec_sf_add(OBJECT_CONSTRUCT(
  'vectors', ARRAY_AGG(embedding::ARRAY),
  'ids', ARRAY_AGG(id),
  'tenant_id', 'tenant_a'
))
FROM dbpedia_vectors WHERE id < 100;

-- Search restricted to tenant_a only
SELECT turbovec_sf_search(OBJECT_CONSTRUCT(
  'query', (SELECT embedding::ARRAY FROM dbpedia_vectors WHERE id = 200),
  'k', 5,
  'tenant_id', 'tenant_a'
));
```

The SIMD kernel short-circuits blocks with no allowed vectors — filtered search is often **faster** than unfiltered because less data is scored.

<!-- ------------------------ -->
## Cleanup
Duration: 2

```sql
USE ROLE SYSADMIN;
DROP SERVICE IF EXISTS TURBOVEC_DEMO.PUBLIC.TURBOVEC;
DROP COMPUTE POOL IF EXISTS TURBOVEC_COMPUTE_POOL;
DROP DATABASE IF EXISTS TURBOVEC_DEMO;
```

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 2

### What You Learned
- TurboVec achieves perfect recall with 8x memory compression via data-oblivious quantization
- No training step required — vectors are indexed immediately on ingest
- SPCS enables running custom vector indexes inside Snowflake's governance boundary
- Kernel-level filtered search provides multi-tenant isolation without separate indexes

### Key Numbers
- **Recall@5:** 1.000 (identical to exact FP32 search)
- **Latency:** 13ms per query at 100K vectors
- **Compression:** 8x (585.9 MB → 73.6 MB)
- **Build time:** 0.24s (vs 12.7s for FAISS PQ training)

### Resources
- [TurboVec GitHub](https://github.com/RyanCodrai/turbovec)
- [TurboQuant Paper (ICLR 2026)](https://arxiv.org/abs/2504.19874)
- [Dataset: Qdrant/DBpedia OpenAI 1536-dim](https://huggingface.co/datasets/Qdrant/dbpedia-entities-openai3-text-embedding-3-large-1536-1M)
- [Snowpark Container Services Docs](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Quickstart Source Code](https://github.com/navnitshukla/sfguide-getting-started-turbovec-on-spcs)
