author: Well Architected Framework Team
id: well-architected-framework-reliability
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: The Reliability Pillar focuses on ensuring a workload performs its intended function correctly and consistently, recovering from failures to meet business and regulatory demands. 
environments: web
status: Published 




# Reliability 
## Overview

The Reliability Pillar focuses on ensuring a workload performs its
intended function correctly and consistently, recovering from failures
to meet business and regulatory demands. This involves architecting for
high availability and fault tolerance, ensuring the resiliency of both
the service and the data itself, and operationalizing plans for business
continuity and disaster recovery. The goal is to build a data platform
that is optimally designed to recover from failure and also meet
fluctuating demand.

## Principles

### Ensure data is trustworthy and correct

> Reliability in the AI Data Cloud is ultimately defined by the
> trustworthiness of the data itself. This principle prioritizes data
> quality, integrity, and correctness as the ultimate measure of a
> reliable system, because business decisions depend on accurate and
> complete data.

### Design systems to anticipate and withstand failure

> A reliable system is designed with the assumption that failures will
> occur. This principle involves building for high availability, fault
> tolerance, and resiliency at every layer, from data storage,
> ingestion, and transformation pipelines, to AI and BI workloads, to
> minimize the impact of disruptions.

### Automate recovery and operations to reduce human error

> Manual processes are a common source of failure and slow down
> recovery. This principle advocates for automating operational tasks,
> recovery procedures, and change management to ensure consistent,
> repeatable, and rapid responses to both planned and unplanned events.

### Continuously test and validate recovery procedures

> A recovery plan is only reliable if it is proven to work. This
> principle mandates the regular testing of business continuity and
> disaster recovery plans through drills and simulations, ensuring that
> both the technology and the operational procedures are effective when
> a real incident occurs.

### Clearly define and operationalize shared responsibilities

> Reliability is a shared effort between the cloud provider, Snowflake,
> and the customer. This principle emphasizes the importance of
> understanding, documenting, and operationalizing the specific
> responsibilities at each layer to ensure there are no gaps in
> ownership for achieving end-to-end reliability.

## Recommendations

The following key recommendations are covered within each principle of
Reliability:

- **Reliability Strategy & Governance**

  - Shared Responsibility Model

  - SLA & Regulatory Compliance

  - Inherited Controls

  - Resource Monitoring & Quotas

  - Immutable Snapshots (WORM) & Archival Storage

- **High Availability & Fault Tolerance**

  - Availability Zones

  - Lifecycle Management (Version Upgrades & Planned Downtime)

  - Automatic Query Retries

  - Error Handling

- **Data & Object Resiliency**

  - Data Resiliency (Streams, Tasks, Database, Stored Procedure, UDF,
    Policy, Object Tag Replication)

  - Account Object Resiliency (Roles, Users, Warehouse, Resource Monitor
    Replication)

  - Time Travel

  - Fail-safe

  - Snowsight Objects (Notebooks & Worksheets)

  - Data Recovery

- **Resilient Data Pipelines**

  - Pipeline Object Replication (Snowpipe, Stages, File Formats)

  - Idempotent Pipeline Integration (External Volume, Multi-location
    Storage/Notification)

  - Load History Replication

  - Exactly Once Delivery without Data Loss

- **Monitoring & Operations**

  - Monitoring, Alerting & Observability

  - Resource Monitoring & Quotas

  - Business Continuity Planning & Testing

- **Disaster Recovery**

  - Replication & Failover Groups

  - Client Redirect

  - Failover Commands (UI & SQL)

  - Backup & Replication

## Reliability strategy & governance

### Overview

Reliability Strategy & Governance establishes the foundational framework
for making informed decisions about your data platform's resilience. It
involves defining *clear responsibilities*, setting *measurable
reliability targets*, and aligning technical architecture with business,
financial, and regulatory requirements. This strategic planning ensures
that all subsequent reliability efforts are purposeful and directly
support your organization's goals.

### Desired outcome

By implementing a sound reliability strategy and governance model, your
organization achieves clear alignment between business objectives,
technical capabilities, and financial investments. This proactive
approach reduces operational and regulatory risk, ensures predictable
performance, and fosters a culture of shared ownership for reliability
across teams. You can confidently claim that your reliability posture is
not merely a technical function but a strategic capability, governed by
clear policies and designed to meet specific business, financial, and
compliance mandates.

### Recommendations

**Shared Responsibility Model**

The Shared Responsibility Model is a framework that delineates the
distinct reliability duties between the cloud provider (e.g., AWS,
Azure, GCP), Snowflake, and you, the customer. Its importance lies in
creating clarity and preventing gaps in ownership, ensuring that every
aspect of reliability—from physical data center security to the code in
your data pipelines—is explicitly accounted for. We recommend you
formally document and socialize this model within your organization,
mapping specific internal roles and teams to the responsibilities
designated to the customer. This ensures clear accountability for tasks
such as data governance, workload management, and business continuity
planning.

**SLA & regulatory compliance**

This involves understanding both your contractual uptime commitments via
the Snowflake Service Level Agreement (SLA) and the mandatory legal and
industry regulations that govern your data, such as DORA for financial
services or HIPAA for healthcare. A key aspect of this is leveraging the
platform's agility to support flexible SLAs for different Lines of
Business (LoB). Not all workloads share the same criticality;
Snowflake's architecture allows you to apply stringent,
high-availability configurations and replication strategies only to the
most critical LoBs, while using more cost-effective approaches for less
critical workloads. Adherence across all levels is critical to avoid
significant financial penalties, operational disruption, and
reputational damage. We recommend you review
(the[/en/legal/](/en/legal/)),
identify all applicable regulations, and map these requirements to
specific Snowflake features and operational procedures to create an
auditable compliance trail that reflects the unique needs of each
business unit.

**Inherited controls**

This allows you to leverage Snowflake's existing third-party
certifications, such as HITRUST or FedRAMP, to accelerate your own
compliance and audit processes. This is a powerful advantage, as it
significantly reduces the time, cost, and effort required to demonstrate
that your data platform meets stringent security and reliability
standards. We recommend you engage your compliance and security teams to
review the reports available on the [https://trust.snowflake.com/](https://trust.snowflake.com/)
You should use the HITRUST Shared Responsibility Matrix to formally
document which controls you inherit from Snowflake, streamlining your
audit preparations and demonstrating due diligence.

**Resource monitoring & quotas**

While Snowflake provides virtually unlimited and readily available
compute, its consumption must be governed to ensure platform
reliability. Resource Monitors are a critical governance control for
managing credit consumption by setting quotas on virtual warehouses and
the account as a whole. Their importance to reliability is profound:
they act as a crucial safety net to prevent runaway queries or
misconfigured workloads from exhausting compute resources, which could
otherwise lead to performance degradation or service disruptions for
critical business processes. We recommend you assign a Resource Monitor
to all production virtual warehouses with clearly defined credit quotas.
You should configure these monitors to send notifications at various
consumption thresholds and to automatically suspend the warehouse if the
quota is exceeded, thereby protecting your critical workloads and
ensuring predictable platform performance.

**Immutable snapshots (WORM) & archival storage**

This area addresses the need to meet strict regulatory requirements for
data retention and legal holds, where data must be stored in a
non-erasable, non-rewritable format (Write-Once, Read-Many, or WORM).
While Snowflake's native Time Travel and Fail-safe features provide
powerful short-term data protection, certain regulations require
longer-term, provably immutable storage. For data subject to these
stringent requirements, we recommend leverage Snowflake Snapshots to
periodically create immutable backups of your tables, schemas and
databases.. This process should be documented thoroughly to provide a
clear audit trail for regulatory bodies.

### How-To’s

**Implement the Shared Responsibility Model:**

1.  Download and review the
    [whitepaper](/en/resources/report/snowflake-shared-responsibility-model/).

2.  Create a RACI (Responsible, Accountable, Consulted, Informed) chart
    that maps your internal teams (e.g., Data Engineering, Security,
    Finance, Application Owners) to each of the "Customer"
    responsibilities.

3.  Incorporate this chart into your team onboarding and operational
    runbooks.

**Set up Demand Management Controls:**

1.  Use the CREATE RESOURCE MONITOR command to establish credit quotas
    for warehouses or the entire account.

2.  Configure the monitor to trigger notifications or suspend warehouses
    at specific consumption thresholds (e.g., NOTIFY AT 75 PERCENT,
    SUSPEND_IMMEDIATE AT 95 PERCENT).

**Perform Basic Capacity Planning:**

1.  Execute queries against the
    SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY view to analyze
    credit consumption over time.

2.  Identify daily, weekly, or monthly peak usage patterns to inform
    warehouse sizing and scaling policy decisions.

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
implementing a comprehensive reliability strategy and governance model:

- **Stakeholder alignment:** Have you identified and engaged key
  stakeholders from business, finance, and technology to contribute to
  the reliability strategy?

- **Business requirements:** Have you conducted a Business Impact
  Analysis to define clear availability and recovery targets (SLOs, RTO,
  RPO) for your critical workloads?

- **Regulatory landscape:** Have you identified and documented all
  industry-specific and geographical regulations (e.g., DORA, HIPAA,
  GDPR) that apply to your data?

- **FinOps maturity:** Does your organization have a defined FinOps team
  or function responsible for cloud financial management and cost
  governance?

- **Ownership:** Have you assigned clear ownership for each of the
  customer responsibilities outlined in the Shared Responsibility Model?

## High availability & fault tolerance

### Overview

High Availability (HA) and Fault Tolerance are the architectural
cornerstones that ensure your data platform remains operational and
accessible, even in the face of component failures or planned
maintenance. This involves leveraging Snowflake’s inherently resilient
architecture, which is distributed across multiple availability zones,
and designing workloads that can gracefully handle transient errors. A
well-architected system minimizes downtime and provides a consistent,
reliable experience for your users and applications.

### Desired outcome

By implementing best practices for High Availability and Fault
Tolerance, your organization achieves continuous operations for its
critical data workloads, enhancing user trust and business productivity.
This design philosophy protects your business processes from localized
infrastructure failures, transient network issues, and planned platform
updates, ensuring consistent and predictable performance. After
implementing these recommendations, you can claim that your data
platform is architected for continuous availability, providing a
resilient foundation for your data-driven applications.

### Recommendations

**Availability Zones**

Snowflake’s architecture is natively designed for high availability by
distributing its service across three independent Availability Zones
(AZs) within a cloud provider's region. This built-in redundancy is
fundamental to the platform's resilience, as it ensures that the failure
of a single data center does not impact the availability of your data or
the service as a whole. We recommend you rely on Snowflake’s intrinsic
multi-AZ architecture for intra-region high availability, as this fault
tolerance is managed automatically without requiring any customer
configuration. For workloads that require an even higher level of
availability beyond a single region, you should complement this native
HA with a multi-region or multi-cloud disaster recovery strategy.

**Lifecycle management (version upgrades & planned downtime)**

Snowflake manages platform updates through a process of weekly,
non-disruptive releases, which are deployed transparently with zero
downtime for your workloads. This approach is critical for maintaining a
high-availability posture, as it eliminates the need for
customer-managed maintenance windows that would otherwise interrupt
service. We recommend you leverage Snowflake's zero-downtime upgrades
for your production accounts to ensure continuous operations. For
customers with Enterprise Edition or higher, we advise designating
non-production accounts for [early access to new
releases](https://docs.snowflake.com/en/user-guide/intro-releases#early-access-to-full-releases)
to test for potential impacts on critical workloads before the
production rollout.

**Automatic query retries**

The Snowflake platform is designed to be fault-tolerant by automatically
retrying certain query failures that occur due to transient,
intermittent issues within the service, such as a temporary network
failure or a faulty compute instance. This built-in mechanism is
important because it transparently handles temporary platform failures,
preventing them from becoming user-facing errors and improving the
overall reliability of your workloads. We recommend you rely on the
native automatic query retry feature to handle transient platform
issues, which simplifies your application logic. For custom data
pipelines, you should supplement this by implementing your own retry
logic for failures outside the scope of automatic retries, such as using
the RETRY LAST option for a failed task graph.

**Error handling**

Robust error handling involves designing a centralized framework to
capture, log, and manage exceptions from all workloads, not just data
loading. This is crucial for creating observable and resilient systems,
as it provides a single source of truth for identifying, analyzing, and
responding to failures from any process, including data pipelines,
stored procedures, or UDFs. We recommend you implement a standardized
error logging pattern, such as writing exceptions to a dedicated event
table. This approach ensures that all failures are captured
consistently, enabling automated alerting and providing a comprehensive
audit trail for root-cause analysis and remediation.

### How-To’s

**Verify Your Snowflake Release:**

1.  To check the current release version of your account, execute the
    following SQL command: SELECT CURRENT_VERSION();

2.  Review the monthly behavior change logs to stay informed of upcoming
    updates.

**Implement Centralized Error Handling:**

1.  Create a standardized event table to log errors from various
    sources: CREATE OR REPLACE TABLE my_event_table (event_timestamp
    TIMESTAMP_LTZ, error_source VARCHAR, error_code VARCHAR,
    error_message VARCHAR);

2.  Within your custom procedures or data pipelines, use a TRY...CATCH
    block to log exceptions to this central table before re-throwing the
    error.

3.  Set up a Snowflake Alert to monitor the event table for new entries
    and trigger a notification, enabling proactive response to any
    failure in your system.

**Retry a Failed Task Graph:**

1.  If a root task in a dependency tree fails, you can restart the run
    from the point of failure.

2.  Execute the following command, which will only re-run the failed
    task and any of its downstream children: EXECUTE TASK my_root_task
    RETRY LAST;

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
High Availability and Fault Tolerance:

- **Regional failure planning:** Have you confirmed that your business
  continuity plan addresses inter-region failure, given that
  intra-region HA is handled by Snowflake?

- **Change management:** Do you have a process to review Snowflake's
  monthly behavior change logs to proactively identify potential impacts
  on your workloads?

- **Application logic:** Are your custom applications and ETL/ELT tools
  prepared to handle non-transient errors that are not automatically
  retried by Snowflake?

- **Data quality feedback loop:** Do you have an automated process for
  reviewing, remediating, and reporting on records that were skipped or
  rejected during data loading?

## Data & object resiliency

### Overview

Data and Object Resiliency provides critical safeguards against logical
data corruption, accidental deletion, or unauthorized changes, ensuring
the integrity of your data and the stability of your operational
environment. This involves leveraging native Snowflake features like
Time Travel for instant point-in-time recovery and object replication to
protect both your data and the account configurations that govern it.
The goal is to enable rapid, granular recovery from common operational
failures without invoking a full disaster recovery plan.

### Desired outcome

By implementing a robust Data and Object Resiliency strategy, your
organization significantly reduces the risk and impact of common
operational failures, such as human error or application bugs. This
ensures the integrity of your critical data assets and the stability of
your governance and security posture, allowing you to confidently meet
operational recovery objectives and minimize data-related incidents.
After implementing these recommendations, you can claim that your data
platform is resilient to logical corruption and that you can restore
both data and critical account configurations to a known good state in
minutes.

### Recommendations

**Data resiliency (Streams & Tasks replication)**

Data Resiliency focuses on replicating not just the data but also the
database-level objects that give it context and automate its lifecycle.
This is paramount because a replicated database is of limited use if the
automated pipelines that populate it or the governance policies that
protect it are missing upon recovery. We recommend that a failover group
always include schemas containing policy and pipeline objects - such as
Streams, Tasks, and UDFs - to ensure that your data automation and
governance logic is synchronized with your data, providing a complete
and functional replica that can be activated quickly.

**Account [object
resiliency](https://docs.snowflake.com/en/user-guide/data-time-travel)
(roles & users replication)**

Use **failover groups** to replicate databases **and** account objects
like users, roles, warehouses with point‑in‑time consistency.This is
crucial for operational continuity, as your security framework (roles
and users) and compute configurations (warehouses) are essential to
making your data accessible and usable after a failover. We recommend
you replicate all critical account-level objects to your secondary
account using an FailoverGroup to ensure your security posture and
operational configurations are available immediately, preventing delays
and security gaps during a recovery event.

**Time Travel**

Snowflake [Time
Travel](https://docs.snowflake.com/en/user-guide/data-time-travel)
allows you to access historical versions of table data at any point
within a defined retention period, which can be configured for up to 90
days. This feature is your first and fastest line of defense against
logical data corruption, such as accidental UPDATE or DELETE statements,
as it enables instant, surgical recovery without restoring from
traditional backups. We recommend you configure an appropriate
DATA_RETENTION_TIME_IN_DAYS for all critical production tables,
balancing your recovery needs with storage costs, and leverage the
extended 90-day retention available in Enterprise Edition for your most
critical data assets.

**Fail-safe**

Fail-safe provides a non-configurable, 7-day data recovery period that
begins immediately after the Time Travel retention period ends. It is a
last-resort recovery service, managed by Snowflake, designed to protect
against catastrophic data loss from extreme operational failures. We
recommend you rely on Fail-safe as a final safety net and not as part of
your standard operational recovery procedures. Understand that recovery
from Fail-safe is initiated via Snowflake Support; your primary and most
immediate recovery tool should always be Time Travel.

**Data recovery**

Data recovery is the practice of restoring data after an incident, which
in Snowflake primarily involves using UNDROP commands or querying
historical data via Time Travel. Having a clear, documented, and tested
process for these actions is essential to executing them quickly and
correctly during a high-stress incident. We recommend you develop and
document specific operational runbooks for common data recovery
scenarios, such as restoring a dropped table using UNDROP or correcting
a faulty data load using Time Travel's AT \| BEFORE clause, and
regularly test these procedures.

### How-To’s

**Use Time Travel to Correct an Error:**

1.  Identify the query ID of the erroneous DML statement from the query
    history.

2.  Re-insert the correct data by querying the table from a point in
    time before the error occurred: INSERT INTO my_table SELECT \* FROM
    my_table BEFORE(STATEMENT =\> '\<query_id_of_bad_dml\>');

**Restore a Dropped Object:**

1.  To restore a recently dropped table, simply execute the
    [UNDROP
    command](https://docs.snowflake.com/en/sql-reference/sql/undrop-table):
    UNDROP TABLE my_table;

2.  This command also works for schemas and databases.

**Configure Extended Data Retention:**

1.  For critical production databases, set the Time Travel window to its
    maximum value (requires Enterprise Edition or higher).

2.  Execute the command: ALTER DATABASE my_prod_db SET
    DATA_RETENTION_TIME_IN_DAYS = 90;

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
Data and Object Resiliency:

- **Data retention policy:** Have you defined the required data
  retention period for each critical table based on business
  requirements and balanced it against storage costs?

- **Object replication scope:** Have you identified all critical account
  and database objects (including roles, users, tasks, and policies)
  that need to be included in replication groups?

- **Recovery runbooks:** Are your operational runbooks for common
  recovery scenarios (e.g., UNDROP, Time Travel query) documented,
  accessible, and regularly tested?

- **Table type strategy:** Have you evaluated the use of TRANSIENT
  tables for staging data to optimize storage costs by opting out of
  Fail-safe protection? Furthermore, have you considered using TEMPORARY
  tables for session-specific, intermediate data that requires no
  recovery whatsoever, providing an additional layer of cost and
  performance optimization?

## Resilient data pipelines

### Overview

Resilient Data Pipelines are the automated processes that reliably move
and transform data from source to destination, engineered to withstand
and recover from failures. This involves architecting for idempotency,
ensuring end-to-end data integrity, and replicating the pipeline's
components and state. The goal is to create a robust, self-healing data
flow that consistently delivers timely and accurate data for analysis.

### Desired outcome

By implementing resilient data pipelines, your organization builds trust
in its data delivery systems, reduces operational overhead, and
accelerates time-to-insight. This ensures that your data pipelines are
not brittle, but are robust systems that can automatically recover from
transient errors, prevent data duplication, and guarantee data
correctness. After implementing these recommendations, you can claim
that your data lifecycle is managed by a reliable, automated, and
fault-tolerant framework that consistently delivers high-quality data to
the business.

### Recommendations

**Pipeline object replication (Snowpipe, stages, file formats)**

Pipeline Object Replication involves replicating the configuration and
metadata of data ingestion components—such as Snowpipes, external and
internal stages, and file formats—to a secondary account. This is
critical for business continuity because a replicated database is of
limited value if the mechanisms to load new data into it are unavailable
after a failover. We recommend you include all production Snowpipe,
Stage, and File Format objects in your replication groups alongside
their target databases to ensure a fully functional and ready-to-use
data ingestion capability in your secondary account. Furthermore, you
should periodically validate that the required permissions are granted
on these replicated objects to prevent access issues post-failover.

**Idempotent pipeline integration**

An idempotent pipeline is one where re-running an operation multiple
times with the same input produces the same result, preventing data
duplication or corruption. This architectural principle is paramount for
building reliable, self-healing pipelines, as it allows you to safely
retry failed jobs without introducing data integrity issues. We
recommend you design all data loading and transformation logic to be
idempotent, for example by using MERGE statements instead of simple
INSERT statements. For streaming data, you should leverage features that
provide exactly-once semantics to ensure each event is processed
precisely one time.

**Load history replication**

Load History Replication specifically replicates the metadata of files
ingested via Snowpipe to a secondary account. This is a crucial, yet
often overlooked, component of a resilient data pipeline, as it prevents
the re-ingestion of already-processed files after a failover. Without
this history, a Snowpipe in a newly promoted primary account would
re-process all existing files in a stage, leading to significant data
duplication. Load History is automatically replicated as part of the
database that is being replicated in a failover group.

**Exactly once delivery without data loss**

Achieving exactly-once delivery is the gold standard for critical data
pipelines, guaranteeing that every record is processed precisely one
time, even in the face of failures and retries. This ensures the highest
level of data integrity by preventing both data loss and data
duplication, which is non-negotiable for financial reporting, regulatory
compliance, and other sensitive use cases. We recommend you combine
idempotent DML logic, transactional controls, and robust error handling
to architect pipelines that achieve exactly-once semantics. For
real-time ingestion, we advise using [Snowpipe
Streaming](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-overview),
which is designed to provide these guarantees out of the box.

### How-To’s

**Add a Pipe to a failover group:**

1.  Identify the database and schema containing the pipe you wish to
    replicate.

2.  Use the ALTER FAILOVER GROUP command to add the pipe's parent
    objects to the group: ALTER FAILOVER GROUP my_fg ADD
    my_db.my_schema.my_pipe TO REPLICATION_SCHEDULE;

**Write an Idempotent
[MERGE](https://docs.snowflake.com/en/sql-reference/sql/merge)
statement:**

1.  Use a MERGE statement to either insert new rows or update existing
    rows based on a unique key, preventing duplicates on re-run.

2.  Example: MERGE INTO target t USING source s ON t.id = s.id WHEN
    MATCHED THEN UPDATE SET t.value = s.value WHEN NOT MATCHED THEN
    INSERT (id, value) VALUES (s.id, s.value);

**Check Snowpipe load history:**

1.  To validate that files have been loaded and to check for errors,
    query the
    [COPY_HISTORY](https://docs.snowflake.com/en/sql-reference/functions/copy_history)
    function.

2.  Example: SELECT \* FROM
    TABLE(INFORMATION_SCHEMA.COPY_HISTORY(TABLE_NAME=\>'my_table',
    START_TIME=\>DATEADD(hours, -1, CURRENT_TIMESTAMP())));

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
building resilient data pipelines:

- **Pipeline inventory:** Have you identified and inventoried all
  critical data pipelines and their constituent objects (pipes, stages,
  tasks, streams) that need to be made resilient?

- **Idempotency review:** Have you audited your existing ETL/ELT scripts
  to ensure they are idempotent and will not cause data duplication if
  retried?

- **Error handling strategy:** Do you have a defined process for
  handling files or records that consistently fail to load (a
  "dead-letter queue" strategy) to prevent them from blocking the entire
  pipeline?

- **Dependency mapping:** For complex, multi-step pipelines using Tasks,
  have you mapped all dependencies to ensure they are replicated and
  will execute in the correct order after a failover?

## Monitoring & operations

### Overview

Monitoring and Operations is the practice of maintaining the health,
performance, and reliability of your data platform in production. It
involves establishing comprehensive observability into system behavior,
implementing proactive controls to manage resource consumption, and
operationalizing your business continuity plans through rigorous
testing. A mature operational posture enables you to move from a
reactive to a proactive state, identifying and mitigating issues before
they impact the business.

### Desired outcome

By implementing a robust Monitoring and Operations strategy, your
organization achieves a state of proactive control over its data
platform, leading to increased stability, predictable performance, and
optimized costs. This approach minimizes the frequency and duration of
service disruptions, ensures that recovery plans are effective, and
provides the necessary visibility to manage resources efficiently. After
implementing these recommendations, you can claim that your data
platform is actively managed, fully observable, and that your
organization is prepared to execute its business continuity plans with
confidence.

### Recommendations

**Monitoring, alerting & observability**

This practice involves gaining deep insights into the health and
performance of your Snowflake environment. While monitoring tells you
*what* is happening, observability helps you understand *why* it's
happening, enabling rapid root-cause analysis. This is critical for
proactively detecting anomalies, performance degradation, or data
pipeline failures. We recommend you leverage the SNOWFLAKE.ACCOUNT_USAGE
schema for historical analysis of query performance and credit
consumption, and implement [Snowflake
Alerts](https://docs.snowflake.com/en/guides-overview-alerts) to
trigger timely, automated notifications for specific conditions,
ensuring your operations team is alerted to potential issues promptly.

**Resource monitoring & quotas**

Resource Monitors are a critical governance control for managing credit
consumption by setting quotas on virtual warehouses and the account as a
whole. Their importance lies in preventing unexpected cost overruns from
runaway queries or misconfigured workloads and ensuring that compute
resources are available for your most critical business processes. We
recommend you assign a
[resource-monitor](https://docs.snowflake.com/en/user-guide/resource-monitors)
to all production virtual warehouses with clearly defined credit quotas
that align with your FinOps budgets. You should configure these monitors
to send notifications at various consumption thresholds and to
automatically suspend the warehouse if the quota is exceeded, thereby
providing a crucial safety net for cost control and resource management.

**Business Continuity planning & testing**

A [Business
Continuity](https://docs.snowflake.com/en/user-guide/business-continuity-disaster-recovery)
plan is a documented strategy outlining how your organization will
maintain critical functions during and after a disruption. However, a
plan is only reliable if it is regularly tested. This practice is
essential for validating your technical recovery procedures, building
operational "muscle memory," and uncovering gaps in your strategy before
a real incident occurs. We recommend you formalize your Business
Continuity and Disaster Recovery (BCDR) plans in accessible operational
runbooks. Crucially, you must establish a regular cadence for conducting
DR drills—such as executing a failover of a non-production
environment—to test your procedures, validate your RTO/RPO targets, and
ensure your operations team is prepared to respond effectively.

### How-To’s

**Create a resource monitor:**

1.  Use the CREATE RESOURCE MONITOR command to define a credit quota and
    notification thresholds.

2.  Example: CREATE RESOURCE MONITOR my_monitor WITH CREDIT_QUOTA = 1000
    TRIGGERS ON 75 PERCENT DO NOTIFY ON 90 PERCENT DO SUSPEND ON 100
    PERCENT DO SUSPEND_IMMEDIATE;

3.  Assign the monitor to a warehouse: ALTER WAREHOUSE my_wh SET
    RESOURCE_MONITOR = my_monitor;

**Set up a Snowflake Alert:**

1.  Create an alert that checks for a specific condition on a schedule.

2.  Example: CREATE OR REPLACE ALERT long_running_query_alert WAREHOUSE
    = my_ops_wh SCHEDULE = '5 MINUTE' IF (EXISTS (SELECT 1 FROM
    SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY WHERE EXECUTION_STATUS =
    'RUNNING' AND START_TIME \< DATEADD(hour, -1, CURRENT_TIMESTAMP())))
    THEN CALL SYSTEM\$SEND_EMAIL(...)

3.  Resume the alert to activate it: ALTER ALERT
    long_running_query_alert RESUME;

**Check for failed Tasks:**

1.  To monitor the operational health of your data pipelines, query the
    TASK_HISTORY function.

2.  Example: SELECT \* FROM
    TABLE(INFORMATION_SCHEMA.TASK_HISTORY(SCHEDULED_TIME_RANGE_START=\>DATEADD('hour',-1,CURRENT_TIMESTAMP()),
    RESULT_LIMIT =\> 100)) WHERE STATE = 'FAILED';

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
implementing a mature Monitoring and Operations practice:

- **Observability strategy:** Do you have a centralized dashboard for
  monitoring key reliability metrics (e.g., query performance, warehouse
  utilization, data loading errors)?

- **Alerting channels:** Are your alert notification channels (e.g.,
  email, PagerDuty) configured and integrated with Snowflake?

- **Quota alignment:** Are your resource monitor quotas aligned with
  your departmental budgets and FinOps strategy?

- **BCDR documentation:** Is your Business Continuity plan documented,
  accessible, and regularly reviewed by all relevant stakeholders?

- **Testing cadence:** Have you defined and committed to a schedule for
  conducting regular DR tests and "game day" exercises?

## Disaster Recovery

### Overview

Disaster Recovery (DR) is a critical component of a comprehensive
reliability strategy, focused on restoring data and service in the event
of a large-scale failure. Snowflake provides a multi-layered approach to
DR, ensuring comprehensive protection is readily available. This begins
with automatic **Cross-Zone** recovery, where the platform transparently
handles an availability zone outage at no additional cost. For broader
incidents, customers can implement **Cross-Region** DR to fail over to
another region, or even **Cross-Cloud** DR to fail over to an entirely
different cloud provider for the highest level of resilience. A
well-architected DR plan leverages these capabilities to minimize data
loss and downtime, ensuring business continuity for your most critical
workloads. For a detailed overview of the concepts and features
involved, refer to Snowflake’s documentation on [business continuity
and disaster
recovery](https://docs.snowflake.com/en/user-guide/replication-intro).

### Desired outcome

By implementing a robust Disaster Recovery (DR) strategy, your
organization ensures business continuity for critical data workloads,
protecting against regional outages and minimizing data loss. This
allows you to confidently meet stringent Recovery Time Objectives (RTO)
and Recovery Point Objectives (RPO), maintain customer trust, and uphold
regulatory obligations even in the face of a major disruption. After
implementing these recommendations, you can claim that your data
platform is resilient and your business is prepared for catastrophic
failures, with a tested and reliable plan to restore service.

### Recommendations

**Failover groups**

Failover groups are the foundational Snowflake concept for implementing
a robust DR strategy. They allow you to group databases and critical
account objects—such as users, roles, and resource monitors—and
replicate them as a single, consistent unit to a secondary account in
another region or cloud. This is paramount for ensuring that not just
your data, but your entire operational environment, can be recovered
with point-in-time consistency after a disaster, thereby minimizing both
data loss (RPO) and recovery time (RTO). We recommend you group critical
databases and their associated account objects into Failover Groups to
ensure they are replicated and failed over together, maintaining both
transactional and operational integrity. Furthermore, you should
configure a frequent replication schedule for these groups, aligned with
your business requirements, to minimize your RPO.

**Client Redirect**

[Client
Redirect](https://docs.snowflake.com/en/user-guide/business-continuity-client-redirect)
is a feature that provides seamless, automated failover for your
applications and users. It works via a connection object that
automatically reroutes client application traffic from a primary account
to a secondary account after a failover has been initiated, without
requiring manual changes to connection strings. This feature The
importance of this feature cannot be overstated, as it dramatically
simplifies the recovery process and reduces your RTO by eliminating the
complex and error-prone task of reconfiguring every client application
during an outage. To leverage this capability, we recommend you
implement a connection object with Client Redirect enabled for all
production applications. It is also critical to ensure that all client
applications are configured to use the single connection URL provided by
this object, rather than direct account URLs, to guarantee the automated
redirection is effective.

**Failover commands (UI & SQL)**

Executing a disaster recovery plan is ultimately controlled by specific
failover commands, which are available through both the Snowsight UI and
SQL. These commands are used to promote a secondary failover group to
become the primary, thereby formally initiating the failover process.
Having a clear, well-understood, and tested procedure for using these
commands is critical for a swift and successful recovery during a
high-stress incident. We recommend you document the exact SQL failover
commands (e.g., ALTER FAILover GROUP... PRIMARY) in your operational
runbooks and grant the necessary privileges to a limited set of
authorized personnel to prevent accidental activation. Additionally,
your operations team should be familiarized with both the UI-based and
SQL-based failover procedures as part of your regular DR testing to
ensure they can execute them efficiently under pressure.

**Backup & replication**

A comprehensive [data
protection](https://docs.snowflake.com/en/user-guide/data-cdp)
strategy must address both large-scale disasters and more common
operational failures. This is achieved by combining physical replication
for disaster recovery with logical backups for operational recovery.
While cross-region replication is essential for surviving a regional
outage, it is not a substitute for protecting against human error or
data corruption. Snowflake’s architecture provides powerful tools for
both scenarios. We recommend you complement your cross-region
replication strategy with a regular, automated process for creating
zero-copy clones of critical databases. These clones serve as highly
efficient, point-in-time logical backups that can be used for rapid
operational recovery, development, and testing without incurring
significant storage costs. You can alternatively leverage Snowflake
Snapshots to periodically create and expire immutable backups. Finally,
you must verify that your backup and replication processes preserve your
Role-Based Access Control (RBAC) and governance policies to ensure
security and compliance are maintained post-recovery.

### How-To’s

**Implement Failover Groups:**

1.  Identify critical databases and account objects (users, roles,
    warehouses, etc.) required for business continuity.

2.  Create a FAILOVER GROUP in your primary account that includes these
    objects.

3.  Create a secondary FAILOVER GROUP in your DR account as a replica
    and set a refresh schedule (e.g., REPLICATION_SCHEDULE = '10
    MINUTE').

**Configure Client Redirect:**

1.  Create a CONNECTION object in your primary account.

2.  Enable CLIENT_REDIRECT for that connection object.

3.  Update all client application connection strings to use the new
    connection URL (e.g.,
    \<organization_name\>-\<connection_name\>.snowflakecomputing.com).

**Establish logical backup procedures:**

1.  Identify critical tables or databases that require frequent,
    point-in-time backups for operational recovery.

2.  Create a Snowflake Task to automatically execute a CREATE TABLE...
    CLONE statement on a defined schedule (e.g., daily).

3.  Implement a data retention policy for these clones to manage storage
    costs.

## Tradeoffs & Considerations

Use the following checklist to assess your organization's readiness for
implementing a disaster recovery strategy:

- **Business impact analysis:** Have you identified your most critical
  data workloads and quantified the business impact of an outage?

- **RTO/RPO definition:** Have you defined and documented the Recovery
  Time Objective (RTO) and Recovery Point Objective (RPO) for each
  critical workload?

- **DR site selection:** Is your secondary Snowflake account located in
  a separate geographic region or on a different cloud provider to
  protect against large-scale failures?

- **Testing cadence:** Have you established a regular cadence for
  conducting DR drills to test your failover procedures and validate
  your RTO/RPO targets?

- **Runbook availability:** Are your DR plans, including specific
  failover commands and personnel contact information, documented in an
  accessible operational runbook?
