author: Well Architected Framework Team
id: well-architected-framework-performance
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: Optimizing performance on Snowflake is crucial for efficient data analysis. 
environments: web
status: Published 




# Performance 

## Overview

Optimizing performance on Snowflake is crucial for efficient data
analysis. This guidance, for data architects, developers, and
administrators, outlines best practices for designing, implementing, and
maintaining data workloads.

Applying these recommendations streamlines operations, enhances user
experience, and improves business value through increased revenue and
reduced costs. For instance, faster query execution translates to
quicker insights and greater adoption.

Performance tuning often balances performance and cost, with
improvements frequently benefiting both. Snowflake's autoscaling
capabilities, for example, ensure consistent performance by dynamically
allocating resources as concurrency increases, while also providing cost
efficiency by scaling down during lower demand.

## Principles and recommendations
### Principles

### Establish and validate performance objectives

> Define clear, measurable, and achievable performance targets within
> technical and budgetary limits before application design. Consider key
> workload characteristics.

### Optimize data architecture and access

> Design efficient data models and access patterns to minimize data
> scanned. Leverage appropriate data types, clustering, indexing, and
> performance features.

### Architect for scalability and workload partitioning

> Utilize Snowflake’s elastic warehouse features and application design
> to strategically partition workloads, optimizing resource utilization,
> concurrency, and latency.

### Implement continuous performance monitoring and optimization

> Establish comprehensive monitoring and logging to identify performance
> bottlenecks. Proactively optimize the system over time, adapting to
> evolving requirements.

### Recommendations

The following key recommendations are covered within the principles of
Performance:

- **Leveraging Elasticity  **
  Dynamically adjust resources based on workload. Utilize horizontal
  scaling (multi-cluster warehouses) and vertical sizing to match query
  complexity. Employ manual scaling for predictable peaks and
  auto-scaling for real-time fluctuations.

- **Peak Load Planning  **
  Proactively plan for high-demand periods. Use manual scaling for
  predictable surges; enable auto-scaling and predictive scaling for
  less predictable demand.

- **Continuous Performance Improvement  **
  Monitor key performance indicators like latency, throughput, and
  utilization. Foster continuous tuning through training, feedback, and
  metric review.

- **Test-First Design  **
  Integrate performance testing into the design phase. Define KPIs,
  establish baselines, and simulate workloads early. Use load,
  scalability, and stress testing throughout development to prevent
  bottlenecks.

- **Effective Data Shaping  **
  Leverage Snowflake micro-partition clustering. Define clustering keys
  for frequently filtered/joined columns to enable efficient pruning and
  reduce I/O. Regularly monitor clustering depth.

- **Well-Designed SQL  **
  Write efficient queries by avoiding SELECT \*, specifying needed
  columns, and using efficient joins. Use query profiling tools to
  refine performance and minimize resource consumption.

- **Optimizing Warehouses  **
  Reduce queues and spillage, scale appropriately, and use query
  acceleration. Right-size warehouses and manage concurrency to reduce
  contention and optimize resource use.

- **Optimizing Storage  **
  Use automatic clustering, Search Optimization Service, and
  materialized views strategically. Match the technique to your
  workload.

- **High-Level Practices  **
  To optimize query performance, select fewer columns, leverage query
  pruning with clustered columns, and use pre-aggregated tables.
  Simplify SQL by reducing unnecessary sorts, preferring window
  functions, and avoiding OR conditions in joins. Minimize view
  complexity, maximize cache usage, scale warehouses, and tune cluster
  scaling policies for balanced performance and cost.

 

## Set performance objectives
### Establish and validate performance objectives

### Overview

Snowflake optimizes performance through its Performance by Design
methodology, integrating performance as a core architectural feature.
This approach links business objectives with efficient resource
management, leveraging key principles, careful configurations, and
Snowflake's elasticity for scalability and cost-efficiency.

### Desired outcome

By implementing these best practices, you can achieve a highly
responsive and cost-optimized Snowflake environment. Expect predictable
query performance that consistently meets Service Level Objectives
(SLOs), eliminate costly architectural debt, and effectively manage
operational expenses by aligning compute resources with workload
demands. Ultimately, businesses can claim a well-architected data
platform that supports their needs without unnecessary expenditure.

### Recommendations

Performance is a core, cost-driven feature. Prioritize "as fast as
necessary" over "as fast as possible" to prevent over-provisioning.
Define performance (latency, throughput, concurrency) as a negotiable
business metric requiring cost-benefit analysis, as it directly impacts
Snowflake's operational expenses through credit consumption.
Understanding cloud architecture's continuous financial implications is
crucial. Performance planning from the start is essential to avoid
inefficiencies, poor user experience, and costly re-engineering.

### Performance by Design

Achieve a high-performing Snowflake environment by implementing a
deliberate strategy before coding. The Performance by Design methodology
ensures performance is a core architectural feature from a project's
start, aligning business objectives, user experience, and financial
governance. Proactive decisions establish an efficiently scalable
foundation, preventing expensive architectural debt.

**Performance as a feature**

Prior to solution design, it is imperative to internalize a key
principle of cloud computing: every performance requirement entails a
direct and quantifiable cost. The paradigm shift from "maximize speed"
to "achieve necessary speed" represents the initial stride toward a
meticulously architected system.

**Performance as a negotiable business metric**

Performance, latency, and concurrency are more than fixed technical
specs; they're business requirements that need to be defined and
justified like any other product feature. If someone asks for a
"five-second query response time," that should invite a discussion about
value and cost, not be treated as an absolute must-have. Different
workloads have different performance needs, and a one-size-fits-all
approach leads to overspending and wasted resources.

**The Cloud Paradigm: From capital to operational expense**

In a traditional on-premises setup, performance often hinges on
significant upfront spending for hardware. Once purchased, the cost to
run each query is very low. The cloud, however, uses a completely
different financial model. With Snowflake, performance is an ongoing
operational cost. Every active virtual warehouse uses credits, meaning
that your architectural and query design decisions have immediate and
continuous financial consequences.

**Avoiding architectural debt: The cost of unplanned implementation**

Snowflake's inherent simplicity can lead to solutions implemented
without adequate upfront planning, fostering architectural debt. This
debt manifests as excessive credit consumption from inefficient queries,
suboptimal user experience due to unpredictable performance, and
expensive re-engineering projects. To avoid these issues, establish
clear project plans and formalize performance metrics from the outset,
ensuring optimal system health and cost efficiency.

### The Core Process: The Design Document

To translate principle into practice, any significant data project
should begin with a design document. This is not just a technical
document, but a formal agreement that forces critical trade-off
conversations to happen at the project's inception.

#### Assembling the Stakeholders: A Cross-Functional Responsibility

Creating a design document is a collaborative effort. It ensures that
business goals are accurately translated into technical and financial
realities. The key participants include:

- Business Stakeholders: To define the goals and the value of the
  desired outcomes.

- Product Managers: To translate business needs into specific features
  and user stories.

- Engineering Leads: To evaluate technical feasibility and design the
  architecture.

- FinOps/Finance: To provide budget oversight and model the cost
  implications of different service levels.

**Service Level Objectives (SLOs)**

Service Level Objectives (SLOs) are essential for optimizing
performance. They establish measurable and acceptable performance
benchmarks for a system or service. By continuously monitoring and
evaluating against these concrete targets, organizations can ensure
their services consistently fulfill both user expectations and business
needs.

Effective SLOs should be:

- **Specific:** Avoid vague goals. Define precise targets, such as "95%
  of interactive dashboard queries under 10 seconds," to allow for
  accurate measurement.

- **Measurable:** Establish clear metrics and the tools for data
  collection and analysis. For example, to measure "nightly ETL of 1TB
  in under 60 minutes," systems must track data volume and processing
  time.

- **Achievable:** Set realistic and attainable targets given current
  resources and technology, to avoid excessive costs without business
  value.

- **Relevant:** Align SLOs with business needs and end-user
  expectations, focusing on critical user experience or business
  processes.

- **Time-bound:** Many SLOs benefit from a defined timeframe, aiding in
  performance evaluation over a specific period.

Defining and monitoring SLOs helps organizations proactively identify
and address performance bottlenecks, ensuring consistent service
quality, enhanced user satisfaction, and better business outcomes.
Regular review and adjustment of SLOs are crucial to adapt to evolving
business needs and technological advancements.

### Defining the four pillars of workload requirements

Define a workload’s performance profile using these four key pillars:

- **Workload Categorization**: Not all work is the same. The first step
  is to classify each workload based on its usage pattern and
  performance characteristics. Common categories include:

  - **Interactive:** User-facing queries, typically from dashboards
    (e.g., Tableau, Power BI, Looker), where low latency and high
    concurrency are critical for a good user experience.

  - **Ad-Hoc/Exploratory:** Queries from data scientists or analysts
    that are often complex, unpredictable, and long-running. Latency is
    less critical than preventing impact on other workloads.

  - **Batch:** Scheduled, large-scale data processing jobs like ELT/ETL
    pipelines. Throughput and predictability are the primary goals.

  - **Programmatic:** Automated queries from applications or services
    that often have highly predictable patterns and strict performance
    requirements.

- **Workload Performance Targets**: For each category, establish
  specific, measurable, and realistic performance targets. Avoid overly
  general goals, such as "all queries must return in 10 seconds," in
  favor of concrete objectives.

  - **Latency Example:** "95% of all interactive dashboard filter
    queries must complete in under 10 seconds."

  - **Throughput Example:** "The nightly ETL process must load and
    transform 1 TB of data in under 60 minutes."

- **Data Freshness Tiers:** The demand for real-time data must be
  balanced against its often higher cost. Define explicit data freshness
  tiers to align business value with architectural complexity and credit
  consumption.

  - **Near Real-Time (Seconds to Minutes):** Highest cost; requires a
    streaming architecture (e.g., Snowpipe, Dynamic Tables). Justified
    for use cases like fraud detection, real-time ad selection, etc.

  - **Hourly:** Medium cost; suitable for operational reporting.

  - **Daily:** Lowest cost; standard for most strategic business
    intelligence and analytics.

- **Concurrency and Scale Projections:** Plan for the expected load and
  future growth to inform warehouse sizing and scaling strategies.
  Examples of key questions to answer include:

  - How many users are expected to use this system simultaneously during
    peak hours?

  - What is the anticipated data volume growth over the next 6-12
    months?

  - Are there predictable spikes in usage (e.g., end-of-quarter
    reporting, Black Friday)?

**Integrating performance into the development lifecycle**

Validate agreements from the design phase throughout development.
Proactive performance testing, a "shift-left" methodology, mitigates
project risks and prevents launch-time performance issues.

Do not await large-scale data for performance analysis. Early on, review
query profiles and EXPLAIN plans to identify potential problems like
exploding joins (join with a missing or incorrect condition, causing a
massive, unintended multiplication of rows) or full table scans, which
indicate ineffective query pruning.

### Mandatory pre-release benchmarking

Before deploying a new workload to production, benchmark it as a formal
quality gate. This involves running it on a production-sized data clone
in a staging environment to validate that it meets the Workload
Requirements Agreement's SLOs.

For critical workloads, integrate performance benchmarks into the CI/CD
pipeline. This practice automatically detects performance regressions
from code changes, allowing for immediate fixes rather than user
discovery in production.

### Common design shortcomings to avoid

Failing to implement a Performance by Design methodology often leads to
one of the following common and costly mistakes.

**Applying a single, aggressive SLA universally**

Applying a single, aggressive performance target (e.g., "all queries
under 5 seconds") to every workload leads to inefficiencies. This forces
ad-hoc analysis, outlier queries, and interactive dashboards to share
the same expensive configuration, increasing credit usage unnecessarily.

**Disregarding the cost of data freshness**

An unexamined data latency requirement, such as "data must be 1 minute
fresh," can significantly increase credit consumption. Often, data
freshness exceeds actual needs without fully discussing associated
costs. This can lead to paying a high price for a streaming architecture
that may not deliver proportional business value.

**Performance discrepancies at deployment**

Deferring performance testing until a project's end results in
unacceptably slow or expensive processes discovered just before launch.
This often leads to emergency fixes, missed deadlines, and the
brute-force solution of running workloads on oversized warehouses. This
obscures underlying design flaws at a significant ongoing cost.

## Build for performance
### Foundational First Steps

### Performance in the cloud

In an on-premises environment, performance is often a sunk cost. The
cloud, particularly Snowflake, links performance and cost optimization.
Every query, active virtual warehouse, and background service consumes
credits, making performance an ongoing operational consideration.

This guide focuses on initial steps to build a performant, scalable, and
cost-effective environment. Make conscious performance and cost
decisions before significant development to establish a solid
architectural foundation, preventing costly re-engineering.

### Establish and validate performance objectives

Effective performance objectives are specific, measurable, and
realistic. They serve as the benchmark against which you can measure the
success of your architecture. When defining your targets, you should
focus on key metrics that directly impact your workloads.

Consider the following core performance characteristics:

- **Latency**: Ensure queries complete quickly for interactive
  applications. For example, 95% of dashboard filter queries should
  complete in under 10 seconds.

- **Throughput**: Measure the work your system accomplishes over time,
  vital for batch processing and data ingestion. For instance, the
  nightly ETL process must load and transform 1 TB in under 60 minutes.

- **Concurrency**: Determine how many simultaneous queries your system
  supports without performance issues, crucial for applications with
  numerous users. The primary BI warehouse should support 200 concurrent
  users during peak hours without query queuing.

These objectives must be aligned with specific workload characteristics
and balanced against the real-world business and budget constraints of
your project. They are established for a specific workload and rarely
apply across all workloads.

### Tactical Day One configurations & concepts

Once you have a strategic plan, you can implement tactical
configurations that set a baseline for good performance and cost
management.

#### Proactive guardrails

Optimizing warehouse performance involves strategic configuration. These
settings are your first line of defense against runaway queries and
unexpected costs.

- An effective **Warehouse auto-suspend strategy** balances credit
  savings and performance. Suspended warehouses consume no credits but
  lose their data cache, leading to slower subsequent queries. Tailor
  the strategy to your workload:

- **ELT/ETL warehouses:** Use an aggressive suspend time (e.g., 1-2
  minutes). These jobs are typically bursty, making it inefficient to
  keep the warehouse running after completion.

- **BI/dashboard warehouses:** Employ a more lenient suspend time (e.g.,
  10-20 minutes). The performance benefit of a warm cache for
  latency-sensitive users often outweighs the cost of brief idle
  periods.

- **Setting statement timeouts** is crucial to prevent long-running,
  costly queries. The default timeout (48 hours) is often too long.
  Configure the
  [<u>STATEMENT_TIMEOUT_IN_SECONDS</u>](https://docs.snowflake.com/en/sql-reference/parameters#statement-timeout-in-seconds)
  parameter on your warehouses to a sensible maximum, such as 15 minutes
  for a dashboard warehouse or 8 hours for a complex ETL warehouse.

<!-- -->

- **Configuring Resource Monitors** provides a safety net for budget
  control. These monitors track warehouse credit consumption and can
  trigger actions like notifications or automatic suspension when
  thresholds are exceeded. It's best practice to set up monitors at both
  the account and individual warehouse levels. Refer to [<u>Working with
  resource monitors in the Snowflake
  documentation</u>](https://docs.snowflake.com/en/user-guide/resource-monitors)
  for more information.

<!-- -->

- **Budgets** offer a flexible way to monitor and control spending
  across your Snowflake account. They track credit usage for
  customizable objects, including warehouses and serverless features.
  Budgets can alert stakeholders when projected costs approach or exceed
  predefined limits, enabling a proactive approach to managing overall
  spend. See [<u>Monitor credit usage with budgets in the Snowflake
  documentation</u>](https://docs.snowflake.com/en/user-guide/budgets)
  for details.

#### Fundamental architectural concepts

- **Scale up for complexity:** Increase warehouse size (e.g., from
  Medium to Large) to improve a single, large, or complex query's
  performance. A larger warehouse provides more resources—memory, CPU,
  and temporary storage—to complete the work faster.

- **Scale out for concurrency:** For a higher number of concurrent users
  and queries, increase the number of clusters in a multi-cluster
  warehouse. This doesn't make individual queries faster but allows more
  to run simultaneously without performance bottlenecks.

#### Using the right tool for the job (targeted acceleration)

Snowflake offers several powerful features that accelerate performance
for specific use cases. Using them correctly is key.

- **Search Optimization Service** This service accelerates point-lookup
  queries on large tables. It creates a lightweight search access path,
  allowing Snowflake to pinpoint data in micro-partitions and bypass
  full table scans. It's most effective on high-cardinality columns like
  UUIDs or email addresses. See [<u>The Expat Guide to Search
  Optimization
  Service</u>](https://medium.com/snowflake/search-optimization-c99b2117cb2e).

- **Materialized Views (MVs)** MVs are for massive-scale problems, not
  general tuning. Consider them only when data reduction from the base
  table is substantial, such as for pre-calculating large dashboard
  aggregations or optimizing multi-billion row tables. MVs incur
  continuous storage and compute costs for maintenance, which must be
  justified by performance gains. See [<u>Working with Materialized
  Views in the Snowflake
  documentation</u>](https://docs.snowflake.com/en/user-guide/views-materialized).

- **Query Acceleration Service (QAS)** QAS acts as a safety net for your
  warehouse, handling outlier queries with unexpectedly large scans. It
  offloads parts of this work to shared Snowflake compute resources,
  preventing large queries from monopolizing your warehouse and
  impacting other users. QAS is not a primary tuning tool, but it
  improves warehouse stability. See [<u>Using the Query Acceleration
  Service (QAS) in the Snowflake
  documentation</u>](https://docs.snowflake.com/en/user-guide/query-acceleration-service).

#### Modern data transformation

Dynamic Tables offer declarative data transformation. When designing
them, simplicity is key. Performance depends on the query and a hidden
Change Data Capture (CDC) process checking source tables. Complex
queries with many joins create intricate CDC dependency graphs, slowing
refresh times. Chaining simpler Dynamic Tables is often more performant
and manageable than a single, complex one. For more information, see
[<u>Dynamic tables in the Snowflake
documentation</u>](https://docs.snowflake.com/en/user-guide/dynamic-tables-about).

#### Conclusion

A high-performing Snowflake environment starts on day one. By moving
from strategic planning to tactical configurations, you establish a
robust framework. These initial steps—defining objectives, configuring
guardrails, and using the right tools—are essential for building a
performant, scalable, and cost-effective architecture in the Snowflake
Data Cloud.

### Leveraging elasticity for performance

#### The power of elastic compute

Snowflake’s architecture separates storage and compute, enabling
independent and dynamic scaling. This ensures the precise processing
power needed for your workloads. Leveraging this elasticity is crucial
for a well-architected Snowflake environment.

The goal is optimal price-for-performance, avoiding both
under-provisioning (slow queries, missed SLOs) and over-provisioning
(unnecessary credit consumption).

This guide details three primary elasticity mechanisms. Understanding
how and when to use each helps build a responsive, efficient, and
cost-effective data platform. The three mechanisms are:

- **Vertical Scaling:** Adjusting the size of a warehouse (for example
  from Medium to Large) to handle more complex queries and larger data
  volumes.

- **Horizontal Scaling:** Adjusting the number of clusters in a
  warehouse to manage workload concurrency.

- **Query Acceleration Service:** Augmenting a warehouse with serverless
  resources to handle unpredictable, outlier queries.

#### Isolate your workloads

Before applying any scaling strategy, you must first isolate your
workloads. A common performance anti-pattern is to direct all users and
processes to a single, large virtual warehouse. This approach makes it
impossible to apply the correct scaling strategy, as the warehouse is
forced to handle workloads with conflicting performance profiles.

A fundamental best practice is to create separate, dedicated warehouses
for distinct workloads. For example, your architecture should include
different warehouses for:

- **ETL/ELT:** These workloads are often characterized by complex,
  long-running transformations that benefit from larger warehouses but
  may not require high concurrency.

- **BI Dashboards:** These workloads typically involve many concurrent,
  short-running, repetitive queries. They demand low latency and benefit
  from horizontal scaling.

- **Data Science:** These workloads can be highly variable, often
  involving exploratory analysis and long-running model training that
  require specific sizing and timeouts.

- **Ad-Hoc Analysis:** These queries from data analysts are often
  unpredictable in both complexity and concurrency.

By isolating workloads, you can observe the specific performance profile
of each and apply the most appropriate and cost-effective scaling
strategy described below.

#### Vertical scaling: sizing up for complexity and scale

Vertical scaling, or resizing, modifies a warehouse's compute power.
Snowflake warehouses, offered in "t-shirt sizes" (X-Small, Small,
Medium, etc.), double compute resources—CPU, memory, and local disk
cache—with each size increase.

Consider scaling up when a single query or complex operations demand
more resources than the current warehouse size can efficiently provide.
A larger warehouse can accelerate complex queries by parallelizing work
across more nodes. However, increasing warehouse size is not a universal
solution for slow queries; diagnose the performance bottleneck first.

### When to scale up: A diagnostic checklist

Before increasing a warehouse’s size, use the following checklist to
validate that it is the appropriate solution.

#### Symptom 1: Disk spilling

Spilling occurs when a query’s intermediate results exceed a warehouse’s
available memory and must be written to disk. This is a primary
indicator of an undersized warehouse. You can identify spilling in the
Query Profile. There are two types of spilling, each with a different
level of severity:

- **Local Spilling:** This indicates a **warning**. Data is written from
  memory to the warehouse’s local disk, impacting query performance.
  Evaluate local spilling within your workload's SLA and the
  spill-to-RAM ratio. For instance, if 1 TB of data is processed in
  memory with 10 GB spilled, the impact might be minor. However, if 20
  GB is processed with 10 GB spilled, the warehouse is likely
  undersized.

- **Remote Spilling:** This is a **critical alert**. Data has exhausted
  both memory and local disk, spilling to remote cloud storage. This
  severely degrades performance. Queries exhibiting significant remote
  spilling are strong candidates for a larger warehouse.

#### Symptom 2: Slow, CPU-bound queries (non-spilling)

Sometimes a query is slow even without spilling significant data. This
often indicates that the query is CPU-bound and could benefit from the
additional processing power of a larger warehouse. However, before
resizing, you must first verify that the query can actually take
advantage of the added resources.

- **Prerequisite 1: Verify Sufficient Parallelism Potential.** A query’s
  parallelism is limited by the number of micro-partitions it scans. If
  there are not enough partitions, additional nodes in a larger
  warehouse will sit idle. As a rule of thumb, a query should scan at
  least **~40 micro-partitions per node** in the warehouse for a size
  increase to be effective. You can find the number of partitions
  scanned in the Table Scan operator within the Query Profile.

- **Prerequisite 2: Verify a Lack of Execution Skew.** Performance
  issues can also arise from data skew, where most of the processing is
  forced onto a single node. In the [<u>Query
  Profile</u>](https://docs.google.com/document/d/1LDeFasziRlYL1Z5t9BqJ_MwhECtJHbRDKG5BNWUAuwU/edit?tab=t.lhzra61et1j6),
  check the per-node execution time. If one node is active for
  significantly longer than its peers, the problem lies in the data
  distribution or query structure, not the warehouse size. Sizing up
  will not solve this problem.

Only after confirming that a query has sufficient parallelism potential
and is not suffering from execution skew should you test it on a larger
warehouse to address a CPU bottleneck.

See [<u>Increasing warehouse size in the Snowflake
documentation</u>](https://docs.snowflake.com/en/user-guide/performance-query-warehouse-size)
for more information.

#### Reference Table: Warehouse sizing for parallelism

Use the following table to determine the minimum number of
micro-partitions a query should scan to effectively utilize a given
warehouse size.

| **Warehouse Size** | **Minimum Micro-partitions Scanned** |<br>
|--------------------|--------------------------------------|<br>
| X-Small -----------| 40 ----------------------------------|<br>
| Small   -------------| 80  ----------------------------------|<br>
| Medium  -----------| 160   ---------------------------------|<br>
| Large   -------------| 320  ---------------------------------|<br>
| X-Large -----------| 640  ---------------------------------|<br>
| 2X-Large ----------| 1,280 -------------------------------|<br>
| 3X-Large ----------| 2,560  -------------------------------|<br>
| 4X-Large ----------| 5,120  -------------------------------| <br>
| 5X-Large ----------| 10,240   ------------------------------| <br>
|--------------------|---------------------------------------|<br>

### Horizontal scaling: scaling out for concurrency

Horizontal scaling increases the number of compute clusters available to
your warehouse. This is the primary tool for managing high
concurrency—that is, a high volume of simultaneous queries. When you
configure a multi-cluster warehouse, Snowflake automatically adds and
removes clusters of the same size in response to query load.

This allows your warehouse to handle fluctuating numbers of users and
queries without queueing. As more queries arrive, new clusters are
started to run them in parallel. As the query load subsides, clusters
are automatically suspended to save credits.

#### Configuration modes

You can configure a multi-cluster warehouse to run in one of two modes:

- **Auto-scale Mode:** The default and most common setting, this mode
  automatically adjusts the number of clusters within a defined minimum
  and maximum (e.g., 1 to 8). This is ideal for varying concurrency, as
  Snowflake starts and stops clusters to match query load.

- **Maximized Mode:** This mode continuously runs the maximum specified
  number of clusters (e.g., 8 clusters if both minimum and maximum are
  set to 8). It suits workloads with consistently high and predictable
  concurrency, eliminating latency from new cluster starts.

#### Tuning auto-scale with scaling policies

When using Auto-scale mode, you can further refine its behavior by
setting a scaling policy. This allows you to define the warehouse’s
priority: minimizing wait time or maximizing credit savings.

- **Standard Policy (Performance-First):** This policy prioritizes a
  fast user experience, minimizing queueing by launching new clusters if
  a query is queued for a few seconds. It is ideal for time-sensitive,
  user-facing workloads such as BI dashboards and analytical
  applications.

- **Economy Policy (Cost-First):** This policy prioritizes cost savings
  by starting new clusters more conservatively. A new cluster launches
  only if a query backlog is estimated to keep it busy for at least six
  minutes. This makes it a good choice for non-urgent background
  processes like ETL/ELT pipelines, where some queueing is an acceptable
  trade-off for lower credit consumption.

See [<u>Multi-cluster warehouses in the Snowflake
documentation</u>](https://docs.snowflake.com/en/user-guide/warehouses-multicluster)
for more information.

#### Query Acceleration Service (QAS): Handling workload volatility

The Query Acceleration Service (QAS) enhances warehouse performance by
providing serverless compute resources to accelerate specific, eligible
queries, particularly large table scans. QAS addresses **workload
volatility**, handling unpredictable, large "outlier" queries that
occasionally burden a correctly sized warehouse. This service ensures
smooth performance without requiring a larger, more expensive warehouse
for infrequent, costly queries.

#### The use case for QAS

You should consider enabling QAS for a warehouse when you observe
queries that fit the following profile:

1.  **The query is an outlier:** The warehouse performs well for the
    majority of its queries but struggles with a few long-running
    queries.

2.  **The query is dominated by table scans:** The performance
    bottleneck is the part of the query reading large amounts of data.

3.  **The query reduces the number of rows:** After scanning a large
    amount of data, filters or aggregates reduce the row count
    significantly.

4.  **The estimated scan time is greater than one minute:** QAS has a
    small startup overhead, making it ineffective for shorter queries.
    It only provides a benefit when accelerating scan operations that
    are estimated to take longer than 60 seconds.

Using QAS for this specific use case allows you to improve the
performance of a volatile workload in a highly cost-effective manner.

See [<u>Using the Query Acceleration Service (QAS) in the Snowflake
documentation</u>](https://docs.snowflake.com/en/user-guide/query-acceleration-service)
for more information on QAS

#### Summary: A strategic decision framework

Choosing the right elasticity tool begins with understanding your
workload and identifying the specific performance problem you are
facing. Once you have isolated your workloads into dedicated warehouses,
use the following framework to guide your scaling strategy.

Start by asking: **"What is making my warehouse slow?"**

- **Symptom:** "My queries are waiting in a queue because too many are
  running at once."

  - **Solution:** Your problem is **concurrency**. Use **Horizontal
    Scaling** by configuring a multi-cluster warehouse. Tune the scaling
    policy (Standard or Economy) based on the workload’s time
    sensitivity.

- **Symptom:** "A single, complex query is taking too long to complete,
  even when running by itself."

  - **Solution:** Your problem is **complexity**. Use the diagnostic
    checklist for **Vertical Scaling**. First, check for disk spilling.
    If there is none, verify that the query has sufficient parallelism
    potential and is not skewed before testing it on a larger warehouse.

- **Symptom:** "My warehouse is usually fast, but occasionally a single
  huge query slows everything down."

  - **Solution:** Your problem is **volatility**. Investigate using the
    **Query Acceleration Service**. Verify that the outlier queries are
    scan-heavy and meet the one-minute scan time threshold.

Performance management is not a one-time setup. It is an iterative
process. You should continuously monitor your query performance and
warehouse utilization, using these elasticity tools to tune your
environment and maintain the optimal balance between performance and
cost.

### Test-first design: Building performance into every stage

A high-performing Snowflake environment stems from a deliberate
strategy. Performance validation is integrated into every development
phase. This "Test-First Design" approach shifts performance
considerations to a proactive, continuous process, preventing
architectural debt and ensuring efficient resource utilization. It
supports the Performance by Design philosophy, ensuring that defined
Service Level Objectives (SLOs) are met, validated, and sustained with
optimal cost efficiency.

### Proactive performance validation

In Snowflake's consumption model, performance cost is tied to resource
usage. Deferring performance testing creates technical debt, as flaws
become expensive to fix. This can lead to re-engineering, missed
deadlines, or over-provisioning compute, masking inefficiencies at
significant cost.

Snowflake's ease of use and elasticity can lead to an informal approach
to performance. Vague directives like "queries should be fast" are
insufficient. Without clear, measurable, agreed-upon performance
metrics, designing, validating, or guaranteeing objectives is
impossible.

Proactive performance validation addresses these challenges head-on by:

- **Mitigating Technical Debt:** Identifying and correcting design flaws
  early, when they are cheapest to fix.

- **Ensuring Predictable Outcomes:** Translating business expectations
  into quantifiable performance objectives that guide design and
  development.

- **Optimizing Cost Efficiency:** Balancing performance needs with
  resource consumption to achieve the best price-for-performance.

- **Reducing Risk:** Preventing performance problems before production
  deployment.

### Formalizing performance: KPIs, SLOs, and baselines

Successful performance validation starts with clearly defined
expectations. Vague expectations cannot be tested, measured, or
optimized. Formalize performance requirements using Key Performance
Indicators (KPIs) and Service Level Objectives (SLOs) to establish
baselines for testing and operational monitoring. This process extends
the Workload Requirements Agreements (WRA) detailed in the Performance
by Design guidance.

**Key Performance Indicators (KPIs) for Snowflake Workloads:**

- **Data Freshness (Latency):** The elapsed time from when data is
  generated in source systems to when it is available for querying in
  Snowflake.

  - *Example SLO:* "99% of all point-of-sale transaction data must be
    available in the SALES_ANALYTICS table within 5 minutes of the
    transaction occurring."

- **Query Latency (Response Time):** The time taken for a query to
  execute and return results to the user or application. This is often
  expressed using percentiles to account for variability.

  - *Example SLO:* "For the EXECUTIVE_DASHBOARD_WH, P90 (90th
    percentile) of interactive queries must complete in under 3 seconds,
    and P99 must complete in under 5 seconds."

- **Throughput:** The volume of data or number of operations processed
  within a given timeframe, crucial for batch and ingestion workloads.

  - *Example SLO:* "The nightly ETL_LOAD_WH must ingest and transform 50
    GB of raw transactional data into aggregated analytical tables
    within 30 minutes."

- **Concurrency:** The number of simultaneous queries or users the
  system can support without significant performance degradation or
  excessive queuing.

  - *Example SLO:* "The primary BI_REPORTING_WH must seamlessly support
    100 concurrent users during peak hours (9 AM - 11 AM PST) with
    average query queue time not exceeding 5 seconds."

- **Cost Efficiency:** The credit consumption relative to the business
  value or volume of work performed. This is a critical KPI for CDOs and
  FinOps.

  - *Example SLO:* "The DAILY_REPORTING_JOB must process 1 TB of raw
    data at a cost of no more than 100 credits per run, across all
    associated warehouses."

### Establishing baselines:

Baselines represent the expected or target performance. For new
projects, these are often derived from:

- **Design document:** The formally agreed-upon SLOs become the initial
  target baselines.

- **Synthetic data & Proof-of-Concept (PoC):** Early tests with
  representative, scaled-down data can provide initial estimates.

- **Historical data:** For migrations, existing system performance can
  inform baselines, with adjustments for Snowflake's capabilities.

- **Industry benchmarks:** Comparisons with similar workloads in
  comparable environments.

These formalized metrics transform abstract goals into concrete,
testable objectives, laying the groundwork for effective performance
validation.

#### Shifting left: Integrating performance testing into design & development

The shift-left principle for performance involves embedding testing
activities as early as possible in the development lifecycle. This
ensures that performance considerations are an inherent part of the
design and implementation, preventing the accumulation of technical
debt.

#### Performance in the design phase:

Even before a single line of code is written, critical performance
decisions are made. This phase focuses on architectural review and
proactive estimation.

- **Architectural Review:** Evaluate data models, ingestion, and access
  patterns, and transformation logic for performance. Consider the
  impact of large JOINs on data shuffling or complex views on query
  execution.

- **Early Warehouse Sizing Estimates:** Based on workload categorization
  and concurrency projections, make initial projections for warehouse
  sizes and multi-cluster configurations. Validate these estimates
  through subsequent testing.

- **Query Review:** Analyze proposed high-impact SQL queries or
  transformation logic. Use EXPLAIN on hypothetical queries to
  understand the planned execution and identify potential anti-patterns
  like full table scans or excessive data movement.

#### Performance in the development phase:

As development progresses, unit-level and integration-level performance
testing becomes crucial. Developers must be empowered with the knowledge
and tools to self-diagnose and optimize their code.

- **Unit Testing for Queries:** Developers should test individual SQL
  queries, views, or stored procedures with representative (often
  scaled-down or synthetic) data. The focus here is on the efficiency of
  the specific logic.

- **Query Profile and EXPLAIN Plan Mastery:** For developers,
  understanding the Snowflake [<u>Query
  Profile</u>](https://docs.google.com/document/d/1LDeFasziRlYL1Z5t9BqJ_MwhECtJHbRDKG5BNWUAuwU/edit?tab=t.lhzra61et1j6)
  is paramount. It provides a detailed breakdown of query execution,
  identifying bottlenecks, spilling, data shuffling, and operator costs.

  - **Critical Early Warning Signs:** Beyond obvious remote spilling,
    developers should look for:

    - **High Remote I/O:** Indicates excessive data reads from remote
      storage, potentially due to poor filtering or table design.

    - **Large Data Shuffled:** Signifies inefficient joins or
      aggregations causing significant data movement between warehouse
      nodes.

    - **Ineffective Pruning:** Scanning many more micro-partitions than
      necessary, suggesting missing WHERE clause filters or suboptimal
      clustering.

- **Dedicated Dev/Test Environments with Data Cloning:** Leverage
  Snowflake's Zero-Copy Cloning capability to create isolated,
  full-scale, or representative copies of production data in development
  and testing environments. This allows developers and testers to run
  realistic performance tests without impacting production or incurring
  high costs for duplicate data storage.

### Comprehensive performance validation: load, scale, and stress testing

Before promoting any significant change or new workload to production, a
structured approach to load, scalability, and stress testing is
essential. These tests validate the architecture under various
real-world and extreme conditions, directly addressing the risks of
deploying untested changes and ensuring performance at scale.

#### Load testing:

Load testing simulates the expected peak concurrent user and query
volumes defined in the SLOs. The goal is to verify that the system can
consistently meet its performance objectives under anticipated
production loads.

- **Validation:** Confirm that query latency and throughput SLOs are
  met, and that query queuing is within acceptable limits.

- **Multi-Cluster warehouse behavior:** Observe how multi-cluster
  warehouses (in auto-scale mode) respond to increasing load, ensuring
  clusters spin up and down efficiently according to the chosen scaling
  policy (Standard for performance-first, Economy for cost-first).

- **Tools:** Can involve custom scripting, industry-standard load
  testing frameworks (e.g., JMeter configured for JDBC/ODBC), or
  specialized Snowflake testing partners.

#### Scalability testing:

Scalability testing assesses how the system performs as data volumes
and/or user growth increase significantly beyond current expectations.
This helps identify limitations in the architecture that might not
appear under typical load.

- **Data volume growth:** Simulate increased data over projected periods
  (e.g., 6-12 months). This ensures queries maintain performance or
  degrade predictably, informing long-term warehouse sizing and
  architectural decisions.

- **User growth:** Test with more concurrent users than the current
  peak. This helps understand system capacity and identify potential
  bottlenecks.

- **Detection:** Look for non-linear performance degradation, where
  small load increases lead to disproportionately large performance
  decreases, often signaling a scaling bottleneck.

#### Stress testing:

Stress testing is crucial for identifying the true limits of a system,
validating its resilience, and understanding its failure modes. This
process aims to uncover the performance limitations in the system as
designed, and if necessary correct early – well in advance of
deployment.

- **Extreme Load:** Subject the system to sustained, extreme concurrency
  or data processing volumes.

- **Warehouse Size**: Determine if a larger warehouse size is needed to
  handle the workload.

- **Multi-Cluster Width**: Explore options for horizontal scale-out to
  distribute the load across multiple clusters.

- **Analyze query performance:** Identify slow-running queries and
  optimize their execution plan.

- **Monitor warehouse usage:** Regularly review warehouse credit
  consumption and adjust size as needed.

- **Recovery:** Evaluate how the system recovers after extreme load,
  ensuring stability and data integrity.

- **Query Acceleration Service (QAS) Behavior:** Observe how QAS
  mitigates the impact of unpredictable, outlier queries under stress.

#### Regression testing and CI/CD integration:

To prevent performance degradation from new features or code changes,
integrate performance benchmarks into the Continuous
Integration/Continuous Deployment (CI/CD) pipeline.

- **Best practice**: Major code changes should initiate performance
  tests using representative data.

- **Early detection:** Identify performance regressions immediately,
  allowing developers to fix issues before they propagate downstream or
  reach production.

- **Controlled environments:** Establish dedicated, isolated test
  environments (often using
  [<u>CLONE</u>](https://docs.snowflake.com/en/sql-reference/sql/create-clone)
  of production data) for consistent and repeatable performance
  measurements.

#### Performance and cost tradeoffs: the continuous optimization loop

In Snowflake, every performance decision is inherently a cost decision.
Ignoring these tradeoffs can lead to overspending, even with a
performant system. The Test-First Design philosophy extends into a
continuous optimization loop, where cost is a primary KPI.

By integrating performance and cost considerations from design to
continuous operation, organizations can build a Snowflake environment
that is not only robust and responsive but also financially prudent.
This proactive, data-driven approach ensures that the investment in
Snowflake delivers maximum value while avoiding the common pitfalls of
deferred performance management.

## Data design and access
### Optimize data architecture and access

### Overview

Optimal performance relies on solid architectural practices. This
entails implementing and upholding a comprehensive architectural review
process, employing a layered design to efficiently handle complexity,
and making the best possible design decisions. This process should
actively gather input from diverse teams involved in business
application development, ensuring all business needs are addressed, and
the resulting design accommodates a broad spectrum of requirements.

Key components of this process are periodic application performance
reviews, incorporating data quality validations and data lifecycle
management. Planning physical data access paths to support peak
performance is also crucial. Tools for achieving this include effective
data modeling techniques, appropriate data type selections for storing
values, and creating favorable data access pathways.

### Desired outcome

Adhering to sound architectural and data access recommendations helps
Snowflake applications achieve optimal performance and scalability. This
proactive approach ensures that the application's foundation is robust,
enabling it to efficiently handle evolving business demands and large
volumes of data. The outcome is a highly responsive application that
delivers a superior user experience, while simultaneously minimizing
operational overhead and resource consumption.

A well-defined architectural review process, coupled with a layered
design, leads to a more maintainable and adaptable Snowflake
application. This structured approach simplifies future enhancements,
bug fixes, and integrations, reducing the total cost of ownership. The
ability to incorporate diverse team input throughout the design phase
guarantees that the application effectively addresses a broad spectrum
of business requirements, resulting in a solution that is both
comprehensive and future-proof.

Finally, strategic planning for physical data access paths, along with
effective data modeling and appropriate data type selections, directly
translates to accelerated query execution and improved data integrity.
Regular performance reviews, including data quality validations and
lifecycle management, ensure that data remains accurate, accessible, and
optimized for peak performance. This integrated approach ultimately
empowers users with timely and reliable insights, driving better
business decisions and maximizing the value derived from the Snowflake
platform.

### Recommendations

The following list provides actionable recommendations for a database
practitioner to achieve strong performance in a Snowflake environment:

1.  Maintain high data quality

2.  Optimize data models

3.  Carefully choose data types

4.  Refine data access

#### Maintain high data quality

Maintaining high data quality is critical for achieving optimal query
performance and deriving reliable business insights within Snowflake. By
strategically utilizing Snowflake's inherent capabilities, such as the
careful selection of datatypes and the implementation of NOT NULL
constraints, you can establish a robust foundation for data accuracy and
consistency. This approach not only streamlines development efforts but
also significantly improves the efficiency of join operations.

While Snowflake offers declarative constraints like PRIMARY KEY, UNIQUE,
and FOREIGN KEY, it's crucial to understand that these are not actively
enforced by the database. As a result, ensuring true data integrity,
uniqueness, and accurate referential relationships requires external
enforcement. You can achieve this by designing application logic or
integrated data integration processes. Such external validation is
indispensable for optimizing query execution, guaranteeing the
trustworthiness of analytical results, and ultimately maximizing the
value of your data in Snowflake.

#### Optimize data models

Optimizing data models can enhance Snowflake's performance. When
designing schemas, consider the impact of very wide tables. While
Snowflake is efficient, extensive wide table schemas can increase query
compilation time, particularly for complex queries or deep view/CTE
hierarchies. For short, interactive queries, this impact can be more
noticeable. As an alternative, consider VARIANT for numerous scalar
elements, or VARCHAR structured as JSON, utilizing PARSE_JSON().
However, avoid filtering or joining on scalar attributes in complex
VARIANT/VARCHAR values, as this can hinder pruning effectiveness.

Strategic denormalization is another valid technique, especially for
analytical workloads. By pre-joining and storing relevant data together,
you reduce the number of join operations, benefiting from Snowflake's
columnar storage and micro-partitioning. This co-locates frequently
accessed attributes, improving data locality and enhancing
micro-partition pruning for faster query execution and optimized
resource consumption.

#### Carefully choose data types

Optimizing application query performance in Snowflake relies on data
type selection during schema design. Specifically, the data types of
columns used in filter predicates, join keys, and aggregation keys
significantly influence the query optimizer's efficiency and can
introduce computational overhead.

For optimal performance, use numeric data types for join keys. Temporal
data types like DATE and TIMESTAMP_NTZ also generally outperform others
in filtering and join key scenarios due to their numerical nature.

Coordinating data types for common join keys across tables within the
same schema is crucial. Mismatched data types require explicit or
implicit type casting, which consumes CPU cycles and can reduce the
effectiveness of dynamic (execution time) pruning, leading to measurable
performance degradation, especially on the probe side of a join.

Finally, while collation is sometimes necessary, it introduces
significant performance overhead and should be used sparingly, ideally
only for presentation values and never for join keys, as it can
interfere with crucial performance features like pruning.

#### Refine data access

Optimizing data access in Snowflake is crucial for achieving peak query
performance. Several techniques are recommended, starting with
**Pruning**, which minimizes scanned micro-partitions by leveraging
metadata. Both static pruning (compile-time, based on WHERE clauses) and
dynamic pruning (runtime, based on join filters) are utilized. Static
pruning is generally preferred due to its predictability.

[<u>Clustering</u>](https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions)
significantly enhances pruning by physically co-locating similar data
within micro-partitions. This reduces the data range for filtered
columns, leading to more efficient micro-partition elimination.
Effective clustering also benefits join operations, aggregations, and
DML (UPDATE, DELETE, MERGE) by reducing I/O requirements.

The [<u>Search Optimization
Service</u>](https://docs.snowflake.com/en/user-guide/search-optimization-service)
dramatically accelerates various query types, including selective point
lookups, searches on character data (using SEARCH, LIKE, RLIKE), and
queries on semi-structured or geospatial data.

[<u>Materialized
Views</u>](https://docs.snowflake.com/en/user-guide/views-materialized)
improve performance by pre-computing and storing expensive query
results, offering faster access for frequently executed or complex
operations. They are particularly useful for aggregations and queries on
external tables, with Snowflake handling automatic updates.

[<u>Dynamic
Tables</u>](https://docs.snowflake.com/en/user-guide/dynamic-tables-about)
also pre-compute query results, but offer continuous refreshment, ideal
for BI dashboards needing low-latency data. They leverage Snowflake's
query optimizations and can be further enhanced with clustering and
search optimization.

Finally, **Join Elimination** optimizes queries by removing unnecessary
joins when they don't alter the result set, typically in primary/foreign
key relationships where joined columns aren't projected, significantly
reducing data processing overhead.

- Step-by-step Instruction

  - [<u>A Data-Driven Methodology for Choosing a Snowflake Clustering
    Key</u>](/en/developers/guides/getting-started-with-snowflake-cluster-key-selection/)

- Blog Articles

  - [<u>Turbo-charge your Data Model with Snowflake’s Join
    Elimination</u>](https://medium.com/snowflake/turbo-charge-your-data-model-with-snowflakes-join-elimination-4fedc8a47d26)

  - [<u>Automatic Clustering at
    Snowflake</u>](https://medium.com/snowflake/automatic-clustering-at-snowflake-317e0bb45541)

  - [<u>Snowfake Clustering
    Demystified</u>](https://medium.com/snowflake/snowflake-clustering-demystified-8042fa81289e)

  - [<u>Snowflake Dynamic Table Complete
    Guide</u>](https://medium.com/snowflake/snowflake-dynamic-table-complete-guide-6-final-c363aa7e273a)



### Data quality for better performance

Maintaining high data quality is crucial for optimal query performance
within your application workflow. Snowflake offers built-in features for
automatic data quality enforcement and declarative capabilities for
external implementations.

Operating on well-structured, high-quality data provides benefits across
the data lifecycle, from ingestion to advanced analytics and reporting.
These advantages lead to greater efficiency, reduced costs, and more
reliable business insights.

- **Cleaner SQL code and reduced development effort:** Clean data
  minimizes defensive coding, simplifying SQL for transparency and
  maintainability. This allows focus on business logic over data
  cleansing, accelerating development, reducing support, and freeing
  engineering resources. Predictable query behavior and fewer errors
  result.

- **Faster join performance:** Efficient join operations require
  equality predicates, clean data, and matching data types. Inconsistent
  data types or dirty data impede the optimizer, creating performance
  bottlenecks. Data cleanliness and type consistency enable efficient
  join algorithms, speeding query execution for complex analytical
  workloads.

### Using data types for data quality enforcement

Proper datatype selection is a fundamental aspect of robust data quality
practices. While often overlooked, correct datatype assignment provides
inherent constraints and optimizations, significantly contributing to
data accuracy, consistency, and integrity. For instance, storing
numerical values as numbers, rather than strings, prevents invalid
entries like "abc" and enables accurate mathematical operations.
Similarly, date/time datatypes ensure chronological order and allow for
precise time-based filtering and analysis.

Stricter data types offer significant advantages for database
performance, primarily by establishing a clear domain of valid values,
which benefits the query optimizer, reduces storage utilization, and
improves join performance.

**Optimizing query performance through stricter data types**

- **Improved query optimizer efficiency:** Variability in data values
  can lead to complex filters and join predicates, hindering query
  performance. Stricter data types limit this variability, reducing
  cardinality and enhancing micro-partition statistics.

- **Accurate cardinality estimation:**Data statistics are gathered at
  the micro-partition level. Varying values with the same meaning
  distort the query optimizer's cardinality estimations. Stricter data
  types, such as BOOLEAN or DATE, provide precise information, leading
  to accurate cardinality estimates.

- **Enhanced performance with numerical data types:** Stricter data
  types, often numerical, optimize performance. This facilitates binary
  predicates in filters and joins, resulting in faster database
  application performance.

**Reduced storage utilization**

- **Efficient data storage:** Numerical data types generally consume
  less storage due to their inherent efficiency in how computer systems
  represent and process numbers. Integers and floating-point numbers
  store in fixed-size memory blocks, with size determining range and
  precision. This contrasts with variable-length types like strings or
  complex objects.

- **Improved data compression** occurs with strictly defined data types,
  reducing cardinality within micro-partitions. Tighter constraints
  increase value unification, enabling more efficient compression
  algorithms. This minimizes storage footprint and accelerates data
  retrieval and processing due to reduced data volume, optimizing
  storage and performance in modern data warehousing and database
  systems.

- **Physical I/O reduction:** For large tables, storage optimization
  significantly reduces the physical storage footprint, directly
  decreasing the number of physical I/O operations for data access and
  processing. This leads to substantial overall performance improvement.
  Minimizing disk read/write needs allows systems to complete queries
  and operations more quickly, enhancing responsiveness and efficiency
  for users and applications, and optimizing resources for a more
  efficient data processing pipeline.

**Optimized join performance**

- **Consistent data types for join keys:** For optimal query
  performance, ensure columns used in equality join conditions have
  identical data types. Mismatched data types lead to implicit
  conversions, degrading performance. Meticulous data type assignment
  during design, matching frequently joined columns across tables, is
  crucial for a performant database application.

- **Superior performance of numerical types in joins:** Numerical data
  types generally offer better performance in equality join conditions
  compared to VARCHAR.

- **Temporal data type efficiency:** For optimal performance in join
  keys and filters, consider using DATE and TIMESTAMP_NTZ. These data
  types do not store timezone information, eliminating runtime
  adjustments and allowing the optimizer to utilize Min/Max statistics
  effectively.

### NOT NULL constraints for data quality enforcement

Snowflake's NOT NULL constraints ensure data quality by requiring
specified columns to always contain a value, preventing incomplete or
missing data. This establishes a baseline for critical data points,
reducing the need for later cleansing.

Beyond data quality, NOT NULL constraints enhance query performance. The
optimizer can make more efficient query plan decisions when a column is
known to contain no NULL values, especially in equality join conditions.
This allows for more streamlined equality predicates.

**Performance benefits of NOT NULL constraints:**

- **Simplified query logic:** Eliminates the need for separate IS
  \[NOT\] NULL predicates, streamlining query construction. You can
  write cleaner, more concise SQL, reducing complexity and improving
  readability, maintainability, and debugging. This approach minimizes
  potential errors, leading to more robust and efficient database
  operations.

- **Reduced query overhead:** Snowflake's query optimizer automatically
  introduces a nullability filter when a nullable column is used in an
  equality inner join. This additional filter consumes CPU time,
  resulting in performance overhead that you can avoid by using NOT NULL
  constraints.

### The role of primary key and unique constraints

Snowflake supports PRIMARY KEY and UNIQUE constraints for SQL
compatibility, but these are not enforced. Maintaining data integrity is
your application's responsibility.

External enforcement of these constraints is vital for data integrity in
analytical workloads, ensuring reliable reporting and correct
aggregations. Validation checks, deduplication, or upsert mechanisms in
your data pipelines ensure only valid, unique records are loaded.

Beyond integrity, external enforcement benefits query performance. When
data is guaranteed unique externally, Snowflake's query optimizer
generates more efficient execution plans by leveraging metadata and
statistics. This avoids unexpected data duplication in joins and
promotes cleaner query code, reducing complexity.

**Optimizing query performance with primary key and unique constraints**

- **Enhanced query optimizer selectivity:** Enforcing Primary Key and
  Unique constraints ensures cleaner data, which benefits
  micro-partition statistics. Accurate record counts and distinct values
  are crucial for the query optimizer to estimate selectivity precisely,
  leading to more effective query plans.

- **Enabling join rlimination:** The RELY property, when set for a
  Primary Key or Unique constraint, is a prerequisite for Snowflake's
  Join Elimination. This dynamically removes unnecessary joins,
  improving query performance, and relies on externally enforced
  uniqueness.

- **Reduced fefensive voding:** External uniqueness enforcement
  minimizes defensive SQL coding in downstream applications,
  streamlining development and enhancing application robustness.

### Foreign key constraints

Snowflake supports foreign key constraints for SQL compatibility but
does not enforce them. Maintaining referential integrity is your
responsibility. Enforcing these constraints ensures data consistency and
accuracy, improving downstream query performance by assuming valid table
relationships. This simplifies query logic and streamlines join
operations, leading to faster, more predictable query execution.

**Performance benefits of foreign key constraints**

- **Snowflake Join Elimination:** Setting the RELY property on a foreign
  key constraint enables Snowflake's Join Elimination, improving query
  efficiency by removing unnecessary joins.

- **INNER JOIN optimization:** When a foreign key is externally
  enforced, INNER JOINs offer optimizations not available with OUTER
  JOIN. Use OUTER JOIN only for inconsistent data where foreign key
  constraints are not strictly enforced.

### Data modeling for performance

Optimizing data models can significantly enhance Snowflake's already
impressive performance. Most industry-standard data modeling techniques
are applicable when designing a schema in Snowflake. The following
sections explore common and model-specific considerations.

### Star Schema

The Star Schema model works well with Snowflake, favoring right-deep
query execution plans. This positions the largest fact table on the far
probe side of joins. The model also benefits from Join Elimination,
which excludes optional dimensions (joined with OUTER JOIN) if they're
not part of the final projections.

**Considerations:**

- **Fact table clustering:** You should consider clustering large fact
  tables. Clustering key candidates should include frequently used
  filters, join keys, and a temporal attribute reflecting the natural
  data ingestion order.

- **Numerical data types for keys:** Use of numerical data types for key
  columns involved in equality joins is strongly recommended for optimal
  performance.

### Data Vault 2.0

**Considerations:**

- **Numerical keys:** For optimal performance, use numerical keys
  instead of hash keys (e.g., MD5). Hash keys, being alphanumeric
  VARCHAR, are less effective for clustering because Snowflake only
  considers the first five bytes for clustering, ignoring the rest.
  Their random nature also prevents natural record co-location, leading
  to higher reclustering costs and suboptimal states.

- **Strategic table clustering:** Data Vault schemas, with their higher
  normalization, often involve queries across many large tables. To
  improve performance, strategically cluster these tables using a shared
  attribute that is also part of join and filter conditions. This
  enhances pruning and improves query performance.

- **Local materializations:** For performance issues when joining
  multiple large tables, consider limited materializations using Dynamic
  Tables to boost query execution speed.

#### Very vide tables

Query compilation time in Snowflake can be affected by very wide tables
(hundreds of columns). The optimizer processes more metadata at
compilation, extending the time from submission to execution. This is
more noticeable in complex queries referencing many columns or involving
intricate logic, especially with deep dynamic views or [<u>CTE
hierarchies</u>](https://docs.snowflake.com/en/user-guide/queries-cte).
While often minor for long-running analytical queries, it can impact
short interactive queries.

A balanced schema design is key. Consider using a VARIANT data type for
numerous individual scalar data elements, or a large VARCHAR structured
as JSON. The PARSE_JSON() function allows for easy data access.
Snowflake automatically subcolumnarizes up to a set number of unique
elements within a VARIANT, though this is not guaranteed and has
restrictions.

Avoid combining scalar attributes frequently used for filtering and
joins into a single VARIANT or VARCHAR, as this can reduce pruning
effectiveness due to a lack of collected statistics for these complex
values.

#### Denormalization

Denormalization can optimize query performance in Snowflake,
particularly for analytical tasks. While a normalized schema ensures
data integrity, it often necessitates multiple joins, adding
computational overhead. Strategic denormalization pre-joins relevant
data, reducing the need for joins at query time.

This approach leverages Snowflake's columnar storage and
micro-partitioning. By co-locating frequently accessed attributes within
the same micro-partition, data locality improves for common queries,
minimizing I/O operations. Micro-partition pruning is also enhanced,
allowing the warehouse to efficiently skip irrelevant data during scans.

Strategic denormalization significantly improves query performance and
optimizes resource usage. By reducing complex joins and leveraging
micro-partition pruning, you can design schemas for highly performant
analytical workloads. This provides faster access to insights and a more
responsive user experience, balancing performance with data integrity.

#### Finding the balance

Achieving the right balance among these concepts requires careful
testing. There's no universal guideline or ideal degree of
denormalization; each data model and dataset is unique. Therefore,
extensive testing is crucial to determine the most effective approach
for your specific business needs.

### Data type for performance

Optimizing query performance depends on the data type choices made
during schema design. The physical data type of a column can
significantly impact the query optimizer's choices and introduce
computational overhead. This is especially true when the column is used
in filter predicates, join key predicates, or as an aggregation key.

### Data type recommendations

Consider the following data type recommendations when designing a
schema:

- **Join key data types:** Use numerical data types for join keys for
  superior performance. Snowflake often pushes join filters to the probe
  side, and numerical values create a more robust filter.

- **Temporal data types:** Understand the performance implications of
  temporal data types. DATE and TIMESTAMP_NTZ generally perform better
  in filtering and join key scenarios.

- **Collation considerations:** Use collation only when essential due to
  its performance impact. Avoid using collation for join keys.

### Data types and join performance

For optimal performance, use identical data types for common join keys
across tables in the same schema. Type casting of join keys, whether
explicit or implicit, introduces performance overhead due to CPU cycles
and can hinder dynamic pruning.

Snowflake automatically casts columns with lower precision to match the
data type of the opposite join key, but this still incurs the same
performance disadvantages as explicit casting. When type casting is
applied to a key on the probe side of a join, it typically leads to
measurable performance degradation. You can observe type casting in a
join on the query profile for each join operation.

The Snowflake query optimizer pushes join filters derived from equality
join conditions in inner joins to the probe side. Filters based on
numerical values offer superior initial filtering and enhanced
performance. DATE and TIMESTAMP_NTZ data types are numerical and share
these performance characteristics, meaning the impact of non-coordinated
data types also applies to them.

See ​​[<u>Data Type Considerations for Join Keys in
Snowflake</u>](https://medium.com/snowflake/data-type-considerations-for-join-keys-in-snowflake-304d515d2b91)
for further exploration of this topic.

### Temporal data type choices and performance 

Snowflake offers various temporal data types, all stored numerically.
For optimal **filtering** performance, DATE and TIMESTAMP_NTZ are
superior.

These types are offsets from EPOCH. DATE uses smaller numerical values,
leading to better performance for equality join keys due to its smaller
memory and storage footprint. TIMESTAMP_NTZ offers greater precision
with only slightly lower performance.

TIMESTAMP_TZ and TIMESTAMP_LTZ, which include a timezone component, are
stored using UTC and a dynamic timezone offset. This dynamic calculation
consumes CPU cycles and interferes with pruning. While suitable for
presentation, if precise filtering or joining on timestamp values with
timezones is needed, use two columns: one without a timezone (DATE or
TIMESTAMP_NTZ) for pruning, and another with a timezone for accurate
representation.

### Collation

Collation introduces measurable performance overhead, especially for
join keys. Numerical join keys are faster, regardless of collation. You
should restrict collation use to presentation values only for optimal
performance.

Even with a collation definition at the DATABASE, SCHEMA, or TABLE
level, data is physically stored without collation. The transformation
is dynamic upon data access. While column statistics at the
micro-partition level reflect the default (no collation) state for
min/max values, filters and join keys must adhere to collation rules.
This misalignment hinders important performance features like pruning.

See [<u>Performance implications of using
collation</u>](https://docs.snowflake.com/en/sql-reference/collation#performance-implications-of-using-collation)
for further exploration of this topic.

### Summary

Taking the time to thoughtfully choose data types can make a significant
difference in performance, particularly at scale. Data types matter in
Snowflake, but not always in expected ways. Pay special attention to the
data types for join keys, temporal data types, and avoid the use of
collations where possible.

### Data access

### Pruning

Pruning eliminates unnecessary Snowflake scanning. This efficiency is
measured by the ratio of unscanned to total micro-partitions during
table access. For instance, scanning only one out of 100
micro-partitions yields 99% pruning efficiency. Pruning decisions are
based on the minimum and maximum values stored as metadata for columns
involved in filters or join keys.

### Static vs dynamic pruning

Snowflake utilizes both static and dynamic pruning. Static pruning,
which occurs during query compilation in the Cloud Services Layer, uses
WHERE clause filters to optimize queries. Its impact on the execution
plan is analyzed and factored into cost calculations.

Dynamic pruning, performed at runtime by the Virtual Warehouse, employs
join filters to prune unnecessary scans. Its effectiveness is not known
during compilation, thus it doesn't affect execution plan cost or table
join order.

Static pruning is generally preferred. Regardless, a query profile will
always show actual scanning statistics and the number of
micro-partitions scanned.

### Clustering

Snowflake performance is significantly enhanced by clustering, which
minimizes micro-partition scans by co-locating frequently queried
records. The primary goal is to reduce the range of values in
micro-partition statistics for columns used in query filter predicates,
improving pruning.

To select an effective clustering key, identify queries needing
optimization and choose potential candidates based on filters and join
predicates. Evaluate the cardinality of these candidates to determine an
optimal combined clustering key cardinality relative to the total number
of full-size micro-partitions. Finally, test the chosen key on a subset
of actual data.

Clustering also benefits DML operations (UPDATE, DELETE, MERGE). By
using a specific clustering key combination, you can facilitate the
co-location of records frequently modified by the same DML query. This
reduces the number of micro-partitions affected by DML logic, leading to
lower physical write I/O and improved query execution performance.

### Search Optimization Service

The Snowflake [<u>Search Optimization
Service</u>](https://docs.snowflake.com/en/user-guide/search-optimization-service)
significantly improves query performance for faster response times and a
better user experience. This service helps data consumers, from business
analysts to data scientists, gain insights with unmatched speed.

A key benefit is the acceleration of selective point lookup queries,
which return a small number of distinct rows. These queries are vital
for applications requiring immediate data retrieval, such as critical
dashboards needing real-time data for decision-making.

Search Optimization Service also improves the speed of searches
involving character data and IPv4 addresses using the
[<u>SEARCH</u>](https://docs.snowflake.com/en/sql-reference/functions/search)
and
[<u>SEARCH_IP</u>](https://docs.snowflake.com/en/sql-reference/functions/search_ip)
functions. This is particularly beneficial for applications relying on
text-based queries, such as log analysis or security monitoring, where
quick identification of specific text patterns or IP addresses is
critical.

The service extends performance enhancements to substring and regular
expression searches, supporting functions like
[<u>LIKE</u>](https://docs.snowflake.com/en/sql-reference/functions/like),
[<u>ILIKE</u>](https://docs.snowflake.com/en/sql-reference/functions/ilike),
and
[<u>RLIKE</u>](https://docs.snowflake.com/en/sql-reference/functions/rlike).
This capability is vital for scenarios requiring fuzzy matching or
complex pattern recognition, allowing for quicker and more comprehensive
data exploration without typical performance bottlenecks.

Finally, search optimization delivers substantial performance
improvements for queries on semi-structured data (VARIANT, OBJECT, and
ARRAY columns) and geospatial data. For semi-structured data, it
optimizes equality,
[<u>IN</u>](https://docs.snowflake.com/en/sql-reference/functions/in),
[<u>ARRAY_CONTAINS</u>](https://docs.snowflake.com/en/sql-reference/functions/array_contains),
[<u>ARRAYS_OVERLAP</u>](https://docs.snowflake.com/en/sql-reference/functions/arrays_overlap),
full-text search, substring, regular expression, and NULL value
predicates. For geospatial data, it speeds up queries using selected
[<u>GEOGRAPHY</u>](https://docs.snowflake.com/en/sql-reference/functions-geospatial)
functions. These optimizations are crucial for efficiently handling
diverse and complex data structures, ensuring modern applications can
rapidly query and analyze all data types.

### Materialized views

[<u>Materialized
views</u>](https://docs.snowflake.com/en/user-guide/views-materialized)
improve query performance by pre-computing and storing data sets, making
queries inherently faster than repeatedly executing complex queries
against base tables. This is especially beneficial for frequently
executed or computationally complex queries, accelerating data retrieval
and analysis.

These views speed up expensive operations like aggregation, projection,
and selection. This includes scenarios where query results represent a
small subset of the base table's rows and columns, or when queries
demand significant processing power, such as analyzing semi-structured
data or calculating time-intensive aggregates.

Materialized views also offer an advantage when querying external
tables, which can sometimes exhibit slower performance. By materializing
views on these external sources, you can mitigate performance
bottlenecks, ensuring quicker data access and more efficient analytical
workflows.

Snowflake's implementation ensures data currency and transparent
maintenance. A background service automatically updates the materialized
view as base table changes occur, eliminating manual upkeep and reducing
errors. This guarantees that data accessed through materialized views is
always current, providing consistent and reliable performance.

### Leverage Dynamic Tables for query performance

Dynamic Tables boost query performance by materializing data. Unlike
standard views that re-execute queries, Dynamic Tables pre-compute and
store results, creating continuously refreshed data. This means complex
queries are computed once per refresh, not every time a user queries.

This benefits applications like BI dashboards and embedded analytics,
where low latency is crucial. Directing these applications to a Dynamic
Table makes end-user queries simple SELECT statements on pre-computed
results. This significantly improves performance by bypassing complex
logic, leading to quicker execution and better response for many
concurrent users.

As periodically refreshed tables, Dynamic Tables share performance
advantages with standard tables. Snowflake automatically collects
statistical metadata and applies advanced query optimizations. You can
further optimize Dynamic Tables with features like automatic clustering,
Search Optimization Service for improved partition pruning, and
additional serverless features such as Materialized Views and the Query
Acceleration Service.

### Join elimination

[<u>Join
elimination</u>](https://docs.snowflake.com/en/user-guide/join-elimination),
a powerful Snowflake query optimization, significantly enhances query
performance by removing unnecessary joins. This occurs when the
optimizer determines a join won't change the query result, typically
involving primary/foreign key relationships declared with the RELY
keyword. Columns from the "joined" table must not be required in the
final projection (e.g., not selected or used in WHERE, GROUP BY, or
ORDER BY clauses that would alter the outcome).

The primary benefit of join elimination is a substantial reduction in
processed and transferred data, leading to faster query execution and
lower compute costs. By eliminating a join, Snowflake avoids reading
unnecessary data and performing the join operation, which is
particularly beneficial in complex queries. This intelligent
simplification allows Snowflake to focus computational resources on
essential query components, delivering results more efficiently.

### Data Lifecycle Management

Data Lifecycle Management (DLM) is crucial for optimizing Snowflake
performance. By setting clear policies for data retention, archiving,
and deletion, organizations ensure that only actively used data resides
in frequently accessed objects. This proactive approach minimizes data
processed for queries, leading to faster execution and reduced compute
costs. Efficiently managed data also improves micro-partition pruning,
making your dataset more concise.

As data ages and access declines, keeping seldom-accessed historical
data in active tables with many micro-partitions can create performance
overhead during query compilation. Isolating historical data into
separate tables maintains peak query performance for frequently used
data, while ensuring full access for analytical purposes. This also
allows for alternative clustering strategies that benefit analytical
query performance. Since data is often transferred in large batches,
periodic reordering may be unnecessary. You can choose manual data
clustering by sorting records in each batch to reduce ongoing automatic
clustering costs.

## Scale and workload management
### Architect for scalability and workload partitioning

### Overview

To achieve highly performant, scalable solutions on Snowflake, fully
leverage its multi-cluster shared data architecture. This architecture
separates compute from storage, allowing independent scaling. Assigning
different workloads to dedicated virtual warehouses lets you match
compute resources to query complexity. This ensures one workload (e.g.,
data engineering) doesn't negatively impact another (e.g., a critical BI
dashboard). Workload isolation typically improves cache hit ratios and
compute resource utilization, leading to faster performance and better
price-performance.

### Desired outcomes

Adhering to this principle improves business agility and
decision-making. Quickly available data insights help you respond to
market changes and adapt strategic plans. This principle also
contributes to greater data operation stability and reliability.
Workload isolation prevents poorly performing queries from crippling
analytical operations, creating a more robust data platform, increasing
user trust, and reducing troubleshooting. Finally, it leads to reduced
operational costs and simplified performance administration.
Right-sizing virtual warehouses avoids over-provisioning and
under-provisioning. Simplifying administration frees technical resources
to focus on business advancement.

### Recommendations

Here are some specific and actionable recommendations to architect
high-performance, scalable solutions on Snowflake:

#### Optimize virtual warehouses for cost and performance

Optimizing for cost and performance is a key best practice on Snowflake,
involving the strategic tuning of warehouse-level parameters to match
workload needs. Leveraging parameters like AUTO_RESUME and AUTO_SUSPEND
is a great way to ensure you're only paying for compute resources when
queries are actively running. You often right-size the warehouse's
t-shirt size to match query complexity, while using multi-cluster
settings like MIN_CLUSTER_COUNT and MAX_CLUSTER_COUNT allows for
automatic scaling to handle any potential ebbs and flows of concurrent
activity. Finer control over how clusters scale and handle queries can
be achieved with the scaling policy and MAX_CONCURRENCY_LEVEL parameter,
which helps teams achieve the best price-performance for their specific
workload.

#### Implement strategies for handling concurrent queries

Effectively handling concurrent queries is a key architectural
consideration on Snowflake, and the preferred approach is using
multi-cluster virtual warehouses which automatically scale compute
resources in response to query load. You can fine-tune this behavior
with parameters like MIN_CLUSTER_COUNT and MAX_CLUSTER_COUNT to define
the scaling boundaries, and MAX_CONCURRENCY_LEVEL to control the number
of queries per cluster. For predictable batch workloads, a great
strategy is to stagger scheduled jobs to reduce concurrency spikes and
lessen demand on warehouses. Additionally, isolating large,
rarely-executed scheduled jobs into a dedicated warehouse is a best
practice, as it prevents resource contention and allows for programmatic
resume and suspend to eliminate idle time and save on cost.

#### Utilize Snowflake's serverless features

Snowflake's serverless features abstract away the manual configuration
of virtual warehouses by leveraging shared compute that is typically
metered by the second. In contrast, virtual warehouses are dedicated to
a customer and have a one-minute minimum for billing. This allows for
better utilization of shared compute resources via an economy of scale,
which in turn enables Snowflake to provide excellent price-performance.
By leveraging these services, teams can achieve significant compute
efficiency gains for a variety of specific workloads.

The Search Optimization Service automatically builds a data structure
that drastically reduces the amount of data scanned for highly selective
queries. The Query Acceleration Service offloads parts of resource-heavy
queries to shared compute pools, which prevents long-running "outlier"
queries from monopolizing a warehouse. For repeatable, complex
aggregations, the Materialized View Service automatically maintains
pre-computed results, allowing subsequent queries to bypass
recomputation entirely. Finally, Serverless Tasks automatically manage
and right-size the compute for scheduled jobs, eliminating the need for
manual warehouse configuration and ensuring efficient credit
consumption.

#### Leverage Dynamic Tables for data engineering pipelines

Dynamic Tables are a powerful new feature that dramatically simplifies
the creation and management of data pipelines on Snowflake. By using a
declarative SQL syntax, they automate the complex incremental DML
operations required to keep a table up-to-date, eliminating the need for
manual orchestration, which can be tedious, suboptimal, and prone to
errors. Similar to materialized views, they pre-compute and store query
results, which significantly improves the performance of downstream
queries. This declarative approach simplifies pipeline development and
monitoring, leading to enhanced data engineering productivity and a more
streamlined architecture.

### Optimize virtual warehouses for cost and performance

### Isolate workloads

Implementing workload isolation with multiple virtual warehouses is
crucial for optimizing Snowflake performance. This strategy prevents
resource contention by dedicating separate compute resources to distinct
tasks, such as isolating long-running ETL from time-sensitive BI
queries. It also provides a robust mechanism for cost management and
accountability, especially for organizations with a single Snowflake
account and many business units, by simplifying internal chargeback and
encouraging teams to optimize their compute usage.

**Examples include:**

- A smaller, multi-cluster warehouse (e.g., X-Small or Small with an
  upper bound of 5-10 clusters) is ideal for ad-hoc queries from
  business users and analysts. This setup dynamically scales to meet
  variable, bursty query loads, ensuring performance objectives are met
  without over-provisioning and keeping costs in check.

- A Medium or Large single-cluster warehouse suits data ingestion and
  data engineering jobs. These jobs often process larger data sets and
  require more compute, especially with complex transformations.

- A very large dedicated warehouse (e.g., 2X-Large or higher) is best
  for complex, high-volume monthly batch jobs. Isolating such jobs
  prevents negative impact on others and allows for precise
  right-sizing. You can programmatically resume the warehouse before the
  job and suspend it afterward, avoiding idle time costs.

### Use meaningful names for warehouses

Use descriptive names (e.g., BI_REPORTING_WH, ETL_LOADER_WH) to make it
easy for users and administrators to understand the purpose of each
warehouse and prevent mixing workloads. This will also make it easier to
understand dashboards and reports that provide insights into performance
and cost metrics by warehouse name.

### Leverage auto-resume and auto-suspend

Warehouses typically benefit from auto-resume (default). This allows a
warehouse to spin up automatically from a suspended state when a query
is issued. Disabling this requires manual resumption via an ALTER
WAREHOUSE RESUME command, leading to:

- a query failing because it's issued against a suspended warehouse.

- a manually resumed warehouse sitting idle, accruing credits without
  servicing queries.

Configure virtual warehouses to automatically suspend after inactivity
(e.g., 60-300 seconds). This saves credit when not in use, benefiting
intermittent workloads. However, suspension flushes the data cache,
which avoids expensive remote reads. For a BI dashboard, a longer
suspension (e.g., ten minutes) might be better to keep the cache warm.
For data engineering, where caching often yields less benefit, a shorter
auto-suspend interval is often optimal.

### Right-size your warehouses

Start with a smaller warehouse size and scale up if queries spill or
take too long. For slow queries, if stepping up the warehouse size
(doubling CPU, memory, and SSD) does not roughly halve the query time,
consider a smaller size for better resource utilization. If necessary,
perform performance profiling to identify why it isn't scaling linearly,
often due to uneven processing.

Warehouse size should primarily be driven by workload complexity, not
average or peak concurrency, which is often better handled by
multi-cluster warehouses. Increasing warehouse size for concurrency,
especially peak, typically results in over-provisioning and increased
credit consumption without a corresponding price-performance ratio.

Spilling occurs when a fixed-size resource (memory or local SSD) is
fully utilized, requiring additional resources. Local spilling moves
memory contents to SSD; remote spilling moves SSD contents to remote
storage. Excessive spilling, particularly remote, often signals an
undersized warehouse for its assigned workload. The QUERY_HISTORY view
in ACCOUNT_USAGE provides insights into local and remote spilling via
bytes_spilled_to_local_storage and bytes_spilled_to_remote_storage
attributes. These metrics can identify warehouses for upsizing due to
excessive spilling.

### Enable multi-cluster warehouses (MCWs)

For high-concurrency BI reporting, enable [<u>multi-cluster
warehouses</u>](https://docs.snowflake.com/en/user-guide/warehouses-multicluster)
(Enterprise Edition and above). This allows Snowflake to automatically
scale out clusters when queries queue and scale in when load decreases,
ensuring consistent performance during peak times without
over-provisioning.

The SCALING_POLICY parameter can be configured to influence scale-out
behavior with STANDARD (default) and ECONOMY values. While STANDARD
suits most workloads, ECONOMY can conserve credits by establishing a
higher bar for spinning up new clusters, leading to increased queuing.
This tradeoff may be worthwhile for cost-optimized workloads.

Multi-cluster warehouses often provide better price-performance for
"bursty" workloads by elastically adjusting clusters. However, if
additional compute is required for complex individual queries,
increasing cluster size is more appropriate, as a single query executes
against a single cluster.

### Drive accountability via warehouse-level chargeback

In larger organizations with a single Snowflake account, workload isolation promotes accountability and effective administration. Virtual warehouses are often the dominant cost driver, so dedicating specific warehouses to business units provides a clear mechanism for internal chargeback. This drives cost control and empowers each team to manage their own compute usage. This simplifies governance, as each business unit can manage its dedicated warehouse with local control, minimizing the risk of one team's actions affecting another's workload. Always secure access to warehouses via an effective RBAC (Role-based access control) strategy to ensure only authorized users/roles/teams have access.

### Query Acceleration Service (and Scale Factor)

Enable [<u>Query
Acceleration</u>](https://docs.snowflake.com/en/user-guide/query-acceleration-service#evaluating-cost-and-performance)
on your warehouse to parallelize parts of qualifying queries, reducing
the need to over-provision for "outlier" queries with heavy table scans.
The **QUERY_ACCELERATION_MAX_SCALE_FACTOR** parameter defines the
supplemental compute available. While the default is eight, begin with a
lower value (even one) to validate its benefits before increasing it to
optimize price-performance.

### Implement strategies for handling concurrent queries

### Tune max concurrency level

For multi-cluster warehouses, fine-tune concurrency with the
MAX_CONCURRENCY_LEVEL parameter, which sets the maximum queries per
cluster. Reducing this value can benefit resource-intensive queries by
providing more compute power, potentially improving throughput by
minimizing concurrency overhead and optimizing resource utilization.

This parameter's "unit of measurement" is not strictly a query count,
but rather "full, cluster-wide queries." While no single query counts
for more than one unit, some, like stored procedure CALL statements,
count for less. A CALL statement, being a single control thread, uses
only a fraction of a cluster's "width," representing a fraction of a
unit. Thus, multiple CALL statements might aggregate into one unit,
meaning a MAX_CONCURRENCY_LEVEL of eight could support more than eight
concurrent CALL statements. Snowflake automatically manages these
calculations for optimized resource utilization.

While query concurrency can exceed MAX_CONCURRENCY_LEVEL due to lower
degrees of parallelism, fewer queries might be assigned to a cluster
before queueing due to memory budgeting. Each query has a memory metric
that determines if a cluster can accept it without exceeding its budget.
If exceeded, the query is not assigned. If no clusters are available,
the query queues, awaiting capacity. Larger or more complex queries
increase the memory metric, reducing net concurrency for warehouses
processing heavyweight queries.

This parameter also applies to single-cluster warehouses. Reducing its
value will cause queueing. Without a multi-cluster warehouse (MCW),
queries will wait for capacity to free up when others complete, rather
than a new cluster spinning up. However, for some scenarios, tuning this
value for a single-cluster warehouse may be appropriate.

### Stagger scheduled jobs

For predictable, high-concurrency workloads like scheduled batch jobs,
staggering their start times effectively avoids concurrency spikes,
allowing more efficient use of warehouse resources. This prevents jobs
from running simultaneously and competing for resources, mitigating the
negative impacts of concurrency spikes.

Since most jobs begin with scan-based activity (I/O), even slight
staggering of heavyweight queries can prevent "stampedes" that arise
from simultaneous dispatch. While Snowflake and cloud storage are highly
scalable, making staggering not a strict requirement, it is a best
practice for optimal resource utilization.

This principle also applies to concurrent queries dispatched from an
application. Introducing a slight delay, sometimes via a small random
offset for each query, provides similar benefits to staggering scheduled
jobs.

### Monitor for queuing

When queries queue on a warehouse, it's a signal that the warehouse
might be under-provisioned for the workload, and either a larger
warehouse size or a multi-cluster warehouse (with an increased maximum
cluster count) would be beneficial. You can use Snowflake's
[<u>QUERY_HISTORY</u>](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
view in the ACCOUNT_USAGE share to monitor query queuing and identify
concurrency issues. There are three queueing-related attributes in the
view:

- queued_provisioning_time

  - Warehouse start up (resume from suspended; less relevant here)

- queued_repair_time

  - Warehouse repair (less common; not relevant here)

- queued_overload_time

  - Query waiting for warehouse resources to free up (most relevant
    here)

When coupled with the following attributes that are also included in the
view:

- warehouse_id / warehouse_name

- warehouse_size

- start_time

- end_time

It is fairly straightforward to identify warehouses that require
additional compute resources, and also whether this is periodic or
sustained.

### Special considerations for concurrent stored procedures

Snowflake stored procedures, invoked via a CALL statement, coordinate
child SQL statements. The CALL statement itself uses minimal warehouse
resources, but child statements, executing as separate queries, can
fully utilize a warehouse cluster. By default, child statements run on
the same warehouse as the parent.

In environments with extensive stored procedure use and high CALL
statement concurrency, parent and child statements can intertwine on a
single warehouse. While lightweight parent statements are easily
assigned, high concurrency can lead to child statements queuing. A
parent statement cannot complete until all its children do. This can
cause a subtle deadlock: many parent statements wait for children, but
some children are blocked due to insufficient warehouse capacity.

To prevent this, isolate parent and child statements on different
warehouses. This is achieved by having the parent issue a USE WAREHOUSE
command before launching child statements. This simple strategy
effectively avoids deadlocks in high stored procedure concurrency.
Additionally, using two warehouses allows each to be optimally
configured for its specific purpose.

## Platform features
### Utilize Snowflake's serverless features

### Automatic Clustering Service

[<u>Automatic
clustering</u>](https://docs.snowflake.com/en/user-guide/tables-auto-reclustering)
in Snowflake is a background service that continuously manages data
reclustering for tables with a defined and enabled cluster key.
Clustering table data effectively, based on columns or expressions, is a
highly effective performance optimization. It directly supports pruning,
where specific micro-partitions are eliminated from a query's table
scan. This micro-partition elimination provides direct performance
benefits, as I/O operations, especially across a network to remote
storage, can be expensive. By clustering data to align with common
access paths, MIN-MAX ranges for columns become narrower, reducing the
number of micro-partitions scanned for a query.

[<u>Defining the correct cluster
key</u>](https://docs.snowflake.com/en/user-guide/tables-clustering-keys)
is crucial for achieving excellent query performance and optimizing
credit consumption. While the Automatic Clustering Service incurs credit
charges to maintain a table's clustering state, when implemented
correctly, overall credit consumption should be lower, often by an order
or two of magnitude, compared to not managing clustering. Best practices
for cluster key selection include:

- The order of expressions in a multi-part cluster key is crucial. The
  first expression, or "leading edge," has the greatest impact on
  clustering.

- Currently, Snowflake ignores any expressions beyond the fourth in a
  cluster key. Do not define a cluster key with more than four
  expressions.

- Even with four or fewer expressions, not all may affect clustering.
  Clustering co-locates rows into micro-partitions to achieve narrow
  MIN-MAX ranges. If the composite cluster key's cardinality exceeds the
  number of micro-partitions, further co-location is not possible.

- For activity-based tables that continually grow (e.g., sales, web
  clicks), a date/time-based leading edge is often effective. Unless
  older data is restated, micro-partitions stabilize quickly, reducing
  churn. This benefits Search Optimization, Materialized Views, Dynamic
  Tables, and Replication through reduced churn.

- If a column has high cardinality but is valuable as an access path,
  consider reducing its cardinality with a system function. Ensure the
  function maintains the original column's partial ordering, segmenting
  values into "buckets" that preserve relative order. To reduce the
  cardinality of:

  - A string (VARCHAR), use LEFT().

  - A timestamp, use TO_DATE to truncate to a DATE, or DATE_TRUNC for
    other units (HOUR, WEEK, MONTH, etc.).

  - An integer, use TRUNC(\<COL\>, \<BUCKETSIZE\>).

- For string expressions in a cluster key, Snowflake rarely considers
  more than five characters (never more than six). For multi-byte
  non-Latin characters, this can be as low as one. Therefore, COL_X as a
  cluster key expression is functionally equivalent to LEFT(COL_X, 5)
  for Latin characters. To consider more characters, stitch them
  together as multiple expressions, e.g., CLUSTER BY (LEFT(COL_X, 5),
  SUBSTR(COL_X, 6, 5)) for the first ten characters.

- Do not use functions like MOD, as they do not result in narrow MIN-MAX
  ranges. For example, MOD(COL, 10) treats 1, 11, and 100000001 as
  equivalent for clustering, but results in a very wide MIN-MAX range,
  significantly diminishing pruning effectiveness.

### Search Optimization (SO) Service

For highly selective queries on large tables, enable the [<u>Search
Optimization
Service</u>](https://docs.snowflake.com/en/user-guide/search-optimization-service).
This serverless feature creates a persistent data structure (index) for
efficient micro-partition pruning, significantly reducing scanned data
and improving query performance. It is effective for point lookups and
substring searches, even on semi-structured data.

Consider Search Optimization indexes when clustering alone doesn't meet
performance objectives. Search Optimization enhances pruning without
requiring narrow MIN-MAX ranges, using Bloom filters to identify
micro-partitions that do not contain matching rows.

Clustering often affects Search Optimization's effectiveness.
Establishing a cluster key before assessing Search Optimization's
pruning is often advantageous, as altering clustering can change pruning
effectiveness.

Search Optimization builds incrementally on registered micro-partitions.
An index may cover 0% to 100% of active micro-partitions. If a query is
issued with partial coverage, the index is leveraged for covered
micro-partitions, providing an additional pruning option beyond MIN-MAX
pruning. Uncovered micro-partitions miss this secondary pruning. Heavy
table churn can diminish Search Optimization's effectiveness, so
minimize unnecessary churn when the service is configured.

### Materialized View (MV) Service

For frequently-run queries with repeated subquery results, such as
complex aggregations, use a materialized view. The [<u>Materialized View
Service</u>](https://docs.snowflake.com/en/user-guide/views-materialized)
automatically refreshes the view when the underlying base table changes,
allowing subsequent queries to use pre-computed results for faster
performance.

Similar to Search Optimization, Materialized View maintenance is
incremental on active micro-partitions. If a table experiences extensive
micro-partition churn, performance benefits diminish. Queries
encountering non-covered micro-partitions revert to the base table,
impacting performance.

For MVs that aggregate data (via DISTINCT or GROUP BY), results are
stored per source micro-partition, requiring a query-time final
aggregation. This final aggregation is usually negligible, but if
significant, consider alternative data materialization via manual ETL or
Dynamic Tables, balancing data access and latency.

### Query Acceleration Service (QAS)

To speed up portions of a query workload on an existing warehouse,
enable the Query Acceleration Service. This service automatically
offloads parts of the query processing work, particularly large scans
with selective filters, to shared compute resources. It's ideal for ad
hoc analytics or workloads with unpredictable data volumes, as it
reduces the impact of resource-hungry "outlier queries" without needing
to manually scale up the entire warehouse.

It is important to understand that QAS is limited to a subset of
operation types within the processing of a query. Specifically, there
are two primary scenarios where QAS can be employed within a query
today:

- For a COPY INTO, it can participate in the entire operation for a
  subset of the source files that are being ingested. It can scan,
  transform, and write out rows.

- For SELECT and INSERT (including CTAS), QAS can only participate in
  the following operation types:

  - Table Scan

  - Transformation (computed columns)

  - Filter (predicate and join filters)

  - Aggregation (GROUP BY)

If any other operation type is encountered within a query execution
plan, QAS will share its partial result with the warehouse and will not
participate in that query any further. This includes (but is not limited
to):

- Join

- Sort

- Insert (write data to new micro-partitions)

### Serverless tasks

For scheduled, single-statement SQL or stored procedure-based workloads,
consider using serverless tasks instead of user-managed warehouses. With
serverless tasks, Snowflake automatically manages the compute resources,
dynamically allocating the optimal warehouse size for each run based on
past performance. This eliminates the need for manual warehouse sizing,
automates cost management, and ensures that your data pipelines run
efficiently without consuming credits when idle.

### Leverage Dynamic Tables for data engineering pipelines

### Improve downstream query performance

Dynamic Tables enhance query performance for downstream consumers by
materializing data. Unlike standard views, which re-execute their
underlying query each time they are called, Dynamic Tables pre-compute
and store query results, providing a periodically refreshed version of
the data. This means complex, performance-intensive queries, such as
those with multiple joins and aggregations, are computed once during the
refresh cycle, rather than every time the result is queried.

This significantly benefits applications like BI dashboards and embedded
analytics, where low latency is crucial. By directing these applications
to a fast-responding Dynamic Table instead of a complex view, end-user
queries become simple SELECT statements on pre-computed results. This
can substantially boost performance, as the query engine bypasses
transformation logic, leading to quicker query execution and a more
responsive analytical experience for many concurrent users.

As materialized tables, Dynamic Tables offer powerful performance
advantages similar to standard tables. They collect the same statistical
metadata automatically, and Snowflake's advanced query optimizations
apply when Dynamic Tables are the query source. Effectively, from a
query perspective, Dynamic Tables function as materialized standard
tables.

Additionally, Dynamic Tables are compatible with serverless features for
further performance enhancements. You can apply Automatic Clustering for
better partition pruning during data scanning. A Search Optimization
Service index can be built to accelerate scans for highly selective
filter criteria. Other serverless features, like Materialized Views and
the Query Acceleration Service, can also be layered on top of a Dynamic
Table for even greater optimization.

### Enhance organizational productivity

Dynamic Tables simplify data engineering by allowing you to define a
table's desired final state with a CREATE DYNAMIC TABLE AS SELECT...
statement, rather than complex MERGE or INSERT, UPDATE, DELETE commands.
This declarative approach removes the burden of managing incremental
logic, which is often error-prone.

Beyond initial pipeline creation, Dynamic Tables automate data
orchestration by intelligently performing full or incremental refreshes,
applying only necessary changes. This eliminates the need for manual
pipeline construction using STREAMS and TASKS, and facilitates chaining
Dynamic Tables for complex dependencies without external tools.

Administration and monitoring are also streamlined. Snowflake's
dedicated Snowsight graphical interface provides a visual representation
of your pipeline's status, refresh history, and dependencies,
simplifying troubleshooting and governance. This "single pane of glass"
identifies bottlenecks or failures quickly, replacing manual log
inspection or metadata queries.

Ultimately, Dynamic Tables' declarative syntax, automated refresh logic,
and integrated monitoring transform data engineering. You can configure
them to run on a set schedule or on-demand. By automating low-level
tasks, Dynamic Tables enable data teams to focus on building new data
products and driving business value, resulting in a more efficient and
agile data platform.

### [<u>Best practices for Dynamic Tables</u>](https://docs.snowflake.com/en/user-guide/dynamic-table-performance-guide)

**Simplify the core definition:** Avoid overly complex single Dynamic
Table definitions. For clarity and performance, it's a best practice to
keep the number of joined tables in a single definition to a minimum,
ideally no more than five. For more complex transformations, chain
multiple Dynamic Tables together, with each one building on the
previous.

**Leverage dependency chaining:** Use the DOWNSTREAM keyword to specify
dependencies between Dynamic Tables, which ensures that a dependent
table is only refreshed after its upstream source has been updated. This
also allows Snowflake to optimize processing by permitting refreshes on
a Dynamic Table to be deferred until it is required by a downstream
Dynamic Table.

**Set the TARGET_LAG parameter appropriately:** The [<u>TARGET_LAG</u>
<u>parameter</u>](https://docs.snowflake.com/en/user-guide/dynamic-tables-target-lag)
controls the maximum delay of the data in the Dynamic Table relative to
its source. It's crucial to set this value to the highest number that
still meets your business requirements. Setting a TARGET_LAG that is
lower than necessary can cause more frequent, less efficient refreshes,
which increases credit consumption and resource usage without providing
any tangible business benefit.

**Avoid high DML churn on source tables**

Excessive DML operations like UPDATE or DELETE on a source table can
significantly impact the performance of its dependent Dynamic Table.
This is because the underlying change data capture (CDC) mechanism has
to process a higher volume of changes, which requires more compute and
can lead to slower refresh times. Designing data pipelines to be
append-only when possible is a key best practice for maximizing
efficiency.

**Utilize the IMMUTABLE WHERE clause**

Use the **IMMUTABLE WHERE** clause in your Dynamic Table definition to
specify a predicate for immutable source data. This allows the refresh
service to avoid re-scanning historical data that is guaranteed not to
change, which can significantly improve the efficiency and performance
of incremental refreshes.

**Manage backfills with BACKFILL FROM clause**

To load historical data into a new Dynamic Table, or one that is
undergoing a change to its schema definition, use the BACKFILL FROM
parameter in the CREATE DYNAMIC TABLE syntax. This allows you to specify
a timestamp from which the initial refresh should begin, providing a
simple, declarative way to backfill the table with historical records.
It eliminates the need for manual, complex backfilling scripts.

**Right-size the refresh warehouse:** Ensure the warehouse specified for
the Dynamic Table refresh is appropriately sized for the workload. A
larger warehouse can process large refreshes more quickly, while a
smaller one may be more cost-effective for frequent, smaller incremental
updates.

**Monitor refresh history:** Regularly monitor the refresh history of
your Dynamic Tables using the DYNAMIC_TABLE_REFRESH_HISTORY view. This
provides insights into the refresh performance, latency, and costs,
allowing you to fine-tune your definitions and warehouse sizes for
continuous optimization.

## Monitor and optimize
### Implement continuous performance monitoring and optimization

### Overview

Establish comprehensive monitoring and logging to identify performance
bottlenecks. Proactively optimize the system by analyzing queries and
workloads to adapt to evolving requirements.

### Desired outcome

Effective performance monitoring and optimization yield a system with
predictable performance and stable costs, even as data and applications
evolve. This foundation supports future growth in data volume and query
activity, enabling better root cause analysis and cost management.

### Recommendations

Performance optimization often follows the 80/20 rule, where a minimal
investment can yield significant improvements. While definitive rules
are elusive due to diverse workloads, these recommendations establish a
foundation for a performant, cost-stable workload on the Snowflake
platform.

### Understand how Snowflake works

A technical understanding of the Snowflake architecture is crucial for
diagnosing performance issues and identifying optimization
opportunities. While most workloads perform well without deep expertise,
performance tuning requires a greater investment in understanding the
platform's fundamentals.

### Measure performance

Objective measurement is a prerequisite for meaningful optimization.
Without a clear and objective baseline, success cannot be defined,
leaving initiatives without direction.

### Identify bottlenecks

Focus optimization efforts on significant bottlenecks at the macro
(application), workload, or micro (query) level. Addressing
inconsequential components yields minimal overall improvement.

### Proactively optimize

Address performance proactively, not just reactively. Regular analysis
of performance patterns and slow queries can prevent emergencies.
Establishing a performance baseline is key to tracking trends and
determining if performance is improving or degrading over time.

### Thoroughly test performance optimizations

Predicting query performance is difficult; therefore, testing is
essential. Validate that changes improve the target workload without
negatively impacting others. Testing proves whether a proposed solution
has the desired effect.

### Meticulously validate AI suggestions

AI can be a useful tool, but suggestions require critical validation.
Test AI-driven recommendations thoroughly against platform knowledge and
reliable sources before implementation.

### Trade-offs & considerations 

#### Cost versus performance

The relationship between cost and performance is not linear. While some
optimizations increase cost, others can reduce it. For example, a query
that takes 10 minutes on an XS warehouse and spills to remote storage
might complete in one minute on a Small warehouse without spilling. In
this case, selecting a larger, more expensive warehouse results in a
faster, cheaper query execution.

#### Monitoring versus analysis

Snowflake's rich performance data favors targeted analysis over constant
monitoring. A proactive approach to reviewing and comparing performance
data is required. The optimal balance depends on workload criticality;
sensitive operations may benefit from continuous analysis, while stable
processes can rely on retrospective analysis.

#### Statistical rigor versus agility

Accurate performance insights require statistically sound metrics.
However, this rigor can slow down the optimization process. Balance the
need for statistically valid data with the need for agile
decision-making. Less rigorous measurements may suffice for initial
troubleshooting, with comprehensive testing reserved for validating
major changes.

### Factors impacting performance

Numerous factors can impact query and workload performance. This list is
a starting point for consideration.

- **Data volume**: Significant changes in data volume can impact
  performance, especially if a threshold is crossed that causes
  operations like remote spilling.

- **Data distribution**: Data value distribution affects micro-partition
  scanning and overall performance. Changes can alter query plans and
  the amount of data processed.

- **Data clustering**: Clustering, the physical grouping of data in
  micro-partitions, is critical. Poor clustering increases
  micro-partition scanning, degrading performance. Maintaining good
  clustering improves partition pruning.

- **Data model**: The logical data organization profoundly impacts
  performance. Poorly designed models can lead to inefficient query
  plans, while overly wide tables can also present challenges.

- **Query syntax**: The structure of a SQL query significantly affects
  its execution plan. Inefficient syntax, like poor JOIN conditions, can
  prevent the optimizer from choosing an efficient plan.

- **View definitions**: A view's underlying definition impacts the
  performance of queries that use it. A complex view can hide
  performance problems and introduce computational overhead with every
  execution.

- **Data share changes**: Changes to shared data, such as new columns or
  modified clustering keys, can impact consumer query performance.

- **Search Optimization changes**: The Search Optimization Service can
  accelerate point lookups. Adding or removing it can have a massive
  impact on the performance of applicable queries.

- **Use of Hybrid Tables**: Hybrid Tables blend OLTP and OLAP
  capabilities. Their performance characteristics for analytical queries
  may differ from standard tables, requiring specific workload
  considerations.

- **Warehouse characteristics**: Virtual warehouse configuration has a
  direct impact on performance. This includes:

  - Virtual warehouse size

  - Multi-Cluster Warehouse (MCW) settings

  - MAX_CONCURRENCY_LEVEL

  - Query Acceleration Service (QAS)

  - Snowpark-optimized warehouse settings

  - Warehouse generation (Gen1 vs. Gen2)

- **Caching**: Snowflake uses metadata, result set, and warehouse data
  caching. A valid cache hit accelerates query execution, while a cache
  miss can be slower.

- **Concurrency**: Multiple queries competing for resources can slow
  individual execution times. Proper warehouse sizing and MCW
  configuration can prevent concurrency bottlenecks.

- **Queuing due to load**: When a warehouse is at capacity, new queries
  are queued, increasing total execution time. This indicates a need for
  a larger warehouse or more clusters.

- **Queuing due to locks**: Locks ensure data integrity during DML
  operations. While minimal, lock contention can occur and must be
  resolved to maintain a responsive system.

- **Snowflake updates**: Regular platform updates, which often include
  performance enhancements, can occasionally alter query optimizer
  behavior and execution plans, potentially impacting specific
  workloads.

This list is not exhaustive, and some of these things are much more
likely than others.

## Measure performance
### Measuring performance

### Overview

Rigorous measurement is essential for achieving performance targets,
confirming improvements, and preventing performance issues. Snowflake
provides a wealth of performance data, which reduces the need for
constant monitoring. This data only gains meaning through consistent
review and comparative analysis.

### Desired outcome

Understanding current performance allows identification of anomalies and
their origins. It can also help understand how time spent within
Snowflake relates to other parts of an application or pipeline.

### Recommendations

A robust performance measurement strategy is built on a clear purpose, a
defined scope, and a consistent process for evaluating critical
workloads. These recommendations are essential to properly measuring
performance:

### Clarify reasons for measuring performance

Identifying the reason for measuring performance guides the effort and
time invested. The common reasons for measuring the performance of a
query or workload include establishing a baseline, comparing to a
baseline, troubleshooting, controlling costs, and understanding
contributions to Service Level Objectives (SLOs) or performance targets.

### Define measurement scope

Define the dimensions of the analysis. Pinpoint the object of
measurement, since performance in Snowflake can be evaluated at
different levels of granularity.

Understanding the granularity of performance measurement guides the
techniques and tools employed.

### Identify priority workloads and queries

The choice of what to measure depends on the reason for performance
analysis and the desired granularity. There are different considerations
for measuring single queries, workloads , and workloads with
concurrency. The overall goal is to focus effort where it will have the
most impact.

### Select metrics

Carefully choose and measure performance metrics in Snowflake to ensure
effective analysis.There are many valid metrics, including overall query
execution time, query cost, and metrics like files scanned. Statistical
significance is important in measuring performance.

### Define your measurement cadence

Establish a clear schedule and triggers for measuring performance.
Understanding when to measure performance allows for focused effort and
helps avoid over-reacting to perceived performance problems. The goal is
to provide a valid comparison point and understand the impact of various
factors on performance.

### Clarify reasons for measuring performance

### Overview

Establishing a clear reason for measuring performance from the outset is
paramount for understanding what data to examine and which strategic
directions to pursue.

### Desired outcome

Defining the "why" behind a performance initiative guides the level of
effort and ensures resources are directed to the most impactful areas.

### Recommendations

Common reasons for measuring the performance of a query or workload
include:

- **Establishing a baseline:** A baseline provides a reference point for
  comparing future changes or problems. This comparison helps determine
  the value of potential modifications and the importance of addressing
  an issue. It is crucial to gather metrics in a statistically sound
  manner to avoid skewed results from transitory differences.

  - **Query-Level baseline:** A single query is the simplest unit for a
    baseline. Measure a query along several dimensions and record the
    values for later comparison. Establishing a query-level baseline
    often involves accessing information already stored by Snowflake.
    Recording a timestamp and query ID for lookup in QUERY_HISTORY is
    often sufficient, though longer retention may require storing this
    data in a separate table. A baseline can be as simple as execution
    time and micro-partitions scanned, or more detailed using
    GET_QUERY_OPERATOR_STATS().

  - **Workload-level baseline:** A workload is a logical grouping of
    queries, often identified by query tags, user, or warehouse. Since
    the number of queries in a workload can change, a simple
    query-by-query analysis is often insufficient.

- **Comparing to a baseline:** Once established, a baseline is used to
  evaluate the impact of optimizations. When making changes, measure
  performance against the baseline to quantify the improvement. This can
  be applied to both individual queries and entire workloads.

- **Troubleshooting:** A primary reason to collect performance data is
  to make a query or workload faster. To quantify an improvement, one
  must first measure the initial performance. Understanding the scale of
  a performance problem helps determine the appropriate level of urgency
  and resource allocation. Without a baseline, it is impossible to
  determine if performance has degraded, or by how much.

- **Understanding contributions to SLOs:** The performance of a query or
  workload is often critical to a larger application or pipeline with a
  Service Level Objective (SLO). Understanding the contribution of each
  component is essential for overall performance improvement and for
  assessing the severity of any performance issues.

### Define measurement scope

### Overview

A successful performance measurement strategy begins with a clear
definition of the scope of the analysis. It is important to identify the
specific object of measurement, as performance in Snowflake can be
evaluated at several different levels of granularity.

### Desired outcome

The level of granularity chosen for performance measurement will guide
subsequent decisions, such as the appropriate measurement techniques.
This clarity is essential for directing performance tuning efforts in
the most effective way.

### Recommendations

Performance can be measured at various levels of granularity. The most
common granularities for performance measurement are:

- **Single query:** The performance of a single query is often a
  critical factor. A single query can be the most resource-intensive
  component of a pipeline or application, or it may be executed with
  such high frequency that its individual performance has a significant
  cumulative impact. Analyzing individual queries can also reveal
  patterns in performance or data modeling that can be applied to
  improve a broader set of queries. A focus on individual query
  performance is generally a necessary part of any effort to improve
  overall performance or reduce costs.

- **Workload:** In many cases, optimizing the performance of a single
  query is not enough. An improvement to one query can sometimes lead to
  a degradation in the performance of another. To achieve significant
  performance gains, it may be necessary to analyze the performance of
  all queries within a pipeline or application. A comprehensive approach
  to workload analysis, including the establishment of a baseline and a
  well-defined testing methodology, is essential for effective
  regression testing and overall performance improvement.

- **Concurrency:** Concurrency testing is a specialized area of testing
  that is most likely to be something that is needed for high
  concurrency and low latency applications. It is rare to engage in
  concurrency testing to simply reduce costs or in the pursuit of better
  metrics on paper. Concurrency testing generally involves using a
  third-party app, such as JMeter, to run queries in specific patterns.

### Concurrency testing anti-patterns

As mentioned above, there are many potential anti-patterns for
concurrency testing. Here are several to avoid:

- **Failing to simulate a realistic ramp-up:** Starting a concurrency
  test with a sudden, massive spike of concurrent queries rather than a
  gradual ramp-up. A sudden burst does not allow time for proper scaling
  at the virtual warehouse and the cloud services layer, unless those
  layers are specifically configured to handle bursting workloads. Such
  a pattern can trigger queuing and auto-scaling. This pattern may not
  be representative of how users naturally log on and begin their work
  throughout the day, and may have negative performance patterns that
  are not representative of a real workload.

- **Not validating the test environment:** Failing to ensure the testing
  environment (including data volume, data distribution, and data
  clustering) is a true representation of the production environment. A
  test run on a small, non-representative dataset may yield results that
  are not applicable to the real-world workload.

- **Failing to use separate warehouses for distinct workloads:** Lumping
  together disparate workloads—such as ETL and BI dashboards—on the same
  warehouse. This is an anti-pattern for performance in general, but in
  concurrency testing, it can skew results and hide the true bottlenecks
  for each workload type.

- **Using a single, large warehouse for all workloads:** Testing a mix
  of small, fast-running queries and large, resource-intensive queries
  on a single, oversized warehouse. This can lead to resource contention
  and queuing for the smaller queries, which could be handled more
  efficiently on a smaller, separate warehouse. It also wastes credits
  by over-provisioning for the smaller workloads.

- **Ignoring the multi-cluster warehouse's scaling policies:** Not
  understanding the difference between the "Standard" and "Economy"
  scaling policies. Testing with "Economy" can lead to high queuing as
  Snowflake attempts to fully utilize existing clusters before spinning
  up new ones, while a workload requiring low latency might need the
  "Standard" policy's more rapid scaling.

- **Using an un-representative test workload:** Simulating concurrency
  with a small, static set of queries that do not accurately reflect
  real-world user behavior. A good concurrency test needs a mix of query
  types, complexities, and data access patterns that mirror the
  production workload.

- **Overlooking the impact of caching:** Not accounting for the various
  cache layers in Snowflake (result, warehouse, and metadata cache). A
  poorly designed test may repeatedly hit the same cached result, giving
  a false impression of performance under load. A true concurrency test
  must be designed to invalidate the cache and simulate a realistic mix
  of cold and warm queries. Disabling the result set cache is a bad idea
  for concurrency testing - if the test is properly designed, the result
  set cache will be used appropriately.

- **Not establishing a baseline without concurrency:** Running a
  concurrency test without first measuring the performance of individual
  queries in isolation. Without this baseline, it is impossible to
  attribute performance degradation to concurrency versus other factors,
  like query complexity or data changes.

- **Treating Snowflake like an OLTP database:** For optimal performance
  in Snowflake, some level of denormalization is often advantageous.
  Grouping DML operations logically, rather than executing a large
  number of individual INSERT, UPDATE, DELETE, or MERGE operations that
  affect only a few rows, tends to be more cost-efficient and perform
  better.

### Identify priority workloads and queries

### Overview

After establishing the reason for performance analysis and the required
granularity [<u>of what you’re
measuring</u>](https://docs.google.com/document/d/1LDeFasziRlYL1Z5t9BqJ_MwhECtJHbRDKG5BNWUAuwU/edit?tab=t.l1pikt37o4sn),
the next step is to identify the specific workloads or queries that will
be the focus of the investigation.

### Desired outcome

Targeting performance measurements allows for the efficient allocation
of time and resources to the areas where they will have the most
significant impact.

### Recommendations

The selection of a query or workload for performance measurement may be
apparent based on the reason for measuring performance. However, if a
specific target has not yet been identified, the following
recommendations can help guide the selection process based on the chosen
level of granularity.

### Single query

Identifying a single query for performance analysis from a large volume
of queries requires a systematic approach. Queries can be prioritized
based on various dimensions, including:

- **Cost:** The most expensive queries in terms of resource consumption.

- **Expectations:** Queries that deviate from expected performance
  norms.

- **Criticality:** Queries that are essential to the functionality of an
  application, dashboard, or pipeline.

- **User impact:** Queries that directly affect the end-user experience.

- **Historical performance:** Queries that have been identified as
  problematic in the past.

- **Complexity:** Queries with a high degree of complexity.

- **Data access:** Queries that scan a large number of micro-partitions.

- **Performance variance:** Queries that exhibit a wide range of
  execution times.

It is important to focus on queries that are meaningful and relevant to
the overall performance goals. Analyzing random queries is unlikely to
yield significant improvements. The insights gained from optimizing a
single query can often be applied to other queries with similar
patterns.

The QUERY_HISTORY view in ACCOUNT_USAGE is a valuable resource for
identifying queries that meet specific criteria. Aggregating data on the
QUERY_PARAMETERIZED_HASH can help identify patterns across multiple
executions of a query with different parameters, which is a common
characteristic of workloads that support BI dashboards.

### Workload

The process of selecting a workload for performance analysis is similar
to that of selecting a single query. However, the decision is often
influenced by business-related factors, such as the impact of the
workload on a critical metric. A workload is typically chosen for
analysis because it is a source of user frustration or because it is
associated with high costs, rather than solely because of its technical
complexity.

A workload can be defined as a group of queries, and the criteria for
grouping can vary. Queries can be grouped by user, virtual warehouse, or
application. The use of query tags can be a helpful mechanism for
identifying and tracking the queries that constitute a specific workload
in QUERY_HISTORY and other monitoring tools.

### Concurrency

Concurrency testing is a specialized form of performance analysis that
is typically reserved for applications with high-concurrency and
low-latency requirements. It is not generally employed for the sole
purpose of cost reduction or for improving metrics that are not directly
related to concurrency. Concurrency testing usually involves the use of
third-party tools, such as JMeter, to simulate specific query patterns.

### Select metrics

### Overview

After deciding to measure performance, the next step is to determine
which metrics to use and how to apply them. Using inappropriate metrics
or applying them incorrectly can be counterproductive. A thoughtful and
deliberate approach to choosing and measuring metrics ensures a better
return on the time and effort invested in performance analysis.

### Recommendations

There are two main aspects to consider when selecting metrics for
performance measurement: what to measure and how to measure it. The
choices made will depend on the overall goals of the performance
analysis and the specific context of the measurement. It is crucial to
ensure that the measurement methodology is valid.

### What to measure

- **Query execution tTime:** The most common metric for analyzing the
  performance of a single query or a workload is its execution time. In
  Snowflake, it is generally not beneficial to focus on individual
  components of the execution time, such as compilation time, as a
  longer compilation time can sometimes result in a shorter overall
  execution time.

- **Query cost:** There is a nuanced relationship between performance
  and cost in Snowflake. A query that runs for 2 minutes on an X-Small
  warehouse may cost the same as the same query running for 1 minute on
  a Small warehouse. It is even possible for a query to be both faster
  and cheaper on a larger warehouse. Rigorous testing is essential to
  determine if changes that might seem to increase costs, such as using
  a larger warehouse or clustering a table, actually lead to a reduction
  in overall cost.

- **Files scanned and other metrics:** Other metrics should also be
  considered. For example, the number of files scanned can be a key
  performance indicator, especially when working with large datasets.
  Minimizing the amount of data that needs to be processed is often a
  crucial step in improving performance.

### How to measure

Once a metric has been selected, it is important to decide how to
measure it. A single execution of a query or workload is not a
sufficient basis for a reliable measurement due to the many variables
that can affect performance, such as warehouse startup times and cache
population. For a representative sample, it is recommended to run each
query or workload at least 10 times, preferably at different times of
the day and on different days. The results can then be aggregated to
provide a single, comparable number. Here are a few examples of common
aggregations:

- **Mean/average:** The average of a metric across multiple executions
  provides a good understanding of what to expect. While the average
  will not be the exact value for every execution, it is a simple and
  widely understood calculation that can be used to put performance in
  the context of a larger pipeline or application.

- **P90 or higher:** When meeting a Service Level Objective (SLO) is the
  primary goal, edge cases become more important. The 90th percentile
  (P90) can provide insight into what to expect when conditions are not
  ideal. This is particularly useful in concurrency testing but can also
  be applied to other types of performance analysis.

- **Sum across multiple executions:** The sum of a metric across
  multiple executions can be a useful way to incorporate both the
  expected performance and the variance into a single metric, although
  it does not provide an easy way to understand the performance in
  context.

### Performance metric anti-patterns

When measuring performance, it is important to avoid common pitfalls
that can lead to inaccurate conclusions.

- **Basing analysis on a single query execution** - Basing performance
  conclusions on a single execution of a query should be avoided, as
  this approach lacks statistical significance. Numerous transient
  factors can cause a single execution to run unusually fast or slow,
  leading to flawed assumptions based on a best-case or worst-case
  scenario rather than on a representative performance sample.

- **Focusing on isolated execution phases** - Avoid focusing on isolated
  components of query execution, such as compilation time. A longer
  compilation phase can sometimes result in a more optimized execution
  plan and a shorter total execution time. The primary metric for
  analysis should be the total elapsed time for the query, not the
  duration of its individual phases.

### Define your measurement cadence

### Overview

While there are often specific motivations for measuring performance,
such as investigating a reported issue, establishing a regular cadence
for performance measurement is a critical practice. Even basic
measurements, like recording a timestamp and query ID, become more
valuable when collected as part of a structured approach.

### Desired Outcome

A well-defined cadence for performance measurement allows for the
focused allocation of time and effort, ensuring that performance
analysis is conducted when it is most impactful.

### Recommendations

Performance should be measured at several key moments to ensure a
comprehensive understanding of the system's behavior. The following
catalysts and cadences are recommended:

- **Establish a baseline:** A performance baseline provides a reference
  point for all future comparisons. Without a baseline, it is difficult
  to objectively determine if performance has degraded, or to quantify
  the severity of a performance issue. A defined measurement
  methodology, combined with a baseline, allows for a straightforward
  comparison to identify and assess performance problems.

- **Before and after significant changes**: It is important to validate
  or re-establish a performance baseline before any significant change,
  such as an application upgrade, a data model alteration, or a
  substantial data change. This ensures a recent and valid point of
  comparison. Following the change, performance should be measured again
  to assess the impact and to establish a new baseline for future
  analysis.

- **Testing potential changes:** Snowflake's table cloning capabilities
  provide an efficient and cost-effective way to test the impact of
  potential changes. This is particularly useful for regression testing,
  where the goal is to determine if a change will negatively affect
  performance before it is implemented in production.

- **On a periodic interval:** Regular performance checks are valuable
  even in the absence of known issues. Periodic measurement can help
  identify gradual performance degradation caused by changes in data or
  other subtle factors within an application or pipeline. For workloads
  with annual peak periods, it may be beneficial to retain performance
  data, such as that found in QUERY_HISTORY, for longer than the
  standard retention period to allow for year-over-year comparisons.

### Identifying bottlenecks

### Overview

Identifying performance bottlenecks is a critical step in any
optimization process. To ensure that time and resources are used
effectively, it is essential to focus on the parts of a query or
workload where improvements will have the most significant impact on
overall performance metrics.

### Recommendations

A multi-faceted approach is recommended for identifying performance
bottlenecks. It's best to begin with a holistic understanding of the
application's context to focus optimization efforts where they will have
the most impact. Analysis can then be performed at two levels using
Snowflake's native tools.

### Tools for query-level analysis

For granular analysis of individual queries, several tools provide
detailed insights into the execution plan and performance
characteristics.

- **Query profile:** The <span class="mark">query profile</span> offers
  a detailed visual representation of a query's execution. It is the
  primary tool for identifying common issues such as poor
  micro-partition pruning, join explosions, remote spilling, and the
  specific operators consuming the most resources. The profile displays
  actual execution statistics after a query has completed (or a partial
  view while it is running) but is not accessible programmatically. Data
  is available for 14 days.

- **GET_QUERY_OPERATOR_STATS():** For programmatic access to the data
  found in the query profile, use the
  [<span class="mark"><u>GET_QUERY_OPERATOR_STATS()</u></span>](https://docs.snowflake.com/en/sql-reference/functions/get_query_operator_stats)
  function. This table function returns detailed, operator-level
  statistics in a structured format, making it ideal for automated
  analysis or for capturing performance data for long-term storage and
  comparison.

- **EXPLAIN:** The
  [<u>EXPLAIN</u>](https://docs.snowflake.com/en/sql-reference/sql/explain)
  command provides a look at a query's logical execution plan *before*
  it runs. It is useful for understanding the optimizer's choices but
  should be treated as an estimate, as it does not contain the actual
  run-time statistics available in the query profile.

### Tools for workload-level analysis

Analyzing performance across an entire workload requires a broader
perspective. The following ACCOUNT_USAGE views are invaluable for
identifying trends and high-impact queries.

- **QUERY_HISTORY:** The [<u>QUERY_HISTORY</u>
  <u>view</u>](https://docs.snowflake.com/en/sql-reference/account-usage/query_history)
  is the foundational tool for workload analysis. It contains a
  comprehensive record of executed queries, allowing for the
  identification of performance patterns. It is particularly useful for:

  - Finding queries with specific characteristics, such as long queue
    times (queued_overload_time).

  - Comparing workload performance against a baseline, especially when
    using query tags for easy filtering.

  - Aggregating metrics for queries that have the same structure but
    different literal values, using the query_parameterized_hash.

- **Specialized views:**

  - [<u>AGGERGATE_QUERY_HISTORY</u>](https://docs.snowflake.com/en/sql-reference/account-usage/aggregate_query_history):
    This view is comparable to QUERY_HISTORY when using hybrid tables.

  - [<u>QUERY_ATTRIBUTION_HISTORY</u>](https://docs.snowflake.com/en/sql-reference/account-usage/query_attribution_history)**:**
    This view is designed to provide a more accurate picture of the
    compute cost of a query, taking concurrency into account. It is
    excellent when the primary concern is attributing costs to specific
    queries or workloads.

  - [<u>QUERY_INSIGHTS</u>](https://docs.snowflake.com/en/sql-reference/account-usage/query_insights)**:**
    This view proactively identifies queries that match known
    performance anti-patterns. It can help pinpoint queries to
    investigate, but it is important to note that not every insight
    requires immediate action. See [<u>the documentation for details on
    the types of insights currently available and what they
    mean</u>](https://docs.snowflake.com/en/user-guide/query-insights).

  - [<u>TABLE_QUERY_PRUNING_HISTORY</u>](https://docs.snowflake.com/sql-reference/account-usage/table_query_pruning_history)
    and
    [<u>COLUMN_QUERY_PRUNING_HISTORY</u>](https://docs.snowflake.com/sql-reference/account-usage/table_query_pruning_history)**:**
    These views provide targeted data on micro-partition pruning
    effectiveness. Analyzing this data can help identify tables that may
    benefit from a clustering key. See [<u>Tim Sander’s article on using
    the pruning history
    views</u>](https://medium.com/snowflake/supercharging-snowflake-pruning-using-new-account-usage-views-52530b24bf2e)
    for more information.

## Responsible AI usage
### Meticulously validating AI suggestions

### Overview

AI can be a source of suggestions for performance improvement. However,
all suggestions require critical evaluation and comprehensive testing
before implementation. An unverified recommendation can waste time and
credits or even degrade performance.

### Recommendations

- **Apply foundational knowledge** Evaluate AI suggestions against a
  foundational understanding of the Snowflake platform. For complex or
  costly recommendations, consult the Snowflake documentation, conduct
  further research, or engage with Snowflake staff like Sales Engineers,
  Solutions Architects, and if appropriate, Technical Support.

- **Consider data timeliness** AI training data can be months or years
  old, failing to reflect Snowflake's rapid evolution. A suggestion
  might be correct based on old information but suboptimal given new
  features.

- **Test thoroughly** Performance improvements involve time and cost.
  Thoroughly test all suggestions in a controlled environment to verify
  they meet business requirements. Proper validation prevents unexpected
  issues, saving resources and improving outcomes.

### Conclusion

A strong understanding of the Snowflake platform provides the necessary
context to assess whether an AI suggestion warrants further
investigation and testing.

For additional information, see [<u>Optimizing performance in
Snowflake</u>](https://docs.snowflake.com/en/guides-overview-performance)
