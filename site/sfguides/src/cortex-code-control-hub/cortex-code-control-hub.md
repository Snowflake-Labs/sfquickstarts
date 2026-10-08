author: Ramkumar Chandrasekaran
id: cortex-code-control-hub
language: en
summary: Build an enterprise governance layer for Snowflake Cortex Code — manage token credits, model access tiers, intelligent rebalancing, responsible AI monitoring, and full observability natively inside Snowflake.
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/cortex-code
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Enterprise CoCo (Cortex Code) Governance on Snowflake

<!-- ------------------------ -->
## Overview
Duration: 5

This quickstart walks you through deploying **CoCo Control Hub** — an enterprise governance application for Snowflake Cortex Code built entirely as a Streamlit-in-Snowflake app.

At enterprise scale, organizations need governance patterns layered on top of Cortex Code's native credit controls: team-level budgets, self-service rebalancing, model access tiers, responsible AI monitoring, and immutable audit trails.

CoCo Control Hub provides all of this in a single Streamlit app — no external services, no credentials outside Snowflake, deployable in under 30 minutes.

### What You'll Build
- A 16-page governance application running inside Snowflake
- Cohort-based credit budgets by Snowflake role or user tag
- EWMA-based intelligent credit rebalancing across CLI, Snowsight, and Desktop surfaces
- Interactive model tier management (TIER_1 / TIER_2 / TIER_3)
- Self-service credit requests with admin approval queue
- Responsible AI monitoring with semantic policy insights (PII, security, prompt injection)
- Full session observability — prompts, token economics, cache hit rate
- Budget forecasting and cost attribution
- Native AI Budgets and Cortex AI Guardrails integration
- Full audit trail on every admin action

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
- How to use `AI_OBSERVABILITY_EVENTS` to build session-level analytics
- How to integrate Cortex LLM functions for semantic policy evaluation

### Source Code
**GitHub (Snowflake-Labs):** https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/cortex-code-control-hub/assets/code

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

### Surface Detection

CoCo Control Hub tracks usage across three Cortex Code surfaces. Surface is resolved from `AI_OBSERVABILITY_EVENTS.CODING_AGENT` using a 3-level COALESCE:

```sql
UPPER(COALESCE(
    CASE coding_agent.origin_application
        WHEN 'snowsight'              THEN 'SNOWSIGHT'
        WHEN 'cortex-code-cli'        THEN 'CLI'
        WHEN 'snowflake_coco_desktop' THEN 'DESKTOP'
        ELSE NULL
    END,
    coding_agent.entrypoint,
    CASE coding_agent.client_type
        WHEN 'codingagent_snowsight'  THEN 'SNOWSIGHT'
        WHEN 'codingagent_snova'      THEN 'CLI'
        WHEN 'codingagent_desktop'    THEN 'DESKTOP'
        WHEN 'snowflake_coco_desktop' THEN 'DESKTOP'
        ELSE NULL
    END
)) AS ENTRYPOINT
```

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

### Step 1: Download and Configure

Download the source files from the Snowflake-Labs sfquickstarts repository:

```
https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/cortex-code-control-hub/assets/code
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
2. Click **Create Missing Objects** — runs `prerequisites.sql` and creates all tables, SPs, and tasks
3. Click **Seed Default Settings** — populates `CC_APP_CONFIG` with defaults and seeds policy rules
4. Click **Run Initial Data Refresh** — backfills 30 days of usage data from `AI_OBSERVABILITY_EVENTS`

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
## Observability and Session Analytics
Duration: 5

### Session-Level Visibility

The **Observability** page reads directly from `SNOWFLAKE.ACCOUNT_USAGE.AI_OBSERVABILITY_EVENTS` to provide session-level analytics with zero additional pipelines:

- Every session: prompts sent, tokens used (input/output/cache), estimated credits, entrypoint surface
- Cache hit rate: `cache_read_tokens / (cache_read_tokens + cache_write_tokens)` — indicates how well Prompt Cache is performing
- Token economics: input vs output vs cached token breakdown per session
- Cohort drill-down: filter to any role's members and see their individual session detail

### Usage Trends

The **Usage Trends** page provides time-series analysis across CLI, Snowsight, and Desktop:

- Daily and hourly usage heatmaps (last 7 days by default)
- Credit consumption by surface with consistent color coding
- Peak usage hour identification for capacity planning
- Per-user ranking to identify top consumers and outliers

<!-- ------------------------ -->
## Responsible AI Monitoring
Duration: 5

### Policy Rules and Semantic Evaluation

The **Policy Rules** page lets admins configure semantic evaluation rules that the intelligence engine applies against session prompts. Rules are evaluated using Cortex LLM functions — no regex, no keyword lists.

Default rule categories:

| Category | Example Rule |
|---|---|
| PII_RISK | Detect prompts containing personal identifiers (SSN, credit card, passport numbers) |
| SECURITY | Detect prompts with credentials, API keys, or access tokens |
| PERSONAL_USE | Detect prompts unrelated to software development or data work |
| USAGE_ANOMALY | Detect unusually long sessions relative to the account baseline |
| SECURITY | Detect prompt injection attempts using semantic similarity |

Rules are stored in `CC_POLICY_RULES` and evaluated nightly or on-demand. Admins can add, edit, or toggle any rule from the UI.

### Governance Insights

Navigate to **Governance Insights** to see which sessions triggered policy rules. Admins can:

- Filter by severity (HIGH / MEDIUM / LOW), category, user, or date range
- View the original prompt and the LLM's reasoning for the flag
- Take action (acknowledge, escalate, add to allowlist)
- Export findings for compliance reporting

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

- A fully operational enterprise governance layer for Cortex Code with 16 pages
- Cohort budgets, self-service rebalancing, model tiers, and audit trail — all inside Snowflake
- Owner-rights SP architecture that scales to 50,000+ users without external services
- Semantic responsible AI monitoring powered by Cortex LLM functions
- Full session observability across CLI, Snowsight, and Desktop surfaces

### The Pattern

The governance-as-code approach used in this app is reusable beyond Cortex Code. Snowflake's owner-rights model, stored procedures, and Streamlit-in-Snowflake together provide the right primitives for any governance application that needs to take elevated actions on behalf of unprivileged users.

### Next Steps

- Configure cohort budgets for your teams in **Credit Configuration**
- Assign model tiers in **Model Access**
- Add domain leads in **Settings** for delegated approval
- Review usage patterns in **Usage Trends** and **Audit Log**
- Enable policy rules in **Policy Rules** for responsible AI monitoring

### Resources

- **Source Code (Snowflake-Labs):** https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/cortex-code-control-hub/assets/code
- **Cortex Code Docs:** https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code
- **Streamlit in Snowflake:** https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit
