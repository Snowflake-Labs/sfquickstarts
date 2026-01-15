author: Chanin Nantasenamat
id: create-snowflake-quickstarts-with-agents-md
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Learn how to use the AGENTS.md file with AI assistants to convert Jupyter notebooks into properly formatted Snowflake Quickstarts tutorials.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Create Snowflake Quickstarts with AGENTS.md
<!-- ------------------------ -->
## Overview

Creating written tutorials can be time-consuming and error-prone when done manually. The AGENTS.md file provides a structured approach to automate this process using AI assistants like Claude, ChatGPT, or Cursor AI.

This tutorial walks you through the complete workflow of using AGENTS.md to convert input Jupyter notebooks into properly formatted Snowflake Quickstarts that follow official guidelines.

### About AGENTS.md

The `AGENTS.md` file follows the standard format defined at [agents.md](https://agents.md/) and it is a specification for providing instructions to AI coding agents. This standardized format ensures AI assistants can reliably interpret and follow project-specific guidelines.

Our Snowflake Quickstarts `AGENTS.md` combines this standard format with content from two official Snowflake resources:

1. **[Get Started with Guides](https://www.snowflake.com/en/developers/guides/get-started-with-guides/)** - The official Snowflake quickstart creation guide
2. **[Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template)** - The official template structure from the `sfquickstarts` repository

While the official markdown template can be used directly, the AGENTS.md file adds additional value by including:

- **AI-specific instructions** - Guidance for how AI assistants should process and convert documents
- **Validation checklists** - Pre-publish verification steps to catch common errors
- **Category reference tables** - Complete taxonomy paths for easy lookup
- **Best practices** - Lessons learned from creating multiple quickstarts
- **Workflow automation** - Structured prompts and output formatting rules

This layered approach combines the [agents.md](https://agents.md/) standard format, official Snowflake guidelines, and practical automation patterns for AI-assisted quickstart generation.

### What You'll Learn
- How the AGENTS.md file structures the conversion process
- The required metadata fields and their formats
- How to organize content into the Quickstarts template
- Best practices for code blocks, headers, and formatting
- How to validate your generated quickstart

### What You'll Build
By the end of this tutorial, you'll be able to:
- Convert a Jupyter notebook into a publish-ready Snowflake Quickstart
- Use the AGENTS.md file to guide AI assistants through the conversion process
- Apply proper metadata, categories, and formatting to meet Snowflake's publishing standards

**Real-world example:** We'll reference the [Build Business-Ready Queries with Snowflake Semantic Views](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Snowflake_Semantic_View_Business_Ready_Queries) quickstart, which was generated from a Jupyter notebook using this exact workflow.

**Where to publish your work:**
| Asset | Repository |
|-------|------------|
| Input Jupyter notebook | [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks) - Collection of Snowflake Notebook demos, tutorials, and examples |
| Generated quickstart | [sfquickstarts](https://github.com/Snowflake-Labs/sfquickstarts) - Official Snowflake Quickstarts repository |

### Prerequisites
- Access to an AI assistant (Claude, ChatGPT, Cursor AI, or similar)
- A Jupyter notebook to convert into a quickstart
- Basic understanding of Markdown formatting

<!-- ------------------------ -->
## Understanding AGENTS.md

The AGENTS.md file is an instruction set that guides AI assistants through the quickstart conversion process. It contains:

### Key Components

| Component | Purpose |
|-----------|---------|
| **Quick Start** | 3-step workflow overview |
| **Agent Behavior** | What the AI should do on load |
| **Quick Reference** | Fast lookup table for rules |
| **Validation Checklist** | Pre-publish verification |
| **Template Structure** | The exact format to follow |
| **Category Lists** | Valid taxonomy paths |
| **Content Rules** | Formatting guidelines |

### The Conversion Workflow

```
1. AI asks for author name
2. AI asks for document to convert
3. AI processes document:
   - Extracts content hierarchy
   - Matches categories
   - Preserves code snippets
   - Generates action-verb title
4. AI outputs ZIP file with:
   - folder-name/
   └── folder-name.md
```

<!-- ------------------------ -->
## Required Metadata Fields

Every quickstart begins with metadata. Here's what the AGENTS.md requires:

### Metadata Example (Semantic View Quickstart)

```yaml
author: Chanin Nantasenamat
id: build-business-ready-queries-with-snowflake-semantic-views
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/analytics, snowflake-site:taxonomy/product/ai
language: en
summary: Learn how to create Semantic Views in Snowflake to simplify complex SQL queries and build business-friendly abstractions over your data.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
```

### Field Rules

| Field | Rule | Example |
|-------|------|---------|
| `author` | Ask user—never assume | `Chanin Nantasenamat` |
| `id` | Lowercase, hyphens, matches filename AND folder | `build-business-ready-queries-with-snowflake-semantic-views` |
| `categories` | From approved list, always include quickstart | See category tables in AGENTS.md |
| `language` | Valid code: en, es, it, fr, ja, ko, pt_br | `en` |
| `summary` | One sentence description | Brief overview of the guide |
| `status` | `Published` or `Archived` | `Published` |

<!-- ------------------------ -->
## Content Structure

The AGENTS.md defines a specific structure that every quickstart must follow.

### Required Sections

1. **Overview** (with subsections)
   - What You'll Learn
   - What You'll Build
   - Prerequisites

2. **Main Content Sections** (H2 headings)

3. **Conclusion And Resources**
   - What You Learned
   - Related Resources

### Header Hierarchy

```markdown
## Main Section (H2) - Appears in right-side menu
### Subsection (H3) - For detailed steps
#### Sub-subsection (H4) - Maximum depth allowed
```

> **Important:** Never go beyond H4 (`####`). Deeper headings won't render correctly.

### Real Example: Semantic View Quickstart Structure

```
## Overview
### What You'll Learn
### What You'll Build
### Prerequisites

## About the TPC-DS Dataset
### Traditional SQL vs Semantic SQL
### Query Complexity Framework

## Create Semantic Views

## Traditional vs Semantic SQL

## Low Question / Low Schema
### Query 1: Store Numbers in Tennessee
### Query 2: Customers with Dependents
### Query 3: Stores in Midway

## High Question / Low Schema
### Query 11: Customer Count by State
...

## Conclusion And Resources
### Question/Schema Complexity: Key Findings
### Lessons Learned
### What You Learned
### Related Resources
```

<!-- ------------------------ -->
## Category Selection

Categories must come from the approved lists in AGENTS.md. Here's how to select them:

### Always Include Quickstart

```
snowflake-site:taxonomy/solution-center/certification/quickstart
```

### Match Content to Categories

For the Semantic View quickstart, we matched:

| Content Keywords | Selected Category |
|-----------------|-------------------|
| "Analytics", "queries", "SQL" | `snowflake-site:taxonomy/product/analytics` |
| "Semantic Views", "AI-powered" | `snowflake-site:taxonomy/product/ai` |

### Category Sources in AGENTS.md

1. **Product Categories** - AI, Analytics, Data Engineering, Platform
2. **Technical Use-Cases** - Ingestion, Transformation, Business Intelligence
3. **Prioritized Features** - Cortex Analyst, Snowpark, Dynamic Tables
4. **Industries** - Financial Services, Healthcare, Retail

<!-- ------------------------ -->
## Validation Checklist

Before finalizing, run through this checklist from AGENTS.md:

### Pre-Publish Verification

- [ ] Categories are from the approved list
- [ ] ID is lowercase with hyphens (not underscores)
- [ ] ID matches markdown file name (without .md extension)
- [ ] ID matches the folder name containing the markdown file
- [ ] Language tag is populated with valid code
- [ ] Title starts with an action verb
- [ ] Overview section includes all required subsections
- [ ] Prerequisites includes Snowflake account signup link as first item
- [ ] Conclusion starts with "Congratulations! You've successfully..."
- [ ] No HTML is used in the markdown
- [ ] All code snippets are preserved exactly
- [ ] Headers do not exceed H4 (`####`)
- [ ] H2 headings are 3-4 words max

### Semantic View Quickstart Validation

| Check | Status |
|-------|--------|
| ID: `build-business-ready-queries-with-snowflake-semantic-views` | ✓ Lowercase, hyphens |
| Folder: `build-business-ready-queries-with-snowflake-semantic-views/` | ✓ Matches ID |
| File: `build-business-ready-queries-with-snowflake-semantic-views.md` | ✓ Matches ID |
| Title: "Build Business-Ready Queries..." | ✓ Starts with action verb |
| Prerequisites: Snowflake signup link first | ✓ Included |
| Conclusion: "Congratulations! You've successfully..." | ✓ Correct format |

<!-- ------------------------ -->
## Output Format

The AGENTS.md specifies exactly how to package the output.

### File Structure

```
build-business-ready-queries-with-snowflake-semantic-views/
└── build-business-ready-queries-with-snowflake-semantic-views.md
```

### Key Rules

1. **Folder name** = `id` field value
2. **File name** = `id` field value + `.md`
3. **Package** = ZIP file containing the folder
4. **Delivery** = Download link (not displayed in chat)

### Why Not Display in Chat?

Quickstart markdown files are typically 500-1500+ lines. Displaying them in chat:
- Overwhelms the conversation
- Makes it hard to download
- Can cause rendering issues

Instead, provide as a downloadable ZIP file.

<!-- ------------------------ -->
## Complete Workflow Example

Let's walk through how the Semantic View quickstart was created:

### Step 1: Provide Author Name

```
User: "Chanin Nantasenamat"
```

### Step 2: Provide Source Document

```
User: build-business-ready-queries-with-snowflake-semantic-views.ipynb
```

### Step 3: AI Processes Document

The AI:
- Extracted the notebook content and structure
- Identified 12 queries organized by complexity
- Preserved all SQL code snippets exactly
- Matched categories: Analytics, AI, Quickstart
- Generated action-verb title: "Build Business-Ready Queries..."

### Step 4: Iterative Refinement

After initial generation, we refined:
- Added ASCII output examples for each query
- Added "Why it's simpler" explanations
- Added Query Complexity Framework section
- Formatted SQL keywords with backticks (`JOIN`, `WHERE`, etc.)
- Verified all documentation links

### Step 5: Final Validation

Ran through the validation checklist and confirmed all items passed.

### Step 6: Output Delivery

```
build-business-ready-queries-with-snowflake-semantic-views.zip
├── build-business-ready-queries-with-snowflake-semantic-views/
│   └── build-business-ready-queries-with-snowflake-semantic-views.md
```

<!-- ------------------------ -->
## Best Practices

Based on creating the Semantic View quickstart, here are key best practices:

### Displaying Query Output

When showing SQL query results, use ASCII tables to display expected output. This makes it easy for readers to verify their results match the expected output.

**Format:**
```
**Expected Output:** Brief description of what the query returns.

+------------+----------------+
| COLUMN_ONE | COLUMN_TWO     |
+------------+----------------+
| value1     |          12345 |
| value2     |          67890 |
| ...        |            ... |
+------------+----------------+
```

**Example from the Semantic View quickstart:**

```
**Expected Output:** Returns customer counts by state, with Texas (TX) having the most customers at over 5 million.

+----------+----------------+
| CA_STATE | CUSTOMER_COUNT |
+----------+----------------+
| TX       |        5154196 |
| GA       |        3225083 |
| VA       |        2735265 |
| KY       |        2431364 |
| ...      |            ... |
+----------+----------------+
```

**Tips for ASCII tables:**
- Align column headers with the data
- Right-align numeric values
- Use `...` to indicate truncated rows
- Include a brief summary before the table explaining what the output shows

### The Notebook as Source of Truth

The input notebook serves as the **single source of truth** for quickstart generation. A well-structured notebook contains two essential components that form the core of any quickstart:

| Component | Purpose | Example |
|-----------|---------|---------|
| **Code Documentation** | Markdown cells explaining concepts, context, and expected outcomes | "This query retrieves store information filtered by state..." |
| **Code Snippets** | Executable code cells with SQL queries, Python code, or configurations | `SELECT * FROM store WHERE s_state = 'TN'` |

The AI extracts both components from the notebook and transforms them into the quickstart format—documentation becomes explanatory prose, and code snippets are preserved exactly as written.

**Example:** The Semantic View quickstart was generated from this Snowflake Demo Notebook:
- [Snowflake_Semantic_View_Business_Ready_Queries](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Snowflake_Semantic_View_Business_Ready_Queries) - Contains all SQL queries, markdown explanations, and expected outputs that became the quickstart content.

### Content Fidelity (Preventing Hallucination)

The AGENTS.md enforces strict rules to prevent AI hallucination and ensure all content comes exclusively from the provided input document:

| Rule | Description |
|------|-------------|
| **Document-only content** | Use ONLY content from the provided document—do not infer from external sources |
| **Preserve code exactly** | Make NO changes to code snippets—preserve exactly as provided |
| **Retain structure** | Maintain the hierarchical order of sections and sub-sections from the source |
| **Deduce from document** | All content within template brackets `[ ]` must come directly from the provided document |

**Why this matters:**
- Ensures technical accuracy—AI won't invent SQL syntax or function names
- Maintains consistency between the source notebook and the published tutorial
- Prevents outdated or incorrect information from external sources
- Makes fact-checking easier since all content is traceable to the source

**Example:** If the source notebook shows a specific SQL query, that exact query must appear in the quickstart—not a "cleaned up" or "improved" version.

### Fact-Checking Is Essential

After AI generates the quickstart, **fact-checking against official documentation is critical**. The AGENTS.md includes explicit guidance for this in the Iteration section:

**What to verify:**
1. **Technical claims** - Verify SQL syntax, function names, and parameter descriptions against [Snowflake Documentation](https://docs.snowflake.com/)
2. **Links** - Ensure all URLs in Related Resources are valid and point to current documentation
3. **Terminology** - Confirm Snowflake-specific terms match official naming conventions

**Example from Semantic View quickstart:**

During fact-checking, we verified the `CREATE SEMANTIC VIEW` components against the official documentation:
- Confirmed `FACTS` refers to row-level expressions (non-aggregated), not aggregates
- Verified `METRICS` is the correct term for aggregate expressions (`SUM`, `COUNT`, `AVG`)
- Updated links to point to current documentation URLs

**AGENTS.md enforces this through:**
- Validation Checklist: "Verify all links"
- Iteration guidance: "Fact-check technical claims - Verify against official docs"
- Quick Reference: "Content source | Document only - no external"

### Adding Images Post-Generation

Images and screenshots can be added **after** the quickstart has been generated through:

1. **Manual addition** - Capture screenshots and add them to the markdown with proper formatting:
   ```markdown
   ![description of image](assets/image-name.png)
   ```

2. **Additional vibe coding rounds** - Ask the AI to suggest where images would be helpful and what they should show, then capture and add them

**Image requirements from AGENTS.md:**
- Naming: lowercase with hyphens (no underscores, no special characters)
- Maximum file size: 1 MB (GIFs may be larger but should be optimized)
- Format: Use Markdown syntax only—NOT HTML
- Location: Place in an `assets/` folder within the quickstart directory

### Formatting

1. **Format SQL keywords** - Use backticks: `JOIN`, `WHERE`, `GROUP BY`
2. **Keep H2 headings short** - 3-4 words maximum
3. **Use tables for structured data** - Quick reference, comparisons
4. **Add summaries** - Brief descriptions before/after code blocks

### Documentation

1. **Verify all links** - Check that documentation URLs are valid
2. **Include multiple resource types** - Docs, quickstarts, GitHub repos
3. **Add context** - Explain why each resource is relevant

### Iteration

1. **Review generated content** - AI may need corrections
2. **Add missing context** - Output examples, explanations
3. **Fact-check technical claims** - Verify against official docs

<!-- ------------------------ -->
## Publishing Your Work

Once your quickstart is validated and ready, submit it to the official Snowflake repositories via Pull Request.

### Submit Your Jupyter Notebook

1. Fork [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks)
2. Create a folder with your notebook name (use underscores, e.g., `Snowflake_Semantic_View_Business_Ready_Queries`)
3. Add your `.ipynb` file and any supporting files
4. Submit a Pull Request

### Submit Your Quickstart

1. Fork [sfquickstarts](https://github.com/Snowflake-Labs/sfquickstarts)
2. Navigate to `site/sfguides/src/`
3. Extract your ZIP file locally, create a folder for your quickstart at `site/sfguides/src/`, which is where your markdown file will reside. Practically, this will look like this `site/sfguides/src/build-business-ready-queries-with-snowflake-semantic-views/build-business-ready-queries-with-snowflake-semantic-views.md`
4. Submit a Pull Request

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully learned how to use the AGENTS.md file to create Snowflake Quickstarts tutorials. You now understand the complete workflow from providing a source document to generating a properly formatted, validated quickstart.

### What You Learned
- The structure and purpose of AGENTS.md
- Required metadata fields and their formats
- Content organization and header hierarchy
- Category selection from approved lists
- How notebooks serve as the source of truth (code documentation + code snippets)
- Content fidelity rules to prevent AI hallucination
- The importance of fact-checking against official documentation
- Validation checklist for pre-publish verification
- Adding images post-generation (manual or vibe coding)
- Output packaging as folder + markdown in ZIP
- How to submit your notebook and quickstart to GitHub for publishing

### Related Resources

AGENTS.md Standard:
- [agents.md](https://agents.md/) - The official specification for providing instructions to AI coding agents

Official Snowflake Quickstart Resources:
- [Get Started with Guides](https://www.snowflake.com/en/developers/guides/get-started-with-guides/) - Official guide for creating Snowflake quickstarts
- [Snowflake Guides - Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template) - Official template structure for Snowflake Guides from `sfquickstarts` repository
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides) - Official Snowflake quickstarts repository
- [Snowflake Documentation](https://docs.snowflake.com/) - Official Snowflake docs

Example Quickstarts:
- [Build Business-Ready Queries with Snowflake Semantic Views](build-business-ready-queries-with-snowflake-semantic-views/) - The example quickstart used in this tutorial

Source Notebooks:
- [Snowflake_Semantic_View_Business_Ready_Queries](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Snowflake_Semantic_View_Business_Ready_Queries) - The input notebook that was converted into the Semantic View quickstart

Publishing Your Work:
- [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks) - Submit your input Jupyter notebooks here
- [sfquickstarts](https://github.com/Snowflake-Labs/sfquickstarts) - Submit your generated quickstarts here

Happy quickstart creation!
