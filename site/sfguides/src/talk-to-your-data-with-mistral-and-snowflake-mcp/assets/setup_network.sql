-- =============================================================================
-- Network Policy Setup for Mistral MCP Access
-- =============================================================================
-- If your Snowflake account has a network policy enabled, Mistral's servers
-- must be explicitly allowed to reach the MCP Server endpoint.
--
-- This script creates a network rule with known Mistral AI egress IPs and
-- either creates a new network policy or adds the rule to an existing one.
--
-- Run as: ACCOUNTADMIN
--
-- WARNING: The IP ranges below are known Mistral AI egress IPs as of July 2025.
-- These may change without notice. Use at your own risk and verify with Mistral's
-- documentation or support before deploying to production. Monitor your
-- connectivity and update these ranges if Mistral changes their infrastructure.
-- =============================================================================

USE ROLE ACCOUNTADMIN;

-- =============================================================================
-- Step 1: Check if a network policy already exists on your account
-- =============================================================================

SHOW NETWORK POLICIES;

-- If no network policy exists, Mistral can already reach your MCP Server
-- and you can skip this script entirely.

-- =============================================================================
-- Step 2: Create a network rule with Mistral's known egress IPs
-- =============================================================================
-- These are known Mistral AI egress IP ranges (Azure-based + non-Azure).
-- WARNING: These IPs may change. Verify with Mistral's documentation or
-- support team for the latest ranges before production use.

CREATE OR REPLACE NETWORK RULE LOGISTICS_C.SHIPPING_MARTS.MISTRAL_ALLOW_RULE
  TYPE = IPV4
  MODE = INGRESS
  VALUE_LIST = (
    '52.161.104.33',
    '4.223.0.0/16',
    '4.225.0.0/16',
    '20.240.0.0/16',
    '51.12.0.0/16',
    '83.228.144.0/24',
    '135.225.0.0/16'
  )
  COMMENT = 'Mistral AI egress IPs (Azure /16 ranges + non-Azure). Verify with Mistral for latest.';

-- =============================================================================
-- Step 3: Apply the rule to a network policy
-- =============================================================================

CREATE NETWORK POLICY IF NOT EXISTS MISTRAL_NETWORK_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('LOGISTICS_C.SHIPPING_MARTS.MISTRAL_ALLOW_RULE')
  COMMENT = 'Network policy allowing Mistral AI to access Snowflake MCP Server';

-- =============================================================================
-- Step 4: Assign the policy to the MCP user
-- =============================================================================
-- A user-level policy overrides the account-level policy for that user.
-- This means only the IPs in MISTRAL_NETWORK_POLICY will be allowed for this user.
--
-- IMPORTANT: If you also access Snowflake from a VPN or specific IPs, you must
-- add those IPs to MISTRAL_ALLOW_RULE (or create a separate rule and add it to
-- this policy) — otherwise YOUR OWN access will be blocked.

ALTER USER <YOUR_USERNAME> SET NETWORK_POLICY = MISTRAL_NETWORK_POLICY;

-- =============================================================================
-- Step 5: Verify
-- =============================================================================

DESCRIBE NETWORK POLICY MISTRAL_NETWORK_POLICY;
DESCRIBE NETWORK RULE LOGISTICS_C.SHIPPING_MARTS.MISTRAL_ALLOW_RULE;

-- =============================================================================
-- Cleanup (if you need to remove later)
-- =============================================================================
-- ALTER ACCOUNT UNSET NETWORK_POLICY;
-- DROP NETWORK POLICY IF EXISTS MISTRAL_NETWORK_POLICY;
-- DROP NETWORK RULE IF EXISTS LOGISTICS_C.SHIPPING_MARTS.MISTRAL_ALLOW_RULE;
