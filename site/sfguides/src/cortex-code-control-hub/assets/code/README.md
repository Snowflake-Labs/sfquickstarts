# CoCo Control Hub

> Govern AI spend. Protect responsibly. Audit everything.

A **Streamlit-in-Snowflake** application that wraps Snowflake's native Cortex Code credit parameters with enterprise governance — cohort budgets, intelligent rebalancing, model-tier enforcement, responsible AI monitoring, and a full audit trail. Everything runs inside your Snowflake account. Zero external dependencies.

[![Snowflake](https://img.shields.io/badge/Built%20for-Snowflake-29B5E8)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
[![Platform](https://img.shields.io/badge/Deployment-Streamlit%20in%20Snowflake-blue)](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

---

## The Problem

Snowflake Cortex Code bills on token consumption. Native controls are minimal:

```sql
ALTER ACCOUNT SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 20;  -- everyone
ALTER USER john SET CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = 30; -- one person
```

For an enterprise with 5,000–50,000 users this doesn't scale:

| Gap | Business impact |
|---|---|
| No team-level budgets | Admin runs N `ALTER USER` statements per team change |
| No audit trail | Compliance can't answer who changed what limit, when, and why |
| No self-service | Developer hits limit at 2 PM → blocked for the day → files a ticket |
| No intelligence | 60 % of daily allocations go unused while others are blocked |
| No model governance | Junior analyst uses Opus when Sonnet handles the task fine |
| No budget forecasting | Finance asks "what will AI cost next quarter?" — no answer |
| No responsible AI visibility | No way to know if users are sharing PII or attempting jailbreaks |

---

## What's Inside

### 16 Pages

| Page | Purpose |
|---|---|
| **Setup** | 7-step Account Prerequisites + Phases A–E wizard. Creates all objects, seeds defaults. No CLI required. |
| **Home** | Executive snapshot: KPIs, surface split (CLI/Snowsight/Desktop), top users, model breakdown, AI Guardrails status, daily trend. |
| **Access Management** | Grant `CORTEX_USER` + `COPILOT_USER` to users, roles, or by user tag. View role inheritance. |
| **Credit Configuration** | Set daily limits at account, cohort (role or tag), or individual user level. Temporary overrides auto-revert. Native AI Budgets (Preview) for agent-level hard enforcement. |
| **Usage Trends** | Stacked area trend, timezone-aware heatmap, spike detection, recommendations. |
| **Budget Forecast** | Linear regression projections. Trend-adjusted 7d / 30d / 90d. Per-cohort spend breakdown. |
| **Model Access** | Discover models in use, assign to tiers (TIER_1/2/3), map tiers to roles, enforce via `CORTEX_MODELS_ALLOWLIST` + model RBAC. |
| **AI Observability** | Account → Cohort → User drill-down. DAU, WoW, Cortex AI Guardrails status, latency, prompt intelligence with surface split (CLI/Snowsight/Desktop), tool call tracking, Token Economics, Cache Hit Rate. |
| **Cost Attribution** | Per-prompt & per-session credit costs via ACCOUNT_USAGE join. Configurable USD/credit rate. Cohort cost breakdown. |
| **Prompt Insights** | Responsible AI governance dashboard. HIGH/MEDIUM/LOW severity classification, user governance profiles, insights feed. Classifies **both user prompts and AI responses**. |
| **Policy Rules** | Admin-configurable keyword, regex, or AI_CLASSIFY (semantic) rules. Rules can target prompts, AI responses, or both. |
| **Credit Requests** | User self-service: request more credits or a model tier upgrade. Admin/domain-lead approval queue with system recommendations. |
| **Settings** | Approval mode, rebalance parameters, donor strategy, rate limits, USD/credit rate, evaluation model config. |
| **Audit Log** | Immutable log of every grant, limit change, approval, rejection, and rebalance. Filterable, CSV export. |
| **User Intelligence** | Full per-user profile: credits, tokens, cache efficiency, governance score, prompt search. |
| **Model Intelligence** | LLM comparison: latency (P50/P95), Token Economics, Cache Hit Rate, Custom Quality (Experimental), Prompt Insights per model. |

---

## Responsible AI Governance

Three-tier classification pipeline powered by `SP_CC_CLASSIFY_PROMPTS`:

```
SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS
    ↓  Step 0: extract prompts + AI responses (CodingAgent.Step-0 + CodingAgentRun)
CC_PROMPT_EVENTS               ← typed columns, clustered by date, sub-second reads
    ↓  Tier 1: KEYWORD (free)  ← Python substring match
    ↓  Tier 2: REGEX (free)    ← Python re.search()
    ↓  Tier 3: SEMANTIC        ← SNOWFLAKE.CORTEX.AI_CLASSIFY(text, [rule_labels, 'benign'])
CC_PROMPT_VIOLATIONS           ← one row per insight, CONTENT_TYPE = PROMPT|RESPONSE
    ↓  Step 5: daily aggregate
CC_PROMPT_ANALYSIS_DAILY       ← fast-read governance dashboard, per user per day
```

**Key design decisions:**
- Tiers run in order — prompts caught by Tier 1/2 never reach Tier 3 (cost control)
- SHA-256 dedup — identical prompts/responses classified once (~$0.00005 cr/unique text)
- Rules apply to `PROMPT`, `RESPONSE`, or `BOTH` — controllable per rule
- Private Mode sessions: response is null — response rules skipped, prompt rules fire normally
- SEMANTIC cap: 5,000 unique prompts, 2,000 unique responses per run
- Severity levels: HIGH / MEDIUM / LOW — configurable per policy rule

### Cortex AI Guardrails (Enterprise Preview)

Platform-level protection against prompt injection and jailbreak attacks, available via Snowflake Horizon Catalog. Status shown on Home page and AI Observability. Enable via Setup → Account Prerequisites → Step 6.

```sql
ALTER ACCOUNT SET AI_SETTINGS = $$
  guardrails:
    advanced_prompt_injection:
      - enabled: true
$$;
```

### Native AI Budgets (Snowflake Preview)

Tag-based hard enforcement for Cortex Agent objects — automated REVOKE USAGE when monthly spend reaches 100%. Complements CoCo's per-user soft limits. Configured via Credit Configuration → Native AI Budgets.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Streamlit in Snowflake                  │
│   (owner-rights: all SQL runs as Streamlit owner role)  │
│                                                         │
│  pages/          ← UI rendering, zero direct DDL        │
│  utils.py        ← Read-only cached data access         │
│  intelligence.py ← EWMA prediction + donor selection    │
│  audit.py        ← Write-only audit log                 │
│  config.py       ← 3-tier DB/schema resolution          │
│  sp_definitions.py ← Bulk SP DDL for setup              │
└──────────────┬───────────────────────────────┬──────────┘
               │  CALL SP (elevated actions)    │  SELECT (reads)
               ▼                               ▼
┌──────────────────────┐         ┌──────────────────────────┐
│  Owner-Rights SPs    │         │  App Tables (CC_*)        │
│  EXECUTE AS OWNER    │         │  CC_USAGE_DAILY_SUMMARY   │
│  ─────────────────   │         │  CC_USAGE_HOURLY_SUMMARY  │
│  SP_CC_BULK_SET_*    │         │  CC_CREDIT_CONFIG         │
│  SP_CC_BULK_GRANT_*  │         │  CC_AUDIT_LOG             │
│  SP_CC_SET_USER_*    │         │  CC_CREDIT_REQUESTS       │
│  SP_CC_GRANT_ACCESS  │         │  CC_APP_CONFIG            │
│  SP_CC_REBALANCE_*   │         │  CC_MODEL_CONFIG          │
│  SP_CC_REFRESH_*     │         │  CC_USER_COHORT_RESOLVED  │
│  SP_CC_DAILY_RESET   │         │  CC_POLICY_RULES          │
│  SP_CC_CLASSIFY_*    │         │  CC_PROMPT_EVENTS         │
└──────────────────────┘         │  CC_PROMPT_VIOLATIONS     │
                                 │  CC_PROMPT_ANALYSIS_DAILY │
                                 └──────────────────────────┘
               │  ALTER USER / GRANT DATABASE ROLE
               ▼
┌──────────────────────────────────┐
│   Snowflake Account Metadata     │
│   User parameters, role grants   │
│   ACCOUNT_USAGE views            │
└──────────────────────────────────┘
```

### Owner-Rights Execution Model

All SQL — including `ALTER USER`, `GRANT DATABASE ROLE`, and `CREATE TABLE` — runs as the role that **owns the Streamlit object** (recommended: ACCOUNTADMIN). End users never need elevated privileges. Every privileged action is channelled through stored procedures that validate inputs before executing.

### Role Separation

| Role | Owns | Purpose |
|---|---|---|
| `CC_SP_OWNER_ROLE` | All SPs and tasks | Has MANAGE GRANTS + ALTER USER privileges. Assumed by nobody — only used via EXECUTE AS OWNER. |
| `CC_APP_ROLE` | App tables | Streamlit runtime role. Can read/write CC_* tables and CALL SPs. |
| `CC_ADMIN_ROLE` | — | Inherits CC_APP_ROLE. Grant to platform admins who manage the app. |
| `CC_USER_ROLE` | — | Inherits CC_APP_ROLE. Grant to Cortex Code end users. |

> **In practice** you don't need CC_ADMIN_ROLE or CC_USER_ROLE. Just add your existing org roles to `admin.roles` in `config.yaml`. The only non-negotiable role is `CC_SP_OWNER_ROLE` — it's what makes `ALTER USER` safe without handing out ACCOUNTADMIN.

---

## Intelligence Engine

When a user requests additional credits, the system decides automatically whether to fulfill the request — no admin intervention needed in AUTO mode.

### How EWMA Prediction Works

```
For each potential donor in the cohort:

  1. Collect 14 days of hourly usage history
  2. For each remaining hour today:
       predicted_hour = ewm(alpha=0.3).mean()     ← EWMA, recent data weighted higher
       if >= 3 same-weekday observations:
           predicted_hour = 0.4 × all-days + 0.6 × same-weekday   ← DOW adjustment
  3. predicted_remaining = sum(predicted hours)
  4. safe_surplus = limit - used_today - predicted_remaining - (limit × buffer%)
  5. transferable = min(safe_surplus, limit × max_transfer_cap%)
```

**Cold-start guard:** Users with fewer than 5 days of history are treated as full-consumption (transferable = 0). New joiners are never selected as donors.

### Four Donor Strategies

| Strategy | Behaviour | Best for |
|---|---|---|
| **WEIGHTED_RANDOM** | Probabilistic selection proportional to surplus. Same person not always chosen. | Most deployments (default) |
| **HIGHEST_SURPLUS** | Always take from whoever has the most available. Predictable. | Conservative/audit-sensitive orgs |
| **MINIMUM_DONORS** | Tries to satisfy the full request from a single donor first; falls back to greedy-from-largest. | Minimise blast radius |
| **ROUND_ROBIN** | Skips donors who donated in the last N hours. Most equitable rotation. | Fairness-sensitive teams |

---

## Deployment

### Step 0 — Account Prerequisites (run once as ACCOUNTADMIN)

Before deploying, run these 7 one-time grants in Snowsight. The Setup page shows copy-paste SQL for each:

1. **Cross-region inference** — `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY'`
2. **AI Observability access** — `GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE`
3. **ACCOUNT_USAGE access** — `GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CC_SP_OWNER_ROLE`
4. **Model access for users** — `GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CC_USER_ROLE`
5. **Credit limits** _(optional)_ — `ALTER ACCOUNT SET CORTEX_CODE_CREDIT_LIMIT = N`
6. **AI Guardrails** _(Enterprise, optional)_ — `ALTER ACCOUNT SET AI_SETTINGS = $$ guardrails: ... $$`
7. **Native AI Budgets** _(Preview, optional)_ — tag-based budget enforcement for Cortex Agent objects

### Step 1 — Configure `config.yaml`

```yaml
deployment:
  database: YOUR_DB      # e.g. MY_DB — leave blank to use CURRENT_DATABASE()
  schema: YOUR_SCHEMA    # e.g. APPS — leave blank to use CURRENT_SCHEMA()

admin:
  roles:
    - ACCOUNTADMIN
    - YOUR_PLATFORM_ADMIN_ROLE   # optional — roles that see all admin pages
```

### Step 2 — Deploy

```bash
cd streamlit-apps/cortex-code-credit-manager
snow streamlit deploy --connection YOUR_CONNECTION --database YOUR_DB --schema YOUR_SCHEMA
```

### Step 3 — Run Setup Phases

Open the app → **Setup** page:
- **Phase A** — Create all objects (roles, tables, tasks, stream, email integration)
- **Phase B** — Seed default settings
- **Phase C** — Create stored procedures
- **Phase D** — Initial data load (D1: usage summaries, D2: prompt events, D3: model config)
- **Phase E** — Verify all objects exist

---

## Configuration Reference

### `config.yaml`

```yaml
deployment:
  database: ""   # Leave blank to use CURRENT_DATABASE()
  schema: ""     # Leave blank to use CURRENT_SCHEMA()

admin:
  roles:         # Roles that see all admin pages
    - ACCOUNTADMIN
    # - YOUR_PLATFORM_ADMIN_ROLE
```

The sidebar **Deployment Target** picker overrides these values at runtime without redeploying — useful when managing multiple environments from one app.

### App Settings (via Settings page)

| Setting | Default | Description |
|---|---|---|
| `APPROVAL_MODE` | `ADMIN` | `AUTO` = instant rebalance. `ADMIN` = queue for review. |
| `DONOR_STRATEGY` | `WEIGHTED_RANDOM` | See Intelligence Engine section above. |
| `REBALANCE_BUFFER_PCT` | `20` | Safety margin % kept with donor after prediction. |
| `REBALANCE_MAX_TRANSFER_PCT` | `50` | Max % of donor's limit that can be transferred. |
| `REBALANCE_LOOKBACK_DAYS` | `14` | Days of hourly history used for EWMA prediction. |
| `DONOR_PROTECTION_HOURS` | `4` | Hours before a recent donor can be selected again (ROUND_ROBIN). |
| `MAX_REQUESTS_PER_USER_PER_DAY` | `2` | Rate limit: max credit requests per UTC day. |
| `REQUEST_COOLDOWN_MINUTES` | `60` | Wait time between two requests. |
| `MAX_EXTRA_CREDITS_PER_WEEK` | `20` | Rolling 7-day extra credit cap per user. |
| `DAILY_RESET_ENABLED` | `TRUE` | Restore rebalanced limits to cohort defaults at midnight UTC. |
| `EVAL_ENABLED` | `FALSE` | Enable LLM-as-Judge custom quality scoring (optional, costs credits). |
| `EVAL_MODEL` | `llama3.1-70b` | Model used as judge (configurable). |

---

## Key Metrics

| Metric | Source | Formula | Notes |
|---|---|---|---|
| Cache Hit Rate | CC_PROMPT_EVENTS | `cache_read / (cache_read + cache_write)` | Standard hits/(hits+misses). GPT models may show 100% if cache_write=0. |
| P50/P95 Latency | CC_PROMPT_EVENTS | `PERCENTILE_CONT(0.95)` on LATENCY_MS | From `planning.duration` in AI_OBSERVABILITY_EVENTS. |
| Custom Quality Scores | CC_RESPONSE_QUALITY | LLM judge via CORTEX.COMPLETE | **Experimental** — not Snowflake's built-in quality measurement. |
| Governance Score | Computed in-app | `high_insights×0.15 + insight_rate×0.02 + safety_penalty` | **Experimental** composite — directional signal only. |

---

## Scale Design

Built for 50,000+ users:

| Challenge | Solution |
|---|---|
| Cohort apply (N ALTER USER calls) | `SP_CC_BULK_SET_COHORT_LIMITS` — single SP call, server-side loop, no CLIENT_ABORT risk |
| Bulk access grants | `SP_CC_BULK_GRANT_ACCESS` — single SP call with JSON array, returns `{success, failed, errors}` |
| User search dropdown | Server-side `ACCOUNT_USAGE.USERS ILIKE '%query%' LIMIT 50` — never loads 50K users into browser |
| Per-render SQL overhead | `get_current_user`, `user_is_admin`, `SHOW DATABASES` all cached with `@st.cache_data(ttl=600)` |
| New user as donor | Cold-start guard: < 5 days history → transferable = 0 |

---

## SQL Injection Prevention

Four independent layers: Python identifier validation → SQL literal escaping (`escape_sql_literal`) → SP-level `REGEXP_LIKE` validation → Role separation (CC_APP_ROLE cannot execute `ALTER USER` directly). See code comments for details.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Snowflake Enterprise or higher | Required for ACCOUNT_USAGE views and Cortex AI Guardrails |
| ACCOUNTADMIN (one-time) | For Account Prerequisites (step 0) and setup |
| Cortex Code enabled on account | Contact your Snowflake account team if not active |
| Any warehouse (XSMALL sufficient) | App is read-heavy; smallest warehouse works fine |
| Snowflake CLI (optional) | `pip install snowflake-cli` — for `snow streamlit deploy` |

---

## Contributing

Visualization standard: **Altair only**. Every chart must use `configure_view(strokeWidth=0)` and `.configure(background='#0e1117')`. No Plotly. No pie charts. No hardcoded FQNs — always use `fq_table(session, TABLE_NAME)`.

Built with [Cortex Code](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code).



---

## Known Data Behaviours

| Observation | Explanation |
|---|---|
| Sessions show as "Surface Unknown" / blank | `origin_application` is used as the primary surface lookup (always populated with `snowsight`, `cortex-code-cli`, or `snowflake_coco_desktop`). Old rows stored `ENTRYPOINT = ''` (empty string) before the fix — empty strings bypass `IS NOT NULL` filters. Fix: Phase C (recreate SP) + truncate `CC_PROMPT_EVENTS` + Phase D2 re-backfill 180 days. |
| Desktop Sessions = 0 even after fix | Run Phase C (recreate SP) then Phase D2 (re-backfill). Pages read from CC_PROMPT_EVENTS — no page code changes needed. |
| GPT models show 100% cache hit rate | OpenAI does not report `cache_write` tokens. Formula `cache_read / (cache_read + 0) = 100%` — treat as "cache write data unavailable", not a true hit rate. |
| Prompt Intelligence numbers unchanged across periods | `CC_PROMPT_EVENTS` only holds data for periods the SP was run. If backfill covers only 30 days and all events fall within 7 days, selecting 7 / 14 / 30 returns the same count. Run D2 with a larger window to fill gaps. |
| Desktop Sessions = 0 | Expected if no users are running Cortex Code Desktop in this account. CLI and Snowsight are the primary surfaces. |

---

## ENTRYPOINT / Surface Detection

Surface (CLI / SNOWSIGHT / DESKTOP) is stored in `CC_PROMPT_EVENTS.ENTRYPOINT` by `SP_CC_CLASSIFY_PROMPTS`.
Confirmed from live enterprise `AI_OBSERVABILITY_EVENTS` data.

### Resolution logic (`origin_application` is primary — always populated)

```sql
UPPER(COALESCE(
    -- PRIMARY: origin_application is always set to one of 3 known values
    CASE coding_agent.origin_application
        WHEN 'snowsight'              THEN 'SNOWSIGHT'
        WHEN 'cortex-code-cli'        THEN 'CLI'
        WHEN 'snowflake_coco_desktop' THEN 'DESKTOP'
        ELSE NULL
    END,
    -- Fallback: entrypoint field (CLI also sets this to 'cli')
    coding_agent.entrypoint,
    -- Fallback: client_type (future-proof for unknown origin_app values)
    CASE coding_agent.client_type
        WHEN 'codingagent_snowsight'  THEN 'SNOWSIGHT'
        WHEN 'codingagent_snova'      THEN 'CLI'
        WHEN 'codingagent_desktop'    THEN 'DESKTOP'
        WHEN 'snowflake_coco_desktop' THEN 'DESKTOP'
        ELSE NULL
    END
))
```

### Confirmed field values (from enterprise `AI_OBSERVABILITY_EVENTS`)

| Surface | origin_application | client_type | entrypoint |
|---|---|---|---|
| CLI | `cortex-code-cli` | `codingagent_snova` | `cli` |
| Snowsight | `snowsight` | `codingagent_snowsight` | NULL |
| Desktop | `snowflake_coco_desktop` | `snowflake_coco_desktop` | NULL |

**Key learnings:**
- `origin_application` is **always populated** — use it as the primary lookup
- `codingagent_desktop` is a legacy client_type that is **never actually emitted**
- Desktop is typically the **majority** of sessions in enterprise accounts
- `entrypoint` is only set for CLI sessions; NULL for Desktop and Snowsight

### Empty-string ENTRYPOINT bug (now fixed)

Old SP used `fillna('')` which stored `''` instead of `NULL` when the surface was unresolved.
Empty strings are `IS NOT NULL = TRUE` so they bypassed all filters and appeared as a blank label.

**Fix applied:** SP now stores `None` (NULL) for unresolved sessions. Query also filters `AND ENTRYPOINT != ''`.

### Re-backfill existing blank sessions

```sql
-- Step 1: Reset watermark so all events are re-processed
TRUNCATE TABLE <DB>.<SCHEMA>.CC_PROMPT_EVENTS;

-- Step 2: Re-classify 180 days with the fixed SP
CALL <DB>.<SCHEMA>.SP_CC_CLASSIFY_PROMPTS(4320);  -- 180 × 24 = 4320 hours
```

**No page code changes needed** — all pages read ENTRYPOINT from CC_PROMPT_EVENTS.

---

## Deploying Updates — What to Re-Run

After a code-only deploy (`snow streamlit deploy --replace`):

| Changed | Re-run needed |
|---|---|
| `sp_definitions.py` | Phase C (recreate SPs) + Phase D2 (re-backfill if needed) |
| `pages/*.py` only | None — takes effect on page reload |
| `config.yaml` admin roles | None — read at runtime |
| `prerequisites.sql` | Phase A only if new tables added |


---

## Desktop Surface — Complete Fix Record

Desktop (`snowflake_coco_desktop`) was missing from multiple components. All gaps fixed in this release:

### What was missing

| Component | Gap | Fix |
|---|---|---|
| `CC_CREDIT_CONFIG` table | No `DESKTOP_DAILY_LIMIT` column | Added |
| `CC_USAGE_DAILY_SUMMARY` table | No `DESKTOP_LIMIT_AT_DATE` column | Added |
| `SP_CC_REFRESH_USAGE_SUMMARIES` | No `CORTEX_CODE_DESKTOP_USAGE_HISTORY` MERGE | Added (daily + hourly) |
| `SP_CC_DAILY_RESET_LIMITS` | Only reset CLI + Snowsight at midnight | Now resets Desktop too |
| `credit_config.py _apply_cohort` | Silently dropped Desktop limit | Now saves `DESKTOP_DAILY_LIMIT` |
| `credit_config.py` user override | Same | Fixed |
| `observability.py` cohort credits | No `DT_CREDITS` surface split | Added |
| `observability.py` user detail | Only CLI + Snowsight metrics | Added Desktop Credits card |
| `cost_attribution.py` cohort summary | No `COHORT_DT_LIMIT` | Added |

Already correct: all other SPs (rebalance, bulk set/grant, expire), `config.py SURFACES`, `home.py`, `usage_trends.py`.

### ENTRYPOINT empty-string bug (also fixed)

SP was using `fillna("")` which stored `""` not `NULL` for unresolved sessions. Empty strings bypass `IS NOT NULL` filters, appearing as a blank row in charts. Fixed: SP stores `None`; query adds `AND ENTRYPOINT != ""`.

### Deployment sequence for a fresh install

After deploying updated code (`snow streamlit deploy --replace`):

1. **Account Prerequisites** — 7 SQL blocks in Snowsight as ACCOUNTADMIN
2. **Phase A** — recreates all objects including new Desktop columns
3. **Phase B** — seed defaults
4. **Phase C** — recreates `SP_CC_CLASSIFY_PROMPTS` with `origin_application`-first ENTRYPOINT
5. **`TRUNCATE CC_PROMPT_EVENTS`** — resets watermark for full re-backfill
6. **Phase D1** — backfill credits (now includes Desktop via `CORTEX_CODE_DESKTOP_USAGE_HISTORY`)
7. **Phase D2 / 180 days** — re-classify all prompts with correct surface (`CALL SP_CC_CLASSIFY_PROMPTS(4320)`)
8. **Phase E** — verify all objects
