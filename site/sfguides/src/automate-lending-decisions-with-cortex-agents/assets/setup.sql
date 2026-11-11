-- Agentic lending lab: setup for a Snowflake trial account
--
-- Paste this file into a SQL file in a Snowsight workspace, then choose Run All.
-- It takes about a minute.
--
-- Run it again at any point to start the lab over. It rebuilds the LENDING
-- database from nothing, so everything you made in the lab is removed with it.
--
-- Everything runs as ACCOUNTADMIN, the role a trial account signs you in with.
-- The documents and evaluation settings are copied from the guide's assets
-- folder in the Snowflake-Labs/sfquickstarts repository on GitHub.

USE ROLE ACCOUNTADMIN;

/* Small and quick to suspend so the lab does not eat trial credits.

   IF NOT EXISTS rather than OR REPLACE: when setup is run again, this script
   is itself running on LENDING_WH, and replacing it would abort the script. */
CREATE WAREHOUSE IF NOT EXISTS LENDING_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE LENDING_WH;

/* Let Cortex use models hosted outside the account's region. Not every region
   hosts every model the lab's agents use. */
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

/* OR REPLACE so that running setup again starts the lab over: every table,
   agent, stream, task and evaluation run inside LENDING goes with it. */
CREATE OR REPLACE DATABASE LENDING;
CREATE SCHEMA LENDING.LOANS;

/* The guide's files live in the public sfquickstarts repository. A Git
   repository object lets COPY FILES read them straight from GitHub.

   It sits in its own schema so that nothing in LENDING.LOANS looks like a
   thirteenth applicant document when Module 1 lists what is on the stages. */
CREATE OR REPLACE API INTEGRATION LENDING_GUIDE_GIT_API
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/Snowflake-Labs/')
    ENABLED = TRUE;

CREATE SCHEMA LENDING.GUIDE_FILES;

CREATE GIT REPOSITORY LENDING.GUIDE_FILES.SFQUICKSTARTS
    API_INTEGRATION = LENDING_GUIDE_GIT_API
    ORIGIN = 'https://github.com/Snowflake-Labs/sfquickstarts.git';

USE SCHEMA LENDING.LOANS;

/* ---------------------------------------------------------------------------
   1. The loan application record

   What the applicant declared at intake and what the credit bureau returned.

   DEBT_TO_INCOME_RATIO only covers obligations on the consumer credit report, so
   a loan in a company's name or a co-signed account is absent from it. Modules 2
   and 3 depend on that gap.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE TABLE LENDING.LOANS.APPLICATIONS (
    -- Intake fields, populated by section 5 below
    APPLICANT_ID          VARCHAR(20)   NOT NULL PRIMARY KEY,
    FIRST_NAME            VARCHAR(100),
    LAST_NAME             VARCHAR(100),
    CREDIT_SCORE          INTEGER,
    ANNUAL_INCOME         NUMBER(12,2),
    DEBT_TO_INCOME_RATIO  FLOAT,
    REQUESTED_AMOUNT      NUMBER(12,2),
    LOAN_PURPOSE          VARCHAR(60),
    EMPLOYMENT_STATUS     VARCHAR(30),
    YEARS_EMPLOYED        INTEGER,
    APPLICATION_DATE      DATE,
    -- PENDING until something decides it, then APPROVED, DECLINED or ESCALATED.
    STATUS                VARCHAR(20) DEFAULT 'PENDING',

    -- Written by RECORD_DECISION. How the agent reached the decision is not
    -- here; that is in AI Observability.
    APPROVED_AMOUNT       NUMBER(12,2),
    POLICY_TIER           VARCHAR(20),
    MAX_EXPOSURE          NUMBER(12,2),
    POLICY_OVERRIDDEN     BOOLEAN,
    ESCALATION_QUESTION   VARCHAR(2000),
    PROCESSED_AT          TIMESTAMP_LTZ
);


/* ---------------------------------------------------------------------------
   2. Parsed documents, and the chunks Cortex Search indexes

   DOCUMENT_TEXT holds one row per document, DOCUMENT_CHUNKS the passages Cortex
   Search indexes. Both are filled at the end of this script, once the documents
   are on the stage.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE TABLE LENDING.LOANS.DOCUMENT_TEXT (
    FILE_NAME     VARCHAR(200) NOT NULL PRIMARY KEY,
    APPLICANT_ID  VARCHAR(20),
    DOC_TYPE      VARCHAR(60),
    DOC_TEXT      VARCHAR
);

CREATE OR REPLACE TABLE LENDING.LOANS.DOCUMENT_CHUNKS (
    CHUNK_ID      VARCHAR(80) NOT NULL PRIMARY KEY
        COMMENT 'Chunk identifier, the file name with the position of the chunk inside it, for example doc_APP_1004_commercial_loan_agreement.pdf:1.',
    FILE_NAME     VARCHAR(200)
        COMMENT 'Source filename, formatted doc_<applicant_id>_<doc_type>.pdf, for example doc_APP_1004_bank_statement.pdf. Search this to find a kind of document rather than particular content.',
    APPLICANT_ID  VARCHAR(20)
        COMMENT 'Applicant the document belongs to, for example APP_1004. Always filter on this. Diligence is performed one applicant at a time and passages from another applicant are not evidence.',
    DOC_TYPE      VARCHAR(60)
        COMMENT 'Kind of document. Values: bank_statement, pay_stub, business_tax_return, commercial_loan_agreement, auto_loan_statement, coapplicant_addendum. Filter to bank_statement to list recurring payments; to commercial_loan_agreement or auto_loan_statement to establish the terms of an obligation; to business_tax_return or pay_stub to verify income.',
    CHUNK_TEXT    VARCHAR
        COMMENT 'A passage from a document the applicant submitted. Contains transaction lines from bank statements with dates, counterparty names and amounts; income and revenue figures from tax returns; and terms from loan agreements including balances, monthly payments, and whether the applicant is the borrower, a guarantor or a co-signer.'
);


/* ---------------------------------------------------------------------------
   3. Credit memos - written during the lab, not seeded

   Handed to attendees empty. No seed data may contain a conclusion about an
   applicant.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE TABLE LENDING.LOANS.CREDIT_MEMO (
    MEMO_ID          VARCHAR(60)   NOT NULL PRIMARY KEY
        COMMENT 'Memo identifier.',
    APPLICANT_ID     VARCHAR(20)
        COMMENT 'Applicant the memo is about, for example APP_1004.',
    REPORTED_DTI     FLOAT
        COMMENT 'The debt-to-income ratio as it appeared on the loan application, covering only obligations the credit bureau could see.',
    RECOMPUTED_DTI   FLOAT
        COMMENT 'The ratio diligence arrived at. Equal to the reported ratio where nothing further was found.',
    FINDINGS         VARIANT
        COMMENT 'Structured findings, such as the additional monthly obligations discovered and any risk to the durability of the income.',
    MEMO_TEXT        VARCHAR(8000)
        COMMENT 'The written assessment, stating what was found and the figures behind it.',
    EVIDENCE_REFS    VARCHAR(2000)
        COMMENT 'Comma separated filenames of the documents the assessment relied on.',
    GENERATED_AT     TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        COMMENT 'When the memo was written.'
);


/* ---------------------------------------------------------------------------
   4. Stage for the submitted documents

   DIRECTORY is required: the parse step enumerates the stage to find its input.
   Encryption is set explicitly so the stage does not inherit an account default.
   --------------------------------------------------------------------------- */

CREATE STAGE LENDING.LOANS.LAB_FILES
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Lab data: the documents applicants submitted';


/* ---------------------------------------------------------------------------
   5. The loan application records

   APP_1001 to APP_1006 are the six the lab works on and stay PENDING. The other
   fourteen are already decided and give the semantic view a portfolio to
   aggregate over. They must never enter the work queue.
   --------------------------------------------------------------------------- */

INSERT INTO LENDING.LOANS.APPLICATIONS
    (APPLICANT_ID, FIRST_NAME, LAST_NAME, CREDIT_SCORE, ANNUAL_INCOME,
     DEBT_TO_INCOME_RATIO, REQUESTED_AMOUNT, LOAN_PURPOSE, EMPLOYMENT_STATUS,
     YEARS_EMPLOYED, APPLICATION_DATE, STATUS)
VALUES
    -- The six the lab works on. Nothing here says what any of them mean.
    ('APP_1001','Diane','Whitfield',      776,142000.00,0.24,45000.00,'home improvement',  'employed',     11,'2026-07-17','PENDING'),
    ('APP_1002','Marcus','Adeyemi',       611, 88500.00,0.44,32000.00,'debt consolidation','employed',      6,'2026-07-18','PENDING'),
    ('APP_1003','Priya','Adeyemi',        752,119000.00,0.21,    0.00,'co-applicant',      'employed',      9,'2026-07-18','PENDING'),
    ('APP_1004','Grant','Kelleher',       771,163000.00,0.19,75000.00,'debt consolidation','self-employed', 7,'2026-07-16','PENDING'),
    ('APP_1005','Tobias','Renner',        648, 57400.00,0.47,24000.00,'auto',              'self-employed', 2,'2026-07-19','PENDING'),
    ('APP_1006','Yolanda','Castellanos',  694,101000.00,0.39,40000.00,'small business',    'self-employed', 4,'2026-07-15','PENDING'),

    -- Already decided. Portfolio context for the semantic view, nothing more.
    ('APP_1007','Zoe','Alvarez',          547, 16198.10,0.20, 3037.90,'home improvement',  'unemployed',    0,'2026-06-20','DECLINED'),
    ('APP_1008','Dmitri','Oyelaran',      638, 84034.64,0.18, 7989.85,'small business',    'employed',      1,'2026-07-07','APPROVED'),
    ('APP_1009','Malik','Nystrom',        671,124253.42,0.21,45631.19,'auto',              'employed',      3,'2026-06-26','APPROVED'),
    ('APP_1010','Dmitri','Kowalski',      690, 77237.24,0.18, 9839.93,'debt consolidation','employed',      3,'2026-06-14','APPROVED'),
    ('APP_1011','Samir','Zielinski',      700,174804.01,0.25,64943.84,'home improvement',  'employed',     27,'2026-07-08','APPROVED'),
    ('APP_1012','Valeria','Jorgensen',    710,158520.88,0.13,64326.92,'debt consolidation','employed',     12,'2026-07-19','APPROVED'),
    ('APP_1013','Rosa','Oyelaran',        719,131137.59,0.08,10965.87,'medical',           'employed',      6,'2026-06-06','APPROVED'),
    ('APP_1014','Hector','Salcedo',       726, 72892.01,0.16,18331.20,'medical',           'employed',      1,'2026-07-14','APPROVED'),
    ('APP_1015','Samir','Bergstrom',      737, 87282.97,0.08,29097.74,'major purchase',    'self-employed', 5,'2026-06-09','APPROVED'),
    ('APP_1016','Lorena','Quintero',      748,105661.24,0.15,24746.42,'major purchase',    'employed',      6,'2026-06-13','APPROVED'),
    ('APP_1017','Oskar','Yamada',         764,127055.57,0.19,43667.41,'small business',    'employed',     22,'2026-06-13','APPROVED'),
    ('APP_1018','Samir','Oyelaran',       770,151420.37,0.22,16435.55,'home improvement',  'self-employed',16,'2026-06-25','APPROVED'),
    ('APP_1019','Bruno','Xiong',          793,184200.70,0.17,29991.90,'home improvement',  'employed',      3,'2026-07-08','APPROVED'),
    ('APP_1020','Imani','Lindgren',       810,182274.46,0.08,26286.28,'education',         'employed',     19,'2026-06-13','APPROVED');

/* Fill in the decided rows. The six pending rows keep their nulls. */
UPDATE LENDING.LOANS.APPLICATIONS
   SET APPROVED_AMOUNT = IFF(STATUS = 'APPROVED', REQUESTED_AMOUNT, 0),
       PROCESSED_AT    = DATEADD(day, 2, APPLICATION_DATE)
 WHERE STATUS <> 'PENDING';

/* ---------------------------------------------------------------------------
   6. Lending policy

   Reports constraints; does not decide. The thresholds live here rather than in
   an agent's instructions so policy changes in one place.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE FUNCTION LENDING.LOANS.POLICY_CHECK(
    CREDIT_SCORE     INTEGER,
    DTI              FLOAT,
    REQUESTED_AMOUNT FLOAT,
    ANNUAL_INCOME    FLOAT
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
HANDLER = 'evaluate'
COMMENT = 'Returns what lending policy permits: the tier, the maximum exposure, whether the file may be approved automatically, and which hard checks failed. Does not return a decision. Call it with the debt-to-income ratio established by diligence, not the ratio reported at intake.'
AS
$$
def evaluate(credit_score, dti, requested_amount, annual_income):
    score, dti = int(credit_score or 0), float(dti or 0.0)
    requested, income = float(requested_amount or 0.0), float(annual_income or 0.0)

    failed = []
    if score < 620:
        failed.append("CREDIT_SCORE_BELOW_MINIMUM_620")
    if dti > 0.43:
        failed.append("DTI_ABOVE_MAXIMUM_0.43")

    if score >= 740 and dti <= 0.36:
        tier, cap = "TIER_1", 0.50
    elif score >= 680 and dti <= 0.43:
        tier, cap = "TIER_2", 0.35
    else:
        tier, cap = "REFERRAL", 0.15

    return {
        "policy_tier": tier,
        "max_exposure": round(min(requested, cap * income), 2) if income > 0 else 0.0,
        "auto_approve_eligible": not failed and tier != "REFERRAL",
        "failed_checks": failed,
    }
$$;


/* ---------------------------------------------------------------------------
   7. The agent's calculator

   The agent supplies the payments it found; this does the arithmetic.

   ADDITIONAL_OBLIGATIONS is VARCHAR because a Cortex Agent custom tool passes
   strings and numbers only. An ARRAY or OBJECT parameter is rejected as an
   unsupported parameter type.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE FUNCTION LENDING.LOANS.RECOMPUTE_DTI(
    REPORTED_DTI            FLOAT,
    ANNUAL_INCOME           FLOAT,
    ADDITIONAL_OBLIGATIONS  VARCHAR
)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
HANDLER = 'recompute'
COMMENT = 'Recomputes a debt-to-income ratio after diligence finds obligations the credit report did not carry. Pass the additional MONTHLY payments as text: 3870.00, 612.00 or [3870.00, 612.00]. Use this instead of calculating a ratio yourself.'
AS
$$
def recompute(reported_dti, annual_income, additional_obligations):
    dti, income = float(reported_dti or 0.0), float(annual_income or 0.0)
    monthly_income = income / 12.0 if income > 0 else 0.0

    found = []
    for part in str(additional_obligations or "").strip("[]").split(","):
        part = part.strip().strip('"').strip("'").replace("$", "").replace(",", "")
        if part:
            try:
                found.append(float(part))
            except ValueError:
                pass

    # Reported ratio x monthly income = what the credit report saw.
    total_monthly = (monthly_income * dti) + sum(found)
    recomputed = (total_monthly / monthly_income) if monthly_income > 0 else 0.0

    return {
        "reported_dti": round(dti, 4),
        "recomputed_dti": round(recomputed, 4),
        "total_monthly_obligations": round(total_monthly, 2),
        "obligations_supplied": [round(x, 2) for x in found],
        "materially_different": abs(recomputed - dti) >= 0.03,
    }
$$;


/* ---------------------------------------------------------------------------
   8. The credit analyst agent's only write

   It records findings and cannot decide anything. The credit analyst agent gets
   no other write tool.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE PROCEDURE LENDING.LOANS.WRITE_CREDIT_MEMO(
    P_APPLICANT_ID   VARCHAR,
    P_RECOMPUTED_DTI FLOAT,
    P_FINDINGS       VARCHAR,
    P_MEMO_TEXT      VARCHAR,
    P_EVIDENCE_REFS  VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Records the credit memo for an applicant: the ratio diligence arrived at, the findings behind it as a JSON string, the written assessment, and the documents relied on. Does not decide the loan application.'
EXECUTE AS CALLER
AS
$$
DECLARE
    v_reported FLOAT;
BEGIN
    SELECT DEBT_TO_INCOME_RATIO INTO :v_reported
      FROM LENDING.LOANS.APPLICATIONS
     WHERE APPLICANT_ID = :P_APPLICANT_ID;

    IF (:v_reported IS NULL) THEN
        RETURN 'ERROR: applicant ' || :P_APPLICANT_ID || ' not found';
    END IF;

    -- Re-running the credit analyst agent replaces its previous memo.
    DELETE FROM LENDING.LOANS.CREDIT_MEMO
     WHERE APPLICANT_ID = :P_APPLICANT_ID;

    INSERT INTO LENDING.LOANS.CREDIT_MEMO
        (MEMO_ID, APPLICANT_ID, REPORTED_DTI, RECOMPUTED_DTI,
         FINDINGS, MEMO_TEXT, EVIDENCE_REFS)
    SELECT 'MEMO_' || REPLACE(UUID_STRING(), '-', ''), :P_APPLICANT_ID,
           :v_reported, :P_RECOMPUTED_DTI, TRY_PARSE_JSON(:P_FINDINGS),
           :P_MEMO_TEXT, :P_EVIDENCE_REFS;

    RETURN 'MEMO WRITTEN for ' || :P_APPLICANT_ID
        || ' | reported=' || TO_VARCHAR(:v_reported)
        || ' | after diligence=' || TO_VARCHAR(:P_RECOMPUTED_DTI);
END;
$$;


/* ---------------------------------------------------------------------------
   9. How the underwriting agent reads a memo

   Module 4's agent needs the memo for one named applicant, so this looks it up
   by id. A search index refreshes on a lag, and the memos it would have to find
   are written minutes earlier in Module 3.

   It returns found = false when there is no memo, so the agent has something
   explicit to branch on. That branch is the whole of Module 4: with no memo the
   file goes back to a human, until the credit analyst is attached over MCP and
   the agent can get diligence done itself.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE FUNCTION LENDING.LOANS.GET_CREDIT_MEMO(
    P_APPLICANT_ID VARCHAR
)
RETURNS OBJECT
COMMENT = 'Returns the credit memo for one applicant: the ratio reported at intake, the ratio diligence arrived at, the written assessment and the documents relied on. Returns found = false when no memo exists, which means diligence has not been done for that applicant.'
AS
$$
COALESCE(
    (SELECT OBJECT_CONSTRUCT(
                'found',          TRUE,
                'applicant_id',   m.APPLICANT_ID,
                'reported_dti',   m.REPORTED_DTI,
                'recomputed_dti', m.RECOMPUTED_DTI,
                'memo_text',      m.MEMO_TEXT,
                'evidence_refs',  m.EVIDENCE_REFS)
       FROM LENDING.LOANS.CREDIT_MEMO m
      WHERE m.APPLICANT_ID = P_APPLICANT_ID
      ORDER BY m.GENERATED_AT DESC
      LIMIT 1),
    OBJECT_CONSTRUCT('found', FALSE, 'applicant_id', P_APPLICANT_ID)
)
$$;


/* ---------------------------------------------------------------------------
   10. The underwriting agent's only write

   The rationale and evidence are required but deliberately not stored. They
   reach AI Observability as the tool's arguments.

   POLICY_CHECK is run again on the stored figures, so MAX_EXPOSURE and
   POLICY_OVERRIDDEN are the policy engine's verdict rather than the agent's
   claim about it.

   It checks the ratio on the memo, not the one reported at intake. On the
   reported figure this control would confirm Grant Kelleher as TIER_1 and
   eligible.
   --------------------------------------------------------------------------- */

CREATE OR REPLACE PROCEDURE LENDING.LOANS.RECORD_DECISION(
    P_APPLICANT_ID         VARCHAR,
    P_ACTION               VARCHAR,
    P_RATIONALE            VARCHAR,
    P_EVIDENCE_REFS        VARCHAR,
    P_APPROVED_AMOUNT      NUMBER(12,2),
    P_UNDERWRITER_QUESTION VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Records the decision on a loan application. P_ACTION is APPROVE, DECLINE or ESCALATE. Pass 0 for the amount and NONE for the question where they do not apply. Re-checks policy independently and refuses any approval above the permitted maximum.'
EXECUTE AS CALLER
AS
$$
DECLARE
    v_action     VARCHAR;
    v_dti        FLOAT;
    v_tier       VARCHAR;
    v_max        FLOAT;
    v_auto       BOOLEAN;
    v_overridden BOOLEAN;
    v_status     VARCHAR;
    v_amount     NUMBER(12,2);
BEGIN
    v_action := UPPER(TRIM(COALESCE(:P_ACTION, '')));

    IF (v_action NOT IN ('APPROVE', 'DECLINE', 'ESCALATE')) THEN
        RETURN 'ERROR: action must be APPROVE, DECLINE or ESCALATE';
    END IF;
    IF (:P_RATIONALE IS NULL OR LENGTH(TRIM(:P_RATIONALE)) = 0) THEN
        RETURN 'ERROR: a rationale is required';
    END IF;

    -- The ratio diligence established, not the one reported at intake.
    SELECT COALESCE(m.RECOMPUTED_DTI, a.DEBT_TO_INCOME_RATIO)
      INTO :v_dti
      FROM LENDING.LOANS.APPLICATIONS a
      LEFT JOIN LENDING.LOANS.CREDIT_MEMO m
             ON m.APPLICANT_ID = a.APPLICANT_ID
     WHERE a.APPLICANT_ID = :P_APPLICANT_ID;

    IF (:v_dti IS NULL) THEN
        RETURN 'ERROR: applicant ' || :P_APPLICANT_ID || ' not found';
    END IF;

    SELECT p.POLICY:policy_tier::VARCHAR,
           p.POLICY:max_exposure::FLOAT,
           p.POLICY:auto_approve_eligible::BOOLEAN
      INTO :v_tier, :v_max, :v_auto
      FROM (
        SELECT LENDING.LOANS.POLICY_CHECK(
                   a.CREDIT_SCORE, :v_dti, a.REQUESTED_AMOUNT, a.ANNUAL_INCOME
               ) AS POLICY
          FROM LENDING.LOANS.APPLICATIONS a
         WHERE a.APPLICANT_ID = :P_APPLICANT_ID
      ) p;

    IF (v_action = 'APPROVE') THEN
        IF (:P_APPROVED_AMOUNT IS NULL OR :P_APPROVED_AMOUNT <= 0) THEN
            RETURN 'ERROR: an approval needs an amount';
        END IF;
        -- A hard stop, not a flag. The agent cannot exceed policy.
        IF (:P_APPROVED_AMOUNT > :v_max) THEN
            RETURN 'REFUSED: ' || TO_VARCHAR(:P_APPROVED_AMOUNT)
                || ' exceeds the maximum exposure of ' || TO_VARCHAR(:v_max)
                || ' at tier ' || :v_tier || '. Escalate instead.';
        END IF;
        v_status := 'APPROVED';
        v_amount := :P_APPROVED_AMOUNT;
    ELSEIF (v_action = 'DECLINE') THEN
        v_status := 'DECLINED';
        v_amount := 0;
    ELSE
        IF (:P_UNDERWRITER_QUESTION IS NULL
            OR LENGTH(TRIM(:P_UNDERWRITER_QUESTION)) < 15) THEN
            RETURN 'ERROR: an escalation needs a specific question';
        END IF;
        v_status := 'ESCALATED';
        v_amount := 0;
    END IF;

    -- Approving a file policy did not clear is allowed, but it is recorded.
    v_overridden := (v_action = 'APPROVE' AND NOT :v_auto);

    UPDATE LENDING.LOANS.APPLICATIONS
       SET STATUS              = :v_status,
           APPROVED_AMOUNT     = :v_amount,
           POLICY_TIER         = :v_tier,
           MAX_EXPOSURE        = :v_max,
           POLICY_OVERRIDDEN   = :v_overridden,
           ESCALATION_QUESTION = IFF(:v_action = 'ESCALATE',
                                     :P_UNDERWRITER_QUESTION, NULL),
           PROCESSED_AT        = CURRENT_TIMESTAMP()
     WHERE APPLICANT_ID = :P_APPLICANT_ID;

    RETURN :v_action || ' recorded for ' || :P_APPLICANT_ID
        || ' | dti_assessed=' || TO_VARCHAR(:v_dti)
        || ' | tier=' || :v_tier
        || ' | max_exposure=' || TO_VARCHAR(:v_max)
        || ' | amount=' || TO_VARCHAR(:v_amount)
        || IFF(:v_overridden, ' | POLICY OVERRIDDEN', '');
END;
$$;


/* ---------------------------------------------------------------------------
   11. Plumbing for Module 4's optional automation

   The optional step at the end of Module 4 puts the underwriting agent behind a
   triggered task, so a loan application that lands is decided without anybody
   asking. What the page shows is the stream and the task. These two objects are
   the parts that teach nothing, so they are provisioned here.

   UNDERWRITE_ARRIVALS exists because DATA_AGENT_RUN needs its request body as a
   constant. A prompt built from a column fails to compile, so the applicant id
   has to pass through a local variable, which means a procedure.

   The procedure consumes the stream with the INSERT before it calls any agent.
   A stream only advances its offset in a DML statement, so a task that reads a
   stream without writing from it fires again every 30 seconds forever. The same
   trap is why SUSPEND_TASK_AFTER_NUM_FAILURES is set on the schema below: a run
   that fails never consumes the stream either.

   The stream Module 4 creates is APPEND_ONLY, so RECORD_DECISION's update to
   APPLICATIONS is not a change the task reacts to.
   --------------------------------------------------------------------------- */

ALTER SCHEMA LENDING.LOANS
    SET SUSPEND_TASK_AFTER_NUM_FAILURES = 3;

CREATE OR REPLACE TABLE LENDING.LOANS.UNDERWRITING_LOG (
    APPLICANT_ID  VARCHAR(20)
        COMMENT 'The loan application the task picked up.',
    ARRIVED_AT    TIMESTAMP_LTZ
        COMMENT 'When the task read the loan application off the stream.',
    DECIDED_AT    TIMESTAMP_LTZ
        COMMENT 'When the underwriting agent finished with it. NULL while in flight.'
)
COMMENT = 'One row per loan application the Module 4 automation handled, with the time it arrived and the time it was decided.';

CREATE OR REPLACE PROCEDURE LENDING.LOANS.UNDERWRITE_ARRIVALS()
RETURNS VARCHAR
LANGUAGE SQL
COMMENT = 'Reads new loan applications off the NEW_APPLICATIONS stream and asks the underwriting agent to decide each one. Called by a triggered task in the optional step of Module 4.'
AS
$$
DECLARE
    c CURSOR FOR
        SELECT APPLICANT_ID
        FROM   LENDING.LOANS.UNDERWRITING_LOG
        WHERE  DECIDED_AT IS NULL
        ORDER  BY ARRIVED_AT;
    n INTEGER DEFAULT 0;
BEGIN
    INSERT INTO LENDING.LOANS.UNDERWRITING_LOG
        (APPLICANT_ID, ARRIVED_AT)
    SELECT APPLICANT_ID, CURRENT_TIMESTAMP()
    FROM   LENDING.LOANS.NEW_APPLICATIONS
    WHERE  STATUS = 'PENDING';

    FOR r IN c DO
        LET aid VARCHAR := r.APPLICANT_ID;
        LET body VARCHAR := '{"messages":[{"role":"user","content":[{"type":"text",'
            || '"text":"Underwrite ' || :aid
            || ' against our lending policy. Record the decision on the loan application."}]}]}';
        LET resp VARCHAR := (SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
                                 'LENDING.LOANS.UNDERWRITING_AGENT',
                                 :body, TRUE));
        UPDATE LENDING.LOANS.UNDERWRITING_LOG
           SET DECIDED_AT = CURRENT_TIMESTAMP()
         WHERE APPLICANT_ID = :aid AND DECIDED_AT IS NULL;
        n := n + 1;
    END FOR;

    RETURN n || ' loan application(s) underwritten';
END;
$$;


/* ---------------------------------------------------------------------------
   12. A starting semantic view

   Every field carries a description; Module 3's agent relies on them.

   DEBT_TO_INCOME_RATIO's description is incomplete on purpose and must stay that
   way. It gives the formula but not the fact that the ratio only covers
   obligations the credit bureau reported, which is why Grant Kelleher's file
   looks sound. Attendees extend it in Module 2.

   MAX_EXPOSURE, POLICY_OVERRIDDEN and ESCALATION_QUESTION are left out. An agent
   reads those from POLICY_CHECK.

   avg_reported_dti is named for the intake ratio because from Module 3 there are
   two.

   No synonyms: current Snowflake guidance is to skip them unless a term is
   industry-specific.
   --------------------------------------------------------------------------- */
CREATE OR REPLACE SEMANTIC VIEW LENDING.LOANS.APPLICATION_ANALYTICS
    TABLES (
        applications AS LENDING.LOANS.APPLICATIONS
            PRIMARY KEY (APPLICANT_ID)
            COMMENT = 'One row per loan application: what the applicant declared at intake, what the credit bureau returned, and the decision if one has been recorded.'
    )
    FACTS (
        applications.credit_score AS CREDIT_SCORE
            COMMENT = 'Consumer credit score returned by the credit bureau.',
        applications.annual_income AS ANNUAL_INCOME
            COMMENT = 'Gross annual income as declared by the applicant.',
        applications.debt_to_income_ratio AS DEBT_TO_INCOME_RATIO
            COMMENT = 'Monthly debt obligations divided by gross monthly income.',
        applications.requested_amount AS REQUESTED_AMOUNT
            COMMENT = 'Loan principal the applicant asked for.',
        applications.approved_amount AS APPROVED_AMOUNT
            COMMENT = 'Principal actually approved. Zero on a declined file, and empty while a loan application is still pending.',
        applications.years_employed AS YEARS_EMPLOYED
            COMMENT = 'Years in current employment or self-employment.'
    )
    DIMENSIONS (
        applications.applicant_id AS APPLICANT_ID
            COMMENT = 'Unique applicant identifier, for example APP_1004.',
        applications.first_name AS FIRST_NAME
            COMMENT = 'Applicant given name.',
        applications.last_name AS LAST_NAME
            COMMENT = 'Applicant family name.',
        applications.loan_purpose AS LOAN_PURPOSE
            COMMENT = 'What the applicant intends to use the money for.',
        applications.employment_status AS EMPLOYMENT_STATUS
            COMMENT = 'employed, self-employed or unemployed. Self-employed income is evidenced by business records rather than payroll, so it takes more work to verify.',
        applications.status AS STATUS
            COMMENT = 'Where the loan application has got to: PENDING until something decides it, then APPROVED, DECLINED or ESCALATED. This is the only column that says whether a file is still waiting.',
        applications.policy_tier AS POLICY_TIER
            COMMENT = 'The lending tier policy placed this file in. Written when a decision is recorded, so it is empty on a pending loan application.',
        applications.application_date AS APPLICATION_DATE
            COMMENT = 'Date the loan application was submitted.'
    )
    METRICS (
        applications.application_count AS COUNT(applications.applicant_id)
            COMMENT = 'Number of loan applications.',
        applications.avg_credit_score AS AVG(applications.credit_score)
            COMMENT = 'Average credit score.',
        applications.avg_annual_income AS AVG(applications.annual_income)
            COMMENT = 'Average declared annual income.',
        applications.avg_reported_dti AS AVG(applications.debt_to_income_ratio)
            COMMENT = 'Average debt-to-income ratio as reported at intake.',
        applications.avg_requested AS AVG(applications.requested_amount)
            COMMENT = 'Average principal requested.',
        applications.total_requested AS SUM(applications.requested_amount)
            COMMENT = 'Total principal requested.',
        applications.total_approved AS SUM(applications.approved_amount)
            COMMENT = 'Total principal this bank has approved.'
    )
    COMMENT = 'Loan applications for Northwind Financial consumer lending: what was requested, what the bureau reported, and what has been decided.';


---------------------------------

----- Load the applicant documents onto the stage -----
/* The PDFs are in the guide's assets folder. AI_PARSE_DOCUMENT can
   only read from a stage, so they are copied onto one. COPY FILES copies them
   byte for byte, uncompressed, which is what AI_PARSE_DOCUMENT needs. */

COPY FILES
    INTO @LENDING.LOANS.LAB_FILES
    FROM @LENDING.GUIDE_FILES.SFQUICKSTARTS/branches/master/site/sfguides/src/automate-lending-decisions-with-cortex-agents/assets/
    PATTERN = '.*doc_APP_[0-9]+_.*[.]pdf';

/* Without REFRESH the directory table stays empty. */
ALTER STAGE LENDING.LOANS.LAB_FILES REFRESH;
---------------------------------


----- Build the reasoning layer -----
/* Loads the parsed documents and indexes them for search. Attendees do not
   build this. */

/* One row per document.

   The text was parsed once with AI_PARSE_DOCUMENT in LAYOUT mode when the lab
   was built, and is shipped as document_text.json. Parsing on every account
   would give the same text, but it calls Cortex for each document and can take
   minutes. Module 2 shows how the parsing works.

   LAYOUT mode returns markdown, so the monthly payment in a loan agreement
   stays in the same table cell as its label.

   DOC_TYPE keeps the file name's underscores. Module 3 filters on values like
   bank_statement, and a filter that matches nothing returns empty rather than
   erroring. */

CREATE STAGE LENDING.LOANS.PARSED_TEXT
    COMMENT = 'The applicant documents as parsed text, loaded into DOCUMENT_TEXT';

COPY FILES
    INTO @LENDING.LOANS.PARSED_TEXT
    FROM @LENDING.GUIDE_FILES.SFQUICKSTARTS/branches/master/site/sfguides/src/automate-lending-decisions-with-cortex-agents/assets/
    FILES = ('document_text.json');

COPY INTO LENDING.LOANS.DOCUMENT_TEXT (FILE_NAME, APPLICANT_ID, DOC_TYPE, DOC_TEXT)
FROM (SELECT $1:FILE_NAME, $1:APPLICANT_ID, $1:DOC_TYPE, $1:DOC_TEXT
        FROM @LENDING.LOANS.PARSED_TEXT)
FILE_FORMAT = (TYPE = 'JSON');

/* The passages Cortex Search indexes.

   1200 characters with 200 of overlap. The overlap keeps a figure and its label
   in one passage when a split falls between them. */

INSERT INTO LENDING.LOANS.DOCUMENT_CHUNKS
    (CHUNK_ID, FILE_NAME, APPLICANT_ID, DOC_TYPE, CHUNK_TEXT)
SELECT t.FILE_NAME || ':' || c.INDEX,
       t.FILE_NAME,
       t.APPLICANT_ID,
       t.DOC_TYPE,
       c.VALUE::VARCHAR
FROM LENDING.LOANS.DOCUMENT_TEXT t,
     LATERAL FLATTEN(input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(
         t.DOC_TEXT, 'markdown', 1200, 200)) c;

/* The search service.

   ATTRIBUTES fixes what can be filtered later. Module 3 filters on APPLICANT_ID
   and DOC_TYPE, so dropping either breaks it.

   PRIMARY KEY makes a refresh re-embed only the passages that changed.

   Module 3 uses CHUNK_ID and FILE_NAME as its id and title columns, so they have
   to stay in this query.

   The COMMENT is what an agent reads when choosing between tools.

   TARGET_LAG is long because DOCUMENT_CHUNKS is written once, here. Nothing in
   the lab adds a document, so a shorter lag would refresh an index that never
   changes. */

CREATE OR REPLACE CORTEX SEARCH SERVICE
    LENDING.LOANS.DOCUMENT_SEARCH
    ON CHUNK_TEXT
    PRIMARY KEY (CHUNK_ID)
    ATTRIBUTES APPLICANT_ID, DOC_TYPE
    WAREHOUSE = LENDING_WH
    TARGET_LAG = '365 days'
    REQUEST_LOGGING = TRUE
    COMMENT = 'Passages from the documents applicants submitted: bank statements, tax returns, loan agreements, pay stubs and addenda. Search this to verify income, identify recurring payments, and find obligations that do not appear on the consumer credit report.'
    AS SELECT CHUNK_ID, CHUNK_TEXT, APPLICANT_ID, DOC_TYPE, FILE_NAME
       FROM LENDING.LOANS.DOCUMENT_CHUNKS;
---------------------------------


----- The evaluation dataset -----
/* Module 3 builds the agent in iterations, and each iteration needs measuring
   against something decided before any of it was built. That is this.

   Every row is a question and a description of what a good answer contains. An
   LLM judge reads the agent reply and scores it against that description. No row
   names a tool, so the dataset holds what a good answer looks like rather than
   how the agent should go about producing it.

   Four rows, one behaviour each:

     APP_1004  finds what the credit report does not show
     APP_1006  leaves a ratio alone when nothing is wrong with it
     APP_1005  says so when there is no evidence
     rates     declines a question it has no business answering

   GROUND_TRUTH has to be VARIANT. TO_VARIANT guarantees that, where
   OBJECT_CONSTRUCT on its own returns OBJECT and the judge will not read it.
   ground_truth_output is the key the answer correctness judge looks for. */

CREATE OR REPLACE TABLE
    LENDING.LOANS.CREDIT_ANALYST_TEST_QUESTIONS (
    INPUT_QUERY  VARCHAR,
    GROUND_TRUTH VARIANT
);

INSERT INTO LENDING.LOANS.CREDIT_ANALYST_TEST_QUESTIONS
    (INPUT_QUERY, GROUND_TRUTH)
SELECT question,
       TO_VARIANT(OBJECT_CONSTRUCT('ground_truth_output', good_answer))
FROM VALUES

    ('Assess APP_1004 for credit risk. Reconcile the reported debt-to-income ratio against the bank statement and write a credit memo.',
     'Finds monthly obligations of about 7,062.83 on the bank statement, against the 2,580.83 that the reported ratio of 0.19 accounts for on 163,000 gross annual income. Names both obligations the credit report is missing: a commercial term loan payment of 3,870.00 under a personal guarantee, and a co-signed auto loan payment of 612.00. Gives the ratio after diligence as about 0.52, and cites the bank statement and the commercial loan agreement. A poor answer repeats 0.19, or finds one of the two obligations and not the other.'),

    ('Assess APP_1006 for credit risk. Check whether the bank statement supports the reported debt-to-income ratio and write a credit memo.',
     'Finds recurring debits of 3,282.50 a month, which is what a reported ratio of 0.39 on 101,000 gross annual income accounts for, and says nothing is missing and the ratio stands at 0.39. It may add that the business tax return shows most revenue arriving in the middle two quarters, so income is uneven through the year. A poor answer invents an undisclosed debt, or changes the ratio to something other than 0.39.'),

    ('Assess APP_1005 for credit risk and write a credit memo.',
     'Says there are no documents for this applicant, so the reported ratio of 0.47 on 57,400 gross annual income cannot be verified, and says what would be needed to verify it. A poor answer describes a document, quotes a payment amount, or gives a ratio other than the reported one, because there is nothing to derive any of that from.'),

    ('What will interest rates do next year, and should we tighten lending policy because of it?',
     'Says this is outside what it can do, because nothing in the loan applications or the documents forecasts interest rates or sets lending policy, and points to what it can do instead, such as assessing a named applicant. A poor answer forecasts a rate, quotes a figure, or recommends a change to lending policy.')

AS t(question, good_answer);

/* Publish the table as a dataset. An evaluation cannot read a table directly.

   The drop first keeps this script re-runnable. A dataset version is an
   immutable snapshot, so creating one that already exists fails.

   The mapping keys here are the ones this function takes. The evaluation
   configuration in Module 3 uses query_text and ground_truth for the same two
   columns, which is a difference between the two APIs rather than a mistake. */

DROP DATASET IF EXISTS LENDING.LOANS.CREDIT_ANALYST_TESTS;

CALL SYSTEM$CREATE_EVALUATION_DATASET(
    'Cortex Agent',
    'LENDING.LOANS.CREDIT_ANALYST_TEST_QUESTIONS',
    'LENDING.LOANS.CREDIT_ANALYST_TESTS',
    OBJECT_CONSTRUCT(
        'query_text',     'INPUT_QUERY',
        'expected_tools', 'GROUND_TRUTH'
    )
);
---------------------------------


----- The evaluation configuration -----
/* An evaluation run started from SQL reads its settings from a YAML file on a
   stage: which agent, which dataset, which metrics. None of that varies through
   Module 3, and writing it teaches nobody anything, so it is shipped here and
   the module spends its time on the agent instead.

   The run name is an argument of EXECUTE_AI_EVALUATION rather than part of this
   file, so one configuration serves every run in the module.

   The stage needs a file format that reads a file as lines of text. Without it
   Snowflake parses the YAML as CSV and the run fails to read its own settings.

   This is not LAB_FILES. That stage has a directory table and holds the twelve
   documents the applicants submitted, which Module 1 lists back. A config file
   in there would look like a thirteenth document.

   The files are copied from the guide's assets folder. */

CREATE FILE FORMAT
    LENDING.LOANS.YAML_FILE_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = NONE
    RECORD_DELIMITER = '\n'
    SKIP_HEADER = 0
    FIELD_OPTIONALLY_ENCLOSED_BY = NONE
    ESCAPE_UNENCLOSED_FIELD = NONE
    COMMENT = 'Reads a YAML file as lines of text';

CREATE STAGE
    LENDING.LOANS.LAB_STAGE
    DIRECTORY = (ENABLE = TRUE)
    FILE_FORMAT = LENDING.LOANS.YAML_FILE_FORMAT
    COMMENT = 'Lab configuration files: the evaluation configurations';

COPY FILES
    INTO @LENDING.LOANS.LAB_STAGE/
    FROM @LENDING.GUIDE_FILES.SFQUICKSTARTS/branches/master/site/sfguides/src/automate-lending-decisions-with-cortex-agents/assets/
    FILES = ('credit_analyst_baseline_eval.yaml', 'credit_analyst_eval.yaml');

ALTER STAGE LENDING.LOANS.LAB_STAGE REFRESH;
---------------------------------

----- Provision Module 3 improved agent and Module 4 agents and MCP server -----

CREATE OR REPLACE AGENT LENDING.LOANS.CREDIT_ANALYST_AGENT_IMPROVED
  WITH PROFILE = '{"display_name": "Credit Analyst Agent (Improved)"}'
  COMMENT = 'Assesses credit risk for one applicant, reconciles the debt-to-income ratio against submitted documents, and writes a credit memo.'
  FROM SPECIFICATION
  $$
models:
  orchestration: "claude-sonnet-4-5"

orchestration:
  budget:
    seconds: 300
    tokens: 32000

instructions:
  response: |
    Write the memo the way a credit analyst writes a file note. State what you
    found, give the figures behind it, and name the document that each finding
    came from. Do not recommend approving or declining the loan.
  orchestration: |
    Your job is to establish what an applicant actually owes, and to record
    what you found and how you know it. You have **four tools**,
    application_analytics, document_search, recompute_dti and
    write_credit_memo. **Do not use any other tool.**

    Use application_analytics to get the loan application record. Use
    document_search to read the documents the applicant submitted. Filter
    every search to the applicant you were asked about.

    What you can rely on, and what you cannot:

    - Money leaving a bank account is evidence. It happened.
    - The application form is a claim by the applicant.
    - The reported debt-to-income ratio is a claim by the credit bureau. It
      covers only what the bureau could see. Obligations documented in
      another name, such as a company or a family member, are absent from it.

    Reconciling the two is the work. What the bureau saw is the reported
    ratio applied to gross monthly income. What is really being paid is on
    the bank statement. A gap means somebody is being paid whom the bureau
    never saw. Find out who, and on what basis the applicant is liable.

    Liability follows the obligation, not the name on the account. A personal
    guarantee and a co-signed account are real personal debts even where the
    borrower is someone else.

    A document may also establish that the assessment is not the record
    you started from, that a loan application is joint, or that this person
    is supporting evidence for somebody else's file. When a document
    establishes that, it governs. Assess what the documents describe.

    Constraints:

    - Any ratio in the memo must come from recompute_dti. Do not put a ratio
      you worked out yourself in the memo. Pass additional
      obligations as MONTHLY amounts.
    - If a document search returns nothing, the applicant submitted no
      documents. Say so, pass the reported ratio through unchanged, and do
      not keep searching.
    - Also record anything bearing on whether the income will last:
      revenue concentration, expiring contracts, declining revenue,
      seasonality, or arrears on an account the applicant is liable for.
    - Assess only the applicant named in the request. If no applicant is
      named, say the question is outside what you do and write no memo.
    - Otherwise finish with exactly one call to write_credit_memo.
      evidence_refs names the actual files you relied on.

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "application_analytics"
      description: "The loan application record: credit score, declared income, reported debt-to-income ratio, requested amount, employment status. The reported ratio covers only obligations visible on the consumer credit report."
  - tool_spec:
      type: "cortex_search"
      name: "document_search"
      description: "Passages from the documents this applicant submitted: bank statements, tax returns, loan agreements, instalment statements, pay stubs and addenda. Always filter by applicant id."
  - tool_spec:
      type: "generic"
      name: "recompute_dti"
      description: "Recomputes the debt-to-income ratio after diligence finds obligations that were not on the credit report. Returns the new ratio and the arithmetic behind it."
      input_schema:
        type: "object"
        properties:
          REPORTED_DTI:
            type: "number"
            description: "The debt-to-income ratio on the loan application record."
          ANNUAL_INCOME:
            type: "number"
            description: "Gross annual income."
          ADDITIONAL_OBLIGATIONS:
            type: "string"
            description: "The additional MONTHLY payment amounts found during diligence, as a comma-separated list, for example 3870.00,612.00. Amounts only."
        required:
          - "REPORTED_DTI"
          - "ANNUAL_INCOME"
          - "ADDITIONAL_OBLIGATIONS"
  - tool_spec:
      type: "generic"
      name: "write_credit_memo"
      description: "Records the credit memo for this applicant. Call once, at the end."
      input_schema:
        type: "object"
        properties:
          P_APPLICANT_ID:
            type: "string"
            description: "Applicant id, e.g. APP_1004"
          P_RECOMPUTED_DTI:
            type: "number"
            description: "The ratio diligence arrived at. Use the reported ratio if nothing was found."
          P_FINDINGS:
            type: "string"
            description: "Findings as a JSON string."
          P_MEMO_TEXT:
            type: "string"
            description: "The written assessment."
          P_EVIDENCE_REFS:
            type: "string"
            description: "Comma separated filenames of the documents relied on."
        required:
          - "P_APPLICANT_ID"
          - "P_RECOMPUTED_DTI"
          - "P_MEMO_TEXT"
          - "P_EVIDENCE_REFS"

tool_resources:
  application_analytics:
    semantic_view: "LENDING.LOANS.APPLICATION_ANALYTICS"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60
  document_search:
    search_service: "LENDING.LOANS.DOCUMENT_SEARCH"
    max_results: 8
    title_column: "FILE_NAME"
    id_column: "CHUNK_ID"
    columns_and_descriptions:
      CHUNK_TEXT:
        description: "A passage from a document the applicant submitted. Contains transaction lines from bank statements with dates, counterparty names and amounts; revenue figures from tax returns; and terms from loan agreements including monthly payments, and whether the applicant is the borrower, a guarantor or a co-signer."
        type: "string"
        searchable: true
        filterable: false
      FILE_NAME:
        description: "Source filename, formatted doc_<applicant_id>_<doc_type>.pdf, for example doc_APP_1004_bank_statement.pdf."
        type: "string"
        searchable: false
        filterable: false
      APPLICANT_ID:
        description: "Applicant the document belongs to, for example APP_1004. Always filter on this."
        type: "string"
        searchable: false
        filterable: true
      DOC_TYPE:
        description: "Kind of document. Values: bank_statement, pay_stub, business_tax_return, commercial_loan_agreement, auto_loan_statement, coapplicant_addendum. Filter to bank_statement to list recurring payments; to commercial_loan_agreement or auto_loan_statement to establish the terms of an obligation."
        type: "string"
        searchable: false
        filterable: true
  recompute_dti:
    type: "function"
    identifier: "LENDING.LOANS.RECOMPUTE_DTI"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60
  write_credit_memo:
    type: "procedure"
    identifier: "LENDING.LOANS.WRITE_CREDIT_MEMO"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60
  $$;

CREATE OR REPLACE AGENT LENDING.LOANS.UNDERWRITING_AGENT
  WITH PROFILE = '{"display_name": "Underwriting Agent"}'
  COMMENT = 'Decides a loan application from the credit memo: approves within policy, declines where a hard policy check fails, and escalates to a human underwriter otherwise.'
  FROM SPECIFICATION
  $$
models:
  orchestration: "auto"

orchestration:
  budget:
    seconds: 180
    tokens: 32000

instructions:
  response: |
    State the decision, the figures behind it, and the documents they came
    from. Name the policy tier and any failed checks.

  orchestration: |
    ## Role
    You are an underwriter. You assess one loan application at a time.

    ## Goal
    For the applicant named in the request, reach a decision: approve, decline,
    or escalate. Record it with the evidence it rests on. Knowing when a file
    is not ready to decide is correct, not a failure.

    ## What your decision rests on
    Every decision rests on a verified debt-to-income ratio: the ratio the
    credit analyst established by reading the applicant's documents, not the
    ratio reported at intake. The reported ratio is what the credit bureau
    recorded. The verified ratio accounts for every obligation the applicant
    actually carries, including ones the credit bureau did not see.

    If no credit memo exists for this applicant, diligence has not been done.
    You do not decide files that have not been through diligence. Escalate and
    ask: what obligations does this applicant carry that are not on the credit
    report, and what is the correct debt-to-income ratio?

    ## Tool selection
    get_credit_memo: use this first. It tells you whether diligence has been
    done and what it found: whether a memo exists, the recomputed ratio, the
    written assessment, and the documents the analyst relied on.

    application_analytics: use this to get the credit score, annual income,
    requested amount and employment status. These figures reflect what the
    applicant disclosed and what the credit bureau recorded. They do not
    contain what diligence found.

    policy_check: use this to convert the recomputed ratio into policy
    constraints: the tier, the maximum exposure, which hard checks failed, and
    whether the file may be approved automatically. Use the recomputed ratio
    from get_credit_memo, not the reported ratio from application_analytics.
    policy_check returns constraints, not a decision.

    record_decision: call this once to record the outcome. Do not call it to
    explore options and do not call it more than once.

    ## Decision authority
    Approve when policy permits it. Do not approve above max_exposure under
    any circumstances.

    Decline when a hard policy check fails and the memo establishes the reason.
    A good credit score does not override a documented obligation that breaks
    policy.

    Escalate when the file is incomplete, contradictory, or requires a judgment
    the documented evidence cannot support. Give the reviewer a specific
    question: name what must be determined and what evidence would settle it.
    Never write "please review".

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "application_analytics"
      description: "Answers questions about loan applications: credit score, annual income, requested amount, employment status and the debt-to-income ratio reported at intake."

  - tool_spec:
      type: "generic"
      name: "get_credit_memo"
      description: "Returns the credit memo for one applicant: the ratio reported at intake, the ratio diligence arrived at, the written assessment and the documents relied on. Returns found = false when no memo exists."
      input_schema:
        type: "object"
        properties:
          P_APPLICANT_ID:
            type: "string"
            description: "Applicant identifier, for example APP_1004."
        required:
          - P_APPLICANT_ID

  - tool_spec:
      type: "generic"
      name: "policy_check"
      description: "Returns what lending policy permits: the tier, the maximum exposure, whether the file may be approved automatically, and which hard checks failed. Call it with the ratio established by diligence."
      input_schema:
        type: "object"
        properties:
          CREDIT_SCORE:
            type: "number"
            description: "Consumer credit score."
          DTI:
            type: "number"
            description: "Debt-to-income ratio to assess. Use the recomputed ratio from the memo."
          REQUESTED_AMOUNT:
            type: "number"
            description: "Loan principal requested."
          ANNUAL_INCOME:
            type: "number"
            description: "Gross annual income."
        required:
          - CREDIT_SCORE
          - DTI
          - REQUESTED_AMOUNT
          - ANNUAL_INCOME

  - tool_spec:
      type: "generic"
      name: "record_decision"
      description: "Records the decision on an application. Re-checks policy independently and refuses any approval above the permitted maximum."
      input_schema:
        type: "object"
        properties:
          P_APPLICANT_ID:
            type: "string"
            description: "Applicant identifier."
          P_ACTION:
            type: "string"
            description: "APPROVE, DECLINE or ESCALATE."
          P_RATIONALE:
            type: "string"
            description: "Why, in the underwriter's words, naming the figures and documents."
          P_EVIDENCE_REFS:
            type: "string"
            description: "Documents relied on, comma separated. Pass NONE where there are none."
          P_APPROVED_AMOUNT:
            type: "number"
            description: "Principal approved. Pass 0 for a decline or an escalation."
          P_UNDERWRITER_QUESTION:
            type: "string"
            description: "The question a human must answer. Pass NONE where it does not apply."
        required:
          - P_APPLICANT_ID
          - P_ACTION
          - P_RATIONALE
          - P_EVIDENCE_REFS
          - P_APPROVED_AMOUNT
          - P_UNDERWRITER_QUESTION

tool_resources:
  application_analytics:
    semantic_view: "LENDING.LOANS.APPLICATION_ANALYTICS"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  get_credit_memo:
    type: "function"
    identifier: "LENDING.LOANS.GET_CREDIT_MEMO"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  policy_check:
    type: "function"
    identifier: "LENDING.LOANS.POLICY_CHECK"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  record_decision:
    type: "procedure"
    identifier: "LENDING.LOANS.RECORD_DECISION"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60
  $$;

CREATE OR REPLACE MCP SERVER LENDING.LOANS.CREDIT_ANALYST_MCP
  FROM SPECIFICATION $$
tools:
  - title: "Credit analyst"
    name: "credit_analyst"
    type: "CORTEX_AGENT_RUN"
    identifier: "LENDING.LOANS.CREDIT_ANALYST_AGENT_IMPROVED"
    description: "Performs credit diligence on one named applicant: reads the documents they submitted, reconciles what is actually paid each month against the reported debt-to-income ratio, and writes a credit memo. Ask it to assess a single applicant by id."
$$;

CREATE OR REPLACE AGENT LENDING.LOANS.UNDERWRITER_WITH_DELEGATION_AGENT
  WITH PROFILE = '{"display_name": "Underwriter With Delegation"}'
  COMMENT = 'Decides a loan application from the credit memo. When no memo exists, delegates to the credit analyst over MCP before deciding.'
  FROM SPECIFICATION
  $$
models:
  orchestration: "auto"

orchestration:
  budget:
    seconds: 300
    tokens: 32000

instructions:
  response: |
    State the decision, the figures behind it, and the documents they came
    from. Name the policy tier and any failed checks.

  orchestration: |
    ## Role
    You are an underwriter. You assess one loan application at a time.

    ## Goal
    For the applicant named in the request, reach a decision: approve, decline,
    or escalate. Record it with the evidence it rests on. Knowing when a file
    is not ready to decide is correct, not a failure.

    ## What your decision rests on
    Every decision rests on a verified debt-to-income ratio: the ratio the
    credit analyst established by reading the applicant's documents, not the
    ratio reported at intake. The reported ratio is what the credit bureau
    recorded. The verified ratio accounts for every obligation the applicant
    actually carries, including ones the credit bureau did not see.

    If no credit memo exists for this applicant, the credit analyst has not
    assessed them yet. Ask the credit analyst to perform diligence on this
    applicant, then call get_credit_memo again before proceeding.

    ## Tool selection
    get_credit_memo: use this first. It tells you whether diligence has been
    done and what it found: whether a memo exists, the recomputed ratio, the
    written assessment, and the documents the analyst relied on.

    application_analytics: use this to get the credit score, annual income,
    requested amount and employment status. These figures reflect what the
    applicant disclosed and what the credit bureau recorded. They do not
    contain what diligence found.

    policy_check: use this to convert the recomputed ratio into policy
    constraints: the tier, the maximum exposure, which hard checks failed, and
    whether the file may be approved automatically. Use the recomputed ratio
    from get_credit_memo, not the reported ratio from application_analytics.
    policy_check returns constraints, not a decision.

    record_decision: call this once to record the outcome. Do not call it to
    explore options and do not call it more than once.

    ## Decision authority
    Approve when policy permits it. Do not approve above max_exposure under
    any circumstances.

    Decline when a hard policy check fails and the memo establishes the reason.
    A good credit score does not override a documented obligation that breaks
    policy.

    Escalate when the file is incomplete, contradictory, or requires a judgment
    the documented evidence cannot support. Give the reviewer a specific
    question: name what must be determined and what evidence would settle it.
    Never write "please review".

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "application_analytics"
      description: "Answers questions about loan applications: credit score, annual income, requested amount, employment status and the debt-to-income ratio reported at intake."

  - tool_spec:
      type: "generic"
      name: "get_credit_memo"
      description: "Returns the credit memo for one applicant: the ratio reported at intake, the ratio diligence arrived at, the written assessment and the documents relied on. Returns found = false when no memo exists."
      input_schema:
        type: "object"
        properties:
          P_APPLICANT_ID:
            type: "string"
            description: "Applicant identifier, for example APP_1004."
        required:
          - P_APPLICANT_ID

  - tool_spec:
      type: "generic"
      name: "policy_check"
      description: "Returns what lending policy permits: the tier, the maximum exposure, whether the file may be approved automatically, and which hard checks failed. Call it with the ratio established by diligence."
      input_schema:
        type: "object"
        properties:
          CREDIT_SCORE:
            type: "number"
            description: "Consumer credit score."
          DTI:
            type: "number"
            description: "Debt-to-income ratio to assess. Use the recomputed ratio from the memo."
          REQUESTED_AMOUNT:
            type: "number"
            description: "Loan principal requested."
          ANNUAL_INCOME:
            type: "number"
            description: "Gross annual income."
        required:
          - CREDIT_SCORE
          - DTI
          - REQUESTED_AMOUNT
          - ANNUAL_INCOME

  - tool_spec:
      type: "generic"
      name: "record_decision"
      description: "Records the decision on an application. Re-checks policy independently and refuses any approval above the permitted maximum."
      input_schema:
        type: "object"
        properties:
          P_APPLICANT_ID:
            type: "string"
            description: "Applicant identifier."
          P_ACTION:
            type: "string"
            description: "APPROVE, DECLINE or ESCALATE."
          P_RATIONALE:
            type: "string"
            description: "Why, in the underwriter's words, naming the figures and documents."
          P_EVIDENCE_REFS:
            type: "string"
            description: "Documents relied on, comma separated. Pass NONE where there are none."
          P_APPROVED_AMOUNT:
            type: "number"
            description: "Principal approved. Pass 0 for a decline or an escalation."
          P_UNDERWRITER_QUESTION:
            type: "string"
            description: "The question a human must answer. Pass NONE where it does not apply."
        required:
          - P_APPLICANT_ID
          - P_ACTION
          - P_RATIONALE
          - P_EVIDENCE_REFS
          - P_APPROVED_AMOUNT
          - P_UNDERWRITER_QUESTION

tool_resources:
  application_analytics:
    semantic_view: "LENDING.LOANS.APPLICATION_ANALYTICS"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  get_credit_memo:
    type: "function"
    identifier: "LENDING.LOANS.GET_CREDIT_MEMO"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  policy_check:
    type: "function"
    identifier: "LENDING.LOANS.POLICY_CHECK"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

  record_decision:
    type: "procedure"
    identifier: "LENDING.LOANS.RECORD_DECISION"
    execution_environment:
      type: "warehouse"
      warehouse: "LENDING_WH"
      query_timeout: 60

mcp_servers:
  - server_spec:
      name: "LENDING.LOANS.CREDIT_ANALYST_MCP"
  $$;

---------------------------------

----- Check the setup -----
/* One row. Every column should read as described in setup step 3 of the lab
   guide. APP_1005 submitted no documents, so five applicants have them. */

SELECT
    (SELECT COUNT(*) FROM LENDING.LOANS.DOCUMENT_TEXT
      WHERE DOC_TEXT IS NOT NULL AND DOC_TEXT <> '')          AS DOCUMENTS_PARSED,
    (SELECT COUNT(DISTINCT APPLICANT_ID)
       FROM LENDING.LOANS.DOCUMENT_TEXT)                       AS APPLICANTS_WITH_DOCUMENTS,
    (SELECT COUNT(*) FROM LENDING.LOANS.DOCUMENT_CHUNKS)       AS PASSAGES_INDEXED,
    ARRAY_SIZE(PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
        'LENDING.LOANS.DOCUMENT_SEARCH',
        '{"query": "monthly payment obligation on a loan",
          "columns": ["CHUNK_TEXT"],
          "filter": {"@eq": {"APPLICANT_ID": "APP_1004"}},
          "limit": 3}'))['results'])                           AS SEARCH_RESULTS,
    (SELECT COUNT(*) FROM DIRECTORY(@LENDING.LOANS.LAB_STAGE)) AS EVAL_CONFIGS,
    IFF(DOCUMENTS_PARSED = 12 AND SEARCH_RESULTS = 3 AND EVAL_CONFIGS = 2,
        'Setup complete', 'Setup incomplete: check the columns')  AS STATUS;

