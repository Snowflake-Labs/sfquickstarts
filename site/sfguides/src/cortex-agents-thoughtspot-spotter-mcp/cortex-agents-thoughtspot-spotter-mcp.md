author: Ali Alladin
id: cortex-agents-thoughtspot-spotter-mcp
summary: Learn how to integrate Snowflake Cortex Agents into ThoughtSpot Spotter as custom tools using MCP.
categories: snowflake-site:taxonomy/solution/cortex-agents-thoughtspot-spotter, snowflake-site:taxonomy/snowflake-feature/cortex-thoughtspot-mcp
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: Cortex, MCP, ThoughtSpot, AI, Agents, OAuth, Spotter
language: en

# Integrating Snowflake Cortex Agents with ThoughtSpot Spotter via MCP
<!-- ------------------------ -->
## Overview
Duration: 3

This guide walks Snowflake Account Teams through integrating Snowflake Cortex Agents into ThoughtSpot Spotter as custom tools using the **Model Context Protocol (MCP)**. This integration enables ThoughtSpot Spotter to leverage the advanced AI capabilities of Snowflake Cortex Agents for enhanced analytical insights and automated workflows.

### The "Two-Way Street" Architecture

- **Snowflake (MCP Server):** Acts as the **Tool Provider**. It exposes Cortex Agents, Cortex Search, and Analyst services. Snowflake-managed MCP servers currently support tool capabilities only (MCP revision 2025-06-18); they do not support resources, prompts, or roots.
- **ThoughtSpot Spotter (MCP Host):** Acts as the **Tool Consumer**. Spotter invokes the Snowflake-managed tools to retrieve structured and unstructured data, then persists those insights into ThoughtSpot objects.

### Technical Data Flow (OAuth Handshake)

1. **Request:** The user prompts Spotter; Spotter identifies the need for a Snowflake tool.
2. **Handshake:** Spotter redirects the user to Snowflake for OAuth 2.0 authentication.
3. **Token:** Upon success, Snowflake issues an access token to ThoughtSpot.
4. **Execution:** Spotter calls the Snowflake MCP URL with the Bearer token; Snowflake executes the `CORTEX_AGENT_RUN` tool and returns the result.

### Business Value for Snowflake Teams

- **Actionable Liveboards:** Transition from natural language queries to governed, shareable Liveboards in seconds.
- **Zero Infrastructure:** Leverage a Snowflake-managed endpoint without deploying or maintaining middle-tier MCP servers.
- **Governed AI:** Maintain full Snowflake RBAC; the AI agent only sees what the authenticated Snowflake user is permitted to see.

### What You Will Learn

- How to create a Snowflake-managed MCP Server object
- How to configure OAuth security integration for ThoughtSpot
- How to whitelist domains and enable Spotter 3.0 agentic capabilities
- How to register the Snowflake custom connector in ThoughtSpot
- How to generate insights via the Spotter interface

### What You Will Build

An end-to-end integration between Snowflake Cortex Agents and ThoughtSpot Spotter using the Model Context Protocol (MCP), enabling natural language queries against governed Snowflake data from within ThoughtSpot.

<!-- ------------------------ -->
## Prerequisites & Security Requirements
Duration: 5

Before you begin, ensure the following prerequisites are met.

> **⚠️ Important — Hostnames & Naming Conventions:** Snowflake hostnames and MCP object names **must use hyphens (`-`) instead of underscores (`_`)**. MCP connection protocols often fail if the hostname contains underscores.

### Snowflake Configuration

- **Cortex Agent:** A functional Cortex Agent with a defined semantic model and/or search service already created in your Snowflake account.
- **Security Role:** `ACCOUNTADMIN` is required for initial setup. For production, transition to a functional role with `USAGE` on the MCP Server and the specific Cortex Agent.
- **Object Hierarchy:** A dedicated database and schema for housing the MCP Server object.

### ThoughtSpot Configuration

- **Subscription:** Active ThoughtSpot Analytics Enterprise or ThoughtSpot Embedded.
- **User Privileges:** Users must have the **'data download'** privilege assigned within ThoughtSpot to persist Spotter results as Liveboards.
- **Admin Access:** Permissions to modify ThoughtSpot AI settings and **Develop > Security Settings**.

<!-- ------------------------ -->
## Configuring the Snowflake-Managed MCP Server
Duration: 10

In this step, you will create the MCP Server object, the OAuth security integration, and retrieve the client credentials — all within Snowflake.

### Step 3A: Create the MCP Server Object

The Snowflake-managed MCP server requires no separate infrastructure — it is defined entirely through SQL. Navigate to your desired database and schema in Snowsight, then execute the following:

```sql
CREATE OR REPLACE MCP SERVER my_cortex_agent_mcp_server
  FROM SPECIFICATION $$
  tools:
    - name: "my-cortex-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "<database>.<schema>.<cortex_agent_name>"
      description: "My custom Cortex Agent for advanced analytics"
      title: "My Cortex Agent"
  $$
;
```

> **Note:** Replace `<database>`, `<schema>`, and `<cortex_agent_name>` with your specific Snowflake details. The `description` and `title` fields are crucial for tool discovery and understanding by the consuming AI agent (ThoughtSpot Spotter).

### Step 3B: Create the OAuth Security Integration

Run the following SQL to establish the trust relationship. Use `https://oauth.thoughtspot.app/callback` as the mandatory redirect URI:

```sql
CREATE OR REPLACE SECURITY INTEGRATION THOUGHTSPOT_MCP_OAUTH
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://oauth.thoughtspot.app/callback';
```

### Step 3C: Retrieve Client Credentials

Execute the following command to get your credentials:

```sql
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('THOUGHTSPOT_MCP_OAUTH');
```

> **Important:** This returns a JSON string. You **must** parse this string to extract the `OAUTH_CLIENT_ID` and `OAUTH_CLIENT_SECRET`. Save these values — you will need them when registering the connector in ThoughtSpot in Step 5.

<!-- ------------------------ -->
## Security Whitelisting & Spotter 3.0 Enabling
Duration: 5

To ensure the OAuth handshake and tool calls are not blocked by browser security policies, you must configure ThoughtSpot's security headers and enable agentic capabilities.

### Step 4A: Whitelist agent.thoughtspot.app

1. Navigate to **Develop > Customizations > Security Settings**.
2. Click **Edit**.
3. Add `agent.thoughtspot.app` to the **CORS whitelisted domains**.
4. If your organization uses **SAML SSO**, navigate to the **All Orgs** tab (if applicable) and add `agent.thoughtspot.app` to the **SAML redirect domains**.

### Step 4B: Enable Agentic Capabilities

1. Navigate to **Admin settings > ThoughtSpot AI**.
2. Under **Spotter 3 capabilities**, click **Edit**.
3. Set **Enable Connectors/MCP** to **Enabled**.
4. Click **Save**.

> **⚠️ Warning:** Enabling this setting may cause a brief service interruption.

<!-- ------------------------ -->
## Registering the Snowflake Custom Connector
Duration: 5

Register the Snowflake endpoint as a tool provider within the Spotter framework.

1. Navigate to **Admin settings > ThoughtSpot AI > Spotter Connectors**.
2. Click **Edit > Add custom connector**.
3. Fill in the following fields:

| Field | Required Value / Format |
|---|---|
| **Connector Display Name** | e.g., `Snowflake MCP Agent` |
| **MCP URL** | `https://<account_identifier>.snowflakecomputing.com/api/v2/databases/{db}/schemas/{schema}/mcp-servers/{server_name}` |
| **Authentication** | `OAuth` |
| **Client ID** | The ID parsed from Step 3C |
| **Client Secret** | The Secret parsed from Step 3C |

> **Technical Tip:** The `<account_identifier>` should use the Snowflake Account URL format, typically `orgname-accountname`. Remember: **hyphens, not underscores**.

<!-- ------------------------ -->
## Generating Insights via Spotter
Duration: 5

Users interact with the Cortex Agent through the Spotter interface using natural language.

### Using the Integration

1. **Enable Tool:** In the Spotter prompt bar, toggle the **"Snowflake Sales Agent"** connector to **ON**.
2. **OAuth Login:** Click the prompt to authenticate. This generates the secure token Snowflake requires to execute tools.
3. **Natural Language Query:** Ask a question, for example:
   > *"Identify the top 5 regions by revenue growth this year."*
4. **Tool Invocation:** Spotter recognizes the query requires Snowflake data, calls the `CORTEX_AGENT_RUN` tool, and receives the structured result.
5. **Persist Results:** Save the returned insights as a ThoughtSpot **Liveboard** for sharing and governance.

<!-- ------------------------ -->
## Troubleshooting & Best Practices
Duration: 5

### Common Errors

#### 500 Internal Server Error
- Verify the Snowflake warehouse is **not suspended**.
- Ensure the Snowflake account URL or MCP Server name **does not contain underscores**.
- Confirm the ThoughtSpot cluster is up and running.

#### Auth Failures
- Check that `agent.thoughtspot.app` is whitelisted in **both** CORS and SAML redirect settings in ThoughtSpot.
- Re-verify that the Snowflake Security Integration `OAUTH_REDIRECT_URI` **exactly matches** `https://oauth.thoughtspot.app/callback`.

#### Empty Results / Tool Not Found
- Ensure the Snowflake role has `USAGE` on the MCP Server object.
- Ensure the role has `USAGE` on the Cortex Agent.
- If using Cortex Analyst, ensure the role has `SELECT` on the Semantic View.

### Best Practices

- **Version Control:** Ensure your MCP client logic is compatible with MCP revision `2025-06-18`.
- **Node.js Requirements:** If utilizing any local bridge components, ensure **Node.js version 22 or later** is installed on the host machine.
- **Governance:** Periodically audit the Snowflake Security Integration to ensure only authorized redirect URIs are active.
- **Role Separation:** For production deployments, create a dedicated functional role rather than relying on `ACCOUNTADMIN`.

<!-- ------------------------ -->
## Conclusion & Resources
Duration: 2

Congratulations! You have successfully integrated Snowflake Cortex Agents with ThoughtSpot Spotter using the Model Context Protocol (MCP).

### What You Learned

- How to create a Snowflake-managed MCP Server object using SQL
- How to configure an OAuth Security Integration for ThoughtSpot
- How to whitelist domains and enable Spotter 3.0 agentic capabilities
- How to register a Snowflake custom connector in ThoughtSpot Spotter
- How to generate and persist analytical insights using natural language queries

### Related Resources

- [Snowflake Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Snowflake MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/mcp-server)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [ThoughtSpot Spotter Documentation](https://docs.thoughtspot.com/)
- [Snowflake OAuth Security Integrations](https://docs.snowflake.com/en/sql-reference/sql/create-security-integration-oauth)
