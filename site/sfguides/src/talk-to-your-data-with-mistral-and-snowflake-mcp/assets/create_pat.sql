-- =============================================================================
-- Programmatic Access Token (PAT) Creation
-- =============================================================================
-- A PAT allows external applications (like Mistral Vibe Chat) to authenticate
-- to Snowflake without interactive login. The PAT inherits the permissions of 
-- the user who creates it, using the role specified at creation time.
--
-- Run as: The user who will own the PAT (must have MCP_USER_ROLE granted)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Step 1: Switch to the role that has MCP access
-- ---------------------------------------------------------------------------

USE ROLE MCP_USER_ROLE;

-- ---------------------------------------------------------------------------
-- Step 2: Create a Programmatic Access Token
-- ---------------------------------------------------------------------------
-- The PAT is scoped to the role active at creation time.
-- Choose an expiry that matches your security requirements.

ALTER USER <YOUR_USERNAME> ADD PROGRAMMATIC ACCESS TOKEN
  TOKEN_NAME = 'mistral_mcp_token'
  COMMENT = 'PAT for Mistral Vibe Chat MCP integration'
  -- DAYS_TO_EXPIRY = 90  -- Optional: days until expiry (default varies by account)
;

-- ---------------------------------------------------------------------------
-- IMPORTANT: Copy the token value immediately!
-- ---------------------------------------------------------------------------
-- The token value is displayed ONLY ONCE after creation. 
-- Store it securely — you will need it when configuring the Mistral connector.
--
-- If you lose the token, you must drop and recreate it:
--   ALTER USER <YOUR_USERNAME> DROP PROGRAMMATIC ACCESS TOKEN TOKEN_NAME = 'mistral_mcp_token';
--   Then re-run Step 2 above.

-- ---------------------------------------------------------------------------
-- Step 3: Verify the token exists
-- ---------------------------------------------------------------------------

SHOW USER PATS;
-- ---------------------------------------------------------------------------
-- Step 4: Test authentication (optional — run from terminal)
-- ---------------------------------------------------------------------------
--
-- Replace <ACCOUNT_URL> and <PAT_TOKEN> with your values.
-- NOTE: If your account URL contains underscores, replace them with hyphens
--       in the hostname (e.g., myorg-my_account -> myorg-my-account).
--       See: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp#mcp-server-security-recommendations
--
--   curl -s -X POST \
--     "https://<ACCOUNT_URL>/api/v2/databases/LOGISTICS_C/schemas/SHIPPING_MARTS/mcp-servers/SHIPPING_MCP_SERVER" \
--     -H "Content-Type: application/json" \
--     -H "Accept: application/json" \
--     -H "Authorization: Bearer <PAT_TOKEN>" \
--     -H "X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN" \
--     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
--
-- Expected: A JSON response listing 3 tools (shipping-logistics-agent, shipment-analytics, shipping-docs-search)
