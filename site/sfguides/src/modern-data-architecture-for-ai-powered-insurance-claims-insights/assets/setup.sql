-- Step 3a: Create Warehouse, Database, Schema, and Stages

CREATE WAREHOUSE IF NOT EXISTS INSURANCE_CLAIMS_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE INSURANCE_CLAIMS_WH;

CREATE DATABASE IF NOT EXISTS INSURANCE_CLAIMS_INSIGHTS_DB;

CREATE SCHEMA IF NOT EXISTS INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS;

CREATE STAGE IF NOT EXISTS INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE 
  DIRECTORY = (ENABLE = TRUE) 
  COMMENT = 'Stage to store raw data files';

CREATE STAGE IF NOT EXISTS INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.ML_MODELS
  DIRECTORY = (ENABLE = TRUE) 
  COMMENT = 'Stage to store model files';

-- Step 3b: Create Catalog Linked Database

CREATE DATABASE IF NOT EXISTS glue_database_linked_db
  LINKED_CATALOG = (
    CATALOG = 'glue_db_catalog_integration'
  );

-- Step 3c: Upload data and model files to stages 

PUT policy_details.csv @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT raud_flags.csv @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT adjuster_notes.parquet @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT fnol_reports.parquet @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT initial_estimates.parquet @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT fraud_detection_model.pkl @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.ML_MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
PUT fraud_model.py @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.ML_MODELS AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

-- Step 3d: Create Iceberg Tables in the Catalog Linked Database

USE DATABASE GLUE_DATABASE_LINKED_DB;
USE SCHEMA INSURANCE_CLAIMS_ICEBERG_GLUE_DB;
CREATE ICEBERG TABLE IF NOT EXISTS "fnol_reports" (
    "claim_id" STRING,
    "policy_number" STRING,
    "date_of_loss" DATE,
    "time_of_loss" TIME,
    "date_reported" DATE,
    "claimant_name" STRING,
    "claimant_phone" STRING,
    "claimant_email" STRING,
    "loss_location_address" STRING,
    "loss_location_city" STRING,
    "loss_location_state" STRING,
    "loss_location_zip" STRING,
    "vehicle_year" INTEGER,
    "vehicle_make" STRING,
    "vehicle_model" STRING,
    "vehicle_vin" STRING,
    "loss_type" STRING,
    "loss_description" STRING,
    "police_report_filed" BOOLEAN,
    "police_report_number" STRING,
    "injuries_reported" BOOLEAN,
    "injury_description" STRING,
    "other_party_involved" BOOLEAN,
    "other_party_name" STRING,
    "other_party_phone" STRING,
    "other_party_insurance" STRING,
    "tow_required" BOOLEAN,
    "reported_by" STRING,
    "reporter_relationship" STRING
)
BASE_LOCATION = 's3://<account-id>-us-west-2-insurance-claims-iceberg-data/fnol_reports/'
AUTO_REFRESH = TRUE;


CREATE ICEBERG TABLE IF NOT EXISTS "adjuster_notes" (
    "note_id" STRING,
    "claim_id" STRING,
    "adjuster_id" STRING,
    "adjuster_name" STRING,
    "note_date" DATE,
    "note_time" TIME,
    "note_type" STRING,
    "note_content" STRING
)
BASE_LOCATION = 's3://<account-id>-us-west-2-insurance-claims-iceberg-data/adjuster_notes/'
AUTO_REFRESH = TRUE;


CREATE ICEBERG TABLE IF NOT EXISTS "initial_estimates" (
    "estimate_id" STRING,
    "claim_id" STRING,
    "estimate_date" DATE,
    "estimate_type" STRING,
    "estimator_name" STRING,
    "shop_name" STRING,
    "labor_hours" FLOAT,
    "labor_rate" FLOAT,
    "labor_total" FLOAT,
    "parts_total" FLOAT,
    "paint_materials" FLOAT,
    "sublet_total" FLOAT,
    "other_charges" FLOAT,
    "subtotal" FLOAT,
    "tax_rate" FLOAT,
    "tax_amount" FLOAT,
    "total_estimate" FLOAT,
    "deductible" FLOAT,
    "net_payable" FLOAT,
    "status" STRING,
    "notes" TEXT
)
BASE_LOCATION = 's3://<account-id>-us-west-2-insurance-claims-iceberg-data/initial_estimates/'
AUTO_REFRESH = TRUE;

-- Step 3e: Load data into Iceberg Tables

COPY INTO GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.fnol_reports
FROM @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE/fnol_reports.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

SELECT COUNT(*) FROM GLUE_DATABASE_LINKED_DB."INSURANCE_CLAIMS_ICEBERG_GLUE_DB"."fnol_reports";


COPY INTO GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.adjuster_notes
FROM @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE/adjuster_notes.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

SELECT COUNT(*) FROM GLUE_DATABASE_LINKED_DB."INSURANCE_CLAIMS_ICEBERG_GLUE_DB"."adjuster_notes";

COPY INTO GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.initial_estimates
FROM @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE/initial_estimates.parquet
FILE_FORMAT = (TYPE = PARQUET)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;

SELECT COUNT(*) FROM GLUE_DATABASE_LINKED_DB."INSURANCE_CLAIMS_ICEBERG_GLUE_DB"."initial_estimates";

-- Step 3f: Create Snowflake Native Tables

USE DATABASE INSURANCE_CLAIMS_INSIGHTS_DB;
USE SCHEMA CLAIMS_ANALYTICS;

CREATE OR REPLACE TABLE FRAUD_FLAGS (
    flag_id VARCHAR(20),
    claim_id VARCHAR(20),
    flag_date DATE,
    flag_type VARCHAR(50),
    flag_source VARCHAR(50),
    risk_score NUMBER,
    flag_description VARCHAR(500),
    siu_referral VARCHAR(5),
    siu_case_number VARCHAR(20),
    investigation_status VARCHAR(20),
    investigation_outcome VARCHAR(30),
    investigator_id VARCHAR(20),
    investigator_name VARCHAR(50),
    red_flags_identified VARCHAR(200),
    prior_claims_count NUMBER,
    prior_fraud_indicators VARCHAR(100),
    resolution_date DATE,
    resolution_notes VARCHAR(500)
);

CREATE OR REPLACE TABLE POLICY_DETAILS (
    policy_number VARCHAR(20),
    policy_type VARCHAR(50),
    effective_date DATE,
    expiration_date DATE,
    policyholder_name VARCHAR(100),
    policyholder_dob DATE,
    policyholder_address VARCHAR(200),
    policyholder_city VARCHAR(50),
    policyholder_state VARCHAR(2),
    policyholder_zip VARCHAR(10),
    coverage_liability_limit VARCHAR(50),
    coverage_collision_deductible NUMBER,
    coverage_comprehensive_deductible NUMBER,
    coverage_pip_limit NUMBER,
    coverage_um_uim_limit VARCHAR(50),
    coverage_rental_daily NUMBER,
    coverage_rental_max NUMBER,
    annual_premium NUMBER(10,2),
    payment_frequency VARCHAR(20),
    policy_status VARCHAR(20),
    drivers_count NUMBER,
    vehicles_count NUMBER,
    prior_claims_3yr NUMBER,
    discount_good_driver VARCHAR(5),
    discount_multi_policy VARCHAR(5),
    discount_safe_vehicle VARCHAR(5),
    risk_tier VARCHAR(30),
    underwriting_score NUMBER
);

-- Step 3g: Load data into Native Tables

COPY INTO INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.POLICY_DETAILS
FROM @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE/policy_details.csv
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

COPY INTO INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.FRAUD_FLAGS
FROM @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.DATA_STAGE/fraud_flags.csv
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

-- Step 3h: Verify data loaded successfully

SELECT 'fnol_reports' AS table_name, COUNT(*) AS row_count FROM GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.fnol_reports
UNION ALL
SELECT 'adjuster_notes', COUNT(*) FROM GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.adjuster_notes
UNION ALL
SELECT 'initial_estimates', COUNT(*) FROM GLUE_DATABASE_LINKED_DB.INSURANCE_CLAIMS_ICEBERG_GLUE_DB.initial_estimates
UNION ALL
SELECT 'POLICY_DETAILS', COUNT(*) FROM INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.POLICY_DETAILS
UNION ALL
SELECT 'FRAUD_FLAGS', COUNT(*) FROM INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.FRAUD_FLAGS;

-- Step 3i: Verify model files uploaded successfully

LIST @INSURANCE_CLAIMS_INSIGHTS_DB.CLAIMS_ANALYTICS.ML_MODELS;
