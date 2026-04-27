-- ============================================================================
-- Voice Order Processing with Snowflake AI - Setup Script
-- Run this BEFORE opening the notebook.
-- Requires ACCOUNTADMIN role.
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- ============================================================================
-- 1. Warehouse
-- ============================================================================
CREATE WAREHOUSE IF NOT EXISTS TASTY_AUDIO_WH
    WITH WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE TASTY_AUDIO_WH;

-- ============================================================================
-- 2. Database and Schema
-- ============================================================================
CREATE DATABASE IF NOT EXISTS TASTY_AUDIO_DB;
CREATE SCHEMA IF NOT EXISTS TASTY_AUDIO_DB.ORDERS;

USE DATABASE TASTY_AUDIO_DB;
USE SCHEMA ORDERS;

-- ============================================================================
-- 3. External Network Access (for Google Translate TTS)
-- ============================================================================
CREATE OR REPLACE NETWORK RULE google_tts_rule
  MODE = EGRESS
  TYPE = HOST_PORT
  VALUE_LIST = ('translate.google.com:443');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION google_tts_integration
  ALLOWED_NETWORK_RULES = (google_tts_rule)
  ENABLED = TRUE;

-- ============================================================================
-- 4. Stage for Audio Files
-- ============================================================================
CREATE STAGE IF NOT EXISTS AUDIO_STAGE
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for voice order recordings';

-- ============================================================================
-- 5. Tables
-- ============================================================================
CREATE OR REPLACE TABLE CUSTOMER_ORDERS (
    order_id INTEGER AUTOINCREMENT PRIMARY KEY,
    order_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    audio_file VARCHAR(255),
    raw_transcript TEXT,
    item_name VARCHAR(255),
    quantity INTEGER,
    size VARCHAR(50),
    special_instructions TEXT,
    order_status VARCHAR(50) DEFAULT 'PENDING'
);

CREATE OR REPLACE TABLE ORDER_PHRASES (
    phrase_id INTEGER,
    order_text VARCHAR(500)
);

-- ============================================================================
-- 6. Seed Data (75 Order Phrases)
-- ============================================================================
INSERT INTO ORDER_PHRASES (phrase_id, order_text) VALUES
    (1, 'I want a hamburger with pickles and onion.'),
    (2, 'Cheeseburger with extra cheese and no mayo.'),
    (3, 'Bacon burger, medium rare, with fries.'),
    (4, 'Double cheeseburger with everything on it.'),
    (5, 'Veggie burger with no tomato.'),
    (6, 'Just a plain hamburger, nothing else.'),
    (7, 'Three hamburgers for the kids, plain with ketchup only.'),
    (8, 'Two double cheeseburgers with bacon and a large fry.'),
    (9, 'One veggie burger, make it spicy please.'),
    (10, 'Can I get five hamburgers for the office? All with lettuce and tomato.'),
    (11, 'Cheeseburger, no onions, extra pickles.'),
    (12, 'Two bacon cheeseburgers, one with no tomato.'),
    (13, 'Can I get a chicken sandwich with lettuce?'),
    (14, 'Turkey club sandwich on wheat bread.'),
    (15, 'Grilled cheese sandwich with tomato soup.'),
    (16, 'Fish sandwich with tartar sauce on the side.'),
    (17, 'Two chicken sandwiches, both spicy.'),
    (18, 'BLT on sourdough, extra crispy bacon.'),
    (19, 'Three turkey clubs for a meeting, cut in halves please.'),
    (20, 'Philly cheesesteak with peppers and onions.'),
    (21, 'Pizza with tomato sauce only.'),
    (22, 'Large pepperoni pizza, thin crust.'),
    (23, 'Small cheese pizza and a side of ranch.'),
    (24, 'Slice of veggie pizza with mushrooms and peppers.'),
    (25, 'Hawaiian pizza with extra pineapple.'),
    (26, 'Meat lovers pizza, but no sausage.'),
    (27, 'White pizza with spinach and garlic.'),
    (28, 'Two slices of pepperoni and a soda.'),
    (29, 'Gluten-free pizza with mozzarella.'),
    (30, 'Deep dish pizza with sausage and onions.'),
    (31, 'Three large pepperoni pizzas for a party.'),
    (32, 'Two medium cheese pizzas and one large supreme.'),
    (33, 'Four slices of cheese pizza to go.'),
    (34, 'Extra large margherita pizza with fresh basil.'),
    (35, 'One small veggie and one small meat lovers.'),
    (36, 'Can I get a large Coke?'),
    (37, 'I will take a medium iced tea, unsweetened.'),
    (38, 'Small chocolate milkshake.'),
    (39, 'Water with lemon, please.'),
    (40, 'Large coffee with cream and sugar.'),
    (41, 'Six waters for the table.'),
    (42, 'Two large Cokes and a medium Sprite.'),
    (43, 'Four chocolate milkshakes for the birthday party.'),
    (44, 'Large vanilla milkshake, extra thick.'),
    (45, 'Three iced coffees, all with oat milk.'),
    (46, 'Diet Coke, no ice please.'),
    (47, 'Two hot chocolates with whipped cream.'),
    (48, 'Large order of fries with cheese sauce.'),
    (49, 'Two orders of onion rings.'),
    (50, 'Chicken nuggets twenty piece with honey mustard.'),
    (51, 'Three large fries and two small fries.'),
    (52, 'Mozzarella sticks with marinara sauce.'),
    (53, 'Side salad with ranch dressing.'),
    (54, 'Two side salads, both with Italian dressing.'),
    (55, 'Loaded nachos with extra jalapenos.'),
    (56, 'Family meal: four burgers, four fries, and four drinks.'),
    (57, 'Two pepperoni pizzas, one order of wings, and a two liter Coke.'),
    (58, 'Kids meal with chicken nuggets, small fry, and apple juice.'),
    (59, 'Three kids meals, two with hamburgers and one with nuggets.'),
    (60, 'Party pack: five large pizzas, assorted toppings.'),
    (61, 'Hamburger with gluten-free bun please.'),
    (62, 'Cheeseburger, no bun, lettuce wrap style.'),
    (63, 'Vegan burger with vegan cheese.'),
    (64, 'Two salads, no croutons, dressing on the side.'),
    (65, 'Grilled chicken sandwich, no bread, extra veggies.'),
    (66, 'Breakfast burrito with extra salsa.'),
    (67, 'Two egg sandwiches on English muffins.'),
    (68, 'Stack of pancakes with maple syrup.'),
    (69, 'Three bacon egg and cheese sandwiches for the crew.'),
    (70, 'Large orange juice and a blueberry muffin.'),
    (71, 'Chocolate brownie sundae with extra fudge.'),
    (72, 'Two apple pies, warmed up please.'),
    (73, 'Ice cream cone, chocolate and vanilla swirl.'),
    (74, 'Slice of cheesecake to go.'),
    (75, 'Four cookies, two chocolate chip and two oatmeal raisin.');

-- ============================================================================
-- Done! Now open the notebook and add GOOGLE_TTS_INTEGRATION
-- in Settings > External access before running cells.
-- ============================================================================
SELECT 'Setup complete! Open the notebook to begin.' AS STATUS;
