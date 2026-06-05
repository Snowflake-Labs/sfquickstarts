# Chat Completions / Inference Queries

## Total API Calls by Model

```sql
SELECT 
    MODEL_NAME,
    COUNT(*) AS total_requests,
    SUM(TOKENS) AS total_tokens,
    AVG(TOKENS) AS avg_tokens_per_request,
    MIN(START_TIME) AS first_request,
    MAX(START_TIME) AS last_request
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

## Request Distribution by Hour

```sql
SELECT 
    HOUR(START_TIME) AS hour_of_day,
    COUNT(*) AS request_count,
    AVG(TOKENS) AS avg_tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1;
```

## Large Token Requests (Potential Long Conversations)

```sql
SELECT 
    START_TIME,
    MODEL_NAME,
    TOKENS,
    USER_ID
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
  AND TOKENS > 10000  -- Adjust threshold as needed
ORDER BY TOKENS DESC
LIMIT 50;
```

## Request Rate Over Time

```sql
SELECT 
    DATE_TRUNC('hour', START_TIME) AS hour_bucket,
    COUNT(*) AS requests_per_hour,
    SUM(TOKENS) AS tokens_per_hour
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -3, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1 DESC;
```

## Model Performance Comparison

```sql
SELECT 
    MODEL_NAME,
    COUNT(*) AS total_requests,
    AVG(TOKENS) AS avg_tokens,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY TOKENS) AS median_tokens,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY TOKENS) AS p95_tokens
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```
