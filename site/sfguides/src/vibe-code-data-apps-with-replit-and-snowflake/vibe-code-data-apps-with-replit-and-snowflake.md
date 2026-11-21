author: Vino Duraisamy, Manny Bernabe
id: vibe-code-data-apps-with-replit-and-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart
language: en
summary: This QuickStart guides you through connecting Replit to Snowflake so you can start vibe coding data apps using natural language
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Vibe Code Data Apps with Replit and Snowflake

<!-- ------------------------ -->
## Overview

This guide walks you through connecting Replit to Snowflake so you can start vibe coding data apps. Three roles are involved:

1. **Snowflake Account Admin** - Creates the OAuth integration in Snowflake
2. **Replit Workspace Admin** - Configures the connector in Replit
3. **Builder** - Signs in and starts building

### What You'll Learn

- How to create an OAuth security integration in Snowflake
- How to configure the Snowflake connector in Replit
- How to authenticate and connect to your Snowflake data
- How to use Agent to build data apps with natural language

### What You'll Build

In this guide, you will set up the integration between Replit and Snowflake, enabling you to build data applications using natural language prompts. Once connected, you can describe the app you want and Agent builds it—no SQL or code required.

### What is Vibe Coding?

Vibe coding is a new approach to building applications where you describe what you want in plain language and an AI agent builds it for you. With Replit's Agent and Snowflake's data platform, you can:

- Build data dashboards by describing them
- Create interactive visualizations without writing code
- Query and explore your data using natural language

### Prerequisites

- A [Snowflake account](https://signup.snowflake.com/) with `ACCOUNTADMIN` role access
- A Replit Teams or Enterprise plan with Workspace Admin privileges
- Ability to run SQL in Snowflake worksheets
- Basic familiarity with Snowflake

<!-- ------------------------ -->
## Create OAuth Integration

**Who does this:** Snowflake Account Admin (requires ACCOUNTADMIN role)

### Instructions

1. Log into Snowflake and make sure you're using the **ACCOUNTADMIN** role
2. Open **Worksheets** and create a new worksheet
3. Copy and paste this SQL script and run it:

```sql
-- ============================================================================
-- SNOWFLAKE OAUTH INTEGRATION FOR REPLIT
-- ============================================================================

-- Drop existing integration if needed
DROP INTEGRATION IF EXISTS REPLIT_OAUTH;

-- Create OAuth integration for Replit
CREATE SECURITY INTEGRATION REPLIT_OAUTH
  TYPE = OAUTH
  ENABLED = TRUE
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://replit.com/connectors/oauth/callback'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 7776000
  OAUTH_ALLOW_NON_TLS_REDIRECT_URI = FALSE
  BLOCKED_ROLES_LIST = ()
  COMMENT = 'OAuth integration for Replit connector';

-- ============================================================================
-- RETRIEVE OAUTH CREDENTIALS
-- ============================================================================

-- View integration details
DESCRIBE INTEGRATION REPLIT_OAUTH;

-- Get Client ID and Secret
WITH secrets AS (
  SELECT PARSE_JSON(SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('REPLIT_OAUTH')) as creds
)
SELECT
  creds:OAUTH_CLIENT_ID::STRING as CLIENT_ID,
  creds:OAUTH_CLIENT_SECRET::STRING as CLIENT_SECRET
FROM secrets;
```

### Important Notes

| Note | Details |
|------|---------|
| **Redirect URI** | Must be exactly `https://replit.com/connectors/oauth/callback` |
| **Blocked Roles** | `BLOCKED_ROLES_LIST = ()` ensures no roles are blocked. Without this, you may get "Invalid consent request" or "role blocked" errors |

4. Copy the **Client ID** and **Client Secret** from the output. You'll need these for the next step.

<!-- ------------------------ -->
## Configure Replit Connector

**Who does this:** Replit Workspace Admin (Teams or Enterprise plan)

Once configured, anyone on the team can sign in.

### Instructions

1. Go to Replit workspace settings
2. Navigate to **Integrations**
3. Click **Add New Connector** and select **Snowflake**
4. Enter:
   - **Client ID** (from the previous step)
   - **Client Secret** (from the previous step)
5. Set scope to **refresh_token**
6. Save

### Important Note

Only use the `refresh_token` scope. Other scopes like `session:role-any` or `session:role:PUBLIC` may cause an "invalid scope" error.

<!-- ------------------------ -->
## Sign In to Snowflake

**Who does this:** Any team member

We recommend signing in from the Integrations page first to verify the connection before using it with Agent.

### Instructions

1. Go to **Integrations** in Replit
2. Under **Connectors**, find **Snowflake**
3. Click **Sign In**
4. When prompted, enter your **Snowflake Account ID**

### How to Find Your Account ID

Your Snowflake URL looks like `https://app.snowflake.com/kqxkbju/jdb83373`. Take the two parts after `app.snowflake.com/` and join them with a `-` instead of `/`.

| URL Path | Account ID |
|----------|------------|
| `/kqxkbju/jdb83373` | `kqxkbju-jdb83373` |

5. You'll be forwarded to the Snowflake login page. Enter your Snowflake credentials to complete the OAuth flow.

<!-- ------------------------ -->
## Start Vibe Coding

You're connected! Now you can use the Snowflake connector with Agent:

| Method | Description |
|--------|-------------|
| **Slash command** | Type `/snowflake` in the prompt to pull up the connector |
| **Natural language** | Just ask Agent to use your Snowflake data |

### Example Prompt

Once you're connected, just describe what you want in plain language. Here's an example of what a prompt looks like:

```
Build me a Regional Sales Performance Dashboard using my Snowflake data.
I want to see:

1. A map showing our 5 regions (Africa, America, Asia, Europe, Middle East)
   color-coded by performance - green if revenue is growing, red if declining

2. Key numbers at the top: total revenue, total orders, year-over-year change

3. Bar chart comparing revenue across regions

4. Line chart showing revenue trends over time by quarter

5. When I click a region, show me:
   - Top 10 customers in that region
   - Countries in that region with their revenue
   - Order trends for that region

Dark theme. Clean, modern look. Make the charts interactive.
```

No SQL. No code. Just describe the app you want and Agent builds it.

<!-- ------------------------ -->
## Troubleshooting

### "Invalid consent request" or "Role blocked" error

Your Snowflake integration may have roles blocked by default. Make sure your integration was created with `BLOCKED_ROLES_LIST = ()`.

If you've already created the integration without it, you can fix it by running:

```sql
CREATE OR REPLACE SECURITY INTEGRATION REPLIT_OAUTH
  TYPE = OAUTH
  ENABLED = TRUE
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://replit.com/connectors/oauth/callback'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 7776000
  OAUTH_ALLOW_NON_TLS_REDIRECT_URI = FALSE
  BLOCKED_ROLES_LIST = ()
  COMMENT = 'OAuth integration for Replit connector';
```

If the error persists, check that the user's default role isn't blocked:

```sql
-- Set the user's default role to PUBLIC
ALTER USER "YOUR_USERNAME" SET DEFAULT_ROLE = 'PUBLIC';
```

### 404 error on authentication

Check that the redirect URI in your Snowflake integration is exactly:

```
https://replit.com/connectors/oauth/callback
```

### "Invalid scope" error

Make sure the connector scope in Replit is set to `refresh_token` only. Remove any other scopes.

### "Failed to connect" error

Verify that the Client ID and Client Secret in Replit match what Snowflake generated. You can re-check by running:

```sql
WITH secrets AS (
  SELECT PARSE_JSON(SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('REPLIT_OAUTH')) as creds
)
SELECT
  creds:OAUTH_CLIENT_ID::STRING as CLIENT_ID,
  creds:OAUTH_CLIENT_SECRET::STRING as CLIENT_SECRET
FROM secrets;
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully connected Replit to Snowflake for vibe coding data apps. You can now build interactive data applications using natural language prompts.

### What You Learned

- How to create an OAuth security integration in Snowflake for Replit
- How to configure the Snowflake connector in Replit workspace settings
- How to authenticate via OAuth and connect your Snowflake account
- How to use Agent with natural language prompts to build data apps

### Related Resources

- [Snowflake - Configure OAuth for Custom Clients](https://docs.snowflake.com/en/user-guide/oauth-custom)
- [Replit Docs - Warehouse Connectors](https://docs.replit.com/replitai/warehouse-connectors#warehouse-connectors)
