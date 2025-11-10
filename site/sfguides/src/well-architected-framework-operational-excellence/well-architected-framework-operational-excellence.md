author: Well Architected Framework Team
id: well-architected-framework-operational-excellence
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: Operational Excellence in the Snowflake AI Data Cloud is the practice of running and monitoring systems to deliver business value and continuously improve supporting processes and procedures. 
environments: web
status: Published 


# Operational Excellence

## Overview

Operational Excellence in the Snowflake AI Data Cloud is the practice of
running and monitoring systems to deliver business value and
continuously improve supporting processes and procedures. It focuses on
maximizing automation, gaining deep observability into workloads, and
establishing a culture of iterative improvement. This empowers your
organization to innovate faster with data engineering, analytics, AI,
applications, and collaboration, all while managing risk and optimizing
for cost and performance.

This pillar emphasizes aligning technology with business outcomes to
support the transformations Snowflake enables. Each Operational
Excellence principle follows a phase-based structure to reflect an
iterative approach:

- Prepare

- Implement

- Operate

- Improve

## Principles

#### Ensure operational readiness & performance

> Proactively define performance targets (SLOs), test and validate
> capacity, and continuously optimize compute engines to ensure
> workloads meet business expectations.

#### Automate infrastructure & maintenance

> Eliminate manual operational tasks by codifying all infrastructure,
> configuration, and data pipelines, leveraging Snowflake's built-in
> automation for scaling and maintenance.

#### Enhance observability & issue resolution

> Gain deep, end-to-end visibility into the platform by capturing and
> analyzing telemetry, logs, and traces to rapidly diagnose and resolve
> issues.

#### Manage incidents & problems

> Minimize the impact of incidents using AI-driven diagnostics,
> immutable backups for rapid recovery, and automated governance
> controls.

#### Enable collaboration & Secure Sharing

> Foster a collaborative data culture by establishing a secure, governed
> internal marketplace for sharing data, applications, and models.

#### Manage the AI/ML software development lifecycle

> Implement a governed, end-to-end MLOps framework to manage models and
> features, from experimentation and fine-tuning to deployment and
> monitoring, directly within the data cloud.

#### Continuously improve performance & practices

> Proactively define performance targets (SLOs), test and validate
> capacity, and continuously optimize compute engines to ensure
> workloads meet business expectations.

## Ensure operational readiness & performance

### Overview

Ensuring operational readiness and performance in the Snowflake AI Data
Cloud is about creating a stable, efficient, and scalable environment
that consistently meets your business objectives. This involves
proactively planning for capacity, monitoring system health, optimizing
query performance, and implementing robust processes for management and
support. A well-performing and operationally sound platform builds
trust, drives user adoption, and maximizes the return on your data
investment. It ensures that your data engineering pipelines run on
schedule, analytical queries return quickly, AI models are trained and
deployed efficiently, and data applications deliver a seamless user
experience.

### Focus areas

To achieve peak performance and operational excellence in Snowflake,
concentrate on four key areas that directly impact your workloads.

- **Workload management & optimization:** This involves configuring
  virtual warehouses to match specific workload demands (e.g.,
  separating data loading from BI queries), implementing dynamic scaling
  policies to handle fluctuations in demand, and continuously analyzing
  query performance to identify and resolve bottlenecks. For AI
  workloads, this means providing sufficient compute for model training
  without disrupting other business-critical analytics.

- **Capacity & cost management:** This area focuses on forecasting
  future needs based on usage patterns and business growth. It includes
  establishing budgets, setting alerts for cost anomalies using resource
  monitors, and employing strategies like query optimization and
  choosing the right warehouse size to manage consumption effectively.
  The goal is to ensure you have the resources you need without
  unnecessary expense.

- **Monitoring, logging, & alerting:** A comprehensive monitoring
  strategy is crucial for proactive management. This involves leveraging
  Snowflake's native monitoring capabilities (e.g., Snowsight
  dashboards, QUERY_HISTORY view) and integrating with third-party
  tools. Key activities include tracking credit consumption, monitoring
  query queues and latency, and setting up automated alerts for
  performance degradation, security events, or system errors to enable a
  rapid response from your SRE and engineering teams.

- **Business Continuity & Disaster Recovery (BCDR):** This ensures your
  data and operations are resilient. It involves defining Recovery Time
  Objectives (RTO) and Recovery Point Objectives (RPO) for critical
  workloads. Key practices include leveraging Snowflake's cross-region
  data replication and failover/failback features to protect against
  regional outages and implementing regular testing of your BCDR plan to
  ensure its effectiveness.

### Phase-based activities

#### Prepare

In this initial phase, the focus is on planning and design to build a
foundation for operational excellence.

- **Define Service Level Objectives (SLOs):** Work with business
  stakeholders to define and document clear performance targets for key
  workloads. For example, specify the maximum acceptable latency for an
  executive dashboard (Analytics) or the required completion time for a
  critical data ingestion pipeline (Data Engineering). Build in the
  training and learning plans to enable personas to function at high
  effectiveness.

- **Establish warehouse strategy:** Design a multi-warehouse strategy
  that isolates workloads to prevent resource contention. For instance,
  create separate virtual warehouses for data loading (ETL/ELT), BI
  tools, data science experimentation (AI), and customer-facing
  applications (Applications).

- **Plan for monitoring:** Identify key performance indicators (KPIs) to
  monitor, such as query latency, queueing time, credit consumption, and
  storage growth. Select the monitoring tools (native Snowflake or
  third-party) and define the alerting strategy.

- **Design BCDR Plan:** Determine RTO/RPO requirements for different
  datasets and workloads. Based on these, design a replication and
  failover strategy using Snowflake's features.

#### Implement

During implementation, you will build and configure the Snowflake
environment based on the designs from the Prepare phase.

- **Configure virtual warehouses:** Create the virtual warehouses
  defined in your strategy, setting appropriate sizes (e.g., X-Small for
  ad-hoc queries, Large for data transformation jobs) and auto-scaling
  policies.

- **Set up resource monitors:** Implement resource monitors to control
  costs and prevent unexpected warehouse usage. Configure monitors to
  suspend warehouses or send notifications when credit consumption
  reaches a predefined threshold.

- **Implement monitoring & alerting:** Configure Snowsight dashboards or
  integrate with external tools like Datadog or Grafana to visualize
  KPIs. Set up automated alerts for long-running queries, failed tasks,
  or cost spikes.

- **Configure data replication:** For BCDR, set up account replication
  for your primary databases to a secondary Snowflake region.

#### Operate

The Operate phase focuses on the day-to-day management and maintenance
of the Snowflake environment.

- **Proactive monitoring:** SRE and Engineering teams continuously
  monitor dashboards and respond to alerts. They actively look for
  performance degradation, resource contention, and signs of system
  stress.

- **Query performance tuning:** Regularly review query history to
  identify inefficient or long-running queries. Use the Query Profile to
  diagnose bottlenecks (e.g., table scans, "exploding" joins) and work
  with developers to optimize SQL code.

- **Cost management:** Review daily and monthly credit consumption
  against budgets. Analyze usage patterns to identify opportunities for
  cost savings, such as shutting down idle warehouses or resizing
  underutilized ones.

- **Execute BCDR drills:** Periodically conduct failover tests to ensure
  the disaster recovery plan works as expected and that the team is
  prepared to execute it.

#### Improve

This phase is about continuous improvement through analysis, learning,
and refinement.

- **Conduct performance reviews:** Hold regular (e.g., quarterly)
  reviews of workload performance against the established SLOs. Analyze
  trends in query performance and resource utilization. Feed persona
  knowledge gaps back into the training and development program.

- **Refine warehouse configuration:** Based on usage data, adjust
  warehouse sizes, scaling policies, and workload assignments. For
  example, if a data science warehouse is consistently underutilized,
  consider downsizing it or merging it with another non-critical
  workload.

- **Optimize data structures:** Analyze query patterns to identify
  opportunities for performance gains through data modeling
  improvements, such as implementing clustering keys on large tables to
  improve query pruning.

- **Update BCDR Plan:** Incorporate lessons learned from BCDR drills and
  evolving business requirements into the disaster recovery plan.

### Recommendations

Here are the key recommendations focused specifically on ensuring
operational readiness and performance for your Snowflake environment.

#### Isolate workloads to guarantee performance

Your top priority for predictable performance is to prevent different
jobs from competing for the same resources. A heavy data science task
should never slow down a critical business dashboard.

**Workload isolation** ensures that each process gets the compute it
needs without interference.

- **For Architects and Engineering Leads:** Define a clear warehouse
  strategy by categorizing your workloads (e.g., INGESTION,
  TRANSFORMATION, ANALYTICS, DATA_SCIENCE). Mandate this separation as a
  core design principle.

- **For Engineers and SREs:** Create distinct virtual warehouses for
  each category. Use Snowflake's **Role-Based Access Control (RBAC)** to
  enforce this strategy. For example, grant your ETL tool's service role
  USAGE permission *only* on the INGESTION_WH. This simple step makes it
  impossible for an ingestion process to impact analytics performance.

For additional information, review the best practices in [Virtual
Warehouse
Considerations](https://docs.snowflake.com/en/user-guide/warehouses-considerations).

#### Continuously tune warehouse size for optimal performance

Choosing the right warehouse size is a balancing act. Too small, and
queries will run slowly or fail; too large, and you're wasting
resources. The key is to use data, not guesswork, to find the sweet
spot.

- **For Developers (Engineering & Data Science):** When building a new
  job, **start with a small warehouse** (X-SMALL or SMALL). After a test
  run, immediately open the **Query Profile** in Snowsight. Look for
  significant time spent on **"Local or Remote Disk I/O."** This is
  called "spilling," and it's a clear sign the warehouse is too small
  for the data it's processing. Test with the next size up until
  spilling is minimal.

- **For SREs:** Proactively monitor for performance issues. Query the
  SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_LOAD_HISTORY view to find warehouses
  with high AVG_RUNNING and AVG_QUEUED_LOAD times. This data points you
  directly to overloaded warehouses that are creating bottlenecks.

Learn to diagnose bottlenecks using the [Query
Profile](https://docs.snowflake.com/en/user-guide/ui-query-profile)
and monitor load with the views in [Monitoring Warehouse
Load](https://docs.snowflake.com/en/user-guide/warehouses-monitor-load).

#### Automate monitoring and alerting

You can't achieve operational readiness by manually checking dashboards.
You need an automated system that alerts you to problems *before* your
users report them.

- **For SRE and Operations teams:**

  1.  **Identify critical scenarios:** Define what constitutes a
      problem, such as a data loading task failing, a query running
      longer than 30 minutes, or a sudden spike in warehouse queuing.

  2.  **Build detection with Snowflake Tasks:** Write SQL queries
      against the SNOWFLAKE.ACCOUNT_USAGE views (like QUERY_HISTORY and
      TASK_HISTORY) to detect these scenarios.

  3.  **Schedule the queries to run automatically** using a CREATE TASK
      statement. For instance, a task can run every five minutes to look
      for failed tasks.

  4.  **Trigger alerts:** From the task, use an **External Function** to
      send a notification directly to your team's incident management
      tool, like PagerDuty or Slack.

Build your automated alert system by following the guide [Introduction to
Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro).

#### Validate your recovery plan with regular drills

An untested disaster recovery (BCDR) plan is just a theory. Operational
readiness means having a proven, practiced process to restore service
after a major incident.

- **For Architects and SREs:** Schedule and lead BCDR drills at least
  twice a year. After providing notice to stakeholders, initiate the
  failover using a single command: ALTER DATABASE my_db ENABLE FAILover
  TO ACCOUNT my_secondary_account;.

- **For Application and Engineering Teams:** Actively participate in the
  drill. Once the failover is complete, connect your applications and
  tools to Snowflake (the connection URL doesn't change) and run a
  pre-written script to validate data integrity and system
  functionality. Your feedback is crucial for refining the recovery
  process. This "muscle memory" ensures your team can execute flawlessly
  during a real emergency.

Find the specific commands and procedures in the guide for [Database
Replication and
Failover/Failback](https://docs.snowflake.com/en/user-guide/account-replication-intro).

### Persona responsibilities (RACI chart)

The table below outlines the roles and responsibilities for ensuring
operational readiness and performance.

**Legend:** **R** - Responsible, **A** - Accountable, **C** - Consulted,
**I** - Informed

| Activity | C-Level (CIO/CDO/CFO) | Chief Enterprise Architect | Engineering | Data Science | Security | SRE |
|---|---|---|---|---|---|---|
| Define business SLOs & budgets | A | R | I | I | I | I |
| Design warehouse strategy | I | A | R | C | I | R |
| Implement & configure warehouses | I | C | A | I | I | R |
| Monitor cost & performance | I | I | R | I | I | A |
| Optimize queries & pipelines | I | C | A | R | I | C |
| Define & test BCDR plan | A | R | R | C | C | R |
| Respond to performance incidents | I | I | R | I | I | A |

## Automate infrastructure & maintenance

### Overview

Automating infrastructure and maintenance is crucial for achieving
efficiency, consistency, and scalability in the Snowflake AI Data Cloud.
Because Snowflake is a fully managed service, automation efforts focus
less on provisioning underlying servers and more on managing the
configuration, workloads, and ecosystem surrounding your data. This
framework provides principles and best practices for automating the
setup, deployment, and operation of your Snowflake environment to
support data engineering, analytics, AI, and application workloads
reliably and at scale.

### Focus areas

To effectively automate your Snowflake environment, concentrate on four
key areas. These areas provide a structured approach to managing your
data ecosystem programmatically, reducing manual effort and minimizing
human error.

- **Infrastructure as Code (IaC):** This is the practice of managing and
  provisioning your Snowflake environment through machine-readable
  definition files rather than manual setup. This includes creating and
  managing databases, schemas, warehouses, roles, users, and resource
  monitors declaratively. This ensures environments are consistent,
  repeatable, and version-controlled.

- **CI/CD for data & applications:** Continuous Integration and
  Continuous Deployment (CI/CD) automates the build, test, and
  deployment of your data pipelines and applications. For Snowflake,
  this means automating the deployment of SQL scripts, dbt models,
  Snowpark jobs (Python, Java, Scala), AI/ML models, and Snowflake
  Native Apps. This practice accelerates development cycles and improves
  the reliability of changes.

- **Observability & monitoring automation:** This involves automatically
  collecting, analyzing, and acting upon telemetry data from Snowflake.
  This includes tracking query performance, credit consumption, storage
  costs, and security access patterns. Automated monitoring provides
  proactive insights into the health, performance, and cost of your
  workloads, triggering alerts or optimization routines.

- **Automated governance & security:** This area focuses on
  programmatically enforcing your security and governance policies. It
  includes automating user and role provisioning (Role-Based Access
  Control - RBAC), applying data masking policies, monitoring for
  compliance deviations, and managing network policies and integrations.
  Automation ensures that security is consistently applied and auditable
  across the platform.

### Phase-based activities

Adopting automation is a journey. The following activities are organized
by phase to provide a clear roadmap from initial preparation to
continuous improvement, aligned with our defined focus areas.

### Prepare

The **Prepare** phase is about planning and laying the foundation for
successful automation.

| Focus Area | Activities |
|---|---|
| Infrastructure as Code (IaC) | - Evaluate and select an IaC tool (e.g., Terraform, Schemachange).<br>- Define and document naming conventions and standards for all Snowflake objects.<br>- Establish a Git repository structure for managing your IaC configurations. |
| CI/CD for data & applications | - Choose CI/CD tools (e.g., GitHub Actions, Jenkins, GitLab CI) that integrate with your code repositories.<br>- Define a branching and deployment strategy (e.g., GitFlow) for promoting changes from development to production. |
| Observability & monitoring | - Identify key metrics for cost, performance, and security that need to be tracked. Evaluate tools for collecting and visualizing data from the Snowflake `ACCOUNT_USAGE` schema.<br>- Define initial alert thresholds for critical events like high credit usage or long-running queries. |
| Automated governance | - Define your RBAC model and map business roles to Snowflake roles.<br>- Document your data classification standards and corresponding security controls (e.g., masking policies for PII). |


### Implement

The Implement phase involves the initial build-out and rollout of your
automation scripts and pipelines.

| Focus Area | Activities |
|---|---|
| Infrastructure as Code (IaC) | - Evaluate and select an IaC tool (e.g., Terraform, Schemachange).<br>- Define and document naming conventions and standards for all Snowflake objects.<br>- Establish a Git repository structure for managing your IaC configurations. |
| CI/CD for data & applications | - Choose CI/CD tools (e.g., GitHub Actions, Jenkins, GitLab CI) that integrate with your code repositories.<br>- Define a branching and deployment strategy (e.g., GitFlow) for promoting changes from development to production. |
| Observability & monitoring | - Identify key metrics for cost, performance, and security that need to be tracked. Evaluate tools for collecting and visualizing data from the Snowflake `ACCOUNT_USAGE` schema.<br>- Define initial alert thresholds for critical events like high credit usage or long-running queries. |
| Automated governance | - Define your RBAC model and map business roles to Snowflake roles.<br>- Document your data classification standards and corresponding security controls (e.g., masking policies for PII). |

### Operate

The Operate phase focuses on using and managing your automated systems
for day-to-day activities.

| Focus Area | Activities |
|---|---|
| Infrastructure as Code (IaC) | - Develop initial IaC modules to manage core objects: roles, users, warehouses, and databases.<br>- Create a sandbox environment entirely provisioned through your IaC scripts to validate the process. |
| CI/CD for data & applications | - Build a starter CI/CD pipeline for a single data engineering (e.g., dbt) or Snowpark project.<br>- This pipeline should automate code linting, unit testing, and deployment to a development environment. |
| Observability & monitoring | - Develop scripts or configure tools to automatically pull data from `ACCOUNT_USAGE` into a monitoring dashboard.<br>- Configure basic automated alerts for budget overruns (via resource monitors) and warehouse contention. |
| Automated governance | - Write scripts to provision your defined RBAC model in Snowflake.<br>- Implement initial dynamic data masking policies on a non-production table containing sensitive data. |


### Improve

The Improve phase is about refining and optimizing your automation to
increase efficiency and capability.

| Focus Area | Activities |
|---|---|
| Infrastructure as Code (IaC) | - Refactor IaC modules for greater reusability and simplicity.<br>- Implement automated validation and policy-as-code checks (e.g., ensuring all warehouses have auto-suspend enabled) before applying changes. |
| CI/CD for data & applications | - Optimize pipeline performance to reduce deployment times.<br>- Introduce more sophisticated testing, such as data quality tests (e.g., using dbt tests) and integration tests within the pipeline.<br>- Explore zero-downtime deployment strategies for applications and stored procedures. |
| Observability & monitoring | - Implement automated cost optimization actions, such as automatically resizing warehouses based on historical usage patterns.<br>- Use machine learning to forecast future credit usage and detect performance anomalies. |
| Automated governance | - Automate the tagging of data objects based on their contents to streamline governance.<br>- Develop automated routines to scan for and mask newly discovered sensitive data, ensuring continuous compliance. |

### Recommendations

- **Start small and iterate:** Don't try to automate everything at once.
  Begin with a single, high-impact area, such as role management via IaC
  or deploying a single dbt project with CI/CD. Prove the value and
  expand from there.

- **Treat your platform code like application code:** All scripts,
  configurations, and definitions (IaC, CI/CD, etc.) should be stored in
  a version control system like Git. Use pull requests and code reviews
  to manage changes. Decide early on rollback versus fix forward.

- **Empower teams with self-service:** The goal of automation is to
  enable teams (Data Engineering, AI, Analytics) to provision the
  resources they need safely and efficiently without waiting for a
  central team. Well-designed automation provides guardrails, not
  roadblocks.

- **Prioritize cost and performance monitoring:** The most immediate
  benefits of automation often come from gaining control over
  consumption. Automate the tracking of warehouse credit usage and query
  performance to identify optimization opportunities early.

- **Integrate security into your pipelines:** Shift security left by
  embedding automated checks into your CI/CD process. This includes
  scanning for insecure code patterns, checking for overly permissive
  grants, and ensuring compliance with organizational policies before
  deployment.

### Persona responsibilities (RACI chart)

This RACI (Responsible, Accountable, Consulted, Informed) matrix
clarifies the roles and responsibilities for automation activities
across different personas.

**Legend:** **R** = Responsible, **A** = Accountable, **C** = Consulted,
**I** = Informed

| **Activity** | **C-Level (CIO/CDO)** | **Chief Architect** | **Engineering / SRE** | **Data Science** | **Security** |
|----|----|----|----|----|----|
| **Defining automation strategy & tooling** | A | R | C | C | C |
| **Developing IaC modules & scripts** | I | C | R | I | C |
| **Building CI/CD pipelines** | I | C | R | C | C |
| **Managing environments via IaC** | I | A | R | I | I |
| **Deploying workloads via CI/CD** | I | I | R | R | I |
| **Defining & implementing monitoring alerts** | I | A | R | C | C |
| **Automating governance & access controls** | A | C | R | I | R |
| **Reviewing automated cost/usage reports** | A | I | C | C | I |

## Enhance Observability & Issue Resolution

### Overview

Observability in the Snowflake AI Data Cloud is about gaining deep,
actionable insights into your platform's health, performance, cost, and
security. It goes beyond simple monitoring by providing the context
needed to understand *why* something is happening, enabling you to move
from reactive problem-fixing to proactive optimization. Effective
observability ensures your data engineering pipelines are reliable, your
analytics are fast and accurate, your AI models are performant, and your
applications are secure. This framework provides a structured approach
to building a comprehensive observability strategy that delivers trust
and maximizes the value of your Snowflake investment for all
stakeholders, from engineers to the C-suite.

### Focus areas

We'll organize our observability strategy around four key focus areas.
These pillars ensure a holistic view of your Snowflake environment,
covering everything from cost efficiency to data integrity.

- **Cost & performance intelligence:** This involves monitoring resource
  consumption and query execution to optimize for both speed and spend.
  The goal is to maximize performance while maintaining predictable
  costs and providing clear chargeback/showback to business units.

- **Workload health & reliability:** This focuses on the end-to-end
  operational status of all workloads. It involves tracking the success
  and performance of data ingestion, transformation jobs, analytics
  queries, and AI/ML model execution to ensure they meet service-level
  objectives (SLOs).

- **Security & access analytics:** This is about safeguarding your data
  by continuously monitoring who is accessing what, when, and how. It
  includes tracking access patterns, identifying potential threats, and
  ensuring compliance with governance policies.

- **Data integrity & lineage:** This ensures the data itself is
  accurate, fresh, and trustworthy. It involves monitoring data quality
  metrics, tracking data lineage from source to consumption, and quickly
  identifying the root cause of data-related issues.

### Phase-based activities

A successful observability strategy is implemented incrementally. The
following phases provide a roadmap from initial preparation to
continuous improvement.

#### Prepare

This foundational phase is about defining what "good" looks like by
establishing goals, metrics, and ownership before implementing any
tools.

| Focus area | Activities |
|---|---|
| Cost & performance intelligence | - Define cost allocation strategy: Establish a consistent tagging methodology for users, roles, and warehouses to enable accurate chargeback.<br>- Establish performance baselines: Identify key queries and workloads (e.g., critical dashboard refreshes, ETL jobs) and document their expected runtimes and credit consumption.<br>- Select tooling: Evaluate whether to use native Snowflake features (Snowsight, `ACCOUNT_USAGE` views), third-party observability platforms, or a combination. |
| Workload health & reliability | - Define key Service Level Objectives (SLOs): For each workload, define measurable reliability targets. Examples: Snowpipe data freshness within 5 minutes; critical data transformation (dbt) jobs complete by 6 AM.<br>- Map critical data paths: Document the key data flows for your most important analytics, applications, and AI models. |
| Security & access analytics | - Define sensitive data & roles: Classify sensitive data objects and map the roles and users that should have access.<br>- Establish alerting policies: Define what constitutes a security incident (e.g., unauthorized access attempts, privilege escalation, data exfiltration patterns) that requires an immediate alert. |
| Data integrity & lineage | - Identify Critical Data Elements (CDEs): Pinpoint the most vital datasets that power executive dashboards, financial reporting, or production AI models.<br>- Define data quality rules: For CDEs, define rules for key metrics like freshness, completeness, and validity (e.g., `order_date` cannot be in the future). |

#### Implement

In this phase, you'll configure the tools and processes defined during
preparation to start collecting and visualizing observability data.

| Focus area | Activities |
|---|---|
| Cost & performance intelligence | - **Configure resource monitors:** set up warehouse-level monitors to prevent budget overruns by suspending warehouses or sending notifications at defined credit thresholds.<br>- **Build foundational dashboards:** create Snowsight dashboards to visualize credit usage by warehouse/tag, identify long-running queries (`QUERY_HISTORY`), and monitor warehouse queuing. |
| Workload health & reliability | - **Implement error notifications:** configure notifications for failed tasks (`SYSTEM$SEND_EMAIL`) or Snowpipe copy errors to immediately alert the responsible teams.<br>- **Monitor data ingestion:** use the `COPY_HISTORY` and `PIPE_USAGE_HISTORY` views to track the latency and health of data loading processes. |
| Security & access analytics | - **Enable access monitoring:** build dashboards on top of the `ACCESS_HISTORY` and `LOGIN_HISTORY` views to visualize user login patterns, query activity on sensitive tables, and privilege grants.<br>- **Set up security alerts:**** implement Snowflake alerts to trigger notifications for defined security events, such as a user being granted the `ACCOUNTADMIN` role. |
| Data integrity & lineage | - **Deploy data quality tests:** implement data quality checks as part of your data transformation pipeline (e.g., using dbt tests) that run on a schedule.<br>- **Utilize object tagging for lineage:** apply tags to tables and columns to create a basic, searchable framework for tracking data lineage. |


#### Operate

This phase focuses on the day-to-day use of the implemented
observability systems to monitor health and resolve issues.

| Focus area | Activities |
|---|---|
| Cost & performance intelligence | **Conduct regular cost reviews:** Hold weekly or bi-weekly reviews with engineering and finance teams to analyze spending trends and identify optimization opportunities.<br>**Triage performance issues:** Use query history and query profiles to investigate and troubleshoot slow-running queries, identifying bottlenecks like disk spilling or inefficient joins. |
| Workload health & reliability | **Respond to workload alerts:** Triage and resolve alerts for failed tasks, data loading errors, or SLO breaches.<br>**Manage incidents:** Follow a defined incident management process for critical failures, including communication, root cause analysis (RCA), and post-mortems. |
| Security & access analytics | **Review access logs:** Periodically audit access to sensitive data, investigate anomalous queries, and ensure access patterns align with business needs.<br>- Investigate security alerts: When an alert is triggered, follow a security runbook to investigate the potential threat, determine its impact, and remediate as needed. |
| Data integrity & lineage | **Investigate data quality failures:** When a data quality test fails, use lineage information to trace the issue back to its source and notify the data producers.<br>**Communicate data incidents:** Proactively inform data consumers when a known data quality issue impacts their dashboards or applications. |


#### Improve

This final phase is about moving from reactive to proactive operations
by analyzing trends, automating responses, and continuously refining
your observability strategy.

| Focus area | Activities |
|---|---|
| Cost & performance intelligence | **Automate warehouse scaling:** Use historical workload patterns to right-size warehouses or implement a more dynamic scaling strategy for spiky workloads.<br> **Optimize high-cost queries:** Proactively identify the top credit-consuming queries each month and assign them to engineering teams for performance tuning or rewriting. |
| Workload health & reliability | **Perform trend analysis:** Analyze historical task and pipe error rates to identify systemic issues in data pipelines and prioritize fixes.<br>**Refine SLOs and alerts:** Adjust SLO thresholds based on historical performance and business needs. Tune alerts to reduce noise and false positives. |
| Security & access analytics | **Automate access reviews:** Develop automated workflows to periodically require business owners to certify who has access to their data, reducing manual toil for security teams.<br> **Enhance threat detection models:** Use historical access data to build simple anomaly detection models (e.g., using Snowpark) to identify suspicious behavior that deviates from a user's normal baseline. |
| Data integrity & lineage | **Implement automated lineage:** Adopt tools that automatically parse SQL from QUERY_HISTORY to generate column-level lineage, dramatically speeding up impact analysis and root cause identification.<br>**Expand data quality coverage:** Use insights from data incidents to expand data quality monitoring to more datasets across the platform. |

### Recommendations

The following recommendations provide actionable steps for implementing
a robust observability and issue resolution strategy on Snowflake. They
are designed to guide interactions between teams and leverage specific
platform features.

### Establish a centralized observability data model

Instead of allowing teams to query raw metadata independently, create a
governed, centralized foundation for all observability data. This
ensures consistency and simplifies access control.

**For Enterprise Architects & SREs:**

- **Action:** In a dedicated OBSERVABILITY database, create a schema
  (e.g., MONITORING). Use a service role with IMPORTED PRIVILEGES on the
  SNOWFLAKE database to create **secure views** on top of critical
  ACCOUNT_USAGE views. This decouples your monitoring from the
  underlying Snowflake schema and provides a stable interface.

- **Key views to include:**

  - QUERY_HISTORY for performance analysis.

  - WAREHOUSE_METERING_HISTORY for cost and load analysis.

  - ACCESS_HISTORY and LOGIN_HISTORY for security forensics.

  - TASK_HISTORY and PIPE_USAGE_HISTORY for data engineering workload
    health.

  - AUTOMATIC_CLUSTERING_HISTORY and MATERIALIZED_VIEW_REFRESH_HISTORY
    for storage and performance optimization.

**For Engineering & Data Science teams:**

- **Action:** Build all monitoring dashboards and alerts exclusively
  from these centralized, secure views. This ensures that everyone, from
  a data engineer debugging a pipeline to a CIO reviewing costs, is
  looking at the same source of truth.

### Enrich observability data with contextual tagging

Raw metrics like "credit usage" or "query runtime" are not actionable
without context. A consistent tagging strategy is crucial for quickly
isolating the source of any issue.

**For Chief Architects & Engineering Leads:**

- **Action:** Define and enforce a mandatory **Object Tagging** policy
  for all key objects. The policy should require tags that map directly
  to your operational structure, such as project_name, cost_center,
  workload_type: \[engineering, analytics, ai, application\], and
  owner_email.

**For SREs & on-call engineers:**

- **Action:** During an incident, use tags as the primary filtering
  mechanism for issue resolution.

  - **Cost spike:** If a **resource monitor** alert triggers,
    immediately filter the WAREHOUSE_METERING_HISTORY view by tags to
    identify which project_name or workload_type caused the overage.

  - **Performance degradation:** If a dashboard is slow, filter
    QUERY_HISTORY by the workload_type: analytics tag and the relevant
    warehouse to find the long-running queries without the noise from
    other workloads.

### Implement persona-driven observability dashboards

A single dashboard cannot serve everyone. Build a tiered set of
dashboards in Snowsight that provides the right level of detail for each
persona, enabling them to answer their specific questions quickly.

**For SREs & platform owners:**

- **Action:** Create a "Platform Health" triage dashboard. This is the
  first place an on-call engineer looks. It should include:

  - Active Snowflake Alerts.

  - Recent task failures from TASK_HISTORY.

  - High-latency data loads from PIPE_USAGE_HISTORY.

  - Warehouse queuing and spilling metrics.

  - Queries with error codes from the last hour.

**For Engineering & Data Science leads:**

- **Action:** Build "Workload Performance" dashboards for your specific
  domains.

  - **Data Engineering:** Visualize task dependencies (your DAG) and
    color-code them by status (SUCCEEDED/FAILED) from **TASK_HISTORY**.
    Track credit consumption per pipeline.

  - **AI/ML:** Monitor the execution time and credit usage of Snowpark
    model training jobs. Instrument Snowpark Python code to log metrics
    to a Snowflake table and visualize them here.

**For C-Level stakeholders (CIO/CFO):**

- **Action:** Create a high-level "Executive Summary" dashboard showing:

  - Platform-wide credit consumption vs. forecast.

  - Cost breakdown by business unit (using tags).

  - Key SLO attainment (e.g., "99.9% of critical data pipelines
    completed on time").

### Automate detection and response with alerts & tasks

Move from passive monitoring to active, automated observability. Use
Snowflake's native features to not only detect issues but also to notify
the right people and, where appropriate, trigger corrective actions.

**For Security & SRE teams:**

- **Action:** Implement the "Detect, Notify, Remediate" pattern using
  Snowflake's serverless features.

  1.  **Detect:** Create **Snowflake Alerts** that periodically run a
      query to check for an issue.

      - *Security Example:* CREATE ALERT suspicious_grant_alert ... IF
        (EXISTS (SELECT 1 FROM ... QUERY_HISTORY WHERE query_text ILIKE
        'GRANT ACCOUNTADMIN%')) ...

      - *Performance Example:* An alert that checks QUERY_HISTORY for
        queries running longer than 1 hour.

  2.  **Notify:** Configure the Alert's action to call a **Notification
      Integration** that sends a detailed message to a Slack channel,
      PagerDuty, or email via SYSTEM\$SEND_EMAIL. The message should
      include context, like the QUERY_ID or USER_NAME, to accelerate
      triage.

  3.  **Remediate (with caution):** For well-understood, low-risk
      problems, have the Alert's action call a stored procedure. For
      example, an alert for a long-running, non-critical query could
      call a procedure that cancels it using SYSTEM\$CANCEL_QUERY.

### Persona responsibilities (RACI chart)

This RACI (Responsible, Accountable, Consulted, Informed) matrix
clarifies the roles and responsibilities for key observability
activities across different teams.

**Legend:** **R** = Responsible, **A** = Accountable, **C** = Consulted,
**I** = Informed

| Activity | C-Level (CIO/CDO/CFO) | Chief Architect | Engineering | Data Science | Security | SRE |
|---|---|---|---|---|---|---|
| Define cost & security policies | A | R | C | C | R | C |
| Implement & manage budgets (resource monitors) | A | C | R | I | I | R |
| Build & maintain observability dashboards | I | C | R | C | C | R |
| Investigate & resolve | I | C | R | C | I | R |
| Monitor & triage workload failures (ETL, AI) | I | I | R | R | I | A |
| Define & monitor data quality rules | C | C | C | A | I | I |
| Investigate & remediate security incidents | A | C | C | I | R | C |
| Conduct access & entitlement reviews | A | I | C | C | R | I |
 

## Manage incidents & problems

### Overview

Effective incident and problem management is the cornerstone of a
reliable data platform. In the Snowflake AI Data Cloud, where critical
data pipelines, analytics, AI workloads, and applications depend on high
availability and performance, a structured approach to handling
disruptions is essential. The primary goal is to maintain the trust of
your stakeholders by ensuring that data services are available,
performant, and deliver accurate results.

This framework addresses two distinct but related disciplines:

- **Incident Management:** Focuses on the immediate restoration of
  service following an unplanned disruption. The objective is to
  minimize business impact and reduce the Mean Time to Resolution
  (MTTR). In Snowflake, an incident could be a stalled data engineering
  pipeline, a severely degraded analytics dashboard, or an application
  query failure.

- **Problem Management:** Focuses on identifying and remediating the
  underlying root cause of one or more incidents. By addressing the
  source of the issue, problem management aims to prevent future
  incidents from occurring, thereby increasing the overall stability and
  resilience of the platform. Build in AI Models to automatically
  remediate incidents, predict issues and track anomalies.

This section provides a structured approach for managing the entire
incident lifecycle within the Snowflake AI Data Cloud—from proactive
detection and rapid response to thorough root cause analysis. Adopting
these practices builds confidence in your data platform, ensuring it
remains a dependable foundation for critical business decisions and
innovation.

### **Focus areas**

**Detection & alerting**

This is the "smoke alarm" for your data platform. The goal is to
identify deviations from normal behavior as quickly as possible, often
before users are impacted. This involves instrumenting key Snowflake
metrics, such as query execution time, warehouse load, and data latency,
and setting up automated alerts to notify the on-call team of potential
issues.

**Response & Triage**

When an alert fires, this is the initial assessment and firefighting
phase. The focus is on understanding the impact ("who is affected?"),
determining the severity ("how bad is it?"), and executing immediate
actions to stabilize the service. In Snowflake, this could involve
canceling a runaway query, resizing a virtual warehouse, or
communicating the initial findings to stakeholders.

**Resolution & recovery**

This area focuses on fully resolving the incident and returning the
service to a healthy state. It involves deeper diagnosis to find a fix
or a workaround that restores functionality for all affected users. This
phase concludes when the immediate impact is over and the service is
operating under normal conditions again.

**Root Cause Analysis (RCA)**

Once the immediate fire is out, the problem management process begins.
RCA is the systematic investigation to uncover the fundamental cause of
an incident, not just the symptoms. The objective is to ask "why"
repeatedly until the core issue is identified, such as an inefficient
query pattern, a flawed data model, or an inadequate warehouse
configuration.

**Readiness & Preparation**

This is the proactive area focused on learning from past incidents and
improving future responses. It involves creating and refining runbooks
for common failure scenarios, conducting incident response drills, and
ensuring roles and communication plans are clearly defined. A
well-prepared team can significantly reduce the time it takes to resolve
future incidents.

### Phase-based activities

### Prepare

This phase includes all the proactive work your teams do *before* an
incident occurs to ensure they are ready to respond effectively.

- **Detection & alerting:** Define Key Performance Indicators (KPIs) for
  your critical workloads, such as query duration, warehouse queuing,
  and data ingestion latency. Establish the acceptable performance
  thresholds that, if crossed, will trigger an alert.

- **Response & triage:** Define clear incident **severity levels**
  (e.g., SEV-1, SEV-2) based on business impact. Create communication
  templates and establish on-call rotations and escalation paths so
  everyone knows their role.

- **Resolution & recovery:** Identify and document potential mitigation
  actions for common incidents. For example, note the exact commands for
  resizing a warehouse or terminating a query.

- **Root Cause Analysis (RCA):** Create a standardized, blameless
  **post-mortem template** to ensure consistent analysis after an
  incident. Define the criteria for which incidents require a formal
  RCA.

- **Readiness & preparation:** Brainstorm the most likely or most
  impactful failure scenarios for your specific Snowflake workloads,
  such as a bad data deployment or a query storm from an application.

### Implement

In this phase, you build and configure the systems, tools, and
documentation needed to manage incidents efficiently.

- **Detection & alerting:** Build **Snowsight dashboards** using
  ACCOUNT_USAGE data to visualize your KPIs. Configure **Snowflake
  Alerts** or integrate with third-party tools like PagerDuty to send
  notifications when your defined thresholds are breached.

- **Response & triage:** Set up your on-call scheduling software and
  configure dedicated communication channels, such as a specific Slack
  channel, where the incident response team will coordinate.

- **Resolution & recovery:** Ensure that on-call engineers have the
  necessary permissions in Snowflake to execute mitigation commands,
  like ALTER WAREHOUSE, without needing to wait for approvals.

- **Root Cause Analysis (RCA):** Create a centralized and searchable
  repository, such as a Confluence space or shared drive, to store all
  post-mortem documentation for future reference.

- **Readiness & preparation:** Write and maintain runbooks that provide
  clear, step-by-step diagnostic and resolution instructions for the
  failure scenarios you identified in the Prepare phase.

### Operate

This phase covers the real-time activities your team performs *during*
an active incident.

- **Detection & alerting:** Monitor dashboards to correlate events and
  understand the scope of the issue. Acknowledge and begin investigating
  triggered alerts to confirm that an incident is occurring.

- **Response & triage:** Officially declare an incident and assign the
  correct severity level. Assemble the response team in the designated
  channel and execute the communication plan to keep stakeholders
  informed.

- **Resolution & recovery:** Execute the appropriate resolution from
  your runbook. This could involve running SYSTEM\$CANCEL_QUERY(),
  resizing a warehouse with ALTER WAREHOUSE, or triggering a database
  failover. Verify that the service is restored before closing the
  incident.

- **Root Cause Analysis (RCA):** Gather evidence while the incident is
  active. Save relevant query IDs, take screenshots of the Query
  Profile, and note key event timestamps to support the future RCA.

- **Readiness & preparation:** Consult the appropriate runbook to guide
  your response. This ensures a consistent and efficient process,
  preventing responders from having to solve problems from scratch under
  pressure.

### Improve

This phase is about learning from past incidents *after* they are
resolved to build a more resilient system and process.

- **Detection & alerting:** Tune your alerts to reduce false positives
  (noise) and false negatives (missed incidents). Create new alerts to
  detect the failure modes discovered during your most recent
  post-mortem.

- **Response & triage:** Based on feedback, refine your severity
  definitions, communication templates, and on-call escalation processes
  to make them more effective for the next incident.

- **Resolution & recovery:** Document the successful resolution steps in
  the relevant runbook. If a manual workaround was used, create a ticket
  for a permanent engineering **fix** to address the underlying issue.

- **Root Cause Analysis (RCA):** Conduct a blameless post-mortem with
  all involved parties. Perform a deep-dive analysis using Snowflake's
  Query Profile to find the true root cause and assign owners to
  actionable follow-up items.

- **Readiness & preparation:** Update your runbooks with new information
  learned during the incident. Proactively test your team's readiness
  and the accuracy of your documentation by conducting "Game Days" that
  simulate real-world incidents.

### Recommendations

Effective incident management in Snowflake relies on leveraging its
unique architectural strengths—separating compute from storage and
providing rich operational metadata. These recommendations provide
actionable steps for detection, response, and improvement.

### Establish a single source of truth for triage

During an incident, speed and accuracy are paramount. Centralize your
initial investigation using Snowflake's comprehensive metadata logs to
shorten the time from detection to diagnosis.

Centralize incident detection with ACCOUNT_USAGE views

- **Action**: Your on-call SRE and Engineering teams should treat the
  SNOWFLAKE.ACCOUNT_USAGE schema as the definitive event log. Build
  pre-configured Snowsight dashboards and alerts that immediately
  highlight anomalies in key views:

  - QUERY_HISTORY: To spot long-running, failing, or unusually high-IO
    queries.

  - WAREHOUSE_LOAD_HISTORY: To detect warehouse overload, queuing, and
    resource contention.

  - LOGIN_HISTORY: To investigate potential access or security-related
    incidents.

- **Snowflake Tooling**: [ACCOUNT_USAGE
  schema](https://docs.snowflake.com/en/sql-reference/account-usage),
  Snowsight Dashboards, Snowflake Alerts.

### Isolate and mitigate performance incidents immediately 

Snowflake's architecture provides powerful levers to contain and resolve
performance degradation without affecting the entire platform. Your
response should focus on isolating the problematic workload and
adjusting compute resources dynamically.

**Terminate runaway queries without affecting the warehouse**

- **Action:** The on-call Engineer should first use QUERY_HISTORY to
  identify the specific query ID causing a performance issue.
  Immediately execute the SYSTEM\$CANCEL_QUERY() function to terminate
  that single query. This surgical action stops the resource drain
  without needing to restart the entire virtual warehouse, leaving all
  other running queries unaffected.

- **Snowflake Tooling:**
  [SYSTEM$CANCEL_QUERY(<query_id>)](https://docs.snowflake.com/en/sql-reference/functions/system_cancel_query)

**Dynamically scale compute to resolve resource contention**

- **Action:** If an incident is caused by a legitimate surge in workload
  (e.g., month-end reporting), the SRE or Engineering Lead can instantly
  mitigate it. For warehouses already configured as Multi-cluster
  Warehouses (MCW), scaling is automatic. If not, manually resize the
  warehouse using the ALTER WAREHOUSE command. This on-the-fly scaling
  resolves queuing and provides immediate relief, a unique advantage of
  Snowflake's elastic architecture.

- **Snowflake Tooling:** [ALTER
  WAREHOUSE](https://docs.snowflake.com/en/sql-reference/sql/alter-warehouse)
  ... SET WAREHOUSE_SIZE = ..., Multi-cluster Warehouse configuration.

### Automate disaster recovery and high-availability responses 

For major incidents like a regional outage, your response should be
swift, tested, and reliable. This depends on preparation and leveraging
Snowflake's built-in business continuity features.

**Execute pre-defined runbooks for cross-region failover.**

- **Action:** The CIO/CTO provides the business approval, and the SRE
  team executes the failover runbook. This involves running a single
  command (ALTER FAILOVER GROUP ... PRIMARY) to promote a replica
  database in a secondary region to primary status. This action is
  underpinned by asynchronous database replication, which should already
  be configured for all critical databases. Applications can then be
  seamlessly rerouted using **Client Redirect**.

- **Snowflake Tooling:** [Database
  Replication](https://docs.snowflake.com/en/user-guide/account-replication-intro),
  **Failover Groups**, **Client Redirect**

### Perform data-driven post-mortems for continuous improvement

Every incident is a learning opportunity. Use Snowflake's detailed query
execution data to move beyond symptoms and identify the precise root
cause, leading to permanent fixes.

**Analyze the query profile to pinpoint inefficiencies**

- **Action:** As part of a blameless post-mortem, the **Engineering**
  and **Data Science** teams involved should analyze the **Query
  Profile** of the problematic query in Snowsight. This tool provides a
  visual, step-by-step breakdown of query execution. Look for specific
  anti-patterns like "exploding" joins, excessive remote disk spilling,
  or full table scans on poorly clustered data. This turns a generic
  "slow query" incident into an actionable finding.

- **Snowflake Tooling:** [Query
  Profile](https://docs.snowflake.com/en/user-guide/ui-query-profile)
  interface in Snowsight.

### Persona responsibilities (RACI chart)

A RACI (Responsible, Accountable, Consulted, Informed) matrix defines
the roles and responsibilities for incident and governance management:

**Legend:** **R** = Responsible, **A** = Accountable, **C** = Consulted,
**I** = Informed

| Role | CIO/CDO/CTO/CFO | Chief Enterprise Architect | Engineering | Data Science | Security | SRE |
|---|---|---|---|---|---|---|
| Incident management | A | C | R | I | C | R |
| Governance | A | R | C | I | R | C |
| Security | A | C | I | I | R | C |
| Cost management | A | C | R | I | I | C |

## Enable collaboration & Secure Sharing

### Overview

Enabling secure, real-time collaboration across your organization, with
customers, and with business partners is a foundational pillar of the
Snowflake AI Data Cloud. Unlike traditional methods that involve risky
and inefficient data duplication and FTP transfers, Snowflake's
architecture allows you to **share live, governed data without moving or
copying it**. This unlocks new opportunities for data-driven insights,
AI development, and monetization while maintaining a strong security and
governance posture.

This framework provides principles and best practices to help you build
a robust strategy for sharing and collaboration. By implementing these
guidelines, you can break down data silos, accelerate innovation, and
create new value streams, all while ensuring your data remains
protected.

### Focus areas

To effectively enable collaboration and secure sharing in Snowflake,
concentrate on four key areas. These areas provide a structured approach
to designing, implementing, and managing your data sharing ecosystem.

- **Secure data sharing architecture:** This area focuses on the
  foundational components and patterns for sharing data. It covers the
  technical constructs like Shares, Reader Accounts, and the Snowflake
  Marketplace, and how to structure them to meet various business needs,
  from internal cross-departmental access to public data monetization.

- **Granular governance and control:** Secure sharing is impossible
  without robust governance. This area addresses the policies and
  controls needed to protect data. Key technologies include Role-Based
  Access Control (RBAC), Dynamic Data Masking, Row-Access Policies, and
  Data Classification (using tags) to ensure that consumers only see the
  data they are authorized to see.

- **Unified collaboration for workloads:** This focuses on the tools and
  features that enable different teams and workloads to collaborate
  effectively on the same data. It includes using Snowpark for joint
  data science and engineering projects, leveraging Streams and Tasks
  for building collaborative data pipelines, and developing Snowflake
  Native Apps to share data-powered applications securely.

- **Comprehensive auditing and monitoring:** To maintain trust and
  security, you should have visibility into how shared data is being
  used. This area covers the practices for monitoring share consumption,
  auditing access patterns using views like ACCESS_HISTORY, and setting
  up alerts to detect and respond to anomalous activity.

### Phase-based activities

A successful data sharing strategy is implemented progressively. The
following phases outline the journey from initial planning to continuous
improvement.

### Prepare

The Prepare phase is about establishing the strategy, governance
framework, and organizational alignment needed for secure data sharing.

| **Focus area** | **Activities** |
|----|----|
| **Secure data sharing architecture** | Identify and prioritize datasets suitable for sharing. Define potential data consumers (internal teams, external partners) and their access requirements. Design a hub-and-spoke or federated sharing model. |
| **Granular governance and control** | Define a data sharing policy that outlines acceptable use, security requirements, and the approval process. Establish a data classification framework to tag sensitive data (e.g., PII, confidential). |
| **Unified collaboration for workloads** | Identify key collaboration use cases, such as joint AI/ML model development or building a shared analytics dashboard. |
| **Comprehensive auditing and monitoring** | Define key metrics for success and risk, such as the number of data consumers, query volume on shares, and types of sensitive data being accessed. Plan your auditing strategy. |

### Implement

The Implement phase involves the hands-on configuration of the Snowflake
platform to bring your sharing strategy to life.

| **Focus area** | **Activities** |
|----|----|
| **Secure data sharing architecture** | Create SHARE objects and grant them access to specific database objects (tables, secure views). For external sharing without a Snowflake account, provision Reader Accounts. For broad distribution, create listings on the Snowflake Marketplace. |
| **Granular governance and control** | Implement RBAC roles for data sharing administration and consumption. Apply dynamic data masking policies to sensitive columns and row-access policies to tables before adding them to a share. Use object tags to automate policy application. |
| **Unified collaboration for workloads** | Develop and deploy Snowpark applications that can be shared via listings. Build shared data engineering pipelines using Streams and Tasks. Package and publish Snowflake Native Apps to offer data and application logic together. |
| **Comprehensive auditing and monitoring** | Configure alerts on QUERY_HISTORY and ACCESS_HISTORY to monitor for unusual access patterns on shared objects. Set up monitoring dashboards to track share consumption and performance. |

### Operate

The Operate phase focuses on the day-to-day management of your data
sharing environment, ensuring it runs smoothly and securely.

| **Focus area** | **Activities** |
|----|----|
| **Secure data sharing architecture** | Manage the lifecycle of data consumers, including approving requests, providing support, and revoking access when necessary. Regularly update data in shares to ensure consumers have the freshest information. |
| **Granular governance and control** | Conduct periodic reviews of access controls and sharing policies to ensure they remain aligned with business needs and compliance requirements. |
| **Unified collaboration for workloads** | Provide support for shared assets like Snowpark applications and data pipelines. Gather feedback from users to identify areas for improvement. |
| **Comprehensive auditing and monitoring** | Regularly review audit logs and monitoring dashboards. Investigate any security alerts or performance degradation related to data sharing activities. |

### Improve

The Improve phase is about optimizing and evolving your data sharing
capabilities based on feedback, usage data, and new business
requirements.

| **Focus area** | **Activities** |
|----|----|
| **Secure data sharing architecture** | Actively solicit feedback from data consumers to enhance datasets and create new data products. Analyze Marketplace usage to optimize listings and pricing. Automate the consumer onboarding process. |
| **Granular governance and control** | Refine and automate the application of governance policies using tag-based masking and access controls. Update the data sharing policy based on lessons learned and evolving regulations. |
| **Unified collaboration for workloads** | Enhance Snowflake Native Apps with new features based on consumer feedback. Explore new collaboration patterns using emerging Snowflake features. |
| **Comprehensive auditing and Monitoring** | Fine-tune monitoring alerts to reduce false positives. Develop more sophisticated usage analytics to better understand the value derived from shared data and identify new sharing opportunities. |

### Recommendations

To activate your data sharing and collaboration strategy, your teams
should take specific, coordinated actions. The following recommendations
provide an imperative guide for stakeholders, detailing the exact tools
to use and referencing official Snowflake documentation for further
detail.

### Mandate the use of secure views for all shares

Instead of sharing raw tables, always use [SECURE
VIEWS](https://docs.snowflake.com/en/user-guide/views-secure) as the
interface for your data consumers. This creates a durable, controlled
contract that decouples consumers from your underlying physical data
model and embeds fine-grained security logic directly into the shared
object.

**Action Plan:**

1.  The Chief Enterprise Architect and Security team will mandate a
    policy stating that no TABLE object can be directly added to a
    SHARE.

2.  For a new sharing request, the Data Science or business user defines
    the specific columns and row-level filtering criteria needed by the
    consumer.

3.  The Data Engineer translates these requirements into a CREATE SECURE
    VIEW statement. Within the WHERE clause of the view, they use
    functions like CURRENT_ROLE() or IS_ROLE_IN_SESSION() to implement
    logic that filters data based on the consumer's role.

4.  The Security team reviews and approves the view's DDL to ensure it
    doesn't expose sensitive data.

5.  Finally, the Data Engineer grants SELECT on the secure view to the
    SHARE.

### Operationalize a "data as a product" mindset with in-platform documentation

Treat every shared dataset as a product. A product requires clear
documentation that allows consumers to discover, understand, and trust
it. Use Snowflake's native features to build and share this
documentation alongside the data itself.

**Action Plan:**

1.  The Data Governance team defines a standard for documentation,
    including mandatory descriptions for all shared tables, views, and
    columns.

2.  During development, the Data Engineer adds descriptive
    [COMMENT](https://docs.snowflake.com/en/sql-reference/sql/comment)
    metadata to every object and column using COMMENT = '...' in their
    DDL or COMMENT ON ... IS '...' statements.

3.  The Chief Enterprise Architect designs a "Data Dictionary" view
    built on the SNOWFLAKE.ACCOUNT_USAGE.COLUMNS view. This view should
    be shared with all internal data consumers, allowing them to query
    and explore available datasets and their documented business
    context.

4.  For external consumers on the Marketplace, the Engineering team adds
    rich descriptions and sample queries directly into the listing's UI
    in Snowsight.

### Automate governance at scale with tag-based policies

Manually applying security policies to hundreds of tables is not
scalable and is prone to error. Instead, implement a [tag-based
governance
framework](https://docs.snowflake.com/en/user-guide/tag-based-masking-policies)
where security policies (like masking) automatically attach to data
based on its classification.

**Action Plan:**

1.  The Security team, in consultation with the CIO/CDO, defines a data
    classification taxonomy and creates the corresponding object tags in
    Snowflake (e.g., CREATE TAG pii_level WITH ALLOWED_VALUES 'HIGH',
    'LOW').

2.  Security then creates generic masking policies. For example, a
    policy named mask_pii_high that redacts data, and another named
    mask_email that shows only the email domain.

3.  Security then associates these policies with the tags (e.g., ALTER
    TAG pii_level SET MASKING POLICY mask_pii_high).

4.  As part of their CI/CD process, Data Engineers are responsible for
    setting the appropriate tags on tables and columns as they are
    created (e.g., ALTER TABLE ... MODIFY COLUMN email SET TAG pii_level
    = 'HIGH').

5.  Snowflake automatically applies the correct masking policy to the
    email column by virtue of the tag, ensuring governance is enforced
    without manual intervention before the data is ever added to a
    share.

### Distribute application logic securely with Snowflake Native Apps

When you need to share more than just data—such as a proprietary
algorithm, a machine learning model, or a complete interactive
application—use the [Snowflake Native App
Framework](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about).
This allows consumers to run your logic on their own data without the
code or data ever leaving their secure Snowflake environment.

**Action Plan:**

1.  A Data Science team develops a predictive model using Snowpark for
    Python and saves it as a User-Defined Function (UDF).

2.  An Application Developer (within Engineering) builds a user
    interface using the Streamlit in Snowflake integration that allows
    users to input data and see the model's prediction.

3.  The developer packages the Snowpark UDF, the Streamlit UI, and any
    necessary stored procedures into an APPLICATION PACKAGE. They define
    the components in a manifest.yml file and a setup.sql script.

4.  The CDO and Engineering lead decide to list the application on the
    Marketplace. The engineer uses Snowsight to create a listing from
    the application package, adding pricing and usage terms.

5.  A consumer can now "install" this application, running the
    provider's proprietary model against their own private customer
    table, with the provider having zero access to the consumer's data.

### Persona responsibilities (RACI chart)

Clarifying roles and responsibilities is crucial for a well-governed
data sharing program. The following RACI (Responsible, Accountable,
Consulted, Informed) matrix outlines the typical duties for each
persona.

**Legend:** **R** = Responsible, **A** = Accountable, **C** = Consulted,
**I** = Informed

| **Activity** | **CIO / CDO** | **Chief Enterprise Architect** | **Security** | **Engineering / SRE** | **Data Science** |
|----|----|----|----|----|----|
| Define Data Sharing & Monetization Strategy | A | C | C | I | C |
| Establish Governance & Sharing Policies | A | C | R | I | I |
| Design the Sharing Architecture (e.g., Shares, Views) | I | A | C | R | C |
| Implement and Apply Security Controls (Masking/Row Access) | I | I | A | R | I |
| Publish and Manage Marketplace Listings | A | I | C | R | C |
| Approve and Onboard Data Consumers | I | I | C | R | A |
| Monitor and Audit Sharing Usage | I | I | A | R | I |
| Develop Collaborative Snowpark/Native App Assets | I | C | C | R | A |

## Manage the Software Development Lifecycle (SDLC)

### Overview

A well-defined Software Development Lifecycle (SDLC) in Snowflake
enables teams to innovate faster while maintaining stability and
governance. It transforms development from an ad-hoc process into a
predictable, repeatable, and automated workflow. By applying software
engineering best practices like version control, automated testing, and
CI/CD to your data projects, you can significantly reduce manual errors,
improve collaboration, and increase the trustworthiness of your data
assets. This is essential for all key workloads, whether you are
building scalable data pipelines, developing complex machine learning
models with Snowpark, or deploying native applications.

### Focus areas

To build a robust SDLC, we recommend concentrating on five key focus
areas. These areas provide the foundation for a mature and scalable
development process on Snowflake.

- **Version control & code management:** The practice of tracking and
  managing changes to your code and configuration files. This is the
  bedrock of collaborative development, enabling teams to work in
  parallel, review changes, and maintain a complete history of every
  modification. Key components include Git-based repositories, branching
  strategies (e.g., GitFlow), and mandatory peer reviews.

- **CI/CD automation (Continuous Integration/Continuous Deployment):**
  The automation of building, testing, and deploying code changes.
  **CI** focuses on automatically integrating code changes from multiple
  contributors into a single shared repository. **CD** extends this by
  automatically deploying the integrated code to various environments
  (development, staging, production) after it passes all tests. This
  accelerates delivery and reduces deployment risk.

- **Testing & quality assurance:** The process of validating that your
  data, code, and models meet quality standards. This is not just about
  code functionality but also about data accuracy, integrity, and
  performance. This includes unit tests for Snowpark functions,
  integration tests for data pipelines, and data quality checks using
  tools like dbt Tests or Great Expectations.

- **Environment management:** The strategy for creating and managing
  separate, isolated Snowflake environments for different stages of the
  SDLC (e.g., Development, Test/QA, Production). This ensures that
  development work doesn't impact production workloads and allows for
  safe testing of changes before they are promoted. This often involves
  Snowflake's Zero-Copy Cloning for efficient environment creation.

- **Observability & monitoring:** The ability to understand the internal
  state of your systems from their external outputs. This involves
  collecting logs, metrics, and traces to monitor the health,
  performance, and cost of your Snowflake workloads. Effective
  observability helps you detect issues proactively, troubleshoot
  failures, and optimize resource usage.

### Phase-based activities

Managing the SDLC in a well-architected way can be broken down into four
distinct phases. Here's how the focus areas apply to each phase.

### Prepare

This phase is about planning and setting up the foundational components
for your project.

- **Version control:** Establish a Git repository (e.g., in GitHub,
  GitLab) for your project. Define and document a branching strategy.

- **CI/CD automation:** Select and configure your CI/CD tools (e.g.,
  GitHub Actions, Jenkins). Create starter pipeline templates for
  different workload types (dbt, Snowpark, Streamlit).

- **Testing:** Define the project's testing strategy. Identify the tools
  and frameworks you'll use for unit, integration, and data quality
  testing.

- **Environment management:** Define your environment promotion
  strategy. Use scripts (e.g., Terraform, SQL) to create role-based
  access controls and provision separate development, testing, and
  production databases or schemas.

- **Observability:** Define key performance indicators (KPIs) for the
  workload. Set up logging standards and choose monitoring tools to
  capture query history, credit usage, and performance metrics from
  Snowflake's ACCOUNT_USAGE views.

### Implement

This phase involves the core development and building of your data asset
or application.

- **Version control:** Developers create feature branches to work on new
  code. All changes are committed to these branches with clear,
  descriptive messages. Pull/Merge Requests are used to initiate code
  reviews.

- **CI/CD automation:** Upon a pull request, the CI pipeline
  automatically triggers. It runs linters, builds artifacts (e.g.,
  Snowpark UDFs), and executes unit tests.

- **Testing:** Developers write unit tests for their code (e.g., Pytest
  for Snowpark Python). Integration tests are developed to validate
  interactions between different components, and data quality tests are
  defined (e.g., asserting not_null on a primary key column).

- **Environment management:** Developers use their dedicated, isolated
  development environments or databases, often created using Zero-Copy
  Clones of production data subsets, to build and test their features
  safely.

- **Observability:** Implement structured logging within your code
  (e.g., in Snowpark functions or stored procedures). Add custom tags to
  queries to track lineage and cost attribution.

### Operate

This phase focuses on deploying, managing, and monitoring the solution
in production.

- **Version control:** Merging a feature branch into the main branch
  serves as the trigger for deployment and creates an immutable, tagged
  release.

- **CI/CD automation:** The CD pipeline takes over after a successful CI
  run and merge. It automatically deploys the changes to the production
  environment, applying database object changes (SchemaOps/GitOps) and
  updating tasks or streams.

- **Testing:** Automated smoke tests run immediately after deployment to
  verify the health of the production system. Continuous data quality
  tests run against production data to catch anomalies.

- **Environment management:** The CI/CD pipeline manages the promotion
  of code and database objects through environments (Dev -\> Test -\>
  Prod). Access to the production environment is highly restricted and
  managed via automation.

- **Observability:** Actively monitor dashboards for system health,
  query performance, and credit consumption. Configure alerts to notify
  the SRE team of failures, performance degradation, or cost anomalies.

### Improve

This final phase is about iterating on the solution and the process
itself based on operational feedback.

- **Version control:** Analyze the commit history and pull request
  feedback to identify areas for improving code quality and
  collaboration.

- **CI/CD automation:** Optimize pipeline performance to reduce build
  and deployment times. Add new steps to the pipeline to automate more
  quality checks or security scans.

- **Testing:** Review test failures and data quality alerts to identify
  recurring issues. Refine and expand the test suite to improve coverage
  and prevent regressions.

- **Environment management:** Periodically review and clean up old
  development environments. Use feedback to improve the environment
  creation and data seeding processes.

- **Observability:** Analyze performance and cost trends from monitoring
  data. Use these insights to refactor inefficient queries, optimize
  warehouse sizes, and improve the overall architecture. Conduct
  post-mortems on incidents to identify root causes and implement
  preventative measures.

### Recommendations

To implement a mature SDLC for the Snowflake AI Data Cloud, your teams
should adopt specific practices and tools. These recommendations provide
actionable guidance for each stakeholder to build a reliable, automated,
and governable development lifecycle.

### Standardize your core SDLC toolchain

**Action:** The Chief Enterprise Architect and Engineering Leads should
define and enforce a single, approved toolchain for source control,
CI/CD, and infrastructure management. This prevents fragmentation and
ensures consistency.

- Engineering and SRE teams will configure a central Git provider (e.g.,
  GitHub, GitLab) as the single source of truth for all
  Snowflake-related code, including SQL scripts, Snowpark Python/Java
  files, and dbt models.

- They will create standardized CI/CD pipeline templates (e.g., using
  GitHub Actions, Jenkins) that all teams must use. These templates
  should include predefined stages for linting, testing, building, and
  deploying to Snowflake.

- Developers and Data Scientists should use these templates to ensure
  every project adheres to the same quality and security gates before
  code is merged. This streamlines onboarding and enforces best
  practices automatically.

These CI/CD pipelines will use tools like the [SnowSQL
CLI](https://docs.snowflake.com/en/user-guide/snowsql) or the
[Snowflake Connector for
Python](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector)
to execute scripts and deploy objects against Snowflake environments.

### Adopt GitOps for all Snowflake object management

**Action:** All changes to Snowflake database objects (schemas, tables,
views, roles, grants) can be managed declaratively as code in Git.
Direct CREATE OR REPLACE commands against production environments should
be prohibited.

- The SRE and Engineering teams should consider implementing an
  open-source schema migration tool like
  [schemachange](https://github.com/Snowflake-Labs/schemachange)
  within the standard CD pipeline. This tool compares the state of a
  target database with the state defined in Git and applies only the
  necessary changes in a versioned, ordered manner.

- Developers and Data Engineers must commit all database object changes
  as new, version-numbered SQL scripts in a designated folder within
  their Git repository.

- The deployment pipeline, triggered by a merge to the main branch, will
  automatically execute schemachange to apply these scripts to the
  target Snowflake environment. This creates a fully auditable and
  reversible history of every change to your database schema.

This practice provides a robust audit trail for all DDL, DML, and DCL
statements executed against Snowflake, improving governance and
simplifying troubleshooting.

### Automate quality gates with comprehensive testing

**Action:** Enforce automated testing as a mandatory step in your CI
pipeline. Pull requests that do not pass all tests must be blocked from
merging.

- Data Scientists and Engineers working with Snowpark must write unit
  tests for their Python/Java/Scala code using standard frameworks
  (e.g., pytest, JUnit). These tests validate business logic within
  User-Defined Functions (UDFs) and Stored Procedures before they are
  deployed to Snowflake.

- Data Engineers using tools like dbt must write data quality tests
  (e.g., not_null, unique, relationships) for their data models. These
  tests are defined in YAML files alongside the models and run
  automatically as part of the CI process.

- The SRE team must configure the CI pipeline to execute these tests
  against a temporary, cloned environment for every pull request. The
  test results should be published back to the pull request to provide
  immediate feedback.

Testing can be done against temporary schemas or databases created using
Zero-Copy Cloning, providing a production-like environment without
incurring storage costs or performance impact.

### Isolate workflows with on-demand cloned environments

**Action:** Empower your development teams with self-service, isolated
environments using Snowflake's [Zero-Copy
Cloning](https://docs.snowflake.com/en/user-guide/object-clone)
feature. This eliminates development bottlenecks and ensures
high-fidelity testing.

- SRE and DevOps teams should create an automated job or script (e.g.,
  in the CI/CD tool or a chatbot) that allows any developer to instantly
  provision a new environment. This script should execute the
  [CREATE TRANSIENT DATABASE <dev_db_name> CLONE
  <prod_db_name>;](https://docs.snowflake.com/en/sql-reference/sql/create-clone)
  command and apply the appropriate role-based access controls.

- Developers and Data Scientists should trigger this job at the start of
  any new feature branch work. This provides them with a full-scale,
  read-only copy of the production data to develop and test against
  without any risk to the production environment.

- A nightly job should be created to automatically tear down cloned
  environments older than a few days to maintain hygiene.

This directly leverages one of Snowflake's most powerful features.
Cloning is an instantaneous metadata operation, meaning environments are
ready in seconds, not hours, and consume no additional storage until
changes are made.

### Embed cost and performance monitoring into the workflow

**Action:** Make cost and performance explicit responsibilities of the
development team, not just an operational afterthought. Integrate
monitoring directly into the SDLC.

- SREs and Engineering Leads should build shared dashboards using data
  from the SNOWFLAKE.ACCOUNT_USAGE schema, specifically views like
  QUERY_HISTORY and WAREHOUSE_METERING_HISTORY. These dashboards should
  be reviewed in weekly team meetings.

- All Developers should programmatically set the QUERY_TAG session
  parameter at the start of their CI/CD jobs, applications, or data
  pipelines. The tag should include context like the Git commit hash,
  feature name, or executing user (e.g., {'git_commit':'a1b2c3d',
  'feature':'new_customer_model'}).

- During code review, developers should be required to analyze the query
  profile for new, complex queries to identify performance bottlenecks
  before the code is merged into production.

This leverages Snowflake's rich metadata and governance features. Using
QUERY_TAG allows you to precisely attribute credit consumption to
specific features or changes, enabling true cost visibility.

### Persona responsibilities (RACI chart)

This RACI (Responsible, Accountable, Consulted, Informed) matrix
outlines the typical roles and responsibilities across the SDLC
lifecycle.

**Legend:** **R** = Responsible, **A** = Accountable, **C** = Consulted,
**I** = Informed

| Focus Area / Activity                 | Engineering | Data Science | SRE | Security | Architecture | C‑Level |
|---|---|---|---|---|---|---|
| Define SDLC toolchain & standards     | R | C | C | C | A | I |
| Set up Git repos & branching strategy | R | R | C | I | A | I |
| Develop & commit code/models          | R | R | I | I | C | I |
| Conduct peer code reviews                   | R | R | C | C | I | I |
| Build & maintain CI/CD pipelines            | R | C | A | C | C | I |
| Write unit & integration tests              | R | R | C | I | I | I |
| Manage environment provisioning (IaC)       | C | I | R | C | A | I |
| Execute production deployments              | A | I | R | C | I | I |
| Monitor production health & performance     | C | C | R | I | I | I |
| Respond to production incidents             | C | C | R | I | I | I |
| Optimize pipeline performance cost                           | R | R | A | I | C | I |
| Define & enforce security policies | C | C | C | A | R | I |

## Continuously improve performance & practices

### Overview

Continuously improving performance and operational practices is
essential for maximizing the value, efficiency, and innovation you get
from the Snowflake AI Data Cloud. It's not a one-time task but an
ongoing cycle of measurement, analysis, and optimization that ensures
your platform evolves with your business needs. This approach helps you
control costs, enhance user experience, and maintain a robust, scalable
data environment.

### Focus areas

To structure your improvement efforts, concentrate on these four key
areas. They provide a comprehensive framework for optimizing every
aspect of your Snowflake usage, from query execution to team expertise.

- **Workload optimization**: This involves tuning the technical aspects
  of your Snowflake environment to ensure that data engineering
  pipelines, analytics queries, AI models, and applications run as
  efficiently as possible. The goal is to improve speed and reduce
  resource consumption.

- **Cost governance and FinOps**: This area focuses on managing and
  optimizing your Snowflake spend. It involves monitoring usage,
  forecasting costs, setting budgets, and fostering a culture of
  cost-awareness across all teams. It's about treating cost as a
  critical performance metric.

- **Operational excellence**: This centers on automating and
  streamlining the processes used to manage your Snowflake environment.
  It includes CI/CD (Continuous Integration/Continuous Deployment) for
  code, infrastructure-as-code (IaC) for environment setup, monitoring,
  alerting, and incident response to ensure reliability and reduce
  manual effort.

- **Practice and skill enhancement**: This is the human element of
  continuous improvement. It involves keeping your teams' skills sharp
  and ensuring they follow best practices. A platform as dynamic as
  Snowflake requires continuous learning to leverage new features and
  capabilities effectively.

### Phase-based activities

Continuous improvement is a journey. By breaking it down into the four
distinct iterative phases of the Operational Excellence pillar, you can
apply focused effort at each stage of your project lifecycle.

### Prepare

In this phase, you lay the groundwork for success by defining goals,
standards, and metrics before a project begins.

- **Workload optimization**:

  - Define clear Service Level Objectives (SLOs) for critical workloads.

  - Estimate compute needs and select initial virtual warehouse sizes
    based on workload characteristics (e.g., small for data ingestion,
    large for complex transformations).

- **Cost governance and FinOps**:

  - Establish budgets and spending alerts for the new project using
    Snowflake's resource monitors.

  - Define a comprehensive tagging strategy to allocate costs accurately
    to different teams, projects, or cost centers.

- **Operational excellence**:

  - Define standards for monitoring, logging, and alerting for the new
    workload.

  - Plan your CI/CD and IaC strategy for managing Snowflake objects and
    code.

- **Practice and skill enhancement**:

  - Identify any new Snowflake features the project will use (e.g.,
    Snowpark, Streamlit) and arrange for team training.

### Implement

During the development and deployment phase, you turn plans into action,
with a focus on building efficient and manageable solutions.

- **Workload optimization**:

  - Use the **Query Profile** tool in Snowsight to analyze and tune
    complex queries during development.

  - Implement data clustering on large tables based on common query
    filter patterns to improve performance.

- **Cost governance and FinOps**:

  - Apply resource tags to all objects (warehouses, databases, etc.) as
    defined in the prepare phase.

  - Monitor development and testing costs to ensure they align with
    projections.

- **Operational excellence**:

  - Develop automated deployment pipelines for database objects, roles,
    and tasks.

  - Implement automated data quality and functional tests within your
    CI/CD process.

- **Practice and skill enhancement**:

  - Conduct regular peer code reviews to share knowledge and enforce
    best practices for SQL, Snowpark, and application code.

### Operate

Once a solution is live, the focus shifts to monitoring, maintenance,
and real-time optimization.

- **Workload optimization**:

  - Continuously monitor warehouse utilization using Snowsight
    dashboards to identify underutilized or overloaded warehouses.

  - Adjust warehouse settings dynamically, such as scaling up for peak
    demand, scaling out with multi-cluster warehouses for high
    concurrency, or suspending during idle periods.

- **Cost governance and FinOps**:

  - Review daily and weekly spend using the ACCOUNT_USAGE schema to
    track costs against budgets and identify anomalies.

  - Analyze storage costs and implement data lifecycle management
    policies.

- **Operational excellence**:

  - Respond to automated alerts for performance degradation or job
    failures.

  - Use Snowflake Tasks and Streams to automate data pipelines and
    reduce operational overhead.

- **Practice and skill enhancement**:

  - Encourage teams to participate in Snowflake webinars, workshops, and
    community forums to stay current.

### Improve

This proactive phase involves looking for opportunities to refine and
enhance your existing solutions and practices.

- **Workload optimization**:

  - Proactively analyze historical query performance data
    (QUERY_HISTORY) to find and refactor inefficient queries.

  - Experiment with advanced Snowflake features like the Search
    Optimization Service for point lookups or Query Acceleration Service
    for large-scale scans.

- **Cost governance and FinOps**:

  - Conduct quarterly FinOps reviews to analyze spending trends and set
    new optimization goals.

  - Optimize storage by identifying unused tables or converting large,
    transient tables to temporary ones where appropriate.

- **Operational excellence**:

  - Refine monitoring dashboards to provide more insightful, role-based
    views of platform health.

  - Automate repetitive operational tasks identified during the operate
    phase, such as user provisioning or access reviews.

- **Practice and skill enhancement**:

  - Establish a Center of Excellence (CoE) to formalize best practices,
    provide internal consulting, and drive platform adoption.

  - Invest in official Snowflake certifications to validate and deepen
    team expertise.

### Recommendations

### Proactively manage workload performance with observability tools

Don't wait for performance issues to arise. Empower your teams to use
Snowflake's built-in observability tools to find and fix inefficiencies
before they impact the business.

**Action for Engineering & Data Science**:

- **Analyze before you deploy:** During development, every complex or
  long-running query must be analyzed using the [**Query
  Profile**](https://docs.snowflake.com/en/user-guide/ui-query-profile).
  Use this tool to visually identify performance bottlenecks, such as
  inefficient joins, excessive data spillage to storage, or full table
  scans that could be avoided with better pruning.

- **Investigate historical performance:** Regularly review your team's
  most expensive or slowest queries from the past week using the **Query
  History** page in Snowsight. Look for performance regressions after a
  new release or changes in data volume.

**Action for SREs & Architects**:

- **Build centralized monitoring:** Create a dedicated Snowsight
  dashboard for platform health using data from the
  SNOWFLAKE.ACCOUNT_USAGE schema. Key views to monitor include
  QUERY_HISTORY (to spot slow queries), WAREHOUSE_LOAD_HISTORY (to see
  queuing), and WAREHOUSE_METERING_HISTORY (to correlate performance
  with cost).

- **Set performance benchmarks:** Use the data from these dashboards to
  establish performance Service Level Objectives (SLOs) for critical
  workloads and configure alerts that trigger when these SLOs are at
  risk.

### Implement a continuous compute optimization cycle

Virtual warehouse configuration is not a "set it and forget it" task.
Create a formal, data-driven process to ensure your compute resources
are always perfectly matched to your workloads.

**Action for Engineering Leads & SREs**:

- Establish a quarterly [warehouse
  review](https://docs.snowflake.com/en/user-guide/warehouses-considerations).
  Schedule a recurring meeting to review the performance and utilization
  of every production warehouse. Use the WAREHOUSE_LOAD_HISTORY view to
  answer key questions:

  - Is there queuing? A high AVG_RUNNING and AVG_QUEUED_LOAD value
    indicates the warehouse is undersized or needs a multi-cluster
    configuration.

  - Is it idle? If a warehouse has low utilization, consider resizing it
    down or consolidating its workloads with another warehouse.

- Automate suspension. Ensure every warehouse has an aggressive
  AUTO_SUSPEND setting (e.g., 60 seconds) to eliminate payment for idle
  compute time. This enforces an efficient "on-demand" practice.

**Action for Engineering & Finance (FinOps)**:

- Use [Resource
  Monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
  for governance. For each major workload or department, apply a
  Resource Monitor to its set of warehouses. This acts as a performance
  and cost circuit breaker, automatically notifying stakeholders or
  suspending compute when consumption exceeds its budget—often a sign of
  a runaway query or performance issue.

### Automate performance guardrails and operational tasks

Reduce manual effort and human error by embedding performance best
practices and operational duties directly into your automated workflows
and data pipelines.

**Action for SREs & DevOps Engineers**:

- **Automate performance regression testing:** As part of your CI/CD
  pipeline, use Snowflake's [Zero-Copy
  Cloning](https://docs.snowflake.com/en/user-guide/object-clone)
  feature to create an instantaneous, full-scale clone of your
  production data for testing. Before merging code, automatically run a
  suite of benchmark queries against this clone to ensure the changes do
  not negatively impact performance.

- **Manage warehouses as code:** Use an Infrastructure-as-Code (IaC)
  tool like Terraform to manage all virtual warehouse configurations.
  This enforces consistency and allows changes to warehouse sizing or
  scaling policies to go through a peer-reviewed, auditable process.

**Action for Data Engineers**:

- **Automate data pipelines with
  [Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)**:
  For any recurring data processing logic (e.g., merging data from a
  staging table, refreshing a materialized view), use Snowflake Tasks.
  This serverless tool removes the need for external orchestrators for
  many common workflows, improving reliability and reducing operational
  complexity.

### Foster a culture of continuous learning and excellence

Your team's expertise is the most critical factor in achieving sustained
performance. Invest in a structured program to keep skills sharp and
align everyone on best practices.

**Action for C-Level & Chief Architects**:

- **Charter and fund a Center of Excellence (CoE):** The CoE is
  accountable for platform-wide best practices. Its members must
  regularly evaluate new Snowflake features announced in the monthly
  [Release
  Notes](https://docs.snowflake.com/release-notes/all-release-notes?bundle=true)
  and create actionable guidance on how teams can use them to improve
  performance (e.g., adopting Query Acceleration Service, using
  Snowpark-optimized warehouses).

**Action for Team Leads & Engineers**:

- **Conduct performance-focused code reviews:** Make performance a
  mandatory part of every code review. Ask questions like: "Is there a
  WHERE clause to enable partition pruning?" or "Could this join be
  rewritten to be more efficient?"

- **Share knowledge actively:** Create an internal channel (e.g., Slack,
  Teams) dedicated to Snowflake performance. Encourage engineers to
  share their Query Profile screenshots, optimization successes, and
  tough performance challenges to foster [collaborative
  problem-solving.](https://community.snowflake.com/s/)

### Persona responsibilities (RACI chart)

Clarifying roles ensures that everyone understands their part in the
continuous improvement process. The matrix below outlines typical
responsibilities.



**Legend:** **R** - Responsible, **A** - Accountable, **C** - Consulted,
**I** - Informed

| Activity | C-Level (CIO/CDO) | Chief Architect | Engineering | Data Science | Security | SRE |
|---|---|---|---|---|---|---|
| Set platform budget & cost strategy | A | C | I | I | I | I |
| Define performance & architectural standards | A | R | C | C | C | C |
| Tune queries & optimize workloads | I | C | R | R | I | C |
| Monitor & adjust warehouse configuration | I | C | R | C | I | R |
| Develop & maintain CI/CD pipelines | I | C | R | C | I | A |
| Implement cost tagging & monitoring | I | A | R | R | I | R |
| Conduct regular FinOps reviews | A | R | C | C | I | C |
| Establish a Center of Excellence (CoE) | A | R | C | C | C | C |


