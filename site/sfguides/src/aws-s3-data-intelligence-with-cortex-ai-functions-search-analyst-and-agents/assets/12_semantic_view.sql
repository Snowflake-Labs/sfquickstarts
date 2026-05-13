/*=============================================================================
  12 - SEMANTIC VIEW FOR CORTEX ANALYST
  Healthcare AI Intelligence Pipeline

  Enables natural-language queries over structured healthcare data:
    - Patient demographics and registration
    - Provider directory and specialties
    - Claims data (billing, diagnosis, procedures, status)
    - Appointments (scheduling, visit types, recording status)

  Depends on: 09 (structured data tables)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA ANALYTICS;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- SEMANTIC VIEW
-----------------------------------------------------------------------
CREATE OR REPLACE SEMANTIC VIEW ANALYTICS.HEALTHCARE_ANALYTICS

  TABLES (
    PATIENTS AS ANALYTICS.PATIENTS
      PRIMARY KEY (PATIENT_ID)
      COMMENT = 'Patient demographics and registration',

    PROVIDERS AS ANALYTICS.PROVIDERS
      PRIMARY KEY (PROVIDER_ID)
      COMMENT = 'Provider directory and specialties',

    CLAIMS AS ANALYTICS.CLAIMS
      PRIMARY KEY (CLAIM_ID)
      COMMENT = 'Claims data including billing, diagnosis, procedures, and status',

    APPOINTMENTS AS ANALYTICS.APPOINTMENTS
      PRIMARY KEY (APPOINTMENT_ID)
      COMMENT = 'Appointment scheduling, visit types, and recording status'
  )

  RELATIONSHIPS (
    patients_to_providers AS
      PATIENTS (PRIMARY_PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID),
    claims_to_patients AS
      CLAIMS (PATIENT_ID) REFERENCES PATIENTS (PATIENT_ID),
    claims_to_providers AS
      CLAIMS (PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID),
    appointments_to_patients AS
      APPOINTMENTS (PATIENT_ID) REFERENCES PATIENTS (PATIENT_ID),
    appointments_to_providers AS
      APPOINTMENTS (PROVIDER_ID) REFERENCES PROVIDERS (PROVIDER_ID)
  )

  DIMENSIONS (
    PATIENTS.first_name AS FIRST_NAME
      COMMENT = 'Patient first name',
    PATIENTS.last_name AS LAST_NAME
      COMMENT = 'Patient last name',
    PATIENTS.date_of_birth AS DATE_OF_BIRTH
      COMMENT = 'Patient date of birth',
    PATIENTS.gender AS GENDER
      COMMENT = 'Patient gender (Male, Female)',
    PATIENTS.city AS CITY
      COMMENT = 'Patient city of residence',
    PATIENTS.state AS STATE
      COMMENT = 'Patient state of residence',
    PATIENTS.zip_code AS ZIP_CODE
      COMMENT = 'Patient zip code',
    PATIENTS.insurance_plan AS INSURANCE_PLAN
      COMMENT = 'Insurance plan name (Aetna PPO, UnitedHealth Choice Plus, Cigna Open Access, Anthem Blue Cross, Medicare Advantage)',
    PATIENTS.registered_date AS REGISTERED_DATE
      COMMENT = 'Date patient was registered in the system',

    PROVIDERS.provider_name AS PROVIDER_NAME
      COMMENT = 'Full name of the doctor or provider',
    PROVIDERS.specialty AS SPECIALTY
      COMMENT = 'Medical specialty (Internal Medicine, Cardiology, Orthopedics, Neurology, Oncology, Psychiatry, Pediatrics, Dermatology, Radiology, Pulmonology, Endocrinology, Gastroenterology)',
    PROVIDERS.facility_name AS FACILITY_NAME
      COMMENT = 'Hospital or clinic name where provider practices',
    PROVIDERS.provider_city AS PROVIDERS.CITY
      COMMENT = 'City where the facility is located',
    PROVIDERS.provider_state AS PROVIDERS.STATE
      COMMENT = 'State where the facility is located',
    PROVIDERS.npi_number AS NPI_NUMBER
      COMMENT = 'National Provider Identifier number',
    PROVIDERS.is_active AS IS_ACTIVE
      COMMENT = 'Whether the provider is currently active',

    CLAIMS.service_date AS SERVICE_DATE
      COMMENT = 'Date the medical service was performed',
    CLAIMS.claim_date AS CLAIM_DATE
      COMMENT = 'Date the claim was submitted',
    CLAIMS.procedure_code AS PROCEDURE_CODE
      COMMENT = 'CPT procedure code',
    CLAIMS.procedure_desc AS PROCEDURE_DESC
      COMMENT = 'Description of the medical procedure',
    CLAIMS.diagnosis_code AS DIAGNOSIS_CODE
      COMMENT = 'ICD-10 diagnosis code',
    CLAIMS.diagnosis_desc AS DIAGNOSIS_DESC
      COMMENT = 'Description of the diagnosis',
    CLAIMS.claim_status AS CLAIM_STATUS
      COMMENT = 'Status of the claim: Approved, Denied, Pending, Under Review',
    CLAIMS.denial_reason AS DENIAL_REASON
      COMMENT = 'Reason for claim denial if applicable',

    APPOINTMENTS.appointment_date AS APPOINTMENT_DATE
      COMMENT = 'Date and time of the appointment',
    APPOINTMENTS.appointment_type AS APPOINTMENT_TYPE
      COMMENT = 'Type of visit: In-Person, Telehealth, Phone',
    APPOINTMENTS.visit_reason AS VISIT_REASON
      COMMENT = 'Reason for the visit or chief complaint',
    APPOINTMENTS.status AS STATUS
      COMMENT = 'Appointment status: Completed, Cancelled, No-Show, Scheduled',
    APPOINTMENTS.has_audio_recording AS HAS_AUDIO_RECORDING
      COMMENT = 'Whether the consultation was recorded as audio (TRUE/FALSE)',
    APPOINTMENTS.has_document AS HAS_DOCUMENT
      COMMENT = 'Whether a medical document was generated (TRUE/FALSE)'
  )

  METRICS (
    CLAIMS.total_billed_amount AS SUM(BILLED_AMOUNT)
      COMMENT = 'Total amount billed by the provider in dollars',
    CLAIMS.avg_billed_amount AS AVG(BILLED_AMOUNT)
      COMMENT = 'Average amount billed by the provider in dollars',
    CLAIMS.total_allowed_amount AS SUM(ALLOWED_AMOUNT)
      COMMENT = 'Total amount allowed by the insurance plan in dollars',
    CLAIMS.avg_allowed_amount AS AVG(ALLOWED_AMOUNT)
      COMMENT = 'Average amount allowed by the insurance plan in dollars',
    CLAIMS.total_paid_amount AS SUM(PAID_AMOUNT)
      COMMENT = 'Total amount paid by insurance in dollars',
    CLAIMS.avg_paid_amount AS AVG(PAID_AMOUNT)
      COMMENT = 'Average amount paid by insurance in dollars',
    CLAIMS.total_patient_responsibility AS SUM(PATIENT_RESPONSIBILITY)
      COMMENT = 'Total amount the patient owes (copay, coinsurance, deductible) in dollars',
    CLAIMS.avg_patient_responsibility AS AVG(PATIENT_RESPONSIBILITY)
      COMMENT = 'Average amount the patient owes in dollars',
    CLAIMS.claim_count AS COUNT(CLAIM_ID)
      COMMENT = 'Number of claims',

    APPOINTMENTS.total_duration_minutes AS SUM(DURATION_MINUTES)
      COMMENT = 'Total duration of appointments in minutes',
    APPOINTMENTS.avg_duration_minutes AS AVG(DURATION_MINUTES)
      COMMENT = 'Average duration of appointments in minutes',
    APPOINTMENTS.appointment_count AS COUNT(APPOINTMENT_ID)
      COMMENT = 'Number of appointments',

    PATIENTS.patient_count AS COUNT(PATIENT_ID)
      COMMENT = 'Number of patients',

    PROVIDERS.provider_count AS COUNT(PROVIDER_ID)
      COMMENT = 'Number of providers'
  )

  COMMENT = 'Healthcare analytics semantic view for Cortex Analyst. Covers patients, providers, claims, and appointments.';

-----------------------------------------------------------------------
-- VERIFY
-----------------------------------------------------------------------
SHOW SEMANTIC VIEWS IN SCHEMA ANALYTICS;
DESCRIBE SEMANTIC VIEW ANALYTICS.HEALTHCARE_ANALYTICS;
