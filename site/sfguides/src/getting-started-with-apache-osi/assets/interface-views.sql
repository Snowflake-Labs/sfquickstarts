-- Interface layer: views between the physical TPC-H tables and the semantic model.
-- Views only rename, key and type the data. Business rules stay in the OSI model.
CREATE SCHEMA IF NOT EXISTS OSI_GUIDE.TPCH;

CREATE OR REPLACE VIEW OSI_GUIDE.TPCH.ORDER_LINE COMMENT = 'Interface view: one row per order line' AS
SELECT L_ORDERKEY || '-' || L_LINENUMBER AS order_line_key,   -- single-column surrogate key
       L_ORDERKEY      AS order_key,
       L_LINENUMBER    AS line_number,
       L_PARTKEY       AS part_key,
       L_RETURNFLAG    AS return_flag,
       L_LINESTATUS    AS line_status,
       L_SHIPDATE      AS ship_date,
       L_EXTENDEDPRICE AS extended_price,
       L_DISCOUNT      AS discount
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM;

CREATE OR REPLACE VIEW OSI_GUIDE.TPCH.SALES_ORDER COMMENT = 'Interface view: one row per order' AS
SELECT O_ORDERKEY      AS order_key,
       O_CUSTKEY       AS customer_key,
       O_ORDERDATE     AS order_date,
       O_ORDERPRIORITY AS order_priority,
       O_TOTALPRICE    AS total_price
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS;

CREATE OR REPLACE VIEW OSI_GUIDE.TPCH.CUSTOMER COMMENT = 'Interface view: one row per customer' AS
SELECT C_CUSTKEY    AS customer_key,
       C_NATIONKEY  AS nation_key,
       C_MKTSEGMENT AS market_segment
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER;

CREATE OR REPLACE VIEW OSI_GUIDE.TPCH.NATION COMMENT = 'Interface view: one row per nation' AS
SELECT N_NATIONKEY AS nation_key,
       N_REGIONKEY AS region_key,
       N_NAME      AS nation_name
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION;

CREATE OR REPLACE VIEW OSI_GUIDE.TPCH.REGION COMMENT = 'Interface view: one row per region' AS
SELECT R_REGIONKEY AS region_key,
       R_NAME      AS region_name
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION;

-- The surrogate key must be unique: both counts should be 6,001,215.
SELECT COUNT(*), COUNT(DISTINCT order_line_key) FROM OSI_GUIDE.TPCH.ORDER_LINE;
