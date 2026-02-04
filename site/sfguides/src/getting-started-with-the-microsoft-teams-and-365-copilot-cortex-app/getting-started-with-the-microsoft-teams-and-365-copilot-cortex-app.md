author: Matt Marzillo, Mary Law
id: getting-started-with-the-microsoft-teams-and-365-copilot-cortex-app
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: This is a quickstart showing users how use the Microsoft Teams and M365 Copilot Cortex App 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Getting Started with The Microsoft Teams and M365 Copilot Cortex App



## Overview 

The Microsoft M365 Copilot and Snowflake Cortex Agents integration simplifies AI-powered data interactions so that both technical and business users can interact with their structured and unstructured data using natural language. Direct access to Cortex Agents from Microsoft M365 Copilot makes it possible to combine powerful generative AI data agents with secure data in Snowflake, unlocking endless business efficiencies for every organization, from faster customer support to optimized supply chain operations.

In this quickstart, you’ll learn to build a Snowflake Cortex Agent App and connect to it from  Microsoft Teams or Microsoft M365 Copilot. After setting up the Snowflake Environment there will be a section for configuring the app connectivity followed by a use case showing how to run the application depending on your role and desired outcomes.

Snowflake Cortex Agents orchestrate across both structured and unstructured data sources to deliver insights. They plan tasks, use tools to execute these tasks, and generate responses. Agents use Cortex Analyst (structured) and Cortex Search (unstructured) as tools, along with LLMs, to analyze data. Cortex Search extracts insights from unstructured sources, while Cortex Analyst generates SQL to process structured data. A comprehensive support for tool identification and tool execution enables delivery of sophisticated applications grounded in enterprise data.

The Microsoft Teams and  M365 Copilot app is an AI-powered productivity assistant integrated into Microsoft Teams and Microsoft M365 Services (Word, Excel, Outlook, etc.). It's part of Microsoft’s broader Copilot ecosystem, which embeds generative AI into everyday work apps and can connect to services like Snowflake Cortex Agents.

CURRENTLY THIS IS AVAILABLE IN ALL SNOWFLAKE PUBLIC CLOUDS AND REGIONS

### Use Case
In this use cases we will build two data sources, one with structured sales data and another with unstructured sales call data. Then we will create a Cortex Agent that uses Search (for unstructured data) and Analyst (for structured data) then wrap a Cortex Agent around it so that it can combine both the services in a unified agentic experience. This can then be used by Copilot leveraging oauth authentication and triggered by a simple phrase in your Microsoft Copilot to access sales data easily with plain text questions.

Snowflake Cortex has proven to be a best-in-class platform for building GenAI services (Search and Analyst) and agents with your data and now customers can seamlessly connect to Cortex Agents in Microsoft Teams and M365 Copilots alongside all of their Microsoft GenAI experiences.

### Prerequisites
- Familiarity with [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) and a Snowflake account
- A Microsoft Teams account or M365 Copilot (with administrator privileges if following that section)

### What You’ll Learn
- Creating Snowflake Cortex Services for Search, Analyst and Agents
- Securely connecting Microsoft Teams and M365 Copilot App to Cortex Agents
- Using the Microsoft Teams and M365 App with Cortex Agents!

First we will build a simple Cortex agent that leverages Analyst and Search Services on structured and unstructured data respectively.

![](assets/agentarch.png)

Next, we will configure connectivity to connect the Microsoft Teams/ M365 Copilot App to Cortex then use it, with the underlying architecture like below. 
![](assets/cortexteamsarch.png)
The authentication and user flow goes like this:

1. User authenticates to Entra ID and via the Bot Resource to authenticate into their Snowflake Account.
2. The user then interacts with the MS app and the Bot Resource sends the request, along with the token from step 1, to the Bot backend with the user.
3. The Bot Backend stores and retrieves the tenant level configuration and prompts the Cortex Agent API and executes queries against the SQL API when needed.
4. Responses traverse through the Bot Backend, through the Bot Resource back to the application and to the user.

...

### What You’ll Need
- [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) 
- A Microsoft Teams account or M365 Copilot (with administrator privileges if following that section)

### What You'll Build
- A Snowflake Search Service
- A Snowflake Analyst Service
- A Snowflake Agent
- A Microsoft Teams or M365 Copilot App that connects to the Cortex Agent

<!-- ------------------------ -->
## Setup Snowflake

Copy and paste the code below into a Snowflake Worksheet to create the following:
1. A dataset with unstructured data on sales conversations.
2. A Cortex Search Service with that unstructured data.
3. A structured dataset with deal metrics.

```sql
-- Create database and schema
CREATE OR REPLACE DATABASE sales_intelligence;
CREATE OR REPLACE SCHEMA sales_intelligence.data;
CREATE OR REPLACE WAREHOUSE sales_intelligence_wh;

-- Create tables for sales data
CREATE TABLE sales_conversations (
    conversation_id VARCHAR,
    transcript_text TEXT,
    customer_name VARCHAR,
    deal_stage VARCHAR,
    sales_rep VARCHAR,
    conversation_date TIMESTAMP,
    deal_value FLOAT,
    product_line VARCHAR
);

CREATE TABLE sales_metrics (
    deal_id FLOAT PRIMARY KEY,
    customer_name VARCHAR,
    deal_value FLOAT,
    close_date DATE,
    sales_stage VARCHAR,
    win_status BOOLEAN,
    sales_rep VARCHAR,
    product_line VARCHAR
);

-- First, let's insert data into sales_conversations
INSERT INTO sales_conversations 
(conversation_id, transcript_text, customer_name, deal_stage, sales_rep, conversation_date, deal_value, product_line)
VALUES

('CONV001', 'Initial discovery call with TechCorp Inc''s IT Director and Solutions Architect. Client showed strong interest in our enterprise solution features, particularly the automated workflow capabilities. Main discussion centered around integration timeline and complexity. They currently use Legacy System X for their core operations and expressed concerns about potential disruption during migration. Team asked detailed questions about API compatibility and data migration tools. Action items: 1) Provide detailed integration timeline document 2) Schedule technical deep-dive with their infrastructure team 3) Share case studies of similar Legacy System X migrations. Client mentioned Q2 budget allocation for digital transformation initiatives. Overall positive engagement with clear next steps.', 'TechCorp Inc', 'Discovery', 'Sarah Johnson', '2024-01-15 10:30:00', 75000, 'Enterprise Suite'),

('CONV002', 'Follow-up call with SmallBiz Solutions'' Operations Manager and Finance Director. Primary focus was on pricing structure and ROI timeline. They compared our Basic Package pricing with Competitor Y''s small business offering. Key discussion points included: monthly vs. annual billing options, user license limitations, and potential cost savings from process automation. Client requested detailed ROI analysis focusing on: 1) Time saved in daily operations 2) Resource allocation improvements 3) Projected efficiency gains. Budget constraints were clearly communicated - they have a maximum budget of $30K for this year. Showed interest in starting with basic package with room for potential upgrade in Q4. Need to provide competitive analysis and customized ROI calculator by next week.', 'SmallBiz Solutions', 'Negotiation', 'Mike Chen', '2024-01-16 14:45:00', 25000, 'Basic Package'),

('CONV003', 'Strategy session with SecureBank Ltd''s CISO and Security Operations team. Extremely positive 90-minute deep dive into our Premium Security package. Customer emphasized immediate need for implementation due to recent industry compliance updates. Our advanced security features, especially multi-factor authentication and encryption protocols, were identified as perfect fits for their requirements. Technical team was particularly impressed with our zero-trust architecture approach and real-time threat monitoring capabilities. They''ve already secured budget approval and have executive buy-in. Compliance documentation is ready for review. Action items include: finalizing implementation timeline, scheduling security audit, and preparing necessary documentation for their risk assessment team. Client ready to move forward with contract discussions.', 'SecureBank Ltd', 'Closing', 'Rachel Torres', '2024-01-17 11:20:00', 150000, 'Premium Security'),

('CONV004', 'Comprehensive discovery call with GrowthStart Up''s CTO and Department Heads. Team of 500+ employees across 3 continents discussed current challenges with their existing solution. Major pain points identified: system crashes during peak usage, limited cross-department reporting capabilities, and poor scalability for remote teams. Deep dive into their current workflow revealed bottlenecks in data sharing and collaboration. Technical requirements gathered for each department. Platform demo focused on scalability features and global team management capabilities. Client particularly interested in our API ecosystem and custom reporting engine. Next steps: schedule department-specific workflow analysis and prepare detailed platform migration plan.', 'GrowthStart Up', 'Discovery', 'Sarah Johnson', '2024-01-18 09:15:00', 100000, 'Enterprise Suite'),

('CONV005', 'In-depth demo session with DataDriven Co''s Analytics team and Business Intelligence managers. Showcase focused on advanced analytics capabilities, custom dashboard creation, and real-time data processing features. Team was particularly impressed with our machine learning integration and predictive analytics models. Competitor comparison requested specifically against Market Leader Z and Innovative Start-up X. Price point falls within their allocated budget range, but team expressed interest in multi-year commitment with corresponding discount structure. Technical questions centered around data warehouse integration and custom visualization capabilities. Action items: prepare detailed competitor feature comparison matrix and draft multi-year pricing proposals with various discount scenarios.', 'DataDriven Co', 'Demo', 'James Wilson', '2024-01-19 13:30:00', 85000, 'Analytics Pro'),

('CONV006', 'Extended technical deep dive with HealthTech Solutions'' IT Security team, Compliance Officer, and System Architects. Four-hour session focused on API infrastructure, data security protocols, and compliance requirements. Team raised specific concerns about HIPAA compliance, data encryption standards, and API rate limiting. Detailed discussion of our security architecture, including: end-to-end encryption, audit logging, and disaster recovery protocols. Client requires extensive documentation on compliance certifications, particularly SOC 2 and HITRUST. Security team performed initial architecture review and requested additional information about: database segregation, backup procedures, and incident response protocols. Follow-up session scheduled with their compliance team next week.', 'HealthTech Solutions', 'Technical Review', 'Rachel Torres', '2024-01-20 15:45:00', 120000, 'Premium Security'),

('CONV007', 'Contract review meeting with LegalEase Corp''s General Counsel, Procurement Director, and IT Manager. Detailed analysis of SLA terms, focusing on uptime guarantees and support response times. Legal team requested specific modifications to liability clauses and data handling agreements. Procurement raised questions about payment terms and service credit structure. Key discussion points included: disaster recovery commitments, data retention policies, and exit clause specifications. IT Manager confirmed technical requirements are met pending final security assessment. Agreement reached on most terms, with only SLA modifications remaining for discussion. Legal team to provide revised contract language by end of week. Overall positive session with clear path to closing.', 'LegalEase Corp', 'Negotiation', 'Mike Chen', '2024-01-21 10:00:00', 95000, 'Enterprise Suite'),

('CONV008', 'Quarterly business review with GlobalTrade Inc''s current implementation team and potential expansion stakeholders. Current implementation in Finance department showcasing strong adoption rates and 40% improvement in processing times. Discussion focused on expanding solution to Operations and HR departments. Users highlighted positive experiences with customer support and platform stability. Challenges identified in current usage: need for additional custom reports and increased automation in workflow processes. Expansion requirements gathered from Operations Director: inventory management integration, supplier portal access, and enhanced tracking capabilities. HR team interested in recruitment and onboarding workflow automation. Next steps: prepare department-specific implementation plans and ROI analysis for expansion.', 'GlobalTrade Inc', 'Expansion', 'James Wilson', '2024-01-22 14:20:00', 45000, 'Basic Package'),

('CONV009', 'Emergency planning session with FastTrack Ltd''s Executive team and Project Managers. Critical need for rapid implementation due to current system failure. Team willing to pay premium for expedited deployment and dedicated support team. Detailed discussion of accelerated implementation timeline and resource requirements. Key requirements: minimal disruption to operations, phased data migration, and emergency support protocols. Technical team confident in meeting aggressive timeline with additional resources. Executive sponsor emphasized importance of going live within 30 days. Immediate next steps: finalize expedited implementation plan, assign dedicated support team, and begin emergency onboarding procedures. Team to reconvene daily for progress updates.', 'FastTrack Ltd', 'Closing', 'Sarah Johnson', '2024-01-23 16:30:00', 180000, 'Premium Security'),

('CONV010', 'Quarterly strategic review with UpgradeNow Corp''s Department Heads and Analytics team. Current implementation meeting basic needs but team requiring more sophisticated analytics capabilities. Deep dive into current usage patterns revealed opportunities for workflow optimization and advanced reporting needs. Users expressed strong satisfaction with platform stability and basic features, but requiring enhanced data visualization and predictive analytics capabilities. Analytics team presented specific requirements: custom dashboard creation, advanced data modeling tools, and integrated BI features. Discussion about upgrade path from current package to Analytics Pro tier. ROI analysis presented showing potential 60% improvement in reporting efficiency. Team to present upgrade proposal to executive committee next month.', 'UpgradeNow Corp', 'Expansion', 'Rachel Torres', '2024-01-24 11:45:00', 65000, 'Analytics Pro');

-- Now, let's insert corresponding data into sales_metrics
INSERT INTO sales_metrics 
(deal_id, customer_name, deal_value, close_date, sales_stage, win_status, sales_rep, product_line)
VALUES
('001', 'TechCorp Inc', 75000, '2024-02-15', 'Closed', true, 'Sarah Johnson', 'Enterprise Suite'),

('002', 'SmallBiz Solutions', 25000, '2024-02-01', 'Lost', false, 'Mike Chen', 'Basic Package'),

('003', 'SecureBank Ltd', 150000, '2024-01-30', 'Closed', true, 'Rachel Torres', 'Premium Security'),

('004', 'GrowthStart Up', 100000, '2024-02-10', 'Pending', false, 'Sarah Johnson', 'Enterprise Suite'),

('005', 'DataDriven Co', 85000, '2024-02-05', 'Closed', true, 'James Wilson', 'Analytics Pro'),

('006', 'HealthTech Solutions', 120000, '2024-02-20', 'Pending', false, 'Rachel Torres', 'Premium Security'),

('007', 'LegalEase Corp', 95000, '2024-01-25', 'Closed', true, 'Mike Chen', 'Enterprise Suite'),

('008', 'GlobalTrade Inc', 45000, '2024-02-08', 'Closed', true, 'James Wilson', 'Basic Package'),

('009', 'FastTrack Ltd', 180000, '2024-02-12', 'Closed', true, 'Sarah Johnson', 'Premium Security'),

('010', 'UpgradeNow Corp', 65000, '2024-02-18', 'Pending', false, 'Rachel Torres', 'Analytics Pro');

-- Enable change tracking
ALTER TABLE sales_conversations SET CHANGE_TRACKING = TRUE;

-- Create the search service
CREATE OR REPLACE CORTEX SEARCH SERVICE sales_conversation_search
  ON transcript_text
  ATTRIBUTES customer_name, deal_stage, sales_rep
  WAREHOUSE = sales_intelligence_wh
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        conversation_id,
        transcript_text,
        customer_name,
        deal_stage,
        sales_rep,
        conversation_date
    FROM sales_conversations
    WHERE conversation_date >= '2024-01-01' 
);

CREATE OR REPLACE STAGE models DIRECTORY = (ENABLE = TRUE);
```

Now we will have to set up a semantic view for Cortex Analyst.
<br>

[Semantic view](https://docs.snowflake.com/en/user-guide/views-semantic/overview) is a new Snowflake schema-level object. You can define business metrics and model business entities and their relationships. By adding business meaning to physical data, the semantic view enhances data-driven decisions and provides consistent business definitions across enterprise applications. 


Setting up Cortex Analyst
- Go to **AI & ML** on the side and select **Cortex Analyst**.
- Select the `SALES_INTELLIGENCE.DATA` Database and Schema.
- Select **Create New** and select **Create new Semantic View**.
 ![](assets/analystui.png)

 Name the Analyst Service `SALES_METRICS_MODEL` and select **Next**.
 - We will skip the `Provide context (optional)` so click **Next**
 - Select the `SALES_INTELLIGENCE` database, `DATA` schema, `SALES_METRICS` table then select **Next**.
 - Select all of the columns
 - Check  
 ☑️ Add sample values to the semantic view  
 ☑️ Add descriptions to the semantic view
 -  Select **Create and Save**.
  ![](assets/createsv.png)
 
 This is a VERY simple Analyst service. You can click through the dimensions and see that Cortex used LLMS to write descriptions and synonyms for each of the dimensions. We're going to leave this as-is, but know that you can adjust this as needed to enhance the performance of Cortex Analyst.
 ![](assets/builtanalyst.png)

Setting up Cortex Agent
- Go to **AI * ML** on the side and select **Cortex Agent**.
- Select the `SALES_INTELLIGENCE.DATA` Database and Schema.
- Select **Create Agent**.
- Name the agent `SALES_INTELLIGENCE_AGENT` and create the agent.
![](assets/salesintelligence.png)

Let's add the tools and orchestration to the agent
- Select **Tools** and **Add** by Cortex Analyst.
- Select the `SALES_INTELLIGENCE.DATA` Database and Schema and Select the `SALES_METRICS_MODEL` created earlier and generate a Description with Cortex AI.
- Select **Add**
![](assets/analysttoolui.png)

- Select **Add** by Cortex Search.
- Select the `SALES_INTELLIGENCE.DATA` Database and Schema and Select the `SALES_CONVERSATION_SEARCH`.
- Enter the name `SALES_CONVERSATION_SEARCH` and enter the description "the search service is for providing information on sales call transcripts".
- Select `CONVERSATION_ID` as the ID column and `CUSTOMER_NAME` as the Title Column.
- Select **Add**.
![](assets/searchtoolui2.png)

- Select **Orchestration** and leave the model set to **auto**.
- Add the following orchestration instructions, "use the analyst tool for sales metric and the search tool for call details".
- Add the following response instructions, "make the response concise and direct so that a strategic sales person can quickly understand the information provided".
- Select **Save**.

> 🧪 Feel free to test the agent created with the following questions:-
> - what is the largest deal size? 
> - what is the meeting with TechCorp Inc about and any action item?
![](assets/testcortexagent.png)

And last we will run this below script to grant the appropriate privileges to the `PUBLIC` role (or whatever role you can use). 

```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE PUBLIC;
GRANT USAGE ON DATABASE SALES_INTELLIGENCE TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA DATA TO ROLE PUBLIC;
GRANT SELECT ON SALES_METRICS TO ROLE PUBLIC;
GRANT SELECT ON SALES_INTELLIGENCE.DATA.SALES_METRICS TO ROLE PUBLIC;
GRANT USAGE ON CORTEX SEARCH SERVICE SALES_CONVERSATION_SEARCH TO ROLE PUBLIC;
GRANT USAGE ON WAREHOUSE SALES_INTELLIGENCE_WH TO ROLE PUBLIC;
```
<!-- ------------------------ -->
## App Connectivity

A Global Administrator for your Microsoft Entra ID tenant must use the two links below to grant the necessary permissions for the applications. Please review the permissions requested on each consent screen before accepting.

Replace <TENANT-ID> with your organization’s tenant identifier:

```
https://login.microsoftonline.com/<TENANT-ID>/adminconsent?client_id=5a840489-78db-4a42-8772-47be9d833efe
```
> Note that `client_id=5a840489-78db-4a42-8772-47be9d833efe` ia also known as the application ID of the application. You can build the same URL to grant tenant-wide admin consent. This is the Snowflake Microsofts application ID. Refer to [Microsoft doc](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/grant-admin-consent?pivots=portal#construct-the-url-for-g[…]nant-wide-admin-consent)

![](assets/consentone.png)

Replace <TENANT-ID> with your organization’s tenant identifier:

```
https://login.microsoftonline.com/<TENANT-ID>/adminconsent?client_id=bfdfa2a2-bce5-4aee-ad3d-41ef70eb5086
```

![](assets/consenttwo.png)

Admins should also make sure the Snowflake users have an email address in their Snowflake user that matches their Microsoft tenant.

Admins should execute the below code to create the security integration necessary to authenticate with Entra ID.
 <TENANT-ID> with your organization’s tenant identifier:
```sql
CREATE OR REPLACE SECURITY INTEGRATION entra_id_cortex_agents_integration 
TYPE = EXTERNAL_OAUTH 
ENABLED = TRUE 
EXTERNAL_OAUTH_TYPE = AZURE 
EXTERNAL_OAUTH_ISSUER = 'https://login.microsoftonline.com/<TENANT-ID>/v2.0'
EXTERNAL_OAUTH_JWS_KEYS_URL = 'https://login.microsoftonline.com/<TENANT-ID>/discovery/v2.0/keys'
EXTERNAL_OAUTH_AUDIENCE_LIST = ('5a840489-78db-4a42-8772-47be9d833efe') EXTERNAL_OAUTH_TOKEN_USER_MAPPING_CLAIM = ('email', 'upn')
EXTERNAL_OAUTH_SNOWFLAKE_USER_MAPPING_ATTRIBUTE = 'email_address' 
EXTERNAL_OAUTH_ANY_ROLE_MODE = 'ENABLE'
```
Search for "Snowflake Cortex Agents" in the Microsoft Teams App Store and click "Add".

The first user from your organization to interact with the agent will be guided through a one-time setup process to connect your Snowflake account for the whole organization. This user must have administrative permissions in the target Snowflake account to complete the setup.

Depending on your organization’s Microsoft Teams policies, a Microsoft Teams Administrator may need to approve or unblock the application before it is available to users. Reach to [Overview of app management and governance in Microsoft Teams admin center”](https://learn.microsoft.com/en-us/microsoftteams/manage-apps) article in order to get more information on managing access to Microsoft Teams Applications across an organization.

Upon the first interaction with the agent, you will be prompted to log in with your Microsoft account.

The agent will inform you that no Snowflake account is configured for your organization and will ask for your Snowflake account URL. Clicking “I’m the Snowflake administrator” action will unveil a simple form, where you can provide your account’s URL.
-The full URL to enter is your_organization-your_account.snowflakecomputing.com.
![](assets/adminscreen.png)

If all checks pass, the Snowflake configuration has been successfully added for your organization. All users from your Microsoft tenant can now interact with the agent using this Snowflake account.

<!-- ------------------------ -->
## Run Application

Access the App from M365 Copilot or Microsoft Teams experience. The experience will be mostly the same with some minor variations in the UI. See the two screenshots below.

#### Microsoft Teams
![](assets/openteamsagent.png)

#### M365 Copilot
![](assets/opencopilotagent.png)


You can start by asking "view available commands" to then access the admin panel, get help or choose a new snowflake account.
![](assets/viewcommands.png)


Ask by typing "what was the largest deal size" to see the answer.
![](assets/answer.png)

And you are now ready to go! You can continue asking questions like:
- Plot our largest deals by deal size?
- How was the call with Securebank?
- What was the worst customer call we had?
- Show the deals that are currently pending

![](assets/agent.gif)

The Snowflake Cortex Teams and M365 App now supports the below functionality. Users are encouraged to expand on this use case to explore its complete functionality

- Multi-Agent Support: Users can now use and switch between multiple agents across multiple Snowflake accounts.

- Multi-Turn Conversations: Stateful conversations are now supported via the new Threads API, providing a genuine chatbot experience.

- Improved Reasoning & UX: Agents now use a multi-step “Reasoning Path” for tools, and the UI shows “thinking” traces and status updates.
<!-- ------------------------ -->
## Conclusion and Resources

### Technical Considerations
Now that you've mastered creating a Cortex Agent app, you're ready to unlock powerful insights for your organization. We're excited to see how you build on this new capability, enabling your business users to query all types of data using plain text within Microsoft Teams and M365 Copilot.

### What you learned
By following this quickstart, you learned how to:
- Create Snowflake Cortex Services for Search, Analyst and Agents
- Securely connect Microsoft Teams and M365 Copilot App to Cortex Agents
- Use the Microsoft Teams and M365 App with Cortex Agents

### Resources
- Learn more about the complete [Snowflake Cortex set of features](/en/product/features/cortex/)
- Learn more about using [Agents in Cortex](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- Learn more about using [M365](https://www.microsoft.com/en-us/microsoft-365/products-apps-services)
- Learn more about using [M365 Copilot](https://www.microsoft.com/en-us/microsoft-copilot/organizations)
- The official [Microsoft Teams and M365 Copilot Cortex App Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-teams-integration)
- [Demo Video](https://cloudpartners.transform.microsoft.com/download?assetname=assets%2FCopilot-Partner-Demo-Snowflake-v2505.mp4)
