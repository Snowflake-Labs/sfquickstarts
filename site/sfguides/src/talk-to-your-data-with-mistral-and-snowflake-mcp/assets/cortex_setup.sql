-- =============================================================================
-- Shipping Logistics Demo — Cortex AI & MCP Setup
-- Target: LOGISTICS_C.SHIPPING_MARTS
--
-- Execution order:
--   1. Cortex Search Service (no dependencies)
--   2. Semantic View (no dependencies)
--   3. Cortex Agent (depends on Search + Semantic View)
--   4. MCP Server (depends on Agent + Search + Semantic View)
-- =============================================================================

USE ROLE ACCOUNTADMIN;
USE DATABASE LOGISTICS_C;
USE SCHEMA SHIPPING_MARTS;
USE WAREHOUSE COMPUTE_WH;

-- =============================================================================
-- 1. CORTEX SEARCH SERVICE
-- =============================================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE SHIPPING_DOCS_SEARCH
  ON CONTENT
  ATTRIBUTES CATEGORY, REGION, PORT_CODE
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  COMMENT = 'Shipping document search — policies, bulletins, SOPs'
AS (
  SELECT
    DOC_ID,
    CATEGORY,
    TITLE,
    CONTENT,
    REGION,
    PORT_CODE,
    EFFECTIVE_DATE,
    TAGS
  FROM LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS
  WHERE EXPIRY_DATE IS NULL OR EXPIRY_DATE >= CURRENT_DATE()
);

-- =============================================================================
-- 2. SEMANTIC VIEW
-- =============================================================================

CREATE OR REPLACE SEMANTIC VIEW SHIPMENT_ANALYTICS_SV

  TABLES (
    shipments AS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENTS
      PRIMARY KEY (SHIPMENT_ID)
      WITH SYNONYMS ('shipments', 'bookings', 'cargo')
      COMMENT = 'Core shipment fact table with booking, departure, arrival, and freight data',
    events AS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_EVENTS
      PRIMARY KEY (EVENT_ID)
      WITH SYNONYMS ('shipment events', 'tracking events')
      COMMENT = 'Shipment lifecycle events',
    performance AS LOGISTICS_C.SHIPPING_MARTS.FACT_SHIPMENT_PERFORMANCE
      PRIMARY KEY (SHIPMENT_ID)
      WITH SYNONYMS ('delivery performance', 'on-time performance')
      COMMENT = 'Shipment performance metrics',
    customers AS LOGISTICS_C.SHIPPING_MARTS.DIM_CUSTOMERS
      PRIMARY KEY (CUSTOMER_ID)
      WITH SYNONYMS ('clients', 'shippers')
      COMMENT = 'Customer master data',
    vessels AS LOGISTICS_C.SHIPPING_MARTS.DIM_VESSELS
      PRIMARY KEY (VESSEL_ID)
      WITH SYNONYMS ('ships', 'container vessels')
      COMMENT = 'Vessel fleet data',
    ports AS LOGISTICS_C.SHIPPING_MARTS.DIM_PORTS
      PRIMARY KEY (PORT_CODE)
      WITH SYNONYMS ('terminals', 'harbors')
      COMMENT = 'Port reference data',
    routes AS LOGISTICS_C.SHIPPING_MARTS.DIM_ROUTES
      PRIMARY KEY (ROUTE_ID)
      WITH SYNONYMS ('trade lanes', 'shipping lanes')
      COMMENT = 'Shipping route definitions'
  )

  RELATIONSHIPS (
    shipments_to_customers AS shipments (CUSTOMER_ID) REFERENCES customers,
    shipments_to_routes AS shipments (ROUTE_ID) REFERENCES routes,
    shipments_to_vessels AS shipments (VESSEL_ID) REFERENCES vessels,
    performance_to_shipments AS performance (SHIPMENT_ID) REFERENCES shipments,
    events_to_shipments AS events (SHIPMENT_ID) REFERENCES shipments,
    events_to_ports AS events (PORT_CODE) REFERENCES ports,
    routes_to_origin_port AS routes (ORIGIN_PORT_CODE) REFERENCES ports (PORT_CODE),
    routes_to_dest_port AS routes (DESTINATION_PORT_CODE) REFERENCES ports (PORT_CODE)
  )

  FACTS (
    shipments.container_count_fact AS CONTAINER_COUNT COMMENT = 'Number of containers',
    shipments.weight_fact AS TOTAL_WEIGHT_KG COMMENT = 'Total cargo weight in kg',
    shipments.freight_fact AS FREIGHT_CHARGE_USD COMMENT = 'Freight charge in USD',
    performance.delay_days_fact AS DELAY_DAYS COMMENT = 'Delay days (0 if on time)'
  )

  DIMENSIONS (
    shipments.shipment_id_dim AS SHIPMENT_ID WITH SYNONYMS = ('shipment number', 'booking number') COMMENT = 'Unique shipment identifier',
    shipments.shipment_status AS SHIPMENT_STATUS WITH SYNONYMS = ('status') COMMENT = 'BOOKED, IN_TRANSIT, DELAYED, or DELIVERED',
    shipments.container_type AS CONTAINER_TYPE COMMENT = '20GP, 40GP, 40HC, or REEFER',
    shipments.cargo_type AS CARGO_TYPE COMMENT = 'General, Perishable, Hazardous, or Automotive',
    shipments.booking_date_dim AS BOOKING_DATE WITH SYNONYMS = ('booked date') COMMENT = 'Booking date',
    shipments.booking_month AS MONTH(BOOKING_DATE) COMMENT = 'Booking month',
    shipments.booking_year AS YEAR(BOOKING_DATE) COMMENT = 'Booking year',
    shipments.planned_departure_dim AS PLANNED_DEPARTURE COMMENT = 'Scheduled departure',
    shipments.planned_arrival_dim AS PLANNED_ARRIVAL COMMENT = 'Scheduled arrival',
    shipments.actual_departure_dim AS ACTUAL_DEPARTURE COMMENT = 'Actual departure',
    shipments.actual_arrival_dim AS ACTUAL_ARRIVAL COMMENT = 'Actual arrival',
    customers.customer_name_dim AS CUSTOMER_NAME WITH SYNONYMS = ('client name') COMMENT = 'Customer company name',
    customers.industry_dim AS INDUSTRY COMMENT = 'Customer industry vertical',
    customers.contract_tier_dim AS CONTRACT_TIER WITH SYNONYMS = ('tier', 'SLA tier') COMMENT = 'Gold, Silver, Bronze, or Standard',
    customers.customer_country_dim AS COUNTRY COMMENT = 'Customer HQ country',
    vessels.vessel_name_dim AS VESSEL_NAME WITH SYNONYMS = ('ship name') COMMENT = 'Vessel name',
    vessels.vessel_type_dim AS VESSEL_TYPE COMMENT = 'Container, RoRo, or Bulk',
    vessels.capacity_teu_dim AS CAPACITY_TEU COMMENT = 'Vessel TEU capacity',
    ports.port_name_dim AS PORT_NAME WITH SYNONYMS = ('harbor', 'terminal') COMMENT = 'Port full name',
    ports.port_country_dim AS ports.COUNTRY COMMENT = 'Port country',
    ports.port_region_dim AS ports.REGION WITH SYNONYMS = ('geographic region') COMMENT = 'Mediterranean, North Europe, or Eastern Mediterranean',
    routes.route_name_dim AS ROUTE_NAME COMMENT = 'Origin to destination route',
    routes.trade_lane_dim AS TRADE_LANE COMMENT = 'Trade lane classification',
    routes.standard_transit_days_dim AS STANDARD_TRANSIT_DAYS COMMENT = 'Standard transit days for the route',
    performance.delay_reason_dim AS DELAY_REASON WITH SYNONYMS = ('cause of delay') COMMENT = 'PORT_CONGESTION, WEATHER, CUSTOMS, MECHANICAL, or NONE',
    performance.on_time_flag_dim AS ON_TIME_FLAG WITH SYNONYMS = ('on time', 'punctual') COMMENT = 'TRUE if delivered on time',
    events.event_type_dim AS EVENT_TYPE WITH SYNONYMS = ('tracking event') COMMENT = 'DEPARTURE, ARRIVAL, TRANSSHIPMENT, etc.',
    events.event_timestamp_dim AS EVENT_TIMESTAMP COMMENT = 'Event timestamp',
    events.remarks_dim AS REMARKS COMMENT = 'Event description'
  )

  METRICS (
    shipments.total_shipments AS COUNT(SHIPMENT_ID) WITH SYNONYMS = ('shipment count') COMMENT = 'Total shipment count',
    shipments.total_containers AS SUM(shipments.container_count_fact) WITH SYNONYMS = ('container volume') COMMENT = 'Total containers',
    shipments.total_freight_revenue AS SUM(shipments.freight_fact) WITH SYNONYMS = ('revenue', 'freight revenue') COMMENT = 'Total freight revenue USD',
    shipments.avg_freight_per_shipment AS AVG(shipments.freight_fact) COMMENT = 'Average freight per shipment',
    shipments.total_weight AS SUM(shipments.weight_fact) COMMENT = 'Total cargo weight kg',
    performance.avg_transit_time AS AVG(ACTUAL_TRANSIT_DAYS) WITH SYNONYMS = ('average transit') COMMENT = 'Average transit time in days',
    performance.avg_delay AS AVG(performance.delay_days_fact) WITH SYNONYMS = ('average delay') COMMENT = 'Average delay days',
    performance.on_time_rate AS AVG(IFF(ON_TIME_FLAG, 1, 0)) WITH SYNONYMS = ('OTD rate', 'on-time rate') COMMENT = 'On-time delivery rate (0 to 1)',
    performance.delayed_shipment_count AS COUNT_IF(ON_TIME_FLAG = FALSE) WITH SYNONYMS = ('late shipments') COMMENT = 'Count of late shipments',
    events.total_events AS COUNT(EVENT_ID) COMMENT = 'Total shipment events'
  )

  COMMENT = 'Europe-Mediterranean shipment analytics'

  AI_SQL_GENERATION 'When generating SQL: 1. Round numeric results to 2 decimal places. 2. For on-time rate, multiply by 100 to show as percentage. 3. Default to BOOKING_DATE for date filtering. 4. If no date range specified, default to last 3 months. 5. Use SHIPMENT_STATUS to filter active vs completed shipments.'

  AI_QUESTION_CATEGORIZATION 'This covers shipping in Europe-Mediterranean from Dec 2025 to May 2026. Reject questions about HR, finance beyond freight, or topics unrelated to shipping.';

-- =============================================================================
-- 3. CORTEX AGENT
-- =============================================================================

CREATE OR REPLACE AGENT SHIPPING_LOGISTICS_AGENT
  COMMENT = 'Shipping logistics conversational agent for Europe-Mediterranean trade'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto

  orchestration:
    budget:
      seconds: 60
      tokens: 16000

  instructions:
    response: >
      You are a shipping logistics assistant specializing in
      Europe-Mediterranean trade lanes. You help users with shipment tracking,
      supply chain analytics, and shipping policy questions. Be specific with
      port names, route details, and dates. Use professional maritime terminology.
      When presenting data, format numbers clearly and include relevant context.
    orchestration: >
      For questions about shipment data, tracking, performance metrics, transit times,
      delays, revenue, or volumes, use the ShipmentAnalytics tool to query structured data.
      For questions about shipping policies, demurrage rules, customs procedures,
      trade lane bulletins, SOPs, or operational guidelines, use the ShippingDocsSearch tool.
      When a question requires both data and policy context (e.g. "my shipment is delayed,
      what are my options?"), use both tools — first get the shipment data, then look up
      relevant policies.
    sample_questions:
      - question: "Where is shipment SH-00042?"
      - question: "What is the on-time delivery rate for Q1 2026?"
      - question: "What is the demurrage policy for reefer containers in Marseille?"
      - question: "Which routes have the highest average delay?"
      - question: "My shipment is delayed. What are my options?"

  tools:
    - tool_spec:
        type: "cortex_analyst_text_to_sql"
        name: "ShipmentAnalytics"
        description: >
          Converts natural language questions into SQL queries over shipment data.
          Use for: shipment tracking, status lookups, transit time analysis, on-time rates,
          delay analysis, freight revenue, container volumes, customer analytics, route
          performance, vessel utilization, and port activity. Covers Europe-Mediterranean
          trade lanes from December 2025 to May 2026.
    - tool_spec:
        type: "cortex_search"
        name: "ShippingDocsSearch"
        description: >
          Searches shipping documentation including demurrage and detention policies,
          trade lane bulletins (congestion alerts, weather advisories, schedule changes),
          customs and regulatory updates, and standard operating procedures (container loading,
          hazmat handling, customs clearance, reefer inspection). Use for policy lookups,
          compliance questions, and operational guidelines.

  tool_resources:
    ShipmentAnalytics:
      semantic_view: "LOGISTICS_C.SHIPPING_MARTS.SHIPMENT_ANALYTICS_SV"
      execution_environment:
        type: "warehouse"
        warehouse: "COMPUTE_WH"
    ShippingDocsSearch:
      name: "LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS_SEARCH"
      max_results: "5"
      title_column: "TITLE"
      id_column: "DOC_ID"
  $$;

-- =============================================================================
-- 4. MCP SERVER
-- =============================================================================

CREATE OR REPLACE MCP SERVER SHIPPING_MCP_SERVER
  FROM SPECIFICATION $$
  tools:
    - name: "shipping-logistics-agent"
      type: "CORTEX_AGENT_RUN"
      identifier: "LOGISTICS_C.SHIPPING_MARTS.SHIPPING_LOGISTICS_AGENT"
      description: >
        Shipping logistics agent. Handles shipment tracking,
        supply chain analytics, and shipping policy questions for
        Europe-Mediterranean trade lanes. This is the primary tool —
        it internally routes between structured data queries and
        document search.
      title: "Shipping Logistics Agent"

    - name: "shipment-analytics"
      type: "CORTEX_ANALYST_MESSAGE"
      identifier: "LOGISTICS_C.SHIPPING_MARTS.SHIPMENT_ANALYTICS_SV"
      description: >
        Direct text-to-SQL analytics over shipment data.
        Use for specific data queries about shipments, transit times,
        delays, revenue, and volumes. Fallback tool if the agent
        does not route correctly.
      title: "Shipment Analytics"

    - name: "shipping-docs-search"
      type: "CORTEX_SEARCH_SERVICE_QUERY"
      identifier: "LOGISTICS_C.SHIPPING_MARTS.SHIPPING_DOCS_SEARCH"
      description: >
        Search shipping policies, trade lane bulletins, and SOPs.
        Use for questions about demurrage, customs procedures, port
        advisories, and operational guidelines. Fallback tool if the
        agent does not route correctly.
      title: "Shipping Document Search"
  $$;

-- =============================================================================
-- Validation
-- =============================================================================

SHOW CORTEX SEARCH SERVICES IN SCHEMA LOGISTICS_C.SHIPPING_MARTS;
SHOW SEMANTIC VIEWS IN SCHEMA LOGISTICS_C.SHIPPING_MARTS;
SHOW AGENTS IN SCHEMA LOGISTICS_C.SHIPPING_MARTS;
SHOW MCP SERVERS IN SCHEMA LOGISTICS_C.SHIPPING_MARTS;
DESCRIBE MCP SERVER LOGISTICS_C.SHIPPING_MARTS.SHIPPING_MCP_SERVER;
