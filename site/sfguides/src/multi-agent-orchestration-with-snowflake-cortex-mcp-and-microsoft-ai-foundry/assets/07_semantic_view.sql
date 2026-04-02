/*=============================================================
  07 — Create Semantic View
  SUPPLY_CHAIN_ANALYTICS — powers Cortex Analyst text-to-SQL
  5 tables, 5 relationships, facts, dimensions,
  9 metrics, 5 filters, 3 verified queries
  Uses YAML approach via SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML
  NOTE: SHIPMENTS and STORE_SALES excluded — supplementary data in Amazon S3
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  'SUPPLY_CHAIN_DEMO.PUBLIC',
  $$
name: SUPPLY_CHAIN_ANALYTICS
description: >
  Supply chain analytics semantic view for Cortex Analyst.
  Covers suppliers, products, warehouses, inventory, and purchase orders.
  Freight costs and customer returns data is in Amazon S3.

tables:
  # ── 1. SUPPLIERS ──
  - name: SUPPLIERS
    description: Supplier master data including contact info, reliability scores, and contract details
    base_table:
      database: SUPPLY_CHAIN_DEMO
      schema: PUBLIC
      table: SUPPLIERS
    primary_key:
      columns:
        - SUPPLIER_ID
    facts:
      - name: LEAD_TIME_DAYS
        description: Average lead time in days for this supplier
        expr: LEAD_TIME_DAYS
        data_type: NUMBER
      - name: RELIABILITY_SCORE
        description: "Supplier reliability score from 0 to 1. Below 0.7 is considered low reliability."
        expr: RELIABILITY_SCORE
        data_type: NUMBER
    dimensions:
      - name: SUPPLIER_ID
        expr: SUPPLIER_ID
        data_type: NUMBER
      - name: SUPPLIER_NAME
        description: Name of the supplier
        expr: SUPPLIER_NAME
        data_type: VARCHAR
      - name: CONTACT_NAME
        description: Primary contact person at the supplier
        expr: CONTACT_NAME
        data_type: VARCHAR
      - name: COUNTRY
        description: Country where the supplier is located
        expr: COUNTRY
        data_type: VARCHAR
      - name: REGION
        description: Geographic region of the supplier
        expr: REGION
        data_type: VARCHAR
      - name: PAYMENT_TERMS
        description: Payment terms agreed with the supplier
        expr: PAYMENT_TERMS
        data_type: VARCHAR
    time_dimensions:
      - name: CONTRACT_START
        description: Contract start date
        expr: CONTRACT_START
        data_type: DATE
      - name: CONTRACT_END
        description: Contract end date
        expr: CONTRACT_END
        data_type: DATE
    metrics:
      - name: AVG_RELIABILITY_SCORE
        description: Average supplier reliability score
        expr: AVG(RELIABILITY_SCORE)
      - name: AVG_LEAD_TIME
        description: Average supplier lead time in days
        expr: AVG(LEAD_TIME_DAYS)
    filters:
      - name: LOW_RELIABILITY_SUPPLIERS
        description: Suppliers with reliability score below 0.7
        expr: "RELIABILITY_SCORE < 0.7"

  # ── 2. PRODUCTS ──
  - name: PRODUCTS
    description: Product catalog with pricing, weight, and perishability info
    base_table:
      database: SUPPLY_CHAIN_DEMO
      schema: PUBLIC
      table: PRODUCTS
    primary_key:
      columns:
        - PRODUCT_ID
    facts:
      - name: UNIT_COST
        description: Cost per unit from supplier
        expr: UNIT_COST
        data_type: NUMBER
      - name: UNIT_PRICE
        description: Selling price per unit
        expr: UNIT_PRICE
        data_type: NUMBER
      - name: WEIGHT_KG
        description: Product weight in kilograms
        expr: WEIGHT_KG
        data_type: NUMBER
      - name: REORDER_POINT
        description: Minimum stock level that triggers a reorder
        expr: REORDER_POINT
        data_type: NUMBER
      - name: REORDER_QTY
        description: Quantity to order when stock hits reorder point
        expr: REORDER_QTY
        data_type: NUMBER
    dimensions:
      - name: PRODUCT_ID
        expr: PRODUCT_ID
        data_type: NUMBER
      - name: PRODUCT_NAME
        description: Name of the product
        expr: PRODUCT_NAME
        data_type: VARCHAR
      - name: CATEGORY
        synonyms:
          - product category
        description: "Product category: Raw Materials, Components, Food & Beverage, Electronics, Packaging, Equipment, Safety Supplies, Maintenance"
        expr: CATEGORY
        data_type: VARCHAR
      - name: SUBCATEGORY
        description: Product subcategory
        expr: SUBCATEGORY
        data_type: VARCHAR
      - name: SUPPLIER_ID
        expr: SUPPLIER_ID
        data_type: NUMBER
      - name: IS_PERISHABLE
        description: TRUE if the product is perishable and has a shelf life
        expr: IS_PERISHABLE
        data_type: BOOLEAN
    filters:
      - name: PERISHABLE_PRODUCTS
        description: Only perishable products
        expr: "IS_PERISHABLE = TRUE"

  # ── 3. WAREHOUSES ──
  - name: WAREHOUSES
    description: Warehouse locations with capacity info
    base_table:
      database: SUPPLY_CHAIN_DEMO
      schema: PUBLIC
      table: WAREHOUSES
    primary_key:
      columns:
        - WAREHOUSE_ID
    facts:
      - name: CAPACITY_SQFT
        description: Total warehouse capacity in square feet
        expr: CAPACITY_SQFT
        data_type: NUMBER
    dimensions:
      - name: WAREHOUSE_ID
        expr: WAREHOUSE_ID
        data_type: NUMBER
      - name: WAREHOUSE_NAME
        description: Name of the warehouse
        expr: WAREHOUSE_NAME
        data_type: VARCHAR
      - name: CITY
        description: City where the warehouse is located
        expr: CITY
        data_type: VARCHAR
      - name: STATE_PROVINCE
        description: State or province where the warehouse is located
        expr: STATE_PROVINCE
        data_type: VARCHAR
      - name: COUNTRY
        description: Country where the warehouse is located
        expr: COUNTRY
        data_type: VARCHAR
      - name: WAREHOUSE_TYPE
        description: Type of warehouse
        expr: WAREHOUSE_TYPE
        data_type: VARCHAR

  # ── 4. INVENTORY ──
  - name: INVENTORY
    description: Current inventory levels per product per warehouse
    base_table:
      database: SUPPLY_CHAIN_DEMO
      schema: PUBLIC
      table: INVENTORY
    primary_key:
      columns:
        - INVENTORY_ID
    facts:
      - name: QUANTITY_ON_HAND
        description: Current stock quantity available
        expr: QUANTITY_ON_HAND
        data_type: NUMBER
      - name: QUANTITY_RESERVED
        description: Quantity reserved for pending orders
        expr: QUANTITY_RESERVED
        data_type: NUMBER
      - name: QUANTITY_AVAILABLE
        description: Quantity available for new orders
        expr: QUANTITY_AVAILABLE
        data_type: NUMBER
      - name: DAYS_OF_SUPPLY
        description: "Estimated number of days the current stock will last. Below 5 is critical."
        expr: DAYS_OF_SUPPLY
        data_type: NUMBER
    dimensions:
      - name: INVENTORY_ID
        expr: INVENTORY_ID
        data_type: NUMBER
      - name: PRODUCT_ID
        expr: PRODUCT_ID
        data_type: NUMBER
      - name: WAREHOUSE_ID
        expr: WAREHOUSE_ID
        data_type: NUMBER
    time_dimensions:
      - name: LAST_RESTOCK_DATE
        description: Date of the last restock
        expr: LAST_RESTOCK_DATE
        data_type: DATE
    metrics:
      - name: TOTAL_STOCK_ON_HAND
        description: Total inventory quantity across all warehouses
        expr: SUM(QUANTITY_ON_HAND)
      - name: AVG_DAYS_OF_SUPPLY
        description: Average days of supply across all inventory records
        expr: AVG(DAYS_OF_SUPPLY)
      - name: CRITICAL_STOCK_ITEMS
        description: Count of inventory records with 5 or fewer days of supply remaining
        expr: SUM(CASE WHEN DAYS_OF_SUPPLY <= 5 THEN 1 ELSE 0 END)
    filters:
      - name: CRITICAL_STOCK
        description: Inventory items with 5 or fewer days of supply remaining
        expr: "DAYS_OF_SUPPLY <= 5"

  # ── 5. PURCHASE_ORDERS ──
  - name: PURCHASE_ORDERS
    description: Purchase order records with delivery tracking and cost details
    base_table:
      database: SUPPLY_CHAIN_DEMO
      schema: PUBLIC
      table: PURCHASE_ORDERS
    primary_key:
      columns:
        - PO_ID
    facts:
      - name: QUANTITY_ORDERED
        description: Number of units ordered
        expr: QUANTITY_ORDERED
        data_type: NUMBER
      - name: PO_UNIT_COST
        description: Cost per unit on this purchase order
        expr: UNIT_COST
        data_type: NUMBER
      - name: TOTAL_COST
        description: Total purchase order cost (quantity_ordered * unit_cost)
        expr: TOTAL_COST
        data_type: NUMBER
      - name: DELAY_DAYS
        description: "Number of days the delivery was delayed beyond expected date. 0 means on time."
        expr: DELAY_DAYS
        data_type: NUMBER
    dimensions:
      - name: PO_ID
        expr: PO_ID
        data_type: NUMBER
      - name: SUPPLIER_ID
        expr: SUPPLIER_ID
        data_type: NUMBER
      - name: PRODUCT_ID
        expr: PRODUCT_ID
        data_type: NUMBER
      - name: PO_STATUS
        synonyms:
          - order status
          - status
        description: "Order status: Ordered, In Transit, Delivered, Delayed"
        expr: STATUS
        data_type: VARCHAR
    time_dimensions:
      - name: ORDER_DATE
        description: Date the purchase order was placed
        expr: ORDER_DATE
        data_type: DATE
      - name: EXPECTED_DELIVERY_DATE
        description: Expected delivery date
        expr: EXPECTED_DELIVERY_DATE
        data_type: DATE
      - name: ACTUAL_DELIVERY_DATE
        description: Actual delivery date
        expr: ACTUAL_DELIVERY_DATE
        data_type: DATE
    metrics:
      - name: TOTAL_PO_VALUE
        description: Total value of all purchase orders
        expr: SUM(TOTAL_COST)
      - name: AVG_DELAY_DAYS
        description: Average number of days orders are delayed
        expr: AVG(DELAY_DAYS)
      - name: TOTAL_ORDERS
        description: Total number of purchase orders
        expr: COUNT(PO_ID)
      - name: ON_TIME_DELIVERY_RATE
        description: Percentage of purchase orders delivered on time (0 delay days)
        expr: "SUM(CASE WHEN DELAY_DAYS = 0 THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(PO_ID), 0)"
    filters:
      - name: DELIVERED_ORDERS
        description: Only delivered purchase orders
        expr: "STATUS = 'Delivered'"
      - name: DELAYED_ORDERS
        description: Purchase orders that were delivered late
        expr: "DELAY_DAYS > 0"

# ── RELATIONSHIPS ──
relationships:
  - name: PRODUCTS_TO_SUPPLIERS
    left_table: PRODUCTS
    right_table: SUPPLIERS
    relationship_columns:
      - left_column: SUPPLIER_ID
        right_column: SUPPLIER_ID
    relationship_type: many_to_one
  - name: INVENTORY_TO_PRODUCTS
    left_table: INVENTORY
    right_table: PRODUCTS
    relationship_columns:
      - left_column: PRODUCT_ID
        right_column: PRODUCT_ID
    relationship_type: many_to_one
  - name: INVENTORY_TO_WAREHOUSES
    left_table: INVENTORY
    right_table: WAREHOUSES
    relationship_columns:
      - left_column: WAREHOUSE_ID
        right_column: WAREHOUSE_ID
    relationship_type: many_to_one
  - name: PO_TO_SUPPLIERS
    left_table: PURCHASE_ORDERS
    right_table: SUPPLIERS
    relationship_columns:
      - left_column: SUPPLIER_ID
        right_column: SUPPLIER_ID
    relationship_type: many_to_one
  - name: PO_TO_PRODUCTS
    left_table: PURCHASE_ORDERS
    right_table: PRODUCTS
    relationship_columns:
      - left_column: PRODUCT_ID
        right_column: PRODUCT_ID
    relationship_type: many_to_one

# ── VERIFIED QUERIES ──
verified_queries:
  - name: SUPPLIERS_WITH_DELIVERY_DELAYS
    question: "Which suppliers are causing the most delivery delays?"
    sql: |
      SELECT s.SUPPLIER_NAME, s.RELIABILITY_SCORE,
             COUNT(po.PO_ID) AS total_orders,
             SUM(CASE WHEN po.DELAY_DAYS > 0 THEN 1 ELSE 0 END) AS delayed_orders,
             ROUND(AVG(po.DELAY_DAYS), 1) AS avg_delay_days,
             ROUND(AVG(CASE WHEN po.DELAY_DAYS > 0 THEN po.DELAY_DAYS END), 1) AS avg_delay_when_late
      FROM SUPPLY_CHAIN_DEMO.PUBLIC.PURCHASE_ORDERS po
      JOIN SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIERS s ON po.SUPPLIER_ID = s.SUPPLIER_ID
      GROUP BY s.SUPPLIER_NAME, s.RELIABILITY_SCORE
      HAVING SUM(CASE WHEN po.DELAY_DAYS > 0 THEN 1 ELSE 0 END) > 0
      ORDER BY avg_delay_days DESC
    verified_at: 1741500000
    verified_by: bsuresh
    use_as_onboarding_question: true

  - name: PRODUCTS_AT_RISK_OF_STOCKOUT
    question: "What products are at risk of stockouts?"
    sql: |
      SELECT p.PRODUCT_NAME, p.CATEGORY, w.WAREHOUSE_NAME, w.CITY,
             i.QUANTITY_ON_HAND, p.REORDER_POINT, i.DAYS_OF_SUPPLY,
             CASE WHEN i.DAYS_OF_SUPPLY <= 3 THEN 'Critical'
                  WHEN i.DAYS_OF_SUPPLY <= 5 THEN 'Low'
                  ELSE 'Adequate' END AS stock_status
      FROM SUPPLY_CHAIN_DEMO.PUBLIC.INVENTORY i
      JOIN SUPPLY_CHAIN_DEMO.PUBLIC.PRODUCTS p ON i.PRODUCT_ID = p.PRODUCT_ID
      JOIN SUPPLY_CHAIN_DEMO.PUBLIC.WAREHOUSES w ON i.WAREHOUSE_ID = w.WAREHOUSE_ID
      WHERE i.QUANTITY_ON_HAND <= p.REORDER_POINT
      ORDER BY i.DAYS_OF_SUPPLY ASC
    verified_at: 1741500000
    verified_by: bsuresh
    use_as_onboarding_question: true

  - name: ON_TIME_DELIVERY_RATE_BY_SUPPLIER
    question: "What is the on-time delivery rate by supplier?"
    sql: |
      SELECT s.SUPPLIER_NAME, s.COUNTRY, s.RELIABILITY_SCORE,
             COUNT(po.PO_ID) AS total_orders,
             SUM(CASE WHEN po.DELAY_DAYS = 0 THEN 1 ELSE 0 END) AS on_time_orders,
             ROUND(SUM(CASE WHEN po.DELAY_DAYS = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(po.PO_ID), 1) AS otd_rate_pct
      FROM SUPPLY_CHAIN_DEMO.PUBLIC.PURCHASE_ORDERS po
      JOIN SUPPLY_CHAIN_DEMO.PUBLIC.SUPPLIERS s ON po.SUPPLIER_ID = s.SUPPLIER_ID
      WHERE po.STATUS = 'Delivered'
      GROUP BY s.SUPPLIER_NAME, s.COUNTRY, s.RELIABILITY_SCORE
      ORDER BY otd_rate_pct ASC
    verified_at: 1741500000
    verified_by: bsuresh
    use_as_onboarding_question: true
  $$
);
