/*=============================================================
  02 — Create Tables
  8 tables (5 structured, 1 semi-structured, 2 unstructured)
  + 1 internal stage
  NOTE: Logistics & Sales domain tables (SHIPMENTS,
        STORE_SALES, SHIPMENT_UPDATES, DELIVERY_TRACKING_EVENTS)
        and LOGISTICS_INCIDENT_REPORTS are excluded — supplementary
        data (freight costs, customer returns) lives in Amazon S3.
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- ============================================================
-- STRUCTURED TABLES (5) — Supply & Inventory Domain
-- ============================================================

-- 1. SUPPLIERS — supplier master data
CREATE OR REPLACE TABLE SUPPLIERS (
    SUPPLIER_ID    INT PRIMARY KEY,
    SUPPLIER_NAME  VARCHAR(100),
    CONTACT_NAME   VARCHAR(100),
    REGION         VARCHAR(50),
    COUNTRY        VARCHAR(50),
    LEAD_TIME_DAYS INT,
    RELIABILITY_SCORE FLOAT,
    CONTRACT_START DATE,
    CONTRACT_END   DATE,
    PAYMENT_TERMS  VARCHAR(30)
);

-- 2. PRODUCTS — product catalog
CREATE OR REPLACE TABLE PRODUCTS (
    PRODUCT_ID    INT PRIMARY KEY,
    PRODUCT_NAME  VARCHAR(150),
    CATEGORY      VARCHAR(50),
    SUBCATEGORY   VARCHAR(50),
    UNIT_COST     FLOAT,
    UNIT_PRICE    FLOAT,
    REORDER_POINT INT,
    REORDER_QTY   INT,
    SUPPLIER_ID   INT REFERENCES SUPPLIERS(SUPPLIER_ID),
    WEIGHT_KG     FLOAT,
    IS_PERISHABLE BOOLEAN
);

-- 3. WAREHOUSES — warehouse master data
CREATE OR REPLACE TABLE WAREHOUSES (
    WAREHOUSE_ID   INT PRIMARY KEY,
    WAREHOUSE_NAME VARCHAR(100),
    CITY           VARCHAR(50),
    STATE_PROVINCE VARCHAR(50),
    COUNTRY        VARCHAR(50),
    CAPACITY_SQFT  INT,
    WAREHOUSE_TYPE VARCHAR(30)
);

-- 4. INVENTORY — current inventory levels
CREATE OR REPLACE TABLE INVENTORY (
    INVENTORY_ID       INT AUTOINCREMENT PRIMARY KEY,
    PRODUCT_ID         INT REFERENCES PRODUCTS(PRODUCT_ID),
    WAREHOUSE_ID       INT REFERENCES WAREHOUSES(WAREHOUSE_ID),
    QUANTITY_ON_HAND   INT,
    QUANTITY_RESERVED  INT,
    QUANTITY_AVAILABLE INT,
    LAST_RESTOCK_DATE  DATE,
    DAYS_OF_SUPPLY     INT
);

-- 5. PURCHASE_ORDERS — procurement orders
CREATE OR REPLACE TABLE PURCHASE_ORDERS (
    PO_ID                  INT PRIMARY KEY,
    SUPPLIER_ID            INT REFERENCES SUPPLIERS(SUPPLIER_ID),
    PRODUCT_ID             INT REFERENCES PRODUCTS(PRODUCT_ID),
    ORDER_DATE             DATE,
    EXPECTED_DELIVERY_DATE DATE,
    ACTUAL_DELIVERY_DATE   DATE,
    STATUS                 VARCHAR(30),
    QUANTITY_ORDERED       INT,
    UNIT_COST              FLOAT,
    TOTAL_COST             FLOAT,
    DELAY_DAYS             INT DEFAULT 0
);

-- ============================================================
-- SEMI-STRUCTURED TABLE (1) — VARIANT column for JSON
-- ============================================================

-- 6. IOT_SENSOR_LOGS — warehouse sensor readings as JSON
CREATE OR REPLACE TABLE IOT_SENSOR_LOGS (
    LOG_ID          INT AUTOINCREMENT PRIMARY KEY,
    WAREHOUSE_ID    INT,
    LOG_TIMESTAMP   TIMESTAMP,
    SENSOR_PAYLOAD  VARIANT
);

-- ============================================================
-- UNSTRUCTURED TEXT TABLES (2)
-- NOTE: LOGISTICS_INCIDENT_REPORTS excluded — data lives in Amazon S3
-- ============================================================

-- 7. SUPPLIER_EMAILS — supplier communications
CREATE OR REPLACE TABLE SUPPLIER_EMAILS (
    EMAIL_ID      INT AUTOINCREMENT PRIMARY KEY,
    SUPPLIER_ID   INT REFERENCES SUPPLIERS(SUPPLIER_ID),
    SUPPLIER_NAME VARCHAR(100),
    SENDER        VARCHAR(150),
    SUBJECT       VARCHAR(200),
    EMAIL_BODY    VARCHAR(5000),
    DATE_SENT     DATE,
    PRIORITY      VARCHAR(20)
);

-- 8. WAREHOUSE_INSPECTION_NOTES — facility inspections
CREATE OR REPLACE TABLE WAREHOUSE_INSPECTION_NOTES (
    INSPECTION_ID      INT AUTOINCREMENT PRIMARY KEY,
    WAREHOUSE_ID       INT REFERENCES WAREHOUSES(WAREHOUSE_ID),
    WAREHOUSE_NAME     VARCHAR(100),
    INSPECTION_DATE    DATE,
    INSPECTOR          VARCHAR(100),
    OVERALL_RATING     VARCHAR(20),
    FOLLOW_UP_REQUIRED BOOLEAN,
    INSPECTION_NOTES   VARCHAR(5000)
);

-- ============================================================
-- STAGE — for semantic model YAML (if needed)
-- ============================================================

CREATE OR REPLACE STAGE SEMANTIC_MODELS
  DIRECTORY = (ENABLE = TRUE);
