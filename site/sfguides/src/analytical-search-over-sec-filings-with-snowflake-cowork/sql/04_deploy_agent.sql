USE ROLE ACCOUNTADMIN;
USE DATABASE SEC_FILINGS;
USE SCHEMA FILING_DATA;

-- Ensure Snowflake Intelligence (CoWork) object exists
CREATE SNOWFLAKE INTELLIGENCE IF NOT EXISTS SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT;

-- Deploy the Analytical Search agent (co-located with search service + semantic view)
CREATE OR REPLACE AGENT SEC_FILINGS.FILING_DATA.SEC_ANALYTICAL_SEARCH_AGENT
COMMENT = 'SEC filing research agent v7 - FILED_AT/PERIOD_OF_REPORT are now native DATE in the search service, range filters supported.'
FROM SPECIFICATION $$
{
  "models": { "orchestration": "claude-opus-4-7" },
  "orchestration": { "budget": { "seconds": 600, "tokens": 200000 } },
  "instructions": {
    "orchestration": "You are SEC Filing Analyst, an investment-research agent over a corpus of SEC EDGAR 10-K, 10-Q, 8-K filings.\n\nFor questions about counts, comparisons, exhaustive lists, or cross-filing patterns:\n1. Search broadly using multiple relevant queries — use synonyms and related phrasings.\n2. Return a clear answer with company name, form type, filing date, and the specific evidence from each filing chunk."
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_search",
        "name": "filing_semantic_search",
        "description": "Multi-index Cortex Search over SEC filing chunks."
      }
    },
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "filing_analyst",
        "description": "Structured analytics over pre-extracted filing signals (sector counts, sentiment percentages, signal trends)."
      }
    }
  ],
  "tool_resources": {
    "filing_semantic_search": {
      "name": "SEC_FILINGS.FILING_DATA.SEC_FILING_SEARCH",
      "search_service": "SEC_FILINGS.FILING_DATA.SEC_FILING_SEARCH",
      "database_schema": "SEC_FILINGS.FILING_DATA",
      "is_multi_index": true,
      "max_results": 1000,
      "id_column": "CHUNK_ID",
      "title_column": "COMPANY_NAME",
      "base_table": "SEC_FILINGS.FILING_DATA.FILING_CHUNKS",
      "base_table_columns": [
        "CHUNK_ID","CHUNK_TEXT","ACCESSION_NO","COMPANY_NAME","TICKER",
        "FORM_TYPE","SECTION_NAME","FILED_AT","PERIOD_OF_REPORT",
        "INDUSTRY_SECTOR","INDUSTRY_TITLE"
      ],
      "execution_environment": {"type": "warehouse", "warehouse": "FILING_WH"},
      "columns_and_descriptions": {
        "CHUNK_ID":         {"description": "Chunk primary key", "type": "string", "searchable": true,  "filterable": true},
        "CHUNK_TEXT":       {"description": "Full filing passage text. Search here for filing content.", "type": "string", "searchable": true, "filterable": false},
        "COMPANY_NAME":     {"description": "Filer company name. Search here for specific companies.", "type": "string", "searchable": true, "filterable": true},
        "TICKER":           {"description": "Stock ticker (e.g. NVDA, MSFT, GOOGL). Use for searching or filtering filings by specific public companies. Approximately 85% of filings have a populated ticker.", "type": "string", "searchable": true, "filterable": true},
        "FORM_TYPE":        {"description": "10-K, 10-K/A, 10-Q, 10-Q/A, 8-K, 8-K/A.", "type": "string", "searchable": false, "filterable": true},
        "SECTION_NAME":     {"description": "Filing section (Risk Factors, MD&A, Item 1.01, etc.).", "type": "string", "searchable": true, "filterable": true},
        "FILED_AT":         {"description": "SEC filing date (DATE). Supports @gte / @lte range filters.", "type": "date", "searchable": false, "filterable": true},
        "PERIOD_OF_REPORT": {"description": "Fiscal period end date (DATE). Supports @gte / @lte range filters.", "type": "date", "searchable": false, "filterable": true},
        "INDUSTRY_SECTOR":  {"description": "SIC-based sector grouping.", "type": "string", "searchable": false, "filterable": true},
        "INDUSTRY_TITLE":   {"description": "Detailed SIC industry title.", "type": "string", "searchable": false, "filterable": true},
        "ACCESSION_NO":     {"description": "SEC accession number, unique per filing.", "type": "string", "searchable": false, "filterable": true}
      }
    },
    "filing_analyst": {
      "semantic_view": "SEC_FILINGS.FILING_DATA.SEC_FILING_ANALYTICS",
      "execution_environment": {"type": "warehouse", "warehouse": "FILING_WH"}
    }
  }
}
$$;

-- Register in Snowflake CoWork
ALTER SNOWFLAKE INTELLIGENCE SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT
    ADD AGENT SEC_FILINGS.FILING_DATA.SEC_ANALYTICAL_SEARCH_AGENT;