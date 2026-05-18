sidebar: true
sidebar_json: well-architected-framework
author: Well Architected Framework Team
id: well-architected-framework-ai-data-governance-lens
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: The AI & Data Governance Lens provides prescriptive guidance for organizations deploying AI/ML pipelines, agentic AI workloads, and data sharing scenarios subject to regulatory obligations on Snowflake.
environments: web
status: Published 



# AI & Data Governance Lens

## Overview

| Field | Description |
|-------|-------------|
| Scope | Snowflake deployments that store, process, or serve sensitive data (PII, PHI, PCI, financial data) in AI/ML pipelines, agentic AI workloads (Snowflake Intelligence), or data sharing scenarios subject to GDPR, CCPA, EU AI Act, or NIST AI RMF obligations |
| Target Audience | CISOs, Security DevOps practitioners, Data Governance Centers of Excellence, ML Engineers, Data Scientists, Data Engineers |
| Prerequisites | Core WAF pillars adopted; Snowflake Enterprise or Business Critical Edition; Snowflake Horizon Catalog available in account |
| Out of Scope | Non-Snowflake infrastructure security; application-layer authentication outside Snowflake sessions; SPCS workload hardening (covered separately); Unistore/Hybrid Table security patterns |

### Why This Lens Exists

Organizations face escalating financial and regulatory consequences when sensitive data is mishandled. At the same time, AI and machine learning workloads expand the attack surface: sensitive data enters pipelines at multiple stages, models become exfiltration targets, and agentic AI introduces new identity and authorization challenges not seen in traditional workloads.

The five core WAF pillars (Security & Governance, Operational Excellence, Reliability, Performance, Cost Optimization) provide universal guidance, but AI and data governance require more specific controls. The seven-stage ML pipeline (Source Data Sets → Enrichment → Model Development → Model Registry → Model Deployment → Auditing & Monitoring → Update/Retire) introduces distinct risks at each phase — including unclassified training data, data poisoning, model exfiltration, prompt injection, and cost harvesting. Agentic AI systems such as Snowflake Intelligence must ensure every session inherits — and is strictly limited by — the user's existing identity, roles, and data access policies. These requirements demand prescriptive guidance.

Regulatory pressure adds urgency. The EU AI Act defines four risk tiers, with significant obligations for High-Risk systems. The NIST AI RMF outlines four functions: Map, Measure, Manage, and Govern. GDPR Articles 25, 32, and 15–20 map directly to Snowflake controls, from data protection by design to the right to be forgotten. ISO/IEC 42001 requires documented AI risk management processes. Together, these frameworks require organizations to demonstrate — across the data and AI stack — that sensitive data is detected, classified, protected, audited, and disposable on demand.

### Design Principles

| # | Principle | Description |
|---|-----------|-------------|
| 1 | Defense-in-Depth | Layer security controls from the network perimeter inward: Network Policies → Authentication Policies → Identity & Access Management → RBAC → Classification & Tagging → Data Quality Policies → Column and Row Level Policies, with HA/DR, Auditing/Monitoring, and Encryption as cross-cutting foundations, Data Movement Policies |
| 2 | Shift-Left Governance | Classify and protect sensitive data before it enters any ML pipeline stage; never allow unclassified data to reach training, fine-tuning, or inference workloads |
| 3 | Policy Follows Data | Tags and associated protection policies travel with the data — automatically applied on classification and preserved through all data movement and sharing operations |
| 4 | Least Privilege for Agents and Models | Snowflake Intelligence sessions inherit the user's existing identity, role, and warehouse; agents cannot exceed those permissions; Cortex Analyst generates SELECT-only queries; masking, row access policies, and tokenization are automatically applied |
| 5 | Automate Governance at Scale | Rely on the three-step automatic workflow — Automatically Detect → Automatically Tag → Auto Apply Policy — to eliminate manual classification gaps as data volumes grow |
| 6 | Continuous Compliance | Continuously evaluate the account against EU AI Act, NIST AI RMF, GDPR, and ISO/IEC 42001 obligations using Trust Center scanners, audit views, and scheduled classification re-evaluation |

## Pillar Guidance

### Security & Governance

#### Overview

AI and data governance workloads extend the Security & Governance pillar in two directions simultaneously. First, they require hardening of the full Snowflake perimeter using Snowflake Horizon's seven-layer defense-in-depth stack. Second, they require that every stage of the ML pipeline be assessed for its specific attack surface and protected with stage-appropriate controls. Snowflake Horizon Catalog provides five built-in governance pillars — Security, Privacy, Access, Compliance, and Interoperability — that together form the technical foundation for satisfying regulatory obligations without exporting data to external tools.

#### Principles

- Deploy all seven layers of Snowflake's defense-in-depth in order: Network Policies → Authentication Policies → Identity & Access Management → RBAC → Classification & Tagging → Data Quality Policies → Column and Row Level Policies; supplement with HA/DR, Auditing/Monitoring, and Encryption as cross-cutting foundations
- Authenticate based on identity type: Human users → Federated SSO (SAML/OAuth); Programmatic service users → Key Pair with Network Policies; Fallback programmatic → PAT with Network Policies; Break-glass → Snowflake MFA; AI pipeline workloads → Workload Identity Federation (WIF)
- Use centralized user management system via SCIM to automatically provision and de-provision users and roles
- Classify and tag every sensitive data asset before it enters any ML pipeline; use SNOWFLAKE.DATA_PRIVACY.CUSTOM_CLASSIFIER for domain-specific categories (employee IDs, industry codes such as ICD-10)
- Apply stage-appropriate controls at every one of the seven ML pipeline stages based on its documented attack surface

#### Recommendations

| # | Recommendation | Description | Risk Level |
|---|---------------|-------------|------------|
| 1 | Deploy Snowflake Horizon Defense-in-Depth | Implement all seven security layers in order. For inbound: configure network policies restricting allowed IP ranges and/or enable private connectivity (AWS PrivateLink, Azure Private Link, GCP Private Service Connect for Business Critical Edition). For outbound: control egress to external models (Azure OpenAI, Amazon Bedrock) via External Access Integrations. Connections must be Protected, Encrypted, Resilient, and Authenticated. | High |
| 2 | Enforce Authentication Decision Tree | Require SAML/OAuth/MFA for all human users; enforce OAuth or Key Pair authentication for programmatic service accounts; Deprecate any password only authentication - use PAT with network policies as fallback; restrict Snowflake MFA to break-glass scenarios only. Enforce client type via Authentication Policies. Use SCIM for automated user/role lifecycle management. Deploy Workload Identity Federation (WIF) for AI pipeline service identities. | High |
| 3 | Enable Trust Center Scanners | Activate the free Security Essentials scanner package to detect MFA non-compliance and users without network policies. Enable the CIS Snowflake Foundations Benchmark scanner for expanded best-practice coverage. Enable the Threat Intelligence scanner to monitor for risky users. Trust Center provides cross-cloud security monitoring in a single pane to lower TCO and minimize escalation risk. | High |
| 4 | Deploy Auto-Classification Profile with auto_tag: true | Create a SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE with auto_tag: true, maximum_classification_validity_days: 30, and minimum_object_age_for_classification_days: 0. Associate the profile with all schemas containing sensitive data. This serverless capability automatically detects, tags (PII, PCI, PHI), and protects sensitive columns without manual orchestration. Tags and associated policies travel with the data. | High |
| 5 | Apply Column-Level Security and Row Access Policies | Implement Dynamic Data Masking (DDM) on all columns classified as IDENTIFIER or QUASI_IDENTIFIER. Use Row Access Policies (RAPs) for attribute-based access control (ABAC) on sensitive datasets. Apply tag-based policies so that masking follows classification tags automatically. | High |
| 6 | Enable Tri-Secret Secure (TSS/BYOK) on accounts with Highest-Sensitivity Data | For data requiring BYOK, configure Tri-Secret Secure using AWS KMS, Azure Key Vault, or GCP KMS. Snowflake's default encryption is AES-256 at rest with 30-day key rotation and TLS in transit — TSS adds a customer-managed encryption key as the third secret, so Snowflake cannot decrypt data without customer key participation. | High |
| 7 | Protect the ML Pipeline at Every Stage | Source Data Sets: classify and tag before ingestion; redact sensitive columns; control who/what can update training data. Enrichment: validate lineage; detect data poisoning via quality policies. Model Development: apply SecDevOps practices; use synthetic data for training and fine-tuning to avoid PII exposure. Model Registry: log models with tagging and versioning; restrict USAGE and OWNERSHIP privileges. Model Deployment: enable Cortex Guard (Llama Guard) for input validation and output encoding. Auditing & Monitoring: monitor for model poisoning, jailbreak attempts, and obsolete models. Update/Retire: retire models via Time Travel and crypto deletion. | High |
| 8 | Secure Snowflake Intelligence with Private Connectivity | For agentic AI workloads using Snowflake Intelligence: (1) Enable private connectivity and configure ALLOWED_INTERFACES to limit business user access to AI surfaces; (2) Verify that agent sessions inherit user identity, role, and warehouse — agents cannot exceed these permissions; (3) Configure RBAC for LLM access using account-level allowlists and role-level grants via CORTEX_USER, CORTEX_EMBED_USER, and CORTEX_AGENT_USER roles; (4) Confirm Cortex Analyst generates SELECT-only queries with masking/RAPs/tokenization automatically applied. | High |

#### Anti-Patterns

- Storing unclassified or unlabeled PII, PHI, or PCI data in training datasets — leaves attack surface open at the first ML pipeline stage
- Using password-based authentication for programmatic service accounts — deprecated and non-compliant; credentials are credential-stuffing targets
- Deploying AI models in the Model Registry without RBAC on USAGE and OWNERSHIP — enables unauthorized model access and model exfiltration
- Enabling Snowflake Intelligence without private connectivity — exposes agent traffic to public internet and eliminates network-layer protection
- Applying auto-classification once and never re-evaluating — classification validity expires; new tables added to a schema may be unclassified for weeks without a scheduled profile
- Granting CORTEX_USER to all roles indiscriminately — creates uncontrolled LLM spend and removes the ability to audit AI access by identity

#### Assessment Questions

- Are all seven layers of the Horizon defense-in-depth stack configured and validated?
- Is federated SSO (SAML/OAuth) enforced for every human user, with no active password-only accounts?
- Do you use secretless authentication for service users, or have a defined strategy for secret rotation if using key pair and PAT?
- Is an auto-classification profile deployed on all sensitive schemas with auto_tag: true and a maximum_classification_validity_days threshold set?
- Are all IDENTIFIER and QUASI_IDENTIFIER columns protected with Dynamic Data Masking or Row Access Policies?
- Is Tri-Secret Secure enabled for data classified as requiring BYOK/customer-managed encryption?
- Are Snowflake Intelligence agent sessions confirmed to operate within the inheriting user's RBAC perimeter?
- Has Trust Center Security Essentials been enabled and are all High-severity findings remediated?

### Operational Excellence

#### Overview

AI governance operations require MLOps lifecycle management, continuous automated classification, policy drift detection, structured incident response, and the ability to fulfill data subject rights (DSAR, Right to Erasure) on demand. Snowflake's Account Usage schema provides the audit visibility backbone; the Sensitive Data Incident Response process follows the NIST 6-phase IR model. Manual governance at scale is not viable — operational excellence in this lens means automating the detect-tag-protect lifecycle and ensuring that model and data artifacts have documented lineage and retirement procedures.

#### Principles

- Automate the Detect → Tag → Protect workflow via CLASSIFICATION_PROFILE associated with every sensitive schema
- Use Account Usage audit views (LOGIN_HISTORY, QUERY_HISTORY, ACCESS_HISTORY, OBJECT_DEPENDENCIES) as the foundation for continuous monitoring, not periodic manual review
- Implement and test a NIST 6-phase Incident Response process: Prepare → Identify → Contain → Eradicate → Recover → Lesson Learned
- Maintain model registry artifacts with versioning, tagging, lineage, and explicit retirement procedures
- Define DSAR and RTBF procedures before data goes into production, not after a request is received

#### Recommendations

| # | Recommendation | Description | Risk Level |
|---|---------------|-------------|------------|
| 1 | Schedule Auto-Classification Re-evaluation | Configure CLASSIFICATION_PROFILE with maximum_classification_validity_days: 30 on all sensitive schemas. This ensures that new tables are automatically classified within one day (minimum_object_age_for_classification_days: 0), and previously classified tables are re-evaluated monthly. Monitor classification results via SQL or the Snowsight governance UI. | High |
| 2 | Enable Account Usage Audit Views | Activate and query LOGIN_HISTORY for failed logins and unusual session activity; QUERY_HISTORY for sensitive data access patterns; ACCESS_HISTORY for column-level access tracking against tagged sensitive columns; OBJECT_DEPENDENCIES for tracking model registry and data pipeline lineage. Use ACCOUNT_USAGE views rather than INFORMATION_SCHEMA for complete historical retention. | High |
| 3 | Implement NIST 6-Phase Incident Response | Document and test: (1) Prepare — assign IR roles, establish runbooks for session/user/data/account containment; (2) Identify — use LOGIN_HISTORY and ACCESS_HISTORY to detect anomalous access; (3) Contain — suspend sessions/users, modify network policies, disable model endpoints as appropriate to the scope; (4) Eradicate — remove unauthorized access grants, retire compromised models; (5) Recover — validate that governance controls are reinstated; (6) Lesson Learned — update runbooks and classification profiles. | High |
| 4 | Establish Model Registry Governance | Log every model to the Model Registry with tagging (sensitivity level, data lineage, owner), versioning, and ML lineage tracking. Restrict USAGE to authorized roles and OWNERSHIP to designated model owners. Document retirement schedules. Monitor for obsolete models using OBJECT_DEPENDENCIES and ACCESS_HISTORY. | Medium |
| 5 | Implement DSAR and RTBF Procedures | Map data subject access rights to Snowflake controls: Right of Access (DSAR) → ACCESS_HISTORY to locate data subject records; Right to Erasure (RTBF) → Crypto Deletion of encryption keys, Dynamic Data Masking to block access immediately, TIME_TRAVEL retention window (0–90 days configurable) and FAIL_SAFE (7-day non-configurable) define deletion time frames. Restricting processing → Row Access Policies to block access without deletion. Document these procedures and test them annually. | Medium |
| 6 | Set Up Alerts and Notifications for Sensitive Data Events | Configure native Snowflake alerting using Data Metric Functions (DMFs) to monitor training data quality (null rates, anomaly detection, EXPECTATION clause). Set alerts on ACCESS_HISTORY for access to IDENTIFIER-classified columns by unexpected roles. Enable anomaly detection notifications for biased or inaccurate AI model outputs. | Medium |

#### Anti-Patterns

- Manual, ad-hoc classification triggered only when a compliance audit is scheduled — leaves newly created tables unprotected for extended periods
- No documented incident response plan for AI-specific threats (model poisoning, prompt injection, model exfiltration) — security teams default to general IR procedures that do not address ML-specific containment
- Deploying models without lineage tracking in the Model Registry — breaks the data supply chain audit trail required by EU AI Act and NIST AI RMF obligations
- Responding to DSAR requests by manually searching for PII across schemas — should be automated via ACCESS_HISTORY and classification tags

#### Assessment Questions

- Is the auto-classification profile configured with a maximum_classification_validity_days threshold and verified to be running on schedule?
- Are Account Usage audit views being queried for anomaly detection, and are alerts configured for sensitive column access?
- Has a NIST-based incident response playbook been documented and tested for AI-specific threat scenarios?
- Are model registry artifacts versioned, tagged, and traceable through ML lineage?
- Have DSAR and RTBF procedures been tested end-to-end, including crypto deletion and Time Travel time frame verification?

### Reliability

#### Overview

Governance controls must replicate alongside data — an account failover that loses network policies, SAML configuration, or role assignments effectively disables the entire security posture in the DR account. Snowflake Account Replication covers the full governance object set. Client Redirect reduces RTO from hours (or days for manual failover) to seconds, preserving continuous governance enforcement across regions.

#### Principles

- Replicate governance objects alongside data — never treat security policy replication as optional
- Design for sub-second RTO using Client Redirect rather than manual failover procedures
- Account for Time Travel and Fail-safe time frames when designing deletion and recovery workflows

#### Recommendations

| # | Recommendation | Description | Risk Level |
|---|---------------|-------------|------------|
| 1 | Configure Account Replication Including Governance Objects | Enable Account Replication to include: network policies, SAML configuration, roles and users, and SCIM configuration. This ensures that the DR account immediately enforces the same security posture as the primary account without requiring manual policy reconstruction post-failover. | High |
| 2 | Implement Client Redirect for Near-Zero RTO | Configure Client Redirect to point Snowflake driver and connector URLs to the current primary account. During failover, Client Redirect switches the active account in seconds — compared to hours or days required for manual DNS and application reconfiguration. This is critical for governance-sensitive workloads where prolonged access without enforced policies is unacceptable. | High |
| 3 | Design DSAR/RTBF Workflows with Time Travel and Fail-safe Awareness | Time Travel is configurable from 0 to 90 days (Enterprise Edition); Fail-safe provides an additional 7 days non-configurable. Data that must be deleted to satisfy RTBF requests remains recoverable during these windows. Crypto Deletion of the encryption key is the recommended RTBF mechanism for immediate effective deletion — physical deletion completes when Time Travel and Fail-safe windows expire. Document this time frame in DSAR procedures. | Medium |

#### Anti-Patterns

- Replicating data tables to DR accounts without replicating associated network policies, SAML configuration, and role assignments — creates a DR account with data but no enforced access controls
- Using manual DNS changes or application reconfiguration for account failover — results in RTO measured in hours, during which governance controls may be absent

#### Assessment Questions

- Does Account Replication configuration explicitly include network policies, SAML configuration, and role/user objects?
- Has Client Redirect been configured and tested with a documented RTO target?
- Are DSAR/RTBF procedures documented with explicit reference to Time Travel and Fail-safe time frames?

### Performance

#### Overview

AI workloads introduce inference latency, throughput, and compute sizing considerations that do not exist in traditional analytics workloads. Governance adds classification pipeline overhead that must be managed to avoid degrading production pipeline performance. The key principle is that governance automation — particularly serverless auto-classification and scheduled re-evaluation — should be configured to run during off-peak windows rather than on every query.

#### Principles

- Use dedicated virtual warehouses sized appropriately for inference workloads, separate from training and ETL workloads
- Configure auto-classification as a scheduled serverless operation, not a query-time trigger
- Minimize masking policy chain depth; avoid applying multiple overlapping policies to the same column

#### Recommendations

| # | Recommendation | Description | Risk Level |
|---|---------------|-------------|------------|
| 1 | Dedicate Warehouses for ML Inference vs. Training | Inference requires low-latency, consistent compute; training requires high-throughput burst compute. Separate these into dedicated virtual warehouses to prevent resource contention. Tag warehouses by workload type to enable cost attribution and governance of compute resources. | Medium |
| 2 | Optimize Classification Pipeline Performance | Use the serverless CLASSIFICATION_PROFILE rather than running SYSTEM$CLASSIFY manually in a large warehouse. Schedule classification during off-peak hours using Tasks. Avoid triggering re-classification on every table access — use the maximum_classification_validity_days parameter to control re-evaluation frequency. | Medium |
| 3 | Use Cortex Analyst's SELECT-Only Query Path for Performant AI Data Access | Cortex Analyst generates SELECT-only SQL queries and automatically applies the querying user's masking policies, Row Access Policies, and tokenization — without requiring any special query construction. This provides both performance predictability (no ad-hoc DML) and security enforcement (governance controls applied transparently). | Low |
| 4 | Monitor AI Inference Latency and Data Quality Together | Use Data Metric Functions (DMFs) to continuously monitor training data quality metrics (freshness, null rates, row count anomalies) alongside inference latency. Configure the EXPECTATION clause to alert when data quality thresholds are breached — degraded input data quality directly impacts model output reliability. | Medium |

#### Anti-Patterns

- Running full-schema SYSTEM$CLASSIFY on a large X-Large warehouse on every data ingestion event — classification is compute-intensive and should run on a schedule
- Chaining multiple masking policies on a single column — increases query execution time and makes policy intent opaque during audits

#### Assessment Questions

- Are ML inference and training workloads running on separate, appropriately sized virtual warehouses?
- Is auto-classification configured as a scheduled serverless operation rather than triggered on every access?
- Are Data Metric Functions deployed to monitor training data quality metrics that feed AI models?

### Cost Optimization

#### Overview

AI governance costs include classification compute, masking policy evaluation, LLM token usage through Cortex AI, and compliance audit storage. The largest cost risks are uncontrolled Cortex LLM spend (when CORTEX_USER is granted broadly) and running classification on large warehouses when serverless compute is sufficient. Aligning data retention periods with RTBF requirements avoids paying for storage that regulatory obligations require to be deleted.

#### Principles

- Use serverless auto-classification to avoid warehouse costs for governance workloads
- Control Cortex LLM token usage with account-level allowlists and role-level CORTEX_USER grants
- Align data retention settings with RTBF and DSAR obligations to avoid unnecessary storage spend

#### Recommendations

| # | Recommendation | Description | Risk Level |
|---|---------------|-------------|------------|
| 1 | Use Serverless Auto-Classification | SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE uses serverless compute — no virtual warehouse is required. This eliminates warehouse idle costs for governance operations and allows classification to run on a schedule without pre-provisioning compute. | Low |
| 2 | Control Cortex LLM Access to Prevent Runaway Spend | Grant CORTEX_USER, CORTEX_EMBED_USER, and CORTEX_AGENT_USER roles only to roles that have a documented, approved AI use case. Use the account-level LLM allowlist to restrict which models are accessible. Monitor Cortex AI token usage via QUERY_HISTORY. Uncontrolled CORTEX_USER grants create unpredictable AI inference spend — a cost harvesting attack vector identified in the ML pipeline threat model. | Medium |
| 3 | Start with Trust Center Security Essentials Before Purchasing Premium Packages | Trust Center Security Essentials is free and covers MFA compliance and network policy usage — the two most common High-severity findings in Snowflake accounts. Enable Security Essentials first, remediate all findings, then evaluate whether CIS Benchmarks or Threat Intelligence scanner packages provide incremental value for your risk profile. | Low |
| 4 | Set Data Retention Periods Aligned with RTBF Obligations | Configure TIME_TRAVEL retention to the minimum period required for operational needs. For data with RTBF obligations, use Crypto Deletion to satisfy immediate deletion requirements rather than relying on short Time Travel windows. Avoid retaining data beyond regulatory requirements — storage for data that should have been deleted is both a cost and a compliance risk. | Low |

#### Anti-Patterns

- Granting CORTEX_USER to SYSADMIN or PUBLIC roles — effectively gives all users unrestricted Cortex AI access, creating unpredictable token spend and eliminating the ability to audit AI use by identity
- Running SYSTEM$CLASSIFY on a Large or X-Large warehouse rather than using the serverless classification profile — an order-of-magnitude cost difference for classification operations

#### Assessment Questions

- Is auto-classification configured to use the serverless CLASSIFICATION_PROFILE rather than a warehouse?
- Are CORTEX_USER, CORTEX_EMBED_USER, and CORTEX_AGENT_USER roles granted only to approved roles with documented business justification?
- Have Time Travel retention periods been reviewed and set to the minimum required by operational and regulatory needs?

## Lifecycle Guidance

The AI and data governance workload follows a seven-stage ML pipeline lifecycle. Each stage has a distinct threat surface and requires stage-appropriate governance controls.

| Phase | Key Activities | Pillar Intersections |
|-------|---------------|---------------------|
| 1. Source Data Sets | Classify all training data using auto-classification profile before ingestion. Redact sensitive columns. Use Synthetic Data for training and fine-tuning to avoid exposing PII. Control who and what can update training data via RBAC and network policies. | Security & Governance, Operational Excellence |
| 2. Enrichment | Validate lineage for all enrichment feeds (Marketplace, third-party datasets). Run data quality checks using Data Metric Functions. Verify no new sensitive data has been introduced without classification. | Security & Governance, Reliability |
| 3. Model Development | Apply SecDevOps practices; scan code for vulnerabilities. Restrict who can push to the Model Registry via RBAC. Use synthetic data for training and fine-tuning. Apply Differential Privacy where available. | Security & Governance, Operational Excellence |
| 4. Model Registry | Log every model with versioning, tagging (sensitivity, owner, data lineage), and ML lineage. Restrict USAGE to approved roles; restrict OWNERSHIP to designated model owners. Monitor for broken model lineage and obsolete models. | Security & Governance, Reliability |
| 5. Model Deployment | Configure CORTEX_USER, CORTEX_EMBED_USER, CORTEX_AGENT_USER roles with least-privilege grants. Enable Cortex Guard (Llama Guard) for input validation and output encoding. Confirm private connectivity for Snowflake Intelligence agent traffic. Verify Cortex Analyst generates SELECT-only queries with governance controls applied. | Security & Governance, Performance |
| 6. Auditing & Monitoring | Query ACCESS_HISTORY for sensitive column access by unexpected roles. Monitor LOGIN_HISTORY and QUERY_HISTORY for anomalies. Deploy DMF-based alerting for data quality regressions. Monitor for model poisoning, jailbreak attempts, obsolete models, and model spamming. | Operational Excellence, Security & Governance |
| 7. Update/Retire | Retire models via Time Travel (configurable 0–90 days) and Crypto Deletion of encryption keys. Document retirement in Model Registry. Re-classify any residual data. Fulfill DSAR and RTBF requests using ACCESS_HISTORY to locate records. | Operational Excellence, Cost Optimization |

## Maturity Model

| Level | Name | Description |
|-------|------|-------------|
| 1 | Foundational | Manual, ad-hoc data classification; some sensitive columns untagged; password-based authentication still present for some service accounts; Trust Center not enabled; no documented incident response plan for AI threats; model registry in use but no tagging or lineage; no formal DSAR/RTBF procedures |
| 2 | Managed | Auto-classification profile deployed on all sensitive schemas with auto_tag: true; federated SSO enforced for all human users; key pair/PAT enforced for programmatic users; Dynamic Data Masking on IDENTIFIER columns; Trust Center Security Essentials enabled with High-severity findings remediated; structured IR plan documented covering AI-specific threats; model registry with versioning and tagging; DSAR/RTBF procedures documented |
| 3 | Optimized | Continuous classify-tag-protect automation across all schemas with scheduled re-evaluation; Tri-Secret Secure (BYOK) enabled for highest-sensitivity data; private connectivity enforced for all AI agent workloads; CORTEX_USER grants limited to approved roles with monitored usage; EU AI Act risk tier classification completed and mapped to Snowflake controls; ISO/IEC 42001 alignment documented; NIST AI RMF Map/Measure/Manage/Govern functions operationalized; DSAR and RTBF workflows automated and tested; Client Redirect configured with tested RTO of seconds; Account Replication verified to include all governance objects |

## Assessment Checklist

### Security & Governance

- All seven layers of Horizon defense-in-depth configured: Network Policies, Authentication Policies, IAM, RBAC, Classification & Tagging, Data Quality Policies, Column and Row Level Policies
- Private connectivity (PrivateLink) enabled for all AI and sensitive data workloads (Business Critical Edition)
- Federated SSO (SAML/OAuth) enforced for all human users; no active password-only accounts
- Key Pair or PAT with network policies enforced for all programmatic service users
- Authentication Policies deployed to enforce client type restrictions
- SCIM configured for automated user and role provisioning/de-provisioning
- Workload Identity Federation (WIF) deployed for AI pipeline service identities
- Trust Center Security Essentials enabled; all High-severity findings remediated
- SNOWFLAKE.DATA_PRIVACY.CLASSIFICATION_PROFILE deployed with auto_tag: true on all sensitive schemas
- Dynamic Data Masking applied to all IDENTIFIER and QUASI_IDENTIFIER classified columns
- Row Access Policies deployed for ABAC on sensitive datasets
- CORTEX_USER, CORTEX_EMBED_USER, CORTEX_AGENT_USER granted only to approved roles
- Snowflake Intelligence ALLOWED_INTERFACES configured; agent sessions verified to operate within user RBAC perimeter
- Tri-Secret Secure enabled for data requiring BYOK (Business Critical Edition)
- Cortex Guard enabled for model deployments using Cortex AI

### Operational Excellence

- Auto-classification profile scheduled with maximum_classification_validity_days: 30
- Account Usage audit views activated: LOGIN_HISTORY, QUERY_HISTORY, ACCESS_HISTORY, OBJECT_DEPENDENCIES
- Alerts configured for access to IDENTIFIER-classified columns by unexpected roles
- NIST 6-phase IR process documented and tested for AI-specific threat scenarios
- Model Registry artifacts include versioning, tagging, and ML lineage for all production models
- DSAR and RTBF procedures documented, including Time Travel and Fail-safe time frame disclosures
- Data Metric Functions (DMFs) deployed to monitor training data quality

### Reliability

- Account Replication configured to include network policies, SAML configuration, roles, and users
- Client Redirect configured and tested with documented RTO target
- DSAR/RTBF procedures reference Time Travel retention window and Fail-safe expiry dates

### Performance

- Separate virtual warehouses configured for ML inference vs. training workloads
- Auto-classification running as scheduled serverless operation, not on-query trigger
- Data Metric Functions monitoring key quality dimensions for AI training data

### Cost Optimization

- Serverless CLASSIFICATION_PROFILE in use (no warehouse assigned for classification)
- CORTEX_USER grants reviewed; usage monitored via QUERY_HISTORY
- Time Travel retention periods set to minimum required by operational and regulatory needs
- Trust Center Security Essentials enabled (free) before evaluating paid scanner packages

## References & Resources

| Resource | Type | Link |
|----------|------|------|
| Snowflake Horizon Trust Center | Documentation | https://docs.snowflake.com/en/user-guide/trust-center |
| Auto-Classification Profile | Documentation | https://docs.snowflake.com/en/user-guide/classify-auto |
| Dynamic Data Masking | Documentation | https://docs.snowflake.com/en/user-guide/security-column-ddm |
| Row Access Policies | Documentation | https://docs.snowflake.com/en/user-guide/security-row-row-access-policies |
| Tri-Secret Secure | Documentation | https://docs.snowflake.com/en/user-guide/security-encryption-manage-tss |
| Account Replication | Documentation | https://docs.snowflake.com/en/user-guide/account-replication-config |
| Snowflake Intelligence (Cortex Agents) | Documentation | https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agent |
| NIST AI Risk Management Framework | External | https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf |
| EU AI Act | External | https://www.europarl.europa.eu/doceo/document/TA-9-2024-0138_EN.html |
| ISO/IEC 42001 | External | https://www.iso.org/standard/81230.html |
