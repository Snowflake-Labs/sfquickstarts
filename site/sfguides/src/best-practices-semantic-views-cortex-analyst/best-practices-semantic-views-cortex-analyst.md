author: Abhinav Vadrevu
id: best-practices-semantic-views-cortex-analyst
language: en
summary: Learn best practices for designing high-quality semantic views for Cortex Analyst using Snowflake’s AI-assisted “autopilot” workflow.
categories: snowflake-site:taxonomy/solution-center/ai-ml/quickstart
environments: web
open in snowflake link: https://app.snowflake.com/_deeplink/#/cortex/analyst?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_content=best-practices-to-building-cortex-agents&utm_cta=developer-guides-deeplink
status: Published

# Best Practices for Creating Semantic Views for Cortex Analyst

## Overview

Creating high-quality semantic views is the foundation for delivering accurate, intuitive, and trustworthy answers in Cortex Analyst.

This guide walks through best practices for designing and building semantic views using **“autopilot”**, Snowflake’s AI-assisted, UI-based workflow. Whether you’re just getting started or refining a production model, these principles will help you create semantic views that are organized, explainable, and optimized for both performance and accuracy.

This guide focuses on the autopilot workflow. If you prefer to build semantic views programmatically using SQL (for example, for CI/CD pipelines), use the SQL-focused semantic view guide instead.

### Prerequisites

- Familiarity with your business domain (the questions end users will ask)
- Read access to the source tables you want to model
- Basic SQL knowledge (recommended)

### What You’ll Learn

- Core semantic view design principles (“think like your end users”)
- How to scope, organize, and route semantic views by business domain
- How to select tables/columns and define relationships correctly
- How to improve accuracy with descriptions, metrics, filters, verified queries, and custom instructions
- How to test and iterate using evaluation sets and feedback loops

### What You’ll Need

- A Snowflake account with access to Snowsight
- One or more tables you want to expose through Cortex Analyst

### What You’ll Build

- A production-ready semantic view approach (design + checklist) for Cortex Analyst

## Step 1: Choose Your Creation Path (Autopilot vs SQL)

There are two paths for creating semantic views:

- **Autopilot (UI + AI assistance)**:
  - Best when you’re new to the semantic view specification, want fast iteration, and want interactive testing with Cortex Analyst.
  - Autopilot can help by generating or improving field descriptions and offering suggestions as you define the model.
  - You can also start from existing dashboards or SQL queries to accelerate setup.

- **SQL API (programmatic)**:
  - Best when you already know the semantic view specification and want to script or automate semantic view creation.
  - Ideal for CI/CD pipelines or integration workflows.

## Step 2: Semantic View Design Principles

### Core philosophy: Think like your end users

- **Design from the end-user perspective**, not the database perspective.
- Use **business terminology**, not technical table names.
- Ask: “If I were explaining this data to a business stakeholder, how would I describe it?”

### Organize by business domain (not by schema)

Structure semantic views by business topic/domain (for example: Sales, Marketing, Customer Support).

- Keep models focused; don’t try to cover everything in one model unless necessary.
- Split by **use case**, not by data structure.

Good examples:

- Sales Performance semantic view
- Customer Support Metrics semantic view
- Marketing Campaign Analysis semantic view

Avoid:

- “All CRM Tables” semantic view

## Step 3: Routing vs a Single Semantic View

Cortex Analyst no longer has hard limitations on semantic view size, but it can still make sense to break up large semantic views.

### When to use multiple semantic views (routing)

Routing may make sense when:

1. You have distinct business domains that don’t need to be joined
2. Different user groups need different views of the data

Routing best practices:

- Use **clear, distinct semantic view descriptions** to improve routing performance.
- Split by use case (Sales vs Legal vs Marketing), not by similarity.
- Avoid many “almost identical” semantic view descriptions; that reduces routing accuracy.
- Routing adds slight latency (a few seconds for reranking).
- Routing will **not** join across semantic views; each semantic view is independent.

### When to use a single larger semantic view

Use a single semantic view when:

- You have densely connected tables that frequently need to be joined
- You have one business domain with many related tables
- You’re using frontier models where pruning allows large semantic views (for example, Claude or GPT)

## Step 4: Build the Semantic View (Tables, Columns, Relationships)

### Start small for your first POC

Even if there are no strict limits, start small to make debugging easier:

- Start with **5–10 tables** for an initial POC
- Expand gradually
- Split into multiple semantic views with routing when it makes sense

### Column selection

- Include only **business-relevant** columns that users will ask about.
- Filter out “everything else” that won’t be used in the generated SQL.
- Use the litmus test: “Will my end users ask about this?”

### Relationships (joins)

Cortex Analyst will not join tables unless relationships are **explicitly defined** in the semantic view. Ensure you define all required relationships.

#### Many-to-many relationships

Many-to-many relationships are not directly supported. A common workaround is to create a shared dimension table that bridges the gap, turning the problem into two many-to-one relationships.

## Step 5: Write High-Quality Descriptions (Most Important Element)

Descriptions are a major driver of accuracy and are not optional.

Why descriptions matter:

- Descriptions greatly improve performance.
- LLMs may understand public-domain concepts (for example, countries), but they won’t understand your proprietary terms unless you explain them.

### Table description example

Good table description:

```yaml
description: "Daily sales data by product line, aligned with
'Cost of Goods Sold' (COGS) and forecasted revenue. Use this
table to analyze sales trends and profit by product."
```

Poor table description:

```yaml
description: "Sales table" # Too vague
```

### Column description example

Good column description:

```yaml
- name: csat_score
  description: "Customer Satisfaction Score (CSAT): measures
  customer satisfaction on a scale of 1-5, where 5 is most
  satisfied. Also referred to as KPI_1 in legacy systems."
```

Poor column description:

```yaml
- name: csat_score
  description: "Score" # Assumes knowledge
```

### Synonyms (current guidance)

Current guidance is to **avoid synonyms** unless you have unique or industry-specific cases that the model is unlikely to know:

- Recent evaluations with frontier models show synonyms typically don’t provide meaningful gains.
- They consume tokens without significant accuracy improvement.

## Step 6: Define Metrics and Filters (Often Underused, Highly Impactful)

Metrics and filters help Cortex Analyst generate consistent, correct SQL and reduce ambiguity.

### Metrics

Metrics are reusable, pre-defined calculations:

```yaml
metrics:
  - name: total_revenue
    description: "Sum of all order revenue, calculated as unit price × quantity"
    expr: SUM(unit_price * quantity)
  - name: average_order_value
    description: "Average revenue per order"
    expr: SUM(revenue) / COUNT(DISTINCT order_id)
```

### Filters

Filters define reusable WHERE-clause logic:

```yaml
filters:
  - name: active_customers
    description: "Customers with purchases in the last year"
    expr: last_purchase_date >= DATEADD(year, -1, CURRENT_DATE())
```

Best practices:

- Define metrics and filters wherever possible.
- If available in your workflow, use “get more suggestions” to propose metrics and filters (often driven by adding verified queries).

## Step 7: Improve Accuracy After Initial Setup

Once the basic semantic view structure is in place, these features are essential for production-quality accuracy.

### Add verified queries (gold SQL examples)

Why add verified queries:

- They are included only when the user’s question is semantically similar, so they don’t usually add significant token overhead.
- They materially improve SQL accuracy.
- They can also drive improvements to filters, metrics, descriptions, and other model elements.

How many to add:

- Start with **10–20 verified queries** covering your most common questions.
- Continue adding based on real user questions over time (there’s no meaningful upper limit).
- Use suggestions (if available) based on query history and usage.

### Use custom instructions correctly

A common mistake is mixing up the two instruction types:

#### SQL Generation instructions

Applied during SQL generation for all queries; use for business-specific logic:

```yaml
module_custom_instructions:
  sql_generation: |-
    - "Our fiscal year starts on February 1st, not January 1st"
    - "When calculating revenue, always use net_revenue (revenue minus returns), not gross_revenue"
    - "Always apply the is_paying_customer filter by default unless the user specifically asks about all customers"
    - "The product_id column in orders table maps to id column in products table, even though naming differs"
```

#### Question categorization (classification) instructions

Applied only during question understanding; use to accept/reject and disambiguate:

```yaml
module_custom_instructions:
  question_categorization: |-
    # Rejection examples
    - "Reject questions about employee salaries or compensation"
    - "Reject questions containing profanity or inappropriate content"
    # Disambiguation examples
    - "When users ask about 'active users', clarify whether they mean users active in last 90 days"
```

Best practices:

- Be specific.
  - Good: “If no date filter is provided, apply a filter for the last year”
  - Bad: “Filter queries for the last year”
- Always test after adding instructions (the playground is a good way to validate behavior).

## Step 8: Add Cortex Search Services (For Fuzzy Text Matching)

Cortex Search services enable fuzzy matching for **text columns** where user input won’t match your data exactly. This helps Cortex Analyst generate higher-quality WHERE clauses.

When you need this:

- Product names (for example, user asks “iPhone 13” but the data has “Apple iPhone 13 - 128GB Blue”)
- Customer names (for example, “John Smith” vs “Smith, John A.”)
- Company names (for example, “Microsoft” vs “Microsoft Corporation”)
- Venue names (for example, “Madison Square Garden” vs “MSG - Madison Square Garden Arena”)

Common mistakes:

- Using search services with numeric or date columns
- Using them with paragraph-style text fields (notes, long descriptions, comments)

## Step 9: Testing and Iteration

### Create an evaluation set

Build benchmark questions:

- Start with ~10 representative questions
- Source them from business users, existing dashboards, or real usage
- Include different complexity levels and use cases

### Measure accuracy

Available tools:

- Use an OSS Streamlit evaluation tool to measure SQL accuracy (recommended)
- A native Snowsight evaluation experience may be available depending on product timing

### Iterative improvement workflow

- Review suggestions and feedback regularly.
- Add verified queries derived from real usage.
- Use resulting suggestions to refine metrics, filters, custom instructions, and descriptions.

## Step 10: Common Pitfalls and How to Avoid Them

- **Undefined scope**
  - What happens: Stakeholders keep adding “just one more thing”
  - Solution: Define crisp success criteria with clear boundaries

- **Starting too big**
  - What happens: Modeling an entire enterprise warehouse on day one
  - Solution: Start with 5–10 tables, one domain, one use case

- **Skipping verified queries**
  - What happens: Inconsistent accuracy on common questions
  - Solution: Add 10–20 verified queries early and grow over time

- **Wrong initial use case**
  - What happens: Starting with high-stakes domains (Finance/Legal) that require near-perfect accuracy
  - Solution: Begin with lower-stakes domains (Sales/Marketing) to iterate safely

### Production-ready semantic view checklist

Foundation:

- Every table has a clear business description
- Every column has a clear description
- Proprietary terms and abbreviations are explained

Critical features:

- 10–20 verified queries covering common questions
- Custom instructions for business-specific logic
- Cortex Search services for high-cardinality text columns
- Metrics defined for reusable calculations
- Filters defined for common conditions

Testing (recommended before deployment):

- An evaluation set exists
- SQL accuracy is measured with an evaluation tool

Ongoing optimization:

- Weekly review of suggestions and feedback
- A process exists for adding verified queries and applying related improvements

## Conclusion And Resources

### What We Covered

- How to scope and organize semantic views by business domain
- When to use routing vs a single semantic view
- How to select tables/columns and define relationships reliably
- How to improve accuracy with descriptions, metrics, filters, verified queries, custom instructions, and search services
- How to test and iterate using evaluation sets and feedback loops

### Related Resources

- Semantic views overview and core concepts (Snowflake documentation)
- Cortex Analyst documentation (Snowflake documentation)
- SQL-based semantic view creation guide (Snowflake developer guides)

