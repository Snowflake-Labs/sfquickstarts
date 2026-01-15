id: extracting-insights-from-multimodal-customer-service-data
summary: Analyze multimodal customer service data with Snowflake Cortex AI for insights from text, audio, images, and conversation transcripts.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/build
language: en
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
author: James Cha-Earley


# Snowflake Cortex AI SQL: Extracting Insights from Multimodal Customer Service Data

## Overview

In this quickstart, you'll learn how to build a comprehensive customer service analytics system that processes audio, text, and document data using Snowflake Cortex AI functions. This application demonstrates how to extract insights from multimodal data sources including call recordings, chat logs, support tickets, and PDF documents.

### What You'll Learn
- Using AI_TRANSCRIBE to convert audio recordings to text
- Implementing AI_TRANSLATE for multilingual support
- Applying AI_SENTIMENT for emotion detection
- Leveraging AI_CLASSIFY for automatic categorization
- Using AI_COMPLETE for intelligent summarization
- Processing documents with AI_PARSE_DOCUMENT
- Validating data quality with AI_EXTRACT
- Building complex SQL queries with multiple AI functions

### What You'll Build
A production-ready customer service analytics system that:
- Transcribes and analyzes customer service calls
- Translates conversations to English automatically
- Detects sentiment and categorizes issues
- Generates call summaries using LLMs
- Parses PDF documents for information extraction
- Validates chat logs against support tickets
- Identifies misalignments in customer data

### Prerequisites
- [Snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) in a [supported region for Cortex functions](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#label-cortex-llm-availability)
- Account must have these features enabled:
  - [Snowflake Notebooks](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks)
  - [Cortex AI Functions](https://docs.snowflake.com/en/sql-reference/functions-ai)

## Setup Environment

### Run Setup Script

1. Download the [setup.sql](https://github.com/Snowflake-Labs/sfguide-extracting-insights-from-multimodal-customer-data/blob/main/setup.sql) file from GitHub
2. Open a new SQL worksheet in Snowflake
3. Copy and paste the contents of setup.sql into the worksheet
4. Run the entire script to create:
   - Database and schema
   - Storage stages for audio files and documents
   - Required tables for storing results
   - Sample data tables

## Open Snowflake Notebooks

1. Download the [Notebook](https://github.com/Snowflake-Labs/sfguide-extracting-insights-from-multimodal-customer-data/blob/main/extracting_insights_from%20multimodal_customer_service_data.ipynb) from GitHub (NOTE: Do NOT right-click to download.)
2. In your Snowflake account:
   * On the left hand navigation menu, click on Projects » Notebooks
   * On the top right, click on Notebook down arrow and select **Import .ipynb** file from the dropdown menu
   * Select the file you downloaded in step 1 above
3. In the Create Notebook popup:
   * For Notebook location, select **MULTIMODAL_CUSTOMER_SERVICE** for your database and **DATA** as your schema
   * Select your **Warehouse**
   * Click on Create button

## Process Audio with AI Functions

The Notebook demonstrates how to chain multiple Snowflake Cortex AI functions together to analyze customer service calls. This section covers the complete audio processing pipeline.

### Build the Complete Pipeline

The first cell shows a comprehensive query that combines multiple AI functions:

1. **AI_TRANSCRIBE** - Converts audio files to text with speaker identification
2. **Flatten and Combine** - Extracts transcript segments and creates full conversation text
3. **AI_TRANSLATE** - Automatically translates conversations to English
4. **AI_SENTIMENT** - Analyzes emotional tone (positive, negative, neutral, mixed)
5. **AI_CLASSIFY** - Categorizes calls into custom issue types
6. **AI_COMPLETE** - Generates concise 50-word summaries using claude-sonnet-4-5

This unified approach processes each call through the entire analytics pipeline in one execution, storing comprehensive results in the transcription_results table.

### Explore Individual Functions

The Notebook then breaks down each AI function step-by-step, creating temporary tables to demonstrate:

- How AI_TRANSCRIBE returns structured JSON with segments and timestamps
- How to flatten transcript segments using the FLATTEN function
- How AI_TRANSLATE detects and converts multiple languages
- How AI_SENTIMENT provides detailed emotion analysis
- How AI_CLASSIFY uses custom categories with descriptions
- How AI_COMPLETE generates intelligent summaries with LLM prompts

### Custom Classification Categories

The AI_CLASSIFY function uses five business-specific categories:

1. **Fraud & Security Issues** - Unauthorized transactions, identity theft, account freezes
2. **Technical & System Errors** - Login problems, system glitches, auto-pay failures
3. **Payment & Transaction Problems** - Duplicate charges, failed payments, fee disputes
4. **Account Changes & Modifications** - Policy changes, fund transfers, coverage adjustments
5. **General Inquiries & Information Requests** - Status checks, documentation requests

Each category includes detailed descriptions to ensure accurate AI classification.

### Review Results

After processing, query the transcription_results table to see all analyzed calls with transcriptions, translations, sentiments, categories, and summaries. The Notebook includes cleanup steps to drop temporary tables.

> 
> TROUBLESHOOTING: If transcription quality is poor, check:
> - Audio file quality and clarity
> - Background noise levels
> - Speaker volume consistency
> - File format compatibility

## Process Documents and Text Data

### Parse PDF Documents

The Notebook demonstrates AI_PARSE_DOCUMENT for extracting structured information from PDF files. The function processes all documents in the COMPANY_DOCUMENTS stage using 'LAYOUT' mode with page splitting enabled.

The function returns detailed JSON containing:
- Extracted text content
- Document structure and layout
- Page-by-page information
- Metadata about the document

This parsed data can be used for document search, information extraction, or integration with RAG systems.

### Validate Chat Logs

For chat logs, the Notebook implements a validation system using AI_EXTRACT, AI_CLASSIFY, and AI_SENTIMENT to check data quality:

1. **Reconstruct Conversations** - Flatten message arrays into complete text
2. **Apply AI Analysis** - Analyze conversations with multiple AI functions
3. **Validate Self-Reported Data** - Compare AI results against agent classifications
4. **Flag Discrepancies** - Identify mismatches in categories and sentiments

The AI_EXTRACT function extracts structured information like:
- Issue descriptions
- Product names mentioned
- Error messages or codes
- Resolutions provided
- Customer satisfaction indicators
- Urgency levels

### Align Tickets with Chats

The final analysis uses AI_COMPLETE to semantically compare support tickets with their corresponding chat logs. The AI analyzes both data sources and returns:

- **Alignment status** - Whether they match (aligned/misaligned/partial)
- **Confidence level** - How certain the AI is (high/medium/low)
- **Reasoning** - Brief explanation of the assessment
- **Severity** - Impact level of any misalignment (critical/moderate/minor)

The query creates a comprehensive flagging system that identifies issue misalignments, category mismatches, and product inconsistencies. This cross-validation ensures data consistency across customer service systems and helps identify where processes need improvement.

## Conclusion and Resources

Congratulations! You've successfully built a comprehensive multimodal customer service analytics system using Snowflake Cortex AI functions. Using Snowflake Notebooks, you've implemented a solution that transcribes audio calls, translates conversations, analyzes sentiment, categorizes issues, generates summaries, parses documents, and validates data quality - all while keeping your data secure within Snowflake's environment.

### What You Learned
- How to use AI_TRANSCRIBE to convert audio recordings into searchable text
- How to implement AI_TRANSLATE for automatic multilingual support
- How to apply AI_SENTIMENT for customer emotion detection
- How to leverage AI_CLASSIFY for intelligent issue categorization
- How to use AI_COMPLETE with LLMs for generating summaries
- How to process PDF documents with AI_PARSE_DOCUMENT
- How to validate data quality using AI_EXTRACT
- How to build complex SQL queries combining multiple AI functions
- How to create comprehensive data validation pipelines

### Related Resources

**Documentation:**
- [Snowflake Cortex AI Functions](https://docs.snowflake.com/en/sql-reference/functions-ai)

**Sample Code & Guides:**
- [Snowflake Document AI](https://quickstarts.snowflake.com/guide/doc-ai-invoice-reconciliation/index.html?index=..%2F..index#0)
