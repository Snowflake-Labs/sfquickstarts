author: Julia Beck and Neeraj Jain
id: create-a-document-processing-pipeline-with-ai-extract
language: en
summary: Learn how to create an automated document processing pipeline using AI_EXTRACT to extract structured data from documents.
categories: snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/unstructured-data-analysis, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
open in snowflake: https://docs.snowflake.com/en/sql-reference/functions/ai_extract

# Create a Document Processing Pipeline with AI_EXTRACT
<!-- ------------------------ -->
## Overview

With AI_EXTRACT, you can process text or document files of various formats, and extract information from text-heavy paragraphs, images that contain text like handwritten text or logos, and embedded structures like lists and tables, all through a single programmatic call. This tutorial introduces you to AI_EXTRACT by setting up the required objects and privileges, and creating an AI_EXTRACT function to use in a processing pipeline.

### Prerequisites
- You must connect as a user that has the ACCOUNTADMIN role which is used to create a custom role used in this tutorial and grant the new role required privileges.
- You must ensure that AI_EXTRACT is either available as an [in-region offering](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql#label-cortex-llm-availability), or enable [cross-region inference](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference#label-use-cross-region-inference).
- You must have a warehouse ready to use with AI_EXTRACT. As scaling up the warehouse does not increase the speed of query processing, but might result in unnecessary costs, an XS warehouse is recommended.

### What You'll Learn
- How to set up the objects and privileges required to work with AI_EXTRACT
- How to configure the AI_EXTRACT SQL function to extract structured data from documents
- How to create a pipeline for continuous processing of new documents from a Stage, using the AI_EXTRACT function with streams and tasks

### What You'll Need
- Snowflake account with ACCOUNTADMIN role access
- A warehouse (XS recommended)
- [Sample document files](https://docs.snowflake.com/en/_downloads/79147fc17de2a37ecd330f0e45f29bf3/extraction_dataset.zip)

### What You'll Build
- An automated document processing pipeline that extracts structured data from PDFs using AI_EXTRACT, streams, and tasks

<!-- ------------------------ -->
## Set Up Required Objects and Privileges

In this section, you will create the necessary database, schema, and custom role, and grant the required privileges for working with AI_EXTRACT.

### Create Database and Schema

Create a database and schema to contain the AI_EXTRACT pipeline objects.

```sql
CREATE DATABASE doc_ai_db;
CREATE SCHEMA doc_ai_db.doc_ai_schema;
```

### Create Custom Role

Create a custom role `doc_ai_role` to prepare the AI_EXTRACT document processing pipeline.

```sql
USE ROLE ACCOUNTADMIN;
CREATE ROLE doc_ai_role;
```

### Grant Required Privileges

Grant the privileges required to work with AI_EXTRACT:

```sql
-- 1. Grant the SNOWFLAKE.CORTEX_USER database role to the doc_ai_role role:
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE doc_ai_role;

-- 2. Grant warehouse usage and operating privileges to the doc_ai_role role:
GRANT USAGE, OPERATE ON WAREHOUSE <your_warehouse> TO ROLE doc_ai_role;

-- 3. Grant the privileges to use the database and schema you created to the doc_ai_role:
GRANT USAGE ON DATABASE doc_ai_db TO ROLE doc_ai_role;
GRANT USAGE ON SCHEMA doc_ai_db.doc_ai_schema TO ROLE doc_ai_role;

-- 4. Grant the create stage privilege on the schema to the doc_ai_role role to store the documents for extraction:
GRANT CREATE STAGE ON SCHEMA doc_ai_db.doc_ai_schema TO ROLE doc_ai_role;

-- 5. Grant the privileges required to create a processing pipeline using streams and tasks to the doc_ai_role role:
GRANT CREATE STREAM, CREATE TABLE, CREATE TASK, CREATE FUNCTION, CREATE VIEW ON SCHEMA doc_ai_db.doc_ai_schema TO ROLE doc_ai_role;
GRANT EXECUTE TASK ON ACCOUNT TO ROLE doc_ai_role;

-- 6. Grant the doc_ai_role to tutorial user for use in the next steps of the tutorial:
GRANT ROLE doc_ai_role TO USER <your_user_name>;
```

### Enable Cross-Region Inference (If Needed)

If AI_EXTRACT is not [available in-region](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql#label-cortex-llm-availability), run the following command to allow cross-region inference:

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

### Assume the New Role

To assume the newly created role:

```sql
USE ROLE doc_ai_role;
```

<!-- ------------------------ -->
## Set Up Prompt Table

In this section, you will create a prompt table that defines the values to be extracted from your documents using natural language.

### Create the Prompt Table

The prompt table will be structured such that each row corresponds to a template of a document type to be processed. In this tutorial, only one template will be used. You can store multiple templates in this table, along with multiple versions of a given template.

```sql
CREATE TABLE IF NOT EXISTS prompt_templates (
    template_id VARCHAR PRIMARY KEY,
    response_format VARIANT
);
```

### Define Extraction Schema

Insert the defined data values for the inspection review document type:

```sql
INSERT INTO prompt_templates
SELECT
    'INSPECTION_REVIEWS',
    PARSE_JSON('{
        "schema": {
            "type": "object",
            "properties": {
                "list_of_units": {
                    "description": "Extract the table showing all units and their reported conditions",
                    "type": "object",
                    "column_ordering": ["unit_name", "condition"],
                    "properties": {
                        "unit_name": {
                            "description": "Name of the unit",
                            "type": "array"
                        },
                        "condition": {
                            "description": "Condition reported for the unit",
                            "type": "array"
                        }
                    }
                },
                "inspection_date": {
                    "description": "What is the inspection date?",
                    "type": "string"
                },
                "inspection_grade": {
                    "description": "What is the grade?",
                    "type": "string"
                },
                "inspector": {
                    "description": "Who performed the inspection?",
                    "type": "string"
                }
            }
        }
    }');
```

<!-- ------------------------ -->
## Create AI_EXTRACT Wrapper Function

In this section, you will create an internal stage for document storage and package AI_EXTRACT in a wrapper function for easy reuse.

### Create Internal Stage

Create the stage with directory enabled for metadata tracking:

```sql
CREATE STAGE IF NOT EXISTS my_pdf_stage
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');
```

### Create the Wrapper Function

This function will accept a file path in the stage as input and return the extracted data from the document:

```sql
CREATE OR REPLACE FUNCTION extract_document_data(
    stage_name STRING,
    file_path STRING
)
RETURNS VARIANT
LANGUAGE SQL
AS $$
    SELECT AI_EXTRACT(
        file => TO_FILE(stage_name, file_path),
        responseFormat => (
            SELECT response_format 
            FROM prompt_templates 
        )
    ):response
$$;
```

<!-- ------------------------ -->
## Test AI_EXTRACT

In this section, you will test the AI_EXTRACT function on sample documents.

### Upload Sample Documents

1. Download the [zip file](https://docs.snowflake.com/en/_downloads/79147fc17de2a37ecd330f0e45f29bf3/extraction_dataset.zip) to your local file system.
2. Unzip the content, which includes PDF files.
3. Sign in to [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html#label-snowsight-getting-started-sign-in).
4. In the navigation menu, select **Catalog** » **Database Explorer**.
5. Select the `doc_ai_db` database, the `doc_ai_schema`, and the `my_pdf_stage` stage.
6. Select **+ Files**.
7. In the **Upload Your Files** dialog that appears, select `Manual_2022-02-01.pdf` from the files you just downloaded. Feel free to add additional files to parse directly.
8. Select Upload.

### View Extracted Data

View data extracted from the test file(s) by running the below command over the stage:

```sql
SELECT
    RELATIVE_PATH,
    extract_document_data('@my_pdf_stage', RELATIVE_PATH) as EXTRACTED_DATA
FROM DIRECTORY('@my_pdf_stage');
```

<!-- ------------------------ -->
## Create Automated Processing Pipeline

In this section, you will create an automated processing pipeline using streams and tasks that will continuously process new documents uploaded to the stage.

### Create Stream on Stage

Create a `my_pdf_stream` stream on the `my_pdf_stage`:

```sql
CREATE STREAM my_pdf_stream ON STAGE my_pdf_stage;
ALTER STAGE my_pdf_stage REFRESH;
```

### Create Results Table

Create a `pdf_reviews` table to store the information about the documents and the extracted data:

```sql
CREATE OR REPLACE TABLE pdf_reviews (
  file_name VARCHAR,
  file_size VARIANT,
  last_modified VARCHAR,
  snowflake_file_url VARCHAR,
  json_content VARIANT
);
```

The `json_content` column will include the extracted information in JSON format.

### Create Processing Task

Create a `load_new_file_data` task to process new documents in the stage:

```sql
CREATE OR REPLACE TASK load_new_file_data
  WAREHOUSE = <your_warehouse>
  SCHEDULE = '1 minutes'
  COMMENT = 'Process new files in the stage and insert data into the pdf_reviews table.'
WHEN SYSTEM$STREAM_HAS_DATA('my_pdf_stream')
AS
INSERT INTO pdf_reviews (
  SELECT
    RELATIVE_PATH AS file_name,
    size AS file_size,
    last_modified,
    file_url AS snowflake_file_url,
    extract_document_data('@my_pdf_stage',RELATIVE_PATH) AS json_content
  FROM my_pdf_stream
  WHERE METADATA$ACTION = 'INSERT'
);
```

### Resume the Task

Newly created tasks are automatically suspended. Start the newly created task:

```sql
ALTER TASK load_new_file_data RESUME;
```

<!-- ------------------------ -->
## Process New Documents

In this section, you will upload new documents and view the automatically extracted results.

### Upload Documents to Stage

1. Sign in to [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html#label-snowsight-getting-started-sign-in).
2. In the navigation menu, select **Catalog** » **Database Explorer**.
3. Select the `doc_ai_db` database, the `doc_ai_schema`, and the `my_pdf_stage` stage.
4. Select **+ Files**.
5. In the **Upload Your Files** dialog that appears, select the files you downloaded in the previous section.

> Note that this will not process the existing files in the stage. To include these files, delete the existing files from the stage prior to uploading the folder contents. You can quickly remove all existing files from the stage using:
> ```sql
> REMOVE @my_pdf_stage;
> ```

6. Select Upload.

### View Extracted Information

After uploading the documents to the stage, view the information extracted from new documents:

```sql
SELECT * FROM pdf_reviews;
```

> Note that as the task runs every minute, the table may take approximately 1-2 minutes to be populated.

### Create Analysis View

Create `pdf_reviews_view` to analyze the extracted information in separate columns:

```sql
CREATE VIEW pdf_reviews_view AS
SELECT 
    file_name,
    file_size,
    last_modified,
    snowflake_file_url,
    json_content:inspection_date::STRING AS inspection_date,
    json_content:inspection_grade::STRING AS inspection_grade,
    json_content:inspector::STRING AS inspector,
    json_content:list_of_units:unit_name::ARRAY AS list_of_units_name,
    json_content:list_of_units:condition::ARRAY AS list_of_units_condition,
FROM pdf_reviews;
```

View the output:

```sql
SELECT * FROM pdf_reviews_view;
```

<!-- ------------------------ -->
## Conclusion

Congratulations! You have successfully completed this tutorial. You are now ready to start working with Document AI on your own use cases.

### What You Learned
- How to set up the required objects and privileges to work with AI_EXTRACT
- How to create a prompt table defining the data values to be extracted using natural language
- How to create an AI_EXTRACT wrapper function
- How to test AI_EXTRACT on a sample document by calling the function directly
- How to automate a document processing pipeline by creating a stream and a task and using the AI_EXTRACT function to extract information from new documents

### Related Resources
- [Working with AI_EXTRACT](https://docs.snowflake.com/en/sql-reference/functions/ai_extract)
- [Calling AI_EXTRACT using Python](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.functions.ai_extract)
- [Introduction to Streams](https://docs.snowflake.com/en/user-guide/streams-intro)
- [Introduction to Tasks](https://docs.snowflake.com/en/user-guide/tasks-intro)
- [Stream and Task Commands](https://docs.snowflake.com/en/sql-reference/commands-stream)
