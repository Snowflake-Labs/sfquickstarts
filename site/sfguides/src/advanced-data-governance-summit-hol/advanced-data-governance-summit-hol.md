authors: Ankit Gupta (sfc-gh-ankgupta)
id: advanced-data-governance-summit-hol
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/solution-center/certification/community-sourced, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/compliance-security-discovery-governance, snowflake-site:taxonomy/snowflake-feature/horizon
language: en
summary: Master automated sensitive data discovery and protection at scale — AI-powered classification, Trust Center Data Security UI, AI_REDACT for unstructured PII, and Cortex Code governance skills. 90-minute Snowflake Summit hands-on lab.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol

# Advanced Data Governance: AI-Powered Sensitive Data Discovery and Protection at Scale
<!-- ------------------------ -->
## Overview

Safeguarding sensitive data at scale is nonnegotiable for regulatory compliance. In this essential hands-on lab you will master the art of automated sensitive data discovery and protection. You will leverage the power of AI to classify PII across your data estate, generate robust data protection policies, explore the Trust Center Data Security UI to verify your governance posture, establish an airtight audit trail, and use Cortex Code governance skills to assess maturity and build policies in plain English.

You'll work through a step-by-step guide using a synthetic customer dataset containing names, SSNs, emails, credit cards, phone numbers, and order transactions — a realistic representation of sensitive data in enterprise systems.

**Three personas, one dataset:**

| Persona | Role | Responsibility |
|---------|------|----------------|
| Data Engineer | `HRZN_DATA_ENGINEER` | Creates and loads data assets; explores RBAC |
| Data Governor | `HRZN_DATA_GOVERNOR` | Classifies data; defines and applies all policies |
| IT Admin | `HRZN_IT_ADMIN` | Audits access history and compliance trail |

### Prerequisites
- Familiarity with SQL
- Basic understanding of data governance concepts

### What You'll Learn

**Core Governance:**
- Automate PII discovery with AI-powered CLASSIFICATION_PROFILE and custom tag mapping (BYOT pattern)
- Protect sensitive data with multi-type tag-based masking policies that scale automatically to derived tables
- Apply consent-based and geographic row access policies for defense-in-depth
- Use aggregation and projection policies to prevent individual record access
- Establish a complete audit trail with Access History and column-level lineage

**AI-Powered Governance:**
- Use the Trust Center Data Security UI to verify classification results and generate Sensitive Data Entitlement Reports — no SQL required
- Redact PII from free-form text with AI_REDACT
- Use Cortex Code governance skills to assess governance maturity, create best-practice policies, and run compliance audits in plain English

### What You'll Need
- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account with ACCOUNTADMIN access (trial accounts work)
- Approximately 90 minutes to complete all steps

### What You'll Build
- A complete data governance framework with RBAC roles for three personas
- AI-powered classification with a custom 5-tier taxonomy (PII → RESTRICTED → SENSITIVE → INTERNAL → PUBLIC)
- Tag-based masking policies (STRING, NUMBER, DATE, TIMESTAMP) that auto-apply to all tagged columns
- Consent-based and geographic row access policies
- Trust Center Data Security dashboard with Sensitive Data Entitlement reporting
- Privacy-safe analytics on unstructured customer feedback text
- Cortex Code skill-generated compliance reports and best-practice policy recommendations

### Key Features in This Lab

| Feature | Description |
|---------|-------------|
| **CLASSIFICATION_PROFILE** with tag_map | Auto-tag 50+ PII types using your custom taxonomy |
| **DATA_CLASSIFICATION** tag with PROPAGATE | Tags flow automatically to all derived tables |
| Multi-type tag-based masking | One policy per data type; auto-applied to all tagged columns |
| Row access policies | Consent-based and geographic row filtering |
| Trust Center Data Security | No-SQL dashboard for classification results and entitlement reporting |
| **AI_REDACT** | Remove PII from free-form text for safe ML and analytics |
| Cortex Code governance skills | Plain-English governance: maturity scoring, policy creation, audit |

<!-- ------------------------ -->
## Setup

> **Source of Truth:** The full SQL scripts for this lab are in the [GitHub repository](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol). This guide provides narrative context; the SQL files are the canonical source for execution.

### Run the Setup Script

**Script:** [0-lab-setup.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/0-lab-setup.sql)

1. In Snowsight, create a new SQL worksheet named `0_lab_setup`
2. Copy the contents of `0-lab-setup.sql` into your worksheet
3. Run all statements as `ACCOUNTADMIN`

### What the Setup Creates

| Object | Purpose |
|--------|---------|
| `HRZN_DATA_ENGINEER` role | Creates and loads data assets |
| `HRZN_DATA_GOVERNOR` role | Classification, masking policies, governance |
| `HRZN_DATA_USER` role | Restricted analyst — sees masked data, MA state only |
| `HRZN_IT_ADMIN` role | Audits access history and compliance |
| `HRZN_WH` warehouse | Compute for all lab steps |
| `HRZN_DB` database | Schemas: `HRZN_SCH`, `TAG_SCHEMA`, `CLASSIFIERS` |
| `CUSTOMER` table | 1,000 rows of synthetic customer PII |
| `CUSTOMER_ORDERS` table | Order transactions linked to customers |
| `ROW_POLICY_MAP` table | Maps roles to visible states (MA for `HRZN_DATA_USER`) |
| Trust Center grants | `TRUST_CENTER_ADMIN`, `DATA_SECURITY_ADMIN` for `HRZN_DATA_GOVERNOR` |
| Cortex Code skills grants | `GOVERNANCE_VIEWER`, `SECURITY_VIEWER` for `ACCOUNT_USAGE` access |

### Key Setup Concepts

The setup script demonstrates Snowflake's **Role-Based Access Control (RBAC)**:
- Custom roles are created and assigned to `SYSADMIN` in the hierarchy
- Each role gets the minimum privileges needed for its persona
- `APPLY TAG`, `APPLY MASKING POLICY`, `APPLY ROW ACCESS POLICY` on account allow the governor to define and attach policies without object ownership

<!-- ------------------------ -->
## Access Control

**Script:** [1-access-control.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/1-access-control.sql) | Role: `HRZN_DATA_ENGINEER`

### RBAC and DAC Fundamentals

Snowflake access control combines:
- **Discretionary Access Control (DAC):** Object owners grant access to their objects
- **Role-Based Access Control (RBAC):** Privileges are assigned to roles; roles are assigned to users

> **Access is denied by default in Snowflake.** Every privilege must be explicitly granted. Without `USAGE` on the database, querying any object inside it returns: `"Database 'HRZN_DB' does not exist or not authorized."`

### The Complete Privilege Grant Pattern

```sql
-- 1. Create the role (USERADMIN)
CREATE OR REPLACE ROLE HRZN_DATA_ANALYST COMMENT = 'Analyst role';

-- 2. Grant warehouse access (SECURITYADMIN)
GRANT USAGE ON WAREHOUSE HRZN_WH TO ROLE HRZN_DATA_ANALYST;

-- 3. Grant database and schema access
GRANT USAGE ON DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HRZN_DB TO ROLE HRZN_DATA_ANALYST;

-- 4. Grant object-level privileges
GRANT SELECT ON ALL TABLES IN SCHEMA HRZN_DB.HRZN_SCH TO ROLE HRZN_DATA_ANALYST;
```

### Explore the Raw Data

After completing this step you will observe that the CUSTOMER table exposes 15 columns of PII — SSN, email, credit card, phone, birthdate — with no masking. This is the problem Step 2 solves.

**Key Takeaways:**
- All Snowflake access is deny-by-default; every privilege requires an explicit GRANT
- Role hierarchy means a role inherits all privileges of roles below it
- The raw CUSTOMER table exposes PII to anyone with SELECT — Step 2 fixes this

<!-- ------------------------ -->
## Know and Protect Your Data

**Script:** [2-classification-and-policies.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/2-classification-and-policies.sql) | Role: `HRZN_DATA_GOVERNOR`

### AI-Powered Classification with the BYOT Pattern

The **BYOT (Bring Your Own Tags)** pattern maps AI-detected categories to your organization's custom taxonomy. Create the enterprise `DATA_CLASSIFICATION` tag with propagation enabled:

```sql
CREATE OR REPLACE TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    ALLOWED_VALUES 'PII', 'RESTRICTED', 'SENSITIVE', 'INTERNAL', 'PUBLIC'
    PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT;
```

> **`PROPAGATE = ON_DEPENDENCY_AND_DATA_MOVEMENT`** automatically flows this tag to tables created via `CTAS`, `INSERT ... SELECT`, and views — downstream tables inherit governance automatically.

Create a Classification Profile mapping AI-detected categories to your custom tag values:

```sql
CREATE SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE
    HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE({
    'auto_tag': true,
    'tag_map': {
      'column_tag_map': [
        { 'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
          'tag_value': 'PII',
          'semantic_categories': ['EMAIL', 'US_SOCIAL_SECURITY_NUMBER', 'CREDIT_CARD_NUMBER'] },
        { 'tag_name': 'HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION',
          'tag_value': 'RESTRICTED',
          'semantic_categories': ['PHONE_NUMBER', 'DATE_OF_BIRTH'] }
      ]
    }
});
```

Run classification:
```sql
CALL SYSTEM$CLASSIFY(
    'HRZN_DB.HRZN_SCH.CUSTOMER',
    'HRZN_DB.HRZN_SCH.HRZN_STANDARD_CLASSIFICATION_PROFILE'
);
```

### Tag-Based Masking Policies (Multi-Type)

Create one masking policy per data type and attach all to the `DATA_CLASSIFICATION` tag. Any column tagged automatically gets the correct masking applied:

| Policy | Data Type | PII | RESTRICTED | SENSITIVE |
|--------|-----------|-----|------------|-----------|
| `DATA_CLASSIFICATION_MASK_STRING` | VARCHAR | `***PII-REDACTED***` | `***-1234` (last 4) | SHA2 hash |
| `DATA_CLASSIFICATION_MASK_NUMBER` | NUMBER | `NULL` | Rounded | ABS(HASH) |
| `DATA_CLASSIFICATION_MASK_DATE` | DATE | `NULL` | Year only | Month only |
| `DATA_CLASSIFICATION_MASK_TIMESTAMP` | TIMESTAMP | `NULL` | Day only | Month only |

```sql
-- Attach all policies to the DATA_CLASSIFICATION tag
ALTER TAG HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION
    SET MASKING POLICY HRZN_DB.TAG_SCHEMA.DATA_CLASSIFICATION_MASK_STRING;
-- Repeat for NUMBER, DATE, TIMESTAMP
```

> **Key Benefit:** Tag a column → masking is applied immediately, for the correct data type, automatically.

### Row Access Policies

**Consent-based (opt-in) policy:**
```sql
CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_OPTIN_POLICY
    AS (OPTIN_STATUS STRING) RETURNS BOOLEAN ->
    CASE
        WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR') THEN TRUE
        WHEN CURRENT_ROLE() = 'HRZN_DATA_USER' AND OPTIN_STATUS = 'Y' THEN TRUE
        ELSE FALSE
    END;
```

**State-based (geographic) policy using a mapping table:**
```sql
CREATE OR REPLACE ROW ACCESS POLICY HRZN_DB.TAG_SCHEMA.CUSTOMER_STATE_RESTRICTIONS
    AS (STATE STRING) RETURNS BOOLEAN ->
       CURRENT_ROLE() IN ('ACCOUNTADMIN', 'HRZN_DATA_GOVERNOR')
        OR EXISTS (
            SELECT 1 FROM HRZN_DB.TAG_SCHEMA.ROW_POLICY_MAP rp
            WHERE rp.ROLE = CURRENT_ROLE() AND rp.STATE_VISIBILITY = STATE
        );
```

> **Defense-in-Depth:** Row access policies control WHO sees WHICH records. Masking policies control HOW data appears when visible. Together they provide layered protection.

### Aggregation and Projection Policies

```sql
-- Aggregation: force non-admin users to group by ≥100 rows
CREATE OR REPLACE AGGREGATION POLICY HRZN_DB.TAG_SCHEMA.AGGREGATION_POLICY
    AS () RETURNS AGGREGATION_CONSTRAINT ->
    CASE
        WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR') THEN NO_AGGREGATION_CONSTRAINT()
        ELSE AGGREGATION_CONSTRAINT(MIN_GROUP_SIZE => 100)
    END;

-- Projection: block ZIP from appearing in SELECT output (but allow it in WHERE)
CREATE OR REPLACE PROJECTION POLICY HRZN_DB.TAG_SCHEMA.PROJECTION_POLICY
    AS () RETURNS PROJECTION_CONSTRAINT ->
    CASE
        WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR') THEN PROJECTION_CONSTRAINT(ALLOW => true)
        ELSE PROJECTION_CONSTRAINT(ALLOW => false)
    END;
```

### Tag Propagation to Derived Tables

```sql
CREATE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_COPY AS
SELECT * FROM HRZN_DB.HRZN_SCH.CUSTOMER;
-- DATA_CLASSIFICATION tags propagate automatically
-- Masking policies apply to CUSTOMER_COPY without any manual configuration
```

**Key Takeaways:**

| Policy Type | Controls | Use Case |
|-------------|----------|---------|
| **Masking** | HOW data appears | Hide PII from analysts |
| **Row Access** | WHICH rows visible | Geographic or consent filtering |
| **Aggregation** | Query type allowed | Force aggregate-only access |
| **Projection** | Column projectability | Block specific columns in SELECT |

- Tag propagation scales governance to thousands of derived tables automatically
- Tag-based masking scales better than per-column policies — add a table, just tag the columns

<!-- ------------------------ -->
## Trust Center Verification

**Script:** [3-trust-center-data-security.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/3-trust-center-data-security.sql) | Role: `HRZN_DATA_GOVERNOR`

The Trust Center **Data Security** tab (GA: April 2026) provides a consolidated, no-SQL view of your sensitive data posture.

### Navigate the Dashboard

**Navigation:** Snowsight → **Governance & Security** → **Trust Center** → **Data Security** tab

The dashboard shows:
- **Sensitive Objects** count — tables and columns with detected PII, PCI, or PHI
- **PII / PCI / PHI breakdown** tiles
- **Objects that need review** — pending classification decisions
- **Policy coverage** — percentage of sensitive objects with masking policies

### Verify Classification Results via SQL

These queries read from `SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST` — the same view the dashboard reads:

```sql
-- Mirror the dashboard breakdown tiles
SELECT TAG_VALUE AS CLASSIFICATION_LEVEL,
    COUNT(DISTINCT COLUMN_NAME) AS COLUMN_COUNT,
    COUNT(DISTINCT TABLE_NAME) AS TABLE_COUNT
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST
WHERE TABLE_DATABASE = 'HRZN_DB'
GROUP BY TAG_VALUE ORDER BY COLUMN_COUNT DESC;
```

> **Note:** `ACCOUNT_USAGE` has up to 3-hour latency. Use `INFORMATION_SCHEMA.TAG_REFERENCES_ALL_COLUMNS` for immediate verification (demonstrated in Step 2).

### Objects That Need Review (UI Walkthrough)

Select **"Objects that need review"** to open the review workflow:
- Inspect each column's **CLASSIFICATION CATEGORY** | **TAGS** | **SAMPLE VALUES**
- Accept, change, or remove AI-generated recommendations
- Click **"Save and apply tags to selected tables"** to commit

### Sensitive Data Entitlement Report

The Entitlement Report answers: **"Who can access my sensitive data?"**

**Enable in UI:**
1. **Trust Center** → **Data Security** → **Settings** tab
2. **Reporting** section → **Sensitive Data Entitlement Report** → **Enable**
3. Select **Daily** cadence → **Enable report** → **Run now**

**Query the results:**
```sql
SELECT DISTINCT USER_NAME, TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, PRIVILEGE
FROM SNOWFLAKE.DATA_SECURITY.ENTITLEMENT_REPORT
ORDER BY USER_NAME, TABLE_NAME, PRIVILEGE;
```

### Governance Gap Analysis

```sql
-- Sensitive columns WITHOUT an active masking policy
SELECT dc.TABLE_NAME, dc.COLUMN_NAME, dc.TAG_VALUE AS SENSITIVITY_LEVEL,
    CASE WHEN pr.REF_COLUMN_NAME IS NOT NULL THEN 'Protected' ELSE 'UNPROTECTED' END AS STATUS
FROM SNOWFLAKE.ACCOUNT_USAGE.DATA_CLASSIFICATION_LATEST dc
LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.POLICY_REFERENCES pr
    ON dc.TABLE_NAME = SPLIT_PART(pr.REF_ENTITY_NAME, '.', 3)
    AND dc.COLUMN_NAME = pr.REF_COLUMN_NAME
    AND pr.POLICY_KIND = 'MASKING_POLICY'
WHERE dc.TABLE_DATABASE = 'HRZN_DB';
```

**Key Takeaways:**
- Trust Center provides a compliance dashboard without requiring SQL knowledge
- The Entitlement Report is essential for "who has access" audits required by GDPR, HIPAA, and SOX
- Gap analysis bridges classification and protection — find classified-but-unmasked columns instantly

<!-- ------------------------ -->
## Access and Audit Trail

**Script:** [4-audit-trail.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/4-audit-trail.sql) | Role: `HRZN_IT_ADMIN`

Access History (`SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY`) tracks every query that touched your data — what was read, what was written, when, and by whom.

> **Important:** Access History has up to 3-hour latency. Some queries may return empty results immediately after lab steps. This is expected; plan for this latency in production compliance reporting.

### Query Count and Read/Write Patterns

```sql
-- Access count by object
SELECT value:"objectName"::STRING AS object_name,
    COUNT(DISTINCT query_id) AS number_of_queries
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
LATERAL FLATTEN(input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name ORDER BY number_of_queries DESC;

-- Read vs. write breakdown
SELECT value:"objectName"::STRING AS object_name,
    CASE WHEN object_modified_by_ddl IS NOT NULL THEN 'write' ELSE 'read' END AS query_type,
    COUNT(DISTINCT query_id) AS number_of_queries,
    MAX(query_start_time) AS last_access
FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
LATERAL FLATTEN(input => direct_objects_accessed)
WHERE object_name ILIKE 'HRZN%'
GROUP BY object_name, query_type;
```

### Sensitive Data Column-Level Lineage

The script includes a column-level lineage query that traces how tagged columns (PII, RESTRICTED, SENSITIVE) flow from source tables through INSERT/CTAS operations into derived objects. This proves to auditors that PII was not copied to unauthorized locations and confirms tag propagation covered all derived paths.

**Key Takeaways:**
- `DIRECT_OBJECTS_ACCESSED`: objects named explicitly in the query
- `BASE_OBJECTS_ACCESSED`: objects actually read (including through views)
- `OBJECTS_MODIFIED`: objects written (INSERT, CTAS, DDL)
- Access History is the foundation for GDPR data subject access reports, SOX audit logs, and HIPAA access audits

<!-- ------------------------ -->
## AI_REDACT for Unstructured PII

**Script:** [5-ai-redact.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/5-ai-redact.sql) | Role: `HRZN_DATA_GOVERNOR`

Steps 1–4 protect **structured columns**. But customer feedback, support tickets, and survey responses are free-form text with PII embedded anywhere. AI_REDACT handles this automatically.

### The Problem: PII in Free-Form Text

```
"Customer John Smith called from 555-123-4567. Email: john.smith@email.com"
"Customer Sarah Williams mentioned her SSN 123-45-6789 was visible on invoice."
```

Column masking cannot help here — the PII is embedded in a text string, not a typed column.

### AI_REDACT: Automatic PII Removal

```sql
SELECT
    original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(original_feedback) AS redacted_feedback
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS LIMIT 5;
```

**Result:**
```
ORIGINAL: "Customer John Smith called from 555-123-4567. Email: john.smith@email.com"
REDACTED: "Customer [NAME] called from [PHONE_NUMBER]. Email: [EMAIL]"
```

AI_REDACT detects and replaces 50+ PII types including `[NAME]`, `[EMAIL]`, `[PHONE_NUMBER]`, `[US_SOCIAL_SECURITY_NUMBER]`, `[STREET_ADDRESS]` — no regex patterns required.

### Selective Redaction

```sql
-- Redact only names and emails; preserve phone numbers
SNOWFLAKE.CORTEX.AI_REDACT(text, ['NAME', 'EMAIL'])
```

### Pre-Compute + Secure View Pattern

Running AI_REDACT on every query is expensive. Best practice:

```sql
-- 1. Create a redacted table once (batch job)
CREATE TABLE HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED AS
SELECT ORDER_ID,
    CUSTOMER_FEEDBACK AS original_feedback,
    SNOWFLAKE.CORTEX.AI_REDACT(CUSTOMER_FEEDBACK) AS redacted_feedback
FROM HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS WHERE CUSTOMER_FEEDBACK IS NOT NULL LIMIT 100;

-- 2. Secure view switches columns based on role
CREATE SECURE VIEW HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_SECURE AS
SELECT ORDER_ID,
    CASE WHEN CURRENT_ROLE() IN ('HRZN_DATA_GOVERNOR') THEN original_feedback
         ELSE redacted_feedback
    END AS CUSTOMER_FEEDBACK
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED;
```

### Privacy-Safe Sentiment Analysis

```sql
SELECT redacted_feedback,
    SNOWFLAKE.CORTEX.SENTIMENT(redacted_feedback) AS sentiment_score
FROM HRZN_DB.HRZN_SCH.CUSTOMER_FEEDBACK_REDACTED;
```

> **Tag Propagation:** `CUSTOMER_FEEDBACK_REDACTED` automatically inherits `DATA_CLASSIFICATION` tags from `CUSTOMER_ORDERS` because of the propagation setting from Step 2.

**Key Takeaways:**

| Data Type | Governance Approach |
|-----------|-------------------|
| Structured columns (email, SSN, phone) | Classification + tag-based masking (Steps 2–3) |
| Unstructured text (feedback, notes) | `AI_REDACT` (Step 5) |

Both approaches are complementary — together they provide complete PII coverage.

<!-- ------------------------ -->
## Cortex Code Skills

**Script:** [6-cortex-code-governance-skills.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/hol-lab/6-cortex-code-governance-skills.sql) | Role: `HRZN_DATA_GOVERNOR`

Cortex Code is Snowflake's AI-powered coding assistant. Its built-in data governance skills let you accomplish governance tasks in plain English — no SQL required.

**Open Cortex Code:** Click the **✨ Cortex Code** icon in the Snowsight left navigation sidebar.

### Skill Domains Used in This Lab

| Skill | What It Does |
|-------|-------------|
| General Data Governance | Audit access, compliance posture, role hierarchy, tag/policy inventory |
| Sensitive Data Classification | Scan for PII, analyze results, create profiles and custom classifiers |
| Data Protection Policies | Create/audit masking and row access policies with best practices |

### 6.1 — Governance Maturity Assessment

```
"What is the governance coverage for HRZN_DB?
 Which tables have PII but no masking policy applied?"

"Generate a data governance health report for HRZN_DB.
 Include: tables with sensitive data, policy coverage percentage, and top risks."
```

Cortex Code queries `DATA_CLASSIFICATION_LATEST` and `POLICY_REFERENCES` and returns a synthesized health summary with a governance maturity grade.

### 6.2 — AI Classification via Skills

```
"Scan HRZN_DB.HRZN_SCH.CUSTOMER_ORDERS for PII and sensitive data."

"Which tables in HRZN_DB need re-classification because their results are older than 30 days?"

"Help me create a custom classifier for employee IDs matching the pattern EMP-XXXXX."
```

Cortex Code generates and executes `SYSTEM$CLASSIFY` calls automatically, then explains the results in plain English.

### 6.3 — Policy Creation and Audit

```
"Audit all masking policies in HRZN_DB.TAG_SCHEMA. Are there anti-patterns?"

"Create a GDPR-compliant masking policy for the SSN column in HRZN_DB.HRZN_SCH.CUSTOMER."

"What is the recommended ABAC pattern for masking in Snowflake?"
```

> **Anti-Pattern Teaching Moment:** The masking policies created in Step 2 use `CURRENT_ROLE()`. Cortex Code will flag this: `CURRENT_ROLE()` only evaluates the primary active role, while `IS_ROLE_IN_SESSION()` evaluates all active roles including secondary roles. Best practice is always `IS_ROLE_IN_SESSION()`.

> Cortex Code generates complete, runnable `CREATE MASKING POLICY` SQL using Snowflake best practices. Review the generated SQL before applying it to production tables.

### 6.4 — Compliance Audit

```
"Who has accessed HRZN_DB.HRZN_SCH.CUSTOMER in the last 30 days?"

"Were there any queries on HRZN_DB sensitive tables outside of business hours?"

"Which roles have the APPLY MASKING POLICY privilege on my account?"

"Show the role hierarchy for HRZN_DATA_GOVERNOR."
```

Each prompt generates SQL that queries `ACCOUNT_USAGE` automatically.

**Key Takeaways:**

| Skill | Key Value |
|-------|-----------|
| Maturity Assessment | Scores governance coverage without SQL expertise |
| Classification | Runs `SYSTEM$CLASSIFY`, explains detections in plain English |
| Policy Creation | Generates best-practice policies; flags `CURRENT_ROLE()` anti-pattern |
| Compliance Audit | Answers access audit questions from `ACCOUNT_USAGE` via natural language |

**Cortex Code Tips:**
- Use fully-qualified names: `DATABASE.SCHEMA.TABLE` for the most accurate results
- Start broad (`"health report for HRZN_DB"`) then drill into specific issues
- If `ACCOUNT_USAGE` is not yet populated, tell Cortex Code: `"Check INFORMATION_SCHEMA as ACCOUNT_USAGE may not be populated yet"`

<!-- ------------------------ -->
## Conclusion and Resources

Congratulations! You've completed the Advanced Data Governance Summit HOL.

### What You Learned

| Topic | Feature | Step |
|-------|---------|------|
| Access Control | RBAC, privilege grants, deny-by-default | Step 1 |
| AI Classification | CLASSIFICATION_PROFILE, BYOT tag_map, custom classifiers | Step 2 |
| Masking | Multi-type tag-based masking with auto-propagation | Step 2 |
| Row Access | Consent-based and geographic row filtering | Step 2 |
| Advanced Policies | Aggregation and projection policies | Step 2 |
| Trust Center UI | Data Security dashboard, Entitlement Report | Step 3 |
| Audit Trail | Access History, column-level PII lineage | Step 4 |
| Unstructured PII | AI_REDACT, pre-compute + secure view pattern | Step 5 |
| Cortex Code Skills | Maturity score, policy creation, compliance audit | Step 6 |

### Clean Up

Run [99-teardown.sql](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol/blob/main/99-teardown.sql) to remove all lab objects from your account.

### Related Resources
- [Snowflake Horizon Catalog](https://docs.snowflake.com/en/user-guide/snowflake-horizon)
- [Introduction to Sensitive Data Classification](https://docs.snowflake.com/en/user-guide/classify-intro)
- [Trust Center Data Security](https://docs.snowflake.com/en/user-guide/classify-ui-trust-center)
- [Masking Policies](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro)
- [Row Access Policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
- [AI_REDACT Function](https://docs.snowflake.com/en/sql-reference/functions/ai_redact)
- [Cortex Code Governance Skills](https://docs.snowflake.com/en/user-guide/governance-skills)
- [Sensitive Data Entitlement Report](https://docs.snowflake.com/en/user-guide/classify-ui-trust-center#sensitive-data-entitlement-report)
- [Lab GitHub Repository](https://github.com/sfc-gh-ankgupta/sfguide-advanced-data-governance-summit-hol)
