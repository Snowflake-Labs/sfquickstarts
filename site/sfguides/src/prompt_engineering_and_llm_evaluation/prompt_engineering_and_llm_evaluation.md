author: Vino Duraisamy
id: prompt_engineering_and_llm_evaluation
summary: This guide provides instructions to perform prompt engineering on your LLM models and to build a streamlit app for evaluating LLM responses using human feedback
categories: data-science-&-ml, app-development
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Generative AI, Snowflake External Access, OpenAI, LLMs, Streamlit, Snowflake Marketplace

# Prompt Engineering and Evaluation of LLM responses through human feedback
<!-- ------------------------ -->
## Overview 

Duration: 5

This quickstart will cover the basics of prompt engineering on your Large Language Models (LLMs) and how to evaluate the responses of different LLMs through human feedback.

By completing this guide, you will learn how to run AI experimentation with different LLMs for your use case. First part of the quickstart focusses on using prompt engineering to generate different model responses by tweaking your prompts. The second part focusses on evaluating different LLM model responses through human feedback.

Here is a summary of what you will be able to learn in each step following this quickstart:

- **Setup Environment**: Setup your Snowflake Free Trial environment
- **Snowflake Marketplace**: Download the data you need from Snowflake Marketplace and use it in your analysis
- **Snowflake External Access**: Integrate LLMs such as GPT-3.5 and GPT4 to Snowflake using External Access
- **Prompt Engineering**: Use different prompts on an LLM and capture the responses into a Snowflake table
- **LLM Evaluation with Human Feedback**: Build a Streamlit App to compare and rate the LLM responses and capture the ratings in a Snowflake table
- **What's next?**: What other applications can you build for your industry and data, inspired from this quickstart?

Let's dive into the key features and technologies used in the demo, for better understanding.

### Key features & technology

- Large language models (LLMs)
- Prompt Engineering
- LLM Evaluation
- Snowflake External Access
- Snowflake Marketplace
- Streamlit

### What is a large language model (LLM)?

A large language model, or LLM, is a deep learning algorithm that can recognize, summarize, translate, predict and generate text and other content based on knowledge gained from massive datasets. Some examples of popular LLMs are [GPT-4](https://openai.com/research/gpt-4), [GPT-3](https://openai.com/blog/gpt-3-apps), [BERT](https://cloud.google.com/ai-platform/training/docs/algorithms/bert-start), [LLaMA](https://ai.facebook.com/blog/large-language-model-llama-meta-ai/), and [LaMDA](https://blog.google/technology/ai/lamda/).

### What is OpenAI?

OpenAI is the AI research and deployment company behind ChatGPT, GPT-4 (and its predecessors), DALL-E, and other notable offerings. Learn more about [OpenAI](https://openai.com/). We use OpenAI in this guide, but you are welcome to use the large language model of your choice in its place.

### What is Prompt Engineering?

A prompt is a natural language text that requests the Generative AI model to perform a specific task. Prompt Engineering is the process of guiding the AI model to generate a specific response by tweaking the prompt text. Prompt Engineering uses a mix of creativity and experimentation to identify the right set of prompts that ensures the AI model will return the desired response.

### What is LLM Evaluation?

Since Large Language Model outputs free form texts that may not have the ground truth, it can be difficult to evaluate the LLMs using traditional model metrics such as Accuracy, Precision, Recall, F1-Score, etc. There are multiple frameworks in development to evaluate the bias, toxicity and hallucination in LLM responses. However, the most popular and efficient method has been human-in-the-loop evaluation. That is, letting humans rate the model responses as helpful and right.

### What is Snowflake External Access?

[External Access](https://docs.snowflake.com/en/developer-guide/external-network-access/external-network-access-overview) helps to securely connect to the OpenAI API from [Snowpark](https://docs.snowflake.com/en/developer-guide/snowpark/index), the set of libraries and runtimes in Snowflake that run non-SQL code, including Python, Java and Scala. External Access provides flexibility to reach public internet endpoints from the Snowpark sandbox without any additional infrastructure setup.

### What is the Snowflake Marketplace?

The [Snowflake Marketplace](https://www.snowflake.com/en/data-cloud/marketplace/) provides users with access to a wide range of datasets from third-party data stewards, expanding the data available for transforming business processes and making decisions. Data providers can publish datasets and offer data analytics services to Snowflake customers. Customers can securely access shared datasets directly from their Snowflake accounts and receive automatic real-time updates.

### What is Streamlit?

Streamlit is an open-source Python library that enables developers to quickly create, deploy, and share web apps from Python scripts. Learn more about [Streamlit](https://streamlit.io/).

### What You Will Learn

- How to access data from Snowflake Marketplace and use it for your analysis
- How to use External Access to securely connect to the OpenAI API from Snowpark
- How to use different prompts on a Large Language Model and capture model responses in a Snowflake table
- How to build a Streamlit App to compare the model responses and capture the review in a Snowflake table

### Prerequisites

- A **Snowflake account** with ACCOUNTADMIN role access - [Sign-in or create a free trial account](https://signup.snowflake.com/)
- **Anaconda Terms & Conditions accepted**. See Getting Started section in [Third-Party Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#getting-started).
- **GitHub account** - If you don't already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/signup) page to get started.
- A **OpenAI account** or API key to another language model - [Sign-in or create an account](https://openai.com/)
  - [OpenAI API Key](https://platform.openai.com/account/api-keys)

<!-- ------------------------ -->

