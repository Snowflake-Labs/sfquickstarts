author: Vino Duraisamy
id: build_rag_based_blog_ai_assistant_using_streamlit_openai_and_llamaindex
summary: This guide will provide step-by-step details for building an LLM chatbot called SnowStart that answers questions based on Snowflake Quickstart Blogs
categories: data-science-&-ml,app-development
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, LLMs, Generative AI, Streamlit, ChatBot, OpenAI

# SnowStart: Build a Retrieval Augmented Generation(RAG) based LLM assistant using  Streamlit, OpenAI and LlamaIndex
<!-- ------------------------ -->
## Overview

Duration: 5

This quickstart will cover the basics of Retrieval Augmented Generation (RAG) and how to build an LLM assistant (SnowStart) using Streamlit, OpenAI and LlamaIndex. The AI assistant will be trained on Snowpark data engineering quickstarts and can answer questions related to those blogs.

Here is a summary of what you will be able to learn in each step following this quickstart:

- **Setup Environment**: Setup your development environment, access OpenAI API keys and install the dependancies needed to run this quickstart
- **Data Pipeline**: Build a data pipeline to download the blogs on which the AI assisstant is trained on
- **Build Index**: Chunk the blogs into smaller contexts which can then be appended with the input prompt to an LLM
- **Streamlit Application**: Build a Streamlit App to serve as the UI for SnowStart

Let's dive into the key features and technologies used in the demo, for better understanding.

### Key Features & Technology

- Large Language Models (LLMs)
- Retrieval Augmented Generation
- LlamaIndex
- Streamlit

### What is a large language model (LLM)?

A large language model, or LLM, is a deep learning algorithm that can recognize, summarize, translate, predict and generate text and other content based on knowledge gained from massive datasets. Some examples of popular LLMs are [GPT-4](https://openai.com/research/gpt-4), [GPT-3](https://openai.com/blog/gpt-3-apps), [BERT](https://cloud.google.com/ai-platform/training/docs/algorithms/bert-start), [LLaMA](https://ai.facebook.com/blog/large-language-model-llama-meta-ai/), and [LaMDA](https://blog.google/technology/ai/lamda/).

### What is OpenAI?

OpenAI is the AI research and deployment company behind ChatGPT, GPT-4 (and its predecessors), DALL-E, and other notable offerings. Learn more about [OpenAI](https://openai.com/). We use OpenAI in this guide, but you are welcome to use the large language model of your choice in its place.

### What is Retrieval Augmented Generation(RAG)?

Retrieval Augmentation Generation (RAG) is an architecture that augments the capabilities of a Large Language Model (LLM) like GPT-4 by adding an information retrieval system that provides the models with relevant contextual data. Through this information retrieval system, we could provide the LLM with additional information around specific industry or a company's proprietary data and so on.

### What is LlamaIndex?

Applications built on top of LLMs often require augmenting these models with private or domain-specific data. LlamaIndex (formerly GPT Index) is a data framework for LLM applications to ingest, structure, and access private or domain-specific data.

### What is Streamlit?

Streamlit enables data scientists and Python developers to combine Streamlit's component-rich, open-source Python library with the scale, performance, and security of the Snowflake platform. Learn more about [Streamlit](https://streamlit.io/).

### What You Will Learn?

- How to build a data pipeline to download the blogs for retrieval
- How to chuck the blogs into smaller contexts which can then be augmented with the input prompt to an LLM
- How to build a Streamlit App to serve as the UI for SnowStart bot

### Prerequisites

- **GitHub account** - If you don't already have a GitHub account you can create one for free. Visit the [Join GitHub](https://github.com/signup) page to get started.
- A **OpenAI account** or API key to another language model - [Sign-in or create an account](https://openai.com/)
  - [OpenAI API Key](https://platform.openai.com/account/api-keys)

<!-- ------------------------ -->
