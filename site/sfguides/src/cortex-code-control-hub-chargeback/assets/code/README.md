# CoCo Control Hub & Chargeback

> See it. Control it. Charge it back. A Snowflake-native app for governing, observing, and cross-charging Cortex Code (CoCo) usage.

A **Streamlit-in-Snowflake** application that combines Cortex Code governance and observability with a full **chargeback + attribution** capability. Everything runs inside your Snowflake account — no data leaves, no external services.

[![Snowflake](https://img.shields.io/badge/Built%20for-Snowflake-29B5E8)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
[![Platform](https://img.shields.io/badge/Deployment-Streamlit%20in%20Snowflake-blue)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

This repository is a dedicated, standalone home for the solution. It is built on the
Cortex Code credit-manager Quickstart (see [NOTICE](NOTICE)) with a chargeback layer added on top.

---

## What it does

- **See it** — usage, prompts, models, and cost by user and surface (CLI / Desktop / Snowsight); AI observability.
- **Control it** — per-user credit limits, cohort budgets, model-tier access, budgets, alerts, and a full audit trail.
- **Charge it back** — internal showback or external invoice across three adoption models, with a confidence-scored attribution waterfall and an unattributed queue (never bill blindly).

### Chargeback highlights

- **Flat AI pricing** built in — $2.00 global / $2.20 in-region (Apr 2025 list); rate editable.
- **Bill** = LLM token credits, plus **optional** SQL / warehouse compute at your contract rate.
- **Attribution waterfall** — service account (L3) → user tag (L4) → role (L5), confidence-labeled; anything unmatched lands in an **Unattributed Queue**, reviewed and never billed blindly.
- **Read-only tag sync** from native Snowflake user tags — the app never alters account objects.
- **PDF / CSV export** — showback statement or external invoice with margin.

## Adoption models

| Model | Scenario | Money flow | Grain |
|---|---|---|---|
| **M1 · Internal Cross-Charge** | One shared account, many teams | Platform owner bills each internal team/vertical (at-cost showback) | User → vertical tag |
| **M2 · Build Here, Deploy There** | You run CoCo in your account, deploy assets to a customer | You invoice the customer per engagement | Engagement (optional session overlay) |
| **M3 · Partner on Customer Account** | Partner staff work in the customer's account | Customer bills the partner back | Partner-user identity |

Measurement is always at the account level (`SNOWFLAKE.ACCOUNT_USAGE`); attribution only slices that same usage by the chosen dimension.

## Prerequisites

- A Snowflake account with Cortex Code usage.
- `ACCOUNTADMIN` (or an owner role with equivalent grants) to run the one-time setup.
- Snowflake CLI (`snow`) configured with a connection, for deployment.

## Deploy

The app deploys as a warehouse Streamlit-in-Snowflake object.

**1. Configure for your account.** Edit the three placeholders in `snowflake.yml` to your target
database, schema, and warehouse (or ask Cortex Code to set them for you):

```yaml
identifier:
  database: MY_DATABASE     # your database
  schema:   MY_SCHEMA       # your schema
query_warehouse: MY_WAREHOUSE   # your warehouse
```

You do **not** need to edit anything else — the app auto-detects where it is deployed at runtime
(`config.yaml` is left blank on purpose, so it resolves the current database/schema of the session).

**2. Deploy.** From the repo root:

```bash
snow streamlit deploy -c <your-connection> --role ACCOUNTADMIN --replace
```

**3. Provision objects.** Open the app's **Setup** page and run Phases A–E once to create all backing
tables, stored procedures, tasks, and seed defaults.

See [GETTING_STARTED.md](GETTING_STARTED.md) and [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detail.

## Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) — quickest path to a running app.
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — deployment options and configuration.
- [SOLUTION.md](SOLUTION.md) — architecture and design.
- [CHANGELOG.md](CHANGELOG.md) — version history.

## License / distribution

Snowflake internal — proprietary. Not for external distribution. See [LICENSE](LICENSE).
