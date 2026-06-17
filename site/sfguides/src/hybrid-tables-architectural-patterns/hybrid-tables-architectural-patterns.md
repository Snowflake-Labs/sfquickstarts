author: Adam Timm
id: hybrid-tables-architectural-patterns
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering
language: en
summary: Overview of architectural patterns for Hybrid Table workloads — analytics pipelines, streaming ingest, change detection, data management, and operational monitoring.
environments: web
status: Hidden
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

<!--
keywords: hybrid table, architectural patterns, analytics, streaming, CDC, change detection, monitoring, fan-in, hot cold, OLTP, Unistore, Task, MERGE, Dynamic Table, Materialized View, Kafka, alert
skill_level: intermediate
prerequisite_guides: getting-started-with-hybrid-tables
-->

# Architectural Patterns for Hybrid Table Workloads — Overview
<!-- ------------------------ -->
## Overview

Hybrid Tables are optimized for low-latency point lookups and transactional writes. Several features commonly used in analytics and data engineering pipelines are not available directly on Hybrid Tables:

- **Streams** (change tracking)
- **Dynamic Tables** (cannot read from a HT)
- **Materialized Views** (cannot be created on a HT)
- **Result cache** (does not apply to HT queries)
- **Clustering keys** (HT uses indexes instead)

This means you need an architectural layer between the Hybrid Table and your analytics consumers, change-tracking systems, and operational tooling. This series of guides covers the patterns that address each limitation.

### The Three Guides

This series is split into three focused quickstarts. Use the decision matrix below to find the pattern you need, then navigate to the appropriate guide.

| Guide | Patterns Covered |
|-------|-----------------|
| [Analytics Patterns](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/) | Task snapshot, Dynamic Tables, Materialized Views, Precomputed KPI serving |
| [Streaming and Change Detection](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) | HT ingest buffer + real-time rollup, Watermark CDC, Outbound event notifications |
| [Data Management and Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/) | Fan-in aggregation, Hot/cold tiering, Alert-based monitoring |

<!-- ------------------------ -->
## Decision Matrix

Use this matrix to find the right pattern for your workload.

| Need | Pattern | Guide | Freshness | Complexity |
|------|---------|-------|-----------|------------|
| BI dashboards on HT data | Task + MERGE to Standard Table | [Analytics](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/) | Minutes | Low |
| Derived aggregations, complex rollups | Dynamic Tables on ST copy | [Analytics](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/) | TARGET_LAG | Low |
| Simple precomputed rollups on one table | Materialized Views on ST copy | [Analytics](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/) | Automatic | Low |
| Fast dashboard KPI lookups | Precompute aggregations to HT | [Analytics](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/) | Minutes | Medium |
| High-freq streaming ingest + real-time rollup | HT ingest buffer + 30s Task + Data Share | [Streaming](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) | 30 seconds | Medium |
| Incremental change detection (no Streams) | Timestamp watermark polling | [Streaming](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) | Minutes | Medium |
| Publish events to Kafka/SNS/webhooks | Task + Notification Integration | [Streaming](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/) | ~1 minute | Medium |
| Cross-domain analytics (multiple HTs) | Fan-in to consolidated Standard Table | [Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/) | Minutes | Medium |
| Manage HT storage growth | Hot/cold data tiering | [Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/) | Daily | Low |
| Monitor HT latency and throttling | AGGREGATE_QUERY_HISTORY + Alerts | [Operations](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/) | Hours (view latency) | Medium |

<!-- ------------------------ -->
> aside positive
> **Need help with your Hybrid Table architecture?** Book a 30-minute session with our specialist team to discuss your use case, review your schema design, or troubleshoot performance: [Schedule a session](https://calendar.app.google/cGfVnKFe7xbeDqDo8)

## Related Resources

- [Analytics Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-analytics-patterns/)
- [Streaming and Change Detection Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-streaming-patterns/)
- [Data Management and Operations Patterns for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-operations-patterns/)
- [Hybrid Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-hybrid)
- [Hybrid Table Limitations](https://docs.snowflake.com/en/user-guide/tables-hybrid-limitations)
- [Best Practices for Hybrid Tables](https://docs.snowflake.com/en/user-guide/tables-hybrid-best-practices)
- [Converting Standard Tables to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-standard-to-hybrid-migration/)
- [Secondary Index Design for Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-secondary-index-design/)
- [Connecting Applications to Hybrid Tables](https://www.snowflake.com/en/developers/guides/hybrid-tables-application-connectors/)
