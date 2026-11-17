author: Tianxia Jia, Chanin Nantasenamat
id: getting-started-with-business-ontology
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/platform
language: en
summary: Build a governed Business Ontology on top of well-built semantic views, connect it to a Cortex Agent, and measure what it adds with a fair A/B test.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Getting Started with Business Ontology

## Overview

> **Private Preview:** Business Ontology is available to selected accounts. Contact your Snowflake account team to confirm access before starting this guide.

Ask a simple question like "How many suppliers do we have?" and you might expect a simple answer. In most companies, though, there are several correct-looking numbers. The vendor master holds 15 vendor records, but one of them is a probationary vendor that procurement policy says doesn't count, so the official answer is 14. Both numbers are computed correctly. They just answer slightly different questions.

People resolve this kind of ambiguity from experience: they know which number Finance reports, what "Tier A supplier" means at your company, and that you never cut a material that goes into something you sell. An AI agent doesn't have that experience. Given two plausible metrics, it may pick the wrong one, hedge with "15 or 14", or give different answers to different teams. Good semantic views help a lot, but each view describes one team's data. None of them is the place to decide which of two competing definitions is the official one.

Business Ontology, currently in Private Preview, is a governed layer of business meaning that sits above your semantic views. It doesn't replace them: the semantic views still compute every number. The ontology records what each business word means, which metric is canonical and which is only a look-alike, which policies apply, and how concepts connect across domains. A domain owner approves each definition, and the agent looks it up before it queries data.

With the ontology in place, the agent searches for "supplier count" first, finds the approved definition that says probationary vendors are excluded, queries the semantic view metric that implements it, and answers 14. It also names the definition it used, so anyone can check the answer. A steward can update shared meaning in the ontology without rewriting each agent's prompt. If the change affects how a number is computed, the implementing semantic view must also match the new rule; changing ontology text alone does not change metric SQL.

In this guide, you build exactly that on a synthetic SAP supply-chain dataset: three domain semantic views plus an ontology covering Procurement, Finance & Controlling, and Sales & Distribution. You build it in 10 steps. Each step identifies what to run or review, shows a `$business-ontology` Cortex Code (CoCo) alternative, and ends with a check so you know the step worked. At the end, you compare two agents using the same semantic views, one with ontology search and ontology-oriented instructions and one without, to see how their answers differ.

A quick word on those prompts. Cortex Code (CoCo) is Snowflake's AI coding assistant. You can use it in a side panel in Snowsight, as a desktop app, or as a command-line tool. It can load *skills*, which are packaged instructions that teach it how to do a specific job well. `business-ontology` is the skill for building and managing Business Ontology, and it comes bundled with Cortex Code, so there's nothing to install. Starting a message with `$business-ontology` tells Cortex Code to use that skill for the request. You then describe what you want in plain language, for example "Create three domains...", and the skill turns it into the right Business Ontology SQL calls. It shows you each draft for review before anything is written. Where a step includes a **The SQL Behind It** subsection, it shows the SQL that the skill runs for you.

### What You'll Learn

- What belongs in a semantic view and what belongs in Business Ontology
- How to model canonical metrics, their look-alikes, company vocabulary and policies
- How to connect ontology nodes to the semantic view metrics that implement them
- How to configure a Cortex Agent to search the ontology before it queries data
- How to measure what the ontology adds with a fair A/B test

Those are the skills. Here's the concrete result they produce.

### What You'll Build

The architecture below follows the data from source tables to agent answers. The upper path supplies governed definitions; the lower path computes the numbers.

![End-to-end Business Ontology architecture: source tables feed shared semantic views, account-level ontology definitions guide the BON agent, and two agents feed an answer comparison](assets/architecture-diagram.png)

1. **Prepare the data.** Load synthetic SAP tables into the raw schema, then clone them into the working schema with reference tables and helper views.
2. **Define the computations.** Three enriched semantic views expose Procurement, Finance and Sales metrics. Both comparison agents query these same views.
3. **Govern the meaning.** Three account-level ontology domains contain the approved concepts and relationships. Representations link those concepts to their implementing data objects and metrics; they do not copy data.
4. **Make definitions searchable.** Approve the drafts and verify search indexing before testing answers. The BON agent looks up definitions to select metrics and apply business rules; the baseline agent has no ontology search.
5. **Compare the answers.** Check both agents' numbers and explanations. The optional benchmark repeats the comparison. The warehouse supplies compute for the SQL operations.

By the end of this guide, your account holds the objects below: three domains of governed nodes, the relationships and representations that connect them to each other and to your data, and the semantic views and agents that put them to work. The counts are the same ones the **Check** lines confirm along the way.

| Object | Count | Notes |
|---|---|---|
| Domains | 3 | Procurement · Finance & Controlling · Sales & Distribution |
| Entities | 13 | Supplier, Material, Assembly, Bill of Materials, Purchase Order, Shipment, Carrier, Inspection Lot, AP Line Item, Cost Posting, Sales Order, Customer, Pricing Condition |
| Metrics | 16 | Canonical metrics, their look-alikes (e.g. *Vendor Record Count*, *Carrier Reported On-Time Rate*, *Gross Bookings*), and cross-domain metrics (*Product Gross Margin*, *Customer Profit*, *Revenue at Risk*) |
| Terms | 8 | Code fields and company vocabulary: Vendor Account Group, Material Group, Posting Key, GL Account, Cost Object, Condition Type, Sales Organization, **Tier A Supplier** |
| Policies | 3 | Probationary Vendor Exclusion, Credit Memo Sign Rule, BOM Input Protection |
| Relationships | 51 | MEASURES 13 · DERIVES 13 · CLASSIFIES 8 · RELATED_TO 6 · APPLIES_TO 4 · HAS_PART 3 · HAS_VARIANT 3 · IS_A 1 |
| Representations | 43 | IMPLEMENTS 12 · REPRESENTS 14 · RELATED_SEMANTIC_VIEW 8 · DESCRIBES 7 · REFERENCE_DATA 2 |
| Semantic views | 6 | Three enriched views used here: `PROCUREMENT_ENRICHED_SV`, `FINANCE_ENRICHED_SV`, `SALES_ENRICHED_SV`; three bare views for the additional baseline agent |
| Agents | 7 | Arm A is `BARE_AGENT`, an additional bare-SV baseline not evaluated here. The A/B experiment compares arm B, `ENRICHED_AGENT` (enriched SVs only), with arm C, `BON_AGENT` (same SVs + ontology search and instructions). The script also creates two Finance/Sales team pairs for consistency checks. |

The semantic views and agents live in `BUSINESS_ONTOLOGY.SAP`. Ontology domains are account-level containers; their representations point to objects in that schema.

> **Policies:** the generated script drafts policies with `itemKind: POLICY_CONCEPT`; the sample node read-backs identify them as `POLICY`. Keep the script's input spelling when reproducing this demo. Preview APIs can evolve, so check the current Business Ontology documentation before adapting node kinds for another project.

With the end result in mind, check that you have everything needed to build it.

### What You'll Need

Here's what you need before you start. Everything in the table is required except Python, which you only need for the optional full benchmark in Step 10.

| Requirement | Details |
|---|---|
| Account | Business Ontology enabled (Private Preview); search indexing enabled in your region |
| Snowsight | **Catalog > Business Ontology**, and a SQL worksheet to run the scripts |
| Role | One role for the whole guide, used as your primary role. It needs `CREATE ONTOLOGY DOMAIN` on the account to create the three domains (`ACCOUNTADMIN` has it by default), plus the usual privileges to create a database, warehouse, semantic views and agents. The role that creates a domain owns it, so it can then draft, approve and link nodes, and search them. The demo used ACCOUNTADMIN. |
| Local setup | A terminal with Bash and standard `mkdir` and `cat` commands. The Setup section writes all nine SQL scripts, including the synthetic SAP data, and the Python benchmark locally; no Git or repository download is required |
| CoCo | Cortex Code in Snowsight (opened by **Generate Ontology**, below) or Cortex Code Desktop, for the prompts, plus the Cortex Code CLI for the search check in Step 8. The `business-ontology` skill is bundled, so no install is needed. |
| Python (optional) | Python 3.10+ and `snowflake-connector-python`, only for the full benchmark in Step 10 |
| Time | About an hour of hands-on work, plus a variable search-indexing wait. In our trials, terms were first observed as searchable approximately 5 to 14 hours after the final ontology write. These are observation times, not guaranteed indexing durations (Step 8). |

If this is your first time with Business Ontology, start by finding it in Snowsight. In the left sidebar, hover over **Catalog** under **Horizon Catalog** and click **Business Ontology**, which carries a **PREVIEW** label. The page lists every node you can see, with its domain and description, and you can switch between a **List** and a **Graph** view or filter by domain and state. On a new account the list is empty; the screenshot below comes from an account that already has the demo ontology.

**Expected:** the catalog page opens. The illustrative checklist below covers both an empty account and one with existing nodes.

| Action | Visible state to look for |
|---|---|
| Open Business Ontology | A node list, or an empty state if no visible nodes exist |
| Switch List / Graph | The selected view shows the visible ontology nodes |
| Filter by domain or state | Results reflect the selected filter; clear it before later checks |

To build an ontology from this page, click **Generate Ontology** at the top right. A CoCo session opens in the right panel and loads the `business-ontology` skill for you, then explains the ways you can generate an ontology: define it directly, import a glossary or documents, extract it from existing metadata such as semantic views, or promote a Cortex Sense context. Nothing is created until you confirm. This panel is the easiest place to paste the **Use CoCo** prompts in this guide. In Snowsight, use `/business-ontology`. The prompts in this guide use `$business-ontology`, the form for Cortex Code Desktop and the CLI. Use the form for your surface rather than assuming the two prefixes are interchangeable.

**Expected:** the panel is ready for a request. The content below is illustrative, not an exact CoCo transcript.

```text
Business Ontology generation
Choose a source: direct definitions, glossary/documents, metadata, or context.
Next: describe what you want to build and review the proposal.
```

![The Business Ontology page in Snowsight, with Generate Ontology open in the CoCo panel](assets/generate_ontology.png)

Before you build anything, it helps to be clear on what Business Ontology is and how it differs from the semantic views you may already have, so that's where we start.

## What Is Business Ontology

Business Ontology is the governed meaning layer in Horizon Catalog. It models shared business meaning as a connected graph of **terms, metrics and entities**, organised into **domains**, linked by **typed relationships**, and tied to the Snowflake objects that implement them through **representations**. Only approved items are visible to agents.

**Semantic Views tell Snowflake *how* to compute a metric. Business Ontology tells everyone *what* that metric means, *which* one is canonical, *who* approved it, and *whether* teams agree.**

The table below puts the two layers side by side, using the supplier count example from the introduction.

| Layer | Owns | Example from the demo |
|---|---|---|
| Semantic View | Tables, joins, dimensions, metric SQL; executes the number | `PROCUREMENT_ENRICHED_SV` has `VENDOR_RECORD_COUNT` (15); `FINANCE_ENRICHED_SV` has `ACTIVE_SUPPLIER_COUNT` (14) |
| Business Ontology | Which metric is canonical, business vocabulary, policies, cross-domain links | "Supplier Count" means active suppliers; *Probationary Vendor Exclusion* applies to it; it is implemented by `ACTIVE_SUPPLIER_COUNT` |

The picture below shows the same question asked twice. On the left, the agent has only the semantic views: it sees two defensible metrics, `VENDOR_RECORD_COUNT` and `ACTIVE_SUPPLIER_COUNT`, and either picks one or hedges. On the right, the ontology tells it which metric is official and which policy applies, so it answers 14 and cites the governed term.

![Semantic views alone compared with semantic views plus Business Ontology](assets/comparison.png)

The SV still computes the number. The ontology makes the agent pick the right one and say why.

That split between computing a number and deciding what it means is worth spelling out, because the rest of the guide builds on it.

### How Semantic Views and the Ontology Divide the Work

Most of the decisions in this guide follow from one division of labour:

- **The semantic view is the computation authority.** The SQL that produces a number lives in the view. A formula recorded in the ontology is documentation and a cross-check, not the calculation.
- **The ontology is the meaning authority.** When two correct metrics compete for the same business word, the ontology is where you say which one is official, and why.

That's also why a good ontology definition *decides* rather than just describes. "Number of suppliers" describes. "The official supplier count used in all reporting; probationary vendors are excluded; the vendor record count is an operational variant, not the official count" decides, and that sentence is what turns an agent's "it depends" into an answer.

With that rule in mind, here's how it plays out when you decide where a piece of business knowledge belongs.

### What Goes Where

As a rule of thumb, anything about *how* to compute a number belongs in the semantic view, and anything about *which* definition is official, or what a word means across teams, belongs in the ontology. The table gives concrete examples of each.

| Put it in the **Semantic View** | Put it in **Business Ontology** |
|---|---|
| Table joins, dimensions, facts | Which of several metrics is the canonical one |
| Metric SQL, including filters and sign logic (`ACTIVE_SUPPLIER_COUNT`, `COGS_RAW_MATERIALS` with credit memos subtracted) | Business vocabulary the data doesn't name ("Tier A supplier", "gross bookings is not revenue") |
| Synonyms that only help text-to-SQL | Policies that constrain how metrics are used (exclusions, sign rules, what must not be cut) |
| Verified queries | Cross-domain chains (Sales → BOM → Procurement cost) and who approved each definition |

**Don't** create one ontology metric for every SV metric. Create ontology nodes where meaning is contested, company-specific or cross-domain. The SV computes; the ontology decides and explains.

With that mental model in place, the next section explains how the 10 build steps are laid out, so you know what to expect from each one.

## How This Guide Works

The diagram below shows the 10 build steps in order. The blue steps (metrics, terms and policies, and the A/B test) are where most of the value comes from, and the amber step is the indexing wait. If you already have semantic views, the dashed bootstrap path can stand in for the early steps.

![End-to-end process](assets/steps.png)

Each of the 10 steps has the same parts, and all but the first are subsections under the step's heading:

- **What to run:** each step opens by telling you the one thing to do, which is usually to run a named section of a script created in the Setup section in a Snowsight SQL worksheet. Following the script path and the guide's approval statements creates the demo's 40 nodes, 51 relationships and 43 representations.
- **Use CoCo:** a subsection with an alternative to the script. A short sentence explains what the prompt in the box below it asks the `$business-ontology` skill to do, so you can paste the prompt into Cortex Code (CoCo) instead of running the script section. The prompts are shortened for reading. Use them to learn the workflow and to build an ontology on your own data. If you use them here, your ontology will differ from the demo and so may your results.
- **The SQL Behind It:** where it appears, a subsection showing the system function that both the script and the prompt call, with notes on how it behaves. It's for reference; you don't run it separately.
- **Check:** a subsection that says what to look at once the step has run, where to find it, and what to do if it doesn't match. Adjacent **Expected** blocks show sample outputs or expected states. Exact counts apply to the complete script path, not the shortened CoCo prompts.

> **Reading the examples:** sample SQL and agent results below use this guide's database, warehouse and domain names. JSON excerpts show selected fields only. `<generated-domain-id>` and `<generated-term-id>` stand for IDs Snowflake returns for your objects; save your actual IDs rather than pasting these placeholders. CoCo review cards are illustrative content, not exact UI transcripts. Agent answers and optional-path outputs can vary.

Pick one way per step. Running both the script and the prompt drafts every node twice.

> **Keep one worksheet session.** Steps 1 to 6 approve drafts with the session-scoped form of `SYSTEM$APPROVE_ALL_GLOSSARY_TERMS`, which approves only what the current session drafted. Run them all in the same worksheet. If you switch sessions, approve by term ID instead (Step 6 shows both forms).

If you already have semantic views of your own, read **Bootstrap from Semantic Views** under **Going Further** after you finish: the import covers Step 2, and Steps 3 to 5 fill the gaps it can't infer.

Now that you know the shape of each step, you set up the demo data and the semantic views that the ontology will sit on top of.

## Setup

### Create working directory

The setup script creates the nine SQL scripts and the Python benchmark directly on your computer. All file contents are included in the script, so you do not need to clone a repository. After downloading the script, folder setup works offline. You run the SQL later, in the order explained below.

Choose a local working directory where you want the `business-ontology` folder. The script creates the full working directory `business-ontology/getting-started` with two sub-folders consisting of `benchmark` and `sql`.

Open the raw [setup_business_ontology.sh](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/site/sfguides/src/getting-started-with-business-ontology/src/setup_business_ontology.sh) file and save it as `setup_business_ontology.sh` in your chosen local working directory. The link opens the script text directly; use your browser's **Save As** command to save the raw file, keeping the `.sh` extension rather than saving a web page or adding `.txt`.

Open your local terminal in the directory containing the downloaded script. Review the script, then run the following command.

```bash
bash setup_business_ontology.sh
```

Successful folder setup prints the following two lines. No Snowflake statements or benchmark calls have run yet.

```text
Created 10 project files in business-ontology/getting-started.
No Snowflake statements or benchmark were executed.
```

The child shell's directory change does not persist in your terminal. After both success lines appear, enter the new project folder in your current shell and check its location.

```bash
cd business-ontology/getting-started
pwd
```

**Expected:** the printed absolute path ends in `/business-ontology/getting-started`. All subsequent local file paths and benchmark commands in this guide are relative to this project folder.

### Inspecting the project working directory

Then run the first six scripts in `sql/` in order. Everything lives in the `BUSINESS_ONTOLOGY` database and runs on the `BUSINESS_ONTOLOGY_WH` warehouse, split across two schemas: `RAW` holds the synthetic SAP source tables, and `SAP` holds everything you build on top of them. `03_sap_schema.sql` clones the `RAW` tables into `SAP` and stops with an error if they are missing.

**Expected after folder setup:** the `getting-started` project folder contains the ten files below, shown relative to that folder. This is a file-layout check. Open `sql/01_setup.sql` in a SQL worksheet and keep that session for the build.

```text
sql/01_setup.sql
sql/02_raw_data.sql
sql/03_sap_schema.sql
sql/04_ground_truth.sql
sql/05_bare_svs.sql
sql/06_enriched_svs.sql
sql/07_ontology.sql
sql/08_representations.sql
sql/09_agents.sql
benchmark/run_benchmark.py
```

**Expected worksheet state (illustrative):** the script is open and your selected primary role can create the demo objects. Opening the file alone does not execute it. Check that the default database, warehouse and domain names do not belong to an existing project before running scripts that replace objects.

```text
Open script: sql/01_setup.sql
Primary role: your approved setup role
Execution: not started merely by opening the file
Name check: demo targets are not shared or pre-existing project resources
```

The list below shows the six setup scripts in the order you run them, with a comment after each one saying what it creates. Run each file in full in a Snowsight SQL worksheet before you open the next one.

```
sql/01_setup.sql              # BUSINESS_ONTOLOGY database, RAW schema, BUSINESS_ONTOLOGY_WH warehouse
sql/02_raw_data.sql           # 15 SAP tables + synthetic data in RAW
sql/03_sap_schema.sql         # SAP schema: tables cloned from RAW, T077K and T023T code tables
sql/04_ground_truth.sql       # BENCHMARK_QUESTIONS, BENCHMARK_GROUND_TRUTH (20 questions)
sql/05_bare_svs.sql           # CUSTOMERS_VIEW, BOM_EXPLOSION_VIEW, bare SVs (benchmark arm A only)
sql/06_enriched_svs.sql       # PROCUREMENT / FINANCE / SALES _ENRICHED_SV
```

**Expected after each script:** these are sample messages and read-back counts from a fresh setup. `USE` statements return `Statement executed successfully.`; creation messages can differ when an object already exists.

| Script | Sample result messages | Expected resulting state |
|---|---|---|
| `01_setup.sql` | `Database BUSINESS_ONTOLOGY successfully created.`; `Schema RAW successfully created.`; `Warehouse BUSINESS_ONTOLOGY_WH successfully created.` | Database, RAW schema and warehouse created |
| `02_raw_data.sql` | `Table LFA1 successfully created.`; insert results show `number of rows inserted` = `1` for individual inserts | 15 RAW tables; sample counts: LFA1 = 15, MARA = 24, EKPO = 25, LIKP = 20 |
| `03_sap_schema.sql` | `RAW source tables found`; `cloned 15` | 15 SAP clones with matching counts; T077K = 3 rows, T023T = 6 rows |
| `04_ground_truth.sql` | `Table BENCHMARK_QUESTIONS successfully created.`; `Table BENCHMARK_GROUND_TRUTH successfully created.` | 20 questions and 20 ground-truth rows |
| `05_bare_svs.sql` | `Semantic view PROCUREMENT_BARE_SV successfully created.` (and corresponding Finance/Sales messages) | CUSTOMERS_VIEW, BOM_EXPLOSION_VIEW and three bare semantic views |
| `06_enriched_svs.sql` | `Semantic view FINANCE_ENRICHED_SV successfully created.` (and corresponding Procurement/Sales messages) | Three enriched semantic views; active suppliers = 14, net revenue = 711915 |

The final query in `02_raw_data.sql` returns the following counts for the synthetic dataset. Rows are shown here alphabetically for readability.

| TBL | ROW_COUNT |
|---|---:|
| BSEG | 38 |
| COEP | 19 |
| EKPO | 25 |
| KONV | 25 |
| LFA1 | 15 |
| LFA2 | 6 |
| LFB1 | 15 |
| LIKP | 20 |
| MARA | 24 |
| QALS | 10 |
| QUAL_MATRIX | 28 |
| STPO | 15 |
| T001W | 5 |
| T320 | 8 |
| VBAP | 13 |

With the data and semantic views in place, the remaining three scripts build everything else: the ontology, the links to your data, and the agents. Don't run them yet. Each one is a sequence of build steps rather than a single action, so the guide walks through them a section at a time. The list below is reference only, with no execution required here.

```
sql/07_ontology.sql           # 3 domains, 40 nodes, 51 relationships
sql/08_representations.sql    # 43 representations
sql/09_agents.sql             # 7 agents
```

The scripts and the build steps are numbered separately, so the table below shows which script each build step uses. Steps 1 to 6 work through `07_ontology.sql` with the guide's approval statements and checks; Steps 3 and 4 are review only.

| Build step | What you run |
|---|---|
| 1. Create Domains | `07_ontology.sql`: the `Domains` section |
| 2. Add Entities | `07_ontology.sql`: the three node sections |
| 3. Add Metrics | Nothing new; Step 2 already drafted them |
| 4. Terms and Policies | Nothing new; Step 2 drafted them, except *Tier A Supplier*, which comes in Step 5 |
| 5. Define Relationships | The approval SQL in this guide, then the `Relationships` section and the last section of `07_ontology.sql`, approving Tier A Supplier before its relationships |
| 6. Approve and Verify | The check queries in this guide |
| 7. Add Representations | All of `08_representations.sql` |
| 8. Confirm Search Indexing | Three search commands, no script |
| 9. Build the Agent | All of `09_agents.sql` |
| 10. Run A/B Tests | Questions to the agents in Snowsight, plus an optional Python benchmark |

Before you build anything on top of the setup, it's worth confirming that it worked.

### Check semantic view

A semantic view (SV) describes a set of tables in business terms, with metrics and dimensions an agent can query. Scripts `05` and `06` each create three of them, so listing the semantic views in the `SAP` schema should show six. Run the statement below in a SQL worksheet.

```sql
SHOW SEMANTIC VIEWS IN SCHEMA BUSINESS_ONTOLOGY.SAP;
```

**Expected after checking semantic views:** the statement returns six rows. These are the selected name and schema columns, sorted here for readability.

| name | database_name | schema_name |
|---|---|---|
| FINANCE_BARE_SV | BUSINESS_ONTOLOGY | SAP |
| FINANCE_ENRICHED_SV | BUSINESS_ONTOLOGY | SAP |
| PROCUREMENT_BARE_SV | BUSINESS_ONTOLOGY | SAP |
| PROCUREMENT_ENRICHED_SV | BUSINESS_ONTOLOGY | SAP |
| SALES_BARE_SV | BUSINESS_ONTOLOGY | SAP |
| SALES_ENRICHED_SV | BUSINESS_ONTOLOGY | SAP |

The three enriched views are the ones the rest of the guide uses. The three bare views support `BARE_AGENT`, which the current B/C Python benchmark does not call. If any views are missing, rerun the script that creates them, `05_bare_svs.sql` or `06_enriched_svs.sql`, and expect the complete six-row list above.

With the data and semantic views in place, you're ready to build the ontology itself, starting with the domains that hold everything else.

## 1. Create Domains

A domain is a container for one business area, such as Procurement. It groups the nodes that area owns, where a node is any entry in the ontology: an entity, a metric, a term or a policy. The demo uses three domains, one for each part of the business the questions touch.

To create the domains, open `sql/07_ontology.sql` and run the `Domains` section (the three `SYSTEM$CREATE_GLOSSARY_DOMAIN` statements).

**Expected:** each call returns a domain ID with `error` set to `false`. This selected-field excerpt shows the Procurement result; the other two results name Finance & Controlling and Sales & Distribution.

```json
{
  "error": false,
  "domainId": "<generated-domain-id>",
  "name": "Procurement",
  "path": "Business Ontology > Procurement"
}
```

If you'd rather describe what you want in plain language than run SQL, you can build the same domains with Cortex Code.

### Use CoCo

To create the domains through the skill, open **Catalog > Business Ontology** in Snowsight, click **Generate Ontology**, and paste the prompt below into the CoCo panel that opens on the right. Keep that panel open for the later steps' prompts. It asks the skill to create the three domains and write a description for each one that states its scope and its accountable business owner.

```
$business-ontology Create three domains: Procurement, Finance & Controlling, Sales & Distribution.
Describe each one's scope and its accountable business owner.
```

**Expected from CoCo (illustrative review content):** review the names, scope and stewardship descriptions before confirming creation. No particular owner identity is assumed.

| Proposed domain | Scope | Stewardship to confirm |
|---|---|---|
| Procurement | Suppliers, materials, purchasing and logistics | Procurement business owner |
| Finance & Controlling | Postings, costs and financial metrics | Finance business owner |
| Sales & Distribution | Orders, customers and pricing | Sales business owner |

Whichever way you choose, the same SQL function does the work, and knowing it helps when you read the script or debug an error.

### The SQL Behind It

Both the script and the prompt call this function underneath. One call looks like `SYSTEM$CREATE_GLOSSARY_DOMAIN('Procurement')`, and you don't need to run it separately. Domains are created immediately and don't need approval. The API can't set owners and stewards yet, so record stewardship in the domain description. Domains can't be renamed yet, so choose names carefully.

With the domains created, confirm that all three are there before you add anything to them.

### Check

First, look at the result of each of the three statements: each should return without an error. Then, in Snowsight, open **Catalog > Business Ontology** and look at the list of domains. You should see three new domains named exactly Procurement, Finance & Controlling and Sales & Distribution, each with no nodes yet. If a statement fails with an `Insufficient privileges` error, your primary role is missing `CREATE ONTOLOGY DOMAIN` (see **Troubleshooting**). Retry creation only after confirming that the statement failed and the domain was not created.

**Expected catalog state (illustrative layout):** after the three creation calls succeed, look for these domains in the catalog.

| Domain | Nodes before Step 2 |
|---|---|
| Procurement | None yet |
| Finance & Controlling | None yet |
| Sales & Distribution | None yet |

If a domain is absent only in the UI, check filters and refresh before retrying creation; do not infer that a successful SQL call failed from a stale page.

The domains are empty containers for now. Next, you fill them with entities, the business objects that everything else connects to.

## 2. Add Entities

Entities are the business objects that metrics measure, such as a supplier, a material or a customer. Each one is described in business language, so a reader who doesn't know the tables can still understand it, and names the key column that identifies it.

Back in `07_ontology.sql`, run the three node sections (`Procurement nodes`, `Finance & Controlling nodes`, `Sales & Distribution nodes`), stopping at the `Approve` comment. The script is organised by domain, so this one run drafts the entities, metrics, terms and policies for Steps 2 to 4 together: 39 drafts. A draft is a node that has been written but not yet approved, so agents can't use it yet. Steps 3 and 4 explain the metrics, terms and policies you just drafted and have nothing extra to run.

**Expected:** 39 successful draft responses. The Supplier response below shows the shape; each draft has its own generated term ID.

```json
{"error":false,"termId":"<generated-term-id>","termName":"Supplier","state":"DRAFT"}
```

As in Step 1, you can draft the entities with a prompt instead of the script.

### Use CoCo

To draft the entities through the skill, paste the prompt below into CoCo. It lists each entity by domain, with a business description and, for *Supplier*, the key that identifies it and the vendors it excludes. The skill turns each line into a draft node.

```
$business-ontology Add these entities to Procurement:
- Supplier: an active vendor we purchase from, identified by vendor number (LFA1.LIFNR).
  Vendors in a probationary account group are vendor records but not suppliers.
- Material, Assembly, Bill of Materials, Purchase Order, Shipment, Carrier, Inspection Lot
Add AP Line Item and Cost Posting to Finance & Controlling.
Add Sales Order, Customer and Pricing Condition to Sales & Distribution.
```

**Expected from CoCo (illustrative review content):** proposed entities with business descriptions, followed by draft IDs if you confirm. This prompt drafts entities only; it does not reproduce the script's metrics, terms and policies.

| Candidate | Kind | Definition detail to review |
|---|---|---|
| Procurement.Supplier | ENTITY | Vendor number `LFA1.LIFNR`; probationary exclusion |
| Finance & Controlling.AP Line Item | ENTITY | An accounts-payable posting line |
| Sales & Distribution.Customer | ENTITY | A customer identified in sales and pricing data |

Each entity becomes one call to the function below.

### The SQL Behind It

Both the script and the prompt call this function underneath. One call looks like `SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"Supplier","domainName":"Procurement","itemKind":"ENTITY","description":"<business-description>"}')`, and you don't need to run it separately. The description is a placeholder in this reference example. The skill shows each draft before it writes it.

Because this one run drafts 39 nodes at once, check that every statement worked before you move on.

### Check

Look at the result of each statement as it runs. All 39 should succeed, and each one returns the ID of the draft it created. If any statement returns an error, fix the cause and rerun only that statement, because rerunning the whole section drafts the other nodes twice. The drafts don't appear in **Catalog > Business Ontology**, in the approved term list or to agents yet. That's expected, and it changes when you approve them in Step 5.

**Expected check summary for the script path:** use this checklist to review your draft responses; it is not a separate SQL result.

```text
Draft responses: 39
Each response: error=false, state=DRAFT, termId present
Approval: still pending
```

Entities give the ontology its nouns. Next come the metrics that measure them, which is where most of the conflicts the ontology resolves actually live.

## 3. Add Metrics

A metric is a number the business reports, such as a supplier count or revenue. Many questions have more than one plausible answer: "how many suppliers" could mean all vendor records or only the active ones. So for each metric, the ontology records which number is canonical, meaning the official one, and **also adds the defensible-but-wrong look-alike** as its own node that says it is not the canonical one. That gives the agent both options to tell apart, instead of only the one it might stumble on.

There's nothing new to run here, because Step 2 already drafted all 16 metrics. Instead, read them in `07_ontology.sql` to see the pattern, for example *Supplier Count* next to *Vendor Record Count*, and *Revenue* next to *Gross Bookings*.

To see how the same metrics are described in plain language, look at the prompt below, which drafts them with the skill.

### Use CoCo

To draft the metrics through the skill, paste the prompt below into CoCo. It gives each canonical metric with its formula and, next to it, the look-alike metric that says it is not the canonical one, so the skill drafts both as separate nodes.

```
$business-ontology Add these metrics to Procurement:
- Supplier Count: number of active suppliers. Canonical answer to "how many suppliers".
  Excludes probationary vendors. Formula: COUNT(DISTINCT LIFNR) WHERE account group is not probationary.
- Vendor Record Count: all vendor master records, including probationary.
  NOT the supplier count; use only when the question is explicitly about vendor records.
- On-Time Delivery Rate: share of deliveries where actual goods-issue date <= planned date (LIKP).
  Canonical OTD.
- Carrier Reported On-Time Rate: carriers' self-reported OTD (LFA2.OTRAT).
  NOT our OTD; do not use as on-time delivery.
- Procurement Spend, BOM Cost Rollup
```

**Expected from CoCo (illustrative review content):** separate canonical and look-alike candidates. Review the formula and the implementing view rather than assuming this abbreviated prompt produces all 16 demo metrics.

| Candidate | Decision recorded |
|---|---|
| Supplier Count | Official count; exclude probationary vendors |
| Vendor Record Count | All records; not the official supplier count |
| On-Time Delivery Rate | Operational delivery dates determine OTD |
| Carrier Reported On-Time Rate | Carrier self-report; not operational OTD |

The prompt covers Procurement only, but every domain follows the same canonical and look-alike pattern, and a few rules apply to all metrics.

### Metric Notes

The other two domains contain these metrics:

- **Finance & Controlling:** COGS Raw Materials, COGS Freight, Cost Center Total, Product Gross Margin, Customer Profit, Break-even Discount.
- **Sales & Distribution:** Revenue (net of discounts) versus Gross Bookings (NOT revenue), Customer Discounts, Revenue at Risk.

Keep these rules in mind when you read or write a metric:

- `formula` is **descriptive**, not executable. The agent computes numbers with the SV metric and uses the formula to check it (see Step 9). Write it so a reviewer can see the rule: the numerator, the denominator, the filter and the grain.
- Only `METRIC` nodes carry `formula`. The formula is returned by `SYSTEM$GET_GLOSSARY_TERM`, not by graph or list reads.
- **Cross-domain metrics are the exception.** No single SV computes *Product Gross Margin* or *Revenue at Risk*. Their definitions must name each component and the bridge between domains (for example, "sold assembly → BOM components → material standard cost"), because the agent combines those components itself.

### Check

This is a review-only step on the script path, with no additional execution. Step 2 already returned the metric drafts; Step 6 reads them back after approval.

**Expected from reviewing the script:** the Supplier Count draft contains the fields below. This is source content to recognise, not an approved-node query result at this point.

```json
{
  "name": "Supplier Count",
  "itemKind": "METRIC",
  "formula": "COUNT(DISTINCT LIFNR) WHERE KTOKK IN (ZSTR, ZSTD)"
}
```

Metrics settle which number is official. Terms and policies add the company vocabulary and the business rules that the data alone doesn't spell out.

## 4. Terms and Policies

Data often holds codes that mean nothing to a newcomer, such as `ZPRB` for a probationary vendor, and companies have their own vocabulary, such as "Tier A supplier". **Terms** decode those codes and capture that vocabulary. **Policies** are business rules the agent must apply, such as leaving probationary vendors out of supplier counts.

There's nothing new to run here either: Step 2 drafted 7 of the 8 terms and all 3 policies. The eighth term, *Tier A Supplier*, is added at the end of Step 5, because the script adds it in its own section after the relationships.

The prompts below show the same terms and policies in plain language.

### Use CoCo

To draft the terms and policies through the skill, paste the two prompts below into CoCo, one at a time. The first drafts the terms. Each line names a term, the code field it decodes, and the code values that business rules depend on.

```
$business-ontology Add these terms:
Procurement:
- Vendor Account Group: KTOKK on LFA1. ZSTR=Strategic, ZSTD=Standard, ZPRB=Probationary
  (flagged EXCLUDE_FROM_ACTIVE_COUNT in reference table T077K).
- Material Group: MATKL on MARA. Full mapping in T023T.
- Tier A Supplier: our internal name for strategic suppliers, meaning vendors in account group ZSTR.
  Synonyms: tier-A, strategic supplier.
Finance & Controlling: Posting Key (31 = invoice, 34 = credit memo), GL Account, Cost Object
Sales & Distribution: Condition Type (PR00 base, K007 customer discount, KF00 freight), Sales Organization
```

**Expected from CoCo (illustrative review content):** terms that explain code fields and company vocabulary. This alternative includes Tier A Supplier now; do not draft it again in Step 5 if you already created it.

| Candidate | Meaning to review |
|---|---|
| Vendor Account Group | ZSTR = strategic, ZSTD = standard, ZPRB = probationary |
| Tier A Supplier | ZSTR suppliers only; not all active suppliers |
| Posting Key | 31 = invoice; 34 = credit memo |
| Condition Type | PR00 = base price; K007 = discount; KF00 = freight |

Once the terms are drafted, paste the second prompt, which drafts the three policies. Each line names the domain and the policy, followed by the rule the agent must apply.

```
$business-ontology Add these policies:
- Procurement / Probationary Vendor Exclusion: probationary vendors are excluded from supplier
  counts and supplier KPIs until promoted.
- Finance & Controlling / Credit Memo Sign Rule: credit memos (posting key 34) are subtracted
  from every cost and COGS total.
- Procurement / BOM Input Protection: a material used at any level of a sold assembly's BOM is a
  production input and must not be cut to reduce spend.
```

**Expected from CoCo (illustrative review content):** three policy proposals, with the rule and domain visible before writing drafts.

| Policy | Rule to review |
|---|---|
| Procurement.Probationary Vendor Exclusion | Exclude probationary vendors from supplier counts and KPIs |
| Finance & Controlling.Credit Memo Sign Rule | Subtract posting-key 34 credit memos |
| Procurement.BOM Input Protection | Protect production inputs at every level of a sold assembly's BOM |

The *Vendor Account Group* term lists only three code values, even though real code fields can have hundreds. The tip below explains why.

### Scaling Code Fields

> **Scale code fields with one term per field, not one per value.** Inline only the values that business rules depend on. Keep the full code list in a reference table joined in the SV, and link the term to it with a `REFERENCE_DATA` representation. New code values arrive through ETL. The term changes only when the *rule* changes.

### Check

This is also review only on the script path; no additional execution is required. Step 6 confirms that every node in all three domains, including these, is approved and counted.

**Expected from reviewing Step 2's results:** the terms and policies are still drafts. Tier A Supplier is not yet present on the script path.

```text
Terms drafted by the script: 7
Policies drafted by the script: 3
Tier A Supplier: added in Step 5
```

Every node is now drafted. Next, you approve the drafts and connect them with typed relationships, so the ontology becomes a connected graph rather than a list.

## 5. Define Relationships

So far the nodes are a list. Relationships connect them into a graph, with an edge, or link, between two nodes. Each edge has a type that says how the nodes relate, for example that *Supplier Count* `MEASURES` *Supplier*. Use the most specific type that fits. An edge runs from a source node to a target node, except `IS_A`, which runs from the instance or subtype to the class. The table lists each type, when to use it, and an example from the demo.

| Type | Use for | Demo example |
|---|---|---|
| `MEASURES` | a metric quantifies an entity | Supplier Count MEASURES Supplier |
| `DERIVES` | the target is computed from the source | Revenue DERIVES Product Gross Margin |
| `CLASSIFIES` | a code or dimension categorises an entity | Vendor Account Group CLASSIFIES Supplier |
| `APPLIES_TO` | a policy constrains a concept | Probationary Vendor Exclusion APPLIES_TO Supplier Count |
| `HAS_PART` | a structural component | Bill of Materials HAS_PART Material |
| `HAS_VARIANT` | the same concept, scoped or narrowed | a look-alike or scoped variant of a canonical metric |
| `IS_A` | a subtype or instance | Tier A Supplier IS_A Supplier |
| `IDENTIFIED_BY`, `SCOPES`, `EQUIVALENT_TO` | keys, context boundaries, true synonyms with their own definition | Not used in the demo |
| `RELATED_TO` | only when nothing else fits | used sparingly |
| `CUSTOM` | only on explicit request, and needs a label | Not used in the demo |

Work through the three actions below in this order, using `07_ontology.sql` and the approval SQL in this guide. Relationship calls refer to nodes by name, and only approved nodes can be found by name, so the first action approves the drafts. The script's approval placeholder is commented out: running the script alone does not perform this approval.

1. Run the SQL below from this guide in the same worksheet session to approve the 39 drafts from Step 2. The statement approves every draft that this worksheet session created, and nothing drafted in other sessions, so the nodes exist as approved terms before the relationships refer to them.

   ```sql
   SELECT SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('[]', 'ACTIVE', '{"sessionId":"CURRENT_SESSION"}');
   ```

   **Expected:** the first approval returned the following totals. The per-term `results` field is omitted here.

   ```json
   {"error":false,"approved":39,"failed":0,"skipped":0,"truncated":false}
   ```

2. Run the `Relationships` section: 49 `SYSTEM$CREATE_GLOSSARY_RELATIONSHIP` statements.

   **Expected:** 49 successful responses. This selected-field excerpt is from the first relationship.

   ```json
   {"error":false,"sourceTermName":"Assembly","targetTermName":"Bill of Materials","relationshipType":"HAS_PART","state":"APPROVED"}
   ```

3. Run the last section, `Added for benchmark Q19`, in three parts: the *Tier A Supplier* draft from the script, then run the approval SQL above from this guide again in the same worksheet session, then run its two relationships from the script. Do not skip the approval between the draft and its relationships. That makes 40 nodes and 51 relationships.

   **Expected:** the draft response, the second approval totals and the two relationship responses contain these fields, in order. These counts apply to the full script path without duplicate drafts.

   ```json
   {"error":false,"termId":"<generated-term-id>","termName":"Tier A Supplier","state":"DRAFT"}
   ```

   The second approval promotes only the new Tier A Supplier draft.

   ```json
   {"error":false,"approved":1,"failed":0,"skipped":0,"truncated":false}
   ```

   The two relationship results are summarised below.

   | sourceTermName | targetTermName | relationshipType | state | error |
   |---|---|---|---|---|
   | Vendor Account Group | Tier A Supplier | CLASSIFIES | APPROVED | false |
   | Tier A Supplier | Supplier | IS_A | APPROVED | false |

If you're using CoCo instead, the prompt below defines the relationships for you.

### Use CoCo

To define the relationships through the skill, paste the prompt below into CoCo. It names a few relationships explicitly, using domain-qualified names and the relationship types from the table above, then asks the skill to propose the rest for you to review.

```
$business-ontology Define these relationships (use domain-qualified names):
- Procurement.Supplier Count MEASURES Procurement.Supplier
- Procurement.Probationary Vendor Exclusion APPLIES_TO Procurement.Supplier Count
- Procurement.Vendor Account Group CLASSIFIES Procurement.Tier A Supplier
- Procurement.Tier A Supplier IS_A Procurement.Supplier
- Sales & Distribution.Revenue DERIVES Finance & Controlling.Product Gross Margin
- Procurement.BOM Cost Rollup DERIVES Finance & Controlling.Product Gross Margin
Then find more relationships I missed in each domain.
```

**Expected from CoCo (illustrative review content):** a list of proposed edges, distinguishing the ones you requested from additional suggestions. Review and approve the referenced nodes first. A shortened prompt does not guarantee the script's 51 edges.

| Source | Type | Target | Review |
|---|---|---|---|
| Procurement.Supplier Count | MEASURES | Procurement.Supplier | Requested |
| Procurement.Tier A Supplier | IS_A | Procurement.Supplier | Requested |
| Sales & Distribution.Revenue | DERIVES | Finance & Controlling.Product Gross Margin | Requested cross-domain link |
| Additional candidates | Most specific applicable type | Proposed target | Review before writing |

Whichever way you created them, it helps to see what the relationships look like as a picture.

### The Resulting Graph

The graph below shows a slice of what you just created. Each box is a node, coloured by kind (entities white, metrics blue, terms purple, policies red), and each arrow is a typed relationship. Notice how *Revenue* in Sales & Distribution and *BOM Cost Rollup* in Procurement both feed *Product Gross Margin* in Finance & Controlling: those two `DERIVES` edges are the cross-domain bridge.

![A slice of the demo graph](assets/relationships.png)

Each arrow in that picture comes from one call to the function below.

### The SQL Behind It

Both the script and the prompt call this function underneath. One call looks like `SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('Procurement.Tier A Supplier','Procurement.Supplier','IS_A')`, and you don't need to run it separately. That call creates the edge straight away. For reference only, the alternative `SYSTEM$DRAFT_GLOSSARY_RELATIONSHIP` workflow drafts an edge for later approval; it is not an additional execution step here. Both calls accept domain-qualified names or term IDs.

The graph is useful to people, but the agent doesn't read it directly, which affects how you write your definitions.

### What the Agent Sees

> **Important:** agent search results **do not include relationships**. The agent follows links by reading definitions. Graph edges are for governance, lineage and the catalog. Any link the agent must follow, especially a cross-domain bridge, must **also** be stated in the description text.

With that in mind, confirm that the three actions worked.

### Check

Look at the results of the three actions. Both approve statements should succeed, and all 51 relationship statements (49 in the `Relationships` section and 2 for *Tier A Supplier*) should return without an error. A relationship statement that fails usually names a node that isn't approved yet, so rerun the approve statement and then rerun only the failed relationship. In **Catalog > Business Ontology**, the nodes now appear in their domains, and opening *Supplier Count* shows its `MEASURES` link to *Supplier*.

**Expected:** the SQL responses show the two approval totals above and `error:false` for all 51 relationships. The catalog detail should expose the following connection, shown here as an illustrative text view.

```text
Procurement.Supplier Count
  MEASURES -> Procurement.Supplier
```

With nodes and relationships in place, take a moment to confirm that everything is approved and counted correctly before you connect it to data.

## 6. Approve and Verify

Agents can only use approved nodes, so a draft that was missed is invisible to them. If you followed Step 5, everything is already approved, and this step confirms it before you go further.

Start by running the queries in the **Check** below. If any counts are short, first identify the missing drafts, then use one of the two forms below. These are alternative recovery examples, not two statements to run together. Replace `<generated-term-id>` with an actual draft ID for the first form; the second approves drafts from the current session. No recovery execution is needed when the checks pass.

```sql
-- Approve specific drafts, or everything from this session. Never call with no arguments:
-- an unscoped call promotes CREATE drafts account-wide.
SELECT SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('["<generated-term-id>"]');
SELECT SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('[]', 'ACTIVE', '{"sessionId":"CURRENT_SESSION"}');
```

**Expected for recovery (illustrative):** inspect the returned counts and per-term results rather than expecting another batch of 39. For one valid unapproved draft, the selected fields would look like this.

```json
{"error":false,"approved":1,"failed":0,"skipped":0}
```

Already approved or unavailable drafts can produce different totals. After recovery, the checks below should show 19/12/9, regardless of which approval form you used.

If you'd rather have CoCo find any leftover drafts for you, use the prompt below instead of the SQL above.

### Use CoCo

To find and approve any remaining drafts through the skill, paste the prompt below into CoCo. It lists the drafts this session created, so you can review them before the skill approves them.

```
$business-ontology Show all drafts I created this session and approve them.
```

**Expected from CoCo (illustrative review content):** a session-scoped draft list and approval proposal. On the completed script path there should be nothing left to approve; do not approve unrelated drafts to reach a target count.

```text
Scope: drafts created in this session
Review: each remaining draft's name, domain and ID
Next: approve only the reviewed drafts, or report no remaining drafts
```

Either way, the check below tells you whether anything is still missing.

### Check

Run the two queries below. The first counts the approved nodes in each domain, and the second reads back the formula of the *Supplier Count* metric.

```sql
SELECT 'Procurement' AS domain, ARRAY_SIZE(PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM_LIST('Procurement')):terms) AS nodes
UNION ALL SELECT 'Finance & Controlling', ARRAY_SIZE(PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM_LIST('Finance & Controlling')):terms)
UNION ALL SELECT 'Sales & Distribution', ARRAY_SIZE(PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM_LIST('Sales & Distribution')):terms);

-- Formula is returned only by the per-term read (argument must be a constant)
SELECT PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM('Procurement.Supplier Count')):formula::STRING;
```

#### Expected

The first query returns these three rows (40 approved nodes in total).

| DOMAIN | NODES |
|---|---|
| Procurement | 19 |
| Finance & Controlling | 12 |
| Sales & Distribution | 9 |

The second query returns one string. The expression is descriptive formula text, not SQL to execute.

```text
COUNT(DISTINCT LIFNR) WHERE KTOKK IN (ZSTR, ZSTD)
```

If a count is short, check for missing or unapproved drafts, approve the intended ones with a scoped form above, and run the check again. If the formula is empty or the read fails, inspect the term's name, approval state and stored formula; an empty formula alone does not prove it is a draft.

For reference only, with no additional execution required, `SYSTEM$GET_GLOSSARY_GRAPH('Procurement')` reads the approved graph and `SYSTEM$GET_GLOSSARY_DRAFT_GRAPH()` reads drafts. A domain graph can include neighbouring domains and can be truncated, so do not use its returned edge count as proof of all 51 relationships.

The ontology now says what things mean. Next, you tie each node to the Snowflake object that implements it, so the agent knows where to compute each answer.

## 7. Add Representations

The ontology now defines what each node means, but not where its data lives. A representation fills that gap: it records which Snowflake object, such as a table, a column or a semantic view metric, implements a node. This is not just catalog decoration. The skill's agent builder reads approved SV representations to write each SV tool's description, and that description is how the agent chooses which view to query.

There are five representation roles, and each one links a particular kind of node to a particular kind of Snowflake object. The diagram below shows each pairing.

![Representation roles](assets/representations.png)

The table lists the same roles, with how many of each the demo creates.

| Role | From → To | Demo count |
|---|---|---|
| `IMPLEMENTS` | metric → the exact SV metric (field level) | 12 |
| `RELATED_SEMANTIC_VIEW` | cross-domain metric → each SV that supplies a component | 8 |
| `REPRESENTS` | entity → table or view | 14 |
| `DESCRIBES` | term → column | 7 |
| `REFERENCE_DATA` | term → code table (T077K, T023T) | 2 |

Run all of `sql/08_representations.sql`, which contains 43 `SYSTEM$CREATE_GLOSSARY_ASSOCIATION` statements.

**Expected:** 43 responses with `error:false`. The first response contains these fields; validity is checked separately by reading the node back.

```json
{
  "error": false,
  "termName": "Supplier Count",
  "fqn": "BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV",
  "entityQualifier": "VENDORS",
  "subObjectName": "ACTIVE_SUPPLIER_COUNT",
  "associationRole": "IMPLEMENTS",
  "state": "APPROVED"
}
```

As with the earlier steps, CoCo can add the representations from a prompt instead.

### Use CoCo

To add the representations through the skill, paste the prompt below into CoCo. It links one metric to its semantic view metric explicitly, then asks the skill to propose a representation for every other node and show them to you for review before it writes them.

```
$business-ontology In Procurement, associate the metric Supplier Count with metric
ACTIVE_SUPPLIER_COUNT (logical table VENDORS) in semantic view
BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV as IMPLEMENTS.
Then propose representations for every other node in all three domains and show them for review.
```

**Expected from CoCo (illustrative review content):** the explicit Supplier Count mapping plus proposals for the remaining nodes. Review the object, logical table and field, not just the view name. The proposed total can differ from 43.

| Node | Role | Target to review |
|---|---|---|
| Procurement.Supplier Count | IMPLEMENTS | `BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV`, `VENDORS.ACTIVE_SUPPLIER_COUNT` |
| Sales & Distribution.Customer | REPRESENTS | `BUSINESS_ONTOLOGY.SAP.CUSTOMERS_VIEW` |

Each of the 43 representations comes from one call to the same function.

### The SQL Behind It

The script and the skill both call `SYSTEM$CREATE_GLOSSARY_ASSOCIATION`. The example below, one of the 43 statements, links the *On-Time Delivery Rate* metric to the `OPERATIONAL_OTD_RATE` metric on the `SHIPMENTS` logical table in `PROCUREMENT_ENRICHED_SV`, with the role `IMPLEMENTS`. This is reference only, with no additional execution required because it is already in the script.

```sql
SELECT SYSTEM$CREATE_GLOSSARY_ASSOCIATION('Procurement.On-Time Delivery Rate',
  '{"refType":"SEMANTIC_VIEW","fqn":"BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV",
    "subObjectType":"METRIC","entityQualifier":"SHIPMENTS","subObjectName":"OPERATIONAL_OTD_RATE"}',
  'IMPLEMENTS');
```

One caution applies to representations after you create them:

> In preview, representations are **not revalidated** when a semantic view is rebuilt, renamed or dropped, and there is no automatic drift detection between a definition and its implementation. After any SV change, re-check with `$business-ontology Find drift between ontology and semantic views`.

**Expected from the drift prompt (illustrative review content):** a comparison of meaning, binding and current SQL, followed by proposed fixes for review. A stored `VALID` flag alone is not proof that the implementation still matches.

| Node | Comparison to review | Next action if different |
|---|---|---|
| Procurement.Supplier Count | Approved exclusion rule versus `VENDORS.ACTIVE_SUPPLIER_COUNT` SQL in `FINANCE_ENRICHED_SV` | Review both definition and implementation changes |
| Sales & Distribution.Customer | Representation target versus current `CUSTOMERS_VIEW` | Repair the binding if the target changed |

Next, confirm that the representations were created and point at real objects.

### Check

Look at the result of each statement as it runs. All 43 should succeed (19 for Procurement nodes, 14 for Finance & Controlling and 10 for Sales & Distribution), and each result should contain `"error":false`. If a result contains `"error":true`, inspect its message and the node and object names. Then run the query below to read back the representations of two nodes, one metric and one entity.

```sql
SELECT 'Supplier Count' AS node, TO_JSON(PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM('Procurement.Supplier Count')):representedAs) AS representations
UNION ALL SELECT 'Customer', TO_JSON(PARSE_JSON(SYSTEM$GET_GLOSSARY_TERM('Sales & Distribution.Customer')):representedAs);
```

#### Expected

The query returns two rows. These selected fields from each `REPRESENTATIONS` value make the targets easier to read.

| NODE | associationRole | fqn | entityQualifier / subObjectName | validity |
|---|---|---|---|---|
| Supplier Count | IMPLEMENTS | BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV | VENDORS / ACTIVE_SUPPLIER_COUNT | VALID |
| Customer | REPRESENTS | BUSINESS_ONTOLOGY.SAP.CUSTOMERS_VIEW | Not applicable | VALID |

The Supplier Count array contains an object with the fields below; additional returned fields are omitted here.

```json
[
  {
    "refType": "SEMANTIC_VIEW",
    "fqn": "BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV",
    "subObjectType": "METRIC",
    "entityQualifier": "VENDORS",
    "subObjectName": "ACTIVE_SUPPLIER_COUNT",
    "associationRole": "IMPLEMENTS",
    "validity": "VALID"
  }
]
```

The complete script path creates 43 representations: 19 on Procurement nodes, 14 on Finance & Controlling nodes and 10 on Sales & Distribution nodes. This two-row check samples only two of them; read every node back if you need to check all 43. If a representation is missing or invalid, inspect its creation response and target before rerunning the affected statement. Use the per-node read rather than a potentially truncated graph response.

The ontology is complete and bound to your semantic views. Before an agent can use it, though, it has to appear in search, which is what the next step checks.

## 8. Confirm Search Indexing

Agents don't read the ontology directly. They search an index, a searchable copy that Snowflake builds from your approved nodes in the background. In our trials, terms were first observed as searchable approximately 5 to 14 hours after the final ontology write. These are observation times, not guaranteed indexing durations. Confirm readiness with the search checks before proceeding. Deleted terms can also keep appearing in results for a while after deletion.

To find out whether the index is ready, run the three searches below in a terminal, using the Cortex Code command-line tool (CLI). They use the benchmark's supplier, Tier A and revenue probes. Run them against the same account and role as the agents; if your CLI default differs, add `-c <conn>` using your connection name.

```bash
cortex search object "supplier count active suppliers" --types=business-ontology
cortex search object "tier a suppliers" --types=business-ontology
cortex search object "revenue net of discounts" --types=business-ontology
```

**Expected:** results include the intended identities and definitions below. These sample contents use the guide's domain names rather than a fixed terminal layout. Rank, result count and duplicate-looking names can vary.

| Search | Identity to match | Definition detail to check |
|---|---|---|
| supplier count active suppliers | Procurement.Supplier Count (`METRIC`) | Active ZSTR/ZSTD suppliers; ZPRB excluded; `FINANCE_ENRICHED_SV` and `vendors.active_supplier_count` |
| tier a suppliers | Procurement.Tier A Supplier (`TERM`) | Tier A means vendor account group ZSTR, not all active suppliers |
| revenue net of discounts | Sales & Distribution.Revenue (`METRIC`) | Net of K007 discounts; `SALES_ENRICHED_SV` and `net_revenue` |

**Abridged, normalised search example:** this shows one matching result using the guide's domain names. The number is illustrative, not a promised rank.

```text
1. Procurement.Supplier Count (METRIC)
   Name: Supplier Count
   Domain: Procurement
   Definition: Official supplier count used in all reporting: active suppliers in account group ZSTR (strategic) or ZSTD (standard). Probationary vendors (ZPRB) are excluded by procurement policy. Canonical implementation: FINANCE_ENRICHED_SV metric vendors.active_supplier_count.
   Formula: COUNT(DISTINCT LIFNR) WHERE KTOKK IN (ZSTR, ZSTD)
```

### Check

Read the results that each search prints. Match the domain-qualified name, kind and definition to the table above. Where the result exposes an ID, compare it with the ID saved during creation or read-back; where it exposes a representation, check the intended `BUSINESS_ONTOLOGY.SAP` target. A similarly named term in another domain is not a pass. If a search returns no objects or an error, confirm the Step 6 counts and the searching role's access, then retry after allowing more time. An empty result alone does not identify the cause.

Because the agents depend on this index, the search result decides when you can move on.

> **Stop here until all three searches pass.** Creating the agents in Step 9 doesn't need the index, so you can run it while you wait. Don't ask the agents questions or run the benchmark until the searches pass. The harness uses these three probes and also checks for retired `SAP Purchasing`, `SAP Finance` and `SAP Sales` domain hits. Read its `ready=True` result in Step 10; a successful process exit alone is not an indexing check.

Once search can find your terms, or while you wait for it, you create the agents that put the ontology to work.

## 9. Build the Agent

A Cortex Agent is an AI assistant in Snowflake that answers questions by calling tools, such as a semantic view it can query. In this step you create agents that also have a tool for searching the ontology, so they look up what a term means before they compute anything.

The diagram below shows what happens when a question comes in. The agent first searches the ontology for each business term and gets back the canonical metric, any policies and the company vocabulary. It then computes the number with the semantic view metric that the definition names, combines results across domains when the metric spans more than one, and answers with the governed term cited.

![How the agent uses the ontology](assets/agent.png)

Run all of `sql/09_agents.sql`. It creates 7 agents with the same `auto` model setting and budget. Each BON agent adds ontology-oriented orchestration and citation instructions as well as the search tool. Agents with Business Ontology (BON) search turned on have `BON` in their name, such as `BON_AGENT`. An A/B comparison asks two configurations the same questions to see how their answers differ. The script labels its main configurations A (bare semantic views), B (enriched semantic views) and C (enriched semantic views plus BON). Arm A is an additional baseline not evaluated in this guide; the experiment compares B and C:

| Arm | Agent | Tools |
|---|---|---|
| B | `ENRICHED_AGENT` | 3 enriched SVs |
| C | `BON_AGENT` | the same 3 enriched SVs + `business_ontology` search |

The script also creates arm A, `BARE_AGENT` (the additional bare-SV baseline, not run by the current harness), and the benchmark consistency pairs `FINANCE_ENRICHED_AGENT` / `FINANCE_BON_AGENT` and `SALES_ENRICHED_AGENT` / `SALES_BON_AGENT`.

**Expected:** the seven creation statements returned these messages.

```text
Agent BARE_AGENT successfully created.
Agent ENRICHED_AGENT successfully created.
Agent BON_AGENT successfully created.
Agent FINANCE_ENRICHED_AGENT successfully created.
Agent FINANCE_BON_AGENT successfully created.
Agent SALES_ENRICHED_AGENT successfully created.
Agent SALES_BON_AGENT successfully created.
```

If you're building an agent for your own data, CoCo can write the agent for you.

### Use CoCo

To build the agent through the skill, paste the first prompt below into CoCo. It asks the skill to write the agent spec, with one tool for each enriched semantic view and the ontology search turned on, and to check the three ontology settings before it creates the agent.

```
$business-ontology Create an agent that uses the ontology for Procurement, Finance & Controlling
and Sales & Distribution, with tools for PROCUREMENT_ENRICHED_SV, FINANCE_ENRICHED_SV and
SALES_ENRICHED_SV in BUSINESS_ONTOLOGY.SAP.
```

**Expected from CoCo (illustrative review content):** an agent specification proposal using the three named views, plus the ontology tool and instructions. This single-agent prompt is not a replacement for all seven agents in the script.

```text
Proposed tools: query_procurement, query_finance, query_sales, business_ontology
Ontology flag: EnableSnowscopeBusinessOntologySearch = true
Search tool type: snowscope_search
Search corpus: businessOntology
Instructions: look up governed terms before querying; cite the term and metric
Next: review the specification before creation
```

If you already have an agent, the second prompt below adds the ontology to it instead of creating a new one. Review that the proposal preserves its existing tools while adding the search tool, settings and ontology instructions. This is an optional alternative: do not apply it to `ENRICHED_AGENT` if you plan to use that agent as the no-ontology baseline in Step 10.

```
$business-ontology Add the ontology to agent BUSINESS_ONTOLOGY.SAP.ENRICHED_AGENT
```

**Expected from CoCo (illustrative review content):** a before/after proposal to review before changing the existing agent.

| Item | Before | Proposed after |
|---|---|---|
| Enriched SV tools | Three | Same three |
| Ontology search | Absent | `business_ontology` with the flag/type/corpus above |
| Instructions | Existing analytics instructions | Existing instructions plus ontology lookup and citations |
| Evaluation role | No-ontology baseline | No longer a no-ontology baseline if applied |

To understand what the script or the skill actually creates, it helps to read the agent's specification.

### The Agent Spec

Whichever way you build it, the spec below is the core of the demo's `BON_AGENT`, shortened for reading (the full spec is in `sql/09_agents.sql`). It is reference only, with no execution required. It shows the ontology switch under `experimental`, the instructions that tell the agent to search the ontology before it queries data, and the four tools: one `business_ontology` search tool and one text-to-SQL tool for each enriched semantic view.

```yaml
models:
  orchestration: auto
experimental:
  EnableSnowscopeBusinessOntologySearch: true
orchestration:
  budget: {seconds: 150, tokens: 40000}
instructions:
  orchestration: |
    Before querying data, search business_ontology for each business term in the question,
    one concept per search. Use the governed definition to choose the canonical metric and to
    apply any policy. Compute numbers with the semantic view metric that implements the term;
    use the ontology formula only as a check. For cross-domain metrics, query each domain tool
    and combine the results as the definition describes.
  response: |
    State the answer first. When you used a governed definition, name the term (domain.node)
    and the semantic view metric that implements it.
tools:
  - tool_spec: {type: snowscope_search, name: business_ontology,
                description: "Governed business terms, metrics, entities and policies."}
  - tool_spec: {type: cortex_analyst_text_to_sql, name: query_procurement, description: "..."}
  - tool_spec: {type: cortex_analyst_text_to_sql, name: query_finance,    description: "..."}
  - tool_spec: {type: cortex_analyst_text_to_sql, name: query_sales,      description: "..."}
tool_resources:
  business_ontology: {corpus: businessOntology}
  query_procurement: {semantic_view: BUSINESS_ONTOLOGY.SAP.PROCUREMENT_ENRICHED_SV}
  query_finance: {semantic_view: BUSINESS_ONTOLOGY.SAP.FINANCE_ENRICHED_SV}
  query_sales: {semantic_view: BUSINESS_ONTOLOGY.SAP.SALES_ENRICHED_SV}
  # Execution environment settings are omitted from this reference excerpt.
```

Three lines in that spec are what connect the agent to the ontology, and they need extra care. **`CREATE AGENT` does not validate these three settings.** A typo is accepted, and the agent then silently never searches the ontology:

- `experimental.EnableSnowscopeBusinessOntologySearch: true`
- `tool_spec.type: snowscope_search`
- `tool_resources.business_ontology.corpus: businessOntology` (the resource key must equal the tool `name`)

Note the different spellings: the CLI search type is `business-ontology`, while the agent corpus is `businessOntology`.

That's why the check for this step reads the settings back from the agent you created.

### Check

Because `CREATE AGENT` accepts typos in the three settings above, confirm that they were saved correctly by describing `BON_AGENT`.

```sql
DESCRIBE AGENT BUSINESS_ONTOLOGY.SAP.BON_AGENT;
```

#### Expected

The statement returns one row. These selected fields from `agent_spec` were present in the saved agent; other tools and settings are omitted from this excerpt.

```json
{
  "experimental": {"EnableSnowscopeBusinessOntologySearch": true},
  "tools": [
    {"tool_spec": {"name": "business_ontology", "type": "snowscope_search"}}
  ],
  "tool_resources": {"business_ontology": {"corpus": "businessOntology"}}
}
```

If a setting is absent or misspelled, correct the specification and recreate the affected agent, then expect these same values on read-back. Correct configuration alone does not prove the agent actually searched; Step 10 checks its tool use. If you used CoCo, you can ask it to do the configuration check: `$business-ontology Verify the ontology settings on agent BON_AGENT`.

**Expected from CoCo (illustrative check content):** each required setting is compared with the saved specification, and any mismatch is reported rather than silently changed.

| Setting | Required value |
|---|---|
| experimental.EnableSnowscopeBusinessOntologySearch | true |
| business_ontology tool type | snowscope_search |
| tool_resources.business_ontology.corpus | businessOntology |

Everything is built. The last step compares the two configurations by asking agents with the same semantic views the same questions.

## 10. Run A/B Tests

In this step you compare `ENRICHED_AGENT` (B) and `BON_AGENT` (C). They use the same enriched semantic views, model setting and budget, while C adds ontology search plus instructions to use and cite governed definitions. This evaluates the combined configuration, not the isolated causal effect of adding a tool. Start with a quick hands-on comparison, then run the full benchmark if you want repeated-run scores.

### Try It

In Snowsight, open **AI & ML > Agents**, and ask `ENRICHED_AGENT` and then `BON_AGENT` the same two questions from the benchmark. For each question, the table gives the answer the ontology makes official and the look-alike answer an agent without it may give.

**Expected when opening the agents (illustrative UI state):** the selected agent's conversation is available. Check its object name before sending each question so the baseline and BON responses are not mixed.

| Question | Correct answer | Defensible-but-wrong answer |
|---|---|---|
| How many suppliers do we have? | 14 (active suppliers) | 15 (all vendor records, including probationary) |
| What is our revenue? | 711,915 (net of K007 discounts) | 746,000 (gross bookings) |

**Expected answer content:** the table below summarises the four observed diagnostic responses and tool paths, rather than reproducing exact chat formatting. Other runs can differ.

| Agent and question | Observed answer summary | Observed tool path |
|---|---|---|
| ENRICHED_AGENT: suppliers | Led with 15 suppliers on file, then offered 14 active | `query_procurement`, `system_execute_sql` |
| BON_AGENT: suppliers | 14 suppliers; ZSTR/ZSTD included, ZPRB excluded; official Supplier Count and `vendors.active_supplier_count` | `business_ontology`, `query_finance`, `system_execute_sql` |
| ENRICHED_AGENT: revenue | Offered both 711,915 net and 746,000 gross | `query_sales`, `system_execute_sql` |
| BON_AGENT: revenue | 711,915; governed Revenue, implemented by `SALES_ENRICHED_SV.net_revenue` | `business_ontology`, `query_sales`, `system_execute_sql` |

**Sample BON answers:** these excerpts are normalised and paraphrased from the observed responses for readability, not exact transcripts.

> **Suppliers:** We have 14 suppliers. The official Supplier Count includes strategic (ZSTR) and standard (ZSTD) vendors and excludes the probationary (ZPRB) vendor. Finance's `vendors.active_supplier_count` metric calculates this count.

> **Revenue:** Our revenue is 711,915, net of K007 customer discounts. This follows the governed `Sales & Distribution.Revenue` definition and uses the Sales view's `SALES_ENRICHED_SV.net_revenue` metric, rather than gross bookings.

These two questions check supplier and revenue definitions; they do not establish that every node is indexed or that every cross-domain question works. Inspect the tool responses to identify which domains supplied each answer.

Answer text alone does not prove ontology retrieval, even when it names a governed term. If the full `DATA_AGENT_RUN` response is available, inspect its `tool_use` and `tool_result` entries: match their `tool_use_id`, confirm a successful `business_ontology` result, and check the returned domain-qualified identity and definition against Step 8. Then check that retrieval precedes the computation tools. If only answer text is available, record retrieval as unverified.

**Illustrative extracted trace:** the observed tool names and returned identities are shown below with domain names normalised and matching IDs replaced by placeholders. This is a reading aid, not a runnable API request or a complete response schema.

```text
Suppliers:
  tool_use: business_ontology; query="supplier count"; tool_use_id=<supplier-search-id>
  tool_result: business_ontology; status=success; tool_use_id=<supplier-search-id>
    Returned identity: Procurement.Supplier Count (METRIC)
  Later tools: query_finance, system_execute_sql
Revenue:
  tool_use: business_ontology; query="revenue"; tool_use_id=<revenue-search-id>
  tool_result: business_ontology; status=success; tool_use_id=<revenue-search-id>
    Returned identity: Sales & Distribution.Revenue (METRIC)
  Later tools: query_sales, system_execute_sql
```

Once you have both agents' answers, compare them with the table.

#### Check

Compare the two agents' answers to each question against the table. `BON_AGENT` should give the correct answer, 14 suppliers and 711,915 in revenue, and name the governed term and metric it used, for example `Procurement.Supplier Count` implemented by `ACTIVE_SUPPLIER_COUNT`. `ENRICHED_AGENT` may give the right number on some runs, but it can also pick the look-alike or hedge ("15 or 14"), and it has no governed term to cite. Because agents vary from run to run, ask each question two or three times.

**Expected on repeats (evaluation criteria):** record the headline answer, whether it hedges, whether it names the governing term and metric, and whether it actually calls `business_ontology`. Repeats need not produce identical wording or a guaranteed baseline failure.

```text
Supplier target: 14; official Supplier Count; VENDORS.ACTIVE_SUPPLIER_COUNT
Revenue target: 711915; Sales & Distribution.Revenue; NET_REVENUE
BON tool-use check: business_ontology appears before computation
```

These diagnostic calls illustrate the difference, but they do not measure repeated-run accuracy. The optional benchmark does that across more questions.

### Run the Benchmark

This part is optional and needs the Python requirements in **What You'll Need**. The benchmark is a Python script that asks the agents 20 questions, grouped into four tiers, from controls that the semantic views alone can answer to questions that need cross-domain reasoning or governed definitions, and scores each answer against the correct one, called the ground truth, stored in `sql/04_ground_truth.sql`.

From the project folder created in the Setup section (your current directory should end in `/business-ontology/getting-started`), install the Snowflake Python connector the script needs. Stay in this folder for all benchmark commands below; the benchmark script is already present.

```bash
pip install snowflake-connector-python
```

**Expected (illustrative installation output):** pip reports that the connector was installed or was already available. Package versions and dependency lines depend on your environment.

```text
Successfully installed snowflake-connector-python-<installed-version>
```

Next, check the index using the same three probes as Step 8. Replace `<conn>` with your configured Snowflake connection name, not an API key or password.

```bash
SNOWFLAKE_CONNECTION_NAME=<conn> python -u benchmark/run_benchmark.py --check-index
```

**Expected (illustrative ready-state output):** all three expected names are found, there are no retired-domain hits, and the report ends with `ready=True`.

```text
BON search index check:
  'supplier count active suppliers': expected=found, retired-domain hits=none
  'revenue net of discounts': expected=found, retired-domain hits=none
  'tier a suppliers': expected=found, retired-domain hits=none
  ready=True
```

The current harness can exit successfully even with `ready=False`, and it does not surface every search-process error. Read the report and inspect the direct Step 8 results; do not use the shell exit code alone or bypass the gate. If a probe says `MISSING`, confirm access and identity and retry later. Do not delete unfamiliar domains just to make a retired-domain check pass.

Once that gate passes, run the full benchmark against arms B and C: 20 questions, 3 runs each (5 for tiers 2 and 3), plus the Finance/Sales consistency pairs. This optional command calls agents and an LLM judge and writes benchmark results.

```bash
SNOWFLAKE_CONNECTION_NAME=<conn> python -u benchmark/run_benchmark.py --arms B,C --runs 3 --runs-hard 5
```

**Expected (illustrative output shape):** progress lines followed by accuracy, stability, cost/traceability and consistency sections. Angle-bracket entries below are labels for values your run will produce, not sample measurements.

```text
run_id=<generated-run-id>: <scheduled-calls> agent calls, 6 parallel
  [<completed>/<scheduled-calls>] main B Q06 run1 <OK-or-BAD> <seconds>s tools=<count> val=<headline-value>
ACCURACY BY VALUE PILLAR (% correct)       B enriched  C +BON  BON uplift (C-B)
  <pillar>                               <B-score>  <C-score>  <difference>
STABILITY              same answer every run   always right
  arm B                     <stable-percent>% <always-right-percent>%
COST & TRACEABILITY   median s   avg tools   names term+SV metric   fell for trap   hedged
  arm B                <seconds> <count>       <percent>%           <percent>%     <percent>%
CONSISTENCY ACROSS TEAMS  Finance agent vs Sales agent, same question
  bon Q06 agree <percent>% both right <percent>%
Saved <project-folder>/benchmark/scorecard_<generated-run-id>.json; raw rows in BUSINESS_ONTOLOGY.SAP.BENCHMARK_RESULTS WHERE RUN_ID = '<generated-run-id>'
```

The harness also saves `benchmark/scorecard_<generated-run-id>.json` and rows in `BUSINESS_ONTOLOGY.SAP.BENCHMARK_RESULTS`. Its JSON scorecard contains `run_id`, `accuracy`, `stability`, `cost_trace` and `consistency`. Inspect these outputs after your run completes.

The harness includes Q07 in the Finance/Sales consistency comparison, but the Finance-only agent lacks the Sales view needed to answer that revenue question. Flag Q07 separately rather than interpreting that pair's disagreement as ontology performance.

A full run takes a while, because each question is asked several times. When it finishes, read the scorecard as described below.

#### Check

When the run finishes, compare arm B (`ENRICHED_AGENT`) with arm C (`BON_AGENT`) by value pillar and inspect the question-level results. Controls test whether both configurations can answer questions the semantic views already cover. Contested questions test canonical choices; do not assume every run must produce an uplift or a control-tier tie.

**Expected scorecard to compare against:** use the ground-truth answers to assess correctness and compare the B/C results from your own run. Review accuracy, stability, cost/traceability and team consistency together. Scores describe that run and the combined configuration; they are not a general accuracy guarantee or proof of a tool-only causal effect.

The benchmark measures this demo. When you build an ontology for your own data, you'll want an evaluation of your own, designed the same way.

### Design Your Own

When you evaluate an ontology on your own data, follow the same rules the demo used:

- **Questions:** write 5 to 10 per domain where meaning is contested (look-alike metrics, company vocabulary, policies, cross-domain chains). Add **controls** where the SV alone should succeed, and at least one question about a concept that doesn't exist, which the agent should decline to answer.
- **Runs:** run each question several times, because agents vary from run to run. The demo used 3 runs, and 5 for the hard tiers.
- **Scoring:** a hedged answer ("15 or 14") counts as wrong. Track accuracy, right on every run, hedging, and whether the answer cites a governed term.
- **Starting point:** adapt `benchmark/run_benchmark.py` and the ground-truth tables.

To get a first set of questions, paste the prompt below into CoCo. It asks the skill to draft 10 evaluation questions from your approved Procurement nodes, in the same mix of question types as the demo, each with its expected answer, its look-alike answer and the node that governs it.

```
$business-ontology Using the approved nodes in Procurement, draft 10 evaluation questions:
4 where two plausible metrics exist, 2 using company vocabulary, 2 that need a policy,
1 control a semantic view alone should answer, and 1 about a term that doesn't exist.
For each, give the expected answer, the wrong-but-defensible answer, and the governing node.
```

**Expected from CoCo (illustrative evaluation draft):** 10 proposed questions in the requested mix. The sample rows below show the content to review; confirm numeric ground truth against the data before using the draft as a benchmark.

| Question type | Sample question | Expected answer | Look-alike / refusal check | Governing node |
|---|---|---|---|---|
| Competing metrics | How many suppliers do we have? | 14 on this dataset | 15 is the vendor record count | Procurement.Supplier Count |
| Vocabulary | What does Tier A supplier mean? | ZSTR strategic suppliers | Not every active supplier | Procurement.Tier A Supplier |
| Policy | Do probationary vendors count as suppliers? | No | Including ZPRB conflicts with policy | Procurement.Probationary Vendor Exclusion |
| Unknown term | What is our Platinum-Plus supplier rule? | No approved definition found, if absent from your ontology | Do not invent a definition | None; verify absence |

For your own evaluation, the expected deliverable is a reviewed question set with ground truth, followed by repeat-run results recording correctness, hedging and citations. The suggested unknown term above is an illustrative test case, not an assertion about every account's catalog.

That completes the core build and the hands-on comparison: an approved ontology bound to semantic views and used by an agent. The full benchmark is optional, as is the section that follows.

## Going Further

The first part shows how to keep the ontology current as definitions change. The second shows how to start a new ontology from semantic views you already have.

### Update the Ontology

Once the ontology is live, the prompts below start common maintenance workflows. These are optional examples, not steps to run against the finished demo before evaluating it. Replace placeholder descriptions with approved business definitions. In particular, `<domain>` must identify a domain you own and intend to remove.

**Expected for each prompt (illustrative review content):** review the proposed change before applying it. The adjacent column shows the content to expect, not exact card formatting or guaranteed completion.

| Task | Prompt | Expected review content |
|---|---|---|
| Edit a definition or formula | `$business-ontology Update Procurement.Supplier Count: also exclude temporary vendors (ZTMP)` | Before: active ZSTR/ZSTD suppliers. Proposal: explicitly exclude ZTMP. Check whether SQL needs a change; ZTMP is already outside the demo metric's inclusion list. No invented new supplier count. |
| Add a metric | `$business-ontology Add a metric Net Price Realization to Sales & Distribution. Formula: <approved-formula>. Description: <approved-description>.` | Candidate name, domain, formula and business definition; ask for missing meaning rather than inventing the formula. |
| Find missing edges | `$business-ontology Find more relationships in the Finance & Controlling domain` | Candidate source/type/target and rationale; proposals can be empty if no further edges are justified. |
| Rename a node | `$business-ontology Rename Procurement.Inspection Lot to Quality Inspection` | Before: Inspection Lot. Proposed name: Quality Inspection. Approval pending; affected references shown for review. Search can still show the old name until refresh. |
| Delete a domain | `$business-ontology Delete the <domain> domain` | Exact target and dependent contents, followed by a destructive-action confirmation; no deletion before confirmation. |

Edits to **ACTIVE** nodes go through an **edit card** (`SYSTEM$DRAFT_GLOSSARY_TERM_UPDATE`). The live definition stays in force until the edit is approved, and agents see the change only after the index refreshes. The skill's quality gate shows the old and new values side by side.

**Expected after an approved maintenance change (illustrative state):** the node read-back reflects the approved name or definition; the search result catches up after indexing. For a deletion, the selected domain is absent after its contents are removed. A computational rule change also needs a matching semantic-view implementation and a drift review; approving text alone does not alter SQL.

Updating assumes the ontology already exists, as yours does now. If you're starting a new ontology on top of semantic views you already have, the skill can draft much of it for you.

### Bootstrap from Semantic Views

To start that way, paste the prompt below into CoCo, with your own database and schema in place of `BUSINESS_ONTOLOGY.SAP`. It asks the skill to read the semantic views in that schema and propose a draft ontology from them for you to review.

```
$business-ontology Bootstrap ontology from our semantic views in BUSINESS_ONTOLOGY.SAP
```

**Expected from CoCo (illustrative bootstrap review content):** candidates with source provenance and unresolved business decisions. Run this on a new ontology, not alongside the completed script path.

| Candidate | Evidence to show at review | Business decision still needed |
|---|---|---|
| Supplier entity | Vendor identity and joins in the semantic views | Official scope of a supplier |
| Supplier-count metric | `FINANCE_ENRICHED_SV.VENDORS.ACTIVE_SUPPLIER_COUNT` | Whether it is canonical |
| Vendor-record metric | `PROCUREMENT_ENRICHED_SV.VENDORS.VENDOR_RECORD_COUNT` | Whether it is an operational variant |
| IMPLEMENTS representation | Source view, logical table and metric | Confirm the proposed binding |

Candidate names and counts depend on your source metadata. Bootstrap output alone does not establish the demo's 40 nodes or its policies.

The skill scans the views (`SHOW`/`DESCRIBE`, metrics, comments, verified queries, join graph) and proposes:

- entities derived from the join graph, not one per table;
- metric and term candidates, with duplicates across views merged;
- a domain for each candidate, with its provenance shown;
- `IMPLEMENTS` representations back to the source metrics.

The diagram below shows that flow from left to right. The skill scans your views and proposes candidates, a steward reviews them, and the items the import can't infer are added by hand before everything becomes the approved ontology.

![Bootstrapping from semantic views](assets/bootstrap.png)

Nothing is written until you approve it at review. What the import **can't** infer is exactly where the value lies:

- which of two look-alike metrics is canonical;
- company vocabulary such as "Tier A";
- policies;
- cross-domain bridges.

Add those by hand using Steps 3 to 5. **Expected:** the review content should now distinguish canonical metrics, vocabulary, policies and cross-domain links as those steps illustrate. Approve and read back the selected nodes before testing search; exact counts depend on what you imported.

Semantic views aren't the only starting point. Depending on where your definitions live today, you can start from any of these sources:

**Expected for alternate sources (illustrative review content):** substitute your actual stage path, schema or context. Candidates and counts depend on the source contents and the import's outcome.

| You have | Prompt or reference | Expected review content |
|---|---|---|
| CSV, spreadsheet or document on a stage | `$business-ontology Import ontology terms from @my_stage/glossary.csv` | Source row or passage, proposed term, domain and definition; unresolved mappings flagged |
| dbt project | `$business-ontology Extract ontology from our dbt manifest at @my_stage/manifest.json` | Source model/metric, candidate concept and provenance; business meaning needing review |
| Table and column comments | `$business-ontology Extract terms from our tables in <db.schema>` | Source table/column comment paired with a candidate term; duplicates for review |
| Cortex Sense context | `$business-ontology Promote our <context> context to the ontology` | Selected context definitions and proposed ontology mappings; conflicts for review |
| Knowledge in people's heads | `$business-ontology I need an ontology for procurement. We count suppliers excluding probationary vendors.` | Supplier Count candidate, exclusion policy and questions about the implementation |
| OWL / RDF / Turtle | Reference only: `business-ontology-owl-dev`; no execution required in this guide | Confirm the skill's availability and supported import path before using it |

If any step didn't match its expected check, the table below maps common symptoms to their likely causes and fixes.

## Troubleshooting

Each row starts from what you see, then gives a possible cause, a fix and the state to check afterward. These are conditional recovery actions, not a script to run in full. **Expected** entries below are illustrative postconditions or review content; confirm the actual result after applying a fix.

| Symptom | Possible cause | Fix | Expected |
|---|---|---|---|
| `Unknown function SYSTEM$CREATE_GLOSSARY_DOMAIN` | Feature not enabled | Contact your account team | Confirmation of preview eligibility/enablement before retrying; no provisioning result is assumed |
| `Insufficient privileges ... must have CREATE ONTOLOGY DOMAIN` | Your primary role can't create top-level domains | Select a primary role with the privilege, or have an admin review `GRANT CREATE ONTOLOGY DOMAIN ON ACCOUNT TO ROLE <role>` with the intended role substituted | Role/grant review names the intended role and privilege; a subsequent domain call can return `error:false` as in Step 1 |
| A relationship statement fails | A node it names is still a draft | Approve the intended drafts (Step 5, action 1), then rerun only the failed statement | Approval counts reflect remaining drafts; relationship result has `error:false`, `state:APPROVED` |
| Node counts in Step 6 are short | Missing drafts or drafts made in another session | Create any missing drafts first. For existing drafts from another session, approve by actual term ID; the current-session prompt cannot select them | Review the intended names, domains and IDs; final script-path counts are 19/12/9 |
| Agent never calls `business_ontology` | Flag, type or corpus misspelled | `DESCRIBE AGENT` and check all three settings | Step 9's flag/type/corpus values match; a later answer trace actually includes `business_ontology` |
| Search returns nothing for new terms | Draft state, indexing delay, search error or lack of access | Confirm approval and role access, allow more time, then repeat Step 8's probes | Supplier Count, Tier A Supplier and Revenue match by identity and meaning; elapsed time alone does not establish readiness |
| Deleted or renamed terms still returned | Stale index | Wait for re-index; don't benchmark until probes are clean | Current identities and definitions are returned; absence of stale hits is checked, not inferred from elapsed time |
| Agent still picks the look-alike metric | Definition does not distinguish canonical and variant metrics | Review a separate look-alike metric and the applicable policy | Proposal: Vendor Record Count is operational; Supplier Count excludes ZPRB. After approval/indexing, test for a headline answer of 14 |
| Agent can't follow a cross-domain link | Bridge exists only as a graph edge | Also state the bridge in the definition text | Review content names the chain, for example sold assembly to BOM components to material standard cost; retest the answer |
| Agent picks the wrong SV tool | Tool description or representation is incomplete | Review `IMPLEMENTS` bindings and regenerate the spec, or edit tool descriptions | Supplier Count maps to `FINANCE_ENRICHED_SV.VENDORS.ACTIVE_SUPPLIER_COUNT`; agent tool selection agrees |
| `GET_GLOSSARY_TERM` error inside a query | The argument must be a constant | Pass a literal name or ID | Step 6's literal Supplier Count read returns the documented formula |
| Representation points at a rebuilt view | No revalidation in preview | Use the drift prompt in Step 7 | Review shows stored target versus current object and SQL; discrepancies remain flagged until repaired |
| `Invalid identifier` or parsing error near JSON | Quoting may be wrong | Inspect the SQL string and double embedded single quotes where required | The intended field text parses correctly and the call succeeds; do not assume every identifier error is a quoting issue |

For day-to-day work after this guide, the quick reference below collects the calls you used in one place.

## API Quick Reference

The table is reference only, with no execution required. It lists the calls already discussed; angle-bracket values are placeholders, not runnable identifiers. Read the corresponding build step for executable context and expected output.

| Operation | Call |
|---|---|
| Create domain | `SYSTEM$CREATE_GLOSSARY_DOMAIN('<name>')` |
| Draft node | `SYSTEM$DRAFT_GLOSSARY_TERM('{"name":"<name>","domainName":"<domain>","itemKind":"ENTITY","description":"<description>"}')`; use the appropriate kind and add `formula` only for a metric |
| Approve nodes | `SYSTEM$APPROVE_ALL_GLOSSARY_TERMS('["<generated-term-id>"]')` or `SYSTEM$APPROVE_GLOSSARY_TERM('<id or name>')` |
| Edit an active node | `SYSTEM$DRAFT_GLOSSARY_TERM_UPDATE(...)`, then approve the edit card |
| Relationship | `SYSTEM$CREATE_GLOSSARY_RELATIONSHIP('<src>','<tgt>','<TYPE>')` or `DRAFT_` + `APPROVE_` |
| Representation | `SYSTEM$CREATE_GLOSSARY_ASSOCIATION('<node>','<assetRefJson>','<ROLE>')` |
| Read | `SYSTEM$GET_GLOSSARY_TERM('<id or domain.name>')`, `SYSTEM$GET_GLOSSARY_TERM_LIST('<domain>')`, `SYSTEM$GET_GLOSSARY_GRAPH('<domain>')`, `SYSTEM$GET_GLOSSARY_DRAFT_GRAPH()` |
| Delete domain | `SYSTEM$DELETE_GLOSSARY_DOMAIN('<domain>')` |

Gotchas:
- The field is `itemKind`, not `termType`.
- Only `METRIC` nodes take `formula`.
- Relationship calls use positional arguments.
- Never call approve-all without arguments.

When you're finished exploring, clean up the demo objects. Agents search every domain the caller can see, so leftover demo terms become noise for other agents in your account.

## Clean Up

Only remove resources created for your run of this guide. If the default names belonged to existing or shared resources, do not delete them. Ontology domains are account-level objects and survive `DROP DATABASE`.

Empty the three demo domains first. A domain can't be deleted while it still contains terms, including drafts. Review the skill's plan to remove representations, relationships (including cross-domain links) and terms before confirming. The prompt below removes the contents but leaves the empty domains for the SQL deletion step.

```
$business-ontology Review and remove the contents of only the Procurement, Finance & Controlling,
and Sales & Distribution domains created for this guide. Include representations, cross-domain
relationships, approved terms and drafts. Show the exact targets and ask for confirmation before
deleting anything. Leave the three empty domains in place for the SQL deletion step.
```

**Expected from CoCo:** the proposal identifies the three domains, their contents and affected links before asking for confirmation. Inspect actual dependencies rather than assuming the initial demo counts still apply.

```text
Deletion targets: contents of Procurement, Finance & Controlling, Sales & Distribution
Review: representations, relationships (including cross-domain links), terms and drafts
Confirmation required before deletion
Expected after approved completion: three empty domains remain
```

After confirming that all three domains are empty, run these statements as a role with `OWNERSHIP` on each domain. If a call reports remaining contents, stop and review those contents before retrying only the failed deletion.

```sql
SELECT SYSTEM$DELETE_GLOSSARY_DOMAIN('Procurement');
SELECT SYSTEM$DELETE_GLOSSARY_DOMAIN('Finance & Controlling');
SELECT SYSTEM$DELETE_GLOSSARY_DOMAIN('Sales & Distribution');
```

**Expected after domain deletion:** each successful response has `error:false` and `state:DELETED`, with the deleted domain's name and ID. All three demo domains are absent from the catalog after refresh. Search may still return stale entries until re-indexing, so immediate search absence is not the deletion postcondition.

Then run the two statements below in a SQL worksheet, only if this guide created these resources. They drop the `BUSINESS_ONTOLOGY` database, including its `RAW` and `SAP` schemas, semantic views and agents, and the `BUSINESS_ONTOLOGY_WH` warehouse.

```sql
DROP DATABASE IF EXISTS BUSINESS_ONTOLOGY;
DROP WAREHOUSE IF EXISTS BUSINESS_ONTOLOGY_WH;
```

**Expected after successful execution:** each statement removes its named resource if present.

| Statement | Expected state |
|---|---|
| `DROP DATABASE IF EXISTS BUSINESS_ONTOLOGY` | Database and its contained schemas, tables, views and agents no longer exist |
| `DROP WAREHOUSE IF EXISTS BUSINESS_ONTOLOGY_WH` | Demo warehouse no longer exists |

If either operation fails, resolve the reported dependency or privilege issue before claiming cleanup is complete. Dropping the database does not substitute for deleting the account-level ontology domains.

Whether you retain the demo for further exploration or complete cleanup, here's a recap of what you built and where to go next.

## Conclusion And Resources

Congratulations! You've built a governed Business Ontology on top of three well-built semantic views, connected it to a Cortex Agent, and learned how to measure what it adds with a fair A/B test. The semantic views compute the numbers; the ontology decides which number is canonical and explains why.

### What You Learned

- What belongs in a semantic view and what belongs in Business Ontology
- How to model canonical metrics alongside their defensible-but-wrong look-alikes
- How terms and policies capture company vocabulary and business rules
- How representations link ontology nodes to the semantic view metrics that implement them
- How to configure a Cortex Agent with `snowscope_search` over the `businessOntology` corpus
- How to evaluate ontology uplift with controls, repeat runs and hedge-aware scoring

To go deeper on any of these, the resources below are a good place to start.

### Related Resources

- [Business Ontology](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-horizon/business-ontology): overview and concepts
- [Access control](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-horizon/business-ontology-access-control): domain-level privileges
- [Agent integration](https://docs.snowflake.com/en/LIMITEDACCESS/snowflake-horizon/business-ontology-agents): `snowscope_search` with the `businessOntology` corpus
- [Horizon Context](https://docs.snowflake.com/en/user-guide/snowflake-horizon/horizon-context): how Business Ontology fits with semantic views and Cortex Sense
