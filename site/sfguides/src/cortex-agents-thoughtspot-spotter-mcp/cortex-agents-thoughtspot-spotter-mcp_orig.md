author: Ali Alladin
id: cortex-agents-thoughtspot-spotter-mcp
summary: Use Snowflake Cortex Agents and the managed MCP server to power ThoughtSpot Spotter with agentic analytics on Snowflake data.
categories: getting-started
environments: web
status: Published
language:en
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
tags: quickstart,cortex agents,thoughtspot,spotter,mcp,ai,semantic views

# Connecting Snowflake Cortex Agents to ThoughtSpot Spotter via MCP
<!-- ------------------------ -->
## Overview
Duration: 2

This guide walks through the end-to-end process of configuring Snowflake Cortex Agents as custom tools in ThoughtSpot Spotter using the Model Context Protocol (MCP). The integration enables agentic analytics where Spotter can invoke Cortex Agents mid-conversation to answer complex, multi-step questions against data stored in Snowflake.

**Architecture Overview:** Snowflake hosts a managed MCP server that exposes Cortex Agents as tools. ThoughtSpot Spotter (acting as an MCP Host) connects to that server and invokes those tools during analytical sessions.

### End-to-End Flow

```
Build Semantic View over source tables
           ↓
Build and configure a Cortex Agent
           ↓
Create the Snowflake Managed MCP Server
           ↓
Test with Postman (optional but recommended)
           ↓
Configure ThoughtSpot Spotter MCP Integration
           ↓
Validate end-to-end integration
```

### Prerequisites

- Familiarity with Snowflake SQL and Snowsight UI
- Basic understanding of REST APIs and JSON
- Access to a ThoughtSpot Cloud instance

### What You'll Learn

- How to create a Semantic View to power Cortex Analyst
- How to build and configure a Snowflake Cortex Agent
- How to create and expose a Snowflake-managed MCP server
- How to configure OAuth authentication for secure connectivity
- How to register the MCP server as a custom connector in ThoughtSpot Spotter
- How to test and validate the end-to-end integration

### What You'll Need

- Snowflake account (Enterprise edition or higher)
- `ACCOUNTADMIN` role or a role with `CREATE MCP SERVER` privilege
- Access to Snowsight (Snowflake web UI)
- ThoughtSpot Cloud instance (version 26.3.0.cl or later with Spotter 3 support)
- ThoughtSpot administrator credentials
- Postman (optional, for testing)
- Source data tables in Snowflake to query via agents

### What You'll Build

- A Snowflake Semantic View over your source data tables
- A Snowflake Cortex Agent with Cortex Analyst and/or Cortex Search tools
- A Snowflake-managed MCP server exposing the agent as a callable tool
- A registered custom connector in ThoughtSpot Spotter
- A working agentic analytics integration between Snowflake and ThoughtSpot

<!-- ------------------------ -->
## Create a Semantic View
Duration: 10

If your agent needs to answer structured data questions (e.g. *"What was revenue last quarter?"*), you must first create a Semantic View. This is the metadata layer that teaches Cortex Analyst about your tables, joins, metrics, and business logic.

> aside positive
>
> **Semantic View vs. YAML Semantic Model:** Semantic Views are native Snowflake schema objects with full RBAC support and MCP compatibility. Legacy YAML semantic models work but Semantic Views are strongly recommended for all new setups.

> aside negative
>
> **Skip this step only if** your Cortex Agent will exclusively use Cortex Search (unstructured/document search) and does not need to query structured data tables.

### Option A: AI-Assisted Generation in Snowsight (Recommended)

1. Navigate to **AI & ML → Cortex Analyst** in Snowsight  
2. Click **Create New → Create New Semantic View**  
3. Choose a database and schema to store the Semantic View  
4. Provide a name (e.g. `financial_semantic_view`) and description  
5. Select your source tables (recommended: no more than 10 tables)  
6. Choose relevant columns from each table  
7. Optionally provide example SQL queries to guide the AI  
8. Click **Generate** — Snowflake AI drafts the Semantic View  
9. Review, refine, and click **Save**

### Option B: SQL Definition

```sql
CREATE OR REPLACE SEMANTIC VIEW my_db.my_schema.financial_semantic_view
  TABLES (
    my_db.my_schema.fact_revenue    AS revenue  PRIMARY KEY (transaction_id),
    my_db.my_schema.dim_customer    AS customer PRIMARY KEY (customer_id),
    my_db.my_schema.dim_product     AS product  PRIMARY KEY (product_id)
  )
  RELATIONSHIPS (
    revenue (customer_id) REFERENCES customer (customer_id),
    revenue (product_id)  REFERENCES product  (product_id)
  )
  FACTS (
    revenue.amount AS total_revenue
      SYNONYMS ('revenue', 'sales', 'earnings')
      DESCRIPTION 'Total transaction revenue in USD'
  )
  DIMENSIONS (
    customer.region          AS customer_region,
    product.category         AS product_category,
    revenue.transaction_date AS transaction_date
  )
  METRICS (
    SUM(revenue.amount) AS total_revenue_sum
      DESCRIPTION 'Sum of all revenue across transactions'
  );
```

### Grant Access to the Semantic View

```sql
GRANT SELECT ON SEMANTIC VIEW my_db.my_schema.financial_semantic_view
  TO ROLE analyst_role;
```

<!-- ------------------------ -->
## Build the Cortex Agent
Duration: 10

After creating your Semantic View, create the Cortex Agent that will orchestrate tool calls at query time.

### Step 1: Create the Agent Object

**Option A: Using Snowsight UI (Recommended for first-time setup)**

1. Navigate to **AI & ML → Agents** in Snowsight  
2. Click **Create Agent**  
3. Set the **Agent Object Name** (e.g. `financial_reporting_agent`) — used in SQL and API references  
4. Set the **Display Name** (e.g. *Financial Reporting Assistant*) — shown in the UI  
5. Click **Create Agent**

**Option B: SQL Definition**

```sql
CREATE OR REPLACE AGENT my_db.my_schema.financial_reporting_agent
  COMMENT = 'Agent for financial reporting and forecasting queries'
  PROFILE = '{"display_name": "Financial Reporting Assistant", "color": "blue"}'
  FROM SPECIFICATION $$
  orchestration:
    budget:
      seconds: 30
      tokens: 16000
    instructions:
      response: "Respond concisely and professionally with structured data"
      orchestration: "For revenue queries use Cortex Analyst; for policy questions use Cortex Search"
      system: "You are a financial data assistant specializing in revenue analysis"
    sample_questions:
      - question: "What was total revenue last quarter?"
        answer: "I will analyze the revenue data using our financial database."
      - question: "Show me top performing products by revenue"
        answer: "I will query the product revenue data and present the top performers."
  $$;
```

### Step 2: Add Tools to the Agent

Open your agent in Snowsight and click **Edit → Tools**.

<table>
  <thead>
    <tr>
      <th>Tool Type</th>
      <th>What It Does</th>
      <th>Requires</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>Cortex Analyst</td><td>Text-to-SQL queries against Semantic Views</td><td>Semantic View</td></tr>
    <tr><td>Cortex Search</td><td>Unstructured document and vector search</td><td>Cortex Search Service</td></tr>
    <tr><td>Data to Chart</td><td>Auto-generates visualizations from query results</td><td>None</td></tr>
    <tr><td>Custom Tools</td><td>Stored procedures or UDFs for custom logic</td><td>UDF / Stored Proc</td></tr>
    <tr><td>Web Search</td><td>Live web search capability</td><td>None</td></tr>
  </tbody>
</table>

**Add Cortex Analyst Tool:**

1. Click **+ Add** under Cortex Analyst  
2. Select your Semantic View (e.g. `financial_semantic_view`)  
3. Assign a warehouse for query execution  
4. Set query timeout (recommended: 60 seconds)  
5. Click **Save**

### Step 3: Configure Orchestration

1. Click **Orchestration** in the left pane of the agent editor  
2. Set the **Orchestration Model** (`auto` to start, or `claude-4-sonnet` for advanced reasoning)  
3. Add **Planning Instructions**, for example:  
   - *"For structured data queries about revenue, customers, or products, use Cortex Analyst. For questions about policies or documents, use Cortex Search."*  
4. Add **Response Instructions**, for example:  
   - *"Respond concisely and professionally. Present numerical data in tables when appropriate. Cite your data sources."*  
5. Set execution **Budget** (time and token limits to prevent runaway queries)  
6. Click **Save**

### Step 4: Grant Access and Test

```sql
GRANT USAGE ON AGENT my_db.my_schema.financial_reporting_agent
  TO ROLE analyst_role;

-- Verify agent exists
SHOW AGENTS IN ACCOUNT;
DESCRIBE AGENT my_db.my_schema.financial_reporting_agent;
```

Before proceeding, validate the agent works correctly by testing it in the **Agent Playground** in Snowsight (AI & ML → Agents → select agent → Playground).

> aside negative
>
> **Do not proceed to the next step** until the agent is returning correct, expected results in the Playground. Debugging is much easier at this stage than after wiring up MCP.

<!-- ------------------------ -->
## Create the Snowflake Managed MCP Server
Duration: 8

The Snowflake-managed MCP server requires no separate infrastructure — it is defined entirely in SQL in the same database and schema as your agent.

### Step 1: Create the MCP Server

**Single agent tool:**

```sql
CREATE OR REPLACE MCP SERVER my_cortex_agent_mcp
FROM SPECIFICATION $$
tools:
  - title: "Financial Reporting Agent"
    name: "financial_agent"
    type: "CORTEX_AGENT_RUN"
    identifier: "my_db.my_schema.financial_reporting_agent"
    description: "Agent that answers questions about revenue, expenses, and financial forecasts"
$$;
```

**Multi-tool server (mix and match tool types):**

```sql
CREATE OR REPLACE MCP SERVER analytics_mcp_server
FROM SPECIFICATION $$
tools:
  - name: "product-search"
    type: "CORTEX_SEARCH_SERVICE_QUERY"
    identifier: "my_db.my_schema.product_search_service"
    title: "Product Search"
    description: "Search all product documentation"
  - name: "revenue-analyst"
    type: "CORTEX_ANALYST_MESSAGE"
    identifier: "my_db.my_schema.financial_semantic_view"
    title: "Revenue Analyst"
    description: "Text-to-SQL for financial and revenue analysis"
  - name: "financial_agent"
    type: "CORTEX_AGENT_RUN"
    identifier: "my_db.my_schema.financial_reporting_agent"
    title: "Financial Reporting Agent"
    description: "Multi-step reasoning for financial reporting queries"
$$;
```

<table>
  <thead>
    <tr><th>Tool Type</th><th>Use Case</th></tr>
  </thead>
  <tbody>
    <tr><td><code>CORTEX_AGENT_RUN</code></td><td>Multi-step agent queries with reasoning</td></tr>
    <tr><td><code>CORTEX_ANALYST_MESSAGE</code></td><td>Text-to-SQL on Semantic Views</td></tr>
    <tr><td><code>CORTEX_SEARCH_SERVICE_QUERY</code></td><td>Unstructured and vector search</td></tr>
    <tr><td><code>SYSTEM_EXECUTE_SQL</code></td><td>Direct SQL execution</td></tr>
    <tr><td><code>GENERIC</code></td><td>User-defined functions and stored procedures</td></tr>
  </tbody>
</table>

### Step 2: Verify the MCP Server

```sql
-- List all MCP servers in your schema
SHOW MCP SERVERS IN SCHEMA my_db.my_schema;

-- Describe the server specification
DESCRIBE MCP SERVER my_cortex_agent_mcp;
```

### Step 3: Configure RBAC

> aside negative
>
> **Important:** Access to the MCP server does NOT automatically grant access to its underlying tools. Each object must be granted separately.

```sql
-- Allow a role to connect and discover tools
GRANT USAGE ON MCP SERVER my_db.my_schema.my_cortex_agent_mcp
  TO ROLE analyst_role;

-- Grant access to the Cortex Agent
GRANT USAGE ON AGENT my_db.my_schema.financial_reporting_agent
  TO ROLE analyst_role;

-- If using Cortex Analyst, also grant on the Semantic View
GRANT SELECT ON SEMANTIC VIEW my_db.my_schema.financial_semantic_view
  TO ROLE analyst_role;

-- If using Cortex Search, also grant on the Search Service
GRANT USAGE ON CORTEX SEARCH SERVICE my_db.my_schema.my_search_service
  TO ROLE analyst_role;
```

<table>
  <thead>
    <tr><th>Privilege</th><th>Object</th><th>Purpose</th></tr>
  </thead>
  <tbody>
    <tr><td><code>CREATE</code></td><td>MCP SERVER</td><td>Create the MCP server object</td></tr>
    <tr><td><code>OWNERSHIP</code></td><td>MCP SERVER</td><td>Update server configuration</td></tr>
    <tr><td><code>MODIFY</code></td><td>MCP SERVER</td><td>Drop, describe, or show server details</td></tr>
    <tr><td><code>USAGE</code></td><td>MCP SERVER</td><td>Connect to server and discover tools</td></tr>
    <tr><td><code>USAGE</code></td><td>Cortex Agent</td><td>Invoke the agent as a tool</td></tr>
    <tr><td><code>SELECT</code></td><td>Semantic View</td><td>Invoke Cortex Analyst tool</td></tr>
    <tr><td><code>USAGE</code></td><td>Cortex Search Service</td><td>Invoke search tool</td></tr>
  </tbody>
</table>

### Step 4: Set Up OAuth Authentication

> aside positive
>
> Snowflake strongly recommends OAuth over Personal Access Tokens (PATs) for production use. PATs are fine for testing only.

**For ThoughtSpot (production):**

```sql
CREATE OR REPLACE SECURITY INTEGRATION thoughtspot_mcp_oauth
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://oauth.thoughtspot.app/callback';
```

**For Postman (testing only):**

```sql
CREATE OR REPLACE SECURITY INTEGRATION postman_mcp_oauth
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://oauth.pstmn.io/v1/callback';
```

**Retrieve your client credentials** (integration name must be UPPERCASE):

```sql
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('THOUGHTSPOT_MCP_OAUTH');
```

Save the returned `client_id` and `client_secret` — you will need them in the ThoughtSpot configuration step.

### Step 5: Note Your MCP Server Endpoint

```
https://<account_url>/api/v2/databases/<database>/schemas/<schema>/mcp-servers/<server_name>
```

> aside negative
>
> **Critical:** Use **hyphens** (`-`) not underscores (`_`) in the account URL hostname. Underscore-formatted hostnames cause SSL and 404 connection failures.
>
> ✅ `https://myorg-myaccount.snowflakecomputing.com/...`  
> ❌ `https://myorg_myaccount.snowflakecomputing.com/...`

To find your account URL: Snowsight → profile (bottom left) → **Account** → **View account details**.

<!-- ------------------------ -->
## Test the MCP Server with Postman
Duration: 5

Before configuring ThoughtSpot, verify the MCP server is reachable and returning expected tool responses.

> aside positive
>
> This step is optional but strongly recommended. It isolates any Snowflake-side issues before introducing ThoughtSpot into the debugging surface.

### Step 1: Generate a Test Token

**PAT (quickest for testing):**

1. In Snowsight, click your profile (bottom left)  
2. Navigate to **My Profile → Programmatic Access Tokens**  
3. Click **Generate Token**, set expiry, and copy the value  

> aside positive
>
> **PAT vs Bearer Token:** “Bearer” is the HTTP authentication scheme. A PAT is the actual token value. When you use a PAT in Postman, you send it as a Bearer token: `Authorization: Bearer <your_PAT_value>`

### Step 2: Configure Postman

<table>
  <thead>
    <tr><th>Field</th><th>Value</th></tr>
  </thead>
  <tbody>
    <tr><td>Method</td><td><code>POST</code></td></tr>
    <tr><td>URL</td><td>Your MCP server endpoint from the previous step</td></tr>
    <tr><td>Authorization tab</td><td>Type: Bearer Token → paste PAT value</td></tr>
    <tr><td>Content-Type header</td><td><code>application/json</code></td></tr>
  </tbody>
</table>

### Step 3: Test Tool Discovery

Always run this first to confirm connectivity:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

Expected response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "financial_agent",
        "description": "Agent that answers questions about revenue, expenses, and financial forecasts",
        "inputSchema": {
          "type": "object",
          "properties": {
            "message": { "type": "string" }
          }
        }
      }
    ]
  }
}
```

### Step 4: Test Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "financial_agent",
    "arguments": {
      "message": "What was total revenue last quarter?"
    }
  }
}
```

### Common Errors

<table>
  <thead>
    <tr><th>Error</th><th>Cause</th><th>Resolution</th></tr>
  </thead>
  <tbody>
    <tr><td><code>401 Unauthorized</code></td><td>Token invalid or expired</td><td>Regenerate PAT or refresh OAuth token</td></tr>
    <tr><td><code>403 Forbidden</code></td><td>Role lacks USAGE on MCP server or agent</td><td>Re-run RBAC grants</td></tr>
    <tr><td><code>404 Not Found</code></td><td>Underscores in account hostname</td><td>Replace underscores with hyphens</td></tr>
  </tbody>
</table>

<!-- ------------------------ -->
## Configure ThoughtSpot Spotter
Duration: 8

With the MCP server verified, register it as a custom connector in ThoughtSpot Spotter.

### Step 1: Enable Spotter 3 with MCP Support

1. Log into ThoughtSpot as an administrator  
2. Navigate to **Admin Settings → ThoughtSpot AI**  
3. Under **Spotter 3 capabilities**, click **Edit**  
4. Set **Enable Connectors/MCP** to **Enabled**  
5. Click **Save**

> aside negative
>
> Enabling this feature may cause a brief service interruption (typically under 1 minute). Plan accordingly.

### Step 2: Register the Snowflake MCP Server as a Custom Connector

1. Navigate to **Admin Settings → ThoughtSpot AI → Spotter Connectors**  
2. Click **Edit → Add Custom Connector**  
3. Fill in the connector configuration:

<table>
  <thead>
    <tr><th>Field</th><th>Value</th></tr>
  </thead>
  <tbody>
    <tr><td>Connector Display Name</td><td>e.g., *Snowflake Financial Reporting Agent*</td></tr>
    <tr><td>MCP URL</td><td>Your MCP server endpoint</td></tr>
    <tr><td>Authentication</td><td>OAuth (recommended) or Bearer/PAT</td></tr>
    <tr><td>Client ID</td><td>From <code>SYSTEM$SHOW_OAUTH_CLIENT_SECRETS</code> output</td></tr>
    <tr><td>Client Secret</td><td>From <code>SYSTEM$SHOW_OAUTH_CLIENT_SECRETS</code> output</td></tr>
  </tbody>
</table>

4. Click **Save** to register the connector

> aside positive
>
> Ensure ThoughtSpot's callback URL `https://oauth.thoughtspot.app/callback` is set as the `OAUTH_REDIRECT_URI` in your Snowflake Security Integration.

### Step 3: End-User Activation

Connectors are **not automatically enabled for all users**. Each user must individually activate:

1. Open Spotter in ThoughtSpot  
2. Click the connector toggle or **+** icon in the **Spotter prompt bar**  
3. Select the Snowflake Cortex Agent connector  
4. Complete individual OAuth authentication against Snowflake  
5. Confirm the connection is successful  

After authentication, Spotter will automatically discover and invoke the Cortex Agent tool during multi-step analytical queries.

<!-- ------------------------ -->
## Validate the Integration
Duration: 5

### Test with a Real Query

Ask Spotter a question that requires the Cortex Agent's capabilities:

> *"What were our top 5 revenue-generating products last quarter, and what is the forecasted growth for Q2?"*

Spotter should:

1. Recognize the query requires Snowflake data analysis  
2. Invoke the Cortex Agent tool via MCP  
3. Receive structured results from the agent  
4. Present findings with proper attribution  

### Troubleshooting Guide

<table>
  <thead>
    <tr><th>Issue</th><th>Resolution</th></tr>
  </thead>
  <tbody>
    <tr><td>404 or SSL errors from Spotter</td><td>Verify account URL uses hyphens, not underscores</td></tr>
    <tr><td>Authentication failures</td><td>Confirm OAuth client credentials match security integration output</td></tr>
    <tr><td>Tool not invoked by Spotter</td><td>Check RBAC grants on MCP server and Cortex Agent objects</td></tr>
    <tr><td>Permission denied</td><td>Verify user's default role has USAGE privileges on the agent</td></tr>
    <tr><td>Agent returns incomplete results</td><td>Increase agent budget (seconds/tokens) in orchestration settings</td></tr>
    <tr><td>Semantic View not found</td><td>Verify SELECT grant on Semantic View for the invoking role</td></tr>
  </tbody>
</table>

### Key Limitations

- MCP server supports **tool capabilities only** — no resources, prompts, or streaming responses  
- Non-streaming responses only  
- MCP protocol revision `2025-06-18` only — ensure client versions are aligned  
- No dynamic client registration for OAuth  
- Cortex Analyst only works with **Semantic Views** — legacy YAML semantic models are not supported via MCP  

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 2

Congratulations! You have successfully connected Snowflake Cortex Agents to ThoughtSpot Spotter via MCP. Spotter can now invoke your Cortex Agent as a custom tool, enabling multi-step agentic analytics directly from natural language queries in ThoughtSpot.

### What You Learned

- How to create a Semantic View to power structured data queries  
- How to build, configure, and test a Snowflake Cortex Agent  
- How to expose a Cortex Agent via a Snowflake-managed MCP server  
- How to configure OAuth authentication between Snowflake and ThoughtSpot  
- How to register and activate an MCP connector in ThoughtSpot Spotter  
- How to validate and troubleshoot the end-to-end integration  

### Related Resources

**Official Documentation**

- [Snowflake Semantic Views Documentation](https://docs.snowflake.com/en/user-guide/views-semantic/overview)  
- [Snowflake Cortex Agents Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)  
- [Snowflake Managed MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)  
- [Snowflake Quickstart: Build MCP Server for Cortex Agents](https://www.snowflake.com/en/developers/guides/mcp-server-for-cortex-agents/)  
- [Snowflake Quickstart: Getting Started with Semantic Views](https://www.snowflake.com/en/developers/guides/snowflake-semantic-view/)  
- [ThoughtSpot Spotter Connectors Documentation](https://help-cloud.vercel.app/cloud/26.3.0.cl/spotter-connectors)  
- [ThoughtSpot MCP Integration Guide](https://developers.thoughtspot.com/docs/mcp-integration)  

**GitHub Repositories**

- [Snowflake Cortex Agent MCP Server](https://github.com/Snowflake-Labs/snowflake-cortex-agent-mcp-server)  
- [ThoughtSpot MCP Server](https://github.com/thoughtspot/mcp-server)  
- [Getting Started with Cortex Agents Lab Guide](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-agents)  

**Video Tutorials**

- [ThoughtSpot Agentic MCP Server Demo](https://www.youtube.com/watch?v=kiTpUPzgCbg)  
- [Build Your First AI Agent in Snowflake Intelligence](https://www.youtube.com/watch?v=-OS2RTchbzU)  
