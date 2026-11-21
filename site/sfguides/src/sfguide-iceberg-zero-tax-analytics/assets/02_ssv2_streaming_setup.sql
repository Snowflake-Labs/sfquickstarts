-- =============================================================================
-- Quickstart: Snowflake + Iceberg Interoperability
-- 02_ssv2_streaming_setup.sql -- SSV2 Streaming Ingest + Iceberg V3 VARIANT (Module 2)
-- =============================================================================
-- Creates the nyc_weather_ssv2 Iceberg V3 table and the SSV2 pipe that
-- receives streamed rows from SSV2WeatherIngest.java.
--
-- Flow:
--   1. Run this file to create the table and pipe.
--   2. From a terminal: cd ssv2-streaming
--      mvn package && mvn exec:java \
--        -Dexec.mainClass="com.snowflake.snowpipestreaming.demo.SSV2WeatherIngest"
--   3. Return here and run the verification + query sections below.
-- =============================================================================

USE ROLE DEMO_ADMIN;
USE WAREHOUSE DEMO_WH;
USE DATABASE ICEBERG_DEMO;
USE SCHEMA PUBLIC;

-- ---------------------------------------------------------------------------
-- Confirm database-level Iceberg V3 default is set (done in 00_setup.sql)
-- VARIANT columns require FORMAT_VERSION = 3
-- This verifies ICEBERG_VERSION_DEFAULT = 3, which is a prerequisite for the VARIANT column in nyc_weather_ssv2
-- ---------------------------------------------------------------------------
SHOW PARAMETERS LIKE 'ICEBERG_VERSION_DEFAULT' IN DATABASE ICEBERG_DEMO;

-- ---------------------------------------------------------------------------
-- Create nyc_weather_ssv2: Iceberg V3 table with VARIANT column
--   One row per airport per month. weather_data holds the full hourly JSON
--   response from Open-Meteo including temperature, precipitation, wind
--   speed, and weather codes (700+ data points per row).
--   Explicit internal-storage syntax:
--     CATALOG = SNOWFLAKE
--     EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
--   These two settings mean Snowflake manages the underlying Iceberg storage — no customer S3/GCS/ADLS bucket needed
-- ---------------------------------------------------------------------------
CREATE OR REPLACE ICEBERG TABLE nyc_weather_ssv2 (
    location     STRING           NOT NULL,
    latitude     FLOAT            NOT NULL,
    longitude    FLOAT            NOT NULL,
    weather_data VARIANT          NOT NULL,
    ingested_at  TIMESTAMP_LTZ(6)
)
CATALOG = SNOWFLAKE
EXTERNAL_VOLUME = SNOWFLAKE_MANAGED
COMMENT = 'NYC airport weather — streamed via SSV2 from Open-Meteo API';

-- ---------------------------------------------------------------------------
-- Create SSV2 pipe — end-to-end SSV2 (Snowpipe Streaming V2) data flow:
--   1. The external Java app (SSV2WeatherIngest.java) calls appendRow() to stream rows into this pipe
--   2. DATA_SOURCE(TYPE => 'STREAMING') receives the in-memory rowset — no staging files involved
--   3. The Java app sends the parsed JSON as a Map<String,Object> — the SDK writes it directly as VARIANT
--   4. No PARSE_JSON needed — the pipe is a straight pass-through mapping
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PIPE nyc_weather_ssv2_pipe
AS COPY INTO nyc_weather_ssv2
FROM (
    SELECT
        $1:location::STRING,
        $1:latitude::FLOAT,
        $1:longitude::FLOAT,
        $1:weather_data::VARIANT,
        $1:ingested_at::TIMESTAMP_LTZ
    FROM TABLE(DATA_SOURCE(TYPE => 'STREAMING'))
);

SELECT * FROM nyc_weather_ssv2; --empty

-- ---------------------------------------------------------------------------
-- Verify table is FORMAT_VERSION = 3 (required for VARIANT)
-- ---------------------------------------------------------------------------
SELECT SYSTEM$GET_ICEBERG_TABLE_INFORMATION('nyc_weather_ssv2') AS metadata;

-- =============================================================================
-- NOW RUN SSV2WeatherIngest.java FROM YOUR TERMINAL
--
-- The Java app has two modes you can configure via constants in the source:
--   - Default (SKIP_ARCHIVE=false, LIVE_MODE=false): loads 36 archive rows
--   - Full run (SKIP_ARCHIVE=false, LIVE_MODE=true): loads 36 + 9 = 45 rows
--
-- Run from terminal:
--   cd ssv2-streaming
/*
mvn package && mvn exec:java \
-Dexec.mainClass="com.snowflake.snowpipestreaming.demo.SSV2WeatherIngest"
*/
--
-- Expected terminal output: "All 36 rows committed to nyc_weather_ssv2." (or 45 with LIVE_MODE=true)
--
-- AFTER RUNNING THE JAVA APP
SELECT COUNT(*) AS row_count FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2;  -- expect 36 (or 45)

SELECT * FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2; 

-- The VARIANT column is immediately queryable using Snowflake's semi-structured dot notation.
-- You should see timezone, elevation, and API generation time extracted from the nested JSON.
SELECT
    location,
    ingested_at,
    weather_data:timezone::STRING         AS timezone,
    weather_data:elevation::FLOAT         AS elevation_m,
    weather_data:generationtime_ms::FLOAT AS api_gen_ms
FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2
ORDER BY ingested_at DESC, location
LIMIT 9;

-- ---------------------------------------------------------------------------
-- Sub-column pruning proof
--   Run the SELECT * first, then the pruned query below. Compare
--   BYTES_SCANNED in QUERY_HISTORY for each: the pruned query reads only
--   the precipitation-unit sub-column path, dramatically reducing I/O.
-- ---------------------------------------------------------------------------
ALTER SESSION SET USE_CACHED_RESULT = FALSE;
ALTER WAREHOUSE DEMO_WH SUSPEND;
ALTER WAREHOUSE DEMO_WH RESUME;
USE WAREHOUSE DEMO_WH;
SELECT * FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2;

ALTER SESSION SET USE_CACHED_RESULT = FALSE;
ALTER WAREHOUSE DEMO_WH_2 RESUME;
USE WAREHOUSE DEMO_WH_2;
SELECT
    location,
    weather_data:hourly_units:precipitation::STRING AS precip_unit
FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2;

-- ---------------------------------------------------------------------------
-- Raw VARIANT preview — see the full nested JSON before flattening
-- ---------------------------------------------------------------------------
USE WAREHOUSE DEMO_WH;
SELECT 
    location, weather_data
FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2
    WHERE location = 'JFK'
LIMIT 1;

-- ---------------------------------------------------------------------------
-- LATERAL FLATTEN — hourly precipitation at JFK into per-hour rows
--   700+ hourly values in one VARIANT array become individual records.
--   No pre-processing, no schema definition required.
-- ---------------------------------------------------------------------------
SELECT
    w.location,
    t.value::STRING AS weather_hour,
    p.value::FLOAT  AS precipitation_mm,
    c.value::INT    AS weather_code
FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2 w,
    LATERAL FLATTEN(input => w.weather_data:hourly:time)          t,
    LATERAL FLATTEN(input => w.weather_data:hourly:precipitation) p,
    LATERAL FLATTEN(input => w.weather_data:hourly:weathercode)   c
WHERE t.index = p.index
  AND t.index = c.index
  AND w.location = 'JFK'
  AND p.value::FLOAT > 0
ORDER BY t.value::STRING
LIMIT 20;

-- ---------------------------------------------------------------------------
-- Weather enrichment join — tip percentage by weather condition
--   Joins 40M taxi trips to SSV2-streamed weather data on pickup hour.
--   The similarity in tip percentages IS the insight: NYC riders tip
--   consistently (~20 %) regardless of rain — a testament to tipping culture.
-- ---------------------------------------------------------------------------
SELECT
    CASE WHEN w_precip > 0 THEN 'Rainy' ELSE 'Dry' END AS weather_condition,
    COUNT(*)                                            AS trip_count,
    ROUND(AVG(y.tip_amount / NULLIF(y.fare_amount, 0)) * 100, 2) AS avg_tip_pct
FROM ICEBERG_DEMO.PUBLIC.yellow_trips y
JOIN (
    SELECT
        w.location,
        TO_TIMESTAMP(t.value::STRING)  AS weather_hour,
        p.value::FLOAT                 AS w_precip
    FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2 w,
        LATERAL FLATTEN(input => w.weather_data:hourly:time)          t,
        LATERAL FLATTEN(input => w.weather_data:hourly:precipitation) p
    WHERE t.index = p.index
      AND w.location = 'JFK'
) weather
ON DATE_TRUNC('hour', y.tpep_pickup_datetime) = weather.weather_hour
WHERE y.fare_amount > 0
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------------
-- Trip volume by weather condition
--   Shows a clearer weather effect than tip percentage: fewer trips in rain,
--   and slightly longer average distances as short walks are replaced by rides.
-- ---------------------------------------------------------------------------
SELECT
    CASE WHEN w_precip > 0 THEN 'Rainy' ELSE 'Dry' END AS weather_condition,
    COUNT(*)                                            AS trip_count,
    ROUND(AVG(y.trip_distance), 2)                      AS avg_distance_miles
FROM ICEBERG_DEMO.PUBLIC.yellow_trips y
JOIN (
    SELECT
        w.location,
        TO_TIMESTAMP(t.value::STRING)  AS weather_hour,
        p.value::FLOAT                 AS w_precip
    FROM ICEBERG_DEMO.PUBLIC.nyc_weather_ssv2 w,
        LATERAL FLATTEN(input => w.weather_data:hourly:time)          t,
        LATERAL FLATTEN(input => w.weather_data:hourly:precipitation) p
    WHERE t.index = p.index
      AND w.location = 'JFK'
) weather
ON DATE_TRUNC('hour', y.tpep_pickup_datetime) = weather.weather_hour
WHERE y.fare_amount > 0
GROUP BY 1
ORDER BY 1;

