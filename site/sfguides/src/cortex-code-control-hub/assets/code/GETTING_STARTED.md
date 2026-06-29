# CoCo Control Hub — AI Deployment Starter Prompt

Copy and paste the text below into your AI assistant (Cortex Code, Claude, or any LLM).
Point it to the folder containing the app code and these skills.
The AI will ask you questions and guide you through the full deployment.

---

## How to Use

1. Make sure your AI has access to the skills in the `skills/` folder
2. Copy the prompt below
3. Paste it into your AI session
4. Answer the questions the AI asks — it will do the rest

If you are using Cortex Code CLI:
```bash
# Add the skills so CoCo knows about them
cortex skill add skills/coco-hub-knowledge
cortex skill add skills/coco-hub-deploy

# Start a session
cortex
```

Then paste the starter prompt.

---

## IMPORTANT — Before You Start

**The code in this folder must NOT be modified.**

The only two files you are allowed to edit are:
- `snowflake.yml` — deployment target (database, schema, warehouse, optional SPCS settings)
- `config.yaml` — admin roles and data schema location

Everything else — all `.py` files, `prerequisites.sql`, `streamlit_app.py` — must stay exactly as provided. All configuration happens through the app's built-in Setup page after deployment.

---

## Starter Prompt (copy everything below this line)

---

I want to deploy CoCo Control Hub (Cortex Code Credit Manager) in my Snowflake account.

The app code is in this folder. Please use the `coco-hub-deploy` skill to guide me through the deployment.

Before we start, here is what I need you to know:

1. **Do NOT modify any source code files.** The only files you may change are `snowflake.yml` and `config.yaml`. All other files — `sp_definitions.py`, `config.py`, `prerequisites.sql`, `streamlit_app.py`, and all files in `pages/` — must be deployed exactly as they are.

2. **Ask me questions first** before making any changes. I need to tell you:
   - Whether I want Streamlit on Warehouse or Streamlit on Container (SPCS)
   - Which database and schema to deploy the app into
   - Which warehouse to use
     > **Warehouse sizing recommendation:** An **X-Small (XS)** warehouse is sufficient for all setup phases and the two overnight scheduled tasks (`CC_CLASSIFY_PROMPTS_TASK`, `CC_REFRESH_USAGE_SUMMARIES`). For the app query warehouse, use **Small (S)** or larger if you have many concurrent users. Set `AUTO_SUSPEND = 300` to avoid constant cold-start delays.
   - Whether I will use ACCOUNTADMIN or a custom role for deployment
   - Which roles should have admin access to the app

3. **If I am using a custom role** (not ACCOUNTADMIN), please show me all the SQL grants I need to run first, including:
   - Schema and database access
   - Streamlit and stage creation
   - Account-level privileges (CREATE INTEGRATION, CREATE TASK, EXECUTE TASK, CREATE ALERT, MANAGE GRANTS)
   - ACCOUNT_USAGE access (IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE)
   - AI Observability reader (SNOWFLAKE.AI_OBSERVABILITY_READER database role)
   - SPCS compute pool access (if applicable)

4. After deployment, guide me through the 7-step Account Prerequisites (shown in Setup page), then Phases A through E in the correct order.

5. After setup, remind me to resume the nightly tasks and configure email alerts.

Please start by asking me the deployment questions.

---

## What This App Does

CoCo Control Hub is a governance dashboard for Cortex Code usage in Snowflake. It gives admins:
- Credit usage visibility and limits per user, cohort, and surface (CLI/Snowsight/Desktop)
- AI Observability: prompt patterns, token economics, cache efficiency, latency, surface split
- **Cortex AI Guardrails** status monitoring (Enterprise — prompt injection + jailbreak protection)
- **Native AI Budgets** (Preview) — hard enforcement via tag-based Snowflake budgets
- Responsible AI: keyword/regex/semantic policy classification with HIGH/MEDIUM/LOW severity
- Custom Quality Evaluation _(Experimental)_: configurable LLM judge for Answer Relevance, Coherence, Safety
- User Governance Profiles: per-user full profile with prompt search and governance score
- Alert system with HTML email notifications

For questions about what the app does or how any feature works, use the `coco-hub-knowledge` skill.

