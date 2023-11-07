------------------------------------------------------------------------
----- Create Kay Co tables.
------------------------------------------------------------------------
CREATE OR REPLACE DATABASE kayak_co_db;
CREATE SCHEMA kayak_co_schema;
-- |-----------|--------------------------------------------------------
-- | Table     | Columns
-- |-----------|--------------------------------------------------------
-- | customers | customer_id, name, email, phone_num, ship_address, ship_city, ship_state, ship_zipcode
-- | products  | product_sku, product_type, price
-- | purchases | purchases_id, customer_id, product_sku, date
-- |-----------|--------------------------------------------------------

CREATE OR REPLACE TABLE customers (
  customer_id STRING PRIMARY KEY,
  name STRING,
  email STRING,
  ship_zipcode STRING
);
  
CREATE OR REPLACE TABLE products (
  product_sku STRING PRIMARY KEY,
  product_name STRING,
  product_type STRING,
  price DOUBLE);


CREATE OR REPLACE TABLE purchases (
  purchases_id STRING PRIMARY KEY,
  customer_id STRING FOREIGN KEY REFERENCES customers(customer_id),
  product_sku STRING FOREIGN KEY REFERENCES products(product_sku),
  date DATE);

GRANT SELECT ON TABLE CUSTOMERS TO ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE PRODUCTS TO ROLE ACCOUNTADMIN;
GRANT SELECT ON TABLE PURCHASES TO ROLE ACCOUNTADMIN;

USE DATABASE kayak_co_db;
USE SCHEMA kayak_co_schema;

CREATE OR REPLACE PROCEDURE generate_KC_data(
    GROUP_PREFIX STRING,
    USER_COUNT DOUBLE,
    PRODUCTS_COUNT DOUBLE,
    GENERATE_PURCHASE_PROB DOUBLE
) 
  RETURNS STRING
  LANGUAGE JAVASCRIPT
  EXECUTE AS caller
AS $$
let user_num = 0;
purchase_cmd = `INSERT INTO purchases VALUES `;
user_cmd = `INSERT INTO customers VALUES `;
is_first_purchase = true;
is_first_user = true;

while (user_num < USER_COUNT) {
    let user_id = `KAY_${GROUP_PREFIX}${user_num}`;
    let email = `email_${GROUP_PREFIX}${user_num}@mail.com`;
    user_num = user_num + 1;
    let zipcode = `9404${user_num % 9}`;
    if(!is_first_user) {
      user_cmd += ', '
    }
    is_first_user = false;
    user_cmd += `('${user_id}', 'Name ${user_id}', '${email}', '${zipcode}')`;

    // Adding PURCHASE data
    if (GENERATE_PURCHASE_PROB > Math.random()) {
        let purchases_id = `sell_${GROUP_PREFIX}${Math.floor(Math.random()*2000)}`;
        let p_id = `p_${Math.floor(Math.random()*PRODUCTS_COUNT)}`;
        if(!is_first_purchase) {
          purchase_cmd += ', '
        }
        is_first_purchase = false;
        purchase_cmd += `('${purchases_id}', '${user_id}', '${p_id}', DATE('2013-05-17'))`;
    }
}
purchase_cmd += ';'
user_cmd += ';'
if (!is_first_user) {
  snowflake.execute({sqlText: user_cmd});
}
if (!is_first_purchase) {
  snowflake.execute({sqlText: purchase_cmd});
}
return "Created stuff successfully"
$$;


------------------------------------------------------------------------
----------------------------- Data Generation --------------------------
------------------------------------------------------------------------


------------------------------------------------------------------------
----- Generate data for Kay Co.
------------------------------------------------------------------------
USE DATABASE kayak_co_db;
USE SCHEMA kayak_co_schema;
INSERT INTO products VALUES ('p_0', 'Kayak - single', 'Kayak', 1499.99);
INSERT INTO products VALUES ('p_1', 'Kayak - duble', 'Kayak', 1499.99);
INSERT INTO products VALUES ('p_2', 'Kayak - duble', 'Kayak', 1875.99);
INSERT INTO products VALUES ('p_3', 'Launch Dock', 'Other', 2479.99);
INSERT INTO products VALUES ('p_4', 'Universal Carrier', 'Other', 39.99);
INSERT INTO products VALUES ('p_5', 'Signaling whistle.', 'Other', 2.99);
INSERT INTO products VALUES ('p_6', 'Headlamp/light with extra batteries ', 'Other', 12.99);
INSERT INTO products VALUES ('p_7', 'Headlamp/light', 'Other', 10.99);
INSERT INTO products VALUES ('p_8', 'Paddle - single - M ', 'Paddle', 54.99);
INSERT INTO products VALUES ('p_9', 'Paddle - single - L', 'Paddle', 55.99);
INSERT INTO products VALUES ('p_10', 'Paddle - single - XL', 'Paddle', 545.99);
INSERT INTO products VALUES ('p_11', 'Paddle - single - XL', 'Paddle', 545.99);

CALL generate_KC_data(1, 1167, 5, 0.01);
CALL generate_KC_data(2, 1141, 8, 0.02);
CALL generate_KC_data(4, 1258, 12, 0.05);
CALL generate_KC_data(5, 1182, 12, 0.06);
CALL generate_KC_data(7, 581, 12, 0.04);
CALL generate_KC_data(8, 1102, 12, 0.07);

CALL generate_KC_data(3, 5384, 12, 0.09);
CALL generate_KC_data(6, 8213, 12, 0.14);
CALL generate_KC_data(9, 4355, 12, 0.13);

CALL generate_KC_data(11, 117, 5, 0.01);
CALL generate_KC_data(12, 141, 8, 0.02);
CALL generate_KC_data(14, 125, 12, 0.05);
CALL generate_KC_data(15, 182, 12, 0.06);
CALL generate_KC_data(17, 81, 12, 0.04);
CALL generate_KC_data(18, 112, 12, 0.07);

CALL generate_KC_data(13, 534, 12, 0.09);
CALL generate_KC_data(16, 213, 12, 0.14);
CALL generate_KC_data(19, 455, 12, 0.13);

-- Users that are only in KayCo
CALL generate_KC_data(201, 6012, 12, 0.09);
CALL generate_KC_data(202, 5012, 5, 0.19);
CALL generate_KC_data(203, 16012, 5, 0.01);

-- Add a little bit of overlap with individuals in bigPaddle
CALL generate_KC_data(301, 140, 12, 0.09);

-- Remove douplicates
DELETE FROM CUSTOMERS 
WHERE customer_id IN (
    SELECT customer_id FROM CUSTOMERS
    GROUP BY ALL
    HAVING count(*) > 1
);

SELECT COUNT(*) FROM CUSTOMERS;
SELECT * FROM CUSTOMERS SAMPLE(5 ROWS);
SELECT * FROM PRODUCTS SAMPLE(5 ROWS);
SELECT * FROM PURCHASES SAMPLE(5 ROWS);
