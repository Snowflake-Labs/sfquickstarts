---version: 0, author: admin
CREATE TABLE IF NOT EXISTS ${MY_DB}.${MY_SCHEMA}.ORDERS (
    order_id INT,
    customer_id INT,
    order_amount NUMBER(10,2),
    order_date DATE
);
---rollback: DROP TABLE IF EXISTS ${MY_DB}.${MY_SCHEMA}.ORDERS;
