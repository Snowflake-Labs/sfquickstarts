author: Adam Timm
id: hybrid-tables-overview
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/snowflake-feature/hybrid-tables
language: en
summary: A complete guide to the Snowflake Unistore architecture — when to use Hybrid Tables, how they fit with Standard Tables and Snowflake Postgres, and links to every quickstart in the series.
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid tables, unistore, OLTP, OLAP, standard tables, snowflake postgres, architecture, overview, decision guide
skill_level: beginner
-->

# Hybrid Tables — Architecture Overview and Quickstart Library
<!-- ------------------------ -->
## Overview
Duration: 5

Most data platforms force a choice: fast transactional databases for apps, or scalable analytical warehouses for insights. Moving data between them requires ETL pipelines, replication services, and additional vendors — complexity that adds cost, introduces latency, and creates stale data.

**Snowflake Unistore** eliminates that tradeoff. By combining Hybrid Tables, Standard Tables, and Snowflake Postgres in a single platform with a single SQL interface, you get:

- **Sub-millisecond point lookups** alongside petabyte-scale analytics — in the same query
- **Enforced constraints** (PRIMARY KEY, FOREIGN KEY, UNIQUE) for transactional integrity
- **Unified governance** — the same roles, masking policies, and data sharing that govern your analytical tables apply automatically
- **No ETL pipelines** between your operational and analytical layers

This page is your starting point. It explains the architecture, helps you choose the right table type, and links to every quickstart in the series.

### What You Will Learn

- How the Unistore architecture works
- When to use Hybrid Tables vs Standard Tables vs Snowflake Postgres
- Which quickstart is the right starting point for your use case

<!-- ------------------------ -->
## Architecture
Duration: 5

### How Hybrid Tables Work

A Hybrid Table uses a **row store** as its primary storage engine. When you write to a Hybrid Table, data goes directly into the row store, enabling the fast indexed reads and row-level locking that transactional workloads need. Snowflake asynchronously copies data to columnar object storage for large scans.

![Unistore architecture](https://docs.snowflake.com/static/images/unistore-arch.png)

Key properties:

- **Indexes** — PRIMARY KEY is required. Additional secondary indexes support any query predicate. Indexes are updated synchronously on every write.
- **Row-level locking** — concurrent writes from many application threads don't block each other
- **Enforced constraints** — PRIMARY KEY, FOREIGN KEY, and UNIQUE constraints are enforced at write time, not just documented
- **Unified SQL** — join a Hybrid Table to a Standard Table in a single query with no federation overhead

### The Three Table Types

| | Hybrid Table | Standard Table | Snowflake Postgres |
|---|---|---|---|
| **Storage** | Row store (primary) + columnar (secondary) | Columnar micro-partitions | Full Postgres row store |
| **Optimized for** | Point lookups, high-concurrency writes | Bulk scans, aggregations | Full Postgres compatibility |
| **Indexes** | Required PK + optional secondary indexes | Search optimization service | Full Postgres index types |
| **Constraints** | Enforced (PK, FK, UNIQUE) | Not enforced | Enforced |
| **Streams / Dynamic Tables** | Not supported | Supported | N/A |
| **Client connectivity** | Snowflake JDBC/ODBC/Python | Snowflake JDBC/ODBC/Python | Postgres wire protocol (psql, PDO, JDBC) |
| **Best for** | OLTP state inside Snowflake | Analytics, data engineering | Migrating a Postgres app to Snowflake |

<!-- ------------------------ -->
## When to Use Each Table Type
Duration: 5

### Decision Framework

| I need to... | Recommended approach |
|---|---|
| Point lookup by ID from an app (sub-10ms) | **Hybrid Table** |
| Serve precomputed KPIs to a dashboard (sub-second) | **Hybrid Table** |
| Store metadata/state for a workflow with high-concurrency updates | **Hybrid Table** |
| Run GROUP BY aggregates over millions of rows | **Standard Table** |
| Bulk ingest and scan large datasets | **Standard Table** |
| Use Streams or Dynamic Tables for CDC/materialization | **Standard Table** |
| Keep latest operational state AND full analytical history | **Hybrid Table + Standard Table together** |
| Run a PHP/Python/Java app with a Postgres ORM | **Snowflake Postgres** |
| Mirror data from an existing Postgres database into Snowflake | **Snowflake Postgres + Data Mirroring** |
| Convert an existing Standard Table to handle OLTP queries | **Standard-to-Hybrid Migration guide** |

### When NOT to Use Hybrid Tables

Hybrid Tables are not a replacement for Standard Tables. Avoid Hybrid Tables when:

- **Full table scans** are the primary access pattern — GROUP BY, COUNT(*), and aggregate queries over millions of rows perform better on Standard Tables with clustering keys
- **Streams or Dynamic Tables** are required — neither is supported on Hybrid Tables; use a Standard Table copy as the analytics layer
- **Bulk analytical reads** dominate — columnar storage with micro-partition pruning outperforms the row store for this workload
- **Initial bulk load into a non-empty table** is needed — after a Hybrid Table has data, load throughput drops to ~1M rows/min on the standard insert path

> **The most common production pattern** is HT + ST together: Hybrid Table for current operational state (one row per entity, sub-second PK lookup) and Standard Table for full history (append-only, clustered by date, used for analytics and AI).

<!-- ------------------------ -->
## Use Cases
Duration: 5

### IoT and Sensor Telemetry

Devices generate a continuous stream of readings. You need the latest reading per device in under 10ms for a real-time dashboard, plus 90-day history for trend analysis and anomaly detection.

**Architecture:** Hybrid Table stores one row per sensor (latest state). Standard Table stores the full time-series. A Task routes incoming data to both. Cortex AI runs anomaly detection on the Standard Table.

**Start here:** [From Postgres to Native Snowflake](https://quickstarts.snowflake.com/guide/postgres-to-native-snowflake/) or [Streaming & Change Detection Patterns](https://quickstarts.snowflake.com/guide/hybrid-tables-streaming-patterns/)

### E-Commerce and Order Management

An order management system requires sub-second order lookups by order ID, customer ID, and status — and needs to run fraud scoring in real time alongside analytical reporting.

**Architecture:** Hybrid Table stores active orders with PK on `order_id` and secondary indexes on `customer_id` and `status`. Standard Table stores completed order history. Dynamic Tables on the Standard Table power BI dashboards.

**Start here:** [Getting Started with Hybrid Tables](https://quickstarts.snowflake.com/guide/getting-started-with-hybrid-tables/) or [Build a Data Application with Hybrid Tables](https://quickstarts.snowflake.com/guide/build-a-data-application-with-hybrid-tables/)

### Financial Risk and Market Data

A risk platform needs to serve precomputed credit spreads and risk curves to portfolio managers in under 50ms, with hourly refresh from an analytical pipeline.

**Architecture:** Hybrid Table serves as the precomputed KPI serving layer — indexes on `curve_id` and `as_of_date`. A Task snapshots the latest values from a Standard Table every hour.

**Start here:** [Analytics Patterns — Precomputed KPI Serving](https://quickstarts.snowflake.com/guide/hybrid-tables-analytics-patterns/)

### Application Metadata and Workflow State

A data ingestion pipeline has 5,000 parallel workers updating a shared state table. Each worker checks and updates one row per job — requires row-level locking to prevent conflicts.

**Architecture:** Hybrid Table with PK on `job_id` — row-level locking ensures concurrent workers don't conflict. Standard Table stores the completed job audit log.

**Start here:** [Getting Started with Hybrid Tables](https://quickstarts.snowflake.com/guide/getting-started-with-hybrid-tables/)

<!-- ------------------------ -->
## Quickstart Library
Duration: 2

### Getting Started

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [Getting Started with Hybrid Tables](https://quickstarts.snowflake.com/guide/getting-started-with-hybrid-tables/) | First schema, CRUD operations, indexes, constraints | Beginner |
| [Build a Data Application with Hybrid Tables](https://quickstarts.snowflake.com/guide/build-a-data-application-with-hybrid-tables/) | Full OLTP application backed by Hybrid Tables | Intermediate |

### Architecture and Design Patterns

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [Architectural Patterns — Overview](https://quickstarts.snowflake.com/guide/hybrid-tables-architectural-patterns/) | Decision matrix for all HT patterns | Beginner |
| [Analytics Patterns](https://quickstarts.snowflake.com/guide/hybrid-tables-analytics-patterns/) | Task snapshot pipeline, Dynamic Tables, Materialized Views, precomputed KPI serving | Intermediate |
| [Streaming and Change Detection Patterns](https://quickstarts.snowflake.com/guide/hybrid-tables-streaming-patterns/) | HT ingest buffer, watermark CDC, outbound event notifications | Intermediate |
| [Operations Patterns](https://quickstarts.snowflake.com/guide/hybrid-tables-operations-patterns/) | Fan-in aggregation, hot/cold tiering, alert-based monitoring | Intermediate |
| [Serving Layer Patterns](https://quickstarts.snowflake.com/guide/hybrid-tables-serving-layer/) | Precomputed results serving at scale | Intermediate |

### Performance and Optimization

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [Secondary Index Design](https://quickstarts.snowflake.com/guide/hybrid-tables-secondary-index-design/) | Index selection theory, composite index design, anti-patterns | Intermediate |
| [Write Optimization](https://quickstarts.snowflake.com/guide/hybrid-tables-write-optimization/) | Bulk load paths, bound variables, batching patterns | Intermediate |
| [Performance Optimization Primer](https://quickstarts.snowflake.com/guide/hybrid-tables-performance-optimization-primer/) | Warehouse sizing, query diagnostics, latency tuning | Intermediate |
| [JMeter Performance Testing](https://quickstarts.snowflake.com/guide/hybrid-tables-jmeter-performance-testing/) | Load testing framework for Hybrid Table workloads | Advanced |

### Migration and Connectivity

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [Standard to Hybrid Migration](https://quickstarts.snowflake.com/guide/hybrid-tables-standard-to-hybrid-migration/) | Assessment framework, DDL conversion, validation | Intermediate |
| [Application Connectors](https://quickstarts.snowflake.com/guide/hybrid-tables-application-connectors/) | JDBC, Python, Node.js, and Kafka connection patterns | Intermediate |

### Monitoring and Operations

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [Monitoring and Observability](https://quickstarts.snowflake.com/guide/hybrid-tables-monitoring-observability/) | AGGREGATE_QUERY_HISTORY dashboards, alerting, Streamlit, Datadog, Grafana | Intermediate |

### Snowflake Postgres + Hybrid Tables

| Guide | What you build | Skill level |
|-------|---------------|-------------|
| [From Postgres to Native Snowflake](https://quickstarts.snowflake.com/guide/postgres-to-native-snowflake/) | Data mirroring from Snowflake Postgres into HT + Standard Table architecture | Intermediate |

<!-- ------------------------ -->
## User Guide Reference
Duration: 1

The following Snowflake documentation pages provide the authoritative reference for Hybrid Tables:

- [Hybrid Tables overview](https://docs.snowflake.com/en/user-guide/tables-hybrid) — Architecture, features, and when to use
- [Create hybrid tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-create) — DDL reference and constraint syntax
- [Best practices for hybrid tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices) — Index design, warehouse sizing, client patterns
- [Hybrid table limitations](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations) — Unsupported features and regional availability
- [Evaluate cost for hybrid tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-cost) — Storage and compute cost model
- [AGGREGATE_QUERY_HISTORY view](https://docs.snowflake.com/sql-reference/account-usage/aggregate_query_history) — Dedicated telemetry view for monitoring HT workloads

> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)
