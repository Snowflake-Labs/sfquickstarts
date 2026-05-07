-- ============================================================================
-- Snowday Sample Data Loader
-- Runs ALL vignette setup scripts in dependency order
-- Alternative to running each vignette's setup script individually
-- ============================================================================

USE DATABASE COCO_WORKSHOP;
USE SCHEMA SOURCE_DATA;
USE WAREHOUSE COCO_WORKSHOP_WH;

-- ============================================================================
-- Vignette 1: Bronze source tables (SAP + Oracle)
-- See: vignettes/01_pipeline_builder/setup/01_precreate_bronze.sql
-- ============================================================================

-- BRONZE_SAP_AP_INVOICES
CREATE OR REPLACE TABLE BRONZE_SAP_AP_INVOICES (
    INVOICE_ID          VARCHAR(20),
    INVOICE_NUMBER      VARCHAR(30),
    VENDOR_ID           VARCHAR(15),
    VENDOR_NAME         VARCHAR(100),
    INVOICE_DATE        DATE,
    DUE_DATE            DATE,
    INVOICE_AMOUNT      NUMBER(18,2),
    CURRENCY_CODE       VARCHAR(3),
    PAYMENT_TERMS       VARCHAR(20),
    PO_NUMBER           VARCHAR(20),
    LINE_DESCRIPTION    VARCHAR(200),
    GL_ACCOUNT          VARCHAR(20),
    COST_CENTER         VARCHAR(20),
    APPROVAL_STATUS     VARCHAR(20),
    CREATED_AT          TIMESTAMP_NTZ,
    SAP_COMPANY_CODE    VARCHAR(10),
    SAP_DOCUMENT_TYPE   VARCHAR(10)
);

INSERT INTO BRONZE_SAP_AP_INVOICES VALUES
('SAP-001', 'INV-2025-0001', 'V-1001', 'Acme Industrial Supply', '2025-01-15', '2025-02-14', 12500.00, 'USD', 'NET30', 'PO-4500001', 'Hydraulic pumps Q1 order', '5100-10', 'CC-ENG-01', 'APPROVED', '2025-01-15 08:30:00', '1000', 'KR'),
('SAP-002', 'INV-2025-0002', 'V-1002', 'Global Parts GmbH', '2025-01-22', '2025-03-22', 8750.50, 'EUR', 'NET60', 'PO-4500002', 'Precision bearings batch', '5100-20', 'CC-MFG-02', 'APPROVED', '2025-01-22 09:15:00', '2000', 'KR'),
('SAP-003', 'INV-2025-0003', 'V-1003', 'TechServ Solutions', '2025-02-01', '2025-03-03', 45000.00, 'USD', 'NET30', 'PO-4500003', 'IT consulting services Feb', '6200-10', 'CC-IT-01', 'PENDING', '2025-02-01 10:00:00', '1000', 'KR'),
('SAP-004', 'INV-2025-0004', 'V-1001', 'Acme Industrial Supply', '2025-02-10', '2025-03-12', 7200.00, 'USD', 'NET30', 'PO-4500004', 'Replacement valve assemblies', '5100-10', 'CC-ENG-01', 'APPROVED', '2025-02-10 14:20:00', '1000', 'KR'),
('SAP-005', 'INV-2025-0005', 'V-1004', 'UK Safety Supplies Ltd', '2025-02-15', '2025-04-16', 3200.00, 'GBP', 'NET60', 'PO-4500005', 'PPE quarterly restock', '5300-10', 'CC-OPS-03', 'APPROVED', '2025-02-15 11:45:00', '3000', 'KR'),
('SAP-006', 'INV-2025-0006', 'V-1005', 'CleanTech Environmental', '2025-03-01', '2025-03-31', 18900.00, 'USD', 'NET30', 'PO-4500006', 'Waste disposal services Q1', '6300-20', 'CC-FAC-01', 'APPROVED', '2025-03-01 08:00:00', '1000', 'KR'),
('SAP-007', 'INV-2025-0007', 'V-1002', 'Global Parts GmbH', '2025-03-10', '2025-05-09', 15400.75, 'EUR', 'NET60', 'PO-4500007', 'Motor assemblies spring batch', '5100-20', 'CC-MFG-02', 'PENDING', '2025-03-10 09:30:00', '2000', 'KR'),
('SAP-008', 'INV-2025-0008', 'V-1006', 'Express Logistics Inc', '2025-03-15', '2025-04-14', 6800.00, 'USD', 'NET30', 'PO-4500008', 'Freight charges March', '6100-10', 'CC-LOG-01', 'APPROVED', '2025-03-15 16:10:00', '1000', 'KR'),
('SAP-009', 'INV-2025-0009', 'V-1003', 'TechServ Solutions', '2025-04-01', '2025-05-01', 45000.00, 'USD', 'NET30', 'PO-4500009', 'IT consulting services Apr', '6200-10', 'CC-IT-01', 'APPROVED', '2025-04-01 10:00:00', '1000', 'KR'),
('SAP-010', 'INV-2025-0010', 'V-1007', 'Pacific Raw Materials', '2025-04-05', '2025-05-05', 92000.00, 'USD', 'NET30', 'PO-4500010', 'Steel alloy shipment Q2', '5000-10', 'CC-MFG-01', 'APPROVED', '2025-04-05 07:45:00', '1000', 'KR'),
('SAP-011', 'INV-2025-0011', 'V-1004', 'UK Safety Supplies Ltd', '2025-04-20', '2025-06-19', 4100.00, 'GBP', 'NET60', 'PO-4500011', 'Fire safety equipment', '5300-10', 'CC-OPS-03', 'PENDING', '2025-04-20 13:00:00', '3000', 'KR'),
('SAP-012', 'INV-2025-0012', 'V-1005', 'CleanTech Environmental', '2025-05-01', '2025-05-31', 18900.00, 'USD', 'NET30', 'PO-4500012', 'Waste disposal services Q2-M1', '6300-20', 'CC-FAC-01', 'APPROVED', '2025-05-01 08:00:00', '1000', 'KR'),
('SAP-013', 'INV-2025-0013', 'V-1008', 'Schneider Electric AG', '2025-05-10', '2025-07-09', 28500.00, 'EUR', 'NET60', 'PO-4500013', 'PLC controllers upgrade', '5200-10', 'CC-ENG-02', 'APPROVED', '2025-05-10 10:30:00', '2000', 'KR'),
('SAP-014', 'INV-2025-0014', 'V-1006', 'Express Logistics Inc', '2025-05-15', '2025-06-14', 7350.00, 'USD', 'NET30', 'PO-4500014', 'Freight charges May', '6100-10', 'CC-LOG-01', 'APPROVED', '2025-05-15 16:00:00', '1000', 'KR'),
('SAP-015', 'INV-2025-0015', 'V-1001', 'Acme Industrial Supply', '2025-06-01', '2025-07-01', 21000.00, 'USD', 'NET30', 'PO-4500015', 'Hydraulic pumps Q2 order', '5100-10', 'CC-ENG-01', 'PENDING', '2025-06-01 08:30:00', '1000', 'KR');


-- BRONZE_ORACLE_AP_INVOICES
CREATE OR REPLACE TABLE BRONZE_ORACLE_AP_INVOICES (
    INV_ID              VARCHAR(20),
    INV_NUM             VARCHAR(30),
    SUPPLIER_ID         VARCHAR(15),
    SUPPLIER_NAME       VARCHAR(100),
    INV_DATE            DATE,
    PAYMENT_DUE_DATE    DATE,
    TOTAL_AMOUNT        NUMBER(18,2),
    CURRENCY            VARCHAR(3),
    TERMS_CODE          VARCHAR(20),
    PURCHASE_ORDER      VARCHAR(20),
    DESCRIPTION         VARCHAR(200),
    ACCOUNT_CODE        VARCHAR(20),
    DEPT_CODE           VARCHAR(20),
    STATUS              VARCHAR(20),
    CREATION_DATE       TIMESTAMP_NTZ,
    ORACLE_ORG_ID       VARCHAR(10),
    ORACLE_SOURCE       VARCHAR(20)
);

INSERT INTO BRONZE_ORACLE_AP_INVOICES VALUES
('ORA-001', 'ORA-INV-50001', 'S-2001', 'Midwest Tool & Die Co', '2025-01-10', '2025-02-09', 34200.00, 'USD', 'N30', 'OP-7100001', 'Custom tooling for Line 3', 'A5100-40', 'D-ENG', 'VALIDATED', '2025-01-10 07:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-002', 'ORA-INV-50002', 'S-2002', 'Deutsche Industrie Werke', '2025-01-20', '2025-03-21', 19800.00, 'EUR', 'N60', 'OP-7100002', 'CNC machine calibration service', 'A6200-20', 'D-MFG', 'VALIDATED', '2025-01-20 08:30:00', 'ORG-102', 'AP_IMPORT'),
('ORA-003', 'ORA-INV-50003', 'S-2003', 'Summit Energy Corp', '2025-02-05', '2025-03-07', 67500.00, 'USD', 'N30', 'OP-7100003', 'Natural gas supply Feb', 'A6400-10', 'D-FAC', 'VALIDATED', '2025-02-05 06:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-004', 'ORA-INV-50004', 'S-2001', 'Midwest Tool & Die Co', '2025-02-18', '2025-03-20', 15600.00, 'USD', 'N30', 'OP-7100004', 'Replacement dies for stamping press', 'A5100-40', 'D-ENG', 'APPROVED', '2025-02-18 11:00:00', 'ORG-101', 'MANUAL'),
('ORA-005', 'ORA-INV-50005', 'S-2004', 'Yorkshire Chemical Ltd', '2025-02-25', '2025-04-26', 8900.00, 'GBP', 'N60', 'OP-7100005', 'Industrial solvents quarterly', 'A5400-10', 'D-OPS', 'VALIDATED', '2025-02-25 09:15:00', 'ORG-103', 'AP_IMPORT'),
('ORA-006', 'ORA-INV-50006', 'S-2005', 'Apex Staffing Solutions', '2025-03-01', '2025-03-31', 52000.00, 'USD', 'N30', 'OP-7100006', 'Contract labor March - assembly', 'A6500-10', 'D-HR', 'VALIDATED', '2025-03-01 07:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-007', 'ORA-INV-50007', 'S-2002', 'Deutsche Industrie Werke', '2025-03-12', '2025-05-11', 42300.00, 'EUR', 'N60', 'OP-7100007', 'Spare parts for robotic welders', 'A5100-50', 'D-MFG', 'PENDING', '2025-03-12 10:45:00', 'ORG-102', 'AP_IMPORT'),
('ORA-008', 'ORA-INV-50008', 'S-2006', 'National Insurance Brokers', '2025-03-15', '2025-04-14', 125000.00, 'USD', 'N30', 'OP-7100008', 'Property insurance renewal Q2', 'A6600-10', 'D-FIN', 'VALIDATED', '2025-03-15 14:30:00', 'ORG-101', 'MANUAL'),
('ORA-009', 'ORA-INV-50009', 'S-2003', 'Summit Energy Corp', '2025-04-01', '2025-05-01', 71200.00, 'USD', 'N30', 'OP-7100009', 'Natural gas supply Apr', 'A6400-10', 'D-FAC', 'VALIDATED', '2025-04-01 06:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-010', 'ORA-INV-50010', 'S-2007', 'Consolidated Packaging', '2025-04-08', '2025-05-08', 11800.00, 'USD', 'N30', 'OP-7100010', 'Shipping materials April', 'A5500-10', 'D-LOG', 'VALIDATED', '2025-04-08 08:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-011', 'ORA-INV-50011', 'S-2004', 'Yorkshire Chemical Ltd', '2025-04-22', '2025-06-21', 9500.00, 'GBP', 'N60', 'OP-7100011', 'Adhesives and coatings batch', 'A5400-10', 'D-OPS', 'APPROVED', '2025-04-22 09:00:00', 'ORG-103', 'AP_IMPORT'),
('ORA-012', 'ORA-INV-50012', 'S-2005', 'Apex Staffing Solutions', '2025-05-01', '2025-05-31', 48000.00, 'USD', 'N30', 'OP-7100012', 'Contract labor May - assembly', 'A6500-10', 'D-HR', 'VALIDATED', '2025-05-01 07:00:00', 'ORG-101', 'AP_IMPORT'),
('ORA-013', 'ORA-INV-50013', 'S-2008', 'Precision Instruments AG', '2025-05-10', '2025-07-09', 16700.00, 'EUR', 'N60', 'OP-7100013', 'Quality testing equipment', 'A5200-20', 'D-QA', 'PENDING', '2025-05-10 11:30:00', 'ORG-102', 'AP_IMPORT'),
('ORA-014', 'ORA-INV-50014', 'S-2006', 'National Insurance Brokers', '2025-05-20', '2025-06-19', 8500.00, 'USD', 'N30', 'OP-7100014', 'Workers comp adjustment', 'A6600-10', 'D-FIN', 'VALIDATED', '2025-05-20 15:00:00', 'ORG-101', 'MANUAL'),
('ORA-015', 'ORA-INV-50015', 'S-2003', 'Summit Energy Corp', '2025-06-01', '2025-07-01', 58900.00, 'USD', 'N30', 'OP-7100015', 'Natural gas supply Jun', 'A6400-10', 'D-FAC', 'VALIDATED', '2025-06-01 06:00:00', 'ORG-101', 'AP_IMPORT');


-- ============================================================================
-- Vignette 2: Additional bronze source tables (Baan + Workday)
-- See: vignettes/02_pipeline_maintainer/setup/02_precreate_new_sources.sql
-- ============================================================================

-- BRONZE_BAAN_AP_INVOICES
CREATE OR REPLACE TABLE BRONZE_BAAN_AP_INVOICES (
    BAN_INVOICE_ID      VARCHAR(20),
    BAN_INVOICE_REF     VARCHAR(30),
    BAN_VENDOR_CODE     VARCHAR(15),
    BAN_VENDOR_DESC     VARCHAR(100),
    BAN_INV_DATE        DATE,
    BAN_PAY_DATE        DATE,
    BAN_AMOUNT          NUMBER(18,2),
    BAN_CURR            VARCHAR(3),
    BAN_PAY_TERMS       VARCHAR(20),
    BAN_PO_REF          VARCHAR(20),
    BAN_LINE_DESC       VARCHAR(200),
    BAN_GL_CODE         VARCHAR(20),
    BAN_COST_CTR        VARCHAR(20),
    BAN_STATUS          VARCHAR(20),
    BAN_CREATED         TIMESTAMP_NTZ,
    BAN_COMPANY         VARCHAR(10)
);

INSERT INTO BRONZE_BAAN_AP_INVOICES VALUES
('BAN-001', 'BN-2025-1001', 'BV-301', 'Nordic Metals AB', '2025-02-01', '2025-03-03', 27500.00, 'EUR', 'N30', 'BP-8001', 'Aluminum extrusions Feb shipment', 'GL-510', 'BC-MFG', 'POSTED', '2025-02-01 06:00:00', 'BN-100'),
('BAN-002', 'BN-2025-1002', 'BV-302', 'Rotterdam Port Services', '2025-02-15', '2025-03-17', 14200.00, 'EUR', 'N30', 'BP-8002', 'Port handling and customs Feb', 'GL-610', 'BC-LOG', 'POSTED', '2025-02-15 08:30:00', 'BN-100'),
('BAN-003', 'BN-2025-1003', 'BV-303', 'Manchester Engineering Ltd', '2025-03-01', '2025-04-30', 38900.00, 'GBP', 'N60', 'BP-8003', 'Custom fabrication project Alpha', 'GL-520', 'BC-ENG', 'POSTED', '2025-03-01 09:00:00', 'BN-200'),
('BAN-004', 'BN-2025-1004', 'BV-301', 'Nordic Metals AB', '2025-03-10', '2025-04-09', 31200.00, 'EUR', 'N30', 'BP-8004', 'Steel plate order March', 'GL-510', 'BC-MFG', 'APPROVED', '2025-03-10 07:15:00', 'BN-100'),
('BAN-005', 'BN-2025-1005', 'BV-304', 'Belgian Chemicals NV', '2025-03-20', '2025-05-19', 9600.00, 'EUR', 'N60', 'BP-8005', 'Industrial lubricants Q1', 'GL-540', 'BC-OPS', 'POSTED', '2025-03-20 10:00:00', 'BN-100'),
('BAN-006', 'BN-2025-1006', 'BV-305', 'Zurich Consulting AG', '2025-04-01', '2025-05-01', 55000.00, 'EUR', 'N30', 'BP-8006', 'ERP optimization consulting Apr', 'GL-620', 'BC-IT', 'POSTED', '2025-04-01 08:00:00', 'BN-100'),
('BAN-007', 'BN-2025-1007', 'BV-302', 'Rotterdam Port Services', '2025-04-15', '2025-05-15', 16800.00, 'EUR', 'N30', 'BP-8007', 'Port handling and customs Apr', 'GL-610', 'BC-LOG', 'PENDING', '2025-04-15 08:30:00', 'BN-100'),
('BAN-008', 'BN-2025-1008', 'BV-303', 'Manchester Engineering Ltd', '2025-05-01', '2025-06-30', 22100.00, 'GBP', 'N60', 'BP-8008', 'Fabrication project Alpha phase 2', 'GL-520', 'BC-ENG', 'POSTED', '2025-05-01 09:00:00', 'BN-200'),
('BAN-009', 'BN-2025-1009', 'BV-306', 'Amsterdam IT Services BV', '2025-05-10', '2025-06-09', 12500.00, 'EUR', 'N30', 'BP-8009', 'Network infrastructure upgrade', 'GL-620', 'BC-IT', 'POSTED', '2025-05-10 11:00:00', 'BN-100'),
('BAN-010', 'BN-2025-1010', 'BV-301', 'Nordic Metals AB', '2025-06-01', '2025-07-01', 29800.00, 'EUR', 'N30', 'BP-8010', 'Aluminum extrusions Jun shipment', 'GL-510', 'BC-MFG', 'APPROVED', '2025-06-01 06:00:00', 'BN-100');


-- BRONZE_WORKDAY_AP_INVOICES
CREATE OR REPLACE TABLE BRONZE_WORKDAY_AP_INVOICES (
    WD_INVOICE_ID       VARCHAR(20),
    WD_INVOICE_NUM      VARCHAR(30),
    WD_SUPPLIER_ID      VARCHAR(15),
    WD_SUPPLIER_NAME    VARCHAR(100),
    WD_INVOICE_DATE     DATE,
    WD_DUE_DATE         DATE,
    WD_AMOUNT           NUMBER(18,2),
    WD_CURRENCY         VARCHAR(3),
    WD_PAY_TERMS        VARCHAR(20),
    WD_PO_NUMBER        VARCHAR(20),
    WD_MEMO             VARCHAR(200),
    WD_LEDGER_ACCOUNT   VARCHAR(20),
    WD_COST_CENTER      VARCHAR(20),
    WD_APPROVAL_STATUS  VARCHAR(20),
    WD_CREATED_DATE     TIMESTAMP_NTZ,
    WD_TENANT_ID        VARCHAR(10)
);

INSERT INTO BRONZE_WORKDAY_AP_INVOICES VALUES
('WD-001', 'WD-AP-90001', 'WS-401', 'CloudScale Analytics', '2025-01-20', '2025-02-19', 22000.00, 'USD', 'Net 30', 'WPO-6001', 'Data platform subscription Jan', 'LA-6200', 'WCC-TECH', 'Approved', '2025-01-20 10:00:00', 'WD-T1'),
('WD-002', 'WD-AP-90002', 'WS-402', 'Premier Office Solutions', '2025-02-01', '2025-03-03', 5600.00, 'USD', 'Net 30', 'WPO-6002', 'Office supplies and furniture Q1', 'LA-6800', 'WCC-ADMIN', 'Approved', '2025-02-01 09:00:00', 'WD-T1'),
('WD-003', 'WD-AP-90003', 'WS-403', 'Talent Bridge HR', '2025-02-10', '2025-03-12', 35000.00, 'USD', 'Net 30', 'WPO-6003', 'Executive recruiting services Feb', 'LA-6500', 'WCC-HR', 'Approved', '2025-02-10 14:00:00', 'WD-T1'),
('WD-004', 'WD-AP-90004', 'WS-404', 'London Legal Partners LLP', '2025-02-20', '2025-04-21', 18500.00, 'GBP', 'Net 60', 'WPO-6004', 'Legal advisory services Q1', 'LA-6700', 'WCC-LEGAL', 'In Review', '2025-02-20 11:30:00', 'WD-T2'),
('WD-005', 'WD-AP-90005', 'WS-401', 'CloudScale Analytics', '2025-03-01', '2025-03-31', 22000.00, 'USD', 'Net 30', 'WPO-6005', 'Data platform subscription Mar', 'LA-6200', 'WCC-TECH', 'Approved', '2025-03-01 10:00:00', 'WD-T1'),
('WD-006', 'WD-AP-90006', 'WS-405', 'Frankfurt Marketing Agentur', '2025-03-15', '2025-05-14', 42000.00, 'EUR', 'Net 60', 'WPO-6006', 'Brand campaign spring launch', 'LA-6900', 'WCC-MKT', 'Approved', '2025-03-15 08:00:00', 'WD-T2'),
('WD-007', 'WD-AP-90007', 'WS-402', 'Premier Office Solutions', '2025-04-01', '2025-05-01', 3200.00, 'USD', 'Net 30', 'WPO-6007', 'Office supplies April', 'LA-6800', 'WCC-ADMIN', 'Approved', '2025-04-01 09:00:00', 'WD-T1'),
('WD-008', 'WD-AP-90008', 'WS-406', 'CyberShield Security Inc', '2025-04-10', '2025-05-10', 67000.00, 'USD', 'Net 30', 'WPO-6008', 'Annual security audit + pen test', 'LA-6200', 'WCC-TECH', 'Approved', '2025-04-10 13:00:00', 'WD-T1'),
('WD-009', 'WD-AP-90009', 'WS-403', 'Talent Bridge HR', '2025-05-01', '2025-05-31', 28000.00, 'USD', 'Net 30', 'WPO-6009', 'Recruiting services May', 'LA-6500', 'WCC-HR', 'In Review', '2025-05-01 14:00:00', 'WD-T1'),
('WD-010', 'WD-AP-90010', 'WS-401', 'CloudScale Analytics', '2025-05-15', '2025-06-14', 22000.00, 'USD', 'Net 30', 'WPO-6010', 'Data platform subscription May', 'LA-6200', 'WCC-TECH', 'Approved', '2025-05-15 10:00:00', 'WD-T1');


-- ============================================================================
-- Vignette 3 (Optional): Agent evaluation dataset (tables)
-- Ensures agent exercises have a repeatable “golden question set” available.
-- Source-of-truth questions live in: setup/question_set.yaml
-- ============================================================================

-- Evaluation question set
CREATE OR REPLACE TABLE AGENT_EVAL_SET (
    QUESTION         VARCHAR(500),
    EXPECTED_ANSWER  VARCHAR(2000),
    EXPECTED_SQL     VARCHAR(10000),
    EXPECTED_METRIC  VARCHAR(200),
    EXPECTED_GRAIN   VARCHAR(100),
    NOTES            VARCHAR(500)
);

-- NOTE: Demo-simple mode intentionally does NOT create "eval harness" run/result tables.
-- We keep only a question set table (AGENT_EVAL_SET) plus a tiny 5-question smoke-test set (DEMO_EVAL_SET) below.

-- Insert the golden eval questions (15 total)
-- Mirrors: setup/question_set.yaml
INSERT INTO AGENT_EVAL_SET (QUESTION, EXPECTED_ANSWER, EXPECTED_SQL, EXPECTED_METRIC, EXPECTED_GRAIN, NOTES) VALUES

-- Core
(
  'What is the total spend by vendor?',
  'A breakdown of total invoice amounts grouped by vendor name, ranked by total spend.',
  'SELECT VENDOR_NAME, SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES GROUP BY VENDOR_NAME ORDER BY TOTAL_SPEND DESC;',
  'SUM(INVOICE_AMOUNT)',
  'VENDOR_NAME',
  'Core'
),
(
  'How many invoices per month?',
  'Monthly invoice counts showing a trend over time (DATE_TRUNC(''MONTH'', INVOICE_DATE)).',
  'SELECT DATE_TRUNC(''MONTH'', INVOICE_DATE) AS INVOICE_MONTH, COUNT(*) AS INVOICE_COUNT FROM SILVER_AP_INVOICES GROUP BY INVOICE_MONTH ORDER BY INVOICE_MONTH;',
  'COUNT(*)',
  'MONTH(INVOICE_DATE)',
  'Core'
),
(
  'Which source system has the most invoices?',
  'Invoice counts by SOURCE_SYSTEM, ordered by count descending.',
  'SELECT SOURCE_SYSTEM, COUNT(*) AS INVOICE_COUNT FROM SILVER_AP_INVOICES GROUP BY SOURCE_SYSTEM ORDER BY INVOICE_COUNT DESC;',
  'COUNT(*)',
  'SOURCE_SYSTEM',
  'Core'
),
(
  'What is the average invoice amount by currency?',
  'Average invoice amount grouped by CURRENCY_CODE (USD, EUR, GBP, ...).',
  'SELECT CURRENCY_CODE, AVG(INVOICE_AMOUNT) AS AVG_INVOICE_AMOUNT FROM SILVER_AP_INVOICES GROUP BY CURRENCY_CODE ORDER BY CURRENCY_CODE;',
  'AVG(INVOICE_AMOUNT)',
  'CURRENCY_CODE',
  'Core'
),
(
  'Top 5 vendors by total spend',
  'The 5 vendors with the highest total spend, ordered descending.',
  'SELECT VENDOR_NAME, SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES GROUP BY VENDOR_NAME ORDER BY TOTAL_SPEND DESC LIMIT 5;',
  'SUM(INVOICE_AMOUNT) + LIMIT 5',
  'VENDOR_NAME',
  'Core'
),
(
  'Invoice count by approval status',
  'Counts of invoices grouped by APPROVAL_STATUS.',
  'SELECT APPROVAL_STATUS, COUNT(*) AS INVOICE_COUNT FROM SILVER_AP_INVOICES GROUP BY APPROVAL_STATUS ORDER BY INVOICE_COUNT DESC, APPROVAL_STATUS;',
  'COUNT(*)',
  'APPROVAL_STATUS',
  'Core'
),

-- Variations
(
  'Show me vendor spending',
  'Same as total spend by vendor (variation of total spend by vendor).',
  'SELECT VENDOR_NAME, SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES GROUP BY VENDOR_NAME ORDER BY TOTAL_SPEND DESC;',
  'SUM(INVOICE_AMOUNT)',
  'VENDOR_NAME',
  'Variation'
),
(
  'How much did we spend with Acme Industrial Supply?',
  'Total spend filtered to vendor \"Acme Industrial Supply\".',
  'SELECT SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES WHERE VENDOR_NAME = ''Acme Industrial Supply'';',
  'SUM(INVOICE_AMOUNT) WHERE VENDOR_NAME = ''Acme Industrial Supply''',
  'Single vendor filter',
  'Variation'
),
(
  'Give me the invoice breakdown by system',
  'Invoice counts grouped by SOURCE_SYSTEM (a valid breakdown by system).',
  'SELECT SOURCE_SYSTEM, COUNT(*) AS INVOICE_COUNT FROM SILVER_AP_INVOICES GROUP BY SOURCE_SYSTEM ORDER BY INVOICE_COUNT DESC;',
  'COUNT(*)',
  'SOURCE_SYSTEM',
  'Variation'
),
(
  'What''s our monthly spend trend for 2025?',
  'Monthly total spend for invoices in calendar year 2025.',
  'SELECT DATE_TRUNC(''MONTH'', INVOICE_DATE) AS INVOICE_MONTH, SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES WHERE INVOICE_DATE >= ''2025-01-01''::DATE AND INVOICE_DATE < ''2026-01-01''::DATE GROUP BY INVOICE_MONTH ORDER BY INVOICE_MONTH;',
  'SUM(INVOICE_AMOUNT)',
  'MONTH, filtered to 2025',
  'Variation'
),

-- Edge cases
(
  'Show me overdue invoices',
  'Invoices with DUE_DATE before today. (Sample data does not include a paid/unpaid flag.)',
  'SELECT * FROM SILVER_AP_INVOICES WHERE DUE_DATE < CURRENT_DATE() ORDER BY DUE_DATE, INVOICE_DATE;',
  'Filter: DUE_DATE < CURRENT_DATE()',
  'Individual invoices',
  'Edge case'
),
(
  'What invoices are over $100,000?',
  'List of invoices where INVOICE_AMOUNT > 100000, ordered by amount descending.',
  'SELECT * FROM SILVER_AP_INVOICES WHERE INVOICE_AMOUNT > 100000 ORDER BY INVOICE_AMOUNT DESC;',
  'Filter: INVOICE_AMOUNT > 100000',
  'Individual invoices',
  'Edge case'
),

-- Ambiguous
(
  'Show me recent invoices',
  'Should ask a clarifying question (what time window counts as \"recent\"?) or apply a documented default.',
  'WITH mx AS (SELECT MAX(INVOICE_DATE) AS MAX_INVOICE_DATE FROM SILVER_AP_INVOICES) SELECT s.* FROM SILVER_AP_INVOICES s JOIN mx ON s.INVOICE_DATE >= DATEADD(''DAY'', -30, mx.MAX_INVOICE_DATE) ORDER BY s.INVOICE_DATE DESC;',
  'ORDER BY INVOICE_DATE DESC',
  'Individual invoices, recent',
  'Ambiguous (data-relative window)'
),
(
  'Which vendors are problematic?',
  'Should ask for clarification: problematic could mean overdue, high rejection rate, disputes, or unusually high spend.',
  NULL,
  'Needs clarification',
  'Vendor-level',
  'Ambiguous (clarification required)'
),

-- Data validation
(
  'What is the total spend across all invoices?',
  'Single grand total: SUM(INVOICE_AMOUNT) across all rows.',
  'SELECT SUM(INVOICE_AMOUNT) AS TOTAL_SPEND FROM SILVER_AP_INVOICES;',
  'SUM(INVOICE_AMOUNT)',
  'Grand total',
  'Data validation'
);

-- ============================================================================
-- Verify all tables loaded
-- ============================================================================

SELECT 'BRONZE_SAP_AP_INVOICES' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM BRONZE_SAP_AP_INVOICES
UNION ALL
SELECT 'BRONZE_ORACLE_AP_INVOICES', COUNT(*) FROM BRONZE_ORACLE_AP_INVOICES
UNION ALL
SELECT 'BRONZE_BAAN_AP_INVOICES', COUNT(*) FROM BRONZE_BAAN_AP_INVOICES
UNION ALL
SELECT 'BRONZE_WORKDAY_AP_INVOICES', COUNT(*) FROM BRONZE_WORKDAY_AP_INVOICES
UNION ALL
SELECT 'AGENT_EVAL_SET', COUNT(*) FROM AGENT_EVAL_SET
-- UNION ALL
-- SELECT 'DEMO_EVAL_SET', COUNT(*) FROM DEMO_EVAL_SET;
;
