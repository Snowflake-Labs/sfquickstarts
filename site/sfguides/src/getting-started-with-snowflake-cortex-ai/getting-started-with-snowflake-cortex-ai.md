id: getting-started-with-snowflake-cortex-ai
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-llm-functions
language: en
summary: This guide provides the instructions for getting started with Snowflake Cortex AI. 
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
authors: Dash Desai


# Getting Started With Snowflake Cortex AI
<!-- ------------------------ -->
## Overview


Getting started with AI on enterprise data can seem overwhelming, between getting familiar with LLMs, how to perform custom prompt engineering, and how to get a wide range of LLMs deployed/integrated to run multiple tests all while keeping that valuable enterprise data secure. Well, a lot of these complexities are being abstracted away for you in Snowflake Cortex AI. 

In this guide, we will go through various flows and show you the fastest and easiest way to get started with Snowflake Cortex AI.

### What is Snowflake Cortex AI?
Snowflake offers two broad categories of powerful, intelligent features based on Artificial Intelligence (AI) and Machine Learning (ML). These features can help you do more with your data in less time than ever before.

Snowflake Cortex is a suite of AI features that use large language models (LLMs) to understand unstructured data, answer freeform questions, and provide intelligent assistance.

Learn more about [Snowflake Cortex AI](/en/product/features/cortex/).

### What You Will Learn
- How to use Snowflake Cortex AI for custom tasks like summarizing long-form text into JSON formatted output using prompt engineering and task-specific LLM functions to perform operations like translate, sentiment scoring, etc
- How to fine-tune an LLM in Snowflake
- How to build a Streamlit application and a Snowflake Notebook that uses Snowflake Cortex AI capabilities in Snowflake

### What You Will Build
- An interactive Streamlit application and a Snowflake Notebook that uses Snowflake Cortex AI capabilities -- both running securely in Snowflake.

### Prerequisites

- A [Snowflake](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) account in a region where your choice of LLMs are [available](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability).

<!-- ------------------------ -->
## Setup


Prior to GenAI, a lot of the information was buried in text format and therefore going underutilized for root cause analysis due to complexities in implementing natural language processing. But with Snowflake Cortex AI it’s as easy as writing a SQL statement! 

In this guide, we'll utilize synthetic call transcripts data, mimicking text sources commonly overlooked by organizations, including customer calls/chats, surveys, interviews, and other text data generated in marketing and sales teams.

### Create Table and Load Data

In a new SQL worksheet, run the following statements to set up your environment. This will:

- Create a database, schema, and warehouse
- Create a table
- Load sample data from an Amazon S3 bucket

```sql
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS DASH_DB;
CREATE SCHEMA IF NOT EXISTS DASH_SCHEMA;
CREATE WAREHOUSE IF NOT EXISTS DASH_XS_WH WAREHOUSE_SIZE=XSMALL;

USE DASH_DB.DASH_SCHEMA;
USE WAREHOUSE DASH_XS_WH;

CREATE or REPLACE file format csvformat
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  type = 'CSV';

CREATE or REPLACE stage call_transcripts_data_stage
  file_format = csvformat
  url = 's3://sfquickstarts/misc/call_transcripts/';

CREATE or REPLACE table CALL_TRANSCRIPTS ( 
  date_created date,
  language varchar(60),
  country varchar(60),
  product varchar(60),
  category varchar(60),
  damage_type varchar(90),
  transcript varchar
) COMMENT = '{"origin":"sf_sit-is", "name":"aiml_notebooks_cortex_ai", "version":{"major":1, "minor":0}, "attributes":{"is_quickstart":1, "source":"sql"}}';

COPY into CALL_TRANSCRIPTS
  from @call_transcripts_data_stage;
```

> 
> IMPORTANT: If you use different names for objects created in this section, be sure to update scripts and code in the following sections accordingly.

<!-- ------------------------ -->
## Task Specific LLM Functions


Given the data in `CALL_TRANSCRIPTS` table, let’s see how we can use task specific LLMs functions in Snowflake Cortex. It offers access to industry-leading AI models, without requiring any knowledge of how the AI models work, how to deploy LLMs, or how to manage GPU infrastructure.

Run the following statements in the same or a new SQL worksheet.

### Translate
Using Snowflake Cortex function **snowflake.cortex.translate** we can easily translate any text from one language to another. Let’s see how easy it is to use this function.

```sql
select snowflake.cortex.translate('wie geht es dir heute?','de_DE','en_XX');
```

Executing the above SQL should generate ***"How are you today?"***

#### Batch mode

Now let’s see how you can translate call transcripts from German to English in batch mode using just SQL.

```sql
select transcript,snowflake.cortex.translate(transcript,'de_DE','en_XX') from call_transcripts where language = 'German';
```

See the list of [supported languages](https://docs.snowflake.com/en/sql-reference/functions/translate-snowflake-cortex#usage-notes).

### Sentiment Score
Now let’s see how we can use **snowflake.cortex.sentiment** function to generate sentiment scores on call transcripts. 

*Note: Score is between -1 and 1; -1 = most negative, 1 = positive, 0 = neutral*

```sql
select transcript, snowflake.cortex.sentiment(transcript) from call_transcripts where language = 'English';
```

### Summarize
Now that we know how to translate call transcripts in English, it would be great to have the model pull out the most important details from each transcript so we don’t have to read the whole thing. Let’s see how **snowflake.cortex.summarize** function can do this and try it on one record.

```sql
select transcript,snowflake.cortex.summarize(transcript) as summary from call_transcripts where language = 'English' limit 1;
```

#### Summary with tokens count

```sql
select transcript,snowflake.cortex.summarize(transcript) as summary,snowflake.cortex.count_tokens('summarize',transcript) as number_of_tokens from call_transcripts where language = 'English' limit 1;
```

> 
> NOTE: Snowflake Cortex LLM functions incur compute cost based on the number of tokens processed. Refer to the [documentation](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions#cost-considerations) for more details on each function’s cost in credits per million tokens.

<!-- ------------------------ -->
## Prompt Engineering


Being able to pull out the summary is good, but it would be great if we specifically pull out the product name, what part of the product was defective, and limit the summary to 200 words. 

Let’s see how we can accomplish this using the **snowflake.cortex.complete** function.

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

SET prompt = 
'### 
Summarize this transcript in less than 200 words. 
Put the product name, defect and summary in JSON format. 
###';

select snowflake.cortex.complete('claude-4-sonnet',concat('[INST]',$prompt,transcript,'[/INST]')) as summary
from call_transcripts where language = 'English' limit 1;
```

Here we’re selecting the Claude 4 model and giving it a prompt telling it how to customize the output. Sample response:

```json
{
    "product": "XtremeX helmets",
    "defect": "Broken buckles that won't secure the helmet properly",
    "summary": "Jessica Turner from Mountain Ski Adventures contacted customer service regarding a recent order (order #68910) of XtremeX helmets. Upon inspection, they discovered that 10 helmets had broken buckles that wouldn't secure properly. The customer service agent apologized for the inconvenience and offered either a refund or replacement. Jessica requested replacements since they still needed the helmets for their customers. The agent processed a replacement order for 10 new XtremeX helmets with functioning buckles, which will be expedited and should arrive within 3-5 business days. The issue was resolved satisfactorily with the customer expressing appreciation for the assistance."
}
```

<!-- ------------------------ -->
## Streamlit Application


To put it all together, let's create a Streamlit application in Snowflake.

### Setup

**Step 1.** Click on **Streamlit** on the left navigation menu

**Step 2.** Click on **+ Streamlit App** on the top right

**Step 3.** Enter **App name**

**Step 4.** Select **App location** (DASH_DB and DASH_SCHEMA) and **App warehouse** (DASH_XS_WH) 

**Step 5.** Select **Run on warehouse** for **Runtime**.

**Step 6.** Click on **Create**

- At this point, you will be provided code for an example Streamlit application

**Step 7.** Replace the entire sample application code on the left with the following code snippet.

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(layout='wide')
session = get_active_session()

def summarize():
    with st.container():
        st.header("JSON Summary With Snowflake Cortex AI")
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=400,placeholder='Enter text. For example, a call transcript.')
        btn_summarize = st.button("Summarize",type="primary")
        if entered_text and btn_summarize:
            entered_text = entered_text.replace("'", "\\'")
            prompt = f"Summarize this transcript in less than 200 words. Put the product name, defect if any, and summary in JSON format: {entered_text}"
            cortex_prompt = "'[INST] " + prompt + " [/INST]'"
            cortex_response = session.sql(f"select snowflake.cortex.complete('claude-4-sonnet', {cortex_prompt}) as response").to_pandas().iloc[0]['RESPONSE']
            st.write(cortex_response)

def translate():
    supported_languages = {'German':'de','French':'fr','Korean':'ko','Portuguese':'pt','English':'en','Italian':'it','Russian':'ru','Swedish':'sv','Spanish':'es','Japanese':'ja','Polish':'pl'}
    with st.container():
        st.header("Translate With Snowflake Cortex AI")
        col1,col2 = st.columns(2)
        with col1:
            from_language = st.selectbox('From',dict(sorted(supported_languages.items())))
        with col2:
            to_language = st.selectbox('To',dict(sorted(supported_languages.items())))
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=300,placeholder='Enter text. For example, a call transcript.')
        btn_translate = st.button("Translate",type="primary")
        if entered_text and btn_translate:
          entered_text = entered_text.replace("'", "\\'")
          cortex_response = session.sql(f"select snowflake.cortex.translate('{entered_text}','{supported_languages[from_language]}','{supported_languages[to_language]}') as response").to_pandas().iloc[0]['RESPONSE']
          st.write(cortex_response)

def sentiment_analysis():
    with st.container():
        st.header("Sentiment Analysis With Snowflake Cortex AI")
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=400,placeholder='Enter text. For example, a call transcript.')
        btn_sentiment = st.button("Sentiment Score",type="primary")
        if entered_text and btn_sentiment:
          entered_text = entered_text.replace("'", "\\'")
          cortex_response = session.sql(f"select snowflake.cortex.sentiment('{entered_text}') as sentiment").to_pandas().iloc[0]['SENTIMENT']
          st.text(f"Sentiment score: {cortex_response}")
          st.caption("Note: Score is between -1 and 1; -1 = Most negative, 1 = Positive, 0 = Neutral")  

page_names_to_funcs = {
    "JSON Summary": summarize,
    "Translate": translate,
    "Sentiment Analysis": sentiment_analysis,
}

selected_page = st.sidebar.selectbox("Select", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
```

### Run

To run the application, click on **Run** located at the top right corner. If all goes well, you should see the application running as shown below.

#### Sample Transcript

Copy and paste the following sample transcript for JSON Summary, Translate, and Sentiment Analysis:

```sh
Customer: Hello!
Agent: Hello! I hope you're having a great day. To best assist you, can you please share your first and last name and the company you're calling from?
Customer: Sure, I'm Michael Green from SnowSolutions.
Agent: Thanks, Michael! What can I help you with today?
Customer: We recently ordered several DryProof670 jackets for our store, but when we opened the package, we noticed that half of the jackets have broken zippers. We need to replace them quickly to ensure we have sufficient stock for our customers. Our order number is 60877.
Agent: I apologize for the inconvenience, Michael. Let me look into your order. It might take me a moment.
Customer: Thank you.
```

### Update LLM

Let's try using one of the [other supported LLMs in Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability) with `snowflake.cortex.complete` function and see how it might perform given the same prompt/instructions.

1) On line 16, or, search for `claude-4-sonnet` in the Streamlit app code and repalce it with `llama3.1-70b`. *Note: If that model is not available in your region, pick another one that you can use.*
2) Click on **Run** at the top right.
3) Select **JSON Summary** from the sidebar menu.
4) Copy-paste the same sample transcript from above and click on **Summarize** button.

This is also a good way to quickly and easily compare how different LLMs might perform given the same prompt/instructions.

<!-- ------------------------ -->
## End-to-End Application


For an end-to-end application experience with Snowflake Cortex AI using SQL and Python APIs, download this [.ipynb](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Getting%20Started%20With%20Snowflake%20Cortex%20AI%20in%20Snowflake%20Notebooks/dash_snowflake_cortex_ai_101_notebook_app.ipynb) and [import](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-create#label-notebooks-import) it in your Snowflake account. 

> 
> NOTE: Before running the cells in the notebook, make sure of the prerequisites listed below.

### Prerequisites

- Install packages `snowflake`, `snowflake-ml-python`, `streamlit`. Learn how to [install packages](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-import-packages#import-packages-from-anaconda).
- For Fine-tuning, you must be using a Snowflake account in [supported regions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-finetuning).

### Table of Contents

  - Task-Specific LLM Functions  
    - Translate  
    - Sentiment Score  
    - Summarize  
  - Prompt Engineering  
  - Guardrails  
  - Compute Cost and Credits  
    - Count Tokens  
    - Track Credit Consumption  
      - Credit Consumption by Functions and LLMs  
      - Credit Consumption by Queries
  - Use Case
      - Automatic Ticket Categorization Using LLM  
        - Load Data
        - Preview Support Tickets  
        - Define Categorization Prompt  
        - Use Larger LLM  
        - Compare Larger and Smaller LLM Outputs  
      - Fine-Tune  
        - Generate Dataset to Fine-Tune Smaller LLM  
        - Split Data – Training and Evaluation  
        - Fine-Tune Options: SQL or Snowflake AI & ML Studio  
        - Fine-Tune Using SQL
            - Fine-Tuning Status  
        - Inference Using Fine-Tuned LLM  
        - Compare Token Credits
      - Streamlit Application  
        - Auto-Generate Custom Emails and Text Messages  

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You've successfully completed the Getting Started with Snowflake Cortex AI quickstart guide. 

### What You Learned

- How to use Snowflake Cortex AI for custom tasks like summarizing long-form text into JSON formatted output using prompt engineering and task-specific LLM functions to perform operations like translate, sentiment scoring, etc
- How to fine-tune an LLM in Snowflake
- How to build a Streamlit application and a Snowflake Notebook that uses Snowflake Cortex AI capabilities in Snowflake

### Related Resources

- [Snowflake Cortex AI: End-to-End Application Notebook](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/blob/main/Getting%20Started%20With%20Snowflake%20Cortex%20AI%20in%20Snowflake%20Notebooks/dash_snowflake_cortex_ai_101_notebook_app.ipynb)
- [Snowflake Cortex AI: Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)
- [Snowflake Cortex AI: Functions](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions)
- [Snowflake Cortex AI: Functions Cost Considerations](https://docs.snowflake.com/user-guide/snowflake-cortex/llm-functions#cost-considerations)
- [Snowflake Cortex AI: ML Functions](https://docs.snowflake.com/en/guides-overview-ml-functions)
