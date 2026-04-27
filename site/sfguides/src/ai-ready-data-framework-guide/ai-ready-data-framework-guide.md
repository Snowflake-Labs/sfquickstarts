author: Jacob Prall
id: ai-ready-data-framework-guide
language: en
summary: Use the AI-Ready Data Framework to assess, score, and remediate your Snowflake data for AI workloads like RAG, agents, feature serving, and training.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/ai-ready-data/issues
fork repo link: https://github.com/Snowflake-Labs/ai-ready-data

# AI-Ready Data Framework: Assess and Remediate Your Data for AI

## Overview

The **AI-Ready Data Framework** is an open standard that defines what "AI-ready" actually means. It provides six factors, 62 measurable requirements, and five workload profiles that you can use to evaluate your data, pipelines, and platforms against the demands of AI workloads.

The framework ships as an installable **agent skill** that any coding agent can load and execute. Point it at your Snowflake data and say "assess my data for RAG readiness" — the agent scans your schemas, scores every requirement 0–1, and guides you through remediation.

In this guide, you will walk through two end-to-end demos:

1. **Scan + Agents** — Scan a multi-schema data estate, identify the lowest-readiness schema, deep-assess it for agentic AI, and remediate failures.
2. **RAG Readiness** — Assess a single schema against the RAG profile, drill into diagnostics, and fix what fails.

By the end, you will understand how the framework evaluates data across six dimensions and how to use the skill to move from assessment to action.

### Prerequisites

- A Snowflake account with access to `SNOWFLAKE_LEARNING_DB` (or ability to create it)
- Familiarity with running SQL in Snowflake
- Basic understanding of AI/ML data concepts (RAG, embeddings, feature stores)

### What You'll Learn

- The six factors of AI-ready data and why they matter for AI workloads
- How the framework organizes requirements into workload profiles
- How to scan a data estate for comparative readiness prioritization
- How to run a deep assessment and interpret scored results
- How to use agent-guided remediation to fix failing requirements

### What You'll Need

- [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/index) (`snow`) installed and configured
- [Cortex Code CLI](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code) installed
- Node.js / npx available
- A Snowflake role with `CREATE SCHEMA` privileges on `SNOWFLAKE_LEARNING_DB` (ACCOUNTADMIN works for demos)
- `IMPORTED PRIVILEGES` on the SNOWFLAKE database (for governance checks)

### What You'll Build

- A scored AI-readiness report across your data estate
- A deep assessment of a specific schema against a workload profile
- Remediated data assets with improved readiness scores

## The Six Factors of AI-Ready Data

The framework evaluates data across six factors. Every assessment is organized into six stages — one per factor — producing a scored report that tells you exactly where your data stands and where it falls short.

### Factor 0: Clean

Clean data is consistently accurate, complete, valid, and free of errors that would compromise downstream consumption. Clean is Factor 0 because nothing else matters without it — context, consumability, freshness, lineage, and compliance all assume the underlying data is trustworthy.

Example requirements: `data_completeness`, `uniqueness`, `referential_integrity`, `encoding_validity`

### Factor 1: Contextual

Meaning is explicit and colocated with the data. No external lookup, tribal knowledge, or human context is required to take action. AI systems have none of the institutional context that human analysts accumulate — if the meaning isn't machine-readable and colocated, the model is operating blind.

Example requirements: `semantic_documentation`, `relationship_declaration`, `entity_identifier_declaration`

### Factor 2: Consumable

Data is served in the right format and at the right latencies for AI workloads. Traditional analytics tolerates seconds or minutes; AI workloads require millisecond vector retrieval, sub-100ms feature serving, and pre-chunked documents sized for context windows.

Example requirements: `embedding_coverage`, `vector_index_coverage`, `serving_latency_compliance`, `access_optimization`

### Factor 3: Current

Data reflects the present state, with freshness enforced by infrastructure rather than assumed by convention. Models have no concept of time — every input is treated as ground truth. When a model receives stale data, it produces a confident, wrong answer.

Example requirements: `change_detection`, `data_freshness`, `incremental_update_coverage`

### Factor 4: Correlated

Data is traceable from source to every decision it informs. When something goes wrong — a bad prediction, a hallucinated answer — you need to trace backward through transformations, feature engineering, and inference to find the root cause.

Example requirements: `data_provenance`, `lineage_completeness`, `agent_attribution`

### Factor 5: Compliant

Data is governed with explicit ownership, enforced access boundaries, and AI-specific safeguards. AI introduces novel governance surface area: PII leaks through embeddings, bias encoded in training distributions, and model outputs that fall under regulatory scrutiny.

Example requirements: `classification`, `column_masking`, `access_audit_coverage`, `row_access_policy`

## Profiles, Requirements, and Scoring

### Requirements

Each factor is backed by measurable **requirements** — platform-agnostic criteria that define what must be true of your data. The framework includes 62 requirements, each with:

- A unique key (e.g. `data_completeness`)
- A factor assignment (Clean, Contextual, etc.)
- A scope (schema, table, or column)
- Platform-specific implementations containing a **check** (scoring SQL), **diagnostic** (detail drill-down), and **fix** (remediation guidance)

All checks return a normalized score between 0 and 1, where **1.0 is perfect**. A requirement passes when `score >= threshold`.

### Profiles

A **profile** is a curated subset of requirements with thresholds tuned for a specific workload. The framework ships five built-in profiles:

| Profile             | Requirements | Best For                                                                |
| ------------------- | ------------ | ----------------------------------------------------------------------- |
| **scan**            | 8            | Estate-level sweep for portfolio analysis and prioritization            |
| **rag**             | 27           | Retrieval-augmented generation: chunking, embeddings, vector search     |
| **feature-serving** | 39           | Online feature stores: low-latency lookups, materialized features       |
| **training**        | 50           | Fine-tuning and ML training: reproducibility, bias testing, licensing   |
| **agents**          | 37           | Text-to-SQL and agentic tool use: strict schema docs, strong audit trail|

### Overrides

Before running, you can adjust any profile on the fly:

- **`skip <requirement>`** — exclude a check entirely
- **`set <requirement> <threshold>`** — override a threshold
- **`add <requirement> <threshold>`** — include a check not in the base profile

For repeatability, save overrides as a custom profile:

```yaml
name: my-rag-profile
extends: rag
overrides:
  skip:
    - embedding_coverage
  set:
    chunk_readiness: { min: 0.70 }
  add:
    row_access_policy: { min: 0.50 }
```

## Install the Skill

Install the AI-Ready Data skill into Cortex Code CLI:

```bash
npx skills add Snowflake-Labs/ai-ready-data -a cortex
```

Verify the installation:

```
cortex
/skill list
```

You should see `ai-ready-data` in the list.

If `SNOWFLAKE_LEARNING_DB` does not exist in your account, create it:

```sql
CREATE DATABASE IF NOT EXISTS SNOWFLAKE_LEARNING_DB;
```

## Demo 1: Scan + Agents Assessment

This demo provisions a multi-schema environment with intentionally different levels of data readiness, then walks through the full workflow: estate-level scan, drill into the worst schema, deep agents assessment, and remediation.

### Provision the environment

Run the setup script outside of Cortex Code:

```bash
./demos/run.sh setup scan-agents
# Or with a specific Snowflake connection:
./demos/run.sh setup scan-agents -c <your-connection>
```

This creates multiple schemas in `SNOWFLAKE_LEARNING_DB` — some well-governed, some partially documented, some completely raw. The final query prints a summary of what was created.

### Scan the data estate

Start Cortex Code:

```bash
cortex -c <your-connection> -w /path/to/ai-ready-data
```

Then trigger the scan:

```
Scan my data estate for AI readiness
```

When prompted, choose **Snowflake** as the platform and **SNOWFLAKE_LEARNING_DB** as the database.

The agent runs the lightweight scan profile (8 requirements across 4 factors) across all schemas and presents a portfolio view — a comparative ranking by readiness score. You should see a clear tier structure:

| Tier   | What You'll See                                              |
| ------ | ------------------------------------------------------------ |
| High   | A well-documented, governed, optimized schema                |
| Medium | Partially documented, limited governance                     |
| Low    | No documentation, no governance, no optimization             |

The scan is fast and designed for breadth — it immediately shows which parts of the estate are AI-ready and which need attention.

### Drill into the worst schema

After the scan, pick the lowest-scoring schema for a deep assessment:

```
Assess that schema in depth
```

When asked for the assessment profile, choose **agents**:

```
Agents readiness
```

The agents profile is the broadest and most demanding — 37 requirements across all six factors with strict thresholds. The low-readiness schema should fail broadly:

| Stage (Factor) | Expected | Why                                                              |
| --------------- | -------- | ---------------------------------------------------------------- |
| Clean           | FAIL     | Nulls, duplicates, encoding errors, bad types, orphan FKs        |
| Contextual      | FAIL     | No column comments, no primary keys, no constraints              |
| Consumable      | FAIL     | No clustering, no search optimization                            |
| Current         | FAIL     | No change tracking, no streams                                   |
| Correlated      | Partial  | Query history may show some agent attribution                    |
| Compliant       | FAIL     | PII columns without masking, no tags, no row access policies     |

### Explore diagnostics

Before remediating, drill into a specific failure:

```
Tell me more about data_completeness
```

The agent runs diagnostic SQL and shows which columns have nulls, how many, and in which tables. This demonstrates the two-phase workflow: understand the problem, then fix it.

### Remediate

Start the remediation loop:

```
Remediate the Clean stage
```

The agent will:

1. Show which requirements are failing
2. Load fix SQL for each one
3. Present a remediation plan with the exact SQL it will run
4. Wait for your approval before executing
5. Re-run the check SQL to show before/after scores

Remediation is agent-assisted, not agent-autonomous — the agent proposes, you approve. Every fix shows the exact SQL before execution, and before/after verification closes the loop.

### (Optional) Re-scan the estate

After remediating a few stages, go back to the estate level:

```
Scan the estate again
```

The previously-low schema should now score higher, closing the loop on the full workflow: scan, prioritize, assess, fix, verify.

> aside positive
> Governance checks that use `snowflake.account_usage` views (tags, masking policies) have ~2 hour latency for newly created objects. If you create tags or policies during remediation, those checks may still show FAIL until the views catch up.

### Tear down

```bash
./demos/run.sh teardown scan-agents
# Or with a connection:
./demos/run.sh teardown scan-agents -c <your-connection>
```

## Demo 2: RAG Readiness Assessment

This demo provisions a single schema with 8 tables and intentional data quality and governance gaps, then walks through a focused RAG readiness assessment.

### Provision the environment

```bash
./demos/run.sh setup rag
# Or with a specific connection:
./demos/run.sh setup rag -c <your-connection>
```

This creates `SNOWFLAKE_LEARNING_DB.AIRDF_DEMO` with 8 tables:

| Table               | Rows   | Description                                           |
| ------------------- | ------ | ----------------------------------------------------- |
| CUSTOMERS           | 20     | Core entity with PII (email, phone, address)          |
| PRODUCTS            | 15     | Product catalog with pricing                          |
| ORDERS              | 25     | Transactions — includes duplicates and orphans        |
| ORDER_ITEMS         | 26     | Line items linking orders to products                 |
| PRODUCT_REVIEWS     | 10     | Reviews with JSON payloads (some invalid)             |
| SUPPLIER_CONTRACTS  | 7      | Contracts with date ranges                            |
| INVENTORY_SNAPSHOTS | 15,000 | Large generated table — no clustering key             |
| MARKETING_EVENTS    | 12     | Behavioral events with JSON payloads                  |

### Run the assessment

Start Cortex Code:

```bash
cortex -c <your-connection> -w /path/to/ai-ready-data
```

Trigger the assessment:

```
Assess SNOWFLAKE_LEARNING_DB.AIRDF_DEMO for RAG readiness
```

The agent will:

1. Load the RAG profile (6 stages, one per factor)
2. Discover the 8 tables in `AIRDF_DEMO`
3. Ask you to confirm scope and offer override options
4. Run check SQL for each requirement, stage by stage
5. Present a scored report

The demo data is designed to produce failures across every stage:

| Stage (Factor) | Expected | Why                                                             |
| --------------- | -------- | --------------------------------------------------------------- |
| Clean           | FAIL     | Nulls, duplicates, encoding errors, bad types, orphan FKs       |
| Contextual      | FAIL     | No column comments, no primary keys, no constraints             |
| Consumable      | FAIL     | No embeddings, no vector indexes, no chunks, no clustering      |
| Current         | FAIL     | No change tracking, no streams                                  |
| Correlated      | Partial  | Query history may show some agent attribution                   |
| Compliant       | FAIL     | PII columns without masking, no tags, no row access policies    |

### Explore diagnostics

Pick a failing requirement and ask for details:

```
Tell me more about data_completeness
```

The agent runs diagnostic SQL and shows which columns have nulls, how many, and in which tables.

### Remediate

```
Remediate the Clean stage
```

The agent loads fix SQL for each failing requirement, presents a remediation plan, waits for approval, executes, and re-runs checks to show improvement.

Good requirements to remediate live:

| Requirement                      | What the fix does                              |
| -------------------------------- | ---------------------------------------------- |
| `data_completeness`              | Fill nulls with defaults or delete incomplete rows |
| `uniqueness`                     | Deduplicate the ORDERS table                   |
| `encoding_validity`              | Replace encoding errors (U+FFFD, null bytes)   |
| `entity_identifier_declaration`  | Add primary key constraints                    |
| `semantic_documentation`         | Add column and table comments                  |
| `change_detection`               | Enable change tracking on tables               |
| `access_optimization`            | Add clustering key to INVENTORY_SNAPSHOTS      |

> aside positive
> Skip `embedding_coverage` and `vector_index_coverage` during remediation unless you have Cortex embedding functions available. These checks require `SNOWFLAKE.CORTEX` access. This is a good opportunity to demonstrate the `skip` override.

### Tear down

```bash
./demos/run.sh teardown rag
# Or with a connection:
./demos/run.sh teardown rag -c <your-connection>
```

## Conclusion and Resources

You have now walked through the full AI-Ready Data Framework workflow: scanning a data estate for comparative prioritization, deep-assessing specific schemas against workload profiles, drilling into diagnostics, and remediating failures with agent-guided fixes.

The framework is designed to be extended. You can add new requirements, create custom profiles, and implement platform-specific checks beyond Snowflake. Every requirement follows the same structure: a platform-agnostic definition in the manifest, and platform-specific check, diagnostic, and fix files.

### What You Learned

- The six factors of AI-ready data: Clean, Contextual, Consumable, Current, Correlated, Compliant
- How requirements are organized into workload profiles (scan, RAG, agents, feature-serving, training)
- How to scan a data estate and prioritize schemas by readiness
- How to run deep assessments and interpret scored results
- How to use diagnostics to understand failures before remediating
- How to remediate failures with agent-guided, approval-gated fixes

### Related Resources

- [AI-Ready Data Framework on GitHub](https://github.com/Snowflake-Labs/ai-ready-data)
- [Cortex Code CLI Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code)
- [Snowflake CLI Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-cli-v2/index)
