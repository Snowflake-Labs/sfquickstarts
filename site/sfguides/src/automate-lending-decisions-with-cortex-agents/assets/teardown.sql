-- Agentic lending lab: teardown
--
-- Removes everything setup.sql created. Run as ACCOUNTADMIN.
--
-- The files in your workspace are yours, not the lab's. Delete them yourself
-- if you no longer want them.

USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS LENDING;
DROP WAREHOUSE IF EXISTS LENDING_WH;
DROP API INTEGRATION IF EXISTS LENDING_GUIDE_GIT_API;
