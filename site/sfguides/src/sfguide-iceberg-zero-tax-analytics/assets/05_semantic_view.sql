-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 05_semantic_view.sql -- Semantic View + Cortex Agent (Module 5)
-- =============================================================================
-- Creates a semantic view over yellow_trips + zone_lookup that defines
-- business-friendly dimensions, metrics, synonyms, and verified queries.
-- Then creates a Cortex Agent that uses this semantic view as its tool,
-- enabling natural language queries via Snowflake Intelligence.
--
-- DESIGN DECISIONS:
--   - yellow_trips + zone_lookup ONLY (no weather, no green_trips)
--   - Weather excluded intentionally: demonstrates the "guardrail" —
--     when a user asks about weather, the agent declines because the
--     semantic view has no context for that data.
--   - Metrics are pre-aggregated (SUM, AVG, COUNT) for reliable answers.
--   - Verified queries (VQRs) provide gold-standard Q&A pairs that
--     dramatically improve Cortex Analyst accuracy.
--   - Synonyms map business language to physical column names.
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- SECTION 1: Create the Semantic View
-- ---------------------------------------------------------------------------
-- Using SQL DDL (CREATE SEMANTIC VIEW) rather than YAML for demo clarity.
-- Two logical tables: yellow_trips (trips) and zone_lookup (zones).
-- Relationship: PULocationID -> LocationID (many_to_one).

CREATE OR REPLACE SEMANTIC VIEW nyc_taxi_analytics

  TABLES (
    trips AS ICEBERG_DEMO.PUBLIC.YELLOW_TRIPS
      WITH SYNONYMS ('yellow taxi', 'yellow cab', 'taxi trips', 'rides')
      COMMENT = 'NYC Yellow Taxi trip records from Jan 2024 to Feb 2026',

    zones AS ICEBERG_DEMO.PUBLIC.ZONE_LOOKUP
      PRIMARY KEY (LOCATIONID)
      WITH SYNONYMS ('taxi zones', 'locations', 'neighborhoods')
      COMMENT = 'NYC taxi zone lookup — maps LocationID to Borough and Zone name'
  )

  RELATIONSHIPS (
    pickup_zone AS
      trips (PULOCATIONID) REFERENCES zones (LOCATIONID)
  )

  FACTS (
    trips.fare AS fare_amount
      COMMENT = 'Base fare amount in USD',
    trips.tip AS tip_amount
      COMMENT = 'Tip amount in USD',
    trips.total AS total_amount
      COMMENT = 'Total charge including fare, tips, tolls, surcharges',
    trips.distance AS trip_distance
      COMMENT = 'Trip distance in miles',
    trips.passengers AS passenger_count
      COMMENT = 'Number of passengers in the vehicle',
    zones.borough_name AS Borough
      COMMENT = 'NYC borough name from zone lookup'
  )

  DIMENSIONS (
    trips.pickup_datetime AS tpep_pickup_datetime
      WITH SYNONYMS = ('pickup time', 'start time', 'trip start')
      COMMENT = 'Timestamp when the taxi meter was engaged',

    trips.dropoff_datetime AS tpep_dropoff_datetime
      WITH SYNONYMS = ('dropoff time', 'end time', 'trip end')
      COMMENT = 'Timestamp when the taxi meter was disengaged',

    trips.pickup_hour AS HOUR(tpep_pickup_datetime)
      WITH SYNONYMS = ('hour of day', 'time of day')
      COMMENT = 'Hour of pickup (0-23)',

    trips.pickup_date AS DATE(tpep_pickup_datetime)
      WITH SYNONYMS = ('trip date', 'date')
      COMMENT = 'Date of pickup',

    trips.pickup_month AS DATE_TRUNC('month', tpep_pickup_datetime)
      WITH SYNONYMS = ('month', 'trip month')
      COMMENT = 'Month of pickup',

    trips.pickup_day_of_week AS DAYNAME(tpep_pickup_datetime)
      WITH SYNONYMS = ('day of week', 'weekday')
      COMMENT = 'Day of week (Mon, Tue, etc.)',

    trips.payment_method AS
      CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Unknown'
      END
      WITH SYNONYMS = ('payment type', 'how they paid')
      COMMENT = 'Human-readable payment method',

    zones.pickup_borough AS BOROUGH
      WITH SYNONYMS = ('borough', 'pickup area', 'neighborhood')
      COMMENT = 'NYC borough of pickup location',

    zones.pickup_zone_name AS "ZONE"
      WITH SYNONYMS = ('zone', 'pickup zone', 'pickup neighborhood')
      COMMENT = 'NYC taxi zone name of pickup'
  )

  METRICS (
    trips.total_trips AS COUNT(*)
      WITH SYNONYMS = ('trip count', 'number of rides', 'ride count', 'how many trips')
      COMMENT = 'Total number of taxi trips',

    trips.total_revenue AS SUM(trips.total)
      WITH SYNONYMS = ('revenue', 'total sales', 'earnings', 'income')
      COMMENT = 'Total revenue in USD (fare + tips + tolls + surcharges)',

    trips.avg_fare AS AVG(trips.fare)
      WITH SYNONYMS = ('average fare', 'mean fare', 'typical fare')
      COMMENT = 'Average base fare amount in USD',

    trips.avg_tip_pct AS AVG(trips.tip / NULLIF(trips.fare, 0)) * 100
      WITH SYNONYMS = ('tip percentage', 'tip rate', 'tipping rate', 'average tip percent')
      COMMENT = 'Average tip as a percentage of fare',

    trips.avg_distance AS AVG(trips.distance)
      WITH SYNONYMS = ('average distance', 'mean distance', 'typical trip length')
      COMMENT = 'Average trip distance in miles',

    trips.avg_passengers AS AVG(trips.passengers)
      WITH SYNONYMS = ('average passengers', 'riders per trip')
      COMMENT = 'Average number of passengers per trip'
  )

  COMMENT = 'NYC Yellow Taxi analytics — trip volumes, revenue, tipping, and geography. Covers Jan 2024 through Feb 2026.'

  AI_SQL_GENERATION 'Always round currency values to 2 decimal places. Always round percentages to 1 decimal place. When computing tip percentage, exclude rows where fare_amount is 0 or NULL. Default sort order is descending by the primary metric unless the user specifies otherwise.'

  AI_QUESTION_CATEGORIZATION 'This semantic view covers NYC yellow taxi trip data only. It does NOT contain weather data, green taxi data, or airport information. If asked about weather, precipitation, temperature, or green taxis, respond that you do not have that information available. If the question is ambiguous about time range, default to all available data (Jan 2024 - Feb 2026).'

  AI_VERIFIED_QUERIES (
    revenue_by_borough AS (
      QUESTION 'What is total revenue by borough?'
      ONBOARDING_QUESTION TRUE
      VERIFIED_BY '(STEWARD = demo_admin)'
      SQL 'SELECT
               __zones.pickup_borough,
               ROUND(SUM(__trips.total), 2) AS total_revenue
             FROM __trips
             LEFT JOIN __zones ON __trips.pulocationid = __zones.locationid
             GROUP BY __zones.pickup_borough
             ORDER BY total_revenue DESC'
    ),

    avg_fare_by_payment AS (
      QUESTION 'What is the average fare by payment method?'
      ONBOARDING_QUESTION TRUE
      VERIFIED_BY '(STEWARD = demo_admin)'
      SQL 'SELECT
               __trips.payment_method,
               ROUND(AVG(__trips.fare), 2) AS avg_fare
             FROM __trips
             GROUP BY __trips.payment_method
             ORDER BY avg_fare DESC'
    ),

    busiest_day_of_week AS (
      QUESTION 'Which day of the week has the most trips?'
      ONBOARDING_QUESTION TRUE
      VERIFIED_BY '(STEWARD = demo_admin)'
      SQL 'SELECT
               __trips.pickup_day_of_week,
               COUNT(*) AS total_trips
             FROM __trips
             GROUP BY __trips.pickup_day_of_week
             ORDER BY total_trips DESC'
    ),

    tip_pct_by_borough AS (
      QUESTION 'What is the average tip percentage by borough?'
      VERIFIED_BY '(STEWARD = demo_admin)'
      SQL 'SELECT
               __zones.pickup_borough,
               ROUND(AVG(__trips.tip / NULLIF(__trips.fare, 0)) * 100, 1) AS avg_tip_pct
             FROM __trips
             LEFT JOIN __zones ON __trips.pulocationid = __zones.locationid
             WHERE __trips.fare > 0
             GROUP BY __zones.pickup_borough
             ORDER BY avg_tip_pct DESC'
    ),

    monthly_trip_volume AS (
      QUESTION 'Show me monthly trip volume over time'
      VERIFIED_BY '(STEWARD = demo_admin)'
      SQL 'SELECT
               __trips.pickup_month,
               COUNT(*) AS total_trips
             FROM __trips
             GROUP BY __trips.pickup_month
             ORDER BY __trips.pickup_month'
    )
  );

-- ---------------------------------------------------------------------------
-- SECTION 1B: Export the Semantic View as YAML
-- ---------------------------------------------------------------------------
-- SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW converts the SQL DDL above into the
-- equivalent YAML specification. Run the SELECT below to see the output.
--
-- WHY BOTH FORMATS?
--   SQL DDL (Section 1)  → Human-readable, great for demos and version control.
--   YAML (below)         → Machine-portable, used by SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML
--                           to recreate the view in another account/schema.
--
-- WHAT TO COMPARE (SQL vs. YAML):
--   ┌─────────────────────────┬──────────────────────────────────────────────┐
--   │ SQL DDL                 │ YAML equivalent                              │
--   ├─────────────────────────┼──────────────────────────────────────────────┤
--   │ TABLES (...)            │ tables: [list of logical tables]             │
--   │ RELATIONSHIPS (...)     │ relationships: [join definitions]            │
--   │ FACTS (...)             │ facts: under each table                      │
--   │ DIMENSIONS (...)        │ dimensions: under each table                 │
--   │ METRICS (...)           │ metrics: under each table                    │
--   │ AI_SQL_GENERATION       │ module_custom_instructions.sql_generation    │
--   │ AI_QUESTION_CATEGOR...  │ module_custom_instructions.question_categ... │
--   │ AI_VERIFIED_QUERIES     │ verified_queries: [list]                     │
--   └─────────────────────────┴──────────────────────────────────────────────┘
--
-- KEY DIFFERENCES TO NOTICE:
--   1. YAML adds explicit data_type and access_modifier (inferred from DDL).
--   2. YAML nests facts/dimensions/metrics INSIDE each table definition,
--      whereas SQL DDL groups them in top-level clauses.
--   3. Relationship type (many_to_one) is auto-inferred — no need to declare it.
--   4. VQRs in YAML use snake_case field names (use_as_onboarding_question)
--      vs. SQL keywords (ONBOARDING_QUESTION TRUE).
--   5. The YAML is what gets stored internally — SQL DDL is syntactic sugar.
-- ---------------------------------------------------------------------------

SELECT SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW('ICEBERG_DEMO.PUBLIC.NYC_TAXI_ANALYTICS');
/*
name: NYC_TAXI_ANALYTICS
description: "NYC Yellow Taxi analytics — trip volumes, revenue, tipping, and geography. Covers Jan 2024 through Feb 2026."
tables:
  - name: TRIPS
    synonyms:
      - yellow taxi
      - yellow cab
      - taxi trips
      - rides
    description: NYC Yellow Taxi trip records from Jan 2024 to Feb 2026
    base_table:
      database: ICEBERG_DEMO
      schema: PUBLIC
      table: YELLOW_TRIPS
    dimensions:
      - name: DROPOFF_DATETIME
        synonyms:
          - dropoff time
          - end time
          - trip end
        description: Timestamp when the taxi meter was disengaged
        expr: tpep_dropoff_datetime
        data_type: TIMESTAMP_NTZ(6)
      - name: PAYMENT_METHOD
        synonyms:
          - payment type
          - how they paid
        description: Human-readable payment method
        expr: |-
          CASE payment_type
                  WHEN 1 THEN 'Credit Card'
                  WHEN 2 THEN 'Cash'
                  WHEN 3 THEN 'No Charge'
                  WHEN 4 THEN 'Dispute'
                  ELSE 'Unknown'
                END
        data_type: VARCHAR(11)
      - name: PICKUP_DATE
        synonyms:
          - trip date
          - date
        description: Date of pickup
        expr: DATE(tpep_pickup_datetime)
        data_type: DATE
      - name: PICKUP_DATETIME
        synonyms:
          - pickup time
          - start time
          - trip start
        description: Timestamp when the taxi meter was engaged
        expr: tpep_pickup_datetime
        data_type: TIMESTAMP_NTZ(6)
      - name: PICKUP_DAY_OF_WEEK
        synonyms:
          - day of week
          - weekday
        description: "Day of week (Mon, Tue, etc.)"
        expr: DAYNAME(tpep_pickup_datetime)
        data_type: VARCHAR(3)
      - name: PICKUP_HOUR
        synonyms:
          - hour of day
          - time of day
        description: Hour of pickup (0-23)
        expr: HOUR(tpep_pickup_datetime)
        data_type: "NUMBER(2,0)"
      - name: PICKUP_MONTH
        synonyms:
          - month
          - trip month
        description: Month of pickup
        expr: "DATE_TRUNC('month', tpep_pickup_datetime)"
        data_type: TIMESTAMP_NTZ(9)
    facts:
      - name: DISTANCE
        description: Trip distance in miles
        expr: trip_distance
        data_type: FLOAT
        access_modifier: public_access
      - name: FARE
        description: Base fare amount in USD
        expr: fare_amount
        data_type: FLOAT
        access_modifier: public_access
      - name: PASSENGERS
        description: Number of passengers in the vehicle
        expr: passenger_count
        data_type: "NUMBER(38,0)"
        access_modifier: public_access
      - name: TIP
        description: Tip amount in USD
        expr: tip_amount
        data_type: FLOAT
        access_modifier: public_access
      - name: TOTAL
        description: "Total charge including fare, tips, tolls, surcharges"
        expr: total_amount
        data_type: FLOAT
        access_modifier: public_access
    metrics:
      - name: AVG_DISTANCE
        synonyms:
          - average distance
          - mean distance
          - typical trip length
        description: Average trip distance in miles
        expr: AVG(trips.distance)
        access_modifier: public_access
      - name: AVG_FARE
        synonyms:
          - average fare
          - mean fare
          - typical fare
        description: Average base fare amount in USD
        expr: AVG(trips.fare)
        access_modifier: public_access
      - name: AVG_PASSENGERS
        synonyms:
          - average passengers
          - riders per trip
        description: Average number of passengers per trip
        expr: AVG(trips.passengers)
        access_modifier: public_access
      - name: AVG_TIP_PCT
        synonyms:
          - tip percentage
          - tip rate
          - tipping rate
          - average tip percent
        description: Average tip as a percentage of fare
        expr: "AVG(trips.tip / NULLIF(trips.fare, 0)) * 100"
        access_modifier: public_access
      - name: TOTAL_REVENUE
        synonyms:
          - revenue
          - total sales
          - earnings
          - income
        description: Total revenue in USD (fare + tips + tolls + surcharges)
        expr: SUM(trips.total)
        access_modifier: public_access
      - name: TOTAL_TRIPS
        synonyms:
          - trip count
          - number of rides
          - ride count
          - how many trips
        description: Total number of taxi trips
        expr: COUNT(*)
        access_modifier: public_access
  - name: ZONES
    synonyms:
      - taxi zones
      - locations
      - neighborhoods
    description: NYC taxi zone lookup — maps LocationID to Borough and Zone name
    base_table:
      database: ICEBERG_DEMO
      schema: PUBLIC
      table: ZONE_LOOKUP
    primary_key:
      columns:
        - LOCATIONID
    dimensions:
      - name: PICKUP_BOROUGH
        synonyms:
          - borough
          - pickup area
          - neighborhood
        description: NYC borough of pickup location
        expr: BOROUGH
        data_type: VARCHAR(16777216)
      - name: PICKUP_ZONE_NAME
        synonyms:
          - zone
          - pickup zone
          - pickup neighborhood
        description: NYC taxi zone name of pickup
        expr: '"ZONE"'
        data_type: VARCHAR(16777216)
    facts:
      - name: BOROUGH_NAME
        description: NYC borough name from zone lookup
        expr: Borough
        data_type: VARCHAR(16777216)
        access_modifier: public_access
relationships:
  - name: PICKUP_ZONE
    left_table: TRIPS
    right_table: ZONES
    relationship_columns:
      - left_column: PULOCATIONID
        right_column: LOCATIONID
module_custom_instructions:
  sql_generation: "Always round currency values to 2 decimal places. Always round percentages to 1 decimal place. When computing tip percentage, exclude rows where fare_amount is 0 or NULL. Default sort order is descending by the primary metric unless the user specifies otherwise."
  question_categorization: "This semantic view covers NYC yellow taxi trip data only. It does NOT contain weather data, green taxi data, or airport information. If asked about weather, precipitation, temperature, or green taxis, respond that you do not have that information available. If the question is ambiguous about time range, default to all available data (Jan 2024 - Feb 2026)."
verified_queries:
  - name: REVENUE_BY_BOROUGH
    sql: |-
      SELECT
                     __zones.pickup_borough,
                     ROUND(SUM(__trips.total), 2) AS total_revenue
                   FROM __trips
                   LEFT JOIN __zones ON __trips.pulocationid = __zones.locationid
                   GROUP BY __zones.pickup_borough
                   ORDER BY total_revenue DESC
    question: What is total revenue by borough?
    verified_by: (STEWARD = demo_admin)
    use_as_onboarding_question: true
  - name: AVG_FARE_BY_PAYMENT
    sql: |-
      SELECT
                     __trips.payment_method,
                     ROUND(AVG(__trips.fare), 2) AS avg_fare
                   FROM __trips
                   GROUP BY __trips.payment_method
                   ORDER BY avg_fare DESC
    question: What is the average fare by payment method?
    verified_by: (STEWARD = demo_admin)
    use_as_onboarding_question: true
  - name: BUSIEST_DAY_OF_WEEK
    sql: |-
      SELECT
                     __trips.pickup_day_of_week,
                     COUNT(*) AS total_trips
                   FROM __trips
                   GROUP BY __trips.pickup_day_of_week
                   ORDER BY total_trips DESC
    question: Which day of the week has the most trips?
    verified_by: (STEWARD = demo_admin)
    use_as_onboarding_question: true
  - name: TIP_PCT_BY_BOROUGH
    sql: |-
      SELECT
                     __zones.pickup_borough,
                     ROUND(AVG(__trips.tip / NULLIF(__trips.fare, 0)) * 100, 1) AS avg_tip_pct
                   FROM __trips
                   LEFT JOIN __zones ON __trips.pulocationid = __zones.locationid
                   WHERE __trips.fare > 0
                   GROUP BY __zones.pickup_borough
                   ORDER BY avg_tip_pct DESC
    question: What is the average tip percentage by borough?
    verified_by: (STEWARD = demo_admin)
  - name: MONTHLY_TRIP_VOLUME
    sql: |-
      SELECT
                     __trips.pickup_month,
                     COUNT(*) AS total_trips
                   FROM __trips
                   GROUP BY __trips.pickup_month
                   ORDER BY __trips.pickup_month
    question: Show me monthly trip volume over time
    verified_by: (STEWARD = demo_admin)

*/
-- ---------------------------------------------------------------------------
-- SECTION 2: Verify the semantic view
-- ---------------------------------------------------------------------------
DESCRIBE SEMANTIC VIEW nyc_taxi_analytics;

SHOW SEMANTIC DIMENSIONS IN nyc_taxi_analytics;
SHOW SEMANTIC METRICS IN nyc_taxi_analytics;

-- ---------------------------------------------------------------------------
-- SECTION 3: Test with a direct semantic query
-- ---------------------------------------------------------------------------
SELECT * FROM SEMANTIC_VIEW(
  nyc_taxi_analytics
  METRICS trips.total_trips, trips.total_revenue
  DIMENSIONS zones.pickup_borough
) ORDER BY total_revenue DESC;

-- ---------------------------------------------------------------------------
-- SECTION 4: Grant access
-- ---------------------------------------------------------------------------
GRANT REFERENCES, SELECT ON SEMANTIC VIEW ICEBERG_DEMO.PUBLIC.nyc_taxi_analytics
  TO ROLE DEMO_ANALYST;

-- ---------------------------------------------------------------------------
-- SECTION 5: Create Cortex Agent
-- ---------------------------------------------------------------------------
-- The agent wraps the semantic view and makes it accessible via
-- Snowflake Intelligence (natural language chat interface).
-- When a user asks a question, the agent routes it to Cortex Analyst,
-- which reads the semantic view definition and generates SQL.

USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE AGENT nyc_taxi_agent
  COMMENT = 'NYC Yellow Taxi trip analyst — answers questions about trip volumes, revenue, tips, and geography'
  FROM SPECIFICATION $$
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: taxi_analytics
      description: "Answers questions about NYC yellow taxi trips including revenue, trip counts, tip percentages, payment methods, boroughs, and time-based trends. Covers January 2024 through February 2026."
tool_resources:
  taxi_analytics:
    semantic_view: "ICEBERG_DEMO.PUBLIC.NYC_TAXI_ANALYTICS"
    execution_environment:
      type: warehouse
      warehouse: "DEMO_WH"
$$;

-- Grant usage so DEMO_ADMIN and DEMO_ANALYST can chat with the agent
GRANT USAGE ON AGENT ICEBERG_DEMO.PUBLIC.nyc_taxi_agent TO ROLE DEMO_ADMIN;
GRANT USAGE ON AGENT ICEBERG_DEMO.PUBLIC.nyc_taxi_agent TO ROLE DEMO_ANALYST;

-- ---------------------------------------------------------------------------
-- SECTION 6: Test the agent (optional — can also test via Snowflake Intelligence UI)
-- ---------------------------------------------------------------------------
USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;

SELECT TRY_PARSE_JSON(
  SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'ICEBERG_DEMO.PUBLIC.NYC_TAXI_AGENT',
    $${ 
      "messages": [
        {
          "role": "user",
          "content": [{"type": "text", "text": "What is total revenue by borough?"}]
        }
      ]
    }$$
  )
) AS resp;

-- ---------------------------------------------------------------------------
-- SECTION 7: RBAC enforcement demo
-- ---------------------------------------------------------------------------
-- Demonstrates that Snowflake's privilege model applies to semantic views.
-- We create a fresh role (DEMO_SV_DENIED) that has warehouse + DB/schema
-- usage but NO grants on the semantic view or underlying tables.
-- When this role tries to query, it fails — proving RBAC is enforced.

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS DEMO_SV_DENIED
  COMMENT = 'Role with no semantic view or table access — for RBAC demo';
GRANT ROLE DEMO_SV_DENIED TO ROLE ACCOUNTADMIN;
GRANT USAGE ON WAREHOUSE DEMO_WH TO ROLE DEMO_SV_DENIED;
GRANT USAGE ON DATABASE ICEBERG_DEMO TO ROLE DEMO_SV_DENIED;
GRANT USAGE ON SCHEMA ICEBERG_DEMO.PUBLIC TO ROLE DEMO_SV_DENIED;

-- Switch to the denied role and disable secondary roles so inherited
-- privileges from other roles (DEMO_ADMIN, ACCOUNTADMIN, etc.) don't apply.
USE ROLE DEMO_SV_DENIED;
USE SECONDARY ROLES NONE;
USE WAREHOUSE DEMO_WH;

SELECT * FROM SEMANTIC_VIEW(
  nyc_taxi_analytics
  METRICS trips.total_trips
  DIMENSIONS zones.pickup_borough
);
-- Expected: Insufficient privileges error — no SELECT on semantic view or tables

-- Switch back to admin and restore secondary roles
USE ROLE DEMO_ADMIN;
USE SECONDARY ROLES ALL;
USE WAREHOUSE DEMO_WH;
USE WAREHOUSE DEMO_WH;

-- ---------------------------------------------------------------------------
-- DONE. Try it out!
-- ---------------------------------------------------------------------------
-- Open Snowflake Intelligence in Snowsight:
--   AI & ML → Snowflake Intelligence → select nyc_taxi_agent → start chatting
--
-- QUESTIONS TO TRY (Snowflake Intelligence):
--   1. "What is total revenue by borough?" (hits VQR — high confidence)
--   2. "Which day of the week is busiest?" (hits VQR)
--   3. "Show me monthly trip trends" (hits VQR)
--   4. "What's the average tip percentage for credit card vs cash?" (cross-dim)
--   5. "How many trips happened in Manhattan in January 2025?" (filter + dim)
--
-- GUARDRAIL TEST (Snowflake Intelligence):
--   6. "What was the weather like on rainy days?" → Agent declines (no weather data in SV)
--   7. "Show me green taxi trips" → Agent declines (no green_trips in SV)
--
-- RBAC TEST (Snowflake Intelligence):
--   8. Switch to a role without grants on the SV → query fails
--      Even through AI, RBAC is enforced. No bypass.
--
-- CORTEX CODE (CoCo) — TRY THESE PROMPTS:
--   Open Cortex Code (CLI or Snowsight panel) and try:
--
--   "What tables exist in ICEBERG_DEMO.PUBLIC? Describe the Iceberg tables."
--
--   "Write a query showing the top 10 busiest pickup zones from yellow_trips
--    with average fare and tip percentage. Join with zone_lookup for zone names."
--
--   "Explore the nyc_weather_ssv2 table. Show me how to extract hourly
--    temperature data from the weather_data VARIANT column for JFK."
--
--   "Explain what this masking policy does and which columns it protects."
--    (open 03_horizon_governance.sql first)
--
--   "Write a verified query for the nyc_taxi_analytics semantic view that
--    answers: What is the average trip distance by hour of day?"
-- ---------------------------------------------------------------------------
