author: Joviane Bellegarde
id: cortex_ai_demo_framework
summary: Cortex AI Demo Framework - Build sophisticated Cortex-powered demos in ~5 minutes
categories: Cortex, AI, Demo Development, Getting-Started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Cortex, AI, Demo Development, Framework

# Cortex AI Demo Framework
<!-- ------------------------ -->

## Overview
Duration: 5

Demo development is crucial for businesses to showcase their AI capabilities and win new customers. Through rapid prototyping and professional presentation tools, businesses can transform weeks of development into minutes of setup, dramatically accelerating sales cycles and proof-of-concept delivery.

In this Quickstart, we will build a comprehensive demo development platform called "Cortex AI Demo Framework". This demonstrates how to use Snowflake Cortex AI functions to create synthetic data, build interactive analytics, deploy search capabilities, and generate complete demonstration environments.

This Quickstart showcases the complete Cortex AI Demo Framework with:
- **6-application integrated demo platform** with Synthetic Data Generator, Structured Tables, SQL to YAML Converter, Snow Demo, YAML Wizard, and Snow Viz
- **AI-powered data generation** using all Cortex functions
- **Advanced semantic search** and automated model creation
- **Cortex Search Service** for intelligent data discovery
- **Cortex Analyst integration** for natural language queries
- **Production-ready applications** with professional UI/UX


### What You Will Build
- Complete 6-application integrated demo platform
- AI-powered synthetic data generation system using Cortex functions
- Advanced semantic modeling and search capabilities
- Professional demo orchestration and configuration tools
- Interactive dashboard creation wizard with database introspection
- Advanced dashboard renderer with multiple visualization types
- Interactive Cortex Search Service for semantic discovery
- Production-ready Streamlit applications with advanced visualizations
- Reusable framework for rapid demo creation across any industry

### What You Will Learn
- How to set up a production demo development pipeline with Snowflake
- How to use Snowflake Notebooks for complex AI demo workflows
- How to implement all Cortex AI functions (SENTIMENT, EXTRACT_ANSWER, COMPLETE)
- How to build scalable demo platforms with synthetic data
- How to create automated semantic models and search services
- How to deploy interactive Streamlit applications in Snowflake

### Prerequisites
- Familiarity with Python and SQL
- Familiarity with Streamlit applications
- Go to the [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) sign-up page and register for a free account

<!-- ------------------------ -->
## Setup Snowflake Environment  
Duration: 5

In this step, you'll create the Snowflake database objects and prepare for framework deployment.

### Step 1: Create Database Objects

> aside positive
> 
> Starting in September 2025, Snowflake is gradually upgrading accounts from Worksheets to [Workspaces](https://docs.snowflake.com/en/user-guide/ui-snowsight/workspaces). Workspaces will become the default SQL editor. Follow the instructions below that match your interface.

**If you have Workspaces:**
1. In Snowsight, click `Projects`, then `Workspaces` in the left navigation
2. Click `+ Add new` to create a new Workspace
3. Click `SQL File` to create a new SQL file
4. Copy the setup script from [setup.sql](https://github.com/Snowflake-Labs/sfguide-cortex-demo-developer-framework/blob/main/scripts/setup.sql) and paste it into your SQL file, then run it

**If you have Worksheets:**
1. In Snowsight, click `Projects`, then `Worksheets` in the left navigation
2. Click `+` in the top-right corner to open a new Worksheet
3. Copy the setup script from [setup.sql](https://github.com/Snowflake-Labs/sfguide-cortex-demo-developer-framework/blob/main/scripts/setup.sql) and paste it into your worksheet, then run it

The setup script creates:
- **Database**: `CORTEX_FRAMEWORK_DB` with `BRONZE_LAYER`, `SILVER_LAYER`, `APPS`, and `CONFIGS` schemas
- **Role**: `CORTEX_FRAMEWORK_DATA_SCIENTIST` with all necessary permissions  
- **Warehouse**: `CORTEX_FRAMEWORK_WH` for compute resources
- **Stages**: `FRAMEWORK_DATA_STAGE`, `SEMANTIC_MODELS`, and `DEMO_CONFIGS` for file uploads
- **File Formats**: `CSV_FORMAT`, `YAML_FORMAT`, and `JSON_FORMAT` for data processing
- **AI Access**: `SNOWFLAKE.CORTEX_USER` role for Cortex functions

### Step 2: Download Required Framework Files

Download these framework files from the GitHub repository:

| File | Purpose | Download Link |
|------|---------|---------------|
| **Notebook** | Setup notebook for framework deployment | [cortex_ai_demo_framework_setup.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/notebooks/cortex_ai_demo_framework_setup.ipynb) |
| **Environment File** | Conda environment configuration for latest Streamlit | [environment.yml](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/environment.yml) |
| **Synthetic Data Generator** | AI-powered synthetic data creation | [01_ai_framework_synthetic_data_generator.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/01_ai_framework_synthetic_data_generator.py) |
| **Structured Tables** | Data structuring and transformation | [02_ai_framework_structured_tables.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/02_ai_framework_structured_tables.py) |
| **SQL to YAML Converter** | SQL to YAML configuration converter (generates semantic models) | [03_ai_framework_sql_to_yaml_converter.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/03_ai_framework_sql_to_yaml_converter.py) |
| **Snow Demo** | Demo configuration and runner | [04_ai_framework_snow_demo.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/04_ai_framework_snow_demo.py) |
| **YAML Wizard** | Interactive dashboard configuration creator | [05_ai_framework_snow_viz_yaml_wizard.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/05_ai_framework_snow_viz_yaml_wizard.py) |
| **Snow Viz** | Advanced visualization dashboard renderer | [06_ai_framework_snow_viz.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-cortex-ai-demo-framework/blob/main/scripts/06_ai_framework_snow_viz.py) |

### Step 3: Upload Framework Files to Single Stage

1. In Snowsight, change your role to `cortex_ai_demo_data_scientist`

2. Navigate to `Catalog` → `Database Explorer` → `AI_FRAMEWORK_DB` → `APPS` → `Stages`

**Upload all framework files to the single `AI_FRAMEWORK_APPS` stage:**

3. Click on `AI_FRAMEWORK_APPS` stage, then click `Enable Directory Table` and upload all 7 files:
   - `01_ai_framework_synthetic_data_generator.py`
   - `02_ai_framework_structured_tables.py`
   - `03_ai_framework_sql_to_yaml_converter.py`
   - `04_ai_framework_snow_demo.py`
   - `05_ai_framework_snow_viz_yaml_wizard.py`
   - `06_ai_framework_snow_viz.py`
   - `environment.yml`

### Step 4: Import the Framework Setup Notebook

1. **Import into Snowflake**:
   - Navigate to `Projects` → `Notebooks` in Snowsight
   - Click the down arrow next to `+ Notebook` and select `Import .ipynb file`
   - Choose `cortex_ai_demo_framework_setup.ipynb` from your downloads

2. **Configure the notebook settings**:
   - **Role**: Select `cortex_ai_demo_data_scientist`
   - **Database**: Select `AI_FRAMEWORK_DB`
   - **Schema**: Select `BRONZE_LAYER`  
   - **Query Warehouse**: Select `cortex_ai_demo_wh`
   - **Notebook Warehouse**: Select `cortex_ai_demo_wh`

3. **Click `Create`** to import the notebook

The notebook creates all 6 Streamlit applications using the single stage approach with automatic environment.yml detection for the latest Streamlit version.

<!-- ------------------------ -->
## Run Framework Demo Notebook
Duration: 8

### Execute the Framework Deployment Workflow

1. Go to `Projects` → `Notebooks` in Snowsight
2. Click on `CORTEX_FRAMEWORK_DEMO` Notebook to open it
3. Click `Run all` to execute all cells in the notebook at once

**What the notebook does:**
- Creates sample customer survey data tables
- Processes data with Cortex AI functions (SENTIMENT, EXTRACT_ANSWER, COMPLETE)
- Deploys all 6 Streamlit applications from the uploaded stage files
- Sets up the complete framework for immediate demo creation

The notebook processes sample data and deploys the complete framework application suite.

<!-- ------------------------ -->
## Explore Framework Applications
Duration: 10

### Access Your Demo Framework

1. Navigate to `Projects` → `Streamlit` in Snowsight
2. You'll see 6 framework applications deployed:

### Core Applications

#### **Synthetic Data Generator** (Start Here 🚀)
**Purpose**: Create realistic AI-powered datasets for any industry
**How to use**: 
- Select industry template (retail, healthcare, finance, etc.)
- Define data parameters (rows, columns, relationships)
- Generate synthetic data with AI-powered realistic values
- Export to Snowflake tables for immediate use

#### **Structured Tables** 
**Purpose**: Design optimal data schemas and relationships
**How to use**:
- Import existing table structures or create new ones
- Define relationships between tables (foreign keys, joins)
- Optimize schema design for analytics performance
- Generate DDL scripts for table creation

#### **SQL to YAML Converter**
**Purpose**: Generate semantic models for Cortex Analyst integration
**How to use**:
- Input SQL queries or table structures
- Automatically convert to YAML semantic model format
- Configure dimensions, measures, and relationships
- Deploy semantic models for natural language querying

#### **Snow Demo**
**Purpose**: Configure and orchestrate complete demo scenarios
**How to use**:
- Combine data, visualizations, and AI insights into demo flows
- Set up presentation sequences and talking points
- Configure demo parameters and customizations
- Execute end-to-end demo scenarios

#### **YAML Wizard**
**Purpose**: Interactive dashboard configuration creator with database introspection
**How to use**:
- Connect to any Snowflake database and analyze table structures
- Auto-detect dimensions, metrics, and data relationships
- Customize dashboard configurations through guided interface
- Generate YAML files for advanced dashboard creation
- Create Intelligence Agents for natural language data interaction

#### **Snow Viz**
**Purpose**: Advanced dashboard renderer that uses YAML configurations
**How to use**:
- Load YAML configurations created by YAML Wizard or manually
- Render interactive dashboards with multiple visualization types
- Support for Overview, Product, Compare, TopN, Search, and Analyst tabs
- Integrate Cortex Search and Cortex Analyst capabilities
- Export and share professional dashboard presentations

### Demo Creation Workflow

**Create a complete demo in ~5 minutes:**

**Step 1: Data Creation** (Required)
→ Use **Synthetic Data Generator** to create realistic datasets

**Optional Enhancements:**
- **Schema Design** → Use **Structured Tables** to optimize data organization
- **AI Integration** → Use **SQL to YAML Converter** for Cortex Analyst capabilities
- **Dashboard Configuration** → Use **YAML Wizard** to create interactive dashboard configs
- **Visualization** → Use **Snow Viz** to render dashboards from YAML configurations
- **Demo Orchestration** → Use **Snow Demo** to configure presentation flow

### Framework Capabilities

- **Industry Templates**: Retail, Financial Services, Healthcare, Manufacturing, Telecommunications
- **AI Features**: Sentiment analysis, text generation, semantic search, natural language queries
- **Visualization Types**: Charts, dashboards, interactive filters, drill-down capabilities
- **Performance**: Real-time data generation, sub-second dashboard response, scalable architecture

<!-- ------------------------ -->
## Clean Up Resources
Duration: 3

### Remove All Created Objects

When you're ready to remove all the resources created during this quickstart:

1. Open the [setup.sql](https://github.com/Snowflake-Labs/sfguide-cortex-demo-developer-framework/blob/main/scripts/setup.sql) script
2. Scroll to the bottom to find the "TEARDOWN SCRIPT" section
3. Uncomment the teardown statements
4. Run the freshly uncommented script to remove all databases, warehouses, roles, and objects

This will clean up all framework components while preserving any other work in your Snowflake account.

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 2

Congratulations! You've successfully built the complete Cortex AI Demo Framework using Snowflake Cortex AI!

### What You Learned
- **8-Application Demo Platform**: How to build Framework Overview, Synthetic Data Generator, Data Provider, Structured Tables, YAML Wizard, Semantic Model Creator, Demo Orchestrator, and Advanced Visualizations
- **Advanced AI Processing**: How to implement complete Cortex AI integration with SENTIMENT, EXTRACT_ANSWER, and COMPLETE functions
- **Cortex Search Service**: How to create semantic search across synthetic data with natural language queries
- **Production-Ready Streamlit Apps**: How to develop complete interactive demo platform with advanced visualizations
- **Rapid Demo Development**: How to transform weeks of development into minutes of setup

### Resources
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit in Snowflake](https://docs.snowflake.com/developer-guide/streamlit/about-streamlit)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
