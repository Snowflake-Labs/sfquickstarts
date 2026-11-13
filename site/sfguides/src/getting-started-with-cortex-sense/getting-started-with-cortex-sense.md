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

An agent with full access to your tables can usually find the right columns and work out the joins. It can't find what sits outside the schema: what your team means by "clean claim", which admissions a readmission rate excludes, what an internal program name refers to, or what your data release policy says. When it has to guess at those, it usually answers anyway, and the answer looks right.

In this guide you work with **Juniper Valley Health**, a fictional health system. Its analytics warehouse has 8 tables and about 16,000 synthetic rows covering facilities, patients, encounters, claims, denials, readmissions, and patient surveys. As at a real organization, its business definitions are in internal docs, saved queries, and a dashboard. You ask an agent the same questions without and with a Cortex Sense context, as the same analyst role, and compare the answers.

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
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli), version 1.1.94 or later (this guide was tested with 1.2.44). This guide uses the CLI's `/sense` page throughout; CoCo Desktop doesn't have that page yet.
- A Snowflake CLI connection to your account in `~/.snowflake/connections.toml`

### What You'll Build
- A health-system warehouse with its business definitions kept in a separate knowledge schema
- A Cortex Sense context named `JUNIPER_HEALTH` that indexes those definitions
- A side-by-side comparison of agent answers without and with that context

<!-- ------------------------ -->
## Run the Setup Script

All of the demo's data, docs, saved queries, and dashboard are in the public [companion repository](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense). One SQL script loads them straight from GitHub through Snowflake's Git integration, so there's nothing to clone or install.

1. In Snowsight, open a new SQL worksheet.
2. Copy the contents of [`setup.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/setup.sql) into the worksheet.
3. Run all of it.

The script starts as `ACCOUNTADMIN` and grants the `SNOWFLAKE.CORTEX_SENSE_BUILDER` database role to a new demo role. That grant succeeds whether or not your account is enrolled in the preview, so setup can't tell you. Enrollment is checked when `/sense` runs its pre-flight checks. In an account that isn't enrolled, Snowflake reports that Cortex Context Builder is not enabled for this account.

When it finishes, the last result shows one row per check. Every row should say `PASS`. The script is idempotent, so if something fails, fix the cause and run it again. Don't re-run it after you've built the context, though: it recreates the tables and semantic views the context indexed.

### Objects created by setup

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

Keep whatever authentication settings your existing connection uses. If you sign in with a programmatic access token that's restricted to one role, it can't use these roles; create a token without a role restriction, or use key-pair authentication.

`cortex -c <connection>` sets only the SQL connection. CoCo's **Agent Connection** (called **Inference Connection** in `/settings` and the docs) comes from your settings, so pin both for each role with a project-level settings file in its own working directory:

```bash
mkdir -p ~/juniper-builder/.cortex ~/juniper-analyst/.cortex

cat > ~/juniper-builder/.cortex/settings.json <<'EOF'
{ "cortexAgentConnectionName": "juniper_builder", "sqlConnectionName": "juniper_builder" }
EOF

cat > ~/juniper-analyst/.cortex/settings.json <<'EOF'
{ "cortexAgentConnectionName": "juniper_analyst", "sqlConnectionName": "juniper_analyst" }
EOF
```

From here on, start each session from its own directory. The header shows **Agent Connection** and **SQL Connection**; check that both name the same connection before you go on. The project-level files leave your global CoCo settings unchanged.

<!-- ------------------------ -->
## Explore the Demo

The comparison is fair because of how access is split between the two schemas:

| Schema | Holds | Who can read it |
|---|---|---|
| `ANALYTICS` | Tables whose comments describe grain and column meaning only, plus `CLAIMS_SV`, whose `clean_claims` metric is the outdated definition | `JUNIPER_BUILDER` and `JUNIPER_ANALYST` |
| `KNOWLEDGE` | Every current definition, exclusion rule, program criterion, and threshold | `JUNIPER_BUILDER` only |

`JUNIPER_ANALYST` can query every table but can't read any of the current definitions.

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

### Browse the knowledge stage

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

Start a builder session from the builder directory:

```bash
cd ~/juniper-builder
cortex -c juniper_builder
```

Type `/sense` and choose **+ Start a new Cortex Sense object**. A short wizard follows:

1. **Name:** type `juniper_health`.
2. **Scope:** paste this as a single line. A line break would submit it early.

   ```
   Create it in JUNIPER_HEALTH.SENSE. Include exactly these sources: table and column metadata for JUNIPER_HEALTH.ANALYTICS.*; the semantic view JUNIPER_HEALTH.KNOWLEDGE.CLAIMS_SV_CERTIFIED and no other semantic view; query history looking back 30 days; the markdown docs and saved SQL files on the stage JUNIPER_HEALTH.KNOWLEDGE.KNOWLEDGE_STAGE under markdown/ and query-history/; and the Streamlit app JUNIPER_HEALTH.KNOWLEDGE.OPERATIONS_DASHBOARD. Don't include anything else from JUNIPER_HEALTH.KNOWLEDGE.
   ```

3. The wizard puts a `$cortex-sense create ...` message in the composer. Read it over and press Enter.

The `cortex-sense` skill takes over. It runs pre-flight checks and asks permission to run its bundled scripts and some `SHOW` queries, all as `JUNIPER_BUILDER`. Then it shows the proposed scope:

| Source | Expected |
|---|---|
| Tables | `JUNIPER_HEALTH.ANALYTICS.*`, 8 tables |
| Semantic views | `JUNIPER_HEALTH.KNOWLEDGE.CLAIMS_SV_CERTIFIED` only |
| Streamlit apps | `JUNIPER_HEALTH.KNOWLEDGE.OPERATIONS_DASHBOARD` |
| Files | `KNOWLEDGE_STAGE/markdown/` and `KNOWLEDGE_STAGE/query-history/` |
| Excluded | `JUNIPER_HEALTH.KNOWLEDGE.*`, which keeps out the support view `CLAIMS_WITH_DENIAL_FLAG` |

Query history doesn't appear in the box; the skill says it's handled internally. The skill may also say it can't confirm the `.sql` files will be indexed, since only text and markdown files are documented as supported. Every definition is also in the markdown docs, so the answers don't depend on them. Be strict about the semantic view source. `ANALYTICS.CLAIMS_SV` is what the analyst sees without context, and indexing it as a definition would teach Cortex Sense the wrong one.

The skill also stores the name in upper case, `JUNIPER_HEALTH`, unless you ask it to keep it lowercase. The rest of this guide uses `JUNIPER_HEALTH`.

### Confirm and let it run

The skill asks who else should get processing-failure notifications. Reply `just me`. Then:

1. Type `build` to approve the scope and notification setup.
2. The skill drafts a description that agents read to decide when to use this context. Type `yes` to accept it, or type your own.

The skill saves the context as `JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH` and queues the build. The skill runs its queries as `JUNIPER_BUILDER`, the build role, which is fixed for the life of the context. The summary also names a warehouse (`JUNIPER_WH`), which you can change with `use warehouse <name>`; the indexing itself is billed as AI credits (see Cost below). The docs say builds take a few hours; this small scope finished in about 10 minutes in our test. Leave this session open and move on to the baseline.

CoCo also accepts facts from you while it builds. Don't give it any here: if you tell it a definition, the comparison no longer measures what it learned from the sources.

Scheduled refresh isn't implemented yet during private preview, so a context reflects its sources as they were when it was built.

> **Cost:** Builds are billed at the same rates as `AI_COMPLETE` and scale with scope. Most early-preview customers spent fewer than 1,000 credits on an initial build, and small demo setups cost much less. You can't set a credit cap during private preview. Build credits appear in `CORTEX_AI_FUNCTIONS_USAGE_HISTORY`.

<!-- ------------------------ -->
## Ask Baseline Questions

Now record what an agent answers without Cortex Sense. A new context has only one grant, `OWNERSHIP` for the builder role, so the analyst role can't reach it yet. **Finish this step before you grant the analyst role access** in a later step.

Open a second terminal and start the analyst session from its directory, which holds nothing but its settings file:

```bash
cd ~/juniper-analyst
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

Check that the role is `JUNIPER_ANALYST` and that `CURRENT_SECONDARY_ROLES()` comes back empty before you continue. For a stronger check, ask the agent to select from `JUNIPER_HEALTH.KNOWLEDGE.CLAIMS_WITH_DENIAL_FLAG`; it should get "does not exist or not authorized". Many users have all their roles active as secondary roles by default, which would give the analyst session your builder privileges.

Roles can't hide query history. It shows a user every query they ran under any role, and you ran setup yourself, so without the query history rule in the prompt, the analyst session could read the definitions out of setup's statements.

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

Answers an agent tends to reach from the schema alone:

| Question | The tempting answer |
|---|---|
| Clean claim rate | `submission_count = 1` alone gives **88.0%**, with UnitedHealthcare best at 92.5% |
| Readmission rate | Unplanned readmissions over inpatient stays gives **about 20%**: 20.3% (191 of 941 completed stays) in our baseline run, or 20.8% (205 of all 984), above the 18% that Juniper Valley Health treats as CMS penalty territory |
| BEACON | No answer. The word appears nowhere the analyst can read. |
| Tailwind rate | No answer, since the program name appears nowhere. An agent that guesses "claims within 24 hours" across all facilities gets **49.7%**. |
| External release | Generic advice: privacy sign-off, a BAA, and the common HHS small-cell threshold of 11. Applied to readmission counts, that threshold suppresses the wrong facilities, and the Data Governance Council never comes up. |

Your agent's wording and numbers may differ. What you should see is an agent that gets the routine questions right and these ones wrong or unanswered.

Exit this session when you're done.

<!-- ------------------------ -->
## Check the Build

Back in the builder session, type `/sense` and pick `JUNIPER_HEALTH` from the list. `Tab` moves between tabs and `?` lists the keys.

| Tab | What to look for |
|---|---|
| **Overview** | Build state (**ready**), sources (**5 of 5**), accuracy, inbox, notification contacts, who has access, and suggested questions to try |
| **Scope** | The sources from the build step, and nothing else from `KNOWLEDGE` |
| **Inbox** | Corrections to what Cortex Sense believes about the data. `1` to `3` filter, `A` approves, `E` edits. |
| **Accuracy** | Eval results, including lift over the pre-context baseline |
| **Activate** | Ways to serve the context: a CoWork agent, an existing agent, or a CoCo skill |

A **ready** state means the build finished, not that every source succeeded, so check the source count on **Overview**. Its suggested questions are a quick sign of what the build picked up: they should mention the readmission threshold, BEACON, and the Tailwind target. Don't create or change objects in `JUNIPER_HEALTH.SENSE` by hand, since that can corrupt the context.

<!-- ------------------------ -->
## Ask Again with Cortex Sense

### Grant the analyst role access

The docs list `USAGE` on the context as the only requirement for querying it. In our test the analyst couldn't resolve the context until we also granted `USAGE` on the `SENSE` schema and used the fully qualified context name, so grant both from a Snowsight worksheet. If you kept the name lowercase, quote it: `JUNIPER_HEALTH.SENSE."juniper_health"`.

```sql
USE ROLE JUNIPER_BUILDER;
GRANT USAGE ON SCHEMA JUNIPER_HEALTH.SENSE TO ROLE JUNIPER_ANALYST;
GRANT USAGE ON CORTEX SENSE JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH TO ROLE JUNIPER_ANALYST;
SHOW GRANTS ON CORTEX SENSE JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH;
```

`SHOW GRANTS` reports the object type as `CORTEX_CONTEXT`, which is how `CORTEX SENSE` objects are reported back.

`JUNIPER_ANALYST` still can't read the `KNOWLEDGE` schema. Any definition it uses from here on has to come through the context.

### Ask the same questions

Start a new analyst session from its directory:

```bash
cd ~/juniper-analyst
cortex -c juniper_analyst
```

Set the ground rules again, this time pointing at the context:

```
You are a data analyst at Juniper Valley Health. Before anything else, run
USE SECONDARY ROLES NONE; then show me
SELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES().
Use the JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH Cortex Sense context for definitions,
and compute every answer against the tables in JUNIPER_HEALTH.ANALYTICS. Don't
read query history, search the web, or search past conversations.
```

This prompt drops the baseline's rule against reading local files, because the `cortex-sense` skill reads its own instruction files.

The docs' intended way to query a context from CoCo is a serving skill generated on the **Activate** tab. This guide calls the `cortex-sense` skill directly instead, which worked in our test. CoCo won't always reach for the context on its own yet, so ask each question through the skill, naming the context in full:

```
$cortex-sense query JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH about: What's our clean claim rate by payer?
```

Ask the same five questions that way. Each answer cites the context entries it used. If the skill says it can't find or resolve the context, check the fully qualified name and both grants above. Here are the correct answers, so you can check what comes back:

| Question | Correct answer | Where the definition is written |
|---|---|---|
| Clean claim rate | **63.9%** (2,001 of 3,131). A claim is clean only if it was accepted on first submission, is `Paid`, and has no denial. UnitedHealthcare drops from first to last, at 54.2%. | `Metrics_Glossary.md`, `clean_claim_rate_by_payer.sql` |
| Readmission rate | **10.5%** (62 of 590 eligible index admissions), well below 18%. The base is inpatient stays that weren't cancelled and have a discharge date. Patients under 18 and obstetric admissions leave the denominator. The numerator counts only unplanned readmissions within 30 days whose index admission is eligible. | `Metrics_Glossary.md` |
| BEACON | **One facility:** Summit Orthopedic Hospital. BEACON stands for Balanced Excellence Across Clinical Outcomes and Net revenue, and requires all three of an Experience Score of 85 or higher, a readmission rate below 8%, and a denial rate below 4%. Cedar Ridge Hospital misses only on readmission, and Willow Creek Hospital only on denial rate. | `BEACON_Facility_Designation.md` |
| Tailwind rate | **78.3%** (1,175 of 1,500), just under the 80% target. Project Tailwind counts claims submitted within 24 hours of discharge, at ACO facilities only, for completed encounters. | `Project_Tailwind.md`, `tailwind_rate_by_month.sql` |
| External release | **Not as-is.** It's a Tier 3 release with four conditions: facility-level aggregates only; suppress facilities with fewer than 20 eligible index admissions, which applies to 3 of the 8 reporting facilities; replace facility names with blinded codes; and get written approval from the Data Governance Council, allowing 10 business days. A BAA doesn't authorize the release. | `External_Data_Release_Policy.md` |

The release and BEACON answers both depend on the readmission definition, because the suppression rule counts *eligible* index admissions. With the naive definition, an agent suppresses none of the facilities when three must be suppressed, and no longer sees Willow Creek as a BEACON near miss.

The Tailwind question shows that scope can matter more than the formula. The same 24-hour calculation gives 49.7% across all facilities and 78.3% across the ACO facilities the program covers.

In our test run, all five answers with context matched this table, each with citations to the context. The readmission answer also mentioned the naive 20.3% (191 of 941) reading and said the context rules it out.

The release question has the most riding on it. In our baseline run, the agent without context recommended suppressing Summit Orthopedic Hospital, which the policy doesn't require, and left Women's and Children's visible, which it does. It also never mentioned the Data Governance Council approval the policy requires.

### Share it beyond CoCo

To put the context in front of people who don't use CoCo, open the **Activate** tab in the builder session. You can create a CoWork agent from the context, add it to an existing agent, or create a CoCo skill. Access to an agent is separate from access to its context, so anyone using the agent also needs `USAGE` on the agent and on the context.

<!-- ------------------------ -->
## Improve the Context

### Record corrections

When an answer is wrong, tell CoCo the right definition in the builder session. Corrections collect on the **Inbox** tab, where you approve or reject each one. Approved corrections take effect at query time, with no rebuild.

### Measure it with evals

The companion repository has all seven questions and their expected answers in [`evals/questions.yaml`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/evals/questions.yaml). To run them, open the **Accuracy** tab in the builder session, choose **+ Start a new evaluation run**, and give it those questions and answers. Cortex Sense runs them, reports which ones failed and why, and can update the context and re-run.

### Check the answers yourself

[`answer_key.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/answer_key.sql) computes every correct answer from the base tables. Run it only **after** you've finished comparing. Anything you run lands in query history, which the context reads the next time it's built. The same applies to the baseline's wrong answers, so rebuild the context only when you're done experimenting.

<!-- ------------------------ -->
## Clean Up

If you used the **Activate** tab, first remove what it created: uninstall the CoCo skill, and drop any agent. Then delete the context. In the builder session, ask:

```
Delete the JUNIPER_HEALTH Cortex Sense context in JUNIPER_HEALTH.SENSE.
```

The skill shows the exact command it will run and asks you to type the context name to confirm. It leaves two things behind: the notification contact `JUNIPER_HEALTH.SENSE.JUNIPER_HEALTH_CONTACT`, which goes when the database is dropped, and a local `juniper_health_scope.yaml` draft in `~/juniper-builder`. Deletion can take a moment; check that the context no longer appears on the `/sense` page before you continue.

Then run [`teardown.sql`](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense/blob/main/teardown.sql) in a Snowsight SQL worksheet. It drops the database as `JUNIPER_BUILDER`, then removes the warehouse, the API integration, and both demo roles as `ACCOUNTADMIN`.

Finally, delete the `juniper_builder` and `juniper_analyst` blocks from `~/.snowflake/connections.toml`, and the `~/juniper-builder` and `~/juniper-analyst` directories.

<!-- ------------------------ -->
## Conclusion And Resources

The context came entirely from artifacts Juniper Valley Health already had: internal docs, saved queries, a dashboard, and a certified semantic view. Building it took a scope description and a few confirmations, with no new modeling. Semantic views remain the most precise path for domains you curate, and Cortex Sense covers the rest.

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
