author: Luke Ambrosetti, Amanda Cameron-Windsor
id: retail-realtime-recommendations
summary: Build a real-time product recommendation engine for retail using Snowflake Feature Store, Model Registry, and Snowpark Container Services
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/model-development, snowflake-site:taxonomy/snowflake-feature/snowpark-container-services, snowflake-site:taxonomy/snowflake-feature/dynamic-tables, snowflake-site:taxonomy/solution-center/industry/retail, snowflake-site:taxonomy/product/data-engineering
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/retail-realtime-recommendations
language: en
tags: Getting Started, Data Science, ML, Personalization, Retail, Feature Store, Real-Time, SPCS

# Build Real-Time Product Recommendations for Retail with Snowflake
<!-- ------------------------ -->
## Overview
Duration: 5

Modern retailers need to deliver personalized product recommendations in real-time to drive conversion, increase average order value, and improve customer satisfaction. This quickstart guide walks through building a complete real-time recommendation engine powered entirely by Snowflake.

You will build a hybrid batch + real-time ML pipeline that:
1. Generates synthetic retail customer, event, product catalog, and inventory data
2. Builds a Customer 360 gold layer using Dynamic Tables
3. Registers features in the Snowflake Feature Store for training data retrieval
4. Trains two XGBoost models: a batch propensity model (daily) and a real-time product ranking model
5. Deploys the ranking model to Snowpark Container Services (SPCS) for real-time inference
6. Sets up Snowflake Postgres for low-latency operational serving of features, propensity scores, and inventory
7. Builds a FastAPI orchestrator service that fetches data from Postgres, calls the ranking model, and returns top-N recommendations

The architecture follows a pattern discussed in the context of retail Customer 360: the intersection of customer intelligence and product catalog data, positioned as a precursor to agentic commerce.

> **Extension Note:** The availability/delivery estimation step in this quickstart uses a deterministic SQL filter on inventory. For retailers with real logistics data (carrier performance, distance to warehouse, seasonal demand), this filter can be replaced with a CatBoost delivery estimation model to boost customer satisfaction and reduce returns.

### Prerequisites
- Snowflake Enterprise Edition account
- `ACCOUNTADMIN` role or privileges to create databases, warehouses, compute pools, image repositories, services, and Postgres instances
- SPCS enabled on your account
- Snowflake Postgres enabled on your account
- Basic knowledge of Python and ML concepts

### What You'll Learn
- How to generate synthetic retail data using Snowflake UDTFs
- How to build a Customer 360 gold layer with Dynamic Tables
- How to use the Snowflake Feature Store for offline training data retrieval
- How to train and register ML models in the Snowflake Model Registry
- How to deploy a model to SPCS and build a FastAPI orchestrator for real-time recommendations
- How to use Snowflake Postgres for low-latency operational serving

### What You'll Need
- [Snowflake](https://snowflake.com) Enterprise Edition account
- [Docker](https://www.docker.com/) (for building and pushing the orchestrator container)

### What You'll Build
- Real-time product recommendation API powered by Snowflake ML

<!-- ------------------------ -->
## Architecture Overview
Duration: 3

The solution uses a hybrid batch + real-time architecture:

**Batch Path (Daily):**
- Customer 360 Dynamic Table aggregates raw events into customer features
- Propensity model scores each customer's affinity per product category
- Results are stored in the GOLD schema
- Customer features, propensity scores, and inventory are synced to Snowflake Postgres for low-latency serving

**Real-Time Path (Per Request):**
- Orchestrator receives a recommendation request with `customer_id` and `zip_code`
- Customer features, propensity scores, and inventory are fetched from Snowflake Postgres in parallel (~15ms)
- Customer-product pair features are computed and sent to the ranking model service
- Top-N recommendations are returned with product details and estimated delivery
- Falls back to Snowflake warehouse queries if Postgres is not configured

**Key Design Decisions:**
- Customer propensity is batch because it changes slowly (loyalty tier, purchase history)
- Product ranking is real-time because it depends on current inventory and request context
- Inventory availability is deterministic (SQL filter) rather than ML-based
- XGBoost is used for speed — lightweight tree models keep inference under 200ms
- Snowflake Postgres provides single-digit-millisecond lookups for operational serving, reducing end-to-end latency from ~850ms to ~80ms
- Customer features and propensity scores are kept in separate Postgres tables due to different cardinality (1 row/customer vs 12 rows/customer), query patterns, and refresh cadences

<!-- ------------------------ -->
## Setting Up Infrastructure
Duration: 3

Connect to Snowflake and run the following SQL to create the database, schemas, warehouse, role, compute pool, and image repository.

```sql
USE ROLE ACCOUNTADMIN;

-- Database and schemas
CREATE OR REPLACE DATABASE RETAIL_RECOMMENDATION_QS;
CREATE SCHEMA RETAIL_RECOMMENDATION_QS.RAW;
CREATE SCHEMA RETAIL_RECOMMENDATION_QS.GOLD;
CREATE SCHEMA RETAIL_RECOMMENDATION_QS.FEATURE_STORE;
CREATE SCHEMA RETAIL_RECOMMENDATION_QS.ML_REGISTRY;

-- Warehouse
CREATE OR REPLACE WAREHOUSE RETAIL_QS_WH
  WITH WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 120
  AUTO_RESUME = TRUE;

-- Role
CREATE OR REPLACE ROLE RETAIL_QS_ROLE;
GRANT USAGE ON DATABASE RETAIL_RECOMMENDATION_QS TO ROLE RETAIL_QS_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE RETAIL_RECOMMENDATION_QS TO ROLE RETAIL_QS_ROLE;
GRANT ALL ON SCHEMA RETAIL_RECOMMENDATION_QS.RAW TO ROLE RETAIL_QS_ROLE;
GRANT ALL ON SCHEMA RETAIL_RECOMMENDATION_QS.GOLD TO ROLE RETAIL_QS_ROLE;
GRANT ALL ON SCHEMA RETAIL_RECOMMENDATION_QS.FEATURE_STORE TO ROLE RETAIL_QS_ROLE;
GRANT ALL ON SCHEMA RETAIL_RECOMMENDATION_QS.ML_REGISTRY TO ROLE RETAIL_QS_ROLE;
GRANT USAGE ON WAREHOUSE RETAIL_QS_WH TO ROLE RETAIL_QS_ROLE;
GRANT CREATE DYNAMIC TABLE ON SCHEMA RETAIL_RECOMMENDATION_QS.GOLD TO ROLE RETAIL_QS_ROLE;
GRANT CREATE DYNAMIC TABLE ON SCHEMA RETAIL_RECOMMENDATION_QS.FEATURE_STORE TO ROLE RETAIL_QS_ROLE;
GRANT CREATE TABLE ON SCHEMA RETAIL_RECOMMENDATION_QS.RAW TO ROLE RETAIL_QS_ROLE;
GRANT CREATE TABLE ON SCHEMA RETAIL_RECOMMENDATION_QS.GOLD TO ROLE RETAIL_QS_ROLE;
GRANT CREATE TABLE ON SCHEMA RETAIL_RECOMMENDATION_QS.FEATURE_STORE TO ROLE RETAIL_QS_ROLE;
GRANT CREATE MODEL ON SCHEMA RETAIL_RECOMMENDATION_QS.ML_REGISTRY TO ROLE RETAIL_QS_ROLE;
GRANT CREATE FUNCTION ON SCHEMA RETAIL_RECOMMENDATION_QS.RAW TO ROLE RETAIL_QS_ROLE;
GRANT ROLE RETAIL_QS_ROLE TO ROLE ACCOUNTADMIN;

-- Compute pool for SPCS
CREATE COMPUTE POOL IF NOT EXISTS RETAIL_QS_COMPUTE_POOL
  MIN_NODES = 1
  MAX_NODES = 3
  INSTANCE_FAMILY = CPU_X64_S;

GRANT USAGE ON COMPUTE POOL RETAIL_QS_COMPUTE_POOL TO ROLE RETAIL_QS_ROLE;
GRANT MONITOR ON COMPUTE POOL RETAIL_QS_COMPUTE_POOL TO ROLE RETAIL_QS_ROLE;

-- Image repository
CREATE IMAGE REPOSITORY IF NOT EXISTS RETAIL_RECOMMENDATION_QS.RAW.RETAIL_QS_IMAGES;
GRANT READ ON IMAGE REPOSITORY RETAIL_RECOMMENDATION_QS.RAW.RETAIL_QS_IMAGES TO ROLE RETAIL_QS_ROLE;

-- Stage for orchestrator spec
CREATE STAGE IF NOT EXISTS RETAIL_RECOMMENDATION_QS.RAW.ORCHESTRATOR_STAGE;
GRANT ALL ON STAGE RETAIL_RECOMMENDATION_QS.RAW.ORCHESTRATOR_STAGE TO ROLE RETAIL_QS_ROLE;

-- SPCS permissions
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE RETAIL_QS_ROLE;
GRANT CREATE SERVICE ON SCHEMA RETAIL_RECOMMENDATION_QS.RAW TO ROLE RETAIL_QS_ROLE;
GRANT CREATE SERVICE ON SCHEMA RETAIL_RECOMMENDATION_QS.ML_REGISTRY TO ROLE RETAIL_QS_ROLE;

SHOW IMAGE REPOSITORIES IN SCHEMA RETAIL_RECOMMENDATION_QS.RAW;
```

Note the `repository_url` from the last command — you will need it when pushing the orchestrator container later.

<!-- ------------------------ -->
## Creating Reference Tables
Duration: 2

These reference tables provide the foundation for synthetic data generation: store locations, product categories, loyalty tiers, and promotions.

```sql
USE ROLE RETAIL_QS_ROLE;
USE DATABASE RETAIL_RECOMMENDATION_QS;
USE SCHEMA RAW;
USE WAREHOUSE RETAIL_QS_WH;

-- Store locations
CREATE OR REPLACE TABLE STORES AS
SELECT
  SEQ4() AS STORE_ID,
  CONCAT('Store_', LPAD(SEQ4()::STRING, 4, '0')) AS STORE_CODE,
  CASE (ABS(HASH(SEQ4())) % 4)
    WHEN 0 THEN 'Flagship' WHEN 1 THEN 'Standard'
    WHEN 2 THEN 'Outlet' ELSE 'Express' END AS STORE_TYPE,
  CASE (ABS(HASH(SEQ4(), 1)) % 10)
    WHEN 0 THEN 'New York' WHEN 1 THEN 'Los Angeles' WHEN 2 THEN 'Chicago'
    WHEN 3 THEN 'Houston' WHEN 4 THEN 'Phoenix' WHEN 5 THEN 'Dallas'
    WHEN 6 THEN 'Seattle' WHEN 7 THEN 'Miami' WHEN 8 THEN 'Atlanta'
    ELSE 'Denver' END AS CITY,
  CASE (ABS(HASH(SEQ4(), 1)) % 10)
    WHEN 0 THEN 'NY' WHEN 1 THEN 'CA' WHEN 2 THEN 'IL'
    WHEN 3 THEN 'TX' WHEN 4 THEN 'AZ' WHEN 5 THEN 'TX'
    WHEN 6 THEN 'WA' WHEN 7 THEN 'FL' WHEN 8 THEN 'GA'
    ELSE 'CO' END AS STATE,
  CASE (ABS(HASH(SEQ4(), 1)) % 10)
    WHEN 0 THEN 'Northeast' WHEN 1 THEN 'West' WHEN 2 THEN 'Midwest'
    WHEN 3 THEN 'South' WHEN 4 THEN 'West' WHEN 5 THEN 'South'
    WHEN 6 THEN 'West' WHEN 7 THEN 'Southeast' WHEN 8 THEN 'Southeast'
    ELSE 'West' END AS REGION,
  CASE (ABS(HASH(SEQ4(), 2)) % 5)
    WHEN 0 THEN 'Mall' WHEN 1 THEN 'Strip Center'
    WHEN 2 THEN 'Standalone' WHEN 3 THEN 'Downtown'
    ELSE 'Suburban' END AS LOCATION_TYPE,
  (ABS(HASH(SEQ4(), 3)) % 30000 + 5000) AS SQUARE_FEET
FROM TABLE(GENERATOR(ROWCOUNT => 500));

-- Product categories
CREATE OR REPLACE TABLE PRODUCT_CATEGORIES AS
SELECT * FROM VALUES
  ('CAT-001', 'Apparel', 'Womens Clothing', 25.00, 250.00),
  ('CAT-002', 'Apparel', 'Mens Clothing', 30.00, 200.00),
  ('CAT-003', 'Apparel', 'Kids Clothing', 15.00, 80.00),
  ('CAT-004', 'Footwear', 'Athletic Shoes', 60.00, 200.00),
  ('CAT-005', 'Footwear', 'Casual Shoes', 40.00, 150.00),
  ('CAT-006', 'Accessories', 'Bags & Wallets', 30.00, 400.00),
  ('CAT-007', 'Accessories', 'Jewelry', 20.00, 500.00),
  ('CAT-008', 'Home', 'Bedding', 50.00, 300.00),
  ('CAT-009', 'Home', 'Kitchen', 15.00, 200.00),
  ('CAT-010', 'Beauty', 'Skincare', 15.00, 150.00),
  ('CAT-011', 'Beauty', 'Makeup', 10.00, 80.00),
  ('CAT-012', 'Electronics', 'Audio', 30.00, 400.00)
AS c(CATEGORY_ID, DEPARTMENT, CATEGORY_NAME, MIN_PRICE, MAX_PRICE);

-- Loyalty tiers
CREATE OR REPLACE TABLE LOYALTY_TIERS AS
SELECT * FROM VALUES
  ('TIER-001', 'Bronze', 0, 499, 1.0, 0),
  ('TIER-002', 'Silver', 500, 1499, 1.25, 5),
  ('TIER-003', 'Gold', 1500, 4999, 1.5, 10),
  ('TIER-004', 'Platinum', 5000, 99999, 2.0, 15)
AS t(TIER_ID, TIER_NAME, MIN_ANNUAL_SPEND, MAX_ANNUAL_SPEND, POINTS_MULTIPLIER, DISCOUNT_PCT);
```

<!-- ------------------------ -->
## Creating the Product Catalog
Duration: 2

The product catalog contains 2,000 products across the 12 categories defined above. Each product has a name, brand, price, and category assignment. This UDTF generates realistic retail product data.

```sql
USE SCHEMA RAW;

CREATE OR REPLACE FUNCTION GENERATE_PRODUCT(SEED INT)
RETURNS TABLE (
  PRODUCT_ID NUMBER,
  PRODUCT_NAME STRING,
  CATEGORY_ID STRING,
  DEPARTMENT STRING,
  CATEGORY_NAME STRING,
  BRAND STRING,
  PRICE FLOAT,
  WEIGHT_LBS FLOAT,
  IS_PERISHABLE BOOLEAN,
  PRODUCT_TYPE STRING
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'Generator'
AS $$
import random

class Generator:
    BRANDS = {
        'Apparel': ['NorthStyle', 'UrbanThread', 'ClassicCo', 'TrendLine', 'EverWear'],
        'Footwear': ['StridePro', 'WalkEasy', 'RunFast', 'ComfortStep', 'TrailBlaze'],
        'Accessories': ['LuxCarry', 'DailyGem', 'TrendSet', 'FineCraft', 'StyleVault'],
        'Home': ['HomeNest', 'CozyLife', 'ModernLiv', 'PureLinen', 'CraftHome'],
        'Beauty': ['GlowUp', 'PureSkin', 'FreshFace', 'NaturalGlow', 'LuxBeauty'],
        'Electronics': ['SoundMax', 'AudioPeak', 'BeatWave', 'ClearTone', 'BassDrop'],
    }
    CATEGORIES = [
        ('CAT-001', 'Apparel', 'Womens Clothing', 25.0, 250.0),
        ('CAT-002', 'Apparel', 'Mens Clothing', 30.0, 200.0),
        ('CAT-003', 'Apparel', 'Kids Clothing', 15.0, 80.0),
        ('CAT-004', 'Footwear', 'Athletic Shoes', 60.0, 200.0),
        ('CAT-005', 'Footwear', 'Casual Shoes', 40.0, 150.0),
        ('CAT-006', 'Accessories', 'Bags & Wallets', 30.0, 400.0),
        ('CAT-007', 'Accessories', 'Jewelry', 20.0, 500.0),
        ('CAT-008', 'Home', 'Bedding', 50.0, 300.0),
        ('CAT-009', 'Home', 'Kitchen', 15.0, 200.0),
        ('CAT-010', 'Beauty', 'Skincare', 15.0, 150.0),
        ('CAT-011', 'Beauty', 'Makeup', 10.0, 80.0),
        ('CAT-012', 'Electronics', 'Audio', 30.0, 400.0),
    ]
    ADJECTIVES = ['Premium', 'Classic', 'Modern', 'Essential', 'Deluxe', 'Ultra',
                  'Pro', 'Signature', 'Everyday', 'Performance']
    NOUNS = {
        'Womens Clothing': ['Blouse', 'Dress', 'Jacket', 'Skirt', 'Cardigan'],
        'Mens Clothing': ['Shirt', 'Polo', 'Chinos', 'Blazer', 'Sweater'],
        'Kids Clothing': ['Tee', 'Hoodie', 'Shorts', 'Romper', 'Jacket'],
        'Athletic Shoes': ['Runner', 'Trainer', 'Court Shoe', 'Cleats', 'Trail Shoe'],
        'Casual Shoes': ['Loafer', 'Sneaker', 'Sandal', 'Boot', 'Slip-On'],
        'Bags & Wallets': ['Tote', 'Crossbody', 'Wallet', 'Backpack', 'Clutch'],
        'Jewelry': ['Necklace', 'Bracelet', 'Ring', 'Earrings', 'Watch'],
        'Bedding': ['Sheet Set', 'Comforter', 'Pillow', 'Duvet', 'Blanket'],
        'Kitchen': ['Mug Set', 'Cutting Board', 'Knife Set', 'Pan', 'Mixer'],
        'Skincare': ['Moisturizer', 'Serum', 'Cleanser', 'Sunscreen', 'Mask'],
        'Makeup': ['Foundation', 'Lipstick', 'Mascara', 'Palette', 'Blush'],
        'Audio': ['Headphones', 'Earbuds', 'Speaker', 'Soundbar', 'Turntable'],
    }

    def process(self, seed):
        rng = random.Random(seed)
        cat_id, dept, cat_name, min_p, max_p = rng.choice(self.CATEGORIES)
        brand = rng.choice(self.BRANDS[dept])
        adj = rng.choice(self.ADJECTIVES)
        noun = rng.choice(self.NOUNS[cat_name])
        name = f"{brand} {adj} {noun}"
        price = round(rng.uniform(min_p, max_p), 2)
        weight = round(rng.uniform(0.2, 15.0), 1)
        is_perishable = dept == 'Beauty' and rng.random() < 0.3
        ptype = 'daily_staple' if price < 50 else ('mid_range' if price < 150 else 'premium')
        yield (seed, name, cat_id, dept, cat_name, brand, price, weight, is_perishable, ptype)
$$;

CREATE OR REPLACE TABLE PRODUCT_CATALOG AS
SELECT p.*
FROM TABLE(GENERATOR(ROWCOUNT => 2000)) g,
TABLE(GENERATE_PRODUCT(SEQ4()::INT)) p;

SELECT DEPARTMENT, COUNT(*) AS CNT, ROUND(AVG(PRICE), 2) AS AVG_PRICE
FROM PRODUCT_CATALOG GROUP BY DEPARTMENT ORDER BY CNT DESC;
```

<!-- ------------------------ -->
## Creating the Inventory Table
Duration: 1

The inventory table tracks stock levels per product per warehouse region. This is the deterministic availability layer — no ML needed for "is it in stock?"

```sql
USE SCHEMA RAW;

CREATE OR REPLACE TABLE INVENTORY AS
SELECT
  p.PRODUCT_ID,
  regions.REGION,
  regions.WAREHOUSE_NAME,
  CASE
    WHEN UNIFORM(0, 100, RANDOM()) < 85 THEN UNIFORM(5, 500, RANDOM())
    ELSE 0
  END AS QTY_ON_HAND,
  CASE regions.REGION
    WHEN 'Northeast' THEN UNIFORM(1, 3, RANDOM())
    WHEN 'Southeast' THEN UNIFORM(1, 4, RANDOM())
    WHEN 'Midwest' THEN UNIFORM(2, 4, RANDOM())
    WHEN 'South' THEN UNIFORM(2, 5, RANDOM())
    WHEN 'West' THEN UNIFORM(2, 5, RANDOM())
  END AS EST_DELIVERY_DAYS,
  CURRENT_TIMESTAMP() AS LAST_UPDATED
FROM PRODUCT_CATALOG p
CROSS JOIN (
  SELECT COLUMN1 AS REGION, COLUMN2 AS WAREHOUSE_NAME FROM VALUES
    ('Northeast', 'WH-NE-01'),
    ('Southeast', 'WH-SE-01'),
    ('Midwest', 'WH-MW-01'),
    ('South', 'WH-SO-01'),
    ('West', 'WH-WE-01')
) AS regions;

SELECT REGION, COUNT(*) AS PRODUCTS, SUM(CASE WHEN QTY_ON_HAND > 0 THEN 1 ELSE 0 END) AS IN_STOCK
FROM INVENTORY GROUP BY REGION;
```

<!-- ------------------------ -->
## Generating Synthetic Customers
Duration: 3

This UDTF generates 50,000 synthetic retail customers with demographics, loyalty tier assignment, and channel preferences.

```sql
USE SCHEMA RAW;

CREATE OR REPLACE FUNCTION GENERATE_RETAIL_CUSTOMER(SEED INT)
RETURNS TABLE (
  CUSTOMER_ID NUMBER,
  EMAIL STRING,
  PHONE STRING,
  FIRST_NAME STRING,
  LAST_NAME STRING,
  DATE_OF_BIRTH DATE,
  GENDER STRING,
  STREET_ADDRESS STRING,
  CITY STRING,
  STATE STRING,
  ZIP_CODE STRING,
  CUSTOMER_SINCE_DATE DATE,
  LOYALTY_TIER STRING,
  HAS_APP BOOLEAN,
  EMAIL_SUBSCRIBER BOOLEAN,
  SMS_SUBSCRIBER BOOLEAN
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('faker')
HANDLER = 'Generator'
AS $$
import random
from faker import Faker

class Generator:
    TIERS = ['Bronze', 'Silver', 'Gold', 'Platinum']
    TIER_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

    def process(self, seed):
        fake = Faker('en_US')
        Faker.seed(seed)
        rng = random.Random(seed)
        cid = seed + 1000000
        gender = rng.choices(['Female', 'Male', 'Non-binary'], weights=[55, 40, 5])[0]
        first = fake.first_name_female() if gender == 'Female' else fake.first_name_male() if gender == 'Male' else fake.first_name()
        last = fake.last_name()
        email = f"{first.lower()}.{last.lower()}{rng.randint(1,999)}@{rng.choice(['gmail.com','yahoo.com','outlook.com','aol.com'])}"
        phone = fake.phone_number()
        dob = fake.date_of_birth(minimum_age=18, maximum_age=75)
        addr = fake.street_address()
        city = fake.city()
        state = fake.state_abbr()
        zipcode = fake.zipcode()
        since = fake.date_between(start_date='-10y', end_date='today')
        tier = rng.choices(self.TIERS, weights=self.TIER_WEIGHTS)[0]
        has_app = rng.random() < 0.45
        email_sub = rng.random() < 0.70
        sms_sub = rng.random() < 0.35
        yield (cid, email, phone, first, last, dob, gender, addr, city, state, zipcode, since, tier, has_app, email_sub, sms_sub)
$$;

CREATE OR REPLACE TABLE CUSTOMERS AS
SELECT c.* FROM TABLE(GENERATOR(ROWCOUNT => 50000)) g,
TABLE(GENERATE_RETAIL_CUSTOMER(SEQ4()::INT)) c;

SELECT LOYALTY_TIER, COUNT(*) AS CNT,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS PCT
FROM CUSTOMERS GROUP BY LOYALTY_TIER ORDER BY CNT DESC;
```

<!-- ------------------------ -->
## Generating Synthetic Events
Duration: 5

This UDTF generates a realistic event stream for each customer: browsing, cart activity, purchases, post-purchase events, loyalty events, and in-store visits. Events include product IDs from the catalog to enable recommendation model training.

```sql
USE SCHEMA RAW;

CREATE OR REPLACE FUNCTION GENERATE_RETAIL_EVENTS(
  CUSTOMER_ID INT, HAS_APP BOOLEAN, CITY STRING, STATE STRING, LOYALTY_TIER STRING
)
RETURNS TABLE (
  EVENT_ID STRING,
  CUSTOMER_ID NUMBER,
  EVENT_TYPE STRING,
  EVENT_TIMESTAMP TIMESTAMP_NTZ,
  CHANNEL STRING,
  SESSION_ID STRING,
  DEVICE_TYPE STRING,
  PRODUCT_ID NUMBER,
  PRODUCT_CATEGORY STRING,
  PRODUCT_PRICE FLOAT,
  QUANTITY INT,
  CART_VALUE FLOAT,
  ORDER_ID STRING,
  ORDER_TOTAL FLOAT,
  STORE_ID INT,
  PROMO_CODE STRING,
  POINTS_EARNED INT,
  POINTS_REDEEMED INT
)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'Generator'
AS $$
import random
import uuid
from datetime import datetime, timedelta

class Generator:
    EVENT_TYPES = {
        'browse': ['page_view', 'product_view', 'category_browse', 'search', 'add_to_wishlist'],
        'cart': ['add_to_cart', 'remove_from_cart', 'cart_view', 'abandoned_cart'],
        'purchase': ['checkout_start', 'payment', 'order_complete'],
        'post': ['order_shipped', 'order_delivered', 'return_initiated', 'review_submitted'],
        'loyalty': ['points_earned', 'points_redeemed', 'tier_upgrade'],
        'store': ['store_visit', 'pos_purchase'],
    }
    CATEGORIES = ['CAT-001','CAT-002','CAT-003','CAT-004','CAT-005','CAT-006',
                  'CAT-007','CAT-008','CAT-009','CAT-010','CAT-011','CAT-012']
    PROMOS = ['SPRING20', 'SUMMER40', 'BTS25', 'BLACKFRI', 'HOLIDAY15', 'NEWYEAR30', 'VIPONLY', 'FREESHIP']
    TIER_ACTIVITY = {'Bronze': 40, 'Silver': 70, 'Gold': 110, 'Platinum': 160}

    def process(self, customer_id, has_app, city, state, loyalty_tier):
        rng = random.Random(customer_id)
        num_events = self.TIER_ACTIVITY.get(loyalty_tier, 60) + rng.randint(-20, 30)
        num_events = max(10, num_events)
        base_date = datetime.now() - timedelta(days=365)
        sessions = rng.randint(5, num_events // 3 + 1)
        fav_cats = rng.sample(self.CATEGORIES, k=min(3, len(self.CATEGORIES)))
        order_counter = 0

        for _ in range(num_events):
            ts = base_date + timedelta(seconds=rng.randint(0, 365 * 86400))
            session_id = f"S-{customer_id}-{rng.randint(1, sessions)}"
            group = rng.choices(
                ['browse', 'cart', 'purchase', 'post', 'loyalty', 'store'],
                weights=[35, 15, 8, 5, 5, 12 if not has_app else 7]
            )[0]
            evt = rng.choice(self.EVENT_TYPES[group])

            if has_app:
                channel = rng.choices(['Web', 'App', 'Store'], weights=[40, 40, 20])[0]
                device = rng.choice(['Mobile', 'Desktop', 'Tablet']) if channel != 'Store' else 'POS'
            else:
                channel = rng.choices(['Web', 'Store'], weights=[55, 45])[0]
                device = rng.choice(['Mobile', 'Desktop']) if channel != 'Store' else 'POS'

            cat = rng.choices(self.CATEGORIES, weights=[3 if c in fav_cats else 1 for c in self.CATEGORIES])[0]
            cat_idx = self.CATEGORIES.index(cat)
            prod_id = cat_idx * 200 + rng.randint(0, 160)
            price = round(rng.uniform(10, 300), 2)
            qty = rng.choice([1, 1, 1, 2, 3]) if evt in ('add_to_cart', 'order_complete', 'pos_purchase') else 0
            cart_val = round(price * qty, 2) if qty > 0 else None
            order_id = None
            order_total = None
            store_id = rng.randint(0, 499) if channel == 'Store' else None
            promo = rng.choice(self.PROMOS) if evt == 'order_complete' and rng.random() < 0.15 else None
            pts_earned = rng.randint(10, 200) if evt == 'points_earned' else 0
            pts_redeemed = rng.randint(50, 500) if evt == 'points_redeemed' else 0

            if evt in ('order_complete', 'pos_purchase'):
                order_counter += 1
                order_id = f"ORD-{customer_id}-{order_counter}"
                order_total = round(price * max(qty, 1) * rng.uniform(0.85, 1.15), 2)

            yield (
                str(uuid.UUID(int=rng.getrandbits(128))),
                customer_id, evt, ts, channel, session_id, device,
                prod_id, cat, price, qty, cart_val, order_id, order_total,
                store_id, promo, pts_earned, pts_redeemed
            )
$$;

CREATE OR REPLACE TABLE EVENT_STREAM AS
SELECT e.* FROM CUSTOMERS c,
TABLE(GENERATE_RETAIL_EVENTS(
  c.CUSTOMER_ID, c.HAS_APP, c.CITY, c.STATE, c.LOYALTY_TIER
)) e;

SELECT EVENT_TYPE, COUNT(*) AS CNT
FROM EVENT_STREAM GROUP BY EVENT_TYPE ORDER BY CNT DESC LIMIT 15;
```

This will generate approximately 3-5 million events depending on tier distribution. The query should take 2-4 minutes on a MEDIUM warehouse.

<!-- ------------------------ -->
## Building the Customer 360 Gold Layer
Duration: 3

The Customer 360 Dynamic Table aggregates raw events into a rich customer feature set. It refreshes automatically as new data arrives.

```sql
USE SCHEMA GOLD;

CREATE OR REPLACE DYNAMIC TABLE CUSTOMER_360
  TARGET_LAG = '30 minutes'
  WAREHOUSE = RETAIL_QS_WH
AS
WITH purchase_stats AS (
  SELECT
    CUSTOMER_ID,
    COUNT(DISTINCT ORDER_ID) AS TOTAL_ORDERS,
    SUM(ORDER_TOTAL) AS LIFETIME_SPEND,
    AVG(ORDER_TOTAL) AS AVG_ORDER_VALUE,
    MAX(EVENT_TIMESTAMP) AS LAST_PURCHASE_DATE,
    COUNT(DISTINCT PRODUCT_CATEGORY) AS CATEGORIES_PURCHASED,
    DATEDIFF('day', MAX(EVENT_TIMESTAMP), CURRENT_TIMESTAMP()) AS DAYS_SINCE_PURCHASE
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  WHERE EVENT_TYPE IN ('order_complete', 'pos_purchase')
  GROUP BY CUSTOMER_ID
),
browse_stats AS (
  SELECT
    CUSTOMER_ID,
    COUNT(*) AS TOTAL_BROWSE_EVENTS,
    COUNT(DISTINCT SESSION_ID) AS TOTAL_SESSIONS,
    COUNT(DISTINCT PRODUCT_CATEGORY) AS CATEGORIES_BROWSED,
    MODE(PRODUCT_CATEGORY) AS FAVORITE_BROWSE_CATEGORY,
    AVG(PRODUCT_PRICE) AS AVG_BROWSED_PRICE
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  WHERE EVENT_TYPE IN ('product_view', 'category_browse', 'search')
  GROUP BY CUSTOMER_ID
),
cart_stats AS (
  SELECT
    CUSTOMER_ID,
    SUM(CASE WHEN EVENT_TYPE = 'add_to_cart' THEN 1 ELSE 0 END) AS ADD_TO_CART_COUNT,
    SUM(CASE WHEN EVENT_TYPE = 'abandoned_cart' THEN 1 ELSE 0 END) AS ABANDONED_CART_COUNT
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  WHERE EVENT_TYPE IN ('add_to_cart', 'abandoned_cart')
  GROUP BY CUSTOMER_ID
),
channel_stats AS (
  SELECT
    CUSTOMER_ID,
    MODE(CHANNEL) AS PREFERRED_CHANNEL,
    MODE(DEVICE_TYPE) AS PREFERRED_DEVICE,
    SUM(CASE WHEN CHANNEL = 'Store' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS STORE_RATIO
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  GROUP BY CUSTOMER_ID
),
loyalty_stats AS (
  SELECT
    CUSTOMER_ID,
    SUM(POINTS_EARNED) AS TOTAL_POINTS_EARNED,
    SUM(POINTS_REDEEMED) AS TOTAL_POINTS_REDEEMED
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  WHERE EVENT_TYPE IN ('points_earned', 'points_redeemed')
  GROUP BY CUSTOMER_ID
),
favorite_product_cat AS (
  SELECT
    CUSTOMER_ID,
    MODE(PRODUCT_CATEGORY) AS FAVORITE_PURCHASE_CATEGORY
  FROM RETAIL_RECOMMENDATION_QS.RAW.EVENT_STREAM
  WHERE EVENT_TYPE IN ('order_complete', 'pos_purchase')
  GROUP BY CUSTOMER_ID
)
SELECT
  c.CUSTOMER_ID,
  c.FIRST_NAME,
  c.LAST_NAME,
  c.EMAIL,
  c.GENDER,
  c.DATE_OF_BIRTH,
  DATEDIFF('year', c.DATE_OF_BIRTH, CURRENT_DATE()) AS AGE,
  c.CITY,
  c.STATE,
  c.ZIP_CODE,
  c.CUSTOMER_SINCE_DATE,
  DATEDIFF('month', c.CUSTOMER_SINCE_DATE, CURRENT_DATE()) AS TENURE_MONTHS,
  c.LOYALTY_TIER,
  c.HAS_APP,
  c.EMAIL_SUBSCRIBER,
  c.SMS_SUBSCRIBER,
  COALESCE(p.TOTAL_ORDERS, 0) AS TOTAL_ORDERS,
  COALESCE(p.LIFETIME_SPEND, 0) AS LIFETIME_SPEND,
  COALESCE(p.AVG_ORDER_VALUE, 0) AS AVG_ORDER_VALUE,
  p.LAST_PURCHASE_DATE,
  COALESCE(p.DAYS_SINCE_PURCHASE, 999) AS DAYS_SINCE_PURCHASE,
  COALESCE(p.CATEGORIES_PURCHASED, 0) AS CATEGORIES_PURCHASED,
  COALESCE(b.TOTAL_BROWSE_EVENTS, 0) AS TOTAL_BROWSE_EVENTS,
  COALESCE(b.TOTAL_SESSIONS, 0) AS TOTAL_SESSIONS,
  COALESCE(b.CATEGORIES_BROWSED, 0) AS CATEGORIES_BROWSED,
  b.FAVORITE_BROWSE_CATEGORY,
  COALESCE(b.AVG_BROWSED_PRICE, 0) AS AVG_BROWSED_PRICE,
  COALESCE(ct.ADD_TO_CART_COUNT, 0) AS ADD_TO_CART_COUNT,
  COALESCE(ct.ABANDONED_CART_COUNT, 0) AS ABANDONED_CART_COUNT,
  CASE WHEN COALESCE(ct.ADD_TO_CART_COUNT, 0) > 0
    THEN ROUND(COALESCE(ct.ABANDONED_CART_COUNT, 0) * 1.0 / ct.ADD_TO_CART_COUNT, 3)
    ELSE 0 END AS CART_ABANDONMENT_RATE,
  ch.PREFERRED_CHANNEL,
  ch.PREFERRED_DEVICE,
  COALESCE(ch.STORE_RATIO, 0) AS STORE_RATIO,
  COALESCE(l.TOTAL_POINTS_EARNED, 0) AS TOTAL_POINTS_EARNED,
  COALESCE(l.TOTAL_POINTS_REDEEMED, 0) AS TOTAL_POINTS_REDEEMED,
  fpc.FAVORITE_PURCHASE_CATEGORY,
  CASE
    WHEN COALESCE(p.DAYS_SINCE_PURCHASE, 999) <= 30 AND COALESCE(p.TOTAL_ORDERS, 0) >= 5 AND COALESCE(p.LIFETIME_SPEND, 0) >= 500 THEN 'Champion'
    WHEN COALESCE(p.TOTAL_ORDERS, 0) >= 3 AND COALESCE(p.LIFETIME_SPEND, 0) >= 200 THEN 'Loyal'
    WHEN COALESCE(p.DAYS_SINCE_PURCHASE, 999) <= 60 THEN 'Active'
    WHEN COALESCE(p.DAYS_SINCE_PURCHASE, 999) <= 180 THEN 'At_Risk'
    ELSE 'Dormant'
  END AS RFM_SEGMENT,
  ROUND(
    LEAST(100,
      COALESCE(b.TOTAL_SESSIONS, 0) * 0.3 +
      COALESCE(p.TOTAL_ORDERS, 0) * 5 +
      COALESCE(l.TOTAL_POINTS_EARNED, 0) * 0.01 +
      CASE WHEN c.HAS_APP THEN 10 ELSE 0 END +
      CASE WHEN c.EMAIL_SUBSCRIBER THEN 5 ELSE 0 END
    ), 1
  ) AS ENGAGEMENT_SCORE
FROM RETAIL_RECOMMENDATION_QS.RAW.CUSTOMERS c
LEFT JOIN purchase_stats p ON c.CUSTOMER_ID = p.CUSTOMER_ID
LEFT JOIN browse_stats b ON c.CUSTOMER_ID = b.CUSTOMER_ID
LEFT JOIN cart_stats ct ON c.CUSTOMER_ID = ct.CUSTOMER_ID
LEFT JOIN channel_stats ch ON c.CUSTOMER_ID = ch.CUSTOMER_ID
LEFT JOIN loyalty_stats l ON c.CUSTOMER_ID = l.CUSTOMER_ID
LEFT JOIN favorite_product_cat fpc ON c.CUSTOMER_ID = fpc.CUSTOMER_ID;

SELECT RFM_SEGMENT, COUNT(*) AS CNT, ROUND(AVG(ENGAGEMENT_SCORE), 1) AS AVG_ENGAGEMENT
FROM CUSTOMER_360 GROUP BY RFM_SEGMENT ORDER BY CNT DESC;
```

> **Note:** Snowflake may select FULL refresh mode for this Dynamic Table because of `AVG()` aggregations on FLOAT columns combined with JOINs. This does not affect correctness — it simply means each refresh recomputes the full table rather than incrementally updating. For production, consider casting FLOAT columns to `DECIMAL(18,4)` to enable incremental refresh.

<!-- ------------------------ -->
## Feature Store, Model Training, and Registration
Duration: 15

This step uses a Snowflake Notebook to:

1. **Set up the Feature Store** with two feature views (customer features and product features) for training data retrieval
2. **Train the propensity model** (XGBoost) — predicts customer affinity per product category, run as daily batch
3. **Train the ranking model** (XGBoost) — scores customer-product pairs in real-time
4. **Register both models** in the Snowflake Model Registry
5. **Deploy the ranking model** to SPCS for real-time inference

### Running the Notebook

1. Download [`01_train_and_register.ipynb`](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/retail-realtime-recommendations/notebooks/01_train_and_register.ipynb) from the companion repository
2. Open Snowsight and navigate to **Notebooks**
3. Click **+ Notebook** → **Import .ipynb file** and upload the downloaded notebook
4. Before running, add the required packages via the **Packages** button in the top-right:
   - `snowflake-ml-python` (>= 1.7.0)
   - `xgboost`
   - `scikit-learn`
5. Set the role to `RETAIL_QS_ROLE` and warehouse to `RETAIL_QS_WH`
6. Run all cells sequentially

> **Note:** This notebook must be run interactively in Snowsight — it cannot be executed headlessly via `EXECUTE NOTEBOOK` because the required packages must be added through the UI package selector.

After the notebook completes, verify the models are registered:

```sql
USE ROLE RETAIL_QS_ROLE;
SHOW MODELS IN SCHEMA RETAIL_RECOMMENDATION_QS.ML_REGISTRY;
```

You should see two models:
- `CATEGORY_PROPENSITY_MODEL` — batch propensity (target_platforms: WAREHOUSE)
- `PRODUCT_RANKING_MODEL` — real-time ranking (target_platforms: SNOWPARK_CONTAINER_SERVICES)

<!-- ------------------------ -->
## Running Batch Propensity Scoring
Duration: 3

After training, run the propensity model in batch mode to score all customers. This creates a table of per-customer propensity scores.

> **Note:** Model inference calls (`MODEL!PREDICT_PROBA`) are not currently supported inside Dynamic Table definitions. We use a CTAS statement instead, which you can schedule with a Snowflake Task for daily refresh.

```sql
USE ROLE RETAIL_QS_ROLE;
USE DATABASE RETAIL_RECOMMENDATION_QS;
USE SCHEMA GOLD;
USE WAREHOUSE RETAIL_QS_WH;

CREATE OR REPLACE TABLE CUSTOMER_PROPENSITY AS
WITH customer_features AS (
  SELECT
    CUSTOMER_ID,
    AGE,
    TENURE_MONTHS,
    CASE LOYALTY_TIER
      WHEN 'Bronze' THEN 0 WHEN 'Silver' THEN 1
      WHEN 'Gold' THEN 2 WHEN 'Platinum' THEN 3
    END AS LOYALTY_TIER_NUM,
    TOTAL_ORDERS,
    LIFETIME_SPEND,
    AVG_ORDER_VALUE,
    DAYS_SINCE_PURCHASE,
    CATEGORIES_PURCHASED,
    TOTAL_BROWSE_EVENTS,
    TOTAL_SESSIONS,
    CART_ABANDONMENT_RATE,
    ENGAGEMENT_SCORE
  FROM RETAIL_RECOMMENDATION_QS.GOLD.CUSTOMER_360
),
categories AS (
  SELECT CATEGORY_ID FROM RETAIL_RECOMMENDATION_QS.RAW.PRODUCT_CATEGORIES
)
SELECT
  cf.CUSTOMER_ID,
  cat.CATEGORY_ID,
  RETAIL_RECOMMENDATION_QS.ML_REGISTRY.CATEGORY_PROPENSITY_MODEL!PREDICT_PROBA(
    cf.AGE, cf.TENURE_MONTHS, cf.LOYALTY_TIER_NUM, cf.TOTAL_ORDERS,
    cf.LIFETIME_SPEND, cf.AVG_ORDER_VALUE, cf.DAYS_SINCE_PURCHASE,
    cf.CATEGORIES_PURCHASED, cf.TOTAL_BROWSE_EVENTS, cf.TOTAL_SESSIONS,
    cf.CART_ABANDONMENT_RATE, cf.ENGAGEMENT_SCORE
  ):output_feature_1::FLOAT AS PROPENSITY_SCORE
FROM customer_features cf
CROSS JOIN categories cat;

SELECT * FROM CUSTOMER_PROPENSITY
WHERE CUSTOMER_ID = 1000000
ORDER BY PROPENSITY_SCORE DESC;
```

> **Note:** The argument order must match the model's function signature exactly. Run `SHOW FUNCTIONS IN MODEL RETAIL_RECOMMENDATION_QS.ML_REGISTRY.CATEGORY_PROPENSITY_MODEL;` to verify. The `PREDICT_PROBA` call uses the model's default version.

<!-- ------------------------ -->
## Setting Up Snowflake Postgres for Low-Latency Serving
Duration: 5

To achieve sub-100ms end-to-end latency for the recommendation API, we use **Snowflake Postgres** — a managed PostgreSQL instance that runs in the same AWS region as your SPCS services, providing single-digit-millisecond lookups. Without Postgres, the orchestrator falls back to Snowflake warehouse queries which add ~500-600ms of overhead.

> **Note:** Snowflake Postgres instances are account-level objects (not database-scoped). Network rules for Postgres instances must use `MODE = POSTGRES_INGRESS`.

### Create the Postgres Instance

```sql
USE ROLE ACCOUNTADMIN;

CREATE POSTGRES INSTANCE IF NOT EXISTS RETAIL_QS_PG
  COMPUTE_FAMILY = 'STANDARD_M'
  STORAGE_SIZE_GB = 50
  AUTHENTICATION_AUTHORITY = POSTGRES;
```

> **Important:** The `CREATE` output returns the admin password in the `access_roles` JSON. **Save it immediately** — it cannot be retrieved later. Note the `host` value as well; you will need both for data loading and the orchestrator service.

Wait for the instance to reach `READY` state:

```sql
SHOW POSTGRES INSTANCES;
```

### Create Network Rules and Access Policies

The Postgres instance needs an ingress network rule to allow connections, and the SPCS orchestrator needs an egress rule to reach it:

```sql
-- Allow connections to the Postgres instance (POSTGRES_INGRESS mode required)
CREATE OR REPLACE NETWORK RULE RETAIL_RECOMMENDATION_QS.RAW.RETAIL_QS_PG_INGRESS
  TYPE = IPV4
  MODE = POSTGRES_INGRESS
  VALUE_LIST = ('0.0.0.0/0');

CREATE OR REPLACE NETWORK POLICY RETAIL_QS_PG_POLICY
  ALLOWED_NETWORK_RULE_LIST = ('RETAIL_RECOMMENDATION_QS.RAW.RETAIL_QS_PG_INGRESS');

ALTER POSTGRES INSTANCE RETAIL_QS_PG SET NETWORK_POLICY = RETAIL_QS_PG_POLICY;

-- Egress rule for SPCS orchestrator to reach Postgres
CREATE OR REPLACE NETWORK RULE RETAIL_RECOMMENDATION_QS.RAW.PG_EGRESS_RULE
  TYPE = HOST_PORT
  MODE = EGRESS
  VALUE_LIST = ('<your-pg-host>:5432');

-- Store the Postgres password as a secret for SPCS
CREATE OR REPLACE SECRET RETAIL_RECOMMENDATION_QS.RAW.PG_PASSWORD
  TYPE = GENERIC_STRING
  SECRET_STRING = '<your-admin-password>';

-- External access integration for SPCS
CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION PG_ACCESS_INTEGRATION
  ALLOWED_NETWORK_RULES = (RETAIL_RECOMMENDATION_QS.RAW.PG_EGRESS_RULE)
  ALLOWED_AUTHENTICATION_SECRETS = (RETAIL_RECOMMENDATION_QS.RAW.PG_PASSWORD)
  ENABLED = TRUE;
```

> **Important:** Replace `<your-pg-host>` with the host from `DESCRIBE POSTGRES INSTANCE RETAIL_QS_PG` and `<your-admin-password>` with the `admin_password` value.

<!-- ------------------------ -->
## Loading Data into Postgres
Duration: 5

With the Postgres instance running, connect via `psql` to create the serving tables and load data from Snowflake.

### Connect to Postgres

```bash
psql "host=<your-pg-host> port=5432 dbname=postgres user=snowflake_admin password=<your-admin-password> sslmode=require"
```

### Create Tables

```sql
CREATE TABLE IF NOT EXISTS customer_features (
  customer_id BIGINT PRIMARY KEY,
  age INT, tenure_months INT, loyalty_tier_num INT,
  total_orders INT, lifetime_spend DOUBLE PRECISION,
  avg_order_value DOUBLE PRECISION, days_since_purchase INT,
  categories_purchased INT, total_browse_events INT,
  total_sessions INT, avg_browsed_price DOUBLE PRECISION,
  add_to_cart_count INT, cart_abandonment_rate DOUBLE PRECISION,
  store_ratio DOUBLE PRECISION, engagement_score DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS customer_propensity (
  customer_id BIGINT,
  category_id TEXT,
  propensity_score DOUBLE PRECISION,
  PRIMARY KEY (customer_id, category_id)
);

CREATE TABLE IF NOT EXISTS inventory (
  product_id BIGINT,
  region TEXT,
  warehouse_name TEXT,
  qty_on_hand INT,
  est_delivery_days INT,
  PRIMARY KEY (region, product_id)
);
```

This creates three tables:

| Table | Rows | Primary Key | Purpose |
|-------|------|-------------|---------|
| `customer_features` | 50K | `customer_id` | Customer 360 features (1 row per customer) |
| `customer_propensity` | 600K | `(customer_id, category_id)` | Category propensity scores (12 rows per customer) |
| `inventory` | ~8.5K | `(region, product_id)` | Regional stock levels |

> **Design Note:** Customer features and propensity scores are kept in separate tables because they have different cardinality (1:1 vs 1:12), different query patterns (point lookup vs top-N ranked), and different refresh cadences. Denormalizing would bloat the table 12x with no benefit.

### Load Data from Snowflake

Download [`load_pg.py`](https://github.com/Snowflake-Labs/sf-samples/blob/main/samples/retail-realtime-recommendations/load_pg.py) from the companion repository. This script exports data from Snowflake and loads it into Postgres using `snowflake-connector-python` and `psycopg2`:

```bash
pip install snowflake-connector-python psycopg2-binary
export SNOWFLAKE_CONNECTION_NAME=<your-connection-name>
export PG_HOST=<your-pg-host>
export PG_PASSWORD=<your-admin-password>
python load_pg.py
```

### Verify Row Counts

In `psql`:

```sql
SELECT 'customer_features' AS tbl, COUNT(*) FROM customer_features
UNION ALL SELECT 'customer_propensity', COUNT(*) FROM customer_propensity
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory;
-- Expected: 50000, 600000, ~8500
```

<!-- ------------------------ -->
## Deploying the Ranking Model Service
Duration: 5

Deploy the real-time ranking model as an SPCS service. This creates a REST endpoint that the orchestrator will call.

```sql
USE ROLE RETAIL_QS_ROLE;
```

The ranking model was registered with `target_platforms=["SNOWPARK_CONTAINER_SERVICES"]` in the notebook. Deploy it:

```python
# Run this in the notebook (cell at the end) or in a Snowflake Python worksheet:
from snowflake.ml.registry import Registry
from snowflake.snowpark.context import get_active_session

session = get_active_session()
reg = Registry(session=session, database_name="RETAIL_RECOMMENDATION_QS",
               schema_name="ML_REGISTRY")
mv = reg.get_model("PRODUCT_RANKING_MODEL").default
mv.create_service(
    service_name="RANKING_MODEL_SERVICE",
    service_compute_pool="RETAIL_QS_COMPUTE_POOL",
    ingress_enabled=True
)
```

Wait for the service to start, then verify:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('RETAIL_RECOMMENDATION_QS.ML_REGISTRY.RANKING_MODEL_SERVICE');
SHOW ENDPOINTS IN SERVICE RETAIL_RECOMMENDATION_QS.ML_REGISTRY.RANKING_MODEL_SERVICE;
```

Note the `ingress_url` — this is the external endpoint for the ranking model.

<!-- ------------------------ -->
## Building and Deploying the Orchestrator
Duration: 8

The orchestrator is a FastAPI service that coordinates the recommendation pipeline: fetches customer features, propensity scores, and inventory from Snowflake Postgres in parallel, computes pair features, calls the ranking model, and returns top-N recommendations. It falls back to Snowflake warehouse queries if Postgres is not configured.

### Get the Orchestrator Code

Download the orchestrator files from the [companion repository](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/retail-realtime-recommendations/orchestrator):

```bash
git clone https://github.com/Snowflake-Labs/sf-samples.git
cd sf-samples/samples/retail-realtime-recommendations/orchestrator
```

### Review the Orchestrator Code

The orchestrator (`app.py`) handles the following flow per request:

1. Receives `POST /recommend {"customer_id": int, "zip_code": str, "top_n": 5}`
2. Fetches customer features from Postgres (falls back to Snowflake warehouse query)
3. Fetches propensity scores from Postgres (falls back to Snowflake warehouse query)
4. Queries available products from Postgres inventory (falls back to Snowflake warehouse query)
5. All three fetches run in parallel using a thread pool
6. Computes customer-product pair features
7. Calls the ranking model service
8. Returns top-N ranked products with details and estimated delivery

### Build the Container

First, get the image repository URL:

```sql
SHOW IMAGE REPOSITORIES IN SCHEMA RETAIL_RECOMMENDATION_QS.RAW;
```

Then build and push from your terminal:

```bash
REPO_URL=<repository_url from above>

docker login $REPO_URL --username <SNOWFLAKE_USER>
docker build --platform linux/amd64 -t $REPO_URL/retail_orchestrator:latest .
docker push $REPO_URL/retail_orchestrator:latest
```

> **Tip:** If you modify `app.py` and rebuild, Docker may cache layers. Use `docker build --platform linux/amd64 --no-cache` to force a clean rebuild and ensure the pushed image reflects your changes.

### Deploy the Orchestrator Service

```sql
USE ROLE ACCOUNTADMIN;
USE DATABASE RETAIL_RECOMMENDATION_QS;
USE SCHEMA RAW;

CREATE SERVICE ORCHESTRATOR_SERVICE
  IN COMPUTE POOL RETAIL_QS_COMPUTE_POOL
  EXTERNAL_ACCESS_INTEGRATIONS = (PG_ACCESS_INTEGRATION)
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  FROM SPECIFICATION $$
spec:
  containers:
  - name: orchestrator
    image: /retail_recommendation_qs/raw/retail_qs_images/retail_orchestrator:latest
    env:
      SNOWFLAKE_WAREHOUSE: RETAIL_QS_WH
      PYTHONUNBUFFERED: "1"
      PG_HOST: <your-pg-host>
      PG_USER: snowflake_admin
      PG_DB: postgres
      PG_PORT: "5432"
    secrets:
    - snowflakeSecret: RETAIL_RECOMMENDATION_QS.RAW.PG_PASSWORD
      secretKeyRef: secret_string
      envVarName: PG_PASSWORD
    resources:
      requests:
        cpu: 0.5
        memory: 512M
      limits:
        cpu: 2
        memory: 2G
  endpoints:
  - name: ui
    port: 8000
    public: true
$$;
```

> **Important:** Replace `<your-pg-host>` with your Postgres instance hostname. The service must be created with `EXTERNAL_ACCESS_INTEGRATIONS` to allow egress to Postgres — this requires `ACCOUNTADMIN` role.

Wait for the service to start:

```sql
CALL SYSTEM$GET_SERVICE_STATUS('ORCHESTRATOR_SERVICE');
SELECT SYSTEM$GET_SERVICE_LOGS('RETAIL_RECOMMENDATION_QS.RAW.ORCHESTRATOR_SERVICE', 0, 'orchestrator', 20);
```

You should see in the logs:
```
Postgres connected: 50000 features, 600000 propensity, 8474 inventory rows
Ready - 2000 products cached, ..., backend=postgres
```

Get the public endpoint:

```sql
SHOW ENDPOINTS IN SERVICE ORCHESTRATOR_SERVICE;
```

<!-- ------------------------ -->
## Testing the Recommendations
Duration: 3

### Test via Interactive UI

Navigate to `https://{ORCHESTRATOR_INGRESS_URL}/` in your browser (you will need to authenticate with your Snowflake credentials via OAuth). This loads a self-contained test page where you can enter a Customer ID, Zip Code, and Top N, then click **Get Recommendations** to call the API.

> **Note:** The default FastAPI Swagger UI (`/docs`) does not work in SPCS because the ingress proxy blocks the external CDN assets it requires. The built-in test page at `/` is self-contained and works within SPCS.

### Test via Health Check

Navigate to `https://{ORCHESTRATOR_INGRESS_URL}/health` to verify the service is running. You should see:

```json
{"status": "ok", "products_cached": 2000, "backend": "postgres"}
```

The `backend` field confirms whether the service is using Postgres (`postgres`) or falling back to Snowflake warehouse queries (`snowflake`).

### Test via cURL

Create a [programmatic access token (PAT)](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens) for authenticating to the SPCS ingress endpoint:

```sql
ALTER USER ADD PAT ORCHESTRATOR_PAT DAYS_TO_EXPIRY = 7;
```

Copy the `token_secret` from the output and use it in the cURL:

```bash
curl -s "https://{ORCHESTRATOR_INGRESS_URL}/recommend?customer_id=1000000&zip_code=10001&top_n=5" \
  -H 'Authorization: Snowflake Token="<PAT_TOKEN>"' | python3 -m json.tool
```

### Test via GET URL

You can also test directly in your browser URL bar:

```
https://{ORCHESTRATOR_INGRESS_URL}/recommend?customer_id=1000000&zip_code=10001&top_n=5
```

Expected recommendation response:

```json
{
  "customer_id": 1000000,
  "zip_code": "10001",
  "region": "Northeast",
  "recommendations": [
    {
      "rank": 1,
      "product_id": 42,
      "product_name": "NorthStyle Premium Blouse",
      "category": "Womens Clothing",
      "department": "Apparel",
      "price": 89.99,
      "score": 0.9234,
      "in_stock_qty": 145,
      "est_delivery_days": 2
    }
  ],
  "timings": {
    "features_ms": 15.5,
    "propensity_ms": 16.9,
    "inventory_ms": 19.6,
    "candidates": 1723,
    "pair_features_ms": 1.4,
    "model_ms": 56.2,
    "model_ok": true,
    "total_ms": 77.7,
    "backend": "postgres"
  }
}
```

> **Performance:** With Snowflake Postgres, all three data lookups (features, propensity, inventory) complete in parallel in under 20ms. The ranking model inference (~56ms) is the primary latency contributor, bringing total server-side latency to ~78ms — a **91% reduction** from the ~858ms baseline using direct Snowflake warehouse queries.

<!-- ------------------------ -->
## Cleanup
Duration: 2

To fully remove everything created in this quickstart:

```sql
USE ROLE ACCOUNTADMIN;

-- Services
ALTER SERVICE IF EXISTS RETAIL_RECOMMENDATION_QS.RAW.ORCHESTRATOR_SERVICE SUSPEND;
DROP SERVICE IF EXISTS RETAIL_RECOMMENDATION_QS.RAW.ORCHESTRATOR_SERVICE;
ALTER SERVICE IF EXISTS RETAIL_RECOMMENDATION_QS.ML_REGISTRY.RANKING_MODEL_SERVICE SUSPEND;
DROP SERVICE IF EXISTS RETAIL_RECOMMENDATION_QS.ML_REGISTRY.RANKING_MODEL_SERVICE;

-- Compute pool
DROP COMPUTE POOL IF EXISTS RETAIL_QS_COMPUTE_POOL;

-- Postgres instance and networking
DROP POSTGRES INSTANCE IF EXISTS RETAIL_QS_PG;
DROP NETWORK POLICY IF EXISTS RETAIL_QS_PG_POLICY;
DROP INTEGRATION IF EXISTS PG_ACCESS_INTEGRATION;

-- Database (drops all schemas, tables, models, feature views, dynamic tables,
-- network rules, secrets, and stages)
DROP DATABASE IF EXISTS RETAIL_RECOMMENDATION_QS;

-- User and role
DROP USER IF EXISTS RETAIL_QS_SVC_USER;
DROP ROLE IF EXISTS RETAIL_QS_ROLE;

-- Warehouse
DROP WAREHOUSE IF EXISTS RETAIL_QS_WH;
```

<!-- ------------------------ -->
## Conclusion and Next Steps
Duration: 2

### What You Built

You built a complete real-time product recommendation engine for retail, powered entirely by Snowflake:

- **Synthetic data layer** with 50K customers, ~4M events, 2K products, and regional inventory
- **Customer 360 gold layer** using Dynamic Tables for automatic refresh
- **Feature Store** for offline training data retrieval
- **Two XGBoost models**: batch propensity (daily, warehouse) and real-time ranking (SPCS)
- **Snowflake Postgres** for low-latency operational serving (~15ms lookups vs ~575ms from warehouse)
- **SPCS orchestrator** that fetches data from Postgres in parallel, calls the ranking model, and returns recommendations in ~78ms end-to-end (91% faster than the warehouse-only baseline of ~858ms)

### What You Learned

- How to use Snowflake UDTFs to generate realistic synthetic retail data
- How to build a Customer 360 with Dynamic Tables
- How to use the Feature Store for training data management
- How to train and register models in the Snowflake Model Registry
- How to deploy ML models and custom services on Snowpark Container Services
- How to use Snowflake Postgres for low-latency operational serving alongside SPCS
- The hybrid batch + real-time pattern for production ML systems

### Next Steps

- **Automated Postgres Sync**: Use Snowflake Tasks to periodically refresh Postgres tables from the Feature Store and batch propensity outputs
- **CatBoost Delivery Estimation**: Replace the deterministic inventory filter with a CatBoost model trained on real logistics data (carrier performance, distance, demand signals) for accurate delivery date predictions
- **Identity Resolution**: Add a Cortex Search-based identity resolution layer to unify customer profiles across channels
- **Agentic Commerce**: Build a Cortex Agent on top of the recommendation API to enable conversational product discovery
- **Activation**: Connect recommendations to GrowthLoop or HighTouch for audience activation and campaign orchestration
- **A/B Testing**: Implement model version aliasing to A/B test different ranking strategies

### Resources

- [Snowflake Feature Store Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/feature-store/overview)
- [Snowflake Model Registry Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Snowpark Container Services Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/postgres/overview)
- [Programmatic Access Tokens](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [Companion Code on GitHub](https://github.com/Snowflake-Labs/sf-samples/tree/main/samples/retail-realtime-recommendations)
