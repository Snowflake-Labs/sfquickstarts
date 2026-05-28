author: Ramkumar Chandrasekaran
id: enterprise-cortex-code-governance
summary: Build an enterprise governance layer for Snowflake Cortex Code — manage token credits, model access tiers, and intelligent auto-rebalancing natively inside Snowflake.
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Enterprise CoCo (Cortex Code) Governance on Snowflake

<!-- ------------------------ -->
## Overview
Duration: 5

This quickstart walks you through deploying **CoCo Control Hub** — an enterprise governance application for Snowflake Cortex Code built entirely as a Streamlit-in-Snowflake app.

At enterprise scale, organizations need governance patterns layered on top of Cortex Code's native credit controls: team-level budgets, self-service rebalancing, model access tiers, and immutable audit trails.

CoCo Control Hub provides all of this in a single Streamlit app — no external services, no credentials outside Snowflake, deployable in under 30 minutes.

### What You'll Build
- A 10-page governance application running inside Snowflake
- Cohort-based credit budgets by Snowflake role or user tag
- EWMA-based intelligent credit rebalancing
- Interactive model tier management (TIER_1 / TIER_2 / TIER_3)
- Self-service credit requests with admin approval queue
- Full audit trail and budget forecasting

### Prerequisites
- Snowflake account with ACCOUNTADMIN access (one-time setup only)
- Cortex Code enabled on the account
- Snowflake CLI installed: `curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh`
- Any warehouse (XSMALL sufficient)

### What You'll Learn
- How Snowflake's owner-rights execution model enables safe privilege escalation
- How to build bulk stored procedures that avoid O(N) Python round-trips
- How EWMA prediction improves credit surplus estimation over simple averages
- How TTL-based locking prevents concurrency issues in credit rebalancing

### Source Code
**GitHub:** https://github.com/sfc-gh-rchandrasekaran/snowbox-rchandrasekaran/tree/main/streamlit-apps/cortex-code-credit-manager

<!-- ------------------------ -->
## Architecture
Duration: 5

### The Owner-Rights Execution Model

The most important architectural decision in CoCo Control Hub is Snowflake's **owner-rights model** for Streamlit apps.

When a Streamlit app is owned by a role with elevated privileges, every SQL statement executes as that owner role — not as the end user viewing the app. A developer with no Snowflake admin access can trigger an `ALTER USER` through the app, and the stored procedure validates, executes, and logs it.

```
Streamlit (owned by ACCOUNTADMIN)
    │
    ├── Read queries ──► CC_* tables (direct)
    └── Elevated actions ─► CALL SP (owner-rights)
                                │
                                ├── ALTER USER SET credit limit
                                └── GRANT DATABASE ROLE to user
```

**Three SP classes:**
- **Single-operation SPs** (SQL language) — one validated, atomic action
- **Bulk operation SPs** (Python language) — accept a JSON array, loop server-side
- **Bridge rebalance SP** (Python language) — full EWMA pipeline in one call

### Configurable Deployment

All deployment targets are configured via `config.yaml` — no hardcoded values anywhere in the codebase:

```yaml
deployment:
  database: YOUR_DATABASE
  schema: YOUR_SCHEMA

roles:
  sp_owner: CC_SP_OWNER_ROLE   # or reuse existing elevated role
  app_role: CC_APP_ROLE        # or existing Streamlit runtime role
  admin_role: CC_ADMIN_ROLE
  user_role: CC_USER_ROLE

admin:
  roles:
    - ACCOUNTADMIN
    - YOUR_ADMIN_ROLE
```

<!-- ------------------------ -->
## Setup
Duration: 10

### Step 1: Clone and Configure

```bash
git clone https://github.com/sfc-gh-rchandrasekaran/snowbox-rchandrasekaran.git
cd snowbox-rchandrasekaran/streamlit-apps/cortex-code-credit-manager
```

Edit `config.yaml` with your database and schema:

```yaml
deployment:
  database: YOUR_DATABASE
  schema: YOUR_SCHEMA

admin:
  roles:
    - ACCOUNTADMIN
```

### Step 2: Deploy the Streamlit App

```bash
snow streamlit deploy \
  --connection YOUR_CONNECTION \
  --database YOUR_DATABASE \
  --schema YOUR_SCHEMA
```

### Step 3: In-App Setup

Open the app in Snowsight and navigate to **Setup**:

1. Click **Run Check** — verifies all required objects (tables, SPs, tasks, roles)
2. Click **Create Missing Objects** — runs `prerequisites.sql` and creates all 12 tables, 14 SPs, and 2 tasks
3. Click **Seed Default Settings** — populates `CC_APP_CONFIG` with defaults
4. Click **Run Initial Data Refresh** — backfills 30 days of usage data

<!-- ------------------------ -->
## Cohort Credit Management
Duration: 5

### Setting Team Budgets

Cohort budgets let you govern credit consumption at the team level — by Snowflake role or user tag — rather than managing individuals one by one.

Navigate to **Credit Configuration → Cohort (Role or Tag)** tab:

1. Select **Role** and choose a Snowflake role (e.g., your data engineering team role)
2. Set daily limits for CLI, Snowsight, and Desktop surfaces
3. Choose **Permanent** or **Temporary** (with auto-revert date)
4. Click **Apply to Cohort**

One SP call applies to all members server-side. No O(N) Python round-trips. No browser timeouts.

### User-Level Overrides

Navigate to **Credit Configuration → User Override** to set limits for specific individuals that override their cohort default. Useful for power users or temporary grants.

<!-- ------------------------ -->
## Self-Service Credit Requests
Duration: 5

### How the Intelligence Engine Works

When a user submits a credit request, the system runs a full EWMA surplus analysis inside `SP_CC_COMPUTE_REBALANCE`:

1. Gets cohort members from `CC_USER_COHORT_RESOLVED`
2. Gets current limits via `SHOW PARAMETERS IN USER` (server-side — no Streamlit timeout risk)
3. Gets today's usage in one `GROUP BY` query
4. Gets 14-day hourly history and computes EWMA prediction per hour:

```python
def _ewma(values, alpha=0.3):
    result = values[0]
    for v in values[1:]:
        result = alpha * v + (1 - alpha) * result
    return result
```

5. Applies a 20% safety buffer and day-of-week adjustment
6. Selects donors using a configurable strategy (Weighted Random, Highest Surplus, Minimum Donors, Round Robin)
7. Executes `ALTER USER` changes or queues for admin approval

### Four Donor Strategies

Configure in **Settings → Donor Selection Strategy**:

| Strategy | Behaviour |
|---|---|
| Weighted Random (default) | Probabilistic — same person not always chosen |
| Highest Surplus | Always takes from whoever has the most available |
| Minimum Donors | Prefers a single donor who can cover the full request |
| Round Robin | Rotates — skips donors who donated recently |

<!-- ------------------------ -->
## Model Tier Management
Duration: 5

### Creating Tiers

Navigate to **Model Access → Tier Management**:

1. Click **+ Create New Tier** — enter name, description, token efficiency, and best-for audience
2. Expand an existing tier → click **Edit** → **Manage Models**
3. Each model card shows capabilities, popular use cases, and 30-day credit consumption
4. Click **Add** or **Remove** to assign models to tiers

### Mapping Roles to Tiers

Navigate to **Model Access → Role-Model Mapping**:

1. Select a Snowflake role
2. Use the quick-assign buttons (auto-generated from configured tiers) or multiselect
3. Choose enforcement method: per-user `CORTEX_MODELS_ALLOWLIST`, account-wide, or save only
4. Click **Save & Apply**

<!-- ------------------------ -->
## Access Management
Duration: 5

### Granting Cortex Code Access

Navigate to **Access Management → Grant Access** tab.

Three grant paths:

**Individual Users (Search)** — server-side search against `ACCOUNT_USAGE.USERS`. Works at 50,000+ users without loading them all into the browser.

**Account Role** — recommended for scale. Grants `SNOWFLAKE.CORTEX_USER` and `SNOWFLAKE.COPILOT_USER` to an account role. All current and future members inherit automatically.

**By User Tag** — queries `SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES` to find users with a specific tag value (e.g., `DEPARTMENT = CLINICAL_DS`).

<!-- ------------------------ -->
## Conclusion
Duration: 2

### What You Built

- A fully operational enterprise governance layer for Cortex Code
- Cohort budgets, self-service rebalancing, model tiers, and audit trail — all inside Snowflake
- Owner-rights SP architecture that scales to 50,000+ users without external services

### The Pattern

The governance-as-code approach used in this app is reusable beyond Cortex Code. Snowflake's owner-rights model, stored procedures, and Streamlit-in-Snowflake together provide the right primitives for any governance application that needs to take elevated actions on behalf of unprivileged users.

### Next Steps

- Configure cohort budgets for your teams in **Credit Configuration**
- Assign model tiers in **Model Access**
- Add domain leads in **Settings** for delegated approval
- Review usage patterns in **Usage Trends** and **Audit Log**

### Resources

- **Source Code:** https://github.com/sfc-gh-rchandrasekaran/snowbox-rchandrasekaran/tree/main/streamlit-apps/cortex-code-credit-manager
- **Cortex Code Docs:** https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code
- **Streamlit in Snowflake:** https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit
