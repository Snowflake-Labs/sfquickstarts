author: Well Architected Framework Team
id: well-architected-framework-security-and-governance
categories: snowflake-site:taxonomy/solution-center/certification/well-architected-framework
language: en
summary: The Security & Governance pillar focuses on building a secure and compliant Snowflake environment by implementing the principles of the Confidentiality, Integrity, and Availability (CIA) triad. 
environments: web
status: Published 


# Security & Governance Pillar



## Overview

The Security & Governance pillar focuses on building a secure and
compliant Snowflake environment by implementing the principles of the
**Confidentiality, Integrity, and Availability (CIA)** triad. The
recommendations provided within this framework are based on the **Shared
Responsibility Model** and focus on the security controls that are the
customer's responsibility. The goal is to minimize security risks by
securing the Snowflake perimeter, using the principle of least privilege
for data access, responsibly deploying AI, and preparing for security
incidents.

## Principles

### Secure the perimeter

> A strong security perimeter is built using network, identity, and
> policy constructs. You should assess network traffic to and from your
> Snowflake accounts to ensure network and endpoint security are in
> place for all connections. For identities, leverage modern
> authentication and authorization flows and enforce conditional access
> policies for Snowflake accounts.

### Governance

> Governance in the security pillar is about enforcing, monitoring, and
> auditing data access, privacy, and compliance controls. This ensures
> that auditors can prove who can see what, and under what conditions.
> Broader governance concepts like data quality and lineage are
> addressed in other pillars.

### Responsible AI

> The rapid adoption of AI capabilities brings security concerns,
> particularly regarding the protection of sensitive data. It's crucial
> to use AI responsibly and ensure that AI deployments are secure within
> your Snowflake environment.

### Assume breach

> You must prepare for security events by having established **Cyber
> Security Incident Response Plans (CSIRP)** specifically for your
> Snowflake accounts. This includes creating playbooks with actionable
> tasks for different incident scenarios and conducting regular training
> and tabletop exercises. Continuous monitoring of Snowflake accounts
> for anomalous behavior is also vital.

## Recommendations

The following key recommendations are covered within each principle of
Security & Governance:

- **Shared Responsibility Model**

  - Reliability and security are shared responsibilities between the
    cloud provider, Snowflake, and the customer. The **Shared
    Responsibility Model** outlines this division of responsibilities
    and is the foundation for all security recommendations. It is
    essential for customers to understand, document, and operationalize
    these specific responsibilities to prevent gaps in security
    ownership. You can find more information about this model in the
    Snowflake documentation:
    [/en/resources/report/snowflake-shared-responsibility-model/](/en/resources/report/snowflake-shared-responsibility-model/)

- **Network Security**

  - You can build a strong security perimeter by using **network
    policies** to control network traffic to your Snowflake account.
    Network policies are a crucial first step in securing your
    environment by allowing or denying user access based on their IP
    address. It is a best practice to define a clear set of network
    policies that restrict access to only trusted IP addresses or IP
    ranges. For more advanced network control, consider using features
    like Snowflake's Private Connectivity options.

- **Authentication & Authorization**

  - Authentication and authorization are fundamental to securing your
    Snowflake environment. You should use **Role-Based Access Control
    (RBAC)** to manage user permissions and ensure that each user has
    the minimum level of access required to perform their job duties, a
    principle known as **least privilege**. Modern authentication
    methods like federated authentication with SSO (Single Sign-On)
    should be used whenever possible to simplify user management and
    improve security.

- **Data Protection**

  - Data protection involves implementing controls to protect sensitive
    data at rest and in transit. Snowflake provides native features like
    **Default Encryption at Rest** and **Client-Side Encryption**. You
    can enhance this with **Customer-Managed Keys (CMK)** using
    Snowflake's integration with cloud provider key management services.
    Additionally, features such as **Time Travel** and **Fail-safe**
    provide data protection and recovery from logical errors by allowing
    you to restore data to a previous state. For more details, see the
    documentation on [Time
    Travel](https://docs.snowflake.com/en/user-guide/data-time-travel).

- **Data Governance**

  Data governance ensures that data access, privacy, and compliance
    controls are enforced, auditable, and monitored. This includes the
    use of **Dynamic Data Masking** and **Row Access Policies** to
    control who can see what data under what conditions.
    **Classification** and **Object Tracking** are also critical for
    identifying and protecting sensitive data and maintaining data
    lineage.

- **Incident Response**

  Having a well-defined **Cyber Security Incident Response Plan
    (CSIRP)** is vital for preparing for security events. The plan
    should include playbooks with actionable tasks and should be
    regularly tested through tabletop exercises to ensure effectiveness.
    Regular monitoring for anomalous behavior in your Snowflake accounts
    is key to early detection and rapid response to potential incidents.

## Secure the Perimeter

### Overview

Securing the perimeter of a Snowflake environment is crucial for
protecting data and maintaining business continuity. A well-architected
framework for this involves a multi-layered approach that addresses
network policies, identity and credential management, and authentication
hardening. By implementing these controls, you can ensure that access to
your data platform is strictly controlled, external threats are
proactively blocked, and your organization is resilient against
potential security breaches.

### Recommendations

**Hardening the perimeter and network access**

Implementing **Network Policies** is a critical first step to securing
your Snowflake environment. These policies, such as Network ACLs, should
be used to restrict connections to your data platform from only approved
and trusted IP ranges. Proactively mitigating data exfiltration pathways
is also essential; this involves securing external stages, restricting
outbound connectivity, and actively monitoring for high-volume data
egress. You can significantly reduce your attack surface by utilizing a
combination of user-level and account-level network policies.
Account-level policies prevent the use of stolen credentials from
exploited IP addresses and ensure all users access the platform from
known IPs. User-level policies can be used to prevent end-users from
using service accounts and allow for enforced exceptions to
account-level policies. For further information, see the Snowflake
documentation on network policies.

**Identity and credential management**

A robust security posture requires the **elimination of static
credentials** across your organization. Instead, you should mandate the
adoption of modern authentication flows like SAML, Key Pair, and OAuth
for all identities, including human users, service accounts, and
machine-to-machine processes. This approach minimizes the risk of
credentials being compromised. It's also vital to establish a
**Privileged Access Management (PAM) program** to govern, monitor, and
strictly control access for administrative and high-privilege roles.
This process helps to mitigate the risk of misuse of administrative
access. A formal process should exist for granting, reviewing, and
revoking high-privilege access, ideally with a tool to manage and
monitor these administrative sessions.

**Hardening authentication**

Enforcing **Multi-Factor Authentication (MFA)** is a key recommendation
for hardening your Snowflake environment. Snowflake supports various MFA
methods, including TOTP (Time-based One-Time Password) authenticator
apps like Microsoft and Google Authenticator, as well as Passkeys and
DUO, the only method with a "Push" notification option. It's recommended
to avoid SMS as a fallback to prevent SIM swapping attacks by selecting
the "Tablet" option in DUO instead of "Phone". Additionally, you should
implement **Workload Identity Federation (WIF)**, allows
for service-to-service authentication method
that lets workloads, such as applications, services, or containers,
authenticate with Snowflake using their cloud provider’s native identity
system, such as AWS Identity and Access Management (AWS IAM) roles,
Microsoft Entra ID (Managed Principles), and Google Cloud service
accounts to get an attestation that Snowflake can use and validate.

## Data Governance

### Overview

The Governance principle defines how sensitive data is accessed,
protected, and proven compliant. In Snowflake, this means translating
business rules into enforceable controls: masking and row policies,
projection constraints, role hierarchies, and auditable evidence, so
that teams can state with confidence who can see what, under what
conditions, and how that access is monitored. Governance is most
effective when it is automated and observable: tags drive policy
attachment, Access History substantiates usage, and dashboards highlight
drift and exceptions. The broader disciplines of lineage, quality, and
continuous improvement are addressed across other pillars, but their
outcomes are strengthened by a sound governance baseline here.

### Desired outcome

A well‑architected governance posture lets organizations demonstrate that sensitive data is consistently classified and protected across environments, access is role‑based and least‑privilege, row‑level and projection rules limit exposure to the minimal necessary surface, AI/LLM interactions are scoped and logged, and regulatory obligations are mapped to Snowflake‑native controls with reproducible evidence. When governance operates in this manner, audit readiness becomes routine and does not hinder delivery.

### Common anti-patterns

Weak governance often shows up as direct user‑to‑role grants without
federation, unmasked PII in widely used datasets, manual access reviews
that miss drift, agentic/LLM activity that is neither logged nor
constrained, and uncontrolled role/object growth that accumulates
technical debt. These patterns increase the likelihood of over‑exposure
and complicate audits.

### Benefits

A cohesive approach reduces breach and compliance risk, accelerates
onboarding and offboarding through automated RBAC, improves trust in
analytics and AI and shortens audit cycles by turning control checks
into repeatable queries and evidence packs. Teams gain faster access to
the right data because policies are pre‑bound and self‑enforcing.

### Risks

Absent these practices, unauthorized access to sensitive data becomes
more likely, regulatory obligations become hard to prove and model or
agent outputs may inadvertently reveal protected information. Over time,
unmanaged roles and objects increase operational drag and obscure
ownership.

### Recommendations

Start by defining a policy model in business terms:
what constitutes sensitive information, who requires access, and what
contextual factors must be considered (role, location, purpose). Express
those rules as tags and policies in Snowflake. Classify sensitive
columns, apply masking and row access policies that reference tags, and
route consumption through curated views with explicit projection
constraints. Integrate with an Identity Provider so users receive
privileges via roles, not direct grants. Enable Access History and
utilize Account Usage to create governance dashboards. Schedule drift
detection to flag untagged columns, unused or over‑privileged roles, and
detached policies. Finally, connect obligations (GDPR, HIPAA, PCI, SOX)
to the specific Snowflake controls and the queries that produce
evidence.

**Recommendation checklist**

1.  Define RBAC hierarchy

2.  Classify/tag sensitive datasets, bind masking &
    RAP policies

3.  Enable **Access History** and build audit
    dashboards

4.  Automate drift detection (orphan roles, untagged
    columns, policy detachment)

5.  Configure **Cortex AI governance** (prompt
    logging, redaction, agent scope)

6.  Build control-to-query library for regulatory
    evidence

7.  Review governance scorecard quarterly (coverage,
    exceptions, audit readiness)

### Data privacy & protection

#### CLS (column‑level security)

[Column‑level
security](https://docs.snowflake.com/en/user-guide/security-column-ddm-intro)
protects sensitive attributes with masking policies that adapt to
context. In practice, tags like SENSITIVITY and REGULATORY_SCOPE travel
with columns and trigger masking automatically, while session attributes
such as role, network location, or declared purpose inform whether data
is shown in the clear or redacted. Deterministic masking can preserve
joinability where required, and clear‑text access can be logged via
secure UDF patterns when justified. In regulated scenarios, tokenization
may be necessary; it should be paired with strict stewardship and
evidence of necessity.

**Design approach**
Keep base tables secured and expose consumers to policy‑protected views.
Separate administrative personas from analytical personas to avoid
privilege creep and ensure least privilege.

**Assessment Prompts**
Which roles can view clear PII, and under what context? How are
exceptions time‑boxed, tracked, and reviewed?

#### RAP (row access policies)

[Row access
policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
constrain visibility at the record level based on attributes like
geography or line of business. Centralizing rules in secure UDFs and
driving entitlements from reference tables makes policies explainable
and maintainable. Performance should be validated against real
workloads, and pruning/clustering strategies used where helpful.

**Design Approach**
Adopt a hub‑and‑spoke model: one policy per domain, so all child tables
and views inherit the same semantics through tags.

**Assessment Prompts**
Are RAP rules managed from a single source of truth rather than embedded
in views? What are the policy evaluation latency and cache hit rates
under load?

#### Projection policy

[Projection
controls](https://docs.snowflake.com/en/user-guide/projection-policies)
define which columns (or combinations of columns) may be selected
together, preventing risky joins (e.g., date of birth with ZIP and
gender). Express these rules in curated secure views and verify them in
CI so prohibited projections never reach production. Pair projection
constraints with
[masking](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
and row access for layered protection.

**Design Approach**
Publish approved column bundles per persona and provide redaction views
for common but risky analytics patterns.

**Assessment Prompts**
Which disallowed column combinations are blocked today? How are
projection constraints tested and reported in CI pipelines?

### Regulatory & compliance

Regulatory alignment translates legal obligations into concrete
Snowflake controls and reproducible evidence. A practical way to manage
this is to maintain a control catalog that maps each clause (for GDPR,
[HIPAA](https://medium.com/snowflake/how-snowflake-helps-with-hipaa-compliance-8e578f353b1a),
PCI, SOX, and others) to the tags, policies, and queries that
demonstrate enforcement. Evidence should be generated from Access
History and Account Usage on a schedule, producing consistent,
reviewer‑ready artifacts. For high‑risk data, segment databases and
schemas and apply stricter RAP and masking baselines. This keeps audits
predictable and allows quick re‑generation of a full evidence set -
ideally in hours rather than weeks.

**Assessment Prompts**
For each regulation, which Snowflake controls satisfy which clauses? How
quickly can a complete evidence pack be re‑built, and how is its
freshness tracked?

### Monitoring & reporting

Monitoring proves that controls are effective and alerts teams to drift.
A governance control center, implemented in Snowsight or an external BI
tool, should surface tagging and masking coverage, access to sensitive
data, RAP evaluations, share usage, data quality scores, and the
freshness of audit evidence. Alerting should detect untagged new
columns, policy detachments, anomalous access, and changes to external
shares. For AI/LLM, track prompt volumes, redactions, tool usage, and
violations. Behind the scenes, a metrics lake pulls data from Account
Usage, Information Schema, and Access History. Tasks and
[notifications](https://docs.snowflake.com/en/sql-reference/account-usage)
drive alerts, and exception workflows integrate with ticketing, ensuring
each alert has an assigned owner, runbook, and SLA.

**Assessment Prompts**
Which risks are trending, which alerts produce action, and what is the
false‑positive rate? Are owners and remediation steps clearly defined in
every alert type?

### **Sample Governance Scorecard**

- Coverage of tagged sensitive columns

- Percentage of policy‑protected assets

- Number of sensitive reads

- RAP evaluations

- Policy exceptions

- MTTR for data‑quality and policy incidents

- Evidence freshness

Treat these as quarterly OKRs and use them to prioritize automation that
removes recurring toil.

## Responsible AI

### Overview

Responsible AI is a crucial component of a comprehensive AI strategy,
ensuring that AI is developed and used in a manner that aligns with an
organization's core values. It involves a commitment to harnessing the
transformative impact of AI to positively contribute to society. A
well-architected Responsible AI plan leverages key principles to manage
risks, uphold trust, and maintain compliance, ensuring that your
organization is prepared for the security and ethical challenges that
arise from using AI. For a detailed overview of Snowflake's commitment
to Responsible AI, refer to [this
statement](/en/company/responsible-ai/).

### Desired outcome

By implementing a robust Responsible AI strategy, your organization can
confidently innovate with AI while mitigating risks associated with
prompt injection, insecure output handling, and data poisoning. This
enables you to safeguard sensitive information, maintain customer trust,
and fulfill regulatory requirements. Following these recommendations
ensures your data platform is resilient against AI-specific threats, and
your business is prepared for the ethical and security challenges of AI
adoption.

### Recommendations

**Alignment to OWASP Top 10 for LLM Applications**

Aligning with the [OWASP Top 10 for Large Language Model (LLM)
Applications](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
is a fundamental best practice for a robust AI security posture. This
framework provides a comprehensive list of the most critical security
risks associated with LLMs, such as Prompt Injection, Insecure Output
Handling, and Training Data Poisoning. It is paramount to address these
threats to protect your applications and data. We recommend that you use
the OWASP guidelines as a checklist to assess and mitigate risks in your
AI implementations, ensuring that your security controls are
comprehensive and up-to-date.

**Role-Based Access Control (RBAC)**

User and Model RBAC provides granular control over who can access and
use specific AI models and data objects. This is a critical security
measure because it helps enforce the principle of least privilege,
ensuring that users and applications only have the permissions necessary
to perform their tasks. For example, Model RBAC can be used to create
allow-lists or deny-lists for specific models, providing an extra layer
of control over which LLMs are approved for use within your
organization. We recommend leveraging the granular roles and
entitlements available to tightly scope access, ensuring that all
interactions are logged and auditable.

**Cortex Guard**

Cortex Guard is a powerful control that helps protect against common LLM
vulnerabilities like Prompt Injection and Insecure Output Handling. It
functions by performing input validation and output encoding to sanitize
potentially malicious content before it can be executed or cause harm.
The importance of this feature cannot be overstated, as it provides a
critical defense against threats that could lead to data exfiltration or
code execution. We recommend enabling Cortex Guard to automatically
sanitize and encode outputs, thereby reducing the risk of security
vulnerabilities and simplifying the recovery process by eliminating the
need for manual sanitization.

**Auditing & observability**

Auditing and observability are essential for monitoring AI interactions,
detecting anomalies, and ensuring compliance. By logging all
authorization decisions, agent interactions, and LLM prompt traffic, you
can maintain a clear audit trail for traceability and non-repudiation.
The QUERY_HISTORY view, for example, logs function calls and
inferencing, providing a record of all AI-related activities. We
recommend leveraging Snowflake's auditing features to monitor AI usage
and ensure that all activities are aligned with your security and
compliance policies. You should also explore functions like
SYSTEM\$CORTEX_ANALYST_REQUESTS to extend real-time visibility for your
administrative and compliance teams.

### Responsible AI Checklist

1.  Align your AI strategy with the **OWASP Top 10 for LLM
    Applications** to identify and prioritize security risks.

2.  Establish **User and Model RBAC** to control access to AI models and
    data objects, ensuring least privilege is enforced.

3.  Leverage **Cortex Guard** for input validation and output encoding
    to protect against common LLM vulnerabilities.

4.  Utilize **Auditing and Observability** tools, such as the
    QUERY_HISTORY view, to monitor and log all AI interactions.

## Assume Breach

### Overview

Organizations commonly have Cybersecurity Incident Response Plans
(CSIRP) that document and outline how they respond to and recover from
security incidents. Snowflake customers should have cybersecurity
incident response plans in place for handling and responding to
cybersecurity incidents that may compromise the confidentiality,
integrity and availability of their Snowflake Accounts in accordance
with industry standards.

### Recommendations

To be best prepared to deter and respond to threats, consider the
following recommendations based on industry best practices. These
recommendations are important to assess security posture, minimize
damage and downtime, prevent future threats, and protect reputational
brands. The following recommendations are aligned to industry standards
(eg. [NIST 800-61, Rev. 2- Computer Security Incident Handling
Guide](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final),
[SANS 504-B Incident Response
Cycle](https://www.sans.org/media/score/504-incident-response-cycle.pdf),
[MITRE ATT&CK Framework](https://attack.mitre.org/), MITRE
[SaaS
Matrix](https://attack.mitre.org/matrices/enterprise/cloud/saas/),
[Snowflake’s Security & Trust
Center](/product/security-and-trust-center/)
& [Snowflake CIS
Benchmarks](https://www.cisecurity.org/benchmark/snowflake)).

**Cybersecurity Incident Response Planning**

A Cybersecurity Incident Response Plan (CIRP) is a procedural framework
for properly handling and responding to cybersecurity incidents that
could compromise the confidentiality, integrity, and availability of
data and business operations. The purpose of a CIRP is to minimize the
adverse impact on business operations, quickly restore normal service,
assist in meeting contractual and regulatory obligations, and protect
sensitive data. A CIRP provides a clear strategy and a set of rules for
an organization to follow, ensuring that all stakeholders know their
roles and responsibilities during a security event. Organizations must
consult with their internal security and legal teams to align the plan
with their specific program requirements.

**SANS Incident Response Phases**

The [SANS Incident Response
Phases](https://www.sans.org/security-resources/glossary-of-terms/incident-response)
are a structured, six-step cycle for handling cybersecurity incidents.
This framework provides a standardized and repeatable process for
incident handling, which is crucial for a swift and effective response.
By following these phases—Preparation, Identification, Containment,
Eradication, Recovery, and Lessons Learned—your organization can ensure
that all necessary actions are taken in a logical order, from
pre-incident readiness to post-incident analysis. We strongly advise
that your incident response team members receive training on these
phases and are provided with the necessary access and tools to perform
their duties effectively.

**Shared Responsibility Model**

The Shared Responsibility Model defines the specific security
obligations of both the customer and Snowflake. Understanding this model
is critical for effective cybersecurity, as it clarifies which security
controls you are responsible for implementing and managing, such as
protecting against social engineering, hardening account configurations,
and managing access controls for sensitive data. We recommend you use
this model to conduct a thorough risk assessment and ensure that your
own Governance, Risk, and Compliance teams are aligned with their
responsibilities in securing your Snowflake deployment.

**Identity & Access Management (IAM)**

Identity & Access Management (IAM) is a security discipline that ensures
the right individuals and applications have the right access to the
right resources at the right time. Implementing a robust IAM strategy is
paramount to preventing unauthorized access and mitigating the risk of
credential compromise. We recommend enforcing modern authentication
protocols, such as SAML 2.0, for human users and OAuth or Key Pair
authentication for programmatic use cases, to minimize the use of static
credentials. Additionally, apply the Principle of Least Privilege,
ensuring users and roles have only the minimum permissions necessary to
perform their duties, and limit the number of users with the powerful
ACCOUNTADMIN role.

**Network security**

Network security involves the use of policies and controls to protect
your network and data from unauthorized access and cyberattacks. This is
important for minimizing your attack surface and preventing data
exfiltration. Snowflake provides customer-configurable Network Policies
and Network Rules that can restrict access to specific IP ranges (CIDR
blocks), effectively terminating public access to your Snowflake
account. We advise you to leverage private networking services provided
by cloud providers to ensure all traffic remains within a trusted,
private network. All traffic to Snowflake is encrypted in transit using
TLS 1.2, providing confidentiality and data integrity.

**Data exfiltration mitigations**

Data Exfiltration Mitigations are controls designed to prevent or
monitor the unauthorized transfer of data out of your Snowflake
environment. Data exfiltration poses a significant risk to data
confidentiality and can lead to severe business consequences. Snowflake
provides account-level parameters that can prevent ad-hoc data unload
operations to external stages and require the use of a storage
integration object for stage creation and operations. It is a best
practice to enable these preventative controls to limit data movement
and supplement them with continuous monitoring of privileged objects to
detect suspicious activity. For more information, please see the
Snowflake documentation on [preventing data
exfiltration](https://docs.snowflake.com/en/user-guide/security-encryption-exfiltration-prevention).

**Tri-Secret Secure & Data Replication**

Tri-Secret Secure is a security feature that provides an additional
layer of data protection by enabling you to manage your own
customer-managed key (CMK). This capability is essential for managing
risk in an "assume breach" scenario, as revoking the CMK will prevent
the decryption of all customer data objects at the account level. We
recommend that you also enable data replication to a secondary account
to support your business continuity plan. This allows for rapid recovery
in a disaster recovery scenario, ensuring you can meet your Recovery
Time Objective (RTO) and Recovery Point Objective (RPO) requirements.

## Identify and assess threat

### Identification phase - audit

1.  Access your **Account Usage** database, which provides 365 days of
    "tamper proof" audit logs.

2.  Use the QUERY_HISTORY and ACCESS_HISTORY views to investigate a
    potentially compromised user.

3.  Query the QUERY_HISTORY view to identify any unauthorized changes,
    such as privilege escalation, security configuration changes, or
    data object modifications.

4.  Correlate the compromised user's activity with known threat
    intelligence feeds to identify potential malicious activity.

### Containing Impact

1.  **Containment:** Immediately disable the identified user account or
    integration to prevent further compromise.

2.  **Eradication:** Perform a detailed forensic analysis by reviewing
    audit logs to ensure the initial compromise is fully contained and
    the threat is removed.

3.  **Recovery:** Restore normal business functionality by leveraging
    **Time Travel** to recover from unintended data object changes.
    Alternatively, use replicated data objects in a secondary account to
    restore service in a multi-region redundancy scenario.

## Tradeoffs & considerations

Use the following checklist to assess your organization's readiness for
handling a cybersecurity incident:

- **Incident response plan:** Is a formal CSIRP in place that aligns
  with industry standards like NIST and SANS?

- **Security features:** Have you implemented Snowflake's recommended
  security features, such as network policies, multi-factor
  authentication (MFA), and data classification?

- **Audit & monitoring:** Do you have a process to regularly audit and
  monitor Snowflake's Account Usage logs for indicators of compromise
  (IoCs) and security anomalies?

- **Tabletop exercises:** Do you conduct regular "tabletop" exercises to
  test your CIRP and ensure your team can execute the plan efficiently
  under pressure?

- **Postmortem & lessons learned:** Do you have a structured process for
  conducting a postmortem analysis of all security incidents and false
  positives to improve your threat model and security architecture?
