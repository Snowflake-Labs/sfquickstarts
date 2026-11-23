author: Chanin Nantasenamat, James Cha-Earley
id: getting-started-with-cortex-sense-semantic-views-and-business-ontology
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform
language: en
summary: Give AI agents a shared understanding of your business. Use Cortex Sense to discover context, a semantic view to calculate metrics once, and Business Ontology to define and approve what your terms mean, then ask CoCo questions in plain English.
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology

# Getting Started with Cortex Sense, Semantic Views, and Business Ontology
<!-- ------------------------ -->
## Overview

Ask an AI agent that sees only the raw tables "How many suppliers do we have?" and it counts the rows in the vendor master: 15. Procurement would tell you the answer is 14, because one vendor is on probation and policy says probationary vendors don't count. Ask for the on-time delivery rate and the agent might average what carriers report about themselves (90%) when Procurement measures it from its own receipts (66.67%).

Neither answer is a bug. The knowledge that decides them is spread across code tables, team habits and people's heads. In this guide you bring that knowledge together in Snowflake, with three features that each do one job:

| Feature | Its job | In this guide |
|---|---|---|
| **Semantic view** | Calculates each metric once, so every tool gets the same number | `PROCUREMENT_SV` computes the supplier count, delivery rates and spend |
| **Business Ontology** | Records what each business term officially means, how terms relate, which data represents them, and who approved each definition | Two teams, Procurement and Logistics, define and approve their terms |
| **Cortex Sense** | Discovers context from metadata and from how data is used, and hands it to agents | A context named `PROCUREMENT` reads the tables, the semantic view, query history and the approved terms |

Then you ask CoCo, the AI coding agent in Snowsight, the same questions in plain English and check that its answers follow the approved definitions.

Every step ends with a check query and the exact numbers you should see.

This guide focuses on how the three features work together in a 45-minute lab, including two teams with different definitions of the same metric. For a deeper look at Business Ontology alone, including an A/B benchmark of agents with and without it, see [Getting Started with Business Ontology](https://www.snowflake.com/en/developers/guides/getting-started-with-business-ontology/).

> **Note:** Business Ontology and Cortex Sense are in Preview. CoCo is powered by LLMs and is non-deterministic, so its wording and the SQL it writes will differ from what you see here. The check queries read your data, not CoCo's chat, so they tell you whether an answer is right.

### Prerequisites
- Basic SQL: you can read a `SELECT` with a join and a `GROUP BY`
- Familiarity with Snowsight. No SAP knowledge needed: the guide explains every table it uses.

### What You'll Learn
- How Cortex Sense discovers context from table metadata, semantic views, query history and Business Ontology
- How a semantic view calculates key metrics the same way for every tool
- How to define and approve business terms in Business Ontology, connect related terms, keep two teams' different definitions side by side, and link each term to the semantic view metric that computes it
- How to see who approved a definition, and when
- How to ask CoCo business questions in plain English and get answers based on the approved definitions

### What You'll Need
- A Snowflake account where Business Ontology and Cortex Sense are available, with access to CoCo in Snowsight. To check Business Ontology, run `SELECT SYSTEM$GET_ONTOLOGY_SUMMARY();` in a SQL file: an error means it isn't enabled on your account yet.
- The `ACCOUNTADMIN` role for setup and clean up. Setup creates a lab role, `SENSE_ONTOLOGY_ROLE`, that you use for everything after that.
- The companion GitHub repo, which you'll open as a workspace: [sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology)
- Nothing to install. Everything runs in your browser.

> **Using a trial account?** AI features, including CoCo, are disabled by default on self-service trial accounts. To turn them on, go to **Admin** » **Billing**, open the **Snowflake billing** tab, and add a credit card. Adding a card doesn't upgrade the trial to a paid account or end the trial period.

### What You'll Build
- A semantic view, `PROCUREMENT_SV`, with five metrics: two official metrics, their two look-alikes, and procurement spend
- Two Business Ontology domains with 12 approved terms, 11 relationships and 12 links to the data
- A Cortex Sense context, `PROCUREMENT`, that agents use to find the right tables and the approved definitions

```
SAP tables ──► PROCUREMENT_SV ──────────────┐
  (17)         calculates the metrics       │
     │                                      ▼
     │         Business Ontology ──► Cortex Sense ──► CoCo and agents
     │         defines and approves  context PROCUREMENT
     │         the terms                    ▲
     └──────────────────────────────────────┘
               tables, columns and query history
```

### Run sheet

| Step | What happens | Time |
|------|--------------|------|
| Setup | Open the repo as a workspace and load the data | 5 min |
| 1 | Calculate the metrics in a semantic view | 5 min |
| 2 | Define, approve and connect the terms in Business Ontology | 15 min |
| 3 | Build the Cortex Sense context and see what it discovered | 10 min |
| 4 | Ask CoCo | 10 min |

<!-- ------------------------ -->
## The Scenario

A manufacturer runs procurement on SAP. SAP tables have short German names, so the data isn't easy to read on its own:

| Table | What it holds | Rows |
|---|---|---|
| `LFA1` | Vendor master: one row per vendor, with its account group `KTOKK` | 15 |
| `T077K` | Vendor account groups: `ZSTR` strategic, `ZSTD` standard, `ZPRB` probationary | 3 |
| `LIKP` | Inbound shipments, with planned (`LFDAT`) and actual (`WADAT`) delivery dates | 20 |
| `LFA2` | Carriers, with the on-time ratio each one reports about itself (`OTRAT`) | 6 |
| `EKPO` | Purchase order lines, with net value `NETWR` | 25 |
| `T320` | Storage locations at each plant | 8 |

The schema `SENSE_ONTOLOGY_QS.SAP` holds 17 tables in all, including materials, plants, contracts, inspections and finance tables.

Two teams use this data, and they disagree:

- **Procurement** reports the **supplier count** as active vendors only. A probationary vendor (`ZPRB`) doesn't count until it's promoted, so the answer is **14**, not the 15 records in the vendor master.
- **Procurement** measures the **on-time delivery rate** from its own receipts: delivered shipments that arrived on or before the planned date. That's **66.67%**.
- **Logistics** scores carriers on what they report about themselves. That average is **90%**, and it's a fair number for a carrier scorecard. It isn't delivery performance.

Both teams are right about their own numbers. Your job is to record which definition applies where, so an agent gives the right one.

<!-- ------------------------ -->
## Set Up Your Environment

### Sign in as ACCOUNTADMIN

Sign in to Snowsight. In the user menu in the lower-left corner, switch your role to **ACCOUNTADMIN**. You need it only for setup.

### Create a Git-backed workspace

The companion repo holds every file you'll run in this lab. Open it as a workspace so the files are already in Snowsight.

First, allow Snowflake to clone from the repo's GitHub account. In the navigation menu, select **Projects** » **Workspaces**. In **My Workspace**, select **+ Add new** » **SQL File**, paste the statements below, and select **Run all**:

```sql
USE ROLE ACCOUNTADMIN;

CREATE API INTEGRATION IF NOT EXISTS GITHUB_SENSE_ONTOLOGY_LAB
  API_PROVIDER = GIT_HTTPS_API
  API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-JCHAEARLEY')
  ENABLED = TRUE;
```

Then create the workspace:

1. In the **Workspaces** menu, select **From Git repository**.
2. For **Repository URL**, enter `https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology`.
3. Optional: rename the workspace, for example to `sense-and-ontology`.
4. In the **API Integration** menu, select `GITHUB_SENSE_ONTOLOGY_LAB`.
5. Select **Public repository**.
6. Select **Create**.

The workspace opens with the repo's files in the file explorer on the left:

| File | What it's for |
|------|---------------|
| `setup.sql` | Creates the lab role, warehouse, database and SAP tables |
| `semantic_view.sql` | Step 1: the semantic view |
| `ontology.sql` | Step 2: the two domains and their terms |
| `sense.sql` | Step 3: the Cortex Sense context |
| `checks.sql` | One check block per step, with the expected answers |
| `teardown.sql` | Removes everything the lab created |
| `optional/agents.sql` | Compares two Cortex Agents on the same questions |

### Run the setup script

Open **`setup.sql`** and select **Run all**. The script:
- creates `SENSE_ONTOLOGY_ROLE` and grants it to you. It gets `SNOWFLAKE.CORTEX_USER` for CoCo and agents, `SNOWFLAKE.CORTEX_SENSE_USER` to build a Cortex Sense context, and `CREATE ONTOLOGY DOMAIN` to create ontology domains.
- creates `SENSE_ONTOLOGY_WH`, an X-Small warehouse that suspends after 60 seconds
- creates `SENSE_ONTOLOGY_QS` and makes `SENSE_ONTOLOGY_ROLE` its owner
- switches to `SENSE_ONTOLOGY_ROLE` and loads the 17 SAP tables in the `SAP` schema

The data is synthetic and fixed, so everyone gets the same rows. If you need to start over, run `teardown.sql` and then `setup.sql`.

### Switch to the lab role

In the user menu in the lower-left corner, switch your role to **SENSE_ONTOLOGY_ROLE**. CoCo starts its session with whatever role is active in Snowsight, so it works with the lab role's access. `SENSE_ONTOLOGY_ROLE` is granted only one warehouse, `SENSE_ONTOLOGY_WH`, so use that wherever you're asked to choose a warehouse.

### CHECK 1

Open **`checks.sql`**. You'll run one block from it after each step. Select and run the **CHECK 1** block. Every row should say **PASS**:

| check_name | expected |
|---|---|
| Tables in SENSE_ONTOLOGY_QS.SAP | 17 |
| Vendor master records (LFA1) | 15 |
| Shipments (LIKP) | 20 |

<!-- ------------------------ -->
## Calculate the Metrics

A semantic view describes tables in business terms (tables, joins, dimensions and metrics) and calculates each metric the same way for every tool that queries it: SQL, CoCo, a Cortex Agent or a BI tool.

### Run the script

Open **`semantic_view.sql`** and select **Run all**. It creates `PROCUREMENT_SV` over 11 of the 17 tables and then queries it. The metrics that matter in this lab:

| Metric | Definition | Value |
|---|---|---|
| `LFA1.SUPPLIER_COUNT` | Distinct vendors whose account group counts as active | 14 |
| `LFA1.VENDOR_RECORD_COUNT` | Every vendor record, including probationary | 15 |
| `LIKP.ON_TIME_DELIVERY_RATE` | Percent of delivered shipments that arrived on or before the planned date | 66.67 |
| `LFA2.CARRIER_REPORTED_ON_TIME_RATE` | Average of what carriers report about themselves | 90.00 |
| `EKPO.PROCUREMENT_SPEND` | Total net value of purchase order lines | 1,353,690.00 |

Look at how `SUPPLIER_COUNT` decides what "active" means:

```sql
LFA1.IS_ACTIVE_SUPPLIER AS NOT T077K.EXCLUDE_FROM_ACTIVE_COUNT
...
LFA1.SUPPLIER_COUNT AS COUNT(DISTINCT IFF(LFA1.IS_ACTIVE_SUPPLIER, LFA1.LIFNR, NULL))
```

The rule lives in the code table `T077K`, not in a hard-coded list of codes. If Procurement adds a new account group, it adds one row to `T077K` and every tool's supplier count follows.

The view holds both the official metrics and their look-alikes, because some teams rely on the look-alikes. What the view can't say is which one to use when someone asks for "the supplier count". That's the ontology's job.

Six tables are left out of the view on purpose, including `T320` (storage locations). In Step 3, Cortex Sense finds them anyway.

### CHECK 2

Run the **CHECK 2** block in `checks.sql`:

| check_name | expected |
|---|---|
| SUPPLIER_COUNT (official) | 14.00 |
| VENDOR_RECORD_COUNT (look-alike) | 15.00 |
| ON_TIME_DELIVERY_RATE (official) | 66.67 |
| CARRIER_REPORTED_ON_TIME_RATE (look-alike) | 90.00 |

<!-- ------------------------ -->
## Define and Approve the Terms

Business Ontology is where teams record what their business terms officially mean. It has four building blocks:

| Building block | What it is | Example |
|---|---|---|
| **Domain** | A business area. Its description names the team that owns it | Procurement, Logistics |
| **Node** | A term in a domain: an entity, metric, term or policy | Supplier Count (metric) |
| **Relationship** | A typed link between two nodes | Supplier Count `HAS_VARIANT` Vendor Record Count |
| **Representation** | A link from a node to the data that represents it | Supplier Count → `PROCUREMENT_SV` metric `LFA1.SUPPLIER_COUNT` |

A new node starts as a **draft**. Agents use only **approved** nodes, so a definition doesn't reach anyone until its owner approves it.

### Run the script

Open **`ontology.sql`** and select **Run all**. It has six parts.

**Part 1** checks that no domain named Procurement or Logistics exists yet, then creates one domain per team:

```sql
SELECT SYSTEM$CREATE_ONTOLOGY_DOMAIN('Procurement',
  'Suppliers, materials, purchase orders, spend and delivery performance. Steward: Procurement data steward. [sense-ontology-qs]');
```

> **Note:** Domains are account-wide, not inside a database. If your account already has a Procurement or Logistics domain, Part 1 stops and nothing is created. If the domain is left over from this lab, run `teardown.sql` and then `setup.sql`. If another guide created it, for example Getting Started with Business Ontology, run that guide's clean up first.

**Part 2** drafts 12 nodes. Each metric states its definition in plain language and points to the semantic view as its formula source, and each official metric names its look-alike. An excerpt:

```sql
SELECT SYSTEM$DRAFT_ONTOLOGY_TERM('{"name": "Supplier Count", "domainName": "Procurement", "itemKind": "METRIC",
  "synonyms": ["Number of suppliers", "Active suppliers", "Active supplier count"],
  "description": "The official supplier count used in all reporting: the number of active suppliers ... Probationary vendors are excluded by policy. Counting vendor master records overstates it: use Vendor Record Count only for data maintenance.",
  "formulaSource": "SENSE_ONTOLOGY_QS.SAP.PROCUREMENT_SV", ...}');
```

| Domain | Nodes |
|---|---|
| Procurement | Supplier, Material, Purchase Order (entities); Vendor Account Group (term); Probationary Vendor Exclusion (policy); Supplier Count, Vendor Record Count, Procurement Spend, On-Time Delivery Rate (metrics) |
| Logistics | Shipment, Carrier (entities); Carrier Reported On-Time Rate (metric) |

**Part 3** approves the drafts, one domain at a time. In a real account, each domain's steward approves their own terms.

**Part 4** connects the nodes with 11 relationships. Two of them cross from Procurement to Logistics, and that's where the teams' definitions meet:

```sql
SELECT SYSTEM$CREATE_ONTOLOGY_RELATIONSHIP('Procurement.On-Time Delivery Rate', 'Logistics.Shipment', 'MEASURES', '', 'MANUAL');
SELECT SYSTEM$CREATE_ONTOLOGY_RELATIONSHIP('Procurement.On-Time Delivery Rate', 'Logistics.Carrier Reported On-Time Rate', 'HAS_VARIANT', '', 'MANUAL');
```

`HAS_VARIANT` is how the ontology leaves room for real differences between teams. Logistics keeps its carrier-reported rate as an approved definition for carrier scorecards, and the ontology records that it's a variant of the delivery rate, not a replacement for it.

**Part 5** links each node to the data that represents it: 5 metrics to their semantic view metrics, 6 entities and terms to their tables, and the probationary policy to the `EXCLUDE_FROM_ACTIVE_COUNT` column. An agent that finds a definition also finds the one place the number is calculated.

**Part 6** reads everything back, including the approval record for Supplier Count:

| CHANGED_AT | CHANGE | BEFORE_VALUE | AFTER_VALUE | CHANGED_BY | CHANGED_BY_ROLE |
|---|---|---|---|---|---|
| `<time>` | CREATED | | `<the new definition>` | `<your user>` | SENSE_ONTOLOGY_ROLE |
| `<time>` | STATUS_CHANGED | DRAFT | ACTIVE | `<your user>` | SENSE_ONTOLOGY_ROLE |

That's the record of who approved each definition, with which role, and when.

### See it in Snowsight

In the navigation menu, select **Catalog** » **Business Ontology**. Filter by the Procurement or Logistics domain, and switch between the **List** and **Graph** views to see the nodes and how they connect.

> **Prefer to work in plain language?** The `business-ontology` skill in CoCo can draft, connect and approve nodes for you. On the **Business Ontology** page, select **Generate Ontology** to open CoCo with the skill loaded. It shows each draft for review before anything is written. Its wording will differ from the script, so the counts in CHECK 3 apply to the script.

### CHECK 3

Run the **CHECK 3** block in `checks.sql`:

| check_name | expected |
|---|---|
| Approved nodes | 12 |
| Relationships | 11 |
| Cross-domain relationships (Procurement to Logistics) | 2 |
| Representations | 12 |
| Metrics linked to a semantic view metric | 5 |

<!-- ------------------------ -->
## Discover Context with Cortex Sense

The ontology covers the terms your teams care most about. Most of a data estate will never have an approved definition: which table holds storage locations, how two tables join, what a code like `ZPRB` means. Cortex Sense discovers that context for you.

A Cortex Sense context is built from a **scope**, the list of sources it reads:

| Source | What Cortex Sense learns from it |
|---|---|
| `catalog_objects` | Every table in `SENSE_ONTOLOGY_QS.SAP`: names, columns, comments and keys |
| `semantic_views` | `PROCUREMENT_SV`: its metrics, joins and synonyms |
| `query_history` | How people actually use the tables: which joins and filters they run |
| `business_ontology` | The approved terms in the Procurement and Logistics domains |

From those sources it writes a document per table, metric and term, and serves them to agents through one lookup. Approved ontology terms come back as their own documents, so an agent can tell an approved definition from what Cortex Sense inferred.

This lab shows discovery from metadata, the semantic view and the ontology. Your lab tables are brand new, so there's almost no query history to learn from. In an account where people have queried the data for months, query history is where Cortex Sense learns the joins and filters people actually use.

### Build the context

Open **`sense.sql`**. Select and run **Part 1**. It saves the scope as a context named `PROCUREMENT`, starts the build, and returns:

```
Context PROCUREMENT saved. The build is running: run CHECK 4 in checks.sql until it says PASS.
```

The build runs in the background and takes a few minutes. Run the **CHECK 4** block in `checks.sql` every few minutes until it says **PASS**:

| check_name | expected |
|---|---|
| PROCUREMENT context processed | processed |

### See what Cortex Sense discovered

Once CHECK 4 passes, select and run **Part 2** of `sense.sql`. Each of its three lookups returns the documents an agent gets for a question.

For *"How many suppliers do we have?"* you should see something like this. The order can differ.

| RANK | DOC_TYPE | ENTITY_KEY | What it is |
|---|---|---|---|
| 1 | table_entity | SENSE_ONTOLOGY_QS.SAP.LFA1 | The vendor master, also called suppliers and vendors |
| 2 | table_entity | SENSE_ONTOLOGY_QS.SAP.T077K | The account group code table |
| 3 | ontology_node | `<id>` | Supplier (approved, Procurement) |
| 4 | ontology_node | `<id>` | Supplier Count (approved, Procurement) |
| 5 | datamart | SENSE_ONTOLOGY_QS.SAP.PROCUREMENT_SV | The semantic view |
| 6 | datamart | `<domain key>` | The Procurement domain |

The table documents, the approved terms and the semantic view come back together, and an agent gets all of them in one lookup.

For *"storage location"*, the first document is `T320`. That table isn't in the semantic view and has no ontology node, but Cortex Sense found it and documented its grain and columns.

The last query shows the full document for `LFA1`. Cortex Sense combined the column metadata, the semantic view's descriptions and its join to `T077K` into one document, and added example questions people are likely to ask of the table.

> **Optional: let Cortex Sense suggest terms.** After a build, Cortex Sense compares what it inferred with the ontology and records where they differ. To review its suggestions, open CoCo and send `/business-ontology Review the Cortex Sense report for the PROCUREMENT context against the Procurement domain.` In testing, it flagged three metrics where its inferred description differed from the approved one, and proposed nothing that would overwrite an approved definition. You decide whether to accept, edit or decline each suggestion.

<!-- ------------------------ -->
## Ask CoCo

Now ask business questions in plain English. CoCo can use the Cortex Sense context to find the approved definitions, the semantic view to compute the numbers, and the tables to fill in the rest.

### Open CoCo

Select the **CoCo** icon in the lower-right corner of the workspace. Check that your role is still `SENSE_ONTOLOGY_ROLE`. Start a new conversation.

### Prompt 1

```
I'm a procurement analyst. Our data is in SENSE_ONTOLOGY_QS.SAP. The metrics
are in the semantic view SENSE_ONTOLOGY_QS.SAP.PROCUREMENT_SV, the approved
business definitions are in Business Ontology, and the Cortex Sense context
SENSE_ONTOLOGY_QS.SAP.PROCUREMENT knows the tables. Use warehouse
SENSE_ONTOLOGY_WH.

How many suppliers do we have?
```

The first paragraph tells CoCo where to look. New objects can take a while to appear in Snowflake's catalog search, so naming them saves CoCo a search. You only need to say it once per conversation.

### What CoCo should do

1. Look up "supplier" in the context and find the approved **Supplier Count** node in the Procurement domain.
2. Use the semantic view metric the node links to, `LFA1.SUPPLIER_COUNT`, and answer **14**.
3. Explain why it isn't 15: Vendor Record Count includes the probationary vendor, and the Probationary Vendor Exclusion policy says probationary vendors don't count.

If CoCo answers 15, ask: *"Is there an approved definition of Supplier Count in Business Ontology? Use it."*

### Prompt 2

In the same conversation, send:

```
What's our on-time delivery rate?
```

CoCo should answer **66.67%** from Procurement's **On-Time Delivery Rate**: 10 of the 15 delivered shipments arrived on or before the planned date. It should also mention that Logistics has a different, approved metric, **Carrier Reported On-Time Rate** (90%), which is for carrier scorecards, not delivery performance.

Both numbers are approved, each for its own purpose. The `HAS_VARIANT` relationship tells CoCo which one answers a question about delivery performance.

### Prompt 3

```
How many storage locations does plant PLT-001 have?
```

CoCo should answer **3**: `WH-001` Austin Raw Materials Hub, `WH-002` Austin Finished Goods Depot and `WH-008` Houston Regional Distribution Hub. This answer comes from `T320`, a table that's outside the semantic view and has no approved definition. Cortex Sense found it in Step 3.

There's no approved definition here, so CoCo is making its own judgment. It may point out that a Houston storage location sits under the Austin plant. That's a good question to take to the data owner, and a sign this term might be worth adding to the ontology.

### CHECK 5

Run the **CHECK 5** block in `checks.sql`. It computes the three answers without CoCo, so you can compare them with CoCo's:

| question | expected |
|---|---|
| How many suppliers do we have? | 14 |
| What is our on-time delivery rate? | 66.67% |
| How many storage locations does plant PLT-001 have? | 3 |

<!-- ------------------------ -->
## Optional: Compare Two Agents

`optional/agents.sql` creates two Cortex Agents and asks each one the first two questions:

| Agent | Tools |
|---|---|
| `SV_ONLY_AGENT` | The semantic view only |
| `GOVERNED_AGENT` | The semantic view, Business Ontology search and the Cortex Sense context |

Open **`optional/agents.sql`** and select **Run all**. Part 2 takes a minute or two.

In testing, both agents reached 14 and 66.67%, because the semantic view's metric definitions already encode the right logic. The difference was in how they explained it:
- `GOVERNED_AGENT` named the approved terms, the probationary policy, and the variant it didn't use.
- `SV_ONLY_AGENT` had to infer the reason from the data: one vendor was excluded, "most likely the probationary group."

The semantic view produced the right number. The ontology let the agent say why it's right and which definition it used.

> **Note:** Business Ontology search builds its index from approved terms in the background, and new terms can take up to a day to show up in search. Until then, `GOVERNED_AGENT` still gets the approved terms through the Cortex Sense context.

To chat with the agents, go to **AI & ML** » **Agents** and open `GOVERNED_AGENT`.

<!-- ------------------------ -->
## Clean Up

Ontology domains are account-level objects, so dropping the database doesn't remove them. `teardown.sql` removes everything in the right order.

1. Open **`teardown.sql`** and select **Run all**. The script:
   - deletes the `PROCUREMENT` context
   - empties the Procurement and Logistics domains (representations, then relationships, then nodes) and deletes them. It deletes a domain only if its description carries this lab's `[sense-ontology-qs]` marker, and reports any other domain with those names as left in place.
   - switches to `ACCOUNTADMIN` and drops `SENSE_ONTOLOGY_QS` (including the semantic view and any agents), `SENSE_ONTOLOGY_WH`, `SENSE_ONTOLOGY_ROLE`, and the `GITHUB_SENSE_ONTOLOGY_LAB` API integration
2. In **Projects** » **Workspaces**, delete your lab workspace. Then delete the SQL file in **My Workspace** that you used for the API integration.

<!-- ------------------------ -->
## Conclusion and Resources

You started with two teams, 17 tables with cryptic names, and two numbers that each had a plausible look-alike. You calculated the metrics once in a semantic view, and recorded which definition each team owns, how they relate and who approved them. Then you let Cortex Sense bring all of it together for agents. CoCo should have answered in plain English with the approved numbers, explained why, and told you when it was relying on its own judgment.

### What You Learned
- A semantic view calculates each metric the same way for every tool
- Business Ontology records what terms officially mean, connects them, keeps different teams' definitions side by side as variants, and links each term to the data that computes it
- Every approval is recorded with the user, role and time
- Cortex Sense discovers context from metadata, semantic views, query history and the ontology, and gives an agent all of it in one lookup
- Approved definitions take precedence, and where none exists, an agent can still find the data but has to use its own judgment

### Related Resources

Code:
- [Companion repo: sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology](https://github.com/sfc-gh-JCHAEARLEY/sfguide-getting-started-with-cortex-sense-semantic-views-and-business-ontology)

Guides:
- [Getting Started with Business Ontology](https://www.snowflake.com/en/developers/guides/getting-started-with-business-ontology/)
- [Build a Business Ontology for a Bank, from Definitions to Agent](https://www.snowflake.com/en/developers/guides/build-a-business-ontology-for-a-bank/)

Documentation:
- [Business Ontology](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-horizon/business-ontology)
- [Horizon Context](https://docs.snowflake.com/en/user-guide/snowflake-horizon/horizon-context)
- [Semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [CoCo in Snowsight](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-snowsight)
