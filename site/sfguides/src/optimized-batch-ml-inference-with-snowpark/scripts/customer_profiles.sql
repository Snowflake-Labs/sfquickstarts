-- ============================================================================
-- Snowflake seed script for the Optimized Batch ML Inference quickstart.
--
-- Creates the BATCH_INF_DEMO database and populates CUSTOMER_PROFILES with
-- 500 synthetic customer profiles to join against the ingested transactions.
-- ============================================================================

USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS BATCH_INF_DEMO;
CREATE SCHEMA IF NOT EXISTS BATCH_INF_DEMO.PUBLIC;
USE SCHEMA BATCH_INF_DEMO.PUBLIC;

CREATE OR REPLACE TABLE CUSTOMER_PROFILES (
    customer_id     INT,
    home_country    STRING,
    credit_limit    NUMBER(10, 2),
    risk_tier       STRING
);

INSERT INTO CUSTOMER_PROFILES
SELECT
    SEQ4() + 1 AS customer_id,
    CASE MOD(SEQ4(), 6)
        WHEN 0 THEN 'US' WHEN 1 THEN 'CA' WHEN 2 THEN 'GB'
        WHEN 3 THEN 'FR' WHEN 4 THEN 'DE' ELSE 'JP'
    END AS home_country,
    ROUND(UNIFORM(2000, 25000, RANDOM(42)), 2) AS credit_limit,
    CASE MOD(SEQ4(), 3)
        WHEN 0 THEN 'LOW' WHEN 1 THEN 'MEDIUM' ELSE 'HIGH'
    END AS risk_tier
FROM TABLE(GENERATOR(ROWCOUNT => 500));

SELECT COUNT(*) AS total_customers FROM CUSTOMER_PROFILES;
