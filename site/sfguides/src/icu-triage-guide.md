author: Parshu Anantharam
id: build-a-secure-icu-triage-agent-with-snowflake-cortex
language: en
summary: Build an ICU triage Cortex Agent over structured vitals and unstructured clinical notes, harden it with layered AI security controls, attack it, and evaluate it.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: <optional but modify to link to your repo>
open in snowflake: <optional but modify to link into the product>

# Build a Secure ICU Triage Agent with Snowflake Cortex
<!-- ------------------------ -->
## Overview

Intensive care teams need fast answers that draw on both **structured** telemetry (MAP, lactate, shock index) and **unstructured** documentation (handoff notes, prescription rationale). In this guide you build `ICU_TRIAGE_AGENT`, a Cortex Agent that combines both, using a fully synthetic dataset of 20 patients.

Because clinical data is sensitive, you then harden the agent with six security layers, run simulated attacks against it to prove that each layer works, and finally batch-evaluate the agent's answer quality.

The guide follows two Snowflake Notebooks:

- `icu_triage.ipynb`: data, semantic view, search service, agent, security demos, and evaluation
- `icu_security_hardening.ipynb`: the security layers, one cell per step

> NOTE:
> All data in this guide is synthetic. The agent is a decision-support demo, not a diagnostic or treatment-ordering system.

### Prerequisites
- Familiarity with SQL and Snowflake Notebooks
- Basic understanding of Cortex AI (Cortex Analyst, Cortex Search, Cortex Agents)

### What You'll Learn
- How to model ICU vitals as a **semantic view** for Cortex Analyst
- How to build a multi-index **Cortex Search** service over notes and prescriptions
- How to create a **Cortex Agent** that orchestrates both tools
- How to secure an agent with Cortex AI Guardrails, Restricted Session Scope, agent-aware masking, AI_REDACT, data movement policies, and Multi-Party Approval
- How to run simulated attacks and read the audit trail
- How to evaluate an agent with `EXECUTE_AI_EVALUATION`

### What You'll Need
- A Snowflake account with `ACCOUNTADMIN` access
- **Enterprise Edition** or higher for guardrails, masking, and data movement policies
- **Business Critical Edition** for Multi-Party Approval (optional, Step 7 of the hardening)
- A **second user** with an email address who can approve requests (needed only for Multi-Party Approval)
- Cross-region inference enabled if your region doesn't host the required models

### What You'll Build
- `ICU_TRIAGE_AGENT`: a hardened clinical decision-support agent with audited security controls and a repeatable evaluation run

<!-- ------------------------ -->
## Import the Notebooks

1. In Snowsight, open **Projects » Workspaces**.
2. Upload `icu_triage.ipynb` and `icu_security_hardening.ipynb` to your workspace.
3. Open each notebook and connect it to a notebook service (a default CPU service is fine).

Run the cells in this order:

| Order | Notebook | Cells |
|---|---|---|
| 1 | `icu_triage` | Setup → Cortex Agent |
| 2 | `icu_security_hardening` | Steps 1–6, then Verification (Step 7 last, once) |
| 3 | `icu_triage` | Masking: re-apply → Security Demos → Evidence → Cleanup |
| 4 | `icu_triage` | Agent Evaluation (E1–E7) |

> NOTE:
> The `icu_triage` notebook also contains a **Security Hardening** cell. Skip it and use the `icu_security_hardening` notebook instead, which splits the same work into separate steps you can check one by one.

<!-- ------------------------ -->
## Set Up the Environment

Run the **Setup** cell. It creates a project role, a warehouse, the database and schema, and a stage. It also grants Cortex access to the role.

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS ICU_TRIAGE_ADMIN;

SET CURRENT_USER_NAME = CURRENT_USER();
GRANT ROLE ICU_TRIAGE_ADMIN TO USER IDENTIFIER($CURRENT_USER_NAME);
GRANT CREATE DATABASE ON ACCOUNT TO ROLE ICU_TRIAGE_ADMIN;

CREATE WAREHOUSE IF NOT EXISTS ICU_ANALYTICS_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
GRANT USAGE, OPERATE ON WAREHOUSE ICU_ANALYTICS_WH TO ROLE ICU_TRIAGE_ADMIN;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ICU_TRIAGE_ADMIN;

USE ROLE ICU_TRIAGE_ADMIN;
USE WAREHOUSE ICU_ANALYTICS_WH;
CREATE DATABASE IF NOT EXISTS ICU_TRIAGE_DB;
CREATE SCHEMA IF NOT EXISTS ICU_TRIAGE_DB.CLINICAL_DATA;

CREATE OR REPLACE STAGE ICU_TRIAGE_DB.CLINICAL_DATA.MODEL_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

If your region doesn't host the models, uncomment `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';` in the cell.

<!-- ------------------------ -->
## Load Synthetic Clinical Data

Run these four cells in order:

1. **Ingestion** creates `PATIENT_VITALS` (20 patients: 14 active and 6 discharged) and `PARSED_CLINICAL_NOTES` (20 notes).
2. **Synthetic Prescriptions** creates `PRESCRIPTIONS` (RX-001 to RX-025) with dosing rationale and monitoring parameters.
3. **Scrub patient IDs from free text** removes literal IDs such as `P009` from note and prescription text.
4. **Column Descriptions** adds column comments that help the AI tools.

```sql
CREATE OR REPLACE TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PATIENT_VITALS (
  PATIENT_ID VARCHAR(50),
  VENTILATION_STATUS VARCHAR(10),
  MAP_MMHG INT,
  LACTATE_MMOL_L FLOAT,
  HEART_RATE INT,
  SYSTOLIC_BP INT,
  DISCHARGE_TIMESTAMP TIMESTAMP_NTZ DEFAULT NULL
);

CREATE OR REPLACE TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES (
  NOTE_ID VARCHAR(50),
  PATIENT_ID VARCHAR(50),
  TEXT_CHUNK VARCHAR(16777216),
  DISCHARGE_STATUS VARCHAR(50),
  ACUITY_SCORE VARCHAR(50)
);
```

### Consistent patient identifiers

The agent has two tools: Cortex Analyst reads the vitals and Cortex Search reads the documents. Both must return the **same** patient ID, or the agent can't join a patient's vitals to that patient's notes.

The vitals table keeps the raw ID (`P001`). Later, a masking policy shows agents a hashed surrogate of that ID. The document tables store the surrogate directly, because a masking policy that uses `SYS_CONTEXT` makes Cortex Search refreshes fail.

```sql
UPDATE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES
   SET PATIENT_ID = 'PT-' || SUBSTR(SHA2(PATIENT_ID), 1, 8)
 WHERE PATIENT_ID NOT LIKE 'PT-%';

UPDATE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES
   SET TEXT_CHUNK = REGEXP_REPLACE(TEXT_CHUNK, '\\bP0[0-9]{2}\\b,? ?', '');
```

<!-- ------------------------ -->
## Create the Semantic View

The **Semantic view** cell exposes **active** patients only to Cortex Analyst. It defines synonyms, the metrics MAP, lactate, and shock index, and verified queries.

```sql
CREATE OR REPLACE SEMANTIC VIEW ICU_TRIAGE_DB.CLINICAL_DATA.ICU_TRIAGE_METRICS_VIEW
  TABLES (
    vitals AS (
      SELECT * FROM ICU_TRIAGE_DB.CLINICAL_DATA.PATIENT_VITALS
      WHERE DISCHARGE_TIMESTAMP IS NULL
    )
    COMMENT = 'Live telemetry and acuity metrics for active ICU patients.'
  )
  DIMENSIONS (
    vitals.patient_id AS patient_id
      WITH SYNONYMS = ('MRN', 'patient reference', 'case id'),
    vitals.ventilation_status AS ventilation_status
      WITH SYNONYMS = ('on vent', 'intubated', 'mechanical ventilation')
  )
  METRICS (
    vitals.mean_arterial_pressure AS AVG(MAP_mmHg)
      WITH SYNONYMS = ('MAP', 'perfusion pressure'),
    vitals.lactate_level AS MAX(LACTATE_mmol_L)
      WITH SYNONYMS = ('lactic acid', 'lactate concentration'),
    vitals.shock_index AS MAX(HEART_RATE / SYSTOLIC_BP)
      WITH SYNONYMS = ('shock ratio')
  )
  AI_VERIFIED_QUERIES (
    active_patient_count AS (
      QUESTION 'How many active patients are currently in the ICU?'
      VERIFIED_AT 1729000000
      ONBOARDING_QUESTION TRUE
      SQL 'SELECT COUNT(DISTINCT patient_id) AS active_patient_count FROM __vitals'
    )
  );
```

The notebook cell includes the full comments and three more verified queries: high lactate, MAP by ventilation status, and shock index > 1.0.

<!-- ------------------------ -->
## Create the Cortex Search Service

The **Cortex Search Service** cell builds one search corpus from notes and prescriptions combined (`UNION ALL`). It creates both keyword (text) and vector (semantic) indexes.

```sql
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES SET CHANGE_TRACKING = TRUE;
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PRESCRIPTIONS         SET CHANGE_TRACKING = TRUE;

CREATE OR REPLACE CORTEX SEARCH SERVICE ICU_TRIAGE_DB.CLINICAL_DATA.ICU_PROTOCOL_SEARCH_SERVICE
  TEXT INDEXES TEXT_CONTENT, DOC_ID
  VECTOR INDEXES TEXT_CONTENT (model = 'snowflake-arctic-embed-l-v2.0')
  ATTRIBUTES PATIENT_ID, DOC_TYPE, ACUITY_OR_ROUTE, STATUS_OR_DRUG
  WAREHOUSE = ICU_ANALYTICS_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT NOTE_ID AS DOC_ID, PATIENT_ID, TEXT_CHUNK AS TEXT_CONTENT,
           'clinical_note' AS DOC_TYPE, ACUITY_SCORE AS ACUITY_OR_ROUTE,
           DISCHARGE_STATUS AS STATUS_OR_DRUG
    FROM ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES
    UNION ALL
    SELECT RX_ID, PATIENT_ID, PRESCRIPTION_NOTES,
           'prescription', ROUTE, DRUG_NAME
    FROM ICU_TRIAGE_DB.CLINICAL_DATA.PRESCRIPTIONS
  );

ALTER CORTEX SEARCH SERVICE ICU_TRIAGE_DB.CLINICAL_DATA.ICU_PROTOCOL_SEARCH_SERVICE REFRESH;
```

`ACUITY_OR_ROUTE` and `STATUS_OR_DRUG` each hold two kinds of value. Read them together with `DOC_TYPE`:
- For notes, they hold the acuity score and the discharge status.
- For prescriptions, they hold the route and the drug name.

<!-- ------------------------ -->
## Create the Cortex Agent

The **Cortex Agent** cell creates `ICU_TRIAGE_AGENT` with three tools:

- `analyst_tool`: Cortex Analyst over the semantic view. It is the only source for the active census.
- `search_tool`: Cortex Search over notes and prescriptions, with analytical search enabled
- `data_to_chart`: charts built from tool results

The agent's instructions set clinical safety rules. It must give a decision-support disclaimer, never recommend medication changes, and cite `NOTE_ID`/`RX_ID`. The instructions also set routing rules: patient counts always go to `analyst_tool`, and both tools return IDs in the same `PT-` format.

```sql
USE ROLE ICU_TRIAGE_ADMIN;

CREATE OR REPLACE AGENT ICU_TRIAGE_DB.CLINICAL_DATA.ICU_TRIAGE_AGENT
  COMMENT = '
ICU Triage & Clinical Decision Support Agent

This agent provides clinical intelligence for intensive care unit operations by combining real-time structured patient vitals with unstructured clinical documentation and prescription records.

CAPABILITIES:
- Hemodynamic monitoring: Query mean arterial pressure (MAP), lactate levels, shock index, heart rate, and systolic blood pressure for active ICU patients. Identify patients in shock states or with deteriorating perfusion.
- Ventilation status tracking: Filter and compare metrics for mechanically ventilated vs. spontaneously breathing patients.
- Prescription review: Search 25+ detailed prescription documents covering vasopressors, antibiotics, sedatives, anticoagulants, and other critical ICU medications. Each prescription includes dosing rationale, monitoring parameters, and titration protocols.
- Clinical note analysis: Search bedside assessments, shift handoff summaries, triage observations, and protocol adherence notes.
- Analytical search: Run corpus-wide queries across all clinical documents — count prescriptions by drug class, identify patients on specific therapies, detect trends in prescribing patterns, or aggregate clinical observations across the full ICU census.
- Visualization: Generate charts from query results for clinical dashboards and team briefings.

DATA SCOPE:
- Structured data: PATIENT_VITALS table (active patients only, filtered by DISCHARGE_TIMESTAMP IS NULL) with MAP, lactate, heart rate, systolic BP, ventilation status.
- Unstructured data: Unified corpus of PARSED_CLINICAL_NOTES (bedside notes, handoff summaries) and PRESCRIPTIONS (medication orders with full clinical rationale), indexed for both keyword and semantic search.
- Refresh cadence: Search index refreshes hourly (TARGET_LAG = 1 hour).

IMPORTANT CLINICAL CAVEATS:
- This agent is a decision-support tool, NOT a diagnostic or treatment-ordering system. All outputs must be reviewed by a qualified physician before any clinical action is taken.
- Outputs may be incomplete, delayed, or incorrect. Never use agent responses as the sole basis for treatment decisions, medication changes, or triage escalations.
- The agent queries a synthetic demonstration dataset. In a production deployment, validate data freshness, completeness, and integration with your EHR before clinical use.
- Analytical search results (counts, aggregates) depend on the quality and completeness of the underlying documentation. Missing or inconsistently documented records will affect accuracy.
- Drug interaction checking, allergy verification, and contraindication screening are NOT performed by this agent. These must be handled by your pharmacy information system.
- This agent does not replace clinical judgment, institutional protocols, or regulatory requirements for patient care documentation.
'
  PROFILE = '{"display_name": "ICU Triage Agent", "color": "red"}'
  FROM SPECIFICATION $$
models:
  orchestration: auto

orchestration:
  capabilities:
    analytical_search: true
  budget:
    seconds: 60
    tokens: 32000

instructions:
  response: |
    You are an ICU Triage and Clinical Decision Support AI Assistant.
    Your role is to help intensive care physicians assess clinical priority,
    detect decompensation, and review prescription and documentation data
    across the ICU census.

    CLINICAL SAFETY REQUIREMENTS — FOLLOW THESE IN EVERY RESPONSE:
    1. Begin treatment-related responses with: "CLINICAL DECISION SUPPORT ONLY —
       All findings require independent verification by a qualified physician
       before any clinical action."
    2. Never recommend starting, stopping, or changing a medication. Present data
       only; defer treatment decisions to the attending physician.
    3. When reporting vitals or lab thresholds (e.g., lactate > 4, MAP < 65,
       shock index > 1.0), state the values and the clinical significance but
       do not issue a diagnosis.
    4. If a question falls outside the scope of the available data (e.g., imaging,
       microbiology, allergy history), state clearly that the information is not
       available in this system rather than speculating.
    5. When presenting aggregate or analytical results, note that completeness
       depends on documentation quality — missing records may affect counts.
    6. Never present synthetic/demo data as real patient information. If asked
       whether data is real, clarify that this is a demonstration dataset.

    RESPONSE FORMAT:
    - Use structured markdown tables for patient lists and comparisons.
    - Cite document IDs (NOTE_ID or RX_ID) when referencing specific records.
    - For analytical search results, describe the methodology (search scope,
      filters applied, extraction logic) so clinicians can assess reliability.
  orchestration: |
    For structured metric questions (vitals, MAP, lactate, shock index, patient counts),
    use analyst_tool. For document search (notes, prescriptions, protocols, drug rationale),
    use search_tool. For questions requiring analysis across many documents (e.g., how many
    patients are on vasopressors, what drugs were prescribed for sepsis), use search_tool
    with analytical search enabled.

    CENSUS RULE: For any question about how many patients are in the ICU, the active
    census, or which patients are currently admitted, ALWAYS use analyst_tool. It reads
    only active patients (DISCHARGE_TIMESTAMP IS NULL). Never count patients from
    search_tool documents or from the PATIENT_ID value range — the document corpus also
    covers discharged patients. When a question combines patient counts with documents,
    take the active patient list from analyst_tool first, then use search_tool for evidence.

    PATIENT ID RULE: analyst_tool and search_tool return the SAME patient identifier
    format, 'PT-' followed by 8 hex characters (e.g., PT-df1e4005). A PATIENT_ID from
    analyst_tool can be used directly as a PATIENT_ID filter in search_tool, and vice versa.
  sample_questions:
    - question: "How many active patients are currently in the ICU?"
    - question: "Which patients have dangerously elevated lactate levels?"
    - question: "What is the average MAP for ventilated vs non-ventilated patients?"
    - question: "List all patients who were prescribed vasopressors for septic shock."
    - question: "What are the most commonly prescribed drugs across the ICU?"
    - question: "Which patients have a shock index greater than 1.0?"
    - question: "Summarize the clinical rationale for antibiotic prescriptions in the ICU."
    - question: "How many prescriptions mention renal dose adjustment?"

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "analyst_tool"
      description: "Authoritative source for the active ICU census. Queries structured patient vitals for ACTIVE patients only (discharged patients excluded) and aggregates hemodynamic metrics including MAP, lactate, heart rate, systolic BP, shock index, and ventilation status. Use for every patient count."
  - tool_spec:
      type: "cortex_search"
      name: "search_tool"
      description: "Searches a unified corpus of unstructured ICU clinical notes and prescription documents for both active and discharged patients. Use for protocol lookup, drug rationale, clinical handoff details, and corpus-wide analytical queries over prescriptions and notes. Do not use to count active ICU patients."
  - tool_spec:
      type: "data_to_chart"
      name: "data_to_chart"
      description: "Generates visualizations from data returned by other tools."

tool_resources:
  analyst_tool:
    semantic_view: "ICU_TRIAGE_DB.CLINICAL_DATA.ICU_TRIAGE_METRICS_VIEW"
    execution_environment:
      type: "warehouse"
      warehouse: "ICU_ANALYTICS_WH"
  search_tool:
    search_service: "ICU_TRIAGE_DB.CLINICAL_DATA.ICU_PROTOCOL_SEARCH_SERVICE"
    max_results: "1000"
    id_column: "DOC_ID"
    columns_and_descriptions:
      TEXT_CONTENT:
        description: "Free-text document body. For clinical notes: contains bedside assessments, handoff summaries, protocol adherence observations, and triage reasoning. For prescriptions: contains dosing instructions, monitoring parameters, clinical context, contraindication reviews, lab targets, titration protocols, and duration plans. Sample values include phrases like 'MAP remains below 65 mmHg despite fluid resuscitation', 'Initiating norepinephrine drip at 0.1 mcg/kg/min', 'RASS target -2 to 0'. Use this column for semantic search queries and as input to AI_EXTRACT (drug names, diagnoses, lab targets, monitoring schedules) and AI_FILTER (clinical predicates like vasopressor-dependent, renal dosing, ventilated)."
        type: "string"
        searchable: true
        filterable: false
      DOC_ID:
        description: "Unique document identifier. Format: NOTE_ID for clinical notes (e.g., N001-N020) or RX_ID for prescriptions (e.g., RX-001 to RX-025). Use for deduplication and citation references. Searchable via keyword index for direct document lookup."
        type: "string"
        searchable: true
        filterable: false
      PATIENT_ID:
        description: "Patient surrogate identifier linking documents to patient records. Format: 'PT-' followed by 8 hex characters (e.g., PT-df1e4005). This is IDENTICAL to the PATIENT_ID returned by analyst_tool, so analyst_tool IDs can be used directly as a filter here and documents can be matched to vitals by exact equality. Documents cover BOTH active and discharged patients; this set is NOT the active census. Get the active patient list and counts from analyst_tool."
        type: "string"
        searchable: false
        filterable: true
      DOC_TYPE:
        description: "Document type classifier. Values: 'clinical_note' (bedside assessments, handoff notes, triage observations) or 'prescription' (medication orders with clinical rationale). Use for filtering to isolate notes vs prescriptions. Essential for analytical search queries scoped to one document type."
        type: "string"
        searchable: false
        filterable: true
      ACUITY_OR_ROUTE:
        description: "Dual-purpose attribute. For clinical notes (DOC_TYPE='clinical_note'): acuity score classification. Values: Critical, High, Moderate, Low. For prescriptions (DOC_TYPE='prescription'): route of administration. Values: IV, Subcutaneous, Nebulizer, Oral. Use for filtering by severity level or administration route."
        type: "string"
        searchable: false
        filterable: true
      STATUS_OR_DRUG:
        description: "Dual-purpose attribute. For clinical notes (DOC_TYPE='clinical_note'): discharge status. Values: Discharged, Active, or NULL. For prescriptions (DOC_TYPE='prescription'): drug name. Values include Norepinephrine, Vancomycin, Fentanyl, Propofol, Albuterol, Heparin, Insulin Regular, Amiodarone, Meropenem, Dexmedetomidine, Furosemide, Dobutamine, Mannitol, Ceftriaxone, Azithromycin, and others. Use for filtering by discharge status or by specific medication."
        type: "string"
        searchable: false
        filterable: true
$$;
```

Open the agent in **AI & ML » Agents** and try: *"Which patients have dangerously elevated lactate levels?"*

<!-- ------------------------ -->
## Harden the Agent

Now switch to **`icu_security_hardening.ipynb`**. Run it after the Cortex Agent cell and before the Security Demos. Skip the Security Hardening cell inside `icu_triage`.

| Step | Feature | What it does | Edition |
|---|---|---|---|
| 1 | Cortex AI Guardrails | Scans agent tool calls for prompt injection and jailbreaks | Enterprise |
| 2 | Restricted Session Scope | Makes agent sessions read-only and blocks the admin roles | GA |
| 3 | Agent-aware masking | Hashes `PATIENT_ID` when an agent accesses it | Enterprise |
| 5 | AI_REDACT view | Strips PII from free-text notes | GA |
| 6 | Data Movement Policy | Caps agent access at 500 rows and blocks external `COPY` on PHI | Enterprise |
| 7 | Multi-Party Approval | Requires a second approver to change guardrails or session policies | Business Critical |

Step 4 is a placeholder because Multi-Party Approval runs last, as Step 7.

### Step 1: Cortex AI Guardrails

```sql
USE ROLE ACCOUNTADMIN;
ALTER ACCOUNT SET AI_SETTINGS = $$
guardrails:
  advanced_prompt_injection:
    - enabled: true
$$;
```

### Step 2: Restricted Session Scope

Restricted Session Scope sets a ceiling on what an agent can do on a user's behalf, whatever roles that user holds.

```sql
CREATE SCHEMA IF NOT EXISTS ICU_TRIAGE_DB.GOVERNANCE;

CREATE OR ALTER RESTRICTED SESSION SCOPE ICU_TRIAGE_DB.GOVERNANCE.ICU_AGENT_SCOPE AS $$
privilege_scopes:
  allowed_privileges:
    - privileges: [data read]
      account: [all]
    - privileges: [usage]
      object_types: [agent, cortex search service]
      databases: [ICU_TRIAGE_DB]
    - privileges: [compute usage]
      account: [all]
role_scopes:
  blocked_roles: [ACCOUNTADMIN, SYSADMIN, SECURITYADMIN]
  allow_role_switching: true
$$;

CREATE SESSION POLICY IF NOT EXISTS ICU_TRIAGE_DB.GOVERNANCE.ICU_AGENT_SESSION_POLICY
  AGENT_RESTRICTED_SESSION_SCOPE = 'ICU_TRIAGE_DB.GOVERNANCE.ICU_AGENT_SCOPE';

ALTER ACCOUNT SET SESSION POLICY ICU_TRIAGE_DB.GOVERNANCE.ICU_AGENT_SESSION_POLICY;
```

### Step 3: Agent-aware masking

```sql
CREATE MASKING POLICY IF NOT EXISTS ICU_TRIAGE_DB.GOVERNANCE.PATIENT_ID_AGENT_MASK
AS (val VARCHAR) RETURNS VARCHAR ->
  CASE
    WHEN SYS_CONTEXT('SNOWFLAKE$CURRENT', 'IS_AGENT_ACTIVATED')::BOOLEAN = TRUE
      THEN 'PT-' || SUBSTR(SHA2(val), 1, 8)
    ELSE val
  END;
```

### Step 5: AI_REDACT view

```sql
CREATE OR REPLACE VIEW ICU_TRIAGE_DB.CLINICAL_DATA.REDACTED_CLINICAL_NOTES AS
SELECT NOTE_ID, PATIENT_ID, AI_REDACT(TEXT_CHUNK) AS TEXT_CHUNK,
       DISCHARGE_STATUS, ACUITY_SCORE
FROM ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES;
```

### Step 6: Data movement policies

The movement policy is attached to a `SENSITIVITY` tag, and you tag the clinical tables `'PHI'`. The policy has three rules:
- Agent access is capped at 500 rows.
- `COPY INTO` an external stage is blocked.
- Snowsight downloads of more than 100 rows raise an alert.

```sql
CREATE TAG IF NOT EXISTS ICU_TRIAGE_DB.GOVERNANCE.SENSITIVITY
  ALLOWED_VALUES 'PHI', 'PII', 'INTERNAL'
  PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT;

CREATE OR REPLACE DATA MOVEMENT RULE ICU_TRIAGE_DB.GOVERNANCE.AGENT_PHI_LIMIT
  TYPE = 'AGENT_ACCESS' MAX_ROWS AS () RETURNS INTEGER -> (500);
CREATE OR REPLACE DATA MOVEMENT RULE ICU_TRIAGE_DB.GOVERNANCE.BLOCK_EXTERNAL_EXPORT
  TYPE = 'COPY_INTO_EXTERNAL_STAGE' MAX_ROWS AS () RETURNS INTEGER -> (0);
CREATE OR REPLACE DATA MOVEMENT RULE ICU_TRIAGE_DB.GOVERNANCE.UI_ALERT
  TYPE = 'SNOWSIGHT_UI' MAX_ROWS AS () RETURNS INTEGER -> (100);

CREATE OR REPLACE DATA MOVEMENT POLICY ICU_TRIAGE_DB.GOVERNANCE.PHI_MOVEMENT_POLICY
  ENFORCE_RULES = (ICU_TRIAGE_DB.GOVERNANCE.AGENT_PHI_LIMIT,
                   ICU_TRIAGE_DB.GOVERNANCE.BLOCK_EXTERNAL_EXPORT)
  ALERT_RULES = (ICU_TRIAGE_DB.GOVERNANCE.UI_ALERT);

ALTER TAG ICU_TRIAGE_DB.GOVERNANCE.SENSITIVITY
  SET DATA MOVEMENT POLICY ICU_TRIAGE_DB.GOVERNANCE.PHI_MOVEMENT_POLICY;
```

### Step 7: Multi-Party Approval (run last, once)

Replace the approver usernames with two real users. Because `self_approval_allowed: false`, you can never approve your own request.

```sql
CREATE MULTI PARTY APPROVAL POLICY IF NOT EXISTS ICU_TRIAGE_DB.GOVERNANCE.ICU_MPA_POLICY
AS $$
description: 'Protects ICU agent security controls from unilateral changes'
rules:
  - name: self_protection
    operations: [MODIFY_MULTI_PARTY_APPROVAL]
    approvers:
      users: ['<APPROVER_1>', '<APPROVER_2>']
    required_approvals: 1
    self_approval_allowed: false
  - name: guardrails_and_session_protection
    operations: [MODIFY_CORTEX_GUARDRAILS, MODIFY_SESSION_POLICY]
    approvers:
      users: ['<APPROVER_1>', '<APPROVER_2>']
    required_approvals: 1
    self_approval_allowed: false
$$;

ALTER ACCOUNT SET MULTI PARTY APPROVAL POLICY ICU_TRIAGE_DB.GOVERNANCE.ICU_MPA_POLICY;
```

> NOTE:
> After Step 7 is attached, re-running Steps 1–2 or changing the approval policy needs a second approver.

Finally, run the hardening notebook's **Verification** cell to confirm that each layer is active.

### Return to icu_triage: re-apply masking

Hardening Step 3 also attaches the mask to `PARSED_CLINICAL_NOTES`. A `SYS_CONTEXT` mask on a search source table suspends Cortex Search indexing. Back in `icu_triage`, run the **Masking: re-apply to all three clinical tables** cell. It moves the mask so it sits on `PATIENT_VITALS` only, and it tags all three tables `PHI`.

```sql
USE ROLE ACCOUNTADMIN;
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES MODIFY COLUMN PATIENT_ID UNSET MASKING POLICY;
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PRESCRIPTIONS         MODIFY COLUMN PATIENT_ID UNSET MASKING POLICY;
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PATIENT_VITALS        MODIFY COLUMN PATIENT_ID UNSET MASKING POLICY;
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PATIENT_VITALS        MODIFY COLUMN PATIENT_ID SET MASKING POLICY ICU_TRIAGE_DB.GOVERNANCE.PATIENT_ID_AGENT_MASK;

ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PATIENT_VITALS        SET TAG ICU_TRIAGE_DB.GOVERNANCE.SENSITIVITY = 'PHI';
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PARSED_CLINICAL_NOTES SET TAG ICU_TRIAGE_DB.GOVERNANCE.SENSITIVITY = 'PHI';
ALTER TABLE ICU_TRIAGE_DB.CLINICAL_DATA.PRESCRIPTIONS         SET TAG ICU_TRIAGE_DB.GOVERNANCE.SENSITIVITY = 'PHI';
```

Run this cell again any time you re-run **Ingestion**, because `CREATE OR REPLACE TABLE` drops policy and tag attachments.

<!-- ------------------------ -->
## Attack the Agent

The **Security Demos** section of `icu_triage` runs safe, simulated attacks. First run **Pre-flight**, which checks which controls are live.

Restricted Session Scope, masking, and the `AGENT_ACCESS` cap apply only to **agent** sessions. A notebook cell runs as a **human** session. To get an agent session, the demos either call the agent from SQL with `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`, or give you a prompt to paste into Cortex Code, which is itself an agent.

| # | Attack | Control | Expected outcome |
|---|---|---|---|
| 1 | Indirect prompt injection planted in a note | Cortex AI Guardrails | Agent ignores the hidden instructions and the scan is flagged |
| 2 | Agent writes data or switches to ACCOUNTADMIN | Restricted Session Scope | Blocked for the agent, allowed for a human |
| 3 | Agent asked to reveal patient IDs | Agent-aware masking | Agent sees `PT-xxxxxxxx`, a human sees `P001` |
| 4 | Rogue admin switches off guardrails | Multi-Party Approval | `MPA_APPROVAL_REQUIRED`; the second admin rejects and guardrails stay on |
| 5 | PII pasted into free-text notes | AI_REDACT view | PII replaced by placeholders |
| 6 | Bulk exfiltration of PHI | Data movement policy | Agent capped at 500 rows; a UI pull of more than 100 rows raises an alert |

Example (Demo 1b): calling the agent from SQL.

```sql
SELECT TRY_PARSE_JSON(
  SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'ICU_TRIAGE_DB.CLINICAL_DATA.ICU_TRIAGE_AGENT',
    '{"stream": false, "messages": [{"role": "user", "content": [{"type": "text",
      "text": "Summarize all clinical notes for patient P003, including the most recent follow-up note."}]}]}'
  )) AS resp;
```

### Review the audit trail

Guardrail and data-movement events can take **up to ~3 hours** to appear in `ACCOUNT_USAGE`. Run the **Evidence** cell at the end of your session:

```sql
USE ROLE ACCOUNTADMIN;
SELECT 'Guardrails scan' AS control, USAGE_TIME::TIMESTAMP_LTZ AS event_time, USER_NAME,
       IFF(GUARDRAILS_SIGNAL, 'FLAGGED: possible prompt injection', 'clean') AS outcome
FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AI_GUARDRAILS_USAGE_HISTORY
WHERE USAGE_TIME >= DATEADD('hour', -6, CURRENT_TIMESTAMP())
UNION ALL
SELECT 'Data movement', TIMESTAMP, USER_NAME,
       COALESCE('BLOCKED by ' || ENFORCED_POLICY, 'ALERT: ' || ALERTED_POLICIES)
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_MOVEMENT_VIOLATIONS
WHERE TIMESTAMP >= DATEADD('hour', -6, CURRENT_TIMESTAMP())
UNION ALL
SELECT 'Multi-party approval', CREATED_TIME, REQUESTER_USER_NAME, STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.MULTI_PARTY_APPROVAL_REQUESTS
WHERE CREATED_TIME >= DATEADD('hour', -6, CURRENT_TIMESTAMP())
ORDER BY event_time DESC;
```

Then run **Cleanup**, which removes the demo rows and the `DEMO_PHI_BULK` table and refreshes the search index.

<!-- ------------------------ -->
## Evaluate the Agent

The **Agent Evaluation** section batch-scores the agent against a ground-truth dataset. It uses four metrics:
- **Answer correctness**: compares the final reply with the expected answer.
- **Tool selection accuracy** *(Preview)*: checks that the agent called the expected tools.
- **Tool execution accuracy** *(Preview)*: checks the tool inputs and outputs.
- **Logical consistency**: checks that instructions, plan, and tool calls agree. It needs no ground truth.

1. **E1**: creates `ICU_AGENT_EVAL_INPUTS`, with questions and the expected answers in a `ground_truth_output` field.
2. **E2**: registers the table as the dataset `ICU_AGENT_EVALSET`.
3. **E3**: configures the run. Either use the agent's **Evaluations** tab in Snowsight, or upload an evaluation config YAML to `@ICU_TRIAGE_DB.CLINICAL_DATA.MODEL_STAGE`.
4. **E4–E7**: start the run, check its status, and read the scores.

```sql
USE DATABASE ICU_TRIAGE_DB;
USE SCHEMA CLINICAL_DATA;

CALL EXECUTE_AI_EVALUATION(
  'START',
  OBJECT_CONSTRUCT('run_name', 'icu-baseline-1'),
  '@ICU_TRIAGE_DB.CLINICAL_DATA.MODEL_STAGE/agent_evaluation_config.yaml');

SELECT METRIC_NAME, ROUND(AVG(EVAL_AGG_SCORE), 3) AS avg_score,
       COUNT_IF(ERROR IS NOT NULL) AS errors
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(
       'ICU_TRIAGE_DB', 'CLINICAL_DATA', 'ICU_TRIAGE_AGENT', 'CORTEX AGENT', 'icu-baseline-1'))
GROUP BY METRIC_NAME
ORDER BY METRIC_NAME;
```

Give each iteration a new `run_name` (for example `icu-prompt-v2`), so you can compare runs after you change the instructions or tools.

<!-- ------------------------ -->
## Conclusion And Resources

You built a clinical decision-support agent over hybrid data, added six layers of defense, proved each layer against a simulated attack, and set up a repeatable evaluation loop. Next, try the same pattern on your own governed data.

### What You Learned
- How to combine Cortex Analyst and Cortex Search in one Cortex Agent
- How to keep patient identifiers consistent across agent tools while masking them
- How to layer Guardrails, Restricted Session Scope, masking, AI_REDACT, data movement policies, and Multi-Party Approval
- How to audit security events and evaluate agent quality

### Related Resources
- <link to github code repo>
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [EXECUTE_AI_EVALUATION](https://docs.snowflake.com/en/sql-reference/functions/execute_ai_evaluation)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
