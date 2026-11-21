-- Set the PRefix for the HOL Accounts (used to run SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT)
-- Us this one for the test trial account
--set acct_prefix='HOL_ACCOUNT';
-- Use this one for the actual HOL ACcounts for Summit 2026
set acct_prefix='SUMMIT_26_DM214';


USE ROLE GLOBALORGADMIN;

CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH INITIALLY_SUSPENDED=TRUE AUTO_SUSPEND=60 WAREHOUSE_SIZE = XSMALL;

USE WAREHOUSE COMPUTE_WH;

-- 01. Sales -------------------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS SALES;

CREATE ORGANIZATION PROFILE SALES
  AS 'title: "Sales"
description: "The Sales business unit drives revenue generation through strategic customer acquisition, relationship management, and pipeline development. Teams identify new opportunities, manage sales cycles, and build lasting client partnerships that contribute to sustained business growth."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:diamond:orange"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;


-- 02. Marketing -------------------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS MARKETING;

CREATE ORGANIZATION PROFILE MARKETING
  AS 'title: "Marketing"
description: "The Marketing business unit develops and executes strategies to build brand awareness, generate demand, and support revenue growth. Activities span digital campaigns, content creation, market research, and customer engagement to position the company competitively across all channels."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:team:pink"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
PUBLISH = TRUE;

-- 03. Supply Chain ------------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS SUPPLYCHAIN;

CREATE ORGANIZATION PROFILE SUPPLYCHAIN
  AS 'title: "Supply Chain"
description: "The Supply Chain business unit manages the end-to-end flow of goods, services, and information from raw material sourcing through final delivery. Teams optimize logistics, inventory management, supplier relationships, and distribution networks to maximize operational efficiency and resilience."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:blocks:aqua"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 04. R&D ---------------------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS RND;

CREATE ORGANIZATION PROFILE RND
  AS 'title: "R&D"
description: "The Research and Development business unit drives innovation by exploring emerging technologies, developing new products, and advancing existing capabilities. Teams conduct experiments, build prototypes, and translate scientific discovery into commercially viable solutions that strengthen competitive advantage."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:healthscience:violet"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 05. Manufacturing -----------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS MANUFACTURING;

CREATE ORGANIZATION PROFILE MANUFACTURING
  AS 'title: "Manufacturing"
description: "The Manufacturing business unit oversees production operations to ensure products are built to specification, on schedule, and within cost targets. Teams manage shop floor processes, equipment maintenance, capacity planning, and lean manufacturing practices to deliver quality output at scale."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:gear:blue"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 06. Quality Assurance -------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS QNA;

CREATE ORGANIZATION PROFILE QNA
  AS 'title: "Quality Assurance"
description: "The Quality Assurance business unit establishes and enforces standards to ensure products, services, and processes meet defined requirements. Teams conduct systematic testing, audits, and continuous improvement initiatives to minimize defects, reduce risk, and maintain high levels of customer satisfaction."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:code:orange"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 07. Corporate Strategy ------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS CORPORATESTRATEGY;

CREATE ORGANIZATION PROFILE CORPORATESTRATEGY
  AS 'title: "Corporate Strategy"
description: "The Corporate Strategy business unit shapes the company long-term direction by analyzing market trends, competitive dynamics, and strategic growth opportunities. Teams define organizational priorities, evaluate mergers and acquisitions, and coordinate cross-functional initiatives to drive sustainable business value."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:classification:pink"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 08. Customer Success --------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS CUSTOMERSUCCESS;

CREATE ORGANIZATION PROFILE CUSTOMERSUCCESS
  AS 'title: "Customer Success"
description: "The Customer Success business unit ensures customers achieve their desired outcomes using the company products and services. Teams manage onboarding, adoption, and retention programs while acting as dedicated customer advocates to drive long-term satisfaction, loyalty, and expansion."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:compute:aqua"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 09. Business Development ----------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS BUSINESSDEVELOPMENT;

CREATE ORGANIZATION PROFILE BUSINESSDEVELOPMENT
  AS 'title: "Business Development"
description: "The Business Development business unit identifies and cultivates new growth opportunities through strategic partnerships, market expansion, and channel development. Teams negotiate business agreements, evaluate new market verticals, and build relationships that extend the company reach and diversify its revenue."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:energy:violet"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 10. Public Relations --------------------------------------------

DROP ORGANIZATION PROFILE IF EXISTS PR;

CREATE ORGANIZATION PROFILE PR
  AS 'title: "Public Relations"
description: "The Public Relations business unit manages the company reputation and external communications with media, analysts, and the public. Teams craft press materials, manage media relationships, coordinate crisis communications, and shape public narrative to protect and enhance the company brand image."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:loudspeaker:blue"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 11. Human Resources ---------------------------------------------

DROP ORGANIZATION PROFILE IF EXISTS HR;

CREATE ORGANIZATION PROFILE HR
  AS 'title: "Human Resources"
description: "The Human Resources business unit manages the full employee lifecycle, including talent acquisition, onboarding, compensation, benefits, performance management, and career development. Teams foster an inclusive workplace culture, support employee wellbeing, and ensure compliance with labor laws and HR policies."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:team:orange"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 12. Information Technology --------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS IT;

CREATE ORGANIZATION PROFILE IT
  AS 'title: "Information Technology"
description: "The Information Technology business unit designs, deploys, and maintains the technology infrastructure and enterprise systems that power business operations. Teams manage cybersecurity, cloud services, application support, and IT service delivery to ensure organizational productivity, reliability, and security."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:dataengineering:pink"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 13. Finance & Accounting ----------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS FINANCE;

CREATE ORGANIZATION PROFILE FINANCE
  AS 'title: "Finance & Accounting"
description: "The Finance and Accounting business unit safeguards the financial health of the organization through budgeting, forecasting, reporting, and compliance. Teams manage accounts payable and receivable, treasury operations, tax planning, and regulatory filings to support accurate financial decision-making."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:book:aqua"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 14. Legal -------------------------------------------------------

DROP ORGANIZATION PROFILE IF EXISTS LEGAL;

CREATE ORGANIZATION PROFILE LEGAL
  AS 'title: "Legal"
description: "The Legal business unit provides strategic counsel on regulatory compliance, contract management, intellectual property protection, and litigation risk. Teams advise business units on governance matters, review commercial agreements, and work proactively to protect the company from legal exposure across all jurisdictions."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:legal:violet"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 15. Compliance & Risk -------------------------------------------

DROP ORGANIZATION PROFILE IF EXISTS COMPLIANCE;

CREATE ORGANIZATION PROFILE COMPLIANCE
  AS 'title: "Compliance & Risk"
description: "The Compliance and Risk business unit identifies, assesses, and mitigates enterprise-wide risks while ensuring adherence to applicable laws, regulations, and internal policies. Teams develop risk frameworks, conduct compliance audits, and promote a culture of accountability and ethical business conduct."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:shieldlock:blue"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 16. Logistics & Distribution ------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS LOGISTICS;

CREATE ORGANIZATION PROFILE LOGISTICS
  AS 'title: "Logistics & Distribution"
description: "The Logistics and Distribution business unit coordinates the movement, storage, and delivery of goods across the supply chain. Teams manage warehousing operations, freight coordination, last-mile delivery, and transportation networks to ensure timely, accurate, and cost-effective product fulfillment."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:transportation:orange"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 17. Procurement -------------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS PROCUREMENT;

CREATE ORGANIZATION PROFILE PROCUREMENT
  AS 'title: "Procurement"
description: "The Procurement business unit sources and acquires the goods and services required for business operations. Teams manage supplier selection, contract negotiation, purchase order workflows, and vendor performance evaluation to optimize cost, quality, and delivery across the entire supply base."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:scale:pink"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 18. Sustainability & ESG ------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS ESG;

CREATE ORGANIZATION PROFILE ESG
  AS 'title: "Sustainability & ESG"
description: "The Sustainability and ESG business unit develops strategies to reduce environmental impact, advance social responsibility, and strengthen governance practices. Teams track ESG performance metrics, manage sustainability reporting, and embed responsible business principles into operations to meet stakeholder expectations."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:environment:aqua"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 19. Facilities Management ---------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS FACILITIES;

CREATE ORGANIZATION PROFILE FACILITIES
  AS 'title: "Facilities Management"
description: "The Facilities Management business unit oversees the physical workplace, infrastructure, and operational services that support the organization. Teams manage building maintenance, space planning, health and safety programs, and vendor services to ensure a productive, safe, and well-functioning work environment."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:pinbuilding:violet"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;

-- 20. Investor Relations ------------------------------------------
DROP ORGANIZATION PROFILE IF EXISTS INVESTORRELATIONS;

CREATE ORGANIZATION PROFILE INVESTORRELATIONS
  AS 'title: "Investor Relations"
description: "The Investor Relations business unit manages communications between the company and its financial stakeholders, including shareholders, analysts, and prospective investors. Teams prepare earnings disclosures, respond to investor inquiries, and ensure transparent reporting of financial performance and strategic outlook."
contact: "dm214_support@maildrop.cc"
approver_contact: "dm214_support@maildrop.cc"
logo: "urn:icon:writinghand:blue"
allowed_publishers:
  access: 
    - all_internal_accounts: "true"'
  PUBLISH = TRUE;



-- Custom Attributes 
DROP INTERNAL MARKETPLACE CONFIG attribute_confidentiality;

CREATE INTERNAL MARKETPLACE CONFIG attribute_confidentiality AS $$
    title: "Confidentiality"
    description: "Confidentiality classification of this data product"
    config_type: "CUSTOM_ATTRIBUTE"
    is_required: true
    props:
      is_filterable: true
      custom_attribute_type: "SINGLE_SELECT"
      allowed_value_definitions:
        - name: Unknown
          display_name: "Unknown"
          status: active
        - name: Public
          display_name: "Public"
          status: active
        - name: Internal
          display_name: "Internal use only"
          status: active
        - name: High
          display_name: "High"
          status: active
        - name: TopSecret
          display_name: "Top Secret"
          status: active
$$;

DROP INTERNAL MARKETPLACE CONFIG attr_source_system;

CREATE INTERNAL MARKETPLACE CONFIG attr_source_system AS $$
        title: "Source Systems"
        description: "Original source of the data"
        config_type: "CUSTOM_ATTRIBUTE"
        is_required: true
        props:
          is_filterable: true
          custom_attribute_type: "MULTI_SELECT"
          allowed_value_definitions:
            - name: SQLServerPayroll
              display_name: "Payroll System"
              status: active
            - name: TreasuryAPI
              display_name: "Treasury API"
              status: active
            - name: TaxLogicDB
              display_name: "Tax Logic DB"
              status: active
            - name: BillingGateway
              display_name: "Billing Gateway"
              status: active
            - name: SalesAndCRM
              display_name: "Sales & CRM Transactions"
              status: active
            - name: SalesforceCRM
              display_name: "Salesforce CRM"
              status: active
            - name: LeadGenSQL
              display_name: "Lead Generation Database"
              status: active
            - name: OrderMgment
              display_name: "Order Management Application"
              status: active
            - name: ChurnPredictor
              display_name: "Churn Predictor"
              status: active
            - name: HumanCapitalManagement
              display_name: "Human Capital Management"
              status: active
            - name: Procurement
              display_name: "Procurement Engine"
              status: active
            - name: LMSCore
              display_name: "LMS Core"
              status: active
            - name: SupplyChainAndLogistics
              display_name: "Supply Chain & Logistics DB"
              status: active
            - name: LogisticsAPI
              display_name: "Logistics API"
              status: active
            - name: FleetIoT
              display_name: "Fleet IoT"
              status: active
            - name: VendorLink
              display_name: "Vendor Link"
              status: active
            - name: MarketingAndCustomerExperience
              display_name: "Marketing & Customer Experience"
              status: active
            - name: SocialMedia
              display_name: "Social Media Analytics"
              status: active
            - name: CampaignEngine
              display_name: "Campaign Engine"
              status: active
            - name: WebAnalytics
              display_name: "Web Analytics"
              status: active
            - name: EnterpriseDataAndRisk
              display_name: "Enterprise Data & Risk"
              status: active
            - name: SnowflakeStaging
              display_name: "Snowflake Staging"
              status: active
            - name: ComplianceDB
              display_name: "Compliance DB"
              status: active
            - name: LegalVault
              display_name: "Legal Vault"
              status: active
    $$;


-- Run Enable Global Data Sharing on all HOL Accounts
USE ROLE GLOBALORGADMIN;
show accounts;
set qid=last_query_id();

EXECUTE IMMEDIATE $$
DECLARE
    -- Enable Global Data Sharing on all accounts
    listing_cursor CURSOR FOR select
                                'SELECT SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT('''||"account_name"||''');' as stmt
                              from table(result_scan($qid))
                              where "account_name" like $acct_prefix||'%';
BEGIN
    FOR record IN listing_cursor DO
        execute immediate record.stmt;
    END FOR;
END;
$$
;




