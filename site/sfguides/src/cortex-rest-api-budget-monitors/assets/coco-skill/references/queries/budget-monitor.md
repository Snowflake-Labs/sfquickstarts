# Budget Monitor Queries

## Check Daily Budget Status

```sql
-- Parameters: Set your daily budget threshold
SET daily_budget = 1000000;  -- 1M tokens

SELECT 
    COALESCE(SUM(TOKENS), 0) AS today_tokens,
    $daily_budget AS budget,
    ROUND(100.0 * COALESCE(SUM(TOKENS), 0) / $daily_budget, 2) AS pct_used,
    CASE 
        WHEN COALESCE(SUM(TOKENS), 0) >= $daily_budget THEN 'OVER BUDGET'
        WHEN COALESCE(SUM(TOKENS), 0) >= $daily_budget * 0.8 THEN 'WARNING'
        ELSE 'OK'
    END AS status
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE DATE(START_TIME) = CURRENT_DATE();
```

## Check Weekly Budget Status

```sql
-- Parameters: Set your weekly budget threshold  
SET weekly_budget = 5000000;  -- 5M tokens

SELECT 
    COALESCE(SUM(TOKENS), 0) AS week_tokens,
    $weekly_budget AS budget,
    ROUND(100.0 * COALESCE(SUM(TOKENS), 0) / $weekly_budget, 2) AS pct_used,
    CASE 
        WHEN COALESCE(SUM(TOKENS), 0) >= $weekly_budget THEN 'OVER BUDGET'
        WHEN COALESCE(SUM(TOKENS), 0) >= $weekly_budget * 0.8 THEN 'WARNING'
        ELSE 'OK'
    END AS status
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATE_TRUNC('week', CURRENT_TIMESTAMP());
```

## Budget Status by Model

```sql
SELECT 
    MODEL_NAME,
    SUM(TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    ROUND(100.0 * SUM(TOKENS) / SUM(SUM(TOKENS)) OVER (), 2) AS pct_of_total
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATE_TRUNC('month', CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

## Daily Burn Rate

```sql
SELECT 
    DATE_TRUNC('day', START_TIME)::DATE AS usage_date,
    SUM(TOKENS) AS daily_tokens,
    COUNT(*) AS daily_requests,
    AVG(SUM(TOKENS)) OVER (ORDER BY DATE_TRUNC('day', START_TIME)::DATE ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d_avg
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1 DESC;
```

## Projected Monthly Usage

```sql
WITH daily_avg AS (
    SELECT AVG(daily_tokens) AS avg_daily_tokens
    FROM (
        SELECT SUM(TOKENS) AS daily_tokens
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY 
        WHERE START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
        GROUP BY DATE(START_TIME)
    )
)
SELECT 
    avg_daily_tokens,
    avg_daily_tokens * 30 AS projected_monthly_tokens,
    avg_daily_tokens * 7 AS projected_weekly_tokens
FROM daily_avg;
```
