author: ushareng
id: automated_contract_analysis_using_llm_with_snowflake_notebooks
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Automated Contract Analysis using LLM with Snowflake Notebooks
<!-- ------------------------ -->
## Overview 
Duration: 5

LLMs like Snowflake-Arctic and Llama offer unparalleled capabilities in understanding and processing natural language, making them ideal for contract analysis. These models can be fine-tuned to identify specific legal terms, obligations, and risks, transforming raw contract text into structured insights.

Automated Contract Analysis not only enhances productivity by handling large volumes of documents but also provides consistency and reduces the potential for oversight. By integrating such AI-driven solutions into their operations, companies can streamline contract review processes, ensuring faster negotiations, better risk management, and overall improved legal compliance.

This shift toward automation marks a pivotal advancement in how legal workflows are managed in legal Business. 

### Prerequisites
- A Snowflake Account that you have `ACCOUNTADMIN`
- Familiarity with Snowflake SQL
- Agreed to the [Snowflake Consumer Terms of Service](https://other-docs.snowflake.com/en/collaboration/consumer-becoming) for the Marketplace

### What You’ll Learn 
- How to use LLMs within the Snowflakes Notebooks
- Trying out different Prompt Engineering Techniques
- Create a Streamlit App with Snowflakes Notebooks

### What You’ll Need 
- [Snowflake Account](https://signup.snowflake.com/?utm_cta=quickstarts_) with `ACCOUNTADMIN` access
- [FullContact Trial Account](https://platform.fullcontact.com/register/offer/snowresolve)

### What You’ll Build 
An Automated Contract Analysis App Using Snowflakes

<!-- ------------------------ -->
## Load the Data
Duration: 2

Steps to load data in the notebook are as follows:

- We will use the Sample CSV Data file available [here](https://drive.google.com/file/d/1LtSDibZA9sIwwWuLOI4fK401QduntOBX/view?usp=sharing)
- Open a SnowFlakes Worksheet
- Run the Following Query to Create a Database with a Schema:
```
USE ROLE accountadmin;
CREATE OR REPLACE DATABASE Contract;
CREATE SCHEMA notebooks;
```
- Go to `Data -> Databases` and Select the Database you create and then select the Schema
- On the Right Top, you will find an Option to `CREATE-> Table -> From File`
  
  <img width="468" alt="image" src="https://github.com/user-attachments/assets/c867f18b-121e-4804-8868-1dadc9ed79a5">
- Upload the csv file via Browse
- Click on Next and Load the Data after giving it some Name
  
  <img width="468" alt="image" src="https://github.com/user-attachments/assets/4e0e7ee2-0b53-4e2d-9e28-0f97f26edd1c">

## Getting Started with Notebooks
Duration: 5

To start with snowflake notebook, follow the detailed steps below:
- Go to Projects -> Notebooks
- On the Top Right, click on the “+ Noteobooks”
- Run Setup.sql file
- Make sure the Python Environment is “Run On Container” and Select the Database and Scheme which was Created Earlier
  
  <img width="468" alt="image" src="https://github.com/user-attachments/assets/39a22fd6-f606-476c-80d6-ef278e4b4324">
- On the Top Right, Start a Session and turn on the External Access `starter.py`
- The dataset consists of unstructured contract information, detailing agreements between two parties (Party A and Party B), including key contract dates like effective and termination dates, renewal options, obligations for each party, and dispute resolution methods. It provides structured insights into various contracts by summarizing critical data points like payments, services, and legal jurisdictions `loadData.py`
- You convert the Snowflake DataFrame (referred to as cell2) into a Pandas DataFrame using .to_pandas(). Then, you remove the column labeled DISPUTERESOLUTION using drop(), which allows you to simplify the dataset by eliminating unnecessary information. Now, let’s create some helper functions `helperFunction.py`
- You define two functions. The maketrueoutput(i) function generates a JSON structure from your Pandas DataFrame, formatting the contract data for a specific row (i). The check() function compares two JSON objects, evaluating their similarity using a model, which returns a score between 0 (no match) and 1 (exact match). This helps ensure data accuracy during comparisons.

## Zero-Shot Prompting
Duration: 1

- Now, we will do the Zero-Shot Prompting
`zeroshot.py`
- We get a score of 7.99 out of 20, thus there is good room for improvement.

## Few-Shot Prompting
Duration: 1

In **Few-Shot Prompting**, you provide the model with an example format of the structured JSON you want, which helps guide its responses. This prompt includes a sample JSON output, so the model understands the structure you expect. The for loop applies the model to 20 rows of unstructured data, comparing each output against the true JSON, and summing the similarity scores.

Few-Shot Prompting is typically better than **Zero Shot** because it gives the model a concrete example, which improves accuracy and consistency in structuring the data. By seeing the desired format, the model is more likely to follow it closely, reducing errors.

We get a score of **15.57**, quite an improvement
 
## Self Reflection

Duration: 1

In Self-Reflection, the model critically reviews its own output before returning the final response. The initial Prompt provides a structured JSON format and guidelines for verifying each key and value (such as dates, obligations, and renewal options). In the loop, after generating a first output, the model is asked to analyze and recheck it for errors, ensuring that all keys are correct and in the expected format. The corrected JSON is then compared to the true output, and the accuracy score is updated.

Self-Reflection is the best method because the model actively critiques and refines its own response, reducing the chances of errors. By prompting the model to validate and adjust its work, this approach leads to more accurate, reliable results compared to both Zero-Shot and Few Shot prompting. It ensures deeper consistency and correctness, especially in complex tasks like parsing contracts.

We get a score of **16.107**

## Streamlit App

<img width="468" alt="image" src="https://github.com/user-attachments/assets/b8217a4f-5a15-46f1-8286-7a17fde812f0">

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

In conclusion, Self-Reflexion emerges as the most effective method, closely followed by Few-Shot, due to its ability to refine the model’s output through self-analysis and correction. True-Output, being the benchmark, demonstrates the ideal performance, but Self-Reflexion comes remarkably close, indicating its strength in improving accuracy. 

Zero-Shot, while fast, proves less reliable, highlighting the importance of providing structured examples or allowing for self-correction. Overall, incorporating feedback mechanisms significantly enhances the quality of model-generated outputs.


### What You Learned
- Using LLM with Snowflake notebooks
- Prompt Engineering Techniques
- Making a Streamlit app

### Related Resources
- https://medium.com/@ingridwickstevens/extract-structured-data-from-unstructured-text-using-llms-71502addf52b
- https://www.promptingguide.ai/
- https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions

