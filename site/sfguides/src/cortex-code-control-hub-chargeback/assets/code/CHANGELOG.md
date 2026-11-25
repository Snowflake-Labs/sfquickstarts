# Changelog

All notable changes to the CoCo Control Hub & Chargeback solution.

## [1.3.0] — 2026-08-12

Rebrand: app display name is now **CoCo Control Hub & Chargeback** (was "CoCo Control Hub").

- Display-only change across all user-facing surfaces: in-app title / sidebar / home header
  (`APP_NAME`), Snowsight object title, alert/email footer branding, the PDF invoice header,
  and the Setup help text. Docs updated (README, GETTING_STARTED).
- No functional change: the Streamlit object name, stage, and URL
  (`.../CORTEX_CODE_CREDIT_MANAGER`) are unchanged; no schema, query, or data was touched.

## [1.2.2] — 2026-08-07

Fix: prompt/observability pipeline silently stopped ingesting.

- **`SP_CC_CLASSIFY_PROMPTS` timestamp fix.** `EVENT_TS` was written to `CC_PROMPT_EVENTS`
  from a pandas nanosecond datetime, corrupting the stored `TIMESTAMP_NTZ` values. The next
  run's incremental watermark (`MAX(EVENT_TS)`) then failed to render, the load query threw,
  and the exception was swallowed — so the task reported success while ingesting zero rows.
  Observability, User Intelligence, Prompt Insights, and Model Intelligence froze at the first
  backfill date.
- **Fix:** load and store `EVENT_TS` as a formatted string (`YYYY-MM-DD HH24:MI:SS.FF3`) so
  Snowflake casts it into `TIMESTAMP_NTZ` on write; compute the watermark as a formatted
  literal. No pages or schema changed. Existing installs need a one-time truncate +
  re-backfill of `CC_PROMPT_EVENTS` after upgrading.

## [1.2.1] — 2026-08-07

Packaging cleanup.

- **Removed the bundled `skills/` folder** (`coco-hub-deploy`, `coco-hub-knowledge`). The
  skills are not used by the running app and are not required to deploy or operate it.
- `GETTING_STARTED.md` now points to `DEPLOYMENT_GUIDE.md` and the in-app Setup page for the
  guided deployment path. No change to application behavior.

## [1.2.0] — 2026-08-03

Deployment portability: the app installs cleanly on any Snowflake account with minimal setup.

- **Auto-detects its location:** `config.yaml` is left blank so the app resolves the current
  database/schema of the session it runs in — no editing required.
- **Single configuration point:** set your `MY_DATABASE` / `MY_SCHEMA` / `MY_WAREHOUSE` values in
  `snowflake.yml` (or ask Cortex Code to set them). The README documents this one step.
- **No hardcoded targets:** the project-attribution starter kit uses `<YOUR_DB>.<YOUR_SCHEMA>`
  placeholders, and Setup resolves the warehouse from the active session.
- No change to application behavior; existing deployments are unaffected.

## [1.1.0] — 2026-07-31

New governance features and correctness fixes.

### New features
- **Native Per-User Quotas (Preview):** admin page fronting `SNOWFLAKE.CORE.QUOTA` for hard per-user
  credit enforcement (`SP_CC_MANAGE_QUOTA`, `CC_NATIVE_QUOTAS`, `CC_COHORT_TAG`).
- **AI Budgets:** manage native `SNOWFLAKE.CORE.BUDGET` objects from Settings, backed by
  `CC_AI_BUDGETS` / `CC_AI_BUDGET_USAGE` and a nightly refresh task.

### Fixes
- More accurate usage summaries: duplicate-row dedup, cohort fan-out fix, and multi-model credit
  correction in `SP_CC_REFRESH_USAGE_SUMMARIES` (the chargeback bill reads these).
- Credit requests: approving an unlimited user no longer caps them; daily rate limits count in UTC.
- Credit configuration: fixed cohort-resolution and Desktop-override save errors; added app-tracked
  monthly budgets.
- Model access: safe upsert-then-prune (no window where a role has zero models).
- Cost attribution now includes Desktop credits (previously CLI + Snowsight only).
- Additional fixes: usage-trends heatmap, budget-forecast clamping, and prompt session-id resolution.

## [1.0.0] — 2026-07-24

Initial release: the CoCo Control Hub plus the full chargeback + attribution layer.

### Governance & observability
- Usage, prompt, model, and cost visibility by user and surface (CLI / Desktop / Snowsight).
- Per-user and cohort credit limits, model-tier access, budgets, alerts.
- Full audit trail of admin actions.

### Chargeback & attribution
- Guided bill-generation flow across three adoption models (M1 Internal Cross-Charge,
  M2 Build Here / Deploy There, M3 Partner on Customer Account).
- Flat AI pricing built in ($2.00 global / $2.20 in-region, Apr 2025); editable rate,
  separate warehouse (contract) rate.
- Bill = LLM token credits, plus optional SQL / warehouse compute (default off).
- Confidence-scored attribution waterfall (service account → user tag → role) with an
  Unattributed Queue — usage is never billed blindly.
- Cost tagging: manual grid plus read-only auto-sync of native Snowflake user tags
  (`SP_CC_SYNC_COST_TAGS`); the app never alters account objects.
- Attribution & Tags page with unified identity levers and an advanced project-grain starter kit.
- Model Bake-off tab; sectioned navigation.
- PDF / CSV export: internal showback statement or external invoice with margin.
