bash <<'BON_BOOTSTRAP'
set -euo pipefail
set -C

parent='business-ontology'
target='business-ontology/getting-started'
if [[ -L "$parent" || ( -e "$parent" && ! -d "$parent" ) ]]; then
  printf '%s\n' 'Refusing setup: business-ontology must be a real directory, not a file or symlink.' >&2
  exit 1
fi
if [[ ! -d "$parent" ]]; then
  mkdir -- "$parent"
fi
cd -- "$parent"
if ! mkdir -- getting-started; then
  printf '%s\n' 'Refusing setup: business-ontology/getting-started already exists (including a symlink), or cannot be created. Nothing was overwritten.' >&2
  exit 1
fi
trap 'status=$?; if [[ "$status" -ne 0 ]]; then printf "%s\n" "Setup stopped. Files already written in $target are left intact for inspection and manual recovery; nothing is removed. Re-running refuses this existing target." >&2; fi; exit "$status"' EXIT
cd -- getting-started
mkdir -- sql benchmark

cat > 'sql/01_setup.sql' <<'BON_FILE_01_SETUP_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- Setup: Create database, schema, and warehouse
CREATE DATABASE IF NOT EXISTS BUSINESS_ONTOLOGY;
CREATE SCHEMA IF NOT EXISTS BUSINESS_ONTOLOGY.RAW;
CREATE WAREHOUSE IF NOT EXISTS BUSINESS_ONTOLOGY_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE;

USE DATABASE BUSINESS_ONTOLOGY;
USE SCHEMA RAW;
USE WAREHOUSE BUSINESS_ONTOLOGY_WH;
BON_FILE_01_SETUP_SQL

cat > 'sql/02_raw_data.sql' <<'BON_FILE_02_RAW_DATA_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================
-- RAW: Enterprise SAP-coded tables
-- Self-contained script: CREATE + INSERT for all tables
-- Realistic SAP column names (LIFNR, MAKTX, MATKL etc.)
-- This simulates what a real SAP extraction looks like.
-- =====================================================

USE DATABASE BUSINESS_ONTOLOGY;
USE SCHEMA RAW;
USE WAREHOUSE BUSINESS_ONTOLOGY_WH;

-- =============================================================================
-- MASTER DATA
-- =============================================================================

-- =====================================================
-- LFA1: Vendor Master
-- =====================================================
CREATE OR REPLACE TABLE LFA1 (
    LIFNR VARCHAR(10) NOT NULL PRIMARY KEY, -- Vendor number
    NAME1 VARCHAR(100),                     -- Vendor name
    ORT01 VARCHAR(50),                      -- City
    LAND1 VARCHAR(5),                       -- Country code
    STCD1 VARCHAR(30),                      -- Tax ID
    KRAUS VARCHAR(15),                      -- DUNS number (SAP uses KRAUS field)
    KTOKK VARCHAR(10),                      -- Account group (ZSTR=Strategic, ZSTD=Standard, ZPRB=Probationary)
    ZTERM VARCHAR(10)                       -- Payment terms
);

INSERT INTO LFA1 VALUES ('V10045', 'SHENZHEN ELECTRONICS CO. LTD', 'Shenzhen', 'CN', '91440300MA5FPQG72B', '54-138-7209', 'ZSTR', 'NET45');
INSERT INTO LFA1 VALUES ('V10078', 'PACIFIC METALS CORPORATION', 'Long Beach', 'US', '95-4821073', '07-823-6541', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10089', 'ADVANCED SILICON SOLUTIONS INC.', 'Santa Clara', 'US', '77-3920184', '15-738-2904', 'ZSTR', 'NET45');
INSERT INTO LFA1 VALUES ('V10098', 'TOKYO SENSOR TECHNOLOGIES K.K.', 'Tokyo', 'JP', 'JP5010401098234', '71-385-6249', 'ZSTD', 'NET45');
INSERT INTO LFA1 VALUES ('V10102', 'RHINE CHEMICAL GMBH', 'Ludwigshafen', 'DE', 'DE283741956', '31-592-4780', 'ZSTR', 'NET30');
INSERT INTO LFA1 VALUES ('V10134', 'BAYERN KUNSTSTOFFE AG', 'Munich', 'DE', 'DE192847563', '44-591-7823', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10156', 'OSAKA PRECISION INSTRUMENTS CO.', 'Osaka', 'JP', 'JP8120001098765', '69-247-1058', 'ZSTR', 'NET60');
INSERT INTO LFA1 VALUES ('V10167', 'GUANGZHOU RARE EARTH MATERIALS LTD', 'Guangzhou', 'CN', '91440101MA9URXG44N', '63-904-2175', 'ZSTD', 'NET60');
INSERT INTO LFA1 VALUES ('V10190', 'SCHWARZWALD PRECISION TOOLS GMBH', 'Freiburg', 'DE', 'DE314725890', '37-462-8105', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10201', 'MONTERREY PACKAGING S.A. DE C.V.', 'Monterrey', 'MX', 'MPS040512QR7', '82-461-3097', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10223', 'LONE STAR INDUSTRIAL SUPPLY CO.', 'Houston', 'US', '76-1948302', '28-617-4930', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10245', 'PUEBLA CORRUGATED PRODUCTS SA', 'Puebla', 'MX', 'PCP090318HV5', NULL, 'ZPRB', 'NET30');
INSERT INTO LFA1 VALUES ('V10278', 'JIANGSU COPPER ALLOYS CO. LTD', 'Nanjing', 'CN', '91320100MA1MPKG28R', '56-813-4027', 'ZSTD', 'NET45');
INSERT INTO LFA1 VALUES ('V10312', 'ACME LOGISTICS INC', 'Chicago', 'US', '36-4829107', '09-284-5716', 'ZSTD', 'NET30');
INSERT INTO LFA1 VALUES ('V10334', 'NAGOYA STEEL WORKS LTD', 'Nagoya', 'JP', 'JP3180001054321', '48-729-3061', 'ZSTD', 'NET60');

-- =====================================================
-- LFA2: Carriers (Forwarding Agents)
-- =====================================================
CREATE OR REPLACE TABLE LFA2 (
    TDLNR VARCHAR(10) NOT NULL PRIMARY KEY, -- Forwarding agent number
    NAME1 VARCHAR(100),                     -- Carrier name
    VSART VARCHAR(5),                       -- Transport type (01=Ocean, 02=FTL, 03=Air, 04=Intermodal, 05=LTL)
    LZEIT NUMBER(38,0),                     -- Transit time (days)
    OTRAT NUMBER(4,2)                       -- On-time rate (carrier self-reported)
);

INSERT INTO LFA2 VALUES ('CAR-001', 'TransGlobal Freight Inc.', '01', 28, 0.87);
INSERT INTO LFA2 VALUES ('CAR-002', 'EuroHaul Logistics GmbH', '02', 4, 0.94);
INSERT INTO LFA2 VALUES ('CAR-003', 'SkyBridge Air Cargo', '03', 3, 0.96);
INSERT INTO LFA2 VALUES ('CAR-004', 'Pacific Intermodal Corp.', '04', 18, 0.91);
INSERT INTO LFA2 VALUES ('CAR-005', 'MexLine Transportes S.A.', '05', 6, 0.83);
INSERT INTO LFA2 VALUES ('CAR-006', 'Shenzhen Coastal Shipping Ltd.', '01', 22, 0.89);

-- =====================================================
-- MARA: Material Master
-- =====================================================
CREATE OR REPLACE TABLE MARA (
    MATNR VARCHAR(10) NOT NULL PRIMARY KEY, -- Material number
    MAKTX VARCHAR(100),                     -- Material description
    MATKL VARCHAR(5),                       -- Material group code
    STPRS NUMBER(10,2)                      -- Standard price
);

INSERT INTO MARA VALUES ('ASSY-001', 'Sensor Module Assembly', '048', 45.00);
INSERT INTO MARA VALUES ('ASSY-002', 'Power Distribution Board', '048', 32.00);
INSERT INTO MARA VALUES ('ASSY-003', 'Ruggedized Enclosure', '048', 380.00);
INSERT INTO MARA VALUES ('ASSY-004', 'Integrated System Module', '048', 520.00);
INSERT INTO MARA VALUES ('MAT-001', 'Multilayer Ceramic Capacitor 100nF', '043', 0.12);
INSERT INTO MARA VALUES ('MAT-002', 'Epoxy Resin ER-4500', '044', 18.50);
INSERT INTO MARA VALUES ('MAT-003', 'Aluminum Sheet 6061-T6 2mm', '045', 42.00);
INSERT INTO MARA VALUES ('MAT-004', 'MEMS Accelerometer IC', '043', 3.75);
INSERT INTO MARA VALUES ('MAT-005', 'Corrugated Box 400x300x200mm', '046', 1.85);
INSERT INTO MARA VALUES ('MAT-006', 'Isopropyl Alcohol 99.7%', '044', 5.20);
INSERT INTO MARA VALUES ('MAT-007', 'Copper Alloy Strip C17200', '045', 28.90);
INSERT INTO MARA VALUES ('MAT-008', 'ARM Cortex-M4 Microcontroller', '043', 6.40);
INSERT INTO MARA VALUES ('MAT-009', 'Anti-Static Foam Insert', '046', 0.95);
INSERT INTO MARA VALUES ('MAT-010', 'Stainless Steel Rod 304L 10mm', '045', 12.30);
INSERT INTO MARA VALUES ('MAT-011', 'Neodymium Rare Earth Magnet N52', '047', 2.10);
INSERT INTO MARA VALUES ('MAT-012', 'Silicone Thermal Paste TG-7', '044', 85.00);
INSERT INTO MARA VALUES ('MAT-013', 'Power MOSFET IRF540N', '043', 0.85);
INSERT INTO MARA VALUES ('MAT-014', 'Polyethylene Stretch Wrap 500mm', '046', 14.50);
INSERT INTO MARA VALUES ('MAT-015', 'Titanium Alloy Ti-6Al-4V Plate', '045', 120.00);
INSERT INTO MARA VALUES ('MAT-016', 'Fiber Optic Transceiver SFP+ 10G', '043', 22.00);
INSERT INTO MARA VALUES ('MAT-017', 'Hydrochloric Acid 37% ACS Grade', '044', 8.75);
INSERT INTO MARA VALUES ('MAT-018', 'Precision Ball Bearing 6205-2RS', '047', 4.50);
INSERT INTO MARA VALUES ('MAT-019', 'Carbon Fiber Sheet 3K Twill 2mm', '047', 65.00);
INSERT INTO MARA VALUES ('MAT-020', 'ESD Protective Bag 200x300mm', '046', 0.35);

-- =====================================================
-- T001W: Plants
-- =====================================================
CREATE OR REPLACE TABLE T001W (
    WERKS VARCHAR(10) NOT NULL PRIMARY KEY, -- Plant code
    NAME1 VARCHAR(100),                     -- Plant name
    REGIO VARCHAR(20)                       -- Region
);

INSERT INTO T001W VALUES ('PLT-001', 'Austin Manufacturing Center', 'AMERICAS');
INSERT INTO T001W VALUES ('PLT-002', 'Stuttgart Assembly Plant', 'EMEA');
INSERT INTO T001W VALUES ('PLT-003', 'Shanghai Production Facility', 'APAC');
INSERT INTO T001W VALUES ('PLT-004', 'Monterrey Operations Plant', 'AMERICAS');
INSERT INTO T001W VALUES ('PLT-005', 'Nagoya Precision Works', 'APAC');

-- =====================================================
-- T320: Storage Locations (Warehouses)
-- =====================================================
CREATE OR REPLACE TABLE T320 (
    LGORT VARCHAR(10) NOT NULL PRIMARY KEY, -- Storage location
    LGOBE VARCHAR(100),                     -- Storage location description
    WERKS VARCHAR(10),                      -- Plant
    LKAPA NUMBER(5,1)                       -- Capacity utilization %
);

INSERT INTO T320 VALUES ('WH-001', 'Austin Raw Materials Hub', 'PLT-001', 72.5);
INSERT INTO T320 VALUES ('WH-002', 'Austin Finished Goods Depot', 'PLT-001', 61.0);
INSERT INTO T320 VALUES ('WH-003', 'Stuttgart Inbound Logistics Center', 'PLT-002', 88.3);
INSERT INTO T320 VALUES ('WH-004', 'Shanghai Bonded Warehouse', 'PLT-003', 55.2);
INSERT INTO T320 VALUES ('WH-005', 'Shanghai Distribution Center', 'PLT-003', 79.8);
INSERT INTO T320 VALUES ('WH-006', 'Monterrey Cross-Dock Facility', 'PLT-004', 42.1);
INSERT INTO T320 VALUES ('WH-007', 'Nagoya JIT Storage', 'PLT-005', 91.7);
INSERT INTO T320 VALUES ('WH-008', 'Houston Regional Distribution Hub', 'PLT-001', 67.4);

-- =============================================================================
-- TRANSACTIONS
-- =============================================================================

-- =====================================================
-- EKPO: Purchase Order Items
-- =====================================================
CREATE OR REPLACE TABLE EKPO (
    EBELN VARCHAR(20) NOT NULL,             -- PO number
    EBELP VARCHAR(5) NOT NULL,              -- PO item number
    LIFNR VARCHAR(10),                      -- Vendor number
    MATNR VARCHAR(10),                      -- Material number
    WERKS VARCHAR(10),                      -- Plant
    BEDAT DATE,                             -- Order date
    MENGE NUMBER(38,0),                     -- Quantity
    NETWR NUMBER(12,2),                     -- Net value (USD)
    STATU VARCHAR(5),                       -- Status (O=Open, C=Closed, R=Received)
    PRIMARY KEY (EBELN, EBELP)
);

INSERT INTO EKPO VALUES ('PO-2024-001', '10', 'V10045', 'MAT-001', 'PLT-003', '2024-09-15', 100000, 11000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-002', '10', 'V10078', 'MAT-002', 'PLT-002', '2024-09-20', 5000, 89000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-003', '10', 'V10089', 'MAT-003', 'PLT-001', '2024-10-01', 1200, 48600.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-004', '10', 'V10098', 'MAT-004', 'PLT-005', '2024-10-10', 20000, 72000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-005', '10', 'V10102', 'MAT-005', 'PLT-004', '2024-10-15', 15000, 26250.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-006', '10', 'V10134', 'MAT-008', 'PLT-001', '2024-11-01', 10000, 62000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-007', '10', 'V10156', 'MAT-002', 'PLT-002', '2024-11-10', 3000, 57300.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-008', '10', 'V10167', 'MAT-011', 'PLT-003', '2024-11-15', 50000, 97500.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-009', '10', 'V10278', 'MAT-007', 'PLT-003', '2024-12-01', 2000, 55000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-010', '10', 'V10334', 'MAT-010', 'PLT-005', '2024-12-05', 5000, 59000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-011', '10', 'V10102', 'MAT-014', 'PLT-004', '2024-11-20', 800, 11040.00, 'R');
INSERT INTO EKPO VALUES ('PO-2024-012', '10', 'V10201', 'MAT-004', 'PLT-001', '2024-12-10', 8000, 30400.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-001', '10', 'V10045', 'MAT-013', 'PLT-003', '2025-01-10', 50000, 41000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2025-002', '10', 'V10201', 'MAT-016', 'PLT-005', '2025-01-20', 4000, 84000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2025-003', '10', 'V10190', 'MAT-006', 'PLT-001', '2025-02-01', 10000, 49000.00, 'R');
INSERT INTO EKPO VALUES ('PO-2025-004', '10', 'V10312', 'MAT-018', 'PLT-002', '2025-02-15', 8000, 34400.00, 'R');
INSERT INTO EKPO VALUES ('PO-2025-005', '10', 'V10089', 'MAT-015', 'PLT-001', '2025-03-01', 300, 34500.00, 'R');
INSERT INTO EKPO VALUES ('PO-2025-006', '10', 'V10134', 'MAT-008', 'PLT-001', '2025-03-15', 15000, 93000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-007', '10', 'V10078', 'MAT-017', 'PLT-002', '2025-04-01', 8000, 67200.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-008', '10', 'V10223', 'MAT-005', 'PLT-004', '2025-04-05', 20000, 33000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-009', '10', 'V10098', 'MAT-004', 'PLT-005', '2025-04-10', 25000, 90000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-010', '10', 'V10167', 'MAT-011', 'PLT-003', '2025-04-12', 40000, 80000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-011', '10', 'V10045', 'MAT-001', 'PLT-001', '2025-04-15', 200000, 22000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-012', '10', 'V10278', 'MAT-007', 'PLT-003', '2025-04-16', 3000, 84000.00, 'O');
INSERT INTO EKPO VALUES ('PO-2025-013', '10', 'V10245', 'MAT-009', 'PLT-001', '2025-03-01', 25000, 22500.00, 'R');

-- =====================================================
-- LIKP: Shipments
-- =====================================================
CREATE OR REPLACE TABLE LIKP (
    TKNUM VARCHAR(10) NOT NULL PRIMARY KEY, -- Shipment number
    TDLNR VARCHAR(10),                      -- Forwarding agent (carrier)
    LGORT_SRC VARCHAR(10),                  -- Source storage location (origin warehouse)
    WERKS_DST VARCHAR(10),                  -- Destination plant
    MATNR VARCHAR(10),                      -- Material
    MENGE NUMBER(38,0),                     -- Quantity
    LFDAT DATE,                             -- Expected arrival
    WADAT DATE,                             -- Actual arrival
    FRTCO NUMBER(10,2),                     -- Freight cost
    STATU VARCHAR(5)                        -- Status (D=Delivered, T=In Transit, X=Delayed)
);

INSERT INTO LIKP VALUES ('SHP-001', 'CAR-006', 'WH-004', 'PLT-001', 'MAT-001', 100000, '2024-10-10', '2024-10-08', 2800.00, 'D');
INSERT INTO LIKP VALUES ('SHP-002', 'CAR-002', 'WH-003', 'PLT-002', 'MAT-002', 5000, '2024-09-26', '2024-09-25', 1200.00, 'D');
INSERT INTO LIKP VALUES ('SHP-003', 'CAR-003', 'WH-008', NULL, 'MAT-003', 1200, '2024-10-06', '2024-10-06', 3500.00, 'D');
INSERT INTO LIKP VALUES ('SHP-004', 'CAR-004', 'WH-007', 'PLT-005', 'MAT-004', 20000, '2024-11-02', '2024-11-05', 4200.00, 'D');
INSERT INTO LIKP VALUES ('SHP-005', 'CAR-005', 'WH-006', 'PLT-004', 'MAT-005', 15000, '2024-10-23', '2024-10-22', 850.00, 'D');
INSERT INTO LIKP VALUES ('SHP-006', 'CAR-003', 'WH-001', NULL, 'MAT-008', 10000, '2024-11-11', '2024-11-11', 5100.00, 'D');
INSERT INTO LIKP VALUES ('SHP-007', 'CAR-001', 'WH-004', NULL, 'MAT-011', 50000, '2024-12-18', '2024-12-22', 3100.00, 'D');
INSERT INTO LIKP VALUES ('SHP-008', 'CAR-006', 'WH-005', NULL, 'MAT-007', 2000, '2024-12-27', '2024-12-26', 1900.00, 'D');
INSERT INTO LIKP VALUES ('SHP-009', 'CAR-002', 'WH-003', 'PLT-002', 'MAT-018', 8000, '2025-02-22', '2025-02-21', 980.00, 'D');
INSERT INTO LIKP VALUES ('SHP-010', 'CAR-004', 'WH-007', NULL, 'MAT-016', 4000, '2025-02-12', '2025-02-14', 3800.00, 'D');
INSERT INTO LIKP VALUES ('SHP-011', 'CAR-001', 'WH-008', NULL, 'MAT-006', 10000, '2025-03-05', '2025-03-08', 2400.00, 'D');
INSERT INTO LIKP VALUES ('SHP-012', 'CAR-003', 'WH-001', 'PLT-001', 'MAT-015', 300, '2025-03-23', '2025-03-23', 1800.00, 'D');
INSERT INTO LIKP VALUES ('SHP-013', 'CAR-006', 'WH-004', 'PLT-003', 'MAT-013', 50000, '2025-02-06', '2025-02-04', 2200.00, 'D');
INSERT INTO LIKP VALUES ('SHP-014', 'CAR-005', 'WH-006', 'PLT-004', 'MAT-014', 800, '2024-11-28', '2024-11-30', 450.00, 'D');
INSERT INTO LIKP VALUES ('SHP-015', 'CAR-002', 'WH-003', 'PLT-002', 'MAT-002', 3000, '2025-03-29', '2025-03-28', 1100.00, 'D');
INSERT INTO LIKP VALUES ('SHP-016', 'CAR-001', 'WH-005', NULL, 'MAT-011', 40000, '2025-05-12', NULL, 3050.00, 'T');
INSERT INTO LIKP VALUES ('SHP-017', 'CAR-004', 'WH-007', 'PLT-005', 'MAT-004', 25000, '2025-05-03', NULL, 4500.00, 'T');
INSERT INTO LIKP VALUES ('SHP-018', 'CAR-003', 'WH-001', NULL, 'MAT-008', 8000, '2025-04-13', NULL, 4800.00, 'X');
INSERT INTO LIKP VALUES ('SHP-019', 'CAR-006', 'WH-004', NULL, 'MAT-007', 3000, '2025-05-10', NULL, 2600.00, 'T');
INSERT INTO LIKP VALUES ('SHP-020', 'CAR-005', 'WH-006', 'PLT-004', 'MAT-005', 20000, '2025-04-14', NULL, 920.00, 'X');

-- =====================================================
-- LFB1: Vendor Contracts
-- =====================================================
CREATE OR REPLACE TABLE LFB1 (
    LIFNR VARCHAR(10) NOT NULL,             -- Vendor
    VKONT VARCHAR(10) NOT NULL,             -- Contract number
    VTART VARCHAR(5),                       -- Contract type (M=Master, F=Framework, S=Spot)
    DTEND DATE,                             -- Expiration date
    JWERT NUMBER(12,2),                     -- Annual value
    PRIMARY KEY (LIFNR, VKONT)
);

INSERT INTO LFB1 VALUES ('V10045', 'CTR-001', 'M', '2026-12-31', 4500000.00);
INSERT INTO LFB1 VALUES ('V10078', 'CTR-002', 'M', '2026-06-30', 3200000.00);
INSERT INTO LFB1 VALUES ('V10089', 'CTR-003', 'F', '2026-03-31', 2800000.00);
INSERT INTO LFB1 VALUES ('V10098', 'CTR-004', 'M', '2027-12-31', 5200000.00);
INSERT INTO LFB1 VALUES ('V10102', 'CTR-005', 'F', '2025-05-31', 450000.00);
INSERT INTO LFB1 VALUES ('V10134', 'CTR-006', 'M', '2027-02-28', 7000000.00);
INSERT INTO LFB1 VALUES ('V10156', 'CTR-007', 'F', '2025-12-31', 1200000.00);
INSERT INTO LFB1 VALUES ('V10167', 'CTR-008', 'S', '2025-09-30', 980000.00);
INSERT INTO LFB1 VALUES ('V10190', 'CTR-015', 'F', '2025-07-31', 600000.00);
INSERT INTO LFB1 VALUES ('V10201', 'CTR-009', 'M', '2026-03-31', 3800000.00);
INSERT INTO LFB1 VALUES ('V10223', 'CTR-014', 'S', '2025-07-15', 250000.00);
INSERT INTO LFB1 VALUES ('V10245', 'CTR-010', 'F', '2025-12-31', 2000000.00);
INSERT INTO LFB1 VALUES ('V10278', 'CTR-011', 'M', '2026-05-31', 1500000.00);
INSERT INTO LFB1 VALUES ('V10312', 'CTR-012', 'F', '2025-12-31', 800000.00);
INSERT INTO LFB1 VALUES ('V10334', 'CTR-013', 'M', '2026-09-30', 3500000.00);

-- =====================================================
-- QALS: Inspection Lots
-- =====================================================
CREATE OR REPLACE TABLE QALS (
    PRUEFLOS VARCHAR(10) NOT NULL PRIMARY KEY, -- Inspection lot
    MATNR VARCHAR(10),                         -- Material
    QAESSION NUMBER(6,3),                      -- Defect rate
    VCODE VARCHAR(5)                           -- Disposition (A=Accepted, R=Rejected, C=Conditional)
);

INSERT INTO QALS VALUES ('INS-001', 'MAT-001', 0.006, 'A');
INSERT INTO QALS VALUES ('INS-002', 'MAT-002', 0.060, 'C');
INSERT INTO QALS VALUES ('INS-003', 'MAT-003', 0.001, 'A');
INSERT INTO QALS VALUES ('INS-004', 'MAT-004', 0.150, 'A');
INSERT INTO QALS VALUES ('INS-005', 'MAT-005', 0.011, 'A');
INSERT INTO QALS VALUES ('INS-006', 'MAT-006', 0.005, 'A');
INSERT INTO QALS VALUES ('INS-007', 'MAT-007', 0.050, 'C');
INSERT INTO QALS VALUES ('INS-008', 'MAT-008', 0.000, 'A');
INSERT INTO QALS VALUES ('INS-009', 'MAT-001', 0.010, 'A');
INSERT INTO QALS VALUES ('INS-010', 'MAT-003', 0.002, 'A');

-- =============================================================================
-- STRUCTURE
-- =============================================================================

-- =====================================================
-- STPO: BOM Items
-- =====================================================
CREATE OR REPLACE TABLE STPO (
    STLNR VARCHAR(10) NOT NULL,             -- BOM number
    IDNRK VARCHAR(10) NOT NULL,             -- Component material
    MENGE NUMBER(10,3),                     -- Quantity per unit
    STUFE NUMBER(38,0),                     -- BOM level
    PRIMARY KEY (STLNR, IDNRK)
);

INSERT INTO STPO VALUES ('ASSY-001', 'MAT-001', 10.000, 1);
INSERT INTO STPO VALUES ('ASSY-001', 'MAT-004', 2.000, 1);
INSERT INTO STPO VALUES ('ASSY-001', 'MAT-008', 1.000, 1);
INSERT INTO STPO VALUES ('ASSY-001', 'MAT-012', 0.050, 1);
INSERT INTO STPO VALUES ('ASSY-002', 'MAT-001', 20.000, 1);
INSERT INTO STPO VALUES ('ASSY-002', 'MAT-007', 0.500, 1);
INSERT INTO STPO VALUES ('ASSY-002', 'MAT-013', 4.000, 1);
INSERT INTO STPO VALUES ('ASSY-003', 'ASSY-001', 1.000, 1);
INSERT INTO STPO VALUES ('ASSY-003', 'ASSY-002', 1.000, 1);
INSERT INTO STPO VALUES ('ASSY-003', 'MAT-003', 2.000, 1);
INSERT INTO STPO VALUES ('ASSY-003', 'MAT-015', 0.300, 1);
INSERT INTO STPO VALUES ('ASSY-003', 'MAT-019', 1.000, 1);
INSERT INTO STPO VALUES ('ASSY-004', 'ASSY-003', 1.000, 1);
INSERT INTO STPO VALUES ('ASSY-004', 'MAT-016', 2.000, 1);
INSERT INTO STPO VALUES ('ASSY-004', 'MAT-018', 4.000, 1);

-- =====================================================
-- QUAL_MATRIX: Alternate Supplier Qualifications
-- (Quality engineering data)
-- =====================================================
CREATE OR REPLACE TABLE QUAL_MATRIX (
    MATNR VARCHAR(10) NOT NULL,             -- Material number
    LIFNR VARCHAR(10) NOT NULL,             -- Vendor number
    QUAL_STATUS VARCHAR(10),                -- APPROVED, PENDING, EXPIRED, REJECTED
    QUAL_DATE DATE,                         -- Qualification date
    PRIMARY KEY (MATNR, LIFNR)
);

INSERT INTO QUAL_MATRIX VALUES ('MAT-001', 'V10045', 'APPROVED', '2023-06-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-001', 'V10048', 'APPROVED', '2024-01-20');
INSERT INTO QUAL_MATRIX VALUES ('MAT-001', 'V10052', 'PENDING', '2025-03-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-002', 'V10054', 'APPROVED', '2023-07-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-002', 'V10056', 'APPROVED', '2024-03-10');
INSERT INTO QUAL_MATRIX VALUES ('MAT-003', 'V10053', 'APPROVED', '2023-04-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-003', 'V10060', 'APPROVED', '2024-11-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-004', 'V10055', 'APPROVED', '2023-09-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-004', 'V10057', 'APPROVED', '2024-07-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-005', 'V10057', 'APPROVED', '2024-08-20');
INSERT INTO QUAL_MATRIX VALUES ('MAT-005', 'V10059', 'APPROVED', '2023-11-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-006', 'V10049', 'APPROVED', '2023-06-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-007', 'V10051', 'APPROVED', '2023-05-20');
INSERT INTO QUAL_MATRIX VALUES ('MAT-008', 'V10045', 'EXPIRED', '2022-12-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-008', 'V10055', 'APPROVED', '2024-05-10');
INSERT INTO QUAL_MATRIX VALUES ('MAT-009', 'V10057', 'APPROVED', '2024-02-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-010', 'V10055', 'APPROVED', '2023-12-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-011', 'V10050', 'APPROVED', '2023-08-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-012', 'V10049', 'APPROVED', '2023-05-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-012', 'V10054', 'APPROVED', '2024-04-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-013', 'V10045', 'APPROVED', '2023-06-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-014', 'V10057', 'APPROVED', '2023-08-20');
INSERT INTO QUAL_MATRIX VALUES ('MAT-015', 'V10053', 'APPROVED', '2023-10-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-015', 'V10058', 'PENDING', '2025-06-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-016', 'V10057', 'APPROVED', '2024-01-10');
INSERT INTO QUAL_MATRIX VALUES ('MAT-017', 'V10049', 'APPROVED', '2023-09-01');
INSERT INTO QUAL_MATRIX VALUES ('MAT-018', 'V10055', 'APPROVED', '2023-07-15');
INSERT INTO QUAL_MATRIX VALUES ('MAT-019', 'V10049', 'APPROVED', '2023-06-01');

-- =============================================================================
-- FINANCE
-- =============================================================================

-- =====================================================
-- BSEG: Accounting Document Segment
-- =====================================================
CREATE OR REPLACE TABLE BSEG (
    BELNR VARCHAR(10) NOT NULL,             -- Accounting document number
    BUZEI VARCHAR(3) NOT NULL,              -- Line item number
    EBELN VARCHAR(20),                      -- Purchase order number
    LIFNR VARCHAR(10),                      -- Vendor number
    HKONT VARCHAR(15),                      -- G/L account number
    DMBTR NUMBER(12,2),                     -- Amount in local currency
    BUDAT DATE,                             -- Posting date
    BSCHL VARCHAR(3),                       -- Posting key (31=vendor invoice, 34=debit memo)
    GJAHR NUMBER(4,0),                      -- Fiscal year
    MONAT NUMBER(2,0),                      -- Fiscal period
    PRIMARY KEY (BELNR, BUZEI)
);

INSERT INTO BSEG VALUES ('5100000001', '001', 'PO-2024-001', 'V10045', '0040100000', 11000.00, '2024-10-15', '31', 2024, 10);
INSERT INTO BSEG VALUES ('5100000002', '001', 'PO-2024-002', 'V10078', '0040100000', 89000.00, '2024-10-20', '31', 2024, 10);
INSERT INTO BSEG VALUES ('5100000003', '001', 'PO-2024-003', 'V10089', '0040100000', 48600.00, '2024-11-01', '31', 2024, 11);
INSERT INTO BSEG VALUES ('5100000004', '001', 'PO-2024-004', 'V10098', '0040100000', 72000.00, '2024-11-10', '31', 2024, 11);
INSERT INTO BSEG VALUES ('5100000005', '001', 'PO-2024-005', 'V10102', '0040100000', 26250.00, '2024-11-15', '31', 2024, 11);
INSERT INTO BSEG VALUES ('5100000006', '001', 'PO-2024-006', 'V10134', '0040100000', 62000.00, '2024-12-01', '31', 2024, 12);
INSERT INTO BSEG VALUES ('5100000007', '001', 'PO-2024-007', 'V10156', '0040100000', 57300.00, '2024-12-10', '31', 2024, 12);
INSERT INTO BSEG VALUES ('5100000008', '001', 'PO-2024-008', 'V10167', '0040100000', 97500.00, '2024-12-15', '31', 2024, 12);
INSERT INTO BSEG VALUES ('5100000009', '001', 'PO-2024-009', 'V10278', '0040100000', 55000.00, '2025-01-01', '31', 2025, 1);
INSERT INTO BSEG VALUES ('5100000010', '001', 'PO-2024-010', 'V10334', '0040100000', 59000.00, '2025-01-05', '31', 2025, 1);
INSERT INTO BSEG VALUES ('5100000011', '001', 'PO-2024-011', 'V10102', '0040100000', 11040.00, '2024-12-20', '31', 2024, 12);
INSERT INTO BSEG VALUES ('5100000012', '001', 'PO-2024-012', 'V10201', '0040100000', 30400.00, '2025-01-10', '31', 2025, 1);
INSERT INTO BSEG VALUES ('5100000013', '001', 'PO-2025-001', 'V10045', '0040100000', 41000.00, '2025-02-10', '31', 2025, 2);
INSERT INTO BSEG VALUES ('5100000014', '001', 'PO-2025-002', 'V10201', '0040100000', 84000.00, '2025-02-20', '31', 2025, 2);
INSERT INTO BSEG VALUES ('5100000015', '001', 'PO-2025-003', 'V10190', '0040100000', 49000.00, '2025-03-01', '31', 2025, 3);
INSERT INTO BSEG VALUES ('5100000016', '001', 'PO-2025-004', 'V10312', '0040100000', 34400.00, '2025-03-15', '31', 2025, 3);
INSERT INTO BSEG VALUES ('5100000017', '001', 'PO-2025-005', 'V10089', '0040100000', 34500.00, '2025-04-01', '31', 2025, 4);
INSERT INTO BSEG VALUES ('5100000018', '001', 'PO-2025-006', 'V10134', '0040100000', 93000.00, '2025-04-15', '31', 2025, 4);
INSERT INTO BSEG VALUES ('5100000019', '001', 'PO-2025-007', 'V10078', '0040100000', 67200.00, '2025-05-01', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000020', '001', 'PO-2025-008', 'V10223', '0040100000', 33000.00, '2025-05-05', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000021', '001', 'PO-2025-009', 'V10098', '0040100000', 90000.00, '2025-05-10', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000022', '001', 'PO-2025-010', 'V10167', '0040100000', 80000.00, '2025-05-12', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000023', '001', 'PO-2025-011', 'V10045', '0040100000', 22000.00, '2025-05-15', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000024', '001', 'PO-2025-012', 'V10278', '0040100000', 84000.00, '2025-05-16', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000025', '001', 'PO-2025-013', 'V10245', '0040100000', 22500.00, '2025-04-01', '31', 2025, 4);
INSERT INTO BSEG VALUES ('5100000030', '001', 'PO-2024-003', 'V10089', '0040100000', 12150.00, '2024-12-01', '34', 2024, 12);
INSERT INTO BSEG VALUES ('5100000031', '001', 'PO-2024-008', 'V10167', '0040100000', 19500.00, '2025-01-15', '34', 2025, 1);
INSERT INTO BSEG VALUES ('5100000032', '001', 'PO-2025-003', 'V10190', '0040100000', 9800.00, '2025-04-01', '34', 2025, 4);
INSERT INTO BSEG VALUES ('5100000033', '001', 'PO-2025-007', 'V10078', '0040100000', 6720.00, '2025-06-01', '34', 2025, 6);
INSERT INTO BSEG VALUES ('5100000034', '001', 'PO-2024-006', 'V10134', '0040100000', 15500.00, '2025-02-01', '34', 2025, 2);
INSERT INTO BSEG VALUES ('5100000040', '001', 'PO-2024-001', 'V10045', '0040200000', 2200.00, '2024-10-20', '31', 2024, 10);
INSERT INTO BSEG VALUES ('5100000041', '001', 'PO-2024-004', 'V10098', '0040200000', 8500.00, '2024-11-15', '31', 2024, 11);
INSERT INTO BSEG VALUES ('5100000042', '001', 'PO-2025-002', 'V10201', '0040200000', 12600.00, '2025-03-01', '31', 2025, 3);
INSERT INTO BSEG VALUES ('5100000043', '001', 'PO-2025-009', 'V10098', '0040200000', 11000.00, '2025-05-15', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000044', '001', 'PO-2025-006', 'V10134', '0040200000', 5500.00, '2025-04-20', '31', 2025, 4);
INSERT INTO BSEG VALUES ('5100000050', '001', 'PO-2024-001', 'V10045', '0021100000', 13200.00, '2024-10-15', '31', 2024, 10);
INSERT INTO BSEG VALUES ('5100000051', '001', 'PO-2025-009', 'V10098', '0021100000', 101000.00, '2025-05-10', '31', 2025, 5);
INSERT INTO BSEG VALUES ('5100000052', '001', 'PO-2025-006', 'V10134', '0021100000', 98500.00, '2025-04-15', '31', 2025, 4);

-- =====================================================
-- COEP: CO Line Items (Cost Element Postings)
-- =====================================================
CREATE OR REPLACE TABLE COEP (
    OBJNR VARCHAR(20),                      -- Cost center / object number
    KSTAR VARCHAR(15),                      -- Cost element
    WRTBTR NUMBER(12,2),                    -- Amount in controlling area currency
    GJAHR NUMBER(4,0),                      -- Fiscal year
    PERIO NUMBER(2,0),                      -- Posting period
    MATNR VARCHAR(10)                       -- Material number
);

INSERT INTO COEP VALUES ('KS-LOG', '0047000000', 39800.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-LOG', '0047000000', 42100.00, 2025, 2, NULL);
INSERT INTO COEP VALUES ('KS-MFG-AP', '0040100000', 177500.00, 2025, 1, 'MAT-011');
INSERT INTO COEP VALUES ('KS-MFG-AP', '0040100000', 139000.00, 2025, 2, 'MAT-007');
INSERT INTO COEP VALUES ('KS-MFG-AP', '0040100000', 74000.00, 2025, 3, 'MAT-001');
INSERT INTO COEP VALUES ('KS-MFG-AP', '0047000000', 31200.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-MFG-AP', '0048000000', 14800.00, 2025, 2, NULL);
INSERT INTO COEP VALUES ('KS-MFG-EU', '0040100000', 213500.00, 2025, 1, 'MAT-002');
INSERT INTO COEP VALUES ('KS-MFG-EU', '0040100000', 67200.00, 2025, 2, 'MAT-017');
INSERT INTO COEP VALUES ('KS-MFG-EU', '0040100000', 34400.00, 2025, 3, 'MAT-018');
INSERT INTO COEP VALUES ('KS-MFG-EU', '0047000000', 22300.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-MFG-EU', '0048000000', 11500.00, 2025, 2, NULL);
INSERT INTO COEP VALUES ('KS-MFG-US', '0040100000', 172550.00, 2025, 1, 'MAT-003');
INSERT INTO COEP VALUES ('KS-MFG-US', '0040100000', 127500.00, 2025, 2, 'MAT-004');
INSERT INTO COEP VALUES ('KS-MFG-US', '0040100000', 93000.00, 2025, 3, 'MAT-008');
INSERT INTO COEP VALUES ('KS-MFG-US', '0047000000', 18500.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-MFG-US', '0048000000', 8200.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-QA', '0048000000', 22000.00, 2025, 1, NULL);
INSERT INTO COEP VALUES ('KS-QA', '0048000000', 18500.00, 2025, 2, NULL);

-- =============================================================================
-- SALES
-- =============================================================================

-- =====================================================
-- VBAP: Sales Order Items
-- =====================================================
CREATE OR REPLACE TABLE VBAP (
    VBELN VARCHAR(10) NOT NULL,             -- Sales document number
    POSNR VARCHAR(5) NOT NULL,              -- Sales document item
    MATNR VARCHAR(10),                      -- Material number
    KWMENG NUMBER(10,0),                    -- Order quantity
    NETWR NUMBER(12,2),                     -- Net value
    KUNNR VARCHAR(10),                      -- Customer number
    ERDAT DATE,                             -- Created on date
    VKORG VARCHAR(5),                       -- Sales organization
    PRIMARY KEY (VBELN, POSNR)
);

INSERT INTO VBAP VALUES ('SO-001', '010', 'ASSY-004', 50, 60000.00, 'C-1001', '2025-01-15', '1000');
INSERT INTO VBAP VALUES ('SO-001', '020', 'ASSY-003', 100, 85000.00, 'C-1001', '2025-01-15', '1000');
INSERT INTO VBAP VALUES ('SO-002', '010', 'ASSY-004', 80, 96000.00, 'C-1002', '2025-02-10', '2000');
INSERT INTO VBAP VALUES ('SO-002', '020', 'ASSY-003', 60, 51000.00, 'C-1002', '2025-02-10', '2000');
INSERT INTO VBAP VALUES ('SO-003', '010', 'ASSY-004', 30, 36000.00, 'C-1003', '2025-03-01', '3000');
INSERT INTO VBAP VALUES ('SO-004', '010', 'ASSY-004', 120, 144000.00, 'C-1001', '2025-04-01', '1000');
INSERT INTO VBAP VALUES ('SO-005', '010', 'ASSY-004', 45, 54000.00, 'C-1004', '2025-04-15', '2000');
INSERT INTO VBAP VALUES ('SO-006', '010', 'ASSY-003', 75, 63750.00, 'C-1005', '2025-03-20', '1000');
INSERT INTO VBAP VALUES ('SO-007', '010', 'ASSY-003', 40, 34000.00, 'C-1003', '2025-05-01', '3000');
INSERT INTO VBAP VALUES ('SO-008', '010', 'ASSY-001', 200, 24000.00, 'C-1001', '2025-02-01', '1000');
INSERT INTO VBAP VALUES ('SO-009', '010', 'ASSY-001', 500, 60000.00, 'C-1004', '2025-04-10', '2000');
INSERT INTO VBAP VALUES ('SO-010', '010', 'ASSY-002', 300, 25500.00, 'C-1002', '2025-03-05', '2000');
INSERT INTO VBAP VALUES ('SO-011', '010', 'ASSY-002', 150, 12750.00, 'C-1005', '2025-05-10', '1000');

-- =====================================================
-- KONV: Pricing Conditions
-- =====================================================
CREATE OR REPLACE TABLE KONV (
    KNUMV VARCHAR(10) NOT NULL,             -- Condition document number
    KPOSN VARCHAR(5) NOT NULL,              -- Item number
    KSCHL VARCHAR(5) NOT NULL,              -- Condition type (PR00=Price, K007=Customer discount, KF00=Freight surcharge)
    KBETR NUMBER(8,2),                      -- Condition rate / percentage
    KWERT NUMBER(12,2),                     -- Condition value
    MATNR VARCHAR(10),                      -- Material number
    KUNNR VARCHAR(10),                      -- Customer number
    PRIMARY KEY (KNUMV, KPOSN, KSCHL)
);

INSERT INTO KONV VALUES ('KN-001', '010', 'K007', 5.00, -3000.00, 'ASSY-004', 'C-1001');
INSERT INTO KONV VALUES ('KN-001', '010', 'PR00', 1200.00, 60000.00, 'ASSY-004', 'C-1001');
INSERT INTO KONV VALUES ('KN-001', '020', 'K007', 5.00, -4250.00, 'ASSY-003', 'C-1001');
INSERT INTO KONV VALUES ('KN-001', '020', 'PR00', 850.00, 85000.00, 'ASSY-003', 'C-1001');
INSERT INTO KONV VALUES ('KN-002', '010', 'K007', 8.00, -7680.00, 'ASSY-004', 'C-1002');
INSERT INTO KONV VALUES ('KN-002', '010', 'PR00', 1200.00, 96000.00, 'ASSY-004', 'C-1002');
INSERT INTO KONV VALUES ('KN-002', '020', 'PR00', 850.00, 51000.00, 'ASSY-003', 'C-1002');
INSERT INTO KONV VALUES ('KN-003', '010', 'KF00', 2.00, 720.00, 'ASSY-004', 'C-1003');
INSERT INTO KONV VALUES ('KN-003', '010', 'PR00', 1200.00, 36000.00, 'ASSY-004', 'C-1003');
INSERT INTO KONV VALUES ('KN-004', '010', 'K007', 5.00, -7200.00, 'ASSY-004', 'C-1001');
INSERT INTO KONV VALUES ('KN-004', '010', 'PR00', 1200.00, 144000.00, 'ASSY-004', 'C-1001');
INSERT INTO KONV VALUES ('KN-005', '010', 'K007', 3.00, -1620.00, 'ASSY-004', 'C-1004');
INSERT INTO KONV VALUES ('KN-005', '010', 'PR00', 1200.00, 54000.00, 'ASSY-004', 'C-1004');
INSERT INTO KONV VALUES ('KN-006', '010', 'K007', 4.00, -2550.00, 'ASSY-003', 'C-1005');
INSERT INTO KONV VALUES ('KN-006', '010', 'PR00', 850.00, 63750.00, 'ASSY-003', 'C-1005');
INSERT INTO KONV VALUES ('KN-007', '010', 'KF00', 3.00, 1020.00, 'ASSY-003', 'C-1003');
INSERT INTO KONV VALUES ('KN-007', '010', 'PR00', 850.00, 34000.00, 'ASSY-003', 'C-1003');
INSERT INTO KONV VALUES ('KN-008', '010', 'KF00', 2.00, 480.00, 'ASSY-001', 'C-1001');
INSERT INTO KONV VALUES ('KN-008', '010', 'PR00', 120.00, 24000.00, 'ASSY-001', 'C-1001');
INSERT INTO KONV VALUES ('KN-009', '010', 'K007', 10.00, -6000.00, 'ASSY-001', 'C-1004');
INSERT INTO KONV VALUES ('KN-009', '010', 'PR00', 120.00, 60000.00, 'ASSY-001', 'C-1004');
INSERT INTO KONV VALUES ('KN-010', '010', 'K007', 7.00, -1785.00, 'ASSY-002', 'C-1002');
INSERT INTO KONV VALUES ('KN-010', '010', 'PR00', 85.00, 25500.00, 'ASSY-002', 'C-1002');
INSERT INTO KONV VALUES ('KN-011', '010', 'KF00', 3.00, 382.50, 'ASSY-002', 'C-1005');
INSERT INTO KONV VALUES ('KN-011', '010', 'PR00', 85.00, 12750.00, 'ASSY-002', 'C-1005');

-- =====================================================
-- Verify row counts
-- =====================================================
SELECT 'LFA1' AS TBL, COUNT(*) AS ROW_COUNT FROM LFA1
UNION ALL SELECT 'LFA2', COUNT(*) FROM LFA2
UNION ALL SELECT 'MARA', COUNT(*) FROM MARA
UNION ALL SELECT 'T001W', COUNT(*) FROM T001W
UNION ALL SELECT 'T320', COUNT(*) FROM T320
UNION ALL SELECT 'EKPO', COUNT(*) FROM EKPO
UNION ALL SELECT 'LIKP', COUNT(*) FROM LIKP
UNION ALL SELECT 'LFB1', COUNT(*) FROM LFB1
UNION ALL SELECT 'QALS', COUNT(*) FROM QALS
UNION ALL SELECT 'STPO', COUNT(*) FROM STPO
UNION ALL SELECT 'QUAL_MATRIX', COUNT(*) FROM QUAL_MATRIX
UNION ALL SELECT 'BSEG', COUNT(*) FROM BSEG
UNION ALL SELECT 'COEP', COUNT(*) FROM COEP
UNION ALL SELECT 'VBAP', COUNT(*) FROM VBAP
UNION ALL SELECT 'KONV', COUNT(*) FROM KONV
ORDER BY TBL;
BON_FILE_02_RAW_DATA_SQL

cat > 'sql/03_sap_schema.sql' <<'BON_FILE_03_SAP_SCHEMA_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 03: SAP schema, cloned data, reference (code) tables
-- Built objects live in SAP; the source tables stay untouched in RAW.
-- =====================================================================
USE DATABASE BUSINESS_ONTOLOGY;

CREATE SCHEMA IF NOT EXISTS BUSINESS_ONTOLOGY.SAP
  COMMENT = 'Business Ontology demo: domain SVs (bare/enriched), governed BON, fair 3-agent benchmark';
USE SCHEMA BUSINESS_ONTOLOGY.SAP;

-- Zero-copy clone of the SAP source tables from RAW.
-- PREREQUISITE: run 01_setup.sql and 02_raw_data.sql first;
-- they create RAW and load the synthetic SAP data this script clones.
EXECUTE IMMEDIATE $$
DECLARE
  missing_source EXCEPTION (-20001, 'RAW.LFA1 not found. Run sql/01_setup.sql and sql/02_raw_data.sql first.');
BEGIN
  IF (NOT EXISTS (SELECT 1 FROM BUSINESS_ONTOLOGY.INFORMATION_SCHEMA.TABLES
                  WHERE TABLE_SCHEMA = 'RAW' AND TABLE_NAME = 'LFA1')) THEN
    RAISE missing_source;
  END IF;
  RETURN 'RAW source tables found';
END;
$$;

EXECUTE IMMEDIATE $$
DECLARE
  t ARRAY DEFAULT ARRAY_CONSTRUCT('LFA1','LFA2','LFB1','MARA','EKPO','LIKP','T001W','T320',
                                  'STPO','QALS','BSEG','COEP','VBAP','KONV','QUAL_MATRIX');
  i INTEGER DEFAULT 0;
  n VARCHAR;
BEGIN
  FOR i IN 0 TO ARRAY_SIZE(t)-1 DO
    n := t[i];
    EXECUTE IMMEDIATE 'CREATE OR REPLACE TABLE BUSINESS_ONTOLOGY.SAP.' || n ||
                      ' CLONE BUSINESS_ONTOLOGY.RAW.' || n;
  END FOR;
  RETURN 'cloned ' || ARRAY_SIZE(t);
END;
$$;

-- Reference (code) tables: BON holds one term per code field that points here.
-- New codes arrive via normal ETL into these tables; BON only changes when a rule changes.
CREATE OR REPLACE TABLE T077K (
  KTOKK VARCHAR(10) PRIMARY KEY COMMENT 'Vendor account group code',
  TXT30 VARCHAR(60) COMMENT 'Account group description',
  EXCLUDE_FROM_ACTIVE_COUNT BOOLEAN COMMENT 'TRUE if vendors in this group are excluded from the active supplier count'
) COMMENT = 'Vendor account group reference (code table)' AS
SELECT * FROM VALUES ('ZSTR','Strategic partner',FALSE),('ZSTD','Standard vendor',FALSE),('ZPRB','Probationary vendor',TRUE);

CREATE OR REPLACE TABLE T023T (
  MATKL VARCHAR(5) PRIMARY KEY COMMENT 'Material group code',
  WGBEZ VARCHAR(60) COMMENT 'Material group description'
) COMMENT = 'Material group texts (code table)' AS
SELECT * FROM VALUES ('043','Electronics'),('044','Chemicals'),('045','Metals'),('046','Packaging'),('047','Raw Materials'),('048','Assembly');
BON_FILE_03_SAP_SCHEMA_SQL

cat > 'sql/04_ground_truth.sql' <<'BON_FILE_04_GROUND_TRUTH_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 04: Benchmark questions + SQL-verified ground truth
-- Canonical Revenue = order value net of K007 customer discounts.
-- Gross margin, revenue at risk, and customer profit all build on it.
-- =====================================================================
USE SCHEMA BUSINESS_ONTOLOGY.SAP;

CREATE OR REPLACE TABLE BENCHMARK_QUESTIONS (
  QID VARCHAR, TIER NUMBER, TIER_NAME VARCHAR, VALUE_PILLAR VARCHAR, QUESTION VARCHAR
) AS SELECT * FROM VALUES
('Q01',1,'Business rules (single SV)','baseline-fairness','What is our cost of goods sold for raw materials?'),
('Q02',1,'Business rules (single SV)','baseline-fairness','What is the total cost allocated to US manufacturing?'),
('Q03',1,'Business rules (single SV)','baseline-fairness','How much revenue are we losing to customer discounts?'),
('Q04',1,'Business rules (single SV)','baseline-fairness','How much have we spent on electronics materials?'),
('Q05',1,'Business rules (single SV)','baseline-fairness','What is our net freight cost of goods sold?'),
('Q06',2,'Conflicting definitions & business vocabulary','canonical-choice','How many suppliers do we have?'),
('Q07',2,'Conflicting definitions & business vocabulary','canonical-choice','What is our revenue?'),
('Q08',2,'Conflicting definitions & business vocabulary','canonical-choice','What is our on-time delivery rate?'),
('Q09',2,'Conflicting definitions & business vocabulary','canonical-choice','What does it cost us to make one Integrated System Module (ASSY-004)?'),
('Q19',2,'Conflicting definitions & business vocabulary','canonical-choice','How much have we spent with our Tier A suppliers?'),
('Q10',3,'Cross-SV reasoning','cross-domain','What is the gross margin on the Integrated System Module (ASSY-004)?'),
('Q11',3,'Cross-SV reasoning','cross-domain','If supplier V10089 (Advanced Silicon Solutions) has a force majeure, how much revenue is at risk?'),
('Q12',3,'Cross-SV reasoning','cross-domain','What is our total revenue divided by our number of suppliers?'),
('Q13',3,'Cross-SV reasoning','cross-domain','We need to cut procurement spend by 15%. Which materials should we cut without disrupting production of anything we sell?'),
('Q14',3,'Cross-SV reasoning','cross-domain','Which customer contributes the most profit after material costs?'),
('Q15',4,'Governed meaning','governed-meaning','What counts as an active supplier, and why are some vendors excluded?'),
('Q16',4,'Governed meaning','governed-meaning','Should we report gross bookings or net revenue as our revenue, and why?'),
('Q17',4,'Governed meaning','governed-meaning','Why are credit memos subtracted when calculating COGS?'),
('Q18',4,'Governed meaning','governed-meaning','What is the difference between gross bookings and revenue?'),
('Q20',4,'Governed meaning','governed-meaning','What is our Supplier Resilience Score?');

-- Expected values were computed with the verification queries below.
CREATE OR REPLACE TABLE BENCHMARK_GROUND_TRUTH (
  QID VARCHAR, EXPECTED_VALUE FLOAT, TOLERANCE_PCT FLOAT, CANONICAL_METRIC VARCHAR, PLAUSIBLE_WRONG VARCHAR, GRADING_RULE VARCHAR
) AS SELECT * FROM VALUES
('Q01',1290020,0.5,'COGS Raw Materials','1,417,360 (credit memos added instead of subtracted)','numeric'),
('Q02',419750,0.5,'Cost Center Total','other cost objects included','numeric'),
('Q03',34085,0.5,'Customer Discounts','36,687.50 (freight surcharges KF00 included)','numeric'),
('Q04',505400,0.5,'Procurement Spend','wrong material group code','numeric'),
('Q05',39800,0.5,'COGS Freight','sign not applied to credit memos','numeric'),
('Q06',14,0,'Supplier Count','15 (all vendor master records incl. probationary ZPRB)','numeric'),
('Q07',711915,0.5,'Revenue','746,000 (gross bookings before K007 discounts)','numeric'),
('Q08',66.7,1,'On-Time Delivery Rate','90% (carrier self-reported OTRAT)','numeric'),
('Q09',286.60,0.5,'BOM Cost Rollup','520 (standard price STPRS of the assembly)','numeric'),
('Q10',277355,0.5,'Product Gross Margin','296,855 (gross bookings) or 221,000 (standard price)','numeric'),
('Q11',597450,0.5,'Revenue at Risk','226,950 (ASSY-003 only: direct BOM, missed ASSY-004 at level 2) or 623,750 (gross bookings)','numeric'),
('Q12',50851,0.5,'Revenue / Supplier Count','49,733 (746,000/15) or 47,461 (711,915/15) or 53,286 (746,000/14)','numeric'),
('Q13',203054,0,'Procurement Spend','cuts any BOM input (MAT-001/003/004/007/008/013/015/016/018)','set: all cut materials non-BOM AND total >= 203,054 (15% of 1,353,690)'),
('Q14',223498,0.5,'Customer Profit','C-1001 at 237,948 (gross) or 177,600 (standard price)','numeric: customer C-1001 with ~223,498'),
('Q15',NULL,NULL,'Supplier Count','vague answer without the ZPRB probationary rule','definition: active = KTOKK ZSTR or ZSTD; ZPRB probationary excluded by policy'),
('Q16',NULL,NULL,'Revenue','recommends gross bookings, or says either is fine','definition: report net revenue (order value net of K007 customer discounts, 711,915); gross bookings (746,000) is a Sales pipeline/quota measure, not official revenue'),
('Q17',NULL,NULL,'Credit Memo Sign Rule','no reason given','definition: BSCHL 34 credit memos reverse vendor invoices (BSCHL 31), so they reduce cost'),
('Q18',NULL,NULL,'Revenue','treats them as the same','definition: gross bookings = order value before discounts (Sales view); revenue = net of K007 discounts (canonical)'),
('Q19',251690,0.5,'Tier A Supplier','1,331,190 (strategic + standard, i.e. all active suppliers) or 1,353,690 (all suppliers)','numeric'),
('Q20',NULL,NULL,'(none: not defined)','invents a formula, or presents a different metric (e.g. a risk or quality score) as the Supplier Resilience Score','abstain: states that no governed or official definition of Supplier Resilience Score exists; may suggest related governed metrics or ask for a definition, but must not present an invented or substituted number as the score');

-- ---------------------------------------------------------------------
-- Verification queries (re-run to confirm ground truth)
-- ---------------------------------------------------------------------
-- Q01  SELECT SUM(CASE WHEN BSCHL='31' THEN DMBTR WHEN BSCHL='34' THEN -DMBTR END) FROM BSEG WHERE HKONT='0040100000';  -- 1,290,020
-- Q05  same with HKONT='0040200000';                                                                                  -- 39,800
-- Q06  SELECT COUNT(DISTINCT LIFNR) FROM LFA1 WHERE KTOKK IN ('ZSTR','ZSTD');                                         -- 14
-- Q07  SUM(VBAP.NETWR) - SUM(ABS(KONV.KWERT)) WHERE KSCHL='K007';                                                    -- 746,000 - 34,085 = 711,915
-- Q08  SELECT 100*COUNT_IF(WADAT<=LFDAT)/COUNT(*) FROM LIKP WHERE STATU='D';                                          -- 66.7
-- Q09-Q14 use the recursive BOM rollup below.
WITH RECURSIVE x AS (
  SELECT STLNR AS root, IDNRK AS comp, MENGE::FLOAT AS qty FROM STPO
  UNION ALL SELECT x.root, s.IDNRK, x.qty * s.MENGE FROM x JOIN STPO s ON s.STLNR = x.comp
), leaf AS (
  SELECT root, SUM(x.qty * m.STPRS) bom_cost FROM x JOIN MARA m ON m.MATNR = x.comp
  WHERE x.comp NOT IN (SELECT STLNR FROM STPO) GROUP BY root
), disc AS (
  SELECT MATNR, KUNNR, SUM(ABS(KWERT)) d FROM KONV WHERE KSCHL='K007' GROUP BY 1,2
), v AS (
  SELECT MATNR, KUNNR, SUM(NETWR) gross, SUM(KWMENG) qty FROM VBAP GROUP BY 1,2
)
SELECT v.MATNR, v.KUNNR, v.gross, COALESCE(d.d,0) AS discount, v.gross-COALESCE(d.d,0) AS net_revenue,
       l.bom_cost, v.gross-COALESCE(d.d,0) - l.bom_cost*v.qty AS profit
FROM v JOIN leaf l ON l.root=v.MATNR LEFT JOIN disc d ON d.MATNR=v.MATNR AND d.KUNNR=v.KUNNR
ORDER BY 1,2;
-- ASSY-004 bom_cost 286.60 | margin 370,500 - 93,145 = 277,355 | break-even discount 1 - 286.60/1200 = 76.1%
-- Q11 V10089 supplies MAT-003, MAT-015 (Metals) -> ASSY-003 directly, ASSY-004 only at BOM level 2 (via ASSY-003):
--     net 226,950 + 370,500 = 597,450 | gross 623,750 | direct-BOM-only 226,950
-- Q12 Revenue / Supplier Count = 711,915 / 14 = 50,851
-- Q19 Tier A = ZSTR. SELECT SUM(e.NETWR) FROM EKPO e JOIN LFA1 l USING (LIFNR) WHERE l.KTOKK='ZSTR';    -- 251,690
-- Q20 intentionally undefined everywhere (no SV metric, no BON term).
-- Top customer C-1001: 223,498
BON_FILE_04_GROUND_TRUTH_SQL

cat > 'sql/05_bare_svs.sql' <<'BON_FILE_05_BARE_SVS_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 05: Helper views + BARE domain semantic views
-- BARE = what many teams start with: tables, keys, joins, label comments.
-- No metrics, synonyms, code values, instructions, or verified queries.
-- =====================================================================
USE SCHEMA BUSINESS_ONTOLOGY.SAP;

-- Customer dimension (derived from sales/pricing documents)
CREATE OR REPLACE VIEW CUSTOMERS_VIEW COMMENT = 'Customer master (derived from sales and pricing documents)' AS
SELECT DISTINCT KUNNR FROM (SELECT KUNNR FROM VBAP UNION SELECT KUNNR FROM KONV);

-- Flattened multi-level BOM (used by the ENRICHED Procurement view; BARE uses raw STPO)
CREATE OR REPLACE VIEW BOM_EXPLOSION_VIEW
  COMMENT = 'Multi-level BOM flattened: every component reachable from each assembly with total extended quantity per assembly unit'
AS
WITH RECURSIVE x AS (
  SELECT STLNR AS ASSEMBLY, IDNRK AS COMPONENT, MENGE::NUMBER(18,4) AS QTY, 1 AS LVL FROM STPO
  UNION ALL
  SELECT x.ASSEMBLY, s.IDNRK, (x.QTY * s.MENGE)::NUMBER(18,4), x.LVL + 1 FROM x JOIN STPO s ON s.STLNR = x.COMPONENT
)
SELECT ASSEMBLY, COMPONENT, SUM(QTY)::NUMBER(18,4) AS EXTENDED_QTY, MAX(LVL) AS MAX_BOM_LEVEL,
       COMPONENT NOT IN (SELECT STLNR FROM STPO) AS IS_LEAF
FROM x GROUP BY ASSEMBLY, COMPONENT;

-- ---------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW PROCUREMENT_BARE_SV
TABLES (
  LFA1 AS BUSINESS_ONTOLOGY.SAP.LFA1 PRIMARY KEY (LIFNR) COMMENT = 'Vendor master data',
  T077K AS BUSINESS_ONTOLOGY.SAP.T077K PRIMARY KEY (KTOKK) COMMENT = 'Vendor account groups',
  LFB1 AS BUSINESS_ONTOLOGY.SAP.LFB1 PRIMARY KEY (LIFNR, VKONT) COMMENT = 'Vendor contract data',
  MARA AS BUSINESS_ONTOLOGY.SAP.MARA PRIMARY KEY (MATNR) COMMENT = 'Material master data',
  T023T AS BUSINESS_ONTOLOGY.SAP.T023T PRIMARY KEY (MATKL) COMMENT = 'Material group texts',
  EKPO AS BUSINESS_ONTOLOGY.SAP.EKPO PRIMARY KEY (EBELN, EBELP) COMMENT = 'Purchasing document items',
  T001W AS BUSINESS_ONTOLOGY.SAP.T001W PRIMARY KEY (WERKS) COMMENT = 'Plant data',
  LIKP AS BUSINESS_ONTOLOGY.SAP.LIKP PRIMARY KEY (TKNUM) COMMENT = 'Shipment data',
  LFA2 AS BUSINESS_ONTOLOGY.SAP.LFA2 PRIMARY KEY (TDLNR) COMMENT = 'Forwarding agent data',
  QALS AS BUSINESS_ONTOLOGY.SAP.QALS PRIMARY KEY (PRUEFLOS) COMMENT = 'Inspection lot data',
  STPO AS BUSINESS_ONTOLOGY.SAP.STPO PRIMARY KEY (STLNR, IDNRK) COMMENT = 'BOM items'
)
RELATIONSHIPS (
  LFA1 (KTOKK) REFERENCES T077K,
  MARA (MATKL) REFERENCES T023T,
  LFB1 (LIFNR) REFERENCES LFA1,
  EKPO (LIFNR) REFERENCES LFA1,
  EKPO (MATNR) REFERENCES MARA,
  EKPO (WERKS) REFERENCES T001W,
  LIKP (TDLNR) REFERENCES LFA2,
  LIKP (WERKS_DST) REFERENCES T001W,
  QALS (MATNR) REFERENCES MARA,
  STPO (IDNRK) REFERENCES MARA
)
FACTS (
  MARA.STPRS AS STPRS COMMENT = 'Standard price',
  EKPO.NETWR AS NETWR COMMENT = 'Net order value',
  EKPO.MENGE AS MENGE COMMENT = 'Purchase order quantity',
  LIKP.MENGE AS MENGE COMMENT = 'Delivery quantity',
  LIKP.FRTCO AS FRTCO COMMENT = 'Freight cost',
  LFA2.OTRAT AS OTRAT COMMENT = 'Carrier on-time ratio',
  LFA2.LZEIT AS LZEIT COMMENT = 'Transit time',
  QALS.QAESSION AS QAESSION COMMENT = 'Defect rate',
  LFB1.JWERT AS JWERT COMMENT = 'Annual contract value',
  STPO.MENGE AS MENGE COMMENT = 'Component quantity',
  STPO.STUFE AS STUFE COMMENT = 'BOM level'
)
DIMENSIONS (
  LFA1.LIFNR AS LIFNR COMMENT = 'Vendor number', LFA1.NAME1 AS NAME1 COMMENT = 'Vendor name', LFA1.ORT01 AS ORT01 COMMENT = 'City', LFA1.LAND1 AS LAND1 COMMENT = 'Country code', LFA1.KTOKK AS KTOKK COMMENT = 'Account group', LFA1.ZTERM AS ZTERM COMMENT = 'Payment terms key',
  T077K.KTOKK AS KTOKK COMMENT = 'Account group', T077K.TXT30 AS TXT30 COMMENT = 'Description', T077K.EXCLUDE_FROM_ACTIVE_COUNT AS EXCLUDE_FROM_ACTIVE_COUNT COMMENT = 'Exclude flag',
  LFB1.VKONT AS VKONT COMMENT = 'Contract account', LFB1.VTART AS VTART COMMENT = 'Contract type', LFB1.DTEND AS DTEND COMMENT = 'Validity end date',
  MARA.MATNR AS MATNR COMMENT = 'Material number', MARA.MAKTX AS MAKTX COMMENT = 'Material description', MARA.MATKL AS MATKL COMMENT = 'Material group',
  T023T.WGBEZ AS WGBEZ COMMENT = 'Material group description',
  EKPO.EBELN AS EBELN COMMENT = 'Purchasing document number', EKPO.EBELP AS EBELP COMMENT = 'Item number', EKPO.LIFNR AS LIFNR COMMENT = 'Vendor number', EKPO.MATNR AS MATNR COMMENT = 'Material number', EKPO.WERKS AS WERKS COMMENT = 'Plant', EKPO.STATU AS STATU COMMENT = 'Status', EKPO.BEDAT AS BEDAT COMMENT = 'Purchasing document date',
  T001W.WERKS AS WERKS COMMENT = 'Plant', T001W.NAME1 AS NAME1 COMMENT = 'Name', T001W.REGIO AS REGIO COMMENT = 'Region',
  LIKP.TKNUM AS TKNUM COMMENT = 'Shipment number', LIKP.TDLNR AS TDLNR COMMENT = 'Forwarding agent', LIKP.MATNR AS MATNR COMMENT = 'Material number', LIKP.STATU AS STATU COMMENT = 'Delivery status', LIKP.LFDAT AS LFDAT COMMENT = 'Delivery date', LIKP.WADAT AS WADAT COMMENT = 'Goods issue date', LIKP.WERKS_DST AS WERKS_DST COMMENT = 'Destination plant',
  LFA2.TDLNR AS TDLNR COMMENT = 'Forwarding agent', LFA2.NAME1 AS NAME1 COMMENT = 'Name', LFA2.VSART AS VSART COMMENT = 'Shipping type',
  QALS.PRUEFLOS AS PRUEFLOS COMMENT = 'Inspection lot', QALS.MATNR AS MATNR COMMENT = 'Material number', QALS.VCODE AS VCODE COMMENT = 'Usage decision code',
  STPO.STLNR AS STLNR COMMENT = 'Bill of material', STPO.IDNRK AS IDNRK COMMENT = 'BOM component'
)
COMMENT = 'SAP procurement data: vendors, materials, purchase orders, shipments, carriers, inspections, BOM';

-- ---------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW FINANCE_BARE_SV
TABLES (
  BSEG AS BUSINESS_ONTOLOGY.SAP.BSEG PRIMARY KEY (BELNR, BUZEI) COMMENT = 'Accounting document line items',
  COEP AS BUSINESS_ONTOLOGY.SAP.COEP COMMENT = 'Cost element line items',
  LFA1 AS BUSINESS_ONTOLOGY.SAP.LFA1 PRIMARY KEY (LIFNR) COMMENT = 'Vendor master data',
  T077K AS BUSINESS_ONTOLOGY.SAP.T077K PRIMARY KEY (KTOKK) COMMENT = 'Vendor account groups'
)
RELATIONSHIPS (
  BSEG (LIFNR) REFERENCES LFA1,
  LFA1 (KTOKK) REFERENCES T077K
)
FACTS (
  BSEG.DMBTR AS DMBTR COMMENT = 'Amount in local currency',
  COEP.WRTBTR AS WRTBTR COMMENT = 'Value in reporting currency'
)
DIMENSIONS (
  BSEG.BELNR AS BELNR COMMENT = 'Document number', BSEG.BUZEI AS BUZEI COMMENT = 'Line item', BSEG.EBELN AS EBELN COMMENT = 'Purchasing document number', BSEG.LIFNR AS LIFNR COMMENT = 'Vendor number', BSEG.HKONT AS HKONT COMMENT = 'GL account', BSEG.BSCHL AS BSCHL COMMENT = 'Posting key', BSEG.GJAHR AS GJAHR COMMENT = 'Fiscal year', BSEG.MONAT AS MONAT COMMENT = 'Fiscal period', BSEG.BUDAT AS BUDAT COMMENT = 'Posting date',
  COEP.OBJNR AS OBJNR COMMENT = 'Cost object number', COEP.KSTAR AS KSTAR COMMENT = 'Cost element', COEP.GJAHR AS GJAHR COMMENT = 'Fiscal year', COEP.PERIO AS PERIO COMMENT = 'Period', COEP.MATNR AS MATNR COMMENT = 'Material number',
  LFA1.NAME1 AS NAME1 COMMENT = 'Vendor name', LFA1.KTOKK AS KTOKK COMMENT = 'Account group',
  T077K.TXT30 AS TXT30 COMMENT = 'Description', T077K.EXCLUDE_FROM_ACTIVE_COUNT AS EXCLUDE_FROM_ACTIVE_COUNT COMMENT = 'Exclude flag'
)
COMMENT = 'SAP finance data: accounting line items, cost postings, vendors';

-- ---------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW SALES_BARE_SV
TABLES (
  VBAP AS BUSINESS_ONTOLOGY.SAP.VBAP PRIMARY KEY (VBELN, POSNR) COMMENT = 'Sales document items',
  KONV AS BUSINESS_ONTOLOGY.SAP.KONV PRIMARY KEY (KNUMV, KPOSN, KSCHL) COMMENT = 'Pricing condition records',
  MARA AS BUSINESS_ONTOLOGY.SAP.MARA PRIMARY KEY (MATNR) COMMENT = 'Material master data',
  KNA1 AS BUSINESS_ONTOLOGY.SAP.CUSTOMERS_VIEW PRIMARY KEY (KUNNR) COMMENT = 'Customers'
)
RELATIONSHIPS (
  VBAP (MATNR) REFERENCES MARA,
  VBAP (KUNNR) REFERENCES KNA1,
  KONV (MATNR) REFERENCES MARA,
  KONV (KUNNR) REFERENCES KNA1
)
FACTS (
  VBAP.NETWR AS NETWR COMMENT = 'Net value',
  VBAP.KWMENG AS KWMENG COMMENT = 'Order quantity',
  KONV.KBETR AS KBETR COMMENT = 'Rate',
  KONV.KWERT AS KWERT COMMENT = 'Condition value',
  MARA.STPRS AS STPRS COMMENT = 'Standard price'
)
DIMENSIONS (
  VBAP.VBELN AS VBELN COMMENT = 'Sales document', VBAP.POSNR AS POSNR COMMENT = 'Item number', VBAP.MATNR AS MATNR COMMENT = 'Material number', VBAP.KUNNR AS KUNNR COMMENT = 'Customer number', VBAP.VKORG AS VKORG COMMENT = 'Sales organization', VBAP.ERDAT AS ERDAT COMMENT = 'Created on date',
  KONV.KNUMV AS KNUMV COMMENT = 'Condition number', KONV.KPOSN AS KPOSN COMMENT = 'Condition item', KONV.KSCHL AS KSCHL COMMENT = 'Condition type', KONV.MATNR AS MATNR COMMENT = 'Material number', KONV.KUNNR AS KUNNR COMMENT = 'Customer number',
  MARA.MATNR AS MATNR COMMENT = 'Material number', MARA.MAKTX AS MAKTX COMMENT = 'Material description', MARA.MATKL AS MATKL COMMENT = 'Material group',
  KNA1.KUNNR AS KUNNR COMMENT = 'Customer number'
)
COMMENT = 'SAP sales data: sales document items, pricing conditions, materials, customers';
BON_FILE_05_BARE_SVS_SQL

cat > 'sql/06_enriched_svs.sql' <<'BON_FILE_06_ENRICHED_SVS_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 06: ENRICHED domain semantic views
-- ENRICHED = what a strong customer builds for each team: metrics, code
-- values in comments, synonyms, custom instructions, verified queries.
--
-- Deliberate, realistic conflicts across teams (each defensible locally):
--   Supplier count : Procurement vendor_record_count = 15  vs  Finance active_supplier_count = 14
--   On-time rate   : Procurement carrier_otd_rate = 90%    vs  operational_otd_rate = 66.7%
--   Revenue        : Sales gross_bookings = 746,000       vs  net_revenue = 711,915
--   Unit cost      : Procurement avg_standard_price (STPRS) vs bom_material_cost
-- Enriched SVs document each team's rules but NOT the cross-team canonical
-- decision. That decision is what Business Ontology governs.
-- =====================================================================
USE SCHEMA BUSINESS_ONTOLOGY.SAP;

CREATE OR REPLACE SEMANTIC VIEW PROCUREMENT_ENRICHED_SV
TABLES (
  vendors AS BUSINESS_ONTOLOGY.SAP.LFA1 PRIMARY KEY (LIFNR) WITH SYNONYMS ('suppliers','vendor master') COMMENT = 'Vendor master (LFA1). One row per vendor record, including probationary vendors.',
  account_groups AS BUSINESS_ONTOLOGY.SAP.T077K PRIMARY KEY (KTOKK) COMMENT = 'Vendor account group code table (T077K).',
  contracts AS BUSINESS_ONTOLOGY.SAP.LFB1 PRIMARY KEY (LIFNR, VKONT) COMMENT = 'Vendor contracts (LFB1).',
  materials AS BUSINESS_ONTOLOGY.SAP.MARA PRIMARY KEY (MATNR) WITH SYNONYMS ('products','parts') COMMENT = 'Material master (MARA): raw materials and assemblies.',
  material_groups AS BUSINESS_ONTOLOGY.SAP.T023T PRIMARY KEY (MATKL) COMMENT = 'Material group code table (T023T).',
  purchase_orders AS BUSINESS_ONTOLOGY.SAP.EKPO PRIMARY KEY (EBELN, EBELP) WITH SYNONYMS ('PO lines','procurement') COMMENT = 'Purchase order line items (EKPO).',
  plants AS BUSINESS_ONTOLOGY.SAP.T001W PRIMARY KEY (WERKS) COMMENT = 'Plants (T001W).',
  shipments AS BUSINESS_ONTOLOGY.SAP.LIKP PRIMARY KEY (TKNUM) WITH SYNONYMS ('deliveries') COMMENT = 'Inbound shipments (LIKP).',
  carriers AS BUSINESS_ONTOLOGY.SAP.LFA2 PRIMARY KEY (TDLNR) WITH SYNONYMS ('forwarding agents','logistics providers') COMMENT = 'Carriers / forwarding agents (LFA2).',
  inspections AS BUSINESS_ONTOLOGY.SAP.QALS PRIMARY KEY (PRUEFLOS) COMMENT = 'Quality inspection lots (QALS).',
  bom AS BUSINESS_ONTOLOGY.SAP.BOM_EXPLOSION_VIEW PRIMARY KEY (ASSEMBLY, COMPONENT) WITH SYNONYMS ('bill of materials') COMMENT = 'Flattened multi-level bill of materials: every component of each assembly with extended quantity per one assembly unit.'
)
RELATIONSHIPS (
  vendors_to_groups AS vendors (KTOKK) REFERENCES account_groups,
  materials_to_groups AS materials (MATKL) REFERENCES material_groups,
  contracts_to_vendors AS contracts (LIFNR) REFERENCES vendors,
  po_to_vendors AS purchase_orders (LIFNR) REFERENCES vendors,
  po_to_materials AS purchase_orders (MATNR) REFERENCES materials,
  po_to_plants AS purchase_orders (WERKS) REFERENCES plants,
  shipments_to_carriers AS shipments (TDLNR) REFERENCES carriers,
  shipments_to_plants AS shipments (WERKS_DST) REFERENCES plants,
  inspections_to_materials AS inspections (MATNR) REFERENCES materials,
  bom_to_components AS bom (COMPONENT) REFERENCES materials
)
FACTS (
  materials.standard_price AS STPRS COMMENT = 'Standard price per unit (STPRS). For assemblies this is a planning price, not the material cost to build.',
  purchase_orders.order_value AS NETWR COMMENT = 'Net PO line value',
  purchase_orders.order_qty AS MENGE COMMENT = 'PO quantity',
  shipments.freight_cost AS FRTCO COMMENT = 'Freight cost per shipment',
  shipments.is_on_time AS IFF(WADAT <= LFDAT, 1, 0) COMMENT = '1 if goods issue date on or before planned delivery date',
  shipments.is_delivered AS IFF(STATU = 'D', 1, 0) COMMENT = '1 if shipment status is D (delivered)',
  carriers.carrier_on_time_ratio AS OTRAT COMMENT = 'Carrier self-reported on-time ratio (0-1)',
  inspections.defect_rate AS QAESSION COMMENT = 'Defect rate of the inspection lot',
  contracts.annual_contract_value AS JWERT COMMENT = 'Annual contract value',
  bom.extended_qty AS EXTENDED_QTY COMMENT = 'Component quantity needed for one unit of the assembly',
  bom.leaf_material_cost AS IFF(IS_LEAF, EXTENDED_QTY * materials.standard_price, 0) COMMENT = 'Material cost contributed by a leaf (purchased) component per assembly unit'
)
DIMENSIONS (
  vendors.vendor_id AS LIFNR WITH SYNONYMS ('supplier id','LIFNR') COMMENT = 'Vendor number',
  vendors.vendor_name AS NAME1 COMMENT = 'Vendor name',
  vendors.vendor_city AS ORT01 COMMENT = 'City',
  vendors.vendor_country AS LAND1 COMMENT = 'Country code',
  vendors.account_group AS KTOKK WITH SYNONYMS ('KTOKK','vendor type') COMMENT = 'Vendor account group: ZSTR = Strategic partner, ZSTD = Standard vendor, ZPRB = Probationary vendor',
  account_groups.account_group_name AS TXT30 COMMENT = 'Account group description',
  account_groups.excluded_from_active_count AS EXCLUDE_FROM_ACTIVE_COUNT COMMENT = 'TRUE for groups excluded from active supplier counts (ZPRB)',
  materials.material_id AS MATNR WITH SYNONYMS ('MATNR','part number') COMMENT = 'Material number. ASSY-* are assemblies we sell; MAT-* are purchased components.',
  materials.material_name AS MAKTX COMMENT = 'Material description',
  materials.material_group AS MATKL WITH SYNONYMS ('MATKL') COMMENT = 'Material group code: 043 Electronics, 044 Chemicals, 045 Metals, 046 Packaging, 047 Raw Materials, 048 Assembly',
  material_groups.material_group_name AS WGBEZ WITH SYNONYMS ('category') COMMENT = 'Material group description',
  purchase_orders.po_number AS EBELN COMMENT = 'Purchase order number',
  purchase_orders.po_status AS STATU COMMENT = 'PO status',
  purchase_orders.po_date AS BEDAT COMMENT = 'PO date',
  plants.plant_id AS WERKS COMMENT = 'Plant',
  plants.plant_name AS NAME1 COMMENT = 'Plant name',
  plants.region AS REGIO COMMENT = 'Region',
  shipments.shipment_id AS TKNUM COMMENT = 'Shipment number',
  shipments.shipment_status AS STATU COMMENT = 'Shipment status: D = Delivered, T = In transit, X = Cancelled',
  shipments.planned_delivery_date AS LFDAT COMMENT = 'Planned delivery date',
  shipments.goods_issue_date AS WADAT COMMENT = 'Actual goods issue date',
  carriers.carrier_id AS TDLNR COMMENT = 'Carrier id',
  carriers.carrier_name AS NAME1 COMMENT = 'Carrier name',
  carriers.shipping_type AS VSART COMMENT = 'Shipping type',
  inspections.usage_decision AS VCODE COMMENT = 'Inspection usage decision code',
  contracts.contract_type AS VTART COMMENT = 'Contract type',
  bom.assembly_id AS ASSEMBLY WITH SYNONYMS ('finished good','assembly') COMMENT = 'Assembly material number (ASSY-*)',
  bom.component_id AS COMPONENT COMMENT = 'Component material number',
  bom.is_leaf_component AS IS_LEAF COMMENT = 'TRUE if the component is purchased (not a sub-assembly)'
)
METRICS (
  vendors.vendor_record_count AS COUNT(DISTINCT vendors.LIFNR) WITH SYNONYMS ('supplier count','number of suppliers','vendor count') COMMENT = 'Count of vendor master records. Procurement operational view: includes every vendor on file, including probationary (ZPRB).',
  purchase_orders.procurement_spend AS SUM(purchase_orders.order_value) WITH SYNONYMS ('spend','purchase spend') COMMENT = 'Total net PO value',
  carriers.carrier_otd_rate AS AVG(carriers.carrier_on_time_ratio) * 100 WITH SYNONYMS ('on-time delivery rate','OTD','carrier on-time rate') COMMENT = 'Average carrier self-reported on-time rate, in percent',
  shipments.operational_otd_rate AS 100 * SUM(shipments.is_on_time * shipments.is_delivered) / NULLIF(SUM(shipments.is_delivered), 0) WITH SYNONYMS ('actual on-time delivery','measured OTD') COMMENT = 'Percent of delivered shipments with goods issue on or before planned date, in percent',
  shipments.total_freight_cost AS SUM(shipments.freight_cost) COMMENT = 'Total freight cost on shipments',
  bom.bom_material_cost AS SUM(bom.leaf_material_cost) WITH SYNONYMS ('BOM cost','material cost per unit','cost to build') COMMENT = 'Material cost to build one unit of an assembly: sum of extended quantity x standard price over purchased (leaf) components. Group by assembly_id.',
  materials.avg_standard_price AS AVG(materials.standard_price) WITH SYNONYMS ('unit cost','standard cost') COMMENT = 'Average standard price (STPRS)',
  inspections.avg_defect_rate AS AVG(inspections.defect_rate) COMMENT = 'Average defect rate'
)
COMMENT = 'Procurement domain (owned by the Purchasing team): vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.'
AI_SQL_GENERATION 'Material codes: MATKL 043 = Electronics, 047 = Raw Materials, 048 = Assembly. Join material_groups for group names. Assemblies (ASSY-*) are built from components listed in bom; bom already includes all levels, so never recurse. Shipment status D = delivered.'
AI_VERIFIED_QUERIES (
  spend_by_group AS (QUESTION 'Procurement spend by material group' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV METRICS purchase_orders.procurement_spend DIMENSIONS material_groups.material_group_name)'),
  bom_cost_by_assembly AS (QUESTION 'Material cost to build each assembly' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV METRICS bom.bom_material_cost DIMENSIONS bom.assembly_id)')
);

-- ---------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW FINANCE_ENRICHED_SV
TABLES (
  ap_lines AS BUSINESS_ONTOLOGY.SAP.BSEG PRIMARY KEY (BELNR, BUZEI) WITH SYNONYMS ('accounts payable','AP postings','invoices') COMMENT = 'Accounting document line items (BSEG) for vendor invoices and credit memos.',
  cost_postings AS BUSINESS_ONTOLOGY.SAP.COEP WITH SYNONYMS ('cost allocations','controlling postings') COMMENT = 'Controlling cost postings by cost object (COEP).',
  vendors AS BUSINESS_ONTOLOGY.SAP.LFA1 PRIMARY KEY (LIFNR) WITH SYNONYMS ('suppliers') COMMENT = 'Vendor master (LFA1) as used by Finance.',
  account_groups AS BUSINESS_ONTOLOGY.SAP.T077K PRIMARY KEY (KTOKK) COMMENT = 'Vendor account group code table (T077K).'
)
RELATIONSHIPS (
  ap_to_vendors AS ap_lines (LIFNR) REFERENCES vendors,
  vendors_to_groups AS vendors (KTOKK) REFERENCES account_groups
)
FACTS (
  ap_lines.amount AS DMBTR COMMENT = 'Posting amount in local currency (always positive; direction comes from posting_key)',
  ap_lines.signed_amount AS CASE WHEN BSCHL = '31' THEN DMBTR WHEN BSCHL = '34' THEN -DMBTR ELSE 0 END COMMENT = 'Amount with sign: invoice (31) positive, credit memo (34) negative',
  cost_postings.posted_cost AS WRTBTR COMMENT = 'Cost value in reporting currency'
)
DIMENSIONS (
  ap_lines.document_number AS BELNR COMMENT = 'Accounting document number',
  ap_lines.po_number AS EBELN COMMENT = 'Purchase order number',
  ap_lines.vendor_id AS LIFNR COMMENT = 'Vendor number',
  ap_lines.gl_account AS HKONT WITH SYNONYMS ('HKONT','GL account') COMMENT = 'GL account: 0040100000 = COGS Raw Materials, 0040200000 = COGS Freight, 0021100000 = Accounts Payable',
  ap_lines.posting_key AS BSCHL WITH SYNONYMS ('BSCHL') COMMENT = 'Posting key: 31 = vendor invoice (adds cost), 34 = vendor credit memo (reduces cost)',
  ap_lines.fiscal_year AS GJAHR COMMENT = 'Fiscal year',
  ap_lines.fiscal_period AS MONAT COMMENT = 'Fiscal period',
  ap_lines.posting_date AS BUDAT COMMENT = 'Posting date',
  cost_postings.cost_object AS OBJNR WITH SYNONYMS ('OBJNR','cost center') COMMENT = 'Cost object: KS-MFG-US = US Manufacturing, KS-MFG-EU = EU Manufacturing, KS-MFG-AP = APAC Manufacturing, KS-LOG = Logistics, KS-QA = Quality Assurance',
  cost_postings.cost_element AS KSTAR COMMENT = 'Cost element',
  cost_postings.material_id AS MATNR COMMENT = 'Material number',
  vendors.vendor_name AS NAME1 COMMENT = 'Vendor name',
  vendors.account_group AS KTOKK WITH SYNONYMS ('KTOKK') COMMENT = 'Vendor account group: ZSTR = Strategic, ZSTD = Standard, ZPRB = Probationary',
  account_groups.excluded_from_active_count AS EXCLUDE_FROM_ACTIVE_COUNT COMMENT = 'TRUE for probationary groups'
)
METRICS (
  ap_lines.cogs_raw_materials AS SUM(IFF(ap_lines.HKONT = '0040100000', ap_lines.signed_amount, 0)) WITH SYNONYMS ('COGS','cost of goods sold','raw material COGS') COMMENT = 'COGS for raw materials: GL 0040100000, invoices minus credit memos',
  ap_lines.cogs_freight AS SUM(IFF(ap_lines.HKONT = '0040200000', ap_lines.signed_amount, 0)) WITH SYNONYMS ('freight COGS') COMMENT = 'Freight COGS: GL 0040200000, invoices minus credit memos',
  ap_lines.net_ap_amount AS SUM(ap_lines.signed_amount) COMMENT = 'Net payable amount across all GL accounts, credit memos subtracted',
  cost_postings.total_posted_cost AS SUM(cost_postings.posted_cost) WITH SYNONYMS ('allocated cost','cost center total') COMMENT = 'Total cost posted; filter or group by cost_object',
  vendors.active_supplier_count AS COUNT(DISTINCT IFF(vendors.KTOKK IN ('ZSTR','ZSTD'), vendors.LIFNR, NULL)) WITH SYNONYMS ('supplier count','number of suppliers','active vendors') COMMENT = 'Active suppliers for Finance reporting: strategic (ZSTR) and standard (ZSTD) vendors; probationary (ZPRB) excluded'
)
COMMENT = 'Finance & Controlling domain (owned by the Finance team): AP postings, COGS, cost allocations.'
AI_SQL_GENERATION 'Always apply the posting-key sign: BSCHL 31 adds, BSCHL 34 subtracts. Use signed_amount, never raw amount, for any cost or COGS total. Cost object codes are in cost_object.'
AI_VERIFIED_QUERIES (
  cogs_raw AS (QUESTION 'What is COGS for raw materials?' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV METRICS ap_lines.cogs_raw_materials)'),
  cost_by_object AS (QUESTION 'Total cost by cost object' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV METRICS cost_postings.total_posted_cost DIMENSIONS cost_postings.cost_object)')
);

-- ---------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW SALES_ENRICHED_SV
TABLES (
  sales_items AS BUSINESS_ONTOLOGY.SAP.VBAP PRIMARY KEY (VBELN, POSNR) WITH SYNONYMS ('sales orders','orders','bookings') COMMENT = 'Sales order line items (VBAP). NETWR is the order value before customer discounts.',
  pricing AS BUSINESS_ONTOLOGY.SAP.KONV PRIMARY KEY (KNUMV, KPOSN, KSCHL) WITH SYNONYMS ('pricing conditions','conditions') COMMENT = 'Pricing condition records (KONV): list price, discounts, surcharges.',
  products AS BUSINESS_ONTOLOGY.SAP.MARA PRIMARY KEY (MATNR) WITH SYNONYMS ('materials','assemblies') COMMENT = 'Material master (MARA): the assemblies we sell.',
  customers AS BUSINESS_ONTOLOGY.SAP.CUSTOMERS_VIEW PRIMARY KEY (KUNNR) WITH SYNONYMS ('accounts','clients') COMMENT = 'Customers.'
)
RELATIONSHIPS (
  sales_to_products AS sales_items (MATNR) REFERENCES products,
  sales_to_customers AS sales_items (KUNNR) REFERENCES customers,
  pricing_to_products AS pricing (MATNR) REFERENCES products,
  pricing_to_customers AS pricing (KUNNR) REFERENCES customers
)
FACTS (
  sales_items.order_value AS NETWR COMMENT = 'Order line value before customer discounts',
  sales_items.order_qty AS KWMENG COMMENT = 'Units ordered',
  pricing.condition_value AS KWERT COMMENT = 'Condition value (discounts are negative)',
  pricing.condition_rate AS KBETR COMMENT = 'Condition rate; for PR00 this is the list price per unit',
  pricing.discount_amount AS IFF(KSCHL = 'K007', ABS(KWERT), 0) COMMENT = 'Customer discount amount (K007), positive',
  pricing.surcharge_amount AS IFF(KSCHL = 'KF00', ABS(KWERT), 0) COMMENT = 'Freight surcharge amount (KF00)'
)
DIMENSIONS (
  sales_items.sales_document AS VBELN COMMENT = 'Sales document number',
  sales_items.sales_org AS VKORG WITH SYNONYMS ('VKORG','sales organization','region') COMMENT = 'Sales organization: 1000 = Americas, 2000 = EMEA, 3000 = APAC',
  sales_items.order_date AS ERDAT COMMENT = 'Order created date',
  pricing.condition_type AS KSCHL WITH SYNONYMS ('KSCHL') COMMENT = 'Condition type: PR00 = list price, K007 = customer discount, KF00 = freight surcharge',
  products.product_id AS MATNR WITH SYNONYMS ('MATNR','assembly id') COMMENT = 'Material number (ASSY-* assemblies)',
  products.product_name AS MAKTX COMMENT = 'Product description',
  customers.customer_id AS KUNNR WITH SYNONYMS ('KUNNR','customer number') COMMENT = 'Customer number'
)
METRICS (
  sales_items.gross_bookings AS SUM(sales_items.order_value) WITH SYNONYMS ('revenue','sales','total sales','bookings') COMMENT = 'Gross bookings: total order value before customer discounts. Sales team pipeline and quota metric.',
  sales_items.units_sold AS SUM(sales_items.order_qty) WITH SYNONYMS ('quantity sold','volume') COMMENT = 'Units ordered',
  pricing.customer_discounts AS SUM(pricing.discount_amount) WITH SYNONYMS ('discounts','discount leakage','revenue lost to discounts') COMMENT = 'Customer discounts granted (K007 only; excludes freight surcharges)',
  pricing.freight_surcharges AS SUM(pricing.surcharge_amount) COMMENT = 'Freight surcharges billed (KF00)',
  pricing.list_price AS AVG(IFF(pricing.KSCHL = 'PR00', pricing.condition_rate, NULL)) WITH SYNONYMS ('price','unit price') COMMENT = 'List price per unit (PR00 condition rate)',
  net_revenue AS sales_items.gross_bookings - pricing.customer_discounts WITH SYNONYMS ('net sales','revenue after discounts') COMMENT = 'Order value net of K007 customer discounts'
)
COMMENT = 'Sales & Distribution domain (owned by the Sales team): orders, pricing conditions, customers.'
AI_SQL_GENERATION 'Discounts are condition type K007; freight surcharges KF00 are not discounts. List price is the PR00 condition rate.'
AI_VERIFIED_QUERIES (
  bookings_by_product AS (QUESTION 'Gross bookings by product' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV METRICS sales_items.gross_bookings DIMENSIONS products.product_id)'),
  discounts_total AS (QUESTION 'How much do we give away in customer discounts?' SQL 'SELECT * FROM SEMANTIC_VIEW(BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV METRICS pricing.customer_discounts)')
);

-- Verification (all match BENCHMARK_GROUND_TRUTH):
-- SELECT * FROM SEMANTIC_VIEW(PROCUREMENT_ENRICHED_SV METRICS bom.bom_material_cost DIMENSIONS bom.assembly_id);   -- ASSY-004 = 286.60
-- SELECT * FROM SEMANTIC_VIEW(PROCUREMENT_ENRICHED_SV METRICS shipments.operational_otd_rate, carriers.carrier_otd_rate); -- 66.7 / 90
-- SELECT * FROM SEMANTIC_VIEW(FINANCE_ENRICHED_SV METRICS ap_lines.cogs_raw_materials, ap_lines.cogs_freight, vendors.active_supplier_count); -- 1,290,020 / 39,800 / 14
-- SELECT * FROM SEMANTIC_VIEW(SALES_ENRICHED_SV METRICS sales_items.gross_bookings, pricing.customer_discounts, net_revenue);  -- 746,000 / 34,085 / 711,915
BON_FILE_06_ENRICHED_SVS_SQL

cat > 'sql/07_ontology.sql' <<'BON_FILE_07_ONTOLOGY_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 07: Governed Business Ontology
-- 3 domains, 40 nodes (ENTITY / METRIC / TERM / POLICY_CONCEPT), 51 typed edges.
--
-- Design rules:
--   * Every METRIC states the canonical definition in plain language, names the
--     SV metric that implements it, and names the non-canonical variants.
--   * Variants are separate METRIC nodes with a `scope` and a HAS_VARIANT edge.
--   * Code fields are one TERM each, pointing to a reference table; never one node per code value.
--   * Business rules are POLICY_CONCEPT nodes linked with APPLIES_TO.
--   * Cross-domain metrics (margin, profit, break-even, revenue at risk) carry the
--     reasoning chain; the SVs compute each piece.
--
-- Run after 06_enriched_svs.sql. Term references below use Domain.Term paths;
-- if a name collides with a term in another domain, use the termId returned by DRAFT.
-- =====================================================================

-- ---------------------------------------------------------------- Domains
SELECT SYSTEM$CREATE_GLOSSARY_DOMAIN('Procurement', 'Governed procurement concepts: suppliers, materials, purchasing, logistics, bill of materials. Steward: Procurement data steward.');
SELECT SYSTEM$CREATE_GLOSSARY_DOMAIN('Finance & Controlling', 'Governed finance concepts: revenue, COGS, margin, cost allocation, posting rules. Steward: Finance data steward.');
SELECT SYSTEM$CREATE_GLOSSARY_DOMAIN('Sales & Distribution', 'Governed sales concepts: orders, bookings, pricing conditions, discounts, customers. Steward: Sales data steward.');

-- ---------------------------------------------------------------- Procurement nodes
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Supplier","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Vendor","Supply partner"],"description":"A company we buy materials from, recorded in the vendor master (LFA1). Each supplier has an account group (KTOKK) that determines whether it counts as an active supplier."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Material","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Part","Component","Raw material"],"description":"A purchased item in the material master (MARA), identified by MATNR (MAT-*). Materials are grouped by material group (MATKL)."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Assembly","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Finished good","Product","Sellable product"],"description":"A product we build and sell (ASSY-*), made from materials and sub-assemblies defined in the bill of materials. Assemblies are the items on sales orders."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Bill of Materials","domainName":"Procurement","itemKind":"ENTITY","synonyms":["BOM","Product structure"],"description":"The multi-level structure of components and quantities needed to build one unit of an assembly (STPO). Sub-assemblies have their own BOMs, so costs and dependencies must be traced through every level."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Purchase Order","domainName":"Procurement","itemKind":"ENTITY","synonyms":["PO","PO line"],"description":"An order line placed with a supplier for a material (EKPO). Its net value (NETWR) is procurement spend."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Shipment","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Delivery","Inbound shipment"],"description":"An inbound delivery (LIKP) with a planned delivery date (LFDAT), actual goods issue date (WADAT), and status (D delivered, T in transit, X cancelled)."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Carrier","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Forwarding agent","Logistics provider"],"description":"A logistics provider that moves shipments (LFA2). Carriers self-report an on-time ratio (OTRAT), which is not the official on-time measure."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Inspection Lot","domainName":"Procurement","itemKind":"ENTITY","synonyms":["Quality inspection"],"description":"A quality inspection of a material batch (QALS) with a measured defect rate."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Supplier Count","domainName":"Procurement","itemKind":"METRIC","synonyms":["Number of suppliers","Active suppliers","Active supplier count"],"description":"Official supplier count used in all reporting: the number of active suppliers, meaning vendors in account group ZSTR (strategic) or ZSTD (standard). Probationary vendors (ZPRB) are excluded by procurement policy. Canonical implementation: FINANCE_ENRICHED_SV metric vendors.active_supplier_count. The Procurement view metric vendor_record_count counts all vendor master records and is an operational variant, not the official count.","formula":"COUNT(DISTINCT LIFNR) WHERE KTOKK IN (ZSTR, ZSTD)","exclusions":["KTOKK = ZPRB (probationary)"],"formulaSource":"BUSINESS_ONTOLOGY.SAP.LFA1"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Vendor Record Count","domainName":"Procurement","itemKind":"METRIC","scope":"Procurement operations","synonyms":["Vendor master record count"],"description":"Operational variant of Supplier Count: every vendor record on file, including probationary vendors. Use only for vendor master data maintenance, never as the supplier count. Implemented by PROCUREMENT_ENRICHED_SV metric vendors.vendor_record_count.","formula":"COUNT(DISTINCT LIFNR)","formulaSource":"BUSINESS_ONTOLOGY.SAP.LFA1"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"On-Time Delivery Rate","domainName":"Procurement","itemKind":"METRIC","synonyms":["OTD","On-time delivery","Delivery performance"],"description":"Official on-time delivery rate: percent of delivered shipments (status D) whose actual goods issue date is on or before the planned delivery date. Canonical implementation: PROCUREMENT_ENRICHED_SV metric shipments.operational_otd_rate. The carrier self-reported ratio (carrier_otd_rate, OTRAT) is not the official measure.","formula":"100 * COUNT(WADAT <= LFDAT) / COUNT(*) WHERE STATU = D","formulaSource":"BUSINESS_ONTOLOGY.SAP.LIKP"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Carrier Reported On-Time Rate","domainName":"Procurement","itemKind":"METRIC","scope":"Carrier scorecard","synonyms":["OTRAT","Carrier OTD"],"description":"Variant of On-Time Delivery Rate: average on-time ratio self-reported by carriers. Useful for carrier negotiations only; not the official delivery performance. Implemented by PROCUREMENT_ENRICHED_SV metric carriers.carrier_otd_rate.","formula":"AVG(OTRAT) * 100","formulaSource":"BUSINESS_ONTOLOGY.SAP.LFA2"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"BOM Cost Rollup","domainName":"Procurement","itemKind":"METRIC","synonyms":["Unit cost to build","Cost to make","Material cost per unit","Product cost"],"description":"Official cost to build one unit of an assembly: sum over every purchased component at every BOM level of extended quantity times component standard price. This is the unit cost for all margin, profit, and pricing decisions. The standard price STPRS stored on an assembly is a planning price, not its cost. Canonical implementation: PROCUREMENT_ENRICHED_SV metric bom.bom_material_cost grouped by bom.assembly_id.","formula":"SUM(extended_qty * component STPRS) over leaf BOM components, per assembly","formulaSource":"BUSINESS_ONTOLOGY.SAP.BOM_EXPLOSION_VIEW"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Procurement Spend","domainName":"Procurement","itemKind":"METRIC","synonyms":["Purchase spend","Spend"],"description":"Total net value of purchase order lines (EKPO NETWR). Canonical implementation: PROCUREMENT_ENRICHED_SV metric purchase_orders.procurement_spend.","formula":"SUM(NETWR)","formulaSource":"BUSINESS_ONTOLOGY.SAP.EKPO"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Vendor Account Group","domainName":"Procurement","itemKind":"TERM","synonyms":["KTOKK","Vendor type"],"description":"Code field KTOKK on the vendor master that classifies suppliers: ZSTR = strategic partner, ZSTD = standard vendor, ZPRB = probationary. The full code list and the EXCLUDE_FROM_ACTIVE_COUNT flag live in reference table T077K; new codes are added there, not here."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Material Group","domainName":"Procurement","itemKind":"TERM","synonyms":["MATKL","Material category"],"description":"Code field MATKL that classifies materials: 043 Electronics, 044 Chemicals, 045 Metals, 046 Packaging, 047 Raw Materials, 048 Assembly. The full code list lives in reference table T023T."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Probationary Vendor Exclusion","domainName":"Procurement","itemKind":"POLICY_CONCEPT","description":"Procurement policy: vendors in a probationary account group (ZPRB, flagged EXCLUDE_FROM_ACTIVE_COUNT in T077K) are not active suppliers. They are excluded from supplier counts and supplier KPIs until promoted."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"BOM Input Protection","domainName":"Procurement","itemKind":"POLICY_CONCEPT","description":"Procurement policy: a material that is a component, at any BOM level, of an assembly we sell is a production input and must not be cut to reduce spend. Only materials that appear in no sold assembly BOM are discretionary spend."}');

-- ---------------------------------------------------------------- Finance & Controlling nodes
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"AP Line Item","domainName":"Finance & Controlling","itemKind":"ENTITY","synonyms":["Accounts payable posting","Vendor invoice line"],"description":"An accounts payable accounting line (BSEG) for a vendor invoice or credit memo, posted to a GL account with a posting key that sets its direction."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Cost Posting","domainName":"Finance & Controlling","itemKind":"ENTITY","synonyms":["Cost allocation","Controlling posting"],"description":"A controlling cost posting (COEP) allocated to a cost object such as a manufacturing cost center."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"COGS Raw Materials","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Cost of goods sold","COGS","Raw material COGS"],"description":"Official cost of goods sold for raw materials: AP postings on GL 0040100000, with vendor invoices (posting key 31) added and credit memos (posting key 34) subtracted. Canonical implementation: FINANCE_ENRICHED_SV metric ap_lines.cogs_raw_materials.","formula":"SUM(DMBTR if BSCHL=31, -DMBTR if BSCHL=34) WHERE HKONT = 0040100000","formulaSource":"BUSINESS_ONTOLOGY.SAP.BSEG"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"COGS Freight","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Freight cost of goods sold","Net freight COGS"],"description":"Freight cost of goods sold: AP postings on GL 0040200000, invoices minus credit memos. Canonical implementation: FINANCE_ENRICHED_SV metric ap_lines.cogs_freight.","formula":"SUM(signed DMBTR) WHERE HKONT = 0040200000","formulaSource":"BUSINESS_ONTOLOGY.SAP.BSEG"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Cost Center Total","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Allocated cost","Manufacturing cost"],"description":"Total cost posted to a cost object (OBJNR), for example KS-MFG-US for US Manufacturing. Canonical implementation: FINANCE_ENRICHED_SV metric cost_postings.total_posted_cost filtered by cost_object.","formula":"SUM(WRTBTR) WHERE OBJNR = cost object","formulaSource":"BUSINESS_ONTOLOGY.SAP.COEP"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Product Gross Margin","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Gross margin","Product margin"],"description":"Gross margin of an assembly: Revenue (net of customer discounts) minus BOM Cost Rollup times units sold. Revenue comes from the Sales view (net_revenue) and unit cost from the Procurement view (bom_material_cost); query both and combine. Never use the assembly standard price STPRS as cost, and never use gross bookings as revenue.","formula":"Revenue - (BOM Cost Rollup * units sold), per assembly"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Customer Profit","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Customer profitability","Profit contribution"],"description":"Profit contributed by a customer after material costs: Revenue (net of discounts) for that customer minus BOM Cost Rollup times units sold to that customer, summed over the assemblies they bought. Combines Sales (net_revenue and units_sold by customer and product) with Procurement (bom_material_cost by assembly).","formula":"SUM over products(Revenue - BOM Cost Rollup * units), per customer"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Break-even Discount","domainName":"Finance & Controlling","itemKind":"METRIC","synonyms":["Maximum discount","Discount floor"],"description":"Largest discount off list price (PR00) before the unit price falls below the cost to build: 1 minus BOM Cost Rollup divided by list price. List price comes from the Sales view (list_price); unit cost from the Procurement view (bom_material_cost).","formula":"1 - BOM Cost Rollup / list price"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Posting Key","domainName":"Finance & Controlling","itemKind":"TERM","synonyms":["BSCHL"],"description":"Code field BSCHL that sets the direction of an AP line: 31 = vendor invoice (adds cost), 34 = vendor credit memo (reduces cost)."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"GL Account","domainName":"Finance & Controlling","itemKind":"TERM","synonyms":["HKONT","General ledger account"],"description":"Code field HKONT: 0040100000 = COGS Raw Materials, 0040200000 = COGS Freight, 0021100000 = Accounts Payable."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Cost Object","domainName":"Finance & Controlling","itemKind":"TERM","synonyms":["OBJNR","Cost center"],"description":"Code field OBJNR: KS-MFG-US = US Manufacturing, KS-MFG-EU = EU Manufacturing, KS-MFG-AP = APAC Manufacturing, KS-LOG = Logistics, KS-QA = Quality Assurance."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Credit Memo Sign Rule","domainName":"Finance & Controlling","itemKind":"POLICY_CONCEPT","description":"Accounting policy: a vendor credit memo (posting key 34) reverses part of a vendor invoice (posting key 31), so it must be subtracted from every cost and COGS total. Summing raw amounts overstates cost."}');

-- ---------------------------------------------------------------- Sales & Distribution nodes
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Sales Order","domainName":"Sales & Distribution","itemKind":"ENTITY","synonyms":["Order","Sales order line"],"description":"A customer order line for an assembly (VBAP). Its value NETWR is the order value before customer discounts."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Customer","domainName":"Sales & Distribution","itemKind":"ENTITY","synonyms":["Account","Client"],"description":"A company that buys our assemblies, identified by KUNNR."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Pricing Condition","domainName":"Sales & Distribution","itemKind":"ENTITY","synonyms":["Price condition"],"description":"A pricing record on a sales order (KONV): list price, customer discount, or surcharge, distinguished by condition type."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Revenue","domainName":"Sales & Distribution","itemKind":"METRIC","synonyms":["Net revenue","Net sales","Sales revenue"],"description":"Official revenue for all reporting, margin, profit, and risk analysis: order value net of customer discounts (condition type K007). Canonical implementation: SALES_ENRICHED_SV derived metric net_revenue. Gross Bookings (order value before discounts, the Sales view metric gross_bookings) is a sales pipeline variant and is not revenue.","formula":"SUM(VBAP.NETWR) - SUM(ABS(KONV.KWERT)) WHERE KSCHL = K007","exclusions":["Freight surcharges (KF00) are not discounts"],"formulaSource":"BUSINESS_ONTOLOGY.SAP.VBAP"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Gross Bookings","domainName":"Sales & Distribution","itemKind":"METRIC","scope":"Sales pipeline","synonyms":["Bookings","Order value"],"description":"Variant of Revenue used by the Sales team for pipeline and quota: total order value before customer discounts. Not official revenue. Implemented by SALES_ENRICHED_SV metric sales_items.gross_bookings.","formula":"SUM(VBAP.NETWR)","formulaSource":"BUSINESS_ONTOLOGY.SAP.VBAP"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Customer Discounts","domainName":"Sales & Distribution","itemKind":"METRIC","synonyms":["Discount leakage","Revenue lost to discounts"],"description":"Value of customer discounts granted: pricing conditions of type K007 only. Freight surcharges (KF00) are not discounts. Canonical implementation: SALES_ENRICHED_SV metric pricing.customer_discounts.","formula":"SUM(ABS(KWERT)) WHERE KSCHL = K007","exclusions":["KSCHL = KF00 (freight surcharge)"],"formulaSource":"BUSINESS_ONTOLOGY.SAP.KONV"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Revenue at Risk","domainName":"Sales & Distribution","itemKind":"METRIC","synonyms":["Supplier disruption impact","Exposed revenue"],"description":"Revenue (net of discounts) exposed when a supplier cannot deliver: find the materials the supplier provides (Procurement purchase orders), find every sold assembly whose BOM contains any of those materials at any level (Procurement bom, which is already fully exploded), then sum Revenue for those assemblies (Sales net_revenue by product).","formula":"SUM(Revenue) for assemblies whose BOM contains a material supplied by the supplier"}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Condition Type","domainName":"Sales & Distribution","itemKind":"TERM","synonyms":["KSCHL"],"description":"Code field KSCHL on pricing conditions: PR00 = list price, K007 = customer discount, KF00 = freight surcharge."}');
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Sales Organization","domainName":"Sales & Distribution","itemKind":"TERM","synonyms":["VKORG","Sales org"],"description":"Code field VKORG: 1000 = Americas, 2000 = EMEA, 3000 = APAC."}');

-- Approve: pass the 39 termIds returned above (scoped form; never the no-arg form)
-- SELECT SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('["<termId>", ...]');

-- ---------------------------------------------------------------- Relationships (49)
-- Entity structure
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Assembly','Procurement.Bill of Materials','HAS_PART');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Bill of Materials','Procurement.Material','HAS_PART');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Supplier','Procurement.Material','RELATED_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Purchase Order','Procurement.Supplier','RELATED_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Purchase Order','Procurement.Material','RELATED_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Carrier','Procurement.Shipment','RELATED_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Inspection Lot','Procurement.Material','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Sales Order','Procurement.Assembly','RELATED_TO');          -- cross-domain
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Sales Order','Sales & Distribution.Customer','RELATED_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Sales Order','Sales & Distribution.Pricing Condition','HAS_PART');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Purchase Order','Finance & Controlling.AP Line Item','DERIVES');      -- cross-domain
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.AP Line Item','Finance & Controlling.Cost Posting','DERIVES');
-- Metrics: what they measure, canonical vs variant, derivation chains
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Supplier Count','Procurement.Supplier','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Supplier Count','Procurement.Vendor Record Count','HAS_VARIANT');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.On-Time Delivery Rate','Procurement.Shipment','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.On-Time Delivery Rate','Procurement.Carrier Reported On-Time Rate','HAS_VARIANT');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue','Sales & Distribution.Sales Order','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue','Sales & Distribution.Gross Bookings','HAS_VARIANT');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Gross Bookings','Sales & Distribution.Revenue','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Customer Discounts','Sales & Distribution.Revenue','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.BOM Cost Rollup','Procurement.Assembly','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Bill of Materials','Procurement.BOM Cost Rollup','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue','Finance & Controlling.Product Gross Margin','DERIVES');   -- cross-domain
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.BOM Cost Rollup','Finance & Controlling.Product Gross Margin','DERIVES');  -- cross-domain
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Product Gross Margin','Procurement.Assembly','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue','Finance & Controlling.Customer Profit','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.BOM Cost Rollup','Finance & Controlling.Customer Profit','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Customer Profit','Sales & Distribution.Customer','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.BOM Cost Rollup','Finance & Controlling.Break-even Discount','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Pricing Condition','Finance & Controlling.Break-even Discount','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue','Sales & Distribution.Revenue at Risk','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Bill of Materials','Sales & Distribution.Revenue at Risk','DERIVES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Revenue at Risk','Procurement.Supplier','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.COGS Raw Materials','Finance & Controlling.AP Line Item','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.COGS Freight','Finance & Controlling.AP Line Item','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Cost Center Total','Finance & Controlling.Cost Posting','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Procurement Spend','Procurement.Purchase Order','MEASURES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Customer Discounts','Sales & Distribution.Pricing Condition','MEASURES');
-- Code terms classify entities; policies apply to metrics
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Vendor Account Group','Procurement.Supplier','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Material Group','Procurement.Material','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Condition Type','Sales & Distribution.Pricing Condition','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Sales & Distribution.Sales Organization','Sales & Distribution.Sales Order','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Posting Key','Finance & Controlling.AP Line Item','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.GL Account','Finance & Controlling.AP Line Item','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Cost Object','Finance & Controlling.Cost Posting','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Probationary Vendor Exclusion','Procurement.Supplier Count','APPLIES_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Credit Memo Sign Rule','Finance & Controlling.COGS Raw Materials','APPLIES_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Finance & Controlling.Credit Memo Sign Rule','Finance & Controlling.COGS Freight','APPLIES_TO');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.BOM Input Protection','Procurement.Procurement Spend','APPLIES_TO');

-- ---------------------------------------------------------------- Added for benchmark Q19 (company vocabulary)
SELECT SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Tier A Supplier","domainName":"Procurement","itemKind":"TERM","synonyms":["Tier A suppliers","Tier A vendor","Tier-A supplier"],"description":"Company term for our top supplier tier: a supplier in vendor account group ZSTR (strategic partner). Tier A does not include standard (ZSTD) or probationary (ZPRB) vendors. Spend with Tier A suppliers = Procurement Spend (PROCUREMENT_ENRICHED_SV purchase_orders.procurement_spend) filtered to vendors.account_group = ZSTR."}');
-- SELECT SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('["<termId>"]');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Vendor Account Group','Procurement.Tier A Supplier','CLASSIFIES');
SELECT SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Tier A Supplier','Procurement.Supplier','IS_A');
BON_FILE_07_ONTOLOGY_SQL

cat > 'sql/08_representations.sql' <<'BON_FILE_08_REPRESENTATIONS_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 08: Representations (bind meaning to the assets that implement it)
-- 43 representations:
--   IMPLEMENTS            : metric -> the exact SV metric (field-level binding, verified working)
--   RELATED_SEMANTIC_VIEW : cross-SV metric -> every SV that supplies one of its inputs
--   REPRESENTS            : entity -> table/view
--   DESCRIBES             : code-mapping term -> column
--   REFERENCE_DATA        : code-mapping term -> code table (T077K, T023T)
-- Verified: owners/stewards cannot be set via API (patch schema rejects `owners`);
-- stewardship is recorded in domain descriptions.
-- =====================================================================
-- Helper: SV sub-component ref = {"refType":"SEMANTIC_VIEW","fqn":<sv>,"subObjectType":"METRIC","entityQualifier":<logical table>,"subObjectName":<metric>}

-- ------------------------------------------------ Canonical metrics -> implementing SV metric
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Supplier Count', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"VENDORS","subObjectName":"ACTIVE_SUPPLIER_COUNT"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Vendor Record Count', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"VENDORS","subObjectName":"VENDOR_RECORD_COUNT"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.On-Time Delivery Rate', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"SHIPMENTS","subObjectName":"OPERATIONAL_OTD_RATE"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Carrier Reported On-Time Rate', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"CARRIERS","subObjectName":"CARRIER_OTD_RATE"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.BOM Cost Rollup', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"BOM","subObjectName":"BOM_MATERIAL_COST"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Procurement Spend', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"PURCHASE_ORDERS","subObjectName":"PROCUREMENT_SPEND"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Revenue', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","subObjectType":"DERIVED_METRIC","subObjectName":"NET_REVENUE"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Gross Bookings', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"SALES_ITEMS","subObjectName":"GROSS_BOOKINGS"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Customer Discounts', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"PRICING","subObjectName":"CUSTOMER_DISCOUNTS"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.COGS Raw Materials', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"AP_LINES","subObjectName":"COGS_RAW_MATERIALS"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.COGS Freight', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"AP_LINES","subObjectName":"COGS_FREIGHT"}', 'IMPLEMENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Cost Center Total', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV","subObjectType":"METRIC","entityQualifier":"COST_POSTINGS","subObjectName":"TOTAL_POSTED_COST"}', 'IMPLEMENTS');

-- ------------------------------------------------ Cross-SV metrics -> each contributing SV
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Product Gross Margin', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","objectName":"SALES_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Product Gross Margin', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","objectName":"PROCUREMENT_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Customer Profit', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","objectName":"SALES_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Customer Profit', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","objectName":"PROCUREMENT_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Break-even Discount', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","objectName":"SALES_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Break-even Discount', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","objectName":"PROCUREMENT_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Revenue at Risk', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV","objectName":"SALES_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Revenue at Risk', '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV","objectName":"PROCUREMENT_ENRICHED_SV"}', 'RELATED_SEMANTIC_VIEW');

-- ------------------------------------------------ Entities -> tables / views
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Supplier', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.LFA1","objectName":"LFA1"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Material', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.MARA","objectName":"MARA"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Assembly', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.MARA","objectName":"MARA"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Bill of Materials', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.STPO","objectName":"STPO"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Bill of Materials', '{"refType":"VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.BOM_EXPLOSION_VIEW","objectName":"BOM_EXPLOSION_VIEW"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Purchase Order', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.EKPO","objectName":"EKPO"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Shipment', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.LIKP","objectName":"LIKP"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Carrier', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.LFA2","objectName":"LFA2"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Inspection Lot', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.QALS","objectName":"QALS"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Sales Order', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.VBAP","objectName":"VBAP"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Customer', '{"refType":"VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.CUSTOMERS_VIEW","objectName":"CUSTOMERS_VIEW"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Pricing Condition', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.KONV","objectName":"KONV"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.AP Line Item', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.BSEG","objectName":"BSEG"}', 'REPRESENTS');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Cost Posting', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.COEP","objectName":"COEP"}', 'REPRESENTS');

-- ------------------------------------------------ Code-mapping terms -> columns + code tables
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Vendor Account Group', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.LFA1","dimensionName":"KTOKK"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Vendor Account Group', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.T077K","objectName":"T077K"}', 'REFERENCE_DATA');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Material Group', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.MARA","dimensionName":"MATKL"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.Material Group', '{"refType":"TABLE","fqn":"BUSINESS_ONTOLOGY.SAP.T023T","objectName":"T023T"}', 'REFERENCE_DATA');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Condition Type', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.KONV","dimensionName":"KSCHL"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Sales & Distribution.Sales Organization', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.VBAP","dimensionName":"VKORG"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Posting Key', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.BSEG","dimensionName":"BSCHL"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.GL Account', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.BSEG","dimensionName":"HKONT"}', 'DESCRIBES');
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Finance & Controlling.Cost Object', '{"refType":"COLUMN","fqn":"BUSINESS_ONTOLOGY.SAP.COEP","dimensionName":"OBJNR"}', 'DESCRIBES');
BON_FILE_08_REPRESENTATIONS_SQL

cat > 'sql/09_agents.sql' <<'BON_FILE_09_AGENTS_SQL'
-- Copyright 2026 Snowflake Inc.
-- SPDX-License-Identifier: Apache-2.0
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

-- =====================================================================
-- Business Ontology demo, 09: Agent matrix
-- Every agent: same model (auto), same budget (150 s / 40k tokens), same
-- response text, same domain tool descriptions. The ONLY difference between
-- an arm and its "+ BON" twin is the business_ontology tool and its 2-step instruction.
--
--   Arm A  BARE_AGENT        3 BARE SVs
--   Arm B  ENRICHED_AGENT    3 ENRICHED SVs
--   Arm C  BON_AGENT         3 ENRICHED SVs + Business Ontology      (BON uplift = C - B)
--   Consistency pairs (do two teams get the same answer?)
--          FINANCE_ENRICHED_AGENT / FINANCE_BON_AGENT   Finance + Procurement ENRICHED SVs
--          SALES_ENRICHED_AGENT   / SALES_BON_AGENT     Sales + Procurement ENRICHED SVs
--   Finance sees active_supplier_count (14); Sales only sees vendor_record_count (15).
--   Without BON they disagree; with BON both should answer 14.
--
-- After creating, DESCRIBE AGENT and confirm agent_spec contains
--   "EnableSnowscopeBusinessOntologySearch":true, "type":"snowscope_search", "corpus":"businessOntology"
-- (CREATE AGENT does not validate these values.)
-- Terms were first observed as searchable approximately 5 to 14 hours after the final ontology write.
-- These are observation times, not guaranteed indexing durations. Confirm readiness with search checks.
-- =====================================================================

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.BARE_AGENT
  COMMENT = 'benchmark arm A: 3 BARE domain semantic views, no Business Ontology'
  PROFILE = '{"display_name": "SAP Assistant (bare SVs)"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
  orchestration: |
    Data lives in three domain tools. Each tool queries one domain only and
    cannot join to another domain, so for questions that span domains, query
    each relevant tool and combine the results yourself.
    - query_procurement: vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials
    - query_finance: accounts payable postings, COGS, cost allocations by cost object
    - query_sales: sales orders, pricing conditions, discounts, customers
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_finance
      description: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_sales
      description: Sales domain data - sales orders, pricing conditions, discounts, customers.
tool_resources:
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_BARE_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_finance:
    semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_BARE_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_sales:
    semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_BARE_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.ENRICHED_AGENT
  COMMENT = 'benchmark arm B: 3 ENRICHED domain semantic views, no Business Ontology'
  PROFILE = '{"display_name": "SAP Assistant (enriched SVs)"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
  orchestration: |
    Data lives in three domain tools. Each tool queries one domain only and
    cannot join to another domain, so for questions that span domains, query
    each relevant tool and combine the results yourself.
    - query_procurement: vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials
    - query_finance: accounts payable postings, COGS, cost allocations by cost object
    - query_sales: sales orders, pricing conditions, discounts, customers
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_finance
      description: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_sales
      description: Sales domain data - sales orders, pricing conditions, discounts, customers.
tool_resources:
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_finance:
    semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_sales:
    semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.BON_AGENT
  COMMENT = 'benchmark arm C: 3 ENRICHED domain semantic views + native Business Ontology search'
  PROFILE = '{"display_name": "SAP Assistant (enriched SVs + Business Ontology)"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
experimental:
  EnableSnowscopeBusinessOntologySearch: true
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
    When you used a governed Business Ontology definition, name the term and
    the semantic view metric that implements it.
  orchestration: |
    Data lives in three domain tools. Each tool queries one domain only and
    cannot join to another domain, so for questions that span domains, query
    each relevant tool and combine the results yourself.
    - query_procurement: vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials
    - query_finance: accounts payable postings, COGS, cost allocations by cost object
    - query_sales: sales orders, pricing conditions, discounts, customers

    Before querying data, call business_ontology to look up the governed
    definition of each business term in the question. Prefer terms from the
    Procurement, Finance & Controlling, and Sales & Distribution domains. When
    the ontology names a canonical metric and the semantic view metric that
    implements it, use that metric rather than a similarly named variant, and
    follow any policy that applies to it. If the question only asks what
    something means, answer from the ontology without querying data.
tools:
  - tool_spec:
      type: snowscope_search
      name: business_ontology
      description: Governed business definitions - canonical metrics and their implementing semantic view metrics, scoped variants, business policies, code meanings, and how concepts relate across Procurement, Finance and Sales.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_finance
      description: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_sales
      description: Sales domain data - sales orders, pricing conditions, discounts, customers.
tool_resources:
  business_ontology:
    corpus: businessOntology
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_finance:
    semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_sales:
    semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

-- ------------------------------------------------ Consistency pairs
CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_AGENT
  COMMENT = 'consistency pair: Finance team agent (Finance + Procurement enriched SVs), no BON'
  PROFILE = '{"display_name": "Finance Assistant"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
  orchestration: |
    You support the Finance team. Data lives in the domain tools below. Each
    tool queries one domain only and cannot join to another domain, so for
    questions that span domains, query each relevant tool and combine the
    results yourself.
    - query_finance: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
    - query_procurement: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_finance
      description: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tool_resources:
  query_finance:
    semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.FINANCE_BON_AGENT
  COMMENT = 'consistency pair: Finance team agent (Finance + Procurement enriched SVs) + BON'
  PROFILE = '{"display_name": "Finance Assistant + BON"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
experimental:
  EnableSnowscopeBusinessOntologySearch: true
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
    When you used a governed Business Ontology definition, name the term and
    the semantic view metric that implements it.
  orchestration: |
    You support the Finance team. Data lives in the domain tools below. Each
    tool queries one domain only and cannot join to another domain, so for
    questions that span domains, query each relevant tool and combine the
    results yourself.
    - query_finance: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
    - query_procurement: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
    Before querying data, call business_ontology to look up the governed
    definition of each business term in the question. Prefer terms from the
    Procurement, Finance & Controlling, and Sales & Distribution domains. When
    the ontology names a canonical metric and the semantic view metric that
    implements it, use that metric rather than a similarly named variant, and
    follow any policy that applies to it. If the ontology names a semantic view
    metric this agent does not have, compute the same definition with the
    tools available. If the question only asks what something means, answer
    from the ontology without querying data.
tools:
  - tool_spec:
      type: snowscope_search
      name: business_ontology
      description: Governed business definitions - canonical metrics and their implementing semantic view metrics, scoped variants, business policies, code meanings, and how concepts relate across Procurement, Finance and Sales.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_finance
      description: Finance domain data - accounts payable postings, cost of goods sold, cost allocations by cost object.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tool_resources:
  business_ontology:
    corpus: businessOntology
  query_finance:
    semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_AGENT
  COMMENT = 'consistency pair: Sales team agent (Sales + Procurement enriched SVs), no BON'
  PROFILE = '{"display_name": "Sales Assistant"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
  orchestration: |
    You support the Sales team. Data lives in the domain tools below. Each
    tool queries one domain only and cannot join to another domain, so for
    questions that span domains, query each relevant tool and combine the
    results yourself.
    - query_sales: Sales domain data - sales orders, pricing conditions, discounts, customers.
    - query_procurement: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_sales
      description: Sales domain data - sales orders, pricing conditions, discounts, customers.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tool_resources:
  query_sales:
    semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;

CREATE OR REPLACE AGENT BUSINESS_ONTOLOGY.SAP.SALES_BON_AGENT
  COMMENT = 'consistency pair: Sales team agent (Sales + Procurement enriched SVs) + BON'
  PROFILE = '{"display_name": "Sales Assistant + BON"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto
experimental:
  EnableSnowscopeBusinessOntologySearch: true
orchestration:
  budget:
    seconds: 150
    tokens: 40000
instructions:
  response: |
    You are an enterprise analytics assistant for SAP supply chain data.
    Answer precisely. State the final answer as a clear number or list first,
    then briefly explain how it was computed and which data was used.
    When you used a governed Business Ontology definition, name the term and
    the semantic view metric that implements it.
  orchestration: |
    You support the Sales team. Data lives in the domain tools below. Each
    tool queries one domain only and cannot join to another domain, so for
    questions that span domains, query each relevant tool and combine the
    results yourself.
    - query_sales: Sales domain data - sales orders, pricing conditions, discounts, customers.
    - query_procurement: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
    Before querying data, call business_ontology to look up the governed
    definition of each business term in the question. Prefer terms from the
    Procurement, Finance & Controlling, and Sales & Distribution domains. When
    the ontology names a canonical metric and the semantic view metric that
    implements it, use that metric rather than a similarly named variant, and
    follow any policy that applies to it. If the ontology names a semantic view
    metric this agent does not have, compute the same definition with the
    tools available. If the question only asks what something means, answer
    from the ontology without querying data.
tools:
  - tool_spec:
      type: snowscope_search
      name: business_ontology
      description: Governed business definitions - canonical metrics and their implementing semantic view metrics, scoped variants, business policies, code meanings, and how concepts relate across Procurement, Finance and Sales.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_sales
      description: Sales domain data - sales orders, pricing conditions, discounts, customers.
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: query_procurement
      description: Procurement domain data - vendors, materials, purchase orders, shipments, carriers, inspections, bill of materials.
tool_resources:
  business_ontology:
    corpus: businessOntology
  query_sales:
    semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
  query_procurement:
    semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV
    execution_environment: {type: warehouse, warehouse: BUSINESS_ONTOLOGY_WH, query_timeout: 120}
$$;
BON_FILE_09_AGENTS_SQL

cat > 'benchmark/run_benchmark.py' <<'BON_FILE_10_RUN_BENCHMARK_PY'
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Business Ontology demo benchmark harness.

Measures Business Ontology uplift as arm C (enriched SVs + BON) minus arm B
(enriched SVs alone). Same model, budget,
instructions, and SVs across B and C: the only difference is the BON tool.

Value scorecard (maps to Business Ontology positioning):
  canonical choice       Tier 2: pick the governed metric among conflicting SV metrics
  cross-domain           Tier 3: compose meaning across Sales/Finance/Procurement SVs
  governed meaning       Tier 4: explain the business definition, policy, implementation
  consistency            same question, two teams' agents, same answer?
  baseline fairness      Tier 1: enriched SVs already handle single-SV rules (BON adds ~0)
  accuracy stability     answers identical across repeated runs
  cost                   latency and tool calls per answer
  traceability           answer names the governed term and its implementing SV metric

Usage:
  SNOWFLAKE_CONNECTION_NAME=<conn> python run_benchmark.py            # full run
  SNOWFLAKE_CONNECTION_NAME=<conn> python run_benchmark.py --runs 1 --qids Q06,Q07
  SNOWFLAKE_CONNECTION_NAME=<conn> python run_benchmark.py --check-index
"""
import argparse
import json
import os
import re
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import snowflake.connector

DATABASE = os.environ.get("SNOWFLAKE_DATABASE", "BUSINESS_ONTOLOGY")
SCHEMA_NAME = os.environ.get("SNOWFLAKE_SCHEMA", "SAP")
SCHEMA = f"{DATABASE}.{SCHEMA_NAME}"
ARMS = {"B": "ENRICHED_AGENT", "C": "BON_AGENT"}
PAIRS = {  # Same question asked through two teams' agents
    "no_bon": ("FINANCE_ENRICHED_AGENT", "SALES_ENRICHED_AGENT"),
    "bon": ("FINANCE_BON_AGENT", "SALES_BON_AGENT"),
}
PAIR_QIDS = ["Q06", "Q07", "Q09"]
JUDGE_MODEL = "claude-sonnet-4-5"
# Index check: a new node that must be searchable, and nodes from the retired SAP * domains that must not be.
INDEX_PROBES = [("supplier count active suppliers", "Procurement.Supplier Count"),
                ("revenue net of discounts", "Sales & Distribution.Revenue"),
                ("tier a suppliers", "Procurement.Tier A Supplier")]
RETIRED_DOMAINS = ("SAP Purchasing.", "SAP Finance.", "SAP Sales.")


def connect():
    # SNOWFLAKE_ROLE / SNOWFLAKE_WAREHOUSE override the connection's defaults, e.g. when its default role is read-only.
    overrides = {k: os.environ[e] for k, e in (("role", "SNOWFLAKE_ROLE"), ("warehouse", "SNOWFLAKE_WAREHOUSE")) if os.environ.get(e)}
    return snowflake.connector.connect(connection_name=os.environ.get("SNOWFLAKE_CONNECTION_NAME", "default"), **overrides)


def check_index():
    """Return (ready, report). Ready when new nodes are found and retired SAP * domain nodes are gone."""
    ready, lines = True, []
    # Search the same connection the benchmark runs on.
    conn_args = ["-c", os.environ["SNOWFLAKE_CONNECTION_NAME"]] if os.environ.get("SNOWFLAKE_CONNECTION_NAME") else []
    for query, expected in INDEX_PROBES:
        out = subprocess.run(["cortex", "search", "object", query, "--types=business-ontology", *conn_args],
                             capture_output=True, text=True, timeout=120).stdout
        hits = re.findall(r"\d+\. ([^\n(]+) \(", out)
        found = expected in [h.strip() for h in hits]
        stale = [h.strip() for h in hits if h.strip().startswith(RETIRED_DOMAINS)]
        ready &= found and not stale
        lines.append(f"  '{query}': expected={'found' if found else 'MISSING'}, retired-domain hits={stale or 'none'}")
    return ready, "\n".join(lines)


def run_agent(conn, agent, question):
    body = json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]})
    t0 = time.time()
    cur = conn.cursor()
    try:
        cur.execute("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(%s, %s)", (f"{SCHEMA}.{agent}", body))
        resp = json.loads(cur.fetchone()[0])
        err = None
    except Exception as e:  # keep the run; a failure is a scored wrong answer
        resp, err = {"content": []}, str(e)[:500]
    finally:
        cur.close()
    latency = round(time.time() - t0, 1)
    content = resp.get("content", [])
    tools = [c["tool_use"]["name"] for c in content if c.get("type") == "tool_use"]
    texts = [c.get("text", "") for c in content if c.get("type") == "text"]
    answer = "\n".join(t for t in texts if t.strip())
    return {"answer": answer or (err or ""), "tools": tools, "latency_s": latency, "error": err}


JUDGE_PROMPT = """You grade an analytics agent's answer against ground truth.
Question: {q}
Expected: {expected}
Grading rule: {rule}
Plausible wrong answer to watch for: {wrong}
Agent answer:
<<<
{answer}
>>>
Return only JSON with keys:
  "headline_value": the single final number the agent gave as its answer (number, or null if none). If the agent mentions several numbers but clearly states which one is the official or recommended answer, use that one,
  "hedged": true only if the agent offers two or more competing answers AND never states which one is official or recommended, leaving the choice to the user. Mentioning an alternative after clearly committing to one answer is NOT hedging,
  "correct": true/false applying the grading rule (for numeric rules, compare the headline value, not side numbers). A hedged answer is NOT correct, even if one of its options matches,
  "fell_for_wrong": true if the agent's headline answer matches the plausible wrong answer,
  "names_governed_term": true if the answer names a governed business term AND the semantic view metric that implements it,
  "reason": one short sentence."""


def parse_judge(raw):
    """AI_COMPLETE may return the text JSON-encoded and wrapped in a ```json fence."""
    text = raw
    try:
        decoded = json.loads(raw)
        if isinstance(decoded, str):
            text = decoded
        elif isinstance(decoded, dict):
            return decoded
    except (TypeError, ValueError):
        pass
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except ValueError:
            pass
    return {"correct": False, "reason": "unparseable judge output: " + str(raw)[:200]}


def judge(conn, gt, answer):
    expected = gt["EXPECTED_VALUE"] if gt["EXPECTED_VALUE"] is not None else gt["GRADING_RULE"]
    prompt = JUDGE_PROMPT.format(q=gt["QUESTION"], expected=expected, rule=gt["GRADING_RULE"],
                                 wrong=gt["PLAUSIBLE_WRONG"], answer=answer[:6000])
    cur = conn.cursor()
    try:
        cur.execute("SELECT AI_COMPLETE(%s, %s)", (JUDGE_MODEL, prompt))
        raw = cur.fetchone()[0]
    finally:
        cur.close()
    v = parse_judge(raw)
    # Deterministic check for plain numeric questions: the judge only extracts the headline number.
    if gt["GRADING_RULE"] == "numeric" and gt["EXPECTED_VALUE"] is not None and v.get("headline_value") is not None:
        try:
            exp, got = float(gt["EXPECTED_VALUE"]), float(v["headline_value"])
            tol = float(gt["TOLERANCE_PCT"] or 0) / 100 * abs(exp)
            v["correct"] = abs(got - exp) <= max(tol, 0.051 if exp < 100 else 0.5) and not v.get("hedged")
        except (TypeError, ValueError):
            pass
    return v


def load_questions(conn, qids):
    cur = conn.cursor(snowflake.connector.DictCursor)
    cur.execute(f"""SELECT q.QID, q.TIER, q.TIER_NAME, q.VALUE_PILLAR, q.QUESTION, g.EXPECTED_VALUE,
                    g.TOLERANCE_PCT, g.CANONICAL_METRIC, g.PLAUSIBLE_WRONG, g.GRADING_RULE
                    FROM {SCHEMA}.BENCHMARK_QUESTIONS q JOIN {SCHEMA}.BENCHMARK_GROUND_TRUTH g USING (QID) ORDER BY QID""")
    rows = cur.fetchall()
    return [r for r in rows if not qids or r["QID"] in qids]


def ensure_results_table(conn):
    conn.cursor().execute(f"""CREATE TABLE IF NOT EXISTS {SCHEMA}.BENCHMARK_RESULTS (
        RUN_ID STRING, RUN_TS TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(), EXPERIMENT STRING, ARM STRING,
        AGENT STRING, QID STRING, RUN_NO INT, CORRECT BOOLEAN, FELL_FOR_WRONG BOOLEAN,
        NAMES_GOVERNED_TERM BOOLEAN, HEADLINE_VALUE FLOAT, LATENCY_S FLOAT, TOOL_CALLS INT,
        USED_BON BOOLEAN, ANSWER STRING, JUDGE_REASON STRING, ERROR STRING)""")
    conn.cursor().execute(f"ALTER TABLE {SCHEMA}.BENCHMARK_RESULTS ADD COLUMN IF NOT EXISTS HEDGED BOOLEAN")


def save(conn, run_id, rows):
    cur = conn.cursor()
    cur.executemany(f"""INSERT INTO {SCHEMA}.BENCHMARK_RESULTS (RUN_ID, EXPERIMENT, ARM, AGENT, QID, RUN_NO, CORRECT,
        FELL_FOR_WRONG, NAMES_GOVERNED_TERM, HEADLINE_VALUE, LATENCY_S, TOOL_CALLS, USED_BON, ANSWER, JUDGE_REASON, ERROR, HEDGED)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        [(run_id, r["experiment"], r["arm"], r["agent"], r["qid"], r["run_no"], bool(r["correct"]),
          bool(r.get("fell_for_wrong")), bool(r.get("names_governed_term")), r.get("headline_value"),
          r["latency_s"], len(r["tools"]), "business_ontology" in r["tools"], r["answer"][:16000],
          r.get("reason"), r.get("error"), bool(r.get("hedged"))) for r in rows])
    cur.close()


def task(experiment, arm, agent, gt, run_no, attempts=3):
    # Retry the whole call: transient connection errors (e.g. 390422 IP blocks) otherwise abort the run.
    for i in range(attempts):
        conn = None
        try:
            conn = connect()
            res = run_agent(conn, agent, gt["QUESTION"])
            v = judge(conn, gt, res["answer"])
            break
        except snowflake.connector.errors.Error as e:
            if i == attempts - 1:
                raise
            print(f"  retry {i + 1} {experiment} {arm} {gt['QID']} run{run_no}: {str(e)[:80]}")
            time.sleep(30 * (i + 1))
        finally:
            if conn:
                conn.close()
    try:
        hv = float(v.get("headline_value")) if v.get("headline_value") is not None else None
    except (TypeError, ValueError):
        hv = None
    return {"experiment": experiment, "arm": arm, "agent": agent, "qid": gt["QID"], "run_no": run_no,
            **res, **v, "headline_value": hv}


def scorecard(conn, run_id):
    cur = conn.cursor(snowflake.connector.DictCursor)
    cur.execute(f"""
      WITH r AS (SELECT r.*, q.VALUE_PILLAR FROM {SCHEMA}.BENCHMARK_RESULTS r
                 JOIN {SCHEMA}.BENCHMARK_QUESTIONS q USING (QID) WHERE RUN_ID = %s AND EXPERIMENT = 'main')
      SELECT VALUE_PILLAR, ARM, ROUND(100*AVG(IFF(CORRECT,1,0)),0) PCT, COUNT(*) N
      FROM r GROUP BY 1,2 ORDER BY 1,2""", (run_id,))
    acc = cur.fetchall()
    cur.execute(f"""
      WITH per_q AS (SELECT ARM, QID, COUNT(DISTINCT IFF(HEADLINE_VALUE IS NULL, 'x:'||CORRECT::STRING,
                            ROUND(HEADLINE_VALUE,1)::STRING)) DISTINCT_ANSWERS, MIN(IFF(CORRECT,1,0)) ALL_CORRECT
                     FROM {SCHEMA}.BENCHMARK_RESULTS WHERE RUN_ID = %s AND EXPERIMENT = 'main' GROUP BY 1,2)
      SELECT ARM, ROUND(100*AVG(IFF(DISTINCT_ANSWERS = 1,1,0)),0) STABLE_PCT,
             ROUND(100*AVG(ALL_CORRECT),0) ALWAYS_RIGHT_PCT FROM per_q GROUP BY 1 ORDER BY 1""", (run_id,))
    stab = cur.fetchall()
    cur.execute(f"""SELECT ARM, ROUND(MEDIAN(LATENCY_S),1) P50_S, ROUND(AVG(TOOL_CALLS),1) AVG_TOOLS,
             ROUND(100*AVG(IFF(NAMES_GOVERNED_TERM,1,0)),0) TRACE_PCT, ROUND(100*AVG(IFF(FELL_FOR_WRONG,1,0)),0) TRAP_PCT,
             ROUND(100*AVG(IFF(HEDGED,1,0)),0) HEDGE_PCT
             FROM {SCHEMA}.BENCHMARK_RESULTS WHERE RUN_ID = %s AND EXPERIMENT = 'main' GROUP BY 1 ORDER BY 1""", (run_id,))
    cost = cur.fetchall()
    cur.execute(f"""
      WITH p AS (SELECT ARM, QID, RUN_NO, AGENT, HEADLINE_VALUE, CORRECT FROM {SCHEMA}.BENCHMARK_RESULTS
                 WHERE RUN_ID = %s AND EXPERIMENT = 'consistency')
      SELECT f.ARM, f.QID, ROUND(100*AVG(IFF(ROUND(f.HEADLINE_VALUE,1) = ROUND(s.HEADLINE_VALUE,1),1,0)),0) AGREE_PCT,
             ROUND(100*AVG(IFF(f.CORRECT AND s.CORRECT,1,0)),0) BOTH_RIGHT_PCT
      FROM p f JOIN p s ON f.ARM = s.ARM AND f.QID = s.QID AND f.RUN_NO = s.RUN_NO
       AND f.AGENT LIKE 'FINANCE%%' AND s.AGENT LIKE 'SALES%%' GROUP BY 1,2 ORDER BY 1,2""", (run_id,))
    cons = cur.fetchall()
    cur.close()
    return {"accuracy": acc, "stability": stab, "cost_trace": cost, "consistency": cons}


def print_scorecard(sc):
    pillars = {}
    for r in sc["accuracy"]:
        pillars.setdefault(r["VALUE_PILLAR"], {})[r["ARM"]] = int(r["PCT"])
    print("\nACCURACY BY VALUE PILLAR (% correct)       B enriched  C +BON  BON uplift (C-B)")
    for p, a in sorted(pillars.items()):
        print(f"  {p:<28} {a.get('B',0):>10}% {a.get('C',0):>6}%   {a.get('C',0)-a.get('B',0):+d} pts")
    print("\nSTABILITY              same answer every run   always right")
    for r in sc["stability"]:
        print(f"  arm {r['ARM']}  {int(r['STABLE_PCT']):>28}% {int(r['ALWAYS_RIGHT_PCT']):>14}%")
    print("\nCOST & TRACEABILITY   median s   avg tools   names term+SV metric   fell for trap   hedged")
    for r in sc["cost_trace"]:
        print(f"  arm {r['ARM']}  {r['P50_S']:>18} {r['AVG_TOOLS']:>11} {int(r['TRACE_PCT']):>21}% "
              f"{int(r['TRAP_PCT']):>14}% {int(r['HEDGE_PCT'] or 0):>7}%")
    print("\nCONSISTENCY ACROSS TEAMS  Finance agent vs Sales agent, same question")
    for r in sc["consistency"]:
        print(f"  {r['ARM']:<7} {r['QID']}  agree {int(r['AGREE_PCT'])}%  both right {int(r['BOTH_RIGHT_PCT'])}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3, help="runs per question for tiers 1 and 4")
    ap.add_argument("--runs-hard", type=int, default=5, help="runs per question for tiers 2 and 3, where BON uplift is expected")
    ap.add_argument("--qids", default="")
    ap.add_argument("--arms", default="B,C")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--skip-consistency", action="store_true")
    ap.add_argument("--check-index", action="store_true", help="only report whether the BON search index is ready")
    ap.add_argument("--force", action="store_true", help="run even if the BON index is not ready")
    ap.add_argument("--resume", default="", help="existing RUN_ID: run only the calls not yet saved for it")
    a = ap.parse_args()

    ready, report = check_index()
    print("BON search index check:\n" + report + f"\n  ready={ready}")
    if a.check_index:
        return
    if not ready and not a.force:
        print("Index not ready (new nodes missing or retired-domain nodes still served). "
              "Re-run later or pass --force. Propagation can take up to 6 hours.")
        return

    conn = connect()
    ensure_results_table(conn)
    qs = load_questions(conn, set(filter(None, a.qids.split(","))))
    run_id = a.resume or (time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:4])
    runs_for = lambda gt: a.runs_hard if int(gt["TIER"]) in (2, 3) else a.runs
    jobs = [("main", arm, ARMS[arm], gt, n) for gt in qs for arm in a.arms.split(",") for n in range(1, runs_for(gt) + 1)]
    if not a.skip_consistency:
        gts = {g["QID"]: g for g in load_questions(conn, set(PAIR_QIDS))}
        jobs += [("consistency", label, agent, gts[q], n) for label, agents in PAIRS.items()
                 for agent in agents for q in PAIR_QIDS for n in range(1, a.runs + 1)]
    if a.resume:
        cur = conn.cursor()
        cur.execute(f"SELECT EXPERIMENT, ARM, AGENT, QID, RUN_NO FROM {SCHEMA}.BENCHMARK_RESULTS WHERE RUN_ID = %s", (run_id,))
        saved = {tuple(r) for r in cur.fetchall()}
        cur.close()
        jobs = [j for j in jobs if (j[0], j[1], j[2], j[3]["QID"], j[4]) not in saved]
        print(f"resuming {run_id}: {len(saved)} calls already saved")
    print(f"run_id={run_id}: {len(jobs)} agent calls, {a.workers} parallel")

    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(task, *j) for j in jobs]
        for f in as_completed(futs):
            r = f.result()
            rows.append(r)
            done += 1
            print(f"  [{done}/{len(jobs)}] {r['experiment']:<11} {r['arm']:<6} {r['qid']} run{r['run_no']} "
                  f"{'OK ' if r['correct'] else 'BAD'} {r['latency_s']:>5}s tools={len(r['tools'])} "
                  f"val={r.get('headline_value')}")
            if len(rows) >= 12:
                save(conn, run_id, rows)
                rows = []
    if rows:
        save(conn, run_id, rows)

    sc = scorecard(conn, run_id)
    print_scorecard(sc)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"scorecard_{run_id}.json")
    with open(out, "w") as fh:
        json.dump({"run_id": run_id, **sc}, fh, indent=2, default=str)
    print(f"\nSaved {out}; raw rows in {SCHEMA}.BENCHMARK_RESULTS WHERE RUN_ID = '{run_id}'")
    conn.close()


if __name__ == "__main__":
    main()
BON_FILE_10_RUN_BENCHMARK_PY

files=(
  'sql/01_setup.sql'
  'sql/02_raw_data.sql'
  'sql/03_sap_schema.sql'
  'sql/04_ground_truth.sql'
  'sql/05_bare_svs.sql'
  'sql/06_enriched_svs.sql'
  'sql/07_ontology.sql'
  'sql/08_representations.sql'
  'sql/09_agents.sql'
  'benchmark/run_benchmark.py'
)
for file in "${files[@]}"; do
  if [[ ! -s "$file" ]]; then
    printf 'Setup failed: missing or empty file: %s\n' "$file" >&2
    exit 1
  fi
done
printf '%s\n' \
  'Created 10 project files in business-ontology/getting-started.' \
  'No Snowflake statements or benchmark were executed.'
BON_BOOTSTRAP
