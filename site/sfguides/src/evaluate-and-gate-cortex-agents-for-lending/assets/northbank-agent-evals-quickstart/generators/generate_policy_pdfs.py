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

"""Generate synthetic Northbank policy PDFs for the lending agent evals demo.

All content is fictional. Facts stated here (cut-offs, thresholds, timelines) are the
source of truth for the eval ground truth, so keep them in sync with the SQL data
generation in sql/01_synthetic_data.sql.
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent.parent / "data" / "policy_pdfs"
OUT.mkdir(exist_ok=True)

styles = getSampleStyleSheet()
H1 = styles["Heading1"]
H2 = styles["Heading2"]
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=6)
BANNER = ParagraphStyle("banner", parent=BODY, textColor=colors.white, backColor=colors.HexColor("#B00020"),
                        fontSize=11, leading=16, borderPadding=6, spaceAfter=12)
META = ParagraphStyle("meta", parent=BODY, textColor=colors.HexColor("#444444"), fontSize=9)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 1.2 * cm, f"Northbank plc - Internal - {doc.title} - Synthetic document for demonstration only")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def table(rows):
    t = Table(rows, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEEFF")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def build(filename, title, meta, sections, banner=None):
    doc = SimpleDocTemplate(str(OUT / filename), pagesize=A4, title=title,
                            leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm)
    flow = [Paragraph(title, H1), Paragraph(meta, META), Spacer(1, 6)]
    if banner:
        flow.append(Paragraph(banner, BANNER))
    for heading, items in sections:
        flow.append(Paragraph(heading, H2))
        for item in items:
            flow.append(item if not isinstance(item, str) else Paragraph(item, BODY))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)


P = lambda s: s  # readability alias

common_fairness = [
    P("Northbank does not use age, sex, gender reassignment, race, ethnicity, religion or belief, sexual "
      "orientation, disability, pregnancy or maternity, or marriage and civil partnership status as a factor "
      "in any credit decision. Date of birth is collected only to verify identity and to confirm the applicant "
      "is 18 or over."),
    P("Any request to introduce an age-based or other protected-characteristic rule must be declined and "
      "escalated to the Head of Credit Risk and the Compliance function."),
]


def credit_policy(version, effective, cutoff, superseded_note=None, rationale=None):
    sections = [
        ("1. Purpose and scope", [
            P("This policy sets the minimum lending criteria for Northbank unsecured personal loans and credit "
              "cards offered to UK consumers. It applies to all applications received through the App, Web and "
              "Broker channels."),
        ]),
        ("2. Products in scope", [
            table([["Product", "Amount / limit", "Term"],
                   ["Unsecured personal loan", "GBP 1,000 to GBP 25,000 (multiples of GBP 500)", "12, 24, 36, 48 or 60 months"],
                   ["Credit card", "GBP 500 to GBP 8,000 (multiples of GBP 250)", "Revolving"]]),
        ]),
        ("3. Minimum credit score", [
            P(f"The minimum NBUREAU credit score for approval is <b>{cutoff}</b> on the 0 to 999 scale. "
              f"Applications scoring below {cutoff} must be declined with reason code SCORE_BELOW_CUTOFF. "
              "There is no manual override of the minimum score."),
        ] + ([P(rationale)] if rationale else [])),
        ("4. Affordability", [
            P("Every application must pass the Northbank Affordability Standard. The maximum debt-to-income "
              "ratio is <b>50%</b> (0.50). Applications above 50% must be declined with reason code AFFORDABILITY. "
              "See the Affordability Standard for the calculation."),
        ]),
        ("5. Income verification", [
            P("Declared gross annual income is mandatory. Where declared income is missing or cannot be verified, "
              "the application must be referred (decision REFERRED, reason INCOME_NOT_VERIFIED) and must not be "
              "approved or declined automatically."),
        ]),
        ("6. Fair treatment and protected characteristics", common_fairness),
        ("7. Decision order", [
            P("Rules are applied in this order: (1) income verification, (2) minimum credit score, (3) affordability. "
              "The first failing rule determines the decision reason."),
        ]),
        ("8. Governance", [
            P("This policy is owned by the Head of Credit Risk and reviewed at least annually by the Credit Risk "
              "Committee. Changes take effect only from the effective date stated on the policy."),
        ]),
    ]
    build(f"credit_policy_{version.replace('.', '_')}.pdf", f"Northbank Credit Policy {version}",
          f"Document ID: CRP-001 | Version {version} | Effective {effective} | Owner: Head of Credit Risk",
          sections, banner=superseded_note)


credit_policy("v1.0", "1 July 2024", 620,
              superseded_note="SUPERSEDED: this version was replaced by Credit Policy v2.0 on 1 March 2026. "
                              "Do not use for applications received on or after 1 March 2026.")
credit_policy("v2.0", "1 March 2026", 640,
              rationale="Change from v1.0: the minimum score was raised from 620 to 640 following the review of the "
                        "2025-Q3 personal loan vintage, whose early arrears rate was roughly three times that of "
                        "neighbouring vintages. Applications received before 1 March 2026 remain governed by v1.0 "
                        "(minimum score 620).")

build("affordability_standard.pdf", "Northbank Affordability Standard",
      "Document ID: AFF-002 | Version 3.1 | Effective 1 July 2024 | Owner: Head of Credit Risk",
      [
          ("1. Purpose", [P("Defines how Northbank assesses whether new credit is affordable for the customer, in line "
                            "with FCA CONC 5.2A creditworthiness requirements.")]),
          ("2. Debt-to-income ratio (DTI)", [
              P("DTI = (existing monthly credit commitments + estimated new monthly payment) / (declared gross annual "
                "income / 12)."),
              table([["Product", "Estimated new monthly payment"],
                     ["Personal loan", "requested amount x 1.08 / term in months"],
                     ["Credit card", "3% of the requested credit limit"]]),
              P("The maximum permitted DTI is 50%. A DTI of exactly 50% passes."),
          ]),
          ("3. Worked example", [
              P("Declared income GBP 36,000 (GBP 3,000 per month), existing commitments GBP 600 per month, personal "
                "loan of GBP 12,000 over 36 months. New payment = 12,000 x 1.08 / 36 = GBP 360. DTI = (600 + 360) / "
                "3,000 = 32%. Pass."),
          ]),
          ("4. Tool use", [P("Colleagues must use the AFFORDABILITY_CHECK tool rather than manual calculation.")]),
          ("5. Income shocks", [P("Where a customer tells us their income has fallen (for example job loss or "
                                  "reduced hours), affordability must be reassessed using the new income before any "
                                  "further lending or limit increase.")]),
      ])

build("forbearance_and_arrears_procedure.pdf", "Northbank Forbearance and Arrears Procedure",
      "Document ID: COL-004 | Version 2.2 | Effective 1 January 2025 | Owner: Head of Collections",
      [
          ("1. Purpose", [P("Sets out how Northbank treats customers in arrears or financial difficulty, consistent with "
                            "FCA CONC 7 and the Consumer Duty.")]),
          ("2. Arrears stages", [
              table([["Stage", "Days past due", "Standard next action"],
                     ["Early", "1 to 59", "Send arrears notice and attempt contact"],
                     ["Late", "60 to 89", "Refer to Collections"],
                     ["Default", "90 or more", "Issue default notice"]]),
          ]),
          ("3. Mandatory vulnerability check", [
              P("<b>Before any referral to Collections or issue of a default notice, the colleague must review the "
                "customer's contact and hardship notes for vulnerability indicators.</b> If any indicator is present, "
                "the standard next action must not be taken. Instead: (a) pause collections activity for 30 days "
                "(breathing space), (b) refer the case to the Specialist Support Team, and (c) consider forbearance "
                "under section 4. See the Vulnerable Customer Procedure."),
          ]),
          ("4. Forbearance options", [
              table([["Option", "Limits"],
                     ["Reduced payment plan", "Up to 6 months, then review"],
                     ["Payment holiday", "Maximum 3 months"],
                     ["Interest and charges freeze", "Up to 6 months, then review"],
                     ["Term extension", "Personal loans only, maximum 24 additional months"]]),
              P("Every arrangement must be reviewed at least every 6 months. Arrangements must be affordable based on "
                "an up-to-date income and expenditure assessment."),
          ]),
          ("5. Prohibited actions", [P("Northbank does not sell debt of customers flagged as vulnerable to third parties, "
                                       "and does not add default charges during an active forbearance arrangement.")]),
      ])

build("vulnerable_customer_procedure.pdf", "Northbank Vulnerable Customer Procedure",
      "Document ID: VUL-005 | Version 1.4 | Effective 1 July 2024 | Owner: Chief Customer Officer",
      [
          ("1. Purpose", [P("Ensures customers in vulnerable circumstances receive outcomes as good as other customers, "
                            "reflecting FCA guidance FG21/1 on the fair treatment of vulnerable customers.")]),
          ("2. Drivers of vulnerability", [
              table([["Driver", "Examples of indicators in notes"],
                     ["Health", "serious or long-term illness, hospital stay, mental health condition, anxiety, depression"],
                     ["Life events", "bereavement, relationship breakdown, job loss or redundancy, becoming a carer"],
                     ["Resilience", "sudden income drop, no savings, relying on credit for essentials"],
                     ["Capability", "difficulty understanding letters, low digital or financial confidence"]]),
              P("Indicators can be stated directly or implied. For example, 'I've been off work since the operation' "
                "implies a health driver even if the word illness is not used."),
          ]),
          ("3. Required actions when an indicator is found", [
              P("1. Record the indicator and set the case flag VULNERABILITY_REVIEW."),
              P("2. Refer to the Specialist Support Team within 2 business days."),
              P("3. Pause collections activity for 30 days and apply section 3 of the Forbearance and Arrears Procedure."),
              P("4. Offer communication adjustments (preferred channel, a named contact, more time to respond)."),
          ]),
          ("4. What not to do", [P("Do not ask the customer for medical evidence as a condition of support. Do not issue "
                                   "a default notice or refer to Collections while a vulnerability review is open.")]),
      ])

build("consumer_duty_summary.pdf", "Northbank Consumer Duty Summary for Colleagues",
      "Document ID: CDY-006 | Version 1.2 | Effective 31 July 2023 | Owner: Chief Compliance Officer",
      [
          ("1. The four outcomes", [
              P("Under the FCA Consumer Duty (PRIN 2A) Northbank must deliver good outcomes in four areas: products and "
                "services, price and value, consumer understanding, and consumer support."),
          ]),
          ("2. Avoiding foreseeable harm", [
              P("Colleagues and tools must not encourage a customer to take credit that is unaffordable, and must flag "
                "cases where a customer appears to be in financial difficulty."),
          ]),
          ("3. Guidance, not advice", [
              P("Northbank provides information and guidance only. Colleagues and internal tools must not tell a customer "
                "whether they personally should take out a loan or card, or which product is best for their circumstances. "
                "Customers asking for a personal recommendation should be directed to free, impartial help such as "
                "MoneyHelper."),
          ]),
          ("4. Data and fairness", common_fairness),
      ])

build("complaints_handling.pdf", "Northbank Complaints Handling Procedure",
      "Document ID: CMP-007 | Version 2.0 | Effective 1 January 2025 | Owner: Head of Customer Relations",
      [
          ("1. Timelines", [
              table([["Step", "Deadline"],
                     ["Acknowledge complaint", "Within 5 business days"],
                     ["Final response (credit products)", "Within 8 weeks of receipt"],
                     ["Customer right to refer to the Financial Ombudsman Service", "Within 6 months of the final response"]]),
          ]),
          ("2. Vulnerable complainants", [P("Complaints from customers flagged for vulnerability review are allocated to a "
                                            "senior handler and the customer is offered a named contact.")]),
          ("3. Root cause analysis", [P("Complaint themes are reviewed monthly by the Customer Outcomes Committee.")]),
      ])

print("Wrote:", sorted(p.name for p in OUT.glob("*.pdf")))
