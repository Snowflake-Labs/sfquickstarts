-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 06_cortex_code_prompts.sql -- Cortex Code (CoCo) Prompts (Module 6 — OPTIONAL)
-- =============================================================================
-- This file contains curated prompts you can paste into Cortex Code (CoCo) to
-- explore the entire quickstart with AI assistance. No executable SQL here —
-- just prompts organized by module.
--
-- HOW TO USE:
--   1. Open Cortex Code in Snowsight (lower-right panel) or use the CLI
--   2. Copy any prompt below and paste it into CoCo
--   3. CoCo will generate SQL, explain concepts, or build artifacts for you
--
-- Each section maps to a quickstart module so you can try prompts as you go.
-- =============================================================================


-- ---------------------------------------------------------------------------
-- SECTION 1: Data Engineering — Tables & Setup (Modules 0–1)
-- ---------------------------------------------------------------------------
-- These prompts help you explore and understand the Iceberg table setup.

-- "What tables exist in ICEBERG_DEMO.PUBLIC? Describe each one including
--  row counts, column types, and whether they are Iceberg tables."

-- "Explain the difference between CATALOG = SNOWFLAKE and using an external
--  volume with a customer-managed bucket. What are the tradeoffs?"

-- "Create a new Iceberg table called trip_summary that aggregates yellow_trips
--  by pickup date and borough with total trips, revenue, and average fare."

-- "Show me the Iceberg metadata for yellow_trips — what format version is it,
--  how many data files, and what is the partition spec?"


-- ---------------------------------------------------------------------------
-- SECTION 2: Real-Time Streaming (Module 2)
-- ---------------------------------------------------------------------------
-- These prompts explore the SSV2 weather table and VARIANT data.

-- "Explore the nyc_weather_ssv2 table. Show me how to extract hourly
--  temperature and precipitation from the weather_data VARIANT column for JFK."

-- "Write a query that finds the rainiest days at each airport station using
--  the VARIANT data in nyc_weather_ssv2. Flatten the hourly array."

-- "Explain how Snowpipe Streaming V2 works. What is the difference between
--  SSV2 and classic Snowpipe? When would I choose one over the other?"

-- "Write a query that joins nyc_weather_ssv2 weather data with yellow_trips
--  to see if rainy days have lower tip percentages."


-- ---------------------------------------------------------------------------
-- SECTION 3: Governance — Masking & RLS (Module 3)
-- ---------------------------------------------------------------------------
-- These prompts explore how governance policies work and how to build new ones.

-- "Explain what masking and row-level security policies are applied in
--  ICEBERG_DEMO.PUBLIC. Which tables and columns are protected?"

-- "Write a new masking policy that redacts the first 3 digits of total_amount
--  for any role that is NOT DEMO_ADMIN. Apply it to green_trips."

-- "Show me how to verify that the borough_rls policy is working. Write
--  queries that demonstrate filtered vs unfiltered results by role."

-- "What is the difference between Path A and Path B when Databricks reads
--  through Horizon? Explain the governance enforcement mechanism."


-- ---------------------------------------------------------------------------
-- SECTION 4: Multi-Engine / Databricks (Module 4)
-- ---------------------------------------------------------------------------
-- These prompts cover cross-engine interoperability via Horizon IRC.

-- "Generate the Spark configuration needed for Databricks to connect to
--  Snowflake's Iceberg REST Catalog. Include both Path A and Path B setup."

-- "Explain how Horizon decides whether to vend STS credentials (Path A) or
--  route through Snowflake compute (Path B). What triggers each path?"

-- "If I wanted to add Trino as another external consumer reading through
--  Horizon IRC, what would the catalog configuration look like?"


-- ---------------------------------------------------------------------------
-- SECTION 5: Semantic View + Cortex Agent (Module 5)
-- ---------------------------------------------------------------------------
-- These prompts help you build, modify, and debug the semantic layer.

-- "Show me the semantic view nyc_taxi_analytics. What dimensions, metrics,
--  and verified queries does it define?"

-- "Add a new metric to the nyc_taxi_analytics semantic view called
--  avg_trip_duration that calculates average minutes between pickup and dropoff."

-- "Write a new verified query (VQR) for the semantic view that answers:
--  What is the average trip distance by hour of day?"

-- "Create a Cortex Agent called trip_explorer_agent that uses the
--  nyc_taxi_analytics semantic view. Include a helpful instruction prompt."

-- "Debug this question against the semantic view: 'Show me revenue trends
--  by week for Manhattan.' If it fails, explain why and suggest a fix."


-- ---------------------------------------------------------------------------
-- SECTION 6: Open-Ended Exploration
-- ---------------------------------------------------------------------------
-- These prompts go beyond the quickstart — use them to push CoCo further.

-- "Build a Streamlit dashboard that shows a bar chart of total trips by
--  borough and a line chart of daily revenue trends from yellow_trips."

-- "Compare yellow_trips and green_trips — what are the differences in schema,
--  row counts, and trip patterns? Which boroughs does each serve?"

-- "What are the most expensive queries running in this account? Show me
--  the top 10 by execution time and suggest optimizations."

-- "Write a data quality check that validates yellow_trips has no future
--  pickup dates, no negative fares, and no null location IDs."

-- "Generate a complete YAML representation of the nyc_taxi_analytics
--  semantic view using SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW."
-- ---------------------------------------------------------------------------
