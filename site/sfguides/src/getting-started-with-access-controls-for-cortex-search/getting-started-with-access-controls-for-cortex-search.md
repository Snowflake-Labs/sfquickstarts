author: Tim Buchhorn (sfc-gh-tbuchhorn)
id: getting-started-with-access-controls-for-cortex-search
language: en
summary: Build secure RAG chatbot applications with Cortex Search access controls for role-based document retrieval and compliance.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/compliance-security-discovery-governance, snowflake-site:taxonomy/snowflake-feature/cortex-search
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: AI, Conversational Assistants, Cortex Search

# Getting Started with Access Controls for RAGs (Cortex Search)
<!-- ------------------------ -->
## Overview 

Retrieval-Augmented Generation (RAG) promises to unlock unprecedented value from enterprise data. The vast majority (80-90%) of corporate knowledge is trapped in unstructured documents, emails, and messages, often containing sensitive PII, IP, and financial data with inconsistent access controls. Deploying AI models without robust governance exposes this sensitive data, creating severe risks of data breaches, regulatory non-compliance, and loss of intellectual property.

For businesses to adopt AI safely, applications must be "permissions-aware." This is not an optional feature but a foundational requirement. AI systems must respect and enforce the existing security and access permissions of every user at the moment of retrieval. An employee must only be allowed to "see" and surface data that the user querying it is already authorized to access.

In this guide, you will build a secure RAG pipeline (using Cortex Search) that enforces document-level access control. Specifically, we will create a RAG that utilises user attributes (such as their role) and pass this on as a filter condition to the cortex search service on the backend of a client-facing application.


### Prerequisites
- Access to an account that can create External Access Integrations (trial accounts are not able to).
- Access to an elevated role (such as ACCOUNTADMIN) to create External Access Integrations, Roles and Users.

### What You’ll Learn 
- How to build a RAG chatbot in Streamlit in Snowflake (SiS) with access controls.

### What You’ll Need 
- A Snowflake account with the ability to create Compute Pools (SPCS)
- Ability to create new users and roles in Snowflake

### What You’ll Build 
- A RAG chatbot built with Streamlit in Snowflake (SiS) with access controls, powered by Cortex Search.

<!-- ------------------------ -->
## Use Case 
Duration: 5

In this guide, we are going to play the role of a chain of sporting goods stores. We have product information on ski equipment, and bicycles. We want to help our customer service teams be able to query information on our products that currently exists in unstructured documents (PDFs).

Most importantly, we only want the Ski department to query information on source documents that are related to ski equipment. Similarly we want the Bicycle department to only query information from the PDF documents related to bicycles.

To do this, we are going to create a RAG pipeline utilizing Snowflake features (including [Cortex Search Service](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)), and utilize Streamlit in Snowflake (SiS) running on Snowpark Container Services (SPCS) to expose this functionality to users from both the Ski and Bicycle department.

<!-- ------------------------ -->
## Setup
Duration: 10

### Snowflake Setup

Open a SQL Worksheet and run through the following code to set up the necessary objects and permissions in Snowflake.

```SQL
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS RAG_OWNER;
CREATE ROLE IF NOT EXISTS SKI;
CREATE ROLE IF NOT EXISTS BICYCLE;

-- Create the users to test access controls. It is strongly recommended that MFA is enabled for these users
CREATE OR REPLACE USER bicycle_user
    PASSWORD             = '<enter initial password>'
    LOGIN_NAME           = 'bicycle_user'
    FIRST_NAME           = 'Bicycle'
    LAST_NAME            = 'User'
    EMAIL                = '<enter your email>'
    DEFAULT_ROLE         = BICYCLE  
    MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE BICYCLE TO USER bicycle_user;

CREATE OR REPLACE USER ski_user
    PASSWORD             = '<enter initial password>'
    LOGIN_NAME           = 'ski_user'
    FIRST_NAME           = 'Ski'
    LAST_NAME            = 'User'
    EMAIL                = '<enter your email>'
    DEFAULT_ROLE         = SKI 
    MUST_CHANGE_PASSWORD = TRUE;

GRANT ROLE SKI TO USER ski_user;

GRANT CREATE DATABASE ON ACCOUNT TO ROLE RAG_OWNER;
GRANT CREATE COMPUTE POOL ON ACCOUNT TO ROLE RAG_OWNER;
GRANT CREATE WAREHOUSE ON ACCOUNT TO ROLE RAG_OWNER;

SET USERNAME = (SELECT CURRENT_USER());
SELECT $USERNAME;
GRANT ROLE RAG_OWNER to USER identifier($USERNAME);

-- Create compute

USE ROLE RAG_OWNER;

CREATE COMPUTE POOL IF NOT EXISTS RAG_STREAMLIT
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_XS;

CREATE WAREHOUSE IF NOT EXISTS RAG_WH
  WAREHOUSE_TYPE = STANDARD
  WAREHOUSE_SIZE = XSMALL;

--- Create database and schema

CREATE DATABASE IF NOT EXISTS RAG_DB;
USE DATABASE RAG_DB;
CREATE SCHEMA IF NOT EXISTS RAG_DB.RAG_SCHEMA;
USE SCHEMA RAG_SCHEMA;

--- Create network rule and apply it in External Access Integration

CREATE OR REPLACE NETWORK RULE pypi_network_rule
 MODE = EGRESS
 TYPE = HOST_PORT
 VALUE_LIST = ('pypi.org', 'pypi.python.org', 'pythonhosted.org',  'files.pythonhosted.org');

USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION pypi_access_integration
 ALLOWED_NETWORK_RULES = (pypi_network_rule)
 ENABLED = true;

-- Grant necessary privileges

GRANT USAGE ON INTEGRATION pypi_access_integration TO ROLE RAG_OWNER;

GRANT CREATE STREAMLIT ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE RAG_OWNER;

GRANT USAGE ON WAREHOUSE RAG_WH TO ROLE BICYCLE;
GRANT USAGE ON WAREHOUSE RAG_WH TO ROLE SKI;

GRANT USAGE ON COMPUTE POOL RAG_STREAMLIT TO ROLE BICYCLE;
GRANT USAGE ON COMPUTE POOL RAG_STREAMLIT TO ROLE SKI;

GRANT USAGE ON DATABASE RAG_DB TO ROLE BICYCLE;
GRANT USAGE ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE BICYCLE;

GRANT USAGE ON DATABASE RAG_DB TO ROLE SKI;
GRANT USAGE ON SCHEMA RAG_DB.RAG_SCHEMA TO ROLE SKI;

-- Create stages for streamlit source code and source documentation

USE ROLE RAG_OWNER;

CREATE OR REPLACE STAGE STREAMLIT_UI DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');
CREATE OR REPLACE STAGE SOURCE_DOCUMENTS DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE='SNOWFLAKE_SSE');
```

### Upload Documents
Duration: 5

Upload the documents in the unzipped Documents.zip folder [here](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-access-controls-for-cortex-search/assets/Documents.zip) to the SOURCE_DOCUMENTS stage we just created. You can do this through the Snowsight UI. The instructions on how to do this can be found in our documentation [here](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-stage-ui#upload-files-onto-a-named-internal-stage) 

Be sure to select the RAG_DB database, the RAG_SCHEMA schema and the SOURCE_DOCUMENTS stage. These source documents are the PDFs on both the Bicycle and Ski equipment products in one directory. See the screenshot below

![Upload Files](assets/load_file_menu.png)

Once you have uploaded them, run the following SQL from your SQL Worksheet to check if the files have been uploaded successfully.

```SQL
LS @SOURCE_DOCUMENTS;
```

You should see the 4 files loaded in the stage.

## Prepare Data for RAG
Duration: 20

In this section, we use Snowflake's helper functions to prepare the unstructured documents and set up the Cortex Search Service. 

The functions below simplify the process of creating a RAG into only a few steps. Specifically, we are using the following unique Snowflake features:
- Cortex AI Functions (AI_PARSE_DOCUMENT):
- SPLIT_TEXT_RECURSIVE_CHARACTER:

Note that we are adding an attribute column that we will filter on later to make sure that users only see the correct documents. We are using the file names, but you could also use [AI_CLASSIFY](https://docs.snowflake.com/en/sql-reference/functions/ai_classify) as part of your pipeline.

Run the following SQL in a SQL worksheet

```SQL
USE SCHEMA RAG_DB.RAG_SCHEMA;

CREATE OR REPLACE TABLE documents_table AS
  (SELECT TO_FILE('@source_documents', RELATIVE_PATH) AS docs, 
    RELATIVE_PATH as RELATIVE_PATH
    FROM DIRECTORY(@source_documents));

-- Use Cortex AI function to parse PDF. Create identifier column so we can filter based on user attribute
CREATE OR REPLACE TABLE EXTRACTED_TEXT_TABLE AS (
    SELECT  RELATIVE_PATH, 
            AI_PARSE_DOCUMENT(docs, {'mode': 'OCR'}):content::VARCHAR AS EXTRACTED_TEXT,
            CASE
                WHEN RELATIVE_PATH ILIKE '%ski%' THEN 'SKI'
                WHEN RELATIVE_PATH ILIKE '%bike%' OR RELATIVE_PATH ILIKE '%bicycle%' THEN 'BICYCLE'
                ELSE 'Other'
            END AS product_department
            FROM documents_table
            );

-- Chunk parsed document for RAG
CREATE OR REPLACE TABLE CHUNKED_TABLE AS (
        SELECT
            e.*,
            c.value::VARCHAR AS chunk
        FROM EXTRACTED_TEXT_TABLE e,
        LATERAL FLATTEN(
            INPUT => snowflake.cortex.split_text_recursive_character(
                EXTRACTED_TEXT,
                'none',
                2000,
                300
            )
        ) c
    );

-- Test chunked table
SELECT * FROM CHUNKED_TABLE;

-- Create Cortex Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE rag_cortex_search_service
  ON chunk
  ATTRIBUTES product_department
  WAREHOUSE = RAG_WH
  TARGET_LAG = '1 hour'
  INITIALIZE = ON_CREATE
AS SELECT * FROM RAG_DB.RAG_SCHEMA.CHUNKED_TABLE;
```

The Cortex Search Service may take a few minutes to set up. Once it has completed,  we can test the cortex search service by running the following SQL. Check if the serving_state column is ACTIVE.

```SQL
DESC CORTEX SEARCH SERVICE rag_cortex_search_service;
```

Next, we will alter it to return a "scoring profile" which allows us to provide thresholds for the relevancy of returned documents

```SQL
ALTER CORTEX SEARCH SERVICE RAG_DB.RAG_SCHEMA.rag_cortex_search_service
  ADD SCORING PROFILE IF NOT EXISTS default_with_components
  '{
    "component_scores": true
  }';
```

We can execute the following SQL to test if the Cortex Search Service is working.

```SQL
SELECT PARSE_JSON(
  SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
      'rag_cortex_search_service',
      '{
         "query": "Tell me about the Ski Bootz",
         "filter": {"@eq": {"product_department": "SKI"} },
         "limit":10
      }'
  )
)['results'] as results;
```

## Prepare Streamlit App
Duration: 10

The next step is to create a UI that can use these objects and present them to our business users in a safe and secure way. We are going to use Streamlit in Snowflake on a Container Runtime to make this simple. Since this is an internal application, we can leverage Snowflake's authentication and authorization mechanisms to ensure the app is "aware" of who is trying to access the data, and only return information from the documents they have access to.

Upload the streamlit python file and corresponding assets by downloading and unzipping the [streamlit_assets.zip](https://github.com/Snowflake-Labs/sfquickstarts/blob/master/site/sfguides/src/getting-started-with-access-controls-for-cortex-search/assets/streamlit_assets.zip) and uploading to the STREAMLIT_UI stage. Follow similar steps to how you uploaded the source documents. The instructions on how to do this can be found in our documentation [here](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-stage-ui#upload-files-onto-a-named-internal-stage). Be sure to select the RAG_DB database, the RAG_SCHEMA schema and the STREAMLIT_UI stage. See the screenshot below:

![Upload Streamlit Files](assets/upload_streamlit_files.png)

Next, run the following SQL to create the Streamlit app.

```SQL
CREATE OR REPLACE STREAMLIT rag_access_control_app
  FROM '@rag_db.rag_schema.streamlit_ui/'
  MAIN_FILE = 'rag_access_control_streamlit_ui.py'
  RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
  COMPUTE_POOL = RAG_STREAMLIT
  QUERY_WAREHOUSE = RAG_WH
  EXTERNAL_ACCESS_INTEGRATIONS = (pypi_access_integration);

ALTER STREAMLIT rag_access_control_app ADD LIVE VERSION FROM LAST;
```

## Open App as Owner
Duration: 5

Navigate to Projects > Streamlit in the left navigation menu. You should now see RAG_ACCESS_CONTROL_APP. Click to open the app. Make sure you have assumed the role RAG_OWNER (you can check this by clicking over your initials in the bottom left of the screen).

You should now see the streamlit UI. See screenshot below:

![Streamlit Home Page](assets/streamlit_home_page.png)

If you type a question, it will not respond with a helpful answer since the filters applied do not allow the owner role to see the underlying data via the app. Since the owner role owns the Cortex Search Service, it could however query the service directly outside of the app. If this were to be implemented, this role would not be granted to users that needed access controls applied to them.

![No Documents](assets/no_documents.png)

## Share Streamlit App
Duration: 5

We now want to test this functionality as different users with different permissions. First we need to grant access to other roles to this app. In the top right of the page, click the "Share" button. In the modal, grant access to "SKI" and "BICYCLE" roles as "View Only".

![Grant Streamlit Access](assets/grant_streamlit_access.png)

Select the 'Copy Link' button. Then Sign Out as the current user. You can find this button in the bottom left of the screen.

Next sign out as the current user. You can find this by clicking your initials icon in the bottom left of the UI.

## Test App as Different Users
Duration: 15

Paste the copied link from the previous section into the browser. It should then prompt you to login. We are going to test the app experience as the 'Ski' user. Type in ski_user in the Username field, and the initial password you created as part of the initial set up. N.B. if you have a MFA enforcement policy set up (highly recommended), you will be prompted to complete those steps upon initial sign-in.

You should see the streamlit app load in the UI.

First, lets see if we can see any information on bicycles. We should not, since the filter on the backend should only return chunks from documents related to skis.

Ask "Tell me about the Mondracer bike"

You should see that the app responded that it did not have any relevant information. Similarly the "Context Documents" in the left navigation menu (with Debug Mode on) should be empty.

![No Documents with Debug](assets/no_documents_2.png)

Now lets ask a question which should return results.

Ask "Tell me about the TD Ski Bootz"

You should see a response and also relevant chunks being returned to answer the question.

![Ski Response](assets/ski_response.png)

You can now test this for "bicycle_user" by logging out and logging back in as bicycle_user.

When logged in as bicycle_user, ask:

"Tell me about the Mondracer bike"

You should see a response. 

![Bicycle Response](assets/bicycle_response.png)

Next ask:

"Tell me about the TD Ski Bootz".

You should not see a response that references source documents.

![Bicycle No Response](assets/bicycle_no_response.png)

<!-- ------------------------ -->
## Understanding the Streamlit Code
Duration: 10

The Streamlit code contains the logic that allows us to safely use the Cortex Search Service and return only the relevant information to the authenticated user.

Cortex Search Services runs with Owner's Rights by design. This is to ensure that it runs with the same security model as other Snowflake objects that run with Owner's Rights and keeps the service performant for real world use cases. More information on this model can be found in our documentation [here](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/query-cortex-search-service#querying-with-owner-s-rights).

In this app, we are following recommended best practice of using explicit filters on the client-side query to filter for access controls. These filters are based on user attributes that are obtained from the authentication flow from logging in to Snowflake.

Only the RAG_OWNER Role, which owns both the streamlit app and the Cortex Search Service, has the ability to use the Cortex Search Service, and modify any of the code within the streamlit app. Both the SKI and BICYCLE roles only have access to viewing and using the Streamlit app.

Here is a walkthrough of some of the key functionality in the streamlit python code:

The following block reads the credentials of the owner of the container the app is running on. This is true whether this is Streamlit in Snowflake (SiS) running on containers, or if you were to push your own app to SPCS. Snowflake will provide this OAuth token at the location (/snowflake/session/token). More information can be found in our documentation [here](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/additional-considerations-services-jobs#connecting-with-a-snowflake-provided-oauth-token).

```python
def get_system_token():
    """
    Reads the container's system token.
    """
    try:
        with open("/snowflake/session/token", "r") as f:
            return f.read().strip()
    except Exception:
        return None
```

The code below creates two sessions. One is the owner session to utilise Cortex Search (which is not exposed to the user). The other creates the visitor session to obtain the attributes of the user logging in.

We do this by obtaining the ingress_user_token from the HTTP headers.

```python
headers = st.context.headers or {}
ingress_user_token = headers.get("Sf-Context-Current-User-Token")
ingress_user = headers.get("Sf-Context-Current-User")
```

Once we have obtained the header information, we can initialize both the sessions in the initialize_sessions function.

The next key part of the functionality is how we apply the filters to the Cortex Search service. As previously mentioned, the Cortex Search Service runs with Owner's Rights, so we need to utilise the Owner's session in backend code (so it is not exposed to the visiting user). Similarly, we need to provide a filter on the Cortex Search service that cannot be tampered with. We use the Snowflake generated headers and calling the Context Function CURRENT_ROLE() to do this. 

```python
current_role = get_current_role_from_session(current_session)

filter_condition = {"@eq": {"product_department": current_role}}
context_documents = cortex_search_service.search(
    query,
    columns=["CHUNK"],
    filter=filter_condition,
    scoring_profile=scoring_profile,
)
filter_applied = f"product_department @eq '{current_role}' (server-validated)"
```

This way we are able to expose the RAG functionality to the authenticated user, without providing access to all indexed source documents.

This same design could be utilized for application architectures other than streamlit. You would similarly pass an identifier along with the [Cortex Search API request](https://docs.snowflake.com/developer-guide/snowflake-rest-api/reference/cortex-search-service#post--api-v2-databases-database-schemas-schema-cortex-search-services-service_name-query) from the backend.


<!-- ------------------------ -->
## Clean Up
Duration: 5

Log in as the RLS Owner user, and run the following SQL to clean up.

```SQL
USE ROLE ACCOUNTADMIN;
DROP ROLE RAG_OWNER;
DROP ROLE SKI;
DROP ROLE BICYCLE;

DROP USER bicycle_user;
DROP USER ski_user;

ALTER COMPUTE POOL RAG_STREAMLIT STOP ALL;
DROP COMPUTE POOL RAG_STREAMLIT;
DROP WAREHOUSE RAG_WH;
DROP DATABASE RAG_DB CASCADE;
DROP EXTERNAL ACCESS INTEGRATION pypi_access_integration;
```

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 5

Congratulations! You have successfully built and deployed a secure, permissions-aware Retrieval-Augmented Generation (RAG) application entirely within Snowflake.

By combining **Cortex Search** with **Streamlit in Snowflake (on Container Runtime)**, you demonstrated how to move beyond generic chatbots to enterprise-ready solutions that respect existing data governance policies. You utilized Snowflake's native access control (RBAC) to dynamically filter search results, ensuring that users (like our Ski and Bicycle representatives) only interact with data they are authorized to see.

### What You Learned
- **Data Preparation for RAG:** How to use `AI_PARSE_DOCUMENT` to extract text from unstructured files (PDFs) and `SPLIT_TEXT_RECURSIVE_CHARACTER` to chunk data for indexing.
- **Cortex Search Configuration:** How to configure a Cortex Search Service with specific `ATTRIBUTES` to enable metadata filtering.
- **Streamlit on SPCS:** How to deploy a Streamlit app using the Container Runtime to leverage specific python versions and libraries.
- **Secure Filtering Pattern:** How to implement a pattern that captures the authenticated user's role and applies a server-validated filter to the Cortex Search query, effectively implementing Row-Level Security for your RAG pipeline.

### Related Resources
- [Documentation: Cortex Search Service](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)
- [Documentation: Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)
- [Documentation: Snowpark Container Services](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Documentation: Openflow Connectors with Access Controls](https://docs.snowflake.com/en/user-guide/data-integration/openflow/connectors/sharepoint/setup#query-the-cortex-search-service)
- [Guide Source Code on GitHub](https://github.com/Snowflake-Labs/sfguides)
