# Usage by User Queries

## Token Usage by User (Last 30 Days)

```sql
SELECT 
    u.NAME AS user_name,
    SUM(c.TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    COUNT(DISTINCT c.MODEL_NAME) AS models_used
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON c.USER_ID = u.USER_ID
WHERE c.START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

## Daily Usage by User

```sql
SELECT 
    DATE_TRUNC('day', c.START_TIME)::DATE AS usage_date,
    u.NAME AS user_name,
    SUM(c.TOKENS) AS total_tokens,
    COUNT(*) AS request_count,
    COUNT(DISTINCT c.MODEL_NAME) AS models_used
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON c.USER_ID = u.USER_ID
WHERE c.START_TIME >= DATEADD(day, -14, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

## Usage by User with Model Breakdown

```sql
WITH model_agg AS (
    SELECT 
        DATE_TRUNC('day', c.START_TIME)::DATE AS usage_date,
        COALESCE(u.NAME, 'Unknown') AS user_name,
        c.MODEL_NAME,
        SUM(c.TOKENS) AS model_total
    FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
    LEFT JOIN (
        SELECT USER_ID, NAME
        FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
        QUALIFY ROW_NUMBER() OVER (PARTITION BY USER_ID ORDER BY USER_ID) = 1
    ) u ON c.USER_ID = u.USER_ID
    WHERE c.START_TIME >= DATEADD(day, -14, CURRENT_TIMESTAMP())
    GROUP BY 1, 2, 3
)
SELECT 
    usage_date,
    user_name,
    SUM(model_total) AS total_tokens,
    COUNT(*) AS models_used,
    LISTAGG(MODEL_NAME || ':' || model_total, ', ') WITHIN GROUP (ORDER BY model_total DESC) AS model_tokens
FROM model_agg
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;
```

## Top Token Consumers

```sql
SELECT 
    u.NAME AS user_name,
    SUM(c.TOKENS) AS total_tokens,
    ROUND(100.0 * SUM(c.TOKENS) / SUM(SUM(c.TOKENS)) OVER (), 2) AS pct_of_total
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON c.USER_ID = u.USER_ID
WHERE c.START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```
