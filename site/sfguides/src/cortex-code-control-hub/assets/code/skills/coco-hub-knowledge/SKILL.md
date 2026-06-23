---
name: coco-hub-knowledge
description: >
  Complete knowledge base for CoCo Control Hub (Cortex Code Credit Manager v2).
  Invoke whenever someone asks about the app's architecture, pages, data flow,
  stored procedures, tables, analytics concepts, token economics, LLM-as-Judge
  evaluation, responsible AI classification, alert system, prompt patterns,
  latency interpretation, insight rates, cache efficiency, data sources,
  or how to interpret any dashboard metric. Covers common questions, known
  bugs, design decisions, and the full nightly SP pipeline.
triggers:
  - CoCo Control Hub
  - Cortex Code Credit Manager
  - how does the app work
  - what does this page show
  - explain the observability
  - how are insights detected
  - what is the nightly SP
  - token economics
  - LLM-as-Judge
  - groundedness
  - prompt patterns
  - user intelligence
  - cache hit rate
  - how do I interpret
  - why is output so small
  - why are scores low
  - insights more than prompts
  - what does P95 mean
  - where does data come from
  - which event table
  - system prompts filtered
  - prompt insights
---

# CoCo Control Hub — Complete Knowledge Base

## What the App Is

CoCo Control Hub is a **Snowflake Streamlit** admin dashboard for governing Cortex Code usage across an enterprise. It gives administrators visibility into who is using Cortex Code AI, what they are asking, how much it costs, whether usage is compliant with responsible AI policies, and how the AI models are performing.

Deployed as a Streamlit app (warehouse-mode or SPCS container) reading from:
- `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` — raw Cortex Code spans (nightly backfill)
- `SNOWFLAKE.ACCOUNT_USAGE.*` — credit/usage history (nightly backfill)
- Custom tables in the app schema (pre-aggregated, fast reads)

---

## Architecture

```
AI_OBSERVABILITY_EVENTS (raw spans, Snowflake-managed)
         │
         ▼  [SP_CC_CLASSIFY_PROMPTS — nightly 2am UTC]
CC_PROMPT_EVENTS          ← typed columns, token economics, categories, cost
CC_PROMPT_VIOLATIONS      ← policy violations per prompt
CC_PROMPT_ANALYSIS_DAILY  ← per-user daily risk aggregation

ACCOUNT_USAGE.* (credit history)
         │
         ▼  [SP_CC_REFRESH_USAGE_SUMMARIES — every 30 min]
CC_USAGE_DAILY_SUMMARY    ← credits/tokens/requests by user+surface+date

CC_PROMPT_EVENTS + ACCOUNT_USAGE (REQUEST_ID join, nightly)
         │
         ▼  [SP_CC_CLASSIFY_PROMPTS Step 6b]
PROMPT_COST_CREDITS       ← actual billing per prompt

CC_PROMPT_EVENTS → SP_CC_EVALUATE_RESPONSES (on demand)
         │
         ▼
CC_RESPONSE_QUALITY       ← LLM-as-Judge scores per response
```

---

## Pages & What They Show (sidebar order)

| Page | Group | Purpose |
|---|---|---|
| **Home** | — | Executive snapshot: KPIs, surface split, top users, top LLMs, 7-day trend, health pulse |
| **Setup** | Admin | 5-phase install: objects, defaults, SPs, data load, verify |
| **Settings** | Admin | App config: eval model, credit pricing, alert email, backfill period |
| **Audit Log** | Admin | All admin actions on this account |
| **Access Management** | Access & Limits | Grant/revoke Cortex Code access by user or role |
| **Credit Configuration** | Access & Limits | Credit limits at account → cohort → user level |
| **Model Access** | Access & Limits | Tier management (TIER_1/2/3), role-model assignments |
| **Credit Requests** | Access & Limits | Self-service credit increase requests |
| **Usage Trends** | Usage & Cost | Credit burn over time, DAU, heatmap, spike detection, forecast |
| **Cost Attribution** | Usage & Cost | Credits by cohort, top users by credits, per-prompt cost |
| **AI Observability** | Observability | 11-tab span-level intelligence (see Observability Tabs below) |
| **User Intelligence** | Observability | Full per-user profile: credits, tokens, insights, quality, prompt search |
| **Prompt Insights** | Responsible AI | Risk dashboard, user governance profiles, full insights feed |
| **Policy Rules** | Responsible AI | KEYWORD/REGEX/SEMANTIC rule CRUD |
| **Alerts** | Responsible AI | Alert rules, history, email notifications |
| **Model Intelligence** | Intelligence | LLM comparison: latency, token economics, LLM-as-Judge, insights, usage share |

### AI Observability Tabs (11 total)
Activity Trend · Top Users · Model Usage · Tool Calls · Prompt Browser · Sessions · Token Economics · Tool Intelligence · Entrypoints · Quality Scores · Prompt Patterns

---

## Key Tables

| Table | Purpose | Populated by |
|---|---|---|
| `CC_PROMPT_EVENTS` | All prompts with 20+ columns: tokens, cache, steps, category, cost | SP_CC_CLASSIFY_PROMPTS (nightly) |
| `CC_PROMPT_VIOLATIONS` | Policy violations per prompt | SP_CC_CLASSIFY_PROMPTS (nightly) |
| `CC_PROMPT_ANALYSIS_DAILY` | Per-user daily risk aggregation | SP_CC_CLASSIFY_PROMPTS (nightly) |
| `CC_USAGE_DAILY_SUMMARY` | Credits/tokens/queries by user+surface+date | SP_CC_REFRESH_USAGE_SUMMARIES (30min) |
| `CC_RESPONSE_QUALITY` | LLM-as-Judge scores (4 dimensions) | SP_CC_EVALUATE_RESPONSES (on demand) |
| `CC_POLICY_RULES` | Rule definitions (8 system defaults + custom) | Admin UI / seeded |
| `CC_ALERT_CONFIG` | Alert thresholds | Admin UI / seeded |
| `CC_APP_CONFIG` | All app settings (key-value) | Phase B seed |
| `CC_MODEL_CONFIG` | Model tier assignments | Phase D3 seed |
| `CC_CREDIT_CONFIG` | Credit limits per cohort/user | Credit Configuration page |

### CC_PROMPT_EVENTS — key columns
`MODEL`, `PROMPT`, `RESPONSE`, `LATENCY_MS`, `STATUS`, `REQUEST_ID`, `TOTAL_TOKENS`, `INPUT_TOKENS`, `OUTPUT_TOKENS`, `CACHE_READ_TOKENS`, `CACHE_WRITE_TOKENS`, `STEP_NUMBER`, `ENTRYPOINT`, `PRIVATE_MODE`, `PROMPT_CATEGORY`, `PROMPT_COST_CREDITS`
Clustered by `EVENT_DATE` for fast date-range queries at 50K+ users.

---

## Stored Procedures

| SP | Created by | Purpose |
|---|---|---|
| `SP_CC_REFRESH_USAGE_SUMMARIES` | Phase A | Incremental usage/credit aggregation from ACCOUNT_USAGE |
| `SP_CC_CLASSIFY_PROMPTS(LOOKBACK_HOURS)` | Phase C | See detailed steps below |
| `SP_CC_CHECK_ALERTS(MODE)` | Phase C | Batch + real-time alert evaluation with HTML email |
| `SP_CC_EVALUATE_RESPONSES(BATCH_SIZE, EVAL_MODEL)` | Phase C | LLM-as-Judge: 4 evaluation dimensions |

### SP_CC_CLASSIFY_PROMPTS — Steps
1. Load new spans from AI_OBSERVABILITY_EVENTS (watermark-based, write_pandas — never in query history)
2. **SQL KEYWORD classification** — `FLATTEN(CONDITIONS:keywords)` + `CONTAINS()` — single Snowflake query, scales to 50K users (replaced Python loops)
3. REGEX classification — Python (session depth anomaly detection)
4. SEMANTIC classification — `AI_CLASSIFY` on unique prompt hashes
5. Count insights
6. MERGE `CC_PROMPT_ANALYSIS_DAILY`
6a-pre. **Mark system_internal prompts** — Cortex CLI commands (`cortex ctx task`, `cortex memory remember`, etc.) tagged as `system_internal` BEFORE AI_CLASSIFY runs
6a. **Category classification** — `AI_CLASSIFY` assigns 1 of 8 categories to uncategorised prompts. Dedup by SHA2 hash, batch 50, cap 5K/night
6b. **Cost attribution** — JOIN with `ACCOUNT_USAGE.CORTEX_CODE_*_USAGE_HISTORY` on REQUEST_ID → populate `PROMPT_COST_CREDITS`

---

## Analytics Concepts

### Token Economics
Data source: `CC_PROMPT_EVENTS` — extracted from `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` span attribute `snow.ai.observability.agent.planning.token_count.*` via `CodingAgent.Step-0` spans.

| Metric | What it is |
|---|---|
| **Input tokens** | Fresh prompt tokens processed from scratch — question, history, open files, tool definitions |
| **Output tokens** | Tokens the LLM *generated* in its response |
| **Cache Read tokens** | Tokens served from Snowflake's prompt cache — NOT re-processed, ~10× cheaper |
| **Cache Write tokens** | Tokens written INTO the cache for the first time |
| **Cache Hit Rate** | `cache_read / (cache_read + cache_write)` × 100. Higher = more credit savings. |

### Custom Quality (Experimental) (Snowflake AI Observability terminology)
| Metric | Definition |
|---|---|
| **Answer Relevance** | Did the LLM directly address what the user asked? (1.0 = fully answers) |
| **Groundedness** | Factually grounded without hallucinating code, APIs, or functions? (1.0 = no hallucination) |
| **Coherence** | Logically structured and clear? (1.0 = very clear) |
| **Safety** | Free from harmful content? (1.0 = fully safe) |

### Prompt Pattern Categories (AI_CLASSIFY — 8 types)
`sql_data_engineering`, `agent_automation`, `code_review_debug`, `data_migration`, `data_modeling`, `analytics_reporting`, `documentation`, `general`

### Policy Insight Categories
| Category | What triggers it | Risk |
|---|---|---|
| `PII_RISK` | SSN, credit cards, passport, bank account | HIGH |
| `SECURITY` | API keys, passwords, prompt injection, jailbreak, data exfiltration | HIGH |
| `COMPETITOR` | Databricks, BigQuery, Redshift, Synapse, etc. | MEDIUM |
| `USAGE_ANOMALY` | Session depth > threshold (automation/runaway agent) | MEDIUM |
| `PERSONAL_USE` | Entertainment, personal errands, social content | LOW |

### Composite Risk Score (User Intelligence)
`risk_score = min(1.0, (high_violations × 0.15) + (violation_rate × 0.02) + max(0, 0.7 - safety_score))`
Badges: ✅ Clean (< 0.25), ⚠️ Monitor (0.25–0.6), 🔴 Review (≥ 0.6)

---

## Common Questions & Answers

### "Why is Output tokens only 0.1%? Don't I get output for every input?"

Yes, you do get output for every input. The 0.1% is not wrong — it reflects the multi-step agent architecture:

1. The `LATENCY_MS` and token counts come from **`CodingAgent.Step-0` spans** — one span per **agent reasoning step**, not per full user interaction
2. Each Step-0 output = the planning decision for that step: "I'll use sql_execute tool" (~15 tokens) or "Let me read the file first" (~10 tokens)
3. These short planning outputs make output look tiny compared to input
4. The actual response the user reads spans multiple steps and is separately tracked in the `CodingAgentRun` span

**Expected distribution for Cortex Code:**
- Input: ~50% (fresh prompt tokens each step)
- Cache Read: ~35-40% (system prompts, skill context served from cache)
- Cache Write: ~10-15% (first-time caching)
- Output: ~0.1-2% (planning decisions per step)

This is normal and expected, not a data quality issue.

### "Is 37% Cache Read normal? Is high cache read common?"

37% cache hit rate is **excellent**. For Cortex Code specifically it is common and expected because:
- Every session has a large fixed system prompt (skill instructions, tool definitions, coding guidelines)
- These get cached after the first call and reused for all subsequent steps
- Users who ask many follow-up questions in one session get higher cache hit rates
- 37% means ~37% of all tokens were served at ~10× lower cost — real credit savings

**Rule of thumb:**
- > 20% cache hit: efficient, system is working well
- < 5% cache hit: something wrong — skills not loading, very short sessions

### "Why are my LLM-as-Judge scores so low (Answer Relevance: 0.22)?"

Low scores are NOT because of the judge model (llama3.1-70b). The root cause is **evaluating intermediate planning steps, not final answers**:

The SP was picking up ALL responses where `LENGTH > 20`, which includes:
- "I'll use the sql_execute tool to run this query" (15 tokens → scores 0.1 relevance correctly)
- "Let me read the file first" (8 tokens → same)

These are agent planning decisions, not user-facing answers. The judge correctly scores them low.

**Fix applied:** Filter `LENGTH(RESPONSE) > 200` + `ORDER BY STEP_NUMBER DESC` to only evaluate substantive final responses.

**Expected scores after fix:** 0.65–0.85 range for Answer Relevance, Groundedness, and Coherence. Safety stays ~1.0.

**To re-evaluate:** Truncate `CC_RESPONSE_QUALITY` and re-run D4 (Phase D → Run D4).

### "P95 is 22.52s and P50 is 6.38s — does it take 22s on average?"

No. The numbers mean:
- **P50 = 6.38s** — 50% of all LLM calls completed in 6.38s or less. This is the **typical user experience**.
- **P95 = 22.52s** — only the **slowest 5%** of calls exceed 22.52s. This is the worst-case threshold.

The "average" is much closer to P50 (~6-8s), not P95.

**Important nuance:** These are per-step latencies (one `CodingAgent.Step-0` span). A full user interaction has 3-5 steps:
- 3 steps × P50 (6.38s) ≈ 19-20 seconds total end-to-end
- This matches what users typically experience

**Large P95 gap is normal** for Cortex Code because:
- First call of session: cache is cold, all tokens processed fresh
- Complex reasoning steps with 50K+ token contexts take longer
- Multi-file operations add time
- Occasional model-side load spikes on Snowflake infrastructure

### "Insights show more than prompts — is that right?"

No — this was a **JOIN fan-out bug** that has been fixed. The old query joined `CC_PROMPT_EVENTS` with `CC_PROMPT_VIOLATIONS` on `USER_NAME + DATE`. One user with 100 prompts and 50 violations on the same date produced 100 × 50 = 5,000 counted violations.

**Fix:** Pre-aggregate insights per user+date with `COUNT(DISTINCT VIOLATION_ID)` in a CTE before joining to prompt events. After fix, insights should be a small fraction of prompts.

### "Where does the token data come from? Which event table?"

**Raw source:** `SNOWFLAKE.LOCAL.AI_OBSERVABILITY_EVENTS` — a Snowflake-managed event table automatically populated by Cortex Code. The token counts live in `RECORD_ATTRIBUTES`:

```sql
RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.token_count.input']::INT
RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.token_count.output']::INT
RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.token_count.cache_read_input']::INT
RECORD_ATTRIBUTES['snow.ai.observability.agent.planning.token_count.cache_write_input']::INT
```

Filter: `RECORD_TYPE = 'SPAN' AND RECORD:name::STRING = 'CodingAgent.Step-0'`

**Lineage:** AI_OBSERVABILITY_EVENTS → `SP_CC_CLASSIFY_PROMPTS` (nightly) → `CC_PROMPT_EVENTS` (typed columns) → Dashboard charts (aggregate queries)

The app never queries AI_OBSERVABILITY_EVENTS directly for dashboards — all reads go to `CC_PROMPT_EVENTS` (clustered, fast) or `CC_USAGE_DAILY_SUMMARY`.

### "Why does 'documentation' appear as the top prompt category?"

This happens when **system-injected Cortex CLI commands** get classified. Commands like:
- `cortex memory remember "prefer tabs over spaces"`
- `cortex ctx task add "Fix the bug"`
- `cortex_memory_remember something`

These look like documentation/instruction text to AI_CLASSIFY. The fix adds a `system_internal` pre-classification step (Step 6a-pre) that marks these before they reach AI_CLASSIFY.

To fix existing misclassified rows:
```sql
UPDATE CC_PROMPT_EVENTS
SET PROMPT_CATEGORY = 'system_internal'
WHERE PROMPT_CATEGORY IS NOT NULL
  AND PROMPT_CATEGORY != 'system_internal'
  AND (
      LOWER(PROMPT) ILIKE 'cortex ctx task %'
      OR LOWER(PROMPT) ILIKE 'cortex ctx step %'
      OR LOWER(PROMPT) ILIKE 'cortex memory remember%'
      OR LOWER(PROMPT) ILIKE '%cortex_memory_remember%'
  );
```

### "Phase C shows 4 SPs but only creates 3 — is something wrong?"

No. `SP_CC_REFRESH_USAGE_SUMMARIES` is created by **Phase A** (from `prerequisites.sql`), not Phase C. Phase C creates the 3 SPs defined in `sp_definitions.py`:
- `SP_CC_CLASSIFY_PROMPTS`
- `SP_CC_CHECK_ALERTS`
- `SP_CC_EVALUATE_RESPONSES`

The table in Phase C shows all 4 SPs with a "Created by" column to clarify this.

### "Setup Phase D — should I reload data after SP changes?"

The watermark in `SP_CC_CLASSIFY_PROMPTS` prevents re-loading events that already exist. Only new events are loaded on each run. But:
- **New columns (INPUT_TOKENS etc.)** on OLD rows stay NULL — watermark prevents re-processing
- **Categories (PROMPT_CATEGORY)** ARE backfilled on all rows where `PROMPT_CATEGORY IS NULL` — no watermark needed
- **Cost (PROMPT_COST_CREDITS)** IS backfilled on all rows where NULL

For full column population on old rows: truncate `CC_PROMPT_EVENTS` and re-run D2 with 180 days.

### "Can insights be more than prompts?"

No, that should never happen. If it does it's the JOIN fan-out bug (see above). Expected insight rates:
- Clean account: < 5 insights per 1,000 prompts
- Active policy enforcement: 10-50 per 1,000
- > 100 per 1,000 indicates data quality issue (likely fan-out bug)

---

## Data Privacy Design
- Prompts/responses never inserted as SQL VALUES literals (appear in QUERY_HISTORY)
- All bulk inserts use `session.write_pandas()` → COPY INTO (data not in query history)
- Private Mode: response not logged (NULL in RESPONSE column), shown with 🔒
- KEYWORD insights use `SHA2(PROMPT)` hash — only hash in Python, not prompt text

## Scale Design (50K users)
- `CC_PROMPT_EVENTS` clustered by `EVENT_DATE` — micro-partition pruning on all date queries
- All dashboard queries hit `CC_USAGE_DAILY_SUMMARY` (small aggregated) — never raw events
- Prompt Browser: mandatory date filter + hard LIMIT 5,000
- KEYWORD classification: SQL `FLATTEN + CONTAINS` (Snowflake-parallel, not Python loops)
- Category classification: 5K prompts/night cap, QUALIFY dedup by prompt hash

## Nightly Task Schedule
| Task | Schedule |
|---|---|
| `CC_REFRESH_USAGE_SUMMARIES` | Every 30 min |
| `CC_CLASSIFY_PROMPTS_TASK` | 2am UTC |
| `CC_DAILY_RESET_LIMITS` | Midnight UTC (only if credit limits configured) |
| `CC_ALERT_CHECK` | Every 5 min |
| `CC_REALTIME_VIOLATION_ALERT` | Every 1 min (stream-based, HIGH severity only) |

## Roles
| Role | Purpose |
|---|---|
| `CC_SP_OWNER_ROLE` | Owns all SPs. Has MANAGE GRANTS + ALTER USER. Never assumed by humans. |
| `CC_APP_ROLE` | Streamlit runtime. Can read/write CC_* tables and CALL all SPs. |
| `CC_ADMIN_ROLE` | Human admins. Has CC_APP_ROLE. Sees all pages. |
| `CC_USER_ROLE` | End users. Has CC_APP_ROLE. Sees Home + Credit Requests only. |

Admin page access controlled by `admin.roles` in `config.yaml`.

---

## Cortex AI Guardrails

Platform-level protection (Snowflake Horizon Catalog, Enterprise Edition) against prompt injection and jailbreak attacks on Cortex Code, Cortex Agents, and Snowflake Intelligence.

- **Where shown:** Home page metric card ("AI Guardrails"), AI Observability headline expander (auto-expands when disabled)
- **Detection:** `SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT` — checks for `enabled: true` in the YAML value
- **Enable SQL:** `ALTER ACCOUNT SET AI_SETTINGS = $$ guardrails: advanced_prompt_injection: - enabled: true $$;`
- **Requires:** Enterprise Edition + `CORTEX_ENABLED_CROSS_REGION = 'ANY'`
- **Cost:** Billed per token scanned (see Service Consumption Table)
- **Setup:** Setup page → Account Prerequisites → Step 6

---

## Native AI Budgets (Snowflake Preview)

Tag-based hard enforcement for Cortex Agent objects. Automates REVOKE USAGE when monthly spend reaches 100% of the configured limit.

- **How it differs from CoCo credit management:** CoCo = soft per-user daily limits (governance layer). Native Budgets = hard monthly cap on Cortex Agent objects (enforcement layer).
- **Scope:** Cortex Agent objects only — NOT general Cortex Code CLI/Snowsight usage
- **Enforcement lag:** Up to 8 hours standard, ~2 hours with low-latency option
- **Where shown:** Credit Configuration page → Native AI Budgets expander; Setup → Account Prerequisites → Step 7
- **Setup flow:** Create tag → apply to agent → create SNOWFLAKE.CORE.BUDGET → SET_SPENDING_LIMIT → SET_NOTIFICATION_THRESHOLD

---

## Cache Hit Rate Formula

**Correct formula:** `cache_read / (cache_read + cache_write)` × 100

- `cache_read` = tokens served from cache (hit) — charged at 0.1× base
- `cache_write` = tokens written to cache for first time (miss) — charged at 1.25× base
- `input_tokens` = fresh uncached tokens — NOT part of the cache system, excluded from formula
- This is the standard hits/(hits+misses) ratio used in all Deloitte/McKinsey observability frameworks
- **GPT models showing 100%:** If `cache_write = 0`, formula gives 100% — this is a data reporting artifact (GPT may not report write tokens separately), not a true hit rate

**Previous wrong formula (now fixed):** `cache_read / (cache_read + input)` — was diluting the ratio by including unrelated input tokens.

---

## Terminology Guide (Enterprise-Friendly)

| Old term | New term | Why |
|---|---|---|
| Violations | Prompt Insights | Governance framing, not punitive |
| Violation Rate | Insight Rate | Same |
| Risk Dashboard | Governance Dashboard | Deloitte/Bain standard |
| Risk Profile | Governance Profile | Same |
| High/Medium/Low Risk | High/Medium/Low Severity | Standard ITSM/SOC language |
| LLM-as-Judge Evaluation | Custom Quality (Experimental) | Honest about limitations |

---

## Account Prerequisites (Setup Page — 7 Steps)

Before running Phases A–E, admins must run these one-time account-level grants:

1. **Cross-Region Inference** — `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY'`
2. **AI Observability Access** — `GRANT DATABASE ROLE SNOWFLAKE.AI_OBSERVABILITY_READER TO ROLE CC_SP_OWNER_ROLE`
3. **ACCOUNT_USAGE Access** — `GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CC_SP_OWNER_ROLE`
4. **Model Access for Users** — `GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE CC_USER_ROLE`
5. **Credit Limits** _(optional)_ — `ALTER ACCOUNT SET CORTEX_CODE_CREDIT_LIMIT = N`
6. **AI Guardrails** _(optional, Enterprise)_ — `ALTER ACCOUNT SET AI_SETTINGS = $$ guardrails: ... $$`
7. **Native AI Budgets** _(optional, Preview)_ — tag-based budget enforcement

Setup page shows copy-paste SQL for each. Status chips show ✓ green (done) / ⚠ amber (not yet configured). Red only for explicitly wrong values.

---

## config.yaml Defaults

```yaml
deployment:
  database: ""    # Leave blank → uses CURRENT_DATABASE()
  schema: ""      # Leave blank → uses CURRENT_SCHEMA()

admin:
  roles:
    - ACCOUNTADMIN
    # Add customer's own admin role here
```

Never hardcode YOUR_DB or YOUR_SCHEMA — those are the developer's personal account values.


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

Surface (CLI / SNOWSIGHT / DESKTOP) comes from the `CodingAgentRun` span in `AI_OBSERVABILITY_EVENTS`:

```sql
-- Primary field (populated for CLI/Desktop)
snow.ai.observability.agent.coding_agent.entrypoint  -> CLI / DESKTOP

-- Fallback for Snowsight (entrypoint is NULL but client_type is set)
snow.ai.observability.agent.coding_agent.client_type
  codingagent_snowsight   -> SNOWSIGHT
  codingagent_snova       -> CLI
  codingagent_desktop     -> DESKTOP  (legacy)
  snowflake_coco_desktop  -> DESKTOP  (actual Desktop client_type as confirmed from enterprise accounts)
```

The SP uses `COALESCE(entrypoint, CASE client_type ...)` to handle both cases.
Requires Phase C re-run to take effect in new deployments.

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
