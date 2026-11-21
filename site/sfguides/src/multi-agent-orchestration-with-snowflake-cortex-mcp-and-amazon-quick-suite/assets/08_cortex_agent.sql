/*=============================================================
  08 -- Create Cortex Agent
  SUPPLY_CHAIN_AGENT with 3 tools:
    - Analyst (text-to-SQL via semantic view)
    - SupplierEmailSearch (Cortex Search)
    - InspectionSearch (Cortex Search)
  NOTE: IncidentSearch removed -- data moved to Amazon S3
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

CREATE OR REPLACE AGENT SUPPLY_CHAIN_AGENT
  COMMENT = 'Supply chain intelligence agent combining structured data queries (Cortex Analyst) with unstructured text search (Cortex Search) across supplier communications and warehouse inspections.'
  FROM SPECIFICATION
  $$
  orchestration:
    budget:
      seconds: 60
      tokens: 16000

  instructions:
    system: >
      You are a supply chain intelligence assistant. You help users analyze
      supplier performance, inventory levels, purchase orders, and warehouse
      operations. You combine structured data analysis with unstructured
      text search across supplier emails and warehouse inspection notes.
      Shipments, delivery tracking, store sales, carrier data, and logistics
      incident reports are not available here — freight costs and customer
      returns are in the Amazon S3 knowledge base.
    orchestration: >
      Use Analyst for questions about suppliers, products, inventory levels,
      purchase orders, costs, delays, and delivery rates.
      Use SupplierEmailSearch for questions about supplier communications,
      emails, negotiations, complaints, or correspondence.
      Use InspectionSearch for questions about warehouse inspections,
      facility conditions, compliance, or inspection findings.
      For logistics incidents, safety events, or disruptions, mention that
      this data is available in the Amazon S3 knowledge base.
    response: >
      Provide concise, data-driven answers. When presenting numbers,
      include context and comparisons where possible. If data from
      Amazon S3 (freight costs, customer returns) is needed, mention
      that it is available in the S3 knowledge base.
    sample_questions:
      - question: "Which suppliers have the worst on-time delivery rates?"
        answer: "I'll query the purchase orders data to calculate on-time delivery rates by supplier."
      - question: "What products are at risk of stockout?"
        answer: "I'll analyze current inventory levels against reorder points to identify at-risk items."
      - question: "Show me recent supplier complaints."
        answer: "I'll search supplier emails for recent complaints and quality issues."

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "Analyst"
        description: "Queries structured supply chain data including suppliers, products, warehouses, inventory levels, and purchase orders. Use for quantitative questions about costs, delays, stock levels, and delivery performance."
    - tool_spec:
        type: "cortex_search"
        name: "SupplierEmailSearch"
        description: "Searches supplier email communications for information about negotiations, complaints, updates, and correspondence with suppliers."
    - tool_spec:
        type: "cortex_search"
        name: "InspectionSearch"
        description: "Searches warehouse inspection notes for facility conditions, compliance findings, and maintenance issues."

  tool_resources:
    Analyst:
      semantic_view: "SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_ANALYTICS"
      execution_environment:
        type: "warehouse"
        warehouse: "SUPPLY_CHAIN_WH"
    SupplierEmailSearch:
      name: "SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIER_COMMS_SEARCH"
      max_results: "5"
    InspectionSearch:
      name: "SUPPLY_CHAIN_DEMO.PUBLIC.WAREHOUSE_INSPECTIONS_SEARCH"
      max_results: "5"
  $$;

-- ============================================================
-- Verify
-- ============================================================

SHOW AGENTS IN SUPPLY_CHAIN_DEMO.PUBLIC;
DESCRIBE AGENT SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLY_CHAIN_AGENT;
