
-- =============================================================================
-- Creator Commerce ML Demo — Environment Setup
-- Verified against: Snowflake docs, snowflake-ml-python >= 1.7.0
-- =============================================================================

-- 1. Database and schemas
CREATE DATABASE IF NOT EXISTS CC_DEMO;

CREATE SCHEMA IF NOT EXISTS CC_DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.ML;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.ML_REGISTRY;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.FEATURE_STORE;
CREATE SCHEMA IF NOT EXISTS CC_DEMO.APPS;

-- [PASS] Schemas created

-- 2. Warehouse for ML workloads
CREATE WAREHOUSE IF NOT EXISTS CC_ML_WH
    WAREHOUSE_SIZE = 'MEDIUM'
    AUTO_SUSPEND = 120
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- [PASS] Warehouse created

-- 3. Compute pool for SPCS model serving
CREATE COMPUTE POOL IF NOT EXISTS CC_COMPUTE_POOL
    MIN_NODES = 1
    MAX_NODES = 2
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_SUSPEND_SECS = 300;

-- [PASS] Compute pool created

-- 4. Raw data tables
USE SCHEMA CC_DEMO.RAW;

CREATE OR REPLACE TABLE CREATORS (
    CREATOR_ID        VARCHAR(16)    NOT NULL,
    CREATOR_NAME      VARCHAR(128),
    CATEGORY          VARCHAR(32),
    FOLLOWER_COUNT    NUMBER(12,0),
    COUNTRY           VARCHAR(3),
    AVG_ENGAGEMENT    FLOAT,
    JOINED_DATE       DATE,
    PRIMARY KEY (CREATOR_ID)
);

CREATE OR REPLACE TABLE BRANDS (
    BRAND_ID          VARCHAR(16)    NOT NULL,
    BRAND_NAME        VARCHAR(128),
    CATEGORY          VARCHAR(32),
    BUDGET_TIER       VARCHAR(16),
    PRIMARY KEY (BRAND_ID)
);

CREATE OR REPLACE TABLE BEHAVIORAL_EVENTS (
    EVENT_ID          VARCHAR(36)    NOT NULL,
    CREATOR_ID        VARCHAR(16),
    BRAND_ID          VARCHAR(16),
    SESSION_ID        VARCHAR(36),
    EVENT_TYPE        VARCHAR(16),
    EVENT_DATE        DATE,
    EVENT_TIMESTAMP   TIMESTAMP_NTZ,
    GMV               FLOAT,
    CLICK_THROUGH_RATE FLOAT,
    ENGAGEMENT_SCORE  FLOAT,
    PLATFORM          VARCHAR(16)
);

CREATE OR REPLACE TABLE CREATOR_BRAND_INTERACTIONS (
    INTERACTION_ID    VARCHAR(36)    NOT NULL,
    CREATOR_ID        VARCHAR(16),
    BRAND_ID          VARCHAR(16),
    CAMPAIGN_ID       VARCHAR(16),
    EVENT_TIMESTAMP   TIMESTAMP_NTZ,
    CONVERTED         BOOLEAN,
    MATCH_QUALITY     FLOAT
);

-- [PASS] Raw tables created

-- 5. Creator content table (for embeddings + Cortex Search demos)
CREATE OR REPLACE TABLE CREATOR_CONTENT (
    CREATOR_ID        VARCHAR(16),
    CONTENT_TEXT      VARCHAR(2000),
    CATEGORY          VARCHAR(32),
    PLATFORM          VARCHAR(16)
);

-- 200 rows across 8 categories x 4 platforms for credible Cortex Search demo
INSERT INTO CREATOR_CONTENT VALUES
    -- fashion (25)
    ('CR_00001', 'Sustainable fashion haul featuring eco-friendly brands', 'fashion', 'instagram'),
    ('CR_00007', 'Minimalist wardrobe capsule for fall outfits', 'fashion', 'instagram'),
    ('CR_00010', 'Street style lookbook: mixing high and low fashion', 'fashion', 'tiktok'),
    ('CR_00015', 'How to style one blazer five different ways', 'fashion', 'youtube'),
    ('CR_00020', 'Thrift store haul: designer finds under $50', 'fashion', 'tiktok'),
    ('CR_00025', 'Spring fashion trends you need to know about', 'fashion', 'instagram'),
    ('CR_00030', 'Building a capsule wardrobe on a budget', 'fashion', 'youtube'),
    ('CR_00035', 'Vintage denim styling guide for everyday wear', 'fashion', 'app'),
    ('CR_00040', 'Luxury vs affordable: can you tell the difference', 'fashion', 'tiktok'),
    ('CR_00045', 'Resort wear essentials for your next vacation', 'fashion', 'instagram'),
    ('CR_00050', 'Sustainable brands that are actually affordable', 'fashion', 'youtube'),
    ('CR_00055', 'Workwear outfit ideas for creative professionals', 'fashion', 'instagram'),
    ('CR_00060', 'How I organize my closet with the capsule method', 'fashion', 'tiktok'),
    ('CR_00065', 'Festival fashion guide: boho chic on a budget', 'fashion', 'app'),
    ('CR_00070', 'Matching sets trend: how to style co-ords', 'fashion', 'instagram'),
    ('CR_00075', 'Denim on denim: the Canadian tuxedo done right', 'fashion', 'tiktok'),
    ('CR_00080', 'Transitional outfits from summer to fall', 'fashion', 'youtube'),
    ('CR_00085', 'Accessory haul: bags belts and jewelry under $30', 'fashion', 'instagram'),
    ('CR_00090', 'Fashion week street style recap and top looks', 'fashion', 'tiktok'),
    ('CR_00095', 'Ethical fashion brands you should know in 2026', 'fashion', 'youtube'),
    ('CR_00100', 'Date night outfit ideas for every budget', 'fashion', 'instagram'),
    ('CR_00105', 'Oversized blazer trend: how to nail the fit', 'fashion', 'tiktok'),
    ('CR_00110', 'Color blocking guide for bold style statements', 'fashion', 'app'),
    ('CR_00115', 'Best online thrift stores ranked and reviewed', 'fashion', 'youtube'),
    ('CR_00120', 'Athletic wear that doubles as streetwear', 'fashion', 'instagram'),
    -- beauty (25)
    ('CR_00002', 'Morning skincare routine with clean beauty products', 'beauty', 'tiktok'),
    ('CR_00008', 'Anti-aging serum comparison and honest review', 'beauty', 'youtube'),
    ('CR_00125', 'Glass skin tutorial: Korean skincare routine', 'beauty', 'tiktok'),
    ('CR_00130', 'Drugstore dupes for high-end makeup products', 'beauty', 'youtube'),
    ('CR_00135', 'Natural makeup look for beginners step by step', 'beauty', 'instagram'),
    ('CR_00140', 'Retinol guide: everything you need to know', 'beauty', 'youtube'),
    ('CR_00145', 'Bold lip colors for every skin tone', 'beauty', 'tiktok'),
    ('CR_00150', 'Nighttime skincare routine for acne-prone skin', 'beauty', 'instagram'),
    ('CR_00155', 'Clean beauty brands that actually work', 'beauty', 'youtube'),
    ('CR_00160', 'Contouring tutorial for different face shapes', 'beauty', 'tiktok'),
    ('CR_00165', 'SPF guide: best sunscreens that dont leave a white cast', 'beauty', 'instagram'),
    ('CR_00170', 'Hair care routine for curly and coily textures', 'beauty', 'youtube'),
    ('CR_00175', 'Minimal makeup routine in under 5 minutes', 'beauty', 'tiktok'),
    ('CR_00180', 'Vitamin C serum comparison: which one is best', 'beauty', 'instagram'),
    ('CR_00185', 'Full coverage foundation for oily skin review', 'beauty', 'youtube'),
    ('CR_00190', 'Eyebrow shaping tutorial at home no salon needed', 'beauty', 'tiktok'),
    ('CR_00195', 'Body care routine for smooth glowing skin', 'beauty', 'instagram'),
    ('CR_00200', 'Fragrance collection tour and top picks for spring', 'beauty', 'youtube'),
    ('CR_00205', 'Lip liner tricks that make your lips look fuller', 'beauty', 'tiktok'),
    ('CR_00210', 'Sensitive skin approved products I swear by', 'beauty', 'instagram'),
    ('CR_00215', 'Nail art tutorial: easy designs for beginners', 'beauty', 'tiktok'),
    ('CR_00220', 'Double cleansing method explained with demo', 'beauty', 'youtube'),
    ('CR_00225', 'Best setting sprays for all-day makeup wear', 'beauty', 'instagram'),
    ('CR_00230', 'Affordable skincare routine under $50 total', 'beauty', 'tiktok'),
    ('CR_00235', 'Makeup brushes vs sponges: which is better', 'beauty', 'youtube'),
    -- home (25)
    ('CR_00003', 'Budget-friendly home office makeover DIY', 'home', 'youtube'),
    ('CR_00240', 'Small apartment organization hacks that work', 'home', 'tiktok'),
    ('CR_00245', 'Cozy living room transformation on a budget', 'home', 'youtube'),
    ('CR_00250', 'DIY wall art ideas using recycled materials', 'home', 'instagram'),
    ('CR_00255', 'Kitchen pantry organization with clear containers', 'home', 'tiktok'),
    ('CR_00260', 'Minimalist bedroom design tips for better sleep', 'home', 'youtube'),
    ('CR_00265', 'Indoor plant care guide for beginners', 'home', 'instagram'),
    ('CR_00270', 'Bathroom renovation before and after on a budget', 'home', 'tiktok'),
    ('CR_00275', 'Seasonal home decor swaps for instant refresh', 'home', 'youtube'),
    ('CR_00280', 'Smart home gadgets that are actually worth buying', 'home', 'app'),
    ('CR_00285', 'Closet organization system that stays tidy', 'home', 'instagram'),
    ('CR_00290', 'Patio and balcony makeover for outdoor living', 'home', 'tiktok'),
    ('CR_00295', 'Gallery wall layout tips and hanging guide', 'home', 'youtube'),
    ('CR_00300', 'Laundry room transformation with storage hacks', 'home', 'instagram'),
    ('CR_00305', 'Candle and diffuser collection for cozy vibes', 'home', 'tiktok'),
    ('CR_00310', 'Renter-friendly decor ideas no damage to walls', 'home', 'youtube'),
    ('CR_00315', 'Desk setup tour for productivity and aesthetics', 'home', 'app'),
    ('CR_00320', 'Bed linen guide: thread count and materials explained', 'home', 'instagram'),
    ('CR_00325', 'Entryway organization ideas for small spaces', 'home', 'tiktok'),
    ('CR_00330', 'Holiday decorating on a budget festive and fun', 'home', 'youtube'),
    ('CR_00335', 'Cleaning routine that keeps your home spotless', 'home', 'instagram'),
    ('CR_00340', 'Best storage solutions from IKEA tested and ranked', 'home', 'tiktok'),
    ('CR_00345', 'Color palette guide for cohesive room design', 'home', 'youtube'),
    ('CR_00350', 'Thrifted furniture flips and upcycling projects', 'home', 'app'),
    ('CR_00355', 'Nursery design ideas that grow with your child', 'home', 'instagram'),
    -- fitness (25)
    ('CR_00004', 'HIIT workout for beginners at home', 'fitness', 'instagram'),
    ('CR_00360', 'Full body dumbbell workout no gym needed', 'fitness', 'youtube'),
    ('CR_00365', 'Morning yoga flow for energy and flexibility', 'fitness', 'instagram'),
    ('CR_00370', 'Abs workout routine you can do anywhere', 'fitness', 'tiktok'),
    ('CR_00375', 'Running tips for beginners couch to 5K guide', 'fitness', 'youtube'),
    ('CR_00380', 'Resistance band exercises for toned arms', 'fitness', 'instagram'),
    ('CR_00385', 'Post-workout stretching routine for recovery', 'fitness', 'tiktok'),
    ('CR_00390', 'Meal prep for muscle gain high protein recipes', 'fitness', 'youtube'),
    ('CR_00395', 'Jump rope workout that burns serious calories', 'fitness', 'tiktok'),
    ('CR_00400', 'Gym bag essentials everything you actually need', 'fitness', 'instagram'),
    ('CR_00405', 'Pilates for beginners full 30 minute session', 'fitness', 'youtube'),
    ('CR_00410', 'Best protein powders tested and ranked 2026', 'fitness', 'tiktok'),
    ('CR_00415', 'Glute activation exercises for better workouts', 'fitness', 'instagram'),
    ('CR_00420', 'Swimming workout plan for cardio and strength', 'fitness', 'youtube'),
    ('CR_00425', 'Walking workout with intervals for fat loss', 'fitness', 'tiktok'),
    ('CR_00430', 'Home gym setup guide on every budget level', 'fitness', 'app'),
    ('CR_00435', 'Flexibility challenge 30 days to splits', 'fitness', 'instagram'),
    ('CR_00440', 'Pre-workout vs coffee which is better for energy', 'fitness', 'tiktok'),
    ('CR_00445', 'Strength training for women myths debunked', 'fitness', 'youtube'),
    ('CR_00450', 'Recovery day routine foam rolling and mobility', 'fitness', 'instagram'),
    ('CR_00455', 'Cycling workout indoor trainer vs outdoor ride', 'fitness', 'tiktok'),
    ('CR_00460', 'Beginner calisthenics progressions push pull legs', 'fitness', 'youtube'),
    ('CR_00465', 'Fitness tracker comparison which one to buy', 'fitness', 'app'),
    ('CR_00470', 'Dance cardio workout fun and effective routine', 'fitness', 'tiktok'),
    ('CR_00475', 'Posture correction exercises for desk workers', 'fitness', 'instagram'),
    -- lifestyle (25)
    ('CR_00480', 'Morning routine that changed my productivity', 'lifestyle', 'youtube'),
    ('CR_00485', 'Minimalist living tips for a clutter-free life', 'lifestyle', 'instagram'),
    ('CR_00490', 'Self care Sunday routine for mental wellness', 'lifestyle', 'tiktok'),
    ('CR_00495', 'Budget-friendly date night ideas at home', 'lifestyle', 'youtube'),
    ('CR_00500', 'How I plan my week for maximum productivity', 'lifestyle', 'instagram'),
    ('CR_00505', 'Journal prompts for self reflection and growth', 'lifestyle', 'tiktok'),
    ('CR_00510', 'Sustainable living swaps you can make today', 'lifestyle', 'youtube'),
    ('CR_00515', 'Reading list: best books I read this year', 'lifestyle', 'instagram'),
    ('CR_00520', 'Digital detox challenge one week without social media', 'lifestyle', 'tiktok'),
    ('CR_00525', 'Night routine for better sleep quality', 'lifestyle', 'youtube'),
    ('CR_00530', 'How to start a side hustle from home', 'lifestyle', 'app'),
    ('CR_00535', 'Gratitude practice that improved my mental health', 'lifestyle', 'instagram'),
    ('CR_00540', 'Apartment tour: how I decorated on a budget', 'lifestyle', 'tiktok'),
    ('CR_00545', 'Work from home tips from a remote work veteran', 'lifestyle', 'youtube'),
    ('CR_00550', 'Monthly reset routine for goals and habits', 'lifestyle', 'instagram'),
    ('CR_00555', 'Mindfulness meditation guide for beginners', 'lifestyle', 'tiktok'),
    ('CR_00560', 'Capsule lifestyle: simplify every area of life', 'lifestyle', 'youtube'),
    ('CR_00565', 'Best podcasts for personal development 2026', 'lifestyle', 'instagram'),
    ('CR_00570', 'How I budget and save as a content creator', 'lifestyle', 'tiktok'),
    ('CR_00575', 'Vision board tutorial and goal setting workshop', 'lifestyle', 'youtube'),
    ('CR_00580', 'Day in my life as a full-time creator', 'lifestyle', 'instagram'),
    ('CR_00585', 'Gift guide: thoughtful presents under $25', 'lifestyle', 'tiktok'),
    ('CR_00590', 'Time management tips for creative professionals', 'lifestyle', 'app'),
    ('CR_00595', 'Healthy habits that stick science-backed tips', 'lifestyle', 'youtube'),
    ('CR_00600', 'Aesthetic desk organization for content creators', 'lifestyle', 'instagram'),
    -- food (25)
    ('CR_00005', 'Meal prep: 5 healthy lunch recipes under 30 min', 'food', 'tiktok'),
    ('CR_00605', 'Easy weeknight dinner recipes for busy families', 'food', 'youtube'),
    ('CR_00610', 'Sourdough bread from scratch beginner guide', 'food', 'instagram'),
    ('CR_00615', 'Protein-packed breakfast ideas for busy mornings', 'food', 'tiktok'),
    ('CR_00620', 'Restaurant quality pasta at home in 20 minutes', 'food', 'youtube'),
    ('CR_00625', 'Smoothie bowl recipes that taste like dessert', 'food', 'instagram'),
    ('CR_00630', 'Air fryer recipes you need to try this week', 'food', 'tiktok'),
    ('CR_00635', 'Vegan meal prep for the whole week', 'food', 'youtube'),
    ('CR_00640', 'Best coffee brewing methods compared at home', 'food', 'app'),
    ('CR_00645', 'Baking cookies from scratch: 5 classic recipes', 'food', 'instagram'),
    ('CR_00650', 'Asian fusion recipes inspired by street food', 'food', 'tiktok'),
    ('CR_00655', 'Grocery haul and budget meal planning tips', 'food', 'youtube'),
    ('CR_00660', 'Homemade pizza dough recipe better than delivery', 'food', 'instagram'),
    ('CR_00665', 'Healthy snack ideas for work and school', 'food', 'tiktok'),
    ('CR_00670', 'One pot meals for lazy cooking nights', 'food', 'youtube'),
    ('CR_00675', 'Brunch recipes to impress your weekend guests', 'food', 'instagram'),
    ('CR_00680', 'Fermented foods guide: kimchi kombucha and more', 'food', 'tiktok'),
    ('CR_00685', 'Meal plan for weight loss that actually tastes good', 'food', 'youtube'),
    ('CR_00690', 'Charcuterie board assembly for entertaining', 'food', 'app'),
    ('CR_00695', 'Quick lunch wraps and sandwiches for meal prep', 'food', 'instagram'),
    ('CR_00700', 'Holiday baking: cookies cakes and festive treats', 'food', 'tiktok'),
    ('CR_00705', 'Budget cooking: feed a family of four for $50/week', 'food', 'youtube'),
    ('CR_00710', 'Instant pot recipes for beginners easy and fast', 'food', 'instagram'),
    ('CR_00715', 'Food photography tips for better Instagram posts', 'food', 'tiktok'),
    ('CR_00720', 'Copycat restaurant recipes made at home', 'food', 'youtube'),
    -- travel (25)
    ('CR_00006', 'Tokyo street style guide and vintage shop tour', 'travel', 'app'),
    ('CR_00725', 'Budget travel tips: see Europe for under $50/day', 'travel', 'youtube'),
    ('CR_00730', 'Best hidden gems in Bali off the tourist trail', 'travel', 'instagram'),
    ('CR_00735', 'Solo travel safety tips for first-time travelers', 'travel', 'tiktok'),
    ('CR_00740', 'Road trip essentials and packing checklist', 'travel', 'youtube'),
    ('CR_00745', 'Weekend getaway ideas within driving distance', 'travel', 'instagram'),
    ('CR_00750', 'How to find cheap flights and hotel deals', 'travel', 'tiktok'),
    ('CR_00755', 'Travel vlog: exploring the streets of Lisbon', 'travel', 'youtube'),
    ('CR_00760', 'Best travel backpacks reviewed and compared', 'travel', 'app'),
    ('CR_00765', 'Island hopping guide for the Greek islands', 'travel', 'instagram'),
    ('CR_00770', 'Travel photography tips for stunning vacation photos', 'travel', 'tiktok'),
    ('CR_00775', 'Food tour in Mexico City tacos and street eats', 'travel', 'youtube'),
    ('CR_00780', 'Digital nomad guide: working remotely abroad', 'travel', 'app'),
    ('CR_00785', 'National parks camping guide for beginners', 'travel', 'instagram'),
    ('CR_00790', 'Luxury travel on a budget upgrade hacks', 'travel', 'tiktok'),
    ('CR_00795', 'Cultural etiquette tips for traveling in Japan', 'travel', 'youtube'),
    ('CR_00800', 'Packing guide: one carry-on for two weeks', 'travel', 'instagram'),
    ('CR_00805', 'Train travel across Europe itinerary and tips', 'travel', 'tiktok'),
    ('CR_00810', 'Best travel credit cards for points and rewards', 'travel', 'youtube'),
    ('CR_00815', 'Adventure travel: hiking Patagonia trail guide', 'travel', 'app'),
    ('CR_00820', 'City guide: 48 hours in New York on a budget', 'travel', 'instagram'),
    ('CR_00825', 'Safari planning guide: what to expect in Kenya', 'travel', 'tiktok'),
    ('CR_00830', 'Airport lounge access hacks without premium cards', 'travel', 'youtube'),
    ('CR_00835', 'Southeast Asia backpacking route for one month', 'travel', 'instagram'),
    ('CR_00840', 'Travel journal ideas to document your adventures', 'travel', 'tiktok'),
    -- tech (25)
    ('CR_00845', 'Best productivity apps for 2026 tested and ranked', 'tech', 'youtube'),
    ('CR_00850', 'Smartphone camera tips for professional-looking photos', 'tech', 'tiktok'),
    ('CR_00855', 'Home office tech setup for content creators', 'tech', 'youtube'),
    ('CR_00860', 'Wireless earbuds comparison: which sounds best', 'tech', 'instagram'),
    ('CR_00865', 'Smart home automation setup guide for beginners', 'tech', 'youtube'),
    ('CR_00870', 'Best laptops for students and creators 2026', 'tech', 'tiktok'),
    ('CR_00875', 'Cloud storage comparison: which service to use', 'tech', 'app'),
    ('CR_00880', 'Video editing software comparison for beginners', 'tech', 'youtube'),
    ('CR_00885', 'Tech gadgets under $50 that are actually useful', 'tech', 'tiktok'),
    ('CR_00890', 'Mechanical keyboard guide for typing enthusiasts', 'tech', 'instagram'),
    ('CR_00895', 'AI tools for content creation honest review', 'tech', 'youtube'),
    ('CR_00900', 'Streaming setup guide: camera mic and lighting', 'tech', 'tiktok'),
    ('CR_00905', 'Phone case comparison: protection vs style', 'tech', 'instagram'),
    ('CR_00910', 'Tablet vs laptop: which should you buy in 2026', 'tech', 'youtube'),
    ('CR_00915', 'Portable charger and power bank buying guide', 'tech', 'tiktok'),
    ('CR_00920', 'Smart watch health features compared and tested', 'tech', 'app'),
    ('CR_00925', 'Monitor setup guide for work and gaming', 'tech', 'youtube'),
    ('CR_00930', 'Best apps for photo editing on your phone', 'tech', 'tiktok'),
    ('CR_00935', 'VPN guide: privacy and streaming access explained', 'tech', 'instagram'),
    ('CR_00940', 'Drone buying guide for beginners and creators', 'tech', 'youtube'),
    ('CR_00945', 'Cable management and desk organization tech setup', 'tech', 'tiktok'),
    ('CR_00950', 'E-reader comparison Kindle vs Kobo for bookworms', 'tech', 'instagram'),
    ('CR_00955', 'Podcast recording setup on a budget', 'tech', 'youtube'),
    ('CR_00960', 'Bluetooth speaker roundup best portable options', 'tech', 'tiktok'),
    ('CR_00965', 'Digital planner apps for iPad and Android tablet', 'tech', 'app');

-- [PASS] Creator content table created (200 rows, 8 categories, 4 platforms)

-- 6. Dynamic Table for feature computation
USE SCHEMA CC_DEMO.ML;

CREATE OR REPLACE DYNAMIC TABLE CREATOR_ENGAGEMENT_FEATURES
    TARGET_LAG = '2 minutes'
    WAREHOUSE = CC_ML_WH
AS
SELECT
    CREATOR_ID,
    COUNT(DISTINCT SESSION_ID)                                    AS SESSIONS_7D,
    AVG(CLICK_THROUGH_RATE)                                       AS AVG_CTR_7D,
    SUM(CASE WHEN EVENT_TYPE = 'purchase' THEN 1 ELSE 0 END)     AS PURCHASES_7D,
    SUM(GMV)                                                      AS GMV_7D,
    COUNT(DISTINCT BRAND_ID)                                      AS UNIQUE_BRANDS_7D,
    AVG(ENGAGEMENT_SCORE)                                         AS AVG_ENGAGEMENT_7D,
    CURRENT_TIMESTAMP()                                           AS FEATURE_TIMESTAMP
FROM CC_DEMO.RAW.BEHAVIORAL_EVENTS
WHERE EVENT_DATE >= DATEADD('day', -7, CURRENT_DATE())
GROUP BY CREATOR_ID;

-- [PASS] Dynamic Table created

-- NOTE: CREATOR_PROFILES_LIVE Dynamic Table is created by creator_brand_match.py
-- after CREATOR_PROFILES table is populated by the ML pipeline. Do not create here.

-- [SETUP COMPLETE]
SELECT '[SETUP COMPLETE] CC_DEMO ready for demo' AS STATUS;
