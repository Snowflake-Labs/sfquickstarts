-- =============================================================================
-- 99: Full Teardown
--
-- Removes ALL objects created by this quickstart:
--   - Agent
--   - Cortex Search service
--   - Semantic view
--   - All tables, UDFs, procedures
--   - Database (SEC_FILINGS)
--   - Warehouse (FILING_WH)
--   - External Access Integration + Network Rule
--
-- Run with ACCOUNTADMIN. This is irreversible.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- Database (drops all tables, views, UDFs, procedures within)
DROP DATABASE IF EXISTS SEC_FILINGS;

-- Warehouse
DROP WAREHOUSE IF EXISTS FILING_WH;

-- External Access Integration + Network Rule
DROP INTEGRATION IF EXISTS SEC_EDGAR_EAI;
-- Note: Network rules are dropped with the database since they live in SEC_FILINGS.FILING_DATA
