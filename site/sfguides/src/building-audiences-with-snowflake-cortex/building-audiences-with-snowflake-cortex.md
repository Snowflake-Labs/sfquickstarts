author: Luke Ambrosetti, Dureti Shemsi
id: building-audiences-with-snowflake-cortex
language: en
summary: Build intelligent, industry-specific Cortex Agents for natural language audience building and customer analytics in Retail, Financial Services, and Gaming verticals.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/applied-analytics, snowflake-site:taxonomy/snowflake-feature/cortex-analyst, snowflake-site:taxonomy/solution-center/certification/certified-solution
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-building-audiences-with-snowflake-cortex


# Building Audiences with Snowflake Cortex

<!-- ------------------------ -->
## Overview

Through this guide, you will build and deploy three intelligent Cortex Agents—for Retail, Financial Services, and Gaming—that enable natural language audience building and customer analytics. Powered by Snowflake Cortex Analyst and industry-specific semantic models, these agents translate conversational questions into precise SQL queries, allowing you to analyze customer behavior, build targeted marketing segments, and materialize audiences directly in Snowflake Intelligence—no SQL required.

### Prerequisites

- Snowflake account with appropriate privileges
- ACCOUNTADMIN role or equivalent permissions
- Access to Snowflake Intelligence features
- Snowflake Cortex AI features enabled
- [Cross Region Cortex Inference enabled](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference) (if required for your region)

### What You'll Learn

- Setting up Cortex Agents for customer analytics
- Configuring Cortex Analyst tools
- Building natural language query interfaces
- Materializing audience segments

### What You'll Need

- [SFGuide GitHub Repository Files](https://github.com/Snowflake-Labs/sfguide-building-audiences-with-snowflake-cortex/tree/main) including SQL setup script and three semantic model YAML files
- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account

### What You'll Build

**Three intelligent Cortex Agents** (Retail, FSI, Gaming) integrated with **Snowflake Intelligence**, enabling you to:

- **Interact conversationally** with your customer data through Snowflake Intelligence's natural language interface
- **Build targeted marketing audiences** by asking questions and refining segments across multiple industries
- **Analyze customer behavior** including segmentation, lifetime value, and campaign ROI—all through conversation
- **Generate actionable insights** with business outcomes, financial projections, and recommended actions
- **Materialize campaign audiences** as permanent tables ready for CRM activation

**End result:** Complete, ROI-justified marketing campaigns built in minutes through conversational analytics—no SQL required.

<!-- ------------------------ -->
## Setup Environment

Navigate to <a href="https://app.snowflake.com/_deeplink/#/workspaces?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=building-audiences-with-snowflake-cortex&utm_cta=developer-guides-deeplink" class="_deeplink">**Projects → Workspaces**</a> in Snowsight and create a new SQL worksheet. Copy the complete SQL script below and execute all statements by clicking **▶ Run All** or pressing `Ctrl+Shift+Enter`.

> NOTE:
> 
> The script uses `accountadmin` role for initial setup and automatically loads sample data from Snowflake's public S3 bucket.

```sql
-- ============================================================================
--                      CUSTOMER ANALYTICS SCRIPT
-- ============================================================================

-- ============================================================================
-- SECTION 1: GLOBAL INFRASTRUCTURE SETUP
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- Set query tag for tracking and analytics
ALTER SESSION SET query_tag = '{"origin":"sf_sit-is","name":"building_audiences_with_cortex","version":{"major":1,"minor":0},"attributes":{"is_quickstart":1,"source":"sql"}}';

-- ----------------------------------------------------------------------------
-- Step 1.1: Create CUSTOMER_ANALYTICS_ROLE Role
-- ----------------------------------------------------------------------------
-- Create a dedicated role for customer analytics with appropriate permissions
CREATE ROLE IF NOT EXISTS CUSTOMER_ANALYTICS_ROLE;
GRANT ROLE CUSTOMER_ANALYTICS_ROLE TO ROLE ACCOUNTADMIN;

-- Grant Cortex access to both ACCOUNTADMIN and CUSTOMER_ANALYTICS_ROLE
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ACCOUNTADMIN;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- Enable cross-region inference to ensure Cortex models are available in all regions
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

-- ----------------------------------------------------------------------------
-- Step 1.2: Create Database and Schema
-- ----------------------------------------------------------------------------
CREATE OR REPLACE DATABASE CUSTOMER_ANALYTICS_DB;
CREATE OR REPLACE SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS;

-- ----------------------------------------------------------------------------
-- Step 1.3: Create Warehouse
-- ----------------------------------------------------------------------------
CREATE OR REPLACE WAREHOUSE CUSTOMER_ANALYTICS_WH
    WAREHOUSE_SIZE = 'MEDIUM' 
    AUTO_SUSPEND = 60 
    AUTO_RESUME = TRUE;

-- ----------------------------------------------------------------------------
-- Step 1.4: Grant Privileges to CUSTOMER_ANALYTICS_ROLE Role
-- ----------------------------------------------------------------------------
-- Grant database and schema access
GRANT USAGE ON DATABASE CUSTOMER_ANALYTICS_DB TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT USAGE ON SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- Grant warehouse access
GRANT USAGE ON WAREHOUSE CUSTOMER_ANALYTICS_WH TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- Grant privileges on all current and future objects
GRANT ALL ON SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON ALL TABLES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON FUTURE TABLES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- Grant access to file formats, stages, functions, and procedures
GRANT ALL ON ALL FILE FORMATS IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON FUTURE FILE FORMATS IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON ALL STAGES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON FUTURE STAGES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON FUTURE FUNCTIONS IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON ALL PROCEDURES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT ALL ON FUTURE PROCEDURES IN SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- ----------------------------------------------------------------------------
-- Step 1.5: Setup Snowflake Intelligence for Agents
-- ----------------------------------------------------------------------------
-- Create Snowflake Intelligence database and schema for AI agents
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE;
GRANT USAGE ON DATABASE SNOWFLAKE_INTELLIGENCE TO ROLE CUSTOMER_ANALYTICS_ROLE;

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_INTELLIGENCE.AGENTS;
GRANT USAGE ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- Grant permission to create and use agents
GRANT CREATE AGENT ON SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT USAGE ON ALL AGENTS IN SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE CUSTOMER_ANALYTICS_ROLE;
GRANT USAGE ON FUTURE AGENTS IN SCHEMA SNOWFLAKE_INTELLIGENCE.AGENTS TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- ============================================================================
-- SECTION 2: CORTEX ANALYST DATA SETUP
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Step 2.1: Set Context
-- ----------------------------------------------------------------------------
USE WAREHOUSE CUSTOMER_ANALYTICS_WH;
USE SCHEMA CUSTOMER_ANALYTICS_DB.ANALYTICS;

-- ----------------------------------------------------------------------------
-- Step 2.2: Create Supporting Objects
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FILE FORMAT common_csv_format
    TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    COMMENT = 'Standard CSV format with a header and optional quotes.';
CREATE OR REPLACE STAGE semantic_models
    DIRECTORY = (ENABLE = TRUE) COMMENT = 'Internal stage for Cortex Analyst semantic model YAML files.';

-- ----------------------------------------------------------------------------
-- Step 2.3: Create Custom Stored Procedure for Audience Materialization
-- ----------------------------------------------------------------------------
-- This procedure enables AI agents to save query results as permanent tables
CREATE OR REPLACE PROCEDURE materialize_table(sql_text STRING, table_name STRING)
RETURNS VARCHAR(16777216)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'materialize_table'
COMMENT = 'Materializes the results of a SQL SELECT statement into a permanent table. Used by AI agents to save audience segments.'
EXECUTE AS CALLER
AS
$$
def materialize_table(session, sql_text, table_name):
    """
    Materializes a table from a SQL query using Snowpark.
    
    Args:
        session: Snowpark session object (automatically provided by Snowflake)
        sql_text: SQL SELECT statement to execute
        table_name: Name of the table to create
        
    Returns:
        'success' if table is created successfully
        'error' if there was an error during table creation
    """
    try:
        # Execute the SQL query to create a DataFrame
        df = session.sql(sql_text)
        
        # Materialize the DataFrame as a table (overwrites if exists)
        df.write.mode("overwrite").save_as_table(table_name)
        
        return 'success'
    except Exception as e:
        # Return error status if anything goes wrong
        return 'error'
$$;

-- Grant explicit permission to the role to execute this procedure
GRANT USAGE ON PROCEDURE materialize_table(STRING, STRING) TO ROLE CUSTOMER_ANALYTICS_ROLE;

-- ----------------------------------------------------------------------------
-- Step 2.4: Create Vertical-Specific Tables
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS retail_customer (
    customer_id                       VARCHAR(50),
    full_name                         VARCHAR(200),
    email                             VARCHAR(200),
    phone                             VARCHAR(50),
    street                            VARCHAR(200),
    city                              VARCHAR(100),
    state                             VARCHAR(50),
    zip                               VARCHAR(20),
    country                           VARCHAR(50),
    registration_date                 DATE,
    last_transaction_date             DATE,
    age                               NUMBER(3),
    gender                            VARCHAR(20),
    marital_status                    VARCHAR(50),
    children                          NUMBER(2),
    education_level                   VARCHAR(50),
    occupation                        VARCHAR(200),
    ltv_band                          VARCHAR(50),
    annual_income                     NUMBER(12, 2),
    home_ownership                    VARCHAR(50),
    device_preferences                VARCHAR(50),
    preferred_shopping_time           VARCHAR(50),
    social_media_presence             VARCHAR(50),
    customer_acquisition_channel      VARCHAR(100),
    preferred_payment_method          VARCHAR(50),
    favorite_product_category         VARCHAR(100),
    sports                            BOOLEAN,
    travel                            BOOLEAN,
    cooking                           BOOLEAN,
    arts                              BOOLEAN,
    technology                        BOOLEAN,
    reading                           BOOLEAN,
    photography                       BOOLEAN,
    gardening                         BOOLEAN,
    music                             BOOLEAN,
    movies                            BOOLEAN,
    diy_projects                      BOOLEAN,
    fitness                           BOOLEAN,
    outdoors                          BOOLEAN,
    pets                              BOOLEAN,
    shopping                          BOOLEAN,
    brand_interaction_preference      VARCHAR(100),
    preferred_communication_channel   VARCHAR(50),
    customer_referral                 BOOLEAN,
    subscribed_to_newsletter          BOOLEAN,
    loyalty_program_tier              VARCHAR(50),
    abandoned_cart_rate               FLOAT,
    conversion_rate                   FLOAT,
    emails_opened_last_month          NUMBER(10),
    average_review_score              FLOAT,
    high_value_customer               BOOLEAN,
    promotional_sensitivity           VARCHAR(50),
    total_transactions                NUMBER(10),
    total_transaction_amount          NUMBER(38, 2),
    average_order_value               NUMBER(38, 2),
    zero_purchase                     BOOLEAN,
    one_purchase                      BOOLEAN,
    first_purchase_date               DATE,
    second_purchase_date              DATE,
    purchase_entropy                  VARCHAR(50),
    is_at_risk                        BOOLEAN,
    is_loyal_customer                 BOOLEAN,
    is_new_customer                   BOOLEAN,
    predicted_ltv                     NUMBER(38, 2),
    key_segment                       VARCHAR(100)
) COMMENT = 'Customer data for the Retail vertical.';

CREATE TABLE IF NOT EXISTS fsi_customer (
    customer_id                       VARCHAR(50),
    full_name                         VARCHAR(200),
    email                             VARCHAR(200),
    phone                             VARCHAR(50),
    state                             VARCHAR(50),
    metro_area                        VARCHAR(100),
    country                           VARCHAR(50),
    registration_date                 DATE,
    age                               NUMBER(3),
    gender                            VARCHAR(20),
    marital_status                    VARCHAR(50),
    children                          NUMBER(2),
    education_level                   VARCHAR(50),
    occupation                        VARCHAR(200),
    annual_income                     NUMBER(12, 2),
    home_ownership                    VARCHAR(50),
    device_preferences                VARCHAR(50),
    auto_loan_default_flag            BOOLEAN,
    personal_loan_default_flag        BOOLEAN,
    checking_account_flag             BOOLEAN,
    savings_account_flag              BOOLEAN,
    high_yield_savings_flag           BOOLEAN,
    kid_savings_account_flag          BOOLEAN,
    biz_checking_account_flag         BOOLEAN,
    biz_credit_card_flag              BOOLEAN,
    personal_credit_card_flag         BOOLEAN,
    cashback_card_flag                BOOLEAN,
    travel_rewards_card_flag          BOOLEAN,
    balance_transfer_card_flag        BOOLEAN,
    bad_credit_card_flag              BOOLEAN,
    auto_loan_flag                    BOOLEAN,
    personal_loan_flag                BOOLEAN,
    estimated_net_worth               NUMBER(15, 2),
    personal_credit_limit             NUMBER(12, 2),
    fico_score                        NUMBER(3),
    personal_credit_balance           NUMBER(12, 2),
    personal_credit_utilization       FLOAT,
    wealth_management_flag            BOOLEAN,
    marketing_eligibility_flag        BOOLEAN,
    marketing_preference_opt_in       BOOLEAN,
    venture_card_marketing_flag       BOOLEAN,
    marketing_propensity              NUMBER(3),
    transactions_last_30              NUMBER(10),
    last_transaction_date             DATE,
    preferred_communication_channel   VARCHAR(50),
    subscribed_to_newsletter          BOOLEAN,
    engagement_last_month             NUMBER(10),
    high_value_customer               BOOLEAN
) COMMENT = 'Customer data for the Financial Services (FSI) vertical.';

CREATE TABLE IF NOT EXISTS gaming_customer (
    account_creation_date             DATE,
    age                               NUMBER(3),
    customer_id                       VARCHAR(50),
    email                             VARCHAR(200),
    full_name                         VARCHAR(200),
    gamer_tag                         VARCHAR(200),
    gender                            VARCHAR(50),
    phone                             VARCHAR(50),
    state                             VARCHAR(50),
    achievements_points               NUMBER(10),
    active_game_subscription          BOOLEAN,
    activity_last_30_hours            NUMBER(10),
    activity_last_7_hours             NUMBER(10),
    activity_last_90_hours            NUMBER(10),
    avg_weekly_playtime_hours         NUMBER(10),
    beta_opt_in                       BOOLEAN,
    companion_app_installed           BOOLEAN,
    days_since_last_login             NUMBER(10),
    friend_count_ingame               NUMBER(10),
    last_login_date                   DATE,
    latest_expansion_preorder_date    DATE,
    latest_expansion_purchase_date    DATE,
    lifetime_spend_usd                NUMBER(38, 2),
    marketing_channel_preference      VARCHAR(100),
    number_of_dlc_purchased           NUMBER(10),
    social_media_linked               BOOLEAN,
    c_marketing                       BOOLEAN,
    c_channel_email                   BOOLEAN,
    c_channel_in_app                  BOOLEAN,
    c_channel_sms                     BOOLEAN,
    c_topic_console_news              BOOLEAN,
    c_topic_new_games                 BOOLEAN,
    c_topic_promotions                BOOLEAN
) COMMENT = 'Customer data for the Gaming/Entertainment vertical.';

-- ----------------------------------------------------------------------------
-- Step 2.5: Load Customer Data Directly from S3
-- ----------------------------------------------------------------------------
COPY INTO retail_customer
    FROM 's3://sfquickstarts/sfguide-building-audiences-with-snowflake-cortex/retail_customer.csv'
    FILE_FORMAT = (FORMAT_NAME = 'common_csv_format')
    ON_ERROR = 'CONTINUE';

COPY INTO fsi_customer
    FROM 's3://sfquickstarts/sfguide-building-audiences-with-snowflake-cortex/fsi_customer.csv'
    FILE_FORMAT = (FORMAT_NAME = 'common_csv_format')
    ON_ERROR = 'CONTINUE';

COPY INTO gaming_customer
    FROM 's3://sfquickstarts/sfguide-building-audiences-with-snowflake-cortex/gaming_customer.csv'
    FILE_FORMAT = (FORMAT_NAME = 'common_csv_format')
    ON_ERROR = 'CONTINUE';

-- ============================================================================
--                          SETUP COMPLETE
-- ============================================================================
```

The script creates roles, warehouses, databases, schemas, customer data tables (Retail, FSI, Gaming), and a custom materialization procedure—all with sample data loaded from S3.

<!-- ------------------------ -->
## Configure Semantic Models

[Download the three semantic model YAML files](https://github.com/Snowflake-Labs/sfguide-building-audiences-with-snowflake-cortex/tree/main/scripts/semantic_models) from the GitHub repository: `retail_customer.yaml`, `fsi_customer.yaml`, and `gaming_customer.yaml`.

In Snowsight, navigate to **Data → Databases → CUSTOMER_ANALYTICS_DB → ANALYTICS → Stages → SEMANTIC_MODELS**. Click **+ Files** and upload all three YAML files.

Each semantic model contains tables, dimensions, measures, time dimensions, synonyms, and relationships that enable natural language understanding.

<!-- ------------------------ -->
## Create Cortex Agents

You'll create three Cortex Agents—one for each industry vertical. Each agent follows the same configuration pattern.

### Retail Customer Intelligence Agent

1. Navigate to **AI & ML → Cortex Agents** and click **+ Cortex Agent**
2. **Object name**: `RETAIL_CUSTOMER_INTELLIGENCE_AGENT`
3. **Display name**: `Retail Customer Intelligence Agent`
4. Click **Create**, then **Edit**

**About Tab:**

```
A Cortex Agent to help analyze retail customer behavior, build targeted audiences, and identify high-value customer segments based on purchase patterns, interests, and demographics.
```

**Tools Tab:**
- Click **+ Add** → **Cortex Analyst** → **Semantic Model File**
- **Database**: `CUSTOMER_ANALYTICS_DB`, **Schema**: `ANALYTICS`, **Stage**: `SEMANTIC_MODELS`
- **Name**: `Retail_Customer_Model`
- **Description**: `Semantic model for analyzing retail customer demographics, purchase behavior, interests, and lifetime value predictions.`
- Select **retail_customer.yaml**
- **Warehouse**: `CUSTOMER_ANALYTICS_WH`, **Timeout**: 60 seconds

**Orchestration Tab:**
- **Orchestration instructions**: `When answering questions about retail customers, always consider multiple dimensions such as demographics, purchase behavior, and customer interests. Break down complex queries into logical steps and provide context for your findings. If building audience segments, clearly state the criteria being used.`
- **Response instructions**: `Respond in a professional yet conversational tone. When providing customer lists or segments, summarize key statistics first before showing detailed results. Always include actionable insights that marketing teams can use for campaign planning.`

Click **Save**.

### FSI Customer Intelligence Agent

1. Navigate to **AI & ML → Cortex Agents** and click **+ Cortex Agent**
2. **Object name**: `FSI_CUSTOMER_INTELLIGENCE_AGENT`
3. **Display name**: `FSI Customer Intelligence Agent`
4. Click **Create**, then **Edit**

**About Tab:**

```
A Cortex Agent to help analyze financial services customers, identify high-value accounts, assess credit risk, and build targeted marketing campaigns based on product holdings, credit profiles, and financial behavior.
```

**Tools Tab:**
- Click **+ Add** → **Cortex Analyst** → **Semantic Model File**
- **Database**: `CUSTOMER_ANALYTICS_DB`, **Schema**: `ANALYTICS`, **Stage**: `SEMANTIC_MODELS`
- **Name**: `FSI_Customer_Model`
- **Description**: `Semantic model for analyzing financial services customers including account types, credit scores, product holdings, and marketing eligibility.`
- Select **fsi_customer.yaml**
- **Warehouse**: `CUSTOMER_ANALYTICS_WH`, **Timeout**: 60 seconds

**Orchestration Tab:**
- **Orchestration instructions**: `When analyzing financial services customers, prioritize data privacy and compliance considerations. Consider credit risk, account relationships, and product holdings holistically. For cross-sell opportunities, evaluate customer eligibility and financial health before making recommendations.`
- **Response instructions**: `Respond with financial industry professionalism. When discussing credit scores, risk profiles, or account details, be precise and data-driven. Always emphasize customer value and eligibility criteria when building marketing segments. Highlight compliance considerations where relevant.`

Click **Save**.

### Gaming Customer Intelligence Agent

1. Navigate to **AI & ML → Cortex Agents** and click **+ Cortex Agent**
2. **Object name**: `GAMING_CUSTOMER_INTELLIGENCE_AGENT`
3. **Display name**: `Gaming Customer Intelligence Agent`
4. Click **Create**, then **Edit**

**About Tab:**

```
A Cortex Agent to help analyze gaming customer engagement, identify active and at-risk players, build targeted campaigns, and understand player behavior based on gameplay metrics, purchases, and social interactions.
```

**Tools Tab:**
- Click **+ Add** → **Cortex Analyst** → **Semantic Model File**
- **Database**: `CUSTOMER_ANALYTICS_DB`, **Schema**: `ANALYTICS`, **Stage**: `SEMANTIC_MODELS`
- **Name**: `Gaming_Customer_Model`
- **Description**: `Semantic model for analyzing gaming customers including playtime activity, subscription status, DLC purchases, and engagement metrics.`
- Select **gaming_customer.yaml**
- **Warehouse**: `CUSTOMER_ANALYTICS_WH`, **Timeout**: 60 seconds

**Orchestration Tab:**
- **Orchestration instructions**: `When analyzing gaming customers, consider engagement patterns, activity levels, and purchase behavior together. For churn risk analysis, look at login frequency and activity trends. When building campaign audiences, respect marketing consent preferences and communication channel choices.`
- **Response instructions**: `Respond in an engaging, gaming-industry-appropriate tone. When discussing player activity or engagement metrics, provide context about what constitutes healthy engagement. For campaign targeting, clearly explain the behavioral signals and consent status that qualify players for outreach.`

Click **Save**.

<!-- ------------------------ -->
## Materialize Campaign Audiences

To enable saving audience segments as permanent tables, add a custom tool to each Cortex Agent.

1. Navigate to **AI & ML → Cortex Agents** and select an agent
2. Click **Edit** → **Tools** tab → **+ Add** → **Custom Tool**
3. **Resource type**: **procedure**
4. **Database & Schema**: `CUSTOMER_ANALYTICS_DB.ANALYTICS`
5. **Custom tool identifier**: `CUSTOMER_ANALYTICS_DB.ANALYTICS.MATERIALIZE_TABLE(VARCHAR, VARCHAR)`
6. **Name**: `Materialize_Audience`
7. **Warehouse**: `CUSTOMER_ANALYTICS_WH`, **Timeout**: 60 seconds
8. **Description**: `Save query results as a permanent table for future use. Use this tool when the user asks to save, materialize, or create a table from audience segment results.`
9. Click **Add** and **Save**

Repeat this for all three agents (Retail, FSI, Gaming).

<!-- ------------------------ -->
## Retail Campaign Walkthrough

### The Challenge

Your direct-to-consumer retail company is facing a critical issue: high-value customers are going dormant. The marketing team suspects there are hundreds of millions in potential lifetime value at risk, but they lack the data to quantify the problem, understand why it's happening, or build a targeted reactivation campaign.

**Your challenge today:** Build a complete, ROI-justified win-back campaign in minutes, not weeks.

Navigate to **AI & ML > Snowflake Intelligence** and select the **Retail Customer Intelligence Agent**.

### Step 1: Quantify At-Risk Revenue

Copy and paste this into Snowflake Intelligence:

```
How many high-value customers with predicted lifetime value over $2,000 are flagged as at risk? What's the total revenue at risk from this group?
```

This query identifies high-value customers at risk and calculates total revenue exposure to establish campaign urgency.

### Step 2: Diagnose Dormancy Patterns

Copy and paste this into Snowflake Intelligence:

```
For those at-risk high-value customers, how long has it been since their last purchase? What's their average abandoned cart rate? What are the top product interests across this group?
```

This query diagnoses dormancy severity and reveals behavioral signals that indicate reactivation potential.

### Step 3: Profile Target Customers

Copy and paste this into Snowflake Intelligence:

```
Show me 10 specific examples of at-risk high-value customers who are interested in both fitness and technology. Include their favorite product categories, shopping times, and how much they spent when they were active.
```

This query surfaces specific customer profiles to inform campaign creative, messaging, and channel strategy.

### Step 4: Build Priority Audience

Copy and paste this into Snowflake Intelligence:

```
From the fitness and technology interested group who were previously loyal customers, give me the top 1,000 ranked by predicted lifetime value. Include email, phone, preferred channel, and promotional sensitivity. Save this as HIGH_VALUE_WINBACK_CAMPAIGN_Q1.
```

This query creates a prioritized, activation-ready audience list and materializes it as a permanent table in Snowflake.

### Step 5: Model Financial Impact

Copy and paste this into Snowflake Intelligence:

```
For this 1,000-customer campaign list, what was their average order value when they were active? If we achieve a 20% win-back rate with a 30% discount offer, what's the first-year revenue impact? Is the ROI positive if our campaign costs $15,000?
```

This query calculates expected ROI with specific campaign assumptions to justify spend and secure budget approval.

<!-- ------------------------ -->
## FSI Campaign Walkthrough

### The Challenge

Your financial services institution has identified a significant opportunity: premium credit card cross-sell to qualified customers. The product team believes there's substantial untapped revenue from customers who meet all the credit criteria but haven't been offered the right product. However, they need data to identify qualified prospects, assess their financial capacity, and build a targeted campaign with ROI projections.

**Your challenge today:** Build a complete, compliance-ready premium card campaign with full ROI analysis in minutes, not weeks.

Navigate to **AI & ML > Snowflake Intelligence** and select the **FSI Customer Intelligence Agent**.

### Step 1: Identify Qualified Prospects

Copy and paste this into Snowflake Intelligence:

```
How many customers have excellent credit scores above 740, make over $100K a year, have a checking account with us, but don't have a travel rewards card yet?
```

This query sizes the qualified prospect pool by filtering across creditworthiness, income, and existing product relationships.

### Step 2: Assess Financial Capacity

Copy and paste this into Snowflake Intelligence:

```
For those qualified prospects, what's the breakdown of their credit utilization rates? Show me how many have low utilization under 30%, and what's their average net worth compared to those with higher utilization.
```

This query diagnoses which prospects have actual borrowing capacity and financial stability for a premium card.

### Step 3: Validate Marketing Readiness

Copy and paste this into Snowflake Intelligence:

```
From the low-utilization, high-net-worth group, show me 20 specific customers with their marketing propensity scores, recent transaction counts, preferred contact channels, and how long they've been customers. Who looks most engaged?
```

This query surfaces specific customer profiles to understand engagement levels, contact preferences, and relationship depth.

### Step 4: Build Campaign List

Copy and paste this into Snowflake Intelligence:

```
Give me the top 1,000 customers from the low-utilization, high-net-worth group ranked by net worth, but only include those eligible for marketing and opted in. I need email, phone, preferred contact method, and marketing propensity score. Save this as FSI_PREMIUM_CARD_Q1_PROSPECTS.
```

This query creates a compliance-ready, prioritized prospect list and materializes it as a permanent table in Snowflake.

### Step 5: Project Lifetime Value

Copy and paste this into Snowflake Intelligence:

```
If we convert 30% of these 1,000 prospects to travel rewards cardholders at $850 annual revenue each, and our campaign costs $50 per prospect to execute, what's our net first-year revenue? What about 5-year customer lifetime value?
```

This query builds a comprehensive business case with ROI projections that account for both campaign costs and long-term customer value.

<!-- ------------------------ -->
## Gaming Campaign Walkthrough

### The Challenge

Your gaming studio is preparing to launch a major expansion pack and needs to maximize day-one adoption and viral reach. The product team knows that engaged, socially connected players drive launch success, but they need data to identify the right VIP influencers, understand their purchase behavior, and build a campaign that leverages network effects for maximum amplification.

**Your challenge today:** Build a complete VIP influencer campaign with viral revenue projections in minutes, not weeks.

Navigate to **AI & ML > Snowflake Intelligence** and select the **Gaming Customer Intelligence Agent**.

### Step 1: Size Engaged Player Base

Copy and paste this into Snowflake Intelligence:

```
How many active subscribers played at least 20 hours in the last 30 days? What's their average lifetime spend compared to all subscribers?
```

This query establishes a baseline of highly engaged players to understand the addressable market for expansion pack marketing.

### Step 2: Segment Influence Tiers

Copy and paste this into Snowflake Intelligence:

```
From those engaged subscribers, how many have 15 or more in-game friends and use the companion app? Show me their breakdown by playtime: casual gamers around 10-20 hours weekly, regular players at 20-35 hours, and hardcore players over 35 hours per week.
```

This query identifies players with social reach and platform engagement to amplify launch buzz through their networks.

### Step 3: Profile VIP Candidates

Copy and paste this into Snowflake Intelligence:

```
Show me 15 specific hardcore social players from that group. For each one, show me when they bought the last expansion, how many DLCs they own, their marketing consent channels, and their friend count. Who are our best VIP candidates?
```

This query surfaces specific player profiles to identify VIP candidates and understand purchase patterns and communication preferences.

### Step 4: Create VIP List

Copy and paste this into Snowflake Intelligence:

```
From the hardcore social players who bought the last expansion within 7 days of launch, give me the top 1,000 ranked by friend count. Include gamer tag, email, phone, preferred notification channel, lifetime spend, and DLC count. Save this as EXPANSION_LAUNCH_INFLUENCERS_SPRING.
```

This query creates a prioritized VIP list ranked by social influence and materializes it as a permanent table in Snowflake.

### Step 5: Calculate Network Effects

Copy and paste this into Snowflake Intelligence:

```
If 75% of these VIPs buy the expansion at launch for $39.99, and each influences 3 friends to buy within the first month, what's our total projected revenue? Compare two scenarios: full price with standard viral effect versus 20% VIP discount with accelerated adoption and stronger network cascade. Does the viral multiplier justify the discount investment?
```

This query quantifies the viral multiplier effect and proves that incentivizing influencers generates net-positive ROI through network amplification.

<!-- ------------------------ -->
## Conclusion

Congratulations! You've completed the Building Audiences with Snowflake Cortex guide!

### What You Accomplished

- Built sophisticated audience segments across three industries using natural language
- Combined demographics, behavior, and predictive metrics without SQL
- Generated actionable contact lists for campaigns
- Saved audiences as permanent tables for activation

**Key takeaway:** Snowflake Cortex and semantic models enable self-service analytics across any domain—Retail, FSI, Gaming, or your own business.

### What You Learned

- Setting up Cortex Agents with semantic models for customer analytics
- Creating natural language interfaces for marketing audience building
- Configuring industry-specific orchestration patterns
- Materializing audience segments as permanent tables

### Related Resources

- [SFGuide GitHub Repository](https://github.com/Snowflake-Labs/sfguide-building-audiences-with-snowflake-cortex/tree/main)
- [Snowflake Cortex AI Documentation](https://docs.snowflake.com/en/guides-overview-ai-features)
- [Cortex Analyst Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Intelligence Documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/snowflake-intelligence?_ga=2.191660586.1400445987.1762962408-1322428164.1757697987&_gac=1.162580302.1762217442.CjwKCAiAwqHIBhAEEiwAx9cTedSfDOZVCiqeWnA8OzH_hIUccsg787q86tkyw4qJtQq1hrLSDqVInRoCgdsQAvD_BwE)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
