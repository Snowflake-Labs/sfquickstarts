/*=============================================================
  01 — Create Database and Warehouse
  Multi-Agent Orchestrator Demo: Supply Chain Intelligence
=============================================================*/

USE ROLE ACCOUNTADMIN;

-- Create the demo database
CREATE DATABASE IF NOT EXISTS SUPPLY_CHAIN_DEMO;

-- Create a dedicated warehouse (X-Small, auto-suspend after 60s)
CREATE WAREHOUSE IF NOT EXISTS SUPPLY_CHAIN_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND   = 60
  AUTO_RESUME    = TRUE;

-- Set context
USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- Verify
SHOW DATABASES LIKE 'SUPPLY_CHAIN_DEMO';
SHOW WAREHOUSES LIKE 'SUPPLY_CHAIN_WH';
