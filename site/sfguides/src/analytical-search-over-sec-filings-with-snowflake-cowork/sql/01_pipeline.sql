-- =============================================================================
-- SEC Filing Intelligence — Self-Contained Pipeline
-- =============================================================================
-- All-in-one ingestion, enrichment, chunking, and signal extraction for
-- SEC EDGAR filings. 

-- Ingests SEC EDGAR filings (10-K, 10-Q, 8-K), enriches with tickers + industry
-- classification, chunks for search, and extracts AI signals (sentiment, events,
-- key metrics, forward guidance).
--
-- Usage:
--   1. Edit SECTION 1 (configuration) below
--   2. Run this entire file in a Snowsight worksheet as ACCOUNTADMIN
--   3. Call RUN_PIPELINE() — or call individual steps as needed
--
-- Date range: config_start_date to config_end_date (1 day to 1 year)
-- =============================================================================


USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- SECTION 1: CONFIGURATION (edit these values)
-- =============================================================================

SET config_database   = 'SEC_FILINGS';
SET config_schema     = 'FILING_DATA';
SET config_warehouse  = 'FILING_WH';
SET config_user_agent = 'YourOrg SEC-Filing-Demo your_name@company.com';
SET config_start_date = '2025-02-03';  -- ingestion start (YYYY-MM-DD)
SET config_end_date   = '2025-02-03';  -- ingestion end   (same date = 1 day)

-- =============================================================================
-- SECTION 2: TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS FILING_INDEX (
    ACCESSION_NO       VARCHAR(30)     NOT NULL PRIMARY KEY,
    CIK                VARCHAR(10),
    COMPANY_NAME       VARCHAR(500),
    FORM_TYPE          VARCHAR(20),
    FILED_AT           TIMESTAMP_TZ,
    PRIMARY_DOC_URL    VARCHAR(1000),
    FILING_INDEX_URL   VARCHAR(1000),
    IS_AMENDMENT       BOOLEAN         DEFAULT FALSE,
    PERIOD_OF_REPORT   DATE,
    SIC_CODE           VARCHAR(4),
    INDUSTRY_SECTOR    VARCHAR(100),
    INDUSTRY_TITLE     VARCHAR(200),
    TICKER             VARCHAR(20),
    TICKER_CHECKED_AT  TIMESTAMP_TZ,
    DOWNLOADED_AT      TIMESTAMP_TZ,
    CREATED_AT         TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FILING_CONTENT (
    ACCESSION_NO       VARCHAR(30)     NOT NULL PRIMARY KEY,
    CONTENT_TEXT       VARCHAR(16777216),
    STAGE_FILE_PATH    VARCHAR(500),
    FILE_SIZE_BYTES    NUMBER,
    FILE_FORMAT        VARCHAR(20)     DEFAULT 'FEED',
    PARSE_STATUS       VARCHAR(20)     DEFAULT 'PENDING',
    PARSE_ERROR        VARCHAR(2000),
    SIGNAL_STATUS      VARCHAR(20)     DEFAULT 'PENDING',
    CREATED_AT         TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS FILING_CHUNKS (
    CHUNK_ID           VARCHAR(60)     NOT NULL PRIMARY KEY,
    ACCESSION_NO       VARCHAR(30)     NOT NULL,
    COMPANY_NAME       VARCHAR(500),
    TICKER             VARCHAR(20),
    FORM_TYPE          VARCHAR(20),
    FILED_AT           TIMESTAMP_TZ,
    SECTION_NAME       VARCHAR(100),
    CHUNK_INDEX        NUMBER,
    CHUNK_TEXT         VARCHAR(16777216),
    TOKEN_COUNT        NUMBER,
    INDUSTRY_SECTOR    VARCHAR(100),
    INDUSTRY_TITLE     VARCHAR(200),
    PERIOD_OF_REPORT   DATE,
    CREATED_AT         TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP()
) CLUSTER BY (FORM_TYPE, FILED_AT);

CREATE TABLE IF NOT EXISTS FILING_SIGNALS (
    SIGNAL_ID              VARCHAR(60)     NOT NULL PRIMARY KEY,
    ACCESSION_NO           VARCHAR(30)     NOT NULL,
    COMPANY_NAME           VARCHAR(500),
    TICKER                 VARCHAR(20),
    FORM_TYPE              VARCHAR(20),
    SIGNAL_DATE            TIMESTAMP_TZ,
    PERIOD_OF_REPORT       DATE,
    EVENT_TYPE             VARCHAR(200),
    EVENT_TYPE_NORMALIZED  VARCHAR(50),
    SENTIMENT              VARCHAR(20),
    SUMMARY                VARCHAR(16777216),
    KEY_METRICS            VARCHAR(16777216),
    REVENUE                NUMBER(18,2),
    NET_INCOME             NUMBER(18,2),
    EPS                    NUMBER(10,4),
    YOY_CHANGE             VARCHAR(200),
    FORWARD_GUIDANCE       VARCHAR(16777216),
    RISK_FLAGS             ARRAY,
    MATERIAL_ITEMS         ARRAY,
    INDUSTRY_SECTOR        VARCHAR(100),
    INDUSTRY_TITLE         VARCHAR(200),
    EXTRACTION_MODEL       VARCHAR(50)     DEFAULT 'arctic-extract',
    IS_AMENDMENT           BOOLEAN         DEFAULT FALSE,
    CREATED_AT             TIMESTAMP_TZ    DEFAULT CURRENT_TIMESTAMP()
) CLUSTER BY (FORM_TYPE, SIGNAL_DATE);

CREATE TABLE IF NOT EXISTS SIC_CODES (
    SIC_CODE        VARCHAR(4)     NOT NULL PRIMARY KEY,
    OFFICE          VARCHAR(100)   NOT NULL,
    INDUSTRY_TITLE  VARCHAR(200)   NOT NULL,
    SECTOR          VARCHAR(100)   NOT NULL
);

CREATE TABLE IF NOT EXISTS _FEED_INGEST_LOG (
    FEED_DATE    DATE NOT NULL PRIMARY KEY,
    LOADED       NUMBER DEFAULT 0,
    STATUS       VARCHAR(20) DEFAULT 'PENDING',
    STARTED_AT   TIMESTAMP_TZ,
    UPDATED_AT   TIMESTAMP_TZ
);

INSERT OVERWRITE INTO SIC_CODES (SIC_CODE, OFFICE, INDUSTRY_TITLE, SECTOR) VALUES
('3571', 'Office of Technology', 'Electronic Computers', 'Technology'),
('3572', 'Office of Technology', 'Computer Storage Devices', 'Technology'),
('3575', 'Office of Technology', 'Computer Terminals', 'Technology'),
('3576', 'Office of Technology', 'Computer Communications Equipment', 'Technology'),
('3577', 'Office of Technology', 'Computer Peripheral Equipment, NEC', 'Technology'),
('3578', 'Office of Technology', 'Calculating & Accounting Machines', 'Technology'),
('3579', 'Office of Technology', 'Office Machines, NEC', 'Technology'),
('3612', 'Office of Technology', 'Power, Distribution & Specialty Transformers', 'Technology'),
('3613', 'Office of Technology', 'Switchgear & Switchboard Apparatus', 'Technology'),
('3621', 'Office of Technology', 'Motors & Generators', 'Technology'),
('3622', 'Office of Technology', 'Industrial Controls', 'Technology'),
('3625', 'Office of Technology', 'Relays & Industrial Controls', 'Technology'),
('3630', 'Office of Technology', 'Household Appliances', 'Technology'),
('3634', 'Office of Technology', 'Housewares & Fans', 'Technology'),
('3640', 'Office of Technology', 'Electric Lighting & Wiring Equipment', 'Technology'),
('3651', 'Office of Technology', 'Household Audio & Video Equipment', 'Technology'),
('3652', 'Office of Technology', 'Phonograph Records & Prerecorded Audio', 'Technology'),
('3661', 'Office of Technology', 'Telephone & Telegraph Apparatus', 'Technology'),
('3663', 'Office of Technology', 'Radio & TV Broadcasting & Communications Equipment', 'Technology'),
('3669', 'Office of Technology', 'Communications Equipment, NEC', 'Technology'),
('3670', 'Office of Technology', 'Electronic Components & Accessories', 'Technology'),
('3672', 'Office of Technology', 'Printed Circuit Boards', 'Technology'),
('3674', 'Office of Technology', 'Semiconductors & Related Devices', 'Technology'),
('3677', 'Office of Technology', 'Electronic Coils, Transformers & Inductors', 'Technology'),
('3678', 'Office of Technology', 'Electronic Connectors', 'Technology'),
('3679', 'Office of Technology', 'Electronic Components, NEC', 'Technology'),
('3690', 'Office of Technology', 'Electronic & Electrical Equipment, NEC', 'Technology'),
('3695', 'Office of Technology', 'Magnetic & Optical Recording Media', 'Technology'),
('3699', 'Office of Technology', 'Electronic & Electrical Equipment, NEC', 'Technology'),
('3810', 'Office of Technology', 'Search, Detection & Navigation Equipment', 'Technology'),
('3812', 'Office of Technology', 'Defense Electronics & Communications Equipment', 'Technology'),
('4800', 'Office of Technology', 'Communications', 'Technology'),
('4812', 'Office of Technology', 'Radiotelephone Communications', 'Technology'),
('4813', 'Office of Technology', 'Telephone Communications', 'Technology'),
('4822', 'Office of Technology', 'Telegraph & Other Message Communications', 'Technology'),
('4832', 'Office of Technology', 'Radio Broadcasting Stations', 'Technology'),
('4833', 'Office of Technology', 'Television Broadcasting Stations', 'Technology'),
('4841', 'Office of Technology', 'Cable & Other Pay Television Services', 'Technology'),
('4899', 'Office of Technology', 'Communications Services, NEC', 'Technology'),
('7370', 'Office of Technology', 'Computer Programming & Data Processing', 'Technology'),
('7371', 'Office of Technology', 'Computer Programming Services', 'Technology'),
('7372', 'Office of Technology', 'Prepackaged Software', 'Technology'),
('7373', 'Office of Technology', 'Computer Integrated Systems Design', 'Technology'),
('7374', 'Office of Technology', 'Computer Processing & Data Preparation', 'Technology'),
('7375', 'Office of Technology', 'Computer Rental & Leasing', 'Technology'),
('7376', 'Office of Technology', 'Computer Maintenance & Repair', 'Technology'),
('7377', 'Office of Technology', 'Computer Rental & Leasing', 'Technology'),
('7378', 'Office of Technology', 'Computer Maintenance & Repair', 'Technology'),
('7379', 'Office of Technology', 'Services Allied to Computer Programming', 'Technology'),
('7380', 'Office of Technology', 'Miscellaneous Business Services, NEC', 'Technology'),
('7381', 'Office of Technology', 'Investigation & Security Services', 'Technology'),
('7382', 'Office of Technology', 'Home Health Care Services', 'Technology'),
('7385', 'Office of Technology', 'Telephone Interconnect Systems', 'Technology'),
('7389', 'Office of Technology', 'Services Allied to Motion Picture Production', 'Technology'),
('8700', 'Office of Technology', 'Engineering, Accounting, Research & Management Services', 'Technology'),
('8711', 'Office of Technology', 'Engineering Services', 'Technology'),
('8712', 'Office of Technology', 'Architectural Services', 'Technology'),
('8713', 'Office of Technology', 'Surveying Services', 'Technology'),
('8721', 'Office of Technology', 'Accounting, Auditing & Bookkeeping', 'Technology'),
('8731', 'Office of Technology', 'Commercial Physical & Biological Research', 'Technology'),
('8732', 'Office of Technology', 'Commercial Testing & Research, NEC', 'Technology'),
('8733', 'Office of Technology', 'Noncommercial Research Organizations', 'Technology'),
('8734', 'Office of Technology', 'Testing Laboratories', 'Technology'),
('8741', 'Office of Technology', 'Management Services', 'Technology'),
('8742', 'Office of Technology', 'Management Consulting Services', 'Technology'),
('8743', 'Office of Technology', 'Public Relations Services', 'Technology'),
('8744', 'Office of Technology', 'Facilities Support Management Services', 'Technology'),
('3570', 'Office of Technology', 'Computer & Office Equipment', 'Technology'),
('3600', 'Office of Technology', 'Electronic & Electrical Equipment', 'Technology'),
('3620', 'Office of Technology', 'Electrical Industrial Apparatus', 'Technology'),
('2830', 'Office of Life Sciences', 'Industrial Chemicals & Synthetics', 'Life Sciences'),
('2833', 'Office of Life Sciences', 'Pharmaceutical Preparations', 'Life Sciences'),
('2834', 'Office of Life Sciences', 'Pharmaceutical Preparations', 'Life Sciences'),
('2835', 'Office of Life Sciences', 'In Vitro & In Vivo Diagnostic Substances', 'Life Sciences'),
('2836', 'Office of Life Sciences', 'Biological Products (No Diagnostic Substances)', 'Life Sciences'),
('2840', 'Office of Life Sciences', 'Soap, Detergents & Cleaning Preparations', 'Life Sciences'),
('2842', 'Office of Life Sciences', 'Specialty Cleaning & Polishing Preparations', 'Life Sciences'),
('2844', 'Office of Life Sciences', 'Perfumes, Cosmetics & Toilet Preparations', 'Life Sciences'),
('3826', 'Office of Life Sciences', 'Laboratory Analytical Instruments', 'Life Sciences'),
('3827', 'Office of Life Sciences', 'Optical Instruments & Lenses', 'Life Sciences'),
('3841', 'Office of Life Sciences', 'Surgical & Medical Instruments & Apparatus', 'Life Sciences'),
('3842', 'Office of Life Sciences', 'Orthopedic, Prosthetic & Surgical Supplies', 'Life Sciences'),
('3843', 'Office of Life Sciences', 'Dental Equipment & Supplies', 'Life Sciences'),
('3844', 'Office of Life Sciences', 'X-Ray Apparatus & Tubes', 'Life Sciences'),
('3845', 'Office of Life Sciences', 'Electromedical & Electrotherapeutic Apparatus', 'Life Sciences'),
('3851', 'Office of Life Sciences', 'Ophthalmic Goods', 'Life Sciences'),
('5047', 'Office of Life Sciences', 'Medical & Hospital Equipment & Supplies', 'Life Sciences'),
('5048', 'Office of Life Sciences', 'Ophthalmic Goods', 'Life Sciences'),
('5122', 'Office of Life Sciences', 'Drugs, Drug Proprietaries & Druggists Sundries', 'Life Sciences'),
('5912', 'Office of Life Sciences', 'Drug Stores & Proprietary Stores', 'Life Sciences'),
('8000', 'Office of Life Sciences', 'Health Services', 'Life Sciences'),
('8011', 'Office of Life Sciences', 'Offices & Clinics of Doctors of Medicine', 'Life Sciences'),
('8021', 'Office of Life Sciences', 'Offices & Clinics of Dentists', 'Life Sciences'),
('8031', 'Office of Life Sciences', 'Offices & Clinics of Osteopathic Physicians', 'Life Sciences'),
('8041', 'Office of Life Sciences', 'Offices & Clinics of Chiropractors', 'Life Sciences'),
('8042', 'Office of Life Sciences', 'Offices & Clinics of Optometrists', 'Life Sciences'),
('8049', 'Office of Life Sciences', 'Offices & Clinics of Other Health Practitioners', 'Life Sciences'),
('8050', 'Office of Life Sciences', 'Nursing & Personal Care Facilities', 'Life Sciences'),
('8051', 'Office of Life Sciences', 'Skilled Nursing Care Facilities', 'Life Sciences'),
('8060', 'Office of Life Sciences', 'Hospitals', 'Life Sciences'),
('8062', 'Office of Life Sciences', 'General Medical & Surgical Hospitals, NEC', 'Life Sciences'),
('8071', 'Office of Life Sciences', 'Health Services', 'Life Sciences'),
('8082', 'Office of Life Sciences', 'Home Health Care Services', 'Life Sciences'),
('8090', 'Office of Life Sciences', 'Health Services, NEC', 'Life Sciences'),
('8093', 'Office of Life Sciences', 'Specialty Outpatient Facilities, NEC', 'Life Sciences'),
('8099', 'Office of Life Sciences', 'Health Services, NEC', 'Life Sciences'),
('6020', 'Office of Finance', 'State Commercial Banks, Federal Reserve Members', 'Finance'),
('6021', 'Office of Finance', 'National Commercial Banks', 'Finance'),
('6022', 'Office of Finance', 'State Commercial Banks, Non-Fed Members', 'Finance'),
('6029', 'Office of Finance', 'Commercial Banks, NEC', 'Finance'),
('6035', 'Office of Finance', 'Savings Institution, Federally Chartered', 'Finance'),
('6036', 'Office of Finance', 'Savings Institutions, Not Federally Chartered', 'Finance'),
('6099', 'Office of Finance', 'Functions Related to Depository Banking', 'Finance'),
('6111', 'Office of Finance', 'Federal & Federally-Sponsored Credit Agencies', 'Finance'),
('6120', 'Office of Finance', 'Savings Institution, Federally Chartered', 'Finance'),
('6140', 'Office of Finance', 'Personal Credit Institutions', 'Finance'),
('6141', 'Office of Finance', 'Personal Credit Institutions', 'Finance'),
('6150', 'Office of Finance', 'Business Credit Institutions', 'Finance'),
('6153', 'Office of Finance', 'Short-Term Business Credit Institutions', 'Finance'),
('6159', 'Office of Finance', 'Federal-Sponsored Credit Agencies, NEC', 'Finance'),
('6162', 'Office of Finance', 'Mortgage Bankers, Loan Correspondents', 'Finance'),
('6163', 'Office of Finance', 'Loan Brokers', 'Finance'),
('6172', 'Office of Finance', 'Finance Services', 'Finance'),
('6199', 'Office of Finance', 'Finance Services', 'Finance'),
('6200', 'Office of Finance', 'Security & Commodity Services', 'Finance'),
('6211', 'Office of Finance', 'Security Brokers, Dealers & Flotation Companies', 'Finance'),
('6221', 'Office of Finance', 'Commodity Contracts Dealers, Brokers', 'Finance'),
('6282', 'Office of Finance', 'Investment Advice', 'Finance'),
('6311', 'Office of Finance', 'Life Insurance', 'Finance'),
('6321', 'Office of Finance', 'Accident & Health Insurance', 'Finance'),
('6324', 'Office of Finance', 'Hospital & Medical Service Plans', 'Finance'),
('6331', 'Office of Finance', 'Fire, Marine & Casualty Insurance', 'Finance'),
('6351', 'Office of Finance', 'Surety Insurance', 'Finance'),
('6399', 'Office of Finance', 'Insurance Carriers, NEC', 'Finance'),
('6411', 'Office of Finance', 'Insurance Agents, Brokers & Service', 'Finance'),
('6500', 'Office of Finance', 'Real Estate', 'Finance'),
('6510', 'Office of Finance', 'Real Estate Operators & Lessors', 'Finance'),
('6512', 'Office of Finance', 'Operators of Apartment Buildings', 'Finance'),
('6513', 'Office of Finance', 'Operators of Real Property, NEC', 'Finance'),
('6519', 'Office of Finance', 'Real Property Lessors, NEC', 'Finance'),
('6531', 'Office of Finance', 'Real Estate Agents & Managers', 'Finance'),
('6532', 'Office of Finance', 'Real Estate Dealers (for Own Account)', 'Finance'),
('6552', 'Office of Finance', 'Land Subdividers & Developers', 'Finance'),
('6726', 'Office of Finance', 'Investment Offices, NEC', 'Finance'),
('6770', 'Office of Finance', 'Blank Checks', 'Finance'),
('6792', 'Office of Finance', 'Investment Trusts, NEC', 'Finance'),
('6794', 'Office of Finance', 'Patent Owners & Lessors', 'Finance'),
('6795', 'Office of Finance', 'Mineral Royalty Traders', 'Finance'),
('6798', 'Office of Finance', 'Real Estate Investment Trusts', 'Finance'),
('6799', 'Office of Finance', 'Investors, NEC', 'Finance'),
('6189', 'Office of Finance', 'Asset-Backed Securities', 'Finance'),
('6361', 'Office of Finance', 'Title Insurance', 'Finance'),
('1500', 'Office of Real Estate & Construction', 'Building Construction General Contractors', 'Real Estate & Construction'),
('1520', 'Office of Real Estate & Construction', 'General Building Contractors, Residential', 'Real Estate & Construction'),
('1521', 'Office of Real Estate & Construction', 'General Contractors, Residential Buildings', 'Real Estate & Construction'),
('1531', 'Office of Real Estate & Construction', 'Operative Builders', 'Real Estate & Construction'),
('1540', 'Office of Real Estate & Construction', 'General Building Contractors, Nonresidential', 'Real Estate & Construction'),
('1541', 'Office of Real Estate & Construction', 'General Contractors, Industrial & Commercial', 'Real Estate & Construction'),
('1600', 'Office of Real Estate & Construction', 'Heavy Construction, Except Building', 'Real Estate & Construction'),
('1623', 'Office of Real Estate & Construction', 'Water, Sewer, Pipeline Construction', 'Real Estate & Construction'),
('1700', 'Office of Real Estate & Construction', 'Construction Special Trade Contractors', 'Real Estate & Construction'),
('1731', 'Office of Real Estate & Construction', 'Electrical Work', 'Real Estate & Construction'),
('1000', 'Office of Energy & Transportation', 'Metal Mining', 'Energy & Transportation'),
('1040', 'Office of Energy & Transportation', 'Gold and Silver Ores Mining', 'Energy & Transportation'),
('1090', 'Office of Energy & Transportation', 'Metal Mining Services', 'Energy & Transportation'),
('1220', 'Office of Energy & Transportation', 'Bituminous Coal & Lignite Mining', 'Energy & Transportation'),
('1221', 'Office of Energy & Transportation', 'Bituminous Coal & Lignite Surface Mining', 'Energy & Transportation'),
('1311', 'Office of Energy & Transportation', 'Crude Petroleum & Natural Gas', 'Energy & Transportation'),
('1381', 'Office of Energy & Transportation', 'Drilling Oil & Gas Wells', 'Energy & Transportation'),
('1382', 'Office of Energy & Transportation', 'Oil & Gas Field Services, NEC', 'Energy & Transportation'),
('1389', 'Office of Energy & Transportation', 'Services Allied to Oil & Gas Extraction', 'Energy & Transportation'),
('1400', 'Office of Energy & Transportation', 'Mining & Quarrying of Nonmetallic Minerals', 'Energy & Transportation'),
('2911', 'Office of Energy & Transportation', 'Petroleum Refining', 'Energy & Transportation'),
('2990', 'Office of Energy & Transportation', 'Petroleum & Coal Products, NEC', 'Energy & Transportation'),
('2999', 'Office of Energy & Transportation', 'Products of Petroleum & Coal, NEC', 'Energy & Transportation'),
('4011', 'Office of Energy & Transportation', 'Railroads, Line-Haul Operating', 'Energy & Transportation'),
('4013', 'Office of Energy & Transportation', 'Railroad Switching & Terminal Establishments', 'Energy & Transportation'),
('4100', 'Office of Energy & Transportation', 'Local & Suburban Transit', 'Energy & Transportation'),
('4210', 'Office of Energy & Transportation', 'Trucking & Courier Services (No Air)', 'Energy & Transportation'),
('4213', 'Office of Energy & Transportation', 'Trucking (Except Local)', 'Energy & Transportation'),
('4220', 'Office of Energy & Transportation', 'Public Warehousing & Storage', 'Energy & Transportation'),
('4231', 'Office of Energy & Transportation', 'Terminal & Joint Terminal Maintenance', 'Energy & Transportation'),
('4400', 'Office of Energy & Transportation', 'Water Transportation', 'Energy & Transportation'),
('4412', 'Office of Energy & Transportation', 'Deep Sea Foreign Transportation of Freight', 'Energy & Transportation'),
('4512', 'Office of Energy & Transportation', 'Air Transportation, Scheduled', 'Energy & Transportation'),
('4513', 'Office of Energy & Transportation', 'Air Courier Services', 'Energy & Transportation'),
('4522', 'Office of Energy & Transportation', 'Air Transportation, Nonscheduled', 'Energy & Transportation'),
('4581', 'Office of Energy & Transportation', 'Airports, Flying Fields & Airport Terminal Services', 'Energy & Transportation'),
('4610', 'Office of Energy & Transportation', 'Pipe Lines (No Natural Gas)', 'Energy & Transportation'),
('4700', 'Office of Energy & Transportation', 'Transportation Services', 'Energy & Transportation'),
('4731', 'Office of Energy & Transportation', 'Arrangement of Transportation of Freight & Cargo', 'Energy & Transportation'),
('4900', 'Office of Energy & Transportation', 'Electric, Gas & Sanitary Services', 'Energy & Transportation'),
('4911', 'Office of Energy & Transportation', 'Electric Services', 'Energy & Transportation'),
('4922', 'Office of Energy & Transportation', 'Natural Gas Transmission', 'Energy & Transportation'),
('4923', 'Office of Energy & Transportation', 'Natural Gas Transmission & Distribution', 'Energy & Transportation'),
('4924', 'Office of Energy & Transportation', 'Natural Gas Distribution', 'Energy & Transportation'),
('4931', 'Office of Energy & Transportation', 'Electric & Other Services Combined', 'Energy & Transportation'),
('4932', 'Office of Energy & Transportation', 'Gas & Other Services Combined', 'Energy & Transportation'),
('4941', 'Office of Energy & Transportation', 'Water Supply', 'Energy & Transportation'),
('4950', 'Office of Energy & Transportation', 'Sanitary Services', 'Energy & Transportation'),
('4953', 'Office of Energy & Transportation', 'Refuse Systems', 'Energy & Transportation'),
('4955', 'Office of Energy & Transportation', 'Hazardous Waste Management', 'Energy & Transportation'),
('4991', 'Office of Energy & Transportation', 'Cogeneration Services & Small Power Producers', 'Energy & Transportation'),
('2000', 'Office of Manufacturing', 'Food & Kindred Products', 'Manufacturing'),
('2011', 'Office of Manufacturing', 'Meat Packing Plants', 'Manufacturing'),
('2013', 'Office of Manufacturing', 'Sausages & Other Prepared Meats', 'Manufacturing'),
('2015', 'Office of Manufacturing', 'Poultry Slaughtering & Processing', 'Manufacturing'),
('2020', 'Office of Manufacturing', 'Dairy Products', 'Manufacturing'),
('2024', 'Office of Manufacturing', 'Ice Cream & Frozen Desserts', 'Manufacturing'),
('2030', 'Office of Manufacturing', 'Canned, Frozen & Preserved Fruits & Vegetables', 'Manufacturing'),
('2033', 'Office of Manufacturing', 'Canned Fruits, Vegetables & Preserves', 'Manufacturing'),
('2040', 'Office of Manufacturing', 'Grain Mill Products', 'Manufacturing'),
('2050', 'Office of Manufacturing', 'Bakery Products', 'Manufacturing'),
('2052', 'Office of Manufacturing', 'Cookies & Crackers', 'Manufacturing'),
('2060', 'Office of Manufacturing', 'Sugar & Confectionery Products', 'Manufacturing'),
('2070', 'Office of Manufacturing', 'Fats & Oils', 'Manufacturing'),
('2080', 'Office of Manufacturing', 'Beverages', 'Manufacturing'),
('2082', 'Office of Manufacturing', 'Malt Beverages', 'Manufacturing'),
('2086', 'Office of Manufacturing', 'Bottled & Canned Soft Drinks & Carbonated Water', 'Manufacturing'),
('2090', 'Office of Manufacturing', 'Food Preparations, NEC', 'Manufacturing'),
('2092', 'Office of Manufacturing', 'Prepared Fresh or Frozen Fish & Seafood', 'Manufacturing'),
('2100', 'Office of Manufacturing', 'Tobacco Products', 'Manufacturing'),
('2111', 'Office of Manufacturing', 'Cigarettes', 'Manufacturing'),
('2200', 'Office of Manufacturing', 'Textile Mill Products', 'Manufacturing'),
('2211', 'Office of Manufacturing', 'Broadwoven Fabric Mills, Cotton', 'Manufacturing'),
('2221', 'Office of Manufacturing', 'Broadwoven Fabric Mills, Man Made Fiber & Silk', 'Manufacturing'),
('2250', 'Office of Manufacturing', 'Knitting Mills', 'Manufacturing'),
('2253', 'Office of Manufacturing', 'Knit Outerwear Mills', 'Manufacturing'),
('2273', 'Office of Manufacturing', 'Carpets & Rugs', 'Manufacturing'),
('2300', 'Office of Manufacturing', 'Apparel & Other Finished Products', 'Manufacturing'),
('2320', 'Office of Manufacturing', 'Mens & Boys Furnishings, Work Clothing', 'Manufacturing'),
('2330', 'Office of Manufacturing', 'Womens, Misses & Juniors Outerwear', 'Manufacturing'),
('2340', 'Office of Manufacturing', 'Childrens Outerwear', 'Manufacturing'),
('2390', 'Office of Manufacturing', 'Fabricated Textile Products, NEC', 'Manufacturing'),
('2400', 'Office of Manufacturing', 'Lumber & Wood Products (No Furniture)', 'Manufacturing'),
('2421', 'Office of Manufacturing', 'Sawmills & Planing Mills, General', 'Manufacturing'),
('2430', 'Office of Manufacturing', 'Millwork, Veneer, Plywood & Structural Members', 'Manufacturing'),
('2451', 'Office of Manufacturing', 'Mobile Homes', 'Manufacturing'),
('2510', 'Office of Manufacturing', 'Household Furniture', 'Manufacturing'),
('2511', 'Office of Manufacturing', 'Wood Household Furniture', 'Manufacturing'),
('2520', 'Office of Manufacturing', 'Office Furniture', 'Manufacturing'),
('2522', 'Office of Manufacturing', 'Office Furniture (No Wood)', 'Manufacturing'),
('2531', 'Office of Manufacturing', 'Public Building & Related Furniture', 'Manufacturing'),
('2590', 'Office of Manufacturing', 'Miscellaneous Furniture & Fixtures', 'Manufacturing'),
('2600', 'Office of Manufacturing', 'Papers & Allied Products', 'Manufacturing'),
('2611', 'Office of Manufacturing', 'Pulp Mills', 'Manufacturing'),
('2621', 'Office of Manufacturing', 'Paper Mills', 'Manufacturing'),
('2631', 'Office of Manufacturing', 'Paperboard Mills', 'Manufacturing'),
('2650', 'Office of Manufacturing', 'Paperboard Containers & Boxes', 'Manufacturing'),
('2670', 'Office of Manufacturing', 'Converted Paper & Paperboard Products', 'Manufacturing'),
('2673', 'Office of Manufacturing', 'Plastics, Foil & Coated Paper Bags', 'Manufacturing'),
('2710', 'Office of Manufacturing', 'Newspapers: Publishing & Printing', 'Manufacturing'),
('2711', 'Office of Manufacturing', 'Newspapers: Publishing & Printing', 'Manufacturing'),
('2720', 'Office of Manufacturing', 'Periodicals: Publishing & Printing', 'Manufacturing'),
('2721', 'Office of Manufacturing', 'Periodicals: Publishing & Printing', 'Manufacturing'),
('2731', 'Office of Manufacturing', 'Books: Publishing & Printing', 'Manufacturing'),
('2732', 'Office of Manufacturing', 'Book Printing', 'Manufacturing'),
('2741', 'Office of Manufacturing', 'Miscellaneous Publishing', 'Manufacturing'),
('2750', 'Office of Manufacturing', 'Commercial Printing', 'Manufacturing'),
('2761', 'Office of Manufacturing', 'Manifold Business Forms', 'Manufacturing'),
('2780', 'Office of Manufacturing', 'Blankbooks, Looseleaf Binders & Devices', 'Manufacturing'),
('2790', 'Office of Manufacturing', 'Service Industries for the Printing Trade', 'Manufacturing'),
('2800', 'Office of Manufacturing', 'Chemicals & Allied Products', 'Manufacturing'),
('2810', 'Office of Manufacturing', 'Industrial Chemicals & Synthetics', 'Manufacturing'),
('2812', 'Office of Manufacturing', 'Alkalies & Chlorine', 'Manufacturing'),
('2813', 'Office of Manufacturing', 'Industrial Gases', 'Manufacturing'),
('2816', 'Office of Manufacturing', 'Inorganic Pigments', 'Manufacturing'),
('2819', 'Office of Manufacturing', 'Industrial Inorganic Chemicals, NEC', 'Manufacturing'),
('2820', 'Office of Manufacturing', 'Plastics Materials & Synthetic Resins', 'Manufacturing'),
('2821', 'Office of Manufacturing', 'Plastics Materials, Synthetic Resins & Nonvulcanizable Elastomers', 'Manufacturing'),
('2822', 'Office of Manufacturing', 'Synthetic Rubber', 'Manufacturing'),
('2823', 'Office of Manufacturing', 'Cellulosic Manmade Fibers', 'Manufacturing'),
('2824', 'Office of Manufacturing', 'Manmade Organic Fibers (No Cellulosic)', 'Manufacturing'),
('2841', 'Office of Manufacturing', 'Soap & Other Detergents (Except Specialty Cleaning)', 'Manufacturing'),
('2851', 'Office of Manufacturing', 'Paints, Varnishes, Lacquers & Allied Products', 'Manufacturing'),
('2860', 'Office of Manufacturing', 'Industrial Chemicals & Synthetics', 'Manufacturing'),
('2869', 'Office of Manufacturing', 'Industrial Organic Chemicals, NEC', 'Manufacturing'),
('2870', 'Office of Manufacturing', 'Agricultural Chemicals', 'Manufacturing'),
('2891', 'Office of Manufacturing', 'Adhesives & Sealants', 'Manufacturing'),
('2899', 'Office of Manufacturing', 'Chemicals & Chemical Preparations, NEC', 'Manufacturing'),
('3000', 'Office of Manufacturing', 'Rubber & Misc Plastics Products', 'Manufacturing'),
('3011', 'Office of Manufacturing', 'Tires & Inner Tubes', 'Manufacturing'),
('3021', 'Office of Manufacturing', 'Rubber & Plastics Footwear', 'Manufacturing'),
('3050', 'Office of Manufacturing', 'Gaskets, Packing & Sealing Devices', 'Manufacturing'),
('3060', 'Office of Manufacturing', 'Fabricated Rubber Products, NEC', 'Manufacturing'),
('3080', 'Office of Manufacturing', 'Plastics Products Manufacturing', 'Manufacturing'),
('3081', 'Office of Manufacturing', 'Plastics Plumbing Fixtures', 'Manufacturing'),
('3086', 'Office of Manufacturing', 'Plastics Foam Products', 'Manufacturing'),
('3089', 'Office of Manufacturing', 'Plastics Products Manufacturing, NEC', 'Manufacturing'),
('3100', 'Office of Manufacturing', 'Leather & Leather Products', 'Manufacturing'),
('3140', 'Office of Manufacturing', 'Footwear (No Rubber)', 'Manufacturing'),
('3211', 'Office of Manufacturing', 'Flat Glass', 'Manufacturing'),
('3220', 'Office of Manufacturing', 'Glass & Glassware, Pressed or Blown', 'Manufacturing'),
('3221', 'Office of Manufacturing', 'Glass Containers', 'Manufacturing'),
('3231', 'Office of Manufacturing', 'Glass Products Made of Purchased Glass', 'Manufacturing'),
('3241', 'Office of Manufacturing', 'Cement, Hydraulic', 'Manufacturing'),
('3250', 'Office of Manufacturing', 'Structural Clay Products', 'Manufacturing'),
('3270', 'Office of Manufacturing', 'Concrete, Gypsum & Plaster Products', 'Manufacturing'),
('3272', 'Office of Manufacturing', 'Concrete Products (No Block & Brick)', 'Manufacturing'),
('3281', 'Office of Manufacturing', 'Cut Stone & Stone Products', 'Manufacturing'),
('3290', 'Office of Manufacturing', 'Abrasive, Asbestos & Misc Nonmetallic Mineral Products', 'Manufacturing'),
('3310', 'Office of Manufacturing', 'Steel Works, Blast Furnaces & Rolling & Finishing Mills', 'Manufacturing'),
('3312', 'Office of Manufacturing', 'Steel Works, Blast Furnaces (Incl Coke Ovens)', 'Manufacturing'),
('3317', 'Office of Manufacturing', 'Steel Pipe & Tubes', 'Manufacturing'),
('3320', 'Office of Manufacturing', 'Iron & Steel Foundries', 'Manufacturing'),
('3330', 'Office of Manufacturing', 'Primary Smelting & Refining of Nonferrous Metals', 'Manufacturing'),
('3334', 'Office of Manufacturing', 'Primary Production of Aluminum', 'Manufacturing'),
('3340', 'Office of Manufacturing', 'Secondary Smelting & Refining of Nonferrous Metals', 'Manufacturing'),
('3350', 'Office of Manufacturing', 'Rolling, Drawing & Extruding of Nonferrous Metals', 'Manufacturing'),
('3357', 'Office of Manufacturing', 'Drawing & Insulating of Nonferrous Metals', 'Manufacturing'),
('3360', 'Office of Manufacturing', 'Nonferrous Foundries (Castings)', 'Manufacturing'),
('3390', 'Office of Manufacturing', 'Misc Primary Metal Products', 'Manufacturing'),
('3411', 'Office of Manufacturing', 'Metal Cans', 'Manufacturing'),
('3412', 'Office of Manufacturing', 'Metal Shipping Barrels, Drums, Kegs & Pails', 'Manufacturing'),
('3420', 'Office of Manufacturing', 'Cutlery, Handtools & General Hardware', 'Manufacturing'),
('3421', 'Office of Manufacturing', 'Cutlery, Handtools & General Hardware', 'Manufacturing'),
('3430', 'Office of Manufacturing', 'Heating Equipment & Plumbing Fixtures', 'Manufacturing'),
('3433', 'Office of Manufacturing', 'Heating Equipment, Except Electric & Warm Air Furnaces', 'Manufacturing'),
('3440', 'Office of Manufacturing', 'Fabricated Structural Metal Manufacturing', 'Manufacturing'),
('3442', 'Office of Manufacturing', 'Metal Doors, Sash, Frames, Molding & Trim', 'Manufacturing'),
('3443', 'Office of Manufacturing', 'Fabricated Plate Work (Boiler Shops)', 'Manufacturing'),
('3444', 'Office of Manufacturing', 'Sheet Metal Work', 'Manufacturing'),
('3448', 'Office of Manufacturing', 'Prefabricated Metal Buildings & Components', 'Manufacturing'),
('3451', 'Office of Manufacturing', 'Screw Machine Products', 'Manufacturing'),
('3452', 'Office of Manufacturing', 'Bolts, Nuts, Screws, Rivets & Washers', 'Manufacturing'),
('3460', 'Office of Manufacturing', 'Metal Forgings & Stampings', 'Manufacturing'),
('3470', 'Office of Manufacturing', 'Services to Buildings & Dwellings', 'Manufacturing'),
('3480', 'Office of Manufacturing', 'Ordnance & Accessories, NEC', 'Manufacturing'),
('3489', 'Office of Manufacturing', 'Ordnance & Accessories, NEC', 'Manufacturing'),
('3490', 'Office of Manufacturing', 'Misc Fabricated Metal Products', 'Manufacturing'),
('3491', 'Office of Manufacturing', 'Industrial Valves', 'Manufacturing'),
('3492', 'Office of Manufacturing', 'Fluid Power Valves & Hose Fittings', 'Manufacturing'),
('3493', 'Office of Manufacturing', 'Steel Springs, Except Wire', 'Manufacturing'),
('3494', 'Office of Manufacturing', 'Valves & Pipe Fittings, NEC', 'Manufacturing'),
('3499', 'Office of Manufacturing', 'Metal Services, NEC', 'Manufacturing'),
('3510', 'Office of Manufacturing', 'Engines & Turbines', 'Manufacturing'),
('3523', 'Office of Manufacturing', 'Farm Machinery & Equipment', 'Manufacturing'),
('3524', 'Office of Manufacturing', 'Lawn & Garden Tractors & Equipment', 'Manufacturing'),
('3530', 'Office of Manufacturing', 'Construction, Mining & Materials Handling Equipment', 'Manufacturing'),
('3531', 'Office of Manufacturing', 'Construction Machinery & Equipment', 'Manufacturing'),
('3532', 'Office of Manufacturing', 'Mining Machinery & Equipment', 'Manufacturing'),
('3533', 'Office of Manufacturing', 'Oil & Gas Field Machinery & Equipment', 'Manufacturing'),
('3537', 'Office of Manufacturing', 'Industrial Trucks, Tractors, Trailers & Stackers', 'Manufacturing'),
('3540', 'Office of Manufacturing', 'Metalworking Machinery & Equipment', 'Manufacturing'),
('3541', 'Office of Manufacturing', 'Machine Tools, Metal Cutting Types', 'Manufacturing'),
('3550', 'Office of Manufacturing', 'Special Industry Machinery (No Metalworking)', 'Manufacturing'),
('3555', 'Office of Manufacturing', 'Printing Trades Machinery & Equipment', 'Manufacturing'),
('3556', 'Office of Manufacturing', 'Food Products Machinery', 'Manufacturing'),
('3559', 'Office of Manufacturing', 'Special Industry Machinery, NEC', 'Manufacturing'),
('3560', 'Office of Manufacturing', 'General Industrial Machinery & Equipment', 'Manufacturing'),
('3561', 'Office of Manufacturing', 'Pumps & Pumping Equipment', 'Manufacturing'),
('3562', 'Office of Manufacturing', 'Ball & Roller Bearings', 'Manufacturing'),
('3564', 'Office of Manufacturing', 'Industrial & Commercial Fans & Blowers', 'Manufacturing'),
('3567', 'Office of Manufacturing', 'Industrial Process Furnaces & Ovens', 'Manufacturing'),
('3569', 'Office of Manufacturing', 'General Industrial Machinery & Equipment, NEC', 'Manufacturing'),
('3580', 'Office of Manufacturing', 'Refrigeration & Heating Equipment', 'Manufacturing'),
('3585', 'Office of Manufacturing', 'Air-Conditioning & Warm Air Heating Equipment', 'Manufacturing'),
('3589', 'Office of Manufacturing', 'Industrial & Commercial Machinery, NEC', 'Manufacturing'),
('3590', 'Office of Manufacturing', 'Misc Industrial & Commercial Machinery & Equipment', 'Manufacturing'),
('3599', 'Office of Manufacturing', 'Industrial & Commercial Machinery, NEC', 'Manufacturing'),
('3711', 'Office of Manufacturing', 'Motor Vehicles & Passenger Car Bodies', 'Manufacturing'),
('3713', 'Office of Manufacturing', 'Truck Trailers', 'Manufacturing'),
('3714', 'Office of Manufacturing', 'Motor Vehicle Parts & Accessories', 'Manufacturing'),
('3715', 'Office of Manufacturing', 'Truck Trailers', 'Manufacturing'),
('3716', 'Office of Manufacturing', 'Motor Homes', 'Manufacturing'),
('3720', 'Office of Manufacturing', 'Aircraft & Parts', 'Manufacturing'),
('3721', 'Office of Manufacturing', 'Aircraft', 'Manufacturing'),
('3724', 'Office of Manufacturing', 'Aircraft Engines & Engine Parts', 'Manufacturing'),
('3728', 'Office of Manufacturing', 'Aircraft Parts & Auxiliary Equipment, NEC', 'Manufacturing'),
('3730', 'Office of Manufacturing', 'Ship & Boat Building & Repairing', 'Manufacturing'),
('3743', 'Office of Manufacturing', 'Railroad Equipment', 'Manufacturing'),
('3751', 'Office of Manufacturing', 'Motorcycles, Bicycles & Parts', 'Manufacturing'),
('3760', 'Office of Manufacturing', 'Guided Missiles & Space Vehicles & Parts', 'Manufacturing'),
('3769', 'Office of Manufacturing', 'Guided Missiles & Space Vehicles, NEC', 'Manufacturing'),
('3790', 'Office of Manufacturing', 'Misc Transportation Equipment', 'Manufacturing'),
('3795', 'Office of Manufacturing', 'Tanks & Tank Components', 'Manufacturing'),
('3822', 'Office of Manufacturing', 'Automatic Controls for Temperature Regulation', 'Manufacturing'),
('3823', 'Office of Manufacturing', 'Industrial Instruments for Measurement', 'Manufacturing'),
('3824', 'Office of Manufacturing', 'Industrial Instruments for Measurement, Totalizing Fluid Meters', 'Manufacturing'),
('3825', 'Office of Manufacturing', 'Instruments for Measuring & Testing of Electricity', 'Manufacturing'),
('3829', 'Office of Manufacturing', 'Measuring & Controlling Devices, NEC', 'Manufacturing'),
('3861', 'Office of Manufacturing', 'Photographic Equipment & Supplies', 'Manufacturing'),
('3873', 'Office of Manufacturing', 'Watches, Clocks & Clockwork Operated Devices', 'Manufacturing'),
('3911', 'Office of Manufacturing', 'Jewelry, Precious Metal', 'Manufacturing'),
('3931', 'Office of Manufacturing', 'Musical Instruments', 'Manufacturing'),
('3942', 'Office of Manufacturing', 'Dolls & Stuffed Toys', 'Manufacturing'),
('3944', 'Office of Manufacturing', 'Games, Toys & Childrens Vehicles', 'Manufacturing'),
('3949', 'Office of Manufacturing', 'Sporting & Athletic Goods, NEC', 'Manufacturing'),
('3950', 'Office of Manufacturing', 'Pens, Pencils & Artists Materials', 'Manufacturing'),
('3960', 'Office of Manufacturing', 'Costume Jewelry & Novelties', 'Manufacturing'),
('3990', 'Office of Manufacturing', 'Miscellaneous Manufacturing Industries', 'Manufacturing'),
('3993', 'Office of Manufacturing', 'Signs & Advertising Specialties', 'Manufacturing'),
('3999', 'Office of Manufacturing', 'Manufacturing Industries, NEC', 'Manufacturing'),
('2890', 'Office of Manufacturing', 'Industrial Chemicals, NEC', 'Manufacturing'),
('3341', 'Office of Manufacturing', 'Secondary Smelting of Nonferrous Metals', 'Manufacturing'),
('3821', 'Office of Manufacturing', 'Laboratory Apparatus & Furniture', 'Manufacturing'),
('3910', 'Office of Manufacturing', 'Jewelry, Silverware & Plated Ware', 'Manufacturing'),
('5000', 'Office of Trade & Services', 'Durable Goods, Wholesale', 'Trade & Services'),
('5010', 'Office of Trade & Services', 'Motor Vehicles & Motor Vehicle Parts & Supplies', 'Trade & Services'),
('5013', 'Office of Trade & Services', 'Motor Vehicle Supplies & New Parts', 'Trade & Services'),
('5020', 'Office of Trade & Services', 'Furniture & Homefurnishings', 'Trade & Services'),
('5030', 'Office of Trade & Services', 'Lumber & Other Construction Materials', 'Trade & Services'),
('5040', 'Office of Trade & Services', 'Professional & Commercial Equipment & Supplies', 'Trade & Services'),
('5045', 'Office of Trade & Services', 'Computers & Peripherals & Software', 'Trade & Services'),
('5050', 'Office of Trade & Services', 'Metals & Minerals (No Petroleum)', 'Trade & Services'),
('5051', 'Office of Trade & Services', 'Metals Service Centers & Offices', 'Trade & Services'),
('5063', 'Office of Trade & Services', 'Electrical Apparatus & Equipment, Wiring Supplies', 'Trade & Services'),
('5064', 'Office of Trade & Services', 'Electrical Appliances, Television & Radio Sets', 'Trade & Services'),
('5065', 'Office of Trade & Services', 'Electronic Parts & Equipment, NEC', 'Trade & Services'),
('5070', 'Office of Trade & Services', 'Hardware & Plumbing & Heating Equipment & Supplies', 'Trade & Services'),
('5080', 'Office of Trade & Services', 'Industrial & Personal Service Paper', 'Trade & Services'),
('5082', 'Office of Trade & Services', 'Construction & Mining Machinery & Equipment', 'Trade & Services'),
('5084', 'Office of Trade & Services', 'Industrial Machinery & Equipment', 'Trade & Services'),
('5090', 'Office of Trade & Services', 'Durable Goods, NEC', 'Trade & Services'),
('5094', 'Office of Trade & Services', 'Jewelry, Watches & Precious Stones', 'Trade & Services'),
('5099', 'Office of Trade & Services', 'Durable Goods, NEC', 'Trade & Services'),
('5110', 'Office of Trade & Services', 'Paper & Paper Products', 'Trade & Services'),
('5130', 'Office of Trade & Services', 'Apparel, Piece Goods & Notions', 'Trade & Services'),
('5140', 'Office of Trade & Services', 'Groceries & Related Products, NEC', 'Trade & Services'),
('5141', 'Office of Trade & Services', 'Groceries, General Line', 'Trade & Services'),
('5150', 'Office of Trade & Services', 'Farm-Product Raw Materials', 'Trade & Services'),
('5160', 'Office of Trade & Services', 'Chemicals & Allied Products', 'Trade & Services'),
('5171', 'Office of Trade & Services', 'Petroleum & Petroleum Products (No Bulk Stations)', 'Trade & Services'),
('5172', 'Office of Trade & Services', 'Petroleum Products, NEC', 'Trade & Services'),
('5180', 'Office of Trade & Services', 'Beer, Wine & Distilled Alcoholic Beverages', 'Trade & Services'),
('5190', 'Office of Trade & Services', 'Misc Nondurable Goods, Wholesale', 'Trade & Services'),
('5200', 'Office of Trade & Services', 'Retail Stores, Building Materials & Garden Supplies', 'Trade & Services'),
('5211', 'Office of Trade & Services', 'Lumber & Other Building Materials Dealers', 'Trade & Services'),
('5271', 'Office of Trade & Services', 'Mobile Home Dealers', 'Trade & Services'),
('5311', 'Office of Trade & Services', 'Department Stores', 'Trade & Services'),
('5331', 'Office of Trade & Services', 'Variety Stores', 'Trade & Services'),
('5399', 'Office of Trade & Services', 'Misc General Merchandise Stores', 'Trade & Services'),
('5400', 'Office of Trade & Services', 'Retail Stores, Food', 'Trade & Services'),
('5411', 'Office of Trade & Services', 'Grocery Stores', 'Trade & Services'),
('5412', 'Office of Trade & Services', 'Convenience Stores', 'Trade & Services'),
('5500', 'Office of Trade & Services', 'Retail Stores, Auto Dealers & Gas Stations', 'Trade & Services'),
('5531', 'Office of Trade & Services', 'Auto & Home Supply Stores', 'Trade & Services'),
('5600', 'Office of Trade & Services', 'Retail Stores, Apparel & Accessory', 'Trade & Services'),
('5621', 'Office of Trade & Services', 'Womens Clothing Stores', 'Trade & Services'),
('5651', 'Office of Trade & Services', 'Family Clothing Stores', 'Trade & Services'),
('5661', 'Office of Trade & Services', 'Shoe Stores', 'Trade & Services'),
('5700', 'Office of Trade & Services', 'Retail Stores, Home Furniture & Equipment', 'Trade & Services'),
('5712', 'Office of Trade & Services', 'Furniture Stores', 'Trade & Services'),
('5731', 'Office of Trade & Services', 'Radio, Television & Consumer Electronics Stores', 'Trade & Services'),
('5734', 'Office of Trade & Services', 'Computer & Computer Software Stores', 'Trade & Services'),
('5735', 'Office of Trade & Services', 'Record & Prerecorded Tape Stores', 'Trade & Services'),
('5810', 'Office of Trade & Services', 'Eating & Drinking Places', 'Trade & Services'),
('5812', 'Office of Trade & Services', 'Eating Places', 'Trade & Services'),
('5900', 'Office of Trade & Services', 'Retail Stores, Misc', 'Trade & Services'),
('5940', 'Office of Trade & Services', 'Sporting Goods & Bicycle Shops', 'Trade & Services'),
('5944', 'Office of Trade & Services', 'Jewelry Stores', 'Trade & Services'),
('5945', 'Office of Trade & Services', 'Hobby, Toy & Game Shops', 'Trade & Services'),
('5947', 'Office of Trade & Services', 'Gift, Novelty & Souvenir Shops', 'Trade & Services'),
('5960', 'Office of Trade & Services', 'Retail Stores, NEC - Nonstore Retailers', 'Trade & Services'),
('5961', 'Office of Trade & Services', 'Catalog & Mail-Order Houses', 'Trade & Services'),
('5990', 'Office of Trade & Services', 'Retail Stores, NEC', 'Trade & Services'),
('5999', 'Office of Trade & Services', 'Retail Stores, NEC', 'Trade & Services'),
('7000', 'Office of Trade & Services', 'Hotels, Rooming Houses, Camps & Other Lodging', 'Trade & Services'),
('7011', 'Office of Trade & Services', 'Hotels & Motels', 'Trade & Services'),
('7200', 'Office of Trade & Services', 'Laundry, Cleaning, Garment Services', 'Trade & Services'),
('7310', 'Office of Trade & Services', 'Services-Advertising', 'Trade & Services'),
('7311', 'Office of Trade & Services', 'Advertising Services', 'Trade & Services'),
('7312', 'Office of Trade & Services', 'Advertising Services', 'Trade & Services'),
('7320', 'Office of Trade & Services', 'Services-Credit Reporting & Collection', 'Trade & Services'),
('7330', 'Office of Trade & Services', 'Mailing, Reproduction & Stenographic Services', 'Trade & Services'),
('7340', 'Office of Trade & Services', 'Services to Buildings & Dwellings', 'Trade & Services'),
('7350', 'Office of Trade & Services', 'Misc Equipment Rental & Leasing', 'Trade & Services'),
('7359', 'Office of Trade & Services', 'Equipment Rental & Leasing, NEC', 'Trade & Services'),
('7361', 'Office of Trade & Services', 'Help Supply Services', 'Trade & Services'),
('7363', 'Office of Trade & Services', 'Help Supply Services', 'Trade & Services'),
('7500', 'Office of Trade & Services', 'Automotive Repair, Services & Parking', 'Trade & Services'),
('7510', 'Office of Trade & Services', 'Automotive Rental & Leasing', 'Trade & Services'),
('7600', 'Office of Trade & Services', 'Miscellaneous Repair Services', 'Trade & Services'),
('7812', 'Office of Trade & Services', 'Motion Picture & Tape Distribution', 'Trade & Services'),
('7819', 'Office of Trade & Services', 'Services Allied to Motion Picture Production', 'Trade & Services'),
('7822', 'Office of Trade & Services', 'Motion Picture Distribution (Non-Theatrical)', 'Trade & Services'),
('7841', 'Office of Trade & Services', 'Video Tape Rental', 'Trade & Services'),
('7900', 'Office of Trade & Services', 'Amusement & Recreation Services', 'Trade & Services'),
('7941', 'Office of Trade & Services', 'Professional Sports Clubs', 'Trade & Services'),
('7948', 'Office of Trade & Services', 'Racing, Including Track Operation', 'Trade & Services'),
('7990', 'Office of Trade & Services', 'Services, NEC', 'Trade & Services'),
('7997', 'Office of Trade & Services', 'Membership Sports & Recreation Clubs', 'Trade & Services'),
('7999', 'Office of Trade & Services', 'Amusement & Recreation Services, NEC', 'Trade & Services'),
('8200', 'Office of Trade & Services', 'Educational Services', 'Trade & Services'),
('8300', 'Office of Trade & Services', 'Social Services', 'Trade & Services'),
('8351', 'Office of Trade & Services', 'Child Day Care Services', 'Trade & Services'),
('8600', 'Office of Trade & Services', 'Membership Organizations', 'Trade & Services'),
('8900', 'Office of Trade & Services', 'Services, NEC', 'Trade & Services'),
('5031', 'Office of Trade & Services', 'Lumber & Construction Materials, Wholesale', 'Trade & Services'),
('5072', 'Office of Trade & Services', 'Hardware & Plumbing & Heating Equipment, Wholesale', 'Trade & Services'),
('7331', 'Office of Trade & Services', 'Mailing, Reproduction & Stenographic Services', 'Trade & Services'),
('7830', 'Office of Trade & Services', 'Motion Picture & Videotape Distribution', 'Trade & Services'),
('8111', 'Office of Trade & Services', 'Legal Services', 'Trade & Services'),
('0100', 'Other', 'Crops', 'Other'),
('0200', 'Other', 'Livestock & Animal Specialties', 'Other'),
('0700', 'Other', 'Agricultural Services', 'Other'),
('0800', 'Other', 'Forestry', 'Other'),
('0900', 'Other', 'Fishing, Hunting & Trapping', 'Other'),
('8880', 'Other', 'American Depositary Receipts', 'Other'),
('8888', 'Other', 'Foreign Governments', 'Other'),
('9111', 'Other', 'Executive Offices', 'Other'),
('9199', 'Other', 'General Government, NEC', 'Other'),
('9311', 'Other', 'Finance, Taxation & Monetary Policy', 'Other'),
('9500', 'Other', 'Environmental Quality & Housing', 'Other'),
('9611', 'Other', 'Administration of General Economic Programs', 'Other'),
('9621', 'Other', 'Regulation & Administration of Transportation', 'Other'),
('9631', 'Other', 'Regulation of Utilities', 'Other'),
('9651', 'Other', 'Regulation of Misc Commercial Sectors', 'Other'),
('9711', 'Other', 'National Security', 'Other'),
('9995', 'Other', 'Nonclassifiable Establishments', 'Other');


-- =============================================================================
-- SECTION 3: PYTHON UDFs
-- =============================================================================

-- Strips HTML/XML tags, XBRL metadata, decodes entities, normalizes whitespace
CREATE OR REPLACE FUNCTION CLEAN_TEXT("RAW_TEXT" VARCHAR)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'clean_text'
AS $$
import re

ENTITY_MAP = {
    160: ' ', 8211: '-', 8212: '-', 8216: "'", 8217: "'", 8218: "'",
    8220: '"', 8221: '"', 8222: '"', 8226: '*', 8230: '...', 9679: '*',
    9744: '[ ]', 9745: '[x]', 9746: '[x]', 174: '(R)', 169: '(C)',
    176: ' degrees ', 8364: 'EUR', 163: 'GBP', 165: 'JPY', 38: '&',
}

def _decode_entity(m):
    code = int(m.group(1))
    if code in ENTITY_MAP: return ENTITY_MAP[code]
    if 32 <= code <= 126: return chr(code)
    if 126 < code < 65536:
        c = chr(code)
        if c.isprintable(): return c
    return ' '

def _decode_hex_entity(m):
    code = int(m.group(1), 16)
    if code in ENTITY_MAP: return ENTITY_MAP[code]
    if 32 <= code <= 126: return chr(code)
    if 126 < code < 65536:
        c = chr(code)
        if c.isprintable(): return c
    return ' '

def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ''
    text = re.sub(r'<ix:header>.*?</ix:header>', ' ', raw_text, count=1, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    for entity, char in [('&nbsp;',' '),('&amp;','&'),('&lt;','<'),
                          ('&gt;','>'),('&quot;','"'),('&#39;',"'"),
                          ('&ndash;','-'),('&mdash;','-'),('&bull;','*')]:
        text = text.replace(entity, char)
    text = re.sub(r'&#(\d+);', _decode_entity, text)
    text = re.sub(r'&#x([0-9a-fA-F]+);', _decode_hex_entity, text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
$$;

-- Section-aware chunking (1500 chars, 200 overlap)
CREATE OR REPLACE FUNCTION CHUNK_FILING(
    "CONTENT_TEXT" VARCHAR,
    "FORM_TYPE" VARCHAR,
    "MAX_CHARS" NUMBER(38,0) DEFAULT 1500,
    "OVERLAP_CHARS" NUMBER(38,0) DEFAULT 200
)
RETURNS ARRAY
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'chunk_filing'
AS '
import re

SECTION_PATTERNS = {
    ''10-K'': [
        (r''item\\s+1[^a-z\\d]'',  ''Business''),
        (r''item\\s+1a[^a-z\\d]'', ''Risk Factors''),
        (r''item\\s+1b[^a-z\\d]'', ''Unresolved Staff Comments''),
        (r''item\\s+2[^a-z\\d]'',  ''Properties''),
        (r''item\\s+3[^a-z\\d]'',  ''Legal Proceedings''),
        (r''item\\s+7[^a-z\\d]'',  ''MD&A''),
        (r''item\\s+7a[^a-z\\d]'', ''Market Risk''),
        (r''item\\s+8[^a-z\\d]'',  ''Financial Statements''),
        (r''item\\s+9a[^a-z\\d]'', ''Controls and Procedures''),
    ],
    ''10-Q'': [
        (r''item\\s+1[^a-z\\d]'',  ''Financial Statements''),
        (r''item\\s+2[^a-z\\d]'',  ''MD&A''),
        (r''item\\s+3[^a-z\\d]'',  ''Market Risk''),
        (r''item\\s+1a[^a-z\\d]'', ''Risk Factors''),
        (r''item\\s+4[^a-z\\d]'',  ''Controls and Procedures''),
    ],
    ''8-K'': [
        (r''item\\s+1\\.01'', ''Material Agreement''),
        (r''item\\s+1\\.02'', ''Termination of Agreement''),
        (r''item\\s+2\\.01'', ''Completion of Acquisition''),
        (r''item\\s+2\\.02'', ''Results of Operations''),
        (r''item\\s+2\\.05'', ''Departure of Officers''),
        (r''item\\s+5\\.02'', ''Director/Officer Changes''),
        (r''item\\s+7\\.01'', ''Regulation FD Disclosure''),
        (r''item\\s+8\\.01'', ''Other Events''),
        (r''item\\s+9\\.01'', ''Financial Statements and Exhibits''),
    ],
}

def find_sections(text, form_type):
    lower = text.lower()
    patterns = SECTION_PATTERNS.get(form_type.split(''/'')[0].upper(), [])
    boundaries = []
    for pattern, label in patterns:
        for m in re.finditer(pattern, lower):
            boundaries.append((m.start(), label))
    boundaries.sort(key=lambda x: x[0])
    deduped = []
    prev_label = None
    for pos, label in boundaries:
        if label != prev_label:
            deduped.append((pos, label))
            prev_label = label
    return deduped

def chunk_filing(content_text, form_type, max_chars, overlap_chars):
    if not content_text:
        return []
    text = content_text
    sections = find_sections(text, form_type)
    chunks = []
    chunk_index = 0
    if not sections:
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            ct = text[start:end].strip()
            if ct:
                chunks.append({''section_name'': ''Document'', ''chunk_index'': chunk_index, ''chunk_text'': ct})
                chunk_index += 1
            start += max_chars - overlap_chars
        return chunks
    for i, (sec_start, label) in enumerate(sections):
        sec_end = sections[i+1][0] if i+1 < len(sections) else len(text)
        section_text = text[sec_start:sec_end]
        start = 0
        while start < len(section_text):
            end = min(start + max_chars, len(section_text))
            ct = section_text[start:end].strip()
            if ct:
                chunks.append({''section_name'': label, ''chunk_index'': chunk_index, ''chunk_text'': ct})
                chunk_index += 1
            start += max_chars - overlap_chars
    return chunks
';


-- =============================================================================
-- SECTION 4: INGESTION STORED PROCEDURES
-- =============================================================================

-- Downloads a single day's feed archive, parses SEC headers, inserts filings
CREATE OR REPLACE PROCEDURE LOAD_FEED_ARCHIVE(
    FEED_DATE VARCHAR,
    USER_AGENT VARCHAR DEFAULT 'YourOrg SEC-Filing-Project admin@company.com'
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'requests')
HANDLER = 'load_feed_archive'
EXTERNAL_ACCESS_INTEGRATIONS = (SEC_EDGAR_EAI)
EXECUTE AS CALLER
AS $$
import requests
import tarfile
import io
import re
import time
import pandas as pd
from datetime import datetime, timezone

TARGET_FORMS = {
    '10-K', '10-K/A', '10-KT', '10-KSB',
    '10-Q', '10-Q/A', '10-QSB',
    '8-K',  '8-K/A'
}
MAX_TEXT_CHARS = 16_000_000

def parse_sec_header(text):
    header = {}
    snippet = text[:5000]
    m = re.search(r'CENTRAL INDEX KEY:\s*(\d+)', snippet)
    if not m: m = re.search(r'<CIK>(\d+)', snippet)
    if m: header['CIK'] = m.group(1).zfill(10)
    m = re.search(r'COMPANY CONFORMED NAME:\s*(.+)', snippet)
    if not m: m = re.search(r'<CONFORMED-NAME>([^<\n]+)', snippet)
    if m: header['COMPANY_NAME'] = m.group(1).strip()[:500]
    m = re.search(r'FORM TYPE:\s*(.+)', snippet)
    if not m: m = re.search(r'<TYPE>([^\s<]+)', snippet)
    if m: header['FORM_TYPE'] = m.group(1).strip()
    m = re.search(r'FILED AS OF DATE:\s*(\d{8})', snippet)
    if not m: m = re.search(r'<FILING-DATE>(\d{8})', snippet)
    if m:
        try:
            dt = datetime.strptime(m.group(1), '%Y%m%d').replace(tzinfo=timezone.utc)
            header['FILED_AT'] = dt.strftime('%Y-%m-%d %H:%M:%S +0000')
        except ValueError: pass
    m = re.search(r'CONFORMED PERIOD OF REPORT:\s*(\d{8})', snippet)
    if not m: m = re.search(r'<PERIOD>(\d{8})', snippet)
    if m: header['PERIOD_OF_REPORT'] = m.group(1)
    m = re.search(r'STANDARD INDUSTRIAL CLASSIFICATION:.*\[(\d+)\]', snippet)
    if not m: m = re.search(r'<ASSIGNED-SIC>(\d+)', snippet)
    if m: header['SIC_CODE'] = m.group(1).zfill(4)
    m = re.search(r'ACCESSION NUMBER:\s*(\S+)', snippet)
    if not m: m = re.search(r'<ACCESSION-NUMBER>([^\s<]+)', snippet)
    if m: header['ACCESSION_NO'] = m.group(1).strip()
    return header

def load_feed_archive(session, feed_date: str, user_agent: str) -> str:
    db = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
    schema = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
    fqn = f"{db}.{schema}"
    FLUSH_EVERY = 100

    dt = datetime.strptime(feed_date, '%Y-%m-%d')
    year, quarter = dt.year, (dt.month - 1) // 3 + 1
    date_compact = dt.strftime('%Y%m%d')
    url = f"https://www.sec.gov/Archives/edgar/Feed/{year}/QTR{quarter}/{date_compact}.nc.tar.gz"
    headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}

    content = None
    expected_size = 0
    download_seconds = 0
    for attempt in range(3):
        t0 = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=600, stream=True)
            if resp.status_code == 404:
                session.sql(f"MERGE INTO {fqn}._FEED_INGEST_LOG t USING (SELECT '{feed_date}' AS feed_date) s ON t.feed_date = s.feed_date WHEN NOT MATCHED THEN INSERT (feed_date, loaded, status, started_at, updated_at) VALUES (s.feed_date, 0, 'SKIPPED_404', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()) WHEN MATCHED AND t.status NOT IN ('DONE','SKIPPED_404') THEN UPDATE SET status='SKIPPED_404', updated_at=CURRENT_TIMESTAMP()").collect()
                return f"No feed archive for {feed_date} (HTTP 404)"
            if resp.status_code != 200:
                return f"ERROR: HTTP {resp.status_code} for {feed_date}"
            expected_size = int(resp.headers.get('Content-Length', 0))
            chunks_dl = []
            for chunk in resp.iter_content(chunk_size=10*1024*1024):
                chunks_dl.append(chunk)
            content = b''.join(chunks_dl)
            download_seconds = round(time.time() - t0, 1)
            break
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            download_seconds = round(time.time() - t0, 1)
            if attempt == 2:
                return f"ERROR: Download failed after 3 attempts for {feed_date}"
            time.sleep(30 * (attempt + 1))

    session.sql(f"MERGE INTO {fqn}._FEED_INGEST_LOG t USING (SELECT '{feed_date}' AS feed_date) s ON t.feed_date = s.feed_date WHEN NOT MATCHED THEN INSERT (feed_date, loaded, status, started_at, updated_at) VALUES (s.feed_date, 0, 'DOWNLOADING', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()) WHEN MATCHED AND t.status != 'DONE' THEN UPDATE SET status='DOWNLOADING', updated_at=CURRENT_TIMESTAMP()").collect()

    def _flush_batch(idx_rows, cnt_rows):
        if not idx_rows: return
        df_index = pd.DataFrame(idx_rows).drop_duplicates(subset=['ACCESSION_NO'])
        tmp_idx = f"{fqn}._FEED_INDEX_TMP"
        session.create_dataframe(df_index).write.mode("overwrite").save_as_table(tmp_idx, table_type="temporary")
        session.sql(f"INSERT INTO {fqn}.FILING_INDEX (ACCESSION_NO, CIK, COMPANY_NAME, FORM_TYPE, FILED_AT, PRIMARY_DOC_URL, FILING_INDEX_URL, IS_AMENDMENT, PERIOD_OF_REPORT, SIC_CODE) SELECT t.ACCESSION_NO, t.CIK, t.COMPANY_NAME, t.FORM_TYPE, t.FILED_AT::TIMESTAMP_TZ, t.PRIMARY_DOC_URL, t.FILING_INDEX_URL, t.IS_AMENDMENT::BOOLEAN, TRY_TO_DATE(t.PERIOD_OF_REPORT, 'YYYYMMDD'), t.SIC_CODE FROM {tmp_idx} t WHERE NOT EXISTS (SELECT 1 FROM {fqn}.FILING_INDEX fi WHERE fi.ACCESSION_NO = t.ACCESSION_NO)").collect()
        session.sql(f"UPDATE {fqn}.FILING_INDEX fi SET PERIOD_OF_REPORT = COALESCE(fi.PERIOD_OF_REPORT, TRY_TO_DATE(t.PERIOD_OF_REPORT, 'YYYYMMDD')), SIC_CODE = COALESCE(fi.SIC_CODE, t.SIC_CODE) FROM {tmp_idx} t WHERE fi.ACCESSION_NO = t.ACCESSION_NO AND (fi.PERIOD_OF_REPORT IS NULL OR fi.SIC_CODE IS NULL)").collect()
        df_content = pd.DataFrame(cnt_rows).drop_duplicates(subset=['ACCESSION_NO'])
        tmp_cnt = f"{fqn}._FEED_CONTENT_TMP"
        session.create_dataframe(df_content).write.mode("overwrite").save_as_table(tmp_cnt, table_type="temporary")
        session.sql(f"INSERT INTO {fqn}.FILING_CONTENT (ACCESSION_NO, CONTENT_TEXT, STAGE_FILE_PATH, FILE_SIZE_BYTES, FILE_FORMAT, PARSE_STATUS, PARSE_ERROR) SELECT t.ACCESSION_NO, t.CONTENT_TEXT, t.STAGE_FILE_PATH, t.FILE_SIZE_BYTES::NUMBER, t.FILE_FORMAT, t.PARSE_STATUS, t.PARSE_ERROR FROM {tmp_cnt} t WHERE NOT EXISTS (SELECT 1 FROM {fqn}.FILING_CONTENT fc WHERE fc.ACCESSION_NO = t.ACCESSION_NO)").collect()
        session.sql(f"UPDATE {fqn}.FILING_INDEX fi SET DOWNLOADED_AT = CURRENT_TIMESTAMP() WHERE fi.ACCESSION_NO IN (SELECT ACCESSION_NO FROM {tmp_cnt}) AND fi.DOWNLOADED_AT IS NULL").collect()
        session.sql(f"DROP TABLE IF EXISTS {tmp_idx}").collect()
        session.sql(f"DROP TABLE IF EXISTS {tmp_cnt}").collect()

    index_rows, content_rows = [], []
    skipped, total_loaded = 0, 0
    try:
        tar_bytes = io.BytesIO(content)
        with tarfile.open(fileobj=tar_bytes, mode='r:gz') as tar:
            for member in tar.getmembers():
                if not member.isfile(): continue
                f = tar.extractfile(member)
                if f is None: continue
                try: raw_text = f.read().decode('latin-1', errors='replace')
                except: skipped += 1; continue
                hdr = parse_sec_header(raw_text)
                form_type = hdr.get('FORM_TYPE', '')
                if form_type not in TARGET_FORMS: skipped += 1; continue
                accession_no = hdr.get('ACCESSION_NO')
                if not accession_no:
                    parts = member.name.split('/')
                    if len(parts) >= 3: accession_no = parts[-1].replace('.txt', '')
                if not accession_no: skipped += 1; continue
                cik = hdr.get('CIK', '0000000000')
                company_name = hdr.get('COMPANY_NAME', '')
                filed_at = hdr.get('FILED_AT')
                primary_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession_no.replace('-', '')}/{accession_no}.txt"
                index_rows.append({'ACCESSION_NO': accession_no, 'CIK': cik, 'COMPANY_NAME': company_name, 'FORM_TYPE': form_type, 'FILED_AT': filed_at, 'PRIMARY_DOC_URL': primary_url[:1000], 'FILING_INDEX_URL': None, 'IS_AMENDMENT': '/' in form_type, 'PERIOD_OF_REPORT': hdr.get('PERIOD_OF_REPORT'), 'SIC_CODE': hdr.get('SIC_CODE')})
                text_match = re.search(r'<TEXT>(.*?)</TEXT>', raw_text, re.DOTALL)
                doc_content = text_match.group(1) if text_match else raw_text
                content_rows.append({'ACCESSION_NO': accession_no, 'CONTENT_TEXT': doc_content[:MAX_TEXT_CHARS], 'STAGE_FILE_PATH': None, 'FILE_SIZE_BYTES': len(raw_text), 'FILE_FORMAT': 'FEED', 'PARSE_STATUS': 'PENDING', 'PARSE_ERROR': None})
                if len(index_rows) >= FLUSH_EVERY:
                    _flush_batch(index_rows, content_rows)
                    total_loaded += len(index_rows)
                    index_rows, content_rows = [], []
                    session.sql(f"UPDATE {fqn}._FEED_INGEST_LOG SET loaded={total_loaded}, status='LOADING', updated_at=CURRENT_TIMESTAMP() WHERE feed_date='{feed_date}'").collect()
    except Exception as e:
        if index_rows:
            _flush_batch(index_rows, content_rows)
            total_loaded += len(index_rows)
        session.sql(f"UPDATE {fqn}._FEED_INGEST_LOG SET loaded={total_loaded}, status='PARTIAL', updated_at=CURRENT_TIMESTAMP() WHERE feed_date='{feed_date}'").collect()
        return f"ERROR parsing tar.gz (loaded {total_loaded}): {str(e)[:300]}"

    if index_rows:
        _flush_batch(index_rows, content_rows)
        total_loaded += len(index_rows)

    if total_loaded == 0:
        return f"No target filings in archive for {feed_date}. Skipped: {skipped}"

    session.sql(f"UPDATE {fqn}._FEED_INGEST_LOG SET loaded={total_loaded}, status='DONE', updated_at=CURRENT_TIMESTAMP() WHERE feed_date='{feed_date}'").collect()
    return f"Feed {feed_date}: loaded {total_loaded} filings, skipped {skipped}. Download: {expected_size/(1024*1024):.0f}MB in {download_seconds}s"
$$;


-- Loops weekdays in a date range, calling LOAD_FEED_ARCHIVE for each
CREATE OR REPLACE PROCEDURE LOAD_FEED_DATE_RANGE(
    START_DATE VARCHAR,
    END_DATE VARCHAR,
    USER_AGENT VARCHAR DEFAULT 'YourOrg SEC-Filing-Project admin@company.com'
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    cur_date DATE;
    end_dt DATE;
    result VARCHAR;
    loaded INT DEFAULT 0;
    skipped INT DEFAULT 0;
    day_status VARCHAR;
BEGIN
    cur_date := TO_DATE(:START_DATE);
    end_dt := TO_DATE(:END_DATE);
    WHILE (:cur_date <= :end_dt) DO
        IF (DAYOFWEEK(:cur_date) NOT IN (0, 6)) THEN
            SELECT COALESCE(MAX(STATUS), '') INTO :day_status
            FROM _FEED_INGEST_LOG WHERE FEED_DATE = :cur_date;
            IF (:cur_date > CURRENT_DATE()) THEN
                skipped := skipped + 1;
            ELSEIF (:day_status IN ('DONE', 'SKIPPED_404')) THEN
                skipped := skipped + 1;
            ELSE
                CALL LOAD_FEED_ARCHIVE(TO_VARCHAR(:cur_date, 'YYYY-MM-DD'), :USER_AGENT);
                result := (SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));
                IF (NOT CONTAINS(:result, 'ERROR') AND NOT CONTAINS(:result, 'No target')) THEN
                    loaded := loaded + 1;
                ELSE
                    skipped := skipped + 1;
                END IF;
            END IF;
        END IF;
        cur_date := DATEADD('day', 1, :cur_date);
    END WHILE;
    RETURN 'Feed range complete: ' || :loaded || ' days loaded, ' || :skipped || ' skipped';
END;
$$;


-- Bulk ticker enrichment via SEC company_tickers.json (one HTTP call, ~12K mappings)
CREATE OR REPLACE PROCEDURE ENRICH_TICKERS_BULK(
    USER_AGENT VARCHAR DEFAULT 'YourOrg SEC-Filing-Project admin@company.com'
)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'requests')
HANDLER = 'enrich_tickers_bulk'
EXTERNAL_ACCESS_INTEGRATIONS = (SEC_EDGAR_EAI)
EXECUTE AS CALLER
AS $$
import requests
import json

def enrich_tickers_bulk(session, user_agent: str) -> str:
    db = session.sql("SELECT CURRENT_DATABASE()").collect()[0][0]
    schema = session.sql("SELECT CURRENT_SCHEMA()").collect()[0][0]
    fqn = f"{db}.{schema}"
    headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}

    resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=60)
    if resp.status_code != 200:
        return f"ERROR: SEC returned status {resp.status_code}"

    data = resp.json()
    seen_ciks = {}
    for entry in data.values():
        cik = str(entry.get('cik_str', '')).zfill(10)
        ticker = entry.get('ticker', '')
        if cik and ticker and cik not in seen_ciks:
            seen_ciks[cik] = ticker
    mappings = list(seen_ciks.items())
    if not mappings:
        return "ERROR: No mappings found in company_tickers.json"

    total_updated = 0
    batch_size = 5000
    for i in range(0, len(mappings), batch_size):
        batch = mappings[i:i + batch_size]
        values_list = ", ".join(
            f"('{cik}', '{ticker.replace(chr(39), chr(39)+chr(39))}')"
            for cik, ticker in batch
        )
        result = session.sql(f"MERGE INTO {fqn}.FILING_INDEX tgt USING (SELECT COLUMN1 AS CIK, COLUMN2 AS TICKER FROM VALUES {values_list}) src ON tgt.CIK = src.CIK AND tgt.TICKER IS NULL WHEN MATCHED THEN UPDATE SET tgt.TICKER = src.TICKER, tgt.TICKER_CHECKED_AT = CURRENT_TIMESTAMP()").collect()
        rows = result[0]['number of rows updated'] if result else 0
        total_updated += rows

    return f"Bulk enrichment: {len(mappings)} CIK->ticker mappings, {total_updated} filings updated"
$$;

CREATE OR REPLACE VIEW V_SIGNAL_EXCERPT AS
SELECT
    fc.ACCESSION_NO,
    fi.COMPANY_NAME,
    fi.TICKER,
    fi.FORM_TYPE,
    fi.FILED_AT,
    fi.PERIOD_OF_REPORT,
    fi.IS_AMENDMENT,
    fi.INDUSTRY_SECTOR,
    fi.INDUSTRY_TITLE,
    CASE
        WHEN fi.FORM_TYPE IN ('10-K','10-Q','10-K/A','10-Q/A','10-KT')
             AND ce.targeted_excerpt IS NOT NULL
             AND LENGTH(ce.targeted_excerpt) > 500
        THEN LEFT(ce.targeted_excerpt, 16000)
        ELSE LEFT(CLEAN_TEXT(fc.CONTENT_TEXT), 16000)
    END AS EXCERPT
FROM FILING_CONTENT fc
JOIN FILING_INDEX fi ON fi.ACCESSION_NO = fc.ACCESSION_NO
LEFT JOIN (
    SELECT ck.ACCESSION_NO,
        COALESCE(LEFT(LISTAGG(
            CASE WHEN ck.SECTION_NAME = 'Risk Factors' THEN ck.CHUNK_TEXT END, ' '
        ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 3000), '') ||
        COALESCE(LEFT(LISTAGG(
            CASE WHEN ck.SECTION_NAME = 'MD&A' THEN ck.CHUNK_TEXT END, ' '
        ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 5000), '') ||
        COALESCE(LEFT(LISTAGG(
            CASE WHEN ck.SECTION_NAME = 'Financial Statements' AND ck.CHUNK_INDEX <= 3 THEN ck.CHUNK_TEXT END, ' '
        ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 3000), '') ||
        COALESCE(LEFT(LISTAGG(
            CASE WHEN ck.SECTION_NAME = 'Business' THEN ck.CHUNK_TEXT END, ' '
        ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 3000), '') ||
        COALESCE(LEFT(LISTAGG(
            CASE WHEN ck.SECTION_NAME = 'Market Risk' THEN ck.CHUNK_TEXT END, ' '
        ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 2000), '')
        AS targeted_excerpt
    FROM FILING_CHUNKS ck
    GROUP BY ck.ACCESSION_NO
) ce ON ce.ACCESSION_NO = fc.ACCESSION_NO
WHERE fc.CONTENT_TEXT IS NOT NULL;


-- =============================================================================
-- SECTION 5: MASTER PIPELINE PROCEDURE
-- =============================================================================

CREATE OR REPLACE PROCEDURE RUN_PIPELINE(
    P_START_DATE VARCHAR,
    P_END_DATE VARCHAR,
    P_USER_AGENT VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    wh_name VARCHAR;
    result VARCHAR;
    msg VARCHAR DEFAULT '';
BEGIN
    wh_name := (SELECT CURRENT_WAREHOUSE());

    -- =========================================================================
    -- PHASE 1: INGEST 
    -- =========================================================================
    EXECUTE IMMEDIATE 'ALTER WAREHOUSE ' || :wh_name || ' SET WAREHOUSE_SIZE = ''LARGE'' WAREHOUSE_TYPE = ''SNOWPARK-OPTIMIZED''';

    CALL LOAD_FEED_DATE_RANGE(:P_START_DATE, :P_END_DATE, :P_USER_AGENT);
    result := (SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));
    msg := :result;

    -- =========================================================================
    -- PHASE 2: ENRICH (single HTTP call + SQL UPDATEs — SMALL is sufficient)
    -- =========================================================================
    EXECUTE IMMEDIATE 'ALTER WAREHOUSE ' || :wh_name || ' SET WAREHOUSE_SIZE = ''SMALL'' WAREHOUSE_TYPE = ''STANDARD''';

    CALL ENRICH_TICKERS_BULK(:P_USER_AGENT);
    result := (SELECT * FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));
    msg := :msg || ' | ' || :result;

    -- Map SIC codes to industry sector
    UPDATE FILING_INDEX fi
    SET INDUSTRY_SECTOR = sc.SECTOR,
        INDUSTRY_TITLE = sc.INDUSTRY_TITLE
    FROM SIC_CODES sc
    WHERE fi.SIC_CODE = sc.SIC_CODE
      AND fi.INDUSTRY_SECTOR IS NULL;

    -- =========================================================================
    -- PHASE 3: CHUNK (Python UDF — SMALL handles fine for <1K filings)
    -- =========================================================================
    INSERT INTO FILING_CHUNKS (CHUNK_ID, ACCESSION_NO, COMPANY_NAME, TICKER, FORM_TYPE,
                               FILED_AT, SECTION_NAME, CHUNK_INDEX, CHUNK_TEXT, TOKEN_COUNT,
                               INDUSTRY_SECTOR, INDUSTRY_TITLE, PERIOD_OF_REPORT)
    SELECT
        fc.ACCESSION_NO || '_' || c.VALUE:chunk_index::VARCHAR  AS CHUNK_ID,
        fc.ACCESSION_NO,
        fi.COMPANY_NAME,
        fi.TICKER,
        fi.FORM_TYPE,
        fi.FILED_AT,
        c.VALUE:section_name::VARCHAR   AS SECTION_NAME,
        c.VALUE:chunk_index::NUMBER     AS CHUNK_INDEX,
        c.VALUE:chunk_text::VARCHAR     AS CHUNK_TEXT,
        LENGTH(c.VALUE:chunk_text::VARCHAR) / 4  AS TOKEN_COUNT,
        fi.INDUSTRY_SECTOR,
        fi.INDUSTRY_TITLE,
        fi.PERIOD_OF_REPORT
    FROM FILING_CONTENT fc
    JOIN FILING_INDEX fi ON fi.ACCESSION_NO = fc.ACCESSION_NO,
    LATERAL FLATTEN(CHUNK_FILING(CLEAN_TEXT(fc.CONTENT_TEXT), fi.FORM_TYPE)) c
    WHERE fc.PARSE_STATUS = 'PENDING'
      AND fc.CONTENT_TEXT IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM FILING_CHUNKS ch WHERE ch.ACCESSION_NO = fc.ACCESSION_NO);

    UPDATE FILING_CONTENT SET PARSE_STATUS = 'CHUNKED'
    WHERE PARSE_STATUS = 'PENDING'
      AND ACCESSION_NO IN (SELECT DISTINCT ACCESSION_NO FROM FILING_CHUNKS);

    -- =========================================================================
    -- PHASE 4: AI SIGNAL EXTRACTION (Cortex AI runs on separate infra, SMALL is fine)
    -- =========================================================================

    -- Pre-claim: mark filings we're about to process (prevents duplicates on re-run)
    UPDATE FILING_CONTENT SET SIGNAL_STATUS = 'PROCESSING'
    WHERE SIGNAL_STATUS = 'PENDING'
      AND CONTENT_TEXT IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM FILING_SIGNALS sg WHERE sg.ACCESSION_NO = FILING_CONTENT.ACCESSION_NO);

    -- Extract signals using section-targeted excerpts (V_SIGNAL_EXCERPT)
    INSERT INTO FILING_SIGNALS
        (SIGNAL_ID, ACCESSION_NO, COMPANY_NAME, TICKER, FORM_TYPE,
         SIGNAL_DATE, PERIOD_OF_REPORT, EVENT_TYPE, SENTIMENT, SUMMARY,
         KEY_METRICS, RISK_FLAGS, MATERIAL_ITEMS, INDUSTRY_SECTOR, INDUSTRY_TITLE,
         EXTRACTION_MODEL, IS_AMENDMENT)
    WITH source AS (
        SELECT
            v.ACCESSION_NO, v.COMPANY_NAME, v.TICKER, v.FORM_TYPE, v.FILED_AT,
            v.PERIOD_OF_REPORT, v.IS_AMENDMENT, v.INDUSTRY_SECTOR, v.INDUSTRY_TITLE,
            v.EXCERPT
        FROM V_SIGNAL_EXCERPT v
        JOIN FILING_CONTENT fc ON fc.ACCESSION_NO = v.ACCESSION_NO
        WHERE fc.SIGNAL_STATUS = 'PROCESSING'
    ),
    extracted AS (
        SELECT s.*,
            SNOWFLAKE.CORTEX.AI_EXTRACT(
                text => s.excerpt,
                responseFormat => {
                    'event_type':     'string - one of: Earnings, M&A, Leadership Change, Risk Disclosure, Guidance Update, Regulatory, Capital Markets, Bankruptcy, Other',
                    'sentiment':      'string - one of: POSITIVE, NEGATIVE, NEUTRAL, MIXED',
                    'summary':        'string - 2-3 sentence summary of the most material information',
                    'key_metrics':    'object - financial figures: revenue, net_income, eps, guidance, yoy_change',
                    'risk_flags':     'array of strings - specific risk categories mentioned',
                    'material_items': 'array of strings - for 8-Ks: Item numbers reported'
                }
            ) AS ai_result
        FROM source s
    )
    SELECT
        e.ACCESSION_NO || '_sig',
        e.ACCESSION_NO, e.COMPANY_NAME, e.TICKER, e.FORM_TYPE, e.FILED_AT,
        e.PERIOD_OF_REPORT,
        COALESCE(
            NULLIF(e.ai_result:response:event_type::VARCHAR, 'None'),
            CASE WHEN e.FORM_TYPE='10-K' THEN 'Annual Report'
                 WHEN e.FORM_TYPE='10-Q' THEN 'Quarterly Report'
                 WHEN e.FORM_TYPE='8-K'  THEN 'Current Report'
                 ELSE 'Other' END
        ),
        COALESCE(NULLIF(e.ai_result:response:sentiment::VARCHAR, 'None'), 'NEUTRAL'),
        NULLIF(e.ai_result:response:summary::TEXT, 'None'),
        NULLIF(e.ai_result:response:key_metrics::VARCHAR, 'None'),
        CASE WHEN e.ai_result:response:risk_flags::VARCHAR = 'None' THEN NULL
             ELSE e.ai_result:response:risk_flags::ARRAY END,
        CASE WHEN e.ai_result:response:material_items::VARCHAR = 'None' THEN NULL
             ELSE e.ai_result:response:material_items::ARRAY END,
        e.INDUSTRY_SECTOR, e.INDUSTRY_TITLE, 'arctic-extract', e.IS_AMENDMENT
    FROM extracted e
    WHERE e.ai_result IS NOT NULL;

    -- Finalize: mark successfully extracted
    UPDATE FILING_CONTENT SET SIGNAL_STATUS = 'EXTRACTED'
    WHERE SIGNAL_STATUS = 'PROCESSING'
      AND ACCESSION_NO IN (SELECT ACCESSION_NO FROM FILING_SIGNALS);

    -- Reset any that failed (so they retry next run)
    UPDATE FILING_CONTENT SET SIGNAL_STATUS = 'PENDING'
    WHERE SIGNAL_STATUS = 'PROCESSING';

    -- =========================================================================
    -- PHASE 5: METRICS + GUIDANCE (AI_COMPLETE — still SMALL warehouse)
    -- =========================================================================

    -- Key metrics (revenue, EPS, net_income) from keyword-targeted Financial/MD&A chunks
    UPDATE FILING_SIGNALS fs
    SET REVENUE    = TRY_TO_NUMBER(PARSE_JSON(clean_json):revenue::VARCHAR, 18, 2),
        NET_INCOME = TRY_TO_NUMBER(PARSE_JSON(clean_json):net_income::VARCHAR, 18, 2),
        EPS        = TRY_TO_NUMBER(PARSE_JSON(clean_json):eps::VARCHAR, 10, 4),
        YOY_CHANGE = NULLIF(PARSE_JSON(clean_json):yoy_change::VARCHAR, 'null')
    FROM (
        SELECT SIGNAL_ID,
            REGEXP_REPLACE(metrics, '```(json)?\\s*|```\\s*$', '') AS clean_json
        FROM (
            SELECT
                sg.SIGNAL_ID,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.3-70b',
                    'Extract key financial metrics from this SEC filing excerpt. Only extract explicitly stated numbers. If a metric is not found, return null. IMPORTANT: SEC filings state their reporting unit (e.g., "in thousands", "in millions"). Convert all values to millions USD. Examples: header says "in thousands" and revenue shows $178,882 -> return 178.882. header says "in millions" and revenue shows $2,142.3 -> return 2142.3. Return ONLY a valid JSON object with keys: revenue (number in millions USD or null), net_income (number in millions USD or null), eps (earnings per share as decimal or null), yoy_change (percentage string like "+15%" or null). No explanation, no markdown fences.' ||
                    CHR(10) || CHR(10) || me.excerpt
                ) AS metrics
            FROM FILING_SIGNALS sg
            JOIN (
                SELECT fi.ACCESSION_NO,
                    LEFT(LISTAGG(
                        CASE WHEN LOWER(ck.CHUNK_TEXT) LIKE '%revenue%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%net income%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%net loss%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%earnings per share%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%diluted%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%total net sales%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%in thousands%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%in millions%'
                        THEN ck.CHUNK_TEXT END, ' '
                    ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 16000) AS excerpt
                FROM FILING_INDEX fi
                JOIN FILING_CHUNKS ck ON ck.ACCESSION_NO = fi.ACCESSION_NO
                WHERE ck.SECTION_NAME IN ('Financial Statements', 'MD&A', 'Results of Operations')
                  AND fi.FORM_TYPE IN ('10-K', '10-Q')
                GROUP BY fi.ACCESSION_NO
                HAVING excerpt IS NOT NULL AND LENGTH(excerpt) > 200
            ) me ON me.ACCESSION_NO = sg.ACCESSION_NO
            WHERE sg.REVENUE IS NULL
              AND sg.FORM_TYPE IN ('10-K', '10-Q')
        )
    ) m
    WHERE fs.SIGNAL_ID = m.SIGNAL_ID
      AND TRY_PARSE_JSON(m.clean_json) IS NOT NULL;

    -- Forward guidance from keyword-targeted MD&A/Business chunks
    UPDATE FILING_SIGNALS fs
    SET FORWARD_GUIDANCE = NULLIF(PARSE_JSON(clean_json):guidance::VARCHAR, 'null')
    FROM (
        SELECT SIGNAL_ID,
            REGEXP_REPLACE(guidance, '```(json)?\\s*|```\\s*$', '') AS clean_json
        FROM (
            SELECT
                sg.SIGNAL_ID,
                SNOWFLAKE.CORTEX.COMPLETE(
                    'llama3.3-70b',
                    'Extract forward-looking financial guidance from this SEC filing excerpt. Look for: specific revenue/earnings targets, growth rate expectations, margin guidance, or outlook statements for future periods. Return the exact forward guidance statement as a brief summary. Return null if no forward-looking financial guidance is stated. Do NOT return accounting standards or historical results as guidance. Return ONLY a valid JSON object with key "guidance" containing a concise summary, or {"guidance": null} if none found. No markdown fences.' ||
                    CHR(10) || CHR(10) || ge.excerpt
                ) AS guidance
            FROM FILING_SIGNALS sg
            JOIN (
                SELECT fi.ACCESSION_NO,
                    LEFT(LISTAGG(
                        CASE WHEN LOWER(ck.CHUNK_TEXT) LIKE '%we expect%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%outlook%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%we anticipate%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%forecast%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%full year%expect%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%we now expect%'
                             OR LOWER(ck.CHUNK_TEXT) LIKE '%guidance%range%'
                        THEN ck.CHUNK_TEXT END, ' '
                    ) WITHIN GROUP (ORDER BY ck.CHUNK_INDEX), 16000) AS excerpt
                FROM FILING_INDEX fi
                JOIN FILING_CHUNKS ck ON ck.ACCESSION_NO = fi.ACCESSION_NO
                WHERE ck.SECTION_NAME IN ('MD&A', 'Results of Operations', 'Business')
                  AND fi.FORM_TYPE IN ('10-K', '10-Q')
                GROUP BY fi.ACCESSION_NO
                HAVING excerpt IS NOT NULL AND LENGTH(excerpt) > 200
            ) ge ON ge.ACCESSION_NO = sg.ACCESSION_NO
            WHERE sg.FORWARD_GUIDANCE IS NULL
              AND sg.FORM_TYPE IN ('10-K', '10-Q')
        )
    ) g
    WHERE fs.SIGNAL_ID = g.SIGNAL_ID
      AND TRY_PARSE_JSON(g.clean_json) IS NOT NULL;

    -- =========================================================================
    -- PHASE 6: NORMALIZE + PROPAGATE
    -- =========================================================================

    -- Normalize event types (97+ AI variants → 12 canonical categories)
    UPDATE FILING_SIGNALS
    SET EVENT_TYPE_NORMALIZED = CASE
        WHEN EVENT_TYPE IN ('Earnings','M&A','Leadership Change','Risk Disclosure',
                           'Guidance Update','Regulatory','Capital Markets','Bankruptcy',
                           'Annual Report','Quarterly Report','Current Report','Other')
            THEN EVENT_TYPE
        WHEN EVENT_TYPE ILIKE '%acqui%' OR EVENT_TYPE ILIKE '%merger%' OR EVENT_TYPE ILIKE '%disposition%'
            OR EVENT_TYPE ILIKE '%change in control%' THEN 'M&A'
        WHEN EVENT_TYPE ILIKE '%leadership%' OR EVENT_TYPE ILIKE '%chief%' OR EVENT_TYPE ILIKE '%officer%'
            THEN 'Leadership Change'
        WHEN EVENT_TYPE ILIKE '%regulation%' OR EVENT_TYPE ILIKE '%compliance%' OR EVENT_TYPE ILIKE '%audit%'
            OR EVENT_TYPE ILIKE '%accountant%' OR EVENT_TYPE ILIKE '%ESG%' THEN 'Regulatory'
        WHEN EVENT_TYPE ILIKE '%dividend%' OR EVENT_TYPE ILIKE '%issuance%' OR EVENT_TYPE ILIKE '%repurchase%'
            OR EVENT_TYPE ILIKE '%capital%' OR EVENT_TYPE ILIKE '%credit%' OR EVENT_TYPE ILIKE '%notes%'
            THEN 'Capital Markets'
        WHEN EVENT_TYPE ILIKE '%guidance%' OR EVENT_TYPE ILIKE '%forward%look%' OR EVENT_TYPE ILIKE '%outlook%'
            OR EVENT_TYPE ILIKE '%update%' THEN 'Guidance Update'
        WHEN EVENT_TYPE ILIKE '%risk%' THEN 'Risk Disclosure'
        WHEN EVENT_TYPE ILIKE '%bankrupt%' OR EVENT_TYPE ILIKE '%shell%' THEN 'Bankruptcy'
        ELSE 'Other'
    END
    WHERE EVENT_TYPE_NORMALIZED IS NULL;

    -- Propagate metadata to chunks and signals
    UPDATE FILING_CHUNKS ch
    SET TICKER = fi.TICKER,
        INDUSTRY_SECTOR = fi.INDUSTRY_SECTOR,
        INDUSTRY_TITLE = fi.INDUSTRY_TITLE,
        PERIOD_OF_REPORT = fi.PERIOD_OF_REPORT
    FROM FILING_INDEX fi
    WHERE ch.ACCESSION_NO = fi.ACCESSION_NO
      AND (ch.TICKER IS NULL OR ch.INDUSTRY_SECTOR IS NULL);

    UPDATE FILING_SIGNALS sg
    SET TICKER = fi.TICKER,
        INDUSTRY_SECTOR = fi.INDUSTRY_SECTOR,
        INDUSTRY_TITLE = fi.INDUSTRY_TITLE
    FROM FILING_INDEX fi
    WHERE sg.ACCESSION_NO = fi.ACCESSION_NO
      AND (sg.TICKER IS NULL OR sg.INDUSTRY_SECTOR IS NULL);

    -- =========================================================================
    -- DONE: suspend warehouse to stop billing
    -- =========================================================================
    EXECUTE IMMEDIATE 'ALTER WAREHOUSE ' || :wh_name || ' SUSPEND';

    msg := :msg || ' | Pipeline complete. Warehouse suspended.';
    RETURN :msg;
END;
$$;


-- =============================================================================
-- SECTION 6: RUN IT
-- =============================================================================
-- Full pipeline (ingest + enrich + AI signals):
CALL RUN_PIPELINE('2025-02-03', '2025-02-03', 'YourOrg SEC-Filing-Demo your_name@company.com');
