author: Randy Pettus
id: getting-started-with-writer-and-snowflake-mcp-for-campaign-planning
language: en
summary: Connect WRITER to Snowflake MCP to build a campaign planning playbook grounded in customer data with governed write-back.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/snowflake-feature/connectors,snowflake-site:taxonomy/snowflake-feature/cortex-analyst,snowflake-site:taxonomy/snowflake-feature/cortex-search,snowflake-site:taxonomy/snowflake-feature/ingestion/conversational-assistants
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with WRITER and Snowflake MCP for Campaign Planning
<!-- ------------------------ -->
## Overview

[WRITER](https://writer.com) is an enterprise AI platform for agentic marketing and revenue teams. When paired with Snowflake MCP, WRITER enables teams to activate their Snowflake data in every workflow to close the loop from insight to execution. You can learn more about WRITER & Snowflake's integration in this [link](https://writer.com/product/snowflake/).

In this guide you will connect WRITER to Snowflake through a Snowflake-managed MCP server, building a campaign-planning playbook that grounds its recommendations in customer data and saves the finished brief back to Snowflake through a stored procedure you control. We'll create all objects from scratch in this guide, but feel free to skip to the skip to the Connect to WRITER section if you already have an MCP server ready to be used.

By the end you will have a WRITER playbook that asks a Cortex Agent which customer micro-segments to target, finds historical campaign copy that has performed well, drafts a brief, and writes it back to Snowflake — all governed by Snowflake.

### Prerequisites
- A Snowflake account with access to [Cortex AI features](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability) (Cortex Agents, Cortex Search, and Semantic Views)
- `ACCOUNTADMIN`, or a role that can create databases, warehouses, roles, and security integrations
- A WRITER organization with permission to add a custom MCP connector (this may require a WRITER org admin — confirm before you start)
- Basic familiarity with Snowflake and SQL

> **New to Snowflake MCP?** If you haven't set up a Snowflake MCP Server yet, follow [Getting Started with Snowflake MCP Server](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-mcp-server/) to create one with Cortex Analyst and Search tools. For guidance on building Cortex Agents, see [Best Practices to Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/).

### What You'll Learn
- How to create a Cortex Agent with both semantic view and search tools
- How to build a governed write-back path using a stored procedure exposed as an MCP tool
- How to configure OAuth for MCP server authentication
- How to connect WRITER to a Snowflake MCP server and build a playbook
- How to build a playbook in WRITER to enable reusable workflows for your team

### What You'll Need
- A [Snowflake](https://signup.snowflake.com/) account with access to Cortex AI features
- A [WRITER](https://writer.com) organization with MCP connector access
- About 30 minutes

### What You'll Build
- A complete Snowflake environment with customer data, campaign history, a Cortex Agent, and an MCP server
- A WRITER playbook that plans campaigns grounded in Snowflake data and writes briefs back through a governed procedure

The MCP server provide two tools to WRITER:

| Tool | Type | Purpose |
|------|------|---------|
| `campaign-planner` | `CORTEX_AGENT_RUN` | Routes questions to a semantic view (structured) or a Cortex Search service (unstructured). |
| `save-brief` | `GENERIC` (procedure) | Writes a campaign brief to a single table through a governed stored procedure with a fixed signature. |

```
WRITER playbook
  |
  |-- campaign-planner --> WRITER_CAMPAIGN_PLANNER (Cortex Agent)
  |                          |-- CustomerAnalyst --> CUSTOMER_360_SV (semantic view)
  |                          |                        |-- CUSTOMER_360
  |                          |                        |-- MICRO_SEGMENTS
  |                          |-- CampaignSearch  --> CAMPAIGN_LIBRARY_SEARCH
  |                                                   |-- CAMPAIGN_LIBRARY
  |
  |-- save-brief ---------> SAVE_BRIEF (stored procedure)
                              |-- CAMPAIGN_BRIEFS
```

<!-- ------------------------ -->
## Snowflake Setup

This step creates the database, warehouse, role, and all sample data for the quickstart. The full SQL is in [setup_data.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-writer-and-snowflake-mcp-for-campaign-planning/assets/setup_data.sql). Run it in a Snowsight SQL Worksheet as `ACCOUNTADMIN`.

**What it creates:**

| Object | Description |
|--------|-------------|
| `WRITER_SF_QUICKSTART` database | Isolated environment for the quickstart |
| `MARKETING` schema | All tables and AI objects live here |
| `WRITER_QUICKSTART_WH` warehouse | XSMALL, auto-suspend 60s |
| `WRITER_QUICKSTART_ROLE` role | Least-privileged role for MCP access |
| `CUSTOMER_360` table | 5,000 synthetic customer profiles with RFM scoring and churn risk |
| `MICRO_SEGMENTS` table | 42 segment rollups ranked by intent score |
| `CAMPAIGN_LIBRARY` table | 60 historical campaigns with copy, CTAs, and performance metrics |

> In production you would use your own data with the necessary Semantic Views and Cortex Search services. The synthetic data here lets you complete the quickstart without any external dependencies.

**Verify** the setup completed correctly:

```sql
SELECT
  (SELECT COUNT(*) FROM WRITER_SF_QUICKSTART.MARKETING.CUSTOMER_360)   AS customers,
  (SELECT COUNT(*) FROM WRITER_SF_QUICKSTART.MARKETING.MICRO_SEGMENTS) AS segments,
  (SELECT COUNT(*) FROM WRITER_SF_QUICKSTART.MARKETING.CAMPAIGN_LIBRARY) AS campaigns;
```

**Expected:** 5,000 customers, 42 segments, 60 campaigns.

<!-- ------------------------ -->
## Cortex AI Setup

This step creates the Cortex Search service, semantic view, agent, MCP server, write-back procedure, and all grants. The full SQL is in [cortex_setup.sql](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-writer-and-snowflake-mcp-for-campaign-planning/assets/cortex_setup.sql). Run it in a Snowsight SQL Worksheet as `ACCOUNTADMIN`, after `setup_data.sql` has completed.

**What it creates:**

| Object | Type | Purpose |
|--------|------|---------|
| `CAMPAIGN_BRIEFS` | Table | Empty write-back target for campaign briefs |
| `SAVE_BRIEF` | Stored Procedure | Governed write path — upserts briefs via MERGE |
| `CAMPAIGN_LIBRARY_SEARCH` | Cortex Search Service | Semantic search over 60 historical campaigns |
| `CUSTOMER_360_SV` | Semantic View | Text-to-SQL over customer and segment data |
| `WRITER_CAMPAIGN_PLANNER` | Cortex Agent | Routes between the semantic view and search service |
| `WRITER_QUICKSTART_MCP_SERVER` | MCP Server | Exposes `campaign-planner` and `save-brief` tools |

> The Cortex Search service may take 1-5 minutes to finish indexing. Both `indexing_state` and `serving_state` must show `ACTIVE` before the agent can answer campaign-copy questions.

**Verify** the AI objects are ready:

```sql
DESCRIBE MCP SERVER WRITER_SF_QUICKSTART.MARKETING.WRITER_QUICKSTART_MCP_SERVER;
SHOW CORTEX SEARCH SERVICES IN SCHEMA WRITER_SF_QUICKSTART.MARKETING;
```

**Expected:** `DESCRIBE MCP SERVER` shows both tools (`campaign-planner` and `save-brief`). The Search service shows both states as `ACTIVE`.

<!-- ------------------------ -->
## OAuth Configuration

WRITER authenticates to the MCP server with OAuth 2.0. This creates the security integration and retrieves the client credentials you will paste into WRITER. You can find out more about how to connect WRITER to Snowflake in WRITER's [documentation](https://dev.writer.com/connectors/snowflake).

You will need to capture the security integration client ID and secret, and a fully qualified MCP server URL to plug into WRITER in the following section. Make sure the OAUTH_REDIRECT_URI is the same as the value presented in the `Connect via OAuth` screenshot below.

```sql
USE ROLE ACCOUNTADMIN;

CREATE SECURITY INTEGRATION WRITER_QUICKSTART_OAUTH
  TYPE = OAUTH
  OAUTH_CLIENT = CUSTOM
  ENABLED = TRUE
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://app.writer.com/mcp/oauth/callback'
  OAUTH_USE_SECONDARY_ROLES = NONE
  ALLOWED_ROLES_LIST = ('WRITER_QUICKSTART_ROLE')
  COMMENT = 'OAuth integration for the WRITER quickstart MCP connector';

-- Client ID and secret for WRITER. Treat these as credentials.
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('WRITER_QUICKSTART_OAUTH');

-- Your MCP server URL
SELECT 'https://'
  || LOWER(CURRENT_ORGANIZATION_NAME()) || '-' || LOWER(CURRENT_ACCOUNT_NAME())
  || '.snowflakecomputing.com'
  || '/api/v2/databases/WRITER_SF_QUICKSTART/schemas/MARKETING'
  || '/mcp-servers/WRITER_QUICKSTART_MCP_SERVER' AS mcp_server_url;
```

**Expected:** A client ID and secret, and a fully qualified MCP server URL. Keep both for the WRITER connection step.

> If your account identifier contains underscores, replace them with hyphens in the hostname. Some MCP clients fail to connect to hostnames with underscores. This applies to the hostname only — database, schema, and server names in the path retain their original underscores.

<!-- ------------------------ -->
## Role Setup

For simplicity, in this quickstart we'll update your  `DEFAULT_ROLE` to be the `WRITER_QUICKSTART_ROLE`. For more information on role behavior with OAuth sessions and Snowflake MCP, see [Snowflake documenatation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp#role-behavior-in-oauth-sessions).

```sql
USE ROLE ACCOUNTADMIN;

-- Check your current defaults (note them so you can restore later)
DESCRIBE USER <your_username>;

ALTER USER <your_username>
  SET DEFAULT_ROLE      = 'WRITER_QUICKSTART_ROLE'
      DEFAULT_WAREHOUSE = 'WRITER_QUICKSTART_WH';
```


<!-- ------------------------ -->
## Connect WRITER

Now the WRITER admin will need to add a new connector in WRITER. Open up WRITER AI Studio and navigate to `Connectors & tools`>`Connectors`. 

Then select `+ New connector`.

![WRITER NEW Connector](assets/new_connector.png)

Find the **Snowflake** connector and click `Configure`.

![Configure the Snowflake Connector](assets/configure_snowflake.png)

You will need to add a profile name (`Snowflake Cortex connection`) and description (`Connects to your Snowflake data`). Then select `All teams` and click `Next`.

![Set connector profile values](assets/snowflake_profile.png)

Now select the default settings in the `Configure Snowflake` screen and click `Next`.

![Select OAuth configuration](assets/configure_oauth1.png)

Now you will need the following values from the OAuth Configuration steps above:

| Field | Value |
|-------|-------|
| Client ID | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS` |
| Client secret | From `SYSTEM$SHOW_OAUTH_CLIENT_SECRETS` |
| Tenant URL | The `mcp_server_url` from the OAuth step |

Select `Client Secret` on the menu. Then enter the Client ID, Client Secret, and the Server URL as captured above.
![Connect via OAuth](assets/configure_oauth2.png)

WRITER will open a browser window for the Snowflake OAuth consent screen. Sign in with your Snowflake user and approve.

After connecting, WRITER should discover **two** tools: `campaign-planner` and `save-brief`.

You are now finished with the connection steps and are ready to use Snowflake with WRITER.

<!-- ------------------------ -->
## Build the Playbook

### Create the playbook

Now we are ready to build a playbook in WRITER that uses the Snowflake Connector. 

While in WRITER, click on **Playbooks**. Once in the playbooks screen, select `+ New playbook`.
![Select Playbooks](assets/writer_menu_playbook.png)

**Add one variable:**

| Key | Type |
|-----|------|
| `Campaign__Topic` | text |

**Paste this as the agent prompt:**

```
### Instructions

You are planning a marketing campaign for Apex Athletics, a B2B activewear company.
The campaign topic is [w-var](Campaign__Topic).

**Step 1 — Find the audience**

Ask [w-connector](SNOWFLAKE) using campaign-planner:
"Which 3 micro-segments should we target for a campaign about <topic>? For each, give
the segment name, customer count, average LTV, intent score, and churn risk tier."

**Step 2 — Find what has worked**

Ask [w-connector](SNOWFLAKE) using campaign-planner:
"What historical campaign copy has performed well for these segments and for the topic
<topic>? Include subject lines, CTAs, tone, and conversion rates."

**Step 3 — Draft the brief**

Write a campaign brief grounded only in what came back from Snowflake. Do not invent
segment names, metrics, or campaign history. Include:
- Campaign name and a one-line objective
- The 3 target segments with their metrics and a sentence on why each fits
- Recommended channels, with a rationale referencing historical performance
- Three subject line options in the tone that performed best
- Success metrics, using the historical conversion rates as the baseline
- Any assumptions or open questions

**Step 4 — Save it to Snowflake**

Call the save-brief tool on [w-connector](SNOWFLAKE) with:
- P_CAMPAIGN_ID: a new identifier in the form CMP-2026-NNN
- P_BRIEF_JSON: the complete brief as a JSON string, including brief_id, status
  ("draft"), created_by ("WRITER playbook"), title, and a section for each part of
  the brief above

Report the returned BRIEF_ID and the table it was written to.
```

Run it with a topic such as `winter running gear` or `win back lapsed customers`.

![WRITER playbook builder](assets/writer-playbook-builder.png)

![Playbook running against Snowflake MCP](assets/writer-playbook-running.png)

<!-- ------------------------ -->
## Verify Write-Back

Back in Snowflake, confirm the brief landed:

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE WRITER_SF_QUICKSTART;
USE SCHEMA MARKETING;
USE WAREHOUSE WRITER_QUICKSTART_WH;

SELECT
  BRIEF_ID,
  CAMPAIGN_ID,
  STATUS,
  CREATED_BY,
  CREATED_AT,
  BRIEF_CONTENT:title::VARCHAR AS title
FROM CAMPAIGN_BRIEFS;

-- Full brief content
SELECT BRIEF_CONTENT
FROM CAMPAIGN_BRIEFS
ORDER BY CREATED_AT DESC
LIMIT 1;
```

**Expected:** One row. `CREATED_BY` reflects the value from the playbook prompt. `BRIEF_CONTENT` holds the brief WRITER wrote, with its structure intact.

![Campaign brief result in Snowflake](assets/snowflake-brief-result.png)

Run the playbook again with the same `P_CAMPAIGN_ID` and `brief_id` — the row count stays at 1 because the `MERGE` updates rather than duplicates.

<!-- ------------------------ -->
## Conclusion And Resources

You have connected WRITER to Snowflake through an MCP server with two governed tools: a Cortex Agent for reading customer intelligence, and a stored procedure for writing campaign briefs. The integration is built on least-privileged roles, OAuth, and a fixed procedure contract that defines exactly what WRITER can do in Snowflake.

### What You Learned
- How to build a Cortex Agent that routes between a semantic view and a Cortex Search service
- How to create a governed write-back path using a stored procedure exposed as an MCP tool
- How to configure OAuth for Snowflake MCP server authentication
- How WRITER discovers tool contracts through MCP `tools/list` — no hardcoded signatures needed
- How to build a WRITER playbook that grounds content in Snowflake data and writes results back

### Cleanup

Run the teardown to remove all objects created by this guide:

```sql
USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS WRITER_SF_QUICKSTART;
DROP WAREHOUSE IF EXISTS WRITER_QUICKSTART_WH;
DROP SECURITY INTEGRATION IF EXISTS WRITER_QUICKSTART_OAUTH;
DROP ROLE IF EXISTS WRITER_QUICKSTART_ROLE;

-- Restore your original default role and warehouse:
-- ALTER USER <your_username>
--   SET DEFAULT_ROLE = '<original_role>' DEFAULT_WAREHOUSE = '<original_warehouse>';

-- Confirm nothing is left
SHOW DATABASES LIKE 'WRITER_SF_QUICKSTART';
SHOW WAREHOUSES LIKE 'WRITER_QUICKSTART_WH';
SHOW ROLES LIKE 'WRITER_QUICKSTART_ROLE';
SHOW INTEGRATIONS LIKE 'WRITER_QUICKSTART_OAUTH';
```

Also remove the connector in WRITER, since its credentials no longer resolve.

### Troubleshooting

| Symptom | Likely Cause | Check |
|---------|-------------|-------|
| WRITER connects, no tools appear | Default role lacks USAGE on MCP server | `SHOW GRANTS TO ROLE WRITER_QUICKSTART_ROLE` |
| Tools appear but fail on invocation | Tool-level grants missing | Confirm AGENT, SEMANTIC_VIEW, SEARCH, PROCEDURE grants |
| Agent says table "does not exist" | Table rebuilt after grants ran | Re-run grants from Write-Back Contract step |
| Session fails to initialize | No DEFAULT_WAREHOUSE on user | `SHOW USERS LIKE '<you>'` |
| Wrong data or none visible | Default role is not WRITER_QUICKSTART_ROLE | Check `default_role` in SHOW USERS |
| OAuth consent fails | Redirect URI mismatch | `DESCRIBE INTEGRATION WRITER_QUICKSTART_OAUTH` |
| Hostname connection failure | Underscores in account hostname | Use hyphens in hostname only |
| Agent returns nothing for copy questions | Search still indexing | `SHOW CORTEX SEARCH SERVICES` — both states must be ACTIVE |
| Second save fails | Missing UPDATE on CAMPAIGN_BRIEFS | Check grants include UPDATE |

### Related Resources
- [Building a Marketing Content Supply Chain Flywheel with WRITER & Snowflake Technical Blog](https://medium.com/snowflake/building-a-marketing-content-supply-chain-flywheel-with-writer-snowflake-cb13d76641ad)
- [WRITER + Snowflake](https://writer.com/product/snowflake/)
- [Getting Started with Snowflake MCP Server](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-mcp-server/)
- [Best Practices to Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/)
- [Snowflake MCP Server Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Snowflake Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [WRITER - Snowflake Connector Documentation](https://dev.writer.com/connectors/snowflake)

### Next Steps
- **Extend to the full content supply chain.** Add a `save-asset` tool for copy and an `activate-segment` tool for audience delivery — both follow the same `GENERIC` procedure pattern as `save-brief`.
- **Dynamic Tables.** Rebuild `CUSTOMER_360` as a Dynamic Table over a real event stream with `TARGET_LAG`, so segments stay current automatically.
- **Index the briefs.** Add a Cortex Search service over `CAMPAIGN_BRIEFS` so each campaign can learn from the ones before it.
