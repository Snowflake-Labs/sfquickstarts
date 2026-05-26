---------------- SIMPLE QUERIES ----------------
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "What is the total spend across all campaigns?" }] }]}$$
        )
    ) AS resp;
    
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Generate a report for our holiday gift guide" }] }]}$$
        )
    ) AS resp;
    
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "What content format generated the most revenue per dollar spent?" }] }]}$$
        )
    ) AS resp;

SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Compare the A/B test performance for our email vs social media campaigns" }] }]}$$
        )
    ) AS resp;
---------------- Multi-Tool Queries ----------------
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Which campaign had the highest ROI and what did customers say about it? Generate a report for that campaign too." }] }]}$$
        )
    ) AS resp;
    
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Which audience segment responded best to our promotions and what was their average spend?" }] }]}$$
        )
    ) AS resp;
    
---------------- Complex Synthesis Queries ----------------
    
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Show me campaigns where customer sentiment was negative but ROI was still positive — what made them work financially?" }] }]}$$
        )
    ) AS resp;
    
SELECT
    TRY_PARSE_JSON(
        SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
            'SELF_IMPROVING_AGENT_DB.AGENTS.MARKETING_CAMPAIGNS_AGENT',
            $${ "messages": [{ "role": "user", "content": [{ "type": "text", "text": "Which campaigns had the best A/B test lift but the worst customer sentiment?" }] }]}$$
        )
