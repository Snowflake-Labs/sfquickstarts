summary: Getting Started with Multimodal Analysis on Snowflake Cortex 
id: getting-started-with-multimodal-analysis-on-snowflake-cortex
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
author: James Cha-Earley

# Getting Started with Multimodal Analysis on Snowflake Cortex AI
<!-- ------------------------ -->
## Overview


In this quickstart, you'll learn how to build an end-to-end application for multimodal analysis using AI models through Snowflake Cortex AI. This application uses AI_COMPLETE with models like Claude 4 Sonnet and Pixtral-large to extract insights, detect emotions, and generate descriptions from images, plus uses AI_TRANSCRIBE to transcribe audio with speaker identification - all within the Snowflake ecosystem.

*Note: AI_COMPLETE multimodal capability and AI_TRANSCRIBE are currently in Public Preview.*

### What You'll Learn
- Setting up a Snowflake environment for multimodal processing
- Creating storage structures for image and audio data
- Using AI_COMPLETE to analyze images with AI models
- Implementing audio transcription with AI_TRANSCRIBE

### What You'll Build
A multimodal analysis system that enables users to:
- Upload and store images and audio files in Snowflake
- Extract detailed insights from images using AI models
- Identify scenes, objects, text, and emotions in images
- Transcribe audio with speaker identification and precise timestamps
- Generate custom descriptions based on specific prompts
- Process media files individually
- Combine image analysis with audio transcription for comprehensive content understanding

### Prerequisites
- Snowflake account in a [supported region for AI functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability)
- Account must have these features enabled:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [AI_COMPLETE Function](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
  - [AI_TRANSCRIBE Function](https://docs.snowflake.com/en/sql-reference/functions/ai-transcribe)

<!-- ------------------------ -->
## Setup Environment


To set up your Snowflake environment for multimodal analysis:

1. Download the [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-multimodal-analysis-with-anthropic-snowflake-cortex/blob/main/setup.sql) file
2. Open a new worksheet in Snowflake
3. Paste the contents of setup.sql or upload and run the file
4. The script will create:
   - A new database and schema for your project
   - Image and audio storage stages

### Upload Media Files

After running the setup script:

1. Download the [data.zip](https://github.com/Snowflake-Labs/sfguide-getting-started-with-multimodal-analysis-with-anthropic-snowflake-cortex/blob/main/data/data.zip) and unzip for sample images and audio files
2. For images:
   - Navigate to Data > Databases > MULTIMODAL_ANALYSIS > MEDIA > IMAGES > Stages
   - Click "Upload Files" button in top right
   - Select your image files
3. For audio files:
   - Navigate to Data > Databases > MULTIMODAL_ANALYSIS > MEDIA > AUDIO > Stages
   - Click "Upload Files" button in top right
   - Select your audio files
4. Verify upload success:

```sql
-- Check uploaded images
LS @MULTIMODAL_ANALYSIS.MEDIA.IMAGES;

-- Check uploaded audio files
LS @MULTIMODAL_ANALYSIS.MEDIA.AUDIO;
```

You should see your uploaded files listed with their sizes.

> 
> TIP: For best results, ensure your media files are:
> **Images:**
> - Clear and well-lit
> - In common formats (PNG, JPEG, WEBP)
> - No larger than 20MB
> - Have sufficient resolution for details you want to analyze
> 
> **Audio:**
> - Clear audio quality
> - Supported formats: FLAC, MP3, OGG, WAV, WEBM
> - Maximum 2 hours for text transcription, 1 hour for speaker segmentation
> - Maximum file size: 700 MiB

<!-- ------------------------ -->
## Create Snowflake Notebook


Let's create a notebook to explore multimodal analysis techniques:

1. Navigate to Projects > Notebooks in Snowflake
2. Click "+ Notebook" button in the top right
3. To import the existing notebook:
   * Click the dropdown arrow next to "+ Notebook" 
   * Select "Import .ipynb" from the dropdown menu
   * Upload the [multimodal_analysis_notebook.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-multimodal-analysis-with-anthropic-snowflake-cortex/blob/main/multimodal_analysis_notebook.ipynb) file
4. In the Create Notebook popup:
   * Select your MULTIMODAL_ANALYSIS database and MEDIA schema
   * Choose an appropriate warehouse
   * Click "Create" to finish the import

The notebook includes:
- Setup code for connecting to your Snowflake environment
- Functions for analyzing images with different AI models
- Audio transcription with various modes (text, word-level, speaker identification)
- Example analysis with various prompt types
- Comparison between Claude 4 Sonnet and Pixtral-large models for analyzing images

<!-- ------------------------ -->
## Conclusion And Resources


Congratulations! You've successfully built an end-to-end multimodal analysis system using AI models via Snowflake Cortex. This solution allows you to extract valuable insights from both images and audio content, perform transcription with speaker identification, detect emotions, analyze scenes, and generate rich descriptions - all within the Snowflake environment using AI_COMPLETE and AI_TRANSCRIBE functions.

The combination of visual and audio analysis capabilities opens up powerful possibilities for content understanding, customer experience analysis, compliance monitoring, and automated content processing workflows.

### What You Learned
- How to set up Snowflake for multimodal content storage and processing
- How to use AI_COMPLETE with AI models like Claude 4 Sonnet and Pixtral-large for comprehensive image analysis
- How to implement audio transcription with AI_TRANSCRIBE including speaker identification and timestamps
- How to create custom prompts for specialized analysis tasks
- How to implement batch processing for multiple media files
- How to combine image and audio analysis for enhanced content understanding

### Related Resources
- [AI_COMPLETE Function Reference](https://docs.snowflake.com/en/sql-reference/functions/ai_complete)
- [AI_TRANSCRIBE Function Reference](https://docs.snowflake.com/en/sql-reference/functions/ai-transcribe)
- [Anthropic Tool Use on Snowflake Cortex Quickstart](/en/developers/guides/getting-started-with-tool-use-on-cortex-and-anthropic-claude/)
- [Anthropic RAG on Snowflake Cortex Quickstart](/en/developers/guides/getting-started-with-anthropic-on-snowflake-cortex/)
