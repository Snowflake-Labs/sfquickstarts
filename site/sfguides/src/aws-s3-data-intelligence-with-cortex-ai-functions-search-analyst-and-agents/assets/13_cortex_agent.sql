/*=============================================================================
  13 - CORTEX AGENT (4 tools)
  Healthcare AI Intelligence Pipeline

  The agent combines:
    1. Cortex Analyst (text-to-SQL) over the semantic view for structured queries
    2. Cortex Search over parsed PDF documents
    3. Cortex Search over enriched TXT documents
    4. Cortex Search over transcribed patient consultations (audio)

  This agent is what Snowflake Intelligence will use as its backend.

  Depends on: 11 (search services), 12 (semantic view)
=============================================================================*/

USE ROLE ACCOUNTADMIN;
USE DATABASE HEALTHCARE_AI_DEMO;
USE SCHEMA ANALYTICS;
USE WAREHOUSE HEALTHCARE_AI_WH;

-----------------------------------------------------------------------
-- CORTEX AGENT
-----------------------------------------------------------------------
CREATE OR REPLACE AGENT ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT
  COMMENT = 'Healthcare intelligence agent combining structured data queries with unstructured search across PDF documents, text documents, and audio consultation transcripts.'
  FROM SPECIFICATION
$$
models:
  orchestration: auto

instructions:
  system: >
    You are a healthcare intelligence assistant. You help clinical staff,
    administrators, and analysts explore patient data, claims, appointments,
    medical documents, and consultation recordings. You combine structured
    data analysis with unstructured text search across AI-processed medical
    reports (PDFs), text documents, and audio transcriptions.
    Provide concise, clinically relevant answers. When presenting financial
    data, include totals and averages where helpful. When referencing documents
    or audio transcripts, cite the file name. Always protect patient privacy
    in your responses.
  orchestration: >
    Use HealthcareAnalyst for questions about patients, providers, claims
    (billed amounts, denied claims, insurance plans), appointments (scheduling,
    visit types, durations), and any quantitative or aggregate questions.

    Use PDFSearch for questions about specific PDF medical document content -
    diagnoses, lab results, prescriptions, radiology findings, clinical notes,
    or any information found in PDF medical reports.

    Use TXTSearch for questions about text-based medical documents -
    clinical notes, intake forms, nursing notes, referral letters, or any
    information found in TXT medical files.

    Use AudioSearch for questions about patient consultation recordings -
    what was discussed in a visit, chief complaints, medications mentioned,
    follow-up actions, or any information from transcribed audio.

    If a question spans both structured and unstructured data, use
    HealthcareAnalyst for the structured part and the appropriate search tool
    for the unstructured part, then combine the results in your response.
  sample_questions:
    - question: "Which providers have the highest total billed amounts?"
    - question: "How many claims were denied and what were the reasons?"
    - question: "Show me patients on Medicare Advantage with cardiology appointments"
    - question: "Find PDF documents mentioning diabetes or hypertension"
    - question: "Search text documents for clinical notes about medication changes"
    - question: "What consultations discussed medication changes?"
    - question: "Summarize the consultation notes for follow-up visits"
    - question: "What is the average claim amount by specialty?"
    - question: "Find radiology reports with abnormal findings"
    - question: "Which patients have documents, text files, and audio recordings?"
    - question: "What are the most common diagnoses across all claims?"
    - question: "Compare findings across PDF and TXT documents for the same patient"

tools:
  - tool_spec:
      type: cortex_analyst_text_to_sql
      name: HealthcareAnalyst
      description: >
        Queries structured healthcare data including patients, providers,
        claims (billing, diagnosis codes, procedure codes, payment status),
        and appointments (scheduling, visit types, durations). Use for any
        quantitative questions about costs, claim denials, patient counts,
        appointment trends, insurance plans, and provider performance.
  - tool_spec:
      type: cortex_search
      name: PDFSearch
      description: >
        Searches AI-processed PDF medical documents including lab reports,
        discharge summaries, prescriptions, radiology reports, clinical notes,
        and insurance claims. PDFs have been parsed with AI_PARSE_DOCUMENT,
        enriched with AI_EXTRACT, AI_CLASSIFY, AI_SENTIMENT, AI_SUMMARIZE,
        AI_TRANSLATE, AI_REDACT, and AI_COMPLETE. Search across the full text,
        summaries, key insights, and extracted diagnoses.
  - tool_spec:
      type: cortex_search
      name: TXTSearch
      description: >
        Searches AI-processed text medical documents including clinical notes,
        patient intake forms, nursing notes, and referral letters. Text files
        have been enriched with AI_EXTRACT, AI_CLASSIFY, AI_SENTIMENT,
        AI_SUMMARIZE, AI_TRANSLATE, AI_REDACT, and AI_COMPLETE. Search across
        the full text, summaries, key insights, and extracted diagnoses.
  - tool_spec:
      type: cortex_search
      name: AudioSearch
      description: >
        Searches transcribed patient consultation recordings (WAV and MP3 audio).
        Consultations have been transcribed with AI_TRANSCRIBE and enriched
        with AI_EXTRACT, AI_CLASSIFY, AI_SENTIMENT, AI_SUMMARIZE, AI_TRANSLATE,
        and AI_COMPLETE (SOAP notes). Search across full transcripts, summaries,
        consultation notes, and extracted chief complaints.

tool_resources:
  HealthcareAnalyst:
    semantic_view: "HEALTHCARE_AI_DEMO.ANALYTICS.HEALTHCARE_ANALYTICS"
  PDFSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.PDF_SEARCH"
  TXTSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.TXT_SEARCH"
  AudioSearch:
    name: "HEALTHCARE_AI_DEMO.PROCESSED.AUDIO_SEARCH"
$$;

-----------------------------------------------------------------------
-- VERIFY
-----------------------------------------------------------------------
DESCRIBE AGENT ANALYTICS.HEALTHCARE_INTELLIGENCE_AGENT;
