/*=============================================================================
  09 - STRUCTURED DATA: Providers, Patients, Claims & Appointments
  Healthcare AI Intelligence Pipeline

  Structured/transactional data that Cortex Analyst will query via the
  semantic view. Includes synthetic sample data for demo purposes.

  Depends on: 01 (database/schemas)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA ANALYTICS;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- 1. PROVIDERS — doctors, specialists, facilities
-----------------------------------------------------------------------
CREATE OR REPLACE TABLE ANALYTICS.PROVIDERS (
    PROVIDER_ID     NUMBER PRIMARY KEY,
    PROVIDER_NAME   VARCHAR        NOT NULL,
    SPECIALTY       VARCHAR(100)   NOT NULL,
    FACILITY_NAME   VARCHAR(200),
    CITY            VARCHAR(100),
    STATE           VARCHAR(50),
    NPI_NUMBER      VARCHAR(20)    COMMENT 'National Provider Identifier',
    IS_ACTIVE       BOOLEAN        DEFAULT TRUE
);

INSERT INTO ANALYTICS.PROVIDERS VALUES
  (1,  'Dr. Sarah Chen',       'Internal Medicine',    'Mercy General Hospital',        'Hartford',      'CT', '1234567890', TRUE),
  (2,  'Dr. James Okafor',     'Cardiology',           'Mercy General Hospital',        'Hartford',      'CT', '1234567891', TRUE),
  (3,  'Dr. Maria Rodriguez',  'Orthopedics',          'St. Luke''s Medical Center',    'New Haven',     'CT', '1234567892', TRUE),
  (4,  'Dr. Robert Kim',       'Neurology',            'Yale New Haven Hospital',       'New Haven',     'CT', '1234567893', TRUE),
  (5,  'Dr. Aisha Patel',      'Oncology',             'Hartford Healthcare Cancer',    'Hartford',      'CT', '1234567894', TRUE),
  (6,  'Dr. David Thompson',   'Psychiatry',           'Silver Hill Hospital',          'New Canaan',    'CT', '1234567895', TRUE),
  (7,  'Dr. Lisa Wang',        'Pediatrics',           'Connecticut Children''s',       'Hartford',      'CT', '1234567896', TRUE),
  (8,  'Dr. Michael Johnson',  'Dermatology',          'Dermatology Associates',        'Stamford',      'CT', '1234567897', TRUE),
  (9,  'Dr. Emily Foster',     'Radiology',            'Mercy General Hospital',        'Hartford',      'CT', '1234567898', TRUE),
  (10, 'Dr. Ahmed Hassan',     'Pulmonology',          'Bridgeport Hospital',           'Bridgeport',    'CT', '1234567899', TRUE),
  (11, 'Dr. Priya Sharma',     'Endocrinology',        'Yale New Haven Hospital',       'New Haven',     'CT', '1234567900', TRUE),
  (12, 'Dr. Carlos Mendez',    'Gastroenterology',     'St. Luke''s Medical Center',    'New Haven',     'CT', '1234567901', TRUE);

-----------------------------------------------------------------------
-- 2. PATIENTS
-----------------------------------------------------------------------
CREATE OR REPLACE TABLE ANALYTICS.PATIENTS (
    PATIENT_ID      NUMBER PRIMARY KEY,
    FIRST_NAME      VARCHAR(100)   NOT NULL,
    LAST_NAME       VARCHAR(100)   NOT NULL,
    DATE_OF_BIRTH   DATE           NOT NULL,
    GENDER          VARCHAR(20),
    CITY            VARCHAR(100),
    STATE           VARCHAR(50),
    ZIP_CODE        VARCHAR(10),
    INSURANCE_PLAN  VARCHAR(200),
    PRIMARY_PROVIDER_ID NUMBER     COMMENT 'FK to PROVIDERS',
    REGISTERED_DATE DATE           DEFAULT CURRENT_DATE()
);

INSERT INTO ANALYTICS.PATIENTS VALUES
  (101, 'John',     'Whitfield',  '1958-03-15', 'Male',   'Hartford',     'CT', '06101', 'Aetna PPO',                1,  '2023-01-10'),
  (102, 'Margaret', 'Sullivan',   '1965-11-22', 'Female', 'New Haven',    'CT', '06510', 'UnitedHealth Choice Plus', 2,  '2023-02-14'),
  (103, 'David',    'Park',       '1972-07-08', 'Male',   'Stamford',     'CT', '06901', 'Cigna Open Access',        3,  '2023-03-20'),
  (104, 'Sandra',   'Williams',   '1980-01-30', 'Female', 'Bridgeport',   'CT', '06601', 'Anthem Blue Cross',        1,  '2023-04-05'),
  (105, 'Roberto',  'Garcia',     '1955-09-12', 'Male',   'Hartford',     'CT', '06103', 'Medicare Advantage',       2,  '2023-05-18'),
  (106, 'Linda',    'Brown',      '1948-12-05', 'Female', 'New Canaan',   'CT', '06840', 'Medicare Advantage',       5,  '2023-06-01'),
  (107, 'Wei',      'Zhang',      '1990-04-17', 'Male',   'New Haven',    'CT', '06511', 'Aetna PPO',                4,  '2023-07-12'),
  (108, 'Patricia', 'O''Brien',   '1975-08-25', 'Female', 'Hartford',     'CT', '06105', 'UnitedHealth Choice Plus', 6,  '2023-08-03'),
  (109, 'Michael',  'Torres',     '1988-02-14', 'Male',   'Bridgeport',   'CT', '06604', 'Cigna Open Access',        10, '2023-09-15'),
  (110, 'Amara',    'Johnson',    '2015-06-20', 'Female', 'Hartford',     'CT', '06106', 'Anthem Blue Cross',        7,  '2023-10-22'),
  (111, 'Catherine','Lee',        '1960-10-03', 'Female', 'Stamford',     'CT', '06902', 'Aetna PPO',                11, '2023-11-08'),
  (112, 'James',    'Murphy',     '1970-05-19', 'Male',   'New Haven',    'CT', '06512', 'Medicare Advantage',       12, '2024-01-05'),
  (113, 'Fatima',   'Ali',        '1985-03-28', 'Female', 'Hartford',     'CT', '06102', 'UnitedHealth Choice Plus', 1,  '2024-02-14'),
  (114, 'Thomas',   'Anderson',   '1952-07-11', 'Male',   'New Canaan',   'CT', '06840', 'Medicare Advantage',       2,  '2024-03-01'),
  (115, 'Yuki',     'Tanaka',     '1995-01-25', 'Female', 'New Haven',    'CT', '06513', 'Cigna Open Access',        8,  '2024-04-10');

-----------------------------------------------------------------------
-- 3. CLAIMS
-----------------------------------------------------------------------
CREATE OR REPLACE TABLE ANALYTICS.CLAIMS (
    CLAIM_ID         NUMBER PRIMARY KEY,
    PATIENT_ID       NUMBER         NOT NULL COMMENT 'FK to PATIENTS',
    PROVIDER_ID      NUMBER         NOT NULL COMMENT 'FK to PROVIDERS',
    SERVICE_DATE     DATE           NOT NULL,
    CLAIM_DATE       DATE           NOT NULL,
    PROCEDURE_CODE   VARCHAR(20)    COMMENT 'CPT code',
    PROCEDURE_DESC   VARCHAR(500),
    DIAGNOSIS_CODE   VARCHAR(20)    COMMENT 'ICD-10 code',
    DIAGNOSIS_DESC   VARCHAR(500),
    BILLED_AMOUNT    NUMBER(10,2),
    ALLOWED_AMOUNT   NUMBER(10,2),
    PAID_AMOUNT      NUMBER(10,2),
    PATIENT_RESPONSIBILITY NUMBER(10,2),
    CLAIM_STATUS     VARCHAR(50)    COMMENT 'Approved, Denied, Pending, Under Review',
    DENIAL_REASON    VARCHAR(500)
);

INSERT INTO ANALYTICS.CLAIMS VALUES
  (1001, 101, 1, '2024-06-10', '2024-06-12', '99213', 'Office visit - established patient (moderate)',     'I10',    'Essential hypertension',                     185.00, 142.00, 113.60, 28.40, 'Approved', NULL),
  (1002, 101, 2, '2024-06-15', '2024-06-17', '93000', 'Electrocardiogram (ECG)',                           'I10',    'Essential hypertension',                     350.00, 280.00, 224.00, 56.00, 'Approved', NULL),
  (1003, 102, 2, '2024-07-01', '2024-07-03', '93306', 'Echocardiography, transthoracic',                   'I25.10', 'Atherosclerotic heart disease',              1200.00, 960.00, 768.00, 192.00, 'Approved', NULL),
  (1004, 103, 3, '2024-07-10', '2024-07-12', '27447', 'Total knee replacement',                            'M17.11', 'Primary osteoarthritis, right knee',         45000.00, 38000.00, 30400.00, 7600.00, 'Approved', NULL),
  (1005, 104, 1, '2024-07-20', '2024-07-22', '99214', 'Office visit - established patient (moderate-high)', 'J06.9',  'Acute upper respiratory infection',          250.00, 195.00, 156.00, 39.00, 'Approved', NULL),
  (1006, 105, 2, '2024-08-05', '2024-08-07', '93458', 'Left heart catheterization',                        'I25.10', 'Atherosclerotic heart disease',              8500.00, 7200.00, 5760.00, 1440.00, 'Approved', NULL),
  (1007, 106, 5, '2024-08-12', '2024-08-14', '88305', 'Surgical pathology - tissue exam',                   'C50.911','Malignant neoplasm, right breast',           425.00, 340.00, 272.00, 68.00, 'Approved', NULL),
  (1008, 107, 4, '2024-08-20', '2024-08-22', '95819', 'Electroencephalogram (EEG) with sleep',             'G40.909','Epilepsy, unspecified',                       800.00, 640.00, 512.00, 128.00, 'Approved', NULL),
  (1009, 108, 6, '2024-09-01', '2024-09-03', '90834', 'Psychotherapy, 45 minutes',                         'F33.0',  'Major depressive disorder, recurrent, mild', 200.00, 180.00, 144.00, 36.00, 'Approved', NULL),
  (1010, 109, 10,'2024-09-10', '2024-09-12', '94010', 'Spirometry (pulmonary function test)',               'J45.20', 'Mild intermittent asthma',                   275.00, 220.00, 176.00, 44.00, 'Approved', NULL),
  (1011, 110, 7, '2024-09-18', '2024-09-20', '99392', 'Preventive visit - age 1-4',                        'Z00.129','Routine child health exam',                  225.00, 200.00, 160.00, 40.00, 'Approved', NULL),
  (1012, 111, 11,'2024-10-01', '2024-10-03', '83036', 'Hemoglobin A1c test',                               'E11.65', 'Type 2 diabetes with hyperglycemia',         85.00,  68.00,  54.40,  13.60, 'Approved', NULL),
  (1013, 112, 12,'2024-10-15', '2024-10-17', '43239', 'Upper GI endoscopy with biopsy',                    'K21.0',  'GERD with esophagitis',                      3200.00, 2700.00, 2160.00, 540.00, 'Approved', NULL),
  (1014, 113, 1, '2024-10-22', '2024-10-24', '99395', 'Preventive visit - age 18-39',                      'Z00.00', 'General adult medical exam',                 275.00, 225.00, 180.00, 45.00, 'Approved', NULL),
  (1015, 114, 2, '2024-11-01', '2024-11-03', '33533', 'Coronary artery bypass graft (CABG)',                'I25.10', 'Atherosclerotic heart disease',              85000.00, 72000.00, 57600.00, 14400.00, 'Approved', NULL),
  (1016, 101, 1, '2024-11-10', '2024-11-12', '99214', 'Office visit - established patient (moderate-high)', 'I10',    'Essential hypertension',                     250.00, 195.00, 156.00, 39.00, 'Approved', NULL),
  (1017, 102, 2, '2024-11-20', '2024-11-22', '93000', 'Electrocardiogram (ECG)',                            'I25.10', 'Atherosclerotic heart disease',              350.00, 280.00, 224.00, 56.00, 'Approved', NULL),
  (1018, 105, 2, '2024-12-01', '2024-12-03', '99215', 'Office visit - established patient (high)',          'I25.10', 'Atherosclerotic heart disease',              375.00, 300.00, 240.00, 60.00, 'Approved', NULL),
  (1019, 106, 5, '2024-12-10', '2024-12-12', '77063', 'Screening mammography, bilateral',                  'Z12.31', 'Screening mammogram',                        285.00, 250.00, 200.00, 50.00, 'Approved', NULL),
  (1020, 108, 6, '2024-12-15', '2024-12-17', '90834', 'Psychotherapy, 45 minutes',                         'F33.1',  'Major depressive disorder, recurrent, moderate', 200.00, 180.00, 144.00, 36.00, 'Pending', NULL),
  (1021, 103, 3, '2025-01-08', '2025-01-10', '99213', 'Office visit - post-op follow-up',                   'M17.11', 'Primary osteoarthritis, right knee',        185.00, 142.00, 113.60, 28.40, 'Approved', NULL),
  (1022, 107, 4, '2025-01-15', '2025-01-17', '70553', 'MRI brain with and without contrast',                'G40.909','Epilepsy, unspecified',                      2800.00, 2200.00, 1760.00, 440.00, 'Approved', NULL),
  (1023, 109, 10,'2025-01-25', '2025-01-27', '99214', 'Office visit - established patient (moderate-high)', 'J45.20', 'Mild intermittent asthma',                  250.00, 195.00, 156.00, 39.00, 'Approved', NULL),
  (1024, 115, 8, '2025-02-01', '2025-02-03', '11102', 'Tangential biopsy of skin',                         'L82.1',  'Seborrheic keratosis',                       350.00, 280.00, 224.00, 56.00, 'Approved', NULL),
  (1025, 113, 9, '2025-02-10', '2025-02-12', '71046', 'Chest X-ray, 2 views',                              'R05.9',  'Cough, unspecified',                         180.00, 145.00, 116.00, 29.00, 'Denied', 'Prior authorization not obtained'),
  (1026, 111, 11,'2025-02-20', '2025-02-22', '80053', 'Comprehensive metabolic panel',                      'E11.65', 'Type 2 diabetes with hyperglycemia',        125.00, 100.00, 80.00,  20.00, 'Approved', NULL),
  (1027, 112, 12,'2025-03-01', '2025-03-03', '99214', 'Office visit - GI follow-up',                        'K21.0',  'GERD with esophagitis',                     250.00, 195.00, 156.00, 39.00, 'Approved', NULL),
  (1028, 104, 1, '2025-03-10', '2025-03-12', '36415', 'Venipuncture (blood draw)',                          'Z00.00', 'General adult medical exam',                 35.00,  28.00,  22.40,  5.60,  'Approved', NULL),
  (1029, 110, 7, '2025-03-15', '2025-03-17', '90460', 'Immunization administration',                       'Z23',    'Immunization encounter',                     65.00,  55.00,  44.00,  11.00, 'Approved', NULL),
  (1030, 114, 2, '2025-03-20', '2025-03-22', '99215', 'Office visit - post-CABG follow-up',                 'I25.10', 'Atherosclerotic heart disease',             375.00, 300.00, 240.00, 60.00, 'Under Review', NULL);

-----------------------------------------------------------------------
-- 4. APPOINTMENTS
-----------------------------------------------------------------------
CREATE OR REPLACE TABLE ANALYTICS.APPOINTMENTS (
    APPOINTMENT_ID   NUMBER PRIMARY KEY,
    PATIENT_ID       NUMBER         NOT NULL,
    PROVIDER_ID      NUMBER         NOT NULL,
    APPOINTMENT_DATE TIMESTAMP_NTZ  NOT NULL,
    APPOINTMENT_TYPE VARCHAR(100)   COMMENT 'In-Person, Telehealth, Phone',
    VISIT_REASON     VARCHAR(500),
    DURATION_MINUTES NUMBER,
    STATUS           VARCHAR(50)    COMMENT 'Completed, Cancelled, No-Show, Scheduled',
    HAS_AUDIO_RECORDING BOOLEAN    DEFAULT FALSE COMMENT 'Whether consultation was recorded',
    HAS_DOCUMENT     BOOLEAN       DEFAULT FALSE COMMENT 'Whether a document was generated'
);

INSERT INTO ANALYTICS.APPOINTMENTS VALUES
  (2001, 101, 1, '2024-06-10 09:00:00', 'In-Person',  'Hypertension follow-up, medication review',         30, 'Completed',  TRUE,  TRUE),
  (2002, 101, 2, '2024-06-15 10:30:00', 'In-Person',  'Cardiology referral — ECG and evaluation',          45, 'Completed',  TRUE,  TRUE),
  (2003, 102, 2, '2024-07-01 08:00:00', 'In-Person',  'Echocardiogram and cardiac assessment',             60, 'Completed',  FALSE, TRUE),
  (2004, 103, 3, '2024-07-10 07:00:00', 'In-Person',  'Total knee replacement surgery',                    180,'Completed',  FALSE, TRUE),
  (2005, 104, 1, '2024-07-20 14:00:00', 'Telehealth', 'Acute respiratory infection — virtual visit',       20, 'Completed',  TRUE,  TRUE),
  (2006, 105, 2, '2024-08-05 09:00:00', 'In-Person',  'Cardiac catheterization, pre-op assessment',        90, 'Completed',  TRUE,  TRUE),
  (2007, 106, 5, '2024-08-12 11:00:00', 'In-Person',  'Pathology results review — breast biopsy',          30, 'Completed',  TRUE,  TRUE),
  (2008, 107, 4, '2024-08-20 13:00:00', 'In-Person',  'EEG with sleep study — seizure evaluation',         120,'Completed',  FALSE, TRUE),
  (2009, 108, 6, '2024-09-01 15:00:00', 'Telehealth', 'Psychotherapy session — depression management',     45, 'Completed',  TRUE,  FALSE),
  (2010, 109, 10,'2024-09-10 10:00:00', 'In-Person',  'Pulmonary function test — asthma evaluation',       40, 'Completed',  TRUE,  TRUE),
  (2011, 110, 7, '2024-09-18 09:30:00', 'In-Person',  'Well-child check-up, immunizations',                30, 'Completed',  FALSE, TRUE),
  (2012, 111, 11,'2024-10-01 08:30:00', 'In-Person',  'Diabetes management — A1c review',                  30, 'Completed',  TRUE,  TRUE),
  (2013, 112, 12,'2024-10-15 07:30:00', 'In-Person',  'Upper GI endoscopy — GERD evaluation',              60, 'Completed',  FALSE, TRUE),
  (2014, 113, 1, '2024-10-22 11:00:00', 'In-Person',  'Annual physical exam',                              45, 'Completed',  TRUE,  TRUE),
  (2015, 114, 2, '2024-11-01 06:00:00', 'In-Person',  'Coronary artery bypass surgery',                    300,'Completed',  FALSE, TRUE),
  (2016, 101, 1, '2024-11-10 09:00:00', 'Telehealth', 'BP check and medication adjustment',                20, 'Completed',  TRUE,  TRUE),
  (2017, 108, 6, '2024-12-15 15:00:00', 'Telehealth', 'Psychotherapy session — progress review',           45, 'Completed',  TRUE,  FALSE),
  (2018, 105, 2, '2024-12-01 10:00:00', 'In-Person',  'Post-catheterization follow-up',                    30, 'Completed',  TRUE,  TRUE),
  (2019, 115, 8, '2025-02-01 14:30:00', 'In-Person',  'Skin lesion evaluation and biopsy',                 25, 'Completed',  FALSE, TRUE),
  (2020, 114, 2, '2025-03-20 09:00:00', 'In-Person',  'Post-CABG cardiac rehabilitation follow-up',        45, 'Completed',  TRUE,  TRUE),
  (2021, 103, 3, '2025-04-15 10:00:00', 'In-Person',  'Post-op knee rehab assessment',                     30, 'Scheduled',  FALSE, FALSE),
  (2022, 107, 4, '2025-04-20 13:00:00', 'Telehealth', 'Epilepsy medication review',                        30, 'Scheduled',  FALSE, FALSE),
  (2023, 106, 5, '2025-04-25 11:00:00', 'In-Person',  'Oncology follow-up — 6-month imaging',              45, 'Scheduled',  FALSE, FALSE),
  (2024, 109, 10,'2025-05-01 10:00:00', 'Phone',      'Asthma action plan review',                         15, 'Scheduled',  FALSE, FALSE);

-----------------------------------------------------------------------
-- 5. VERIFY ROW COUNTS
-----------------------------------------------------------------------
SELECT 'PROVIDERS' AS TBL, COUNT(*) AS "ROWS" FROM ANALYTICS.PROVIDERS
UNION ALL SELECT 'PATIENTS', COUNT(*) FROM ANALYTICS.PATIENTS
UNION ALL SELECT 'CLAIMS', COUNT(*) FROM ANALYTICS.CLAIMS
UNION ALL SELECT 'APPOINTMENTS', COUNT(*) FROM ANALYTICS.APPOINTMENTS;
