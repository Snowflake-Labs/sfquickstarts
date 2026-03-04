-- Snowflake Iceberg V3 Comprehensive Guide
-- Script 08: Network Policy for Streaming Access (Optional)
-- =========================================================
-- 
-- This script creates a network policy to allow inbound connections from
-- your local machine running the streaming script. This may be needed if:
-- - Your organization has restrictive network policies
-- - You're connecting from a VPN
-- - You're getting connection errors from the Python streaming script
--
-- IMPORTANT: Be careful with network policies - they can lock you out!
-- Only run this if you're having connection issues.

USE ROLE ACCOUNTADMIN;

-- ============================================
-- OPTION 1: Auto-detect your current IP (Recommended)
-- ============================================

-- This anonymous block automatically captures your current IP and creates
-- a network rule allowing only that IP address.

DECLARE
    my_ip VARCHAR;
BEGIN
    -- Get the current IP address as seen by Snowflake
    SELECT CURRENT_IP_ADDRESS() INTO :my_ip;
    
    -- Create network rule with the detected IP
    EXECUTE IMMEDIATE '
        CREATE OR REPLACE NETWORK RULE FLEET_STREAMING_NETWORK_RULE
            MODE = INGRESS
            TYPE = IPV4
            VALUE_LIST = (''' || :my_ip || ''')
            COMMENT = ''Network rule for Fleet Analytics streaming - IP: ' || :my_ip || '''
    ';
    
    -- Create network policy using the rule
    EXECUTE IMMEDIATE '
        CREATE OR REPLACE NETWORK POLICY FLEET_STREAMING_POLICY
            ALLOWED_NETWORK_RULE_LIST = (FLEET_STREAMING_NETWORK_RULE)
            COMMENT = ''Network policy for Fleet Analytics streaming script''
    ';
    
    RETURN 'Network rule and policy created for IP: ' || :my_ip;
END;

-- Verify what was created
SELECT 'Your detected IP:' AS info, CURRENT_IP_ADDRESS() AS value
UNION ALL
SELECT 'Network rule created for IP shown above. Policy NOT YET APPLIED.' AS info, '' AS value;

-- ============================================
-- OPTION 2: Allow specific IP ranges (Manual)
-- ============================================
-- If you know your VPN or corporate IP range, uncomment and customize:

-- CREATE OR REPLACE NETWORK RULE FLEET_STREAMING_NETWORK_RULE
--     MODE = INGRESS
--     TYPE = IPV4
--     VALUE_LIST = (
--         '10.0.0.0/8',      -- Private network range
--         '172.16.0.0/12',   -- Private network range  
--         '192.168.0.0/16'   -- Private network range
--     )
--     COMMENT = 'Network rule for private network access';

-- ============================================
-- APPLY THE POLICY (Use with caution!)
-- ============================================
-- 
-- WARNING: Applying a network policy restricts connections to ONLY those
-- matching the policy. Make sure your current IP is included!
--
-- To apply to your user only (safer for testing):
-- SET MY_USER = CURRENT_USER();
-- EXECUTE IMMEDIATE 'ALTER USER ' || $MY_USER || ' SET NETWORK_POLICY = FLEET_STREAMING_POLICY';
--
-- Or manually:
-- ALTER USER <your_username> SET NETWORK_POLICY = FLEET_STREAMING_POLICY;
--
-- To apply account-wide (be very careful!):
-- ALTER ACCOUNT SET NETWORK_POLICY = FLEET_STREAMING_POLICY;

-- ============================================
-- VERIFY SETUP
-- ============================================

SHOW NETWORK POLICIES LIKE 'FLEET%';
SHOW NETWORK RULES LIKE 'FLEET%';

-- ============================================
-- CLEANUP (if needed later)
-- ============================================
-- 
-- To remove the policy from your user:
-- ALTER USER <your_username> UNSET NETWORK_POLICY;
--
-- To remove the policy from the account:
-- ALTER ACCOUNT UNSET NETWORK_POLICY;
--
-- To drop the objects:
-- DROP NETWORK POLICY IF EXISTS FLEET_STREAMING_POLICY;
-- DROP NETWORK RULE IF EXISTS FLEET_STREAMING_NETWORK_RULE;
