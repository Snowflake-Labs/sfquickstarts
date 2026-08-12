-- =============================================================================
-- Network Policy Setup for UiPath Orchestrator MCP Access
-- =============================================================================
-- If your Snowflake account has a network policy enabled, UiPath Orchestrator's
-- servers must be explicitly allowed to reach the MCP Server endpoint.
--
-- This script creates a network rule with UiPath Orchestrator egress IPs and
-- either creates a new network policy or adds the rule to an existing one.
--
-- Run as: ACCOUNTADMIN
--
-- IMPORTANT: Get UiPath Orchestrator's outbound IP addresses from:
-- https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/orchestrator-outbound-ip-addresses
--
-- The IP addresses below are for the US region.
-- If you are in a different region (EU, Japan, Australia, etc.), replace with
-- the IPs for YOUR UiPath region from the link above.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- Step 1: Check if a network policy already exists on your account
-- =============================================================================

SHOW NETWORK POLICIES;

-- If no network policy exists, UiPath can already reach your MCP Server
-- and you can skip this script entirely.

-- =============================================================================
-- Step 2: Create a network rule with UiPath Orchestrator's egress IPs
-- =============================================================================
-- The IPs below are for the US region (Enterprise + Delayed update organizations).
-- For other regions, replace with IPs from:
-- https://docs.uipath.com/orchestrator/automation-cloud/latest/user-guide/orchestrator-outbound-ip-addresses

CREATE OR REPLACE NETWORK RULE LOGISTICS_C.SHIPPING_MARTS.UIPATH_ALLOW_RULE
  TYPE = IPV4
  MODE = INGRESS
  VALUE_LIST = (
        -- UiPath MCP Servers — US (primary + secondary)
        '104.211.63.160/30',
        '104.211.58.236/30',
        -- UiPath Orchestrator — US (Enterprise Users)
        '20.124.53.40/30',
        '20.121.182.72/30',
        '20.121.104.124/30',
        '40.114.108.32/30',
        '40.114.108.220/30',
        '20.232.224.12/30',
        '20.66.65.144/30',
        -- UiPath Orchestrator — US (Delayed update organizations)
        '40.114.109.36/30',
        '40.114.109.64/30',   
      )
  COMMENT = 'UiPath Orchestrator egress IPs (US region). Update for other regions per UiPath docs.';

-- =============================================================================
-- Step 3: Apply the rule to a network policy
-- =============================================================================

CREATE NETWORK POLICY IF NOT EXISTS UIPATH_NETWORK_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('LOGISTICS_C.SHIPPING_MARTS.UIPATH_ALLOW_RULE')
  COMMENT = 'Network policy allowing UiPath Orchestrator to access Snowflake MCP Server';

-- =============================================================================
-- Step 4: Assign the policy to the MCP user
-- =============================================================================
-- A user-level policy overrides the account-level policy for that user.
-- This means only the IPs in UIPATH_NETWORK_POLICY will be allowed for this user.
--
-- IMPORTANT: If you also access Snowflake from a VPN or specific IPs, you must
-- add those IPs to UIPATH_ALLOW_RULE (or create a separate rule and add it to
-- this policy) — otherwise YOUR OWN access will be blocked.

ALTER USER <YOUR_USERNAME> SET NETWORK_POLICY = UIPATH_NETWORK_POLICY;

-- =============================================================================
-- Step 5: Verify
-- =============================================================================

DESCRIBE NETWORK POLICY UIPATH_NETWORK_POLICY;
DESCRIBE NETWORK RULE LOGISTICS_C.SHIPPING_MARTS.UIPATH_ALLOW_RULE;

-- =============================================================================
-- Cleanup (if you need to remove later)
-- =============================================================================
-- ALTER USER <YOUR_USERNAME> UNSET NETWORK_POLICY;
-- DROP NETWORK POLICY IF EXISTS UIPATH_NETWORK_POLICY;
-- DROP NETWORK RULE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.UIPATH_ALLOW_RULE;
