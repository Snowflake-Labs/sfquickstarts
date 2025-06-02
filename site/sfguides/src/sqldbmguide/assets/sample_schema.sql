-- **************************************  PII
CREATE TAG PII ALLOWED_VALUES 'NO', 'YES';

-- **************************************  RETENTION_PERIOD
CREATE TAG RETENTION_PERIOD ALLOWED_VALUES '7 YEARS';

-- ************************************** dim_store
CREATE TABLE dim_store
(
 store_id    string NOT NULL COMMENT 'Unique store identifier (primary key).',
 store_name  string COMMENT 'Name of the store.',
 store_type  string COMMENT 'Store type (e.g., Physical, Online).',
 address     string COMMENT 'Store address.',
 city        string COMMENT 'City where the store is located.',
 state       string COMMENT 'State or province of the store.',
 postal_code string COMMENT 'ZIP or postal code of the store.',
 country     string COMMENT 'Country where the store operates.',
 region      string COMMENT 'Geographical region (e.g., North America, EMEA).',

 CONSTRAINT pk_dim_store PRIMARY KEY ( store_id )
)
COMMENT = 'Store dimension table representing physical and online store locations.';

-- ************************************** dim_product
CREATE TABLE dim_product
(
 product_id   string NOT NULL COMMENT 'Unique product identifier (primary key).',
 product_name string COMMENT 'Name of the product.',
 category     string COMMENT 'Product category (e.g., Electronics).',
 sub_category string COMMENT 'Sub-category within the main category.',
 brand        string COMMENT 'Brand of the product.',
 size         string COMMENT 'Size specification (if applicable).',
 color        string COMMENT 'Color of the product.',
 unit_price   number(10,2) COMMENT 'Standard unit price for the product.',

 CONSTRAINT pk_dim_product PRIMARY KEY ( product_id )
)
COMMENT = 'Product dimension table containing product attributes for sales analysis.';

-- ************************************** dim_employee
CREATE TABLE dim_employee
(
 employee_id string NOT NULL COMMENT 'Unique employee identifier (primary key).',
 first_name  string COMMENT 'Employee first name.',
 last_name   string COMMENT 'Employee last name.',
 email       string COMMENT 'Employee email address.',
 phone       string COMMENT 'Employee contact number.',
 hire_date   date COMMENT 'Date when the employee was hired.',
 job_title   string COMMENT 'Employee job title or role.',
 department  string COMMENT 'Department the employee works in.',
 manager_id  string COMMENT 'Manager or supervisor ID (if applicable).',

 CONSTRAINT pk_dim_employee PRIMARY KEY ( employee_id )
)
COMMENT = 'Employee dimension table with personnel and organizational role data.';

-- ************************************** dim_date
CREATE TABLE dim_date
(
 date_key    date NOT NULL COMMENT 'Unique identifier for the date (primary key).',
 full_date   string COMMENT 'Formatted date (e.g., "2025-04-14").',
 day_of_week string COMMENT 'Name of the weekday (e.g., "Monday").',
 day         int COMMENT 'Day of the month (1-31).',
 week        int COMMENT 'ISO week number of the year.',
 month       int COMMENT 'Month number (1-12).',
 month_name  string COMMENT 'Full month name (e.g., "January").',
 quarter     int COMMENT 'Calendar quarter (1-4).',
 year        int COMMENT 'Four-digit year.',
 is_weekend  boolean COMMENT 'Flag to indicate if the date falls on a weekend.',

 CONSTRAINT pk_dim_date PRIMARY KEY ( date_key )
)
COMMENT = 'Date dimension table providing date-level attributes for time-based analysis.';

-- ************************************** dim_customer
CREATE TABLE dim_customer
(
 customer_id      string NOT NULL COMMENT 'Unique customer identifier (primary key).',
 first_name       string COMMENT 'Customer first name.',
 last_name        string COMMENT 'Customer last name.',
 email            string COMMENT 'Customer email address.',
 phone            string COMMENT 'Customer phone number.',
 address          string COMMENT 'Street address.',
 city             string COMMENT 'City of the customer.',
 state            string COMMENT 'State or province of the customer.',
 postal_code      string COMMENT 'Postal or ZIP code.',
 country          string COMMENT 'Customer country.',
 customer_segment string COMMENT 'Customer segment (e.g., Retail, Corporate).',

 CONSTRAINT pk_dim_customer PRIMARY KEY ( customer_id )
)
COMMENT = 'Customer dimension table storing customer details and segmentation data.';

-- ************************************** fact_sales
CREATE TABLE fact_sales
(
 sales_id      string NOT NULL COMMENT 'Unique identifier for each sales transaction (primary key).',
 date_key      date NOT NULL COMMENT 'Foreign key to dim_date.',
 customer_id   string NOT NULL COMMENT 'Foreign key to dim_customer.',
 product_id    string NOT NULL COMMENT 'Foreign key to dim_product.',
 store_id      string NOT NULL COMMENT 'Foreign key to dim_store.',
 employee_id   string NOT NULL COMMENT 'Foreign key to dim_employee.',
 quantity_sold int COMMENT 'Number of product units sold.',
 unit_price    number(10,2) COMMENT 'Unit price at time of sale.',
 discount      number(5,2) COMMENT 'Discount applied on the transaction.',
 total_amount  number(12,2) COMMENT 'Final sale amount after discount.',
 profit        number(12,2) COMMENT 'Profit earned from the transaction.',

 CONSTRAINT pk_fact_sales PRIMARY KEY ( sales_id, date_key, customer_id, product_id, store_id, employee_id ),
 CONSTRAINT fk_fact_sales_customer FOREIGN KEY ( customer_id ) REFERENCES dim_customer ( customer_id ),
 CONSTRAINT fk_fact_sales_date FOREIGN KEY ( date_key ) REFERENCES dim_date ( date_key ),
 CONSTRAINT fk_fact_sales_employee FOREIGN KEY ( employee_id ) REFERENCES dim_employee ( employee_id ),
 CONSTRAINT fk_fact_sales_product FOREIGN KEY ( product_id ) REFERENCES dim_product ( product_id ),
 CONSTRAINT fk_fact_sales_store FOREIGN KEY ( store_id ) REFERENCES dim_store ( store_id )
)
COMMENT = 'Fact table that records all sales transactions, referencing associated dimensions for analytics.';

