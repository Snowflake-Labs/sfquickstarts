author: Josh Reini, Prathamesh Nimkar
id: build-and-evaluate-agents-with-langgraph-and-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: Build and evaluate a multi-agent supervisor system using LangGraph and Snowflake Cortex Agents
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Build and Evaluate Multi-Agent Systems with Snowflake and LangGraph

## Overview
Duration: 5

Modern organizations need to combine multiple AI capabilities to handle complex business questions. This quickstart demonstrates how to build a **multi-agent supervisor architecture** using LangGraph and Snowflake Cortex Agents for customer intelligence, churn prediction, and business analytics.

### What is a Multi-Agent Supervisor Architecture?

A multi-agent supervisor architecture uses a central "supervisor" LLM that:

1. **Analyzes** incoming queries to understand intent
2. **Plans** an execution strategy with explicit steps
3. **Routes** queries to specialized agents based on the plan
4. **Synthesizes** results from multiple agents into coherent executive summaries

```
User Query → Supervisor (Plan) → Specialized Agent(s) → Supervisor (Synthesize) → Executive Summary
```

### Why LangGraph

LangGraph provides low-level supporting infrastructure for any long-running, stateful workflow or agent. LangGraph is great for building durable, stateful agents across multiple systems.

If you're not building with LangGraph, try this [guide](https://www.snowflake.com/en/developers/guides/multi-agent-orchestration-snowflake-intelligence/) to build a multi-agent system entirely native to Snowflake.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Query                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SUPERVISOR (Planning)                       │
│               Plans execution and routes queries                 │
└─────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  CONTENT_AGENT  │  │ DATA_ANALYST    │  │ RESEARCH_AGENT  │
│                 │  │ _AGENT          │  │                 │
│ • Sentiment     │  │ • Metrics       │  │ • Market Intel  │
│ • Feedback      │  │ • Behavior      │  │ • Strategy      │
│ • Support       │  │ • Analytics     │  │ • Trends        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Snowflake AI Tools                              │
│     Cortex Search │ Cortex Analyst │ Custom AI UDFs             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SUPERVISOR (Synthesis)                        │
│              Creates executive summary response                  │
└─────────────────────────────────────────────────────────────────┘
```

### What You'll Learn

- How to set up Snowflake Cortex Agents with specialized tools
- How to create Cortex Search services for semantic search
- How to build Semantic Views for Cortex Analyst text-to-SQL
- How to build a multi-agent supervisor workflow using LangGraph
- How to evaluate agent performance using TruLens with Snowflake

### What You'll Build

A complete multi-agent customer intelligence system that:

- Routes queries to specialized agents (Content, Data Analyst, Research)
- Uses Cortex Search for semantic search across support tickets
- Uses Cortex Analyst for natural language to SQL conversion
- Uses custom AI UDFs for sentiment analysis and churn prediction
- Evaluates responses using Agent Goal-Plan-Action alignment metrics via TruLens

### Prerequisites

- [Snowflake Account](https://signup.snowflake.com/) with Cortex AI features enabled
- Python 3.9+ installed locally
- [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- Basic familiarity with LangGraph and LangChain concepts (optional)

## Setup Git Integration

Duration: 5

The first step is to clone the repository into Snowflake using Git Integration. This gives you access to all the SQL scripts and demo data files.

### Create Database and Clone Repository

Open Snowsight and create a new SQL Worksheet. Run the following SQL:

```sql
USE ROLE ACCOUNTADMIN;

-- Create database and schema
CREATE DATABASE IF NOT EXISTS CUSTOMER_INTELLIGENCE_DB;
USE DATABASE CUSTOMER_INTELLIGENCE_DB;
CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

-- Create API integration for GitHub
CREATE API INTEGRATION IF NOT EXISTS github_api_integration
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/Snowflake-Labs/')
    ENABLED = TRUE;

-- Clone the GitHub repository
CREATE OR REPLACE GIT REPOSITORY customer_intelligence_demo
    API_INTEGRATION = github_api_integration
    ORIGIN = 'https://github.com/Snowflake-Labs/sfguide-build-and-evaluate-agents-with-snowflake-and-langgraph.git';

-- Fetch latest from GitHub
ALTER GIT REPOSITORY customer_intelligence_demo FETCH;

-- Verify repository contents
LS @customer_intelligence_demo/branches/main/;
```

You should see the SQL scripts and CSV files in the repository listing.

### Run Setup Scripts

After the Git integration is set up, you can run each SQL script directly from the repository. Navigate to **Data » Databases » CUSTOMER_INTELLIGENCE_DB » PUBLIC » Git Repositories » customer_intelligence_demo » branches » main » sql** and execute each script in order:

| Order | Script | Purpose |
|-------|--------|---------|
| 1 | `01_setup_database_and_load_data.sql` | Creates tables and loads CSV data |
| 2 | `02_setup_cortex_search.sql` | Creates Cortex Search services |
| 3 | `03_setup_semantic_views.sql` | Creates Semantic Views for Cortex Analyst |
| 4 | `04_setup_udfs.sql` | Creates AI UDFs (tools for agents) |
| 5 | `05_setup_cortex_agents.sql` | Creates the three Cortex Agents |

> **Note:** Run scripts in order as later scripts depend on earlier ones.

The following sections explain what each script does in detail.

## Setup Database and Load Data
Duration: 10

The `01_setup_database_and_load_data.sql` script creates the tables and loads demo data. Here's what it does:

### Create Tables

Create the four tables that will store customer data:

```sql
-- CUSTOMERS TABLE
CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id VARCHAR(50) PRIMARY KEY,
    signup_date DATE NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    company_size VARCHAR(20) NOT NULL,
    industry VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    monthly_revenue DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- USAGE_EVENTS TABLE
CREATE OR REPLACE TABLE USAGE_EVENTS (
    event_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    event_date DATE NOT NULL,
    feature_used VARCHAR(50) NOT NULL,
    session_duration_minutes INTEGER NOT NULL,
    actions_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- SUPPORT_TICKETS TABLE
CREATE OR REPLACE TABLE SUPPORT_TICKETS (
    ticket_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    created_date DATE NOT NULL,
    category VARCHAR(30) NOT NULL,
    priority VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,
    resolution_time_hours INTEGER,
    satisfaction_score INTEGER,
    ticket_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- CHURN_EVENTS TABLE
CREATE OR REPLACE TABLE CHURN_EVENTS (
    churn_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    churn_date DATE NOT NULL,
    churn_reason VARCHAR(50) NOT NULL,
    days_since_signup INTEGER NOT NULL,
    final_plan_type VARCHAR(20),
    final_monthly_revenue DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
```

### Step 3: Load Demo Data

Load the CSV files from the Git repository:

```sql
-- Create file format
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE = CSV 
    SKIP_HEADER = 1 
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL', 'null') 
    EMPTY_FIELD_AS_NULL = TRUE;

-- Load CUSTOMERS
INSERT INTO CUSTOMERS (customer_id, signup_date, plan_type, company_size, industry, status, monthly_revenue)
SELECT $1,$2,$3,$4,$5,$6,$7 
FROM @customer_intelligence_demo/branches/main/demo_customers.csv (FILE_FORMAT=>csv_format);

-- Load USAGE_EVENTS  
INSERT INTO USAGE_EVENTS (event_id, customer_id, event_date, feature_used, session_duration_minutes, actions_count)
SELECT $1,$2,$3,$4,$5,$6 
FROM @customer_intelligence_demo/branches/main/demo_usage_events.csv (FILE_FORMAT=>csv_format);

-- Load SUPPORT_TICKETS
INSERT INTO SUPPORT_TICKETS (ticket_id, customer_id, created_date, category, priority, status, resolution_time_hours, satisfaction_score, ticket_text)
SELECT $1,$2,$3,$4,$5,$6,$7,$8,$9 
FROM @customer_intelligence_demo/branches/main/demo_support_tickets.csv (FILE_FORMAT=>csv_format);

-- Load CHURN_EVENTS
INSERT INTO CHURN_EVENTS (churn_id, customer_id, churn_date, churn_reason, days_since_signup, final_plan_type, final_monthly_revenue)
SELECT $1,$2,$3,$4,$5,$6,$7 
FROM @customer_intelligence_demo/branches/main/demo_churn_events.csv (FILE_FORMAT=>csv_format);
```

### Step 4: Verify Data Loaded

```sql
SELECT 'CUSTOMERS' as table_name, COUNT(*) as row_count FROM CUSTOMERS
UNION ALL SELECT 'USAGE_EVENTS', COUNT(*) FROM USAGE_EVENTS
UNION ALL SELECT 'SUPPORT_TICKETS', COUNT(*) FROM SUPPORT_TICKETS
UNION ALL SELECT 'CHURN_EVENTS', COUNT(*) FROM CHURN_EVENTS;
```

You should see data in all four tables.

## Setup Cortex Search Services
Duration: 5

Cortex Search provides hybrid search (semantic + keyword) capabilities for unstructured text data. We'll create search services that the agents will use to find relevant customer feedback and support tickets.

### Create Support Tickets Search Service

This service enables semantic search across all customer support tickets:

```sql
USE DATABASE CUSTOMER_INTELLIGENCE_DB;
USE SCHEMA PUBLIC;

CREATE OR REPLACE CORTEX SEARCH SERVICE SUPPORT_TICKETS_SEARCH
ON ticket_text
ATTRIBUTES customer_id, ticket_id, category, priority, status, created_date
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        ticket_id,
        customer_id,
        category,
        priority,
        status,
        created_date,
        ticket_text
    FROM SUPPORT_TICKETS
);
```

### Create Customers Search Service (Optional)

```sql
CREATE OR REPLACE CORTEX SEARCH SERVICE CUSTOMERS_SEARCH
ON industry
ATTRIBUTES customer_id, plan_type, company_size, status, monthly_revenue
WAREHOUSE = COMPUTE_WH
TARGET_LAG = '1 hour'
AS (
    SELECT 
        customer_id,
        plan_type,
        company_size,
        industry,
        status,
        monthly_revenue
    FROM CUSTOMERS
);
```

### Verify Search Services

```sql
SHOW CORTEX SEARCH SERVICES IN SCHEMA CUSTOMER_INTELLIGENCE_DB.PUBLIC;
```

## Setup Semantic Views
Duration: 10

Semantic Views power Cortex Analyst, enabling natural language to SQL conversion. They define the schema, relationships, and business metrics that the AI uses to generate accurate SQL queries.

### Create Customer Behavior Analyst View

This semantic view is used by the DATA_ANALYST_AGENT for customer behavior analytics:

```sql
CREATE OR REPLACE SEMANTIC VIEW CUSTOMER_BEHAVIOR_ANALYST
  TABLES (
    CUSTOMERS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.CUSTOMERS
      PRIMARY KEY (CUSTOMER_ID)
      COMMENT = 'Customer master data',
    USAGE_EVENTS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.USAGE_EVENTS
      COMMENT = 'Customer usage events',
    SUPPORT_TICKETS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.SUPPORT_TICKETS
      COMMENT = 'Support tickets',
    CHURN_EVENTS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.CHURN_EVENTS
      COMMENT = 'Churn events'
  )
  RELATIONSHIPS (
    CUSTOMER_TO_USAGE AS USAGE_EVENTS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID),
    CUSTOMER_TO_SUPPORT AS SUPPORT_TICKETS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID),
    CUSTOMER_TO_CHURN AS CHURN_EVENTS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID)
  )
  FACTS (
    CUSTOMERS.MONTHLY_REVENUE AS CUSTOMERS.MONTHLY_REVENUE
      WITH SYNONYMS = ('MRR', 'monthly recurring revenue')
      COMMENT = 'Monthly revenue per customer',
    USAGE_EVENTS.SESSION_DURATION_MINUTES AS USAGE_EVENTS.SESSION_DURATION_MINUTES
      WITH SYNONYMS = ('session length')
      COMMENT = 'Session duration in minutes',
    USAGE_EVENTS.ACTIONS_COUNT AS USAGE_EVENTS.ACTIONS_COUNT
      COMMENT = 'Number of actions in session',
    SUPPORT_TICKETS.SATISFACTION_SCORE AS SUPPORT_TICKETS.SATISFACTION_SCORE
      WITH SYNONYMS = ('CSAT')
      COMMENT = 'Customer satisfaction score'
  )
  DIMENSIONS (
    CUSTOMERS.CUSTOMER_ID AS CUSTOMERS.CUSTOMER_ID
      WITH SYNONYMS = ('customer identifier', 'account id')
      COMMENT = 'Unique customer identifier',
    CUSTOMERS.INDUSTRY AS CUSTOMERS.INDUSTRY
      WITH SYNONYMS = ('sector', 'vertical')
      COMMENT = 'Customer industry',
    CUSTOMERS.PLAN_TYPE AS CUSTOMERS.PLAN_TYPE
      WITH SYNONYMS = ('subscription', 'tier')
      COMMENT = 'Subscription plan level'
  )
  METRICS (
    CUSTOMERS.TOTAL_CUSTOMERS AS COUNT(CUSTOMERS.CUSTOMER_ID)
      WITH SYNONYMS = ('customer count')
      COMMENT = 'Total number of customers',
    CUSTOMERS.ARPU AS AVG(CUSTOMERS.MONTHLY_REVENUE)
      WITH SYNONYMS = ('average revenue per user')
      COMMENT = 'Average revenue per customer',
    USAGE_EVENTS.AVG_SESSION_DURATION AS AVG(USAGE_EVENTS.SESSION_DURATION_MINUTES)
      COMMENT = 'Average session duration'
  )
  COMMENT = 'Customer behavior analytics for usage patterns, churn analysis, and retention insights';
```

### Create Strategic Research Analyst View

This semantic view is used by the RESEARCH_AGENT for market intelligence:

```sql
CREATE OR REPLACE SEMANTIC VIEW STRATEGIC_RESEARCH_ANALYST
  TABLES (
    CUSTOMERS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.CUSTOMERS
      PRIMARY KEY (CUSTOMER_ID)
      COMMENT = 'Customer master data',
    USAGE_EVENTS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.USAGE_EVENTS
      COMMENT = 'Usage data',
    SUPPORT_TICKETS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.SUPPORT_TICKETS
      COMMENT = 'Support data',
    CHURN_EVENTS AS CUSTOMER_INTELLIGENCE_DB.PUBLIC.CHURN_EVENTS
      COMMENT = 'Churn data'
  )
  RELATIONSHIPS (
    CUSTOMER_TO_USAGE AS USAGE_EVENTS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID),
    CUSTOMER_TO_SUPPORT AS SUPPORT_TICKETS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID),
    CUSTOMER_TO_CHURN AS CHURN_EVENTS (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID)
  )
  METRICS (
    CUSTOMERS.TOTAL_MRR AS SUM(CUSTOMERS.MONTHLY_REVENUE)
      WITH SYNONYMS = ('total recurring revenue')
      COMMENT = 'Total monthly recurring revenue',
    CHURN_EVENTS.LOST_REVENUE AS SUM(CHURN_EVENTS.FINAL_MONTHLY_REVENUE)
      COMMENT = 'Total lost revenue'
  )
  COMMENT = 'Strategic research and market intelligence for executive-level business analysis';
```

### Verify Semantic Views

```sql
SHOW SEMANTIC VIEWS IN SCHEMA CUSTOMER_INTELLIGENCE_DB.PUBLIC;
```

## Setup Custom AI UDFs
Duration: 10

Custom UDFs (User-Defined Functions) extend agent capabilities with specialized AI analysis. These functions use Snowflake Cortex AI to perform sentiment analysis, behavior analysis, and strategic insights.

### Create Customer Content Analyzer UDF

Used by the CONTENT_AGENT for sentiment and feedback analysis:

```sql
CREATE OR REPLACE FUNCTION AI_ANALYZE_CUSTOMER_CONTENT_V2(
    "CUSTOMER_IDS_STRING" VARCHAR, 
    "ANALYSIS_TYPE" VARCHAR DEFAULT 'recent_support_tickets'
)
RETURNS VARIANT
LANGUAGE SQL
AS '
WITH parsed_customer_ids AS (
  SELECT TRIM(VALUE) as customer_id
  FROM TABLE(SPLIT_TO_TABLE(customer_ids_string, '',''))
),
target_tickets AS (
  SELECT 
    st.customer_id,
    st.ticket_text,
    st.category,
    st.priority,
    st.satisfaction_score,
    st.created_date
  FROM support_tickets st
  INNER JOIN parsed_customer_ids pci ON st.customer_id = pci.customer_id
  ORDER BY st.created_date DESC
  LIMIT 10
),
content_summary AS (
  SELECT 
    COUNT(*) as total_tickets,
    COUNT(DISTINCT customer_id) as customers_with_tickets,
    ROUND(AVG(satisfaction_score), 2) as avg_satisfaction,
    COUNT(CASE WHEN priority IN (''high'', ''critical'') THEN 1 END) as urgent_tickets,
    LISTAGG(DISTINCT category, '', '') as ticket_categories,
    SUBSTRING(LISTAGG(ticket_text, '' | ''), 1, 1000) as combined_ticket_text
  FROM target_tickets
),
ai_content_analysis AS (
  SELECT 
    cs.*,
    CASE 
      WHEN cs.total_tickets > 0 THEN
        AI_COMPLETE(
          ''claude-3-5-sonnet'',
          CONCAT(
            ''Analyze customer feedback: '', analysis_type, ''\\n'',
            ''Tickets: '', cs.total_tickets, '' ('', cs.urgent_tickets, '' urgent)\\n'',
            ''Satisfaction: '', cs.avg_satisfaction, ''/5\\n'',
            ''Categories: '', cs.ticket_categories, ''\\n'',
            ''Content: '', cs.combined_ticket_text, ''\\n\\n'',
            ''JSON: {"sentiment":"positive/neutral/negative","urgency":"low/medium/high","key_issue":"main_problem","action_needed":"recommendation"}''
          )
        )
      ELSE NULL
    END as ai_content_insights
  FROM content_summary cs
)
SELECT OBJECT_CONSTRUCT(
    ''analysis_type'', analysis_type,
    ''customer_ids_input'', customer_ids_string,
    ''content_metrics'', OBJECT_CONSTRUCT(
      ''total_tickets'', total_tickets,
      ''customers_affected'', customers_with_tickets,
      ''avg_satisfaction'', avg_satisfaction,
      ''urgent_tickets'', urgent_tickets
    ),
    ''ai_content_insights'', TRY_PARSE_JSON(ai_content_insights),
    ''analysis_timestamp'', CURRENT_TIMESTAMP()
)::VARIANT as result
FROM ai_content_analysis
';
```

### Create Customer Behavior Analyzer UDF

Used by the DATA_ANALYST_AGENT for behavior and churn analysis:

```sql
CREATE OR REPLACE FUNCTION AI_ANALYZE_CUSTOMER_BEHAVIOR_SEGMENT_V2(
    "CUSTOMER_IDS_STRING" VARCHAR, 
    "ANALYSIS_DAYS" NUMBER(38,0) DEFAULT 30
)
RETURNS VARIANT
LANGUAGE SQL
AS '
WITH parsed_customer_ids AS (
  SELECT TRIM(VALUE) as customer_id
  FROM TABLE(SPLIT_TO_TABLE(customer_ids_string, '',''))
),
target_customers AS (
  SELECT 
    c.customer_id,
    c.plan_type,
    c.monthly_revenue,
    c.company_size,
    c.industry,
    c.status
  FROM customers c
  INNER JOIN parsed_customer_ids pci ON c.customer_id = pci.customer_id
),
behavior_metrics AS (
  SELECT 
    COUNT(DISTINCT u.customer_id) as active_customers,
    COUNT(*) as total_events,
    ROUND(AVG(u.session_duration_minutes), 2) as avg_session_duration,
    SUM(u.actions_count) as total_actions
  FROM usage_events u
  INNER JOIN parsed_customer_ids pci ON u.customer_id = pci.customer_id
),
analysis_result AS (
  SELECT 
    tc.customer_count,
    tc.total_mrr,
    bm.active_customers,
    bm.total_events,
    bm.avg_session_duration,
    CASE 
      WHEN tc.customer_count > 0 THEN
        AI_COMPLETE(
          ''claude-3-5-sonnet'',
          CONCAT(
            ''Analyze customer behavior:\\n'',
            ''Customers: '', tc.customer_count, '', MRR: $'', tc.total_mrr, ''\\n'',
            ''Active: '', COALESCE(bm.active_customers, 0), ''\\n'',
            ''Events: '', COALESCE(bm.total_events, 0), ''\\n'',
            ''JSON: {"engagement":"high/medium/low","churn_risk":"low/medium/high","recommendation":"action"}''
          )
        )
      ELSE NULL
    END as ai_behavior_insights
  FROM (
    SELECT 
      COUNT(*) as customer_count,
      SUM(monthly_revenue) as total_mrr
    FROM target_customers
  ) tc
  CROSS JOIN behavior_metrics bm
)
SELECT OBJECT_CONSTRUCT(
    ''customer_ids_input'', customer_ids_string,
    ''behavior_metrics'', OBJECT_CONSTRUCT(
      ''customer_count'', customer_count,
      ''total_mrr'', total_mrr,
      ''active_customers'', COALESCE(active_customers, 0),
      ''avg_session_duration'', COALESCE(avg_session_duration, 0)
    ),
    ''ai_behavior_insights'', TRY_PARSE_JSON(ai_behavior_insights),
    ''analysis_timestamp'', CURRENT_TIMESTAMP()
)::VARIANT as result
FROM analysis_result
';
```

### Verify UDFs

```sql
SHOW USER FUNCTIONS IN SCHEMA CUSTOMER_INTELLIGENCE_DB.PUBLIC;
```

## Create Cortex Agents
Duration: 15

Now we create the three specialized Cortex Agents that will be orchestrated by the LangGraph supervisor. Each agent has specific tools and instructions for their domain.

### Create Agent Database

```sql
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
USE DATABASE SNOWFLAKE_INTELLIGENCE;
CREATE SCHEMA IF NOT EXISTS AGENTS;
USE SCHEMA AGENTS;
```

### Create CONTENT_AGENT

The Content Agent specializes in customer feedback, sentiment analysis, and support intelligence:

```sql
CREATE OR REPLACE AGENT CONTENT_AGENT
  COMMENT = 'Customer feedback, sentiment analysis, and communication intelligence specialist'
FROM SPECIFICATION $$
{
    "models": {
        "orchestration": "claude-4-sonnet"
    },
    "orchestration": {
        "budget": {
            "seconds": 60,
            "tokens": 32000
        }
    },
    "instructions": {
        "system": "The Content Agent specializes in analyzing customer feedback, support interactions, and satisfaction trends. It combines targeted customer analysis with broad pattern recognition to distinguish between isolated incidents and systemic issues.",
        "response": "Always synthesize data into executive insights. Provide maximum 3-5 key findings with business impact."
    },
    "tools": [
        {
            "tool_spec": {
                "type": "cortex_search",
                "name": "CUSTOMER_FEEDBACK_SEARCH",
                "description": "Semantic search across all customer support tickets and feedback."
            }
        },
        {
            "tool_spec": {
                "type": "generic",
                "name": "CUSTOMER_CONTENT_ANALYZER",
                "description": "AI-powered analysis of specific customer feedback and support interactions.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_ids_string": {
                            "type": "string",
                            "description": "Comma-separated list of customer IDs to analyze"
                        }
                    },
                    "required": ["customer_ids_string"]
                }
            }
        }
    ],
    "tool_resources": {
        "CUSTOMER_FEEDBACK_SEARCH": {
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            },
            "search_service": "CUSTOMER_INTELLIGENCE_DB.PUBLIC.SUPPORT_TICKETS_SEARCH",
            "id_column": "ticket_id",
            "title_column": "ticket_text"
        },
        "CUSTOMER_CONTENT_ANALYZER": {
            "type": "procedure",
            "identifier": "CUSTOMER_INTELLIGENCE_DB.PUBLIC.AI_ANALYZE_CUSTOMER_CONTENT_V2",
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            }
        }
    }
}
$$;
```

### Create DATA_ANALYST_AGENT

The Data Analyst Agent specializes in customer behavior, metrics, and predictive analytics:

```sql
CREATE OR REPLACE AGENT DATA_ANALYST_AGENT
  COMMENT = 'Customer behavior, business metrics, and predictive analytics specialist'
FROM SPECIFICATION $$
{
    "models": {
        "orchestration": "claude-4-sonnet"
    },
    "orchestration": {
        "budget": {
            "seconds": 60,
            "tokens": 32000
        }
    },
    "instructions": {
        "system": "Expert customer behavior analyst specializing in data-driven insights about customer engagement, usage patterns, churn prediction, and retention strategies.",
        "response": "Always synthesize data into executive insights. Never return raw data tables."
    },
    "tools": [
        {
            "tool_spec": {
                "type": "cortex_analyst_text_to_sql",
                "name": "BUSINESS_INTELLIGENCE_ANALYST",
                "description": "Natural language to SQL for comprehensive customer behavior analytics."
            }
        },
        {
            "tool_spec": {
                "type": "generic",
                "name": "CUSTOMER_BEHAVIOR_ANALYZER",
                "description": "AI-powered targeted customer behavior analysis.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "customer_ids_string": {
                            "type": "string",
                            "description": "Comma-separated list of customer IDs to analyze"
                        }
                    },
                    "required": ["customer_ids_string"]
                }
            }
        }
    ],
    "tool_resources": {
        "BUSINESS_INTELLIGENCE_ANALYST": {
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            },
            "semantic_view": "CUSTOMER_INTELLIGENCE_DB.PUBLIC.CUSTOMER_BEHAVIOR_ANALYST"
        },
        "CUSTOMER_BEHAVIOR_ANALYZER": {
            "type": "procedure",
            "identifier": "CUSTOMER_INTELLIGENCE_DB.PUBLIC.AI_ANALYZE_CUSTOMER_BEHAVIOR_SEGMENT_V2",
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            }
        }
    }
}
$$;
```

### Create RESEARCH_AGENT

The Research Agent specializes in market intelligence and strategic analysis:

```sql
CREATE OR REPLACE AGENT RESEARCH_AGENT
  COMMENT = 'Market intelligence, strategic analysis, and competitive insights specialist'
FROM SPECIFICATION $$
{
    "models": {
        "orchestration": "claude-4-sonnet"
    },
    "orchestration": {
        "budget": {
            "seconds": 60,
            "tokens": 32000
        }
    },
    "instructions": {
        "system": "Strategic research and market intelligence specialist focused on executive-level business analysis, competitive positioning, and market opportunity identification.",
        "response": "Always synthesize data into executive insights. Provide board-ready intelligence."
    },
    "tools": [
        {
            "tool_spec": {
                "type": "cortex_analyst_text_to_sql",
                "name": "STRATEGIC_MARKET_ANALYST",
                "description": "Executive-level market intelligence platform for strategic analysis."
            }
        }
    ],
    "tool_resources": {
        "STRATEGIC_MARKET_ANALYST": {
            "execution_environment": {
                "type": "warehouse",
                "warehouse": "COMPUTE_WH",
                "query_timeout": 300
            },
            "semantic_view": "CUSTOMER_INTELLIGENCE_DB.PUBLIC.STRATEGIC_RESEARCH_ANALYST"
        }
    }
}
$$;
```

### Verify Agents

```sql
SHOW AGENTS IN SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS;
```

## Build LangGraph Supervisor Workflow
Duration: 20

Now we'll build the LangGraph workflow that orchestrates these Snowflake Cortex Agents. This section walks through the Python code from the Jupyter notebook.

### Local Environment Setup

First, set up your local Python environment:

```bash
# Clone the repository
git clone https://github.com/Snowflake-Labs/sfguide-build-and-evaluate-agents-with-snowflake-and-langgraph.git
cd sfguide-build-and-evaluate-agents-with-snowflake-and-langgraph

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file with your Snowflake credentials:

```env
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=CUSTOMER_INTELLIGENCE_DB
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=your_role
```

### Import Dependencies

```python
# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.graph.message import MessagesState

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate

# Snowflake imports
from langchain_snowflake import ChatSnowflake, SnowflakeCortexAgent, create_session_from_env

# Utility imports
import json
import os
from typing import Dict, List, Optional, Literal
from dotenv import load_dotenv

load_dotenv()
```

### Define Workflow State

The state tracks messages, execution plan, and current step:

```python
class State(MessagesState):
    """Extended state that tracks execution plan and progress."""
    execution_plan: Optional[Dict] = None  # The supervisor's explicit plan
    current_step: int = 0  # Current step being executed
```

### Create Snowflake Session

```python
session = create_session_from_env()

# Ensure warehouse is set
warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
session.sql(f"USE WAREHOUSE {warehouse}").collect()

print(f"Connected to: {session.get_current_database()}")
```

### Initialize Components

```python
# Supervisor model for routing and synthesis
supervisor_model = ChatSnowflake(
    session=session,
    model="claude-4-sonnet",
    temperature=0.1,
    max_tokens=2000
)

# Agent configuration
AGENT_DATABASE = "SNOWFLAKE_INTELLIGENCE"
AGENT_SCHEMA = "AGENTS"
AGENT_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')

# Initialize specialized agents
content_agent = SnowflakeCortexAgent(
    session=session,
    name="CONTENT_AGENT",
    database=AGENT_DATABASE,
    schema=AGENT_SCHEMA,
    warehouse=AGENT_WAREHOUSE,
)

data_analyst_agent = SnowflakeCortexAgent(
    session=session,
    name="DATA_ANALYST_AGENT",
    database=AGENT_DATABASE,
    schema=AGENT_SCHEMA,
    warehouse=AGENT_WAREHOUSE,
)

research_agent = SnowflakeCortexAgent(
    session=session,
    name="RESEARCH_AGENT",
    database=AGENT_DATABASE,
    schema=AGENT_SCHEMA,
    warehouse=AGENT_WAREHOUSE,
)
```

### Create Supervisor Prompts

The supervisor uses two prompts - one for planning and one for synthesis:

```python
planning_prompt = """
You are an Executive AI Assistant supervisor. Create EFFICIENT execution plans.

**Agent Selection:**
| Question Type | Agent | Why |
|--------------|-------|-----|
| Counts, averages, metrics, trends | DATA_ANALYST_AGENT | Direct SQL query |
| Customer complaints, feedback themes | CONTENT_AGENT | Semantic search needed |
| Industry analysis, market segments, CLV | RESEARCH_AGENT | Strategic SQL analytics |

**JSON Response Format:**
{
    "plan_summary": "Single-agent approach: [AGENT] will [direct action]",
    "steps": [
        {
            "step_number": 1,
            "agent": "AGENT_NAME",
            "purpose": "Direct answer to the question",
            "expected_output": "The specific answer with metrics"
        }
    ],
    "combination_strategy": "Present agent's response directly",
    "expected_final_output": "Clear answer to the question"
}

**Query:** {input}

**RESPOND WITH ONLY THE JSON**
"""

synthesis_prompt = """
You are an Executive AI Assistant synthesizing agent results.

**Original Question**: {question}
**Plan Summary**: {plan_summary}
**Agent Results**: {agent_outputs}

Provide a clear, confident answer with:
## Summary
[Direct answer in 2-3 sentences with key metrics]

## Key Findings
[3-5 bullet points of important insights]

## Recommendations
[2-3 actionable next steps]
"""
```

### Build the Graph

```python
# Create the StateGraph
workflow = StateGraph(State)

# Add nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("CONTENT_AGENT", content_agent_node)
workflow.add_node("DATA_ANALYST_AGENT", data_analyst_agent_node)
workflow.add_node("RESEARCH_AGENT", research_agent_node)

# Add entry point
workflow.add_edge(START, "supervisor")

# Compile
app = workflow.compile()
```

## Evaluate with TruLens
Duration: 15

TruLens provides observability and evaluation for your multi-agent system. We'll set up metrics to assess plan quality, execution efficiency, and response accuracy.

### Import TruLens Dependencies

```python
from trulens.apps.langgraph import TruGraph
from trulens.connectors.snowflake import SnowflakeConnector
from trulens.providers.cortex import Cortex
from trulens.core.feedback.custom_metric import MetricConfig
from trulens.core.feedback.selector import Selector
from trulens.core.run import Run, RunConfig
from functools import partial
import uuid
```

### Setup TruLens Connector

```python
# Connect TruLens to Snowflake for observability
sf_connector = SnowflakeConnector(snowpark_session=session)

# Initialize Cortex provider for evaluations
trace_eval_provider = Cortex(
    model_engine="openai-gpt-5",
    snowpark_session=session
)
```

### Configure Evaluation Metrics

```python
# Plan Quality - Evaluates supervisor's planning ability
f_plan_quality = MetricConfig(
    metric_implementation=partial(
        trace_eval_provider.plan_quality_with_cot_reasons,
        enable_trace_compression=False
    ),
    metric_name="Plan Quality",
    selectors={"trace": Selector(trace_level=True)},
)

# Plan Adherence - Checks if agents follow the plan
f_plan_adherence = MetricConfig(
    metric_implementation=partial(
        trace_eval_provider.plan_adherence_with_cot_reasons,
        enable_trace_compression=False
    ),
    metric_name="Plan Adherence",
    selectors={"trace": Selector(trace_level=True)},
)

# Execution Efficiency - Measures workflow efficiency
f_execution_efficiency = MetricConfig(
    metric_implementation=partial(
        trace_eval_provider.execution_efficiency_with_cot_reasons,
        enable_trace_compression=False
    ),
    metric_name="Execution Efficiency",
    selectors={"trace": Selector(trace_level=True)},
)

# Logical Consistency - Verifies response consistency
f_logical_consistency = MetricConfig(
    metric_implementation=partial(
        trace_eval_provider.logical_consistency_with_cot_reasons,
        enable_trace_compression=False
    ),
    metric_name="Logical Consistency",
    selectors={"trace": Selector(trace_level=True)},
)
```

### Create Instrumented App

Directly wrap the LangGraph graph with TruGraph:

```python
# Create TruLens instrumented app by directly wrapping the graph
APP_NAME = "Customer Intelligence Multi-Agent"
APP_VERSION = f"V{uuid.uuid4().hex[:8]}"

tru_app = TruGraph(
    app,  # The compiled StateGraph directly
    app_name=APP_NAME,
    app_version=APP_VERSION,
    main_method=app.invoke,  # Use graph's invoke method directly
    connector=sf_connector,
)
```

### Run Evaluation

The evaluation dataset contains full LangGraph state dicts that are passed directly to `graph.invoke()`:

```python
import pandas as pd

# Define evaluation inputs as full LangGraph state dicts
# This passes the actual state that LangGraph expects directly to graph.invoke()
evaluation_inputs = [
    {
        "messages": [HumanMessage(content="Assess the churn risk for customers complaining about API issues.")],
    },
    {
        "messages": [HumanMessage(content="What industries have the highest customer lifetime value?")],
    },
]

# Create DataFrame with the state dicts
queries_df = pd.DataFrame({"input_state": evaluation_inputs})

# Configure run - map to the column containing state dicts
run_config = RunConfig(
    run_name=f"customer_intel_eval_{uuid.uuid4().hex[:8]}",
    dataset_name="customer_intelligence_queries",
    source_type="DATAFRAME",
    dataset_spec={"RECORD_ROOT.INPUT": "input_state"},  # Maps to state dict column
)

# Add run and execute
run = tru_app.add_run(run_config=run_config)
run.start(input_df=queries_df)

# Compute metrics
metrics = [
    "answer_relevance",
    f_plan_quality,
    f_plan_adherence,
    f_execution_efficiency,
    f_logical_consistency,
]
run.compute_metrics(metrics)
```

## Conclusion and Resources

Duration: 5

Congratulations! You've successfully built a **multi-agent supervisor architecture** using LangGraph and Snowflake Cortex. This system demonstrates:

### What You Built

1. **Snowflake Infrastructure**
   - Database with customer intelligence data
   - Cortex Search services for semantic search
   - Semantic Views for text-to-SQL
   - Custom AI UDFs for specialized analysis
   - Three specialized Cortex Agents

2. **LangGraph Workflow**
   - Supervisor model for intelligent routing
   - Explicit execution planning
   - Multi-agent orchestration
   - Response synthesis

3. **Evaluation Pipeline**
   - TruLens integration for observability
   - Custom metrics for goal-plan-action (GPA) alignment
   - Snowflake-native evaluation storage

### Next Steps

- **Add more agents**: Extend with specialized agents for sales, finance, or operations
- **Tune prompts**: Use the evaluations to guide improvements to supervisor and agent prompts.
- **Build custom tools**: Create additional UDFs for domain-specific analysis

### Related Resources

- [Developer Guide GitHub Repository](https://github.com/Snowflake-Labs/sfguide-build-and-evaluate-agents-with-snowflake-and-langgraph)
- [LangChain Snowflake Integration](https://github.com/langchain-ai/langchain-snowflake)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Cortex Agents Guide](https://docs.snowflake.com/user-guide/snowflake-cortex/cortex-agents)
- [TruLens Documentation](https://www.trulens.org/)

