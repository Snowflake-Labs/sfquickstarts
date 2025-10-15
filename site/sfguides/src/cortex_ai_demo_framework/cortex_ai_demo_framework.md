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
## Framework Overview
Duration: 3

### Access Your Demo Framework

1. Navigate to `Projects` → `Streamlit` in Snowsight
2. You'll see 6 framework applications deployed

### The 6 Applications

#### **1. Synthetic Data Generator** 🎲 (Always Start Here)
Creates realistic AI-powered datasets using Cortex LLMs. Saves raw JSON to `BRONZE_LAYER` tables.

#### **2. Structured Tables** 🔄
Transforms raw JSON into clean, structured database tables. Outputs analytics-ready data to `SILVER_LAYER`.

#### **3. SQL to YAML Converter** ⚙️
Converts SQL queries into interactive demo configurations for Snow Demo (App 4).

#### **4. Snow Demo** 📊
Runs interactive SQL-driven presentations with live visualizations and AI experimentation.

#### **5. YAML Wizard** 🧙
Guided dashboard configuration creator. Generates YAML files for Snow Viz (App 6).

#### **6. Snow Viz** 📈
Renders advanced interactive dashboards with multi-tab analytics and AI integration.

### Application Dependencies

```console
1. SYNTHETIC DATA GENERATOR (START HERE)
   └─ Creates realistic datasets
      │
      ├─ 2. STRUCTURED TABLES
      │  └─ Transforms JSON → SQL tables
      │     │
      │     └─ 5. YAML WIZARD
      │        └─ Generates dashboard configs
      │           │
      │           └─ 6. SNOW VIZ
      │              └─ Renders dashboards
      │
      └─ 3. SQL TO YAML CONVERTER
         └─ Converts queries → demo configs
            │
            └─ 4. SNOW DEMO
               └─ Runs interactive SQL demos
```

**Next**: Page 5 shows which apps to use based on your role and goals.

<!-- ------------------------ -->
## Persona Workflows
Duration: 5

### Who Should Use This Framework?

The framework supports **4 different user personas**. Find your role below to see which apps you need and in what order.

---

### Persona 1: Full-Stack Data Developer

**Who You Are**:
- Data engineers building end-to-end pipelines
- Analytics developers creating dashboards
- Technical users who want the complete experience

**What You'll Build**: A complete analytics pipeline from data generation to interactive dashboards

**Apps You'll Use**: Synthetic Data Generator → Structured Tables → YAML Wizard → Snow Viz

**Time Required**: ~25 minutes

**Your Workflow**:
1. **Synthetic Data Generator**: Generate synthetic data
2. **Structured Tables**: Transform JSON to structured table
3. **YAML Wizard**: Create dashboard configuration
4. **Snow Viz**: View your interactive dashboard

**What You'll Get**:
- Synthetic dataset with realistic values
- Clean, structured database table
- Interactive dashboard with multiple visualization tabs

---

### Persona 2: SQL Demo Creator / Solutions Architect

**Who You Are**:
- Solutions architects building customer demos
- Technical evangelists presenting Snowflake capabilities
- Demo creators showcasing SQL + AI features

**What You'll Build**: Interactive SQL-driven presentations with live query execution and AI experimentation

**Apps You'll Use**: Synthetic Data Generator → Structured Tables → SQL to YAML Converter → Snow Demo

**Time Required**: ~30 minutes

**Your Workflow**:
1. **Synthetic Data Generator**: Generate synthetic data for demos
2. **Structured Tables**: Create structured table
3. **SQL to YAML Converter**: Write SQL queries and convert to demo format
4. **Snow Demo**: Run interactive SQL presentation

**What You'll Get**:
- Realistic demo dataset
- Multi-step SQL presentation
- Interactive visualizations with live AI experimentation

---

### Persona 3: Data Preparation Specialist

**Who You Are**:
- Data scientists needing training data
- ML engineers requiring test datasets
- BI developers prototyping dashboards

**What You'll Build**: Clean, structured datasets for export to external tools (notebooks, ML pipelines, BI tools)

**Apps You'll Use**: Synthetic Data Generator → Structured Tables

**Time Required**: ~15 minutes

**Your Workflow**:
1. **Synthetic Data Generator**: Generate synthetic data
2. **Structured Tables**: Transform to structured table
3. Export data via CSV, Python/Snowpark, or direct BI tool connections

**What You'll Get**:
- Production-ready synthetic datasets
- Validated data quality
- Export-ready structured tables

---

### Persona 4: Dashboard Consumer / Executive

**Who You Are**:
- Business executives viewing insights
- Managers making data-driven decisions
- Analysts exploring pre-built dashboards

**What You'll Do**: View and interact with dashboards created by your data team (no setup required)

**Apps You'll Use**: Snow Viz only (after colleague completes setup)

**Time Required**: ~5 minutes

**Prerequisites**:
A colleague must first complete Synthetic Data Generator → Structured Tables → YAML Wizard to create the dashboard. Once that's done, you can view and explore it.

**Your Workflow**:
1. **Snow Viz**: Open app and select dashboard
2. Explore tabs with different visualization types
3. Use AI Assistant to ask questions in plain English
4. Export data to CSV for further analysis

**What You Can Do**:
- View key metrics and trends
- Ask questions in natural language
- Export results to spreadsheets

---

### Choose Your Path

**Ready to get started?** Jump to the pages for your persona:

| Persona | Apps to Follow | What You'll Build |
|---------|----------------|-------------------|
| **Full-Stack Developer** | Synthetic Data Generator → Structured Tables → YAML Wizard → Snow Viz | Complete analytics pipeline with dashboards |
| **SQL Demo Creator** | Synthetic Data Generator → Structured Tables → SQL to YAML Converter → Snow Demo | Interactive SQL presentations with AI |
| **Data Preparation** | Synthetic Data Generator → Structured Tables | Clean datasets for ML/BI/external tools |
| **Dashboard Consumer** | Snow Viz only | Explore pre-built dashboards (no setup) |

**Or read all app instructions** (Pages 6-11) to understand the full framework capabilities.

<!-- ------------------------ -->
## Synthetic Data Generator
Duration: 10

**Purpose**: Create realistic AI-powered datasets for any business scenario using Cortex LLMs  
**Dependencies**: None (START HERE)  
**Output**: Raw JSON data saved to `BRONZE_LAYER` tables

### Who Uses This App

**All Personas start here!** This is the foundation of the framework.

- **Persona 1** (Full-Stack Developer): Generate 100 records for dashboards
- **Persona 2** (SQL Demo Creator): Generate 150 records for presentations  
- **Persona 3** (Data Preparation): Generate 300+ records for ML/BI export
- **Persona 4** (Dashboard Consumer): Your colleague uses this to create data for you

---

### Step-by-Step Instructions

#### Step 1: Open the App

Navigate to `Projects` → `Streamlit` → **`SYNTHETIC_DATA_GENERATOR`**

#### Step 2: Configuration Management (Optional)

**Left Sidebar - Top Section:**
```
Load Configuration: Create New ▼

If you have saved configurations, select one from dropdown and click:
📁 Load Configuration
```

For first-time use, leave as "Create New"

#### Step 3: Dataset Configuration

**Left Sidebar:**

```
Company Name: TechCorp
(Default: "Acme Corp" - change to your company)

Topic/Domain: Customer Orders
(Default: "Customer Orders" - change to your use case)
```

**Examples**:
- Retail: "RetailCorp" + "Product Sales"
- Healthcare: "MedCenter" + "Patient Vitals"
- Finance: "FinanceFirst" + "Loan Applications"

#### Step 4: Define Data Fields

**Left Sidebar - Fields Section:**

```
Fields (one per line):
customer_id
customer_name
email
order_date
product_name
quantity
price
total_amount
```

**Tips**:
- One field per line
- Use descriptive field names
- Include date fields for time-series analysis
- Add 6-10 fields for realistic datasets

#### Step 5: Batch Configuration

**Left Sidebar:**

```
Records per Batch: 10
(Slider: 10-200, step 10)

Number of Batches: 10
(Slider: 1-1000)

Total records to generate: 100
```

> aside positive
> 
> **Recommended Settings**:
> - **Testing**: 10 records × 10 batches = 100 records (~2-3 min)
> - **Demos**: 30 records × 15 batches = 450 records (~8-10 min)
> - **Production**: 50 records × 20 batches = 1000 records (~15-20 min)

**Why smaller batches?**
- Higher accuracy (95%+ valid JSON)
- Faster generation per batch
- Better error recovery

#### Step 6: Configure Cortex LLM

**Left Sidebar:**

```
Model Type: LARGE ▼
(Options: SMALL, MEDIUM, LARGE)

Model: mistral-large2 ▼
(Recommended for consistent results)

Temperature: 0.7
(Slider: 0.0-1.0, step 0.1)

Max Tokens: 4000
(Slider: 100-8000, step 100)
```

> aside positive
> 
> **Model Selection Guide**:
> - **mistral-large2** (LARGE): Best accuracy, handles any batch size
> - **mixtral-8x7b** (MEDIUM): Good balance, use ≤30 records/batch
> - **llama3.1-8b** (SMALL): Fastest, use ≤20 records/batch
> 
> **Temperature Guide**:
> - **0.1-0.3**: Medical/financial data (high consistency)
> - **0.7**: General business data (balanced)
> - **0.9**: Creative content (reviews, feedback)

#### Step 7: Performance Configuration

**Left Sidebar:**

```
☑ High-Performance Mode
(Uses stored procedures - RECOMMENDED)

☐ Show Manual Scripts
(Leave unchecked unless you need SQL)
```

Keep "High-Performance Mode" checked for best results!

#### Step 8: Auto-save Configuration

**Left Sidebar:**

```
☑ Auto-save batches to table

Database: AI_FRAMEWORK_DB
Schema: BRONZE_LAYER
Table Name: techcorp_orders

☑ Append to existing table
```

> aside positive
> 
> **Important**: Data saves to `BRONZE_LAYER` first. You'll transform it to `SILVER_LAYER` in App 2!

#### Step 9: Generate Data

**Main Panel:**

1. Click **"Generate Default Prompts"** button
   - System prompt appears (left column)
   - User prompt appears (right column)
   - You can edit these if needed

2. Review the prompts (300px text areas)
   - System prompt: Instructions for AI behavior
   - User prompt: Specific data requirements

3. Scroll down and click **"🎲 Generate Synthetic Data"**

4. Watch progress:
   ```
   Batch 1/10: Generated 10 records
   Batch 2/10: Generated 10 records
   ...
   Batch 10/10: Generated 10 records
   ```

Generation time: ~2-3 minutes for 100 records

#### Step 10: Verify Success

**Expected Output**:
```
Generated 100 records successfully!
Data saved to: AI_FRAMEWORK_DB.BRONZE_LAYER.TECHCORP_ORDERS

Sample data preview:
| CUSTOMER_NAME | PRODUCT_NAME | QUANTITY | PRICE | TOTAL_AMOUNT |
|---------------|--------------|----------|-------|--------------|
| Sarah Johnson | Laptop Pro   | 1        | 1299  | 1299         |
| Mike Chen     | Wireless Mouse| 2       | 29    | 58           |
```

**Verification Steps**:

1. Go to Snowsight → **Data** → **Databases** → **AI_FRAMEWORK_DB** → **BRONZE_LAYER**
2. Find your table (e.g., `TECHCORP_ORDERS`)
3. Click to view:
   - Should see **10 rows** (one per batch)
   - Each row has **MESSAGES** column with JSON array
   - Check **_META_** columns for generation metadata

**Data Quality Check**:
```sql
-- Run this query to check your data
SELECT 
    COUNT(*) as total_batches,
    SUM(_META_RECORDS_IN_BATCH) as total_records,
    AVG(_META_RECORDS_IN_BATCH) as avg_records_per_batch,
    _META_COMPANY_NAME,
    _META_TOPIC
FROM AI_FRAMEWORK_DB.BRONZE_LAYER.TECHCORP_ORDERS
GROUP BY _META_COMPANY_NAME, _META_TOPIC;
```

Expected: 10 batches, 100 total records

#### Step 11: Save Configuration (Optional)

**Bottom of Main Panel:**

```
Configuration Name: TechCorp_Customer_Orders_Config

💾 Save Configuration
```

Save your configuration to reuse later with different batch sizes or models!

---

### Common Use Cases

#### **Retail / E-commerce**
```
Company: ShopSmart
Topic: Product Sales
Fields: product_id, product_name, category, sale_date, sale_amount, 
        customer_segment, region, payment_method
```

#### **Healthcare**
```
Company: MedCenter
Topic: Patient Vitals
Fields: patient_id, age, gender, blood_pressure_systolic, 
        blood_pressure_diastolic, heart_rate, temperature, 
        oxygen_saturation, recorded_date
```

#### **Financial Services**
```
Company: FinanceFirst
Topic: Loan Applications
Fields: application_id, applicant_name, loan_amount, credit_score, 
        income, employment_status, application_date, approval_status
```

---

### Troubleshooting

#### **Issue: Generation is slow**
**Solution**: 
- Reduce batch size (try 10 records/batch)
- Use smaller model (llama3.1-8b for speed)
- Check warehouse size (use Medium or Large)

#### **Issue: Invalid JSON in results**
**Solution**:
- Lower temperature (try 0.3 for consistency)
- Reduce batch size (10-20 records)
- Use mistral-large2 model (best accuracy)

#### **Issue: Data doesn't look realistic**
**Solution**:
- Edit prompts to be more specific
- Add industry context in Topic/Domain
- Include expected value ranges in field descriptions

#### **Issue: Date fields have invalid dates**
**Solution**:
- App automatically adds YYYY-MM-DD formatting instructions
- Use TRY_TO_DATE() in queries to filter invalid dates
- Lower temperature (0.1-0.3) for better date consistency

---

### Best Practices

**Start small**: Test with 10 records × 10 batches first  
**Use mistral-large2**: Best accuracy across all scenarios  
**Name tables descriptively**: Include company/topic in table name  
**Save configurations**: Reuse settings for consistent results  
**Check data quality**: Verify first batch before generating more  
**Use appropriate temperature**: Low for factual, high for creative

---

### What's Next?

**For All Personas**:
→ Continue to **Page 7 (App 2 - Structured Tables)** to transform your data from `BRONZE_LAYER` to `SILVER_LAYER`

Your data is now in raw JSON format. App 2 will clean and structure it into proper database columns!

<!-- ------------------------ -->
## Structured Tables
Duration: 8

**Purpose**: Transform raw JSON data into clean, structured database tables  
**Dependencies**: Requires data from App 1  
**Output**: Analytics-ready data in `SILVER_LAYER` tables

### Who Uses This App

- **Persona 1** (Full-Stack Developer): Transform to structured tables for dashboards
- **Persona 2** (SQL Demo Creator): Clean data for SQL presentations
- **Persona 3** (Data Preparation): Structure data before export to ML/BI tools
- **Persona 4** (Dashboard Consumer): Your colleague uses this to prepare data

---

**[FULL DETAILED INSTRUCTIONS WILL BE ADDED HERE - Similar to App 1 format above]**

**Next**: Continue to Page 8, 10, or 11 depending on your persona workflow.

<!-- ------------------------ -->
## SQL to YAML Converter
Duration: 10

**Purpose**: Convert SQL queries into interactive demo configurations for Snow Demo  
**Dependencies**: Requires tables from App 1 or 2  
**Output**: YAML files for `FRAMEWORK_YAML_STAGE`

### Who Uses This App

- **Persona 2** (SQL Demo Creator): Convert SQL queries to demo YAML

---

**[FULL DETAILED INSTRUCTIONS WILL BE ADDED HERE - Similar to App 1 format above]**

**Next**: Continue to Page 9 (App 4 - Snow Demo) to run your interactive SQL presentation.

<!-- ------------------------ -->
## Snow Demo
Duration: 10

**Purpose**: Run interactive SQL-driven presentations with live visualizations  
**Dependencies**: Requires YAML configs from App 3 (uploaded to `FRAMEWORK_YAML_STAGE`)  
**Output**: Live demo orchestration with charts and AI experimentation

### Who Uses This App

- **Persona 2** (SQL Demo Creator): Present interactive SQL demos with live AI

---

**[FULL DETAILED INSTRUCTIONS WILL BE ADDED HERE - Similar to App 1 format above]**

**Next**: Your demo is complete! Return to Page 5 to explore other workflows or see cleanup instructions on Page 12.

<!-- ------------------------ -->
## YAML Wizard
Duration: 12

**Purpose**: Create dashboard configurations through guided interface  
**Dependencies**: Requires tables from App 1 or 2  
**Output**: YAML files for `VISUALIZATION_YAML_STAGE`

### Who Uses This App

- **Persona 1** (Full-Stack Developer): Create dashboard YAML from structured tables

---

**[FULL DETAILED INSTRUCTIONS WILL BE ADDED HERE - Similar to App 1 format above]**

**Next**: Continue to Page 11 (App 6 - Snow Viz) to view your interactive dashboard.

<!-- ------------------------ -->
## Snow Viz
Duration: 10

**Purpose**: Render advanced interactive dashboards from YAML configurations  
**Dependencies**: Requires YAML configs from App 5 (uploaded to `VISUALIZATION_YAML_STAGE`)  
**Output**: Multi-tab analytics dashboards with AI integration

### Who Uses This App

- **Persona 1** (Full-Stack Developer): View complete analytics dashboard
- **Persona 4** (Dashboard Consumer): Explore pre-built dashboards (read-only)

---

**[FULL DETAILED INSTRUCTIONS WILL BE ADDED HERE - Similar to App 1 format above]**

**Next**: Your dashboard is complete! Return to Page 5 to explore other workflows or see cleanup instructions on Page 12.

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
- **6-Application Demo Platform**: How to build complete demo infrastructure from data generation to visualization
- **Persona-Based Workflows**: How different roles use the framework for their specific needs
- **Advanced AI Processing**: How to implement Cortex AI integration with SENTIMENT, EXTRACT_ANSWER, and COMPLETE functions
- **Production-Ready Streamlit Apps**: How to develop interactive demo platforms with advanced visualizations
- **Rapid Demo Development**: How to transform weeks of development into minutes of setup

### Resources
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit in Snowflake](https://docs.snowflake.com/developer-guide/streamlit/about-streamlit)
- [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
