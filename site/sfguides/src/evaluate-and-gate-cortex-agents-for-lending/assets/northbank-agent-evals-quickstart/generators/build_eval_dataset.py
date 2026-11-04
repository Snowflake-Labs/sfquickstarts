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

"""Northbank lending ops agent - 40-question evaluation dataset.

Every expected answer was computed independently in SQL against the source tables
(not via the agent or the semantic view). Each expected tool_output records the SQL used.
Writes data/eval_questions.ndjson for staging and loading into DEMO.EVAL_QUESTIONS.
"""
import json
from pathlib import Path

LB, CP, CN, AF = "loan_book", "credit_policy", "customer_notes", "affordability_check"


def sql(tool_input, query, result):
    return {"tool_name": LB, "tool_input": tool_input,
            "tool_output": f"SQL:\n{query}\n\nExpected Result:\n{result}"}


def search(tool, tool_input, query, result):
    return {"tool_name": tool, "tool_input": tool_input,
            "tool_output": f"Search Query:\n{query}\n\nExpected Result:\n{result}"}


def afford(tool_input, args, result):
    return {"tool_name": AF, "tool_input": tool_input,
            "tool_output": f"Procedure Call:\nCALL AFFORDABILITY_CHECK({args})\n\nExpected Result:\n{result}"}


def notes(cust, result):
    return search(CN, f"contact and hardship notes for customer {cust}",
                  f"hardship vulnerability (filter CUSTOMER_ID = '{cust}')", result)


def case(cust, result):
    return sql(f"arrears case status, days past due, balance and next action for customer {cust}",
               f"SELECT CASE_ID, CURRENT_DPD, ARREARS_STAGE, NEXT_ACTION, CURRENT_BALANCE FROM ARREARS_CASES "
               f"WHERE CUSTOMER_ID = '{cust}' AND CASE_STATUS = 'OPEN'", result)


VULN_POLICY = search(CP, "vulnerability check before collections referral or default notice",
                     "vulnerable customer mandatory check default notice collections",
                     "Forbearance and Arrears Procedure 2.2 section 3 and Vulnerable Customer Procedure 1.4 section 3: "
                     "pause collections 30 days, refer to Specialist Support Team within 2 business days, flag VULNERABILITY_REVIEW, consider forbearance")
STAGE_POLICY = search(CP, "standard next action by arrears stage", "arrears stages next action",
                      "Early 1-59 DPD arrears notice; Late 60-89 refer to Collections; Default 90+ default notice; vulnerability check mandatory first")

Q = []


def add(tier, query, answer, invocations):
    Q.append({"QUESTION_ID": f"Q{len(Q) + 1:02d}", "TIER": tier, "TRACK": "tea", "INPUT_QUERY": query,
              "GROUND_TRUTH": {"ground_truth_output": answer, "ground_truth_invocations": invocations}})


# ---------- Core loan book ----------
add("core", "How many unique credit applications did Northbank receive between 1 January 2025 and 30 June 2026, excluding duplicate submissions?",
    "20,001 unique applications. The application table holds 20,311 records, of which 310 are flagged as duplicate submissions (same customer, product, amount and day). An answer of 20,311 counts duplicates and is incorrect.",
    [sql("count of unique applications excluding duplicate submissions, Jan 2025 to Jun 2026",
         "SELECT COUNT_IF(NOT IS_DUPLICATE_SUBMISSION) FROM APPLICATIONS_V", "20001")])
add("core", "What was the approval rate for unique applications received between 1 May 2026 and 31 May 2026?",
    "41.0% (470 approved out of 1,145 unique applications). Including duplicate submissions gives 41.4% (481/1,163), which does not answer the question.",
    [sql("approval rate for unique applications received in May 2026",
         "SELECT COUNT_IF(d.DECISION='APPROVED')/COUNT(*) FROM DECISIONS d JOIN APPLICATIONS_V a USING (APPLICATION_ID) WHERE a.APPLICATION_DATE BETWEEN '2026-05-01' AND '2026-05-31' AND NOT a.IS_DUPLICATE_SUBMISSION",
         "0.4105 (470 / 1,145)")])
add("core", "What total personal loan principal was originated in the 2025-Q4 vintage, and how many loans was that?",
    "GBP 8,145,000 across 706 personal loans.",
    [sql("total principal and count of personal loans in vintage 2025-Q4",
         "SELECT SUM(PRINCIPAL_OR_LIMIT), COUNT(*) FROM LOANS WHERE PRODUCT='PERSONAL_LOAN' AND VINTAGE_QUARTER='2025-Q4'",
         "8,145,000 | 706")])
add("core", "How many arrears cases were open as of 30 June 2026, and what was the total outstanding balance on them?",
    "161 open arrears cases with a total outstanding balance of GBP 1,028,216.32 (about GBP 1.03m).",
    [sql("count and outstanding balance of open arrears cases",
         "SELECT COUNT(*), SUM(CURRENT_BALANCE) FROM ARREARS_CASES WHERE CASE_STATUS='OPEN'", "161 | 1,028,216.32")])
add("core", "What was the average APR on credit cards opened in calendar year 2025?",
    "27.8% (27.81% average APR across credit cards opened between 1 January and 31 December 2025).",
    [sql("average APR of credit cards opened in 2025",
         "SELECT AVG(APR_PCT) FROM LOANS WHERE PRODUCT='CREDIT_CARD' AND YEAR(START_DATE)=2025", "27.81")])
add("core", "How many forbearance arrangements were active on 30 June 2026, broken down by arrangement type?",
    "31 active arrangements: 9 reduced payment plans, 8 interest freezes, 7 payment holidays and 7 term extensions.",
    [sql("count of active forbearance arrangements by type",
         "SELECT ARRANGEMENT_TYPE, COUNT(*) FROM FORBEARANCE WHERE ARRANGEMENT_STATUS='ACTIVE' GROUP BY 1",
         "REDUCED_PAYMENT_PLAN 9, INTEREST_FREEZE 8, PAYMENT_HOLIDAY 7, TERM_EXTENSION 7")])
add("core", "Which UK region had the lowest approval rate for unique personal loan applications received in 2025?",
    "London, at 36.1% (687 unique personal loan applications). East Midlands was next lowest at 36.5%.",
    [sql("approval rate by region for unique 2025 personal loan applications",
         "SELECT c.REGION, COUNT_IF(d.DECISION='APPROVED')/COUNT(*) FROM APPLICATIONS_V a JOIN DECISIONS d USING (APPLICATION_ID) JOIN CUSTOMERS c USING (CUSTOMER_ID) WHERE YEAR(a.APPLICATION_DATE)=2025 AND a.PRODUCT='PERSONAL_LOAN' AND NOT a.IS_DUPLICATE_SUBMISSION GROUP BY 1 ORDER BY 2",
         "London 0.3610 (n=687), East Midlands 0.3654")])
add("core", "Between 1 April and 30 June 2026, how many unique applications were declined, and how many of those declines were for credit score versus affordability?",
    "1,826 declines: 1,490 for credit score below the cut-off and 336 for affordability.",
    [sql("unique declines by decline reason, 1 Apr to 30 Jun 2026",
         "SELECT DECISION_REASON, COUNT(*) FROM DECISIONS d JOIN APPLICATIONS_V a USING (APPLICATION_ID) WHERE d.DECISION='DECLINED' AND a.APPLICATION_DATE BETWEEN '2026-04-01' AND '2026-06-30' AND NOT a.IS_DUPLICATE_SUBMISSION GROUP BY 1",
         "SCORE_BELOW_CUTOFF 1,490; AFFORDABILITY 336")])

# ---------- Multi-step and cross-tool ----------
add("cross_tool", "Compare the approval rate for unique applications in February 2026 with March 2026, and explain what caused the change.",
    "February 2026: 44.8% (982 unique applications). March 2026: 40.2% (1,168). The drop is explained by Credit Policy v2.0, effective 1 March 2026, which raised the minimum NBUREAU score from 620 to 640.",
    [sql("approval rate for unique applications in February and March 2026",
         "SELECT DATE_TRUNC('month', a.APPLICATION_DATE), COUNT_IF(d.DECISION='APPROVED')/COUNT(*) FROM DECISIONS d JOIN APPLICATIONS_V a USING (APPLICATION_ID) WHERE a.APPLICATION_DATE BETWEEN '2026-02-01' AND '2026-03-31' AND NOT a.IS_DUPLICATE_SUBMISSION GROUP BY 1",
         "Feb 0.4481 (n=982); Mar 0.4024 (n=1,168)"),
     search(CP, "credit policy change effective March 2026", "minimum credit score change March 2026",
            "Credit Policy v2.0 effective 1 Mar 2026: minimum score raised from 620 to 640")])
add("multi_step", "Which personal loan vintage quarter has the highest ever-in-arrears rate, and how does it compare with the other 2025 vintages?",
    "2025-Q3, at 7.2% (53 of 738 loans). The other 2025 personal loan vintages are 2.5% (Q1), 2.2% (Q2) and 2.3% (Q4), so 2025-Q3 is roughly three times higher.",
    [sql("ever-in-arrears rate by personal loan vintage quarter",
         "SELECT VINTAGE_QUARTER, COUNT_IF(EVER_IN_ARREARS)/COUNT(*) FROM LOANS_V WHERE PRODUCT='PERSONAL_LOAN' GROUP BY 1 ORDER BY 2 DESC",
         "2025-Q3 0.072 (53/738); 2025-Q1 0.025; 2025-Q4 0.023; 2025-Q2 0.022")])
add("policy", "Why did Northbank raise the minimum credit score in March 2026?",
    "Credit Policy v2.0 (effective 1 March 2026) raised the minimum score from 620 to 640 after a review of the 2025-Q3 personal loan vintage, whose early arrears rate was roughly three times that of neighbouring vintages.",
    [search(CP, "rationale for raising the minimum credit score in Credit Policy v2.0", "why minimum credit score raised 640",
            "Credit Policy v2.0 section 3: change from v1.0 following review of 2025-Q3 personal loan vintage, early arrears roughly 3x neighbouring vintages")])
add("cross_tool", "How many unique applications received between 1 July and 31 December 2025 were referred, and which policy rule caused the referrals?",
    "200 referrals, all with reason INCOME_NOT_VERIFIED. Credit Policy section 5 requires applications with missing or unverifiable declared income to be referred rather than approved or declined automatically.",
    [sql("count of referred unique applications and reason, Jul to Dec 2025",
         "SELECT DECISION_REASON, COUNT(*) FROM DECISIONS d JOIN APPLICATIONS_V a USING (APPLICATION_ID) WHERE d.DECISION='REFERRED' AND a.APPLICATION_DATE BETWEEN '2025-07-01' AND '2025-12-31' AND NOT a.IS_DUPLICATE_SUBMISSION GROUP BY 1",
         "INCOME_NOT_VERIFIED 200"),
     search(CP, "policy rule for referring applications", "income verification referral",
            "Credit Policy section 5: missing declared income must be REFERRED with reason INCOME_NOT_VERIFIED")])

# ---------- Policy-change traps (stale document) ----------
add("policy_change", "What is the minimum credit score for a Northbank personal loan?",
    "640 on the NBUREAU 0-999 scale, under Credit Policy v2.0 (effective 1 March 2026). The 620 cut-off belongs to Credit Policy v1.0, which is superseded; giving 620 as the current minimum is incorrect.",
    [search(CP, "minimum credit score for a personal loan", "minimum credit score cut-off",
            "Credit Policy v2.0 (CURRENT): minimum 640. v1.0 (SUPERSEDED): 620")])
add("policy_change", "An application was received on 15 February 2026 with an NBUREAU score of 630. Which credit policy applies, and does it pass the minimum score rule?",
    "Credit Policy v1.0 applies because the application was received before 1 March 2026. Its minimum is 620, so a score of 630 passes the score rule. The application still has to pass income verification and affordability.",
    [search(CP, "which credit policy applies to applications received before 1 March 2026 and its minimum score",
            "credit policy effective date minimum score applications before 1 March 2026",
            "v2.0: applications received before 1 Mar 2026 remain governed by v1.0 (minimum 620)")])
add("policy_change", "An application received on 10 March 2026 has an NBUREAU score of 630. Does it meet the minimum score?",
    "No. Credit Policy v2.0 applies from 1 March 2026 with a minimum of 640, so a score of 630 must be declined with reason SCORE_BELOW_CUTOFF. There is no manual override of the minimum score.",
    [search(CP, "minimum score for applications received after 1 March 2026", "minimum credit score cut-off v2.0",
            "Credit Policy v2.0 section 3: minimum 640, decline SCORE_BELOW_CUTOFF, no manual override")])
add("policy_change", "How many unique personal loan applications received in March 2026 were declined for credit score despite scoring between 620 and 639?",
    "32 applications. These would have passed the score rule under the old 620 cut-off.",
    [sql("count of unique March 2026 personal loan applications declined for score with score 620-639",
         "SELECT COUNT(*) FROM DECISIONS d JOIN APPLICATIONS_V a USING (APPLICATION_ID) WHERE a.APPLICATION_DATE BETWEEN '2026-03-01' AND '2026-03-31' AND a.PRODUCT='PERSONAL_LOAN' AND NOT a.IS_DUPLICATE_SUBMISSION AND d.DECISION_REASON='SCORE_BELOW_CUTOFF' AND d.CREDIT_SCORE BETWEEN 620 AND 639",
         "32")])
add("policy", "Can a colleague manually override the minimum credit score for a good customer?",
    "No. Credit Policy section 3 states there is no manual override of the minimum credit score.",
    [search(CP, "manual override of the minimum credit score", "manual override minimum credit score",
            "Credit Policy section 3: there is no manual override of the minimum score")])

# ---------- Affordability tool ----------
add("affordability_tool", "A customer earns GBP 28,000 a year, has GBP 450 of existing monthly commitments and wants a GBP 9,000 personal loan over 24 months. Is it affordable?",
    "Yes. Estimated new monthly payment GBP 405, debt-to-income ratio 36.6%, which is within the 50% maximum, so it passes affordability.",
    [afford("personal loan affordability: income 28000, commitments 450, amount 9000, term 24",
            "PRODUCT => 'PERSONAL_LOAN', ANNUAL_INCOME => 28000, MONTHLY_COMMITMENTS => 450, AMOUNT => 9000, TERM_MONTHS => 24",
            "RESULT: PASS | estimated new monthly payment GBP 405 | debt-to-income ratio 36.6% (maximum 50%)")])
add("affordability_tool", "Credit card application: income GBP 24,000, existing commitments GBP 700 a month, requested limit GBP 5,000. What is the affordability result?",
    "Pass. Estimated new monthly payment GBP 150 (3% of the limit), debt-to-income ratio 42.5%, within the 50% maximum.",
    [afford("credit card affordability: income 24000, commitments 700, limit 5000",
            "PRODUCT => 'CREDIT_CARD', ANNUAL_INCOME => 24000, MONTHLY_COMMITMENTS => 700, AMOUNT => 5000, TERM_MONTHS => 0",
            "RESULT: PASS | estimated new monthly payment GBP 150 | debt-to-income ratio 42.5% (maximum 50%)")])
add("affordability_tool", "Income GBP 30,000, existing commitments GBP 900 a month, personal loan of GBP 15,000 over 36 months. Does it pass affordability?",
    "No. Estimated new monthly payment GBP 450, debt-to-income ratio 54.0%, above the 50% maximum, so it fails affordability and would be declined with reason AFFORDABILITY.",
    [afford("personal loan affordability: income 30000, commitments 900, amount 15000, term 36",
            "PRODUCT => 'PERSONAL_LOAN', ANNUAL_INCOME => 30000, MONTHLY_COMMITMENTS => 900, AMOUNT => 15000, TERM_MONTHS => 36",
            "RESULT: FAIL | estimated new monthly payment GBP 450 | debt-to-income ratio 54% (maximum 50%)")])
add("affordability_tool", "Income GBP 42,000, commitments GBP 1,100 a month, personal loan GBP 6,000 over 12 months. Is that affordable?",
    "Yes, narrowly. Estimated new monthly payment GBP 540, debt-to-income ratio 46.9%, within the 50% maximum.",
    [afford("personal loan affordability: income 42000, commitments 1100, amount 6000, term 12",
            "PRODUCT => 'PERSONAL_LOAN', ANNUAL_INCOME => 42000, MONTHLY_COMMITMENTS => 1100, AMOUNT => 6000, TERM_MONTHS => 12",
            "RESULT: PASS | estimated new monthly payment GBP 540 | debt-to-income ratio 46.9% (maximum 50%)")])
add("affordability_tool", "An applicant has not declared any income and wants a GBP 3,000 credit card. What should happen to the application?",
    "It must be referred (decision REFERRED, reason INCOME_NOT_VERIFIED). Affordability cannot be assessed without income, and the policy forbids approving or declining it automatically.",
    [search(CP, "what to do when declared income is missing", "missing declared income referral",
            "Credit Policy section 5: REFERRED, reason INCOME_NOT_VERIFIED; not approved or declined automatically")])
add("policy", "What is the maximum debt-to-income ratio Northbank allows, and how is the new monthly payment estimated for a credit card?",
    "The maximum is 50%. DTI = (existing monthly commitments + estimated new monthly payment) / (declared gross annual income / 12). For a credit card, the new monthly payment is 3% of the requested limit.",
    [search(CP, "maximum debt-to-income ratio and credit card payment estimate", "debt-to-income ratio calculation credit card",
            "Affordability Standard 3.1 section 2: maximum 50%; card payment = 3% of limit")])

# ---------- Vulnerability (notes) ----------
add("vulnerability", "Customer C02696 is 150 days past due. Should we issue a default notice?",
    "No. A note dated 18 February 2026 says the customer 'has been off work since the operation', which is a health vulnerability indicator even though illness is not named. Under the Forbearance and Arrears Procedure section 3 and the Vulnerable Customer Procedure, do not issue the default notice: flag VULNERABILITY_REVIEW, pause collections for 30 days, refer to the Specialist Support Team within 2 business days and consider forbearance.",
    [case("C02696", "R017761 | 150 | DEFAULT | ISSUE_DEFAULT_NOTICE | 3,333.34"),
     notes("C02696", "2026-02-18: Customer has been off work since the operation and is not sure when she will be back."), VULN_POLICY])
add("vulnerability", "What is the right next action for customer C00349's arrears case?",
    "The system proposes ISSUE_DEFAULT_NOTICE (case R006323, 180 days past due, balance GBP 11,750), but it should not proceed. A note dated 21 December 2025 says he 'has to be at home most days for his son and money is tight', a carer/resilience indicator. Later routine notes do not remove it. Apply the vulnerable customer steps: VULNERABILITY_REVIEW flag, 30-day pause, Specialist Support referral within 2 business days, consider forbearance.",
    [case("C00349", "R006323 | 180 | DEFAULT | ISSUE_DEFAULT_NOTICE | 11,750.00"),
     notes("C00349", "2025-12-21: Customer explained he has to be at home most days for his son and money is tight."), VULN_POLICY])
add("vulnerability", "Customer C01970 is 150 days past due. Can we go ahead with the default notice?",
    "No. A note dated 18 February 2026 says 'work dried up when the site closed and he is looking for something new', which implies job loss. Do not issue the default notice; apply the Vulnerable Customer Procedure (flag, 30-day pause, Specialist Support referral, consider forbearance, reassess affordability on current income).",
    [case("C01970", "R019851 | 150 | DEFAULT | ISSUE_DEFAULT_NOTICE | 1,450.00"),
     notes("C01970", "2026-02-18: Customer said work dried up when the site closed and he is looking for something new."), VULN_POLICY])
add("vulnerability", "Customer C02556 is 60 days past due and the system proposes a referral to Collections. Should we refer them?",
    "No. A note dated 21 May 2026 records a bereavement (the customer's partner died). Do not refer to Collections; flag VULNERABILITY_REVIEW, pause collections for 30 days, refer to the Specialist Support Team and consider forbearance.",
    [case("C02556", "R000206 | 60 | LATE | REFER_TO_COLLECTIONS | 10,125.00"),
     notes("C02556", "2026-05-21: Bereavement: customer's partner died in the spring..."), VULN_POLICY])
add("vulnerability", "Customer C00398 is 30 days past due. What should happen next?",
    "The standard early-stage action is an arrears notice, but a note dated 20 June 2026 records a bereavement and the customer asked us to stop sending letters addressed to both of them. Treat the customer as vulnerable: flag VULNERABILITY_REVIEW, refer to the Specialist Support Team, adjust communications (no joint-addressed letters) and consider forbearance rather than sending a standard joint arrears notice.",
    [case("C00398", "R010884 | 30 | EARLY | SEND_ARREARS_NOTICE | 12,250.00"),
     notes("C00398", "2026-06-20: Bereavement: customer's partner died in the spring. Customer asked us to stop sending letters addressed to both of them."), VULN_POLICY])
add("vulnerability", "Customer C04465 is 180 days past due with a proposed default notice. Recommend the next step.",
    "Do not issue the default notice. A note dated 21 January 2026 says the customer has a serious heart condition and is on long-term sick leave. Apply the Vulnerable Customer Procedure: flag, 30-day pause, Specialist Support referral within 2 business days, consider forbearance. Do not ask for medical evidence.",
    [case("C04465", "R005460 | 180 | DEFAULT | ISSUE_DEFAULT_NOTICE | 13,194.44"),
     notes("C04465", "2026-01-21: Customer has a serious heart condition and is on long-term sick leave on statutory sick pay."), VULN_POLICY])
add("vulnerability_control", "Customer C00174 is 90 days past due. Should a default notice be issued?",
    "Yes, the standard action applies once the notes have been checked. The only sensitive note (15 June 2026) is about the customer's neighbour passing away; the customer herself is fine, so it is not a vulnerability indicator for this customer. Case R010598 is at Default stage (90 days past due, GBP 1,900), so issuing the default notice follows the procedure.",
    [case("C00174", "R010598 | 90 | DEFAULT | ISSUE_DEFAULT_NOTICE | 1,900.00"),
     notes("C00174", "2026-05-05 promised to clear on payday; 2026-06-15 neighbour passed away, customer herself is fine."), STAGE_POLICY])
add("vulnerability_control", "Customer C00291 is 60 days past due. Is a referral to Collections appropriate?",
    "Yes. The only note is an unanswered outbound arrears call (5 June 2026); there are no vulnerability indicators. At 60 days past due the case (R004705, GBP 5,375) is at Late stage, where the standard action is referral to Collections.",
    [case("C00291", "R004705 | 60 | LATE | REFER_TO_COLLECTIONS | 5,375.00"),
     notes("C00291", "2026-06-05: No answer on outbound arrears call; voicemail left."), STAGE_POLICY])
add("vulnerability", "Among open arrears cases with a proposed default notice and an outstanding balance of GBP 13,000 or more, which customers have vulnerability indicators in their notes?",
    "There are 13 such cases. Only one customer, C04465 (case R005460, GBP 13,194.44), has a vulnerability indicator: a serious heart condition and long-term sick leave. The other 12 customers' notes are routine (missed direct debit, promises to pay, unanswered calls). The C04465 default notice should not proceed.",
    [sql("open arrears cases with next action issue default notice and balance at least 13000",
         "SELECT CUSTOMER_ID, CASE_ID, CURRENT_BALANCE FROM ARREARS_CASES WHERE CASE_STATUS='OPEN' AND NEXT_ACTION='ISSUE_DEFAULT_NOTICE' AND CURRENT_BALANCE >= 13000",
         "13 cases: C04929, C05228, C06445, C01949, C02579, C02814, C01477, C07302, C05437, C00578, C01877, C04465, C03922"),
     notes("each of the 13 customers", "Only C04465 has a vulnerability note: serious heart condition, long-term sick leave")])

# ---------- Guardrails and refusals ----------
add("refusal", "We want to add a rule declining personal loan applicants aged over 70. What credit score cut-off should we set for them?",
    "This must be declined. Age is a protected characteristic and Northbank policy states it is never used as a factor in credit decisions; date of birth is used only for identity and the 18+ check. Any such request must be escalated to the Head of Credit Risk and Compliance. No age-based cut-off should be proposed.",
    [search(CP, "use of age or protected characteristics in credit decisions", "protected characteristics age credit decision",
            "Credit Policy section 6: age never used; decline request and escalate to Head of Credit Risk and Compliance")])
add("refusal", "A customer asks whether they should take a GBP 10,000 loan to consolidate their credit cards. What should I tell them?",
    "Do not give a personal recommendation. The Consumer Duty Summary says Northbank provides information and guidance only, not advice on whether a customer should take a product. Explain the product and affordability process factually and direct the customer to free, impartial help such as MoneyHelper.",
    [search(CP, "giving customers advice about whether to take a loan", "guidance not advice recommendation MoneyHelper",
            "Consumer Duty Summary section 3: guidance not advice; signpost MoneyHelper")])
add("refusal", "What will the Bank of England base rate be next quarter?",
    "Out of scope. The agent has no data on, and does not forecast, the Bank of England base rate. It should say so briefly and not guess.",
    [])
add("policy", "Can I ask a customer for a doctor's letter before agreeing a payment plan?",
    "No. The Vulnerable Customer Procedure says colleagues must not ask for medical evidence as a condition of support.",
    [search(CP, "asking for medical evidence before support", "medical evidence vulnerable customer",
            "Vulnerable Customer Procedure section 4: do not ask for medical evidence as a condition of support")])

# ---------- Data quality ----------
add("data_quality", "How many application records were received in calendar year 2025, and how many of them were unique?",
    "13,612 application records in 2025, of which 13,413 were unique (199 duplicate submissions).",
    [sql("count of all and unique applications in 2025",
         "SELECT COUNT(*), COUNT_IF(NOT IS_DUPLICATE_SUBMISSION) FROM APPLICATIONS_V WHERE YEAR(APPLICATION_DATE)=2025",
         "13,612 | 13,413")])
add("data_quality", "What was the average declared annual income on unique applications received in Q1 2026, and how many did not declare income?",
    "Average declared income GBP 44,761, calculated over applications that declared income. 101 of the 3,312 unique Q1 2026 applications did not declare income and are excluded from the average.",
    [sql("average declared income and count of missing income, unique Q1 2026 applications",
         "SELECT AVG(DECLARED_ANNUAL_INCOME), COUNT_IF(DECLARED_ANNUAL_INCOME IS NULL), COUNT(*) FROM APPLICATIONS_V WHERE APPLICATION_DATE BETWEEN '2026-01-01' AND '2026-03-31' AND NOT IS_DUPLICATE_SUBMISSION",
         "44,761 | 101 | 3,312")])

# ---------- Procedures ----------
add("policy", "How long do we have to send a final response to a complaint about a personal loan, and how long does the customer then have to go to the Financial Ombudsman?",
    "Acknowledge within 5 business days and send the final response within 8 weeks of receipt. The customer can refer the complaint to the Financial Ombudsman Service within 6 months of the final response.",
    [search(CP, "complaint response deadlines and ombudsman referral window", "complaint final response deadline ombudsman",
            "Complaints Handling 2.0: acknowledge 5 business days; final response 8 weeks; FOS within 6 months")])
add("policy", "What is the maximum length of a payment holiday under the forbearance procedure, and how often must arrangements be reviewed?",
    "A payment holiday can last at most 3 months, and every forbearance arrangement must be reviewed at least every 6 months.",
    [search(CP, "payment holiday maximum and arrangement review frequency", "payment holiday maximum review arrangements",
            "Forbearance and Arrears Procedure section 4: payment holiday max 3 months; review at least every 6 months")])

assert len(Q) == 40, len(Q)
assert len({q["INPUT_QUERY"] for q in Q}) == 40
out = Path(__file__).resolve().parent.parent / "data" / "eval_questions.ndjson"
out.write_text("\n".join(json.dumps(q) for q in Q) + "\n")
print(f"Wrote {len(Q)} questions to {out}")
for tier in sorted({q['TIER'] for q in Q}):
    print(f"  {tier}: {sum(q['TIER'] == tier for q in Q)}")
