
WITH CUSTOMERS AS (
    SELECT * FROM VALUES
        (1, 'John Doe', 'john@example.com'),
        (2, 'Jane Smith', 'jane@example.com')
    AS T(customer_id, customer_name, email)
),
ORDERS AS (
    SELECT * FROM VALUES
        (101, 1, 250.00),
        (102, 1, 100.00),
        (103, 2, 300.00)
    AS T(order_id, customer_id, order_amount)
),
EXPECTED_DATA AS (
    SELECT
        1 AS customer_id,
        'John Doe' AS customer_name,
        2 AS total_orders,
        350.00 AS total_spent
    UNION ALL
    SELECT
        2 AS customer_id,
        'Jane Smith' AS customer_name,
        1 AS total_orders,
        300.00 AS total_spent
)
SELECT * FROM ${MY_DB}.${MY_SCHEMA}.CUSTOMER_SUMMARY;
