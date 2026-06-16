# Daily Usage Queries

## Daily Usage Summary (Last 14 Days)

```sql
SELECT 
    DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    COUNT(DISTINCT MODEL_NAME) AS models_used,
    COUNT(DISTINCT USER_ID) AS users_active
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -14, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1 DESC;
```

## Hourly Usage Pattern (Last 7 Days)

```sql
SELECT 
    HOUR(START_TIME) AS hour_of_day,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    AVG(TOKENS) AS avg_tokens_per_request
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1;
```

## Day of Week Usage Pattern

```sql
SELECT 
    DAYNAME(START_TIME) AS day_of_week,
    DAYOFWEEK(START_TIME) AS day_num,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 2;
```

## Usage Trend Comparison (This Week vs Last Week)

```sql
SELECT 
    'This Week' AS period,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATE_TRUNC('week', CURRENT_TIMESTAMP())

UNION ALL

SELECT 
    'Last Week' AS period,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(week, -1, DATE_TRUNC('week', CURRENT_TIMESTAMP()))
  AND START_TIME < DATE_TRUNC('week', CURRENT_TIMESTAMP());
```
