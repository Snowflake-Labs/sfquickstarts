# Snowflake MCP Server Setup Guide

Reference for creating, securing, and connecting Snowflake MCP servers to external AI clients (Gemini Enterprise, Claude, etc.).

---

## Architecture

```
External AI Client (Gemini Enterprise, etc.)
    │
    │  OAuth 2.0 (confidential client)
    ▼
Snowflake MCP Server  ← GRANT USAGE required for connecting role
    │
    │  tool invocation
    ▼
Cortex Agent  ← GRANT USAGE required for connecting role
    │
    │  text-to-SQL via semantic view
    ▼
Iceberg Table / View
```

Each layer is a separate securable object. The connecting role needs grants on **every layer** it touches.

---

## 1. Create the MCP Server

```sql
CREATE OR REPLACE MCP SERVER <db>.<schema>.<mcp_server_name>
  FROM SPECIFICATION $$
  tools:
    - name: "<tool-name>"
      type: "CORTEX_AGENT_RUN"
      identifier: "<DB>.<SCHEMA>.<AGENT_NAME>"
      description: "<What the tool does — this text is shown to the AI client>"
      title: "<Human-readable title>"
  $$;
```

### Multi-tool example

```sql
CREATE OR REPLACE MCP SERVER analytics_db.public.company_mcp
  FROM SPECIFICATION $$
  tools:
    - name: "finance-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "ANALYTICS_DB.PUBLIC.FINANCE_AGENT"
      description: "Answers questions about revenue, margins, and financial KPIs."
      title: "Finance Agent"
    - name: "hr-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "ANALYTICS_DB.PUBLIC.HR_AGENT"
      description: "Answers questions about headcount, attrition, and compensation."
      title: "HR Agent"
  $$;
```

---

## 2. Grant Access (Critical)

The connecting role must have USAGE on **both** the MCP server and the underlying agent(s). Missing either grant causes silent failures — the client authenticates but sees no tools.

```sql
USE ROLE ACCOUNTADMIN;

-- MCP server grant (without this, tool discovery returns empty)
GRANT USAGE ON MCP SERVER <db>.<schema>.<mcp_server_name> TO ROLE <consumer_role>;

-- Agent grant (without this, tool calls fail with permission error)
GRANT USAGE ON AGENT <db>.<schema>.<agent_name> TO ROLE <consumer_role>;

-- Data grants (agent needs to read the underlying data)
GRANT SELECT ON SEMANTIC VIEW <db>.<schema>.<view> TO ROLE <consumer_role>;
GRANT SELECT ON TABLE <db>.<schema>.<table> TO ROLE <consumer_role>;

-- Warehouse grant (agent needs compute)
GRANT USAGE ON WAREHOUSE <wh> TO ROLE <consumer_role>;

-- Database/schema grants (role needs to resolve object names)
GRANT USAGE ON DATABASE <db> TO ROLE <consumer_role>;
GRANT USAGE ON SCHEMA <db>.<schema> TO ROLE <consumer_role>;
```

### Complete grant checklist

| Object | Grant | Why |
|--------|-------|-----|
| MCP Server | `USAGE` | Client discovers available tools |
| Agent | `USAGE` | Client can invoke the agent |
| Semantic View | `SELECT` | Agent can run text-to-SQL |
| Table/View | `SELECT` | Agent reads underlying data |
| Warehouse | `USAGE` | Agent has compute for queries |
| Database | `USAGE` | Role can resolve the namespace |
| Schema | `USAGE` | Role can resolve the namespace |

---

## 3. OAuth Security Integration

Required for external clients to authenticate via OAuth 2.0.

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE SECURITY INTEGRATION <integration_name>
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = '<client_redirect_uri>'
  ENABLED = TRUE;
```

### Common redirect URIs

| Client | Redirect URI |
|--------|-------------|
| Gemini Enterprise | `https://vertexaisearch.cloud.google.com/oauth-redirect` |
| Custom app | Your app's callback URL |

### Retrieve OAuth credentials

```sql
SELECT PARSE_JSON(SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('<INTEGRATION_NAME>')) AS secrets;
```

---

## 4. MCP Server URL (Use Fully-Qualified)

There are two URL formats. **Always use the fully-qualified format.**

| Format | URL | Behavior |
|--------|-----|----------|
| Generic (unreliable) | `https://<account>.snowflakecomputing.com/api/v2/cortex/mcp` | Requires the role to have broad discovery privileges. Often returns empty tool list. |
| **Fully-qualified (recommended)** | `https://<account>.snowflakecomputing.com/api/v2/databases/<DB>/schemas/<SCHEMA>/mcp-servers/<MCP_NAME>` | Routes directly to the server. Works with minimal grants. |

### Generating the URL dynamically

```sql
SELECT 'https://' || CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
       || '.snowflakecomputing.com/api/v2/databases/'
       || '<DB>' || '/schemas/' || '<SCHEMA>' || '/mcp-servers/' || '<MCP_SERVER_NAME>'
       AS mcp_server_url;
```

---

## 5. Client Registration (Gemini Enterprise)

Output all connection parameters in one query for easy copy-paste:

```sql
WITH secrets AS (
  SELECT PARSE_JSON(SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('<INTEGRATION_NAME>')) AS s
),
account_url AS (
  SELECT 'https://' || CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
         || '.snowflakecomputing.com' AS base
)
SELECT field_name, value
FROM (
  SELECT 1 AS ord, 'MCP Server URL' AS field_name,
    a.base || '/api/v2/databases/<DB>/schemas/<SCHEMA>/mcp-servers/<MCP_NAME>' AS value
    FROM account_url a
  UNION ALL SELECT 2, 'Auth URL', a.base || '/oauth/authorize' FROM account_url a
  UNION ALL SELECT 3, 'Token URL', a.base || '/oauth/token-request' FROM account_url a
  UNION ALL SELECT 4, 'Client ID', s.s:OAUTH_CLIENT_ID::STRING FROM secrets s
  UNION ALL SELECT 5, 'Client Secret', s.s:OAUTH_CLIENT_SECRET::STRING FROM secrets s
  UNION ALL SELECT 6, 'Scopes', 'session:role:<consumer_role>' FROM secrets s
) ORDER BY ord;
```

### Gemini Enterprise steps

1. Google Cloud Console → search "Gemini for Google Cloud" → **Data Connectors** → **Add Connector** → Custom MCP Server
2. Fill in fields from the query output above
3. Complete OAuth authorization when prompted
4. Click **Enable Actions** to activate tools

---

## 6. Troubleshooting

### Gemini authenticates but shows no tools / actions

**Cause:** Missing `GRANT USAGE ON MCP SERVER` to the role specified in the OAuth scope.

```sql
-- Fix
USE ROLE ACCOUNTADMIN;
GRANT USAGE ON MCP SERVER <db>.<schema>.<mcp_name> TO ROLE <consumer_role>;
```

### Tools appear but invocation fails

**Cause:** Missing grant on the agent or underlying data objects.

```sql
-- Check what's missing
GRANT USAGE ON AGENT <db>.<schema>.<agent> TO ROLE <consumer_role>;
GRANT SELECT ON SEMANTIC VIEW <db>.<schema>.<view> TO ROLE <consumer_role>;
GRANT SELECT ON TABLE <db>.<schema>.<table> TO ROLE <consumer_role>;
```

### OAuth errors or timeouts from Gemini

**Cause:** Network policy blocking external IPs.

```sql
-- Temporarily allow all connections (re-enable after testing)
USE ROLE ACCOUNTADMIN;
ALTER ACCOUNT UNSET NETWORK_POLICY;

-- Re-enable:
-- ALTER ACCOUNT SET NETWORK_POLICY = <your_policy_name>;
```

### Google Cloud org policy blocks MCP connectors

**Cause:** `constraints/discoveryengine.managed.disableCustomMcpServerConnector` is enforced.

**Fix:** IAM & Admin → Organization Policies → search `disableCustomMcpServerConnector` → set Enforcement to **Off** → Save.

### Generic URL returns empty tool list even with grants

**Cause:** The account-level `/api/v2/cortex/mcp` endpoint requires discovery privileges beyond simple USAGE.

**Fix:** Switch to the fully-qualified URL format (see section 4).

---

## 7. End-to-End Template

Copy and customize this complete setup:

```sql
-- === SETUP (run as ACCOUNTADMIN) ===
USE ROLE ACCOUNTADMIN;

-- Consumer role for external access
CREATE ROLE IF NOT EXISTS mcp_consumer_role;
GRANT ROLE mcp_consumer_role TO USER <service_user>;

-- Database/schema access
GRANT USAGE ON DATABASE my_db TO ROLE mcp_consumer_role;
GRANT USAGE ON SCHEMA my_db.public TO ROLE mcp_consumer_role;
GRANT USAGE ON WAREHOUSE my_wh TO ROLE mcp_consumer_role;

-- Cortex access
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE mcp_consumer_role;

-- === BUILD (run as builder role) ===
USE ROLE builder_role;

-- Assume agent and semantic view already exist...

-- Create MCP server
CREATE OR REPLACE MCP SERVER my_db.public.my_mcp
  FROM SPECIFICATION $$
  tools:
    - name: "my-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "MY_DB.PUBLIC.MY_AGENT"
      description: "Description of what the agent does."
      title: "My Agent"
  $$;

-- === GRANTS (run as ACCOUNTADMIN) ===
USE ROLE ACCOUNTADMIN;

GRANT USAGE ON MCP SERVER my_db.public.my_mcp TO ROLE mcp_consumer_role;
GRANT USAGE ON AGENT my_db.public.my_agent TO ROLE mcp_consumer_role;
GRANT SELECT ON SEMANTIC VIEW my_db.public.my_view TO ROLE mcp_consumer_role;
GRANT SELECT ON TABLE my_db.public.my_table TO ROLE mcp_consumer_role;

-- OAuth integration
CREATE OR REPLACE SECURITY INTEGRATION my_mcp_oauth
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://vertexaisearch.cloud.google.com/oauth-redirect'
  ENABLED = TRUE;
```

---

## Key Principles

1. **Every securable needs an explicit grant.** MCP server, agent, semantic view, table, warehouse, database, schema — miss one and it silently fails.
2. **Use fully-qualified MCP URLs.** The generic endpoint adds a discovery layer that requires extra privileges and is unreliable with minimal grants.
3. **The OAuth scope determines the role.** `session:role:<role>` in the scope field controls which role the external client assumes. All grants must target that role.
4. **Test with the consumer role first.** Before connecting externally, verify the agent works from within Snowflake using `USE ROLE <consumer_role>` and calling `SNOWFLAKE.CORTEX.DATA_AGENT_RUN`.
