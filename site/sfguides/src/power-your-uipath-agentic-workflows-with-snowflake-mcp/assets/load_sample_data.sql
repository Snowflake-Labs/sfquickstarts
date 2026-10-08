-- =============================================================================
-- Shipping Logistics Demo — Load Sample Data
-- =============================================================================
-- This script populates all tables with sample data for the quickstart.
--
-- Prerequisites:
--   1. Run setup_ddl.sql first to create the database, schema, and tables
--   2. Upload the CSV files from the assets/data/ folder to a Snowflake stage
--
-- Run as: ACCOUNTADMIN (or role with INSERT privileges on LOGISTICS_C.SHIPPING_MARTS)
-- =============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE LOGISTICS_C;
USE SCHEMA SHIPPING_MARTS;
USE WAREHOUSE COMPUTE_WH;

-- =============================================================================
-- 1. DIMENSION TABLES (small — direct INSERT)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- DIM_PORTS (18 rows)
-- ---------------------------------------------------------------------------
INSERT INTO DIM_PORTS (PORT_CODE, PORT_NAME, COUNTRY, REGION, TERMINAL, TIMEZONE) VALUES
('BEANR', 'Antwerp', 'Belgium', 'North Europe', 'PSA Antwerp', 'Europe/Brussels'),
('DEHAM', 'Hamburg', 'Germany', 'North Europe', 'HHLA Container Terminal Altenwerder', 'Europe/Berlin'),
('DZBJA', 'Bejaia', 'Algeria', 'Mediterranean', 'Port of Bejaia', 'Africa/Algiers'),
('EGPSD', 'Port Said', 'Egypt', 'Eastern Mediterranean', 'Suez Canal Container Terminal', 'Africa/Cairo'),
('ESALG', 'Algeciras', 'Spain', 'Mediterranean', 'APM Terminals Algeciras', 'Europe/Madrid'),
('ESVLC', 'Valencia', 'Spain', 'Mediterranean', 'Valencia Container Terminal', 'Europe/Madrid'),
('FRFOS', 'Fos-sur-Mer', 'France', 'Mediterranean', 'Marseille Fos Port - West Terminal', 'Europe/Paris'),
('FRLEH', 'Le Havre', 'France', 'North Europe', 'Terminal de France', 'Europe/Paris'),
('FRMRS', 'Marseille', 'France', 'Mediterranean', 'Marseille Fos Port - East Terminal', 'Europe/Paris'),
('GRPIR', 'Piraeus', 'Greece', 'Eastern Mediterranean', 'Piraeus Container Terminal', 'Europe/Athens'),
('ILHFA', 'Haifa', 'Israel', 'Eastern Mediterranean', 'Haifa Port', 'Asia/Jerusalem'),
('ITGIT', 'Gioia Tauro', 'Italy', 'Mediterranean', 'Medcenter Container Terminal', 'Europe/Rome'),
('ITGOA', 'Genoa', 'Italy', 'Mediterranean', 'Genoa Port Terminal', 'Europe/Rome'),
('LBBEY', 'Beirut', 'Lebanon', 'Eastern Mediterranean', 'Port of Beirut', 'Asia/Beirut'),
('MAPTM', 'Tanger Med', 'Morocco', 'Mediterranean', 'Tanger Med Port Authority', 'Africa/Casablanca'),
('MTMAR', 'Marsaxlokk', 'Malta', 'Mediterranean', 'Malta Freeport Terminal', 'Europe/Malta'),
('NLRTM', 'Rotterdam', 'Netherlands', 'North Europe', 'APM Terminals Rotterdam', 'Europe/Amsterdam'),
('TRIST', 'Istanbul', 'Turkey', 'Eastern Mediterranean', 'Kumport Terminal', 'Europe/Istanbul');

-- ---------------------------------------------------------------------------
-- DIM_VESSELS (15 rows)
-- ---------------------------------------------------------------------------
INSERT INTO DIM_VESSELS (VESSEL_ID, VESSEL_NAME, VESSEL_TYPE, CAPACITY_TEU, FLAG_COUNTRY, BUILD_YEAR) VALUES
('VES-001', 'MED MARCO POLO', 'Container', 16020, 'France', 2012),
('VES-002', 'MED JULES VERNE', 'Container', 16000, 'France', 2013),
('VES-003', 'MED KERGUELEN', 'Container', 17722, 'United Kingdom', 2015),
('VES-004', 'MED BOUGAINVILLE', 'Container', 17722, 'France', 2015),
('VES-005', 'MED ANTOINE DE SAINT EXUPERY', 'Container', 20954, 'France', 2018),
('VES-006', 'MED JEAN MERMOZ', 'Container', 20954, 'France', 2018),
('VES-007', 'MED LOUIS BLERIOT', 'Container', 20954, 'Malta', 2018),
('VES-008', 'MED JACQUES SAADE', 'Container', 23112, 'France', 2020),
('VES-009', 'MED CHAMPS ELYSEES', 'Container', 23112, 'France', 2020),
('VES-010', 'MED RIVIERA', 'Container', 23112, 'Malta', 2020),
('VES-011', 'MED PALAIS ROYAL', 'Container', 23112, 'France', 2021),
('VES-012', 'MED SORBONNE', 'Container', 23112, 'France', 2021),
('VES-013', 'MED MARSEILLE', 'Container', 14000, 'France', 2010),
('VES-014', 'MED THALASSA', 'Container', 11400, 'Malta', 2008),
('VES-015', 'MED MEDEA', 'Container', 9400, 'France', 2006);

-- ---------------------------------------------------------------------------
-- DIM_ROUTES (25 rows)
-- ---------------------------------------------------------------------------
INSERT INTO DIM_ROUTES (ROUTE_ID, ROUTE_NAME, ORIGIN_PORT_CODE, DESTINATION_PORT_CODE, TRADE_LANE, STANDARD_TRANSIT_DAYS, SERVICE_FREQUENCY) VALUES
('RTE-0001', 'Le Havre → Tanger Med', 'FRLEH', 'MAPTM', 'Europe-Mediterranean', 7, 'Weekly'),
('RTE-0002', 'Le Havre → Port Said', 'FRLEH', 'EGPSD', 'Europe-Mediterranean', 5, 'Weekly'),
('RTE-0003', 'Le Havre → Algeciras', 'FRLEH', 'ESALG', 'Europe-Mediterranean', 7, 'Weekly'),
('RTE-0004', 'Le Havre → Bejaia', 'FRLEH', 'DZBJA', 'Europe-Mediterranean', 4, 'Bi-weekly'),
('RTE-0005', 'Hamburg → Fos-sur-Mer', 'DEHAM', 'FRFOS', 'Europe-Mediterranean', 11, 'Weekly'),
('RTE-0006', 'Hamburg → Port Said', 'DEHAM', 'EGPSD', 'Europe-Mediterranean', 12, 'Weekly'),
('RTE-0007', 'Hamburg → Algeciras', 'DEHAM', 'ESALG', 'Europe-Mediterranean', 11, 'Weekly'),
('RTE-0008', 'Hamburg → Genoa', 'DEHAM', 'ITGOA', 'Europe-Mediterranean', 11, 'Bi-weekly'),
('RTE-0009', 'Rotterdam → Algeciras', 'NLRTM', 'ESALG', 'Europe-Mediterranean', 10, 'Bi-weekly'),
('RTE-0010', 'Rotterdam → Fos-sur-Mer', 'NLRTM', 'FRFOS', 'Europe-Mediterranean', 10, 'Bi-weekly'),
('RTE-0011', 'Rotterdam → Beirut', 'NLRTM', 'LBBEY', 'Europe-Mediterranean', 11, 'Weekly'),
('RTE-0012', 'Rotterdam → Marsaxlokk', 'NLRTM', 'MTMAR', 'Europe-Mediterranean', 5, 'Weekly'),
('RTE-0013', 'Antwerp → Piraeus', 'BEANR', 'GRPIR', 'Europe-Mediterranean', 7, 'Weekly'),
('RTE-0014', 'Antwerp → Haifa', 'BEANR', 'ILHFA', 'Europe-Mediterranean', 7, 'Bi-weekly'),
('RTE-0015', 'Antwerp → Gioia Tauro', 'BEANR', 'ITGIT', 'Europe-Mediterranean', 6, 'Bi-weekly'),
('RTE-0016', 'Antwerp → Fos-sur-Mer', 'BEANR', 'FRFOS', 'Europe-Mediterranean', 6, 'Bi-weekly'),
('RTE-0017', 'Istanbul → Fos-sur-Mer', 'TRIST', 'FRFOS', 'Europe-Mediterranean', 6, 'Weekly'),
('RTE-0018', 'Istanbul → Marseille', 'TRIST', 'FRMRS', 'Europe-Mediterranean', 2, 'Weekly'),
('RTE-0019', 'Istanbul → Marsaxlokk', 'TRIST', 'MTMAR', 'Europe-Mediterranean', 3, 'Bi-weekly'),
('RTE-0020', 'Algeciras → Istanbul', 'ESALG', 'TRIST', 'Europe-Mediterranean', 5, 'Weekly'),
('RTE-0021', 'Algeciras → Bejaia', 'ESALG', 'DZBJA', 'Europe-Mediterranean', 3, 'Bi-weekly'),
('RTE-0022', 'Fos-sur-Mer → Marseille', 'FRFOS', 'FRMRS', 'Europe-Mediterranean', 5, 'Bi-weekly'),
('RTE-0023', 'Fos-sur-Mer → Piraeus', 'FRFOS', 'GRPIR', 'Europe-Mediterranean', 5, 'Bi-weekly'),
('RTE-0024', 'Fos-sur-Mer → Genoa', 'FRFOS', 'ITGOA', 'Europe-Mediterranean', 3, 'Weekly'),
('RTE-0025', 'Bejaia → Genoa', 'DZBJA', 'ITGOA', 'Europe-Mediterranean', 6, 'Weekly');

-- ---------------------------------------------------------------------------
-- DIM_CUSTOMERS (50 rows)
-- ---------------------------------------------------------------------------
INSERT INTO DIM_CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, INDUSTRY, COUNTRY, REGION, CONTRACT_TIER, CREATED_DATE) VALUES
('CUST-0001', 'EuroLogis GmbH', 'Pharmaceuticals', 'Morocco', 'Europe-Mediterranean', 'Gold', '2024-03-07'),
('CUST-0002', 'MedTrans SA', 'Electronics', 'France', 'Europe-Mediterranean', 'Gold', '2025-07-29'),
('CUST-0003', 'Atlas Freight Ltd', 'FMCG', 'Spain', 'Europe-Mediterranean', 'Gold', '2024-04-06'),
('CUST-0004', 'Aegean Exports Co', 'FMCG', 'Morocco', 'Europe-Mediterranean', 'Standard', '2025-03-21'),
('CUST-0005', 'Sahara Trading SARL', 'Electronics', 'Egypt', 'Europe-Mediterranean', 'Bronze', '2023-07-27'),
('CUST-0006', 'Levant Commodities', 'Agriculture', 'France', 'Europe-Mediterranean', 'Silver', '2023-11-18'),
('CUST-0007', 'Adriatic Shipping SpA', 'Electronics', 'Belgium', 'Europe-Mediterranean', 'Bronze', '2025-05-26'),
('CUST-0008', 'Baltic Import Export', 'FMCG', 'Belgium', 'Europe-Mediterranean', 'Gold', '2025-07-30'),
('CUST-0009', 'Iberian Cargo SL', 'Electronics', 'Germany', 'Europe-Mediterranean', 'Bronze', '2023-06-18'),
('CUST-0010', 'Alpine Logistics AG', 'Chemicals', 'Egypt', 'Europe-Mediterranean', 'Bronze', '2023-07-29'),
('CUST-0011', 'Bosphorus Trade AS', 'Automotive', 'Turkey', 'Europe-Mediterranean', 'Gold', '2023-04-02'),
('CUST-0012', 'Nile Valley Industries', 'Electronics', 'Germany', 'Europe-Mediterranean', 'Bronze', '2023-07-06'),
('CUST-0013', 'Maghreb Distribution', 'Pharmaceuticals', 'Egypt', 'Europe-Mediterranean', 'Bronze', '2024-03-20'),
('CUST-0014', 'Hellenic Marine Supplies', 'FMCG', 'Germany', 'Europe-Mediterranean', 'Gold', '2023-12-25'),
('CUST-0015', 'Rhine Valley Chemicals', 'FMCG', 'Netherlands', 'Europe-Mediterranean', 'Gold', '2023-06-10'),
('CUST-0016', 'Danube Agri Corp', 'FMCG', 'Germany', 'Europe-Mediterranean', 'Standard', '2025-01-21'),
('CUST-0017', 'Cote dAzur Imports', 'Electronics', 'Belgium', 'Europe-Mediterranean', 'Silver', '2024-10-18'),
('CUST-0018', 'Catalonia Fresh Produce', 'Chemicals', 'Spain', 'Europe-Mediterranean', 'Bronze', '2023-11-14'),
('CUST-0019', 'Teutonic Auto Parts', 'Pharmaceuticals', 'Germany', 'Europe-Mediterranean', 'Silver', '2024-05-04'),
('CUST-0020', 'Adriatic Pharma doo', 'Pharmaceuticals', 'Spain', 'Europe-Mediterranean', 'Silver', '2024-07-16'),
('CUST-0021', 'Marseille Textiles SARL', 'Electronics', 'Netherlands', 'Europe-Mediterranean', 'Silver', '2023-12-01'),
('CUST-0022', 'Rotterdam Bulk Traders BV', 'Chemicals', 'France', 'Europe-Mediterranean', 'Silver', '2023-07-14'),
('CUST-0023', 'Antwerp Electronics NV', 'Automotive', 'Belgium', 'Europe-Mediterranean', 'Standard', '2025-01-31'),
('CUST-0024', 'Hamburg Machinery GmbH', 'Automotive', 'Spain', 'Europe-Mediterranean', 'Bronze', '2025-03-29'),
('CUST-0025', 'Genoa Wine Exports Srl', 'Pharmaceuticals', 'Turkey', 'Europe-Mediterranean', 'Standard', '2023-05-11'),
('CUST-0026', 'Valencia Ceramics SL', 'Pharmaceuticals', 'Turkey', 'Europe-Mediterranean', 'Silver', '2025-02-03'),
('CUST-0027', 'Piraeus Steel Works SA', 'FMCG', 'Spain', 'Europe-Mediterranean', 'Bronze', '2023-09-29'),
('CUST-0028', 'Istanbul Garments AS', 'Textiles', 'Greece', 'Europe-Mediterranean', 'Standard', '2024-10-27'),
('CUST-0029', 'Cairo Consumer Goods', 'FMCG', 'Italy', 'Europe-Mediterranean', 'Standard', '2025-07-31'),
('CUST-0030', 'Tangier Automotive SA', 'Agriculture', 'France', 'Europe-Mediterranean', 'Gold', '2025-05-29'),
('CUST-0031', 'Malta Spirits Ltd', 'Pharmaceuticals', 'Italy', 'Europe-Mediterranean', 'Standard', '2024-03-01'),
('CUST-0032', 'Beirut Fresh Foods', 'Automotive', 'Greece', 'Europe-Mediterranean', 'Standard', '2024-03-01'),
('CUST-0033', 'Algiers Petrochemicals', 'Electronics', 'Morocco', 'Europe-Mediterranean', 'Bronze', '2024-04-14'),
('CUST-0034', 'Haifa Tech Components', 'Agriculture', 'France', 'Europe-Mediterranean', 'Gold', '2023-12-04'),
('CUST-0035', 'Naples Fashion House Srl', 'Textiles', 'Netherlands', 'Europe-Mediterranean', 'Bronze', '2025-07-10'),
('CUST-0036', 'Lisbon Cork Exports Lda', 'Chemicals', 'Greece', 'Europe-Mediterranean', 'Silver', '2024-07-25'),
('CUST-0037', 'Zurich Precision AG', 'Automotive', 'Netherlands', 'Europe-Mediterranean', 'Silver', '2024-05-31'),
('CUST-0038', 'Vienna Organic Foods', 'Automotive', 'Netherlands', 'Europe-Mediterranean', 'Silver', '2025-05-29'),
('CUST-0039', 'Warsaw Electronics SA', 'Chemicals', 'Italy', 'Europe-Mediterranean', 'Gold', '2024-02-27'),
('CUST-0040', 'Prague Glass Works sro', 'Chemicals', 'Turkey', 'Europe-Mediterranean', 'Gold', '2025-07-10'),
('CUST-0041', 'Budapest Grain Trading Kft', 'Chemicals', 'Netherlands', 'Europe-Mediterranean', 'Silver', '2025-09-03'),
('CUST-0042', 'Bucharest Textiles SRL', 'FMCG', 'Egypt', 'Europe-Mediterranean', 'Gold', '2025-08-06'),
('CUST-0043', 'Sofia Chemicals AD', 'Pharmaceuticals', 'Turkey', 'Europe-Mediterranean', 'Gold', '2023-09-15'),
('CUST-0044', 'Zagreb Machinery doo', 'Textiles', 'Italy', 'Europe-Mediterranean', 'Silver', '2023-12-27'),
('CUST-0045', 'Ljubljana Wood Products', 'Electronics', 'Morocco', 'Europe-Mediterranean', 'Silver', '2025-02-03'),
('CUST-0046', 'Bratislava Auto Parts sro', 'Textiles', 'Egypt', 'Europe-Mediterranean', 'Standard', '2025-03-30'),
('CUST-0047', 'Tallinn Digital Systems', 'Textiles', 'Spain', 'Europe-Mediterranean', 'Bronze', '2024-09-19'),
('CUST-0048', 'Riga Timber Exports', 'Pharmaceuticals', 'Belgium', 'Europe-Mediterranean', 'Standard', '2023-04-25'),
('CUST-0049', 'Vilnius Pharma UAB', 'Textiles', 'Turkey', 'Europe-Mediterranean', 'Gold', '2025-02-21'),
('CUST-0050', 'Helsinki Paper Oy', 'FMCG', 'Germany', 'Europe-Mediterranean', 'Bronze', '2025-10-11');

-- =============================================================================
-- 2. FACT TABLES & DOCS (large — load from CSV via stage)
-- =============================================================================
-- The fact tables and shipping docs are loaded from CSV files.
-- Upload the CSV files from the assets/ folder to a Snowflake stage, then COPY INTO.

-- ---------------------------------------------------------------------------
-- Step 2a: Create a file format and stage for loading
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FILE FORMAT LOGISTICS_C.SHIPPING_MARTS.CSV_LOAD_FORMAT
  TYPE = CSV
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  SKIP_HEADER = 1
  NULL_IF = ('', '\\N')
  EMPTY_FIELD_AS_NULL = TRUE;

CREATE OR REPLACE STAGE LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE
  FILE_FORMAT = LOGISTICS_C.SHIPPING_MARTS.CSV_LOAD_FORMAT;

-- ---------------------------------------------------------------------------
-- Step 2b: Upload CSV files to stage
-- ---------------------------------------------------------------------------
-- IMPORTANT: PUT commands CANNOT be executed in Snowsight worksheets.
-- You must use SnowSQL or SnowCLI to upload files to a stage.
--
-- Option A: Using SnowSQL
--   snowsql -a <account> -u <user> -r ACCOUNTADMIN -w COMPUTE_WH
--   Then run these PUT commands in the SnowSQL session:

PUT file:///<path_to_assets>/fact_shipments.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE AUTO_COMPRESS=FALSE;
PUT file:///<path_to_assets>/fact_performance.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE AUTO_COMPRESS=FALSE;
PUT file:///<path_to_assets>/fact_events.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE AUTO_COMPRESS=FALSE;
PUT file:///<path_to_assets>/shipping_docs.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE AUTO_COMPRESS=FALSE;

-- Option B: Using SnowCLI
--   snow stage copy <local_path>/fact_shipments.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE --overwrite
--   snow stage copy <local_path>/fact_performance.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE --overwrite
--   snow stage copy <local_path>/fact_events.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE --overwrite
--   snow stage copy <local_path>/shipping_docs.csv @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE --overwrite
--
-- Option C: Using Snowsight UI
--   1. Navigate to Data → Databases → LOGISTICS_C → SHIPPING_MARTS → Stages → DATA_LOAD_STAGE
--   2. Click the '+' button in the top right to upload files
--   3. In the dialog that opens, select all 4 CSV files and upload them
--   4. Verify the files appear in the stage listing
--
-- After uploading (any option), verify files are on stage:
--   LIST @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE;

-- ---------------------------------------------------------------------------
-- Step 2c: Load data from stage into tables
-- ---------------------------------------------------------------------------

COPY INTO FACT_SHIPMENTS (SHIPMENT_ID, CUSTOMER_ID, ROUTE_ID, VESSEL_ID, CONTAINER_COUNT, CONTAINER_TYPE, CARGO_TYPE, BOOKING_DATE, PLANNED_DEPARTURE, PLANNED_ARRIVAL, ACTUAL_DEPARTURE, ACTUAL_ARRIVAL, SHIPMENT_STATUS, TOTAL_WEIGHT_KG, FREIGHT_CHARGE_USD)
FROM @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE/fact_shipments.csv;

COPY INTO FACT_SHIPMENT_PERFORMANCE (SHIPMENT_ID, PLANNED_TRANSIT_DAYS, ACTUAL_TRANSIT_DAYS, DELAY_DAYS, DELAY_REASON, ON_TIME_FLAG)
FROM @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE/fact_performance.csv;

COPY INTO FACT_SHIPMENT_EVENTS (EVENT_ID, SHIPMENT_ID, EVENT_TYPE, PORT_CODE, EVENT_TIMESTAMP, REMARKS)
FROM @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE/fact_events.csv;

COPY INTO SHIPPING_DOCS (DOC_ID, CATEGORY, TITLE, CONTENT, REGION, PORT_CODE, EFFECTIVE_DATE, EXPIRY_DATE, TAGS)
FROM @LOGISTICS_C.SHIPPING_MARTS.DATA_LOAD_STAGE/shipping_docs.csv;

-- =============================================================================
-- 3. Validation
-- =============================================================================

SELECT 'DIM_CUSTOMERS' AS table_name, COUNT(*) AS row_count FROM DIM_CUSTOMERS
UNION ALL SELECT 'DIM_VESSELS', COUNT(*) FROM DIM_VESSELS
UNION ALL SELECT 'DIM_PORTS', COUNT(*) FROM DIM_PORTS
UNION ALL SELECT 'DIM_ROUTES', COUNT(*) FROM DIM_ROUTES
UNION ALL SELECT 'FACT_SHIPMENTS', COUNT(*) FROM FACT_SHIPMENTS
UNION ALL SELECT 'FACT_SHIPMENT_EVENTS', COUNT(*) FROM FACT_SHIPMENT_EVENTS
UNION ALL SELECT 'FACT_SHIPMENT_PERFORMANCE', COUNT(*) FROM FACT_SHIPMENT_PERFORMANCE
UNION ALL SELECT 'SHIPPING_DOCS', COUNT(*) FROM SHIPPING_DOCS
ORDER BY table_name;

-- Expected counts:
-- DIM_CUSTOMERS:             50
-- DIM_PORTS:                 18
-- DIM_ROUTES:                25
-- DIM_VESSELS:               15
-- FACT_SHIPMENTS:          1000
-- FACT_SHIPMENT_EVENTS:    2426
-- FACT_SHIPMENT_PERFORMANCE: 1000
-- SHIPPING_DOCS:             42
