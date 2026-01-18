author: Chanin Nantasenamat
id: create-snowflake-guides-with-agents-md
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
summary: Learn how to use the AGENTS.md file with AI assistants to convert Jupyter notebooks into properly formatted Snowflake Guides.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues


# Create Snowflake Guides with AGENTS.md
<!-- ------------------------ -->
## Overview

Creating written tutorials can be a time-consuming and error-prone process, especially when done manually. The AGENTS.md file provides a structured approach to automate this process using AI assistants like Claude, ChatGPT, or Cursor AI.

This tutorial walks you through the complete workflow of using AGENTS.md to convert input Jupyter notebooks into properly formatted Snowflake Guides that follow official guidelines.

> **Note:** Snowflake Guides (formerly known as Snowflake Quickstarts) are step-by-step tutorials published on the Snowflake developer site. "Quickstart" is now a content type category within Snowflake Guides, alongside other types like Community Solution, Partner Solution, and Certified Solution.

### About AGENTS.md

The AGENTS.md file provides instruction and sets of rules to AI coding agents, following the standard format defined at [https://agents.md/](https://agents.md/). This standardized format ensures that AI assistants can reliably interpret and follow project-specific guidelines.

The [Snowflake Guides AGENTS.md](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Create-Snowflake-Guides-with-AGENTS-md/AGENTS.md) as proposed herein combines this standard format with specific instructions from two official Snowflake resources:

1. **[Get Started with Guides](https://www.snowflake.com/en/developers/guides/get-started-with-guides/)** - The official Snowflake Guides creation guide
2. **[Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template)** - The official template structure from the `sfquickstarts` repository

While the official markdown template can be used directly to create guides, the AGENTS.md file adds additional value by including:

- **AI-specific instructions** - Guidance for how AI assistants should process and convert documents
- **Validation checklists** - Pre-publish verification steps to catch common errors
- **Category reference tables** - Complete taxonomy analysis for automatically identifying the appropriate categories
- **Best practices** - Apply best practices in the creation of guides
- **Workflow automation** - Structured prompts and output formatting rules

### What You'll Learn
- How the AGENTS.md file structures the conversion process
- The required metadata fields and their formats
- How to organize content into the Snowflake Guides template
- Best practices for code blocks, headers, and formatting
- How to validate your generated guide

### What You'll Build
By the end of this tutorial, you'll be able to:
- Convert a Jupyter notebook into a publish-ready Snowflake Guide
- Use the AGENTS.md file to guide AI assistants through the conversion process
- Apply proper metadata, categories, and formatting to meet Snowflake's publishing standards

### Prerequisites
- Access to an AI assistant (Claude, ChatGPT, Cursor AI, or similar)
- A Jupyter notebook to convert into a guide
- Basic understanding of Markdown formatting

<!-- ------------------------ -->
## Understanding AGENTS.md

The AGENTS.md file is an instruction set that guides AI assistants through the Snowflake Guide conversion process. It contains:

### Key Components

| Component | Purpose |
|-----------|---------|
| **Agent Behavior** | What the AI should do on load |
| **Template Structure** | The exact format to follow |
| **Content Rules** | Formatting guidelines |
| **Validation Checklist** | Pre-publish verification |

### The Conversion Workflow

```
1. AI asks for author name
2. AI asks for document to convert
3. AI processes document:
   - Extracts content hierarchy
   - Matches categories
   - Preserves code snippets
   - Generates action-verb title
4. AI outputs ZIP file:
   - folder-name/
   └── folder-name.md
```

<!-- ------------------------ -->
## Anatomy of a Snowflake Guide

This section covers the key structural elements that make up a properly formatted Snowflake Guide.

### Required Metadata Fields

Every guide begins with metadata. Here's what it looks like:

#### Metadata Example

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

#### Metadata Fields

| Field | Rule | Example |
|-------|------|---------|
| `author` | Ask user | `Chanin Nantasenamat` |
| `id` | Lowercase, hyphens, matches filename AND folder | `build-business-ready-queries-with-snowflake-semantic-views` |
| `categories` | From approved list, always include quickstart | See category tables in AGENTS.md |
| `language` | Valid code: en, es, it, fr, ja, ko, pt_br | `en` |
| `summary` | One sentence description | Brief overview of the guide |
| `status` | `Published` or `Archived` | `Published` |

### Content Structure

The official Snowflake Guides template defines the specific structure that every guide must follow:

1. **Overview** (with subsections)
   - What You'll Learn
   - What You'll Build
   - Prerequisites

2. **Main Content Sections** (H2 headings)

3. **Conclusion And Resources**
   - What You Learned
   - Related Resources

#### Header Hierarchy

```markdown
## Main Section (H2) - Appears in right-side menu
### Subsection (H3) - For detailed steps
#### Sub-subsection (H4) - Maximum depth allowed
```

> **Important:** Never go beyond H4 (`####`). Deeper headings won't render correctly.

#### Example of Content Structure: Semantic View

```markdown
## Overview
### What You'll Learn
### What You'll Build
### Prerequisites

## About the TPC-DS Dataset
### Traditional SQL vs Semantic SQL
### Query Complexity Framework

## Create Semantic Views

## Traditional vs Semantic SQL

## Simple Questions
### Store Numbers in Tennessee
### Customers with Dependents
### Stores in Midway

## Advanced Questions
### Customer Count by State
...

## Conclusion And Resources
### Question/Schema Complexity: Key Findings
### Lessons Learned
### What You Learned
### Related Resources
```

### Category Selection

Categories must come from the approved lists stored in AGENTS.md. Here's how the agent selects them:

#### Content Type: Quickstart

"Quickstart" is a content type category that must be included in every guide:

```
snowflake-site:taxonomy/solution-center/certification/quickstart
```

Other content types include: Community Solution, Partner Solution, and Certified Solution.

#### Match Content to Categories

For the Semantic View guide, we matched:

| Content Keywords | Selected Category |
|-----------------|-------------------|
| "Analytics", "queries", "SQL" | `snowflake-site:taxonomy/product/analytics` |
| "Semantic Views", "AI-powered" | `snowflake-site:taxonomy/product/ai` |

#### Category Sources in AGENTS.md

1. **Product Categories** - AI, Analytics, Data Engineering, Platform
2. **Technical Use-Cases** - Ingestion, Transformation, Business Intelligence
3. **Prioritized Features** - Cortex Analyst, Snowpark, Dynamic Tables
4. **Industries** - Financial Services, Healthcare, Retail

### Validation Checklist

Before finalizing, the agent runs the generated guide through this checklist provided in AGENTS.md:

#### Pre-Publish Verification

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

#### Example of Guide Validation: Semantic View

| Check | Status |
|-------|--------|
| ID: `build-business-ready-queries-with-snowflake-semantic-views` | ✓ Lowercase, hyphens |
| Folder: `build-business-ready-queries-with-snowflake-semantic-views/` | ✓ Matches ID |
| File: `build-business-ready-queries-with-snowflake-semantic-views.md` | ✓ Matches ID |
| Title: "Build Business-Ready Queries..." | ✓ Starts with action verb |
| Prerequisites: Snowflake signup link first | ✓ Included |
| Conclusion: "Congratulations! You've successfully..." | ✓ Correct format |

### Export Format

The AGENTS.md specifies exactly how to package the generated guide.

#### File Structure

```
build-business-ready-queries-with-snowflake-semantic-views/
└── build-business-ready-queries-with-snowflake-semantic-views.md
```

#### Key Rules

1. **Folder name** = `id` field value
2. **File name** = `id` field value + `.md`
3. **Package** = ZIP file containing the folder
4. **Delivery** = Download ZIP file (i.e. depending on the AI assistant, it may only allow Copy/paste of file contents)


<!-- ------------------------ -->
## Complete Workflow Example

Let's walk through how the Semantic View guide was created:

### Step 1: Reference the agent file

Enter the following into the chat box:
```
@AGENTS.md
```

### Step 2: Provide Author Name

After a few moments, the AI will ask:
```
Welcome! I'll help you convert your document into a Snowflake Guide. Before we begin, please tell me:

What is your name? (This will be used as the author)
```

I'll go ahead and enter my name:
```
Chanin Nantasenamat
```

### Step 3: Provide Source Document

Next, the AI asks:
```
Please provide the document you'd like to convert into a tutorial.
```

I'll proceed with referencing the file by entering `@` followed by the Jupyter notebook filename (without spacing after the `@` character):
```
@build-business-ready-queries-with-snowflake-semantic-views.ipynb
```

### Step 4: AI Processes the Input Content

The AI performs the following tasks:
- Extracted the notebook's content and structure
- Identified 12 queries organized by complexity
- Preserved all SQL code snippets exactly
- Matched categories: Analytics, AI, Quickstart
- Generated action-verb title: "Build XYZ..."

### Step 5: Iterative Refinement

After initial generation, we refined:
- Added ASCII output examples for each query
- Added "Why it's simpler" explanations
- Added Query Complexity Framework section
- Formatted SQL keywords with backticks (`JOIN`, `WHERE`, etc.)
- Verified all documentation links are correct

### Step 6: Final Validation

Ran through the validation checklist and confirmed all items passed.

### Step 7: Output Delivery

Upon completion, the AI will say:
```
I've generated your Snowflake Guide.
```

This is followed by details of the generated guide:
```
### ✅ Tutorial Generated
+----------------+---------------------------------------------------------------------+
| Field          | Value                                                               |
|----------------+---------------------------------------------------------------------|
| **Author**     | Chanin Nantasenamat                                                 |
| **Title**      | Build Business-Ready Queries with Snowflake Semantic Views          |
| **ID**         | `build-business-ready-queries-with-snowflake-semantic-views`        |
| **Categories** | Quickstart, Analytics, Business Intelligence, Interactive Analytics |
| **Language**   | English (en)                                                        |
+----------------+---------------------------------------------------------------------+

### 📁 Files Created

semantic-view/
├── build-business-ready-queries-with-snowflake-semantic-views/
│ └── build-business-ready-queries-with-snowflake-semantic-views.md
└── build-business-ready-queries-with-snowflake-semantic-views.zip

### 📥 Download Location

Your ZIP file is ready at:
Users/chanin/Documents/Cursor/semantic-view/build-business-ready-queries-with-snowflake-semantic-views.zip
```

<!-- ------------------------ -->
## Best Practices

Here are some key best practices:

### The Notebook as Source of Truth

The input notebook serves as the **single source of truth** for generation of Snowflake Guides. A well-structured notebook contains two essential components that form the core of any guide:

| Component | Purpose | Example |
|-----------|---------|---------|
| **Code Documentation** | Markdown cells explaining concepts, context, and expected outcomes | "This query retrieves store information filtered by state..." |
| **Code Snippets** | Executable code cells with SQL queries, Python code, or configurations | `SELECT * FROM store WHERE s_state = 'TN'` |

The AI extracts both components from the notebook and transforms them into the guide format—documentation becomes explanatory prose, and code snippets are preserved exactly as written.

**Example:** The Semantic View guide was generated from this Jupyter notebook:
- [Snowflake_Semantic_View_Business_Ready_Queries](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Snowflake_Semantic_View_Business_Ready_Queries) - Contains all SQL queries, markdown explanations, and expected outputs that became the guide content.

### Content Fidelity (Preventing Hallucination)

The AGENTS.md enforces strict rules to prevent AI hallucination and ensure all content comes exclusively from the provided input notebook:

| Rule | Description |
|------|-------------|
| **Document-only content** | Use ONLY content from the provided document; do not infer from external sources |
| **Preserve code exactly** | Make NO changes to code snippets; preserve exactly as provided |
| **Retain structure** | Maintain the hierarchical order of sections and sub-sections from the source |
| **Deduce from document** | All content within template brackets `[ ]` must come directly from the provided document |

**Why this matters:**
- Ensures technical accuracy; AI won't invent SQL syntax or function names
- Maintains consistency between the source notebook and the published tutorial
- Prevents outdated or incorrect information from external sources
- Makes fact-checking easier since all content is traceable to the source

**Example:** If the source notebook shows a specific SQL query, that exact query must appear in the guide—not a "cleaned up" or "improved" version.

### Fact-Checking Is Essential

After AI generates the guide, fact-checking against official documentation is critical. The AGENTS.md includes explicit guidance for this in the Iteration section:

**What to verify:**
1. **Technical claims** - Verify SQL syntax, function names, and parameter descriptions against [Snowflake Documentation](https://docs.snowflake.com/)
2. **Links** - Ensure all URLs in Related Resources are valid and point to current documentation
3. **Terminology** - Confirm Snowflake-specific terms match official naming conventions

**Example from Semantic View guide:**

During fact-checking, we verified the `CREATE SEMANTIC VIEW` components against the official documentation:
- Confirmed `FACTS` refers to row-level expressions (non-aggregated), not aggregates
- Verified `METRICS` is the correct term for aggregate expressions (`SUM`, `COUNT`, `AVG`)
- Updated links to point to current documentation URLs

### Adding Images Post-Generation

Images and screenshots can be added **after** the guide has been generated through:

1. **Manual addition** - Capture screenshots and add them to the markdown with proper formatting:
   ```markdown
   ![description of image](assets/image-name.png)
   ```

2. **Additional vibe coding rounds** - Ask the AI to suggest where images would be helpful and what they should show, then capture and add them

**Image requirements from AGENTS.md:**
- Naming: lowercase with hyphens (no underscores, no special characters)
- Maximum file size: 1 MB (GIFs may be larger but should be optimized)
- Format: PNG or JPG
- Location: Place in an `assets/` folder within the guide directory

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

Once your guide is validated and ready, submit it to the official Snowflake repositories on GitHub.

### Submit Your Jupyter Notebook

1. Fork the [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks) repo
2. Create a folder with your notebook name (use underscores, e.g., `Snowflake_Semantic_View_Business_Ready_Queries`)
3. Add your `.ipynb` file and any supporting files
4. Submit a Pull Request

### Submit Your Guide

1. Fork the [sfquickstarts](https://github.com/Snowflake-Labs/sfquickstarts) repo
2. Navigate to `site/sfguides/src/`
3. Extract your ZIP file (creates the folder with your markdown file)
4. Submit a Pull Request

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You've successfully learned how to use the AGENTS.md file to create Snowflake Guides. You now understand the complete workflow from providing a source document to generating a properly formatted, validated guide.

### What You Learned
- **AGENTS.md structure** - Metadata fields, content hierarchy, and category selection
- **Source of truth** - Notebooks provide code documentation and snippets; content fidelity rules prevent hallucination
- **Quality assurance** - Validation checklist and fact-checking against official docs
- **Output & publishing** - ZIP packaging and GitHub submission workflow
- **Post-generation** - Adding images via manual capture or additional AI rounds

### Related Resources

AGENTS.md:
- [Snowflake Guides AGENTS.md](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Create-Snowflake-Guides-with-AGENTS-md/AGENTS.md)
- [AGENTS.md Guidelines](https://agents.md/) - The official specification for providing instructions to AI coding agents

Official Snowflake Guides Resources:
- [Get Started with Guides](https://www.snowflake.com/en/developers/guides/get-started-with-guides/) - Official guide for creating Snowflake Guides
- [Snowflake Guides - Markdown Template](https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/_markdown-template) - Official template structure from `sfquickstarts` repository
- [SFGuides on GitHub](https://github.com/Snowflake-Labs/sfguides) - Official Snowflake Guides repository
- [Snowflake Documentation](https://docs.snowflake.com/) - Official Snowflake docs

Example Guides:
- [Build Business-Ready Queries with Snowflake Semantic Views](build-business-ready-queries-with-snowflake-semantic-views/) - The example guide used in this tutorial

Example Notebooks:
- [Snowflake_Semantic_View_Business_Ready_Queries](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Snowflake_Semantic_View_Business_Ready_Queries) - The input notebook that was converted into the Semantic View guide
- [Create Snowflake Guides with AGENTS.md](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main/Create-Snowflake-Guides-with-AGENTS-md)

Publishing Your Work:
- [snowflake-demo-notebooks](https://github.com/Snowflake-Labs/snowflake-demo-notebooks) - Submit your input Jupyter notebooks here
- [sfquickstarts](https://github.com/Snowflake-Labs/sfquickstarts) - Submit your generated guides here

Happy creations!
