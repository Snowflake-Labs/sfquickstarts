/*
=============================================================================
  setup.sql
  Complete setup for MCP Connectors guide.
  Architecture: SI -> Cortex Agents -> MCP Servers -> Tools
  Database: ACME_CORP
  Schemas: HR, FINANCE, IT (domain-specific)
  Frontend: Snowflake Intelligence (SI)

  Run order:
    1. Database & Schemas
    2. Tables (16 tables across HR, Finance, IT domains)
    3. Cortex Search Services (4)
    4. Semantic Views (8)
    5. MCP Servers (10 specialized)
    6. Cortex Agents (3 specialized: HR, Finance, IT)
    7. RBAC Roles & Grants
=============================================================================
*/

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE COMPUTE;

-- ============================================================
-- STEP 0: DATABASE & SCHEMAS
-- ============================================================

CREATE DATABASE IF NOT EXISTS ACME_CORP;
CREATE SCHEMA IF NOT EXISTS ACME_CORP.HR;
CREATE SCHEMA IF NOT EXISTS ACME_CORP.FINANCE;
CREATE SCHEMA IF NOT EXISTS ACME_CORP.IT;

-- ============================================================
-- STEP 1: TABLES
-- ============================================================

-- HR tables
CREATE OR REPLACE TABLE ACME_CORP.HR.employees (
    employee_id   INT,
    name          VARCHAR,
    email         VARCHAR,
    department    VARCHAR,
    title         VARCHAR,
    level         VARCHAR,
    salary        NUMBER(10,2),
    ssn           VARCHAR,
    hire_date     DATE,
    manager_id    INT
);

INSERT INTO ACME_CORP.HR.employees VALUES
(1,  'Sarah Chen',        'schen@acme.com',      'Engineering', 'VP of Engineering',     'L8', 285000, '412-55-1234', '2018-03-15', NULL),
(2,  'Marcus Johnson',    'mjohnson@acme.com',    'Engineering', 'Senior Engineer',       'L6', 195000, '523-66-2345', '2019-07-22', 1),
(3,  'Priya Patel',       'ppatel@acme.com',      'Engineering', 'Staff Engineer',        'L7', 235000, '634-77-3456', '2019-01-10', 1),
(4,  'James Wilson',      'jwilson@acme.com',     'Engineering', 'Engineer',              'L5', 155000, '745-88-4567', '2021-06-01', 2),
(5,  'Lisa Zhang',        'lzhang@acme.com',      'Engineering', 'Engineer',              'L5', 150000, '856-99-5678', '2022-01-15', 2),
(6,  'David Kim',         'dkim@acme.com',        'Sales',       'VP of Sales',           'L8', 275000, '967-11-6789', '2017-11-01', NULL),
(7,  'Rachel Green',      'rgreen@acme.com',      'Sales',       'Account Executive',     'L5', 135000, '178-22-7890', '2020-09-10', 6),
(8,  'Tom Martinez',      'tmartinez@acme.com',   'Sales',       'Account Executive',     'L5', 140000, '289-33-8901', '2020-04-20', 6),
(9,  'Nina Gupta',        'ngupta@acme.com',      'HR',          'HR Director',           'L7', 210000, '390-44-9012', '2018-08-05', NULL),
(10, 'Carlos Rivera',     'crivera@acme.com',     'HR',          'HR Business Partner',   'L5', 125000, '401-55-0123', '2021-02-14', 9),
(11, 'Amy Thompson',      'athompson@acme.com',   'Finance',     'CFO',                   'L9', 320000, '512-66-1230', '2016-05-01', NULL),
(12, 'Brian Lee',         'blee@acme.com',        'Finance',     'Financial Analyst',     'L5', 130000, '623-77-2341', '2022-03-15', 11),
(13, 'Diana Ross',        'dross@acme.com',       'Marketing',   'VP of Marketing',       'L8', 260000, '734-88-3452', '2019-04-01', NULL),
(14, 'Eric Huang',        'ehuang@acme.com',      'Marketing',   'Marketing Manager',     'L6', 165000, '845-99-4563', '2021-08-20', 13),
(15, 'Fatima Ali',        'fali@acme.com',        'IT',          'IT Director',           'L7', 220000, '956-11-5674', '2018-10-15', NULL),
(16, 'George Park',       'gpark@acme.com',       'IT',          'Systems Engineer',      'L5', 145000, '167-22-6785', '2020-12-01', 15),
(17, 'Hannah Brown',      'hbrown@acme.com',      'IT',          'DevOps Engineer',       'L6', 175000, '278-33-7896', '2019-06-15', 15),
(18, 'Ian Stewart',       'istewart@acme.com',    'Engineering', 'Senior Engineer',       'L6', 190000, '389-44-8907', '2020-03-01', 1),
(19, 'Julia Nguyen',      'jnguyen@acme.com',     'Sales',       'Sales Director',        'L7', 225000, '490-55-9018', '2018-01-20', 6),
(20, 'Kevin O''Brien',    'kobrien@acme.com',     'Engineering', 'Engineer',              'L4', 125000, '501-66-0129', '2023-09-01', 3);

CREATE OR REPLACE TABLE ACME_CORP.HR.compensation_bands (
    band_id     INT,
    level       VARCHAR,
    title       VARCHAR,
    min_salary  NUMBER(10,2),
    max_salary  NUMBER(10,2),
    department  VARCHAR
);

INSERT INTO ACME_CORP.HR.compensation_bands VALUES
(1,  'L4', 'Junior Engineer',         100000, 140000, 'Engineering'),
(2,  'L5', 'Engineer',                130000, 175000, 'Engineering'),
(3,  'L6', 'Senior Engineer',         170000, 220000, 'Engineering'),
(4,  'L7', 'Staff Engineer',          210000, 270000, 'Engineering'),
(5,  'L8', 'VP',                      250000, 330000, 'Engineering'),
(6,  'L5', 'Account Executive',       110000, 160000, 'Sales'),
(7,  'L7', 'Sales Director',          190000, 260000, 'Sales'),
(8,  'L8', 'VP',                      240000, 320000, 'Sales'),
(9,  'L5', 'HR Business Partner',     105000, 145000, 'HR'),
(10, 'L7', 'HR Director',             180000, 240000, 'HR'),
(11, 'L5', 'Financial Analyst',       110000, 155000, 'Finance'),
(12, 'L9', 'CFO',                     280000, 380000, 'Finance'),
(13, 'L5', 'IT Engineer',             120000, 165000, 'IT'),
(14, 'L6', 'Senior IT Engineer',      155000, 200000, 'IT'),
(15, 'L7', 'IT Director',             190000, 250000, 'IT'),
(16, 'L6', 'Marketing Manager',       140000, 190000, 'Marketing'),
(17, 'L8', 'VP',                      230000, 300000, 'Marketing');

CREATE OR REPLACE TABLE ACME_CORP.HR.handbook_docs (
    doc_id       INT,
    title        VARCHAR,
    section      VARCHAR,
    content      VARCHAR,
    last_updated DATE
);

INSERT INTO ACME_CORP.HR.handbook_docs VALUES
(1, 'PTO Policy', 'Time Off', 'Employees receive 20 days of paid time off per year, accruing at 1.67 days per month. Unused PTO carries over up to a maximum of 10 days. PTO requests must be submitted at least 2 weeks in advance for periods longer than 3 days. Manager approval is required for all PTO requests.', '2025-01-15'),
(2, 'Remote Work Policy', 'Work Arrangements', 'Acme supports a hybrid work model. Employees are expected in-office Tuesday through Thursday. Monday and Friday are optional remote days. Fully remote arrangements require VP-level approval and an updated remote work agreement. Equipment stipends of $1,500 are provided for home office setup.', '2025-03-01'),
(3, 'Health Insurance', 'Benefits', 'Acme offers three health insurance tiers: Bronze ($150/mo employee cost, $2,000 deductible), Silver ($300/mo, $1,000 deductible), and Gold ($500/mo, $250 deductible). Dental and vision are included in Silver and Gold tiers. Coverage begins on the first day of employment. Open enrollment occurs in November each year.', '2025-02-10'),
(4, 'Parental Leave', 'Time Off', 'Primary caregivers receive 16 weeks of fully paid parental leave. Secondary caregivers receive 8 weeks of fully paid leave. Leave must begin within 12 months of the birth or adoption. Employees may extend leave with accrued PTO or unpaid leave up to 6 additional months.', '2025-01-20'),
(5, '401(k) Retirement Plan', 'Benefits', 'Acme matches 401(k) contributions dollar-for-dollar up to 6% of base salary. Vesting is immediate for the first 3% and follows a 3-year graded schedule for the remaining match. Employees can contribute up to the IRS annual limit. Financial planning consultations are available quarterly at no cost.', '2025-02-01'),
(6, 'Performance Review Process', 'Career Development', 'Performance reviews occur twice annually in March and September. Reviews include self-assessment, manager evaluation, and peer feedback from at least 2 colleagues. Ratings use a 5-point scale: Exceeds, Strong, Meets, Developing, Below. Compensation adjustments are tied to the March review cycle.', '2025-03-15'),
(7, 'Expense Reimbursement', 'Finance', 'Business expenses must be submitted within 30 days via the expense portal. Receipts are required for expenses over $25. Manager approval is required for individual expenses over $500. Travel expenses follow the GSA per diem rates. Corporate cards are available for employees at L6 and above.', '2025-01-10'),
(8, 'Code of Conduct', 'Compliance', 'All employees must adhere to Acme''s code of conduct covering ethical business practices, conflicts of interest, confidentiality, and anti-harassment policies. Annual compliance training is mandatory. Violations should be reported to HR or the anonymous ethics hotline. Retaliation against reporters is strictly prohibited.', '2025-02-20'),
(9, 'IT Security Policy', 'IT & Security', 'All company devices must use full-disk encryption and require biometric or PIN authentication. Password requirements: minimum 12 characters, changed every 90 days. VPN is required when accessing company resources from non-office networks. Phishing simulation tests are conducted monthly. Report suspicious emails to security@acme.com.', '2025-03-10'),
(10, 'Promotion Guidelines', 'Career Development', 'Promotions are considered during the March review cycle. Candidates must have been in their current level for at least 12 months. Promotion packets require a self-nomination document, manager sponsorship, and supporting evidence of impact at the next level. A calibration committee reviews all nominations to ensure consistency across departments.', '2025-01-25'),
(11, 'Onboarding Guide', 'Getting Started', 'New hires complete a 2-week onboarding program covering company culture, tools setup, security training, and team introductions. Day 1 includes laptop provisioning, badge access, and benefits enrollment. A dedicated onboarding buddy is assigned for the first 90 days. All onboarding tasks are tracked in the HR portal.', '2025-02-15'),
(12, 'Stock Options', 'Compensation', 'Eligible employees at L5 and above receive stock option grants as part of their compensation package. Initial grants vest over 4 years with a 1-year cliff. Annual refresh grants are awarded based on performance and level. Employees can exercise vested options up to 90 days after departure.', '2025-03-01');

CREATE OR REPLACE TABLE ACME_CORP.HR.org_chart (
    employee_id      INT,
    name             VARCHAR,
    department       VARCHAR,
    title            VARCHAR,
    manager_name     VARCHAR,
    span_of_control  INT,
    org_level        INT
);

INSERT INTO ACME_CORP.HR.org_chart VALUES
(1,  'Sarah Chen',        'Engineering', 'VP of Engineering',     NULL,              4, 1),
(2,  'Marcus Johnson',    'Engineering', 'Senior Engineer',       'Sarah Chen',      1, 2),
(3,  'Priya Patel',       'Engineering', 'Staff Engineer',        'Sarah Chen',      1, 2),
(4,  'James Wilson',      'Engineering', 'Engineer',              'Marcus Johnson',  0, 3),
(5,  'Lisa Zhang',        'Engineering', 'Engineer',              'Marcus Johnson',  0, 3),
(6,  'David Kim',         'Sales',       'VP of Sales',           NULL,              3, 1),
(7,  'Rachel Green',      'Sales',       'Account Executive',     'Julia Nguyen',    0, 3),
(8,  'Tom Martinez',      'Sales',       'Account Executive',     'Julia Nguyen',    0, 3),
(9,  'Nina Gupta',        'HR',          'HR Director',           NULL,              1, 1),
(10, 'Carlos Rivera',     'HR',          'HR Business Partner',   'Nina Gupta',      0, 2),
(11, 'Amy Thompson',      'Finance',     'CFO',                   NULL,              1, 1),
(12, 'Brian Lee',         'Finance',     'Financial Analyst',     'Amy Thompson',    0, 2),
(13, 'Diana Ross',        'Marketing',   'VP of Marketing',       NULL,              1, 1),
(14, 'Eric Huang',        'Marketing',   'Marketing Manager',     'Diana Ross',      0, 2),
(15, 'Fatima Ali',        'IT',          'IT Director',           NULL,              2, 1),
(16, 'George Park',       'IT',          'Systems Engineer',      'Fatima Ali',      0, 2),
(17, 'Hannah Brown',      'IT',          'DevOps Engineer',       'Fatima Ali',      0, 2),
(18, 'Ian Stewart',       'Engineering', 'Senior Engineer',       'Sarah Chen',      0, 2),
(19, 'Julia Nguyen',      'Sales',       'Sales Director',        'David Kim',       2, 2),
(20, 'Kevin O''Brien',    'Engineering', 'Engineer',              'Priya Patel',     0, 3);

CREATE OR REPLACE TABLE ACME_CORP.HR.benefits_plans (
    plan_id                  INT,
    plan_name                VARCHAR,
    plan_type                VARCHAR,
    provider                 VARCHAR,
    monthly_cost_employee    NUMBER(8,2),
    monthly_cost_employer    NUMBER(8,2),
    coverage_details         VARCHAR,
    eligibility              VARCHAR,
    enrollment_deadline      DATE
);

INSERT INTO ACME_CORP.HR.benefits_plans VALUES
(1, 'Bronze Health', 'Medical', 'Aetna', 150.00, 450.00, 'Basic medical coverage with $2,000 individual deductible and $4,000 family deductible. Covers preventive care at 100%, specialist visits at 80% after deductible.', 'All full-time employees', '2025-11-30'),
(2, 'Silver Health', 'Medical', 'Aetna', 300.00, 600.00, 'Mid-tier medical coverage with $1,000 individual deductible. Includes dental and vision. Specialist copay $40.', 'All full-time employees', '2025-11-30'),
(3, 'Gold Health', 'Medical', 'Aetna', 500.00, 800.00, 'Premium medical coverage with $250 individual deductible. Full dental, vision, and orthodontia.', 'All full-time employees', '2025-11-30'),
(4, 'Dental Plus', 'Dental', 'Delta Dental', 45.00, 90.00, 'Standalone dental plan covering preventive at 100%, basic at 80%, major at 50%.', 'All full-time employees', '2025-11-30'),
(5, 'Vision Care', 'Vision', 'VSP', 25.00, 50.00, 'Vision plan covering annual eye exam with $10 copay. Frame allowance $200 every 24 months.', 'All full-time employees', '2025-11-30'),
(6, 'Life Insurance', 'Life', 'MetLife', 0.00, 120.00, 'Company-paid basic life insurance equal to 2x annual salary up to $500,000.', 'All full-time employees', '2025-11-30'),
(7, 'FSA', 'FSA', 'WageWorks', 0.00, 0.00, 'Flexible Spending Account for healthcare expenses up to $3,050 annual limit.', 'All full-time employees', '2025-01-31'),
(8, 'HSA', 'HSA', 'Fidelity', 0.00, 50.00, 'Health Savings Account available with Bronze Health plan only. Triple tax advantage.', 'Bronze Health enrollees only', '2025-11-30');

CREATE OR REPLACE TABLE ACME_CORP.HR.benefits_enrollments (
    enrollment_id   INT,
    employee_id     INT,
    employee_name   VARCHAR,
    plan_id         INT,
    plan_name       VARCHAR,
    coverage_tier   VARCHAR,
    monthly_cost    NUMBER(8,2),
    start_date      DATE
);

INSERT INTO ACME_CORP.HR.benefits_enrollments VALUES
(1,  1,  'Sarah Chen',        3, 'Gold Health',     'Employee + Family',  850.00, '2018-04-01'),
(2,  1,  'Sarah Chen',        6, 'Life Insurance',  'Employee',           0.00,   '2018-04-01'),
(3,  2,  'Marcus Johnson',    2, 'Silver Health',   'Employee + Spouse',  520.00, '2019-08-01'),
(4,  2,  'Marcus Johnson',    4, 'Dental Plus',     'Employee + Spouse',  80.00,  '2019-08-01'),
(5,  3,  'Priya Patel',       3, 'Gold Health',     'Employee Only',      500.00, '2019-02-01'),
(6,  3,  'Priya Patel',       5, 'Vision Care',     'Employee Only',      25.00,  '2019-02-01'),
(7,  4,  'James Wilson',      1, 'Bronze Health',   'Employee Only',      150.00, '2021-07-01'),
(8,  4,  'James Wilson',      8, 'HSA',             'Employee Only',      0.00,   '2021-07-01'),
(9,  5,  'Lisa Zhang',        2, 'Silver Health',   'Employee Only',      300.00, '2022-02-01'),
(10, 6,  'David Kim',         3, 'Gold Health',     'Employee + Family',  850.00, '2017-12-01'),
(11, 6,  'David Kim',         6, 'Life Insurance',  'Employee + Spouse',  0.00,   '2017-12-01'),
(12, 7,  'Rachel Green',      1, 'Bronze Health',   'Employee Only',      150.00, '2020-10-01'),
(13, 8,  'Tom Martinez',      2, 'Silver Health',   'Employee Only',      300.00, '2020-05-01'),
(14, 9,  'Nina Gupta',        3, 'Gold Health',     'Employee + Spouse',  750.00, '2018-09-01'),
(15, 9,  'Nina Gupta',        7, 'FSA',             'Employee',           0.00,   '2025-01-01'),
(16, 10, 'Carlos Rivera',     2, 'Silver Health',   'Employee Only',      300.00, '2021-03-01'),
(17, 11, 'Amy Thompson',      3, 'Gold Health',     'Employee + Family',  850.00, '2016-06-01'),
(18, 11, 'Amy Thompson',      6, 'Life Insurance',  'Employee + Family',  0.00,   '2016-06-01'),
(19, 12, 'Brian Lee',         1, 'Bronze Health',   'Employee Only',      150.00, '2022-04-01'),
(20, 12, 'Brian Lee',         8, 'HSA',             'Employee Only',      0.00,   '2022-04-01'),
(21, 13, 'Diana Ross',        3, 'Gold Health',     'Employee + Spouse',  750.00, '2019-05-01'),
(22, 14, 'Eric Huang',        2, 'Silver Health',   'Employee Only',      300.00, '2021-09-01'),
(23, 15, 'Fatima Ali',        3, 'Gold Health',     'Employee + Family',  850.00, '2018-11-01'),
(24, 15, 'Fatima Ali',        5, 'Vision Care',     'Employee + Family',  60.00,  '2018-11-01'),
(25, 16, 'George Park',       2, 'Silver Health',   'Employee Only',      300.00, '2021-01-01'),
(26, 17, 'Hannah Brown',      2, 'Silver Health',   'Employee + Spouse',  520.00, '2019-07-01'),
(27, 18, 'Ian Stewart',       1, 'Bronze Health',   'Employee Only',      150.00, '2020-04-01'),
(28, 19, 'Julia Nguyen',      3, 'Gold Health',     'Employee + Spouse',  750.00, '2018-02-01'),
(29, 20, 'Kevin O''Brien',    1, 'Bronze Health',   'Employee Only',      150.00, '2023-10-01'),
(30, 20, 'Kevin O''Brien',    8, 'HSA',             'Employee Only',      0.00,   '2023-10-01');

-- Finance tables
CREATE OR REPLACE TABLE ACME_CORP.FINANCE.budgets (
    budget_id        INT,
    department       VARCHAR,
    fiscal_year      INT,
    fiscal_quarter   VARCHAR,
    allocated_amount NUMBER(12,2),
    spent_amount     NUMBER(12,2)
);

INSERT INTO ACME_CORP.FINANCE.budgets VALUES
(1,  'Engineering', 2025, 'Q1', 2500000, 2150000),
(2,  'Engineering', 2025, 'Q2', 2500000, 1800000),
(3,  'Engineering', 2025, 'Q3', 2700000, 950000),
(4,  'Engineering', 2025, 'Q4', 2700000, 0),
(5,  'Sales',       2025, 'Q1', 1800000, 1650000),
(6,  'Sales',       2025, 'Q2', 1800000, 1400000),
(7,  'Sales',       2025, 'Q3', 2000000, 700000),
(8,  'Sales',       2025, 'Q4', 2000000, 0),
(9,  'HR',          2025, 'Q1', 800000,  720000),
(10, 'HR',          2025, 'Q2', 800000,  600000),
(11, 'HR',          2025, 'Q3', 850000,  300000),
(12, 'HR',          2025, 'Q4', 850000,  0),
(13, 'Marketing',   2025, 'Q1', 1200000, 1100000),
(14, 'Marketing',   2025, 'Q2', 1200000, 900000),
(15, 'Marketing',   2025, 'Q3', 1500000, 500000),
(16, 'Marketing',   2025, 'Q4', 1500000, 0),
(17, 'IT',          2025, 'Q1', 1000000, 880000),
(18, 'IT',          2025, 'Q2', 1000000, 750000),
(19, 'IT',          2025, 'Q3', 1100000, 400000),
(20, 'IT',          2025, 'Q4', 1100000, 0);

CREATE OR REPLACE TABLE ACME_CORP.FINANCE.expenses (
    expense_id     INT,
    employee_name  VARCHAR,
    department     VARCHAR,
    amount         NUMBER(10,2),
    category       VARCHAR,
    status         VARCHAR,
    submitted_date DATE,
    description    VARCHAR
);

INSERT INTO ACME_CORP.FINANCE.expenses VALUES
(1,  'Marcus Johnson',  'Engineering', 2500.00, 'Conference',      'Approved',  '2025-02-10', 'KubeCon NA registration and travel'),
(2,  'Priya Patel',     'Engineering', 450.00,  'Software',        'Approved',  '2025-02-15', 'JetBrains annual license'),
(3,  'James Wilson',    'Engineering', 89.99,   'Books',           'Approved',  '2025-03-01', 'System Design Interview book'),
(4,  'Rachel Green',    'Sales',       3200.00, 'Client Dinner',   'Approved',  '2025-01-20', 'Q1 client appreciation dinner'),
(5,  'Tom Martinez',    'Sales',       1800.00, 'Travel',          'Approved',  '2025-02-28', 'Client site visit - Chicago'),
(6,  'Rachel Green',    'Sales',       15000.00,'Sponsorship',     'Pending',   '2025-03-15', 'Industry conference booth sponsorship'),
(7,  'Nina Gupta',      'HR',          5500.00, 'Training',        'Approved',  '2025-01-10', 'Leadership development program'),
(8,  'Carlos Rivera',   'HR',          350.00,  'Software',        'Approved',  '2025-02-20', 'BambooHR monthly subscription'),
(9,  'Brian Lee',       'Finance',     1200.00, 'Software',        'Approved',  '2025-01-15', 'Tableau license renewal'),
(10, 'Eric Huang',      'Marketing',   8500.00, 'Advertising',     'Approved',  '2025-02-01', 'Google Ads Q1 campaign'),
(11, 'Eric Huang',      'Marketing',   4200.00, 'Content',         'Pending',   '2025-03-10', 'Video production for product launch'),
(12, 'Diana Ross',      'Marketing',   25000.00,'Event',           'Pending',   '2025-03-20', 'Annual user conference venue deposit'),
(13, 'George Park',     'IT',          12000.00,'Hardware',        'Approved',  '2025-01-25', 'Server rack expansion'),
(14, 'Hannah Brown',    'IT',          3600.00, 'Software',        'Approved',  '2025-02-10', 'Datadog annual monitoring license'),
(15, 'Fatima Ali',      'IT',          8000.00, 'Consulting',      'Pending',   '2025-03-05', 'Security audit - external firm'),
(16, 'Sarah Chen',      'Engineering', 6000.00, 'Hardware',        'Approved',  '2025-01-30', 'M4 MacBook Pro for new hire'),
(17, 'David Kim',       'Sales',       950.00,  'Entertainment',   'Approved',  '2025-02-14', 'Team building event'),
(18, 'Ian Stewart',     'Engineering', 199.00,  'Software',        'Approved',  '2025-03-08', 'GitHub Copilot annual subscription'),
(19, 'Julia Nguyen',    'Sales',       4500.00, 'Travel',          'Approved',  '2025-03-12', 'Enterprise client QBR - NYC'),
(20, 'Kevin O''Brien',  'Engineering', 75.00,   'Books',           'Approved',  '2025-03-18', 'Designing Data-Intensive Applications');

CREATE OR REPLACE TABLE ACME_CORP.FINANCE.financial_reports (
    report_id          INT,
    report_type        VARCHAR,
    fiscal_year        INT,
    fiscal_quarter     VARCHAR,
    department         VARCHAR,
    revenue            NUMBER(12,2),
    cogs               NUMBER(12,2),
    gross_margin       NUMBER(12,2),
    operating_expense  NUMBER(12,2),
    net_income         NUMBER(12,2),
    generated_date     DATE
);

INSERT INTO ACME_CORP.FINANCE.financial_reports VALUES
(1,  'P&L', 2025, 'Q1', 'Engineering', 0,         0,        0,         2150000,  -2150000, '2025-04-05'),
(2,  'P&L', 2025, 'Q1', 'Sales',       8500000,   1200000,  7300000,   1650000,   5650000, '2025-04-05'),
(3,  'P&L', 2025, 'Q1', 'HR',          0,         0,        0,         720000,   -720000,  '2025-04-05'),
(4,  'P&L', 2025, 'Q1', 'Marketing',   0,         0,        0,         1100000,  -1100000, '2025-04-05'),
(5,  'P&L', 2025, 'Q1', 'IT',          0,         0,        0,         880000,   -880000,  '2025-04-05'),
(6,  'P&L', 2025, 'Q1', 'Finance',     0,         0,        0,         450000,   -450000,  '2025-04-05'),
(7,  'P&L', 2025, 'Q2', 'Engineering', 0,         0,        0,         1800000,  -1800000, '2025-07-05'),
(8,  'P&L', 2025, 'Q2', 'Sales',       9200000,   1350000,  7850000,   1400000,   6450000, '2025-07-05'),
(9,  'P&L', 2025, 'Q2', 'HR',          0,         0,        0,         600000,   -600000,  '2025-07-05'),
(10, 'P&L', 2025, 'Q2', 'Marketing',   0,         0,        0,         900000,   -900000,  '2025-07-05'),
(11, 'P&L', 2025, 'Q2', 'IT',          0,         0,        0,         750000,   -750000,  '2025-07-05'),
(12, 'P&L', 2025, 'Q2', 'Finance',     0,         0,        0,         380000,   -380000,  '2025-07-05');

CREATE OR REPLACE TABLE ACME_CORP.FINANCE.spend_approvals (
    approval_id    INT,
    requestor      VARCHAR,
    department     VARCHAR,
    amount         NUMBER(10,2),
    category       VARCHAR,
    justification  VARCHAR,
    status         VARCHAR,
    approver       VARCHAR,
    submitted_date DATE,
    decided_date   DATE
);

INSERT INTO ACME_CORP.FINANCE.spend_approvals VALUES
(1,  'Sarah Chen',      'Engineering', 45000.00,  'Hardware', 'GPU servers for ML training pipeline.', 'Approved', 'Amy Thompson', '2025-01-15', '2025-01-18'),
(2,  'Marcus Johnson',  'Engineering', 12000.00,  'Software', 'Datadog APM license expansion.', 'Approved', 'Sarah Chen', '2025-01-22', '2025-01-23'),
(3,  'David Kim',       'Sales',       75000.00,  'Event', 'Annual Sales Kickoff event.', 'Approved', 'Amy Thompson', '2025-02-01', '2025-02-05'),
(4,  'Diana Ross',      'Marketing',   35000.00,  'Advertising', 'Q2 digital marketing campaign.', 'Pending', NULL, '2025-03-10', NULL),
(5,  'Fatima Ali',      'IT',          28000.00,  'Consulting', 'External penetration testing.', 'Approved', 'Amy Thompson', '2025-02-20', '2025-02-22'),
(6,  'Rachel Green',    'Sales',       15000.00,  'Sponsorship', 'Conference booth sponsorship.', 'Pending', NULL, '2025-03-15', NULL),
(7,  'Nina Gupta',      'HR',          18000.00,  'Training', 'DEI training program.', 'Approved', 'Amy Thompson', '2025-02-10', '2025-02-12'),
(8,  'Hannah Brown',    'IT',          8500.00,   'Software', 'PagerDuty Enterprise upgrade.', 'Approved', 'Fatima Ali', '2025-03-01', '2025-03-03'),
(9,  'Eric Huang',      'Marketing',   4200.00,   'Content', 'Video production for launch.', 'Pending', NULL, '2025-03-10', NULL),
(10, 'Priya Patel',     'Engineering', 6500.00,   'Conference', 'Team attendance at re:Invent.', 'Approved', 'Sarah Chen', '2025-02-28', '2025-03-01');

-- IT tables
CREATE OR REPLACE TABLE ACME_CORP.IT.incidents (
    incident_id  INT,
    title        VARCHAR,
    severity     VARCHAR,
    status       VARCHAR,
    description  VARCHAR,
    assigned_to  VARCHAR,
    created_date TIMESTAMP,
    resolved_date TIMESTAMP
);

INSERT INTO ACME_CORP.IT.incidents VALUES
(1001, 'Production API latency spike', 'P1', 'Resolved', 'API response times exceeded 5s for 15 minutes during peak traffic. Root cause: connection pool exhaustion on primary database.', 'Hannah Brown', '2025-03-01 09:15:00', '2025-03-01 09:45:00'),
(1002, 'SSO login failures', 'P2', 'Resolved', 'Multiple users reported inability to log in via SSO. SAML assertion validation was failing due to expired IdP certificate.', 'George Park', '2025-03-05 14:30:00', '2025-03-05 16:00:00'),
(1003, 'Data pipeline stale - 6h delay', 'P2', 'Resolved', 'Daily ETL pipeline for sales analytics was delayed by 6 hours. Snowflake task was suspended due to warehouse credit quota.', 'Hannah Brown', '2025-03-08 06:00:00', '2025-03-08 12:30:00'),
(1004, 'Memory leak in notification service', 'P3', 'Resolved', 'Notification microservice memory usage grew linearly over 48 hours, triggering OOM kills.', 'George Park', '2025-03-10 10:00:00', '2025-03-12 14:00:00'),
(1005, 'CDN cache invalidation failure', 'P2', 'Resolved', 'Static assets serving stale content after deployment. CloudFront invalidation limit exceeded.', 'Fatima Ali', '2025-03-14 11:20:00', '2025-03-14 13:00:00'),
(1006, 'Kubernetes node not ready', 'P3', 'Resolved', 'Worker node k8s-prod-07 entered NotReady state due to disk pressure from container logs.', 'Hannah Brown', '2025-03-15 08:45:00', '2025-03-15 10:15:00'),
(1007, 'Email delivery delays', 'P3', 'Open', 'Transactional emails experiencing 30-45 minute delays. SES sending rate appears throttled.', 'George Park', '2025-03-18 16:00:00', NULL),
(1008, 'Staging environment down', 'P3', 'Open', 'Staging cluster unreachable after routine maintenance. Load balancer health checks failing.', 'Hannah Brown', '2025-03-19 09:30:00', NULL),
(1009, 'Database replication lag > 30s', 'P1', 'Investigating', 'Read replica lag exceeding 30 seconds during business hours.', 'Fatima Ali', '2025-03-20 07:00:00', NULL),
(1010, 'SSL certificate expiring in 7 days', 'P4', 'Open', 'Wildcard certificate for *.internal.acme.com expires March 27. Auto-renewal failed.', 'George Park', '2025-03-20 10:00:00', NULL);

CREATE OR REPLACE TABLE ACME_CORP.IT.services (
    service_id   INT,
    service_name VARCHAR,
    status       VARCHAR,
    uptime_pct   NUMBER(5,2),
    owner_team   VARCHAR,
    environment  VARCHAR
);

INSERT INTO ACME_CORP.IT.services VALUES
(1, 'API Gateway',           'Healthy',   99.95, 'Platform',    'Production'),
(2, 'Authentication Service','Healthy',   99.99, 'Platform',    'Production'),
(3, 'Notification Service',  'Degraded',  99.80, 'Platform',    'Production'),
(4, 'Data Pipeline',         'Healthy',   99.90, 'Data Eng',    'Production'),
(5, 'Web Application',       'Healthy',   99.97, 'Frontend',    'Production'),
(6, 'Search Service',        'Healthy',   99.92, 'Platform',    'Production'),
(7, 'Payment Processing',    'Healthy',   99.99, 'Payments',    'Production'),
(8, 'Analytics Dashboard',   'Healthy',   99.85, 'Data Eng',    'Production'),
(9, 'CI/CD Pipeline',        'Healthy',   99.70, 'DevOps',      'Internal'),
(10,'Staging Cluster',       'Down',      95.20, 'DevOps',      'Staging');

CREATE OR REPLACE TABLE ACME_CORP.IT.sla_records (
    sla_id          INT,
    service_name    VARCHAR,
    metric_name     VARCHAR,
    target_value    NUMBER(6,2),
    actual_value    NUMBER(6,2),
    period          VARCHAR,
    status          VARCHAR,
    breach_minutes  INT
);

INSERT INTO ACME_CORP.IT.sla_records VALUES
(1,  'API Gateway',            'Uptime %',            99.90, 99.95, '2025-Q1', 'Met',      0),
(2,  'API Gateway',            'P99 Latency (ms)',    500,   320,   '2025-Q1', 'Met',      0),
(3,  'Authentication Service', 'Uptime %',            99.99, 99.99, '2025-Q1', 'Met',      0),
(4,  'Authentication Service', 'Login Success Rate',  99.50, 99.20, '2025-Q1', 'Breached', 0),
(5,  'Notification Service',   'Uptime %',            99.90, 99.80, '2025-Q1', 'Breached', 144),
(6,  'Notification Service',   'Delivery Latency (s)',30,    45,    '2025-Q1', 'Breached', 0),
(7,  'Data Pipeline',          'Uptime %',            99.90, 99.90, '2025-Q1', 'Met',      0),
(8,  'Data Pipeline',          'Max Delay (hours)',   2,     6,     '2025-Q1', 'Breached', 240),
(9,  'Web Application',        'Uptime %',            99.95, 99.97, '2025-Q1', 'Met',      0),
(10, 'Web Application',        'P95 Load Time (s)',   3,     2.1,   '2025-Q1', 'Met',      0),
(11, 'Search Service',         'Uptime %',            99.90, 99.92, '2025-Q1', 'Met',      0),
(12, 'Payment Processing',     'Uptime %',            99.99, 99.99, '2025-Q1', 'Met',      0),
(13, 'Payment Processing',     'Transaction Success', 99.95, 99.97, '2025-Q1', 'Met',      0),
(14, 'Analytics Dashboard',    'Uptime %',            99.50, 99.85, '2025-Q1', 'Met',      0),
(15, 'CI/CD Pipeline',         'Uptime %',            99.00, 99.70, '2025-Q1', 'Met',      0),
(16, 'CI/CD Pipeline',         'Build Success Rate',  95.00, 92.30, '2025-Q1', 'Breached', 0),
(17, 'Staging Cluster',        'Uptime %',            99.00, 95.20, '2025-Q1', 'Breached', 5472),
(18, 'API Gateway',            'Error Rate %',        1.00,  0.45,  '2025-Q1', 'Met',      0),
(19, 'Notification Service',   'Queue Depth',         1000,  3500,  '2025-Q1', 'Breached', 0),
(20, 'Data Pipeline',          'Freshness (hours)',   1,     0.5,   '2025-Q1', 'Met',      0);

CREATE OR REPLACE TABLE ACME_CORP.IT.infrastructure_assets (
    asset_id            INT,
    asset_name          VARCHAR,
    asset_type          VARCHAR,
    environment         VARCHAR,
    status              VARCHAR,
    cpu_utilization     NUMBER(5,2),
    memory_utilization  NUMBER(5,2),
    last_health_check   TIMESTAMP,
    owner_team          VARCHAR
);

INSERT INTO ACME_CORP.IT.infrastructure_assets VALUES
(1,  'k8s-prod-01', 'Kubernetes Node', 'Production', 'Healthy',  45.20, 62.10, '2025-03-20 10:00:00', 'Platform'),
(2,  'k8s-prod-02', 'Kubernetes Node', 'Production', 'Healthy',  52.80, 58.30, '2025-03-20 10:00:00', 'Platform'),
(3,  'k8s-prod-03', 'Kubernetes Node', 'Production', 'Healthy',  38.50, 71.20, '2025-03-20 10:00:00', 'Platform'),
(4,  'k8s-prod-04', 'Kubernetes Node', 'Production', 'Warning',  78.90, 85.40, '2025-03-20 10:00:00', 'Platform'),
(5,  'k8s-prod-05', 'Kubernetes Node', 'Production', 'Healthy',  41.10, 55.70, '2025-03-20 10:00:00', 'Platform'),
(6,  'k8s-prod-06', 'Kubernetes Node', 'Production', 'Healthy',  35.60, 48.90, '2025-03-20 10:00:00', 'Platform'),
(7,  'k8s-prod-07', 'Kubernetes Node', 'Production', 'Cordoned', 0.00,  12.30, '2025-03-15 10:15:00', 'Platform'),
(8,  'db-primary-01','Database Server', 'Production', 'Healthy',  62.40, 78.50, '2025-03-20 10:00:00', 'Data Eng'),
(9,  'db-replica-01','Database Server', 'Production', 'Warning',  55.30, 72.10, '2025-03-20 10:00:00', 'Data Eng'),
(10, 'db-replica-02','Database Server', 'Production', 'Healthy',  48.70, 65.80, '2025-03-20 10:00:00', 'Data Eng'),
(11, 'lb-prod-01',  'Load Balancer',   'Production', 'Healthy',  22.10, 35.40, '2025-03-20 10:00:00', 'Platform'),
(12, 'lb-prod-02',  'Load Balancer',   'Production', 'Healthy',  19.80, 32.10, '2025-03-20 10:00:00', 'Platform'),
(13, 'cache-prod-01','Redis Cluster',   'Production', 'Healthy',  31.50, 45.20, '2025-03-20 10:00:00', 'Platform'),
(14, 'k8s-stg-01',  'Kubernetes Node', 'Staging',    'Down',     0.00,  0.00,  '2025-03-19 09:30:00', 'DevOps'),
(15, 'k8s-stg-02',  'Kubernetes Node', 'Staging',    'Down',     0.00,  0.00,  '2025-03-19 09:30:00', 'DevOps');

CREATE OR REPLACE TABLE ACME_CORP.FINANCE.product_usage (
    usage_id        INT,
    product_name    VARCHAR,
    customer_name   VARCHAR,
    department      VARCHAR,
    fiscal_quarter  VARCHAR,
    fiscal_year     INT,
    active_users    INT,
    sessions        INT,
    api_calls       INT,
    revenue         NUMBER(12,2),
    arr             NUMBER(12,2),
    churn_risk      VARCHAR
);

INSERT INTO ACME_CORP.FINANCE.product_usage VALUES
(1,  'Acme Analytics Pro',  'TechCorp Inc',       'Enterprise', 'Q1', 2025, 1250, 45000,  320000,  125000, 500000,  'Low'),
(2,  'Acme Analytics Pro',  'DataDriven LLC',      'Mid-Market', 'Q1', 2025, 380,  12000,  95000,   48000,  192000,  'Medium'),
(3,  'Acme Analytics Pro',  'StartupXYZ',          'SMB',        'Q1', 2025, 45,   1800,   12000,   8500,   34000,   'High'),
(4,  'Acme Workflow Suite', 'TechCorp Inc',        'Enterprise', 'Q1', 2025, 890,  32000,  180000,  95000,  380000,  'Low'),
(5,  'Acme Workflow Suite', 'Global Logistics Co', 'Enterprise', 'Q1', 2025, 2100, 78000,  520000,  175000, 700000,  'Low'),
(6,  'Acme Workflow Suite', 'DataDriven LLC',      'Mid-Market', 'Q1', 2025, 210,  7500,   48000,   32000,  128000,  'Low'),
(7,  'Acme Dev Tools',      'TechCorp Inc',        'Enterprise', 'Q1', 2025, 450,  18000,  250000,  65000,  260000,  'Low'),
(8,  'Acme Dev Tools',      'CodeShop Agency',     'SMB',        'Q1', 2025, 85,   3200,   42000,   12000,  48000,   'Medium'),
(9,  'Acme Analytics Pro',  'TechCorp Inc',        'Enterprise', 'Q2', 2025, 1320, 48000,  345000,  125000, 500000,  'Low'),
(10, 'Acme Analytics Pro',  'DataDriven LLC',      'Mid-Market', 'Q2', 2025, 350,  10500,  82000,   48000,  192000,  'High'),
(11, 'Acme Analytics Pro',  'StartupXYZ',          'SMB',        'Q2', 2025, 28,   900,    6000,    8500,   34000,   'High'),
(12, 'Acme Workflow Suite', 'TechCorp Inc',        'Enterprise', 'Q2', 2025, 920,  34000,  195000,  95000,  380000,  'Low'),
(13, 'Acme Workflow Suite', 'Global Logistics Co', 'Enterprise', 'Q2', 2025, 2250, 82000,  548000,  175000, 700000,  'Low'),
(14, 'Acme Workflow Suite', 'DataDriven LLC',      'Mid-Market', 'Q2', 2025, 195,  6800,   41000,   32000,  128000,  'Medium'),
(15, 'Acme Dev Tools',      'TechCorp Inc',        'Enterprise', 'Q2', 2025, 480,  19500,  268000,  65000,  260000,  'Low'),
(16, 'Acme Dev Tools',      'CodeShop Agency',     'SMB',        'Q2', 2025, 72,   2600,   35000,   12000,  48000,   'High');

CREATE OR REPLACE TABLE ACME_CORP.FINANCE.invoices (
    invoice_id      INT,
    vendor_name     VARCHAR,
    invoice_number  VARCHAR,
    department      VARCHAR,
    amount          NUMBER(12,2),
    status          VARCHAR,
    due_date        DATE,
    description     VARCHAR,
    category        VARCHAR,
    submitted_date  DATE
);

INSERT INTO ACME_CORP.FINANCE.invoices VALUES
(1,  'AWS',                'INV-2025-0012', 'IT',          85000.00,  'Paid',     '2025-02-15', 'AWS monthly infrastructure costs for January 2025. Includes EC2, S3, RDS, and CloudFront usage across production and staging environments. Usage increased 12% MoM due to ML training workloads.', 'Cloud Infrastructure', '2025-01-31'),
(2,  'Datadog',            'DD-4891',       'IT',          3600.00,   'Paid',     '2025-02-28', 'Annual Datadog Enterprise monitoring license renewal. Covers APM, infrastructure monitoring, log management, and synthetic testing for 50 hosts.', 'Software', '2025-02-10'),
(3,  'WeWork',             'WW-2025-Q1',    'HR',          45000.00,  'Paid',     '2025-01-31', 'Q1 2025 office lease payment for 120-person capacity at 500 Market St, San Francisco. Includes conference rooms, common areas, and parking allocation.', 'Facilities', '2025-01-15'),
(4,  'Salesforce',         'SF-98234',      'Sales',       28000.00,  'Paid',     '2025-03-01', 'Salesforce Enterprise CRM annual subscription renewal for 35 seats. Includes Sales Cloud, Service Cloud, and Pardot marketing automation.', 'Software', '2025-02-15'),
(5,  'Deloitte',           'DLT-2025-0891', 'Finance',     125000.00, 'Pending',  '2025-04-15', 'Q1 2025 external audit services. Includes SOX compliance review, financial statement audit, and internal controls assessment.', 'Professional Services', '2025-03-20'),
(6,  'Google Cloud',       'GCP-JAN-2025',  'Engineering', 42000.00,  'Paid',     '2025-02-10', 'Google Cloud Platform January 2025 usage. BigQuery analytics, GKE cluster management, and Vertex AI model training costs.', 'Cloud Infrastructure', '2025-01-31'),
(7,  'Figma',              'FIG-2025-112',  'Marketing',   4800.00,   'Paid',     '2025-02-20', 'Figma Enterprise annual subscription for 15 designer seats. Includes FigJam, Dev Mode, and advanced prototyping.', 'Software', '2025-02-05'),
(8,  'CrowdStrike',        'CS-ENT-7723',   'IT',          18500.00,  'Paid',     '2025-03-15', 'CrowdStrike Falcon Enterprise endpoint protection renewal. Covers 200 endpoints with EDR, threat intelligence, and managed hunting.', 'Security', '2025-03-01'),
(9,  'Stripe',             'STR-2025-Q1',   'Engineering', 15200.00,  'Paid',     '2025-04-01', 'Stripe payment processing fees for Q1 2025. 2.9% + $0.30 per transaction across all payment methods.', 'Payment Processing', '2025-03-31'),
(10, 'Robert Half',        'RH-2025-0234',  'HR',          35000.00,  'Pending',  '2025-04-10', 'Temporary staffing services for Q1 2025. Three contract recruiters supporting Engineering and Sales hiring pipeline.', 'Professional Services', '2025-03-25'),
(11, 'Snowflake',          'SNO-2025-0089', 'Engineering', 52000.00,  'Paid',     '2025-03-01', 'Snowflake compute and storage credits for February 2025. Includes warehouse usage for analytics, ML feature store, and data sharing.', 'Cloud Infrastructure', '2025-02-28'),
(12, 'Gartner',            'GART-MQ-2025',  'Sales',       22000.00,  'Pending',  '2025-04-30', 'Gartner Magic Quadrant participation and analyst access subscription. Includes 4 analyst inquiry sessions and research portal access.', 'Research', '2025-03-15');

SELECT 'All 16 tables created in ACME_CORP' AS status;

-- ============================================================
-- STEP 2: CORTEX SEARCH SERVICES (4)
-- ============================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE ACME_CORP.HR.handbook_search_svc
  ON content
  ATTRIBUTES title, section
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  AS (
    SELECT doc_id, title, section, content, last_updated
    FROM ACME_CORP.HR.handbook_docs
  );

CREATE OR REPLACE CORTEX SEARCH SERVICE ACME_CORP.IT.incident_search_svc
  ON description
  ATTRIBUTES title, severity, status, assigned_to
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  AS (
    SELECT incident_id, title, severity, status, description, assigned_to, created_date, resolved_date
    FROM ACME_CORP.IT.incidents
  );

CREATE OR REPLACE CORTEX SEARCH SERVICE ACME_CORP.FINANCE.invoice_search_svc
  ON description
  ATTRIBUTES vendor_name, invoice_number, department, category, status
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  AS (
    SELECT invoice_id, vendor_name, invoice_number, department, amount, status, due_date, description, category, submitted_date
    FROM ACME_CORP.FINANCE.invoices
  );

CREATE OR REPLACE CORTEX SEARCH SERVICE ACME_CORP.FINANCE.spend_approvals_search_svc
  ON justification
  ATTRIBUTES requestor, department, category, status, approver
  WAREHOUSE = COMPUTE
  TARGET_LAG = '1 hour'
  AS (
    SELECT approval_id, requestor, department, amount, category, justification, status, approver, submitted_date, decided_date
    FROM ACME_CORP.FINANCE.spend_approvals
  );

SELECT 'Cortex Search services created (4)' AS status;

-- ============================================================
-- STEP 3: SEMANTIC VIEWS
-- ============================================================

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.HR.comp_semantic_view
  TABLES (
    employees AS ACME_CORP.HR.employees PRIMARY KEY (employee_id),
    compensation_bands AS ACME_CORP.HR.compensation_bands PRIMARY KEY (band_id) UNIQUE (level, department)
  )
  RELATIONSHIPS (
    employees (level, department) REFERENCES compensation_bands (level, department)
  )
  FACTS (
    employees.salary AS salary,
    compensation_bands.min_salary AS min_salary,
    compensation_bands.max_salary AS max_salary
  )
  DIMENSIONS (
    employees.name AS name COMMENT = 'Full name of the employee',
    employees.department AS department COMMENT = 'Department (Engineering, Sales, HR, Finance, Marketing, IT)',
    employees.title AS title COMMENT = 'Job title of the employee',
    employees.level AS level COMMENT = 'Career level from L4 (junior) to L9 (C-suite)',
    employees.email AS email,
    employees.hire_date AS hire_date COMMENT = 'Date the employee was hired'
  )
  METRICS (
    employees.headcount AS COUNT(employee_id) COMMENT = 'Total number of employees',
    employees.average_salary AS AVG(salary) COMMENT = 'Average employee salary',
    employees.total_payroll AS SUM(salary) COMMENT = 'Total salary expenditure',
    employees.max_salary_in_group AS MAX(salary) COMMENT = 'Highest salary in the group',
    employees.min_salary_in_group AS MIN(salary) COMMENT = 'Lowest salary in the group'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.FINANCE.budget_semantic_view
  TABLES (
    budgets AS ACME_CORP.FINANCE.budgets PRIMARY KEY (budget_id),
    expenses AS ACME_CORP.FINANCE.expenses PRIMARY KEY (expense_id)
  )
  FACTS (
    budgets.allocated_amount AS allocated_amount,
    budgets.spent_amount AS spent_amount,
    expenses.amount AS amount
  )
  DIMENSIONS (
    budgets.department AS department COMMENT = 'Department name (Engineering, Sales, HR, Finance, Marketing, IT)',
    budgets.fiscal_year AS fiscal_year COMMENT = 'Fiscal year for the budget',
    budgets.fiscal_quarter AS fiscal_quarter COMMENT = 'Fiscal quarter (Q1, Q2, Q3, Q4)',
    expenses.employee_name AS employee_name COMMENT = 'Employee who submitted the expense',
    expenses.category AS category COMMENT = 'Expense category (Conference, Software, Travel, Hardware, etc.)',
    expenses.status AS status COMMENT = 'Approval status: Approved or Pending',
    expenses.submitted_date AS submitted_date COMMENT = 'Date the expense was submitted',
    expenses.description AS description COMMENT = 'Description of the expense'
  )
  METRICS (
    budgets.total_allocated AS SUM(allocated_amount) COMMENT = 'Total budget allocated',
    budgets.total_spent AS SUM(spent_amount) COMMENT = 'Total budget spent',
    expenses.total_expenses AS SUM(amount) COMMENT = 'Total expense amount',
    expenses.expense_count AS COUNT(expense_id) COMMENT = 'Number of expense submissions',
    expenses.average_expense AS AVG(amount) COMMENT = 'Average expense amount'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.FINANCE.product_usage_semantic_view
  TABLES (
    product_usage AS ACME_CORP.FINANCE.product_usage PRIMARY KEY (usage_id)
  )
  FACTS (
    product_usage.active_users AS active_users,
    product_usage.sessions AS sessions,
    product_usage.api_calls AS api_calls,
    product_usage.revenue AS revenue,
    product_usage.arr AS arr
  )
  DIMENSIONS (
    product_usage.product_name AS product_name COMMENT = 'Product name (Acme Analytics Pro, Acme Workflow Suite, Acme Dev Tools)',
    product_usage.customer_name AS customer_name COMMENT = 'Customer account name',
    product_usage.department AS department COMMENT = 'Customer segment (Enterprise, Mid-Market, SMB)',
    product_usage.fiscal_quarter AS fiscal_quarter COMMENT = 'Fiscal quarter (Q1, Q2, Q3, Q4)',
    product_usage.fiscal_year AS fiscal_year COMMENT = 'Fiscal year',
    product_usage.churn_risk AS churn_risk COMMENT = 'Churn risk level (Low, Medium, High)'
  )
  METRICS (
    product_usage.total_revenue AS SUM(revenue) COMMENT = 'Total revenue across products and customers',
    product_usage.total_arr AS SUM(arr) COMMENT = 'Total annual recurring revenue',
    product_usage.total_active_users AS SUM(active_users) COMMENT = 'Total active users across all products',
    product_usage.total_sessions AS SUM(sessions) COMMENT = 'Total user sessions',
    product_usage.total_api_calls AS SUM(api_calls) COMMENT = 'Total API calls',
    product_usage.avg_revenue_per_customer AS AVG(revenue) COMMENT = 'Average revenue per customer',
    product_usage.customer_count AS COUNT(DISTINCT customer_name) COMMENT = 'Number of unique customers'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.HR.benefits_semantic_view
  TABLES (
    benefits_plans AS ACME_CORP.HR.benefits_plans PRIMARY KEY (plan_id),
    benefits_enrollments AS ACME_CORP.HR.benefits_enrollments PRIMARY KEY (enrollment_id)
  )
  RELATIONSHIPS (
    benefits_enrollments (plan_id) REFERENCES benefits_plans (plan_id)
  )
  FACTS (
    benefits_plans.monthly_cost_employee AS monthly_cost_employee,
    benefits_plans.monthly_cost_employer AS monthly_cost_employer,
    benefits_enrollments.monthly_cost AS monthly_cost
  )
  DIMENSIONS (
    benefits_plans.plan_name AS plan_name COMMENT = 'Name of the benefits plan (Bronze Health, Silver Health, Gold Health, Dental Plus, Vision Care, Life Insurance, FSA, HSA)',
    benefits_plans.plan_type AS plan_type COMMENT = 'Type of plan (Medical, Dental, Vision, Life, FSA, HSA)',
    benefits_plans.provider AS provider COMMENT = 'Insurance provider name',
    benefits_plans.eligibility AS eligibility COMMENT = 'Who is eligible for this plan',
    benefits_enrollments.employee_name AS employee_name COMMENT = 'Name of enrolled employee',
    benefits_enrollments.coverage_tier AS coverage_tier COMMENT = 'Coverage tier (Employee Only, Employee + Spouse, Employee + Family)',
    benefits_enrollments.start_date AS start_date COMMENT = 'Date enrollment began'
  )
  METRICS (
    benefits_enrollments.total_enrollment_cost AS SUM(monthly_cost) COMMENT = 'Total monthly cost across all enrollments',
    benefits_enrollments.enrollment_count AS COUNT(enrollment_id) COMMENT = 'Number of benefit enrollments',
    benefits_enrollments.avg_employee_cost AS AVG(monthly_cost) COMMENT = 'Average monthly employee cost',
    benefits_plans.total_employer_cost AS SUM(monthly_cost_employer) COMMENT = 'Total monthly employer cost across plans'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.HR.org_semantic_view
  TABLES (
    org_chart AS ACME_CORP.HR.org_chart PRIMARY KEY (employee_id),
    employees AS ACME_CORP.HR.employees PRIMARY KEY (employee_id)
  )
  RELATIONSHIPS (
    org_chart (employee_id) REFERENCES employees (employee_id)
  )
  FACTS (
    org_chart.span_of_control AS span_of_control,
    org_chart.org_level AS org_level,
    employees.salary AS salary
  )
  DIMENSIONS (
    org_chart.name AS name COMMENT = 'Employee name',
    org_chart.department AS department COMMENT = 'Department (Engineering, Sales, HR, Finance, Marketing, IT)',
    org_chart.title AS title COMMENT = 'Job title',
    org_chart.manager_name AS manager_name COMMENT = 'Direct manager name (NULL for top-level)',
    employees.level AS level COMMENT = 'Career level (L4 to L9)',
    employees.hire_date AS hire_date COMMENT = 'Hire date'
  )
  METRICS (
    org_chart.total_headcount AS COUNT(employee_id) COMMENT = 'Total headcount',
    org_chart.avg_span AS AVG(span_of_control) COMMENT = 'Average span of control',
    org_chart.max_depth AS MAX(org_level) COMMENT = 'Deepest org level',
    org_chart.total_direct_reports AS SUM(span_of_control) COMMENT = 'Total direct reports across managers'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.FINANCE.spend_semantic_view
  TABLES (
    spend_approvals AS ACME_CORP.FINANCE.spend_approvals PRIMARY KEY (approval_id)
  )
  FACTS (
    spend_approvals.amount AS amount
  )
  DIMENSIONS (
    spend_approvals.requestor AS requestor COMMENT = 'Person who requested the spend',
    spend_approvals.department AS department COMMENT = 'Department (Engineering, Sales, HR, Marketing, IT)',
    spend_approvals.category AS category COMMENT = 'Spend category (Hardware, Software, Event, Consulting, Training, etc.)',
    spend_approvals.status AS status COMMENT = 'Approval status (Approved, Pending)',
    spend_approvals.approver AS approver COMMENT = 'Person who approved (NULL if pending)',
    spend_approvals.submitted_date AS submitted_date COMMENT = 'Date submitted',
    spend_approvals.decided_date AS decided_date COMMENT = 'Date decided (NULL if pending)'
  )
  METRICS (
    spend_approvals.total_requested AS SUM(amount) COMMENT = 'Total amount requested',
    spend_approvals.request_count AS COUNT(approval_id) COMMENT = 'Number of spend requests',
    spend_approvals.avg_request_amount AS AVG(amount) COMMENT = 'Average request amount'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.FINANCE.financial_reports_semantic_view
  TABLES (
    financial_reports AS ACME_CORP.FINANCE.financial_reports PRIMARY KEY (report_id)
  )
  FACTS (
    financial_reports.revenue AS revenue,
    financial_reports.cogs AS cogs,
    financial_reports.gross_margin AS gross_margin,
    financial_reports.operating_expense AS operating_expense,
    financial_reports.net_income AS net_income
  )
  DIMENSIONS (
    financial_reports.report_type AS report_type COMMENT = 'Report type (P&L)',
    financial_reports.fiscal_year AS fiscal_year COMMENT = 'Fiscal year',
    financial_reports.fiscal_quarter AS fiscal_quarter COMMENT = 'Fiscal quarter (Q1, Q2)',
    financial_reports.department AS department COMMENT = 'Department (Engineering, Sales, HR, Marketing, IT, Finance)',
    financial_reports.generated_date AS generated_date COMMENT = 'Date report was generated'
  )
  METRICS (
    financial_reports.total_revenue AS SUM(revenue) COMMENT = 'Total revenue',
    financial_reports.total_net_income AS SUM(net_income) COMMENT = 'Total net income',
    financial_reports.total_opex AS SUM(operating_expense) COMMENT = 'Total operating expenses',
    financial_reports.total_gross_margin AS SUM(gross_margin) COMMENT = 'Total gross margin',
    financial_reports.avg_margin_pct AS AVG(CASE WHEN revenue > 0 THEN gross_margin / revenue * 100 END) COMMENT = 'Average gross margin percentage'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.IT.infra_semantic_view
  TABLES (
    infrastructure_assets AS ACME_CORP.IT.infrastructure_assets PRIMARY KEY (asset_id)
  )
  FACTS (
    infrastructure_assets.cpu_utilization AS cpu_utilization,
    infrastructure_assets.memory_utilization AS memory_utilization
  )
  DIMENSIONS (
    infrastructure_assets.asset_name AS asset_name COMMENT = 'Infrastructure asset name (k8s-prod-01, db-primary-01, lb-prod-01, cache-prod-01, etc.)',
    infrastructure_assets.asset_type AS asset_type COMMENT = 'Asset type (Kubernetes Node, Database Server, Load Balancer, Redis Cluster)',
    infrastructure_assets.environment AS environment COMMENT = 'Environment (Production, Staging)',
    infrastructure_assets.status AS status COMMENT = 'Asset health status (Healthy, Warning, Cordoned, Down)',
    infrastructure_assets.owner_team AS owner_team COMMENT = 'Team that owns the asset (Platform, Data Eng, DevOps)'
  )
  METRICS (
    infrastructure_assets.avg_cpu AS AVG(cpu_utilization) COMMENT = 'Average CPU utilization %',
    infrastructure_assets.avg_memory AS AVG(memory_utilization) COMMENT = 'Average memory utilization %',
    infrastructure_assets.asset_count AS COUNT(asset_id) COMMENT = 'Number of infrastructure assets'
  );

CREATE OR REPLACE SEMANTIC VIEW ACME_CORP.IT.sla_semantic_view
  TABLES (
    sla_records AS ACME_CORP.IT.sla_records PRIMARY KEY (sla_id)
  )
  FACTS (
    sla_records.target_value AS target_value,
    sla_records.actual_value AS actual_value,
    sla_records.breach_minutes AS breach_minutes
  )
  DIMENSIONS (
    sla_records.service_name AS service_name COMMENT = 'Service name (API Gateway, Authentication Service, Notification Service, Data Pipeline, Web Application, etc.)',
    sla_records.metric_name AS metric_name COMMENT = 'SLA metric name (Uptime %, P99 Latency ms, Error Rate %, Login Success Rate, Build Success Rate, etc.)',
    sla_records.period AS period COMMENT = 'SLA measurement period (e.g. 2025-Q1)',
    sla_records.status AS status COMMENT = 'SLA compliance status (Met or Breached)'
  )
  METRICS (
    sla_records.total_breach_minutes AS SUM(breach_minutes) COMMENT = 'Total SLA breach minutes',
    sla_records.sla_count AS COUNT(sla_id) COMMENT = 'Number of SLA records',
    sla_records.breach_count AS COUNT(CASE WHEN status = 'Breached' THEN 1 END) COMMENT = 'Number of breached SLAs'
  );

SELECT 'Semantic views created' AS status;

-- ============================================================
-- STEP 4: MCP SERVERS (10 specialized)
-- ============================================================

CREATE OR REPLACE MCP SERVER ACME_CORP.HR.handbook_comp_server
  FROM SPECIFICATION $$
    tools:
      - name: "handbook-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "ACME_CORP.HR.handbook_search_svc"
        title: "Employee Handbook Search"
        description: "Search the employee handbook. Searchable text: content. Filterable attributes: title, section (Benefits, Career Development, Compensation, Compliance, Finance, Getting Started, IT & Security, Time Off, Work Arrangements). Returned columns: doc_id, title, section, content, last_updated. Use @eq filter on section to narrow results. Only @eq filters are supported — no @gte, @lte, @gt, @lt. For date questions, include date terms in the query text instead. Do NOT request columns not listed here."

      - name: "compensation-analyst"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.HR.comp_semantic_view"
        title: "Compensation Analyst"
        description: "Ask natural language questions about employee compensation, salary bands, headcount by department, and payroll analytics."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.FINANCE.budget_server
  FROM SPECIFICATION $$
    tools:
      - name: "budget-analyst"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.FINANCE.budget_semantic_view"
        title: "Budget Analyst"
        description: "Ask natural language questions about department budgets, expense trends, budget utilization rates, and spending forecasts."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.IT.incident_server
  FROM SPECIFICATION $$
    tools:
      - name: "incident-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "ACME_CORP.IT.incident_search_svc"
        title: "Incident Search"
        description: "Search IT incident records. Searchable text: description. Filterable attributes: severity (P1, P2, P3, P4), status (Open, Resolved, Investigating), title, assigned_to. Returned columns: incident_id, title, severity, status, description, assigned_to, created_date, resolved_date. Use @eq filter on severity to find P1 incidents. Only @eq filters are supported — no @gte, @lte, @gt, @lt. For date questions, include date terms in the query text instead. Do NOT request columns not listed here."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.HR.benefits_server
  FROM SPECIFICATION $$
    tools:
      - name: "benefits-cost-analysis"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.HR.benefits_semantic_view"
        title: "Benefits Cost Analysis"
        description: "Analyze benefits plan costs — employer vs employee costs, enrollment costs by plan type, coverage tier breakdowns, and total benefits spend."

      - name: "enrollment-stats"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.HR.benefits_semantic_view"
        title: "Enrollment Statistics"
        description: "Query benefits enrollment statistics — enrollment counts by plan, coverage tier distribution, employee participation rates."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.HR.org_server
  FROM SPECIFICATION $$
    tools:
      - name: "org-explorer"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.HR.org_semantic_view"
        title: "Org Structure Explorer"
        description: "Explore organizational structure — reporting chains, span of control, department sizing, org depth, and manager hierarchies."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.FINANCE.product_usage_server
  FROM SPECIFICATION $$
    tools:
      - name: "product-analytics"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.FINANCE.product_usage_semantic_view"
        title: "Product Usage Analytics"
        description: "Query product usage metrics — active users, sessions, API calls, revenue, ARR, and churn risk by product, customer, and segment."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.FINANCE.invoice_search_server
  FROM SPECIFICATION $$
    tools:
      - name: "invoice-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "ACME_CORP.FINANCE.invoice_search_svc"
        title: "Invoice Search"
        description: "Search invoices. Searchable text: description. Filterable attributes: vendor_name, invoice_number, department, status (Paid, Pending), category (Cloud Infrastructure, Facilities, Payment Processing, Professional Services, Research, Security, Software). Returned columns: invoice_id, vendor_name, invoice_number, department, amount, status, due_date, description, category, submitted_date. Use @eq filter on vendor_name or status to narrow results. Only @eq filters are supported — no @gte, @lte, @gt, @lt. For date questions, include date terms in the query text instead. Do NOT request columns not listed here."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.FINANCE.spend_approvals_server
  FROM SPECIFICATION $$
    tools:
      - name: "approval-search"
        type: "CORTEX_SEARCH_SERVICE_QUERY"
        identifier: "ACME_CORP.FINANCE.spend_approvals_search_svc"
        title: "Approval Request Search"
        description: "Search spend approval requests. Searchable text: justification. Filterable attributes: requestor, department, category (Advertising, Conference, Consulting, Content, Event, Hardware, Software, Sponsorship, Training), status (Approved, Pending), approver. Returned columns: approval_id, requestor, department, amount, category, justification, status, approver, submitted_date, decided_date. Use @eq filter on status to find pending approvals. Only @eq filters are supported — no @gte, @lte, @gt, @lt. For date questions, include date terms in the query text instead. Do NOT request columns not listed here."

      - name: "spend-analytics"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.FINANCE.spend_semantic_view"
        title: "Spend Analytics"
        description: "Query spend approval analytics — total requested amounts, approval rates, spending by department and category, pending vs approved requests."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.FINANCE.reporting_server
  FROM SPECIFICATION $$
    tools:
      - name: "financial-reporting"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.FINANCE.financial_reports_semantic_view"
        title: "Financial Reporting"
        description: "Query P&L financial reports — revenue, COGS, gross margin, operating expenses, and net income by department and quarter."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

CREATE OR REPLACE MCP SERVER ACME_CORP.IT.infra_monitor_server
  FROM SPECIFICATION $$
    tools:
      - name: "infra-health"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.IT.infra_semantic_view"
        title: "Infrastructure Health"
        description: "Query infrastructure asset health — CPU/memory utilization, asset status, unhealthy nodes, resource capacity by environment and team."

      - name: "sla-compliance"
        type: "CORTEX_ANALYST_MESSAGE"
        identifier: "ACME_CORP.IT.sla_semantic_view"
        title: "SLA Compliance"
        description: "Query SLA compliance — breached vs met SLAs, breach minutes, target vs actual values by service and metric."

      - name: "execute-sql"
        type: "SYSTEM_EXECUTE_SQL"
        title: "Execute SQL"
        description: "Execute SQL queries generated by analyst tools against Snowflake."
  $$;

SELECT 'Internal MCP servers created (10): handbook_comp_server, benefits_server, org_server, budget_server, product_usage_server, invoice_search_server, spend_approvals_server, reporting_server, incident_server, infra_monitor_server' AS status;



-- ============================================================
-- STEP 5: CORTEX AGENTS (MCP Clients)
-- 3 specialized domain agents
-- All tools come through MCP servers — no direct tools on agents.
-- ============================================================

CREATE OR REPLACE AGENT ACME_CORP.HR.hr_agent
  COMMENT = 'HR domain agent — handbook search, compensation, benefits, org structure'
  PROFILE = '{"display_name": "HR Assistant"}'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "claude-sonnet-4-5"},
    "instructions": {
      "orchestration": "You are an HR assistant for Acme Corp. Use handbook_search for policy questions. Use compensation_analyst for salary and headcount questions. Use benefits_cost_analysis or enrollment_stats for benefits questions. Use org_explorer for org structure and reporting chain questions. Present data in markdown tables. Be concise. Never reference charts or visualizations.",
      "sample_questions": [
        {"question": "What is the total employee benefits cost by department?"},
        {"question": "What is the average salary by department?"},
        {"question": "What is the PTO policy?"},
        {"question": "How many employees are in each department?"}
      ]
    },
    "mcp_servers": [
      {"server_spec": {"name": "ACME_CORP.HR.handbook_comp_server"}},
      {"server_spec": {"name": "ACME_CORP.HR.benefits_server"}},
      {"server_spec": {"name": "ACME_CORP.HR.org_server"}}
    ]
  }
  $$;

CREATE OR REPLACE AGENT ACME_CORP.FINANCE.finance_agent
  COMMENT = 'Finance domain agent — budget, product usage, invoices, spend approvals, P&L reporting'
  PROFILE = '{"display_name": "Finance Assistant"}'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "claude-sonnet-4-5"},
    "instructions": {
      "orchestration": "You are a finance assistant for Acme Corp. Use budget_analyst for budget and utilization questions. Use product_analytics for product usage, revenue, ARR, and churn. Use invoice_search for invoice lookups. Use approval_search or spend_analytics for spend approval requests. Use financial_reporting for P&L, revenue, margins, and income statements. Present data in markdown tables with currency formatting. Be concise. Never reference charts or visualizations.",
      "sample_questions": [
        {"question": "Show me all pending invoices and pending spend approval requests. What is the total outstanding amount?"},
        {"question": "What is the gross margin by department for Q1 2025?"},
        {"question": "Which department has the highest budget utilization in Q1 2025?"},
        {"question": "What is total ARR by product in early 2025?"}
      ]
    },
    "mcp_servers": [
      {"server_spec": {"name": "ACME_CORP.FINANCE.budget_server"}},
      {"server_spec": {"name": "ACME_CORP.FINANCE.product_usage_server"}},
      {"server_spec": {"name": "ACME_CORP.FINANCE.invoice_search_server"}},
      {"server_spec": {"name": "ACME_CORP.FINANCE.spend_approvals_server"}},
      {"server_spec": {"name": "ACME_CORP.FINANCE.reporting_server"}}
    ]
  }
  $$;

CREATE OR REPLACE AGENT ACME_CORP.IT.it_agent
  COMMENT = 'IT domain agent — incident search, infrastructure health, SLA compliance'
  PROFILE = '{"display_name": "IT Ops Assistant"}'
  FROM SPECIFICATION $$
  {
    "models": {"orchestration": "claude-sonnet-4-5"},
    "instructions": {
      "orchestration": "You are an IT operations assistant for Acme Corp. Use incident_search for incident and outage questions. Use infra_health for infrastructure asset health and utilization. Use sla_compliance for SLA breach and compliance questions. Present data in markdown tables with severity and status. Be concise. Never reference charts or visualizations.",
      "sample_questions": [
        {"question": "What P1 incidents occurred in March 2025?"},
        {"question": "Which SLAs were breached in Q1 2025?"},
        {"question": "Which infrastructure assets have high CPU utilization?"},
        {"question": "What is the status of the API Gateway?"},
        {"question": "Show me all unresolved incidents in March 2025."}
      ]
    },
    "mcp_servers": [
      {"server_spec": {"name": "ACME_CORP.IT.incident_server"}},
      {"server_spec": {"name": "ACME_CORP.IT.infra_monitor_server"}}
    ]
  }
  $$;

SELECT 'All agents created: hr_agent, finance_agent, it_agent' AS status;

-- ============================================================
-- STEP 6: RBAC ROLES & GRANTS
-- Grant chain: Role -> Agent -> MCP Server -> Tool -> Data
-- ============================================================

CREATE ROLE IF NOT EXISTS hr_analyst_role;
CREATE ROLE IF NOT EXISTS finance_analyst_role;
CREATE ROLE IF NOT EXISTS it_ops_role;

-- Warehouse access
GRANT USAGE ON WAREHOUSE COMPUTE TO ROLE hr_analyst_role;
GRANT USAGE ON WAREHOUSE COMPUTE TO ROLE finance_analyst_role;
GRANT USAGE ON WAREHOUSE COMPUTE TO ROLE it_ops_role;

-- Database access
GRANT USAGE ON DATABASE ACME_CORP TO ROLE hr_analyst_role;
GRANT USAGE ON DATABASE ACME_CORP TO ROLE finance_analyst_role;
GRANT USAGE ON DATABASE ACME_CORP TO ROLE it_ops_role;

-- HR analyst: HR schema + objects
GRANT USAGE ON SCHEMA ACME_CORP.HR TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.employees TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.compensation_bands TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.handbook_docs TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.org_chart TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.benefits_plans TO ROLE hr_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.HR.benefits_enrollments TO ROLE hr_analyst_role;
GRANT USAGE ON CORTEX SEARCH SERVICE ACME_CORP.HR.handbook_search_svc TO ROLE hr_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.HR.comp_semantic_view TO ROLE hr_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.HR.benefits_semantic_view TO ROLE hr_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.HR.org_semantic_view TO ROLE hr_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.HR.handbook_comp_server TO ROLE hr_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.HR.benefits_server TO ROLE hr_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.HR.org_server TO ROLE hr_analyst_role;
GRANT USAGE ON AGENT ACME_CORP.HR.hr_agent TO ROLE hr_analyst_role;

-- Finance analyst: FINANCE schema + objects
GRANT USAGE ON SCHEMA ACME_CORP.FINANCE TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.budgets TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.expenses TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.financial_reports TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.spend_approvals TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.product_usage TO ROLE finance_analyst_role;
GRANT SELECT ON TABLE ACME_CORP.FINANCE.invoices TO ROLE finance_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.FINANCE.budget_semantic_view TO ROLE finance_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.FINANCE.product_usage_semantic_view TO ROLE finance_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.FINANCE.spend_semantic_view TO ROLE finance_analyst_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.FINANCE.financial_reports_semantic_view TO ROLE finance_analyst_role;
GRANT USAGE ON CORTEX SEARCH SERVICE ACME_CORP.FINANCE.invoice_search_svc TO ROLE finance_analyst_role;
GRANT USAGE ON CORTEX SEARCH SERVICE ACME_CORP.FINANCE.spend_approvals_search_svc TO ROLE finance_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.FINANCE.budget_server TO ROLE finance_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.FINANCE.product_usage_server TO ROLE finance_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.FINANCE.invoice_search_server TO ROLE finance_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.FINANCE.spend_approvals_server TO ROLE finance_analyst_role;
GRANT USAGE ON MCP SERVER ACME_CORP.FINANCE.reporting_server TO ROLE finance_analyst_role;
GRANT USAGE ON AGENT ACME_CORP.FINANCE.finance_agent TO ROLE finance_analyst_role;

-- IT ops: IT schema + objects
GRANT USAGE ON SCHEMA ACME_CORP.IT TO ROLE it_ops_role;
GRANT SELECT ON ALL TABLES IN SCHEMA ACME_CORP.IT TO ROLE it_ops_role;
GRANT USAGE ON CORTEX SEARCH SERVICE ACME_CORP.IT.incident_search_svc TO ROLE it_ops_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.IT.infra_semantic_view TO ROLE it_ops_role;
GRANT SELECT ON SEMANTIC VIEW ACME_CORP.IT.sla_semantic_view TO ROLE it_ops_role;
GRANT USAGE ON MCP SERVER ACME_CORP.IT.incident_server TO ROLE it_ops_role;
GRANT USAGE ON MCP SERVER ACME_CORP.IT.infra_monitor_server TO ROLE it_ops_role;
GRANT USAGE ON AGENT ACME_CORP.IT.it_agent TO ROLE it_ops_role;

SELECT 'RBAC roles created: hr_analyst_role, finance_analyst_role, it_ops_role' AS status;
SELECT 'Setup complete! Use Snowflake Intelligence to interact with agents.' AS status;

-- =============================================================================
-- TEARDOWN (uncomment to drop all demo artifacts)
-- =============================================================================
-- USE ROLE ACCOUNTADMIN;
-- USE WAREHOUSE COMPUTE;
--
-- -- RBAC Roles
-- DROP ROLE IF EXISTS it_ops_role;
-- DROP ROLE IF EXISTS finance_analyst_role;
-- DROP ROLE IF EXISTS hr_analyst_role;
--
-- -- Agents
-- DROP AGENT IF EXISTS ACME_CORP.HR.hr_agent;
-- DROP AGENT IF EXISTS ACME_CORP.FINANCE.finance_agent;
-- DROP AGENT IF EXISTS ACME_CORP.IT.it_agent;
--
-- -- MCP Servers
-- DROP MCP SERVER IF EXISTS ACME_CORP.HR.handbook_comp_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.HR.benefits_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.HR.org_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.FINANCE.budget_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.FINANCE.product_usage_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.FINANCE.invoice_search_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.FINANCE.spend_approvals_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.FINANCE.reporting_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.IT.incident_server;
-- DROP MCP SERVER IF EXISTS ACME_CORP.IT.infra_monitor_server;
--
-- -- Semantic Views
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.HR.comp_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.HR.benefits_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.HR.org_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.FINANCE.budget_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.FINANCE.product_usage_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.FINANCE.spend_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.FINANCE.financial_reports_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.IT.infra_semantic_view;
-- DROP SEMANTIC VIEW IF EXISTS ACME_CORP.IT.sla_semantic_view;
--
-- -- Cortex Search Services
-- DROP CORTEX SEARCH SERVICE IF EXISTS ACME_CORP.HR.handbook_search_svc;
-- DROP CORTEX SEARCH SERVICE IF EXISTS ACME_CORP.IT.incident_search_svc;
-- DROP CORTEX SEARCH SERVICE IF EXISTS ACME_CORP.FINANCE.invoice_search_svc;
-- DROP CORTEX SEARCH SERVICE IF EXISTS ACME_CORP.FINANCE.spend_approvals_search_svc;
--
-- -- Note: Also drop any external MCP servers you created:
-- -- DROP EXTERNAL MCP SERVER IF EXISTS ACME_CORP.IT.atlassian_mcp_server;
-- -- DROP EXTERNAL MCP SERVER IF EXISTS ACME_CORP.IT.github_mcp_server;
-- -- DROP EXTERNAL MCP SERVER IF EXISTS ACME_CORP.IT.glean_mcp_server;
-- -- DROP EXTERNAL MCP SERVER IF EXISTS ACME_CORP.IT.linear_mcp_server;
-- -- DROP EXTERNAL MCP SERVER IF EXISTS ACME_CORP.FINANCE.salesforce_mcp_server;
-- -- DROP API INTEGRATION IF EXISTS atlassian_mcp_integration;
-- -- DROP API INTEGRATION IF EXISTS github_mcp_integration;
-- -- DROP API INTEGRATION IF EXISTS glean_mcp_integration;
-- -- DROP API INTEGRATION IF EXISTS linear_mcp_integration;
-- -- DROP API INTEGRATION IF EXISTS salesforce_mcp_integration;
--
-- -- Tables (HR)
-- DROP TABLE IF EXISTS ACME_CORP.HR.employees;
-- DROP TABLE IF EXISTS ACME_CORP.HR.compensation_bands;
-- DROP TABLE IF EXISTS ACME_CORP.HR.handbook_docs;
-- DROP TABLE IF EXISTS ACME_CORP.HR.org_chart;
-- DROP TABLE IF EXISTS ACME_CORP.HR.benefits_plans;
-- DROP TABLE IF EXISTS ACME_CORP.HR.benefits_enrollments;
--
-- -- Tables (Finance)
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.budgets;
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.expenses;
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.financial_reports;
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.spend_approvals;
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.product_usage;
-- DROP TABLE IF EXISTS ACME_CORP.FINANCE.invoices;
--
-- -- Tables (IT)
-- DROP TABLE IF EXISTS ACME_CORP.IT.incidents;
-- DROP TABLE IF EXISTS ACME_CORP.IT.services;
-- DROP TABLE IF EXISTS ACME_CORP.IT.sla_records;
-- DROP TABLE IF EXISTS ACME_CORP.IT.infrastructure_assets;
--
-- -- Schemas & Database
-- DROP SCHEMA IF EXISTS ACME_CORP.HR;
-- DROP SCHEMA IF EXISTS ACME_CORP.FINANCE;
-- DROP SCHEMA IF EXISTS ACME_CORP.IT;
-- DROP DATABASE IF EXISTS ACME_CORP;
--
-- SELECT 'All ACME_CORP demo artifacts dropped.' AS status;
