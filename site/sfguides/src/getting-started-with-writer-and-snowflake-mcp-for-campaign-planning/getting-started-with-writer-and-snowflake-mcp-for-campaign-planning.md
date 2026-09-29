author: Randy Pettus
id: getting-started-with-writer-and-snowflake-mcp-for-campaign-planning
language: en
summary: Connect WRITER to Snowflake MCP to build a campaign planning playbook grounded in customer data with governed write-back.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/snowflake-feature/connectors,snowflake-site:taxonomy/snowflake-feature/cortex-analyst,snowflake-site:taxonomy/snowflake-feature/cortex-search,snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with WRITER and Snowflake MCP for Campaign Planning
<!-- ------------------------ -->
## Overview

[WRITER](https://writer.com) is an enterprise AI platform for content generation. In this guide you will connect WRITER to Snowflake through a Snowflake-managed MCP server, building a campaign-planning playbook that grounds its recommendations in your customer data and saves the finished brief back to Snowflake through a stored procedure you control.

The MCP server exposes exactly two tools:

| Tool | Type | Purpose |
|------|------|---------|
| `campaign-planner` | `CORTEX_AGENT_RUN` | Routes questions to a semantic view (structured) or a Cortex Search service (unstructured). Snowflake owns the routing decision. |
| `save-brief` | `GENERIC` (procedure) | Writes a campaign brief to a single table through a governed stored procedure with a fixed signature. |

By the end you will have a WRITER playbook that asks a Cortex Agent which customer micro-segments to target, finds historical campaign copy that has performed well, drafts a brief, and writes it back to Snowflake — all governed by least-privileged roles and a fixed procedure contract.

### Prerequisites
- A Snowflake account with Cortex AI enabled (Enterprise or higher, or a trial)
- `ACCOUNTADMIN`, or a role that can create databases, warehouses, roles, and security integrations
- A WRITER organization with permission to add a custom MCP connector (this may require a WRITER org admin — confirm before you start)
- Basic familiarity with Snowflake and SQL

> **New to Snowflake MCP?** If you haven't set up a Snowflake MCP Server yet, follow [Getting Started with Snowflake MCP Server](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-mcp-server/) to create one with Cortex Analyst and Search tools. For guidance on building Cortex Agents, see [Best Practices to Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/).

### What You'll Learn
- How to create a Cortex Agent with both semantic view and search tools
- How to build a governed write-back path using a stored procedure exposed as an MCP tool
- How to configure OAuth for MCP server authentication
- How to connect WRITER to a Snowflake MCP server and build a playbook
- How MCP tool discovery works — WRITER discovers the procedure contract automatically

### What You'll Need
- A [Snowflake](https://signup.snowflake.com/) account (Enterprise or higher, or trial)
- A [WRITER](https://writer.com) organization with MCP connector access
- About 15 minutes

### What You'll Build
- A complete Snowflake environment with customer data, campaign history, a Cortex Agent, and an MCP server
- A WRITER playbook that plans campaigns grounded in Snowflake data and writes briefs back through a governed procedure

```
WRITER playbook
  |
  |-- campaign-planner --> WRITER_CAMPAIGN_PLANNER (Cortex Agent)
  |                          |-- CustomerAnalyst --> CUSTOMER_360_SV (semantic view)
  |                          |                        |-- CUSTOMER_360
  |                          |                        |-- MICRO_SEGMENTS
  |                          |-- CampaignSearch  --> CAMPAIGN_LIBRARY_SEARCH
  |                                                   |-- CAMPAIGN_LIBRARY
  |
  |-- save-brief ---------> SAVE_BRIEF (stored procedure)
                              |-- CAMPAIGN_BRIEFS
```

<!-- ------------------------ -->
## Environment Setup

Creates the database, schema, warehouse, and a least-privileged role that WRITER will use.

Run the pre-flight check first — it should return **0 rows**. If it returns a row, either drop the existing database or change the name consistently throughout this guide.

```sql
USE ROLE ACCOUNTADMIN;

-- Pre-flight: expect 0 rows
SHOW DATABASES LIKE 'WRITER_SF_QUICKSTART';

-- Environment
CREATE DATABASE WRITER_SF_QUICKSTART
  COMMENT = 'WRITER + Snowflake MCP quickstart';

CREATE SCHEMA WRITER_SF_QUICKSTART.MARKETING
  COMMENT = 'Apex Athletics marketing data, AI objects, and write-back target';

CREATE WAREHOUSE WRITER_QUICKSTART_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for the WRITER quickstart';

CREATE ROLE WRITER_QUICKSTART_ROLE
  COMMENT = 'MCP access role for the WRITER quickstart';

GRANT ROLE WRITER_QUICKSTART_ROLE TO ROLE SYSADMIN;

USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

SELECT
  CURRENT_DATABASE()  AS db,
  CURRENT_SCHEMA()    AS sch,
  CURRENT_WAREHOUSE() AS wh;
```

**Expected:** `WRITER_SF_QUICKSTART | MARKETING | WRITER_QUICKSTART_WH`.

Everything is created in a new `WRITER_SF_QUICKSTART` database with its own warehouse, role, and OAuth integration. Nothing existing in your account is modified, except for one `ALTER USER` in the Default Role Setup step which you will record and can revert.

<!-- ------------------------ -->
## Customer Data

Two tables power the agent's customer intelligence:

- **CUSTOMER_360** — one row per customer with behavioral metrics, RFM scoring, churn risk, and predictive scores. 5,000 rows.
- **MICRO_SEGMENTS** — customers grouped by RFM segment, churn tier, and preferred channel, scored and ranked by intent. This is what the agent reads when asked "who should I target?"

All values are generated deterministically from `HASH(SEQ4())`, so your numbers will match the ones in this guide.

> In production these would be Dynamic Tables with `TARGET_LAG`, built over a raw event stream so segment attributes refresh automatically. We use plain tables here so setup is a single paste.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

CREATE OR REPLACE TABLE CUSTOMER_360 AS
WITH
  base AS (
    SELECT
      SEQ4() AS n,
      'CUST-' || LPAD(SEQ4() + 1, 6, '0')                    AS CUSTOMER_ID,
      ABS(MOD(HASH(SEQ4(), 'fn'),   20))                     AS i_first,
      ABS(MOD(HASH(SEQ4(), 'ln'),   20))                     AS i_last,
      ABS(MOD(HASH(SEQ4(), 'geo'),  12))                     AS i_geo,
      ABS(MOD(HASH(SEQ4(), 'gen'),   3))                     AS i_gender,
      ABS(MOD(HASH(SEQ4(), 'tier'),  4))                     AS i_tier,
      ABS(MOD(HASH(SEQ4(), 'chan'),  3))                     AS i_chan,
      ABS(MOD(HASH(SEQ4(), 'cat'),   6))                     AS i_cat,
      ABS(MOD(HASH(SEQ4(), 'tenure'), 1780)) + 20            AS TENURE_DAYS,
      ABS(MOD(HASH(SEQ4(), 'pc'),    25))                    AS PURCHASE_COUNT_12M,
      ROUND(45 + ABS(MOD(HASH(SEQ4(), 'aov'), 23500)) / 100.0, 2) AS AVG_ORDER_VALUE,
      ABS(MOD(HASH(SEQ4(), 'recency'), 540)) + 1             AS DAYS_SINCE_LAST_PURCHASE,
      ABS(MOD(HASH(SEQ4(), 'ev'),   395)) + 5                AS TOTAL_EVENTS_12M,
      ABS(MOD(HASH(SEQ4(), 'ad'),   200)) + 1                AS ACTIVE_DAYS_12M,
      ABS(MOD(HASH(SEQ4(), 'tl'),   150))                    AS TRAINING_LOGS_12M,
      ABS(MOD(HASH(SEQ4(), 'goal'),  12))                    AS GOALS_SET_12M,
      ABS(MOD(HASH(SEQ4(), 'rev'),    8))                    AS REVIEWS_WRITTEN_12M,
      ABS(MOD(HASH(SEQ4(), 'ret'),    5))                    AS RETURN_COUNT_12M,
      ABS(MOD(HASH(SEQ4(), 'recv'),  49)) + 12               AS EMAILS_RECEIVED_12M,
      ABS(MOD(HASH(SEQ4(), 'pts'), 15000))                   AS LOYALTY_POINTS,
      ABS(MOD(HASH(SEQ4(), 'op'),   100))                    AS pct_open,
      ABS(MOD(HASH(SEQ4(), 'cl'),   100))                    AS pct_click,
      ABS(MOD(HASH(SEQ4(), 'cv'),   100))                    AS pct_conv,
      ABS(MOD(HASH(SEQ4(), 'opt'),  100))                    AS pct_opt
    FROM TABLE(GENERATOR(ROWCOUNT => 5000))
  ),
  derived AS (
    SELECT
      b.*,
      GET(ARRAY_CONSTRUCT('Avery','Jordan','Riley','Casey','Rowan','Quinn','Sage','Reese',
                          'Micah','Harper','Devon','Skyler','Emery','Finley','Hayden',
                          'Kendall','Logan','Parker','Tatum','Wren'), i_first)::VARCHAR AS FIRST_NAME,
      GET(ARRAY_CONSTRUCT('Nguyen','Alvarez','Okafor','Fischer','Rossi','Kowalski','Haddad',
                          'Silva','Novak','Petrov','Dubois','Larsen','Moreau','Costa','Bauer',
                          'Ivanov','Mendes','Sorensen','Vargas','Weber'), i_last)::VARCHAR AS LAST_NAME,
      GET(ARRAY_CONSTRUCT('Portland','Austin','Denver','Boston','Seattle','Chicago','Atlanta',
                          'Phoenix','Nashville','Minneapolis','San Diego','Philadelphia'), i_geo)::VARCHAR AS CITY,
      GET(ARRAY_CONSTRUCT('OR','TX','CO','MA','WA','IL','GA','AZ','TN','MN','CA','PA'), i_geo)::VARCHAR AS STATE,
      GET(ARRAY_CONSTRUCT('West','South','West','Northeast','West','Midwest','South',
                          'West','South','Midwest','West','Northeast'), i_geo)::VARCHAR AS REGION,
      GET(ARRAY_CONSTRUCT('female','male','nonbinary'), i_gender)::VARCHAR             AS GENDER,
      GET(ARRAY_CONSTRUCT('Starter','Active','Performance','Elite'), i_tier)::VARCHAR  AS LOYALTY_TIER_NAME,
      GET(ARRAY_CONSTRUCT('email','push','sms'), i_chan)::VARCHAR                      AS PREFERRED_CHANNEL,
      GET(ARRAY_CONSTRUCT('Running','Yoga','Training','Outdoor','Recovery','Cycling'), i_cat)::VARCHAR AS TOP_CATEGORY,
      (pct_opt < 78)                                                                   AS MARKETING_OPT_IN,
      DATEADD(day, -TENURE_DAYS, CURRENT_DATE())                                       AS SIGNUP_DATE,
      CASE WHEN PURCHASE_COUNT_12M = 0 THEN NULL
           ELSE DATEADD(day, -DAYS_SINCE_LAST_PURCHASE, CURRENT_DATE()) END            AS LAST_PURCHASE_DATE,
      ROUND(PURCHASE_COUNT_12M * AVG_ORDER_VALUE, 2)                                   AS TOTAL_SPEND_12M,
      PURCHASE_COUNT_12M * (1 + ABS(MOD(HASH(n, 'cart'), 4)))                          AS CART_ADD_COUNT_12M,
      FLOOR(EMAILS_RECEIVED_12M * (pct_open / 100.0))                                  AS EMAIL_OPENS_12M
    FROM base b
  ),
  derived2 AS (
    SELECT
      d.*,
      FLOOR(EMAIL_OPENS_12M * (pct_click / 100.0))                                     AS EMAIL_CLICKS_12M,
      ROUND(50 + ABS(MOD(HASH(n, 'annual'), 245000)) / 100.0, 2)                       AS ANNUAL_SPEND
    FROM derived d
  ),
  derived3 AS (
    SELECT
      d.*,
      FLOOR(EMAIL_CLICKS_12M * (pct_conv / 100.0))                                     AS CAMPAIGN_CONVERSIONS_12M
    FROM derived2 d
  ),
  rfm AS (
    SELECT
      n,
      NTILE(5) OVER (ORDER BY DAYS_SINCE_LAST_PURCHASE DESC) AS R_SCORE,
      NTILE(5) OVER (ORDER BY PURCHASE_COUNT_12M ASC)        AS F_SCORE,
      NTILE(5) OVER (ORDER BY TOTAL_SPEND_12M ASC)           AS M_SCORE
    FROM derived3
  )
SELECT
  d.CUSTOMER_ID, d.FIRST_NAME, d.LAST_NAME,
  LOWER(d.FIRST_NAME || '.' || d.LAST_NAME || d.n || '@example.com')  AS EMAIL,
  d.GENDER, d.CITY, d.STATE, d.REGION,
  d.LOYALTY_TIER_NAME, d.PREFERRED_CHANNEL, d.TOP_CATEGORY, d.MARKETING_OPT_IN,
  d.SIGNUP_DATE, d.LAST_PURCHASE_DATE, d.TENURE_DAYS, d.DAYS_SINCE_LAST_PURCHASE,
  d.ANNUAL_SPEND, d.LOYALTY_POINTS,
  d.PURCHASE_COUNT_12M, d.TOTAL_SPEND_12M, d.AVG_ORDER_VALUE,
  d.CART_ADD_COUNT_12M, d.RETURN_COUNT_12M,
  d.TOTAL_EVENTS_12M, d.ACTIVE_DAYS_12M, d.TRAINING_LOGS_12M,
  d.EMAILS_RECEIVED_12M, d.EMAIL_OPENS_12M, d.EMAIL_CLICKS_12M,
  d.CAMPAIGN_CONVERSIONS_12M,
  ROUND(d.CAMPAIGN_CONVERSIONS_12M * (35 + ABS(MOD(HASH(d.n, 'crev'), 245))), 2) AS CAMPAIGN_REVENUE_12M,
  CASE WHEN d.EMAILS_RECEIVED_12M > 0
       THEN ROUND(d.EMAIL_OPENS_12M / d.EMAILS_RECEIVED_12M, 4) ELSE 0 END   AS EMAIL_OPEN_RATE,
  CASE WHEN d.EMAIL_OPENS_12M > 0
       THEN ROUND(d.EMAIL_CLICKS_12M / d.EMAIL_OPENS_12M, 4) ELSE 0 END      AS EMAIL_CLICK_RATE,
  CASE WHEN d.EMAILS_RECEIVED_12M > 0
       THEN ROUND(d.CAMPAIGN_CONVERSIONS_12M / d.EMAILS_RECEIVED_12M, 4) ELSE 0 END AS CAMPAIGN_CONVERSION_RATE,
  r.R_SCORE, r.F_SCORE, r.M_SCORE,
  ROUND((r.R_SCORE + r.F_SCORE + r.M_SCORE) / 3.0, 2) AS RFM_COMPOSITE_SCORE,
  CASE
    WHEN r.R_SCORE >= 4 AND r.F_SCORE >= 4 THEN 'Champion'
    WHEN r.R_SCORE >= 3 AND r.F_SCORE >= 3 THEN 'Loyal'
    WHEN r.R_SCORE >= 4 AND r.F_SCORE <  3 THEN 'Recent'
    WHEN r.R_SCORE <  2 AND r.F_SCORE >= 4 THEN 'At Risk'
    WHEN r.R_SCORE <  2 AND r.F_SCORE <  2 THEN 'Dormant'
    WHEN r.R_SCORE >= 3                    THEN 'Potential'
    WHEN r.F_SCORE >= 3                    THEN 'Needs Attention'
    ELSE 'New'
  END AS RFM_SEGMENT,
  CASE
    WHEN d.LAST_PURCHASE_DATE IS NULL OR d.DAYS_SINCE_LAST_PURCHASE > 180 THEN 'High'
    WHEN d.DAYS_SINCE_LAST_PURCHASE > 90 THEN 'Medium'
    ELSE 'Low'
  END AS CHURN_RISK_TIER,
  LEAST(100, ROUND(
    d.ACTIVE_DAYS_12M * 0.15 + d.TRAINING_LOGS_12M * 0.20 +
    d.GOALS_SET_12M * 1.20 + d.REVIEWS_WRITTEN_12M * 1.50 +
    d.PURCHASE_COUNT_12M * 0.60
  , 1)) AS ENGAGEMENT_SCORE,
  LEAST(100, ROUND(
    d.DAYS_SINCE_LAST_PURCHASE * 0.15 +
    GREATEST(0, 30 - d.ACTIVE_DAYS_12M) * 0.5 +
    d.RETURN_COUNT_12M * 2.0
  , 1)) AS CHURN_RISK_SCORE,
  ROUND(GREATEST(d.TOTAL_SPEND_12M, d.ANNUAL_SPEND * 0.5), 2) AS LTV_ANNUALIZED,
  LEAST(100, ROUND(
    r.R_SCORE * 5 + r.F_SCORE * 5 + r.M_SCORE * 5 +
    d.ACTIVE_DAYS_12M * 0.06 + d.TRAINING_LOGS_12M * 0.05
  , 1)) AS CUSTOMER_HEALTH_SCORE,
  ROUND(d.AVG_ORDER_VALUE * (1 + d.i_tier * 0.25) * 2.5, 2) AS REVENUE_OPPORTUNITY_SCORE
FROM derived3 d
JOIN rfm r ON r.n = d.n;

-- MICRO_SEGMENTS
CREATE OR REPLACE TABLE MICRO_SEGMENTS AS
WITH
  segment_base AS (
    SELECT
      RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL,
      COUNT(*) AS CUSTOMER_COUNT,
      ROUND(AVG(ANNUAL_SPEND), 2) AS AVG_SPEND,
      ROUND(AVG(ENGAGEMENT_SCORE), 2) AS AVG_ENGAGEMENT_SCORE,
      ROUND(AVG(CAMPAIGN_CONVERSION_RATE), 4) AS AVG_CAMPAIGN_CONVERSION_RATE,
      ROUND(AVG(LTV_ANNUALIZED), 2) AS AVG_LTV_ANNUALIZED,
      ROUND(SUM(REVENUE_OPPORTUNITY_SCORE), 2) AS TOTAL_REVENUE_OPPORTUNITY
    FROM CUSTOMER_360
    GROUP BY RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL
    HAVING COUNT(*) >= 30
  ),
  ranked AS (
    SELECT
      ROW_NUMBER() OVER (
        ORDER BY TOTAL_REVENUE_OPPORTUNITY DESC, AVG_ENGAGEMENT_SCORE DESC
      ) AS SEGMENT_ID,
      RFM_SEGMENT || ' / ' || CHURN_RISK_TIER || ' Churn / ' || UPPER(PREFERRED_CHANNEL) AS SEGMENT_NAME,
      RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL,
      CUSTOMER_COUNT, AVG_SPEND, AVG_ENGAGEMENT_SCORE,
      AVG_CAMPAIGN_CONVERSION_RATE, AVG_LTV_ANNUALIZED,
      TOTAL_REVENUE_OPPORTUNITY,
      ROUND(
        60.5 + (
          (RANK() OVER (ORDER BY
             TOTAL_REVENUE_OPPORTUNITY * 0.4 +
             AVG_ENGAGEMENT_SCORE * 0.35 +
             AVG_LTV_ANNUALIZED * 0.25
          ) - 1) / NULLIF(COUNT(*) OVER () - 1, 0) * 22.4
        ), 1
      ) AS INTENT_SCORE
    FROM segment_base
  )
SELECT * FROM ranked ORDER BY INTENT_SCORE DESC;

-- Verify
SELECT
  (SELECT COUNT(*) FROM CUSTOMER_360)   AS customers,
  (SELECT COUNT(*) FROM MICRO_SEGMENTS) AS segments;
```

**Expected:** 5,000 customers and 42 segments. Run a quick sanity check to confirm scores spread across their bands rather than pinning at 100:

```sql
SELECT
  ROUND(AVG(ENGAGEMENT_SCORE), 1)        AS avg_engagement,
  ROUND(STDDEV(ENGAGEMENT_SCORE), 1)     AS sd_engagement,
  COUNT_IF(ENGAGEMENT_SCORE >= 100)      AS engagement_at_ceiling,
  ROUND(AVG(CUSTOMER_HEALTH_SCORE), 1)   AS avg_health,
  COUNT_IF(CUSTOMER_HEALTH_SCORE >= 100) AS health_at_ceiling,
  ROUND(AVG(CHURN_RISK_SCORE), 1)        AS avg_churn
FROM CUSTOMER_360;
```

**Expected:** Averages in the 40-60 range with a standard deviation above 10, and 0 rows at either ceiling.

<!-- ------------------------ -->
## Campaign Library

60 historical campaigns with subject lines, body copy, CTAs, and performance metrics. This is what the agent searches when asked "what has worked for this audience before?"

The copy is built from 20 coherent campaign themes, each crossed with 3 audience and channel variants. Performance tier is derived from the generated rates, so "top-performing campaigns" queries return rows whose numbers actually support the label.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

CREATE OR REPLACE TABLE CAMPAIGN_LIBRARY (
  CAMPAIGN_ID        VARCHAR(15)  NOT NULL,
  CAMPAIGN_NAME      VARCHAR(100) NOT NULL,
  BRIEF_ID           VARCHAR(20),
  TARGET_SEGMENT     VARCHAR(100),
  CAMPAIGN_TYPE      VARCHAR(30)  NOT NULL,
  CHANNEL            VARCHAR(20)  NOT NULL,
  SUBJECT_LINE       VARCHAR(200),
  BODY_PREVIEW       VARCHAR(500),
  CTA_TEXT           VARCHAR(100),
  TONE               VARCHAR(50),
  PERFORMANCE_TIER   VARCHAR(20),
  OPEN_RATE          NUMBER(5,4),
  CLICK_RATE         NUMBER(5,4),
  CONVERSION_RATE    NUMBER(5,4),
  REVENUE_GENERATED  NUMBER(12,2),
  CREATED_DATE       DATE,
  LAST_USED_DATE     DATE,
  TAGS               VARCHAR(500)
);

INSERT INTO CAMPAIGN_LIBRARY
WITH
  themes AS (
    SELECT * FROM VALUES
      ('Winter_Running_Layers', 'seasonal', 'confident',
       'Your cold-weather running kit is here',
       'Temperatures are dropping but your training does not have to. Our thermal layering system keeps core heat in and moisture out, so mile ten feels like mile one. Built for runners who do not wait for spring.',
       'Shop winter running', 'winter,running,layering,thermal,cold-weather,seasonal'),
      ('Yoga_Mobility_Restore', 'lifecycle', 'calm',
       'A gentler practice for recovery days',
       'Not every session needs to be intense. Our mobility and restorative yoga collection is designed for the days between hard efforts, with mats and props that support slower, deliberate movement.',
       'Explore mobility gear', 'yoga,mobility,recovery,restorative,rest-day,wellness'),
      ('Marathon_16_Week_Block', 'engagement', 'motivating',
       'Sixteen weeks to your marathon start line',
       'Race day is closer than it feels. This training block breaks the next sixteen weeks into build, peak, and taper phases, with the gear checkpoints that matter at each stage.',
       'Start the plan', 'marathon,training,endurance,running,race-prep,plan'),
      ('Cart_Recovery_Nudge', 'transactional', 'helpful',
       'You left something in your bag',
       'Your items are still saved. Sizes on some of these move quickly, so we are holding your selection for a little longer in case you want to finish checking out.',
       'Complete your order', 'cart-abandonment,recovery,transactional,reminder,checkout'),
      ('Elite_Tier_Unlock', 'loyalty', 'exclusive',
       'You have unlocked Elite status',
       'Your Elite benefits are now active: early access to launches, free expedited shipping, and a dedicated gear consultation. Thank you for training with us this year.',
       'View Elite benefits', 'loyalty,tier-upgrade,elite,rewards,retention,vip'),
      ('New_Member_Welcome', 'welcome', 'warm',
       'Welcome to Apex Athletics',
       'Glad you are here. Tell us what you train for and we will point you to the gear that fits, plus the training content that is actually relevant to your sport.',
       'Set your preferences', 'welcome,onboarding,new-member,preferences,lifecycle'),
      ('Winback_Lapsed_Athlete', 'winback', 'direct',
       'It has been a while since your last session',
       'Training gets interrupted, that is normal. Here is what has changed since your last visit, and a fresh look at the categories you used to shop most.',
       'See what is new', 'winback,lapsed,re-engagement,churn-risk,retention'),
      ('Gear_Review_Request', 'engagement', 'appreciative',
       'How is your new gear holding up?',
       'You have had a few weeks with it now. A short review helps other athletes choose well, and tells us what to build next.',
       'Write a review', 'review,feedback,post-purchase,ugc,engagement'),
      ('Season_End_Clearance', 'promotional', 'urgent',
       'Final markdowns on last season styles',
       'These are the last units in most sizes. Same construction, same materials, previous season colorways at a reduced price.',
       'Shop clearance', 'clearance,promotional,discount,seasonal,inventory'),
      ('Cycling_Collection_Launch', 'launch', 'bold',
       'The cycling collection just landed',
       'Bib shorts with a chamois we tested over nine thousand combined miles, jerseys that hold shape in the drops, and a wind shell that packs into its own pocket.',
       'Shop cycling', 'cycling,launch,new-arrival,bike,collection'),
      ('Sleep_Recovery_Focus', 'lifecycle', 'calm',
       'Recovery is part of the training',
       'Sleep and rest are where adaptation actually happens. Our recovery line covers compression, sleep-friendly fabrics, and the tools that help you take rest days seriously.',
       'Explore recovery', 'recovery,sleep,rest,compression,wellness,adaptation'),
      ('Trail_Outdoor_Exploration', 'seasonal', 'adventurous',
       'Take your training off the pavement',
       'Trail running asks different things of your gear. Grippier outsoles, more durable uppers, and packs sized for longer unsupported efforts.',
       'Shop trail', 'trail,outdoor,hiking,off-road,adventure,running'),
      ('Strength_Fundamentals', 'engagement', 'instructive',
       'Build the strength base your sport needs',
       'Endurance athletes often skip strength work and pay for it later. Start with these fundamentals: three movements, twice a week, minimal equipment.',
       'Get the routine', 'strength,training,fundamentals,cross-training,education'),
      ('Hydration_Nutrition_Guide', 'engagement', 'instructive',
       'Dial in your hydration strategy',
       'Most athletes underestimate fluid loss in cool weather. This guide covers sweat rate testing, electrolyte timing, and what to carry on longer efforts.',
       'Read the guide', 'hydration,nutrition,electrolytes,education,performance'),
      ('Race_Day_Checklist', 'lifecycle', 'reassuring',
       'Your race day checklist',
       'Nothing new on race day. Here is the gear to lay out the night before, the timing for your warmup, and the small things athletes most often forget.',
       'View checklist', 'race-day,checklist,preparation,event,running'),
      ('Sustainable_Materials_Story', 'engagement', 'thoughtful',
       'Where our recycled fabrics come from',
       'Sixty-two percent of our fabric volume is now recycled content. Here is the supply chain behind that number, and the parts of it we are still working on.',
       'Read the story', 'sustainability,recycled,materials,transparency,brand'),
      ('Referral_Invite', 'referral', 'friendly',
       'Bring a training partner',
       'Training with someone else makes it stick. Share your referral link and you both get credit toward your next order.',
       'Share your link', 'referral,advocacy,word-of-mouth,growth,rewards'),
      ('Birthday_Reward', 'loyalty', 'celebratory',
       'A little something for your birthday',
       'Happy birthday from all of us. Your reward is loaded and ready to use on anything in the store for the next thirty days.',
       'Use your reward', 'birthday,reward,loyalty,milestone,retention'),
      ('Back_In_Stock_Alert', 'transactional', 'helpful',
       'Back in stock in your size',
       'The item you were watching is available again. Restocks in popular sizes tend not to last, so we wanted you to know first.',
       'Shop now', 'restock,back-in-stock,inventory,alert,transactional'),
      ('Community_Step_Challenge', 'engagement', 'motivating',
       'Join the thirty day movement challenge',
       'Log your sessions alongside eleven thousand other athletes. Any activity counts, and there are milestone rewards at ten, twenty, and thirty days.',
       'Join the challenge', 'challenge,community,engagement,gamification,movement')
    AS t(THEME, CAMPAIGN_TYPE, TONE, SUBJECT_LINE, BODY_PREVIEW, CTA_TEXT, TAGS)
  ),
  variants AS (
    SELECT * FROM VALUES
      (0, 'Champion',        'email'),
      (1, 'At Risk',         'push'),
      (2, 'Needs Attention', 'sms')
    AS v(V, TARGET_SEGMENT, CHANNEL)
  ),
  numbered AS (
    SELECT
      t.*, v.V, v.TARGET_SEGMENT, v.CHANNEL,
      ROW_NUMBER() OVER (ORDER BY t.THEME, v.V) AS rn
    FROM themes t CROSS JOIN variants v
  ),
  scored AS (
    SELECT
      n.*,
      ROUND(0.18 + ABS(MOD(HASH(rn, 'open'), 4200)) / 10000.0, 4) AS OPEN_RATE,
      ROUND((0.18 + ABS(MOD(HASH(rn, 'open'), 4200)) / 10000.0)
            * (0.12 + ABS(MOD(HASH(rn, 'ctr'), 2800)) / 10000.0), 4) AS CLICK_RATE,
      ROUND((0.18 + ABS(MOD(HASH(rn, 'open'), 4200)) / 10000.0)
            * (0.12 + ABS(MOD(HASH(rn, 'ctr'), 2800)) / 10000.0)
            * (0.08 + ABS(MOD(HASH(rn, 'cvr'), 2700)) / 10000.0), 4) AS CONVERSION_RATE
    FROM numbered n
  ),
  tiered AS (
    SELECT s.*,
      NTILE(4) OVER (ORDER BY CONVERSION_RATE DESC) AS tier_q
    FROM scored s
  )
SELECT
  'CMP-2025-' || LPAD(rn, 3, '0') AS CAMPAIGN_ID,
  THEME || '_' || UPPER(CHANNEL) AS CAMPAIGN_NAME,
  'BRF-H' || LPAD(rn, 3, '0') AS BRIEF_ID,
  TARGET_SEGMENT, CAMPAIGN_TYPE, CHANNEL, SUBJECT_LINE, BODY_PREVIEW, CTA_TEXT, TONE,
  CASE tier_q
    WHEN 1 THEN 'Elite' WHEN 2 THEN 'Performance'
    WHEN 3 THEN 'Active' ELSE 'Starter'
  END AS PERFORMANCE_TIER,
  OPEN_RATE, CLICK_RATE, CONVERSION_RATE,
  ROUND(CONVERSION_RATE * (180000 + ABS(MOD(HASH(rn, 'rev'), 520000))), 2) AS REVENUE_GENERATED,
  DATEADD(day, -(400 - rn * 5), CURRENT_DATE()) AS CREATED_DATE,
  DATEADD(day, -(90 - ABS(MOD(HASH(rn, 'used'), 80))), CURRENT_DATE()) AS LAST_USED_DATE,
  TAGS
FROM tiered;

-- Verify
SELECT
  COUNT(*) AS campaigns,
  COUNT(DISTINCT SUBJECT_LINE) AS distinct_subjects,
  COUNT(DISTINCT CAMPAIGN_TYPE) AS types,
  COUNT(DISTINCT CHANNEL) AS channels,
  COUNT(DISTINCT PERFORMANCE_TIER) AS tiers,
  COUNT_IF(BODY_PREVIEW IS NULL) AS null_body,
  COUNT_IF(CONVERSION_RATE > CLICK_RATE OR CLICK_RATE > OPEN_RATE) AS bad_funnel
FROM CAMPAIGN_LIBRARY;
```

**Expected:** 60 campaigns, 20 distinct subject lines, 10 types, 3 channels, 4 tiers, and 0 for both `null_body` and `bad_funnel`.

<!-- ------------------------ -->
## Write-Back Contract

This is the governed half of the integration: one target table and one stored procedure.

**CAMPAIGN_BRIEFS** starts empty — it is the write target, nothing else. **SAVE_BRIEF** is the only way anything reaches that table from outside Snowflake.

| Constraint | Effect |
|------------|--------|
| Two `VARCHAR` parameters, fixed | No arbitrary column list, no extra tables |
| `MERGE` on `BRIEF_ID` | Re-saving the same brief updates it; no duplicate rows |
| `PARSE_JSON` into one `VARIANT` column | Structure is the caller's, but it lands in one typed place |
| `BRIEF_ID` generated server-side when absent | Callers cannot collide or overwrite by guessing |
| One target table | Cannot reach `CUSTOMER_360`, `MICRO_SEGMENTS`, or `CAMPAIGN_LIBRARY` |
| `EXECUTE AS CALLER` | The caller's own grants still apply — no privilege escalation |

> `P_BRIEF_JSON` must be a `VARCHAR` — this is a platform constraint. Snowflake does not support custom MCP or agent tools with a parameter of type `object`. The brief crosses the MCP boundary serialized as a string, and `PARSE_JSON` inside the procedure turns it back into structure.

> `CREATE OR REPLACE TABLE` drops every grant on that table. If you go back and re-run an earlier step, re-run this step's grants afterward.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

-- CAMPAIGN_BRIEFS — starts empty
CREATE OR REPLACE TABLE CAMPAIGN_BRIEFS (
  BRIEF_ID      VARCHAR(50)   NOT NULL,
  CAMPAIGN_ID   VARCHAR(30),
  STATUS        VARCHAR(20)   DEFAULT 'draft',
  CREATED_BY    VARCHAR(100),
  CREATED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  APPROVED_AT   TIMESTAMP_NTZ,
  BRIEF_CONTENT VARIANT
)
COMMENT = 'Campaign briefs written back from WRITER through SAVE_BRIEF';

-- SAVE_BRIEF — the governed write path
CREATE OR REPLACE PROCEDURE SAVE_BRIEF(
  P_CAMPAIGN_ID VARCHAR,
  P_BRIEF_JSON  VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Upserts a campaign brief into CAMPAIGN_BRIEFS. Returns the BRIEF_ID.'
EXECUTE AS CALLER
AS
$$
DECLARE
  v_brief_id  VARCHAR;
  v_brief_obj VARIANT;
BEGIN
  v_brief_obj := PARSE_JSON(:P_BRIEF_JSON);

  v_brief_id := COALESCE(
    v_brief_obj:brief_id::VARCHAR,
    'BRF-' || REPLACE(:P_CAMPAIGN_ID, 'CMP-', '') || '-' ||
      TO_CHAR(CURRENT_TIMESTAMP(), 'HH24MISS')
  );

  MERGE INTO CAMPAIGN_BRIEFS tgt
  USING (SELECT :v_brief_id AS BRIEF_ID) src
    ON (tgt.BRIEF_ID = src.BRIEF_ID)
  WHEN MATCHED THEN UPDATE SET
    CAMPAIGN_ID   = :P_CAMPAIGN_ID,
    STATUS        = COALESCE(:v_brief_obj:status::VARCHAR, 'draft'),
    CREATED_BY    = :v_brief_obj:created_by::VARCHAR,
    BRIEF_CONTENT = :v_brief_obj
  WHEN NOT MATCHED THEN INSERT (
    BRIEF_ID, CAMPAIGN_ID, STATUS, CREATED_BY, CREATED_AT, BRIEF_CONTENT
  ) VALUES (
    :v_brief_id,
    :P_CAMPAIGN_ID,
    COALESCE(:v_brief_obj:status::VARCHAR, 'draft'),
    :v_brief_obj:created_by::VARCHAR,
    CURRENT_TIMESTAMP(),
    :v_brief_obj
  );

  RETURN :v_brief_id;
END;
$$;

-- GRANTS
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON WAREHOUSE WRITER_QUICKSTART_WH        TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON DATABASE WRITER_SF_QUICKSTART         TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON SCHEMA WRITER_SF_QUICKSTART.MARKETING TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE CUSTOMER_360     TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE MICRO_SEGMENTS   TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT ON TABLE CAMPAIGN_LIBRARY TO ROLE WRITER_QUICKSTART_ROLE;
GRANT SELECT, INSERT, UPDATE ON TABLE CAMPAIGN_BRIEFS TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON PROCEDURE SAVE_BRIEF(VARCHAR, VARCHAR) TO ROLE WRITER_QUICKSTART_ROLE;

-- Smoke test as the actual role
USE ROLE WRITER_QUICKSTART_ROLE;
USE SECONDARY ROLES NONE;
USE WAREHOUSE WRITER_QUICKSTART_WH;
USE SCHEMA WRITER_SF_QUICKSTART.MARKETING;

CALL SAVE_BRIEF('CMP-TEST-001', '{"brief_id":"BRF-SMOKE-001","status":"draft","created_by":"setup smoke test","title":"Smoke test brief"}');

CALL SAVE_BRIEF('CMP-TEST-001', '{"brief_id":"BRF-SMOKE-001","status":"approved","created_by":"setup smoke test","title":"Smoke test brief, revised"}');

SELECT BRIEF_ID, CAMPAIGN_ID, STATUS, CREATED_BY,
       BRIEF_CONTENT:title::VARCHAR AS title
FROM CAMPAIGN_BRIEFS;

-- Clean up
USE ROLE ACCOUNTADMIN;
DELETE FROM CAMPAIGN_BRIEFS WHERE BRIEF_ID = 'BRF-SMOKE-001';
SELECT COUNT(*) AS should_be_zero FROM CAMPAIGN_BRIEFS;
```

**Expected:** Both `CALL` statements return `BRF-SMOKE-001`. The `SELECT` shows one row with status `approved` — proving the `MERGE` updated rather than inserting a duplicate. Final count is 0.

<!-- ------------------------ -->
## AI Layer

Four objects: a Cortex Search service, a semantic view, the agent, and the MCP server.

> The two YAML specs in this block are whitespace-sensitive. They are passed inside `$$ ... $$` and parsed as YAML. If your editor re-indents on paste you will get a parse error.

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

-- Cortex Search over campaign copy
CREATE OR REPLACE CORTEX SEARCH SERVICE CAMPAIGN_LIBRARY_SEARCH
  ON SEARCH_CONTENT
  ATTRIBUTES CAMPAIGN_ID, CAMPAIGN_NAME, TARGET_SEGMENT, CAMPAIGN_TYPE, CHANNEL, TONE, PERFORMANCE_TIER
  WAREHOUSE = WRITER_QUICKSTART_WH
  TARGET_LAG = '1 hour'
  EMBEDDING_MODEL = 'snowflake-arctic-embed-m-v1.5'
  COMMENT = 'Searchable index of 60 historical Apex Athletics campaigns'
  AS
    SELECT
      CAMPAIGN_ID, CAMPAIGN_NAME, TARGET_SEGMENT, CAMPAIGN_TYPE, CHANNEL, TONE,
      PERFORMANCE_TIER, OPEN_RATE, CLICK_RATE, CONVERSION_RATE, REVENUE_GENERATED,
      SUBJECT_LINE || ' ' ||
      COALESCE(BODY_PREVIEW, '') || ' ' ||
      COALESCE(CTA_TEXT, '') || ' ' ||
      'Tone: ' || COALESCE(TONE, '') || '. ' ||
      'Campaign type: ' || CAMPAIGN_TYPE || '. ' ||
      'Channel: ' || CHANNEL || '. ' ||
      'Target segment: ' || COALESCE(TARGET_SEGMENT, '') || '. ' ||
      'Performance tier: ' || COALESCE(PERFORMANCE_TIER, '') || '. ' ||
      'Tags: ' || COALESCE(TAGS, '') AS SEARCH_CONTENT
    FROM CAMPAIGN_LIBRARY;

-- Semantic view over customer data
CREATE OR REPLACE SEMANTIC VIEW CUSTOMER_360_SV
  TABLES (
    c AS CUSTOMER_360
      PRIMARY KEY (CUSTOMER_ID),
    s AS MICRO_SEGMENTS
      PRIMARY KEY (SEGMENT_ID)
      UNIQUE (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
  )
  RELATIONSHIPS (
    c (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
    REFERENCES s (RFM_SEGMENT, CHURN_RISK_TIER, PREFERRED_CHANNEL)
  )
  FACTS (
    c.ANNUAL_SPEND             AS ANNUAL_SPEND             COMMENT = 'Annual spend from profile',
    c.TOTAL_SPEND_12M          AS TOTAL_SPEND_12M          COMMENT = 'Total spend last 12 months',
    c.AVG_ORDER_VALUE          AS AVG_ORDER_VALUE          COMMENT = 'Average order value (12 months)',
    c.LOYALTY_POINTS           AS LOYALTY_POINTS           COMMENT = 'Current loyalty points balance',
    c.PURCHASE_COUNT_12M       AS PURCHASE_COUNT_12M       COMMENT = 'Purchases last 12 months',
    c.CART_ADD_COUNT_12M       AS CART_ADD_COUNT_12M       COMMENT = 'Cart adds last 12 months',
    c.TOTAL_EVENTS_12M         AS TOTAL_EVENTS_12M         COMMENT = 'Total behavioral events last 12 months',
    c.ACTIVE_DAYS_12M          AS ACTIVE_DAYS_12M          COMMENT = 'Active days last 12 months',
    c.TRAINING_LOGS_12M        AS TRAINING_LOGS_12M        COMMENT = 'Training logs last 12 months',
    c.EMAIL_OPENS_12M          AS EMAIL_OPENS_12M          COMMENT = 'Emails opened last 12 months',
    c.EMAIL_CLICKS_12M         AS EMAIL_CLICKS_12M         COMMENT = 'Email clicks last 12 months',
    c.CAMPAIGN_CONVERSIONS_12M AS CAMPAIGN_CONVERSIONS_12M COMMENT = 'Campaign conversions last 12 months',
    c.CAMPAIGN_REVENUE_12M     AS CAMPAIGN_REVENUE_12M     COMMENT = 'Campaign revenue last 12 months',
    c.TENURE_DAYS              AS TENURE_DAYS              COMMENT = 'Days since customer signup',
    c.DAYS_SINCE_LAST_PURCHASE AS DAYS_SINCE_LAST_PURCHASE COMMENT = 'Days since last purchase',
    c.LTV_ANNUALIZED           AS LTV_ANNUALIZED           COMMENT = 'Annualized customer lifetime value',
    c.ENGAGEMENT_SCORE         AS ENGAGEMENT_SCORE         COMMENT = 'Engagement score (0-100)',
    s.TOTAL_REVENUE_OPPORTUNITY AS TOTAL_REVENUE_OPPORTUNITY COMMENT = 'Total revenue opportunity for segment'
  )
  DIMENSIONS (
    c.CUSTOMER_ID        AS CUSTOMER_ID        COMMENT = 'Unique customer identifier (CUST-NNNNNN)',
    c.FIRST_NAME         AS FIRST_NAME         COMMENT = 'Customer first name',
    c.LAST_NAME          AS LAST_NAME          COMMENT = 'Customer last name',
    c.EMAIL              AS EMAIL              COMMENT = 'Customer email address',
    c.GENDER             AS GENDER             COMMENT = 'Gender',
    c.CITY               AS CITY               COMMENT = 'City of residence',
    c.STATE              AS STATE              COMMENT = 'US state',
    c.REGION             AS REGION             COMMENT = 'Geographic region',
    c.LOYALTY_TIER_NAME  AS LOYALTY_TIER_NAME  COMMENT = 'Loyalty tier: Starter/Active/Performance/Elite',
    c.PREFERRED_CHANNEL  AS PREFERRED_CHANNEL  COMMENT = 'Preferred channel (email/push/sms)',
    c.TOP_CATEGORY       AS TOP_CATEGORY       COMMENT = 'Top product category (Running/Yoga/Training/Outdoor/Recovery/Cycling)',
    c.MARKETING_OPT_IN   AS MARKETING_OPT_IN   COMMENT = 'Opted in to marketing',
    c.RFM_SEGMENT        AS RFM_SEGMENT        COMMENT = 'RFM segment (Champion/Loyal/Recent/At Risk/Dormant/Potential/Needs Attention/New)',
    c.CHURN_RISK_TIER    AS CHURN_RISK_TIER    COMMENT = 'Churn risk tier (High/Medium/Low)',
    c.SIGNUP_DATE        AS SIGNUP_DATE        COMMENT = 'Date customer joined Apex Athletics',
    c.LAST_PURCHASE_DATE AS LAST_PURCHASE_DATE COMMENT = 'Date of most recent purchase',
    s.SEGMENT_ID         AS SEGMENT_ID         COMMENT = 'Micro-segment ID',
    s.SEGMENT_NAME       AS SEGMENT_NAME       COMMENT = 'Full micro-segment name'
  )
  METRICS (
    c.AVG_ENGAGEMENT_SCORE   AS AVG(ENGAGEMENT_SCORE)          COMMENT = 'Average engagement score (0-100)',
    c.AVG_CHURN_RISK         AS AVG(CHURN_RISK_SCORE)          COMMENT = 'Average churn risk score (0-100)',
    c.AVG_HEALTH_SCORE       AS AVG(CUSTOMER_HEALTH_SCORE)     COMMENT = 'Average customer health score',
    c.AVG_LTV                AS AVG(LTV_ANNUALIZED)            COMMENT = 'Average annualized LTV',
    c.TOTAL_LTV              AS SUM(LTV_ANNUALIZED)            COMMENT = 'Total annualized LTV',
    c.TOTAL_REVENUE_OPP      AS SUM(REVENUE_OPPORTUNITY_SCORE) COMMENT = 'Total revenue opportunity',
    c.TOTAL_CAMPAIGN_REVENUE AS SUM(CAMPAIGN_REVENUE_12M)      COMMENT = 'Total campaign revenue last 12 months',
    c.AVG_EMAIL_OPEN_RATE    AS AVG(EMAIL_OPEN_RATE)           COMMENT = 'Average email open rate',
    c.AVG_CLICK_RATE         AS AVG(EMAIL_CLICK_RATE)          COMMENT = 'Average email click-through rate',
    c.AVG_CONVERSION_RATE    AS AVG(CAMPAIGN_CONVERSION_RATE)  COMMENT = 'Average campaign conversion rate',
    c.CUSTOMER_COUNT         AS COUNT(CUSTOMER_ID)             COMMENT = 'Number of distinct customers',
    s.AVG_INTENT_SCORE       AS AVG(INTENT_SCORE)              COMMENT = 'Average segment intent score (60.5-82.9)'
  )
  COMMENT = 'Apex Athletics customer intelligence: CUSTOMER_360 + MICRO_SEGMENTS, 18 dimensions, 18 facts, 12 metrics';

-- Cortex Agent
CREATE OR REPLACE AGENT WRITER_CAMPAIGN_PLANNER
  COMMENT = 'Apex Athletics campaign planning agent for the WRITER quickstart'
  PROFILE = '{"display_name": "WRITER Campaign Planner", "color": "blue"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  orchestration:
    budget:
      seconds: 120
      tokens: 16000

  instructions:
    response: >
      You are the Apex Athletics campaign planner. Lead with specific numbers:
      customer counts, LTV, intent scores, and conversion rates. When recommending
      campaigns, cite the historical campaign that supports the recommendation by
      name. Keep responses concise and structured for a marketer to act on.
    orchestration: >
      Use CustomerAnalyst for any question about customers, segments, counts, LTV,
      churn risk, engagement, intent scores, or conversion rates.
      Use CampaignSearch for questions about past campaign copy, subject lines,
      CTAs, tone, or what has performed well for an audience.
      When asked to recommend an audience for a campaign, call CustomerAnalyst
      first to rank segments, then CampaignSearch to find supporting campaign history.

    sample_questions:
      - question: "Which five micro-segments have the highest intent score?"
      - question: "What campaigns have worked for at-risk customers?"
      - question: "Compare average LTV across churn risk tiers"
      - question: "Which segments should I target for a winter running campaign, and what copy has worked?"

  tools:
    - tool_spec:
        type: cortex_analyst_text_to_sql
        name: CustomerAnalyst
        description: >
          Queries the CUSTOMER_360_SV semantic view for customer and segment
          analytics. Use for segment rankings by intent score, LTV, churn risk,
          engagement scores, customer counts, and campaign conversion rates.

    - tool_spec:
        type: cortex_search
        name: CampaignSearch
        description: >
          Searches 60 historical Apex Athletics campaigns. Use to find past
          subject lines, body copy, CTAs, tone, and performance by audience or topic.

  tool_resources:
    CustomerAnalyst:
      semantic_view: WRITER_SF_QUICKSTART.MARKETING.CUSTOMER_360_SV
      execution_environment:
        type: warehouse
        warehouse: WRITER_QUICKSTART_WH

    CampaignSearch:
      name: WRITER_SF_QUICKSTART.MARKETING.CAMPAIGN_LIBRARY_SEARCH
      max_results: 5
  $$;

-- MCP Server
CREATE OR REPLACE MCP SERVER WRITER_QUICKSTART_MCP_SERVER
  FROM SPECIFICATION
  $$
  tools:
    - title: "WRITER Campaign Planner"
      name: "campaign-planner"
      type: "CORTEX_AGENT_RUN"
      identifier: "WRITER_SF_QUICKSTART.MARKETING.WRITER_CAMPAIGN_PLANNER"
      description: >
        Recommends Apex Athletics customer micro-segments and retrieves historical
        campaign performance. Use this for any question about which audience to
        target, segment metrics such as intent score, LTV, or churn risk, and what
        campaign copy has performed well before.

    - title: "Save Campaign Brief"
      name: "save-brief"
      type: "GENERIC"
      identifier: "WRITER_SF_QUICKSTART.MARKETING.SAVE_BRIEF"
      description: >
        Saves a completed campaign brief to Snowflake and returns the BRIEF_ID.
        Call this only after the brief has been fully drafted. Re-calling with the
        same brief_id updates the existing brief instead of creating a duplicate.
      config:
        type: "procedure"
        warehouse: "WRITER_QUICKSTART_WH"
        query_timeout: 120
        input_schema:
          type: "object"
          properties:
            P_CAMPAIGN_ID:
              type: "string"
              description: "Campaign identifier, for example CMP-2026-001"
            P_BRIEF_JSON:
              type: "string"
              description: >
                The complete campaign brief serialized as a JSON string. Include
                a brief_id, status, created_by, title, and any brief sections.
          required: ["P_CAMPAIGN_ID", "P_BRIEF_JSON"]
  $$;

-- Remaining grants
GRANT SELECT ON SEMANTIC VIEW CUSTOMER_360_SV               TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON CORTEX SEARCH SERVICE CAMPAIGN_LIBRARY_SEARCH TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON AGENT WRITER_CAMPAIGN_PLANNER                TO ROLE WRITER_QUICKSTART_ROLE;
GRANT USAGE ON MCP SERVER WRITER_QUICKSTART_MCP_SERVER      TO ROLE WRITER_QUICKSTART_ROLE;

-- Verify
DESCRIBE AGENT WRITER_CAMPAIGN_PLANNER;
DESCRIBE MCP SERVER WRITER_QUICKSTART_MCP_SERVER;

SHOW CORTEX SEARCH SERVICES IN SCHEMA WRITER_SF_QUICKSTART.MARKETING;
```

**Expected:** `DESCRIBE MCP SERVER` shows both tools, with `save-brief` carrying `config.type = procedure` and an `input_schema` listing `P_CAMPAIGN_ID` and `P_BRIEF_JSON`. The Search service should show both `indexing_state` and `serving_state` as `ACTIVE` (this may take 1-5 minutes).

![DESCRIBE MCP SERVER output](assets/describe-mcp-server.png)

![Search service showing ACTIVE status](assets/search-service-active.png)

<!-- ------------------------ -->
## OAuth Configuration

WRITER authenticates to the MCP server with OAuth 2.0. This creates the security integration and retrieves the client credentials you will paste into WRITER.

```sql
USE ROLE ACCOUNTADMIN;

CREATE SECURITY INTEGRATION WRITER_QUICKSTART_OAUTH
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://app.writer.com/mcp/oauth/callback'
  OAUTH_USE_SECONDARY_ROLES = NONE
  ALLOWED_ROLES_LIST = ('WRITER_QUICKSTART_ROLE')
  COMMENT = 'OAuth integration for the WRITER quickstart MCP connector';

-- Client ID and secret for WRITER. Treat these as credentials.
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('WRITER_QUICKSTART_OAUTH');

-- Your MCP server URL
SELECT 'https://'
  || LOWER(CURRENT_ORGANIZATION_NAME()) || '-' || LOWER(CURRENT_ACCOUNT_NAME())
  || '.snowflakecomputing.com'
  || '/api/v2/databases/WRITER_SF_QUICKSTART/schemas/MARKETING'
  || '/mcp-servers/WRITER_QUICKSTART_MCP_SERVER' AS mcp_server_url;
```

**Expected:** A client ID and secret, and a fully qualified MCP server URL. Keep both for the WRITER connection step.

> If your account identifier contains underscores, replace them with hyphens in the hostname. Some MCP clients fail to connect to hostnames with underscores. This applies to the hostname only — database, schema, and server names in the path retain their original underscores.

<!-- ------------------------ -->
## Default Role Setup

This is the step most likely to cost you time, and it fails in a way that looks like something else.

MCP OAuth sessions use the connecting user's `DEFAULT_ROLE`. If your default role is not `WRITER_QUICKSTART_ROLE`, WRITER will authenticate successfully and then fail to see or invoke the tools.

**Record your current values first.** This is a user-level setting.

```sql
USE ROLE ACCOUNTADMIN;

-- Note DEFAULT_ROLE and DEFAULT_WAREHOUSE. Write them down.
SHOW USERS LIKE '<your_username>';

ALTER USER <your_username>
  SET DEFAULT_ROLE      = 'WRITER_QUICKSTART_ROLE'
      DEFAULT_WAREHOUSE = 'WRITER_QUICKSTART_WH';

-- Confirm
SHOW USERS LIKE '<your_username>';
```

> **Running this alongside an existing MCP integration?** `DEFAULT_ROLE` is a single value per user. If you already have a working connector, create a dedicated user for this quickstart instead:
>
> ```sql
> CREATE USER WRITER_QUICKSTART_USER
>   PASSWORD = '<choose-a-strong-password>'
>   MUST_CHANGE_PASSWORD = FALSE
>   DEFAULT_ROLE      = 'WRITER_QUICKSTART_ROLE'
>   DEFAULT_WAREHOUSE = 'WRITER_QUICKSTART_WH';
> GRANT ROLE WRITER_QUICKSTART_ROLE TO USER WRITER_QUICKSTART_USER;
> ```

<!-- ------------------------ -->
## Connect WRITER

In WRITER, add a custom MCP connector using the values from the OAuth step:

| Field | Value |
|-------|-------|
| Server URL | The `mcp_server_url` from the OAuth step |
| Client ID | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS` |
| Client secret | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS` |

WRITER will open a browser window for the Snowflake OAuth consent screen. Sign in as the user whose default role you set in the previous step and approve.

After connecting, WRITER should discover **two** tools: `campaign-planner` and `save-brief`.

![WRITER MCP connector configuration](assets/writer-connector-config.png)

![WRITER showing discovered tools](assets/writer-tools-discovered.png)

> If WRITER connects but shows no tools, or shows them and fails on invocation, revisit the Default Role Setup step. That is the usual cause.

<!-- ------------------------ -->
## Build the Playbook

### How WRITER discovers the contract

You never tell WRITER the signature of `SAVE_BRIEF`. When a client connects, it issues an MCP `tools/list` request, and the server returns each tool's `inputSchema`. WRITER's model reads it at discovery time and calls the tool accordingly.

The tool descriptions drive tool selection — WRITER decides between `campaign-planner` and `save-brief` from their names and descriptions alone. The parameter descriptions are functional, not documentation: they tell the model that `P_BRIEF_JSON` wants a serialized JSON string, not a nested object.

### Create the playbook

Create a new playbook in WRITER with one agent node.

**Add one variable:**

| Key | Type |
|-----|------|
| `Campaign__Topic` | text |

**Paste this as the agent prompt:**

```
### Instructions

You are planning a marketing campaign for Apex Athletics, a B2B activewear company.
The campaign topic is [w-var](Campaign__Topic).

**Step 1 — Find the audience**

Ask [w-connector](SNOWFLAKE) using campaign-planner:
"Which 3 micro-segments should we target for a campaign about <topic>? For each, give
the segment name, customer count, average LTV, intent score, and churn risk tier."

**Step 2 — Find what has worked**

Ask [w-connector](SNOWFLAKE) using campaign-planner:
"What historical campaign copy has performed well for these segments and for the topic
<topic>? Include subject lines, CTAs, tone, and conversion rates."

**Step 3 — Draft the brief**

Write a campaign brief grounded only in what came back from Snowflake. Do not invent
segment names, metrics, or campaign history. Include:
- Campaign name and a one-line objective
- The 3 target segments with their metrics and a sentence on why each fits
- Recommended channels, with a rationale referencing historical performance
- Three subject line options in the tone that performed best
- Success metrics, using the historical conversion rates as the baseline
- Any assumptions or open questions

**Step 4 — Save it to Snowflake**

Call the save-brief tool on [w-connector](SNOWFLAKE) with:
- P_CAMPAIGN_ID: a new identifier in the form CMP-2026-NNN
- P_BRIEF_JSON: the complete brief as a JSON string, including brief_id, status
  ("draft"), created_by ("WRITER playbook"), title, and a section for each part of
  the brief above

Report the returned BRIEF_ID and the table it was written to.
```

Run it with a topic such as `winter running gear` or `win back lapsed customers`.

![WRITER playbook builder](assets/writer-playbook-builder.png)

![Playbook running against Snowflake MCP](assets/writer-playbook-running.png)

<!-- ------------------------ -->
## Verify Write-Back

Back in Snowflake, confirm the brief landed:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

SELECT
  BRIEF_ID,
  CAMPAIGN_ID,
  STATUS,
  CREATED_BY,
  CREATED_AT,
  BRIEF_CONTENT:title::VARCHAR AS title
FROM CAMPAIGN_BRIEFS;

-- Full brief content
SELECT BRIEF_CONTENT
FROM CAMPAIGN_BRIEFS
ORDER BY CREATED_AT DESC
LIMIT 1;
```

**Expected:** One row. `CREATED_BY` reflects the value from the playbook prompt. `BRIEF_CONTENT` holds the brief WRITER wrote, with its structure intact.

![Campaign brief result in Snowflake](assets/snowflake-brief-result.png)

Run the playbook again with the same `P_CAMPAIGN_ID` and `brief_id` — the row count stays at 1 because the `MERGE` updates rather than duplicates.

<!-- ------------------------ -->
## Conclusion And Resources

You have connected WRITER to Snowflake through an MCP server with two governed tools: a Cortex Agent for reading customer intelligence, and a stored procedure for writing campaign briefs. The integration is built on least-privileged roles, OAuth, and a fixed procedure contract that defines exactly what WRITER can do in Snowflake.

### What You Learned
- How to build a Cortex Agent that routes between a semantic view and a Cortex Search service
- How to create a governed write-back path using a stored procedure exposed as an MCP tool
- How to configure OAuth for Snowflake MCP server authentication
- How WRITER discovers tool contracts through MCP `tools/list` — no hardcoded signatures needed
- How to build a WRITER playbook that grounds content in Snowflake data and writes results back

### Cleanup

Run the teardown to remove all objects created by this guide:

```sql
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS WRITER_SF_QUICKSTART;
DROP WAREHOUSE IF EXISTS WRITER_QUICKSTART_WH;
DROP SECURITY INTEGRATION IF EXISTS WRITER_QUICKSTART_OAUTH;
DROP ROLE IF EXISTS WRITER_QUICKSTART_ROLE;

-- Only if you created a dedicated user:
-- DROP USER IF EXISTS WRITER_QUICKSTART_USER;

-- Restore your original default role and warehouse:
-- ALTER USER <your_username>
--   SET DEFAULT_ROLE = '<original_role>' DEFAULT_WAREHOUSE = '<original_warehouse>';

-- Confirm nothing is left
SHOW DATABASES LIKE 'WRITER_SF_QUICKSTART';
SHOW WAREHOUSES LIKE 'WRITER_QUICKSTART_WH';
SHOW ROLES LIKE 'WRITER_QUICKSTART_ROLE';
SHOW INTEGRATIONS LIKE 'WRITER_QUICKSTART_OAUTH';
```

Also remove the connector in WRITER, since its credentials no longer resolve.

### Troubleshooting

| Symptom | Likely Cause | Check |
|---------|-------------|-------|
| WRITER connects, no tools appear | Default role lacks USAGE on MCP server | `SHOW GRANTS TO ROLE WRITER_QUICKSTART_ROLE` |
| Tools appear but fail on invocation | Tool-level grants missing | Confirm AGENT, SEMANTIC_VIEW, SEARCH, PROCEDURE grants |
| Agent says table "does not exist" | Table rebuilt after grants ran | Re-run grants from Write-Back Contract step |
| Session fails to initialize | No DEFAULT_WAREHOUSE on user | `SHOW USERS LIKE '<you>'` |
| Wrong data or none visible | Default role is not WRITER_QUICKSTART_ROLE | Check `default_role` in SHOW USERS |
| OAuth consent fails | Redirect URI mismatch | `DESCRIBE INTEGRATION WRITER_QUICKSTART_OAUTH` |
| Hostname connection failure | Underscores in account hostname | Use hyphens in hostname only |
| Agent returns nothing for copy questions | Search still indexing | `SHOW CORTEX SEARCH SERVICES` — both states must be ACTIVE |
| Second save fails | Missing UPDATE on CAMPAIGN_BRIEFS | Check grants include UPDATE |

### Related Resources
- [Getting Started with Snowflake MCP Server](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-mcp-server/)
- [Best Practices to Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/)
- [Snowflake MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [WRITER Documentation](https://developer.writer.com/)

### Next Steps
- **Extend to the full content supply chain.** Add a `save-asset` tool for copy and an `activate-segment` tool for audience delivery — both follow the same `GENERIC` procedure pattern as `save-brief`.
- **Dynamic Tables.** Rebuild `CUSTOMER_360` as a Dynamic Table over a real event stream with `TARGET_LAG`, so segments stay current automatically.
- **Index the briefs.** Add a Cortex Search service over `CAMPAIGN_BRIEFS` so each campaign can learn from the ones before it.
