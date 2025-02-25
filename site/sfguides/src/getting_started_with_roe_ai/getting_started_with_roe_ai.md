author: 
id: getting-started-with-roe-ai
summary: "Unstructured data is the last frontier—learn how Roe AI’s Native App in Snowflake helps you unlock insights quickly."
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# ROE AI: Unlocking Unstructured Data in Snowflake
<!-- ------------------------ -->
## Overview 
Duration: 3

Roe AI offers a seamless way to analyze and extract insights from unstructured data within Snowflake. By integrating Roe AI with Snowflake, you can quickly ingest, classify, and search your documents—unlocking valuable insights from PDFs, images, and other text-based files. This guide will walk you through setting up Roe AI and running your first unstructured data analysis pipeline in Snowflake.

### What You’ll Learn
- How to install and configure Roe AI in your Snowflake account.  
- How to ingest unstructured documents (PDFs, text files, images) and store them in Snowflake.  
- How Roe AI’s processing capabilities can help you extract and search document content quickly.

### What You’ll Build
- A simple text ingestion pipeline using Roe AI in Snowflake.  
- A quick demo query to show how Roe AI extracts text from uploaded data, storing it in a target table.

### Prerequisites
- [Snowflake](https://www.snowflake.com/) Account (configured in a supported region).  
- [Roe AI on Snowflake Marketplace](https://app.snowflake.com/marketplace/listing/GZTYZVLLLX3/roe-ai-advanced-document-ai-agents) (installation access).  
- Familiarity with basic Snowflake concepts (warehouses, databases, schemas). 
- Ability to run SQL queries in Snowflake.
- Some experience working with unstructured data is helpful but not required.

<!-- ------------------------ -->
## Step 1: Install Roe AI Native App
Duration: 2

Roe AI combines SQL and powerful AI agents, bringing unstructured data analysis directly into the workflows data teams already use. Our platform empowers analysts to process, query, and interpret unstructured data without leaving Snowflake.

If you haven’t already, deploy the Roe AI Native App into your Snowflake account. Refer to the **Snowflake Marketplace** listing for Roe AI and click **Get** Once you finish the marketplace flow, verify that Roe AI objects are now visible in your chosen database or schema.

During the **Launch App** stage, you are required to:
- Bind service endpoint, permission to create compute pool
- Allow external excess
- Provide required Azure OpenAI API Endpoint, Azure OpenAI API Version and Azure OpenAI API Key

Those are all required for Roe AI app to hook with LLM for analysis.

> aside positive
> 
> Roe AI integrates seamlessly with your chosen Snowflake environment, making it easy to install and update via the Marketplace.

<!-- ------------------------ -->
## Step 2: Create a Roe AI Agent
Duration: 4

Once your data is uploaded and ingested, you can create a specialized Roe AI Agent to leverage targeted AI capabilities on your unstructured data. This agent will help you process documents more effectively for tasks such as text extraction, entity recognition, and beyond.

In the **Manage Agent** section under **Create Agent** -> **Add Agent**, you can currently choose between two agent types:
- PDFExtractionEngine: Extracts structured insights from documents.
- PDFParserEngine: Converts documents into an LLM-ready format.

For this example, we'll use the PDFExtractionEngine.

### Metadata
- Agent Name: Provide the agent’s name.
- Agent Description: Optionally, include a description for the agent (this won’t affect the prompt).

### Arguments
Arguments represent the inputs for analysis. By default, there is a single argument named `pdf_file` of type `File`, indicating that a file must be provided for analysis.

You can also add additional arguments as needed.

### Prompt Configs
- (Optional) Instructions: Provide directions for how you want the LLM to analyze the files. For instance, specify the type of information to focus on and any sections you want to exclude.

- (Optional) Page Filtering: You can filter pages by using a free-form description, page range (with @PAGERANGE), or the table of contents (with @TOC). Indicate which specific pages or sections should be analyzed.

- (Required) PDF File: Use the syntax ${pdf_file} to connect the PDF file from your Arguments. This ensures the agent will analyze the file specified under `pdf_file`.

- (Optional) JSON Output: Typically needed to define the information you want retrieved from your PDF. For example, if you're uploading a restaurant receipt, you might configure:
  - File Type: object
  - Description (Optional)

  Then add multiple object fields, such as:
    - Field Name: restaurant_name
      - File Type: string
      - Description (Optional)

    - Field Name: bill_cost
      - File Type: number
      - Description (Optional)

Roe AI will interpret like below json format:
```
{
  "type": "object",
  "properties": {
    "restaurant": {
      "type": "string"
    },
    "price": {
      "type": "number"
    }
  }
}
```

The sample of output would be like
```
restaurant_name: Spoon
bill_cost: 27.38
```

<!-- ------------------------ -->
## Step 3: Upload the File to Stage
Duration: 3

### Prepare your data
To analyze files, you first upload them to a Snowflake stage, then use Roe AI’s procedures or functions to process and extract text content.

```sql
-- Create a stage for your documents
CREATE STAGE MY_TEST.PUBLIC.ROE_APP_FILES
    DIRECTORY = (ENABLE = TRUE);

-- Upload your file to your stage.
PUT file:///Users/<your-username>/Downloads/receipt.pdf @roe_app_files AUTO_COMPRESS = FALSE
```

### Connect to your Data
In the **Connect Data** section, you need to provide the stage name so Roe AI can connect with it.

**Stage Name**: @MY_TEST.PUBLIC.ROE_APP_FILES

You need to grant required permissions for Roe AI App.
```sql
GRANT USAGE ON DATABASE MY_TEST TO APPLICATION ROE_APP;
GRANT USAGE ON SCHEMA MY_TEST.PUBLIC TO APPLICATION ROE_APP;
GRANT READ ON STAGE MY_TEST.PUBLIC.ROE_APP_FILES TO APPLICATION ROE_APP;
```

> aside negative
> 
> Make sure your Snowflake Role has sufficient privileges to read/write stages and call Roe AI procedures.

<!-- ------------------------ -->
## Step 4: Run the Agent and Analyze Extracted Text
Duration: 4

After creating your agent, upload your files to snowflake stage and establish the connection. You can also query the extracted results:

```sql
-- Example: Run the Roe AI Agent
SELECT ROE_APP.CORE.RUN_AGENT('32d649c7-4245-45e6-a1bc-7d49f8d879c7', {
    'pdf_file': 'roe_app_files/' || relative_path
    }::MAP(VARCHAR, VARCHAR)) AS result
FROM DIRECTORY(@MY_TEST.PUBLIC.ROE_APP_FILES);
```

Roe AI will create or update relevant tables to store your processed text. You can run SQL queries on these tables for further analysis or to join them with structured data.

This step allows you to see how Roe AI can surface relevant details from large volumes of files—within minutes.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 5

In just a few steps, you’ve leveraged Roe AI inside Snowflake to install the app, upload files to a stage, create your own Roe AI Agent, and run it to analyze unstructured data. From here, you can explore more advanced use cases, such as building analytics dashboards or feeding the extracted text into machine learning models for deeper insights.

### What You Learned
- How to set up and configure Roe AI via the Snowflake Marketplace.  
- How to ingest and analyze unstructured documents stored in Snowflake stages.  
- How to create and run a Roe AI Agent.  
- How to quickly query extracted text alongside structured data.

### Related Resources
- [Medium Article: Unlock your unstructured data in minutes with Roe AI + Snowflake](https://medium.com/snowflake/unlock-your-unstructured-data-in-minutes-with-roe-ai-snowflake-970830ef6cff)  
- [Roe AI Documentation](https://roeai-docs.example.com)  
- [Snowflake Marketplace Listing for Roe AI](https://app.snowflake.com/marketplace/)
