/*=============================================================================
  TELCO AI ASSISTANT - REGION CUSTOMIZATION SCRIPT
  =============================================================================
  
  This script allows you to customize the demo data to use regions/locations
  that are relevant to your geography. By default, the data uses Malaysian
  regions. Use this script to map them to your preferred regions.
  
  INSTRUCTIONS:
  1. Review the default region mappings below
  2. Modify the NEW_REGION values to match your preferred geography
  3. Optionally customize tower name prefixes
  4. Run this script after deploying the base quickstart
  
  EXAMPLE MAPPINGS:
  - US Regions: Northeast, Southeast, Midwest, Southwest, West Coast
  - European: UK, Germany, France, Spain, Italy, Netherlands
  - APAC: Singapore, Hong Kong, Tokyo, Sydney, Mumbai
  - Generic: Region-A, Region-B, Region-C, etc.
  
=============================================================================*/

USE ROLE TELCO_ANALYST_ROLE;
USE WAREHOUSE TELCO_WH;
USE DATABASE TELCO_OPERATIONS_AI;
USE SCHEMA RAW;

/*-----------------------------------------------------------------------------
  STEP 1: CREATE REGION MAPPING TABLE
  
  Modify the NEW_REGION values below to your preferred region names.
  The OLD_REGION values are the Malaysian regions in the original data.
-----------------------------------------------------------------------------*/

CREATE OR REPLACE TEMPORARY TABLE REGION_MAPPING (
    OLD_REGION VARCHAR,
    NEW_REGION VARCHAR,
    OLD_PREFIX VARCHAR,
    NEW_PREFIX VARCHAR
);

-- ============================================================================
-- CUSTOMIZE YOUR REGIONS HERE
-- ============================================================================
-- Modify the second value (NEW_REGION) and fourth value (NEW_PREFIX) for each row

INSERT INTO REGION_MAPPING VALUES
    -- Format: (Original Region, Your New Region, Original Tower Prefix, Your New Prefix)
    ('Kuala Lumpur', 'Metro Central', 'KL', 'MC'),
    ('Selangor', 'Northern Region', 'SEL', 'NR'),
    ('Penang', 'Coastal West', 'PEN', 'CW'),
    ('Johor', 'Southern Region', 'JHR', 'SR'),
    ('Perak', 'Mountain District', 'PRK', 'MD'),
    ('Sabah', 'Eastern Territory', 'SBH', 'ET'),
    ('Sarawak', 'Western Territory', 'SWK', 'WT'),
    ('Melaka', 'Heritage Zone', 'MLK', 'HZ'),
    ('Negeri Sembilan', 'Central Plains', 'NS', 'CP'),
    ('Kedah', 'Northern Plains', 'KDH', 'NP'),
    ('Kelantan', 'Eastern Coast', 'KTN', 'EC'),
    ('Terengganu', 'Coastal East', 'TRG', 'CE'),
    ('Pahang', 'Highland Region', 'PHG', 'HR'),
    ('Perlis', 'Border Region', 'PLS', 'BR'),
    ('Putrajaya', 'Capital District', 'PTJ', 'CD'),
    ('Labuan', 'Island Territory', 'LBN', 'IT');

-- View your mappings before applying
SELECT * FROM REGION_MAPPING;

/*-----------------------------------------------------------------------------
  STEP 2: UPDATE NETWORK PERFORMANCE TABLE
-----------------------------------------------------------------------------*/

UPDATE TELCO_OPERATIONS_AI.RAW.NETWORK_PERFORMANCE np
SET 
    REGION = rm.NEW_REGION,
    TOWER_NAME = REPLACE(
        REPLACE(np.TOWER_NAME, rm.OLD_REGION, rm.NEW_REGION),
        ' ' || rm.OLD_REGION,
        ' ' || rm.NEW_REGION
    ),
    TOWER_ID = REPLACE(np.TOWER_ID, '_' || rm.OLD_PREFIX || '_', '_' || rm.NEW_PREFIX || '_')
FROM REGION_MAPPING rm
WHERE np.REGION = rm.OLD_REGION;

/*-----------------------------------------------------------------------------
  STEP 3: UPDATE INFRASTRUCTURE CAPACITY TABLE
-----------------------------------------------------------------------------*/

UPDATE TELCO_OPERATIONS_AI.RAW.INFRASTRUCTURE_CAPACITY ic
SET 
    REGION = rm.NEW_REGION,
    TOWER_NAME = REPLACE(
        REPLACE(ic.TOWER_NAME, rm.OLD_REGION, rm.NEW_REGION),
        ' ' || rm.OLD_REGION,
        ' ' || rm.NEW_REGION
    ),
    TOWER_ID = REPLACE(ic.TOWER_ID, '_' || rm.OLD_PREFIX || '_', '_' || rm.NEW_PREFIX || '_')
FROM REGION_MAPPING rm
WHERE ic.REGION = rm.OLD_REGION;

/*-----------------------------------------------------------------------------
  STEP 4: UPDATE CUSTOMER FEEDBACK SUMMARY TABLE
-----------------------------------------------------------------------------*/

UPDATE TELCO_OPERATIONS_AI.RAW.CUSTOMER_FEEDBACK_SUMMARY cfs
SET REGION = rm.NEW_REGION
FROM REGION_MAPPING rm
WHERE cfs.REGION = rm.OLD_REGION;

/*-----------------------------------------------------------------------------
  STEP 5: VERIFY THE CHANGES
-----------------------------------------------------------------------------*/

-- Check regions in each table
SELECT 'NETWORK_PERFORMANCE' AS TABLE_NAME, REGION, COUNT(*) AS RECORD_COUNT 
FROM TELCO_OPERATIONS_AI.RAW.NETWORK_PERFORMANCE 
GROUP BY REGION 
ORDER BY REGION;

SELECT 'INFRASTRUCTURE_CAPACITY' AS TABLE_NAME, REGION, COUNT(*) AS RECORD_COUNT 
FROM TELCO_OPERATIONS_AI.RAW.INFRASTRUCTURE_CAPACITY 
GROUP BY REGION 
ORDER BY REGION;

SELECT 'CUSTOMER_FEEDBACK_SUMMARY' AS TABLE_NAME, REGION, COUNT(*) AS RECORD_COUNT 
FROM TELCO_OPERATIONS_AI.RAW.CUSTOMER_FEEDBACK_SUMMARY 
GROUP BY REGION 
ORDER BY REGION;

-- Sample tower names to verify updates
SELECT DISTINCT TOWER_ID, TOWER_NAME, REGION 
FROM TELCO_OPERATIONS_AI.RAW.NETWORK_PERFORMANCE 
ORDER BY REGION 
LIMIT 20;

/*-----------------------------------------------------------------------------
  STEP 6: REFRESH VIEWS (if any views depend on these tables)
-----------------------------------------------------------------------------*/

-- Views will automatically reflect the updated base table data
-- No action needed unless you have materialized views

/*=============================================================================
  QUICK CUSTOMIZATION PRESETS
  
  Uncomment ONE of the following blocks to use a preset configuration,
  or create your own custom mapping above.
=============================================================================*/

/*
-- PRESET: US REGIONS
DELETE FROM REGION_MAPPING;
INSERT INTO REGION_MAPPING VALUES
    ('Kuala Lumpur', 'New York Metro', 'KL', 'NYC'),
    ('Selangor', 'Los Angeles', 'SEL', 'LA'),
    ('Penang', 'Chicago', 'PEN', 'CHI'),
    ('Johor', 'Houston', 'JHR', 'HOU'),
    ('Perak', 'Phoenix', 'PRK', 'PHX'),
    ('Sabah', 'Philadelphia', 'SBH', 'PHL'),
    ('Sarawak', 'San Antonio', 'SWK', 'SA'),
    ('Melaka', 'San Diego', 'MLK', 'SD'),
    ('Negeri Sembilan', 'Dallas', 'NS', 'DAL'),
    ('Kedah', 'Austin', 'KDH', 'AUS'),
    ('Kelantan', 'Jacksonville', 'KTN', 'JAX'),
    ('Terengganu', 'San Jose', 'TRG', 'SJ'),
    ('Pahang', 'Fort Worth', 'PHG', 'FTW'),
    ('Perlis', 'Columbus', 'PLS', 'COL'),
    ('Putrajaya', 'Charlotte', 'PTJ', 'CLT'),
    ('Labuan', 'Seattle', 'LBN', 'SEA');
*/

/*
-- PRESET: EUROPEAN REGIONS
DELETE FROM REGION_MAPPING;
INSERT INTO REGION_MAPPING VALUES
    ('Kuala Lumpur', 'London', 'KL', 'LON'),
    ('Selangor', 'Paris', 'SEL', 'PAR'),
    ('Penang', 'Berlin', 'PEN', 'BER'),
    ('Johor', 'Madrid', 'JHR', 'MAD'),
    ('Perak', 'Rome', 'PRK', 'ROM'),
    ('Sabah', 'Amsterdam', 'SBH', 'AMS'),
    ('Sarawak', 'Vienna', 'SWK', 'VIE'),
    ('Melaka', 'Brussels', 'MLK', 'BRU'),
    ('Negeri Sembilan', 'Munich', 'NS', 'MUC'),
    ('Kedah', 'Milan', 'KDH', 'MIL'),
    ('Kelantan', 'Barcelona', 'KTN', 'BCN'),
    ('Terengganu', 'Dublin', 'TRG', 'DUB'),
    ('Pahang', 'Zurich', 'PHG', 'ZRH'),
    ('Perlis', 'Stockholm', 'PLS', 'STO'),
    ('Putrajaya', 'Copenhagen', 'PTJ', 'CPH'),
    ('Labuan', 'Oslo', 'LBN', 'OSL');
*/

/*
-- PRESET: GENERIC REGIONS (Region A, B, C, etc.)
DELETE FROM REGION_MAPPING;
INSERT INTO REGION_MAPPING VALUES
    ('Kuala Lumpur', 'Region Alpha', 'KL', 'RA'),
    ('Selangor', 'Region Beta', 'SEL', 'RB'),
    ('Penang', 'Region Gamma', 'PEN', 'RG'),
    ('Johor', 'Region Delta', 'JHR', 'RD'),
    ('Perak', 'Region Epsilon', 'PRK', 'RE'),
    ('Sabah', 'Region Zeta', 'SBH', 'RZ'),
    ('Sarawak', 'Region Eta', 'SWK', 'RH'),
    ('Melaka', 'Region Theta', 'MLK', 'RT'),
    ('Negeri Sembilan', 'Region Iota', 'NS', 'RI'),
    ('Kedah', 'Region Kappa', 'KDH', 'RK'),
    ('Kelantan', 'Region Lambda', 'KTN', 'RL'),
    ('Terengganu', 'Region Mu', 'TRG', 'RM'),
    ('Pahang', 'Region Nu', 'PHG', 'RN'),
    ('Perlis', 'Region Xi', 'PLS', 'RX'),
    ('Putrajaya', 'Region Omicron', 'PTJ', 'RO'),
    ('Labuan', 'Region Pi', 'LBN', 'RP');
*/

COMMIT;

SELECT '✅ Region customization complete!' AS STATUS;
