summary: Getting Started with Analyzing Images with Anthropic on Snowflake Cortex
id: getting_started_with_analyzing_images_with_anthropic_on_snowflake_cortex
categories: getting-started
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, SQL, Data Engineering, AI
author: James Cha-Earley

# Getting Started with Analyzing Images with Anthropic on Snowflake Cortex AI
<!-- ------------------------ -->
## Overview

Duration: 5

In this quickstart, you'll learn how to build an end-to-end application for image analysis using AI models through Snowflake Cortex AI. This application leverages multimodal capabilities of models like Claude 4 Sonnet and Pixtral-large to extract insights, detect emotions, and generate descriptions from images - all within the Snowflake ecosystem. 

*Note: SNOWFLAKE.CORTEX.COMPLETE multimodal capability is currently in Public Preview.*

### What You'll Learn
- Setting up a Snowflake environment for image processing
- Creating storage structures for image data
- Using Snowflake Cortex to analyze images with AI models
- Building an interactive image analysis application
- Implementing batch processing for multiple images

### What You'll Build
A full-stack application that enables users to:
- Upload and store images in Snowflake
- Extract detailed insights from images using AI models
- Identify scenes, objects, text, and emotions in images
- Generate custom descriptions based on specific prompts
- Process images individually or in batch

### Prerequisites
- Snowflake account in a [supported region for Cortex functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability)
- Account must have these features enabled:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Anaconda Packages](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages#using-third-party-packages-from-anaconda)
  - [Cortex LLM Functions](https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex)
  - [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

<!-- ------------------------ -->
## Setup Environment

Duration: 10

To set up your Snowflake environment for image analysis:

1. Download the [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-image-classification-with-anthropic-snowflake-cortex/blob/main/setup.sql) file
2. Open a new worksheet in Snowflake
3. Paste the contents of setup.sql or upload and run the file
4. The script will create:
   - A new database and schema for your project
   - An image storage stage
   - Table for processing images

### Upload Images

After running the setup script:

1. Download the [data.zip](https://github.com/Snowflake-Labs/sfguide-getting-started-with-image-classification-with-anthropic-snowflake-cortex/blob/main/data/data.zip) and unzip for sample photos
2. Navigate to Data > Databases > IMAGE_ANALYSIS > IMAGES > Stages
3. Click "Upload Files" button in top right
4. Select your image files
5. Verify upload success:

```sql
ls @image_analysis.images;
```

You should see your uploaded files listed with their sizes.

> aside positive
> TIP: For best results, ensure your images are:
> - Clear and well-lit
> - In common formats (PNG, JPEG, WEBP)
> - No larger than 20MB
> - Have sufficient resolution for details you want to analyze

<!-- ------------------------ -->
## Create Snowflake Notebook

Duration: 15

Let's create a notebook to further explore image analysis techniques:

1. Navigate to Projects > Notebooks in Snowflake
2. Click "+ Notebook" button in the top right
3. To import the existing notebook:
   * Click the dropdown arrow next to "+ Notebook" 
   * Select "Import .ipynb" from the dropdown menu
   * Upload the [image_analysis_notebook.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-image-classification-with-anthropic-snowflake-cortex/blob/main/image_analysis_notebook.ipynb) file
4. In the Create Notebook popup:
   * Select your IMAGE_ANALYSIS database and schema
   * Choose an appropriate warehouse
   * Click "Create" to finish the import

The notebook includes:
- Setup code for connecting to your Snowflake environment
- Functions for analyzing images with different AI models
- Example analysis with various prompt types
- Batch processing capabilities for multiple images
- Comparison between Claude 3.5 Sonnet and Pixtral-large models

<!-- ------------------------ -->
## Build Streamlit Application

Duration: 15

Let's create a Streamlit application for interactive image analysis:

### Setting Up the Streamlit App

To create and configure your Streamlit application in Snowflake:

1. Navigate to Streamlit in Snowflake:
   * Click on the **Streamlit** tab in the left navigation pane
   * Click on **+ Streamlit App** button in the top right

2. Configure App Settings:
   * Enter a name for your app (e.g., "Image Analyzer")
   * Select your preferred warehouse
   * Choose IMAGE_ANALYSIS as your database and schema

3. Create the app:
   * In the editor, paste the complete code provided in the [image_analysis_streamlit.py](https://github.com/Snowflake-Labs/sfguide-getting-started-with-image-classification-with-anthropic-snowflake-cortex/blob/main/image_analysis_streamlit.py) file
   * Click "Run" to launch your application

The application provides:
- A model selector dropdown (Claude 4 Sonnet or Pixtral-large)
- Analysis type selection
- Custom prompt capability
- Image selection and display
- Prompt display for transparency
- Results viewing

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 5

Congratulations! You've successfully built an end-to-end image analysis application using AI models via Snowflake Cortex. This solution allows you to extract valuable insights from images, detect emotions, analyze scenes, and generate rich descriptions - all within the Snowflake environment.

To continue your learning journey, explore creating more advanced prompting techniques, building domain-specific image analysis systems, or integrating this capability with other Snowflake data workflows.

### What You Learned
- How to set up Snowflake for image storage and processing
- How to use AI models like Claude 4 Sonnet and Pixtral-large for multimodal analysis
- How to create custom prompts for specialized image analysis
- How to build a Streamlit application for interactive image analysis
- How to implement batch processing for multiple images

### Related Resources
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-llm-rest-api)
- [Anthropic Tool Use on Snowflake Cortex Quickstart](https://quickstarts.snowflake.com/guide/getting-started-with-tool-use-on-cortex-and-anthropic-claude/index.html?index=..%2F..index#0)
- [Anthropic RAG on Snowflake Cortex Quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_anthropic_on_snowflake_cortex/index.html?index=..%2F..index#0)
