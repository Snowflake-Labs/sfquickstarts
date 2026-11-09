author: James Cha-Earley
id: getting-started-with-cortex-sense
language: en
summary: Build a Cortex Sense context over a synthetic health-system warehouse and measure how it changes agent answers on questions that depend on house definitions.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/industry/healthcare-and-life-sciences
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex Sense, Cortex Code, CoCo, Cortex Agents, AI, Semantic Views, Healthcare
fork repo link: https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense

# Getting Started with Cortex Sense

<!-- ------------------------ -->
## Overview

Cortex Sense builds a working model of your business from metadata your account already produces: query history, semantic views, dashboards, table metadata, and documents on a stage. Cortex Agents and Cortex Code (CoCo) then use that context to answer questions accurately.

The gap it closes is a specific one. An agent with full access to your tables can usually find the right columns and work out the joins. What it can't find is the stuff that lives outside the schema: what your team means by "clean claim", which admissions a readmission rate excludes, what an internal program name refers to, or what your data release policy says. When it has to guess at those, it usually gives you a confident, plausible, wrong answer.

In this guide you work with **Juniper Valley Health**, a fictional health system. Its analytics warehouse has 8 tables and about 16,000 synthetic rows covering facilities, patients, encounters, claims, denials, readmissions, and patient surveys. Its business definitions live where they would at a real organization: in internal docs, saved queries, and a dashboard. You ask an agent the same questions without and with a Cortex Sense context, as the same analyst role, and compare the answers.

> **Private Preview:** Cortex Sense is in private preview. Your account must be enrolled before you can follow this guide. If it isn't, contact your account team.

### Prerequisites
- A Snowflake account enrolled in the Cortex Sense private preview
- A user who can use the `ACCOUNTADMIN` role
- Basic familiarity with Cortex Code CLI and SQL

### What You'll Learn
- How Cortex Sense differs from a semantic view, and when each one does the work
- How to scope, build, and check a Cortex Sense context with the `/sense` command
- How to measure an agent without and with context on the same questions
- How to grant a context to another role

### What You'll Need
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli), version 1.1.94 or later. This guide uses the CLI's `/sense` page throughout; CoCo Desktop doesn't have that page yet.
- A Snowflake CLI connection to your account in `~/.snowflake/connections.toml`

### What You'll Build
- A health-system warehouse with its business definitions kept in a separate knowledge schema
- A Cortex Sense context named `juniper_health` that indexes those definitions
- A side-by-side comparison of agent answers without and with that context

<!-- ------------------------ -->
## Run the Setup Script

All of the demo's data, docs, saved queries, and dashboard are in the public [companion repository](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense). One SQL script loads them straight from GitHub through Snowflake's Git integration, so there's nothing to clone or install.

1. In Snowsight, open a new SQL worksheet.
2. Copy the contents of [`setup.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/setup.sql) into the worksheet.
3. Run all of it.

The script starts as `ACCOUNTADMIN`. Its first grant gives the `SNOWFLAKE.CORTEX_SENSE_BUILDER` database role to a new demo role. If your account isn't enrolled in the preview, the script stops there, after creating only the two empty demo roles.

When it finishes, the last result shows one row per check. Every row should say `PASS`. The script is idempotent, so if something fails, fix the cause and run it again. Don't re-run it after you've built the context, though: it recreates the tables and semantic views the context indexed.

### What setup created

| Object | Purpose |
|---|---|
| `JUNIPER_BUILDER` role | Owns the demo and builds the Cortex Sense context |
| `JUNIPER_ANALYST` role | Can read the `ANALYTICS` schema only. You'll ask all your questions as this role. |
| `JUNIPER_WH` warehouse | XSMALL, auto-suspends after 60 seconds |
| `JUNIPER_GITHUB` API integration | Read-only access to the companion repository |
| `JUNIPER_HEALTH.ANALYTICS` | The 8 tables and the `CLAIMS_SV` semantic view analysts use today |
| `JUNIPER_HEALTH.KNOWLEDGE` | `KNOWLEDGE_STAGE` (internal docs and saved queries), `STREAMLIT_STAGE` and the `OPERATIONS_DASHBOARD` Streamlit app, the certified `CLAIMS_SV_CERTIFIED` semantic view, and its support view `CLAIMS_WITH_DENIAL_FLAG` |
| `JUNIPER_HEALTH.SENSE` | Empty. The Cortex Sense context goes here. |

Both demo roles are granted to your user, and deliberately not to `SYSADMIN`, so no other role inherits access to the context. Setup also runs the four saved queries once, so they show up in query history the way they would at a real organization. At the end it drops its temporary `SETUP` schema, which held the Git repository clone, because the clone includes the answer key.

<!-- ------------------------ -->
## Create the CoCo Connections

You'll run two CoCo sessions: one as `JUNIPER_BUILDER` to build the context, and one as `JUNIPER_ANALYST` to ask questions. Give each its own connection, so the analyst session can never pick up the builder's privileges by accident.

Open `~/.snowflake/connections.toml`, copy the block for the connection you normally use, and add two new blocks that differ only in name, role, and warehouse. For example, if your connection uses browser SSO:

```toml
[juniper_builder]
account = "<your_account>"
user = "<your_user>"
authenticator = "externalbrowser"
role = "JUNIPER_BUILDER"
warehouse = "JUNIPER_WH"

[juniper_analyst]
account = "<your_account>"
user = "<your_user>"
authenticator = "externalbrowser"
role = "JUNIPER_ANALYST"
warehouse = "JUNIPER_WH"
```

Keep whatever authentication settings your existing connection uses. You start each session with `cortex -c <connection>`, then type `/settings` and confirm that both **Inference Connection** and **SQL Connection** point at that same connection.

<!-- ------------------------ -->
## Explore the Demo

Before building anything, look at how the demo is arranged. The arrangement is what makes the comparison fair.

| Schema | Holds | Who can read it |
|---|---|---|
| `ANALYTICS` | Tables whose comments describe grain and column meaning only, plus `CLAIMS_SV`, whose `clean_claims` metric is the outdated definition | `JUNIPER_BUILDER` and `JUNIPER_ANALYST` |
| `KNOWLEDGE` | Every current definition, exclusion rule, program criterion, and threshold | `JUNIPER_BUILDER` only |

`JUNIPER_ANALYST` has the tables but not the definitions. Without Cortex Sense, an agent running as that role is in the same position as a capable new analyst on their first day.

### See a definition gap in SQL

Both semantic views have a `clean_claims` metric. The one in `ANALYTICS` counts claims accepted on first submission. The certified one in `KNOWLEDGE` also requires the claim to be paid and never denied. Run them side by side in your Snowsight worksheet:

```sql
USE ROLE JUNIPER_BUILDER;
USE WAREHOUSE JUNIPER_WH;
USE DATABASE JUNIPER_HEALTH;

-- What analysts have today
SELECT * FROM SEMANTIC_VIEW(ANALYTICS.CLAIMS_SV
  METRICS clean_claims, total_claims
  DIMENSIONS payer_name)
ORDER BY clean_claims / total_claims DESC;

-- What the Metrics Glossary defines
SELECT * FROM SEMANTIC_VIEW(KNOWLEDGE.CLAIMS_SV_CERTIFIED
  METRICS clean_claims, total_claims
  DIMENSIONS payer_name)
ORDER BY clean_claims / total_claims DESC;
```

The first view puts UnitedHealthcare at the top. The second puts it last. Nothing an analyst can read tells them which reading is right.

### Look at where the definitions live

```sql
LIST @JUNIPER_HEALTH.KNOWLEDGE.KNOWLEDGE_STAGE;
```

Under the `markdown/` prefix are four internal docs: `Metrics_Glossary.md`, `BEACON_Facility_Designation.md`, `Project_Tailwind.md`, and `External_Data_Release_Policy.md`. Under `query-history/` are the four saved queries that implement them.

To see the dashboard, switch your Snowsight role to `JUNIPER_BUILDER` and open **Juniper Valley Health operations** under **Projects » Streamlit**.

The docs teach definitions and deliberately state no answers, so an agent with context still has to compute every number.

<!-- ------------------------ -->
## Build the Cortex Sense Context

Starting the build now lets it run in the background while you collect baseline answers in the next step.

> **One context per role:** During private preview, give each role access to a single context. A query that isn't scoped to named contexts searches every context the role can reach. The demo roles are new, so this holds as long as you don't grant them other contexts.

### Start a new context

Start a builder session and open the Cortex Sense page:

```bash
cortex -c juniper_builder
```

Type `/sense`, choose **+ Start a new Cortex Sense object**, and follow the prompts. CoCo scans your account and proposes a scope. Refine it in plain language until it matches this:

```
Name the context juniper_health and create it in JUNIPER_HEALTH.SENSE.
Include exactly these sources:

- Table and column metadata for JUNIPER_HEALTH.ANALYTICS.*
- The semantic view JUNIPER_HEALTH.KNOWLEDGE.CLAIMS_SV_CERTIFIED, and no other semantic view
- Query history, looking back 30 days
- The markdown docs and saved SQL files on the stage
  JUNIPER_HEALTH.KNOWLEDGE.KNOWLEDGE_STAGE, under markdown/ and query-history/
- The Streamlit app JUNIPER_HEALTH.KNOWLEDGE.OPERATIONS_DASHBOARD

Don't include anything else from JUNIPER_HEALTH.KNOWLEDGE.
```

Two of these rules matter more than they look:

- **No wildcard over `KNOWLEDGE`.** The semantic view source names exactly one object in that schema.
- **Only the certified semantic view.** `ANALYTICS.CLAIMS_SV` is what the analyst sees without context. Indexing it as a definition would teach Cortex Sense the wrong one.

CoCo may ask about inputs it can't detect, such as a dbt project or BI tool. This demo has none, so skip them.

### Confirm and let it run

When the scope looks right, confirm it:

```
looks good
```

Indexing starts only after you confirm, and the build takes a few hours. Leave this session open and move on to the baseline.

CoCo also lets you give it facts while it builds. Don't do that in this demo. Telling it a definition yourself would skip the very thing you're measuring.

Scheduled refresh isn't implemented yet during private preview, so a context reflects its sources as they were when it was built.

> **Cost:** Builds are billed at the same rates as `AI_COMPLETE` and scale with scope. Most early-preview customers spent fewer than 1,000 credits on an initial build, and small demo setups cost much less. During private preview you can't pick a warehouse or set a credit cap. Build credits appear in `CORTEX_AI_FUNCTIONS_USAGE_HISTORY`.

<!-- ------------------------ -->
## Ask Baseline Questions

Now record what an agent answers without Cortex Sense. A new context has only one grant, `OWNERSHIP` for the builder role, so the analyst role can't reach it yet. **Finish this step before you grant the analyst role access** in a later step.

Open a second terminal. Start the session from an empty directory, so the agent has no local files to read:

```bash
mkdir -p ~/juniper-analyst && cd ~/juniper-analyst
cortex -c juniper_analyst
```

Set the ground rules first:

```
You are a data analyst at Juniper Valley Health. Before anything else, run
USE SECONDARY ROLES NONE; then show me
SELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES().
Answer my questions from the JUNIPER_HEALTH.ANALYTICS schema only. Don't use any
Cortex Sense tooling, don't read query history, don't search the web, don't read
local files, and don't search past conversations. If you have to guess a
definition, say so.
```

Check that the role is `JUNIPER_ANALYST` and that `CURRENT_SECONDARY_ROLES()` comes back empty before you continue. Many users have all their roles active as secondary roles by default, which would quietly give the analyst session your builder privileges.

The query history rule closes the one gap roles can't. Query history shows a user every query they ran, whatever role is active, and you ran setup yourself, so the analyst session could read the definitions straight out of setup's statements.

Start with the two routine questions, which the schema can answer on its own:

```
What is our overall denial rate?
```

```
Which facilities participate in the ACO?
```

Expect **12.1%** (379 distinct denied claims of 3,131) and five facilities. Now ask the five questions that depend on house definitions, one at a time, and write down each answer:

1. `What's our clean claim rate by payer?`
2. `Show me our 30-day readmission rate`
3. `Which facilities have the BEACON designation?`
4. `What's our Tailwind rate?`
5. `An external benchmarking partner wants our facility-level 30-day readmission rates. Can I send them, and what do I have to do first?`

Here's what the schema alone leads to:

| Question | The tempting answer |
|---|---|
| Clean claim rate | `submission_count = 1` alone gives **88.0%**, with UnitedHealthcare best at 92.5% |
| Readmission rate | Unplanned readmissions over all 984 inpatient encounters gives **20.8%**, above the 18% that Juniper Valley Health treats as CMS penalty territory |
| BEACON | No answer. The word appears nowhere the analyst can read. |
| Tailwind rate | No answer, since the program name appears nowhere. An agent that guesses "claims within 24 hours" across all facilities gets **49.7%**. |
| External release | A generic yes, usually with advice to get a BAA |

Your agent's wording and numbers may differ. What you should see is an agent that gets the routine questions right and these ones wrong or unanswered.

Exit this session when you're done.

<!-- ------------------------ -->
## Check the Build

Back in the builder session, type `/sense` to open the Cortex Sense page and pick `juniper_health`, or go straight to it with `/sense juniper_health`. `Tab` moves between tabs and `?` lists the keys.

| Tab | What to look for |
|---|---|
| **Overview** | Build state, eval score, and per-source progress |
| **Scope** | The five sources from the build step, and nothing else from `KNOWLEDGE` |
| **Inbox** | Corrections to what Cortex Sense believes about the data. `1` to `3` filter, `A` approves, `E` edits. |
| **Accuracy** | Eval results, including lift over the pre-context baseline |
| **Activate** | Options for using the context in an agent or a CoCo skill |

A **ready** state means the build finished, not that every source succeeded. Check per-source progress on **Overview** before you test anything, and note the context's exact name there. Don't create or change objects in `JUNIPER_HEALTH.SENSE` by hand, since that can corrupt the context.

<!-- ------------------------ -->
## Ask Again with Cortex Sense

### Grant the analyst role access

Querying a context needs only `USAGE` on it. Grant it from a Snowsight worksheet, keeping the quotes around the context name. If **Overview** showed a different name or case, use that:

```sql
USE ROLE JUNIPER_BUILDER;
GRANT USAGE ON CORTEX SENSE JUNIPER_HEALTH.SENSE."juniper_health" TO ROLE JUNIPER_ANALYST;
SHOW GRANTS ON CORTEX SENSE JUNIPER_HEALTH.SENSE."juniper_health";
```

`SHOW GRANTS` reports the object type as `CORTEX_CONTEXT`, which is how `CORTEX SENSE` objects are reported back.

`JUNIPER_ANALYST` still can't read the `KNOWLEDGE` schema. Any definition it uses from here on has to come through the context.

### Activate the context

In the builder session, open the **Activate** tab. You have two options:

- **CoCo serving skill:** generates a skill that queries this context from CoCo. Follow the prompts on the tab to generate and install it. Anyone who uses it also needs `USAGE` on the context, which you just granted.
- **Cortex Agent:** creates an agent that uses this context, or adds the context to an existing agent. CoWork runs on Cortex Agents, so it uses the same context. Access to an agent is separate from access to its context, so if you go this way, also grant `USAGE` on the agent to `JUNIPER_ANALYST`.

### Ask the same questions

For the serving skill, start a new analyst session from the same empty directory:

```bash
cd ~/juniper-analyst
cortex -c juniper_analyst
```

Set the ground rules again, this time pointing at the context:

```
You are a data analyst at Juniper Valley Health. Before anything else, run
USE SECONDARY ROLES NONE; then show me
SELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES().
Use the juniper_health Cortex Sense context for definitions, and compute every
answer against the tables in JUNIPER_HEALTH.ANALYTICS. Don't read query history,
search the web, read local files, or search past conversations.
```

Ask the same five questions. Here are the correct answers, so you can check what comes back:

| Question | Correct answer | Where the definition lives |
|---|---|---|
| Clean claim rate | **63.9%** (2,001 of 3,131). A claim is clean only if it was accepted on first submission, is `Paid`, and has no denial. UnitedHealthcare drops from first to last, at 54.2%. | `Metrics_Glossary.md`, `clean_claim_rate_by_payer.sql` |
| Readmission rate | **10.5%** (62 of 590 eligible index admissions), well below 18%. The base is inpatient stays that weren't cancelled and have a discharge date. Patients under 18 and obstetric admissions leave the denominator. The numerator counts only unplanned readmissions within 30 days whose index admission is eligible. | `Metrics_Glossary.md` |
| BEACON | **One facility:** Summit Orthopedic Hospital. BEACON stands for Balanced Excellence Across Clinical Outcomes and Net revenue, and requires all three of an Experience Score of 85 or higher, a readmission rate below 8%, and a denial rate below 4%. Cedar Ridge Hospital misses only on readmission, and Willow Creek Hospital only on denial rate. | `BEACON_Facility_Designation.md` |
| Tailwind rate | **78.3%** (1,175 of 1,500), just under the 80% target. Project Tailwind counts claims submitted within 24 hours of discharge, at ACO facilities only, for completed encounters. | `Project_Tailwind.md`, `tailwind_rate_by_month.sql` |
| External release | **Not as-is.** It's a Tier 3 release with four conditions: facility-level aggregates only; suppress facilities with fewer than 20 eligible index admissions, which applies to 3 of the 8 reporting facilities; replace facility names with blinded codes; and get written approval from the Data Governance Council, allowing 10 business days. A BAA doesn't authorize the release. | `External_Data_Release_Policy.md` |

Some of these answers depend on each other. The release policy's suppression rule counts *eligible* index admissions, so an agent using the naive readmission definition suppresses none of the facilities when three must be suppressed. It also misses Willow Creek as a BEACON near miss.

The Tailwind question shows that scope can matter more than the formula. The same 24-hour calculation gives 49.7% across all facilities and 78.3% across the ACO facilities the program actually covers.

The release question is the one to remember. Without context, the other questions produce a wrong number or no answer. This one produces a wrong decision.

<!-- ------------------------ -->
## Improve the Context

### Record corrections

When an answer is wrong, tell CoCo what the right definition is. Corrections collect on the **Inbox** tab, where you approve or reject each one. Approved corrections take effect at query time, with no rebuild.

### Measure it with evals

The companion repository has all seven questions and their expected answers in [`evals/questions.yaml`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/evals/questions.yaml). To run them, open the **Accuracy** tab in the builder session, choose **+ Start a new evaluation run**, and give it those questions and answers. Cortex Sense runs them, reports which ones failed and why, and can update the context and re-run.

### Check the answers yourself

[`answer_key.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/answer_key.sql) computes every correct answer from the base tables. Run it only **after** you've finished comparing. Anything you run lands in query history, which the context reads the next time it's built. The same applies to the baseline's wrong answers, so rebuild the context only when you're done experimenting.

<!-- ------------------------ -->
## Clean Up

First remove what you created on the **Activate** tab: uninstall the serving skill, and drop any agent you created. Then delete the context. In the builder session, ask:

```
Delete the juniper_health Cortex Sense context in JUNIPER_HEALTH.SENSE.
```

Deleting a context is asynchronous. Check that it no longer appears on the `/sense` page before you continue.

Then run [`teardown.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/teardown.sql) in a Snowsight SQL worksheet. It drops the database as `JUNIPER_BUILDER`, then removes the warehouse, the API integration, and both demo roles as `ACCOUNTADMIN`.

Finally, delete the `juniper_builder` and `juniper_analyst` blocks from `~/.snowflake/connections.toml`, and the `~/juniper-analyst` directory.

<!-- ------------------------ -->
## Conclusion And Resources

You set up a health-system warehouse whose definitions live outside its schema. You recorded how an agent answers without that knowledge, built a Cortex Sense context over the docs, saved queries, dashboard, and certified semantic view where those definitions actually live, and asked the same questions again as the same role.

None of the context required new modeling work. It came from artifacts the organization had already produced. Semantic views remain the most precise path for domains you curate, and Cortex Sense covers the rest.

### What You Learned
- Why an agent with full table access still gets house-definition questions wrong
- How to scope a context so it indexes the right sources and nothing more
- How to build, check, and activate a context with `/sense`
- How to grant a context to another role and improve it with corrections and evals

### Related Resources
- [Get started with Cortex Sense](https://docs.snowflake.com/en/LIMITEDACCESS/cortex-sense)
- [Cortex Sense reference](https://docs.snowflake.com/en/LIMITEDACCESS/cortex-sense-reference)
- [Companion repository](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense)
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
