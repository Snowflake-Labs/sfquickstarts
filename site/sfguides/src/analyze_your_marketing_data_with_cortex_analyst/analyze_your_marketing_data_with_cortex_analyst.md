author: Zachary Bricker
id: analyze_your_marketing_data_with_cortex_analyst
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Analyzing Your Marketing Data with Cortex Analyst
<!-- ------------------------ -->
## Overview 
Duration: 2

In this guide, you will learn how to integrate your marketing data into Snowflake, set up Cortex Analyst, and build a custom marketing analyst Large Language Model (LLM) to interact with your data using natural language queries. By following this guide, you will be able to perform advanced analytics on your marketing campaigns and gain valuable insights.

### Prerequisites
- Basic understanding of SQL and Python
- Familiarity with Snowflake and its interface

### What You’ll Learn 
- How to import your marketing data into Snowflake
- How to set up and use the Semantic Model Generator
- How to configure Cortex Analyst to use your semantic models
- How to interact with your data using Cortex Analyst and natural language queries

### What You’ll Need 
- Access to a Snowflake account
- Marketing data exports from platforms like Google Ads, Facebook Ads, and Mailchimp (or use the provided demo data)
- [GitHub](https://github.com/) account to access the demo files
- [Python 3.8+](https://www.python.org/downloads/) installed
- [Streamlit](https://streamlit.io/) installed
- [Snowflake Connector for Python](https://docs.snowflake.com/en/developer-guide/python-connector) installed

### What You’ll Build 
- A Snowflake data warehouse containing your marketing data
- Semantic models for your data using the Semantic Model Generator
- A custom marketing analyst LLM powered by Cortex Analyst
- A Streamlit app to interact with your data using natural language queries

<!-- ------------------------ -->
## Step 1: Gather Your Marketing Data
Duration: 5

To begin, you need to gather your marketing data from various sources. You can obtain your data through marketing ETL solutions or by exporting data directly from your marketing platforms such as Google Ads, Facebook Ads, and Mailchimp.

For the purpose of this guide, you can also use our provided demo data, which you can download from our GitHub repository:

<button>

  [Download Demo Marketing Data](https://github.com/your-repo/marketing-data-demo)
</button>

*Note: Replace the placeholder link with the actual URL to your GitHub repository containing the demo data.*

<!-- ------------------------ -->
## Step 2: Set Up Your Snowflake Environment
Duration: 10

### Create a Warehouse, Database, and Schema

1. **Log in to your Snowflake account** via the web interface.

2. **Create a new Warehouse**:

   - Navigate to the **Warehouses** tab.
   - Click on **Create** and enter the following details:
     - **Name**: `MARKETING_WH`
     - **Size**: Choose an appropriate size (e.g., `X-SMALL`)
     - **Auto Suspend**: Set to `5` minutes
     - **Auto Resume**: Enabled
   - Click **Finish** to create the warehouse.

3. **Create a new Database**:

   - Navigate to the **Databases** tab.
   - Click on **Create** and enter the following details:
     - **Name**: `MARKETING_DEMO`
   - Click **Finish** to create the database.

4. **Create a new Schema**:

   - In the **MARKETING_DEMO** database, click on **Schemas**.
   - Click on **Create** and enter the following details:
     - **Name**: `MARKETING_DATA`
   - Click **Finish** to create the schema.

### Set the Context for Your Session

Before proceeding, ensure that your session is using the correct warehouse, database, and schema.

In the **Worksheet** tab, run the following SQL commands:

```sql
USE WAREHOUSE MARKETING_WH;
USE DATABASE MARKETING_DEMO;
USE SCHEMA MARKETING_DATA;
```

<!-- ------------------------ -->
## Step 3: Create Tables and Import Data
Duration: 10

### Create Tables for Your Marketing Data

Assuming you have data from Google Ads, Facebook Ads, and Mailchimp, you will create tables to store this data.

#### 1. Create Table for Google Ads Data

```sql
CREATE OR REPLACE TABLE GOOGLE_ADS_DATA (
  date DATE,
  campaign_name STRING,
  ad_group_name STRING,
  device_type STRING,
  geo_targeting STRING,
  age STRING,
  gender STRING,
  impressions INTEGER,
  clicks INTEGER,
  cost FLOAT,
  user_id STRING,
  conversions INTEGER,
  conversion_value FLOAT,
  conv_rate FLOAT,
  cost_per_conv FLOAT
);
```

#### 2. Create Table for Facebook Ads Data

```sql
CREATE OR REPLACE TABLE FACEBOOK_ADS_DATA (
  date DATE,
  campaign_name STRING,
  ad_set_name STRING,
  placement STRING,
  age STRING,
  gender STRING,
  region STRING,
  impressions INTEGER,
  reach INTEGER,
  clicks INTEGER,
  cost FLOAT,
  user_id STRING,
  conversions INTEGER,
  revenue FLOAT,
  purchase_roas FLOAT,
  cpc FLOAT,
  ctr FLOAT
);
```

#### 3. Create Table for Mailchimp Campaigns

```sql
CREATE OR REPLACE TABLE MAILCHIMP_CAMPAIGNS (
  email_address STRING,
  user_id STRING,
  campaign_name STRING,
  send_time DATE,
  open_rate FLOAT,
  click_rate FLOAT,
  last_opened DATE,
  last_clicked DATE,
  total_opens INTEGER,
  total_clicks INTEGER
);
```

### Import Data into Snowflake

You can load your data into Snowflake using the web interface or the SnowSQL command-line tool.

#### Using the Web Interface:

1. **Navigate to the Table**:

   - Go to **Databases** > **MARKETING_DEMO** > **MARKETING_DATA** > **Tables**.
   - Select the table you want to load data into (e.g., `GOOGLE_ADS_DATA`).

2. **Load Data**:

   - Click on **Load Data**.
   - Select **Load from your computer**.
   - Choose the CSV file corresponding to the table.
   - Configure the loading options:
     - **File Format**: Create a new file format or use an existing one (e.g., `CSV` with header).
     - **Header Rows to Skip**: `0`
   - Click **Load** to start the data import.

3. **Repeat** the steps for each table and corresponding data file.

#### Verify Data Load

After loading the data, you can run a simple query to verify:

```sql
SELECT * FROM GOOGLE_ADS_DATA LIMIT 10;
```

<!-- ------------------------ -->
## Step 4: Set Up the Semantic Model Generator
Duration: 10

The Semantic Model Generator is a tool that creates semantic model YAML files based on your database schema, which are used by Cortex Analyst.

### Install the Semantic Model Generator

Assuming you have Python installed, run the following command to clone the Semantic Model Generator repository:

```bash
git clone https://github.com/Snowflake-Labs/semantic-model-generator.git
```

### Install Dependencies

Navigate to the cloned directory and install the required Python packages:

```bash
cd semantic-model-generator
pip install -r requirements.txt
```

### Configure Connection Parameters

Create a `config.yaml` file with your Snowflake connection details:

```yaml
snowflake:
  account: "<your_account>"
  user: "<your_username>"
  password: "<your_password>"
  role: "<your_role>"
  warehouse: "MARKETING_WH"
  database: "MARKETING_DEMO"
  schema: "MARKETING_DATA"
```

*Note: Replace `<your_account>`, `<your_username>`, etc., with your actual Snowflake credentials.*

### Generate Semantic Models

Run the Semantic Model Generator to create YAML files for your tables:

```bash
python generate_semantic_models.py --tables GOOGLE_ADS_DATA,FACEBOOK_ADS_DATA,MAILCHIMP_CAMPAIGNS
```

This will create YAML files for each table in the `models` directory.

<!-- ------------------------ -->
## Step 5: Adjust Semantic Models
Duration: 5

Review and edit the generated YAML files to add descriptions and synonyms for fields, enhancing the natural language understanding of Cortex Analyst.

For example, in `GOOGLE_ADS_DATA.yaml`, you can add synonyms:

```yaml
- name: impressions
  type: sum
  expression: impressions
  description: 'The total number of times your Google Ads were displayed to users.'
  synonyms:
    - 'ad views'
    - 'display count'
    - 'times shown'
```

Repeat this process for each field in your semantic models.

<!-- ------------------------ -->
## Step 6: Upload Semantic Models to Snowflake
Duration: 5

Upload the semantic model YAML files to a stage in Snowflake for Cortex Analyst to access.

### Create a Stage

```sql
CREATE OR REPLACE STAGE SEMANTIC_MODELS_STAGE;
```

### Upload Files to the Stage

Use the Snowflake web interface or the SnowSQL command-line tool to upload the files.

#### Using SnowSQL:

```bash
snowsql -a <your_account> -u <your_username> -p
```

Once logged in:

```sql
PUT file://path/to/semantic_models/*.yaml @SEMANTIC_MODELS_STAGE;
```

*Note: Replace `path/to/semantic_models` with the actual path to your YAML files.*

<!-- ------------------------ -->
## Step 7: Set Up Cortex Analyst
Duration: 15

Cortex Analyst is an open-source tool that allows you to interact with your data using natural language queries.

### Install Cortex Analyst

Assuming you have Python and Streamlit installed, install Cortex Analyst:

```bash
pip install cortex-analyst
```

### Configure Cortex Analyst

Create a `config.yaml` file for Cortex Analyst:

```yaml
database:
  type: snowflake
  account: "<your_account>"
  user: "<your_username>"
  password: "<your_password>"
  role: "<your_role>"
  warehouse: "MARKETING_WH"
  database: "MARKETING_DEMO"
  schema: "MARKETING_DATA"

models:
  path: "@SEMANTIC_MODELS_STAGE/"
```

### Run Cortex Analyst

Start the Cortex Analyst application:

```bash
streamlit run cortex_analyst_app.py
```

*Note: Replace `cortex_analyst_app.py` with the actual script or entry point for Cortex Analyst.*

<!-- ------------------------ -->
## Step 8: Interact with Your Data Using Cortex Analyst
Duration: 10

With Cortex Analyst running, you can now interact with your marketing data using natural language queries.

### Example Queries

- "Show total impressions and clicks by campaign name in Google Ads data."
- "What is the average open rate for Mailchimp campaigns?"
- "List the top regions by conversions in Facebook Ads data."

### Analyze Results

Review the results returned by Cortex Analyst and refine your queries as needed to gain insights into your marketing data.

<!-- ------------------------ -->
## Conclusion and Resources
Duration: 2

Congratulations! You have successfully set up a Snowflake data warehouse with your marketing data, created semantic models, configured Cortex Analyst, and interacted with your data using natural language queries.

### What You Learned

- How to import marketing data into Snowflake
- How to generate and adjust semantic models using the Semantic Model Generator
- How to configure and use Cortex Analyst to perform natural language queries
- How to gain insights from your marketing data across different platforms

### Related Resources

- [Cortex Analyst GitHub Repository](https://github.com/Snowflake-Labs/cortex-analyst)
- [Semantic Model Generator GitHub Repository](https://github.com/Snowflake-Labs/semantic-model-generator)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)