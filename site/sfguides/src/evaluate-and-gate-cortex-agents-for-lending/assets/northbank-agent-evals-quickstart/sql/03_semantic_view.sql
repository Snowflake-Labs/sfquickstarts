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
-- Northbank agent evals quickstart | 03 Semantic view
-- The loan_book tool: Cortex Analyst over applications, decisions, loans, arrears
-- and forbearance. Note the modelling choices the evaluation depends on:
--   - UNIQUE_APPLICATIONS excludes duplicate submissions;
--   - DATE_OF_BIRTH is deliberately not exposed (protected characteristic);
--   - ARREARS_CASES.NEXT_ACTION is documented as ignoring vulnerability.
-- =============================================================================
USE DATABASE NORTHBANK_AGENT_EVALS;
USE WAREHOUSE NORTHBANK_EVAL_WH;

create or replace semantic view NORTHBANK_AGENT_EVALS.DEMO.SV_LOAN_BOOK
	tables (
		NORTHBANK_AGENT_EVALS.DEMO.CUSTOMERS primary key (CUSTOMER_ID) comment='One row per Northbank customer. Date of birth is deliberately not exposed (protected characteristic).',
		APPLICATIONS as NORTHBANK_AGENT_EVALS.DEMO.APPLICATIONS_V primary key (APPLICATION_ID) comment='Credit applications for unsecured personal loans and credit cards. Includes duplicate submissions (same customer, product, amount and day); use UNIQUE_APPLICATIONS to exclude them.',
		NORTHBANK_AGENT_EVALS.DEMO.DECISIONS primary key (DECISION_ID) comment='Credit decision for each application. POLICY_VERSION records which credit policy applied (CREDIT_POLICY_V1 before 1 Mar 2026, cut-off 620; CREDIT_POLICY_V2 from 1 Mar 2026, cut-off 640).',
		LOANS as NORTHBANK_AGENT_EVALS.DEMO.LOANS_V primary key (LOAN_ID) comment='Booked personal loans and credit cards, with arrears status as of 30 Jun 2026.',
		NORTHBANK_AGENT_EVALS.DEMO.ARREARS_CASES primary key (CASE_ID) comment='One arrears case per account that has ever been past due, with the status and next action as of 30 Jun 2026. NEXT_ACTION is the system-proposed standard action and does not account for vulnerability; colleagues must check customer notes before collections or default actions.',
		NORTHBANK_AGENT_EVALS.DEMO.FORBEARANCE primary key (ARRANGEMENT_ID) comment='Forbearance arrangements agreed on arrears cases.'
	)
	relationships (
		APPLICATIONS_TO_CUSTOMERS as APPLICATIONS(APP_CUSTOMER_ID) references CUSTOMERS(CUSTOMER_ID),
		DECISIONS_TO_APPLICATIONS as DECISIONS(DEC_APPLICATION_ID) references APPLICATIONS(APPLICATION_ID),
		LOANS_TO_APPLICATIONS as LOANS(LOAN_APPLICATION_ID) references APPLICATIONS(APPLICATION_ID),
		ARREARS_TO_LOANS as ARREARS_CASES(CASE_LOAN_ID) references LOANS(LOAN_ID),
		FORBEARANCE_TO_ARREARS as FORBEARANCE(FB_CASE_ID) references ARREARS_CASES(CASE_ID)
	)
	facts (
		CUSTOMERS.ANNUAL_INCOME as ANNUAL_INCOME comment='Customer gross annual income in GBP recorded at onboarding.',
		APPLICATIONS.REQUESTED_AMOUNT as REQUESTED_AMOUNT comment='Requested loan amount or credit limit in GBP.',
		APPLICATIONS.TERM_MONTHS as TERM_MONTHS comment='Loan term in months (NULL for credit cards).',
		APPLICATIONS.DECLARED_ANNUAL_INCOME as DECLARED_ANNUAL_INCOME comment='Gross annual income declared on the application in GBP (NULL if not declared).',
		APPLICATIONS.MONTHLY_COMMITMENTS as MONTHLY_COMMITMENTS comment='Existing monthly credit commitments in GBP.',
		DECISIONS.CREDIT_SCORE as CREDIT_SCORE comment='NBUREAU credit score (0-999) used in the decision.',
		DECISIONS.SCORE_CUTOFF as SCORE_CUTOFF comment='Minimum score applied under the policy version.',
		DECISIONS.DEBT_TO_INCOME_RATIO as DEBT_TO_INCOME_RATIO comment='Debt-to-income ratio as a decimal (0.32 = 32%); NULL when income was not declared.',
		LOANS.PRINCIPAL_OR_LIMIT as PRINCIPAL_OR_LIMIT comment='Loan principal or card credit limit in GBP.',
		LOANS.APR_PCT as APR_PCT comment='APR in percent.',
		LOANS.LOAN_CURRENT_DPD as CURRENT_DPD comment='Days past due as of 30 Jun 2026 (0 if up to date).',
		ARREARS_CASES.CASE_CURRENT_DPD as CURRENT_DPD comment='Days past due as of 30 Jun 2026.',
		ARREARS_CASES.CASE_BALANCE as CURRENT_BALANCE comment='Outstanding balance in GBP as of 30 Jun 2026.'
	)
	dimensions (
		CUSTOMERS.CUSTOMER_ID as CUSTOMER_ID comment='Customer identifier, format C00001.',
		CUSTOMERS.REGION as REGION comment='UK region of residence.' sample_values ('London', 'Scotland', 'North West', 'Wales'),
		CUSTOMERS.EMPLOYMENT_STATUS as EMPLOYMENT_STATUS comment='Employment status at onboarding.' sample_values ('FULL_TIME', 'PART_TIME', 'SELF_EMPLOYED', 'RETIRED', 'UNEMPLOYED'),
		CUSTOMERS.CUSTOMER_SINCE as CUSTOMER_SINCE comment='Date the customer relationship started.',
		APPLICATIONS.APPLICATION_ID as APPLICATION_ID comment='Application identifier.',
		APPLICATIONS.APP_CUSTOMER_ID as CUSTOMER_ID comment='Customer who applied.',
		APPLICATIONS.PRODUCT as PRODUCT comment='Product applied for.' sample_values ('PERSONAL_LOAN', 'CREDIT_CARD'),
		APPLICATIONS.CHANNEL as CHANNEL comment='Application channel.' sample_values ('APP', 'WEB', 'BROKER'),
		APPLICATIONS.IS_DUPLICATE_SUBMISSION as IS_DUPLICATE_SUBMISSION comment='TRUE when this is a repeat submission of an application already made the same day.',
		APPLICATIONS.INCOME_DECLARED as DECLARED_ANNUAL_INCOME IS NOT NULL comment='FALSE when the applicant did not declare income.',
		APPLICATIONS.APPLICATION_DATE as APPLICATION_DATE comment='Date the application was received.',
		DECISIONS.DECISION_ID as DECISION_ID comment='Decision identifier.',
		DECISIONS.DEC_APPLICATION_ID as APPLICATION_ID comment='Application the decision relates to.',
		DECISIONS.DECISION as DECISION comment='Decision outcome.' sample_values ('APPROVED', 'DECLINED', 'REFERRED'),
		DECISIONS.DECISION_REASON as DECISION_REASON comment='Reason code for declines and referrals (NULL for approvals).' sample_values ('SCORE_BELOW_CUTOFF', 'AFFORDABILITY', 'INCOME_NOT_VERIFIED'),
		DECISIONS.POLICY_VERSION as POLICY_VERSION comment='Credit policy version applied.' sample_values ('CREDIT_POLICY_V1', 'CREDIT_POLICY_V2'),
		DECISIONS.DECISION_DATE as DECISION_DATE comment='Date the decision was made.',
		LOANS.LOAN_ID as LOAN_ID comment='Loan or card account identifier.',
		LOANS.LOAN_APPLICATION_ID as APPLICATION_ID comment='Originating application.',
		LOANS.LOAN_CUSTOMER_ID as CUSTOMER_ID comment='Borrower.',
		LOANS.LOAN_PRODUCT as PRODUCT comment='Product type.' sample_values ('PERSONAL_LOAN', 'CREDIT_CARD'),
		LOANS.VINTAGE_QUARTER as VINTAGE_QUARTER comment='Origination quarter, format YYYY-QN.' sample_values ('2025-Q1', '2025-Q3', '2026-Q1'),
		LOANS.EVER_IN_ARREARS as EVER_IN_ARREARS comment='TRUE if the account has ever been 1+ days past due.',
		LOANS.LOAN_START_DATE as START_DATE comment='Date the loan was drawn or the card opened.',
		ARREARS_CASES.CASE_ID as CASE_ID comment='Arrears case identifier.',
		ARREARS_CASES.CASE_LOAN_ID as LOAN_ID comment='Account in arrears.',
		ARREARS_CASES.CASE_CUSTOMER_ID as CUSTOMER_ID comment='Customer in arrears.',
		ARREARS_CASES.CASE_STATUS as CASE_STATUS comment='OPEN if currently past due, otherwise CURED.' sample_values ('OPEN', 'CURED'),
		ARREARS_CASES.ARREARS_STAGE as ARREARS_STAGE comment='EARLY (1-59 DPD), LATE (60-89), DEFAULT (90+).' sample_values ('EARLY', 'LATE', 'DEFAULT'),
		ARREARS_CASES.NEXT_ACTION as NEXT_ACTION comment='System-proposed next action.' sample_values ('SEND_ARREARS_NOTICE', 'REFER_TO_COLLECTIONS', 'ISSUE_DEFAULT_NOTICE', 'MONITOR_ARRANGEMENT', 'CLOSE_CASE'),
		ARREARS_CASES.CASE_OPENED_DATE as OPENED_DATE comment='Month-end when the account first went past due.',
		FORBEARANCE.ARRANGEMENT_ID as ARRANGEMENT_ID comment='Arrangement identifier.',
		FORBEARANCE.FB_CASE_ID as CASE_ID comment='Arrears case the arrangement belongs to.',
		FORBEARANCE.ARRANGEMENT_TYPE as ARRANGEMENT_TYPE comment='Type of forbearance.' sample_values ('REDUCED_PAYMENT_PLAN', 'PAYMENT_HOLIDAY', 'INTEREST_FREEZE', 'TERM_EXTENSION'),
		FORBEARANCE.ARRANGEMENT_STATUS as ARRANGEMENT_STATUS comment='ACTIVE or COMPLETED as of 30 Jun 2026.' sample_values ('ACTIVE', 'COMPLETED'),
		FORBEARANCE.ARRANGEMENT_START_DATE as START_DATE comment='Arrangement start date.'
	)
	metrics (
		APPLICATIONS.TOTAL_APPLICATIONS as COUNT(APPLICATIONS.APPLICATION_ID) comment='All application records including duplicate submissions.',
		APPLICATIONS.UNIQUE_APPLICATIONS as COUNT_IF(NOT APPLICATIONS.IS_DUPLICATE_SUBMISSION) comment='Applications excluding duplicate submissions.',
		APPLICATIONS.DUPLICATE_SUBMISSIONS as COUNT_IF(APPLICATIONS.IS_DUPLICATE_SUBMISSION) comment='Number of duplicate submissions.',
		APPLICATIONS.AVG_REQUESTED_AMOUNT as AVG(APPLICATIONS.REQUESTED_AMOUNT) comment='Average requested amount in GBP.',
		DECISIONS.DECISION_COUNT as COUNT(DECISIONS.DECISION_ID) comment='Number of decisions.',
		DECISIONS.APPROVED_COUNT as COUNT_IF(DECISIONS.DECISION = 'APPROVED') comment='Number of approvals.',
		DECISIONS.APPROVAL_RATE as COUNT_IF(DECISIONS.DECISION = 'APPROVED') / NULLIF(COUNT(DECISIONS.DECISION_ID), 0) comment='Approvals divided by all decisions, as a decimal.',
		DECISIONS.AVG_CREDIT_SCORE as AVG(DECISIONS.CREDIT_SCORE) comment='Average credit score.',
		LOANS.LOAN_COUNT as COUNT(LOANS.LOAN_ID) comment='Number of booked accounts.',
		LOANS.TOTAL_ORIGINATED as SUM(LOANS.PRINCIPAL_OR_LIMIT) comment='Total principal or limit originated in GBP.',
		LOANS.EVER_ARREARS_RATE as COUNT_IF(LOANS.EVER_IN_ARREARS) / NULLIF(COUNT(LOANS.LOAN_ID), 0) comment='Share of accounts that have ever been in arrears, as a decimal.',
		LOANS.AVG_APR as AVG(LOANS.APR_PCT) comment='Average APR in percent.',
		ARREARS_CASES.CASE_COUNT as COUNT(ARREARS_CASES.CASE_ID) comment='Number of arrears cases.',
		ARREARS_CASES.OPEN_CASE_COUNT as COUNT_IF(ARREARS_CASES.CASE_STATUS = 'OPEN') comment='Number of open arrears cases.',
		ARREARS_CASES.ARREARS_BALANCE as SUM(IFF(ARREARS_CASES.CASE_STATUS = 'OPEN', ARREARS_CASES.CURRENT_BALANCE, 0)) comment='Outstanding balance on open arrears cases in GBP.',
		FORBEARANCE.ARRANGEMENT_COUNT as COUNT(FORBEARANCE.ARRANGEMENT_ID) comment='Number of forbearance arrangements.'
	)
	comment='Northbank UK consumer lending loan book (synthetic): applications, credit decisions, booked personal loans and credit cards, arrears cases and forbearance arrangements. Data covers applications from 1 Jan 2025 to 30 Jun 2026; loan performance and arrears status are as of 30 Jun 2026.'
	with extension (CA='{"tables":[{"name":"CUSTOMERS","dimensions":[{"name":"CUSTOMER_ID"},{"name":"REGION"},{"name":"EMPLOYMENT_STATUS"}],"facts":[{"name":"ANNUAL_INCOME"}],"time_dimensions":[{"name":"CUSTOMER_SINCE"}]},{"name":"APPLICATIONS","dimensions":[{"name":"APPLICATION_ID"},{"name":"APP_CUSTOMER_ID"},{"name":"PRODUCT"},{"name":"CHANNEL"},{"name":"IS_DUPLICATE_SUBMISSION"},{"name":"INCOME_DECLARED"}],"facts":[{"name":"REQUESTED_AMOUNT"},{"name":"TERM_MONTHS"},{"name":"DECLARED_ANNUAL_INCOME"},{"name":"MONTHLY_COMMITMENTS"}],"metrics":[{"name":"TOTAL_APPLICATIONS"},{"name":"UNIQUE_APPLICATIONS"},{"name":"DUPLICATE_SUBMISSIONS"},{"name":"AVG_REQUESTED_AMOUNT"}],"time_dimensions":[{"name":"APPLICATION_DATE"}]},{"name":"DECISIONS","dimensions":[{"name":"DECISION_ID"},{"name":"DEC_APPLICATION_ID"},{"name":"DECISION"},{"name":"DECISION_REASON"},{"name":"POLICY_VERSION"}],"facts":[{"name":"CREDIT_SCORE"},{"name":"SCORE_CUTOFF"},{"name":"DEBT_TO_INCOME_RATIO"}],"metrics":[{"name":"DECISION_COUNT"},{"name":"APPROVED_COUNT"},{"name":"APPROVAL_RATE"},{"name":"AVG_CREDIT_SCORE"}],"time_dimensions":[{"name":"DECISION_DATE"}]},{"name":"LOANS","dimensions":[{"name":"LOAN_ID"},{"name":"LOAN_APPLICATION_ID"},{"name":"LOAN_CUSTOMER_ID"},{"name":"LOAN_PRODUCT"},{"name":"VINTAGE_QUARTER"},{"name":"EVER_IN_ARREARS"}],"facts":[{"name":"PRINCIPAL_OR_LIMIT"},{"name":"APR_PCT"},{"name":"LOAN_CURRENT_DPD"}],"metrics":[{"name":"LOAN_COUNT"},{"name":"TOTAL_ORIGINATED"},{"name":"EVER_ARREARS_RATE"},{"name":"AVG_APR"}],"time_dimensions":[{"name":"LOAN_START_DATE"}]},{"name":"ARREARS_CASES","dimensions":[{"name":"CASE_ID"},{"name":"CASE_LOAN_ID"},{"name":"CASE_CUSTOMER_ID"},{"name":"CASE_STATUS"},{"name":"ARREARS_STAGE"},{"name":"NEXT_ACTION"}],"facts":[{"name":"CASE_CURRENT_DPD"},{"name":"CASE_BALANCE"}],"metrics":[{"name":"CASE_COUNT"},{"name":"OPEN_CASE_COUNT"},{"name":"ARREARS_BALANCE"}],"time_dimensions":[{"name":"CASE_OPENED_DATE"}]},{"name":"FORBEARANCE","dimensions":[{"name":"ARRANGEMENT_ID"},{"name":"FB_CASE_ID"},{"name":"ARRANGEMENT_TYPE"},{"name":"ARRANGEMENT_STATUS"}],"metrics":[{"name":"ARRANGEMENT_COUNT"}],"time_dimensions":[{"name":"ARRANGEMENT_START_DATE"}]}],"relationships":[{"name":"APPLICATIONS_TO_CUSTOMERS"},{"name":"DECISIONS_TO_APPLICATIONS"},{"name":"LOANS_TO_APPLICATIONS"},{"name":"ARREARS_TO_LOANS"},{"name":"FORBEARANCE_TO_ARREARS"}]}');

SHOW SEMANTIC VIEWS IN SCHEMA NORTHBANK_AGENT_EVALS.DEMO;
