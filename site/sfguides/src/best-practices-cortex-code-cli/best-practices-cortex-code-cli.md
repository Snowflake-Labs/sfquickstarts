author: Umesh Unnikrishnan, Shayak Sen 
id: best-practices-cortex-code-cli
language: en 
summary: Learn best practices for using Cortex Code CLI, your AI-powered command-line coding agent for building, debugging, and deploying Snowflake applications.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web 
status: Published 

# Best Practices for Cortex Code CLI

This is your guide to Snowflake's [**Cortex Code CLI**](http://docs.snowflake.com/user-guide/cortex-code/cortex-code-cli), an AI-powered command-line coding agent designed to streamline the process of building, debugging, and deploying Snowflake applications through natural language conversations.

[![A video thumbnail for Cortex Code CLI Overview](https://www.snowflake.com/content/dam/snowflake-site/general/external/cli-thumbnail-dev-guide.png)](https://www.youtube.com/watch?v=lftWaAcG2nE)

[Watch how you can use Cortex Code CLI in less than 3 minutes](https://www.youtube.com/watch?v=lftWaAcG2nE).

## Installation instructions

### What you'll need
- Snowflake account with appropriate permissions
- A supported environment: macOS on Apple Silicon, Intel Linux on Intel, or Windows Subsystem for Linux (WSL)
- Terminal access

``` 
curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh 
```

> **If you're not yet a Snowflake customer** [start your 30-day Cortex Code CLI trial](https://signup.snowflake.com/cortex-code). 

For more details on setup, connections, supported models, or CLI reference, see the [Cortex Code CLI documentation](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli).

## Terminology

- **[Cortex Code CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)** is an AI-powered coding agent for building, debugging, and working in Snowflake through natural language conversations.
- **[Skills](https://docs.snowflake.com/en/user-guide/cortex-code/extensibility)**: reusable instruction packs (playbooks) that guide Cortex Code through specific workflows (e.g., `agent-optimization`, `semantic-view-optimization`).
- **[Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)**: conversational AI assistants you build in Snowflake that can autonomously answer questions, use tools, and interact with your data.
- **[Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)**: Snowflake service that translates natural language questions into SQL queries, using semantic models to understand business logic.
- **[Semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/overview)**: schema-level objects that combine data with business context (definitions, relationships, and metrics) to power consistent analytics and natural-language-to-SQL experiences.

## Best practices

> **Always ensure you're on the latest CLI version.** Run `cortex --version` and update if needed.

### Communicate naturally

* Use plain language to describe what you want, not how to do it  
* Iterate conversationally - just say what you'd like changed
* If you feel stuck, ask "What steps are available to me?"  
* New skills are always being added. Ask "what skills are available?" to see the latest.
* Check if specialized skills should be loaded for agents, semantic models, or complex workflows  

### Review before accepting

* Understand proposed changes before they're executed, especially SQL DDL/DML operations  
* Verify file modifications - what will be created, edited, or deleted  
* Use caution with production environments and destructive operations (DROP, DELETE, etc.)  
* Ask for explanations if unsure: "Why are you doing this?" or "What will this change?"

### Work effectively

* Start small and test frequently - build one component at a time  
* Use `/plan` for complex tasks to see the full approach before starting  
* Run Cortex Code in a VS Code/Cursor terminal to view code files side-by-side  
* Write complex requirements in `.md` files and reference them in the conversation  
* If you hit unexpected behavior, confirm you’re on the latest CLI version (for example: run `cortex --version` and update if needed)

### Security & governance

* Never commit secrets - keep credentials out of code and version control  
* Review privilege grants and RBAC changes carefully   
* Leverage built-in help - ask "How does this work?" or check Snowflake documentation

## Where to start

Everyone can start with [data exploration](#data-exploration) to find data you can work with and validate access.

Then, discover use cases that best match your goal:

- **Data engineering (pipelines and operations)**: explore how to [create and manage dbt projects](#create-and-manage-dbt-projects), or operationalize runs with [Apache Airflow® orchestration](#apache-airflow-orchestration). Learn how to add [semantic views to your gold tables](#add-semantic-views-to-your-gold-tables) when you're ready to standardize metrics and definitions for downstream users.
- **Analytics and app builders (interactive experiences)**: learn how to [build interactive dashboards](#build-interactive-dashboards) using Streamlit, or configure production-ready [Cortex Agents for Snowflake Intelligence](#cortex-agents-for-snowflake-intelligence) so end users can self-serve answers and insights, grounded in governed data and the right tools.

## Data exploration

In this section, you’ll use Cortex Code CLI to discover data you can work with, confirm you have the right permissions, and run a few exploratory questions. If you don’t have a convenient dataset handy, you can generate a small synthetic one to follow along—then use it in the dashboard example that follows. 

### Discover and explore data

Search your data catalog, understand lineage, and find relevant tables.

``` 
Find all tables related to customers that I have write access to.
```

### Ensure you have the right role with the correct permissions

``` 
What privileges does my role have on this database?
```

Diagnose access issues and understand role privileges.

``` 
Why am I getting a permissions error?
```

### Generate synthetic data

If you need a dataset to practice on, generate a small synthetic one.

Examples:

**Fraud analysis for a fintech company**

``` 
Generate realistic-looking synthetic data into <database name>. Create a table of
10,000 financial transactions where ~0.5% of them are fraudulent. Include amount,
location, merchant, and time. Make the fraudulent ones look suspicious based on
location or amount.
```

**Pharma trial data**

``` 
Make a dummy dataset for a clinical trial of a new blood pressure medication. List
100 patients, their age, their dosage group (Placebo vs. 10mg), and their blood
pressure readings over 4 weeks.
```

**Customer churn data**

```
Create a customer churn dataset for a telecom company showing customer usage 
for 100,000 customers. 
Include basic demographic data such as fake names, phone numbers, U.S. city and
state. Also include data usage (GB), call minutes, contract length, and whether
they cancelled their service (churn). Ensure there's a customer_id column that's
unique. Create the data locally and then upload it to Snowflake.
```

### Query your data

Ask anything! Here are some basic examples:

```
Calculate the churn rate grouped by state and contract length. 
Order the results by the highest churn rate first so I can see 
the most risky regions and contract types.
```
```
I want to identify the heaviest data users who are also churning.
```

## Build interactive dashboards

Next, turn your exploration into an interactive Streamlit app you can share.

Create and deploy Streamlit apps with charts, filters, and interactivity.

Open a good-looking dashboard (for example, [this dashboard](https://s3-figma-hubfile-images-production.figma.com/hub/file/carousel/img/fc3a04485c66b47e6985c5bd5f0c4b28495a3456)), copy it to the clipboard, then paste it into Cortex Code (Ctrl+V).

```
Build an interactive Streamlit dashboard on this data with state filters and 
use the conversation so far for examples of the kinds of charts to show. 
Use the attached image as a template for visuals and branding.
```

Once you've verified that the dashboard is working and looks good, you can now upload it to Snowflake. 

``` 
Ensure that the Streamlit app will work with Snowflake and upload it to Snowflake. 
Give me a link to access the dashboard when it's done.
```

Congratulations! You should now have a working Streamlit dashboard that displays the dataset you created!

## Cortex Agents for Snowflake Intelligence

Now, let's make this more interactive by creating a Cortex Agent to answer questions about this data in Snowflake Intelligence. In this process, we'll augment the existing synthetic data with some synthetic data of customer calls. 

Check out [Best Practices for Building Cortex Agents](https://www.snowflake.com/en/developers/guides/best-practices-to-building-cortex-agents/) for additional guidance as you configure your agent's design, tooling, and orchestration instructions for optimal reliability.

We’ll set up two building blocks: one for structured analytics and one for unstructured text, then combine them into a single agent experience.

### Create a semantic view for Cortex Analyst

Now let's create a semantic view so that you can use Cortex Analyst with this data. Try the prompt below and use the defaults for all the questions it asks. 

```
Write a Semantic View named DEMO_TELECOM_CHURN_ANALYTICS for Cortex Analyst 
based on this data. Use the semantic-view-optimization skill.
```

### Create a Cortex Search service

Step 1: Generate some synthetic data containing customer service calls 

```
Generate a new table called customer_call_logs. Generate 50 realistic customer
service transcripts (2-3 sentences each) as PDF files. Some should be angry
complaints about coverage, others should be questions about billing. Then 
Use the AI_PARSE_DOCUMENT function to extract the text and layout information
from the PDFs into the TRANSCRIPT_TEXT column. Split text into chunks for better
search quality. 
``` 

Step 2: Create a Cortex Search service to index it: 

```
Create a Cortex Search Service named CALL_LOGS_SEARCH that indexes these
transcripts. It should index the TRANSCRIPT_TEXT column and filter by CUSTOMER_ID
```

### Create a Cortex Agent

Finally, let's create a Cortex Agent that uses these two services and add it to Snowflake Intelligence:

```
Build a Cortex Agent that has access to two tools:
cortex_analyst: For querying the TELECOM_CUSTOMERS SQL table.
cortex_search: For searching the CALL_LOGS_SEARCH service. Write a system prompt for this agent. 
Persona: You are a Senior Retention Specialist.
Routing Logic: If the user asks for 'metrics', 'counts', or 'averages', 
use the Analyst tool. If the user asks for 'sentiment', 'reasons', or 
'summaries of calls', use the Search tool.
Output Format: Always verify the customer ID before answering. 
If the risk score is high, end the response with a recommended retention offer 
(e.g., 'Offer 10% discount').
Constraint: Never reveal the raw CHURN_RISK_SCORE to the user; interpret it as
'Low', 'Medium', or 'High'.
```

### Optimize your Cortex Agent

Once the agent is created, iterate on reliability and usefulness with the `agent-optimization` skill:

```
Use the agent-optimization skill to review and improve this Cortex Agent configuration (system prompt, tool routing logic, and guardrails). Make it more reliable, reduce unnecessary tool calls, and add any missing constraints or clarifying questions for edge cases.
```

### Deploy to Snowflake Intelligence

Finally, we can deploy the agent to [Snowflake Intelligence](https://ai.snowflake.com/)

```
Let's deploy this agent to Snowflake Intelligence
```

Ta-da! You have successfully created and deployed a Snowflake Intelligence agent. 

Now you should be able to access this agent in Snowflake Intelligence and ask it questions like: 

- *"What are customers complaining about in their calls?"*
- *"Show me high-risk customers with monthly charges over $100."*

## Create and manage dbt projects

Sometimes starting a brand-new dbt project can feel like a full-day task: jumping between Snowsight, your IDE, your terminal, and your dbt repo to define sources, build models, add tests, run builds, validate outputs, and share results.

With Cortex Code CLI, you can often collapse that end-to-end loop into a single conversation, staying in flow while it handles the boilerplate, wiring, and Snowflake-specific best practices.


### dbt Core and dbt Cloud

If you run dbt from your own repo (dbt Core) or manage it via dbt Cloud, you can still use Cortex Code CLI to generate and evolve the project locally—while respecting your existing connection setup (for example, using `~/.dbt` instead of creating a new `profiles.yml`).

For example:

```
Create a dbt project under /tasty_food that builds a data pipeline to analyze order information and trends using my source data in Database tb_101 Schema RAW. Add appropriate tests, run a build, validate the output, and generate a shareable HTML summary. Don’t create a profiles.yml file; I already have a Snowflake connection via ~/.dbt. When running dbt commands, use --target PM.
```

And when your project grows, you can use Cortex Code CLI to help keep it fast and cost-efficient:

```
Take a look at /target/run_results.json, identify the slowest-running models, suggest specific performance optimizations, and flag any models that aren’t referenced downstream and could potentially be removed.
```
### dbt Projects on Snowflake

[dbt Projects on Snowflake](https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake-using-workspaces) are a Snowflake native implementation of dbt that unlocks project management and orchestration through Workspaces.

If you are using Snowflake's native dbt implementation, try prompts like:

```
Find all of the tables within Database tb_101 Schema RAW.
```

```
Create a dbt project that uses these source tables to create an operations pipeline to analyze weekly food truck performance using the Tasty Bytes dataset. Using the raw order, menu, and truck location data, build a model that calculates weekly revenue, total orders, and average order value by truck and city. Add appropriate tests, run a build, validate the output, and generate a shareable HTML summary of the results.
```

```
Open the generated HTML summary in my browser.
```

Once you have a first version working, keep iterating with follow-up prompts like:
- Why did you structure the model this way?
- Can you add more tests for nulls and uniqueness?
- Can you refactor this into staging and mart layers?
- How would you optimize this project for performance and cost?

## Apache Airflow® orchestration

Apache Airflow® + Snowflake workflows often fail in cross-tool ways: a DAG task fails, a dbt model doesn’t populate, upstream data is missing, or a warehouse setting causes timeouts.

Cortex Code CLI provides built-in support for Airflow, giving you a natural language interface to monitor DAGs, manage runs, debug failures, author pipelines, and understand lineage across your Airflow deployments.

### Capabilities at a glance

- **Pipeline monitoring**: health checks, DAG inspection, connection/variable visibility, and scheduling control. For example: "Is my Airflow instance healthy?"
- **Run management**: trigger DAGs on demand, wait for results, and pass custom run configuration. For example: "Test the daily_etl DAG and let me know when it finishes."
- **Failure debugging**: root cause analysis across run state, task instances, and logs with impact assessment and fix recommendations. For example: "Why did my_pipeline fail last night?"
- **DAG authoring**: guided DAG creation using your existing patterns, connections, and providers. For example: "Create a DAG that extracts from Snowflake and loads to S3 daily."
- **Lineage and impact**: upstream origin tracing and downstream impact analysis through DAG source code. For example: "What would break if I change the customers table schema?"
- **Migration and modern patterns**: migrate Airflow 2 → 3 and add human-in-the-loop steps (Airflow 3.1+). For example: "Migrate my DAGs from Airflow 2 to Airflow 3."

### Quick setup

- **Prereq**: install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) (required for `cortex airflow`).
- **Configure an instance**:
  - Run `/airflow` inside Cortex Code (supports multiple named instances), or
  - Export connection details before starting Cortex Code:

```bash
export AIRFLOW_API_URL=https://airflow.example.com
export AIRFLOW_AUTH_TOKEN=your-api-token
# Or use AIRFLOW_USERNAME / AIRFLOW_PASSWORD
```

- **In-session**: `/airflow` (manage), `/airflow show` (masked), `/airflow clear` (remove)

### Common commands

```bash
cortex airflow health
cortex airflow dags list
cortex airflow dags source my_pipeline
cortex airflow runs trigger my_pipeline
cortex airflow runs list my_pipeline
cortex airflow tasks list my_pipeline <run_id>
```

Run `cortex airflow --help` for the full list of commands.

### Example prompts

For end-to-end failure triage:

```
Why did my_pipeline fail last night? Identify the root cause from run state and task logs, assess downstream impact, and recommend a fix.
```

To trigger a run and wait for results:

```
Test the daily_etl DAG and let me know when it finishes. If it fails, summarize the failing task and the error.
```

For lineage/impact questions:

```
What would break if I change the customers table schema? Trace upstream origins and downstream dependencies through DAG source code.
```

### Troubleshooting quick checks

- **Connection refused**: verify `AIRFLOW_API_URL` and run `cortex airflow health`
- **401/403**: verify token/credentials; check expiry and API permissions
- **DAG not found**: confirm DAG ID and check for import/parse errors preventing it from loading

## Add semantic views to your gold tables

Once your dbt pipeline produces “gold” (business-ready) models (typically your mart layer), you can add a semantic view on top to define metrics, dimensions, and joins in one place. This helps downstream consumers (dashboards, BI tools, and AI apps) use consistent definitions without everyone re-implementing business logic in their own queries.

How do you know your dbt outputs are “gold”? Typically, they:
- **Have stable business meaning** (one agreed definition for key metrics like “weekly revenue”)
- **Are consumer-ready** (modeled for analytics, often your `marts/` layer rather than `staging/` or `intermediate/`)
- **Are tested and reliable** (core tests pass consistently and runs are repeatable)
- **Are documented** (clear naming + descriptions so others know what to query)

Try a prompt like:

```
Create a semantic view named <SEMANTIC_VIEW_NAME (e.g., WEEKLY_TRUCK_PERFORMANCE_SEMANTIC)> on top of my gold dbt models (mart layer): <GOLD_MODELS_OR_SCHEMA (e.g., DB.SCHEMA or MART_*)>.
Define:
- Dimensions: <DIMENSIONS (e.g., truck_id, city, week_start_date)>
- Measures (with definitions): <MEASURES (e.g., weekly_revenue = sum(net_amount), total_orders = count_distinct(order_id))>
- Relationships/joins: <RELATIONSHIPS_OR_JOINS (e.g., weekly_metrics.truck_id -> dim_truck.truck_id)>
Use business-friendly names and descriptions, and validate it answers questions like <EXAMPLE_QUESTIONS (e.g., "Which cities grew WoW revenue?", "Top 10 trucks by AOV last week")>.
```

Then refine it with a follow-up prompt:

```
Use the semantic-view-optimization skill to review and improve <SEMANTIC_VIEW_NAME>. Tighten metric definitions, check joins/relationships, improve naming and descriptions, and recommend any verified queries or custom instructions to make it more reliable for downstream consumers.
```

Semantic view design principles to keep in mind:
- **Design from your end users' perspective, not the database perspective**: use business terminology (not raw table/column names) and define metrics the way stakeholders talk about them. Ask: “If I were explaining this data to a business stakeholder, how would I describe it?”
- **Keep views focused**: organize by business domain/use case; split very large models when different audiences need different slices.
- **Add rich metadata**: fill in descriptions, metrics, and filters; include verified queries and custom instructions when needed to steer consistent outputs.
- **Use assisted creation where possible**: Snowflake **Semantic View Autopilot** can accelerate scaffolding, then refine by hand.

Check out more [best practices and semantic view design principles](https://www.snowflake.com/en/developers/guides/best-practices-semantic-views-cortex-analyst/#semantic-view-design-principles).

## Conclusion and resources

The key to success with Cortex Code CLI is to start small, test frequently, and iterate based on feedback. Leverage the built-in skills for complex workflows, always review proposed changes before execution, and use best practices like proper descriptions, verified queries, and custom instructions to ensure your applications are accurate and maintainable.

- [Cortex Code CLI docs](http://docs.snowflake.com/user-guide/cortex-code/cortex-code-cli)
- Start your [30-day Cortex Code CLI Trial](https://signup.snowflake.com/cortex-code)
- [Cortex Code in Snowsight](http://docs.snowflake.com/user-guide/cortex-code/cortex-code-snowsight)

