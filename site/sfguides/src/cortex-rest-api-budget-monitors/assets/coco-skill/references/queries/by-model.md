# Usage by Model Queries

## Token Usage by Model (Last 30 Days)

```sql
SELECT 
    MODEL_NAME,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    AVG(TOKENS) AS avg_tokens_per_request
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

## Daily Token Usage by Model

```sql
SELECT 
    DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
    MODEL_NAME,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -14, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1, 2;
```

## Top Models by Token Consumption

```sql
SELECT 
    MODEL_NAME,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    ROUND(100.0 * SUM(TOKENS) / SUM(SUM(TOKENS)) OVER (), 2) AS pct_of_total
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```
