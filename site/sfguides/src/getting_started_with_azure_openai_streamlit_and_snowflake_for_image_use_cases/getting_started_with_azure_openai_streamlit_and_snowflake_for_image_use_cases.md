id: getting_started_with_azure_openai_streamlit_and_snowflake_for_image_use_cases
summary: Getting Started with Azure OpenAI Streamlit and Snowflake using Snowpark External Access for image use cases
categories: featured,getting-started,app-development, azure, openai, streamlit, genai, ai, ml, image
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Generative AI, Snowflake External Access, Azure, OpenAI, Snowpark, Streamlit
authors: Matt Marzillo

# Getting Started with Azure OpenAI, Streamlit and Snowflake
<!-- ------------------------ -->
## Overview

Duration: 5

In this quickstart we will build a Streamlit application that leverages Snowpark External Access in Snowflake with Azure OpenAI that will generate a recommendation for clothing items given an image of a person.

In summary this is what you will do:
- Set up environments in both Snowflake and Azure.
- Create a function that leverages Snowpark External Access to make a call to Open AI.
- Create a Streamlit app that leverages the above function to generate responses using data from Snowflake and prompts.

### What is Generative AI?
Generative AI is a category of artificial intelligence techniques that enable machines to create new, original content, such as text, images, or music, by learning from existing data. These models, often based on neural networks, generate content by understanding patterns and structures in the training data and then producing novel examples that resemble what they have learned. Generative AI has applications in various fields, including natural language processing, computer vision, and creative arts.

### What is Azure OpenAI?
Azure OpenAI is a cloud-based service provided by Microsoft that integrates OpenAI's powerful language models, including GPT-4, into the Azure platform, enabling developers and businesses to build and deploy AI applications with advanced natural language processing capabilities. This collaboration offers high scalability, enterprise-grade security, and compliance features, making it suitable for a wide range of applications, from chatbots to complex data analysis. Users can access Azure's robust infrastructure and tools to train, fine-tune, and manage AI models efficiently. Azure OpenAI simplifies the process of implementing AI solutions while providing the flexibility to customize them according to specific organizational needs.

### What is Snowflake?
Snowflake is a cloud-based data warehousing solution that allows businesses to store and analyze large volumes of data efficiently. It separates storage and compute functionalities, enabling users to scale resources independently and pay only for what they use. Snowflake supports a wide range of data workloads, including data warehousing, data lakes, and data engineering, and offers robust data sharing capabilities across different cloud platforms.

### What is Streamlit?
Streamlit is a Python library that makes it easy to create and share custom web apps for machine learning and data science. In just a few minutes you can build and deploy powerful data apps.

### Pre-requisites
- Familiarity with [Snowflake](https://quickstarts.snowflake.com/guide/getting_started_with_snowflake/index.html#0) and a Snowflake account
with Access to [Streamlit](https://streamlit.io/) in your Snowflake account.
- [Azure Account](https://azure.microsoft.com) with Azure OpenAI or a stand alone OpenAI service.
- Familiarity with the Python programming language.

### What you’ll build
We will build an efficient architecture all within Snowflake that will access product urls and images in Snowflake and pass that data to a an Azure OpenAI model to generate a recommendation . The architecture will look like this

![](assets/architecture.png)

<!-- ------------------------ -->
## Use Case
Duration: 5

This use case will leverage sample urls along with sample images that will be passed to the OpenAI model in order to provide recommendations from the urls using the image data as context along with the prompt.

<!-- ------------------------ -->
## Azure / Open AI Environment

Duration: 10



![](assets/)

<!-- ------------------------ -->
## Snowflake Environment

Duration: 10

Copy and paste the below code into your Snowflake worksheet, what we’ll be doing here is creating two tables inside of a database that will be used in our application.

```sql

```

<!-- ------------------------ -->
## Snowpark External Access to call OpenAI

Duration: 15

Now we will work through the below code which will access the purchase data from Snowflake and generate a message from OpenAI. You will have to update the 2-3 values from the OpenAI tokens that we generated earlier.

```sql

```

<!-- ------------------------ -->
## Build Streamlit App - With data in Snowflake (OPTIONAL)

Duration:

Let's build a new app similar to the one above, but with some of the data that we loaded to Snowflake. The app will additionally include a filter for a specific customer to provide context. There are several lines of code indicated below where the user has to write Snowpark and Python code to complete the app

```python

```

<!-- ------------------------ -->
## Test Prompt Engineering (OPTIONAL)

Duration: 

Prompt engineering for a language model involves crafting your questions or prompts in a way that maximizes the effectiveness and accuracy of the responses you receive. Here are some simple guidelines to help you with prompt engineering:

**Be Clear and Specific:** The more specific your prompt, the better. Clearly define what you're asking for. If you need information on a specific topic, mention it explicitly.

**Provide Context:** If your question builds on particular knowledge or a specific scenario, provide that context. This helps the model understand the frame of reference and respond more accurately.

**Use Direct Questions:** Phrase your prompts as direct questions if you're looking for specific answers. This approach tends to yield more focused responses.

**Break Down Complex Queries:** If you have a complex question, break it down into smaller, more manageable parts. This can help in getting more detailed and precise answers.

**Specify the Desired Format:** If you need the information in a particular format (like a list, a summary, a detailed explanation), mention this in your prompt.

**Avoid Ambiguity:** Try to avoid ambiguous language. The clearer you are, the less room there is for misinterpretation.

**Sequential Prompts for Follow-ups:** If you're not satisfied with an answer or need more information, use follow-up prompts that build on the previous ones. This helps in maintaining the context and getting more refined answers.

**Experiment and Iterate:** Don’t hesitate to rephrase or adjust your prompts based on the responses you get. Sometimes a slight change in wording can make a big difference.

**Consider the Model's Limitations:** Remember that the model may not have the latest information, and it cannot browse the internet or access personal data unless explicitly provided in the prompt.

**Ethical Use:** Always use the model ethically. Avoid prompts that are harmful, biased, or violate privacy or legal guidelines.

Let’s look at how we can experiment and iterate on the prompt that we provided to the LLM function in Streamlit. Go back to the previous step and test out different prompt strategies to see if you can improve the accuracy of the response.

Consider the above concepts and also consider this pointed [guide to prompting](https://github.com/VILA-Lab/ATLAS/blob/main/data/README.md)

(it is required that you try the prompt in principal #6 🙂)

<!-- ------------------------ -->
## Conclusion

Duration: 5

### What we covered
After setting up our AWS and Snowflake and environments we built two primary things: a UDF that utilizes Snowpark External Access to make a call to different OpenAI models and a Streamlit app that leverages that function to make a simple and useful app that can be shared within an organization. With these two, easy to build, Snowflake features we expect customers to see value quickly when using Snowflake and OpenAI!

### What You Learned

- How to set up a Snowflake and Azure / OpenAI environment to integrate the two platforms.
- How to build a Snowpark External Access integration to call OpenAI.
- How to build a Streamlit app that calls OpenAI leveraging tabular and image data from Snowflake.


### Related resources 
- [RBAC with External Services](https://www.youtube.com/watch?v=fALb8SosA_U)

- [Prompting](https://github.com/VILA-Lab/ATLAS/blob/main/data/README.md)

- [Streamlit](https://streamlit.io/)

- [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)

If you have any questions, reach out to your Snowflake account team!
