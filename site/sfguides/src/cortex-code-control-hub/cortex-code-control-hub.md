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
- An 18-page governance application running inside Snowflake
- Cohort-based credit budgets by Snowflake role or user tag
- EWMA-based intelligent credit rebalancing across CLI, Snowsight, and Desktop surfaces
- Interactive model tier management (TIER_1 / TIER_2 / TIER_3)
- Self-service credit requests with admin approval queue
- Responsible AI monitoring with semantic policy insights (PII, security, prompt injection)
- Full session observability — prompts, token economics, cache hit rate
- Budget forecasting and cost attribution
- Native AI Budgets and Cortex AI Guardrails integration
- Native per-user quotas (`SNOWFLAKE.CORE.QUOTA`) for hard enforcement
- Full audit trail on every admin action

### Prerequisites
- Snowflake account with ACCOUNTADMIN access (for initial setup, and to own the app while Setup Phases A and C run — on install and on every upgrade)
- Cortex Code enabled on the account
- **Snowflake CLI** (`snow`) installed — the deploy step runs `snow streamlit deploy`. See [Installing Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation).
- **Cortex Code CLI** (optional, for the AI-assisted deploy in `GETTING_STARTED.md`): `curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh`
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

CoCo Control Hub tracks usage across three Cortex Code surfaces. Surface is resolved from the span attributes in `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` — `RECORD_ATTRIBUTES['snow.ai.observability.agent.coding_agent.origin_application']`, then `...coding_agent.entrypoint`, then `...coding_agent.client_type` — using a 3-level COALESCE (shorthand below; `coding_agent.x` means `RECORD_ATTRIBUTES['snow.ai.observability.agent.coding_agent.x']`):

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
  sp_owner: CC_SP_OWNER_ROLE   # or reuse existing elevated role (credit-limit SPs still stay ACCOUNTADMIN-owned)
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

Edit `config.yaml` with your database and schema, and replace the `MY_DATABASE` / `MY_SCHEMA` / `MY_WAREHOUSE` placeholders in `snowflake.yml`:

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
snow streamlit deploy --connection YOUR_CONNECTION
```

Make sure the app is owned by ACCOUNTADMIN before running Setup (Setup runs as the app owner):

```sql
SHOW STREAMLITS IN SCHEMA YOUR_DATABASE.YOUR_SCHEMA;   -- "owner" column
GRANT OWNERSHIP ON STREAMLIT YOUR_DATABASE.YOUR_SCHEMA.CORTEX_CODE_CREDIT_MANAGER
  TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS;
```

### Step 3: In-App Setup

Open the app in Snowsight and navigate to **Setup**:

1. **Account Prerequisites** — run the 7 SQL blocks shown on the page in a worksheet as ACCOUNTADMIN (cross-region inference, `AI_OBSERVABILITY_READER` application role, ACCOUNT_USAGE access, Cortex roles for users, and optional limits, guardrails and budgets)
2. **Phase A — Create Objects** — runs `prerequisites.sql` (roles, tables, tasks, alerts, stream, email integration, core SPs), creates the bulk/rebalance/model-access SPs, and grants SP USAGE to the app and SP owner roles
3. **Phase B — Seed Defaults** — populates `CC_APP_CONFIG` and policy rules
4. **Phase C — Create Stored Procedures** — classification, alerting, evaluation, budget and quota SPs
5. **Phase D — Initial Data Load** — backfills usage summaries and prompt events
6. **Phase E — Verify** — every object, credit-limit SP ownership, and the temporary-limit columns must be green

Phases A and C must run with the app owned by ACCOUNTADMIN — the credit-limit SPs only work when ACCOUNTADMIN owns them. The Setup page warns if it is not.

<!-- ------------------------ -->
## Cohort Credit Management
Duration: 5

### Setting Team Budgets

Cohort budgets let you govern credit consumption at the team level — by Snowflake role or user tag — rather than managing individuals one by one.

Navigate to **Credit Configuration → Cohort (Role or Tag)** tab:

1. Select **Role** and choose a Snowflake role (e.g., your data engineering team role) — or enter a pattern such as `ENG_*` to create one cohort per matching role
2. Set daily limits for CLI, Snowsight, and Desktop surfaces
3. Choose **Permanent** or **Temporary** (with an end date — the hourly `CC_EXPIRE_TEMPORARY_CREDITS` task restores the previous limits after it)
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

The **Observability** page reads from `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` (via the nightly `CC_PROMPT_EVENTS` table) to provide session-level analytics with zero additional pipelines:

- Every session: prompts sent, tokens used (input/output/cache), estimated credits, entrypoint surface
- Cache hit rate: `cache_read_tokens / (cache_read_tokens + cache_write_tokens)` — indicates how well Prompt Cache is performing
- Token economics: input vs output vs cached token breakdown per session
- Cohort drill-down: filter to any role's members and see their individual session detail

> **Source of truth for credits:** Snowflake delivers AI observability trace data on a best-effort basis, so credit figures derived from it are **estimates**. The `ACCOUNT_USAGE` usage-history views are authoritative for billed credits; the **Usage Trends** and **Cost Attribution** pages use them.

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
3. Choose enforcement method (model RBAC — grants `SNOWFLAKE."CORTEX-MODEL-ROLE-*"` application roles):
   - **Role Directly** (recommended) — grants the model application roles to the role; all current and future members inherit them
   - **Role Members** — per-user model RBAC: grants the model application roles to each current member individually
   - **Save mapping only** — record the mapping and enforce later

   There is no account-wide option: the `CORTEX_MODELS_ALLOWLIST` account parameter is being retired by [BCR-2378](https://docs.snowflake.com/en/release-notes/bcr-bundles/2026_07/bcr-2378) (2026_07 bundle, generally enabled January 2027).
4. Click **Save & Apply**

<!-- ------------------------ -->
## Access Management
Duration: 5

### Granting Cortex Code Access

Navigate to **Access Management → Grant Access** tab.

Three grant paths:

**Individual Users (Search)** — server-side search against `ACCOUNT_USAGE.USERS`. Works at 50,000+ users without loading them all into the browser.

**Account Role** — recommended for scale. Grants the Cortex database roles to an account role. All current and future members inherit automatically.

Database roles offered on every path:

- `SNOWFLAKE.CORTEX_USER` — full Cortex access, including Cortex Code
- `SNOWFLAKE.CORTEX_AGENT_USER` — least-privilege alternative for Cortex Code (agent features only)
- `SNOWFLAKE.COPILOT_USER` — **transitional**. CoCo in Snowsight requires it only until [BCR-2445](https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/bcr-2445) reaches your account (rolling out from October 2026); after that, granting or revoking it has no effect on CoCo.

**By User Tag** — queries `SNOWFLAKE.ACCOUNT_USAGE.TAG_REFERENCES` to find users with a specific tag value (e.g., `DEPARTMENT = DATA_SCIENCE`).

<!-- ------------------------ -->
## Upgrading an Existing Installation
Duration: 5

This release adds temporary-limit expiry, new security checks on the privileged stored procedures, and keeps the credit-limit stored procedures owned by ACCOUNTADMIN. **Run Phases A and C after updating.**

1. Get the latest code from `assets/code/` and keep your own values in `config.yaml` and `snowflake.yml` (database, schema, warehouse, admin roles).
2. Redeploy the app: `snow streamlit deploy --replace --connection <your_connection>`
3. Make sure the app is **owned by ACCOUNTADMIN** — Setup runs as the app owner, and the credit-limit SPs only work when ACCOUNTADMIN owns them:
   ```sql
   SHOW STREAMLITS IN SCHEMA <db>.<schema>;   -- check the "owner" column
   GRANT OWNERSHIP ON STREAMLIT <db>.<schema>.CORTEX_CODE_CREDIT_MANAGER TO ROLE ACCOUNTADMIN COPY CURRENT GRANTS;
   ```
4. If not done before, grant AI Observability access (it is an **application** role):
   `GRANT APPLICATION ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE;`
5. Open the app → **Setup** → run **Phase A**. It is idempotent: it adds the temporary-limit columns to `CC_CREDIT_CONFIG`, creates the hourly `CC_EXPIRE_TEMPORARY_CREDITS` task, recreates the SPs, re-applies USAGE grants, and resumes alerts and the budget refresh task if they were running.
6. Run **Phase C**.
7. Run **Phase E**. All checks must be green — including ownership of the credit-limit SPs and the new columns.
8. Confirm the tasks are running: `SHOW TASKS LIKE 'CC_%' IN SCHEMA <db>.<schema>;`

**Behaviour changes in this release**
- Model Access no longer offers an account-wide option (`CORTEX_MODELS_ALLOWLIST` is retired by BCR-2378). Use **Role Directly** or **Role Members** (model RBAC).
- Access grants offer `CORTEX_USER` or `CORTEX_AGENT_USER`; `COPILOT_USER` is transitional (BCR-2445).
- Temporary limits created before this release have no expiry date recorded and will not auto-revert — re-apply them as Temporary if needed.
- If the app was owned by a custom role, transfer it to ACCOUNTADMIN for Phases A and C, then transfer it back.

<!-- ------------------------ -->
## Native Per-User Quotas
Duration: 3

### Hard Enforcement with SNOWFLAKE.CORE.QUOTA

The **User Quotas** page manages Snowflake's native per-user quotas (`SNOWFLAKE.CORE.QUOTA` objects, generally available). These complement the app's daily limits:

| | Daily limits (Credit Configuration) | Native quotas (User Quotas) |
|---|---|---|
| **Mechanism** | `ALTER USER SET CORTEX_CODE_*_DAILY_EST_CREDIT_LIMIT_PER_USER` | `SNOWFLAKE.CORE.QUOTA` object |
| **Cycle** | Daily, per surface | Monthly, weekly and daily, aligned to the UTC calendar (custom cycle start dates are not supported) |
| **Scope** | Per user, per cohort | One quota per role cohort |

From the page you can create quotas (one per matched role when you use a role pattern), review live limits and remove quotas. See [Per-user quotas](https://docs.snowflake.com/en/user-guide/budgets/per-user-quotas).

<!-- ------------------------ -->
## How This Complements Native Controls
Duration: 2

Snowflake now provides native per-user quotas and MDM policy enforcement (preview), which overlap parts of this app's cost and policy features. Use the native controls for hard platform-level enforcement; the app adds the governance workflow around them:

- **Per-user overrides** on top of cohort defaults, including temporary limits that auto-revert
- **Self-service credit requests** with an admin and domain-lead approval queue
- **Intelligent rebalancing** of unused credits between users
- **Pattern-based administration** — apply limits, access and model RBAC to many roles, users or tag values at once
- **A full audit trail** of every admin action in `CC_AUDIT_LOG`

<!-- ------------------------ -->
## Conclusion
Duration: 2

### What You Built

- A fully operational enterprise governance layer for Cortex Code with 18 pages
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
