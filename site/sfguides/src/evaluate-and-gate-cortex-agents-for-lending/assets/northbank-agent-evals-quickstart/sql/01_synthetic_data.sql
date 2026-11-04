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

-- =============================================================================
-- Northbank agent evals quickstart | 01 Synthetic loan book
-- Deterministic generator: every run produces identical rows, so the expected
-- answers in data/eval_questions.ndjson stay correct. Do not change the HASH salts.
-- Run in a Snowsight SQL worksheet (Run All), in numeric order.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE WAREHOUSE NORTHBANK_EVAL_WH;

-- Traps built into the data (see README "What makes this dataset hard"):
--   duplicate submissions, missing incomes, a superseded credit policy, a 2025-Q3 arrears spike,
--   vulnerable customers with and without forbearance, and keyword distractors in the notes.

-- Generate 8,000 synthetic Northbank customers
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.CUSTOMERS AS
WITH g AS (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS n FROM TABLE(GENERATOR(ROWCOUNT => 8000))),
u AS (
  SELECT n,
    (ABS(HASH(n,'emp')) % 100) AS emp_b,
    (ABS(HASH(n,'inc')) % 10000) / 10000.0 AS inc_u
  FROM g
)
SELECT
  'C' || LPAD(n, 5, '0') AS CUSTOMER_ID,
  DATEADD(day, -(ABS(HASH(n,'dob')) % (57*365)), '2008-01-01'::DATE) AS DATE_OF_BIRTH,
  ARRAY_CONSTRUCT('London','South East','South West','East of England','West Midlands','East Midlands',
                  'Yorkshire and the Humber','North West','North East','Wales','Scotland','Northern Ireland')
    [ABS(HASH(n,'reg')) % 12]::VARCHAR AS REGION,
  CASE WHEN emp_b < 60 THEN 'FULL_TIME' WHEN emp_b < 72 THEN 'PART_TIME' WHEN emp_b < 85 THEN 'SELF_EMPLOYED'
       WHEN emp_b < 95 THEN 'RETIRED' ELSE 'UNEMPLOYED' END AS EMPLOYMENT_STATUS,
  ROUND(CASE WHEN emp_b < 60 THEN 22000 + inc_u * 68000
             WHEN emp_b < 72 THEN 9000 + inc_u * 16000
             WHEN emp_b < 85 THEN 15000 + inc_u * 75000
             WHEN emp_b < 95 THEN 14000 + inc_u * 22000
             ELSE 4000 + inc_u * 8000 END, -2) AS ANNUAL_INCOME,
  DATEADD(day, ABS(HASH(n,'since')) % (7*365), '2018-01-01'::DATE) AS CUSTOMER_SINCE
FROM u;

-- Generate applications with deliberate duplicates and null incomes
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS AS
WITH g AS (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) AS n FROM TABLE(GENERATOR(ROWCOUNT => 20000))),
base AS (
  SELECT
    n,
    'A' || LPAD(n, 6, '0') AS APPLICATION_ID,
    'C' || LPAD(1 + ABS(HASH(n,'cust')) % 8000, 5, '0') AS CUSTOMER_ID,
    DATEADD(minute, ABS(HASH(n,'min')) % 1440,
      DATEADD(day, ABS(HASH(n,'day')) % 546, '2025-01-01'::TIMESTAMP_NTZ)) AS APPLICATION_TS,
    IFF(ABS(HASH(n,'prod')) % 100 < 60, 'PERSONAL_LOAN', 'CREDIT_CARD') AS PRODUCT,
    (ABS(HASH(n,'amt')) % 10000) / 10000.0 AS amt_u,
    ABS(HASH(n,'term')) % 5 AS term_i,
    (ABS(HASH(n,'inc')) % 10000) / 10000.0 AS inc_u,
    (ABS(HASH(n,'com')) % 10000) / 10000.0 AS com_u,
    ABS(HASH(n,'null')) % 100 AS null_b,
    ABS(HASH(n,'chan')) % 100 AS chan_b
  FROM g
),
apps AS (
  SELECT
    b.APPLICATION_ID, b.CUSTOMER_ID, b.APPLICATION_TS, b.PRODUCT,
    IFF(b.PRODUCT = 'PERSONAL_LOAN', ROUND((1000 + b.amt_u * 24000) / 500) * 500,
                                     ROUND((500 + b.amt_u * 7500) / 250) * 250) AS REQUESTED_AMOUNT,
    IFF(b.PRODUCT = 'PERSONAL_LOAN', ARRAY_CONSTRUCT(12,24,36,48,60)[b.term_i]::INT, NULL) AS TERM_MONTHS,
    IFF(b.null_b < 3, NULL, ROUND(c.ANNUAL_INCOME * (0.9 + b.inc_u * 0.2), -2)) AS DECLARED_ANNUAL_INCOME,
    ROUND(c.ANNUAL_INCOME / 12 * (0.05 + b.com_u * 0.40), 0) AS MONTHLY_COMMITMENTS,
    CASE WHEN b.chan_b < 45 THEN 'APP' WHEN b.chan_b < 85 THEN 'WEB' ELSE 'BROKER' END AS CHANNEL
  FROM base b JOIN NORTHBANK_AGENT_EVALS.DEMO.CUSTOMERS c ON c.CUSTOMER_ID = b.CUSTOMER_ID
),
dups AS (
  SELECT 'A9' || SUBSTR(APPLICATION_ID, 2) AS APPLICATION_ID, CUSTOMER_ID,
         DATEADD(minute, 1 + ABS(HASH(APPLICATION_ID,'dupmin')) % 20, APPLICATION_TS) AS APPLICATION_TS,
         PRODUCT, REQUESTED_AMOUNT, TERM_MONTHS, DECLARED_ANNUAL_INCOME, MONTHLY_COMMITMENTS, CHANNEL
  FROM apps
  WHERE ABS(HASH(APPLICATION_ID,'dup')) % 67 = 0
)
SELECT * FROM apps
UNION ALL
SELECT * FROM dups;

-- Generate bureau scores per application (0-999 scale)
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.BUREAU_SCORES AS
SELECT
  APPLICATION_ID,
  CUSTOMER_ID,
  'NBUREAU' AS BUREAU,
  APPLICATION_TS::DATE AS SCORE_DATE,
  LEAST(999, GREATEST(0,
    420 + ABS(HASH(CUSTOMER_ID,'basescore')) % 480
        + (ABS(HASH(CUSTOMER_ID, APPLICATION_TS::DATE,'noise')) % 81) - 40)) AS CREDIT_SCORE
FROM NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS;

-- Generate credit decisions applying v1/v2 cut-off and affordability rules
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.DECISIONS AS
WITH x AS (
  SELECT a.APPLICATION_ID, a.CUSTOMER_ID, a.APPLICATION_TS::DATE AS app_date, a.PRODUCT,
         a.REQUESTED_AMOUNT, a.TERM_MONTHS, a.DECLARED_ANNUAL_INCOME, a.MONTHLY_COMMITMENTS,
         s.CREDIT_SCORE,
         IFF(a.APPLICATION_TS::DATE < '2026-03-01', 'CREDIT_POLICY_V1', 'CREDIT_POLICY_V2') AS POLICY_VERSION,
         IFF(a.APPLICATION_TS::DATE < '2026-03-01', 620, 640) AS SCORE_CUTOFF,
         IFF(a.PRODUCT = 'PERSONAL_LOAN', a.REQUESTED_AMOUNT * 1.08 / a.TERM_MONTHS, a.REQUESTED_AMOUNT * 0.03) AS new_payment
  FROM NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS a
  JOIN NORTHBANK_AGENT_EVALS.DEMO.BUREAU_SCORES s ON s.APPLICATION_ID = a.APPLICATION_ID
),
d AS (
  SELECT *,
    ROUND(DIV0NULL(MONTHLY_COMMITMENTS + new_payment, DECLARED_ANNUAL_INCOME / 12), 4) AS DEBT_TO_INCOME_RATIO
  FROM x
)
SELECT
  'D' || SUBSTR(APPLICATION_ID, 2) AS DECISION_ID,
  APPLICATION_ID,
  CUSTOMER_ID,
  DATEADD(day, ABS(HASH(APPLICATION_ID,'dd')) % 3, app_date) AS DECISION_DATE,
  POLICY_VERSION,
  SCORE_CUTOFF,
  CREDIT_SCORE,
  IFF(DECLARED_ANNUAL_INCOME IS NULL, NULL, DEBT_TO_INCOME_RATIO) AS DEBT_TO_INCOME_RATIO,
  CASE WHEN DECLARED_ANNUAL_INCOME IS NULL THEN 'REFERRED'
       WHEN CREDIT_SCORE < SCORE_CUTOFF THEN 'DECLINED'
       WHEN DEBT_TO_INCOME_RATIO > 0.50 THEN 'DECLINED'
       ELSE 'APPROVED' END AS DECISION,
  CASE WHEN DECLARED_ANNUAL_INCOME IS NULL THEN 'INCOME_NOT_VERIFIED'
       WHEN CREDIT_SCORE < SCORE_CUTOFF THEN 'SCORE_BELOW_CUTOFF'
       WHEN DEBT_TO_INCOME_RATIO > 0.50 THEN 'AFFORDABILITY'
       ELSE NULL END AS DECISION_REASON
FROM d;

-- Book loans and credit cards from approved, non-duplicate applications
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.LOANS AS
SELECT
  'L' || SUBSTR(a.APPLICATION_ID, 2) AS LOAN_ID,
  a.APPLICATION_ID,
  a.CUSTOMER_ID,
  a.PRODUCT,
  a.REQUESTED_AMOUNT AS PRINCIPAL_OR_LIMIT,
  a.TERM_MONTHS,
  IFF(a.PRODUCT = 'PERSONAL_LOAN',
      ROUND(LEAST(29.9, GREATEST(6.9, 29.9 - (d.CREDIT_SCORE - 620) * 0.07)), 1),
      ROUND(LEAST(34.9, GREATEST(19.9, 34.9 - (d.CREDIT_SCORE - 620) * 0.05)), 1)) AS APR_PCT,
  DATEADD(day, 3, d.DECISION_DATE) AS START_DATE,
  YEAR(DATEADD(day, 3, d.DECISION_DATE)) || '-Q' || QUARTER(DATEADD(day, 3, d.DECISION_DATE)) AS VINTAGE_QUARTER,
  d.CREDIT_SCORE AS SCORE_AT_ORIGINATION
FROM NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS a
JOIN NORTHBANK_AGENT_EVALS.DEMO.DECISIONS d ON d.APPLICATION_ID = a.APPLICATION_ID
WHERE d.DECISION = 'APPROVED'
  AND LENGTH(a.APPLICATION_ID) = 7
  AND ABS(HASH(a.APPLICATION_ID,'takeup')) % 100 < 92
  AND DATEADD(day, 3, d.DECISION_DATE) <= '2026-06-30';

-- Regenerate performance: only 70% of vulnerable customers get forbearance (trap)
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.LOAN_PERFORMANCE AS
WITH m AS (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1 AS mi FROM TABLE(GENERATOR(ROWCOUNT => 20))),
l AS (
  SELECT lo.*,
    LEAST(0.30, GREATEST(0.01, 0.02 + (720 - SCORE_AT_ORIGINATION) * 0.0008))
      * IFF(PRODUCT = 'PERSONAL_LOAN' AND VINTAGE_QUARTER = '2025-Q3', 3, 1) AS p_delq,
    (ABS(HASH(LOAN_ID,'delq')) % 10000) / 10000.0 AS u_delq,
    2 + ABS(HASH(LOAN_ID,'onset')) % 10 AS onset_m,
    (ABS(HASH(CUSTOMER_ID,'vuln')) % 100 < 8) AS is_vuln,
    ABS(HASH(LOAN_ID,'forb')) % 100 AS forb_b,
    ABS(HASH(LOAN_ID,'vforb')) % 100 AS vforb_b,
    0.2 + (ABS(HASH(LOAN_ID,'util')) % 70) / 100.0 AS util
  FROM NORTHBANK_AGENT_EVALS.DEMO.LOANS lo
),
lm AS (
  SELECT l.*, m.mi, LAST_DAY(DATEADD(month, m.mi, l.START_DATE)) AS MONTH_END,
    (l.u_delq < l.p_delq) AS ever_delq,
    (l.u_delq < l.p_delq AND ((l.is_vuln AND l.vforb_b < 70) OR (NOT l.is_vuln AND l.forb_b < 25))) AS gets_forb
  FROM l JOIN m ON LAST_DAY(DATEADD(month, m.mi, l.START_DATE)) <= '2026-06-30'
              AND (l.TERM_MONTHS IS NULL OR m.mi < l.TERM_MONTHS)
)
SELECT
  LOAN_ID, CUSTOMER_ID, PRODUCT, VINTAGE_QUARTER, MONTH_END, mi AS MONTHS_ON_BOOK,
  CASE WHEN NOT ever_delq OR mi < onset_m THEN 0
       WHEN gets_forb AND mi >= onset_m + 7 THEN 0
       WHEN gets_forb THEN 30
       ELSE LEAST((mi - onset_m + 1) * 30, 180) END AS DAYS_PAST_DUE,
  ROUND(IFF(PRODUCT = 'PERSONAL_LOAN',
            PRINCIPAL_OR_LIMIT * GREATEST(0, 1 - mi / TERM_MONTHS),
            PRINCIPAL_OR_LIMIT * util), 2) AS BALANCE,
  gets_forb AS _GETS_FORB, onset_m AS _ONSET_M
FROM lm;

-- Derive arrears cases from loan performance
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.ARREARS_CASES AS
WITH first_delq AS (
  SELECT LOAN_ID, CUSTOMER_ID, PRODUCT, MIN(MONTH_END) AS OPENED_DATE, MAX(_GETS_FORB::INT) AS has_forb
  FROM NORTHBANK_AGENT_EVALS.DEMO.LOAN_PERFORMANCE WHERE DAYS_PAST_DUE > 0 GROUP BY 1,2,3
),
latest AS (
  SELECT LOAN_ID, MONTH_END AS AS_OF_DATE, DAYS_PAST_DUE AS CURRENT_DPD, BALANCE AS CURRENT_BALANCE
  FROM NORTHBANK_AGENT_EVALS.DEMO.LOAN_PERFORMANCE
  QUALIFY ROW_NUMBER() OVER (PARTITION BY LOAN_ID ORDER BY MONTH_END DESC) = 1
)
SELECT
  'R' || SUBSTR(f.LOAN_ID, 2) AS CASE_ID,
  f.LOAN_ID, f.CUSTOMER_ID, f.PRODUCT, f.OPENED_DATE, l.AS_OF_DATE, l.CURRENT_DPD, l.CURRENT_BALANCE,
  IFF(l.CURRENT_DPD > 0, 'OPEN', 'CURED') AS CASE_STATUS,
  CASE WHEN l.CURRENT_DPD = 0 THEN NULL
       WHEN l.CURRENT_DPD < 60 THEN 'EARLY'
       WHEN l.CURRENT_DPD < 90 THEN 'LATE'
       ELSE 'DEFAULT' END AS ARREARS_STAGE,
  CASE WHEN l.CURRENT_DPD = 0 THEN 'CLOSE_CASE'
       WHEN f.has_forb = 1 THEN 'MONITOR_ARRANGEMENT'
       WHEN l.CURRENT_DPD < 60 THEN 'SEND_ARREARS_NOTICE'
       WHEN l.CURRENT_DPD < 90 THEN 'REFER_TO_COLLECTIONS'
       ELSE 'ISSUE_DEFAULT_NOTICE' END AS NEXT_ACTION
FROM first_delq f JOIN latest l ON l.LOAN_ID = f.LOAN_ID;

-- Create forbearance arrangements for cases with forbearance
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.FORBEARANCE AS
SELECT
  'F' || SUBSTR(c.CASE_ID, 2) AS ARRANGEMENT_ID,
  c.CASE_ID, c.LOAN_ID, c.CUSTOMER_ID,
  ARRAY_CONSTRUCT('REDUCED_PAYMENT_PLAN','PAYMENT_HOLIDAY','INTEREST_FREEZE','TERM_EXTENSION')
    [ABS(HASH(c.CASE_ID,'ftype')) % 4]::VARCHAR AS ARRANGEMENT_TYPE,
  LAST_DAY(DATEADD(month, 1, c.OPENED_DATE)) AS START_DATE,
  LAST_DAY(DATEADD(month, 7, c.OPENED_DATE)) AS END_DATE,
  IFF(LAST_DAY(DATEADD(month, 7, c.OPENED_DATE)) <= '2026-06-30', 'COMPLETED', 'ACTIVE') AS ARRANGEMENT_STATUS
FROM NORTHBANK_AGENT_EVALS.DEMO.ARREARS_CASES c
WHERE c.LOAN_ID IN (SELECT DISTINCT LOAN_ID FROM NORTHBANK_AGENT_EVALS.DEMO.LOAN_PERFORMANCE WHERE _GETS_FORB);

-- Drop helper columns from LOAN_PERFORMANCE
ALTER TABLE NORTHBANK_AGENT_EVALS.DEMO.LOAN_PERFORMANCE DROP COLUMN _GETS_FORB, _ONSET_M;

-- Create hidden customer vulnerability labels
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.GROUND_TRUTH.CUSTOMER_VULNERABILITY AS
SELECT CUSTOMER_ID,
  (ABS(HASH(CUSTOMER_ID,'vuln')) % 100 < 8) AS IS_VULNERABLE,
  IFF(ABS(HASH(CUSTOMER_ID,'vuln')) % 100 < 8,
      ARRAY_CONSTRUCT('BEREAVEMENT','JOB_LOSS','SERIOUS_ILLNESS','MENTAL_HEALTH','CARER')[ABS(HASH(CUSTOMER_ID,'vtype')) % 5]::VARCHAR,
      NULL) AS VULNERABILITY_TYPE,
  IFF(ABS(HASH(CUSTOMER_ID,'vuln')) % 100 < 8,
      IFF(ABS(HASH(CUSTOMER_ID,'vsubtle')) % 100 < 40, 'SUBTLE', 'EXPLICIT'), NULL) AS SIGNAL_STRENGTH
FROM NORTHBANK_AGENT_EVALS.DEMO.CUSTOMERS;

-- ---- Customer contact notes ------------------------------------------------

-- Create note template library (explicit/subtle vulnerability, neutral, distractor)
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTE_TEMPLATES (TEMPLATE_ID INT, KIND VARCHAR, VULNERABILITY_TYPE VARCHAR, SIGNAL_STRENGTH VARCHAR, TEXT VARCHAR) AS
SELECT * FROM VALUES
(1,'VULN','BEREAVEMENT','EXPLICIT','Customer called to say her husband passed away last month and she is now managing the household finances alone. Asked for some time before the next payment.'),
(2,'VULN','BEREAVEMENT','EXPLICIT','Customer explained his mother died recently and he has been paying the funeral costs. Says he is struggling to keep up with repayments.'),
(3,'VULN','BEREAVEMENT','EXPLICIT','Bereavement: customer''s partner died in the spring. Customer upset on the call and asked us to stop sending letters addressed to both of them.'),
(4,'VULN','JOB_LOSS','EXPLICIT','Customer has been made redundant and has no income until a new job starts. Asked about options for reducing payments.'),
(5,'VULN','JOB_LOSS','EXPLICIT','Customer lost their job at the warehouse two weeks ago and is now claiming Universal Credit.'),
(6,'VULN','JOB_LOSS','EXPLICIT','Customer confirmed redundancy; final salary was paid last month and there is no other household income.'),
(7,'VULN','SERIOUS_ILLNESS','EXPLICIT','Customer diagnosed with cancer and starting chemotherapy, unable to work for several months.'),
(8,'VULN','SERIOUS_ILLNESS','EXPLICIT','Customer is in hospital after a stroke. His daughter called on his behalf with his consent.'),
(9,'VULN','SERIOUS_ILLNESS','EXPLICIT','Customer has a serious heart condition and is on long-term sick leave on statutory sick pay.'),
(10,'VULN','MENTAL_HEALTH','EXPLICIT','Customer said he is being treated for depression and finds letters about the debt overwhelming.'),
(11,'VULN','MENTAL_HEALTH','EXPLICIT','Customer disclosed severe anxiety and asked to be contacted by email only.'),
(12,'VULN','MENTAL_HEALTH','EXPLICIT','Customer mentioned a bipolar disorder diagnosis and said she struggles to manage money during episodes.'),
(13,'VULN','CARER','EXPLICIT','Customer has become a full-time carer for her disabled son and has reduced her working hours.'),
(14,'VULN','CARER','EXPLICIT','Customer is now caring for his elderly father who has dementia; household income has dropped.'),
(15,'VULN','CARER','EXPLICIT','Customer has given up work to care for his wife after her accident.'),
(21,'VULN','BEREAVEMENT','SUBTLE','Customer said things have been very difficult since the funeral and she has not been opening her post.'),
(22,'VULN','BEREAVEMENT','SUBTLE','Customer asked us to remove the second name from correspondence, saying he is not with us any more.'),
(23,'VULN','BEREAVEMENT','SUBTLE','Customer said she is sorting out her late father''s affairs and will call back when she can.'),
(24,'VULN','JOB_LOSS','SUBTLE','Customer said work dried up when the site closed and he is looking for something new.'),
(25,'VULN','JOB_LOSS','SUBTLE','Customer mentioned his last payslip was in May and he is waiting to hear back from interviews.'),
(26,'VULN','JOB_LOSS','SUBTLE','Customer asked whether payments can wait until the new job starts, as she is between jobs at the moment.'),
(27,'VULN','SERIOUS_ILLNESS','SUBTLE','Customer has been off work since the operation and is not sure when she will be back.'),
(28,'VULN','SERIOUS_ILLNESS','SUBTLE','Customer said treatment is every week at the moment so she cannot get to the branch.'),
(29,'VULN','SERIOUS_ILLNESS','SUBTLE','Customer''s wife called to say he is still on the ward and asked what happens to the account.'),
(30,'VULN','MENTAL_HEALTH','SUBTLE','Customer said she has not been coping lately and the letters make it worse.'),
(31,'VULN','MENTAL_HEALTH','SUBTLE','Customer became very distressed on the call and said he cannot deal with this right now.'),
(32,'VULN','MENTAL_HEALTH','SUBTLE','Customer said his GP has signed him off for stress and he is not sleeping.'),
(33,'VULN','CARER','SUBTLE','Customer said she can only work mornings now because of her mum''s hospital appointments.'),
(34,'VULN','CARER','SUBTLE','Customer explained he has to be at home most days for his son and money is tight.'),
(35,'VULN','CARER','SUBTLE','Customer said she has had to cut her hours to look after her husband.'),
(41,'ARREARS_NEUTRAL',NULL,NULL,'Customer forgot to update the direct debit after changing bank; will pay the arrears on Friday.'),
(42,'ARREARS_NEUTRAL',NULL,NULL,'Customer promised to clear the missed payment on payday.'),
(43,'ARREARS_NEUTRAL',NULL,NULL,'Customer disputed the late fee and said the payment was sent a day late because of the bank holiday.'),
(44,'ARREARS_NEUTRAL',NULL,NULL,'No answer on outbound arrears call; voicemail left asking customer to call back.'),
(45,'ARREARS_NEUTRAL',NULL,NULL,'Customer was on holiday and missed the reminder; payment arranged by card on the call.'),
(51,'SERVICE',NULL,NULL,'Customer updated their address details.'),
(52,'SERVICE',NULL,NULL,'Customer asked how to activate their new card; walked through app activation.'),
(53,'SERVICE',NULL,NULL,'Customer requested a copy of the credit agreement; sent by email.'),
(54,'SERVICE',NULL,NULL,'Customer asked how to make an overpayment on the loan.'),
(55,'SERVICE',NULL,NULL,'Customer queried the interest on the latest statement; calculation explained.'),
(56,'SERVICE',NULL,NULL,'Customer reported card lost; card blocked and replacement issued.'),
(61,'DISTRACTOR',NULL,NULL,'Customer asked whether the loan includes payment protection for illness or redundancy; explained Northbank does not offer PPI.'),
(62,'DISTRACTOR',NULL,NULL,'Customer said a colleague was made redundant and asked whether that affects her own account; no change to her own circumstances.'),
(63,'DISTRACTOR',NULL,NULL,'Customer said her neighbour passed away and asked in general how a family member could be authorised on an account; customer herself is fine.');

-- Generate ~2.5k customer notes from templates (staged with labels)
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTES_STAGING AS
WITH v AS (SELECT * FROM NORTHBANK_AGENT_EVALS.GROUND_TRUTH.CUSTOMER_VULNERABILITY),
arr AS (SELECT CUSTOMER_ID, MIN(OPENED_DATE) AS OPENED_DATE FROM NORTHBANK_AGENT_EVALS.DEMO.ARREARS_CASES GROUP BY 1),
src AS (
  -- A: vulnerability signal note for every vulnerable customer
  SELECT v.CUSTOMER_ID,
    COALESCE(DATEADD(day, -10, arr.OPENED_DATE), DATEADD(day, 4 + ABS(HASH(v.CUSTOMER_ID,'nd1')) % 536, '2025-01-01'::DATE)) AS NOTE_DATE,
    (CASE v.VULNERABILITY_TYPE WHEN 'BEREAVEMENT' THEN 1 WHEN 'JOB_LOSS' THEN 4 WHEN 'SERIOUS_ILLNESS' THEN 7 WHEN 'MENTAL_HEALTH' THEN 10 ELSE 13 END)
      + IFF(v.SIGNAL_STRENGTH = 'SUBTLE', 20, 0) + ABS(HASH(v.CUSTOMER_ID,'tpl')) % 3 AS TEMPLATE_ID
  FROM v LEFT JOIN arr USING (CUSTOMER_ID) WHERE v.IS_VULNERABLE
  UNION ALL
  -- B: extra service note for half of vulnerable customers
  SELECT CUSTOMER_ID, DATEADD(day, ABS(HASH(CUSTOMER_ID,'nd2')) % 545, '2025-01-01'::DATE), 51 + ABS(HASH(CUSTOMER_ID,'svc')) % 6
  FROM v WHERE IS_VULNERABLE AND ABS(HASH(CUSTOMER_ID,'b')) % 2 = 0
  UNION ALL
  -- C: neutral arrears note for every customer with an arrears case (vulnerable or not)
  SELECT CUSTOMER_ID, LEAST(DATEADD(day, 5, OPENED_DATE), '2026-06-30'::DATE), 41 + ABS(HASH(CUSTOMER_ID,'arr')) % 5 FROM arr
  UNION ALL
  SELECT CUSTOMER_ID, LEAST(DATEADD(day, 20, OPENED_DATE), '2026-06-30'::DATE), 41 + ABS(HASH(CUSTOMER_ID,'arr2')) % 5
  FROM arr WHERE ABS(HASH(CUSTOMER_ID,'c2')) % 2 = 0
  UNION ALL
  -- D: general service notes across the book
  SELECT 'C' || LPAD(1 + ABS(HASH(n,'svcust')) % 8000, 5, '0'), DATEADD(day, ABS(HASH(n,'svd')) % 545, '2025-01-01'::DATE), 51 + ABS(HASH(n,'svt')) % 6
  FROM (SELECT ROW_NUMBER() OVER (ORDER BY SEQ4()) n FROM TABLE(GENERATOR(ROWCOUNT => 1400)))
  UNION ALL
  -- E: distractor notes (keywords without vulnerability) for non-vulnerable customers
  SELECT CUSTOMER_ID, DATEADD(day, ABS(HASH(CUSTOMER_ID,'dd')) % 545, '2025-01-01'::DATE), 61 + ABS(HASH(CUSTOMER_ID,'dt')) % 3
  FROM v WHERE NOT IS_VULNERABLE AND ABS(HASH(CUSTOMER_ID,'dist')) % 160 = 0
)
SELECT
  'N' || LPAD(ROW_NUMBER() OVER (ORDER BY s.NOTE_DATE, s.CUSTOMER_ID, s.TEMPLATE_ID), 6, '0') AS NOTE_ID,
  s.CUSTOMER_ID, s.NOTE_DATE,
  ARRAY_CONSTRUCT('PHONE','PHONE','PHONE','CHAT','EMAIL','BRANCH')[ABS(HASH(s.CUSTOMER_ID, s.NOTE_DATE,'ch')) % 6]::VARCHAR AS CHANNEL,
  ARRAY_CONSTRUCT('J. Patel','S. Okafor','M. Evans','R. Campbell','A. Novak','L. Hughes','K. Ahmed','D. Murphy')[ABS(HASH(s.CUSTOMER_ID, s.NOTE_DATE,'ag')) % 8]::VARCHAR AS COLLEAGUE,
  t.TEXT AS NOTE_TEXT,
  t.KIND, t.VULNERABILITY_TYPE, t.SIGNAL_STRENGTH, s.TEMPLATE_ID
FROM src s JOIN NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTE_TEMPLATES t ON t.TEMPLATE_ID = s.TEMPLATE_ID;

-- Create agent-visible CUSTOMER_NOTES (no labels)
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.DEMO.CUSTOMER_NOTES AS
SELECT NOTE_ID, CUSTOMER_ID, NOTE_DATE, CHANNEL, COLLEAGUE, NOTE_TEXT
FROM NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTES_STAGING;

-- Create hidden NOTES_LABELS and drop staging
CREATE OR REPLACE TABLE NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTES_LABELS AS
SELECT NOTE_ID, CUSTOMER_ID, KIND, (KIND = 'VULN') AS IS_VULNERABILITY_SIGNAL, VULNERABILITY_TYPE, SIGNAL_STRENGTH, TEMPLATE_ID
FROM NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTES_STAGING;

-- Drop notes staging table
DROP TABLE NORTHBANK_AGENT_EVALS.GROUND_TRUTH.NOTES_STAGING;

-- ---- Views used by the semantic view -------------------------------------

-- Create APPLICATIONS_V flagging duplicate submissions
CREATE OR REPLACE VIEW NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS_V
  COMMENT = 'Applications with duplicate-submission flag (same customer, product, amount and day)'
AS
SELECT a.*,
  a.APPLICATION_TS::DATE AS APPLICATION_DATE,
  IFF(ROW_NUMBER() OVER (PARTITION BY a.CUSTOMER_ID, a.PRODUCT, a.REQUESTED_AMOUNT, a.APPLICATION_TS::DATE
                         ORDER BY a.APPLICATION_TS, a.APPLICATION_ID) > 1, TRUE, FALSE) AS IS_DUPLICATE_SUBMISSION
FROM NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS a;

-- Create LOANS_V with arrears status per loan
CREATE OR REPLACE VIEW NORTHBANK_AGENT_EVALS.DEMO.LOANS_V
  COMMENT = 'Booked loans and cards with arrears status as of 2026-06-30'
AS
SELECT l.*,
  (c.LOAN_ID IS NOT NULL) AS EVER_IN_ARREARS,
  COALESCE(c.CURRENT_DPD, 0) AS CURRENT_DPD,
  c.CASE_STATUS AS ARREARS_CASE_STATUS
FROM NORTHBANK_AGENT_EVALS.DEMO.LOANS l
LEFT JOIN NORTHBANK_AGENT_EVALS.DEMO.ARREARS_CASES c ON c.LOAN_ID = l.LOAN_ID;

-- Sanity check: these counts must match README "Expected row counts".
SELECT 'APPLICATIONS' t, COUNT(*) n FROM DEMO.APPLICATIONS UNION ALL
SELECT 'UNIQUE_APPLICATIONS', COUNT_IF(NOT IS_DUPLICATE_SUBMISSION) FROM DEMO.APPLICATIONS_V UNION ALL
SELECT 'LOANS', COUNT(*) FROM DEMO.LOANS UNION ALL
SELECT 'ARREARS_CASES', COUNT(*) FROM DEMO.ARREARS_CASES UNION ALL
SELECT 'FORBEARANCE', COUNT(*) FROM DEMO.FORBEARANCE UNION ALL
SELECT 'CUSTOMER_NOTES', COUNT(*) FROM DEMO.CUSTOMER_NOTES;
