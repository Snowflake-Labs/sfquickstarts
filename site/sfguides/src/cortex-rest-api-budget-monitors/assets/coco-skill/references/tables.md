# CORTEX_REST_API_USAGE_HISTORY Table Reference

## View Location
```
SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY
```

## Latency
- Up to **2 hours** latency from request time to availability in view

## Required Privileges
```sql
-- Option 1: ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Option 2: Grant privileges to another role
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <your_role>;
```

## Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `START_TIME` | TIMESTAMP_LTZ | Start time of the API request |
| `END_TIME` | TIMESTAMP_LTZ | End time of the API request |
| `USER_ID` | NUMBER | Unique identifier of the user who made the request |
| `MODEL_NAME` | VARCHAR | Name of the model used (e.g., 'claude-3-5-sonnet', 'mistral-large2') |
| `TOKENS` | NUMBER | Total tokens consumed (input + output) |
| `REQUEST_ID` | VARCHAR | Unique identifier for the request |

## Common Models

| Model Name | Provider | Description |
|------------|----------|-------------|
| `claude-3-5-sonnet` | Anthropic | Claude 3.5 Sonnet |
| `claude-sonnet-4-5` | Anthropic | Claude Sonnet 4.5 |
| `claude-sonnet-4-6` | Anthropic | Claude Sonnet 4.6 |
| `mistral-large2` | Mistral | Mistral Large 2 |
| `llama3.1-70b` | Meta | Llama 3.1 70B |
| `llama3.1-405b` | Meta | Llama 3.1 405B |

## Related Views

| View | Purpose |
|------|---------|
| `SNOWFLAKE.ACCOUNT_USAGE.USERS` | Join to get user names from USER_ID |
| `SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY` | Credit consumption history |
| `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` | Query execution history |

## Sample Join for User Names

```sql
SELECT 
    c.START_TIME,
    u.NAME AS user_name,
    c.MODEL_NAME,
    c.TOKENS
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_REST_API_USAGE_HISTORY c
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON c.USER_ID = u.USER_ID
WHERE c.START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY c.START_TIME DESC;
```
