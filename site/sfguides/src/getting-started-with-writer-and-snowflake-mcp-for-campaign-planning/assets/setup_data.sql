/*=============================================================================
  WRITER + Snowflake MCP Quickstart — Data Setup
  
  Getting Started with WRITER and Snowflake MCP for Campaign Planning
  https://github.com/Snowflake-Labs/sfquickstarts

  Run this script in a Snowsight SQL Worksheet as ACCOUNTADMIN.
  It creates:
    - Database:  WRITER_SF_QUICKSTART
    - Schema:    MARKETING
    - Warehouse: WRITER_QUICKSTART_WH
    - Role:      WRITER_QUICKSTART_ROLE
    - Table:     CUSTOMER_360        (5,000 rows — synthetic customer profiles)
    - Table:     MICRO_SEGMENTS      (42 rows — RFM segment rollups)
    - Table:     CAMPAIGN_LIBRARY    (60 rows — historical campaign copy)

  All data is deterministic (HASH-based, not RANDOM), so re-running produces
  identical results.
=============================================================================*/

USE ROLE ACCOUNTADMIN;

-- ── Environment ─────────────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS WRITER_SF_QUICKSTART
  COMMENT = 'WRITER + Snowflake MCP quickstart';

CREATE SCHEMA IF NOT EXISTS WRITER_SF_QUICKSTART.MARKETING
  COMMENT = 'WRITER + Snowflake setup: Apex Athletics marketing data, AI objects, and write-back target';

CREATE WAREHOUSE IF NOT EXISTS WRITER_QUICKSTART_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for the WRITER quickstart';

CREATE ROLE IF NOT EXISTS WRITER_QUICKSTART_ROLE
  COMMENT = 'MCP access role for the WRITER quickstart';

GRANT ROLE WRITER_QUICKSTART_ROLE TO ROLE SYSADMIN;

USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

SELECT
  CURRENT_DATABASE()  AS db,
  CURRENT_SCHEMA()    AS sch,
  CURRENT_WAREHOUSE() AS wh;

-- ── CUSTOMER_360 — unified customer profile, 5,000 rows ────────────────────
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

-- ── MICRO_SEGMENTS — RFM segment x churn tier x preferred channel ──────────
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

-- ── CAMPAIGN_LIBRARY — 60 historical campaigns ────────────────────────────
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

-- ── Verify ─────────────────────────────────────────────────────────────────
SELECT
  (SELECT COUNT(*) FROM CUSTOMER_360)   AS customers,
  (SELECT COUNT(*) FROM MICRO_SEGMENTS) AS segments;

SELECT
  COUNT(*) AS campaigns,
  COUNT(DISTINCT SUBJECT_LINE) AS distinct_subjects,
  COUNT(DISTINCT CAMPAIGN_TYPE) AS types,
  COUNT(DISTINCT CHANNEL) AS channels,
  COUNT(DISTINCT PERFORMANCE_TIER) AS tiers,
  COUNT_IF(BODY_PREVIEW IS NULL) AS null_body,
  COUNT_IF(CONVERSION_RATE > CLICK_RATE OR CLICK_RATE > OPEN_RATE) AS bad_funnel
FROM CAMPAIGN_LIBRARY;
