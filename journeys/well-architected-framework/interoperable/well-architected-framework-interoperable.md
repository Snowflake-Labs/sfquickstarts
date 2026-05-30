sidebar: true
sidebar_json: well-architected-framework
author: Well Architected Framework Team
id: well-architected-framework-interoperable
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: The Open and Interoperable Lens provides guidance for multi-engine data access via Apache Iceberg, external catalog integration, cross-organizational data sharing, and data portability across the Snowflake ecosystem.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-code-skills/tree/main/skills/well-architected-framework-assessment



# Open and Interoperable Lens

## Overview

| Field | Description |
|-------|-------------|
| Scope | Multi-engine data access via Apache Iceberg, external catalog integration, cross-organizational data sharing, CDC and data integration patterns, and data portability across the Snowflake ecosystem |
| Target Audience | Data architects, platform engineers, data engineers, and technology leaders who design and operate data platforms spanning multiple engines, tools, and organizational boundaries |
| Prerequisites | Familiarity with the five Snowflake Well-Architected Framework pillars. Core WAF pillar guidance should be adopted before applying this lens. |
| Out of Scope | Foundational Snowflake architecture (covered by WAF pillars), single-engine Snowflake deployments without external integration needs, application-layer integration patterns |

### Why This Lens Exists

Current state (Q1 2026). Open table formats and catalog protocols have matured substantially, but cross-platform governance, policy enforcement, and business logic portability remain uneven across the industry. Customers operating heterogeneous data estates will encounter real friction in these areas today. Snowflake is actively working to close these gaps and shares the open, interoperable future-state vision — this lens calls out current limitations explicitly so architecture decisions are grounded in present capabilities rather than projected ones.

Organizations increasingly operate multi-engine data ecosystems where Spark, Trino, Flink, DuckDB, and other engines need governed access to the same data. Apache Iceberg has emerged as the open table format standard enabling this, and Snowflake sits at the center—as both a catalog provider (through Horizon Catalog's Polaris APIs) and a catalog consumer (through Catalog-Linked Databases and catalog integrations). Snowflake created Apache Polaris and contributed it to the Apache Software Foundation, where it graduated to a Top-Level Project in February 2026.

Snowflake's interoperability is bidirectional by design. Through the Iceberg REST catalog protocol, Snowflake serves as both a catalog provider (external engines connect to Polaris APIs in Horizon Catalog to read and write Snowflake-managed Iceberg Tables) and a catalog consumer (Snowflake connects to any external Iceberg REST-enabled catalog to read and write Iceberg Tables managed elsewhere). This bidirectional openness is a defining characteristic: rather than requiring all data to be imported into a proprietary format, Snowflake participates as a peer in the open Iceberg ecosystem.

Interoperability extends beyond data formats to semantic definitions. Snowflake co-founded the Open Semantic Interchange (OSI) initiative—a vendor-neutral standard (spec v0.1 finalized January 2026, Apache 2.0 license) for exchanging semantic models (metrics, dimensions, relationships) across BI, AI, and analytics platforms. With 50+ member organizations including Salesforce, Databricks, dbt Labs, Oracle, and Collibra, OSI ensures that business logic defined in one tool is portable to others without manual re-creation.

Snowflake's Iceberg support continues to advance: Apache Iceberg v3 support adds new data types (geography, geometry, nanosecond, variant), default values, deletion vectors, and row lineage. These are distinct features with different purposes: deletion vectors enable merge-on-read write optimization, improving write throughput by deferring physical deletes. Row lineage is a separate capability providing standardized CDC semantics (INSERT, UPDATE, DELETE, MERGE) readable by both Snowflake and external engines — including externally-managed Iceberg tables. Iceberg v3 is in Public Preview in Snowflake as of March 2026, and ecosystem-wide adoption remains limited — most production tables are on v2. See the Feature Status table for Snowflake's current support status.

The core WAF pillars address universal Snowflake architecture concerns. This lens provides the additional guidance that arises when Snowflake participates in a broader data ecosystem—catalog strategy, table format selection, cross-engine governance, semantic model portability, CDC patterns (Streams + Tasks, Dynamic Tables, Dynamic Iceberg Tables), Delta Lake interop, cross-organizational sharing, and integration surface continuity. Apply this lens alongside the pillars, not instead of them.

### Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | Bring compute to data, not data to compute | Let engines query data in place rather than copying it to each consumer. Snowflake enables this through Horizon Catalog, Catalog-Linked Databases, and Iceberg Tables on customer-managed storage. |
| 2 | Embrace open standards; work toward unified governance | Use Apache Iceberg, the Iceberg REST catalog protocol, and Snowflake Horizon to provide open-format flexibility. In OSS engine deployments, Horizon can serve as a single governance control plane. In vendor co-existence deployments, governance fragmentation is a current operational reality — design policies to be duplicated across catalogs in the interim while working toward convergence on cross-vendor enforcement standards. |
| 3 | Share data securely without copying | Prefer Secure Data Sharing and Data Clean Rooms over file extracts to eliminate governance gaps, staleness, and storage duplication. |
| 4 | Preserve optionality through open standards | Snowflake's support for ANSI SQL, Apache Iceberg, PostgreSQL wire protocol (Snowflake Postgres), and standard APIs (JDBC, ODBC, REST, Polaris) ensures that skills and workloads remain portable. Evaluate portability alongside capability—not instead of it. |
| 5 | Design for resilience across the integration surface | Extend continuity planning beyond databases to the full integration layer—catalog endpoints, external engine connections, Shares, Clean Rooms, and pipelines—using Failover Groups and Client Redirect. |
| 6 | Enable semantic interoperability across tools | Adopt the Open Semantic Interchange (OSI) standard so that metrics, dimensions, and business logic definitions are portable across BI, AI, and analytics platforms—eliminating redundant semantic definitions and ensuring consistent meaning across the ecosystem. |

## Pillar Guidance

### Security & Governance

#### Overview

Security and governance for interoperable architectures extends the Security & Governance pillar into territory the base pillar does not cover: governing data that is accessed by external engines through Horizon Catalog's Polaris APIs, consumed from external catalogs via Catalog-Linked Databases, shared across organizations through Secure Data Sharing and Data Clean Rooms, and described by portable semantic models through OSI. Each of these access paths introduces governance surface area—authentication, authorization, audit, and policy enforcement—that must remain consistent regardless of which engine or tool initiates the query. The unique challenge is preventing governance fragmentation: when multiple engines can reach the same data, the catalog must be the single control plane, not a collection of per-engine policies.

#### Principles

- Horizon Catalog is the governance control plane—route all external engine access through it rather than granting direct storage access.
- Governance consistency is the goal, not the current state. For OSS engines (Spark, Trino, Flink) connecting through Horizon Catalog, Snowflake governance applies uniformly. In vendor co-existence scenarios (Databricks, AWS, Microsoft Fabric): each vendor's catalog federates via service accounts, requiring governance policies to be duplicated across catalogs today. Design for the unified future state while accounting for this operational reality in the interim.

#### Recommendations

| # | Recommendation | Description | Priority |
|---|---------------|-------------|----------|
| 1 | Serve Iceberg tables to external engines via Horizon Catalog | External engines connect to Horizon's Polaris APIs via standard Iceberg REST catalog configuration—no Snowflake-side DDL required. Reads are GA; writes are in preview (see Feature Status). RBAC controls table and namespace access; row-access policies and masking are not yet enforced for external engine queries via the Polaris API (see Feature Status). | High |
| 2 | Consume external Iceberg tables via Catalog-Linked Databases | Catalog-Linked Databases auto-sync metadata from external Iceberg REST catalogs into Snowflake. Supported catalogs include Unity Catalog, AWS Glue REST (CATALOG_API_TYPE = AWS_GLUE with SigV4 authentication), self-hosted Apache Polaris, and any Iceberg REST-compliant catalog. Snowflake governance (RBAC, row-access policies, masking) applies to linked tables. | High |
| 3 | Use vended credentials for storage access | Configure vended credentials so the catalog issues temporary cloud storage credentials (AWS session tokens, Azure SAS tokens, GCS OAuth tokens) to external engines. This makes the catalog the single point of access control for both metadata and data. | High |
| 4 | Enable privacy-preserving collaboration with Data Clean Rooms | Use Data Clean Rooms for cross-organizational collaboration where regulatory or competitive concerns prevent raw data sharing. Clean Rooms support Iceberg-backed datasets and work cross-cloud. Data Clean Rooms require both parties to be Snowflake customers. | Medium |
| 5 | Automate policy enforcement with Horizon | Use classification, tag-based masking, and Access History to scale governance. These policies apply to all Snowflake-governed access paths. For external engines querying through Polaris APIs, row-access and masking policies are not yet enforced—see Feature Status. | Medium |
| 6 | Audit for ungoverned access paths | Identify external engines reading raw cloud storage files, manual file exports, or direct S3/ADLS access that bypasses catalog governance. Route them through Horizon or CLD. | Medium |
| 7 | Govern semantic definitions through OSI | Adopt the Open Semantic Interchange standard to ensure metrics, dimensions, and business logic are defined once and governed centrally—then portable across BI, AI, and analytics tools without re-creation or drift. | Medium |

#### Anti-Patterns

- Granting direct S3/ADLS/GCS access to external engines instead of routing through Horizon Catalog
- Using file extracts for cross-organizational collaboration instead of Secure Data Sharing or Clean Rooms
- Manually creating individual Iceberg tables for each external catalog table when CLD would auto-sync
- Treating vendor co-existence governance (Databricks, AWS Glue, Microsoft Fabric) as equivalent to OSS engine governance—each vendor catalog federates via a service account, requiring governance policy duplication until the industry converges on a cross-vendor enforcement standard

#### Assessment Questions

- Are external engines accessing Iceberg data through the Polaris API in Horizon Catalog, or through ungoverned paths?
- Is inbound external catalog data consumed through Catalog-Linked Databases with Snowflake governance applied?
- Are vended credentials the default storage access model for external engines?
- Are there cross-organizational collaboration needs that Data Clean Rooms could address?
- Are semantic definitions (metrics, dimensions, business logic) governed centrally and exchanged via OSI-compatible formats?

### Operational Excellence

#### Overview

Operational excellence for interoperable architectures extends the Operational Excellence pillar with concerns specific to multi-engine and multi-catalog environments: establishing repeatable CDC pipelines using native Snowflake mechanisms (Streams + Tasks, Dynamic Tables, Dynamic Iceberg Tables), automating metadata synchronization from external catalogs through Catalog-Linked Databases, reading upstream Delta Lake tables via Delta Direct, maintaining semantic model portability through OSI-compatible definitions, and curating governed data products that are discoverable across the ecosystem.

#### Principles

- Prefer native Snowflake CDC mechanisms (Streams + Tasks, Dynamic Tables) and managed integration (Openflow, Snowpipe) over custom pipelines.
- Curate data as products—each dataset should have a designated owner, documented SLAs, and self-service discoverability through Horizon.
- For version-controlled deployment of interop infrastructure (catalog integrations, external volumes, Iceberg tables), evaluate DCM Projects for declarative, Git-backed change management across environments (see Feature Status).

#### Recommendations

| # | Recommendation | Description | Priority |
|---|---------------|-------------|----------|
| 1 | Use Streams + Tasks for native CDC | Streams capture row-level changes with exactly-once semantics. Tasks execute incremental MERGE logic on schedule or when SYSTEM$STREAM_HAS_DATA() returns true. Iceberg table support: Snowflake-managed Iceberg (v2 or v3) supports full change data streams; externally-managed Iceberg v2 supports append-only streams only; externally-managed Iceberg v3 supports full CDC streams via row lineage. | High |
| 2 | Use Dynamic Tables and Dynamic Iceberg Tables for declarative pipelines | Dynamic Tables express transformation results declaratively—Snowflake manages incremental refresh to meet the target lag. For multi-engine interoperability, use Dynamic Iceberg Tables to write transformation output in Iceberg format to external storage, making pipeline results directly accessible to external engines through Horizon. | High |
| 3 | Use Catalog-Linked Databases for metadata sync | CLD automatically discovers and syncs tables from external Iceberg REST catalogs. Use for environments where Databricks, Spark, or Flink write Iceberg data that Snowflake needs to query. | High |
| 4 | Evaluate Openflow for unified data integration | Openflow (built on Apache NiFi) provides pre-built connectors for CDC from OLTP databases, streaming from Kafka/Kinesis, SaaS integration, and file-based sources. GA for both BYOC and Snowflake Deployments (SPCS). | Medium |
| 5 | Use Delta Direct for Delta Lake interop | Read Delta Lake tables directly in Snowflake without conversion using TABLE_FORMAT = DELTA in the catalog integration. Auto-refresh keeps tables current as upstream processes write new Delta commits. | Medium |
| 6 | Convert externally-managed Iceberg tables to Snowflake-managed | Use ALTER ICEBERG TABLE ... CONVERT TO MANAGED to migrate tables from external catalogs to Snowflake-managed, gaining write support, automatic compaction, and full lifecycle management. Validate carefully and coordinate with upstream producers before cutting over. | Medium |
| 7 | Curate Trusted Data Products | Identify authoritative datasets with clear ownership, freshness SLAs, and business context documented in Horizon. Enable self-service discovery through Universal Search. Evaluate Marketplace for third-party data before building acquisition pipelines. | Medium |

#### Anti-Patterns

- Building custom CDC pipelines when Streams + Tasks or Dynamic Tables would suffice
- Manually creating individual Iceberg tables for each external catalog table instead of using CLD
- Running self-managed NiFi when Openflow provides a managed equivalent
- Extracting Delta Lake data to staging files instead of using Delta Direct
- Relying on tribal knowledge for data discovery instead of Horizon and Universal Search

#### Assessment Questions

- What percentage of data integration uses custom ETL vs. native Snowflake capabilities (Streams, Tasks, Dynamic Tables, Openflow)?
- Are external catalog tables consumed through CLD or through manual individual table creation?
- Are Delta Lake tables from upstream engines accessed via Delta Direct?
- Are data products documented with ownership, SLAs, and business context in Horizon?

### Reliability

#### Overview

Reliability for interoperable architectures extends the Reliability pillar beyond database availability to the full integration surface. When external engines depend on Horizon Catalog's Polaris API endpoint, cross-organizational collaborators rely on Shares and Clean Rooms, and ingestion flows through Openflow or Snowpipe, each becomes a continuity concern the base pillar does not specifically address. Snowflake extends its managed DR capabilities to open-format data: Iceberg tables—including Dynamic Iceberg Tables—replicate through Failover Groups alongside standard tables, eliminating the need for custom replication engineering.

#### Principles

- During a disruption, the full integration surface must continue to function: databases, catalog endpoints, Shares, Clean Rooms, and pipelines.
- Include integration surface components in Failover Groups so they fail over together.

#### Recommendations

| # | Recommendation | Description | Priority |
|---|---------------|-------------|----------|
| 1 | Inventory the full integration surface | Document every dependency: databases (including Iceberg Tables), Polaris API endpoints, Shares, Clean Room configurations, Openflow pipelines, Snowpipe configurations. Assign RPO/RTO to each and tier by criticality. | High |
| 2 | Include Shares and Roles in Failover Groups | Configure Failover Groups with OBJECT_TYPES = DATABASES, SHARES, ROLES so consumers, Clean Room collaborators, and access policies fail over alongside data. | High |
| 3 | Configure Iceberg table replication | Snowflake-managed Iceberg tables (including Dynamic Iceberg Tables) replicate through Failover Groups alongside standard tables. Pre-configure external volumes with storage locations in the target region. Enable ENABLE_ICEBERG_MANAGED_TABLE_REPLICATION on both source and target accounts. Requires Business Critical Edition or higher. | High |
| 4 | Configure catalog endpoint failover | Use Client Redirect and Connection objects so external engines pointing at Horizon's Polaris API resolve to the active account during failover. Configure external engines to use Connection URLs rather than direct account endpoints. | High |
| 5 | Test recovery across all interop components | Conduct planned failover exercises that verify external engine reconnection to the secondary Polaris API endpoint, Iceberg table accessibility on the replica, Share and Clean Room accessibility, and pipeline resumption. | Medium |
| 6 | Plan pipeline continuity | Openflow runs on SPCS (regional). For critical ingestion, deploy redundant instances in the secondary region. Configure Snowpipe notification re-routing for cloud storage sources. Coordinate Snowflake Postgres cross-region replication with broader Failover Group timing. | Medium |

#### Integration Surface Continuity

| Component | Continuity Mechanism | Key Consideration |
|-----------|---------------------|-------------------|
| Snowflake databases (incl. Iceberg Tables) | Database replication + Failover Groups | Iceberg Tables replicate alongside standard tables within the same database |
| Polaris API / Horizon Catalog endpoint | Client Redirect + Connection objects | External engines must use Connection URLs, not direct account endpoints |
| Shares and Clean Room configurations | Include SHARES in Failover Groups | Shares fail over with the group; consumers must reconnect to secondary account |
| Openflow pipelines | Regional — deploy redundant instances in secondary region | Openflow runs on SPCS, which is regional |
| Snowflake Postgres instances | Cross-region replication built into Postgres | Coordinate with database failover timing |
| Snowpipe / Snowpipe Streaming | Configure notifications and SDK connections to secondary | Cloud storage notifications may need re-routing |

#### Anti-Patterns

- Planning DR only for Snowflake databases while ignoring catalog endpoints, Shares, and pipelines
- Assuming external engines will automatically reconnect to secondary Polaris API endpoints without Client Redirect
- Excluding Shares and Clean Room configurations from Failover Groups
- Treating all integration components with equal protection rather than tiering by criticality
- Assuming Iceberg tables replicate automatically without pre-configuring external volume storage locations in the target region

#### Assessment Questions

- Does the continuity plan cover the full integration surface, or only Snowflake databases?
- Can external engines connected through Polaris APIs automatically redirect during failover?
- Are Shares and Clean Room configurations included in Failover Groups?
- When was the last failover test that validated external engine reconnection and Clean Room availability?
- Are Iceberg tables included in Failover Groups with external volumes pre-configured for the target region?

### Performance

#### Overview

Performance for interoperable architectures extends the Performance pillar with considerations unique to multi-engine data access. Table format selection (native vs. Iceberg vs. Dynamic Iceberg) directly affects query optimization, caching behavior, and cross-engine read performance. Credential flows—how external engines authenticate and receive vended storage tokens through Horizon—introduce latency that compounds at scale if metadata caching and TTLs are not tuned. Delta Direct's ability to read Delta Lake tables as Iceberg avoids the performance penalty of legacy external tables.

#### Principles

- Table format selection should be driven by workload requirements: native tables for Snowflake-only workloads, Iceberg for multi-engine access.
- Credential and metadata caching patterns have material performance impact at scale.

#### Recommendations

| # | Recommendation | Description | Priority |
|---|---------------|-------------|----------|
| 1 | Use native tables for Snowflake-only workloads | Native tables offer Snowflake's most mature performance optimizations — micro-partition pruning, automatic clustering, result caching, and Search Optimization Service. Many of these extend to Iceberg tables too, but native tables remain the best choice when no external engine needs the data. | High |
| 2 | Use Iceberg Tables for multi-engine access | Iceberg Tables enable external engines to query governed data through Horizon. Use Snowflake-managed Iceberg (with external volume) for Snowflake query optimization with open-format portability — today this incurs ~5% TPC-DS overhead versus native tables, with parity as the goal. For pipelines requiring open-format output, use Dynamic Iceberg Tables. | High |
| 3 | Tune serialization and file size for cross-engine reads | Set STORAGE_SERIALIZATION_POLICY = COMPATIBLE on Iceberg tables that external engines will query—this writes Parquet files optimized for Spark, Trino, and Flink. Set TARGET_FILE_SIZE to 64MB or 128MB for tables read by external engines. These are the two most impactful interoperability tuning parameters. | High |
| 4 | Use Snowflake Postgres with pg_lake for transactional-analytical bridging | Snowflake Postgres runs PostgreSQL with full wire-protocol compatibility. The pg_lake extension queries Iceberg Tables from Postgres, bridging transactional and analytical workloads. | Medium |
| 5 | Optimize credential TTLs and metadata caching | Vended credential TTLs should balance security and renewal overhead. Monitor Polaris API call volumes—Horizon API requests are billed as Cloud Services. Optimize engine metadata caching to reduce catalog round-trips. | Medium |
| 6 | Right-size integration compute | Separate integration warehouses (Dynamic Table refreshes, Openflow-triggered loads) from interactive query warehouses. Configure auto-suspend for integration warehouses. Tier refresh frequency to business SLA requirements rather than defaulting to the shortest lag available. | Medium |

#### Anti-Patterns

- Defaulting all tables to Iceberg format without a concrete multi-engine requirement
- Using legacy external tables or COPY INTO for Delta Lake data when Delta Direct is available
- Granting external engines independent storage IAM roles instead of using vended credentials
- Running integration and interactive workloads on the same warehouse
- Leaving STORAGE_SERIALIZATION_POLICY at OPTIMIZED and TARGET_FILE_SIZE at AUTO for tables that external engines query

#### Assessment Questions

- Are Iceberg Tables used only where multi-engine access is a concrete requirement, with native tables elsewhere?
- Are Iceberg tables intended for multi-engine access configured with COMPATIBLE serialization policy and appropriate target file sizes?
- Have performance-critical workloads been benchmarked on both native and Iceberg tables?
- Are Polaris API call volumes monitored? Are external engines caching metadata appropriately?

### Cost Optimization

#### Overview

Cost optimization for interoperable architectures extends the Cost Optimization pillar with cost dimensions specific to multi-engine and multi-catalog environments. Horizon Catalog API calls are billed as Cloud Services, data movement between engines creates storage and transfer costs, and the choice between Snowflake-managed services and self-managed infrastructure affects total cost of ownership across four dimensions (direct, hidden, opportunity, exit).

#### Principles

- Account for four cost dimensions when evaluating integration components: direct costs, hidden costs (maintenance, patching, incident response), opportunity costs (engineering diverted from business value), and exit costs.
- Minimize data movement—sharing in place is almost always cheaper than copying.

#### Recommendations

| # | Recommendation | Description | Priority |
|---|---------------|-------------|----------|
| 1 | Apply a four-dimension TCO framework | For each integration component (catalog, ETL, orchestration, transactional DB), evaluate direct costs, hidden costs, opportunity costs, and exit costs. Include DR management burden. Use this framework when comparing Snowflake-managed alternatives against self-managed options. | High |
| 2 | Prefer zero-copy sharing over extracts | Secure Data Sharing eliminates storage cost for consumers. Polaris APIs enable multi-engine access to data in place. File extracts are the most expensive approach: storage duplication at every destination plus transfer charges plus reconciliation engineering. | High |
| 3 | Monitor Horizon API costs | Polaris API calls are billed at 0.5 credits per million calls (billing starts mid-2026). Consider tuning engine metadata caching to reduce catalog round-trips. | Medium |
| 4 | Evaluate managed consolidation on TCO merits | Assess whether Openflow, Dynamic Tables, Snowflake Postgres, or Snowpark Container Services could replace self-managed components. Evaluate each on total cost—consolidation should reduce TCO, not just vendor count. | Medium |
| 5 | Use cross-region replication selectively | Database replication adds storage and synchronization costs. Cross-cloud transfers incur additional data transfer charges. Reserve cross-region and cross-cloud replication for workloads where RPO/RTO requirements justify the expense. | Low |

#### Consolidation Opportunities

| Self-Managed Component | Snowflake Alternative | Cost Benefit |
|------------------------|----------------------|--------------|
| Custom ETL scripts, self-managed NiFi | Openflow | Eliminates ETL server infrastructure; reduces engineering maintenance burden |
| Standalone PostgreSQL instances | Snowflake Postgres | Eliminates DB server management; pg_lake bridges transactional and Iceberg/analytical data |
| Custom orchestration (Airflow DAGs, cron) | Dynamic Tables + Tasks | Declarative pipelines eliminate orchestration infrastructure and operational toil |
| Separate Kubernetes / ECS clusters | Snowpark Container Services | Containers run within Snowflake governance without separate cluster management |
| Self-managed Hive Metastore | Horizon Catalog (Polaris APIs) | Unified catalog with zero additional infrastructure |
| Separate BI / application hosting | Streamlit in Snowflake + Native Apps | Applications run within Snowflake, eliminating app server costs |
| Separate ML training infrastructure | Snowflake ML + Cortex AI | Model training and inference within governed environment |

#### Anti-Patterns

- Evaluating cost using only direct costs (license, compute) while ignoring hidden and opportunity costs
- Creating data copies for each consuming engine instead of sharing through Polaris APIs or Secure Data Sharing
- Maintaining self-managed infrastructure solely to avoid vendor dependency without accounting for the operational cost of that independence
- Applying cross-region replication uniformly rather than tiering by criticality

#### Assessment Questions

- Has the organization applied a four-dimension TCO framework (direct, hidden, opportunity, exit) to integration components?
- What percentage of data sharing uses Secure Data Sharing vs. file extracts?
- What is the engineering cost of operating self-managed integration components vs. Snowflake-managed alternatives?
- Are Polaris API call volumes monitored and optimized?

## Key Decisions & Tradeoffs

| Decision | Option A | Option B | Choose A When | Choose B When |
|----------|----------|----------|---------------|---------------|
| Table format | Native tables | Iceberg Tables | Workloads run exclusively in Snowflake | Multi-engine access or open-format portability required |
| Catalog approach | Horizon Catalog (Polaris APIs) | Open Catalog | Default recommendation — integrated governance, single endpoint, zero extra infrastructure | Organization requires fully decoupled, vendor-neutral catalog independent of Snowflake compute |
| Catalog direction | Outbound (Snowflake as provider) | Inbound (Snowflake as consumer) | Snowflake manages the Iceberg data and external engines query through Horizon | Data is managed in an external Iceberg REST catalog (Unity Catalog, Glue, self-hosted Polaris) |
| Storage access | Vended credentials | External volume direct | Simplest multi-engine path — catalog vends temporary storage tokens, centralizing access control | Fine-grained IAM control or engine-specific storage policies required |
| Data integration | Openflow | Snowpipe / Connectors | Broad source coverage, CDC from OLTP, streaming from Kafka/Kinesis, or diverse source mix | Simple cloud storage loading or purpose-built SaaS connectors are sufficient |
| Transactional workloads | Snowflake Postgres | Hybrid Tables (Unistore) | Migrating existing Postgres applications; need PostgreSQL wire-protocol compatibility | Building new OLTP + OLAP workloads natively in Snowflake without wire-protocol requirement |
| Cross-org collaboration | Secure Data Sharing | Data Clean Rooms | Consumers need direct, governed read access to shared data | Privacy regulations or competitive concerns prohibit raw data exposure |
| CDC pattern | Dynamic Tables (declarative) | Streams + Tasks (imperative) | Transformation logic is expressible as SQL; freshness SLAs are sufficient | Complex scheduling, multi-step dependencies, or non-SQL processing logic required |
| Openflow deployment | Snowflake Deployment (fully managed) | BYOC (customer VPC) | Prefer fully managed with zero infrastructure overhead | Data residency requirements or network security controls require customer VPC deployment |
| Resilience level | Built-in multi-AZ | Cross-region / cross-cloud replication | Workloads tolerate regional failure risk; RPO/RTO objectives are relaxed | RPO/RTO requirements demand protection beyond a single region or cloud provider |
| Cross-engine governance | OSS engines via Horizon | Vendor co-existence (Databricks, AWS, Fabric) | For OSS engines, Horizon can serve as a single governance control plane | For vendor co-existence, each platform federates via service accounts — governance policies must currently be duplicated across catalogs |

## Maturity Model

| Level | Name | Description |
|-------|------|-------------|
| 1 | Foundational | Ad-hoc integration. Data shared via file extracts. No catalog strategy for external engines. CDC done through custom scripts or manual loads. Governance is manual and inconsistent across access paths. DR covers databases only. |
| 2 | Managed | Horizon Catalog governs outbound multi-engine access. CLD or catalog integrations handle inbound external data. Streams + Tasks or Dynamic Tables provide native CDC. Dynamic Iceberg Tables used for pipelines requiring open-format output. Delta Direct used for upstream Delta tables. Trusted Data Products identified with ownership and SLAs. Failover Groups cover the full integration surface including Shares and Roles. Semantic definitions beginning to adopt OSI-compatible formats. |
| 3 | Optimized | All external engine access governed through Horizon with vended credentials. CLD auto-syncs external catalogs with namespace filtering. Dynamic Iceberg Tables power cross-engine pipeline output. Governance automated through classification and tag-based masking. Semantic models managed centrally via OSI and portable across BI/AI tools. DR tested regularly across the full integration surface including external engine reconnection. TCO reviewed periodically across all four dimensions. New Snowflake capabilities evaluated quarterly for consolidation opportunities. |

## Assessment Checklist

- External engine access governed through Horizon Catalog with vended credentials (Security & Governance)
- Inbound external catalog data consumed through Catalog-Linked Databases (Security & Governance)
- Ungoverned access paths identified and remediated (Security & Governance)
- Semantic definitions governed centrally and exchanged via OSI-compatible formats (Security & Governance)
- CDC implemented using Streams + Tasks, Dynamic Tables, or Dynamic Iceberg Tables (Operational Excellence)
- Delta Lake tables from upstream engines accessed via Delta Direct (Operational Excellence)
- Trusted Data Products documented with ownership, SLAs, and business context (Operational Excellence)
- Data shared via Secure Data Sharing or Clean Rooms, not file extracts (Operational Excellence)
- Failover Groups include DATABASES, SHARES, and ROLES with Iceberg tables and external volumes configured (Reliability)
- Client Redirect configured for catalog endpoint failover (Reliability)
- Failover tested across full integration surface including external engine reconnection (Reliability)
- Table format matches workload: native for Snowflake-only, Iceberg for multi-engine (Performance)
- Multi-engine Iceberg tables configured with COMPATIBLE serialization policy and appropriate target file sizes (Performance)
- Integration and interactive workloads on separate warehouses (Performance)
- Four-dimension TCO framework applied to all integration components (Cost Optimization)
- Polaris API call volumes monitored and engine metadata caching optimized (Cost Optimization)

## Feature Status

The following features referenced in this lens are not yet generally available. Status is as of the lens publication date (March 2026). Check Snowflake Release Notes for current status.

| Feature | Status | As Of |
|---------|--------|-------|
| External engine writes to Iceberg tables via Horizon | Public Preview | Mar 2026 |
| Apache Iceberg v3 support (new types, deletion vectors, row lineage) | Public Preview | Mar 2026 |
| Iceberg table replication via Failover Groups | Public Preview | Mar 2026 |
| DCM Projects (declarative change management) | Public Preview | Mar 2026 |
| Full change streams on externally-managed Iceberg v2 tables | Not supported (append-only only) | Apr 2026 |
| Time Travel / UNDROP for externally-managed Iceberg tables | Not supported | Apr 2026 |
| Row-access policies and masking for external engine queries | Not yet supported | Mar 2026 |

## References & Resources

| Resource | Type | Link |
|----------|------|------|
| Snowflake Well-Architected Framework | Documentation | snowflake.com |
| Horizon Catalog (external engine access) | Documentation | docs.snowflake.com |
| Catalog-Linked Databases | Documentation | docs.snowflake.com |
| Apache Iceberg Tables | Documentation | docs.snowflake.com |
| Delta Direct (Iceberg on Delta files) | Documentation | docs.snowflake.com |
| Apache Polaris | Project | polaris.apache.org |
| Vended Credentials | Documentation | docs.snowflake.com |
| Streams | Documentation | docs.snowflake.com |
| Dynamic Tables | Documentation | docs.snowflake.com |
| Openflow | Documentation | docs.snowflake.com |
| Secure Data Sharing | Documentation | docs.snowflake.com |
| Data Clean Rooms | Documentation | docs.snowflake.com |
| Snowflake Postgres | Documentation | docs.snowflake.com |
| Snowflake Open Catalog | Documentation | docs.snowflake.com |
| Dynamic Iceberg Tables | Documentation | docs.snowflake.com |
| Iceberg Best Practices | Documentation | docs.snowflake.com |
| Iceberg v3 Support | Documentation | docs.snowflake.com |
| Open Semantic Interchange (OSI) | Standard | open-semantic-interchange.org |
| Iceberg Table Replication | Documentation | docs.snowflake.com |
| Failover Groups | Documentation | docs.snowflake.com |
